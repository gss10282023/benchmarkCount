"""Monitor or resume the locked WebArena-Verified pilot/full run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evidence_system.orchestrator.webarena_verified_run_control import (
    DEFAULT_CONTROL_ACCEPTANCE,
    DEFAULT_CIRCUIT_RECOVERY_RECEIPT,
    DEFAULT_JOBS_INDEX,
    PAID_FULL_CONFIRMATION,
    WebArenaRunControlError,
    build_full_run_control_acceptance,
    execute_resumable_full_schedule,
    load_materialized_full_plan,
    monitor_namespace,
    write_control_acceptance,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--monitor-only",
        action="store_true",
        help="Read slot artifacts and update only the issue ledger/progress receipt.",
    )
    action.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the full-run control acceptance without paid calls (default).",
    )
    action.add_argument(
        "--execute",
        action="store_true",
        help="Resume the paid full run after every launch gate passes.",
    )
    parser.add_argument("--mode", choices=("pilot", "full"), default="full")
    parser.add_argument("--jobs-index", default=str(DEFAULT_JOBS_INDEX))
    parser.add_argument("--site-lock", default="configs/webarena_verified_sites.lock.json")
    parser.add_argument("--result-namespace")
    parser.add_argument("--control-output", default=str(DEFAULT_CONTROL_ACCEPTANCE))
    parser.add_argument("--ssh-key-path")
    parser.add_argument("--confirm-paid-full", default="")
    parser.add_argument(
        "--circuit-recovery-receipt",
        default=str(DEFAULT_CIRCUIT_RECOVERY_RECEIPT),
    )
    parser.add_argument("--confirm-circuit-recovery", default="")
    parser.add_argument(
        "--retry-exhausted-receipt",
        help=(
            "Signed disposition receipt for terminal slots whose one permitted "
            "retry has already been consumed."
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.execute and args.mode != "full":
        parser.error("--execute is valid only with --mode full")
    if args.execute and (
        not args.ssh_key_path or args.confirm_paid_full != PAID_FULL_CONFIRMATION
    ):
        parser.error(
            "--execute requires --ssh-key-path and exact "
            f"--confirm-paid-full {PAID_FULL_CONFIRMATION}"
        )
    if args.mode == "full" and not args.ssh_key_path:
        parser.error("full remote-retention monitoring requires --ssh-key-path")
    try:
        snapshot = monitor_namespace(
            mode=args.mode,
            index_path=args.jobs_index,
            result_namespace=args.result_namespace,
            site_lock_path=args.site_lock,
            ssh_key_path=args.ssh_key_path,
            write_outputs=True,
        )
        if args.monitor_only:
            payload: dict[str, object] = snapshot.progress
        else:
            plan = load_materialized_full_plan(args.jobs_index)
            if args.execute:
                execution = execute_resumable_full_schedule(
                    plan,
                    ssh_key_path=args.ssh_key_path,
                    confirm_paid_full=args.confirm_paid_full,
                    circuit_recovery_receipt_path=args.circuit_recovery_receipt,
                    confirm_circuit_recovery=args.confirm_circuit_recovery,
                    retry_exhausted_receipt_path=args.retry_exhausted_receipt,
                    jobs_index_path=args.jobs_index,
                    site_lock_path=args.site_lock,
                )
                refreshed = monitor_namespace(
                    mode="full",
                    index_path=args.jobs_index,
                    site_lock_path=args.site_lock,
                    ssh_key_path=args.ssh_key_path,
                    write_outputs=True,
                )
                payload = build_full_run_control_acceptance(
                    plan=plan,
                    jobs_index_path=args.jobs_index,
                    snapshot=refreshed,
                    circuit_recovery_receipt_path=args.circuit_recovery_receipt,
                    dry_run=False,
                )
                payload["execution"] = execution
            else:
                payload = build_full_run_control_acceptance(
                    plan=plan,
                    jobs_index_path=args.jobs_index,
                    snapshot=(snapshot if args.mode == "full" else None),
                    circuit_recovery_receipt_path=args.circuit_recovery_receipt,
                    dry_run=True,
                )
            write_control_acceptance(
                payload,
                output_path=Path(args.control_output),
            )
    except (OSError, ValueError, WebArenaRunControlError) as exc:
        if args.mode == "full" and args.ssh_key_path:
            try:
                blocked_snapshot = monitor_namespace(
                    mode="full",
                    index_path=args.jobs_index,
                    site_lock_path=args.site_lock,
                    ssh_key_path=args.ssh_key_path,
                    write_outputs=True,
                )
                blocked_plan = load_materialized_full_plan(args.jobs_index)
                blocked_acceptance = build_full_run_control_acceptance(
                    plan=blocked_plan,
                    jobs_index_path=args.jobs_index,
                    snapshot=blocked_snapshot,
                    circuit_recovery_receipt_path=args.circuit_recovery_receipt,
                    dry_run=not args.execute,
                )
                blocked_acceptance["status"] = "blocked"
                blocked_acceptance["formal_paid_launch_ready"] = False
                blocked_acceptance["blocked_error_type"] = type(exc).__name__
                write_control_acceptance(
                    blocked_acceptance,
                    output_path=Path(args.control_output),
                )
            except Exception:
                pass
        error = {
            "schema_version": "webarena_verified_run_control_error/v1",
            "status": "blocked",
            "error_type": type(exc).__name__,
            "secret_material_recorded": False,
        }
        if args.json:
            print(json.dumps(error, indent=2, sort_keys=True))
        else:
            print(f"BLOCKED: {type(exc).__name__}")
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        counts = dict(snapshot.progress.get("counts") or {})
        print(
            "PASS: "
            f"mode={args.mode} canonical={counts.get('canonical_reusable', 0)}/"
            f"{counts.get('expected', 0)} issues={counts.get('issues', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
