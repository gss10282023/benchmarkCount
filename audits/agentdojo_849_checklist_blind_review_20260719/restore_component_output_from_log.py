#!/usr/bin/env python3
"""Restore a schema-valid component JSON output from its completed Codex JSONL log."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


AUDIT_ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("safe_name")
    args = parser.parse_args()
    safe_name = args.safe_name
    log_path = AUDIT_ROOT / "component_reviews" / "logs" / f"{safe_name}.jsonl"
    output_path = AUDIT_ROOT / "component_reviews" / "outputs" / f"{safe_name}.json"
    schema = json.loads((AUDIT_ROOT / "component_review.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    candidates = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") if isinstance(event, dict) else None
        if not isinstance(item, dict) or item.get("type") != "agent_message":
            continue
        try:
            payload = json.loads(str(item.get("text") or ""))
        except json.JSONDecodeError:
            continue
        if not list(validator.iter_errors(payload)):
            candidates.append(payload)
    if not candidates:
        raise SystemExit(f"No schema-valid agent_message payload in {log_path}")
    payload = candidates[-1]
    expected_type, suite, task_id = safe_name.split("__", 2)
    if payload.get("component_type") != expected_type or payload.get("component_id") != f"{suite}:{task_id}":
        raise SystemExit("Recovered payload identity mismatch")
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
