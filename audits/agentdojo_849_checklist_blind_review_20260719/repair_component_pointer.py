#!/usr/bin/env python3
"""Apply one verified source-identity correction to a component review pointer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


AUDIT_ROOT = Path(__file__).resolve().parent
SAFE_NAME = "injection__banking__injection_task_8"
BAD = "official/evaluator_oracle_excerpts.json::excerpts[21].content"
GOOD = "official/evaluator_oracle_excerpts.json::excerpts[20].content"


def replace(node: Any) -> int:
    count = 0
    if isinstance(node, dict):
        for key, value in node.items():
            if value == BAD:
                node[key] = GOOD
                count += 1
            else:
                count += replace(value)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            if value == BAD:
                node[index] = GOOD
                count += 1
            else:
                count += replace(value)
    return count


def main() -> int:
    source_path = (
        AUDIT_ROOT
        / "component_reviews"
        / "inputs"
        / SAFE_NAME
        / "sources"
        / "official"
        / "evaluator_oracle_excerpts.json"
    )
    output_path = AUDIT_ROOT / "component_reviews" / "outputs" / f"{SAFE_NAME}.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    excerpts = source["excerpts"]
    if len(excerpts) != 21:
        raise SystemExit(f"Expected 21 excerpts, found {len(excerpts)}")
    target = excerpts[20]
    if "released_evaluator_dispatch" not in target.get("roles", []):
        raise SystemExit("excerpt[20] is not the released evaluator dispatch")
    if not str(target.get("source", {}).get("symbol") or "").endswith(
        "TaskSuite._check_injection_task_security"
    ):
        raise SystemExit("excerpt[20] is not _check_injection_task_security")
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    count = replace(payload)
    if count < 1:
        raise SystemExit(f"No pointer matched {BAD}")
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    audit = {
        "schema_version": "agentdojo_component_pointer_correction/v1",
        "component_id": "banking:injection_task_8",
        "old_pointer": BAD,
        "new_pointer": GOOD,
        "replacement_count": count,
        "basis": {
            "source_excerpt_count": len(excerpts),
            "target_excerpt_id": target["excerpt_id"],
            "target_roles": target["roles"],
            "target_symbol": target["source"]["symbol"],
        },
        "semantic_text_changed": False,
    }
    (AUDIT_ROOT / "component_pointer_correction.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
