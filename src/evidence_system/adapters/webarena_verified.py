"""WebArena Step 8 planner and executor using the original `web-arena-x/webarena` runtime."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shlex
import shutil
from typing import TYPE_CHECKING, Any, Mapping

from evidence_system.adapters.base import (
    AdapterSkeleton,
    dotenv_source_prefix,
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


ADAPTER = AdapterSkeleton(canonical_domain_id="webarena_verified", supports_direct_execution=True)

WEBARENA_REQUIRED_PROVIDER = "openrouter"
WEB_ARENA_EXPECTED_ARTIFACT_TYPES = (
    "browser_artifact",
    "network_trace",
    "structured_output",
    "native_evaluator_input",
    "native_evaluator_output",
    "file",
)
WEB_ARENA_DEFAULT_SHOPPING_URL = "http://127.0.0.1:7770"
WEB_ARENA_DEFAULT_SHOPPING_ADMIN_URL = "http://127.0.0.1:7780/admin"
WEB_ARENA_DEFAULT_REDDIT_URL = "http://127.0.0.1:9999"
WEB_ARENA_DEFAULT_GITLAB_URL = "http://127.0.0.1:8023"
WEB_ARENA_DEFAULT_WIKIPEDIA_URL = "http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
WEB_ARENA_DEFAULT_MAP_URL = "http://127.0.0.1:3000"
WEB_ARENA_DEFAULT_MAX_STEPS = 30


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
    if role["provider"] != WEBARENA_REQUIRED_PROVIDER:
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=WEB_ARENA_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "WebArena original-run jobs require OpenRouter-backed agents; "
                f"found provider={role['provider']} model={role['model']}."
            ),
            notes=(
                f"source_bundle={source_bundle_path}",
                "worker expects OPENROUTER_API_KEY from the sourced .env file",
            ),
        )

    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    benchmark_python = str(target.benchmark_config.get("python_bin") or f"{install_dir}/.venv/bin/python")
    repo_src = str(Path(target.remote_workdir) / "src")
    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    output_dir = _remote_output_dir(target, job)

    environment = dict(target.benchmark_config.get("environment") or {})
    health_urls = dict(environment.get("health_urls") or {})
    shopping_url = str(health_urls.get("shopping") or WEB_ARENA_DEFAULT_SHOPPING_URL)
    shopping_admin_url = str(health_urls.get("shopping_admin") or WEB_ARENA_DEFAULT_SHOPPING_ADMIN_URL)
    reddit_url = str(health_urls.get("reddit") or WEB_ARENA_DEFAULT_REDDIT_URL)
    gitlab_url = str(health_urls.get("gitlab") or WEB_ARENA_DEFAULT_GITLAB_URL)
    wikipedia_url = str(health_urls.get("wikipedia") or WEB_ARENA_DEFAULT_WIKIPEDIA_URL)
    map_url = str(health_urls.get("map") or WEB_ARENA_DEFAULT_MAP_URL)
    max_steps = int(environment.get("max_steps") or target.benchmark_config.get("max_steps") or WEB_ARENA_DEFAULT_MAX_STEPS)
    webarena_repo_dir = install_dir

    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.webarena_official_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(source_entry or {})} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--task-id {shlex.quote(str(job['task_id']))} "
        f"--model-id {shlex.quote(str(role['model']))} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--timeout-seconds {shlex.quote(str(role['timeout_seconds']))} "
        f"--retry {shlex.quote(str(role['retry']))} "
        f"--openrouter-api-key-env {shlex.quote(str(role['api_key_env']))} "
        f"--shopping-base-url {shlex.quote(shopping_url)} "
        f"--shopping-admin-base-url {shlex.quote(shopping_admin_url)} "
        f"--reddit-base-url {shlex.quote(reddit_url)} "
        f"--gitlab-base-url {shlex.quote(gitlab_url)} "
        f"--wikipedia-base-url {shlex.quote(wikipedia_url)} "
        f"--map-base-url {shlex.quote(map_url)} "
        f"--webarena-repo-dir {shlex.quote(webarena_repo_dir)} "
        f"--max-steps {shlex.quote(str(max_steps))}"
    )
    source_ref = _source_ref(source_entry)
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=WEB_ARENA_EXPECTED_ARTIFACT_TYPES,
        notes=(
            f"source_bundle={source_bundle_path}",
            f"source_ref={source_ref}" if source_ref else "source_ref=missing",
            f"requested_model={role['provider']}::{role['model']}",
            "runner uses the original web-arena-x/webarena repository with its official ScriptBrowserEnv, prompt constructor, render helper, and evaluator router",
            "no expected-answer fallback is allowed for full WebArena runs; used_expected_fallback must remain false",
            "the only custom layer is the OpenRouter transport plus evidence archiving around the official run.py components",
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
        raise RuntimeError(f"WebArena worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if _retryable_worker_error(summary):
        raise RuntimeError(str(summary.get("error_message") or "WebArena worker transient error"))
    llm_path, _ = write_llm_call_logs(
        events=_webarena_llm_events(paths.native_run_dir),
        job=job,
        context=context,
        output_dir=paths.llm_dir,
    )
    status = "COMPLETED" if summary.get("status") == "completed" else "INFRA_EXCLUDED"
    native_label = None
    native_score = None
    if status == "COMPLETED":
        success = bool(summary.get("success"))
        native_label = "success" if success else "fail"
        native_score = 1.0 if success else 0.0
    descriptors = _webarena_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
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
        episode_ids=[f"webarena_verified:{job['task_id']}"],
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
        if domain != "webarena_verified":
            continue
        return dict(entry)
    return None


def _remote_output_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/webarena_verified/{job['job_id']}"


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


def _webarena_artifacts(native_run_dir: Path) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    for relative, artifact_type, producer_role, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "adapter", False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True),
        ("run_summary.json", "structured_output", "adapter", False),
        ("job.json", "file", "adapter", False),
        ("source_bundle_entry.json", "file", "adapter", False),
        ("worker_config.json", "file", "adapter", False),
        ("webarena_env.json", "file", "adapter", False),
    ):
        path = native_run_dir / relative
        if not path.exists():
            continue
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role=producer_role,
                producer_name="webarena-official-worker" if producer_role == "adapter" else "webarena",
                producer_version="0.2.0" if producer_role == "adapter" else "webarena",
                official_runner=official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="webarena" if official_evaluator else None,
                evaluator_version="webarena" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if artifact_type == "native_evaluator_output" else (),
            )
        )
    for relative, artifact_type in (
        ("traces", "browser_artifact"),
        ("llm_attempts", "file"),
        ("official_run", "file"),
    ):
        path = native_run_dir / relative
        if not path.exists():
            continue
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role="adapter",
                producer_name="webarena-official-worker",
                producer_version="0.2.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
    for render_path in sorted(native_run_dir.glob("render_*.html")):
        descriptors.append(
            file_descriptor(
                render_path,
                artifact_type="browser_artifact",
                producer_role="official_runner",
                producer_name="webarena",
                producer_version="run.py",
                official_runner=True,
                official_evaluator=False,
            )
        )
    for task_dir in sorted(path for path in native_run_dir.iterdir() if path.is_dir() and path.name.isdigit()):
        for relative, artifact_type in (
            ("agent_response.json", "structured_output"),
            ("solver_trace.json", "structured_output"),
            ("official_task_config.json", "file"),
        ):
            path = task_dir / relative
            if not path.exists():
                continue
            descriptors.append(
                file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role="adapter",
                producer_name="webarena-official-worker",
                producer_version="0.2.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
    return tuple(descriptors)


def _webarena_llm_events(native_run_dir: Path) -> list[dict[str, Any]]:
    attempts_dir = native_run_dir / "llm_attempts"
    events: list[dict[str, Any]] = []
    for prompt_path in sorted(attempts_dir.glob("*_prompt.json")):
        stem = prompt_path.stem.replace("_prompt", "")
        response_path = attempts_dir / f"{stem}_response.json"
        if not response_path.exists():
            continue
        prompt = json.loads(prompt_path.read_text(encoding="utf-8"))
        response = json.loads(response_path.read_text(encoding="utf-8"))
        request_ts = str(prompt.get("request_timestamp") or _path_iso(prompt_path))
        response_ts = str(response.get("response_timestamp") or _path_iso(response_path, floor=request_ts))
        usage = dict(response.get("usage") or {})
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        response_metadata = {
            "status": "error" if response.get("error_message") else "success",
            "transport": "openrouter",
        }
        if response.get("error_type"):
            response_metadata["error_type"] = str(response["error_type"])
        if response.get("error_message"):
            response_metadata["error_message"] = str(response["error_message"])
        events.append(
            {
                "call_id": f"webarena-{stem}",
                "request_timestamp": request_ts,
                "response_timestamp": response_ts,
                "request_payload": {
                    "model": prompt.get("model"),
                    "messages": prompt.get("messages"),
                    "temperature": prompt.get("temperature"),
                    "max_tokens": prompt.get("max_tokens"),
                },
                "response_payload": response,
                "response_metadata": response_metadata,
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
    return "OpenRouter response content is missing" in message or "OpenRouter transport error" in message


def _path_iso(path: Path, *, floor: str | None = None) -> str:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0)
    if floor is not None:
        floor_dt = datetime.fromisoformat(floor.replace("Z", "+00:00"))
        if timestamp <= floor_dt:
            timestamp = floor_dt + timedelta(seconds=1)
    return timestamp.isoformat()
