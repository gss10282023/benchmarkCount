"""Step 8 smoke-job planning helpers.

This module intentionally stops at provisional Step 8 planning. It builds
validated `job/v1` payloads for smoke/vertical-slice adapter work without
claiming a full Step 9 scheduler implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from importlib import import_module
import json
import os
from pathlib import Path
import re
import threading
from typing import Any, Callable, Sequence

from evidence_system.adapters.runtime import (
    SmokeExecutionContext,
    build_smoke_execution_context,
    job_result_relative_dir,
    normalize_result_namespace,
)
from evidence_system.contracts.common import (
    load_mapping,
    normalize_domain,
    normalize_domain_or_none,
    utc_now_iso,
    write_json,
)
from evidence_system.contracts.draft import DEFAULT_TAXONOMY_VERSION
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object


_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")

_AGENTDOJO_FULL_RESULT_NAMESPACE = "agentdojo_full_v1.2.2_direct"
_AGENTDOJO_FULL_EXECUTION_STAGING_NAMESPACE = (
    "agentdojo_full_v1.2.2_direct_execution_staging"
)
_AGENTDOJO_FULL_LOCK_SCHEMA_VERSION = "agentdojo_full_experiment_lock/v2"
_AGENTDOJO_FULL_LOCK_REVISION = "checklist-freeze-v1"
_AGENTDOJO_FULL_FREEZE_COUNTS = {
    "case_packets": 949,
    "source_entries": 949,
    "valid_drafts": 949,
    "reviewed": 949,
    "locked": 949,
    "unresolved_drafts": 0,
}
_BLIND_FAILURE_LEDGER_LOCK = threading.Lock()

_WEBARENA_VERIFIED_CASE_PACKET_ROOT = Path("experiments/case_packets/webarena_verified")
_WEBARENA_VERIFIED_TASK_CONTRACT_INDEX = (
    _WEBARENA_VERIFIED_CASE_PACKET_ROOT / "task_contract_index.json"
)
_WEBARENA_VERIFIED_TASK_CONTRACT_INDEX_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
_WEBARENA_VERIFIED_VERSION = "1.2.3"
_WEBARENA_VERIFIED_EVALUATOR_CHECKSUM = (
    "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e"
)
_WEBARENA_VERIFIED_DATA_CHECKSUM = (
    "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
)
_WEBARENA_VERIFIED_RUNTIME_CONFIG_SHA256 = (
    "0b54e748bfed53d23852cb0d0f2b54b8a405b8e035b560ff86f3632e7c84f673"
)
_WEBARENA_VERIFIED_EVALUATOR_IMAGE = (
    "ghcr.io/servicenow/webarena-verified@"
    "sha256:d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
)
_WEBARENA_RUNNER_KIND = "project_selected_webarena_dce04686_with_verified_v1_2_3_scorer"
_WEBARENA_ALLOWED_EVALUATORS = frozenset(
    {"AgentResponseEvaluator", "NetworkEventEvaluator"}
)
_WEBARENA_RESULT_STATUSES = frozenset({"success", "failure", "error"})
_WEBARENA_AGENT_INPUT_FIELDS = {
    "intent",
    "intent_template_id",
    "sites",
    "start_urls",
    "task_id",
}
_WEBARENA_FULL_HAR_ENTRY_FIELDS = frozenset(
    {"startedDateTime", "time", "request", "response", "cache", "timings"}
)
_WEBARENA_FULL_HAR_REQUEST_FIELDS = frozenset(
    {
        "method",
        "url",
        "httpVersion",
        "cookies",
        "headers",
        "queryString",
        "headersSize",
        "bodySize",
    }
)
_WEBARENA_FULL_HAR_RESPONSE_FIELDS = frozenset(
    {
        "status",
        "statusText",
        "httpVersion",
        "cookies",
        "headers",
        "content",
        "redirectURL",
        "headersSize",
        "bodySize",
    }
)


@dataclass(frozen=True)
class InfraBenchmarkTarget:
    machine_id: str
    machine_role: str
    ssh_host: str
    ssh_user: str
    ssh_port: int
    ssh_key_path: str
    remote_workdir: str
    runner_workdir: str
    benchmark_name: str
    benchmark_config: dict[str, Any]
    benchmark_config_hash: str
    runner_command: str
    machine_concurrency: int
    ssh_known_hosts_file: str | None = None
    ssh_host_ed25519_fingerprint: str | None = None


@dataclass(frozen=True)
class PlannedJob:
    job: dict[str, Any]
    job_path: Path
    official_split_hash: str
    execution_plan: dict[str, Any]


@dataclass(frozen=True)
class ExecutedJob:
    planned: PlannedJob
    execution_result: dict[str, Any]


JobProgressCallback = Callable[[PlannedJob, dict[str, Any], int, int], None]


def plan_smoke_jobs(
    *,
    domain: str,
    phase: str,
    experiment_type: str,
    case_count: int | None,
    agent_ids: list[str],
    seed: int,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    contracts_dir: str | Path,
    infra_config_path: str | Path,
    agents_config_path: str | Path,
    jobs_dir: str | Path,
    result_namespace: str | None = None,
    execution_lock_path: str | Path | None = None,
) -> list[PlannedJob]:
    manifest = load_mapping(manifest_path)
    validate_object("experiment_manifest", manifest, raise_on_error=True)
    result_namespace = resolve_result_namespace(
        manifest=manifest,
        requested=result_namespace,
        execution_lock_path=execution_lock_path,
    )
    execution_binding: dict[str, Any] | None = None
    if result_namespace is not None:
        execution_binding = validate_namespaced_manifest_inputs(
            manifest=manifest,
            manifest_path=manifest_path,
            source_bundle_path=source_bundle_path,
            infra_config_path=infra_config_path,
            agents_config_path=agents_config_path,
            phase=phase,
            experiment_type=experiment_type,
            execution_lock_path=execution_lock_path,
        )
    bundle = load_mapping(source_bundle_path)
    infra = load_mapping(infra_config_path)
    target = resolve_infra_target(domain, infra)
    # Raw execution is intentionally independent from the concurrently edited
    # checklist workspace.  The later pre-score join lock is the first point at
    # which checklist artifacts may be combined with sealed evidence.
    contract_index = (
        {} if execution_binding is not None else load_contract_index(contracts_dir)
    )
    domain_key = normalize_domain(domain)
    domain_contracts = contract_index.get(domain_key, {})
    domain_block = _manifest_domain_block(manifest, domain_key)
    declared_experiment_type = str(domain_block.get("experiment_type") or "")
    if experiment_type != declared_experiment_type:
        raise ValueError(
            f"{domain_key}: requested experiment_type does not match manifest: "
            f"requested={experiment_type!r} manifest={declared_experiment_type!r}"
        )
    available_cases = list(domain_block.get("case_units") or [])
    if case_count is None:
        selected_cases = available_cases
    else:
        if case_count <= 0:
            raise ValueError(
                "case_count must be greater than zero or omitted to select all manifest cases"
            )
        if case_count > len(available_cases):
            raise ValueError(
                f"{domain_key}: requested {case_count} cases but manifest contains only {len(available_cases)}"
            )
        selected_cases = available_cases[:case_count]
    manifest_hash = sha256_file(resolve_repo_path(manifest_path))
    agents_hash = sha256_file(resolve_repo_path(agents_config_path))
    jobs_root = resolve_repo_path(jobs_dir)
    jobs_root.mkdir(parents=True, exist_ok=True)

    planned: list[PlannedJob] = []
    for case_index, case_ref in enumerate(selected_cases, start=1):
        case_unit_id = str(case_ref["case_unit_id"])
        task_id = str(case_ref["task_id"])
        contract = domain_contracts.get(case_unit_id)
        phase_contract_prefix = _safe_id(str(phase or "run"))
        contract_id = str(
            contract.get("contract_id")
            if contract
            else f"{phase_contract_prefix}-{domain_key}-{_safe_id(case_unit_id)}"
        )
        contract_version = str(
            contract.get("contract_version") if contract else "1.0.0"
        )
        contract_hash = str(
            contract.get("contract_hash")
            if contract
            else sha256_object({"case_unit_id": case_unit_id, "domain": domain_key})
        )
        taxonomy_version = str(
            contract.get("taxonomy_version") if contract else DEFAULT_TAXONOMY_VERSION
        )
        artifact_contract = {
            "required_artifacts": list(contract.get("required_artifacts") or [])
            if contract
            else [],
        }
        for agent_index, agent_id in enumerate(agent_ids, start=1):
            safe_case = _safe_id(case_unit_id)
            safe_agent = _safe_id(agent_id.lower().replace(" ", "_"))
            job_id = f"{phase}-{domain_key}-{safe_case}-{safe_agent}"
            record_slot_id = f"slot-{domain_key}-{safe_case}-{safe_agent}"
            run_id = f"run-{domain_key}-{safe_case}-{safe_agent}"
            attempt_id = f"attempt-{domain_key}-{safe_case}-{safe_agent}"
            job_payload = {
                "schema_version": "job/v1",
                "job_id": job_id,
                "domain": domain_key,
                "domain_display_name": str(
                    domain_block.get("domain_display_name") or target.benchmark_name
                ),
                "benchmark_name": str(
                    domain_block.get("domain_display_name") or target.benchmark_name
                ),
                "case_unit_id": case_unit_id,
                "task_id": task_id,
                "record_slot_id": record_slot_id,
                "run_id": run_id,
                "attempt_id": attempt_id,
                "final_attempt": True,
                "seed": (
                    seed + case_index - 1
                    if execution_binding is not None
                    else seed + case_index + agent_index - 2
                ),
                "agent_id": agent_id,
                "phase": phase,
                "experiment_type": experiment_type,
                "priority": str(domain_block["priority"]),
                "adapter_module": f"evidence_system.adapters.{domain_key}",
                "agent_config_hash": agents_hash,
                "benchmark_config_hash": target.benchmark_config_hash,
                "manifest_hash": manifest_hash,
                "evidence_contract_id": contract_id,
                "evidence_contract_version": contract_version,
                "evidence_contract_hash": contract_hash,
                "contract_id": contract_id,
                "contract_version": contract_version,
                "contract_hash": contract_hash,
                "taxonomy_version": taxonomy_version,
                "artifact_contract": artifact_contract,
                "deterministic_selection": dict(manifest["deterministic_selection"]),
            }
            if result_namespace is not None:
                job_payload["result_namespace"] = result_namespace
            if execution_binding is not None:
                definition = dict(execution_binding["lock"]["definition"])
                job_payload.update(
                    {
                        "execution_lock_path": str(execution_binding["lock_path"]),
                        "execution_lock_sha256": str(execution_binding["lock_sha256"]),
                        "execution_policy_sha256": str(
                            definition["execution_policy_sha256"]
                        ),
                        "openrouter_runtime_policy": dict(
                            execution_binding["runtime_policy"]
                        ),
                        "openrouter_runtime_policy_sha256": str(
                            definition["rate_limit_policy"][
                                "runtime_policy_semantic_sha256"
                            ]
                        ),
                        "openrouter_runtime_policy_file_sha256": str(
                            definition["runtime_policy"]["sha256"]
                        ),
                    }
                )
                execution_binding["module"].verify_job_binding(
                    job_payload,
                    execution_binding["lock"],
                    lock_path=execution_binding["lock_path"],
                    lock_sha256=execution_binding["lock_sha256"],
                )
            validate_object("job", job_payload, raise_on_error=True)
            job_path = jobs_root / f"{job_id}.json"
            write_json(job_path, job_payload)
            execution_plan = plan_adapter_execution(
                job_payload,
                target=target,
                agents_config_path=agents_config_path,
                dotenv_path=".env",
                source_bundle_path=source_bundle_path,
                bundle=bundle,
            )
            planned.append(
                PlannedJob(
                    job=job_payload,
                    job_path=job_path,
                    official_split_hash=str(
                        domain_block.get("official_split_hash") or "0" * 64
                    ),
                    execution_plan=execution_plan,
                )
            )
    if execution_binding is not None:
        locked_entries = list(
            dict(execution_binding["lock"]["definition"]["job_plan"])["entries"]
        )
        locked_order = {
            (str(entry["case_unit_id"]), str(entry["agent_id"])): index
            for index, entry in enumerate(locked_entries)
        }
        planned.sort(
            key=lambda item: locked_order[
                (str(item.job["case_unit_id"]), str(item.job["agent_id"]))
            ]
        )
    return planned


def execute_smoke_jobs(
    *,
    domain: str,
    phase: str,
    experiment_type: str,
    case_count: int | None,
    agent_ids: list[str],
    seed: int,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    contracts_dir: str | Path,
    infra_config_path: str | Path,
    agents_config_path: str | Path,
    jobs_dir: str | Path,
    result_namespace: str | None = None,
    execution_lock_path: str | Path | None = None,
) -> list[ExecutedJob]:
    planned = plan_smoke_jobs(
        domain=domain,
        phase=phase,
        experiment_type=experiment_type,
        case_count=case_count,
        agent_ids=agent_ids,
        seed=seed,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        contracts_dir=contracts_dir,
        infra_config_path=infra_config_path,
        agents_config_path=agents_config_path,
        jobs_dir=jobs_dir,
        result_namespace=result_namespace,
        execution_lock_path=execution_lock_path,
    )
    return execute_planned_jobs(
        planned,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        infra_config_path=infra_config_path,
        agents_config_path=agents_config_path,
    )


def execute_planned_jobs(
    planned: Sequence[PlannedJob],
    *,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    infra_config_path: str | Path,
    agents_config_path: str | Path,
    max_workers: int | None = None,
    progress_callback: JobProgressCallback | None = None,
    fail_fast_on_noncompleted: bool = False,
    skip_completed: bool = False,
    retry_no_response_attempts: int = 0,
    continue_on_error: bool | None = None,
) -> list[ExecutedJob]:
    if not planned:
        return []
    domains = {str(item.job["domain"]) for item in planned}
    if len(domains) != 1:
        raise ValueError(
            f"execute_planned_jobs expects exactly one domain batch, found: {sorted(domains)}"
        )
    domain = next(iter(domains))
    manifest_hash = sha256_file(resolve_repo_path(manifest_path))
    source_bundle_hash = sha256_file(resolve_repo_path(source_bundle_path))
    target = resolve_infra_target(domain, load_mapping(infra_config_path))
    context = build_smoke_execution_context(
        manifest_path=manifest_path,
        manifest_hash=manifest_hash,
        source_bundle_path=source_bundle_path,
        source_bundle_hash=source_bundle_hash,
        official_split_hash=planned[0].official_split_hash,
        agents_config_path=agents_config_path,
        dotenv_path=".env",
    )
    bound_execution = _verify_bound_execution_policy(planned)
    effective_continue_on_error = bool(continue_on_error)
    if bound_execution is not None:
        failure_policy = dict(bound_execution["definition"]["failure_policy"])
        locked_continue = bool(failure_policy["continue_on_job_error"])
        if continue_on_error is not None and bool(continue_on_error) != locked_continue:
            raise ValueError(
                "continue_on_error differs from the published execution lock"
            )
        effective_continue_on_error = locked_continue
        if int(retry_no_response_attempts) != int(
            failure_policy["retry_transient_model_attempts"]
        ):
            raise ValueError(
                "retry_no_response_attempts differs from the published execution lock"
            )
        if skip_completed is not True:
            raise ValueError(
                "execution lock requires skip_completed=True; completed evidence must not be rerun"
            )

    def _execute(item: PlannedJob) -> ExecutedJob:
        if skip_completed:
            existing_result = _existing_completed_result(item, context=context)
            if existing_result is not None:
                return ExecutedJob(planned=item, execution_result=existing_result)
        executor = getattr(
            import_module(str(item.job["adapter_module"])), "execute_smoke_job", None
        )
        if executor is None:
            raise ValueError(
                f"{item.job['adapter_module']} has no execute_smoke_job() helper"
            )
        if item.execution_plan.get("status") == "blocked":
            raise ValueError(
                f"{item.job['job_id']} is blocked: {item.execution_plan.get('blocking_reason')}"
            )
        attempts_used = 0
        while True:
            try:
                result = dict(
                    executor(
                        item.job,
                        target=target,
                        execution_plan=item.execution_plan,
                        context=context,
                    )
                )
                if attempts_used:
                    result["retry_no_response_attempts"] = attempts_used
                    result["retry_transient_model_attempts"] = attempts_used
                return ExecutedJob(planned=item, execution_result=result)
            except Exception as exc:
                if attempts_used >= max(0, int(retry_no_response_attempts)):
                    raise
                if not _is_retryable_transient_model_failure(item, exc):
                    raise
                attempts_used += 1

    worker_limit = max(1, int(target.machine_concurrency or 1))
    if max_workers is not None:
        worker_limit = min(worker_limit, max(1, int(max_workers)))
    if normalize_domain(domain) == "webarena_verified":
        worker_limit = min(worker_limit, 1)
    effective_workers = min(len(planned), worker_limit)
    if bound_execution is not None:
        ramp = list(bound_execution["definition"]["concurrency_policy"]["ramp_workers"])
        if effective_workers not in ramp and effective_workers != len(planned):
            raise ValueError(
                f"effective worker count {effective_workers} is outside locked ramp {ramp}"
            )
    total = len(planned)

    if effective_workers <= 1:
        ordered: list[ExecutedJob] = []
        for completed_count, item in enumerate(planned, start=1):
            try:
                result = _execute(item)
                _raise_for_noncompleted(
                    item, result, context=context, enabled=fail_fast_on_noncompleted
                )
            except Exception as exc:
                if not effective_continue_on_error:
                    raise
                result = _blind_failed_execution(
                    item,
                    exc,
                    bound_execution=bound_execution,
                    retry_no_response_attempts=retry_no_response_attempts,
                )
            ordered.append(result)
            if progress_callback is not None:
                progress_callback(item, result.execution_result, completed_count, total)
        return ordered

    ordered: dict[str, ExecutedJob] = {}
    completed_count = 0
    with ThreadPoolExecutor(
        max_workers=effective_workers, thread_name_prefix=f"step8-{target.machine_role}"
    ) as pool:
        pending_items = iter(planned)
        futures = {}

        def _submit_next() -> None:
            try:
                item = next(pending_items)
            except StopIteration:
                return
            futures[pool.submit(_execute, item)] = item

        for _ in range(effective_workers):
            _submit_next()

        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                item = futures.pop(future)
                try:
                    result = future.result()
                    _raise_for_noncompleted(
                        item, result, context=context, enabled=fail_fast_on_noncompleted
                    )
                except Exception as exc:
                    if not effective_continue_on_error:
                        for pending in futures:
                            pending.cancel()
                        raise
                    result = _blind_failed_execution(
                        item,
                        exc,
                        bound_execution=bound_execution,
                        retry_no_response_attempts=retry_no_response_attempts,
                    )
                ordered[str(item.job["job_id"])] = result
                completed_count += 1
                if progress_callback is not None:
                    progress_callback(
                        item, result.execution_result, completed_count, total
                    )
                _submit_next()
    return [ordered[str(item.job["job_id"])] for item in planned]


def _verify_bound_execution_policy(
    planned: Sequence[PlannedJob],
) -> dict[str, Any] | None:
    bound = [item for item in planned if item.job.get("execution_lock_sha256")]
    if not bound:
        return None
    if len(bound) != len(planned):
        raise ValueError("a batch cannot mix execution-locked and legacy jobs")
    lock_paths = {str(item.job.get("execution_lock_path") or "") for item in bound}
    lock_hashes = {str(item.job.get("execution_lock_sha256") or "") for item in bound}
    policy_hashes = {
        str(item.job.get("execution_policy_sha256") or "") for item in bound
    }
    if len(lock_paths) != 1 or "" in lock_paths:
        raise ValueError("execution-locked batch must reference exactly one lock path")
    if len(lock_hashes) != 1 or "" in lock_hashes:
        raise ValueError("execution-locked batch must reference exactly one lock hash")
    if len(policy_hashes) != 1 or "" in policy_hashes:
        raise ValueError("execution-locked batch must reference exactly one policy hash")

    execution_module = import_module(
        "evidence_system.contracts.agentdojo_full_execution"
    )
    verified = execution_module.verify_execution_lock(lock_path=next(iter(lock_paths)))
    if verified.lock_sha256 != next(iter(lock_hashes)):
        raise ValueError("planned job execution_lock_sha256 is stale")
    lock = load_mapping(verified.lock_path)
    definition = dict(lock["definition"])
    if definition.get("execution_policy_sha256") != next(iter(policy_hashes)):
        raise ValueError("planned job execution_policy_sha256 is stale")
    for item in bound:
        execution_module.verify_job_binding(
            item.job,
            lock,
            lock_path=verified.lock_path,
            lock_sha256=verified.lock_sha256,
        )
    return {
        "module": execution_module,
        "lock": lock,
        "lock_path": str(verified.lock_path),
        "lock_sha256": verified.lock_sha256,
        "definition": definition,
    }


def _blind_failed_execution(
    item: PlannedJob,
    exc: BaseException,
    *,
    bound_execution: dict[str, Any] | None,
    retry_no_response_attempts: int,
) -> ExecutedJob:
    """Persist operations-only failure metadata without exposing case evidence."""

    message = str(exc)
    error_digest = sha256_object(
        {"exception_type": type(exc).__name__, "message": message}
    )
    identity_digest = sha256_object(
        {
            "job_id": item.job.get("job_id"),
            "case_unit_id": item.job.get("case_unit_id"),
            "agent_id": item.job.get("agent_id"),
            "attempt_id": item.job.get("attempt_id"),
        }
    )
    timestamp = utc_now_iso()
    incident_id = sha256_object(
        {
            "job_identity_sha256": identity_digest,
            "error_detail_sha256": error_digest,
            "timestamp": timestamp,
        }
    )
    if bound_execution is not None:
        failure_policy = dict(bound_execution["definition"]["failure_policy"])
        ledger_path = resolve_repo_path(failure_policy["blind_failure_ledger_path"])
    else:
        ledger_path = resolve_repo_path(
            "results/logs/job_execution_failures.blind.jsonl"
        )
    record = {
        "schema_version": "agentdojo_job_execution_failure_blind/v1",
        "timestamp": timestamp,
        "event_type": "job_failure",
        "incident_id": incident_id,
        "job_identity_sha256": identity_digest,
        "error_category": _blind_error_category(message),
        "exception_type": type(exc).__name__,
        "error_detail_sha256": error_digest,
        "retryable_transient_model_failure": _is_retryable_transient_model_failure(
            item, Exception(message)
        ),
        "retry_attempts_configured": int(retry_no_response_attempts),
        "execution_lock_sha256": item.job.get("execution_lock_sha256"),
        "execution_policy_sha256": item.job.get("execution_policy_sha256"),
        "blind_health_fields_only": True,
        "contains_case_prompt_trajectory_evaluator_or_label": False,
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    with _BLIND_FAILURE_LEDGER_LOCK:
        with ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    return ExecutedJob(
        planned=item,
        execution_result={
            "status": "failed_recorded",
            "incident_id": incident_id,
            "error_category": record["error_category"],
            "blind_failure_ledger_path": str(ledger_path),
            "blind_health_fields_only": True,
        },
    )


def _blind_error_category(message: str) -> str:
    lowered = message.lower()
    if "http 429" in lowered or "rate limit" in lowered:
        return "rate_limit"
    if "http 402" in lowered or "credit" in lowered or "budget" in lowered:
        return "budget_or_credit"
    if "http 401" in lowered or "http 403" in lowered or "api key" in lowered:
        return "authentication"
    if any(marker.lower() in lowered for marker in _TRANSIENT_JOB_CONNECTION_MARKERS):
        return "transport_or_ssh"
    if "no response from model" in lowered or "response content is missing" in lowered:
        return "model_no_response"
    if "post-run artifact audit" in lowered:
        return "post_run_artifact_audit"
    return "unclassified_runtime"


_TRANSIENT_JOB_CONNECTION_MARKERS = (
    "connection closed",
    "connection reset",
    "broken pipe",
    "connection timed out",
    "incompleteread",
)


def _raise_for_noncompleted(
    item: PlannedJob,
    result: ExecutedJob,
    *,
    context: SmokeExecutionContext,
    enabled: bool,
) -> None:
    if not enabled:
        return
    status = str(result.execution_result.get("status") or "unknown")
    if status == "skipped_completed":
        return
    if status != "completed":
        raise RuntimeError(
            f"{item.job['job_id']} returned non-completed status: {status}"
        )
    if _existing_completed_result(item, context=context) is None:
        raise RuntimeError(
            f"{item.job['job_id']} completed but failed post-run artifact audit"
        )


def _is_retryable_transient_model_failure(item: PlannedJob, exc: Exception) -> bool:
    message = str(exc)
    if "OpenRouter HTTP 402" in message or "OpenRouter HTTP 400" in message:
        return False
    domain = normalize_domain(item.job["domain"])
    if domain == "agentdojo" and "No response from model" in message:
        return True
    if "OpenRouter response content is missing" in message:
        return True
    if "IncompleteRead" in message:
        return True
    if domain == "appworld" and "TimeoutError" in message and "timed out" in message:
        return True
    return False


def _existing_completed_result(
    item: PlannedJob,
    *,
    context: SmokeExecutionContext,
) -> dict[str, Any] | None:
    job = item.job
    root = resolve_repo_path(job_result_relative_dir(job) / "adapter")
    raw_run_path = root / "raw_run.json"
    artifact_manifest_path = root / "artifact_manifest.json"
    environment_path = root / "environment.json"
    if (
        not raw_run_path.exists()
        or not artifact_manifest_path.exists()
        or not environment_path.exists()
    ):
        return None

    raw_run = _load_existing_mapping(raw_run_path)
    artifact_manifest = _load_existing_mapping(artifact_manifest_path)
    environment = _load_existing_mapping(environment_path)
    if raw_run is None or artifact_manifest is None or environment is None:
        return None
    if str(raw_run.get("status") or "").lower() != "completed":
        return None
    if str(raw_run.get("diagnostic_status") or "completed").lower() != "completed":
        return None
    if not _raw_run_matches_job(raw_run, job):
        return None
    if not _artifact_manifest_matches_job(
        artifact_manifest,
        job,
        source_bundle_hash=str(context.source_bundle_hash),
        official_split_hash=str(item.official_split_hash),
    ):
        return None
    if not _environment_matches_job(environment, job):
        return None
    if str(raw_run.get("artifact_manifest_sha256") or "") != sha256_file(
        artifact_manifest_path
    ):
        return None
    if not _record_pointer_matches(
        raw_run.get("artifact_manifest_path"), artifact_manifest_path
    ):
        return None
    if not _record_pointer_matches(raw_run.get("raw_source_path"), raw_run_path):
        return None
    if not _llm_calls_are_successful(root / "llm_calls"):
        return None
    if normalize_domain(
        job["domain"]
    ) == "agentdojo" and not _agentdojo_native_run_is_successful(root):
        return None
    if normalize_domain(
        job["domain"]
    ) == "webarena_verified" and not _webarena_native_run_is_auditable(root):
        return None
    return {
        "status": "skipped_completed",
        "skipped_existing": True,
        "raw_run_path": str(raw_run_path),
        "artifact_manifest_path": str(artifact_manifest_path),
    }


def resolve_result_namespace(
    *,
    manifest: dict[str, Any],
    requested: str | None,
    execution_lock_path: str | Path | None = None,
) -> str | None:
    """Resolve a CLI run-set namespace against its locked manifest value."""

    declared = normalize_result_namespace(manifest.get("result_namespace"))
    explicit = normalize_result_namespace(requested)
    if execution_lock_path is not None:
        if declared != _AGENTDOJO_FULL_RESULT_NAMESPACE:
            raise ValueError(
                "an AgentDojo execution lock may only be used with the full manifest"
            )
        if (
            explicit is not None
            and explicit != _AGENTDOJO_FULL_EXECUTION_STAGING_NAMESPACE
        ):
            raise ValueError(
                "execution-lock raw collection must use the sealed staging namespace: "
                f"{_AGENTDOJO_FULL_EXECUTION_STAGING_NAMESPACE}"
            )
        return _AGENTDOJO_FULL_EXECUTION_STAGING_NAMESPACE
    if declared is not None and explicit is not None and declared != explicit:
        raise ValueError(
            "requested result_namespace does not match manifest: "
            f"requested={explicit!r} manifest={declared!r}"
        )
    return explicit or declared


def validate_namespaced_manifest_inputs(
    *,
    manifest: dict[str, Any],
    manifest_path: str | Path | None = None,
    source_bundle_path: str | Path,
    infra_config_path: str | Path,
    agents_config_path: str | Path,
    phase: str | None = None,
    experiment_type: str | None = None,
    execution_lock_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Fail closed when a namespaced run's locked inputs differ on disk.

    Legacy manifests predate isolated run sets and retain their historical
    permissive behavior.  A manifest that opts into ``result_namespace`` is a
    new run-set lock and therefore must bind the exact inputs used to plan it.
    """

    if execution_lock_path is not None:
        if manifest.get("result_namespace") != _AGENTDOJO_FULL_RESULT_NAMESPACE:
            raise ValueError("execution lock is only valid for AgentDojo full raw collection")
        if phase != "full" or experiment_type != "appendix":
            raise ValueError(
                "execution lock only authorizes phase='full', experiment_type='appendix'"
            )
        if manifest_path is None:
            raise ValueError("manifest_path is required with an execution lock")
        execution_module = import_module(
            "evidence_system.contracts.agentdojo_full_execution"
        )
        try:
            verified = execution_module.verify_execution_lock(
                lock_path=execution_lock_path,
                manifest_path=manifest_path,
                source_bundle_path=source_bundle_path,
                agents_config_path=agents_config_path,
                runtime_infra_path=infra_config_path,
            )
        except Exception as exc:
            raise ValueError(
                f"AgentDojo execution-lock currentness verification failed: {exc}"
            ) from exc
        lock = load_mapping(verified.lock_path)
        definition = dict(lock.get("definition") or {})
        if lock.get("result_namespace") != _AGENTDOJO_FULL_EXECUTION_STAGING_NAMESPACE:
            raise ValueError("execution lock does not bind the sealed staging namespace")
        if definition.get("formal_result_namespace") != _AGENTDOJO_FULL_RESULT_NAMESPACE:
            raise ValueError("execution lock formal namespace binding is invalid")
        policy_ref = dict(definition.get("runtime_policy") or {})
        runtime_policy = load_mapping(str(policy_ref.get("path") or ""))
        runtime_control = import_module(
            "evidence_system.adapters.agentdojo_runtime_control"
        )
        runtime_control.load_runtime_policy(
            runtime_policy,
            expected_semantic_sha256=str(
                dict(definition.get("rate_limit_policy") or {}).get(
                    "runtime_policy_semantic_sha256"
                )
                or ""
            ),
        )
        return {
            "module": execution_module,
            "lock": lock,
            "lock_path": str(verified.lock_path),
            "lock_sha256": verified.lock_sha256,
            "runtime_policy": runtime_policy,
        }

    # Validate the immutable experiment-lock identity before comparing the
    # individual input hashes.  This keeps a copied manifest from being able
    # to hide the more fundamental path-binding violation behind whichever
    # shared config file happened to drift first.
    lock_ref = manifest.get("experiment_lock_path")
    if lock_ref:
        if manifest_path is None:
            raise ValueError(
                "manifest_path is required when manifest declares experiment_lock_path"
            )
        validate_namespaced_experiment_lock(
            manifest=manifest,
            manifest_path=manifest_path,
            lock_path=str(lock_ref),
            source_bundle_path=source_bundle_path,
            phase=phase,
            experiment_type=experiment_type,
        )

    locked_inputs = (
        ("source_bundle_hash", source_bundle_path),
        ("infra_config_hash", infra_config_path),
        ("agents_config_hash", agents_config_path),
    )
    mismatches: list[str] = []
    for field, path in locked_inputs:
        locked = str(manifest.get(field) or "").removeprefix("sha256:")
        actual = sha256_file(resolve_repo_path(path))
        if locked != actual:
            mismatches.append(
                f"{field}: manifest={locked or '<missing>'} actual={actual}"
            )
    if mismatches:
        raise ValueError(
            "namespaced manifest input hash mismatch; refusing to plan against unlocked inputs: "
            + "; ".join(mismatches)
        )
    return None


