#!/usr/bin/env python3
"""Reject or retain raw AppWorld conflict candidates using official relation scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class RecheckError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = parse_args()
    audit_root = args.audit_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise RecheckError(f"refusing existing output root: {output_root}")
    output_root.mkdir(parents=True)
    index = load_json(audit_root / "index.json")
    confirmed: list[str] = []
    for item in index:
        case_id = str(item["case_unit_id"])
        raw_path = audit_root / "adjudication_outputs" / f"{case_id}.json"
        if not raw_path.is_file():
            continue
        raw = load_json(raw_path)
        if raw.get("case_conflict_status") != "confirmed_conflict":
            continue
        confirmed.append(case_id)
        workspace_value = Path(str(item["workspace"]))
        workspace = workspace_value if workspace_value.is_absolute() else audit_root / workspace_value
        projection_path = workspace / "official/base_state/relationship_scope.json"
        if not projection_path.is_file():
            raise RecheckError(f"raw candidate lacks relation-scope projection: {case_id}")
        projection = load_json(projection_path)
        if projection.get("data_version") != "0.2.0":
            raise RecheckError(f"candidate projection version differs: {case_id}")
        if projection.get("outcome_or_released_result_inputs_read") != []:
            raise RecheckError(f"candidate projection is not outcome-blind: {case_id}")
        if projection.get("private_target_exactly_matches_relation_scope") is not True:
            raise RecheckError(f"candidate remains unresolved after relation projection: {case_id}")
        target_ids = projection["private_target_group_ids"]
        all_ids = projection["all_task_added_group_ids"]
        excluded_ids = sorted(set(all_ids) - set(target_ids))
        relation = projection["requested_relation_plural"]
        reason = (
            f"The raw candidate omitted the official {relation} scope. Reconstructing the exact "
            f"AppWorld 0.2.0 initial state from the locked base databases plus task-local SQL "
            f"shows that private target groups {target_ids} exactly equal the task-added groups "
            f"whose non-supervisor members match {relation}; excluded groups {excluded_ids} do "
            "not match that requested relation. The target therefore checks the same scoped "
            "outcome as the instruction, so a different-outcome benchmark conflict is not established."
        )
        records = [
            {
                "task_id": record["task_id"],
                "final_status": "not_confirmed",
                "final_relation": "same_outcome_weaker_or_under_specified",
                "confirmed_benchmark_conflict": False,
                "reason": reason,
            }
            for record in raw["records"]
        ]
        pointers = [
            "official/specs.json::$.instruction",
            "official/specs.json::$.supervisor",
            "official/ground_truth/public_data.json::$.relations",
            "official/ground_truth/private_data.json::$",
            "official/dbs/simple_note.jsonl::$",
            "official/dbs/splitwise.jsonl::$",
            "official/base_state/base_database_lock.json::$",
            "official/base_state/relationship_scope.json::$.private_target_group_ids",
            "official/base_state/relationship_scope.json::$.relation_matching_added_group_ids",
            "official/base_state/relationship_scope.json::$.task_added_groups",
        ]
        write_json(
            output_root / f"{case_id}.json",
            {
                "schema_version": "appworld_conflict_candidate_recheck/v1",
                "case_unit_id": case_id,
                "raw_candidate_status": "confirmed_conflict",
                "recheck_phase": "separate_record_level_review_after_raw_adjudication",
                "final_status": "not_confirmed",
                "different_outcome_description": None,
                "disposition": "rejected_relation_scope_false_positive",
                "reason": reason,
                "records": records,
                "source_pointers": pointers,
                "non_dispositive_inputs_used_as_proof": {
                    "released_evaluator_label": False,
                    "native_evidence_verdict": False,
                    "stronger_measurement_result": False,
                    "historical_v4_score": False,
                },
            },
        )
    if not confirmed:
        raise RecheckError("no raw confirmed candidates were found")
    write_json(
        output_root / "manifest.json",
        {
            "schema_version": "appworld_conflict_candidate_recheck_manifest/v1",
            "raw_confirmed_candidate_count": len(confirmed),
            "raw_confirmed_case_unit_ids": sorted(confirmed),
            "source_data_version": "0.2.0",
            "rule": "Only explicit official source support for a different checked outcome can retain a confirmed benchmark conflict.",
        },
    )
    print(json.dumps({"candidate_count": len(confirmed), "case_unit_ids": sorted(confirmed)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
