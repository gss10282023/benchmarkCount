#!/usr/bin/env python3
"""Prepare content-addressed, prelocked wave_003 checklist repairs.

This command performs no model calls.  It refuses incomplete wave/QC evidence,
snapshots the repair toolchain, materializes immutable repair packets, and
freezes the exact Codex CLI/read-only/xhigh/six-worker execution contract.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import SemanticReviewError
from build_repair_selection import verify_selection_reconstructed_from_bound_sources

from repair_pipeline_common import (
    AUTOMATIC_QC_CHECK_KEYS,
    EXPECTED_CASE_COUNT,
    EXPECTED_PARALLELISM,
    REPAIR_LARGE_CASE_THRESHOLD_BYTES,
    REPAIR_ORDER_SEMANTICS,
    REPAIR_CONFIG_SCHEMA,
    REPAIR_PRELOCK_SCHEMA,
    REPO_ROOT,
    RUNTIME_SOURCE_SNAPSHOT_SCHEMA,
    PRELOCK_FILE_SHA256_PLACEHOLDER,
    PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    canonical_runtime_tree,
    closed_child_environment,
    file_binding,
    exact_snapshot_tree_descriptor,
    isolated_bootstrap_command,
    isolated_bootstrap_record,
    load_audit_selection,
    load_json,
    load_source_prelock,
    object_sha256,
    parse_codex_login_status,
    python_runtime_binding,
    repo_relative,
    resolve_repo_path,
    safe_id,
    sha256_file,
    tool_binding,
    tree_record,
    utc_now,
    verify_checklist_pair,
    verify_closed_child_environment,
    verify_file_binding,
    verify_internal_hash,
    verify_runtime_source_snapshot_binding,
    verify_source_wave_complete,
    verify_source_context_freeze,
    write_json_create_once,
)


SOURCE_SCRIPTS = Path(__file__).resolve().parent
SOURCE_PROMPT = WORK_ROOT / "prompts" / "androidworld_checklist_repair_v1.supplement.md"
SNAPSHOT_SCRIPT_NAMES = (
    "semantic_review_common.py",
    "repair_pipeline_common.py",
    "build_scope_aware_wave3_guard.py",
    "build_repair_selection.py",
    "record_repair_prelock_supersession.py",
    "record_readonly_snapshot_invalidation.py",
    "record_readonly_interphase_drift.py",
    "capture_repair_readonly_snapshot.py",
    "readonly_snapshot_helper.py",
    "prepare_checklist_repair.py",
    "run_checklist_repair_batch.py",
    "strict_draft_automatic_qc.py",
)
STRICT_QC_REQUIRED_CALLABLES = (
    "validate_prelock",
    "load_batch_records",
    "validate_batch_summary",
    "per_case_qc",
)


def verify_strict_qc_base_interface(path: Path) -> None:
    """Check the frozen QC adapter interface without importing live code."""

    if not path.is_file():
        raise RepairPipelineError(f"strict QC base is missing: {path}")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise RepairPipelineError(f"strict QC base cannot be parsed: {exc}") from exc
    functions = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = sorted(set(STRICT_QC_REQUIRED_CALLABLES) - functions)
    if missing:
        raise RepairPipelineError(f"strict QC base interface is incomplete: {missing}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-prelock", type=Path, required=True)
    parser.add_argument("--automatic-qc-root", type=Path, required=True)
    parser.add_argument("--audit-selection", type=Path, required=True)
    parser.add_argument("--original-generation-guard", type=Path, required=True)
    parser.add_argument("--changed-path-incident", type=Path, required=True)
    parser.add_argument("--scope-aware-guard", type=Path, required=True)
    parser.add_argument("--supersession-incident", type=Path, required=True)
    parser.add_argument("--repair-readonly-pre-snapshot", type=Path, required=True)
    parser.add_argument("--readonly-interphase-drift-incident", type=Path, required=True)
    parser.add_argument("--repair-id")
    parser.add_argument("--model", default="gpt-5.6-sol", choices=("gpt-5.6-sol",))
    parser.add_argument("--reasoning-effort", default="xhigh", choices=("xhigh",))
    parser.add_argument("--max-parallel", type=int, default=6)
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--large-codex-timeout-seconds", type=int, default=3600)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def check_codex(environment: Mapping[str, str]) -> dict[str, Any]:
    # The runner contract and sanitized child PATH are pinned to this exact
    # Homebrew invocation.  Never let an ambient nvm/npm shim silently select a
    # different (or partially uninstalled) Codex CLI during prelock.
    invocation = Path("/opt/homebrew/bin/codex")
    if not invocation.is_file():
        raise RepairPipelineError(
            "required frozen Codex invocation is missing: /opt/homebrew/bin/codex"
        )
    binary = invocation.resolve()
    exact_environment = verify_closed_child_environment(
        environment, "Codex prelock environment"
    )
    if shutil.which("codex", path=exact_environment["PATH"]) != str(invocation):
        raise RepairPipelineError("closed child PATH does not select /opt/homebrew/bin/codex")
    version = subprocess.run(
        [str(binary), "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=exact_environment,
    )
    login = subprocess.run(
        [str(binary), "login", "status"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=exact_environment,
    )
    if version.returncode != 0 or login.returncode != 0:
        raise RepairPipelineError(
            f"Codex CLI/login prelock failed: version_rc={version.returncode}, "
            f"login_rc={login.returncode}"
        )
    version_output = version.stdout.strip()
    version_stderr = [line.strip() for line in version.stderr.splitlines() if line.strip()]
    from repair_pipeline_common import CODEX_PATH_ALIAS_WARNING

    if version_stderr not in ([], [CODEX_PATH_ALIAS_WARNING]):
        raise RepairPipelineError(
            f"Codex version emitted unrecognized stderr: {version_stderr}"
        )
    if version_output != "codex-cli 0.144.4":
        raise RepairPipelineError(
            f"repair protocol requires codex-cli 0.144.4, observed {version_output!r}"
        )
    login_evidence = parse_codex_login_status(
        login.stdout, login.stderr, "Codex CLI/login prelock"
    )
    return {
        "invocation_path": str(invocation),
        "binary_path": str(binary),
        "binary_sha256": sha256_file(binary),
        "version": version_output,
        "cli_version": "0.144.4",
        "login_status_at_prelock": login_evidence["login_status"],
        "login_success_format": "Logged in using ChatGPT",
        "login_path_alias_warning_present_at_prelock": login_evidence[
            "path_alias_warning_present"
        ],
        "login_path_alias_warning_at_prelock": login_evidence[
            "path_alias_warning"
        ],
        "login_path_alias_warning_sha256_at_prelock": login_evidence[
            "path_alias_warning_sha256"
        ],
        "version_path_alias_warning_present_at_prelock": bool(version_stderr),
        "environment_sha256": object_sha256(exact_environment),
        "auth_mode": "codex_login",
    }


def python_runtime(
    expected_runner_script_directory: Path,
    codex_invocation_path: Path,
    runtime_source_directory: Path,
) -> dict[str, Any]:
    """Capture runtime semantics with the immutable source copy replacing live ``src``."""

    live_source = (REPO_ROOT / "src").resolve(strict=True)
    frozen_source = runtime_source_directory.resolve(strict=True)
    original_sys_path = list(sys.path)
    rewritten_sys_path: list[str] = []
    replacement_count = 0
    for raw_entry in original_sys_path:
        if raw_entry and Path(os.path.abspath(raw_entry)) == live_source:
            rewritten_sys_path.append(str(frozen_source))
            replacement_count += 1
        else:
            rewritten_sys_path.append(raw_entry)
    if replacement_count != 1:
        raise RepairPipelineError(
            "runtime capture requires exactly one editable live repo/src sys.path entry"
        )
    try:
        sys.path[:] = rewritten_sys_path
        runtime = python_runtime_binding(
            expected_runner_script_directory=expected_runner_script_directory.resolve(
                strict=True
            ),
            codex_invocation_path=codex_invocation_path,
            execution_requires_isolated_bootstrap=True,
        )
    finally:
        sys.path[:] = original_sys_path
    expected_paths = list(runtime.get("expected_runner_sys_path") or [])
    captured_paths = list(runtime.get("observed_capture_sys_path") or [])
    if (
        expected_paths.count(str(frozen_source)) != 1
        or captured_paths.count(str(frozen_source)) != 1
        or str(live_source) in expected_paths
        or str(live_source) in captured_paths
    ):
        raise RepairPipelineError("frozen runtime retained the mutable editable repo/src path")
    return runtime


def frozen_runner_command(
    *,
    runtime: Mapping[str, Any],
    prelock_path: Path,
    repair_tree_sha256: str,
    source_tree_sha256: str,
    runtime_source_tree_sha256: str,
    batch_runner: Mapping[str, Any],
    packet_root: Path,
    output_root: Path,
    prompt: Mapping[str, Any],
    codex_timeout_seconds: int,
    large_codex_timeout_seconds: int,
) -> list[str]:
    target_args = [
        "--case-packet-root",
        str(packet_root.resolve()),
        "--output-root",
        str(output_root.resolve()),
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
        str(codex_timeout_seconds),
        "--large-codex-timeout-seconds",
        str(large_codex_timeout_seconds),
        "--codex-sandbox",
        "read-only",
        "--prompt-supplement",
        str(resolve_repo_path(prompt["path"], inside_candidate=True)),
        "--quality-check",
        "none",
        "--sort-by",
        "name",
    ]
    if "--appworld-v56-runtime-gate" in target_args:
        raise RepairPipelineError(
            "AndroidWorld repair batch must not enable the AppWorld v5.6 runtime gate"
        )
    return isolated_bootstrap_command(
        runtime=runtime,
        prelock_path=prelock_path,
        prelock_file_sha256=PRELOCK_FILE_SHA256_PLACEHOLDER,
        prelock_internal_sha256=PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
        repair_tree_sha256=repair_tree_sha256,
        source_tree_sha256=source_tree_sha256,
        runtime_source_tree_sha256=runtime_source_tree_sha256,
        mode="batch",
        target=resolve_repo_path(batch_runner["path"], inside_candidate=True),
        target_args=target_args,
    )


def expected_drafter_attempt_commands(
    *,
    runtime: Mapping[str, Any],
    prelock_path: Path,
    repair_tree_sha256: str,
    source_tree_sha256: str,
    runtime_source_tree_sha256: str,
    drafter: Mapping[str, Any],
    packet_path: Path,
    output_dir: Path,
    prompt: Mapping[str, Any],
    regular_codex_timeout_seconds: int,
    large_codex_timeout_seconds: int,
) -> list[dict[str, Any]]:
    """Reconstruct every exact drafter argv that the frozen batch runner may launch."""

    drafter_path = resolve_repo_path(drafter["path"], inside_candidate=True)
    prompt_path = resolve_repo_path(prompt["path"], inside_candidate=True)
    is_oversized = packet_path.stat().st_size > REPAIR_LARGE_CASE_THRESHOLD_BYTES
    http_timeout = 480 if is_oversized else 180
    codex_timeout = (
        large_codex_timeout_seconds if is_oversized else regular_codex_timeout_seconds
    )
    rows: list[dict[str, Any]] = []
    for attempt_index, token_budget in enumerate((12000, 16000, 20000), 1):
        prefix = f"attempt_{attempt_index:02d}"
        target_args = [
            str(packet_path),
            "-o",
            str(output_dir / f"{prefix}.checklist.yaml"),
            "--raw-json-output",
            str(output_dir / f"{prefix}.checklist.json"),
            "--raw-api-response",
            str(output_dir / f"{prefix}.api_response.json"),
            "--model",
            "gpt-5.6-sol",
            "--provider",
            "codex",
            "--reasoning-effort",
            "xhigh",
            "--max-output-tokens",
            str(token_budget),
            "--http-timeout-seconds",
            str(http_timeout),
            "--codex-timeout-seconds",
            str(codex_timeout),
            "--codex-sandbox",
            "read-only",
            "--prompt-supplement",
            str(prompt_path),
        ]
        command = isolated_bootstrap_command(
            runtime=runtime,
            prelock_path=prelock_path,
            prelock_file_sha256=PRELOCK_FILE_SHA256_PLACEHOLDER,
            prelock_internal_sha256=PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
            repair_tree_sha256=repair_tree_sha256,
            source_tree_sha256=source_tree_sha256,
            runtime_source_tree_sha256=runtime_source_tree_sha256,
            mode="script",
            target=drafter_path,
            target_args=target_args,
        )
        if any(any(character.isspace() for character in argument) for argument in command):
            raise RepairPipelineError(
                "exact process-command audit requires whitespace-free argv elements"
            )
        command_line = " ".join(command)
        rows.append(
            {
                "attempt_index": attempt_index,
                "max_output_tokens": token_budget,
                "lane": "oversized" if is_oversized else "regular",
                "http_timeout_seconds": http_timeout,
                "codex_timeout_seconds": codex_timeout,
                "command": command,
                "command_sha256": object_sha256(command),
                "ps_command_line_sha256": object_sha256(command_line),
            }
        )
    return rows


def verify_automatic_qc(
    root: Path,
    order: list[str],
    source_prelock_path: Path,
    source_prelock: Mapping[str, Any],
    wave: Path,
) -> dict[str, Any]:
    try:
        root.resolve().relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("automatic QC root must be inside candidate116") from exc
    summary_path = root / "summary.json"
    summary = load_json(summary_path, "wave3 automatic QC summary")
    if summary.get("schema_version") != "androidworld_checklist_automatic_qc_summary/v2":
        raise RepairPipelineError("automatic QC summary schema is not v2")
    verify_internal_hash(summary, ("summary_sha256",), "wave3 automatic QC summary")
    exact_summary = {
        "case_count": EXPECTED_CASE_COUNT,
        "expected_case_count": EXPECTED_CASE_COUNT,
        "reported_case_count": EXPECTED_CASE_COUNT,
        "passed_count": 72,
        "automatic_passed_count": 72,
        "failed_count": 44,
        "automatic_failed_count": 44,
        "case_report_schema_version": "androidworld_checklist_automatic_qc/v2",
        "status": "fail",
        "automatic_status": "automatic_failed_or_incomplete",
        "global_issues": [],
        "prelock_path": repo_relative(source_prelock_path),
        "prelock_file_sha256": sha256_file(source_prelock_path),
        "prelock_sha256": source_prelock["prelock_sha256"],
        "wave_root": repo_relative(wave),
        "report_root": repo_relative(root),
    }
    for field, wanted in exact_summary.items():
        if summary.get(field) != wanted:
            raise RepairPipelineError(
                f"automatic QC summary {field}={summary.get(field)!r}, expected {wanted!r}"
            )
    packet_by_case = {
        row["case_unit_id"]: row for row in source_prelock.get("packet_inputs") or []
    }
    if set(packet_by_case) != set(order):
        raise RepairPipelineError("automatic QC source packet set is not the exact 116 cases")
    summary_index = summary.get("case_report_index")
    if not isinstance(summary_index, list) or len(summary_index) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("automatic QC summary report index is not exactly 116 rows")
    report_index: list[dict[str, Any]] = []
    passed_cases: list[str] = []
    failed_cases: list[str] = []
    expected_summary_issues: list[dict[str, Any]] = []
    for rank, case_id in enumerate(order):
        path = root / case_id / "qc.json"
        report = load_json(path, f"{case_id} automatic QC")
        if report.get("schema_version") != "androidworld_checklist_automatic_qc/v2":
            raise RepairPipelineError(f"{case_id} automatic QC schema is not v2")
        if report.get("case_unit_id") != case_id or report.get("selection_rank") != rank:
            raise RepairPipelineError(f"{case_id} automatic QC identity/rank differs")
        if report.get("task_id") != case_id:
            raise RepairPipelineError(f"{case_id} automatic QC task identity differs")
        checklist_path = wave / case_id / "checklist.yaml"
        if (
            report.get("checklist_path") != repo_relative(checklist_path)
            or report.get("checklist_sha256") != sha256_file(checklist_path)
        ):
            raise RepairPipelineError(f"{case_id} automatic QC checklist binding differs")
        packet = packet_by_case[case_id]
        packet_path = verify_file_binding(packet, f"{case_id} prelocked full packet", inside_candidate=True)
        if (
            packet.get("selection_rank") != rank
            or packet.get("task_id") != case_id
            or report.get("packet_path") != repo_relative(packet_path)
            or report.get("packet_sha256") != packet.get("sha256")
        ):
            raise RepairPipelineError(f"{case_id} automatic QC packet binding differs")
        checks = report.get("checks")
        issues = report.get("issues")
        if (
            not isinstance(checks, Mapping)
            or set(checks) != AUTOMATIC_QC_CHECK_KEYS
            or any(not isinstance(value, bool) for value in checks.values())
        ):
            raise RepairPipelineError(f"{case_id} automatic QC checks are not a boolean map")
        if not isinstance(issues, list) or any(not isinstance(issue, Mapping) for issue in issues):
            raise RepairPipelineError(f"{case_id} automatic QC issues are not an object list")
        computed_pass = not issues and all(checks.values())
        expected_status = "passed" if computed_pass else "failed"
        if report.get("status") != expected_status:
            raise RepairPipelineError(f"{case_id} automatic QC status is inconsistent with checks/issues")
        if not computed_pass and (
            not issues
            or not any(issue.get("severity") == "error" for issue in issues)
        ):
            raise RepairPipelineError(
                f"{case_id} failed automatic QC must contain at least one error issue"
            )
        expected_index_row = {
            "case_unit_id": case_id,
            "path": repo_relative(path),
            "selection_rank": rank,
            "status": expected_status,
        }
        if summary_index[rank] != expected_index_row:
            raise RepairPipelineError(f"{case_id} automatic QC summary index row differs")
        report_index.append(
            {
                "selection_rank": rank,
                "case_unit_id": case_id,
                "task_id": case_id,
                "status": expected_status,
                "report": file_binding(path),
                "checklist": file_binding(checklist_path),
                "packet": file_binding(packet_path),
            }
        )
        if computed_pass:
            passed_cases.append(case_id)
        else:
            failed_cases.append(case_id)
            expected_summary_issues.append(
                {
                    "case_issue_count": len(issues),
                    "case_unit_id": case_id,
                    "check": "case_reports",
                    "code": "case_automatic_qc_failed",
                    "message": "per-case automatic QC did not pass",
                    "severity": "error",
                }
            )
    if passed_cases != summary.get("automatic_passed_cases"):
        raise RepairPipelineError("automatic QC passed-case list differs from 116 reports")
    if failed_cases != summary.get("automatic_failed_cases"):
        raise RepairPipelineError("automatic QC failed-case list differs from 116 reports")
    if len(passed_cases) != 72 or len(failed_cases) != 44:
        raise RepairPipelineError("automatic QC report outcomes are not exactly 72 pass / 44 fail")
    if summary.get("issues") != expected_summary_issues:
        raise RepairPipelineError("automatic QC summary issue index differs from failed reports")
    return {
        "summary": file_binding(summary_path) | {"summary_sha256": summary["summary_sha256"]},
        "report_index": report_index,
        "report_index_sha256": object_sha256(report_index),
        "passed_count": len(passed_cases),
        "failed_count": len(failed_cases),
    }


def verify_drift_evidence(
    original_path: Path,
    incident_path: Path,
    scope_path: Path,
) -> dict[str, Any]:
    original = load_json(original_path, "original generation guard")
    incident = load_json(incident_path, "changed-path incident")
    scope = load_json(scope_path, "scope-aware guard")
    verify_internal_hash(original, ("guard_sha256",), "original generation guard")
    verify_internal_hash(incident, ("incident_sha256",), "changed-path incident")
    verify_internal_hash(scope, ("scope_guard_sha256",), "scope-aware guard")
    if original.get("generation_id") != "wave_003":
        raise RepairPipelineError("original generation guard is not wave_003")
    if incident.get("generation_id") != "wave_003" or scope.get("generation_id") != "wave_003":
        raise RepairPipelineError("drift evidence is not wave_003")
    if scope.get("status") != "pass":
        raise RepairPipelineError("scope-aware guard did not pass")
    if scope.get("packet_inputs_unchanged") is not True:
        raise RepairPipelineError("scope-aware guard did not prove packet inputs unchanged")
    if scope.get("v3_snapshot_files_unchanged") is not True:
        raise RepairPipelineError("scope-aware guard did not prove v3 snapshot bytes unchanged")
    if scope.get("v3_bound_live_origins_unchanged") is not True:
        raise RepairPipelineError("scope-aware guard did not prove v3 live origins unchanged")
    protected = scope.get("protected_root_equality") or {}
    if not protected or not all(value is True for value in protected.values()):
        raise RepairPipelineError("scope-aware guard did not prove protected root equality")
    if scope.get("official100_equal") is not True:
        raise RepairPipelineError("scope-aware guard did not prove official100 unchanged")
    bound_original = scope.get("original_guard") or {}
    if bound_original.get("sha256") != sha256_file(original_path):
        raise RepairPipelineError("scope-aware guard does not bind the original guard file")
    if scope.get("live_drift_incident_sha256") != incident.get("incident_sha256"):
        raise RepairPipelineError("scope-aware guard and changed-path incident disagree")
    bound_incident = scope.get("live_drift_incident")
    if isinstance(bound_incident, Mapping):
        verify_file_binding(bound_incident, "scope guard incident", inside_candidate=True)
    return {
        "original_guard": file_binding(original_path)
        | {"guard_sha256": original["guard_sha256"], "status": original.get("status")},
        "changed_path_incident": file_binding(incident_path)
        | {"incident_sha256": incident["incident_sha256"]},
        "scope_aware_guard": file_binding(scope_path)
        | {"scope_guard_sha256": scope["scope_guard_sha256"]},
        "policy": "original guard is preserved even when failed; scope-aware pass is additive",
    }


def verify_supersession_incident(path: Path) -> dict[str, Any]:
    incident_path = path.resolve()
    try:
        incident_path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("supersession incident must be inside candidate116") from exc
    incident = load_json(incident_path, "repair supersession incident")
    if incident.get("schema_version") != "androidworld_checklist_repair_supersession_incident/v1":
        raise RepairPipelineError("repair supersession incident schema is invalid")
    verify_internal_hash(incident, ("incident_sha256",), "repair supersession incident")
    if incident_path.stem != incident["incident_sha256"]:
        raise RepairPipelineError("supersession incident filename is not its content address")
    expected = {
        "status": "aborted_before_first_repair_model_call",
        "reason_code": "repair_issue_context_loss",
        "promotion_forbidden": True,
        "repair_output_eligible": False,
        "model_calls_started": False,
        "model_output_root_absent": True,
    }
    for field, wanted in expected.items():
        if incident.get(field) != wanted:
            raise RepairPipelineError(f"supersession incident {field} is not {wanted!r}")
    required = incident.get("required_replacement") or {}
    if (
        required.get("selection_schema") != "androidworld_checklist_repair_selection/v2"
        or required.get("issue_schema") != "androidworld_checklist_repair_issue/v2"
        or required.get("new_content_addressed_packets") is not True
        or required.get("new_generation_prelock") is not True
    ):
        raise RepairPipelineError("supersession incident replacement requirements are incomplete")
    selection_path = verify_file_binding(
        incident.get("superseded_selection"), "superseded selection", inside_candidate=True
    )
    old_selection = load_json(selection_path, "superseded selection")
    if old_selection.get("schema_version") != "androidworld_checklist_repair_selection/v1":
        raise RepairPipelineError("superseded selection is not the affected v1 schema")
    verify_internal_hash(old_selection, ("selection_sha256",), "superseded selection")
    if incident["superseded_selection"].get("selection_sha256") != old_selection["selection_sha256"]:
        raise RepairPipelineError("supersession incident selection internal hash differs")
    old_prelock_path = verify_file_binding(
        incident.get("superseded_prelock"), "superseded repair prelock", inside_candidate=True
    )
    old_prelock = load_json(old_prelock_path, "superseded repair prelock")
    if old_prelock.get("schema_version") != REPAIR_PRELOCK_SCHEMA:
        raise RepairPipelineError("superseded repair prelock schema is invalid")
    verify_internal_hash(old_prelock, ("prelock_sha256",), "superseded repair prelock")
    if incident["superseded_prelock"].get("prelock_sha256") != old_prelock["prelock_sha256"]:
        raise RepairPipelineError("supersession incident prelock internal hash differs")
    if (old_prelock.get("audit_selection") or {}).get("sha256") != sha256_file(selection_path):
        raise RepairPipelineError("superseded prelock no longer binds the v1 selection")
    config_path = verify_file_binding(
        incident.get("superseded_config"), "superseded repair config", inside_candidate=True
    )
    old_config = load_json(config_path, "superseded repair config")
    verify_internal_hash(old_config, ("config_sha256",), "superseded repair config")
    if incident["superseded_config"].get("config_sha256") != old_config["config_sha256"]:
        raise RepairPipelineError("supersession incident config internal hash differs")
    output_root = resolve_repo_path(old_config.get("output_root"), inside_candidate=True)
    if output_root.exists():
        raise RepairPipelineError("superseded repair output root is no longer absent")
    old_snapshot_path = verify_file_binding(
        incident.get("superseded_toolchain_snapshot"),
        "superseded repair snapshot",
        inside_candidate=True,
    )
    old_snapshot = load_json(old_snapshot_path, "superseded repair snapshot")
    verify_internal_hash(old_snapshot, ("snapshot_sha256",), "superseded repair snapshot")
    if (
        incident["superseded_toolchain_snapshot"].get("snapshot_sha256")
        != old_snapshot["snapshot_sha256"]
    ):
        raise RepairPipelineError("supersession incident snapshot internal hash differs")
    packet_root = resolve_repo_path(old_config.get("packet_set_root"), inside_candidate=True)
    if tree_record(packet_root) != incident.get("superseded_packet_set"):
        raise RepairPipelineError("superseded repair packet set changed after incident")
    return file_binding(incident_path) | {
        "incident_sha256": incident["incident_sha256"],
        "status": incident["status"],
        "promotion_forbidden": True,
        "superseded_selection_sha256": old_selection["selection_sha256"],
        "superseded_prelock_sha256": old_prelock["prelock_sha256"],
    }


def verify_repair_readonly_pre_snapshot(path: Path, repair_id: str) -> dict[str, Any]:
    snapshot_path = path.resolve()
    record = load_json(snapshot_path, "repair read-only pre-snapshot")
    if record.get("schema_version") != "androidworld_checklist_repair_readonly_snapshot/v2":
        raise RepairPipelineError("repair read-only pre-snapshot schema is invalid")
    if not snapshot_path.name.endswith(".pre_v2.json"):
        raise RepairPipelineError("repair read-only v2 pre-snapshot must use a create-once .pre_v2 path")
    verify_internal_hash(record, ("snapshot_sha256",), "repair read-only pre-snapshot")
    expected_phase = f"before_checklist_repair_generation_{repair_id}"
    if record.get("phase") != expected_phase:
        raise RepairPipelineError(
            f"repair read-only pre-snapshot phase must be {expected_phase}"
        )
    helper = record.get("snapshot_helper") or {}
    helper_path = verify_file_binding(helper, "repair read-only snapshot helper", inside_candidate=True)
    expected_helper = (SOURCE_SCRIPTS / "readonly_snapshot_helper.py").resolve()
    if helper_path != expected_helper or helper != file_binding(expected_helper):
        raise RepairPipelineError("repair read-only snapshot helper differs from dedicated helper")
    tree = ast.parse(helper_path.read_text(encoding="utf-8"), filename=str(helper_path))
    imports = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module != "__future__"
    }
    nonstdlib = sorted(name for name in imports if name and name not in sys.stdlib_module_names)
    if nonstdlib:
        raise RepairPipelineError(f"dedicated read-only helper imports non-stdlib modules: {nonstdlib}")
    invalidation_binding = record.get("supersedes_invalidated_pre_snapshot") or {}
    invalidation_path = verify_file_binding(
        invalidation_binding,
        "invalidated v1 read-only snapshot incident",
        inside_candidate=True,
    )
    invalidation = load_json(invalidation_path, "invalidated v1 read-only snapshot incident")
    if (
        invalidation.get("schema_version")
        != "androidworld_checklist_repair_readonly_snapshot_invalidation/v1"
        or invalidation.get("status") != "invalidated_before_repair_prelock"
        or invalidation.get("promotion_forbidden") is not True
        or invalidation.get("model_calls_started") is not False
    ):
        raise RepairPipelineError("v1 read-only snapshot invalidation incident is invalid")
    verify_internal_hash(invalidation, ("incident_sha256",), "v1 snapshot invalidation")
    if (
        invalidation.get("incident_sha256") != invalidation_binding.get("incident_sha256")
        or (invalidation.get("replacement_helper") or {}).get("sha256") != helper.get("sha256")
        or (invalidation.get("invalidated_pre_snapshot") or {}).get("snapshot_sha256")
        != "4907901ab5e436f9177543e445d69c2b5dffee7b2c680891091278f7a00a48c1"
    ):
        raise RepairPipelineError("v1 snapshot invalidation does not bind the expected replacement")
    readonly = record.get("readonly_snapshot")
    if not isinstance(readonly, Mapping):
        raise RepairPipelineError("repair read-only pre-snapshot payload is not an object")
    expected_roots = {
        "neurips_ed_track_minimal",
        "results",
        "paper_result_packages",
        "paper_result_packages/androidworld_both_agents_scored_cases_official_full100",
    }
    if (
        readonly.get("schema_version")
        != "androidworld_checklist_repair_dedicated_readonly_snapshot/v1"
        or readonly.get("phase") != expected_phase
        or readonly.get("write_scope") != repo_relative(WORK_ROOT)
        or set((readonly.get("roots") or {})) != expected_roots
    ):
        raise RepairPipelineError("repair read-only pre-snapshot scope/roots are invalid")
    official = readonly.get("official100") or {}
    if (
        official.get("path")
        != "experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json"
        or official.get("file_count") != 1
        or not isinstance(official.get("sha256"), str)
    ):
        raise RepairPipelineError("repair read-only pre-snapshot official100 binding is invalid")
    core = {
        "write_scope": readonly["write_scope"],
        "policy": readonly["policy"],
        "roots": readonly["roots"],
        "official100": readonly["official100"],
    }
    if record.get("readonly_core_sha256") != object_sha256(core):
        raise RepairPipelineError("repair read-only pre-snapshot core hash differs")
    return {
        "pre_snapshot": file_binding(snapshot_path)
        | {
            "snapshot_sha256": record["snapshot_sha256"],
            "readonly_core_sha256": record["readonly_core_sha256"],
            "phase": expected_phase,
        },
        "pre_capture_helper": dict(helper),
        "invalidated_pre_snapshot_incident": dict(invalidation_binding),
        "protected_roots": sorted(expected_roots - {"neurips_ed_track_minimal"}),
        "nonbinding_live_tool_root": "neurips_ed_track_minimal",
        "official100_path": official["path"],
    }


def verify_readonly_interphase_drift(
    path: Path, readonly_window: Mapping[str, Any]
) -> dict[str, Any]:
    incident_path = path.resolve()
    incident = load_json(incident_path, "repair read-only interphase drift incident")
    verify_internal_hash(incident, ("incident_sha256",), "read-only interphase drift")
    if (
        incident.get("schema_version")
        != "androidworld_checklist_repair_readonly_interphase_drift/v1"
        or incident.get("status")
        != "recorded_interphase_drift_before_repair_prelock"
        or incident.get("repair_model_calls_started") is not False
        or incident.get("repair_prelock_created") is not False
        or incident.get("deletion_performed") is not False
        or incident.get("attribution")
        != "not_attributed; namespace location is evidence, not actor or cause"
        or incident.get("paper_result_packages_equal") is not True
        or incident.get("submitted_official100_package_equal") is not True
        or incident.get("official100_selector_equal") is not True
        or (incident.get("root_content_equality") or {}).get("results") is not False
    ):
        raise RepairPipelineError("read-only interphase drift incident contract is invalid")
    new_snapshot = incident.get("new_v2_snapshot") or {}
    if (
        new_snapshot.get("sha256") != readonly_window["pre_snapshot"].get("sha256")
        or new_snapshot.get("snapshot_sha256")
        != readonly_window["pre_snapshot"].get("snapshot_sha256")
    ):
        raise RepairPipelineError("interphase drift incident does not bind the v2 pre-snapshot")
    invalidation_path = verify_file_binding(
        readonly_window["invalidated_pre_snapshot_incident"],
        "v1 snapshot invalidation for interphase drift",
        inside_candidate=True,
    )
    invalidation = load_json(invalidation_path, "v1 snapshot invalidation for interphase drift")
    if incident.get("old_v1_snapshot") != invalidation.get("invalidated_pre_snapshot"):
        raise RepairPipelineError("interphase drift incident does not bind the invalidated v1 snapshot")
    return file_binding(incident_path) | {"incident_sha256": incident["incident_sha256"]}


def packet_text(
    *,
    case_id: str,
    rank: int,
    original_yaml: str,
    issues: list[dict[str, Any]],
    full_packet: str,
) -> str:
    issue_json = json.dumps(issues, ensure_ascii=False, sort_keys=True, indent=2)
    return (
        "# AndroidWorld Checklist Repair Packet\n\n"
        "## Case Metadata\n\n"
        "- domain: `androidworld`\n"
        f"- case_unit_id: `{case_id}`\n"
        f"- task_id: `{case_id}`\n"
        f"- selection_rank: `{rank}`\n\n"
        "## Repair Control (untrusted leads; never semantic evidence)\n\n"
        "The old checklist and issue statements below identify what must be checked. "
        "They are not source facts, runtime evidence, or valid support targets. The "
        "verbatim full packet later in this file is the sole semantic authority.\n\n"
        "### Bound issues\n\n```json\n"
        f"{issue_json}\n```\n\n"
        "### Original checklist to repair\n\n```yaml\n"
        f"{original_yaml.rstrip()}\n```\n\n"
        "## Authoritative Full Case Packet (verbatim; sole semantic authority)\n\n"
        f"{full_packet.rstrip()}\n"
    )


def materialize_packets(
    *,
    repair_id: str,
    prelock: Mapping[str, Any],
    audit_rows: list[dict[str, Any]],
    wave: Path,
) -> tuple[Path, list[dict[str, Any]]]:
    packet_set_root = WORK_ROOT / "repair_generation" / "packet_sets" / repair_id
    try:
        packet_set_root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RepairPipelineError(f"repair packet set already exists: {packet_set_root}") from exc
    content_root = WORK_ROOT / "repair_generation" / "content_addressed_packets"
    content_root.mkdir(parents=True, exist_ok=True)
    row_by_case = {row["case_unit_id"]: row for row in audit_rows}
    packet_by_case = {row["case_unit_id"]: row for row in prelock.get("packet_inputs") or []}
    repair_inputs: list[dict[str, Any]] = []
    try:
        for rank, case_id in enumerate(prelock["case_order"]):
            audit = row_by_case[case_id]
            if audit["disposition"] != "repair":
                continue
            packet_record = packet_by_case[case_id]
            full_path = verify_file_binding(packet_record, f"{case_id} full packet", inside_candidate=True)
            original_dir = wave / case_id
            verify_checklist_pair(original_dir, case_id)
            original_yaml_path = original_dir / "checklist.yaml"
            original_json_path = original_dir / "checklist.json"
            text = packet_text(
                case_id=case_id,
                rank=rank,
                original_yaml=original_yaml_path.read_text(encoding="utf-8"),
                issues=audit["issues"],
                full_packet=full_path.read_text(encoding="utf-8"),
            )
            payload = text.encode("utf-8")
            packet_sha = __import__("hashlib").sha256(payload).hexdigest()
            addressed = content_root / packet_sha / "case_packet.md"
            if addressed.exists():
                if addressed.read_bytes() != payload:
                    raise RepairPipelineError(f"content-address collision for {case_id}")
            else:
                addressed.parent.mkdir(parents=True, exist_ok=True)
                temporary = addressed.parent / f".{addressed.name}.{os.getpid()}.tmp"
                try:
                    with temporary.open("xb") as handle:
                        handle.write(payload)
                        handle.flush()
                        os.fsync(handle.fileno())
                    try:
                        os.link(temporary, addressed)
                    except FileExistsError:
                        if addressed.read_bytes() != payload:
                            raise RepairPipelineError(f"content-address collision for {case_id}")
                finally:
                    temporary.unlink(missing_ok=True)
            case_dir = packet_set_root / case_id
            case_dir.mkdir()
            packet_path = case_dir / "case_packet.md"
            with packet_path.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            bindings = {
                "authoritative_full_packet": file_binding(full_path),
                "original_checklist_yaml": file_binding(original_yaml_path),
                "original_checklist_json": file_binding(original_json_path),
                "automatic_qc": audit["automatic_qc"],
                "audit_sources": audit["audit_sources"],
                "content_addressed_packet": file_binding(addressed),
                "batch_packet": file_binding(packet_path),
            }
            descriptor = {
                "schema_version": "androidworld_checklist_repair_packet/v1",
                "repair_id": repair_id,
                "case_unit_id": case_id,
                "task_id": case_id,
                "selection_rank": rank,
                "audit_case_sha256": audit["audit_case_sha256"],
                "issues": audit["issues"],
                "packet_sha256": packet_sha,
                "semantic_authority": "authoritative_full_packet_only",
                "bindings": bindings,
            }
            descriptor = add_self_hash(descriptor, "descriptor_sha256")
            descriptor_path = case_dir / "repair_packet_descriptor.json"
            write_json_create_once(descriptor_path, descriptor)
            repair_inputs.append(
                {
                    "selection_rank": rank,
                    "case_unit_id": case_id,
                    "task_id": case_id,
                    "audit_case_sha256": audit["audit_case_sha256"],
                    "issues_sha256": object_sha256(audit["issues"]),
                    "repair_packet_sha256": packet_sha,
                    "descriptor": file_binding(descriptor_path)
                    | {"descriptor_sha256": descriptor["descriptor_sha256"]},
                    "bindings": bindings,
                }
            )
    except BaseException:
        shutil.rmtree(packet_set_root, ignore_errors=True)
        raise
    return packet_set_root, repair_inputs


def repair_execution_plan(repair_inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reproduce the frozen batch runner's deterministic submission plan.

    The frozen runner first sorts packet directories by name, then submits the
    complete regular lane before the complete oversized lane.  Worker start and
    completion timing inside either six-worker lane remains scheduler-dependent;
    this plan never mislabels JSONL ``as_completed`` order as invocation order.
    """

    by_name = sorted(repair_inputs, key=lambda row: str(row["case_unit_id"]))
    regular: list[dict[str, Any]] = []
    oversized: list[dict[str, Any]] = []
    for row in by_name:
        packet_path = resolve_repo_path(
            row["bindings"]["batch_packet"]["path"], inside_candidate=True
        )
        target = (
            oversized
            if packet_path.stat().st_size > REPAIR_LARGE_CASE_THRESHOLD_BYTES
            else regular
        )
        target.append(row)
    ordered = regular + oversized
    if len({row["case_unit_id"] for row in ordered}) != len(repair_inputs):
        raise RepairPipelineError("repair execution plan contains duplicate case ids")
    return [
        {
            "execution_rank": rank,
            "case_unit_id": row["case_unit_id"],
            "selection_rank": row["selection_rank"],
            "lane": (
                "oversized"
                if resolve_repo_path(
                    row["bindings"]["batch_packet"]["path"], inside_candidate=True
                ).stat().st_size
                > REPAIR_LARGE_CASE_THRESHOLD_BYTES
                else "regular"
            ),
        }
        for rank, row in enumerate(ordered)
    ]


