"""AppWorld Step 8 smoke planning helper."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
import shlex
from pathlib import Path
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


ADAPTER = AdapterSkeleton(canonical_domain_id="appworld", supports_direct_execution=True)

APPWORLD_REQUIRED_PROVIDER = "openrouter"
APPWORLD_OFFICIAL_AGENT_NAME = "simplified_react_code_agent"
APPWORLD_OFFICIAL_MAX_STEPS = 50
APPWORLD_OFFICIAL_REPO_URL = "https://github.com/StonyBrookNLP/appworld.git"
APPWORLD_OFFICIAL_REPO_REF = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
APPWORLD_OFFICIAL_REPO_REF_SHORT = APPWORLD_OFFICIAL_REPO_REF[:7]
APPWORLD_EXPECTED_ARTIFACT_TYPES = (
    "trace",
    "database_snapshot",
    "api_log",
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
    install_dir = Path(str(target.benchmark_config.get("install_dir") or target.runner_workdir))
    output_dir = _remote_output_dir(target, job)
    experiment_name = f"{job.get('phase') or 'smoke'}_{job['job_id']}"

    if role["provider"] != APPWORLD_REQUIRED_PROVIDER:
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=APPWORLD_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "AppWorld official simplified_react_code_agent wrapper currently expects "
                f"provider={APPWORLD_REQUIRED_PROVIDER}; found provider={role['provider']} "
                f"model={role['model']}."
            ),
            notes=(
                f"source_bundle={source_bundle_path}",
                "worker delegates to the official AppWorld simplified_react_code_agent",
            ),
        )

    prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
    official_install_dir = install_dir.parent / f"{install_dir.name}-official-{APPWORLD_OFFICIAL_REPO_REF_SHORT}"
    official_root = official_install_dir / "project"
    benchmark_python = official_install_dir / ".venv" / "bin" / "python"
    repo_src = str(Path(target.remote_workdir) / "src")
    ensure_official_agents = _official_bootstrap_command(
        official_install_dir=official_install_dir,
        official_root=official_root,
    )
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && {ensure_official_agents} && "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"APPWORLD_ROOT={shlex.quote(str(official_root))} "
        f"{shlex.quote(str(benchmark_python))} -m evidence_system.adapters.appworld_official_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(source_entry or {})} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--experiment-name {shlex.quote(experiment_name)} "
        f"--provider {shlex.quote(str(role['provider']))} "
        f"--model {shlex.quote(str(role['model']))} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--openrouter-api-key-env {shlex.quote(str(role['api_key_env']))} "
        f"--max-steps {APPWORLD_OFFICIAL_MAX_STEPS}"
    )
    source_ref = _source_ref(source_entry)
    notes = [
        f"source_bundle={source_bundle_path}",
        f"source_ref={source_ref}" if source_ref else "source_ref=missing",
        f"requested_model={role['provider']}::{role['model']}",
        f"worker delegates task execution to the official AppWorld {APPWORLD_OFFICIAL_AGENT_NAME}",
        "official prompt path: experiments/prompts/react_code_agent/instructions.txt",
        f"official max_steps={APPWORLD_OFFICIAL_MAX_STEPS}",
        f"official repo ref: {APPWORLD_OFFICIAL_REPO_REF}",
        f"official install dir: {official_install_dir}",
        f"official APPWORLD_ROOT: {official_root}",
        "official AppWorld 0.2.0 data is downloaded into the isolated official root",
        "bootstraps a dedicated official AppWorld main checkout and venv once under a remote lock",
        "worker fails before any LM request unless code, data, DB schema, and task versions are officially compatible",
        f"worker copies official AppWorld task outputs into {output_dir}/appworld_task_output and writes repo-local manifests under {output_dir}",
        "native artifacts expected: native_evaluator_input.json, native_evaluator_output.json, official_runner_config.json, appworld_task_output/dbs, appworld_task_output/logs/api_calls.jsonl, appworld_task_output/logs/environment_io.md, appworld_task_output/logs/lm_calls.jsonl",
    ]
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=APPWORLD_EXPECTED_ARTIFACT_TYPES,
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
        raise RuntimeError(f"AppWorld worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if completed.returncode != 0 or summary.get("status") == "error":
        raise RuntimeError(
            f"AppWorld worker failed for {job['job_id']} "
            f"exit_code={completed.returncode}: "
            f"{summary.get('error_type') or summary.get('status')}: {summary.get('error_message') or ''}".strip()
        )
    llm_path, _ = write_llm_call_logs(
        events=_appworld_llm_events(paths.native_run_dir),
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
    descriptors = _appworld_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
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
        episode_ids=[f"appworld:{job['task_id']}"],
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
        if domain != "appworld":
            continue
        return dict(entry)
    return None


def _source_ref(source_entry: Mapping[str, Any] | None) -> str | None:
    if not source_entry:
        return None
    explicit = source_entry.get("source_ref")
    if isinstance(explicit, str) and explicit:
        return explicit
    visible_inputs = source_entry.get("visible_inputs")
    if isinstance(visible_inputs, Mapping):
        native_sources = list(visible_inputs.get("native_sources") or [])
        if native_sources and isinstance(native_sources[0], Mapping):
            value = native_sources[0].get("source_ref") or native_sources[0].get("task_dir")
            if value:
                return str(value)
    return None


def _remote_output_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/appworld/{job['job_id']}"


def _official_bootstrap_command(
    *,
    official_install_dir: Path,
    official_root: Path,
) -> str:
    sentinel = official_install_dir / f".official_ready_{APPWORLD_OFFICIAL_REPO_REF_SHORT}"
    commands = [
        f"OFFICIAL_APPWORLD_DIR={shlex.quote(str(official_install_dir))};",
        f"OFFICIAL_APPWORLD_ROOT={shlex.quote(str(official_root))};",
        f"OFFICIAL_APPWORLD_SENTINEL={shlex.quote(str(sentinel))};",
        'OFFICIAL_APPWORLD_LOCKDIR="/tmp/appworld-official-bootstrap.lock";',
        'while ! mkdir "$OFFICIAL_APPWORLD_LOCKDIR" 2>/dev/null; do sleep 2; done;',
        'cleanup_official_appworld_lock(){ rmdir "$OFFICIAL_APPWORLD_LOCKDIR"; };',
        "trap cleanup_official_appworld_lock EXIT;",
        'if [ ! -f "$OFFICIAL_APPWORLD_SENTINEL" ] || [ ! -x "$OFFICIAL_APPWORLD_DIR/.venv/bin/python" ]; then',
        'rm -rf "$OFFICIAL_APPWORLD_DIR";',
        'mkdir -p "$(dirname "$OFFICIAL_APPWORLD_DIR")";',
        "git lfs install >/dev/null 2>&1 || true;",
        f"git clone --depth 1 {shlex.quote(APPWORLD_OFFICIAL_REPO_URL)} \"$OFFICIAL_APPWORLD_DIR\";",
        'cd "$OFFICIAL_APPWORLD_DIR";',
        f"git checkout --detach {shlex.quote(APPWORLD_OFFICIAL_REPO_REF)};",
        "python3 -m venv .venv;",
        '.venv/bin/pip install --upgrade pip setuptools wheel;',
        '.venv/bin/pip install -e .;',
        '.venv/bin/pip install -e "experiments[simplified]";',
        '.venv/bin/appworld install --repo;',
        'touch "$OFFICIAL_APPWORLD_SENTINEL";',
        "fi;",
        'mkdir -p "$OFFICIAL_APPWORLD_ROOT";',
        'mkdir -p "$OFFICIAL_APPWORLD_ROOT/experiments/outputs";',
        'if [ "$(cat "$OFFICIAL_APPWORLD_ROOT/data/version.txt" 2>/dev/null)" != "0.2.0" ] || [ "$(cat "$OFFICIAL_APPWORLD_ROOT/data/base_dbs/version.txt" 2>/dev/null)" != "0.2.0" ] || [ ! -s "$OFFICIAL_APPWORLD_ROOT/data/api_docs/standard/api_docs.json" ]; then',
        '"$OFFICIAL_APPWORLD_DIR/.venv/bin/appworld" download data --version 0.2.0 --root "$OFFICIAL_APPWORLD_ROOT";',
        "fi;",
        "trap - EXIT;",
        'rmdir "$OFFICIAL_APPWORLD_LOCKDIR";',
    ]
    return f"( {' '.join(commands)} )"


def _appworld_artifacts(native_run_dir: Path) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    for relative, artifact_type, producer_role, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "official_runner", False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True),
        ("official_runner_config.json", "file", "official_runner", False),
        ("artifact_manifest.json", "file", "adapter", False),
        ("run_summary.json", "structured_output", "adapter", False),
        ("job.json", "file", "adapter", False),
        ("source_bundle_entry.json", "file", "adapter", False),
        ("worker_config.json", "file", "adapter", False),
    ):
        path = native_run_dir / relative
        if not path.exists():
            continue
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role=producer_role,
                producer_name="appworld" if producer_role != "adapter" else "appworld-worker",
                producer_version="appworld" if producer_role != "adapter" else "0.1.0",
                official_runner=producer_role == "official_runner" or official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="appworld-evaluator" if official_evaluator else None,
                evaluator_version="appworld" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if artifact_type == "native_evaluator_output" else (),
            )
        )
    for relative, artifact_type in (
        ("appworld_task_output/logs/api_calls.jsonl", "api_log"),
        ("appworld_task_output/logs/environment_io.md", "trace"),
        ("appworld_task_output/logs/lm_calls.jsonl", "file"),
        ("appworld_task_output/logs/logger.jsonl", "file"),
        ("appworld_task_output/logs/logger.log", "file"),
        ("appworld_task_output/dbs", "database_snapshot"),
        ("appworld_task_output/evaluation", "file"),
        ("appworld_task_output/version", "file"),
        ("appworld_task_output/misc", "file"),
    ):
        path = native_run_dir / relative
        if not path.exists():
            continue
        from_official_runner = relative.startswith("appworld_task_output")
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role="official_runner" if from_official_runner else "adapter",
                producer_name="appworld" if from_official_runner else "appworld-worker",
                producer_version="appworld" if from_official_runner else "0.1.0",
                official_runner=from_official_runner,
                official_evaluator=False,
            )
        )
    return tuple(descriptors)


def _appworld_llm_events(native_run_dir: Path) -> list[dict[str, Any]]:
    log_path = native_run_dir / "appworld_task_output" / "logs" / "lm_calls.jsonl"
    events: list[dict[str, Any]] = []
    if not log_path.exists():
        return events
    for index, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        prompt = dict(record.get("input") or {})
        response = dict(record.get("output") or {})
        timestamps = dict(response.get("timestamps") or {})
        request_ts = str(timestamps.get("start") or _path_iso(log_path))
        response_ts = str(timestamps.get("end") or request_ts)
        usage = dict(response.get("usage") or {})
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        events.append(
            {
                "call_id": str(record.get("id") or f"appworld-{index:04d}"),
                "request_timestamp": request_ts,
                "response_timestamp": response_ts,
                "request_payload": prompt,
                "response_payload": response,
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


def _path_iso(path: Path, *, floor: str | None = None) -> str:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0)
    if floor is not None:
        floor_dt = datetime.fromisoformat(floor.replace("Z", "+00:00"))
        if timestamp <= floor_dt:
            timestamp = floor_dt + timedelta(seconds=1)
    return timestamp.isoformat()
