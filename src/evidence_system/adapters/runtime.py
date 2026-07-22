"""Shared Step 8 runtime helpers for remote smoke execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import threading
import time
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.dotenv import load_project_dotenv
from evidence_system.core.hashing import (
    sha256_bytes,
    sha256_file,
    sha256_object,
    sha256_path,
)
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object
from evidence_system.llm.cost import compute_cost, normalize_token_usage
from evidence_system.llm.logging import LLMCallLogger, make_llm_call_record
from evidence_system.llm.openrouter_client import load_role_config

if TYPE_CHECKING:
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


DEFAULT_SYNC_PATHS = (
    "src/evidence_system",
    "experiments/smoke",
    "experiments/official_splits",
    "experiments/step20/webarena_verified/jobs/full",
    "configs/infra.yaml",
)
_SYNC_LOCK = threading.Lock()
_SYNCED_SUPPORT_KEYS: set[tuple[str, str, tuple[str, ...], bool, bool]] = set()
_TRANSIENT_SSH_ERRORS = (
    "Connection closed by",
    "Connection reset by",
    "kex_exchange_identification",
    "Broken pipe",
    "Connection timed out",
    "Operation timed out",
)
_RESULT_NAMESPACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FORMAL_JOB_LAUNCH_MARKER = "formal_job_launch_intent.json"
FORMAL_JOB_STARTED_MARKER = "formal_job_started.json"
FORMAL_JOB_WORKER_SUCCESS_MARKER = "formal_worker_success.json"
FORMAL_JOB_COMPLETION_MARKER = "formal_job_completion.json"
FORMAL_JOB_MARKER_NAMES = frozenset(
    {
        FORMAL_JOB_LAUNCH_MARKER,
        FORMAL_JOB_STARTED_MARKER,
        FORMAL_JOB_WORKER_SUCCESS_MARKER,
        FORMAL_JOB_COMPLETION_MARKER,
    }
)


class AdapterRuntimeError(RuntimeError):
    """Raised when Step 8 remote execution or artifact capture fails."""


@dataclass(frozen=True)
class SealedRemoteCommandResult:
    """Content-free result from a command whose streams stay on the VPS."""

    returncode: int
    outcome: str
    timed_out: bool
    group_gone: bool
    session_id: str
    boot_changed: bool = False


@dataclass(frozen=True)
class SmokeExecutionContext:
    manifest_path: Path
    manifest_hash: str
    source_bundle_path: Path
    source_bundle_hash: str
    official_split_hash: str
    agents_config_path: Path
    dotenv_path: Path


@dataclass(frozen=True)
class JobPaths:
    root: Path
    native_run_dir: Path
    logs_dir: Path
    stdout_log: Path
    stderr_log: Path
    llm_dir: Path
    llm_jsonl: Path
    raw_run_path: Path
    artifact_manifest_path: Path
    environment_path: Path
    failure_record_path: Path


@dataclass(frozen=True)
class ArtifactDescriptor:
    local_path: Path
    artifact_type: str
    producer_role: str
    producer_name: str
    producer_version: str
    official_runner: bool
    official_evaluator: bool
    evaluator_name: str | None = None
    evaluator_version: str | None = None
    artifact_contract_requirement_ids: tuple[str, ...] = ()
    visibility: str = "access_controlled"
    redaction_status: str = "not_needed"
    verified_evaluator_output_object_hash: str | None = None


def formal_job_binding_sha256(job: Mapping[str, Any]) -> str:
    """Bind a remote formal marker to the complete immutable job payload."""

    return sha256_object(dict(job))


def formal_job_file_sha256(job: Mapping[str, Any]) -> str:
    """Hash the exact sorted/indented bytes used by the immutable job writer."""

    encoded = (
        json.dumps(dict(job), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return sha256_bytes(encoded)


def formal_native_tree_inventory(root: str | Path) -> list[dict[str, str]]:
    """Return the marker-excluded formal native-tree inventory.

    The completion marker commits to the worker-produced evidence tree, not to
    the three controller/worker lifecycle markers.  Symlinks are rejected so a
    later read cannot be redirected outside the job namespace.
    """

    resolved = Path(root).absolute()
    try:
        root_info = os.lstat(resolved)
    except OSError as exc:
        raise AdapterRuntimeError(
            "formal native result root cannot be inspected"
        ) from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise AdapterRuntimeError("formal native result root must be a regular directory")
    inventory: list[dict[str, str]] = []
    for path in sorted(resolved.rglob("*")):
        try:
            info = os.lstat(path)
        except OSError as exc:
            raise AdapterRuntimeError(
                f"formal native result tree entry cannot be inspected: {path}"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise AdapterRuntimeError(
                f"formal native result tree contains a symlink: {path}"
            )
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise AdapterRuntimeError(
                f"formal native result tree contains a special inode: {path}"
            )
        if info.st_nlink != 1:
            raise AdapterRuntimeError(
                f"formal native result tree contains a hard-linked file: {path}"
            )
        try:
            relative_path = path.relative_to(resolved)
        except ValueError as exc:  # pragma: no cover - Path.rglob invariant
            raise AdapterRuntimeError(
                "formal native result tree entry escapes its root"
            ) from exc
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise AdapterRuntimeError("formal native result tree entry escapes its root")
        relative = relative_path.as_posix()
        if relative in FORMAL_JOB_MARKER_NAMES:
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            raise AdapterRuntimeError(
                "formal native result tree contains an untracked Python cache artifact"
            )
        inventory.append({"path": relative, "sha256": sha256_file(path)})
    return inventory


def formal_native_tree_sha256(root: str | Path) -> str:
    """Hash the immutable worker evidence inventory committed by its marker."""

    return sha256_object(formal_native_tree_inventory(root))


def formal_native_tree_total_bytes(root: str | Path) -> int:
    """Count marker-excluded evidence bytes without exposing the inventory."""

    resolved = Path(root)
    inventory = formal_native_tree_inventory(resolved)
    return sum((resolved / item["path"]).stat().st_size for item in inventory)


def build_smoke_execution_context(
    *,
    manifest_path: str | Path,
    manifest_hash: str,
    source_bundle_path: str | Path,
    source_bundle_hash: str,
    official_split_hash: str,
    agents_config_path: str | Path,
    dotenv_path: str | Path,
) -> SmokeExecutionContext:
    return SmokeExecutionContext(
        manifest_path=resolve_repo_path(manifest_path),
        manifest_hash=manifest_hash,
        source_bundle_path=resolve_repo_path(source_bundle_path),
        source_bundle_hash=source_bundle_hash,
        official_split_hash=official_split_hash,
        agents_config_path=resolve_repo_path(agents_config_path),
        dotenv_path=resolve_repo_path(dotenv_path),
    )


def normalize_result_namespace(value: Any) -> str | None:
    """Validate an optional result namespace without silently rewriting it.

    Result namespaces become filesystem path components on both the controller
    and benchmark host.  Rejecting unsafe values (rather than slugifying them)
    prevents two distinct run-set identifiers from aliasing the same directory.
    """

    if value is None:
        return None
    namespace = str(value)
    if not _RESULT_NAMESPACE_RE.fullmatch(namespace):
        raise ValueError(
            "result_namespace must match "
            "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
        )
    return namespace


def job_result_relative_dir(job: Mapping[str, Any]) -> Path:
    """Return a job's result directory relative to the repository root.

    Jobs without ``result_namespace`` retain the historical path exactly.
    Namespaced jobs are rooted below ``results/namespaces`` so that even a
    namespace named ``full`` cannot alias ``results/full``.
    """

    base = Path("results")
    namespace = normalize_result_namespace(job.get("result_namespace"))
    if namespace is not None:
        base = base / "namespaces" / namespace
    return (
        base
        / str(job.get("phase") or "smoke")
        / str(job["domain"])
        / str(job["job_id"])
    )


def remote_job_result_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    """Return the controller-equivalent result directory on a benchmark host."""

    return f"{target.remote_workdir.rstrip('/')}/{job_result_relative_dir(job).as_posix()}"


def build_job_paths(job: Mapping[str, Any]) -> JobPaths:
    root = resolve_repo_path(job_result_relative_dir(job) / "adapter")
    native_run_dir = root / "native_run"
    logs_dir = root / "logs"
    llm_dir = root / "llm_calls"
    native_run_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    llm_dir.mkdir(parents=True, exist_ok=True)
    return JobPaths(
        root=root,
        native_run_dir=native_run_dir,
        logs_dir=logs_dir,
        stdout_log=logs_dir / "stdout.log",
        stderr_log=logs_dir / "stderr.log",
        llm_dir=llm_dir,
        llm_jsonl=llm_dir / "calls.jsonl",
        raw_run_path=root / "raw_run.json",
        artifact_manifest_path=root / "artifact_manifest.json",
        environment_path=root / "environment.json",
        failure_record_path=root / "failure_record.json",
    )


def sync_repo_support_files(
    target: "InfraBenchmarkTarget",
    *,
    paths: Sequence[str | Path] = DEFAULT_SYNC_PATHS,
    include_dotenv: bool = True,
    delete_directories: bool = False,
    timeout_seconds: float | None = None,
    transient_retry_attempts: int = 4,
) -> None:
    sync_items = tuple(Path(path) for path in paths)
    sync_key = (
        target.machine_id,
        target.remote_workdir,
        tuple(path.as_posix() for path in sync_items),
        include_dotenv,
        delete_directories,
    )
    with _SYNC_LOCK:
        if sync_key in _SYNCED_SUPPORT_KEYS:
            return
        resolved_items = list(sync_items)
        if include_dotenv and (repo_root() / ".env").exists():
            resolved_items.append(Path(".env"))
        for relative in resolved_items:
            local_path = resolve_repo_path(relative)
            if not local_path.exists():
                continue
            remote_parent = f"{target.remote_workdir}/{relative.parent.as_posix()}" if relative.parent.as_posix() != "." else target.remote_workdir
            ensure_remote_directory(target, remote_parent)
            rsync_argv = [
                "rsync",
                "-az",
                "--exclude",
                "__pycache__/",
                "--exclude",
                "*.pyc",
                "-e",
                _ssh_transport(target),
                str(local_path),
                f"{_ssh_target(target)}:{remote_parent}/",
            ]
            if delete_directories and local_path.is_dir():
                rsync_argv.insert(2, "--delete")
            _run_subprocess(
                rsync_argv,
                timeout_seconds=timeout_seconds,
                transient_retry_attempts=transient_retry_attempts,
            )
        _SYNCED_SUPPORT_KEYS.add(sync_key)


def ensure_remote_directory(target: "InfraBenchmarkTarget", remote_dir: str) -> None:
    command = f"mkdir -p {shlex.quote(remote_dir)}"
    completed = _run_subprocess(_ssh_argv(target, command), check=False)
    if completed.returncode != 0:
        raise AdapterRuntimeError(f"failed to create remote directory {remote_dir}: {completed.stderr.strip()}")


def run_remote_command(
    target: "InfraBenchmarkTarget",
    command: str,
    *,
    stdout_path: str | Path,
    stderr_path: str | Path,
    stdin_text: str | None = None,
    timeout_seconds: float | None = None,
    transient_retry_attempts: int = 4,
) -> subprocess.CompletedProcess[str]:
    completed = _run_subprocess(
        _ssh_argv(target, command),
        check=False,
        capture_output=True,
        input_text=stdin_text,
        timeout_seconds=timeout_seconds,
        transient_retry_attempts=transient_retry_attempts,
    )
    _write_text(stdout_path, completed.stdout or "")
    _write_text(stderr_path, completed.stderr or "")
    return completed


def run_remote_blind_command(
    target: "InfraBenchmarkTarget",
    command: str,
    *,
    timeout_seconds: float | None = None,
    transient_retry_attempts: int = 4,
    maximum_stdout_bytes: int = 131_072,
    maximum_stderr_bytes: int = 16_384,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a control-plane command without writing its blind output locally.

    Callers must parse the returned output as a fixed control envelope.  This
    helper is not suitable for benchmark workers or any command that can emit
    prompts, responses, trajectories, evaluator values, or native logs.
    """

    completed = _run_subprocess(
        _ssh_argv(target, command),
        check=False,
        capture_output=True,
        input_text=stdin_text,
        timeout_seconds=timeout_seconds,
        transient_retry_attempts=transient_retry_attempts,
    )
    if len((completed.stdout or "").encode("utf-8")) > maximum_stdout_bytes:
        raise AdapterRuntimeError("blind remote command exceeded its stdout envelope")
    if len((completed.stderr or "").encode("utf-8")) > maximum_stderr_bytes:
        raise AdapterRuntimeError("blind remote command exceeded its stderr envelope")
    return completed


