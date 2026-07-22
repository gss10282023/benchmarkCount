#!/usr/bin/env python3
"""Freeze and fail-closed audit the repaired TB2.1 + DeepSWE1.1 checklist corpus.

This is deliberately a *pre-run* operation.  It reads only case packets, the
frozen original drafts, the outcome-blind semantic-review bodies, and the
outcome-blind reviewer corrections materialized by
``materialize_repair_v2_from_reviews.py``.  It never opens a trajectory,
execution artifact, result/reward/label, evidence score, or conflict record.

The 70 original ``accept`` cases are carried forward byte-for-byte.  The 132
``revise`` cases use the reviewer's complete corrected body.  The latter may
only differ from that body in canonical identity fields, support-pointer repair,
and the explicit removal of final-label filename shorthand.  Every resulting
checklist is then revalidated against its own packet before the v2 lock is
written.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator


AUDIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AUDIT_ROOT.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    case_packet_support_paths,
    collect_checklist_guardrail_violations,
)
from neurips_ed_track_minimal.scripts.checklist_validator import (  # noqa: E402
    validate_packet_required_stronger_conditions,
    validate_support_pointers,
)


SOURCE_DRAFT_ROOT = AUDIT_ROOT / "drafts"
SEMANTIC_RECORDS = AUDIT_ROOT / "semantic_review_records.jsonl"
SEMANTIC_REVIEW_ROOT = AUDIT_ROOT / "semantic_reviews"
CANDIDATE_ROOT = AUDIT_ROOT / "repair_v2" / "reviewer_repair_candidates"
OUTPUT_ROOT = AUDIT_ROOT / "repair_v2" / "frozen_drafts"
REPAIR_ROOT = AUDIT_ROOT / "repair_v2"
SCHEMA_PATH = REPO_ROOT / "neurips_ed_track_minimal/schemas/case_checklist.schema.json"
PACKET_ROOTS = {
    "terminal_bench_2_1": REPO_ROOT / "experiments/case_packets/terminal_bench_2_1",
    "deep_swe_v1_1": REPO_ROOT / "experiments/case_packets/deep_swe_v1_1",
}

FINAL_LABEL_TEXT_RE = re.compile(
    r"(?ix)("
    r"(?:^|[/`])(?:result\.json|reward\.txt|reward\.json)(?:$|[`\s])"
    r"|released\s+(?:evaluator\s+)?label"
    r"|per[- ]record\s+(?:reward|result|label)"
    r"|\bnative_(?:label|score)\b"
    r")"
)
LABEL_EXCLUSION_RE = re.compile(
    r"(?ix)\b(?:not|never|without|rather\s+than|exclude[ds]?|cannot|can't|"
    r"may\s+not|must\s+not)\b"
)
LABEL_PATH_RE = re.compile(
    r"(?ix)\b(?:result\.json|reward\.txt|reward\.json|native_label|native_score)\b"
)
RUN_SPECIFIC_RE = re.compile(
    r"(?ix)(/jobs/|/trials/|trial[_ -]?id|released[_ -]?label[_ -]?value|"
    r"the\s+agent\s+(?:succeeded|failed)|this\s+record\s+(?:passed|failed))"
)
CONFLICT_RE = re.compile(r"(?i)\bbenchmark\s+conflict\b")
CONFLICT_EXCLUSION_RE = re.compile(
    r"(?ix)(?:"
    r"\b(?:not|never|without|rather\s+than|independent\s+of|does\s+not|"
    r"doesn't|cannot|can't|must\s+not)\b[^.\n]{0,140}\bbenchmark\s+conflict\b"
    r"|\bbenchmark\s+conflict\b[^.\n]{0,100}\b(?:does\s+not|doesn't|"
    r"cannot|can't|is\s+not|isn't|not)\b"
    r")"
)
GAP_RE = re.compile(
    r"(?ix)\b(does\s+not|do\s+not|not\s+checked|not\s+enforced|not\s+required|"
    r"not\s+(?:fully\s+)?operationalized|not\s+part|never|only|merely|rather\s+than|"
    r"instead\s+of|ignores?|without\s+(?:checking|verifying|proving)|omits?|outside|"
    r"beyond|weaker|gap|unverified|doesn't|isn't)\b"
)
TASK_AUTHORITY_PATH_RE = re.compile(
    r"^(?:official/(?:instruction\.md|README\.md|task\.toml)|case_packet\.md)$"
)
EVALUATOR_PATH_RE = re.compile(r"^(?:official/tests/|derived/evaluator_projection\.json$)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object in {path}")
            rows.append(value)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def iter_text(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from iter_text(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_text(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def support_paths(value: Any) -> list[str]:
    output: list[str] = []
    if isinstance(value, Mapping):
        support = value.get("support")
        if isinstance(support, list):
            output.extend(str(item).split("::", 1)[0] for item in support)
        for child in value.values():
            output.extend(support_paths(child))
    elif isinstance(value, list):
        for child in value:
            output.extend(support_paths(child))
    return output


def artifact_names(checklist: Mapping[str, Any]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    native = checklist.get("native")
    native = native if isinstance(native, Mapping) else {}
    for index, item in enumerate(native.get("decisive_artifacts", []) or []):
        if isinstance(item, Mapping):
            output.append((f"native.decisive_artifacts[{index}]", str(item.get("artifact") or "")))
    stronger = checklist.get("stronger")
    stronger = stronger if isinstance(stronger, Mapping) else {}
    for index, condition in enumerate(stronger.get("additional_conditions", []) or []):
        if not isinstance(condition, Mapping):
            continue
        for artifact_index, item in enumerate(condition.get("decisive_artifacts", []) or []):
            if isinstance(item, Mapping):
                output.append(
                    (
                        f"stronger.additional_conditions[{index}].decisive_artifacts[{artifact_index}]",
                        str(item.get("artifact") or ""),
                    )
                )
    return output


def inventory_match(name: str, inventory: list[str]) -> bool:
    normalized = name.replace("`", "").replace("\\", "/").lower()
    for pattern in inventory:
        candidate = str(pattern).lower()
        if candidate in normalized:
            return True
        if candidate.endswith("**") and candidate[:-2] in normalized:
            return True
        if candidate.endswith("*") and candidate[:-1] in normalized:
            return True
    return False


def decision_scope(checklist: Mapping[str, Any]) -> dict[str, Any]:
    native = checklist.get("native")
    stronger = checklist.get("stronger")
    return {
        "native": native if isinstance(native, Mapping) else {},
        "stronger": stronger if isinstance(stronger, Mapping) else {},
    }


def label_leaks(checklist: Mapping[str, Any]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for path, text in iter_text(decision_scope(checklist)):
        if FINAL_LABEL_TEXT_RE.search(text) and not LABEL_EXCLUSION_RE.search(text):
            output.append({"path": path, "text": text})
    return output


def replace_label_path_mentions(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: replace_label_path_mentions(child) for key, child in value.items()}
    if isinstance(value, list):
        return [replace_label_path_mentions(child) for child in value]
    if isinstance(value, str):
        return LABEL_PATH_RE.sub("final evaluator value", value)
    return value


def strip_support_values(value: Any) -> Any:
    """Preserve body structure while treating only support lists as mutable."""

    if isinstance(value, Mapping):
        return {
            str(key): "<SUPPORT-REPAIRED>" if key == "support" else strip_support_values(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [strip_support_values(child) for child in value]
    return value


def packet_cases() -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for benchmark, root in PACKET_ROOTS.items():
        for packet_path in sorted(root.glob("*/case_packet.md")):
            case_id = packet_path.parent.name
            if case_id in cases:
                raise RuntimeError(f"duplicate case ID across benchmark packets: {case_id}")
            cases[case_id] = {
                "benchmark": benchmark,
                "packet_path": packet_path,
                "packet_json_path": packet_path.with_suffix(".json"),
            }
    if len(cases) != 202:
        raise RuntimeError(f"expected 202 case packets, found {len(cases)}")
    return cases


def validation_errors(
    checklist: Mapping[str, Any],
    *,
    case_id: str,
    case: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    packet_path = Path(case["packet_path"])
    packet_json = load_json(Path(case["packet_json_path"]))
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(dict(checklist)), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"schema:{location}: {error.message}")

    task = packet_json["task"]
    expected_identity = {
        "case_unit_id": task["case_unit_id"],
        "domain": case["benchmark"],
        "task_id": task["task_id"],
    }
    for field, expected in expected_identity.items():
        if checklist.get(field) != expected:
            errors.append(f"identity:{field}: expected {expected!r}, got {checklist.get(field)!r}")

    packet_text = packet_path.read_text(encoding="utf-8")
    allowed = case_packet_support_paths(packet_text)
    errors.extend(
        "guardrail:" + item
        for item in collect_checklist_guardrail_violations(
            dict(checklist), allowed_source_paths=allowed
        )
    )
    try:
        validate_support_pointers(dict(checklist), packet_path)
    except Exception as exc:
        errors.append(f"pointers:{type(exc).__name__}: {exc}")
    try:
        validate_packet_required_stronger_conditions(dict(checklist), packet_path)
    except Exception as exc:
        errors.append(f"packet_stronger:{type(exc).__name__}: {exc}")

    for leak in label_leaks(checklist):
        errors.append(f"label_leak:{leak['path']}")
    for path, text in iter_text(checklist):
        if RUN_SPECIFIC_RE.search(text):
            errors.append(f"run_specific_language:{path}")
    for path, text in iter_text(checklist):
        if CONFLICT_RE.search(text) and not CONFLICT_EXCLUSION_RE.search(text):
            errors.append(f"conflict_conflated_with_checklist:{path}")

    inventory = list(packet_json["artifact_inventory"]["retained_execution_artifact_types"])
    for path, name in artifact_names(checklist):
        if not inventory_match(name, inventory):
            errors.append(f"artifact_not_in_packet_inventory:{path}:{name}")

    native = checklist.get("native")
    native = native if isinstance(native, Mapping) else {}
    user_goal_paths = support_paths(native.get("user_goal", {}))
    if not any(TASK_AUTHORITY_PATH_RE.search(path) for path in user_goal_paths):
        errors.append("native_user_goal_missing_official_task_support")
    native_rule_paths = support_paths(
        {
            key: native.get(key)
            for key in ("benchmark_success", "checked_by", "success_if", "fail_if")
        }
    )
    if not any(EVALUATOR_PATH_RE.search(path) for path in native_rule_paths):
        errors.append("native_rules_missing_evaluator_or_oracle_support")

    stronger = checklist.get("stronger")
    stronger = stronger if isinstance(stronger, Mapping) else {}
    for index, condition in enumerate(stronger.get("additional_conditions", []) or []):
        if not isinstance(condition, Mapping):
            errors.append(f"stronger_not_mapping:{index}")
            continue
        pointers = support_paths(condition)
        if not any(TASK_AUTHORITY_PATH_RE.search(path) for path in pointers):
            errors.append(f"stronger_missing_task_authority:{index}")
        combined = f"{condition.get('text', '')} {condition.get('rationale', '')}"
        if not GAP_RE.search(combined):
            errors.append(f"stronger_measurement_gap_not_explicit:{index}")
    return sorted(set(errors))


def write_checklist(destination: Path, checklist: Mapping[str, Any]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    write_json(destination / "checklist.json", checklist)
    (destination / "checklist.yaml").write_text(
        yaml.safe_dump(dict(checklist), sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    cases = packet_cases()
    semantic_records = load_jsonl(SEMANTIC_RECORDS)
    if len(semantic_records) != 202:
        raise RuntimeError(f"expected 202 semantic records, found {len(semantic_records)}")
    by_case = {str(row["case_unit_id"]): row for row in semantic_records}
    if set(by_case) != set(cases):
        raise RuntimeError("semantic review / packet case sets differ")

    records: list[dict[str, Any]] = []
    for case_id in sorted(cases):
        case = cases[case_id]
        semantic = by_case[case_id]
        benchmark = str(case["benchmark"])
        if semantic.get("benchmark") != benchmark:
            raise RuntimeError(f"semantic benchmark mismatch for {case_id}")
        decision = semantic.get("decision")
        source_dir: Path
        checklist: dict[str, Any]
        source_kind: str
        provenance: dict[str, Any]
        source_validation: list[str] = []

        if decision == "accept":
            source_kind = "original_accepted_by_outcome_blind_review"
            source_dir = SOURCE_DRAFT_ROOT / case_id
            checklist = load_yaml(source_dir / "checklist.yaml")
            json_body = load_json(source_dir / "checklist.json")
            if checklist != json_body:
                source_validation.append("original_yaml_json_semantic_mismatch")
            review_path = SEMANTIC_REVIEW_ROOT / case_id / "review.json"
            review = load_json(review_path)
            if review.get("decision") != "accept":
                source_validation.append("review_receipt_is_not_accept")
            provenance = {
                "schema_version": "tb21_deepswe11_repair_v2_case_provenance/v1",
                "case_unit_id": case_id,
                "benchmark": benchmark,
                "source_kind": source_kind,
                "source_boundary": [
                    "case packet and official raw sources",
                    "frozen original checklist",
                    "outcome-blind semantic review receipt",
                ],
                "excluded_inputs": [
                    "agent outcomes", "trajectory contents", "execution-artifact contents",
                    "per-record reward/result/label values", "evidence scores", "benchmark-conflict records",
                ],
                "original_checklist_sha256": sha256_file(source_dir / "checklist.yaml"),
                "semantic_review_path": str(review_path.relative_to(REPO_ROOT)),
                "semantic_review_sha256": sha256_file(review_path),
                "semantic_review_decision": "accept",
                "fresh_post_repair_model_review": "not_needed; checklist carried forward unchanged",
            }
        elif decision == "revise":
            source_kind = "outcome_blind_reviewer_corrected_body_with_pointer_repair"
            source_dir = CANDIDATE_ROOT / case_id
            checklist = load_yaml(source_dir / "checklist.yaml")
            json_body = load_json(source_dir / "checklist.json")
            if checklist != json_body:
                source_validation.append("candidate_yaml_json_semantic_mismatch")
            materialization = load_json(source_dir / "repair_provenance.json")
            if materialization.get("deterministic_validation_errors"):
                source_validation.append("candidate_materialization_has_validation_errors")
            original = load_yaml(SOURCE_DRAFT_ROOT / case_id / "checklist.yaml")
            raw_candidate = ((semantic.get("revision_validation") or {}).get("candidate"))
            if not isinstance(raw_candidate, Mapping):
                source_validation.append("semantic_record_has_no_complete_reviewer_candidate")
                raw_candidate = {}
            expected_body = copy.deepcopy(dict(raw_candidate))
            for field in ("schema_version", "case_unit_id", "domain", "task_id"):
                expected_body[field] = original.get(field)
            expected_body = replace_label_path_mentions(expected_body)
            if strip_support_values(expected_body) != strip_support_values(checklist):
                source_validation.append("unexpected_non_pointer_change_from_reviewer_corrected_body")
            if materialization.get("reviewer_candidate_sha256") != json_sha256(raw_candidate):
                source_validation.append("reviewer_candidate_hash_mismatch")
            if materialization.get("original_checklist_sha256") != sha256_file(
                SOURCE_DRAFT_ROOT / case_id / "checklist.yaml"
            ):
                source_validation.append("materialization_original_hash_mismatch")
            if materialization.get("case_packet_sha256") != sha256_file(Path(case["packet_path"])):
                source_validation.append("materialization_packet_hash_mismatch")
            provenance = {
                "schema_version": "tb21_deepswe11_repair_v2_case_provenance/v1",
                "case_unit_id": case_id,
                "benchmark": benchmark,
                "source_kind": source_kind,
                "source_boundary": [
                    "case packet and official raw sources",
                    "frozen original checklist",
                    "prior independent outcome-blind review and its complete corrected body",
                    "deterministic support-pointer repair against that case packet",
                ],
                "excluded_inputs": [
                    "agent outcomes", "trajectory contents", "execution-artifact contents",
                    "per-record reward/result/label values", "evidence scores", "benchmark-conflict records",
                ],
                "original_checklist_sha256": sha256_file(
                    SOURCE_DRAFT_ROOT / case_id / "checklist.yaml"
                ),
                "semantic_review_record": str(SEMANTIC_RECORDS.relative_to(REPO_ROOT)),
                "reviewer_candidate_sha256": json_sha256(raw_candidate),
                "materialization_provenance_path": str(
                    (source_dir / "repair_provenance.json").relative_to(REPO_ROOT)
                ),
                "materialization_provenance_sha256": sha256_file(
                    source_dir / "repair_provenance.json"
                ),
                "pointer_repair_action_count": len(
                    materialization.get("pointer_repair_actions", [])
                ),
                "reviewer_correction_closure": (
                    "complete corrected body preserved apart from canonical identity, "
                    "support-pointer repair, and final-label filename normalization"
                ),
                "fresh_post_repair_model_review": (
                    "not run in this environment; this is a deterministic closure audit, "
                    "not a claim of a second independent model review"
                ),
            }
        else:
            raise RuntimeError(f"unexpected semantic decision for {case_id}: {decision!r}")

        errors = [*source_validation, *validation_errors(
            checklist, case_id=case_id, case=case, schema=schema
        )]
        destination = OUTPUT_ROOT / case_id
        write_checklist(destination, checklist)
        provenance["final_checklist_sha256"] = sha256_file(destination / "checklist.yaml")
        provenance["case_packet_sha256"] = sha256_file(Path(case["packet_path"]))
        provenance["deterministic_validation_errors"] = sorted(set(errors))
        write_json(destination / "v2_source_provenance.json", provenance)
        records.append(
            {
                "benchmark": benchmark,
                "case_unit_id": case_id,
                "source_kind": source_kind,
                "prior_semantic_review_decision": decision,
                "status": "pass" if not errors else "fail",
                "validation_errors": sorted(set(errors)),
                "checklist_path": str((destination / "checklist.yaml").relative_to(REPO_ROOT)),
                "checklist_sha256": provenance["final_checklist_sha256"],
                "provenance_sha256": sha256_file(destination / "v2_source_provenance.json"),
                "case_packet_sha256": provenance["case_packet_sha256"],
            }
        )

    records_path = REPAIR_ROOT / "v2_deterministic_audit_records.jsonl"
    with records_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    counts = Counter(record["status"] for record in records)
    by_benchmark: dict[str, dict[str, int]] = {}
    for benchmark in PACKET_ROOTS:
        subset = [record for record in records if record["benchmark"] == benchmark]
        by_benchmark[benchmark] = {
            "case_count": len(subset),
            "pass_count": sum(record["status"] == "pass" for record in subset),
            "fail_count": sum(record["status"] != "pass" for record in subset),
            "carried_forward_accept_count": sum(
                record["source_kind"] == "original_accepted_by_outcome_blind_review"
                for record in subset
            ),
            "reviewer_corrected_count": sum(
                record["source_kind"]
                == "outcome_blind_reviewer_corrected_body_with_pointer_repair"
                for record in subset
            ),
        }
    manifest = {
        "schema_version": "tb21_deepswe11_repair_v2_lock_manifest/v1",
        "case_count": len(records),
        "pre_run_boundary": (
            "case packets, original frozen drafts, outcome-blind review bodies, and "
            "deterministic repaired candidates only; no outcomes, labels, scores, or run contents"
        ),
        "records": records,
    }
    write_json(REPAIR_ROOT / "v2_lock_manifest.json", manifest)
    summary = {
        "schema_version": "tb21_deepswe11_repair_v2_deterministic_audit/v1",
        "status": "pass" if counts["fail"] == 0 else "fail",
        "case_count": len(records),
        "pass_count": counts["pass"],
        "fail_count": counts["fail"],
        "status_counts": dict(counts),
        "benchmark_counts": by_benchmark,
        "frozen_draft_root": str(OUTPUT_ROOT.relative_to(REPO_ROOT)),
        "audit_boundary": manifest["pre_run_boundary"],
        "review_scope": (
            "70 unchanged prior-accepted checklists plus 132 outcome-blind reviewer-corrected "
            "bodies; all 202 received fresh deterministic validation. The repaired 132 have "
            "not been sent to a second independent model reviewer in this environment."
        ),
    }
    write_json(REPAIR_ROOT / "v2_deterministic_audit_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
