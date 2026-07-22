"""Three-VPS executor for an accepted frozen WebArena-Verified full schedule."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import threading
from typing import Any

from evidence_system.adapters.runtime import build_smoke_execution_context
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator.jobs import InfraBenchmarkTarget
from evidence_system.orchestrator.webarena_verified_full import (
    ARTIFACT_RETENTION_MODE,
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_MANIFEST,
    DEFAULT_REMOTE_WORKDIR,
    DEFAULT_SITE_LOCK,
    DEFAULT_SOURCE_BUNDLE,
    EXPECTED_AGENT_IDS,
    EXPECTED_RECORD_SLOT_COUNT,
    EXPECTED_ROUTES,
    EXPECTED_SOURCE_BUNDLE_SHA256,
    EXPECTED_SOURCE_SHA256,
    FullSchedulePlan,
    WebArenaFullScheduleError,
    formal_benchmark_config,
)
from evidence_system.webarena_sites import load_site_lock


AdapterPlanner = Callable[..., dict[str, Any]]
AdapterExecutor = Callable[..., dict[str, Any]]
ProgressCallback = Callable[[Mapping[str, Any], Mapping[str, Any], int, int], None]


@dataclass(frozen=True)
class FullExecutedJob:
    job: dict[str, Any]
    execution_result: dict[str, Any]


def _materialized_lineage_sha256(
    plan: FullSchedulePlan,
    field: str,
) -> str:
    """Return one hash agreed by every materialized formal job."""

    values = {
        str(dict(job.get("formal_policy_lock") or {}).get(field) or "")
        for job in plan.jobs
    }
    if len(values) != 1:
        raise WebArenaFullScheduleError(
            f"materialized formal jobs disagree on historical lineage: {field}"
        )
    value = next(iter(values))
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise WebArenaFullScheduleError(
            f"materialized formal jobs have no valid historical lineage hash: {field}"
        )
    return value


def execute_full_schedule(
    plan: FullSchedulePlan,
    *,
    ssh_key_path: str | Path,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    dotenv_path: str | Path = ".env",
    site_lock_path: str | Path = DEFAULT_SITE_LOCK,
    remote_workdir: str = DEFAULT_REMOTE_WORKDIR,
    progress_callback: ProgressCallback | None = None,
    adapter_planner: AdapterPlanner | None = None,
    adapter_executor: AdapterExecutor | None = None,
    recovery_prelude_slot_ids: Sequence[str] = (),
) -> list[FullExecutedJob]:
    """Run exactly one sequential 812-case lane on each locked VPS.

    The three lanes run concurrently, but each VPS has exactly one in-flight
    slot.  A recovery-authorized prelude may first execute an exact set of
    previously failed slots before any lane resumes.  The WebArena adapter
    performs and validates the mandatory site reset receipt before reading the
    API key or starting the browser/model worker.
    """

    _validate_executable_plan(plan)
    key_path = resolve_repo_path(ssh_key_path)
    if not key_path.is_file():
        raise WebArenaFullScheduleError(f"SSH private key is missing: {key_path}")
    manifest_file = resolve_repo_path(manifest_path)
    source_bundle_file = resolve_repo_path(source_bundle_path)
    agents_file = resolve_repo_path(agents_config_path)
    dotenv_file = resolve_repo_path(dotenv_path)
    site_lock_file = resolve_repo_path(site_lock_path)
    if site_lock_file.resolve() != resolve_repo_path(DEFAULT_SITE_LOCK).resolve():
        raise WebArenaFullScheduleError(
            "formal execution site-lock path differs from the planned canonical path"
        )
    if remote_workdir.rstrip("/") != DEFAULT_REMOTE_WORKDIR:
        raise WebArenaFullScheduleError(
            "formal execution remote_workdir differs from the hashed runtime config"
        )
    for label, path in (
        ("manifest", manifest_file),
        ("source bundle", source_bundle_file),
        ("agents config", agents_file),
        ("site lock", site_lock_file),
    ):
        if not path.is_file() or path.is_symlink():
            raise WebArenaFullScheduleError(f"formal execution {label} is missing or unsafe: {path}")
    if sha256_file(source_bundle_file) != EXPECTED_SOURCE_BUNDLE_SHA256:
        raise WebArenaFullScheduleError("formal execution source bundle hash changed after planning")

    source_bundle = load_json_or_yaml(source_bundle_file)
    if not isinstance(source_bundle, Mapping):
        raise WebArenaFullScheduleError("formal execution source bundle is not an object")
    site_lock = load_site_lock(site_lock_file)
    manifest = load_json_or_yaml(manifest_file)
    if not isinstance(manifest, Mapping) or not isinstance(
        manifest.get("common_run_policy"), Mapping
    ):
        raise WebArenaFullScheduleError("formal execution manifest run policy is missing")
    native_claim_index_sha256 = _materialized_lineage_sha256(
        plan,
        "native_claim_index_sha256",
    )
    context = build_smoke_execution_context(
        manifest_path=manifest_file,
        manifest_hash=sha256_file(manifest_file),
        source_bundle_path=source_bundle_file,
        source_bundle_hash=sha256_file(source_bundle_file),
        official_split_hash=EXPECTED_SOURCE_SHA256,
        agents_config_path=agents_file,
        dotenv_path=dotenv_file,
    )
    adapter = import_module("evidence_system.adapters.webarena_verified")
    planner = adapter_planner or getattr(adapter, "plan_smoke_execution")
    executor = adapter_executor or getattr(adapter, "execute_smoke_job")
    targets = _execution_targets(
        plan.jobs,
        ssh_key_path=key_path,
        site_lock=site_lock,
        site_lock_path=site_lock_file,
        remote_workdir=remote_workdir,
        common_run_policy=dict(manifest["common_run_policy"]),
        source_bundle_sha256=sha256_file(source_bundle_file),
        native_claim_index_sha256=native_claim_index_sha256,
        site_lock_sha256=sha256_file(site_lock_file),
    )

    lanes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    jobs_by_slot: dict[str, dict[str, Any]] = {}
    for raw_job in plan.jobs:
        job = dict(raw_job)
        slot_id = str(job["record_slot_id"])
        lanes[str(job["agent_id"])].append(job)
        jobs_by_slot[slot_id] = job
    if set(lanes) != set(EXPECTED_AGENT_IDS):
        raise WebArenaFullScheduleError("formal execution lost one or more agent lanes")
    prelude_slot_ids = tuple(str(slot_id) for slot_id in recovery_prelude_slot_ids)
    if len(prelude_slot_ids) != len(set(prelude_slot_ids)):
        raise WebArenaFullScheduleError("recovery prelude contains duplicate slots")
    missing_prelude = [slot_id for slot_id in prelude_slot_ids if slot_id not in jobs_by_slot]
    if missing_prelude:
        raise WebArenaFullScheduleError(
            f"recovery prelude contains unknown slot: {missing_prelude[0]}"
        )
    prelude_slot_set = set(prelude_slot_ids)

    stop = threading.Event()
    progress_lock = threading.Lock()
    result_lock = threading.Lock()
    completed_count = 0
    by_slot: dict[str, FullExecutedJob] = {}

    def execute_one(job: dict[str, Any]) -> None:
        nonlocal completed_count
        target = targets[str(job["agent_id"])]
        execution_plan = planner(
            job,
            target=target,
            agents_config_path=str(agents_file),
            dotenv_path=str(dotenv_file),
            source_bundle_path=str(source_bundle_file),
            source_bundle=dict(source_bundle),
        )
        if execution_plan.get("status") != "runnable":
            stop.set()
            raise WebArenaFullScheduleError(
                f"slot {job['record_slot_id']} is not runnable: "
                f"{execution_plan.get('blocking_reason')}"
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
                f"slot {job['record_slot_id']} did not complete: {result.get('status')}"
            )
        executed = FullExecutedJob(job=job, execution_result=result)
        with result_lock:
            if job["record_slot_id"] in by_slot:
                stop.set()
                raise WebArenaFullScheduleError(
                    f"duplicate executed slot: {job['record_slot_id']}"
                )
            by_slot[str(job["record_slot_id"])] = executed
        with progress_lock:
            completed_count += 1
            current = completed_count
            if progress_callback is not None:
                progress_callback(job, result, current, EXPECTED_RECORD_SLOT_COUNT)

    def run_lane(agent_id: str) -> None:
        for job in lanes[agent_id]:
            if stop.is_set():
                return
            if str(job["record_slot_id"]) in prelude_slot_set:
                continue
            execute_one(job)

    # Recovery preludes run to completion before B/C or any new A slot can
    # start.  If a repaired slot still fails, its wrapped executor raises and
    # the normal circuit policy prevents the full three-lane resume.
    for slot_id in prelude_slot_ids:
        execute_one(jobs_by_slot[slot_id])

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="webarena-full") as pool:
        futures = {pool.submit(run_lane, agent_id): agent_id for agent_id in EXPECTED_AGENT_IDS}
        try:
            for future in as_completed(futures):
                future.result()
        except Exception:
            stop.set()
            for future in futures:
                future.cancel()
            raise

    ordered = [by_slot[str(job["record_slot_id"])] for job in plan.jobs]
    if len(ordered) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError(
            f"formal execution completed {len(ordered)} of {EXPECTED_RECORD_SLOT_COUNT} slots"
        )
    return ordered


def _execution_targets(
    jobs: Sequence[Mapping[str, Any]],
    *,
    ssh_key_path: Path,
    site_lock: Mapping[str, Any],
    site_lock_path: Path,
    remote_workdir: str,
    common_run_policy: Mapping[str, Any],
    source_bundle_sha256: str,
    native_claim_index_sha256: str,
    site_lock_sha256: str,
) -> dict[str, InfraBenchmarkTarget]:
    del site_lock_path
    targets: dict[str, InfraBenchmarkTarget] = {}
    for agent_id in EXPECTED_AGENT_IDS:
        route = EXPECTED_ROUTES[agent_id]
        agent_jobs = [job for job in jobs if job.get("agent_id") == agent_id]
        hashes = {str(job.get("benchmark_config_hash")) for job in agent_jobs}
        if len(hashes) != 1:
            raise WebArenaFullScheduleError(
                f"{agent_id} formal jobs do not share one benchmark config hash"
            )
        benchmark_config = formal_benchmark_config(
            route=route,
            common_run_policy=common_run_policy,
            source_bundle_sha256=source_bundle_sha256,
            native_claim_index_sha256=native_claim_index_sha256,
            site_lock_sha256=site_lock_sha256,
        )
        benchmark_config_hash = sha256_object(benchmark_config)
        if hashes != {benchmark_config_hash}:
            raise WebArenaFullScheduleError(
                f"{agent_id} job benchmark_config_hash does not match the exact runtime config"
            )
        runner_root = str(benchmark_config["install_dir"])
        if runner_root != str(site_lock["runner_root"]):
            raise WebArenaFullScheduleError(
                f"{agent_id} site lock runner root differs from runtime config"
            )
        targets[agent_id] = InfraBenchmarkTarget(
            machine_id=str(route["server_id"]),
            machine_role="webarena_vps",
            ssh_host=str(route["ssh_host"]),
            ssh_user=str(route["ssh_user"]),
            ssh_port=22,
            ssh_key_path=str(ssh_key_path),
            remote_workdir=remote_workdir.rstrip("/"),
            runner_workdir=runner_root,
            benchmark_name="WebArena-Verified",
            benchmark_config=benchmark_config,
            benchmark_config_hash=benchmark_config_hash,
            runner_command=f"{runner_root}/.venv/bin/python",
            machine_concurrency=1,
            ssh_host_ed25519_fingerprint=str(
                route["ssh_host_ed25519_fingerprint"]
            ),
            ssh_public_key_fingerprint=str(
                route["controller_ssh_public_key_fingerprint"]
            ),
        )
    return targets


def _validate_executable_plan(plan: FullSchedulePlan) -> None:
    if plan.acceptance.get("status") != "pass" or plan.acceptance.get(
        "formal_launch_eligible"
    ) is not True:
        raise WebArenaFullScheduleError("refusing to execute a non-launchable schedule")
    if len(plan.jobs) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("formal execution requires exactly 2,436 jobs")
    seen: set[str] = set()
    for position, job in enumerate(plan.jobs):
        task_id = position // len(EXPECTED_AGENT_IDS)
        agent_id = EXPECTED_AGENT_IDS[position % len(EXPECTED_AGENT_IDS)]
        expected_slot_id = f"wv123-task-{task_id:03d}-agent-{agent_id[-1].lower()}"
        if str(job.get("record_slot_id")) != expected_slot_id:
            raise WebArenaFullScheduleError(
                f"formal execution slot order changed at position {position}"
            )
        if expected_slot_id in seen:
            raise WebArenaFullScheduleError(f"duplicate formal slot: {expected_slot_id}")
        seen.add(expected_slot_id)
        if int(job.get("task_id", -1)) != task_id or job.get("agent_id") != agent_id:
            raise WebArenaFullScheduleError(
                f"formal execution task/agent product changed at {expected_slot_id}"
            )
        if int(job.get("seed", -1)) != 123000 + task_id:
            raise WebArenaFullScheduleError(
                f"formal execution paired seed changed at {expected_slot_id}"
            )
        if job.get("execution_target") != EXPECTED_ROUTES[agent_id]:
            raise WebArenaFullScheduleError(
                f"formal execution route changed at {expected_slot_id}"
            )
        if job.get("requested_model") != EXPECTED_ROUTES[agent_id]["model"]:
            raise WebArenaFullScheduleError(
                f"formal execution model changed at {expected_slot_id}"
            )
        if job.get("reset_policy") != "recreate_task_sites_from_digest_v1":
            raise WebArenaFullScheduleError(
                f"formal execution reset policy changed at {expected_slot_id}"
            )
        if job.get("reset_receipt_relative_path") != "reset_receipt.json":
            raise WebArenaFullScheduleError(
                f"formal execution reset receipt path changed at {expected_slot_id}"
            )
        if job.get("artifact_retention_mode") != ARTIFACT_RETENTION_MODE:
            raise WebArenaFullScheduleError(
                f"formal execution artifact retention changed at {expected_slot_id}"
            )
        if not list(job.get("task_sites") or []):
            raise WebArenaFullScheduleError(
                f"formal execution task sites are empty at {expected_slot_id}"
            )


def execution_input_hash(plan: FullSchedulePlan) -> str:
    """Return a stable, secret-free hash for the exact executable schedule."""

    return sha256_object(list(plan.jobs))
