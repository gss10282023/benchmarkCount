#!/usr/bin/env python3
"""Mechanically replace selector-style support pointers with exact array indices."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml


PART = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\[(?P<selector>[^]]+)\])?$")
INDEX = re.compile(r"^\d+$")
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--deterministic-audit-jsonl", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-cases", type=int, default=8)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def normalize_pointer(packet_dir: Path, pointer: str) -> tuple[str, list[dict[str, Any]]]:
    source, separator, remainder = pointer.partition("::")
    if separator != "::":
        return pointer, []
    location, symbol_separator, symbol = remainder.partition("::")
    current: Any = load_json(packet_dir / "raw_case" / source)
    normalized_parts: list[str] = []
    changes: list[dict[str, Any]] = []
    for raw_part in location.split("."):
        match = PART.fullmatch(raw_part)
        if match is None or not isinstance(current, Mapping):
            raise ValueError(f"cannot traverse pointer: {pointer}")
        name = match.group("name")
        if name not in current:
            raise ValueError(f"missing field while traversing pointer: {pointer}")
        current = current[name]
        selector = match.group("selector")
        normalized_part = name
        if selector is not None:
            if not isinstance(current, list):
                raise ValueError(f"selector does not address an array: {pointer}")
            if INDEX.fullmatch(selector):
                index = int(selector)
            else:
                key, equals, expected = selector.partition("=")
                if equals != "=" or not key or not expected:
                    raise ValueError(f"unsupported selector: {pointer}")
                matches = [
                    index
                    for index, item in enumerate(current)
                    if isinstance(item, Mapping) and str(item.get(key)) == expected
                ]
                if len(matches) != 1:
                    raise ValueError(f"selector must match exactly one item: {pointer}")
                index = matches[0]
                changes.append(
                    {
                        "array": name,
                        "selector": selector,
                        "resolved_index": index,
                    }
                )
            if index >= len(current):
                raise ValueError(f"array index out of range: {pointer}")
            current = current[index]
            normalized_part = f"{name}[{index}]"
        normalized_parts.append(normalized_part)
    normalized = f"{source}::{'.'.join(normalized_parts)}"
    if symbol_separator:
        normalized += f"::{symbol}"
    return normalized, changes


def rewrite_supports(
    node: Any,
    packet_dir: Path,
    path: str = "$",
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "support" and isinstance(value, list):
                for index, pointer in enumerate(value):
                    if not isinstance(pointer, str):
                        continue
                    normalized, selector_changes = normalize_pointer(packet_dir, pointer)
                    if normalized != pointer:
                        value[index] = normalized
                        changes.append(
                            {
                                "checklist_path": f"{path}.support[{index}]",
                                "old_pointer": pointer,
                                "new_pointer": normalized,
                                "selector_resolutions": selector_changes,
                            }
                        )
            else:
                changes.extend(rewrite_supports(value, packet_dir, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            changes.extend(rewrite_supports(value, packet_dir, f"{path}[{index}]"))
    return changes


def main() -> int:
    args = parse_args()
    selected: list[str] = []
    with args.deterministic_audit_jsonl.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if "unresolvable_source_pointer" in row.get("blocking_finding_codes", []):
                selected.append(row["directory_name"])
    if len(selected) != args.expected_cases:
        raise ValueError(
            f"expected {args.expected_cases} selector-pointer cases, found {len(selected)}"
        )

    args.output_root.mkdir(parents=True, exist_ok=False)
    receipts: list[dict[str, Any]] = []
    for name in sorted(selected):
        source = args.draft_root / name / "checklist.yaml"
        checklist = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not isinstance(checklist, dict):
            raise ValueError(f"expected checklist object: {source}")
        changes = rewrite_supports(checklist, args.packet_root / name)
        if not changes:
            raise ValueError(f"no selector-style pointers changed: {name}")
        destination = args.output_root / name / "checklist.yaml"
        destination.parent.mkdir(parents=True)
        destination.write_text(
            yaml.safe_dump(checklist, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        receipts.append(
            {
                "directory_name": name,
                "source_checklist_sha256": sha256(source),
                "normalized_checklist_sha256": sha256(destination),
                "change_count": len(changes),
                "changes": changes,
            }
        )

    manifest = {
        "schema_version": "agentdojo_selector_pointer_normalization/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(receipts),
        "agent_outcomes_read": False,
        "semantic_text_modified": False,
        "cases": receipts,
    }
    manifest_path = args.output_root / "NORMALIZATION_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "case_count": len(receipts),
                "pointer_change_count": sum(row["change_count"] for row in receipts),
                "manifest": str(manifest_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
