"""Stage controller for the execution-locked AgentDojo full evidence branch.

This controller never reads evaluator outputs, trajectories, prompts, or model
responses.  It plans the 2,847 locked job objects, selects only the immutable
promotion samples, and consumes content-free machine health receipts between
stages.  Checklist artifacts are not loaded by the execution-lock planner.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import errno
import fcntl
import json
import os
from pathlib import Path
import shutil
import shlex
import stat
import tempfile
import threading
import time
from typing import Any
import uuid

from evidence_system.contracts.agentdojo_full_execution import (
    DEFAULT_EXECUTION_LOCK,
    EXPECTED_AGENTS,
    EXPECTED_RECORD_SLOT_COUNT,
    ExecutionLockResult,
    verify_job_binding,
    verify_execution_lock,
)
from evidence_system.contracts.agentdojo_execution_namespace import (
    DEFAULT_NAMESPACE_INIT_RECEIPT,
    FORMAL_STAGE_ORDER,
    verify_formal_namespace_init_receipt,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_BUNDLE,
)
from evidence_system.contracts.common import ContractLifecycleError, utc_now_iso
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.adapters.agentdojo_runtime_control import (
    agentdojo_model_config_sha256,
    build_formal_locked_stage_workload,
    execution_runtime_snapshot,
    load_runtime_policy,
    resource_worker_process_binding_sha256,
)
from evidence_system.adapters.runtime import (
    formal_job_binding_sha256,
    formal_job_file_sha256,
    run_remote_blind_command,
)
from evidence_system.orchestrator.jobs import (
    ExecutedJob,
    PlannedJob,
    execute_planned_jobs,
    plan_adapter_execution,
    plan_smoke_jobs,
    resolve_infra_target,
)


STAGING_NAMESPACE = "agentdojo_full_v1.2.2_direct_execution_staging"
DEFAULT_LOCKED_PLAN_ROOT = Path(
    "experiments/agentdojo_full_v1.2.2_direct/execution_plan"
)
DEFAULT_LOCKED_JOBS_DIR = None
DEFAULT_JOB_PLAN_INDEX = None
DEFAULT_STAGE_RECEIPT_ROOT = (
    Path("results/namespaces") / STAGING_NAMESPACE / "provenance/formal_stage_receipts"
)
DEFAULT_STAGE_EXECUTION_ROOT = DEFAULT_STAGE_RECEIPT_ROOT / "execution_observations"
DEFAULT_STAGE_AUTHORIZATION_ROOT = DEFAULT_STAGE_RECEIPT_ROOT / "authorizations"
DEFAULT_STAGE_INTENT_ROOT = DEFAULT_STAGE_RECEIPT_ROOT / "intents"
DEFAULT_CONTROLLER_LIFECYCLE_LOCK = (
    Path("experiments/agentdojo_full_v1.2.2_direct/runtime/controller")
    / ".formal-controller.lifecycle.lock"
)
DEFAULT_MACHINE_HEALTH_ROOT = DEFAULT_STAGE_RECEIPT_ROOT / "machine_health"
DEFAULT_STAGE_WORKLOAD_ROOT = DEFAULT_STAGE_RECEIPT_ROOT / "health_workloads"
DEFAULT_COMPLETION_RECEIPT = (
    Path("results/namespaces")
    / STAGING_NAMESPACE
    / "provenance/formal_execution_completion_receipt.json"
)
DEFAULT_ANOMALY_RECEIPT = (
    Path("results/namespaces")
    / STAGING_NAMESPACE
    / "provenance/formal_execution_anomaly_receipt.json"
)
DEFAULT_REMOTE_COMPLETION_INDEX = (
    Path("results/namespaces")
    / STAGING_NAMESPACE
    / "provenance/formal_remote_completion_index.json"
)
STAGE_ORDER = FORMAL_STAGE_ORDER


HealthVerifier = Callable[..., Mapping[str, Any]]
Executor = Callable[..., list[ExecutedJob]]


@dataclass(frozen=True)
class LockedEvidencePlan:
    execution: ExecutionLockResult
    lock_payload: dict[str, Any]
    planned: tuple[PlannedJob, ...]
    by_slot: dict[str, PlannedJob]
    plan_index_path: Path
    plan_index_sha256: str


@dataclass(frozen=True)
class LockedStage:
    stage_id: str
    workers: int
    planned: tuple[PlannedJob, ...]
    record_slot_ids_sha256: str
    sequence_predecessor_stage_id: str | None
    health_parent_stage_id: str | None
    health_parent_agent_id: str | None


def build_and_verify_locked_plan(
    *,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    infra_config_path: str | Path,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    jobs_dir: str | Path | None = DEFAULT_LOCKED_JOBS_DIR,
    plan_index_path: str | Path | None = DEFAULT_JOB_PLAN_INDEX,
) -> LockedEvidencePlan:
    """Materialize and verify the exact 949 x 3 execution-bound job files."""

    execution = verify_execution_lock(
        lock_path=execution_lock_path,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        agents_config_path=agents_config_path,
        runtime_infra_path=infra_config_path,
    )
    lock_payload = json.loads(execution.lock_path.read_text(encoding="utf-8"))
    if not isinstance(lock_payload, dict):
        raise ContractLifecycleError("execution lock payload is not an object")
    promotion = dict(
        execution.definition["concurrency_policy"]["promotion_policy"]
    )
    if promotion.get("formal_stage_order") != list(STAGE_ORDER):
        raise ContractLifecycleError("execution lock formal stage order is stale")
    canonical_root = resolve_repo_path(
        DEFAULT_LOCKED_PLAN_ROOT / execution.lock_sha256
    )
    canonical_jobs_dir = canonical_root / "jobs"
    canonical_index_path = canonical_root / "plan_index.json"
    if jobs_dir is not None and resolve_repo_path(jobs_dir) != canonical_jobs_dir:
        raise ContractLifecycleError(
            "formal jobs must use the execution-lock-derived canonical plan path"
        )
    if (
        plan_index_path is not None
        and resolve_repo_path(plan_index_path) != canonical_index_path
    ):
        raise ContractLifecycleError(
            "formal plan index must use the execution-lock-derived canonical path"
        )
    if canonical_root.exists() or canonical_root.is_symlink():
        return _load_existing_locked_plan(
            execution=execution,
            lock_payload=lock_payload,
            canonical_root=canonical_root,
            manifest_path=manifest_path,
            source_bundle_path=source_bundle_path,
            infra_config_path=infra_config_path,
            agents_config_path=agents_config_path,
        )
    canonical_root.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=f".{execution.lock_sha256}.",
            suffix=".tmp",
            dir=canonical_root.parent,
        )
    )
    temporary_jobs_dir = temporary_root / "jobs"
    planned = plan_smoke_jobs(
        domain="agentdojo",
        phase="full",
        experiment_type="appendix",
        case_count=None,
        agent_ids=list(EXPECTED_AGENTS),
        seed=int(execution.definition["job_plan"]["base_seed"]),
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        # Ignored by the execution-lock branch; this explicit non-checklist
        # path documents and tests the branch separation.
        contracts_dir=resolve_repo_path(
            "experiments/agentdojo_full_v1.2.2_direct/runtime/no_checklist_inputs"
        ),
        infra_config_path=infra_config_path,
        agents_config_path=agents_config_path,
        jobs_dir=temporary_jobs_dir,
        result_namespace=None,
        execution_lock_path=execution.lock_path,
    )
    locked_entries = list(execution.definition["job_plan"]["entries"])
    if len(planned) != EXPECTED_RECORD_SLOT_COUNT or len(locked_entries) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("locked job planner must contain exactly 2,847 entries")
    planned_projection = [
        {
            field: item.job[field]
            for field in (
                "job_id",
                "case_unit_id",
                "task_id",
                "record_slot_id",
                "run_id",
                "attempt_id",
                "seed",
                "agent_id",
                "force_rerun",
                "rerun_completed",
                "formal_wall_clock_timeout_seconds",
            )
        }
        for item in planned
    ]
    if planned_projection != locked_entries:
        raise ContractLifecycleError("materialized job order/mapping differs from execution lock")
    if any(item.execution_plan.get("status") != "runnable" for item in planned):
        blocked = Counter(str(item.execution_plan.get("status")) for item in planned)
        raise ContractLifecycleError(f"locked planner contains non-runnable jobs: {dict(blocked)}")
    if len({item.job["record_slot_id"] for item in planned}) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("materialized job plan contains duplicate record slots")
    if any(item.job.get("execution_lock_sha256") != execution.lock_sha256 for item in planned):
        raise ContractLifecycleError("materialized job is not bound to the current execution lock")

    jobs_root = temporary_jobs_dir
    expected_job_paths = {item.job_path.resolve() for item in planned}
    observed_job_paths = {
        path.resolve()
        for path in jobs_root.glob("full-agentdojo-*.json")
        if path.is_file()
    }
    if observed_job_paths != expected_job_paths:
        raise ContractLifecycleError(
            "job-plan directory differs from the locked 2,847-file namespace"
        )
    index_entries = [
        {
            "job_id": item.job["job_id"],
            "record_slot_id": item.job["record_slot_id"],
            "agent_id": item.job["agent_id"],
            "path": _display(canonical_jobs_dir / item.job_path.name),
            "sha256": sha256_file(item.job_path),
            "execution_lock_sha256": item.job["execution_lock_sha256"],
        }
        for item in planned
    ]
    index = {
        "schema_version": "agentdojo_locked_job_plan_index/v2",
        "result_namespace": STAGING_NAMESPACE,
        "canonical_plan_root": _display(canonical_root),
        "execution_lock_path": _display(execution.lock_path),
        "execution_lock_sha256": execution.lock_sha256,
        "execution_policy_sha256": execution.definition["execution_policy_sha256"],
        "job_count": EXPECTED_RECORD_SLOT_COUNT,
        "record_slot_count": EXPECTED_RECORD_SLOT_COUNT,
        "agent_batch_order": list(EXPECTED_AGENTS),
        "job_mapping_sha256": execution.definition["job_plan"]["mapping_sha256"],
        "entries_sha256": sha256_object(index_entries),
        "entries": index_entries,
    }
    temporary_index_path = temporary_root / "plan_index.json"
    _write_identical_or_new(temporary_index_path, index)
    _fsync_plan_tree(temporary_root)
    if canonical_root.exists() or canonical_root.is_symlink():
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise ContractLifecycleError(
            "canonical formal plan destination appeared during publication"
        )
    os.rename(temporary_root, canonical_root)
    _fsync_directory(canonical_root.parent)
    return _load_existing_locked_plan(
        execution=execution,
        lock_payload=lock_payload,
        canonical_root=canonical_root,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        infra_config_path=infra_config_path,
        agents_config_path=agents_config_path,
    )


def _load_existing_locked_plan(
    *,
    execution: ExecutionLockResult,
    lock_payload: Mapping[str, Any],
    canonical_root: Path,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    infra_config_path: str | Path,
    agents_config_path: str | Path,
) -> LockedEvidencePlan:
    """Load an already published canonical plan without rewriting one byte."""

    if canonical_root.is_symlink() or not canonical_root.is_dir():
        raise ContractLifecycleError("canonical formal plan root is not a directory")
    observed_root = {path.name for path in canonical_root.iterdir()}
    if observed_root != {"jobs", "plan_index.json"}:
        raise ContractLifecycleError(
            "canonical formal plan root contains unexpected entries"
        )
    jobs_root = canonical_root / "jobs"
    index_path = canonical_root / "plan_index.json"
    for path, label in ((jobs_root, "jobs directory"), (index_path, "plan index")):
        info = path.lstat()
        expected_kind = stat.S_ISDIR if path == jobs_root else stat.S_ISREG
        if path.is_symlink() or not expected_kind(info.st_mode) or info.st_nlink != 1:
            raise ContractLifecycleError(
                f"canonical formal {label} is linked, symlinked, or wrong type"
            )
    job_paths = sorted(jobs_root.iterdir(), key=lambda value: value.name)
    if len(job_paths) != EXPECTED_RECORD_SLOT_COUNT or any(
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_nlink != 1
        or path.suffix != ".json"
        for path in job_paths
    ):
        raise ContractLifecycleError(
            "canonical formal jobs directory is not exactly 2,847 regular files"
        )

    index = load_mapping(index_path)
    expected_index_fields = {
        "schema_version",
        "result_namespace",
        "canonical_plan_root",
        "execution_lock_path",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "job_count",
        "record_slot_count",
        "agent_batch_order",
        "job_mapping_sha256",
        "entries_sha256",
        "entries",
    }
    if set(index) != expected_index_fields or (
        index.get("schema_version") != "agentdojo_locked_job_plan_index/v2"
        or index.get("result_namespace") != STAGING_NAMESPACE
        or index.get("canonical_plan_root") != _display(canonical_root)
        or index.get("execution_lock_path") != _display(execution.lock_path)
        or index.get("execution_lock_sha256") != execution.lock_sha256
        or index.get("execution_policy_sha256")
        != execution.definition["execution_policy_sha256"]
        or index.get("job_count") != EXPECTED_RECORD_SLOT_COUNT
        or index.get("record_slot_count") != EXPECTED_RECORD_SLOT_COUNT
        or index.get("agent_batch_order") != list(EXPECTED_AGENTS)
        or index.get("job_mapping_sha256")
        != execution.definition["job_plan"]["mapping_sha256"]
    ):
        raise ContractLifecycleError("canonical formal plan-index binding is stale")
    entries = list(index.get("entries") or [])
    if len(entries) != EXPECTED_RECORD_SLOT_COUNT or index.get(
        "entries_sha256"
    ) != sha256_object(entries):
        raise ContractLifecycleError("canonical formal plan-index denominator differs")

    expected_mapping = list(execution.definition["job_plan"]["entries"])
    bundle = load_mapping(source_bundle_path)
    infra = load_mapping(infra_config_path)
    target = resolve_infra_target("agentdojo", infra)
    manifest = load_mapping(manifest_path)
    domain_blocks = [
        dict(value)
        for value in list(manifest.get("domains") or [])
        if str(value.get("domain") or "").lower().replace("-", "_")
        == "agentdojo"
    ]
    if len(domain_blocks) != 1:
        raise ContractLifecycleError("canonical formal manifest has no unique AgentDojo block")
    official_split_hash = str(
        domain_blocks[0].get("official_split_hash") or "0" * 64
    )

    planned: list[PlannedJob] = []
    indexed_paths: set[Path] = set()
    for ordinal, (entry, expected_mapping_entry) in enumerate(
        zip(entries, expected_mapping, strict=True)
    ):
        if not isinstance(entry, Mapping):
            raise ContractLifecycleError("canonical formal plan entry is not an object")
        expected_entry_fields = {
            "job_id",
            "record_slot_id",
            "agent_id",
            "path",
            "sha256",
            "execution_lock_sha256",
        }
        if set(entry) != expected_entry_fields:
            raise ContractLifecycleError("canonical formal plan entry fields differ")
        expected_job_path = jobs_root / f"{expected_mapping_entry['job_id']}.json"
        indexed_path = resolve_repo_path(str(entry["path"]))
        if indexed_path != expected_job_path or indexed_path in indexed_paths:
            raise ContractLifecycleError(
                "canonical formal plan entry path/order is not exact"
            )
        indexed_paths.add(indexed_path)
        if entry.get("sha256") != sha256_file(indexed_path):
            raise ContractLifecycleError("canonical formal job file hash is stale")
        job = load_mapping(indexed_path)
        if formal_job_file_sha256(job) != entry["sha256"]:
            raise ContractLifecycleError("canonical formal job bytes are not canonical")
        verify_job_binding(
            job,
            lock_payload,
            lock_path=execution.lock_path,
            lock_sha256=execution.lock_sha256,
        )
        projection = {
            field: job[field]
            for field in expected_mapping_entry
        }
        if projection != dict(expected_mapping_entry) or (
            entry.get("job_id") != job.get("job_id")
            or entry.get("record_slot_id") != job.get("record_slot_id")
            or entry.get("agent_id") != job.get("agent_id")
            or entry.get("execution_lock_sha256") != execution.lock_sha256
        ):
            raise ContractLifecycleError(
                f"canonical formal job mapping differs at ordinal {ordinal}"
            )
        execution_plan = plan_adapter_execution(
            dict(job),
            target=target,
            agents_config_path=str(agents_config_path),
            dotenv_path=".env",
            source_bundle_path=str(source_bundle_path),
            bundle=bundle,
        )
        if execution_plan.get("status") != "runnable":
            raise ContractLifecycleError("canonical formal job is not runnable")
        planned.append(
            PlannedJob(
                job=dict(job),
                job_path=indexed_path,
                official_split_hash=official_split_hash,
                execution_plan=execution_plan,
            )
        )
    if indexed_paths != set(job_paths):
        raise ContractLifecycleError("canonical formal plan has unindexed job files")
    by_slot = {str(item.job["record_slot_id"]): item for item in planned}
    if len(by_slot) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("canonical formal plan contains duplicate slots")
    return LockedEvidencePlan(
        execution=execution,
        lock_payload=dict(lock_payload),
        planned=tuple(planned),
        by_slot=by_slot,
        plan_index_path=index_path,
        plan_index_sha256=sha256_file(index_path),
    )


def _fsync_plan_tree(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda value: len(value.parts),
        reverse=True,
    ):
        _fsync_directory(directory)
    _fsync_directory(root)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def select_locked_stage(plan: LockedEvidencePlan, stage_id: str) -> LockedStage:
    if stage_id not in STAGE_ORDER:
        raise ContractLifecycleError(f"unsupported locked evidence stage: {stage_id}")
    promotion = dict(plan.execution.definition["concurrency_policy"]["promotion_policy"])
    if stage_id == "canary":
        workers = 4
        slots = list(dict(promotion["canary"])["record_slot_ids"])
    elif stage_id.startswith("ramp-"):
        _, agent_suffix, worker_text = stage_id.split("-", 2)
        workers = int(worker_text)
        agent_id = {"a": "Agent A", "b": "Agent B", "c": "Agent C"}[
            agent_suffix
        ]
        matching = [
            dict(value)
            for value in dict(promotion["agent_ramp_stages"])[agent_id]
            if int(value["workers"]) == workers
        ]
        if len(matching) != 1:
            raise ContractLifecycleError(f"locked promotion sample missing for {stage_id}")
        slots = list(matching[0]["record_slot_ids"])
    else:
        kind, agent_suffix = stage_id.split("-", 1)
        agent_id = {"a": "Agent A", "b": "Agent B", "c": "Agent C"}[agent_suffix]
        workers = int(plan.execution.definition["concurrency_policy"]["maximum_workers"])
        if kind == "remaining":
            excluded = set(dict(promotion["canary"])["record_slot_ids"])
            for ramps in dict(promotion["agent_ramp_stages"]).values():
                for ramp in ramps:
                    excluded.update(ramp["record_slot_ids"])
            slots = [
                str(item.job["record_slot_id"])
                for item in plan.planned
                if item.job["agent_id"] == agent_id
                and item.job["record_slot_id"] not in excluded
            ]
        else:
            slots = [
                str(item.job["record_slot_id"])
                for item in plan.planned
                if item.job["agent_id"] == agent_id
            ]
    selected = tuple(_select_exact_slots(plan, slots))
    sequence_predecessor = (
        STAGE_ORDER[STAGE_ORDER.index(stage_id) - 1]
        if STAGE_ORDER.index(stage_id) > 0
        else None
    )
    health_parent_stage, health_parent_agent = _health_parent(stage_id)
    return LockedStage(
        stage_id=stage_id,
        workers=workers,
        planned=selected,
        record_slot_ids_sha256=sha256_object(slots),
        sequence_predecessor_stage_id=sequence_predecessor,
        health_parent_stage_id=health_parent_stage,
        health_parent_agent_id=health_parent_agent,
    )


def run_locked_stage(
    plan: LockedEvidencePlan,
    stage: LockedStage,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    infra_config_path: str | Path,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    executor: Executor = execute_planned_jobs,
    receipt_root: str | Path = DEFAULT_STAGE_RECEIPT_ROOT,
    execution_observation_root: str | Path = DEFAULT_STAGE_EXECUTION_ROOT,
    namespace_init_receipt_path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
    namespace_verifier: Callable[..., Any] = verify_formal_namespace_init_receipt,
    stage_authorization_root: str | Path = DEFAULT_STAGE_AUTHORIZATION_ROOT,
    authorization_closer: Callable[..., None] | None = None,
    stage_intent_root: str | Path = DEFAULT_STAGE_INTENT_ROOT,
    controller_lifecycle_lock_path: str | Path = DEFAULT_CONTROLLER_LIFECYCLE_LOCK,
    _controller_lock_held: bool = False,
) -> dict[str, Any]:
    """Run one immutable stage; operational failures are recorded and continued."""

    if not _controller_lock_held:
        with _controller_lifecycle_lock(controller_lifecycle_lock_path):
            return run_locked_stage(
                plan,
                stage,
                manifest_path=manifest_path,
                source_bundle_path=source_bundle_path,
                infra_config_path=infra_config_path,
                agents_config_path=agents_config_path,
                executor=executor,
                receipt_root=receipt_root,
                execution_observation_root=execution_observation_root,
                namespace_init_receipt_path=namespace_init_receipt_path,
                namespace_verifier=namespace_verifier,
                stage_authorization_root=stage_authorization_root,
                authorization_closer=authorization_closer,
                stage_intent_root=stage_intent_root,
                controller_lifecycle_lock_path=controller_lifecycle_lock_path,
                _controller_lock_held=True,
            )

    namespace = namespace_verifier(
        namespace_init_receipt_path,
        execution_lock_path=plan.execution.lock_path,
        plan_index_path=plan.plan_index_path,
    )
    namespace_path = Path(namespace.path)
    namespace_sha256 = str(namespace.sha256)
    receipt_directory = resolve_repo_path(receipt_root)
    final_receipt_path = receipt_directory / f"{stage.stage_id}.json"
    observation_path = resolve_repo_path(execution_observation_root) / f"{stage.stage_id}.json"
    if final_receipt_path.exists():
        raise ContractLifecycleError(
            f"formal execution stage is already sealed: {stage.stage_id}"
        )
    stage_index = STAGE_ORDER.index(stage.stage_id)
    if stage_index:
        previous_stage = STAGE_ORDER[stage_index - 1]
        previous_stage_path = receipt_directory / f"{previous_stage}.json"
        if previous_stage_path.is_symlink() or not previous_stage_path.is_file():
            raise ContractLifecycleError(
                f"{stage.stage_id} cannot run before immutable {previous_stage} receipt"
            )
        previous_stage_receipt = json.loads(
            previous_stage_path.read_text(encoding="utf-8")
        )
        if (
            previous_stage_receipt.get("stage_id") != previous_stage
            or previous_stage_receipt.get("execution_lock_sha256")
            != plan.execution.lock_sha256
            or previous_stage_receipt.get("execution_policy_sha256")
            != plan.execution.definition["execution_policy_sha256"]
        ):
            raise ContractLifecycleError("previous formal stage receipt binding is stale")

    effective_workers, finalized_model_ceiling = _finalized_stage_worker_ceiling(
        plan, stage
    )
    health_decision: dict[str, Any] | None = None
    if stage.health_parent_stage_id is not None:
        previous_final = json.loads(
            (receipt_directory / f"{stage.health_parent_stage_id}.json").read_text(
                encoding="utf-8"
            )
        )
        health_decision = _stage_health_decision(
            previous_final,
            parent_stage_id=stage.health_parent_stage_id,
            agent_id=stage.health_parent_agent_id,
        )
        if health_decision.get("promotion_authorized") is not True:
            safe_workers = int(health_decision.get("safe_workers") or 0)
            locked_workers = list(
                plan.execution.definition["concurrency_policy"]["ramp_workers"]
            )
            if safe_workers not in locked_workers or safe_workers > stage.workers:
                raise ContractLifecycleError(
                    "prior failed health gate does not bind a valid safe concurrency"
                )
            effective_workers = min(effective_workers, safe_workers)

    sequence_ref = _optional_path_lock(
        receipt_directory,
        stage.sequence_predecessor_stage_id,
    )
    health_parent_ref = _optional_path_lock(
        receipt_directory,
        stage.health_parent_stage_id,
    )
    authorization_path = (
        resolve_repo_path(stage_authorization_root) / f"{stage.stage_id}.json"
    )
    intent_path = resolve_repo_path(stage_intent_root) / f"{stage.stage_id}.json"
    intent = _load_or_publish_stage_intent(
        path=intent_path,
        plan=plan,
        stage=stage,
        effective_workers=effective_workers,
        namespace_path=namespace_path,
        namespace_sha256=namespace_sha256,
        authorization_path=authorization_path,
    )
    authorization = _publish_stage_authorization(
        path=authorization_path,
        plan=plan,
        stage=stage,
        effective_workers=effective_workers,
        namespace_path=namespace_path,
        namespace_sha256=namespace_sha256,
        sequence_predecessor_receipt=sequence_ref,
        health_parent_receipt=health_parent_ref,
        health_decision=health_decision,
        session_id=str(intent["session_id"]),
        created_at=str(intent["created_at"]),
    )

    close_authorization = authorization_closer or _close_remote_stage_authorization
    if observation_path.exists() or observation_path.is_symlink():
        observation = _load_current_stage_observation(
            observation_path, plan=plan, stage=stage, authorization=authorization
        )
        close_authorization(
            infra_config_path=infra_config_path,
            remote_path=authorization["_controller_context"][
                "authorization_remote_path"
            ],
            expected_sha256=sha256_file(authorization_path),
            runtime_state_root=authorization["runtime_state_root"],
        )
        return {
            **observation,
            "observation_path": _display(observation_path),
            "observation_sha256": sha256_file(observation_path),
            "requires_post_stage_machine_health_receipt": True,
            "resumed_after_observation_publication": True,
        }

    started_at = utc_now_iso()
    executed = executor(
        stage.planned,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        infra_config_path=infra_config_path,
        agents_config_path=agents_config_path,
        max_workers=effective_workers,
        fail_fast_on_noncompleted=True,
        skip_completed=True,
        retry_no_response_attempts=int(
            plan.execution.definition["failure_policy"][
                "retry_transient_model_attempts"
            ]
        ),
        continue_on_error=True,
        locked_stage_authorization_path=authorization_path,
        locked_stage_authorization_context=dict(
            authorization["_controller_context"]
        ),
    )
    ended_at = utc_now_iso()
    if len(executed) != len(stage.planned):
        raise ContractLifecycleError("stage executor did not return every planned slot")
    status_counts = Counter(
        str(item.execution_result.get("status") or "unknown") for item in executed
    )
    completion_entries = [
        {
            field: item.execution_result[field]
            for field in (
                "job_identity_sha256",
                "job_binding_sha256",
                "artifact_tree_sha256",
                "artifact_file_count",
                "artifact_total_bytes",
                "completion_marker_semantic_sha256",
            )
        }
        for item in executed
        if item.execution_result.get("status")
        in {"sealed_remote_completed", "sealed_remote_reused"}
    ]
    sealed_status_count = int(status_counts.get("sealed_remote_completed", 0)) + int(
        status_counts.get("sealed_remote_reused", 0)
    )
    if len(completion_entries) != sealed_status_count:
        raise ContractLifecycleError("sealed completion projection denominator differs")
    observation = {
        "schema_version": "agentdojo_formal_stage_execution_observation/v1",
        "stage_id": stage.stage_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "execution_lock_sha256": plan.execution.lock_sha256,
        "execution_policy_sha256": plan.execution.definition[
            "execution_policy_sha256"
        ],
        "plan_index_sha256": plan.plan_index_sha256,
        "locked_workers": stage.workers,
        "effective_workers": effective_workers,
        "finalized_model_worker_ceiling": finalized_model_ceiling,
        "planned_record_slot_count": len(stage.planned),
        "record_slot_ids_sha256": stage.record_slot_ids_sha256,
        "status_counts": dict(sorted(status_counts.items())),
        "blind_completion_entry_count": len(completion_entries),
        "blind_completion_entries_sha256": sha256_object(completion_entries),
        "blind_completion_entries": completion_entries,
        "returned_record_slot_count": len(executed),
        "continue_on_error": True,
        "never_rerun_completed": True,
        "blind_only": True,
        "contains_prompt_response_trajectory_evaluator_or_label": False,
        "namespace_init_receipt": {
            "path": _display(namespace_path),
            "sha256": namespace_sha256,
        },
        "stage_authorization": {
            "path": _display(authorization_path),
            "sha256": sha256_file(authorization_path),
            "session_id": authorization["session_id"],
            "remote_path": authorization["_controller_context"][
                "authorization_remote_path"
            ],
        },
        "sequence_predecessor_receipt": (
            sequence_ref
        ),
        "health_parent": {
            "stage_id": stage.health_parent_stage_id,
            "agent_id": stage.health_parent_agent_id,
        },
    }
    _write_identical_or_new(observation_path, observation)
    # The immutable observation is the crash-resume boundary.  Admission is
    # closed only after it is durable, so an interrupted controller can always
    # reconcile the same session without inventing another authorization.
    close_authorization(
        infra_config_path=infra_config_path,
        remote_path=authorization["_controller_context"][
            "authorization_remote_path"
        ],
        expected_sha256=sha256_file(authorization_path),
        runtime_state_root=authorization["runtime_state_root"],
    )
    return {
        **observation,
        "observation_path": _display(observation_path),
        "observation_sha256": sha256_file(observation_path),
        "requires_post_stage_machine_health_receipt": True,
    }


def seal_locked_stage(
    plan: LockedEvidencePlan,
    stage: LockedStage,
    *,
    post_stage_health_receipt_path: str | Path,
    health_verifier: HealthVerifier | None = None,
    receipt_root: str | Path = DEFAULT_STAGE_RECEIPT_ROOT,
    execution_observation_root: str | Path = DEFAULT_STAGE_EXECUTION_ROOT,
    namespace_init_receipt_path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
    namespace_verifier: Callable[..., Any] = verify_formal_namespace_init_receipt,
    controller_lifecycle_lock_path: str | Path = DEFAULT_CONTROLLER_LIFECYCLE_LOCK,
    _controller_lock_held: bool = False,
) -> dict[str, Any]:
    """Bind a machine-generated blind health receipt to a completed stage."""

    if not _controller_lock_held:
        with _controller_lifecycle_lock(controller_lifecycle_lock_path):
            return seal_locked_stage(
                plan,
                stage,
                post_stage_health_receipt_path=post_stage_health_receipt_path,
                health_verifier=health_verifier,
                receipt_root=receipt_root,
                execution_observation_root=execution_observation_root,
                namespace_init_receipt_path=namespace_init_receipt_path,
                namespace_verifier=namespace_verifier,
                controller_lifecycle_lock_path=controller_lifecycle_lock_path,
                _controller_lock_held=True,
            )

    namespace_verifier(
        namespace_init_receipt_path,
        execution_lock_path=plan.execution.lock_path,
        plan_index_path=plan.plan_index_path,
    )
    receipt_directory = resolve_repo_path(receipt_root)
    receipt_path = receipt_directory / f"{stage.stage_id}.json"
    if receipt_path.exists():
        existing = load_mapping(receipt_path)
        if (
            existing.get("stage_id") != stage.stage_id
            or existing.get("execution_lock_sha256") != plan.execution.lock_sha256
        ):
            raise ContractLifecycleError(
                f"formal stage has a stale sealed receipt: {stage.stage_id}"
            )
        return {
            **existing,
            "receipt_path": _display(receipt_path),
            "receipt_sha256": sha256_file(receipt_path),
            "resumed_already_sealed": True,
        }
    observation_path = resolve_repo_path(execution_observation_root) / f"{stage.stage_id}.json"
    if observation_path.is_symlink() or not observation_path.is_file():
        raise ContractLifecycleError(
            f"formal stage execution observation is missing: {stage.stage_id}"
        )
    observation = json.loads(observation_path.read_text(encoding="utf-8"))
    if (
        observation.get("execution_lock_sha256") != plan.execution.lock_sha256
        or observation.get("execution_policy_sha256")
        != plan.execution.definition["execution_policy_sha256"]
        or observation.get("stage_id") != stage.stage_id
        or observation.get("record_slot_ids_sha256")
        != stage.record_slot_ids_sha256
    ):
        raise ContractLifecycleError("formal stage execution observation binding is stale")
    health_path = resolve_repo_path(post_stage_health_receipt_path)
    if health_path.is_symlink() or not health_path.is_file():
        raise ContractLifecycleError("post-stage machine health receipt is missing")
    verifier = health_verifier or _default_health_verifier
    health = dict(
        verifier(
            health_path,
            expected_execution_lock_sha256=plan.execution.lock_sha256,
            expected_execution_policy_sha256=plan.execution.definition[
                "execution_policy_sha256"
            ],
            expected_stage_id=stage.stage_id,
            expected_workers=int(observation["effective_workers"]),
            expected_record_slot_count=len(stage.planned),
            expected_record_slot_ids_sha256=stage.record_slot_ids_sha256,
        )
    )
    if health.get("blind_only") is not True:
        raise ContractLifecycleError("formal stage health receipt is not blind-only")
    model_decisions: list[dict[str, Any]] = []
    if stage.stage_id == "canary":
        model_decisions = [
            dict(row)
            for row in list(health.get("model_decisions") or [])
            if isinstance(row, Mapping)
        ]
        if [row.get("agent_id") for row in model_decisions] != list(
            EXPECTED_AGENTS
        ):
            raise ContractLifecycleError(
                "canary machine health must contain ordered independent A/B/C decisions"
            )
        for row in model_decisions:
            if (
                not isinstance(row.get("promotion_authorized"), bool)
                or int(row.get("safe_workers") or 0) != 4
            ):
                raise ContractLifecycleError(
                    "canary per-model health decision is invalid"
                )
    (
        health_reported_promotion,
        ran_at_locked_target,
        promotion_authorized,
    ) = _locked_target_promotion_decision(
        health,
        locked_workers=stage.workers,
        effective_workers=int(observation["effective_workers"]),
    )
    safe_workers = int(health.get("safe_workers") or 0)
    locked_workers = list(
        plan.execution.definition["concurrency_policy"]["ramp_workers"]
    )
    if safe_workers not in locked_workers or safe_workers > int(
        observation["effective_workers"]
    ):
        raise ContractLifecycleError("machine health receipt safe concurrency is invalid")
    receipt = {
        "schema_version": "agentdojo_formal_stage_receipt/v1",
        "stage_id": stage.stage_id,
        "sealed_at": utc_now_iso(),
        "execution_lock_sha256": plan.execution.lock_sha256,
        "execution_policy_sha256": plan.execution.definition[
            "execution_policy_sha256"
        ],
        "record_slot_ids_sha256": stage.record_slot_ids_sha256,
        "record_slot_count": len(stage.planned),
        "locked_workers": stage.workers,
        "effective_workers": int(observation["effective_workers"]),
        "execution_observation": {
            "path": _display(observation_path),
            "sha256": sha256_file(observation_path),
        },
        "post_stage_machine_health_receipt": {
            "path": _display(health_path),
            "sha256": sha256_file(health_path),
        },
        "promotion_authorized": promotion_authorized,
        "health_reported_promotion": health_reported_promotion,
        "ran_at_locked_target": ran_at_locked_target,
        "safe_workers": safe_workers,
        "model_decisions": model_decisions,
        "health_decision": (
            "promote_from_locked_target"
            if promotion_authorized
            else (
                "hold_prior_safe_concurrency_effective_below_locked_target"
                if not ran_at_locked_target
                else "fallback_to_prior_safe_concurrency_and_continue"
            )
        ),
        "status_counts": dict(observation["status_counts"]),
        "blind_completion_entry_count": int(
            observation["blind_completion_entry_count"]
        ),
        "blind_completion_entries_sha256": str(
            observation["blind_completion_entries_sha256"]
        ),
        "blind_only": True,
        "contains_prompt_response_trajectory_evaluator_or_label": False,
    }
    _write_identical_or_new(receipt_path, receipt)
    return {
        **receipt,
        "receipt_path": _display(receipt_path),
        "receipt_sha256": sha256_file(receipt_path),
    }


def finalize_formal_execution_receipts(
    plan: LockedEvidencePlan,
    *,
    receipt_root: str | Path = DEFAULT_STAGE_RECEIPT_ROOT,
    completion_path: str | Path = DEFAULT_COMPLETION_RECEIPT,
    anomaly_path: str | Path = DEFAULT_ANOMALY_RECEIPT,
    remote_completion_index_path: str | Path = DEFAULT_REMOTE_COMPLETION_INDEX,
    namespace_init_receipt_path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
    namespace_verifier: Callable[..., Any] = verify_formal_namespace_init_receipt,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Freeze blind completion/anomaly aggregates after the recovery stage."""

    namespace = namespace_verifier(
        namespace_init_receipt_path,
        execution_lock_path=plan.execution.lock_path,
        plan_index_path=plan.plan_index_path,
    )
    receipt_directory = resolve_repo_path(receipt_root)
    stage_index: list[dict[str, str]] = []
    stage_payloads: dict[str, dict[str, Any]] = {}
    for stage_id in STAGE_ORDER:
        path = receipt_directory / f"{stage_id}.json"
        if path.is_symlink() or not path.is_file():
            raise ContractLifecycleError(
                f"cannot finalize formal execution without {stage_id} receipt"
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ContractLifecycleError(f"formal stage receipt is not an object: {stage_id}")
        if (
            payload.get("stage_id") != stage_id
            or payload.get("execution_lock_sha256") != plan.execution.lock_sha256
            or payload.get("execution_policy_sha256")
            != plan.execution.definition["execution_policy_sha256"]
            or payload.get("blind_only") is not True
            or payload.get("contains_prompt_response_trajectory_evaluator_or_label")
            is not False
        ):
            raise ContractLifecycleError(f"formal stage receipt binding is invalid: {stage_id}")
        stage_payloads[stage_id] = payload
        stage_index.append(
            {"stage_id": stage_id, "path": _display(path), "sha256": sha256_file(path)}
        )

    final_counts: Counter[str] = Counter()
    remote_entries: list[dict[str, Any]] = []
    for stage_id in ("recovery-a", "recovery-b", "recovery-c"):
        payload = stage_payloads[stage_id]
        final_counts.update(
            {
                str(key): int(value)
                for key, value in dict(payload.get("status_counts") or {}).items()
            }
        )
        observation_ref = dict(payload.get("execution_observation") or {})
        observation_path = resolve_repo_path(str(observation_ref.get("path") or ""))
        if observation_path.is_symlink() or not observation_path.is_file():
            raise ContractLifecycleError(
                f"recovery observation is missing for {stage_id}"
            )
        if observation_ref.get("sha256") != sha256_file(observation_path):
            raise ContractLifecycleError(
                f"recovery observation hash is stale for {stage_id}"
            )
        observation = json.loads(observation_path.read_text(encoding="utf-8"))
        entries = list(observation.get("blind_completion_entries") or [])
        if observation.get("blind_completion_entries_sha256") != sha256_object(entries):
            raise ContractLifecycleError(
                f"recovery completion-entry hash is stale for {stage_id}"
            )
        if int(observation.get("blind_completion_entry_count") or 0) != len(entries):
            raise ContractLifecycleError(
                f"recovery completion-entry count is stale for {stage_id}"
            )
        remote_entries.extend(dict(entry) for entry in entries)
    if sum(final_counts.values()) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError(
            "final recovery receipts do not cover exactly 2,847 locked slots"
        )
    identities = [str(entry.get("job_identity_sha256") or "") for entry in remote_entries]
    if len(identities) != len(set(identities)):
        raise ContractLifecycleError("remote completion index contains duplicate identities")
    for entry in remote_entries:
        if set(entry) != {
            "job_identity_sha256",
            "job_binding_sha256",
            "artifact_tree_sha256",
            "artifact_file_count",
            "artifact_total_bytes",
            "completion_marker_semantic_sha256",
        }:
            raise ContractLifecycleError("remote completion index contains non-blind fields")
        for field in (
            "job_identity_sha256",
            "job_binding_sha256",
            "artifact_tree_sha256",
            "completion_marker_semantic_sha256",
        ):
            _require_sha256(str(entry.get(field) or ""), field)
    completed = len(remote_entries)
    unresolved = EXPECTED_RECORD_SLOT_COUNT - completed
    if unresolved < 0:
        raise ContractLifecycleError("formal completion counters exceed the denominator")

    failure_policy = dict(plan.execution.definition["failure_policy"])
    ledger_path = resolve_repo_path(failure_policy["blind_failure_ledger_path"])
    anomaly_counts: Counter[str] = Counter()
    ledger_records = 0
    if ledger_path.exists():
        if ledger_path.is_symlink() or not ledger_path.is_file():
            raise ContractLifecycleError("blind failure ledger is not a regular file")
        for line_number, line in enumerate(
            ledger_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, Mapping):
                raise ContractLifecycleError(
                    f"blind failure ledger line {line_number} is not an object"
                )
            if value.get("blind_health_fields_only") is not True or value.get(
                "contains_case_prompt_trajectory_evaluator_or_label"
            ) is not False:
                raise ContractLifecycleError("blind failure ledger contains unsealed data")
            if value.get("execution_lock_sha256") != plan.execution.lock_sha256:
                raise ContractLifecycleError("blind failure ledger lock binding is stale")
            ledger_records += 1
            anomaly_counts[str(value.get("error_category") or "unknown")] += 1

    anomaly = {
        "schema_version": "agentdojo_formal_execution_anomaly_receipt/v1",
        "created_at": utc_now_iso(),
        "execution_lock_sha256": plan.execution.lock_sha256,
        "execution_policy_sha256": plan.execution.definition[
            "execution_policy_sha256"
        ],
        "plan_index_sha256": plan.plan_index_sha256,
        "blind_failure_ledger": (
            {
                "path": _display(ledger_path),
                "sha256": sha256_file(ledger_path),
                "record_count": ledger_records,
            }
            if ledger_path.exists()
            else None
        ),
        "anomaly_category_counts": dict(sorted(anomaly_counts.items())),
        "anomaly_record_count": ledger_records,
        "blind_only": True,
        "contains_case_prompt_response_trajectory_evaluator_or_label": False,
    }
    anomaly_file = resolve_repo_path(anomaly_path)
    _write_identical_or_new(anomaly_file, anomaly)

    remote_index = {
        "schema_version": "agentdojo_formal_remote_completion_index/v1",
        "created_at": utc_now_iso(),
        "execution_lock_sha256": plan.execution.lock_sha256,
        "execution_policy_sha256": plan.execution.definition[
            "execution_policy_sha256"
        ],
        "plan_index_sha256": plan.plan_index_sha256,
        "entry_count": len(remote_entries),
        "entries_sha256": sha256_object(remote_entries),
        "entries": remote_entries,
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    remote_index_file = resolve_repo_path(remote_completion_index_path)
    _write_identical_or_new(remote_index_file, remote_index)

    completion = {
        "schema_version": "agentdojo_formal_execution_completion_receipt/v1",
        "created_at": utc_now_iso(),
        "status": (
            "ready_for_evidence_acceptance"
            if unresolved == 0
            else "completed_with_unresolved_failures"
        ),
        "execution_lock_path": _display(plan.execution.lock_path),
        "execution_lock_sha256": plan.execution.lock_sha256,
        "execution_policy_sha256": plan.execution.definition[
            "execution_policy_sha256"
        ],
        "plan_index_path": _display(plan.plan_index_path),
        "plan_index_sha256": plan.plan_index_sha256,
        "stage_receipt_count": len(STAGE_ORDER),
        "stage_receipts_sha256": sha256_object(stage_index),
        "stage_receipts": stage_index,
        "record_slot_count": EXPECTED_RECORD_SLOT_COUNT,
        "completed_or_strictly_reused_record_slots": completed,
        "unresolved_failure_count": unresolved,
        "expected_native_trajectory_count": EXPECTED_RECORD_SLOT_COUNT * 3,
        "remote_completion_index_path": _display(remote_index_file),
        "remote_completion_index_sha256": sha256_file(remote_index_file),
        "failure_recovery_rounds": 1,
        "never_rerun_completed": True,
        "namespace_init_receipt_path": _display(Path(namespace.path)),
        "namespace_init_receipt_sha256": str(namespace.sha256),
        "anomaly_receipt_path": _display(anomaly_file),
        "anomaly_receipt_sha256": sha256_file(anomaly_file),
        "blind_only": True,
        "contains_case_prompt_response_trajectory_evaluator_or_label": False,
    }
    completion_file = resolve_repo_path(completion_path)
    _write_identical_or_new(completion_file, completion)
    return (
        {
            **completion,
            "receipt_path": _display(completion_file),
            "receipt_sha256": sha256_file(completion_file),
        },
        {
            **anomaly,
            "receipt_path": _display(anomaly_file),
            "receipt_sha256": sha256_file(anomaly_file),
        },
    )


def run_all_locked_stages(
    plan: LockedEvidencePlan,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    infra_config_path: str | Path,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    receipt_root: str | Path = DEFAULT_STAGE_RECEIPT_ROOT,
    execution_observation_root: str | Path = DEFAULT_STAGE_EXECUTION_ROOT,
    stage_authorization_root: str | Path = DEFAULT_STAGE_AUTHORIZATION_ROOT,
    stage_intent_root: str | Path = DEFAULT_STAGE_INTENT_ROOT,
    machine_health_root: str | Path = DEFAULT_MACHINE_HEALTH_ROOT,
    stage_workload_root: str | Path = DEFAULT_STAGE_WORKLOAD_ROOT,
    namespace_init_receipt_path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
    controller_lifecycle_lock_path: str | Path = DEFAULT_CONTROLLER_LIFECYCLE_LOCK,
    stop_after_stage: str | None = None,
    executor: Executor = execute_planned_jobs,
    remote_command: Callable[..., Any] = run_remote_blind_command,
) -> dict[str, Any]:
    """Crash-resumably execute, monitor, health-seal, and advance every stage."""

    if stop_after_stage is not None and stop_after_stage not in STAGE_ORDER:
        raise ContractLifecycleError("run-all stop stage is invalid")
    sealed: list[dict[str, str]] = []
    with _controller_lifecycle_lock(controller_lifecycle_lock_path):
        for stage_id in STAGE_ORDER:
            stage = select_locked_stage(plan, stage_id)
            receipt_path = resolve_repo_path(receipt_root) / f"{stage_id}.json"
            if receipt_path.exists():
                existing = load_mapping(receipt_path)
                if (
                    existing.get("stage_id") != stage_id
                    or existing.get("execution_lock_sha256")
                    != plan.execution.lock_sha256
                ):
                    raise ContractLifecycleError(
                        f"run-all found a stale stage receipt: {stage_id}"
                    )
                sealed.append(_path_lock(receipt_path))
            else:
                sampler_holder: dict[str, _RemoteFormalResourceSampler] = {}

                def monitored_executor(
                    planned: Sequence[PlannedJob], **kwargs: Any
                ) -> list[ExecutedJob]:
                    authorization_path = resolve_repo_path(
                        kwargs["locked_stage_authorization_path"]
                    )
                    authorization = load_mapping(authorization_path)
                    sampler = _RemoteFormalResourceSampler(
                        plan=plan,
                        stage=stage,
                        authorization=authorization,
                        authorization_sha256=sha256_file(authorization_path),
                        infra_config_path=infra_config_path,
                        remote_command=remote_command,
                    )
                    sampler_holder["sampler"] = sampler
                    sampler.start()
                    try:
                        return executor(planned, **kwargs)
                    finally:
                        sampler.stop()

                observation = run_locked_stage(
                    plan,
                    stage,
                    manifest_path=manifest_path,
                    source_bundle_path=source_bundle_path,
                    infra_config_path=infra_config_path,
                    agents_config_path=agents_config_path,
                    executor=monitored_executor,
                    receipt_root=receipt_root,
                    execution_observation_root=execution_observation_root,
                    namespace_init_receipt_path=namespace_init_receipt_path,
                    stage_authorization_root=stage_authorization_root,
                    stage_intent_root=stage_intent_root,
                    controller_lifecycle_lock_path=controller_lifecycle_lock_path,
                    _controller_lock_held=True,
                )
                authorization_ref = dict(observation["stage_authorization"])
                authorization_path = resolve_repo_path(
                    str(authorization_ref["path"])
                )
                authorization = load_mapping(authorization_path)
                health_path = resolve_repo_path(machine_health_root) / f"{stage_id}.json"
                workload_path = resolve_repo_path(stage_workload_root) / f"{stage_id}.json"
                sampler = sampler_holder.get("sampler")
                _build_or_recover_remote_formal_health(
                    plan=plan,
                    stage=stage,
                    observation=observation,
                    authorization=authorization,
                    authorization_sha256=sha256_file(authorization_path),
                    infra_config_path=infra_config_path,
                    health_output_path=health_path,
                    workload_output_path=workload_path,
                    receipt_root=receipt_root,
                    sampler=sampler,
                    remote_command=remote_command,
                )
                verifier = _remote_formal_health_verifier(
                    infra_config_path=infra_config_path,
                    remote_command=remote_command,
                )
                sealed_receipt = seal_locked_stage(
                    plan,
                    stage,
                    post_stage_health_receipt_path=health_path,
                    health_verifier=verifier,
                    receipt_root=receipt_root,
                    execution_observation_root=execution_observation_root,
                    namespace_init_receipt_path=namespace_init_receipt_path,
                    controller_lifecycle_lock_path=controller_lifecycle_lock_path,
                    _controller_lock_held=True,
                )
                sealed.append(
                    {
                        "path": str(sealed_receipt["receipt_path"]),
                        "sha256": str(sealed_receipt["receipt_sha256"]),
                    }
                )
            if stage_id == stop_after_stage:
                return {
                    "status": "stopped_after_locked_stage",
                    "stopped_after_stage": stage_id,
                    "sealed_stage_count": len(sealed),
                    "sealed_stages": sealed,
                    "execution_lock_sha256": plan.execution.lock_sha256,
                    "blind_only": True,
                }
    return {
        "status": "all_locked_stages_sealed",
        "sealed_stage_count": len(sealed),
        "sealed_stages": sealed,
        "execution_lock_sha256": plan.execution.lock_sha256,
        "ready_for_completion_freeze": len(sealed) == len(STAGE_ORDER),
        "blind_only": True,
    }


class _RemoteFormalResourceSampler:
    """One content-blind remote sampler loop tied to an authorization session."""

    def __init__(
        self,
        *,
        plan: LockedEvidencePlan,
        stage: LockedStage,
        authorization: Mapping[str, Any],
        authorization_sha256: str,
        infra_config_path: str | Path,
        remote_command: Callable[..., Any],
    ) -> None:
        self.plan = plan
        self.stage = stage
        self.authorization = dict(authorization)
        self.authorization_sha256 = authorization_sha256
        self.infra_config_path = infra_config_path
        self.remote_command = remote_command
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.sample_count = 0
        self.failed_sample_count = 0
        self.metadata: dict[str, Any] | None = None

    @property
    def resource_ledger_path(self) -> str:
        sealed = self.plan.execution.definition["sealed_remote_evidence"]
        return (
            f"{str(sealed['blind_aggregate_root']).rstrip('/')}"
            f"/formal-stage-health/{self.stage.stage_id}-"
            f"{self.authorization['session_id']}/resources.jsonl"
        )

    def start(self) -> None:
        self.metadata = _prepare_remote_sampler(
            plan=self.plan,
            stage=self.stage,
            authorization=self.authorization,
            authorization_sha256=self.authorization_sha256,
            infra_config_path=self.infra_config_path,
            resource_ledger_path=self.resource_ledger_path,
            remote_command=self.remote_command,
        )
        self.thread = threading.Thread(
            target=self._loop,
            name=f"agentdojo-health-{self.stage.stage_id}",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=60)
            if self.thread.is_alive():
                raise ContractLifecycleError("formal resource sampler did not stop")

    def _loop(self) -> None:
        assert self.metadata is not None
        target = resolve_infra_target(
            "agentdojo", load_mapping(self.infra_config_path)
        )
        while not self.stop_event.is_set():
            command = _remote_resource_sample_command(
                plan=self.plan,
                stage=self.stage,
                authorization=self.authorization,
                authorization_sha256=self.authorization_sha256,
                metadata=self.metadata,
                resource_ledger_path=self.resource_ledger_path,
            )
            try:
                result = self.remote_command(
                    target,
                    command,
                    timeout_seconds=30,
                    transient_retry_attempts=1,
                    maximum_stdout_bytes=4096,
                    maximum_stderr_bytes=0,
                )
                if result.returncode == 0:
                    self.sample_count += 1
                else:
                    self.failed_sample_count += 1
            except Exception:
                self.failed_sample_count += 1
            self.stop_event.wait(0.25)


def _prepare_remote_sampler(
    *,
    plan: LockedEvidencePlan,
    stage: LockedStage,
    authorization: Mapping[str, Any],
    authorization_sha256: str,
    infra_config_path: str | Path,
    resource_ledger_path: str,
    remote_command: Callable[..., Any],
) -> dict[str, Any]:
    infra = load_mapping(infra_config_path)
    target = resolve_infra_target("agentdojo", infra)
    python_bin = _locked_remote_python(target)
    script = """
import json, os, pathlib
ledger = pathlib.Path(__import__('sys').argv[1])
ledger.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
if not ledger.exists():
    fd = os.open(ledger, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o640); os.close(fd)
boot = pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
ticks = int(float(pathlib.Path('/proc/uptime').read_text().split()[0]) * os.sysconf('SC_CLK_TCK'))
print(json.dumps({'host_boot_id': boot, 'expected_worker_uid': os.geteuid(), 'minimum_worker_starttime_ticks': max(1,ticks)}))
""".strip()
    command = (
        f"{shlex.quote(python_bin)} -c {shlex.quote(script)} "
        f"{shlex.quote(resource_ledger_path)}"
    )
    result = remote_command(
        target,
        command,
        timeout_seconds=30,
        transient_retry_attempts=1,
        maximum_stdout_bytes=2048,
        maximum_stderr_bytes=0,
    )
    if result.returncode != 0 or result.stderr:
        raise ContractLifecycleError("formal resource sampler initialization failed")
    payload = json.loads(result.stdout)
    if set(payload) != {
        "host_boot_id",
        "expected_worker_uid",
        "minimum_worker_starttime_ticks",
    }:
        raise ContractLifecycleError("formal sampler metadata fields differ")
    return payload


def _remote_resource_sample_command(
    *,
    plan: LockedEvidencePlan,
    stage: LockedStage,
    authorization: Mapping[str, Any],
    authorization_sha256: str,
    metadata: Mapping[str, Any],
    resource_ledger_path: str,
) -> str:
    sealed = plan.execution.definition["sealed_remote_evidence"]
    runtime_root = str(sealed["runtime_state_root"])
    policy_ref = dict(plan.execution.definition["runtime_policy"])
    remote_root = str(
        plan.execution.definition["sealed_remote_evidence"][
            "remote_inventory_helper"
        ]["remote_path"]
    ).split("/src/", 1)[0]
    remote_policy = f"{remote_root}/{policy_ref['path']}"
    policy = load_runtime_policy(load_mapping(policy_ref["path"]))
    database = (
        f"{runtime_root.rstrip('/')}/openrouter-formal_execution-"
        f"{policy.semantic_sha256[:16]}.sqlite3"
    )
    binding = resource_worker_process_binding_sha256(
        execution_scope_sha256=plan.execution.lock_sha256,
        stage_id=stage.stage_id,
        session_id=str(authorization["session_id"]),
        stage_binding_sha256=authorization_sha256,
    )
    python_bin = f"{remote_root}/.venv/bin/python"
    return (
        f"cd {shlex.quote(remote_root)} && PYTHONPATH={shlex.quote(remote_root + '/src')} "
        f"{shlex.quote(python_bin)} -m evidence_system.cli.agentdojo_runtime_health "
        f"sample-resource --ledger {shlex.quote(resource_ledger_path)} "
        f"--worker-concurrency {int(authorization['workers'])} --sample-seconds 0.25 "
        f"--policy {shlex.quote(remote_policy)} --runtime-state-dir {shlex.quote(runtime_root)} "
        f"--budget-scope formal_execution --expected-database-path {shlex.quote(database)} "
        f"--session-id {shlex.quote(str(authorization['session_id']))} "
        f"--host-boot-id {shlex.quote(str(metadata['host_boot_id']))} "
        f"--stage-binding-sha256 {shlex.quote(authorization_sha256)} "
        f"--worker-process-binding-sha256 {shlex.quote(binding)} "
        f"--expected-worker-uid {int(metadata['expected_worker_uid'])} "
        f"--minimum-worker-starttime-ticks {int(metadata['minimum_worker_starttime_ticks'])} "
        f"--shared-group {shlex.quote(str(sealed['blind_group']))}"
    )


def _build_or_recover_remote_formal_health(
    *,
    plan: LockedEvidencePlan,
    stage: LockedStage,
    observation: Mapping[str, Any],
    authorization: Mapping[str, Any],
    authorization_sha256: str,
    infra_config_path: str | Path,
    health_output_path: Path,
    workload_output_path: Path,
    receipt_root: str | Path,
    sampler: _RemoteFormalResourceSampler | None,
    remote_command: Callable[..., Any],
) -> dict[str, Any]:
    if health_output_path.exists():
        if health_output_path.is_symlink() or not health_output_path.is_file():
            raise ContractLifecycleError("formal health output is unsafe")
        return load_mapping(health_output_path)
    if sampler is None or sampler.metadata is None:
        # A controller may crash after publishing the observation.  Recreate
        # only the deterministic paths/metadata needed to seal the already
        # completed session; no episode is rerun.
        sampler = _RemoteFormalResourceSampler(
            plan=plan,
            stage=stage,
            authorization=authorization,
            authorization_sha256=authorization_sha256,
            infra_config_path=infra_config_path,
            remote_command=remote_command,
        )
        sampler.metadata = _prepare_remote_sampler(
            plan=plan,
            stage=stage,
            authorization=authorization,
            authorization_sha256=authorization_sha256,
            infra_config_path=infra_config_path,
            resource_ledger_path=sampler.resource_ledger_path,
            remote_command=remote_command,
        )
    models = dict(plan.execution.definition["models"])
    slot_counts = Counter(str(item.job["agent_id"]) for item in stage.planned)
    agent_models: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENTS:
        model = dict(models[agent_id])
        agent_models.append(
            {
                "agent_id": agent_id,
                "model_id": str(model["model"]),
                "model_config_sha256": agentdojo_model_config_sha256(
                    agent_id=agent_id,
                    provider=str(model["provider"]),
                    model_id=str(model["model"]),
                    temperature=float(model["temperature"]),
                    max_tokens=int(model["max_tokens"]),
                    timeout_seconds=int(model["timeout_seconds"]),
                    retry=int(model["retry"]),
                ),
                "record_slot_count": int(slot_counts.get(agent_id, 0)),
            }
        )
    target_agent = (
        next(iter(slot_counts)) if len(slot_counts) == 1 else None
    )
    workload = build_formal_locked_stage_workload(
        execution_lock_sha256=plan.execution.lock_sha256,
        execution_policy_sha256=plan.execution.definition[
            "execution_policy_sha256"
        ],
        plan_index_sha256=plan.plan_index_sha256,
        stage_id=stage.stage_id,
        workers=int(observation["effective_workers"]),
        record_slot_ids_sha256=stage.record_slot_ids_sha256,
        record_slot_count=len(stage.planned),
        agent_models=agent_models,
        target_agent_id=target_agent,
    )
    _write_identical_or_new(workload_output_path, workload)
    target = resolve_infra_target(
        "agentdojo", load_mapping(infra_config_path)
    )
    remote_root = str(target.remote_workdir).rstrip("/")
    sealed = plan.execution.definition["sealed_remote_evidence"]
    control_root = f"{str(sealed['runtime_state_root']).rstrip('/')}/formal-control"
    workload_sha = sha256_file(workload_output_path)
    remote_workload = f"{control_root}/health-workloads/{workload_sha}.json"
    from evidence_system.adapters.agentdojo import (
        _install_remote_formal_control_file,
    )

    _install_remote_formal_control_file(
        target,
        local_source=workload_output_path,
        remote_destination=remote_workload,
        expected_sha256=workload_sha,
        runtime_state_root=str(sealed["runtime_state_root"]),
    )
    remote_health = (
        f"{str(sealed['blind_aggregate_root']).rstrip('/')}"
        f"/formal-stage-health/{stage.stage_id}-{authorization['session_id']}"
        "/receipt.json"
    )
    remote_policy = f"{remote_root}/{plan.execution.definition['runtime_policy']['path']}"
    remote_infra = (
        f"{remote_root}/{plan.execution.definition['runtime_infra_overlay']['path']}"
    )
    prior_safe = _prior_safe_workers(
        plan=plan,
        stage=stage,
        receipt_root=receipt_root,
        effective_workers=int(observation["effective_workers"]),
    )
    build_command = (
        f"cd {shlex.quote(remote_root)} && PYTHONPATH={shlex.quote(remote_root + '/src')} "
        f"{shlex.quote(_locked_remote_python(target))} -m "
        "evidence_system.cli.agentdojo_runtime_health formal-stage-receipt "
        f"--policy {shlex.quote(remote_policy)} --runtime-infra {shlex.quote(remote_infra)} "
        f"--stage-workload {shlex.quote(remote_workload)} "
        f"--blind-health-ledger {shlex.quote(str(sealed['blind_aggregate_root']).rstrip('/') + '/openrouter_health.jsonl')} "
        f"--resource-ledger {shlex.quote(sampler.resource_ledger_path)} "
        f"--session-id {shlex.quote(str(authorization['session_id']))} "
        f"--host-boot-id {shlex.quote(str(sampler.metadata['host_boot_id']))} "
        f"--session-started-at {shlex.quote(str(observation['started_at']))} "
        f"--session-ended-at {shlex.quote(str(observation['ended_at']))} "
        f"--prior-safe-workers {prior_safe} --output {shlex.quote(remote_health)}"
    )
    result = remote_command(
        target,
        build_command,
        timeout_seconds=120,
        transient_retry_attempts=1,
        maximum_stdout_bytes=131_072,
        maximum_stderr_bytes=0,
    )
    if result.returncode == 0:
        payload = json.loads(result.stdout)
    else:
        payload = _read_remote_blind_json(
            target,
            remote_health,
            remote_command=remote_command,
            maximum_bytes=131_072,
        )
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError("formal remote health receipt is not an object")
    _write_identical_or_new(health_output_path, dict(payload))
    return dict(payload)


def _remote_formal_health_verifier(
    *,
    infra_config_path: str | Path,
    remote_command: Callable[..., Any],
) -> HealthVerifier:
    target = resolve_infra_target(
        "agentdojo", load_mapping(infra_config_path)
    )
    remote_root = str(target.remote_workdir).rstrip("/")

    def verify(path: str | Path, **expected: Any) -> Mapping[str, Any]:
        local = load_mapping(path)
        session = dict(local.get("session") or {})
        workload = dict(local.get("stage_workload") or {})
        remote_health = (
            str(dict(local.get("resource_ledger") or {}).get("path") or "")
            .rsplit("/resources.jsonl", 1)[0]
            + "/receipt.json"
        )
        command = (
            f"cd {shlex.quote(remote_root)} && PYTHONPATH={shlex.quote(remote_root + '/src')} "
            f"{shlex.quote(_locked_remote_python(target))} -m "
            "evidence_system.cli.agentdojo_runtime_health verify-formal-stage-receipt "
            f"--receipt {shlex.quote(remote_health)} "
            f"--execution-lock-sha256 {shlex.quote(str(expected['expected_execution_lock_sha256']))} "
            f"--execution-policy-sha256 {shlex.quote(str(expected['expected_execution_policy_sha256']))} "
            f"--plan-index-sha256 {shlex.quote(str(workload['plan_index_sha256']))} "
            f"--stage-id {shlex.quote(str(expected['expected_stage_id']))} "
            f"--workers {int(expected['expected_workers'])} "
            f"--record-slot-count {int(expected['expected_record_slot_count'])} "
            f"--record-slot-ids-sha256 {shlex.quote(str(expected['expected_record_slot_ids_sha256']))} "
            f"--stage-workload-sha256 {shlex.quote(str(local['stage_workload_sha256']))} "
            f"--runtime-infra-sha256 {shlex.quote(str(local['runtime_infra_file_sha256']))} "
            f"--session-id {shlex.quote(str(session['session_id']))}"
        )
        result = remote_command(
            target,
            command,
            timeout_seconds=120,
            transient_retry_attempts=1,
            maximum_stdout_bytes=131_072,
            maximum_stderr_bytes=0,
        )
        if result.returncode != 0 or result.stderr:
            raise ContractLifecycleError("remote formal health verification failed")
        verified = json.loads(result.stdout)
        if verified != local:
            raise ContractLifecycleError("local/remote formal health receipt differs")
        return local

    return verify


def _prior_safe_workers(
    *,
    plan: LockedEvidencePlan,
    stage: LockedStage,
    receipt_root: str | Path,
    effective_workers: int,
) -> int:
    if stage.health_parent_stage_id is None:
        return min(4, effective_workers)
    parent = load_mapping(
        resolve_repo_path(receipt_root) / f"{stage.health_parent_stage_id}.json"
    )
    decision = _stage_health_decision(
        parent,
        parent_stage_id=stage.health_parent_stage_id,
        agent_id=stage.health_parent_agent_id,
    )
    return min(int(decision.get("safe_workers") or 4), effective_workers)


def _read_remote_blind_json(
    target: Any,
    path: str,
    *,
    remote_command: Callable[..., Any],
    maximum_bytes: int,
) -> dict[str, Any]:
    script = """
import json, os, pathlib, stat, sys
p=pathlib.Path(sys.argv[1]); info=os.lstat(p)
if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1: raise SystemExit(61)
value=json.loads(p.read_text()); print(json.dumps(value, sort_keys=True))
""".strip()
    result = remote_command(
        target,
        f"{shlex.quote(_locked_remote_python(target))} -c {shlex.quote(script)} {shlex.quote(path)}",
        timeout_seconds=30,
        transient_retry_attempts=1,
        maximum_stdout_bytes=maximum_bytes,
        maximum_stderr_bytes=0,
    )
    if result.returncode != 0 or result.stderr:
        raise ContractLifecycleError("remote blind JSON recovery failed")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ContractLifecycleError("remote blind JSON is not an object")
    return value


def _locked_remote_python(target: Any) -> str:
    install_dir = str(
        target.benchmark_config.get("install_dir") or target.runner_workdir
    )
    value = f"{install_dir.rstrip('/')}/.venv/bin/python"
    if not value.startswith("/") or "\n" in value:
        raise ContractLifecycleError("formal remote Python is not an absolute locked path")
    return value


def _default_health_verifier(path: str | Path, **expected: Any) -> Mapping[str, Any]:
    from evidence_system.adapters import agentdojo_runtime_control as runtime_control

    verifier = getattr(runtime_control, "load_formal_stage_health_receipt", None)
    if verifier is None:
        raise ContractLifecycleError(
            "machine formal-stage health verifier is unavailable; refusing promotion"
        )
    return dict(verifier(path, **expected))


def _health_parent(stage_id: str) -> tuple[str | None, str | None]:
    if stage_id == "canary":
        return None, None
    kind, agent_suffix, *worker = stage_id.split("-")
    agent_id = {"a": "Agent A", "b": "Agent B", "c": "Agent C"}[
        agent_suffix
    ]
    if kind == "ramp":
        workers = int(worker[0])
        if workers == 8:
            return "canary", agent_id
        if workers == 16:
            return f"ramp-{agent_suffix}-8", agent_id
        if workers == 32:
            return f"ramp-{agent_suffix}-16", agent_id
        raise ContractLifecycleError(f"invalid formal ramp stage: {stage_id}")
    if kind == "remaining":
        return f"ramp-{agent_suffix}-32", agent_id
    if kind == "recovery":
        return f"remaining-{agent_suffix}", agent_id
    raise ContractLifecycleError(f"invalid formal stage health parent: {stage_id}")


def _stage_health_decision(
    receipt: Mapping[str, Any],
    *,
    parent_stage_id: str,
    agent_id: str | None,
) -> dict[str, Any]:
    if receipt.get("stage_id") != parent_stage_id:
        raise ContractLifecycleError("health-parent stage receipt identity is stale")
    if parent_stage_id != "canary":
        return {
            "promotion_authorized": receipt.get("promotion_authorized"),
            "safe_workers": receipt.get("safe_workers"),
        }
    rows = list(receipt.get("model_decisions") or [])
    expected_agents = list(EXPECTED_AGENTS)
    if [row.get("agent_id") for row in rows if isinstance(row, Mapping)] != expected_agents:
        raise ContractLifecycleError(
            "canary health receipt must bind independent Agent A/B/C decisions"
        )
    matches = [dict(row) for row in rows if row.get("agent_id") == agent_id]
    if len(matches) != 1:
        raise ContractLifecycleError(
            f"canary health receipt has no unique decision for {agent_id}"
        )
    return matches[0]


def _locked_target_promotion_decision(
    health: Mapping[str, Any],
    *,
    locked_workers: int,
    effective_workers: int,
) -> tuple[bool, bool, bool]:
    """A fallback run may prove hold safety, never the next locked ramp target."""

    health_reported_promotion = health.get("promotion_authorized") is True
    ran_at_locked_target = int(effective_workers) == int(locked_workers)
    return (
        health_reported_promotion,
        ran_at_locked_target,
        health_reported_promotion and ran_at_locked_target,
    )


def _load_or_publish_stage_intent(
    *,
    path: Path,
    plan: LockedEvidencePlan,
    stage: LockedStage,
    effective_workers: int,
    namespace_path: Path,
    namespace_sha256: str,
    authorization_path: Path,
) -> dict[str, Any]:
    expected_binding = {
        "execution_lock_sha256": plan.execution.lock_sha256,
        "execution_policy_sha256": plan.execution.definition[
            "execution_policy_sha256"
        ],
        "plan_index_sha256": plan.plan_index_sha256,
        "stage_id": stage.stage_id,
        "stage_order_index": STAGE_ORDER.index(stage.stage_id),
        "locked_workers": stage.workers,
        "effective_workers": effective_workers,
        "record_slot_count": len(stage.planned),
        "record_slot_ids_sha256": stage.record_slot_ids_sha256,
        "namespace_init_receipt": {
            "path": _display(namespace_path),
            "sha256": namespace_sha256,
        },
        "authorization_path": _display(authorization_path),
    }
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            raise ContractLifecycleError("formal stage intent is linked or non-regular")
        payload = load_mapping(path)
        projection = {field: payload.get(field) for field in expected_binding}
        if (
            payload.get("schema_version") != "agentdojo_formal_stage_intent/v1"
            or projection != expected_binding
            or not str(payload.get("session_id") or "").startswith("session-")
            or not str(payload.get("created_at") or "")
        ):
            raise ContractLifecycleError("formal stage intent binding is stale")
        return payload
    payload = {
        "schema_version": "agentdojo_formal_stage_intent/v1",
        "created_at": utc_now_iso(),
        "session_id": f"session-{uuid.uuid4().hex}",
        **expected_binding,
        "crash_resume_policy": "same_session_same_authorization_reconcile_only",
        "formal_episode_started_by_intent": False,
    }
    _write_identical_or_new(path, payload)
    return payload


def _load_current_stage_observation(
    path: Path,
    *,
    plan: LockedEvidencePlan,
    stage: LockedStage,
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise ContractLifecycleError("formal stage observation is linked or non-regular")
    payload = load_mapping(path)
    authorization_ref = dict(payload.get("stage_authorization") or {})
    if (
        payload.get("schema_version") != "agentdojo_formal_stage_execution_observation/v1"
        or payload.get("stage_id") != stage.stage_id
        or payload.get("execution_lock_sha256") != plan.execution.lock_sha256
        or payload.get("execution_policy_sha256")
        != plan.execution.definition["execution_policy_sha256"]
        or payload.get("plan_index_sha256") != plan.plan_index_sha256
        or payload.get("record_slot_ids_sha256") != stage.record_slot_ids_sha256
        or payload.get("planned_record_slot_count") != len(stage.planned)
        or authorization_ref.get("session_id") != authorization.get("session_id")
        or authorization_ref.get("sha256")
        != sha256_file(resolve_repo_path(str(authorization_ref.get("path") or "")))
    ):
        raise ContractLifecycleError("formal stage observation binding is stale")
    return payload


@contextmanager
def _controller_lifecycle_lock(path: str | Path):
    lock_path = resolve_repo_path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.is_symlink():
        raise ContractLifecycleError("formal controller lifecycle lock is symlinked")
    descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in {errno.EACCES, errno.EAGAIN}:
                raise ContractLifecycleError(
                    "another formal stage controller already holds the lifecycle lock"
                ) from exc
            raise
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _finalized_stage_worker_ceiling(
    plan: LockedEvidencePlan, stage: LockedStage
) -> tuple[int, int]:
    """Bind a stage to the measured safe ceiling of its active model(s)."""

    policy_ref = dict(plan.execution.definition.get("runtime_policy") or {})
    policy_path = resolve_repo_path(str(policy_ref.get("path") or ""))
    if (
        policy_path.is_symlink()
        or not policy_path.is_file()
        or policy_ref.get("sha256") != sha256_file(policy_path)
    ):
        raise ContractLifecycleError("formal runtime-policy file binding is stale")
    policy = load_runtime_policy(load_mapping(policy_path))
    if (
        policy.lifecycle_status != "finalized"
        or policy.formal_execution_allowed is not True
        or not policy.per_model_safe_limits
    ):
        raise ContractLifecycleError(
            "formal stages require finalized per-model safe concurrency limits"
        )
    models = dict(plan.execution.definition.get("models") or {})
    active_agents = list(
        dict.fromkeys(str(item.job["agent_id"]) for item in stage.planned)
    )
    ceilings: list[int] = []
    for agent_id in active_agents:
        model_id = str(dict(models.get(agent_id) or {}).get("model") or "")
        limits = dict(policy.per_model_safe_limits.get(model_id) or {})
        ceiling = int(limits.get("concurrent_requests") or 0)
        if ceiling < 1:
            raise ContractLifecycleError(
                f"formal policy has no safe concurrency for {agent_id}"
            )
        ceilings.append(ceiling)
    measured_ceiling = min(ceilings)
    ramp = sorted(
        int(value)
        for value in plan.execution.definition["concurrency_policy"][
            "ramp_workers"
        ]
    )
    eligible = [
        value
        for value in ramp
        if value <= min(int(stage.workers), measured_ceiling)
    ]
    if not eligible:
        raise ContractLifecycleError(
            "finalized per-model safe ceiling is below the locked minimum of four"
        )
    return max(eligible), measured_ceiling


def _close_remote_stage_authorization(
    *,
    infra_config_path: str | Path,
    remote_path: str,
    expected_sha256: str,
    runtime_state_root: str,
) -> None:
    """Atomically remove worker admission after every worker future has joined."""

    target = resolve_infra_target("agentdojo", load_mapping(infra_config_path))
    expected_control_prefix = f"{runtime_state_root.rstrip('/')}/formal-control/"
    if not remote_path.startswith(expected_control_prefix):
        raise ContractLifecycleError("remote stage authorization path escapes control root")
    closed_path = (
        f"{runtime_state_root.rstrip('/')}/formal-control/closed/"
        f"{Path(remote_path).name}.closed"
    )
    script = """
import hashlib, os, pathlib, stat, sys
source = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
expected = sys.argv[3]
if not source.exists() and not source.is_symlink():
    if (destination.is_symlink() or not destination.is_file()
            or destination.stat().st_nlink != 1
            or stat.S_IMODE(destination.stat().st_mode) != 0o600
            or hashlib.sha256(destination.read_bytes()).hexdigest() != expected):
        raise SystemExit(51)
    print('AUTHORIZATION_CLOSED')
    raise SystemExit(0)
if source.is_symlink() or not source.is_file() or destination.exists() or destination.is_symlink():
    raise SystemExit(51)
info = os.lstat(source)
if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
        or stat.S_IMODE(info.st_mode) != 0o600
        or hashlib.sha256(source.read_bytes()).hexdigest() != expected):
    raise SystemExit(52)
destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
parent_info = os.lstat(destination.parent)
if (stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode)
        or stat.S_IMODE(parent_info.st_mode) != 0o700):
    raise SystemExit(53)
os.rename(source, destination)
for directory in (source.parent, destination.parent):
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
print('AUTHORIZATION_CLOSED')
""".strip()
    install_dir = str(
        target.benchmark_config.get("install_dir") or target.runner_workdir
    )
    python_bin = f"{install_dir.rstrip('/')}/.venv/bin/python"
    command = (
        f"{shlex.quote(python_bin)} -c {shlex.quote(script)} "
        f"{shlex.quote(remote_path)} {shlex.quote(closed_path)} "
        f"{shlex.quote(expected_sha256)}"
    )
    result = run_remote_blind_command(
        target,
        command,
        transient_retry_attempts=1,
        maximum_stdout_bytes=64,
        maximum_stderr_bytes=0,
    )
    if result.returncode != 0 or result.stdout.strip() != "AUTHORIZATION_CLOSED":
        raise ContractLifecycleError(
            "remote stage authorization could not be atomically closed: "
            f"exit_code={result.returncode}"
        )


def _optional_path_lock(
    receipt_directory: Path, stage_id: str | None
) -> dict[str, str] | None:
    if stage_id is None:
        return None
    path = receipt_directory / f"{stage_id}.json"
    if path.is_symlink() or not path.is_file():
        raise ContractLifecycleError(f"formal stage receipt is missing: {stage_id}")
    return {"path": _display(path), "sha256": sha256_file(path)}


def _path_lock(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise ContractLifecycleError("immutable provenance file is missing or linked")
    return {"path": _display(path), "sha256": sha256_file(path)}


def _publish_stage_authorization(
    *,
    path: Path,
    plan: LockedEvidencePlan,
    stage: LockedStage,
    effective_workers: int,
    namespace_path: Path,
    namespace_sha256: str,
    sequence_predecessor_receipt: Mapping[str, str] | None,
    health_parent_receipt: Mapping[str, str] | None,
    health_decision: Mapping[str, Any] | None,
    session_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Publish the exact flat authorization envelope consumed by VPS workers."""

    del sequence_predecessor_receipt, health_decision
    bindings = [formal_job_binding_sha256(item.job) for item in stage.planned]
    job_file_hashes = [sha256_file(item.job_path) for item in stage.planned]
    if any(
        digest != formal_job_file_sha256(item.job)
        for digest, item in zip(job_file_hashes, stage.planned, strict=True)
    ):
        raise ContractLifecycleError(
            "formal stage job bytes differ from their immutable payloads"
        )
    slot_ids = [str(item.job["record_slot_id"]) for item in stage.planned]
    if not bindings or len(set(bindings)) != len(bindings):
        raise ContractLifecycleError(
            "formal stage authorization requires a non-empty unique job set"
        )
    timeout_values = {
        int(item.job["formal_wall_clock_timeout_seconds"])
        for item in stage.planned
    }
    if len(timeout_values) != 1:
        raise ContractLifecycleError(
            "formal stage jobs must share one locked wall-clock timeout"
        )
    timeout_seconds = next(iter(timeout_values))
    runtime_snapshot = execution_runtime_snapshot()
    if runtime_snapshot != plan.execution.definition["execution_runtime_snapshot"]:
        raise ContractLifecycleError(
            "formal stage authorization runtime snapshot differs from execution lock"
        )

    models = dict(plan.execution.definition["models"])
    stage_agents = list(dict.fromkeys(str(item.job["agent_id"]) for item in stage.planned))
    allowed_models: list[str] = []
    for agent_id in stage_agents:
        model = dict(models.get(agent_id) or {})
        try:
            allowed_models.append(
                agentdojo_model_config_sha256(
                    agent_id=agent_id,
                    provider=str(model["provider"]),
                    model_id=str(model["model"]),
                    temperature=float(model["temperature"]),
                    max_tokens=int(model["max_tokens"]),
                    timeout_seconds=int(model["timeout_seconds"]),
                    retry=int(model["retry"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractLifecycleError(
                f"formal stage model snapshot is incomplete for {agent_id}"
            ) from exc

    sealed = dict(plan.execution.definition["sealed_remote_evidence"])
    runtime_state_root = str(sealed["runtime_state_root"])
    if not runtime_state_root.startswith("/"):
        raise ContractLifecycleError(
            "formal stage authorization requires an absolute runtime-state root"
        )
    control_root = f"{runtime_state_root.rstrip('/')}/formal-control"
    namespace_remote_path = (
        f"{control_root}/namespace-init/{namespace_sha256}.json"
    )
    previous_health_remote = None
    if health_parent_receipt is not None:
        previous_health_remote = {
            "path": (
                f"{control_root}/health/"
                f"{str(health_parent_receipt['sha256'])}.json"
            ),
            "sha256": str(health_parent_receipt["sha256"]),
        }

    session_id = session_id or f"session-{uuid.uuid4().hex}"
    failure_policy = dict(plan.execution.definition["failure_policy"])
    rate_policy = dict(plan.execution.definition["rate_limit_policy"])
    payload = {
        "schema_version": "agentdojo_formal_stage_authorization/v1",
        "status": "authorized",
        "created_at": created_at or utc_now_iso(),
        "execution_lock_sha256": plan.execution.lock_sha256,
        "execution_policy_sha256": plan.execution.definition[
            "execution_policy_sha256"
        ],
        "plan_index_sha256": plan.plan_index_sha256,
        "namespace_init_receipt": {
            "path": namespace_remote_path,
            "sha256": namespace_sha256,
        },
        "stage_id": stage.stage_id,
        "session_id": session_id,
        "stage_order_index": STAGE_ORDER.index(stage.stage_id),
        "locked_workers": int(stage.workers),
        "workers": int(effective_workers),
        "record_slot_count": len(stage.planned),
        "record_slot_ids_sha256": sha256_object(slot_ids),
        "allowed_job_binding_sha256": bindings,
        "allowed_job_bindings_sha256": sha256_object(bindings),
        "allowed_job_file_sha256": job_file_hashes,
        "allowed_job_files_sha256": sha256_object(job_file_hashes),
        "allowed_model_config_sha256": allowed_models,
        "allowed_model_configs_sha256": sha256_object(allowed_models),
        "runtime_policy_semantic_sha256": str(
            rate_policy["runtime_policy_semantic_sha256"]
        ),
        "runtime_policy_file_sha256": str(
            dict(plan.execution.definition["runtime_policy"])["sha256"]
        ),
        "runtime_infra_file_sha256": str(
            dict(plan.execution.definition["runtime_infra_overlay"])["sha256"]
        ),
        "runtime_state_root": runtime_state_root,
        "runtime_snapshot": runtime_snapshot,
        "previous_health_receipt": previous_health_remote,
        "formal_wall_clock_timeout_seconds": timeout_seconds,
        "kill_grace_seconds": int(
            failure_policy["worker_kill_grace_seconds"]
        ),
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    _write_identical_or_new(path, payload)
    if sha256_file(path) == "":
        raise AssertionError("unreachable empty authorization digest")
    # Local sources are deliberately returned out-of-envelope; the remote
    # authorization stays content-blind and contains only canonical VPS paths.
    payload["_controller_context"] = {
        "authorization_remote_path": (
            f"{control_root}/stage-authorizations/"
            f"{stage.stage_id}-{session_id}.json"
        ),
        "namespace_init_local_path": str(namespace_path.resolve()),
        "plan_index_local_path": str(plan.plan_index_path.resolve()),
        "previous_health_local_path": (
            None
            if health_parent_receipt is None
            else str(resolve_repo_path(str(health_parent_receipt["path"])).resolve())
        ),
    }
    return payload


def _select_exact_slots(
    plan: LockedEvidencePlan, record_slot_ids: Sequence[str]
) -> list[PlannedJob]:
    if len(set(record_slot_ids)) != len(record_slot_ids):
        raise ContractLifecycleError("locked stage contains duplicate record slots")
    missing = [slot for slot in record_slot_ids if slot not in plan.by_slot]
    if missing:
        raise ContractLifecycleError(f"locked stage refers to unknown slots: {missing[:5]}")
    return [plan.by_slot[slot] for slot in record_slot_ids]


def _require_sha256(value: str, field: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ContractLifecycleError(f"{field} is not a lowercase SHA-256 digest")
    return value


def _write_identical_or_new(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ContractLifecycleError(f"refusing symlinked provenance path: {path}")
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != dict(payload):
            raise ContractLifecycleError(f"immutable provenance receipt differs: {path}")
        return
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(resolve_repo_path(".").resolve()).as_posix()
    except ValueError:
        return str(resolved)
