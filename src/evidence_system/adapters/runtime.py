"""Shared Step 8 runtime helpers for remote smoke execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import mimetypes
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import threading
import time
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.dotenv import load_project_dotenv
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
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
    "configs/infra.yaml",
)
_SYNC_LOCK = threading.Lock()
_SYNCED_SUPPORT_KEYS: set[tuple[str, str, tuple[str, ...], bool]] = set()
_TRANSIENT_SSH_ERRORS = (
    "Connection closed by",
    "Connection reset by",
    "kex_exchange_identification",
    "Broken pipe",
    "Connection timed out",
    "Operation timed out",
)


class AdapterRuntimeError(RuntimeError):
    """Raised when Step 8 remote execution or artifact capture fails."""


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


def build_job_paths(job: Mapping[str, Any]) -> JobPaths:
    root = resolve_repo_path(Path("results") / str(job.get("phase") or "smoke") / str(job["domain"]) / str(job["job_id"]) / "adapter")
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
) -> None:
    sync_items = tuple(Path(path) for path in paths)
    sync_key = (
        target.machine_id,
        target.remote_workdir,
        tuple(path.as_posix() for path in sync_items),
        include_dotenv,
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
            _run_subprocess(
                [
                    "rsync",
                    "-az",
                    "-e",
                    _ssh_transport(target),
                    str(local_path),
                    f"{_ssh_target(target)}:{remote_parent}/",
                ]
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
) -> subprocess.CompletedProcess[str]:
    completed = _run_subprocess(
        _ssh_argv(target, command),
        check=False,
        capture_output=True,
    )
    _write_text(stdout_path, completed.stdout or "")
    _write_text(stderr_path, completed.stderr or "")
    return completed


def rsync_remote_tree(target: "InfraBenchmarkTarget", remote_path: str, local_path: str | Path) -> None:
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
        ]
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
        "artifact_manifest_path": _repo_relative(artifact_manifest_path),
        "artifact_manifest_sha256": artifact_manifest_sha256,
        "raw_source_path": _repo_relative(raw_run_path),
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
    validate_object("raw_run", payload, raise_on_error=True)
    written = write_json(raw_run_path, payload)
    return payload, written


def write_environment_snapshot(
    *,
    target: "InfraBenchmarkTarget",
    job: Mapping[str, Any],
    output_path: str | Path,
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
) -> dict[str, Any]:
    created_at = _file_timestamp(descriptor.local_path)
    sha256_value, size_bytes = _path_digest_and_size(descriptor.local_path)
    return {
        "artifact_id": f"{descriptor.artifact_type}:{descriptor.local_path.stem}",
        "artifact_type": descriptor.artifact_type,
        "path": _repo_relative(descriptor.local_path),
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
    return f"ssh -i {shlex.quote(target.ssh_key_path)} -p {target.ssh_port} -o StrictHostKeyChecking=no"


def _ssh_argv(target: "InfraBenchmarkTarget", command: str) -> list[str]:
    script = f"set -euo pipefail\n{command}"
    return [
        "ssh",
        "-i",
        target.ssh_key_path,
        "-p",
        str(target.ssh_port),
        "-o",
        "StrictHostKeyChecking=no",
        _ssh_target(target),
        f"bash -lc {shlex.quote(script)}",
    ]


def _run_subprocess(
    argv: Sequence[str],
    *,
    cwd: str | Path | None = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    argv_list = list(argv)
    completed: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, 5):
        completed = subprocess.run(
            argv_list,
            cwd=str(cwd) if cwd is not None else None,
            check=False,
            text=True,
            capture_output=capture_output,
        )
        if completed.returncode == 0 or not _is_transient_ssh_failure(completed) or attempt == 4:
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
