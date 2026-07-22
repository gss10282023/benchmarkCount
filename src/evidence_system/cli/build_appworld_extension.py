"""Build the frozen 68-normal + 417-challenge AppWorld extension definition."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.appworld_extension import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_BASE_DBS_ROOT,
    DEFAULT_CHALLENGE_SPLIT,
    DEFAULT_CURRENT_CATALOG,
    DEFAULT_DATA_VERSION_PATH,
    DEFAULT_NORMAL_SPLIT,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_TASKS_ROOT,
    build_appworld_extension,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="build_appworld_extension",
    responsibility="Freeze and build the exact 485-case AppWorld full-test extension definition.",
    owner_module="evidence_system.contracts.appworld_extension",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.build_appworld_extension",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--normal-split", default=str(DEFAULT_NORMAL_SPLIT))
    parser.add_argument("--challenge-split", default=str(DEFAULT_CHALLENGE_SPLIT))
    parser.add_argument("--current-catalog", default=str(DEFAULT_CURRENT_CATALOG))
    parser.add_argument("--tasks-root", default=str(DEFAULT_TASKS_ROOT))
    parser.add_argument("--data-version", default=str(DEFAULT_DATA_VERSION_PATH))
    parser.add_argument("--base-dbs-root", default=str(DEFAULT_BASE_DBS_ROOT))
    parser.add_argument("--agents-config", default=str(DEFAULT_AGENTS_CONFIG))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        _emit(
            {
                "name": COMMAND.name,
                "responsibility": COMMAND.responsibility,
                "owner_module": COMMAND.owner_module,
                "status": "ok",
            },
            args.json,
        )
        return 0
    try:
        payload = build_appworld_extension(
            output_root=args.output_root,
            normal_split_path=args.normal_split,
            challenge_split_path=args.challenge_split,
            current_catalog_path=args.current_catalog,
            tasks_root=args.tasks_root,
            data_version_path=args.data_version,
            base_dbs_root=args.base_dbs_root,
            agents_config_path=args.agents_config,
        )
    except (ContractLifecycleError, OSError) as exc:
        _emit({"status": "blocked", "reason": str(exc)}, args.json, file=sys.stderr)
        return 2
    _emit(payload, args.json)
    return 0


def _emit(payload: dict[str, object], as_json: bool, *, file: object = None) -> None:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
    else:
        for key, value in payload.items():
            print(f"{key}: {value}", file=stream)


if __name__ == "__main__":
    sys.exit(main())

