#!/usr/bin/env python3
"""Finalize an already-completed WebArena-Verified 24-slot pilot."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.orchestrator.webarena_verified_pilot_finalization import (  # noqa: E402
    PilotFinalizationError,
    finalize_completed_pilot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--active-secret-env",
        default="OPENROUTER_API_KEY",
        help="environment variable read only in memory for exact-match scanning",
    )
    parser.add_argument("--no-rebuild-aggregate", action="store_true")
    args = parser.parse_args()
    secret = os.environ.get(args.active_secret_env)
    try:
        result = finalize_completed_pilot(
            active_secret=secret,
            rebuild_aggregate=not args.no_rebuild_aggregate,
        )
    except PilotFinalizationError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": str(exc),
                    "paid_calls_made": 0,
                    "dotenv_read": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
