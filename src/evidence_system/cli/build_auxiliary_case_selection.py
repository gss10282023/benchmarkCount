"""Build AndroidWorld and WorkArena appendix case selections and packets."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.auxiliary_case_selection import build_auxiliary_case_selection
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="build_auxiliary_case_selection",
    responsibility="Build deterministic appendix selections, source files, case packets, and source bundle for AndroidWorld and WorkArena.",
    owner_module="evidence_system.contracts.auxiliary_case_selection",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.build_auxiliary_case_selection", description=COMMAND.responsibility)
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument("--main-manifest", default="experiments/experiment_manifest.yaml")
    parser.add_argument("--official-splits", default="experiments/official_splits")
    parser.add_argument("--appendix-manifest", default="experiments/appendix/androidworld_workarena_manifest.yaml")
    parser.add_argument("--appendix-source-bundle", default="experiments/evidence_contracts/source_bundles/appendix_androidworld_workarena_source_bundle.json")
    parser.add_argument("--case-packets-root", default="experiments/case_packets")
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
        payload = build_auxiliary_case_selection(
            infra_config_path=args.infra_config,
            main_manifest_path=args.main_manifest,
            official_splits_root=args.official_splits,
            appendix_manifest_path=args.appendix_manifest,
            appendix_source_bundle_path=args.appendix_source_bundle,
            case_packets_root=args.case_packets_root,
        )
    except ContractLifecycleError as exc:
        result = {"status": "blocked", "reason": str(exc)}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"status: blocked\nreason: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
