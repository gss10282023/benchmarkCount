#!/usr/bin/env python3
"""Plan or explicitly execute the locked WebArena-Verified 8x3 pilot."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.orchestrator.webarena_verified_pilot_execution import (  # noqa: E402
    build_pilot_schedule,
    execute_pilot_schedule,
    materialize_canonical_pilot_schedule,
    validate_canonical_pilot_schedule,
)
from evidence_system.orchestrator.webarena_verified_run_control import (  # noqa: E402
    load_materialized_full_plan,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--ssh-key-path")
    parser.add_argument("--confirm-paid-pilot", default="")
    parser.add_argument(
        "--materialize-schedule",
        action="store_true",
        help="explicitly create/replace the canonical 24-job schedule before validation",
    )
    args = parser.parse_args()
    full = load_materialized_full_plan()
    pilot = build_pilot_schedule(full)
    if args.materialize_schedule:
        materialize_canonical_pilot_schedule(pilot, replace=True)
    schedule = validate_canonical_pilot_schedule(pilot)
    if not args.execute:
        print(
            "PASS: canonical locked 8-case/24-slot pilot is runnable; "
            f"jobs_sha256={schedule['jobs_sha256']}; no calls were made"
        )
        return 0
    if not args.ssh_key_path or args.confirm_paid_pilot != "RUN-24-PAID-PILOT":
        parser.error(
            "--execute requires --ssh-key-path and "
            "--confirm-paid-pilot RUN-24-PAID-PILOT"
        )
    results = execute_pilot_schedule(pilot, ssh_key_path=args.ssh_key_path)
    print(f"PASS: completed {len(results)} pilot slots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
