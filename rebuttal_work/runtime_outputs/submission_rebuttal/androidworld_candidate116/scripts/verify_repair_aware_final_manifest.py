#!/usr/bin/env python3
"""Verify a native v2 repair-aware final manifest through the full validator.

This compatibility command deliberately accepts no legacy v1 handoff/final
schema.  It first proves that the supplied manifest binds the supplied v2
handoff, then invokes the same native validator used by canonical promotion.
That validator rechecks all 116 external root verdicts, both canonical trees,
all 116 case locks, every one of the 348 slot bindings, and runtime eligibility.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from repair_pipeline_common import RepairPipelineError, load_json, verify_file_binding
from repair_aware_final_common import HANDOFF_SCHEMA, verify_handoff
from semantic_review_common import SemanticReviewError
from validate_repair_aware_final_run import DEFAULT_LOCKS, DEFAULT_REPORT, validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-manifest", type=Path, required=True)
    parser.add_argument("--contracts-freeze", type=Path, required=True)
    parser.add_argument("--promotion-handoff", type=Path, required=True)
    parser.add_argument("--case-locks", type=Path, default=DEFAULT_LOCKS)
    parser.add_argument("--promotion-report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    final_path = args.final_manifest.resolve()
    freeze_path = args.contracts_freeze.resolve()
    handoff_path = args.promotion_handoff.resolve()

    context = verify_handoff(handoff_path)
    if context["handoff"].get("schema_version") != HANDOFF_SCHEMA:
        raise RepairPipelineError("promotion handoff is not the native v2 schema")
    final = load_json(final_path, "repair-aware final run manifest")
    bound_handoff = verify_file_binding(
        final.get("promotion_handoff"),
        "final manifest promotion handoff",
        inside_candidate=True,
    )
    if (
        bound_handoff != handoff_path
        or final["promotion_handoff"].get("handoff_sha256")
        != context["handoff"].get("handoff_sha256")
    ):
        raise RepairPipelineError("final manifest binds a different v2 promotion handoff")

    result = validate(
        argparse.Namespace(
            manifest=final_path,
            freeze=freeze_path,
            case_locks=args.case_locks.resolve(),
            promotion_report=args.promotion_report.resolve(),
            self_test=False,
        )
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