def validate_namespaced_experiment_lock(
    *,
    manifest: dict[str, Any],
    manifest_path: str | Path,
    lock_path: str | Path,
    source_bundle_path: str | Path,
    phase: str | None,
    experiment_type: str | None,
) -> None:
    """Enforce the immutable run-set lock before any namespaced job is planned."""

    lock_file = resolve_repo_path(lock_path)
    lock = load_mapping(lock_file)
    definition = {
        key: value
        for key, value in lock.items()
        if key
        not in {
            "schema_version",
            "lock_id",
            "lock_status",
            "locked_at",
            "definition_sha256",
        }
    }
    failures: list[str] = []
    if lock.get("lock_status") != "locked":
        failures.append("lock_status is not locked")
    if sha256_object(definition) != lock.get("definition_sha256"):
        failures.append("definition_sha256 mismatch")
    if lock.get("result_namespace") != manifest.get("result_namespace"):
        failures.append("result_namespace mismatch")

    artifacts = dict(lock.get("artifacts") or {})
    manifest_file = resolve_repo_path(manifest_path)
    source_bundle_file = resolve_repo_path(source_bundle_path)
    locked_manifest_file = resolve_repo_path(str(artifacts.get("manifest_path") or ""))
    locked_source_bundle_file = resolve_repo_path(
        str(artifacts.get("source_bundle_path") or "")
    )
    if locked_manifest_file.resolve() != manifest_file.resolve():
        failures.append("manifest_path mismatch")
    if locked_source_bundle_file.resolve() != source_bundle_file.resolve():
        failures.append("source_bundle_path mismatch")
    if artifacts.get("manifest_sha256") != sha256_file(manifest_file):
        failures.append("manifest_sha256 mismatch")
    if artifacts.get("source_bundle_sha256") != sha256_file(source_bundle_file):
        failures.append("source_bundle_sha256 mismatch")
    packets_root = resolve_repo_path(str(artifacts.get("case_packets_root") or ""))
    if artifacts.get("case_packets_tree_sha256") != sha256_path(packets_root):
        failures.append("case_packets_tree_sha256 mismatch")

    execution = dict(lock.get("execution") or {})
    if phase is not None and execution.get("phase") != phase:
        failures.append(
            f"phase mismatch: lock={execution.get('phase')!r} requested={phase!r}"
        )
    if (
        experiment_type is not None
        and execution.get("experiment_type") != experiment_type
    ):
        failures.append(
            "experiment_type mismatch: "
            f"lock={execution.get('experiment_type')!r} requested={experiment_type!r}"
        )
    for path_text, expected_hash in dict(lock.get("runtime_code_sha256") or {}).items():
        path = resolve_repo_path(path_text)
        if not path.exists() or sha256_file(path) != expected_hash:
            failures.append(f"runtime_code_sha256 mismatch: {path_text}")
    for path_text, expected_hash in dict(
        lock.get("legacy_artifact_snapshot_sha256") or {}
    ).items():
        path = resolve_repo_path(path_text)
        if not path.exists() or sha256_path(path) != expected_hash:
            failures.append(f"legacy artifact changed: {path_text}")

    if manifest.get("result_namespace") == _AGENTDOJO_FULL_RESULT_NAMESPACE:
        if lock.get("schema_version") != _AGENTDOJO_FULL_LOCK_SCHEMA_VERSION:
            failures.append(
                "AgentDojo full namespace requires final checklist-freeze lock schema "
                f"{_AGENTDOJO_FULL_LOCK_SCHEMA_VERSION}"
            )
        if lock.get("lock_revision") != _AGENTDOJO_FULL_LOCK_REVISION:
            failures.append(
                "AgentDojo full namespace requires lock_revision "
                f"{_AGENTDOJO_FULL_LOCK_REVISION}"
            )
        checklist_freeze = lock.get("checklist_freeze")
        freeze_counts = (
            checklist_freeze.get("counts")
            if isinstance(checklist_freeze, dict)
            else None
        )
        if freeze_counts != _AGENTDOJO_FULL_FREEZE_COUNTS:
            failures.append(
                "AgentDojo full checklist-freeze counts must be exactly "
                f"{_AGENTDOJO_FULL_FREEZE_COUNTS}; actual={freeze_counts!r}"
            )
        if (
            lock.get("schema_version") == _AGENTDOJO_FULL_LOCK_SCHEMA_VERSION
            and lock.get("lock_revision") == _AGENTDOJO_FULL_LOCK_REVISION
            and freeze_counts == _AGENTDOJO_FULL_FREEZE_COUNTS
        ):
            full_experiment = import_module(
                "evidence_system.contracts.agentdojo_full_experiment"
            )
            try:
                full_experiment.verify_checklist_freeze_lock(lock_path=lock_file)
            except Exception as exc:
                failures.append(
                    "AgentDojo full checklist-freeze currentness verification failed: "
                    f"{exc}"
                )
    if failures:
        raise ValueError(
            "namespaced experiment lock mismatch; refusing to plan: "
            + "; ".join(failures)
        )


