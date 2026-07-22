"""Atomically promote accepted AgentDojo staging evidence into the formal namespace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evidence_system.contracts.agentdojo_full_evidence import (
    DEFAULT_EVIDENCE_INDEX,
    DEFAULT_PROMOTION_QUIESCENCE_RECEIPT,
    DEFAULT_PROMOTION_RECEIPT,
    promote_agentdojo_full_evidence,
    verify_evidence_promotion_receipt,
)
from evidence_system.contracts.agentdojo_checklist_freeze_v2 import (
    DEFAULT_CHECKLIST_FREEZE_V2,
)
from evidence_system.contracts.agentdojo_full_execution import DEFAULT_EXECUTION_LOCK
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_SCORE_NAMESPACE_ROOTS,
)
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
        default=DEFAULT_PROMOTION_QUIESCENCE_RECEIPT,
    )
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument("--destination-root", type=Path)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_PROMOTION_RECEIPT)
    parser.add_argument("--score-result-root", type=Path, action="append", default=None)
    parser.add_argument("--locked-at")
    parser.add_argument("--verify-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verify_only and (
        args.locked_at is not None or args.destination_root is not None
    ):
        print("--verify-only cannot be combined with mutation options")
        return 2
    common = {
        "execution_lock_path": args.execution_lock,
        "checklist_freeze_lock_path": args.checklist_freeze_lock,
        "review_quiescence_receipt_path": args.review_quiescence_receipt,
        "evidence_index_path": args.evidence_index,
    }
    if args.score_result_root:
        common["score_result_roots"] = (
            *DEFAULT_SCORE_NAMESPACE_ROOTS,
            *tuple(args.score_result_root),
        )
    try:
        if args.verify_only:
            result = verify_evidence_promotion_receipt(
                receipt_path=args.receipt,
                **common,
            )
            action = "verified"
        else:
            result = promote_agentdojo_full_evidence(
                destination_root=args.destination_root,
                receipt_path=args.receipt,
                locked_at=args.locked_at,
                **common,
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
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
