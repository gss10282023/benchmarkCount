"""Stage human-reviewed evidence contracts and review timing."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.review import review_contracts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.review_contracts")
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--draft", action="append", default=[], help="Draft contract file or directory. May be repeated.")
    parser.add_argument("--reviewed-dir", default="experiments/evidence_contracts/reviewed")
    parser.add_argument("--review-log-dir", default="results/reviews/contracts")
    parser.add_argument("--human-time-dir", default="results/human_time/contracts")
    parser.add_argument("--reviewer-id")
    parser.add_argument("--review-started-at")
    parser.add_argument("--review-finished-at")
    parser.add_argument("--review-action", action="append", default=[])
    parser.add_argument("--source-bundle-hash")
    parser.add_argument("--visible-input-hash")
    parser.add_argument("--source-hierarchy", action="append")
    parser.add_argument("--unsupported-requirements-removed", action="store_true")
    parser.add_argument("--marked-stronger-measurement", action="append", default=[])
    parser.add_argument("--draft-created-at")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        payload = {"name": "review_contracts", "status": "ok", "formal_logic": "implemented_step_4", "side_effects": "none"}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    missing = [name for name in ("reviewer_id", "review_started_at", "review_finished_at") if not getattr(args, name)]
    if missing or not args.draft:
        print({"status": "invalid_args", "missing": [*missing, *([] if args.draft else ["draft"])]}, file=sys.stderr)
        return 2
    try:
        results = review_contracts(
            drafts=args.draft,
            reviewed_dir=args.reviewed_dir,
            review_log_dir=args.review_log_dir,
            human_time_dir=args.human_time_dir,
            reviewer_id=args.reviewer_id,
            review_started_at=args.review_started_at,
            review_finished_at=args.review_finished_at,
            review_actions=args.review_action or ["checked source hierarchy"],
            source_bundle_hash=args.source_bundle_hash,
            visible_input_hash=args.visible_input_hash,
            source_hierarchy_applied=args.source_hierarchy,
            unsupported_requirements_removed=args.unsupported_requirements_removed,
            requirements_marked_stronger_measurement=args.marked_stronger_measurement,
            draft_created_at=args.draft_created_at,
        )
        payload = {"status": "ok", "reviewed_count": len(results), "reviews": [item.to_dict() for item in results]}
    except ContractLifecycleError as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