def _load_existing_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = load_json_or_yaml(path)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def _payload_matches_job(payload: dict[str, Any], job: dict[str, Any]) -> bool:
    """Match identity fields strictly; missing provenance must never authorize reuse."""

    expected = {
        "domain": normalize_domain(job["domain"]),
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
        "phase": str(job.get("phase") or "smoke"),
        "experiment_type": str(job["experiment_type"]),
        "priority": str(job["priority"]),
    }
    for key, expected_value in expected.items():
        if key not in payload or payload.get(key) is None:
            return False
        value: Any = payload[key]
        if key == "domain":
            try:
                value = normalize_domain(str(value))
            except Exception:
                return False
        elif isinstance(expected_value, bool):
            if not isinstance(value, bool):
                return False
        elif isinstance(expected_value, int):
            if isinstance(value, bool) or not isinstance(value, int):
                return False
        elif isinstance(expected_value, str):
            value = str(value)
        if value != expected_value:
            return False
    return True


def _raw_run_matches_job(payload: dict[str, Any], job: dict[str, Any]) -> bool:
    if payload.get("schema_version") != "raw_run/v1" or not _payload_matches_job(
        payload, job
    ):
        return False
    expected = {
        "manifest_hash": str(job["manifest_hash"]),
        "contract_id": str(job["contract_id"]),
        "contract_version": str(job["contract_version"]),
        "contract_hash": str(job["contract_hash"]),
        "taxonomy_version": str(job["taxonomy_version"]),
        "evidence_contract_id": str(job["evidence_contract_id"]),
        "evidence_contract_version": str(job["evidence_contract_version"]),
        "evidence_contract_hash": str(job["evidence_contract_hash"]),
        "config_hash": sha256_object(
            {
                "agent_config_hash": str(job["agent_config_hash"]),
                "benchmark_config_hash": str(job["benchmark_config_hash"]),
            }
        ),
    }
    if job.get("execution_lock_sha256") is not None:
        expected["execution_lock_sha256"] = str(job["execution_lock_sha256"])
        expected["execution_policy_sha256"] = str(job["execution_policy_sha256"])
        expected["openrouter_runtime_policy_sha256"] = str(
            job["openrouter_runtime_policy_sha256"]
        )
        expected["openrouter_runtime_policy_file_sha256"] = str(
            job["openrouter_runtime_policy_file_sha256"]
        )
    return all(str(payload.get(key) or "") == value for key, value in expected.items())


