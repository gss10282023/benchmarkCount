#!/usr/bin/env python3
"""Append-only resumed artifact acceptance monitor.

This monitor never changes benchmark results or process state.  It re-audits
the first 28 terminal slots and then audits newly materialized Agent C slots.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any

import artifact_monitor as base


SAMPLES = base.ROOT / "monitoring" / "monitor_artifact_resume.jsonl"
ANOMALIES = base.ROOT / "monitoring" / "monitor_artifact_resume_anomalies.jsonl"
STATE = base.ROOT / "monitoring" / "monitor_artifact_resume_state.json"


def append(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def previously_audited() -> dict[str, str | None]:
    seen: dict[str, str | None] = {}
    if not SAMPLES.exists():
        return seen
    for line in SAMPLES.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("job_id"):
            seen[str(row["job_id"])] = row.get("artifact_manifest_sha256")
    return seen


def anomaly_keys() -> set[str]:
    return base.prior_keys(ANOMALIES, "dedupe_key")


def write_state(
    expected: dict[str, dict[str, Any]],
    terminal_present: set[str],
) -> dict[str, Any]:
    latest: dict[str, dict[str, Any]] = {}
    if SAMPLES.exists():
        for line in SAMPLES.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("job_id") in expected:
                latest[str(row["job_id"])] = row
    present_latest = {
        job_id: row for job_id, row in latest.items() if job_id in terminal_present
    }
    state = {
        "schema_version": "tau3_remaining14_artifact_resume_state/v1",
        "updated_at": base.now(),
        "namespace": base.NAMESPACE,
        "expected_slots": 42,
        "audited_terminal_slots": len(terminal_present & set(expected)),
        "passed": sum(row.get("status") == "PASS" for row in present_latest.values()),
        "failed": sum(row.get("status") == "FAIL" for row in present_latest.values()),
        "unseen": sorted(set(expected) - terminal_present),
        "historically_audited_slots": len(latest),
        "read_only_monitor": True,
    }
    base.write_json_atomic(STATE, state)
    return state


def main() -> int:
    expected = base.load_expected_jobs()
    audited_hashes = previously_audited()
    keys = anomaly_keys()

    structural: list[tuple[str, Any, Any]] = []
    if set(expected) != base.expected_job_ids():
        structural.append(("expected_job_set_mismatch", sorted(base.expected_job_ids()), sorted(expected)))
    slots = [str(job.get("record_slot_id")) for job in expected.values()]
    if len(expected) != 42:
        structural.append(("expected_job_count_mismatch", 42, len(expected)))
    if len(set(slots)) != 42:
        structural.append(("record_slot_uniqueness_failure", 42, len(set(slots))))
    for signal, wanted, observed in structural:
        key = f"resume-global:{signal}"
        if key in keys:
            continue
        append(ANOMALIES, {
            "schema_version": "tau3_remaining14_artifact_resume_anomaly/v1",
            "timestamp": base.now(), "monitor_role": "artifact_monitor_resume",
            "namespace": base.NAMESPACE, "job_id": None, "severity": "error",
            "category": "denominator", "dedupe_key": key, "signal": signal,
            "source_path": base.relative(base.JOBS_ROOT), "expected": wanted,
            "observed": observed, "action_taken": "recorded_only_run_not_interrupted",
        })
        keys.add(key)

    last_heartbeat = 0.0
    while True:
        actual = {
            path.name for path in base.RESULT_ROOT.iterdir() if path.is_dir()
        } if base.RESULT_ROOT.exists() else set()
        for extra in sorted(actual - set(expected)):
            key = f"resume-global:unexpected_result_job:{extra}"
            if key not in keys:
                append(ANOMALIES, {
                    "schema_version": "tau3_remaining14_artifact_resume_anomaly/v1",
                    "timestamp": base.now(), "monitor_role": "artifact_monitor_resume",
                    "namespace": base.NAMESPACE, "job_id": extra, "severity": "error",
                    "category": "denominator", "dedupe_key": key,
                    "signal": "unexpected_result_job",
                    "source_path": base.relative(base.RESULT_ROOT / extra),
                    "expected": "one of the fixed 42 jobs", "observed": extra,
                    "action_taken": "recorded_only_run_not_interrupted",
                })
                keys.add(key)

        added = 0
        terminal_present: set[str] = set()
        for job_id, job in sorted(expected.items()):
            adapter = base.RESULT_ROOT / job_id / "adapter"
            required = (
                adapter / "raw_run.json", adapter / "artifact_manifest.json",
                adapter / "environment.json", adapter / "native_run" / "results.json",
                adapter / "llm_calls" / "calls.jsonl",
            )
            if not all(path.exists() for path in required):
                continue
            terminal_present.add(job_id)
            current_manifest_hash = base.sha256_file(adapter / "artifact_manifest.json")
            if audited_hashes.get(job_id) == current_manifest_hash:
                continue
            sample, issues = base.audit_job(job, adapter)
            sample = {
                **sample,
                "schema_version": "tau3_remaining14_artifact_resume/v1",
                "monitor_role": "artifact_monitor_resume",
                "read_only_reaudit": True,
            }
            append(SAMPLES, sample)
            for issue in issues:
                # A single validation code may apply to multiple concrete
                # artifacts (for example stdout.log and stderr.log).  Keep
                # each affected pointer in the append-only anomaly ledger.
                key = (
                    f"resume:{issue['dedupe_key']}:{issue.get('source_path')}:"
                    f"{issue.get('expected')}:{issue.get('observed')}"
                )
                if key in keys:
                    continue
                append(ANOMALIES, {
                    **issue,
                    "schema_version": "tau3_remaining14_artifact_resume_anomaly/v1",
                    "monitor_role": "artifact_monitor_resume",
                    "dedupe_key": key,
                })
                keys.add(key)
            audited_hashes[job_id] = current_manifest_hash
            added += 1
            print(
                f"{base.now()} artifact_resume job={job_id} status={sample['status']} "
                f"reward={sample['native_reward']} errors={sample['error_count']}",
                flush=True,
            )

        state = write_state(expected, terminal_present)
        current = time.monotonic()
        if added or current - last_heartbeat >= 120:
            print(
                f"{base.now()} artifact_resume audited={state['audited_terminal_slots']}/42 "
                f"pass={state['passed']} fail={state['failed']}",
                flush=True,
            )
            last_heartbeat = current
        if state["audited_terminal_slots"] >= 42:
            break
        time.sleep(15)

    terminal_present = {
        job_id for job_id in expected
        if all(path.exists() for path in (
            base.RESULT_ROOT / job_id / "adapter" / "raw_run.json",
            base.RESULT_ROOT / job_id / "adapter" / "artifact_manifest.json",
            base.RESULT_ROOT / job_id / "adapter" / "environment.json",
            base.RESULT_ROOT / job_id / "adapter" / "native_run" / "results.json",
            base.RESULT_ROOT / job_id / "adapter" / "llm_calls" / "calls.jsonl",
        ))
    }
    state = write_state(expected, terminal_present)
    print(
        f"{base.now()} artifact_resume complete audited=42 "
        f"pass={state['passed']} fail={state['failed']}",
        flush=True,
    )
    return 0 if not structural and state["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
