#!/usr/bin/env python3
"""Run the frozen MiniWoB remaining-22 cohort with gated concurrency ramping."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import shlex
from typing import Any, Mapping, Sequence

from evidence_system.adapters.miniwob_remote_receipt import inventory as remote_inventory
from evidence_system.adapters.runtime import (
    build_job_paths,
    remote_job_result_dir,
    run_remote_blind_command,
)
from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator.jobs import (
    PlannedJob,
    execute_planned_jobs,
    plan_smoke_jobs,
    resolve_infra_target,
)


NAMESPACE = "miniwob_remaining22_bg0143_vps2_20260719_v1"
MANIFEST = "experiments/appendix/miniwob_remaining22_vps2_20260719_manifest.yaml"
BUNDLE = "experiments/evidence_contracts/source_bundles/miniwob_remaining22_vps2_20260719_case_units_source_bundle.json"
CONTRACTS = "experiments/evidence_contracts/locked/miniwob_remaining22_bg0143_v1/checklists"
INFRA = "configs/miniwob_browsergym_0_14_3_vps2_20260719_execution.locked.yaml"
AGENTS = "configs/miniwob_browsergym_0_14_3_vps2_20260719_agents.locked.yaml"
EXPERIMENT_LOCK = "experiments/evidence_contracts/runtime_locks/miniwob_remaining22_vps2_20260719_experiment_lock.json"
JOBS = f"results/namespaces/{NAMESPACE}/jobs"
CONTROL = f"results/namespaces/{NAMESPACE}/campaign_control"
AGENT_IDS = ("Agent A", "Agent B", "Agent C")
RAMP = (1, 2, 4, 6, 8, 10)
EXPECTED_NATIVE = (
    "job.json",
    "source_bundle_entry.json",
    "worker_config.json",
    "run_summary.json",
    "artifact_manifest.json",
    "task_context.json",
    "native_evaluator_input.json",
    "native_evaluator_output.json",
    "task_artifacts/reset_info.json",
    "task_artifacts/task_state_initial.json",
    "task_artifacts/validation_initial.json",
    "task_artifacts/policy_workflow.json",
    "task_artifacts/task_state_final.json",
    "task_artifacts/validation_final.json",
    "task_artifacts/task_info_final.json",
    "task_artifacts/chat_messages_final.json",
    "trajectory/steps.json",
    "remote_tree_receipt.json",
)


def _mapping(path: Path) -> dict[str, Any]:
    loaded = load_json_or_yaml(path)
    if not isinstance(loaded, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return dict(loaded)


def _formalize(item: PlannedJob, target: Any) -> PlannedJob:
    output_dir = remote_job_result_dir(target, item.job)
    job_id = str(item.job["job_id"])
    original = str(item.execution_plan["runner_command"])
    seal = (
        f"PYTHONPATH={shlex.quote(target.remote_workdir + '/src')} "
        f"{shlex.quote(str(target.benchmark_config['python_bin']))} "
        "-m evidence_system.adapters.miniwob_remote_receipt "
        f"--output-dir {shlex.quote(output_dir)} --job-id {shlex.quote(job_id)}"
    )
    watchdog_seconds = 1800
    pid_file = f"/tmp/miniwob-vps2-{sha256_object(job_id)[:20]}.pid"
    inner = shlex.quote(f"{original} && {seal}")
    wrapped = (
        "set -e; "
        f"rm -f {shlex.quote(pid_file)}; "
        f"setsid timeout --signal=TERM --kill-after=30s {watchdog_seconds}s bash -lc {inner} & "
        "miniwob_worker_pid=$!; "
        f"printf '%s\\n' \"$miniwob_worker_pid\" > {shlex.quote(pid_file)}; "
        "set +e; wait \"$miniwob_worker_pid\"; miniwob_worker_rc=$?; set -e; "
        f"rm -f {shlex.quote(pid_file)}; exit \"$miniwob_worker_rc\""
    )
    plan = dict(item.execution_plan)
    plan["runner_command"] = wrapped
    plan["formal_worker_control"] = {
        "timeout_seconds": 1860,
        "remote_watchdog_seconds": watchdog_seconds,
        "transient_retry_attempts": 1,
        "remote_pid_file": pid_file,
        "remote_timeout_command": "timeout --signal=TERM --kill-after=30s",
        "remote_process_group": "setsid",
        "retry_on_timeout_or_ssh_loss": False,
        "support_files_pre_synced_and_locked": True,
        "artifact_fetch_timeout_seconds": 600,
    }
    return replace(item, execution_plan=plan)


def _audit_artifact_manifest(path: Path) -> int:
    payload = _mapping(path)
    verified = 0
    for artifact in list(payload.get("artifacts") or []):
        if not isinstance(artifact, Mapping):
            raise RuntimeError(f"non-mapping artifact entry: {path}")
        artifact_path = resolve_repo_path(str(artifact.get("path") or ""))
        if not artifact_path.exists():
            raise RuntimeError(f"declared artifact missing: {artifact_path}")
        actual_hash = sha256_path(artifact_path)
        if actual_hash != artifact.get("sha256"):
            raise RuntimeError(f"artifact hash mismatch: {artifact_path}")
        if artifact_path.is_file():
            size = artifact_path.stat().st_size
        else:
            size = sum(candidate.stat().st_size for candidate in artifact_path.rglob("*") if candidate.is_file())
        if size != artifact.get("size_bytes"):
            raise RuntimeError(f"artifact size mismatch: {artifact_path}")
        verified += 1
    return verified


def _audit_job(item: PlannedJob, result: Mapping[str, Any]) -> dict[str, Any]:
    if result.get("status") not in {"completed", "skipped_completed"}:
        raise RuntimeError(f"{item.job['job_id']}: non-completed execution: {result.get('status')}")
    paths = build_job_paths(item.job)
    for relative in EXPECTED_NATIVE:
        if not (paths.native_run_dir / relative).is_file():
            raise RuntimeError(f"{item.job['job_id']}: missing native artifact {relative}")
    summary = _mapping(paths.native_run_dir / "run_summary.json")
    raw_run = _mapping(paths.raw_run_path)
    evaluator = _mapping(paths.native_run_dir / "native_evaluator_output.json")
    validation = _mapping(paths.native_run_dir / "task_artifacts/validation_final.json")
    steps = list(_mapping(paths.native_run_dir / "trajectory/steps.json") if False else json.loads((paths.native_run_dir / "trajectory/steps.json").read_text(encoding="utf-8")))
    if summary.get("status") != "completed" or summary.get("close_error"):
        raise RuntimeError(f"{item.job['job_id']}: worker did not close normally")
    if raw_run.get("status") != "COMPLETED" or raw_run.get("diagnostic_status") != "completed" or raw_run.get("appendix_failure_class") != "none":
        raise RuntimeError(f"{item.job['job_id']}: controller classified the run as non-completed")
    for key in ("reward", "done", "message", "info"):
        if evaluator.get(key) != validation.get(key):
            raise RuntimeError(f"{item.job['job_id']}: official evaluator mismatch for {key}")
    success = bool(evaluator.get("done")) and float(evaluator.get("reward") or 0.0) >= 1.0
    if bool(summary.get("success")) != success:
        raise RuntimeError(f"{item.job['job_id']}: success derivation mismatch")
    expected_label = "success" if success else "fail"
    if raw_run.get("native_label") != expected_label or float(raw_run.get("native_score")) != float(success):
        raise RuntimeError(f"{item.job['job_id']}: native label/score mismatch")
    if int(summary.get("step_count") or 0) != len(steps):
        raise RuntimeError(f"{item.job['job_id']}: step count mismatch")
    calls = sorted((paths.native_run_dir / "openrouter_calls").glob("call-*.json"))
    observations = sorted((paths.native_run_dir / "trajectory/observations").glob("*.json"))
    html = sorted((paths.native_run_dir / "browser_artifacts/page_html").glob("*.html"))
    screenshots = sorted((paths.native_run_dir / "browser_artifacts/screenshots").glob("*.png"))
    screenshot_errors = sorted((paths.native_run_dir / "browser_artifacts/screenshots").glob("*.error.json"))
    if len(calls) != len(steps) or len(observations) != len(steps) + 1 or len(html) != len(steps) + 1:
        raise RuntimeError(f"{item.job['job_id']}: trajectory cardinality mismatch")
    if len(screenshots) + len(screenshot_errors) != len(steps) + 1:
        raise RuntimeError(f"{item.job['job_id']}: screenshot cardinality mismatch")
    recordings = [path for path in (paths.native_run_dir / "browser_artifacts/recordings").rglob("*.webm") if path.stat().st_size > 0]
    if not recordings:
        raise RuntimeError(f"{item.job['job_id']}: no non-empty BrowserGym recording")
    receipt = _mapping(paths.native_run_dir / "remote_tree_receipt.json")
    local_inventory = remote_inventory(paths.native_run_dir)
    if receipt.get("status") != "sealed" or receipt.get("job_id") != item.job["job_id"] or receipt.get("inventory") != local_inventory or receipt.get("inventory_sha256") != sha256_object(local_inventory):
        raise RuntimeError(f"{item.job['job_id']}: remote/local tree receipt mismatch")
    manifest_count = _audit_artifact_manifest(paths.artifact_manifest_path)
    return {
        "job_id": item.job["job_id"],
        "case_unit_id": item.job["case_unit_id"],
        "agent_id": item.job["agent_id"],
        "seed": item.job["seed"],
        "native_label": expected_label,
        "step_count": len(steps),
        "openrouter_call_count": len(calls),
        "recording_count": len(recordings),
        "remote_inventory_sha256": receipt["inventory_sha256"],
        "controller_artifact_count_verified": manifest_count,
    }


def _health(target: Any, control_dir: Path, label: str) -> dict[str, Any]:
    command = (
        "set -e; "
        "curl -fsS http://127.0.0.1:8787/miniwob/click-test.html >/dev/null; "
        "test $(df -Pk / | awk 'NR==2 {print $4}') -gt 20971520; "
        "test $(awk '/MemAvailable/ {print $2}' /proc/meminfo) -gt 2097152; "
        "printf 'status=ok\\n'; nproc; awk '/MemAvailable/ {print $2}' /proc/meminfo; df -Pk / | awk 'NR==2 {print $4}'"
    )
    completed = run_remote_blind_command(target, command, timeout_seconds=30, transient_retry_attempts=1)
    output_path = control_dir / f"health-{label}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(completed.stdout or "", encoding="utf-8")
    if completed.returncode != 0 or not (completed.stdout or "").startswith("status=ok\n"):
        raise RuntimeError(f"remote health gate failed at {label}: {completed.stderr}")
    return {"label": label, "returncode": completed.returncode, "output_sha256": sha256_file(output_path)}


def _verify_deployed_runtime(target: Any) -> dict[str, Any]:
    lock = _mapping(resolve_repo_path(EXPERIMENT_LOCK))
    expected = dict(lock.get("runtime_code_sha256") or {})
    if lock.get("lock_status") != "locked" or not expected:
        raise RuntimeError("derived experiment lock is not current")
    for path, digest in expected.items():
        if sha256_file(resolve_repo_path(path)) != digest:
            raise RuntimeError(f"local locked runtime code drift: {path}")
    remote_paths = [f"{target.remote_workdir}/{path}" for path in expected]
    command = "sha256sum " + " ".join(shlex.quote(path) for path in remote_paths)
    completed = run_remote_blind_command(target, command, timeout_seconds=30, transient_retry_attempts=1)
    if completed.returncode != 0:
        raise RuntimeError(f"remote runtime code hashing failed: {completed.stderr}")
    observed: dict[str, str] = {}
    for line in (completed.stdout or "").splitlines():
        digest, remote_path = line.split(maxsplit=1)
        remote_path = remote_path.lstrip("*")
        relative = Path(remote_path).relative_to(Path(target.remote_workdir)).as_posix()
        observed[relative] = digest
    if observed != expected:
        raise RuntimeError("remote runtime code differs from the derived experiment lock")
    return {"experiment_lock_sha256": sha256_file(resolve_repo_path(EXPERIMENT_LOCK)), "runtime_code_sha256": observed}


def _stage_chunks(items: Sequence[PlannedJob]) -> list[tuple[int, list[PlannedJob]]]:
    chunks: list[tuple[int, list[PlannedJob]]] = []
    cursor = 0
    for workers in RAMP[:-1]:
        chunks.append((workers, list(items[cursor : cursor + workers])))
        cursor += workers
    while cursor < len(items):
        chunk = list(items[cursor : cursor + RAMP[-1]])
        chunks.append((RAMP[-1], chunk))
        cursor += len(chunk)
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-stage", type=int, default=1)
    args = parser.parse_args()
    infra_payload = _mapping(resolve_repo_path(INFRA))
    target = resolve_infra_target("miniwob", infra_payload)
    planned: list[PlannedJob] = []
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
    identities = {(item.job["case_unit_id"], item.job["agent_id"]) for item in planned}
    if len(planned) != 66 or len(identities) != 66:
        raise RuntimeError("formal plan is not exactly 22 cases x 3 agents")
    by_case: dict[str, set[int]] = {}
    for item in planned:
        by_case.setdefault(str(item.job["case_unit_id"]), set()).add(int(item.job["seed"]))
    if any(len(seeds) != 1 for seeds in by_case.values()):
        raise RuntimeError("agents do not share the same per-case seed")
    formal = [_formalize(item, target) for item in planned]
    control_dir = resolve_repo_path(CONTROL)
    control_dir.mkdir(parents=True, exist_ok=True)
    preflight_path = control_dir / "preflight_receipt.json"
    preflight = _mapping(preflight_path)
    if (
        preflight.get("status") != "ok"
        or preflight.get("formal_slot_used") is not False
        or preflight.get("remote_local_inventory_verified") is not True
    ):
        raise RuntimeError("the non-formal MiniWoB VPS2 preflight is not accepted")
    deployed_runtime = _verify_deployed_runtime(target)
    campaign = {
        "schema_version": "miniwob_vps2_campaign/v1",
        "status": "running",
        "started_at": utc_now_iso(),
        "namespace": NAMESPACE,
        "manifest_sha256": sha256_file(resolve_repo_path(MANIFEST)),
        "infra_sha256": sha256_file(resolve_repo_path(INFRA)),
        "agents_sha256": sha256_file(resolve_repo_path(AGENTS)),
        "planned_slots": 66,
        "ramp": list(RAMP),
        "preflight_receipt_path": str(preflight_path.relative_to(resolve_repo_path('.'))),
        "preflight_receipt_sha256": sha256_file(preflight_path),
        "deployed_runtime": deployed_runtime,
        "stages": [],
    }
    write_json(control_dir / "campaign.json", campaign)
    chunks = _stage_chunks(formal)
    for stage_index, (workers, batch) in enumerate(chunks, start=1):
        if stage_index < args.start_stage:
            continue
        before = _health(target, control_dir, f"stage-{stage_index:02d}-before")
        progress: list[dict[str, Any]] = []
        executed = execute_planned_jobs(
            batch,
            manifest_path=MANIFEST,
            source_bundle_path=BUNDLE,
            infra_config_path=INFRA,
            agents_config_path=AGENTS,
            max_workers=workers,
            progress_callback=lambda item, result, done, total: progress.append(
                {"job_id": item.job["job_id"], "status": result.get("status"), "done": done, "total": total}
            ),
            fail_fast_on_noncompleted=True,
            skip_completed=True,
            retry_no_response_attempts=0,
            continue_on_error=False,
        )
        audits = [_audit_job(executed_item.planned, executed_item.execution_result) for executed_item in executed]
        after = _health(target, control_dir, f"stage-{stage_index:02d}-after")
        receipt = {
            "schema_version": "miniwob_concurrency_promotion_receipt/v1",
            "status": "promoted",
            "stage_index": stage_index,
            "authorized_workers": workers,
            "batch_size": len(batch),
            "completed_at": utc_now_iso(),
            "health_before": before,
            "health_after": after,
            "progress": progress,
            "audits": audits,
            "infra_excluded_count": 0,
            "official_evaluator_output_verified": True,
            "remote_local_tree_hash_verified": True,
            "controller_artifact_hashes_verified": True,
        }
        receipt_path = control_dir / f"stage-{stage_index:02d}-promotion.json"
        write_json(receipt_path, receipt)
        campaign["stages"].append({"path": str(receipt_path.relative_to(resolve_repo_path('.'))), "sha256": sha256_file(receipt_path), "workers": workers, "batch_size": len(batch)})
        write_json(control_dir / "campaign.json", campaign)
    campaign["status"] = "completed"
    campaign["completed_at"] = utc_now_iso()
    campaign["completed_slots"] = sum(int(stage["batch_size"]) for stage in campaign["stages"])
    if campaign["completed_slots"] != 66:
        raise RuntimeError(f"campaign completed slot count differs: {campaign['completed_slots']}")
    write_json(control_dir / "campaign.json", campaign)
    print(json.dumps(campaign, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
