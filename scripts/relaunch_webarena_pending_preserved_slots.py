#!/usr/bin/env python3
"""Relaunch exact slots that were never started after terminal evidence moved.

This is deliberately narrower than a normal targeted recovery: a controller
storage failure may occur after the old terminal root is preserved but before
the replacement worker begins.  The script proves that state, leaves the
preserved root immutable, and launches exactly one replacement attempt.
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
    _circuit_recovery_gate,
    _live_quiescence,
    _write_sidecar,
    audit_remote_slot,
    load_materialized_full_plan,
    monitor_namespace,
)
from evidence_system.webarena_sites import load_site_lock  # noqa: E402
from scripts.reconcile_webarena_completed_slots import _remote_lane_audits  # noqa: E402


SELECTION_SCHEMA = "webarena_verified_pending_relaunch_selection/v1"
PRIOR_RECEIPT_SCHEMA = "webarena_verified_parallel_targeted_formal_recovery/v1"
DEFAULT_OUTPUT = Path(
    "results/namespaces/webarena_verified_v1_2_3_full_812/"
    "pending_controller_relaunch_receipt.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--prior-retry-receipt", required=True)
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
    path = _repo_file(path_value, label="pending relaunch selection")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("pending relaunch selection is invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("pending relaunch selection has the wrong schema")
    raw = payload.get("retry_once")
    if payload.get("schema_version") != SELECTION_SCHEMA or not isinstance(raw, Mapping):
        raise RuntimeError("pending relaunch selection has the wrong schema")
    if not set(raw).issubset(EXPECTED_AGENT_IDS) or not raw:
        raise RuntimeError("pending relaunch selection has invalid agent IDs")
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
            raise RuntimeError(f"pending relaunch task IDs are invalid for {agent_id}")
        selection[str(agent_id)] = tuple(raw_ids)
    return selection


def _load_prior_receipt(path_value: str | Path) -> Mapping[str, Any]:
    path = _repo_file(path_value, label="prior targeted retry receipt")
    if not _sidecar_valid(path):
        raise RuntimeError("prior targeted retry receipt sidecar is invalid")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("prior targeted retry receipt is invalid JSON") from exc
    if payload.get("schema_version") != PRIOR_RECEIPT_SCHEMA:
        raise RuntimeError("prior targeted retry receipt has the wrong schema")
    if not isinstance(payload.get("results"), list) or not isinstance(
        payload.get("preserved_terminal_artifact_roots"), Mapping
    ):
        raise RuntimeError("prior targeted retry receipt lacks preservation evidence")
    return payload


def _selected_jobs(
    *,
    plan: Any,
    selection: Mapping[str, tuple[int, ...]],
) -> dict[str, tuple[dict[str, Any], ...]]:
    result: dict[str, tuple[dict[str, Any], ...]] = {}
    for agent_id, task_ids in selection.items():
        jobs = tuple(
            dict(job)
            for job in plan.jobs
            if job.get("agent_id") == agent_id and int(job["task_id"]) in task_ids
        )
        if tuple(int(job["task_id"]) for job in jobs) != task_ids:
            raise RuntimeError(f"formal slots are missing for {agent_id}")
        result[agent_id] = jobs
    return result


def _preserved_root_for(
    *,
    prior: Mapping[str, Any],
    agent_id: str,
    task_id: int,
) -> str:
    roots = dict(prior["preserved_terminal_artifact_roots"]).get(agent_id)
    if not isinstance(roots, list):
        raise RuntimeError(f"prior receipt lacks preserved roots for {agent_id}")
    suffix = agent_id[-1].lower()
    marker = (
        f"full-webarena_verified-{task_id:03d}-agent_{suffix}/"
        "adapter.preserved-terminal-rerun-"
    )
    matches = [str(root) for root in roots if marker in str(root)]
    if len(matches) != 1:
        raise RuntimeError(f"prior preserved root is ambiguous for {agent_id} task {task_id}")
    return matches[0]


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.confirm_paid_full != PAID_FULL_CONFIRMATION and not args.dry_run:
        raise RuntimeError("exact paid-full confirmation is required")
    selection = _load_selection(args.selection)
    prior = _load_prior_receipt(args.prior_retry_receipt)
    prior_rows = {
        (str(row.get("agent_id")), int(row["task_id"])): dict(row)
        for row in prior["results"]
        if isinstance(row, Mapping) and isinstance(row.get("task_id"), int)
    }
    for agent_id, task_ids in selection.items():
        for task_id in task_ids:
            row = prior_rows.get((agent_id, task_id))
            if (
                row is None
                or row.get("audit_state") != "pending"
                or row.get("executor_error_type") != "OSError"
            ):
                raise RuntimeError(
                    f"prior receipt does not prove an unstarted controller failure for "
                    f"{agent_id} task {task_id}"
                )

    plan = load_materialized_full_plan(index_path=args.jobs_index)
    selected_by_agent = _selected_jobs(plan=plan, selection=selection)
    selected_slots = {
        str(job["record_slot_id"])
        for jobs in selected_by_agent.values()
        for job in jobs
    }
    snapshot = monitor_namespace(
        mode="full",
        index_path=args.jobs_index,
        site_lock_path=args.site_lock,
        ssh_key_path=args.ssh_key,
        write_outputs=False,
    )
    recovery = _circuit_recovery_gate(
        path_value=args.circuit_recovery_receipt,
        snapshot=snapshot,
        jobs_index_path=args.jobs_index,
    )
    expected_clear = CIRCUIT_RECOVERY_CONFIRMATION_PREFIX + str(
        recovery.get("recovery_id") or ""
    )
    if recovery.get("status") != "pass":
        raise RuntimeError("circuit recovery receipt is not valid for current state")
    if args.confirm_circuit_recovery != expected_clear and not args.dry_run:
        raise RuntimeError("exact circuit-recovery confirmation is required")
    if not set(selection).issubset(set(recovery.get("authorized_agent_ids") or [])):
        raise RuntimeError("recovery receipt does not authorize every selected agent")

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
        max_workers=len(selection), thread_name_prefix="webarena-pending-audit"
    ) as pool:
        futures = [pool.submit(audit_lane, agent_id) for agent_id in selection]
        for future in as_completed(futures):
            agent_id, target, audits = future.result()
            targets[agent_id] = target
            audits_by_slot.update(
                {str(audit["record_slot_id"]): audit for audit in audits}
            )

    preserved_roots: dict[str, str] = {}
    for agent_id, jobs in selected_by_agent.items():
        for job in jobs:
            slot_id = str(job["record_slot_id"])
            audit = audits_by_slot.get(slot_id)
            if audit is None or audit.get("state") != "pending":
                raise RuntimeError(f"slot is no longer a pending relaunch candidate: {slot_id}")
            root = _preserved_root_for(
                prior=prior, agent_id=agent_id, task_id=int(job["task_id"])
            )
            command = (
                f"test -d {shlex.quote(root)} && "
                f"test ! -L {shlex.quote(root)} && "
                f"test -f {shlex.quote(root + '/native_run/run_summary.json')} && "
                f"test ! -e {shlex.quote(root + '/remote_slot_acceptance.json')}"
            )
            checked = run_remote_blind_command(
                targets[agent_id],
                command,
                timeout_seconds=60,
                maximum_stdout_bytes=0,
                maximum_stderr_bytes=1024,
            )
            if checked.returncode != 0 or checked.stderr:
                raise RuntimeError(f"preserved terminal evidence is not intact: {slot_id}")
            preserved_roots[slot_id] = root

    planned = {
        "status": "planned",
        "recovery_id": recovery["recovery_id"],
        "record_slot_ids": sorted(selected_slots),
        "paid_slot_count": len(selected_slots),
        "prior_controller_failure_receipt": str(args.prior_retry_receipt),
        "preserved_terminal_artifact_roots": preserved_roots,
        "full_evidence_synced_to_controller": False,
    }
    print(json.dumps(planned, sort_keys=True), flush=True)
    if args.dry_run:
        return 0

    quiescence = _live_quiescence(
        jobs=plan.jobs,
        ssh_key_path=args.ssh_key,
        site_lock_path=args.site_lock,
    )
    if quiescence.get("status") != "pass":
        raise RuntimeError("all three VPS workers must be quiescent")

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
            return {"status": "runnable", "pending_relaunch_skip": True}
        return dict(real_planner(job, **kwargs))

    def executor(
        job: dict[str, Any],
        *,
        execution_plan: Mapping[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        if execution_plan.get("pending_relaunch_skip") is True:
            return {"status": "completed", "pending_relaunch_skip": True}
        slot_id = str(job["record_slot_id"])
        base = {
            "agent_id": str(job["agent_id"]),
            "task_id": int(job["task_id"]),
            "record_slot_id": slot_id,
            "preserved_terminal_artifact_root": preserved_roots[slot_id],
        }
        try:
            completed = dict(real_executor(job, execution_plan=dict(execution_plan), **kwargs))
            audited = audit_remote_slot(job, ssh_key_path=args.ssh_key, site_lock=site_lock)
            if completed.get("status") == "completed" and audited.reusable:
                record({**base, "status": "canonical_reusable", "audit_state": audited.state})
            else:
                record(
                    {
                        **base,
                        "status": "retry_failed",
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
        return {"status": "completed", "pending_relaunch_recorded": True}

    execute_full_schedule(
        plan,
        ssh_key_path=args.ssh_key,
        site_lock_path=args.site_lock,
        adapter_planner=planner,
        adapter_executor=executor,
    )
    if len(results) != len(selected_slots):
        raise RuntimeError("pending relaunch did not execute every selected slot")

    ordered = sorted(
        results,
        key=lambda row: (EXPECTED_AGENT_IDS.index(str(row["agent_id"])), row["task_id"]),
    )
    canonical = sum(row["status"] == "canonical_reusable" for row in ordered)
    receipt = {
        "schema_version": "webarena_verified_pending_preserved_relaunch/v1",
        "status": "pass" if canonical == len(ordered) else "completed_with_recorded_failures",
        "recovery_id": recovery["recovery_id"],
        "results": ordered,
        "paid_slot_count": len(ordered),
        "canonical_slot_count": canonical,
        "recorded_retry_failure_count": len(ordered) - canonical,
        "prior_controller_failure_receipt": str(args.prior_retry_receipt),
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
