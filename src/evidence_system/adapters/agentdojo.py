"""AgentDojo Step 8 smoke planner and executor."""

from __future__ import annotations

import json
import shlex
import shutil
from typing import TYPE_CHECKING, Any, Mapping

from evidence_system.adapters.base import AdapterSkeleton, dotenv_source_prefix, is_smoke_phase, json_arg, runner_plan, smoke_role_config
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
from evidence_system.contracts.common import utc_now_iso

if TYPE_CHECKING:
    from evidence_system.adapters.runtime import SmokeExecutionContext
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


ADAPTER = AdapterSkeleton(canonical_domain_id="agentdojo", supports_direct_execution=True)

AGENTDOJO_REQUIRED_PROVIDER = "openrouter"
AGENTDOJO_REQUIRED_MODEL = "openai/gpt-5.4-mini"
AGENTDOJO_EXPECTED_ARTIFACT_TYPES = (
    "trace",
    "post_state",
    "tool_log",
    "file",
    "message",
    "native_evaluator_output",
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
    case_bits = str(job["case_unit_id"]).split(":")
    suite = case_bits[1] if len(case_bits) >= 2 else "banking"
    user_task = case_bits[2] if len(case_bits) >= 3 else str(job["task_id"])
    injection_task = case_bits[3] if len(case_bits) >= 4 else str(job["task_id"])
    output_dir = _remote_output_dir(target, job)
    source_entry = _bundle_source_entry(source_bundle, task_id=str(job["task_id"]))

    if role["provider"] != AGENTDOJO_REQUIRED_PROVIDER or (is_smoke_phase(job) and role["model"] != AGENTDOJO_REQUIRED_MODEL):
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "AgentDojo Step 8 smoke runs are pinned to OpenRouter `openai/gpt-5.4-mini`; "
                f"found provider={role['provider']} model={role['model']}."
            ),
            notes=(f"source_bundle={source_bundle_path}",),
        )

    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    benchmark_python = f"{install_dir}/.venv/bin/python"
    repo_src = f"{target.remote_workdir}/src"
    model_id = _openrouter_http_model_id(str(role["model"]))
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.agentdojo_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(source_entry or {})} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--suite {shlex.quote(suite)} "
        f"--user-task {shlex.quote(user_task)} "
        f"--injection-task {shlex.quote(injection_task)} "
        f"--benchmark-version v1.2.2 "
        f"--model-id {shlex.quote(model_id)} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--timeout-seconds {shlex.quote(str(role['timeout_seconds']))} "
        f"--retry {shlex.quote(str(role['retry']))} "
        f"--openrouter-api-key-env {shlex.quote(str(role['api_key_env']))} "
        f"--tool-delimiter tool "
        f"--attack direct"
    )
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
        notes=(
            f"source_bundle={source_bundle_path}",
            f"requested_model={role['provider']}::{role['model']}",
            "worker starts a local OpenAI-compatible proxy on the VPS and routes AgentDojo LOCAL calls to OpenRouter",
            "native artifacts expected: native_evaluator_input.json, native_evaluator_output.json, proxy_calls/*.json, trace_logs/**.json",
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
        raise RuntimeError(f"AgentDojo worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if completed.returncode != 0 or summary.get("status") == "error":
        raise RuntimeError(
            f"AgentDojo worker failed for {job['job_id']} "
            f"exit_code={completed.returncode}: {summary.get('error_message') or summary.get('status')}"
        )
    llm_path, _ = write_llm_call_logs(
        events=_agentdojo_llm_events(paths.native_run_dir),
        job=job,
        context=context,
        output_dir=paths.llm_dir,
    )
    status = "COMPLETED" if summary.get("status") == "completed" else "INFRA_EXCLUDED"
    native_label = None
    native_score = None
    if status == "COMPLETED":
        benign_utility = bool(summary.get("benign_utility"))
        injected_utility = bool(summary.get("injected_utility"))
        injected_security = bool(summary.get("injected_security"))
        success = benign_utility and injected_utility and not injected_security
        native_label = "success" if success else "fail"
        native_score = 1.0 if success else 0.0
    descriptors = _agentdojo_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
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
        diagnostic_status="completed" if status == "COMPLETED" else "infra_excluded",
        appendix_failure_class="none" if status == "COMPLETED" else "infra_pre_run",
        native_label=native_label,
        native_score=native_score,
        episode_ids=[
            f"agentdojo:benign:{job['task_id']}",
            f"agentdojo:injected:{job['task_id']}",
        ],
        llm_calls_log_path=llm_path,
    )
    return {
        "status": "completed" if status == "COMPLETED" else "infra_excluded",
        "completed_exit_code": completed.returncode,
        "raw_run_path": str(raw_run_path),
        "artifact_manifest_path": str(manifest_path),
        "raw_run": raw_run,
        "artifact_manifest": manifest,
    }


def _bundle_source_entry(source_bundle: Mapping[str, Any], *, task_id: str) -> dict[str, Any] | None:
    for entry in list(source_bundle.get("sources") or []):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        domain = str(entry.get("domain") or "").lower().replace("-", "_")
        if domain != "agentdojo":
            continue
        return dict(entry)
    return None


def _remote_output_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/agentdojo/{job['job_id']}"


def _openrouter_http_model_id(model_id: str) -> str:
    return model_id.removeprefix("openrouter/")


def _agentdojo_artifacts(native_run_dir: Any) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    for relative, artifact_type, producer_role, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "official_runner", False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True),
        ("run_summary.json", "structured_output", "adapter", False),
        ("job.json", "file", "adapter", False),
        ("source_bundle_entry.json", "file", "adapter", False),
        ("worker_config.json", "file", "adapter", False),
        ("proxy_calls", "file", "adapter", False),
        ("trace_logs", "trace", "official_runner", False),
    ):
        path = native_run_dir / relative
        if not path.exists():
            continue
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role=producer_role,
                producer_name="agentdojo" if producer_role != "adapter" else "agentdojo-worker",
                producer_version="agentdojo" if producer_role != "adapter" else "0.1.0",
                official_runner=producer_role == "official_runner" or official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="agentdojo-benchmark" if official_evaluator else None,
                evaluator_version="agentdojo" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if artifact_type == "native_evaluator_output" else (),
            )
        )
    return tuple(descriptors)


def _agentdojo_llm_events(native_run_dir: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted((native_run_dir / "proxy_calls").glob("*.json")):
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
                "error_message": payload.get("error_message"),
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
