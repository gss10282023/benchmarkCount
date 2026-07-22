"""Inspect or offline-test the exact AgentDojo disposable round controller."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from evidence_system.adapters.agentdojo_disposable_controller import (
    CountingFakeDisposableTransport,
    VPSDisposableTransport,
    execute_disposable_round,
)
from evidence_system.adapters.agentdojo_runtime_control import RuntimePolicyError
from evidence_system.contracts.agentdojo_rate_lifecycle import (
    load_disposable_round_plan,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--round-plan", required=True)
    fake = commands.add_parser("fake-run")
    fake.add_argument("--round-plan", required=True)
    fake.add_argument("--output", required=True)
    fake.add_argument("--allow-test-fake", action="store_true", required=True)
    real = commands.add_parser("real-run")
    real.add_argument("--round-plan", required=True)
    real.add_argument("--output")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "inspect":
            plan = load_disposable_round_plan(args.round_plan)
            result = {
                "status": "valid",
                "round_definition_sha256": plan["definition_sha256"],
                "round_kind": plan["definition"]["round_kind"],
                "stage_count": len(plan["definition"]["stages"]),
                "record_slot_count": plan["definition"]["exact_workload"][
                    "total_record_slots"
                ],
                "transport_batch_count": 15,
                "mixed_canary_schedule": (
                    "three_serial_four_slot_single_model_subbatches"
                ),
                "network_called": False,
            }
        elif args.command == "fake-run":
            result = execute_disposable_round(
                round_plan_path=args.round_plan,
                transport=CountingFakeDisposableTransport(),
                receipt_path=args.output,
            )
        else:
            transport = VPSDisposableTransport(
                round_plan_path=args.round_plan
            )
            output = args.output or (
                transport.plan["artifact_namespace"]["root"]
                + "/controller_receipt.json"
            )
            result = execute_disposable_round(
                round_plan_path=args.round_plan,
                transport=transport,
                receipt_path=output,
            )
    except (OSError, RuntimeError, ValueError, RuntimePolicyError) as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