def _artifact_manifest_matches_job(
    payload: dict[str, Any],
    job: dict[str, Any],
    *,
    source_bundle_hash: str,
    official_split_hash: str,
) -> bool:
    if payload.get(
        "schema_version"
    ) != "artifact_manifest/v1" or not _payload_matches_job(payload, job):
        return False
    expected = {
        "evidence_contract_id": str(job["evidence_contract_id"]),
        "evidence_contract_version": str(job["evidence_contract_version"]),
        "evidence_contract_hash": str(job["evidence_contract_hash"]),
        "source_bundle_hash": source_bundle_hash,
        "official_splits_hash": official_split_hash,
    }
    if job.get("execution_lock_sha256") is not None:
        expected["execution_lock_sha256"] = str(job["execution_lock_sha256"])
        expected["execution_policy_sha256"] = str(job["execution_policy_sha256"])
        expected["openrouter_runtime_policy_sha256"] = str(
            job["openrouter_runtime_policy_sha256"]
        )
        expected["openrouter_runtime_policy_file_sha256"] = str(
            job["openrouter_runtime_policy_file_sha256"]
        )
    return all(str(payload.get(key) or "") == value for key, value in expected.items())


def _environment_matches_job(payload: dict[str, Any], job: dict[str, Any]) -> bool:
    expected = {
        "benchmark_config_hash": str(job["benchmark_config_hash"]),
        "job_id": str(job["job_id"]),
        "run_id": str(job["run_id"]),
    }
    if job.get("execution_lock_sha256") is not None:
        expected["execution_lock_sha256"] = str(job["execution_lock_sha256"])
        expected["execution_policy_sha256"] = str(job["execution_policy_sha256"])
        expected["openrouter_runtime_policy_sha256"] = str(
            job["openrouter_runtime_policy_sha256"]
        )
        expected["openrouter_runtime_policy_file_sha256"] = str(
            job["openrouter_runtime_policy_file_sha256"]
        )
    return all(str(payload.get(key) or "") == value for key, value in expected.items())


