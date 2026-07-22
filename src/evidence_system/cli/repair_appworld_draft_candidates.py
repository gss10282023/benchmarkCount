"""Freeze, generate, or validate isolated AppWorld draft repair candidates."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.appworld_draft_candidate_repair import (
    DEFAULT_FORMAL_LOCK_PATH,
    DEFAULT_REPAIR_SUPPLEMENT,
    prepare_candidate_repair_lock,
    run_candidate_repairs,
    validate_existing_candidates,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="repair_appworld_draft_candidates",
    responsibility=(
        "Generate exactly 12 AppWorld source-location repair candidates in an "
        "isolated namespace without promoting or changing formal drafts."
    ),
    owner_module="evidence_system.contracts.appworld_draft_candidate_repair",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.repair_appworld_draft_candidates",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    lock_parser = subparsers.add_parser("prepare-lock", help="Write a separate immutable candidate repair lock.")
    lock_parser.add_argument("--subset-ids", required=True)
    lock_parser.add_argument("--repair-lock", required=True)
    lock_parser.add_argument("--candidate-output-root", required=True)
    lock_parser.add_argument("--formal-lock", default=str(DEFAULT_FORMAL_LOCK_PATH))
    lock_parser.add_argument("--prompt-supplement", default=str(DEFAULT_REPAIR_SUPPLEMENT))

    run_parser = subparsers.add_parser("run", help="Generate candidates through logged-in Codex CLI; no promotion.")
    run_parser.add_argument("--repair-lock", required=True)
    run_parser.add_argument(
        "--expected-repair-lock-sha256",
        required=True,
        help="Caller-anchored SHA-256 emitted by prepare-lock; generation refuses a drifted lock.",
    )

    validate_parser = subparsers.add_parser("validate", help="Re-run strict candidate validation read-only.")
    validate_parser.add_argument("--repair-lock", required=True)
    validate_parser.add_argument(
        "--expected-repair-lock-sha256",
        required=True,
        help="Caller-anchored SHA-256 emitted by prepare-lock; validation refuses a drifted lock.",
    )
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
    try:
        if args.command == "prepare-lock":
            result = prepare_candidate_repair_lock(
                subset_ids_path=args.subset_ids,
                repair_lock_path=args.repair_lock,
                candidate_output_root=args.candidate_output_root,
                formal_lock_path=args.formal_lock,
                prompt_supplement_path=args.prompt_supplement,
            )
        elif args.command == "run":
            result = run_candidate_repairs(
                args.repair_lock,
                expected_repair_lock_sha256=args.expected_repair_lock_sha256,
            )
        else:
            result = validate_existing_candidates(
                args.repair_lock,
                expected_repair_lock_sha256=args.expected_repair_lock_sha256,
            )
    except (ContractLifecycleError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        _emit({"status": "blocked", "reason": str(exc)}, as_json=args.json, file=sys.stderr)
        return 2
    _emit(result, as_json=args.json)
    if args.command in {"run", "validate"} and result.get("status") in {
        "failed",
        "candidate_generation_failed_validation",
    }:
        return 1
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
