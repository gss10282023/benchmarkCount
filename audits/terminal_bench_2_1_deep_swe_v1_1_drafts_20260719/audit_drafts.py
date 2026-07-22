#!/usr/bin/env python3
"""Outcome-blind audit for the Terminal-Bench 2.1 and DeepSWE v1.1 drafts.

The audit reads only case packets, draft outputs, drafting provenance, and frozen
schemas/prompts.  It deliberately does not read benchmark runs, agent outcomes,
per-record rewards, released labels, or evidence-scoring outputs.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
MINIMAL_ROOT = REPO_ROOT / "neurips_ed_track_minimal"
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


AUDIT_ROOT = Path(__file__).resolve().parent
DEFAULT_DRAFT_ROOT = (
    REPO_ROOT
    / "results/drafts/terminal_bench_2_1_deep_swe_v1_1_gpt54_high_c32_20260719"
)
PACKET_ROOTS = {
    "terminal_bench_2_1": REPO_ROOT / "experiments/case_packets/terminal_bench_2_1",
    "deep_swe_v1_1": REPO_ROOT / "experiments/case_packets/deep_swe_v1_1",
}
SCHEMA_PATH = MINIMAL_ROOT / "schemas/case_checklist.schema.json"
BASE_PROMPT_PATH = MINIMAL_ROOT / "prompts/draft_case_checklist.prompt.md"
SUPPLEMENT_PATH = AUDIT_ROOT / "draft_system_design_supplement.md"
TARGETED_SUPPLEMENT_PATH = AUDIT_ROOT / "count_dataset_tokens_pointer_supplement.md"
TARGETED_CASE_ID = "count-dataset-tokens"

FINAL_LABEL_BASENAMES = frozenset(
    {
        "result.json",
        "reward.txt",
        "reward.json",
        "native_label",
        "native_score",
    }
)
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
CONFLICT_RE = re.compile(r"(?i)\bbenchmark\s+conflict\b")
RUN_SPECIFIC_RE = re.compile(
    r"(?ix)(/jobs/|/trials/|trial[_ -]?id|released[_ -]?label[_ -]?value|"
    r"the\s+agent\s+(?:succeeded|failed)|this\s+record\s+(?:passed|failed))"
)
GAP_RE = re.compile(
    r"(?ix)\b(does\s+not|do\s+not|not\s+checked|not\s+enforced|not\s+required|"
    r"not\s+(?:fully\s+)?operationalized|not\s+part|never|only|merely|rather\s+than|"
    r"instead\s+of|ignores?|"
    r"without\s+(?:checking|verifying|proving)|omits?|outside|beyond|weaker|gap|"
    r"unverified|doesn't|isn't)\b"
)
TASK_AUTHORITY_PATH_RE = re.compile(
    r"^(?:official/(?:instruction\.md|README\.md|task\.toml)|case_packet\.md)$"
)
EVALUATOR_PATH_RE = re.compile(
    r"^(?:official/tests/|derived/evaluator_projection\.json$)"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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
    paths: list[str] = []
    if isinstance(value, Mapping):
        support = value.get("support")
        if isinstance(support, list):
            for pointer in support:
                paths.append(str(pointer).split("::", 1)[0])
        for child in value.values():
            paths.extend(support_paths(child))
    elif isinstance(value, list):
        for child in value:
            paths.extend(support_paths(child))
    return paths


def rule_scope(checklist: Mapping[str, Any]) -> dict[str, Any]:
    native = checklist.get("native")
    native = native if isinstance(native, Mapping) else {}
    stronger = checklist.get("stronger")
    stronger = stronger if isinstance(stronger, Mapping) else {}
    return {
        "native_decisive_artifacts": native.get("decisive_artifacts", []),
        "native_success_if": native.get("success_if", []),
        "native_fail_if": native.get("fail_if", []),
        "native_undecided_if": native.get("undecided_if", []),
        "stronger": stronger,
    }


def final_label_leaks(checklist: Mapping[str, Any]) -> list[dict[str, str]]:
    leaks: list[dict[str, str]] = []
    for location, text in iter_text(rule_scope(checklist)):
        # An explicit statement that a final label/reward is excluded is part of
        # the intended evidence boundary, not use of that label as evidence.
        if FINAL_LABEL_TEXT_RE.search(text) and not LABEL_EXCLUSION_RE.search(text):
            leaks.append({"path": location, "text": text})
    return leaks


def artifact_names(checklist: Mapping[str, Any]) -> list[tuple[str, str]]:
    names: list[tuple[str, str]] = []
    native = checklist.get("native")
    native = native if isinstance(native, Mapping) else {}
    for index, item in enumerate(native.get("decisive_artifacts", []) or []):
        if isinstance(item, Mapping):
            names.append((f"native.decisive_artifacts[{index}]", str(item.get("artifact") or "")))
    stronger = checklist.get("stronger")
    stronger = stronger if isinstance(stronger, Mapping) else {}
    for index, condition in enumerate(stronger.get("additional_conditions", []) or []):
        if not isinstance(condition, Mapping):
            continue
        for artifact_index, item in enumerate(condition.get("decisive_artifacts", []) or []):
            if isinstance(item, Mapping):
                names.append(
                    (
                        f"stronger.additional_conditions[{index}].decisive_artifacts[{artifact_index}]",
                        str(item.get("artifact") or ""),
                    )
                )
    return names


def inventory_match(name: str, inventory: list[str]) -> bool:
    normalized = name.replace("`", "").replace("\\", "/")
    lowered = normalized.lower()
    for pattern in inventory:
        candidate = pattern.lower()
        if candidate in lowered:
            return True
        if fnmatch.fnmatch(lowered, candidate):
            return True
        prefix = candidate.removesuffix("**").removesuffix("*")
        if prefix and prefix in lowered:
            return True
    return False


def stronger_findings(checklist: Mapping[str, Any]) -> list[dict[str, Any]]:
    stronger = checklist.get("stronger")
    stronger = stronger if isinstance(stronger, Mapping) else {}
    findings: list[dict[str, Any]] = []
    for index, raw in enumerate(stronger.get("additional_conditions", []) or []):
        condition = raw if isinstance(raw, Mapping) else {}
        pointers = support_paths(condition)
        rationale = str(condition.get("rationale") or "")
        text = str(condition.get("text") or "")
        findings.append(
            {
                "index": index,
                "id": str(condition.get("id") or ""),
                "has_task_authority_support": any(
                    TASK_AUTHORITY_PATH_RE.search(pointer) for pointer in pointers
                ),
                "has_evaluator_gap_support": any(
                    EVALUATOR_PATH_RE.search(pointer) for pointer in pointers
                ),
                "gap_explicit": bool(GAP_RE.search(f"{text} {rationale}")),
                "mentions_benchmark_conflict": bool(
                    CONFLICT_RE.search(f"{text} {rationale}")
                ),
                "support_paths": sorted(set(pointers)),
            }
        )
    return findings


def deep_semantic_signals(checklist: Mapping[str, Any]) -> list[str]:
    text = " ".join(value for _, value in iter_text(checklist)).lower()
    signals: list[str] = []
    requirements = {
        "missing_f2p_semantics": ("fail-to-pass" in text or "f2p" in text),
        "missing_p2p_semantics": ("pass-to-pass" in text or "p2p" in text),
        "missing_nonempty_f2p_rule": (
            "non-empty" in text or "nonempty" in text or "at least one" in text
        ),
        "missing_missing_test_failure_rule": "missing" in text,
        "missing_skipped_test_failure_rule": "skipped" in text,
        "missing_duplicate_worst_status_rule": (
            "duplicate" in text and "worst" in text
        ),
    }
    for code, present in requirements.items():
        if not present:
            signals.append(code)

    stronger = checklist.get("stronger")
    stronger_text = " ".join(
        value for _, value in iter_text(stronger if isinstance(stronger, Mapping) else {})
    ).lower()
    if "branch" not in stronger_text:
        signals.append("official_new_branch_requirement_not_in_stronger")
    if "commit" not in stronger_text:
        signals.append("official_commit_everything_requirement_not_in_stronger")
    return signals


def packet_case_map() -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for benchmark, root in PACKET_ROOTS.items():
        for packet_path in sorted(root.glob("*/case_packet.md")):
            case_id = packet_path.parent.name
            if case_id in cases:
                raise RuntimeError(f"duplicate case id across benchmarks: {case_id}")
            cases[case_id] = {
                "benchmark": benchmark,
                "packet_path": packet_path,
                "packet_json_path": packet_path.with_suffix(".json"),
            }
    return cases


def schema_errors(checklist: Mapping[str, Any], validator: Draft202012Validator) -> list[str]:
    errors = sorted(validator.iter_errors(dict(checklist)), key=lambda item: list(item.absolute_path))
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def audit_one(
    case_id: str,
    case: Mapping[str, Any],
    draft_root: Path,
    validator: Draft202012Validator,
) -> dict[str, Any]:
    packet_path = Path(case["packet_path"])
    packet_json = load_json(Path(case["packet_json_path"]))
    draft_dir = draft_root / case_id
    checklist_path = draft_dir / "checklist.yaml"
    checklist_json_path = draft_dir / "checklist.json"
    llm_call_path = draft_dir / "llm_call.json"
    hard_failures: list[str] = []
    review_signals: list[str] = []

    required = [checklist_path, checklist_json_path, llm_call_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        return {
            "benchmark": case["benchmark"],
            "case_unit_id": case_id,
            "status": "fail",
            "hard_failures": ["missing_required_draft_files"],
            "missing_files": missing,
            "review_signals": [],
            "stronger_conditions": [],
            "stronger_condition_count": 0,
            "benchmark_semantic_signals": [],
            "checklist_sha256": None,
            "checklist_json_sha256": None,
            "llm_call_sha256": None,
            "case_packet_sha256": sha256_file(packet_path),
        }

    checklist = load_yaml(checklist_path)
    checklist_json = load_json(checklist_json_path)
    llm_call = load_json(llm_call_path)
    errors = schema_errors(checklist, validator)
    if errors:
        hard_failures.append("schema_validation_failed")
    if checklist != checklist_json:
        hard_failures.append("yaml_json_semantic_mismatch")

    task = packet_json["task"]
    expected_identity = {
        "case_unit_id": task["case_unit_id"],
        "domain": case["benchmark"],
        "task_id": task["task_id"],
    }
    identity_mismatches = {
        key: {"expected": expected, "actual": checklist.get(key)}
        for key, expected in expected_identity.items()
        if checklist.get(key) != expected
    }
    if identity_mismatches:
        hard_failures.append("case_identity_mismatch")

    packet_text = packet_path.read_text(encoding="utf-8")
    guardrails = collect_checklist_guardrail_violations(
        checklist,
        allowed_source_paths=case_packet_support_paths(packet_text),
    )
    if guardrails:
        hard_failures.append("deterministic_guardrail_failed")
    pointer_errors: list[str] = []
    try:
        validate_support_pointers(checklist, packet_path)
        validate_packet_required_stronger_conditions(checklist, packet_path)
    except Exception as exc:  # keep a per-case ledger instead of aborting the batch
        pointer_errors.append(f"{type(exc).__name__}: {exc}")
        hard_failures.append("source_pointer_validation_failed")

    llm_config = {
        "provider": llm_call.get("provider"),
        "model": llm_call.get("model"),
        "reasoning_effort": (
            (llm_call.get("response_metadata") or {}).get("reasoning_effort")
            if isinstance(llm_call.get("response_metadata"), Mapping)
            else None
        ),
        "phase": llm_call.get("phase"),
        "case_unit_id": llm_call.get("case_unit_id"),
    }
    expected_llm = {
        "provider": "codex_cli",
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "phase": "draft",
        "case_unit_id": case_id,
    }
    llm_mismatches = {
        key: {"expected": expected, "actual": llm_config.get(key)}
        for key, expected in expected_llm.items()
        if llm_config.get(key) != expected
    }
    if llm_mismatches:
        hard_failures.append("draft_llm_config_mismatch")

    label_leaks = final_label_leaks(checklist)
    if label_leaks:
        hard_failures.append("released_label_used_in_decision_scope")

    run_specific_mentions = [
        {"path": location, "text": text}
        for location, text in iter_text(checklist)
        if RUN_SPECIFIC_RE.search(text)
    ]
    if run_specific_mentions:
        hard_failures.append("run_specific_or_outcome_language")

    inventory = list(
        packet_json["artifact_inventory"]["retained_execution_artifact_types"]
    )
    artifacts = artifact_names(checklist)
    artifact_inventory_signals = [
        {"path": location, "artifact": name}
        for location, name in artifacts
        if not inventory_match(name, inventory)
    ]
    if artifact_inventory_signals:
        review_signals.append("decisive_artifact_not_mechanically_matched_to_inventory")

    stronger = stronger_findings(checklist)
    if any(not item["has_task_authority_support"] for item in stronger):
        hard_failures.append("stronger_missing_official_task_user_or_policy_support")
    if any(not item["gap_explicit"] for item in stronger):
        hard_failures.append("stronger_measurement_gap_not_explicit")
    if any(item["mentions_benchmark_conflict"] for item in stronger):
        hard_failures.append("stronger_conflated_with_benchmark_conflict")
    if any(not item["has_evaluator_gap_support"] for item in stronger):
        review_signals.append("stronger_evaluator_noncoverage_pointer_needs_review")

    native = checklist.get("native")
    native = native if isinstance(native, Mapping) else {}
    user_goal_paths = support_paths(native.get("user_goal", {}))
    if not any(TASK_AUTHORITY_PATH_RE.search(path) for path in user_goal_paths):
        hard_failures.append("native_user_goal_missing_official_task_support")
    native_rule_paths = support_paths(
        {
            key: native.get(key)
            for key in ("benchmark_success", "checked_by", "success_if", "fail_if")
        }
    )
    if not any(EVALUATOR_PATH_RE.search(path) for path in native_rule_paths):
        hard_failures.append("native_rules_missing_evaluator_or_oracle_support")

    benchmark_semantic_signals: list[str] = []
    if case["benchmark"] == "deep_swe_v1_1":
        benchmark_semantic_signals = deep_semantic_signals(checklist)
        review_signals.extend(benchmark_semantic_signals)

    all_text = " ".join(value for _, value in iter_text(checklist))
    if CONFLICT_RE.search(all_text):
        hard_failures.append("checklist_mentions_benchmark_conflict")

    hard_failures = sorted(set(hard_failures))
    review_signals = sorted(set(review_signals))
    return {
        "benchmark": case["benchmark"],
        "case_unit_id": case_id,
        "status": "pass" if not hard_failures else "fail",
        "hard_failures": hard_failures,
        "review_signals": review_signals,
        "schema_errors": errors,
        "identity_mismatches": identity_mismatches,
        "guardrail_violations": guardrails,
        "pointer_errors": pointer_errors,
        "llm_config": llm_config,
        "llm_mismatches": llm_mismatches,
        "released_label_leaks": label_leaks,
        "run_specific_mentions": run_specific_mentions,
        "artifact_inventory_signals": artifact_inventory_signals,
        "stronger_conditions": stronger,
        "stronger_condition_count": len(stronger),
        "benchmark_semantic_signals": benchmark_semantic_signals,
        "checklist_sha256": sha256_file(checklist_path),
        "checklist_json_sha256": sha256_file(checklist_json_path),
        "llm_call_sha256": sha256_file(llm_call_path),
        "case_packet_sha256": sha256_file(packet_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft-root", type=Path, default=DEFAULT_DRAFT_ROOT)
    args = parser.parse_args()
    draft_root = args.draft_root.resolve()
    cases = packet_case_map()
    if len(cases) != 202:
        raise RuntimeError(f"expected 202 packet cases, found {len(cases)}")

    draft_ids = {path.parent.name for path in draft_root.glob("*/checklist.yaml")}
    expected_ids = set(cases)
    missing_drafts = sorted(expected_ids - draft_ids)
    unexpected_drafts = sorted(draft_ids - expected_ids)

    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    records = [
        audit_one(case_id, cases[case_id], draft_root, validator)
        for case_id in sorted(expected_ids)
    ]
    hard_failure_records = [row for row in records if row["status"] != "pass"]
    signal_records = [row for row in records if row["review_signals"]]

    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    jsonl(AUDIT_ROOT / "audit_records.jsonl", records)
    columns = [
        "benchmark",
        "case_unit_id",
        "status",
        "hard_failures",
        "review_signals",
        "stronger_condition_count",
        "checklist_sha256",
    ]
    with (AUDIT_ROOT / "audit_report.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    **{key: record.get(key) for key in columns},
                    "hard_failures": ";".join(record["hard_failures"]),
                    "review_signals": ";".join(record["review_signals"]),
                }
            )

    failure_counts = Counter(
        code for record in records for code in record["hard_failures"]
    )
    signal_counts = Counter(
        code for record in records for code in record["review_signals"]
    )
    benchmark_counts: dict[str, dict[str, int]] = {}
    for benchmark in PACKET_ROOTS:
        rows = [row for row in records if row["benchmark"] == benchmark]
        benchmark_counts[benchmark] = {
            "expected": len(rows),
            "passed_hard_checks": sum(row["status"] == "pass" for row in rows),
            "failed_hard_checks": sum(row["status"] != "pass" for row in rows),
            "with_review_signals": sum(bool(row["review_signals"]) for row in rows),
            "stronger_condition_count": sum(row["stronger_condition_count"] for row in rows),
        }

    summary = {
        "schema_version": "tb21_deepswe11_draft_outcome_blind_audit/v1",
        "status": (
            "pass"
            if not hard_failure_records and not missing_drafts and not unexpected_drafts
            else "fail"
        ),
        "audit_boundary": (
            "case packets, draft checklists, draft sidecars, frozen schema/prompt only; "
            "no agent outcomes, per-record rewards, released labels, or evidence scores read"
        ),
        "draft_root": str(draft_root.relative_to(REPO_ROOT)),
        "expected_case_count": len(expected_ids),
        "observed_checklist_count": len(draft_ids),
        "missing_draft_ids": missing_drafts,
        "unexpected_draft_ids": unexpected_drafts,
        "passed_hard_check_count": sum(row["status"] == "pass" for row in records),
        "failed_hard_check_count": len(hard_failure_records),
        "with_review_signal_count": len(signal_records),
        "hard_failure_code_counts": dict(sorted(failure_counts.items())),
        "review_signal_code_counts": dict(sorted(signal_counts.items())),
        "benchmarks": benchmark_counts,
        "draft_config_required": {
            "provider": "codex_cli",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "max_parallel": 32,
        },
        "frozen_inputs": {
            "checklist_schema": str(SCHEMA_PATH.relative_to(REPO_ROOT)),
            "checklist_schema_sha256": sha256_file(SCHEMA_PATH),
            "base_draft_prompt": str(BASE_PROMPT_PATH.relative_to(REPO_ROOT)),
            "base_draft_prompt_sha256": sha256_file(BASE_PROMPT_PATH),
            "draft_supplement": str(SUPPLEMENT_PATH.relative_to(REPO_ROOT)),
            "draft_supplement_sha256": sha256_file(SUPPLEMENT_PATH),
            "targeted_pointer_supplement": str(
                TARGETED_SUPPLEMENT_PATH.relative_to(REPO_ROOT)
            ),
            "targeted_pointer_supplement_sha256": sha256_file(
                TARGETED_SUPPLEMENT_PATH
            ),
            "targeted_pointer_supplement_case_id": TARGETED_CASE_ID,
        },
    }
    (AUDIT_ROOT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lock_manifest = {
        "schema_version": "case_checklist_draft_lock_manifest/v1",
        "case_count": len(records),
        "draft_root": str(draft_root.relative_to(REPO_ROOT)),
        "generation_receipts": {
            name: sha256_file(draft_root / name)
            for name in (
                "first_pass_batch_summary.json",
                "first_pass_batch_results.jsonl",
                "first_pass_systemd_journal.log",
                "retry1_batch_summary.json",
                "retry1_batch_results.jsonl",
                "retry1_systemd_journal.log",
                "retry2_batch_summary.json",
                "retry2_batch_results.jsonl",
                "retry2_systemd_journal.log",
                "targeted_count_dataset_tokens_batch_summary.json",
                "targeted_count_dataset_tokens_batch_results.jsonl",
                "targeted_count_dataset_tokens_systemd_journal.log",
            )
            if (draft_root / name).is_file()
        },
        "records": [
            {
                "benchmark": record["benchmark"],
                "case_unit_id": record["case_unit_id"],
                "case_packet_sha256": record.get("case_packet_sha256"),
                "checklist_sha256": record.get("checklist_sha256"),
                "llm_call_sha256": record.get("llm_call_sha256"),
                "audit_status": record["status"],
                "review_signals": record.get("review_signals", []),
                "draft_prompt_variant": (
                    "targeted_pointer_supplement"
                    if record["case_unit_id"] == TARGETED_CASE_ID
                    else "main_system_design_supplement"
                ),
            }
            for record in records
        ],
    }
    (AUDIT_ROOT / "draft_lock_manifest.json").write_text(
        json.dumps(lock_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
