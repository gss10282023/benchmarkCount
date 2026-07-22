#!/usr/bin/env python3
"""Validate and summarize the complete AppWorld-68 record-level audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_BUNDLE = (
    REPO_ROOT
    / "experiments/appworld_test_normal_68_system_design_v4_runtime_semantics_gpt54_high_v1"
)
PUBLIC_JOB = (
    REPO_ROOT
    / "transfer/appworld68_tn_blind_score_system_design_v4_runtime_semantics_20260719_v1/public_score_job"
)
SCORE_RUN = (
    REPO_ROOT
    / "transfer/appworld68_tn_blind_score_gpt54_high_default_c34_20260720_v2_runtime_semantics"
)
RETAINED_ROOT = Path("/Users/gss/Downloads/appworld585_20260719_full_v1_completed")
EXPECTED_CASES = 68
AGENTS = ("agent_a", "agent_b", "agent_c")
AGENT_NAMES = {"agent_a": "Agent A", "agent_b": "Agent B", "agent_c": "Agent C"}
TEST_ID_RE = re.compile(r"\[(appworld_test_[A-Za-z0-9._-]+)\]")
SAME_RELATIONS = {"same_exact", "same_outcome_weaker_or_under_specified"}


class AuditError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-output-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--retained-root", type=Path, default=RETAINED_ROOT)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot load JSON {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def locate_records(retained_root: Path, case_ids: list[str]) -> dict[tuple[str, str], Path]:
    found: dict[tuple[str, str], Path] = {}
    for vps in ("vps1", "vps2"):
        for agent in AGENTS:
            base = retained_root / vps / "outputs" / agent
            if not base.is_dir():
                continue
            for case_id in case_ids:
                candidate = base / case_id
                if candidate.is_dir():
                    key = (case_id, agent)
                    if key in found:
                        raise AuditError(f"duplicate retained record: {key}")
                    found[key] = candidate
    expected = {(case_id, agent) for case_id in case_ids for agent in AGENTS}
    if set(found) != expected:
        raise AuditError(f"retained record set differs: missing={sorted(expected-set(found))[:5]}")
    return found


def expected_native_verdict(checks: list[dict[str, Any]]) -> str:
    statuses = [check.get("status") for check in checks]
    if any(status == "contradicted" for status in statuses):
        return "F"
    if statuses and all(status == "supported" for status in statuses):
        return "S"
    return "U"


def expected_stronger_verdict(checks: list[dict[str, Any]]) -> str:
    if not checks:
        return "NA"
    return expected_native_verdict(checks)


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def validate_model_review(case_id: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("case_unit_id") != case_id:
        errors.append("case_unit_id mismatch")
    case_analysis = payload.get("case_analysis")
    if not isinstance(case_analysis, dict):
        return [*errors, "case_analysis missing"]
    relation = case_analysis.get("semantic_relation")
    if relation not in {*SAME_RELATIONS, "different_outcome", "indeterminate"}:
        errors.append("invalid case semantic relation")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 3:
        return [*errors, "record count differs from 3"]
    expected = {(f"{case_id}__{agent}", AGENT_NAMES[agent]) for agent in AGENTS}
    actual = {(str(row.get("task_id")), str(row.get("agent_id"))) for row in records if isinstance(row, dict)}
    if actual != expected:
        errors.append("record identity set mismatch")
    for record in records:
        if not isinstance(record, dict):
            errors.append("record is not an object")
            continue
        status = record.get("audit_status")
        confirmed = record.get("confirmed_benchmark_conflict")
        difference = record.get("different_outcome_description")
        relation = (record.get("semantic_comparison") or {}).get("relation")
        if status == "confirmed_conflict":
            if confirmed is not True or relation != "different_outcome" or not difference:
                errors.append(f"{record.get('task_id')}: invalid confirmed contract")
        elif status == "not_confirmed":
            if confirmed is not False or relation not in SAME_RELATIONS or difference is not None:
                errors.append(f"{record.get('task_id')}: invalid not-confirmed contract")
        elif status == "insufficient":
            if confirmed is not None or relation != "indeterminate" or difference is not None:
                errors.append(f"{record.get('task_id')}: invalid insufficient contract")
        else:
            errors.append(f"{record.get('task_id')}: invalid audit status")
        checks = record.get("non_dispositive_checks")
        if not isinstance(checks, dict) or any(value is not False for value in checks.values()):
            errors.append(f"{record.get('task_id')}: non-dispositive flag violated")
        system = record.get("our_system_review") or {}
        issues = system.get("issues")
        if not isinstance(issues, list):
            errors.append(f"{record.get('task_id')}: system issues malformed")
        elif system.get("overall_status") == "confirmed_issue" and not issues:
            errors.append(f"{record.get('task_id')}: confirmed issue empty")
        elif system.get("overall_status") == "no_issue_found" and issues:
            errors.append(f"{record.get('task_id')}: no-issue has issue rows")
    return errors


def markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def issue_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["无。"]
    output = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    output.extend("| " + " | ".join(markdown_escape(value) for value in row) + " |" for row in rows)
    return output


def main() -> int:
    args = parse_args()
    review_root = args.review_output_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise AuditError(f"refusing existing output root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=False)
    case_source_root = CASE_BUNDLE / "case_packets/appworld"
    case_ids = sorted(path.name for path in case_source_root.iterdir() if path.is_dir())
    if len(case_ids) != EXPECTED_CASES:
        raise AuditError(f"expected {EXPECTED_CASES} cases, found {len(case_ids)}")
    retained = locate_records(args.retained_root.resolve(), case_ids)

    validation_errors: list[str] = []
    case_rows: list[dict[str, Any]] = []
    record_rows: list[dict[str, Any]] = []
    deterministic_records: list[dict[str, Any]] = []
    for case_id in case_ids:
        review_path = review_root / "outputs" / f"{case_id}.json"
        manifest_path = review_root / "outputs" / f"{case_id}.manifest.json"
        if not review_path.is_file() or not manifest_path.is_file():
            validation_errors.append(f"missing review/manifest: {case_id}")
            continue
        review = load_json(review_path)
        manifest = load_json(manifest_path)
        for error in validate_model_review(case_id, review):
            validation_errors.append(f"{case_id}: {error}")
        if manifest.get("output_sha256") != sha256_file(review_path):
            validation_errors.append(f"{case_id}: review manifest output hash mismatch")
        expected_config = {
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "service_tier": "default",
            "fast_mode": False,
            "sandbox": "read-only",
            "auth_mode": "codex_login",
        }
        for key, value in expected_config.items():
            if manifest.get(key) != value:
                validation_errors.append(f"{case_id}: manifest {key} differs")

        official_test_data = load_json(
            case_source_root / case_id / "raw_case/official/ground_truth/test_data.json"
        )
        if not isinstance(official_test_data, list):
            validation_errors.append(f"{case_id}: official test_data not a list")
            official_test_data = []
        checklist_path_a = PUBLIC_JOB / "tasks" / f"{case_id}__agent_a/checklist.yaml"
        checklist_ids = unique_in_order(TEST_ID_RE.findall(checklist_path_a.read_text(encoding="utf-8")))
        if len(checklist_ids) != len(official_test_data):
            validation_errors.append(
                f"{case_id}: checklist registered-test count {len(checklist_ids)} != official {len(official_test_data)}"
            )
        checklist_hashes = {
            sha256_file(PUBLIC_JOB / "tasks" / f"{case_id}__{agent}/checklist.yaml") for agent in AGENTS
        }
        if len(checklist_hashes) != 1:
            validation_errors.append(f"{case_id}: checklist hash differs across agents")

        case_rows.append(
            {
                "case_unit_id": case_id,
                "review_sha256": sha256_file(review_path),
                "case_analysis": review["case_analysis"],
            }
        )
        by_task = {row["task_id"]: row for row in review["records"]}
        for agent in AGENTS:
            task_id = f"{case_id}__{agent}"
            score_dir = SCORE_RUN / "blind_outputs" / task_id
            score = load_json(score_dir / "score.json")
            score_manifest = load_json(score_dir / "score_manifest.json")
            joined = load_json(SCORE_RUN / "postscore_join/joined_records" / f"{task_id}.json")
            original = retained[(case_id, agent)]
            native_output = load_json(original / "native_evaluator_output.json")
            run_summary = load_json(original / "run_summary.json")
            tracker_success = native_output.get("tracker", {}).get("success")
            if not isinstance(tracker_success, bool):
                validation_errors.append(f"{task_id}: tracker.success is not boolean")
                tracker_success = False
            released_label = "success" if tracker_success else "fail"
            if run_summary.get("success") is not tracker_success:
                validation_errors.append(f"{task_id}: run_summary success differs from tracker")
            if joined.get("released_evaluator_label", {}).get("value") != released_label:
                validation_errors.append(f"{task_id}: joined released label differs")
            if joined.get("released_evaluator_label", {}).get("source_sha256") != sha256_file(
                original / "native_evaluator_output.json"
            ):
                validation_errors.append(f"{task_id}: joined label source hash differs")
            if by_task[task_id].get("released_evaluator_label") != released_label:
                validation_errors.append(f"{task_id}: conflict review released label differs")
            score_ids = [row.get("id") for row in score.get("native", {}).get("test_checks", [])]
            if score_ids != checklist_ids:
                validation_errors.append(f"{task_id}: score test ids/order differ from checklist")
            if score.get("native", {}).get("verdict") != expected_native_verdict(
                score.get("native", {}).get("test_checks", [])
            ):
                validation_errors.append(f"{task_id}: native aggregate is not derived")
            if score.get("stronger", {}).get("verdict") != expected_stronger_verdict(
                score.get("stronger", {}).get("condition_checks", [])
            ):
                validation_errors.append(f"{task_id}: stronger aggregate is not derived")
            expected_score_config = {
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "service_tier": "default",
                "fast_mode": False,
                "blind_mode": True,
            }
            for key, value in expected_score_config.items():
                if score_manifest.get(key) != value:
                    validation_errors.append(f"{task_id}: score manifest {key} differs")
            handling = score_manifest.get("released_label_handling") or {}
            if handling.get("resolved_before_or_during_scoring") is not False:
                validation_errors.append(f"{task_id}: released label was not blind")
            comparison_expected = (
                "match"
                if (released_label == "success" and score["native"]["verdict"] == "S")
                or (released_label == "fail" and score["native"]["verdict"] == "F")
                else "mismatch"
            )
            if joined.get("comparison", {}).get("status") != comparison_expected:
                validation_errors.append(f"{task_id}: joined comparison differs")
            evidence_index = load_json(PUBLIC_JOB / "tasks" / task_id / "evidence/index.json")
            if evidence_index.get("released_result_artifacts_present") is not False:
                validation_errors.append(f"{task_id}: blind evidence says released results present")
            if evidence_index.get("component_evaluator_outputs_present") is not False:
                validation_errors.append(f"{task_id}: blind evidence says component outputs present")

            record_review = by_task[task_id]
            record_rows.append(
                {
                    "case_unit_id": case_id,
                    "task_id": task_id,
                    "agent_id": record_review["agent_id"],
                    "released_evaluator_label": released_label,
                    "native_evidence_verdict": score["native"]["verdict"],
                    "stronger_measurement_verdict": score["stronger"]["verdict"],
                    "label_comparison": joined["comparison"]["status"],
                    "record_level_review": record_review,
                }
            )
            deterministic_records.append(
                {
                    "task_id": task_id,
                    "official_test_count": len(official_test_data),
                    "checklist_test_count": len(checklist_ids),
                    "released_label": released_label,
                    "native_verdict": score["native"]["verdict"],
                    "comparison": comparison_expected,
                    "run_summary_tracker_bound": run_summary.get("success") is tracker_success,
                    "blind_label_isolation_declared": handling.get("resolved_before_or_during_scoring") is False,
                }
            )

    if validation_errors:
        write_json(
            output_root / "VALIDATION_FAILURE.json",
            {"created_at": utc_now(), "error_count": len(validation_errors), "errors": validation_errors},
        )
        raise AuditError(f"validation failed with {len(validation_errors)} errors; see VALIDATION_FAILURE.json")
    if len(case_rows) != 68 or len(record_rows) != 204:
        raise AuditError(f"validated denominator differs: cases={len(case_rows)} records={len(record_rows)}")

    record_status_counts = Counter(
        row["record_level_review"]["audit_status"] for row in record_rows
    )
    relation_counts = Counter(
        row["record_level_review"]["semantic_comparison"]["relation"] for row in record_rows
    )
    official_status_counts = Counter(
        row["case_analysis"]["official_benchmark_assessment"]["status"] for row in case_rows
    )
    checklist_status_counts = Counter(
        row["case_analysis"]["checklist_and_case_packet_assessment"]["status"] for row in case_rows
    )
    system_status_counts = Counter(
        row["record_level_review"]["our_system_review"]["overall_status"] for row in record_rows
    )
    system_component_counts: Counter[str] = Counter()
    for row in record_rows:
        for issue in row["record_level_review"]["our_system_review"]["issues"]:
            system_component_counts[issue["component"]] += 1
    confirmed = [row for row in record_rows if row["record_level_review"]["audit_status"] == "confirmed_conflict"]
    insufficient = [row for row in record_rows if row["record_level_review"]["audit_status"] == "insufficient"]
    official_flagged = [
        row
        for row in case_rows
        if row["case_analysis"]["official_benchmark_assessment"]["status"] != "no_issue_found"
    ]
    checklist_flagged = [
        row
        for row in case_rows
        if row["case_analysis"]["checklist_and_case_packet_assessment"]["status"] != "pass"
    ]
    system_flagged = [
        row
        for row in record_rows
        if row["record_level_review"]["our_system_review"]["overall_status"] != "no_issue_found"
    ]

    summary = {
        "schema_version": "appworld68_complete_record_level_audit_summary/v1",
        "created_at": utc_now(),
        "scope": {"benchmark": "AppWorld", "dataset": "test_normal", "case_count": 68, "record_count": 204},
        "standard": (
            "Confirmed benchmark conflict requires retained artifacts plus explicit source pointers proving "
            "that task/target/evaluator/oracle/reward wiring checked a different outcome."
        ),
        "record_audit_status_counts": dict(sorted(record_status_counts.items())),
        "record_semantic_relation_counts": dict(sorted(relation_counts.items())),
        "official_benchmark_assessment_counts_by_case": dict(sorted(official_status_counts.items())),
        "checklist_case_packet_assessment_counts_by_case": dict(sorted(checklist_status_counts.items())),
        "our_system_assessment_counts_by_record": dict(sorted(system_status_counts.items())),
        "our_system_issue_component_counts": dict(sorted(system_component_counts.items())),
        "confirmed_conflict_record_ids": [row["task_id"] for row in confirmed],
        "insufficient_record_ids": [row["task_id"] for row in insufficient],
        "official_flagged_case_ids": [row["case_unit_id"] for row in official_flagged],
        "checklist_or_case_packet_flagged_case_ids": [row["case_unit_id"] for row in checklist_flagged],
        "our_system_flagged_record_ids": [row["task_id"] for row in system_flagged],
        "deterministic_validation": {
            "status": "pass",
            "error_count": 0,
            "case_count": 68,
            "record_count": 204,
            "official_registered_test_checks_per_agent_total": sum(
                row["official_test_count"] for row in deterministic_records
            ),
            "score_and_checklist_test_counts_match": True,
            "released_label_and_tracker_success_match": True,
            "run_summary_and_tracker_success_match": True,
            "blind_label_isolation_declarations_match": True,
            "score_aggregates_derived": True,
        },
    }
    write_json(output_root / "summary.json", summary)
    write_json(
        output_root / "deterministic_validation.json",
        {
            "schema_version": "appworld68_record_level_audit_deterministic_validation/v1",
            "created_at": utc_now(),
            "status": "pass",
            "records": deterministic_records,
        },
    )
    write_jsonl(output_root / "case_level_reviews.jsonl", case_rows)
    write_jsonl(output_root / "record_level_reviews.jsonl", record_rows)

    report: list[str] = [
        "# AppWorld-68 complete record-level conflict and implementation audit",
        "",
        "## Scope and decision rule",
        "",
        "All 68 `test_normal` cases and all 204 agent records were reviewed. A record is marked as a confirmed benchmark conflict only when retained primary artifacts and explicit source pointers establish that the original task, target construction, evaluator/oracle, or reward wiring/aggregation checked a different outcome than the benchmark appeared to claim. Label disagreement, native S/F/U, and stronger results are routing/context only.",
        "",
        "## Counts",
        "",
        f"- Record conflict status: `{dict(sorted(record_status_counts.items()))}`",
        f"- Semantic relation: `{dict(sorted(relation_counts.items()))}`",
        f"- Official case assessment: `{dict(sorted(official_status_counts.items()))}`",
        f"- Checklist/case-packet assessment: `{dict(sorted(checklist_status_counts.items()))}`",
        f"- Our-system record assessment: `{dict(sorted(system_status_counts.items()))}`",
        f"- Our-system issue components: `{dict(sorted(system_component_counts.items()))}`",
        "",
        "## Confirmed benchmark conflicts",
        "",
        *issue_table(
            ["record", "released", "relation", "different outcome"],
            [
                [
                    row["task_id"],
                    row["released_evaluator_label"],
                    row["record_level_review"]["semantic_comparison"]["relation"],
                    row["record_level_review"]["different_outcome_description"],
                ]
                for row in confirmed
            ],
        ),
        "",
        "## Official benchmark/case issues or limitations",
        "",
        *issue_table(
            ["case", "status", "category", "description"],
            [
                [
                    row["case_unit_id"],
                    row["case_analysis"]["official_benchmark_assessment"]["status"],
                    row["case_analysis"]["official_benchmark_assessment"]["category"],
                    row["case_analysis"]["official_benchmark_assessment"]["description"],
                ]
                for row in official_flagged
            ],
        ),
        "",
        "## Checklist or case-packet issues",
        "",
        *issue_table(
            ["case", "status", "description"],
            [
                [
                    row["case_unit_id"],
                    row["case_analysis"]["checklist_and_case_packet_assessment"]["status"],
                    row["case_analysis"]["checklist_and_case_packet_assessment"]["description"],
                ]
                for row in checklist_flagged
            ],
        ),
        "",
        "## Our code/package/scorer/join issues",
        "",
        *issue_table(
            ["record", "status", "components", "summary"],
            [
                [
                    row["task_id"],
                    row["record_level_review"]["our_system_review"]["overall_status"],
                    ", ".join(
                        issue["component"]
                        for issue in row["record_level_review"]["our_system_review"]["issues"]
                    )
                    or "unresolved",
                    row["record_level_review"]["our_system_review"]["summary"],
                ]
                for row in system_flagged
            ],
        ),
        "",
        "## Insufficient record-level conflict decisions",
        "",
        *issue_table(
            ["record", "reason"],
            [[row["task_id"], row["record_level_review"]["reason"]] for row in insufficient],
        ),
        "",
        "## Deterministic validation",
        "",
        "The 68/204 denominator, task/agent identities, official test counts, checklist-to-score test IDs, score aggregation, blind-label isolation declarations, original `tracker.success`, `run_summary.success`, joined released labels, audit manifests, and model configuration were all independently revalidated. No validation error remained.",
        "",
    ]
    (output_root / "REVIEW_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