def copy_runtime_source_snapshot(
    source_root: Path, snapshot_parent: Path, repair_id: str
) -> tuple[Path, dict[str, Any]]:
    """Stage and atomically promote one exact content-addressed source image."""

    source_root = source_root.resolve(strict=True)
    before = canonical_runtime_tree(source_root)
    if before["symlink_count"]:
        symlinks = [
            row["path"] for row in before["entries"] if row["kind"] == "symlink"
        ]
        raise RepairPipelineError(
            f"live repo/src contains forbidden symlinks at capture: {symlinks}"
        )
    content_id = object_sha256(before["entries"])
    snapshot_parent.mkdir(parents=True, exist_ok=False)
    staging_root = snapshot_parent / f".{content_id}.staging"
    content_root = snapshot_parent / content_id
    snapshot_root = staging_root / "src"
    if content_root.exists():
        raise RepairPipelineError(
            f"runtime-source content address already exists: {content_root}"
        )
    staging_root.mkdir()
    snapshot_root.mkdir()
    for row in before["entries"]:
        relative = Path(str(row["path"]))
        source = source_root / relative
        destination = snapshot_root / relative
        if row["kind"] == "directory":
            destination.mkdir()
        elif row["kind"] == "regular_file":
            shutil.copy2(source, destination, follow_symlinks=False)
        else:
            raise RepairPipelineError(
                f"unsupported live repo/src entry during copy: {row}"
            )
    after = canonical_runtime_tree(source_root)
    copied = canonical_runtime_tree(snapshot_root)
    if after != before:
        raise RepairPipelineError(
            "live repo/src changed during content-addressed runtime-source capture"
        )
    comparable_fields = (
        "entry_count",
        "regular_file_count",
        "directory_count",
        "symlink_count",
        "total_regular_file_bytes",
        "tree_sha256",
        "entries",
    )
    if any(copied[field] != before[field] for field in comparable_fields):
        raise RepairPipelineError(
            "copied runtime-source snapshot differs from the stable live repo/src index"
        )
    final_content_root = content_root.resolve(strict=False)
    final_snapshot_root = final_content_root / "src"
    copied_at_final_path = {**copied, "root": str(final_snapshot_root)}
    bytecode_files = [
        {
            "path": row["path"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
        }
        for row in copied["entries"]
        if row["kind"] == "regular_file"
        and Path(str(row["path"])).suffix.casefold() in {".pyc", ".pyo"}
    ]
    record = {
        "schema_version": RUNTIME_SOURCE_SNAPSHOT_SCHEMA,
        "source_root_absolute_path": str(source_root),
        "content_root_absolute_path": str(final_content_root),
        "snapshot_root_absolute_path": str(final_snapshot_root),
        "source_entry_count": copied["entry_count"],
        "source_regular_file_count": copied["regular_file_count"],
        "source_directory_count": copied["directory_count"],
        "source_total_regular_file_bytes": copied["total_regular_file_bytes"],
        "source_pre_tree_sha256": before["tree_sha256"],
        "source_post_tree_sha256": after["tree_sha256"],
        "snapshot_tree_sha256": copied["tree_sha256"],
        "source_content_id_sha256": content_id,
        "source_pre_tree": before,
        "source_post_tree": after,
        "snapshot_tree": copied_at_final_path,
        "bytecode_file_count": len(bytecode_files),
        "bytecode_files_sha256": object_sha256(bytecode_files),
        "bytecode_policy": (
            "copy and bind every pre-existing .pyc/.pyo byte; create no new bytecode; "
            "reject every post-freeze namespace or byte change"
        ),
        "copy_policy": (
            "pre-index live repo/src, copy every directory and regular file with copy2, "
            "then require source post-index and snapshot index to equal the pre-index"
        ),
        "source_endpoint_equality_required": True,
        "source_endpoint_equality_observed": True,
        "snapshot_all_bytes_equal_source": True,
        "snapshot_symlink_count": 0,
        "live_source_excluded_from_runtime_sys_path": True,
        "sys_path_substitution": {
            "captured_live_editable_path": str(source_root),
            "frozen_snapshot_path": str(final_snapshot_root),
            "required_replacement_count": 1,
            "live_path_allowed_after_substitution": False,
        },
        "live_editable_pth_policy": (
            "never execute site or editable-install .pth files in generation; bind their "
            "capture-time effect explicitly by replacing only live repo/src with runtime_src"
        ),
        "outer_and_nested_preimport_verification_required": True,
        "staged_copy_promoted_atomically": True,
        "staging_policy": (
            "copy and compare under a hidden sibling; write a create-once manifest; atomically "
            "rename to the canonical-entry SHA-256 content address"
        ),
        "post_freeze_live_source_drift_nonbinding": True,
        "dont_write_bytecode_required": True,
        "threat_model_limit": (
            "pre/post endpoint equality and copied-byte equality reject ordinary concurrent "
            "drift but cannot prove absence of malicious modify-and-restore activity inside "
            "the capture interval"
        ),
    }
    record = add_self_hash(record, "runtime_source_snapshot_sha256")
    source_files = [
        {
            "path": f"src/{row['path']}",
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
        }
        for row in copied["entries"]
        if row["kind"] == "regular_file"
    ]
    manifest = add_self_hash(
        {
            "schema_version": "androidworld_repair_runtime_source_snapshot_manifest/v1",
            "repair_id": repair_id,
            "source_content_id_sha256": content_id,
            "runtime_source_snapshot": record,
            "files": source_files,
            "file_count": len(source_files),
            "files_sha256": object_sha256(source_files),
        },
        "snapshot_manifest_sha256",
    )
    staged_manifest = staging_root / "snapshot_manifest.json"
    write_json_create_once(staged_manifest, manifest)
    staging_root.rename(content_root)
    final_manifest = content_root / "snapshot_manifest.json"
    verify_runtime_source_snapshot_binding(record, "new runtime source snapshot")
    if any(path.name.startswith(".") for path in snapshot_parent.iterdir()):
        raise RepairPipelineError("runtime-source staging namespace remained after promotion")
    return final_manifest, record


def copy_toolchain(
    repair_id: str,
    *,
    root: Path | None = None,
    make_readonly: bool = True,
) -> tuple[Path, dict[str, Any]]:
    root = root or (
        WORK_ROOT / "repair_generation" / "toolchain_snapshot" / repair_id
    )
    try:
        root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RepairPipelineError(f"repair snapshot already exists: {root}") from exc
    scripts = root / "scripts"
    prompts = root / "prompts"
    runtime_source_parent = root / "runtime_source"
    scripts.mkdir()
    prompts.mkdir()
    for name in SNAPSHOT_SCRIPT_NAMES:
        source = SOURCE_SCRIPTS / name
        if not source.is_file():
            raise RepairPipelineError(f"repair tool source is missing: {source}")
        shutil.copy2(source, scripts / name)
    shutil.copy2(SOURCE_PROMPT, prompts / SOURCE_PROMPT.name)
    runtime_source_manifest, runtime_source_snapshot = copy_runtime_source_snapshot(
        REPO_ROOT / "src", runtime_source_parent, repair_id
    )
    roles = {
        "semantic_review_primitives": scripts / "semantic_review_common.py",
        "common": scripts / "repair_pipeline_common.py",
        "selection_builder": scripts / "build_repair_selection.py",
        "supersession_recorder": scripts / "record_repair_prelock_supersession.py",
        "readonly_snapshot_invalidation_recorder": scripts
        / "record_readonly_snapshot_invalidation.py",
        "readonly_interphase_drift_recorder": scripts
        / "record_readonly_interphase_drift.py",
        "repair_readonly_snapshotter": scripts / "capture_repair_readonly_snapshot.py",
        "repair_readonly_helper": scripts / "readonly_snapshot_helper.py",
        "prelock_builder": scripts / "prepare_checklist_repair.py",
        "repair_runner": scripts / "run_checklist_repair_batch.py",
        "scope_aware_guard_builder": scripts / "build_scope_aware_wave3_guard.py",
        "strict_qc_base": scripts / "strict_draft_automatic_qc.py",
        "repair_prompt": prompts / SOURCE_PROMPT.name,
    }
    verify_strict_qc_base_interface(roles["strict_qc_base"])
    files = [
        file_binding(path)
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
    ]
    manifest = {
        "schema_version": "androidworld_checklist_repair_toolchain_snapshot/v1",
        "repair_id": repair_id,
        "created_at": utc_now(),
        "roles": {name: file_binding(path) for name, path in sorted(roles.items())},
        "runtime_source_snapshot": runtime_source_snapshot,
        "runtime_source_manifest": file_binding(runtime_source_manifest)
        | {
            "snapshot_manifest_sha256": load_json(
                runtime_source_manifest, "runtime source snapshot manifest"
            )["snapshot_manifest_sha256"]
        },
        "files": files,
        "file_count": len(files),
        "files_sha256": object_sha256(files),
    }
    manifest = add_self_hash(manifest, "snapshot_sha256")
    path = root / "snapshot_manifest.json"
    write_json_create_once(path, manifest)
    if make_readonly:
        for file in root.rglob("*"):
            if file.is_file():
                file.chmod(0o444)
        for directory in sorted(
            (path for path in root.rglob("*") if path.is_dir()), reverse=True
        ):
            directory.chmod(0o555)
        root.chmod(0o555)
    return path, manifest


def main() -> int:
    args = parse_args()
    verify_strict_qc_base_interface(SOURCE_SCRIPTS / "strict_draft_automatic_qc.py")
    if args.max_parallel != EXPECTED_PARALLELISM:
        raise RepairPipelineError("repair protocol requires exactly 6 concurrent workers")
    if args.codex_timeout_seconds <= 0 or args.large_codex_timeout_seconds <= 0:
        raise RepairPipelineError("Codex timeouts must be positive")
    source_prelock_path = args.source_prelock.resolve()
    source_prelock = load_source_prelock(source_prelock_path)
    source_snapshot_binding = source_prelock.get("toolchain_snapshot") or {}
    source_snapshot_manifest = resolve_repo_path(
        source_snapshot_binding.get("path"), inside_candidate=True
    )
    if (
        not source_snapshot_manifest.is_file()
        or sha256_file(source_snapshot_manifest) != source_snapshot_binding.get("sha256")
        or (
            source_snapshot_binding.get("size_bytes") is not None
            and source_snapshot_manifest.stat().st_size
            != source_snapshot_binding.get("size_bytes")
        )
    ):
        raise RepairPipelineError("source v3 toolchain snapshot manifest byte binding changed")
    source_snapshot_payload = load_json(
        source_snapshot_manifest, "source v3 toolchain snapshot manifest"
    )
    verify_internal_hash(
        source_snapshot_payload,
        ("snapshot_sha256",),
        "source v3 toolchain snapshot manifest",
    )
    if source_snapshot_payload.get("snapshot_sha256") != source_snapshot_binding.get(
        "snapshot_sha256"
    ):
        raise RepairPipelineError("source v3 toolchain snapshot internal hash changed")
    if (
        not isinstance(source_snapshot_binding.get("file_count"), int)
        or isinstance(source_snapshot_binding.get("file_count"), bool)
        or source_snapshot_binding.get("file_count")
        != source_snapshot_payload.get("file_count")
    ):
        raise RepairPipelineError("source v3 toolchain snapshot file_count binding changed")
    source_exact_tree = exact_snapshot_tree_descriptor(
        source_snapshot_manifest.parent,
        label="source_v3_toolchain_snapshot",
        manifest_path=source_snapshot_manifest,
        manifest_self_hash_field="snapshot_sha256",
    )
    source_context_freeze = verify_source_context_freeze(source_prelock)
    wave, _ = verify_source_wave_complete(source_prelock)
    order = list(source_prelock["case_order"])
    automatic_qc_root = args.automatic_qc_root.resolve()
    automatic_qc = verify_automatic_qc(
        automatic_qc_root,
        order,
        source_prelock_path,
        source_prelock,
        wave,
    )
    selection_path = args.audit_selection.resolve()
    selection, audit_rows = load_audit_selection(
        selection_path,
        case_order=order,
        automatic_qc_root=automatic_qc_root,
    )
    reconstructed_selection = verify_selection_reconstructed_from_bound_sources(
        selection_path,
        source=source_prelock,
        wave=wave,
        qc_root=automatic_qc_root,
    )
    if reconstructed_selection != selection:
        raise RepairPipelineError("loaded repair selection differs from source reconstruction")
    repair_rows = [row for row in audit_rows if row["disposition"] == "repair"]
    if not repair_rows:
        raise RepairPipelineError("selection has zero repairs; no repair wave is necessary")
    drift = verify_drift_evidence(
        args.original_generation_guard.resolve(),
        args.changed_path_incident.resolve(),
        args.scope_aware_guard.resolve(),
    )
    runner_environment = closed_child_environment()
    codex = check_codex(runner_environment)
    selection_sha = selection["selection_sha256"]
    repair_id = args.repair_id or f"repair_wave_003_{selection_sha[:12]}"
    if not safe_id(repair_id):
        raise RepairPipelineError("repair id contains unsupported characters")
    supersession = verify_supersession_incident(args.supersession_incident)
    readonly_window = verify_repair_readonly_pre_snapshot(
        args.repair_readonly_pre_snapshot,
        repair_id,
    )
    readonly_window = {
        **readonly_window,
        "interphase_drift_incident": verify_readonly_interphase_drift(
            args.readonly_interphase_drift_incident,
            readonly_window,
        ),
    }
    attempt_root = WORK_ROOT / "repair_generation" / "waves" / repair_id
    output_root = attempt_root / "wave"
    evidence_root = attempt_root / "evidence"
    scratch_root = attempt_root / "scratch"
    effective_root = WORK_ROOT / "repair_generation" / "effective_waves" / f"effective_{repair_id}"
    config_path = WORK_ROOT / "repair_generation" / "config" / f"{repair_id}.config.json"
    prelock_path = WORK_ROOT / "repair_generation" / "freeze" / f"{repair_id}.prelock.json"
    packet_set_root = WORK_ROOT / "repair_generation" / "packet_sets" / repair_id
    snapshot_root = WORK_ROOT / "repair_generation" / "toolchain_snapshot" / repair_id
    readonly_post_path = evidence_root / "readonly.post.json"
    readonly_guard_path = evidence_root / "readonly.guard.json"
    concurrency_samples_path = evidence_root / "concurrency.samples.jsonl"
    concurrency_summary_path = evidence_root / "concurrency.summary.json"
    for target in (
        attempt_root,
        effective_root,
        config_path,
        prelock_path,
        packet_set_root,
        snapshot_root,
    ):
        if target.exists():
            raise RepairPipelineError(f"refusing to overwrite repair artifact: {target}")

    if args.dry_run:
        validation_root = WORK_ROOT / "repair_generation" / "validation"
        validation_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=f"{repair_id}.dry_run_toolchain.", dir=validation_root
        ) as raw_preview:
            preview_root = Path(raw_preview) / repair_id
            preview_manifest_path, preview_snapshot = copy_toolchain(
                repair_id, root=preview_root, make_readonly=False
            )
            preview_repair_exact_tree = exact_snapshot_tree_descriptor(
                preview_root,
                label="repair_toolchain_snapshot",
                manifest_path=preview_manifest_path,
                manifest_self_hash_field="snapshot_sha256",
            )
            preview_runtime_source = preview_snapshot["runtime_source_snapshot"]
            preview_runtime_manifest_raw = Path(
                str(preview_snapshot["runtime_source_manifest"]["path"])
            )
            preview_runtime_manifest = (
                preview_runtime_manifest_raw
                if preview_runtime_manifest_raw.is_absolute()
                else REPO_ROOT / preview_runtime_manifest_raw
            )
            preview_runtime_exact_tree = exact_snapshot_tree_descriptor(
                Path(preview_runtime_source["content_root_absolute_path"]),
                label="repair_runtime_source_snapshot",
                manifest_path=preview_runtime_manifest,
                manifest_self_hash_field="snapshot_manifest_sha256",
            )
            runtime = python_runtime(
                preview_root / "scripts",
                Path(codex["invocation_path"]),
                Path(preview_runtime_source["snapshot_root_absolute_path"]),
            )
            verify_runtime_source_snapshot_binding(
                preview_runtime_source,
                "dry-run runtime source snapshot",
                runtime=runtime,
                repair_exact_tree=preview_repair_exact_tree,
                runtime_source_exact_tree=preview_runtime_exact_tree,
            )
            preview_bootstrap = isolated_bootstrap_record()
            fixture_root = Path(raw_preview)
            fixture_attempt_root = fixture_root / "attempt_root"
            fixture_output_root = fixture_attempt_root / "wave"
            fixture_evidence_root = fixture_attempt_root / "evidence"
            fixture_scratch_root = fixture_attempt_root / "scratch"
            fixture_config_path = fixture_root / "gate_self_test.config.json"
            fixture_prelock_path = fixture_root / "gate_self_test.prelock.json"
            fixture_namespace = add_self_hash(
                {
                    "schema_version": "androidworld_checklist_repair_attempt_namespace/v1",
                    "attempt_root": repo_relative(fixture_attempt_root),
                    "layout": {
                        "wave": repo_relative(fixture_output_root),
                        "evidence": repo_relative(fixture_evidence_root),
                        "scratch": repo_relative(fixture_scratch_root),
                    },
                    "root_must_be_absent_at_prelock_and_generation_preflight": True,
                    "root_claim": "os.mkdir(mode=0700, parents=false, exist_ok=false)",
                    "layout_precreated_inside_claim": True,
                    "directory_fds_held_through_final_prelock_revalidation": True,
                    "all_attempt_artifacts_must_be_contained": True,
                    "restart_archives_entire_attempt_root": True,
                    "appworld_v56_runtime_gate": False,
                },
                "attempt_namespace_sha256",
            )
            fixture_trees = {
                "repair": preview_repair_exact_tree,
                "source_v3": source_exact_tree,
                "runtime_source": preview_runtime_exact_tree,
            }
            fixture_config = add_self_hash(
                {
                    "schema_version": REPAIR_CONFIG_SCHEMA,
                    "status": "gate_self_test_fixture",
                    "repair_id": repair_id,
                    "repository_root_absolute": str(REPO_ROOT.resolve()),
                    "snapshot_exact_trees": fixture_trees,
                    "runtime_source_snapshot": preview_runtime_source,
                    "isolated_bootstrap": preview_bootstrap,
                    "python_runtime": runtime,
                    "runner_environment": runner_environment,
                    "runner_environment_sha256": object_sha256(runner_environment),
                    "attempt_root": repo_relative(fixture_attempt_root),
                    "output_root": repo_relative(fixture_output_root),
                    "evidence_root": repo_relative(fixture_evidence_root),
                    "scratch_root": repo_relative(fixture_scratch_root),
                    "attempt_namespace": fixture_namespace,
                    "runner_command": [],
                    "concurrency_audit": {
                        "samples_path": repo_relative(
                            fixture_evidence_root / "concurrency.samples.jsonl"
                        ),
                        "summary_path": repo_relative(
                            fixture_evidence_root / "concurrency.summary.json"
                        ),
                        "appworld_v56_runtime_gate": False,
                        "attempt_namespace_sha256": fixture_namespace[
                            "attempt_namespace_sha256"
                        ],
                        "runner_environment": runner_environment,
                        "runner_environment_sha256": object_sha256(
                            runner_environment
                        ),
                    },
                    "repair_readonly_window": {
                        "post_snapshot_path": repo_relative(
                            fixture_evidence_root / "readonly.post.json"
                        ),
                        "guard_path": repo_relative(
                            fixture_evidence_root / "readonly.guard.json"
                        ),
                    },
                },
                "config_sha256",
            )
            write_json_create_once(fixture_config_path, fixture_config)
            fixture_roles = preview_snapshot["roles"]
            fixture_prelock = add_self_hash(
                {
                    "schema_version": REPAIR_PRELOCK_SCHEMA,
                    "status": "gate_self_test_fixture",
                    "repair_id": repair_id,
                    "repository_root_absolute": str(REPO_ROOT.resolve()),
                    "repair_config": file_binding(fixture_config_path)
                    | {"config_sha256": fixture_config["config_sha256"]},
                    "snapshot_exact_trees": fixture_trees,
                    "runtime_source_snapshot": preview_runtime_source,
                    "isolated_bootstrap": preview_bootstrap,
                    "runner_execution": {"python_runtime": runtime},
                    "repair_tool_bindings": fixture_roles,
                    "attempt_namespace": fixture_namespace,
                },
                "prelock_sha256",
            )
            write_json_create_once(fixture_prelock_path, fixture_prelock)
            fixture_command = isolated_bootstrap_command(
                runtime=runtime,
                prelock_path=fixture_prelock_path,
                prelock_file_sha256=sha256_file(fixture_prelock_path),
                prelock_internal_sha256=fixture_prelock["prelock_sha256"],
                repair_tree_sha256=preview_repair_exact_tree[
                    "descriptor_sha256"
                ],
                source_tree_sha256=source_exact_tree["descriptor_sha256"],
                runtime_source_tree_sha256=preview_runtime_exact_tree[
                    "descriptor_sha256"
                ],
                mode="outer",
                target=resolve_repo_path(
                    fixture_roles["repair_runner"]["path"], inside_candidate=True
                ),
                target_args=[
                    "--prelock",
                    str(fixture_prelock_path),
                    "--gate-self-test",
                ],
            )
            gate_result = subprocess.run(
                fixture_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
                env=runner_environment,
            )
            if gate_result.returncode != 0:
                raise RepairPipelineError(
                    "actual-prelock gate self-test failed: "
                    f"{gate_result.stderr.strip() or gate_result.stdout.strip()}"
                )
            try:
                gate_self_test_result = json.loads(gate_result.stdout)
            except json.JSONDecodeError as exc:
                raise RepairPipelineError(
                    "actual-prelock gate self-test did not return one JSON object"
                ) from exc
            if gate_self_test_result.get("status") != "gate_self_test_pass":
                raise RepairPipelineError(
                    "actual-prelock gate self-test did not report pass"
                )
        print(
            json.dumps(
                {
                    "status": "dry_run_pass",
                    "repair_id": repair_id,
                    "case_count": EXPECTED_CASE_COUNT,
                    "repair_count": len(repair_rows),
                    "retain_count": EXPECTED_CASE_COUNT - len(repair_rows),
                    "issue_severities": dict(
                        Counter(issue["severity"] for row in repair_rows for issue in row["issues"])
                    ),
                    "source_wave": repo_relative(wave),
                    "scope_aware_guard": drift["scope_aware_guard"],
                    "supersession_incident": supersession,
                    "repair_readonly_pre_snapshot": readonly_window["pre_snapshot"],
                    "codex": codex,
                    "python_runtime": {
                        "invocation_path": runtime["invocation_path"],
                        "resolved_binary_sha256": runtime["resolved_binary_sha256"],
                        "required_execution_flags": runtime[
                            "required_execution_flags"
                        ],
                        "required_execution_state": runtime[
                            "required_execution_state"
                        ],
                        "expected_runner_sys_path": runtime[
                            "expected_runner_sys_path"
                        ],
                        "runtime_sha256": object_sha256(runtime),
                    },
                    "source_v3_exact_tree": {
                        "descriptor_sha256": source_exact_tree[
                            "descriptor_sha256"
                        ],
                        "entry_count": source_exact_tree["entry_count"],
                        "regular_file_count": source_exact_tree[
                            "regular_file_count"
                        ],
                    },
                    "repair_exact_tree_preview": {
                        "descriptor_sha256": preview_repair_exact_tree[
                            "descriptor_sha256"
                        ],
                        "entry_count": preview_repair_exact_tree["entry_count"],
                        "regular_file_count": preview_repair_exact_tree[
                            "regular_file_count"
                        ],
                    },
                    "runtime_source_snapshot_preview": {
                        "source_content_id_sha256": preview_runtime_source[
                            "source_content_id_sha256"
                        ],
                        "runtime_source_snapshot_sha256": preview_runtime_source[
                            "runtime_source_snapshot_sha256"
                        ],
                        "source_entry_count": preview_runtime_source[
                            "source_entry_count"
                        ],
                        "source_regular_file_count": preview_runtime_source[
                            "source_regular_file_count"
                        ],
                        "bytecode_file_count": preview_runtime_source[
                            "bytecode_file_count"
                        ],
                        "live_source_excluded_from_runtime_sys_path": (
                            preview_runtime_source[
                                "live_source_excluded_from_runtime_sys_path"
                            ]
                        ),
                    },
                    "runtime_source_exact_tree_preview": {
                        "descriptor_sha256": preview_runtime_exact_tree[
                            "descriptor_sha256"
                        ],
                        "entry_count": preview_runtime_exact_tree["entry_count"],
                        "regular_file_count": preview_runtime_exact_tree[
                            "regular_file_count"
                        ],
                    },
                    "isolated_bootstrap": {
                        "payload_sha256": isolated_bootstrap_record()[
                            "payload_sha256"
                        ],
                        "binding_sha256": object_sha256(
                            isolated_bootstrap_record()
                        ),
                    },
                    "gate_self_test": gate_self_test_result,
                },
                indent=2,
            )
        )
        return 0

    attempt_root.parent.mkdir(parents=True, exist_ok=True)
    if attempt_root.exists():
        raise RepairPipelineError(
            f"attempt root appeared before prelock publication: {attempt_root}"
        )
    packet_set_root, repair_inputs = materialize_packets(
        repair_id=repair_id,
        prelock=source_prelock,
        audit_rows=audit_rows,
        wave=wave,
    )
    repair_selection_order = [row["case_unit_id"] for row in repair_inputs]
    execution_plan = repair_execution_plan(repair_inputs)
    repair_execution_order = [row["case_unit_id"] for row in execution_plan]
    repair_input_by_case = {row["case_unit_id"]: row for row in repair_inputs}
    config_created = False
    prelock_created = False
    try:
        snapshot_path, snapshot = copy_toolchain(repair_id)
        runtime_source_snapshot = snapshot["runtime_source_snapshot"]
        runtime_source_manifest = resolve_repo_path(
            snapshot["runtime_source_manifest"]["path"], inside_candidate=True
        )
        runtime_source_exact_tree = exact_snapshot_tree_descriptor(
            Path(runtime_source_snapshot["content_root_absolute_path"]),
            label="repair_runtime_source_snapshot",
            manifest_path=runtime_source_manifest,
            manifest_self_hash_field="snapshot_manifest_sha256",
        )
        repair_exact_tree = exact_snapshot_tree_descriptor(
            snapshot_path.parent,
            label="repair_toolchain_snapshot",
            manifest_path=snapshot_path,
            manifest_self_hash_field="snapshot_sha256",
        )
        snapshot_exact_trees = {
            "repair": repair_exact_tree,
            "source_v3": source_exact_tree,
            "runtime_source": runtime_source_exact_tree,
        }
        runtime = python_runtime(
            snapshot_path.parent / "scripts",
            Path(codex["invocation_path"]),
            Path(runtime_source_snapshot["snapshot_root_absolute_path"]),
        )
        if (
            runtime.get("required_environment") != runner_environment
            or runtime.get("semantic_environment_sha256")
            != object_sha256(runner_environment)
        ):
            raise RepairPipelineError(
                "frozen Python runtime differs from the exact closed runner environment"
            )
        verify_runtime_source_snapshot_binding(
            runtime_source_snapshot,
            "frozen runtime source snapshot",
            runtime=runtime,
            repair_exact_tree=repair_exact_tree,
            runtime_source_exact_tree=runtime_source_exact_tree,
        )
        bootstrap = isolated_bootstrap_record()
        roles = snapshot["roles"]
        _, original_batch_runner, _ = tool_binding(source_prelock, "batch_runner")
        original_tools = {
            name: dict(binding)
            for name, binding in (source_prelock.get("tool_bindings") or {}).items()
        }
        for name, binding in original_tools.items():
            verify_file_binding(binding, f"original frozen tool {name}", inside_candidate=True)
        execution_readonly_helper = roles["repair_readonly_helper"]
        if (
            execution_readonly_helper.get("sha256")
            != readonly_window["pre_capture_helper"].get("sha256")
        ):
            raise RepairPipelineError(
                "snapshotted dedicated read-only helper differs from pre-capture helper"
            )
        bound_readonly_window = {
            **readonly_window,
            "execution_helper": execution_readonly_helper,
        }
        runner_command = frozen_runner_command(
            runtime=runtime,
            prelock_path=prelock_path,
            repair_tree_sha256=repair_exact_tree["descriptor_sha256"],
            source_tree_sha256=source_exact_tree["descriptor_sha256"],
            runtime_source_tree_sha256=runtime_source_exact_tree["descriptor_sha256"],
            batch_runner=original_batch_runner,
            packet_root=packet_set_root,
            output_root=output_root,
            prompt=roles["repair_prompt"],
            codex_timeout_seconds=args.codex_timeout_seconds,
            large_codex_timeout_seconds=args.large_codex_timeout_seconds,
        )
        runner_command_sha256 = object_sha256(runner_command)
        if "--appworld-v56-runtime-gate" in runner_command:
            raise RepairPipelineError(
                "AndroidWorld frozen batch command contains the AppWorld-only runtime gate"
            )
        attempt_layout = {
            "wave": repo_relative(output_root),
            "evidence": repo_relative(evidence_root),
            "scratch": repo_relative(scratch_root),
        }
        attempt_namespace = add_self_hash(
            {
                "schema_version": "androidworld_checklist_repair_attempt_namespace/v1",
                "attempt_root": repo_relative(attempt_root),
                "layout": attempt_layout,
                "root_must_be_absent_at_prelock_and_generation_preflight": True,
                "root_claim": "os.mkdir(mode=0700, parents=false, exist_ok=false)",
                "layout_precreated_inside_claim": True,
                "directory_fds_held_through_final_prelock_revalidation": True,
                "all_attempt_artifacts_must_be_contained": True,
                "restart_archives_entire_attempt_root": True,
                "appworld_v56_runtime_gate": False,
            },
            "attempt_namespace_sha256",
        )
        ps_invocation = Path("/bin/ps")
        if not ps_invocation.is_file():
            raise RepairPipelineError("required process audit binary is missing: /bin/ps")
        ps_binary = {
            "invocation_path": "/bin/ps",
            "resolved_path": str(ps_invocation.resolve(strict=True)),
            "sha256": sha256_file(ps_invocation),
            "size_bytes": ps_invocation.stat().st_size,
        }
        expected_attempts = []
        for plan_row in execution_plan:
            row = repair_input_by_case[plan_row["case_unit_id"]]
            case_id = row["case_unit_id"]
            case_packet_path = resolve_repo_path(
                row["bindings"]["batch_packet"]["path"], inside_candidate=True
            )
            case_output_dir = (output_root / case_id).resolve()
            allowed_commands = expected_drafter_attempt_commands(
                runtime=runtime,
                prelock_path=prelock_path,
                repair_tree_sha256=repair_exact_tree["descriptor_sha256"],
                source_tree_sha256=source_exact_tree["descriptor_sha256"],
                runtime_source_tree_sha256=runtime_source_exact_tree[
                    "descriptor_sha256"
                ],
                drafter=original_tools["drafter"],
                packet_path=case_packet_path,
                output_dir=case_output_dir,
                prompt=roles["repair_prompt"],
                regular_codex_timeout_seconds=args.codex_timeout_seconds,
                large_codex_timeout_seconds=args.large_codex_timeout_seconds,
            )
            expected_attempts.append(
                {
                    "execution_rank": plan_row["execution_rank"],
                    "execution_lane": plan_row["lane"],
                    "selection_rank": row["selection_rank"],
                    "case_unit_id": case_id,
                    "task_id": case_id,
                    "case_packet_path": str(case_packet_path),
                    "case_output_dir": str(case_output_dir),
                    "allowed_process_commands": allowed_commands,
                    "allowed_process_commands_sha256": object_sha256(allowed_commands),
                    "allowed_commands_are_prelock_hash_templates": True,
                    "allowed_ps_command_line_sha256": [
                        command["ps_command_line_sha256"] for command in allowed_commands
                    ],
                }
            )
        concurrency_audit = {
            "schema_version": "androidworld_checklist_repair_concurrency_audit_config/v1",
            "required_observed_peak_active_case_attempts": EXPECTED_PARALLELISM,
            "maximum_allowed_active_case_attempts": EXPECTED_PARALLELISM,
            "minimum_samples_at_required_peak": 1,
            "every_repair_case_must_be_observed": True,
            "sample_interval_milliseconds": 100,
            "popen_start_new_session": True,
            "failure_cleanup": {
                "scope": "batch_process_group",
                "term_signal": "SIGTERM",
                "term_grace_seconds": 5,
                "kill_signal": "SIGKILL",
                "kill_wait_seconds": 5,
            },
            "outer_signal_cleanup": {
                "signals": ["SIGINT", "SIGTERM", "SIGHUP"],
                "block_during_popen_and_handler_install": True,
                "cleanup_scope": "batch_process_group",
                "restore_original_handlers_and_mask": True,
            },
            "ps_binary": ps_binary,
            "ps_command": [
                "/bin/ps",
                "-ww",
                "-axo",
                "pid=,ppid=,pgid=,command=",
            ],
            "foreign_process_patterns": [
                "run_checklist_repair_batch.py",
                "run_draft_batch.py",
                "draft_case_checklist.py",
                "codex exec",
            ],
            "foreign_drafting_processes_must_be_absent_at_preflight_and_during_run": True,
            "immediate_foreign_preflight_required_inside_signal_block": True,
            "immediate_foreign_preflight_timing_policy": (
                "after deterministic generation-token revalidation and signal blocking, "
                "atomically claim attempt_root and precreate wave/evidence/scratch; then require "
                "final foreign-process absence immediately before the single batch Popen"
            ),
            "batch_process_group_must_be_empty_postflight": True,
            "monitor_implementation": roles["repair_runner"],
            "outer_wrapper_invocation": roles["repair_runner"],
            "batch_runner_command_sha256": runner_command_sha256,
            "batch_runner_command_is_prelock_hash_template": True,
            "appworld_v56_runtime_gate": False,
            "attempt_namespace_sha256": attempt_namespace[
                "attempt_namespace_sha256"
            ],
            "runner_environment": runner_environment,
            "runner_environment_sha256": object_sha256(runner_environment),
            "isolated_bootstrap_sha256": object_sha256(bootstrap),
            "snapshot_exact_tree_hashes": {
                "repair": repair_exact_tree["descriptor_sha256"],
                "source_v3": source_exact_tree["descriptor_sha256"],
                "runtime_source": runtime_source_exact_tree["descriptor_sha256"],
            },
            "runtime_source_snapshot_sha256": runtime_source_snapshot[
                "runtime_source_snapshot_sha256"
            ],
            "frozen_drafter": original_tools["drafter"],
            "expected_case_attempts": expected_attempts,
            "expected_case_attempts_sha256": object_sha256(expected_attempts),
            "repair_execution_plan": execution_plan,
            "repair_execution_plan_sha256": object_sha256(execution_plan),
            "samples_path": repo_relative(concurrency_samples_path),
            "summary_path": repo_relative(concurrency_summary_path),
            "scope_rule": (
                "count only direct children of this batch PID in its dedicated process group "
                "whose command contains the exact frozen "
                "drafter, one exact repair packet, and that case's exact repair output directory; "
                "the complete observed command line hash must equal one prelocked allowed attempt"
            ),
            "execution_order_semantics": (
                "execution_rank is the frozen lane-aware ThreadPoolExecutor submission plan: "
                "name-sorted regular packets, then name-sorted oversized packets; actual "
                "worker start/completion timing is scheduler-dependent and raw JSONL is "
                "as_completed order"
            ),
        }
        config = {
            "schema_version": REPAIR_CONFIG_SCHEMA,
            "status": "prelocked",
            "repair_id": repair_id,
            "source_generation_id": "wave_003",
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": args.model,
            "model_version_claim": None,
            "model_version_note": (
                "Codex CLI exposes the requested model id but no immutable backend snapshot id."
            ),
            "reasoning_effort": args.reasoning_effort,
            "sandbox": "read-only",
            "ephemeral": True,
            "ignore_user_config": True,
            "max_parallel": EXPECTED_PARALLELISM,
            "large_max_parallel": EXPECTED_PARALLELISM,
            "codex_timeout_seconds": args.codex_timeout_seconds,
            "large_codex_timeout_seconds": args.large_codex_timeout_seconds,
            "token_budgets": [12000, 16000, 20000],
            "quality_check": "none",
            "case_count": EXPECTED_CASE_COUNT,
            "repair_count": len(repair_inputs),
            "candidate_case_order": order,
            "candidate_case_order_sha256": object_sha256(order),
            "repair_selection_order": repair_selection_order,
            "repair_selection_order_sha256": object_sha256(repair_selection_order),
            "repair_execution_order": repair_execution_order,
            "repair_execution_order_sha256": object_sha256(repair_execution_order),
            "repair_execution_plan": execution_plan,
            "repair_execution_plan_sha256": object_sha256(execution_plan),
            "packet_set_root": repo_relative(packet_set_root),
            "repair_prelock_path": repo_relative(prelock_path),
            "attempt_root": repo_relative(attempt_root),
            "output_root": repo_relative(output_root),
            "evidence_root": repo_relative(evidence_root),
            "scratch_root": repo_relative(scratch_root),
            "effective_root": repo_relative(effective_root),
            "repair_runner": roles["repair_runner"],
            "frozen_batch_runner": original_batch_runner,
            "repair_prompt": roles["repair_prompt"],
            "repository_root_absolute": str(REPO_ROOT.resolve()),
            "snapshot_exact_trees": snapshot_exact_trees,
            "snapshot_exact_trees_sha256": object_sha256(snapshot_exact_trees),
            "runtime_source_snapshot": runtime_source_snapshot,
            "runtime_source_snapshot_sha256": runtime_source_snapshot[
                "runtime_source_snapshot_sha256"
            ],
            "isolated_bootstrap": bootstrap,
            "codex_cli": codex,
            "python_runtime": runtime,
            "runner_environment": runner_environment,
            "runner_environment_sha256": object_sha256(runner_environment),
            "attempt_namespace": attempt_namespace,
            "runner_command": runner_command,
            "runner_command_sha256": runner_command_sha256,
            "runner_command_prelock_hash_placeholders": {
                "file_sha256": PRELOCK_FILE_SHA256_PLACEHOLDER,
                "internal_sha256": PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
            },
            "supersession_incident": supersession,
            "repair_readonly_window": {
                **bound_readonly_window,
                "post_snapshot_path": repo_relative(readonly_post_path),
                "guard_path": repo_relative(readonly_guard_path),
            },
            "concurrency_audit": concurrency_audit,
            "created_at": utc_now(),
        }
        config = add_self_hash(config, "config_sha256")
        write_json_create_once(config_path, config)
        config_created = True
        source_binding = file_binding(source_prelock_path) | {
            "prelock_sha256": source_prelock["prelock_sha256"]
        }
        retain_rows = [
            {
                "selection_rank": row["selection_rank"],
                "case_unit_id": row["case_unit_id"],
                "task_id": row["task_id"],
                "audit_case_sha256": row["audit_case_sha256"],
                "automatic_qc": row["automatic_qc"],
                "audit_sources": row["audit_sources"],
            }
            for row in audit_rows
            if row["disposition"] == "retain"
        ]
        prelock = {
            "schema_version": REPAIR_PRELOCK_SCHEMA,
            "status": "frozen_before_first_repair_model_call",
            "repair_id": repair_id,
            "source_generation_id": "wave_003",
            "created_at": utc_now(),
            "repository_root_absolute": str(REPO_ROOT.resolve()),
            "case_count": EXPECTED_CASE_COUNT,
            "case_order": order,
            "case_order_sha256": object_sha256(order),
            "candidate_case_order": order,
            "candidate_case_order_sha256": object_sha256(order),
            "repair_selection_order": repair_selection_order,
            "repair_selection_order_sha256": object_sha256(repair_selection_order),
            "repair_execution_order": repair_execution_order,
            "repair_execution_order_sha256": object_sha256(repair_execution_order),
            "repair_execution_plan": execution_plan,
            "repair_execution_plan_sha256": object_sha256(execution_plan),
            "order_semantics": REPAIR_ORDER_SEMANTICS,
            "repair_count": len(repair_inputs),
            "retain_count": len(retain_rows),
            "repair_inputs": repair_inputs,
            "repair_inputs_sha256": object_sha256(repair_inputs),
            "retain_inputs": retain_rows,
            "retain_inputs_sha256": object_sha256(retain_rows),
            "audit_selection": file_binding(selection_path)
            | {"selection_sha256": selection["selection_sha256"]},
            "audit_rows_sha256": object_sha256(audit_rows),
            "automatic_qc": automatic_qc,
            "source_draft": {
                "prelock": source_binding,
                "raw_wave": repo_relative(wave),
                "batch_summary": file_binding(wave / "_batch_summary.json"),
                "batch_results": file_binding(wave / "_batch_results.jsonl"),
                "packet_source_context_freeze": source_context_freeze,
            },
            "drift_evidence": drift,
            "supersedes": {
                "incident": supersession,
                "policy": "v1 selection/prelock aborted before first repair model call; promotion forbidden",
            },
            "repair_readonly_window": {
                **bound_readonly_window,
                "post_snapshot_path": repo_relative(readonly_post_path),
                "guard_path": repo_relative(readonly_guard_path),
                "post_snapshot_required_before_receipt": True,
                "protected_roots_and_official100_exact_equality_required": True,
            },
            "concurrency_audit": concurrency_audit,
            "attempt_namespace": attempt_namespace,
            "repair_config": file_binding(config_path) | {"config_sha256": config["config_sha256"]},
            "repair_toolchain_snapshot": file_binding(snapshot_path)
            | {"snapshot_sha256": snapshot["snapshot_sha256"]},
            "snapshot_exact_trees": snapshot_exact_trees,
            "snapshot_exact_trees_sha256": object_sha256(snapshot_exact_trees),
            "runtime_source_snapshot": runtime_source_snapshot,
            "runtime_source_snapshot_sha256": runtime_source_snapshot[
                "runtime_source_snapshot_sha256"
            ],
            "isolated_bootstrap": bootstrap,
            "repair_tool_bindings": roles,
            "original_v3_tool_bindings": original_tools,
            "codex_cli": codex,
            "runner_execution": {
                "python_runtime": runtime,
                "environment": runner_environment,
                "environment_sha256": object_sha256(runner_environment),
                "command": runner_command,
                "command_sha256": runner_command_sha256,
                "command_is_prelock_hash_template": True,
                "prelock_hash_placeholders": {
                    "file_sha256": PRELOCK_FILE_SHA256_PLACEHOLDER,
                    "internal_sha256": PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
                },
                "repair_execution_order": repair_execution_order,
                "repair_execution_order_sha256": object_sha256(repair_execution_order),
                "repair_execution_plan": execution_plan,
                "repair_execution_plan_sha256": object_sha256(execution_plan),
                "model_request_id": args.model,
                "model_version_claim": None,
                "model_version_note": (
                    "Codex CLI exposes the requested model id but no immutable backend snapshot id."
                ),
            },
            "canonical_output_gate": {
                "repair_wave": repo_relative(output_root),
                "effective_wave": repo_relative(effective_root),
                "effective_qc_required": True,
                "new_independent_codex_semantic_reviews_required": True,
                "explicit_root_agent_acceptance_required": True,
                "legacy_direct_promotion_forbidden": True,
                "separate_content_addressed_downstream_prelock_required": True,
                "downstream_tools_not_part_of_repair_generation_snapshot": True,
            },
        }
        prelock = add_self_hash(prelock, "prelock_sha256")
        write_json_create_once(prelock_path, prelock)
        prelock_created = True
    except BaseException:
        shutil.rmtree(packet_set_root, ignore_errors=True)
        if snapshot_root.exists():
            for path in snapshot_root.rglob("*"):
                try:
                    path.chmod(0o755 if path.is_dir() else 0o644)
                except OSError:
                    pass
            try:
                snapshot_root.chmod(0o755)
            except OSError:
                pass
            shutil.rmtree(snapshot_root, ignore_errors=True)
        if config_created:
            config_path.unlink(missing_ok=True)
        if prelock_created:
            prelock_path.unlink(missing_ok=True)
        raise
    prelock_file = file_binding(prelock_path)
    outer_command = isolated_bootstrap_command(
        runtime=runtime,
        prelock_path=prelock_path,
        prelock_file_sha256=prelock_file["sha256"],
        prelock_internal_sha256=prelock["prelock_sha256"],
        repair_tree_sha256=repair_exact_tree["descriptor_sha256"],
        source_tree_sha256=source_exact_tree["descriptor_sha256"],
        runtime_source_tree_sha256=runtime_source_exact_tree["descriptor_sha256"],
        mode="outer",
        target=resolve_repo_path(roles["repair_runner"]["path"], inside_candidate=True),
        target_args=["--prelock", str(prelock_path)],
    )
    print(
        json.dumps(
            {
                "status": "prelocked",
                "repair_id": repair_id,
                "case_count": EXPECTED_CASE_COUNT,
                "repair_count": len(repair_inputs),
                "retain_count": len(retain_rows),
                "prelock": prelock_file
                | {"prelock_sha256": prelock["prelock_sha256"]},
                "run_command": outer_command,
                "run_command_sha256": object_sha256(outer_command),
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
