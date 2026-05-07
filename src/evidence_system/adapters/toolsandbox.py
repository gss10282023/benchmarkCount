"""ToolSandbox smoke planner and local executor."""

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


ADAPTER = AdapterSkeleton(canonical_domain_id="toolsandbox", supports_direct_execution=True)

TOOLSANDBOX_REQUIRED_PROVIDER = "openrouter"
TOOLSANDBOX_SMOKE_MODEL = "openai/gpt-5.4-mini"
TOOLSANDBOX_DEFAULT_SCENARIO = "cellular_off"
TOOLSANDBOX_EXPECTED_ARTIFACT_TYPES = (
    "trace",
    "tool_log",
    "message",
    "post_state",
    "native_evaluator_input",
    "native_evaluator_output",
    "structured_output",
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
    scenario = _scenario_name(job, source_entry)
    output_dir = _worker_output_dir(target, job)
    benchmark_python = _benchmark_python(target)

    if role["provider"] != TOOLSANDBOX_REQUIRED_PROVIDER or (
        is_smoke_phase(job) and role["model"] != TOOLSANDBOX_SMOKE_MODEL
    ):
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=TOOLSANDBOX_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "ToolSandbox smoke runs are pinned to OpenRouter `openai/gpt-5.4-mini`; "
                f"found provider={role['provider']} model={role['model']}."
            ),
            notes=(
                f"source_bundle={source_bundle_path}",
                "worker expects OPENROUTER_API_KEY from the sourced .env file",
            ),
        )

    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    repo_src = str(Path(target.remote_workdir) / "src")
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.toolsandbox_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(source_entry or {})} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--scenario {shlex.quote(scenario)} "
        f"--model {shlex.quote(str(role['model']))} "
        f"--user-model {shlex.quote(str(role['model']))} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--timeout-seconds {shlex.quote(str(role['timeout_seconds']))} "
        f"--retry {shlex.quote(str(role['retry']))} "
        f"--openrouter-api-key-env {shlex.quote(str(role['api_key_env']))} "
        f"--preferred-tool-backend DEFAULT"
    )
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=TOOLSANDBOX_EXPECTED_ARTIFACT_TYPES,
        notes=(
            f"source_bundle={source_bundle_path}",
            f"requested_model={role['provider']}::{role['model']}",
            f"scenario={scenario}",
            "worker runs Apple ToolSandbox package APIs directly and injects an OpenRouter-backed OpenAI-compatible agent/user role",
            f"worker writes result_summary.json, trajectories/{scenario}/conversation.json, execution_context.json, pretty_print.txt, evaluator payloads, and OpenRouter call captures under {output_dir}",
        ),
    )


def execute_smoke_job(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: dict[str, Any],
    context: "SmokeExecutionContext",
) -> dict[str, Any]:
    paths = build_job_paths(job)
    shutil.rmtree(paths.root, ignore_errors=True)
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
        raise RuntimeError(f"ToolSandbox worker did not create output directory for {job['job_id']}")
    shutil.copytree(worker_output_dir, paths.native_run_dir, dirs_exist_ok=True)

    summary_path = paths.native_run_dir / "run_summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"ToolSandbox worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if completed.returncode != 0 or summary.get("status") == "error":
        raise RuntimeError(
            f"ToolSandbox worker failed for {job['job_id']} "
            f"exit_code={completed.returncode}: "
            f"{summary.get('error_type') or summary.get('status')}: {summary.get('error_message') or ''}".strip()
        )

    llm_path, _ = write_llm_call_logs(
        events=_toolsandbox_llm_events(paths.native_run_dir),
        job=job,
        context=context,
        output_dir=paths.llm_dir,
    )
    completed_status = summary.get("status") == "completed"
    status = "COMPLETED" if completed_status else "INFRA_EXCLUDED"
    native_score = summary.get("similarity")
    native_score_float = float(native_score) if isinstance(native_score, (int, float)) else None
    native_label = None
    if native_score_float is not None:
        native_label = "success" if native_score_float >= 0.999 else "fail"

    descriptors = _toolsandbox_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
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
        native_score=native_score_float,
        episode_ids=[f"toolsandbox:{summary.get('scenario') or job['task_id']}:{job['seed']}"],
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
    return f"{install_dir}/bin/python"


def _worker_output_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/toolsandbox/{job['job_id']}/worker_output"


def _bundle_source_entry(source_bundle: Mapping[str, Any], *, task_id: str) -> dict[str, Any] | None:
    for entry in list(source_bundle.get("sources") or []):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        domain = str(entry.get("domain") or "").lower().replace("-", "_")
        if domain != "toolsandbox":
            continue
        return dict(entry)
    return None


def _scenario_name(job: Mapping[str, Any], source_entry: Mapping[str, Any] | None) -> str:
    if source_entry:
        visible_inputs = source_entry.get("visible_inputs")
        if isinstance(visible_inputs, Mapping):
            task_text = visible_inputs.get("task_text")
            if isinstance(task_text, Mapping) and task_text.get("scenario"):
                return str(task_text["scenario"])
            native_sources = list(visible_inputs.get("native_sources") or [])
            for source in native_sources:
                if not isinstance(source, Mapping):
                    continue
                source_ref = str(source.get("source_ref") or "")
                prefix = "toolsandbox://"
                if source_ref.startswith(prefix):
                    return source_ref[len(prefix) :]
    return str(job.get("task_id") or TOOLSANDBOX_DEFAULT_SCENARIO)


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


def _toolsandbox_artifacts(native_run_dir: Path) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    for relative, artifact_type, producer_role, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "adapter", False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True),
        ("result_summary.json", "native_evaluator_output", "official_evaluator", True),
        ("run_summary.json", "structured_output", "adapter", False),
        ("job.json", "file", "adapter", False),
        ("source_bundle_entry.json", "file", "adapter", False),
        ("worker_config.json", "file", "adapter", False),
        ("scenario_context.json", "file", "adapter", False),
        ("messages.jsonl", "message", "official_runner", False),
        ("tool_calls.jsonl", "tool_log", "official_runner", False),
        ("post_state.json", "post_state", "official_runner", False),
        ("trajectories", "trace", "official_runner", False),
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
                producer_name="toolsandbox" if producer_role != "adapter" else "toolsandbox-worker",
                producer_version="0.0.1" if producer_role != "adapter" else "0.1.0",
                official_runner=producer_role == "official_runner" or official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="toolsandbox-similarity-evaluator" if official_evaluator else None,
                evaluator_version="toolsandbox-0.0.1" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if official_evaluator else (),
            )
        )
    return tuple(descriptors)


def _toolsandbox_llm_events(native_run_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted((native_run_dir / "openrouter_calls").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        response_payload = payload.get("response_payload")
        usage = dict(response_payload.get("usage") or {}) if isinstance(response_payload, Mapping) else {}
        prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        completion_tokens = int(usage.get("completion_tokens", 0) or 0)
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
                    "toolsandbox_role": payload.get("toolsandbox_role"),
                    "attempt": payload.get("attempt"),
                },
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cached_prompt_tokens": int(usage.get("cached_prompt_tokens", 0) or 0),
                    "reasoning_tokens": int(usage.get("reasoning_tokens", 0) or 0),
                    "total_tokens": int(usage.get("total_tokens", prompt_tokens + completion_tokens) or 0),
                },
            }
        )
    return events
