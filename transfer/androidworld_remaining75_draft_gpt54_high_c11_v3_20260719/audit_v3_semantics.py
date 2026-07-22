#!/usr/bin/env python3
"""Conservative semantic lint for the AndroidWorld V3 pre-outcome drafts."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def strings(node: Any) -> list[str]:
    if isinstance(node, dict):
        return [item for value in node.values() for item in strings(value)]
    if isinstance(node, list):
        return [item for value in node for item in strings(value)]
    return [node] if isinstance(node, str) else []


def issue(items: list[dict[str, str]], case_id: str, code: str, message: str) -> None:
    items.append({"case_id": case_id, "code": code, "message": message})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-ids", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    case_ids = [line.strip() for line in args.case_ids.read_text(encoding="utf-8").splitlines() if line.strip()]
    blocking: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    inventory: list[dict[str, Any]] = []

    for case_id in case_ids:
        path = args.result_root / case_id / "checklist.yaml"
        if not path.is_file():
            issue(blocking, case_id, "missing_checklist", str(path))
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        native = data.get("native") or {}
        native_text = " ".join(strings(native))
        goal = str((native.get("user_goal") or {}).get("text") or "")
        success_text = " ".join(strings(native.get("success_if") or []))
        failure_text = " ".join(strings(native.get("fail_if") or []))
        undecided_text = " ".join(strings(native.get("undecided_if") or []))

        if not re.search(r"(?i)\bdone\s*=\s*true\b", native_text):
            issue(blocking, case_id, "missing_done_success_semantics", "Native rules do not state the AndroidWorld done=true gate")
        states_done_failure = bool(
            re.search(r"(?i)\bdone`?(?:\s+value)?\s*(?:=|is)\s*`?false\b", failure_text)
            or re.search(r"(?i)\b(?:never|did not|does not)\b.{0,60}\bdone\s*=\s*true\b", failure_text)
        )
        if not states_done_failure:
            issue(blocking, case_id, "missing_done_failure_semantics", "fail_if does not state the official done=false failure gate")

        conditions = ((data.get("stronger") or {}).get("additional_conditions") or [])
        condition_text = " ".join(strings(conditions))
        inventory.append(
            {
                "case_id": case_id,
                "goal": goal,
                "condition_count": len(conditions),
                "conditions": [
                    {
                        "id": condition.get("id"),
                        "text": condition.get("text"),
                        "rationale": condition.get("rationale"),
                        "support": condition.get("support"),
                    }
                    for condition in conditions
                ],
            }
        )
        for index, condition in enumerate(conditions):
            support = condition.get("support") or []
            artifacts = condition.get("decisive_artifacts") or []
            combined = " ".join(strings(condition))
            if not support or not any(str(pointer).startswith(("official/", "derived/")) for pointer in support):
                issue(blocking, case_id, "stronger_missing_case_source", f"condition {index} lacks case-packet source support")
            if not artifacts or any(not (artifact.get("support") or []) for artifact in artifacts):
                issue(blocking, case_id, "stronger_missing_decisive_artifact", f"condition {index} lacks a supported retainable artifact")
            if re.search(r"(?i)benchmark[ -]conflict", combined):
                issue(blocking, case_id, "conflict_in_draft", f"condition {index} encodes benchmark conflict")
            if re.search(r"(?i)(initial|pre[- ]run).{0,80}(must|require|not on|not off)|final.{0,50}state.{0,80}(still|remain).{0,50}(answer|count)", combined):
                issue(warnings, case_id, "possible_stronger_state_overreach", f"condition {index} may add an unstated initial/final-state requirement")
            if re.search(r"(?i)(metadata template|implementation typo|trailing newline|serialization detail)", combined):
                issue(warnings, case_id, "possible_non_dispatched_or_representation_requirement", f"condition {index} may rely on non-dispatched or incidental representation semantics")

        numeric_format_goal = re.search(r"(?i)\b(?:single|one|just a) (?:base-10 )?(?:integer|number)\b", goal)
        numeric_native_gap = re.search(r"(?i)\b(NUMBER_MATCH|numeric tolerance|tolerance|float\s*\()", native_text)
        if numeric_format_goal and numeric_native_gap and not re.search(r"(?i)\b(integer|single number|exact(?:ly)?(?: the)? (?:number|answer|value)|format)\b", condition_text):
            issue(warnings, case_id, "possible_missing_numeric_format_stronger", "Official goal has an integer/number format while native semantics are tolerant or float-cast")

        fuzzy_native = re.search(r"(?i)\b(fuzzy|approximate|similarity|STRING_MATCH)\b", native_text)
        exact_goal = re.search(r"(?i)\b(title(?:s)? only|specified (?:text|message|content)|requested (?:text|message|content)|entire content|exact)\b", goal)
        if fuzzy_native and exact_goal and not re.search(r"(?i)\bexact|no (?:omissions|duplicates)|verbatim\b", condition_text):
            issue(warnings, case_id, "possible_missing_exactness_stronger", "Official goal specifies concrete text/title content while native semantics use fuzzy matching")

    report = {
        "schema_version": "androidworld_v3_semantic_lint/v1",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(case_ids),
        "decision": "fail" if blocking else "pass_with_manual_review" if warnings else "pass",
        "counts": {
            "blocking": len(blocking),
            "warnings": len(warnings),
            "stronger_positive_cases": sum(row["condition_count"] > 0 for row in inventory),
            "stronger_conditions": sum(row["condition_count"] for row in inventory),
        },
        "blocking_issues": blocking,
        "manual_review_warnings": warnings,
        "stronger_inventory": inventory,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "counts": report["counts"]}, ensure_ascii=False))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
