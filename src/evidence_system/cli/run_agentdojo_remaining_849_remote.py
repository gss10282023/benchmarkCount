"""Durable on-VPS runner for one shard of the remaining-849 AgentDojo run.

The controller admits one frozen agent lane at a time.  Each admitted job is
run by the existing formal detached supervisor and published by the existing
formal postprocessor.  A pause request stops only new admission; already
running process groups are always drained.
"""

from __future__ import annotations

import argparse
import copy
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import threading
import time
from typing import Any, Mapping, Sequence

from evidence_system.adapters import agentdojo as adapter
from evidence_system.adapters import agentdojo_formal_postprocessor as postprocessor
from evidence_system.adapters import agentdojo_formal_supervisor as supervisor
from evidence_system.adapters import runtime as adapter_runtime
from evidence_system.adapters.agentdojo_runtime_control import (
    job_identity_sha256,
    resource_worker_process_binding_sha256,
)
from evidence_system.adapters.runtime import formal_job_binding_sha256
from evidence_system.contracts.agentdojo_execution_namespace import (
    verify_formal_stage_authorization,
)
from evidence_system.contracts.common import load_mapping, utc_now_iso
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.orchestrator.jobs import resolve_infra_target


AGENTS = ("Agent A", "Agent B", "Agent C")
LANE_WORKERS = {"Agent A": 8, "Agent B": 4, "Agent C": 4}
TERMINAL_SUPERVISOR_STATES = {
    "exited",
    "boot_changed",
    "identity_conflict",
}
HARD_FATAL_ERROR_TYPES = {
    "PermissionError",
    "ProcessIdentityConflict",
    "BootChanged",
}
_ORIGINAL_STANDARD_ARTIFACT_DESCRIPTORS = (
    postprocessor._standard_artifact_descriptors
)
_ORIGINAL_CURRENT_GIT_COMMIT_HASH = adapter_runtime.current_git_commit_hash
_POSTPROCESSOR_COMPATIBILITY_LOCK = threading.Lock()
_INSTALLED_REPOSITORY_COMMIT_HASH: str | None = None


class RunnerError(RuntimeError):
    pass


class HardFatal(RunnerError):
    pass


def _map_formal_descriptor_contract_ids(
    descriptors: Sequence[Any],
) -> tuple[Any, ...]:
    """Match the existing AgentDojo adapter's evaluator requirement mapping."""

    return tuple(
        replace(
            descriptor,
            artifact_contract_requirement_ids=(
                "smoke-native-evaluator-output",
            ),
        )
        if descriptor.artifact_type == "native_evaluator_output"
        else descriptor
        for descriptor in descriptors
    )


def _compatible_standard_artifact_descriptors(
    *, native: Path, logs: Path, environment_path: Path
) -> tuple[Any, ...]:
    return _map_formal_descriptor_contract_ids(
        _ORIGINAL_STANDARD_ARTIFACT_DESCRIPTORS(
            native=native, logs=logs, environment_path=environment_path
        )
    )


def _normalize_repository_commit_hash(value: str) -> str:
    return _digest(value, "repository commit hash")


def _locked_current_git_commit_hash() -> str:
    if _INSTALLED_REPOSITORY_COMMIT_HASH is None:  # pragma: no cover - install invariant
        raise HardFatal("repository commit fallback was not installed")
    return _INSTALLED_REPOSITORY_COMMIT_HASH


def install_postprocessor_compatibility_wrapper(
    *, repository_commit_hash: str | None = None
) -> None:
    """Install one immutable, idempotent runner-process compatibility hook."""

    global _INSTALLED_REPOSITORY_COMMIT_HASH
    with _POSTPROCESSOR_COMPATIBILITY_LOCK:
        current = postprocessor._standard_artifact_descriptors
        if current is not _compatible_standard_artifact_descriptors:
            if current is not _ORIGINAL_STANDARD_ARTIFACT_DESCRIPTORS:
                raise HardFatal("formal postprocessor descriptor builder changed")
            postprocessor._standard_artifact_descriptors = (
                _compatible_standard_artifact_descriptors
            )

        if repository_commit_hash is None:
            return
        expected = _normalize_repository_commit_hash(repository_commit_hash)
        current_commit_builder = adapter_runtime.current_git_commit_hash
        if current_commit_builder is _locked_current_git_commit_hash:
            if _INSTALLED_REPOSITORY_COMMIT_HASH != expected:
                raise HardFatal("repository commit fallback changed")
            return
        if current_commit_builder is not _ORIGINAL_CURRENT_GIT_COMMIT_HASH:
            raise HardFatal("repository commit builder changed")

        repository_metadata = adapter_runtime.repo_root() / ".git"
        if repository_metadata.exists() or repository_metadata.is_symlink():
            if _ORIGINAL_CURRENT_GIT_COMMIT_HASH() != expected:
                raise HardFatal("repository commit differs from deployed source")
        _INSTALLED_REPOSITORY_COMMIT_HASH = expected
        adapter_runtime.current_git_commit_hash = _locked_current_git_commit_hash


