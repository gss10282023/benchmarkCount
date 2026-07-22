#!/usr/bin/env python3
"""Issue the exact, append-only recovery authorization for a stopped full run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.core.hashing import sha256_file  # noqa: E402
from evidence_system.core.paths import resolve_repo_path  # noqa: E402
from evidence_system.orchestrator.webarena_verified_run_control import (  # noqa: E402
    CIRCUIT_RECOVERY_ISSUE_CONFIRMATION,
    DEFAULT_CIRCUIT_RECOVERY_RECEIPT,
    DEFAULT_JOBS_INDEX,
    DEFAULT_REMOTE_RETENTION_CANARY_ACCEPTANCE,
    WebArenaRunControlError,
    build_circuit_recovery_receipt,
    monitor_namespace,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key-path", required=True)
    parser.add_argument("--trace-heavy-canary-acceptance", required=True)
    parser.add_argument(
        "--credential-recovery-canary-acceptance",
        default=str(DEFAULT_REMOTE_RETENTION_CANARY_ACCEPTANCE),
    )
    parser.add_argument("--junit-report", required=True)
    parser.add_argument("--jobs-index", default=str(DEFAULT_JOBS_INDEX))
    parser.add_argument(
        "--site-lock", default="configs/webarena_verified_sites.lock.json"
    )
    parser.add_argument("--output", default=str(DEFAULT_CIRCUIT_RECOVERY_RECEIPT))
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != CIRCUIT_RECOVERY_ISSUE_CONFIRMATION:
        parser.error(
            f"--confirm must equal {CIRCUIT_RECOVERY_ISSUE_CONFIRMATION}"
        )
    try:
        snapshot = monitor_namespace(
            mode="full",
            index_path=args.jobs_index,
            site_lock_path=args.site_lock,
            ssh_key_path=args.ssh_key_path,
            write_outputs=True,
        )
        payload = build_circuit_recovery_receipt(
            snapshot=snapshot,
            jobs_index_path=args.jobs_index,
            trace_heavy_canary_acceptance_path=(
                args.trace_heavy_canary_acceptance
            ),
            credential_recovery_canary_acceptance_path=(
                args.credential_recovery_canary_acceptance
            ),
            junit_report_path=args.junit_report,
            ssh_key_path=args.ssh_key_path,
            site_lock_path=args.site_lock,
            confirmation=args.confirm,
            output_path=args.output,
        )
    except (OSError, ValueError, WebArenaRunControlError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": "webarena_verified_circuit_recovery_error/v1",
                    "status": "blocked",
                    "error_type": type(exc).__name__,
                    "secret_material_recorded": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    output = resolve_repo_path(args.output)
    print(
        json.dumps(
            {
                "schema_version": payload["schema_version"],
                "status": payload["status"],
                "recovery_id": payload["recovery_id"],
                "output_path": str(output.relative_to(ROOT)),
                "output_sha256": sha256_file(output),
                "secret_material_recorded": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
