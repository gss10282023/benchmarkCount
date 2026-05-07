"""WorkArena Step 8 smoke planner and remote executor."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import shutil
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
from evidence_system.contracts.common import utc_now_iso

if TYPE_CHECKING:
    from evidence_system.adapters.runtime import SmokeExecutionContext
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


ADAPTER = AdapterSkeleton(canonical_domain_id="workarena", supports_direct_execution=True)

WORKARENA_REQUIRED_PROVIDER = "openrouter"
WORKARENA_REQUIRED_MODEL = "openai/gpt-5.4-mini"
WORKARENA_DEFAULT_DRIVER = "openrouter_chat"
WORKARENA_DEFAULT_MAX_STEPS = 6
WORKARENA_EXPECTED_ARTIFACT_TYPES = (
    "browser_artifact",
    "post_state",
    "trace",
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
    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    benchmark_python = f"{install_dir}/.venv/bin/python"
    repo_src = str(Path(target.remote_workdir) / "src")
    output_dir = _remote_output_dir(target, job)

    if role["provider"] != WORKARENA_REQUIRED_PROVIDER or (is_smoke_phase(job) and role["model"] != WORKARENA_REQUIRED_MODEL):
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=WORKARENA_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "WorkArena Step 8 smoke runs are pinned to OpenRouter `openai/gpt-5.4-mini`; "
                f"found provider={role['provider']} model={role['model']}."
            ),
            notes=(
                f"source_bundle={source_bundle_path}",
                "worker expects OPENROUTER_API_KEY from the sourced .env file",
            ),
        )

    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.workarena_worker "
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
        f"--max-steps {WORKARENA_DEFAULT_MAX_STEPS} "
        f"--driver {WORKARENA_DEFAULT_DRIVER}"
    )

    fixed_config = _fixed_config(source_entry)
    source_ref = _source_ref(source_entry)
    notes = [
        f"source_bundle={source_bundle_path}",
        f"source_ref={source_ref}" if source_ref else "source_ref=missing",
        f"requested_model={role['provider']}::{role['model']}",
        "worker uses BrowserGym WorkArena environments directly and validates with env.task.validate(page, chat_messages)",
        f"worker writes browser state, page snapshots, enterprise workflow artifacts, validator I/O, trajectory, and videos under {output_dir}",
        "driver=openrouter_chat uses BrowserGym high-level WorkArena actions; driver=official_cheat is available for fallback/debugging",
    ]
    if is_smoke_phase(job):
        notes.insert(-1, "smoke model is pinned to OpenRouter openai/gpt-5.4-mini via OPENROUTER_API_KEY from .env")
    if fixed_config:
        notes.append(
            "fixed_config="
            + json.dumps(fixed_config, ensure_ascii=True, sort_keys=True)
        )
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=WORKARENA_EXPECTED_ARTIFACT_TYPES,
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
        raise RuntimeError(f"WorkArena worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    llm_path, _ = write_llm_call_logs(
        events=_workarena_llm_events(paths.native_run_dir),
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

    descriptors = _workarena_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
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
        episode_ids=[f"workarena:{summary.get('env_id') or job['task_id']}:{job['seed']}"],
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
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/workarena/{job['job_id']}"


def _bundle_source_entry(source_bundle: Mapping[str, Any], *, task_id: str) -> dict[str, Any] | None:
    for entry in list(source_bundle.get("sources") or []):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        domain = str(entry.get("domain") or "").lower().replace("-", "_")
        if domain != "workarena":
            continue
        return dict(entry)
    return None


def _fixed_config(source_entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not source_entry:
        return None
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return None
    task_text = visible_inputs.get("task_text")
    if isinstance(task_text, Mapping):
        fixed_config = task_text.get("fixed_config")
        if isinstance(fixed_config, Mapping):
            return dict(fixed_config)
        task_kwargs = task_text.get("task_kwargs")
        if isinstance(task_kwargs, Mapping):
            nested = task_kwargs.get("fixed_config")
            if isinstance(nested, Mapping):
                return dict(nested)
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


def _workarena_artifacts(native_run_dir: Path) -> tuple[Any, ...]:
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
                producer_name="browsergym-workarena" if producer_role != "adapter" else "workarena-worker",
                producer_version="0.5.3" if producer_role != "adapter" else "0.1.0",
                official_runner=producer_role == "official_runner" or official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="workarena-task-validate" if official_evaluator else None,
                evaluator_version="browsergym-workarena" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if artifact_type == "native_evaluator_output" else (),
            )
        )
    return tuple(descriptors)


def _workarena_llm_events(native_run_dir: Path) -> list[dict[str, Any]]:
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
