#!/usr/bin/env python3
"""Reconstruct a durable receipt for interrupted pending-slot relaunches.

The relaunch executor records a row only after a remote slot has reached a
terminal state.  If its controller process is interrupted between rows, this
read-only reconciler rebuilds that small control receipt from the immutable
original preservation evidence and the current VPS hash audit.  It never
launches a browser or a model worker and never retrieves full artifacts.
"""

from __future__ import annotations

import argparse
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
from evidence_system.core.hashing import sha256_file  # noqa: E402
from evidence_system.orchestrator.webarena_verified_full import (  # noqa: E402
    DEFAULT_SITE_LOCK,
    EXPECTED_AGENT_IDS,
)
from evidence_system.orchestrator.webarena_verified_run_control import (  # noqa: E402
    CIRCUIT_RECOVERY_CONFIRMATION_PREFIX,
    DEFAULT_CIRCUIT_RECOVERY_RECEIPT,
    DEFAULT_JOBS_INDEX,
    _atomic_write_json,
    _circuit_recovery_gate,
    _live_quiescence,
    _remote_audit_target,
    _write_sidecar,
    load_materialized_full_plan,
    monitor_namespace,
)
from evidence_system.webarena_sites import load_site_lock  # noqa: E402
from scripts.relaunch_webarena_pending_preserved_slots import (  # noqa: E402
    _load_prior_receipt,
    _load_selection,
    _preserved_root_for,
)


