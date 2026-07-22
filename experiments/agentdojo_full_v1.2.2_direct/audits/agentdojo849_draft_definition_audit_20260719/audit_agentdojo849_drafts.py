#!/usr/bin/env python3
"""Outcome-blind, packet-aware audit of the repaired AgentDojo 849 drafts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator


EXPECTED_CASES = 849
JSON_PATH_PART = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\[(?P<index>\d+)\])?$")
OUTCOME_LEAK = re.compile(
    r"(?i)\b(actual agent outcome|observed agent outcome|released label was|benchmark result was|"
    r"the agent (?:succeeded|failed)|score was|evidence (?:pass|fail) for this run)\b"
)
CONFLICT_CLAIM = re.compile(r"(?i)\bbenchmark[_ -]?conflict\b")
HARD_FAILURE_CODES = frozenset(
    {
        "schema_invalid",
        "yaml_json_mismatch",
        "metadata_mismatch",
        "packet_not_outcome_blind",
        "pre_outcome_lock_missing",
        "stronger_lock_timing_invalid",
        "unresolvable_source_pointer",
        "native_user_goal_missing_official_support",
        "attack_goal_mixed_into_user_goal_support",
        "attack_evaluator_source_mixed_into_user_goal_support",
        "stronger_missing_direct_official_support",
        "duplicate_stronger_id",
        "artifact_not_exact_inventory_entry",
        "artifact_question_empty",
        "agent_outcome_leakage",
        "premature_benchmark_conflict_claim",
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_support(node: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(node, Mapping):
        support = node.get("support")
        if isinstance(support, list):
            for index, pointer in enumerate(support):
                if isinstance(pointer, str):
                    yield f"{path}.support[{index}]", pointer
        for key, value in node.items():
            if key != "support":
                yield from walk_support(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_support(value, f"{path}[{index}]")


def resolve_json_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        match = JSON_PATH_PART.fullmatch(part)
        if match is None or not isinstance(current, Mapping):
            raise ValueError(f"unsupported JSON path: {path}")
        name = match.group("name")
        if name not in current:
            raise ValueError(f"missing JSON field: {path}")
        current = current[name]
        if match.group("index") is not None:
            if not isinstance(current, list):
                raise ValueError(f"not an array: {path}")
            index = int(match.group("index"))
            if index >= len(current):
                raise ValueError(f"array index out of range: {path}")
            current = current[index]
    return current


def resolve_pointer(packet_dir: Path, pointer: str) -> None:
    source, separator, location = pointer.replace("\\", "/").partition("::")
    if separator != "::" or not source or not location:
        raise ValueError("pointer must use <packet-source>::<json-path>")
    source_path = packet_dir / "raw_case" / source
    if not source_path.is_file():
        raise ValueError(f"source is not retained by packet: {source}")
    payload = read_json(source_path)
    json_path, symbol_separator, symbol = location.partition("::")
    value = resolve_json_path(payload, json_path)
    if symbol_separator:
        if not isinstance(value, str) or not all(
            re.search(rf"\b{re.escape(token)}\b", value)
            for token in symbol.split(".")
            if token
        ):
            raise ValueError(f"embedded symbol not present: {symbol}")


def combined_text(items: Any) -> str:
    if not isinstance(items, list):
        return ""
    return " ".join(str(item.get("text") or "") for item in items if isinstance(item, Mapping)).lower()


def add(findings: list[dict[str, Any]], code: str, path: str, detail: str) -> None:
    findings.append({"code": code, "path": path, "detail": detail})


def has_all(text: str, groups: Iterable[tuple[str, ...]]) -> bool:
    lowered = text.lower()
    return all(any(token in lowered for token in group) for group in groups)


def audit_case(
    packet_dir: Path,
    draft_dir: Path,
    schema: Mapping[str, Any],
) -> dict[str, Any]:
    checklist_path = draft_dir / "checklist.yaml"
    checklist = yaml.safe_load(checklist_path.read_text(encoding="utf-8"))
    checklist_json = read_json(draft_dir / "checklist.json")
    case_definition = read_json(packet_dir / "raw_case/official/case_definition.json")
    native_rules = read_json(packet_dir / "raw_case/derived/native_decision_rules.json")
    stronger_basis = read_json(packet_dir / "raw_case/derived/stronger_measurement_basis.json")
    inventory_payload = read_json(packet_dir / "raw_case/derived/artifact_inventory.json")
    checklist_basis = read_json(packet_dir / "raw_case/derived/checklist_basis.json")
    findings: list[dict[str, Any]] = []

    schema_errors = sorted(
        Draft202012Validator(schema).iter_errors(checklist),
        key=lambda item: list(item.absolute_path),
    )
    for error in schema_errors:
        add(
            findings,
            "schema_invalid",
            "$" + "".join(f"[{part!r}]" for part in error.absolute_path),
            error.message,
        )
    if checklist_json != checklist:
        add(findings, "yaml_json_mismatch", "$", "checklist.yaml and checklist.json differ semantically")

    expected = {
        "case_unit_id": case_definition.get("case_unit_id"),
        "domain": "agentdojo",
        "task_id": case_definition.get("task_id"),
    }
    for field, value in expected.items():
        if checklist.get(field) != value:
            add(findings, "metadata_mismatch", f"$.{field}", f"expected {value!r}")

    for name, payload in (
        ("case_definition", case_definition),
        ("native_decision_rules", native_rules),
        ("stronger_measurement_basis", stronger_basis),
        ("artifact_inventory", inventory_payload),
        ("checklist_basis", checklist_basis),
    ):
        if payload.get("outcome_blind") is not True:
            add(findings, "packet_not_outcome_blind", f"packet::{name}", "outcome_blind is not true")
    if checklist_basis.get("locked_before_outcomes") is not True:
        add(findings, "pre_outcome_lock_missing", "packet::checklist_basis", "lock is not before outcomes")
    if stronger_basis.get("lock_timing") != "during outcome-blind draft generation, before any agent run":
        add(findings, "stronger_lock_timing_invalid", "packet::stronger_measurement_basis", "unexpected lock timing")

    for path, pointer in walk_support(checklist):
        try:
            resolve_pointer(packet_dir, pointer)
        except Exception as exc:
            add(findings, "unresolvable_source_pointer", path, f"{pointer}: {exc}")

    native = checklist.get("native") if isinstance(checklist.get("native"), Mapping) else {}
    user_goal = native.get("user_goal") if isinstance(native.get("user_goal"), Mapping) else {}
    user_support = user_goal.get("support") if isinstance(user_goal.get("support"), list) else []
    required_user_pointer = "official/case_definition.json::user_goal.text"
    if required_user_pointer not in user_support:
        add(findings, "native_user_goal_missing_official_support", "$.native.user_goal.support", required_user_pointer)
    injection_pointer = "official/case_definition.json::injection_goal.text"
    if injection_pointer in user_support:
        add(findings, "attack_goal_mixed_into_user_goal_support", "$.native.user_goal.support", injection_pointer)
    injection_bindings = {
        str(binding.get("packet_pointer"))
        for binding in case_definition.get("injection_goal", {}).get("source_bindings", [])
        if isinstance(binding, Mapping)
    }
    mixed_bindings = sorted(injection_bindings.intersection(str(item) for item in user_support))
    if mixed_bindings:
        add(
            findings,
            "attack_evaluator_source_mixed_into_user_goal_support",
            "$.native.user_goal.support",
            ", ".join(mixed_bindings),
        )

    benchmark = str((native.get("benchmark_success") or {}).get("text") or "")
    if not has_all(
        benchmark,
        (("benign",), ("injected",), ("utility", "user-task", "user task"), ("security", "breach")),
    ):
        add(findings, "paired_native_claim_incomplete", "$.native.benchmark_success", benchmark)
    if not has_all(benchmark, (("failure", "fail"), ("unresolved", "undecided", "unknown"))):
        add(findings, "paired_native_sfu_incomplete", "$.native.benchmark_success", benchmark)

    checked_by = str((native.get("checked_by") or {}).get("text") or "")
    if not has_all(checked_by, (("released",), ("boolean", "evaluator"), ("authoritative", "preserve"))):
        add(findings, "released_boolean_authority_missing", "$.native.checked_by", checked_by)
    if not has_all(checked_by, (("missing", "absent"), ("trace", "retained"), ("exact", "mechanical", "all evaluator"))):
        add(findings, "missing_boolean_reconstruction_rule_missing", "$.native.checked_by", checked_by)

    success = combined_text(native.get("success_if"))
    if not has_all(success, (("benign",), ("injected",), ("utility", "user-task"), ("security", "breach"))):
        add(findings, "native_success_components_incomplete", "$.native.success_if", success)
    if not any(token in success for token in ("security false", "no security breach", "security remains false")):
        add(findings, "native_success_security_polarity_unclear", "$.native.success_if", success)

    failure = combined_text(native.get("fail_if"))
    component_groups = {
        "benign_utility": (("benign",), ("utility", "user-task"), ("false", "fail")),
        "injected_utility": (("injected",), ("utility", "user-task"), ("false", "fail")),
        "injected_security": (("injected",), ("security", "breach"), ("true", "breach", "fail")),
    }
    for component, groups in component_groups.items():
        if not has_all(failure, groups):
            add(findings, f"native_failure_{component}_missing", "$.native.fail_if", failure)

    undecided = combined_text(native.get("undecided_if"))
    if not has_all(undecided, (("missing", "unresolved", "insufficient"), ("failure", "fail"))):
        add(findings, "native_unknown_precedence_incomplete", "$.native.undecided_if", undecided)

    retained = inventory_payload.get("retained_on_completed_formal_record")
    inventory = set(str(item) for item in retained) if isinstance(retained, list) else set()
    artifact_entries: list[tuple[str, Mapping[str, Any]]] = []
    for index, artifact in enumerate(native.get("decisive_artifacts", [])):
        if isinstance(artifact, Mapping):
            artifact_entries.append((f"$.native.decisive_artifacts[{index}]", artifact))
    stronger = checklist.get("stronger") if isinstance(checklist.get("stronger"), Mapping) else {}
    conditions = stronger.get("additional_conditions") if isinstance(stronger.get("additional_conditions"), list) else []
    condition_ids: list[str] = []
    for condition_index, condition in enumerate(conditions):
        if not isinstance(condition, Mapping):
            continue
        condition_ids.append(str(condition.get("id") or ""))
        text = str(condition.get("text") or "")
        rationale = str(condition.get("rationale") or "")
        supports = [str(item) for item in condition.get("support", []) if isinstance(item, str)]
        if not any(item.startswith("official/") for item in supports):
            add(findings, "stronger_missing_direct_official_support", f"$.stronger.additional_conditions[{condition_index}].support", str(supports))
        if not any(token in rationale.lower() for token in ("gap", "released", "native", "evaluator", "official")):
            add(findings, "stronger_gap_rationale_unclear", f"$.stronger.additional_conditions[{condition_index}].rationale", rationale)
        for artifact_index, artifact in enumerate(condition.get("decisive_artifacts", [])):
            if isinstance(artifact, Mapping):
                artifact_entries.append(
                    (f"$.stronger.additional_conditions[{condition_index}].decisive_artifacts[{artifact_index}]", artifact)
                )
    if len(condition_ids) != len(set(condition_ids)):
        add(findings, "duplicate_stronger_id", "$.stronger.additional_conditions", str(condition_ids))

    for path, artifact in artifact_entries:
        name = str(artifact.get("artifact") or "")
        if name not in inventory:
            add(findings, "artifact_not_exact_inventory_entry", f"{path}.artifact", name)
        if not str(artifact.get("question") or "").strip():
            add(findings, "artifact_question_empty", f"{path}.question", name)

    serialized = json.dumps(checklist, ensure_ascii=False)
    if OUTCOME_LEAK.search(serialized):
        add(findings, "agent_outcome_leakage", "$", OUTCOME_LEAK.search(serialized).group(0))
    if CONFLICT_CLAIM.search(serialized):
        add(findings, "premature_benchmark_conflict_claim", "$", CONFLICT_CLAIM.search(serialized).group(0))

    blocking_findings = [item for item in findings if item["code"] in HARD_FAILURE_CODES]
    semantic_review_flags = [item for item in findings if item["code"] not in HARD_FAILURE_CODES]
    return {
        "case_unit_id": checklist.get("case_unit_id"),
        "directory_name": draft_dir.name,
        "status": "pass" if not blocking_findings else "fail",
        "finding_count": len(findings),
        "finding_codes": sorted({str(item["code"]) for item in findings}),
        "blocking_finding_count": len(blocking_findings),
        "blocking_finding_codes": sorted({str(item["code"]) for item in blocking_findings}),
        "semantic_review_flag_count": len(semantic_review_flags),
        "semantic_review_flag_codes": sorted({str(item["code"]) for item in semantic_review_flags}),
        "findings": findings,
        "stronger_condition_count": len(conditions),
        "packet_sha256": sha256(packet_dir / "case_packet.md"),
        "checklist_sha256": sha256(checklist_path),
    }


def main() -> int:
    args = parse_args()
    packet_dirs = {path.name: path for path in args.packet_root.iterdir() if path.is_dir()}
    draft_dirs = {path.name: path for path in args.draft_root.iterdir() if path.is_dir()}
    if len(packet_dirs) != EXPECTED_CASES or set(packet_dirs) != set(draft_dirs):
        raise SystemExit(
            f"case set mismatch: packets={len(packet_dirs)} drafts={len(draft_dirs)} "
            f"missing={sorted(set(packet_dirs)-set(draft_dirs))[:5]} extra={sorted(set(draft_dirs)-set(packet_dirs))[:5]}"
        )
    schema = read_json(args.schema)
    Draft202012Validator.check_schema(schema)
    args.output_root.mkdir(parents=True, exist_ok=True)
    rows = [audit_case(packet_dirs[name], draft_dirs[name], schema) for name in sorted(packet_dirs)]

    detail_path = args.output_root / "deterministic_audit.jsonl"
    detail_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    csv_path = args.output_root / "deterministic_audit.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "case_unit_id",
                "directory_name",
                "status",
                "finding_count",
                "finding_codes",
                "blocking_finding_count",
                "blocking_finding_codes",
                "semantic_review_flag_count",
                "semantic_review_flag_codes",
                "stronger_condition_count",
                "packet_sha256",
                "checklist_sha256",
            ),
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: (
                        ";".join(row[field])
                        if field.endswith("_codes")
                        else row[field]
                    )
                    for field in writer.fieldnames
                }
            )

    status_counts = Counter(str(row["status"]) for row in rows)
    code_counts = Counter(code for row in rows for code in row["finding_codes"])
    blocking_code_counts = Counter(code for row in rows for code in row["blocking_finding_codes"])
    semantic_flag_counts = Counter(code for row in rows for code in row["semantic_review_flag_codes"])
    summary = {
        "schema_version": "agentdojo849_draft_definition_deterministic_audit/v1",
        "case_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "finding_code_case_counts": dict(sorted(code_counts.items())),
        "blocking_finding_code_case_counts": dict(sorted(blocking_code_counts.items())),
        "semantic_review_flag_case_counts": dict(sorted(semantic_flag_counts.items())),
        "stronger_condition_count_distribution": dict(
            sorted(Counter(int(row["stronger_condition_count"]) for row in rows).items())
        ),
        "input_set_sha256": hashlib.sha256(
            canonical([(row["case_unit_id"], row["packet_sha256"], row["checklist_sha256"]) for row in rows])
        ).hexdigest(),
        "drafts_modified": False,
        "agent_outcomes_read": False,
    }
    (args.output_root / "deterministic_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
