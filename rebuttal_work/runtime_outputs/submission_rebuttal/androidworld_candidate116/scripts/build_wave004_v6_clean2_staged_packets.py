#!/usr/bin/env python3
"""Build 116 full-canonical packets with bounded, source-addressed read plans."""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
GEN_ROOT = WORK_ROOT / "draft_generation"
PACKET_INDEX = WORK_ROOT / "indexes" / "androidworld_candidate116_packet_index.json"
INPUT_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
SUPERSESSION = GEN_ROOT / "incidents" / "wave_004_v6_clean_prelock_superseded.json"
OUTPUT_ROOT = GEN_ROOT / "packet_sets" / "wave_004_v6_clean2"
MANIFEST_PATH = OUTPUT_ROOT / "packet_set_manifest.json"
TIKTOKEN_ROOT = GEN_ROOT / "tokenizer" / "tiktoken_0_12_0_py312"
TIKTOKEN_CACHE_ROOT = TIKTOKEN_ROOT / "encoding_cache"
os.environ["TIKTOKEN_CACHE_DIR"] = str(TIKTOKEN_CACHE_ROOT)
sys.path.insert(0, str(TIKTOKEN_ROOT))
import tiktoken  # noqa: E402


TOKEN_ENCODING = "o200k_base"
ENCODING = tiktoken.get_encoding(TOKEN_ENCODING)
MAX_MANDATORY_READ_BYTES = 400_000
MAX_MANDATORY_READ_TOKENS = 150_000
MAX_RANGE_LINES = 180
CONTEXT_LINES = 3

COMMON_CALL_NAMES = {
    "add",
    "append",
    "bool",
    "dict",
    "enumerate",
    "float",
    "format",
    "get",
    "int",
    "isinstance",
    "len",
    "list",
    "log",
    "max",
    "min",
    "next",
    "open",
    "print",
    "range",
    "replace",
    "set",
    "sorted",
    "str",
    "sum",
    "super",
    "tuple",
    "type",
    "zip",
}


@dataclass(frozen=True)
class Section:
    path: str
    content_start_index: int
    content_end_index: int
    content_lines: tuple[str, ...]


