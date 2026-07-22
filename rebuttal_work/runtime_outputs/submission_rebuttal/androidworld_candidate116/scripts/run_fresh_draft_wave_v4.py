#!/usr/bin/env python3
"""Fail-closed launcher for the canonical-only 116-case Codex draft wave_004."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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
from typing import Any, Mapping


EXPECTED_CASE_COUNT = 116
EXPECTED_PARALLELISM = 6
EXPECTED_ENV_KEYS = {
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONNOUSERSITE",
    "TMPDIR",
    "TZ",
}
ALLOWED_CODEX_WARNING = (
    "WARNING: proceeding, even though we could not create PATH aliases: "
    "Operation not permitted (os error 1)"
)


class GenerationError(RuntimeError):
    """Raised when generation cannot be proven safe and complete."""


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GenerationError(f"cannot load {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise GenerationError(f"{label} is not a JSON object")
    return value


def verify_self_hash(value: Mapping[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if claimed != canonical_sha256(core):
        raise GenerationError(f"{label} self-hash mismatch")


def write_json_create_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def file_binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise GenerationError(f"bound path is not a regular file: {path}")
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def verify_binding(binding: Mapping[str, Any], label: str) -> Path:
    path = Path(str(binding.get("path") or ""))
    if not path.is_absolute():
        raise GenerationError(f"{label} path is not absolute")
    if path.is_symlink() or not path.is_file():
        raise GenerationError(f"{label} is missing, non-regular, or symlinked")
    if (
        path.stat().st_size != binding.get("size_bytes")
        or sha256_file(path) != binding.get("sha256")
    ):
        raise GenerationError(f"{label} byte binding mismatch")
    return path.resolve(strict=True)


def verify_python_runtime(config: Mapping[str, Any], environment: Mapping[str, str]) -> None:
    runtime = config.get("python_runtime")
    if not isinstance(runtime, Mapping):
        raise GenerationError("Python runtime binding is missing")
    invocation = Path(str(runtime.get("invocation_path") or ""))
    if not invocation.is_absolute() or not invocation.is_symlink():
        raise GenerationError("venv Python invocation is not an absolute symlink")
    expected_chain = runtime.get("symlink_chain")
    if not isinstance(expected_chain, list) or not expected_chain:
        raise GenerationError("venv Python symlink chain is missing")
    observed_chain: list[dict[str, str]] = []
    current = invocation
    seen: set[Path] = set()
    while current.is_symlink():
        if current in seen:
            raise GenerationError("cycle in venv Python symlink chain")
        seen.add(current)
        target = current.readlink()
        observed_chain.append({"path": str(current), "target": str(target)})
        current = target if target.is_absolute() else current.parent / target
        current = current.absolute()
    if observed_chain != expected_chain:
        raise GenerationError("venv Python symlink chain changed")
    if current.resolve(strict=True) != verify_binding(
        runtime.get("resolved_binary") or {}, "venv Python resolved binary"
    ):
        raise GenerationError("venv Python resolved binary changed")
    verify_binding(runtime.get("pyvenv_cfg") or {}, "venv pyvenv.cfg")
    command = config.get("native_batch_command")
    if not isinstance(command, list) or not command or command[0] != str(invocation):
        raise GenerationError("native batch command does not use the bound venv invocation")
    probe = subprocess.run(
        [
            str(invocation),
            "-c",
            "import jsonschema,requests,yaml; print('wave004-runtime-ok')",
        ],
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "wave004-runtime-ok":
        raise GenerationError(f"bound venv dependency probe failed: {probe.stderr.strip()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prelock", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


def parse_codex_status(completed: subprocess.CompletedProcess[str]) -> tuple[str, bool]:
    lines = [
        line.strip()
        for part in (completed.stdout, completed.stderr)
        for line in (part or "").splitlines()
        if line.strip()
    ]
    warning = False
    if lines and lines[0] == ALLOWED_CODEX_WARNING:
        warning = True
        lines = lines[1:]
    if completed.returncode != 0 or lines != ["Logged in using ChatGPT"]:
        raise GenerationError(f"Codex login is not exact: rc={completed.returncode}, lines={lines}")
    return "Logged in using ChatGPT", warning


def codex_check(config: Mapping[str, Any], environment: Mapping[str, str]) -> dict[str, Any]:
    codex = config.get("codex_cli") or {}
    invocation = verify_binding(codex, "Codex CLI")
    version = subprocess.run(
        [str(invocation), "--version"],
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if version.returncode != 0 or version.stdout.strip() != "codex-cli 0.144.4":
        raise GenerationError("Codex CLI version is not exactly 0.144.4")
    login = subprocess.run(
        [str(invocation), "login", "status"],
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    login_status, warning = parse_codex_status(login)
    record = {
        "schema_version": "androidworld_candidate116_codex_auth_check/v1",
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "codex_cli": dict(codex),
        "version": "codex-cli 0.144.4",
        "login_status": login_status,
        "allowed_path_alias_warning_observed": warning,
        "environment_sha256": canonical_sha256(dict(environment)),
    }
    record["auth_check_sha256"] = canonical_sha256(record)
    return record


def load_readonly_helper(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("wave004_readonly_helper", path)
    if spec is None or spec.loader is None:
        raise GenerationError("cannot load frozen read-only helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_snapshot(config: Mapping[str, Any]) -> None:
    manifest_path = verify_binding(
        config.get("toolchain_snapshot") or {}, "toolchain snapshot manifest"
    )
    manifest = load_json(manifest_path, "toolchain snapshot manifest")
    verify_self_hash(manifest, "snapshot_sha256", "toolchain snapshot manifest")
    root = Path(str(manifest.get("snapshot_root_absolute") or ""))
    if root.is_symlink() or not root.is_dir():
        raise GenerationError("toolchain snapshot root is missing or symlinked")
    expected = list(manifest.get("files") or [])
    observed = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        if path == manifest_path:
            continue
        if path.is_symlink():
            raise GenerationError(f"symlink in toolchain snapshot: {path}")
        observed.append(
            {
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    if (
        observed != expected
        or manifest.get("file_count") != len(observed)
        or manifest.get("files_sha256") != canonical_sha256(observed)
    ):
        raise GenerationError("toolchain snapshot exact file namespace changed")


def verify_context(prelock_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    prelock = load_json(prelock_path, "wave_004 prelock")
    verify_self_hash(prelock, "prelock_sha256", "wave_004 prelock")
    if (
        prelock.get("schema_version")
        != "androidworld_candidate116_codex_draft_prelock/v6_clean"
        or prelock.get("status") != "frozen_before_first_model_call"
        or prelock.get("generation_id") != "wave_004_v6_clean"
        or prelock.get("case_count") != EXPECTED_CASE_COUNT
    ):
        raise GenerationError("wave_004 prelock identity/status is invalid")
    config_path = verify_binding(prelock.get("draft_config") or {}, "wave_004 config")
    config = load_json(config_path, "wave_004 config")
    verify_self_hash(config, "config_sha256", "wave_004 config")
    if (
        config.get("schema_version")
        != "androidworld_candidate116_codex_draft_config/v6_clean"
        or config.get("generation_id") != "wave_004_v6_clean"
        or config.get("model") != "gpt-5.6-sol"
        or config.get("reasoning_effort") != "xhigh"
        or config.get("sandbox") != "read-only"
        or config.get("max_parallel") != EXPECTED_PARALLELISM
        or config.get("large_max_parallel") != EXPECTED_PARALLELISM
    ):
        raise GenerationError("wave_004 generation config is invalid")
    environment = config.get("child_environment")
    if (
        not isinstance(environment, dict)
        or set(environment) != EXPECTED_ENV_KEYS
        or config.get("child_environment_sha256") != canonical_sha256(environment)
    ):
        raise GenerationError("wave_004 child environment is not an exact closed set")
    verify_python_runtime(config, environment)
    verify_snapshot(config)
    independent_go_path = verify_binding(
        prelock.get("independent_go") or {}, "wave_004 v6 clean independent GO"
    )
    independent_go = load_json(independent_go_path, "wave_004 v6 clean independent GO")
    verify_self_hash(independent_go, "audit_sha256", "wave_004 v6 clean independent GO")
    gates = independent_go.get("gates")
    if (
        independent_go.get("schema_version")
        != "androidworld_candidate116_wave004_v6_clean_independent_go/v1"
        or independent_go.get("status") != "go"
        or independent_go.get("model_calls_made") != 0
        or not isinstance(gates, dict)
        or len(gates) != 7
        or any(value != "pass" for value in gates.values())
    ):
        raise GenerationError("wave_004 v6 clean independent GO is invalid")
    rejected_path = verify_binding(
        prelock.get("rejected_predecessor_gate") or {}, "rejected predecessor gate"
    )
    rejected = load_json(rejected_path, "rejected predecessor gate")
    if (
        rejected.get("status") != "REJECTED_DO_NOT_USE_AS_GO"
        or rejected.get("replacement_namespace") != "wave_004_v6_clean"
    ):
        raise GenerationError("rejected predecessor gate binding is invalid")
    wrapper = verify_binding(config.get("frozen_wrapper") or {}, "frozen wave_004 wrapper")
    if wrapper != Path(__file__).resolve() or sha256_file(wrapper) != sha256_file(Path(__file__)):
        raise GenerationError("wave_004 must execute through the frozen wrapper")
    verify_binding(prelock.get("packet_index") or {}, "canonical packet index")
    input_freeze_path = verify_binding(
        prelock.get("canonical_input_freeze") or {}, "canonical input freeze"
    )
    input_freeze = load_json(input_freeze_path, "canonical input freeze")
    verify_self_hash(input_freeze, "freeze_sha256", "canonical input freeze")
    cases = list(prelock.get("packet_cases") or [])
    if (
        len(cases) != EXPECTED_CASE_COUNT
        or len({row.get("case_unit_id") for row in cases}) != EXPECTED_CASE_COUNT
        or prelock.get("old_draft_content_or_issue_warnings_visible") is not False
        or config.get("old_draft_content_or_issue_warnings_visible") is not False
        or prelock.get("model_input_policy")
        != "complete canonical packets only; no prior draft-derived content"
        or config.get("model_input_policy")
        != "complete canonical packets only; no prior draft-derived content"
    ):
        raise GenerationError("wave_004 canonical-only packet set is invalid")
    for row in cases:
        packet = verify_binding(
            row.get("packet") or {}, f"{row.get('case_unit_id')} canonical packet"
        )
        if packet.parent.name != row.get("case_unit_id") or packet.name != "case_packet.md":
            raise GenerationError("canonical packet path/case identity mismatch")
        packet_text = packet.read_text(encoding="utf-8")
        if any(
            marker in packet_text
            for marker in (
                "# AndroidWorld Fresh Draft Packet",
                "## Fresh Generation Control",
                "prior_rejected_draft_issue",
                "## Authoritative Full Case Packet",
            )
        ):
            raise GenerationError("canonical packet exposes prior-draft-derived wrapper content")
    if prelock.get("case_order") != [row["case_unit_id"] for row in cases]:
        raise GenerationError("wave_004 prelock/canonical packet case order differs")
    output_root = Path(str(config.get("output_root_absolute") or ""))
    if output_root.exists() or output_root.is_symlink():
        raise GenerationError("wave_004 output root already exists")
    canonical_drafts = Path(str(config.get("canonical_drafts_absolute") or ""))
    canonical_contracts = Path(str(config.get("canonical_contracts_absolute") or ""))
    if any(canonical_drafts.rglob("*")) or (
        canonical_contracts.exists() and any(canonical_contracts.rglob("*"))
    ):
        raise GenerationError("canonical drafts/contracts are not empty before generation")
    return prelock, config


def ps_rows() -> dict[int, dict[str, Any]]:
    completed = subprocess.run(
        ["/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,command="],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        raise GenerationError(f"/bin/ps failed: {completed.stderr.strip()}")
    rows: dict[int, dict[str, Any]] = {}
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) != 4:
            continue
        try:
            pid, ppid, pgid = (int(parts[0]), int(parts[1]), int(parts[2]))
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
    basenames = [Path(token).name for token in argv]
    python_positions = [
        index for index, name in enumerate(basenames) if name.startswith("python")
    ]
    if python_positions and any(
        name in {"run_draft_batch.py", "draft_case_checklist.py"}
        and index > min(python_positions)
        for index, name in enumerate(basenames)
    ):
        return True
    return any(
        Path(token).name.startswith("codex")
        and index + 1 < len(argv)
        and argv[index + 1] == "exec"
        for index, token in enumerate(argv)
    )


def foreign_drafting_processes() -> list[dict[str, Any]]:
    rows = ps_rows()
    excluded = ancestor_pids(rows, os.getpid())
    return [
        {
            "pid": pid,
            "ppid": row["ppid"],
            "pgid": row["pgid"],
            "command_sha256": canonical_sha256(row["command"]),
        }
        for pid, row in sorted(rows.items())
        if pid not in excluded and is_drafting_argv(list(row["argv"]))
    ]


def terminate_group(process: subprocess.Popen[Any]) -> None:
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=10)
    rows = ps_rows()
    remaining = [row for row in rows.values() if row["pgid"] == process.pid]
    if remaining:
        raise GenerationError(f"batch process group is not empty: {remaining}")


def monitor_batch(
    process: subprocess.Popen[Any],
    *,
    config: Mapping[str, Any],
    prelock: Mapping[str, Any],
    stop: threading.Event,
    state: dict[str, Any],
    state_lock: threading.Lock,
) -> None:
    samples_path = Path(str(config["concurrency_samples_absolute"]))
    drafter_path = str(verify_binding(config["frozen_drafter"], "frozen drafter"))
    case_paths = {
        row["case_unit_id"]: str(Path(row["packet"]["path"]).resolve())
        for row in prelock["packet_cases"]
    }
    try:
        with samples_path.open("x", encoding="utf-8", buffering=1) as handle:
            sequence = 0
            while True:
                rows = ps_rows()
                active = []
                for row in rows.values():
                    if row["pgid"] != process.pid or drafter_path not in row["argv"]:
                        continue
                    matches = [case_id for case_id, path in case_paths.items() if path in row["argv"]]
                    if len(matches) != 1:
                        raise GenerationError("active drafter does not bind exactly one case packet")
                    active.append({"pid": row["pid"], "case_unit_id": matches[0]})
                if len(active) > EXPECTED_PARALLELISM:
                    raise GenerationError(f"observed more than six active case attempts: {active}")
                sample = {
                    "schema_version": "androidworld_candidate116_wave004_concurrency_sample/v1",
                    "sequence": sequence,
                    "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "monotonic_ns": time.monotonic_ns(),
                    "batch_pid": process.pid,
                    "active_case_attempt_count": len(active),
                    "active_case_attempts": sorted(active, key=lambda item: item["case_unit_id"]),
                }
                sample["sample_sha256"] = canonical_sha256(sample)
                handle.write(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                with state_lock:
                    state["sample_count"] += 1
                    state["peak"] = max(state["peak"], len(active))
                    state["covered"].update(item["case_unit_id"] for item in active)
                sequence += 1
                if stop.wait(0.1):
                    break
    except BaseException as exc:
        with state_lock:
            state["errors"].append(f"{type(exc).__name__}: {exc}")
        terminate_group(process)


def main() -> int:
    args = parse_args()
    raise GenerationError(
        "NO-GO: this launcher is superseded by the canonical-packet/v6 hardened "
        "chain and is permanently disabled before any model call"
    )
    # Unreachable historical implementation retained below for audit evidence.
    prelock_path = args.prelock.resolve(strict=True)
    prelock, config = verify_context(prelock_path)
    environment = dict(config["child_environment"])
    auth_pre = codex_check(config, environment)

    readonly_helper_path = verify_binding(
        config["frozen_readonly_helper"], "frozen read-only helper"
    )
    helper = load_readonly_helper(readonly_helper_path)
    readonly_before = load_json(
        verify_binding(prelock["readonly_before_snapshot"], "read-only before snapshot"),
        "read-only before snapshot",
    )
    immediate_before = helper.readonly_operation_snapshot(
        phase="immediate_before_candidate116_wave004_v6_clean",
        repo_root=Path(config["repository_root_absolute"]),
        work_root=Path(config["work_root_absolute"]),
    )
    if helper.compare_gate(readonly_before, immediate_before)["status"] != "pass":
        raise GenerationError("protected roots changed before wave_004 launch")

    foreign = foreign_drafting_processes()
    if foreign:
        raise GenerationError(f"foreign drafting processes exist before claim: {foreign}")
    if args.preflight_only:
        print(
            json.dumps(
                {
                    "status": "preflight_pass_no_model_calls",
                    "case_count": len(prelock["case_order"]),
                    "environment_key_count": len(environment),
                    "foreign_drafting_process_count": 0,
                    "output_root_absent": True,
                    "auth_check_sha256": auth_pre["auth_check_sha256"],
                },
                indent=2,
            )
        )
        return 0

    output_root = Path(config["output_root_absolute"])
    output_root.mkdir(mode=0o700, parents=False, exist_ok=False)
    root_stat = output_root.lstat()
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_IMODE(root_stat.st_mode) != 0o700:
        raise GenerationError("wave_004 atomic claim mode/type is invalid")
    claim = {
        "path": str(output_root),
        "device": root_stat.st_dev,
        "inode": root_stat.st_ino,
        "uid": root_stat.st_uid,
        "gid": root_stat.st_gid,
        "mode": stat.S_IMODE(root_stat.st_mode),
        "claimed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    claim["claim_sha256"] = canonical_sha256(claim)

    immediate_foreign = foreign_drafting_processes()
    if immediate_foreign:
        incident = {
            "status": "aborted_before_popen",
            "reason": "foreign drafting process appeared after namespace claim",
            "claim": claim,
            "foreign_processes": immediate_foreign,
            "popen_count": 0,
        }
        incident["incident_sha256"] = canonical_sha256(incident)
        write_json_create_once(output_root / "_pre_popen_abort.json", incident)
        raise GenerationError(f"foreign drafting process appeared after claim: {immediate_foreign}")

    command = list(config["native_batch_command"])
    process: subprocess.Popen[Any] | None = None
    stop = threading.Event()
    state_lock = threading.Lock()
    state: dict[str, Any] = {"sample_count": 0, "peak": 0, "covered": set(), "errors": []}
    previous_handlers = {item: signal.getsignal(item) for item in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}

    def handle_signal(signum: int, _frame: Any) -> None:
        if process is not None:
            terminate_group(process)
        raise GenerationError(f"wrapper received {signal.Signals(signum).name}")

    try:
        for item in previous_handlers:
            signal.signal(item, handle_signal)
        process = subprocess.Popen(
            command,
            cwd=config["repository_root_absolute"],
            env=environment,
            start_new_session=True,
        )
        thread = threading.Thread(
            target=monitor_batch,
            kwargs={
                "process": process,
                "config": config,
                "prelock": prelock,
                "stop": stop,
                "state": state,
                "state_lock": state_lock,
            },
            name="androidworld-wave004-concurrency-monitor",
            daemon=False,
        )
        thread.start()
        returncode = process.wait()
        stop.set()
        thread.join(timeout=30)
        if thread.is_alive():
            terminate_group(process)
            raise GenerationError("concurrency monitor did not stop")
        terminate_group(process)
    finally:
        stop.set()
        for item, handler in previous_handlers.items():
            signal.signal(item, handler)

    with state_lock:
        errors = list(state["errors"])
        covered = sorted(state["covered"])
        peak = int(state["peak"])
        sample_count = int(state["sample_count"])
    if errors:
        raise GenerationError(f"concurrency monitor failed: {errors}")
    if returncode != 0:
        raise GenerationError(f"native NeurIPS batch runner returned {returncode}")
    if peak != EXPECTED_PARALLELISM or covered != sorted(prelock["case_order"]):
        raise GenerationError(
            f"exact-six/coverage gate failed: peak={peak}, covered={len(covered)}"
        )

    summary_path = output_root / "_batch_summary.json"
    results_path = output_root / "_batch_results.jsonl"
    summary = load_json(summary_path, "wave_004 batch summary")
    if (
        summary.get("total_cases") != EXPECTED_CASE_COUNT
        or summary.get("completed_cases") != EXPECTED_CASE_COUNT
        or summary.get("success_cases") != EXPECTED_CASE_COUNT
        or summary.get("failed_cases") != 0
        or summary.get("skipped_cases") != 0
    ):
        raise GenerationError("native batch summary is not a clean 116/116 success")
    auth_post = codex_check(config, environment)
    readonly_after = helper.readonly_operation_snapshot(
        phase="after_candidate116_wave004_v6_clean",
        repo_root=Path(config["repository_root_absolute"]),
        work_root=Path(config["work_root_absolute"]),
    )
    readonly_comparison = helper.compare_gate(readonly_before, readonly_after)
    if readonly_comparison["status"] != "pass":
        raise GenerationError("protected roots changed during wave_004 generation")
    readonly_after["snapshot_sha256"] = canonical_sha256(readonly_after)
    readonly_path = output_root / "_readonly_after.json"
    write_json_create_once(readonly_path, readonly_after)
    guard = {
        "schema_version": "androidworld_candidate116_wave004_readonly_guard/v1",
        "status": "pass",
        "comparison": readonly_comparison,
        "before": dict(prelock["readonly_before_snapshot"]),
        "after": file_binding(readonly_path) | {"snapshot_sha256": readonly_after["snapshot_sha256"]},
    }
    guard["guard_sha256"] = canonical_sha256(guard)
    guard_path = output_root / "_readonly_guard.json"
    write_json_create_once(guard_path, guard)

    final_stat = output_root.lstat()
    if final_stat.st_dev != claim["device"] or final_stat.st_ino != claim["inode"]:
        raise GenerationError("wave_004 claimed directory inode was replaced")
    audit = {
        "schema_version": "androidworld_candidate116_wave004_concurrency_audit/v1",
        "status": "pass",
        "required_peak": EXPECTED_PARALLELISM,
        "observed_peak": peak,
        "sample_count": sample_count,
        "case_count_expected": EXPECTED_CASE_COUNT,
        "case_count_observed": len(covered),
        "observed_cases": covered,
        "samples": file_binding(Path(config["concurrency_samples_absolute"])),
        "never_exceeded_six": True,
        "all_cases_observed": True,
    }
    audit["audit_sha256"] = canonical_sha256(audit)
    audit_path = output_root / "_concurrency_audit.json"
    write_json_create_once(audit_path, audit)

    receipt = {
        "schema_version": "androidworld_candidate116_fresh_draft_generation_receipt/v1",
        "status": "generation_complete_unfrozen",
        "generation_id": "wave_004_v6_clean",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "prelock_sha256": prelock["prelock_sha256"],
        "config_sha256": config["config_sha256"],
        "namespace_claim": claim,
        "child_environment_sha256": config["child_environment_sha256"],
        "codex_auth_pre": auth_pre,
        "codex_auth_post": auth_post,
        "native_batch_summary": file_binding(summary_path),
        "native_batch_results": file_binding(results_path),
        "concurrency_audit": file_binding(audit_path) | {"audit_sha256": audit["audit_sha256"]},
        "readonly_guard": file_binding(guard_path) | {"guard_sha256": guard["guard_sha256"]},
        "case_count": EXPECTED_CASE_COUNT,
        "freeze_authorized": False,
        "freeze_requires": "automatic QC plus independent semantic/root acceptance 116/116",
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    write_json_create_once(output_root / "_generation_receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "receipt_sha256": receipt["receipt_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