@dataclass(frozen=True)
class LockedEntry:
    ordinal: int
    vps_id: str
    agent_id: str
    job_path: Path
    job_file_sha256: str
    job: dict[str, Any]


@dataclass(frozen=True)
class RunnerPaths:
    runtime_root: Path
    raw_root: Path
    blind_root: Path
    failed_root: Path
    attempt_root: Path
    canonical_root: Path
    completion_journal: Path
    failed_journal: Path
    lifecycle_lock: Path


def _digest(value: Any, field: str) -> str:
    normalized = str(value).removeprefix("sha256:")
    if len(normalized) != 64 or any(c not in "0123456789abcdef" for c in normalized):
        raise RunnerError(f"{field} is not a lowercase SHA-256")
    return normalized


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise RunnerError(f"{label} is not a regular file")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RunnerError(f"{label} is linked or non-regular")
    return path


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_regular_file(path, label).read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RunnerError(f"{label} is not a JSON object")
    return value


def _resolve_indexed_path(index: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    direct = (Path.cwd() / candidate).resolve()
    return direct if direct.exists() else (index.parent / candidate).resolve()


def load_locked_entries(
    plan_index: str | Path, *, vps_id: str, agent_id: str
) -> tuple[dict[str, Any], list[LockedEntry]]:
    if agent_id not in AGENTS:
        raise RunnerError("agent lane is invalid")
    index = Path(plan_index).resolve()
    payload = _load_object(index, "campaign plan index")
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list) or not entries_raw:
        raise RunnerError("campaign plan has no entries")
    if payload.get("entries_sha256") is not None and _digest(
        payload["entries_sha256"], "entries_sha256"
    ) != sha256_object(entries_raw):
        raise RunnerError("campaign plan entries hash differs")
    result: list[LockedEntry] = []
    for ordinal, raw in enumerate(entries_raw):
        if not isinstance(raw, Mapping):
            raise RunnerError("campaign plan has a non-object entry")
        assigned = str(raw.get("vps_id") or raw.get("shard_id") or "")
        if assigned != vps_id or str(raw.get("agent_id") or "") != agent_id:
            continue
        raw_path = raw.get("path") or raw.get("job_path")
        if not isinstance(raw_path, str) or not raw_path:
            raise RunnerError("campaign entry has no locked job path")
        path = _resolve_indexed_path(index, raw_path)
        expected = _digest(
            raw.get("sha256") or raw.get("job_file_sha256"),
            "campaign job file sha256",
        )
        if sha256_file(_regular_file(path, "campaign locked job")) != expected:
            raise RunnerError("campaign locked job bytes differ")
        job = _load_object(path, "campaign locked job")
        if str(job.get("agent_id") or "") != agent_id:
            raise RunnerError("campaign locked job agent differs")
        if raw.get("job_identity_sha256") is not None and _digest(
            raw["job_identity_sha256"], "job_identity_sha256"
        ) != job_identity_sha256(job):
            raise RunnerError("campaign job identity differs")
        result.append(
            LockedEntry(
                ordinal=ordinal,
                vps_id=vps_id,
                agent_id=agent_id,
                job_path=path,
                job_file_sha256=expected,
                job=job,
            )
        )
    if not result:
        raise RunnerError("campaign plan assigns no jobs to this VPS/lane")
    return payload, result


def effective_workers(agent_id: str, requested: int | None) -> int:
    locked = LANE_WORKERS[agent_id]
    if requested is None:
        return locked
    if requested < 1:
        raise RunnerError("max-workers must be positive")
    return min(locked, int(requested))


def _paths(target: Any, *, job: Mapping[str, Any], session_id: str) -> RunnerPaths:
    config = target.benchmark_config
    values = {
        "runtime_root": Path(str(config.get("runtime_state_root") or "")),
        "raw_root": Path(str(config.get("remote_raw_root") or "")),
        "blind_root": Path(str(config.get("blind_aggregate_root") or "")),
        "failed_root": Path(str(config.get("failed_attempt_archive_root") or "")),
    }
    if any(not value.is_absolute() for value in values.values()):
        raise RunnerError("formal evidence roots must be absolute")
    if len({str(value) for value in values.values()}) != len(values):
        raise RunnerError("formal evidence roots must be distinct")
    binding = formal_job_binding_sha256(job)
    attempt = values["runtime_root"] / "sealed-attempts" / binding / session_id
    return RunnerPaths(
        **values,
        attempt_root=attempt,
        canonical_root=values["raw_root"] / binding,
        completion_journal=values["blind_root"] / "formal-completion-journal.v2.jsonl",
        failed_journal=values["blind_root"] / "formal-failed-attempt-journal.v1.jsonl",
        lifecycle_lock=values["blind_root"] / ".canonical-lifecycle.lock",
    )


