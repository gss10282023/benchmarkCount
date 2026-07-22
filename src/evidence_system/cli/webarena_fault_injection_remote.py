"""Plan or explicitly execute the real WebArena-Verified 3×4 fault matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_system.webarena_fault_injection_remote import (
    REMOTE_EXECUTION_CONFIRMATION,
    build_remote_fault_plan,
    execute_remote_fault_matrix,
    write_remote_fault_plan,
)


DEFAULT_RECEIPTS_ROOT = Path(
    "experiments/step20/webarena_verified/fault_injection/remote_three_host"
)
DEFAULT_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/fault_injection/"
    "remote_three_host_acceptance.json"
)
DEFAULT_PLAN = Path(
    "experiments/step20/webarena_verified/fault_injection/remote_execution_plan.json"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--infra-config", type=Path, default=Path("configs/infra.yaml"))
    parser.add_argument(
        "--site-lock",
        type=Path,
        default=Path("configs/webarena_verified_sites.lock.json"),
    )
    parser.add_argument("--receipts-root", type=Path, default=DEFAULT_RECEIPTS_ROOT)
    parser.add_argument("--acceptance-output", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--plan-output", type=Path, default=DEFAULT_PLAN)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("plan", help="print the exact 12-slot plan; performs no SSH")
    execute = subparsers.add_parser(
        "execute", help="execute the exact remote 3×4 matrix and recovery checks"
    )
    execute.add_argument(
        "--confirm",
        required=True,
        help=f"Must equal {REMOTE_EXECUTION_CONFIRMATION!r}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        payload = build_remote_fault_plan(
            infra_config_path=args.infra_config,
            receipts_root=args.receipts_root,
        )
        write_remote_fault_plan(args.plan_output, payload)
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "remote_execution_performed": False,
                    "receipt_count": payload["receipt_count"],
                    "paid_model_calls_planned": 0,
                    "plan_output": str(args.plan_output),
                    "plan_core_sha256": payload["integrity"]["core_sha256"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    result = execute_remote_fault_matrix(
        infra_config_path=args.infra_config,
        site_lock_path=args.site_lock,
        receipts_root=args.receipts_root,
        acceptance_output=args.acceptance_output,
        confirmation=args.confirm,
    )
    summary = {
        "status": result.acceptance["status"],
        "receipt_count": len(result.receipt_paths),
        "failure_count": len(result.failures),
        "formal_step20_fault_gate_satisfied": result.acceptance[
            "formal_step20_fault_gate_satisfied"
        ],
        "acceptance_output": str(result.acceptance_path),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if result.acceptance["status"] == "pass" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
