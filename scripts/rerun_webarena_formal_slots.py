#!/usr/bin/env python3
"""Rerun an exact recovery-authorized set of formal WebArena slots."""

from __future__ import annotations

import argparse
from importlib import import_module
import json
from pathlib import Path
import shlex
import sys
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


DEFAULT_OUTPUT = Path(
    "results/namespaces/webarena_verified_v1_2_3_full_812/"
    "targeted_formal_recovery_receipt.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument("--agent", required=True, choices=EXPECTED_AGENT_IDS)
    parser.add_argument("--task-id", required=True, type=int, action="append")
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


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.confirm_paid_full != PAID_FULL_CONFIRMATION and not args.dry_run:
        raise RuntimeError("exact paid-full confirmation is required")
    task_ids = tuple(args.task_id)
    if len(task_ids) != len(set(task_ids)) or not task_ids:
        raise RuntimeError("task ids must be a non-empty unique sequence")

    plan = load_materialized_full_plan(index_path=args.jobs_index)
    selected = tuple(
        dict(job)
        for job in plan.jobs
        if job.get("agent_id") == args.agent and int(job["task_id"]) in task_ids
    )
    if len(selected) != len(task_ids) or tuple(int(job["task_id"]) for job in selected) != task_ids:
        raise RuntimeError("requested formal slots are missing or out of lane order")

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
    if args.agent not in set(recovery.get("authorized_agent_ids") or []):
        raise RuntimeError("recovery receipt does not authorize the selected agent")

    site_lock = load_site_lock(Path(args.site_lock))
    lane = [dict(job) for job in plan.jobs if job.get("agent_id") == args.agent]
    target, audits = _remote_lane_audits(
        lane,
        ssh_key=args.ssh_key,
        site_lock=site_lock,
    )
    audits_by_slot = {str(audit["record_slot_id"]): audit for audit in audits}
    selected_audits = []
    for job in selected:
        audit = audits_by_slot[str(job["record_slot_id"])]
        if (
            audit.get("state") != "in_progress"
            or audit.get("terminal_failure_observed") is not True
            or audit.get("runtime_completed_unsealed") is True
        ):
            raise RuntimeError(
                f"formal slot is not a terminal recovery candidate: {job['record_slot_id']}"
            )
        selected_audits.append(audit)

    planned = {
        "status": "planned",
        "agent_id": args.agent,
        "task_ids": list(task_ids),
        "record_slot_ids": [str(job["record_slot_id"]) for job in selected],
        "recovery_id": recovery["recovery_id"],
        "terminal_failure_codes": [
            str(audit.get("terminal_failure_code") or "")
            for audit in selected_audits
        ],
        "paid_slot_count": len(selected),
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

    preserved_roots = []
    for job, audit in zip(selected, selected_audits, strict=True):
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
            target,
            command,
            timeout_seconds=60,
            maximum_stdout_bytes=0,
            maximum_stderr_bytes=1024,
        )
        if completed.returncode != 0 or completed.stderr:
            raise RuntimeError(f"terminal artifact preservation failed: {job['record_slot_id']}")
        preserved_roots.append(destination)

    selected_slots = {str(job["record_slot_id"]) for job in selected}
    adapter = import_module("evidence_system.adapters.webarena_verified")
    real_planner = getattr(adapter, "plan_smoke_execution")
    real_executor = getattr(adapter, "execute_smoke_job")
    results: list[dict[str, Any]] = []

    def targeted_planner(job: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        if str(job["record_slot_id"]) not in selected_slots:
            return {
                "status": "runnable",
                "runner_command": "targeted-formal-recovery-skip",
                "targeted_formal_recovery_skip": True,
            }
        return dict(real_planner(job, **kwargs))

    def targeted_executor(
        job: dict[str, Any],
        *,
        execution_plan: Mapping[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        if execution_plan.get("targeted_formal_recovery_skip") is True:
            return {"status": "completed", "targeted_formal_recovery_skip": True}
        result = dict(
            real_executor(job, execution_plan=dict(execution_plan), **kwargs)
        )
        audited = audit_remote_slot(
            job,
            ssh_key_path=args.ssh_key,
            site_lock=site_lock,
        )
        if result.get("status") != "completed" or not audited.reusable:
            raise RuntimeError(f"targeted formal rerun is not canonical: {job['record_slot_id']}")
        row = {
            "agent_id": job["agent_id"],
            "task_id": int(job["task_id"]),
            "record_slot_id": job["record_slot_id"],
            "audit_state": audited.state,
            "remote_artifact_root": audited.artifact_root,
            "paid_runtime_replayed": True,
        }
        results.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
        return result

    execute_full_schedule(
        plan,
        ssh_key_path=args.ssh_key,
        site_lock_path=args.site_lock,
        adapter_planner=targeted_planner,
        adapter_executor=targeted_executor,
        recovery_prelude_slot_ids=tuple(
            str(job["record_slot_id"]) for job in selected
        ),
    )
    if len(results) != len(selected):
        raise RuntimeError("targeted formal recovery did not execute every selected slot")

    receipt = {
        "schema_version": "webarena_verified_targeted_formal_recovery/v1",
        "status": "pass",
        "recovery_id": recovery["recovery_id"],
        "agent_id": args.agent,
        "task_ids": list(task_ids),
        "results": results,
        "preserved_terminal_artifact_roots": preserved_roots,
        "paid_slot_count": len(results),
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
                "status": "pass",
                "output_path": str(output.relative_to(ROOT)),
                "paid_slot_count": len(results),
                "canonical_slot_count": len(results),
                "remote_artifact_deleted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
