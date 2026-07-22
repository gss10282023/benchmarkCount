"""Post-exit publication and verification for sealed AgentDojo formal evidence."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
import errno
import fcntl
import grp
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

from evidence_system.adapters.agentdojo_runtime_control import job_identity_sha256
from evidence_system.adapters import agentdojo_formal_supervisor as formal_supervisor
from evidence_system.adapters.runtime import (
    ArtifactDescriptor,
    FORMAL_JOB_COMPLETION_MARKER,
    FORMAL_JOB_LAUNCH_MARKER,
    FORMAL_JOB_STARTED_MARKER,
    FORMAL_JOB_WORKER_SUCCESS_MARKER,
    SmokeExecutionContext,
    build_artifact_manifest,
    build_raw_run,
    file_descriptor,
    formal_job_binding_sha256,
    job_result_relative_dir,
    write_environment_snapshot,
)
from evidence_system.contracts.common import utc_now_iso
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.schemas import validate_object


SEALED_STREAMS = ("sealed_worker.stdout.log", "sealed_worker.stderr.log")
SUPERVISOR_STATE = "formal_supervisor_state.json"
SUPERVISOR_EXIT = "formal_supervisor_exit.json"
ATTEMPT_FAILURE = "formal_attempt_failure.json"
LIFECYCLE_FILES = frozenset(
    {
        FORMAL_JOB_LAUNCH_MARKER,
        FORMAL_JOB_STARTED_MARKER,
        FORMAL_JOB_WORKER_SUCCESS_MARKER,
        SUPERVISOR_STATE,
        SUPERVISOR_EXIT,
        ATTEMPT_FAILURE,
        formal_supervisor.SPEC,
        formal_supervisor.CLAIM,
        *SEALED_STREAMS,
    }
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operation", choices=("verify", "success", "failure"), required=True
    )
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--completion-index", type=Path, required=True)
    parser.add_argument("--failed-attempt-index", type=Path, required=True)
    parser.add_argument("--failed-archive-root", type=Path, required=True)
    parser.add_argument("--lifecycle-lock", type=Path, required=True)
    parser.add_argument("--execution-context-json", required=True)
    parser.add_argument("--stage-authorization-sha256", required=True)
    parser.add_argument("--stage-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--blind-group", required=True)
    parser.add_argument("--worker-exit-code", type=int, default=0)
    parser.add_argument(
        "--failure-category",
        choices=("worker_error", "timeout", "unknown_outcome", "boot_changed"),
        default="worker_error",
    )
    args = parser.parse_args(argv)
    job = _loads_object(args.job_json)
    execution_context = _loads_object(args.execution_context_json)
    try:
        if args.operation == "verify":
            with _exclusive_lifecycle_lock(
                args.lifecycle_lock, blind_group=args.blind_group
            ):
                if args.canonical_root.exists() or args.canonical_root.is_symlink():
                    verified = verify_canonical_job(args.canonical_root, job=job)
                    result = _success_result(verified["marker"], reused=True)
                else:
                    result = {
                        "schema_version": "agentdojo_formal_postprocessor_result/v1",
                        "status": "canonical_absent",
                        **_binding(job),
                        "blind_only": True,
                    }
        elif args.operation == "success":
            result = publish_or_verify_success(
                job=job,
                attempt_root=args.attempt_root,
                canonical_root=args.canonical_root,
                completion_index=args.completion_index,
                authorization_sha256=args.stage_authorization_sha256,
                stage_id=args.stage_id,
                session_id=args.session_id,
                blind_group=args.blind_group,
                execution_context=execution_context,
                lifecycle_lock=args.lifecycle_lock,
            )
        else:
            result = archive_failed_attempt(
                job=job,
                attempt_root=args.attempt_root,
                failed_attempt_index=args.failed_attempt_index,
                authorization_sha256=args.stage_authorization_sha256,
                stage_id=args.stage_id,
                session_id=args.session_id,
                failure_category=args.failure_category,
                worker_exit_code=args.worker_exit_code,
                blind_group=args.blind_group,
                canonical_root=args.canonical_root,
                failed_archive_root=args.failed_archive_root,
                lifecycle_lock=args.lifecycle_lock,
            )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "schema_version": "agentdojo_formal_postprocessor_result/v1",
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_sha256": sha256_object(
                        {"type": type(exc).__name__, "message": str(exc)}
                    ),
                    "blind_only": True,
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


def publish_or_verify_success(
    *,
    job: Mapping[str, Any],
    attempt_root: Path,
    canonical_root: Path,
    completion_index: Path,
    authorization_sha256: str,
    stage_id: str,
    session_id: str,
    blind_group: str,
    execution_context: Mapping[str, Any],
    lifecycle_lock: Path,
) -> dict[str, Any]:
    """Package only after process exit, then publish destination-absent."""

    _digest(authorization_sha256, "authorization_sha256")
    locked_context = _verify_execution_context(execution_context, job=job)
    canonical = Path(canonical_root)
    with _exclusive_lifecycle_lock(lifecycle_lock, blind_group=blind_group):
        if canonical.exists() or canonical.is_symlink():
            verified = verify_canonical_job(canonical, job=job)
            _append_completion_index(
                completion_index,
                marker=verified["marker"],
                canonical_root=canonical,
                blind_group=blind_group,
            )
            return _success_result(verified["marker"], reused=True)
    attempt = _regular_directory(attempt_root, "attempt root")
    _verify_supervisor_exited(attempt, session_id=session_id)
    _verify_worker_success(
        attempt,
        job=job,
        authorization_sha256=authorization_sha256,
        stage_id=stage_id,
        session_id=session_id,
    )
    episode_paths = _exact_episode_paths(attempt, job)
    attempt_inventory = _inventory(attempt, excluded={ATTEMPT_FAILURE})
    attempt_tree_sha = sha256_object(attempt_inventory)
    attempt_total_bytes = _inventory_bytes(attempt, attempt_inventory)
    _seal_tree_read_only(attempt)
    with _exclusive_lifecycle_lock(lifecycle_lock, blind_group=blind_group):
        return _publish_or_reuse_locked(
            job=job,
            attempt=attempt,
            canonical=canonical,
            completion_index=completion_index,
            authorization_sha256=authorization_sha256,
            stage_id=stage_id,
            session_id=session_id,
            blind_group=blind_group,
            execution_context=locked_context,
            attempt_inventory=attempt_inventory,
            attempt_tree_sha=attempt_tree_sha,
            attempt_total_bytes=attempt_total_bytes,
        )


def _publish_or_reuse_locked(
    *,
    job: Mapping[str, Any],
    attempt: Path,
    canonical: Path,
    completion_index: Path,
    authorization_sha256: str,
    stage_id: str,
    session_id: str,
    blind_group: str,
    execution_context: Mapping[str, Any],
    attempt_inventory: Sequence[Mapping[str, str]],
    attempt_tree_sha: str,
    attempt_total_bytes: int,
) -> dict[str, Any]:
    if canonical.exists() or canonical.is_symlink():
        verified = verify_canonical_job(canonical, job=job)
        _append_completion_index(
            completion_index,
            marker=verified["marker"],
            canonical_root=canonical,
            blind_group=blind_group,
        )
        return _success_result(verified["marker"], reused=True)
    parent = _regular_directory(canonical.parent, "canonical raw parent")
    temporary: Path | None = Path(
        tempfile.mkdtemp(prefix=f".{canonical.name}.", suffix=".tmp", dir=parent)
    )
    try:
        adapter = temporary / "adapter"
        native = adapter / "native_run"
        logs = adapter / "logs"
        native.mkdir(parents=True, mode=0o700)
        logs.mkdir(mode=0o700)
        os.chmod(adapter, 0o700)
        os.chmod(native, 0o700)
        os.chmod(logs, 0o700)
        _copy_attempt_native(attempt, native)
        for stream in SEALED_STREAMS:
            shutil.copyfile(attempt / stream, logs / stream)
            os.chmod(logs / stream, 0o600)
        _build_standard_adapter_metadata(
            root=temporary,
            adapter=adapter,
            native=native,
            logs=logs,
            attempt=attempt,
            job=job,
            execution_context=execution_context,
            authorization_sha256=authorization_sha256,
            stage_id=stage_id,
            session_id=session_id,
        )
        artifact_inventory = _inventory(
            temporary, excluded={FORMAL_JOB_COMPLETION_MARKER}
        )
        marker = {
            "schema_version": "agentdojo_formal_job_completion/v2",
            "completed_at": utc_now_iso(),
            **_binding(job),
            "stage_authorization_sha256": authorization_sha256,
            "formal_stage_id": stage_id,
            "formal_stage_session_id": session_id,
            "formal_execution_context_sha256": sha256_object(
                dict(execution_context)
            ),
            "artifact_file_count": len(artifact_inventory),
            "artifact_tree_sha256": sha256_object(artifact_inventory),
            "artifact_total_bytes": _inventory_bytes(temporary, artifact_inventory),
            "native_episode_count": 3,
            "attempt_tree_sha256": attempt_tree_sha,
            "attempt_file_count": len(attempt_inventory),
            "attempt_total_bytes": attempt_total_bytes,
            "supervisor_exit_receipt_sha256": sha256_file(attempt / SUPERVISOR_EXIT),
            "worker_status": "completed",
            "postprocessor": "agentdojo_formal_postprocessor/v1",
        }
        _write_exclusive_json(adapter / FORMAL_JOB_COMPLETION_MARKER, marker)
        _fsync_tree(temporary)
        try:
            _rename_noreplace(temporary, canonical)
            temporary = None
            _fsync_directory(parent)
        except FileExistsError:
            shutil.rmtree(temporary)
            temporary = None
        verified = verify_canonical_job(canonical, job=job)
        _append_completion_index(
            completion_index,
            marker=verified["marker"],
            canonical_root=canonical,
            blind_group=blind_group,
        )
        return _success_result(
            verified["marker"], reused=verified["marker"] != marker
        )
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)


def archive_failed_attempt(
    *,
    job: Mapping[str, Any],
    attempt_root: Path,
    failed_attempt_index: Path,
    authorization_sha256: str,
    stage_id: str,
    session_id: str,
    failure_category: str,
    worker_exit_code: int,
    blind_group: str,
    canonical_root: Path,
    failed_archive_root: Path,
    lifecycle_lock: Path,
) -> dict[str, Any]:
    attempt = _regular_directory(attempt_root, "failed attempt root")
    _verify_supervisor_exited(attempt, session_id=session_id, allow_timeout=True)
    canonical = Path(canonical_root)
    with _exclusive_lifecycle_lock(lifecycle_lock, blind_group=blind_group):
        if canonical.exists() or canonical.is_symlink():
            raise RuntimeError(
                "failed attempt cannot be archived after canonical publication"
            )
    inventory = _inventory(attempt, excluded={ATTEMPT_FAILURE})
    failure = {
        "schema_version": "agentdojo_formal_attempt_failure/v1",
        "sealed_at": utc_now_iso(),
        **_binding(job),
        "stage_authorization_sha256": _digest(
            authorization_sha256, "authorization_sha256"
        ),
        "formal_stage_id": stage_id,
        "formal_stage_session_id": session_id,
        "failure_category": failure_category,
        "worker_exit_code": int(worker_exit_code),
        "attempt_tree_sha256": sha256_object(inventory),
        "attempt_file_count": len(inventory),
        "attempt_total_bytes": _inventory_bytes(attempt, inventory),
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    _write_identical_or_new(attempt / ATTEMPT_FAILURE, failure)
    full_inventory = _inventory(attempt, excluded=set())
    archive_tree_sha = sha256_object(full_inventory)
    archive_total_bytes = _inventory_bytes(attempt, full_inventory)
    archive_root = _regular_directory(
        failed_archive_root, "sealed failed-attempt archive root"
    )
    binding = str(failure["job_binding_sha256"])
    binding_root = archive_root / binding
    if not binding_root.exists() and not binding_root.is_symlink():
        os.mkdir(binding_root, 0o700)
        _fsync_directory(archive_root)
    binding_root = _regular_directory(binding_root, "failed-attempt binding root")
    destination = binding_root / session_id
    with _exclusive_lifecycle_lock(lifecycle_lock, blind_group=blind_group):
        if canonical.exists() or canonical.is_symlink():
            raise RuntimeError(
                "canonical publication raced failed-attempt archival"
            )
        if destination.exists() or destination.is_symlink():
            verified = _verify_failed_archive(
                destination,
                job=job,
                authorization_sha256=authorization_sha256,
                stage_id=stage_id,
                session_id=session_id,
            )
            if (
                verified["archive_tree_sha256"] != archive_tree_sha
                or verified["archive_total_bytes"] != archive_total_bytes
            ):
                raise RuntimeError("failed-attempt archive collision differs")
        else:
            _rename_noreplace(attempt, destination)
            _fsync_directory(binding_root)
            _seal_tree_read_only(destination)
            verified = _verify_failed_archive(
                destination,
                job=job,
                authorization_sha256=authorization_sha256,
                stage_id=stage_id,
                session_id=session_id,
            )
    entry = {
        **failure,
        "archive_relative_path": f"{binding}/{session_id}",
        "attempt_failure_marker_sha256": sha256_file(
            destination / ATTEMPT_FAILURE
        ),
        "archive_tree_sha256": verified["archive_tree_sha256"],
        "archive_file_count": verified["archive_file_count"],
        "archive_total_bytes": verified["archive_total_bytes"],
        "attempt_identity_sha256": sha256_object(
            {
                "job_binding_sha256": failure["job_binding_sha256"],
                "session_id": session_id,
                "stage_authorization_sha256": authorization_sha256,
            }
        ),
    }
    with _exclusive_lifecycle_lock(lifecycle_lock, blind_group=blind_group):
        current = _verify_failed_archive(
            destination,
            job=job,
            authorization_sha256=authorization_sha256,
            stage_id=stage_id,
            session_id=session_id,
        )
        if current != verified:
            raise RuntimeError("failed-attempt archive drifted before index append")
        _append_jsonl_unique(
            failed_attempt_index,
            entry,
            unique_field="attempt_identity_sha256",
            blind_group=blind_group,
        )
    return {
        "schema_version": "agentdojo_formal_postprocessor_result/v1",
        "status": "failed_attempt_archived",
        "attempt_identity_sha256": entry["attempt_identity_sha256"],
        "attempt_tree_sha256": entry["attempt_tree_sha256"],
        "archive_tree_sha256": entry["archive_tree_sha256"],
        "blind_only": True,
    }


def _verify_failed_archive(
    root: Path,
    *,
    job: Mapping[str, Any],
    authorization_sha256: str,
    stage_id: str,
    session_id: str,
) -> dict[str, Any]:
    archive = _regular_directory(root, "sealed failed-attempt archive")
    marker = _loads_file(archive / ATTEMPT_FAILURE)
    expected_fields = {
        "schema_version", "sealed_at", "execution_lock_sha256",
        "execution_policy_sha256", "job_binding_sha256", "job_identity_sha256",
        "stage_authorization_sha256", "formal_stage_id",
        "formal_stage_session_id", "failure_category", "worker_exit_code",
        "attempt_tree_sha256", "attempt_file_count", "attempt_total_bytes",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
    if set(marker) != expected_fields or marker.get("schema_version") != (
        "agentdojo_formal_attempt_failure/v1"
    ):
        raise RuntimeError("sealed failed-attempt marker fields differ")
    for field, value in _binding(job).items():
        if marker.get(field) != value:
            raise RuntimeError(f"sealed failed-attempt marker has stale {field}")
    if (
        marker.get("stage_authorization_sha256") != authorization_sha256
        or marker.get("formal_stage_id") != stage_id
        or marker.get("formal_stage_session_id") != session_id
        or marker.get("blind_only") is not True
        or marker.get(
            "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
        )
        is not False
    ):
        raise RuntimeError("sealed failed-attempt marker binding differs")
    attempt_inventory = _inventory(archive, excluded={ATTEMPT_FAILURE})
    if (
        marker.get("attempt_tree_sha256") != sha256_object(attempt_inventory)
        or marker.get("attempt_file_count") != len(attempt_inventory)
        or marker.get("attempt_total_bytes")
        != _inventory_bytes(archive, attempt_inventory)
    ):
        raise RuntimeError("sealed failed-attempt tree differs")
    full_inventory = _inventory(archive, excluded=set())
    return {
        "archive_tree_sha256": sha256_object(full_inventory),
        "archive_file_count": len(full_inventory),
        "archive_total_bytes": _inventory_bytes(archive, full_inventory),
    }


def verify_canonical_job(
    canonical_root: Path, *, job: Mapping[str, Any]
) -> dict[str, Any]:
    root = _regular_directory(canonical_root, "canonical job root")
    if {path.name for path in root.iterdir()} != {"adapter"}:
        raise RuntimeError("canonical job root field set differs")
    adapter = _regular_directory(root / "adapter", "canonical adapter root")
    expected = {
        "native_run",
        "logs",
        "raw_run.json",
        "artifact_manifest.json",
        "environment.json",
        FORMAL_JOB_COMPLETION_MARKER,
    }
    if {path.name for path in adapter.iterdir()} != expected:
        raise RuntimeError("canonical adapter field set differs")
    for name in expected - {"native_run", "logs"}:
        _regular_file(adapter / name, f"canonical {name}")
    _regular_directory(adapter / "native_run", "canonical native root")
    logs = _regular_directory(adapter / "logs", "canonical logs root")
    if {path.name for path in logs.iterdir()} != set(SEALED_STREAMS):
        raise RuntimeError("canonical sealed stream set differs")
    for name in SEALED_STREAMS:
        _regular_file(logs / name, name)
    _exact_episode_paths(adapter / "native_run", job)
    raw_run = _loads_file(adapter / "raw_run.json")
    environment = _loads_file(adapter / "environment.json")
    manifest = _loads_file(adapter / "artifact_manifest.json")
    _verify_standard_adapter_metadata(
        canonical_root=root,
        adapter=adapter,
        job=job,
        raw_run=raw_run,
        environment=environment,
        manifest=manifest,
    )
    marker = _loads_file(adapter / FORMAL_JOB_COMPLETION_MARKER)
    if set(marker) != {
        "schema_version", "completed_at", "execution_lock_sha256",
        "execution_policy_sha256", "job_binding_sha256", "job_identity_sha256",
        "stage_authorization_sha256", "formal_stage_id", "formal_stage_session_id",
        "formal_execution_context_sha256",
        "artifact_file_count", "artifact_tree_sha256", "artifact_total_bytes",
        "native_episode_count", "attempt_tree_sha256", "attempt_file_count",
        "attempt_total_bytes", "supervisor_exit_receipt_sha256", "worker_status",
        "postprocessor",
    }:
        raise RuntimeError("canonical completion marker fields differ")
    if (
        marker.get("schema_version") != "agentdojo_formal_job_completion/v2"
        or marker.get("worker_status") != "completed"
        or marker.get("postprocessor") != "agentdojo_formal_postprocessor/v1"
        or marker.get("native_episode_count") != 3
    ):
        raise RuntimeError("canonical completion marker status/schema differs")
    for field, value in _binding(job).items():
        if marker.get(field) != value:
            raise RuntimeError(f"canonical completion marker has stale {field}")
    context_sha256 = _digest(
        str(marker.get("formal_execution_context_sha256") or ""),
        "formal_execution_context_sha256",
    )
    for field in (
        "stage_authorization_sha256",
        "attempt_tree_sha256",
        "supervisor_exit_receipt_sha256",
    ):
        _digest(str(marker.get(field) or ""), field)
    if environment.get("formal_execution_context_sha256") != context_sha256:
        raise RuntimeError(
            "canonical completion marker execution context differs from environment"
        )
    for field in (
        "stage_authorization_sha256",
        "formal_stage_id",
        "formal_stage_session_id",
        "supervisor_exit_receipt_sha256",
    ):
        if marker.get(field) != environment.get(field):
            raise RuntimeError(
                f"canonical completion marker {field} differs from environment"
            )
    inventory = _inventory(root, excluded={f"adapter/{FORMAL_JOB_COMPLETION_MARKER}"})
    if (
        marker.get("artifact_file_count") != len(inventory)
        or marker.get("artifact_tree_sha256") != sha256_object(inventory)
        or marker.get("artifact_total_bytes") != _inventory_bytes(root, inventory)
    ):
        raise RuntimeError("canonical artifact tree differs from completion marker")
    return {"marker": marker, "inventory": inventory}


def _verify_worker_success(
    attempt: Path,
    *,
    job: Mapping[str, Any],
    authorization_sha256: str,
    stage_id: str,
    session_id: str,
) -> None:
    marker = _loads_file(attempt / FORMAL_JOB_WORKER_SUCCESS_MARKER)
    expected_fields = {
        "schema_version", "finished_at", "execution_lock_sha256",
        "execution_policy_sha256", "job_binding_sha256", "job_identity_sha256",
        "stage_authorization_sha256", "formal_stage_id",
        "formal_stage_session_id", "expected_episode_count", "worker_status",
    }
    if set(marker) != expected_fields or (
        marker.get("schema_version") != "agentdojo_formal_worker_success/v1"
        or marker.get("worker_status") != "completed"
        or marker.get("expected_episode_count") != 3
        or marker.get("stage_authorization_sha256") != authorization_sha256
        or marker.get("formal_stage_id") != stage_id
        or marker.get("formal_stage_session_id") != session_id
    ):
        raise RuntimeError("formal worker-success marker differs")
    for field, value in _binding(job).items():
        if marker.get(field) != value:
            raise RuntimeError(f"formal worker-success marker has stale {field}")


def _verify_supervisor_exited(
    attempt: Path, *, session_id: str, allow_timeout: bool = False
) -> None:
    exited = formal_supervisor._verify_exit(
        attempt / SUPERVISOR_EXIT, expected_session_id=session_id
    )
    if exited.get("bootstrap_terminal") is True:
        if not allow_timeout or exited.get("exit_code") == 0:
            raise RuntimeError("formal bootstrap terminal receipt cannot prove success")
        return
    state = formal_supervisor._verify_state(
        attempt / SUPERVISOR_STATE, expected_session_id=session_id
    )
    if exited.get("state_sha256") != sha256_object(state):
        raise RuntimeError("formal supervisor exit receipt has stale state hash")
    if exited.get("group_gone") is not True:
        raise RuntimeError("formal worker process group is not proven gone")
    if exited.get("job_binding_sha256") != state.get("job_binding_sha256") or (
        exited.get("stage_authorization_sha256")
        != state.get("stage_authorization_sha256")
    ):
        raise RuntimeError("formal supervisor exit binding differs")
    exit_code = exited.get("exit_code")
    if not isinstance(exit_code, int) or (not allow_timeout and exit_code != 0):
        raise RuntimeError("formal supervisor exit status differs")
    if not allow_timeout and (
        exited.get("outcome") != "worker_exited"
        or exited.get("timed_out") is not False
    ):
        raise RuntimeError("formal supervisor successful outcome differs")
    pid = state["supervisor_pid"]
    starttime = state["supervisor_starttime_ticks"]
    proc = Path(f"/proc/{pid}/stat")
    if proc.exists() and _linux_starttime(proc) == starttime:
        raise RuntimeError("formal supervisor/process group is still alive")
    for name in SEALED_STREAMS:
        stream = _regular_file(attempt / name, name)
        if stat.S_IMODE(stream.stat().st_mode) != 0o600:
            raise RuntimeError("formal sealed stream mode differs")


def _exact_episode_paths(root: Path, job: Mapping[str, Any]) -> list[Path]:
    parts = str(job.get("case_unit_id") or "").split(":")
    if len(parts) != 4:
        raise RuntimeError("formal job case identity cannot derive three episodes")
    _version, suite, user_task, injection_task = parts
    base = root / "trace_logs" / "local" / suite
    expected = [
        base / injection_task / "none" / "none.json",
        base / user_task / "none" / "none.json",
        base / user_task / "direct" / f"{injection_task}.json",
    ]
    observed = sorted((root / "trace_logs").rglob("*.json"))
    if sorted(path.resolve() for path in expected) != [path.resolve() for path in observed]:
        raise RuntimeError("formal native evidence does not contain exactly three traces")
    for path in expected:
        _regular_file(path, "native episode trace")
        _loads_file(path)
    return expected


def _copy_attempt_native(attempt: Path, native: Path) -> None:
    for source in sorted(attempt.rglob("*")):
        relative = source.relative_to(attempt)
        if relative.as_posix() in LIFECYCLE_FILES:
            continue
        if source.is_symlink() or not (source.is_file() or source.is_dir()):
            raise RuntimeError("formal attempt contains a symlink or special file")
        destination = native / relative
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(source, destination)
            os.chmod(destination, 0o600)


def _build_standard_adapter_metadata(
    *,
    root: Path,
    adapter: Path,
    native: Path,
    logs: Path,
    attempt: Path,
    job: Mapping[str, Any],
    execution_context: Mapping[str, Any],
    authorization_sha256: str,
    stage_id: str,
    session_id: str,
) -> None:
    started = _loads_file(attempt / FORMAL_JOB_STARTED_MARKER)
    finished = _loads_file(attempt / FORMAL_JOB_WORKER_SUCCESS_MARKER)
    for payload, label in ((started, "started"), (finished, "worker success")):
        for field, value in _binding(job).items():
            if payload.get(field) != value:
                raise RuntimeError(f"formal {label} marker has stale {field}")
        if payload.get("stage_authorization_sha256") != authorization_sha256:
            raise RuntimeError(f"formal {label} marker has stale authorization")
    if (
        started.get("formal_stage_id") != stage_id
        or started.get("formal_stage_session_id") != session_id
        or finished.get("formal_stage_id") != stage_id
        or finished.get("formal_stage_session_id") != session_id
    ):
        raise RuntimeError("formal worker lifecycle stage/session differs")
    started_at = str(started.get("started_at") or "")
    ended_at = str(finished.get("finished_at") or "")
    spec = formal_supervisor._verify_spec(attempt / formal_supervisor.SPEC)
    if spec.get("command_sha256") != execution_context.get("producer_command_sha256"):
        raise RuntimeError("formal execution context producer command differs")
    target = SimpleNamespace(
        machine_id=execution_context["machine_id"],
        machine_role=execution_context["machine_role"],
        ssh_host=execution_context["ssh_host"],
        ssh_port=execution_context["ssh_port"],
        remote_workdir=execution_context["remote_workdir"],
        runner_workdir=execution_context["runner_workdir"],
        benchmark_name=execution_context["benchmark_name"],
        benchmark_config_hash=execution_context["benchmark_config_hash"],
    )
    context = SmokeExecutionContext(
        manifest_path=Path("locked-manifest"),
        manifest_hash=str(job["manifest_hash"]),
        source_bundle_path=Path("locked-source-bundle"),
        source_bundle_hash=str(execution_context["source_bundle_hash"]),
        official_split_hash=str(execution_context["official_split_hash"]),
        agents_config_path=Path("locked-agents"),
        dotenv_path=Path("secrets-never-synced"),
    )
    _environment, environment_hash = write_environment_snapshot(
        target=target,
        job=job,
        output_path=adapter / "environment.json",
        extra_fields={
            "schema_version": "agentdojo_formal_environment/v1",
            "stage_authorization_sha256": authorization_sha256,
            "formal_stage_id": stage_id,
            "formal_stage_session_id": session_id,
            "supervisor_exit_receipt_sha256": sha256_file(
                attempt / SUPERVISOR_EXIT
            ),
            "formal_execution_context_sha256": sha256_object(
                dict(execution_context)
            ),
            "worker_streams_closed_before_packaging": True,
        },
    )
    descriptors = _standard_artifact_descriptors(
        native=native,
        logs=logs,
        environment_path=adapter / "environment.json",
    )
    local_job_root = job_result_relative_dir(job)

    def declared_path(path: Path) -> str:
        try:
            relative = path.relative_to(root)
        except ValueError as exc:  # pragma: no cover - construction invariant
            raise RuntimeError("formal artifact is outside the package root") from exc
        return (local_job_root / relative).as_posix()

    _manifest, manifest_path, manifest_sha = build_artifact_manifest(
        job=job,
        context=context,
        target=target,
        descriptors=descriptors,
        producer_command=str(spec["command_sha256"]),
        started_at=started_at,
        output_path=adapter / "artifact_manifest.json",
        environment_hash=environment_hash,
        declared_path_mapper=declared_path,
    )
    summary = _loads_file(native / "run_summary.json")
    if summary.get("status") != "completed":
        raise RuntimeError("formal AgentDojo run summary is not completed")
    success = (
        bool(summary.get("benign_utility"))
        and bool(summary.get("injected_utility"))
        and not bool(summary.get("injected_security"))
    )
    local_adapter = local_job_root / "adapter"
    build_raw_run(
        job=job,
        target=target,
        artifact_manifest_path=manifest_path,
        artifact_manifest_sha256=manifest_sha,
        raw_run_path=adapter / "raw_run.json",
        started_at=started_at,
        ended_at=ended_at,
        status="COMPLETED",
        diagnostic_status="completed",
        appendix_failure_class="none",
        native_label="success" if success else "fail",
        native_score=1.0 if success else 0.0,
        episode_ids=[
            f"agentdojo:benign:{job['task_id']}",
            f"agentdojo:injection_task_as_user_task:{job['task_id']}",
            f"agentdojo:injected:{job['task_id']}",
        ],
        llm_calls_log_path=None,
        artifact_manifest_declared_path=local_adapter / "artifact_manifest.json",
        raw_run_declared_path=local_adapter / "raw_run.json",
    )
    validate_object(
        "raw_run", _loads_file(adapter / "raw_run.json"), raise_on_error=True
    )
    validate_object(
        "artifact_manifest",
        _loads_file(adapter / "artifact_manifest.json"),
        raise_on_error=True,
    )


def _standard_artifact_descriptors(
    *, native: Path, logs: Path, environment_path: Path
) -> tuple[ArtifactDescriptor, ...]:
    descriptors: list[ArtifactDescriptor] = []

    def add(
        path: Path,
        *,
        artifact_type: str,
        producer_role: str,
        official_runner: bool,
        official_evaluator: bool,
    ) -> None:
        if not path.exists():
            return
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role=producer_role,
                producer_name=(
                    "agentdojo-0.1.35" if official_runner else "sealed-postprocessor"
                ),
                producer_version="0.1.35" if official_runner else "1",
                official_runner=official_runner,
                official_evaluator=official_evaluator,
                evaluator_name=(
                    "AgentDojo native evaluators" if official_evaluator else None
                ),
                evaluator_version="0.1.35" if official_evaluator else None,
            )
        )

    for relative, artifact_type, role, official_runner, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "official_runner", True, False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True, True),
        ("run_summary.json", "structured_output", "adapter", False, False),
        ("job.json", "file", "adapter", False, False),
        ("source_bundle_entry.json", "file", "adapter", False, False),
        ("worker_config.json", "file", "adapter", False, False),
        ("seed_verification.json", "file", "adapter", False, False),
        ("install_verification.json", "file", "adapter", False, False),
        ("runtime_policy_verification.json", "file", "adapter", False, False),
        ("blind_health", "file", "adapter", False, False),
        ("proxy_calls", "file", "adapter", False, False),
        ("trace_logs", "trace", "official_runner", True, False),
    ):
        add(
            native / relative,
            artifact_type=artifact_type,
            producer_role=role,
            official_runner=official_runner,
            official_evaluator=official_evaluator,
        )
    add(
        environment_path,
        artifact_type="file",
        producer_role="adapter",
        official_runner=False,
        official_evaluator=False,
    )
    add(
        logs / SEALED_STREAMS[0],
        artifact_type="stdout",
        producer_role="adapter",
        official_runner=False,
        official_evaluator=False,
    )
    add(
        logs / SEALED_STREAMS[1],
        artifact_type="stderr",
        producer_role="adapter",
        official_runner=False,
        official_evaluator=False,
    )
    return tuple(descriptors)


def _verify_execution_context(
    payload: Mapping[str, Any], *, job: Mapping[str, Any]
) -> dict[str, Any]:
    expected = {
        "schema_version", "machine_id", "machine_role", "ssh_host", "ssh_port",
        "remote_workdir", "runner_workdir", "benchmark_name",
        "benchmark_config_hash", "source_bundle_hash", "official_split_hash",
        "producer_command_sha256",
    }
    context = dict(payload)
    if set(context) != expected or context.get("schema_version") != (
        "agentdojo_formal_execution_context/v1"
    ):
        raise RuntimeError("formal execution context fields differ")
    for field in (
        "benchmark_config_hash", "source_bundle_hash", "official_split_hash",
        "producer_command_sha256",
    ):
        _digest(str(context.get(field) or ""), field)
    if context.get("benchmark_config_hash") != job.get("benchmark_config_hash") or (
        context.get("benchmark_name") != job.get("benchmark_name")
    ):
        raise RuntimeError("formal execution context benchmark binding differs")
    if not isinstance(context.get("ssh_port"), int) or not all(
        isinstance(context.get(field), str) and bool(context[field])
        for field in (
            "machine_id", "machine_role", "ssh_host", "remote_workdir",
            "runner_workdir", "benchmark_name",
        )
    ):
        raise RuntimeError("formal execution context machine fields are invalid")
    return context


def _append_completion_index(
    path: Path,
    *,
    marker: Mapping[str, Any],
    canonical_root: Path,
    blind_group: str,
) -> None:
    binding = str(marker["job_binding_sha256"])
    if canonical_root.name != binding:
        raise RuntimeError("canonical job directory differs from its job binding")
    marker_path = canonical_root / "adapter" / FORMAL_JOB_COMPLETION_MARKER
    entry = {
        "schema_version": "agentdojo_formal_remote_completion_journal_entry/v2",
        "recorded_at": utc_now_iso(),
        **{
            field: marker[field]
            for field in (
                "execution_lock_sha256", "execution_policy_sha256",
                "job_binding_sha256", "job_identity_sha256",
                "stage_authorization_sha256", "formal_stage_id",
                "formal_stage_session_id", "formal_execution_context_sha256",
                "artifact_file_count",
                "artifact_tree_sha256", "artifact_total_bytes",
                "native_episode_count", "attempt_tree_sha256",
                "attempt_file_count", "attempt_total_bytes",
                "supervisor_exit_receipt_sha256",
            )
        },
        "canonical_job_relative_path": binding,
        "completion_marker_relative_path": (
            f"{binding}/adapter/{FORMAL_JOB_COMPLETION_MARKER}"
        ),
        "completion_marker_file_sha256": sha256_file(marker_path),
        "completion_marker_semantic_sha256": sha256_object(dict(marker)),
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    _append_jsonl_unique(
        path, entry, unique_field="job_identity_sha256", blind_group=blind_group
    )


@contextmanager
def _exclusive_lifecycle_lock(path: Path, *, blind_group: str):
    parent = _regular_directory(path.parent, "canonical lifecycle lock parent")
    if path.is_symlink():
        raise RuntimeError("canonical lifecycle lock is symlinked")
    descriptor = os.open(
        path,
        os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
        0o640,
    )
    try:
        os.fchmod(descriptor, 0o640)
        os.fchown(descriptor, -1, grp.getgrnam(blind_group).gr_gid)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
        os.fsync(descriptor)
        _fsync_directory(parent)
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _append_jsonl_unique(
    path: Path,
    entry: Mapping[str, Any],
    *,
    unique_field: str,
    blind_group: str,
) -> None:
    parent = _regular_directory(path.parent, "blind index parent")
    if path.is_symlink():
        raise RuntimeError("blind index is symlinked")
    flags = os.O_RDWR | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o640)
    try:
        os.fchmod(descriptor, 0o640)
        os.fchown(descriptor, -1, grp.getgrnam(blind_group).gr_gid)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        os.lseek(descriptor, 0, os.SEEK_SET)
        existing = [
            json.loads(line)
            for line in os.read(descriptor, 64 << 20).decode("utf-8").splitlines()
            if line.strip()
        ]
        matches = [row for row in existing if row.get(unique_field) == entry[unique_field]]
        if matches:
            comparable = dict(entry)
            comparable["recorded_at"] = matches[0].get("recorded_at")
            if len(matches) != 1 or matches[0] != comparable:
                raise RuntimeError("blind index contains a conflicting duplicate")
            return
        encoded = (json.dumps(dict(entry), separators=(",", ":"), sort_keys=True) + "\n").encode()
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:  # pragma: no cover - defensive kernel invariant
                raise RuntimeError("blind index write made no progress")
            view = view[written:]
        os.fsync(descriptor)
        _fsync_directory(parent)
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _inventory(root: Path, *, excluded: set[str]) -> list[dict[str, str]]:
    result = []
    for path in sorted(root.rglob("*")):
        try:
            info = os.lstat(path)
        except OSError as exc:
            raise RuntimeError("sealed tree entry cannot be inspected") from exc
        if stat.S_ISLNK(info.st_mode) or not (
            stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
        ):
            raise RuntimeError("sealed tree contains a symlink or special file")
        if stat.S_ISDIR(info.st_mode):
            continue
        if info.st_nlink != 1:
            raise RuntimeError("sealed tree contains a hard-linked file")
        try:
            relative_path = path.relative_to(root)
        except ValueError as exc:  # pragma: no cover - Path.rglob invariant
            raise RuntimeError("sealed tree entry escapes its root") from exc
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError("sealed tree entry escapes its root")
        relative = relative_path.as_posix()
        if relative in excluded:
            continue
        result.append({"path": relative, "sha256": sha256_file(path)})
    return result


def _inventory_bytes(root: Path, inventory: Sequence[Mapping[str, str]]) -> int:
    return sum((root / str(row["path"])).stat().st_size for row in inventory)


def _verify_standard_adapter_metadata(
    *,
    canonical_root: Path,
    adapter: Path,
    job: Mapping[str, Any],
    raw_run: Mapping[str, Any],
    environment: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> None:
    validate_object("raw_run", dict(raw_run), raise_on_error=True)
    validate_object("artifact_manifest", dict(manifest), raise_on_error=True)
    identity_fields = (
        "case_unit_id", "task_id", "record_slot_id", "run_id", "attempt_id",
        "seed", "agent_id",
    )
    for payload in (raw_run, manifest):
        for field in identity_fields:
            if payload.get(field) != job.get(field):
                raise RuntimeError(f"canonical metadata has stale {field}")
    expected_locked = {
        "execution_lock_sha256": job["execution_lock_sha256"],
        "execution_policy_sha256": job["execution_policy_sha256"],
        "openrouter_runtime_policy_sha256": job["openrouter_runtime_policy_sha256"],
        "openrouter_runtime_policy_file_sha256": job[
            "openrouter_runtime_policy_file_sha256"
        ],
    }
    for payload in (raw_run, manifest, environment):
        for field, value in expected_locked.items():
            if payload.get(field) != value:
                raise RuntimeError(f"canonical metadata has stale {field}")
    if (
        raw_run.get("schema_version") != "raw_run/v1"
        or raw_run.get("status") != "COMPLETED"
        or raw_run.get("diagnostic_status") != "completed"
        or raw_run.get("appendix_failure_class") != "none"
        or raw_run.get("native_label_used_as_decisive_evidence") is not False
    ):
        raise RuntimeError("canonical raw-run status differs")
    local_job_root = job_result_relative_dir(job)
    local_adapter = local_job_root / "adapter"
    if raw_run.get("raw_source_path") != (local_adapter / "raw_run.json").as_posix() or (
        raw_run.get("artifact_manifest_path")
        != (local_adapter / "artifact_manifest.json").as_posix()
    ):
        raise RuntimeError("canonical raw-run declared paths differ")
    if raw_run.get("artifact_manifest_sha256") != sha256_file(
        adapter / "artifact_manifest.json"
    ):
        raise RuntimeError("canonical raw-run manifest hash differs")
    expected_episode_ids = [
        f"agentdojo:benign:{job['task_id']}",
        f"agentdojo:injection_task_as_user_task:{job['task_id']}",
        f"agentdojo:injected:{job['task_id']}",
    ]
    if raw_run.get("episode_ids") != expected_episode_ids:
        raise RuntimeError("canonical raw-run episode IDs differ")
    environment_path = adapter / "environment.json"
    if manifest.get("environment_hash") != sha256_file(environment_path):
        raise RuntimeError("canonical artifact environment hash differs")
    artifact_paths: set[Path] = set()
    covered_files: set[Path] = set()
    trace_artifacts = 0
    for entry in list(manifest.get("artifacts") or []):
        if not isinstance(entry, Mapping):
            raise RuntimeError("canonical artifact entry is not an object")
        declared = Path(str(entry.get("path") or ""))
        try:
            relative = declared.relative_to(local_job_root)
        except ValueError as exc:
            raise RuntimeError("canonical artifact path escapes locked local job root") from exc
        actual = canonical_root / relative
        if actual in artifact_paths:
            raise RuntimeError("canonical artifact path is duplicated")
        artifact_paths.add(actual)
        if actual.is_file() and not actual.is_symlink():
            digest, size = sha256_file(actual), actual.stat().st_size
            covered_files.add(actual)
        elif actual.is_dir() and not actual.is_symlink():
            digest = sha256_path(actual)
            members = {path for path in actual.rglob("*") if path.is_file()}
            size = sum(path.stat().st_size for path in members)
            covered_files.update(members)
        else:
            raise RuntimeError("canonical artifact path is absent or linked")
        if entry.get("sha256") != digest or entry.get("size_bytes") != size:
            raise RuntimeError("canonical artifact digest/size differs")
        if entry.get("environment_hash") != manifest.get("environment_hash"):
            raise RuntimeError("canonical artifact environment binding differs")
        if entry.get("source_bundle_hash") != manifest.get("source_bundle_hash"):
            raise RuntimeError("canonical artifact source binding differs")
        if entry.get("artifact_type") == "trace":
            trace_artifacts += 1
            if actual != adapter / "native_run" / "trace_logs":
                raise RuntimeError("canonical trace artifact root differs")
    if trace_artifacts != 1 or environment_path not in artifact_paths:
        raise RuntimeError("canonical artifact graph lacks exact trace/environment nodes")
    control = {
        adapter / "raw_run.json",
        adapter / "artifact_manifest.json",
        adapter / FORMAL_JOB_COMPLETION_MARKER,
    }
    observed_files = {path for path in canonical_root.rglob("*") if path.is_file()}
    if observed_files != covered_files | control:
        raise RuntimeError("canonical artifact graph coverage differs")


def _binding(job: Mapping[str, Any]) -> dict[str, str]:
    return {
        "execution_lock_sha256": _digest(str(job.get("execution_lock_sha256") or ""), "lock"),
        "execution_policy_sha256": _digest(str(job.get("execution_policy_sha256") or ""), "policy"),
        "job_binding_sha256": formal_job_binding_sha256(job),
        "job_identity_sha256": job_identity_sha256(job),
    }


def _success_result(marker: Mapping[str, Any], *, reused: bool) -> dict[str, Any]:
    return {
        "schema_version": "agentdojo_formal_postprocessor_result/v1",
        "status": "canonical_reused" if reused else "canonical_published",
        **{
            field: marker[field]
            for field in (
                "execution_lock_sha256", "execution_policy_sha256",
                "job_binding_sha256", "job_identity_sha256", "artifact_file_count",
                "artifact_tree_sha256", "artifact_total_bytes", "native_episode_count",
            )
        },
        "completion_marker_semantic_sha256": sha256_object(dict(marker)),
        "blind_only": True,
    }


def _rename_noreplace(source: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise RuntimeError("renameat2(RENAME_NOREPLACE) is required")
    result = renameat2(
        -100, os.fsencode(source), -100, os.fsencode(destination), 1
    )
    if result == 0:
        return
    observed = ctypes.get_errno()
    if observed == errno.EEXIST:
        raise FileExistsError(destination)
    raise OSError(observed, os.strerror(observed), str(destination))


def _fsync_tree(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda value: len(value.parts), reverse=True,
    ):
        _fsync_directory(directory)
    _fsync_directory(root)


def _seal_tree_read_only(root: Path) -> None:
    """Remove write bits only after the supervisor proved the process group gone."""

    for path in sorted(root.rglob("*"), key=lambda value: len(value.parts), reverse=True):
        if path.is_symlink():
            raise RuntimeError("cannot seal a formal tree containing symlinks")
        if path.is_file():
            os.chmod(path, 0o400)
        elif path.is_dir():
            os.chmod(path, 0o500)
        else:
            raise RuntimeError("cannot seal a formal tree containing special files")
    os.chmod(root, 0o500)
    _fsync_tree(root)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_exclusive_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)


def _write_identical_or_new(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        if _loads_file(path) != dict(payload):
            raise RuntimeError("immutable failure marker differs")
        return
    _write_exclusive_json(path, payload)


def _regular_directory(path: Path, label: str) -> Path:
    _assert_no_symlink_ancestors(path)
    if path.is_symlink() or not path.is_dir():
        raise RuntimeError(f"{label} is not a regular directory")
    return path


def _regular_file(path: Path, label: str) -> Path:
    _assert_no_symlink_ancestors(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise RuntimeError(f"{label} is not a regular nlink-1 file")
    return path


def _assert_no_symlink_ancestors(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:-1]:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"sealed path has symlink ancestor: {current}")


def _loads_file(path: Path) -> dict[str, Any]:
    return _loads_object(_regular_file(path, str(path)).read_text(encoding="utf-8"))


def _loads_object(value: str) -> dict[str, Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise RuntimeError("expected a JSON object")
    return loaded


def _digest(value: str, field: str) -> str:
    normalized = value.removeprefix("sha256:")
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise RuntimeError(f"{field} is not a lowercase SHA-256")
    return normalized


def _linux_starttime(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    end = raw.rfind(")")
    return int(raw[end + 1 :].strip().split()[19])


if __name__ == "__main__":
    raise SystemExit(main())
