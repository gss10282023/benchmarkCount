"""WebArena-Verified planner and executor with a fail-closed official scorer lane."""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import re
import shlex
import shutil
import tempfile
import time
from typing import TYPE_CHECKING, Any, Mapping

from evidence_system.adapters.base import (
    AdapterSkeleton,
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
    job_result_relative_dir,
    rsync_local_file_to_remote,
    rsync_remote_tree,
    run_remote_blind_command,
    run_remote_command,
    sync_repo_support_files,
    write_environment_snapshot,
    write_llm_call_logs,
)
from evidence_system.adapters.webarena_remote_retention import (
    PERSISTENT_RESULTS_ROOT,
    RETENTION_MODE,
)
from evidence_system.contracts.common import utc_now_iso
from evidence_system.core.dotenv import load_project_dotenv
from evidence_system.webarena_sites import (
    RESET_RECEIPT_SCHEMA,
    SlotIdentity,
    WebArenaSiteController,
    WebArenaSiteError,
    load_site_lock,
    pinned_image_reference,
    run_verified_ssh_argv,
    sites_for_agent_input,
)

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
WEB_ARENA_DEFAULT_MAP_URL = "http://127.0.0.1:3030"
WEB_ARENA_DEFAULT_MAX_STEPS = 30
WEB_ARENA_SYNC_PATHS = (
    "src/evidence_system/adapters/webarena_har_sanitization.py",
    "src/evidence_system/adapters/webarena_official_worker.py",
    "src/evidence_system/adapters/webarena_remote_retention.py",
    "src/evidence_system/adapters/webarena_verified.py",
    "src/evidence_system/orchestrator/webarena_verified_pilot_finalization.py",
    "experiments/smoke",
    "experiments/official_splits",
    "experiments/step20/webarena_verified/jobs/full",
    "configs/infra.yaml",
)
WEB_ARENA_SLOT_HARD_TIMEOUT_SECONDS = 2700
WEB_ARENA_CONTROLLER_TIMEOUT_GRACE_SECONDS = 120
WEBARENA_VERIFIED_CASE_PACKET_ROOT = (
    Path(__file__).resolve().parents[3] / "experiments" / "case_packets" / "webarena_verified"
)
WEBARENA_VERIFIED_EVALUATOR_CONFIG = (
    "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json"
)
WEBARENA_VERIFIED_SITE_LOCK = (
    Path(__file__).resolve().parents[3] / "configs" / "webarena_verified_sites.lock.json"
)
WEBARENA_VERIFIED_AGENT_INPUT_FIELDS = {
    "intent",
    "intent_template_id",
    "sites",
    "start_urls",
    "task_id",
}
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PUBLIC_ERROR_CODE_RE = re.compile(r"^[a-z0-9_]{3,96}$")


class WebArenaRemoteControlError(RuntimeError):
    """A bounded remote failure that is safe for controller classification."""

    def __init__(
        self,
        public_error_code: str,
        *,
        remote_runtime_observed: bool = False,
    ) -> None:
        if _PUBLIC_ERROR_CODE_RE.fullmatch(public_error_code) is None:
            public_error_code = "remote_control_failure"
        self.public_error_code = public_error_code
        self.remote_runtime_observed = bool(remote_runtime_observed)
        super().__init__(public_error_code)


