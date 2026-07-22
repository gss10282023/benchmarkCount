"""Publish or verify the immutable AgentDojo 949-case checklist_freeze/v2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evidence_system.contracts.agentdojo_checklist_freeze_v2 import (
    CHECKLIST_REVIEW_POST_LOCK_GATE_MODE,
    DEFAULT_CHECKLIST_FREEZE_V2,
    DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    DEFAULT_REVIEW_PREFLIGHT_RECEIPT,
    DEFAULT_REVIEW_QUIESCENCE_RECEIPT,
    capture_review_quiescence_receipt,
    checklist_freeze_v2_invalidation_path,
    freeze_agentdojo_full_checklists_v2,
    preflight_agentdojo_full_review_currentness,
    publish_review_currentness_preflight_receipt,
    verify_checklist_freeze_v2,
)
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
    DEFAULT_MANIFEST,
    DEFAULT_SCORE_PROMPT,
    DEFAULT_SCORE_SCHEMA,
    DEFAULT_SOURCE_BUNDLE,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object


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
        "--lifecycle-code-snapshot-root",
        type=Path,
        help=(
            "Sparse immutable root for lifecycle-code files whose locked hashes no "
            "longer match the live repository; requires exact locked hashes."
        ),
    )
    parser.add_argument(
        "--derive-per-case-review-run",
        action="store_true",
        help=(
            "In the guarded v2 compatibility context, derive each accepted "
            "case's immutable review_attempts run instead of trusting the global "
            "resume report run_id."
        ),
    )
    parser.add_argument(
        "--derive-review-attempt-state-machine",
        action="store_true",
        help=(
            "In the guarded v2 compatibility context, validate and bind every "
            "successful, failed, and deterministically rejected review attempt "
            "without rewriting the locked lifecycle artifacts."
        ),
    )
    parser.add_argument(
        "--derive-generation-attempt-state-machine",
        action="store_true",
        help=(
            "In the same guarded v2 compatibility context, validate and bind "
            "every failed and successful draft-generation retry without rewriting "
            "the locked batch artifacts."
        ),
    )
    parser.add_argument(
        "--score-result-root",
        type=Path,
        action="append",
        default=None,
        help="Additional score namespace that must remain empty before freeze.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_CHECKLIST_FREEZE_V2)
    parser.add_argument("--frozen-at")
    parser.add_argument(
        "--preflight-output",
        type=Path,
        help="Optional destination-absent immutable receipt for a passed preflight.",
    )
    parser.add_argument(
        "--review-preflight-receipt",
        type=Path,
        default=DEFAULT_REVIEW_PREFLIGHT_RECEIPT,
        help="Passed preflight receipt required by explicit read-only tree sealing.",
    )
    parser.add_argument(
        "--review-quiescence-receipt",
        type=Path,
        default=DEFAULT_REVIEW_QUIESCENCE_RECEIPT,
    )
    parser.add_argument(
        "--seal-draft-tree-read-only",
        action="store_true",
        help=(
            "Only with --capture-review-quiescence: after a current 949-case "
            "preflight receipt, remove write bits from the draft tree."
        ),
    )
    parser.add_argument(
        "--post-lock-currentness-seal",
        action="store_true",
        help=(
            "Only with --capture-review-quiescence and "
            "--seal-draft-tree-read-only: replace the legacy pre-lock gate with "
            "a complete 949-lock/acceptance/review/empty-output snapshot gate."
        ),
    )
    parser.add_argument(
        "--quiescence-max-age-seconds",
        type=int,
        default=DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--preflight-review-currentness",
        action="store_true",
        help=(
            "Before the legacy batch locker, require 949 current accepted review "
            "lifecycles and destination-absent lock outputs without writing anything."
        ),
    )
    mode.add_argument(
        "--capture-review-quiescence",
        action="store_true",
        help=(
            "Capture a machine-generated zero-review-process receipt; optionally "
            "seal the already-preflighted draft tree read-only."
        ),
    )
    mode.add_argument(
        "--verify-only",
        action="store_true",
        help="Recompute the entire input graph and verify without writing.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (
        args.verify_only
        or args.preflight_review_currentness
        or args.capture_review_quiescence
    ) and args.frozen_at is not None:
        print("read-only preflight/verify modes cannot be combined with --frozen-at")
        return 2
    if args.seal_draft_tree_read_only and not args.capture_review_quiescence:
        print("--seal-draft-tree-read-only requires --capture-review-quiescence")
        return 2
    if args.post_lock_currentness_seal and not (
        args.capture_review_quiescence and args.seal_draft_tree_read_only
    ):
        print(
            "--post-lock-currentness-seal requires --capture-review-quiescence "
            "and --seal-draft-tree-read-only"
        )
        return 2
    if args.preflight_output is not None and not args.preflight_review_currentness:
        print("--preflight-output requires --preflight-review-currentness")
        return 2
    if args.lifecycle_code_snapshot_root is not None and (
        args.preflight_review_currentness
        or (args.capture_review_quiescence and not args.post_lock_currentness_seal)
    ):
        print(
            "--lifecycle-code-snapshot-root is only valid for post-lock capture, "
            "freeze, or freeze verification"
        )
        return 2
    compatibility_switches = (
        args.lifecycle_code_snapshot_root is not None,
        args.derive_per_case_review_run,
        args.derive_review_attempt_state_machine,
        args.derive_generation_attempt_state_machine,
    )
    if any(compatibility_switches) and not all(compatibility_switches):
        print(
            "--lifecycle-code-snapshot-root, --derive-per-case-review-run, and "
            "--derive-review-attempt-state-machine, and "
            "--derive-generation-attempt-state-machine must be supplied together"
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
        "score_result_roots": tuple(args.score_result_root or ()),
        "review_quiescence_receipt_path": args.review_quiescence_receipt,
    }
    if args.lifecycle_code_snapshot_root is not None:
        overrides["lifecycle_code_snapshot_root"] = args.lifecycle_code_snapshot_root
    if args.derive_per_case_review_run:
        overrides["derive_per_case_review_run"] = True
    if args.derive_review_attempt_state_machine:
        overrides["derive_review_attempt_state_machine"] = True
    if args.derive_generation_attempt_state_machine:
        overrides["derive_generation_attempt_state_machine"] = True
    try:
        if args.preflight_review_currentness:
            preflight_overrides = dict(overrides)
            preflight_overrides.pop("review_quiescence_receipt_path")
            preflight = preflight_agentdojo_full_review_currentness(
                **preflight_overrides
            )
            receipt_path = None
            if args.preflight_output is not None:
                receipt_path = publish_review_currentness_preflight_receipt(
                    snapshot=preflight, output_path=args.preflight_output
                )
            print(
                json.dumps(
                    {
                        "action": "preflight-review-currentness",
                        "status": preflight["status"],
                        "counts": preflight["counts"],
                        "case_id_order_sha256": preflight["case_identity"][
                            "case_id_order_sha256"
                        ],
                        "case_entries_sha256": preflight["case_entries_sha256"],
                        "preflight_sha256": sha256_object(preflight),
                        "preflight_receipt_path": (
                            str(receipt_path) if receipt_path is not None else None
                        ),
                        "planned_outputs": preflight["planned_outputs"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if args.capture_review_quiescence:
            receipt = capture_review_quiescence_receipt(
                output_path=args.review_quiescence_receipt,
                draft_root=args.draft_root,
                lifecycle_report_path=args.lifecycle_report,
                lifecycle_index_path=args.lifecycle_index,
                seal_draft_tree_read_only=args.seal_draft_tree_read_only,
                review_preflight_receipt_path=(
                    args.review_preflight_receipt
                    if args.seal_draft_tree_read_only
                    and not args.post_lock_currentness_seal
                    else None
                ),
                post_lock_currentness_seal=args.post_lock_currentness_seal,
                post_lock_snapshot_overrides=(
                    overrides if args.post_lock_currentness_seal else None
                ),
                freeze_output_path=args.output,
            )
            print(
                json.dumps(
                    {
                        "action": "capture-review-quiescence",
                        "receipt_path": str(receipt),
                        "receipt_sha256": sha256_file(receipt),
                        "draft_tree_sealed_read_only": args.seal_draft_tree_read_only,
                        "currentness_gate_mode": (
                            CHECKLIST_REVIEW_POST_LOCK_GATE_MODE
                            if args.post_lock_currentness_seal
                            else "legacy_pre_lock_review_currentness"
                        ),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if args.verify_only:
            result = verify_checklist_freeze_v2(freeze_path=args.output, **overrides)
            action = "verified"
        else:
            result = freeze_agentdojo_full_checklists_v2(
                output_path=args.output,
                frozen_at=args.frozen_at,
                quiescence_max_age_seconds=args.quiescence_max_age_seconds,
                **overrides,
            )
            action = "frozen"
    except (ContractLifecycleError, OSError, ValueError) as exc:
        print(str(exc))
        return 2
    print(
        json.dumps(
            {
                "action": action,
                "freeze_path": str(result.freeze_path),
                "freeze_sha256": result.freeze_sha256,
                "invalidation_path": str(
                    checklist_freeze_v2_invalidation_path(result.freeze_path)
                ),
                "counts": result.definition["counts"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
