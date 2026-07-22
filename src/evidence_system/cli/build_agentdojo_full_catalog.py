"""Build the pinned AgentDojo v1.2.2 full source catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.agentdojo_full_catalog import (
    DEFAULT_PAIRED_CANDIDATES_PATH,
    DEFAULT_SELECTED_SOURCES_PATH,
    build_agentdojo_full_catalog,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="build_agentdojo_full_catalog",
    responsibility="Build and strictly verify the pinned 949-case AgentDojo v1.2.2 direct source catalog.",
    owner_module="evidence_system.contracts.agentdojo_full_catalog",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.build_agentdojo_full_catalog",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--paired-candidates", default=DEFAULT_PAIRED_CANDIDATES_PATH)
    parser.add_argument("--output", default=DEFAULT_SELECTED_SOURCES_PATH)
    parser.add_argument(
        "--agentdojo-repo",
        help="Clean official AgentDojo v0.1.35 git checkout; inferred for editable installs when omitted.",
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
        payload = build_agentdojo_full_catalog(
            paired_candidates_path=args.paired_candidates,
            output_path=args.output,
            agentdojo_repo_path=args.agentdojo_repo,
        )
    except ContractLifecycleError as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"status: blocked\nreason: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
