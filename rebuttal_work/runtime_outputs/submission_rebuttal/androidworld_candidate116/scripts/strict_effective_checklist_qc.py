#!/usr/bin/env python3
"""Run the exact frozen wave3 per-case QC logic over the effective 116 wave."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from repair_pipeline_common import (
    EFFECTIVE_MANIFEST_SCHEMA,
    EXPECTED_CASE_COUNT,
    REPO_ROOT,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    atomic_promote_directory,
    file_binding,
    guarded_output_directory,
    load_json,
    load_jsonl,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    tree_record,
    utc_now,
    verify_file_binding,
    verify_internal_hash,
    verify_repair_concurrency_evidence,
)
from semantic_review_common import write_json_atomic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effective-manifest", type=Path)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--skip-live-login-check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def import_base(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("candidate116_repair_prelocked_strict_qc_base", path)
    if spec is None or spec.loader is None:
        raise RepairPipelineError(f"cannot import strict QC base from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    required = ("validate_prelock", "load_batch_records", "validate_batch_summary", "per_case_qc")
    missing = [name for name in required if not callable(getattr(module, name, None))]
    if missing:
        raise RepairPipelineError(f"strict QC base is missing callables: {missing}")
    return module


def verify_effective_manifest(path: Path) -> tuple[dict[str, Any], Path, dict[str, dict[str, Any]]]:
    manifest = load_json(path, "effective manifest")
    if manifest.get("schema_version") != EFFECTIVE_MANIFEST_SCHEMA:
        raise RepairPipelineError("effective manifest schema is invalid")
    verify_internal_hash(manifest, ("effective_manifest_sha256",), "effective manifest")
    if manifest.get("status") != "composed_not_qc_or_independent_codex_root_agent_accepted":
        raise RepairPipelineError("effective manifest status is invalid")
    order = list(manifest.get("case_order") or [])
    if (
        manifest.get("case_count") != EXPECTED_CASE_COUNT
        or len(order) != EXPECTED_CASE_COUNT
        or len(set(order)) != EXPECTED_CASE_COUNT
        or manifest.get("case_order_sha256") != object_sha256(order)
    ):
        raise RepairPipelineError("effective manifest does not bind exact candidate116 order")
    effective_root = path.resolve().parent
    if path.resolve() != effective_root / "_effective_manifest.json":
        raise RepairPipelineError("effective manifest must be at its wave root")
    verify_file_binding(manifest.get("effective_batch_results"), "effective batch results", inside_candidate=True)
    verify_file_binding(manifest.get("effective_batch_summary"), "effective batch summary", inside_candidate=True)
    rows = list(manifest.get("cases") or [])
    if len(rows) != EXPECTED_CASE_COUNT or manifest.get("cases_sha256") != object_sha256(rows):
        raise RepairPipelineError("effective manifest case index is invalid")
    by_case: dict[str, dict[str, Any]] = {}
    counts = {"wave_003": 0, "repair": 0}
    for rank, (case_id, row) in enumerate(zip(order, rows, strict=True)):
        if not isinstance(row, Mapping):
            raise RepairPipelineError(f"effective case row {rank} is not an object")
        if row.get("selection_rank") != rank or row.get("case_unit_id") != case_id:
            raise RepairPipelineError(f"effective case identity/order mismatch at {case_id}")
        origin = row.get("origin")
        if origin not in counts:
            raise RepairPipelineError(f"{case_id} effective origin is invalid")
        counts[origin] += 1
        checklist_path = verify_file_binding(row.get("effective_checklist"), f"{case_id} checklist", inside_candidate=True)
        if checklist_path != (effective_root / case_id / "checklist.yaml").resolve():
            raise RepairPipelineError(f"{case_id} effective checklist path is noncanonical")
        origin_path = verify_file_binding(row.get("effective_origin"), f"{case_id} origin", inside_candidate=True)
        origin_value = load_json(origin_path, f"{case_id} origin")
        verify_internal_hash(origin_value, ("origin_sha256",), f"{case_id} origin")
        if origin_value.get("origin") != origin or origin_value.get("origin_sha256") != row["effective_origin"].get("origin_sha256"):
            raise RepairPipelineError(f"{case_id} effective origin binding differs")
        if origin == "repair":
            provenance_path = verify_file_binding(row.get("repair_provenance"), f"{case_id} repair provenance", inside_candidate=True)
            provenance = load_json(provenance_path, f"{case_id} repair provenance")
            verify_internal_hash(provenance, ("provenance_sha256",), f"{case_id} repair provenance")
            if provenance.get("provenance_sha256") != row["repair_provenance"].get("provenance_sha256"):
                raise RepairPipelineError(f"{case_id} repair provenance differs")
        elif row.get("repair_provenance") is not None:
            raise RepairPipelineError(f"{case_id} retained origin unexpectedly has repair provenance")
        observed_tree = tree_record(effective_root / case_id)
        expected_tree = row.get("effective_case_tree") or {}
        if (
            observed_tree.get("file_count") != expected_tree.get("file_count")
            or observed_tree.get("tree_sha256") != expected_tree.get("tree_sha256")
            or observed_tree.get("files") != expected_tree.get("files")
        ):
            raise RepairPipelineError(f"{case_id} effective case tree differs from manifest")
        by_case[case_id] = dict(row)
    if counts != manifest.get("origin_counts"):
        raise RepairPipelineError("effective manifest origin counts differ from cases")
    observed_dirs = {p.name for p in effective_root.iterdir() if p.is_dir() and not p.name.startswith(".")}
    if observed_dirs != set(order):
        raise RepairPipelineError("effective wave directory set is not exact candidate116")
    return manifest, effective_root, by_case


def main() -> int:
    args = parse_args()
    if args.self_test and args.effective_manifest is None:
        base = import_base(WORK_ROOT / "scripts" / "strict_draft_automatic_qc.py")
        negative_rejected = False
        with tempfile.TemporaryDirectory(prefix="candidate116_qc_interface_test.") as raw:
            bad = Path(raw) / "bad_qc.py"
            bad.write_text("def validate_prelock():\n    pass\n", encoding="utf-8")
            try:
                import_base(bad)
            except RepairPipelineError:
                negative_rejected = True
        if not negative_rejected:
            raise RepairPipelineError("incomplete strict QC interface negative test failed")
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "base": repo_relative(Path(base.__file__)),
                    "reused_callable": "per_case_qc",
                    "negative_incomplete_interface_rejected": True,
                    "model_invoked": False,
                },
                indent=2,
            )
        )
        return 0
    if args.effective_manifest is None or args.report_root is None:
        raise RepairPipelineError("--effective-manifest and --report-root are required")
    manifest_path = args.effective_manifest.resolve()
    manifest, effective_root, effective_by_case = verify_effective_manifest(manifest_path)
    repair_prelock_path = verify_file_binding(
        manifest.get("repair_prelock"), "repair prelock", inside_candidate=True
    )
    repair_prelock = load_json(repair_prelock_path, "repair prelock")
    verify_internal_hash(repair_prelock, ("prelock_sha256",), "repair prelock")
    repair_receipt_path = verify_file_binding(
        manifest.get("repair_batch_receipt"), "repair batch receipt", inside_candidate=True
    )
    repair_receipt = load_json(repair_receipt_path, "repair batch receipt")
    verify_internal_hash(repair_receipt, ("receipt_sha256",), "repair batch receipt")
    concurrency_evidence = verify_repair_concurrency_evidence(
        repair_prelock,
        repair_receipt,
        repair_root=repair_receipt_path.parent,
    )
    if (
        concurrency_evidence != manifest.get("repair_concurrency_evidence")
        or manifest.get("repair_concurrency_audit")
        != concurrency_evidence.get("summary")
        or manifest.get("repair_concurrency_samples")
        != concurrency_evidence.get("samples")
    ):
        raise RepairPipelineError(
            "effective manifest repair concurrency evidence/audit/samples differ from raw revalidation"
        )
    strict_path = verify_file_binding(
        (repair_prelock.get("repair_tool_bindings") or {}).get("strict_qc_base"),
        "repair-prelocked strict QC base",
        inside_candidate=True,
    )
    base = import_base(strict_path)
    source_prelock_path = verify_file_binding(
        manifest.get("source_prelock"), "source draft prelock", inside_candidate=True
    )
    source_wave = resolve_repo_path(
        repair_prelock.get("source_draft", {}).get("raw_wave"), inside_candidate=True
    )
    # The immutable implementation is reused unchanged; only its location-derived
    # globals are rebound to the original candidate/source context.
    base.WORK_ROOT = WORK_ROOT
    base.REPO_ROOT = REPO_ROOT
    base.DEFAULT_PRELOCK = source_prelock_path
    base.DEFAULT_WAVE_ROOT = source_wave
    base.DEFAULT_REPORT_ROOT = WORK_ROOT / "draft_generation" / "automatic_qc_v3"
    base.EXPECTED_PACKET_ROOT = WORK_ROOT / "case_packets" / "androidworld"
    source_prelock, context, global_problems = base.validate_prelock(
        source_prelock_path,
        skip_live_login_check=args.skip_live_login_check,
    )
    order = list(context["case_order"])
    if order != list(manifest["case_order"]):
        raise RepairPipelineError("strict QC source order differs from effective manifest")
    batch_records, record_problems = base.load_batch_records(effective_root)
    global_problems.extend(record_problems)
    global_problems.extend(
        base.validate_batch_summary(effective_root, case_order=order, records=batch_records)
    )
    packet_by_case = context["packet_by_case"]
    repair_input_by_case = {
        row["case_unit_id"]: row for row in repair_prelock.get("repair_inputs") or []
    }
    source_records = {
        row["case_unit_dir"]: row
        for row in load_jsonl(source_wave / "_batch_results.jsonl")
    }
    for case_id in order:
        record = batch_records.get(case_id) or {}
        effective_row = effective_by_case[case_id]
        origin = effective_row["origin"]
        authority = record.get("qc_authority_full_packet")
        model_input = record.get("model_input_case_packet")
        try:
            authority_path = verify_file_binding(
                authority, f"{case_id} QC authority packet", inside_candidate=True
            )
            expected_authority = resolve_repo_path(
                packet_by_case[case_id]["path"], inside_candidate=True
            )
            if authority_path != expected_authority:
                raise RepairPipelineError("QC authority path differs from frozen full packet")
            model_path = verify_file_binding(
                model_input, f"{case_id} actual model input", inside_candidate=True
            )
            if origin == "repair":
                expected_model = resolve_repo_path(
                    repair_input_by_case[case_id]["bindings"]["batch_packet"]["path"],
                    inside_candidate=True,
                )
                provenance_path = resolve_repo_path(
                    effective_row["repair_provenance"]["path"], inside_candidate=True
                )
                provenance = load_json(provenance_path, f"{case_id} repair provenance")
                expected_source_hash = provenance.get("batch_record_sha256")
            else:
                expected_model = expected_authority
                expected_source_hash = object_sha256(source_records[case_id])
            if model_path != expected_model:
                raise RepairPipelineError("actual model input path differs from origin provenance")
            if record.get("effective_origin") != origin:
                raise RepairPipelineError("effective batch origin differs from manifest")
            if record.get("source_batch_record_sha256") != expected_source_hash:
                raise RepairPipelineError("source batch record hash differs from origin provenance")
        except (RepairPipelineError, Exception) as exc:
            global_problems.append(
                base.issue(
                    "effective_batch_dual_packet_provenance_invalid",
                    str(exc),
                    check="batch_result",
                    detail=case_id,
                )
            )
    roles = (context.get("snapshot_info") or {}).get("role_paths") or {}
    schema_path = roles.get("checklist_schema")
    guardrail_path = roles.get("checklist_guardrails")
    if schema_path is None or guardrail_path is None:
        raise RepairPipelineError("source v3 snapshot schema/guardrail roles are unavailable")
    schema = base.load_json(schema_path)
    guardrail = base.load_guardrail_module(guardrail_path)
    failed_checks = {
        item["check"]
        for item in global_problems
        if item.get("severity") == "error" and item.get("check") in base.CHECK_NAMES
    }
    report_root = args.report_root.resolve()
    try:
        report_root.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("effective QC report root must be inside candidate116") from exc
    staging = guarded_output_directory(report_root)
    generated_at = utc_now()
    reports: list[dict[str, Any]] = []
    try:
        for rank, case_id in enumerate(order):
            report = base.per_case_qc(
                case_id=case_id,
                rank=rank,
                packet_record=context["packet_by_case"].get(case_id),
                wave_root=effective_root,
                batch_record=batch_records.get(case_id),
                schema=schema,
                guardrail_module=guardrail,
                config=context["config"],
                global_input_failed_checks=failed_checks,
            )
            origin = effective_by_case[case_id]
            report.update(
                {
                    "generated_at": generated_at,
                    "effective_wave_id": manifest["effective_wave_id"],
                    "effective_manifest_sha256": manifest["effective_manifest_sha256"],
                    "effective_origin": origin["origin"],
                    "effective_origin_sha256": origin["effective_origin"]["origin_sha256"],
                    "repair_provenance_sha256": (
                        (origin.get("repair_provenance") or {}).get("provenance_sha256")
                    ),
                }
            )
            write_json_atomic(staging / case_id / "qc.json", report)
            reports.append(report)
        passed = [report["case_unit_id"] for report in reports if report["status"] == "passed"]
        failed = [report["case_unit_id"] for report in reports if report["status"] != "passed"]
        all_passed = (
            len(passed) == EXPECTED_CASE_COUNT
            and not failed
            and not any(item.get("severity") == "error" for item in global_problems)
        )
        report_index = []
        for rank, report in enumerate(reports):
            staged = staging / report["case_unit_id"] / "qc.json"
            binding = file_binding(staged)
            binding["path"] = repo_relative(report_root / report["case_unit_id"] / "qc.json")
            report_index.append(
                {
                    "selection_rank": rank,
                    "case_unit_id": report["case_unit_id"],
                    "status": report["status"],
                    "report": binding,
                }
            )
        summary = {
            "schema_version": "androidworld_effective_checklist_automatic_qc_summary/v1",
            "generated_at": generated_at,
            "status": "pass" if all_passed else "fail",
            "case_count": EXPECTED_CASE_COUNT,
            "passed_count": len(passed),
            "failed_count": len(failed),
            "passed_cases": passed,
            "failed_cases": failed,
            "global_issues": global_problems,
            "effective_manifest": file_binding(manifest_path)
            | {"effective_manifest_sha256": manifest["effective_manifest_sha256"]},
            "repair_prelock": file_binding(repair_prelock_path)
            | {"prelock_sha256": repair_prelock["prelock_sha256"]},
            "repair_concurrency_evidence": concurrency_evidence,
            "repair_concurrency_audit": concurrency_evidence["summary"],
            "repair_concurrency_samples": concurrency_evidence["samples"],
            "strict_qc_base": file_binding(strict_path),
            "strict_qc_reuse": {
                "function": "per_case_qc",
                "implementation_modified": False,
                "location_globals_rebound_only": True,
            },
            "case_report_index": report_index,
            "promotion_gate": {
                "automatic_gate_passed": all_passed,
                "repair_concurrency_raw_samples_revalidated": True,
                "independent_codex_semantic_reviews_required": True,
                "explicit_root_agent_acceptance_required": True,
                "human_review_claimed": False,
                "promotion_authorized_by_this_report_alone": False,
            },
        }
        summary = add_self_hash(summary, "summary_sha256")
        write_json_atomic(staging / "summary.json", summary)
        atomic_promote_directory(staging, report_root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(
        json.dumps(
            {
                "status": summary["status"],
                "passed_count": summary["passed_count"],
                "failed_count": summary["failed_count"],
                "summary": file_binding(report_root / "summary.json")
                | {"summary_sha256": summary["summary_sha256"]},
            },
            indent=2,
        )
    )
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RepairPipelineError, Exception) as exc:
        # Base QC raises its own fatal exception type; wrap it uniformly here.
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
