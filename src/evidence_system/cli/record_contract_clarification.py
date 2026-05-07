"""Record post-lock contract clarification as sensitivity-only artifact."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.contracts.clarification import record_contract_clarification
from evidence_system.contracts.common import ContractLifecycleError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.record_contract_clarification")
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--locked-contract")
    parser.add_argument("--output-dir", default="experiments/evidence_contracts/superseded")
    parser.add_argument("--new-version")
    parser.add_argument("--sensitivity-report-id")
    parser.add_argument("--clarification-note", default="post-lock clarification")
    parser.add_argument("--locked-by")
    parser.add_argument("--locked-at")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        payload = {"name": "record_contract_clarification", "status": "ok", "formal_logic": "implemented_step_4", "side_effects": "none"}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    required = ("locked_contract", "new_version", "sensitivity_report_id", "locked_by", "locked_at")
    missing = [field for field in required if not getattr(args, field)]
    if missing:
        print({"status": "invalid_args", "missing": missing}, file=sys.stderr)
        return 2
    try:
        result = record_contract_clarification(
            locked_contract_path=args.locked_contract,
            output_dir=args.output_dir,
            new_version=args.new_version,
            sensitivity_report_id=args.sensitivity_report_id,
            clarification_note=args.clarification_note,
            locked_by=args.locked_by,
            locked_at=args.locked_at,
        )
        payload = {"status": "ok", **result.to_dict()}
    except ContractLifecycleError as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
