"""Build strict WebArena-Verified fault-injection receipts and acceptance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_system.webarena_fault_injection import (
    build_fault_acceptance,
    build_local_simulation_receipts,
    machine_targets_from_infra,
    validate_fault_acceptance,
    validate_fault_receipt,
    write_fault_acceptance,
)


DEFAULT_ROOT = Path(
    "experiments/step20/webarena_verified/fault_injection/local_harness"
)
DEFAULT_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/fault_injection/"
    "local_harness_acceptance.json"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    local = subparsers.add_parser(
        "local-simulate",
        help="write four non-production local simulation receipts and aggregate them",
    )
    local.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    local.add_argument("--acceptance-output", type=Path, default=DEFAULT_ACCEPTANCE)

    aggregate = subparsers.add_parser(
        "aggregate", help="aggregate an exact local or remote receipt matrix"
    )
    aggregate.add_argument("--receipts-root", type=Path, required=True)
    aggregate.add_argument(
        "--scope",
        choices=("local_harness", "remote_three_host"),
        required=True,
    )
    aggregate.add_argument("--infra-config", type=Path, default=Path("configs/infra.yaml"))
    aggregate.add_argument("--acceptance-output", type=Path, required=True)

    validate_receipt = subparsers.add_parser(
        "validate-receipt", help="validate one receipt without changing it"
    )
    validate_receipt.add_argument("path", type=Path)

    validate_acceptance = subparsers.add_parser(
        "validate-acceptance", help="validate one aggregate without changing it"
    )
    validate_acceptance.add_argument("path", type=Path)

    args = parser.parse_args(argv)
    if args.command == "local-simulate":
        build_local_simulation_receipts(root=args.output_root)
        payload = build_fault_acceptance(
            receipts_root=args.output_root,
            scope="local_harness",
        )
        write_fault_acceptance(args.acceptance_output, payload)
        _print_summary(payload, args.acceptance_output)
        return 0 if payload["status"] == "pass" else 2
    if args.command == "aggregate":
        machine_targets = (
            machine_targets_from_infra(args.infra_config)
            if args.scope == "remote_three_host"
            else None
        )
        payload = build_fault_acceptance(
            receipts_root=args.receipts_root,
            scope=args.scope,
            machine_ids=tuple(machine_targets) if machine_targets else None,
            ssh_host_fingerprints=machine_targets,
        )
        write_fault_acceptance(args.acceptance_output, payload)
        _print_summary(payload, args.acceptance_output)
        return 0 if payload["status"] == "pass" else 2
    if args.command == "validate-receipt":
        payload = json.loads(args.path.read_text(encoding="utf-8"))
        validate_fault_receipt(payload)
        print(json.dumps({"status": "pass", "path": str(args.path)}, sort_keys=True))
        return 0
    if args.command == "validate-acceptance":
        payload = json.loads(args.path.read_text(encoding="utf-8"))
        validate_fault_acceptance(payload)
        print(json.dumps({"status": "pass", "path": str(args.path)}, sort_keys=True))
        return 0
    raise AssertionError(args.command)


def _print_summary(payload: dict[str, object], output: Path) -> None:
    print(
        json.dumps(
            {
                "status": payload["status"],
                "scope": payload["scope"],
                "formal_step20_fault_gate_satisfied": payload[
                    "formal_step20_fault_gate_satisfied"
                ],
                "output": str(output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
