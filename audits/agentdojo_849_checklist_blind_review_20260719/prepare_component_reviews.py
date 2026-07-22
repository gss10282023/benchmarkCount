#!/usr/bin/env python3
"""Prepare outcome-blind user/injection component review workspaces."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
AUDIT_ROOT = Path(__file__).resolve().parent
CHECKLIST_ROOT = AUDIT_ROOT / "original_checklists"
PACKET_ROOT = PACKAGE_ROOT / "experiments/agentdojo_full_v1.2.2_direct/case_packets/agentdojo"
OUTPUT_ROOT = AUDIT_ROOT / "component_reviews"


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def support_set(condition: Mapping[str, Any]) -> set[str]:
    return {str(item) for item in condition.get("support", []) if isinstance(item, str)}


def condition_type(condition: Mapping[str, Any]) -> str:
    support = support_set(condition)
    user = any(
        pointer == "official/case_definition.json::user_goal.text"
        or "task_support.user" in pointer
        or "user_goal_candidate_rule" in pointer
        or "official_case_specific_requirements[0]" in pointer
        for pointer in support
    )
    injection = any(
        pointer == "official/case_definition.json::injection_goal.text"
        or "task_support.injection" in pointer
        or "attack_goal_candidate_rule" in pointer
        or "official_case_specific_requirements[1]" in pointer
        for pointer in support
    )
    if user and not injection:
        return "user"
    if injection and not user:
        return "injection"
    text = " ".join(str(condition.get(key) or "") for key in ("id", "text", "rationale")).lower()
    return "injection" if any(word in text for word in ("injection", "attack", "security", "exfiltrat")) else "user"


def unique_objects(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for value in values:
        signature = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if signature not in seen:
            seen.add(signature)
            result.append(value)
    return result


def candidate_rule_texts(checklist: Mapping[str, Any], component_type: str) -> dict[str, list[str]]:
    native = checklist.get("native") if isinstance(checklist.get("native"), Mapping) else {}
    result: dict[str, list[str]] = {"success_if": [], "fail_if": [], "undecided_if": []}
    for field in result:
        for item in native.get(field, []) or []:
            if not isinstance(item, Mapping):
                continue
            text = str(item.get("text") or "")
            lowered = text.lower()
            if any(token in lowered for token in ("authoritative", "boolean is absent", "released record")):
                continue
            if component_type == "user" and "utility" not in lowered:
                continue
            if component_type == "injection" and not any(token in lowered for token in ("security", "breach", "attack")):
                continue
            result[field].append(text)
    return result


def main() -> int:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    candidates: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    rule_candidates: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(
        lambda: {"success_if": [], "fail_if": [], "undecided_if": []}
    )
    origins: dict[tuple[str, str], list[str]] = defaultdict(list)

    for checklist_path in sorted(CHECKLIST_ROOT.glob("*/checklist.yaml")):
        checklist = load_yaml(checklist_path)
        case_id = str(checklist["case_unit_id"])
        _, suite, user_task, injection_task = case_id.split(":")
        packet_dir = PACKET_ROOT / case_id.replace(":", "_")
        for component_type, component_name in (
            ("user", f"{suite}:{user_task}"),
            ("injection", f"{suite}:{injection_task}"),
        ):
            key = (component_type, component_name)
            groups.setdefault(
                key,
                {
                    "representative_case_unit_id": case_id,
                    "representative_packet_dir": str(packet_dir),
                },
            )
            origins[key].append(case_id)
            extracted = candidate_rule_texts(checklist, component_type)
            for field, values in extracted.items():
                rule_candidates[key][field].extend(values)

        stronger = checklist.get("stronger") if isinstance(checklist.get("stronger"), Mapping) else {}
        for raw_condition in stronger.get("additional_conditions", []) or []:
            if not isinstance(raw_condition, Mapping):
                continue
            ctype = condition_type(raw_condition)
            component_name = f"{suite}:{user_task}" if ctype == "user" else f"{suite}:{injection_task}"
            candidates[(ctype, component_name)].append(
                {
                    "origin_case_unit_id": case_id,
                    "id": raw_condition.get("id"),
                    "text": raw_condition.get("text"),
                    "rationale": raw_condition.get("rationale"),
                    "decisive_artifacts": raw_condition.get("decisive_artifacts", []),
                    "support": raw_condition.get("support", []),
                }
            )

    if len(groups) != 132:
        raise RuntimeError(f"Expected 132 unique components, found {len(groups)}")

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    (OUTPUT_ROOT / "inputs").mkdir(parents=True)
    (OUTPUT_ROOT / "outputs").mkdir(parents=True)
    (OUTPUT_ROOT / "logs").mkdir(parents=True)

    index = []
    for (component_type, component_id), metadata in sorted(groups.items()):
        safe_name = f"{component_type}__{component_id.replace(':', '__')}"
        workspace = OUTPUT_ROOT / "inputs" / safe_name
        sources = workspace / "sources"
        sources.mkdir(parents=True)
        packet_dir = Path(metadata["representative_packet_dir"])
        raw_case = packet_dir / "raw_case"
        for relative in (
            "official/case_definition.json",
            "official/evaluator_oracle_excerpts.json",
            "official/state_schema_excerpts.json",
            "derived/stronger_measurement_basis.json",
        ):
            source = raw_case / relative
            destination = sources / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        candidate_values = unique_objects(candidates.get((component_type, component_id), []))
        rules = {
            field: sorted(set(values))
            for field, values in rule_candidates[(component_type, component_id)].items()
        }
        review_input = {
            "schema_version": "agentdojo_component_review_input/v1",
            "component_type": component_type,
            "component_id": component_id,
            "representative_case_unit_id": metadata["representative_case_unit_id"],
            "paired_case_count": len(set(origins[(component_type, component_id)])),
            "actual_independent_artifact_contract": {
                "allowed": [
                    "native/trace_logs/**.json",
                    "native/proxy_calls/*.json",
                    "logs/{sealed_worker.stdout.log,sealed_worker.stderr.log}",
                    "adapter/{artifact_manifest,environment}.json"
                ],
                "prohibited_as_decisive": [
                    "native/native_evaluator_output.json",
                    "native/run_summary.json",
                    "released evaluator label and equivalent component results"
                ],
                "native_evaluator_input_fact": "metadata only; no evaluator-visible pre/post state or model/tool content",
                "standalone_full_pre_post_state_snapshot": False
            },
            "existing_native_rule_candidates": rules,
            "existing_stronger_candidates": candidate_values,
        }
        (workspace / "review_input.json").write_text(
            json.dumps(review_input, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        index.append(
            {
                "component_type": component_type,
                "component_id": component_id,
                "safe_name": safe_name,
                "workspace": str(workspace),
                "output": str(OUTPUT_ROOT / "outputs" / f"{safe_name}.json"),
                "log": str(OUTPUT_ROOT / "logs" / f"{safe_name}.jsonl"),
            }
        )

    (OUTPUT_ROOT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"prepared {len(index)} component review workspaces under {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
