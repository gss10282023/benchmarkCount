"""AndroidWorld Step 8 smoke planner and local executor."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import shutil
import subprocess
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
    write_environment_snapshot,
    write_llm_call_logs,
)
from evidence_system.contracts.common import utc_now_iso

if TYPE_CHECKING:
    from evidence_system.adapters.runtime import SmokeExecutionContext
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


ADAPTER = AdapterSkeleton(canonical_domain_id="androidworld", supports_direct_execution=True)

ANDROIDWORLD_REQUIRED_PROVIDER = "openrouter"
ANDROIDWORLD_REQUIRED_MODEL = "openai/gpt-5.4-mini"
ANDROIDWORLD_EXPECTED_ARTIFACT_TYPES = (
    "post_state",
    "trace",
    "screenshot",
    "tool_log",
    "message",
    "native_evaluator_input",
    "native_evaluator_output",
    "file",
)


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
    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    output_dir = _worker_output_dir(target, job)
    benchmark_python = _benchmark_python(target)

    if role["provider"] != ANDROIDWORLD_REQUIRED_PROVIDER or (is_smoke_phase(job) and role["model"] != ANDROIDWORLD_REQUIRED_MODEL):
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=ANDROIDWORLD_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "AndroidWorld Step 8 smoke runs are pinned to OpenRouter `openai/gpt-5.4-mini`; "
                f"found provider={role['provider']} model={role['model']}."
            ),
            notes=(
                f"source_bundle={source_bundle_path}",
                "worker expects OPENROUTER_API_KEY from the sourced .env file",
            ),
        )

    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    repo_src = str(Path(target.remote_workdir) / "src")
    task_name = _task_name(job, source_entry)
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.androidworld_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(source_entry or {})} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--install-dir {shlex.quote(install_dir)} "
        f"--task-name {shlex.quote(task_name)} "
        f"--model {shlex.quote(str(role['model']))} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--timeout-seconds {shlex.quote(str(role['timeout_seconds']))} "
        f"--retry {shlex.quote(str(role['retry']))} "
        f"--openrouter-api-key-env {shlex.quote(str(role['api_key_env']))} "
        f"--console-port 5554 "
        f"--grpc-port 8554"
    )
    notes = [
        f"source_bundle={source_bundle_path}",
        f"requested_model={role['provider']}::{role['model']}",
        f"task_name={task_name}",
        "worker uses AndroidWorld package APIs directly: env_launcher.load_and_setup_env, suite_utils.create_suite/run, checkpointer.IncrementalCheckpointer, and t3a.T3A",
        f"worker writes device/system snapshots, checkpoint artifacts, normalized trajectories, observations, actions, messages, and native evaluator payloads under {output_dir}",
        "live runs require an Android emulator/AVD already running with gRPC exposed on port 8554",
    ]
    if is_smoke_phase(job):
        notes.insert(-1, "smoke model is pinned to OpenRouter openai/gpt-5.4-mini via OPENROUTER_API_KEY from .env")
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=ANDROIDWORLD_EXPECTED_ARTIFACT_TYPES,
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
    _, environment_hash = write_environment_snapshot(target=target, job=job, output_path=paths.environment_path)
    shutil.rmtree(paths.native_run_dir, ignore_errors=True)
    paths.native_run_dir.mkdir(parents=True, exist_ok=True)
    worker_output_dir = Path(_worker_output_dir(target, job))
    shutil.rmtree(worker_output_dir, ignore_errors=True)
    worker_output_dir.parent.mkdir(parents=True, exist_ok=True)

    started_at = utc_now_iso()
    completed = _run_local_command(
        str(execution_plan["runner_command"]),
        cwd=target.remote_workdir,
        stdout_path=paths.stdout_log,
        stderr_path=paths.stderr_log,
    )
    ended_at = utc_now_iso()
    if not worker_output_dir.exists():
        raise RuntimeError(f"AndroidWorld worker did not create output directory for {job['job_id']}")
    shutil.copytree(worker_output_dir, paths.native_run_dir, dirs_exist_ok=True)

    summary_path = paths.native_run_dir / "run_summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"AndroidWorld worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    llm_path, _ = write_llm_call_logs(
        events=_androidworld_llm_events(paths.native_run_dir),
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

    descriptors = _androidworld_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
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
        episode_ids=[f"androidworld:{summary.get('task_name') or job['task_id']}:{summary.get('instance_id', 0)}"],
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


def _benchmark_python(target: "InfraBenchmarkTarget") -> str:
    runner_command = str(target.runner_command or "").strip()
    if runner_command:
        parts = shlex.split(runner_command)
        if parts:
            return parts[0]
    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    return f"{install_dir}/.venv311/bin/python"


def _worker_output_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/androidworld/{job['job_id']}/worker_output"


def _bundle_source_entry(source_bundle: Mapping[str, Any], *, task_id: str) -> dict[str, Any] | None:
    for entry in list(source_bundle.get("sources") or []):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        domain = str(entry.get("domain") or "").lower().replace("-", "_")
        if domain != "androidworld":
            continue
        return dict(entry)
    return None


def _task_name(job: Mapping[str, Any], source_entry: Mapping[str, Any] | None) -> str:
    if source_entry:
        visible_inputs = source_entry.get("visible_inputs")
        if isinstance(visible_inputs, Mapping):
            task_text = visible_inputs.get("task_text")
            if isinstance(task_text, Mapping):
                for key in ("task_name", "task_id", "task_template"):
                    value = task_text.get(key)
                    if value:
                        return str(value)
            native_sources = list(visible_inputs.get("native_sources") or [])
            for source in native_sources:
                if not isinstance(source, Mapping):
                    continue
                source_ref = str(source.get("source_ref") or "")
                prefix = "androidworld://"
                if source_ref.startswith(prefix):
                    return source_ref[len(prefix) :]
    return str(job["task_id"])


def _run_local_command(
    command: str,
    *,
    cwd: str | Path,
    stdout_path: str | Path,
    stderr_path: str | Path,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["bash", "-lc", f"set -euo pipefail\n{command}"],
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
    )
    Path(stdout_path).write_text(completed.stdout or "", encoding="utf-8")
    Path(stderr_path).write_text(completed.stderr or "", encoding="utf-8")
    return completed


def _androidworld_artifacts(native_run_dir: Path) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    for relative, artifact_type, producer_role, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "adapter", False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True),
        ("artifact_manifest.json", "file", "adapter", False),
        ("run_summary.json", "structured_output", "adapter", False),
        ("job.json", "file", "adapter", False),
        ("source_bundle_entry.json", "file", "adapter", False),
        ("worker_config.json", "file", "adapter", False),
        ("task_context.json", "file", "adapter", False),
        ("device_state", "post_state", "official_runner", False),
        ("system_state", "file", "adapter", False),
        ("evaluator_artifacts", "trace", "official_runner", False),
        ("trajectories", "trace", "official_runner", False),
        ("observations", "screenshot", "official_runner", False),
        ("actions", "tool_log", "official_runner", False),
        ("messages", "message", "official_runner", False),
        ("post_run_artifacts", "post_state", "official_runner", False),
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
                producer_name="androidworld" if producer_role != "adapter" else "androidworld-worker",
                producer_version="androidworld" if producer_role != "adapter" else "0.1.0",
                official_runner=producer_role == "official_runner" or official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="androidworld-task-evaluator" if official_evaluator else None,
                evaluator_version="androidworld" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if artifact_type == "native_evaluator_output" else (),
            )
        )
    return tuple(descriptors)


def _androidworld_llm_events(native_run_dir: Path) -> list[dict[str, Any]]:
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
                "response_metadata": {"transport": "openrouter", "status": "success" if response_payload else "error"},
                "error_message": payload.get("error_message"),
                "error_type": payload.get("error_type"),
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
