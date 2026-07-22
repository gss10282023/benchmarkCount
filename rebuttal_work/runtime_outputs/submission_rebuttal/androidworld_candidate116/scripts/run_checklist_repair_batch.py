#!/usr/bin/env python3
"""Run prelocked checklist repairs through the immutable v3 batch runner."""

# ruff: noqa: E402 -- the built-in-only admission gate must run before imports.

from __future__ import annotations

import sys as _bootstrap_sys

_bootstrap_flags = {
    "isolated": int(_bootstrap_sys.flags.isolated),
    "no_site": int(_bootstrap_sys.flags.no_site),
    "ignore_environment": int(_bootstrap_sys.flags.ignore_environment),
    "safe_path": bool(getattr(_bootstrap_sys.flags, "safe_path", False)),
}
_bootstrap_admission = getattr(
    _bootstrap_sys, "_androidworld_isolated_bootstrap_admission", None
)
if (
    _bootstrap_flags
    != {"isolated": 1, "no_site": 1, "ignore_environment": 1, "safe_path": True}
    or not isinstance(_bootstrap_admission, str)
    or len(_bootstrap_admission) != 64
):
    raise SystemExit(
        "ERROR: direct repair-runner invocation is forbidden; use the fully expanded "
        "prelocked python -I -S -c isolated bootstrap command"
    )
del _bootstrap_admission, _bootstrap_flags, _bootstrap_sys

import argparse
import ast
import importlib.util
import json
import os
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import SemanticReviewError
from build_repair_selection import verify_selection_reconstructed_from_bound_sources

from repair_pipeline_common import (
    ATTEMPT_LAYOUT_ROLES,
    ATTEMPT_ROOT_CLAIM_SCHEMA,
    AUTOMATIC_QC_CHECK_KEYS,
    CODEX_PATH_ALIAS_WARNING,
    EXPECTED_PARALLELISM,
    PRELOCK_FILE_SHA256_PLACEHOLDER,
    PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
    REPAIR_CONFIG_SCHEMA,
    REPAIR_LARGE_CASE_THRESHOLD_BYTES,
    REPAIR_ORDER_SEMANTICS,
    RUNTIME_SOURCE_SNAPSHOT_SCHEMA,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    canonical_diff,
    canonical_runtime_tree,
    case_file_bindings,
    exact_snapshot_tree_descriptor,
    file_binding,
    expand_prelock_sha256,
    isolated_bootstrap_command,
    isolated_bootstrap_record,
    load_json,
    load_jsonl,
    load_audit_selection,
    load_repair_prelock,
    load_source_prelock,
    object_sha256,
    parse_codex_login_status,
    python_runtime_binding,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    tree_record,
    utc_now,
    verify_binding_tree,
    verify_checklist_pair,
    verify_closed_child_environment,
    verify_file_binding,
    verify_exact_snapshot_tree_descriptor,
    verify_internal_hash,
    verify_immediate_foreign_preflight_evidence,
    verify_attempt_root_claim,
    verify_python_runtime_binding,
    verify_runtime_source_snapshot_binding,
    verify_repair_order_bindings,
    verify_source_wave_complete,
    verify_source_context_freeze,
    write_json_create_once,
)


REPO_ROOT = WORK_ROOT.parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path, required=False)
    parser.add_argument(
        "--restart-after-incident",
        action="store_true",
        help="Archive the entire pre-existing failed repair wave, then restart from empty.",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--gate-self-test", action="store_true")
    return parser.parse_args()


def enforce_frozen_runner_identity(prelock_path: Path) -> dict[str, Any]:
    """Reject invoking this protocol through the live, unfrozen wrapper."""

    preview = load_json(prelock_path, "repair prelock identity preview")
    binding = (preview.get("repair_tool_bindings") or {}).get("repair_runner")
    expected = verify_file_binding(
        binding, "prelocked repair runner identity", inside_candidate=True
    )
    actual = Path(__file__).resolve()
    if actual != expected:
        raise RepairPipelineError(
            f"repair must be invoked through the snapshotted runner: {actual} != {expected}"
        )
    return dict(binding)


def current_codex(
    prelock: Mapping[str, Any], environment: Mapping[str, str]
) -> dict[str, Any]:
    exact_environment = verify_closed_child_environment(
        environment, "Codex auth-check environment"
    )
    raw = shutil.which("codex", path=exact_environment["PATH"])
    if not raw:
        raise RepairPipelineError("codex is not on PATH")
    invocation = Path(os.path.abspath(raw))
    binary = invocation.resolve()
    expected = prelock.get("codex_cli") or {}
    if (
        str(invocation) != expected.get("invocation_path")
        or str(binary) != expected.get("binary_path")
        or sha256_file(binary) != expected.get("binary_sha256")
    ):
        raise RepairPipelineError("Codex CLI binary/path changed after repair prelock")
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
            f"Codex login is inactive: version_rc={version.returncode}, "
            f"login_rc={login.returncode}"
        )
    version_output = version.stdout.strip()
    version_stderr = [line.strip() for line in version.stderr.splitlines() if line.strip()]
    if version_stderr not in ([], [CODEX_PATH_ALIAS_WARNING]):
        raise RepairPipelineError(
            f"Codex version emitted unrecognized stderr: {version_stderr}"
        )
    login_evidence = parse_codex_login_status(
        login.stdout, login.stderr, "Codex login status"
    )
    if version_output != expected.get("version"):
        raise RepairPipelineError("Codex CLI version output changed after repair prelock")
    if expected.get("login_success_format") != "Logged in using ChatGPT":
        raise RepairPipelineError("prelocked Codex login success format is invalid")
    evidence = {
        "schema_version": "androidworld_checklist_repair_codex_auth_check/v1",
        "checked_at": utc_now(),
        "invocation_path": str(invocation),
        "binary_path": str(binary),
        "binary_sha256": sha256_file(binary),
        "version": version_output,
        "cli_version": expected.get("cli_version"),
        "login_status": login_evidence["login_status"],
        "login_path_alias_warning_present": login_evidence[
            "path_alias_warning_present"
        ],
        "login_path_alias_warning": login_evidence["path_alias_warning"],
        "login_path_alias_warning_sha256": login_evidence[
            "path_alias_warning_sha256"
        ],
        "version_path_alias_warning_present": bool(version_stderr),
        "environment_sha256": object_sha256(exact_environment),
        "auth_mode": "codex_login",
    }
    return add_self_hash(evidence, "auth_check_sha256")


