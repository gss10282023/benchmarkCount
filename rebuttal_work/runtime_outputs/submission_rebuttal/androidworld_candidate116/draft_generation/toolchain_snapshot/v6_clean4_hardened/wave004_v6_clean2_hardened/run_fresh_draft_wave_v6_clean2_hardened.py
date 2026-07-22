#!/usr/bin/env python3
"""Fail-closed launcher for the canonical-only candidate116 wave_004 v6."""

from __future__ import annotations

import argparse
import datetime as dt
import hmac
import importlib.util
import json
import os
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from wave004_v6_clean2_hardened_common import (
    CASE_COUNT,
    CANDIDATE_REVIEW_SCHEMA,
    CONFIG_SCHEMA,
    EXPECTED_CODEX_VERSION,
    EXPECTED_FREEZE_SHA256,
    EXPECTED_MODEL,
    EXPECTED_REASONING,
    EXPECTED_SANDBOX,
    GENERATION_ID,
    INDEPENDENT_PRELOCK_REVIEW_SCHEMA,
    LAUNCH_APPROVAL_SCHEMA,
    PARALLELISM,
    PRELOCK_SCHEMA,
    SNAPSHOT_SCHEMA,
    Wave004V6Clean2HardenedError,
    add_self_hash,
    canonical_sha256,
    load_json,
    regular_file_binding,
    require_empty_or_absent,
    require_safe_case_id,
    sha256_file,
    verify_exact_directory_files,
    verify_executable_binding,
    verify_regular_file_binding,
    verify_self_hash,
    write_json_create_once,
)
from wave004_v6_clean2_hardened_staging import (
    DISABLED_CODEX_FEATURES,
    MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES,
    MAX_COVERAGE_PLAN_PAGE_TOKENS,
    MAX_COVERAGE_PLAN_ROW_BYTES,
    MAX_READER_ENVELOPE_BYTES,
    MAX_READER_ENVELOPE_TOKENS,
    PRODUCTION_NAMESPACE,
    build_codex_exec_argv,
    coverage_receipt_from_events,
    verify_coverage_receipt_against_events,
    verify_reader_operation_expectations_binding,
)


class GenerationError(Wave004V6Clean2HardenedError):
    """Raised when the raw wave cannot be proven safe and complete."""


EXPECTED_ENV_KEYS = {
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONHASHSEED",
    "PYTHONNOUSERSITE",
    "TMPDIR",
    "TZ",
}
ALLOWED_LOGIN_WARNING = (
    "WARNING: proceeding, even though we could not create PATH aliases: "
    "Operation not permitted (os error 1)"
)
HANDLED_SIGNALS = tuple(
    item
    for item in (
        signal.SIGINT,
        signal.SIGTERM,
        signal.SIGHUP,
        getattr(signal, "SIGQUIT", None),
    )
    if item is not None
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path, required=True)
    parser.add_argument(
        "--launch-approval",
        type=Path,
        required=True,
        help=(
            "Create-once independent post-prelock launch approval. The preparer/candidate "
            "approval can never substitute for this final GO."
        ),
    )
    return parser.parse_args()


