"""Final fail-closed freeze for the 949-case AgentDojo checklist lifecycle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_CASE_CHECKLIST_LOCK,
    DEFAULT_CASE_CHECKLIST_LOCK_ACCEPTANCE,
    DEFAULT_CASE_PACKETS,
    DEFAULT_DRAFT_BUDGET_PLAN,
    DEFAULT_DRAFT_INPUT_LOCK,
    DEFAULT_DRAFT_REVIEW_CONFIG,
    DEFAULT_DRAFT_REVIEW_INDEX,
    DEFAULT_DRAFT_REVIEW_REPORT,
    DEFAULT_DRAFT_ROOT,
    DEFAULT_INFRA_CONFIG,
    DEFAULT_LOCK,
    DEFAULT_MANIFEST,
    DEFAULT_RESULT_NAMESPACE_LOCK,
    DEFAULT_SCORE_PROMPT,
    DEFAULT_SCORE_SCHEMA,
    DEFAULT_SOURCE_BUNDLE,
    freeze_agentdojo_full_checklists,
    verify_checklist_freeze_lock,
)
from evidence_system.contracts.common import ContractLifecycleError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-bundle", type=Path, default=DEFAULT_SOURCE_BUNDLE)
    parser.add_argument(
        "--case-packet-root",
        type=Path,
        default=DEFAULT_CASE_PACKETS / "agentdojo",
    )
    parser.add_argument("--draft-root", type=Path, default=DEFAULT_DRAFT_ROOT)
    parser.add_argument(
        "--resolved-config", type=Path, default=DEFAULT_DRAFT_REVIEW_CONFIG
    )
    parser.add_argument("--input-lock", type=Path, default=DEFAULT_DRAFT_INPUT_LOCK)
    parser.add_argument("--budget-plan", type=Path, default=DEFAULT_DRAFT_BUDGET_PLAN)
    parser.add_argument(
        "--lifecycle-report", type=Path, default=DEFAULT_DRAFT_REVIEW_REPORT
    )
    parser.add_argument(
        "--lifecycle-index", type=Path, default=DEFAULT_DRAFT_REVIEW_INDEX
    )
    parser.add_argument("--case-lock", type=Path, default=DEFAULT_CASE_CHECKLIST_LOCK)
    parser.add_argument(
        "--lock-acceptance",
        type=Path,
        default=DEFAULT_CASE_CHECKLIST_LOCK_ACCEPTANCE,
    )
    parser.add_argument("--score-prompt", type=Path, default=DEFAULT_SCORE_PROMPT)
    parser.add_argument("--score-schema", type=Path, default=DEFAULT_SCORE_SCHEMA)
    parser.add_argument("--agents-config", type=Path, default=DEFAULT_AGENTS_CONFIG)
    parser.add_argument("--infra-config", type=Path, default=DEFAULT_INFRA_CONFIG)
    parser.add_argument(
        "--result-namespace-root",
        type=Path,
        default=DEFAULT_RESULT_NAMESPACE_LOCK.parent,
        help=(
            "Reserved production result namespace (fixed; a differing value is "
            "rejected)."
        ),
    )
    parser.add_argument(
        "--score-result-root",
        type=Path,
        action="append",
        default=None,
        help=(
            "Additional formal score namespace that must be absent/empty. The two "
            "canonical score namespaces are always audited; repeat for extras."
        ),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_LOCK)
    parser.add_argument(
        "--replace-stale-lock",
        action="store_true",
        help="Replace a differing prior lock only with an exact compare-and-swap digest.",
    )
    parser.add_argument("--expected-previous-lock-sha256")
    parser.add_argument("--locked-at")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Recompute and compare the v2 lock without writing anything.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verify_only and (
        args.replace_stale_lock
        or args.expected_previous_lock_sha256 is not None
        or args.locked_at is not None
    ):
        print(
            "--verify-only cannot be combined with replacement or timestamp options",
        )
        return 2
    if args.replace_stale_lock != (args.expected_previous_lock_sha256 is not None):
        print(
            "--replace-stale-lock and --expected-previous-lock-sha256 must be supplied together",
        )
        return 2

    overrides = {
        "manifest_path": args.manifest,
        "source_bundle_path": args.source_bundle,
        "case_packet_root": args.case_packet_root,
        "draft_root": args.draft_root,
        "resolved_config_path": args.resolved_config,
        "input_lock_path": args.input_lock,
        "budget_plan_path": args.budget_plan,
        "lifecycle_report_path": args.lifecycle_report,
        "lifecycle_index_path": args.lifecycle_index,
        "case_lock_path": args.case_lock,
        "lock_acceptance_path": args.lock_acceptance,
        "score_prompt_path": args.score_prompt,
        "score_schema_path": args.score_schema,
        "agents_config_path": args.agents_config,
        "infra_config_path": args.infra_config,
        "result_namespace_root": args.result_namespace_root,
        "score_result_roots": tuple(args.score_result_root or ()),
    }
    try:
        if args.verify_only:
            result = verify_checklist_freeze_lock(lock_path=args.output, **overrides)
            action = "verified"
        else:
            result = freeze_agentdojo_full_checklists(
                output_path=args.output,
                replace_stale_lock=args.replace_stale_lock,
                expected_previous_lock_sha256=args.expected_previous_lock_sha256,
                locked_at=args.locked_at,
                **overrides,
            )
            action = "replaced" if result.replaced else "frozen"
    except (ContractLifecycleError, OSError, ValueError) as exc:
        print(str(exc))
        return 2
    print(
        json.dumps(
            {
                "action": action,
                "lock_path": str(result.lock_path),
                "lock_sha256": result.lock_sha256,
                "counts": result.snapshot["counts"],
                "formal_results_and_scores_are_empty": result.snapshot[
                    "formal_output_precondition"
                ]["formal_results_and_scores_are_empty"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