def run_remote_sealed_command(
    target: "InfraBenchmarkTarget",
    command: str,
    *,
    sealed_job_root: str,
    stage_id: str,
    session_id: str,
    job_binding_sha256: str,
    stage_authorization_sha256: str,
    formal_timeout_seconds: int,
    kill_grace_seconds: int,
) -> SealedRemoteCommandResult:
    """Create-once a detached VPS supervisor, then poll only blind state."""

    root_path = Path(sealed_job_root)
    if not root_path.is_absolute() or "\n" in sealed_job_root:
        raise AdapterRuntimeError("sealed formal job root must be an absolute path")
    _validate_digest(job_binding_sha256, "formal job binding")
    _validate_digest(stage_authorization_sha256, "formal stage authorization")
    if not session_id.startswith("session-") or not stage_id:
        raise AdapterRuntimeError("formal supervisor stage/session is invalid")
    if not 1 <= int(formal_timeout_seconds) <= 86_400 or not 1 <= int(
        kill_grace_seconds
    ) <= 300:
        raise AdapterRuntimeError("formal supervisor timeout policy is invalid")
    launch_command = _formal_supervisor_command(
        target,
        "launch",
        sealed_job_root=sealed_job_root,
        stage_id=stage_id,
        session_id=session_id,
        job_binding_sha256=job_binding_sha256,
        stage_authorization_sha256=stage_authorization_sha256,
        formal_timeout_seconds=formal_timeout_seconds,
        kill_grace_seconds=kill_grace_seconds,
    )
    # Never replay launch.  Even a transport-level unknown outcome is reconciled
    # exclusively through the create-once remote claim and read-only status.
    launched = run_remote_blind_command(
        target,
        launch_command,
        stdin_text=command,
        timeout_seconds=30,
        transient_retry_attempts=1,
        maximum_stdout_bytes=2048,
        maximum_stderr_bytes=4096,
    )
    if launched.returncode == 0:
        if launched.stderr:
            raise AdapterRuntimeError("formal supervisor launch emitted stderr")
        _parse_formal_supervisor_result(
            launched.stdout or "", expected_session_id=session_id
        )
    return reconcile_remote_sealed_command(
        target,
        sealed_job_root=sealed_job_root,
        session_id=session_id,
        maximum_wait_seconds=(
            int(formal_timeout_seconds) + int(kill_grace_seconds) + 300
        ),
    )


