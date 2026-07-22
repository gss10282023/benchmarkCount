"""Freeze or verify the strict AppWorld GPT-5.6 definition ledger."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.appworld_refreeze_v56 import (
    DEFAULT_MATERIALIZATION_ROOT,
    MINIMUM_STABILITY_WINDOW_SECONDS,
    freeze_appworld_definition_v56,
    verify_appworld_definition_refreeze_v56,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="refreeze_appworld_drafts_v56",
    responsibility=(
        "Publish or verify the O_EXCL AppWorld GPT-5.6 definition ledger after a strict stability window."
    ),
    owner_module="evidence_system.contracts.appworld_refreeze_v56",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.refreeze_appworld_drafts_v56",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument(
        "--materialization-root", default=str(DEFAULT_MATERIALIZATION_ROOT)
    )
    parser.add_argument("--output")
    parser.add_argument(
        "--stability-window-seconds",
        type=int,
        default=MINIMUM_STABILITY_WINDOW_SECONDS,
    )
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        return _emit(
            {
                "status": "ok",
                "name": COMMAND.name,
                "responsibility": COMMAND.responsibility,
                "owner_module": COMMAND.owner_module,
            },
            args.json,
        )
    if (
        args.verify_only
        and args.stability_window_seconds != MINIMUM_STABILITY_WINDOW_SECONDS
    ):
        return _emit(
            {
                "status": "blocked",
                "reason": "--verify-only cannot set a stability window",
            },
            args.json,
            file=sys.stderr,
            code=2,
        )
    try:
        if args.verify_only:
            result = verify_appworld_definition_refreeze_v56(
                materialization_root=args.materialization_root,
                ledger_path=args.output,
            )
        else:
            result = freeze_appworld_definition_v56(
                materialization_root=args.materialization_root,
                output_path=args.output,
                stability_window_seconds=args.stability_window_seconds,
            )
    except (ContractLifecycleError, OSError, ValueError) as exc:
        return _emit(
            {"status": "blocked", "reason": str(exc)},
            args.json,
            file=sys.stderr,
            code=2,
        )
    return _emit(result, args.json)


def _emit(
    payload: Mapping[str, object] | dict[str, object],
    as_json: bool,
    *,
    file: object = None,
    code: int = 0,
) -> int:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
    else:
        for key, value in payload.items():
            print(f"{key}: {value}", file=stream)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
