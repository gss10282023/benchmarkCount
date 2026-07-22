#!/usr/bin/env python3
"""Run one paid task-0 WebArena-Verified diagnostic on each locked VPS."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib import import_module
import json
from pathlib import Path
import shlex
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.adapters.runtime import (  # noqa: E402
    build_smoke_execution_context,
    run_remote_blind_command,
)
from evidence_system.adapters.webarena_remote_retention import (  # noqa: E402
    PERSISTENT_RESULTS_ROOT,
    RETENTION_MODE,
)
from evidence_system.core.hashing import sha256_file, sha256_object  # noqa: E402
from evidence_system.core.paths import resolve_repo_path  # noqa: E402
from evidence_system.core.schemas import load_json_or_yaml, validate_object  # noqa: E402
from evidence_system.orchestrator.webarena_verified_full import (  # noqa: E402
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_MANIFEST,
    DEFAULT_REMOTE_WORKDIR,
    DEFAULT_SITE_LOCK,
    DEFAULT_SOURCE_BUNDLE,
    EXPECTED_AGENT_IDS,
    EXPECTED_SOURCE_SHA256,
    WebArenaFullScheduleError,
)
from evidence_system.orchestrator.webarena_verified_full_execution import (  # noqa: E402
    _execution_targets,
)
from evidence_system.orchestrator.webarena_verified_run_control import (  # noqa: E402
    audit_remote_slot,
    load_materialized_full_plan,
)
from evidence_system.webarena_sites import load_site_lock  # noqa: E402


CANARY_NAMESPACE = "webarena_verified_v1_2_3_remote_retention_task0_canary"
PAID_CONFIRMATION = "RUN-3-PAID-CANARY"
DEFAULT_ACCEPTANCE_PATH = Path(
    "experiments/step20/webarena_verified/remote_retention_canary_acceptance.json"
)
CONTROL_BINDING_PATHS = (
    "src/evidence_system/adapters/webarena_har_sanitization.py",
    "src/evidence_system/adapters/webarena_official_worker.py",
    "src/evidence_system/adapters/webarena_remote_retention.py",
    "src/evidence_system/adapters/webarena_verified.py",
    "src/evidence_system/cli/webarena_full_control.py",
    "src/evidence_system/orchestrator/webarena_verified_full_execution.py",
    "src/evidence_system/orchestrator/webarena_verified_pilot_execution.py",
    "src/evidence_system/orchestrator/webarena_verified_run_control.py",
    "scripts/build_webarena_verified_circuit_recovery.py",
    "scripts/build_webarena_verified_step20_acceptance.py",
    "scripts/run_webarena_verified_task0_canary.py",
)


def _control_bindings() -> dict[str, Any]:
    plan = load_materialized_full_plan()
    index = dict(plan.acceptance["jobs_index"])
    return {
        "schema_version": "webarena_verified_canary_control_bindings/v1",
        "materialized_full_jobs_index_path": index["path"],
        "materialized_full_jobs_index_sha256": index["sha256"],
        "materialized_full_jobs_sha256": index["jobs_sha256"],
        "materialized_full_job_count": index["job_count"],
        "legacy_native_claim_compiler_runtime_dependency": False,
        "formal_score_draft_provider": "neurips_ed_track_minimal",
        "critical_code_sha256": {
            path: sha256_file(resolve_repo_path(path))
            for path in CONTROL_BINDING_PATHS
        },
    }


def _canary_jobs(
    *,
    task_id: int = 0,
    result_namespace: str = CANARY_NAMESPACE,
) -> list[dict[str, Any]]:
    full = load_materialized_full_plan()
    source_by_agent = {
        str(job["agent_id"]): dict(job)
        for job in full.jobs
        if int(job["task_id"]) == task_id
    }
    if set(source_by_agent) != set(EXPECTED_AGENT_IDS):
        raise WebArenaFullScheduleError(
            f"full schedule lacks one or more task-{task_id} canary jobs"
        )

    jobs: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENT_IDS:
        suffix = agent_id[-1].lower()
        slot_id = f"wv123-teardown-canary-task-{task_id:03d}-agent-{suffix}"
        job = source_by_agent[agent_id]
        job.update(
            {
                "job_id": f"canary-webarena_verified-{task_id:03d}-agent_{suffix}",
                "record_slot_id": slot_id,
                "run_id": f"run-{slot_id}",
                "attempt_id": f"attempt-{slot_id}-001",
                "phase": "preflight",
                "experiment_type": "diagnostic",
                "result_namespace": result_namespace,
                "artifact_retention_mode": RETENTION_MODE,
            }
        )
        report = validate_object("job", job, formal=False, raise_on_error=False)
        if not report.ok:
            raise WebArenaFullScheduleError(
                f"invalid canary job for {agent_id}: {report.to_dict()}"
            )
        jobs.append(job)
    return jobs


def _canary_result_summary(
    *,
    job: Mapping[str, Any],
    audit: Any,
) -> dict[str, Any]:
    """Record only the bounded VPS verification envelope for one canary."""

    review = dict(audit.semantic_review or {})
    required = (
        "remote_artifact_manifest_sha256",
        "remote_slot_acceptance_sha256",
        "security_finding_count",
        "gold_finding_count",
    )
    if any(review.get(field) in (None, "") for field in required):
        raise WebArenaFullScheduleError(
            f"canary job for {job['agent_id']} lacks a bounded VPS verification field"
        )
    if (
        review.get("security_finding_count") != 0
        or review.get("gold_finding_count") != 0
    ):
        raise WebArenaFullScheduleError(
            f"canary job for {job['agent_id']} has a remote security finding"
        )
    return {
        "status": "pass",
        "agent_id": str(job["agent_id"]),
        "record_slot_id": str(job["record_slot_id"]),
        "audit_state": audit.state,
        "worker_status": "completed",
        "native_score": review.get("score"),
        "paid_model_call_count": review.get("paid_model_call_count"),
        "observed_model_cost_usd": review.get("observed_model_cost_usd"),
        "remote_artifact_root": audit.artifact_root,
        "remote_artifact_manifest_sha256": review.get(
            "remote_artifact_manifest_sha256"
        ),
        "remote_slot_acceptance_sha256": review.get(
            "remote_slot_acceptance_sha256"
        ),
        "security_finding_count": review.get("security_finding_count"),
        "gold_finding_count": review.get("gold_finding_count"),
        "artifact_file_count": review.get("artifact_file_count"),
        "artifact_total_size_bytes": review.get("artifact_total_size_bytes"),
        "full_evidence_synced_to_controller": False,
        "runtime_artifacts_downloaded_to_controller": False,
    }


def _finalize_remote_canary_host(
    *,
    agent_id: str,
    target: Any,
    result_namespace: str,
) -> dict[str, Any]:
    """Finalize and retain a bounded host receipt on the VPS only."""

    namespace_root = PERSISTENT_RESULTS_ROOT / "namespaces" / result_namespace
    python_bin = str(
        target.benchmark_config.get("python_bin")
        or f"{target.runner_workdir}/.venv/bin/python"
    )
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && "
        f"PYTHONPATH={shlex.quote(f'{target.remote_workdir}/src')} "
        f"{shlex.quote(python_bin)} -m "
        "evidence_system.adapters.webarena_remote_retention "
        f"finalize-namespace --namespace-root {shlex.quote(str(namespace_root))} "
        f"--server-id {shlex.quote(target.machine_id)}"
    )
    finalized = run_remote_blind_command(
        target,
        command,
        timeout_seconds=900,
        maximum_stdout_bytes=131_072,
        maximum_stderr_bytes=4096,
    )
    if finalized.returncode != 0 or finalized.stderr:
        raise WebArenaFullScheduleError(
            f"remote host finalization failed for {agent_id}"
        )
    try:
        receipt = json.loads(finalized.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise WebArenaFullScheduleError(
            f"remote host finalization returned invalid JSON for {agent_id}"
        ) from exc
    if (
        not isinstance(receipt, Mapping)
        or receipt.get("status") != "pass"
        or receipt.get("server_id") != target.machine_id
        or receipt.get("persistent_namespace_root") != str(namespace_root)
        or receipt.get("slot_count") != 1
        or receipt.get("security_finding_count") != 0
        or receipt.get("gold_finding_count") != 0
        or receipt.get("remote_directory_cleanup_performed") is not False
        or receipt.get("full_evidence_synced_to_controller") is not False
    ):
        raise WebArenaFullScheduleError(
            f"remote host finalization receipt is invalid for {agent_id}"
        )
    return {
        "agent_id": agent_id,
        "server_id": target.machine_id,
        "persistent_namespace_root": str(namespace_root),
        "status": "pass",
        "slot_count": 1,
        "security_scan_executed_on_vps": receipt.get(
            "security_scan_executed_on_vps"
        ),
        "security_finding_count": 0,
        "gold_finding_count": 0,
        "remote_directory_cleanup_performed": False,
        "full_evidence_synced_to_controller": False,
        "receipt_sha256": sha256_object(dict(receipt)),
        "receipt_hash_algorithm": "sha256_canonical_json_v1",
        "vps_resident": True,
    }


def _acceptance_payload(
    *,
    result_namespace: str,
    task_id: int,
    agent_ids: tuple[str, ...],
    results: Mapping[str, Mapping[str, Any]],
    host_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    ordered_results = [dict(results[agent_id]) for agent_id in agent_ids]
    return {
        "schema_version": "webarena_verified_three_host_task0_canary_acceptance/v1",
        "status": "pass",
        "result_namespace": result_namespace,
        "task_id": task_id,
        "paid_slot_count": len(agent_ids),
        "paid_model_call_count": sum(
            int(item.get("paid_model_call_count") or 0) for item in ordered_results
        ),
        "observed_model_cost_usd": round(
            sum(float(item.get("observed_model_cost_usd") or 0.0) for item in ordered_results),
            12,
        ),
        "browser_teardown_mode": "same_thread_as_sync_playwright_owner",
        "required_artifact_audit_pass_count": len(agent_ids),
        "vps_control_plane_namespace_sha256": sha256_object(
            [
                {
                    "record_slot_id": item["record_slot_id"],
                    "remote_slot_acceptance_sha256": item[
                        "remote_slot_acceptance_sha256"
                    ],
                }
                for item in ordered_results
            ]
        ),
        "artifact_retention_mode": RETENTION_MODE,
        "remote_file_and_hash_verification_over_ssh": True,
        "security_scan_and_finalization_executed_on_each_vps": True,
        "full_evidence_synced_to_controller": False,
        "runtime_artifacts_downloaded_to_controller": False,
        "remote_directory_cleanup_performed": False,
        "remote_host_finalization_receipts": host_receipts,
        "results": ordered_results,
        "control_bindings": _control_bindings(),
        "secret_material_recorded": False,
    }


def execute_canary(
    *,
    ssh_key_path: str | Path,
    task_id: int = 0,
    result_namespace: str = CANARY_NAMESPACE,
    agent_ids: tuple[str, ...] = EXPECTED_AGENT_IDS,
) -> dict[str, Any]:
    all_jobs = _canary_jobs(
        task_id=task_id,
        result_namespace=result_namespace,
    )
    jobs = [
        job
        for job in all_jobs
        if str(job["agent_id"]) in agent_ids
    ]
    if not jobs:
        raise WebArenaFullScheduleError("canary agent selection is empty")
    key = resolve_repo_path(ssh_key_path)
    manifest_path = resolve_repo_path(DEFAULT_MANIFEST)
    source_path = resolve_repo_path(DEFAULT_SOURCE_BUNDLE)
    agents_path = resolve_repo_path(DEFAULT_AGENTS_CONFIG)
    dotenv_path = resolve_repo_path(".env")
    site_lock_path = resolve_repo_path(DEFAULT_SITE_LOCK)
    manifest = load_json_or_yaml(manifest_path)
    source_bundle = load_json_or_yaml(source_path)
    if not isinstance(manifest, Mapping) or not isinstance(source_bundle, Mapping):
        raise WebArenaFullScheduleError("canary manifest/source bundle is invalid")
    site_lock = load_site_lock(site_lock_path)
    full = load_materialized_full_plan()
    native_claim_index_sha256 = str(
        dict(full.acceptance.get("inputs") or {}).get("native_claim_index_sha256") or ""
    )
    targets = _execution_targets(
        all_jobs,
        ssh_key_path=key,
        site_lock=site_lock,
        site_lock_path=site_lock_path,
        remote_workdir=DEFAULT_REMOTE_WORKDIR,
        common_run_policy=dict(manifest["common_run_policy"]),
        source_bundle_sha256=sha256_file(source_path),
        native_claim_index_sha256=native_claim_index_sha256,
        site_lock_sha256=sha256_file(site_lock_path),
    )
    context = build_smoke_execution_context(
        manifest_path=manifest_path,
        manifest_hash=sha256_file(manifest_path),
        source_bundle_path=source_path,
        source_bundle_hash=sha256_file(source_path),
        official_split_hash=EXPECTED_SOURCE_SHA256,
        agents_config_path=agents_path,
        dotenv_path=dotenv_path,
    )
    adapter = import_module("evidence_system.adapters.webarena_verified")
    planner = getattr(adapter, "plan_smoke_execution")
    executor = getattr(adapter, "execute_smoke_job")

    results: dict[str, dict[str, Any]] = {}

    def run(job: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        agent_id = str(job["agent_id"])
        target = targets[agent_id]
        execution_plan = planner(
            job,
            target=target,
            agents_config_path=str(agents_path),
            dotenv_path=str(dotenv_path),
            source_bundle_path=str(source_path),
            source_bundle=dict(source_bundle),
        )
        if execution_plan.get("status") != "runnable":
            raise WebArenaFullScheduleError(f"canary job for {agent_id} is not runnable")
        result = dict(
            executor(
                job,
                target=target,
                execution_plan=execution_plan,
                context=context,
            )
        )
        if result.get("status") != "completed":
            raise WebArenaFullScheduleError(
                f"canary job for {agent_id} did not complete: {result.get('status')}"
            )
        audit = audit_remote_slot(
            job, ssh_key_path=key, site_lock=site_lock
        )
        if not audit.reusable:
            raise WebArenaFullScheduleError(
                f"canary job for {agent_id} failed artifact audit: {audit.state}"
            )
        return agent_id, _canary_result_summary(job=job, audit=audit)

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="webarena-canary") as pool:
        futures = {pool.submit(run, job): str(job["agent_id"]) for job in jobs}
        for future in as_completed(futures):
            agent_id, result = future.result()
            results[agent_id] = result

    host_receipts = [
        _finalize_remote_canary_host(
            agent_id=agent_id,
            target=targets[agent_id],
            result_namespace=result_namespace,
        )
        for agent_id in agent_ids
    ]
    return _acceptance_payload(
        result_namespace=result_namespace,
        task_id=task_id,
        agent_ids=agent_ids,
        results=results,
        host_receipts=host_receipts,
    )


def validate_existing_canary(
    *,
    ssh_key_path: str | Path,
    task_id: int = 0,
    result_namespace: str = CANARY_NAMESPACE,
    agent_ids: tuple[str, ...] = EXPECTED_AGENT_IDS,
) -> dict[str, Any]:
    """Re-audit the three completed canary slots without making paid calls."""

    key = resolve_repo_path(ssh_key_path)
    all_jobs = _canary_jobs(task_id=task_id, result_namespace=result_namespace)
    manifest_path = resolve_repo_path(DEFAULT_MANIFEST)
    source_path = resolve_repo_path(DEFAULT_SOURCE_BUNDLE)
    site_lock_path = resolve_repo_path(DEFAULT_SITE_LOCK)
    manifest = load_json_or_yaml(manifest_path)
    if not isinstance(manifest, Mapping):
        raise WebArenaFullScheduleError("canary manifest is invalid")
    site_lock = load_site_lock(site_lock_path)
    full = load_materialized_full_plan()
    native_claim_index_sha256 = str(
        dict(full.acceptance.get("inputs") or {}).get("native_claim_index_sha256")
        or ""
    )
    targets = _execution_targets(
        all_jobs,
        ssh_key_path=key,
        site_lock=site_lock,
        site_lock_path=site_lock_path,
        remote_workdir=DEFAULT_REMOTE_WORKDIR,
        common_run_policy=dict(manifest["common_run_policy"]),
        source_bundle_sha256=sha256_file(source_path),
        native_claim_index_sha256=native_claim_index_sha256,
        site_lock_sha256=sha256_file(site_lock_path),
    )
    results: dict[str, dict[str, Any]] = {}
    for job in all_jobs:
        if str(job["agent_id"]) not in agent_ids:
            continue
        audit = audit_remote_slot(job, ssh_key_path=key, site_lock=site_lock)
        if not audit.reusable:
            raise WebArenaFullScheduleError(
                f"canary job for {job['agent_id']} failed artifact audit: {audit.state}"
            )
        results[str(job["agent_id"])] = _canary_result_summary(job=job, audit=audit)

    host_receipts = [
        _finalize_remote_canary_host(
            agent_id=agent_id,
            target=targets[agent_id],
            result_namespace=result_namespace,
        )
        for agent_id in agent_ids
    ]
    return _acceptance_payload(
        result_namespace=result_namespace,
        task_id=task_id,
        agent_ids=agent_ids,
        results=results,
        host_receipts=host_receipts,
    )


def write_acceptance(
    payload: Mapping[str, Any],
    *,
    output_path: str | Path = DEFAULT_ACCEPTANCE_PATH,
) -> Path:
    output = resolve_repo_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(f"{output.suffix}.tmp")
    temporary.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    digest = sha256_file(output)
    output.with_suffix(f"{output.suffix}.sha256").write_text(
        f"{digest}  {output.name}\n",
        encoding="ascii",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key-path")
    parser.add_argument("--confirm-paid-canary", default="")
    parser.add_argument("--validate-existing", action="store_true")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--result-namespace")
    parser.add_argument("--acceptance-path")
    parser.add_argument(
        "--agent-id",
        action="append",
        choices=EXPECTED_AGENT_IDS,
        help="run only the selected agent; repeat to select more than one",
    )
    args = parser.parse_args()
    if not args.validate_existing:
        if not args.ssh_key_path:
            parser.error("--ssh-key-path is required for a paid canary")
        if args.confirm_paid_canary != PAID_CONFIRMATION:
            parser.error(f"--confirm-paid-canary must equal {PAID_CONFIRMATION}")
    if not args.ssh_key_path:
        parser.error("--ssh-key-path is required for SSH validation")
    try:
        result_namespace = args.result_namespace or (
            CANARY_NAMESPACE
            if args.task_id == 0
            else f"webarena_verified_v1_2_3_native_env_close_task{args.task_id}_canary"
        )
        acceptance_path = args.acceptance_path or (
            str(DEFAULT_ACCEPTANCE_PATH)
            if args.task_id == 0
            else (
                "experiments/step20/webarena_verified/"
                f"native_env_close_task{args.task_id}_canary_acceptance.json"
            )
        )
        if not args.validate_existing:
            result = execute_canary(
                ssh_key_path=args.ssh_key_path,
                task_id=args.task_id,
                result_namespace=result_namespace,
                agent_ids=tuple(args.agent_id or EXPECTED_AGENT_IDS),
            )
        else:
            result = validate_existing_canary(
                ssh_key_path=args.ssh_key_path,
                task_id=args.task_id,
                result_namespace=result_namespace,
                agent_ids=tuple(args.agent_id or EXPECTED_AGENT_IDS),
            )
        written_acceptance = write_acceptance(result, output_path=acceptance_path)
        result["acceptance_path"] = str(written_acceptance.relative_to(ROOT))
        result["acceptance_sha256"] = sha256_file(written_acceptance)
    except (OSError, ValueError, WebArenaFullScheduleError, RuntimeError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": "webarena_verified_three_host_task0_canary/v1",
                    "status": "blocked",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "secret_material_recorded": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