def reconcile_remote_sealed_command(
    target: "InfraBenchmarkTarget",
    *,
    sealed_job_root: str,
    session_id: str,
    maximum_wait_seconds: int,
) -> SealedRemoteCommandResult:
    """Read-only reconciliation; safe after controller restart or SSH loss."""

    deadline = time.monotonic() + int(maximum_wait_seconds)
    last_transport_error: str | None = None
    while time.monotonic() < deadline:
        status_command = _formal_supervisor_command(
            target,
            "status",
            sealed_job_root=sealed_job_root,
            session_id=session_id,
        )
        observed = run_remote_blind_command(
            target,
            status_command,
            timeout_seconds=45,
            transient_retry_attempts=4,
            maximum_stdout_bytes=2048,
            maximum_stderr_bytes=2048,
        )
        if observed.returncode != 0:
            last_transport_error = f"status_exit={observed.returncode}"
            time.sleep(1.0)
            continue
        if observed.stderr:
            raise AdapterRuntimeError("formal supervisor status emitted stderr")
        payload = _parse_formal_supervisor_result(
            observed.stdout or "", expected_session_id=session_id
        )
        status = str(payload["status"])
        if status == "exited":
            return SealedRemoteCommandResult(
                returncode=int(payload["exit_code"]),
                outcome=str(payload["outcome"]),
                timed_out=bool(payload["timed_out"]),
                group_gone=bool(payload["group_gone"]),
                session_id=session_id,
            )
        if status == "boot_changed":
            return SealedRemoteCommandResult(
                returncode=125,
                outcome="boot_changed",
                timed_out=False,
                group_gone=False,
                session_id=session_id,
                boot_changed=True,
            )
        if status in {"identity_conflict", "exit_receipt_missing"}:
            return SealedRemoteCommandResult(
                returncode=125,
                outcome=status,
                timed_out=False,
                group_gone=False,
                session_id=session_id,
            )
        if status not in {"running", "launch_pending", "bootstrapping"}:
            raise AdapterRuntimeError(
                f"formal supervisor entered unschedulable blind state: {status}"
            )
        time.sleep(1.0)
    raise AdapterRuntimeError(
        "formal supervisor reconciliation exceeded its controller wait bound"
        + (f" ({last_transport_error})" if last_transport_error else "")
    )


def recover_remote_sealed_after_reboot(
    target: "InfraBenchmarkTarget",
    *,
    sealed_job_root: str,
    session_id: str,
) -> SealedRemoteCommandResult:
    """Create a separate no-signal receipt only after a proven host reboot."""

    command = _formal_supervisor_command(
        target,
        "recover-reboot",
        sealed_job_root=sealed_job_root,
        session_id=session_id,
    )
    completed = run_remote_blind_command(
        target,
        command,
        timeout_seconds=45,
        transient_retry_attempts=1,
        maximum_stdout_bytes=2048,
        maximum_stderr_bytes=0,
    )
    if completed.returncode != 0 or completed.stderr:
        raise AdapterRuntimeError("formal reboot recovery failed closed")
    payload = _parse_formal_supervisor_result(
        completed.stdout or "", expected_session_id=session_id
    )
    if payload.get("status") != "exited" or payload.get("outcome") != "boot_changed":
        raise AdapterRuntimeError("formal reboot recovery receipt differs")
    return SealedRemoteCommandResult(
        returncode=int(payload["exit_code"]),
        outcome="boot_changed",
        timed_out=False,
        group_gone=bool(payload["group_gone"]),
        session_id=session_id,
        boot_changed=True,
    )


