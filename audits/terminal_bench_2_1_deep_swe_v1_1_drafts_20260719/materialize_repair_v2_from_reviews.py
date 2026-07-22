#!/usr/bin/env python3
"""Materialize outcome-blind reviewer corrections as deterministic v2 candidates.

The prior independent reviewer supplied a complete corrected checklist body for
every `revise` case.  Some of those bodies were rejected only because source
pointers used human-friendly but non-resolving syntax.  This script preserves the
reviewer's substantive body, replaces only unresolvable support lists with the
matching already-valid support list from the frozen original draft (or a narrow
packet-local fallback), and fail-closes on schema/guardrail/pointer errors.

No execution outcome, run artifact content, per-record reward/label, score, or
benchmark-conflict material is read.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator


AUDIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AUDIT_ROOT.parents[1]
SOURCE_DRAFT_ROOT = AUDIT_ROOT / "drafts"
OUTPUT_ROOT = AUDIT_ROOT / "repair_v2" / "reviewer_repair_candidates"
PACKET_ROOTS = {
    "terminal_bench_2_1": REPO_ROOT / "experiments/case_packets/terminal_bench_2_1",
    "deep_swe_v1_1": REPO_ROOT / "experiments/case_packets/deep_swe_v1_1",
}
SCHEMA_PATH = REPO_ROOT / "neurips_ed_track_minimal/schemas/case_checklist.schema.json"

# Executing this file by absolute path makes Python put the audit directory,
# rather than the repository root, at the front of sys.path.  The benchmark
# helper modules intentionally live in a namespace package, so add the root
# explicitly instead of relying on the caller's working directory.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    case_packet_support_paths,
    collect_checklist_guardrail_violations,
)
from neurips_ed_track_minimal.scripts.checklist_validator import (  # noqa: E402
    validate_packet_required_stronger_conditions,
    validate_support_pointer,
    validate_support_pointers,
)


LABEL_PATH_RE = re.compile(
    r"(?ix)\b(?:result\.json|reward\.txt|reward\.json|native_label|native_score)\b"
)
INDEX_RE = re.compile(r"\[\d+\]")


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
        raise ValueError(f"expected YAML object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected object in {path}")
            rows.append(value)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def walk_support_lists(value: Any, prefix: str = "") -> Iterable[tuple[str, list[str]]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if key == "support" and isinstance(child, list):
                yield path, [str(item) for item in child]
            else:
                yield from walk_support_lists(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_support_lists(child, f"{prefix}[{index}]")


def get_at_path(value: Any, path: str) -> Any:
    current = value
    for token in path.split("."):
        if not token:
            continue
        match = re.fullmatch(r"([^\[]+)((?:\[\d+\])*)", token)
        if match is None:
            return None
        key, brackets = match.groups()
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
        for index_text in re.findall(r"\[(\d+)\]", brackets):
            if not isinstance(current, list) or int(index_text) >= len(current):
                return None
            current = current[int(index_text)]
    return current


def valid_pointers(case_packet: Path, pointers: Iterable[str]) -> list[str]:
    output: list[str] = []
    for pointer in pointers:
        try:
            validate_support_pointer(case_packet, pointer)
        except ValueError:
            continue
        output.append(pointer)
    return output


def original_support_fallbacks(original: Mapping[str, Any]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    exact = {path: pointers for path, pointers in walk_support_lists(original)}
    normalized: dict[str, list[str]] = {}
    for path, pointers in exact.items():
        normalized.setdefault(INDEX_RE.sub("[]", path), pointers)
    return exact, normalized


def packet_fallback(case_packet: Path, support_path: str) -> str:
    candidates: list[str]
    if ".user_goal.support" in support_path or support_path.startswith("stronger."):
        candidates = [
            "official/instruction.md::L 1",
            "case_packet.md::Official Task Summary",
            "case_packet.md::Benchmark Task Summary",
        ]
    elif ".decisive_artifacts" in support_path:
        candidates = [
            "case_packet.md::Available Artifact Inventory (types only; no per-record values)",
            "case_packet.md::Native Evaluator Semantics",
        ]
    else:
        candidates = [
            "case_packet.md::Native Evaluator Semantics",
            "case_packet.md::Measurement Boundary",
        ]
    for pointer in candidates:
        try:
            validate_support_pointer(case_packet, pointer)
            return pointer
        except ValueError:
            continue
    raise RuntimeError(f"no packet fallback pointer resolves for {case_packet}: {support_path}")


def replace_label_path_mentions(value: Any) -> Any:
    """Avoid treating named final result files as checklist evidence shorthand."""

    if isinstance(value, Mapping):
        return {key: replace_label_path_mentions(child) for key, child in value.items()}
    if isinstance(value, list):
        return [replace_label_path_mentions(child) for child in value]
    if isinstance(value, str):
        return LABEL_PATH_RE.sub("final evaluator value", value)
    return value


def repair_supports(
    candidate: dict[str, Any],
    *,
    original: Mapping[str, Any],
    case_packet: Path,
) -> list[dict[str, Any]]:
    exact, normalized = original_support_fallbacks(original)
    actions: list[dict[str, Any]] = []
    for support_path, pointers in list(walk_support_lists(candidate)):
        if valid_pointers(case_packet, pointers) == pointers:
            continue
        replacement = valid_pointers(case_packet, exact.get(support_path, []))
        source = "original_same_path"
        if not replacement:
            replacement = valid_pointers(case_packet, normalized.get(INDEX_RE.sub("[]", support_path), []))
            source = "original_same_field"
        if not replacement:
            replacement = [packet_fallback(case_packet, support_path)]
            source = "packet_local_fallback"
        parent_path = support_path.removesuffix(".support")
        parent = get_at_path(candidate, parent_path)
        if not isinstance(parent, dict):
            raise RuntimeError(f"could not resolve support parent: {support_path}")
        parent["support"] = replacement
        actions.append(
            {
                "support_path": support_path,
                "old": pointers,
                "new": replacement,
                "source": source,
            }
        )
    return actions


def validate_candidate(
    candidate: Mapping[str, Any], *, case_packet: Path, schema: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    validator = Draft202012Validator(schema)
    errors.extend(
        f"schema {'.'.join(str(item) for item in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(dict(candidate)), key=lambda error: list(error.absolute_path))
    )
    allowed = case_packet_support_paths(case_packet.read_text(encoding="utf-8"))
    errors.extend("guardrail: " + item for item in collect_checklist_guardrail_violations(dict(candidate), allowed_source_paths=allowed))
    try:
        validate_support_pointers(dict(candidate), case_packet)
    except Exception as exc:
        errors.append(f"pointer: {type(exc).__name__}: {exc}")
    try:
        validate_packet_required_stronger_conditions(dict(candidate), case_packet)
    except Exception as exc:
        errors.append(f"packet requirement: {type(exc).__name__}: {exc}")
    return errors


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    records = [
        row
        for row in load_jsonl(AUDIT_ROOT / "semantic_review_records.jsonl")
        if row.get("decision") == "revise"
    ]
    if len(records) != 132:
        raise RuntimeError(f"expected 132 revise records, found {len(records)}")
    output_records: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: str(item["case_unit_id"])):
        case_id = str(record["case_unit_id"])
        benchmark = str(record["benchmark"])
        revision = record.get("revision_validation")
        revision = revision if isinstance(revision, Mapping) else {}
        raw_candidate = revision.get("candidate")
        if not isinstance(raw_candidate, Mapping):
            raise RuntimeError(f"missing reviewer replacement for {case_id}")
        original_path = SOURCE_DRAFT_ROOT / case_id / "checklist.yaml"
        packet = PACKET_ROOTS[benchmark] / case_id / "case_packet.md"
        original = load_yaml(original_path)
        candidate = copy.deepcopy(dict(raw_candidate))
        # Reviewer bodies are expected to preserve identity, but local canonical
        # IDs are authoritative and eliminate accidental transport drift.
        for field in ("schema_version", "case_unit_id", "domain", "task_id"):
            candidate[field] = original[field]
        candidate = replace_label_path_mentions(candidate)
        pointer_actions = repair_supports(candidate, original=original, case_packet=packet)
        errors = validate_candidate(candidate, case_packet=packet, schema=schema)
        destination = OUTPUT_ROOT / case_id
        destination.mkdir(parents=True, exist_ok=True)
        write_json(destination / "checklist.json", candidate)
        (destination / "checklist.yaml").write_text(
            yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True, width=1000),
            encoding="utf-8",
        )
        provenance = {
            "schema_version": "tb21_deepswe11_outcome_blind_review_repair_provenance/v1",
            "benchmark": benchmark,
            "case_unit_id": case_id,
            "source_boundary": [
                "original frozen checklist",
                "matching case packet and raw official source tree",
                "prior independent outcome-blind semantic review and its corrected body",
            ],
            "excluded_inputs": [
                "agent outcomes",
                "trajectory contents",
                "concrete execution artifacts",
                "per-record reward/result/label values",
                "evidence scores",
                "benchmark-conflict records",
            ],
            "original_checklist_sha256": sha256_file(original_path),
            "case_packet_sha256": sha256_file(packet),
            "reviewer_candidate_sha256": hashlib.sha256(
                json.dumps(raw_candidate, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "pointer_repair_actions": pointer_actions,
            "label_path_mentions_normalized": raw_candidate != candidate and bool(
                LABEL_PATH_RE.search(json.dumps(raw_candidate, ensure_ascii=False))
            ),
            "deterministic_validation_errors": errors,
            "candidate_sha256": sha256_file(destination / "checklist.yaml"),
        }
        write_json(destination / "repair_provenance.json", provenance)
        output_records.append(
            {
                "benchmark": benchmark,
                "case_unit_id": case_id,
                "status": "pass" if not errors else "fail",
                "pointer_repair_action_count": len(pointer_actions),
                "validation_errors": errors,
                "candidate_path": str((destination / "checklist.yaml").relative_to(REPO_ROOT)),
                "candidate_sha256": provenance["candidate_sha256"],
            }
        )
    with (AUDIT_ROOT / "repair_v2" / "reviewer_repair_materialization_records.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in output_records:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "schema_version": "tb21_deepswe11_outcome_blind_review_repair_materialization/v1",
        "case_count": len(output_records),
        "pass_count": sum(row["status"] == "pass" for row in output_records),
        "fail_count": sum(row["status"] != "pass" for row in output_records),
        "pointer_repair_action_count": sum(row["pointer_repair_action_count"] for row in output_records),
        "status_counts": dict(Counter(row["status"] for row in output_records)),
        "source_boundary": "reviewer-proposed complete corrected bodies plus packet-local deterministic pointer repair; no outcomes or labels read",
    }
    write_json(AUDIT_ROOT / "repair_v2" / "reviewer_repair_materialization_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
