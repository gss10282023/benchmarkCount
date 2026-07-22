#!/usr/bin/env python3
"""Rebuild tau3 manifests from the single used simulation after internal retries."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

from evidence_system.adapters.runtime import (
    build_artifact_manifest,
    build_job_paths,
    build_smoke_execution_context,
    default_adapter_artifacts,
    file_descriptor,
)
from evidence_system.contracts.common import load_mapping, write_json
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import validate_object
from evidence_system.orchestrator.jobs import plan_smoke_jobs, resolve_infra_target


NAMESPACE = "tau3-retail-remaining14-vps-20260716"
MANIFEST = "experiments/appendix/tau3_retail_remaining14_vultr_run_manifest.yaml"
SOURCE_BUNDLE = "experiments/evidence_contracts/source_bundles/tau3_retail_remaining14_source_bundle.json"
CONTRACTS_DIR = "experiments/evidence_contracts/prelock_empty"
INFRA = "configs/tau3_remaining14_vultr.json"
AGENTS_CONFIG = "configs/agents.yaml"
JOBS_DIR = f"results/jobs/full/namespaces/{NAMESPACE}"


def descriptor(path: Path, artifact_type: str, *, evaluator: bool = False):
    return file_descriptor(
        path,
        artifact_type=artifact_type,
        producer_role="official_evaluator" if evaluator else "official_runner",
        producer_name="tau2-runner",
        producer_version="tau2-bench",
        official_runner=True,
        official_evaluator=evaluator,
        evaluator_name="tau2 reward evaluator" if evaluator else None,
        evaluator_version="tau2-bench" if evaluator else None,
        artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if evaluator else (),
    )


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
    archive_root = repo_root() / "monitoring" / "pre_retry_manifest_repair"
    diagnostic_root = repo_root() / "monitoring" / "internal_retry_diagnostics"
    rows = []
    for case_id in case_ids:
        item = by_case[case_id]
        job = item.job
        paths = build_job_paths(job)
        old_manifest = json.loads(paths.artifact_manifest_path.read_text(encoding="utf-8"))
        old_raw_run = json.loads(paths.raw_run_path.read_text(encoding="utf-8"))
        job_archive = archive_root / job["job_id"]
        job_archive.mkdir(parents=True, exist_ok=True)
        shutil.copy2(paths.artifact_manifest_path, job_archive / "artifact_manifest.json")
        shutil.copy2(paths.raw_run_path, job_archive / "raw_run.json")
        status_rows = []
        for status_path in sorted(paths.native_run_dir.rglob("sim_status.json")):
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            status_rows.append((status_path.parent, status_path, payload))
        used = [row for row in status_rows if row[2].get("status") == "used"]
        failed = [row for row in status_rows if row[2].get("status") == "failed"]
        if len(used) != 1 or not failed:
            raise RuntimeError(
                f"{job['job_id']}: expected exactly one used simulation and at least one failed retry"
            )
        used_dir, used_status, _ = used[0]
        results_path = paths.native_run_dir / "results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        simulations = list(results.get("simulations") or [])
        if len(simulations) != 1 or str(simulations[0].get("task_id")) != case_id:
            raise RuntimeError(f"{job['job_id']}: results identity mismatch")
        reward = (simulations[0].get("reward_info") or {}).get("reward")
        if not isinstance(reward, (int, float)) or isinstance(reward, bool):
            raise RuntimeError(f"{job['job_id']}: results reward is not numeric")
        task_logs = sorted(used_dir.glob("task.log"))
        llm_debug = sorted(used_dir.glob("llm_debug/*.json"))
        if len(task_logs) != 1 or not llm_debug:
            raise RuntimeError(f"{job['job_id']}: used simulation lacks task.log or llm_debug")
        descriptors = [descriptor(results_path, "native_evaluator_output", evaluator=True)]
        descriptors.extend(descriptor(path, "tool_log") for path in task_logs)
        descriptors.append(descriptor(used_status, "post_state"))
        descriptors.extend(descriptor(path, "trace") for path in llm_debug)
        descriptors.extend(default_adapter_artifacts(paths))
        environment_hash = sha256_file(paths.environment_path)
        started_at = str(old_raw_run["started_at"])
        new_manifest, manifest_path, manifest_sha = build_artifact_manifest(
            job=job,
            context=context,
            target=target,
            descriptors=tuple(descriptors),
            producer_command=str(item.execution_plan["runner_command"]),
            started_at=started_at,
            output_path=paths.artifact_manifest_path,
            environment_hash=environment_hash,
        )
        ids = [str(row["artifact_id"]) for row in new_manifest["artifacts"]]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"{job['job_id']}: repaired manifest still has duplicate artifact ids")
        new_raw_run = dict(old_raw_run)
        new_raw_run["artifact_manifest_sha256"] = manifest_sha
        validate_object("raw_run", new_raw_run, raise_on_error=True)
        write_json(paths.raw_run_path, new_raw_run)
        diagnostic_files = []
        for failed_dir, status_path, status_payload in failed:
            for file_path in sorted(path for path in failed_dir.rglob("*") if path.is_file()):
                diagnostic_files.append(
                    {
                        "path": str(file_path.relative_to(repo_root())),
                        "sha256": sha256_file(file_path),
                        "size_bytes": file_path.stat().st_size,
                    }
                )
        diagnostic = {
            "schema_version": "tau3_internal_retry_diagnostic/v1",
            "job_id": job["job_id"],
            "case_unit_id": case_id,
            "agent_id": job["agent_id"],
            "used_simulation_dir": str(used_dir.relative_to(repo_root())),
            "failed_simulation_count": len(failed),
            "failed_statuses": [
                {
                    "path": str(status_path.relative_to(repo_root())),
                    "reason": payload.get("reason"),
                    "error_type": payload.get("error_type"),
                    "error": payload.get("error"),
                }
                for _, status_path, payload in failed
            ],
            "failed_retry_files": diagnostic_files,
            "disposition": "retained_as_diagnostic_native_files_but_excluded_from_decisive_artifact_manifest",
        }
        diagnostic_path = diagnostic_root / job["job_id"] / "diagnostic.json"
        write_json(diagnostic_path, diagnostic)
        row = {
            "job_id": job["job_id"],
            "case_unit_id": case_id,
            "native_reward": float(reward),
            "failed_internal_simulations": len(failed),
            "old_artifact_manifest_sha256": sha256_file(job_archive / "artifact_manifest.json"),
            "new_artifact_manifest_sha256": manifest_sha,
            "old_raw_run_sha256": sha256_file(job_archive / "raw_run.json"),
            "new_raw_run_sha256": sha256_file(paths.raw_run_path),
            "old_artifact_count": len(old_manifest.get("artifacts") or []),
            "new_artifact_count": len(new_manifest.get("artifacts") or []),
            "new_artifact_ids_unique": True,
            "selected_task_log_count": len(task_logs),
            "selected_sim_status_count": 1,
            "diagnostic_path": str(diagnostic_path.relative_to(repo_root())),
            "repair_rule": "manifest only the single sim_status=used simulation; retain failed retries as diagnostic native files",
        }
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    report = {
        "schema_version": "tau3_internal_retry_manifest_repair/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "benchmark_runs_modified": False,
        "native_files_modified": False,
        "rows": rows,
    }
    write_json(repo_root() / "monitoring" / "internal_retry_manifest_repair.json", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
