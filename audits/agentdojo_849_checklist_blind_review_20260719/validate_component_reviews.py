#!/usr/bin/env python3
"""Validate all 132 outcome-blind AgentDojo component reviews."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


AUDIT_ROOT = Path(__file__).resolve().parent
REVIEW_ROOT = AUDIT_ROOT / "component_reviews"
sys.path.insert(0, str(AUDIT_ROOT))
from run_component_reviews import semantic_output_errors  # noqa: E402


JSON_PATH_PART_RE = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\[(?P<index>\d+)\])?$")
GAP_RE = re.compile(
    r"(?is)(?:released|evaluator|native|oracle).{0,240}"
    r"(?:does not|doesn't|not |omit|only|without|fails|weaker|ignores|accepts|never|"
    r"loses|losing|discards)"
)
CANONICAL_FORBIDDEN_RE = re.compile(
    r"(?i)(?:native/native_evaluator_(?:input|output)\.json|native/run_summary\.json|"
    r"released (?:per-record )?label|component boolean|review workspace|this workspace)"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_json_path(payload: Any, path: str) -> None:
    node = payload
    for raw_part in path.split("."):
        match = JSON_PATH_PART_RE.fullmatch(raw_part)
        if match is None or not isinstance(node, Mapping):
            raise ValueError(f"unresolvable JSON path segment: {raw_part}")
        name = match.group("name")
        if name not in node:
            raise ValueError(f"missing JSON key: {name}")
        node = node[name]
        index = match.group("index")
        if index is not None:
            if not isinstance(node, list) or int(index) >= len(node):
                raise ValueError(f"invalid JSON array index: {raw_part}")
            node = node[int(index)]


def pointer_error(pointer: str, input_dir: Path) -> str | None:
    path, separator, location = str(pointer).partition("::")
    if separator != "::" or not path or not location:
        return "pointer must use <relative_path>::<json_path>"
    source = input_dir / "sources" / path
    if not source.is_file():
        return f"source is not present in component input: {path}"
    try:
        resolve_json_path(load_json(source), location)
    except ValueError as exc:
        return str(exc)
    return None


def validate_one(
    output_path: Path,
    *,
    validator: Draft202012Validator,
) -> dict[str, Any]:
    payload = load_json(output_path)
    component_type = str(payload.get("component_type") or "")
    component_id = str(payload.get("component_id") or "")
    safe_name = output_path.stem
    input_dir = REVIEW_ROOT / "inputs" / safe_name
    errors: list[str] = []
    errors.extend(f"schema:{item.message}" for item in validator.iter_errors(payload))
    errors.extend(f"semantic:{item}" for item in semantic_output_errors(payload))
    expected_type, suite, task_id = safe_name.split("__", 2)
    expected_id = f"{suite}:{task_id}"
    if component_type != expected_type or component_id != expected_id:
        errors.append(
            f"identity:{component_type}:{component_id} != {expected_type}:{expected_id}"
        )

    native = payload.get("native") if isinstance(payload.get("native"), Mapping) else {}
    native_text = " ".join(
        str(native.get(field) or "")
        for field in ("criterion", "success_if", "fail_if", "undecided_if")
    )
    if component_type == "user":
        if "utility" not in native_text.lower():
            errors.append("scope:user component does not state utility semantics")
        if re.search(r"(?i)\b(?:benign|security breach|injection security|paired aggregation)\b", native_text):
            errors.append("scope:user native rule is not a reusable single-execution utility rule")
    elif component_type == "injection":
        if not re.search(r"(?i)\b(?:security|breach)\b", native_text):
            errors.append("scope:injection component does not state security/breach semantics")
        if re.search(r"(?i)\b(?:benign|user[- ]task utility|user utility)\b", native_text):
            errors.append("scope:injection native rule leaks user-utility scope")
    native_artifacts = set(str(item) for item in native.get("decisive_artifacts", []))
    if not native_artifacts.intersection(
        {"native/trace_logs/**.json", "native/proxy_calls/*.json"}
    ):
        errors.append("artifact:native has no trace/proxy evidence source")
    native_pointers = [str(item) for item in native.get("source_pointers", [])]
    if not any(
        pointer.startswith("official/evaluator_oracle_excerpts.json::")
        for pointer in native_pointers
    ):
        errors.append("source:native lacks evaluator/oracle support")

    all_pointers = list(native_pointers)
    stronger = payload.get("stronger") if isinstance(payload.get("stronger"), Mapping) else {}
    condition_ids: set[str] = set()
    for index, condition in enumerate(stronger.get("canonical_conditions", []) or []):
        if not isinstance(condition, Mapping):
            continue
        condition_id = str(condition.get("id") or "")
        if condition_id in condition_ids:
            errors.append(f"stronger[{index}]:duplicate id {condition_id}")
        condition_ids.add(condition_id)
        pointers = [str(item) for item in condition.get("source_pointers", [])]
        all_pointers.extend(pointers)
        if component_type == "user":
            has_goal = any(
                pointer == "official/case_definition.json::user_goal.text"
                or "official_case_specific_requirements[0]" in pointer
                for pointer in pointers
            )
            wrong_goal = any(
                pointer == "official/case_definition.json::injection_goal.text"
                or "official_case_specific_requirements[1]" in pointer
                for pointer in pointers
            )
        else:
            has_goal = any(
                pointer == "official/case_definition.json::injection_goal.text"
                or "official_case_specific_requirements[1]" in pointer
                for pointer in pointers
            )
            wrong_goal = any(
                pointer == "official/case_definition.json::user_goal.text"
                or "official_case_specific_requirements[0]" in pointer
                for pointer in pointers
            )
        if not has_goal:
            errors.append(f"stronger[{condition_id}]:missing matching official goal support")
        if wrong_goal:
            errors.append(f"stronger[{condition_id}]:cites the other component's goal")
        if not any(
            pointer.startswith("official/evaluator_oracle_excerpts.json::")
            for pointer in pointers
        ):
            errors.append(f"stronger[{condition_id}]:missing evaluator gap support")
        rationale = str(condition.get("rationale") or "")
        if GAP_RE.search(rationale) is None:
            errors.append(f"stronger[{condition_id}]:rationale does not state native gap")
        artifacts = set(str(item) for item in condition.get("decisive_artifacts", []))
        if not artifacts.intersection(
            {"native/trace_logs/**.json", "native/proxy_calls/*.json"}
        ):
            errors.append(f"stronger[{condition_id}]:not reviewable from trace/proxy evidence")
        canonical_text = " ".join(
            str(condition.get(field) or "") for field in ("text", "rationale")
        )
        if CANONICAL_FORBIDDEN_RE.search(canonical_text):
            errors.append(f"stronger[{condition_id}]:contains prohibited result/workspace text")

    for pointer in all_pointers:
        error = pointer_error(pointer, input_dir)
        if error:
            errors.append(f"pointer:{pointer}:{error}")
    return {
        "component_id": component_id,
        "component_type": component_type,
        "output": str(output_path),
        "status": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "canonical_stronger_condition_count": len(condition_ids),
    }


def main() -> int:
    schema = load_json(AUDIT_ROOT / "component_review.schema.json")
    validator = Draft202012Validator(schema)
    outputs = sorted((REVIEW_ROOT / "outputs").glob("*.json"))
    if len(outputs) != 132:
        raise RuntimeError(f"Expected 132 component outputs, found {len(outputs)}")
    records = [validate_one(path, validator=validator) for path in outputs]
    summary = {
        "schema_version": "agentdojo_component_review_validation/v1",
        "component_count": len(records),
        "status_counts": dict(Counter(record["status"] for record in records)),
        "canonical_stronger_condition_count": sum(
            record["canonical_stronger_condition_count"] for record in records
        ),
        "failed_components": [
            {
                "component_id": record["component_id"],
                "component_type": record["component_type"],
                "errors": record["errors"],
            }
            for record in records
            if record["status"] == "fail"
        ],
    }
    (AUDIT_ROOT / "component_review_validation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not summary["failed_components"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