DEFAULT_OUTPUT = Path(
    "results/namespaces/webarena_verified_v1_2_3_full_812/"
    "pending_controller_relaunch_reconciled_receipt.json"
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


def _selected_jobs(
    *,
    plan: Any,
    selection: Mapping[str, tuple[int, ...]],
) -> dict[str, tuple[dict[str, Any], ...]]:
    selected: dict[str, tuple[dict[str, Any], ...]] = {}
    for agent_id, task_ids in selection.items():
        jobs = tuple(
            dict(job)
            for job in plan.jobs
            if str(job["agent_id"]) == agent_id
            and int(job["task_id"]) in task_ids
        )
        if tuple(int(job["task_id"]) for job in jobs) != task_ids:
            raise RuntimeError(f"formal slots are missing for {agent_id}")
        selected[agent_id] = jobs
    return selected


def _validate_preserved_root(*, target: Any, root: str) -> None:
    command = (
        f"test -d {shlex.quote(root)} && "
        f"test ! -L {shlex.quote(root)} && "
        f"test -f {shlex.quote(root + '/native_run/run_summary.json')} && "
        f"test ! -e {shlex.quote(root + '/remote_slot_acceptance.json')}"
    )
    observed = run_remote_blind_command(
        target,
        command,
        timeout_seconds=60,
        maximum_stdout_bytes=0,
        maximum_stderr_bytes=1024,
    )
    if observed.returncode != 0 or observed.stderr:
        raise RuntimeError("preserved terminal evidence is not intact")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    selection = _load_selection(args.selection)
    prior = _load_prior_receipt(args.prior_retry_receipt)
    prior_path = _repo_file(args.prior_retry_receipt, label="prior targeted retry receipt")
    if not _sidecar_valid(prior_path):
        raise RuntimeError("prior targeted retry receipt sidecar is invalid")
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
        # The immediately preceding circuit-recovery receipt performed the
        # full VPS file/hash sweep.  This read-only reconstruction only needs
        # a current bounded receipt audit, then binds it to that exact receipt.
        remote_verify_files=False,
        write_outputs=False,
    )
    recovery = _circuit_recovery_gate(
        path_value=args.circuit_recovery_receipt,
        snapshot=snapshot,
        jobs_index_path=args.jobs_index,
    )
    if recovery.get("status") != "pass":
        raise RuntimeError("circuit recovery receipt is not valid for current state")
    expected_clear = CIRCUIT_RECOVERY_CONFIRMATION_PREFIX + str(
        recovery.get("recovery_id") or ""
    )
    if args.confirm_circuit_recovery != expected_clear and not args.dry_run:
        raise RuntimeError("exact circuit-recovery confirmation is required")
    if not set(selection).issubset(set(recovery.get("authorized_agent_ids") or [])):
        raise RuntimeError("recovery receipt does not authorize every selected agent")
    quiescence = _live_quiescence(
        jobs=plan.jobs,
        ssh_key_path=args.ssh_key,
        site_lock_path=args.site_lock,
    )
    if quiescence.get("status") != "pass":
        raise RuntimeError("all three VPS workers must be quiescent")

    site_lock = load_site_lock(_repo_file(args.site_lock, label="site lock"))
    targets = {
        agent_id: _remote_audit_target(
            jobs[0], ssh_key_path=args.ssh_key, site_lock=site_lock
        )
        for agent_id, jobs in selected_by_agent.items()
    }
    preserved: dict[str, str] = {}
    for agent_id, jobs in selected_by_agent.items():
        for job in jobs:
            slot_id = str(job["record_slot_id"])
            root = _preserved_root_for(
                prior=prior,
                agent_id=agent_id,
                task_id=int(job["task_id"]),
            )
            _validate_preserved_root(target=targets[agent_id], root=root)
            preserved[slot_id] = root

    audits_by_slot = {audit.record_slot_id: audit for audit in snapshot.audits}
    rows: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENT_IDS:
        for job in selected_by_agent.get(agent_id, ()):
            slot_id = str(job["record_slot_id"])
            audit = audits_by_slot.get(slot_id)
            if audit is None:
                raise RuntimeError(f"selected slot is missing from the live audit: {slot_id}")
            base = {
                "agent_id": agent_id,
                "task_id": int(job["task_id"]),
                "record_slot_id": slot_id,
                "preserved_terminal_artifact_root": preserved[slot_id],
                "paid_runtime_replayed": True,
            }
            if audit.reusable:
                rows.append(
                    {
                        **base,
                        "status": "canonical_reusable",
                        "audit_state": audit.state,
                    }
                )
                continue
            if audit.state == "in_progress" and audit.issues:
                rows.append(
                    {
                        **base,
                        "status": "retry_failed",
                        "audit_state": audit.state,
                        "terminal_issue_signatures": sorted(
                            str(issue.get("signature") or "")
                            for issue in audit.issues
                        ),
                    }
                )
                continue
            raise RuntimeError(
                f"selected slot has no terminal replacement outcome: {slot_id}"
            )
    if {str(row["record_slot_id"]) for row in rows} != selected_slots:
        raise RuntimeError("reconciliation did not cover every selected slot")
    canonical = sum(row["status"] == "canonical_reusable" for row in rows)
    receipt = {
        "schema_version": "webarena_verified_pending_preserved_relaunch/v1",
        "status": "pass" if canonical == len(rows) else "completed_with_recorded_failures",
        "recovery_id": recovery["recovery_id"],
        "results": rows,
        "paid_slot_count": len(rows),
        "canonical_slot_count": canonical,
        "recorded_retry_failure_count": len(rows) - canonical,
        "prior_controller_failure_receipt": str(args.prior_retry_receipt),
        "prior_controller_failure_receipt_sha256": sha256_file(prior_path),
        "preserved_terminal_artifact_roots": preserved,
        "full_evidence_synced_to_controller": False,
        "remote_artifact_deleted": False,
        "reconciled_from_live_remote_hash_audit": True,
        "secret_material_recorded": False,
    }
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "planned",
                    "record_slot_ids": sorted(selected_slots),
                    "canonical_slot_count": canonical,
                    "recorded_retry_failure_count": len(rows) - canonical,
                    "full_evidence_synced_to_controller": False,
                },
                sort_keys=True,
            )
        )
        return 0
    _atomic_write_json(output, receipt, mode=0o600)
    _write_sidecar(output)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "output_path": str(output.relative_to(ROOT)),
                "paid_slot_count": len(rows),
                "canonical_slot_count": canonical,
                "recorded_retry_failure_count": len(rows) - canonical,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
