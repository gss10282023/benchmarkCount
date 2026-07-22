#!/usr/bin/env python3
"""Fail closed for the superseded legacy candidate116 final-lock schema.

Only ``validate_repair_aware_final_run.py`` may validate a canonical candidate
run.  It revalidates the v2 handoff, all 116 root-agent verdicts, canonical
draft/contract byte identity, 348 slot bindings, and truthful runtime gates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


class ValidationFailure(RuntimeError):
    """Raised for every attempted legacy validation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--case-locks", type=Path)
    return parser.parse_args()


def main() -> int:
    parse_args()
    raise ValidationFailure(
        "legacy final-lock validation is disabled fail-closed; use "
        "validate_repair_aware_final_run.py for the native v2 chain"
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
