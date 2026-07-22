#!/usr/bin/env python3
"""Continue-on-error supervisor for the remaining-14 tau3 raw collection."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import threading
import time
import traceback

from evidence_system.adapters.runtime import job_result_relative_dir
from evidence_system.core.paths import repo_root
from evidence_system.orchestrator.jobs import execute_planned_jobs, plan_smoke_jobs


CASES = ("104", "85", "88", "42", "44", "55", "63", "43", "96", "4", "48", "110", "9", "24")
AGENTS = ("Agent A", "Agent B", "Agent C")
MODELS = {
    "Agent A": "openrouter/openai/gpt-5.4",
    "Agent B": "openrouter/anthropic/claude-opus-4.7",
    "Agent C": "openrouter/deepseek/deepseek-v4-pro",
}
NAMESPACE = "tau3-retail-remaining14-vps-20260716"
MANIFEST = "experiments/appendix/tau3_retail_remaining14_vultr_run_manifest.yaml"
SOURCE_BUNDLE = "experiments/evidence_contracts/source_bundles/tau3_retail_remaining14_source_bundle.json"
CONTRACTS_DIR = "experiments/evidence_contracts/prelock_empty"
INFRA = "configs/tau3_remaining14_vultr.json"
AGENTS_CONFIG = "configs/agents.yaml"
JOBS_DIR = f"results/jobs/full/namespaces/{NAMESPACE}"
MONITOR_DIR = repo_root() / "monitoring"
STATE_PATH = MONITOR_DIR / "progress.json"
EVENTS_PATH = MONITOR_DIR / "events.jsonl"
ANOMALIES_PATH = MONITOR_DIR / "anomalies.jsonl"
PLAN_ACCEPTANCE_PATH = MONITOR_DIR / "plan_acceptance.json"

_lock = threading.Lock()
_active: dict[str, dict[str, object]] = {}
_attempt_counts: Counter[str] = Counter()
_completed: dict[str, dict[str, object]] = {}
_last_failures: dict[str, dict[str, object]] = {}
_attempted_slots: set[str] = set()
_max_active = 0


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def state_payload() -> dict[str, object]:
    return {
        "schema_version": "tau3_remaining14_progress/v1",
        "updated_at": now(),
        "namespace": NAMESPACE,
        "planned_slots": 42,
        "attempted_unique_slots": len(_attempted_slots),
        "completed_unique_slots": len(_completed),
        "currently_active": len(_active),
        "max_active_observed": _max_active,
        "active": dict(sorted(_active.items())),
        "completed_job_ids": sorted(_completed),
        "unresolved_job_ids": sorted(set(_last_failures) - set(_completed)),
        "attempt_counts": dict(sorted(_attempt_counts.items())),
    }


def publish_state() -> None:
    write_json_atomic(STATE_PATH, state_payload())


def plan_all() -> dict[str, list[object]]:
    batches: dict[str, list[object]] = {}
    for agent in AGENTS:
        batches[agent] = plan_smoke_jobs(
            domain="tau3_retail",
            phase="full",
            experiment_type="appendix",
            case_count=14,
            agent_ids=[agent],
            seed=107,
            manifest_path=MANIFEST,
            source_bundle_path=SOURCE_BUNDLE,
            contracts_dir=CONTRACTS_DIR,
            infra_config_path=INFRA,
            agents_config_path=AGENTS_CONFIG,
            jobs_dir=JOBS_DIR,
            result_namespace=NAMESPACE,
        )
    return batches


def audit_plan(batches: dict[str, list[object]]) -> dict[str, object]:
    all_items = [item for agent in AGENTS for item in batches[agent]]
    errors: list[str] = []
    if len(all_items) != 42:
        errors.append(f"expected 42 jobs, found {len(all_items)}")
    jobs = [item.job for item in all_items]
    if len({job["job_id"] for job in jobs}) != 42:
        errors.append("job ids are not unique")
    if len({job["record_slot_id"] for job in jobs}) != 42:
        errors.append("record slot ids are not unique")
    for agent in AGENTS:
        items = batches[agent]
        if [item.job["case_unit_id"] for item in items] != list(CASES):
            errors.append(f"{agent}: case order mismatch")
        for index, item in enumerate(items):
            job = item.job
            command = str(item.execution_plan.get("runner_command") or "")
            expected_seed = 107 + index
            if job["seed"] != expected_seed:
                errors.append(f"{job['job_id']}: seed {job['seed']} != {expected_seed}")
            if job["agent_id"] != agent or job["task_id"] != job["case_unit_id"]:
                errors.append(f"{job['job_id']}: identity mismatch")
            if job.get("result_namespace") != NAMESPACE:
                errors.append(f"{job['job_id']}: namespace mismatch")
            if job.get("artifact_contract") != {"required_artifacts": []}:
                errors.append(f"{job['job_id']}: prelock fallback contract changed")
            if item.execution_plan.get("status") != "runnable":
                errors.append(f"{job['job_id']}: execution plan is not runnable")
            if re.search(r"<[A-Z][A-Z0-9_]*>", command):
                errors.append(f"{job['job_id']}: unresolved command placeholder")
            required_tokens = (
                "/root/.local/bin/uv run tau2 run",
                f"--task-ids {job['task_id']}",
                f"--seed {expected_seed}",
                "--max-concurrency 1",
                MODELS[agent],
                f"results/namespaces/{NAMESPACE}/full/tau3_retail/{job['job_id']}",
            )
            for token in required_tokens:
                if token not in command:
                    errors.append(f"{job['job_id']}: runner command missing {token!r}")
    payload = {
        "schema_version": "tau3_remaining14_plan_acceptance/v1",
        "created_at": now(),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "planned_jobs": len(all_items),
        "unique_record_slots": len({job["record_slot_id"] for job in jobs}),
        "case_order": list(CASES),
        "agents": list(AGENTS),
        "seed_range": [107, 120],
        "max_workers": 2,
        "contract_mode": "generated_fallback_prelock",
        "formal_scoring_eligible": False,
        "result_namespace": NAMESPACE,
    }
    write_json_atomic(PLAN_ACCEPTANCE_PATH, payload)
    if errors:
        raise RuntimeError("strict plan audit failed: " + "; ".join(errors))
    return payload


def snapshot_failed_attempt(item: object, attempt: int) -> str | None:
    source = repo_root() / job_result_relative_dir(item.job) / "adapter"
    if not source.exists():
        return None
    destination = MONITOR_DIR / "failed_attempt_snapshots" / item.job["job_id"] / f"attempt_{attempt:02d}"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return str(destination.relative_to(repo_root()))


def execute_one(item: object, attempt: int) -> tuple[object, bool, dict[str, object]]:
    global _max_active
    job = item.job
    job_id = str(job["job_id"])
    slot = threading.current_thread().name.rsplit("_", 1)[-1]
    started = time.monotonic()
    with _lock:
        _attempt_counts[job_id] += 1
        _attempted_slots.add(str(job["record_slot_id"]))
        _active[job_id] = {
            "worker_slot": slot,
            "agent_id": job["agent_id"],
            "case_unit_id": job["case_unit_id"],
            "attempt": attempt,
            "started_at": now(),
        }
        _max_active = max(_max_active, len(_active))
        append_jsonl(EVENTS_PATH, {
            "timestamp": now(), "event": "attempt_started", "worker_slot": slot,
            "job_id": job_id, "agent_id": job["agent_id"], "case_unit_id": job["case_unit_id"],
            "attempt": attempt,
        })
        publish_state()
    try:
        executed = execute_planned_jobs(
            [item],
            manifest_path=MANIFEST,
            source_bundle_path=SOURCE_BUNDLE,
            infra_config_path=INFRA,
            agents_config_path=AGENTS_CONFIG,
            max_workers=1,
            fail_fast_on_noncompleted=False,
            skip_completed=True,
            retry_no_response_attempts=0,
        )
        result = dict(executed[0].execution_result)
        status = str(result.get("status") or "unknown").lower()
        success = status in {"completed", "skipped_completed"}
        error_message = None if success else f"noncompleted status={status}"
    except Exception as exc:
        result = {"status": "exception", "exception_type": type(exc).__name__, "message": str(exc)}
        status = "exception"
        success = False
        error_message = f"{type(exc).__name__}: {exc}"
        trace_path = MONITOR_DIR / "tracebacks" / job_id / f"attempt_{attempt:02d}.txt"
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(traceback.format_exc(), encoding="utf-8")
        result["traceback_path"] = str(trace_path.relative_to(repo_root()))
    duration = round(time.monotonic() - started, 3)
    with _lock:
        _active.pop(job_id, None)
        event = {
            "timestamp": now(), "event": "attempt_finished", "worker_slot": slot,
            "job_id": job_id, "agent_id": job["agent_id"], "case_unit_id": job["case_unit_id"],
            "attempt": attempt, "duration_seconds": duration, "status": status,
        }
        append_jsonl(EVENTS_PATH, event)
        if success:
            _completed[job_id] = {**event, "execution_result": result}
            _last_failures.pop(job_id, None)
        else:
            snapshot = snapshot_failed_attempt(item, attempt)
            anomaly = {
                "timestamp": now(),
                "monitor_role": "supervisor",
                "worker_slot": slot,
                "job_id": job_id,
                "agent_id": job["agent_id"],
                "case_id": job["case_unit_id"],
                "attempt": attempt,
                "severity": "error",
                "category": "runner_or_api",
                "signal": error_message,
                "source_path": snapshot,
                "expected": "completed",
                "observed": status,
                "resolution": "pending_retry_after_queue",
                "action_taken": "recorded_and_continued",
            }
            append_jsonl(ANOMALIES_PATH, anomaly)
            _last_failures[job_id] = anomaly
        publish_state()
    print(
        f"{now()} slot={slot} job={job_id} case={job['case_unit_id']} "
        f"agent={job['agent_id']} attempt={attempt} status={status} duration={duration}s",
        flush=True,
    )
    return item, success, result


def run_batch(items: list[object], max_attempts: int) -> None:
    pending = list(items)
    for attempt in range(1, max_attempts + 1):
        if not pending:
            return
        if attempt > 1:
            delay = min(60, 10 * (attempt - 1))
            print(f"{now()} retry_round={attempt} pending={len(pending)} backoff={delay}s", flush=True)
            time.sleep(delay)
        failures: list[object] = []
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="tau3-slot") as executor:
            futures = {executor.submit(execute_one, item, attempt): item for item in pending}
            for future in as_completed(futures):
                item, success, _ = future.result()
                if not success:
                    failures.append(item)
        pending = failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)
    batches = plan_all()
    acceptance = audit_plan(batches)
    print(json.dumps(acceptance, ensure_ascii=False, sort_keys=True), flush=True)
    if args.plan_only:
        return 0
    for batch_index, agent in enumerate(AGENTS, start=1):
        print(f"{now()} batch={batch_index}/3 agent={agent} jobs=14 start", flush=True)
        run_batch(batches[agent], max_attempts=args.max_attempts)
        print(f"{now()} batch={batch_index}/3 agent={agent} done", flush=True)
    with _lock:
        final = state_payload()
        final["status"] = "complete" if len(_completed) == 42 else "incomplete"
        final["finished_at"] = now()
        write_json_atomic(MONITOR_DIR / "supervisor_summary.json", final)
    print(json.dumps(final, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if len(_completed) == 42 else 2


if __name__ == "__main__":
    raise SystemExit(main())
