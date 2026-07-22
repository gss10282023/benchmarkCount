#!/usr/bin/env python3
"""Run the final, serial infrastructure retry for four preserved MiniWoB slots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.paths import resolve_repo_path
from evidence_system.orchestrator.jobs import execute_planned_jobs, plan_smoke_jobs, resolve_infra_target

from run_miniwob_remaining22_vps2_campaign import (
    AGENTS,
    BUNDLE,
    CONTRACTS,
    CONTROL,
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


RETRY_JOB_IDS = (
    "full-miniwob-miniwob.terminal-agent_c",
    "full-miniwob-miniwob.click-pie-nodelay-agent_c",
    "full-miniwob-miniwob.use-slider-agent_c",
    "full-miniwob-miniwob.email-inbox-forward-nl-turk-agent_c",
)


def main() -> int:
    infra_payload = _mapping(resolve_repo_path(INFRA))
    target = resolve_infra_target("miniwob", infra_payload)
    planned = plan_smoke_jobs(
        domain="miniwob",
        phase="full",
        experiment_type="diagnostic",
        case_count=22,
        agent_ids=["Agent C"],
        seed=7,
        manifest_path=MANIFEST,
        source_bundle_path=BUNDLE,
        contracts_dir=CONTRACTS,
        infra_config_path=INFRA,
        agents_config_path=AGENTS,
        jobs_dir=JOBS,
        result_namespace=NAMESPACE,
    )
    selected = {str(item.job["job_id"]): _formalize(item, target) for item in planned}
    if set(RETRY_JOB_IDS) - set(selected):
        raise RuntimeError("final retry job set is not present in the frozen plan")

    control_dir = resolve_repo_path(CONTROL)
    attempt_root = resolve_repo_path(
        f"results/namespaces/{NAMESPACE}/infra_attempts"
    )
    for job_id in RETRY_JOB_IDS:
        if not (attempt_root / job_id / "controller_adapter_attempt2").is_dir():
            raise RuntimeError(f"second controller attempt is not preserved: {job_id}")
        if not (attempt_root / job_id / "remote_native_attempt2" / "remote_tree_receipt.json").is_file():
            raise RuntimeError(f"second remote attempt is not sealed and preserved: {job_id}")

    receipt: dict[str, Any] = {
        "schema_version": "miniwob_final_infra_retry/v1",
        "status": "running",
        "started_at": utc_now_iso(),
        "attempt_number": 3,
        "workers": 1,
        "reason": "final locked retry after preserved provider-empty or environment-close-timeout attempts",
        "benchmark_semantics_changed": False,
        "teardown_timeout_seconds": 60,
        "deployed_runtime": _verify_deployed_runtime(target),
        "health_before": _health(target, control_dir, "final-infra-retry-before"),
        "jobs": [],
    }
    receipt_path = control_dir / "final-infra-retry.json"
    write_json(receipt_path, receipt)

    failed = False
    for job_id in RETRY_JOB_IDS:
        item = selected[job_id]
        record: dict[str, Any] = {"job_id": job_id, "started_at": utc_now_iso()}
        try:
            executed = execute_planned_jobs(
                [item],
                manifest_path=MANIFEST,
                source_bundle_path=BUNDLE,
                infra_config_path=INFRA,
                agents_config_path=AGENTS,
                max_workers=1,
                fail_fast_on_noncompleted=True,
                skip_completed=True,
                retry_no_response_attempts=0,
                continue_on_error=False,
            )
            record["audit"] = _audit_job(
                executed[0].planned, executed[0].execution_result
            )
            record["status"] = "accepted"
        except Exception as exc:
            failed = True
            record.update(
                {
                    "status": "infra_failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
        record["completed_at"] = utc_now_iso()
        receipt["jobs"].append(record)
        write_json(receipt_path, receipt)

    receipt["health_after"] = _health(target, control_dir, "final-infra-retry-after")
    receipt["completed_at"] = utc_now_iso()
    receipt["status"] = "failed" if failed else "accepted"
    receipt["accepted_jobs"] = sum(
        record["status"] == "accepted" for record in receipt["jobs"]
    )
    write_json(receipt_path, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
