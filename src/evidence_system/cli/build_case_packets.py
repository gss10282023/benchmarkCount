"""Build local raw case directories and case_packet.md files for selected cases."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.case_packets import build_case_packets
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="build_case_packets",
    responsibility="Build local raw case directories and case_packet.md files for selected cases.",
    owner_module="evidence_system.contracts.case_packets",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.build_case_packets", description=COMMAND.responsibility)
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--manifest", default="experiments/experiment_manifest.yaml")
    parser.add_argument("--official-splits", default="experiments/official_splits")
    parser.add_argument("--output-root", default="experiments/case_packets")
    parser.add_argument("--source-mode", choices=("local", "remote"), default="local")
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--per-domain-limit", type=int)
    parser.add_argument("--case-unit-id", action="append", dest="case_unit_ids")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bootstrap_check:
        payload = {
            "name": COMMAND.name,
            "responsibility": COMMAND.responsibility,
            "owner_module": COMMAND.owner_module,
            "status": "ok",
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    try:
        results = build_case_packets(
            manifest_path=args.manifest,
            official_splits_path=args.official_splits,
            output_root=args.output_root,
            source_mode=args.source_mode,
            infra_config_path=args.infra_config,
            limit=args.limit,
            per_domain_limit=args.per_domain_limit,
            case_unit_ids=args.case_unit_ids,
        )
    except ContractLifecycleError as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"status: blocked\nreason: {exc}", file=sys.stderr)
        return 2
    payload = {"status": "ok", "built_count": len(results), "built": [result.to_dict() for result in results]}
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
