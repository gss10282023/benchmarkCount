#!/usr/bin/env python3
"""Run prelocked checklist repairs through the immutable v3 batch runner."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import SemanticReviewError

from repair_pipeline_common import (
    EXPECTED_PARALLELISM,
    REPAIR_CONFIG_SCHEMA,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    canonical_diff,
    case_file_bindings,
    file_binding,
    load_json,
    load_jsonl,
    load_repair_prelock,
    load_source_prelock,
    load_yaml_mapping,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    tree_record,
    utc_now,
    verify_binding_tree,
    verify_checklist_pair,
    verify_file_binding,
    verify_internal_hash,
    verify_source_wave_complete,
    write_json_atomic,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path, required=False)
    parser.add_argument(
        "--restart-after-incident",
        action="store_true",
        help="Archive the entire pre-existing failed repair wave, then restart from empty.",
    )
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def current_codex(prelock: Mapping[str, Any]) -> dict[str, Any]:
    raw = shutil.which("codex")
    if not raw:
        raise RepairPipelineError("codex is not on PATH")
    binary = Path(raw).resolve()
    expected = prelock.get("codex_cli") or {}
    if str(binary) != expected.get("binary_path") or sha256_file(binary) != expected.get("binary_sha256"):
        raise RepairPipelineError("Codex CLI binary/path changed after repair prelock")
    version = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, check=False, timeout=30
    )
    login = subprocess.run(
        [str(binary), "login", "status"], capture_output=True, text=True, check=False, timeout=30
    )
    detail = "\n".join(part.strip() for part in (login.stdout, login.stderr) if part.strip())
    if version.returncode != 0 or login.returncode != 0 or "logged in" not in detail.casefold():
        raise RepairPipelineError(f"Codex login is inactive: {detail}")
    if (version.stdout or version.stderr).strip() != expected.get("version"):
        raise RepairPipelineError("Codex CLI version output changed after repair prelock")
    return {"binary_path": str(binary), "binary_sha256": sha256_file(binary), "login": detail}


def verify_prelocked_context(prelock_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prelock = load_repair_prelock(prelock_path)
    config_path = verify_file_binding(prelock.get("repair_config"), "repair config", inside_candidate=True)
    config = load_json(config_path, "repair config")
    if config.get("schema_version") != REPAIR_CONFIG_SCHEMA or config.get("status") != "prelocked":
        raise RepairPipelineError("repair config schema/status is invalid")
    verify_internal_hash(config, ("config_sha256",), "repair config")
    if prelock["repair_config"].get("config_sha256") != config["config_sha256"]:
        raise RepairPipelineError("repair config internal hash differs from prelock")
    expected = {
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "sandbox": "read-only",
        "ephemeral": True,
        "ignore_user_config": True,
        "max_parallel": EXPECTED_PARALLELISM,
        "large_max_parallel": EXPECTED_PARALLELISM,
        "quality_check": "none",
        "repair_count": prelock["repair_count"],
    }
    for field, wanted in expected.items():
        if config.get(field) != wanted:
            raise RepairPipelineError(f"repair config {field} is not {wanted!r}")
    snapshot_path = verify_file_binding(
        prelock.get("repair_toolchain_snapshot"), "repair toolchain snapshot", inside_candidate=True
    )
    snapshot = load_json(snapshot_path, "repair snapshot")
    verify_internal_hash(snapshot, ("snapshot_sha256",), "repair snapshot")
    if snapshot.get("snapshot_sha256") != prelock["repair_toolchain_snapshot"].get("snapshot_sha256"):
        raise RepairPipelineError("repair snapshot hash differs from prelock")
    snapshot_files = list(snapshot.get("files") or [])
    if (
        snapshot.get("file_count") != len(snapshot_files)
        or snapshot.get("files_sha256") != object_sha256(snapshot_files)
    ):
        raise RepairPipelineError("repair snapshot file index is invalid")
    for index, binding in enumerate(snapshot_files):
        verify_file_binding(binding, f"repair snapshot file {index}", inside_candidate=True)
    for name, binding in (prelock.get("repair_tool_bindings") or {}).items():
        verify_file_binding(binding, f"repair tool {name}", inside_candidate=True)
        if (snapshot.get("roles") or {}).get(name) != binding:
            raise RepairPipelineError(f"repair role {name} differs from snapshot manifest")
    for name, binding in (prelock.get("original_v3_tool_bindings") or {}).items():
        verify_file_binding(binding, f"original v3 tool {name}", inside_candidate=True)
    source_path = verify_file_binding(
        prelock.get("source_draft", {}).get("prelock"), "source draft prelock", inside_candidate=True
    )
    source = load_source_prelock(source_path)
    verify_source_wave_complete(source)
    for row in prelock["repair_inputs"]:
        verify_binding_tree(row["bindings"], f"{row['case_unit_id']} repair inputs")
        descriptor_path = verify_file_binding(row["descriptor"], f"{row['case_unit_id']} descriptor", inside_candidate=True)
        descriptor = load_json(descriptor_path, f"{row['case_unit_id']} descriptor")
        verify_internal_hash(descriptor, ("descriptor_sha256",), f"{row['case_unit_id']} descriptor")
        if descriptor.get("descriptor_sha256") != row["descriptor"].get("descriptor_sha256"):
            raise RepairPipelineError(f"{row['case_unit_id']} descriptor internal hash differs")
    return prelock, config, source


def archive_existing(output_root: Path, prelock: Mapping[str, Any]) -> Path:
    if not output_root.exists():
        raise RepairPipelineError("--restart-after-incident was supplied but no prior output exists")
    record = tree_record(output_root)
    incident_id = f"{utc_now().replace(':', '').replace('+', '_')}_{record['tree_sha256'][:12]}"
    incident_root = WORK_ROOT / "repair_generation" / "incidents" / prelock["repair_id"] / incident_id
    if incident_root.exists():
        raise RepairPipelineError(f"incident archive already exists: {incident_root}")
    incident_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(output_root), str(incident_root))
    incident = {
        "schema_version": "androidworld_checklist_repair_restart_incident/v1",
        "created_at": utc_now(),
        "repair_id": prelock["repair_id"],
        "status": "archived_failed_or_incomplete_attempt",
        "promotion_forbidden": True,
        "archived_tree": record | {"archived_path": repo_relative(incident_root)},
        "repair_prelock_sha256": prelock["prelock_sha256"],
    }
    incident = add_self_hash(incident, "incident_sha256")
    write_json_atomic(incident_root / "_restart_incident.json", incident)
    return incident_root


def command_for(config: Mapping[str, Any], prelock: Mapping[str, Any]) -> list[str]:
    runner = verify_file_binding(config["frozen_batch_runner"], "frozen v3 batch runner", inside_candidate=True)
    prompt = verify_file_binding(config["repair_prompt"], "repair prompt", inside_candidate=True)
    packet_root = resolve_repo_path(config["packet_set_root"], inside_candidate=True)
    output_root = resolve_repo_path(config["output_root"], inside_candidate=True)
    return [
        sys.executable,
        str(runner),
        "--case-packet-root",
        str(packet_root),
        "--output-root",
        str(output_root),
        "--provider",
        "codex",
        "--model",
        "gpt-5.6-sol",
        "--reasoning-effort",
        "xhigh",
        "--token-budgets",
        "12000,16000,20000",
        "--max-parallel",
        "6",
        "--large-max-parallel",
        "6",
        "--large-case-threshold-bytes",
        "180000",
        "--codex-timeout-seconds",
        str(config["codex_timeout_seconds"]),
        "--large-codex-timeout-seconds",
        str(config["large_codex_timeout_seconds"]),
        "--codex-sandbox",
        "read-only",
        "--prompt-supplement",
        str(prompt),
        "--quality-check",
        "none",
        "--sort-by",
        "name",
    ]


def validate_and_record(
    prelock_path: Path,
    prelock: Mapping[str, Any],
    config: Mapping[str, Any],
    source: Mapping[str, Any],
) -> dict[str, Any]:
    output_root = resolve_repo_path(config["output_root"], inside_candidate=True)
    summary_path = output_root / "_batch_summary.json"
    results_path = output_root / "_batch_results.jsonl"
    summary = load_json(summary_path, "repair batch summary")
    expected = {
        "total_cases": prelock["repair_count"],
        "completed_cases": prelock["repair_count"],
        "success_cases": prelock["repair_count"],
        "skipped_cases": 0,
        "failed_cases": 0,
        "provider": "codex",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "codex_sandbox": "read-only",
        "quality_check": "none",
    }
    for field, wanted in expected.items():
        if summary.get(field) != wanted:
            raise RepairPipelineError(f"repair batch summary {field}={summary.get(field)!r}, expected {wanted!r}")
    records_list = load_jsonl(results_path)
    records: dict[str, dict[str, Any]] = {}
    for record in records_list:
        case_id = str(record.get("case_unit_dir") or "")
        if case_id in records:
            raise RepairPipelineError(f"duplicate repair batch record: {case_id}")
        records[case_id] = record
    expected_cases = {row["case_unit_id"] for row in prelock["repair_inputs"]}
    observed_dirs = {path.name for path in output_root.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if set(records) != expected_cases or observed_dirs != expected_cases:
        raise RepairPipelineError("repair output/results case set differs from prelock")
    source_wave = resolve_repo_path(prelock["source_draft"]["raw_wave"], inside_candidate=True)
    input_by_case = {row["case_unit_id"]: row for row in prelock["repair_inputs"]}
    provenance_rows: list[dict[str, Any]] = []
    for case_id in prelock["case_order"]:
        if case_id not in expected_cases:
            continue
        record = records[case_id]
        if record.get("status") != "success" or record.get("quality_warnings") not in ([], None):
            raise RepairPipelineError(f"{case_id} repair batch record is not clean success")
        attempts = [
            item for item in record.get("attempts") or []
            if isinstance(item, Mapping)
            and item.get("returncode") == 0
            and str(item.get("validator") or "").startswith("checklist valid:")
        ]
        if len(attempts) != 1:
            raise RepairPipelineError(f"{case_id} must have exactly one accepted attempt")
        case_dir = output_root / case_id
        repaired = verify_checklist_pair(case_dir, case_id)
        original = verify_checklist_pair(source_wave / case_id, case_id)
        changes = canonical_diff(original, repaired)
        if not changes:
            raise RepairPipelineError(f"{case_id} repair output is byte/semantic identical to original")
        diff = {
            "schema_version": "androidworld_checklist_repair_diff/v1",
            "case_unit_id": case_id,
            "task_id": case_id,
            "change_count": len(changes),
            "changes": changes,
            "before_sha256": sha256_file(source_wave / case_id / "checklist.yaml"),
            "after_sha256": sha256_file(case_dir / "checklist.yaml"),
        }
        diff = add_self_hash(diff, "diff_sha256")
        diff_path = case_dir / "repair_diff.json"
        write_json_atomic(diff_path, diff)
        inputs = input_by_case[case_id]
        provenance = {
            "schema_version": "androidworld_checklist_repair_provenance/v1",
            "created_at": utc_now(),
            "repair_id": prelock["repair_id"],
            "case_unit_id": case_id,
            "task_id": case_id,
            "selection_rank": inputs["selection_rank"],
            "repair_prelock": file_binding(prelock_path) | {"prelock_sha256": prelock["prelock_sha256"]},
            "repair_config_sha256": config["config_sha256"],
            "audit_case_sha256": inputs["audit_case_sha256"],
            "repair_packet_sha256": inputs["repair_packet_sha256"],
            "input_bindings": inputs["bindings"],
            "output_sidecars": case_file_bindings(case_dir),
            "accepted_attempt": attempts[0],
            "batch_record_sha256": object_sha256(record),
            "repair_diff": file_binding(diff_path) | {"diff_sha256": diff["diff_sha256"]},
            "promotion_authorized": False,
        }
        provenance = add_self_hash(provenance, "provenance_sha256")
        provenance_path = case_dir / "repair_provenance.json"
        write_json_atomic(provenance_path, provenance)
        provenance_rows.append(
            {
                "selection_rank": inputs["selection_rank"],
                "case_unit_id": case_id,
                "provenance": file_binding(provenance_path)
                | {"provenance_sha256": provenance["provenance_sha256"]},
                "output_checklist": file_binding(case_dir / "checklist.yaml"),
            }
        )
    provenance_rows.sort(key=lambda row: row["selection_rank"])
    repair_summary = {
        "schema_version": "androidworld_checklist_repair_batch_receipt/v1",
        "created_at": utc_now(),
        "status": "repair_generation_complete_not_promoted",
        "repair_id": prelock["repair_id"],
        "repair_count": prelock["repair_count"],
        "retain_count": prelock["retain_count"],
        "case_count_after_effective_composition": 116,
        "repair_prelock": file_binding(prelock_path) | {"prelock_sha256": prelock["prelock_sha256"]},
        "raw_batch_summary": file_binding(summary_path),
        "raw_batch_results": file_binding(results_path),
        "case_provenance": provenance_rows,
        "case_provenance_sha256": object_sha256(provenance_rows),
        "effective_wave_required": True,
        "strict_effective_qc_required": True,
        "new_human_reviews_required": True,
    }
    repair_summary = add_self_hash(repair_summary, "receipt_sha256")
    receipt_path = output_root / "_repair_batch_receipt.json"
    write_json_atomic(receipt_path, repair_summary)
    return repair_summary


def self_test() -> int:
    before = {"a": 1, "b": [1, {"c": 2}]}
    after = {"a": 2, "b": [1, {"c": 3}], "d": True}
    observed = canonical_diff(before, after)
    paths = [item["path"] for item in observed]
    if paths != ["$.a", "$.b[1].c", "$.d"]:
        raise RepairPipelineError(f"canonical diff self-test failed: {paths}")
    print(json.dumps({"status": "self_test_pass", "changed_paths": paths}, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.prelock is None:
        raise RepairPipelineError("--prelock is required unless --self-test is used")
    prelock_path = args.prelock.resolve()
    prelock, config, source = verify_prelocked_context(prelock_path)
    output_root = resolve_repo_path(config["output_root"], inside_candidate=True)
    if output_root.exists():
        if not args.restart_after_incident:
            raise RepairPipelineError(
                "repair output already exists; use --restart-after-incident to archive the entire tree"
            )
        archived = archive_existing(output_root, prelock)
        print(f"Archived prior repair attempt at {archived}", flush=True)
    elif args.restart_after_incident:
        raise RepairPipelineError("--restart-after-incident requires a pre-existing output tree")
    current_codex(prelock)
    command = command_for(config, prelock)
    completed = subprocess.run(command, cwd=WORK_ROOT.parents[3], check=False)
    if completed.returncode != 0:
        raise RepairPipelineError(
            f"frozen v3 batch runner returned {completed.returncode}; preserve output and restart only via incident"
        )
    receipt = validate_and_record(prelock_path, prelock, config, source)
    # Re-read every prelocked input/tool after the calls to catch concurrent mutation.
    verify_prelocked_context(prelock_path)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "repair_id": prelock["repair_id"],
                "repair_count": prelock["repair_count"],
                "receipt_sha256": receipt["receipt_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