def _formal_supervisor_command(
    target: "InfraBenchmarkTarget",
    mode: str,
    *,
    sealed_job_root: str,
    session_id: str,
    stage_id: str | None = None,
    job_binding_sha256: str | None = None,
    stage_authorization_sha256: str | None = None,
    formal_timeout_seconds: int | None = None,
    kill_grace_seconds: int | None = None,
) -> str:
    install_dir = str(
        target.benchmark_config.get("install_dir") or target.runner_workdir
    )
    python_bin = f"{install_dir.rstrip('/')}/.venv/bin/python"
    argv = [
        shlex.quote(python_bin),
        "-m",
        "evidence_system.adapters.agentdojo_formal_supervisor",
        mode,
        "--attempt-root",
        shlex.quote(sealed_job_root),
        "--session-id",
        shlex.quote(session_id),
    ]
    if mode == "launch":
        argv.extend(
            [
                "--stage-id", shlex.quote(str(stage_id)),
                "--job-binding-sha256", shlex.quote(str(job_binding_sha256)),
                "--stage-authorization-sha256",
                shlex.quote(str(stage_authorization_sha256)),
                "--timeout-seconds", str(int(formal_timeout_seconds or 0)),
                "--kill-grace-seconds", str(int(kill_grace_seconds or 0)),
            ]
        )
    return (
        f"cd {shlex.quote(target.remote_workdir)} && "
        f"PYTHONPATH={shlex.quote(f'{target.remote_workdir}/src')} "
        + " ".join(argv)
    )


def _parse_formal_supervisor_result(
    value: str, *, expected_session_id: str
) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise AdapterRuntimeError("formal supervisor returned invalid blind JSON") from exc
    if not isinstance(payload, dict):
        raise AdapterRuntimeError("formal supervisor blind result is not an object")
    base = {"schema_version", "status", "session_id", "blind_only"}
    status = str(payload.get("status") or "")
    expected = set(base)
    if status == "exited":
        expected.update({"exit_code", "outcome", "timed_out", "group_gone"})
    elif status in {"running", "exit_receipt_missing", "bootstrapping"}:
        expected.add("deadline_boottime_seconds")
    if set(payload) != expected or payload.get("schema_version") != (
        "agentdojo_formal_supervisor_result/v1"
    ):
        raise AdapterRuntimeError("formal supervisor blind result fields differ")
    if payload.get("session_id") != expected_session_id or payload.get("blind_only") is not True:
        raise AdapterRuntimeError("formal supervisor blind result binding differs")
    return payload


def _validate_digest(value: str, label: str) -> None:
    normalized = str(value).removeprefix("sha256:")
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise AdapterRuntimeError(f"{label} is not a lowercase SHA-256")


def rsync_remote_tree(
    target: "InfraBenchmarkTarget",
    remote_path: str,
    local_path: str | Path,
    *,
    timeout_seconds: float | None = None,
    transient_retry_attempts: int = 4,
) -> None:
    resolved_local = resolve_repo_path(local_path)
    resolved_local.mkdir(parents=True, exist_ok=True)
    _run_subprocess(
        [
            "rsync",
            "-az",
            "-e",
            _ssh_transport(target),
            f"{_ssh_target(target)}:{remote_path.rstrip('/')}/",
            f"{resolved_local}/",
        ],
        timeout_seconds=timeout_seconds,
        transient_retry_attempts=transient_retry_attempts,
    )


def rsync_local_file_to_remote(
    target: "InfraBenchmarkTarget",
    local_path: str | Path,
    remote_path: str,
    *,
    timeout_seconds: float | None = None,
    transient_retry_attempts: int = 4,
) -> None:
    """Upload one regular control-plane file to an explicit remote path."""

    resolved_local = resolve_repo_path(local_path)
    if not resolved_local.is_file() or resolved_local.is_symlink():
        raise AdapterRuntimeError(
            f"local control-plane upload is missing or unsafe: {resolved_local}"
        )
    ensure_remote_directory(target, str(Path(remote_path).parent))
    _run_subprocess(
        [
            "rsync",
            "-az",
            "-e",
            _ssh_transport(target),
            str(resolved_local),
            f"{_ssh_target(target)}:{remote_path}",
        ],
        timeout_seconds=timeout_seconds,
        transient_retry_attempts=transient_retry_attempts,
    )


def rsync_remote_file(
    target: "InfraBenchmarkTarget",
    remote_path: str,
    local_path: str | Path,
    *,
    timeout_seconds: float | None = None,
    transient_retry_attempts: int = 4,
) -> None:
    """Download one explicitly approved control-plane receipt."""

    resolved_local = resolve_repo_path(local_path)
    resolved_local.parent.mkdir(parents=True, exist_ok=True)
    _run_subprocess(
        [
            "rsync",
            "-az",
            "-e",
            _ssh_transport(target),
            f"{_ssh_target(target)}:{remote_path}",
            str(resolved_local),
        ],
        timeout_seconds=timeout_seconds,
        transient_retry_attempts=transient_retry_attempts,
    )
    if not resolved_local.is_file() or resolved_local.is_symlink():
        raise AdapterRuntimeError(
            f"remote control-plane receipt was not fetched safely: {remote_path}"
        )


