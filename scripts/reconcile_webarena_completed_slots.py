#!/usr/bin/env python3
"""Seal completed-unsealed WebArena slots without replaying paid runtimes."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shlex
from typing import Any, Mapping, Sequence

from evidence_system.adapters.runtime import (
    SmokeExecutionContext,
    run_remote_blind_command,
)
from evidence_system.adapters.webarena_verified import (
    plan_smoke_execution,
    reconcile_completed_remote_slot,
)
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator.webarena_verified_full import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_MANIFEST,
    DEFAULT_REMOTE_WORKDIR,
    DEFAULT_SITE_LOCK,
    DEFAULT_SOURCE_BUNDLE,
    EXPECTED_SOURCE_SHA256,
)
from evidence_system.orchestrator.webarena_verified_run_control import (
    DEFAULT_JOBS_INDEX,
    _remote_audit_target,
    load_full_jobs,
)
from evidence_system.webarena_sites import load_site_lock


CONFIRMATION = "RECONCILE-COMPLETED-NO-PAID"
PRESERVE_INCOMPLETE_CONFIRMATION = "PRESERVE-INCOMPLETE-NO-RUN-SUMMARY"
FORMAL_NAMESPACE_REMOTE_PREFIX = (
    "/opt/webarena-results/controller-results/namespaces/"
    "webarena_verified_v1_2_3_full_812/"
)


def _remote_lane_audits(
    lane: Sequence[Mapping[str, Any]],
    *,
    ssh_key: str,
    site_lock: Mapping[str, Any],
) -> tuple[Any, list[dict[str, Any]]]:
    target = _remote_audit_target(
        lane[0],
        ssh_key_path=ssh_key,
        site_lock=site_lock,
    )
    remote_index = (
        f"{DEFAULT_REMOTE_WORKDIR}/experiments/step20/webarena_verified/"
        "jobs/full/index.json"
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
        raise RuntimeError(f"remote schedule verification failed: {lane[0]['agent_id']}")
    payload = json.loads(completed.stdout or "{}")
    audits = payload.get("audits") if isinstance(payload, dict) else None
    if (
        payload.get("status") != "pass"
        or not isinstance(audits, list)
        or len(audits) != len(lane)
    ):
        raise RuntimeError(f"remote schedule envelope is incomplete: {lane[0]['agent_id']}")
    return target, [dict(item) for item in audits]


def _require_quiescent(target: Any) -> None:
    command = (
        "count=$({ pgrep -f '[w]ebarena_official_worker' || true; } | wc -l); "
        "lock=0; test ! -e /var/lock/webarena-verified-slot.lock || lock=1; "
        "printf '{\"active_worker_count\":%s,\"slot_lock_present\":%s}\\n' "
        '"$count" "$lock"'
    )
    completed = run_remote_blind_command(
        target,
        command,
        timeout_seconds=60,
        maximum_stdout_bytes=1024,
        maximum_stderr_bytes=1024,
    )
    payload = json.loads(completed.stdout or "{}")
    if (
        completed.returncode != 0
        or completed.stderr
        or payload.get("active_worker_count") != 0
        or payload.get("slot_lock_present") != 0
    ):
        raise RuntimeError(f"VPS is not quiescent: {target.machine_id}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument("--dotenv", default=".env")
    parser.add_argument("--jobs-index", default=str(DEFAULT_JOBS_INDEX))
    parser.add_argument("--agent", action="append", choices=("Agent A", "Agent B", "Agent C"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--confirm", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preserve-incomplete-scaffolds", action="store_true")
    return parser


def _preserved_incomplete_root(audit: Mapping[str, Any]) -> str:
    root = str(audit.get("persistent_adapter_root") or "")
    binding = str(audit.get("job_binding_sha256") or "")
    if (
        not root.startswith(FORMAL_NAMESPACE_REMOTE_PREFIX)
        or not root.endswith("/adapter")
        or len(binding) != 64
        or any(character not in "0123456789abcdef" for character in binding)
    ):
        raise RuntimeError("incomplete scaffold has an unsafe preservation binding")
    return f"{root}.preserved-incomplete-{binding[:16]}"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    jobs, _index, _index_path = load_full_jobs(args.jobs_index)
    selected_agents = set(args.agent or ())
    by_agent: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        if selected_agents and job.get("agent_id") not in selected_agents:
            continue
        by_agent.setdefault(str(job["agent_id"]), []).append(dict(job))
    site_lock = load_site_lock(resolve_repo_path(DEFAULT_SITE_LOCK))

    targets: dict[str, Any] = {}
    candidates: dict[str, list[dict[str, Any]]] = {}
    incomplete_candidates: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for agent_id, lane in sorted(by_agent.items()):
        target, audits = _remote_lane_audits(
            lane,
            ssh_key=args.ssh_key,
            site_lock=site_lock,
        )
        targets[agent_id] = target
        jobs_by_slot = {str(job["record_slot_id"]): job for job in lane}
        candidates[agent_id] = [
            jobs_by_slot[str(audit["record_slot_id"])]
            for audit in audits
            if audit.get("state") == "in_progress"
            and audit.get("runtime_completed_unsealed") is True
        ]
        incomplete_candidates[agent_id] = [
            (jobs_by_slot[str(audit["record_slot_id"])], audit)
            for audit in audits
            if audit.get("state") == "in_progress"
            and audit.get("runtime_completed_unsealed") is not True
            and audit.get("terminal_failure_observed") is not True
        ]

    active_candidates: Mapping[str, Sequence[Any]] = (
        incomplete_candidates if args.preserve_incomplete_scaffolds else candidates
    )
    discovered = sum(len(lane) for lane in active_candidates.values())
    print(
        json.dumps(
            {
                "status": "planned",
                "action": (
                    "preserve_incomplete_scaffolds"
                    if args.preserve_incomplete_scaffolds
                    else "seal_completed_unsealed"
                ),
                "candidate_count": discovered,
                "completed_unsealed_count": (
                    0 if args.preserve_incomplete_scaffolds else discovered
                ),
                "incomplete_scaffold_count": (
                    discovered if args.preserve_incomplete_scaffolds else 0
                ),
                "by_agent": {
                    agent_id: len(lane)
                    for agent_id, lane in sorted(active_candidates.items())
                },
                "first_record_slot_by_agent": {
                    agent_id: (
                        (
                            lane[0][0]["record_slot_id"]
                            if args.preserve_incomplete_scaffolds
                            else lane[0]["record_slot_id"]
                        )
                        if lane
                        else None
                    )
                    for agent_id, lane in sorted(active_candidates.items())
                },
                "paid_runtime_replay": False,
                "remote_artifact_deleted": False,
            },
            sort_keys=True,
        )
    )
    if args.dry_run:
        return 0
    expected_confirmation = (
        PRESERVE_INCOMPLETE_CONFIRMATION
        if args.preserve_incomplete_scaffolds
        else CONFIRMATION
    )
    if args.confirm != expected_confirmation:
        raise RuntimeError(f"exact confirmation is required: {expected_confirmation}")
    for target in targets.values():
        _require_quiescent(target)

    if args.preserve_incomplete_scaffolds:
        remaining = args.limit if args.limit is not None else discovered
        preserved_results: list[dict[str, Any]] = []
        for agent_id, lane in sorted(incomplete_candidates.items()):
            for job, audit in lane:
                if remaining <= 0:
                    break
                remaining -= 1
                source = str(audit["persistent_adapter_root"])
                destination = _preserved_incomplete_root(audit)
                command = (
                    f"test -d {shlex.quote(source)} && "
                    f"test ! -L {shlex.quote(source)} && "
                    f"test ! -e {shlex.quote(destination)} && "
                    f"test ! -e {shlex.quote(source + '/native_run/run_summary.json')} && "
                    f"test ! -e {shlex.quote(source + '/remote_slot_acceptance.json')} && "
                    f"mv -- {shlex.quote(source)} {shlex.quote(destination)}"
                )
                completed = run_remote_blind_command(
                    targets[agent_id],
                    command,
                    timeout_seconds=60,
                    maximum_stdout_bytes=0,
                    maximum_stderr_bytes=1024,
                )
                status = (
                    "preserved"
                    if completed.returncode == 0 and not completed.stderr
                    else "failed"
                )
                row = {
                    "record_slot_id": job["record_slot_id"],
                    "agent_id": agent_id,
                    "status": status,
                    "preserved_remote_root": destination if status == "preserved" else None,
                    "paid_runtime_replayed": False,
                    "remote_artifact_deleted": False,
                }
                preserved_results.append(row)
                print(json.dumps(row, sort_keys=True), flush=True)
        failed_count = sum(row["status"] == "failed" for row in preserved_results)
        print(
            json.dumps(
                {
                    "status": "completed" if failed_count == 0 else "partial",
                    "preserved_count": len(preserved_results) - failed_count,
                    "failed_count": failed_count,
                    "paid_runtime_replayed": False,
                    "remote_artifact_deleted": False,
                },
                sort_keys=True,
            )
        )
        return 0 if failed_count == 0 else 2

    manifest = resolve_repo_path(DEFAULT_MANIFEST)
    source_bundle_path = resolve_repo_path(DEFAULT_SOURCE_BUNDLE)
    agents_config = resolve_repo_path(DEFAULT_AGENTS_CONFIG)
    dotenv = resolve_repo_path(args.dotenv)
    source_bundle = load_json_or_yaml(source_bundle_path)
    if not isinstance(source_bundle, Mapping):
        raise RuntimeError("source bundle is not an object")
    context = SmokeExecutionContext(
        manifest_path=manifest,
        manifest_hash=sha256_file(manifest),
        source_bundle_path=source_bundle_path,
        source_bundle_hash=sha256_file(source_bundle_path),
        official_split_hash=EXPECTED_SOURCE_SHA256,
        agents_config_path=agents_config,
        dotenv_path=dotenv,
    )

    remaining = args.limit if args.limit is not None else discovered
    selected: dict[str, list[dict[str, Any]]] = {}
    for agent_id, lane in sorted(candidates.items()):
        take = max(0, min(len(lane), remaining))
        selected[agent_id] = lane[:take]
        remaining -= take

    def reconcile_lane(agent_id: str) -> list[dict[str, Any]]:
        target = targets[agent_id]
        results: list[dict[str, Any]] = []
        for job in selected[agent_id]:
            try:
                execution_plan = plan_smoke_execution(
                    job,
                    target=target,
                    agents_config_path=str(agents_config),
                    dotenv_path=str(dotenv),
                    source_bundle_path=str(source_bundle_path),
                    source_bundle=dict(source_bundle),
                )
                if execution_plan.get("status") != "runnable":
                    raise RuntimeError("seal_only_plan_blocked")
                result = reconcile_completed_remote_slot(
                    job,
                    target=target,
                    execution_plan=execution_plan,
                    context=context,
                )
                if (
                    result.get("status") != "completed"
                    or result.get("paid_runtime_replayed") is not False
                ):
                    raise RuntimeError("seal_only_result_invalid")
                row = {
                    "record_slot_id": job["record_slot_id"],
                    "agent_id": agent_id,
                    "status": "sealed",
                    "paid_runtime_replayed": False,
                }
            except Exception as exc:
                raw_code = str(exc)
                error_code = (
                    raw_code
                    if raw_code.replace("_", "").isalnum() and len(raw_code) <= 96
                    else type(exc).__name__
                )
                row = {
                    "record_slot_id": job["record_slot_id"],
                    "agent_id": agent_id,
                    "status": "failed",
                    "error_code": error_code,
                    "paid_runtime_replayed": False,
                }
            results.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
        return results

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, len(selected))) as pool:
        futures = {
            pool.submit(reconcile_lane, agent_id): agent_id
            for agent_id in selected
            if selected[agent_id]
        }
        for future in as_completed(futures):
            results.extend(future.result())
    failed_count = sum(row["status"] == "failed" for row in results)
    print(
        json.dumps(
            {
                "status": "completed" if failed_count == 0 else "partial",
                "sealed_count": len(results) - failed_count,
                "failed_count": failed_count,
                "paid_runtime_replayed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
