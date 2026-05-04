"""Shared helpers for Step 2 CLI skeletons."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass(frozen=True)
class BootstrapCommand:
    name: str
    responsibility: str
    owner_module: str


def build_bootstrap_parser(command: BootstrapCommand) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"python -m evidence_system.cli.{command.name}",
        description=command.responsibility,
    )
    parser.add_argument(
        "--bootstrap-check",
        action="store_true",
        help="Return command metadata without executing formal experiment logic.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output.",
    )
    return parser


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")


def bootstrap_main(command: BootstrapCommand, argv: Sequence[str] | None = None) -> int:
    parser = build_bootstrap_parser(command)
    args = parser.parse_args(argv)
    payload = {
        **asdict(command),
        "status": "bootstrap_only" if args.bootstrap_check else "blocked",
        "formal_logic": "not_implemented_in_step_2",
        "side_effects": "none",
    }
    if args.bootstrap_check:
        emit(payload, args.json)
        return 0
    payload["reason"] = "Step 2 skeleton fails closed for formal actions."
    emit(payload, args.json)
    return 2


def run(command: BootstrapCommand) -> None:
    sys.exit(bootstrap_main(command))