def plan_smoke_execution(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    agents_config_path: str,
    dotenv_path: str,
    source_bundle_path: str,
    source_bundle: dict[str, Any],
) -> dict[str, Any]:
    del dotenv_path
    role = smoke_role_config(job, agents_config_path=agents_config_path)
    source_entry = _bundle_source_entry(source_bundle, task_id=str(job["task_id"]))
    case_packet, agent_input = _locked_case_material(task_id=int(job["task_id"]))
    safe_source_entry = {
        "schema_version": "webarena_verified_agent_safe_source/v1",
        "task_id": int(job["task_id"]),
        "agent_input": agent_input,
        "case_packet_sha256": _sha256_file(
            WEBARENA_VERIFIED_CASE_PACKET_ROOT / str(job["task_id"]) / "case_packet.json"
        ),
    }
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
                "worker API key is injected only into the remote process over SSH stdin",
            ),
        )

    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    benchmark_python = str(target.benchmark_config.get("python_bin") or f"{install_dir}/.venv/bin/python")
    repo_src = str(Path(target.remote_workdir) / "src")
    api_key_env = str(role["api_key_env"])
    if _ENV_NAME_RE.fullmatch(api_key_env) is None:
        raise RuntimeError(f"invalid OpenRouter API-key environment name: {api_key_env!r}")
    secret_prefix = (
        "IFS= read -r __evidence_api_key && "
        f"export {api_key_env}=\"$__evidence_api_key\" && "
        "unset __evidence_api_key"
    )
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
    evaluator_config = str(
        target.benchmark_config.get("official_evaluator_config")
        or WEBARENA_VERIFIED_EVALUATOR_CONFIG
    )
    # The pinned Chromium payload is installed beside the official v1.2.3
    # runtime tree, while the worker intentionally runs in the original
    # WebArena runner venv.  Playwright otherwise falls back to root's user
    # cache and auto_login fails even though the accepted browser is present.
    playwright_browsers_path = str(
        Path(evaluator_config).parent.parent / "ms-playwright"
    )

    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {secret_prefix} && "
        "timeout --signal=TERM --kill-after=30s "
        f"{WEB_ARENA_SLOT_HARD_TIMEOUT_SECONDS}s env "
        f"PLAYWRIGHT_BROWSERS_PATH={shlex.quote(playwright_browsers_path)} "
        f"PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.webarena_official_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(safe_source_entry)} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--task-id {shlex.quote(str(job['task_id']))} "
        f"--model-id {shlex.quote(str(role['model']))} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--timeout-seconds {shlex.quote(str(role['timeout_seconds']))} "
        f"--retry {shlex.quote(str(role['retry']))} "
        f"--openrouter-api-key-env {shlex.quote(api_key_env)} "
        f"--shopping-base-url {shlex.quote(shopping_url)} "
        f"--shopping-admin-base-url {shlex.quote(shopping_admin_url)} "
        f"--reddit-base-url {shlex.quote(reddit_url)} "
        f"--gitlab-base-url {shlex.quote(gitlab_url)} "
        f"--wikipedia-base-url {shlex.quote(wikipedia_url)} "
        f"--map-base-url {shlex.quote(map_url)} "
        f"--webarena-repo-dir {shlex.quote(webarena_repo_dir)} "
        f"--task-type {shlex.quote(str(case_packet['task']['task_type']))} "
        f"--task-revision {shlex.quote(str(case_packet['task']['revision']))} "
        f"--official-evaluator-config {shlex.quote(evaluator_config)} "
        f"--max-steps {shlex.quote(str(max_steps))}"
    )
    if _remote_retention_enabled(job):
        adapter_root = _remote_adapter_root(target, job)
        agent_input_path = (
            f"{target.remote_workdir.rstrip('/')}/experiments/case_packets/"
            f"webarena_verified/{job['task_id']}/agent_input.json"
        )
        command += (
            " && "
            f"PYTHONPATH={shlex.quote(repo_src)} "
            "python3 -m "
            "evidence_system.adapters.webarena_remote_retention seal "
            f"--job-json {json_arg(job)} "
            f"--adapter-root {shlex.quote(adapter_root)} "
            f"--active-secret-env {shlex.quote(api_key_env)} "
            f"--agent-input-path {shlex.quote(agent_input_path)} --quiet"
        )
    source_ref = _source_ref(source_entry)
    plan = runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=WEB_ARENA_EXPECTED_ARTIFACT_TYPES,
        notes=(
            f"source_bundle={source_bundle_path}",
            f"source_ref={source_ref}" if source_ref else "source_ref=missing",
            f"requested_model={role['provider']}::{role['model']}",
            "task input is the five-field v1.2.3 agent-input-get allowlist; evaluator-private fields are not sent to the worker or model",
            "the model prompt defines the three public task types, requires self-classification from the public objective, and requires an exact four-field JSON object inside the terminal stop action",
            "runner must emit a full embedded-content network.har and use the pinned WebArena-Verified v1.2.3 eval-tasks image",
            "legacy web-arena-x evaluation_harness output is not accepted by the auditable gate",
        ),
    )
    plan["secret_env_name"] = api_key_env
    plan["secret_transport"] = "ssh_stdin_process_environment_v1"
    if _remote_retention_enabled(job):
        plan["artifact_retention_mode"] = RETENTION_MODE
        plan["remote_adapter_root"] = _remote_adapter_root(target, job)
        plan["full_evidence_sync_to_controller"] = False
    return plan


