"""Generate or verify the metadata-only AgentDojo full execution budget plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evidence_system.contracts.agentdojo_execution_budget import (
    DEFAULT_BUDGET_PLAN,
    DEFAULT_HISTORICAL_ROOT,
    publish_budget_plan,
    verify_budget_plan,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, default=DEFAULT_HISTORICAL_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_BUDGET_PLAN)
    parser.add_argument("--created-at")
    parser.add_argument("--verify-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.verify_only:
            plan = verify_budget_plan(args.output)
            output = args.output
            action = "verified"
        else:
            output = publish_budget_plan(
                historical_root=args.historical_root,
                output_path=args.output,
                created_at=args.created_at,
            )
            plan = verify_budget_plan(output)
            action = "published"
    except (ContractLifecycleError, OSError, ValueError) as exc:
        print(str(exc))
        return 2
    definition = dict(plan["definition"])
    print(
        json.dumps(
            {
                "action": action,
                "output": str(output),
                "sha256": sha256_file(output),
                "historical_case_units": definition["historical_observation"]["case_units"],
                "historical_record_slots": definition["historical_observation"]["record_slots"],
                "target_case_units": definition["full_projection"]["case_units"],
                "target_record_slots": definition["full_projection"]["record_slots"],
                "projected_cost_usd": definition["budget_guard"]["projected_cost_usd"],
                "credit_floor_usd": definition["budget_guard"]["credit_floor_usd"],
                "maximum_run_cost_usd": definition["budget_guard"]["maximum_run_cost_usd"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
