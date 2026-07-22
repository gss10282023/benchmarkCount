"""Freeze and strictly accept the canonical AppWorld GPT-5.6 Sol drafts."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.appworld_draft_acceptance_v56 import (
    DEFAULT_ACCEPTANCE_PATH,
    DEFAULT_ACCEPTED_CASES_ROOT,
    DEFAULT_CASES_ROOT,
    DEFAULT_CORRECTIONS_PATH,
    DEFAULT_FINAL_LOCK_PATH,
    DEFAULT_HASH_INDEX_PATH,
    DEFAULT_LOCK_PATH,
    prepare_appworld_draft_run_lock_v56,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="validate_appworld_drafts_v56",
    responsibility="Freeze and fail-closed accept exactly 485 AppWorld gpt-5.6-sol/xhigh Codex-login drafts.",
    owner_module="evidence_system.contracts.appworld_draft_acceptance_v56",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_appworld_drafts_v56",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument("--build-lock", action="store_true", help="Exclusively create the v4 pre-run lock.")
    mode.add_argument("--validate-lock", action="store_true", help="Recompute the v4 pre-run lock closure without formal outputs.")
    mode.add_argument("--write-canary-round-receipt", action="store_true", help="Exclusively validate and lock one completed strict canary round.")
    mode.add_argument("--write-canary-acceptance", action="store_true", help="Exclusively lock the three-round consecutive canary sequence.")
    mode.add_argument("--validate-canary-acceptance", action="store_true", help="Recompute the complete three-round canary receipt chain.")
    mode.add_argument("--write-acceptance", action="store_true", help="Materialize identity accepted cases and lock acceptance.")
    mode.add_argument("--verify-final-lock", action="store_true", help="Recompute the full transitive final-lock closure.")
    parser.add_argument("--lock", default=str(DEFAULT_LOCK_PATH))
    parser.add_argument("--cases-root", default=str(DEFAULT_CASES_ROOT))
    parser.add_argument("--accepted-cases-root", default=str(DEFAULT_ACCEPTED_CASES_ROOT))
    parser.add_argument("--corrections", default=str(DEFAULT_CORRECTIONS_PATH))
    parser.add_argument("--hash-index", default=str(DEFAULT_HASH_INDEX_PATH))
    parser.add_argument("--report", default=str(DEFAULT_ACCEPTANCE_PATH))
    parser.add_argument("--final-lock", default=str(DEFAULT_FINAL_LOCK_PATH))
    parser.add_argument("--canary-round", choices=["round_01", "round_02", "round_03"])
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        _emit({"status": "ok", "name": COMMAND.name, "responsibility": COMMAND.responsibility}, args.json)
        return 0
    try:
        if args.build_lock:
            result = prepare_appworld_draft_run_lock_v56(
                lock_path=args.lock,
                cases_root=args.cases_root,
            )
        elif args.validate_lock:
            from evidence_system.contracts.appworld_draft_acceptance_v56 import validate_appworld_draft_pre_run_lock_v56
            result = validate_appworld_draft_pre_run_lock_v56(lock_path=args.lock)
        elif args.write_canary_round_receipt:
            if args.canary_round is None:
                raise ContractLifecycleError("--write-canary-round-receipt requires --canary-round")
            from evidence_system.contracts.appworld_draft_acceptance_v56 import write_appworld_v56_canary_round_receipt
            result = write_appworld_v56_canary_round_receipt(round_id=args.canary_round)
        elif args.write_canary_acceptance:
            from evidence_system.contracts.appworld_draft_acceptance_v56 import write_appworld_v56_canary_acceptance
            result = write_appworld_v56_canary_acceptance()
        elif args.validate_canary_acceptance:
            from evidence_system.contracts.appworld_draft_acceptance_v56 import validate_appworld_v56_canary_acceptance
            result = validate_appworld_v56_canary_acceptance()
        elif args.write_acceptance:
            from evidence_system.contracts.appworld_draft_acceptance_v56 import write_appworld_draft_acceptance_v56
            result = write_appworld_draft_acceptance_v56(
                lock_path=args.lock,
                cases_root=args.cases_root,
                accepted_cases_root=args.accepted_cases_root,
                corrections_path=args.corrections,
                hash_index_path=args.hash_index,
                report_path=args.report,
                final_lock_path=args.final_lock,
            )
        elif args.verify_final_lock:
            from evidence_system.contracts.appworld_draft_acceptance_v56 import validate_appworld_draft_final_lock_v56
            result = validate_appworld_draft_final_lock_v56(
                final_lock_path=args.final_lock,
                lock_path=args.lock,
            )
        else:
            from evidence_system.contracts.appworld_draft_acceptance_v56 import validate_appworld_draft_formal_run_v56
            result = validate_appworld_draft_formal_run_v56(
                lock_path=args.lock,
                cases_root=args.cases_root,
            )
    except (ContractLifecycleError, OSError, ValueError, KeyError) as exc:
        _emit({"status": "blocked", "reason": str(exc)}, args.json, file=sys.stderr)
        return 2
    _emit(result, args.json)
    return 0


def _emit(payload: MappingLike, as_json: bool, file: object | None = None) -> None:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(dict(payload), indent=2, sort_keys=True), file=stream)
    else:
        for key, value in payload.items():
            print(f"{key}: {value}", file=stream)


MappingLike = dict[str, object]


if __name__ == "__main__":
    raise SystemExit(main())
