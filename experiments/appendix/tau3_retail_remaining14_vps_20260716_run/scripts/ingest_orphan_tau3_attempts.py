#!/usr/bin/env python3
"""Ingest completed Tau2 native outputs after a controller transport loss."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from evidence_system.adapters.runtime import (
    build_artifact_manifest,
    build_job_paths,
    build_raw_run,
    build_smoke_execution_context,
    default_adapter_artifacts,
    remote_job_result_dir,
    rsync_remote_tree,
    write_environment_snapshot,
    write_llm_call_logs,
)
from evidence_system.adapters.tau3_retail import (
    _summarize_tau3_results,
    _tau3_artifacts,
    _tau3_llm_events,
)
from evidence_system.contracts.common import load_mapping
from evidence_system.core.hashing import sha256_file, sha256_path
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.orchestrator.jobs import plan_smoke_jobs, resolve_infra_target


NAMESPACE = "tau3-retail-remaining14-vps-20260716"
MANIFEST = "experiments/appendix/tau3_retail_remaining14_vultr_run_manifest.yaml"
SOURCE_BUNDLE = "experiments/evidence_contracts/source_bundles/tau3_retail_remaining14_source_bundle.json"
CONTRACTS_DIR = "experiments/evidence_contracts/prelock_empty"
INFRA = "configs/tau3_remaining14_vultr.json"
AGENTS_CONFIG = "configs/agents.yaml"
JOBS_DIR = f"results/jobs/full/namespaces/{NAMESPACE}"
STARTED_AT = "2026-07-16T06:43:38+00:00"


def main(case_ids: list[str]) -> int:
    planned = plan_smoke_jobs(
        domain="tau3_retail",
        phase="full",
        experiment_type="appendix",
        case_count=14,
        agent_ids=["Agent C"],
        seed=107,
        manifest_path=MANIFEST,
        source_bundle_path=SOURCE_BUNDLE,
        contracts_dir=CONTRACTS_DIR,
        infra_config_path=INFRA,
        agents_config_path=AGENTS_CONFIG,
        jobs_dir=JOBS_DIR,
        result_namespace=NAMESPACE,
    )
    by_case = {str(item.job["case_unit_id"]): item for item in planned}
    target = resolve_infra_target("tau3_retail", load_mapping(INFRA))
    context = build_smoke_execution_context(
        manifest_path=MANIFEST,
        manifest_hash=sha256_file(resolve_repo_path(MANIFEST)),
        source_bundle_path=SOURCE_BUNDLE,
        source_bundle_hash=sha256_file(resolve_repo_path(SOURCE_BUNDLE)),
        official_split_hash=planned[0].official_split_hash,
        agents_config_path=AGENTS_CONFIG,
        dotenv_path=".env",
    )
    audit_rows = []
    for case_id in case_ids:
        item = by_case[case_id]
        job = item.job
        paths = build_job_paths(job)
        remote_output = remote_job_result_dir(target, job)
        rsync_remote_tree(target, remote_output, paths.native_run_dir)
        results_path = paths.native_run_dir / "results.json"
        if not results_path.is_file():
            raise RuntimeError(f"{job['job_id']}: orphan output has no results.json")
        results = json.loads(results_path.read_text(encoding="utf-8"))
        summary = _summarize_tau3_results(results)
        if summary["status"] != "COMPLETED":
            raise RuntimeError(f"{job['job_id']}: orphan output is not completed")
        simulations = list(results.get("simulations") or [])
        if len(simulations) != 1 or str(simulations[0].get("task_id")) != case_id:
            raise RuntimeError(f"{job['job_id']}: simulation identity mismatch")
        statuses = []
        for status_path in paths.native_run_dir.rglob("sim_status.json"):
            statuses.append(json.loads(status_path.read_text(encoding="utf-8")).get("status"))
        if not statuses or any(value != "used" for value in statuses):
            raise RuntimeError(f"{job['job_id']}: sim_status is not final/used")
        if paths.environment_path.exists():
            environment_hash = sha256_file(paths.environment_path)
        else:
            _, environment_hash = write_environment_snapshot(
                target=target, job=job, output_path=paths.environment_path
            )
        llm_path, _ = write_llm_call_logs(
            events=_tau3_llm_events(paths.native_run_dir),
            job=job,
            context=context,
            output_dir=paths.llm_dir,
        )
        descriptors = _tau3_artifacts(paths, summary["has_native_reward"]) + default_adapter_artifacts(paths)
        _, manifest_path, manifest_sha = build_artifact_manifest(
            job=job,
            context=context,
            target=target,
            descriptors=descriptors,
            producer_command=str(item.execution_plan["runner_command"]),
            started_at=STARTED_AT,
            output_path=paths.artifact_manifest_path,
            environment_hash=environment_hash,
        )
        native_files = [path for path in paths.native_run_dir.rglob("*") if path.is_file()]
        ended_at = datetime.fromtimestamp(
            max(path.stat().st_mtime for path in native_files), timezone.utc
        ).isoformat()
        raw_run, raw_run_path = build_raw_run(
            job=job,
            target=target,
            artifact_manifest_path=manifest_path,
            artifact_manifest_sha256=manifest_sha,
            raw_run_path=paths.raw_run_path,
            started_at=STARTED_AT,
            ended_at=ended_at,
            status=summary["status"],
            diagnostic_status=summary["diagnostic_status"],
            appendix_failure_class=summary["appendix_failure_class"],
            native_label=summary["native_label"],
            native_score=summary["native_score"],
            episode_ids=summary["episode_ids"],
            llm_calls_log_path=llm_path,
        )
        row = {
            "job_id": job["job_id"],
            "case_unit_id": case_id,
            "agent_id": job["agent_id"],
            "status": raw_run["status"],
            "native_score": raw_run["native_score"],
            "started_at_source": "supervisor events.jsonl",
            "ended_at_source": "latest preserved native artifact mtime",
            "adapter_stdout_stderr_recovered": False,
            "native_run_sha256": sha256_path(paths.native_run_dir),
            "artifact_manifest_sha256": manifest_sha,
            "raw_run_sha256": sha256_file(raw_run_path),
            "disposition": "accepted_first_native_attempt_after_controller_transport_loss",
        }
        audit_rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    audit_path = repo_root() / "monitoring" / "orphan_ingest_acceptance.json"
    audit_path.write_text(
        json.dumps(
            {
                "schema_version": "tau3_orphan_ingest_acceptance/v1",
                "status": "PASS",
                "rows": audit_rows,
                "formal_note": "Native first attempts were preserved; adapter stdout/stderr and exact controller end timestamps were unavailable after PTY loss.",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
