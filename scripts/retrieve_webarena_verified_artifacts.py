#!/usr/bin/env python3
"""Resumably retrieve sealed WebArena artifacts and verify every manifest hash."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shutil
import shlex
import threading
from typing import Any, Mapping, Sequence

from evidence_system.adapters.runtime import (
    _run_subprocess,
    _ssh_target,
    _ssh_transport,
    job_result_relative_dir,
    run_remote_blind_command,
)
from evidence_system.adapters.webarena_remote_retention import PERSISTENT_RESULTS_ROOT
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.orchestrator.webarena_verified_run_control import (
    DEFAULT_JOBS_INDEX,
    _remote_audit_target,
    load_full_jobs,
)
from evidence_system.webarena_sites import load_site_lock
from evidence_system.orchestrator.webarena_verified_full import DEFAULT_SITE_LOCK
from evidence_system.orchestrator.webarena_verified_full import DEFAULT_REMOTE_WORKDIR


def _load_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"{label} is missing or unsafe: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object: {path}")
    return value


def _remote_adapter_root(job: Mapping[str, Any]) -> str:
    relative = job_result_relative_dir(job)
    return str(PERSISTENT_RESULTS_ROOT.joinpath(*relative.parts[1:], "adapter"))


def _discover_remote_metadata(
    jobs: Sequence[Mapping[str, Any]],
    *,
    ssh_key: str,
    site_lock: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Read one receipt-only schedule envelope per VPS, never task evidence."""

    by_agent: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        by_agent.setdefault(str(job["agent_id"]), []).append(dict(job))
    metadata: list[dict[str, Any]] = []
    remote_index = (
        f"{DEFAULT_REMOTE_WORKDIR}/experiments/step20/webarena_verified/"
        "jobs/full/index.json"
    )
    for agent_id, lane in sorted(by_agent.items()):
        target = _remote_audit_target(
            lane[0],
            ssh_key_path=ssh_key,
            site_lock=site_lock,
        )
        command = (
            f"cd {shlex.quote(DEFAULT_REMOTE_WORKDIR)} && "
            f"PYTHONPATH={shlex.quote(f'{DEFAULT_REMOTE_WORKDIR}/src')} "
            f"{shlex.quote(target.runner_command)} -m "
            "evidence_system.adapters.webarena_remote_retention verify-schedule "
            f"--jobs-index {shlex.quote(remote_index)} "
            f"--server-id {shlex.quote(target.machine_id)} --receipt-only"
        )
        completed = run_remote_blind_command(
            target,
            command,
            timeout_seconds=1800,
            maximum_stdout_bytes=4_194_304,
            maximum_stderr_bytes=4096,
        )
        if completed.returncode != 0 or completed.stderr:
            raise RuntimeError(f"remote schedule verification failed: {agent_id}")
        payload = json.loads(completed.stdout or "{}")
        audits = payload.get("audits") if isinstance(payload, dict) else None
        if (
            payload.get("status") != "pass"
            or not isinstance(audits, list)
            or len(audits) != len(lane)
        ):
            raise RuntimeError(f"remote schedule envelope is incomplete: {agent_id}")
        lane_by_slot = {str(job["record_slot_id"]): job for job in lane}
        for audit in audits:
            if not isinstance(audit, Mapping) or audit.get("state") != "canonical_reusable":
                continue
            slot_id = str(audit.get("record_slot_id") or "")
            job = lane_by_slot.get(slot_id)
            size = audit.get("artifact_total_size_bytes")
            if (
                job is None
                or isinstance(size, bool)
                or not isinstance(size, int)
                or size < 0
            ):
                raise RuntimeError(f"invalid canonical audit envelope: {agent_id}")
            metadata.append({"job": job, "artifact_size_bytes": size})
    return metadata