@dataclass(frozen=True)
class Definition:
    path: str
    name: str
    start_line: int
    end_line: int
    node: ast.AST


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def legacy_ascii_canonical_sha256(value: Any) -> str:
    """Match freeze_and_slots.payload_sha256 used by the semantic-record builder."""
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise RuntimeError(f"regular non-symlink file required: {path}")
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def tree_binding(root: Path) -> dict[str, Any]:
    resolved = root.resolve(strict=True)
    if root.is_symlink() or not resolved.is_dir():
        raise RuntimeError(f"regular tokenizer directory required: {root}")
    files = [
        {
            "path": path.relative_to(resolved).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(candidate for candidate in resolved.rglob("*") if candidate.is_file())
    ]
    if any(path.is_symlink() for path in resolved.rglob("*")):
        raise RuntimeError("tokenizer tree contains a symlink")
    return {
        "path": str(resolved),
        "file_count": len(files),
        "files": files,
        "files_sha256": canonical_sha256(files),
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def verify_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if claimed != legacy_ascii_canonical_sha256(core):
        raise RuntimeError(f"{label} self-hash mismatch")


def write_create_once(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def write_json_create_once(path: Path, value: Any) -> None:
    write_create_once(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def parse_sections(lines: list[str]) -> dict[str, Section]:
    sections: dict[str, Section] = {}
    index = 0
    while index < len(lines):
        match = re.fullmatch(r"### `([^`]+)`\n?", lines[index])
        if not match:
            index += 1
            continue
        path = match.group(1)
        fence = index + 1
        while fence < len(lines) and not lines[fence].startswith("```"):
            fence += 1
        if fence >= len(lines):
            raise RuntimeError(f"missing opening fence for packet section {path}")
        end = fence + 1
        while end < len(lines) and lines[end].rstrip("\r\n") != "```":
            end += 1
        if end >= len(lines):
            raise RuntimeError(f"missing closing fence for packet section {path}")
        if path in sections:
            raise RuntimeError(f"duplicate packet section: {path}")
        sections[path] = Section(
            path=path,
            content_start_index=fence + 1,
            content_end_index=end,
            content_lines=tuple(lines[fence + 1 : end]),
        )
        index = end + 1
    return sections


def normalize_source_path(raw: str, section_paths: set[str]) -> str | None:
    value = raw.replace("\\", "/")
    marker = "shared_source/source_tree/"
    if marker in value:
        value = value.split(marker, 1)[1]
    candidates = [value]
    if value.startswith("android_world/"):
        candidates.insert(0, f"official/install/{value}")
    if value.startswith("official/install/"):
        candidates.insert(0, value)
    for candidate in candidates:
        if candidate in section_paths:
            return candidate
    suffix_matches = sorted(
        path
        for path in section_paths
        if path.endswith("/" + value) or path.endswith(value)
    )
    preferred = [path for path in suffix_matches if "/.venv" not in path]
    if preferred:
        return preferred[0]
    return suffix_matches[0] if suffix_matches else None


def collect_semantic_ranges(
    semantics: dict[str, Any], section_paths: set[str]
) -> tuple[list[dict[str, Any]], dict[str, set[str]], set[str]]:
    ranges: list[dict[str, Any]] = []
    calls_by_dimension: dict[str, set[str]] = defaultdict(set)
    dimensions_seen: set[str] = set()

    def walk(value: Any, path: tuple[str, ...]) -> None:
        dimension = path[0] if path else "identity"
        if isinstance(value, dict):
            direct_calls = value.get("direct_calls")
            if isinstance(direct_calls, list):
                calls_by_dimension[dimension].update(
                    str(item) for item in direct_calls if isinstance(item, str)
                )
            start = value.get("start_line")
            end = value.get("end_line")
            raw_path = value.get("path") or value.get("artifact_path")
            if isinstance(start, int) and isinstance(end, int) and isinstance(raw_path, str):
                packet_path = normalize_source_path(raw_path, section_paths)
                if packet_path is not None:
                    ranges.append(
                        {
                            "path": packet_path,
                            "start": start,
                            "end": end,
                            "dimensions": {dimension},
                            "symbols": {
                                str(value.get("symbol") or value.get("owner_qualname") or "")
                            }
                            - {""},
                        }
                    )
                    dimensions_seen.add(dimension)
            for key, child in value.items():
                walk(child, path + (str(key),))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + (str(index),))

    walk(semantics, ())
    raw_metadata = semantics.get("raw_metadata") or {}
    source_ref = raw_metadata.get("source_ref") if isinstance(raw_metadata, dict) else None
    if isinstance(source_ref, dict):
        raw_path = source_ref.get("path")
        line_hint = source_ref.get("line_hint")
        if isinstance(raw_path, str) and isinstance(line_hint, int):
            packet_path = normalize_source_path(raw_path, section_paths)
            if packet_path:
                ranges.append(
                    {
                        "path": packet_path,
                        "start": max(1, line_hint - 8),
                        "end": line_hint + 18,
                        "dimensions": {"raw_metadata", "metadata_comparison"},
                        "symbols": {semantics["case_unit_id"]},
                    }
                )
                dimensions_seen.update(("raw_metadata", "metadata_comparison"))
    return ranges, calls_by_dimension, dimensions_seen


def build_definition_index(
    sections: dict[str, Section],
) -> tuple[dict[str, list[Definition]], list[Definition]]:
    by_name: dict[str, list[Definition]] = defaultdict(list)
    definitions: list[Definition] = []
    for path, section in sections.items():
        if not path.endswith(".py"):
            continue
        source = "".join(section.content_lines)
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            end = getattr(node, "end_lineno", None)
            if not isinstance(end, int):
                continue
            definition = Definition(
                path=path,
                name=node.name,
                start_line=node.lineno,
                end_line=end,
                node=node,
            )
            definitions.append(definition)
            by_name[node.name].append(definition)
    return by_name, definitions


def call_leaf(call: ast.Call) -> tuple[str | None, str | None]:
    function = call.func
    if isinstance(function, ast.Name):
        return None, function.id
    if isinstance(function, ast.Attribute):
        module = function.value.id if isinstance(function.value, ast.Name) else None
        return module, function.attr
    return None, None


def helper_expansion(
    ranges: list[dict[str, Any]],
    calls_by_dimension: dict[str, set[str]],
    by_name: dict[str, list[Definition]],
    definitions: list[Definition],
) -> list[dict[str, Any]]:
    pending: list[tuple[str, str, str | None]] = []
    for dimension, calls in calls_by_dimension.items():
        for call in calls:
            parts = call.split(".")
            pending.append((dimension, parts[-1], parts[-2] if len(parts) > 1 else None))
    seen_defs: set[tuple[str, int, int]] = set()
    for _round in range(4):
        additions: list[dict[str, Any]] = []
        next_pending: list[tuple[str, str, str | None]] = []
        for dimension, name, module_hint in pending:
            if name in COMMON_CALL_NAMES or name not in by_name:
                continue
            candidates = by_name[name]
            if module_hint and module_hint not in {"self", "cls"}:
                narrowed = [
                    item for item in candidates if Path(item.path).stem == module_hint
                ]
                if narrowed:
                    candidates = narrowed
            for item in candidates:
                key = (item.path, item.start_line, item.end_line)
                if key in seen_defs:
                    continue
                seen_defs.add(key)
                additions.append(
                    {
                        "path": item.path,
                        "start": item.start_line,
                        "end": item.end_line,
                        "dimensions": {dimension, "helper_chain"},
                        "symbols": {item.name},
                    }
                )
                for child in ast.walk(item.node):
                    if isinstance(child, ast.Call):
                        child_module, child_name = call_leaf(child)
                        if child_name:
                            next_pending.append((dimension, child_name, child_module))
        ranges.extend(additions)
        pending = next_pending
        if not pending:
            break
    # Ensure every initial range can contribute calls from intersecting definitions.
    selected = [
        item
        for item in definitions
        if any(
            row["path"] == item.path
            and row["start"] <= item.end_line
            and row["end"] >= item.start_line
            for row in ranges
        )
    ]
    for item in selected:
        for child in ast.walk(item.node):
            if not isinstance(child, ast.Call):
                continue
            module_hint, name = call_leaf(child)
            if not name or name in COMMON_CALL_NAMES:
                continue
            for target in by_name.get(name, []):
                if module_hint and module_hint not in {"self", "cls"}:
                    if Path(target.path).stem != module_hint:
                        continue
                key = (target.path, target.start_line, target.end_line)
                if key in seen_defs:
                    continue
                seen_defs.add(key)
                ranges.append(
                    {
                        "path": target.path,
                        "start": target.start_line,
                        "end": target.end_line,
                        "dimensions": {"helper_chain"},
                        "symbols": {target.name},
                    }
                )
    return ranges


def add_registry_range(
    ranges: list[dict[str, Any]], sections: dict[str, Section], case_id: str
) -> None:
    path = "official/install/android_world/registry.py"
    section = sections.get(path)
    if section is None:
        raise RuntimeError("canonical packet lacks registry.py")
    matches = [
        index + 1
        for index, line in enumerate(section.content_lines)
        if case_id in line
    ]
    if not matches:
        ranges.append(
            {
                "path": path,
                "start": 1,
                "end": len(section.content_lines),
                "dimensions": {"definition", "runtime_dispatch"},
                "symbols": {"registry", case_id},
            }
        )
        return
    for line in matches:
        ranges.append(
            {
                "path": path,
                "start": max(1, line - 8),
                "end": min(len(section.content_lines), line + 8),
                "dimensions": {"definition", "runtime_dispatch"},
                "symbols": {case_id},
            }
        )


def merge_and_split_ranges(
    rows: list[dict[str, Any]], sections: dict[str, Section]
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        section = sections.get(row["path"])
        if section is None:
            raise RuntimeError(f"planned source is absent from packet: {row['path']}")
        start = max(1, int(row["start"]) - CONTEXT_LINES)
        end = min(len(section.content_lines), int(row["end"]) + CONTEXT_LINES)
        if end < start:
            raise RuntimeError(
                f"invalid planned source range {row['path']}:{row['start']}-{row['end']} "
                f"for {len(section.content_lines)} source lines"
            )
        grouped[row["path"]].append(
            {
                "start": start,
                "end": end,
                "dimensions": set(row["dimensions"]),
                "symbols": set(row["symbols"]),
            }
        )
    merged: list[dict[str, Any]] = []
    for path, values in sorted(grouped.items()):
        values.sort(key=lambda item: (item["start"], item["end"]))
        current = values[0]
        for value in values[1:]:
            if value["start"] <= current["end"] + 5:
                current["end"] = max(current["end"], value["end"])
                current["dimensions"].update(value["dimensions"])
                current["symbols"].update(value["symbols"])
            else:
                merged.append({"path": path, **current})
                current = value
        merged.append({"path": path, **current})
    split: list[dict[str, Any]] = []
    for row in merged:
        start = row["start"]
        while start <= row["end"]:
            end = min(row["end"], start + MAX_RANGE_LINES - 1)
            split.append(
                {
                    "path": row["path"],
                    "start": start,
                    "end": end,
                    "dimensions": sorted(row["dimensions"]),
                    "symbols": sorted(row["symbols"]),
                }
            )
            start = end + 1
    return split


def chunks(start: int, end: int, size: int) -> Iterable[tuple[int, int]]:
    current = start
    while current <= end:
        chunk_end = min(end, current + size - 1)
        yield current, chunk_end
        current = chunk_end + 1


def range_payload(
    *,
    range_id: str,
    kind: str,
    lines: list[str],
    start_index: int,
    end_index: int,
    packet_start: int,
    source_path: str | None,
    source_start: int | None,
    source_end: int | None,
    dimensions: list[str],
    symbols: list[str],
) -> dict[str, Any]:
    selected = "".join(lines[start_index : end_index + 1]).encode("utf-8")
    selected_text = selected.decode("utf-8")
    packet_line_start = packet_start + start_index
    packet_line_end = packet_start + end_index
    return {
        "range_id": range_id,
        "kind": kind,
        "packet_line_start": packet_line_start,
        "packet_line_end": packet_line_end,
        "command": f"sed -n '{packet_line_start},{packet_line_end}p' case_packet.md",
        "source_inventory_path": source_path,
        "source_line_start": source_start,
        "source_line_end": source_end,
        "semantic_dimensions": dimensions,
        "symbols": symbols,
        "utf8_bytes": len(selected),
        "o200k_base_tokens": len(ENCODING.encode(selected_text)),
        "sha256": sha256_bytes(selected),
    }


def build_one(item: dict[str, Any]) -> tuple[dict[str, Any], str]:
    case_id = str(item["case_unit_id"])
    canonical = REPO_ROOT / str(item["case_packet_path"])
    compact = REPO_ROOT / str(item["compact_case_packet_path"])
    semantic = REPO_ROOT / str(item["semantic_record_path"])
    if any(path.is_symlink() or not path.is_file() for path in (canonical, compact, semantic)):
        raise RuntimeError(f"missing/symlinked canonical input for {case_id}")
    if sha256_file(canonical) != item["case_packet_sha256"]:
        raise RuntimeError(f"full packet hash mismatch for {case_id}")
    if sha256_file(compact) != item["compact_case_packet_sha256"]:
        raise RuntimeError(f"compact packet hash mismatch for {case_id}")
    semantics = load_json(semantic)
    verify_self_hash(semantics, "record_sha256", f"semantic record {case_id}")
    if semantics["record_sha256"] != item["semantic_record_sha256"]:
        raise RuntimeError(f"semantic record logical hash mismatch for {case_id}")

    canonical_text = canonical.read_text(encoding="utf-8")
    compact_text = compact.read_text(encoding="utf-8")
    canonical_lines = canonical_text.splitlines(keepends=True)
    compact_lines = compact_text.splitlines(keepends=True)
    sections = parse_sections(canonical_lines)
    if semantics.get("case_unit_id") != case_id or semantics.get("task_id") != case_id:
        raise RuntimeError(f"semantic identity mismatch for {case_id}")
    section_paths = set(sections)
    rows, calls, dimensions_seen = collect_semantic_ranges(semantics, section_paths)
    by_name, definitions = build_definition_index(sections)
    helper_expansion(rows, calls, by_name, definitions)
    add_registry_range(rows, sections, case_id)
    source_ranges = merge_and_split_ranges(rows, sections)

    required_dimensions = {
        "definition",
        "evaluator",
        "goal",
        "initialize_task",
        "is_successful",
        "metadata_comparison",
        "raw_metadata",
        "schema",
    }
    covered_dimensions = set(dimensions_seen)
    for row in source_ranges:
        covered_dimensions.update(row["dimensions"])
    missing_dimensions = sorted(required_dimensions - covered_dimensions)
    if missing_dimensions:
        raise RuntimeError(f"semantic dimensions missing for {case_id}: {missing_dimensions}")

    header_lines = [
        "# AndroidWorld staged full-canonical draft packet\n",
        "\n",
        "This file contains a bounded mandatory reading plan, the frozen compact semantic index,\n",
        "and the complete canonical packet verbatim. The complete canonical packet remains the\n",
        "sole source authority. The compact index is navigation only and is never a support target.\n",
        "Read every mandatory range using its exact command. Do not cat or read this entire file.\n",
        "Resolve every direct/delegated helper named by a mandatory range before drafting.\n",
        "\n",
        "## Machine-readable mandatory reading plan\n",
        "\n",
        "```json\n",
    ]
    compact_prefix = ["```\n", "\n", "## Frozen compact semantic navigation index\n", "\n"]
    compact_suffix = ["\n", "## Complete canonical packet (verbatim; sole source authority)\n", "\n"]

    # First render establishes a fixed line count; replacing numeric values does not
    # change the pretty-printed JSON line count.
    placeholder_plan = {
        "schema_version": "androidworld_staged_read_plan/v1",
        "case_unit_id": case_id,
        "task_id": case_id,
        "required_semantic_dimensions": sorted(required_dimensions),
        "direct_helper_resolution_required": True,
        "whole_file_read_forbidden": True,
        "mandatory_ranges": [],
    }
    placeholder_json = json.dumps(placeholder_plan, ensure_ascii=False, indent=2, sort_keys=True)
    plan_line_count = len(placeholder_json.splitlines())

    # Range count affects plan line count. Iterate until the wrapper offsets stabilize.
    final_plan: dict[str, Any] | None = None
    final_ranges: list[dict[str, Any]] = []
    previous_line_count = -1
    for _ in range(5):
        plan_json_lines = plan_line_count
        compact_start = len(header_lines) + plan_json_lines + len(compact_prefix) + 1
        canonical_start = compact_start + len(compact_lines) + len(compact_suffix)
        ranges_payload: list[dict[str, Any]] = []
        counter = 1
        for start, end in chunks(0, len(compact_lines) - 1, MAX_RANGE_LINES):
            ranges_payload.append(
                range_payload(
                    range_id=f"R{counter:03d}",
                    kind="compact_semantic_navigation",
                    lines=compact_lines,
                    start_index=start,
                    end_index=end,
                    packet_start=compact_start,
                    source_path=None,
                    source_start=None,
                    source_end=None,
                    dimensions=sorted(required_dimensions | {"metadata_conflicts", "runner"}),
                    symbols=[case_id],
                )
            )
            counter += 1
        for row in source_ranges:
            section = sections[row["path"]]
            start_index = section.content_start_index + row["start"] - 1
            end_index = section.content_start_index + row["end"] - 1
            ranges_payload.append(
                range_payload(
                    range_id=f"R{counter:03d}",
                    kind="canonical_source",
                    lines=canonical_lines,
                    start_index=start_index,
                    end_index=end_index,
                    packet_start=canonical_start,
                    source_path=row["path"],
                    source_start=row["start"],
                    source_end=row["end"],
                    dimensions=row["dimensions"],
                    symbols=row["symbols"],
                )
            )
            counter += 1
        plan = {
            "schema_version": "androidworld_staged_read_plan/v1",
            "case_unit_id": case_id,
            "task_id": case_id,
            "canonical_packet_sha256": sha256_file(canonical),
            "compact_semantic_index_sha256": sha256_file(compact),
            "semantic_record_sha256": sha256_file(semantic),
            "required_semantic_dimensions": sorted(required_dimensions),
            "covered_semantic_dimensions": sorted(covered_dimensions),
            "direct_helper_resolution_required": True,
            "dynamic_helper_rule": (
                "For every direct call named in the compact index or selected source, "
                "use rg -n on case_packet.md and read its definition unless already in "
                "a mandatory canonical_source range."
            ),
            "whole_file_read_forbidden": True,
            "forbidden_commands": [
                "cat case_packet.md",
                "sed -n '1,$p' case_packet.md",
                "read_text() over the complete case_packet.md",
            ],
            "mandatory_range_count": len(ranges_payload),
            "mandatory_ranges": ranges_payload,
            "mandatory_read_utf8_bytes": sum(row["utf8_bytes"] for row in ranges_payload),
            "mandatory_read_o200k_base_tokens": sum(
                row["o200k_base_tokens"] for row in ranges_payload
            ),
            "token_capacity_proof": {
                "method": "exact tiktoken 0.12.0 range-by-range count",
                "token_encoding": TOKEN_ENCODING,
                "mandatory_read_exact_token_count": sum(
                    row["o200k_base_tokens"] for row in ranges_payload
                ),
                "mandatory_read_token_limit": MAX_MANDATORY_READ_TOKENS,
                "dynamic_helper_output_reserve_tokens": 30_000,
                "prompt_template_output_reserve_tokens": 70_000,
                "effective_context_budget_tokens": 258_400,
            },
        }
        plan["plan_sha256"] = canonical_sha256(plan)
        rendered = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True)
        line_count = len(rendered.splitlines())
        final_plan = plan
        final_ranges = ranges_payload
        if line_count == previous_line_count:
            break
        previous_line_count = line_count
        plan_line_count = line_count
    else:
        raise RuntimeError(f"reading-plan line offsets did not stabilize for {case_id}")
    if final_plan is None:
        raise RuntimeError("unreachable missing final plan")
    mandatory_bytes = int(final_plan["mandatory_read_utf8_bytes"])
    if mandatory_bytes > MAX_MANDATORY_READ_BYTES:
        breakdown: dict[str, int] = defaultdict(int)
        for row in final_ranges:
            breakdown[str(row.get("source_inventory_path") or row["kind"])] += int(
                row["utf8_bytes"]
            )
        raise RuntimeError(
            f"mandatory read budget exceeded for {case_id}: {mandatory_bytes}; "
            f"breakdown={dict(sorted(breakdown.items(), key=lambda item: -item[1]))}"
        )
    mandatory_tokens = int(final_plan["mandatory_read_o200k_base_tokens"])
    if mandatory_tokens > MAX_MANDATORY_READ_TOKENS:
        raise RuntimeError(
            f"mandatory token budget exceeded for {case_id}: {mandatory_tokens}"
        )
    capacity = final_plan["token_capacity_proof"]
    total_upper = (
        capacity["mandatory_read_exact_token_count"]
        + capacity["dynamic_helper_output_reserve_tokens"]
        + capacity["prompt_template_output_reserve_tokens"]
    )
    if total_upper >= capacity["effective_context_budget_tokens"]:
        raise RuntimeError(f"staged context upper bound is unsafe for {case_id}: {total_upper}")

    plan_json = json.dumps(final_plan, ensure_ascii=False, indent=2, sort_keys=True)
    wrapper_text = "".join(header_lines) + plan_json + "\n" + "".join(compact_prefix)
    wrapper_text += compact_text.rstrip("\n") + "\n" + "".join(compact_suffix)
    canonical_offset = len(wrapper_text)
    wrapper_text += canonical_text
    if wrapper_text[canonical_offset:] != canonical_text:
        raise RuntimeError(f"canonical packet is not verbatim in staged wrapper: {case_id}")

    wrapper_lines = wrapper_text.splitlines(keepends=True)
    for row in final_ranges:
        selected = "".join(
            wrapper_lines[row["packet_line_start"] - 1 : row["packet_line_end"]]
        ).encode("utf-8")
        if len(selected) != row["utf8_bytes"] or sha256_bytes(selected) != row["sha256"]:
            raise RuntimeError(f"final staged range binding mismatch: {case_id}/{row['range_id']}")
    descriptor = {
        "schema_version": "androidworld_staged_full_packet_descriptor/v1",
        "generation_id": "wave_004_v6_clean2",
        "case_unit_id": case_id,
        "task_id": case_id,
        "selection_rank": item["selection_rank"],
        "group": item["group"],
        "canonical_packet": binding(canonical),
        "compact_semantic_index": binding(compact),
        "semantic_record": binding(semantic),
        "plan_sha256": final_plan["plan_sha256"],
        "mandatory_range_count": len(final_ranges),
        "mandatory_read_utf8_bytes": mandatory_bytes,
        "mandatory_read_o200k_base_tokens": mandatory_tokens,
        "staged_context_token_upper_bound": total_upper,
        "full_canonical_packet_utf8_bytes": len(canonical_text.encode("utf-8")),
        "full_canonical_packet_o200k_base_tokens": len(ENCODING.encode(canonical_text)),
        "canonical_packet_embedded_verbatim_once": wrapper_text.count(canonical_text) == 1,
        "old_draft_content_or_issue_warnings_visible": False,
    }
    descriptor["descriptor_sha256"] = canonical_sha256(descriptor)
    return descriptor, wrapper_text


def main() -> int:
    if OUTPUT_ROOT.exists() or OUTPUT_ROOT.is_symlink():
        raise RuntimeError(f"staged packet output already exists: {OUTPUT_ROOT}")
    index = load_json(PACKET_INDEX)
    freeze = load_json(INPUT_FREEZE)
    supersession = load_json(SUPERSESSION)
    verify_self_hash(freeze, "freeze_sha256", "candidate116 input freeze")
    verify_self_hash(supersession, "incident_sha256", "v6-clean supersession")
    items = list(index.get("items") or [])
    if index.get("candidate_count") != 116 or len(items) != 116:
        raise RuntimeError("packet index is not exactly candidate116")
    order = [str(item.get("case_unit_id")) for item in items]
    if order != freeze.get("case_order", {}).get("case_unit_ids") or len(set(order)) != 116:
        raise RuntimeError("packet index order differs from frozen candidate116 order")
    built = [(item, *build_one(item)) for item in items]
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=False)
    cases: list[dict[str, Any]] = []
    for item, descriptor, wrapper_text in built:
        case_dir = OUTPUT_ROOT / descriptor["case_unit_id"]
        case_dir.mkdir()
        packet_path = case_dir / "case_packet.md"
        descriptor_path = case_dir / "packet_descriptor.json"
        write_create_once(packet_path, wrapper_text)
        descriptor["staged_packet"] = binding(packet_path)
        core = dict(descriptor)
        core.pop("descriptor_sha256", None)
        descriptor["descriptor_sha256"] = canonical_sha256(core)
        write_json_create_once(descriptor_path, descriptor)
        cases.append(
            {
                "case_unit_id": descriptor["case_unit_id"],
                "task_id": descriptor["task_id"],
                "selection_rank": descriptor["selection_rank"],
                "group": descriptor["group"],
                "packet": binding(packet_path),
                "descriptor": binding(descriptor_path)
                | {"descriptor_sha256": descriptor["descriptor_sha256"]},
                "canonical_packet": descriptor["canonical_packet"],
                "compact_semantic_index": descriptor["compact_semantic_index"],
                "semantic_record": descriptor["semantic_record"],
                "plan_sha256": descriptor["plan_sha256"],
                "mandatory_range_count": descriptor["mandatory_range_count"],
                "mandatory_read_utf8_bytes": descriptor["mandatory_read_utf8_bytes"],
                "mandatory_read_o200k_base_tokens": descriptor[
                    "mandatory_read_o200k_base_tokens"
                ],
                "staged_context_token_upper_bound": descriptor[
                    "staged_context_token_upper_bound"
                ],
            }
        )
    manifest = {
        "schema_version": "androidworld_candidate116_staged_packet_set/v1",
        "status": "prelock_candidate",
        "generation_id": "wave_004_v6_clean2",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "case_count": len(cases),
        "case_order": order,
        "case_order_sha256": canonical_sha256(order),
        "cases": cases,
        "cases_sha256": canonical_sha256(cases),
        "max_mandatory_read_utf8_bytes": max(
            row["mandatory_read_utf8_bytes"] for row in cases
        ),
        "max_staged_context_token_upper_bound": max(
            row["staged_context_token_upper_bound"] for row in cases
        ),
        "max_mandatory_read_o200k_base_tokens": max(
            row["mandatory_read_o200k_base_tokens"] for row in cases
        ),
        "max_full_canonical_packet_o200k_base_tokens": max(
            load_json(Path(row["descriptor"]["path"]))[
                "full_canonical_packet_o200k_base_tokens"
            ]
            for row in cases
        ),
        "full_canonical_packet_embedded_verbatim_for_all": True,
        "old_draft_content_or_issue_warnings_visible": False,
        "tokenizer": tree_binding(TIKTOKEN_ROOT)
        | {"package_version": tiktoken.__version__, "encoding": TOKEN_ENCODING},
        "packet_index": binding(PACKET_INDEX),
        "canonical_input_freeze": binding(INPUT_FREEZE)
        | {"freeze_sha256": freeze["freeze_sha256"]},
        "superseded_v6_clean": binding(SUPERSESSION)
        | {"incident_sha256": supersession["incident_sha256"]},
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    write_json_create_once(MANIFEST_PATH, manifest)
    print(
        json.dumps(
            {
                "status": "built",
                "case_count": len(cases),
                "max_mandatory_read_utf8_bytes": manifest[
                    "max_mandatory_read_utf8_bytes"
                ],
                "max_staged_context_token_upper_bound": manifest[
                    "max_staged_context_token_upper_bound"
                ],
                "max_mandatory_read_o200k_base_tokens": manifest[
                    "max_mandatory_read_o200k_base_tokens"
                ],
                "max_full_canonical_packet_o200k_base_tokens": manifest[
                    "max_full_canonical_packet_o200k_base_tokens"
                ],
                "manifest_sha256": manifest["manifest_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
