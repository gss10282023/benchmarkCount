"""Lock reviewed evidence contracts before scoring."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.lock import lock_contracts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.lock_contracts")
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--reviewed", action="append", default=[], help="Reviewed contract file or directory. May be repeated.")
    parser.add_argument("--review-log", action="append", default=[], help="Review workflow file or directory. May be repeated.")
    parser.add_argument("--locked-dir", default="experiments/evidence_contracts/locked")
    parser.add_argument("--contract-review-dir", default="results/reviews/contracts/locked")
    parser.add_argument("--manifest-id", required=False)
    parser.add_argument("--manifest-hash", required=False)
    parser.add_argument("--locked-at")
    parser.add_argument("--locked-by")
    parser.add_argument("--first-scoring-started-at")
    parser.add_argument("--allow-test-mock", action="store_true", help="Allow Step 4 mock drafts in lifecycle tests only.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        payload = {"name": "lock_contracts", "status": "ok", "formal_logic": "implemented_step_4", "side_effects": "none"}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    required = ("reviewed", "review_log", "manifest_id", "manifest_hash", "locked_at", "locked_by", "first_scoring_started_at")
    missing = [field for field in required if not getattr(args, field)]
    if missing:
        print({"status": "invalid_args", "missing": missing}, file=sys.stderr)
        return 2
    try:
        results = lock_contracts(
            reviewed=args.reviewed,
            review_logs=args.review_log,
            locked_dir=args.locked_dir,
            contract_review_dir=args.contract_review_dir,
            manifest_id=args.manifest_id,
            manifest_hash=args.manifest_hash,
            locked_at=args.locked_at,
            locked_by=args.locked_by,
            first_scoring_started_at=args.first_scoring_started_at,
            allow_test_mock=args.allow_test_mock,
        )
        payload = {"status": "ok", "locked_count": len(results), "locks": [item.to_dict() for item in results]}
    except ContractLifecycleError as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