def _record_pointer_matches(value: Any, expected_path: Path) -> bool:
    if not value:
        return False
    try:
        return resolve_repo_path(str(value)).resolve() == expected_path.resolve()
    except (OSError, RuntimeError, ValueError):
        return False


def _llm_calls_are_successful(llm_dir: Path) -> bool:
    if not llm_dir.exists():
        return True
    for path in llm_dir.glob("*.json"):
        payload = _load_existing_mapping(path)
        if payload is None:
            return False
        metadata = payload.get("response_metadata")
        if (
            isinstance(metadata, dict)
            and str(metadata.get("status") or "success").lower() != "success"
        ):
            return False
    return True


def _agentdojo_native_run_is_successful(root: Path) -> bool:
    native_root = root / "native_run"
    summary = _load_existing_mapping(native_root / "run_summary.json")
    if summary is None or str(summary.get("status") or "").lower() != "completed":
        return False
    native_job = _load_existing_mapping(native_root / "job.json")
    if native_job is None:
        return False
    if native_job.get("result_namespace"):
        verification = _load_existing_mapping(native_root / "install_verification.json")
        if verification is None:
            return False
        if (
            verification.get("source_lock_enforced") is not True
            or int(verification.get("verified_source_file_count") or 0) < 1
            or verification.get("agentdojo_package_version") != "0.1.35"
            or verification.get("agentdojo_git_commit")
            != "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b"
            or verification.get("agentdojo_git_tree")
            != "3c74b60f2bad4ff321d864e0c0483f256cc8f8d2"
        ):
            return False
    proxy_dir = native_root / "proxy_calls"
    proxy_paths = sorted(proxy_dir.glob("*.json")) if proxy_dir.exists() else []
    if not proxy_paths:
        return False
    for path in proxy_paths:
        payload = _load_existing_mapping(path)
        if payload is None:
            return False
        if payload.get("error_message") or payload.get("error_type"):
            return False
        forwarded_payload = payload.get("forwarded_payload")
        model = ""
        if isinstance(forwarded_payload, dict):
            model = str(forwarded_payload.get("model") or "")
        if model.startswith("openrouter/"):
            return False
    return True


def _strict_webarena_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _webarena_binary_score(status: Any, value: Any) -> float | None:
    if not isinstance(status, str) or status not in _WEBARENA_RESULT_STATUSES:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    score = float(value)
    if score not in {0.0, 1.0}:
        return None
    expected = 1.0 if status == "success" else 0.0
    return score if score == expected else None


