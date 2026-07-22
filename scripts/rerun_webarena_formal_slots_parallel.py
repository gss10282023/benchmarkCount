#!/usr/bin/env python3
"""Run one exact, recovery-authorized formal retry lane on each WebArena VPS.

The controller preserves every prior terminal artifact root before it starts a
replacement attempt.  It intentionally executes no unselected formal slot;
the three selected agent lanes are therefore safe to run concurrently.
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
from scripts.reconcile_webarena_completed_slots import (  # noqa: E402
    FORMAL_NAMESPACE_REMOTE_PREFIX,
    _remote_lane_audits,
)


SELECTION_SCHEMA = "webarena_verified_targeted_retry_selection/v1"
DEFAULT_OUTPUT = Path(
    "results/namespaces/webarena_verified_v1_2_3_full_812/"
    "targeted_parallel_formal_recovery_receipt.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument(
        "--selection",
        required=True,
        help=(
            "JSON selection with a retry_once object mapping every locked "
            "agent ID to an ascending, non-empty list of task IDs"
        ),
    )
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


def _load_selection(path_value: str | Path) -> dict[str, tuple[int, ...]]:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("targeted retry selection is missing or unsafe")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("targeted retry selection is invalid JSON") from exc
    if (
        not isinstance(payload, Mapping)
        or payload.get("schema_version") != SELECTION_SCHEMA
        or not isinstance(payload.get("retry_once"), Mapping)
    ):
        raise RuntimeError("targeted retry selection has the wrong schema")
    raw = payload["retry_once"]
    if set(raw) != set(EXPECTED_AGENT_IDS):
        raise RuntimeError("targeted retry selection must cover exactly three agents")

    selection: dict[str, tuple[int, ...]] = {}
    for agent_id in EXPECTED_AGENT_IDS:
        task_ids = raw[agent_id]
        if (
            not isinstance(task_ids, list)
            or not task_ids
            or any(not isinstance(task_id, int) for task_id in task_ids)
            or task_ids != sorted(task_ids)
            or len(task_ids) != len(set(task_ids))
            or any(task_id < 0 or task_id > 811 for task_id in task_ids)
        ):
            raise RuntimeError(
                f"targeted retry task IDs are invalid for {agent_id}"
            )
        selection[agent_id] = tuple(task_ids)
    return selection


def _preserved_terminal_root(audit: Mapping[str, Any]) -> str:
    root = str(audit.get("persistent_adapter_root") or "")
    binding = str(audit.get("job_binding_sha256") or "")
    if (
        not root.startswith(FORMAL_NAMESPACE_REMOTE_PREFIX)
        or not root.endswith("/adapter")
        or len(binding) != 64
        or any(character not in "0123456789abcdef" for character in binding)
    ):
        raise RuntimeError("terminal slot has an unsafe preservation binding")
    return f"{root}.preserved-terminal-rerun-{binding[:16]}"


def _selected_jobs(
    *,
    plan: Any,
    selection: Mapping[str, tuple[int, ...]],
) -> dict[str, tuple[dict[str, Any], ...]]:
    selected: dict[str, tuple[dict[str, Any], ...]] = {}
    for agent_id in EXPECTED_AGENT_IDS:
        task_ids = selection[agent_id]
        jobs = tuple(
            dict(job)
            for job in plan.jobs
            if job.get("agent_id") == agent_id
            and int(job["task_id"]) in task_ids
        )
        if tuple(int(job["task_id"]) for job in jobs) != task_ids:
            raise RuntimeError(
                f"requested formal slots are missing or out of lane order for {agent_id}"
            )
        selected[agent_id] = jobs
    return selected


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.confirm_paid_full != PAID_FULL_CONFIRMATION and not args.dry_run:
        raise RuntimeError("exact paid-full confirmation is required")

    selection = _load_selection(args.selection)
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
    if not set(EXPECTED_AGENT_IDS).issubset(
        set(recovery.get("authorized_agent_ids") or [])
    ):
        raise RuntimeError("recovery receipt does not authorize every selected agent")

    site_lock = load_site_lock(Path(args.site_lock))

    def audit_lane(agent_id: str) -> tuple[str, Any, list[dict[str, Any]]]:
        lane = [dict(job) for job in plan.jobs if job.get("agent_id") == agent_id]
        target, audits = _remote_lane_audits(
            lane,
            ssh_key=args.ssh_key,
            site_lock=site_lock,
        )
        return agent_id, target, audits

    targets: dict[str, Any] = {}
    audits_by_slot: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="webarena-retry-audit") as pool:
        futures = [pool.submit(audit_lane, agent_id) for agent_id in EXPECTED_AGENT_IDS]
        for future in as_completed(futures):
            agent_id, target, audits = future.result()
            targets[agent_id] = target
            audits_by_slot.update(
                {str(audit["record_slot_id"]): audit for audit in audits}
            )

    selected_audits: dict[str, dict[str, Any]] = {}
    for jobs in selected_by_agent.values():
        for job in jobs:
            slot_id = str(job["record_slot_id"])
            audit = audits_by_slot.get(slot_id)
            if (
                audit is None
                or audit.get("state") != "in_progress"
                or audit.get("terminal_failure_observed") is not True
                or audit.get("runtime_completed_unsealed") is True
            ):
                raise RuntimeError(
                    f"formal slot is not a terminal recovery candidate: {slot_id}"
                )
            selected_audits[slot_id] = audit

    planned = {
        "status": "planned",
        "recovery_id": recovery["recovery_id"],
        "agent_task_ids": {
            agent_id: list(selection[agent_id]) for agent_id in EXPECTED_AGENT_IDS
        },
        "record_slot_ids": sorted(selected_slots),
        "terminal_failure_codes": {
            slot_id: str(
                selected_audits[slot_id].get("terminal_failure_code") or ""
            )
            for slot_id in sorted(selected_slots)
        },
        "paid_slot_count": len(selected_slots),
        "remote_artifact_deleted": False,
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

    def preserve_lane(agent_id: str) -> tuple[str, list[str]]:
        preserved: list[str] = []
        for job in selected_by_agent[agent_id]:
            audit = selected_audits[str(job["record_slot_id"])]
            source = str(audit["persistent_adapter_root"])
            destination = _preserved_terminal_root(audit)
            command = (
                f"test -d {shlex.quote(source)} && "
                f"test ! -L {shlex.quote(source)} && "
                f"test ! -e {shlex.quote(destination)} && "
                f"test -f {shlex.quote(source + '/native_run/run_summary.json')} && "
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
            if completed.returncode != 0 or completed.stderr:
                raise RuntimeError(
                    f"terminal artifact preservation failed: {job['record_slot_id']}"
                )
            preserved.append(destination)
        return agent_id, preserved

    preserved_by_agent: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="webarena-retry-preserve") as pool:
        futures = [pool.submit(preserve_lane, agent_id) for agent_id in EXPECTED_AGENT_IDS]
        for future in as_completed(futures):
            agent_id, preserved = future.result()
            preserved_by_agent[agent_id] = preserved

    adapter = import_module("evidence_system.adapters.webarena_verified")
    real_planner = getattr(adapter, "plan_smoke_execution")
    real_executor = getattr(adapter, "execute_smoke_job")
    results: list[dict[str, Any]] = []
    results_lock = threading.Lock()

    def targeted_planner(job: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        if str(job["record_slot_id"]) not in selected_slots:
            return {
                "status": "runnable",
                "runner_command": "targeted-parallel-formal-recovery-skip",
                "targeted_parallel_formal_recovery_skip": True,
            }
        return dict(real_planner(job, **kwargs))

    def record_result(row: dict[str, Any]) -> None:
        with results_lock:
            results.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    def targeted_executor(
        job: dict[str, Any],
        *,
        execution_plan: Mapping[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        if execution_plan.get("targeted_parallel_formal_recovery_skip") is True:
            return {"status": "completed", "targeted_parallel_formal_recovery_skip": True}

        slot_id = str(job["record_slot_id"])
        base = {
            "agent_id": str(job["agent_id"]),
            "task_id": int(job["task_id"]),
            "record_slot_id": slot_id,
            "previous_terminal_failure_code": str(
                selected_audits[slot_id].get("terminal_failure_code") or ""
            ),
            "paid_runtime_replayed": True,
        }
        try:
            result = dict(
                real_executor(job, execution_plan=dict(execution_plan), **kwargs)
            )
            audited = audit_remote_slot(
                job,
                ssh_key_path=args.ssh_key,
                site_lock=site_lock,
            )
            if result.get("status") == "completed" and audited.reusable:
                record_result(
                    {
                        **base,
                        "status": "canonical_reusable",
                        "audit_state": audited.state,
                        "remote_artifact_root": audited.artifact_root,
                    }
                )
            else:
                record_result(
                    {
                        **base,
                        "status": "retry_failed",
                        "executor_status": str(result.get("status") or ""),
                        "audit_state": audited.state,
                        "remote_artifact_root": audited.artifact_root,
                    }
                )
        except Exception as exc:  # Continue the independent lanes after one retry fails.
            try:
                audited = audit_remote_slot(
                    job,
                    ssh_key_path=args.ssh_key,
                    site_lock=site_lock,
                )
                audit_state = audited.state
                artifact_root = audited.artifact_root
            except Exception:
                audit_state = "audit_unavailable"
                artifact_root = None
            record_result(
                {
                    **base,
                    "status": "retry_failed",
                    "executor_error_type": type(exc).__name__,
                    "audit_state": audit_state,
                    "remote_artifact_root": artifact_root,
                }
            )
        # A failed selected retry is deliberately recorded, not propagated: every
        # selected slot gets exactly one attempt before the controller stops.
        return {"status": "completed", "targeted_parallel_recovery_recorded": True}

    execute_full_schedule(
        plan,
        ssh_key_path=args.ssh_key,
        site_lock_path=args.site_lock,
        adapter_planner=targeted_planner,
        adapter_executor=targeted_executor,
    )
    if len(results) != len(selected_slots):
        raise RuntimeError("parallel targeted recovery did not execute every selected slot")

    ordered_results = sorted(
        results,
        key=lambda item: (EXPECTED_AGENT_IDS.index(str(item["agent_id"])), item["task_id"]),
    )
    canonical_count = sum(
        item.get("status") == "canonical_reusable" for item in ordered_results
    )
    failed_count = len(ordered_results) - canonical_count
    receipt = {
        "schema_version": "webarena_verified_parallel_targeted_formal_recovery/v1",
        "status": "pass" if failed_count == 0 else "completed_with_recorded_failures",
        "recovery_id": recovery["recovery_id"],
        "agent_task_ids": {
            agent_id: list(selection[agent_id]) for agent_id in EXPECTED_AGENT_IDS
        },
        "results": ordered_results,
        "preserved_terminal_artifact_roots": {
            agent_id: preserved_by_agent[agent_id] for agent_id in EXPECTED_AGENT_IDS
        },
        "paid_slot_count": len(ordered_results),
        "canonical_slot_count": canonical_count,
        "recorded_retry_failure_count": failed_count,
        "remote_artifact_deleted": False,
        "full_evidence_synced_to_controller": False,
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
                "paid_slot_count": len(ordered_results),
                "canonical_slot_count": canonical_count,
                "recorded_retry_failure_count": failed_count,
                "remote_artifact_deleted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