def load_readonly_helper(binding: Mapping[str, Any]) -> Any:
    path = verify_file_binding(binding, "repair read-only snapshot helper", inside_candidate=True)
    spec = importlib.util.spec_from_file_location("candidate116_repair_runtime_readonly_helper", path)
    if spec is None or spec.loader is None:
        raise RepairPipelineError(f"cannot load repair read-only helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("readonly_operation_snapshot", "readonly_snapshot_core"):
        if not callable(getattr(module, name, None)):
            raise RepairPipelineError(f"repair read-only helper lacks {name}")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
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
    return module


def readonly_record_core(record: Mapping[str, Any]) -> dict[str, Any]:
    readonly = record.get("readonly_snapshot")
    if not isinstance(readonly, Mapping):
        raise RepairPipelineError("repair read-only snapshot has no payload")
    return {
        "write_scope": readonly.get("write_scope"),
        "policy": readonly.get("policy"),
        "roots": readonly.get("roots"),
        "official100": readonly.get("official100"),
    }


def verify_readonly_window_static(
    config: Mapping[str, Any], prelock: Mapping[str, Any]
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    config_window = config.get("repair_readonly_window")
    prelock_window = prelock.get("repair_readonly_window")
    if not isinstance(config_window, Mapping) or not isinstance(prelock_window, Mapping):
        raise RepairPipelineError("repair read-only window is missing")
    for field in (
        "pre_snapshot",
        "pre_capture_helper",
        "execution_helper",
        "invalidated_pre_snapshot_incident",
        "interphase_drift_incident",
        "protected_roots",
        "nonbinding_live_tool_root",
        "official100_path",
        "post_snapshot_path",
        "guard_path",
    ):
        if config_window.get(field) != prelock_window.get(field):
            raise RepairPipelineError(f"repair read-only window {field} differs across config/prelock")
    pre_path = verify_file_binding(
        config_window.get("pre_snapshot"), "repair read-only pre-snapshot", inside_candidate=True
    )
    record = load_json(pre_path, "repair read-only pre-snapshot")
    if record.get("schema_version") != "androidworld_checklist_repair_readonly_snapshot/v2":
        raise RepairPipelineError("repair read-only pre-snapshot schema is invalid")
    verify_internal_hash(record, ("snapshot_sha256",), "repair read-only pre-snapshot")
    if (
        record.get("snapshot_sha256") != config_window["pre_snapshot"].get("snapshot_sha256")
        or record.get("readonly_core_sha256")
        != config_window["pre_snapshot"].get("readonly_core_sha256")
    ):
        raise RepairPipelineError("repair read-only pre-snapshot hashes differ")
    if record.get("snapshot_helper") != config_window.get("pre_capture_helper"):
        raise RepairPipelineError("repair pre-capture helper differs from pre-snapshot")
    if (
        config_window["pre_capture_helper"].get("sha256")
        != config_window["execution_helper"].get("sha256")
    ):
        raise RepairPipelineError("snapshotted execution helper bytes differ from pre-capture helper")
    helper = load_readonly_helper(config_window["execution_helper"])
    if record.get("readonly_core_sha256") != object_sha256(
        helper.readonly_snapshot_core(record["readonly_snapshot"])
    ):
        raise RepairPipelineError("repair read-only pre-snapshot dedicated core hash differs")
    incident_path = verify_file_binding(
        config_window["invalidated_pre_snapshot_incident"],
        "v1 pre-snapshot invalidation incident",
        inside_candidate=True,
    )
    incident = load_json(incident_path, "v1 pre-snapshot invalidation incident")
    verify_internal_hash(incident, ("incident_sha256",), "v1 pre-snapshot invalidation")
    if (
        incident.get("status") != "invalidated_before_repair_prelock"
        or incident.get("promotion_forbidden") is not True
        or incident.get("model_calls_started") is not False
        or incident.get("incident_sha256")
        != config_window["invalidated_pre_snapshot_incident"].get("incident_sha256")
    ):
        raise RepairPipelineError("v1 pre-snapshot invalidation incident is invalid")
    drift_path = verify_file_binding(
        config_window["interphase_drift_incident"],
        "read-only interphase drift incident",
        inside_candidate=True,
    )
    drift = load_json(drift_path, "read-only interphase drift incident")
    verify_internal_hash(drift, ("incident_sha256",), "read-only interphase drift")
    if (
        drift.get("status") != "recorded_interphase_drift_before_repair_prelock"
        or drift.get("repair_model_calls_started") is not False
        or drift.get("repair_prelock_created") is not False
        or drift.get("deletion_performed") is not False
        or drift.get("old_v1_snapshot") != incident.get("invalidated_pre_snapshot")
        or (drift.get("new_v2_snapshot") or {}).get("snapshot_sha256")
        != record.get("snapshot_sha256")
        or (drift.get("root_content_equality") or {}).get("results") is not False
        or drift.get("paper_result_packages_equal") is not True
        or drift.get("submitted_official100_package_equal") is not True
        or drift.get("official100_selector_equal") is not True
    ):
        raise RepairPipelineError("read-only interphase drift incident is invalid")
    protected = config_window.get("protected_roots")
    if not isinstance(protected, list) or set(protected) != {
        "results",
        "paper_result_packages",
        "paper_result_packages/androidworld_both_agents_scored_cases_official_full100",
    }:
        raise RepairPipelineError("repair read-only protected-root set is invalid")
    if config_window.get("nonbinding_live_tool_root") != "neurips_ed_track_minimal":
        raise RepairPipelineError("repair read-only nonbinding live-tool root is invalid")
    if config_window.get("official100_path") != (
        "experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json"
    ):
        raise RepairPipelineError("repair read-only official100 selector path is invalid")
    return record, helper, dict(config_window)


def _attempt_layout(config: Mapping[str, Any]) -> tuple[Path, dict[str, Path]]:
    attempt_root = resolve_repo_path(config.get("attempt_root"), inside_candidate=True)
    layout = {
        "wave": resolve_repo_path(config.get("output_root"), inside_candidate=True),
        "evidence": resolve_repo_path(config.get("evidence_root"), inside_candidate=True),
        "scratch": resolve_repo_path(config.get("scratch_root"), inside_candidate=True),
    }
    if layout["wave"] != attempt_root / "wave":
        raise RepairPipelineError("attempt wave path differs from fixed layout")
    if layout["evidence"] != attempt_root / "evidence":
        raise RepairPipelineError("attempt evidence path differs from fixed layout")
    if layout["scratch"] != attempt_root / "scratch":
        raise RepairPipelineError("attempt scratch path differs from fixed layout")
    return attempt_root, layout


def verify_attempt_namespace_contract(
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    *,
    require_absent: bool | None,
    claim: Mapping[str, Any] | None = None,
) -> tuple[Path, dict[str, Path]]:
    namespace = config.get("attempt_namespace")
    if not isinstance(namespace, Mapping) or namespace != prelock.get(
        "attempt_namespace"
    ):
        raise RepairPipelineError("attempt namespace differs across config/prelock")
    verify_internal_hash(
        namespace, ("attempt_namespace_sha256",), "attempt namespace"
    )
    attempt_root, layout = _attempt_layout(config)
    expected = {
        "schema_version": "androidworld_checklist_repair_attempt_namespace/v1",
        "attempt_root": repo_relative(attempt_root),
        "layout": {role: repo_relative(layout[role]) for role in ATTEMPT_LAYOUT_ROLES},
        "root_must_be_absent_at_prelock_and_generation_preflight": True,
        "root_claim": "os.mkdir(mode=0700, parents=false, exist_ok=false)",
        "layout_precreated_inside_claim": True,
        "directory_fds_held_through_final_prelock_revalidation": True,
        "all_attempt_artifacts_must_be_contained": True,
        "restart_archives_entire_attempt_root": True,
        "appworld_v56_runtime_gate": False,
    }
    if any(namespace.get(key) != value for key, value in expected.items()):
        raise RepairPipelineError("attempt namespace contract differs")
    evidence_paths = [
        resolve_repo_path(
            config["concurrency_audit"]["samples_path"], inside_candidate=True
        ),
        resolve_repo_path(
            config["concurrency_audit"]["summary_path"], inside_candidate=True
        ),
        resolve_repo_path(
            config["repair_readonly_window"]["post_snapshot_path"],
            inside_candidate=True,
        ),
        resolve_repo_path(
            config["repair_readonly_window"]["guard_path"], inside_candidate=True
        ),
    ]
    if any(path.parent != layout["evidence"] for path in evidence_paths):
        raise RepairPipelineError("attempt evidence artifact escapes evidence root")
    if require_absent is True:
        if os.path.lexists(attempt_root):
            raise RepairPipelineError(
                f"attempt root must be absent before claim: {attempt_root}"
            )
        if claim is not None:
            raise RepairPipelineError("attempt claim is forbidden while requiring absence")
    elif require_absent is False:
        if claim is None:
            raise RepairPipelineError("live attempt namespace requires its exact claim")
        verify_attempt_root_claim(
            claim,
            repair_id=str(prelock.get("repair_id") or ""),
            attempt_root=attempt_root,
            expected_layout=layout,
            label="live repair attempt claim",
        )
    elif claim is not None:
        raise RepairPipelineError("state-neutral attempt validation forbids a claim")
    return attempt_root, layout


def verify_prelocked_context(
    prelock_path: Path,
    *,
    require_attempt_root_absent: bool | None = True,
    attempt_claim: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prelock = load_repair_prelock(prelock_path)
    if getattr(sys, "_androidworld_isolated_bootstrap_admission", None) != prelock.get(
        "prelock_sha256"
    ):
        raise RepairPipelineError("isolated-bootstrap admission differs from repair prelock")
    if getattr(
        sys, "_androidworld_isolated_bootstrap_prelock_file_sha256", None
    ) != sha256_file(prelock_path):
        raise RepairPipelineError("isolated-bootstrap physical prelock admission differs")
    orders = verify_repair_order_bindings(prelock)
    config_path = verify_file_binding(prelock.get("repair_config"), "repair config", inside_candidate=True)
    config = load_json(config_path, "repair config")
    if config.get("schema_version") != REPAIR_CONFIG_SCHEMA or config.get("status") != "prelocked":
        raise RepairPipelineError("repair config schema/status is invalid")
    verify_internal_hash(config, ("config_sha256",), "repair config")
    if prelock["repair_config"].get("config_sha256") != config["config_sha256"]:
        raise RepairPipelineError("repair config internal hash differs from prelock")
    if (
        prelock.get("repository_root_absolute") != str(REPO_ROOT.resolve())
        or config.get("repository_root_absolute") != str(REPO_ROOT.resolve())
        or resolve_repo_path(config.get("repair_prelock_path"), inside_candidate=True)
        != prelock_path.resolve()
    ):
        raise RepairPipelineError("repository-root binding differs across config/prelock")
    exact_trees = prelock.get("snapshot_exact_trees")
    if (
        not isinstance(exact_trees, Mapping)
        or exact_trees != config.get("snapshot_exact_trees")
        or set(exact_trees) != {"repair", "source_v3", "runtime_source"}
        or prelock.get("snapshot_exact_trees_sha256") != object_sha256(exact_trees)
        or config.get("snapshot_exact_trees_sha256") != object_sha256(exact_trees)
    ):
        raise RepairPipelineError("snapshot exact-tree descriptors differ across config/prelock")
    for name in ("repair", "source_v3", "runtime_source"):
        verify_exact_snapshot_tree_descriptor(exact_trees[name], f"{name} snapshot")
    bootstrap = isolated_bootstrap_record()
    if bootstrap != prelock.get("isolated_bootstrap") or bootstrap != config.get(
        "isolated_bootstrap"
    ):
        raise RepairPipelineError("isolated-bootstrap bytes/policy differ across config/prelock")
    expected = {
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": "gpt-5.6-sol",
        "model_version_claim": None,
        "model_version_note": (
            "Codex CLI exposes the requested model id but no immutable backend snapshot id."
        ),
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
    if (
        config.get("candidate_case_order") != orders["candidate_case_order"]
        or config.get("candidate_case_order_sha256")
        != object_sha256(orders["candidate_case_order"])
        or config.get("repair_selection_order") != orders["repair_selection_order"]
        or config.get("repair_selection_order_sha256")
        != object_sha256(orders["repair_selection_order"])
        or config.get("repair_execution_order") != orders["repair_execution_order"]
        or config.get("repair_execution_order_sha256")
        != object_sha256(orders["repair_execution_order"])
        or config.get("repair_execution_plan") != orders["repair_execution_plan"]
        or config.get("repair_execution_plan_sha256")
        != object_sha256(orders["repair_execution_plan"])
    ):
        raise RepairPipelineError("repair config case/execution orders differ from prelock")
    if (
        (prelock.get("runner_execution") or {}).get("model_request_id") != "gpt-5.6-sol"
        or (prelock.get("runner_execution") or {}).get("model_version_claim") is not None
        or (prelock.get("runner_execution") or {}).get("model_version_note")
        != expected["model_version_note"]
        or (prelock.get("codex_cli") or {}).get("cli_version") != "0.144.4"
        or (prelock.get("codex_cli") or {}).get("version") != "codex-cli 0.144.4"
        or (prelock.get("codex_cli") or {}).get("login_status_at_prelock")
        != "Logged in using ChatGPT"
        or (prelock.get("codex_cli") or {}).get("login_success_format")
        != "Logged in using ChatGPT"
        or (prelock.get("codex_cli") or {}).get(
            "login_path_alias_warning_present_at_prelock"
        )
        not in {True, False}
        or (
            (prelock.get("codex_cli") or {}).get(
                "login_path_alias_warning_at_prelock"
            )
            != (
                CODEX_PATH_ALIAS_WARNING
                if (prelock.get("codex_cli") or {}).get(
                    "login_path_alias_warning_present_at_prelock"
                )
                else None
            )
        )
        or (
            (prelock.get("codex_cli") or {}).get(
                "login_path_alias_warning_sha256_at_prelock"
            )
            != (
                object_sha256(CODEX_PATH_ALIAS_WARNING)
                if (prelock.get("codex_cli") or {}).get(
                    "login_path_alias_warning_present_at_prelock"
                )
                else None
            )
        )
    ):
        raise RepairPipelineError("truthful model-version/Codex CLI binding differs")
    runtime = config.get("python_runtime")
    if runtime != (prelock.get("runner_execution") or {}).get("python_runtime"):
        raise RepairPipelineError("Python runtime differs across repair config/prelock")
    if (
        (runtime or {}).get("codex_invocation_path")
        != (prelock.get("codex_cli") or {}).get("invocation_path")
        or (runtime or {}).get("codex_invocation_sha256")
        != (prelock.get("codex_cli") or {}).get("binary_sha256")
    ):
        raise RepairPipelineError("Python runtime Codex path/bytes differ from Codex binding")
    verify_python_runtime_binding(runtime, "prelocked Python runtime")
    runtime_source_snapshot = prelock.get("runtime_source_snapshot")
    if (
        not isinstance(runtime_source_snapshot, Mapping)
        or runtime_source_snapshot != config.get("runtime_source_snapshot")
        or prelock.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot.get("runtime_source_snapshot_sha256")
        or config.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot.get("runtime_source_snapshot_sha256")
    ):
        raise RepairPipelineError(
            "runtime source snapshot binding differs across config/prelock"
        )
    verify_runtime_source_snapshot_binding(
        runtime_source_snapshot,
        "prelocked runtime source snapshot",
        runtime=runtime,
        repair_exact_tree=exact_trees["repair"],
        runtime_source_exact_tree=exact_trees["runtime_source"],
    )
    required_environment = verify_closed_child_environment(
        (runtime or {}).get("required_environment"),
        "prelocked Python closed child environment",
    )
    forbidden_environment = ["PYTHONHOME", "PYTHONPATH", "PYTHONSAFEPATH", "PYTHONUSERBASE"]
    if (
        shutil.which("codex", path=required_environment["PATH"])
        != (prelock.get("codex_cli") or {}).get("invocation_path")
        or (runtime or {}).get("forbidden_child_python_environment")
        != forbidden_environment
        or (runtime or {}).get("semantic_environment_sha256")
        != object_sha256(required_environment)
        or config.get("runner_environment") != required_environment
        or config.get("runner_environment_sha256")
        != object_sha256(required_environment)
        or (prelock.get("runner_execution") or {}).get("environment") != required_environment
        or (prelock.get("runner_execution") or {}).get("environment_sha256")
        != object_sha256(required_environment)
        or (config.get("concurrency_audit") or {}).get("runner_environment")
        != required_environment
        or (config.get("concurrency_audit") or {}).get(
            "runner_environment_sha256"
        )
        != object_sha256(required_environment)
        or (prelock.get("codex_cli") or {}).get("environment_sha256")
        != object_sha256(required_environment)
        or getattr(sys, "_androidworld_closed_child_environment_sha256", None)
        != object_sha256(required_environment)
        or dict(os.environ) != required_environment
    ):
        raise RepairPipelineError("repair runner environment contract is invalid")
    command = config.get("runner_command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(item, str) or not item for item in command)
        or config.get("runner_command_sha256") != object_sha256(command)
        or (prelock.get("runner_execution") or {}).get("command") != command
        or (prelock.get("runner_execution") or {}).get("command_sha256")
        != config.get("runner_command_sha256")
        or command[:5]
        != [runtime["invocation_path"], "-I", "-S", "-c", bootstrap["payload"]]
        or command.count(PRELOCK_FILE_SHA256_PLACEHOLDER) != 1
        or command.count(PRELOCK_INTERNAL_SHA256_PLACEHOLDER) != 1
        or config.get("runner_command_prelock_hash_placeholders")
        != {
            "file_sha256": PRELOCK_FILE_SHA256_PLACEHOLDER,
            "internal_sha256": PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
        }
        or (prelock.get("runner_execution") or {}).get(
            "command_is_prelock_hash_template"
        )
        is not True
        or (prelock.get("runner_execution") or {}).get("prelock_hash_placeholders")
        != config.get("runner_command_prelock_hash_placeholders")
        or "--appworld-v56-runtime-gate" in command
    ):
        raise RepairPipelineError("repair runner command/hash differs across config/prelock")
    concurrency = config.get("concurrency_audit")
    if not isinstance(concurrency, Mapping) or concurrency != prelock.get("concurrency_audit"):
        raise RepairPipelineError("concurrency audit config differs across config/prelock")
    if (
        concurrency.get("required_observed_peak_active_case_attempts") != EXPECTED_PARALLELISM
        or concurrency.get("maximum_allowed_active_case_attempts") != EXPECTED_PARALLELISM
        or concurrency.get("minimum_samples_at_required_peak") != 1
        or concurrency.get("every_repair_case_must_be_observed") is not True
        or concurrency.get("sample_interval_milliseconds") != 100
        or concurrency.get("popen_start_new_session") is not True
        or concurrency.get("failure_cleanup")
        != {
            "scope": "batch_process_group",
            "term_signal": "SIGTERM",
            "term_grace_seconds": 5,
            "kill_signal": "SIGKILL",
            "kill_wait_seconds": 5,
        }
        or concurrency.get("outer_signal_cleanup")
        != {
            "signals": ["SIGINT", "SIGTERM", "SIGHUP"],
            "block_during_popen_and_handler_install": True,
            "cleanup_scope": "batch_process_group",
            "restore_original_handlers_and_mask": True,
        }
        or concurrency.get("ps_command")
        != ["/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,command="]
        or concurrency.get("foreign_process_patterns")
        != [
            "run_checklist_repair_batch.py",
            "run_draft_batch.py",
            "draft_case_checklist.py",
            "codex exec",
        ]
        or concurrency.get(
            "foreign_drafting_processes_must_be_absent_at_preflight_and_during_run"
        )
        is not True
        or concurrency.get(
            "immediate_foreign_preflight_required_inside_signal_block"
        )
        is not True
        or concurrency.get("immediate_foreign_preflight_timing_policy")
        != (
            "after deterministic generation-token revalidation and signal blocking, "
            "atomically claim attempt_root and precreate wave/evidence/scratch; then require "
            "final foreign-process absence immediately before the single batch Popen"
        )
        or concurrency.get("batch_process_group_must_be_empty_postflight") is not True
        or concurrency.get("batch_runner_command_sha256") != config.get("runner_command_sha256")
        or concurrency.get("batch_runner_command_is_prelock_hash_template") is not True
        or concurrency.get("isolated_bootstrap_sha256") != object_sha256(bootstrap)
        or concurrency.get("snapshot_exact_tree_hashes")
        != {
            "repair": exact_trees["repair"]["descriptor_sha256"],
            "source_v3": exact_trees["source_v3"]["descriptor_sha256"],
            "runtime_source": exact_trees["runtime_source"]["descriptor_sha256"],
        }
        or concurrency.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot["runtime_source_snapshot_sha256"]
        or concurrency.get("repair_execution_plan") != orders["repair_execution_plan"]
        or concurrency.get("repair_execution_plan_sha256")
        != object_sha256(orders["repair_execution_plan"])
        or concurrency.get("execution_order_semantics")
        != (
            "execution_rank is the frozen lane-aware ThreadPoolExecutor submission plan: "
            "name-sorted regular packets, then name-sorted oversized packets; actual "
            "worker start/completion timing is scheduler-dependent and raw JSONL is "
            "as_completed order"
        )
    ):
        raise RepairPipelineError("concurrency audit fixed execution contract is invalid")
    ps_binding = concurrency.get("ps_binary") or {}
    ps_path = Path(str(ps_binding.get("invocation_path") or ""))
    if (
        str(ps_path) != "/bin/ps"
        or not ps_path.is_file()
        or str(ps_path.resolve(strict=True)) != ps_binding.get("resolved_path")
        or sha256_file(ps_path) != ps_binding.get("sha256")
        or ps_path.stat().st_size != ps_binding.get("size_bytes")
    ):
        raise RepairPipelineError("bound /bin/ps path/bytes changed")
    monitor = concurrency.get("monitor_implementation")
    if monitor != (prelock.get("repair_tool_bindings") or {}).get("repair_runner"):
        raise RepairPipelineError("concurrency monitor implementation is not the frozen repair runner")
    verify_file_binding(monitor, "concurrency monitor implementation", inside_candidate=True)
    if concurrency.get("outer_wrapper_invocation") != monitor:
        raise RepairPipelineError("outer wrapper invocation is not the frozen repair runner")
    drafter_path = verify_file_binding(
        concurrency.get("frozen_drafter"), "concurrency frozen drafter", inside_candidate=True
    )
    prompt_path = verify_file_binding(
        config.get("repair_prompt"), "concurrency repair prompt", inside_candidate=True
    )
    expected_attempts = concurrency.get("expected_case_attempts")
    if (
        not isinstance(expected_attempts, list)
        or prelock["repair_count"] != 80
        or len(expected_attempts) != 80
        or concurrency.get("expected_case_attempts_sha256") != object_sha256(expected_attempts)
    ):
        raise RepairPipelineError("concurrency expected-case index is invalid")
    repair_by_case = {row["case_unit_id"]: row for row in prelock["repair_inputs"]}
    output_root_for_audit = resolve_repo_path(config["output_root"], inside_candidate=True)
    for execution_rank, (item, plan_row) in enumerate(
        zip(expected_attempts, orders["repair_execution_plan"], strict=True)
    ):
        case_id = item.get("case_unit_id")
        if case_id not in repair_by_case:
            raise RepairPipelineError("concurrency expected-case index has an unknown case")
        if set(item) != {
            "execution_rank",
            "execution_lane",
            "selection_rank",
            "case_unit_id",
            "task_id",
            "case_packet_path",
            "case_output_dir",
            "allowed_process_commands",
            "allowed_process_commands_sha256",
            "allowed_commands_are_prelock_hash_templates",
            "allowed_ps_command_line_sha256",
        }:
            raise RepairPipelineError(f"{case_id} concurrency expected row fields differ")
        packet_path = verify_file_binding(
            repair_by_case[case_id]["bindings"]["batch_packet"],
            f"{case_id} concurrency packet",
            inside_candidate=True,
        )
        if (
            item.get("execution_rank") != execution_rank
            or item.get("execution_rank") != plan_row["execution_rank"]
            or item.get("execution_lane") != plan_row["lane"]
            or case_id != plan_row["case_unit_id"]
            or item.get("selection_rank") != repair_by_case[case_id]["selection_rank"]
            or item.get("selection_rank") != plan_row["selection_rank"]
            or item.get("task_id") != case_id
            or item.get("case_packet_path") != str(packet_path)
            or item.get("case_output_dir") != str((output_root_for_audit / case_id).resolve())
            or item.get("allowed_commands_are_prelock_hash_templates") is not True
        ):
            raise RepairPipelineError(f"{case_id} concurrency expected command binding differs")
        reconstructed = reconstruct_expected_attempt_commands(
            config=config,
            item=item,
            runtime=runtime,
            drafter_path=drafter_path,
            prompt_path=prompt_path,
        )
        if (
            item.get("allowed_process_commands") != reconstructed
            or item.get("allowed_process_commands_sha256") != object_sha256(reconstructed)
            or item.get("allowed_ps_command_line_sha256")
            != [row["ps_command_line_sha256"] for row in reconstructed]
        ):
            raise RepairPipelineError(f"{case_id} allowed drafter commands differ")
    supersession = config.get("supersession_incident")
    if supersession != ((prelock.get("supersedes") or {}).get("incident")):
        raise RepairPipelineError("supersession incident differs across config/prelock")
    incident_path = verify_file_binding(
        supersession, "repair supersession incident", inside_candidate=True
    )
    incident = load_json(incident_path, "repair supersession incident")
    verify_internal_hash(incident, ("incident_sha256",), "repair supersession incident")
    if (
        incident.get("status") != "aborted_before_first_repair_model_call"
        or incident.get("promotion_forbidden") is not True
        or incident.get("model_calls_started") is not False
        or incident.get("incident_sha256") != supersession.get("incident_sha256")
    ):
        raise RepairPipelineError("repair supersession incident no longer proves pre-call abort")
    automatic_qc = prelock.get("automatic_qc") or {}
    summary_path = verify_file_binding(
        automatic_qc.get("summary"), "automatic QC summary", inside_candidate=True
    )
    summary = load_json(summary_path, "automatic QC summary")
    verify_internal_hash(summary, ("summary_sha256",), "automatic QC summary")
    if (
        summary.get("summary_sha256") != automatic_qc["summary"].get("summary_sha256")
        or automatic_qc.get("passed_count") != 72
        or automatic_qc.get("failed_count") != 44
    ):
        raise RepairPipelineError("automatic QC summary binding/counts changed")
    report_index = automatic_qc.get("report_index")
    if (
        not isinstance(report_index, list)
        or len(report_index) != 116
        or automatic_qc.get("report_index_sha256") != object_sha256(report_index)
    ):
        raise RepairPipelineError("automatic QC complete report index is invalid")
    for rank, row in enumerate(report_index):
        case_id = prelock["case_order"][rank]
        if row.get("selection_rank") != rank or row.get("case_unit_id") != case_id:
            raise RepairPipelineError(f"automatic QC report index row {rank} identity differs")
        for field in ("report", "checklist", "packet"):
            bound_path = verify_file_binding(
                row.get(field), f"automatic QC row {rank} {field}", inside_candidate=True
            )
            if field == "report":
                report = load_json(bound_path, f"automatic QC row {rank} report")
                if (
                    report.get("schema_version") != "androidworld_checklist_automatic_qc/v2"
                    or report.get("case_unit_id") != case_id
                    or report.get("task_id") != case_id
                    or report.get("selection_rank") != rank
                    or report.get("status") != row.get("status")
                    or not isinstance(report.get("checks"), Mapping)
                    or set(report["checks"]) != AUTOMATIC_QC_CHECK_KEYS
                    or any(not isinstance(value, bool) for value in report["checks"].values())
                ):
                    raise RepairPipelineError(f"automatic QC report {case_id} strict fields differ")
    verify_readonly_window_static(config, prelock)
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
    observed_source_context = verify_source_context_freeze(source)
    if observed_source_context != (prelock.get("source_draft") or {}).get(
        "packet_source_context_freeze"
    ):
        raise RepairPipelineError("packet/source context freeze differs from repair prelock")
    source_wave_path, _ = verify_source_wave_complete(source)
    selection_path = verify_file_binding(
        prelock.get("audit_selection"), "repair audit selection", inside_candidate=True
    )
    reconstructed = verify_selection_reconstructed_from_bound_sources(
        selection_path,
        source=source,
        wave=source_wave_path,
        qc_root=summary_path.parent,
    )
    if reconstructed.get("selection_sha256") != prelock["audit_selection"].get(
        "selection_sha256"
    ):
        raise RepairPipelineError("reconstructed repair selection hash differs from prelock")
    _, reconstructed_rows = load_audit_selection(
        selection_path,
        case_order=list(source["case_order"]),
        automatic_qc_root=summary_path.parent,
    )
    if object_sha256(reconstructed_rows) != prelock.get("audit_rows_sha256"):
        raise RepairPipelineError("reconstructed 116 audit rows differ from repair prelock")
    for row in prelock["repair_inputs"]:
        verify_binding_tree(row["bindings"], f"{row['case_unit_id']} repair inputs")
        descriptor_path = verify_file_binding(row["descriptor"], f"{row['case_unit_id']} descriptor", inside_candidate=True)
        descriptor = load_json(descriptor_path, f"{row['case_unit_id']} descriptor")
        verify_internal_hash(descriptor, ("descriptor_sha256",), f"{row['case_unit_id']} descriptor")
        if descriptor.get("descriptor_sha256") != row["descriptor"].get("descriptor_sha256"):
            raise RepairPipelineError(f"{row['case_unit_id']} descriptor internal hash differs")
    verify_attempt_namespace_contract(
        config,
        prelock,
        require_absent=require_attempt_root_absent,
        claim=attempt_claim,
    )
    if (
        concurrency.get("appworld_v56_runtime_gate") is not False
        or concurrency.get("attempt_namespace_sha256")
        != (config.get("attempt_namespace") or {}).get(
            "attempt_namespace_sha256"
        )
    ):
        raise RepairPipelineError("attempt namespace/concurrency binding differs")
    return prelock, config, source


def archive_existing(attempt_root: Path, prelock: Mapping[str, Any]) -> Path:
    if not attempt_root.exists():
        raise RepairPipelineError("--restart-after-incident was supplied but no prior attempt exists")
    if attempt_root.is_symlink() or not attempt_root.is_dir():
        raise RepairPipelineError("restart target is not a real attempt-root directory")
    record = tree_record(attempt_root)
    incident_id = f"{utc_now().replace(':', '').replace('+', '_')}_{record['tree_sha256'][:12]}"
    incident_root = WORK_ROOT / "repair_generation" / "incidents" / prelock["repair_id"] / incident_id
    if incident_root.exists():
        raise RepairPipelineError(f"incident archive already exists: {incident_root}")
    incident_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(attempt_root), str(incident_root))
    incident = {
        "schema_version": "androidworld_checklist_repair_restart_incident/v1",
        "created_at": utc_now(),
        "repair_id": prelock["repair_id"],
        "status": "archived_failed_or_incomplete_attempt",
        "promotion_forbidden": True,
        "original_attempt_root": repo_relative(attempt_root),
        "archived_entire_attempt_root": True,
        "archived_tree": record | {"archived_path": repo_relative(incident_root)},
        "repair_prelock_sha256": prelock["prelock_sha256"],
    }
    incident = add_self_hash(incident, "incident_sha256")
    write_json_create_once(incident_root / "_restart_incident.json", incident)
    return incident_root


def command_for(
    config: Mapping[str, Any], prelock: Mapping[str, Any], prelock_path: Path
) -> list[str]:
    runner = verify_file_binding(config["frozen_batch_runner"], "frozen v3 batch runner", inside_candidate=True)
    prompt = verify_file_binding(config["repair_prompt"], "repair prompt", inside_candidate=True)
    packet_root = resolve_repo_path(config["packet_set_root"], inside_candidate=True)
    output_root = resolve_repo_path(config["output_root"], inside_candidate=True)
    runtime = verify_python_runtime_binding(
        config.get("python_runtime"), "prelocked Python runtime before command"
    )
    target_args = [
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
    if "--appworld-v56-runtime-gate" in target_args:
        raise RepairPipelineError("AndroidWorld command enabled the AppWorld-only gate")
    exact_trees = config.get("snapshot_exact_trees") or {}
    template = isolated_bootstrap_command(
        runtime=runtime,
        prelock_path=prelock_path,
        prelock_file_sha256=PRELOCK_FILE_SHA256_PLACEHOLDER,
        prelock_internal_sha256=PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
        repair_tree_sha256=str((exact_trees.get("repair") or {}).get("descriptor_sha256") or ""),
        source_tree_sha256=str((exact_trees.get("source_v3") or {}).get("descriptor_sha256") or ""),
        runtime_source_tree_sha256=str(
            (exact_trees.get("runtime_source") or {}).get("descriptor_sha256") or ""
        ),
        mode="batch",
        target=runner,
        target_args=target_args,
    )
    if template != config.get("runner_command"):
        raise RepairPipelineError("reconstructed runner template differs from prelocked command")
    if "--appworld-v56-runtime-gate" in template:
        raise RepairPipelineError("prelocked AndroidWorld runner contains AppWorld-only flag")
    if object_sha256(template) != config.get("runner_command_sha256"):
        raise RepairPipelineError("reconstructed runner command hash differs from prelock")
    if template != (prelock.get("runner_execution") or {}).get("command"):
        raise RepairPipelineError("reconstructed runner command differs from prelock execution record")
    return expand_prelock_sha256(
        template,
        file_sha256=sha256_file(prelock_path),
        internal_sha256=str(prelock.get("prelock_sha256") or ""),
    )


def reconstruct_expected_attempt_commands(
    *,
    config: Mapping[str, Any],
    item: Mapping[str, Any],
    runtime: Mapping[str, Any],
    drafter_path: Path,
    prompt_path: Path,
) -> list[dict[str, Any]]:
    packet_path = Path(str(item["case_packet_path"]))
    output_dir = Path(str(item["case_output_dir"]))
    is_oversized = packet_path.stat().st_size > REPAIR_LARGE_CASE_THRESHOLD_BYTES
    http_timeout = 480 if is_oversized else 180
    codex_timeout = (
        config["large_codex_timeout_seconds"]
        if is_oversized
        else config["codex_timeout_seconds"]
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
        exact_trees = config.get("snapshot_exact_trees") or {}
        command = isolated_bootstrap_command(
            runtime=runtime,
            prelock_path=resolve_repo_path(
                config.get("repair_prelock_path"), inside_candidate=True
            ),
            prelock_file_sha256=PRELOCK_FILE_SHA256_PLACEHOLDER,
            prelock_internal_sha256=PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
            repair_tree_sha256=str(
                (exact_trees.get("repair") or {}).get("descriptor_sha256") or ""
            ),
            source_tree_sha256=str(
                (exact_trees.get("source_v3") or {}).get("descriptor_sha256") or ""
            ),
            runtime_source_tree_sha256=str(
                (exact_trees.get("runtime_source") or {}).get("descriptor_sha256")
                or ""
            ),
            mode="script",
            target=drafter_path,
            target_args=target_args,
        )
        if any(any(character.isspace() for character in argument) for argument in command):
            raise RepairPipelineError("process audit argv unexpectedly contains whitespace")
        rows.append(
            {
                "attempt_index": attempt_index,
                "max_output_tokens": token_budget,
                "lane": "oversized" if is_oversized else "regular",
                "http_timeout_seconds": http_timeout,
                "codex_timeout_seconds": codex_timeout,
                "command": command,
                "command_sha256": object_sha256(command),
                "ps_command_line_sha256": object_sha256(" ".join(command)),
            }
        )
    return rows


def expanded_expected_case_attempts(
    expected: list[Mapping[str, Any]], prelock: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Expand the two prelock-hash placeholders for live process observation."""

    if not expected:
        return []
    file_sha256 = getattr(
        sys, "_androidworld_isolated_bootstrap_prelock_file_sha256", None
    )
    internal_sha256 = str(prelock.get("prelock_sha256") or "")
    if not isinstance(file_sha256, str):
        raise RepairPipelineError("physical prelock admission is missing")
    result: list[dict[str, Any]] = []
    for item in expected:
        row = dict(item)
        expanded_commands: list[dict[str, Any]] = []
        for raw in item.get("allowed_process_commands") or []:
            command_row = dict(raw)
            command = expand_prelock_sha256(
                list(command_row.get("command") or []),
                file_sha256=file_sha256,
                internal_sha256=internal_sha256,
            )
            command_row["command"] = command
            command_row["command_sha256"] = object_sha256(command)
            command_row["ps_command_line_sha256"] = object_sha256(" ".join(command))
            expanded_commands.append(command_row)
        row["allowed_process_commands"] = expanded_commands
        row["allowed_process_commands_sha256"] = object_sha256(expanded_commands)
        row["allowed_ps_command_line_sha256"] = [
            command["ps_command_line_sha256"] for command in expanded_commands
        ]
        row["allowed_commands_are_prelock_hash_templates"] = False
        result.append(row)
    return result


def parse_ps_rows(output: str) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for line_number, line in enumerate(output.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 3)
        if len(parts) < 3:
            raise RepairPipelineError(f"/bin/ps row {line_number} lacks pid/ppid/pgid")
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
            pgid = int(parts[2])
        except ValueError as exc:
            raise RepairPipelineError(f"/bin/ps row {line_number} has invalid pid/ppid") from exc
        if pid <= 0 or ppid < 0 or pgid < 0 or pid in rows:
            raise RepairPipelineError(f"/bin/ps row {line_number} has duplicate/invalid pid")
        rows[pid] = {
            "pid": pid,
            "ppid": ppid,
            "pgid": pgid,
            "command": parts[3] if len(parts) == 4 else "",
        }
    if not rows:
        raise RepairPipelineError("/bin/ps returned no process rows")
    return rows


def observe_process_rows(audit: Mapping[str, Any], label: str) -> dict[int, dict[str, Any]]:
    observed = subprocess.run(
        list(audit["ps_command"]),
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if observed.returncode != 0:
        raise RepairPipelineError(
            f"{label} /bin/ps returned {observed.returncode}: {observed.stderr.strip()}"
        )
    return parse_ps_rows(observed.stdout)


def process_group_members(
    rows: Mapping[int, Mapping[str, Any]], process_group_id: int
) -> list[dict[str, Any]]:
    return [
        {
            "pid": int(pid),
            "ppid": int(row["ppid"]),
            "pgid": int(row["pgid"]),
            "command_sha256": object_sha256(str(row.get("command") or "")),
        }
        for pid, row in sorted(rows.items())
        if int(row.get("pgid", -1)) == process_group_id
    ]


def descendant_pids(rows: Mapping[int, Mapping[str, Any]], parent_pid: int) -> set[int]:
    descendants = {parent_pid}
    changed = True
    while changed:
        changed = False
        for pid, row in rows.items():
            if pid not in descendants and row.get("ppid") in descendants:
                descendants.add(pid)
                changed = True
    descendants.discard(parent_pid)
    return descendants


def ancestor_pids(rows: Mapping[int, Mapping[str, Any]], child_pid: int) -> set[int]:
    """Return the complete visible ancestor chain, excluding the child itself."""

    ancestors: set[int] = set()
    current = child_pid
    while current in rows:
        parent = int(rows[current].get("ppid", 0))
        if parent <= 0 or parent == current or parent in ancestors:
            break
        ancestors.add(parent)
        current = parent
    return ancestors


def foreign_drafting_processes(
    rows: Mapping[int, Mapping[str, Any]],
    *,
    patterns: list[str],
    excluded_pids: set[int],
) -> list[dict[str, Any]]:
    foreign: list[dict[str, Any]] = []
    for pid, row in sorted(rows.items()):
        if pid in excluded_pids:
            continue
        command = str(row.get("command") or "")
        try:
            argv = shlex.split(command, posix=True)
        except ValueError:
            argv = command.split()
        matched: list[str] = []
        if len(argv) >= 2:
            executable = Path(argv[0]).name
            second = Path(argv[1]).name
            if executable.startswith("python") and second in {
                "run_checklist_repair_batch.py",
                "run_draft_batch.py",
                "draft_case_checklist.py",
            }:
                matched.append(second)
            if executable.startswith("python") and argv[1:4] == ["-I", "-S", "-c"]:
                # Exact isolated-bootstrap layout after the opaque -c payload:
                # prelock, physical hash, internal hash, three tree hashes,
                # mode, target, --, target argv...
                if len(argv) >= 14 and argv[13] == "--":
                    mode = argv[11]
                    target = Path(argv[12]).name
                    if mode == "outer" and target == "run_checklist_repair_batch.py":
                        matched.append("run_checklist_repair_batch.py")
                    if mode == "batch" and target == "run_draft_batch.py":
                        matched.append("run_draft_batch.py")
                    if mode == "script" and target == "draft_case_checklist.py":
                        matched.append("draft_case_checklist.py")
                else:
                    # A malformed isolated Python command mentioning a drafting
                    # target remains foreign; layout corruption is never an
                    # evasion primitive.
                    for target in (
                        "run_checklist_repair_batch.py",
                        "run_draft_batch.py",
                        "draft_case_checklist.py",
                    ):
                        if any(Path(argument).name == target for argument in argv[4:]):
                            matched.append(target)
            if executable == "codex" and argv[1] == "exec":
                matched.append("codex exec")
        matched = sorted({value for value in matched if value in patterns})
        if matched:
            foreign.append(
                {
                    "pid": pid,
                    "ppid": int(row["ppid"]),
                    "pgid": int(row["pgid"]),
                    "matched_patterns": matched,
                    "command_sha256": object_sha256(command),
                }
            )
    return foreign


def foreign_drafting_preflight(config: Mapping[str, Any]) -> dict[str, Any]:
    audit = config["concurrency_audit"]
    observed = subprocess.run(
        list(audit["ps_command"]),
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if observed.returncode != 0:
        raise RepairPipelineError(
            f"foreign-process preflight /bin/ps returned {observed.returncode}"
        )
    rows = parse_ps_rows(observed.stdout)
    excluded = ancestor_pids(rows, os.getpid()) | {os.getpid()}
    foreign = foreign_drafting_processes(
        rows,
        patterns=list(audit["foreign_process_patterns"]),
        excluded_pids=excluded,
    )
    record = {
        "schema_version": "androidworld_checklist_repair_foreign_process_preflight/v1",
        "captured_at": utc_now(),
        "monotonic_ns": time.monotonic_ns(),
        "ps_binary": audit["ps_binary"],
        "ps_command": audit["ps_command"],
        "patterns": audit["foreign_process_patterns"],
        "excluded_runner_pid": os.getpid(),
        "excluded_runner_ancestor_pids": sorted(excluded - {os.getpid()}),
        "foreign_processes": foreign,
        "foreign_process_count": len(foreign),
        "status": "pass" if not foreign else "fail",
        "binding_policy": "foreign drafting processes must be absent before batch launch",
    }
    record = add_self_hash(record, "preflight_sha256")
    if foreign:
        raise RepairPipelineError(
            f"foreign drafting processes are active; wait before repair run: {foreign}"
        )
    return record


def immediate_foreign_drafting_preflight(
    config: Mapping[str, Any],
    *,
    early_foreign_preflight: Mapping[str, Any],
    deterministic_generation_preflight: Mapping[str, Any],
    attempt_claim: Mapping[str, Any],
) -> dict[str, Any]:
    """Capture final foreign-process absence inside the signal/Popen barrier."""

    verify_internal_hash(
        early_foreign_preflight,
        ("preflight_sha256",),
        "early foreign-process preflight",
    )
    verify_internal_hash(
        deterministic_generation_preflight,
        ("generation_preflight_sha256",),
        "deterministic generation preflight",
    )
    verify_internal_hash(attempt_claim, ("claim_sha256",), "attempt-root claim")
    audit = config["concurrency_audit"]
    rows = observe_process_rows(audit, "immediate pre-Popen foreign preflight")
    excluded = ancestor_pids(rows, os.getpid()) | {os.getpid()}
    foreign = foreign_drafting_processes(
        rows,
        patterns=list(audit["foreign_process_patterns"]),
        excluded_pids=excluded,
    )
    record = {
        "schema_version": (
            "androidworld_checklist_repair_immediate_foreign_preflight/v1"
        ),
        "phase": "after_attempt_root_claim_inside_signal_block_before_batch_popen",
        "captured_at": utc_now(),
        "monotonic_ns": time.monotonic_ns(),
        "ps_binary": audit["ps_binary"],
        "ps_command": audit["ps_command"],
        "patterns": audit["foreign_process_patterns"],
        "excluded_runner_pid": os.getpid(),
        "excluded_runner_ancestor_pids": sorted(excluded - {os.getpid()}),
        "foreign_processes": foreign,
        "foreign_process_count": len(foreign),
        "status": "pass" if not foreign else "fail",
        "early_foreign_preflight_sha256": early_foreign_preflight[
            "preflight_sha256"
        ],
        "deterministic_generation_preflight_sha256": (
            deterministic_generation_preflight["generation_preflight_sha256"]
        ),
        "attempt_root_claim_sha256": attempt_claim["claim_sha256"],
        "popen_must_not_occur_if_nonzero": True,
        "binding_policy": (
            "after the exclusive attempt-root claim, layout creation, and every deterministic "
            "tree/runtime recheck while wrapper signals are blocked, require a fresh /bin/ps "
            "observation with zero foreign drafting processes; batch Popen is the immediately "
            "following state-changing operation"
        ),
    }
    return add_self_hash(record, "immediate_preflight_sha256")


def finalize_generation_launch_preflight(
    deterministic: Mapping[str, Any],
    immediate: Mapping[str, Any],
    attempt_claim: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind the deterministic token and final foreign absence into one launch token."""

    verify_internal_hash(
        deterministic,
        ("generation_preflight_sha256",),
        "deterministic generation preflight",
    )
    verify_internal_hash(
        immediate,
        ("immediate_preflight_sha256",),
        "immediate foreign-process preflight",
    )
    verify_internal_hash(attempt_claim, ("claim_sha256",), "attempt-root claim")
    if (
        immediate.get("status") != "pass"
        or immediate.get("foreign_process_count") != 0
        or immediate.get("foreign_processes") != []
        or immediate.get("deterministic_generation_preflight_sha256")
        != deterministic.get("generation_preflight_sha256")
        or immediate.get("attempt_root_claim_sha256")
        != attempt_claim.get("claim_sha256")
    ):
        raise ImmediateForeignPreflightFailure(immediate)
    return add_self_hash(
        {
            "schema_version": (
                "androidworld_checklist_repair_generation_launch_preflight/v2"
            ),
            "created_at": utc_now(),
            "monotonic_ns": time.monotonic_ns(),
            "status": "pass",
            "core": deterministic["core"],
            "core_sha256": deterministic["core_sha256"],
            "deterministic_preflight": dict(deterministic),
            "deterministic_preflight_sha256": deterministic[
                "generation_preflight_sha256"
            ],
            "immediate_foreign_preflight": dict(immediate),
            "immediate_foreign_preflight_sha256": immediate[
                "immediate_preflight_sha256"
            ],
            "attempt_root_claim": dict(attempt_claim),
            "attempt_root_claim_sha256": attempt_claim["claim_sha256"],
            "popen_is_next_state_changing_operation": True,
        },
        "generation_preflight_sha256",
    )


def _creatable_parent_record(target: Path) -> dict[str, Any]:
    """Prove a target has a writable/searchable existing ancestor without creating it."""

    target = Path(os.path.abspath(target))
    ancestor = target.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        raise RepairPipelineError(f"no existing directory ancestor for generation target: {target}")
    writable = os.access(ancestor, os.W_OK)
    searchable = os.access(ancestor, os.X_OK)
    if not writable or not searchable:
        raise RepairPipelineError(
            f"generation target parent is not writable/searchable: {target} via {ancestor}"
        )
    metadata = ancestor.stat()
    return {
        "target": str(target),
        "nearest_existing_ancestor": str(ancestor.resolve(strict=True)),
        "ancestor_mode": metadata.st_mode,
        "ancestor_uid": metadata.st_uid,
        "ancestor_gid": metadata.st_gid,
        "writable": writable,
        "searchable": searchable,
    }


def _generation_preflight_core(
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    command: list[str],
    environment: Mapping[str, str],
    readonly_preflight_record: Mapping[str, Any],
    foreign_preflight: Mapping[str, Any],
    codex_auth_pre: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute every deterministic launch gate without writing any artifact."""

    orders = verify_repair_order_bindings(prelock, "generation preflight")
    command_template = config.get("runner_command")
    prelock_file_sha256 = getattr(
        sys, "_androidworld_isolated_bootstrap_prelock_file_sha256", None
    )
    if not isinstance(command_template, list) or not isinstance(prelock_file_sha256, str):
        raise RepairPipelineError("generation runner template/admission is missing")
    expanded_command = expand_prelock_sha256(
        command_template,
        file_sha256=prelock_file_sha256,
        internal_sha256=str(prelock.get("prelock_sha256") or ""),
    )
    if (
        object_sha256(command_template) != config.get("runner_command_sha256")
        or command != expanded_command
    ):
        raise RepairPipelineError(
            "generation execution command differs from expanded frozen runner template"
        )
    exact_trees = config.get("snapshot_exact_trees") or {}
    if set(exact_trees) != {"repair", "source_v3", "runtime_source"}:
        raise RepairPipelineError("generation exact-tree set is invalid")
    for name in ("repair", "source_v3", "runtime_source"):
        verify_exact_snapshot_tree_descriptor(
            exact_trees[name], f"generation immediate {name} snapshot"
        )
    verify_python_runtime_binding(
        config.get("python_runtime"), "generation immediate Python runtime"
    )
    verify_runtime_source_snapshot_binding(
        config.get("runtime_source_snapshot"),
        "generation immediate runtime source snapshot",
        runtime=config.get("python_runtime"),
        repair_exact_tree=exact_trees["repair"],
        runtime_source_exact_tree=exact_trees["runtime_source"],
    )
    if (
        foreign_preflight.get("status") != "pass"
        or foreign_preflight.get("foreign_process_count") != 0
        or foreign_preflight.get("foreign_processes") != []
    ):
        raise RepairPipelineError("generation preflight lacks fail-closed foreign-process absence")
    verify_internal_hash(
        foreign_preflight,
        ("preflight_sha256",),
        "generation foreign-process preflight",
    )
    verify_internal_hash(
        readonly_preflight_record,
        ("preflight_sha256",),
        "generation read-only preflight",
    )
    required_environment = verify_closed_child_environment(
        config["runner_environment"], "generation child environment contract"
    )
    forbidden = list(config["python_runtime"]["forbidden_child_python_environment"])
    if dict(environment) != required_environment:
        raise RepairPipelineError(
            "generation child environment is not exact key-set/value equality"
        )
    if any(key in environment for key in forbidden):
        raise RepairPipelineError("generation child environment contains a forbidden Python variable")
    audit = config["concurrency_audit"]
    if (
        config.get("runner_environment_sha256")
        != object_sha256(required_environment)
        or audit.get("runner_environment") != required_environment
        or audit.get("runner_environment_sha256")
        != object_sha256(required_environment)
    ):
        raise RepairPipelineError("generation environment hash chain differs")
    attempt_root, attempt_layout = verify_attempt_namespace_contract(
        config, prelock, require_absent=True
    )
    output_root = resolve_repo_path(config["output_root"], inside_candidate=True)
    absent_targets = [attempt_root]
    existing = [str(path) for path in absent_targets if path.exists()]
    if existing:
        raise RepairPipelineError(f"generation preflight output/evidence already exists: {existing}")
    parent_records = [_creatable_parent_record(path) for path in absent_targets]
    packet_root = resolve_repo_path(config["packet_set_root"], inside_candidate=True)
    observed_packet_dirs = sorted(
        path.name for path in packet_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    expected_case_set = sorted(orders["repair_execution_order"])
    if observed_packet_dirs != expected_case_set:
        raise RepairPipelineError("generation packet-root case set differs from frozen repair set")
    expected_attempts = list(audit["expected_case_attempts"])
    if (
        len(expected_attempts) != len(orders["repair_execution_plan"])
        or [item.get("case_unit_id") for item in expected_attempts]
        != orders["repair_execution_order"]
        or [item.get("execution_rank") for item in expected_attempts]
        != list(range(len(expected_attempts)))
        or audit.get("expected_case_attempts_sha256") != object_sha256(expected_attempts)
    ):
        raise RepairPipelineError("generation expected-attempt set/order differs from frozen plan")
    for item, plan_row in zip(
        expected_attempts, orders["repair_execution_plan"], strict=True
    ):
        case_id = plan_row["case_unit_id"]
        packet_path = Path(str(item["case_packet_path"]))
        if (
            item.get("execution_lane") != plan_row["lane"]
            or packet_path != (packet_root / case_id / "case_packet.md").resolve()
            or not packet_path.is_file()
            or Path(str(item["case_output_dir"])) != (output_root / case_id).resolve()
            or Path(str(item["case_output_dir"])).exists()
        ):
            raise RepairPipelineError(f"{case_id} generation packet/output preflight differs")
    frozen_bindings = {
        "batch_runner": config["frozen_batch_runner"],
        "drafter": audit["frozen_drafter"],
        "repair_prompt": config["repair_prompt"],
        "outer_wrapper": audit["outer_wrapper_invocation"],
    }
    for role, binding in frozen_bindings.items():
        verify_file_binding(binding, f"generation preflight frozen {role}", inside_candidate=True)
    return {
        "repair_id": prelock["repair_id"],
        "repair_prelock_sha256": prelock["prelock_sha256"],
        "repair_config_sha256": config["config_sha256"],
        "runner_command_template_sha256": config["runner_command_sha256"],
        "runner_execution_command_sha256": object_sha256(command),
        "prelock_file_sha256_anchor": prelock_file_sha256,
        "prelock_internal_sha256_anchor": prelock["prelock_sha256"],
        "snapshot_exact_tree_hashes": {
            name: descriptor["descriptor_sha256"]
            for name, descriptor in config["snapshot_exact_trees"].items()
        },
        "isolated_bootstrap_sha256": object_sha256(config["isolated_bootstrap"]),
        "python_runtime_sha256": object_sha256(config["python_runtime"]),
        "runtime_source_snapshot_sha256": config[
            "runtime_source_snapshot_sha256"
        ],
        "candidate_case_order_sha256": prelock["candidate_case_order_sha256"],
        "repair_selection_order_sha256": prelock["repair_selection_order_sha256"],
        "repair_execution_order_sha256": prelock["repair_execution_order_sha256"],
        "repair_execution_plan_sha256": prelock["repair_execution_plan_sha256"],
        "expected_case_attempts_sha256": audit["expected_case_attempts_sha256"],
        "expected_case_count": len(expected_attempts),
        "expected_case_ids": orders["repair_execution_order"],
        "packet_root": str(packet_root),
        "attempt_root": str(attempt_root),
        "attempt_layout": {
            role: str(attempt_layout[role]) for role in ATTEMPT_LAYOUT_ROLES
        },
        "attempt_namespace_sha256": config["attempt_namespace"][
            "attempt_namespace_sha256"
        ],
        "output_root": str(output_root),
        "absent_targets": [str(path) for path in absent_targets],
        "creatable_parent_records": parent_records,
        "frozen_bindings": frozen_bindings,
        "required_environment": required_environment,
        "required_environment_sha256": object_sha256(required_environment),
        "forbidden_environment_absent": forbidden,
        "readonly_preflight_sha256": readonly_preflight_record["preflight_sha256"],
        "foreign_process_preflight_sha256": foreign_preflight["preflight_sha256"],
        "codex_auth_pre_sha256": object_sha256(dict(codex_auth_pre)),
        "no_files_created_by_preflight": True,
    }


def deterministic_generation_preflight(
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    command: list[str],
    environment: Mapping[str, str],
    readonly_preflight_record: Mapping[str, Any],
    foreign_preflight: Mapping[str, Any],
    codex_auth_pre: Mapping[str, Any],
) -> dict[str, Any]:
    core = _generation_preflight_core(
        config=config,
        prelock=prelock,
        command=command,
        environment=environment,
        readonly_preflight_record=readonly_preflight_record,
        foreign_preflight=foreign_preflight,
        codex_auth_pre=codex_auth_pre,
    )
    return add_self_hash(
        {
            "schema_version": "androidworld_checklist_repair_generation_preflight/v1",
            "created_at": utc_now(),
            "monotonic_ns": time.monotonic_ns(),
            "status": "pass",
            "core": core,
            "core_sha256": object_sha256(core),
        },
        "generation_preflight_sha256",
    )


def verify_generation_preflight_record(
    record: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    command: list[str],
    environment: Mapping[str, str],
    readonly_preflight_record: Mapping[str, Any],
    foreign_preflight: Mapping[str, Any],
    codex_auth_pre: Mapping[str, Any],
) -> None:
    if (
        not isinstance(record, Mapping)
        or record.get("schema_version")
        != "androidworld_checklist_repair_generation_preflight/v1"
        or record.get("status") != "pass"
    ):
        raise RepairPipelineError("valid generation-preflight pass token is required before Popen")
    verify_internal_hash(
        record,
        ("generation_preflight_sha256",),
        "generation preflight token",
    )
    core = _generation_preflight_core(
        config=config,
        prelock=prelock,
        command=command,
        environment=environment,
        readonly_preflight_record=readonly_preflight_record,
        foreign_preflight=foreign_preflight,
        codex_auth_pre=codex_auth_pre,
    )
    if record.get("core") != core or record.get("core_sha256") != object_sha256(core):
        raise RepairPipelineError("generation preflight token differs at immediate pre-Popen recheck")


def active_case_attempts(
    rows: Mapping[int, Mapping[str, Any]],
    *,
    batch_pid: int,
    drafter_path: str,
    expected: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    descendants = descendant_pids(rows, batch_pid)
    # Also inspect drafter-shaped members of our dedicated PGID even if their
    # parent linkage is wrong, so a reparented/spoofed row fails explicitly
    # instead of disappearing from coverage accounting.
    candidates = descendants | {
        pid
        for pid, row in rows.items()
        if int(row.get("pgid", -1)) == batch_pid
        and drafter_path in str(row.get("command") or "")
    }
    active: list[dict[str, Any]] = []
    observed_cases: set[str] = set()
    for pid in sorted(candidates):
        row = rows[pid]
        command = str(row.get("command") or "")
        if drafter_path not in command:
            continue
        matches = [
            item
            for item in expected
            if str(item["case_packet_path"]) in command
            and str(item["case_output_dir"]) in command
        ]
        if len(matches) != 1:
            raise RepairPipelineError(
                f"drafter descendant pid={pid} does not match exactly one bound repair case"
            )
        case_id = str(matches[0]["case_unit_id"])
        command_sha256 = object_sha256(command)
        allowed = list(matches[0].get("allowed_ps_command_line_sha256") or [])
        if command_sha256 not in allowed:
            raise RepairPipelineError(
                f"drafter descendant pid={pid} command hash is not a prelocked attempt for {case_id}"
            )
        if int(row.get("pgid", -1)) != batch_pid:
            raise RepairPipelineError(
                f"drafter descendant pid={pid} is outside prelocked batch process group"
            )
        if int(row.get("ppid", -1)) != batch_pid:
            raise RepairPipelineError(
                f"drafter descendant pid={pid} is not a direct child of the frozen batch runner"
            )
        if case_id in observed_cases:
            raise RepairPipelineError(f"multiple concurrent drafter processes for case {case_id}")
        observed_cases.add(case_id)
        active.append(
            {
                "pid": pid,
                "ppid": int(row["ppid"]),
                "pgid": int(row["pgid"]),
                "case_unit_id": case_id,
                "execution_rank": int(matches[0]["execution_rank"]),
                "execution_lane": str(matches[0]["execution_lane"]),
                "selection_rank": int(matches[0]["selection_rank"]),
                "command_sha256": command_sha256,
                "drafter_path": drafter_path,
                "case_packet_path": str(matches[0]["case_packet_path"]),
                "case_output_dir": str(matches[0]["case_output_dir"]),
                "expected_attempt_sha256": object_sha256(matches[0]),
            }
        )
    return sorted(active, key=lambda item: (item["execution_rank"], item["pid"]))


class AuditedRepairRunFailure(RepairPipelineError):
    """An after-Popen failure with mandatory process-group cleanup evidence."""

    def __init__(
        self,
        cause: BaseException,
        *,
        batch_pid: int,
        cleanup_event: Mapping[str, Any],
        process_group_postflight: Mapping[str, Any],
        generation_preflight: Mapping[str, Any],
        attempt_lease: AttemptRootLease,
        wrapper_signal: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(f"post-Popen repair wrapper failure: {type(cause).__name__}: {cause}")
        self.cause = cause
        self.batch_pid = batch_pid
        self.cleanup_event = dict(cleanup_event)
        self.process_group_postflight = dict(process_group_postflight)
        self.generation_preflight = dict(generation_preflight)
        self.attempt_lease = attempt_lease
        self.wrapper_signal = dict(wrapper_signal) if wrapper_signal else None


class RunNamespaceClaimError(RepairPipelineError):
    """The create-once attempt root could not be claimed before batch Popen."""

    def __init__(
        self, attempt_root: Path, cause: BaseException, *, created_by_this_process: bool
    ) -> None:
        self.attempt_root = Path(os.path.abspath(attempt_root))
        self.cause = cause
        self.created_by_this_process = created_by_this_process
        super().__init__(
            "repair attempt-root claim failed before Popen: "
            f"{type(cause).__name__}: {cause}"
        )


def _directory_identity(metadata: os.stat_result) -> dict[str, int]:
    return {
        "st_dev": metadata.st_dev,
        "st_ino": metadata.st_ino,
        "st_uid": metadata.st_uid,
        "st_gid": metadata.st_gid,
        "mode": stat.S_IMODE(metadata.st_mode),
        "st_nlink": metadata.st_nlink,
    }


class AttemptRootLease:
    """Open directory descriptors that pin the claimed attempt namespace."""

    def __init__(
        self,
        *,
        root: Path,
        layout: Mapping[str, Path],
        descriptors: Mapping[str, int],
        claim: Mapping[str, Any],
        repair_id: str,
    ) -> None:
        self.root = Path(root)
        self.layout = {key: Path(value) for key, value in layout.items()}
        self.descriptors = dict(descriptors)
        self.claim = dict(claim)
        self.repair_id = repair_id
        self.closed = False

    def verify(self, label: str) -> dict[str, Any]:
        if self.closed:
            raise RepairPipelineError(f"{label} attempt-root lease is already closed")
        verify_attempt_root_claim(
            self.claim,
            repair_id=self.repair_id,
            attempt_root=self.root,
            expected_layout=self.layout,
            label=label,
        )
        paths = {"root": self.root, **self.layout}
        identities = {
            "root": self.claim["root_identity"],
            **self.claim["layout_identities"],
        }
        for role, path in paths.items():
            descriptor = self.descriptors.get(role)
            if not isinstance(descriptor, int):
                raise RepairPipelineError(f"{label} lacks the {role} directory fd")
            descriptor_stat = os.fstat(descriptor)
            path_stat = path.lstat()
            if (
                not stat.S_ISDIR(descriptor_stat.st_mode)
                or not stat.S_ISDIR(path_stat.st_mode)
                or path.is_symlink()
                or descriptor_stat.st_dev != path_stat.st_dev
                or descriptor_stat.st_ino != path_stat.st_ino
            ):
                raise RepairPipelineError(
                    f"{label} {role} path no longer names the held directory inode"
                )
            claimed = identities[role]
            for field in ("st_dev", "st_ino", "st_uid", "st_gid"):
                if getattr(descriptor_stat, field) != claimed[field]:
                    raise RepairPipelineError(
                        f"{label} {role} held directory identity changed at {field}"
                    )
            if stat.S_IMODE(descriptor_stat.st_mode) != claimed["mode"]:
                raise RepairPipelineError(
                    f"{label} {role} held directory mode changed"
                )
        return dict(self.claim)

    def close(self) -> None:
        if self.closed:
            return
        for descriptor in reversed(list(self.descriptors.values())):
            try:
                os.close(descriptor)
            except OSError:
                pass
        self.closed = True


class RepairRunResult:
    """Two-value-compatible run result carrying the long-lived namespace lease."""

    def __init__(
        self,
        returncode: int,
        audit: Mapping[str, Any],
        attempt_lease: AttemptRootLease,
    ) -> None:
        self.returncode = returncode
        self.audit = dict(audit)
        self.attempt_lease = attempt_lease

    def __iter__(self) -> Any:
        yield self.returncode
        yield self.audit


def claim_attempt_root(
    config: Mapping[str, Any], prelock: Mapping[str, Any]
) -> AttemptRootLease:
    """Atomically own the fixed attempt root and precreate its empty layout."""

    attempt_root = resolve_repo_path(config["attempt_root"], inside_candidate=True)
    layout: dict[str, Path] = {}
    created = False
    descriptors: dict[str, int] = {}
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        attempt_root, layout = verify_attempt_namespace_contract(
            config, prelock, require_absent=True
        )
        os.mkdir(attempt_root, mode=0o700)
        created = True
        descriptors["root"] = os.open(attempt_root, flags)
        for role in ATTEMPT_LAYOUT_ROLES:
            expected = attempt_root / role
            if layout[role] != expected:
                raise RepairPipelineError(f"attempt layout role {role} is not direct")
            os.mkdir(role, mode=0o700, dir_fd=descriptors["root"])
            descriptors[role] = os.open(role, flags, dir_fd=descriptors["root"])
        root_identity = _directory_identity(os.fstat(descriptors["root"]))
        layout_identities = {
            role: _directory_identity(os.fstat(descriptors[role]))
            for role in ATTEMPT_LAYOUT_ROLES
        }
        if root_identity["mode"] != 0o700 or any(
            identity["mode"] != 0o700 for identity in layout_identities.values()
        ):
            raise RepairPipelineError("attempt namespace mkdir mode is not exact 0700")
        claim = add_self_hash(
            {
                "schema_version": ATTEMPT_ROOT_CLAIM_SCHEMA,
                "repair_id": prelock["repair_id"],
                "claimed_at": utc_now(),
                "monotonic_ns": time.monotonic_ns(),
                "attempt_root": str(attempt_root),
                "root_identity": root_identity,
                "layout": {role: str(layout[role]) for role in ATTEMPT_LAYOUT_ROLES},
                "layout_identities": layout_identities,
                "layout_sha256": object_sha256(
                    {role: str(layout[role]) for role in ATTEMPT_LAYOUT_ROLES}
                ),
                "root_created_with_exclusive_mkdir": True,
                "root_mkdir_mode": "0700",
                "all_layout_directories_precreated_before_final_foreign_preflight": True,
                "all_paths_contained_in_attempt_root": True,
                "no_symlinks": True,
                "directory_fds_held_until_final_verification": True,
                "appworld_v56_runtime_gate": False,
            },
            "claim_sha256",
        )
        lease = AttemptRootLease(
            root=attempt_root,
            layout=layout,
            descriptors=descriptors,
            claim=claim,
            repair_id=prelock["repair_id"],
        )
        lease.verify("new repair attempt claim")
        return lease
    except BaseException as exc:
        for descriptor in reversed(list(descriptors.values())):
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise RunNamespaceClaimError(
            attempt_root, exc, created_by_this_process=created
        ) from exc


def record_namespace_claim_failure(
    config: Mapping[str, Any], prelock: Mapping[str, Any], exc: RunNamespaceClaimError
) -> dict[str, Any]:
    """Publish claim failure outside a namespace that may belong to another process."""

    attempt_root = resolve_repo_path(config["attempt_root"], inside_candidate=True)
    observed: dict[str, Any] | None = None
    try:
        metadata = attempt_root.lstat()
        observed = {
            "kind": (
                "symlink"
                if stat.S_ISLNK(metadata.st_mode)
                else "directory"
                if stat.S_ISDIR(metadata.st_mode)
                else "other"
            ),
            "identity": _directory_identity(metadata),
        }
    except FileNotFoundError:
        observed = None
    incident = add_self_hash(
        {
            "schema_version": "androidworld_checklist_repair_namespace_claim_failure/v1",
            "created_at": utc_now(),
            "repair_id": prelock["repair_id"],
            "repair_prelock_sha256": prelock["prelock_sha256"],
            "status": "attempt_root_claim_failed_before_popen",
            "promotion_forbidden": True,
            "batch_popen_occurred": False,
            "attempt_root": repo_relative(attempt_root),
            "created_by_this_process": exc.created_by_this_process,
            "observed_attempt_root": observed,
            "error_type": type(exc.cause).__name__,
            "error": str(exc.cause),
        },
        "incident_sha256",
    )
    output = (
        WORK_ROOT
        / "repair_generation"
        / "incidents"
        / "run_namespace_claim_failures"
        / f"{incident['incident_sha256']}.json"
    )
    write_json_create_once(output, incident)
    return file_binding(output) | {"incident_sha256": incident["incident_sha256"]}


class ImmediateForeignPreflightFailure(RepairPipelineError):
    """A final pre-Popen foreign-process rejection carrying its exact evidence."""

    def __init__(self, record: Mapping[str, Any]) -> None:
        self.record = dict(record)
        super().__init__(
            "immediate foreign-process absence failed before Popen: "
            f"{self.record.get('foreign_processes')}"
        )


class RepairWrapperSignal(RepairPipelineError):
    """Raised by the outer wrapper's fail-closed signal handler."""

    def __init__(self, signum: int) -> None:
        self.signum = signum
        self.signal_name = signal.Signals(signum).name
        super().__init__(f"outer repair wrapper received {self.signal_name}")


def force_terminate_and_verify_process_group(
    process: subprocess.Popen[Any],
    audit: Mapping[str, Any],
    reason: str,
) -> tuple[dict[str, Any], list[str]]:
    """Always TERM, then KILL, then independently check the dedicated PGID."""

    failures: list[str] = []
    event: dict[str, Any] = {
        "reason": reason,
        "process_group_id": process.pid,
        "leader_returncode_before_cleanup": process.poll(),
    }
    before: list[dict[str, Any]] | None = None
    try:
        before = process_group_members(
            observe_process_rows(audit, "cleanup preflight"), process.pid
        )
    except BaseException as exc:
        event["preflight_observation_error"] = f"{type(exc).__name__}: {exc}"
    event["members_before"] = before
    event["member_count_before"] = len(before) if before is not None else None

    # Signal delivery is unconditional.  A failed /bin/ps observation must
    # never prevent cleanup of a process group whose leader has already died.
    try:
        os.killpg(process.pid, signal.SIGTERM)
        event["sigterm_sent"] = True
    except ProcessLookupError:
        event["sigterm_sent"] = False
    except BaseException as exc:
        event["sigterm_error"] = f"{type(exc).__name__}: {exc}"
        event["sigterm_sent"] = False

    term_grace_seconds = int(audit["failure_cleanup"]["term_grace_seconds"])
    after_term: list[dict[str, Any]] | None = before
    try:
        deadline = time.monotonic() + term_grace_seconds
        while time.monotonic() < deadline:
            after_term = process_group_members(
                observe_process_rows(audit, "cleanup SIGTERM wait"), process.pid
            )
            if not after_term:
                break
            time.sleep(0.05)
        event["members_after_sigterm"] = after_term
    except BaseException as exc:
        event["sigterm_wait_observation_error"] = f"{type(exc).__name__}: {exc}"
        event["members_after_sigterm"] = None
        time.sleep(term_grace_seconds)

    try:
        os.killpg(process.pid, signal.SIGKILL)
        event["sigkill_sent"] = True
    except ProcessLookupError:
        event["sigkill_sent"] = False
    except BaseException as exc:
        event["sigkill_error"] = f"{type(exc).__name__}: {exc}"
        event["sigkill_sent"] = False

    kill_wait_seconds = int(audit["failure_cleanup"]["kill_wait_seconds"])
    after_kill: list[dict[str, Any]] | None = None
    try:
        kill_deadline = time.monotonic() + kill_wait_seconds
        while time.monotonic() < kill_deadline:
            after_kill = process_group_members(
                observe_process_rows(audit, "cleanup SIGKILL wait"), process.pid
            )
            if not after_kill:
                break
            time.sleep(0.05)
        event["members_after_sigkill"] = after_kill
    except BaseException as exc:
        event["sigkill_wait_observation_error"] = f"{type(exc).__name__}: {exc}"
        event["members_after_sigkill"] = None
        time.sleep(kill_wait_seconds)

    try:
        if process.poll() is None:
            process.wait(timeout=kill_wait_seconds)
    except subprocess.TimeoutExpired:
        event["leader_wait_timed_out"] = True
    except BaseException as exc:
        event["leader_wait_error"] = f"{type(exc).__name__}: {exc}"

    # Reaping the leader can be the event that lets the kernel/init finally
    # dispose of killed descendants.  A single observation immediately after
    # ``wait`` is therefore racy: it can still see a short-lived zombie even
    # though that process can no longer execute.  Keep the gate fail-closed by
    # treating *every* visible PGID member (zombies included) as non-empty, and
    # require two consecutive empty observations inside a bounded post-reap
    # window before declaring cleanup complete.
    after: list[dict[str, Any]] | None = None
    post_reap_observation_count = 0
    consecutive_empty_observations = 0
    try:
        post_reap_deadline = time.monotonic() + kill_wait_seconds
        while True:
            after = process_group_members(
                observe_process_rows(audit, "cleanup post-reap wait"), process.pid
            )
            post_reap_observation_count += 1
            if after:
                consecutive_empty_observations = 0
            else:
                consecutive_empty_observations += 1
                if consecutive_empty_observations >= 2:
                    break
            if time.monotonic() >= post_reap_deadline:
                break
            time.sleep(0.05)
        event["members_after"] = after
        event["member_count_after"] = len(after)
        event["post_reap_observation_count"] = post_reap_observation_count
        event["post_reap_consecutive_empty_observations"] = (
            consecutive_empty_observations
        )
        event["process_group_empty_after_cleanup"] = (
            not after and consecutive_empty_observations >= 2
        )
    except BaseException as exc:
        event["postflight_observation_error"] = f"{type(exc).__name__}: {exc}"
        event["members_after"] = None
        event["member_count_after"] = None
        event["post_reap_observation_count"] = post_reap_observation_count
        event["post_reap_consecutive_empty_observations"] = (
            consecutive_empty_observations
        )
        event["process_group_empty_after_cleanup"] = False
    event["final_returncode"] = process.poll()
    if event["process_group_empty_after_cleanup"] is not True:
        failures.append(f"{reason}: process-group cleanup could not be verified")
    return add_self_hash(event, "cleanup_event_sha256"), failures


def failed_process_group_postflight(
    process: subprocess.Popen[Any],
    audit: Mapping[str, Any],
    cleanup_event: Mapping[str, Any],
    cleanup_failures: list[str],
) -> dict[str, Any]:
    before = cleanup_event.get("members_before")
    remaining = cleanup_event.get("members_after")
    record = {
        "schema_version": "androidworld_checklist_repair_batch_process_group_postflight/v1",
        "captured_at": utc_now(),
        "status": "fail",
        "batch_pid": process.pid,
        "process_group_id": process.pid,
        "ps_binary": audit["ps_binary"],
        "ps_command": audit["ps_command"],
        "members_detected_before_cleanup": before if isinstance(before, list) else [],
        "member_count_before_cleanup": len(before) if isinstance(before, list) else 0,
        # An outer exception always invokes the cleanup path, even if the
        # process group happened to be empty by the first successful sample.
        "cleanup_was_required": True,
        "remaining_processes": remaining if isinstance(remaining, list) else [],
        "remaining_process_count": len(remaining) if isinstance(remaining, list) else 0,
        "process_group_empty": (
            cleanup_event.get("process_group_empty_after_cleanup") is True
        ),
        "cleanup_failures": list(cleanup_failures),
    }
    return add_self_hash(record, "postflight_sha256")


def _run_with_concurrency_audit_inner(
    process: subprocess.Popen[Any],
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    foreign_preflight: Mapping[str, Any],
    generation_preflight: Mapping[str, Any],
    signal_state: Mapping[str, Any],
) -> tuple[int, dict[str, Any]]:
    audit = config["concurrency_audit"]
    samples_path = resolve_repo_path(audit["samples_path"], inside_candidate=True)
    summary_path = resolve_repo_path(audit["summary_path"], inside_candidate=True)
    if samples_path.exists() or summary_path.exists():
        raise RepairPipelineError("concurrency audit evidence already exists")
    samples_path.parent.mkdir(parents=True, exist_ok=True)
    expected = expanded_expected_case_attempts(
        list(audit["expected_case_attempts"]), prelock
    )
    expected_cases = {str(item["case_unit_id"]) for item in expected}
    drafter_path = str(
        verify_file_binding(audit["frozen_drafter"], "concurrency frozen drafter", inside_candidate=True)
    )
    interval = int(audit["sample_interval_milliseconds"]) / 1000.0
    stop = threading.Event()
    first_sample = threading.Event()
    state_lock = threading.Lock()
    monitor_errors: list[str] = []
    covered_cases: set[str] = set()
    sample_count = 0
    peak = 0
    peak_sample_count = 0
    cleanup_events: list[dict[str, Any]] = []
    foreign_seen: list[dict[str, Any]] = []
    cleanup_lock = threading.Lock()
    cleanup_failures: list[str] = []

    def terminate_process_group(reason: str) -> None:
        with cleanup_lock:
            event, failures = force_terminate_and_verify_process_group(
                process, audit, reason
            )
            cleanup_failures.extend(failures)
            cleanup_events.append(event)

    def monitor() -> None:
        nonlocal sample_count, peak, peak_sample_count
        try:
            with samples_path.open("x", encoding="utf-8", buffering=1) as handle:
                sequence = 0
                while True:
                    observed = subprocess.run(
                        list(audit["ps_command"]),
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=5,
                    )
                    if observed.returncode != 0:
                        raise RepairPipelineError(
                            f"/bin/ps returned {observed.returncode}: {observed.stderr.strip()}"
                        )
                    rows = parse_ps_rows(observed.stdout)
                    descendants = descendant_pids(rows, process.pid)
                    own_group = {
                        pid for pid, row in rows.items() if int(row.get("pgid", -1)) == process.pid
                    }
                    launcher_chain = ancestor_pids(rows, os.getpid()) | {os.getpid()}
                    foreign = foreign_drafting_processes(
                        rows,
                        patterns=list(audit["foreign_process_patterns"]),
                        excluded_pids=descendants | own_group | {process.pid} | launcher_chain,
                    )
                    if foreign:
                        known = {
                            (item["pid"], item["command_sha256"])
                            for item in foreign_seen
                        }
                        foreign_seen.extend(
                            item
                            for item in foreign
                            if (item["pid"], item["command_sha256"]) not in known
                        )
                        raise RepairPipelineError(
                            f"foreign drafting process appeared during repair run: {foreign}"
                        )
                    active = active_case_attempts(
                        rows,
                        batch_pid=process.pid,
                        drafter_path=drafter_path,
                        expected=expected,
                    )
                    row = {
                        "schema_version": "androidworld_checklist_repair_concurrency_sample/v1",
                        "sequence": sequence,
                        "captured_at": utc_now(),
                        "monotonic_ns": time.monotonic_ns(),
                        "batch_pid": process.pid,
                        "active_case_attempt_count": len(active),
                        "active_case_attempts": active,
                    }
                    row = add_self_hash(row, "sample_sha256")
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    with state_lock:
                        sample_count += 1
                        covered_cases.update(item["case_unit_id"] for item in active)
                        if len(active) > peak:
                            peak = len(active)
                            peak_sample_count = 1
                        elif len(active) == peak:
                            peak_sample_count += 1
                    first_sample.set()
                    sequence += 1
                    if stop.wait(interval):
                        break
        except BaseException as exc:
            with state_lock:
                monitor_errors.append(f"{type(exc).__name__}: {exc}")
            first_sample.set()
            terminate_process_group("monitor_exception")

    thread = threading.Thread(
        target=monitor,
        name=f"repair-concurrency-audit-{prelock['repair_id']}",
        daemon=False,
    )
    thread_started = False
    try:
        thread.start()
        thread_started = True
    except BaseException as exc:
        with state_lock:
            monitor_errors.append(
                f"monitor_thread_start_failed: {type(exc).__name__}: {exc}"
            )
        with samples_path.open("x", encoding="utf-8"):
            pass
        stop.set()
        terminate_process_group("monitor_thread_start_failed")
    if thread_started and not first_sample.wait(timeout=10):
        with state_lock:
            monitor_errors.append("RepairPipelineError: concurrency monitor first-sample timeout")
        terminate_process_group("first_sample_timeout")
        stop.set()
        thread.join(timeout=10)
        returncode = process.poll() if process.poll() is not None else -1
    elif thread_started:
        try:
            returncode = process.wait()
        except BaseException as exc:
            with state_lock:
                monitor_errors.append(f"{type(exc).__name__}: wrapper interrupted: {exc}")
            terminate_process_group("wrapper_interrupted")
            returncode = process.poll() if process.poll() is not None else -1
        finally:
            stop.set()
            thread.join(timeout=10)
    else:
        returncode = process.poll() if process.poll() is not None else process.wait()
    if thread_started and thread.is_alive():
        terminate_process_group("monitor_thread_join_timeout")
        stop.set()
        thread.join(timeout=10)
        if thread.is_alive():
            raise RepairPipelineError("concurrency monitor thread did not stop after cleanup")
    members_before_postflight = process_group_members(
        observe_process_rows(audit, "batch process-group postflight"), process.pid
    )
    if members_before_postflight:
        terminate_process_group("postwait_residual_process_group")
    remaining_processes = process_group_members(
        observe_process_rows(audit, "batch process-group cleanup recheck"), process.pid
    )
    process_group_postflight = {
        "schema_version": (
            "androidworld_checklist_repair_batch_process_group_postflight/v1"
        ),
        "captured_at": utc_now(),
        "status": (
            "pass"
            if not members_before_postflight
            and not remaining_processes
            and not cleanup_failures
            else "fail"
        ),
        "batch_pid": process.pid,
        "process_group_id": process.pid,
        "ps_binary": audit["ps_binary"],
        "ps_command": audit["ps_command"],
        "members_detected_before_cleanup": members_before_postflight,
        "member_count_before_cleanup": len(members_before_postflight),
        "cleanup_was_required": bool(members_before_postflight),
        "remaining_processes": remaining_processes,
        "remaining_process_count": len(remaining_processes),
        "process_group_empty": not remaining_processes,
        "cleanup_failures": list(cleanup_failures),
    }
    process_group_postflight = add_self_hash(
        process_group_postflight, "postflight_sha256"
    )
    with state_lock:
        missing = sorted(expected_cases - covered_cases)
        extra = sorted(covered_cases - expected_cases)
        errors = list(monitor_errors)
        observed_sample_count = sample_count
        observed_peak = peak
        observed_peak_sample_count = peak_sample_count
        observed_cases = sorted(covered_cases)
    immediate_foreign_preflight = generation_preflight.get(
        "immediate_foreign_preflight"
    ) or {}
    gates = {
        "foreign_process_preflight_pass": (
            foreign_preflight.get("status") == "pass"
            and foreign_preflight.get("foreign_process_count") == 0
            and foreign_preflight.get("foreign_processes") == []
        ),
        "immediate_foreign_preflight_pass": (
            immediate_foreign_preflight.get("status") == "pass"
            and immediate_foreign_preflight.get("foreign_process_count") == 0
            and immediate_foreign_preflight.get("foreign_processes") == []
        ),
        "foreign_processes_absent_during_run": foreign_seen == [],
        "monitor_error_free": not errors,
        "sample_count_positive": observed_sample_count > 0,
        "observed_peak_equals_six": observed_peak == EXPECTED_PARALLELISM,
        "at_least_one_six_way_overlap_sample": observed_peak_sample_count >= 1
        and observed_peak == EXPECTED_PARALLELISM,
        "never_exceeded_six": observed_peak <= EXPECTED_PARALLELISM,
        "all_repair_cases_observed": not missing and not extra,
        "batch_returncode_zero": returncode == 0,
        "batch_process_group_postflight_passed": (
            process_group_postflight["status"] == "pass"
            and process_group_postflight["process_group_empty"] is True
            and process_group_postflight["remaining_process_count"] == 0
        ),
        "no_cleanup_required": (
            process_group_postflight["cleanup_was_required"] is False
            and not cleanup_events
        ),
    }
    summary = {
        "schema_version": "androidworld_checklist_repair_concurrency_audit/v1",
        "created_at": utc_now(),
        "status": "pass" if all(gates.values()) else "fail",
        "repair_id": prelock["repair_id"],
        "repair_prelock_sha256": prelock["prelock_sha256"],
        "batch_pid": process.pid,
        "batch_returncode": returncode,
        "sample_interval_milliseconds": audit["sample_interval_milliseconds"],
        "ps_binary": audit["ps_binary"],
        "ps_command": audit["ps_command"],
        "monitor_implementation": audit["monitor_implementation"],
        "outer_wrapper_invocation": audit["outer_wrapper_invocation"],
        "batch_runner_command_sha256": audit["batch_runner_command_sha256"],
        "batch_runner_execution_command_sha256": (
            generation_preflight.get("core") or {}
        ).get("runner_execution_command_sha256"),
        "prelock_file_sha256_anchor": (
            generation_preflight.get("core") or {}
        ).get("prelock_file_sha256_anchor"),
        "prelock_internal_sha256_anchor": (
            generation_preflight.get("core") or {}
        ).get("prelock_internal_sha256_anchor"),
        "snapshot_exact_tree_hashes": (
            generation_preflight.get("core") or {}
        ).get("snapshot_exact_tree_hashes"),
        "isolated_bootstrap_sha256": (
            generation_preflight.get("core") or {}
        ).get("isolated_bootstrap_sha256"),
        "python_runtime_sha256": (
            generation_preflight.get("core") or {}
        ).get("python_runtime_sha256"),
        "runtime_source_snapshot_sha256": (
            generation_preflight.get("core") or {}
        ).get("runtime_source_snapshot_sha256"),
        "runner_environment": audit["runner_environment"],
        "runner_environment_sha256": audit["runner_environment_sha256"],
        "attempt_namespace_sha256": audit["attempt_namespace_sha256"],
        "attempt_root_claim": generation_preflight.get("attempt_root_claim"),
        "attempt_root_claim_sha256": generation_preflight.get(
            "attempt_root_claim_sha256"
        ),
        "expected_case_attempts_sha256": audit["expected_case_attempts_sha256"],
        "repair_execution_plan": audit["repair_execution_plan"],
        "repair_execution_plan_sha256": audit["repair_execution_plan_sha256"],
        "execution_order_semantics": audit["execution_order_semantics"],
        "scope_rule": audit["scope_rule"],
        "samples": file_binding(samples_path),
        "sample_count": observed_sample_count,
        "observed_peak_active_case_attempts": observed_peak,
        "samples_at_observed_peak": observed_peak_sample_count,
        "expected_case_count": len(expected_cases),
        "observed_case_count": len(observed_cases),
        "observed_cases": observed_cases,
        "missing_cases": missing,
        "extra_cases": extra,
        "monitor_errors": errors,
        "foreign_process_preflight": dict(foreign_preflight),
        "immediate_foreign_preflight": dict(immediate_foreign_preflight),
        "foreign_processes_seen_during_run": foreign_seen,
        "generation_preflight": dict(generation_preflight),
        "outer_wrapper_signal": dict(signal_state) if signal_state.get("received") else None,
        "batch_process_group_postflight": process_group_postflight,
        "popen_start_new_session": True,
        "failure_cleanup_policy": audit["failure_cleanup"],
        "cleanup_events": cleanup_events,
        "gates": gates,
    }
    summary = add_self_hash(summary, "audit_sha256")
    write_json_create_once(summary_path, summary)
    binding = file_binding(summary_path) | {"audit_sha256": summary["audit_sha256"]}
    return returncode, {"summary": binding, "samples": summary["samples"], **summary}


def _run_after_verified_generation_preflight(
    command: list[str],
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    environment: Mapping[str, str],
    foreign_preflight: Mapping[str, Any],
    generation_preflight: Mapping[str, Any],
    lease_sink: list[AttemptRootLease] | None = None,
) -> RepairRunResult:
    """Own the batch PGID after the caller has passed the immediate launch gate."""

    audit = config["concurrency_audit"]
    handled_signals = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    original_handlers = {item: signal.getsignal(item) for item in handled_signals}
    if not hasattr(signal, "pthread_sigmask"):
        raise RepairPipelineError("signal-safe Popen barrier requires pthread_sigmask")
    original_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set(handled_signals))
    process: subprocess.Popen[Any] | None = None
    handlers_installed = False
    mask_restored_after_install = False
    signal_state: dict[str, Any] = {"received": False}
    caught: BaseException | None = None
    result: tuple[int, dict[str, Any]] | None = None
    cleanup_event: dict[str, Any] | None = None
    cleanup_failures: list[str] = []
    process_group_postflight: dict[str, Any] | None = None
    launch_generation_preflight: dict[str, Any] | None = None
    attempt_lease: AttemptRootLease | None = None
    try:
        attempt_lease = claim_attempt_root(config, prelock)
        if lease_sink is not None:
            lease_sink.append(attempt_lease)
        immediate_foreign_preflight = immediate_foreign_drafting_preflight(
            config,
            early_foreign_preflight=foreign_preflight,
            deterministic_generation_preflight=generation_preflight,
            attempt_claim=attempt_lease.claim,
        )
        verify_immediate_foreign_preflight_evidence(
            immediate_foreign_preflight,
            audit=audit,
            early_foreign_preflight=foreign_preflight,
            deterministic_generation_preflight=generation_preflight,
            attempt_claim=attempt_lease.claim,
            label="immediate pre-Popen foreign preflight",
            require_zero=False,
        )
        launch_generation_preflight = finalize_generation_launch_preflight(
            generation_preflight,
            immediate_foreign_preflight,
            attempt_lease.claim,
        )
        process = subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            env=dict(environment),
            start_new_session=True,
        )

        def handle_wrapper_signal(signum: int, _frame: Any) -> None:
            if signal_state["received"]:
                return
            signal_state.update(
                {
                    "received": True,
                    "signum": signum,
                    "signal_name": signal.Signals(signum).name,
                    "captured_at": utc_now(),
                    "monotonic_ns": time.monotonic_ns(),
                    "cleanup_scope": "batch_process_group",
                }
            )
            raise RepairWrapperSignal(signum)

        for item in handled_signals:
            signal.signal(item, handle_wrapper_signal)
        handlers_installed = True
        # Pending signals can only be delivered after every handler knows the
        # newly-owned PGID.  This closes the Popen→handler-install orphan race.
        signal.pthread_sigmask(signal.SIG_SETMASK, original_mask)
        mask_restored_after_install = True
        result = _run_with_concurrency_audit_inner(
            process,
            config=config,
            prelock=prelock,
            foreign_preflight=foreign_preflight,
            generation_preflight=launch_generation_preflight,
            signal_state=signal_state,
        )
    except BaseException as exc:
        caught = exc
    finally:
        if caught is not None and process is not None:
            # This guard covers every instruction after Popen, including monitor
            # setup, wait/join, final /bin/ps observations, summary publication,
            # and exceptions raised while constructing normal postflight proof.
            cleanup_event, cleanup_failures = force_terminate_and_verify_process_group(
                process,
                audit,
                f"outer_wrapper_exception:{type(caught).__name__}",
            )
            process_group_postflight = failed_process_group_postflight(
                process,
                audit,
                cleanup_event,
                cleanup_failures,
            )
        # Block the handled set while restoring the exact pre-run handlers and
        # mask.  A second signal after the first is ignored by the handler until
        # this restoration point and cannot interrupt mandatory PG cleanup.
        signal.pthread_sigmask(signal.SIG_BLOCK, set(handled_signals))
        if handlers_installed:
            for item, old_handler in original_handlers.items():
                signal.signal(item, old_handler)
        signal.pthread_sigmask(signal.SIG_SETMASK, original_mask)
    if caught is not None:
        if process is None:
            if attempt_lease is not None:
                setattr(caught, "attempt_lease", attempt_lease)
            raise caught
        assert cleanup_event is not None and process_group_postflight is not None
        raise AuditedRepairRunFailure(
            caught,
            batch_pid=process.pid,
            cleanup_event=cleanup_event,
            process_group_postflight=process_group_postflight,
            generation_preflight=(launch_generation_preflight or generation_preflight),
            attempt_lease=attempt_lease,
            wrapper_signal=signal_state if signal_state.get("received") else None,
        ) from caught
    if result is None:
        raise RepairPipelineError("monitored repair wrapper returned no result")
    if not mask_restored_after_install:
        raise RepairPipelineError("outer signal mask was not restored after handler installation")
    if attempt_lease is None:
        raise RepairPipelineError("successful monitored run lacks an attempt-root lease")
    attempt_lease.verify("post-batch repair attempt lease")
    return RepairRunResult(result[0], result[1], attempt_lease)


def run_with_concurrency_audit(
    command: list[str],
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    environment: Mapping[str, str],
    foreign_preflight: Mapping[str, Any],
    generation_preflight: Mapping[str, Any],
    readonly_preflight_record: Mapping[str, Any],
    codex_auth_pre: Mapping[str, Any],
    lease_sink: list[AttemptRootLease] | None = None,
) -> RepairRunResult:
    """Require the complete deterministic gate, then enter the PGID owner."""

    # This immediate, side-effect-free recheck is the final generation gate
    # before the signal-safe Popen barrier.  A missing/tampered token or newly
    # created output/evidence path cannot issue the first model call.
    verify_generation_preflight_record(
        generation_preflight,
        config=config,
        prelock=prelock,
        command=command,
        environment=environment,
        readonly_preflight_record=readonly_preflight_record,
        foreign_preflight=foreign_preflight,
        codex_auth_pre=codex_auth_pre,
    )
    return _run_after_verified_generation_preflight(
        command,
        config=config,
        prelock=prelock,
        environment=environment,
        foreign_preflight=foreign_preflight,
        generation_preflight=generation_preflight,
        lease_sink=lease_sink,
    )


def safe_run_with_concurrency_audit(
    command: list[str],
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    environment: Mapping[str, str],
    foreign_preflight: Mapping[str, Any],
    generation_preflight: Mapping[str, Any],
    readonly_preflight_record: Mapping[str, Any],
    codex_auth_pre: Mapping[str, Any],
    lease_sink: list[AttemptRootLease] | None = None,
) -> RepairRunResult:
    try:
        return run_with_concurrency_audit(
            command,
            config=config,
            prelock=prelock,
            environment=environment,
            foreign_preflight=foreign_preflight,
            generation_preflight=generation_preflight,
            readonly_preflight_record=readonly_preflight_record,
            codex_auth_pre=codex_auth_pre,
            lease_sink=lease_sink,
        )
    except BaseException as exc:
        attempt_lease = (
            lease_sink[-1]
            if lease_sink
            else getattr(exc, "attempt_lease", None)
        )
        if isinstance(exc, RunNamespaceClaimError):
            incident = record_namespace_claim_failure(config, prelock, exc)
            raise RepairPipelineError(
                f"attempt-root claim failed with Popen=0; incident={incident}"
            ) from exc
        if not isinstance(attempt_lease, AttemptRootLease):
            synthetic = RunNamespaceClaimError(
                resolve_repo_path(config["attempt_root"], inside_candidate=True),
                exc,
                created_by_this_process=False,
            )
            incident = record_namespace_claim_failure(config, prelock, synthetic)
            raise RepairPipelineError(
                f"pre-claim generation gate failed with Popen=0; incident={incident}"
            ) from exc
        attempt_lease.verify("failed repair attempt lease before evidence")
        audit = config["concurrency_audit"]
        samples_path = resolve_repo_path(audit["samples_path"], inside_candidate=True)
        summary_path = resolve_repo_path(audit["summary_path"], inside_candidate=True)
        samples_path.parent.mkdir(parents=True, exist_ok=True)
        if not samples_path.exists():
            with samples_path.open("x", encoding="utf-8"):
                pass
        if summary_path.exists():
            summary = load_json(summary_path, "failed concurrency audit summary")
            verify_internal_hash(summary, ("audit_sha256",), "failed concurrency audit summary")
        else:
            if isinstance(exc, AuditedRepairRunFailure):
                failure_cause = exc.cause
                failure_batch_pid: int | None = exc.batch_pid
                failure_postflight = dict(exc.process_group_postflight)
                failure_cleanup_events = [dict(exc.cleanup_event)]
                failure_wrapper_signal = exc.wrapper_signal
                failure_generation_preflight = dict(exc.generation_preflight)
                failure_immediate_preflight = dict(
                    failure_generation_preflight.get(
                        "immediate_foreign_preflight"
                    )
                    or {}
                )
                failure_returncode = exc.cleanup_event.get("final_returncode")
                if not isinstance(failure_returncode, int):
                    failure_returncode = -1
            else:
                failure_cause = exc
                failure_batch_pid = None
                failure_cleanup_events = []
                failure_wrapper_signal = None
                failure_generation_preflight = dict(generation_preflight)
                failure_immediate_preflight = (
                    dict(exc.record)
                    if isinstance(exc, ImmediateForeignPreflightFailure)
                    else {}
                )
                failure_returncode = -1
                failure_postflight = add_self_hash(
                    {
                        "schema_version": (
                            "androidworld_checklist_repair_batch_process_group_postflight/v1"
                        ),
                        "captured_at": utc_now(),
                        "status": "unavailable_before_successful_popen",
                        "batch_pid": None,
                        "process_group_id": None,
                        "ps_binary": audit["ps_binary"],
                        "ps_command": audit["ps_command"],
                        "members_detected_before_cleanup": [],
                        "member_count_before_cleanup": 0,
                        "cleanup_was_required": False,
                        "remaining_processes": [],
                        "remaining_process_count": 0,
                        "process_group_empty": False,
                        "cleanup_failures": [f"{type(exc).__name__}: {exc}"],
                    },
                    "postflight_sha256",
                )
            summary = {
                "schema_version": "androidworld_checklist_repair_concurrency_audit/v1",
                "created_at": utc_now(),
                "status": "fail",
                "repair_id": prelock["repair_id"],
                "repair_prelock_sha256": prelock["prelock_sha256"],
                "batch_pid": failure_batch_pid,
                "batch_returncode": failure_returncode,
                "sample_interval_milliseconds": audit["sample_interval_milliseconds"],
                "ps_binary": audit["ps_binary"],
                "ps_command": audit["ps_command"],
                "monitor_implementation": audit["monitor_implementation"],
                "outer_wrapper_invocation": audit["outer_wrapper_invocation"],
                "batch_runner_command_sha256": audit["batch_runner_command_sha256"],
                "runtime_source_snapshot_sha256": audit.get(
                    "runtime_source_snapshot_sha256"
                ),
                "runner_environment": audit["runner_environment"],
                "runner_environment_sha256": audit[
                    "runner_environment_sha256"
                ],
                "attempt_namespace_sha256": audit["attempt_namespace_sha256"],
                "attempt_root_claim": attempt_lease.claim,
                "attempt_root_claim_sha256": attempt_lease.claim[
                    "claim_sha256"
                ],
                "expected_case_attempts_sha256": audit["expected_case_attempts_sha256"],
                "repair_execution_plan": audit["repair_execution_plan"],
                "repair_execution_plan_sha256": audit["repair_execution_plan_sha256"],
                "execution_order_semantics": audit["execution_order_semantics"],
                "scope_rule": audit["scope_rule"],
                "samples": file_binding(samples_path),
                "sample_count": 0,
                "observed_peak_active_case_attempts": 0,
                "samples_at_observed_peak": 0,
                "expected_case_count": len(audit["expected_case_attempts"]),
                "observed_case_count": 0,
                "observed_cases": [],
                "missing_cases": sorted(
                    item["case_unit_id"] for item in audit["expected_case_attempts"]
                ),
                "extra_cases": [],
                "monitor_errors": [
                    f"{type(failure_cause).__name__}: {failure_cause}"
                ],
                "foreign_process_preflight": dict(foreign_preflight),
                "immediate_foreign_preflight": dict(
                    failure_immediate_preflight
                ),
                "foreign_processes_seen_during_run": [],
                "generation_preflight": failure_generation_preflight,
                "outer_wrapper_signal": failure_wrapper_signal,
                "batch_process_group_postflight": failure_postflight,
                "popen_start_new_session": True,
                "failure_cleanup_policy": audit["failure_cleanup"],
                "cleanup_events": failure_cleanup_events,
                "gates": {
                    "foreign_process_preflight_pass": (
                        foreign_preflight.get("status") == "pass"
                        and foreign_preflight.get("foreign_process_count") == 0
                        and foreign_preflight.get("foreign_processes") == []
                    ),
                    "immediate_foreign_preflight_pass": False,
                    "foreign_processes_absent_during_run": True,
                    "monitor_error_free": False,
                    "sample_count_positive": False,
                    "observed_peak_equals_six": False,
                    "at_least_one_six_way_overlap_sample": False,
                    "never_exceeded_six": True,
                    "all_repair_cases_observed": False,
                    "batch_returncode_zero": False,
                    "batch_process_group_postflight_passed": False,
                    "no_cleanup_required": False,
                },
            }
            summary = add_self_hash(summary, "audit_sha256")
            write_json_create_once(summary_path, summary)
        result_audit = {
            "summary": file_binding(summary_path) | {"audit_sha256": summary["audit_sha256"]},
            "samples": summary["samples"],
            **summary,
        }
        attempt_lease.verify("failed repair attempt lease after evidence")
        return RepairRunResult(-1, result_audit, attempt_lease)


def readonly_preflight(
    config: Mapping[str, Any], prelock: Mapping[str, Any]
) -> dict[str, Any]:
    pre_record, helper, window = verify_readonly_window_static(config, prelock)
    post_path = resolve_repo_path(window["post_snapshot_path"], inside_candidate=True)
    guard_path = resolve_repo_path(window["guard_path"], inside_candidate=True)
    if post_path.exists() or guard_path.exists():
        raise RepairPipelineError(
            "repair read-only post/guard evidence already exists; a new attempt requires a new prelock"
        )
    phase = f"runner_preflight_checklist_repair_generation_{prelock['repair_id']}"
    current = helper.readonly_operation_snapshot(
        phase=phase, repo_root=REPO_ROOT, work_root=WORK_ROOT
    )
    before = pre_record["readonly_snapshot"]
    protected_equal = {
        root: before["roots"].get(root) == (current.get("roots") or {}).get(root)
        for root in window["protected_roots"]
    }
    official_equal = before.get("official100") == current.get("official100")
    if not all(protected_equal.values()) or not official_equal:
        raise RepairPipelineError(
            "protected roots or official100 changed between repair pre-snapshot and runner preflight"
        )
    nonbinding = window["nonbinding_live_tool_root"]
    result = {
        "phase": phase,
        "protected_root_equality": protected_equal,
        "official100_equal": official_equal,
        "protected_roots_sha256": object_sha256(
            {root: current["roots"][root] for root in window["protected_roots"]}
        ),
        "official100_sha256": current["official100"]["sha256"],
        "nonbinding_live_tool_root": nonbinding,
        "nonbinding_live_tool_root_matches_pre_snapshot": (
            before["roots"].get(nonbinding) == current["roots"].get(nonbinding)
        ),
        "nonbinding_live_tool_root_observed_sha256": object_sha256(
            current["roots"].get(nonbinding)
        ),
    }
    return add_self_hash(result, "preflight_sha256")


def finalize_readonly_guard(
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    runner_preflight_record: Mapping[str, Any],
) -> dict[str, Any]:
    pre_record, helper, window = verify_readonly_window_static(config, prelock)
    post_path = resolve_repo_path(window["post_snapshot_path"], inside_candidate=True)
    guard_path = resolve_repo_path(window["guard_path"], inside_candidate=True)
    if post_path.exists() or guard_path.exists():
        raise RepairPipelineError("refusing to overwrite repair read-only post/guard evidence")
    phase = f"after_checklist_repair_generation_{prelock['repair_id']}"
    readonly = helper.readonly_operation_snapshot(
        phase=phase, repo_root=REPO_ROOT, work_root=WORK_ROOT
    )
    post_record = {
        "schema_version": "androidworld_checklist_repair_readonly_snapshot/v2",
        "phase": phase,
        "snapshot_helper": window["execution_helper"],
        "supersedes_invalidated_pre_snapshot": window[
            "invalidated_pre_snapshot_incident"
        ],
        "readonly_snapshot": readonly,
        "readonly_core_sha256": object_sha256(helper.readonly_snapshot_core(readonly)),
        "trust_policy": "snapshot semantics come exclusively from the bound stdlib-only helper",
    }
    post_record = add_self_hash(post_record, "snapshot_sha256")
    write_json_create_once(post_path, post_record)
    before = pre_record["readonly_snapshot"]
    comparison = helper.compare_gate(before, readonly)
    protected_equal = comparison["protected_root_equality"]
    official_equal = comparison["official100_equal"]
    nonbinding = window["nonbinding_live_tool_root"]
    status = "pass" if all(protected_equal.values()) and official_equal else "fail"
    guard = {
        "schema_version": "androidworld_checklist_repair_readonly_guard/v1",
        "created_at": utc_now(),
        "status": status,
        "repair_id": prelock["repair_id"],
        "repair_prelock_sha256": prelock["prelock_sha256"],
        "snapshot_helper": window["execution_helper"],
        "pre_snapshot": window["pre_snapshot"],
        "post_snapshot": file_binding(post_path)
        | {
            "snapshot_sha256": post_record["snapshot_sha256"],
            "readonly_core_sha256": post_record["readonly_core_sha256"],
        },
        "runner_preflight": dict(runner_preflight_record),
        "protected_root_equality": protected_equal,
        "protected_roots_unchanged": all(protected_equal.values()),
        "official100_equal": official_equal,
        "nonbinding_live_tool_root": nonbinding,
        "nonbinding_live_tool_root_equal": (
            before["roots"].get(nonbinding) == readonly["roots"].get(nonbinding)
        ),
        "nonbinding_live_tool_root_before_sha256": object_sha256(
            before["roots"].get(nonbinding)
        ),
        "nonbinding_live_tool_root_after_sha256": object_sha256(
            readonly["roots"].get(nonbinding)
        ),
        "policy": (
            "this flow writes only under candidate116 and requires exact pre/post content-and-metadata "
            "endpoint equality for results, paper_result_packages, the submitted official100 package, "
            "and the official100 selector; endpoint equality does not prove that a malicious temporary "
            "write-and-restore never occurred; neurips_ed_track_minimal is recorded but nonbinding"
        ),
    }
    guard = add_self_hash(guard, "guard_sha256")
    write_json_create_once(guard_path, guard)
    return {
        "status": status,
        "guard": file_binding(guard_path) | {"guard_sha256": guard["guard_sha256"]},
        "post_snapshot": guard["post_snapshot"],
        "protected_root_equality": protected_equal,
        "official100_equal": official_equal,
    }


def record_readonly_post_failure(
    config: Mapping[str, Any], prelock: Mapping[str, Any], exc: BaseException
) -> dict[str, Any]:
    window = config.get("repair_readonly_window") or {}
    post_path = resolve_repo_path(window["post_snapshot_path"], inside_candidate=True)
    guard_path = resolve_repo_path(window["guard_path"], inside_candidate=True)
    incident = {
        "schema_version": "androidworld_checklist_repair_readonly_post_failure/v1",
        "created_at": utc_now(),
        "status": "readonly_post_capture_or_guard_failed",
        "repair_id": prelock["repair_id"],
        "repair_prelock_sha256": prelock["prelock_sha256"],
        "promotion_forbidden": True,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "pre_snapshot": window.get("pre_snapshot"),
        "execution_helper": window.get("execution_helper"),
        "expected_post_snapshot_path": window.get("post_snapshot_path"),
        "expected_guard_path": window.get("guard_path"),
        "partial_post_snapshot": file_binding(post_path) if post_path.is_file() else None,
        "partial_guard": file_binding(guard_path) if guard_path.is_file() else None,
    }
    incident = add_self_hash(incident, "incident_sha256")
    output = resolve_repo_path(config["evidence_root"], inside_candidate=True) / (
        "readonly.post_failure.json"
    )
    if output.exists():
        raise RepairPipelineError(f"read-only post failure incident already exists: {output}")
    write_json_create_once(output, incident)
    return file_binding(output) | {"incident_sha256": incident["incident_sha256"]}


def verify_concurrency_audit_evidence(
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    binding: Mapping[str, Any],
    codex_auth_pre: Mapping[str, Any],
) -> dict[str, Any]:
    audit_config = config["concurrency_audit"]
    summary_path = verify_file_binding(
        binding, "concurrency audit summary", inside_candidate=True
    )
    expected_summary_path = resolve_repo_path(audit_config["summary_path"], inside_candidate=True)
    if summary_path != expected_summary_path:
        raise RepairPipelineError("concurrency audit summary path differs from prelock")
    summary = load_json(summary_path, "concurrency audit summary")
    verify_internal_hash(summary, ("audit_sha256",), "concurrency audit summary")
    if summary.get("audit_sha256") != binding.get("audit_sha256"):
        raise RepairPipelineError("concurrency audit internal hash differs from receipt input")
    samples_path = verify_file_binding(
        summary.get("samples"), "concurrency audit samples", inside_candidate=True
    )
    if samples_path != resolve_repo_path(audit_config["samples_path"], inside_candidate=True):
        raise RepairPipelineError("concurrency audit samples path differs from prelock")
    rows = load_jsonl(samples_path)
    expanded_expected = expanded_expected_case_attempts(
        list(audit_config["expected_case_attempts"]), prelock
    )
    expected_cases = {item["case_unit_id"] for item in expanded_expected}
    expected_by_case = {item["case_unit_id"]: item for item in expanded_expected}
    drafter_path = str(
        verify_file_binding(
            audit_config["frozen_drafter"],
            "concurrency verifier frozen drafter",
            inside_candidate=True,
        )
    )
    covered: set[str] = set()
    peak = 0
    peak_count = 0
    previous_monotonic = -1
    for sequence, row in enumerate(rows):
        verify_internal_hash(row, ("sample_sha256",), f"concurrency sample {sequence}")
        active = row.get("active_case_attempts")
        if (
            set(row) != {
                "schema_version",
                "sequence",
                "captured_at",
                "monotonic_ns",
                "batch_pid",
                "active_case_attempt_count",
                "active_case_attempts",
                "sample_sha256",
            }
            or row.get("batch_pid") != summary.get("batch_pid")
            or row.get("schema_version")
            != "androidworld_checklist_repair_concurrency_sample/v1"
            or row.get("sequence") != sequence
            or not isinstance(row.get("monotonic_ns"), int)
            or row["monotonic_ns"] <= previous_monotonic
            or not isinstance(active, list)
            or row.get("active_case_attempt_count") != len(active)
            or len(active) > EXPECTED_PARALLELISM
        ):
            raise RepairPipelineError(f"concurrency sample {sequence} structure/count is invalid")
        previous_monotonic = row["monotonic_ns"]
        case_ids = [item.get("case_unit_id") for item in active if isinstance(item, Mapping)]
        if len(case_ids) != len(active) or len(case_ids) != len(set(case_ids)):
            raise RepairPipelineError(f"concurrency sample {sequence} has duplicate/invalid cases")
        if not set(case_ids).issubset(expected_cases):
            raise RepairPipelineError(f"concurrency sample {sequence} contains an unbound case")
        for active_item in active:
            if set(active_item) != {
                "pid",
                "ppid",
                "pgid",
                "case_unit_id",
                "execution_rank",
                "execution_lane",
                "selection_rank",
                "command_sha256",
                "drafter_path",
                "case_packet_path",
                "case_output_dir",
                "expected_attempt_sha256",
            }:
                raise RepairPipelineError(
                    f"concurrency sample {sequence} active-item fields differ"
                )
            case_id = active_item["case_unit_id"]
            expected_item = expected_by_case[case_id]
            allowed_hashes = expected_item["allowed_ps_command_line_sha256"]
            if (
                not isinstance(active_item["pid"], int)
                or active_item["pid"] <= 0
                or not isinstance(active_item["ppid"], int)
                or active_item["ppid"] != row.get("batch_pid")
                or active_item["pgid"] != row.get("batch_pid")
                or active_item["execution_rank"] != expected_item["execution_rank"]
                or active_item["execution_lane"] != expected_item["execution_lane"]
                or active_item["selection_rank"] != expected_item["selection_rank"]
                or active_item["command_sha256"] not in allowed_hashes
                or active_item["drafter_path"] != drafter_path
                or active_item["case_packet_path"] != expected_item["case_packet_path"]
                or active_item["case_output_dir"] != expected_item["case_output_dir"]
                or active_item["expected_attempt_sha256"] != object_sha256(expected_item)
            ):
                raise RepairPipelineError(
                    f"concurrency sample {sequence} exact scope differs for {case_id}"
                )
        covered.update(case_ids)
        count = len(active)
        if count > peak:
            peak = count
            peak_count = 1
        elif count == peak:
            peak_count += 1
    postflight = summary.get("batch_process_group_postflight")
    if not isinstance(postflight, Mapping):
        raise RepairPipelineError("concurrency summary has no process-group postflight")
    verify_internal_hash(
        postflight, ("postflight_sha256",), "concurrency process-group postflight"
    )
    foreign_preflight = summary.get("foreign_process_preflight")
    if not isinstance(foreign_preflight, Mapping):
        raise RepairPipelineError("concurrency summary has no foreign-process observation")
    verify_internal_hash(
        foreign_preflight,
        ("preflight_sha256",),
        "concurrency foreign-process preflight",
    )
    generation_preflight = summary.get("generation_preflight")
    if not isinstance(generation_preflight, Mapping):
        raise RepairPipelineError("concurrency summary has no deterministic generation preflight")
    verify_internal_hash(
        generation_preflight,
        ("generation_preflight_sha256",),
        "generation launch preflight",
    )
    deterministic_preflight = generation_preflight.get("deterministic_preflight")
    immediate_preflight = generation_preflight.get("immediate_foreign_preflight")
    attempt_claim = generation_preflight.get("attempt_root_claim")
    if not isinstance(deterministic_preflight, Mapping) or not isinstance(
        immediate_preflight, Mapping
    ) or not isinstance(attempt_claim, Mapping):
        raise RepairPipelineError(
            "generation launch preflight lacks deterministic/immediate evidence"
        )
    verify_internal_hash(
        deterministic_preflight,
        ("generation_preflight_sha256",),
        "nested deterministic generation preflight",
    )
    verify_internal_hash(
        immediate_preflight,
        ("immediate_preflight_sha256",),
        "nested immediate foreign preflight",
    )
    verify_immediate_foreign_preflight_evidence(
        immediate_preflight,
        audit=audit_config,
        early_foreign_preflight=foreign_preflight,
        deterministic_generation_preflight=deterministic_preflight,
        attempt_claim=attempt_claim,
        label="concurrency immediate foreign preflight",
    )
    attempt_root, attempt_layout = _attempt_layout(config)
    verify_attempt_root_claim(
        attempt_claim,
        repair_id=prelock["repair_id"],
        attempt_root=attempt_root,
        expected_layout=attempt_layout,
        label="concurrency attempt-root claim",
    )
    generation_core = generation_preflight.get("core") or {}
    expected_output_root = resolve_repo_path(config["output_root"], inside_candidate=True)
    expected_absent_targets = [str(attempt_root)]
    parent_records = generation_core.get("creatable_parent_records")
    if (
        set(generation_preflight)
        != {
            "schema_version",
            "created_at",
            "monotonic_ns",
            "status",
            "core",
            "core_sha256",
            "deterministic_preflight",
            "deterministic_preflight_sha256",
            "immediate_foreign_preflight",
            "immediate_foreign_preflight_sha256",
            "attempt_root_claim",
            "attempt_root_claim_sha256",
            "popen_is_next_state_changing_operation",
            "generation_preflight_sha256",
        }
        or set(deterministic_preflight)
        != {
            "schema_version",
            "created_at",
            "monotonic_ns",
            "status",
            "core",
            "core_sha256",
            "generation_preflight_sha256",
        }
        or generation_preflight.get("schema_version")
        != "androidworld_checklist_repair_generation_launch_preflight/v2"
        or generation_preflight.get("status") != "pass"
        or generation_preflight.get("core_sha256") != object_sha256(generation_core)
        or generation_preflight.get("deterministic_preflight_sha256")
        != deterministic_preflight.get("generation_preflight_sha256")
        or generation_preflight.get("immediate_foreign_preflight_sha256")
        != immediate_preflight.get("immediate_preflight_sha256")
        or generation_preflight.get("attempt_root_claim") != attempt_claim
        or generation_preflight.get("attempt_root_claim_sha256")
        != attempt_claim.get("claim_sha256")
        or generation_preflight.get("popen_is_next_state_changing_operation")
        is not True
        or deterministic_preflight.get("schema_version")
        != "androidworld_checklist_repair_generation_preflight/v1"
        or deterministic_preflight.get("status") != "pass"
        or deterministic_preflight.get("core") != generation_core
        or deterministic_preflight.get("core_sha256")
        != object_sha256(generation_core)
        or not isinstance(generation_preflight.get("monotonic_ns"), int)
        or isinstance(generation_preflight.get("monotonic_ns"), bool)
        or generation_preflight["monotonic_ns"]
        < immediate_preflight["monotonic_ns"]
        or summary.get("immediate_foreign_preflight") != immediate_preflight
        or generation_core.get("repair_id") != prelock["repair_id"]
        or generation_core.get("repair_prelock_sha256") != prelock["prelock_sha256"]
        or generation_core.get("repair_config_sha256") != config["config_sha256"]
        or generation_core.get("runner_command_template_sha256")
        != config["runner_command_sha256"]
        or generation_core.get("runner_execution_command_sha256")
        != object_sha256(
            expand_prelock_sha256(
                config["runner_command"],
                file_sha256=str(
                    getattr(
                        sys,
                        "_androidworld_isolated_bootstrap_prelock_file_sha256",
                        "",
                    )
                ),
                internal_sha256=prelock["prelock_sha256"],
            )
        )
        or generation_core.get("prelock_file_sha256_anchor")
        != getattr(
            sys, "_androidworld_isolated_bootstrap_prelock_file_sha256", None
        )
        or generation_core.get("prelock_internal_sha256_anchor")
        != prelock["prelock_sha256"]
        or generation_core.get("snapshot_exact_tree_hashes")
        != {
            name: descriptor["descriptor_sha256"]
            for name, descriptor in config["snapshot_exact_trees"].items()
        }
        or generation_core.get("isolated_bootstrap_sha256")
        != object_sha256(config["isolated_bootstrap"])
        or generation_core.get("python_runtime_sha256")
        != object_sha256(config["python_runtime"])
        or generation_core.get("runtime_source_snapshot_sha256")
        != config["runtime_source_snapshot_sha256"]
        or generation_core.get("candidate_case_order_sha256")
        != prelock["candidate_case_order_sha256"]
        or generation_core.get("repair_selection_order_sha256")
        != prelock["repair_selection_order_sha256"]
        or generation_core.get("repair_execution_order_sha256")
        != prelock["repair_execution_order_sha256"]
        or generation_core.get("repair_execution_plan_sha256")
        != prelock["repair_execution_plan_sha256"]
        or generation_core.get("expected_case_attempts_sha256")
        != audit_config["expected_case_attempts_sha256"]
        or generation_core.get("expected_case_ids") != prelock["repair_execution_order"]
        or generation_core.get("expected_case_count") != prelock["repair_count"]
        or generation_core.get("packet_root")
        != str(resolve_repo_path(config["packet_set_root"], inside_candidate=True))
        or generation_core.get("attempt_root") != str(attempt_root)
        or generation_core.get("attempt_layout")
        != {role: str(attempt_layout[role]) for role in ATTEMPT_LAYOUT_ROLES}
        or generation_core.get("attempt_namespace_sha256")
        != config["attempt_namespace"]["attempt_namespace_sha256"]
        or generation_core.get("output_root") != str(expected_output_root)
        or generation_core.get("absent_targets") != expected_absent_targets
        or not isinstance(parent_records, list)
        or [row.get("target") for row in parent_records if isinstance(row, Mapping)]
        != expected_absent_targets
        or any(
            not isinstance(row, Mapping)
            or row.get("writable") is not True
            or row.get("searchable") is not True
            or not isinstance(row.get("nearest_existing_ancestor"), str)
            for row in (parent_records or [])
        )
        or generation_core.get("frozen_bindings")
        != {
            "batch_runner": config["frozen_batch_runner"],
            "drafter": audit_config["frozen_drafter"],
            "repair_prompt": config["repair_prompt"],
            "outer_wrapper": audit_config["outer_wrapper_invocation"],
        }
        or generation_core.get("required_environment") != config["runner_environment"]
        or generation_core.get("required_environment_sha256")
        != config["runner_environment_sha256"]
        or generation_core.get("forbidden_environment_absent")
        != config["python_runtime"]["forbidden_child_python_environment"]
        or generation_core.get("foreign_process_preflight_sha256")
        != foreign_preflight["preflight_sha256"]
        or generation_core.get("codex_auth_pre_sha256")
        != object_sha256(dict(codex_auth_pre))
        or generation_core.get("no_files_created_by_preflight") is not True
    ):
        raise RepairPipelineError("deterministic generation preflight bindings are invalid")
    exact_gates = {
        "foreign_process_preflight_pass": (
            foreign_preflight.get("status") == "pass"
            and foreign_preflight.get("foreign_process_count") == 0
            and foreign_preflight.get("foreign_processes") == []
        ),
        "immediate_foreign_preflight_pass": (
            immediate_preflight.get("status") == "pass"
            and immediate_preflight.get("foreign_process_count") == 0
            and immediate_preflight.get("foreign_processes") == []
        ),
        "foreign_processes_absent_during_run": (
            summary.get("foreign_processes_seen_during_run") == []
        ),
        "monitor_error_free": summary.get("monitor_errors") == [],
        "sample_count_positive": len(rows) > 0,
        "observed_peak_equals_six": peak == EXPECTED_PARALLELISM,
        "at_least_one_six_way_overlap_sample": peak == EXPECTED_PARALLELISM
        and peak_count >= 1,
        "never_exceeded_six": peak <= EXPECTED_PARALLELISM,
        "all_repair_cases_observed": covered == expected_cases,
        "batch_returncode_zero": summary.get("batch_returncode") == 0,
        "batch_process_group_postflight_passed": (
            postflight.get("status") == "pass"
            and postflight.get("process_group_empty") is True
            and postflight.get("remaining_process_count") == 0
        ),
        "no_cleanup_required": (
            postflight.get("cleanup_was_required") is False
            and summary.get("cleanup_events") == []
        ),
    }
    if (
        summary.get("status") != "pass"
        or summary.get("repair_prelock_sha256") != prelock["prelock_sha256"]
        or summary.get("batch_runner_command_sha256") != config["runner_command_sha256"]
        or summary.get("batch_runner_execution_command_sha256")
        != generation_core.get("runner_execution_command_sha256")
        or summary.get("prelock_file_sha256_anchor")
        != generation_core.get("prelock_file_sha256_anchor")
        or summary.get("prelock_internal_sha256_anchor")
        != generation_core.get("prelock_internal_sha256_anchor")
        or summary.get("snapshot_exact_tree_hashes")
        != generation_core.get("snapshot_exact_tree_hashes")
        or summary.get("isolated_bootstrap_sha256")
        != generation_core.get("isolated_bootstrap_sha256")
        or summary.get("python_runtime_sha256")
        != generation_core.get("python_runtime_sha256")
        or summary.get("runtime_source_snapshot_sha256")
        != generation_core.get("runtime_source_snapshot_sha256")
        or summary.get("runner_environment") != config["runner_environment"]
        or summary.get("runner_environment_sha256")
        != config["runner_environment_sha256"]
        or summary.get("attempt_namespace_sha256")
        != config["attempt_namespace"]["attempt_namespace_sha256"]
        or summary.get("attempt_root_claim") != attempt_claim
        or summary.get("attempt_root_claim_sha256")
        != attempt_claim.get("claim_sha256")
        or summary.get("expected_case_attempts_sha256")
        != audit_config["expected_case_attempts_sha256"]
        or summary.get("repair_execution_plan") != audit_config["repair_execution_plan"]
        or summary.get("repair_execution_plan_sha256")
        != audit_config["repair_execution_plan_sha256"]
        or summary.get("execution_order_semantics")
        != audit_config["execution_order_semantics"]
        or summary.get("ps_binary") != audit_config["ps_binary"]
        or summary.get("ps_command") != audit_config["ps_command"]
        or summary.get("monitor_implementation") != audit_config["monitor_implementation"]
        or summary.get("outer_wrapper_invocation")
        != audit_config["outer_wrapper_invocation"]
        or summary.get("scope_rule") != audit_config["scope_rule"]
        or summary.get("sample_interval_milliseconds") != 100
        or summary.get("expected_case_count") != 80
        or len(expected_cases) != 80
        or summary.get("batch_returncode") != 0
        or summary.get("sample_count") != len(rows)
        or summary.get("observed_peak_active_case_attempts") != peak
        or summary.get("samples_at_observed_peak") != peak_count
        or summary.get("observed_case_count") != len(covered)
        or summary.get("observed_cases") != sorted(covered)
        or summary.get("missing_cases") != []
        or summary.get("extra_cases") != []
        or summary.get("failure_cleanup_policy") != audit_config["failure_cleanup"]
        or summary.get("cleanup_events") != []
        or summary.get("outer_wrapper_signal") is not None
        or foreign_preflight.get("status") != "pass"
        or set(foreign_preflight)
        != {
            "schema_version",
            "captured_at",
            "monotonic_ns",
            "ps_binary",
            "ps_command",
            "patterns",
            "excluded_runner_pid",
            "excluded_runner_ancestor_pids",
            "foreign_processes",
            "foreign_process_count",
            "status",
            "binding_policy",
            "preflight_sha256",
        }
        or foreign_preflight.get("binding_policy")
        != "foreign drafting processes must be absent before batch launch"
        or foreign_preflight.get("foreign_processes") != []
        or foreign_preflight.get("foreign_process_count") != 0
        or summary.get("foreign_processes_seen_during_run") != []
        or postflight.get("schema_version")
        != "androidworld_checklist_repair_batch_process_group_postflight/v1"
        or postflight.get("batch_pid") != summary.get("batch_pid")
        or postflight.get("process_group_id") != summary.get("batch_pid")
        or postflight.get("ps_binary") != audit_config["ps_binary"]
        or postflight.get("ps_command") != audit_config["ps_command"]
        or postflight.get("members_detected_before_cleanup") != []
        or postflight.get("member_count_before_cleanup") != 0
        or postflight.get("cleanup_was_required") is not False
        or postflight.get("remaining_processes") != []
        or postflight.get("remaining_process_count") != 0
        or postflight.get("process_group_empty") is not True
        or postflight.get("cleanup_failures") != []
        or summary.get("gates") != exact_gates
        or not all(exact_gates.values())
    ):
        raise RepairPipelineError("concurrency audit summary does not independently prove exact 6-way execution")
    return file_binding(summary_path) | {"audit_sha256": summary["audit_sha256"]}


def validate_and_record(
    prelock_path: Path,
    prelock: Mapping[str, Any],
    config: Mapping[str, Any],
    source: Mapping[str, Any],
    readonly_guard: Mapping[str, Any],
    concurrency_audit: Mapping[str, Any],
    codex_auth_pre: Mapping[str, Any],
    codex_auth_post: Mapping[str, Any],
    attempt_claim: Mapping[str, Any],
) -> dict[str, Any]:
    verified_concurrency = verify_concurrency_audit_evidence(
        config,
        prelock,
        concurrency_audit["summary"],
        codex_auth_pre,
    )
    output_root = resolve_repo_path(config["output_root"], inside_candidate=True)
    attempt_root, attempt_layout = _attempt_layout(config)
    verify_attempt_root_claim(
        attempt_claim,
        repair_id=prelock["repair_id"],
        attempt_root=attempt_root,
        expected_layout=attempt_layout,
        label="repair receipt attempt-root claim",
    )
    summary_path = output_root / "_batch_summary.json"
    results_path = output_root / "_batch_results.jsonl"
    summary = load_json(summary_path, "repair batch summary")
    execution_plan = list(prelock["repair_execution_plan"])
    plan_by_case = {row["case_unit_id"]: row for row in execution_plan}
    packet_sizes = {
        item["case_unit_id"]: Path(item["case_packet_path"]).stat().st_size
        for item in config["concurrency_audit"]["expected_case_attempts"]
    }
    lane_sizes = {
        lane: [
            packet_sizes[row["case_unit_id"]]
            for row in execution_plan
            if row["lane"] == lane
        ]
        for lane in ("regular", "oversized")
    }
    expected_lane_stats = {
        lane: {
            "count": len(sizes),
            "min_bytes": min(sizes) if sizes else 0,
            "max_bytes": max(sizes) if sizes else 0,
        }
        for lane, sizes in lane_sizes.items()
    }
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
        "sort_by": "name",
        "large_case_threshold_bytes": REPAIR_LARGE_CASE_THRESHOLD_BYTES,
        "lane_stats": expected_lane_stats,
    }
    for field, wanted in expected.items():
        if summary.get(field) != wanted:
            raise RepairPipelineError(f"repair batch summary {field}={summary.get(field)!r}, expected {wanted!r}")
    records_list = load_jsonl(results_path)
    records: dict[str, dict[str, Any]] = {}
    completion_index_by_case: dict[str, int] = {}
    for completion_index, record in enumerate(records_list):
        case_id = str(record.get("case_unit_dir") or "")
        if case_id in records:
            raise RepairPipelineError(f"duplicate repair batch record: {case_id}")
        records[case_id] = record
        completion_index_by_case[case_id] = completion_index
    raw_batch_completion_order = [str(record.get("case_unit_dir") or "") for record in records_list]
    expected_cases = {row["case_unit_id"] for row in prelock["repair_inputs"]}
    observed_dirs = {path.name for path in output_root.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if set(records) != expected_cases or observed_dirs != expected_cases:
        raise RepairPipelineError("repair output/results case set differs from prelock")
    source_wave = resolve_repo_path(prelock["source_draft"]["raw_wave"], inside_candidate=True)
    input_by_case = {row["case_unit_id"]: row for row in prelock["repair_inputs"]}
    provenance_rows: list[dict[str, Any]] = []
    expected_attempt_by_case = {
        row["case_unit_id"]: row
        for row in config["concurrency_audit"]["expected_case_attempts"]
    }
    for case_id in prelock["repair_execution_order"]:
        record = records[case_id]
        plan_row = plan_by_case[case_id]
        expected_attempt = expected_attempt_by_case[case_id]
        if record.get("status") != "success" or record.get("quality_warnings") not in ([], None):
            raise RepairPipelineError(f"{case_id} repair batch record is not clean success")
        if (
            record.get("case_packet") != str(Path(expected_attempt["case_packet_path"]))
            or record.get("case_packet_size_bytes") != packet_sizes[case_id]
            or record.get("lane") != plan_row["lane"]
        ):
            raise RepairPipelineError(
                f"{case_id} raw batch record differs from its frozen execution-plan row"
            )
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
        write_json_create_once(diff_path, diff)
        inputs = input_by_case[case_id]
        provenance = {
            "schema_version": "androidworld_checklist_repair_provenance/v1",
            "created_at": utc_now(),
            "repair_id": prelock["repair_id"],
            "case_unit_id": case_id,
            "task_id": case_id,
            "selection_rank": inputs["selection_rank"],
            "execution_rank": plan_row["execution_rank"],
            "execution_lane": plan_row["lane"],
            "raw_batch_completion_rank": completion_index_by_case[case_id],
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
        write_json_create_once(provenance_path, provenance)
        provenance_rows.append(
            {
                "selection_rank": inputs["selection_rank"],
                "execution_rank": plan_row["execution_rank"],
                "execution_lane": plan_row["lane"],
                "raw_batch_completion_rank": completion_index_by_case[case_id],
                "case_unit_id": case_id,
                "provenance": file_binding(provenance_path)
                | {"provenance_sha256": provenance["provenance_sha256"]},
                "output_checklist": file_binding(case_dir / "checklist.yaml"),
            }
        )
    provenance_rows.sort(key=lambda row: row["execution_rank"])
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
        "runner_command_template_sha256": config["runner_command_sha256"],
        "runner_execution_command_sha256": concurrency_audit[
            "batch_runner_execution_command_sha256"
        ],
        "prelock_file_sha256_anchor": concurrency_audit[
            "prelock_file_sha256_anchor"
        ],
        "prelock_internal_sha256_anchor": concurrency_audit[
            "prelock_internal_sha256_anchor"
        ],
        "snapshot_exact_trees": config["snapshot_exact_trees"],
        "snapshot_exact_trees_sha256": config["snapshot_exact_trees_sha256"],
        "runtime_source_snapshot": config["runtime_source_snapshot"],
        "runtime_source_snapshot_sha256": config[
            "runtime_source_snapshot_sha256"
        ],
        "attempt_namespace": config["attempt_namespace"],
        "attempt_namespace_sha256": config["attempt_namespace"][
            "attempt_namespace_sha256"
        ],
        "attempt_root_claim": dict(attempt_claim),
        "attempt_root_claim_sha256": attempt_claim["claim_sha256"],
        "runner_environment": config["runner_environment"],
        "runner_environment_sha256": config["runner_environment_sha256"],
        "isolated_bootstrap": config["isolated_bootstrap"],
        "isolated_bootstrap_sha256": object_sha256(config["isolated_bootstrap"]),
        "repair_readonly_guard": readonly_guard["guard"],
        "repair_readonly_post_snapshot": readonly_guard["post_snapshot"],
        "concurrency_audit": verified_concurrency,
        "outer_wrapper_invocation": concurrency_audit["outer_wrapper_invocation"],
        "concurrency_samples": concurrency_audit["samples"],
        "expected_case_attempts_sha256": config["concurrency_audit"][
            "expected_case_attempts_sha256"
        ],
        "candidate_case_order_sha256": prelock["candidate_case_order_sha256"],
        "repair_selection_order_sha256": prelock["repair_selection_order_sha256"],
        "repair_execution_order": prelock["repair_execution_order"],
        "repair_execution_order_sha256": prelock["repair_execution_order_sha256"],
        "repair_execution_plan": execution_plan,
        "repair_execution_plan_sha256": prelock["repair_execution_plan_sha256"],
        "order_semantics": REPAIR_ORDER_SEMANTICS,
        "raw_batch_completion_order": raw_batch_completion_order,
        "raw_batch_completion_order_sha256": object_sha256(raw_batch_completion_order),
        "batch_process_group_postflight": concurrency_audit[
            "batch_process_group_postflight"
        ],
        "foreign_process_preflight": concurrency_audit["foreign_process_preflight"],
        "immediate_foreign_preflight": concurrency_audit[
            "immediate_foreign_preflight"
        ],
        "foreign_processes_seen_during_run": concurrency_audit[
            "foreign_processes_seen_during_run"
        ],
        "generation_preflight": concurrency_audit["generation_preflight"],
        "python_runtime_sha256": object_sha256(config["python_runtime"]),
        "model_request_id": config["model"],
        "model_version_claim": config["model_version_claim"],
        "model_version_note": config["model_version_note"],
        "codex_auth_pre": dict(codex_auth_pre),
        "codex_auth_post": dict(codex_auth_post),
        "codex_auth_checks_sha256": object_sha256(
            {"pre": dict(codex_auth_pre), "post": dict(codex_auth_post)}
        ),
        "codex_login_path_alias_warnings": {
            "pre": {
                "present": codex_auth_pre.get(
                    "login_path_alias_warning_present"
                ),
                "sha256": codex_auth_pre.get(
                    "login_path_alias_warning_sha256"
                ),
            },
            "post": {
                "present": codex_auth_post.get(
                    "login_path_alias_warning_present"
                ),
                "sha256": codex_auth_post.get(
                    "login_path_alias_warning_sha256"
                ),
            },
        },
        "observed_peak_active_case_attempts": concurrency_audit[
            "observed_peak_active_case_attempts"
        ],
        "all_repair_cases_observed_by_concurrency_audit": concurrency_audit["gates"][
            "all_repair_cases_observed"
        ],
        "case_provenance": provenance_rows,
        "case_provenance_sha256": object_sha256(provenance_rows),
        "effective_wave_required": True,
        "strict_effective_qc_required": True,
        "new_independent_codex_semantic_reviews_required": True,
        "explicit_root_agent_acceptance_required": True,
    }
    repair_summary = add_self_hash(repair_summary, "receipt_sha256")
    receipt_path = output_root / "_repair_batch_receipt.json"
    write_json_create_once(receipt_path, repair_summary)
    return repair_summary


def gate_self_test(prelock_path: Path) -> int:
    """Exercise the P0 environment/namespace gates via a real prelock bootstrap."""

    prelock = load_json(prelock_path, "gate self-test prelock")
    verify_internal_hash(prelock, ("prelock_sha256",), "gate self-test prelock")
    if (
        getattr(sys, "_androidworld_isolated_bootstrap_admission", None)
        != prelock["prelock_sha256"]
        or getattr(
            sys, "_androidworld_isolated_bootstrap_prelock_file_sha256", None
        )
        != sha256_file(prelock_path)
    ):
        raise RepairPipelineError(
            "gate self-test was not admitted by its actual prelock bootstrap"
        )
    config_path = verify_file_binding(
        prelock["repair_config"], "gate self-test config", inside_candidate=True
    )
    config = load_json(config_path, "gate self-test config")
    verify_internal_hash(config, ("config_sha256",), "gate self-test config")
    environment = verify_closed_child_environment(
        config["runner_environment"], "gate self-test environment"
    )
    if dict(os.environ) != environment:
        raise RepairPipelineError(
            "gate self-test process did not receive exact environment equality"
        )
    extra_environment = dict(environment)
    extra_environment["OPENAI_API_KEY"] = "must-not-pass"
    try:
        verify_closed_child_environment(
            extra_environment, "gate self-test injected environment"
        )
    except RepairPipelineError:
        extra_environment_rejected = True
    else:
        extra_environment_rejected = False
    if not extra_environment_rejected:
        raise RepairPipelineError("extra child environment key was accepted")
    if (
        "--appworld-v56-runtime-gate" in list(config.get("runner_command") or [])
        or (config.get("concurrency_audit") or {}).get(
            "appworld_v56_runtime_gate"
        )
        is not False
        or (config.get("attempt_namespace") or {}).get(
            "appworld_v56_runtime_gate"
        )
        is not False
    ):
        raise RepairPipelineError(
            "AndroidWorld gate self-test found the AppWorld-only runtime flag"
        )

    popen_calls: list[list[str]] = []
    original_popen = subprocess.Popen

    def forbidden_popen(*args: Any, **kwargs: Any) -> Any:
        del kwargs
        popen_calls.append(list(args[0]) if args else [])
        raise AssertionError("Popen must not run during namespace-claim tests")

    subprocess.Popen = forbidden_popen
    lease: AttemptRootLease | None = None
    try:
        lease = claim_attempt_root(config, prelock)
        lease.verify("gate self-test initial lease")
        try:
            claim_attempt_root(config, prelock)
        except RunNamespaceClaimError:
            claim_competition_rejected = True
        else:
            claim_competition_rejected = False
        if not claim_competition_rejected or popen_calls:
            raise RepairPipelineError(
                "attempt-root claim competition was not rejected with Popen=0"
            )

        scratch = lease.layout["scratch"]
        wave = lease.layout["wave"]
        replacement = scratch / "replacement"
        original = scratch / "original_wave"
        os.mkdir(replacement, mode=0o700)
        os.rename(wave, original)
        os.rename(replacement, wave)
        try:
            lease.verify("gate self-test replaced wave inode")
        except RepairPipelineError:
            replaced_inode_rejected = True
        else:
            replaced_inode_rejected = False
        if not replaced_inode_rejected:
            raise RepairPipelineError("replaced attempt subdirectory inode was accepted")

        os.rmdir(wave)
        os.symlink(str(original), wave)
        try:
            lease.verify("gate self-test symlinked wave")
        except RepairPipelineError:
            symlink_rejected = True
        else:
            symlink_rejected = False
        if not symlink_rejected:
            raise RepairPipelineError("symlinked attempt subdirectory was accepted")
    finally:
        subprocess.Popen = original_popen
        if lease is not None:
            lease.close()
    print(
        json.dumps(
            {
                "status": "gate_self_test_pass",
                "actual_prelock_bootstrap": True,
                "closed_environment_key_count": len(environment),
                "extra_environment_rejected": extra_environment_rejected,
                "claim_competition_rejected": claim_competition_rejected,
                "claim_competition_popen_calls": len(popen_calls),
                "replaced_inode_rejected": replaced_inode_rejected,
                "symlink_rejected": symlink_rejected,
                "appworld_v56_runtime_gate": False,
            },
            indent=2,
        )
    )
    return 0


def self_test_outer_postflight_failure_cleanup() -> dict[str, Any]:
    """Inject a postflight-observation exception and prove the real PGID dies."""

    validation_root = WORK_ROOT / "repair_generation" / "validation"
    validation_root.mkdir(parents=True, exist_ok=True)
    observed_pid: list[int] = []
    original_inner = globals()["_run_with_concurrency_audit_inner"]

    def injected_postflight_ps_failure(
        process: subprocess.Popen[Any],
        *,
        config: Mapping[str, Any],
        prelock: Mapping[str, Any],
        foreign_preflight: Mapping[str, Any],
        generation_preflight: Mapping[str, Any],
        signal_state: Mapping[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        del config, prelock, foreign_preflight, generation_preflight, signal_state
        observed_pid.append(process.pid)
        # Let the shell create its sleeping child in the new process group.
        time.sleep(0.15)
        raise RepairPipelineError(
            "synthetic batch process-group postflight /bin/ps exception"
        )

    with tempfile.TemporaryDirectory(
        prefix="repair_outer_cleanup_selftest_", dir=validation_root
    ) as raw_temp:
        temp_root = Path(raw_temp)
        samples_path = temp_root / "samples.jsonl"
        summary_path = temp_root / "summary.json"
        audit = {
            "sample_interval_milliseconds": 100,
            "ps_binary": {"invocation_path": "/bin/ps", "test_fixture": True},
            "ps_command": ["/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,command="],
            "monitor_implementation": {"test_fixture": True},
            "outer_wrapper_invocation": {"test_fixture": True},
            "batch_runner_command_sha256": object_sha256(["outer-cleanup-self-test"]),
            "foreign_process_patterns": [
                "__repair_outer_cleanup_selftest_no_match__"
            ],
            "expected_case_attempts": [],
            "expected_case_attempts_sha256": object_sha256([]),
            "scope_rule": "self-test injected postflight observation failure",
            "samples_path": repo_relative(samples_path),
            "summary_path": repo_relative(summary_path),
            "failure_cleanup": {
                "scope": "batch_process_group",
                "term_signal": "SIGTERM",
                "term_grace_seconds": 1,
                "kill_signal": "SIGKILL",
                "kill_wait_seconds": 2,
            },
        }
        config = {"concurrency_audit": audit}
        prelock = {
            "repair_id": "outer_cleanup_self_test",
            "prelock_sha256": "0" * 64,
        }
        foreign_preflight = foreign_drafting_preflight(config)
        generation_core: dict[str, Any] = {}
        generation_preflight = add_self_hash(
            {
                "schema_version": "androidworld_checklist_repair_generation_preflight/v1",
                "created_at": utc_now(),
                "monotonic_ns": time.monotonic_ns(),
                "status": "pass",
                "core": generation_core,
                "core_sha256": object_sha256(generation_core),
            },
            "generation_preflight_sha256",
        )
        globals()["_run_with_concurrency_audit_inner"] = injected_postflight_ps_failure
        evidence: dict[str, Any] | None = None
        try:
            try:
                _run_after_verified_generation_preflight(
                    ["/bin/sh", "-c", "trap '' TERM; sleep 60 & wait"],
                    config=config,
                    prelock=prelock,
                    environment={"PATH": "/usr/bin:/bin"},
                    foreign_preflight=foreign_preflight,
                    generation_preflight=generation_preflight,
                )
            except AuditedRepairRunFailure as exc:
                returncode = -1
                evidence = {
                    "status": "fail",
                    "batch_pid": exc.batch_pid,
                    "batch_process_group_postflight": exc.process_group_postflight,
                    "cleanup_events": [exc.cleanup_event],
                    "gates": {"no_cleanup_required": False},
                }
            else:
                raise RepairPipelineError(
                    "outer cleanup self-test unexpectedly returned success"
                )
        finally:
            globals()["_run_with_concurrency_audit_inner"] = original_inner
            if observed_pid:
                batch_pid = observed_pid[0]
                try:
                    rows = observe_process_rows(audit, "outer-cleanup self-test final check")
                    leftovers = process_group_members(rows, batch_pid)
                except BaseException:
                    leftovers = [{"pgid": batch_pid}]
                if leftovers:
                    try:
                        os.killpg(batch_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    raise RepairPipelineError(
                        f"outer cleanup self-test left process group {batch_pid}: {leftovers}"
                    )
        assert evidence is not None
        postflight = evidence.get("batch_process_group_postflight") or {}
        events = evidence.get("cleanup_events") or []
        if (
            returncode != -1
            or evidence.get("status") != "fail"
            or not isinstance(evidence.get("batch_pid"), int)
            or evidence.get("batch_pid") != observed_pid[0]
            or postflight.get("status") != "fail"
            or postflight.get("cleanup_was_required") is not True
            or postflight.get("process_group_empty") is not True
            or postflight.get("remaining_processes") != []
            or postflight.get("cleanup_failures") != []
            or len(events) != 1
            or "sigterm_sent" not in events[0]
            or "sigkill_sent" not in events[0]
            or events[0].get("process_group_empty_after_cleanup") is not True
            or events[0].get("post_reap_observation_count", 0) < 2
            or events[0].get("post_reap_consecutive_empty_observations", 0) < 2
            or evidence.get("gates", {}).get("no_cleanup_required") is not False
        ):
            raise RepairPipelineError(
                "outer cleanup self-test did not preserve audited fail evidence"
            )
        return {
            "batch_pid": observed_pid[0],
            "term_attempted": True,
            "kill_attempted": True,
            "process_group_empty": True,
            "fail_evidence_recorded": True,
        }


def self_test_outer_signal_cleanup(test_signal: signal.Signals) -> dict[str, Any]:
    """Signal the real outer wrapper and prove its six-child PGID is empty."""

    validation_root = WORK_ROOT / "repair_generation" / "validation"
    validation_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f"repair_{test_signal.name.lower()}_cleanup_selftest_", dir=validation_root
    ) as raw_temp:
        temp_root = Path(raw_temp)
        samples_path = temp_root / "samples.jsonl"
        summary_path = temp_root / "summary.json"
        drafter_fixture = file_binding(Path(__file__).resolve())
        audit = {
            "sample_interval_milliseconds": 50,
            "ps_binary": {"invocation_path": "/bin/ps", "test_fixture": True},
            "ps_command": ["/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,command="],
            "monitor_implementation": {"test_fixture": True},
            "outer_wrapper_invocation": {"test_fixture": True},
            "batch_runner_command_sha256": object_sha256(
                [f"{test_signal.name.lower()}-cleanup-self-test"]
            ),
            "expected_case_attempts": [],
            "expected_case_attempts_sha256": object_sha256([]),
            "repair_execution_plan": [],
            "repair_execution_plan_sha256": object_sha256([]),
            "execution_order_semantics": "self-test",
            "scope_rule": "self-test six inert child processes",
            "samples_path": repo_relative(samples_path),
            "summary_path": repo_relative(summary_path),
            "frozen_drafter": drafter_fixture,
            "foreign_process_patterns": [
                f"__repair_{test_signal.name.lower()}_selftest_no_match__"
            ],
            "failure_cleanup": {
                "scope": "batch_process_group",
                "term_signal": "SIGTERM",
                "term_grace_seconds": 1,
                "kill_signal": "SIGKILL",
                "kill_wait_seconds": 2,
            },
        }
        config = {"concurrency_audit": audit}
        prelock = {
            "repair_id": f"{test_signal.name.lower()}_cleanup_self_test",
            "prelock_sha256": "0" * 64,
        }
        foreign_preflight = foreign_drafting_preflight(config)
        generation_core: dict[str, Any] = {}
        generation_preflight = add_self_hash(
            {
                "schema_version": "androidworld_checklist_repair_generation_preflight/v1",
                "created_at": utc_now(),
                "monotonic_ns": time.monotonic_ns(),
                "status": "pass",
                "core": generation_core,
                "core_sha256": object_sha256(generation_core),
            },
            "generation_preflight_sha256",
        )
        original_handlers = {
            item: signal.getsignal(item)
            for item in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
        }
        original_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        sender = threading.Thread(
            target=lambda: (time.sleep(0.35), os.kill(os.getpid(), test_signal)),
            name=f"repair-{test_signal.name.lower()}-selftest-sender",
            daemon=False,
        )
        sender.start()
        evidence: dict[str, Any] | None = None
        try:
            _returncode, evidence = _run_after_verified_generation_preflight(
                [
                    "/bin/sh",
                    "-c",
                    "trap '' TERM; sleep 60 & sleep 60 & sleep 60 & sleep 60 & sleep 60 & sleep 60 & wait",
                ],
                config=config,
                prelock=prelock,
                environment={"PATH": "/usr/bin:/bin"},
                foreign_preflight=foreign_preflight,
                generation_preflight=generation_preflight,
            )
        finally:
            sender.join(timeout=5)
        assert evidence is not None
        batch_pid = evidence.get("batch_pid")
        if not isinstance(batch_pid, int):
            raise RepairPipelineError(f"{test_signal.name} cleanup self-test has no batch PID")
        leftovers = process_group_members(
            observe_process_rows(
                audit, f"{test_signal.name} cleanup self-test final check"
            ),
            batch_pid,
        )
        restored_handlers = all(
            signal.getsignal(item) == old for item, old in original_handlers.items()
        )
        restored_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set()) == original_mask
        wrapper_signal = evidence.get("outer_wrapper_signal") or {}
        cleanup_events = evidence.get("cleanup_events") or []
        if (
            evidence.get("status") != "fail"
            or wrapper_signal.get("signal_name") != test_signal.name
            or not wrapper_signal.get("received")
            or evidence.get("batch_returncode") == 0
            or not cleanup_events
            or any(
                event.get("process_group_empty_after_cleanup") is not True
                or event.get("post_reap_observation_count", 0) < 2
                or event.get("post_reap_consecutive_empty_observations", 0) < 2
                for event in cleanup_events
            )
            or leftovers != []
            or not restored_handlers
            or not restored_mask
        ):
            if leftovers:
                try:
                    os.killpg(batch_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            raise RepairPipelineError(
                f"{test_signal.name} outer-wrapper cleanup did not produce fail evidence "
                "and an empty PGID"
            )
        return {
            "signal": test_signal.name,
            "batch_pid": batch_pid,
            "simulated_concurrent_children": 6,
            "process_group_empty": True,
            "continuing_child_processes": 0,
            "fail_evidence_recorded": True,
            "original_handlers_restored": True,
            "original_signal_mask_restored": True,
        }


def self_test_exact_tree_and_isolated_bootstrap() -> dict[str, Any]:
    """Exercise namespace injection, dual anchors, and nested child isolation."""

    validation_root = WORK_ROOT / "repair_generation" / "validation"
    validation_root.mkdir(parents=True, exist_ok=True)

    def write_text(path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(value)

    def write_manifest(root: Path, name: str) -> Path:
        payload = add_self_hash(
            {
                "schema_version": "androidworld_exact_tree_selftest_manifest/v1",
                "name": name,
            },
            "snapshot_sha256",
        )
        path = root / "snapshot_manifest.json"
        write_json_create_once(path, payload)
        return path

    def absolute_file_binding(path: Path) -> dict[str, Any]:
        resolved = path.resolve(strict=True)
        return {
            "path": str(resolved),
            "sha256": sha256_file(resolved),
            "size_bytes": resolved.stat().st_size,
        }

    def make_runtime_source_fixture(
        live_source: Path, repair_root: Path
    ) -> tuple[dict[str, Any], Path, Path]:
        before = canonical_runtime_tree(live_source)
        content_id = object_sha256(before["entries"])
        content_root = repair_root / "runtime_source" / content_id
        snapshot_root = content_root / "src"
        content_root.mkdir(parents=True)
        shutil.copytree(live_source, snapshot_root, copy_function=shutil.copy2)
        after = canonical_runtime_tree(live_source)
        copied = canonical_runtime_tree(snapshot_root)
        if before != after or before["entries"] != copied["entries"]:
            raise RepairPipelineError("self-test runtime source fixture copy changed")
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
        record = add_self_hash(
            {
                "schema_version": RUNTIME_SOURCE_SNAPSHOT_SCHEMA,
                "source_root_absolute_path": str(live_source),
                "content_root_absolute_path": str(content_root),
                "snapshot_root_absolute_path": str(snapshot_root),
                "source_entry_count": copied["entry_count"],
                "source_regular_file_count": copied["regular_file_count"],
                "source_directory_count": copied["directory_count"],
                "source_total_regular_file_bytes": copied[
                    "total_regular_file_bytes"
                ],
                "source_pre_tree_sha256": before["tree_sha256"],
                "source_post_tree_sha256": after["tree_sha256"],
                "snapshot_tree_sha256": copied["tree_sha256"],
                "source_content_id_sha256": content_id,
                "source_pre_tree": before,
                "source_post_tree": after,
                "snapshot_tree": copied,
                "bytecode_file_count": len(bytecode_files),
                "bytecode_files_sha256": object_sha256(bytecode_files),
                "bytecode_policy": (
                    "copy and bind every pre-existing .pyc/.pyo byte; create no new "
                    "bytecode; reject every post-freeze namespace or byte change"
                ),
                "copy_policy": (
                    "pre-index live repo/src, copy every directory and regular file with "
                    "copy2, then require source post-index and snapshot index to equal the "
                    "pre-index"
                ),
                "source_endpoint_equality_required": True,
                "source_endpoint_equality_observed": True,
                "snapshot_all_bytes_equal_source": True,
                "snapshot_symlink_count": 0,
                "live_source_excluded_from_runtime_sys_path": True,
                "sys_path_substitution": {
                    "captured_live_editable_path": str(live_source),
                    "frozen_snapshot_path": str(snapshot_root),
                    "required_replacement_count": 1,
                    "live_path_allowed_after_substitution": False,
                },
                "live_editable_pth_policy": (
                    "never execute site or editable-install .pth files in generation; bind "
                    "their capture-time effect explicitly by replacing only live repo/src "
                    "with runtime_src"
                ),
                "outer_and_nested_preimport_verification_required": True,
                "staged_copy_promoted_atomically": True,
                "staging_policy": (
                    "copy and compare under a hidden sibling; write a create-once manifest; "
                    "atomically rename to the canonical-entry SHA-256 content address"
                ),
                "post_freeze_live_source_drift_nonbinding": True,
                "dont_write_bytecode_required": True,
                "threat_model_limit": (
                    "pre/post endpoint equality and copied-byte equality reject ordinary "
                    "concurrent drift but cannot prove absence of malicious modify-and-restore "
                    "activity inside the capture interval"
                ),
            },
            "runtime_source_snapshot_sha256",
        )
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
                "schema_version": (
                    "androidworld_repair_runtime_source_snapshot_manifest/v1"
                ),
                "repair_id": "selftest",
                "source_content_id_sha256": content_id,
                "runtime_source_snapshot": record,
                "files": source_files,
                "file_count": len(source_files),
                "files_sha256": object_sha256(source_files),
            },
            "snapshot_manifest_sha256",
        )
        manifest_path = content_root / "snapshot_manifest.json"
        write_json_create_once(manifest_path, manifest)
        return record, manifest_path, snapshot_root

    def expect_tree_rejection(
        descriptor: Mapping[str, Any], label: str
    ) -> None:
        try:
            verify_exact_snapshot_tree_descriptor(descriptor, label)
        except RepairPipelineError:
            return
        raise RepairPipelineError(f"{label} exact-tree injection was accepted")

    def run_child(command: list[str]) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        for variable in runtime["forbidden_child_python_environment"]:
            environment.pop(variable, None)
        environment.update(runtime["required_environment"])
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            env=environment,
        )

    with tempfile.TemporaryDirectory(
        prefix="repair_exact_tree_bootstrap_selftest_", dir=validation_root
    ) as raw_temp:
        temp_root = Path(raw_temp)
        fixture_repo = temp_root / "repository"
        live_source_root = fixture_repo / "src"
        repair_root = fixture_repo / "work" / "repair_snapshot"
        source_root = fixture_repo / "work" / "source_snapshot"
        marker_root = fixture_repo / "work" / "markers"
        marker_root.mkdir(parents=True)
        repair_script = repair_root / "scripts" / "runner.py"
        batch_script = source_root / "scripts" / "run_draft_batch.py"
        drafter_script = source_root / "scripts" / "draft_case_checklist.py"
        validator_script = source_root / "scripts" / "checklist_validator.py"
        other_script = source_root / "scripts" / "other.py"
        write_text(
            repair_script,
            "import sys\nwith open(sys.argv[1], 'x', encoding='utf-8') as h: h.write('outer')\n",
        )
        write_text(
            drafter_script,
            "import sys\nwith open(sys.argv[1], 'x', encoding='utf-8') as h: h.write('nested')\n",
        )
        write_text(validator_script, "pass\n")
        write_text(
            other_script,
            "import sys\nwith open(sys.argv[1], 'x', encoding='utf-8') as h: h.write('forbidden')\n",
        )
        write_text(
            batch_script,
            (
                "import subprocess, sys\n"
                "target = sys.argv[2] if sys.argv[1] == 'allowed' else sys.argv[3]\n"
                "subprocess.run([sys.executable, target, sys.argv[4]], check=True)\n"
            ),
        )
        write_text(live_source_root / "fixture_module.py", "VALUE = 'frozen'\n")
        write_text(
            live_source_root / "cache" / "orphan.cpython-999.pyc",
            "pre-existing bytecode bytes",
        )
        (
            runtime_source_snapshot,
            runtime_source_manifest,
            runtime_source_root,
        ) = make_runtime_source_fixture(live_source_root, repair_root)
        repair_manifest = write_manifest(repair_root, "repair")
        source_manifest = write_manifest(source_root, "source")
        repair_tree = exact_snapshot_tree_descriptor(
            repair_root,
            label="selftest_repair_snapshot",
            manifest_path=repair_manifest,
            manifest_self_hash_field="snapshot_sha256",
        )
        source_tree = exact_snapshot_tree_descriptor(
            source_root,
            label="selftest_source_snapshot",
            manifest_path=source_manifest,
            manifest_self_hash_field="snapshot_sha256",
        )
        runtime_source_tree = exact_snapshot_tree_descriptor(
            Path(runtime_source_snapshot["content_root_absolute_path"]),
            label="selftest_runtime_source_snapshot",
            manifest_path=runtime_source_manifest,
            manifest_self_hash_field="snapshot_manifest_sha256",
        )
        verify_exact_snapshot_tree_descriptor(repair_tree, "selftest repair positive")
        verify_exact_snapshot_tree_descriptor(source_tree, "selftest source positive")
        verify_exact_snapshot_tree_descriptor(
            runtime_source_tree, "selftest runtime source positive"
        )

        injections: list[tuple[str, Path]] = []
        extra_json = repair_root / "scripts" / "json.py"
        write_text(extra_json, "raise RuntimeError('must never import')\n")
        expect_tree_rejection(repair_tree, "extra json.py")
        extra_json.unlink()
        injections.append(("extra_json_py", extra_json))

        cache_dir = repair_root / "scripts" / "__pycache__"
        cache_file = cache_dir / "evil.cpython-312.pyc"
        write_text(cache_file, "not bytecode")
        expect_tree_rejection(repair_tree, "extra nested pyc")
        shutil.rmtree(cache_dir)
        injections.append(("extra_nested_pyc", cache_file))

        empty_dir = repair_root / "scripts" / "extra_package" / "nested"
        empty_dir.mkdir(parents=True)
        expect_tree_rejection(repair_tree, "extra empty directory")
        shutil.rmtree(repair_root / "scripts" / "extra_package")
        injections.append(("extra_directory", empty_dir))

        symlink = repair_root / "scripts" / "linked_runner.py"
        symlink.symlink_to(repair_script)
        expect_tree_rejection(repair_tree, "extra symlink")
        symlink.unlink()
        injections.append(("extra_symlink", symlink))
        verify_exact_snapshot_tree_descriptor(repair_tree, "selftest repair restored")

        original_sys_path = list(sys.path)
        live_project_source = Path(os.path.abspath(REPO_ROOT / "src"))
        replacement_count = 0
        rewritten_sys_path: list[str] = []
        for entry in original_sys_path:
            if entry and Path(os.path.abspath(entry)) == live_project_source:
                rewritten_sys_path.append(str(runtime_source_root))
                replacement_count += 1
            else:
                rewritten_sys_path.append(entry)
        if replacement_count != 1:
            raise RepairPipelineError(
                "self-test could not replace exactly one live editable source path"
            )
        try:
            sys.path[:] = rewritten_sys_path
            runtime = python_runtime_binding(
                expected_runner_script_directory=repair_script.parent,
                codex_invocation_path=Path("/opt/homebrew/bin/codex"),
                execution_requires_isolated_bootstrap=True,
            )
        finally:
            sys.path[:] = original_sys_path
        exact_trees = {
            "repair": repair_tree,
            "source_v3": source_tree,
            "runtime_source": runtime_source_tree,
        }
        verify_runtime_source_snapshot_binding(
            runtime_source_snapshot,
            "self-test runtime source binding",
            runtime=runtime,
            repair_exact_tree=repair_tree,
            runtime_source_exact_tree=runtime_source_tree,
            expected_source_root=live_source_root,
        )
        bootstrap = isolated_bootstrap_record()
        config = add_self_hash(
            {
                "schema_version": "androidworld_isolated_bootstrap_selftest_config/v1",
                "snapshot_exact_trees": exact_trees,
                "runtime_source_snapshot": runtime_source_snapshot,
                "isolated_bootstrap": bootstrap,
                "python_runtime": runtime,
            },
            "config_sha256",
        )
        config_path = fixture_repo / "work" / "config.json"
        write_json_create_once(config_path, config)
        prelock = add_self_hash(
            {
                "schema_version": "androidworld_isolated_bootstrap_selftest_prelock/v1",
                "repair_id": "selftest",
                "repository_root_absolute": str(fixture_repo),
                "repair_config": absolute_file_binding(config_path)
                | {"config_sha256": config["config_sha256"]},
                "snapshot_exact_trees": exact_trees,
                "runtime_source_snapshot": runtime_source_snapshot,
                "isolated_bootstrap": bootstrap,
                "runner_execution": {"python_runtime": runtime},
                "repair_tool_bindings": {
                    "repair_runner": absolute_file_binding(repair_script)
                },
                "original_v3_tool_bindings": {
                    "batch_runner": absolute_file_binding(batch_script),
                    "drafter": absolute_file_binding(drafter_script),
                    "validator": absolute_file_binding(validator_script),
                },
            },
            "prelock_sha256",
        )
        prelock_path = fixture_repo / "work" / "prelock.json"
        write_json_create_once(prelock_path, prelock)
        physical_sha256 = sha256_file(prelock_path)
        internal_sha256 = prelock["prelock_sha256"]
        if physical_sha256 == internal_sha256:
            raise RepairPipelineError("self-test physical/internal prelock hashes collided")

        def command(mode: str, target: Path, args: list[str]) -> list[str]:
            return isolated_bootstrap_command(
                runtime=runtime,
                prelock_path=prelock_path,
                prelock_file_sha256=physical_sha256,
                prelock_internal_sha256=internal_sha256,
                repair_tree_sha256=repair_tree["descriptor_sha256"],
                source_tree_sha256=source_tree["descriptor_sha256"],
                runtime_source_tree_sha256=runtime_source_tree["descriptor_sha256"],
                mode=mode,
                target=target,
                target_args=args,
            )

        original_runtime_source_manifest_bytes = runtime_source_manifest.read_bytes()
        original_runtime_source_manifest = load_json(
            runtime_source_manifest, "self-test runtime source manifest"
        )
        runtime_source_manifest_semantic_tampers_rejected: list[str] = []
        for tamper_name in ("files", "file_count", "files_sha256"):
            tampered_manifest = json.loads(
                json.dumps(original_runtime_source_manifest)
            )
            if tamper_name == "files":
                tampered_files = list(tampered_manifest["files"])
                if not tampered_files:
                    raise RepairPipelineError(
                        "runtime source manifest semantic self-test has no files"
                    )
                tampered_files[0] = {
                    **tampered_files[0],
                    "sha256": "f" * 64,
                }
                tampered_manifest["files"] = tampered_files
                tampered_manifest["file_count"] = len(tampered_files)
                tampered_manifest["files_sha256"] = object_sha256(tampered_files)
            elif tamper_name == "file_count":
                tampered_manifest["file_count"] = int(
                    tampered_manifest["file_count"]
                ) + 1
            else:
                tampered_manifest["files_sha256"] = "0" * 64
            tampered_manifest = add_self_hash(
                tampered_manifest, "snapshot_manifest_sha256"
            )
            runtime_source_manifest.write_text(
                json.dumps(
                    tampered_manifest,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            try:
                tampered_runtime_source_tree = exact_snapshot_tree_descriptor(
                    Path(runtime_source_snapshot["content_root_absolute_path"]),
                    label=f"selftest_runtime_source_manifest_{tamper_name}",
                    manifest_path=runtime_source_manifest,
                    manifest_self_hash_field="snapshot_manifest_sha256",
                )
                tampered_repair_tree = exact_snapshot_tree_descriptor(
                    repair_root,
                    label=f"selftest_repair_manifest_{tamper_name}",
                    manifest_path=repair_manifest,
                    manifest_self_hash_field="snapshot_sha256",
                )
                try:
                    verify_runtime_source_snapshot_binding(
                        runtime_source_snapshot,
                        f"self-test host manifest {tamper_name}",
                        runtime=runtime,
                        repair_exact_tree=tampered_repair_tree,
                        runtime_source_exact_tree=tampered_runtime_source_tree,
                        expected_source_root=live_source_root,
                    )
                except RepairPipelineError:
                    host_rejected = True
                else:
                    host_rejected = False
                if not host_rejected:
                    raise RepairPipelineError(
                        f"host verifier accepted runtime source manifest {tamper_name} tamper"
                    )

                tampered_exact_trees = {
                    "repair": tampered_repair_tree,
                    "source_v3": source_tree,
                    "runtime_source": tampered_runtime_source_tree,
                }
                tampered_config = add_self_hash(
                    {
                        key: value
                        for key, value in config.items()
                        if key != "config_sha256"
                    }
                    | {"snapshot_exact_trees": tampered_exact_trees},
                    "config_sha256",
                )
                tampered_config_path = (
                    fixture_repo / "work" / f"config.manifest_{tamper_name}.json"
                )
                write_json_create_once(tampered_config_path, tampered_config)
                tampered_prelock = add_self_hash(
                    {
                        key: value
                        for key, value in prelock.items()
                        if key != "prelock_sha256"
                    }
                    | {
                        "repair_config": absolute_file_binding(tampered_config_path)
                        | {"config_sha256": tampered_config["config_sha256"]},
                        "snapshot_exact_trees": tampered_exact_trees,
                    },
                    "prelock_sha256",
                )
                tampered_prelock_path = (
                    fixture_repo / "work" / f"prelock.manifest_{tamper_name}.json"
                )
                write_json_create_once(tampered_prelock_path, tampered_prelock)
                tampered_marker = marker_root / f"manifest_{tamper_name}.marker"
                tampered_child_command = isolated_bootstrap_command(
                    runtime=runtime,
                    prelock_path=tampered_prelock_path,
                    prelock_file_sha256=sha256_file(tampered_prelock_path),
                    prelock_internal_sha256=tampered_prelock["prelock_sha256"],
                    repair_tree_sha256=tampered_repair_tree["descriptor_sha256"],
                    source_tree_sha256=source_tree["descriptor_sha256"],
                    runtime_source_tree_sha256=tampered_runtime_source_tree[
                        "descriptor_sha256"
                    ],
                    mode="outer",
                    target=repair_script,
                    target_args=[str(tampered_marker)],
                )
                tampered_child = run_child(tampered_child_command)
                if tampered_child.returncode == 0 or tampered_marker.exists():
                    raise RepairPipelineError(
                        "embedded bootstrap accepted runtime source manifest "
                        f"{tamper_name} tamper"
                    )
                runtime_source_manifest_semantic_tampers_rejected.append(
                    tamper_name
                )
            finally:
                runtime_source_manifest.write_bytes(
                    original_runtime_source_manifest_bytes
                )
        verify_exact_snapshot_tree_descriptor(
            runtime_source_tree,
            "selftest runtime source manifest semantic tests restored",
        )
        verify_exact_snapshot_tree_descriptor(
            repair_tree,
            "selftest repair manifest semantic tests restored",
        )
        verify_runtime_source_snapshot_binding(
            runtime_source_snapshot,
            "self-test runtime source manifest semantic tests restored",
            runtime=runtime,
            repair_exact_tree=repair_tree,
            runtime_source_exact_tree=runtime_source_tree,
            expected_source_root=live_source_root,
        )

        baseline_cache_paths = {
            str(path.relative_to(fixture_repo))
            for root in (repair_root, source_root)
            for path in root.rglob("*")
            if path.is_dir() and path.name == "__pycache__"
            or path.is_file() and path.suffix.casefold() in {".pyc", ".pyo"}
        }
        outer_marker = marker_root / "outer.marker"
        outer_result = run_child(command("outer", repair_script, [str(outer_marker)]))
        if outer_result.returncode != 0 or not outer_marker.is_file():
            raise RepairPipelineError(
                f"isolated outer positive self-test failed: {outer_result.stderr}"
            )
        outer_marker.unlink()

        drifted_live_source = fixture_repo / "src.after_freeze_nonbinding"
        live_source_root.rename(drifted_live_source)
        try:
            live_drift_marker = marker_root / "live_drift.marker"
            live_drift_result = run_child(
                command("outer", repair_script, [str(live_drift_marker)])
            )
            if live_drift_result.returncode != 0 or not live_drift_marker.is_file():
                raise RepairPipelineError(
                    "post-freeze live-source drift incorrectly affected isolated runtime: "
                    f"{live_drift_result.stderr}"
                )
            live_drift_marker.unlink()
        finally:
            drifted_live_source.rename(live_source_root)

        extra_json = repair_root / "scripts" / "json.py"
        write_text(extra_json, "raise RuntimeError('preimport compromise')\n")
        injected_result = run_child(command("outer", repair_script, [str(outer_marker)]))
        extra_json.unlink()
        if injected_result.returncode == 0 or outer_marker.exists():
            raise RepairPipelineError("extra json.py reached the isolated target")

        source_json = source_root / "scripts" / "json.py"
        write_text(source_json, "raise RuntimeError('source preimport compromise')\n")
        source_json_result = run_child(
            command("outer", repair_script, [str(outer_marker)])
        )
        source_json.unlink()
        if source_json_result.returncode == 0 or outer_marker.exists():
            raise RepairPipelineError("source-v3 extra json.py reached the isolated target")
        injections.append(("source_extra_json_py", source_json))

        source_cache_dir = source_root / "scripts" / "__pycache__"
        source_cache_file = source_cache_dir / "evil.cpython-312.pyc"
        write_text(source_cache_file, "not bytecode")
        source_pyc_result = run_child(
            command("outer", repair_script, [str(outer_marker)])
        )
        shutil.rmtree(source_cache_dir)
        if source_pyc_result.returncode == 0 or outer_marker.exists():
            raise RepairPipelineError("source-v3 extra pyc reached the isolated target")
        injections.append(("source_extra_nested_pyc", source_cache_file))

        runtime_extra = runtime_source_root / "json.py"
        write_text(runtime_extra, "raise RuntimeError('runtime source injection')\n")
        expect_tree_rejection(runtime_source_tree, "runtime source extra file")
        runtime_extra_result = run_child(
            command("outer", repair_script, [str(outer_marker)])
        )
        runtime_extra.unlink()
        if runtime_extra_result.returncode == 0 or outer_marker.exists():
            raise RepairPipelineError("runtime-source extra file reached isolated target")
        injections.append(("runtime_source_extra_file", runtime_extra))

        runtime_cache_dir = runtime_source_root / "__pycache__"
        runtime_cache_file = runtime_cache_dir / "evil.cpython-312.pyc"
        write_text(runtime_cache_file, "post-freeze bytecode")
        expect_tree_rejection(runtime_source_tree, "runtime source extra pyc")
        runtime_pyc_result = run_child(
            command("outer", repair_script, [str(outer_marker)])
        )
        shutil.rmtree(runtime_cache_dir)
        if runtime_pyc_result.returncode == 0 or outer_marker.exists():
            raise RepairPipelineError("runtime-source extra pyc reached isolated target")
        injections.append(("runtime_source_extra_pyc", runtime_cache_file))

        runtime_symlink = runtime_source_root / "linked_fixture.py"
        runtime_symlink.symlink_to(runtime_source_root / "fixture_module.py")
        expect_tree_rejection(runtime_source_tree, "runtime source symlink")
        runtime_symlink_result = run_child(
            command("outer", repair_script, [str(outer_marker)])
        )
        runtime_symlink.unlink()
        if runtime_symlink_result.returncode == 0 or outer_marker.exists():
            raise RepairPipelineError("runtime-source symlink reached isolated target")
        injections.append(("runtime_source_symlink", runtime_symlink))

        runtime_fixture = runtime_source_root / "fixture_module.py"
        original_runtime_fixture = runtime_fixture.read_bytes()
        runtime_fixture.write_bytes(b"VALUE = 'tampered'\n")
        expect_tree_rejection(runtime_source_tree, "runtime source byte tamper")
        runtime_tamper_result = run_child(
            command("outer", repair_script, [str(outer_marker)])
        )
        runtime_fixture.write_bytes(original_runtime_fixture)
        if runtime_tamper_result.returncode == 0 or outer_marker.exists():
            raise RepairPipelineError("runtime-source byte tamper reached isolated target")
        injections.append(("runtime_source_byte_tamper", runtime_fixture))
        verify_exact_snapshot_tree_descriptor(
            runtime_source_tree, "selftest runtime source restored"
        )
        verify_exact_snapshot_tree_descriptor(repair_tree, "selftest repair restored again")

        base_command = command("outer", repair_script, [str(outer_marker)])
        wrong_physical = list(base_command)
        wrong_physical[wrong_physical.index(physical_sha256)] = "1" * 64
        wrong_internal = list(base_command)
        wrong_internal[wrong_internal.index(internal_sha256)] = "2" * 64
        swapped = list(base_command)
        file_index = swapped.index(physical_sha256)
        internal_index = swapped.index(internal_sha256)
        swapped[file_index], swapped[internal_index] = swapped[internal_index], swapped[file_index]
        for label, invalid in (
            ("wrong physical anchor", wrong_physical),
            ("wrong internal anchor", wrong_internal),
            ("swapped anchors", swapped),
        ):
            result = run_child(invalid)
            if result.returncode == 0 or outer_marker.exists():
                raise RepairPipelineError(f"{label} was accepted")

        nested_marker = marker_root / "nested.marker"
        batch_args = [
            "allowed",
            str(drafter_script),
            str(other_script),
            str(nested_marker),
        ]
        nested_result = run_child(command("batch", batch_script, batch_args))
        if nested_result.returncode != 0 or not nested_marker.is_file():
            raise RepairPipelineError(
                f"isolated nested drafter positive self-test failed: {nested_result.stderr}"
            )
        nested_marker.unlink()
        forbidden_marker = marker_root / "forbidden.marker"
        unknown_args = [
            "unknown",
            str(drafter_script),
            str(other_script),
            str(forbidden_marker),
        ]
        unknown_result = run_child(command("batch", batch_script, unknown_args))
        if unknown_result.returncode == 0 or forbidden_marker.exists():
            raise RepairPipelineError("unrecognized nested Python target was accepted")

        final_cache_paths = {
            str(path.relative_to(fixture_repo))
            for root in (repair_root, source_root)
            for path in root.rglob("*")
            if path.is_dir() and path.name == "__pycache__"
            or path.is_file() and path.suffix.casefold() in {".pyc", ".pyo"}
        }
        if final_cache_paths != baseline_cache_paths:
            raise RepairPipelineError(
                "isolated bootstrap changed bytecode/cache namespace: "
                f"{sorted(final_cache_paths ^ baseline_cache_paths)}"
            )

        direct = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--self-test"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if direct.returncode == 0 or "direct repair-runner invocation is forbidden" not in (
            direct.stdout + direct.stderr
        ):
            raise RepairPipelineError("direct repair-runner invocation was not rejected")
        return {
            "exact_tree_injections_rejected": [label for label, _ in injections],
            "isolated_outer_positive": True,
            "post_freeze_live_source_drift_nonbinding": True,
            "extra_json_rejected_before_target": True,
            "physical_anchor_mismatch_rejected": True,
            "internal_anchor_mismatch_rejected": True,
            "swapped_anchors_rejected": True,
            "nested_drafter_rewritten_through_isolation": True,
            "unrecognized_nested_python_rejected": True,
            "bytecode_cache_files_created": 0,
            "direct_runner_invocation_rejected": True,
            "runtime_source_manifest_semantic_tampers_rejected": (
                runtime_source_manifest_semantic_tampers_rejected
            ),
        }


def self_test() -> int:
    before = {"a": 1, "b": [1, {"c": 2}]}
    after = {"a": 2, "b": [1, {"c": 3}], "d": True}
    observed = canonical_diff(before, after)
    paths = [item["path"] for item in observed]
    if paths != ["$.a", "$.b[1].c", "$.d"]:
        raise RepairPipelineError(f"canonical diff self-test failed: {paths}")
    batch_pid = 100
    drafter = "/frozen/draft_case_checklist.py"
    expected: list[dict[str, Any]] = []
    rows: dict[int, dict[str, Any]] = {
        batch_pid: {"pid": batch_pid, "ppid": 1, "pgid": batch_pid, "command": "batch"}
    }
    for rank in range(7):
        case_id = f"case_{rank}"
        packet = f"/packets/{case_id}/case_packet.md"
        output = f"/outputs/{case_id}"
        command = f"/python {drafter} {packet} -o {output}/attempt_01.checklist.yaml"
        expected.append(
            {
                "execution_rank": rank,
                "execution_lane": "regular",
                "selection_rank": rank,
                "case_unit_id": case_id,
                "case_packet_path": packet,
                "case_output_dir": output,
                "allowed_ps_command_line_sha256": [object_sha256(command)],
            }
        )
        rows[200 + rank] = {
            "pid": 200 + rank,
            "ppid": batch_pid,
            "pgid": batch_pid,
            "command": command,
        }
    six = active_case_attempts(
        {pid: row for pid, row in rows.items() if pid != 206},
        batch_pid=batch_pid,
        drafter_path=drafter,
        expected=expected,
    )
    seven = active_case_attempts(
        rows, batch_pid=batch_pid, drafter_path=drafter, expected=expected
    )
    if len(six) != 6 or len(seven) != 7 or not (len(six) <= 6 and len(seven) > 6):
        raise RepairPipelineError("concurrency six/seven fixture failed")
    tampered = {pid: dict(row) for pid, row in rows.items() if pid != 206}
    tampered[200]["command"] += " --unbound"
    try:
        active_case_attempts(
            tampered, batch_pid=batch_pid, drafter_path=drafter, expected=expected
        )
    except RepairPipelineError:
        pass
    else:
        raise RepairPipelineError("tampered drafter command was accepted")
    wrong_parent = {pid: dict(row) for pid, row in rows.items() if pid != 206}
    wrong_parent[200]["ppid"] = 999
    try:
        active_case_attempts(
            wrong_parent,
            batch_pid=batch_pid,
            drafter_path=drafter,
            expected=expected,
        )
    except RepairPipelineError:
        pass
    else:
        raise RepairPipelineError("same-PGID drafter with wrong ppid was accepted")
    def isolated_foreign_fixture_argv(
        *,
        python: str,
        payload: str,
        mode: str,
        target: str,
        target_args: list[str] | None = None,
    ) -> list[str]:
        """Build the exact three-tree parser layout without invoking a target."""

        return [
            python,
            "-I",
            "-S",
            "-c",
            payload,
            "/prelock",
            "a" * 64,
            "b" * 64,
            "c" * 64,
            "d" * 64,
            "e" * 64,
            mode,
            target,
            "--",
            *(target_args or []),
        ]

    process_rows = {
        300: {
            "pid": 300,
            "ppid": 1,
            "pgid": 300,
            "command": "/python /tools/run_draft_batch.py --max-parallel 6",
        },
        301: {
            "pid": 301,
            "ppid": 1,
            "pgid": 301,
            "command": "codex exec --sandbox read-only",
        },
        302: {
            "pid": 302,
            "ppid": 1,
            "pgid": 302,
            "command": "/bin/zsh -c echo conversation mentions codex exec",
        },
        303: {
            "pid": 303,
            "ppid": 1,
            "pgid": 303,
            "command": " ".join(
                isolated_foreign_fixture_argv(
                    python="/python",
                    payload="PAYLOAD",
                    mode="outer",
                    target="/tools/run_checklist_repair_batch.py",
                    target_args=["--prelock", "/prelock"],
                )
            ),
        },
        304: {
            "pid": 304,
            "ppid": 1,
            "pgid": 304,
            "command": " ".join(
                isolated_foreign_fixture_argv(
                    python="/python",
                    payload="PAYLOAD",
                    mode="script",
                    target="/tools/draft_case_checklist.py",
                    target_args=["/packet", "-o", "/output"],
                )
            ),
        },
        305: {
            "pid": 305,
            "ppid": 1,
            "pgid": 305,
            # Correct layout but a deliberately invalid mode/target pairing.
            # The malformed fallback would match the target name; the normal
            # parser must not, proving the exact-layout branch was exercised.
            "command": " ".join(
                isolated_foreign_fixture_argv(
                    python="/python",
                    payload="PAYLOAD",
                    mode="outer",
                    target="/tools/draft_case_checklist.py",
                )
            ),
        },
    }
    foreign = foreign_drafting_processes(
        process_rows,
        patterns=[
            "run_checklist_repair_batch.py",
            "run_draft_batch.py",
            "draft_case_checklist.py",
            "codex exec",
        ],
        excluded_pids=set(),
    )
    if [item["pid"] for item in foreign] != [300, 301, 303, 304]:
        raise RepairPipelineError("structured foreign-process fixture failed")
    normal_layout_parser_branch_proved = not any(
        item["pid"] == 305 for item in foreign
    )
    if not normal_layout_parser_branch_proved:
        raise RepairPipelineError(
            "correct-layout foreign parser fixture fell through malformed fallback"
        )
    real_outer = subprocess.Popen(
        isolated_foreign_fixture_argv(
            python=sys.executable,
            payload="__import__('time').sleep(20)",
            mode="outer",
            target="/tools/run_checklist_repair_batch.py",
        ),
        start_new_session=True,
    )
    try:
        time.sleep(0.1)
        real_rows = observe_process_rows(
            {
                "ps_command": [
                    "/bin/ps",
                    "-ww",
                    "-axo",
                    "pid=,ppid=,pgid=,command=",
                ]
            },
            "real isolated outer foreign self-test",
        )
        real_foreign = foreign_drafting_processes(
            real_rows,
            patterns=["run_checklist_repair_batch.py"],
            excluded_pids=set(),
        )
        if real_outer.pid not in {item["pid"] for item in real_foreign}:
            raise RepairPipelineError("real simultaneous outer wrapper evaded foreign detection")
    finally:
        try:
            os.killpg(real_outer.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        real_outer.wait(timeout=5)
    foreign_config = {
        "concurrency_audit": {
            "ps_command": ["/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,command="],
            "ps_binary": {"test_fixture": True},
            "foreign_process_patterns": [
                "run_checklist_repair_batch.py",
                "run_draft_batch.py",
                "draft_case_checklist.py",
                "codex exec",
            ],
        }
    }
    original_subprocess_run = subprocess.run
    try:
        subprocess.run = lambda *args, **kwargs: subprocess.CompletedProcess(  # type: ignore[assignment]
            args=args, returncode=0, stdout="999 1 999 /bin/echo harmless\n", stderr=""
        )
        passing_foreign_preflight = foreign_drafting_preflight(foreign_config)
        subprocess.run = lambda *args, **kwargs: subprocess.CompletedProcess(  # type: ignore[assignment]
            args=args,
            returncode=0,
            stdout="300 1 300 /python /tools/run_draft_batch.py --max-parallel 6\n",
            stderr="",
        )
        try:
            foreign_drafting_preflight(foreign_config)
        except RepairPipelineError:
            foreign_preflight_rejected = True
        else:
            foreign_preflight_rejected = False
    finally:
        subprocess.run = original_subprocess_run
    if (
        passing_foreign_preflight.get("status") != "pass"
        or passing_foreign_preflight.get("foreign_process_count") != 0
        or passing_foreign_preflight.get("foreign_processes") != []
        or not foreign_preflight_rejected
    ):
        raise RepairPipelineError("foreign-process preflight is not fail-closed pass/0/[]")
    immediate_gap_popen_calls: list[list[str]] = []
    original_popen = subprocess.Popen

    def forbidden_gap_popen(
        command: list[str], *args: Any, **kwargs: Any
    ) -> Any:
        del args, kwargs
        immediate_gap_popen_calls.append(command)
        raise AssertionError("Popen must not run after immediate foreign appearance")

    early_fixture = add_self_hash(
        {
            "schema_version": "androidworld_checklist_repair_foreign_process_preflight/v1",
            "captured_at": utc_now(),
            "monotonic_ns": time.monotonic_ns(),
            "ps_binary": foreign_config["concurrency_audit"]["ps_binary"],
            "ps_command": foreign_config["concurrency_audit"]["ps_command"],
            "patterns": foreign_config["concurrency_audit"][
                "foreign_process_patterns"
            ],
            "excluded_runner_pid": os.getpid(),
            "excluded_runner_ancestor_pids": [],
            "foreign_processes": [],
            "foreign_process_count": 0,
            "status": "pass",
            "binding_policy": "foreign drafting processes must be absent before batch launch",
        },
        "preflight_sha256",
    )
    deterministic_fixture = add_self_hash(
        {
            "schema_version": "androidworld_checklist_repair_generation_preflight/v1",
            "created_at": utc_now(),
            "monotonic_ns": time.monotonic_ns(),
            "status": "pass",
            "core": {},
            "core_sha256": object_sha256({}),
        },
        "generation_preflight_sha256",
    )
    immediate_gap_record: dict[str, Any] | None = None
    try:
        subprocess.run = lambda *args, **kwargs: subprocess.CompletedProcess(  # type: ignore[assignment]
            args=args,
            returncode=0,
            stdout=(
                "777 1 777 /python /tools/run_draft_batch.py --max-parallel 6\n"
            ),
            stderr="",
        )
        subprocess.Popen = forbidden_gap_popen  # type: ignore[assignment]
        try:
            _run_after_verified_generation_preflight(
                ["/bin/false"],
                config=foreign_config,
                prelock={},
                environment={},
                foreign_preflight=early_fixture,
                generation_preflight=deterministic_fixture,
            )
        except ImmediateForeignPreflightFailure as exc:
            immediate_gap_record = dict(exc.record)
        else:
            raise RepairPipelineError(
                "foreign process appearing after deterministic rehash was accepted"
            )
    finally:
        subprocess.run = original_subprocess_run
        subprocess.Popen = original_popen
    if (
        immediate_gap_popen_calls
        or immediate_gap_record is None
        or immediate_gap_record.get("foreign_process_count") != 1
        or [
            item.get("pid")
            for item in (immediate_gap_record.get("foreign_processes") or [])
        ]
        != [777]
    ):
        raise RepairPipelineError(
            "immediate foreign-process gap gate did not carry evidence before Popen"
        )
    popen_calls: list[list[str]] = []

    def forbidden_popen(command: list[str], *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        popen_calls.append(command)
        raise AssertionError("Popen must not run after a preflight-token failure")

    subprocess.Popen = forbidden_popen  # type: ignore[assignment]
    try:
        try:
            run_with_concurrency_audit(
                ["/bin/false"],
                config={},
                prelock={},
                environment={},
                foreign_preflight={},
                generation_preflight={},
                readonly_preflight_record={},
                codex_auth_pre={},
            )
        except RepairPipelineError:
            pass
        else:
            raise RepairPipelineError("invalid generation preflight token was accepted")
    finally:
        subprocess.Popen = original_popen
    if popen_calls:
        raise RepairPipelineError("a generation-preflight failure reached Popen")
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    main_node = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    calls = [
        node
        for node in ast.walk(main_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    preflight_calls = [node for node in calls if node.func.id == "foreign_drafting_preflight"]
    generation_preflight_calls = [
        node for node in calls if node.func.id == "deterministic_generation_preflight"
    ]
    safe_calls = [node for node in calls if node.func.id == "safe_run_with_concurrency_audit"]
    if (
        len(preflight_calls) != 1
        or len(generation_preflight_calls) != 1
        or len(safe_calls) != 1
        or preflight_calls[0].lineno >= safe_calls[0].lineno
        or generation_preflight_calls[0].lineno >= safe_calls[0].lineno
        or "foreign_preflight" not in {keyword.arg for keyword in safe_calls[0].keywords}
        or "generation_preflight" not in {keyword.arg for keyword in safe_calls[0].keywords}
    ):
        raise RepairPipelineError("main foreign-preflight wiring fixture failed")
    bootstrap_tree = self_test_exact_tree_and_isolated_bootstrap()
    outer_cleanup = self_test_outer_postflight_failure_cleanup()
    sigterm_cleanup = self_test_outer_signal_cleanup(signal.SIGTERM)
    sighup_cleanup = self_test_outer_signal_cleanup(signal.SIGHUP)
    print(
        json.dumps(
            {
                "status": "self_test_pass",
                "changed_paths": paths,
                "active_case_attempts_six": len(six),
                "active_case_attempts_seven": len(seven),
                "foreign_processes_detected": [item["pid"] for item in foreign],
                "normal_layout_foreign_parser_branch_proved": (
                    normal_layout_parser_branch_proved
                ),
                "real_simultaneous_outer_detected": True,
                "foreign_preflight_fail_closed": True,
                "generation_preflight_failure_popen_calls": len(popen_calls),
                "immediate_foreign_gap_failure_popen_calls": len(
                    immediate_gap_popen_calls
                ),
                "wrong_parent_rejected": True,
                "outer_postflight_failure_cleanup": outer_cleanup,
                "outer_sigterm_cleanup": sigterm_cleanup,
                "outer_sighup_cleanup": sighup_cleanup,
                "exact_tree_and_isolated_bootstrap": bootstrap_tree,
                "main_foreign_preflight_wired": True,
            },
            indent=2,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.gate_self_test:
        if args.prelock is None:
            raise RepairPipelineError(
                "--gate-self-test requires an actual bootstrap-bound --prelock"
            )
        return gate_self_test(args.prelock.resolve())
    if args.self_test:
        return self_test()
    if args.prelock is None:
        raise RepairPipelineError("--prelock is required unless --self-test is used")
    prelock_path = args.prelock.resolve()
    enforce_frozen_runner_identity(prelock_path)
    if args.restart_after_incident:
        prelock, config, source = verify_prelocked_context(
            prelock_path, require_attempt_root_absent=None
        )
        attempt_root, _ = _attempt_layout(config)
        if not os.path.lexists(attempt_root):
            raise RepairPipelineError(
                "--restart-after-incident requires a pre-existing attempt root"
            )
        archived = archive_existing(attempt_root, prelock)
        print(f"Archived prior repair attempt at {archived}", flush=True)
        prelock, config, source = verify_prelocked_context(prelock_path)
    else:
        prelock, config, source = verify_prelocked_context(prelock_path)
    child_environment = verify_closed_child_environment(
        config["runner_environment"], "main repair child environment"
    )
    codex_auth_pre = current_codex(prelock, child_environment)
    command = command_for(config, prelock, prelock_path)
    runner_preflight_record = readonly_preflight(config, prelock)
    lease_sink: list[AttemptRootLease] = []
    try:
        foreign_preflight_record = foreign_drafting_preflight(config)
        generation_preflight_record = deterministic_generation_preflight(
            config=config,
            prelock=prelock,
            command=command,
            environment=child_environment,
            readonly_preflight_record=runner_preflight_record,
            foreign_preflight=foreign_preflight_record,
            codex_auth_pre=codex_auth_pre,
        )
        run_result = safe_run_with_concurrency_audit(
            command,
            config=config,
            prelock=prelock,
            environment=child_environment,
            foreign_preflight=foreign_preflight_record,
            generation_preflight=generation_preflight_record,
            readonly_preflight_record=runner_preflight_record,
            codex_auth_pre=codex_auth_pre,
            lease_sink=lease_sink,
        )
        batch_returncode, concurrency_audit = run_result
        attempt_lease = run_result.attempt_lease
        attempt_lease.verify("repair attempt before read-only post guard")
        try:
            readonly_guard = finalize_readonly_guard(
                config,
                prelock,
                runner_preflight_record,
            )
        except BaseException as exc:
            incident = record_readonly_post_failure(config, prelock, exc)
            raise RepairPipelineError(
                f"read-only post evidence failed; promotion forbidden; incident={incident}"
            ) from exc
        # Re-import and re-hash all frozen runtime dependencies immediately after
        # the model-call subprocess, irrespective of its return code.
        verify_python_runtime_binding(
            config["python_runtime"], "prelocked Python runtime after repair subprocess"
        )
        codex_auth_post = current_codex(prelock, child_environment)
        attempt_lease.verify("repair attempt after post-auth check")
        if readonly_guard["status"] != "pass":
            raise RepairPipelineError(
                "repair read-only post guard failed; evidence is preserved and promotion is forbidden"
            )
        if concurrency_audit["status"] != "pass":
            raise RepairPipelineError(
                "observed concurrency audit failed; evidence is preserved and promotion is forbidden"
            )
        if batch_returncode != 0:
            raise RepairPipelineError(
                f"frozen v3 batch runner returned {batch_returncode}; preserve output and restart only via incident"
            )
        receipt = validate_and_record(
            prelock_path,
            prelock,
            config,
            source,
            readonly_guard,
            concurrency_audit,
            codex_auth_pre,
            codex_auth_post,
            attempt_lease.claim,
        )
        # Re-read every prelocked input/tool and the claimed namespace before
        # releasing the directory descriptors.
        verify_prelocked_context(
            prelock_path,
            require_attempt_root_absent=False,
            attempt_claim=attempt_lease.claim,
        )
        attempt_lease.verify("final repair attempt lease before close")
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
    finally:
        if lease_sink:
            lease_sink[-1].close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