def verify_launch_approval(
    path: Path, *, prelock: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    """Verify two independent post-prelock reviews before any model authorization."""

    if path.is_symlink():
        raise GenerationError("launch approval path may not be a symlink")
    resolved = path.resolve(strict=True)
    if stat.S_IMODE(resolved.stat().st_mode) != 0o444:
        raise GenerationError("launch approval must be a sealed 0444 regular create-once file")
    approval = load_json(resolved, "independent launch approval")
    verify_self_hash(approval, "approval_sha256", "independent launch approval")
    snapshot_sha = (config.get("toolchain_snapshot") or {}).get("snapshot_sha256")
    capacity_sha = (config.get("staged_capacity") or {}).get("capacity_sha256")
    if (
        approval.get("schema_version")
        != LAUNCH_APPROVAL_SCHEMA
        or approval.get("status") != "approved_after_independent_prelock_audit"
        or approval.get("candidate_generation_id") != GENERATION_ID
        or approval.get("model_call_count") != 0
        or approval.get("authorize_first_model_call") is not True
        or approval.get("independent_final_go") is not True
        or approval.get("prelock_sha256") != prelock.get("prelock_sha256")
        or approval.get("config_sha256") != config.get("config_sha256")
        or approval.get("snapshot_sha256") != snapshot_sha
        or approval.get("capacity_sha256") != capacity_sha
    ):
        raise GenerationError("independent launch approval identity/bindings are invalid")
    reviews = list(approval.get("independent_reviews") or [])
    reviewer_ids: list[str] = []
    if len(reviews) != 2:
        raise GenerationError("launch approval requires exactly two independent reviews")
    for index, row in enumerate(reviews):
        reviewer_id = str(row.get("reviewer_id") or "")
        if (
            not reviewer_id
            or row.get("status") != "pass"
            or row.get("independent") is not True
        ):
            raise GenerationError(f"independent launch review {index} is not an exact pass")
        report_path = verify_regular_file_binding(
            row.get("report") or {}, f"independent launch review {index} report"
        )
        report = load_json(report_path, f"independent launch review {index} report")
        verify_self_hash(report, "review_sha256", f"independent launch review {index}")
        if (
            report.get("schema_version")
            != INDEPENDENT_PRELOCK_REVIEW_SCHEMA
            or report.get("status") != "pass"
            or report.get("reviewer_id") != reviewer_id
            or report.get("independent") is not True
            or report.get("model_call_count") != 0
            or report.get("candidate_generation_id") != GENERATION_ID
            or report.get("prelock_sha256") != prelock.get("prelock_sha256")
            or report.get("config_sha256") != config.get("config_sha256")
            or report.get("snapshot_sha256") != snapshot_sha
            or report.get("capacity_sha256") != capacity_sha
            or report.get("review_sha256") != (row.get("report") or {}).get("review_sha256")
        ):
            raise GenerationError(f"independent launch review {index} bindings are invalid")
        reviewer_ids.append(reviewer_id)
    if len(set(reviewer_ids)) != 2:
        raise GenerationError("the two independent launch reviews reuse one reviewer identity")
    return approval | {"path": str(resolved), "file_sha256": sha256_file(resolved)}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise GenerationError(f"cannot import frozen module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_runtime_closure(root: Path, manifest: Mapping[str, Any]) -> None:
    relative = str(manifest.get("runtime_environment_manifest_relative") or "")
    runtime_path = root / relative
    if runtime_path.is_symlink() or not runtime_path.is_file():
        raise GenerationError("runtime environment manifest is missing")
    if sha256_file(runtime_path) != manifest.get("runtime_environment_manifest_sha256"):
        raise GenerationError("runtime environment manifest bytes changed")
    runtime = load_json(runtime_path, "runtime environment closure")
    verify_self_hash(runtime, "runtime_closure_sha256", "runtime environment closure")
    if (
        runtime.get("schema_version")
        != "androidworld_candidate116_python_runtime_closure/v1"
        or runtime.get("production_namespace") != GENERATION_ID
        or runtime.get("status") != "fully_byte_bound"
        or runtime.get("distribution_count") != len(runtime.get("distributions") or [])
    ):
        raise GenerationError("runtime environment closure identity is invalid")
    verify_executable_binding(runtime.get("python_invocation") or {}, "frozen Python")
    verify_regular_file_binding(runtime.get("pyvenv_cfg") or {}, "pyvenv.cfg")
    names: list[str] = []
    for row in runtime.get("distributions") or []:
        names.append(str(row.get("name") or ""))
        files = row.get("files") or []
        if not row.get("version") or not files:
            raise GenerationError(f"runtime distribution is incomplete: {row.get('name')}")
        for index, binding in enumerate(files):
            label = f"runtime {row.get('name')} file {index}"
            if binding.get("kind") == "symlink":
                verify_executable_binding(binding, label)
            else:
                verify_regular_file_binding(binding, label)
    if len(names) != len(set(names)) or len(names) != 11:
        raise GenerationError("runtime distribution closure set is not exact")


def verify_snapshot(config: Mapping[str, Any]) -> tuple[dict[str, Any], Path]:
    manifest_path = verify_regular_file_binding(
        config.get("toolchain_snapshot") or {}, "toolchain snapshot manifest"
    )
    manifest = load_json(manifest_path, "toolchain snapshot manifest")
    verify_self_hash(manifest, "snapshot_sha256", "toolchain snapshot manifest")
    if (
        manifest.get("schema_version") != SNAPSHOT_SCHEMA
        or manifest.get("production_namespace") != GENERATION_ID
        or manifest.get("status") != "frozen_create_once"
        or manifest.get("file_count") != len(manifest.get("files") or [])
        or manifest.get("files_sha256") != canonical_sha256(manifest.get("files") or [])
    ):
        raise GenerationError("toolchain snapshot identity is invalid")
    root = Path(str(manifest.get("snapshot_root_absolute") or ""))
    if root != Path(str(config.get("snapshot_root_absolute") or "")):
        raise GenerationError("toolchain snapshot root differs from config")
    expected_files = list(manifest.get("files") or [])
    verify_exact_directory_files(
        root,
        expected_files,
        label="v6_clean2_hardened toolchain snapshot",
        excluded_relative_paths={"snapshot_manifest.json"},
    )
    adaptations = list(manifest.get("controlled_adaptations") or [])
    if {row.get("name") for row in adaptations} != {
        "checklist_guardrails",
        "checklist_schema",
        "draft_template",
        "drafter",
        "validator",
    }:
        raise GenerationError("required controlled guardrail/validator adaptations are absent")
    snapshot_names = {Path(row["relative_path"]).name for row in expected_files}
    if {
        "draft_source_pointer_strict_v2.supplement.md",
        "androidworld_full_regeneration_v5.supplement.md",
    } & snapshot_names:
        raise GenerationError("forbidden legacy supplement entered v6 snapshot")
    verify_runtime_closure(root, manifest)
    return manifest, root


def expected_native_batch_command(
    config: Mapping[str, Any], prelock: Mapping[str, Any]
) -> list[str]:
    tools = config["tool_bindings"]
    max_size = max(int(row["packet"]["size_bytes"]) for row in prelock["packet_inputs"])
    return [
        str(config["python_runtime"]["path"]),
        str(tools["batch_runner"]["path"]),
        "--case-packet-root",
        str(config["canonical_packet_root_absolute"]),
        "--output-root",
        str(config["output_root_absolute"]),
        "--provider",
        "codex",
        "--model",
        EXPECTED_MODEL,
        "--reasoning-effort",
        EXPECTED_REASONING,
        "--token-budgets",
        ",".join(str(value) for value in config["token_budgets"]),
        "--max-parallel",
        str(PARALLELISM),
        "--large-max-parallel",
        str(PARALLELISM),
        "--large-case-threshold-bytes",
        str(max_size + 1),
        "--http-timeout-seconds",
        "180",
        "--large-http-timeout-seconds",
        "480",
        "--codex-timeout-seconds",
        str(config["codex_timeout_seconds"]),
        "--large-codex-timeout-seconds",
        str(config["large_codex_timeout_seconds"]),
        "--codex-sandbox",
        EXPECTED_SANDBOX,
        "--prompt-supplement",
        str(tools["prompt_supplement"]["path"]),
        "--sort-by",
        "name",
        "--sleep-seconds",
        "2.0",
        "--quality-check",
        "none",
        "--case-ids",
        ",".join(prelock["case_order"]),
    ]


def verify_prompt_and_native_codex_argv(
    config: Mapping[str, Any], snapshot_root: Path
) -> None:
    tools = config["tool_bindings"]
    base_path = verify_regular_file_binding(tools["draft_prompt"], "base prompt")
    supplement_path = verify_regular_file_binding(
        tools["prompt_supplement"], "clean v6 supplement"
    )
    supplement = supplement_path.read_text(encoding="utf-8")
    forbidden = (
        "Fresh Generation Control",
        "wave_003",
        "automatic_qc_v3",
        "manual_audits",
        "278 warning",
    )
    if any(token in supplement for token in forbidden):
        raise GenerationError("clean v6 supplement contains historical warning material")
    effective = (
        base_path.read_text(encoding="utf-8").rstrip()
        + "\n\n"
        + supplement.strip()
        + "\n"
    )
    composition = config.get("prompt_composition") or {}
    composition_core = dict(composition)
    claimed = composition_core.pop("composition_sha256", None)
    if (
        claimed != canonical_sha256(composition_core)
        or composition.get("effective_prompt_sha256")
        != canonical_sha256({"prompt": effective})
        or composition.get("legacy_supplements_included") != []
        or composition.get("historical_draft_or_warning_input_included") is not False
    ):
        raise GenerationError("effective prompt composition binding is invalid")

    drafter_path = verify_regular_file_binding(tools["drafter"], "frozen drafter")
    sys.path.insert(0, str(snapshot_root))
    try:
        drafter = load_module(drafter_path, "wave004_v6_frozen_drafter_probe")
    finally:
        if sys.path and sys.path[0] == str(snapshot_root):
            sys.path.pop(0)
    old_which = drafter.shutil.which
    drafter.shutil.which = lambda _name: str(config["codex_cli"]["path"])
    try:
        with tempfile.TemporaryDirectory(
            prefix="case-checklist-codex-v6-clean2-hardened-probe-",
            dir=config["child_environment"]["TMPDIR"],
        ) as temp_dir:
            workspace = Path(temp_dir)
            observed = drafter.build_codex_command(
                workspace_root=workspace,
                schema_path=workspace / "output_schema.json",
                output_path=workspace / "draft_body.json",
                model=EXPECTED_MODEL,
                reasoning_effort=EXPECTED_REASONING,
                sandbox=EXPECTED_SANDBOX,
            )
            expected = build_codex_exec_argv(
                codex_executable=Path(config["codex_cli"]["resolved_path"]),
                workspace_root=workspace,
                schema_path=workspace / "output_schema.json",
                output_path=workspace / "draft_body.json",
                model=EXPECTED_MODEL,
                reasoning_effort=EXPECTED_REASONING,
                repository_root=Path(config["repository_root_absolute"]),
                wave_tmp_root=Path(config["child_environment"]["TMPDIR"]),
                auth_home=Path(config["child_environment"]["CODEX_HOME"]),
                original_codex_home=Path(config["original_codex_home_absolute"]),
                isolated_home=Path(config["child_environment"]["HOME"]),
                real_home=Path(config["real_home_absolute"]),
            )
    finally:
        drafter.shutil.which = old_which
    if observed != expected:
        raise GenerationError(f"frozen drafter Codex argv is not exact: {observed}")
    if any(Path(config["child_environment"]["TMPDIR"]).iterdir()):
        raise GenerationError("Codex argv probe left residue in the dedicated TMP root")


def verify_packet_inputs(prelock: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    inputs = list(prelock.get("packet_inputs") or [])
    case_order = list(prelock.get("case_order") or [])
    if (
        len(inputs) != CASE_COUNT
        or len(case_order) != CASE_COUNT
        or len(set(case_order)) != CASE_COUNT
        or prelock.get("packet_inputs_sha256") != canonical_sha256(inputs)
        or prelock.get("case_order_sha256") != canonical_sha256(case_order)
    ):
        raise GenerationError("prelock packet inputs/order are not exact 116")
    root = Path(str(config.get("canonical_packet_root_absolute") or ""))
    if root.is_symlink() or not root.is_dir():
        raise GenerationError("canonical packet root is missing or symlinked")
    observed_ids = sorted(path.parent.name for path in root.glob("*/case_packet.md"))
    if observed_ids != sorted(case_order):
        raise GenerationError("canonical packet root discovery differs from prelock")
    for rank, (case_id, row) in enumerate(zip(case_order, inputs, strict=True)):
        require_safe_case_id(case_id)
        expected = root / case_id / "case_packet.md"
        if (
            row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_id
            or row.get("input_kind") != "canonical_full_case_packet"
            or Path(str((row.get("packet") or {}).get("path") or "")) != expected
        ):
            raise GenerationError(f"canonical packet identity mismatch for {case_id}")
        verify_regular_file_binding(row["packet"], f"canonical packet {case_id}")


def load_and_verify_frozen_reader_coverage(
    prelock: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    """Verify the exact clean4 two-file A/B tree and return parsed documents."""

    binding = config.get("frozen_reader_coverage") or {}
    if prelock.get("frozen_reader_coverage") != binding:
        raise GenerationError("prelock/config frozen reader coverage bindings differ")
    root = Path(str(binding.get("root_absolute") or ""))
    index_path = verify_regular_file_binding(
        binding.get("index") or {}, "frozen reader coverage index"
    )
    index = load_json(index_path, "frozen reader coverage index")
    verify_self_hash(index, "coverage_index_sha256", "frozen reader coverage index")
    case_order = list(prelock.get("case_order") or [])
    rows = list(index.get("cases") or [])
    expected_files = [
        "model_input_coverage.json",
        "reader_operation_expectations.json",
    ]
    if (
        index.get("schema_version")
        != "androidworld_candidate116_frozen_reader_coverage_index/v6_clean4_hardened"
        or index.get("production_namespace") != GENERATION_ID
        or index.get("status") != "frozen_A_and_B_before_first_model_call"
        or Path(str(index.get("root_absolute") or "")) != root
        or index.get("case_count") != CASE_COUNT
        or binding.get("case_count") != CASE_COUNT
        or index.get("case_order") != case_order
        or index.get("case_order_sha256") != canonical_sha256(case_order)
        or binding.get("case_order_sha256") != index.get("case_order_sha256")
        or index.get("expected_case_files") != expected_files
        or binding.get("expected_case_files") != expected_files
        or [row.get("case_unit_id") for row in rows] != case_order
        or index.get("cases_sha256") != canonical_sha256(rows)
        or index.get("coverage_index_sha256")
        != (binding.get("index") or {}).get("coverage_index_sha256")
    ):
        raise GenerationError("frozen reader coverage index identity is invalid")
    if root.is_symlink() or not root.is_dir() or stat.S_IMODE(root.stat().st_mode) != 0o555:
        raise GenerationError("frozen reader coverage root is not sealed 0555")
    if sorted(path.name for path in root.iterdir()) != sorted(case_order):
        raise GenerationError("frozen reader coverage case namespace is not exact")

    packet_by_case = {
        str(row["case_unit_id"]): row for row in prelock.get("packet_inputs") or []
    }
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = str(row["case_unit_id"])
        case_root = root / case_id
        if (
            case_root.is_symlink()
            or not case_root.is_dir()
            or stat.S_IMODE(case_root.stat().st_mode) != 0o555
            or sorted(path.name for path in case_root.iterdir()) != expected_files
        ):
            raise GenerationError(f"frozen A/B namespace is invalid for {case_id}")
        requirements_path = verify_regular_file_binding(
            row.get("requirements") or {}, f"{case_id} frozen coverage requirements"
        )
        operations_path = verify_regular_file_binding(
            row.get("reader_operation_expectations") or {},
            f"{case_id} frozen reader operation expectations",
        )
        if (
            requirements_path != case_root / expected_files[0]
            or operations_path != case_root / expected_files[1]
            or stat.S_IMODE(requirements_path.stat().st_mode) != 0o444
            or stat.S_IMODE(operations_path.stat().st_mode) != 0o444
        ):
            raise GenerationError(f"frozen A/B paths/modes are invalid for {case_id}")
        requirements = load_json(requirements_path, f"{case_id} coverage requirements")
        operations = load_json(
            operations_path, f"{case_id} reader operation expectations"
        )
        try:
            verify_reader_operation_expectations_binding(requirements, operations)
        except BaseException as exc:
            raise GenerationError(f"frozen A/B binding failed for {case_id}: {exc}") from exc
        packet = packet_by_case.get(case_id) or {}
        if (
            requirements.get("production_namespace") != GENERATION_ID
            or operations.get("production_namespace") != GENERATION_ID
            or requirements.get("task_id") != row.get("task_id")
            or operations.get("task_id") != row.get("task_id")
            or requirements.get("case_packet_sha256")
            != (packet.get("packet") or {}).get("sha256")
            or row["requirements"].get("requirements_sha256")
            != requirements.get("requirements_sha256")
            or row["reader_operation_expectations"].get(
                "reader_operation_expectations_sha256"
            )
            != operations.get("reader_operation_expectations_sha256")
            or row["reader_operation_expectations"].get("operations_sha256")
            != operations.get("operations_sha256")
        ):
            raise GenerationError(f"frozen A/B semantic binding failed for {case_id}")
        result[case_id] = {
            "requirements": requirements,
            "reader_operation_expectations": operations,
            "index_row": row,
        }
    return result


def verify_clean4_config_namespace(
    *, prelock_path: Path, config_path: Path, config: Mapping[str, Any]
) -> None:
    """Reject any clean3 path or non-exact clean4 create-later namespace."""

    work_root = Path(str(config.get("work_root_absolute") or ""))
    expected = (
        (prelock_path, work_root
        / "draft_generation"
        / "freeze"
        / "androidworld_candidate116_codex_cli_draft_prelock_v6_clean4_hardened.json"),
        (config_path, work_root
        / "draft_generation"
        / "config"
        / "androidworld_candidate116_codex_cli_draft_config_v6_clean4_hardened.json"),
        (Path(str(config.get("snapshot_root_absolute") or "")), work_root
        / "draft_generation"
        / "toolchain_snapshot"
        / "v6_clean4_hardened"),
        (Path(str(config.get("output_root_absolute") or "")), work_root
        / "draft_generation"
        / "waves"
        / GENERATION_ID),
        (Path(str((config.get("child_environment") or {}).get("CODEX_HOME") or "")), Path.home()
        / ".codex-wave004-v6-clean4-hardened-auth"),
        (Path(str((config.get("child_environment") or {}).get("HOME") or "")), Path(
            tempfile.gettempdir()
        ).resolve()
        / "androidworld-wave004-v6-clean4-hardened-home"),
        (Path(str((config.get("child_environment") or {}).get("TMPDIR") or "")), Path(
            tempfile.gettempdir()
        ).resolve()
        / "androidworld-wave004-v6-clean4-hardened-tmp"),
    )
    if any(actual != planned for actual, planned in expected.items()):
        raise GenerationError("clean4 production namespace paths are not exact")
    if any(
        "clean3" in str(path) or "clean4" not in str(path)
        for pair in expected
        for path in pair
    ):
        raise GenerationError("clean3 leaked into a clean4 production identity")


def verify_context(prelock_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    if PRODUCTION_NAMESPACE != GENERATION_ID:
        raise GenerationError(
            "staging/common production namespaces are not the exact clean4 identity"
        )
    prelock = load_json(prelock_path, "wave_004 v6 prelock")
    verify_self_hash(prelock, "prelock_sha256", "wave_004 v6 prelock")
    if (
        prelock.get("schema_version") != PRELOCK_SCHEMA
        or prelock.get("status") != "frozen_before_first_model_call"
        or prelock.get("generation_id") != GENERATION_ID
        or prelock.get("case_count") != CASE_COUNT
        or prelock.get("first_model_call_authorized") is not False
        or prelock.get("first_model_call_authorization_status")
        != "pending_independent_prelock_audit"
        or prelock.get("freeze_authorized") is not False
    ):
        raise GenerationError("wave_004 v6 prelock identity/status is invalid")

    config_path = verify_regular_file_binding(
        prelock.get("draft_config") or {}, "wave_004 v6 config"
    )
    config = load_json(config_path, "wave_004 v6 config")
    verify_self_hash(config, "config_sha256", "wave_004 v6 config")
    verify_clean4_config_namespace(
        prelock_path=prelock_path, config_path=config_path, config=config
    )
    if (
        config.get("schema_version") != CONFIG_SCHEMA
        or config.get("status") != "prelocked_before_first_model_call"
        or config.get("generation_id") != GENERATION_ID
        or config.get("model") != EXPECTED_MODEL
        or config.get("reasoning_effort") != EXPECTED_REASONING
        or config.get("sandbox") != EXPECTED_SANDBOX
        or config.get("ephemeral") is not True
        or config.get("ignore_user_config") is not True
        or config.get("max_parallel") != PARALLELISM
        or config.get("large_max_parallel") != PARALLELISM
        or config.get("sample_interval_seconds") != 0.1
        or config.get("token_budgets") != [32_000]
        or config.get("attempt_policy")
        != {
            "expected_attempt_index": 1,
            "attempts_per_case": 1,
            "implicit_retry_allowed": False,
            "failed_case_followup": "separate_same_input_repair_generation_namespace_only",
        }
    ):
        raise GenerationError("wave_004 v6 generation config is invalid")
    environment = config.get("child_environment")
    if (
        not isinstance(environment, dict)
        or set(environment) != EXPECTED_ENV_KEYS
        or config.get("child_environment_sha256") != canonical_sha256(environment)
    ):
        raise GenerationError("child environment is not the exact closed set")
    runtime_roots = config.get("isolated_runtime_roots") or {}
    if prelock.get("isolated_runtime_roots") != runtime_roots:
        raise GenerationError("prelock/config isolated runtime roots differ")
    auth_home = Path(str((runtime_roots.get("auth_home") or {}).get("path") or ""))
    isolated_home = Path(
        str((runtime_roots.get("isolated_home") or {}).get("path") or "")
    )
    tmp_root = Path(str((runtime_roots.get("wave_tmp_root") or {}).get("path") or ""))
    if (
        str(auth_home) != environment["CODEX_HOME"]
        or str(tmp_root) != environment["TMPDIR"]
        or str(isolated_home) != environment["HOME"]
        or len({auth_home, isolated_home, tmp_root}) != 3
        or any(path.exists() or path.is_symlink() for path in (auth_home, isolated_home, tmp_root))
        or runtime_roots.get("roots_created_at_prelock") is not False
        or runtime_roots.get("creation_policy")
        != "launcher_O_EXCL_after_independent_final_go_and_fresh_ps_zero_foreign_codex"
        or runtime_roots.get("destruction_policy")
        != "launcher_finally_remove_auth_and_all_three_roots"
    ):
        raise GenerationError("isolated runtime root plan is not exact/absent before final GO")
    auth_descriptor = runtime_roots.get("isolated_auth") or {}
    original_descriptor = runtime_roots.get("original_auth_at_copy") or {}
    isolated_auth = auth_home / "auth.json"
    original_auth = Path(config["original_codex_home_absolute"]) / "auth.json"
    if (
        set(auth_descriptor)
        != {"path", "mode", "parent_mode", "byte_equal_must_be_verified_in_memory_at_launch"}
        or set(original_descriptor)
        != {"path", "mode", "read_only_host_source_for_launch_copy"}
        or Path(str(auth_descriptor.get("path") or "")) != isolated_auth
        or Path(str(original_descriptor.get("path") or "")) != original_auth
        or auth_descriptor.get("mode") != 0o600
        or auth_descriptor.get("parent_mode") != 0o700
        or auth_descriptor.get("byte_equal_must_be_verified_in_memory_at_launch") is not True
        or original_descriptor.get("mode") != 0o600
        or original_descriptor.get("read_only_host_source_for_launch_copy") is not True
        or original_auth.is_symlink()
        or not original_auth.is_file()
        or stat.S_IMODE(original_auth.stat().st_mode) != 0o600
    ):
        raise GenerationError("planned isolated Codex auth source/destination binding failed")
    isolated_home_descriptor = runtime_roots.get("isolated_home") or {}
    if isolated_home_descriptor != {
        "path": str(isolated_home),
        "mode": 0o700,
        "namespace": [],
        "namespace_sha256": canonical_sha256([]),
        "initially_empty": True,
    }:
        raise GenerationError("isolated HOME namespace binding is invalid")
    if config.get("real_home_absolute") != (runtime_roots.get("real_home") or {}).get(
        "path"
    ) or (runtime_roots.get("real_home") or {}).get("access_for_model") != "deny":
        raise GenerationError("real HOME deny binding is invalid")
    verify_executable_binding(config.get("codex_cli") or {}, "Codex CLI")
    verify_executable_binding(config.get("python_runtime") or {}, "Python runtime")
    manifest, snapshot_root = verify_snapshot(config)
    if manifest.get("snapshot_sha256") != (config.get("toolchain_snapshot") or {}).get(
        "snapshot_sha256"
    ):
        raise GenerationError("snapshot internal hash is not config-bound")
    wrapper = verify_regular_file_binding(config["frozen_wrapper"], "frozen v6 wrapper")
    if wrapper != Path(__file__).resolve() or sha256_file(wrapper) != sha256_file(Path(__file__)):
        raise GenerationError("v6 must execute through the frozen launcher copy")
    verify_regular_file_binding(config["frozen_common"], "frozen v6 common module")
    verify_regular_file_binding(
        config["frozen_readonly_helper"], "frozen read-only helper"
    )

    if prelock.get("tool_bindings") != config.get("tool_bindings"):
        raise GenerationError("prelock/config tool bindings differ")
    if prelock.get("codex_feature_surface") != config.get("codex_feature_surface"):
        raise GenerationError("prelock/config Codex feature surface differs")
    for name, binding in sorted((config.get("tool_bindings") or {}).items()):
        verify_regular_file_binding(binding, f"tool binding {name}")
    verify_packet_inputs(prelock, config)
    frozen_reader_coverage = load_and_verify_frozen_reader_coverage(prelock, config)
    if list(frozen_reader_coverage) != list(prelock["case_order"]):
        raise GenerationError("frozen reader coverage readback order changed")

    if prelock.get("reviewed_candidate_approval") != config.get(
        "reviewed_candidate_approval"
    ) or prelock.get("staged_capacity") != config.get("staged_capacity"):
        raise GenerationError("prelock/config candidate approval or capacity binding differs")
    approval_path = verify_regular_file_binding(
        config["reviewed_candidate_approval"], "reviewed candidate approval"
    )
    approval = load_json(approval_path, "reviewed candidate approval")
    verify_self_hash(approval, "approval_sha256", "reviewed candidate approval")
    if (
        approval.get("schema_version")
        != CANDIDATE_REVIEW_SCHEMA
        or approval.get("status") != "approved_for_create_once_candidate_prelock"
        or approval.get("candidate_generation_id") != GENERATION_ID
        or approval.get("model_call_count") != 0
        or approval.get("independent_final_go") is not False
        or approval.get("approval_sha256")
        != config["reviewed_candidate_approval"].get("approval_sha256")
    ):
        raise GenerationError("reviewed candidate approval identity is invalid")
    approval_scripts = approval.get("scripts") or {}
    if set(approval_scripts) != {"common", "launcher", "preparer", "staging"}:
        raise GenerationError("reviewed candidate approval script set is not exact")
    for name, binding in sorted(approval_scripts.items()):
        verify_regular_file_binding(binding, f"reviewed candidate script {name}")
    capacity_path = verify_regular_file_binding(
        config["staged_capacity"], "staged capacity manifest"
    )
    capacity = load_json(capacity_path, "staged capacity manifest")
    verify_self_hash(capacity, "capacity_sha256", "staged capacity manifest")
    capacity_cases = list(capacity.get("cases") or [])
    if (
        capacity.get("status") != "pass_116_of_116"
        or capacity.get("production_namespace") != GENERATION_ID
        or capacity.get("case_count") != CASE_COUNT
        or capacity.get("case_order_sha256") != prelock.get("case_order_sha256")
        or capacity.get("cases_sha256") != canonical_sha256(capacity_cases)
        or [row.get("case_unit_id") for row in capacity_cases]
        != list(prelock["case_order"])
        or any(row.get("within_effective_context") is not True for row in capacity_cases)
        or any(row.get("raw_official_omitted_count") != 0 for row in capacity_cases)
        or capacity.get("raw_official_omitted_total") != 0
        or int(capacity.get("max_observed_reader_envelope_o200k_tokens") or 0)
        > MAX_READER_ENVELOPE_TOKENS
        or int(capacity.get("max_observed_reader_envelope_bytes") or 0)
        > MAX_READER_ENVELOPE_BYTES
        or int(capacity.get("max_observed_plan_page_o200k_tokens") or 0)
        > MAX_COVERAGE_PLAN_PAGE_TOKENS
        or int(capacity.get("max_observed_plan_page_output_bytes") or 0)
        > MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES
        or any(
            int(row.get("max_plan_row_serialized_bytes") or 0)
            > MAX_COVERAGE_PLAN_ROW_BYTES
            for row in capacity_cases
        )
        or int(capacity.get("max_conservative_total_tokens") or 0) > 258_400
        or capacity.get("capacity_sha256")
        != config["staged_capacity"].get("capacity_sha256")
    ):
        raise GenerationError("staged capacity manifest is not an exact 116/116 pass")
    tokenizer = capacity.get("tokenizer") or {}
    tokenizer_root = Path(str(tokenizer.get("root") or ""))
    tokenizer_files = list(tokenizer.get("files") or [])
    if (
        tokenizer.get("encoding") != "o200k_base"
        or tokenizer.get("tiktoken_version") != "0.12.0"
        or tokenizer.get("python_abi") != "cp312"
        or tokenizer.get("file_count") != len(tokenizer_files)
        or tokenizer.get("files_sha256") != canonical_sha256(tokenizer_files)
    ):
        raise GenerationError("tokenizer closure identity is invalid")
    for row in tokenizer_files:
        path = tokenizer_root / str(row.get("relative_path") or "")
        if (
            path.is_symlink()
            or not path.is_file()
            or path.stat().st_size != row.get("size_bytes")
            or sha256_file(path) != row.get("sha256")
        ):
            raise GenerationError(f"tokenizer closure file changed: {path}")
    verify_regular_file_binding(tokenizer["merge_table"], "o200k merge table")

    freeze_path = verify_regular_file_binding(
        prelock.get("old_packet_source_freeze") or {}, "fe2018 packet/source freeze"
    )
    freeze = load_json(freeze_path, "fe2018 packet/source freeze")
    verify_self_hash(freeze, "freeze_sha256", "fe2018 packet/source freeze")
    if freeze.get("freeze_sha256") != EXPECTED_FREEZE_SHA256:
        raise GenerationError("fe2018 freeze internal hash changed")
    index_path = verify_regular_file_binding(prelock["packet_index"], "packet index")
    index = load_json(index_path, "packet index")
    if prelock.get("packet_index_payload_sha256") != canonical_sha256(index):
        raise GenerationError("packet index payload hash mismatch")
    static_path = verify_regular_file_binding(
        prelock["static_acceptance"], "strict static acceptance"
    )
    static = load_json(static_path, "strict static acceptance")
    if static.get("status") != "pass" or static.get("case_count") != CASE_COUNT:
        raise GenerationError("strict packet acceptance is not 116/116 pass")
    verify_regular_file_binding(prelock["source_bundle"], "source bundle")
    agents_path = verify_regular_file_binding(prelock["agents_config"], "agents config")
    if (
        prelock.get("agents_config") != config.get("frozen_context_agents_config")
        or sha256_file(agents_path) != freeze.get("agents_config_hash")
        or prelock.get("llm_roles") != config.get("frozen_context_llm_roles")
        or prelock.get("llm_roles_sha256")
        != canonical_sha256(prelock.get("llm_roles"))
        or config.get("frozen_context_llm_roles_sha256")
        != prelock.get("llm_roles_sha256")
    ):
        raise GenerationError("agents config/llm_roles provenance binding differs")

    readonly_path = verify_regular_file_binding(
        prelock["readonly_before_snapshot"], "read-only before snapshot"
    )
    readonly = load_json(readonly_path, "read-only before snapshot")
    readonly_core = dict(readonly)
    claimed_readonly = readonly_core.pop("snapshot_sha256", None)
    if claimed_readonly != canonical_sha256(readonly_core):
        raise GenerationError("read-only before snapshot self-hash mismatch")
    incident_path = verify_regular_file_binding(
        prelock["wave003_supersession"], "wave_003 supersession"
    )
    incident = load_json(incident_path, "wave_003 supersession")
    verify_self_hash(incident, "incident_sha256", "wave_003 supersession")
    if (
        incident.get("promotion_forbidden") is not True
        or incident.get("old_draft_reuse_forbidden") is not True
        or incident.get("replacement_generation_id") != "wave_004"
    ):
        raise GenerationError("wave_003 supersession does not forbid old draft reuse")
    if prelock.get("prior_candidate_abort") != config.get("prior_candidate_abort"):
        raise GenerationError("prelock/config prior candidate abort binding differs")
    prior_abort_path = verify_regular_file_binding(
        config["prior_candidate_abort"], "clean2 prelock abort incident"
    )
    prior_abort = load_json(prior_abort_path, "clean2 prelock abort incident")
    verify_self_hash(prior_abort, "incident_sha256", "clean2 prelock abort incident")
    if (
        prior_abort.get("candidate_generation_id")
        != "wave_004_v6_clean2_hardened"
        or prior_abort.get("replacement_generation_id")
        != "wave_004_v6_clean3_hardened"
        or prior_abort.get("reuse_forbidden") is not True
        or prior_abort.get("model_call_count") != 0
        or prior_abort.get("incident_sha256")
        != config["prior_candidate_abort"].get("incident_sha256")
    ):
        raise GenerationError("clean2 abort lineage is not exact")
    if prelock.get("prior_clean3_revocation") != config.get(
        "prior_clean3_revocation"
    ):
        raise GenerationError("prelock/config clean3 revocation binding differs")
    clean3_path = verify_regular_file_binding(
        config["prior_clean3_revocation"],
        "clean3 unattributed candidate-review revocation",
    )
    clean3_revocation = load_json(
        clean3_path, "clean3 unattributed candidate-review revocation"
    )
    verify_self_hash(
        clean3_revocation,
        "incident_sha256",
        "clean3 unattributed candidate-review revocation",
    )
    effects = clean3_revocation.get("effects_at_revocation") or {}
    if (
        clean3_revocation.get("schema_version")
        != "androidworld_candidate116_candidate_review_provenance_incident/v1"
        or clean3_revocation.get("status")
        != "revoked_before_prelock_or_model_call"
        or clean3_revocation.get("candidate_generation_id")
        != "wave_004_v6_clean3_hardened"
        or clean3_revocation.get("replacement_generation_id") != GENERATION_ID
        or clean3_revocation.get("reuse_forbidden") is not True
        or effects.get("model_call_count") != 0
        or any(
            effects.get(name) is not False
            for name in (
                "draft_config_created",
                "isolated_runtime_roots_created",
                "prelock_created",
                "raw_wave_created",
                "toolchain_snapshot_created",
            )
        )
        or clean3_revocation.get("incident_sha256")
        != config["prior_clean3_revocation"].get("incident_sha256")
    ):
        raise GenerationError("clean3 revocation lineage is not exact")
    if prelock.get("prior_clean3_prelock_abort") != config.get(
        "prior_clean3_prelock_abort"
    ):
        raise GenerationError("prelock/config clean3 prelock abort binding differs")
    clean3_abort_path = verify_regular_file_binding(
        config["prior_clean3_prelock_abort"], "clean3 prelock abort incident"
    )
    clean3_abort = load_json(clean3_abort_path, "clean3 prelock abort incident")
    verify_self_hash(clean3_abort, "incident_sha256", "clean3 prelock abort incident")
    if (
        clean3_abort.get("schema_version")
        != "androidworld_candidate116_prelock_abort_incident/v1"
        or clean3_abort.get("status")
        != "aborted_before_config_prelock_or_model_call"
        or clean3_abort.get("candidate_generation_id")
        != "wave_004_v6_clean3_hardened"
        or clean3_abort.get("replacement_generation_id") != GENERATION_ID
        or clean3_abort.get("reuse_forbidden") is not True
        or clean3_abort.get("model_call_count") != 0
        or clean3_abort.get("incident_sha256")
        != config["prior_clean3_prelock_abort"].get("incident_sha256")
    ):
        raise GenerationError("clean3 prelock abort lineage is not exact")
    wave003 = Path(config["work_root_absolute"]) / "draft_generation" / "waves" / "wave_003"
    if wave003.exists() or wave003.is_symlink():
        raise GenerationError("superseded wave_003 bytes reappeared")

    policy = config.get("model_input_policy") or {}
    if policy != {
        "packet_kind": "canonical_full_case_packet",
        "packet_count": CASE_COUNT,
        "packet_wrapper_used": False,
        "model_delivery": "sealed_staged_raw_source_reader",
        "full_packet_in_readonly_workspace": True,
        "full_packet_in_stdin": False,
        "raw_official_inventory_trust_boundary": "all_members_mandatory",
        "same_sha_alias_physical_read_policy": "one_read_only_after_all_aliases_bound",
        "ast_and_navigation_role": "cross_audit_never_exclusion_filter",
        "inspect_command_allowed": False,
        "reader_receipt_binding": "ordered_same_id_item_completed_terminal_envelope",
        "coverage_receipt_required_per_case": True,
        "provider_output_fields": ["native", "stronger"],
        "wrapper_injected_fields": ["schema_version", "domain", "case_unit_id", "task_id"],
        "historical_draft_bytes_used": False,
        "historical_qc_or_warning_text_used": False,
        "effective_prompt_components": ["frozen_base_prompt", "clean_canonical_v7_staged"],
    }:
        raise GenerationError("canonical-only model input policy is not exact")
    expected_command = expected_native_batch_command(config, prelock)
    if (
        config.get("native_batch_command") != expected_command
        or config.get("native_batch_command_sha256") != canonical_sha256(expected_command)
    ):
        raise GenerationError("native batch argv is not exactly reconstructed")
    output_root = Path(config["output_root_absolute"])
    if output_root.exists() or output_root.is_symlink():
        raise GenerationError("wave_004 output namespace already exists")
    require_empty_or_absent(Path(config["canonical_drafts_absolute"]), "canonical drafts")
    require_empty_or_absent(
        Path(config["canonical_contracts_absolute"]), "canonical contracts/drafts"
    )
    return prelock, config, snapshot_root


def parse_exact_login(completed: subprocess.CompletedProcess[str]) -> tuple[str, bool]:
    lines = [
        line.strip()
        for part in (completed.stdout, completed.stderr)
        for line in (part or "").splitlines()
        if line.strip()
    ]
    warning = bool(lines and lines[0] == ALLOWED_LOGIN_WARNING)
    if warning:
        lines = lines[1:]
    if completed.returncode != 0 or lines != ["Logged in using ChatGPT"]:
        raise GenerationError(
            f"Codex login is not exact ChatGPT login: rc={completed.returncode}, lines={lines}"
        )
    return "Logged in using ChatGPT", warning


def codex_check(
    config: Mapping[str, Any], *, require_initial_namespace: bool = True
) -> dict[str, Any]:
    executable = verify_executable_binding(config["codex_cli"], "Codex CLI")
    environment = dict(config["child_environment"])
    version = subprocess.run(
        [str(executable), "--version"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if (
        version.returncode != 0
        or version.stdout.strip() != EXPECTED_CODEX_VERSION
        or version.stderr.strip()
    ):
        raise GenerationError("Codex version changed after prelock")
    login = subprocess.run(
        [str(executable), "login", "status"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    status, warning = parse_exact_login(login)
    auth_home = Path(environment["CODEX_HOME"])
    child_home = Path(environment["HOME"])
    tmp_root = Path(environment["TMPDIR"])
    if (
        (require_initial_namespace and sorted(path.name for path in auth_home.iterdir()) != ["auth.json"])
        or any(child_home.iterdir())
        or any(tmp_root.iterdir())
    ):
        raise GenerationError("Codex status probe changed an isolated runtime namespace")
    receipt = {
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "version": version.stdout.strip(),
        "login_status": status,
        "allowed_path_alias_warning_observed": warning,
        "initial_auth_namespace_required": require_initial_namespace,
        "closed_environment_sha256": canonical_sha256(environment),
    }
    return add_self_hash(receipt, "auth_check_sha256")


def create_authorized_runtime_roots(config: Mapping[str, Any]) -> dict[str, Any]:
    """Create auth/HOME/TMP only after final GO and a zero-foreign fresh ps."""

    roots = config["isolated_runtime_roots"]
    auth_home = Path(roots["auth_home"]["path"])
    child_home = Path(roots["isolated_home"]["path"])
    tmp_root = Path(roots["wave_tmp_root"]["path"])
    original_auth = Path(roots["original_auth_at_copy"]["path"])
    isolated_auth = Path(roots["isolated_auth"]["path"])
    if (
        len({auth_home, child_home, tmp_root}) != 3
        or isolated_auth != auth_home / "auth.json"
        or any(path.exists() or path.is_symlink() for path in (auth_home, child_home, tmp_root))
        or original_auth.is_symlink()
        or not original_auth.is_file()
        or stat.S_IMODE(original_auth.stat().st_mode) != 0o600
    ):
        raise GenerationError("authorized runtime roots/source auth are not exact and absent")
    created: list[Path] = []
    try:
        before = original_auth.lstat()
        source_bytes = original_auth.read_bytes()
        after = original_auth.lstat()
        if (
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or not hmac.compare_digest(source_bytes, original_auth.read_bytes())
        ):
            raise GenerationError("original auth changed during authorized in-memory copy")
        os.mkdir(auth_home, 0o700)
        created.append(auth_home)
        descriptor = os.open(
            isolated_auth,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(source_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(isolated_auth, 0o600)
        if not hmac.compare_digest(source_bytes, isolated_auth.read_bytes()):
            raise GenerationError("isolated auth in-memory byte equality check failed")
        del source_bytes
        os.mkdir(child_home, 0o700)
        created.append(child_home)
        os.mkdir(tmp_root, 0o700)
        created.append(tmp_root)
        for path in (auth_home, child_home, tmp_root):
            os.chmod(path, 0o700)
        if (
            sorted(path.name for path in auth_home.iterdir()) != ["auth.json"]
            or any(child_home.iterdir())
            or any(tmp_root.iterdir())
        ):
            raise GenerationError("new isolated runtime namespaces are not exact")
    except BaseException:
        for path in reversed(created):
            if path.exists() and not path.is_symlink():
                shutil.rmtree(path)
        raise
    return {
        "schema_version": "androidworld_candidate116_authorized_runtime_creation/v6_clean4_hardened",
        "status": "created_after_final_go_and_zero_foreign_codex",
        "auth_home": {"path": str(auth_home), "mode": 0o700, "namespace": ["auth.json"]},
        "isolated_auth": {
            "path": str(isolated_auth),
            "mode": 0o600,
            "byte_equal_verified_in_memory": True,
            "content_hash_persisted": False,
        },
        "isolated_home": {"path": str(child_home), "mode": 0o700, "namespace": []},
        "wave_tmp_root": {"path": str(tmp_root), "mode": 0o700, "namespace": []},
    }


def destroy_authorized_runtime_roots(config: Mapping[str, Any]) -> dict[str, Any]:
    """Destroy the sensitive auth copy and all ephemeral namespaces on every exit."""

    roots = config["isolated_runtime_roots"]
    paths = [
        Path(roots["auth_home"]["path"]),
        Path(roots["isolated_home"]["path"]),
        Path(roots["wave_tmp_root"]["path"]),
    ]
    if len(set(paths)) != 3:
        raise GenerationError("runtime cleanup roots are not distinct")
    for path in paths:
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
    absent = {str(path): not path.exists() and not path.is_symlink() for path in paths}
    if not all(absent.values()):
        raise GenerationError("sensitive runtime cleanup did not remove every planned root")
    return {
        "schema_version": "androidworld_candidate116_authorized_runtime_cleanup/v6_clean4_hardened",
        "status": "pass",
        "auth_content_or_hash_recorded": False,
        "paths": [
            {"path": str(path), "path_absent": absent[str(path)]} for path in paths
        ],
        "all_paths_absent": True,
    }


def verify_codex_feature_surface(config: Mapping[str, Any]) -> None:
    expected = config.get("codex_feature_surface") or {}
    verify_self_hash(expected, "feature_surface_sha256", "Codex feature surface")
    executable = verify_executable_binding(config["codex_cli"], "Codex CLI")
    completed = subprocess.run(
        [str(executable), "features", "list"],
        env=dict(config["child_environment"]),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0 or completed.stderr.strip():
        raise GenerationError("Codex feature registry changed or cannot be read")
    rows = []
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[-1] not in {"true", "false"}:
            raise GenerationError("Codex feature registry row is not parseable")
        rows.append(
            {
                "name": parts[0],
                "stage": " ".join(parts[1:-1]),
                "default_enabled": parts[-1] == "true",
            }
        )
    if (
        rows != expected.get("rows")
        or canonical_sha256(rows) != expected.get("rows_sha256")
        or list(DISABLED_CODEX_FEATURES) != expected.get("disabled_features")
        or canonical_sha256(list(DISABLED_CODEX_FEATURES))
        != expected.get("disabled_features_sha256")
        or expected.get("strict_config_parse_status") != "pass_no_model_call"
        or expected.get("allowed_execution_surface") != ["shell_tool", "unified_exec"]
    ):
        raise GenerationError("Codex feature surface/deny set differs from prelock")


def ps_rows() -> dict[int, dict[str, Any]]:
    completed = subprocess.run(
        ["/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,command="],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        raise GenerationError(f"fresh /bin/ps failed: {completed.stderr.strip()}")
    rows: dict[int, dict[str, Any]] = {}
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) != 4:
            continue
        try:
            pid, ppid, pgid = map(int, parts[:3])
        except ValueError:
            continue
        try:
            argv = shlex.split(parts[3])
        except ValueError:
            argv = []
        rows[pid] = {
            "pid": pid,
            "ppid": ppid,
            "pgid": pgid,
            "command": parts[3],
            "argv": argv,
        }
    return rows


def ancestor_pids(rows: Mapping[int, Mapping[str, Any]], pid: int) -> set[int]:
    result = {pid}
    current = pid
    while current in rows:
        parent = int(rows[current]["ppid"])
        if parent <= 0 or parent in result:
            break
        result.add(parent)
        current = parent
    return result


def is_drafting_argv(argv: list[str]) -> bool:
    if not argv:
        return False
    basenames = [Path(token).name for token in argv]
    if "run_draft_batch.py" in basenames or "draft_case_checklist.py" in basenames:
        return True
    return any(
        Path(token).name.startswith("codex")
        and "exec" in argv[index + 1 :]
        for index, token in enumerate(argv)
    )


def foreign_drafting_from_rows(
    rows: Mapping[int, Mapping[str, Any]], *, allowed_pgid: int | None = None
) -> list[dict[str, Any]]:
    excluded = ancestor_pids(rows, os.getpid())
    result = []
    for pid, row in sorted(rows.items()):
        if pid in excluded or (allowed_pgid is not None and row["pgid"] == allowed_pgid):
            continue
        if is_drafting_argv(list(row["argv"])):
            result.append(
                {
                    "pid": pid,
                    "ppid": row["ppid"],
                    "pgid": row["pgid"],
                    "command_sha256": canonical_sha256(row["command"]),
                }
            )
    return result


def foreign_drafting_processes(*, allowed_pgid: int | None = None) -> list[dict[str, Any]]:
    return foreign_drafting_from_rows(ps_rows(), allowed_pgid=allowed_pgid)


def single_popen_after_fresh_ps(
    command: list[str],
    *,
    cwd: str,
    environment: Mapping[str, str],
    stdout: Any,
    stderr: Any,
    foreign_probe: Callable[[], list[dict[str, Any]]] = foreign_drafting_processes,
    popen_factory: Callable[..., Any] = subprocess.Popen,
    audit: dict[str, Any] | None = None,
) -> Any:
    """Perform one fresh process probe followed directly by exactly one batch Popen."""

    foreign = foreign_probe()
    if audit is not None:
        audit["fresh_ps_completed_monotonic_ns"] = time.monotonic_ns()
        audit["fresh_ps_foreign_processes"] = foreign
        audit["foreign_probe_count_in_barrier"] = 1
    if foreign:
        raise GenerationError(f"foreign drafting process appeared in launch barrier: {foreign}")
    process = popen_factory(
        command,
        cwd=cwd,
        env=dict(environment),
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
    )
    if audit is not None:
        audit["batch_popen_completed_monotonic_ns"] = time.monotonic_ns()
        audit["batch_popen_count"] = 1
        audit["intervening_subprocess_count"] = 0
    return process


def normalized_codex_ps_argv(argv: list[str]) -> list[str]:
    quoted_config_prefixes = (
        "default_permissions=",
        "permissions.",
        "model_reasoning_effort=",
        "model_verbosity=",
        "web_search=",
        "shell_environment_policy.inherit=",
    )
    return [
        token.replace('\\"', '"').replace('"', "")
        if token.startswith(quoted_config_prefixes)
        else token
        for token in argv
    ]


def validate_codex_exec_argv(argv: list[str], config: Mapping[str, Any]) -> Path:
    argv = normalized_codex_ps_argv(argv)
    try:
        workspace = Path(argv[argv.index("--cd") + 1])
    except (ValueError, IndexError) as exc:
        raise GenerationError(f"Codex exec lacks one exact workspace: {argv}") from exc
    expected = normalized_codex_ps_argv(
        build_codex_exec_argv(
            codex_executable=Path(config["codex_cli"]["resolved_path"]),
            workspace_root=workspace,
            schema_path=workspace / "output_schema.json",
            output_path=workspace / "draft_body.json",
            model=EXPECTED_MODEL,
            reasoning_effort=EXPECTED_REASONING,
            repository_root=Path(config["repository_root_absolute"]),
            wave_tmp_root=Path(config["child_environment"]["TMPDIR"]),
            auth_home=Path(config["child_environment"]["CODEX_HOME"]),
            original_codex_home=Path(config["original_codex_home_absolute"]),
            isolated_home=Path(config["child_environment"]["HOME"]),
            real_home=Path(config["real_home_absolute"]),
        )
    )
    if (
        argv != expected
        or require_safe_case_id(workspace.name) != workspace.name
        or workspace.parent != Path(config["child_environment"]["TMPDIR"])
        or workspace.is_symlink()
    ):
        raise GenerationError(f"Codex exec argv is not native/exact: {argv}")
    return workspace


def validate_drafter_argv(
    argv: list[str], config: Mapping[str, Any], packet_by_path: Mapping[str, str]
) -> str:
    if len(argv) != 25:
        raise GenerationError(f"drafter argv length is not exact: {argv}")
    packet = argv[2]
    case_id = packet_by_path.get(packet)
    if case_id is None:
        raise GenerationError(f"drafter did not receive a bound canonical packet: {packet}")
    case_dir = Path(config["output_root_absolute"]) / case_id
    attempt_yaml = Path(argv[4])
    if (
        attempt_yaml.parent != case_dir
        or attempt_yaml.name != "attempt_01.checklist.yaml"
    ):
        raise GenerationError(f"drafter output is outside bound case directory: {attempt_yaml}")
    prefix = attempt_yaml.name.removesuffix(".checklist.yaml")
    expected = [
        str(config["python_runtime"]["path"]),
        str(config["tool_bindings"]["drafter"]["path"]),
        packet,
        "-o",
        str(case_dir / f"{prefix}.checklist.yaml"),
        "--raw-json-output",
        str(case_dir / f"{prefix}.checklist.json"),
        "--raw-api-response",
        str(case_dir / f"{prefix}.api_response.json"),
        "--model",
        EXPECTED_MODEL,
        "--provider",
        "codex",
        "--reasoning-effort",
        EXPECTED_REASONING,
        "--max-output-tokens",
        argv[16],
        "--http-timeout-seconds",
        "180",
        "--codex-timeout-seconds",
        str(config["codex_timeout_seconds"]),
        "--codex-sandbox",
        EXPECTED_SANDBOX,
        "--prompt-supplement",
        str(config["tool_bindings"]["prompt_supplement"]["path"]),
    ]
    if argv != expected or int(argv[16]) != 32_000:
        raise GenerationError(f"drafter argv is not native/exact: {argv}")
    return case_id


def validate_validator_argv(
    argv: list[str], config: Mapping[str, Any], packet_by_path: Mapping[str, str]
) -> str:
    if len(argv) != 5 or argv[3] != "--case-packet":
        raise GenerationError(f"validator argv is not exact: {argv}")
    case_id = packet_by_path.get(argv[4])
    if (
        case_id is None
        or argv[0] != str(config["python_runtime"]["path"])
        or argv[1] != str(config["tool_bindings"]["validator"]["path"])
        or Path(argv[2]).parent != Path(config["output_root_absolute"]) / case_id
    ):
        raise GenerationError(f"validator argv is not bound to one canonical case: {argv}")
    return case_id


def descendant_of(rows: Mapping[int, Mapping[str, Any]], pid: int, ancestor: int) -> bool:
    seen: set[int] = set()
    current = pid
    while current in rows and current not in seen:
        if current == ancestor:
            return True
        seen.add(current)
        current = int(rows[current]["ppid"])
    return False


def is_codex_exec_argv(argv: list[str]) -> bool:
    return any(
        Path(token).name.startswith("codex") and "exec" in argv[index + 1 :]
        for index, token in enumerate(argv)
    )


def _reader_argv_ledger(workspace: Path) -> set[tuple[str, ...]]:
    manifest_path = workspace / "model_input_coverage.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise GenerationError("live Codex workspace lacks a regular coverage manifest")
    requirements = load_json(manifest_path, "live case coverage requirements")
    requirements_sha = str(requirements.get("requirements_sha256") or "")
    ledger: set[tuple[str, ...]] = {
        ("/usr/bin/python3", "packet_reader.py", "overview"),
        ("/usr/bin/python3", "packet_reader.py", "header"),
    }
    for page in range(int(requirements.get("coverage_page_count") or 0)):
        ledger.add(
            (
                "/usr/bin/python3",
                "packet_reader.py",
                "plan-page",
                "--page",
                str(page),
                "--manifest-sha256",
                requirements_sha,
            )
        )
    for row in requirements.get("required_ranges") or []:
        ledger.add(
            (
                "/usr/bin/python3",
                "packet_reader.py",
                "read",
                "--anchor",
                str(row["anchor"]),
                "--path",
                str(row["path"]),
                "--start",
                str(row["start_line"]),
                "--end",
                str(row["end_line"]),
                "--manifest-sha256",
                requirements_sha,
            )
        )
    return ledger


def validate_reader_descendant_argv(argv: list[str], workspace: Path) -> None:
    """Allow only one exact reader command (or its one shell carrier)."""

    candidate = argv
    if (
        len(argv) == 3
        and argv[0] == "/bin/zsh"
        and argv[1] == "-lc"
    ):
        try:
            candidate = shlex.split(argv[2])
        except ValueError as exc:
            raise GenerationError("reader shell carrier is not parseable") from exc
        if argv[2] != " ".join(candidate):
            raise GenerationError("reader shell carrier contains quoting/operators/wrappers")
    if tuple(candidate) not in _reader_argv_ledger(workspace):
        raise GenerationError(f"Codex descendant is not one frozen reader argv: {argv}")


def inspect_batch_processes(
    rows: Mapping[int, Mapping[str, Any]],
    *,
    batch_pid: int,
    config: Mapping[str, Any],
    packet_by_path: Mapping[str, str],
) -> dict[str, Any]:
    active: list[dict[str, Any]] = []
    drafter_pids: dict[int, str] = {}
    codex_rows: dict[int, tuple[dict[str, Any], Path]] = {}
    other_rows: dict[int, dict[str, Any]] = {}
    batch_command = list(config["native_batch_command"])
    for pid, row in sorted(rows.items()):
        if row["pgid"] != batch_pid:
            continue
        argv = list(row["argv"])
        if pid == batch_pid:
            if argv != batch_command:
                raise GenerationError(f"live native batch argv changed: {argv}")
            continue
        if len(argv) > 1 and argv[1] == config["tool_bindings"]["drafter"]["path"]:
            case_id = validate_drafter_argv(argv, config, packet_by_path)
            drafter_pids[pid] = case_id
            active.append(
                {
                    "pid": pid,
                    "case_unit_id": case_id,
                    "argv_sha256": canonical_sha256(argv),
                }
            )
        elif len(argv) > 1 and argv[1] == config["tool_bindings"]["validator"]["path"]:
            validate_validator_argv(argv, config, packet_by_path)
        elif is_codex_exec_argv(argv):
            codex_rows[pid] = (dict(row), validate_codex_exec_argv(argv, config))
        else:
            other_rows[pid] = dict(row)
    codex_active: list[dict[str, Any]] = []
    codex_per_drafter: dict[int, int] = {}
    for pid, (row, workspace) in sorted(codex_rows.items()):
        parents = [
            (drafter_pid, case_id)
            for drafter_pid, case_id in drafter_pids.items()
            if descendant_of(rows, pid, drafter_pid)
        ]
        if len(parents) != 1:
            raise GenerationError("Codex exec is not owned by exactly one active case drafter")
        drafter_pid, case_id = parents[0]
        if workspace.name != case_id:
            raise GenerationError("Codex workspace basename is not its exact case_unit_id")
        codex_per_drafter[drafter_pid] = codex_per_drafter.get(drafter_pid, 0) + 1
        codex_active.append(
            {
                "pid": pid,
                "drafter_pid": drafter_pid,
                "case_unit_id": case_id,
                "workspace": str(workspace),
                "argv_sha256": canonical_sha256(row["argv"]),
            }
        )
    if any(count > 1 for count in codex_per_drafter.values()):
        raise GenerationError("one case drafter owns more than one simultaneous Codex exec")
    for pid, row in sorted(other_rows.items()):
        parents = [
            (codex_pid, workspace)
            for codex_pid, (_codex_row, workspace) in codex_rows.items()
            if descendant_of(rows, pid, codex_pid)
        ]
        if len(parents) != 1:
            raise GenerationError(f"unknown process in wave_004 process group: {row}")
        validate_reader_descendant_argv(list(row["argv"]), parents[0][1])
    if len(active) > PARALLELISM:
        raise GenerationError(f"observed more than six concurrent case attempts: {active}")
    if len(codex_active) > PARALLELISM:
        raise GenerationError(f"observed more than six concurrent Codex execs: {codex_active}")
    return {
        "active_case_attempts": sorted(active, key=lambda item: item["case_unit_id"]),
        "active_codex_execs": sorted(codex_active, key=lambda item: item["case_unit_id"]),
    }


def monitor_batch(
    process: Any,
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    stop: threading.Event,
    state: dict[str, Any],
    lock: threading.Lock,
) -> None:
    samples_path = Path(config["concurrency_samples_absolute"])
    packet_by_path = {
        str(row["packet"]["path"]): row["case_unit_id"] for row in prelock["packet_inputs"]
    }
    previous: str | None = None
    sequence = 0
    next_deadline = time.monotonic()
    try:
        with samples_path.open("x", encoding="utf-8", buffering=1) as handle:
            while True:
                rows = ps_rows()
                foreign = foreign_drafting_from_rows(rows, allowed_pgid=process.pid)
                if foreign:
                    raise GenerationError(
                        f"foreign drafting process appeared during wave_004: {foreign}"
                    )
                process_state = inspect_batch_processes(
                    rows,
                    batch_pid=process.pid,
                    config=config,
                    packet_by_path=packet_by_path,
                )
                active = process_state["active_case_attempts"]
                active_codex = process_state["active_codex_execs"]
                sample = {
                    "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_concurrency_sample/v1",
                    "sequence": sequence,
                    "previous_sample_sha256": previous,
                    "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "monotonic_ns": time.monotonic_ns(),
                    "batch_pid": process.pid,
                    "active_case_attempt_count": len(active),
                    "active_case_attempts": active,
                    "active_codex_exec_count": len(active_codex),
                    "active_codex_execs": active_codex,
                    "foreign_drafting_processes": [],
                    "native_argv_validation": "pass",
                }
                sample = add_self_hash(sample, "sample_sha256")
                handle.write(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                previous = sample["sample_sha256"]
                with lock:
                    state["sample_count"] += 1
                    state["drafter_peak"] = max(state["drafter_peak"], len(active))
                    state["codex_peak"] = max(state["codex_peak"], len(active_codex))
                    state["covered"].update(item["case_unit_id"] for item in active)
                    state["codex_covered"].update(
                        item["case_unit_id"] for item in active_codex
                    )
                sequence += 1
                if stop.is_set():
                    break
                next_deadline += 0.1
                stop.wait(max(0.0, next_deadline - time.monotonic()))
    except BaseException as exc:
        with lock:
            state["errors"].append(f"{type(exc).__name__}: {exc}")
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def process_group_rows(pgid: int) -> list[dict[str, Any]]:
    return [dict(row) for row in ps_rows().values() if row["pgid"] == pgid]


def clear_process_group(process: Any) -> None:
    pgid = int(process.pid)
    deadline = time.monotonic() + 5
    rows = process_group_rows(pgid)
    if rows:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    while rows and time.monotonic() < deadline:
        time.sleep(0.05)
        rows = process_group_rows(pgid)
    if rows:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 5
        while rows and time.monotonic() < deadline:
            time.sleep(0.05)
            rows = process_group_rows(pgid)
    if rows:
        raise GenerationError(f"wave_004 process group is not empty after cleanup: {rows}")
    try:
        process.wait(timeout=1)
    except (subprocess.TimeoutExpired, ChildProcessError):
        pass


def read_and_verify_samples(
    path: Path, case_order: list[str]
) -> tuple[list[dict[str, Any]], int, int, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise GenerationError("concurrency sample chain is empty")
    samples: list[dict[str, Any]] = []
    previous: str | None = None
    covered: set[str] = set()
    drafter_peak = 0
    codex_peak = 0
    codex_covered: set[str] = set()
    prior_monotonic = 0
    for sequence, line in enumerate(lines):
        try:
            sample = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GenerationError(f"malformed concurrency sample {sequence}") from exc
        if not isinstance(sample, dict):
            raise GenerationError(f"concurrency sample {sequence} is not an object")
        verify_self_hash(sample, "sample_sha256", f"concurrency sample {sequence}")
        if (
            sample.get("sequence") != sequence
            or sample.get("previous_sample_sha256") != previous
            or sample.get("native_argv_validation") != "pass"
            or sample.get("foreign_drafting_processes") != []
            or sample.get("active_case_attempt_count")
            != len(sample.get("active_case_attempts") or [])
            or int(sample.get("active_case_attempt_count") or 0) > PARALLELISM
            or sample.get("active_codex_exec_count")
            != len(sample.get("active_codex_execs") or [])
            or int(sample.get("active_codex_exec_count") or 0) > PARALLELISM
            or int(sample.get("monotonic_ns") or 0) <= prior_monotonic
        ):
            raise GenerationError(f"concurrency sample chain invariant failed at {sequence}")
        count = int(sample["active_case_attempt_count"])
        drafter_peak = max(drafter_peak, count)
        codex_count = int(sample["active_codex_exec_count"])
        codex_peak = max(codex_peak, codex_count)
        covered.update(item["case_unit_id"] for item in sample["active_case_attempts"])
        codex_covered.update(item["case_unit_id"] for item in sample["active_codex_execs"])
        previous = sample["sample_sha256"]
        prior_monotonic = int(sample["monotonic_ns"])
        samples.append(sample)
    if (
        drafter_peak != PARALLELISM
        or codex_peak != PARALLELISM
        or sorted(covered) != sorted(case_order)
        or sorted(codex_covered) != sorted(case_order)
    ):
        raise GenerationError(
            "exact-six/all-116 sample gate failed: "
            f"drafter_peak={drafter_peak}, codex_peak={codex_peak}, "
            f"drafter_covered={len(covered)}, codex_covered={len(codex_covered)}"
        )
    return samples, drafter_peak, codex_peak, sorted(covered)


def verify_generated_cases(
    *, output_root: Path, prelock: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    summary_path = output_root / "_batch_summary.json"
    results_path = output_root / "_batch_results.jsonl"
    summary = load_json(summary_path, "native batch summary")
    if (
        summary.get("total_cases") != CASE_COUNT
        or summary.get("completed_cases") != CASE_COUNT
        or summary.get("success_cases") != CASE_COUNT
        or summary.get("failed_cases") != 0
        or summary.get("skipped_cases") != 0
        or summary.get("provider") != "codex"
        or summary.get("model") != EXPECTED_MODEL
        or summary.get("reasoning_effort") != EXPECTED_REASONING
        or summary.get("codex_sandbox") != EXPECTED_SANDBOX
    ):
        raise GenerationError("native batch summary is not a clean exact 116/116 success")
    results: list[dict[str, Any]] = []
    for index, line in enumerate(results_path.read_text(encoding="utf-8").splitlines()):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GenerationError(f"malformed native result line {index}") from exc
        if not isinstance(row, dict):
            raise GenerationError(f"native result line {index} is not an object")
        results.append(row)
    expected = set(prelock["case_order"])
    observed = [row.get("case_unit_dir") for row in results]
    if len(results) != CASE_COUNT or len(set(observed)) != CASE_COUNT or set(observed) != expected:
        raise GenerationError("native batch results do not contain exactly 116 unique cases")
    result_by_case = {str(row["case_unit_dir"]): row for row in results}

    snapshot_root = Path(config["snapshot_root_absolute"])
    sys.path.insert(0, str(snapshot_root))
    try:
        import yaml  # type: ignore
        from jsonschema import Draft202012Validator  # type: ignore
        from neurips_ed_track_minimal.checklist_guardrails import (  # type: ignore
            case_packet_support_paths,
            validate_checklist_guardrails,
        )
    finally:
        if sys.path and sys.path[0] == str(snapshot_root):
            sys.path.pop(0)
    schema = load_json(
        Path(config["tool_bindings"]["checklist_schema"]["path"]), "checklist schema"
    )
    validator = Draft202012Validator(schema)
    packet_by_case = {row["case_unit_id"]: row for row in prelock["packet_inputs"]}
    capacity_path = verify_regular_file_binding(
        config["staged_capacity"], "staged capacity manifest"
    )
    capacity = load_json(capacity_path, "staged capacity manifest")
    capacity_by_case = {
        str(row["case_unit_id"]): row for row in capacity.get("cases") or []
    }
    coverage_by_case = load_and_verify_frozen_reader_coverage(prelock, config)
    case_receipts = []
    for case_id in prelock["case_order"]:
        row = result_by_case[case_id]
        packet_path = Path(packet_by_case[case_id]["packet"]["path"])
        if (
            row.get("status") != "success"
            or Path(str(row.get("case_packet") or "")).resolve() != packet_path
            or row.get("quality_warnings") != []
            or len(row.get("attempts") or []) != 1
            or (row.get("attempts") or [{}])[0].get("attempt_index") != 1
            or (row.get("attempts") or [{}])[0].get("max_output_tokens") != 32_000
            or (row.get("attempts") or [{}])[0].get("returncode") != 0
        ):
            raise GenerationError(f"native result is not exact success for {case_id}")
        case_dir = output_root / case_id
        if case_dir.is_symlink() or not case_dir.is_dir():
            raise GenerationError(f"generated case directory is missing/symlinked: {case_id}")
        required = (
            "checklist.yaml",
            "checklist.json",
            "api_response.json",
            "llm_call.json",
            "reasoning_summary.txt",
            "stderr.log",
            "stdout.log",
        )
        expected_case_namespace = {
            *required,
            *(f"attempt_01.{name}" for name in required),
        }
        observed_case_namespace = {
            path.name for path in case_dir.iterdir() if path.is_file() and not path.is_symlink()
        }
        if observed_case_namespace != expected_case_namespace or any(
            path.is_symlink() or not path.is_file() for path in case_dir.iterdir()
        ):
            raise GenerationError(
                f"case namespace is not exact final+attempt_01 only for {case_id}: "
                f"{sorted(observed_case_namespace ^ expected_case_namespace)}"
            )
        bindings = {}
        for name in required:
            path = case_dir / name
            bindings[name] = regular_file_binding(path)
            if path.read_bytes() != (case_dir / f"attempt_01.{name}").read_bytes():
                raise GenerationError(
                    f"stable/attempt_01 outputs differ bytewise for {case_id}/{name}"
                )
        checklist_yaml = yaml.safe_load((case_dir / "checklist.yaml").read_text(encoding="utf-8"))
        checklist_json = load_json(case_dir / "checklist.json", f"{case_id} checklist JSON")
        if not isinstance(checklist_yaml, dict) or checklist_yaml != checklist_json:
            raise GenerationError(f"YAML/JSON checklist bodies differ for {case_id}")
        errors = sorted(
            validator.iter_errors(checklist_yaml), key=lambda item: list(item.absolute_path)
        )
        if errors:
            raise GenerationError(f"schema validation failed for {case_id}: {errors[0].message}")
        allowed = case_packet_support_paths(packet_path.read_text(encoding="utf-8"))
        if "case_packet.md" in allowed:
            raise GenerationError("adapted guardrail still permits case_packet.md alias")
        validate_checklist_guardrails(checklist_yaml, allowed_source_paths=allowed)
        if (
            checklist_yaml.get("domain") != "androidworld"
            or checklist_yaml.get("case_unit_id") != case_id
            or checklist_yaml.get("task_id") != packet_by_case[case_id]["task_id"]
        ):
            raise GenerationError(f"checklist identity mismatch for {case_id}")
        llm = load_json(case_dir / "llm_call.json", f"{case_id} llm_call")
        metadata = llm.get("response_metadata") or {}
        if (
            llm.get("provider") != "codex_cli"
            or llm.get("model") != EXPECTED_MODEL
            or llm.get("model_version") != EXPECTED_MODEL
            or llm.get("api_key_env") != "CODEX_HOME"
            or llm.get("domain") != "androidworld"
            or llm.get("case_unit_id") != case_id
            or llm.get("task_id") != packet_by_case[case_id]["task_id"]
            or llm.get("phase") != "draft"
            or llm.get("max_tokens") not in config["token_budgets"]
            or llm.get("timeout_seconds") != config["codex_timeout_seconds"]
            or metadata.get("auth_mode") != "codex_login"
            or metadata.get("reasoning_effort") != EXPECTED_REASONING
            or metadata.get("provider_model") != EXPECTED_MODEL
        ):
            raise GenerationError(f"LLM provenance is not exact for {case_id}")
        api = load_json(case_dir / "api_response.json", f"{case_id} API response")
        codex_receipt = api.get("codex_cli") or {}
        coverage = codex_receipt.get("coverage_receipt") or {}
        verify_self_hash(coverage, "coverage_receipt_sha256", f"{case_id} coverage receipt")
        frozen_documents = coverage_by_case[case_id]
        requirements = frozen_documents["requirements"]
        operation_expectations = frozen_documents[
            "reader_operation_expectations"
        ]
        frozen_readback = codex_receipt.get("frozen_coverage_readback") or {}
        expected_frozen_case_root = Path(
            frozen_documents["index_row"]["requirements"]["path"]
        ).parent
        events = codex_receipt.get("events")
        if not isinstance(events, list) or not all(
            isinstance(event, dict) for event in events
        ):
            raise GenerationError(f"Codex event ledger is invalid for {case_id}")
        try:
            replayed_coverage = coverage_receipt_from_events(
                events, requirements, operation_expectations
            )
            verify_coverage_receipt_against_events(
                coverage, events, requirements, operation_expectations
            )
        except BaseException as exc:
            raise GenerationError(
                f"independent A/B event replay failed for {case_id}: {exc}"
            ) from exc
        if (
            api.get("provider") != "codex_cli"
            or api.get("model") != EXPECTED_MODEL
            or api.get("status") != "completed"
            or codex_receipt.get("permission_profile") != "candidate_draft_isolated"
            or codex_receipt.get("permission_profile_workspace_access") != "read"
            or codex_receipt.get("permission_profile_network_enabled") is not False
            or codex_receipt.get("full_canonical_packet_in_stdin") is not False
            or codex_receipt.get("full_canonical_packet_in_readonly_workspace") is not True
            or codex_receipt.get("malformed_event_lines") != []
            or codex_receipt.get("requirements_sha256")
            != requirements["requirements_sha256"]
            or codex_receipt.get("reader_operation_expectations_sha256")
            != operation_expectations["reader_operation_expectations_sha256"]
            or frozen_readback.get("schema_version")
            != (
                "androidworld_candidate116_runtime_frozen_reader_coverage_readback/"
                "v6_clean4_hardened"
            )
            or frozen_readback.get("production_namespace") != GENERATION_ID
            or frozen_readback.get("case_unit_id") != case_id
            or Path(str(frozen_readback.get("frozen_case_root") or ""))
            != expected_frozen_case_root
            or frozen_readback.get("requirements_sha256")
            != requirements["requirements_sha256"]
            or frozen_readback.get("reader_operation_expectations_sha256")
            != operation_expectations["reader_operation_expectations_sha256"]
            or frozen_readback.get("workspace_A_B_byte_equal_to_frozen") is not True
            or frozen_readback.get("A_B_gate_passed_before_model_call") is not True
            or coverage.get("schema_version")
            != "androidworld_candidate116_staged_source_coverage_receipt/v2"
            or coverage.get("production_namespace") != GENERATION_ID
            or coverage.get("status") != "all_required_reader_operations_completed"
            or coverage.get("case_unit_id") != case_id
            or coverage.get("requirements_sha256")
            != requirements["requirements_sha256"]
            or coverage.get("reader_operation_expectations_sha256")
            != operation_expectations["reader_operation_expectations_sha256"]
            or coverage.get("operations_sha256")
            != operation_expectations["operations_sha256"]
            or capacity_by_case[case_id]["requirements_sha256"]
            != requirements["requirements_sha256"]
            or capacity_by_case[case_id]["reader_operation_expectations_sha256"]
            != operation_expectations["reader_operation_expectations_sha256"]
            or coverage.get("covered_range_count")
            != coverage.get("required_range_count")
            or coverage.get("coverage_page_count")
            != len(coverage.get("coverage_pages_read") or [])
            or coverage.get("additional_command_count") != 0
            or coverage.get("global_order")
            != "overview_then_header_then_all_pages_then_all_ranges"
            or coverage.get("required_operation_count")
            != operation_expectations["operation_count"]
            or coverage.get("completed_operation_count")
            != coverage.get("required_operation_count")
            or coverage.get("completed_operation_count")
            != len(coverage.get("completed_operations") or [])
            or coverage.get("completed_operations_sha256")
            != canonical_sha256(coverage.get("completed_operations") or [])
            or coverage.get("completed_command_event_ids_sha256")
            != canonical_sha256(coverage.get("completed_command_event_ids") or [])
            or len(set(coverage.get("completed_command_event_ids") or []))
            != len(coverage.get("completed_command_event_ids") or [])
            or replayed_coverage != coverage
        ):
            raise GenerationError(f"Codex API response is not exact/completed for {case_id}")
        case_receipts.append(
            {
                "case_unit_id": case_id,
                "task_id": packet_by_case[case_id]["task_id"],
                "packet": packet_by_case[case_id]["packet"],
                "outputs": bindings,
                "deterministic_schema_guardrail_qc": "pass",
                "codex_provenance_qc": "pass",
                "staged_source_coverage_qc": "pass",
                "coverage_receipt_sha256": coverage["coverage_receipt_sha256"],
                "requirements_sha256": requirements["requirements_sha256"],
                "reader_operation_expectations_sha256": operation_expectations[
                    "reader_operation_expectations_sha256"
                ],
            }
        )
    return {
        "case_count": len(case_receipts),
        "case_receipts": case_receipts,
        "case_receipts_sha256": canonical_sha256(case_receipts),
        "native_batch_summary": regular_file_binding(summary_path),
        "native_batch_results": regular_file_binding(results_path),
    }


def output_snapshot(root: Path, exclusions: set[str]) -> dict[str, Any]:
    rows = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative in exclusions:
            continue
        if path.is_symlink():
            raise GenerationError(f"symlink in raw wave output: {relative}")
        if path.is_file():
            rows.append(
                {
                    "relative_path": relative,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    payload = {
        "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_post_output_snapshot/v1",
        "status": "exact_readback_pass",
        "root": str(root),
        "excluded_create_later": sorted(exclusions),
        "file_count": len(rows),
        "files": rows,
        "files_sha256": canonical_sha256(rows),
    }
    return add_self_hash(payload, "snapshot_sha256")


def _run_authorized_batch(
    *,
    prelock_path: Path,
    prelock: Mapping[str, Any],
    config: Mapping[str, Any],
    snapshot_root: Path,
    launch_approval: Mapping[str, Any],
    runtime_creation: Mapping[str, Any],
) -> int:
    auth_pre = codex_check(config)
    verify_codex_feature_surface(config)
    verify_prompt_and_native_codex_argv(config, snapshot_root)

    readonly_helper_path = verify_regular_file_binding(
        config["frozen_readonly_helper"], "frozen read-only helper"
    )
    readonly_helper = load_module(readonly_helper_path, "wave004_v6_readonly_helper")
    readonly_before_path = verify_regular_file_binding(
        prelock["readonly_before_snapshot"], "read-only before snapshot"
    )
    readonly_before = load_json(readonly_before_path, "read-only before snapshot")
    immediate = readonly_helper.readonly_operation_snapshot(
        phase="immediate_before_candidate116_wave004_v6",
        repo_root=Path(config["repository_root_absolute"]),
        work_root=Path(config["work_root_absolute"]),
    )
    if readonly_helper.compare_gate(readonly_before, immediate)["status"] != "pass":
        raise GenerationError("protected roots changed after v6 prelock")

    # Advisory check occurs before namespace claim so an expected foreign batch does
    # not burn the create-once namespace.  The authoritative fresh check is repeated
    # under the signal barrier immediately before the single batch Popen.
    advisory_foreign = foreign_drafting_processes()
    if advisory_foreign:
        raise GenerationError(
            f"foreign drafting processes exist; wave_004 was not claimed: {advisory_foreign}"
        )

    output_root = Path(config["output_root_absolute"])
    output_root.parent.mkdir(parents=True, exist_ok=True)
    os.mkdir(output_root, 0o700)
    root_stat = output_root.lstat()
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_IMODE(root_stat.st_mode) != 0o700:
        raise GenerationError("wave_004 create-once namespace type/mode is invalid")
    claim = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_namespace_claim/v1",
            "claimed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "path": str(output_root),
            "device": root_stat.st_dev,
            "inode": root_stat.st_ino,
            "uid": root_stat.st_uid,
            "gid": root_stat.st_gid,
            "mode": stat.S_IMODE(root_stat.st_mode),
            "prelock_sha256": prelock["prelock_sha256"],
            "config_sha256": config["config_sha256"],
            "launch_approval_sha256": launch_approval["approval_sha256"],
            "authorized_runtime_creation": runtime_creation,
        },
        "claim_sha256",
    )
    write_json_create_once(output_root / "_namespace_claim.json", claim)
    stdout_handle = (output_root / "_batch.stdout.log").open("x", encoding="utf-8")
    stderr_handle = (output_root / "_batch.stderr.log").open("x", encoding="utf-8")

    command = list(config["native_batch_command"])
    process: Any | None = None
    monitor: threading.Thread | None = None
    stop = threading.Event()
    state_lock = threading.Lock()
    state: dict[str, Any] = {
        "sample_count": 0,
        "drafter_peak": 0,
        "codex_peak": 0,
        "covered": set(),
        "codex_covered": set(),
        "errors": [],
    }
    launch_audit: dict[str, Any] = {
        "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_signal_popen_barrier/v1",
        "signals_blocked": [signal.Signals(item).name for item in HANDLED_SIGNALS],
        "required_batch_popen_count": 1,
    }
    prior_handlers = {item: signal.getsignal(item) for item in HANDLED_SIGNALS}
    old_mask: set[signal.Signals] | None = None
    signal_received: list[str] = []

    def handle_signal(signum: int, _frame: Any) -> None:
        name = signal.Signals(signum).name
        signal_received.append(name)
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        raise GenerationError(f"v6 launcher received {name}")

    returncode: int | None = None
    primary_error: BaseException | None = None
    try:
        if threading.current_thread() is not threading.main_thread():
            raise GenerationError("signal/Popen barrier must run on the main thread")
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, HANDLED_SIGNALS)
        launch_audit["signal_barrier_entered_monotonic_ns"] = time.monotonic_ns()
        for item in HANDLED_SIGNALS:
            signal.signal(item, handle_signal)
        process = single_popen_after_fresh_ps(
            command,
            cwd=str(snapshot_root),
            environment=config["child_environment"],
            stdout=stdout_handle,
            stderr=stderr_handle,
            audit=launch_audit,
        )
        if list(process.args) != command or os.getpgid(process.pid) != process.pid:
            raise GenerationError("batch Popen argv/session identity is not exact")
        monitor = threading.Thread(
            target=monitor_batch,
            kwargs={
                "process": process,
                "config": config,
                "prelock": prelock,
                "stop": stop,
                "state": state,
                "lock": state_lock,
            },
            name="androidworld-wave004-v6-monitor",
            daemon=False,
        )
        monitor.start()
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        old_mask = None
        launch_audit["signals_unblocked_after_monitor_start_monotonic_ns"] = time.monotonic_ns()
        returncode = process.wait()
    except BaseException as exc:
        primary_error = exc
    finally:
        stop.set()
        if old_mask is not None:
            try:
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
            except BaseException as exc:
                if primary_error is None:
                    primary_error = exc
        if monitor is not None:
            monitor.join(timeout=30)
            if monitor.is_alive() and primary_error is None:
                primary_error = GenerationError("concurrency monitor did not stop")
        if process is not None:
            try:
                clear_process_group(process)
            except BaseException as exc:
                if primary_error is None:
                    primary_error = exc
        for item, handler in prior_handlers.items():
            signal.signal(item, handler)
        stdout_handle.flush()
        stderr_handle.flush()
        os.fsync(stdout_handle.fileno())
        os.fsync(stderr_handle.fileno())
        stdout_handle.close()
        stderr_handle.close()
    if primary_error is not None:
        incident = add_self_hash(
            {
                "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_abort/v1",
                "status": "aborted_not_eligible",
                "error_type": type(primary_error).__name__,
                "error": str(primary_error),
                "launch_audit": launch_audit,
                "signal_received": signal_received,
                "batch_popen_count": launch_audit.get("batch_popen_count", 0),
                "process_group_cleared": process is None or not process_group_rows(process.pid),
            },
            "incident_sha256",
        )
        write_json_create_once(output_root / "_abort_incident.json", incident)
        raise primary_error

    with state_lock:
        errors = list(state["errors"])
    if errors:
        raise GenerationError(f"concurrency/foreign/native-argv monitor failed: {errors}")
    if returncode != 0:
        raise GenerationError(f"native batch runner returned {returncode}")
    launch_audit["status"] = "pass"
    launch_audit["signal_received"] = signal_received
    launch_audit["process_group_empty_after_wait"] = True
    launch_audit = add_self_hash(launch_audit, "barrier_sha256")
    write_json_create_once(output_root / "_signal_popen_barrier.json", launch_audit)

    samples, drafter_peak, codex_peak, covered = read_and_verify_samples(
        Path(config["concurrency_samples_absolute"]), list(prelock["case_order"])
    )
    generation_qc = verify_generated_cases(
        output_root=output_root, prelock=prelock, config=config
    )
    result_audit = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_generation_qc/v1",
            "status": "automatic_generation_qc_pass_116_of_116",
            "case_count": generation_qc["case_count"],
            "case_receipts": generation_qc["case_receipts"],
            "case_receipts_sha256": generation_qc["case_receipts_sha256"],
            "native_batch_summary": generation_qc["native_batch_summary"],
            "native_batch_results": generation_qc["native_batch_results"],
            "freeze_authorized": False,
            "remaining_gates": ["independent semantic review 116/116", "root acceptance 116/116"],
        },
        "audit_sha256",
    )
    write_json_create_once(output_root / "_automatic_generation_qc.json", result_audit)

    concurrency_audit = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_concurrency_audit/v1",
            "status": "pass",
            "sample_interval_seconds": 0.1,
            "sample_count": len(samples),
            "sample_chain_head": samples[0]["sample_sha256"],
            "sample_chain_tail": samples[-1]["sample_sha256"],
            "required_drafter_peak": PARALLELISM,
            "observed_drafter_peak": drafter_peak,
            "required_codex_exec_peak": PARALLELISM,
            "observed_codex_exec_peak": codex_peak,
            "never_exceeded_six_drafters_or_codex_execs": True,
            "all_116_cases_observed": True,
            "observed_cases": covered,
            "samples": regular_file_binding(Path(config["concurrency_samples_absolute"])),
        },
        "audit_sha256",
    )
    write_json_create_once(output_root / "_concurrency_audit.json", concurrency_audit)

    auth_post = codex_check(config, require_initial_namespace=False)
    auth_audit = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_auth_audit/v1",
            "status": "pass",
            "pre": auth_pre,
            "post": auth_post,
        },
        "audit_sha256",
    )
    write_json_create_once(output_root / "_auth_audit.json", auth_audit)

    readonly_after = readonly_helper.readonly_operation_snapshot(
        phase="after_candidate116_wave004_v6",
        repo_root=Path(config["repository_root_absolute"]),
        work_root=Path(config["work_root_absolute"]),
    )
    comparison = readonly_helper.compare_gate(readonly_before, readonly_after)
    if comparison["status"] != "pass":
        raise GenerationError("protected roots changed during wave_004")
    readonly_after["snapshot_sha256"] = canonical_sha256(readonly_after)
    write_json_create_once(output_root / "_readonly_after.json", readonly_after)
    readonly_guard = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_readonly_guard/v1",
            "status": "pass",
            "comparison": comparison,
            "before": prelock["readonly_before_snapshot"],
            "after": regular_file_binding(output_root / "_readonly_after.json")
            | {"snapshot_sha256": readonly_after["snapshot_sha256"]},
        },
        "guard_sha256",
    )
    write_json_create_once(output_root / "_readonly_guard.json", readonly_guard)

    verify_snapshot(config)
    post_foreign = foreign_drafting_processes()
    if post_foreign:
        raise GenerationError(f"foreign drafting process appeared before post receipt: {post_foreign}")
    final_stat = output_root.lstat()
    if final_stat.st_dev != claim["device"] or final_stat.st_ino != claim["inode"]:
        raise GenerationError("wave_004 claimed directory inode was replaced")
    post_runtime = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_clean4_hardened_post_runtime_snapshot/v1",
            "status": "pass",
            "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "prelock": regular_file_binding(prelock_path)
            | {"prelock_sha256": prelock["prelock_sha256"]},
            "config": prelock["draft_config"],
            "toolchain_snapshot": config["toolchain_snapshot"],
            "child_environment_sha256": config["child_environment_sha256"],
            "foreign_drafting_processes": [],
            "batch_process_group_empty": True,
            "namespace_claim": claim,
        },
        "snapshot_sha256",
    )
    write_json_create_once(output_root / "_post_runtime_snapshot.json", post_runtime)

    post_output = output_snapshot(
        output_root,
        {
            "_post_output_snapshot.json",
            "_generation_receipt.json",
            "_runtime_cleanup_receipt.json",
        },
    )
    write_json_create_once(output_root / "_post_output_snapshot.json", post_output)
    receipt = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_fresh_draft_generation_receipt/v6_clean4_hardened",
            "status": "generation_complete_unfrozen_automatic_qc_pass_116_of_116",
            "generation_id": GENERATION_ID,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "prelock_sha256": prelock["prelock_sha256"],
            "config_sha256": config["config_sha256"],
            "launch_approval": {
                "path": launch_approval["path"],
                "sha256": launch_approval["file_sha256"],
                "approval_sha256": launch_approval["approval_sha256"],
            },
            "namespace_claim": claim,
            "signal_popen_barrier": regular_file_binding(
                output_root / "_signal_popen_barrier.json"
            )
            | {"barrier_sha256": launch_audit["barrier_sha256"]},
            "concurrency_audit": regular_file_binding(
                output_root / "_concurrency_audit.json"
            )
            | {"audit_sha256": concurrency_audit["audit_sha256"]},
            "automatic_generation_qc": regular_file_binding(
                output_root / "_automatic_generation_qc.json"
            )
            | {"audit_sha256": result_audit["audit_sha256"]},
            "auth_audit": regular_file_binding(output_root / "_auth_audit.json")
            | {"audit_sha256": auth_audit["audit_sha256"]},
            "readonly_guard": regular_file_binding(output_root / "_readonly_guard.json")
            | {"guard_sha256": readonly_guard["guard_sha256"]},
            "post_runtime_snapshot": regular_file_binding(
                output_root / "_post_runtime_snapshot.json"
            )
            | {"snapshot_sha256": post_runtime["snapshot_sha256"]},
            "post_output_snapshot": regular_file_binding(
                output_root / "_post_output_snapshot.json"
            )
            | {"snapshot_sha256": post_output["snapshot_sha256"]},
            "case_count": CASE_COUNT,
            "freeze_authorized": False,
            "freeze_requires": (
                "independent semantic review and explicit root acceptance must also pass 116/116"
            ),
        },
        "receipt_sha256",
    )
    write_json_create_once(output_root / "_generation_receipt.json", receipt)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt_sha256": receipt["receipt_sha256"],
                "freeze_authorized": False,
            },
            indent=2,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    prelock_path = args.prelock.resolve(strict=True)
    prelock, config, snapshot_root = verify_context(prelock_path)
    launch_approval = verify_launch_approval(
        args.launch_approval,
        prelock=prelock,
        config=config,
    )
    # This is the first authoritative post-final-GO process probe.  No isolated
    # auth/HOME/TMP namespace exists before it.
    first_foreign = foreign_drafting_processes()
    if first_foreign:
        raise GenerationError(
            f"foreign Codex/draft process blocks authorized runtime creation: {first_foreign}"
        )
    runtime_creation = create_authorized_runtime_roots(config)
    runtime_creation = dict(runtime_creation) | {
        "fresh_ps_foreign_codex_or_draft_processes": [],
        "launch_approval_sha256": launch_approval["approval_sha256"],
    }
    result: int | None = None
    try:
        result = _run_authorized_batch(
            prelock_path=prelock_path,
            prelock=prelock,
            config=config,
            snapshot_root=snapshot_root,
            launch_approval=launch_approval,
            runtime_creation=runtime_creation,
        )
        return result
    finally:
        cleanup = destroy_authorized_runtime_roots(config)
        output_root = Path(config["output_root_absolute"])
        if output_root.is_dir() and not output_root.is_symlink():
            cleanup_receipt = add_self_hash(
                {
                    **cleanup,
                    "generation_returned_success": result == 0,
                    "launch_approval_sha256": launch_approval["approval_sha256"],
                    "generation_receipt": (
                        regular_file_binding(output_root / "_generation_receipt.json")
                        if (output_root / "_generation_receipt.json").is_file()
                        else None
                    ),
                    "abort_incident": (
                        regular_file_binding(output_root / "_abort_incident.json")
                        if (output_root / "_abort_incident.json").is_file()
                        else None
                    ),
                },
                "cleanup_receipt_sha256",
            )
            write_json_create_once(
                output_root / "_runtime_cleanup_receipt.json", cleanup_receipt
            )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Wave004V6Clean2HardenedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
