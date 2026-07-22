#!/usr/bin/env python3
"""Launch exactly six isolated Codex reviewers for semantic review v7."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Mapping

import semantic_review_v7_staging as review_staging
import wave004_v6_clean2_hardened_staging as source_staging
from semantic_review_v7_common import (
    CASE_COUNT,
    CODEX_BINARY_SHA256,
    CODEX_LOGIN_STATUS,
    CODEX_VERSION,
    CONFIG_SCHEMA,
    MODEL,
    PARALLELISM,
    PRELOCK_SCHEMA,
    REASONING_EFFORT,
    RECEIPT_SCHEMA,
    SemanticReviewV7Error,
    add_self_hash,
    canonical_sha256,
    checklist_semantic_inventory,
    covered_line_spans_from_requirements,
    ensure_no_sensitive_hash_fields,
    is_exact_int,
    load_json,
    load_yaml,
    parse_jsonl,
    regular_file_binding,
    sha256_file,
    sha256_text,
    validate_review_body,
    verify_actual_frozen_draft_capacity_row,
    verify_exact_tree,
    verify_regular_file_binding,
    verify_self_hash,
    write_json_create_once,
)

sys.dont_write_bytecode = True


LAUNCH_APPROVAL_SCHEMA = (
    "androidworld_candidate116_semantic_review_v7_launch_approval/v1"
)
ALLOWED_LOGIN_WARNING = (
    "WARNING: proceeding, even though we could not create PATH aliases: "
    "Operation not permitted (os error 1)"
)


class ReviewLaunchError(SemanticReviewV7Error):
    """Raised when the authorized semantic-review batch cannot be proven exact."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path, required=True)
    parser.add_argument("--launch-approval", type=Path, required=True)
    return parser.parse_args()


def verify_snapshot(config: Mapping[str, Any]) -> tuple[dict[str, Any], Path]:
    root = Path(str(config.get("snapshot_root") or ""))
    manifest_path = verify_regular_file_binding(
        config.get("snapshot_manifest") or {}, "review toolchain snapshot manifest"
    )
    if manifest_path != root / "snapshot_manifest.json":
        raise ReviewLaunchError("snapshot manifest path differs from snapshot root")
    manifest = load_json(manifest_path, "review toolchain snapshot manifest")
    verify_self_hash(manifest, "snapshot_sha256", "review toolchain snapshot manifest")
    if (
        manifest.get("schema_version")
        != "androidworld_candidate116_semantic_review_v7_toolchain_snapshot/v1"
        or manifest.get("status") != "create_once_byte_frozen"
        or manifest.get("snapshot_root") != str(root)
        or manifest.get("snapshot_sha256") != config.get("snapshot_sha256")
        or not is_exact_int(
            manifest.get("file_count"), expected=len(manifest.get("files") or [])
        )
        or manifest.get("files_sha256") != canonical_sha256(manifest.get("files") or [])
    ):
        raise ReviewLaunchError("review toolchain snapshot identity is invalid")
    observed_relatives: set[str] = set()
    for row in manifest.get("files") or []:
        relative = row.get("relative_path")
        if not isinstance(relative, str) or relative in observed_relatives:
            raise ReviewLaunchError(
                "snapshot relative file list is malformed/duplicated"
            )
        observed_relatives.add(relative)
        path = root / relative
        observed = regular_file_binding(path)
        for field in (
            "path",
            "repository_relative_path",
            "sha256",
            "size_bytes",
            "mode",
        ):
            if observed[field] != row.get(field):
                raise ReviewLaunchError(f"snapshot file changed: {relative}/{field}")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "snapshot_manifest.json"
    }
    if actual != observed_relatives:
        raise ReviewLaunchError("snapshot exact file namespace changed")
    expected_launcher = root / "scripts" / "run_semantic_review_v7_batch.py"
    if Path(__file__).resolve(strict=True) != expected_launcher:
        raise ReviewLaunchError(
            "production launcher must execute from the frozen snapshot"
        )
    return manifest, root


