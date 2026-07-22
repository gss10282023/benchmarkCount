"""Build deterministic MiniWoB++ selections, source files, case packets, and source bundle."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.miniwob_case_selection import build_miniwob_case_selection


COMMAND = BootstrapCommand(
    name="build_miniwob_case_selection",
    responsibility="Build deterministic MiniWoB++ selections, source files, case packets, and source bundle.",
    owner_module="evidence_system.contracts.miniwob_case_selection",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.build_miniwob_case_selection", description=COMMAND.responsibility)
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument(
        "--source-infra-config",
        help="Source discovery/materialization infra; defaults to --infra-config.",
    )
    parser.add_argument("--agents-config", default="configs/agents.yaml")
    parser.add_argument(
        "--source-mode",
        choices=("remote", "local"),
        default="remote",
        help="Read BrowserGym/MiniWoB sources over SSH (default) or from paths in the local locked infra config.",
    )
    parser.add_argument("--main-manifest", default="experiments/experiment_manifest.yaml")
    parser.add_argument("--official-splits", default="experiments/official_splits")
    parser.add_argument("--selected-sources", default="experiments/official_splits/miniwob_selected_task_sources.json")
    parser.add_argument("--appendix-manifest", default="experiments/appendix/miniwob_manifest.yaml")
    parser.add_argument(
        "--appendix-source-bundle",
        default="experiments/evidence_contracts/source_bundles/miniwob_case_units_source_bundle.json",
    )
    parser.add_argument("--case-packets-root", default="experiments/case_packets")
    parser.add_argument("--selected-count", type=int, default=50)
    parser.add_argument("--selection-offset", type=int, default=0)
    parser.add_argument("--manifest-id")
    parser.add_argument(
        "--result-namespace",
        help="Optional locked run-set namespace written to the generated manifest.",
    )
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
        payload = build_miniwob_case_selection(
            infra_config_path=args.infra_config,
            source_infra_config_path=args.source_infra_config or args.infra_config,
            agents_config_path=args.agents_config,
            source_mode=args.source_mode,
            main_manifest_path=args.main_manifest,
            official_splits_root=args.official_splits,
            manifest_path=args.appendix_manifest,
            selected_sources_path=args.selected_sources,
            source_bundle_path=args.appendix_source_bundle,
            case_packets_root=args.case_packets_root,
            selected_count=args.selected_count,
            selection_offset=args.selection_offset,
            manifest_id=args.manifest_id,
            result_namespace=args.result_namespace,
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
