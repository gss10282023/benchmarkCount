#!/usr/bin/env python3
"""Read-only live remote case/API monitor for the tau3 remaining-14 run."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
from typing import Any


NAMESPACE = "tau3-retail-remaining14-vps-20260716"
REMOTE_REPO = "/root/revised_agent_benchmark_paper_package"
REMOTE_BASE = (
    f"{REMOTE_REPO}/results/namespaces/{NAMESPACE}/full/tau3_retail"
)

REMOTE_PROBE = r'''
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

namespace = sys.argv[1]
base = Path(sys.argv[2])
requested_jobs = set(sys.argv[3:])

processes = []
completed = subprocess.run(
    ["ps", "-eo", "pid=,etimes=,args="],
    text=True,
    capture_output=True,
    check=False,
)
for line in completed.stdout.splitlines():
    if "tau2 run" not in line or "--domain retail" not in line or namespace not in line:
        continue
    match = re.match(r"\s*(\d+)\s+(\d+)\s+(.*)", line)
    if not match:
        continue
    pid, elapsed, command = match.groups()
    task = re.search(r"--task-ids\s+(\S+)", command)
    save_to = re.search(r"--save-to\s+(\S+)", command)
    save_path = save_to.group(1).strip("'\"") if save_to else None
    job_id = Path(save_path).name if save_path else None
    processes.append({
        "pid": int(pid),
        "elapsed_seconds": int(elapsed),
        "task_id": task.group(1).strip("'\"") if task else None,
        "job_id": job_id,
        "save_to": save_path,
    })

rules = {
    "http_auth_or_billing": re.compile(
        r"(?i)(?:HTTP|status(?:_code)?|code)[^\n]{0,40}\b(?:401|402|403)\b|"
        r"unauthori[sz]ed|authentication(?:_error| error)|invalid api key|insufficient (?:credit|balance)"
    ),
    "http_rate_limit": re.compile(
        r"(?i)(?:HTTP|status(?:_code)?|code)[^\n]{0,40}\b429\b|rate.?limit(?:ed|ing| error)"
    ),
    "http_server_error": re.compile(
        r"(?i)(?:HTTP|status(?:_code)?|code)[^\n]{0,40}\b5\d\d\b|service unavailable|bad gateway"
    ),
    "timeout": re.compile(
        r"(?i)TimeoutError|ReadTimeout|ConnectTimeout|request timed out|connection timed out|timed out waiting"
    ),
    "no_response": re.compile(
        r"(?i)No response from model|response content is missing|missing response content|IncompleteRead"
    ),
    "deepseek_empty_message": re.compile(
        r"(?i)empty (?:UserMessage|AssistantMessage)|"
        r"(?:UserMessage|AssistantMessage).{0,120}(?:empty|missing content|must have either content or tool_calls)"
    ),
    "internal_simulation_retry": re.compile(
        r"(?i)(?:retrying|starting).{0,80}(?:simulation|sim_)|simulation.{0,80}(?:retry|attempt)"
    ),
    "traceback": re.compile(r"Traceback \(most recent call last\)"),
    "infrastructure_error": re.compile(r"(?i)infrastructure_error"),
    "model_cost_unmapped": re.compile(r"(?i)This model isn't mapped yet"),
    "missing_reward": re.compile(r"(?i)missing reward|reward_info.+(?:missing|null|none)"),
}

def tail_text(path, limit=524288):
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - limit))
            return handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""

jobs = {}
scan_hits = []
for job_id in sorted(requested_jobs):
    root = base / job_id
    task_logs = sorted(root.rglob("task.log")) if root.exists() else []
    sim_status_files = sorted(root.rglob("sim_status.json")) if root.exists() else []
    debug_files = (
        sorted(
            path for path in root.rglob("*.json")
            if path.parent.name == "llm_debug"
        )
        if root.exists()
        else []
    )
    observed_files = [*task_logs, *sim_status_files, *debug_files]
    total_size = sum(path.stat().st_size for path in observed_files if path.exists())
    latest_mtime = max(
        (path.stat().st_mtime for path in observed_files if path.exists()),
        default=0.0,
    )
    for path in observed_files:
        text = tail_text(path)
        for rule_id, pattern in rules.items():
            count = len(pattern.findall(text))
            if count:
                try:
                    display = str(path.relative_to(base))
                except ValueError:
                    display = str(path)
                scan_hits.append({
                    "job_id": job_id,
                    "rule_id": rule_id,
                    "path": display,
                    "match_count_in_tail": count,
                })

    result_path = root / "results.json"
    result_summary = {
        "exists": result_path.exists(),
        "parse_status": "absent",
        "simulation_count": None,
        "termination_reason": None,
        "has_reward": None,
        "reward": None,
    }
    if result_path.exists():
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            simulations = list(payload.get("simulations") or [])
            simulation = dict(simulations[0] or {}) if simulations else {}
            reward_info = simulation.get("reward_info")
            reward = reward_info.get("reward") if isinstance(reward_info, dict) else None
            result_summary.update({
                "parse_status": "ok",
                "simulation_count": len(simulations),
                "termination_reason": simulation.get("termination_reason"),
                "has_reward": isinstance(reward, (int, float)) and not isinstance(reward, bool),
                "reward": reward if isinstance(reward, (int, float)) else None,
            })
        except Exception as exc:
            result_summary["parse_status"] = type(exc).__name__

    jobs[job_id] = {
        "remote_root_exists": root.exists(),
        "task_log_count": len(task_logs),
        "sim_status_count": len(sim_status_files),
        "llm_debug_count": len(debug_files),
        "observed_size_bytes": total_size,
        "latest_observed_mtime_epoch": latest_mtime,
        "results": result_summary,
    }

meminfo = {}
try:
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        meminfo[key] = int(value.strip().split()[0])
except Exception:
    pass
disk = shutil.disk_usage(base if base.exists() else "/root")
try:
    load = [float(value) for value in Path("/proc/loadavg").read_text().split()[:3]]
except Exception:
    load = []

print(json.dumps({
    "probe_epoch": time.time(),
    "processes": processes,
    "jobs": jobs,
    "scan_hits": scan_hits,
    "resources": {
        "load_average": load,
        "memory_available_mb": round(meminfo.get("MemAvailable", 0) / 1024, 1),
        "swap_free_mb": round(meminfo.get("SwapFree", 0) / 1024, 1),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
    },
}, sort_keys=True))
'''


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_json(path: Path) -> dict[str, Any]:
    for _ in range(3):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return dict(payload)
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.15)
    return {}


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def existing_anomaly_keys(path: Path) -> set[tuple[str, ...]]:
    keys: set[tuple[str, ...]] = set()
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = item.get("dedup_key")
        if isinstance(key, list):
            keys.add(tuple(str(part) for part in key))
    return keys


def remote_probe(
    *, host: str, key_path: str, port: int, active_jobs: list[str]
) -> tuple[dict[str, Any] | None, str | None]:
    remote_command = " ".join(
        [
            "python3",
            "-c",
            shlex.quote(REMOTE_PROBE),
            shlex.quote(NAMESPACE),
            shlex.quote(REMOTE_BASE),
            *(shlex.quote(job_id) for job_id in active_jobs),
        ]
    )
    completed = subprocess.run(
        [
            "ssh",
            "-i",
            key_path,
            "-p",
            str(port),
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ConnectTimeout=12",
            host,
            remote_command,
        ],
        text=True,
        capture_output=True,
        timeout=25,
        check=False,
    )
    if completed.returncode != 0:
        error = (completed.stderr or completed.stdout or "ssh probe failed").strip()
        return None, error[-500:]
    try:
        return dict(json.loads(completed.stdout)), None
    except json.JSONDecodeError as exc:
        return None, f"remote probe returned invalid JSON: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller", type=Path, required=True)
    parser.add_argument("--host", default="root@45.76.20.117")
    parser.add_argument("--key-path", default="/Users/gss/.ssh/id_ed25519")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--observations-name", default="monitor_remote_case.jsonl")
    parser.add_argument("--anomalies-name", default="monitor_remote_case_anomalies.jsonl")
    parser.add_argument("--monitor-role", default="remote_case_api")
    args = parser.parse_args()

    monitor_dir = args.controller / "monitoring"
    progress_path = monitor_dir / "progress.json"
    summary_path = monitor_dir / "supervisor_summary.json"
    observations_path = monitor_dir / args.observations_name
    anomalies_path = monitor_dir / args.anomalies_name
    seen = existing_anomaly_keys(anomalies_path)
    last_signature: dict[tuple[str, int], tuple[int, int, float]] = {}
    last_growth_at: dict[tuple[str, int], float] = {}

    def anomaly(payload: dict[str, Any], dedup_key: tuple[str, ...]) -> bool:
        if dedup_key in seen:
            return False
        seen.add(dedup_key)
        append_jsonl(
            anomalies_path,
            {
                "timestamp": now(),
                "monitor_role": args.monitor_role,
                "namespace": NAMESPACE,
                "dedup_key": list(dedup_key),
                "action_taken": "recorded_only_no_interrupt",
                **payload,
            },
        )
        return True

    while True:
        cycle_started = time.monotonic()
        progress = load_json(progress_path)
        active = dict(progress.get("active") or {})
        active_jobs = sorted(active)
        probe: dict[str, Any] | None
        probe_error: str | None
        try:
            probe, probe_error = remote_probe(
                host=args.host,
                key_path=args.key_path,
                port=args.port,
                active_jobs=active_jobs,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            probe, probe_error = None, f"{type(exc).__name__}: {exc}"

        new_anomalies = 0
        if probe_error:
            if anomaly(
                {
                    "severity": "error",
                    "category": "transport",
                    "signal": "ssh_probe_failed",
                    "observed": probe_error,
                    "expected": "successful read-only SSH probe",
                    "job_id": None,
                },
                ("ssh_probe_failed", probe_error),
            ):
                new_anomalies += 1
        else:
            assert probe is not None
            processes = list(probe.get("processes") or [])
            unique_remote_jobs = {
                str(item.get("job_id"))
                for item in processes
                if item.get("job_id")
            }
            if len(unique_remote_jobs) > 2:
                if anomaly(
                    {
                        "severity": "critical",
                        "category": "resource",
                        "signal": "remote_case_concurrency_exceeded",
                        "observed": len(unique_remote_jobs),
                        "expected": "<=2 unique active benchmark jobs",
                        "job_id": None,
                    },
                    ("remote_concurrency", str(len(unique_remote_jobs))),
                ):
                    new_anomalies += 1

            resources = dict(probe.get("resources") or {})
            if float(resources.get("disk_free_gb") or 0) < 10:
                if anomaly(
                    {
                        "severity": "critical",
                        "category": "resource",
                        "signal": "remote_disk_low",
                        "observed": resources.get("disk_free_gb"),
                        "expected": ">=10 GB free",
                        "job_id": None,
                    },
                    ("remote_disk_low",),
                ):
                    new_anomalies += 1
            if float(resources.get("memory_available_mb") or 0) < 512:
                if anomaly(
                    {
                        "severity": "warning",
                        "category": "resource",
                        "signal": "remote_memory_low",
                        "observed": resources.get("memory_available_mb"),
                        "expected": ">=512 MB available",
                        "job_id": None,
                    },
                    ("remote_memory_low",),
                ):
                    new_anomalies += 1

            for hit in list(probe.get("scan_hits") or []):
                job_id = str(hit.get("job_id") or "unknown")
                attempt = int(dict(active.get(job_id) or {}).get("attempt") or 0)
                rule_id = str(hit.get("rule_id") or "unknown")
                path = str(hit.get("path") or "unknown")
                severity = (
                    "critical"
                    if rule_id == "http_auth_or_billing"
                    else "error"
                    if rule_id in {"traceback", "infrastructure_error", "missing_reward"}
                    else "warning"
                )
                if anomaly(
                    {
                        "severity": severity,
                        "category": "api_or_runner",
                        "signal": rule_id,
                        "job_id": job_id,
                        "attempt": attempt,
                        "source_path": path,
                        "observed": hit.get("match_count_in_tail"),
                        "expected": 0,
                    },
                    (job_id, str(attempt), rule_id, path),
                ):
                    new_anomalies += 1

            remote_jobs = dict(probe.get("jobs") or {})
            monotonic_now = time.monotonic()
            wall_now = datetime.now(timezone.utc)
            for job_id, active_state in active.items():
                state = dict(active_state or {})
                attempt = int(state.get("attempt") or 0)
                key = (job_id, attempt)
                remote_state = dict(remote_jobs.get(job_id) or {})
                signature = (
                    int(remote_state.get("task_log_count") or 0),
                    int(remote_state.get("llm_debug_count") or 0),
                    float(remote_state.get("latest_observed_mtime_epoch") or 0),
                )
                if key not in last_signature or signature != last_signature[key]:
                    last_signature[key] = signature
                    last_growth_at[key] = monotonic_now
                started_at = str(state.get("started_at") or now())
                try:
                    age_seconds = (wall_now - parse_time(started_at)).total_seconds()
                except ValueError:
                    age_seconds = 0
                no_growth_seconds = monotonic_now - last_growth_at.get(key, monotonic_now)
                if age_seconds > 600:
                    if anomaly(
                        {
                            "severity": "warning",
                            "category": "liveness",
                            "signal": "slow_run_over_10m",
                            "job_id": job_id,
                            "attempt": attempt,
                            "observed": round(age_seconds, 1),
                            "expected": "<=600 seconds",
                        },
                        (job_id, str(attempt), "slow_run_over_10m"),
                    ):
                        new_anomalies += 1
                if age_seconds > 900 and no_growth_seconds > 300:
                    if anomaly(
                        {
                            "severity": "error",
                            "category": "liveness",
                            "signal": "stalled_over_15m_no_growth_5m",
                            "job_id": job_id,
                            "attempt": attempt,
                            "observed": {
                                "age_seconds": round(age_seconds, 1),
                                "no_growth_seconds": round(no_growth_seconds, 1),
                            },
                            "expected": "observable artifact growth within 5 minutes",
                        },
                        (job_id, str(attempt), "stalled_over_15m_no_growth_5m"),
                    ):
                        new_anomalies += 1

                result = dict(remote_state.get("results") or {})
                # Tau2 creates results.json before the first simulation finishes.
                # A temporarily empty result is normal while that job still has a
                # live runner process; only flag it after the remote process exits.
                if (
                    result.get("parse_status") == "ok"
                    and result.get("has_reward") is False
                    and job_id not in unique_remote_jobs
                ):
                    if anomaly(
                        {
                            "severity": "error",
                            "category": "runner",
                            "signal": "results_missing_numeric_reward",
                            "job_id": job_id,
                            "attempt": attempt,
                            "source_path": f"{job_id}/results.json",
                            "observed": result,
                            "expected": "one simulation with numeric reward_info.reward",
                        },
                        (job_id, str(attempt), "results_missing_numeric_reward"),
                    ):
                        new_anomalies += 1

        observation = {
            "timestamp": now(),
            "monitor_role": args.monitor_role,
            "namespace": NAMESPACE,
            "planned_slots": progress.get("planned_slots"),
            "attempted_unique_slots": progress.get("attempted_unique_slots"),
            "completed_unique_slots": progress.get("completed_unique_slots"),
            "currently_active": progress.get("currently_active"),
            "active_slots": [
                {"job_id": job_id, **dict(state or {})}
                for job_id, state in sorted(active.items())
            ],
            "remote_probe_status": "error" if probe_error else "ok",
            "remote_probe_error": probe_error,
            "remote": probe,
            "new_anomalies": new_anomalies,
            "action_taken": "read_only_observation",
        }
        append_jsonl(observations_path, observation)

        completed_count = int(progress.get("completed_unique_slots") or 0)
        active_display = ",".join(
            f"slot{dict(state or {}).get('worker_slot')}:{job_id}"
            for job_id, state in sorted(active.items())
        ) or "none"
        print(
            f"{observation['timestamp']} remote_case_monitor "
            f"completed={completed_count}/42 active={active_display} "
            f"probe={observation['remote_probe_status']} new_anomalies={new_anomalies}",
            flush=True,
        )

        summary = load_json(summary_path) if summary_path.exists() else {}
        if completed_count == 42 and summary.get("status") == "complete":
            print(f"{now()} remote_case_monitor terminal=42_complete", flush=True)
            return 0

        elapsed = time.monotonic() - cycle_started
        time.sleep(max(1.0, args.interval - elapsed))


if __name__ == "__main__":
    raise SystemExit(main())