def write_llm_call_logs(
    *,
    events: Sequence[Mapping[str, Any]],
    job: Mapping[str, Any],
    context: SmokeExecutionContext,
    output_dir: str | Path,
) -> tuple[str | None, str | None]:
    if not events:
        return None, None
    resolved_output_dir = resolve_repo_path(output_dir)
    if resolved_output_dir.exists():
        shutil.rmtree(resolved_output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    role_config = load_role_config(str(job["agent_id"]), agents_config_path=context.agents_config_path, formal=False)
    load_project_dotenv()
    logger = LLMCallLogger.from_dir(
        resolved_output_dir,
        secret_values=(os.environ.get(role_config.api_key_env),),
    )
    for index, event in enumerate(events, start=1):
        request_payload = dict(event.get("request_payload") or event.get("request") or {})
        response_payload = event.get("response_payload") or event.get("response")
        response_metadata = dict(event.get("response_metadata") or {})
        if isinstance(response_payload, Mapping) and "provider_response" not in response_metadata:
            response_metadata["provider_response"] = dict(response_payload)
        if event.get("error_type"):
            response_metadata.setdefault("error_type", str(event["error_type"]))
        if event.get("error_message"):
            response_metadata.setdefault("error_message", str(event["error_message"]))
        response_metadata.setdefault("transport", str(event.get("transport") or "openrouter"))
        response_metadata.setdefault("status", str(event.get("status") or ("error" if event.get("error_message") else "success")))
        if isinstance(response_payload, Mapping):
            response_metadata.setdefault("provider_model", response_payload.get("model"))
        token_usage = dict(event.get("token_usage") or _token_usage_from_payload(response_payload))
        cost = dict(
            event.get("cost")
            or compute_cost(
                response_payload if isinstance(response_payload, Mapping) else None,
                token_usage,
                pricing_table=role_config.pricing_table if role_config.cost_tracking else None,
            )
        )
        prompt_hash = str(event.get("prompt_hash") or sha256_object(request_payload))
        request_timestamp = str(event.get("request_timestamp") or event.get("timestamp") or utc_now_iso())
        response_timestamp = _response_timestamp_after_request(
            request_timestamp,
            str(event.get("response_timestamp") or event.get("timestamp") or utc_now_iso()),
        )
        record = make_llm_call_record(
            call_id=str(event.get("call_id") or f"{job['job_id']}-call-{index:04d}"),
            domain=str(job["domain"]),
            phase=str(job["phase"]),
            experiment_type=str(job["experiment_type"]),
            priority=str(job["priority"]),
            agent_id_or_role=role_config.role,
            provider=role_config.provider,
            model=str(request_payload.get("model") or role_config.model),
            model_version=str(event.get("model_version") or (response_payload.get("model") if isinstance(response_payload, Mapping) else role_config.model_version) or role_config.model_version),
            api_key_env=role_config.api_key_env,
            prompt_version=str(event.get("prompt_version") or role_config.prompt_version),
            prompt_hash=prompt_hash,
            temperature=float(request_payload.get("temperature", role_config.temperature)),
            max_tokens=int(request_payload.get("max_tokens", role_config.max_tokens)),
            timeout_seconds=role_config.timeout_seconds,
            retry_index=int(event.get("retry_index") or 0),
            rate_limit_bucket=role_config.rate_limit_bucket,
            request_timestamp=request_timestamp,
            response_timestamp=response_timestamp,
            response_metadata=response_metadata,
            token_usage=token_usage,
            cost=cost,
            config_hash=role_config.config_hash,
            manifest_hash=context.manifest_hash,
            run_id=str(job["run_id"]),
            record_slot_id=str(job["record_slot_id"]),
            attempt_id=str(job["attempt_id"]),
            case_unit_id=str(job["case_unit_id"]),
            task_id=str(job["task_id"]),
            evidence_contract_id=str(job["evidence_contract_id"]),
            contract_version=str(job["evidence_contract_version"]),
            source_bundle_hash=context.source_bundle_hash,
        )
        logger.log(record)
    return _repo_relative(resolved_output_dir / "calls.jsonl"), sha256_file(resolved_output_dir / "calls.jsonl")


def _response_timestamp_after_request(request_timestamp: str, response_timestamp: str) -> str:
    try:
        request_dt = datetime.fromisoformat(request_timestamp.replace("Z", "+00:00"))
        response_dt = datetime.fromisoformat(response_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return response_timestamp
    if response_dt > request_dt:
        return response_timestamp
    return (request_dt + timedelta(microseconds=1)).isoformat()


def build_artifact_manifest(
    *,
    job: Mapping[str, Any],
    context: SmokeExecutionContext,
    target: "InfraBenchmarkTarget",
    descriptors: Sequence[ArtifactDescriptor],
    producer_command: str,
    started_at: str,
    output_path: str | Path,
    environment_hash: str,
    declared_path_mapper: Callable[[Path], str] | None = None,
) -> tuple[dict[str, Any], Path, str]:
    producer_command_hash = sha256_object({"runner_command": producer_command})
    artifacts = [
        _artifact_entry(
            descriptor=descriptor,
            producer_command_hash=producer_command_hash,
            started_at=started_at,
            environment_hash=environment_hash,
            source_bundle_hash=context.source_bundle_hash,
            official_split_hash=context.official_split_hash,
            declared_path=(
                declared_path_mapper(descriptor.local_path)
                if declared_path_mapper is not None
                else None
            ),
        )
        for descriptor in descriptors
    ]
    payload = {
        "schema_version": "artifact_manifest/v1",
        "domain": str(job["domain"]),
        "domain_display_name": str(job["domain_display_name"]),
        "benchmark_name": str(job["benchmark_name"]),
        "case_unit_id": str(job["case_unit_id"]),
        "task_id": str(job["task_id"]),
        "record_slot_id": str(job["record_slot_id"]),
        "run_id": str(job["run_id"]),
        "attempt_id": str(job["attempt_id"]),
        "final_attempt": bool(job["final_attempt"]),
        "seed": int(job["seed"]),
        "agent_id": str(job["agent_id"]),
        "phase": str(job["phase"]),
        "experiment_type": str(job["experiment_type"]),
        "priority": str(job["priority"]),
        "evidence_contract_id": str(job["evidence_contract_id"]),
        "evidence_contract_version": str(job["evidence_contract_version"]),
        "evidence_contract_hash": str(job["evidence_contract_hash"]),
        "source_bundle_hash": context.source_bundle_hash,
        "official_splits_hash": context.official_split_hash,
        "environment_hash": environment_hash,
        "supersedes_manifest_path": None,
        "artifacts": artifacts,
    }
    if job.get("execution_lock_sha256") is not None:
        payload["execution_lock_sha256"] = str(job["execution_lock_sha256"])
        payload["execution_policy_sha256"] = str(job["execution_policy_sha256"])
        payload["openrouter_runtime_policy_sha256"] = str(
            job["openrouter_runtime_policy_sha256"]
        )
        payload["openrouter_runtime_policy_file_sha256"] = str(
            job["openrouter_runtime_policy_file_sha256"]
        )
    validate_object("artifact_manifest", payload, raise_on_error=True)
    written = write_json(output_path, payload)
    return payload, written, sha256_file(written)


def build_raw_run(
    *,
    job: Mapping[str, Any],
    target: "InfraBenchmarkTarget",
    artifact_manifest_path: str | Path,
    artifact_manifest_sha256: str,
    raw_run_path: str | Path,
    started_at: str,
    ended_at: str,
    status: str,
    diagnostic_status: str,
    appendix_failure_class: str,
    native_label: str | None,
    native_score: float | None,
    episode_ids: Sequence[str],
    llm_calls_log_path: str | None,
    artifact_manifest_declared_path: str | Path | None = None,
    raw_run_declared_path: str | Path | None = None,
) -> tuple[dict[str, Any], Path]:
    started_dt = _parse_iso8601(started_at)
    ended_dt = _parse_iso8601(ended_at)
    config_hash = sha256_object(
        {
            "agent_config_hash": str(job["agent_config_hash"]),
            "benchmark_config_hash": str(job["benchmark_config_hash"]),
        }
    )
    payload = {
        "schema_version": "raw_run/v1",
        "domain": str(job["domain"]),
        "domain_display_name": str(job["domain_display_name"]),
        "benchmark_name": str(job["benchmark_name"]),
        "case_unit_id": str(job["case_unit_id"]),
        "task_id": str(job["task_id"]),
        "record_slot_id": str(job["record_slot_id"]),
        "record_id": f"{job['record_slot_id']}::{job['attempt_id']}",
        "episode_ids": list(episode_ids),
        "run_id": str(job["run_id"]),
        "attempt_id": str(job["attempt_id"]),
        "final_attempt": bool(job["final_attempt"]),
        "seed": int(job["seed"]),
        "agent_id": str(job["agent_id"]),
        "phase": str(job["phase"]),
        "experiment_type": str(job["experiment_type"]),
        "priority": str(job["priority"]),
        "status": status,
        "native_label": native_label,
        "native_score": native_score,
        "native_label_used_as_decisive_evidence": False,
        "native_decisive_support": None,
        "diagnostic_status": diagnostic_status,
        "appendix_failure_class": appendix_failure_class,
        "artifact_manifest_path": _repo_relative(
            artifact_manifest_declared_path or artifact_manifest_path
        ),
        "artifact_manifest_sha256": artifact_manifest_sha256,
        "raw_source_path": _repo_relative(raw_run_declared_path or raw_run_path),
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": round((ended_dt - started_dt).total_seconds(), 6),
        "machine_id": target.machine_id,
        "git_commit_hash": current_git_commit_hash(),
        "config_hash": config_hash,
        "manifest_hash": str(job["manifest_hash"]),
        "contract_id": str(job["contract_id"]),
        "contract_version": str(job["contract_version"]),
        "contract_hash": str(job["contract_hash"]),
        "taxonomy_version": str(job["taxonomy_version"]),
        "evidence_contract_id": str(job["evidence_contract_id"]),
        "evidence_contract_version": str(job["evidence_contract_version"]),
        "evidence_contract_hash": str(job["evidence_contract_hash"]),
        "llm_calls_log_path": llm_calls_log_path,
    }
    if job.get("execution_lock_sha256") is not None:
        payload["execution_lock_sha256"] = str(job["execution_lock_sha256"])
        payload["execution_policy_sha256"] = str(job["execution_policy_sha256"])
        payload["openrouter_runtime_policy_sha256"] = str(
            job["openrouter_runtime_policy_sha256"]
        )
        payload["openrouter_runtime_policy_file_sha256"] = str(
            job["openrouter_runtime_policy_file_sha256"]
        )
    validate_object("raw_run", payload, raise_on_error=True)
    written = write_json(raw_run_path, payload)
    return payload, written


def write_environment_snapshot(
    *,
    target: "InfraBenchmarkTarget",
    job: Mapping[str, Any],
    output_path: str | Path,
    extra_fields: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    payload = {
        "machine_id": target.machine_id,
        "machine_role": target.machine_role,
        "ssh_host": target.ssh_host,
        "ssh_port": target.ssh_port,
        "remote_workdir": target.remote_workdir,
        "runner_workdir": target.runner_workdir,
        "benchmark_name": target.benchmark_name,
        "benchmark_config_hash": target.benchmark_config_hash,
        "job_id": str(job["job_id"]),
        "run_id": str(job["run_id"]),
    }
    if job.get("execution_lock_sha256") is not None:
        payload["execution_lock_sha256"] = str(job["execution_lock_sha256"])
        payload["execution_policy_sha256"] = str(job["execution_policy_sha256"])
        payload["openrouter_runtime_policy_sha256"] = str(
            job["openrouter_runtime_policy_sha256"]
        )
        payload["openrouter_runtime_policy_file_sha256"] = str(
            job["openrouter_runtime_policy_file_sha256"]
        )
    if extra_fields is not None:
        collisions = set(payload).intersection(extra_fields)
        if collisions:
            raise AdapterRuntimeError(
                f"environment extra fields collide with canonical fields: {sorted(collisions)}"
            )
        payload.update(dict(extra_fields))
    written = write_json(output_path, payload)
    return payload, sha256_file(written)


def current_git_commit_hash() -> str:
    completed = _run_subprocess(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        check=False,
        cwd=repo_root(),
    )
    if completed.returncode != 0:
        raise AdapterRuntimeError(f"failed to resolve git commit: {completed.stderr.strip()}")
    commit = completed.stdout.strip()
    return commit if len(commit) == 64 else sha256_object({"git_commit": commit})


def file_descriptor(
    local_path: str | Path,
    *,
    artifact_type: str,
    producer_role: str,
    producer_name: str,
    producer_version: str,
    official_runner: bool,
    official_evaluator: bool,
    evaluator_name: str | None = None,
    evaluator_version: str | None = None,
    artifact_contract_requirement_ids: Sequence[str] = (),
    visibility: str = "access_controlled",
    redaction_status: str = "not_needed",
) -> ArtifactDescriptor:
    path = resolve_repo_path(local_path)
    verified_hash = _verified_json_object_hash(path) if path.suffix == ".json" else None
    return ArtifactDescriptor(
        local_path=path,
        artifact_type=artifact_type,
        producer_role=producer_role,
        producer_name=producer_name,
        producer_version=producer_version,
        official_runner=official_runner,
        official_evaluator=official_evaluator,
        evaluator_name=evaluator_name,
        evaluator_version=evaluator_version,
        artifact_contract_requirement_ids=tuple(artifact_contract_requirement_ids),
        visibility=visibility,
        redaction_status=redaction_status,
        verified_evaluator_output_object_hash=verified_hash,
    )


def default_adapter_artifacts(paths: JobPaths) -> tuple[ArtifactDescriptor, ...]:
    artifacts: list[ArtifactDescriptor] = []
    if paths.environment_path.exists():
        artifacts.append(
            file_descriptor(
                paths.environment_path,
                artifact_type="file",
                producer_role="adapter",
                producer_name="step8-adapter",
                producer_version="0.1.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
    if paths.stdout_log.exists():
        artifacts.append(
            file_descriptor(
                paths.stdout_log,
                artifact_type="stdout",
                producer_role="adapter",
                producer_name="step8-adapter",
                producer_version="0.1.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
    if paths.stderr_log.exists():
        artifacts.append(
            file_descriptor(
                paths.stderr_log,
                artifact_type="stderr",
                producer_role="adapter",
                producer_name="step8-adapter",
                producer_version="0.1.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
    if paths.llm_dir.exists() and any(paths.llm_dir.iterdir()):
        artifacts.append(
            file_descriptor(
                paths.llm_dir,
                artifact_type="file",
                producer_role="adapter",
                producer_name="step8-adapter",
                producer_version="0.1.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
    if paths.llm_jsonl.exists():
        artifacts.append(
            file_descriptor(
                paths.llm_jsonl,
                artifact_type="llm_call_log",
                producer_role="adapter",
                producer_name="step8-adapter",
                producer_version="0.1.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
    return tuple(artifacts)


def _artifact_entry(
    *,
    descriptor: ArtifactDescriptor,
    producer_command_hash: str,
    started_at: str,
    environment_hash: str,
    source_bundle_hash: str,
    official_split_hash: str,
    declared_path: str | None = None,
) -> dict[str, Any]:
    created_at = _file_timestamp(descriptor.local_path)
    sha256_value, size_bytes = _path_digest_and_size(descriptor.local_path)
    return {
        "artifact_id": f"{descriptor.artifact_type}:{descriptor.local_path.stem}",
        "artifact_type": descriptor.artifact_type,
        "path": declared_path or _repo_relative(descriptor.local_path),
        "sha256": sha256_value,
        "size_bytes": size_bytes,
        "created_at": created_at,
        "producer_role": descriptor.producer_role,
        "producer_name": descriptor.producer_name,
        "producer_version": descriptor.producer_version,
        "producer_command_hash": producer_command_hash,
        "official_runner": descriptor.official_runner,
        "official_evaluator": descriptor.official_evaluator,
        "evaluator_name": descriptor.evaluator_name,
        "evaluator_version": descriptor.evaluator_version,
        "source_bundle_hash": source_bundle_hash,
        "official_splits_hash": official_split_hash,
        "environment_hash": environment_hash,
        "verified_evaluator_output_object_hash": descriptor.verified_evaluator_output_object_hash,
        "artifact_created_after_run_start": _parse_iso8601(created_at) >= _parse_iso8601(started_at),
        "artifact_contract_requirement_ids": list(descriptor.artifact_contract_requirement_ids),
        "visibility": descriptor.visibility,
        "redaction_status": descriptor.redaction_status,
    }


def _file_timestamp(path: Path) -> str:
    if path.is_dir():
        files = sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
        if files:
            latest = max(candidate.stat().st_mtime for candidate in files)
            return datetime.fromtimestamp(latest, tz=timezone.utc).replace(microsecond=0).isoformat()
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def _verified_json_object_hash(path: Path) -> str | None:
    if path.is_dir():
        return None
    try:
        loaded = load_json_or_yaml(path)
    except Exception:
        return None
    return sha256_object(loaded)


def _path_digest_and_size(path: Path) -> tuple[str, int]:
    if path.is_file():
        return sha256_file(path), path.stat().st_size
    if path.is_dir():
        files = sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
        return sha256_path(path), sum(candidate.stat().st_size for candidate in files)
    raise FileNotFoundError(path)


def _token_usage_from_payload(response_payload: Any) -> dict[str, int]:
    if isinstance(response_payload, Mapping):
        return dict(normalize_token_usage(response_payload))
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cached_prompt_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
    }


def _parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    try:
        return str(resolved.relative_to(repo_root()))
    except ValueError:
        return str(resolved)


def _ssh_target(target: "InfraBenchmarkTarget") -> str:
    return f"{target.ssh_user}@{target.ssh_host}"


def _ssh_transport(target: "InfraBenchmarkTarget") -> str:
    options = " ".join(shlex.quote(value) for value in _ssh_host_key_options(target))
    return (
        f"ssh -i {shlex.quote(target.ssh_key_path)} -p {target.ssh_port} "
        f"{options}"
    )


def _ssh_host_key_options(target: "InfraBenchmarkTarget") -> list[str]:
    known_hosts_file = str(getattr(target, "ssh_known_hosts_file", "") or "")
    expected_fingerprint = str(
        getattr(target, "ssh_host_ed25519_fingerprint", "") or ""
    )
    if not known_hosts_file and expected_fingerprint:
        from evidence_system.webarena_sites import _verified_known_hosts_file

        known_hosts_file = _verified_known_hosts_file(
            host=target.ssh_host,
            port=int(target.ssh_port),
            expected_fingerprint=expected_fingerprint,
        )
    if known_hosts_file:
        _verify_pinned_ssh_identity(
            target,
            known_hosts_file=known_hosts_file,
            expected_host_fingerprint=expected_fingerprint,
        )
    transport_liveness = [
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=30",
        "-o",
        "ServerAliveInterval=15",
        "-o",
        "ServerAliveCountMax=3",
        "-o",
        # A persistent control master inherits the capture pipes created by
        # subprocess.run().  Once a remote command exits, that inherited FD can
        # keep communicate() blocked until ControlPersist expires, leaving the
        # formal scheduler unable to observe the slot's terminal receipt.
        # Explicitly disable multiplexing rather than relying on user ssh
        # configuration so each control-plane request owns and closes its FDs.
        "ControlMaster=no",
        "-o",
        "ControlPersist=no",
        "-o",
        "HostKeyAlgorithms=ssh-ed25519",
        "-o",
        "PubkeyAcceptedAlgorithms=ssh-ed25519",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "PreferredAuthentications=publickey",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "KbdInteractiveAuthentication=no",
    ]
    if known_hosts_file:
        return [
            *transport_liveness,
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={known_hosts_file}",
            "-o",
            "GlobalKnownHostsFile=/dev/null",
        ]
    return [*transport_liveness, "-o", "StrictHostKeyChecking=no"]


def _verify_pinned_ssh_identity(
    target: "InfraBenchmarkTarget",
    *,
    known_hosts_file: str,
    expected_host_fingerprint: str,
) -> None:
    """Fail closed on host-key or controller public-key drift for every SSH."""

    known = Path(known_hosts_file)
    private_key = Path(str(target.ssh_key_path))
    public_key = Path(f"{private_key}.pub")
    for path, label in (
        (known, "known_hosts"),
        (private_key, "controller SSH private key"),
        (public_key, "controller SSH public key"),
    ):
        try:
            info = os.lstat(path)
        except OSError as exc:
            raise AdapterRuntimeError(f"{label} is missing") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise AdapterRuntimeError(f"{label} is linked, symlinked, or not regular")
    if stat.S_IMODE(os.lstat(private_key).st_mode) & 0o077:
        raise AdapterRuntimeError("controller SSH private key permissions are too broad")

    lines = [
        line.strip()
        for line in known.read_text(encoding="ascii").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(lines) != 1:
        raise AdapterRuntimeError("pinned known_hosts must contain exactly one key")
    fields = lines[0].split()
    expected_host_token = (
        str(target.ssh_host)
        if int(target.ssh_port) == 22
        else f"[{target.ssh_host}]:{int(target.ssh_port)}"
    )
    if len(fields) < 3 or fields[0] != expected_host_token or fields[1] != "ssh-ed25519":
        raise AdapterRuntimeError("pinned known_hosts endpoint/algorithm differs")
    observed_host_fingerprint = _openssh_ed25519_fingerprint(fields[1], fields[2])
    if (
        not expected_host_fingerprint
        or observed_host_fingerprint != expected_host_fingerprint
    ):
        raise AdapterRuntimeError("pinned SSH host fingerprint differs")

    public_fields = public_key.read_text(encoding="ascii").strip().split()
    if len(public_fields) < 2 or public_fields[0] != "ssh-ed25519":
        raise AdapterRuntimeError("controller SSH public key is not ED25519")
    observed_public_fingerprint = _openssh_ed25519_fingerprint(
        public_fields[0], public_fields[1]
    )
    expected_public_fingerprint = str(
        getattr(target, "ssh_public_key_fingerprint", "") or ""
    )
    if (
        not expected_public_fingerprint
        or observed_public_fingerprint != expected_public_fingerprint
    ):
        raise AdapterRuntimeError("controller SSH public-key fingerprint differs")


def _openssh_ed25519_fingerprint(algorithm: str, encoded_blob: str) -> str:
    if algorithm != "ssh-ed25519":
        raise AdapterRuntimeError("SSH key algorithm is not ED25519")
    try:
        blob = base64.b64decode(encoded_blob, validate=True)
    except ValueError as exc:
        raise AdapterRuntimeError("SSH public key encoding is invalid") from exc
    return "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode(
        "ascii"
    ).rstrip("=")


def _ssh_argv(target: "InfraBenchmarkTarget", command: str) -> list[str]:
    script = f"set -euo pipefail\n{command}"
    return [
        "ssh",
        "-i",
        target.ssh_key_path,
        "-p",
        str(target.ssh_port),
        *_ssh_host_key_options(target),
        _ssh_target(target),
        f"bash -lc {shlex.quote(script)}",
    ]


def _run_subprocess(
    argv: Sequence[str],
    *,
    cwd: str | Path | None = None,
    capture_output: bool = True,
    check: bool = True,
    input_text: str | None = None,
    timeout_seconds: float | None = None,
    transient_retry_attempts: int = 4,
) -> subprocess.CompletedProcess[str]:
    argv_list = list(argv)
    completed: subprocess.CompletedProcess[str] | None = None
    attempt_limit = max(1, int(transient_retry_attempts))
    for attempt in range(1, attempt_limit + 1):
        try:
            completed = subprocess.run(
                argv_list,
                cwd=str(cwd) if cwd is not None else None,
                check=False,
                text=True,
                capture_output=capture_output,
                input=input_text,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            timeout_marker = f"controller_subprocess_timeout_seconds={timeout_seconds}"
            stderr = f"{stderr.rstrip()}\n{timeout_marker}\n" if stderr else f"{timeout_marker}\n"
            completed = subprocess.CompletedProcess(
                argv_list,
                124,
                stdout=stdout,
                stderr=stderr,
            )
            # A timeout is terminal.  Re-executing an SSH command after its
            # outcome became unknown could duplicate a canonical benchmark run.
            break
        if (
            completed.returncode == 0
            or not _is_transient_ssh_failure(completed)
            or attempt == attempt_limit
        ):
            break
        time.sleep(min(5.0, 0.75 * attempt))
    assert completed is not None
    if check and completed.returncode != 0:
        raise AdapterRuntimeError(
            f"command failed ({' '.join(argv_list)}):\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def _is_transient_ssh_failure(completed: subprocess.CompletedProcess[str]) -> bool:
    stderr = completed.stderr or ""
    return completed.returncode != 0 and any(pattern in stderr for pattern in _TRANSIENT_SSH_ERRORS)


def _write_text(path: str | Path, text: str) -> None:
    resolved = resolve_repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text, encoding="utf-8")
