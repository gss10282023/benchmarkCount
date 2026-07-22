#!/usr/bin/env python3
"""Create a path-rebased 849x3 task plan from the immutable score batch plan.

The original task plan records VPS paths.  This tool changes only path fields,
then verifies the local set is exactly the same 2,547 record identities.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-plan", type=Path, required=True)
    parser.add_argument("--checklist-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--score-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = load_json(args.source_plan)
    tasks = source.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 2547:
        raise SystemExit("source task plan must contain exactly 2,547 tasks")

    score_index: dict[str, Path] = {}
    for score_path in args.score_root.resolve().glob("*/**/score.json"):
        run_dir_name = score_path.parents[2].name
        if run_dir_name in score_index:
            raise SystemExit(f"duplicate score run directory: {run_dir_name}")
        score_index[run_dir_name] = score_path
    if len(score_index) != 2547:
        raise SystemExit(f"expected 2,547 local score files, found {len(score_index)}")

    rebased: list[dict[str, Any]] = []
    for task in tasks:
        row = dict(task)
        case_unit_id = str(row["case_unit_id"])
        version, suite, user_task, injection_task = case_unit_id.split(":")
        case_slug = f"{version}_{suite}_{user_task}_{injection_task}"
        run_dir_name = str(row["run_dir_name"])
        checklist = args.checklist_root.resolve() / case_slug / "checklist.yaml"
        evidence = args.evidence_root.resolve() / run_dir_name / "adapter"
        score = score_index.get(run_dir_name)
        if not checklist.is_file():
            raise SystemExit(f"missing checklist: {checklist}")
        if not evidence.is_dir():
            raise SystemExit(f"missing evidence: {evidence}")
        if score is None or not (score.parent / "score_manifest.json").is_file():
            raise SystemExit(f"missing score or manifest for: {run_dir_name}")
        row["checklist_path"] = str(checklist)
        row["evidence_dir"] = str(evidence)
        row["out_prefix"] = str(score.with_suffix(""))
        rebased.append(row)

    case_counts: dict[str, int] = {}
    for row in rebased:
        case_counts[str(row["case_unit_id"])] = case_counts.get(str(row["case_unit_id"]), 0) + 1
    if len(case_counts) != 849 or any(count != 3 for count in case_counts.values()):
        raise SystemExit("rebased task plan is not exactly 849 cases × 3 records")

    output = dict(source)
    output["tasks"] = rebased
    output["path_rebased_for"] = "local_full_record_level_conflict_audit"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": len(rebased), "cases": len(case_counts), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
