#!/usr/bin/env python3
"""Strictly re-audit the AndroidWorld remaining-75 benchmark-conflict flags.

This pass is deliberately narrower than evidence scoring.  It rechecks the 36
records previously labelled as conflicts (12 cases x 3 agents) against the
actual agent-visible goal, the official task/evaluator source, and the runner
wiring.  Descriptive task_metadata.json drift is reported separately and is
never sufficient to establish a benchmark conflict.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSFER_ROOT = REPO_ROOT / "transfer/androidworld_remaining75_score_gpt54_high_c32_v2_blind_20260720"
JOB_ROOT = TRANSFER_ROOT / "score_job"
SCORE_ROOT = TRANSFER_ROOT / "score_results"
RUN_ROOT = REPO_ROOT / "results/full/androidworld"
DRAFT_ROOT = REPO_ROOT / "results/drafts/androidworld_full100"
SOURCE_ROOT = (
    REPO_ROOT
    / "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source/source_tree"
)
SOURCE_MANIFEST = (
    REPO_ROOT
    / "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/shared_source"
    / "androidworld_source_snapshot_manifest.json"
)
CANONICAL_SEMANTICS_ROOT = (
    REPO_ROOT
    / "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/semantic_records/cases"
)
SEMANTIC_EXTRACTOR = (
    REPO_ROOT
    / "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/scripts"
    / "semantic_extractor.py"
)
PRIOR_AUDIT_ROOT = (
    TRANSFER_ROOT / "benchmark_conflict_audit/superseded_v1_false_positive"
)
DEFAULT_OUTPUT_ROOT = TRANSFER_ROOT / "benchmark_conflict_audit_strict_v2"
EXPECTED_SOURCE_COMMIT = "d9c569f764b3a5629321858de03ff653d0f24056"
EXPECTED_AGENTS = ("agent_a", "agent_b", "agent_c")

AUDIT_STANDARD = (
    "Only after a separate record-level audit, when retained artifacts and source pointers clearly show "
    "that the original benchmark task, target construction, evaluator, oracle, or reward wiring/aggregation "
    "actually checked a different outcome than the benchmark appeared to claim, may the record be marked "
    "as a benchmark conflict."
)


class AuditError(RuntimeError):
    """Raised when strict audit inputs or invariants are invalid."""


@dataclass(frozen=True)
class SourceRange:
    relative: str
    start: int
    end: int

@dataclass(frozen=True)
class CaseReview:
    metadata_lines: tuple[int, int]
    source_ranges: tuple[SourceRange, ...]
    metadata_defect: str
    direct_alignment_finding: str


TASK_METADATA_REL = "android_world/task_metadata.json"
RUNNER_SOURCE = SourceRange("android_world/suite_utils.py", 223, 287)
AGENT_DISPATCH_SOURCE = SourceRange("android_world/suite_utils.py", 453, 460)
METADATA_SUMMARY_SOURCE = SourceRange("android_world/suite_utils.py", 589, 598)
METADATA_MERGE_SOURCE = SourceRange("android_world/suite_utils.py", 703, 707)
IR_EVALUATOR_SOURCE = SourceRange(
    "android_world/task_evals/information_retrieval/information_retrieval.py", 65, 119
)
IR_ANSWER_SOURCE = SourceRange(
    "android_world/task_evals/information_retrieval/proto_utils.py", 147, 205
)


def task_source(relative: str, start: int, end: int) -> SourceRange:
    return SourceRange(relative, start, end)


CASE_REVIEWS: dict[str, CaseReview] = {
    "MarkorAddNoteHeader": CaseReview(
        (182, 188),
        (task_source("android_world/task_evals/single/markor.py", 734, 815),),
        "task_metadata.json omits the rename and uses file_name instead of original_name/new_name.",
        "The dispatched goal includes header insertion and rename; is_successful checks removal of original_name, "
        "existence of new_name, and the exact requested content on the same task params.",
    ),
    "MarkorChangeNoteContent": CaseReview(
        (189, 195),
        (task_source("android_world/task_evals/single/markor.py", 653, 731),),
        "task_metadata.json omits the rename and uses a stale file_name placeholder.",
        "The dispatched goal includes content replacement and rename; is_successful checks the same original_name, "
        "new_name, and updated_content params.",
    ),
    "MarkorEditNote": CaseReview(
        (245, 251),
        (task_source("android_world/task_evals/single/markor.py", 169, 266),),
        "task_metadata.json lists only the header variant although the executable task has header, footer, and replace.",
        "The actual record dispatches its selected edit_type (replace in these three records), and is_successful branches "
        "on that same edit_type and target file.",
    ),
    "NotesRecipeIngredientCount": CaseReview(
        (308, 314),
        (
            task_source(
                "android_world/task_evals/information_retrieval/proto/tasks.textproto", 3169, 3258
            ),
            IR_EVALUATOR_SOURCE,
            IR_ANSWER_SOURCE,
        ),
        "task_metadata.json says 'without abbreviations'; the executable proto asks for the recipe's exact format.",
        "The agent-visible proto prompt and STRING_MATCH expected ingredient_quantity are constructed from the same "
        "task proto and params.",
    ),
    "OsmAndTrack": CaseReview(
        (343, 349),
        (task_source("android_world/task_evals/single/osmand.py", 390, 455),),
        "task_metadata.json contains one fixed two-waypoint example while the executable task generates 2-4 waypoints.",
        "The runtime goal renders params['waypoints']; initialize_task resolves those same waypoints and is_successful "
        "checks them in order in a saved GPX track.",
    ),
    "SportsTrackerActivitiesCountForWeek": CaseReview(
        (698, 704),
        (
            task_source(
                "android_world/task_evals/information_retrieval/proto/tasks.textproto", 2053, 2275
            ),
            IR_EVALUATOR_SOURCE,
            IR_ANSWER_SOURCE,
        ),
        "task_metadata.json omits the executable prompt's Monday week boundary.",
        "The executable prompt, relevant-state date window, exclusions, and COUNT/NUMBER_MATCH target are defined in "
        "one task proto and evaluated from that instantiated proto.",
    ),
    "SportsTrackerActivitiesOnDate": CaseReview(
        (705, 711),
        (
            task_source(
                "android_world/task_evals/information_retrieval/proto/tasks.textproto", 1825, 2051
            ),
            task_source(
                "android_world/task_evals/information_retrieval/activity_app_utils.py", 65, 93
            ),
            IR_EVALUATOR_SOURCE,
            IR_ANSWER_SOURCE,
        ),
        "task_metadata.json says category while the executable prompt says activity type.",
        "This is terminology drift, not target drift: task construction writes the same category value to both the "
        "category and activity_type fields, and the evaluator returns that value.",
    ),
    "SportsTrackerLongestDistanceActivity": CaseReview(
        (726, 732),
        (
            task_source(
                "android_world/task_evals/information_retrieval/proto/tasks.textproto", 2487, 2706
            ),
            IR_EVALUATOR_SOURCE,
            IR_ANSWER_SOURCE,
        ),
        "task_metadata.json omits the Monday week boundary and explicit nearest-integer wording.",
        "The executable prompt, Monday-Sunday target construction, total_distance target, and NUMBER_MATCH tolerance "
        "are defined and evaluated from the same instantiated task proto.",
    ),
    "SportsTrackerTotalDistanceForCategoryOverInterval": CaseReview(
        (738, 744),
        (
            task_source(
                "android_world/task_evals/information_retrieval/proto/tasks.textproto", 2931, 3167
            ),
            IR_EVALUATOR_SOURCE,
            IR_ANSWER_SOURCE,
        ),
        "task_metadata.json says a single integer but omits the executable prompt's explicit rounding wording.",
        "The executable prompt, interval/category state construction, and SUM(total_distance) NUMBER_MATCH target are "
        "defined and evaluated from the same instantiated task proto.",
    ),
    "SportsTrackerTotalDurationForCategoryThisWeek": CaseReview(
        (745, 751),
        (
            task_source(
                "android_world/task_evals/information_retrieval/proto/tasks.textproto", 2708, 2929
            ),
            IR_EVALUATOR_SOURCE,
            IR_ANSWER_SOURCE,
        ),
        "task_metadata.json omits the executable prompt's Monday week boundary.",
        "The executable prompt, Monday-Sunday target construction, and SUM(duration) NUMBER_MATCH target are defined "
        "and evaluated from the same instantiated task proto.",
    ),
    "TasksDueNextWeek": CaseReview(
        (850, 856),
        (
            task_source(
                "android_world/task_evals/information_retrieval/proto/tasks.textproto", 1397, 1524
            ),
            IR_EVALUATOR_SOURCE,
            IR_ANSWER_SOURCE,
        ),
        "task_metadata.json omits the executable prompt's Monday week boundary.",
        "The executable prompt, next-week task state, exclusions, and COUNT/NUMBER_MATCH target are defined and "
        "evaluated from the same instantiated task proto.",
    ),
    "VlcCreateTwoPlaylists": CaseReview(
        (912, 918),
        (task_source("android_world/task_evals/single/vlc.py", 164, 235),),
        "task_metadata.json reuses files1 for playlist two and places the location wording on the opposite clause.",
        "The runtime goal uses files1 and files2 correctly; __init__ creates two evaluators from those same params and "
        "is_successful averages their binary playlist checks, so the runner's >0.5 threshold requires both.",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read JSON {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def line_pointer(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise AuditError(f"invalid source range: {path}:{start}-{end}")
    return f"{repo_rel(path)}::lines {start}-{end}"


def source_pointer(source_range: SourceRange) -> str:
    path = SOURCE_ROOT / source_range.relative
    return line_pointer(path, source_range.start, source_range.end)


def json_pointer(path: Path, selector: str) -> str:
    if not path.is_file():
        raise AuditError(f"missing pointer target: {path}")
    return f"{repo_rel(path)}::{selector}"


def prior_confirmed_cases() -> tuple[set[str], int]:
    path = PRIOR_AUDIT_ROOT / "record_level_conflict_reviews.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    confirmed = [row for row in rows if row.get("confirmed_benchmark_conflict")]
    return {str(row["case_unit_id"]) for row in confirmed}, len(confirmed)


def checklist_hash_audit(receipt: dict[str, Any]) -> dict[str, Any]:
    mismatches: list[str] = []
    for task in receipt["tasks"]:
        task_id = str(task["task_id"])
        case_id = str(task["case_unit_id"])
        packaged = JOB_ROOT / "tasks" / task_id / "checklist.yaml"
        canonical = DRAFT_ROOT / case_id / "checklist.yaml"
        if sha256_file(packaged) != sha256_file(canonical):
            mismatches.append(task_id)
    if mismatches:
        raise AuditError(f"packaged checklist drift: {mismatches[:5]}")
    return {"task_count": len(receipt["tasks"]), "hash_mismatch_count": 0}


def official_metadata_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    metadata_path = SOURCE_ROOT / TASK_METADATA_REL
    manifest_rows = {
        str(row.get("path")): row
        for row in manifest.get("files") or []
        if isinstance(row, dict) and row.get("path")
    }
    manifest_row = manifest_rows.get(TASK_METADATA_REL)
    if not manifest_row or manifest_row.get("source_kind") != "git_source":
        raise AuditError("task_metadata.json is not a pinned git source in the source manifest")
    actual_sha256 = sha256_file(metadata_path)
    if manifest_row.get("sha256") != actual_sha256:
        raise AuditError("task_metadata.json hash differs from the pinned source manifest")

    metadata = load_json(metadata_path)
    by_name = {
        str(row.get("task_name")): row
        for row in metadata
        if isinstance(row, dict) and row.get("task_name")
    }
    for case_id, spec in CASE_REVIEWS.items():
        if case_id not in by_name:
            raise AuditError(f"official task metadata is missing {case_id}")
        metadata_lines = metadata_path.read_text(encoding="utf-8").splitlines()[
            spec.metadata_lines[0] - 1 : spec.metadata_lines[1]
        ]
        if case_id not in "\n".join(metadata_lines):
            raise AuditError(f"metadata source range is not bound to {case_id}")
        if not any(
            case_id
            in "\n".join(
                (SOURCE_ROOT / source_range.relative).read_text(encoding="utf-8").splitlines()[
                    source_range.start - 1 : source_range.end
                ]
            )
            for source_range in spec.source_ranges
        ):
            raise AuditError(f"task/evaluator source ranges are not bound to {case_id}")

        canonical = load_json(CANONICAL_SEMANTICS_ROOT / case_id / "canonical_task_semantics.json")
        comparison = canonical.get("metadata_comparison") or {}
        if not comparison.get("has_difference"):
            raise AuditError(f"canonical source review no longer records metadata drift for {case_id}")
        if comparison.get("metadata_template") != by_name[case_id].get("task_template"):
            raise AuditError(f"canonical/official metadata template mismatch for {case_id}")
    return {
        "path": repo_rel(metadata_path),
        "sha256": actual_sha256,
        "manifest_git_blob_oid": manifest_row.get("git_blob_oid"),
        "reviewed_case_count": len(CASE_REVIEWS),
    }


def final_score_conflict_mentions() -> list[str]:
    pattern = re.compile(
        r"metadata_conflict|benchmark conflict|task_template_vs_runtime|requires_contract_review",
        re.IGNORECASE,
    )
    hits: list[str] = []
    for path in SCORE_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.name not in {"score.json", "score.yaml"} and not path.name.endswith(".reasoning.txt"):
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
            hits.append(repo_rel(path))
    return hits


def review_record(case_id: str, agent: str, spec: CaseReview) -> dict[str, Any]:
    task_id = f"full-androidworld-{case_id}-{agent}"
    native_dir = RUN_ROOT / task_id / "adapter/native_run"
    task_context_path = native_dir / "task_context.json"
    evaluator_input_path = native_dir / "native_evaluator_input.json"
    actions_path = native_dir / "actions/actions.json"
    raw_run_path = RUN_ROOT / task_id / "adapter/raw_run.json"
    checklist_path = JOB_ROOT / "tasks" / task_id / "checklist.yaml"

    task_context = load_json(task_context_path)
    evaluator_input = load_json(evaluator_input_path)
    actions = load_json(actions_path)
    raw_run = load_json(raw_run_path)
    if not isinstance(actions, list) or not actions:
        raise AuditError(f"missing retained actions for {task_id}")

    goal = str(task_context.get("goal") or "")
    prompts = "\n".join(str(row.get("action_prompt") or "") for row in actions if isinstance(row, dict))
    goal_seen_by_agent = bool(goal) and normalized(goal) in normalized(prompts)
    params_bound = task_context.get("params") == evaluator_input.get("task_params")
    task_bound = (
        task_context.get("task_name") == evaluator_input.get("task_name") == case_id
        and raw_run.get("case_unit_id") == case_id
    )
    checklist_text = checklist_path.read_text(encoding="utf-8")
    checklist_uses_task_metadata_prompt = "task_metadata.json" in checklist_text
    if not goal_seen_by_agent or not params_bound or not task_bound:
        raise AuditError(
            f"record binding failed for {task_id}: goal={goal_seen_by_agent}, params={params_bound}, task={task_bound}"
        )
    if checklist_uses_task_metadata_prompt:
        raise AuditError(f"packaged checklist cites task_metadata prompt for {task_id}")

    pointers = [
        json_pointer(task_context_path, "goal"),
        json_pointer(task_context_path, "params"),
        json_pointer(evaluator_input_path, "task_name"),
        json_pointer(evaluator_input_path, "task_params"),
        f"{repo_rel(actions_path)}::$[*].action_prompt",
        json_pointer(raw_run_path, "case_unit_id"),
        source_pointer(
            SourceRange(TASK_METADATA_REL, spec.metadata_lines[0], spec.metadata_lines[1])
        ),
        source_pointer(AGENT_DISPATCH_SOURCE),
        source_pointer(RUNNER_SOURCE),
        *[source_pointer(item) for item in spec.source_ranges],
    ]
    return {
        "schema_version": "androidworld_strict_conflict_record_review/v2",
        "task_id": task_id,
        "case_unit_id": case_id,
        "agent": agent,
        "prior_audit_status": "confirmed_conflict",
        "strict_audit_status": "not_confirmed",
        "confirmed_benchmark_conflict": False,
        "prior_flag_retracted": True,
        "record_checks": {
            "actual_runtime_goal_present_in_retained_agent_prompts": goal_seen_by_agent,
            "task_context_params_equal_native_evaluator_input_params": params_bound,
            "task_and_record_identity_bound": task_bound,
            "packaged_checklist_uses_task_metadata_prompt": checklist_uses_task_metadata_prompt,
        },
        "actual_agent_visible_goal": goal,
        "direct_source_review": spec.direct_alignment_finding,
        "decision_reason": (
            "No different checked outcome is established. The retained agent prompt contains the runtime goal, and "
            "the official task/evaluator source binds the target to the same task params. The observed discrepancy "
            "is confined to descriptive task_metadata.json."
        ),
        "benchmark_issue": {
            "present": True,
            "kind": "official_descriptive_metadata_defect",
            "affects_runtime_task_or_reward_in_this_record": False,
            "description": spec.metadata_defect,
        },
        "our_issue": {
            "present": True,
            "kind": "conflict_audit_false_positive",
            "description": (
                "The prior audit converted a precomputed, manually enumerated metadata-conflict flag directly into "
                "confirmed_benchmark_conflict instead of independently comparing the agent-visible task with the "
                "target/evaluator/reward wiring."
            ),
        },
        "source_pointers": pointers,
        "non_dispositive_inputs_used_as_conflict_proof": {
            "released_evaluator_label": False,
            "native_S_F_U": False,
            "stronger_result": False,
            "native_S_plus_stronger_F": False,
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def markdown_report(summary: dict[str, Any], case_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# AndroidWorld Remaining-75 Strict Conflict Re-audit",
        "",
        "## Outcome",
        "",
        "The prior 36 conflict flags (12 cases x 3 agents) are retracted. Under the strict record-level standard, "
        "this re-audit confirms 0 benchmark conflicts in the previously flagged set.",
        "",
        "The pinned official source does contain 12 stale or inconsistent `task_metadata.json` prompt entries. "
        "Those are benchmark-owned metadata defects, but the executable runner sends `task.goal` to the agent and "
        "the task evaluator checks the same instantiated task parameters. The metadata prompt is not used to run or "
        "score these records.",
        "",
        "## Root Cause",
        "",
        "The prior audit was our code's false positive: it treated a manually enumerated `metadata_conflicts` field "
        "as dispositive and set `confirmed = bool(material_conflicts)`. It did not independently establish a "
        "task/target/evaluator/reward mismatch. In addition, `native_evaluator_output.json::goal` is written by our "
        "adapter from the same `run_result['goal']`; equality with `task_context.json::goal` is a binding check, not "
        "independent evaluator-target evidence.",
        "",
        "## Case Review",
        "",
        "| Case | Strict conflict | Benchmark issue | Direct finding |",
        "|---|---:|---|---|",
    ]
    for row in case_rows:
        lines.append(
            f"| `{row['case_unit_id']}` | No | Metadata defect only | {row['direct_source_review']} |"
        )
    lines.extend(
        [
            "",
            "## Scoring Impact",
            "",
            f"All {summary['score_pipeline_checks']['packaged_checklist_hashes']['task_count']} packaged checklists "
            "match their frozen canonical checklist hashes. None of the 12 reviewed checklists cites "
            "`task_metadata.json`, and no final score/reasoning artifact mentions the prior conflict markers. "
            "The evidence scores therefore are not shown to be invalidated by this audit-code error.",
            "",
            "This report does not claim that all possible AndroidWorld benchmark defects are absent. It retracts "
            "the previously asserted 36 conflicts after a direct re-audit of exactly those records.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    receipt = load_json(JOB_ROOT / "transfer_receipt.json")
    if len(receipt.get("tasks") or []) != 225:
        raise AuditError("expected 225 packaged score tasks")
    prior_cases, prior_count = prior_confirmed_cases()
    if prior_cases != set(CASE_REVIEWS) or prior_count != 36:
        raise AuditError(
            f"prior confirmed set drifted: cases={sorted(prior_cases)}, records={prior_count}"
        )

    manifest = load_json(SOURCE_MANIFEST)
    if manifest.get("source_commit") != EXPECTED_SOURCE_COMMIT or not manifest.get("source_tree_clean"):
        raise AuditError("official source snapshot provenance is not clean or pinned as expected")
    metadata_audit = official_metadata_audit(manifest)

    records = [
        review_record(case_id, agent, CASE_REVIEWS[case_id])
        for case_id in sorted(CASE_REVIEWS)
        for agent in EXPECTED_AGENTS
    ]
    case_rows = []
    for case_id in sorted(CASE_REVIEWS):
        first = next(row for row in records if row["case_unit_id"] == case_id)
        case_rows.append(
            {
                "case_unit_id": case_id,
                "record_count": 3,
                "confirmed_benchmark_conflict": False,
                "prior_flags_retracted": 3,
                "benchmark_metadata_defect": True,
                "benchmark_runtime_task_target_evaluator_conflict": False,
                "metadata_defect": CASE_REVIEWS[case_id].metadata_defect,
                "direct_source_review": first["direct_source_review"],
                "source_pointers": first["source_pointers"][6:],
            }
        )

    score_mentions = final_score_conflict_mentions()
    if score_mentions:
        raise AuditError(f"prior conflict markers leaked into final score outputs: {score_mentions[:5]}")
    checklist_audit = checklist_hash_audit(receipt)
    summary = {
        "schema_version": "androidworld_benchmark_conflict_strict_reaudit/v2",
        "audit_scope": "the 36 records previously flagged as confirmed conflicts",
        "audit_standard": AUDIT_STANDARD,
        "official_source": {
            "commit": EXPECTED_SOURCE_COMMIT,
            "manifest": repo_rel(SOURCE_MANIFEST),
            "source_tree_clean": True,
            "task_metadata": metadata_audit,
        },
        "prior_confirmed_record_count": 36,
        "prior_confirmed_case_count": 12,
        "strict_confirmed_conflict_record_count": 0,
        "strict_confirmed_conflict_case_count": 0,
        "retracted_false_positive_record_count": 36,
        "retracted_false_positive_case_count": 12,
        "benchmark_metadata_defect_case_count": 12,
        "benchmark_runtime_task_target_evaluator_conflict_case_count": 0,
        "root_cause": "our_conflict_audit_code_overclaimed_descriptive_metadata_drift",
        "root_cause_evidence": [
            line_pointer(SEMANTIC_EXTRACTOR, 53, 110),
            source_pointer(METADATA_SUMMARY_SOURCE),
            source_pointer(METADATA_MERGE_SOURCE),
            line_pointer(
                REPO_ROOT / "src/evidence_system/adapters/androidworld_worker.py", 553, 588
            ),
        ],
        "score_pipeline_checks": {
            "packaged_checklist_hashes": checklist_audit,
            "reviewed_checklists_citing_task_metadata_prompt": 0,
            "final_score_or_reasoning_conflict_marker_mentions": 0,
        },
        "non_dispositive_results_used_as_conflict_proof": False,
        "case_reviews": case_rows,
    }

    write_json(output_root / "strict_reaudit_summary.json", summary)
    write_jsonl(output_root / "strict_record_reviews.jsonl", records)
    write_jsonl(output_root / "retracted_prior_conflicts.jsonl", records)
    write_jsonl(output_root / "confirmed_conflicts.jsonl", [])
    write_jsonl(output_root / "benchmark_metadata_defects.jsonl", case_rows)
    (output_root / "README.md").write_text(markdown_report(summary, case_rows), encoding="utf-8")
    with (output_root / "strict_record_reviews.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_id",
                "case_unit_id",
                "agent",
                "prior_audit_status",
                "strict_audit_status",
                "confirmed_benchmark_conflict",
                "prior_flag_retracted",
            ],
        )
        writer.writeheader()
        for row in records:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    print(
        json.dumps(
            {
                "output_root": repo_rel(output_root),
                "records_reaudited": len(records),
                "prior_flags_retracted": len(records),
                "confirmed_benchmark_conflicts": 0,
                "benchmark_metadata_defect_cases": len(case_rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
