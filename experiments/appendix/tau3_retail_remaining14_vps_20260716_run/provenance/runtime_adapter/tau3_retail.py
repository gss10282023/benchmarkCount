"""tau3 retail smoke planning helper."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import shlex
from typing import TYPE_CHECKING, Any

from evidence_system.adapters.base import AdapterSkeleton, dotenv_source_prefix, json_arg, runner_plan, smoke_role_config
from evidence_system.adapters.runtime import (
    build_artifact_manifest,
    build_job_paths,
    build_raw_run,
    default_adapter_artifacts,
    file_descriptor,
    rsync_remote_tree,
    remote_job_result_dir,
    run_remote_command,
    sync_repo_support_files,
    write_environment_snapshot,
    write_llm_call_logs,
)
from evidence_system.contracts.common import utc_now_iso

if TYPE_CHECKING:
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget
    from evidence_system.adapters.runtime import SmokeExecutionContext


ADAPTER = AdapterSkeleton(canonical_domain_id="tau3_retail", supports_direct_execution=True)


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
    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    agent_model = str(role["model"])
    if role["provider"] == "openrouter" and not agent_model.startswith("openrouter/"):
        agent_model = f"openrouter/{agent_model}"
    user_model = agent_model
    llm_args = json_arg({"temperature": role["temperature"]})
    output_dir = _remote_output_dir(target, job)
    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    uv_binary = str(target.benchmark_config.get("uv_binary") or target.runner_command)
    openrouter_openai_bridge = (
        "export OPENAI_API_KEY=\"${OPENAI_API_KEY:-${OPENROUTER_API_KEY:-}}\" "
        "OPENAI_BASE_URL=\"${OPENAI_BASE_URL:-https://openrouter.ai/api/v1}\" "
        "OPENAI_API_BASE=\"${OPENAI_API_BASE:-https://openrouter.ai/api/v1}\""
    )
    command = (
        f"cd {shlex.quote(install_dir)} && {prefix} && "
        f"{openrouter_openai_bridge} && "
        f"{shlex.quote(uv_binary)} run tau2 run --domain retail --task-ids {shlex.quote(str(job['task_id']))} "
        f"--num-trials 1 --agent llm_agent --agent-llm {shlex.quote(agent_model)} "
        f"--agent-llm-args {llm_args} --user-llm {shlex.quote(user_model)} "
        f"--user-llm-args {llm_args} "
        f"--save-to {shlex.quote(output_dir)} "
        f"--max-concurrency 1 --seed {int(job['seed'])} --log-level INFO --verbose-logs"
    )
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=("tool_log", "trace", "post_state", "native_evaluator_output"),
        notes=(
            f"source_bundle={source_bundle_path}",
            f"requested_model={role['provider']}::{role['model']}",
            "tau3 infra display-name key is normalized from τ³-bench retail -> tau3_retail",
            "both --agent-llm and --user-llm are driven from the selected OpenRouter-backed agent role",
            "OPENAI_API_KEY/OPENAI_BASE_URL are bridged to OpenRouter for tau2 LiteLLM/OpenAI SDK paths",
            f"native runner emits results.json plus artifacts/task_{job['task_id']}/sim_*/{{task.log,llm_debug/*.json,sim_status.json}} under {output_dir}",
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

    results_path = paths.native_run_dir / "results.json"
    if not results_path.exists():
        raise RuntimeError(f"tau3 runner completed without results.json for {job['job_id']}")
    results = json.loads(results_path.read_text(encoding="utf-8"))
    if completed.returncode != 0:
        raise RuntimeError(f"tau3 runner failed for {job['job_id']} exit_code={completed.returncode}")
    summary = _summarize_tau3_results(results)
    llm_path, _ = write_llm_call_logs(
        events=_tau3_llm_events(paths.native_run_dir),
        job=job,
        context=context,
        output_dir=paths.llm_dir,
    )
    descriptors = _tau3_artifacts(paths, summary["has_native_reward"]) + default_adapter_artifacts(paths)
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
        status=summary["status"],
        diagnostic_status=summary["diagnostic_status"],
        appendix_failure_class=summary["appendix_failure_class"],
        native_label=summary["native_label"],
        native_score=summary["native_score"],
        episode_ids=summary["episode_ids"],
        llm_calls_log_path=llm_path,
    )
    return {
        "status": summary["status"].lower(),
        "completed_exit_code": completed.returncode,
        "raw_run_path": str(raw_run_path),
        "artifact_manifest_path": str(manifest_path),
        "raw_run": raw_run,
        "artifact_manifest": manifest,
    }


def _summarize_tau3_results(results: dict[str, Any]) -> dict[str, Any]:
    simulations = list(results.get("simulations") or [])
    if not simulations:
        raise RuntimeError("tau3 results.json has no simulations")
    sim = dict(simulations[0] or {}) if simulations else {}
    if not sim:
        raise RuntimeError("tau3 first simulation is empty")
    reward_info = sim.get("reward_info") if isinstance(sim.get("reward_info"), dict) else None
    termination_reason = str(sim.get("termination_reason") or "")
    if termination_reason == "infrastructure_error":
        return {
            "status": "INFRA_EXCLUDED",
            "diagnostic_status": "infra_excluded",
            "appendix_failure_class": "infra_pre_run",
            "native_label": None,
            "native_score": None,
            "episode_ids": [str(sim.get("id") or sim.get("task_id") or "tau3-episode")],
            "has_native_reward": False,
        }
    if reward_info is None:
        raise RuntimeError("tau3 simulation is missing reward_info")
    native_score = reward_info.get("reward") if reward_info else None
    if isinstance(native_score, bool):
        native_score = 1.0 if native_score else 0.0
    if isinstance(native_score, (int, float)):
        native_label = "success" if float(native_score) > 0 else "fail"
    else:
        raise RuntimeError("tau3 reward_info.reward is missing or non-numeric")
    return {
        "status": "COMPLETED",
        "diagnostic_status": "completed",
        "appendix_failure_class": "none",
        "native_label": native_label,
        "native_score": float(native_score),
        "episode_ids": [str(sim.get("id") or sim.get("task_id") or "tau3-episode")],
        "has_native_reward": True,
    }


def _remote_output_dir(target: "InfraBenchmarkTarget", job: dict[str, Any] | Mapping[str, Any]) -> str:
    return remote_job_result_dir(target, job)


def _tau3_artifacts(paths: Path | Any, has_native_reward: bool) -> tuple[Any, ...]:
    job_paths = paths if isinstance(paths, Path) else paths.native_run_dir
    artifacts: list[Any] = []
    results_path = job_paths / "results.json"
    artifacts.append(
        file_descriptor(
            results_path,
            artifact_type="native_evaluator_output" if has_native_reward else "other",
            producer_role="official_evaluator" if has_native_reward else "official_runner",
            producer_name="tau2-runner",
            producer_version="tau2-bench",
            official_runner=True,
            official_evaluator=has_native_reward,
            evaluator_name="tau2 reward evaluator" if has_native_reward else None,
            evaluator_version="tau2-bench" if has_native_reward else None,
            artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if has_native_reward else (),
        )
    )
    for path in sorted(job_paths.rglob("task.log")):
        artifacts.append(
            file_descriptor(
                path,
                artifact_type="tool_log",
                producer_role="official_runner",
                producer_name="tau2-runner",
                producer_version="tau2-bench",
                official_runner=True,
                official_evaluator=False,
            )
        )
    for path in sorted(job_paths.rglob("sim_status.json")):
        artifacts.append(
            file_descriptor(
                path,
                artifact_type="post_state",
                producer_role="official_runner",
                producer_name="tau2-runner",
                producer_version="tau2-bench",
                official_runner=True,
                official_evaluator=False,
            )
        )
    for path in sorted(job_paths.rglob("llm_debug/*.json")):
        artifacts.append(
            file_descriptor(
                path,
                artifact_type="trace",
                producer_role="official_runner",
                producer_name="tau2-runner",
                producer_version="tau2-bench",
                official_runner=True,
                official_evaluator=False,
            )
        )
    return tuple(artifacts)


def _tau3_llm_events(native_run_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted(native_run_dir.rglob("llm_debug/*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        request = dict(payload.get("request") or {})
        response = dict(payload.get("response") or {})
        usage = dict(response.get("usage") or {})
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        events.append(
            {
                "call_id": str(payload.get("call_id") or path.stem),
                "request_timestamp": str(request.get("timestamp") or payload.get("timestamp") or utc_now_iso()),
                "response_timestamp": str(response.get("timestamp") or payload.get("timestamp") or utc_now_iso()),
                "request_payload": request,
                "response_payload": None,
                "response_metadata": {
                    "transport": "tau2-llm-debug",
                    "status": "success",
                    "provider_response": response,
                    "call_name": payload.get("call_name"),
                },
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cached_prompt_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                "model_version": str(request.get("model") or "openrouter/openai/gpt-5.4-mini"),
            }
        )
    return events
