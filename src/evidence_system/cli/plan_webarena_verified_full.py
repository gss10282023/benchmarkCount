"""Validate and optionally materialize the frozen WebArena-Verified full schedule."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from evidence_system.orchestrator.webarena_verified_full import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_DRY_RUN_ACCEPTANCE,
    DEFAULT_JOBS_ROOT,
    DEFAULT_LOCKED_CONTRACTS_ROOT,
    DEFAULT_MANIFEST,
    DEFAULT_NATIVE_CLAIM_ACCEPTANCE,
    DEFAULT_NATIVE_CLAIM_INDEX,
    DEFAULT_SOURCE_BUNDLE,
    DEFAULT_SITE_LOCK,
    DEFAULT_TASK_CONTRACT_INDEX,
    WebArenaFullScheduleError,
    blocked_dry_run_acceptance,
    plan_full_schedule,
    write_acceptance,
    write_jobs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fail-closed dry run for the frozen WebArena-Verified v1.2.3 "
            "812-case / 2,436-record-slot schedule."
        )
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--source-bundle", default=str(DEFAULT_SOURCE_BUNDLE))
    parser.add_argument(
        "--task-contract-index", default=str(DEFAULT_TASK_CONTRACT_INDEX)
    )
    parser.add_argument("--agents-config", default=str(DEFAULT_AGENTS_CONFIG))
    parser.add_argument("--site-lock", default=str(DEFAULT_SITE_LOCK))
    parser.add_argument(
        "--native-claim-index", default=str(DEFAULT_NATIVE_CLAIM_INDEX)
    )
    parser.add_argument(
        "--native-claim-acceptance", default=str(DEFAULT_NATIVE_CLAIM_ACCEPTANCE)
    )
    parser.add_argument(
        "--locked-contracts-root", default=str(DEFAULT_LOCKED_CONTRACTS_ROOT)
    )
    parser.add_argument(
        "--acceptance-output", default=str(DEFAULT_DRY_RUN_ACCEPTANCE)
    )
    parser.add_argument("--jobs-output", default=str(DEFAULT_JOBS_ROOT))
    parser.add_argument(
        "--write-jobs",
        action="store_true",
        help="materialize jobs only after every formal gate passes",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing jobs directory; valid only with --write-jobs",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.replace and not args.write_jobs:
        raise SystemExit("--replace requires --write-jobs")

    plan_kwargs = {
        "manifest_path": args.manifest,
        "source_bundle_path": args.source_bundle,
        "task_contract_index_path": args.task_contract_index,
        "agents_config_path": args.agents_config,
        "site_lock_path": args.site_lock,
        "native_claim_index_path": args.native_claim_index,
        "native_claim_acceptance_path": args.native_claim_acceptance,
        "locked_contracts_root": args.locked_contracts_root,
    }
    try:
        plan = plan_full_schedule(**plan_kwargs)
        receipt = dict(plan.acceptance)
        if args.write_jobs:
            receipt["dry_run"] = False
            receipt["materialization"] = write_jobs(
                plan,
                output_root=args.jobs_output,
                replace=args.replace,
            )
        else:
            receipt["materialization"] = {
                "jobs_written": False,
                "jobs_root": str(Path(args.jobs_output)),
            }
        output = write_acceptance(args.acceptance_output, receipt)
        print(
            f"PASS: {len(plan.jobs)} exact record slots validated; "
            f"receipt={output}"
        )
        return 0
    except WebArenaFullScheduleError as exc:
        receipt = blocked_dry_run_acceptance(
            str(exc),
            manifest_path=args.manifest,
            source_bundle_path=args.source_bundle,
            task_contract_index_path=args.task_contract_index,
            agents_config_path=args.agents_config,
            site_lock_path=args.site_lock,
            native_claim_index_path=args.native_claim_index,
            native_claim_acceptance_path=args.native_claim_acceptance,
            locked_contracts_root=args.locked_contracts_root,
        )
        output = write_acceptance(args.acceptance_output, receipt)
        print(f"BLOCKED: {exc}; receipt={output}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
