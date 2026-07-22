#!/usr/bin/env python3
"""Perform one preserved, terminal-slot retry on an otherwise idle fixed lane.

This helper is deliberately narrower than full resume.  It is for a newly
observed benchmark failure while another model lane is still busy: it proves
the selected lane is idle, moves the old terminal evidence aside on that VPS,
and makes exactly one replacement attempt without moving a task across models.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib import import_module
import json
from pathlib import Path
import shlex
import sys
import threading
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.adapters.runtime import run_remote_blind_command  # noqa: E402
from evidence_system.orchestrator.webarena_verified_full import (  # noqa: E402
    DEFAULT_SITE_LOCK,
    EXPECTED_AGENT_IDS,
)
from evidence_system.orchestrator.webarena_verified_full_execution import (  # noqa: E402
    execute_full_schedule,
)
from evidence_system.orchestrator.webarena_verified_run_control import (  # noqa: E402
    CIRCUIT_RECOVERY_CONFIRMATION_PREFIX,
    DEFAULT_CIRCUIT_RECOVERY_RECEIPT,
    DEFAULT_JOBS_INDEX,
    PAID_FULL_CONFIRMATION,
    _atomic_write_json,
    _write_sidecar,
    audit_remote_slot,
    load_materialized_full_plan,
)
from evidence_system.webarena_sites import load_site_lock  # noqa: E402
from scripts.reconcile_webarena_completed_slots import _remote_lane_audits  # noqa: E402


SELECTION_SCHEMA = "webarena_verified_concurrent_terminal_retry_selection/v1"
RECOVERY_SCHEMA = "webarena_verified_circuit_recovery_receipt/v1"
DEFAULT_OUTPUT = Path(
    "results/namespaces/webarena_verified_v1_2_3_full_812/"
    "concurrent_terminal_retry_receipt.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--jobs-index", default=str(DEFAULT_JOBS_INDEX))
    parser.add_argument("--site-lock", default=str(DEFAULT_SITE_LOCK))
    parser.add_argument(
        "--circuit-recovery-receipt",
        default=str(DEFAULT_CIRCUIT_RECOVERY_RECEIPT),
    )
    parser.add_argument("--confirm-paid-full", default="")
    parser.add_argument("--confirm-circuit-recovery", default="")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _repo_file(path_value: str | Path, *, label: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"{label} is missing or unsafe")
    return path


def _sidecar_valid(path: Path) -> bool:
    sidecar = path.with_suffix(f"{path.suffix}.sha256")
    if not sidecar.is_file() or sidecar.is_symlink():
        return False
    try:
        expected = sidecar.read_text(encoding="ascii").split()[0]
    except OSError:
        return False
    from evidence_system.core.hashing import sha256_file

    return len(expected) == 64 and expected == sha256_file(path)


def _load_selection(path_value: str | Path) -> dict[str, tuple[int, ...]]:
    path = _repo_file(path_value, label="concurrent terminal retry selection")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("concurrent terminal retry selection is invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("concurrent terminal retry selection has the wrong schema")
    raw = payload.get("retry_once")
    if payload.get("schema_version") != SELECTION_SCHEMA or not isinstance(raw, Mapping):
        raise RuntimeError("concurrent terminal retry selection has the wrong schema")
    if not raw or not set(raw).issubset(EXPECTED_AGENT_IDS):
        raise RuntimeError("concurrent terminal retry selection has invalid agent IDs")
    selection: dict[str, tuple[int, ...]] = {}
    for agent_id, raw_ids in raw.items():
        if (
            not isinstance(raw_ids, list)
            or not raw_ids
            or any(not isinstance(task_id, int) for task_id in raw_ids)
            or raw_ids != sorted(raw_ids)
            or len(raw_ids) != len(set(raw_ids))
            or any(task_id < 0 or task_id > 811 for task_id in raw_ids)
        ):
            raise RuntimeError(f"terminal retry task IDs are invalid for {agent_id}")
        selection[str(agent_id)] = tuple(raw_ids)
    return selection


def _load_recovery(path_value: str | Path) -> tuple[Mapping[str, Any], str]:
    path = _repo_file(path_value, label="circuit recovery receipt")
    if not _sidecar_valid(path):
        raise RuntimeError("circuit recovery receipt sidecar is invalid")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("circuit recovery receipt is invalid JSON") from exc
    authorization = payload.get("authorization") if isinstance(payload, Mapping) else None
    recovery_id = payload.get("recovery_id") if isinstance(payload, Mapping) else None
    if (
        payload.get("schema_version") != RECOVERY_SCHEMA
        or payload.get("status") != "pass"
        or not isinstance(authorization, Mapping)
        or authorization.get("decision") != "clear_for_exact_resume"
        or not isinstance(recovery_id, str)
        or len(recovery_id) != 64
    ):
        raise RuntimeError("circuit recovery receipt has the wrong schema or status")
    return payload, recovery_id


def _selected_jobs(
    *, plan: Any, selection: Mapping[str, tuple[int, ...]]
) -> dict[str, tuple[dict[str, Any], ...]]:
    selected: dict[str, tuple[dict[str, Any], ...]] = {}
    for agent_id, task_ids in selection.items():
        jobs = tuple(
            dict(job)
            for job in plan.jobs
            if job.get("agent_id") == agent_id and int(job["task_id"]) in task_ids
        )
        if tuple(int(job["task_id"]) for job in jobs) != task_ids:
            raise RuntimeError(f"formal slots are missing for {agent_id}")
        selected[agent_id] = jobs
    return selected


def _assert_lane_quiescent(target: Any) -> None:
    observed = run_remote_blind_command(
        target,
        "count=$({ pgrep -f '[w]ebarena_official_worker' || true; } | wc -l); "
        'test "$count" -eq 0',
        timeout_seconds=60,
        maximum_stdout_bytes=0,
        maximum_stderr_bytes=1024,
    )
    if observed.returncode != 0 or observed.stderr:
        raise RuntimeError(f"selected VPS is not quiescent: {target.machine_id}")


def _preserved_root(audit: Mapping[str, Any]) -> str:
    root = str(audit.get("persistent_adapter_root") or "")
    binding = str(audit.get("job_binding_sha256") or "")
    if (
        not root.endswith("/adapter")
        or len(binding) != 64
        or any(character not in "0123456789abcdef" for character in binding)
    ):
        raise RuntimeError("terminal retry has an unsafe preservation binding")
    return f"{root}.preserved-terminal-rerun-{binding[:16]}"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.dry_run and args.confirm_paid_full != PAID_FULL_CONFIRMATION:
        raise RuntimeError("exact paid-full confirmation is required")
    selection = _load_selection(args.selection)
    recovery, recovery_id = _load_recovery(args.circuit_recovery_receipt)
    if not args.dry_run and args.confirm_circuit_recovery != (
        CIRCUIT_RECOVERY_CONFIRMATION_PREFIX + recovery_id
    ):
        raise RuntimeError("exact circuit-recovery confirmation is required")
    authorized_agents = set(
        dict(recovery["authorization"]).get("new_failure_streak_epoch_agent_ids") or []
    )
    if not set(selection).issubset(authorized_agents):
        raise RuntimeError("recovery receipt does not authorize every selected agent")

    plan = load_materialized_full_plan(index_path=args.jobs_index)
    selected_by_agent = _selected_jobs(plan=plan, selection=selection)
    selected_slots = {
        str(job["record_slot_id"])
        for jobs in selected_by_agent.values()
        for job in jobs
    }
    site_lock = load_site_lock(Path(args.site_lock))

    def audit_lane(agent_id: str) -> tuple[str, Any, list[dict[str, Any]]]:
        lane = [dict(job) for job in plan.jobs if job.get("agent_id") == agent_id]
        target, audits = _remote_lane_audits(
            lane, ssh_key=args.ssh_key, site_lock=site_lock
        )
        return agent_id, target, audits

    targets: dict[str, Any] = {}
    audits_by_slot: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(
        max_workers=len(selection), thread_name_prefix="webarena-terminal-retry-audit"
    ) as pool:
        futures = [pool.submit(audit_lane, agent_id) for agent_id in selection]
        for future in as_completed(futures):
            agent_id, target, audits = future.result()
            targets[agent_id] = target
            audits_by_slot.update(
                {str(audit["record_slot_id"]): audit for audit in audits}
            )
    selected_audits: dict[str, Mapping[str, Any]] = {}
    for slot_id in selected_slots:
        audit = audits_by_slot.get(slot_id)
        if (
            audit is None
            or audit.get("state") != "in_progress"
            or audit.get("terminal_failure_observed") is not True
            or audit.get("runtime_completed_unsealed") is True
        ):
            raise RuntimeError(f"slot is not a terminal retry candidate: {slot_id}")
        selected_audits[slot_id] = audit
    for target in targets.values():
        _assert_lane_quiescent(target)

    planned = {
        "status": "planned",
        "recovery_id": recovery_id,
        "record_slot_ids": sorted(selected_slots),
        "paid_slot_count": len(selected_slots),
        "full_evidence_synced_to_controller": False,
        "concurrent_recovery_policy": "selected-lane-quiescence-plus-live-terminal-audit",
    }
    print(json.dumps(planned, sort_keys=True), flush=True)
    if args.dry_run:
        return 0

    preserved: dict[str, str] = {}
    for slot_id in sorted(selected_slots):
        audit = selected_audits[slot_id]
        root = str(audit["persistent_adapter_root"])
        destination = _preserved_root(audit)
        agent_id = str(audit["record_slot_id"]).rsplit("-agent-", 1)[-1].upper()
        target = targets[f"Agent {agent_id}"]
        command = (
            f"test -d {shlex.quote(root)} && "
            f"test ! -L {shlex.quote(root)} && "
            f"test ! -e {shlex.quote(destination)} && "
            f"test -f {shlex.quote(root + '/native_run/run_summary.json')} && "
            f"test ! -e {shlex.quote(root + '/remote_slot_acceptance.json')} && "
            f"mv -- {shlex.quote(root)} {shlex.quote(destination)}"
        )
        completed = run_remote_blind_command(
            target,
            command,
            timeout_seconds=60,
            maximum_stdout_bytes=0,
            maximum_stderr_bytes=1024,
        )
        if completed.returncode != 0 or completed.stderr:
            raise RuntimeError(f"terminal artifact preservation failed: {slot_id}")
        preserved[slot_id] = destination

    adapter = import_module("evidence_system.adapters.webarena_verified")
    real_planner = getattr(adapter, "plan_smoke_execution")
    real_executor = getattr(adapter, "execute_smoke_job")
    results: list[dict[str, Any]] = []
    results_lock = threading.Lock()

    def record(row: dict[str, Any]) -> None:
        with results_lock:
            results.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    def planner(job: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        if str(job["record_slot_id"]) not in selected_slots:
            return {"status": "runnable", "terminal_retry_skip": True}
        return dict(real_planner(job, **kwargs))

    def executor(
        job: dict[str, Any], *, execution_plan: Mapping[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        if execution_plan.get("terminal_retry_skip") is True:
            return {"status": "completed", "terminal_retry_skip": True}
        slot_id = str(job["record_slot_id"])
        base = {
            "agent_id": str(job["agent_id"]),
            "task_id": int(job["task_id"]),
            "record_slot_id": slot_id,
            "preserved_terminal_artifact_root": preserved[slot_id],
            "paid_runtime_replayed": True,
        }
        try:
            completed = dict(real_executor(job, execution_plan=dict(execution_plan), **kwargs))
            audited = audit_remote_slot(job, ssh_key_path=args.ssh_key, site_lock=site_lock)
            record(
                {
                    **base,
                    "status": (
                        "canonical_reusable"
                        if completed.get("status") == "completed" and audited.reusable
                        else "retry_failed"
                    ),
                    "audit_state": audited.state,
                    "executor_status": str(completed.get("status") or ""),
                }
            )
        except Exception as exc:
            try:
                audited = audit_remote_slot(job, ssh_key_path=args.ssh_key, site_lock=site_lock)
                if audited.reusable:
                    record(
                        {
                            **base,
                            "status": "canonical_reusable",
                            "audit_state": audited.state,
                            "controller_error_type_after_remote_seal": type(exc).__name__,
                        }
                    )
                else:
                    record(
                        {
                            **base,
                            "status": "retry_failed",
                            "audit_state": audited.state,
                            "executor_error_type": type(exc).__name__,
                        }
                    )
            except Exception:
                record(
                    {
                        **base,
                        "status": "retry_failed",
                        "audit_state": "audit_unavailable",
                        "executor_error_type": type(exc).__name__,
                    }
                )
        return {"status": "completed", "terminal_retry_recorded": True}

    execute_full_schedule(
        plan,
        ssh_key_path=args.ssh_key,
        site_lock_path=args.site_lock,
        adapter_planner=planner,
        adapter_executor=executor,
    )
    if len(results) != len(selected_slots):
        raise RuntimeError("terminal retry did not execute every selected slot")
    ordered = sorted(
        results,
        key=lambda row: (EXPECTED_AGENT_IDS.index(str(row["agent_id"])), row["task_id"]),
    )
    canonical = sum(row["status"] == "canonical_reusable" for row in ordered)
    receipt = {
        "schema_version": "webarena_verified_concurrent_terminal_retry/v1",
        "status": "pass" if canonical == len(ordered) else "completed_with_recorded_failures",
        "recovery_id": recovery_id,
        "results": ordered,
        "paid_slot_count": len(ordered),
        "canonical_slot_count": canonical,
        "recorded_retry_failure_count": len(ordered) - canonical,
        "full_evidence_synced_to_controller": False,
        "remote_artifact_deleted": False,
        "secret_material_recorded": False,
    }
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    _atomic_write_json(output, receipt, mode=0o600)
    _write_sidecar(output)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "output_path": str(output.relative_to(ROOT)),
                "paid_slot_count": len(ordered),
                "canonical_slot_count": canonical,
                "recorded_retry_failure_count": len(ordered) - canonical,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