def verify_launch_approval(
    path: Path, *, prelock: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    if (
        path.is_symlink()
        or not path.is_file()
        or stat.S_IMODE(path.stat().st_mode) != 0o444
    ):
        raise ReviewLaunchError("launch approval must be a sealed 0444 regular file")
    approval = load_json(path.resolve(strict=True), "semantic review launch approval")
    verify_self_hash(approval, "approval_sha256", "semantic review launch approval")
    if (
        approval.get("schema_version") != LAUNCH_APPROVAL_SCHEMA
        or approval.get("status") != "approved_after_independent_prelock_audit"
        or approval.get("review_id") != prelock.get("review_id")
        or approval.get("prelock_sha256") != prelock.get("prelock_sha256")
        or approval.get("config_sha256") != config.get("config_sha256")
        or approval.get("snapshot_sha256") != config.get("snapshot_sha256")
        or approval.get("capacity_sha256") != config.get("capacity_sha256")
        or approval.get("independent_root_audit") is not True
        or approval.get("authorize_model_calls") is not True
        or not is_exact_int(
            approval.get("model_call_count_before_approval"), expected=0
        )
        or approval.get("freeze_authorized") is not False
    ):
        raise ReviewLaunchError("launch approval identity/content bindings are invalid")
    return approval


def verify_context(
    prelock_path: Path, approval_path: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    if (
        prelock_path.is_symlink()
        or not prelock_path.is_file()
        or stat.S_IMODE(prelock_path.stat().st_mode) != 0o444
    ):
        raise ReviewLaunchError("semantic review prelock must be a sealed 0444 file")
    prelock = load_json(prelock_path.resolve(strict=True), "semantic review v7 prelock")
    verify_self_hash(prelock, "prelock_sha256", "semantic review v7 prelock")
    if (
        prelock.get("schema_version") != PRELOCK_SCHEMA
        or prelock.get("status") != "prelocked_waiting_independent_launch_approval"
        or not is_exact_int(prelock.get("case_count"), expected=CASE_COUNT)
        or len(prelock.get("case_order") or []) != CASE_COUNT
        or len(set(prelock.get("case_order") or [])) != CASE_COUNT
        or prelock.get("case_order_sha256")
        != canonical_sha256(prelock.get("case_order") or [])
        or len(prelock.get("case_inputs") or []) != CASE_COUNT
        or prelock.get("case_inputs_sha256")
        != canonical_sha256(prelock.get("case_inputs") or [])
        or not is_exact_int(prelock.get("model_call_count"), expected=0)
        or prelock.get("freeze_authorized") is not False
    ):
        raise ReviewLaunchError("semantic review prelock identity/order is invalid")
    config_path = verify_regular_file_binding(
        prelock.get("review_config") or {}, "semantic review config"
    )
    config = load_json(config_path, "semantic review config")
    verify_self_hash(config, "config_sha256", "semantic review config")
    if (
        config.get("schema_version") != CONFIG_SCHEMA
        or config.get("status") != "prelocked_no_model_calls"
        or config.get("review_id") != prelock.get("review_id")
        or config.get("config_sha256") != prelock.get("review_config_sha256")
        or config.get("provider") != "codex_cli"
        or config.get("auth_mode") != "codex_login"
        or config.get("model") != MODEL
        or config.get("model_version") != MODEL
        or config.get("reasoning_effort") != REASONING_EFFORT
        or not is_exact_int(config.get("max_parallel"), expected=PARALLELISM)
        or not is_exact_int(config.get("required_peak_parallel"), expected=PARALLELISM)
        or not is_exact_int(config.get("case_count"), expected=CASE_COUNT)
        or not is_exact_int(
            config.get("external_codex_exec_required_at_launch"), expected=0
        )
        or config.get("freeze_authorized") is not False
        or config.get("disabled_codex_features")
        != list(review_staging.DISABLED_CODEX_FEATURES)
    ):
        raise ReviewLaunchError(
            "semantic review config is not exact Codex/xhigh/peak-six"
        )
    codex = config.get("codex_cli") or {}
    codex_path = Path(str(codex.get("resolved_path") or ""))
    if (
        codex_path.is_symlink()
        or not codex_path.is_file()
        or sha256_file(codex_path) != CODEX_BINARY_SHA256
        or codex.get("sha256") != CODEX_BINARY_SHA256
        or codex.get("version") != CODEX_VERSION
        or codex.get("login_status_at_prelock") != CODEX_LOGIN_STATUS
        or codex.get("auth_content_or_hash_persisted") is not False
    ):
        raise ReviewLaunchError("Codex CLI binary/login binding changed")
    python_path = verify_regular_file_binding(
        config.get("python_runtime") or {}, "semantic review Python runtime"
    )
    if python_path != Path(sys.executable).resolve(strict=True):
        raise ReviewLaunchError("launcher Python runtime differs from prelock")
    exec_contract = config.get("codex_exec_contract") or {}
    if (
        exec_contract.get("global_prefix") != ["-a", "never", "--strict-config", "exec"]
        or exec_contract.get("working_directory_flag") != "--cd"
        or exec_contract.get("ephemeral") is not True
        or exec_contract.get("ignore_user_config") is not True
        or exec_contract.get("ignore_rules") is not True
        or exec_contract.get("approval_policy") != "never"
        or exec_contract.get("model") != MODEL
        or exec_contract.get("reasoning_effort") != REASONING_EFFORT
        or exec_contract.get("model_verbosity") != "low"
        or exec_contract.get("web_search") != "disabled"
        or exec_contract.get("mcp_servers") != {}
        or exec_contract.get("shell_environment_inherit") != "none"
        or exec_contract.get("permission_profile") != review_staging.PROFILE_NAME
        or exec_contract.get("permission_workspace_access") != "read"
        or exec_contract.get("permission_network_enabled") is not False
        or exec_contract.get("disabled_features")
        != list(review_staging.DISABLED_CODEX_FEATURES)
        or set(exec_contract.get("forbidden_flags") or [])
        != {
            "--sandbox",
            "-s",
            "--add-dir",
            "--search",
            "--dangerously-bypass-approvals-and-sandbox",
        }
        or exec_contract.get("json_events") is not True
        or exec_contract.get("structured_output") is not True
        or exec_contract.get("prompt_transport") != "stdin"
        or exec_contract.get("output_filename") != "review_body.json"
    ):
        raise ReviewLaunchError("Codex exec contract differs from strict review policy")
    snapshot, snapshot_root = verify_snapshot(config)
    capacity_path = verify_regular_file_binding(
        prelock.get("review_capacity") or {}, "semantic review capacity"
    )
    capacity = load_json(capacity_path, "semantic review capacity")
    verify_self_hash(capacity, "capacity_sha256", "semantic review capacity")
    if (
        capacity.get("schema_version")
        != "androidworld_candidate116_semantic_review_v7_capacity/v1"
        or capacity.get("status")
        != "all_116_fit_frozen_o200k_context_with_output_reserve"
        or capacity.get("capacity_sha256") != config.get("capacity_sha256")
        or capacity.get("capacity_sha256") != prelock.get("review_capacity_sha256")
        or not is_exact_int(capacity.get("case_count"), expected=CASE_COUNT)
        or capacity.get("case_order") != prelock.get("case_order")
        or len(capacity.get("cases") or []) != CASE_COUNT
        or capacity.get("cases_sha256") != canonical_sha256(capacity.get("cases") or [])
        or not is_exact_int(
            capacity.get("actual_frozen_draft_case_count"), expected=CASE_COUNT
        )
        or not is_exact_int(
            capacity.get("actual_frozen_draft_capacity_pass_count"),
            expected=CASE_COUNT,
        )
        or capacity.get("all_actual_frozen_drafts_pass_both_exact_gates") is not True
    ):
        raise ReviewLaunchError("semantic review capacity binding/order is invalid")
    verify_exact_tree(prelock.get("raw_draft_tree") or {}, "raw draft tree")
    verify_exact_tree(config.get("tokenizer_root") or {}, "frozen tokenizer root")
    verify_regular_file_binding(
        config.get("tokenizer_cache") or {}, "frozen tokenizer cache"
    )
    for label in (
        "packet_index",
        "draft_generation_prelock",
        "draft_generation_receipt",
        "draft_qc_report",
        "adapted_checklist_schema",
        "review_toolchain_snapshot",
    ):
        verify_regular_file_binding(prelock.get(label) or {}, label.replace("_", " "))
    case_inputs = list(prelock.get("case_inputs") or [])
    capacity_rows = list(capacity.get("cases") or [])
    for rank, (case_id, row, capacity_row) in enumerate(
        zip(prelock["case_order"], case_inputs, capacity_rows, strict=True)
    ):
        verify_self_hash(row, "case_input_sha256", f"{case_id} review input")
        verify_actual_frozen_draft_capacity_row(
            capacity_row,
            label=f"{case_id} actual frozen draft capacity",
            max_staged_input_tokens=review_staging.MAX_STAGED_INPUT_TOKENS,
            max_output_reserve_tokens=review_staging.MAX_OUTPUT_RESERVE_TOKENS,
            effective_context_limit=review_staging.EFFECTIVE_CONTEXT_LIMIT,
            max_checklist_reader_tokens=review_staging.MAX_CHECKLIST_READER_TOKENS,
            max_checklist_reader_bytes=review_staging.MAX_CHECKLIST_READER_BYTES,
            protocol_reserve_tokens=8_000,
        )
        if (
            not is_exact_int(row.get("selection_rank"), expected=rank)
            or row.get("case_unit_id") != case_id
            or row.get("task_id") != case_id
            or capacity_row.get("case_unit_id") != case_id
            or capacity_row.get("actual_frozen_draft")
            != row.get("checklist_yaml")
        ):
            raise ReviewLaunchError(f"{case_id} review input identity/order differs")
        verify_regular_file_binding(row.get("packet") or {}, f"{case_id} packet")
        yaml_path = verify_regular_file_binding(
            row.get("checklist_yaml") or {}, f"{case_id} checklist YAML"
        )
        json_path = verify_regular_file_binding(
            row.get("checklist_json") or {}, f"{case_id} checklist JSON"
        )
        if load_yaml(yaml_path, f"{case_id} checklist YAML") != load_json(
            json_path, f"{case_id} checklist JSON"
        ):
            raise ReviewLaunchError(f"{case_id} checklist YAML/JSON drifted")
    output_root = Path(str(config.get("output_root") or ""))
    if output_root.is_symlink() or output_root.exists():
        raise ReviewLaunchError("semantic review output namespace is not fresh")
    approval = verify_launch_approval(
        approval_path.resolve(strict=True), prelock=prelock, config=config
    )
    ensure_no_sensitive_hash_fields(prelock)
    ensure_no_sensitive_hash_fields(config)
    ensure_no_sensitive_hash_fields(approval)
    return prelock, config, capacity, approval, snapshot_root


def ps_codex_exec_rows() -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["/bin/ps", "-ww", "-axo", "pid=,ppid=,command="],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        raise ReviewLaunchError(f"fresh /bin/ps failed: {completed.stderr.strip()}")
    rows: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        try:
            pid, ppid = int(parts[0]), int(parts[1])
            argv = shlex.split(parts[2])
        except (ValueError, TypeError):
            continue
        if argv and Path(argv[0]).name.startswith("codex") and "exec" in argv[1:]:
            rows.append({"pid": pid, "ppid": ppid, "argv": argv})
    return rows


def verify_login(codex: Path, environment: Mapping[str, str]) -> None:
    completed = subprocess.run(
        [str(codex), "login", "status"],
        env=dict(environment),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    detail = "\n".join(
        part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
    )
    accepted_details = {
        CODEX_LOGIN_STATUS,
        CODEX_LOGIN_STATUS + "\n" + ALLOWED_LOGIN_WARNING,
        ALLOWED_LOGIN_WARNING + "\n" + CODEX_LOGIN_STATUS,
    }
    if completed.returncode != 0 or detail not in accepted_details:
        raise ReviewLaunchError(f"isolated Codex login state is not exact: {detail!r}")


def create_runtime_roots(config: Mapping[str, Any]) -> tuple[dict[str, Path], bytes]:
    paths = {
        key: Path(str(value))
        for key, value in (config.get("isolated_runtime_roots") or {}).items()
    }
    if set(paths) != {"auth_home", "isolated_home", "review_tmp_root"}:
        raise ReviewLaunchError("isolated runtime root set is not exact")
    if len(set(paths.values())) != 3 or any(
        path.exists() or path.is_symlink() for path in paths.values()
    ):
        raise ReviewLaunchError("isolated runtime roots are not absent/distinct")
    original_auth = Path(str(config.get("original_codex_home") or "")) / "auth.json"
    if original_auth.is_symlink() or not original_auth.is_file():
        raise ReviewLaunchError("original auth.json is missing/symlinked")
    auth_bytes = original_auth.read_bytes()
    created: list[Path] = []
    try:
        for path in paths.values():
            os.mkdir(path, 0o700)
            created.append(path)
        isolated_auth = paths["auth_home"] / "auth.json"
        descriptor = os.open(isolated_auth, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(auth_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(isolated_auth, 0o600)
        if sorted(path.name for path in paths["auth_home"].iterdir()) != ["auth.json"]:
            raise ReviewLaunchError(
                "isolated CODEX_HOME namespace is not exactly auth.json"
            )
    except BaseException:
        for path in reversed(created):
            shutil.rmtree(path, ignore_errors=True)
        raise
    return paths, auth_bytes


def destroy_runtime_roots(paths: Mapping[str, Path]) -> dict[str, Any]:
    for path in paths.values():
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
    absent = {
        key: not path.exists() and not path.is_symlink() for key, path in paths.items()
    }
    if not all(absent.values()):
        raise ReviewLaunchError("isolated auth/HOME/TMP terminal cleanup is incomplete")
    return {
        "status": "pass_all_isolated_runtime_roots_absent",
        "paths": {key: str(path) for key, path in paths.items()},
        "all_paths_absent": True,
        "auth_content_or_hash_persisted": False,
    }


def _write_text_create_once(path: Path, value: str, mode: int = 0o444) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, mode)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


class BatchState:
    def __init__(self, output_root: Path) -> None:
        self.lock = threading.RLock()
        self.abort = threading.Event()
        self.monitor_stop = threading.Event()
        self.active: dict[int, dict[str, Any]] = {}
        self.peak_registered = 0
        self.peak_live = 0
        self.covered: set[str] = set()
        self.errors: list[str] = []
        self.results: dict[str, dict[str, Any]] = {}
        self.samples_path = output_root / "_concurrency_samples.jsonl"

    def fail(self, message: str) -> None:
        with self.lock:
            if message not in self.errors:
                self.errors.append(message)
            self.abort.set()
            for row in self.active.values():
                process = row.get("process")
                if process is not None and process.poll() is None:
                    process.terminate()


def monitor_codex_processes(state: BatchState) -> None:
    sequence = 0
    previous: str | None = None
    try:
        with state.samples_path.open("x", encoding="utf-8", buffering=1) as handle:
            while not state.monitor_stop.wait(0.1):
                with state.lock:
                    rows = ps_codex_exec_rows()
                    allowed = set(state.active)
                    observed = {row["pid"] for row in rows}
                    foreign = sorted(observed - allowed)
                    if foreign:
                        raise ReviewLaunchError(
                            f"foreign Codex exec appeared during review: {foreign}"
                        )
                    live = len(observed & allowed)
                    if live > PARALLELISM or len(allowed) > PARALLELISM:
                        raise ReviewLaunchError(
                            "review exceeded six concurrent Codex exec processes"
                        )
                    state.peak_live = max(state.peak_live, live)
                    sample = add_self_hash(
                        {
                            "schema_version": "androidworld_candidate116_semantic_review_v7_concurrency_sample/v1",
                            "sequence": sequence,
                            "previous_sample_sha256": previous,
                            "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                            "active_registered_count": len(allowed),
                            "active_live_codex_exec_count": live,
                            "active_case_ids": sorted(
                                row["case_unit_id"] for row in state.active.values()
                            ),
                            "foreign_codex_exec_pids": [],
                        },
                        "sample_sha256",
                    )
                    handle.write(
                        json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n"
                    )
                    handle.flush()
                    previous = sample["sample_sha256"]
                    sequence += 1
    except BaseException as exc:
        state.fail(f"monitor: {type(exc).__name__}: {exc}")


def run_one_case(
    *,
    rank: int,
    case_id: str,
    input_row: Mapping[str, Any],
    capacity_row: Mapping[str, Any],
    prelock: Mapping[str, Any],
    config: Mapping[str, Any],
    snapshot_root: Path,
    output_root: Path,
    token_counter: Any,
    tokenizer_binding: Mapping[str, Any],
    output_schema: Mapping[str, Any],
    base_prompt: str,
    first_wave_barrier: threading.Barrier,
    state: BatchState,
) -> dict[str, Any]:
    if rank < PARALLELISM:
        first_wave_barrier.wait(timeout=60)
    if state.abort.is_set():
        raise ReviewLaunchError("batch aborted before case launch")
    packet_path = verify_regular_file_binding(input_row["packet"], f"{case_id} packet")
    checklist_path = verify_regular_file_binding(
        input_row["checklist_yaml"], f"{case_id} checklist"
    )
    checklist = load_yaml(checklist_path, f"{case_id} checklist")
    packet_text = packet_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")
    tmp_root = Path(config["isolated_runtime_roots"]["review_tmp_root"])
    workspace = tmp_root / f"semantic-review-v7-{rank:03d}-{case_id}"
    os.mkdir(workspace, 0o700)
    case_dir = output_root / case_id
    os.mkdir(case_dir, 0o700)
    process: subprocess.Popen[bytes] | None = None
    try:
        manifest = review_staging.materialize_review_workspace(
            workspace_root=workspace,
            case_packet_text=packet_text,
            checklist_text=checklist_text,
            checklist=checklist,
            output_schema=output_schema,
            token_counter=token_counter,
            tokenizer_binding=tokenizer_binding,
        )
        if (
            manifest["coverage_requirements"] != capacity_row.get("requirements")
            or manifest["packet_reader_operation_expectations"]
            != capacity_row.get("packet_reader_operation_expectations")
            or manifest["semantic_inventory"] != capacity_row.get("semantic_inventory")
            or manifest["review_operation_expectations"]
            != capacity_row.get("review_operation_expectations")
        ):
            raise ReviewLaunchError(
                f"{case_id} staged A/B/inventory differs from prelock capacity"
            )
        prompt = review_staging.staged_review_prompt(
            base_prompt=base_prompt, manifest=manifest
        )
        if sha256_text(prompt) != capacity_row.get("prompt_sha256"):
            raise ReviewLaunchError(f"{case_id} staged prompt differs from prelock")
        argv = review_staging.build_codex_exec_argv(
            codex_executable=Path(config["codex_cli"]["resolved_path"]),
            workspace_root=workspace,
            model=MODEL,
            reasoning_effort=REASONING_EFFORT,
            repository_root=Path(config["repository_root"]),
            review_tmp_root=tmp_root,
            auth_home=Path(config["isolated_runtime_roots"]["auth_home"]),
            original_codex_home=Path(config["original_codex_home"]),
            isolated_home=Path(config["isolated_runtime_roots"]["isolated_home"]),
            real_home=Path(config["real_home"]),
        )
        with state.lock:
            if state.abort.is_set():
                raise ReviewLaunchError("batch aborted at case Popen barrier")
            # The monitor uses the same lock, so no spawned PID can appear before registration.
            process = subprocess.Popen(
                argv,
                cwd=str(workspace),
                env=dict(config["child_environment"]),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=False,
            )
            state.active[process.pid] = {
                "case_unit_id": case_id,
                "process": process,
                "argv_sha256": canonical_sha256(argv),
            }
            state.covered.add(case_id)
            state.peak_registered = max(state.peak_registered, len(state.active))
        try:
            stdout_bytes, stderr_bytes = process.communicate(
                input=prompt.encode("utf-8"), timeout=int(config["timeout_seconds"])
            )
        except subprocess.TimeoutExpired as exc:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            raise ReviewLaunchError(f"{case_id} Codex review timed out") from exc
        finally:
            with state.lock:
                if process is not None:
                    state.active.pop(process.pid, None)
        stdout_text = stdout_bytes.decode("utf-8", errors="strict")
        stderr_text = stderr_bytes.decode("utf-8", errors="strict")
        normalized_stderr = stderr_text.strip()
        if normalized_stderr not in {"", ALLOWED_LOGIN_WARNING}:
            raise ReviewLaunchError(f"{case_id} Codex stderr is not empty/allowlisted")
        if process.returncode != 0:
            raise ReviewLaunchError(f"{case_id} Codex exited {process.returncode}")
        events_path = case_dir / "codex_events.jsonl"
        stderr_path = case_dir / "codex_stderr.log"
        _write_text_create_once(events_path, stdout_text)
        _write_text_create_once(stderr_path, stderr_text)
        events = parse_jsonl(events_path)
        review_staging.verify_review_workspace(workspace, manifest, require_output=True)
        body = load_json(workspace / "review_body.json", f"{case_id} review body")
        coverage = review_staging.combined_coverage_receipt_from_events(
            events=events,
            requirements=manifest["coverage_requirements"],
            packet_operation_expectations=manifest[
                "packet_reader_operation_expectations"
            ],
            review_operation_expectations=manifest["review_operation_expectations"],
            checklist_text=checklist_text,
            inventory=manifest["semantic_inventory"],
            expected_final_body=body,
            token_counter=token_counter,
        )
        if (
            (coverage.get("codex_0144_event_framing") or {}).get(
                "terminal_agent_message_body_sha256"
            )
            != canonical_sha256(body)
        ):
            raise ReviewLaunchError(
                f"{case_id} final agent JSON differs from review_body.json"
            )
        body_qc = validate_review_body(
            body,
            schema=output_schema,
            checklist=checklist,
            inventory=manifest["semantic_inventory"],
            raw_sources=manifest["raw_sources"],
            require_accept=False,
            covered_line_spans=covered_line_spans_from_requirements(
                manifest["coverage_requirements"]
            ),
        )
        review = add_self_hash(
            {
                "schema_version": "androidworld_candidate116_semantic_review_v7_case_result/v1",
                "status": "structurally_valid_independent_semantic_review",
                "selection_rank": rank,
                "case_unit_id": case_id,
                "task_id": case_id,
                "verdict": body["verdict"],
                "review_body": body,
                "review_body_qc": body_qc,
                "packet": dict(input_row["packet"]),
                "checklist_yaml": dict(input_row["checklist_yaml"]),
                "checklist_json": dict(input_row["checklist_json"]),
                "semantic_inventory_sha256": manifest["inventory_sha256"],
                "coverage_requirements_sha256": manifest["coverage_requirements"][
                    "requirements_sha256"
                ],
                "packet_reader_operation_expectations_sha256": manifest[
                    "packet_reader_operation_expectations_sha256"
                ],
                "review_operation_expectations_sha256": manifest[
                    "review_operation_expectations_sha256"
                ],
                "combined_coverage_receipt": coverage,
                "codex_provenance": {
                    "provider": "codex_cli",
                    "auth_mode": "codex_login",
                    "model": MODEL,
                    "model_version": MODEL,
                    "reasoning_effort": REASONING_EFFORT,
                    "model_verbosity": "low",
                    "fresh_context": True,
                    "ephemeral": True,
                    "permission_profile": review_staging.PROFILE_NAME,
                    "permission_workspace_access": "read",
                    "permission_network_enabled": False,
                    "argv": argv,
                    "argv_sha256": canonical_sha256(argv),
                    "prompt_sha256": sha256_text(prompt),
                    "prelock_sha256": prelock["prelock_sha256"],
                    "config_sha256": config["config_sha256"],
                    "snapshot_sha256": config["snapshot_sha256"],
                    "capacity_sha256": config["capacity_sha256"],
                },
                "codex_events": regular_file_binding(events_path),
                "codex_stderr": regular_file_binding(stderr_path),
                "warning_count": 0,
                "error_count": 0,
                "reviewer_modified_checklist": False,
                "human_review_claimed": False,
                "freeze_authorized": False,
            },
            "review_sha256",
        )
        review_path = case_dir / "review.json"
        write_json_create_once(review_path, review)
        return {
            "selection_rank": rank,
            "case_unit_id": case_id,
            "task_id": case_id,
            "verdict": body["verdict"],
            "review": regular_file_binding(review_path),
            "review_sha256": review["review_sha256"],
            "coverage_receipt_sha256": coverage["coverage_receipt_sha256"],
            "warning_count": 0,
            "error_count": 0,
        }
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if workspace.exists() and not workspace.is_symlink():
            review_staging.unseal_for_cleanup(workspace)
            shutil.rmtree(workspace)


def revalidate_all_actual_frozen_draft_capacity(
    *,
    prelock: Mapping[str, Any],
    capacity: Mapping[str, Any],
    token_counter: Any,
    base_prompt: str,
) -> None:
    input_by_case = {
        row["case_unit_id"]: row for row in prelock.get("case_inputs") or []
    }
    capacity_by_case = {
        row["case_unit_id"]: row for row in capacity.get("cases") or []
    }
    for case_id in prelock["case_order"]:
        input_row = input_by_case[case_id]
        row = capacity_by_case[case_id]
        checklist_path = verify_regular_file_binding(
            input_row["checklist_yaml"], f"{case_id} actual frozen draft"
        )
        checklist_text = checklist_path.read_text(encoding="utf-8")
        checklist = load_yaml(checklist_path, f"{case_id} actual frozen draft")
        inventory = checklist_semantic_inventory(checklist)
        requirements = row["requirements"]
        packet_expectations = row["packet_reader_operation_expectations"]
        review_expectations = row["review_operation_expectations"]
        exact_checklist_output = review_staging.render_checklist_output_for_audit(
            checklist_text=checklist_text,
            inventory=inventory,
            requirements_sha256=requirements["requirements_sha256"],
        )
        manifest_stub = {
            "case_unit_id": case_id,
            "task_id": case_id,
            "checklist_sha256": sha256_text(checklist_text),
            "inventory_sha256": inventory["inventory_sha256"],
            "coverage_requirements": requirements,
            "packet_reader_operation_expectations": packet_expectations,
            "packet_reader_operation_expectations_sha256": review_staging._packet_expectations_hash(
                packet_expectations
            ),
            "review_operation_expectations_sha256": review_expectations[
                "review_operation_expectations_sha256"
            ],
        }
        prompt = review_staging.staged_review_prompt(
            base_prompt=base_prompt, manifest=manifest_stub
        )
        operations = list(packet_expectations.get("operations") or [])
        packet_tokens = sum(
            operation["expected_full_output_o200k_tokens"]
            for operation in operations
        )
        checklist_tokens = token_counter(exact_checklist_output)
        if (
            inventory != row.get("semantic_inventory")
            or token_counter(checklist_text)
            != row.get("actual_frozen_draft_o200k_tokens")
            or sha256_text(exact_checklist_output)
            != row.get("actual_frozen_draft_reader_output_sha256")
            or len(exact_checklist_output.encode("utf-8"))
            != row.get("checklist_reader_output_size_bytes")
            or checklist_tokens != row.get("checklist_reader_output_o200k_tokens")
            or token_counter(prompt) != row.get("prompt_o200k_tokens")
            or sha256_text(prompt) != row.get("prompt_sha256")
            or packet_tokens != row.get("packet_reader_output_o200k_tokens")
        ):
            raise ReviewLaunchError(
                f"{case_id} actual frozen draft exact token-capacity recomputation differs"
            )


def run_batch(
    *,
    prelock: Mapping[str, Any],
    config: Mapping[str, Any],
    capacity: Mapping[str, Any],
    approval: Mapping[str, Any],
    snapshot_root: Path,
) -> dict[str, Any]:
    token_counter, tokenizer_binding = source_staging.load_frozen_o200k_token_counter(
        tokenizer_root=Path(config["tokenizer_root"]["root"]),
        merge_table_path=Path(config["tokenizer_cache"]["path"]),
    )
    if tokenizer_binding != capacity.get("tokenizer_binding"):
        raise ReviewLaunchError("frozen tokenizer binding differs from capacity")
    output_schema = load_json(
        snapshot_root
        / "schemas"
        / "androidworld_candidate116_semantic_review_v7.schema.json",
        "frozen semantic review schema",
    )
    base_prompt = (
        snapshot_root
        / "prompts"
        / "androidworld_candidate116_semantic_review_v7.prompt.md"
    ).read_text(encoding="utf-8")
    revalidate_all_actual_frozen_draft_capacity(
        prelock=prelock,
        capacity=capacity,
        token_counter=token_counter,
        base_prompt=base_prompt,
    )
    if ps_codex_exec_rows():
        raise ReviewLaunchError(
            "external Codex exec process count is not zero at launch"
        )
    runtime_paths, original_auth_bytes = create_runtime_roots(config)
    output_root = Path(config["output_root"])
    if ps_codex_exec_rows():
        destroy_runtime_roots(runtime_paths)
        raise ReviewLaunchError(
            "external Codex exec appeared after isolated auth creation"
        )
    output_root.parent.mkdir(parents=True, exist_ok=True)
    os.mkdir(output_root, 0o700)
    write_json_create_once(
        output_root / "_namespace_claim.json",
        add_self_hash(
            {
                "schema_version": "androidworld_candidate116_semantic_review_v7_namespace_claim/v1",
                "claimed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "review_id": prelock["review_id"],
                "prelock_sha256": prelock["prelock_sha256"],
                "config_sha256": config["config_sha256"],
                "approval_sha256": approval["approval_sha256"],
                "external_codex_exec_count_at_claim": 0,
                "auth_content_or_hash_persisted": False,
            },
            "claim_sha256",
        ),
    )
    state = BatchState(output_root)
    monitor: threading.Thread | None = None
    cleanup: dict[str, Any] | None = None
    try:
        verify_login(
            Path(config["codex_cli"]["resolved_path"]), config["child_environment"]
        )
        if ps_codex_exec_rows():
            raise ReviewLaunchError("external Codex exec appeared before worker start")
        monitor = threading.Thread(
            target=monitor_codex_processes,
            args=(state,),
            daemon=True,
            name="review-v7-monitor",
        )
        monitor.start()
        first_wave_barrier = threading.Barrier(PARALLELISM)
        futures: list[concurrent.futures.Future[dict[str, Any]]] = []
        capacity_by_case = {
            row["case_unit_id"]: row for row in capacity.get("cases") or []
        }
        input_by_case = {
            row["case_unit_id"]: row for row in prelock.get("case_inputs") or []
        }
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=PARALLELISM, thread_name_prefix="semantic-review-v7"
        ) as executor:
            for rank, case_id in enumerate(prelock["case_order"]):
                futures.append(
                    executor.submit(
                        run_one_case,
                        rank=rank,
                        case_id=case_id,
                        input_row=input_by_case[case_id],
                        capacity_row=capacity_by_case[case_id],
                        prelock=prelock,
                        config=config,
                        snapshot_root=snapshot_root,
                        output_root=output_root,
                        token_counter=token_counter,
                        tokenizer_binding=tokenizer_binding,
                        output_schema=output_schema,
                        base_prompt=base_prompt,
                        first_wave_barrier=first_wave_barrier,
                        state=state,
                    )
                )
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                except BaseException as exc:
                    state.fail(f"worker: {type(exc).__name__}: {exc}")
                    for pending in futures:
                        pending.cancel()
                    break
                with state.lock:
                    state.results[result["case_unit_id"]] = result
        state.monitor_stop.set()
        if monitor is not None:
            monitor.join(timeout=10)
        with state.lock:
            errors = list(state.errors)
            results = [
                state.results[case_id]
                for case_id in prelock["case_order"]
                if case_id in state.results
            ]
            peak_registered = state.peak_registered
            peak_live = state.peak_live
            covered = sorted(state.covered)
        if errors:
            raise ReviewLaunchError(f"semantic review batch failed closed: {errors}")
        if (
            len(results) != CASE_COUNT
            or len({row["case_unit_id"] for row in results}) != CASE_COUNT
            or [row["case_unit_id"] for row in results] != prelock["case_order"]
            or peak_registered != PARALLELISM
            or peak_live != PARALLELISM
            or covered != sorted(prelock["case_order"])
            or any(row["warning_count"] or row["error_count"] for row in results)
        ):
            raise ReviewLaunchError(
                f"exact 116/peak-six/warning-free gate failed: results={len(results)}, "
                f"registered={peak_registered}, live={peak_live}, covered={len(covered)}"
            )
        if ps_codex_exec_rows():
            raise ReviewLaunchError(
                "external Codex exec exists after all review workers ended"
            )
        original_auth = Path(config["original_codex_home"]) / "auth.json"
        if original_auth.read_bytes() != original_auth_bytes:
            raise ReviewLaunchError("original Codex auth.json changed during review")
        cleanup = destroy_runtime_roots(runtime_paths)
        receipt = add_self_hash(
            {
                "schema_version": RECEIPT_SCHEMA,
                "status": "complete_116_structurally_valid_independent_reviews",
                "review_id": prelock["review_id"],
                "case_count": CASE_COUNT,
                "case_order": prelock["case_order"],
                "case_order_sha256": prelock["case_order_sha256"],
                "results": results,
                "results_sha256": canonical_sha256(results),
                "accept_count": sum(row["verdict"] == "accept" for row in results),
                "reject_count": sum(row["verdict"] == "reject" for row in results),
                "warning_count": 0,
                "error_count": 0,
                "max_parallel": PARALLELISM,
                "observed_peak_registered": peak_registered,
                "observed_peak_live_codex_exec": peak_live,
                "covered_case_count": len(covered),
                "external_codex_exec_count_before": 0,
                "external_codex_exec_count_after": 0,
                "concurrency_samples": regular_file_binding(state.samples_path),
                "prelock_sha256": prelock["prelock_sha256"],
                "config_sha256": config["config_sha256"],
                "snapshot_sha256": config["snapshot_sha256"],
                "capacity_sha256": config["capacity_sha256"],
                "launch_approval_sha256": approval["approval_sha256"],
                "isolated_runtime_cleanup": cleanup,
                "auth_content_or_hash_persisted": False,
                "human_review_claimed": False,
                "freeze_authorized": False,
                "freeze_requires": [
                    "independent validator accept 116/116 with zero warnings/errors",
                    "root case-by-case acceptance 116/116",
                ],
            },
            "receipt_sha256",
        )
        ensure_no_sensitive_hash_fields(receipt)
        write_json_create_once(output_root / "_review_receipt.json", receipt)
        return receipt
    finally:
        state.monitor_stop.set()
        if monitor is not None and monitor.is_alive():
            monitor.join(timeout=2)
        with state.lock:
            for row in state.active.values():
                process = row.get("process")
                if process is not None and process.poll() is None:
                    process.kill()
            state.active.clear()
        if cleanup is None:
            try:
                cleanup = destroy_runtime_roots(runtime_paths)
            except BaseException:
                pass


def main() -> int:
    args = parse_args()
    prelock, config, capacity, approval, snapshot_root = verify_context(
        args.prelock.resolve(strict=True), args.launch_approval.resolve(strict=True)
    )
    receipt = run_batch(
        prelock=prelock,
        config=config,
        capacity=capacity,
        approval=approval,
        snapshot_root=snapshot_root,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "accept_count": receipt["accept_count"],
                "reject_count": receipt["reject_count"],
                "observed_peak_live_codex_exec": receipt[
                    "observed_peak_live_codex_exec"
                ],
                "warning_count": 0,
                "error_count": 0,
                "receipt_sha256": receipt["receipt_sha256"],
                "freeze_authorized": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewV7Error as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
