"""Build or verify the blind 2,847-slot AgentDojo evidence acceptance index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evidence_system.contracts.agentdojo_full_evidence import (
    DEFAULT_ACCEPTANCE_QUIESCENCE_RECEIPT,
    DEFAULT_EVIDENCE_INDEX,
    DEFAULT_FORMAL_EXECUTION_ANOMALY_RECEIPT,
    DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT,
    DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
    publish_evidence_acceptance_index,
    verify_evidence_acceptance_index,
)
from evidence_system.contracts.agentdojo_checklist_freeze_v2 import (
    DEFAULT_CHECKLIST_FREEZE_V2,
)
from evidence_system.contracts.agentdojo_full_execution import DEFAULT_EXECUTION_LOCK
from evidence_system.contracts.common import ContractLifecycleError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-lock", type=Path, default=DEFAULT_EXECUTION_LOCK)
    parser.add_argument(
        "--checklist-freeze-lock", type=Path, default=DEFAULT_CHECKLIST_FREEZE_V2
    )
    parser.add_argument(
        "--review-quiescence-receipt",
        type=Path,
        default=DEFAULT_ACCEPTANCE_QUIESCENCE_RECEIPT,
    )
    parser.add_argument(
        "--retrieval-quiescence-receipt",
        type=Path,
        default=DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT,
    )
    parser.add_argument(
        "--sealed-retrieval-receipt",
        type=Path,
        default=DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
    )
    parser.add_argument(
        "--staging-evidence-root",
        type=Path,
        help="Must exactly match the staging root declared by the execution lock.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument(
        "--formal-completion-receipt",
        type=Path,
        default=DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    )
    parser.add_argument(
        "--formal-anomaly-receipt",
        type=Path,
        default=DEFAULT_FORMAL_EXECUTION_ANOMALY_RECEIPT,
    )
    parser.add_argument("--locked-at")
    parser.add_argument("--verify-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verify_only and args.locked_at is not None:
        print("--verify-only cannot be combined with --locked-at")
        return 2
    try:
        if args.verify_only:
            result = verify_evidence_acceptance_index(
                index_path=args.output,
                execution_lock_path=args.execution_lock,
                checklist_freeze_lock_path=args.checklist_freeze_lock,
                review_quiescence_receipt_path=args.review_quiescence_receipt,
                retrieval_quiescence_receipt_path=(
                    args.retrieval_quiescence_receipt
                ),
                sealed_retrieval_receipt_path=args.sealed_retrieval_receipt,
                staging_evidence_root=args.staging_evidence_root,
                formal_completion_receipt_path=args.formal_completion_receipt,
                formal_anomaly_receipt_path=args.formal_anomaly_receipt,
            )
            action = "verified"
        else:
            result = publish_evidence_acceptance_index(
                output_path=args.output,
                locked_at=args.locked_at,
                execution_lock_path=args.execution_lock,
                checklist_freeze_lock_path=args.checklist_freeze_lock,
                review_quiescence_receipt_path=args.review_quiescence_receipt,
                retrieval_quiescence_receipt_path=(
                    args.retrieval_quiescence_receipt
                ),
                sealed_retrieval_receipt_path=args.sealed_retrieval_receipt,
                staging_evidence_root=args.staging_evidence_root,
                formal_completion_receipt_path=args.formal_completion_receipt,
                formal_anomaly_receipt_path=args.formal_anomaly_receipt,
            )
            action = "published" if result.created else "verified_existing"
    except (ContractLifecycleError, OSError, ValueError) as exc:
        print(str(exc))
        return 2
    print(
        json.dumps(
            {
                "action": action,
                "path": str(result.path),
                "sha256": result.sha256,
                "counts": result.definition["counts"],
                "blind_audit": result.definition["blind_audit"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
