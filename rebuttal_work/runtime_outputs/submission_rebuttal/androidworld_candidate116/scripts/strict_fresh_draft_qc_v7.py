#!/usr/bin/env python3
"""Stable v7 entry point for the independent fresh-draft post-generation QC."""

from strict_fresh_draft_postgen_qc import QCFailure, main


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QCFailure as exc:
        import sys

        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
