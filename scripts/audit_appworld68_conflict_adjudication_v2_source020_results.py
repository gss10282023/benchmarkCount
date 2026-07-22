#!/usr/bin/env python3
"""Validate, candidate-recheck, and summarize the AppWorld-68 conflict audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from run_appworld68_conflict_adjudications import adjudication_errors, load_json, pointer_error
from run_appworld68_record_level_conflict_reviews import sha256_file


EXPECTED_CASES = 68
EXPECTED_RECORDS = 204
EXPECTED_CONFIG = {
    "model": "gpt-5.4",
    "reasoning_effort": "high",
    "service_tier": "default",
    "fast_mode": False,
    "sandbox": "read-only",
    "auth_mode": "codex_login",
}


class AuditError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--candidate-review-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=lambda value: str(value))}


def review_errors(
    review: dict[str, Any],
    raw: dict[str, Any],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    case_id = str(raw["case_unit_id"])
    if review.get("schema_version") != "appworld_conflict_candidate_recheck/v1":
        errors.append("candidate review schema differs")
    if review.get("case_unit_id") != case_id:
        errors.append("candidate review case id differs")
    if review.get("raw_candidate_status") != "confirmed_conflict":
        errors.append("candidate review does not bind raw confirmed status")
    final_status = review.get("final_status")
    if final_status not in {"confirmed_conflict", "not_confirmed", "insufficient"}:
        errors.append("candidate review final status invalid")
    description = review.get("different_outcome_description")
    if final_status == "confirmed_conflict" and not isinstance(description, str):
        errors.append("confirmed review lacks different-outcome description")
    if final_status != "confirmed_conflict" and description is not None:
        errors.append("non-confirmed review has different-outcome description")
    records = review.get("records")
    if not isinstance(records, list) or len(records) != 3:
        errors.append("candidate review record count differs")
        records = []
    expected_ids = {record["task_id"] for record in raw["records"]}
    if {record.get("task_id") for record in records if isinstance(record, dict)} != expected_ids:
        errors.append("candidate review record ids differ")
    for record in records:
        if not isinstance(record, dict):
            continue
        status = record.get("final_status")
        relation = record.get("final_relation")
        confirmed = record.get("confirmed_benchmark_conflict")
        if status != final_status:
            errors.append(f"{record.get('task_id')}: record/case final status differs")
        if status == "confirmed_conflict" and (relation != "different_outcome" or confirmed is not True):
            errors.append(f"{record.get('task_id')}: confirmed contract differs")
        elif status == "not_confirmed" and (
            relation not in {"same_exact", "same_outcome_weaker_or_under_specified"}
            or confirmed is not False
        ):
            errors.append(f"{record.get('task_id')}: not-confirmed contract differs")
        elif status == "insufficient" and (relation != "indeterminate" or confirmed is not None):
            errors.append(f"{record.get('task_id')}: insufficient contract differs")
    pointers = review.get("source_pointers")
    if not isinstance(pointers, list) or not pointers:
        errors.append("candidate review source pointers missing")
        pointers = []
    for required in (
        "official/specs.json::",
        "official/ground_truth/public_data.json::",
        "official/ground_truth/private_data.json::",
        "official/base_state/relationship_scope.json::",
    ):
        if not any(str(pointer).startswith(required) for pointer in pointers):
            errors.append(f"candidate review lacks {required}")
    for pointer in pointers:
        problem = pointer_error(str(pointer), workspace)
        if problem:
            errors.append(problem)
    return errors


def main() -> int:
    args = parse_args()
    audit_root = args.audit_root.resolve()
    candidate_root = args.candidate_review_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise AuditError(f"refusing existing output root: {output_root}")
    output_root.mkdir(parents=True)

    contract_root = audit_root / "contract"
    prompt_path = contract_root / "adjudication.prompt.md"
    schema_path = contract_root / "adjudication.schema.json"
    validator = Draft202012Validator(load_json(schema_path))
    prompt_hash = sha256_file(prompt_path)
    schema_hash = sha256_file(schema_path)
    index = load_json(audit_root / "index.json")
    if not isinstance(index, list) or len(index) != EXPECTED_CASES:
        raise AuditError(f"case denominator differs from {EXPECTED_CASES}")

    errors: list[str] = []
    case_rows: list[dict[str, Any]] = []
    record_rows: list[dict[str, Any]] = []
    raw_candidates: dict[str, dict[str, Any]] = {}
    input_hashes: dict[str, str] = {}
    raw_case_status = Counter()
    raw_record_status = Counter()
    raw_record_relation = Counter()
    released_labels = Counter()
    official_status = Counter()
    official_category = Counter()
    system_additional_issues = Counter()

    for item in sorted(index, key=lambda value: value["case_unit_id"]):
        case_id = str(item["case_unit_id"])
        workspace_value = Path(str(item["workspace"]))
        workspace = workspace_value if workspace_value.is_absolute() else audit_root / workspace_value
        output_path = audit_root / "adjudication_outputs" / f"{case_id}.json"
        manifest_path = output_path.with_suffix(".manifest.json")
        if not output_path.is_file() or not manifest_path.is_file():
            errors.append(f"{case_id}: output or manifest missing")
            continue
        try:
            raw = load_json(output_path)
            manifest = load_json(manifest_path)
            validation = adjudication_errors(raw, item, validator, workspace.resolve())
        except Exception as exc:
            errors.append(f"{case_id}: validation raised {type(exc).__name__}: {exc}")
            continue
        errors.extend(f"{case_id}: {error}" for error in validation)
        if manifest.get("output_sha256") != sha256_file(output_path):
            errors.append(f"{case_id}: output hash differs from manifest")
        if manifest.get("prompt_sha256") != prompt_hash:
            errors.append(f"{case_id}: prompt hash differs")
        if manifest.get("schema_sha256") != schema_hash:
            errors.append(f"{case_id}: schema hash differs")
        for key, expected in EXPECTED_CONFIG.items():
            if manifest.get(key) != expected:
                errors.append(f"{case_id}: manifest {key} differs")
        provenance = raw.get("source_provenance") or {}
        expected_provenance = {
            "status": "corrected_0_2_0_source_lock",
            "historical_packet_version": "0.1.0",
            "adjudication_source_version": "0.2.0",
            "actual_run_version": "0.2.0",
            "exact_actual_task_source_available": True,
        }
        for key, expected in expected_provenance.items():
            if provenance.get(key) != expected:
                errors.append(f"{case_id}: provenance {key} differs")

        raw_case_status[raw["case_conflict_status"]] += 1
        official = raw["official_case_assessment"]
        official_status[official["status"]] += 1
        official_category[official["category"]] += 1
        for issue in raw["our_system_assessment"]["additional_issues"]:
            system_additional_issues[(issue["component"], issue["status"])] += 1
        if raw["case_conflict_status"] == "confirmed_conflict":
            raw_candidates[case_id] = raw
        case_rows.append(
            {
                "case_unit_id": case_id,
                "raw_case_conflict_status": raw["case_conflict_status"],
                "raw_different_outcome_description": raw["different_outcome_description"],
                "official_case_assessment": official,
                "source_provenance": provenance,
                "raw_output_sha256": sha256_file(output_path),
                "manifest_sha256": sha256_file(manifest_path),
            }
        )
        for record in raw["records"]:
            raw_record_status[record["audit_status"]] += 1
            raw_record_relation[record["relation"]] += 1
            released_labels[record["released_evaluator_label"]] += 1
            record_rows.append(
                {
                    "case_unit_id": case_id,
                    "task_id": record["task_id"],
                    "agent_id": record["agent_id"],
                    "released_evaluator_label": record["released_evaluator_label"],
                    "raw_audit_status": record["audit_status"],
                    "raw_relation": record["relation"],
                    "raw_confirmed_benchmark_conflict": record["confirmed_benchmark_conflict"],
                }
            )
        input_hashes[str(output_path.relative_to(audit_root))] = sha256_file(output_path)
        input_hashes[str(manifest_path.relative_to(audit_root))] = sha256_file(manifest_path)

    review_paths = sorted(
        path for path in candidate_root.glob("*.json") if path.name != "manifest.json"
    )
    review_ids = {path.stem for path in review_paths}
    if review_ids != set(raw_candidates):
        errors.append(
            f"candidate review set differs: expected={sorted(raw_candidates)} actual={sorted(review_ids)}"
        )
    reviews: dict[str, dict[str, Any]] = {}
    for path in review_paths:
        review = load_json(path)
        case_id = path.stem
        raw = raw_candidates.get(case_id)
        if raw is None:
            continue
        item = next(row for row in index if row["case_unit_id"] == case_id)
        workspace_value = Path(str(item["workspace"]))
        workspace = workspace_value if workspace_value.is_absolute() else audit_root / workspace_value
        errors.extend(
            f"{case_id}: {error}" for error in review_errors(review, raw, workspace.resolve())
        )
        reviews[case_id] = review
        input_hashes[f"candidate_reviews/{path.name}"] = sha256_file(path)

    if errors:
        write_json(output_root / "validation_errors.json", {"count": len(errors), "errors": errors})
        raise AuditError(f"validation failed with {len(errors)} errors; see validation_errors.json")

    final_case_status = Counter()
    final_record_status = Counter()
    final_record_relation = Counter()
    candidate_dispositions: list[dict[str, Any]] = []
    for case in case_rows:
        case_id = case["case_unit_id"]
        review = reviews.get(case_id)
        if review is None:
            case["final_case_conflict_status"] = case["raw_case_conflict_status"]
            case["final_different_outcome_description"] = case["raw_different_outcome_description"]
        else:
            case["final_case_conflict_status"] = review["final_status"]
            case["final_different_outcome_description"] = review["different_outcome_description"]
            case["candidate_recheck"] = review
            candidate_dispositions.append(review)
        final_case_status[case["final_case_conflict_status"]] += 1

    review_records = {
        record["task_id"]: record
        for review in reviews.values()
        for record in review["records"]
    }
    for record in record_rows:
        review_record = review_records.get(record["task_id"])
        if review_record is None:
            record["final_audit_status"] = record["raw_audit_status"]
            record["final_relation"] = record["raw_relation"]
            record["final_confirmed_benchmark_conflict"] = record[
                "raw_confirmed_benchmark_conflict"
            ]
        else:
            record["final_audit_status"] = review_record["final_status"]
            record["final_relation"] = review_record["final_relation"]
            record["final_confirmed_benchmark_conflict"] = review_record[
                "confirmed_benchmark_conflict"
            ]
        final_record_status[record["final_audit_status"]] += 1
        final_record_relation[record["final_relation"]] += 1

    if len(case_rows) != EXPECTED_CASES or len(record_rows) != EXPECTED_RECORDS:
        raise AuditError("validated denominator differs after validation")

    summary = {
        "schema_version": "appworld68_conflict_audit_validated_summary/v2_source020",
        "case_count": len(case_rows),
        "record_count": len(record_rows),
        "configuration": EXPECTED_CONFIG,
        "source_provenance": {
            "data_version": "0.2.0",
            "actual_run_version": "0.2.0",
            "historical_v4_packet_version": "0.1.0",
            "historical_v4_score_set_validity": "invalid_historical_v4_wrong_source_version",
            "v5_hotfix_status": "corrected_v5_source_lock",
        },
        "raw_model_adjudication": {
            "case_status": counter_dict(raw_case_status),
            "record_status": counter_dict(raw_record_status),
            "record_relation": counter_dict(raw_record_relation),
            "confirmed_candidate_case_ids": sorted(raw_candidates),
        },
        "post_candidate_recheck": {
            "case_status": counter_dict(final_case_status),
            "record_status": counter_dict(final_record_status),
            "record_relation": counter_dict(final_record_relation),
            "confirmed_case_ids": sorted(
                case["case_unit_id"]
                for case in case_rows
                if case["final_case_conflict_status"] == "confirmed_conflict"
            ),
        },
        "released_evaluator_labels": counter_dict(released_labels),
        "raw_official_case_assessment": {
            "status": counter_dict(official_status),
            "category": counter_dict(official_category),
        },
        "raw_model_additional_system_issue_mentions": {
            f"{component}:{status}": count
            for (component, status), count in sorted(system_additional_issues.items())
        },
        "candidate_recheck_count": len(candidate_dispositions),
        "input_file_count": len(input_hashes),
        "input_hash_index_sha256": hashlib.sha256(
            json.dumps(input_hashes, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    write_json(output_root / "summary.json", summary)
    write_jsonl(output_root / "cases.jsonl", case_rows)
    write_jsonl(output_root / "records.jsonl", record_rows)
    write_json(output_root / "candidate_dispositions.json", candidate_dispositions)
    write_json(output_root / "input_files_sha256.json", input_hashes)
    write_json(output_root / "validation.json", {"status": "pass", "errors": []})
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
