#!/usr/bin/env python3
"""Read-only health, artifact-audit, and progress summaries for WebArena."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
from typing import Any, Mapping

from evidence_system.adapters.runtime import run_remote_blind_command
from evidence_system.core.paths import resolve_repo_path
from evidence_system.orchestrator.webarena_verified_full import EXPECTED_AGENT_IDS
from evidence_system.orchestrator.webarena_verified_run_control import (
    DEFAULT_JOBS_INDEX,
    audit_remote_schedule,
    load_full_jobs,
)
from evidence_system.webarena_sites import load_site_lock


DEFAULT_KEY = Path("/srv/webarena-controller/secrets/id_ed25519")
DEFAULT_STATE = Path("/srv/webarena-controller/state")
DEFAULT_SITE_LOCK = Path("configs/webarena_verified_sites.lock.json")
RUNTIME_ROOT = Path("/run/webarena-controller-watch")
MIN_MEMORY_AVAILABLE_KIB = 2 * 1024 * 1024
RESERVED_STORAGE_BYTES = 20 * 1024**3
P95_ARTIFACT_BYTES = 70 * 1024**2
IMMEDIATE_CODES = {
    "credential_or_billing_failure",
    "active_secret_scan_unavailable",
    "artifact_hash_validation_failed",
    "agent_input_security_scan_failed",
    "runtime_security_scan_failed",
    "persistent_path_validation_failed",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(agent_id: str) -> str:
    return agent_id.lower().replace(" ", "_")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(dict(value), handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _lock(mode: str) -> Any:
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    handle = (RUNTIME_ROOT / f"{mode}.lock").open("a+", encoding="ascii")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return handle


def _controller_active() -> bool:
    observed = subprocess.run(
        ["systemctl", "is-active", "--quiet", "webarena-controller.service"],
        check=False,
        capture_output=True,
    )
    return observed.returncode == 0


def _target_by_agent(*, ssh_key_path: Path) -> tuple[dict[str, Any], dict[str, Any], tuple[dict[str, Any], ...]]:
    jobs, _index, _index_path = load_full_jobs(DEFAULT_JOBS_INDEX)
    site_lock = load_site_lock(resolve_repo_path(DEFAULT_SITE_LOCK))
    targets: dict[str, Any] = {}
    from evidence_system.orchestrator.webarena_verified_run_control import _remote_audit_target

    for agent_id in EXPECTED_AGENT_IDS:
        job = next(item for item in jobs if item.get("agent_id") == agent_id)
        targets[agent_id] = _remote_audit_target(
            job,
            ssh_key_path=ssh_key_path,
            site_lock=site_lock,
        )
    return targets, site_lock, jobs


def _health_command(site_lock: Mapping[str, Any]) -> str:
    sites = list(dict(site_lock.get("sites") or {}).values())
    containers = [str(item["container_name"]) for item in sites]
    lines = [
        "bad_containers=0",
        "bad_sentinels=0",
        "worker_count=$({ pgrep -f '[w]ebarena_official_worker' || true; } | wc -l | tr -d ' ')",
        "lock_present=false",
        f"test -e {shlex.quote(str(site_lock['slot_lock_file']))} && lock_present=true || true",
    ]
    for container in containers:
        quoted = shlex.quote(container)
        lines.append(
            "state=$(docker inspect -f '{{.State.Running}} {{.State.OOMKilled}}' "
            f"{quoted} 2>/dev/null || true); "
            "test \"$state\" = 'true false' || bad_containers=$((bad_containers+1))"
        )
    for site in sites:
        url = shlex.quote(str(site["health_url"]))
        needle = shlex.quote(str(site["health_needle"]))
        lines.append(
            f"if ! body=$(curl -LfsS --max-time 15 {url} 2>/dev/null); then "
            "bad_sentinels=$((bad_sentinels+1)); "
            f"elif ! grep -Fq -- {needle} <<<\"$body\"; then "
            "bad_sentinels=$((bad_sentinels+1)); fi"
        )
    lines.extend(
        [
            "disk_available_bytes=$(df -B1 --output=avail /opt/webarena-results | tail -n 1 | tr -d ' ')",
            "inode_used_percent=$(df --output=ipcent /opt/webarena-results | tail -n 1 | tr -dc '0-9')",
            "memory_available_kib=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)",
            "printf '{\"worker_count\":%s,\"lock_present\":%s,\"bad_container_count\":%s,\"bad_sentinel_count\":%s,\"disk_available_bytes\":%s,\"inode_used_percent\":%s,\"memory_available_kib\":%s}\\n' \"$worker_count\" \"$lock_present\" \"$bad_containers\" \"$bad_sentinels\" \"$disk_available_bytes\" \"$inode_used_percent\" \"$memory_available_kib\"",
        ]
    )
    return "; ".join(lines)


def health(*, key_path: Path, state_root: Path) -> dict[str, Any]:
    targets, site_lock, _jobs = _target_by_agent(ssh_key_path=key_path)
    previous = _load(state_root / "health.json")
    prior_audit = _load(state_root / "audit.json")
    prior_counts = dict(prior_audit.get("counts") or {})
    prior_by_agent = {
        str(item.get("agent_id")): dict(item)
        for item in list(previous.get("agents") or [])
        if isinstance(item, Mapping)
    }
    observations: list[dict[str, Any]] = []
    controller_active = _controller_active()
    for agent_id in EXPECTED_AGENT_IDS:
        target = targets[agent_id]
        remote_returncode: int | None = None
        try:
            completed = run_remote_blind_command(
                target,
                _health_command(site_lock),
                timeout_seconds=120,
                maximum_stdout_bytes=4096,
                maximum_stderr_bytes=4096,
            )
            remote_returncode = completed.returncode
            payload = json.loads(completed.stdout or "{}")
            if completed.returncode != 0 or completed.stderr or not isinstance(payload, Mapping):
                raise RuntimeError("bounded health command failed")
            raw = dict(payload)
            remaining = max(
                0,
                812
                - int(
                    dict(prior_counts.get(agent_id) or {}).get(
                        "canonical_reusable", 0
                    )
                ),
            )
            storage_required = RESERVED_STORAGE_BYTES + remaining * P95_ARTIFACT_BYTES
            unhealthy = bool(
                int(raw.get("bad_container_count", 0))
                or int(raw.get("bad_sentinel_count", 0))
                or int(raw.get("memory_available_kib", 0)) < MIN_MEMORY_AVAILABLE_KIB
                or int(raw.get("disk_available_bytes", 0)) < storage_required
                or int(raw.get("inode_used_percent", 100)) >= 95
            )
            previous_failures = int(prior_by_agent.get(agent_id, {}).get("consecutive_unhealthy_samples", 0))
            observations.append(
                {
                    "agent_id": agent_id,
                    "server_id": target.machine_id,
                    "status": "unhealthy" if unhealthy else "healthy",
                    "consecutive_unhealthy_samples": previous_failures + 1 if unhealthy else 0,
                    "worker_count": int(raw.get("worker_count", 0)),
                    "slot_lock_present": raw.get("lock_present") is True,
                    "bad_container_count": int(raw.get("bad_container_count", 0)),
                    "bad_sentinel_count": int(raw.get("bad_sentinel_count", 0)),
                    "disk_available_bytes": int(raw.get("disk_available_bytes", 0)),
                    "projected_required_bytes": storage_required,
                    "inode_used_percent": int(raw.get("inode_used_percent", 100)),
                    "memory_available_kib": int(raw.get("memory_available_kib", 0)),
                    "verified_over_pinned_ssh": True,
                }
            )
        except Exception as exc:
            previous_failures = int(prior_by_agent.get(agent_id, {}).get("consecutive_unhealthy_samples", 0))
            observations.append(
                {
                    "agent_id": agent_id,
                    "server_id": target.machine_id,
                    "status": "unreachable",
                    "consecutive_unhealthy_samples": previous_failures + 1,
                    "error_code": "remote_health_command_failed",
                    "error_type": type(exc).__name__,
                    "remote_returncode": remote_returncode,
                    "verified_over_pinned_ssh": False,
                }
            )
    result = {
        "schema_version": "webarena_controller_health_watch/v1",
        "generated_at": _now(),
        "controller_active": controller_active,
        "agents": observations,
        "pause_advisory": any(
            int(item.get("consecutive_unhealthy_samples", 0)) >= 3
            for item in observations
        ),
        "monitor_stopped_worker": False,
        "secret_material_recorded": False,
    }
    _write(state_root / "health.json", result)
    return result


def _issue_codes(audit: Any) -> list[str]:
    return sorted(
        {
            str(issue.get("signature") or "unknown")
            for issue in audit.issues
            if isinstance(issue, Mapping)
        }
    )


def audit(*, key_path: Path, state_root: Path) -> dict[str, Any]:
    _targets, site_lock, jobs = _target_by_agent(ssh_key_path=key_path)
    index_path = resolve_repo_path(DEFAULT_JOBS_INDEX)
    audits = audit_remote_schedule(
        jobs,
        jobs_index_path=index_path,
        ssh_key_path=key_path,
        site_lock=site_lock,
        verify_files=False,
    )
    by_slot = {str(item["record_slot_id"]): item for item in jobs}
    previous = _load(state_root / "audit.json")
    previous_slots = {
        str(item.get("record_slot_id")): dict(item)
        for item in list(previous.get("slots") or [])
        if isinstance(item, Mapping)
    }
    streaks = {
        agent_id: int(dict(previous.get("streaks") or {}).get(agent_id, 0))
        for agent_id in EXPECTED_AGENT_IDS
    }
    observations: list[dict[str, Any]] = []
    new_events: list[dict[str, Any]] = []
    for item in audits:
        job = by_slot[item.record_slot_id]
        agent_id = str(job["agent_id"])
        codes = _issue_codes(item)
        observation = {
            "record_slot_id": item.record_slot_id,
            "agent_id": agent_id,
            "task_id": int(job["task_id"]),
            "state": item.state,
            "issue_codes": codes,
        }
        observations.append(observation)
        prior = previous_slots.get(item.record_slot_id)
        changed = prior is not None and (
            prior.get("state") != item.state or prior.get("issue_codes") != codes
        )
        if prior is None:
            continue
        if changed and item.state == "canonical_reusable":
            streaks[agent_id] = 0
            new_events.append({**observation, "event": "canonical"})
        elif changed and codes:
            streaks[agent_id] += 1
            new_events.append({**observation, "event": "case_anomaly"})
    counts: dict[str, dict[str, int]] = {}
    for agent_id in EXPECTED_AGENT_IDS:
        lane = [item for item in observations if item["agent_id"] == agent_id]
        counts[agent_id] = dict(Counter(str(item["state"]) for item in lane))
    immediate = sorted(
        {
            code
            for event in new_events
            for code in event.get("issue_codes", [])
            if code in IMMEDIATE_CODES
        }
    )
    result = {
        "schema_version": "webarena_controller_artifact_watch/v1",
        "generated_at": _now(),
        "baseline_only": not bool(previous_slots),
        "counts": counts,
        "streaks": streaks,
        "new_events": new_events,
        "immediate_issue_codes": immediate,
        "pause_advisory": bool(immediate) or any(value >= 4 for value in streaks.values()),
        "slots": observations,
        "remote_files_rehashed": False,
        "monitor_stopped_worker": False,
        "secret_material_recorded": False,
    }
    _write(state_root / "audit.json", result)
    return result


def summary(*, state_root: Path) -> dict[str, Any]:
    health_payload = _load(state_root / "health.json")
    audit_payload = _load(state_root / "audit.json")
    counts = dict(audit_payload.get("counts") or {})
    canonical = sum(
        int(dict(counts.get(agent_id) or {}).get("canonical_reusable", 0))
        for agent_id in EXPECTED_AGENT_IDS
    )
    result = {
        "schema_version": "webarena_controller_progress_summary/v1",
        "generated_at": _now(),
        "controller_active": _controller_active(),
        "canonical_reusable": canonical,
        "expected": 2436,
        "remaining": 2436 - canonical,
        "per_agent_counts": counts,
        "per_agent_anomaly_streaks": audit_payload.get("streaks") or {},
        "health": [
            {
                "agent_id": item.get("agent_id"),
                "status": item.get("status"),
                "worker_count": item.get("worker_count"),
                "slot_lock_present": item.get("slot_lock_present"),
                "disk_available_bytes": item.get("disk_available_bytes"),
            }
            for item in list(health_payload.get("agents") or [])
            if isinstance(item, Mapping)
        ],
        "pause_advisory": bool(
            health_payload.get("pause_advisory") or audit_payload.get("pause_advisory")
        ),
        "monitor_stopped_worker": False,
        "secret_material_recorded": False,
    }
    _write(state_root / "progress_summary.json", result)
    return result


def _journal_payload(mode: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Keep journals bounded while retaining full private state on disk."""

    if mode != "audit":
        return dict(payload)
    new_events = list(payload.get("new_events") or [])
    return {
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
        "baseline_only": payload.get("baseline_only"),
        "counts": payload.get("counts") or {},
        "streaks": payload.get("streaks") or {},
        "new_event_count": len(new_events),
        "new_events": new_events[:20],
        "new_events_truncated": len(new_events) > 20,
        "immediate_issue_codes": payload.get("immediate_issue_codes") or [],
        "pause_advisory": bool(payload.get("pause_advisory")),
        "monitor_stopped_worker": False,
        "secret_material_recorded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("health", "audit", "summary"))
    parser.add_argument("--ssh-key-path", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()
    with _lock(args.mode):
        if args.mode == "health":
            payload = health(key_path=args.ssh_key_path, state_root=args.state_root)
        elif args.mode == "audit":
            payload = audit(key_path=args.ssh_key_path, state_root=args.state_root)
        else:
            payload = summary(state_root=args.state_root)
    print(
        json.dumps(
            _journal_payload(args.mode, payload),
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