def _webarena_has_private_summary_key(value: Any) -> bool:
    private_keys = {
        "expected",
        "actual",
        "actual_normalized",
        "error_msg",
        "assertion_msgs",
    }
    if isinstance(value, dict):
        return any(
            str(key).lower() in private_keys or _webarena_has_private_summary_key(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_webarena_has_private_summary_key(item) for item in value)
    return False


def _load_locked_webarena_task_material(
    task_id: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    index_path = resolve_repo_path(_WEBARENA_VERIFIED_TASK_CONTRACT_INDEX)
    if not index_path.is_file():
        return None
    try:
        if sha256_file(index_path) != _WEBARENA_VERIFIED_TASK_CONTRACT_INDEX_SHA256:
            return None
    except OSError:
        return None
    index = _load_existing_mapping(index_path)
    if index is None:
        return None
    expected_index_metadata = {
        "schema_version": "webarena_verified_task_contract_index/v1",
        "benchmark": "WebArena-Verified",
        "version": "v1.2.3",
        "split": "full",
        "visibility": "controller_only",
        "raw_tag_dataset_sha256": _WEBARENA_VERIFIED_DATA_CHECKSUM,
    }
    if any(index.get(key) != value for key, value in expected_index_metadata.items()):
        return None
    if _strict_webarena_int(index.get("task_count")) != 812:
        return None
    entries = index.get("entries")
    if not isinstance(entries, list) or len(entries) != 812:
        return None
    entries_by_id: dict[int, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            return None
        entry_id = _strict_webarena_int(entry.get("task_id"))
        if entry_id is None or entry_id not in range(812) or entry_id in entries_by_id:
            return None
        entries_by_id[entry_id] = dict(entry)
    if set(entries_by_id) != set(range(812)):
        return None
    contract = entries_by_id.get(task_id)
    if contract is None:
        return None

    revision = _strict_webarena_int(contract.get("task_revision"))
    intent_template_id = _strict_webarena_int(contract.get("intent_template_id"))
    task_type = contract.get("task_type")
    sites = contract.get("sites")
    evaluator_names = contract.get("evaluator_names_in_order")
    if revision is None or revision < 1 or intent_template_id is None:
        return None
    if task_type not in {"RETRIEVE", "MUTATE", "NAVIGATE"}:
        return None
    if (
        not isinstance(sites, list)
        or not sites
        or any(not isinstance(site, str) for site in sites)
    ):
        return None
    if (
        not isinstance(evaluator_names, list)
        or not evaluator_names
        or evaluator_names[0] != "AgentResponseEvaluator"
        or any(name not in _WEBARENA_ALLOWED_EVALUATORS for name in evaluator_names)
    ):
        return None
    if contract.get("required_run_artifacts") != ["agent_response.json", "network.har"]:
        return None

    case_dir = resolve_repo_path(_WEBARENA_VERIFIED_CASE_PACKET_ROOT) / str(task_id)
    packet_path = case_dir / "case_packet.json"
    agent_input_path = case_dir / "agent_input.json"
    if not packet_path.is_file() or not agent_input_path.is_file():
        return None
    try:
        if sha256_file(packet_path) != contract.get("case_packet_sha256"):
            return None
        if sha256_file(agent_input_path) != contract.get("agent_input_sha256"):
            return None
    except OSError:
        return None
    packet = _load_existing_mapping(packet_path)
    agent_input = _load_existing_mapping(agent_input_path)
    if packet is None or agent_input is None:
        return None
    if set(agent_input) != _WEBARENA_AGENT_INPUT_FIELDS:
        return None
    if _strict_webarena_int(agent_input.get("task_id")) != task_id:
        return None
    if (
        _strict_webarena_int(agent_input.get("intent_template_id"))
        != intent_template_id
    ):
        return None
    if agent_input.get("sites") != sites:
        return None
    start_urls = agent_input.get("start_urls")
    if (
        not isinstance(agent_input.get("intent"), str)
        or not agent_input["intent"]
        or not isinstance(start_urls, list)
        or not start_urls
        or any(not isinstance(url, str) for url in start_urls)
    ):
        return None

    task = packet.get("task")
    visible_input = packet.get("model_visible_input")
    evaluator_reference = packet.get("evaluator_reference")
    leakage_control = packet.get("leakage_control")
    if not all(
        isinstance(item, dict)
        for item in (task, visible_input, evaluator_reference, leakage_control)
    ):
        return None
    assert isinstance(task, dict)
    assert isinstance(visible_input, dict)
    assert isinstance(evaluator_reference, dict)
    assert isinstance(leakage_control, dict)
    if packet.get("schema_version") != "webarena_verified_case_packet/v1":
        return None
    if packet.get("visibility") != "controller_and_human_review_only":
        return None
    if (
        _strict_webarena_int(task.get("task_id")) != task_id
        or _strict_webarena_int(task.get("revision")) != revision
        or _strict_webarena_int(task.get("intent_template_id")) != intent_template_id
        or task.get("task_type") != task_type
        or task.get("instruction") != agent_input["intent"]
        or task.get("sites") != sites
        or task.get("resolved_start_urls") != start_urls
    ):
        return None
    if (
        visible_input.get("path") != "agent_input.json"
        or visible_input.get("sha256") != contract.get("agent_input_sha256")
        or visible_input.get("field_allowlist")
        != ["intent", "intent_template_id", "sites", "start_urls", "task_id"]
    ):
        return None
    if (
        evaluator_reference.get("version") != "v1.2.3"
        or evaluator_reference.get("docker_image") != _WEBARENA_VERIFIED_EVALUATOR_IMAGE
        or evaluator_reference.get("evaluator_config_names") != evaluator_names
        or evaluator_reference.get("required_run_artifacts")
        != contract.get("required_run_artifacts")
    ):
        return None
    if leakage_control != {
        "answer_payload_embedded": False,
        "evaluator_payload_embedded": False,
        "model_receives_only_agent_input_json": True,
        "policy": "allowlist_only_v1",
    }:
        return None
    return contract, packet, agent_input


def _webarena_har_is_full_and_embedded(path: Path) -> bool:
    try:
        har = load_json_or_yaml(path)
    except Exception:
        return False
    if not isinstance(har, dict):
        return False
    log = har.get("log")
    if not isinstance(log, dict) or log.get("version") != "1.2":
        return False
    creator = log.get("creator")
    if (
        not isinstance(creator, dict)
        or "playwright" not in str(creator.get("name") or "").lower()
    ):
        return False
    entries = log.get("entries")
    if not isinstance(entries, list) or not entries:
        return False
    embedded_body_count = 0
    for entry in entries:
        if not isinstance(entry, dict) or not _WEBARENA_FULL_HAR_ENTRY_FIELDS.issubset(
            entry
        ):
            return False
        request = entry.get("request")
        response = entry.get("response")
        if not isinstance(
            request, dict
        ) or not _WEBARENA_FULL_HAR_REQUEST_FIELDS.issubset(request):
            return False
        if not isinstance(
            response, dict
        ) or not _WEBARENA_FULL_HAR_RESPONSE_FIELDS.issubset(response):
            return False
        content = response.get("content")
        if not isinstance(content, dict) or "_file" in content or "_sha1" in content:
            return False
        if "text" in content:
            embedded_body_count += 1
    return embedded_body_count > 0


def _webarena_path_has_name(
    value: Any, expected_name: str, *, parent_name: str | None = None
) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    if path.name != expected_name:
        return False
    return parent_name is None or path.parent.name == parent_name


def _webarena_native_run_is_auditable(root: Path) -> bool:
    native_root = root / "native_run"
    summary = _load_existing_mapping(native_root / "run_summary.json")
    if summary is None or summary.get("status") != "completed":
        return False
    if summary.get("used_expected_fallback") is not False:
        return False
    if summary.get("llm_used") is not True:
        return False
    runner_kind = str(summary.get("runner_kind") or "")
    if runner_kind != _WEBARENA_RUNNER_KIND:
        # All legacy WebArena, BrowserGym-average, and pre-v1.2.3 lanes are
        # deliberately non-resumable for the frozen full-812 experiment.
        return False
    fixes = summary.get("runner_fixes")
    if not isinstance(fixes, dict):
        return False
    expected_fixes = {
        "agent_loop": "official_run_py",
        "prompt": "pinned_bundled_p_cot_id_actree_2s",
        "action_set": "id_accessibility_tree",
        "observation_type": "accessibility_tree",
        "task_input": "official_agent_input_get",
        "final_answer_protocol": "strict_structured_json",
        "prompt_contract": "webarena_verified_public_self_classified_four_field_json_v1",
        "evaluator": "webarena_verified_v1_2_3_eval_tasks",
        "trace": "playwright_full_embedded_har",
    }
    if fixes != expected_fixes:
        return False

    task_id = _strict_webarena_int(summary.get("task_id"))
    task_revision = _strict_webarena_int(summary.get("task_revision"))
    if task_id is None or task_id not in range(812) or task_revision is None:
        return False
    locked_material = _load_locked_webarena_task_material(task_id)
    if locked_material is None:
        return False
    task_contract, case_packet, locked_agent_input = locked_material
    if task_revision != task_contract.get("task_revision"):
        return False
    task_dir = native_root / str(task_id)
    eval_result_path = task_dir / "eval_result.json"
    har_path = task_dir / "network.har"
    agent_response_path = task_dir / "agent_response.json"
    eval_summary_path = task_dir / "eval_summary.json"
    required_files = (
        native_root / "native_evaluator_input.json",
        native_root / "native_evaluator_output.json",
        native_root / "job.json",
        native_root / "source_bundle_entry.json",
        native_root / "worker_config.json",
        native_root / "webarena_env.json",
        native_root / f"render_{task_id}.html",
        native_root / "traces" / f"{task_id}.zip",
        task_dir / "official_task_config.json",
        agent_response_path,
        task_dir / "solver_trace.json",
        har_path,
        eval_result_path,
        eval_summary_path,
        task_dir / "official_evaluator.stdout.log",
        task_dir / "official_evaluator.stderr.log",
        root / "llm_calls" / "calls.jsonl",
    )
    required_directories = (native_root / "llm_attempts", native_root / "official_run")
    if any(not path.is_file() for path in required_files):
        return False
    if any(not path.is_dir() for path in required_directories):
        return False
    try:
        if (root / "llm_calls" / "calls.jsonl").stat().st_size <= 0:
            return False
    except OSError:
        return False

    solver_trace = _load_existing_mapping(task_dir / "solver_trace.json")
    native_output = _load_existing_mapping(native_root / "native_evaluator_output.json")
    native_input = _load_existing_mapping(native_root / "native_evaluator_input.json")
    native_job = _load_existing_mapping(native_root / "job.json")
    worker_config = _load_existing_mapping(native_root / "worker_config.json")
    official_task_config = _load_existing_mapping(
        task_dir / "official_task_config.json"
    )
    eval_result = _load_existing_mapping(eval_result_path)
    eval_summary = _load_existing_mapping(eval_summary_path)
    agent_response = _load_existing_mapping(agent_response_path)
    source_entry = _load_existing_mapping(native_root / "source_bundle_entry.json")
    loaded_mappings = (
        solver_trace,
        native_output,
        native_input,
        native_job,
        worker_config,
        official_task_config,
        eval_result,
        eval_summary,
        agent_response,
        source_entry,
    )
    if any(item is None for item in loaded_mappings):
        return False
    assert solver_trace is not None
    assert native_output is not None
    assert native_input is not None
    assert native_job is not None
    assert worker_config is not None
    assert official_task_config is not None
    assert eval_result is not None
    assert eval_summary is not None
    assert agent_response is not None
    assert source_entry is not None

    if native_job.get("schema_version") != "job/v1":
        return False
    try:
        if normalize_domain(str(native_job.get("domain") or "")) != "webarena_verified":
            return False
    except (ValueError, RuntimeError):
        return False
    if str(native_job.get("task_id")) != str(task_id):
        return False
    if str(native_job.get("case_unit_id")) != str(task_id):
        return False
    for plain_key, evidence_key in (
        ("contract_id", "evidence_contract_id"),
        ("contract_version", "evidence_contract_version"),
        ("contract_hash", "evidence_contract_hash"),
    ):
        if not native_job.get(plain_key) or native_job.get(plain_key) != native_job.get(
            evidence_key
        ):
            return False
    job_contract_hash = str(native_job.get("contract_hash") or "")
    if len(job_contract_hash) != 64 or any(
        character not in "0123456789abcdef" for character in job_contract_hash
    ):
        return False

    if (
        worker_config.get("job") != native_job
        or worker_config.get("source_entry") != source_entry
    ):
        return False
    if (
        _strict_webarena_int(worker_config.get("task_id")) != task_id
        or _strict_webarena_int(worker_config.get("task_revision")) != task_revision
        or worker_config.get("task_type") != task_contract.get("task_type")
        or worker_config.get("official_evaluator_config")
        != "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json"
    ):
        return False

    expected_native_input_fields = {
        "schema_version",
        "runner_kind",
        "task_id",
        "task_revision",
        "agent_response_path",
        "network_har_path",
        "evaluator_config_path",
        "evaluator",
        "evaluator_image",
    }
    if set(native_input) != expected_native_input_fields:
        return False
    if (
        native_input.get("schema_version")
        != "webarena_verified_native_evaluator_input/v1"
        or native_input.get("runner_kind") != runner_kind
        or _strict_webarena_int(native_input.get("task_id")) != task_id
        or _strict_webarena_int(native_input.get("task_revision")) != task_revision
        or native_input.get("evaluator")
        != "ServiceNow/webarena-verified v1.2.3 eval-tasks"
        or native_input.get("evaluator_image") != _WEBARENA_VERIFIED_EVALUATOR_IMAGE
        or native_input.get("evaluator_config_path")
        != "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json"
        or not _webarena_path_has_name(
            native_input.get("agent_response_path"),
            "agent_response.json",
            parent_name=str(task_id),
        )
        or not _webarena_path_has_name(
            native_input.get("network_har_path"),
            "network.har",
            parent_name=str(task_id),
        )
    ):
        return False

    if solver_trace.get("used_expected_fallback") is not False:
        return False
    if solver_trace.get("llm_used") is not True:
        return False
    if solver_trace.get("schema_version") != "webarena_verified_solver_trace/v1":
        return False
    if solver_trace.get("runner_kind") != runner_kind:
        return False
    trace_fixes = solver_trace.get("runner_fixes")
    if not isinstance(trace_fixes, dict):
        return False
    if trace_fixes != fixes:
        return False
    if (
        _strict_webarena_int(solver_trace.get("task_id")) != task_id
        or _strict_webarena_int(solver_trace.get("task_revision")) != task_revision
    ):
        return False

    if set(agent_response) != {
        "task_type",
        "status",
        "retrieved_data",
        "error_details",
    }:
        return False
    if agent_response.get("task_type") != task_contract.get("task_type"):
        return False
    public_status = agent_response.get("status")
    public_failures = {
        "ACTION_NOT_ALLOWED_ERROR",
        "PERMISSION_DENIED_ERROR",
        "NOT_FOUND_ERROR",
        "DATA_VALIDATION_ERROR",
        "UNKNOWN_ERROR",
    }
    if public_status == "SUCCESS":
        if agent_response.get("error_details") is not None:
            return False
        if task_contract.get("task_type") == "RETRIEVE":
            if not isinstance(agent_response.get("retrieved_data"), list):
                return False
        elif agent_response.get("retrieved_data") is not None:
            return False
    elif public_status in public_failures:
        if agent_response.get("retrieved_data") is not None:
            return False
        error_details = agent_response.get("error_details")
        if not isinstance(error_details, str) or not error_details.strip():
            return False
    else:
        return False

    if set(source_entry) != {
        "schema_version",
        "task_id",
        "agent_input",
        "case_packet_sha256",
    }:
        return False
    if source_entry.get("schema_version") != "webarena_verified_agent_safe_source/v1":
        return False
    if _strict_webarena_int(source_entry.get("task_id")) != task_id:
        return False
    if source_entry.get("case_packet_sha256") != task_contract.get(
        "case_packet_sha256"
    ):
        return False
    safe_agent_input = source_entry.get("agent_input")
    if safe_agent_input != locked_agent_input:
        return False

    locked_task = case_packet.get("task")
    if not isinstance(locked_task, dict):
        return False
    if "eval" in official_task_config:
        return False
    if (
        _strict_webarena_int(official_task_config.get("task_id")) != task_id
        or _strict_webarena_int(official_task_config.get("revision")) != task_revision
        or _strict_webarena_int(official_task_config.get("intent_template_id"))
        != task_contract.get("intent_template_id")
        or official_task_config.get("intent") != locked_agent_input.get("intent")
        or official_task_config.get("sites") != task_contract.get("sites")
        or official_task_config.get("start_url")
        != " |AND| ".join(locked_agent_input.get("start_urls") or [])
    ):
        return False
    if not _webarena_har_is_full_and_embedded(har_path):
        return False

    if _strict_webarena_int(eval_result.get("task_id")) != task_id:
        return False
    if _strict_webarena_int(eval_result.get("task_revision")) != task_revision:
        return False
    if _strict_webarena_int(eval_result.get("intent_template_id")) != task_contract.get(
        "intent_template_id"
    ) or eval_result.get("sites") != task_contract.get("sites"):
        return False
    if eval_result.get("webarena_verified_version") != _WEBARENA_VERIFIED_VERSION:
        return False
    if (
        eval_result.get("webarena_verified_evaluator_checksum")
        != _WEBARENA_VERIFIED_EVALUATOR_CHECKSUM
    ):
        return False
    if (
        eval_result.get("webarena_verified_data_checksum")
        != _WEBARENA_VERIFIED_DATA_CHECKSUM
    ):
        return False
    task_status = eval_result.get("status")
    if task_status not in {"success", "failure"}:
        return False
    score = _webarena_binary_score(task_status, eval_result.get("score"))
    if score is None:
        return False

    evaluator_results = eval_result.get("evaluators_results")
    if not isinstance(evaluator_results, list) or not evaluator_results:
        return False
    expected_evaluator_names = task_contract.get("evaluator_names_in_order")
    if not isinstance(expected_evaluator_names, list):
        return False
    evaluator_names: list[str] = []
    evaluator_statuses: list[str] = []
    expected_evaluator_summaries: list[dict[str, Any]] = []
    for position, evaluator_result in enumerate(evaluator_results):
        if not isinstance(evaluator_result, dict):
            return False
        evaluator_name = evaluator_result.get("evaluator_name")
        if (
            not isinstance(evaluator_name, str)
            or evaluator_name not in _WEBARENA_ALLOWED_EVALUATORS
        ):
            return False
        evaluator_names.append(evaluator_name)
        evaluator_status = evaluator_result.get("status")
        evaluator_score = _webarena_binary_score(
            evaluator_status, evaluator_result.get("score")
        )
        if evaluator_score is None:
            return False
        assert isinstance(evaluator_status, str)
        evaluator_statuses.append(evaluator_status)
        assertions = evaluator_result.get("assertions")
        if assertions is None:
            assertion_list: list[Any] = []
        elif isinstance(assertions, list):
            assertion_list = assertions
        else:
            return False
        assertion_status_counts: dict[str, int] = {}
        for assertion in assertion_list:
            if not isinstance(assertion, dict):
                continue
            assertion_status = str(assertion.get("status"))
            assertion_status_counts[assertion_status] = (
                assertion_status_counts.get(assertion_status, 0) + 1
            )
        expected_evaluator_summaries.append(
            {
                "evaluator_name": evaluator_name,
                "status": evaluator_status,
                "score": evaluator_score,
                "assertion_count": len(assertion_list),
                "assertion_status_counts": dict(
                    sorted(assertion_status_counts.items())
                ),
            }
        )
        if position >= len(expected_evaluator_names):
            return False
    if evaluator_names != expected_evaluator_names:
        return False
    derived_status = (
        "error"
        if "error" in evaluator_statuses
        else "success"
        if all(status == "success" for status in evaluator_statuses)
        else "failure"
    )
    if task_status != derived_status:
        return False

    expected_summary_fields = {
        "schema_version",
        "scorer_status",
        "official_evaluation_completed",
        "integrity_verified",
        "task_id",
        "task_revision",
        "status",
        "score",
        "sites",
        "evaluators",
        "official_evaluator_image",
        "official_evaluator_command_kind",
        "official_evaluator_exit_code",
        "webarena_verified_version",
        "webarena_verified_evaluator_checksum",
        "webarena_verified_data_checksum",
        "task_contract_index_sha256",
        "runtime_config_sha256",
        "agent_response_sha256",
        "network_har_sha256",
        "official_eval_result_sha256",
        "official_evaluator_stdout_sha256",
        "official_evaluator_stderr_sha256",
        "official_eval_result_is_controller_only",
        "summary_contains_private_evaluator_payload",
    }
    if set(eval_summary) != expected_summary_fields:
        return False
    native_path_fields = {
        "official_render_path",
        "official_trace_path",
        "official_network_har_path",
    }
    if set(native_output) != expected_summary_fields | native_path_fields:
        return False
    if any(native_output.get(key) != value for key, value in eval_summary.items()):
        return False
    if _webarena_has_private_summary_key(
        eval_summary
    ) or _webarena_has_private_summary_key(native_output):
        return False
    if (
        eval_summary.get("schema_version")
        != "webarena_verified_official_eval_summary/v1"
    ):
        return False
    if eval_summary.get("scorer_status") != "success":
        return False
    if eval_summary.get("official_evaluation_completed") is not True:
        return False
    if eval_summary.get("integrity_verified") is not True:
        return False
    if eval_summary.get("official_eval_result_is_controller_only") is not True:
        return False
    if eval_summary.get("summary_contains_private_evaluator_payload") is not False:
        return False
    if _strict_webarena_int(eval_summary.get("task_id")) != task_id:
        return False
    if _strict_webarena_int(eval_summary.get("task_revision")) != task_revision:
        return False
    summary_eval_score = _webarena_binary_score(
        eval_summary.get("status"), eval_summary.get("score")
    )
    if eval_summary.get("status") != task_status or summary_eval_score != score:
        return False
    if eval_summary.get("sites") != task_contract.get("sites"):
        return False
    if eval_summary.get("evaluators") != expected_evaluator_summaries:
        return False
    if (
        eval_summary.get("official_evaluator_image")
        != _WEBARENA_VERIFIED_EVALUATOR_IMAGE
    ):
        return False
    if (
        eval_summary.get("official_evaluator_command_kind")
        != "pinned_docker_eval-tasks"
    ):
        return False
    if _strict_webarena_int(eval_summary.get("official_evaluator_exit_code")) != 0:
        return False
    if eval_summary.get("webarena_verified_version") != _WEBARENA_VERIFIED_VERSION:
        return False
    if (
        eval_summary.get("webarena_verified_evaluator_checksum")
        != _WEBARENA_VERIFIED_EVALUATOR_CHECKSUM
        or eval_summary.get("webarena_verified_data_checksum")
        != _WEBARENA_VERIFIED_DATA_CHECKSUM
        or eval_summary.get("task_contract_index_sha256")
        != _WEBARENA_VERIFIED_TASK_CONTRACT_INDEX_SHA256
        or eval_summary.get("runtime_config_sha256")
        != _WEBARENA_VERIFIED_RUNTIME_CONFIG_SHA256
    ):
        return False

    stdout_path = task_dir / "official_evaluator.stdout.log"
    stderr_path = task_dir / "official_evaluator.stderr.log"
    try:
        expected_hashes = {
            "official_eval_result_sha256": sha256_file(eval_result_path),
            "agent_response_sha256": sha256_file(agent_response_path),
            "network_har_sha256": sha256_file(har_path),
            "official_evaluator_stdout_sha256": sha256_file(stdout_path),
            "official_evaluator_stderr_sha256": sha256_file(stderr_path),
        }
    except OSError:
        return False
    if any(eval_summary.get(key) != value for key, value in expected_hashes.items()):
        return False
    if not _webarena_path_has_name(
        native_output.get("official_render_path"), f"render_{task_id}.html"
    ):
        return False
    if not _webarena_path_has_name(
        native_output.get("official_trace_path"), f"{task_id}.zip", parent_name="traces"
    ):
        return False
    if not _webarena_path_has_name(
        native_output.get("official_network_har_path"),
        "network.har",
        parent_name=str(task_id),
    ):
        return False

    llm_call_count = _strict_webarena_int(summary.get("llm_call_count"))
    if llm_call_count is None or llm_call_count < 1:
        return False
    if summary.get("evaluation_status") != task_status:
        return False
    summary_score = _webarena_binary_score(
        summary.get("evaluation_status"), summary.get("evaluation_score")
    )
    if summary_score is None or summary_score != score:
        return False
    expected_success = task_status == "success" and score == 1.0
    if summary.get("success") is not expected_success:
        return False
    if (
        summary.get("evaluator_version") != _WEBARENA_VERIFIED_VERSION
        or summary.get("evaluator_checksum") != _WEBARENA_VERIFIED_EVALUATOR_CHECKSUM
        or summary.get("data_checksum") != _WEBARENA_VERIFIED_DATA_CHECKSUM
    ):
        return False
    if not _webarena_path_has_name(
        summary.get("official_render_path"), f"render_{task_id}.html"
    ):
        return False
    if not _webarena_path_has_name(
        summary.get("official_trace_path"), f"{task_id}.zip", parent_name="traces"
    ):
        return False
    if not _webarena_path_has_name(
        summary.get("official_network_har_path"),
        "network.har",
        parent_name=str(task_id),
    ):
        return False
    if not _webarena_path_has_name(
        summary.get("official_eval_result_path"),
        "eval_result.json",
        parent_name=str(task_id),
    ):
        return False
    solver_score = _webarena_binary_score(
        task_status, solver_trace.get("official_evaluation_score")
    )
    if solver_score is None or solver_score != score:
        return False
    if not _webarena_path_has_name(
        solver_trace.get("official_eval_result_path"),
        "eval_result.json",
        parent_name=str(task_id),
    ):
        return False
    return True


def resolve_infra_target(
    domain: str, infra_config: dict[str, Any]
) -> InfraBenchmarkTarget:
    domain_key = normalize_domain(domain)
    constraint_roles = {
        role
        for name, roles in dict(
            infra_config.get("domain_machine_constraints") or {}
        ).items()
        if normalize_domain_or_none(name) == domain_key
        for role in list(roles or [])
    }
    if not constraint_roles:
        raise ValueError(
            f"infra config has no machine-role constraint for {domain_key}"
        )
    for machine in list(infra_config.get("machines") or []):
        if machine.get("enabled") is False:
            continue
        if str(machine.get("role")) not in constraint_roles:
            continue
        benchmark_name, benchmark_config = _benchmark_entry_for_domain(
            machine, domain_key
        )
        if benchmark_config is None:
            continue
        runner_command = str(benchmark_config.get("runner_command") or "").strip()
        if not runner_command:
            raise ValueError(
                f"benchmark {benchmark_name} on machine {machine.get('machine_id')} has no runner_command"
            )
        ssh_config = dict(machine.get("ssh") or {})
        site_controller = dict(benchmark_config.get("site_controller") or {})
        known_hosts_file = str(
            site_controller.get("known_hosts_file")
            or ssh_config.get("known_hosts_file")
            or ""
        )
        host_fingerprint = str(
            site_controller.get("ssh_host_fingerprint")
            or ssh_config.get("ed25519_fingerprint")
            or ssh_config.get("host_ed25519_fingerprint")
            or ""
        )
        return InfraBenchmarkTarget(
            machine_id=str(machine["machine_id"]),
            machine_role=str(machine["role"]),
            ssh_host=str(machine.get("ssh", {}).get("host") or ""),
            ssh_user=str(machine.get("ssh", {}).get("user") or ""),
            ssh_port=int(machine.get("ssh", {}).get("port") or 22),
            ssh_key_path=str(machine.get("ssh", {}).get("key_path") or ""),
            remote_workdir=str(machine.get("remote_workdir") or ""),
            runner_workdir=str(
                machine.get("runner_workdir") or machine.get("remote_workdir") or ""
            ),
            benchmark_name=benchmark_name,
            benchmark_config=dict(benchmark_config),
            benchmark_config_hash=sha256_object(benchmark_config),
            runner_command=runner_command,
            machine_concurrency=int(machine.get("concurrency") or 1),
            ssh_known_hosts_file=known_hosts_file or None,
            ssh_host_ed25519_fingerprint=host_fingerprint or None,
        )
    raise ValueError(f"no enabled machine with benchmark config found for {domain_key}")


def load_contract_index(
    contracts_dir: str | Path,
) -> dict[str, dict[str, dict[str, Any]]]:
    root = resolve_repo_path(contracts_dir)
    index: dict[str, dict[str, dict[str, Any]]] = {}
    for path in sorted(root.rglob("*.json")):
        payload = load_json_or_yaml(path)
        if not isinstance(payload, dict):
            continue
        case_unit_id = payload.get("case_unit_id")
        domain = payload.get("domain")
        if not case_unit_id or not domain:
            continue
        normalized = normalize_domain(domain)
        payload = dict(payload)
        payload.setdefault("contract_hash", sha256_object(payload))
        index.setdefault(normalized, {})[str(case_unit_id)] = payload
    return index


def plan_adapter_execution(
    job: dict[str, Any],
    *,
    target: InfraBenchmarkTarget,
    agents_config_path: str | Path,
    dotenv_path: str | Path,
    source_bundle_path: str | Path,
    bundle: dict[str, Any],
) -> dict[str, Any]:
    module = import_module(str(job["adapter_module"]))
    planner = getattr(module, "plan_smoke_execution", None)
    if planner is None:
        return {
            "status": "blocked",
            "blocking_reason": f"{job['adapter_module']} has no plan_smoke_execution() helper",
        }
    return dict(
        planner(
            job,
            target=target,
            agents_config_path=agents_config_path,
            dotenv_path=dotenv_path,
            source_bundle_path=source_bundle_path,
            source_bundle=bundle,
        )
    )


def _manifest_domain_block(manifest: dict[str, Any], domain: str) -> dict[str, Any]:
    for block in list(manifest.get("domains") or []):
        if normalize_domain(block.get("domain")) == domain:
            return dict(block)
    raise ValueError(f"manifest has no domain block for {domain}")


def _benchmark_entry_for_domain(
    machine: dict[str, Any], domain: str
) -> tuple[str, dict[str, Any] | None]:
    benchmarks = dict(machine.get("benchmarks") or {})
    for benchmark_name, benchmark_config in benchmarks.items():
        try:
            normalized = normalize_domain(benchmark_name)
        except Exception:
            continue
        if normalized == domain:
            return str(benchmark_name), dict(benchmark_config or {})
    return "", None


def _safe_id(value: str) -> str:
    cleaned = _SAFE_ID_RE.sub("-", value).strip("-")
    return cleaned or "x"
