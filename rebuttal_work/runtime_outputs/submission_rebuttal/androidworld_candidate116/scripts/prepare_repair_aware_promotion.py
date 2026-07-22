#!/usr/bin/env python3
"""Fail closed for the superseded v1 promotion-handoff workflow.

The v2 handoff accepted by canonical promotion is created only by
``finalize_effective_semantic_reviews.py`` after effective QC, semantic-model
proposals, independent validation, and 116 pre-existing external root-agent
case verdicts all pass.  Keeping this legacy command as an explicit refusal
prevents old automation from producing a weaker artifact labelled eligible.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repair_pipeline_common import RepairPipelineError
from semantic_review_common import SemanticReviewError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    # Retain the historical flags so old automation receives the deliberate
    # fail-closed message rather than silently selecting a different workflow.
    parser.add_argument("--effective-manifest", type=Path)
    parser.add_argument("--effective-qc-root", type=Path)
    parser.add_argument("--human-review-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    parse_args()
    raise RepairPipelineError(
        "deprecated fail-closed command: use finalize_effective_semantic_reviews.py "
        "to build the v2 handoff after effective QC, semantic validation, and "
        "116/116 external root-agent verdict acceptance"
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
