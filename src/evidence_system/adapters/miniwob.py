"""MiniWoB++ Step 8 smoke planner and remote executor."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import shutil
import threading
from typing import TYPE_CHECKING, Any, Mapping

from evidence_system.adapters.base import (
    AdapterSkeleton,
    dotenv_source_prefix,
    is_smoke_phase,
    json_arg,
    runner_plan,
    smoke_role_config,
)
from evidence_system.adapters.runtime import (
    build_artifact_manifest,
    build_job_paths,
    build_raw_run,
    default_adapter_artifacts,
    file_descriptor,
    rsync_remote_tree,
    run_remote_command,
    sync_repo_support_files,
    write_environment_snapshot,
    write_llm_call_logs,
)
from evidence_system.contracts.common import normalize_domain_or_none, utc_now_iso

if TYPE_CHECKING:
    from evidence_system.adapters.runtime import SmokeExecutionContext
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


ADAPTER = AdapterSkeleton(canonical_domain_id="miniwob", supports_direct_execution=True)

MINIWOB_REQUIRED_PROVIDER = "openrouter"
MINIWOB_REQUIRED_MODEL = "openai/gpt-5.4-mini"
MINIWOB_DEFAULT_DRIVER = "openrouter_chat"
MINIWOB_DEFAULT_MAX_STEPS = 6
MINIWOB_FULL_MAX_STEPS = 30
MINIWOB_EXPECTED_ARTIFACT_TYPES = (
    "browser_artifact",
    "post_state",
    "trace",
    "native_evaluator_input",
    "native_evaluator_output",
    "structured_output",
    "file",
)

_HTTP_SERVER_LOCK = threading.Lock()
_READY_HTTP_SERVERS: set[tuple[str, str, str, int, str]] = set()


def plan_smoke_execution(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    agents_config_path: str,
    dotenv_path: str,
    source_bundle_path: str,
    source_bundle: dict[str, Any],
) -> dict[str, Any]:
    role = smoke_role_config(job, agents_config_path=agents_config_path)
    source_entry = _bundle_source_entry(source_bundle, task_id=str(job["task_id"]))
    benchmark_python = str(target.benchmark_config.get("python_bin") or target.runner_command).strip()
    base_url = str(target.benchmark_config.get("base_url") or "").strip()
    if not benchmark_python:
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=MINIWOB_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=f"MiniWoB++ benchmark config for {target.machine_id} is missing python_bin/runner_command.",
        )
    if not base_url:
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=MINIWOB_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=f"MiniWoB++ benchmark config for {target.machine_id} is missing base_url.",
        )
    if role["provider"] != MINIWOB_REQUIRED_PROVIDER or (is_smoke_phase(job) and role["model"] != MINIWOB_REQUIRED_MODEL):
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=MINIWOB_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "MiniWoB++ smoke runs are pinned to OpenRouter `openai/gpt-5.4-mini`; "
                f"found provider={role['provider']} model={role['model']}."
            ),
            notes=(
                f"source_bundle={source_bundle_path}",
                "worker expects OPENROUTER_API_KEY from the sourced .env file",
            ),
        )

    repo_src = str(Path(target.remote_workdir) / "src")
    output_dir = _remote_output_dir(target, job)
    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    if is_smoke_phase(job):
        max_steps = int(target.benchmark_config.get("smoke_max_steps") or MINIWOB_DEFAULT_MAX_STEPS)
    else:
        max_steps = int(target.benchmark_config.get("full_max_steps") or MINIWOB_FULL_MAX_STEPS)
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && "
        f"MINIWOB_URL={shlex.quote(base_url)} "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.miniwob_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(source_entry or {})} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--task-id {shlex.quote(str(job['task_id']))} "
        f"--model {shlex.quote(str(role['model']))} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--timeout-seconds {shlex.quote(str(role['timeout_seconds']))} "
        f"--retry {shlex.quote(str(role['retry']))} "
        f"--openrouter-api-key-env {shlex.quote(str(role['api_key_env']))} "
        f"--base-url {shlex.quote(base_url)} "
        f"--max-steps {max_steps} "
        f"--driver {MINIWOB_DEFAULT_DRIVER}"
    )
    notes = [
        f"source_bundle={source_bundle_path}",
        f"source_ref={_source_ref(source_entry) or 'missing'}",
        f"requested_model={role['provider']}::{role['model']}",
        "worker uses BrowserGym MiniWoB++ environments directly and validates with env.unwrapped.task.validate(page, chat_messages)",
        f"worker writes screenshots, page HTML, videos, trajectory, task state, validator I/O, and per-call OpenRouter JSON under {output_dir}",
        f"MiniWoB++ base_url={base_url}",
    ]
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=MINIWOB_EXPECTED_ARTIFACT_TYPES,
        notes=tuple(notes),
    )


def execute_smoke_job(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: dict[str, Any],
    context: "SmokeExecutionContext",
) -> dict[str, Any]:
    paths = build_job_paths(job)
    _ensure_remote_http_server(target, paths.logs_dir)
    sync_repo_support_files(target)
    _, environment_hash = write_environment_snapshot(target=target, job=job, output_path=paths.environment_path)
    shutil.rmtree(paths.native_run_dir, ignore_errors=True)
    paths.native_run_dir.mkdir(parents=True, exist_ok=True)

    remote_output_dir = _remote_output_dir(target, job)
    run_remote_command(
        target,
        f"rm -rf {shlex.quote(remote_output_dir)} && mkdir -p {shlex.quote(remote_output_dir)}",
        stdout_path=paths.logs_dir / "prepare.stdout.log",
        stderr_path=paths.logs_dir / "prepare.stderr.log",
    )
    started_at = utc_now_iso()
    completed = run_remote_command(
        target,
        str(execution_plan["runner_command"]),
        stdout_path=paths.stdout_log,
        stderr_path=paths.stderr_log,
    )
    ended_at = utc_now_iso()
    rsync_remote_tree(target, remote_output_dir, paths.native_run_dir)

    summary_path = paths.native_run_dir / "run_summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"MiniWoB++ worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if _retryable_worker_error(summary):
        raise RuntimeError(str(summary.get("error_message") or "MiniWoB++ worker transient error"))

    llm_path, _ = write_llm_call_logs(
        events=_miniwob_llm_events(paths.native_run_dir),
        job=job,
        context=context,
        output_dir=paths.llm_dir,
    )
    completed_status = summary.get("status") == "completed"
    status = "COMPLETED" if completed_status else "INFRA_EXCLUDED"
    native_label = None
    native_score = None
    if completed_status:
        success = bool(summary.get("success"))
        native_label = "success" if success else "fail"
        native_score = 1.0 if success else 0.0

    descriptors = _miniwob_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
    manifest, manifest_path, manifest_sha = build_artifact_manifest(
        job=job,
        context=context,
        target=target,
        descriptors=descriptors,
        producer_command=str(execution_plan["runner_command"]),
        started_at=started_at,
        output_path=paths.artifact_manifest_path,
        environment_hash=environment_hash,
    )
    raw_run, raw_run_path = build_raw_run(
        job=job,
        target=target,
        artifact_manifest_path=manifest_path,
        artifact_manifest_sha256=manifest_sha,
        raw_run_path=paths.raw_run_path,
        started_at=started_at,
        ended_at=ended_at,
        status=status,
        diagnostic_status="completed" if completed_status else "infra_excluded",
        appendix_failure_class="none" if completed_status else "infra_pre_run",
        native_label=native_label,
        native_score=native_score,
        episode_ids=[f"miniwob:{summary.get('env_id') or job['task_id']}:{job['seed']}"],
        llm_calls_log_path=llm_path,
    )
    return {
        "status": "completed" if completed_status else "infra_excluded",
        "completed_exit_code": completed.returncode,
        "raw_run_path": str(raw_run_path),
        "artifact_manifest_path": str(manifest_path),
        "raw_run": raw_run,
        "artifact_manifest": manifest,
    }


def _remote_output_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/miniwob/{job['job_id']}"


def _bundle_source_entry(source_bundle: Mapping[str, Any], *, task_id: str) -> dict[str, Any] | None:
    for entry in list(source_bundle.get("sources") or []):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        if normalize_domain_or_none(entry.get("domain")) != "miniwob":
            continue
        return dict(entry)
    return None


def _source_ref(source_entry: Mapping[str, Any] | None) -> str | None:
    if not source_entry:
        return None
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return None
    native_sources = list(visible_inputs.get("native_sources") or [])
    if not native_sources:
        return None
    first = native_sources[0]
    if isinstance(first, Mapping) and first.get("source_ref"):
        return str(first["source_ref"])
    return None


def _ensure_remote_http_server(target: "InfraBenchmarkTarget", logs_dir: Path) -> None:
    benchmark = dict(target.benchmark_config or {})
    base_url = str(benchmark.get("base_url") or "").strip()
    http_server_dir = str(benchmark.get("http_server_dir") or "").strip()
    session_name = str(benchmark.get("http_server_session") or "miniwob-http").strip()
    port = int(benchmark.get("http_server_port") or 8787)
    python_bin = str(benchmark.get("python_bin") or target.runner_command).strip()
    if not base_url or not http_server_dir or not python_bin:
        return
    ready_key = (target.machine_id, base_url, http_server_dir, port, session_name)
    with _HTTP_SERVER_LOCK:
        if ready_key in _READY_HTTP_SERVERS:
            return
        probe_url = base_url.rstrip("/") + "/click-test.html"
        command = (
            f"if ! curl -fsS {shlex.quote(probe_url)} >/dev/null; then "
            f"(tmux has-session -t {shlex.quote(session_name)} 2>/dev/null && tmux kill-session -t {shlex.quote(session_name)}) || true; "
            f"tmux new-session -d -s {shlex.quote(session_name)} "
            f"{shlex.quote(f'cd {http_server_dir} && {python_bin} -m http.server {port} --bind 127.0.0.1')}; "
            "sleep 2; "
            f"curl -fsS {shlex.quote(probe_url)} >/dev/null; "
            "fi"
        )
        completed = run_remote_command(
            target,
            command,
            stdout_path=logs_dir / "http_server.stdout.log",
            stderr_path=logs_dir / "http_server.stderr.log",
        )
        if completed.returncode != 0:
            raise RuntimeError(f"failed to ensure MiniWoB++ HTTP server on {target.machine_id}: {probe_url}")
        _READY_HTTP_SERVERS.add(ready_key)


def _miniwob_artifacts(native_run_dir: Path) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    for relative, artifact_type, producer_role, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "adapter", False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True),
        ("run_summary.json", "structured_output", "adapter", False),
        ("artifact_manifest.json", "file", "adapter", False),
        ("job.json", "file", "adapter", False),
        ("source_bundle_entry.json", "file", "adapter", False),
        ("worker_config.json", "file", "adapter", False),
        ("task_context.json", "file", "adapter", False),
        ("browser_artifacts", "browser_artifact", "official_runner", False),
        ("task_artifacts", "post_state", "official_runner", False),
        ("trajectory", "trace", "official_runner", False),
        ("openrouter_calls", "file", "adapter", False),
    ):
        path = native_run_dir / relative
        if not path.exists():
            continue
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role=producer_role,
                producer_name="browsergym-miniwob" if producer_role != "adapter" else "miniwob-worker",
                producer_version="0.14.3" if producer_role != "adapter" else "0.1.0",
                official_runner=producer_role == "official_runner" or official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="miniwob-task-validate" if official_evaluator else None,
                evaluator_version="browsergym-miniwob" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if artifact_type == "native_evaluator_output" else (),
            )
        )
    return tuple(descriptors)


def _miniwob_llm_events(native_run_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted((native_run_dir / "openrouter_calls").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        response_payload = payload.get("response_payload")
        usage = dict(response_payload.get("usage") or {}) if isinstance(response_payload, Mapping) else {}
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        events.append(
            {
                "call_id": str(payload.get("call_id") or path.stem),
                "request_timestamp": str(payload.get("request_timestamp") or utc_now_iso()),
                "response_timestamp": str(payload.get("response_timestamp") or utc_now_iso()),
                "request_payload": payload.get("request_payload"),
                "response_payload": response_payload,
                "error_type": payload.get("error_type"),
                "error_message": payload.get("error_message"),
                "response_metadata": {
                    "transport": "openrouter",
                    "status": "error" if payload.get("error_message") else "success",
                    "action_text": payload.get("action_text"),
                    "python_code": payload.get("python_code"),
                },
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cached_prompt_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }
        )
    return events


def _retryable_worker_error(summary: Mapping[str, Any]) -> bool:
    if str(summary.get("status") or "").lower() != "error":
        return False
    message = str(summary.get("error_message") or "")
    if "OpenRouter HTTP 400" in message or "OpenRouter HTTP 402" in message:
        return False
    return (
        "OpenRouter response content is missing" in message
        or "OpenRouter transport error" in message
        or "IncompleteRead" in message
    )
