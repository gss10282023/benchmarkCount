"""Locked 24-slot pilot planner and three-VPS executor."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from importlib import import_module
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from typing import Any

from evidence_system.adapters.runtime import build_smoke_execution_context
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object
from evidence_system.orchestrator.webarena_verified_full import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_JOBS_ROOT,
    DEFAULT_MANIFEST,
    DEFAULT_REMOTE_WORKDIR,
    DEFAULT_SITE_LOCK,
    DEFAULT_SOURCE_BUNDLE,
    EXPECTED_AGENT_IDS,
    EXPECTED_ROUTES,
    EXPECTED_SOURCE_BUNDLE_SHA256,
    EXPECTED_SOURCE_SHA256,
    FullSchedulePlan,
    SCHEDULE_INDEX_SCHEMA_VERSION,
    WebArenaFullScheduleError,
)
from evidence_system.orchestrator.webarena_verified_full_execution import (
    FullExecutedJob,
    _execution_targets,
    _validate_executable_plan,
)
from evidence_system.orchestrator.webarena_verified_pilot import (
    DEFAULT_PILOT_MANIFEST,
    PILOT_AGENT_ORDERS,
    PILOT_TASK_IDS,
    validate_pilot_manifest,
)
from evidence_system.webarena_sites import load_site_lock


PILOT_RESULT_NAMESPACE = "webarena_verified_v1_2_3_pilot_8x3"
PILOT_ATTEMPT_ORDINAL = 9
PILOT_ATTEMPT_POLICY = {
    "attempt_ordinal": PILOT_ATTEMPT_ORDINAL,
    "prior_attempt_ordinal": 8,
    "prior_attempt_archive": (
        "results/namespaces/"
        "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_008_20260717T0231Z"
    ),
    "failed_attempt_archives": [
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_001_20260716T1520Z"
        ),
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_002_20260716T1531Z"
        ),
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_003_20260716T1559Z"
        ),
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_004_20260716T1617Z"
        ),
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_005_20260716T1634Z"
        ),
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_006_20260716T1853Z"
        ),
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_007_20260717T0144Z"
        ),
        (
            "results/namespaces/"
            "webarena_verified_v1_2_3_pilot_8x3_failed_attempt_008_20260717T0231Z"
        ),
    ],
    "retry_basis": "owner_thread_page_quiesce_then_context_har_flush_with_process_boundary_timeout",
    "prior_paid_model_call_count": 663,
    "runtime_timeout_gate": {
        "status": "pass",
        "browser_teardown_mode": (
            "same_thread_page_quiesce_context_har_flush_then_env_close"
        ),
        "remote_slot_hard_timeout_seconds": 2700,
        "controller_timeout_grace_seconds": 120,
        "same_thread_teardown_unit_test": "pass",
        "external_process_timeout_command_unit_test": "pass",
        "multi_page_har_flush_stress_canary": "pass",
    },
    "failed_pre_attempt_diagnostics": [
        {
            "namespace": "webarena_verified_v1_2_3_native_env_close_task97_canary",
            "status": "failed_archived_in_place",
            "failure_class": "native_env_close_did_not_flush_record_har_path",
            "paid_model_call_count": 68,
            "result_splicing_allowed": False,
        }
    ],
    "pre_attempt_regression_gates": [
        {
            "namespace": "webarena_verified_v1_2_3_sanitizer_v4_task21_gate",
            "task_id": 21,
            "agent_id": "Agent A",
            "status": "pass",
            "worker_status": "completed",
            "official_score": 0.0,
            "paid_model_call_count": 2,
        },
        {
            "namespace": "webarena_verified_v1_2_3_sanitizer_v5_task389_gate",
            "task_id": 389,
            "agent_id": "Agent A",
            "status": "pass",
            "worker_status": "completed",
            "official_score": 0.0,
            "paid_model_call_count": 18,
            "sanitizer_algorithm_version": (
                "webarena_verified_har_trace_credential_value_redaction_v5"
            ),
            "auto_login_attempts": 2,
        },
        {
            "namespace": "webarena_verified_v1_2_3_teardown_task0_canary",
            "task_id": 0,
            "agent_ids": list(EXPECTED_AGENT_IDS),
            "status": "pass",
            "worker_status": "completed",
            "required_artifact_audit_pass_count": 3,
            "paid_model_call_count": 24,
            "browser_teardown_mode": "same_thread_as_sync_playwright_owner",
            "acceptance_path": (
                "experiments/step20/webarena_verified/"
                "teardown_task0_canary_acceptance.json"
            ),
            "acceptance_sha256": (
                "0716b287ed5aabf185333f1d7ad308df8c65525307cd6da94bdac1521cf197db"
            ),
        },
        {
            "namespace": (
                "webarena_verified_v1_2_3_page_quiesce_task97_agentb_canary"
            ),
            "task_id": 97,
            "agent_ids": ["Agent B"],
            "status": "pass",
            "worker_status": "completed",
            "required_artifact_audit_pass_count": 1,
            "paid_model_call_count": 7,
            "browser_teardown_mode": (
                "same_thread_page_quiesce_context_har_flush_then_env_close"
            ),
            "acceptance_path": (
                "experiments/step20/webarena_verified/"
                "page_quiesce_task97_agentb_canary_acceptance.json"
            ),
            "acceptance_sha256": (
                "70a583c6ea87e4fb59c7a7f27994a7bb42d96b6edc1970427fe209835e1b5dee"
            ),
        },
    ],
    "all_24_slots_use_fresh_attempt": True,
    "result_splicing_allowed": False,
}
PILOT_SCHEDULE_INDEX_SCHEMA_VERSION = "webarena_verified_pilot_schedule_index/v1"
EXPECTED_PILOT_JOBS_SHA256 = (
    "010c67c5fbf9762c0f937385b0bbadb2c28ee0eb5d7cebb6e629b667bd80a29a"
)
EXPECTED_FULL_SOURCE_JOBS_SHA256 = (
    "5c613b729e96ac020b9e2a8d5cdba667371f086be7c5cad4e46292d9a349e704"
)
EXPECTED_FULL_SOURCE_INDEX_SHA256 = (
    "867f23bdbcb44c9c52fea31fd49d8312f0053ad244a5799dab2d64b6da5969ac"
)
EXPECTED_PILOT_MANIFEST_SHA256 = (
    "1db95635ee81fcc31e6a121c089f41db982a5482997849506fe377490d22c7e7"
)
DEFAULT_FULL_JOBS_INDEX = DEFAULT_JOBS_ROOT / "index.json"
DEFAULT_PILOT_JOBS_ROOT = Path("experiments/step20/webarena_verified/jobs/pilot")
DEFAULT_PILOT_SCHEDULE_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/pilot_schedule_acceptance.json"
)


@dataclass(frozen=True)
class PilotSchedulePlan:
    jobs: tuple[dict[str, Any], ...]
    acceptance: dict[str, Any]


def materialize_canonical_pilot_schedule(
    plan: PilotSchedulePlan,
    *,
    full_jobs_index_path: str | Path = DEFAULT_FULL_JOBS_INDEX,
    output_root: str | Path = DEFAULT_PILOT_JOBS_ROOT,
    acceptance_path: str | Path = DEFAULT_PILOT_SCHEDULE_ACCEPTANCE,
    replace: bool = False,
) -> dict[str, Any]:
    """Atomically freeze the sole authoritative 24-slot pilot schedule.

    Existing materialization is never silently repaired.  Callers must pass
    ``replace=True`` explicitly, and the paid runner only validates this
    canonical schedule; it does not rewrite it.
    """

    _validate_pilot_schedule(plan)
    source = _validate_full_source_index(full_jobs_index_path)
    _validate_plan_source_binding(plan, source)
    pilot_manifest = _regular_file(DEFAULT_PILOT_MANIFEST, "pilot manifest")
    _validate_sha_sidecar(pilot_manifest, "pilot manifest")
    if sha256_file(pilot_manifest) != EXPECTED_PILOT_MANIFEST_SHA256:
        raise WebArenaFullScheduleError("pilot manifest hash changed")
    jobs_sha256 = sha256_object(plan.jobs)
    if jobs_sha256 != EXPECTED_PILOT_JOBS_SHA256:
        raise WebArenaFullScheduleError("pilot aggregate jobs hash changed")

    output = resolve_repo_path(output_root)
    acceptance_file = resolve_repo_path(acceptance_path)
    if output.exists() and not replace:
        return validate_canonical_pilot_schedule(
            plan,
            full_jobs_index_path=full_jobs_index_path,
            jobs_index_path=output / "index.json",
            acceptance_path=acceptance_file,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=str(output.parent))
    )
    try:
        entries: list[dict[str, Any]] = []
        for position, job in enumerate(plan.jobs):
            job_path = temporary / f"{position:04d}-{job['record_slot_id']}.json"
            _write_json(job_path, job)
            entries.append(
                {
                    "position": position,
                    "record_slot_id": job["record_slot_id"],
                    "job_id": job["job_id"],
                    "task_id": int(job["task_id"]),
                    "agent_id": job["agent_id"],
                    "path": job_path.name,
                    "sha256": sha256_file(job_path),
                    "job_object_sha256": sha256_object(job),
                }
            )
        index = {
            "schema_version": PILOT_SCHEDULE_INDEX_SCHEMA_VERSION,
            "result_namespace": PILOT_RESULT_NAMESPACE,
            "attempt_policy": dict(PILOT_ATTEMPT_POLICY),
            "job_count": 24,
            "jobs_sha256": jobs_sha256,
            "source_full_schedule": source,
            "pilot_manifest": {
                "path": _display_path(pilot_manifest),
                "sha256": sha256_file(pilot_manifest),
            },
            "entries": entries,
        }
        index_path = temporary / "index.json"
        _write_json(index_path, index)
        _write_sha_sidecar(index_path)
        if output.exists():
            shutil.rmtree(output)
        os.replace(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    canonical_index = output / "index.json"
    acceptance = dict(plan.acceptance)
    acceptance.update(
        {
            "schema_version": "webarena_verified_pilot_schedule_acceptance/v1",
            "status": "pass",
            "pilot_launch_eligible": True,
            "formal_launch_eligible": False,
            "result_namespace": PILOT_RESULT_NAMESPACE,
            "pilot_jobs_sha256": jobs_sha256,
            "source_full_jobs_sha256": source["jobs_sha256"],
            "source_full_schedule": source,
            "canonical_schedule": {
                "index_path": _display_path(canonical_index),
                "index_sha256": sha256_file(canonical_index),
                "job_count": 24,
                "jobs_sha256": jobs_sha256,
            },
        }
    )
    _write_json(acceptance_file, acceptance)
    _write_sha_sidecar(acceptance_file)
    return validate_canonical_pilot_schedule(
        plan,
        full_jobs_index_path=full_jobs_index_path,
        jobs_index_path=canonical_index,
        acceptance_path=acceptance_file,
    )


def validate_canonical_pilot_schedule(
    plan: PilotSchedulePlan,
    *,
    full_jobs_index_path: str | Path = DEFAULT_FULL_JOBS_INDEX,
    jobs_index_path: str | Path = DEFAULT_PILOT_JOBS_ROOT / "index.json",
    acceptance_path: str | Path = DEFAULT_PILOT_SCHEDULE_ACCEPTANCE,
) -> dict[str, Any]:
    """Fail closed unless disk contains the exact freshly-derived 24 jobs."""

    _validate_pilot_schedule(plan)
    source = _validate_full_source_index(full_jobs_index_path)
    _validate_plan_source_binding(plan, source)
    expected_jobs = [dict(job) for job in plan.jobs]
    if sha256_object(expected_jobs) != EXPECTED_PILOT_JOBS_SHA256:
        raise WebArenaFullScheduleError("derived pilot jobs hash changed")

    index_file = _regular_file(jobs_index_path, "canonical pilot jobs index")
    acceptance_file = _regular_file(acceptance_path, "pilot schedule acceptance")
    _validate_sha_sidecar(index_file, "canonical pilot jobs index")
    _validate_sha_sidecar(acceptance_file, "pilot schedule acceptance")
    index = _load_mapping(index_file, "canonical pilot jobs index")
    acceptance = _load_mapping(acceptance_file, "pilot schedule acceptance")
    if (
        index.get("schema_version") != PILOT_SCHEDULE_INDEX_SCHEMA_VERSION
        or index.get("result_namespace") != PILOT_RESULT_NAMESPACE
        or index.get("attempt_policy") != PILOT_ATTEMPT_POLICY
        or index.get("job_count") != 24
        or index.get("jobs_sha256") != EXPECTED_PILOT_JOBS_SHA256
        or index.get("source_full_schedule") != source
    ):
        raise WebArenaFullScheduleError("canonical pilot jobs index identity changed")
    manifest = dict(index.get("pilot_manifest") or {})
    pilot_manifest = _regular_file(DEFAULT_PILOT_MANIFEST, "pilot manifest")
    _validate_sha_sidecar(pilot_manifest, "pilot manifest")
    if manifest != {
        "path": _display_path(pilot_manifest),
        "sha256": EXPECTED_PILOT_MANIFEST_SHA256,
    } or sha256_file(pilot_manifest) != EXPECTED_PILOT_MANIFEST_SHA256:
        raise WebArenaFullScheduleError("canonical pilot manifest binding changed")

    entries = index.get("entries")
    if not isinstance(entries, list) or len(entries) != 24:
        raise WebArenaFullScheduleError("canonical pilot index must contain 24 entries")
    observed_jobs: list[dict[str, Any]] = []
    for position, (entry, expected) in enumerate(zip(entries, expected_jobs, strict=True)):
        if not isinstance(entry, Mapping) or entry.get("position") != position:
            raise WebArenaFullScheduleError(
                f"canonical pilot index position changed at {position}"
            )
        relative = entry.get("path")
        if not isinstance(relative, str) or Path(relative).name != relative:
            raise WebArenaFullScheduleError(
                f"canonical pilot job path is unsafe at {position}"
            )
        job_file = _regular_file(index_file.parent / relative, f"pilot job {position}")
        observed = _load_mapping(job_file, f"pilot job {position}")
        expected_entry = {
            "position": position,
            "record_slot_id": expected["record_slot_id"],
            "job_id": expected["job_id"],
            "task_id": int(expected["task_id"]),
            "agent_id": expected["agent_id"],
            "path": relative,
            "sha256": sha256_file(job_file),
            "job_object_sha256": sha256_object(expected),
        }
        if dict(entry) != expected_entry or observed != expected:
            raise WebArenaFullScheduleError(
                f"canonical pilot job/index mismatch at {position}"
            )
        observed_jobs.append(observed)
    if sha256_object(observed_jobs) != EXPECTED_PILOT_JOBS_SHA256:
        raise WebArenaFullScheduleError("canonical pilot aggregate jobs hash changed")

    canonical = dict(acceptance.get("canonical_schedule") or {})
    if (
        acceptance.get("schema_version")
        != "webarena_verified_pilot_schedule_acceptance/v1"
        or acceptance.get("status") != "pass"
        or acceptance.get("pilot_launch_eligible") is not True
        or acceptance.get("formal_launch_eligible") is not False
        or acceptance.get("result_namespace") != PILOT_RESULT_NAMESPACE
        or acceptance.get("attempt_policy") != PILOT_ATTEMPT_POLICY
        or acceptance.get("pilot_jobs_sha256") != EXPECTED_PILOT_JOBS_SHA256
        or acceptance.get("source_full_jobs_sha256")
        != EXPECTED_FULL_SOURCE_JOBS_SHA256
        or acceptance.get("source_full_schedule") != source
        or canonical
        != {
            "index_path": _display_path(index_file),
            "index_sha256": sha256_file(index_file),
            "job_count": 24,
            "jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        }
    ):
        raise WebArenaFullScheduleError("pilot schedule acceptance binding changed")
    return {
        "status": "pass",
        "job_count": 24,
        "jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        "index_path": _display_path(index_file),
        "index_sha256": sha256_file(index_file),
        "acceptance_path": _display_path(acceptance_file),
        "acceptance_sha256": sha256_file(acceptance_file),
        "source_full_jobs_sha256": EXPECTED_FULL_SOURCE_JOBS_SHA256,
    }


def build_pilot_schedule(
    full_plan: FullSchedulePlan,
    *,
    pilot_manifest_path: str | Path = DEFAULT_PILOT_MANIFEST,
) -> PilotSchedulePlan:
    if full_plan.acceptance.get("status") != "pass" or full_plan.acceptance.get(
        "formal_launch_eligible"
    ) is not True:
        raise WebArenaFullScheduleError(
            "pilot execution requires the same 812 formally locked contracts as the full run"
        )
    _validate_executable_plan(full_plan)
    pilot_file = resolve_repo_path(pilot_manifest_path)
    pilot = load_json_or_yaml(pilot_file)
    if not isinstance(pilot, Mapping):
        raise WebArenaFullScheduleError("pilot manifest is not a JSON object")
    validate_pilot_manifest(pilot)
    pilot_cases = {
        int(case["task_id"]): dict(case)
        for case in list(pilot.get("cases") or [])
        if isinstance(case, Mapping)
    }
    by_task_agent = {
        (int(job["task_id"]), str(job["agent_id"])): job for job in full_plan.jobs
    }
    jobs: list[dict[str, Any]] = []
    selection_ids = [str(task_id) for task_id in PILOT_TASK_IDS]
    deterministic_selection = {
        "hash_function": "sha256",
        "hash_salt_hash": sha256_object("webarena-verified-v1.2.3-pilot-8x3"),
        "eligible_case_unit_set_hash": sha256_object(sorted(selection_ids, key=int)),
        "excluded_smoke_case_units": [],
        "smoke_exclusion_hash": sha256_object([]),
        "case_selection_order_hash": sha256_object(selection_ids),
        "bootstrap_seed": 123000,
        "bootstrap_resample_count": 1000,
        "audit_sample_seed": 123456,
        "rerun_subset_selection_rule": "no outcome-based pilot rerun",
    }
    for task_id, agent_order in zip(PILOT_TASK_IDS, PILOT_AGENT_ORDERS, strict=True):
        for within_task_order, agent_id in enumerate(agent_order, start=1):
            source = by_task_agent.get((task_id, agent_id))
            if source is None:
                raise WebArenaFullScheduleError(
                    f"full schedule has no locked pilot source job for task {task_id}/{agent_id}"
                )
            if int(source.get("task_revision", -1)) != int(
                pilot_cases[task_id]["revision"]
            ) or list(source.get("task_sites") or []) != list(
                pilot_cases[task_id]["sites"]
            ):
                raise WebArenaFullScheduleError(
                    f"full schedule pilot source binding changed for task {task_id}"
                )
            suffix = agent_id[-1].lower()
            slot_id = f"wv123-pilot-task-{task_id:03d}-agent-{suffix}"
            job = dict(source)
            # The completed 24-slot pilot keeps its original local-evidence
            # contract.  VPS-only retention is a formal/full launch policy and
            # must not retroactively change the canonical pilot job hashes.
            job.pop("artifact_retention_mode", None)
            job.update(
                {
                    "job_id": f"pilot-webarena_verified-{task_id:03d}-agent_{suffix}",
                    "record_slot_id": slot_id,
                    "run_id": f"run-{slot_id}",
                    "attempt_id": (
                        f"attempt-{slot_id}-{PILOT_ATTEMPT_ORDINAL:03d}"
                    ),
                    "phase": "preflight",
                    "experiment_type": "diagnostic",
                    "result_namespace": PILOT_RESULT_NAMESPACE,
                    "pilot_within_task_order": within_task_order,
                    "deterministic_selection": deterministic_selection,
                }
            )
            report = validate_object("job", job, formal=False, raise_on_error=False)
            if not report.ok:
                raise WebArenaFullScheduleError(
                    f"pilot job {slot_id} is invalid: {report.to_dict()}"
                )
            jobs.append(job)
    acceptance = {
        "schema_version": "webarena_verified_pilot_schedule_acceptance/v1",
        "status": "pass",
        "pilot_launch_eligible": True,
        "formal_launch_eligible": False,
        "pilot_manifest_path": str(pilot_manifest_path),
        "pilot_manifest_sha256": sha256_file(pilot_file),
        "full_schedule_jobs_sha256": sha256_object(list(full_plan.jobs)),
        "inputs": dict(full_plan.acceptance.get("inputs") or {}),
        "attempt_policy": dict(PILOT_ATTEMPT_POLICY),
        "counts": {
            "cases": 8,
            "record_slots": 24,
            "per_agent": {agent: 8 for agent in EXPECTED_AGENT_IDS},
            "fallback_contracts": 0,
        },
        "gates": {
            "formally_locked_contract_subset_exact": True,
            "counterbalanced_order_exact": True,
            "paired_seed_exact": True,
            "three_server_route_exact": True,
            "per_slot_reset_required": True,
            "fallback_contracts_zero": True,
            "fresh_attempt_without_result_splicing": True,
        },
    }
    return PilotSchedulePlan(jobs=tuple(jobs), acceptance=acceptance)


def execute_pilot_schedule(
    plan: PilotSchedulePlan,
    *,
    ssh_key_path: str | Path,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    dotenv_path: str | Path = ".env",
    site_lock_path: str | Path = DEFAULT_SITE_LOCK,
    adapter_planner: Callable[..., dict[str, Any]] | None = None,
    adapter_executor: Callable[..., dict[str, Any]] | None = None,
) -> list[FullExecutedJob]:
    _validate_pilot_schedule(plan)
    key = resolve_repo_path(ssh_key_path)
    if not key.is_file():
        raise WebArenaFullScheduleError(f"pilot SSH private key is missing: {key}")
    manifest_file = resolve_repo_path(manifest_path)
    source_file = resolve_repo_path(source_bundle_path)
    agents_file = resolve_repo_path(agents_config_path)
    dotenv_file = resolve_repo_path(dotenv_path)
    site_file = resolve_repo_path(site_lock_path)
    if site_file.resolve() != resolve_repo_path(DEFAULT_SITE_LOCK).resolve():
        raise WebArenaFullScheduleError("pilot site lock path differs from frozen schedule")
    if sha256_file(source_file) != EXPECTED_SOURCE_BUNDLE_SHA256:
        raise WebArenaFullScheduleError("pilot source bundle hash changed")
    manifest = load_json_or_yaml(manifest_file)
    source_bundle = load_json_or_yaml(source_file)
    if not isinstance(manifest, Mapping) or not isinstance(source_bundle, Mapping):
        raise WebArenaFullScheduleError("pilot manifest/source bundle is invalid")
    site_lock = load_site_lock(site_file)
    native_index_sha256 = str(
        dict(plan.acceptance.get("inputs") or {}).get("native_claim_index_sha256") or ""
    )
    targets = _execution_targets(
        plan.jobs,
        ssh_key_path=key,
        site_lock=site_lock,
        site_lock_path=site_file,
        remote_workdir=DEFAULT_REMOTE_WORKDIR,
        common_run_policy=dict(manifest["common_run_policy"]),
        source_bundle_sha256=sha256_file(source_file),
        native_claim_index_sha256=native_index_sha256,
        site_lock_sha256=sha256_file(site_file),
    )
    context = build_smoke_execution_context(
        manifest_path=manifest_file,
        manifest_hash=sha256_file(manifest_file),
        source_bundle_path=source_file,
        source_bundle_hash=sha256_file(source_file),
        official_split_hash=EXPECTED_SOURCE_SHA256,
        agents_config_path=agents_file,
        dotenv_path=dotenv_file,
    )
    adapter = import_module("evidence_system.adapters.webarena_verified")
    planner = adapter_planner or getattr(adapter, "plan_smoke_execution")
    executor = adapter_executor or getattr(adapter, "execute_smoke_job")
    lanes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in plan.jobs:
        lanes[str(raw["agent_id"])].append(dict(raw))
    stop = threading.Event()
    lock = threading.Lock()
    by_slot: dict[str, FullExecutedJob] = {}

    def run_lane(agent_id: str) -> None:
        # Imported lazily because run-control also imports this planner module.
        # A paid pilot resume may reuse only a fully audited canonical slot;
        # partial or invalid evidence fails closed instead of paying twice.
        from evidence_system.orchestrator.webarena_verified_run_control import (
            audit_slot,
        )

        target = targets[agent_id]
        for job in lanes[agent_id]:
            if stop.is_set():
                return
            existing = audit_slot(job, site_lock=site_lock)
            if existing.reusable:
                result = {
                    "status": "completed",
                    "skipped_existing": True,
                    "record_slot_id": str(job["record_slot_id"]),
                }
                with lock:
                    by_slot[str(job["record_slot_id"])] = FullExecutedJob(
                        job, result
                    )
                continue
            if existing.state != "pending":
                stop.set()
                raise WebArenaFullScheduleError(
                    "pilot resume found non-canonical existing evidence for "
                    f"{job['record_slot_id']}: {existing.state}"
                )
            execution_plan = planner(
                job,
                target=target,
                agents_config_path=str(agents_file),
                dotenv_path=str(dotenv_file),
                source_bundle_path=str(source_file),
                source_bundle=dict(source_bundle),
            )
            if execution_plan.get("status") != "runnable":
                stop.set()
                raise WebArenaFullScheduleError(
                    f"pilot slot {job['record_slot_id']} is not runnable"
                )
            result = dict(
                executor(
                    job,
                    target=target,
                    execution_plan=execution_plan,
                    context=context,
                )
            )
            if result.get("status") != "completed":
                stop.set()
                raise WebArenaFullScheduleError(
                    f"pilot slot {job['record_slot_id']} did not complete"
                )
            with lock:
                by_slot[str(job["record_slot_id"])] = FullExecutedJob(job, result)

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="webarena-pilot") as pool:
        futures = [pool.submit(run_lane, agent) for agent in EXPECTED_AGENT_IDS]
        try:
            for future in as_completed(futures):
                future.result()
        except Exception:
            stop.set()
            for future in futures:
                future.cancel()
            raise
    ordered = [by_slot[str(job["record_slot_id"])] for job in plan.jobs]
    if len(ordered) != 24:
        raise WebArenaFullScheduleError("pilot execution did not complete exactly 24 slots")
    return ordered


def _validate_pilot_schedule(plan: PilotSchedulePlan) -> None:
    if plan.acceptance.get("status") != "pass" or plan.acceptance.get(
        "pilot_launch_eligible"
    ) is not True:
        raise WebArenaFullScheduleError("pilot schedule is not launchable")
    if plan.acceptance.get("formal_launch_eligible") is not False:
        raise WebArenaFullScheduleError("pilot schedule must not authorize the formal run")
    if len(plan.jobs) != 24:
        raise WebArenaFullScheduleError("pilot schedule must contain 24 jobs")
    if plan.acceptance.get("attempt_policy") != PILOT_ATTEMPT_POLICY:
        raise WebArenaFullScheduleError("pilot fresh-attempt policy changed")
    expected: list[tuple[int, str]] = []
    for task_id, order in zip(PILOT_TASK_IDS, PILOT_AGENT_ORDERS, strict=True):
        expected.extend((task_id, agent) for agent in order)
    observed = [(int(job["task_id"]), str(job["agent_id"])) for job in plan.jobs]
    if observed != expected:
        raise WebArenaFullScheduleError("pilot task/agent counterbalance order changed")
    for job in plan.jobs:
        task_id = int(job["task_id"])
        agent_id = str(job["agent_id"])
        if int(job["seed"]) != 123000 + task_id:
            raise WebArenaFullScheduleError("pilot paired seed changed")
        if job.get("execution_target") != EXPECTED_ROUTES[agent_id]:
            raise WebArenaFullScheduleError("pilot execution route changed")
        if job.get("reset_policy") != "recreate_task_sites_from_digest_v1":
            raise WebArenaFullScheduleError("pilot reset policy changed")
        expected_attempt_id = (
            f"attempt-{job['record_slot_id']}-{PILOT_ATTEMPT_ORDINAL:03d}"
        )
        if job.get("attempt_id") != expected_attempt_id:
            raise WebArenaFullScheduleError("pilot attempt identity changed")


def _validate_full_source_index(path: str | Path) -> dict[str, Any]:
    source_file = _regular_file(path, "full jobs source index")
    _validate_sha_sidecar(source_file, "full jobs source index")
    source_hash = sha256_file(source_file)
    if source_hash != EXPECTED_FULL_SOURCE_INDEX_SHA256:
        raise WebArenaFullScheduleError("full jobs source index hash changed")
    source = _load_mapping(source_file, "full jobs source index")
    if (
        source.get("schema_version") != SCHEDULE_INDEX_SCHEMA_VERSION
        or source.get("job_count") != 2436
        or source.get("jobs_sha256") != EXPECTED_FULL_SOURCE_JOBS_SHA256
    ):
        raise WebArenaFullScheduleError("full jobs source index identity changed")
    return {
        "path": _display_path(source_file),
        "index_sha256": source_hash,
        "job_count": 2436,
        "jobs_sha256": EXPECTED_FULL_SOURCE_JOBS_SHA256,
    }


def _validate_plan_source_binding(
    plan: PilotSchedulePlan, source: Mapping[str, Any]
) -> None:
    if (
        plan.acceptance.get("full_schedule_jobs_sha256")
        != source.get("jobs_sha256")
    ):
        raise WebArenaFullScheduleError(
            "pilot plan is not derived from the canonical full jobs source"
        )


def _regular_file(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path)
    if not resolved.is_file() or resolved.is_symlink():
        raise WebArenaFullScheduleError(f"{label} is missing or unsafe: {resolved}")
    return resolved


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        raise WebArenaFullScheduleError(f"{label} is not a JSON object")
    return dict(payload)


def _validate_sha_sidecar(path: Path, label: str) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    if not sidecar.is_file() or sidecar.is_symlink():
        raise WebArenaFullScheduleError(f"{label} SHA sidecar is missing")
    parts = sidecar.read_text(encoding="utf-8").strip().split()
    if len(parts) < 1 or parts[0] != sha256_file(path):
        raise WebArenaFullScheduleError(f"{label} SHA sidecar is stale")


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_sha_sidecar(path: Path) -> None:
    path.with_name(path.name + ".sha256").write_text(
        f"{sha256_file(path)}  {path.name}\n", encoding="utf-8"
    )
