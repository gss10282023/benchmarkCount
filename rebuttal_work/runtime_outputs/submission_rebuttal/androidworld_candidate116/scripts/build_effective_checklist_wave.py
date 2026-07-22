#!/usr/bin/env python3
"""Compose the immutable 116-case effective wave from wave_003 and repairs."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

from repair_pipeline_common import (
    EFFECTIVE_MANIFEST_SCHEMA,
    EXPECTED_CASE_COUNT,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    atomic_promote_directory,
    file_binding,
    guarded_output_directory,
    load_json,
    load_jsonl,
    load_repair_prelock,
    load_source_prelock,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    tree_record,
    utc_now,
    verify_checklist_pair,
    verify_file_binding,
    verify_internal_hash,
    verify_repair_concurrency_evidence,
    verify_source_wave_complete,
    write_jsonl,
)
from semantic_review_common import write_json_atomic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def record_map(path: Path, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        case_id = str(row.get("case_unit_dir") or "")
        if not case_id or case_id in result:
            raise RepairPipelineError(f"{label} contains invalid/duplicate case id {case_id!r}")
        result[case_id] = row
    return result


def validate_repair_receipt(
    prelock: Mapping[str, Any], repair_root: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    path = repair_root / "_repair_batch_receipt.json"
    receipt = load_json(path, "repair batch receipt")
    verify_internal_hash(receipt, ("receipt_sha256",), "repair batch receipt")
    if (
        receipt.get("status") != "repair_generation_complete_not_promoted"
        or receipt.get("repair_id") != prelock.get("repair_id")
        or receipt.get("repair_count") != prelock.get("repair_count")
    ):
        raise RepairPipelineError("repair batch receipt identity/status/count is invalid")
    rows = list(receipt.get("case_provenance") or [])
    if len(rows) != prelock["repair_count"] or receipt.get("case_provenance_sha256") != object_sha256(rows):
        raise RepairPipelineError("repair receipt provenance index is invalid")
    by_case: dict[str, Any] = {}
    for row in rows:
        case_id = str(row.get("case_unit_id") or "")
        if case_id in by_case:
            raise RepairPipelineError(f"duplicate repair provenance for {case_id}")
        provenance_path = verify_file_binding(row.get("provenance"), f"{case_id} repair provenance", inside_candidate=True)
        provenance = load_json(provenance_path, f"{case_id} repair provenance")
        verify_internal_hash(provenance, ("provenance_sha256",), f"{case_id} repair provenance")
        if provenance.get("provenance_sha256") != row["provenance"].get("provenance_sha256"):
            raise RepairPipelineError(f"{case_id} repair provenance internal hash differs")
        verify_file_binding(row.get("output_checklist"), f"{case_id} repair checklist", inside_candidate=True)
        by_case[case_id] = {"row": row, "value": provenance, "path": provenance_path}
    concurrency_evidence = verify_repair_concurrency_evidence(
        prelock,
        receipt,
        repair_root=repair_root,
    )
    # The locked common verifier independently re-reads the audit JSON and raw
    # JSONL stream, verifies every self-hashed sample and exact prelock/runtime
    # binding, and recomputes the six-worker peak plus the exact 80-case
    # coverage.  Keep the two raw file bindings explicit at this composition
    # boundary so later handoff/freeze stages cannot silently retain only an
    # aggregate boolean.
    verify_internal_hash(
        concurrency_evidence,
        ("evidence_sha256",),
        "repair concurrency evidence",
    )
    audit_path = verify_file_binding(
        concurrency_evidence.get("summary"),
        "repair concurrency audit",
        inside_candidate=True,
    )
    samples_path = verify_file_binding(
        concurrency_evidence.get("samples"),
        "repair concurrency samples",
        inside_candidate=True,
    )
    receipt_audit_path = verify_file_binding(
        receipt.get("concurrency_audit"),
        "repair receipt concurrency audit",
        inside_candidate=True,
    )
    audit = load_json(audit_path, "repair concurrency audit")
    verify_internal_hash(audit, ("audit_sha256",), "repair concurrency audit")
    audit_samples_path = verify_file_binding(
        audit.get("samples"),
        "repair concurrency audit samples",
        inside_candidate=True,
    )
    if (
        audit_path != receipt_audit_path
        or audit_samples_path != samples_path
        or concurrency_evidence["summary"].get("audit_sha256")
        != audit.get("audit_sha256")
        or concurrency_evidence.get("raw_samples_revalidated") is not True
        or concurrency_evidence.get("observed_peak_active_case_attempts") != 6
        or concurrency_evidence.get("expected_case_count") != 80
        or concurrency_evidence.get("observed_case_count") != 80
    ):
        raise RepairPipelineError(
            "repair receipt concurrency audit/sample bindings are not an exact-6, 80-case proof"
        )
    return receipt, by_case, concurrency_evidence


def normalized_batch_record(
    record: Mapping[str, Any],
    *,
    packet_record: Mapping[str, Any],
    final_case_dir: Path,
    origin: str,
    model_input: Mapping[str, Any],
) -> dict[str, Any]:
    result = copy.deepcopy(dict(record))
    packet_path = resolve_repo_path(packet_record["path"], inside_candidate=True)
    result["case_packet"] = str(packet_path)
    result["case_packet_size_bytes"] = packet_record["size_bytes"]
    result["checklist_path"] = str(final_case_dir / "checklist.yaml")
    result["status"] = "success"
    result["quality_warnings"] = []
    result["effective_record_semantics"] = (
        "case_packet/qc_authority_full_packet identify the frozen full packet used by strict QC; "
        "model_input_case_packet identifies the actual bytes supplied to the drafting call"
    )
    result["effective_origin"] = origin
    result["source_batch_record_sha256"] = object_sha256(record)
    result["model_input_case_packet"] = dict(model_input)
    result["qc_authority_full_packet"] = file_binding(packet_path)
    return result


def relocated_binding(staged: Path, final: Path) -> dict[str, Any]:
    binding = file_binding(staged)
    binding["path"] = repo_relative(final)
    return binding


def relocated_tree(staged: Path, final: Path) -> dict[str, Any]:
    record = tree_record(staged)
    record["path"] = repo_relative(final)
    return record


def main() -> int:
    args = parse_args()
    if args.self_test and args.prelock is None:
        synthetic = {"case_unit_dir": "Synthetic", "status": "success", "attempts": []}
        authority_path = Path(__file__).resolve()
        packet_record = file_binding(authority_path)
        observed = normalized_batch_record(
            synthetic,
            packet_record=packet_record,
            final_case_dir=WORK_ROOT / "never_written" / "Synthetic",
            origin="repair",
            model_input=file_binding(authority_path),
        )
        required = {
            "effective_origin": "repair",
            "source_batch_record_sha256": object_sha256(synthetic),
            "model_input_case_packet": file_binding(authority_path),
            "qc_authority_full_packet": file_binding(authority_path),
        }
        if any(observed.get(key) != value for key, value in required.items()):
            raise RepairPipelineError("effective dual-packet provenance fixture failed")
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "model_input_preserved": True,
                    "qc_authority_preserved": True,
                    "source_record_hash_preserved": True,
                    "writes_performed": False,
                },
                indent=2,
            )
        )
        return 0
    if args.prelock is None:
        raise RepairPipelineError("--prelock is required unless standalone --self-test is used")
    prelock_path = args.prelock.resolve()
    prelock = load_repair_prelock(prelock_path)
    source_prelock_path = verify_file_binding(
        prelock.get("source_draft", {}).get("prelock"), "source prelock", inside_candidate=True
    )
    source = load_source_prelock(source_prelock_path)
    source_wave, source_records = verify_source_wave_complete(source)
    order = list(source["case_order"])
    if order != list(prelock.get("case_order") or []):
        raise RepairPipelineError("repair and source prelock case orders differ")
    repair_root = resolve_repo_path(
        load_json(
            verify_file_binding(prelock["repair_config"], "repair config", inside_candidate=True),
            "repair config",
        )["output_root"],
        inside_candidate=True,
    )
    receipt, repair_provenance, concurrency_evidence = validate_repair_receipt(
        prelock, repair_root
    )
    repair_records = record_map(repair_root / "_batch_results.jsonl", "repair batch results")
    repair_cases = {row["case_unit_id"] for row in prelock["repair_inputs"]}
    if set(repair_records) != repair_cases or set(repair_provenance) != repair_cases:
        raise RepairPipelineError("repair records/provenance set differs from prelock")
    retain_cases = {row["case_unit_id"] for row in prelock["retain_inputs"]}
    if repair_cases & retain_cases or repair_cases | retain_cases != set(order):
        raise RepairPipelineError("repair/retain partition is not exact candidate116")
    packet_by_case = {row["case_unit_id"]: row for row in source["packet_inputs"]}
    audit_sha_by_case = {
        row["case_unit_id"]: row["audit_case_sha256"]
        for row in [*prelock["repair_inputs"], *prelock["retain_inputs"]]
    }
    repair_input_by_case = {row["case_unit_id"]: row for row in prelock["repair_inputs"]}
    effective_root = resolve_repo_path(
        prelock["canonical_output_gate"]["effective_wave"], inside_candidate=True
    )
    if args.self_test:
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "repair_count": len(repair_cases),
                    "retain_count": len(retain_cases),
                    "effective_root_absent": not effective_root.exists(),
                },
                indent=2,
            )
        )
        return 0
    staging = guarded_output_directory(effective_root)
    final_rows: list[dict[str, Any]] = []
    batch_rows: list[dict[str, Any]] = []
    try:
        for rank, case_id in enumerate(order):
            origin = "repair" if case_id in repair_cases else "wave_003"
            source_case_dir = repair_root / case_id if origin == "repair" else source_wave / case_id
            final_case_dir = effective_root / case_id
            staged_case_dir = staging / case_id
            shutil.copytree(source_case_dir, staged_case_dir)
            verify_checklist_pair(staged_case_dir, case_id)
            origin_record: dict[str, Any] = {
                "schema_version": "androidworld_effective_checklist_origin/v1",
                "effective_wave_id": effective_root.name,
                "case_unit_id": case_id,
                "task_id": case_id,
                "selection_rank": rank,
                "origin": origin,
                "audit_case_sha256": audit_sha_by_case[case_id],
                "source_case_tree": tree_record(source_case_dir),
                "source_checklist": file_binding(source_case_dir / "checklist.yaml"),
                "repair_provenance": None,
            }
            if origin == "repair":
                item = repair_provenance[case_id]
                origin_record["repair_provenance"] = file_binding(item["path"]) | {
                    "provenance_sha256": item["value"]["provenance_sha256"]
                }
            origin_record = add_self_hash(origin_record, "origin_sha256")
            origin_path = staged_case_dir / "effective_origin.json"
            write_json_atomic(origin_path, origin_record)
            record = repair_records[case_id] if origin == "repair" else source_records[case_id]
            batch_rows.append(
                normalized_batch_record(
                    record,
                    packet_record=packet_by_case[case_id],
                    final_case_dir=final_case_dir,
                    origin=origin,
                    model_input=(
                        repair_input_by_case[case_id]["bindings"]["batch_packet"]
                        if origin == "repair"
                        else file_binding(resolve_repo_path(packet_by_case[case_id]["path"], inside_candidate=True))
                    ),
                )
            )
            final_rows.append(
                {
                    "selection_rank": rank,
                    "case_unit_id": case_id,
                    "task_id": case_id,
                    "origin": origin,
                    "audit_case_sha256": audit_sha_by_case[case_id],
                    "effective_checklist": relocated_binding(
                        staged_case_dir / "checklist.yaml", final_case_dir / "checklist.yaml"
                    ),
                    "effective_origin": relocated_binding(
                        origin_path, final_case_dir / "effective_origin.json"
                    )
                    | {"origin_sha256": origin_record["origin_sha256"]},
                    "effective_case_tree": relocated_tree(staged_case_dir, final_case_dir),
                    "repair_provenance": origin_record["repair_provenance"],
                }
            )
        write_jsonl(staging / "_batch_results.jsonl", batch_rows)
        batch_summary = {
            "started_at": utc_now(),
            "updated_at": utc_now(),
            "total_cases": EXPECTED_CASE_COUNT,
            "completed_cases": EXPECTED_CASE_COUNT,
            "success_cases": EXPECTED_CASE_COUNT,
            "skipped_cases": 0,
            "failed_cases": 0,
            "warning_count": 0,
            "provider": "codex",
            "model": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "codex_sandbox": "read-only",
            "prompt_supplement": "mixed_prelocked_wave_003_and_repair_prompt_by_origin",
            "token_budgets": [12000, 16000, 20000],
            "sort_by": "effective_candidate116_order",
            "quality_check": "none",
            "large_case_threshold_bytes": 180000,
            "lane_stats": {"effective": {"count": EXPECTED_CASE_COUNT}},
            "output_root": str(effective_root),
            "origin_counts": {"wave_003": len(retain_cases), "repair": len(repair_cases)},
        }
        write_json_atomic(staging / "_batch_summary.json", batch_summary)
        manifest = {
            "schema_version": EFFECTIVE_MANIFEST_SCHEMA,
            "status": "composed_not_qc_or_independent_codex_root_agent_accepted",
            "created_at": utc_now(),
            "effective_wave_id": effective_root.name,
            "case_count": EXPECTED_CASE_COUNT,
            "case_order": order,
            "case_order_sha256": object_sha256(order),
            "origin_counts": {"wave_003": len(retain_cases), "repair": len(repair_cases)},
            "repair_prelock": file_binding(prelock_path) | {"prelock_sha256": prelock["prelock_sha256"]},
            "source_prelock": file_binding(source_prelock_path)
            | {"prelock_sha256": source["prelock_sha256"]},
            "repair_batch_receipt": file_binding(repair_root / "_repair_batch_receipt.json")
            | {"receipt_sha256": receipt["receipt_sha256"]},
            "repair_concurrency_evidence": concurrency_evidence,
            "repair_concurrency_audit": copy.deepcopy(concurrency_evidence["summary"]),
            "repair_concurrency_samples": copy.deepcopy(concurrency_evidence["samples"]),
            "effective_batch_results": relocated_binding(
                staging / "_batch_results.jsonl", effective_root / "_batch_results.jsonl"
            ),
            "effective_batch_summary": relocated_binding(
                staging / "_batch_summary.json", effective_root / "_batch_summary.json"
            ),
            "cases": final_rows,
            "cases_sha256": object_sha256(final_rows),
            "promotion_requirements": {
                "strict_effective_qc_116_of_116": True,
                "repair_concurrency_raw_samples_revalidated": True,
                "independent_codex_semantic_review_116_of_116": True,
                "explicit_root_agent_acceptance_116_of_116": True,
                "human_review_claimed": False,
                "repair_aware_handoff": True,
                "legacy_wave3_direct_promotion_forbidden": True,
            },
            "effective_batch_record_policy": {
                "case_packet_field_is_qc_authority_full_packet": True,
                "actual_model_input_preserved_in_model_input_case_packet": True,
                "source_batch_record_hash_preserved": True,
            },
        }
        manifest = add_self_hash(manifest, "effective_manifest_sha256")
        write_json_atomic(staging / "_effective_manifest.json", manifest)
        atomic_promote_directory(staging, effective_root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "effective_wave": repo_relative(effective_root),
                "origin_counts": manifest["origin_counts"],
                "manifest": file_binding(effective_root / "_effective_manifest.json")
                | {"effective_manifest_sha256": manifest["effective_manifest_sha256"]},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RepairPipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