def _publish_launch_intent(
    path: Path, *, job: Mapping[str, Any], authorization_sha256: str
) -> None:
    namespace = path.parent.parent
    namespace.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(namespace, 0o700)
    path.parent.mkdir(mode=0o700, exist_ok=True)
    if path.exists():
        return
    path.mkdir(mode=0o700)
    payload = {
        "schema_version": "agentdojo_formal_job_launch_intent/v1",
        "created_at": utc_now_iso(),
        "stage_authorization_sha256": authorization_sha256,
        "execution_lock_sha256": str(job["execution_lock_sha256"]),
        "execution_policy_sha256": str(job["execution_policy_sha256"]),
        "job_binding_sha256": formal_job_binding_sha256(job),
        "job_identity_sha256": job_identity_sha256(job),
    }
    marker = path / supervisor.LAUNCH_INTENT
    descriptor = os.open(
        marker,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.write(
            descriptor,
            (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode(),
        )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _source_entry(bundle: Mapping[str, Any], task_id: str) -> dict[str, Any]:
    value = adapter._bundle_source_entry(bundle, task_id=task_id)
    if not isinstance(value, dict):
        raise RunnerError("source bundle has no job task entry")
    return value


def _worker_command(
    *,
    entry: LockedEntry,
    target: Any,
    agents_config: Path,
    source_bundle_path: Path,
    source_bundle: Mapping[str, Any],
    stage_authorization: Path,
    authorization_sha256: str,
    attempt_root: Path,
) -> str:
    plan = adapter.plan_smoke_execution(
        dict(entry.job),
        target=target,
        agents_config_path=str(agents_config),
        dotenv_path=".env",
        source_bundle_path=str(source_bundle_path),
        source_bundle=dict(source_bundle),
    )
    if plan.get("status") != "runnable" or not plan.get("runner_command"):
        raise RunnerError("formal adapter plan is not runnable")
    auth = verify_formal_stage_authorization(
        path=stage_authorization,
        expected_sha256=authorization_sha256,
        job=entry.job,
        expected_runtime_policy_semantic_sha256=str(
            entry.job["openrouter_runtime_policy_sha256"]
        ),
        expected_runtime_policy_file_sha256=str(
            entry.job["openrouter_runtime_policy_file_sha256"]
        ),
        expected_runtime_state_dir=str(target.benchmark_config["runtime_state_root"]),
    )
    token = resource_worker_process_binding_sha256(
        execution_scope_sha256=str(entry.job["execution_lock_sha256"]),
        stage_id=str(auth.payload["stage_id"]),
        session_id=str(auth.payload["session_id"]),
        stage_binding_sha256=authorization_sha256,
    )
    return (
        f"{plan['runner_command']}"
        f" --blind-group {shlex.quote(str(target.benchmark_config['blind_group']))}"
        f" --stage-authorization {shlex.quote(str(stage_authorization))}"
        f" --stage-authorization-sha256 {shlex.quote(authorization_sha256)}"
        f" --resource-stage-token {shlex.quote(token)}"
        f" --output-dir {shlex.quote(str(attempt_root))}"
    )


def _execution_context(
    *,
    target: Any,
    entry: LockedEntry,
    source_bundle_path: Path,
    command: str,
    producer_command_sha256: str | None = None,
) -> dict[str, Any]:
    producer_hash = (
        hashlib.sha256(command.encode()).hexdigest()
        if producer_command_sha256 is None
        else _digest(producer_command_sha256, "producer command sha256")
    )
    return {
        "schema_version": "agentdojo_formal_execution_context/v1",
        "machine_id": target.machine_id,
        "machine_role": target.machine_role,
        "ssh_host": target.ssh_host,
        "ssh_port": int(target.ssh_port),
        "remote_workdir": target.remote_workdir,
        "runner_workdir": target.runner_workdir,
        "benchmark_name": target.benchmark_name,
        "benchmark_config_hash": str(entry.job["benchmark_config_hash"]),
        "source_bundle_hash": sha256_file(source_bundle_path),
        "official_split_hash": str(entry.job.get("official_split_hash") or "0" * 64),
        "producer_command_sha256": producer_hash,
    }


def _append_controller_issue(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    line = json.dumps(dict(payload), separators=(",", ":"), sort_keys=True) + "\n"
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
        0o640,
    )
    try:
        os.write(descriptor, line.encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _linux_starttime_ticks(pid: int) -> int:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").strip()
    end = raw.rfind(")")
    fields = raw[end + 1 :].split() if end >= 2 else []
    if len(fields) <= 19:
        raise RunnerError("controller proc identity is unavailable")
    value = int(fields[19])
    if value <= 0:
        raise RunnerError("controller proc starttime is invalid")
    return value


def _linux_process_state(pid: int) -> str:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").strip()
    end = raw.rfind(")")
    fields = raw[end + 1 :].split() if end >= 2 else []
    if not fields or len(fields[0]) != 1:
        raise RunnerError("controller proc state is unavailable")
    return fields[0]


def _wait_for_supervisor_process_exit(
    attempt_root: Path, *, session_id: str, maximum_wait_seconds: float = 30.0
) -> None:
    """Wait for the supervisor that wrote the exit receipt to leave procfs.

    The exit receipt is fsynced immediately before the detached supervisor
    itself exits.  Treating receipt visibility as process disappearance races
    the postprocessor's strict lifecycle check and can strand a successful,
    already-paid attempt.  This metadata-only wait sends no signal and never
    opens worker output.
    """

    state = supervisor._verify_state(
        attempt_root / supervisor.STATE, expected_session_id=session_id
    )
    pid = int(state["supervisor_pid"])
    expected_starttime = int(state["supervisor_starttime_ticks"])
    deadline = time.monotonic() + maximum_wait_seconds
    while True:
        # launch_once() deliberately detaches the supervisor and drops the
        # Popen handle.  The runner is still its parent, so a completed
        # supervisor can otherwise remain as a zombie in /proc until another
        # subprocess happens to trigger Python's opportunistic cleanup.  The
        # formal postprocessor correctly rejects any matching /proc identity;
        # explicitly reap this exact child before testing process identity.
        try:
            waited_pid, _status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            waited_pid = 0
        if waited_pid == pid:
            return
        try:
            observed_starttime = _linux_starttime_ticks(pid)
        except (FileNotFoundError, ProcessLookupError):
            return
        if observed_starttime != expected_starttime:
            return
        try:
            process_state = _linux_process_state(pid)
        except (FileNotFoundError, ProcessLookupError):
            return
        if process_state == "Z":
            # The detached supervisor fsyncs its exit receipt before exiting.
            # Because it was spawned by this long-lived controller, it may sit
            # as our child zombie until explicitly reaped.  Reaping cannot
            # signal the worker group (already proven gone by the receipt).
            try:
                os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                pass
            return
        if time.monotonic() >= deadline:
            raise HardFatal("supervisor remained alive after its exit receipt")
        time.sleep(0.1)


def _repair_prematurely_sealed_stream_modes(attempt_root: Path) -> None:
    """Restore only the two supervisor streams after failed packaging sealed them.

    The formal postprocessor normally seals the attempt after verifying the
    streams are mode 0600.  A packaging exception in the historical attempt
    path occurred after the tree was made read-only, so reconciliation must
    restore exactly those two control streams to their pre-packaging mode.
    Content bytes are never opened or changed; the successful retry seals the
    complete tree read-only again.
    """

    for name in postprocessor.SEALED_STREAMS:
        path = attempt_root / name
        info = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) not in {0o400, 0o600}
        ):
            raise HardFatal("prematurely sealed stream metadata is unsafe")
        if stat.S_IMODE(info.st_mode) == 0o400:
            os.chmod(path, 0o600)


def _linux_boot_id() -> str:
    value = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    if len(value) != 36:
        raise RunnerError("controller boot identity is invalid")
    return value


def publish_controller_identity(
    path: Path, *, campaign_plan_sha256: str, vps_id: str
) -> dict[str, Any]:
    boot_id = _linux_boot_id()
    payload = {
        "schema_version": "agentdojo_remaining_849_controller_identity/v1",
        "campaign_plan_sha256": _digest(campaign_plan_sha256, "campaign plan sha256"),
        "vps_id": vps_id,
        "pid": os.getpid(),
        "starttime_ticks": _linux_starttime_ticks(os.getpid()),
        "host_boot_id": boot_id,
        "created_at": utc_now_iso(),
    }
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() or path.is_symlink():
        existing = _load_object(path, "controller identity")
        stable_fields = (
            "schema_version",
            "campaign_plan_sha256",
            "vps_id",
            "pid",
            "starttime_ticks",
            "host_boot_id",
        )
        if all(existing.get(field) == payload[field] for field in stable_fields):
            return existing
        raise RunnerError("a different controller identity already exists")
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.write(
            descriptor,
            (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode(),
        )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError:
        existing = _load_object(path, "controller identity")
        stable_fields = (
            "schema_version",
            "campaign_plan_sha256",
            "vps_id",
            "pid",
            "starttime_ticks",
            "host_boot_id",
        )
        if not all(existing.get(field) == payload[field] for field in stable_fields):
            raise RunnerError("a concurrent different controller identity exists")
        return existing
    finally:
        temporary.unlink(missing_ok=True)
    return payload


def preflight_lane(
    *,
    entries: Sequence[LockedEntry],
    target: Any,
    agents_config: Path,
    source_bundle_path: Path,
    source_bundle: Mapping[str, Any],
    stage_authorization: Path,
    authorization_sha256: str,
) -> None:
    """Validate the complete denominator before admitting the first paid job."""

    for entry in entries:
        _source_entry(source_bundle, str(entry.job.get("task_id") or ""))
        verify_formal_stage_authorization(
            path=stage_authorization,
            expected_sha256=authorization_sha256,
            job=entry.job,
            expected_runtime_policy_semantic_sha256=str(
                entry.job["openrouter_runtime_policy_sha256"]
            ),
            expected_runtime_policy_file_sha256=str(
                entry.job["openrouter_runtime_policy_file_sha256"]
            ),
            expected_runtime_state_dir=str(
                target.benchmark_config["runtime_state_root"]
            ),
        )
        planned = adapter.plan_smoke_execution(
            dict(entry.job),
            target=target,
            agents_config_path=str(agents_config),
            dotenv_path=".env",
            source_bundle_path=str(source_bundle_path),
            source_bundle=dict(source_bundle),
        )
        if planned.get("status") != "runnable" or not planned.get("runner_command"):
            raise RunnerError("formal adapter pre-admission plan is not runnable")


def _run_one(
    entry: LockedEntry,
    *,
    target: Any,
    agents_config: Path,
    source_bundle_path: Path,
    source_bundle: Mapping[str, Any],
    stage_authorization: Path,
    authorization_sha256: str,
    stage_payload: Mapping[str, Any],
) -> dict[str, Any]:
    session_id = str(stage_payload["session_id"])
    stage_id = str(stage_payload["stage_id"])
    paths = _paths(target, job=entry.job, session_id=session_id)
    paths.raw_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    paths.blind_root.mkdir(parents=True, exist_ok=True, mode=0o750)
    paths.failed_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if paths.canonical_root.exists():
        verified = postprocessor.verify_canonical_job(paths.canonical_root, job=entry.job)
        return {"status": "reused", "job_identity_sha256": job_identity_sha256(entry.job), "artifact_file_count": len(verified["inventory"])}
    command = _worker_command(
        entry=entry,
        target=target,
        agents_config=agents_config,
        source_bundle_path=source_bundle_path,
        source_bundle=source_bundle,
        stage_authorization=stage_authorization,
        authorization_sha256=authorization_sha256,
        attempt_root=paths.attempt_root,
    )
    binding = formal_job_binding_sha256(entry.job)
    lifecycle_exists = any(
        (paths.attempt_root / name).exists()
        or (paths.attempt_root / name).is_symlink()
        for name in (supervisor.CLAIM, supervisor.STATE, supervisor.EXIT)
    )
    sealed_producer_command_sha256: str | None = None
    if lifecycle_exists:
        # Reconcile an already-started or already-exited paid attempt without
        # passing its worker-produced files through launch_once's intentionally
        # strict pre-launch field-set gate.
        sealed_spec = supervisor._verify_spec(paths.attempt_root / supervisor.SPEC)
        sealed_producer_command_sha256 = _digest(
            sealed_spec["command_sha256"], "sealed producer command sha256"
        )
        status = supervisor.status_only(
            paths.attempt_root, session_id=session_id
        )
    else:
        _publish_launch_intent(
            paths.attempt_root,
            job=entry.job,
            authorization_sha256=authorization_sha256,
        )
        status = supervisor.launch_once(
            attempt_root=paths.attempt_root,
            stage_id=stage_id,
            session_id=session_id,
            job_binding_sha256=binding,
            authorization_sha256=authorization_sha256,
            timeout_seconds=int(stage_payload["formal_wall_clock_timeout_seconds"]),
            kill_grace_seconds=int(stage_payload["kill_grace_seconds"]),
            command=command,
        )
    missing_receipt_since: float | None = None
    while status.get("status") not in TERMINAL_SUPERVISOR_STATES:
        if status.get("status") == "exit_receipt_missing":
            if missing_receipt_since is None:
                missing_receipt_since = time.monotonic()
            elif time.monotonic() - missing_receipt_since >= 30.0:
                raise HardFatal(
                    "supervisor exit receipt remained missing after process exit"
                )
        else:
            missing_receipt_since = None
        time.sleep(2.0)
        status = supervisor.status_only(paths.attempt_root, session_id=session_id)
    if status.get("status") != "exited":
        raise HardFatal(f"unrecoverable supervisor state {status.get('status')}")
    _wait_for_supervisor_process_exit(
        paths.attempt_root, session_id=session_id
    )
    _repair_prematurely_sealed_stream_modes(paths.attempt_root)
    exit_code = int(status.get("exit_code") or 0)
    context = _execution_context(
        target=target,
        entry=entry,
        source_bundle_path=source_bundle_path,
        command=command,
        producer_command_sha256=sealed_producer_command_sha256,
    )
    common = {
        "job": entry.job,
        "attempt_root": paths.attempt_root,
        "canonical_root": paths.canonical_root,
        "authorization_sha256": authorization_sha256,
        "stage_id": stage_id,
        "session_id": session_id,
        "blind_group": str(target.benchmark_config["blind_group"]),
        "lifecycle_lock": paths.lifecycle_lock,
    }
    if exit_code == 0:
        result = postprocessor.publish_or_verify_success(
            **common,
            completion_index=paths.completion_journal,
            execution_context=context,
        )
        return {
            "status": str(result["status"]),
            "job_identity_sha256": job_identity_sha256(entry.job),
            "artifact_file_count": int(result["artifact_file_count"]),
        }
    failure_category = "timeout" if bool(status.get("timed_out")) else "worker_error"
    result = postprocessor.archive_failed_attempt(
        **common,
        failed_attempt_index=paths.failed_journal,
        failed_archive_root=paths.failed_root,
        failure_category=failure_category,
        worker_exit_code=exit_code,
    )
    return {
        "status": "failed",
        "job_identity_sha256": job_identity_sha256(entry.job),
        "attempt_identity_sha256": result["attempt_identity_sha256"],
    }


def _wait_for_pause_release(path: Path, *, poll_seconds: float) -> None:
    """Publish controller identity first, then wait without admitting work."""

    if poll_seconds <= 0:
        raise RunnerError("pause-release poll interval must be positive")
    while True:
        try:
            info = path.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise HardFatal("pause request is not a regular file")
        time.sleep(poll_seconds)


def run_lane(args: argparse.Namespace) -> dict[str, Any]:
    install_postprocessor_compatibility_wrapper(
        repository_commit_hash=getattr(args, "repository_commit_hash", None)
    )
    plan_payload, entries = load_locked_entries(
        args.campaign_plan_index, vps_id=args.vps_id, agent_id=args.agent
    )
    infra = load_mapping(args.infra_config)
    target = resolve_infra_target("agentdojo", infra)
    source_bundle_path = Path(args.source_bundle).resolve()
    source_bundle = load_mapping(source_bundle_path)
    stage_authorization = Path(args.stage_authorization).resolve()
    authorization_sha256 = sha256_file(_regular_file(stage_authorization, "stage authorization"))
    stage_payload = _load_object(stage_authorization, "stage authorization")
    if int(stage_payload["record_slot_count"]) != len(entries):
        raise RunnerError("stage authorization denominator differs from lane shard")
    if str(stage_payload["plan_index_sha256"]) != sha256_file(Path(args.campaign_plan_index)):
        raise RunnerError("stage authorization plan-index binding differs")
    workers = effective_workers(args.agent, args.max_workers)
    if workers > int(stage_payload["workers"]):
        raise RunnerError("requested workers exceed stage authorization")
    pause = Path(args.pause_request).resolve()
    issue_ledger = Path(args.issue_ledger).resolve()
    controller_identity = Path(args.controller_identity).resolve()
    preflight_lane(
        entries=entries,
        target=target,
        agents_config=Path(args.agents_config).resolve(),
        source_bundle_path=source_bundle_path,
        source_bundle=source_bundle,
        stage_authorization=stage_authorization,
        authorization_sha256=authorization_sha256,
    )
    publish_controller_identity(
        controller_identity,
        campaign_plan_sha256=sha256_file(Path(args.campaign_plan_index)),
        vps_id=args.vps_id,
    )
    if getattr(args, "wait_for_pause_release", False):
        _wait_for_pause_release(
            pause, poll_seconds=float(args.barrier_poll_seconds)
        )
    counts = {"completed": 0, "reused": 0, "failed": 0}
    hard_fatal: str | None = None
    admitted = 0
    admission_limit = getattr(args, "max_admissions", None)
    if admission_limit is not None and int(admission_limit) < 1:
        raise RunnerError("max-admissions must be positive")
    selected_entries = (
        entries
        if admission_limit is None
        else entries[: min(int(admission_limit), len(entries))]
    )
    iterator = iter(selected_entries)
    futures: dict[Future[dict[str, Any]], LockedEntry] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while True:
            while len(futures) < workers and not pause.exists() and hard_fatal is None:
                try:
                    entry = next(iterator)
                except StopIteration:
                    break
                future = pool.submit(
                    _run_one,
                    entry,
                    target=target,
                    agents_config=Path(args.agents_config).resolve(),
                    source_bundle_path=source_bundle_path,
                    source_bundle=source_bundle,
                    stage_authorization=stage_authorization,
                    authorization_sha256=authorization_sha256,
                    stage_payload=stage_payload,
                )
                futures[future] = entry
                admitted += 1
            if not futures:
                break
            done, _ = wait(tuple(futures), return_when=FIRST_COMPLETED)
            for future in done:
                entry = futures.pop(future)
                try:
                    result = future.result()
                    status = str(result["status"])
                    counts["reused" if status == "reused" or status.endswith("reused") else "failed" if status == "failed" else "completed"] += 1
                except HardFatal as exc:
                    hard_fatal = type(exc).__name__
                    _append_controller_issue(
                        issue_ledger,
                        {
                            "schema_version": "agentdojo_remaining_849_controller_issue/v1",
                            "recorded_at": utc_now_iso(),
                            "job_identity_sha256": job_identity_sha256(entry.job),
                            "error_type": type(exc).__name__,
                            "error_sha256": sha256_object({"type": type(exc).__name__, "message": str(exc)}),
                            "hard_fatal": True,
                            "blind_only": True,
                        },
                    )
                except Exception as exc:
                    counts["failed"] += 1
                    _append_controller_issue(
                        issue_ledger,
                        {
                            "schema_version": "agentdojo_remaining_849_controller_issue/v1",
                            "recorded_at": utc_now_iso(),
                            "job_identity_sha256": job_identity_sha256(entry.job),
                            "error_type": type(exc).__name__,
                            "error_sha256": sha256_object({"type": type(exc).__name__, "message": str(exc)}),
                            "hard_fatal": type(exc).__name__ in HARD_FATAL_ERROR_TYPES,
                            "blind_only": True,
                        },
                    )
                    if type(exc).__name__ in HARD_FATAL_ERROR_TYPES:
                        hard_fatal = type(exc).__name__
    return {
        "schema_version": "agentdojo_remaining_849_runner_result/v1",
        "status": "hard_fatal" if hard_fatal else "paused_drained" if pause.exists() and admitted < len(selected_entries) else "lane_complete",
        "vps_id": args.vps_id,
        "agent_id": args.agent,
        "workers": workers,
        "planned": len(entries),
        "selected": len(selected_entries),
        "admission_limit": admission_limit,
        "admitted": admitted,
        "terminal": sum(counts.values()),
        "counts": counts,
        "hard_fatal_error_type": hard_fatal,
        "blind_only": True,
    }


def _wait_for_barrier(
    barrier_root: Path, *, next_agent: str, pause_request: Path, poll_seconds: float
) -> bool:
    flag = barrier_root / f"allow-{next_agent.lower().replace(' ', '-')}"
    while not flag.exists() and not pause_request.exists():
        time.sleep(poll_seconds)
    if pause_request.exists():
        return False
    _regular_file(flag, "next-stage barrier")
    if stat.S_IMODE(flag.stat().st_mode) & 0o022:
        raise RunnerError("next-stage barrier is group/world writable")
    return True


def _wait_for_named_barrier(
    barrier_root: Path, *, name: str, pause_request: Path, poll_seconds: float
) -> bool:
    flag = barrier_root / name
    while not flag.exists() and not pause_request.exists():
        time.sleep(poll_seconds)
    if pause_request.exists():
        return False
    _regular_file(flag, "campaign barrier")
    if stat.S_IMODE(flag.stat().st_mode) & 0o022:
        raise RunnerError("campaign barrier is group/world writable")
    return True


def run_campaign(args: argparse.Namespace) -> dict[str, Any]:
    agents = list(args.agent)
    authorizations = list(args.stage_authorization)
    if len(agents) != len(authorizations):
        raise RunnerError("each agent lane requires exactly one stage authorization")
    if agents != list(AGENTS[: len(agents)]):
        raise RunnerError("agent lanes must be an A->B->C prefix")
    barrier_root = Path(args.barrier_root).resolve()
    barrier_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    results: list[dict[str, Any]] = []
    validation_result: dict[str, Any] | None = None
    for index, (agent_id, authorization) in enumerate(zip(agents, authorizations)):
        lane_args = copy.copy(args)
        lane_args.agent = agent_id
        lane_args.stage_authorization = authorization
        lane_args.max_admissions = args.max_admissions
        if index == 0 and args.validation_admissions is not None:
            validation_args = copy.copy(lane_args)
            validation_args.max_admissions = int(args.validation_admissions)
            validation_args.max_workers = int(args.validation_workers)
            if args.validation_issue_ledger is None:
                raise RunnerError(
                    "validation mode requires a separate validation issue ledger"
                )
            validation_args.issue_ledger = args.validation_issue_ledger
            validation_result = run_lane(validation_args)
            validation_result["mode"] = "validation"
            validation_counts = dict(validation_result.get("counts") or {})
            validation_selected = int(validation_result.get("selected") or 0)
            validation_terminal = int(validation_result.get("terminal") or 0)
            validation_passed = (
                validation_result.get("status") == "lane_complete"
                and validation_selected > 0
                and int(validation_counts.get("failed") or 0) == 0
                and validation_terminal == validation_selected
                and (
                    int(validation_counts.get("completed") or 0)
                    + int(validation_counts.get("reused") or 0)
                    == validation_selected
                )
            )
            validation_result["validation_passed"] = validation_passed
            if not validation_passed:
                validation_result["status"] = "validation_failed"
            print(
                json.dumps(validation_result, separators=(",", ":"), sort_keys=True),
                flush=True,
            )
            if not validation_passed:
                results.append(validation_result)
                # Keep the controller identity alive for the independent blind
                # monitors until the operator records a pause or explicitly
                # releases the failed-validation hold.  No new job is admitted.
                stop = barrier_root / "stop-controller"
                pause = Path(args.pause_request).resolve()
                while not stop.exists() and not pause.exists():
                    time.sleep(float(args.barrier_poll_seconds))
                break
            if not _wait_for_named_barrier(
                barrier_root,
                name="resume-agent-a",
                pause_request=Path(args.pause_request).resolve(),
                poll_seconds=float(args.barrier_poll_seconds),
            ):
                results.append(validation_result)
                break
        result = run_lane(lane_args)
        results.append(result)
        print(json.dumps(result, separators=(",", ":"), sort_keys=True), flush=True)
        if result["status"] != "lane_complete":
            break
        if index + 1 < len(agents) and not _wait_for_barrier(
            barrier_root,
            next_agent=agents[index + 1],
            pause_request=Path(args.pause_request).resolve(),
            poll_seconds=float(args.barrier_poll_seconds),
        ):
            break
    all_complete = len(results) == len(agents) and all(
        result["status"] == "lane_complete" for result in results
    )
    if all_complete and args.hold_after_final:
        stop = barrier_root / "stop-controller"
        pause = Path(args.pause_request).resolve()
        while not stop.exists() and not pause.exists():
            time.sleep(float(args.barrier_poll_seconds))
    return {
        "schema_version": "agentdojo_remaining_849_campaign_runner_result/v1",
        "status": (
            "campaign_complete_held_and_released"
            if all_complete
            else str(results[-1]["status"] if results else "hard_fatal")
        ),
        "vps_id": args.vps_id,
        "lane_count": len(results),
        "lane_statuses": [str(result["status"]) for result in results],
        "validation_status": (
            None if validation_result is None else str(validation_result["status"])
        ),
        "blind_only": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-plan-index", type=Path, required=True)
    parser.add_argument("--vps-id", choices=("vps1", "vps2"), required=True)
    parser.add_argument("--agent", choices=AGENTS, action="append", required=True)
    parser.add_argument("--infra-config", type=Path, required=True)
    parser.add_argument("--agents-config", type=Path, required=True)
    parser.add_argument("--source-bundle", type=Path, required=True)
    parser.add_argument(
        "--stage-authorization", type=Path, action="append", required=True
    )
    parser.add_argument("--pause-request", type=Path, required=True)
    parser.add_argument("--issue-ledger", type=Path, required=True)
    parser.add_argument("--controller-identity", type=Path, required=True)
    parser.add_argument("--max-workers", type=int)
    parser.add_argument("--max-admissions", type=int)
    parser.add_argument(
        "--repository-commit-hash",
        help=(
            "normalized 64-hex deployed source commit hash used when the synchronized "
            "VPS tree intentionally omits VCS metadata"
        ),
    )
    parser.add_argument(
        "--wait-for-pause-release",
        action="store_true",
        help=(
            "publish controller identity, then wait without admissions until the "
            "operator removes the existing pause request"
        ),
    )
    parser.add_argument(
        "--validation-admissions",
        "--initial-validation-size",
        dest="validation_admissions",
        type=int,
    )
    parser.add_argument("--validation-workers", type=int, default=4)
    parser.add_argument("--validation-issue-ledger", type=Path)
    parser.add_argument("--barrier-root", type=Path, required=True)
    parser.add_argument("--barrier-poll-seconds", type=float, default=5.0)
    parser.add_argument("--hold-after-final", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_campaign(args)
    except Exception as exc:
        result = {
            "schema_version": "agentdojo_remaining_849_runner_result/v1",
            "status": "hard_fatal",
            "error_type": type(exc).__name__,
            "error_sha256": sha256_object({"type": type(exc).__name__, "message": str(exc)}),
            "blind_only": True,
        }
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 2
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 2 if result["status"] == "hard_fatal" else 3 if result["status"] == "paused_drained" else 0


if __name__ == "__main__":
    raise SystemExit(main())
