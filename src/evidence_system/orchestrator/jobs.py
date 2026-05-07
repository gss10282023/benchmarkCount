"""Step 8 smoke-job planning helpers.

This module intentionally stops at provisional Step 8 planning. It builds
validated `job/v1` payloads for smoke/vertical-slice adapter work without
claiming a full Step 9 scheduler implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from importlib import import_module
from pathlib import Path
import re
from typing import Any, Callable, Sequence

from evidence_system.adapters.runtime import build_smoke_execution_context
from evidence_system.contracts.common import load_mapping, normalize_domain, normalize_domain_or_none, write_json
from evidence_system.contracts.draft import DEFAULT_TAXONOMY_VERSION
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object


_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


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
    case_count: int,
    agent_ids: list[str],
    seed: int,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    contracts_dir: str | Path,
    infra_config_path: str | Path,
    agents_config_path: str | Path,
    jobs_dir: str | Path,
) -> list[PlannedJob]:
    manifest = load_mapping(manifest_path)
    validate_object("experiment_manifest", manifest, raise_on_error=True)
    bundle = load_mapping(source_bundle_path)
    infra = load_mapping(infra_config_path)
    target = resolve_infra_target(domain, infra)
    contract_index = load_contract_index(contracts_dir)
    domain_key = normalize_domain(domain)
    domain_contracts = contract_index.get(domain_key, {})
    domain_block = _manifest_domain_block(manifest, domain_key)
    selected_cases = list(domain_block.get("case_units") or [])[:case_count]
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
        contract_id = str(contract.get("contract_id") if contract else f"{phase_contract_prefix}-{domain_key}-{_safe_id(case_unit_id)}")
        contract_version = str(contract.get("contract_version") if contract else "1.0.0")
        contract_hash = str(contract.get("contract_hash") if contract else sha256_object({"case_unit_id": case_unit_id, "domain": domain_key}))
        taxonomy_version = str(contract.get("taxonomy_version") if contract else DEFAULT_TAXONOMY_VERSION)
        artifact_contract = {
            "required_artifacts": list(contract.get("required_artifacts") or []) if contract else [],
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
                "domain_display_name": str(domain_block.get("domain_display_name") or target.benchmark_name),
                "benchmark_name": str(domain_block.get("domain_display_name") or target.benchmark_name),
                "case_unit_id": case_unit_id,
                "task_id": task_id,
                "record_slot_id": record_slot_id,
                "run_id": run_id,
                "attempt_id": attempt_id,
                "final_attempt": True,
                "seed": seed + case_index + agent_index - 2,
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
                    official_split_hash=str(domain_block.get("official_split_hash") or "0" * 64),
                    execution_plan=execution_plan,
                )
            )
    return planned


def execute_smoke_jobs(
    *,
    domain: str,
    phase: str,
    experiment_type: str,
    case_count: int,
    agent_ids: list[str],
    seed: int,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    contracts_dir: str | Path,
    infra_config_path: str | Path,
    agents_config_path: str | Path,
    jobs_dir: str | Path,
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
) -> list[ExecutedJob]:
    if not planned:
        return []
    domains = {str(item.job["domain"]) for item in planned}
    if len(domains) != 1:
        raise ValueError(f"execute_planned_jobs expects exactly one domain batch, found: {sorted(domains)}")
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

    def _execute(item: PlannedJob) -> ExecutedJob:
        if skip_completed:
            existing_result = _existing_completed_result(item)
            if existing_result is not None:
                return ExecutedJob(planned=item, execution_result=existing_result)
        executor = getattr(import_module(str(item.job["adapter_module"])), "execute_smoke_job", None)
        if executor is None:
            raise ValueError(f"{item.job['adapter_module']} has no execute_smoke_job() helper")
        if item.execution_plan.get("status") == "blocked":
            raise ValueError(f"{item.job['job_id']} is blocked: {item.execution_plan.get('blocking_reason')}")
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
    total = len(planned)

    if effective_workers <= 1:
        ordered: list[ExecutedJob] = []
        for completed_count, item in enumerate(planned, start=1):
            result = _execute(item)
            _raise_for_noncompleted(item, result, enabled=fail_fast_on_noncompleted)
            ordered.append(result)
            if progress_callback is not None:
                progress_callback(item, result.execution_result, completed_count, total)
        return ordered

    ordered: dict[str, ExecutedJob] = {}
    completed_count = 0
    with ThreadPoolExecutor(max_workers=effective_workers, thread_name_prefix=f"step8-{target.machine_role}") as pool:
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
                    _raise_for_noncompleted(item, result, enabled=fail_fast_on_noncompleted)
                except Exception:
                    for pending in futures:
                        pending.cancel()
                    raise
                ordered[str(item.job["job_id"])] = result
                completed_count += 1
                if progress_callback is not None:
                    progress_callback(item, result.execution_result, completed_count, total)
                _submit_next()
    return [ordered[str(item.job["job_id"])] for item in planned]


def _raise_for_noncompleted(item: PlannedJob, result: ExecutedJob, *, enabled: bool) -> None:
    if not enabled:
        return
    status = str(result.execution_result.get("status") or "unknown")
    if status == "skipped_completed":
        return
    if status != "completed":
        raise RuntimeError(f"{item.job['job_id']} returned non-completed status: {status}")
    if _existing_completed_result(item) is None:
        raise RuntimeError(f"{item.job['job_id']} completed but failed post-run artifact audit")


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


def _existing_completed_result(item: PlannedJob) -> dict[str, Any] | None:
    job = item.job
    root = resolve_repo_path(
        Path("results")
        / str(job.get("phase") or "smoke")
        / str(job["domain"])
        / str(job["job_id"])
        / "adapter"
    )
    raw_run_path = root / "raw_run.json"
    artifact_manifest_path = root / "artifact_manifest.json"
    if not raw_run_path.exists() or not artifact_manifest_path.exists():
        return None

    raw_run = _load_existing_mapping(raw_run_path)
    artifact_manifest = _load_existing_mapping(artifact_manifest_path)
    if raw_run is None or artifact_manifest is None:
        return None
    if str(raw_run.get("status") or "").lower() != "completed":
        return None
    if str(raw_run.get("diagnostic_status") or "completed").lower() != "completed":
        return None
    if not _payload_matches_job(raw_run, job):
        return None
    if not _payload_matches_job(artifact_manifest, job):
        return None
    if not _llm_calls_are_successful(root / "llm_calls"):
        return None
    if normalize_domain(job["domain"]) == "agentdojo" and not _agentdojo_native_run_is_successful(root):
        return None
    if normalize_domain(job["domain"]) == "webarena_verified" and not _webarena_native_run_is_auditable(root):
        return None
    return {
        "status": "skipped_completed",
        "skipped_existing": True,
        "raw_run_path": str(raw_run_path),
        "artifact_manifest_path": str(artifact_manifest_path),
    }


def _load_existing_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = load_json_or_yaml(path)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def _payload_matches_job(payload: dict[str, Any], job: dict[str, Any]) -> bool:
    expected = {
        "phase": str(job.get("phase") or "smoke"),
        "domain": normalize_domain(job["domain"]),
        "agent_id": str(job["agent_id"]),
        "case_unit_id": str(job["case_unit_id"]),
    }
    for key, expected_value in expected.items():
        if key not in payload or payload.get(key) is None:
            continue
        value = str(payload[key])
        if key == "domain":
            try:
                value = normalize_domain(value)
            except Exception:
                return False
        if value != expected_value:
            return False
    return True


def _llm_calls_are_successful(llm_dir: Path) -> bool:
    if not llm_dir.exists():
        return True
    for path in llm_dir.glob("*.json"):
        payload = _load_existing_mapping(path)
        if payload is None:
            return False
        metadata = payload.get("response_metadata")
        if isinstance(metadata, dict) and str(metadata.get("status") or "success").lower() != "success":
            return False
    return True


def _agentdojo_native_run_is_successful(root: Path) -> bool:
    summary = _load_existing_mapping(root / "native_run" / "run_summary.json")
    if summary is None or str(summary.get("status") or "").lower() != "completed":
        return False
    proxy_dir = root / "native_run" / "proxy_calls"
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


def _webarena_native_run_is_auditable(root: Path) -> bool:
    native_root = root / "native_run"
    summary = _load_existing_mapping(native_root / "run_summary.json")
    if summary is None or str(summary.get("status") or "").lower() != "completed":
        return False
    if bool(summary.get("used_expected_fallback")):
        return False
    if not bool(summary.get("llm_used")):
        return False
    runner_kind = str(summary.get("runner_kind") or "")
    fixes = summary.get("runner_fixes")
    if not isinstance(fixes, dict):
        return False

    task_id = summary.get("task_id")
    if task_id is None:
        return False
    task_dir = native_root / str(task_id)
    if runner_kind == "browsergym_agentlab":
        if fixes.get("action_set") != "webarena":
            return False
        if fixes.get("final_answer_protocol") != "send_msg_to_user_json":
            return False
        if fixes.get("loopback_url_host_policy") != "localhost":
            return False
        required = (
            native_root / "native_evaluator_input.json",
            native_root / "native_evaluator_output.json",
            native_root / "job.json",
            native_root / "source_bundle_entry.json",
            native_root / "worker_config.json",
            task_dir / "network.har",
            task_dir / "agent_response.json",
            task_dir / "solver_trace.json",
            task_dir / "eval_result.json",
            native_root / "browsergym_run" / "summary_info.json",
            native_root / "llm_attempts",
            root / "llm_calls" / "calls.jsonl",
        )
    elif runner_kind == "official_cli_playwright":
        if fixes.get("task_input") != "official_agent_input_get":
            return False
        if fixes.get("evaluator") != "official_eval_tasks":
            return False
        if fixes.get("browser") != "playwright":
            return False
        required = (
            native_root / "native_evaluator_input.json",
            native_root / "native_evaluator_output.json",
            native_root / "job.json",
            native_root / "source_bundle_entry.json",
            native_root / "worker_config.json",
            native_root / "webarena_config.json",
            native_root / "tasks.json",
            native_root / "browser_artifacts",
            native_root / "trajectory",
            native_root / "llm_attempts",
            task_dir / "network.har",
            task_dir / "agent_response.json",
            task_dir / "solver_trace.json",
            task_dir / "eval_result.json",
            root / "llm_calls" / "calls.jsonl",
        )
    elif runner_kind == "official_run_py_prompt":
        if fixes.get("agent_loop") != "official_run_py":
            return False
        if fixes.get("prompt") != "official_p_cot_id_actree_2s":
            return False
        if fixes.get("evaluator") != "official_evaluator_router":
            return False
        required = (
            native_root / "native_evaluator_input.json",
            native_root / "native_evaluator_output.json",
            native_root / "job.json",
            native_root / "source_bundle_entry.json",
            native_root / "worker_config.json",
            native_root / "webarena_env.json",
            native_root / "llm_attempts",
            native_root / "official_run",
            native_root / f"render_{task_id}.html",
            native_root / "traces" / f"{task_id}.zip",
            task_dir / "official_task_config.json",
            task_dir / "agent_response.json",
            task_dir / "solver_trace.json",
            root / "llm_calls" / "calls.jsonl",
        )
    else:
        return False
    if any(not path.exists() for path in required):
        return False
    if (root / "llm_calls" / "calls.jsonl").stat().st_size <= 0:
        return False

    solver_trace = _load_existing_mapping(task_dir / "solver_trace.json")
    native_output = _load_existing_mapping(native_root / "native_evaluator_output.json")
    if solver_trace is None or native_output is None:
        return False
    if bool(solver_trace.get("used_expected_fallback")):
        return False
    if str(solver_trace.get("runner_kind") or "") != runner_kind:
        return False
    trace_fixes = solver_trace.get("runner_fixes")
    if not isinstance(trace_fixes, dict):
        return False
    if trace_fixes != fixes:
        return False
    try:
        float(native_output.get("score"))
    except (TypeError, ValueError):
        return False
    if not str(native_output.get("status") or ""):
        return False
    if bool(summary.get("success")):
        if str(native_output.get("status") or "").lower() != "success":
            return False
        if float(native_output.get("score") or 0.0) < 1.0:
            return False
    return True


def resolve_infra_target(domain: str, infra_config: dict[str, Any]) -> InfraBenchmarkTarget:
    domain_key = normalize_domain(domain)
    constraint_roles = {
        role
        for name, roles in dict(infra_config.get("domain_machine_constraints") or {}).items()
        if normalize_domain_or_none(name) == domain_key
        for role in list(roles or [])
    }
    if not constraint_roles:
        raise ValueError(f"infra config has no machine-role constraint for {domain_key}")
    for machine in list(infra_config.get("machines") or []):
        if machine.get("enabled") is False:
            continue
        if str(machine.get("role")) not in constraint_roles:
            continue
        benchmark_name, benchmark_config = _benchmark_entry_for_domain(machine, domain_key)
        if benchmark_config is None:
            continue
        runner_command = str(benchmark_config.get("runner_command") or "").strip()
        if not runner_command:
            raise ValueError(f"benchmark {benchmark_name} on machine {machine.get('machine_id')} has no runner_command")
        return InfraBenchmarkTarget(
            machine_id=str(machine["machine_id"]),
            machine_role=str(machine["role"]),
            ssh_host=str(machine.get("ssh", {}).get("host") or ""),
            ssh_user=str(machine.get("ssh", {}).get("user") or ""),
            ssh_port=int(machine.get("ssh", {}).get("port") or 22),
            ssh_key_path=str(machine.get("ssh", {}).get("key_path") or ""),
            remote_workdir=str(machine.get("remote_workdir") or ""),
            runner_workdir=str(machine.get("runner_workdir") or machine.get("remote_workdir") or ""),
            benchmark_name=benchmark_name,
            benchmark_config=dict(benchmark_config),
            benchmark_config_hash=sha256_object(benchmark_config),
            runner_command=runner_command,
            machine_concurrency=int(machine.get("concurrency") or 1),
        )
    raise ValueError(f"no enabled machine with benchmark config found for {domain_key}")


def load_contract_index(contracts_dir: str | Path) -> dict[str, dict[str, dict[str, Any]]]:
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


def _benchmark_entry_for_domain(machine: dict[str, Any], domain: str) -> tuple[str, dict[str, Any] | None]:
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
