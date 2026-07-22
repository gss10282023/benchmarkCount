#!/usr/bin/env python3
"""Build the exact 116-row repair selection from whitelisted audit schemas.

No structural guessing is allowed.  Every manual audit schema must have an
explicit adapter below; unknown schemas fail closed.  The emitted selection
contains manual issues only because the preparation validator independently
re-reads and merges every per-case automatic QC report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import SemanticReviewError

from repair_pipeline_common import (
    EXPECTED_CASE_COUNT,
    REPAIR_SELECTION_SCHEMA,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    file_binding,
    load_json,
    load_source_prelock,
    normalized_issue,
    sha256_file,
    verify_checklist_pair,
    verify_file_binding,
    verify_internal_hash,
    verify_source_wave_complete,
    write_json_create_once,
)


C1_SCHEMA = "androidworld_wave003_manual_semantic_audit/v1"
C2_SCHEMA = "androidworld_wave_003_manual_semantic_audit_batch/v1"
ALLOWED_SCHEMAS = {C1_SCHEMA, C2_SCHEMA}
AUDIT_PARTITIONS = {
    "wave_003_batch_a": (C1_SCHEMA, "a_hashes", 0, 40),
    "wave_003_batch_b": (C2_SCHEMA, "b_flat", 40, 80),
    "wave_003_batch_c1": (C1_SCHEMA, "c1_bindings", 80, 98),
    "wave_003_batch_c2": (C2_SCHEMA, "c2_nested", 98, 116),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-prelock", type=Path, required=True)
    parser.add_argument("--automatic-qc-root", type=Path, required=True)
    parser.add_argument("--manual-audit", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def issue_rows(raw: Mapping[str, Any], case_id: str, source_kind: str) -> list[dict[str, Any]]:
    issues_raw = list(raw.get("issues") or [])
    issues = [
        normalized_issue(
            {
                "issue_id": issue.get("code"),
                "source_issue_id": issue.get("code"),
                "severity": "error",
                "source_kind": source_kind,
                "check": "manual_semantic_audit",
                "field": issue.get("field") or issue.get("checklist_json_path") or "",
                "description": issue.get("detail") or issue.get("message"),
                "required_fix": (
                    "Correct the audited semantic defect: "
                    f"{issue.get('detail') or issue.get('message')}"
                ),
                "detail": issue.get("detail") or issue.get("message"),
                "evidence": issue.get("evidence") or [],
            },
            case_id,
            issue_index,
        )
        for issue_index, issue in enumerate(issues_raw, 1)
        if isinstance(issue, Mapping)
    ]
    if len(issues) != len(issues_raw):
        raise RepairPipelineError(f"{case_id} contains a non-object manual issue")
    status = raw.get("status")
    if status not in {"pass", "fail"} or (status == "pass") != (not issues):
        raise RepairPipelineError(f"{case_id} manual status/issues disagree")
    return issues


def a_hash_rows(
    audit: Mapping[str, Any],
    *,
    audit_path: Path,
    packet_by_case: Mapping[str, Mapping[str, Any]],
    wave: Path,
) -> list[dict[str, Any]]:
    verify_internal_hash(audit, ("audit_body_sha256",), audit_path.name)
    rows = list(audit.get("cases") or [])
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise RepairPipelineError(f"{audit_path.name} cases[{index}] is not an object")
        case_id = str(raw.get("case_unit_id") or "")
        if case_id not in packet_by_case or raw.get("index_zero_based") != index:
            raise RepairPipelineError(f"{audit_path.name} A identity/index invalid at {index}")
        hashes = raw.get("hashes")
        if not isinstance(hashes, Mapping):
            raise RepairPipelineError(f"{audit_path.name} {case_id} hashes is not an object")
        packet_sha = packet_by_case[case_id]["sha256"]
        expected_hashes = {
            "packet_sha256": packet_sha,
            "expected_packet_sha256": packet_sha,
            "packet_matches_prelock": True,
            "checklist_yaml_sha256": sha256_file(wave / case_id / "checklist.yaml"),
            "checklist_json_sha256": sha256_file(wave / case_id / "checklist.json"),
        }
        for field, expected in expected_hashes.items():
            if hashes.get(field) != expected:
                raise RepairPipelineError(f"{audit_path.name} {case_id} {field} differs")
        normalized.append(
            {"case_unit_id": case_id, "issues": issue_rows(raw, case_id, "manual_audit_a")}
        )
    return normalized


def c1_binding_rows(
    audit: Mapping[str, Any],
    *,
    audit_path: Path,
    packet_by_case: Mapping[str, Mapping[str, Any]],
    wave: Path,
) -> list[dict[str, Any]]:
    verify_internal_hash(audit, ("audit_body_sha256",), audit_path.name)
    if audit.get("generation_id") != "wave_003":
        raise RepairPipelineError(f"{audit_path.name} generation_id is not wave_003")
    rows = list(audit.get("cases") or [])
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise RepairPipelineError(f"{audit_path.name} cases[{index}] is not an object")
        case_id = str(raw.get("case_unit_id") or "")
        if not case_id or case_id not in packet_by_case:
            raise RepairPipelineError(f"{audit_path.name} C1 case identity invalid: {case_id!r}")
        issues = issue_rows(raw, case_id, "manual_audit_c1")
        bindings = raw.get("bindings") or {}
        for name in ("packet", "checklist_yaml", "checklist_json"):
            verify_file_binding(bindings.get(name), f"{audit_path.name} {case_id} {name}", inside_candidate=True)
        if bindings["packet"].get("sha256") != packet_by_case[case_id].get("sha256"):
            raise RepairPipelineError(f"{audit_path.name} {case_id} packet hash differs from prelock")
        if bindings["checklist_yaml"].get("sha256") != sha256_file(wave / case_id / "checklist.yaml"):
            raise RepairPipelineError(f"{audit_path.name} {case_id} checklist hash differs")
        if bindings["checklist_json"].get("sha256") != sha256_file(wave / case_id / "checklist.json"):
            raise RepairPipelineError(f"{audit_path.name} {case_id} checklist JSON hash differs")
        prelock = raw.get("prelock") or {}
        if (
            prelock.get("matches") is not True
            or prelock.get("expected_packet_sha256") != packet_by_case[case_id]["sha256"]
            or prelock.get("selection_rank") != packet_by_case[case_id]["selection_rank"]
        ):
            raise RepairPipelineError(f"{audit_path.name} {case_id} prelock binding differs")
        normalized.append({"case_unit_id": case_id, "issues": issues})
    return normalized


def b_flat_rows(
    audit: Mapping[str, Any],
    *,
    audit_path: Path,
    packet_by_case: Mapping[str, Mapping[str, Any]],
    wave: Path,
) -> list[dict[str, Any]]:
    if audit.get("review_type") != "independent_read_only_manual_semantic_nonpromotion":
        raise RepairPipelineError(f"{audit_path.name} C2 review_type is invalid")
    rows = list(audit.get("cases") or [])
    if audit.get("case_count") != len(rows):
        raise RepairPipelineError(f"{audit_path.name} C2 case_count differs")
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise RepairPipelineError(f"{audit_path.name} cases[{index}] is not an object")
        case_id = str(raw.get("case_id") or "")
        if not case_id or case_id not in packet_by_case:
            raise RepairPipelineError(f"{audit_path.name} C2 case identity invalid: {case_id!r}")
        issues = issue_rows(raw, case_id, "manual_audit_b")
        if raw.get("selection_index") != index + 40:
            raise RepairPipelineError(f"{audit_path.name} {case_id} selection_index differs")
        if raw.get("packet_sha256") != packet_by_case[case_id].get("sha256"):
            raise RepairPipelineError(f"{audit_path.name} {case_id} packet hash differs from prelock")
        if raw.get("checklist_sha256") != sha256_file(wave / case_id / "checklist.yaml"):
            raise RepairPipelineError(f"{audit_path.name} {case_id} checklist hash differs")
        normalized.append({"case_unit_id": case_id, "issues": issues})
    return normalized


def c2_nested_rows(
    audit: Mapping[str, Any],
    *,
    audit_path: Path,
    packet_by_case: Mapping[str, Mapping[str, Any]],
    wave: Path,
) -> list[dict[str, Any]]:
    rows = list(audit.get("cases") or [])
    if audit.get("case_count") != len(rows):
        raise RepairPipelineError(f"{audit_path.name} C2 case_count differs")
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise RepairPipelineError(f"{audit_path.name} cases[{index}] is not an object")
        case_id = str(raw.get("case_id") or "")
        if case_id not in packet_by_case:
            raise RepairPipelineError(f"{audit_path.name} C2 case identity invalid: {case_id!r}")
        issues = issue_rows(raw, case_id, "manual_audit_c2")
        packet = raw.get("packet")
        checklist = raw.get("checklist")
        if not isinstance(packet, Mapping) or not isinstance(checklist, Mapping):
            raise RepairPipelineError(f"{audit_path.name} {case_id} nested hashes are missing")
        if packet.get("sha256") != packet_by_case[case_id].get("sha256"):
            raise RepairPipelineError(f"{audit_path.name} {case_id} packet hash differs from prelock")
        if checklist.get("sha256") != sha256_file(wave / case_id / "checklist.yaml"):
            raise RepairPipelineError(f"{audit_path.name} {case_id} checklist hash differs")
        normalized.append({"case_unit_id": case_id, "issues": issues})
    return normalized


def load_manual_audit(
    path: Path,
    *,
    packet_by_case: Mapping[str, Mapping[str, Any]],
    wave: Path,
    sorted_order: list[str],
) -> list[dict[str, Any]]:
    audit = load_json(path, f"manual audit {path.name}")
    schema = audit.get("schema_version")
    if schema not in ALLOWED_SCHEMAS:
        raise RepairPipelineError(
            f"manual audit schema {schema!r} is not explicitly whitelisted; accepted={sorted(ALLOWED_SCHEMAS)}"
        )
    audit_id = str(audit.get("audit_id") or audit.get("batch_id") or "")
    variant = AUDIT_PARTITIONS.get(audit_id)
    if variant is None or variant[0] != schema:
        raise RepairPipelineError(
            f"manual audit id/schema combination is not whitelisted: {audit_id!r}/{schema!r}"
        )
    _, shape, start, end = variant
    handlers = {
        "a_hashes": a_hash_rows,
        "b_flat": b_flat_rows,
        "c1_bindings": c1_binding_rows,
        "c2_nested": c2_nested_rows,
    }
    result = handlers[shape](audit, audit_path=path, packet_by_case=packet_by_case, wave=wave)
    observed = [row["case_unit_id"] for row in result]
    expected = sorted_order[start:end]
    if observed != expected:
        raise RepairPipelineError(
            f"{audit_id} case order/range differs: expected sorted[{start}:{end}]"
        )
    return result


def verify_selection_reconstructed_from_bound_sources(
    selection_path: Path,
    *,
    source: Mapping[str, Any],
    wave: Path,
    qc_root: Path,
) -> dict[str, Any]:
    """Rebuild all 116 emitted rows from the four bound manual audit originals."""

    selection_path = selection_path.resolve()
    try:
        selection_path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("repair selection must be inside candidate116") from exc
    selection = load_json(selection_path, "repair selection for source reconstruction")
    if selection.get("schema_version") != REPAIR_SELECTION_SCHEMA:
        raise RepairPipelineError("repair selection reconstruction schema is invalid")
    verify_internal_hash(selection, ("selection_sha256",), "repair selection reconstruction")
    order = list(source["case_order"])
    if (
        selection.get("case_count") != EXPECTED_CASE_COUNT
        or selection.get("case_order_sha256") != source["case_order_sha256"]
        or selection.get("source_generation_id") != "wave_003"
    ):
        raise RepairPipelineError("repair selection reconstruction source/order differs")
    summary_binding = selection.get("automatic_qc_summary")
    summary_path = verify_file_binding(
        summary_binding, "selection automatic QC summary", inside_candidate=True
    )
    expected_summary_path = (qc_root / "summary.json").resolve()
    if summary_path != expected_summary_path or dict(summary_binding) != file_binding(expected_summary_path):
        raise RepairPipelineError("selection top-level automatic QC summary binding differs")
    manual_bindings = selection.get("manual_audits")
    if not isinstance(manual_bindings, list) or len(manual_bindings) != 4:
        raise RepairPipelineError("selection must bind exactly four manual audit originals")
    audit_paths: list[Path] = []
    audit_ids: list[str] = []
    for index, binding in enumerate(manual_bindings):
        path = verify_file_binding(
            binding, f"selection manual audit {index}", inside_candidate=True
        )
        if dict(binding) != file_binding(path):
            raise RepairPipelineError(f"selection manual audit {index} binding is not exact")
        audit = load_json(path, f"selection manual audit {index}")
        audit_ids.append(str(audit.get("audit_id") or audit.get("batch_id") or ""))
        audit_paths.append(path)
    if audit_ids != list(AUDIT_PARTITIONS):
        raise RepairPipelineError(
            f"selection manual audit ids/order differ: {audit_ids!r}"
        )
    packet_by_case = {row["case_unit_id"]: row for row in source["packet_inputs"]}
    manual_by_case: dict[str, dict[str, Any]] = {}
    for path, binding in zip(audit_paths, manual_bindings, strict=True):
        for row in load_manual_audit(
            path,
            packet_by_case=packet_by_case,
            wave=wave,
            sorted_order=sorted(order),
        ):
            case_id = row["case_unit_id"]
            if case_id in manual_by_case:
                raise RepairPipelineError(f"reconstructed manual audits overlap at {case_id}")
            manual_by_case[case_id] = row | {"audit_source": dict(binding)}
    if set(manual_by_case) != set(order):
        raise RepairPipelineError("reconstructed manual audits do not cover exact candidate116")
    expected_cases: list[dict[str, Any]] = []
    for rank, case_id in enumerate(order):
        qc = load_json(qc_root / case_id / "qc.json", f"{case_id} automatic QC reconstruction")
        if (
            qc.get("case_unit_id") != case_id
            or qc.get("task_id") != case_id
            or qc.get("selection_rank") != rank
        ):
            raise RepairPipelineError(f"{case_id} reconstruction automatic QC identity differs")
        automatic_issues = qc.get("issues")
        if not isinstance(automatic_issues, list) or any(
            not isinstance(item, Mapping) for item in automatic_issues
        ):
            raise RepairPipelineError(f"{case_id} reconstruction automatic issues are invalid")
        checks = qc.get("checks")
        passed = (
            isinstance(checks, Mapping)
            and all(value is True for value in checks.values())
            and not automatic_issues
        )
        if qc.get("status") != ("passed" if passed else "failed"):
            raise RepairPipelineError(f"{case_id} reconstruction automatic status is invalid")
        if not passed and (
            not automatic_issues
            or not any(item.get("severity") == "error" for item in automatic_issues)
        ):
            raise RepairPipelineError(
                f"{case_id} failed automatic QC reconstruction lacks an error issue"
            )
        manual = manual_by_case[case_id]
        expected_cases.append(
            {
                "selection_rank": rank,
                "case_unit_id": case_id,
                "task_id": case_id,
                "disposition": "repair" if automatic_issues or manual["issues"] else "retain",
                "issues": manual["issues"],
                "audit_sources": [manual["audit_source"]],
            }
        )
    if selection.get("cases") != expected_cases:
        raise RepairPipelineError(
            "repair selection cases differ from exact reconstruction of four bound audits"
        )
    return selection


def main() -> int:
    args = parse_args()
    source = load_source_prelock(args.source_prelock.resolve())
    wave, _ = verify_source_wave_complete(source)
    order = list(source["case_order"])
    packet_by_case = {row["case_unit_id"]: row for row in source["packet_inputs"]}
    sorted_order = sorted(order)
    qc_root = args.automatic_qc_root.resolve()
    summary = load_json(qc_root / "summary.json", "automatic QC summary")
    if summary.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("automatic QC summary is not exactly 116 cases")
    audit_paths = [path.resolve() for path in args.manual_audit]
    if len(audit_paths) != len(set(audit_paths)):
        raise RepairPipelineError("duplicate --manual-audit path")
    manual_by_case: dict[str, dict[str, Any]] = {}
    for path in audit_paths:
        binding = file_binding(path)
        for row in load_manual_audit(
            path, packet_by_case=packet_by_case, wave=wave, sorted_order=sorted_order
        ):
            case_id = row["case_unit_id"]
            if case_id in manual_by_case:
                raise RepairPipelineError(f"manual audits overlap at {case_id}")
            manual_by_case[case_id] = row | {"audit_source": binding}
    if set(manual_by_case) != set(order):
        raise RepairPipelineError(
            f"manual audits do not cover exact candidate116: missing={sorted(set(order)-set(manual_by_case))}, "
            f"extra={sorted(set(manual_by_case)-set(order))}"
        )
    cases: list[dict[str, Any]] = []
    for rank, case_id in enumerate(order):
        qc_path = qc_root / case_id / "qc.json"
        qc = load_json(qc_path, f"{case_id} automatic QC")
        if qc.get("case_unit_id") != case_id:
            raise RepairPipelineError(f"{case_id} automatic QC identity differs")
        automatic_issues = list(qc.get("issues") or [])
        if any(not isinstance(item, Mapping) for item in automatic_issues):
            raise RepairPipelineError(f"{case_id} automatic QC contains non-object issue")
        checks = qc.get("checks")
        passed = (
            isinstance(checks, Mapping)
            and all(value is True for value in checks.values())
            and not automatic_issues
        )
        if qc.get("status") != ("passed" if passed else "failed"):
            raise RepairPipelineError(f"{case_id} automatic QC status is inconsistent")
        if not passed and (
            not automatic_issues
            or not any(item.get("severity") == "error" for item in automatic_issues)
        ):
            raise RepairPipelineError(f"{case_id} failed automatic QC lacks an error issue")
        manual = manual_by_case[case_id]
        disposition = "repair" if automatic_issues or manual["issues"] else "retain"
        cases.append(
            {
                "selection_rank": rank,
                "case_unit_id": case_id,
                "task_id": case_id,
                "disposition": disposition,
                "issues": manual["issues"],
                "audit_sources": [manual["audit_source"]],
            }
        )
    selection = {
        "schema_version": REPAIR_SELECTION_SCHEMA,
        "source_generation_id": "wave_003",
        "case_count": EXPECTED_CASE_COUNT,
        "case_order_sha256": source["case_order_sha256"],
        "automatic_qc_summary": file_binding(qc_root / "summary.json"),
        "manual_audits": [file_binding(path) for path in audit_paths],
        "manual_audit_schemas": sorted(
            {load_json(path, path.name)["schema_version"] for path in audit_paths}
        ),
        "cases": cases,
    }
    selection = add_self_hash(selection, "selection_sha256")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_pass",
                    "case_count": len(cases),
                    "repair_count": sum(row["disposition"] == "repair" for row in cases),
                    "retain_count": sum(row["disposition"] == "retain" for row in cases),
                    "selection_sha256": selection["selection_sha256"],
                },
                indent=2,
            )
        )
        return 0
    output = args.output.resolve()
    try:
        output.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("selection output must be inside candidate116") from exc
    write_json_create_once(output, selection)
    print(json.dumps({"status": "written", "selection": file_binding(output) | {"selection_sha256": selection["selection_sha256"]}}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
