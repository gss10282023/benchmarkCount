#!/usr/bin/env python3
"""Fail closed for the superseded direct candidate116 promotion workflow.

This legacy command used draft-wave reviews as its authority and could write
the same canonical paths as the repair-aware v2 promoter.  It is intentionally
disabled: canonical publication must go through
``promote_repair_aware_final_run.py`` and therefore prove effective QC,
accepted semantic proposals, independent validation, and 116/116 external
root-agent case verdicts before create-once publication.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


class PromotionError(RuntimeError):
    """Raised for every attempted legacy promotion."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    # Preserve historical flags so existing automation receives an explicit
    # refusal instead of an argparse compatibility failure.
    parser.add_argument("--review-root", type=Path)
    parser.add_argument("--runtime-config", type=Path)
    parser.add_argument("--draft-prelock", type=Path)
    parser.add_argument("--draft-generation-config", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--frozen-at")
    return parser.parse_args()


def main() -> int:
    parse_args()
    raise PromotionError(
        "legacy direct promotion is disabled fail-closed; use "
        "promote_repair_aware_final_run.py with a validated v2 handoff containing "
        "effective QC, semantic validation, and 116/116 external root-agent verdicts"
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PromotionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
