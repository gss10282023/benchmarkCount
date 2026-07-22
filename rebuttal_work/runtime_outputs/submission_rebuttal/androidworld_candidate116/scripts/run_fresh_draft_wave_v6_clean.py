#!/usr/bin/env python3
"""Fail-closed launcher for the canonical-only candidate116 wave_004 v6."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import shlex
import signal
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from wave004_v6_clean_common import (
    CASE_COUNT,
    CONFIG_SCHEMA,
    EXPECTED_CODEX_VERSION,
    EXPECTED_FREEZE_SHA256,
    EXPECTED_MODEL,
    EXPECTED_REASONING,
    EXPECTED_SANDBOX,
    GENERATION_ID,
    PARALLELISM,
    PRELOCK_SCHEMA,
    SNAPSHOT_SCHEMA,
    Wave004V6CleanError,
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


class GenerationError(Wave004V6CleanError):
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
    return parser.parse_args()


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
        or manifest.get("status") != "frozen_create_once"
        or manifest.get("file_count") != len(manifest.get("files") or [])
        or manifest.get("files_sha256") != canonical_sha256(manifest.get("files") or [])
    ):
        raise GenerationError("toolchain snapshot identity is invalid")
    root = Path(str(manifest.get("snapshot_root_absolute") or ""))
    if root != Path(str(config.get("snapshot_root_absolute") or "")):
        raise GenerationError("toolchain snapshot root differs from config")
    expected_files = list(manifest.get("files") or [])
    observed_expected = [
        row for row in expected_files if row.get("relative_path") != "snapshot_manifest.json"
    ]
    verify_exact_directory_files(root, observed_expected, label="v6 toolchain snapshot")
    adaptations = list(manifest.get("controlled_adaptations") or [])
    if {row.get("name") for row in adaptations} != {
        "checklist_guardrails",
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
        workspace = Path("/tmp/case-checklist-codex-v6-probe")
        observed = drafter.build_codex_command(
            workspace_root=workspace,
            schema_path=workspace / "output_schema.json",
            output_path=workspace / "draft_body.json",
            model=EXPECTED_MODEL,
            reasoning_effort=EXPECTED_REASONING,
            sandbox=EXPECTED_SANDBOX,
        )
    finally:
        drafter.shutil.which = old_which
    expected = [
        str(Path(config["codex_cli"]["resolved_path"])),
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        EXPECTED_SANDBOX,
        "--model",
        EXPECTED_MODEL,
        "-c",
        f'model_reasoning_effort="{EXPECTED_REASONING}"',
        "-c",
        'model_verbosity="low"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(workspace / "output_schema.json"),
        "-o",
        str(workspace / "draft_body.json"),
        "-",
    ]
    if observed != expected:
        raise GenerationError(f"frozen drafter Codex argv is not exact: {observed}")


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


def verify_context(prelock_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    prelock = load_json(prelock_path, "wave_004 v6 prelock")
    verify_self_hash(prelock, "prelock_sha256", "wave_004 v6 prelock")
    if (
        prelock.get("schema_version") != PRELOCK_SCHEMA
        or prelock.get("status") != "frozen_before_first_model_call"
        or prelock.get("generation_id") != GENERATION_ID
        or prelock.get("case_count") != CASE_COUNT
        or prelock.get("first_model_call_authorized") is not True
        or prelock.get("freeze_authorized") is not False
    ):
        raise GenerationError("wave_004 v6 prelock identity/status is invalid")

    config_path = verify_regular_file_binding(
        prelock.get("draft_config") or {}, "wave_004 v6 config"
    )
    config = load_json(config_path, "wave_004 v6 config")
    verify_self_hash(config, "config_sha256", "wave_004 v6 config")
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
    ):
        raise GenerationError("wave_004 v6 generation config is invalid")
    environment = config.get("child_environment")
    if (
        not isinstance(environment, dict)
        or set(environment) != EXPECTED_ENV_KEYS
        or config.get("child_environment_sha256") != canonical_sha256(environment)
    ):
        raise GenerationError("child environment is not the exact closed set")
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
    for name, binding in sorted((config.get("tool_bindings") or {}).items()):
        verify_regular_file_binding(binding, f"tool binding {name}")
    verify_packet_inputs(prelock, config)

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
        or incident.get("replacement_generation_id") != GENERATION_ID
    ):
        raise GenerationError("wave_003 supersession does not forbid old draft reuse")
    wave003 = Path(config["work_root_absolute"]) / "draft_generation" / "waves" / "wave_003"
    if wave003.exists() or wave003.is_symlink():
        raise GenerationError("superseded wave_003 bytes reappeared")

    policy = config.get("model_input_policy") or {}
    if policy != {
        "packet_kind": "canonical_full_case_packet",
        "packet_count": CASE_COUNT,
        "packet_wrapper_used": False,
        "historical_draft_bytes_used": False,
        "historical_qc_or_warning_text_used": False,
        "effective_prompt_components": ["frozen_base_prompt", "clean_canonical_v6"],
    }:
        raise GenerationError("canonical-only model input policy is not exact")
    verify_prompt_and_native_codex_argv(config, snapshot_root)

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


def codex_check(config: Mapping[str, Any]) -> dict[str, Any]:
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
    receipt = {
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "version": version.stdout.strip(),
        "login_status": status,
        "allowed_path_alias_warning_observed": warning,
        "closed_environment_sha256": canonical_sha256(environment),
    }
    return add_self_hash(receipt, "auth_check_sha256")


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
        and index + 1 < len(argv)
        and argv[index + 1] == "exec"
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
    return [
        token.replace('model_reasoning_effort="xhigh"', "model_reasoning_effort=xhigh")
        .replace('model_verbosity="low"', "model_verbosity=low")
        for token in argv
    ]


def validate_codex_exec_argv(argv: list[str], config: Mapping[str, Any]) -> Path:
    argv = normalized_codex_ps_argv(argv)
    if len(argv) != 25:
        raise GenerationError(f"Codex exec argv length is not exact: {argv}")
    workspace = Path(argv[3])
    expected = [
        str(config["codex_cli"]["resolved_path"]),
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        EXPECTED_SANDBOX,
        "--model",
        EXPECTED_MODEL,
        "-c",
        "model_reasoning_effort=xhigh",
        "-c",
        "model_verbosity=low",
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(workspace / "output_schema.json"),
        "-o",
        str(workspace / "draft_body.json"),
        "-",
    ]
    if (
        argv != expected
        or not workspace.name.startswith("case-checklist-codex-")
        or workspace.is_symlink()
    ):
        raise GenerationError(f"Codex exec argv is not native/exact: {argv}")
    return workspace


def validate_drafter_argv(
    argv: list[str], config: Mapping[str, Any], packet_by_path: Mapping[str, str]
) -> str:
    if len(argv) != 31:
        raise GenerationError(f"drafter argv length is not exact: {argv}")
    packet = argv[2]
    case_id = packet_by_path.get(packet)
    if case_id is None:
        raise GenerationError(f"drafter did not receive a bound canonical packet: {packet}")
    case_dir = Path(config["output_root_absolute"]) / case_id
    attempt_yaml = Path(argv[4])
    if (
        attempt_yaml.parent != case_dir
        or not attempt_yaml.name.startswith("attempt_")
        or not attempt_yaml.name.endswith(".checklist.yaml")
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
        argv[17],
        "--http-timeout-seconds",
        "180",
        "--codex-timeout-seconds",
        str(config["codex_timeout_seconds"]),
        "--codex-sandbox",
        EXPECTED_SANDBOX,
        "--prompt-supplement",
        str(config["tool_bindings"]["prompt_supplement"]["path"]),
    ]
    if argv != expected or int(argv[17]) not in config["token_budgets"]:
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


def inspect_batch_processes(
    rows: Mapping[int, Mapping[str, Any]],
    *,
    batch_pid: int,
    config: Mapping[str, Any],
    packet_by_path: Mapping[str, str],
) -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    drafter_pids: dict[int, str] = {}
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
        elif len(argv) > 1 and argv[1] == "exec" and Path(argv[0]).name.startswith("codex"):
            validate_codex_exec_argv(argv, config)
        else:
            raise GenerationError(f"unknown process in wave_004 process group: {row}")
    for pid, row in sorted(rows.items()):
        if row["pgid"] != batch_pid or not (
            len(row["argv"]) > 1 and row["argv"][1] == "exec"
        ):
            continue
        parents = [
            (drafter_pid, case_id)
            for drafter_pid, case_id in drafter_pids.items()
            if descendant_of(rows, pid, drafter_pid)
        ]
        if len(parents) != 1:
            raise GenerationError("Codex exec is not owned by exactly one active case drafter")
    if len(active) > PARALLELISM:
        raise GenerationError(f"observed more than six concurrent case attempts: {active}")
    return sorted(active, key=lambda item: item["case_unit_id"])


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
                active = inspect_batch_processes(
                    rows,
                    batch_pid=process.pid,
                    config=config,
                    packet_by_path=packet_by_path,
                )
                sample = {
                    "schema_version": "androidworld_candidate116_wave004_v6_concurrency_sample/v1",
                    "sequence": sequence,
                    "previous_sample_sha256": previous,
                    "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "monotonic_ns": time.monotonic_ns(),
                    "batch_pid": process.pid,
                    "active_case_attempt_count": len(active),
                    "active_case_attempts": active,
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
                    state["peak"] = max(state["peak"], len(active))
                    state["covered"].update(item["case_unit_id"] for item in active)
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
) -> tuple[list[dict[str, Any]], int, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise GenerationError("concurrency sample chain is empty")
    samples: list[dict[str, Any]] = []
    previous: str | None = None
    covered: set[str] = set()
    peak = 0
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
            or int(sample.get("monotonic_ns") or 0) <= prior_monotonic
        ):
            raise GenerationError(f"concurrency sample chain invariant failed at {sequence}")
        count = int(sample["active_case_attempt_count"])
        peak = max(peak, count)
        covered.update(item["case_unit_id"] for item in sample["active_case_attempts"])
        previous = sample["sample_sha256"]
        prior_monotonic = int(sample["monotonic_ns"])
        samples.append(sample)
    if peak != PARALLELISM or sorted(covered) != sorted(case_order):
        raise GenerationError(
            f"exact-six/all-116 sample gate failed: peak={peak}, covered={len(covered)}"
        )
    return samples, peak, sorted(covered)


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
    case_receipts = []
    for case_id in prelock["case_order"]:
        row = result_by_case[case_id]
        packet_path = Path(packet_by_case[case_id]["packet"]["path"])
        if (
            row.get("status") != "success"
            or Path(str(row.get("case_packet") or "")).resolve() != packet_path
            or row.get("quality_warnings") != []
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
        bindings = {}
        for name in required:
            path = case_dir / name
            bindings[name] = regular_file_binding(path)
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
        if (
            api.get("provider") != "codex_cli"
            or api.get("model") != EXPECTED_MODEL
            or api.get("status") != "completed"
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
        "schema_version": "androidworld_candidate116_wave004_v6_post_output_snapshot/v1",
        "status": "exact_readback_pass",
        "root": str(root),
        "excluded_create_later": sorted(exclusions),
        "file_count": len(rows),
        "files": rows,
        "files_sha256": canonical_sha256(rows),
    }
    return add_self_hash(payload, "snapshot_sha256")


def main() -> int:
    args = parse_args()
    prelock_path = args.prelock.resolve(strict=True)
    prelock, config, snapshot_root = verify_context(prelock_path)
    auth_pre = codex_check(config)

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
            "schema_version": "androidworld_candidate116_wave004_v6_namespace_claim/v1",
            "claimed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "path": str(output_root),
            "device": root_stat.st_dev,
            "inode": root_stat.st_ino,
            "uid": root_stat.st_uid,
            "gid": root_stat.st_gid,
            "mode": stat.S_IMODE(root_stat.st_mode),
            "prelock_sha256": prelock["prelock_sha256"],
            "config_sha256": config["config_sha256"],
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
    state: dict[str, Any] = {"sample_count": 0, "peak": 0, "covered": set(), "errors": []}
    launch_audit: dict[str, Any] = {
        "schema_version": "androidworld_candidate116_wave004_v6_signal_popen_barrier/v1",
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
                "schema_version": "androidworld_candidate116_wave004_v6_abort/v1",
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

    samples, peak, covered = read_and_verify_samples(
        Path(config["concurrency_samples_absolute"]), list(prelock["case_order"])
    )
    generation_qc = verify_generated_cases(
        output_root=output_root, prelock=prelock, config=config
    )
    result_audit = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_generation_qc/v1",
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
            "schema_version": "androidworld_candidate116_wave004_v6_concurrency_audit/v1",
            "status": "pass",
            "sample_interval_seconds": 0.1,
            "sample_count": len(samples),
            "sample_chain_head": samples[0]["sample_sha256"],
            "sample_chain_tail": samples[-1]["sample_sha256"],
            "required_peak": PARALLELISM,
            "observed_peak": peak,
            "never_exceeded_six": True,
            "all_116_cases_observed": True,
            "observed_cases": covered,
            "samples": regular_file_binding(Path(config["concurrency_samples_absolute"])),
        },
        "audit_sha256",
    )
    write_json_create_once(output_root / "_concurrency_audit.json", concurrency_audit)

    auth_post = codex_check(config)
    auth_audit = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_auth_audit/v1",
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
            "schema_version": "androidworld_candidate116_wave004_v6_readonly_guard/v1",
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
            "schema_version": "androidworld_candidate116_wave004_v6_post_runtime_snapshot/v1",
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
        {"_post_output_snapshot.json", "_generation_receipt.json"},
    )
    write_json_create_once(output_root / "_post_output_snapshot.json", post_output)
    receipt = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_fresh_draft_generation_receipt/v6",
            "status": "generation_complete_unfrozen_automatic_qc_pass_116_of_116",
            "generation_id": GENERATION_ID,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "prelock_sha256": prelock["prelock_sha256"],
            "config_sha256": config["config_sha256"],
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


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Wave004V6CleanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)