def _verify_download(root: Path, metadata: Mapping[str, Any]) -> None:
    job = dict(metadata["job"])
    downloaded_manifest = root / "remote_artifact_manifest.json"
    downloaded_slot = root / "remote_slot_acceptance.json"
    downloaded_security = root / "remote_security_acceptance.json"
    slot = _load_object(downloaded_slot, "downloaded slot receipt")
    security = _load_object(downloaded_security, "downloaded security receipt")
    if (
        slot.get("record_slot_id") != job.get("record_slot_id")
        or slot.get("job_binding_sha256") != sha256_object(job)
        or slot.get("remote_artifact_manifest_sha256") != sha256_file(downloaded_manifest)
        or slot.get("remote_security_acceptance_sha256")
        != sha256_file(downloaded_security)
        or dict(security.get("scan") or {}).get("finding_count") != 0
        or dict(security.get("scan") or {}).get("gold_finding_count") != 0
    ):
        raise RuntimeError(f"downloaded receipt binding failed: {job['record_slot_id']}")
    manifest = _load_object(
        downloaded_manifest, "downloaded artifact manifest"
    )
    if (
        manifest.get("status") != "pass"
        or manifest.get("job_binding_sha256") != sha256_object(job)
        or manifest.get("record_slot_id") != job.get("record_slot_id")
    ):
        raise RuntimeError(f"downloaded manifest binding failed: {job['record_slot_id']}")
    for entry in list(manifest["files"]):
        relative_value = str(
            entry.get("relative_path") or entry.get("path") or ""
        )
        relative = Path(relative_value)
        if not relative_value or relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"unsafe manifest path: {job['record_slot_id']}")
        path = root / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != entry.get("size_bytes")
            or sha256_file(path) != entry.get("sha256")
        ):
            raise RuntimeError(
                f"downloaded artifact hash failed: {job['record_slot_id']}:{relative}"
            )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument("--jobs-index", default=str(DEFAULT_JOBS_INDEX))
    parser.add_argument("--agent", action="append", choices=("Agent A", "Agent B", "Agent C"))
    parser.add_argument("--task-id", action="append", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    destination = Path(args.destination).expanduser().resolve()
    if not destination.is_absolute():
        raise RuntimeError("destination must resolve to an absolute path")
    jobs, _index, _index_path = load_full_jobs(args.jobs_index)
    selected_agents = set(args.agent or ())
    selected_tasks = set(args.task_id or ())
    site_lock = load_site_lock(resolve_repo_path(DEFAULT_SITE_LOCK))
    discovered = _discover_remote_metadata(
        jobs,
        ssh_key=args.ssh_key,
        site_lock=site_lock,
    )
    metadata = [
        item
        for item in discovered
        if (
            not selected_agents
            or dict(item["job"]).get("agent_id") in selected_agents
        )
        and (
            not selected_tasks
            or int(dict(item["job"])["task_id"]) in selected_tasks
        )
    ]
    required = sum(int(item["artifact_size_bytes"]) for item in metadata)
    required_with_reserve = int(required * 1.2) + 5 * 1024**3
    destination.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(destination).free
    plan = {
        "sealed_slot_count": len(metadata),
        "artifact_size_bytes": required,
        "required_free_bytes_with_reserve": required_with_reserve,
        "destination_free_bytes": free,
        "destination": str(destination),
    }
    print(json.dumps(plan, indent=2, sort_keys=True))
    if args.dry_run:
        return 0
    if not metadata:
        raise RuntimeError("no sealed security-pass slots match the selection")
    if free < required_with_reserve:
        raise RuntimeError("destination does not have the required free-space reserve")

    by_agent: dict[str, list[dict[str, Any]]] = {}
    for item in metadata:
        by_agent.setdefault(str(dict(item["job"])["agent_id"]), []).append(item)
    completed = 0
    completed_lock = threading.Lock()

    def retrieve_lane(lane: Sequence[Mapping[str, Any]]) -> int:
        nonlocal completed
        lane_count = 0
        for item in lane:
            job = dict(item["job"])
            target = _remote_audit_target(
                job,
                ssh_key_path=args.ssh_key,
                site_lock=site_lock,
            )
            local_root = destination / str(job["agent_id"]).replace(" ", "_") / str(
                job["record_slot_id"]
            ) / "adapter"
            local_root.mkdir(parents=True, exist_ok=True)
            remote_root = _remote_adapter_root(job)
            _run_subprocess(
                [
                    "rsync",
                    "-az",
                    "--partial",
                    "-e",
                    _ssh_transport(target),
                    f"{_ssh_target(target)}:{remote_root.rstrip('/')}/",
                    f"{local_root}/",
                ],
                timeout_seconds=None,
                transient_retry_attempts=4,
            )
            _verify_download(local_root, item)
            lane_count += 1
            with completed_lock:
                completed += 1
                observed_completed = completed
            print(
                json.dumps(
                    {
                        "record_slot_id": job["record_slot_id"],
                        "status": "verified",
                        "completed": observed_completed,
                        "total": len(metadata),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        return lane_count

    with ThreadPoolExecutor(max_workers=max(1, len(by_agent))) as pool:
        futures = [pool.submit(retrieve_lane, lane) for lane in by_agent.values()]
        retrieved = sum(future.result() for future in as_completed(futures))
    if retrieved != len(metadata):
        raise RuntimeError("artifact retrieval ended with an incomplete slot count")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
