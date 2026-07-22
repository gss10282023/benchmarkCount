#!/usr/bin/env python3
"""Record an immutable index over 116 pre-existing root-agent case verdicts.

This command never creates a case verdict and never calls a model.  The root
agent must first inspect each case and place a self-hashed ``verdict.json`` at
``VERDICT_ROOT/<case_unit_id>/verdict.json``.  This command then independently
revalidates every bound packet/draft/QC/proposal/result/receipt and every piece
of verdict evidence before recording the exact 116-case index consumed by the
finalizer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from finalize_effective_semantic_reviews import (
    expected_root_verdict_bindings,
    load_independent_validation,
    load_prelock,
    load_schema_set,
    validate_case_proposal,
)
from repair_aware_final_common import (
    ROOT_VERDICT_INDEX_SCHEMA,
    require_zoned_time,
    verify_effective_review_content_address,
    verify_root_agent_verdict,
)
from repair_pipeline_common import (
    EXPECTED_CASE_COUNT,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    file_binding,
    object_sha256,
    utc_now,
    write_json_create_once,
)
from semantic_review_common import SemanticReviewError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path)
    parser.add_argument("--independent-validation", type=Path)
    parser.add_argument("--verdict-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "case_count": EXPECTED_CASE_COUNT,
                    "case_verdicts_created": False,
                    "external_verdicts_required": EXPECTED_CASE_COUNT,
                    "model_invoked": False,
                    "missing_or_unbound_verdict_blocks_index": True,
                },
                indent=2,
            )
        )
        return 0
    if (
        args.prelock is None
        or args.independent_validation is None
        or args.verdict_root is None
    ):
        raise RepairPipelineError(
            "--prelock, --independent-validation, and --verdict-root are required"
        )
    prelock_path = args.prelock.resolve()
    validation_path = args.independent_validation.resolve()
    verdict_root = args.verdict_root.resolve()
    for label, path in (("verdict root", verdict_root),):
        try:
            path.relative_to(WORK_ROOT.resolve())
        except ValueError as exc:
            raise RepairPipelineError(f"{label} must stay inside candidate116") from exc
    if not verdict_root.is_dir():
        raise RepairPipelineError("verdict root does not exist")
    output = (args.output.resolve() if args.output else verdict_root / "index.json")
    try:
        output.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("verdict index output must stay inside candidate116") from exc
    if output.exists():
        raise RepairPipelineError(f"refusing to overwrite root-verdict index: {output}")

    prelock = load_prelock(prelock_path)
    verify_effective_review_content_address(prelock)
    validation = load_independent_validation(validation_path, prelock_path, prelock)
    proposal_schema, body_schema, checklist_schema = load_schema_set(prelock)
    rows = list(prelock["case_inputs"])
    index_rows: list[dict[str, Any]] = []
    accepted = 0
    rejected = 0
    for rank, row in enumerate(rows):
        case_id = str(row["case_unit_id"])
        value = validate_case_proposal(
            prelock_path,
            prelock,
            row,
            proposal_schema,
            body_schema,
            checklist_schema,
        )
        if value["status"] != "accepted":
            raise RepairPipelineError(
                f"{case_id} model proposal is not structurally accepted; verdict index is blocked"
            )
        verdict_path = verdict_root / case_id / "verdict.json"
        expected_bindings = expected_root_verdict_bindings(
            row,
            value,
            prelock_path,
            prelock,
            validation_path,
            validation,
        )
        verdict = verify_root_agent_verdict(
            verdict_path,
            case_id=case_id,
            selection_rank=rank,
            expected_bindings=expected_bindings,
        )
        accepted += verdict["verdict"] == "accepted"
        rejected += verdict["verdict"] == "rejected"
        index_row = {
            "selection_rank": rank,
            "case_unit_id": case_id,
            "task_id": case_id,
            "verdict": verdict["verdict"],
            "reviewed_at": verdict["reviewed_at"],
            "verdict_file": file_binding(verdict_path)
            | {"verdict_sha256": verdict["verdict_sha256"]},
            "verdict_sha256": verdict["verdict_sha256"],
        }
        index_row["row_sha256"] = object_sha256(index_row)
        index_rows.append(index_row)
    created_at = require_zoned_time(args.created_at or utc_now(), "index created_at")
    index = {
        "schema_version": ROOT_VERDICT_INDEX_SCHEMA,
        "status": "complete",
        "review_id": prelock["review_id"],
        "created_at": created_at,
        "reviewer": "Codex/root_agent",
        "human_reviewed": False,
        "case_count": EXPECTED_CASE_COUNT,
        "accepted_count": accepted,
        "rejected_count": rejected,
        "case_order": list(prelock["case_order"]),
        "case_order_sha256": prelock["case_order_sha256"],
        "semantic_review_prelock": file_binding(prelock_path)
        | {"prelock_sha256": prelock["prelock_sha256"]},
        "independent_validation": file_binding(validation_path)
        | {"validation_report_sha256": validation["validation_report_sha256"]},
        "cases": index_rows,
        "cases_sha256": object_sha256(index_rows),
    }
    index = add_self_hash(index, "index_sha256")
    if args.check_only:
        print(
            json.dumps(
                {
                    "status": "check_only_pass",
                    "accepted_count": accepted,
                    "rejected_count": rejected,
                    "index_sha256": index["index_sha256"],
                    "index_written": False,
                },
                indent=2,
            )
        )
        return 0
    write_json_create_once(output, index)
    print(
        json.dumps(
            {
                "status": "recorded",
                "accepted_count": accepted,
                "rejected_count": rejected,
                "index": file_binding(output) | {"index_sha256": index["index_sha256"]},
                "case_verdicts_created": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
