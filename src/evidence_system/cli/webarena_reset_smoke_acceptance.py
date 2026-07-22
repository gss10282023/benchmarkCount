"""Build the fail-closed 3-host x 4-site WebArena reset-smoke acceptance."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from evidence_system.webarena_reset_acceptance import (
    build_reset_smoke_acceptance,
    write_reset_smoke_acceptance,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--receipts-root",
        default="experiments/step20/webarena_verified/environment_receipts/real_reset_smoke",
    )
    parser.add_argument("--site-lock", default="configs/webarena_verified_sites.lock.json")
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument(
        "--output",
        default=(
            "experiments/step20/webarena_verified/environment_receipts/"
            "real_reset_smoke_acceptance.json"
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_reset_smoke_acceptance(
        receipts_root=args.receipts_root,
        site_lock_path=args.site_lock,
        infra_config_path=args.infra_config,
    )
    write_reset_smoke_acceptance(args.output, payload)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        print(f"observed_receipts: {payload['counts']['observed_receipts']}/12")
        print(f"output: {args.output}")
        for reason in payload["blocking_reasons"]:
            print(f"blocking: {reason}")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
