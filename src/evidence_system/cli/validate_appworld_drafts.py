"""Strictly validate the frozen AppWorld 485-case Codex draft run."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.appworld_draft_acceptance import (
    DEFAULT_ACCEPTED_CASES_ROOT,
    DEFAULT_ACCEPTANCE_PATH,
    DEFAULT_CORRECTIONS_PATH,
    DEFAULT_FINAL_LOCK_PATH,
    DEFAULT_HASH_INDEX_PATH,
    DEFAULT_LOCK_PATH,
    validate_appworld_draft_final_lock,
    validate_appworld_draft_run,
    write_appworld_draft_acceptance,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="validate_appworld_drafts",
    responsibility=(
        "Fail closed unless all 485 AppWorld Codex drafts, attempts, sidecars, "
        "batch records, and locked hashes are exact."
    ),
    owner_module="evidence_system.contracts.appworld_draft_acceptance",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_appworld_drafts",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--lock", default=str(DEFAULT_LOCK_PATH))
    parser.add_argument("--cases-root", help="Immutable formal-run cases root; must equal the pre-run lock.")
    parser.add_argument("--accepted-cases-root", default=str(DEFAULT_ACCEPTED_CASES_ROOT))
    parser.add_argument("--corrections", default=str(DEFAULT_CORRECTIONS_PATH))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write-report",
        action="store_true",
        help="After all gates pass, write the hash index, acceptance report, and post-run final lock.",
    )
    mode.add_argument(
        "--verify-final-lock",
        action="store_true",
        help="Re-run the full transitive validation and verify an existing post-run final lock.",
    )
    parser.add_argument("--hash-index", default=str(DEFAULT_HASH_INDEX_PATH))
    parser.add_argument("--report", default=str(DEFAULT_ACCEPTANCE_PATH))
    parser.add_argument("--final-lock", default=str(DEFAULT_FINAL_LOCK_PATH))
    parser.add_argument("--json", action="store_true")
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
    try:
        if args.verify_final_lock:
            result = validate_appworld_draft_final_lock(
                final_lock_path=args.final_lock,
                lock_path=args.lock,
                accepted_cases_root=args.accepted_cases_root,
                corrections_path=args.corrections,
            )
        elif args.write_report:
            result = write_appworld_draft_acceptance(
                lock_path=args.lock,
                cases_root=args.cases_root,
                accepted_cases_root=args.accepted_cases_root,
                corrections_path=args.corrections,
                hash_index_path=args.hash_index,
                report_path=args.report,
                final_lock_path=args.final_lock,
            )
        else:
            result = validate_appworld_draft_run(
                lock_path=args.lock,
                cases_root=args.cases_root,
                accepted_cases_root=args.accepted_cases_root,
                corrections_path=args.corrections,
            )
    except (ContractLifecycleError, OSError, ValueError, KeyError) as exc:
        _emit({"status": "blocked", "reason": str(exc)}, as_json=args.json, file=sys.stderr)
        return 2
    _emit(result, as_json=args.json)
    return 0


def _emit(payload: dict[str, object], *, as_json: bool, file: object | None = None) -> None:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
        return
    for key, value in payload.items():
        print(f"{key}: {value}", file=stream)


if __name__ == "__main__":
    sys.exit(main())
