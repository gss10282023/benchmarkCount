#!/usr/bin/env python3
"""Independently revalidate a complete semantic-review proposal wave.

This validator is read-only unless ``--report`` is explicitly supplied.  A pass
means 116 structurally and deterministically valid model proposals with intact
provenance; it still does not create root-agent acceptance records or authorize
promotion.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

from semantic_review_common import (
    EXPECTED_CASE_COUNT,
    EXPECTED_PARALLELISM,
    WORK_ROOT,
    SemanticReviewError,
    add_self_hash,
    event_response_id,
    file_binding,
    load_json,
    load_jsonl_events,
    object_sha256,
    resolve_repo_path,
    sha256_file,
    utc_now,
    verify_file_binding,
    verify_semantic_concurrency_evidence,
    verify_self_hash,
    write_json_atomic,
)
from run_semantic_review_batch import (
    load_context,
    verify_global_inputs,
    verify_selected_result,
)


SCRIPT = Path(__file__).resolve()
ATTEMPT_RE = re.compile(r"^attempt_([0-9]+)$")


def _plain_entries(path: Path, label: str) -> list[Path]:
    entries = sorted(path.iterdir(), key=lambda item: item.name)
    if any(item.is_symlink() for item in entries):
        raise SemanticReviewError(f"{label} contains a symlink")
    return entries


def validate_attempt_tree(context: Any, row: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    case_id = str(row["case_unit_id"])
    problems: list[str] = []
    try:
        case_dir = context.output_root / case_id
        allowed_case_entries = {"result.json", "attempts", "failed_results"}
        entries = _plain_entries(case_dir, f"{case_id} case tree")
        unexpected = {item.name for item in entries} - allowed_case_entries
        if unexpected:
            problems.append(f"unexpected case sidecars: {sorted(unexpected)}")
        attempts_root = case_dir / "attempts"
        attempt_dirs = _plain_entries(attempts_root, f"{case_id} attempts")
        parsed: list[tuple[int, Path]] = []
        for path in attempt_dirs:
            match = ATTEMPT_RE.fullmatch(path.name)
            if not path.is_dir() or match is None:
                problems.append(f"unexpected attempt entry: {path.name}")
                continue
            parsed.append((int(match.group(1)), path))
        indices = [index for index, _ in parsed]
        if not indices or indices != list(range(1, max(indices) + 1)):
            problems.append(f"attempt indexes are not contiguous from 1: {indices}")
        chosen = int(result.get("chosen_attempt") or 0)
        successful_attempts: list[int] = []
        for index, path in parsed:
            names = {item.name for item in _plain_entries(path, f"{case_id} attempt {index}")}
            success_names = {
                "proposal.json",
                "model_output.json",
                "codex_events.jsonl",
                "stderr.log",
                "reasoning_summary.txt",
                "llm_call.json",
                "validation.json",
                "receipt.json",
            }
            if "receipt.json" in names or "proposal.json" in names or "llm_call.json" in names:
                successful_attempts.append(index)
                if names != success_names:
                    problems.append(
                        f"successful attempt {index} sidecar set differs: {sorted(names)}"
                    )
                continue
            base_failed = {"codex_events.jsonl", "stderr.log", "attempt_failure.json"}
            if not base_failed.issubset(names):
                problems.append(f"failed attempt {index} sidecar set differs: {sorted(names)}")
                continue
            failure = load_json(path / "attempt_failure.json", f"{case_id} attempt failure")
            verify_self_hash(failure, "failure_sha256", f"{case_id} attempt failure")
            if (
                failure.get("schema_version")
                != "androidworld_semantic_review_attempt_failure/v1"
                or failure.get("status") != "failed"
                or failure.get("code")
                not in {
                    "codex_spawn_failed",
                    "codex_timeout",
                    "codex_nonzero_exit",
                    "missing_structured_output",
                    "proposal_validation_failed",
                    "normalized_proposal_validation_failed",
                }
            ):
                problems.append(f"failed attempt {index} failure record is invalid")
            validation_failure = failure.get("code") in {
                "proposal_validation_failed",
                "normalized_proposal_validation_failed",
            }
            expected_failed_names = (
                base_failed | {"model_output.json", "validation.json"}
                if validation_failure
                else base_failed
            )
            if names != expected_failed_names:
                problems.append(
                    f"failed attempt {index} exact sidecar set differs: {sorted(names)}"
                )
            if validation_failure:
                validation = load_json(path / "validation.json", f"{case_id} failed validation")
                verify_self_hash(
                    validation,
                    "validation_sha256",
                    f"{case_id} failed validation",
                )
                if (
                    validation.get("status") != "failed"
                    or validation.get("case_unit_id") != case_id
                    or validation.get("attempt_index") != index
                    or not isinstance(validation.get("issues"), list)
                    or not validation.get("issues")
                ):
                    problems.append(f"failed attempt {index} validation record differs")
        if successful_attempts != [chosen]:
            problems.append(
                f"exactly the chosen attempt must be successful: chosen={chosen}, observed={successful_attempts}"
            )
        failed_results = case_dir / "failed_results"
        if failed_results.exists():
            for path in _plain_entries(failed_results, f"{case_id} failed-result history"):
                match = re.fullmatch(r"result_([0-9a-f]{64})\.json", path.name)
                if not path.is_file() or match is None or match.group(1) != sha256_file(path):
                    problems.append(f"invalid failed-result history entry: {path.name}")
                    continue
                history = load_json(path, f"{case_id} failed-result history")
                verify_self_hash(history, "result_sha256", f"{case_id} failed-result history")
                if (
                    history.get("status") != "failed"
                    or history.get("case_unit_id") != case_id
                    or history.get("prelock_sha256") != context.prelock["prelock_sha256"]
                ):
                    problems.append(f"failed-result history metadata differs: {path.name}")
    except (OSError, KeyError, SemanticReviewError, ValueError) as exc:
        problems.append(str(exc))
    return problems


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path)
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional new report path under candidate116/review_generation/validation.",
    )
    parser.add_argument(
        "--sidecar-self-test",
        action="store_true",
        help="Run no-model duplicate/unexpected sidecar rejection fixtures.",
    )
    return parser.parse_args()


def run_sidecar_self_test() -> int:
    success_names = {
        "proposal.json",
        "model_output.json",
        "codex_events.jsonl",
        "stderr.log",
        "reasoning_summary.txt",
        "llm_call.json",
        "validation.json",
        "receipt.json",
    }
    with tempfile.TemporaryDirectory(
        prefix="semantic_sidecar_selftest_", dir=WORK_ROOT
    ) as temporary:
        output_root = Path(temporary)
        case_id = "SidecarSelfTest"
        case_dir = output_root / case_id
        attempt_one = case_dir / "attempts" / "attempt_01"
        attempt_one.mkdir(parents=True)
        (case_dir / "result.json").write_text("{}\n", encoding="utf-8")
        for name in success_names:
            (attempt_one / name).write_text("\n", encoding="utf-8")
        context = SimpleNamespace(
            output_root=output_root,
            prelock={"prelock_sha256": "a" * 64, "review_id": "sidecar_selftest"},
        )
        row = {"case_unit_id": case_id}
        result = {"chosen_attempt": 1}
        clean = validate_attempt_tree(context, row, result)
        (attempt_one / "duplicate_proposal.json").write_text("{}\n", encoding="utf-8")
        unexpected = validate_attempt_tree(context, row, result)
        (attempt_one / "duplicate_proposal.json").unlink()
        attempt_two = case_dir / "attempts" / "attempt_02"
        attempt_two.mkdir()
        for name in success_names:
            (attempt_two / name).write_text("\n", encoding="utf-8")
        duplicate = validate_attempt_tree(context, row, result)
    passed = not clean and bool(unexpected) and bool(duplicate)
    if not passed:
        raise SemanticReviewError(
            f"sidecar self-test failed: clean={clean}, unexpected={unexpected}, duplicate={duplicate}"
        )
    print(
        json.dumps(
            {
                "status": "self_test_pass",
                "clean_exact_tree_accepted": True,
                "unexpected_sidecar_rejected": True,
                "duplicate_success_attempt_rejected": True,
                "model_calls": 0,
            },
            indent=2,
        )
    )
    return 0


def validate_case_sidecars(
    context: Any,
    row: Mapping[str, Any],
    result: Mapping[str, Any],
) -> list[str]:
    case_id = str(row["case_unit_id"])
    problems: list[str] = []
    try:
        receipt_path = verify_file_binding(
            result["selected_receipt"], f"{case_id} selected receipt", inside_candidate=True
        )
        receipt = load_json(receipt_path, f"{case_id} receipt")
        llm_path = verify_file_binding(receipt["files"]["llm_call"], f"{case_id} llm_call")
        events_path = verify_file_binding(
            receipt["files"]["codex_events"], f"{case_id} Codex events"
        )
        proposal_path = verify_file_binding(
            receipt["files"]["proposal"], f"{case_id} proposal"
        )
        validation_path = verify_file_binding(
            receipt["files"]["validation"], f"{case_id} validation"
        )
        llm = load_json(llm_path, f"{case_id} llm_call")
        verify_self_hash(llm, "llm_call_sha256", f"{case_id} llm_call")
        expected = {
            "schema_version": "androidworld_semantic_review_llm_call/v1",
            "phase": "independent_semantic_review_proposal",
            "case_unit_id": case_id,
            "task_id": row["task_id"],
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": context.config["model"],
            "model_version_claim": None,
            "model_version_evidence_note": (
                "Codex CLI does not expose an immutable backend model snapshot."
            ),
            "reasoning_effort": context.config["reasoning_effort"],
            "sandbox": "read-only",
            "ephemeral": True,
            "ignore_user_config": True,
            "promotion_authorized": False,
        }
        for key, value in expected.items():
            if llm.get(key) != value:
                problems.append(f"llm_call.{key}={llm.get(key)!r}, expected {value!r}")
        if llm.get("input_bindings") != row.get("input_bindings"):
            problems.append("llm_call input bindings differ from review prelock")
        if (llm.get("prelock") or {}).get("prelock_sha256") != context.prelock["prelock_sha256"]:
            problems.append("llm_call prelock id differs")
        command = llm.get("command")
        if (
            not isinstance(command, list)
            or not command
            or command[0] != str(context.codex_binary)
            or command.count("--model") != 1
            or command[command.index("--model") + 1] != context.config["model"]
            or command.count("--sandbox") != 1
            or command[command.index("--sandbox") + 1] != "read-only"
            or command.count("--ephemeral") != 1
            or command.count("--ignore-user-config") != 1
            or f'model_reasoning_effort="{context.config["reasoning_effort"]}"'
            not in command
        ):
            problems.append("llm_call command does not prove exact frozen Codex flags")
        usage = llm.get("token_usage") or {}
        if not isinstance(usage.get("total_tokens"), int) or usage.get("total_tokens", 0) <= 0:
            problems.append("llm_call has no positive total token count")

        events_text = events_path.read_text(encoding="utf-8")
        events, malformed = load_jsonl_events(events_text)
        if malformed:
            problems.append(f"Codex event stream has {len(malformed)} malformed lines")
        if event_response_id(events) != llm.get("response_id"):
            problems.append("Codex event thread id differs from llm_call")
        if not any(event.get("type") == "turn.completed" for event in events):
            problems.append("Codex event stream has no turn.completed event")

        proposal = load_json(proposal_path, f"{case_id} proposal")
        if (proposal.get("review_configuration") or {}).get("response_id") != llm.get("response_id"):
            problems.append("proposal and llm_call response ids differ")
        if proposal.get("promotion_authorized") is not False:
            problems.append("proposal does not explicitly deny promotion")
        validation = load_json(validation_path, f"{case_id} validation")
        verify_self_hash(validation, "validation_sha256", f"{case_id} validation")
        if (
            validation.get("status") != "passed"
            or validation.get("issues") != []
            or validation.get("promotion_authorized") is not False
        ):
            problems.append("selected validation sidecar is not a clean non-authorizing pass")
    except (KeyError, SemanticReviewError, OSError) as exc:
        problems.append(str(exc))
    return problems


def main() -> int:
    args = parse_args()
    context = load_context(args.prelock)
    validator_binding = context.prelock["tool_bindings"].get("independent_validator")
    validator_path = verify_file_binding(
        validator_binding, "independent validator", inside_candidate=True
    )
    if validator_path.resolve() != SCRIPT:
        raise SemanticReviewError("run the byte-prelocked snapshot independent_validator")
    verify_global_inputs(context)
    root_entries = _plain_entries(context.output_root, "semantic-review output root")
    allowed_root_entries = set(context.prelock["case_order"]) | {
        "_batch_summary.json",
        "_concurrency",
        "_history",
    }
    unexpected_root = {item.name for item in root_entries} - allowed_root_entries
    missing_case_roots = set(context.prelock["case_order"]) - {
        item.name for item in root_entries if item.is_dir()
    }
    if unexpected_root or missing_case_roots:
        raise SemanticReviewError(
            f"proposal wave root differs: unexpected={sorted(unexpected_root)}, "
            f"missing_cases={sorted(missing_case_roots)}"
        )
    history_root = context.output_root / "_history"
    if history_root.exists():
        for path in _plain_entries(history_root, "batch-summary history"):
            match = re.fullmatch(r"batch_summary_([0-9a-f]{64})\.json", path.name)
            if not path.is_file() or match is None or match.group(1) != sha256_file(path):
                raise SemanticReviewError(f"invalid batch-summary history entry: {path.name}")
            old_summary = load_json(path, "batch-summary history")
            verify_self_hash(old_summary, "batch_summary_sha256", "batch-summary history")
            if old_summary.get("review_id") != context.prelock["review_id"]:
                raise SemanticReviewError("batch-summary history review id differs")
    summary_path = context.output_root / "_batch_summary.json"
    summary = load_json(summary_path, "semantic-review batch summary")
    verify_self_hash(summary, "batch_summary_sha256", "semantic-review batch summary")
    expected_summary_fields = {
        "schema_version",
        "status",
        "review_id",
        "source_generation_id",
        "generated_at",
        "case_count",
        "completed_count",
        "failed_count",
        "proposed_accepted_count",
        "proposed_rejected_count",
        "max_parallel",
        "prelock",
        "config",
        "concurrency_evidence",
        "cases",
        "review_authority",
        "promotion_authorized",
        "batch_summary_sha256",
    }
    if set(summary) != expected_summary_fields:
        raise SemanticReviewError("semantic-review batch summary field set is not exact")
    expected_summary = {
        "schema_version": "androidworld_semantic_review_batch_summary/v1",
        "status": "pass",
        "review_id": context.prelock["review_id"],
        "source_generation_id": context.prelock["source_generation_id"],
        "case_count": EXPECTED_CASE_COUNT,
        "completed_count": EXPECTED_CASE_COUNT,
        "failed_count": 0,
        "max_parallel": EXPECTED_PARALLELISM,
        "promotion_authorized": False,
    }
    global_issues: list[str] = []
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            global_issues.append(f"batch summary {key}={summary.get(key)!r}, expected {value!r}")
    if summary.get("prelock") != file_binding(context.prelock_path) | {
        "prelock_sha256": context.prelock["prelock_sha256"]
    }:
        global_issues.append("batch summary prelock binding differs")
    if summary.get("config") != file_binding(context.config_path) | {
        "config_sha256": context.config["config_sha256"]
    }:
        global_issues.append("batch summary config binding differs")
    if (
        summary.get("review_authority")
        != "model_proposals_only_root_agent_acceptance_required"
    ):
        global_issues.append("batch summary review authority differs")
    summary_cases = list(summary.get("cases") or [])
    if len(summary_cases) != EXPECTED_CASE_COUNT:
        global_issues.append("batch summary does not contain exactly 116 case rows")
    concurrency_evidence = verify_semantic_concurrency_evidence(
        events_path=context.output_root / "_concurrency" / "events.jsonl",
        audit_path=context.output_root / "_concurrency" / "audit.json",
        expected_case_order=list(context.prelock["case_order"]),
        expected_prelock_sha256=context.prelock["prelock_sha256"],
    )
    if summary.get("concurrency_evidence") != concurrency_evidence:
        global_issues.append("batch summary concurrency evidence differs from raw events")

    case_reports: list[dict[str, Any]] = []
    accepted = 0
    rejected = 0
    for rank, row in enumerate(context.prelock["case_inputs"]):
        case_id = str(row["case_unit_id"])
        case_issues: list[str] = []
        result_path = context.output_root / case_id / "result.json"
        try:
            result = verify_selected_result(context, row, result_path)
            case_issues.extend(validate_case_sidecars(context, row, result))
            case_issues.extend(validate_attempt_tree(context, row, result))
            expected_summary_row = {
                "case_unit_id": case_id,
                "status": "completed",
                "proposal_status": result.get("proposal_status"),
                "promotion_authorized": False,
                "result": file_binding(result_path),
                "result_sha256": result.get("result_sha256"),
                "receipt_sha256": result.get("receipt_sha256"),
            }
            if rank >= len(summary_cases) or summary_cases[rank] != expected_summary_row:
                case_issues.append("batch summary case row/order differs from result")
            if result.get("proposal_status") == "accepted":
                accepted += 1
            elif result.get("proposal_status") == "rejected":
                rejected += 1
            else:
                case_issues.append("result has no accepted/rejected model proposal status")
        except (SemanticReviewError, OSError, KeyError) as exc:
            result = {"proposal_status": None}
            case_issues.append(str(exc))
        case_reports.append(
            {
                "case_unit_id": case_id,
                "selection_rank": row["selection_rank"],
                "status": "pass" if not case_issues else "fail",
                "proposal_status": result.get("proposal_status"),
                "issues": case_issues,
                "promotion_authorized": False,
            }
        )
    verify_global_inputs(context)
    failed_cases = [row for row in case_reports if row["status"] != "pass"]
    if summary.get("proposed_accepted_count") != accepted:
        global_issues.append("batch proposed_accepted_count differs from revalidation")
    if summary.get("proposed_rejected_count") != rejected:
        global_issues.append("batch proposed_rejected_count differs from revalidation")
    passed = not global_issues and not failed_cases and accepted + rejected == EXPECTED_CASE_COUNT
    report = {
        "schema_version": "androidworld_semantic_review_independent_validation/v1",
        "status": "pass" if passed else "fail",
        "validated_at": utc_now(),
        "review_id": context.prelock["review_id"],
        "source_generation_id": context.prelock["source_generation_id"],
        "case_count": EXPECTED_CASE_COUNT,
        "passed_count": EXPECTED_CASE_COUNT - len(failed_cases),
        "failed_count": len(failed_cases),
        "proposed_accepted_count": accepted,
        "proposed_rejected_count": rejected,
        "global_issues": global_issues,
        "cases": case_reports,
        "prelock": file_binding(context.prelock_path)
        | {"prelock_sha256": context.prelock["prelock_sha256"]},
        "batch_summary": file_binding(summary_path)
        | {"batch_summary_sha256": summary["batch_summary_sha256"]},
        "concurrency_evidence": concurrency_evidence,
        "validator": file_binding(SCRIPT),
        "review_authority": "model_proposals_only_root_agent_acceptance_required",
        "promotion_authorized": False,
    }
    report = add_self_hash(report, "validation_report_sha256")
    if args.report:
        report_path = args.report.resolve()
        allowed_root = WORK_ROOT / "review_generation" / "validation"
        try:
            report_path.relative_to(allowed_root.resolve())
        except ValueError as exc:
            raise SemanticReviewError("--report must be inside review_generation/validation") from exc
        if report_path.exists():
            raise SemanticReviewError(f"refusing to overwrite validation report: {report_path}")
        write_json_atomic(report_path, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
