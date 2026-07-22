#!/usr/bin/env python3
"""Resume the MiniWoB cohort after a health-gated Agent C provider recovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from evidence_system.adapters.runtime import build_job_paths
from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path
from evidence_system.orchestrator.jobs import execute_planned_jobs, plan_smoke_jobs, resolve_infra_target

from run_miniwob_remaining22_vps2_campaign import (
    AGENTS,
    AGENT_IDS,
    BUNDLE,
    CONTRACTS,
    CONTROL,
    EXPERIMENT_LOCK,
    INFRA,
    JOBS,
    MANIFEST,
    NAMESPACE,
    _audit_job,
    _formalize,
    _health,
    _mapping,
    _verify_deployed_runtime,
)


RECOVERY_JOB_IDS = (
    "full-miniwob-miniwob.click-pie-nodelay-agent_c",
    "full-miniwob-miniwob.use-slider-agent_c",
    "full-miniwob-miniwob.email-inbox-forward-nl-turk-agent_c",
)
PROVIDER_HEALTH = (
    f"results/namespaces/{NAMESPACE}/campaign_control/"
    "agent-c-provider-recovery-health.json"
)


def _plan_all(target: Any) -> list[Any]:
    planned = []
    for agent_id in AGENT_IDS:
        planned.extend(
            plan_smoke_jobs(
                domain="miniwob",
                phase="full",
                experiment_type="diagnostic",
                case_count=22,
                agent_ids=[agent_id],
                seed=7,
                manifest_path=MANIFEST,
                source_bundle_path=BUNDLE,
                contracts_dir=CONTRACTS,
                infra_config_path=INFRA,
                agents_config_path=AGENTS,
                jobs_dir=JOBS,
                result_namespace=NAMESPACE,
            )
        )
    formal = [_formalize(item, target) for item in planned]
    if len(formal) != 66:
        raise RuntimeError("recovery plan is not the frozen 66-slot cohort")
    return formal


def _accepted(item: Any) -> bool:
    paths = build_job_paths(item.job)
    if not paths.raw_run_path.is_file():
        return False
    _audit_job(item, {"status": "skipped_completed"})
    return True


def _run_batch(
    batch: Sequence[Any],
    *,
    workers: int,
    label: str,
    target: Any,
    control_dir: Path,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": "miniwob_provider_recovery_stage/v1",
        "status": "running",
        "label": label,
        "started_at": utc_now_iso(),
        "authorized_workers": workers,
        "batch_size": len(batch),
        "job_ids": [str(item.job["job_id"]) for item in batch],
        "health_before": _health(target, control_dir, f"{label}-before"),
        "audits": [],
        "failures": [],
    }
    path = control_dir / f"{label}.json"
    write_json(path, receipt)
    executed = execute_planned_jobs(
        batch,
        manifest_path=MANIFEST,
        source_bundle_path=BUNDLE,
        infra_config_path=INFRA,
        agents_config_path=AGENTS,
        max_workers=workers,
        fail_fast_on_noncompleted=True,
        skip_completed=True,
        retry_no_response_attempts=0,
        continue_on_error=True,
    )
    for result in executed:
        try:
            receipt["audits"].append(
                _audit_job(result.planned, result.execution_result)
            )
        except Exception as exc:
            receipt["failures"].append(
                {
                    "job_id": result.planned.job["job_id"],
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
    receipt["health_after"] = _health(target, control_dir, f"{label}-after")
    receipt["completed_at"] = utc_now_iso()
    receipt["status"] = "accepted" if not receipt["failures"] else "failed"
    write_json(path, receipt)
    return receipt


def main() -> int:
    target = resolve_infra_target("miniwob", _mapping(resolve_repo_path(INFRA)))
    control_dir = resolve_repo_path(CONTROL)
    health_path = resolve_repo_path(PROVIDER_HEALTH)
    provider_health = _mapping(health_path)
    if (
        provider_health.get("status") != "accepted"
        or provider_health.get("logical_successes") != 31
        or provider_health.get("max_workers_verified") != 10
        or provider_health.get("provider_only") != "baidu/fp8"
    ):
        raise RuntimeError("Agent C provider recovery health gate is not accepted")
    deployed = _verify_deployed_runtime(target)
    formal = _plan_all(target)
    by_id = {str(item.job["job_id"]): item for item in formal}
    recovery = [by_id[job_id] for job_id in RECOVERY_JOB_IDS]
    if any(_accepted(item) for item in recovery):
        raise RuntimeError("a provider-recovery slot is unexpectedly already accepted")

    repair = _run_batch(
        recovery,
        workers=1,
        label="provider-recovery-repair-serial",
        target=target,
        control_dir=control_dir,
    )
    if repair["status"] != "accepted":
        return 1

    remaining = [item for item in formal if not _accepted(item)]
    if len(remaining) != 15:
        raise RuntimeError(f"expected 15 untouched Agent C slots after repair, found {len(remaining)}")
    first = _run_batch(
        remaining[:10],
        workers=10,
        label="provider-recovery-full-10",
        target=target,
        control_dir=control_dir,
    )
    if first["status"] != "accepted":
        return 1
    tail = _run_batch(
        remaining[10:],
        workers=10,
        label="provider-recovery-tail-5",
        target=target,
        control_dir=control_dir,
    )
    if tail["status"] != "accepted":
        return 1

    final_audits = [_audit_job(item, {"status": "skipped_completed"}) for item in formal]
    labels: dict[str, int] = {}
    for audit in final_audits:
        label = str(audit["native_label"])
        labels[label] = labels.get(label, 0) + 1
    completion = {
        "schema_version": "miniwob_remaining22_vps2_completion/v1",
        "status": "accepted",
        "completed_at": utc_now_iso(),
        "namespace": NAMESPACE,
        "slot_count": len(final_audits),
        "case_count": 22,
        "agent_count": 3,
        "native_label_counts": labels,
        "all_run_summaries_completed": True,
        "all_environments_closed_normally": True,
        "all_released_evaluator_outputs_verified": True,
        "all_remote_local_tree_receipts_verified": True,
        "all_controller_artifact_hashes_verified": True,
        "provider_health_path": PROVIDER_HEALTH,
        "provider_health_sha256": sha256_file(health_path),
        "experiment_lock_path": EXPERIMENT_LOCK,
        "experiment_lock_sha256": sha256_file(resolve_repo_path(EXPERIMENT_LOCK)),
        "deployed_runtime": deployed,
        "stage_paths": [
            str((control_dir / "provider-recovery-repair-serial.json").relative_to(resolve_repo_path("."))),
            str((control_dir / "provider-recovery-full-10.json").relative_to(resolve_repo_path("."))),
            str((control_dir / "provider-recovery-tail-5.json").relative_to(resolve_repo_path("."))),
        ],
        "audits": final_audits,
    }
    write_json(control_dir / "final-completion-receipt.json", completion)
    print(json.dumps(completion, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
