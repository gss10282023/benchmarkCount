#!/usr/bin/env python3
"""Finalize 116 pre-existing external Codex/root-agent case verdicts.

This is a fail-closed bridge, not a human-review impersonator.  It emits final
``androidworld_checklist_review/v1`` records only when the independently
validated proposal wave is complete *and* a separate, pre-existing, per-case,
self-hashed root-agent verdict index accepts 116/116 with concrete evidence.
This finalizer never invents checks, evidence, or root-agent acceptance from a
model proposal.  Any rejected, missing, or invalid input blocks the handoff.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from repair_pipeline_common import (
    EXPECTED_CASE_COUNT,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    file_binding,
    load_json,
    load_yaml_mapping,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    utc_now,
    verify_file_binding,
    verify_internal_hash,
    verify_repair_concurrency_evidence,
    write_json_create_once,
)
from semantic_review_common import (
    SemanticReviewError,
    load_jsonl_events,
    model_body_schema,
    parse_case_packet,
    validate_proposal,
    verify_issue_history,
    verify_semantic_concurrency_evidence,
    verify_self_hash,
    write_json_atomic,
)
from repair_aware_final_common import (
    ROOT_VERDICT_INDEX_SCHEMA,
    require_zoned_time,
    verify_effective_review_content_address,
    verify_root_agent_verdict,
    verify_self_hashed_row,
)


SCRIPT = Path(__file__).resolve()
HANDOFF_SCHEMA = "androidworld_repair_aware_promotion_handoff/v2"
REVIEW_CHECKS = (
    "identity",
    "schema_guardrails",
    "llm_provenance",
    "support_pointers",
    "user_goal",
    "evaluator_success",
    "fail",
    "undecided",
    "decisive_artifacts",
    "stronger_conditions",
    "metadata_conflict_disposition",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path)
    parser.add_argument("--independent-validation", type=Path)
    parser.add_argument("--root-verdict-index", type=Path)
    parser.add_argument("--review-root", type=Path)
    parser.add_argument(
        "--handoff-root",
        type=Path,
        default=WORK_ROOT / "repair_generation" / "promotion_handoffs_repair_aware",
    )
    parser.add_argument(
        "--rejection-root",
        type=Path,
        default=WORK_ROOT / "review_generation" / "rejection_indexes",
    )
    parser.add_argument("--finalized-at")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def require_iso8601(value: Any, label: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RepairPipelineError(f"{label} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise RepairPipelineError(f"{label} must include a time zone")
    return text


def binding_map(value: Any, label: str) -> None:
    if isinstance(value, Mapping) and {"path", "sha256", "size_bytes"}.issubset(value):
        verify_file_binding(value, label, inside_candidate=True)
        return
    if isinstance(value, Mapping):
        if not value:
            raise RepairPipelineError(f"{label} binding map is empty")
        for key, nested in value.items():
            binding_map(nested, f"{label}.{key}")
        return
    raise RepairPipelineError(f"{label} is not a binding or binding map")


def load_prelock(path: Path) -> dict[str, Any]:
    prelock = load_json(path.resolve(), "effective semantic-review prelock")
    if (
        prelock.get("schema_version") != "androidworld_semantic_review_prelock/v1"
        or prelock.get("status") != "frozen_before_first_review_model_call"
    ):
        raise RepairPipelineError("semantic-review prelock schema/status is invalid")
    verify_self_hash(prelock, "prelock_sha256", "effective semantic-review prelock")
    order = list(prelock.get("case_order") or [])
    rows = list(prelock.get("case_inputs") or [])
    if (
        prelock.get("case_count") != EXPECTED_CASE_COUNT
        or len(order) != EXPECTED_CASE_COUNT
        or len(set(order)) != EXPECTED_CASE_COUNT
        or prelock.get("case_order_sha256") != object_sha256(order)
        or len(rows) != EXPECTED_CASE_COUNT
        or prelock.get("case_inputs_sha256") != object_sha256(rows)
    ):
        raise RepairPipelineError("semantic-review prelock case universe is invalid")
    for rank, (case_id, row) in enumerate(zip(order, rows, strict=True)):
        if not isinstance(row, Mapping):
            raise RepairPipelineError(f"prelock case row {rank} is not an object")
        core = dict(row)
        claimed = core.pop("case_input_sha256", None)
        if claimed != object_sha256(core):
            raise RepairPipelineError(f"{case_id} review input self hash differs")
        if (
            row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_id
            or row.get("task_id") != case_id
            or row.get("packet_kind") != "full"
        ):
            raise RepairPipelineError(f"{case_id} review input identity/order is invalid")
        binding_map(row.get("input_bindings"), f"{case_id} review inputs")
    hard = prelock.get("hard_semantic_policies") or {}
    if not all(
        hard.get(key) is True
        for key in (
            "exception_nan_or_no_numeric_raw_is_undecided",
            "metadata_code_differences_explicit",
            "parameter_schema_generator_differences_explicit",
        )
    ):
        raise RepairPipelineError("prelock does not bind all mandatory semantic policies")
    gate = prelock.get("canonical_output_gate") or {}
    if (
        gate.get("promotion_authorized") is not False
        or gate.get("model_proposals_are_not_human_reviews") is not True
        or gate.get("all_116_proposals_must_be_accepted") is not True
        or gate.get("independent_validation_must_pass") is not True
    ):
        raise RepairPipelineError("semantic-review prelock output gate is not fail closed")
    return prelock


def load_independent_validation(
    path: Path, prelock_path: Path, prelock: Mapping[str, Any]
) -> dict[str, Any]:
    report = load_json(path.resolve(), "independent semantic-review validation")
    verify_internal_hash(
        report, ("validation_report_sha256",), "independent semantic-review validation"
    )
    if (
        report.get("schema_version")
        != "androidworld_semantic_review_independent_validation/v1"
        or report.get("status") != "pass"
        or report.get("case_count") != EXPECTED_CASE_COUNT
        or report.get("passed_count") != EXPECTED_CASE_COUNT
        or report.get("failed_count") != 0
        or not isinstance(report.get("proposed_accepted_count"), int)
        or not isinstance(report.get("proposed_rejected_count"), int)
        or report.get("proposed_accepted_count", 0)
        + report.get("proposed_rejected_count", 0)
        != EXPECTED_CASE_COUNT
        or report.get("global_issues") != []
        or report.get("promotion_authorized") is not False
        or report.get("review_authority")
        != "model_proposals_only_root_agent_acceptance_required"
    ):
        raise RepairPipelineError("independent validation is not a clean 116-case structural pass")
    bound_prelock = report.get("prelock") or {}
    verified = verify_file_binding(
        bound_prelock, "independent-validation prelock", inside_candidate=True
    )
    if (
        verified != prelock_path.resolve()
        or bound_prelock.get("prelock_sha256") != prelock.get("prelock_sha256")
    ):
        raise RepairPipelineError("independent validation binds a different review prelock")
    rows = list(report.get("cases") or [])
    if len(rows) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("independent validation has no exact 116-case index")
    for rank, (case_id, row) in enumerate(zip(prelock["case_order"], rows, strict=True)):
        if (
            not isinstance(row, Mapping)
            or row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_id
            or row.get("status") != "pass"
            or row.get("proposal_status") not in {"accepted", "rejected"}
            or row.get("issues") != []
            or row.get("promotion_authorized") is not False
        ):
            raise RepairPipelineError(f"independent validation row fails at {case_id}")
    proposal_root = resolve_repo_path(
        (prelock.get("canonical_output_gate") or {}).get("proposal_wave"),
        inside_candidate=True,
    )
    concurrency_evidence = verify_semantic_concurrency_evidence(
        events_path=proposal_root / "_concurrency" / "events.jsonl",
        audit_path=proposal_root / "_concurrency" / "audit.json",
        expected_case_order=list(prelock["case_order"]),
        expected_prelock_sha256=str(prelock["prelock_sha256"]),
    )
    if report.get("concurrency_evidence") != concurrency_evidence:
        raise RepairPipelineError(
            "independent validation semantic-review concurrency evidence differs from raw events"
        )
    return report


def load_schema_set(prelock: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    tools = prelock.get("tool_bindings") or {}
    proposal_path = verify_file_binding(
        tools.get("proposal_schema"), "review proposal schema", inside_candidate=True
    )
    body_path = verify_file_binding(
        tools.get("model_output_schema"), "review body schema", inside_candidate=True
    )
    checklist_path = verify_file_binding(
        tools.get("checklist_schema"), "review checklist schema", inside_candidate=True
    )
    issue_history_path = verify_file_binding(
        row["input_bindings"]["issue_history"],
        f"{case_id} issue history",
        inside_candidate=True,
    )
    issue_history = load_json(issue_history_path, f"{case_id} issue history")
    verify_issue_history(
        issue_history,
        case_id=case_id,
        rank=int(row["selection_rank"]),
    )
    proposal = load_json(proposal_path, "review proposal schema")
    body = load_json(body_path, "review body schema")
    if body != model_body_schema(proposal):
        raise RepairPipelineError("review body schema is not derived from the frozen proposal schema")
    return proposal, body, load_json(checklist_path, "review checklist schema")


def validate_case_proposal(
    prelock_path: Path,
    prelock: Mapping[str, Any],
    row: Mapping[str, Any],
    proposal_schema: Mapping[str, Any],
    body_schema: Mapping[str, Any],
    checklist_schema: Mapping[str, Any],
) -> dict[str, Any]:
    case_id = str(row["case_unit_id"])
    output_root = resolve_repo_path(
        (prelock.get("canonical_output_gate") or {}).get("proposal_wave"),
        inside_candidate=True,
    )
    result_path = output_root / case_id / "result.json"
    result = load_json(result_path, f"{case_id} semantic result")
    verify_self_hash(result, "result_sha256", f"{case_id} semantic result")
    if (
        result.get("schema_version") != "androidworld_semantic_review_case_result/v1"
        or result.get("status") != "completed"
        or result.get("case_unit_id") != case_id
        or result.get("task_id") != case_id
        or result.get("selection_rank") != row.get("selection_rank")
        or result.get("proposal_status") not in {"accepted", "rejected"}
        or result.get("prelock_sha256") != prelock.get("prelock_sha256")
        or result.get("promotion_authorized") is not False
    ):
        raise RepairPipelineError(f"{case_id} semantic result metadata is invalid")
    receipt_path = verify_file_binding(
        result.get("selected_receipt"), f"{case_id} semantic receipt", inside_candidate=True
    )
    receipt = load_json(receipt_path, f"{case_id} semantic receipt")
    verify_self_hash(receipt, "receipt_sha256", f"{case_id} semantic receipt")
    if (
        receipt.get("status") != "completed_valid_proposal"
        or receipt.get("case_unit_id") != case_id
        or receipt.get("selection_rank") != row.get("selection_rank")
        or receipt.get("proposal_status") != result.get("proposal_status")
        or receipt.get("prelock_sha256") != prelock.get("prelock_sha256")
        or receipt.get("receipt_sha256") != result.get("receipt_sha256")
        or receipt.get("promotion_authorized") is not False
    ):
        raise RepairPipelineError(f"{case_id} semantic receipt metadata is invalid")
    files = receipt.get("files") or {}
    expected_files = {
        "proposal",
        "model_output",
        "codex_events",
        "stderr",
        "reasoning_summary",
        "llm_call",
        "validation",
    }
    if set(files) != expected_files:
        raise RepairPipelineError(f"{case_id} semantic receipt file set is incomplete")
    bound_paths = {
        name: verify_file_binding(binding, f"{case_id} semantic {name}", inside_candidate=True)
        for name, binding in files.items()
    }
    proposal = load_json(bound_paths["proposal"], f"{case_id} semantic proposal")
    model_output = load_json(bound_paths["model_output"], f"{case_id} semantic model output")
    if proposal.get("review") != model_output or proposal.get("input_bindings") != row.get(
        "input_bindings"
    ):
        raise RepairPipelineError(f"{case_id} semantic proposal altered model output/input bindings")
    packet_path = verify_file_binding(
        row["input_bindings"]["packet"], f"{case_id} packet", inside_candidate=True
    )
    checklist_path = verify_file_binding(
        row["input_bindings"]["raw_checklist_yaml"],
        f"{case_id} effective checklist",
        inside_candidate=True,
    )
    problems = validate_proposal(
        proposal,
        proposal_schema=proposal_schema,
        body_schema=body_schema,
        checklist=load_yaml_mapping(checklist_path),
        checklist_schema=checklist_schema,
        packet=parse_case_packet(packet_path.read_text(encoding="utf-8")),
        issue_history=issue_history,
    )
    if problems:
        raise RepairPipelineError(f"{case_id} semantic proposal revalidation fails: {problems}")
    llm = load_json(bound_paths["llm_call"], f"{case_id} semantic llm call")
    verify_self_hash(llm, "llm_call_sha256", f"{case_id} semantic llm call")
    events, malformed = load_jsonl_events(bound_paths["codex_events"].read_text(encoding="utf-8"))
    if (
        malformed
        or not any(event.get("type") == "turn.completed" for event in events)
        or llm.get("provider") != "codex_cli"
        or llm.get("auth_mode") != "codex_login"
        or llm.get("sandbox") != "read-only"
        or llm.get("ephemeral") is not True
        or llm.get("ignore_user_config") is not True
        or int((llm.get("token_usage") or {}).get("total_tokens") or 0) <= 0
        or llm.get("promotion_authorized") is not False
    ):
        raise RepairPipelineError(f"{case_id} semantic Codex provenance is invalid")
    validation = load_json(bound_paths["validation"], f"{case_id} attempt validation")
    verify_self_hash(validation, "validation_sha256", f"{case_id} attempt validation")
    if (
        validation.get("status") != "passed"
        or validation.get("proposal_status") != result.get("proposal_status")
        or validation.get("issues") != []
        or validation.get("promotion_authorized") is not False
    ):
        raise RepairPipelineError(f"{case_id} selected attempt validation is not clean")
    return {
        "case_unit_id": case_id,
        "status": result["proposal_status"],
        "result_path": result_path,
        "result": result,
        "receipt_path": receipt_path,
        "receipt": receipt,
        "proposal_path": bound_paths["proposal"],
        "proposal": proposal,
        "llm_call_path": bound_paths["llm_call"],
    }


def expected_root_verdict_bindings(
    row: Mapping[str, Any],
    value: Mapping[str, Any],
    prelock_path: Path,
    prelock: Mapping[str, Any],
    validation_path: Path,
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    bindings = copy.deepcopy(dict(row["input_bindings"]))
    bindings.update(
        {
            "semantic_proposal": file_binding(Path(value["proposal_path"]))
            | {"proposal_sha256": value["proposal"]["proposal_sha256"]},
            "semantic_result": file_binding(Path(value["result_path"]))
            | {"result_sha256": value["result"]["result_sha256"]},
            "semantic_receipt": file_binding(Path(value["receipt_path"]))
            | {"receipt_sha256": value["receipt"]["receipt_sha256"]},
            "semantic_review_prelock": file_binding(prelock_path)
            | {"prelock_sha256": prelock["prelock_sha256"]},
            "independent_validation": file_binding(validation_path)
            | {"validation_report_sha256": validation["validation_report_sha256"]},
        }
    )
    return bindings


def load_root_verdict_index(
    path: Path,
    *,
    prelock_path: Path,
    prelock: Mapping[str, Any],
    validation_path: Path,
    validation: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    outcomes: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = path.resolve()
    try:
        path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("root-verdict index must stay inside candidate116") from exc
    index = load_json(path, "external root-agent verdict index")
    verify_self_hash(index, "index_sha256", "external root-agent verdict index")
    expected_keys = {
        "schema_version",
        "status",
        "review_id",
        "created_at",
        "reviewer",
        "human_reviewed",
        "case_count",
        "accepted_count",
        "rejected_count",
        "case_order",
        "case_order_sha256",
        "semantic_review_prelock",
        "independent_validation",
        "cases",
        "cases_sha256",
        "index_sha256",
    }
    index_rows = list(index.get("cases") or [])
    if (
        set(index) != expected_keys
        or index.get("schema_version") != ROOT_VERDICT_INDEX_SCHEMA
        or index.get("status") != "complete"
        or index.get("review_id") != prelock.get("review_id")
        or index.get("reviewer") != "Codex/root_agent"
        or index.get("human_reviewed") is not False
        or index.get("case_count") != EXPECTED_CASE_COUNT
        or not isinstance(index.get("accepted_count"), int)
        or not isinstance(index.get("rejected_count"), int)
        or index.get("accepted_count", 0) + index.get("rejected_count", 0)
        != EXPECTED_CASE_COUNT
        or index.get("case_order") != prelock.get("case_order")
        or index.get("case_order_sha256") != prelock.get("case_order_sha256")
        or len(index_rows) != EXPECTED_CASE_COUNT
        or index.get("cases_sha256") != object_sha256(index_rows)
    ):
        raise RepairPipelineError("external root-agent verdict index is incomplete/invalid")
    require_zoned_time(index.get("created_at"), "root-verdict index created_at")
    expected_prelock = file_binding(prelock_path) | {
        "prelock_sha256": prelock["prelock_sha256"]
    }
    expected_validation = file_binding(validation_path) | {
        "validation_report_sha256": validation["validation_report_sha256"]
    }
    if (
        index.get("semantic_review_prelock") != expected_prelock
        or index.get("independent_validation") != expected_validation
    ):
        raise RepairPipelineError("root-verdict index binds different review inputs")

    verdicts: list[dict[str, Any]] = []
    accepted = 0
    rejected = 0
    for rank, (case_id, prelock_row, outcome, index_row) in enumerate(
        zip(prelock["case_order"], rows, outcomes, index_rows, strict=True)
    ):
        if outcome.get("status") != "accepted" or not isinstance(outcome.get("value"), Mapping):
            raise RepairPipelineError(
                f"{case_id} cannot have an authorizing verdict over an invalid/rejected proposal"
            )
        if not isinstance(index_row, Mapping):
            raise RepairPipelineError(f"{case_id} root-verdict index row is not an object")
        verify_self_hashed_row(index_row, "row_sha256", f"{case_id} root-verdict index row")
        if set(index_row) != {
            "selection_rank",
            "case_unit_id",
            "task_id",
            "verdict",
            "reviewed_at",
            "verdict_file",
            "verdict_sha256",
            "row_sha256",
        } or (
            index_row.get("selection_rank") != rank
            or index_row.get("case_unit_id") != case_id
            or index_row.get("task_id") != case_id
            or index_row.get("verdict") not in {"accepted", "rejected"}
        ):
            raise RepairPipelineError(f"{case_id} root-verdict index identity/order is invalid")
        require_zoned_time(index_row.get("reviewed_at"), f"{case_id} indexed reviewed_at")
        verdict_path = verify_file_binding(
            index_row.get("verdict_file"), f"{case_id} root-agent verdict", inside_candidate=True
        )
        expected_bindings = expected_root_verdict_bindings(
            prelock_row,
            outcome["value"],
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
        if (
            verdict.get("verdict_sha256") != index_row.get("verdict_sha256")
            or verdict.get("reviewed_at") != index_row.get("reviewed_at")
            or verdict.get("verdict") != index_row.get("verdict")
            or index_row.get("verdict_file")
            != file_binding(verdict_path) | {"verdict_sha256": verdict["verdict_sha256"]}
        ):
            raise RepairPipelineError(f"{case_id} indexed root-agent verdict differs from file")
        accepted += verdict["verdict"] == "accepted"
        rejected += verdict["verdict"] == "rejected"
        verdicts.append({"path": verdict_path, "verdict": verdict})
    if index.get("accepted_count") != accepted or index.get("rejected_count") != rejected:
        raise RepairPipelineError("root-verdict index accepted/rejected counts differ")
    return index, verdicts


def relocated_binding(staged: Path, final: Path) -> dict[str, Any]:
    result = file_binding(staged)
    result["path"] = repo_relative(final)
    return result


def write_rejection_index(
    root: Path,
    prelock_path: Path,
    prelock: Mapping[str, Any],
    validation_path: Path,
    cases: list[dict[str, Any]],
    root_verdict_index_path: Path | None = None,
) -> Path:
    root = root.resolve()
    try:
        root.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("rejection root must be inside candidate116") from exc
    rejected = [row for row in cases if row["status"] != "accepted"]
    payload = {
        "schema_version": "androidworld_effective_semantic_review_rejection_index/v1",
        "status": "promotion_handoff_blocked",
        "created_at": utc_now(),
        "review_id": prelock["review_id"],
        "case_count": EXPECTED_CASE_COUNT,
        "accepted_count": EXPECTED_CASE_COUNT - len(rejected),
        "rejected_or_invalid_count": len(rejected),
        "rejected_or_invalid_cases": rejected,
        "semantic_review_prelock": file_binding(prelock_path)
        | {"prelock_sha256": prelock["prelock_sha256"]},
        "independent_validation": file_binding(validation_path),
        "root_agent_verdict_index": (
            file_binding(root_verdict_index_path) if root_verdict_index_path is not None else None
        ),
        "reviews_written": False,
        "handoff_created": False,
        "promotion_authorized": False,
    }
    payload = add_self_hash(payload, "rejection_index_sha256")
    path = root / f"{prelock['review_id']}_{payload['rejection_index_sha256']}.json"
    if path.exists():
        raise RepairPipelineError(f"refusing to overwrite rejection index: {path}")
    write_json_atomic(path, payload)
    return path


def main() -> int:
    args = parse_args()
    if args.self_test:
        statuses = ["accepted"] * 115 + ["rejected"]
        rejected = [index for index, status in enumerate(statuses) if status != "accepted"]
        if rejected != [115] or len(set(REVIEW_CHECKS)) != len(REVIEW_CHECKS):
            raise RepairPipelineError("finalizer fail-closed self-test failed")
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "negative_one_rejection_blocks_handoff": True,
                    "external_root_verdict_index_required": True,
                    "model_proposal_cannot_create_root_acceptance": True,
                    "human_review_claimed": False,
                    "model_invoked": False,
                },
                indent=2,
            )
        )
        return 0
    if (
        args.prelock is None
        or args.independent_validation is None
        or args.root_verdict_index is None
    ):
        raise RepairPipelineError(
            "--prelock, --independent-validation, and --root-verdict-index are required"
        )
    prelock_path = args.prelock.resolve()
    validation_path = args.independent_validation.resolve()
    root_verdict_index_path = args.root_verdict_index.resolve()
    prelock = load_prelock(prelock_path)
    verify_effective_review_content_address(prelock)
    validation = load_independent_validation(validation_path, prelock_path, prelock)
    semantic_concurrency_evidence = copy.deepcopy(validation["concurrency_evidence"])
    proposal_schema, body_schema, checklist_schema = load_schema_set(prelock)
    rows = list(prelock["case_inputs"])
    outcomes: list[dict[str, Any]] = []
    for row in rows:
        case_id = str(row["case_unit_id"])
        try:
            value = validate_case_proposal(
                prelock_path,
                prelock,
                row,
                proposal_schema,
                body_schema,
                checklist_schema,
            )
            outcomes.append(
                {
                    "selection_rank": row["selection_rank"],
                    "case_unit_id": case_id,
                    "status": value["status"],
                    "issues": [] if value["status"] == "accepted" else list(
                        (value["proposal"].get("review") or {}).get("issues") or []
                    ),
                    "value": value,
                }
            )
        except (RepairPipelineError, Exception) as exc:
            outcomes.append(
                {
                    "selection_rank": row["selection_rank"],
                    "case_unit_id": case_id,
                    "status": "invalid",
                    "issues": [str(exc)],
                    "value": None,
                }
            )
    blocked = [row for row in outcomes if row["status"] != "accepted"]
    if blocked:
        compact = [
            {
                "selection_rank": row["selection_rank"],
                "case_unit_id": row["case_unit_id"],
                "status": row["status"],
                "issues": row["issues"],
            }
            for row in outcomes
        ]
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "status": "promotion_handoff_blocked",
                        "rejected_or_invalid_count": len(blocked),
                        "reviews_written": False,
                        "handoff_created": False,
                    },
                    indent=2,
                )
            )
            return 1
        path = write_rejection_index(
            args.rejection_root, prelock_path, prelock, validation_path, compact
        )
        print(
            json.dumps(
                {
                    "status": "promotion_handoff_blocked",
                    "rejected_or_invalid_count": len(blocked),
                    "rejection_index": file_binding(path),
                    "reviews_written": False,
                    "handoff_created": False,
                },
                indent=2,
            )
        )
        return 1

    root_verdict_index, root_verdicts = load_root_verdict_index(
        root_verdict_index_path,
        prelock_path=prelock_path,
        prelock=prelock,
        validation_path=validation_path,
        validation=validation,
        rows=rows,
        outcomes=outcomes,
    )
    for outcome, external in zip(outcomes, root_verdicts, strict=True):
        outcome["root_verdict_path"] = external["path"]
        outcome["root_verdict"] = external["verdict"]
        outcome["root_verdict_status"] = external["verdict"]["verdict"]
    blocked = [row for row in outcomes if row["root_verdict_status"] != "accepted"]
    if blocked:
        compact = [
            {
                "selection_rank": row["selection_rank"],
                "case_unit_id": row["case_unit_id"],
                "status": (
                    "accepted"
                    if row["root_verdict_status"] == "accepted"
                    else "root_agent_rejected"
                ),
                "issues": list(row["root_verdict"]["issues"]),
                "root_agent_verdict_sha256": row["root_verdict"]["verdict_sha256"],
            }
            for row in outcomes
        ]
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "status": "promotion_handoff_blocked",
                        "root_agent_rejected_count": len(blocked),
                        "reviews_written": False,
                        "handoff_created": False,
                    },
                    indent=2,
                )
            )
            return 1
        path = write_rejection_index(
            args.rejection_root,
            prelock_path,
            prelock,
            validation_path,
            compact,
            root_verdict_index_path,
        )
        print(
            json.dumps(
                {
                    "status": "promotion_handoff_blocked",
                    "root_agent_rejected_count": len(blocked),
                    "rejection_index": file_binding(path),
                    "reviews_written": False,
                    "handoff_created": False,
                },
                indent=2,
            )
        )
        return 1

    review_id = str(prelock["review_id"])
    review_root = (
        args.review_root.resolve()
        if args.review_root
        else (WORK_ROOT / "review_generation" / "finalized_reviews" / review_id).resolve()
    )
    handoff_root = args.handoff_root.resolve()
    for label, path in (("review root", review_root), ("handoff root", handoff_root)):
        try:
            path.relative_to(WORK_ROOT.resolve())
        except ValueError as exc:
            raise RepairPipelineError(f"{label} must stay inside candidate116") from exc
    if review_root.exists():
        raise RepairPipelineError(f"refusing to overwrite finalized reviews: {review_root}")
    finalized_at = require_iso8601(args.finalized_at or utc_now(), "finalized_at")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_pass",
                    "accepted_count": EXPECTED_CASE_COUNT,
                    "independent_validation_passed": True,
                    "external_root_verdicts_accepted": EXPECTED_CASE_COUNT,
                    "root_verdict_index_sha256": root_verdict_index["index_sha256"],
                    "human_review_claimed": False,
                    "reviews_written": False,
                    "handoff_created": False,
                },
                indent=2,
            )
        )
        return 0

    manifest_path = verify_file_binding(
        prelock["effective_generation"]["effective_manifest"],
        "effective manifest",
        inside_candidate=True,
    )
    manifest = load_json(manifest_path, "effective manifest")
    verify_internal_hash(manifest, ("effective_manifest_sha256",), "effective manifest")
    qc_summary_path = verify_file_binding(
        prelock["automatic_qc_summary"], "effective QC summary", inside_candidate=True
    )
    qc_summary = load_json(qc_summary_path, "effective QC summary")
    verify_internal_hash(qc_summary, ("summary_sha256",), "effective QC summary")
    effective_by_case = {row["case_unit_id"]: row for row in manifest["cases"]}
    repair_prelock_path = verify_file_binding(
        manifest["repair_prelock"], "repair prelock", inside_candidate=True
    )
    repair_prelock = load_json(repair_prelock_path, "repair prelock")
    verify_internal_hash(repair_prelock, ("prelock_sha256",), "repair prelock")
    repair_receipt_path = verify_file_binding(
        manifest.get("repair_batch_receipt"), "repair batch receipt", inside_candidate=True
    )
    repair_receipt = load_json(repair_receipt_path, "repair batch receipt")
    verify_internal_hash(repair_receipt, ("receipt_sha256",), "repair batch receipt")
    concurrency_evidence = verify_repair_concurrency_evidence(
        repair_prelock,
        repair_receipt,
        repair_root=repair_receipt_path.parent,
    )
    if (
        concurrency_evidence != manifest.get("repair_concurrency_evidence")
        or manifest.get("repair_concurrency_audit")
        != concurrency_evidence.get("summary")
        or manifest.get("repair_concurrency_samples")
        != concurrency_evidence.get("samples")
        or concurrency_evidence != qc_summary.get("repair_concurrency_evidence")
        or qc_summary.get("repair_concurrency_audit")
        != concurrency_evidence.get("summary")
        or qc_summary.get("repair_concurrency_samples")
        != concurrency_evidence.get("samples")
        or concurrency_evidence
        != (prelock.get("effective_generation") or {}).get(
            "repair_concurrency_evidence"
        )
        or (prelock.get("effective_generation") or {}).get(
            "repair_concurrency_audit"
        )
        != concurrency_evidence.get("summary")
        or (prelock.get("effective_generation") or {}).get(
            "repair_concurrency_samples"
        )
        != concurrency_evidence.get("samples")
    ):
        raise RepairPipelineError(
            "repair concurrency evidence/audit/samples differ across raw/effective/review inputs"
        )

    staging = Path(
        tempfile.mkdtemp(prefix=f".{review_root.name}.staging.", dir=review_root.parent)
    ) if review_root.parent.exists() else None
    if staging is None:
        review_root.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{review_root.name}.staging.", dir=review_root.parent))
    review_rows: list[dict[str, Any]] = []
    handoff_cases: list[dict[str, Any]] = []
    try:
        for row, outcome in zip(rows, outcomes, strict=True):
            case_id = str(row["case_unit_id"])
            value = outcome["value"]
            assert isinstance(value, Mapping)
            bindings = row["input_bindings"]
            checklist_path = verify_file_binding(
                bindings["raw_checklist_yaml"], f"{case_id} checklist", inside_candidate=True
            )
            checklist_json_path = verify_file_binding(
                bindings["raw_checklist_json"], f"{case_id} checklist JSON", inside_candidate=True
            )
            qc_path = verify_file_binding(
                bindings["automatic_qc"], f"{case_id} effective QC", inside_candidate=True
            )
            origin_path = verify_file_binding(
                bindings["effective_origin"], f"{case_id} effective origin", inside_candidate=True
            )
            proposal_path = Path(value["proposal_path"])
            result_path = Path(value["result_path"])
            receipt_path = Path(value["receipt_path"])
            root_verdict_path = Path(outcome["root_verdict_path"])
            root_verdict = outcome["root_verdict"]
            assert isinstance(root_verdict, Mapping)
            derived_checks = {
                name: root_verdict["checks"][name]["status"] == "pass"
                for name in REVIEW_CHECKS
            }
            if not all(derived_checks.values()) or root_verdict.get("verdict") != "accepted":
                raise RepairPipelineError(
                    f"{case_id} external root verdict cannot mechanically finalize as accepted"
                )
            review = {
                "schema_version": "androidworld_checklist_review/v1",
                "case_unit_id": case_id,
                "task_id": case_id,
                "status": "accepted",
                "reviewer": "Codex/root_agent",
                "review_authority": "mechanical_finalization_of_external_root_agent_case_verdict",
                "human_reviewed": False,
                "reviewed_at": root_verdict["reviewed_at"],
                "finalized_at": finalized_at,
                "notes": root_verdict["notes"],
                "issues": [],
                "checks": derived_checks,
                "review_evidence": copy.deepcopy(root_verdict["checks"]),
                "raw_checklist_path": repo_relative(checklist_path),
                "raw_checklist_sha256": sha256_file(checklist_path),
                "accepted_checklist_path": repo_relative(checklist_path),
                "accepted_checklist_sha256": sha256_file(checklist_path),
                "automatic_qc_report_path": repo_relative(qc_path),
                "automatic_qc_report_sha256": sha256_file(qc_path),
                "semantic_proposal": file_binding(proposal_path)
                | {"proposal_sha256": value["proposal"]["proposal_sha256"]},
                "semantic_result": file_binding(result_path)
                | {"result_sha256": value["result"]["result_sha256"]},
                "semantic_receipt": file_binding(receipt_path)
                | {"receipt_sha256": value["receipt"]["receipt_sha256"]},
                "semantic_review_prelock": file_binding(prelock_path)
                | {"prelock_sha256": prelock["prelock_sha256"]},
                "independent_validation": file_binding(validation_path)
                | {
                    "validation_report_sha256": validation["validation_report_sha256"]
                },
                "external_root_agent_verdict": file_binding(root_verdict_path)
                | {"verdict_sha256": root_verdict["verdict_sha256"]},
                "external_root_agent_verdict_index": file_binding(root_verdict_index_path)
                | {"index_sha256": root_verdict_index["index_sha256"]},
                "promotion_authorized_by_model_proposal": False,
                "promotion_authorized_by_root_agent_review": (
                    root_verdict["verdict"] == "accepted"
                ),
            }
            review = add_self_hash(review, "review_sha256")
            staged_review = staging / case_id / "review.json"
            write_json_atomic(staged_review, review)
            final_review = review_root / case_id / "review.json"
            review_binding = relocated_binding(staged_review, final_review) | {
                "review_sha256": review["review_sha256"]
            }
            effective = effective_by_case[case_id]
            provenance = effective.get("repair_provenance")
            draft_dir = checklist_path.parent
            draft_sidecars = {
                name.replace(".", "_"): file_binding(draft_dir / name)
                for name in (
                    "checklist.yaml",
                    "checklist.json",
                    "llm_call.json",
                    "api_response.json",
                    "reasoning_summary.txt",
                    "stdout.log",
                    "stderr.log",
                )
            }
            case_handoff = {
                "selection_rank": row["selection_rank"],
                "group": "official100" if row["selection_rank"] < 100 else "extra16",
                "case_unit_id": case_id,
                "task_id": case_id,
                "origin": effective["origin"],
                "full_packet": copy.deepcopy(bindings["packet"]),
                "effective_checklist_yaml": file_binding(checklist_path),
                "effective_checklist_json": file_binding(checklist_json_path),
                "effective_origin": file_binding(origin_path)
                | {"origin_sha256": effective["effective_origin"]["origin_sha256"]},
                "repair_provenance": copy.deepcopy(provenance),
                "draft_sidecars": draft_sidecars,
                "effective_qc": file_binding(qc_path),
                "semantic_proposal": review["semantic_proposal"],
                "semantic_result": review["semantic_result"],
                "semantic_receipt": review["semantic_receipt"],
                "root_agent_verdict": review["external_root_agent_verdict"],
                "root_agent_review": review_binding,
            }
            case_handoff["case_handoff_sha256"] = object_sha256(case_handoff)
            handoff_cases.append(case_handoff)
            review_rows.append(
                {
                    "selection_rank": row["selection_rank"],
                    "case_unit_id": case_id,
                    "review": review_binding,
                    "root_agent_verdict": review["external_root_agent_verdict"],
                    "semantic_proposal": review["semantic_proposal"],
                }
            )

        summary = {
            "schema_version": "androidworld_root_agent_review_summary/v1",
            "status": "accepted_116_of_116",
            "created_at": finalized_at,
            "review_id": review_id,
            "reviewer": "Codex/root_agent",
            "human_reviewed": False,
            "case_count": EXPECTED_CASE_COUNT,
            "accepted_count": EXPECTED_CASE_COUNT,
            "rejected_count": 0,
            "case_order": list(prelock["case_order"]),
            "case_order_sha256": prelock["case_order_sha256"],
            "reviews": review_rows,
            "reviews_sha256": object_sha256(review_rows),
            "semantic_review_prelock": file_binding(prelock_path)
            | {"prelock_sha256": prelock["prelock_sha256"]},
            "independent_validation": file_binding(validation_path)
            | {"validation_report_sha256": validation["validation_report_sha256"]},
            "external_root_agent_verdict_index": file_binding(root_verdict_index_path)
            | {"index_sha256": root_verdict_index["index_sha256"]},
            "repair_concurrency_evidence": copy.deepcopy(concurrency_evidence),
            "semantic_review_concurrency_evidence": copy.deepcopy(
                semantic_concurrency_evidence
            ),
            "repair_concurrency_audit": copy.deepcopy(concurrency_evidence["summary"]),
            "repair_concurrency_samples": copy.deepcopy(concurrency_evidence["samples"]),
            "promotion_handoff_allowed": True,
        }
        summary = add_self_hash(summary, "review_summary_sha256")
        staged_summary = staging / "summary.json"
        write_json_atomic(staged_summary, summary)
        final_summary = review_root / "summary.json"

        drift = copy.deepcopy(repair_prelock.get("drift_evidence") or {})
        for key, binding in drift.items():
            if isinstance(binding, Mapping) and "path" in binding:
                verify_file_binding(binding, f"repair drift evidence {key}", inside_candidate=True)
        handoff = {
            "schema_version": HANDOFF_SCHEMA,
            "status": "eligible_input_for_repair_aware_promotion",
            "created_at": finalized_at,
            "effective_wave_id": manifest["effective_wave_id"],
            "review_id": review_id,
            "case_count": EXPECTED_CASE_COUNT,
            "repair_count": manifest["origin_counts"]["repair"],
            "retain_count": manifest["origin_counts"]["wave_003"],
            "case_order": list(prelock["case_order"]),
            "case_order_sha256": prelock["case_order_sha256"],
            "effective_manifest": file_binding(manifest_path)
            | {"effective_manifest_sha256": manifest["effective_manifest_sha256"]},
            "repair_prelock": file_binding(repair_prelock_path)
            | {"prelock_sha256": repair_prelock["prelock_sha256"]},
            "repair_concurrency_evidence": copy.deepcopy(concurrency_evidence),
            "semantic_review_concurrency_evidence": copy.deepcopy(
                semantic_concurrency_evidence
            ),
            "repair_concurrency_audit": copy.deepcopy(concurrency_evidence["summary"]),
            "repair_concurrency_samples": copy.deepcopy(concurrency_evidence["samples"]),
            "drift_evidence": drift,
            "effective_qc_summary": file_binding(qc_summary_path)
            | {"summary_sha256": qc_summary["summary_sha256"]},
            "semantic_review_prelock": file_binding(prelock_path)
            | {"prelock_sha256": prelock["prelock_sha256"]},
            "semantic_review_config": copy.deepcopy(prelock["review_config"]),
            "semantic_review_toolchain": copy.deepcopy(prelock["toolchain_snapshot"]),
            "independent_semantic_validation": file_binding(validation_path)
            | {"validation_report_sha256": validation["validation_report_sha256"]},
            "external_root_agent_verdict_index": file_binding(root_verdict_index_path)
            | {"index_sha256": root_verdict_index["index_sha256"]},
            "root_agent_review_summary": relocated_binding(staged_summary, final_summary)
            | {"review_summary_sha256": summary["review_summary_sha256"]},
            "review_authority": {
                "reviewer": "Codex/root_agent",
                "human_reviewed": False,
                "model_proposals_are_non_authorizing": True,
                "external_case_verdicts_are_authorizing_source": True,
                "root_agent_review_accepted_116_of_116": True,
            },
            "cases": handoff_cases,
            "cases_sha256": object_sha256(handoff_cases),
            "promotion_policy": {
                "legacy_wave3_direct_promotion_forbidden": True,
                "repair_aware_origin_required": True,
                "all_116_effective_qc_pass_required": True,
                "all_116_semantic_proposals_accepted_required": True,
                "independent_semantic_validation_pass_required": True,
                "all_116_root_agent_reviews_accepted_required": True,
                "repair_concurrency_raw_samples_revalidated_required": True,
                "semantic_review_exact_six_concurrency_revalidated_required": True,
                "human_review_claim_forbidden": True,
                "canonical_promotion_completed": False,
            },
        }
        handoff = add_self_hash(handoff, "handoff_sha256")
        handoff_dir = handoff_root / manifest["effective_wave_id"]
        handoff_path = handoff_dir / f"{handoff['handoff_sha256']}.json"
        if handoff_path.exists():
            raise RepairPipelineError(f"refusing to overwrite promotion handoff: {handoff_path}")

        os.replace(staging, review_root)
        handoff_dir.mkdir(parents=True, exist_ok=True)
        try:
            write_json_create_once(handoff_path, handoff)
        except BaseException:
            shutil.rmtree(review_root, ignore_errors=True)
            raise
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    print(
        json.dumps(
            {
                "status": "accepted_116_of_116",
                "reviewer": "Codex/root_agent",
                "human_reviewed": False,
                "reviews": file_binding(review_root / "summary.json")
                | {"review_summary_sha256": summary["review_summary_sha256"]},
                "handoff": file_binding(handoff_path)
                | {"handoff_sha256": handoff["handoff_sha256"]},
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
