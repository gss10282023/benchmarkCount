"""Preflight, atomically materialize, or validate the AppWorld draft overlay."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.appworld_draft_overlay import (
    DEFAULT_ACCEPTED_CASES_ROOT,
    DEFAULT_CORRECTIONS_PATH,
    DEFAULT_FORMAL_LOCK_PATH,
    DEFAULT_REPAIR_LOCK_PATH,
    materialize_appworld_draft_overlay,
    prepare_appworld_draft_overlay,
    validate_appworld_draft_overlay,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="materialize_appworld_draft_overlay",
    responsibility=(
        "Create the immutable 485-case AppWorld accepted overlay from 472 formal "
        "cases, 12 validated location candidates, and one audited security correction."
    ),
    owner_module="evidence_system.contracts.appworld_draft_overlay",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.materialize_appworld_draft_overlay",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    for command, help_text in (
        ("prepare", "Run all gates read-only and require both outputs to be absent."),
        ("materialize", "Atomically create the accepted tree and exclusive provenance manifest."),
        ("validate", "Recompute and validate an existing overlay read-only."),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("--formal-lock", default=str(DEFAULT_FORMAL_LOCK_PATH))
        child.add_argument("--repair-lock", default=str(DEFAULT_REPAIR_LOCK_PATH))
        child.add_argument("--accepted-cases-root", default=str(DEFAULT_ACCEPTED_CASES_ROOT))
        child.add_argument("--corrections", default=str(DEFAULT_CORRECTIONS_PATH))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        _emit(
            {
                "status": "ok",
                "name": COMMAND.name,
                "responsibility": COMMAND.responsibility,
                "owner_module": COMMAND.owner_module,
            },
            as_json=args.json,
        )
        return 0
    if not args.command:
        build_parser().print_help(sys.stderr)
        return 2
    kwargs = {
        "formal_lock_path": args.formal_lock,
        "repair_lock_path": args.repair_lock,
        "accepted_cases_root": args.accepted_cases_root,
        "corrections_path": args.corrections,
    }
    try:
        if args.command == "prepare":
            result = prepare_appworld_draft_overlay(**kwargs)
        elif args.command == "materialize":
            result = materialize_appworld_draft_overlay(**kwargs)
        else:
            result = validate_appworld_draft_overlay(**kwargs)
    except (ContractLifecycleError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        _emit({"status": "blocked", "reason": str(exc)}, as_json=args.json, file=sys.stderr)
        return 2
    _emit(result, as_json=args.json)
    return 0


def _emit(payload: Mapping[str, object], *, as_json: bool, file: object | None = None) -> None:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(dict(payload), indent=2, sort_keys=True), file=stream)
        return
    for key, value in payload.items():
        print(f"{key}: {value}", file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
