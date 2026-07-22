#!/usr/bin/env python3
"""Atomically freeze an audited remote AppWorld draft batch as claim checklists."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_SCHEMA = "appworld_case_claim_freeze.v1"
CASE_LOCK_SCHEMA = "appworld_case_claim_lock.v1"
FINAL_LOCK_SCHEMA = "appworld_case_claim_final_lock.v1"
ALLOWED_AUDIT_WARNING_CODES = {"codex_stderr_nonempty"}
EXPECTED_AUDIT_CHECKS = {
    "packet_identity_and_sources",
    "batch_success_and_attempt_metadata",
    "canonical_and_successful_attempt_bytes",
    "yaml_json_consistency",
    "json_schema",
    "packet_aware_guardrails",
    "support_pointers",
    "exact_native_and_stronger_semantics",
    "llm_call_identity",
    "codex_runtime_envelope",
    "tool_disabled_argv",
    "direct_stdin_bundle_reconstruction",
    "stderr_and_batch_tail",
    "events_lifecycle_and_final_message",
}


class ClaimFreezeError(RuntimeError):
    """Raised when a claim freeze cannot be built or verified exactly."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ClaimFreezeError(message)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be an object")
    return value


def _canonical_json_bytes(value: Any, *, newline: bool = False) -> bytes:
    suffix = "\n" if newline else ""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + suffix
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_object(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_file(path: Path, label: str) -> Path:
    _require(path.is_file() and not path.is_symlink(), f"{label} is missing or unsafe: {path}")
    return path.resolve()


def _directory(path: Path, label: str) -> Path:
    _require(path.is_dir() and not path.is_symlink(), f"{label} is missing or unsafe: {path}")
    return path.resolve()


def _repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(_regular_file(path, label).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ClaimFreezeError(f"{label} is malformed JSON: {path}: {exc}") from exc
    return _mapping(value, label)


def _load_jsonl(path: Path, label: str) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(
        _regular_file(path, label).read_text(encoding="utf-8").splitlines(), start=1
    ):
        _require(line.strip() != "", f"{label} contains a blank line at {line_number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ClaimFreezeError(
                f"{label} has malformed JSON at line {line_number}: {exc}"
            ) from exc
        rows.append(_mapping(value, f"{label} line {line_number}"))
    return rows


def _strict_tree_inventory(root: Path) -> dict[str, Any]:
    root = _directory(root, "tree root")
    files: list[dict[str, Any]] = []
    directory_count = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        _require(not path.is_symlink(), f"tree contains symlink: {path}")
        if path.is_dir():
            directory_count += 1
            continue
        _require(path.is_file(), f"tree contains a non-regular entry: {path}")
        files.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return {
        "file_count": len(files),
        "directory_count": directory_count,
        "size_bytes": sum(item["size_bytes"] for item in files),
        "strict_tree_sha256": _sha256_object(files),
    }


def _audit_report_semantic_sha256(report: Mapping[str, Any]) -> str:
    return _sha256_object(
        {key: value for key, value in report.items() if key != "report_semantic_sha256"}
    )


def _parse_inventory(path: Path, expected_count: int) -> list[Mapping[str, Any]]:
    expected_fields = {
        "case_unit_id",
        "task_id",
        "domain",
        "dataset_name",
        "split",
        "source_ref",
        "case_packet_sha256",
        "raw_case_manifest_sha256",
    }
    rows = _load_jsonl(path, "case inventory")
    _require(len(rows) == expected_count, "case inventory count mismatch")
    ids: list[str] = []
    for row in rows:
        _require(set(row) == expected_fields, "case inventory field set drift")
        case_id = row.get("case_unit_id")
        _require(isinstance(case_id, str) and case_id, "case inventory ID is invalid")
        _require(
            row.get("task_id") == case_id and row.get("domain") == "appworld",
            f"case inventory identity mismatch: {case_id}",
        )
        ids.append(case_id)
    _require(len(set(ids)) == expected_count, "case inventory has duplicate IDs")
    return rows


def _validate_audit(
    *,
    report_path: Path,
    results_root: Path,
    packet_root: Path,
    runtime_root: Path,
    expected_count: int,
) -> tuple[Mapping[str, Any], dict[str, Mapping[str, Any]]]:
    report = _load_json(report_path, "audit report")
    _require(report.get("status") == "passed", "audit report is not passed")
    _require(
        report.get("report_semantic_sha256") == _audit_report_semantic_sha256(report),
        "audit report semantic hash mismatch",
    )
    inputs = _mapping(report.get("inputs"), "audit inputs")
    for key, expected in (
        ("draft_root", str(results_root.resolve())),
        ("packet_root", str(packet_root.resolve())),
        ("runtime_root", str(runtime_root.resolve())),
        ("expected_count", expected_count),
        ("expected_model", "gpt-5.6-sol"),
        ("expected_reasoning", "max"),
    ):
        _require(inputs.get(key) == expected, f"audit input {key} mismatch")
    summary = _mapping(report.get("summary"), "audit summary")
    _require(
        summary.get("audited_case_count") == expected_count
        and summary.get("passed_case_count") == expected_count
        and summary.get("failed_case_count") == 0
        and summary.get("error_count") == 0
        and summary.get("exit_code") == 0,
        "audit summary is not an exact all-pass result",
    )
    _require(report.get("global_errors") == [], "audit report has global errors")
    cases = report.get("cases")
    _require(isinstance(cases, list) and len(cases) == expected_count, "audit case count mismatch")
    by_id: dict[str, Mapping[str, Any]] = {}
    for raw_case in cases:
        case = _mapping(raw_case, "audit case")
        case_id = case.get("case_unit_id")
        _require(isinstance(case_id, str) and case_id not in by_id, "audit case ID drift")
        checks = _mapping(case.get("checks"), f"{case_id}: audit checks")
        _require(set(checks) == EXPECTED_AUDIT_CHECKS, f"{case_id}: audit check set drift")
        _require(
            case.get("status") == "passed"
            and case.get("errors") == []
            and all(_mapping(value, "audit check").get("status") == "passed" for value in checks.values()),
            f"{case_id}: audit case is not fully passed",
        )
        warnings = case.get("warnings")
        _require(isinstance(warnings, list), f"{case_id}: warnings are invalid")
        _require(
            all(
                isinstance(item, Mapping) and item.get("code") in ALLOWED_AUDIT_WARNING_CODES
                for item in warnings
            ),
            f"{case_id}: unrecognized audit warning",
        )
        by_id[case_id] = case
    return report, by_id


def _source_root_inventory(results_root: Path, case_ids: Sequence[str]) -> dict[str, Any]:
    entries = list(results_root.iterdir())
    directory_ids = {
        path.name for path in entries if path.is_dir() and not path.is_symlink()
    }
    files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    _require(directory_ids == set(case_ids), "source result case-directory set mismatch")
    _require(files == {"_batch_results.jsonl", "_batch_summary.json"}, "source root file set drift")
    _require(
        len(entries) == len(case_ids) + 2,
        "source result root contains unsafe or extra entries",
    )
    return _strict_tree_inventory(results_root)


def _load_checklist_pair(case_dir: Path, case_id: str) -> tuple[Mapping[str, Any], Path, Path]:
    yaml_path = _regular_file(case_dir / "checklist.yaml", f"{case_id}: checklist YAML")
    json_path = _regular_file(case_dir / "checklist.json", f"{case_id}: checklist JSON")
    try:
        yaml_value = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ClaimFreezeError(f"{case_id}: checklist YAML is malformed: {exc}") from exc
    json_value = _load_json(json_path, f"{case_id}: checklist JSON")
    _require(isinstance(yaml_value, Mapping), f"{case_id}: checklist YAML is not an object")
    _require(dict(yaml_value) == dict(json_value), f"{case_id}: checklist YAML/JSON mismatch")
    _require(
        json_value.get("schema_version") == "case_checklist_v1"
        and json_value.get("case_unit_id") == case_id
        and json_value.get("task_id") == case_id
        and json_value.get("domain") == "appworld",
        f"{case_id}: checklist identity mismatch",
    )
    return json_value, yaml_path, json_path


def _build_case_lock(
    *,
    position: int,
    inventory_row: Mapping[str, Any],
    audit_case: Mapping[str, Any],
    results_root: Path,
    packet_root: Path,
    final_freeze_root: Path,
    audit_report_path: Path,
) -> tuple[dict[str, Any], Path, Path]:
    case_id = str(inventory_row["case_unit_id"])
    source_case_dir = _directory(results_root / case_id, f"{case_id}: source result")
    checklist, yaml_path, json_path = _load_checklist_pair(source_case_dir, case_id)
    packet_path = _regular_file(packet_root / case_id / "case_packet.md", f"{case_id}: packet")
    manifest_path = _regular_file(
        packet_root / case_id / "raw_case_manifest.json", f"{case_id}: raw manifest"
    )
    checks = _mapping(audit_case["checks"], f"{case_id}: checks")
    pair_check = _mapping(checks["yaml_json_consistency"], f"{case_id}: pair check")
    packet_check = _mapping(checks["packet_identity_and_sources"], f"{case_id}: packet check")
    canonical = _mapping(
        _mapping(checks["canonical_and_successful_attempt_bytes"], f"{case_id}: canonical check")[
            "canonical_sha256"
        ],
        f"{case_id}: canonical hashes",
    )
    for actual, expected, label in (
        (_sha256_file(yaml_path), pair_check.get("checklist_yaml_sha256"), "YAML"),
        (_sha256_file(json_path), pair_check.get("checklist_json_sha256"), "JSON"),
        (_sha256_file(packet_path), inventory_row.get("case_packet_sha256"), "packet"),
        (_sha256_file(manifest_path), inventory_row.get("raw_case_manifest_sha256"), "manifest"),
    ):
        _require(actual == expected, f"{case_id}: {label} hash differs from audited inventory")
    _require(
        packet_check.get("case_packet_sha256") == inventory_row.get("case_packet_sha256")
        and packet_check.get("raw_case_manifest_sha256")
        == inventory_row.get("raw_case_manifest_sha256"),
        f"{case_id}: packet audit binding drift",
    )
    llm_check = _mapping(checks["llm_call_identity"], f"{case_id}: LLM audit")
    semantic_check = _mapping(
        checks["exact_native_and_stronger_semantics"], f"{case_id}: semantic audit"
    )
    support_check = _mapping(checks["support_pointers"], f"{case_id}: support audit")
    frozen_case_dir = final_freeze_root / "claims" / case_id
    lock = {
        "schema_version": CASE_LOCK_SCHEMA,
        "position": position,
        "case_unit_id": case_id,
        "task_id": inventory_row["task_id"],
        "domain": "appworld",
        "dataset_name": inventory_row["dataset_name"],
        "split": inventory_row["split"],
        "source_ref": inventory_row["source_ref"],
        "case_packet": {
            "path": _repo_path(packet_path),
            "sha256": _sha256_file(packet_path),
            "raw_case_manifest_path": _repo_path(manifest_path),
            "raw_case_manifest_sha256": _sha256_file(manifest_path),
        },
        "claim_checklist": {
            "source_yaml_path": _repo_path(yaml_path),
            "source_yaml_sha256": _sha256_file(yaml_path),
            "source_json_path": _repo_path(json_path),
            "source_json_sha256": _sha256_file(json_path),
            "yaml_path": _repo_path(frozen_case_dir / "checklist.yaml"),
            "yaml_sha256": _sha256_file(yaml_path),
            "json_path": _repo_path(frozen_case_dir / "checklist.json"),
            "json_sha256": _sha256_file(json_path),
            "semantic_sha256": _sha256_object(checklist),
            "source_bytes_identity": True,
            "identity_to_source": True,
        },
        "draft_provenance": {
            "source_case_root": _repo_path(source_case_dir),
            "api_response_sha256": canonical["api_response.json"],
            "llm_call_sha256": canonical["llm_call.json"],
            "model": llm_check["model"],
            "reasoning_effort": llm_check["reasoning_effort"],
            "response_id": llm_check["response_id"],
            "request_timestamp": llm_check["request_timestamp"],
            "response_timestamp": llm_check["response_timestamp"],
        },
        "acceptance": {
            "audit_report_path": _repo_path(audit_report_path),
            "audit_case_semantic_sha256": _sha256_object(audit_case),
            "semantic_audit_sha256": semantic_check["semantic_audit_sha256"],
            "stronger_gap_count": semantic_check["stronger_gap_count"],
            "support_pointer_count": support_check["support_pointer_count"],
            "all_required_checks_passed": True,
        },
    }
    return lock, yaml_path, json_path


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_bytes(json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8") + b"\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_bytes(b"".join(_canonical_json_bytes(row, newline=True) for row in rows))


def _runtime_inventory(runtime_root: Path, audit_report: Mapping[str, Any]) -> dict[str, Any]:
    runtime_hashes = _mapping(
        _mapping(audit_report["inputs"], "audit inputs")["runtime_file_sha256"],
        "runtime hashes",
    )
    expected = {
        "prompt": runtime_root / "prompts/draft_case_checklist.prompt.md",
        "supplement": runtime_root / "prompts/appworld_gpt56_draft_strict_v3.supplement.md",
        "template": runtime_root / "templates/case_checklist.template.yaml",
        "schema": runtime_root / "schemas/case_checklist.schema.json",
    }
    files: dict[str, Any] = {}
    for name, path in expected.items():
        path = _regular_file(path, f"runtime {name}")
        digest = _sha256_file(path)
        _require(digest == runtime_hashes.get(name), f"runtime {name} differs from audit")
        files[name] = {"path": _repo_path(path), "sha256": digest}
    return {"files": files, "tree": _strict_tree_inventory(runtime_root)}


def _freeze_definition(
    *,
    freeze_root: Path,
    frozen_at: str,
    inventory_rows: Sequence[Mapping[str, Any]],
    locks: Sequence[Mapping[str, Any]],
    claims_inventory: Mapping[str, Any],
    source_inventory: Mapping[str, Any],
    audit_report: Mapping[str, Any],
    audit_report_path: Path,
    cases_path: Path,
    results_root: Path,
    packet_root: Path,
    runtime_inventory: Mapping[str, Any],
    lock_file_sha256: str,
) -> dict[str, Any]:
    case_ids = [str(row["case_unit_id"]) for row in inventory_rows]
    split_counts = dict(sorted(Counter(str(row["split"]) for row in inventory_rows).items()))
    warning_count = int(_mapping(audit_report["summary"], "audit summary")["warning_count"])
    batch_summary = _load_json(results_root / "_batch_summary.json", "batch summary")
    audit_batch = _mapping(audit_report["batch"], "audit batch")
    claim_root = freeze_root / "claims"
    lock_path = freeze_root / "provenance/case_claim_locks.jsonl"
    return {
        "schema_version": FREEZE_SCHEMA,
        "status": "locked_claim_checklists_pre_benchmark_run",
        "freeze_id": freeze_root.name,
        "frozen_at": frozen_at,
        "scope": {
            "domain": "appworld",
            "case_count": len(case_ids),
            "case_count_by_split": split_counts,
            "case_ids_ordered_semantic_sha256": _sha256_object(case_ids),
            "case_ids_set_semantic_sha256": _sha256_object(sorted(case_ids)),
            "claim_unit": "one immutable case_checklist_v1 per case_unit_id",
        },
        "source_draft_batch": {
            "job_id": results_root.parent.name,
            "results_root": _repo_path(results_root),
            "results_tree": dict(source_inventory),
            "case_inventory_path": _repo_path(cases_path),
            "case_inventory_sha256": _sha256_file(cases_path),
            "batch_summary_path": _repo_path(results_root / "_batch_summary.json"),
            "batch_summary_sha256": _sha256_file(results_root / "_batch_summary.json"),
            "batch_results_path": _repo_path(results_root / "_batch_results.jsonl"),
            "batch_results_sha256": _sha256_file(results_root / "_batch_results.jsonl"),
            "lane_counts": audit_batch["lane_counts"],
            "started_at": batch_summary["started_at"],
            "completed_at": batch_summary["updated_at"],
        },
        "case_packets": {
            "root": _repo_path(packet_root),
            "case_count": len(case_ids),
            "case_packet_bindings_semantic_sha256": _sha256_object(
                [
                    {
                        "case_unit_id": row["case_unit_id"],
                        "case_packet_sha256": row["case_packet_sha256"],
                        "raw_case_manifest_sha256": row["raw_case_manifest_sha256"],
                    }
                    for row in inventory_rows
                ]
            ),
        },
        "generation_runtime": {
            "provider": "codex_cli",
            "model": "gpt-5.6-sol",
            "reasoning_effort": "max",
            "model_verbosity": "medium",
            "auth_mode": "codex_login",
            "sandbox": "read-only",
            "shell_tool_disabled": True,
            "unified_exec_disabled": True,
            "input_transport": "direct_stdin_sealed_bundle_v1",
            "token_budgets": batch_summary["token_budgets"],
            "lane_execution": "regular_then_oversized",
            "declared_regular_lane_max_parallel": 36,
            "declared_oversized_lane_max_parallel": 36,
            "maximum_total_parallelism": 36,
            "parallelism_provenance": "submission wrapper and VPS environment verified before and after the run",
            "frozen_runtime": dict(runtime_inventory),
        },
        "acceptance_audit": {
            "path": _repo_path(audit_report_path),
            "file_sha256": _sha256_file(audit_report_path),
            "report_semantic_sha256": audit_report["report_semantic_sha256"],
            "audit_status": "passed",
            "passed_case_count": len(case_ids),
            "error_count": 0,
            "warning_count": warning_count,
            "allowed_warning_codes": sorted(ALLOWED_AUDIT_WARNING_CODES),
            "audit_validator_path": _repo_path(REPO_ROOT / "scripts/audit_appworld_remote_drafts.py"),
            "audit_validator_sha256": _sha256_file(
                REPO_ROOT / "scripts/audit_appworld_remote_drafts.py"
            ),
            "semantic_validator_path": _repo_path(
                REPO_ROOT / "src/evidence_system/contracts/appworld_checklist_semantics.py"
            ),
            "semantic_validator_sha256": _sha256_file(
                REPO_ROOT / "src/evidence_system/contracts/appworld_checklist_semantics.py"
            ),
        },
        "frozen_claims": {
            "root": _repo_path(claim_root),
            **dict(claims_inventory),
            "canonical_files_per_case": ["checklist.json", "checklist.yaml"],
            "source_bytes_identity": True,
        },
        "case_locks": {
            "path": _repo_path(lock_path),
            "file_sha256": lock_file_sha256,
            "row_count": len(locks),
            "rows_semantic_sha256": _sha256_object(list(locks)),
            "schema_version": CASE_LOCK_SCHEMA,
        },
        "review_and_authorization": {
            "automated_case_by_case_audit_completed": True,
            "automated_case_by_case_audit_passed": True,
            "explicit_user_freeze_authorization": True,
            "manual_human_case_by_case_review_completed": False,
            "content_correction_count": 0,
        },
        "experiment_design": {
            "draft_role": "pre-run claim/checklist only",
            "draft_saw_benchmark_run_outputs": False,
            "draft_saw_score_outputs": False,
            "benchmark_run_completed_by_this_freeze": False,
            "score_called_by_this_freeze": False,
            "score_runtime_frozen_by_this_manifest": False,
            "required_next_steps": [
                "run each frozen AppWorld case without exposing this claim checklist to the benchmark agent",
                "retain official benchmark run artifacts",
                "score retained artifacts against the exact frozen claim checklist bytes",
            ],
            "claim_mutation_after_freeze_prohibited": True,
        },
    }


def _final_lock_definition(
    *,
    freeze_root: Path,
    frozen_at: str,
    manifest_path: Path,
    lock_path: Path,
    locks: Sequence[Mapping[str, Any]],
    claims_inventory: Mapping[str, Any],
    audit_report_path: Path,
) -> dict[str, Any]:
    closure = {
        "claim_freeze": {
            "path": _repo_path(freeze_root / "provenance/claim_freeze.json"),
            "sha256": _sha256_file(manifest_path),
        },
        "case_claim_locks": {
            "path": _repo_path(freeze_root / "provenance/case_claim_locks.jsonl"),
            "sha256": _sha256_file(lock_path),
            "row_count": len(locks),
            "rows_semantic_sha256": _sha256_object(list(locks)),
        },
        "frozen_claims": {
            "root": _repo_path(freeze_root / "claims"),
            **dict(claims_inventory),
        },
        "acceptance_audit": {
            "path": _repo_path(audit_report_path),
            "sha256": _sha256_file(audit_report_path),
        },
    }
    return {
        "schema_version": FINAL_LOCK_SCHEMA,
        "status": "locked_post_generation_claim_freeze",
        "freeze_id": freeze_root.name,
        "created_at": frozen_at,
        "lifecycle": "claim_checklist_frozen_pre_benchmark_pre_score",
        "human_review_completed": False,
        "benchmark_run_completed": False,
        "score_invoked": False,
        "closure": closure,
        "transitive_closure_sha256": _sha256_object(closure),
    }


def _chmod_frozen_tree(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file():
            path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        elif path.is_dir():
            path.chmod(
                stat.S_IRUSR
                | stat.S_IXUSR
                | stat.S_IRGRP
                | stat.S_IXGRP
                | stat.S_IROTH
                | stat.S_IXOTH
            )
    root.chmod(
        stat.S_IRUSR
        | stat.S_IXUSR
        | stat.S_IRGRP
        | stat.S_IXGRP
        | stat.S_IROTH
        | stat.S_IXOTH
    )


def _validate_frozen_permissions(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        _require(not path.is_symlink(), f"frozen tree contains symlink: {path}")
        _require(path.stat().st_mode & 0o222 == 0, f"frozen entry remains writable: {path}")


def _collect_source(
    *,
    job_root: Path,
    packet_root: Path,
    audit_report_path: Path,
    runtime_root: Path,
    expected_count: int,
) -> dict[str, Any]:
    results_root = _directory(job_root / "results", "source results root")
    cases_path = _regular_file(job_root / "cases.jsonl", "case inventory")
    inventory_rows = _parse_inventory(cases_path, expected_count)
    case_ids = [str(row["case_unit_id"]) for row in inventory_rows]
    report, audit_by_id = _validate_audit(
        report_path=audit_report_path,
        results_root=results_root,
        packet_root=packet_root,
        runtime_root=runtime_root,
        expected_count=expected_count,
    )
    _require(set(audit_by_id) == set(case_ids), "audit and inventory case sets differ")
    return {
        "results_root": results_root,
        "cases_path": cases_path,
        "inventory_rows": inventory_rows,
        "audit_report": report,
        "audit_by_id": audit_by_id,
        "source_inventory": _source_root_inventory(results_root, case_ids),
        "runtime_inventory": _runtime_inventory(runtime_root, report),
    }


def _materialize(
    *,
    staging_root: Path,
    final_freeze_root: Path,
    packet_root: Path,
    audit_report_path: Path,
    source: Mapping[str, Any],
    frozen_at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    claims_root = staging_root / "claims"
    claims_root.mkdir()
    provenance_root = staging_root / "provenance"
    provenance_root.mkdir()
    locks: list[dict[str, Any]] = []
    results_root = Path(source["results_root"])
    audit_by_id = _mapping(source["audit_by_id"], "audit cases")
    for position, inventory_row in enumerate(source["inventory_rows"], start=1):
        case_id = str(inventory_row["case_unit_id"])
        lock, source_yaml, source_json = _build_case_lock(
            position=position,
            inventory_row=inventory_row,
            audit_case=_mapping(audit_by_id[case_id], f"{case_id}: audit case"),
            results_root=results_root,
            packet_root=packet_root,
            final_freeze_root=final_freeze_root,
            audit_report_path=audit_report_path,
        )
        destination = claims_root / case_id
        destination.mkdir()
        shutil.copyfile(source_yaml, destination / "checklist.yaml")
        shutil.copyfile(source_json, destination / "checklist.json")
        _require(
            _sha256_file(destination / "checklist.yaml")
            == lock["claim_checklist"]["yaml_sha256"]
            and _sha256_file(destination / "checklist.json")
            == lock["claim_checklist"]["json_sha256"],
            f"{case_id}: materialized claim bytes changed",
        )
        locks.append(lock)
    lock_path = provenance_root / "case_claim_locks.jsonl"
    _write_jsonl(lock_path, locks)
    claims_inventory = _strict_tree_inventory(claims_root)
    _require(
        claims_inventory["file_count"] == len(locks) * 2
        and claims_inventory["directory_count"] == len(locks),
        "materialized claim tree shape mismatch",
    )
    definition = _freeze_definition(
        freeze_root=final_freeze_root,
        frozen_at=frozen_at,
        inventory_rows=source["inventory_rows"],
        locks=locks,
        claims_inventory=claims_inventory,
        source_inventory=source["source_inventory"],
        audit_report=source["audit_report"],
        audit_report_path=audit_report_path,
        cases_path=Path(source["cases_path"]),
        results_root=results_root,
        packet_root=packet_root,
        runtime_inventory=source["runtime_inventory"],
        lock_file_sha256=_sha256_file(lock_path),
    )
    manifest_path = provenance_root / "claim_freeze.json"
    _write_json(manifest_path, definition)
    final_lock = _final_lock_definition(
        freeze_root=final_freeze_root,
        frozen_at=frozen_at,
        manifest_path=manifest_path,
        lock_path=lock_path,
        locks=locks,
        claims_inventory=claims_inventory,
        audit_report_path=audit_report_path,
    )
    _write_json(provenance_root / "claim_final_lock.json", final_lock)
    return definition, locks


def _verify_materialized(
    *,
    storage_root: Path,
    final_freeze_root: Path,
    packet_root: Path,
    audit_report_path: Path,
    source: Mapping[str, Any],
    require_read_only: bool,
) -> dict[str, Any]:
    provenance_root = _directory(storage_root / "provenance", "freeze provenance root")
    manifest_path = _regular_file(
        provenance_root / "claim_freeze.json", "claim freeze manifest"
    )
    manifest = _load_json(manifest_path, "claim freeze manifest")
    _require(manifest.get("schema_version") == FREEZE_SCHEMA, "freeze schema drift")
    _require(
        manifest.get("status") == "locked_claim_checklists_pre_benchmark_run",
        "freeze status drift",
    )
    frozen_at = manifest.get("frozen_at")
    _require(isinstance(frozen_at, str), "freeze timestamp is missing")
    try:
        datetime.fromisoformat(frozen_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ClaimFreezeError("freeze timestamp is malformed") from exc
    claims_root = _directory(storage_root / "claims", "frozen claims root")
    lock_path = _regular_file(
        provenance_root / "case_claim_locks.jsonl", "case claim locks"
    )
    actual_locks = _load_jsonl(lock_path, "case claim locks")
    _require(len(actual_locks) == len(source["inventory_rows"]), "case lock count mismatch")
    expected_locks: list[dict[str, Any]] = []
    audit_by_id = _mapping(source["audit_by_id"], "audit cases")
    for position, inventory_row in enumerate(source["inventory_rows"], start=1):
        case_id = str(inventory_row["case_unit_id"])
        expected_lock, source_yaml, source_json = _build_case_lock(
            position=position,
            inventory_row=inventory_row,
            audit_case=_mapping(audit_by_id[case_id], f"{case_id}: audit case"),
            results_root=Path(source["results_root"]),
            packet_root=packet_root,
            final_freeze_root=final_freeze_root,
            audit_report_path=audit_report_path,
        )
        frozen_dir = _directory(claims_root / case_id, f"{case_id}: frozen claim")
        frozen_entries = {path.name for path in frozen_dir.iterdir()}
        _require(
            frozen_entries == {"checklist.yaml", "checklist.json"},
            f"{case_id}: frozen claim file set drift",
        )
        _require(
            _sha256_file(frozen_dir / "checklist.yaml") == _sha256_file(source_yaml)
            and _sha256_file(frozen_dir / "checklist.json") == _sha256_file(source_json),
            f"{case_id}: frozen claim no longer matches audited source",
        )
        expected_locks.append(expected_lock)
    _require(
        [dict(row) for row in actual_locks] == expected_locks,
        "case claim lock rows differ from source closure",
    )
    claims_inventory = _strict_tree_inventory(claims_root)
    expected_manifest = _freeze_definition(
        freeze_root=final_freeze_root,
        frozen_at=frozen_at,
        inventory_rows=source["inventory_rows"],
        locks=expected_locks,
        claims_inventory=claims_inventory,
        source_inventory=source["source_inventory"],
        audit_report=source["audit_report"],
        audit_report_path=audit_report_path,
        cases_path=Path(source["cases_path"]),
        results_root=Path(source["results_root"]),
        packet_root=packet_root,
        runtime_inventory=source["runtime_inventory"],
        lock_file_sha256=_sha256_file(lock_path),
    )
    _require(dict(manifest) == expected_manifest, "claim freeze manifest closure drift")
    final_lock_path = _regular_file(
        provenance_root / "claim_final_lock.json", "claim final lock"
    )
    final_lock = _load_json(final_lock_path, "claim final lock")
    expected_final_lock = _final_lock_definition(
        freeze_root=final_freeze_root,
        frozen_at=frozen_at,
        manifest_path=manifest_path,
        lock_path=lock_path,
        locks=expected_locks,
        claims_inventory=claims_inventory,
        audit_report_path=audit_report_path,
    )
    _require(dict(final_lock) == expected_final_lock, "claim final-lock closure drift")
    entries = {path.name for path in storage_root.iterdir()}
    _require(
        entries == {"claims", "provenance"},
        "claim freeze root contains extra or missing entries",
    )
    _require(
        {path.name for path in provenance_root.iterdir()}
        == {"case_claim_locks.jsonl", "claim_freeze.json", "claim_final_lock.json"},
        "claim freeze provenance file set drift",
    )
    if require_read_only:
        _validate_frozen_permissions(storage_root)
    return {
        "schema_version": FREEZE_SCHEMA,
        "status": "verified",
        "freeze_root": _repo_path(final_freeze_root),
        "freeze_manifest_sha256": _sha256_file(manifest_path),
        "final_lock_sha256": _sha256_file(final_lock_path),
        "case_count": len(expected_locks),
        "claim_file_count": claims_inventory["file_count"],
        "claims_strict_tree_sha256": claims_inventory["strict_tree_sha256"],
        "case_locks_sha256": _sha256_file(lock_path),
        "source_results_strict_tree_sha256": source["source_inventory"][
            "strict_tree_sha256"
        ],
    }


def _build(args: argparse.Namespace) -> dict[str, Any]:
    job_root = _directory(args.job_root.expanduser().resolve(), "job root")
    packet_root = _directory(args.packet_root.expanduser().resolve(), "packet root")
    runtime_root = _directory(args.runtime_root.expanduser().resolve(), "runtime root")
    audit_report_path = _regular_file(
        args.audit_report.expanduser().resolve(), "audit report"
    )
    freeze_root = args.freeze_root.expanduser().resolve()
    _require(not freeze_root.exists(), f"freeze root already exists: {freeze_root}")
    freeze_root.parent.mkdir(parents=True, exist_ok=True)
    source = _collect_source(
        job_root=job_root,
        packet_root=packet_root,
        audit_report_path=audit_report_path,
        runtime_root=runtime_root,
        expected_count=args.expected_count,
    )
    frozen_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    staging = Path(tempfile.mkdtemp(prefix=f".{freeze_root.name}.tmp-", dir=freeze_root.parent))
    renamed = False
    try:
        _materialize(
            staging_root=staging,
            final_freeze_root=freeze_root,
            packet_root=packet_root,
            audit_report_path=audit_report_path,
            source=source,
            frozen_at=frozen_at,
        )
        _verify_materialized(
            storage_root=staging,
            final_freeze_root=freeze_root,
            packet_root=packet_root,
            audit_report_path=audit_report_path,
            source=source,
            require_read_only=False,
        )
        _chmod_frozen_tree(staging)
        os.replace(staging, freeze_root)
        renamed = True
        return _verify_materialized(
            storage_root=freeze_root,
            final_freeze_root=freeze_root,
            packet_root=packet_root,
            audit_report_path=audit_report_path,
            source=source,
            require_read_only=True,
        )
    finally:
        if not renamed and staging.exists():
            for path in [staging, *staging.rglob("*")]:
                try:
                    path.chmod(0o700 if path.is_dir() else 0o600)
                except OSError:
                    pass
            shutil.rmtree(staging, ignore_errors=True)


def _verify(args: argparse.Namespace) -> dict[str, Any]:
    job_root = _directory(args.job_root.expanduser().resolve(), "job root")
    packet_root = _directory(args.packet_root.expanduser().resolve(), "packet root")
    runtime_root = _directory(args.runtime_root.expanduser().resolve(), "runtime root")
    audit_report_path = _regular_file(
        args.audit_report.expanduser().resolve(), "audit report"
    )
    freeze_root = _directory(args.freeze_root.expanduser().resolve(), "freeze root")
    source = _collect_source(
        job_root=job_root,
        packet_root=packet_root,
        audit_report_path=audit_report_path,
        runtime_root=runtime_root,
        expected_count=args.expected_count,
    )
    return _verify_materialized(
        storage_root=freeze_root,
        final_freeze_root=freeze_root,
        packet_root=packet_root,
        audit_report_path=audit_report_path,
        source=source,
        require_read_only=True,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--job-root", type=Path, required=True)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--audit-report", type=Path, required=True)
    parser.add_argument("--freeze-root", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=485)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = _build(args) if args.build else _verify(args)
    except (ClaimFreezeError, OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