def _locked_case_material(*, task_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    case_dir = WEBARENA_VERIFIED_CASE_PACKET_ROOT / str(task_id)
    packet_path = case_dir / "case_packet.json"
    agent_input_path = case_dir / "agent_input.json"
    if not packet_path.is_file() or not agent_input_path.is_file():
        raise RuntimeError(f"missing locked WebArena-Verified case packet for task {task_id}")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    agent_input = json.loads(agent_input_path.read_text(encoding="utf-8"))
    if not isinstance(packet, dict) or not isinstance(agent_input, dict):
        raise RuntimeError(f"invalid locked WebArena-Verified case packet for task {task_id}")
    if set(agent_input) != WEBARENA_VERIFIED_AGENT_INPUT_FIELDS:
        raise RuntimeError(f"task {task_id} agent input violates the official field allowlist")
    if int(agent_input.get("task_id", -1)) != task_id:
        raise RuntimeError(f"task {task_id} agent input has a mismatched task ID")
    if int(dict(packet.get("task") or {}).get("task_id", -1)) != task_id:
        raise RuntimeError(f"task {task_id} controller packet has a mismatched task ID")
    visible_ref = dict(packet.get("model_visible_input") or {})
    if visible_ref.get("path") != "agent_input.json":
        raise RuntimeError(f"task {task_id} controller packet has an unsafe visible-input pointer")
    if visible_ref.get("sha256") != _sha256_file(agent_input_path):
        raise RuntimeError(f"task {task_id} agent-input hash does not match its controller packet")
    serialized = json.dumps(agent_input, ensure_ascii=False, sort_keys=True).lower()
    if any(token in serialized for token in ('"expected"', '"eval"', '"reference_answer"', 'sk-or-v1-')):
        raise RuntimeError(f"task {task_id} agent input contains evaluator-private or secret material")
    return packet, agent_input


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _perform_slot_reset(
    job: Mapping[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    receipt_path: str | Path,
) -> dict[str, Any]:
    """Reset the task sites and validate the receipt before any model call."""

    task_id = int(job["task_id"])
    _, agent_input = _locked_case_material(task_id=task_id)
    if job.get("reset_policy") != "recreate_task_sites_from_digest_v1":
        raise RuntimeError("WebArena job is missing the locked per-slot reset policy")
    expected_job_sites = [str(site) for site in agent_input["sites"]]
    if list(job.get("task_sites") or []) != expected_job_sites:
        raise RuntimeError("WebArena job task_sites differ from locked agent_input.json")
    if job.get("reset_receipt_relative_path") != "reset_receipt.json":
        raise RuntimeError("WebArena job reset receipt path is not locked")
    required_identity_fields = ("record_slot_id", "attempt_id", "agent_id", "seed")
    missing = [field for field in required_identity_fields if job.get(field) in (None, "")]
    if missing:
        raise RuntimeError(f"WebArena job reset identity is incomplete: {', '.join(missing)}")

    site_lock = load_site_lock(WEBARENA_VERIFIED_SITE_LOCK)
    controller_config = dict(target.benchmark_config.get("site_controller") or {})
    fingerprint = str(controller_config.get("ssh_host_fingerprint") or "")
    if not fingerprint.startswith("SHA256:"):
        raise RuntimeError("WebArena target has no locked SSH ED25519 fingerprint")
    execution_target = dict(job.get("execution_target") or {})
    if execution_target:
        if str(execution_target.get("ssh_host") or "") != target.ssh_host:
            raise RuntimeError("WebArena job execution_target host differs from resolved target")
        if str(execution_target.get("agent_id") or job["agent_id"]) != str(job["agent_id"]):
            raise RuntimeError("WebArena job execution_target agent differs from slot identity")
        route_fingerprint = str(execution_target.get("ssh_host_ed25519_fingerprint") or "")
        if route_fingerprint and route_fingerprint != fingerprint:
            raise RuntimeError("WebArena job and infra SSH fingerprints differ")

    controller = WebArenaSiteController(
        site_lock=site_lock,
        run_remote=lambda argv, timeout: run_verified_ssh_argv(
            host=target.ssh_host,
            user=target.ssh_user,
            port=target.ssh_port,
            key_path=target.ssh_key_path,
            expected_ed25519_fingerprint=fingerprint,
            argv=argv,
            timeout=timeout,
        ),
        machine_id=target.machine_id,
        ssh_host=target.ssh_host,
        ssh_host_fingerprint=fingerprint,
    )
    expected_sites = sites_for_agent_input(agent_input, expected_task_id=task_id)
    receipt = controller.reset_slot(
        identity=SlotIdentity(
            slot_id=str(job["record_slot_id"]),
            task_id=task_id,
            agent_id=str(job["agent_id"]),
            attempt_id=str(job["attempt_id"]),
            seed=int(job["seed"]),
        ),
        sites=expected_sites,
        receipt_path=receipt_path,
    )
    _validate_slot_reset_receipt(
        receipt,
        job=job,
        target=target,
        expected_sites=expected_sites,
        site_lock=site_lock,
    )
    return receipt


def _perform_slot_reset_with_retry(
    job: Mapping[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    receipt_path: str | Path,
) -> dict[str, Any]:
    """Retry only reset failures proven to precede remote state mutation."""

    delays = (5, 15, 30)
    for attempt in range(len(delays) + 1):
        try:
            return _perform_slot_reset(
                job,
                target=target,
                receipt_path=receipt_path,
            )
        except WebArenaSiteError as exc:
            message = str(exc).lower()
            connection_not_established = "connect to host" in message and any(
                marker in message
                for marker in (
                    "operation timed out",
                    "connection timed out",
                    "connection refused",
                    "no route to host",
                    "network is unreachable",
                )
            )
            retryable = (
                "exclusive-slot-lock-busy" in message
                or "cannot scan ssh ed25519 host key" in message
                or connection_not_established
            )
            if not retryable or attempt == len(delays):
                raise
            time.sleep(delays[attempt])
    raise AssertionError("unreachable reset retry state")


def _validate_slot_reset_receipt(
    receipt: Mapping[str, Any],
    *,
    job: Mapping[str, Any],
    target: "InfraBenchmarkTarget",
    expected_sites: list[str],
    site_lock: Mapping[str, Any],
) -> None:
    if receipt.get("schema_version") != RESET_RECEIPT_SCHEMA or receipt.get("status") != "pass":
        raise RuntimeError("WebArena slot reset receipt is absent, failed, or has the wrong schema")
    expected_slot = {
        "slot_id": str(job["record_slot_id"]),
        "task_id": int(job["task_id"]),
        "agent_id": str(job["agent_id"]),
        "attempt_id": str(job["attempt_id"]),
        "seed": int(job["seed"]),
    }
    if dict(receipt.get("slot") or {}) != expected_slot:
        raise RuntimeError("WebArena slot reset receipt identity differs from the scheduled slot")
    if list(receipt.get("reset_scope") or []) != expected_sites:
        raise RuntimeError("WebArena slot reset receipt scope differs from agent_input sites")
    expected_site_lock_hash = hashlib.sha256(
        json.dumps(
            site_lock,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    if receipt.get("site_lock_sha256") != expected_site_lock_hash:
        raise RuntimeError("WebArena slot reset receipt used a different site lock")
    machine = dict(receipt.get("machine") or {})
    if machine.get("machine_id") != target.machine_id or machine.get("ssh_host") != target.ssh_host:
        raise RuntimeError("WebArena slot reset receipt was produced on the wrong machine")
    fingerprint = str(dict(target.benchmark_config.get("site_controller") or {}).get("ssh_host_fingerprint") or "")
    if machine.get("ssh_host_fingerprint") != fingerprint:
        raise RuntimeError("WebArena slot reset receipt SSH fingerprint differs from infra lock")
    lock = dict(receipt.get("exclusive_lock") or {})
    if not lock.get("acquired_at") or not lock.get("released_at"):
        raise RuntimeError("WebArena slot reset did not hold and release the exclusive remote lock")
    if receipt.get("error") is not None or receipt.get("fail_closed") is not None:
        raise RuntimeError("WebArena slot reset receipt contains a failure marker")

    rows = list(receipt.get("sites") or [])
    if [row.get("site") for row in rows if isinstance(row, Mapping)] != expected_sites:
        raise RuntimeError("WebArena slot reset receipt has missing, duplicate, or reordered site rows")
    for row in rows:
        if not isinstance(row, Mapping) or row.get("ok") is not True:
            raise RuntimeError("WebArena slot reset site row is not successful")
        site = str(row["site"])
        if row.get("image_reference") != pinned_image_reference(site_lock, site):
            raise RuntimeError(f"WebArena slot reset used an unpinned image for {site}")
        before = row.get("before")
        after = row.get("after")
        if not isinstance(after, Mapping) or not after.get("container_id") or after.get("running") is not True:
            raise RuntimeError(f"WebArena slot reset has no running replacement container for {site}")
        if isinstance(before, Mapping) and before.get("container_id") == after.get("container_id"):
            raise RuntimeError(f"WebArena slot reset did not replace the {site} container")
        if after.get("image_id") != row.get("expected_image_id"):
            raise RuntimeError(f"WebArena slot reset container image differs from the pin for {site}")
        sentinels = list(row.get("sentinels") or [])
        if not sentinels or any(not isinstance(check, Mapping) or check.get("ok") is not True for check in sentinels):
            raise RuntimeError(f"WebArena slot reset sentinel failure for {site}")


def execute_smoke_job(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: dict[str, Any],
    context: "SmokeExecutionContext",
) -> dict[str, Any]:
    if _remote_retention_enabled(job):
        return _execute_remote_retention_job(
            job,
            target=target,
            execution_plan=execution_plan,
            context=context,
        )
    paths = build_job_paths(job)
    sync_repo_support_files(
        target,
        paths=WEB_ARENA_SYNC_PATHS,
        include_dotenv=False,
    )
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
    reset_receipt_path = paths.native_run_dir / "reset_receipt.json"
    _perform_slot_reset_with_retry(
        job,
        target=target,
        receipt_path=reset_receipt_path,
    )
    if not reset_receipt_path.is_file():
        raise RuntimeError("WebArena slot reset returned without an atomic receipt")
    secret_env_name = str(execution_plan.get("secret_env_name") or "")
    if _ENV_NAME_RE.fullmatch(secret_env_name) is None:
        raise RuntimeError("WebArena execution plan has no valid secret_env_name")
    api_key = _load_authoritative_api_key(
        dotenv_path=context.dotenv_path,
        secret_env_name=secret_env_name,
    )
    completed = run_remote_command(
        target,
        str(execution_plan["runner_command"]),
        stdout_path=paths.stdout_log,
        stderr_path=paths.stderr_log,
        stdin_text=api_key + "\n",
        timeout_seconds=(
            WEB_ARENA_SLOT_HARD_TIMEOUT_SECONDS
            + WEB_ARENA_CONTROLLER_TIMEOUT_GRACE_SECONDS
        ),
    )
    ended_at = utc_now_iso()
    rsync_remote_tree(target, remote_output_dir, paths.native_run_dir)

    summary_path = paths.native_run_dir / "run_summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"WebArena worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if _retryable_worker_error(summary):
        raise RuntimeError(str(summary.get("error_message") or "WebArena worker transient error"))
    return _finalize_fetched_smoke_job(
        job,
        target=target,
        execution_plan=execution_plan,
        context=context,
        paths=paths,
        environment_hash=environment_hash,
        started_at=started_at,
        ended_at=ended_at,
        completed_exit_code=completed.returncode,
    )


def _execute_remote_retention_job(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: Mapping[str, Any],
    context: "SmokeExecutionContext",
) -> dict[str, Any]:
    """Run and seal a slot while keeping every runtime artifact on the VPS."""

    if execution_plan.get("artifact_retention_mode") != RETENTION_MODE:
        raise RuntimeError("remote-retention execution plan binding is missing")
    paths = build_job_paths(job)
    sync_repo_support_files(
        target,
        paths=WEB_ARENA_SYNC_PATHS,
        include_dotenv=False,
    )
    write_environment_snapshot(
        target=target,
        job=job,
        output_path=paths.environment_path,
        extra_fields={
            "artifact_retention_mode": RETENTION_MODE,
            "full_evidence_synced_to_controller": False,
        },
    )
    adapter_root = _remote_adapter_root(target, job)
    if execution_plan.get("remote_adapter_root") != adapter_root:
        raise RuntimeError("remote adapter root differs from the planned root")
    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    benchmark_python = str(
        target.benchmark_config.get("python_bin") or f"{install_dir}/.venv/bin/python"
    )
    repo_src = f"{target.remote_workdir.rstrip('/')}/src"
    prepare_command = (
        f"cd {shlex.quote(target.remote_workdir)} && "
        f"PYTHONPATH={shlex.quote(repo_src)} {shlex.quote(benchmark_python)} -m "
        "evidence_system.adapters.webarena_remote_retention prepare "
        f"--job-json {json_arg(job)} --adapter-root {shlex.quote(adapter_root)}"
    )
    prepared = run_remote_blind_command(
        target,
        prepare_command,
        timeout_seconds=60,
        maximum_stdout_bytes=4096,
        maximum_stderr_bytes=4096,
    )
    if prepared.returncode != 0 or prepared.stderr:
        raise _remote_control_error(
            prepared.stderr,
            fallback_code="remote_slot_prepare_failed",
        )
    try:
        prepare_receipt = json.loads(prepared.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("VPS persistent slot preparation returned invalid JSON") from exc
    if prepare_receipt.get("status") == "already_sealed":
        _remove_local_remote_retention_dirs(paths)
        verification = _verify_remote_slot_is_canonical(
            job, target=target, adapter_root=adapter_root
        )
        return _remote_retention_result(verification=verification)
    if prepare_receipt.get("status") != "prepared":
        raise RuntimeError("VPS persistent slot preparation did not authorize execution")

    _remove_local_remote_retention_dirs(paths)
    # The reset receipt is controller-generated and is immediately copied to
    # the VPS. It never enters a controller-side runtime-artifact directory.
    with tempfile.TemporaryDirectory(prefix="webarena-reset-") as temporary_dir:
        reset_receipt_path = Path(temporary_dir) / "reset_receipt.json"
        _perform_slot_reset_with_retry(job, target=target, receipt_path=reset_receipt_path)
        if not reset_receipt_path.is_file():
            raise RuntimeError("WebArena slot reset returned without an atomic receipt")
        remote_reset = f"{adapter_root}/native_run/reset_receipt.json"
        rsync_local_file_to_remote(target, reset_receipt_path, remote_reset)

    secret_env_name = str(execution_plan.get("secret_env_name") or "")
    if _ENV_NAME_RE.fullmatch(secret_env_name) is None:
        raise RuntimeError("WebArena execution plan has no valid secret_env_name")
    api_key = _load_authoritative_api_key(
        dotenv_path=context.dotenv_path,
        secret_env_name=secret_env_name,
    )
    remote_stdout = f"{adapter_root}/logs/worker_and_seal.stdout.log"
    remote_stderr = f"{adapter_root}/logs/worker_and_seal.stderr.log"
    sealed_command = (
        "{ "
        + str(execution_plan["runner_command"])
        + "; } >"
        + shlex.quote(remote_stdout)
        + " 2>"
        + shlex.quote(remote_stderr)
    )
    completed = run_remote_blind_command(
        target,
        sealed_command,
        stdin_text=api_key + "\n",
        timeout_seconds=(
            WEB_ARENA_SLOT_HARD_TIMEOUT_SECONDS
            + WEB_ARENA_CONTROLLER_TIMEOUT_GRACE_SECONDS
        ),
        maximum_stdout_bytes=0,
        maximum_stderr_bytes=0,
    )
    if completed.returncode != 0:
        # The SSH command can fail after the paid worker has already written a
        # terminal summary.  Probe the VPS-resident bounded control envelope
        # before classifying the failure; never replay the worker here.
        try:
            observed = _probe_remote_slot(
                job,
                target=target,
                adapter_root=adapter_root,
            )
        except Exception:
            observed = {}
        terminal_code = str(observed.get("terminal_failure_code") or "")
        if observed.get("terminal_failure_observed") is True and terminal_code:
            raise WebArenaRemoteControlError(
                terminal_code,
                remote_runtime_observed=True,
            )
        if observed.get("runtime_completed_unsealed") is True:
            raise WebArenaRemoteControlError(
                "runtime_completed_unsealed",
                remote_runtime_observed=True,
            )
        raise WebArenaRemoteControlError("remote_worker_or_seal_failed")
    verification = _verify_remote_slot_is_canonical(
        job, target=target, adapter_root=adapter_root
    )
    return _remote_retention_result(
        verification=verification,
        completed_exit_code=completed.returncode,
    )


def reconcile_completed_remote_slot(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: Mapping[str, Any],
    context: "SmokeExecutionContext",
) -> dict[str, Any]:
    """Seal a completed remote runtime without reset, browser, or model replay."""

    if execution_plan.get("artifact_retention_mode") != RETENTION_MODE:
        raise RuntimeError("remote-retention reconciliation binding is missing")
    paths = build_job_paths(job)
    sync_repo_support_files(
        target,
        paths=WEB_ARENA_SYNC_PATHS,
        include_dotenv=False,
    )
    adapter_root = _remote_adapter_root(target, job)
    if execution_plan.get("remote_adapter_root") != adapter_root:
        raise RuntimeError("remote adapter root differs from the planned root")
    observed = _probe_remote_slot(job, target=target, adapter_root=adapter_root)
    if observed.get("state") == "canonical_reusable":
        _remove_local_remote_retention_dirs(paths)
        verification = _verify_remote_slot_is_canonical(
            job, target=target, adapter_root=adapter_root
        )
        result = _remote_retention_result(verification=verification)
        result["post_run_reconciliation"] = "already_sealed"
        result["paid_runtime_replayed"] = False
        return result
    if (
        observed.get("status") != "pass"
        or observed.get("state") != "in_progress"
        or observed.get("record_slot_id") != job.get("record_slot_id")
        or observed.get("runtime_completed_unsealed") is not True
    ):
        raise WebArenaRemoteControlError(
            str(observed.get("terminal_failure_code") or "remote_slot_not_reconcilable"),
            remote_runtime_observed=bool(
                observed.get("terminal_failure_observed")
                or observed.get("runtime_completed_unsealed")
            ),
        )

    _remove_local_remote_retention_dirs(paths)

    secret_env_name = str(execution_plan.get("secret_env_name") or "")
    if _ENV_NAME_RE.fullmatch(secret_env_name) is None:
        raise RuntimeError("WebArena execution plan has no valid secret_env_name")
    api_key = _load_authoritative_api_key(
        dotenv_path=context.dotenv_path,
        secret_env_name=secret_env_name,
    )
    repo_src = f"{target.remote_workdir.rstrip('/')}/src"
    agent_input_path = (
        f"{target.remote_workdir.rstrip('/')}/experiments/case_packets/"
        f"webarena_verified/{job['task_id']}/agent_input.json"
    )
    secret_prefix = (
        "IFS= read -r __evidence_api_key && "
        f"export {secret_env_name}=\"$__evidence_api_key\" && "
        "unset __evidence_api_key"
    )
    seal_command = (
        f"cd {shlex.quote(target.remote_workdir)} && {secret_prefix} && "
        f"PYTHONPATH={shlex.quote(repo_src)} python3 -m "
        "evidence_system.adapters.webarena_remote_retention seal "
        f"--job-json {json_arg(job)} --adapter-root {shlex.quote(adapter_root)} "
        f"--active-secret-env {shlex.quote(secret_env_name)} "
        f"--agent-input-path {shlex.quote(agent_input_path)}"
    )
    sealed = run_remote_blind_command(
        target,
        seal_command,
        stdin_text=api_key + "\n",
        timeout_seconds=1800,
        maximum_stdout_bytes=131_072,
        maximum_stderr_bytes=4096,
    )
    if sealed.returncode != 0 or sealed.stderr:
        raise _remote_control_error(
            sealed.stderr,
            fallback_code="remote_post_run_seal_failed",
            remote_runtime_observed=True,
        )
    verification = _verify_remote_slot_is_canonical(
        job, target=target, adapter_root=adapter_root
    )
    result = _remote_retention_result(verification=verification)
    result["post_run_reconciliation"] = "sealed_completed_runtime"
    result["paid_runtime_replayed"] = False
    return result


def _remote_control_error(
    stderr: str | None,
    *,
    fallback_code: str,
    remote_runtime_observed: bool = False,
) -> WebArenaRemoteControlError:
    """Parse only the remote module's content-free JSON error envelope."""

    code = fallback_code
    try:
        payload = json.loads(stderr or "{}")
    except json.JSONDecodeError:
        payload = {}
    if (
        isinstance(payload, Mapping)
        and payload.get("schema_version")
        == "webarena_verified_remote_retention_error/v1"
        and payload.get("status") == "blocked"
        and _PUBLIC_ERROR_CODE_RE.fullmatch(str(payload.get("error_code") or ""))
    ):
        code = str(payload["error_code"])
    return WebArenaRemoteControlError(
        code,
        remote_runtime_observed=remote_runtime_observed,
    )


def _probe_remote_slot(
    job: Mapping[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    adapter_root: str,
) -> dict[str, Any]:
    """Return the bounded VPS verification envelope without fetching evidence."""

    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    benchmark_python = str(
        target.benchmark_config.get("python_bin") or f"{install_dir}/.venv/bin/python"
    )
    repo_src = f"{target.remote_workdir.rstrip('/')}/src"
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && "
        f"PYTHONPATH={shlex.quote(repo_src)} {shlex.quote(benchmark_python)} -m "
        "evidence_system.adapters.webarena_remote_retention verify "
        f"--job-json {json_arg(job)} --adapter-root {shlex.quote(adapter_root)}"
    )
    completed = run_remote_blind_command(
        target,
        command,
        timeout_seconds=900,
        maximum_stdout_bytes=131_072,
        maximum_stderr_bytes=4096,
    )
    if completed.returncode != 0 or completed.stderr:
        raise _remote_control_error(
            completed.stderr,
            fallback_code="remote_slot_verify_failed",
        )
    try:
        verification = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise WebArenaRemoteControlError("remote_slot_verify_invalid_json") from exc
    if not isinstance(verification, dict):
        raise WebArenaRemoteControlError("remote_slot_verify_invalid_envelope")
    return verification


def _remove_local_remote_retention_dirs(paths: Any) -> None:
    """Delete stale controller-side raw directories for a VPS-retained slot."""

    for local_dir in (paths.native_run_dir, paths.logs_dir, paths.llm_dir):
        shutil.rmtree(local_dir, ignore_errors=True)


def _verify_remote_slot_is_canonical(
    job: Mapping[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    adapter_root: str,
) -> dict[str, Any]:
    """Validate the bounded VPS envelope without transferring receipts."""

    verification = _probe_remote_slot(
        job,
        target=target,
        adapter_root=adapter_root,
    )
    if (
        verification.get("status") != "pass"
        or verification.get("state") != "canonical_reusable"
        or verification.get("record_slot_id") != job.get("record_slot_id")
        or verification.get("verified_over_ssh") is not True
    ):
        raise RuntimeError("VPS-resident remote artifact verification did not pass")
    return dict(verification)


def _remote_retention_result(
    *,
    verification: Mapping[str, Any],
    completed_exit_code: int = 0,
) -> dict[str, Any]:
    return {
        "status": "completed",
        "completed_exit_code": completed_exit_code,
        "artifact_retention_mode": RETENTION_MODE,
        "remote_verification": dict(verification),
        "full_evidence_synced_to_controller": False,
        "local_runtime_artifacts_downloaded": False,
        "remote_evidence_retained_on_vps": True,
        "remote_directory_cleanup_performed": False,
    }


def _finalize_fetched_smoke_job(
    job: Mapping[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: Mapping[str, Any],
    context: "SmokeExecutionContext",
    paths: Any,
    environment_hash: str,
    started_at: str,
    ended_at: str,
    completed_exit_code: int,
) -> dict[str, Any]:
    """Seal an already-fetched official run without invoking a model again."""

    summary_path = paths.native_run_dir / "run_summary.json"
    if not summary_path.is_file():
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
    descriptors = _webarena_artifacts(
        paths.native_run_dir,
        job=job,
    ) + default_adapter_artifacts(paths)
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
        "completed_exit_code": completed_exit_code,
        "raw_run_path": str(raw_run_path),
        "artifact_manifest_path": str(manifest_path),
        "raw_run": raw_run,
        "artifact_manifest": manifest,
    }


def _load_authoritative_api_key(
    *, dotenv_path: str | Path, secret_env_name: str
) -> str:
    """Load the explicitly approved project credential over stale inheritance."""

    if _ENV_NAME_RE.fullmatch(secret_env_name) is None:
        raise RuntimeError("WebArena execution has no valid secret environment name")
    # The project dotenv is the explicitly approved credential source for this
    # benchmark. Override any stale controller-process environment inherited
    # before the user replaced the key.
    load_project_dotenv(override=True, paths=(dotenv_path,))
    api_key = os.environ.get(secret_env_name)
    if not api_key:
        raise RuntimeError(
            f"required API key is missing from local environment: {secret_env_name}"
        )
    if any(character in api_key for character in ("\r", "\n", "\x00")):
        raise RuntimeError(
            f"API key contains an unsafe control character: {secret_env_name}"
        )
    return api_key


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
    if _remote_retention_enabled(job):
        return f"{_remote_adapter_root(target, job)}/native_run"
    return f"{target.remote_workdir}/results/{job.get('phase') or 'smoke'}/webarena_verified/{job['job_id']}"


def _remote_adapter_root(
    target: "InfraBenchmarkTarget", job: Mapping[str, Any]
) -> str:
    del target
    relative = job_result_relative_dir(job)
    return str(PERSISTENT_RESULTS_ROOT.joinpath(*relative.parts[1:], "adapter"))


def _remote_retention_enabled(job: Mapping[str, Any]) -> bool:
    return job.get("artifact_retention_mode") == RETENTION_MODE


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


def _artifact_contract_requirement_ids(
    job: Mapping[str, Any] | None,
    artifact_type: str,
) -> tuple[str, ...]:
    if job is None:
        return ()
    contract = job.get("artifact_contract")
    if not isinstance(contract, Mapping):
        return ()
    requirement_ids = {
        str(row.get("contract_requirement_id"))
        for row in list(contract.get("required_artifacts") or [])
        if isinstance(row, Mapping)
        and str(row.get("artifact_type")) == artifact_type
        and row.get("contract_requirement_id")
    }
    return tuple(sorted(requirement_ids))


def _webarena_artifacts(
    native_run_dir: Path,
    *,
    job: Mapping[str, Any] | None = None,
) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    reset_receipt = native_run_dir / "reset_receipt.json"
    if reset_receipt.is_file():
        descriptors.append(
            file_descriptor(
                reset_receipt,
                artifact_type="structured_output",
                producer_role="adapter",
                producer_name="webarena-verified-site-controller",
                producer_version="1.0.0",
                official_runner=False,
                official_evaluator=False,
            )
        )
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
                producer_name=(
                    "webarena-verified-official-worker"
                    if producer_role == "adapter"
                    else "ServiceNow/webarena-verified"
                ),
                producer_version="1.0.0" if producer_role == "adapter" else "1.2.3",
                official_runner=official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="WebArenaVerified.eval-tasks" if official_evaluator else None,
                evaluator_version="1.2.3" if official_evaluator else None,
                artifact_contract_requirement_ids=_artifact_contract_requirement_ids(
                    job, artifact_type
                ),
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
                producer_name="webarena-verified-official-worker",
                producer_version="1.0.0",
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
    for task_dir in sorted(
        path
        for path in native_run_dir.iterdir()
        if path.is_dir() and path.name.isdigit()
    ):
        for relative, artifact_type, producer_role, official_runner, official_evaluator in (
            ("agent_response.json", "structured_output", "adapter", False, False),
            ("network.har", "network_trace", "adapter", False, False),
            ("network_har_sanitization.json", "structured_output", "adapter", False, False),
            ("solver_trace.json", "structured_output", "adapter", False, False),
            ("official_task_config.json", "file", "adapter", False, False),
            ("eval_result.json", "native_evaluator_output", "official_evaluator", True, True),
            ("eval_summary.json", "structured_output", "official_evaluator", True, True),
            ("official_evaluator.stdout.log", "file", "official_runner", True, False),
            ("official_evaluator.stderr.log", "file", "official_runner", True, False),
        ):
            path = task_dir / relative
            if not path.exists():
                continue
            descriptors.append(
                file_descriptor(
                    path,
                    artifact_type=artifact_type,
                    producer_role=producer_role,
                    producer_name=(
                        "ServiceNow/webarena-verified"
                        if producer_role != "adapter"
                        else "webarena-verified-official-worker"
                    ),
                    producer_version="1.2.3" if producer_role != "adapter" else "1.0.0",
                    official_runner=official_runner,
                    official_evaluator=official_evaluator,
                    evaluator_name="WebArenaVerified.eval-tasks" if official_evaluator else None,
                    evaluator_version="1.2.3" if official_evaluator else None,
                    artifact_contract_requirement_ids=(
                        _artifact_contract_requirement_ids(
                            job, "native_evaluator_output"
                        )
                        if official_evaluator
                        else _artifact_contract_requirement_ids(job, artifact_type)
                    ),
                    redaction_status=(
                        "redacted"
                        if relative == "eval_result.json"
                        else "not_needed"
                    ),
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
