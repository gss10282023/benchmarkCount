#!/usr/bin/env python3
"""Read-only VPS resource monitor for resumed tau3 remaining-14 execution."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import time


NAMESPACE = "tau3-retail-remaining14-vps-20260716"

REMOTE_PROBE = r'''
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

namespace = "tau3-retail-remaining14-vps-20260716"
mem = {}
for line in Path("/proc/meminfo").read_text().splitlines():
    key, value = line.split(":", 1)
    mem[key] = int(value.strip().split()[0])

try:
    loads = [float(part) for part in Path("/proc/loadavg").read_text().split()[:3]]
except Exception:
    loads = []

disk_root = Path("/root/revised_agent_benchmark_paper_package")
disk = shutil.disk_usage(disk_root if disk_root.exists() else "/root")
stat = subprocess.run(
    ["df", "-Pi", str(disk_root if disk_root.exists() else Path("/root"))],
    text=True, capture_output=True, check=False,
)
inode = {}
parts = stat.stdout.splitlines()[-1].split() if stat.stdout.splitlines() else []
if len(parts) >= 6:
    inode = {
        "inode_total": int(parts[1]),
        "inode_used": int(parts[2]),
        "inode_available": int(parts[3]),
        "inode_used_pct": int(parts[4].rstrip("%")),
    }

ps = subprocess.run(
    ["ps", "-eo", "pid=,etimes=,pcpu=,rss=,args="],
    text=True, capture_output=True, check=False,
)
processes = []
for line in ps.stdout.splitlines():
    if "tau2 run" not in line or "--domain retail" not in line or namespace not in line:
        continue
    if "python3 -c" in line:
        continue
    match = re.match(r"\s*(\d+)\s+(\d+)\s+([0-9.]+)\s+(\d+)\s+(.*)", line)
    if not match:
        continue
    pid, elapsed, cpu, rss, command = match.groups()
    task = re.search(r"--task-ids\s+(\S+)", command)
    save = re.search(r"--save-to\s+(\S+)", command)
    save_to = save.group(1).strip("'\"") if save else None
    processes.append({
        "pid": int(pid),
        "elapsed_seconds": int(elapsed),
        "cpu_pct": float(cpu),
        "rss_kb": int(rss),
        "task_id": task.group(1).strip("'\"") if task else None,
        "job_id": Path(save_to).name if save_to else None,
        "process_kind": "uv_wrapper" if "uv run tau2 run" in command else "tau2_child",
    })

job_ids = sorted({p["job_id"] for p in processes if p["job_id"]})
oom = subprocess.run(
    ["bash", "-lc", "dmesg --level=err,crit,alert,emerg 2>/dev/null | grep -ciE 'out of memory|oom-kill|killed process' || true"],
    text=True, capture_output=True, check=False,
).stdout.strip()

print(json.dumps({
    "remote_epoch": int(time.time()),
    "load_1": loads[0] if len(loads) > 0 else None,
    "load_5": loads[1] if len(loads) > 1 else None,
    "load_15": loads[2] if len(loads) > 2 else None,
    "mem_total_kb": mem.get("MemTotal", 0),
    "mem_available_kb": mem.get("MemAvailable", 0),
    "mem_available_pct": round(100 * mem.get("MemAvailable", 0) / max(1, mem.get("MemTotal", 1)), 2),
    "swap_total_kb": mem.get("SwapTotal", 0),
    "swap_used_kb": mem.get("SwapTotal", 0) - mem.get("SwapFree", 0),
    "disk_total_bytes": disk.total,
    "disk_available_bytes": disk.free,
    "disk_used_pct": round(100 * disk.used / max(1, disk.total), 2),
    **inode,
    "oom_kill_count": int(oom or 0),
    "tau2_process_count": len(job_ids),
    "tau2_all_count": len(processes),
    "tau2_job_ids": job_ids,
    "tau2_task_ids": sorted({p["task_id"] for p in processes if p["task_id"]}),
    "tau2_cpu_pct_sum": round(sum(p["cpu_pct"] for p in processes), 2),
    "tau2_rss_kb_sum": sum(p["rss_kb"] for p in processes),
    "tau2_processes": processes,
}, sort_keys=True))
'''


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    for _ in range(3):
        try:
            return dict(json.loads(path.read_text(encoding="utf-8")))
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.1)
    return {}


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def local_supervisor_count() -> int:
    completed = subprocess.run(
        ["ps", "-axo", "pid=,args="],
        text=True, capture_output=True, check=False,
    )
    count = 0
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        try:
            tokens = shlex.split(parts[1])
        except ValueError:
            continue
        if not tokens:
            continue
        executable = Path(tokens[0]).name.lower()
        if executable.startswith("python") and any(
            Path(token).name == "run_tau3_remaining14_supervisor.py" for token in tokens[1:]
        ):
            count += 1
    return count


def local_screen_count() -> int:
    completed = subprocess.run(
        ["screen", "-ls"], text=True, capture_output=True, check=False,
    )
    return sum(".tau3_rem14_resume" in line for line in completed.stdout.splitlines())


def probe(host: str, key_path: str, port: int) -> tuple[dict | None, str, float]:
    started = time.monotonic()
    remote_command = "python3 -c " + shlex.quote(REMOTE_PROBE)
    completed = subprocess.run(
        [
            "ssh", "-i", key_path, "-p", str(port),
            "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/tmp/codex_tau3_known_hosts",
            "-o", "ConnectTimeout=12", host, remote_command,
        ],
        text=True, capture_output=True, check=False, timeout=25,
    )
    elapsed = round(time.monotonic() - started, 3)
    if completed.returncode != 0:
        return None, completed.stderr.strip()[-1000:], elapsed
    try:
        return dict(json.loads(completed.stdout)), "", elapsed
    except json.JSONDecodeError as exc:
        return None, f"invalid_probe_json:{exc}; stdout_tail={completed.stdout[-500:]!r}", elapsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller", type=Path, required=True)
    parser.add_argument("--host", default="root@45.76.20.117")
    parser.add_argument("--key-path", default="/Users/gss/.ssh/id_ed25519")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--interval", type=float, default=30.0)
    args = parser.parse_args()

    monitoring = args.controller / "monitoring"
    output = monitoring / "monitor_resource_resume.jsonl"
    sequence = sum(1 for _ in output.open(encoding="utf-8")) if output.exists() else 0
    while True:
        cycle_started = time.monotonic()
        sequence += 1
        progress = load_json(monitoring / "progress.json")
        summary = load_json(monitoring / "supervisor_summary.json")
        try:
            remote, diagnostic, elapsed = probe(args.host, args.key_path, args.port)
        except subprocess.TimeoutExpired:
            remote, diagnostic, elapsed = None, "ssh_probe_timeout", 25.0

        anomalies = []
        if remote is None:
            anomalies.append("ssh_probe_failed")
        else:
            if int(remote.get("oom_kill_count") or 0) > 0:
                anomalies.append("oom_observed")
            if float(remote.get("mem_available_pct") or 100) < 20:
                anomalies.append("low_memory")
            if int(remote.get("disk_available_bytes") or 0) < 50 * 1024**3:
                anomalies.append("low_disk")
            if float(remote.get("load_1") or 0) > 8:
                anomalies.append("high_load")
            if int(remote.get("tau2_process_count") or 0) > 2:
                anomalies.append("concurrency_exceeded")

        record = {
            "schema_version": "tau3_resource_monitor_resume/v1",
            "timestamp": utc_now(),
            "sequence": sequence,
            "namespace": NAMESPACE,
            "supervisor": {
                "process_count": local_supervisor_count(),
                "screen_session_count": local_screen_count(),
                "planned_slots": progress.get("planned_slots"),
                "completed_unique_slots": progress.get("completed_unique_slots"),
                "currently_active": progress.get("currently_active"),
                "unresolved_count": len(progress.get("unresolved_job_ids") or []),
                "summary_status": summary.get("status"),
            },
            "ssh": {"ok": remote is not None, "elapsed_seconds": elapsed, "diagnostic": diagnostic},
            "remote": remote,
            "anomalies": anomalies,
        }
        append_jsonl(output, record)
        remote_jobs = (remote or {}).get("tau2_job_ids") or []
        print(
            f"{record['timestamp']} seq={sequence} complete={progress.get('completed_unique_slots')} "
            f"active={progress.get('currently_active')} supervisor={record['supervisor']['process_count']} "
            f"remote_jobs={','.join(remote_jobs) or '-'} anomalies={','.join(anomalies) or '-'}",
            flush=True,
        )
        if progress.get("completed_unique_slots") == 42 and not remote_jobs:
            return 0
        if summary.get("status") in {"complete", "incomplete"} and not remote_jobs:
            return 0
        time.sleep(max(0.0, args.interval - (time.monotonic() - cycle_started)))


if __name__ == "__main__":
    raise SystemExit(main())
