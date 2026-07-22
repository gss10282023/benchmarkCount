#!/usr/bin/env python3
"""Independent, fail-closed deterministic QC for one fresh candidate116 draft wave.

This validator intentionally does not import or consume any conclusion produced by
an earlier draft wave.  Its authorities are limited to caller-bound fresh raw
outputs, canonical packets, frozen source-coverage requirements, the adapted
checklist schema, a frozen toolchain, and a create-once expectations document.

The production CLI is fixed at exactly 116 cases.  ``run_audit`` exposes a smaller
count only so the accompanying hermetic unit tests can exercise every gate without
manufacturing 116 copies; the CLI never exposes that override.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

try:
    import yaml  # type: ignore[import-not-found]
    from jsonschema import Draft202012Validator  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover - exercised by the production launcher
    print(
        "ERROR: strict fresh-draft QC requires the frozen PyYAML and jsonschema runtime: "
        f"{exc}",
        file=sys.stderr,
    )
    raise SystemExit(2)


PRODUCTION_CASE_COUNT = 116
EXPECTATIONS_SCHEMA = "androidworld_candidate116_fresh_draft_qc_expectations/v2"
REPORT_SCHEMA = "androidworld_candidate116_fresh_draft_deterministic_qc/v1"
CHECKLIST_SCHEMA_VERSION = "case_checklist_v1"
PRODUCTION_NAMESPACE = "wave_004_v6_clean5_hardened"
READER_OPERATION_EXPECTATIONS_SCHEMA = (
    "androidworld_candidate116_reader_operation_expectations/v1"
)
COVERAGE_RECEIPT_SCHEMA = (
    "androidworld_candidate116_staged_source_coverage_receipt/v2"
)
READER_BODY_PREFIX = "WAVE004_READER_BODY "
READER_COMPLETION_PREFIX = "WAVE004_READER_COMPLETE "
MAX_READER_ENVELOPE_BYTES = 24_000
MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES = 10_000
MAX_COVERAGE_CHUNK_BYTES = 10_000
MAX_COVERAGE_PLAN_ROW_BYTES = 4_096
MAX_READER_ENVELOPE_TOKENS = 7_500
MAX_COVERAGE_PLAN_PAGE_TOKENS = 4_000
MAX_CODEX_TOTAL_TOKENS = 258_400
CODEX_EVENT_HOST_SHELL = "/bin/zsh"
CODEX_EVENT_HOST_SHELL_FLAG = "-lc"
SAFE_READER_INNER_COMMAND_RE = re.compile(r"^[A-Za-z0-9_./:= -]+$")
REQUIRED_CONTROL_BINDINGS = ("codex_cli", "config", "prompt", "schema", "template")
REQUIRED_NATIVE_FIELDS = (
    "user_goal",
    "benchmark_success",
    "checked_by",
    "decisive_artifacts",
    "success_if",
    "fail_if",
    "undecided_if",
)
REQUIRED_COVERAGE_ANCHORS = (
    "metadata_task_description",
    "definition",
    "goal",
    "schema",
    "initialize_task",
    "is_successful",
    "evaluator",
)
FORBIDDEN_SUPPORT_EXACT = frozenset(
    {
        "case_packet.md",
        "compact_case_packet.md",
        "model_input_coverage.json",
        "workspace_materialization.json",
        "draft_instructions.md",
        "output_schema.json",
        "template.yaml",
        "draft_body.json",
    }
)
FORBIDDEN_SUPPORT_SEGMENTS = frozenset(
    {"packet_sources", "workspace", "coverage", "draft_generation"}
)
SOURCE_INVENTORY_RE = re.compile(r"^- `([^`\r\n]+)`$")
PACKET_SECTION_RE = re.compile(
    r"^### `(?P<path>[^`\r\n]+)`\n\n"
    r"Source ref: (?P<source_ref>[^\r\n]+)\n\n"
    r"```(?P<language>[A-Za-z0-9_.+-]+)\n"
    r"(?P<body>.*?)^```\n",
    re.MULTILINE | re.DOTALL,
)
SAFE_CASE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
SAFE_SOURCE_PATH_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
LINE_SPAN_RES = (
    re.compile(r"^L(?P<start>[1-9][0-9]*)(?:-L?(?P<end>[1-9][0-9]*))?$"),
    re.compile(r"^lines?:(?P<start>[1-9][0-9]*)(?:-(?P<end>[1-9][0-9]*))?$"),
)
JSON_PATH_TOKEN_RE = re.compile(
    r"(?:\.(?P<name>[A-Za-z_][A-Za-z0-9_-]*))|(?:\[(?P<index>0|[1-9][0-9]*)\])"
)
URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
SEMANTIC_TEXT_RE = re.compile(r"[A-Za-z0-9_\u0080-\uffff]")


class QCFailure(RuntimeError):
    """One fail-closed acceptance failure."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def exact_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's ``False == 0`` coercion."""

    return canonical_bytes(left) == canonical_bytes(right)


def is_exact_int(value: Any) -> bool:
    """JSON integers are accepted, but booleans never stand in for 0/1."""

    return type(value) is int


LAYER_A_INTEGER_FIELDS = frozenset(
    {
        "bound_end_line",
        "bound_start_line",
        "chunk_count",
        "chunk_index",
        "chunk_size_bytes",
        "coverage_page_count",
        "end_line",
        "end_range_index_exclusive",
        "line_count",
        "logical_alias_count",
        "max_coverage_chunk_bytes",
        "max_plan_page_o200k_tokens",
        "max_plan_page_output_bytes",
        "max_plan_row_serialized_bytes",
        "max_reader_envelope_bytes",
        "max_reader_envelope_o200k_tokens",
        "max_row_serialized_bytes",
        "packet_local_unresolved_count",
        "page_index",
        "plan_distinct_content_count",
        "plan_member_count",
        "planned_output_o200k_tokens",
        "planned_output_size_bytes",
        "planned_reader_envelope_max_bytes",
        "planned_reader_envelope_max_o200k_tokens",
        "raw_official_distinct_sha_count",
        "raw_official_inventory_member_count",
        "raw_official_omitted_count",
        "raw_official_source_closure_count",
        "recursive_source_ref_mapping_missing_count",
        "required_range_count",
        "row_count",
        "selected_definition_count",
        "size_bytes",
        "source_binding_mapping_missing_count",
        "start_line",
        "start_range_index",
        "to_end_line",
        "to_start_line",
        "unresolved_internal_import_count",
    }
)
LAYER_A_BOOLEAN_FIELDS = frozenset(
    {
        "byte_identical_aliases_share_one_physical_read_only_when_hash_bound",
        "canonical_runtime_resolution_applied",
        "canonical_source_complete",
        "case_packet_one_shot_read_forbidden",
        "chunks_must_be_read_separately_in_listed_order",
        "every_distinct_raw_official_inventory_payload_must_be_read_completely",
        "fixed_point_reached",
        "goal_samples_reproducible",
        "live_run_ready",
        "live_runtime_verified",
        "metadata_has_open_material_conflict",
        "metadata_has_open_unresolved_conflict",
        "metadata_is_excluded_from_canonical_goal_when_conflicting",
        "raw_inventory_members_may_never_be_excluded_by_navigation_or_ast",
        "semantic_direct",
        "snippet_ends_with_newline",
        "static_draft_ready",
        "static_semantic_record_complete",
    }
)
LAYER_A_OPTIONAL_INTEGER_FIELDS = frozenset(
    {"bound_end_line", "bound_start_line"}
)


def validate_layer_a_scalar_types(value: Any, path: str = "layer-A") -> None:
    """Reject bool/int coercion and undeclared numeric fields recursively."""

    if isinstance(value, Mapping):
        for key, child in value.items():
            require(isinstance(key, str), f"{path} contains a non-string key")
            child_path = f"{path}.{key}"
            if key in LAYER_A_INTEGER_FIELDS:
                require(
                    is_exact_int(child)
                    or (child is None and key in LAYER_A_OPTIONAL_INTEGER_FIELDS),
                    f"{child_path} is not an exact JSON integer",
                )
            if key in LAYER_A_BOOLEAN_FIELDS:
                require(type(child) is bool, f"{child_path} is not an exact JSON boolean")
            require(
                type(child) is not int or key in LAYER_A_INTEGER_FIELDS,
                f"{child_path} is an unrecognized JSON integer",
            )
            require(
                type(child) is not bool or key in LAYER_A_BOOLEAN_FIELDS,
                f"{child_path} is an unrecognized JSON boolean",
            )
            validate_layer_a_scalar_types(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            require(
                type(child) not in (int, bool),
                f"{path}[{index}] is an untyped scalar",
            )
            validate_layer_a_scalar_types(child, f"{path}[{index}]")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise QCFailure(message)


def require_regular(path: Path, label: str) -> Path:
    require(path.exists(), f"{label} is missing: {path}")
    require(not path.is_symlink(), f"{label} is symlinked: {path}")
    metadata = path.lstat()
    require(stat.S_ISREG(metadata.st_mode), f"{label} is not a regular file: {path}")
    return path


def require_directory(path: Path, label: str) -> Path:
    require(path.exists(), f"{label} is missing: {path}")
    require(not path.is_symlink(), f"{label} is symlinked: {path}")
    require(path.is_dir(), f"{label} is not a directory: {path}")
    return path


def load_json(path: Path, label: str) -> dict[str, Any]:
    require_regular(path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QCFailure(f"cannot parse {label} as UTF-8 JSON: {exc}") from exc
    require(isinstance(value, dict), f"{label} is not a JSON object")
    return value


def verify_self_hash(value: Mapping[str, Any], field_name: str, label: str) -> None:
    claimed = value.get(field_name)
    core = dict(value)
    core.pop(field_name, None)
    require(
        isinstance(claimed, str) and claimed == canonical_sha256(core),
        f"{label} self-hash mismatch in {field_name}",
    )


def _all_scalars(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _all_scalars(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_scalars(child)
    else:
        yield value


def _has_scalar(value: Any, expected: Any) -> bool:
    return any(child == expected for child in _all_scalars(value))


def tree_binding(root: Path) -> dict[str, Any]:
    require_directory(root, "frozen toolchain root")
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        require(not path.is_symlink(), f"symlink in frozen toolchain: {relative}")
        if path.is_file():
            rows.append(
                {
                    "relative_path": relative,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return {
        "file_count": len(rows),
        "files_sha256": canonical_sha256(rows),
        "files": rows,
    }


def validate_bound_file(
    root: Path, binding: Mapping[str, Any], label: str, *, allow_absolute: bool = False
) -> Path:
    raw_path = binding.get("relative_path")
    if allow_absolute and isinstance(binding.get("path"), str):
        path = Path(str(binding["path"]))
        require(path.is_absolute(), f"{label} absolute binding is not absolute")
    else:
        require(isinstance(raw_path, str) and raw_path, f"{label} has no relative_path")
        pure = PurePosixPath(str(raw_path))
        require(
            not pure.is_absolute() and all(part not in {"", ".", ".."} for part in pure.parts),
            f"{label} relative path is unsafe: {raw_path!r}",
        )
        path = root / pure
        try:
            path.resolve(strict=True).relative_to(root.resolve(strict=True))
        except ValueError as exc:
            raise QCFailure(f"{label} escapes frozen toolchain root") from exc
    require_regular(path, label)
    require(
        binding.get("sha256") == sha256_file(path)
        and is_exact_int(binding.get("size_bytes"))
        and binding.get("size_bytes") == path.stat().st_size,
        f"{label} physical hash/size binding mismatch",
    )
    return path


def load_case_order(path: Path) -> list[str]:
    require_regular(path, "expected case-order document")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QCFailure(f"cannot parse case-order document: {exc}") from exc
    if isinstance(value, list):
        order = value
    elif isinstance(value, dict) and isinstance(value.get("case_order"), list):
        order = value["case_order"]
    elif isinstance(value, dict) and isinstance(value.get("items"), list):
        order = [row.get("case_unit_id") if isinstance(row, dict) else None for row in value["items"]]
    else:
        raise QCFailure("case-order document has no list/case_order/items sequence")
    require(all(isinstance(item, str) and SAFE_CASE_ID_RE.fullmatch(item) for item in order),
            "case order contains an unsafe/non-string case id")
    return list(order)


@dataclass(frozen=True)
class PacketView:
    case_id: str
    task_id: str
    inventory: tuple[str, ...]
    sources: Mapping[str, Path]
    packet_sha256: str
    packet_path: Path
    packet_text: str


def _metadata_value(header: str, name: str) -> str:
    matches = re.findall(rf"^- {re.escape(name)}: `([^`\r\n]+)`$", header, re.MULTILINE)
    require(len(matches) == 1, f"packet has non-exact {name} metadata")
    return matches[0]


def parse_packet(packet_path: Path, case_dir: Path, expected_case: str, expected_task: str) -> PacketView:
    require_regular(packet_path, f"{expected_case} canonical packet")
    try:
        text = packet_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise QCFailure(f"{expected_case} packet is not valid UTF-8: {exc}") from exc
    require(text.count("## Source Inventory\n") == 1, f"{expected_case} packet Source Inventory is non-exact")
    require(text.count("## Packet Source Files\n") == 1, f"{expected_case} packet source section is non-exact")
    header, sections_text = text.split("## Packet Source Files\n", 1)
    inventory_text = header.split("## Source Inventory\n", 1)[1]
    inventory: list[str] = []
    for line in inventory_text.splitlines():
        if line.startswith("## "):
            break
        match = SOURCE_INVENTORY_RE.fullmatch(line)
        if match:
            inventory.append(match.group(1))
    require(inventory, f"{expected_case} Source Inventory is empty")
    require(len(inventory) == len(set(inventory)), f"{expected_case} Source Inventory has duplicates")
    for source_path in inventory:
        require(SAFE_SOURCE_PATH_RE.fullmatch(source_path) is not None,
                f"{expected_case} has unsafe Source Inventory path: {source_path!r}")
        require(all(part not in {"", ".", ".."} for part in source_path.split("/")),
                f"{expected_case} has dot/traversal Source Inventory path: {source_path!r}")
    sections = list(PACKET_SECTION_RE.finditer(sections_text))
    section_paths = [match.group("path") for match in sections]
    require(section_paths == inventory, f"{expected_case} packet source-section order differs from inventory")
    case_id = _metadata_value(header, "case_unit_id")
    domain = _metadata_value(header, "domain")
    task_id = _metadata_value(header, "task_id")
    require(case_id == expected_case and task_id == expected_task and domain == "androidworld",
            f"{expected_case} packet top-level identity mismatch")
    manifest = load_json(case_dir / "raw_case_manifest.json", f"{expected_case} raw-case manifest")
    require(manifest.get("case_unit_id") == expected_case and manifest.get("task_id", expected_task) == expected_task,
            f"{expected_case} raw-case manifest identity mismatch")
    require(manifest.get("packet_files") == inventory,
            f"{expected_case} raw-case manifest packet_files order mismatch")
    sha_map = manifest.get("sha256_per_file")
    require(isinstance(sha_map, dict) and set(sha_map) == set(inventory),
            f"{expected_case} raw-case manifest hash namespace mismatch")
    raw_root = require_directory(case_dir / "raw_case", f"{expected_case} raw-case root")
    sources: dict[str, Path] = {}
    for match, source_path in zip(sections, inventory, strict=True):
        source = raw_root / PurePosixPath(source_path)
        require_regular(source, f"{expected_case} raw source {source_path}")
        actual = source.read_bytes()
        require(sha_map[source_path] == sha256_bytes(actual),
                f"{expected_case} raw source hash mismatch: {source_path}")
        embedded = match.group("body").encode("utf-8")
        require(embedded == actual,
                f"{expected_case} embedded packet source differs bytewise: {source_path}")
        sources[source_path] = source
    observed_raw = []
    for path in sorted(raw_root.rglob("*"), key=lambda item: item.relative_to(raw_root).as_posix()):
        require(not path.is_symlink(), f"{expected_case} raw-case tree contains symlink")
        if path.is_file():
            observed_raw.append(path.relative_to(raw_root).as_posix())
    require(observed_raw == sorted(inventory), f"{expected_case} raw-case tree has missing/extra files")
    return PacketView(
        expected_case,
        expected_task,
        tuple(inventory),
        sources,
        sha256_file(packet_path),
        packet_path,
        text,
    )


def strip_null_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: strip_null_fields(child) for key, child in value.items() if child is not None}
    if isinstance(value, list):
        return [strip_null_fields(child) for child in value]
    return value


def canonical_checklist_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def canonical_checklist_yaml(value: Mapping[str, Any]) -> bytes:
    rendered = yaml.safe_dump(
        dict(value), sort_keys=False, allow_unicode=True, width=1000
    )
    return rendered.encode("utf-8")


def iter_atomic_supports(checklist: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    native = checklist.get("native")
    require(isinstance(native, dict), "native is not an object")
    require(tuple(native.keys()) == REQUIRED_NATIVE_FIELDS,
            "native keys/order are not the exact seven required categories")
    for name in ("user_goal", "benchmark_success", "checked_by"):
        item = native.get(name)
        require(isinstance(item, dict), f"native.{name} is not an object")
        yield f"native.{name}", item
    for name in ("decisive_artifacts", "success_if", "fail_if", "undecided_if"):
        items = native.get(name)
        require(isinstance(items, list) and items, f"native.{name} is not a non-empty list")
        for index, item in enumerate(items):
            require(isinstance(item, dict), f"native.{name}[{index}] is not an object")
            yield f"native.{name}[{index}]", item
    stronger = checklist.get("stronger")
    require(isinstance(stronger, dict) and tuple(stronger.keys()) == ("additional_conditions",),
            "stronger has a non-exact top-level shape")
    conditions = stronger.get("additional_conditions")
    require(isinstance(conditions, list), "stronger.additional_conditions is not a list")
    ids: list[str] = []
    for index, condition in enumerate(conditions):
        require(isinstance(condition, dict), f"stronger condition {index} is not an object")
        ids.append(str(condition.get("id") or ""))
        yield f"stronger.additional_conditions[{index}]", condition
        artifacts = condition.get("decisive_artifacts")
        require(isinstance(artifacts, list) and artifacts,
                f"stronger.additional_conditions[{index}].decisive_artifacts is empty")
        for artifact_index, artifact in enumerate(artifacts):
            require(isinstance(artifact, dict), "stronger decisive artifact is not an object")
            yield (
                f"stronger.additional_conditions[{index}].decisive_artifacts[{artifact_index}]",
                artifact,
            )
    require(all(ids) and len(ids) == len(set(ids)), "stronger condition ids are empty/duplicated")


def _python_qualnames(source_text: str, source_path: str) -> dict[str, ast.AST]:
    try:
        tree = ast.parse(source_text, filename=source_path)
    except SyntaxError as exc:
        raise QCFailure(f"Python source cannot be parsed for selector resolution: {source_path}: {exc}") from exc
    found: dict[str, ast.AST] = {}

    def visit(node: ast.AST, parents: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = ".".join((*parents, child.name))
                found[qualname] = child
                visit(child, (*parents, child.name))
            elif not isinstance(child, (ast.Lambda, ast.comprehension)):
                visit(child, parents)

    visit(tree, ())
    return found


def _semantic_lines(source_text: str, start: int, end: int, source_path: str) -> str:
    lines = source_text.splitlines(keepends=True)
    require(1 <= start <= end <= len(lines), f"line selector is out of range in {source_path}")
    snippet = "".join(lines[start - 1 : end])
    meaningful = "\n".join(
        line for line in snippet.splitlines() if line.strip() and not line.lstrip().startswith("#")
    )
    require(SEMANTIC_TEXT_RE.search(meaningful) is not None,
            f"line selector resolves only to blank/comment material in {source_path}")
    return snippet


def _resolve_json_pointer(value: Any, selector: str) -> Any:
    current = value
    if selector == "":
        return current
    require(selector.startswith("/"), "RFC6901 pointer must start with /")
    for raw in selector.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        require("~" not in re.sub(r"~[01]", "", raw), "invalid RFC6901 escape")
        if isinstance(current, list):
            require(re.fullmatch(r"0|[1-9][0-9]*", token) is not None,
                    "JSON pointer list token is not a canonical index")
            index = int(token)
            require(index < len(current), "JSON pointer index does not exist")
            current = current[index]
        elif isinstance(current, dict):
            require(token in current, f"JSON/YAML pointer key does not exist: {token}")
            current = current[token]
        else:
            raise QCFailure("JSON/YAML pointer traverses through a scalar")
    return current


def _resolve_dollar_path(value: Any, selector: str) -> Any:
    require(selector.startswith("$"), "JSON/YAML path must start with $")
    require(selector != "$", "JSON/YAML selector must identify a value below the document root")
    current = value
    cursor = 1
    while cursor < len(selector):
        match = JSON_PATH_TOKEN_RE.match(selector, cursor)
        require(match is not None, f"unsupported/non-exact JSON/YAML selector: {selector}")
        if match.group("name") is not None:
            name = match.group("name")
            require(isinstance(current, dict) and name in current,
                    f"JSON/YAML selector key does not exist: {name}")
            current = current[name]
        else:
            require(isinstance(current, list), "JSON/YAML index applied to non-list")
            index = int(match.group("index"))
            require(index < len(current), "JSON/YAML selector index does not exist")
            current = current[index]
        cursor = match.end()
    return current


def _require_nonempty_selected(value: Any, source_path: str) -> None:
    if isinstance(value, str):
        require(bool(value.strip()), f"selector resolves to an empty string in {source_path}")
    elif isinstance(value, (list, dict)):
        require(bool(value), f"selector resolves to an empty container in {source_path}")
    else:
        require(value is not None, f"selector resolves to null in {source_path}")


def resolve_selector(source_path: str, source_file: Path, selector: str) -> dict[str, Any]:
    require(selector == selector.strip() and selector, "support selector has surrounding whitespace/empty text")
    source_text = source_file.read_text(encoding="utf-8")
    for expression in LINE_SPAN_RES:
        match = expression.fullmatch(selector)
        if match:
            start = int(match.group("start"))
            end = int(match.group("end") or start)
            snippet = _semantic_lines(source_text, start, end, source_path)
            return {"kind": "line_span", "start_line": start, "end_line": end,
                    "snippet_sha256": sha256_bytes(snippet.encode("utf-8"))}
    suffix = source_file.suffix.lower()
    if suffix == ".py":
        symbols = _python_qualnames(source_text, source_path)
        relative = source_path
        for prefix in ("official/install/", "official/install/.venv311/lib/python3.11/site-packages/"):
            if relative.startswith(prefix):
                relative = relative[len(prefix) :]
                break
        module = relative.removesuffix(".py").replace("/", ".")
        module_tail = module.rsplit(".", 1)[-1]
        matches = []
        for qualname, node in symbols.items():
            candidates = {qualname, f"{module_tail}.{qualname}", f"{module}.{qualname}"}
            if selector in candidates:
                matches.append((qualname, node))
        require(len(matches) == 1, f"Python selector does not resolve to one exact AST qualname: {source_path}::{selector}")
        qualname, node = matches[0]
        start = int(getattr(node, "lineno", 0) or 0)
        end = int(getattr(node, "end_lineno", 0) or 0)
        snippet = _semantic_lines(source_text, start, end, source_path)
        body = getattr(node, "body", None)
        if isinstance(body, list):
            require(any(not isinstance(child, ast.Pass) for child in body),
                    f"Python selector resolves only to pass: {source_path}::{selector}")
        return {"kind": "python_ast_qualname", "qualified_symbol": qualname,
                "start_line": start, "end_line": end,
                "snippet_sha256": sha256_bytes(snippet.encode("utf-8"))}
    if suffix in {".json", ".yaml", ".yml"}:
        try:
            parsed = json.loads(source_text) if suffix == ".json" else yaml.safe_load(source_text)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise QCFailure(f"cannot parse selector source {source_path}: {exc}") from exc
        selected = _resolve_json_pointer(parsed, selector) if selector.startswith("/") else _resolve_dollar_path(parsed, selector)
        _require_nonempty_selected(selected, source_path)
        return {"kind": "json_yaml_selector", "selector": selector,
                "selected_sha256": canonical_sha256(selected)}
    raise QCFailure(
        f"non-Python/JSON/YAML support requires an explicit line span: {source_path}::{selector}"
    )


def validate_supports(checklist: Mapping[str, Any], packet: PacketView) -> dict[str, Any]:
    resolutions: list[dict[str, Any]] = []
    inventory = set(packet.inventory)
    for field_name, item in iter_atomic_supports(checklist):
        support = item.get("support")
        require(isinstance(support, list) and support,
                f"{field_name}.support must be non-empty; rationale never substitutes")
        require(len(support) == len(set(support)), f"{field_name}.support contains duplicates")
        raw_official = False
        for index, pointer in enumerate(support):
            require(isinstance(pointer, str) and pointer == pointer.strip() and pointer,
                    f"{field_name}.support[{index}] is not an exact non-empty string")
            require(pointer.count("::") == 1,
                    f"{field_name}.support[{index}] must contain exactly one ::")
            source_path, selector = pointer.split("::", 1)
            require(source_path in inventory,
                    f"{field_name}.support[{index}] is not an exact Source Inventory path: {source_path!r}")
            parts = source_path.split("/")
            require(source_path not in FORBIDDEN_SUPPORT_EXACT,
                    f"{field_name}.support[{index}] cites a forbidden alias")
            require(not URL_RE.match(source_path) and not source_path.startswith(("/", "./")),
                    f"{field_name}.support[{index}] uses URL/absolute/dot path")
            require("\\" not in source_path and all(part not in {"", ".", ".."} for part in parts),
                    f"{field_name}.support[{index}] would require path normalization")
            require(not any(part in FORBIDDEN_SUPPORT_SEGMENTS for part in parts),
                    f"{field_name}.support[{index}] cites packet/coverage/workspace material")
            require(not any(part in {"case_packet.md", "model_input_coverage.json"} for part in parts),
                    f"{field_name}.support[{index}] cites a forbidden packet/coverage file")
            raw_official = raw_official or source_path.startswith("official/")
            resolved = resolve_selector(source_path, packet.sources[source_path], selector)
            resolutions.append({"field": field_name, "pointer": pointer, "resolution": resolved})
        require(raw_official, f"{field_name} lacks raw official/... support")
    return {
        "atomic_item_count": len({row["field"] for row in resolutions}),
        "support_pointer_count": len(resolutions),
        "resolutions_sha256": canonical_sha256(resolutions),
    }


def _range_snippet(path: Path, start: int, end: int) -> bytes:
    lines = path.read_bytes().splitlines(keepends=True)
    require(1 <= start <= end <= len(lines), f"coverage range is outside {path}")
    return b"".join(lines[start - 1 : end])


def _validate_coverage_range(row: Mapping[str, Any], packet: PacketView, label: str) -> tuple[str, int, int]:
    source_path = row.get("path")
    require(isinstance(source_path, str) and source_path in packet.inventory,
            f"{label} path is not in exact Source Inventory")
    require(source_path.startswith("official/"), f"{label} is not raw official authority")
    require(row.get("raw_authority") == "official_source", f"{label} raw_authority mismatch")
    require(is_exact_int(row.get("start_line")) and is_exact_int(row.get("end_line")),
            f"{label} line bounds are not integers")
    start, end = int(row["start_line"]), int(row["end_line"])
    source = packet.sources[source_path]
    snippet = _range_snippet(source, start, end)
    require(row.get("file_sha256") == sha256_file(source), f"{label} file hash mismatch")
    require(row.get("snippet_sha256") == sha256_bytes(snippet), f"{label} snippet hash mismatch")
    return source_path, start, end


def validate_coverage(requirements: Mapping[str, Any], packet: PacketView) -> dict[str, Any]:
    require(
        set(requirements)
        == {
            "anchor_raw_official_ranges",
            "anchors",
            "case_packet_sha256",
            "case_unit_id",
            "coverage_page_count",
            "coverage_pages",
            "coverage_pagination",
            "decisive_call_closure",
            "derived_navigation",
            "policy",
            "production_namespace",
            "raw_official_distinct_sha_count",
            "raw_official_inventory_aliases_sha256",
            "raw_official_inventory_member_count",
            "raw_official_omitted_count",
            "raw_official_source_closure",
            "raw_official_source_closure_count",
            "required_range_count",
            "required_ranges",
            "requirements_sha256",
            "schema_version",
            "source_closure_audit",
            "source_inventory",
            "task_id",
            "tokenizer_binding",
        },
        f"{packet.case_id} coverage top-level field set is non-exact",
    )
    validate_layer_a_scalar_types(requirements)
    verify_self_hash(requirements, "requirements_sha256", f"{packet.case_id} coverage requirements")
    require(
        requirements.get("schema_version")
        == "androidworld_candidate116_staged_source_coverage_requirements/v1",
        f"{packet.case_id} coverage schema version mismatch",
    )
    require(requirements.get("production_namespace") == PRODUCTION_NAMESPACE
            and requirements.get("coverage_pagination")
            == "serialized_byte_and_o200k_token_envelope_v1"
            and requirements.get("case_unit_id") == packet.case_id
            and requirements.get("task_id") == packet.task_id,
            f"{packet.case_id} coverage identity mismatch")
    require(
        exact_json_equal(
            requirements.get("policy"),
            {
                "runtime_semantics_authority": "raw_official_source_ranges",
                "derived_role": "navigation_identity_closure_and_conflict_only",
                "required_anchors": list(REQUIRED_COVERAGE_ANCHORS),
                "max_coverage_chunk_bytes": MAX_COVERAGE_CHUNK_BYTES,
                "max_reader_envelope_bytes": MAX_READER_ENVELOPE_BYTES,
                "max_reader_envelope_o200k_tokens": MAX_READER_ENVELOPE_TOKENS,
                "max_plan_row_serialized_bytes": MAX_COVERAGE_PLAN_ROW_BYTES,
                "max_plan_page_output_bytes": MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES,
                "max_plan_page_o200k_tokens": MAX_COVERAGE_PLAN_PAGE_TOKENS,
                "recursive_source_ref_mapping_missing_count": 0,
                "source_binding_mapping_missing_count": 0,
                "every_distinct_raw_official_inventory_payload_must_be_read_completely": True,
                "raw_inventory_members_may_never_be_excluded_by_navigation_or_ast": True,
                "byte_identical_aliases_share_one_physical_read_only_when_hash_bound": True,
                "chunks_must_be_read_separately_in_listed_order": True,
                "case_packet_one_shot_read_forbidden": True,
            },
        ),
        f"{packet.case_id} coverage policy is not production-exact",
    )
    tokenizer = requirements.get("tokenizer_binding")
    require(
        isinstance(tokenizer, Mapping)
        and set(tokenizer)
        == {
            "encoding",
            "tiktoken_version",
            "merge_table_sha256",
            "binding_sha256",
        },
        f"{packet.case_id} tokenizer binding schema is non-exact",
    )
    verify_self_hash(tokenizer, "binding_sha256", f"{packet.case_id} tokenizer binding")
    require(
        tokenizer.get("encoding") == "o200k_base"
        and isinstance(tokenizer.get("tiktoken_version"), str)
        and re.fullmatch(r"[0-9a-f]{64}", str(tokenizer.get("merge_table_sha256")))
        is not None,
        f"{packet.case_id} tokenizer binding identity is invalid",
    )
    source_inventory = requirements.get("source_inventory")
    require(isinstance(source_inventory, list),
            f"{packet.case_id} source inventory binding is not a list")
    expected_inventory = [
        {
            "path": path,
            "sha256": sha256_file(packet.sources[path]),
            "size_bytes": packet.sources[path].stat().st_size,
            "line_count": len(
                packet.sources[path].read_bytes().splitlines(keepends=True)
            ),
        }
        for path in packet.inventory
    ]
    require(
        all(isinstance(row, Mapping) and set(row) == {
            "path", "sha256", "size_bytes", "line_count"
        } for row in source_inventory)
        and exact_json_equal(source_inventory, expected_inventory),
        f"{packet.case_id} source inventory does not exactly bind packet bytes",
    )
    derived_navigation = requirements.get("derived_navigation")
    require(
        isinstance(derived_navigation, Mapping)
        and set(derived_navigation)
        == {
            "canonical_module",
            "canonical_source_file",
            "metadata_comparison_status",
            "metadata_conflicts",
            "readiness",
            "record_sha256",
            "runtime_reported_class",
            "runtime_reported_module",
        },
        f"{packet.case_id} derived navigation schema is non-exact",
    )
    source_audit = requirements.get("source_closure_audit")
    require(
        isinstance(source_audit, Mapping)
        and set(source_audit)
        == {
            "method",
            "unresolved_internal_imports",
            "unresolved_internal_import_count",
            "plan_member_count",
            "plan_distinct_content_count",
        }
        and source_audit.get("method")
        == "all_raw_official_inventory_members_exhaustively_bound_before_ast_audit"
        and source_audit.get("unresolved_internal_imports") == []
        and is_exact_int(source_audit.get("unresolved_internal_import_count"))
        and source_audit.get("unresolved_internal_import_count") == 0
        and is_exact_int(source_audit.get("plan_member_count"))
        and source_audit.get("plan_member_count")
        == len([path for path in packet.inventory if path.startswith("official/")]),
        f"{packet.case_id} source closure audit is non-exact",
    )
    call_closure = requirements.get("decisive_call_closure")
    resolved_edges = (
        call_closure.get("resolved_edges")
        if isinstance(call_closure, Mapping)
        else None
    )
    unresolved_calls = (
        call_closure.get("unresolved_external_semantic_direct_calls")
        if isinstance(call_closure, Mapping)
        else None
    )
    require(
        isinstance(call_closure, Mapping)
        and set(call_closure)
        == {
            "algorithm",
            "fixed_point_reached",
            "packet_local_unresolved_count",
            "resolved_edges",
            "resolved_edges_sha256",
            "selected_definition_count",
            "unresolved_external_semantic_direct_calls",
        }
        and call_closure.get("algorithm") == "packet_local_ast_fixed_point_v1"
        and call_closure.get("fixed_point_reached") is True
        and is_exact_int(call_closure.get("packet_local_unresolved_count"))
        and call_closure.get("packet_local_unresolved_count") == 0
        and isinstance(resolved_edges, list)
        and all(
            isinstance(row, Mapping)
            and set(row)
            in (
                {
                    "call", "from", "semantic_direct", "to_end_line", "to_path",
                    "to_start_line", "to_symbol",
                },
                {
                    "call", "from", "resolution", "semantic_direct", "to_paths",
                    "to_symbol",
                },
            )
            for row in resolved_edges
        )
        and isinstance(unresolved_calls, list)
        and all(
            isinstance(row, Mapping)
            and set(row) == {"call", "classification", "from"}
            for row in unresolved_calls
        )
        and call_closure.get("resolved_edges_sha256")
        == canonical_sha256(resolved_edges),
        f"{packet.case_id} decisive call closure is non-exact",
    )
    anchors = requirements.get("anchors")
    require(isinstance(anchors, list), f"{packet.case_id} coverage anchors are not a list")
    require([row.get("anchor") if isinstance(row, dict) else None for row in anchors] == list(REQUIRED_COVERAGE_ANCHORS),
            f"{packet.case_id} coverage anchor order/set is incomplete")
    flattened_anchor_ranges: list[Mapping[str, Any]] = []
    for anchor in anchors:
        require(set(anchor) == {"anchor", "required_raw_official_ranges"},
                f"{packet.case_id} anchor field set is non-exact")
        ranges = anchor.get("required_raw_official_ranges")
        require(isinstance(ranges, list) and ranges,
                f"{packet.case_id} anchor {anchor.get('anchor')} has no raw official ranges")
        for index, row in enumerate(ranges):
            require(isinstance(row, dict), "coverage anchor range is not an object")
            require(set(row) == {
                "anchor", "raw_authority", "path", "start_line", "end_line",
                "file_sha256", "snippet_sha256", "owner_module", "owner_qualname",
            }, "coverage anchor range field set is non-exact")
            require(row.get("anchor") == anchor.get("anchor"), "coverage anchor label mismatch")
            _validate_coverage_range(row, packet, f"anchor {anchor.get('anchor')}[{index}]")
            flattened_anchor_ranges.append(row)
    metadata_range = anchors[0]["required_raw_official_ranges"][0]
    metadata_path = "official/install/android_world/task_metadata.json"
    require(
        metadata_range.get("path") == metadata_path
        and metadata_range.get("start_line") == 1
        and metadata_range.get("end_line")
        == len(packet.sources[metadata_path].read_bytes().splitlines(keepends=True)),
        f"{packet.case_id} metadata anchor is not the complete raw task_metadata.json",
    )
    flattened_anchor_ranges.sort(
        key=lambda row: (row["anchor"], row["path"], row["start_line"], row["end_line"])
    )
    declared_flat = requirements.get("anchor_raw_official_ranges")
    require(isinstance(declared_flat, list)
            and exact_json_equal(declared_flat, flattened_anchor_ranges),
            f"{packet.case_id} flattened anchor ranges differ from anchor declarations")
    closure = requirements.get("raw_official_source_closure")
    require(isinstance(closure, list) and closure,
            f"{packet.case_id} raw official source closure is empty")
    require(is_exact_int(requirements.get("raw_official_source_closure_count"))
            and requirements.get("raw_official_source_closure_count") == len(closure),
            f"{packet.case_id} raw closure count mismatch")
    closure_paths: list[str] = []
    bound_aliases: list[str] = []
    exact_chunk_rows: list[dict[str, Any]] = []
    for source_index, source_row in enumerate(closure):
        require(isinstance(source_row, dict), "coverage closure row is not an object")
        require(set(source_row) == {
            "chunks", "file_sha256", "line_count", "logical_alias_bindings",
            "logical_alias_count", "logical_aliases", "navigation_reasons",
            "path", "physical_read_path", "size_bytes",
        }, "coverage closure row field set is non-exact")
        source_path = source_row.get("path")
        require(isinstance(source_path, str) and source_path in packet.inventory and source_path.startswith("official/"),
                f"{packet.case_id} closure path is not raw official inventory")
        closure_paths.append(source_path)
        aliases = source_row.get("logical_aliases")
        if aliases is None:
            aliases = [source_path]
        require(isinstance(aliases, list) and aliases and aliases == sorted(aliases)
                and len(aliases) == len(set(aliases)) and source_path in aliases,
                f"{packet.case_id} closure aliases are not exact: {source_path}")
        representative = min(aliases, key=lambda value: ("/.venv" in value, value))
        require(source_path == representative
                and source_row.get("physical_read_path", source_path) == representative,
                f"{packet.case_id} closure physical representative is non-deterministic")
        require(all(
            isinstance(alias, str)
            and alias in packet.inventory
            and alias.startswith("official/")
            and sha256_file(packet.sources[alias]) == sha256_file(packet.sources[source_path])
            for alias in aliases
        ), f"{packet.case_id} closure aliases are not byte-identical raw inventory")
        require(is_exact_int(source_row.get("logical_alias_count"))
                and source_row.get("logical_alias_count") == len(aliases),
                f"{packet.case_id} closure alias count mismatch: {source_path}")
        alias_bindings = source_row.get("logical_alias_bindings")
        if alias_bindings is not None:
            require(isinstance(alias_bindings, list)
                    and [row.get("path") if isinstance(row, dict) else None for row in alias_bindings] == aliases,
                    f"{packet.case_id} closure alias binding order mismatch: {source_path}")
            for alias, binding in zip(aliases, alias_bindings, strict=True):
                require(isinstance(binding, Mapping) and set(binding) == {
                    "path", "file_sha256", "size_bytes", "line_count", "source_ref"
                }, f"{packet.case_id} closure alias binding field set is non-exact")
                alias_file = packet.sources[alias]
                require(binding.get("file_sha256") == sha256_file(alias_file)
                        and is_exact_int(binding.get("size_bytes"))
                        and binding.get("size_bytes") == alias_file.stat().st_size
                        and is_exact_int(binding.get("line_count"))
                        and binding.get("line_count") == len(alias_file.read_bytes().splitlines(keepends=True)),
                        f"{packet.case_id} closure logical alias binding mismatch: {alias}")
        bound_aliases.extend(aliases)
        source = packet.sources[source_path]
        line_count = len(source.read_bytes().splitlines(keepends=True))
        require(source_row.get("file_sha256") == sha256_file(source)
                and is_exact_int(source_row.get("size_bytes"))
                and source_row.get("size_bytes") == source.stat().st_size
                and is_exact_int(source_row.get("line_count"))
                and source_row.get("line_count") == line_count,
                f"{packet.case_id} closure file binding mismatch: {source_path}")
        chunks = source_row.get("chunks")
        require(isinstance(chunks, list) and chunks, f"{packet.case_id} closure chunks are empty: {source_path}")
        cursor = 1
        for chunk_index, chunk in enumerate(chunks):
            require(isinstance(chunk, dict), "coverage chunk is not an object")
            require(set(chunk) == {
                "chunk_count", "chunk_index", "end_line",
                "planned_reader_envelope_max_bytes",
                "planned_reader_envelope_max_o200k_tokens", "size_bytes",
                "snippet_ends_with_newline", "snippet_sha256", "start_line",
            }, "coverage chunk field set is non-exact")
            start, end = chunk.get("start_line"), chunk.get("end_line")
            require(is_exact_int(start) and is_exact_int(end)
                    and start == cursor and end >= start,
                    f"{packet.case_id} closure chunks are non-contiguous: {source_path}")
            snippet = _range_snippet(source, start, end)
            require(is_exact_int(chunk.get("chunk_index"))
                    and chunk.get("chunk_index") == chunk_index
                    and is_exact_int(chunk.get("chunk_count"))
                    and chunk.get("chunk_count") == len(chunks)
                    and is_exact_int(chunk.get("size_bytes"))
                    and chunk.get("size_bytes") == len(snippet)
                    and chunk.get("snippet_sha256") == sha256_bytes(snippet)
                    and type(chunk.get("snippet_ends_with_newline")) is bool
                    and chunk.get("snippet_ends_with_newline") is snippet.endswith(b"\n"),
                    f"{packet.case_id} closure chunk binding mismatch: {source_path}#{chunk_index}")
            policy = requirements.get("policy") or {}
            if "planned_reader_envelope_max_bytes" in chunk:
                require(is_exact_int(chunk.get("planned_reader_envelope_max_bytes"))
                        and chunk["planned_reader_envelope_max_bytes"]
                        <= policy.get("max_reader_envelope_bytes", chunk["planned_reader_envelope_max_bytes"]),
                        f"{packet.case_id} planned reader byte envelope exceeds policy")
            if "planned_reader_envelope_max_o200k_tokens" in chunk:
                require(is_exact_int(chunk.get("planned_reader_envelope_max_o200k_tokens"))
                        and chunk["planned_reader_envelope_max_o200k_tokens"]
                        <= policy.get("max_reader_envelope_o200k_tokens", chunk["planned_reader_envelope_max_o200k_tokens"]),
                        f"{packet.case_id} planned reader token envelope exceeds policy")
            exact_chunk_rows.append(
                {
                    "anchor": "raw_source_closure_chunk",
                    "raw_authority": "official_source",
                    "path": source_path,
                    "logical_aliases": aliases,
                    "start_line": start,
                    "end_line": end,
                    "file_sha256": sha256_file(source),
                    "snippet_sha256": sha256_bytes(snippet),
                    "chunk_index": chunk_index,
                    "chunk_count": len(chunks),
                    "chunk_size_bytes": len(snippet),
                    "owner_module": None,
                    "owner_qualname": "complete_file_chunk",
                }
            )
            cursor = end + 1
        require(cursor == line_count + 1, f"{packet.case_id} chunks do not exhaust file: {source_path}")
    require(len(closure_paths) == len(set(closure_paths)), f"{packet.case_id} closure has duplicate files")
    raw_inventory = [path for path in packet.inventory if path.startswith("official/")]
    require(sorted(bound_aliases) == sorted(raw_inventory) and len(bound_aliases) == len(set(bound_aliases)),
            f"{packet.case_id} closure does not bind every raw official inventory alias exactly once")
    require(is_exact_int(requirements.get("raw_official_inventory_member_count"))
            and requirements.get("raw_official_inventory_member_count") == len(raw_inventory)
            and is_exact_int(requirements.get("raw_official_distinct_sha_count"))
            and requirements.get("raw_official_distinct_sha_count") == len(closure)
            and is_exact_int(requirements.get("raw_official_omitted_count"))
            and requirements.get("raw_official_omitted_count") == 0,
            f"{packet.case_id} raw official inventory closure counters mismatch")
    if "raw_official_inventory_aliases_sha256" in requirements:
        require(requirements["raw_official_inventory_aliases_sha256"] == canonical_sha256(raw_inventory),
                f"{packet.case_id} raw official inventory alias-order hash mismatch")
    required_ranges = requirements.get("required_ranges")
    require(isinstance(required_ranges, list) and required_ranges,
            f"{packet.case_id} required coverage ranges are empty")
    require(is_exact_int(requirements.get("required_range_count"))
            and requirements.get("required_range_count") == len(required_ranges),
            f"{packet.case_id} required range count mismatch")
    for index, row in enumerate(required_ranges):
        require(isinstance(row, dict), "required coverage range is not an object")
        require(set(row) == {
            "anchor", "chunk_count", "chunk_index", "chunk_size_bytes",
            "end_line", "file_sha256", "logical_aliases", "owner_module",
            "owner_qualname", "path", "raw_authority",
            "snippet_ends_with_newline", "snippet_sha256", "start_line",
        }, "required coverage range field set is non-exact")
        _validate_coverage_range(row, packet, f"required range {index}")
    for chunk in exact_chunk_rows:
        require(any(all(exact_json_equal(row.get(key), value) for key, value in chunk.items())
                    for row in required_ranges),
                f"{packet.case_id} required ranges omit an exact raw closure chunk")
    for anchor_range in flattened_anchor_ranges:
        path, start, end = anchor_range["path"], anchor_range["start_line"], anchor_range["end_line"]
        matching_spans = sorted(
            (
                int(row["start_line"]),
                int(row["end_line"]),
            )
            for row in required_ranges
            if (
                row.get("path") == path
                or path in (row.get("logical_aliases") or [])
            )
            and row.get("file_sha256") == anchor_range.get("file_sha256")
            and type(row.get("start_line")) is int
            and type(row.get("end_line")) is int
            and row["end_line"] >= start
            and row["start_line"] <= end
        )
        cursor = start
        for span_start, span_end in matching_spans:
            if span_end < cursor:
                continue
            if span_start > cursor:
                break
            cursor = max(cursor, span_end + 1)
            if cursor > end:
                break
        require(cursor > end,
                f"{packet.case_id} anchor range is not contiguously covered by required reads")
    pages = requirements.get("coverage_pages")
    if pages is not None:
        require(isinstance(pages, list) and pages, "coverage_pages is not a non-empty list")
        cursor = 0
        for page_index, page in enumerate(pages):
            require(isinstance(page, dict)
                    and set(page) == {
                        "end_range_index_exclusive", "max_row_serialized_bytes",
                        "page_index", "planned_output_o200k_tokens",
                        "planned_output_size_bytes", "row_count", "start_range_index",
                    }
                    and is_exact_int(page.get("page_index"))
                    and page.get("page_index") == page_index
                    and is_exact_int(page.get("start_range_index"))
                    and page.get("start_range_index") == cursor
                    and is_exact_int(page.get("end_range_index_exclusive"))
                    and cursor < page["end_range_index_exclusive"] <= len(required_ranges)
                    and is_exact_int(page.get("row_count"))
                    and page.get("row_count") == page["end_range_index_exclusive"] - cursor,
                    f"{packet.case_id} serialized coverage page boundary mismatch: {page_index}")
            policy = requirements.get("policy") or {}
            if "planned_output_size_bytes" in page:
                require(is_exact_int(page["planned_output_size_bytes"])
                        and page["planned_output_size_bytes"]
                        <= policy.get("max_plan_page_output_bytes", page["planned_output_size_bytes"]),
                        f"{packet.case_id} coverage page byte envelope exceeds policy")
            if "planned_output_o200k_tokens" in page:
                require(is_exact_int(page["planned_output_o200k_tokens"])
                        and page["planned_output_o200k_tokens"]
                        <= policy.get("max_plan_page_o200k_tokens", page["planned_output_o200k_tokens"]),
                        f"{packet.case_id} coverage page token envelope exceeds policy")
            cursor = page["end_range_index_exclusive"]
        require(cursor == len(required_ranges)
                and is_exact_int(requirements.get("coverage_page_count"))
                and requirements.get("coverage_page_count") == len(pages),
                f"{packet.case_id} serialized coverage pages do not exhaust required ranges")
    else:
        page_size = requirements.get("coverage_page_size")
        require(is_exact_int(page_size) and page_size > 0, "coverage page size is invalid")
        require(is_exact_int(requirements.get("coverage_page_count"))
                and requirements.get("coverage_page_count") == (len(required_ranges) + page_size - 1) // page_size,
                f"{packet.case_id} coverage page count mismatch")
    return {
        "requirements_sha256": requirements["requirements_sha256"],
        "anchor_count": len(anchors),
        "raw_closure_file_count": len(closure),
        "required_range_count": len(required_ranges),
    }


def _required_reader_argv(row: Mapping[str, Any], requirements_sha: str) -> list[str]:
    return [
        "/usr/bin/python3", "packet_reader.py", "read", "--anchor", str(row["anchor"]),
        "--path", str(row["path"]), "--start", str(row["start_line"]), "--end",
        str(row["end_line"]), "--manifest-sha256", requirements_sha,
    ]


def _required_page_argv(page: int, requirements_sha: str) -> list[str]:
    return [
        "/usr/bin/python3", "packet_reader.py", "plan-page", "--page", str(page),
        "--manifest-sha256", requirements_sha,
    ]


def _sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def _codex_event_shell_carrier_binding() -> dict[str, Any]:
    """Independently reconstruct the frozen Codex 0.144.4 event carrier."""

    payload = {
        "schema_version": "codex_command_event_shell_carrier/v1",
        "codex_cli_version": "0.144.4",
        "shell_path": CODEX_EVENT_HOST_SHELL,
        "shell_flag": CODEX_EVENT_HOST_SHELL_FLAG,
        "inner_command_policy": "single_ascii_spaces_and_safe_reader_tokens_only",
        "event_serialization": "shell -lc single-quoted-inner-command",
        "bare_semantic_argv_event_allowed": False,
        "double_wrapper_allowed": False,
        "shell_operators_or_substitution_allowed": False,
        "calibration_basis": (
            "existing local Codex 0.144.4 item.started/item.completed "
            "command_execution events with safe inner payloads"
        ),
    }
    payload["carrier_binding_sha256"] = canonical_sha256(payload)
    return payload


def _render_codex_event_command(argv: Sequence[str]) -> str:
    require(bool(argv) and all(isinstance(token, str) and token for token in argv),
            "reader semantic argv is not a non-empty string sequence")
    inner = " ".join(argv)
    require(
        SAFE_READER_INNER_COMMAND_RE.fullmatch(inner) is not None
        and not any(
            token in inner
            for token in ("'", '"', "`", "$", ";", "&", "|", "\\", "\n", "\r")
        )
        and "  " not in inner,
        "reader semantic argv cannot use the frozen host shell carrier",
    )
    return f"{CODEX_EVENT_HOST_SHELL} {CODEX_EVENT_HOST_SHELL_FLAG} '{inner}'"


def _parse_codex_event_command(command: str) -> list[str]:
    """Accept one and only one exact host carrier; reject bare/double wrappers."""

    require(isinstance(command, str) and command,
            "command event carrier is not a non-empty string")
    prefix = f"{CODEX_EVENT_HOST_SHELL} {CODEX_EVENT_HOST_SHELL_FLAG} '"
    require(command.startswith(prefix) and command.endswith("'"),
            "command event is not the exact single host-shell carrier")
    inner = command[len(prefix) : -1]
    require(inner and "'" not in inner
            and SAFE_READER_INNER_COMMAND_RE.fullmatch(inner) is not None
            and "  " not in inner
            and not any(
                token in inner
                for token in ('"', "`", "$", ";", "&", "|", "\\", "\n", "\r")
            ),
            "host-shell carrier inner command is unsafe or nested")
    argv = inner.split(" ")
    require(all(argv) and _render_codex_event_command(argv) == command,
            "host-shell carrier is not canonical")
    require(argv[:2] == ["/usr/bin/python3", "packet_reader.py"],
            "host-shell carrier does not contain one packet reader")
    return argv


def _reader_envelope(
    *, kind: str, argv: Sequence[str], requirements_sha256: str, body: str
) -> tuple[str, dict[str, Any]]:
    require(body.endswith("\n"), "independent reader body lacks terminal newline")
    completion = {
        "argv_sha256": canonical_sha256(list(argv)),
        "body_sha256": _sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "kind": kind,
        "requirements_sha256": requirements_sha256,
    }
    output = body + READER_COMPLETION_PREFIX + json.dumps(
        completion, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n"
    return output, completion


def _expected_reader_operations(
    requirements: Mapping[str, Any], packet: PacketView
) -> list[dict[str, Any]]:
    """Independently reconstruct every layer-B command and exact stdout byte string."""

    req_sha = str(requirements.get("requirements_sha256") or "")
    require(re.fullmatch(r"[0-9a-f]{64}", req_sha) is not None,
            f"{packet.case_id} requirements hash is not lowercase SHA-256")
    require(packet.packet_text.count("## Packet Source Files\n") == 1,
            f"{packet.case_id} packet header boundary is non-exact")
    header_text = packet.packet_text.split("## Packet Source Files\n", 1)[0]
    required = requirements.get("required_ranges")
    pages = requirements.get("coverage_pages")
    require(isinstance(required, list) and required,
            f"{packet.case_id} required range plan is absent")
    require(isinstance(pages, list) and pages,
            f"{packet.case_id} serialized page plan is absent")
    operations: list[dict[str, Any]] = []

    def append(
        kind: str,
        argv: list[str],
        body: str,
        semantic_identity: Mapping[str, Any],
    ) -> None:
        output, completion = _reader_envelope(
            kind=kind,
            argv=argv,
            requirements_sha256=req_sha,
            body=body,
        )
        operations.append(
            {
                "operation_index": len(operations),
                "kind": kind,
                "argv": argv,
                "semantic_command": " ".join(argv),
                "exact_command": _render_codex_event_command(argv),
                "semantic_identity": dict(semantic_identity),
                "body": body,
                "output": output,
                "completion": completion,
            }
        )

    overview_keys = (
        "schema_version",
        "production_namespace",
        "case_unit_id",
        "task_id",
        "policy",
        "requirements_sha256",
        "required_range_count",
        "coverage_page_count",
        "raw_official_source_closure_count",
        "raw_official_inventory_member_count",
        "raw_official_distinct_sha_count",
        "raw_official_omitted_count",
        "derived_navigation",
        "anchors",
    )
    try:
        overview_payload = {key: requirements[key] for key in overview_keys}
    except KeyError as exc:
        raise QCFailure(
            f"{packet.case_id} coverage cannot render exact overview; missing {exc.args[0]}"
        ) from exc
    overview_argv = ["/usr/bin/python3", "packet_reader.py", "overview"]
    overview_body = READER_BODY_PREFIX + json.dumps(
        {"kind": "overview"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    overview_body += json.dumps(
        overview_payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    append(
        "overview",
        overview_argv,
        overview_body,
        {
            "case_unit_id": requirements["case_unit_id"],
            "required_range_count": requirements["required_range_count"],
            "coverage_page_count": requirements["coverage_page_count"],
        },
    )

    header_argv = ["/usr/bin/python3", "packet_reader.py", "header"]
    header_body = READER_BODY_PREFIX + json.dumps(
        {"case_packet_sha256": packet.packet_sha256, "kind": "header"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    header_body += header_text if header_text.endswith("\n") else header_text + "\n"
    append(
        "header",
        header_argv,
        header_body,
        {
            "case_packet_sha256": packet.packet_sha256,
            "header_sha256": _sha256_text(header_text),
            "header_size_bytes": len(header_text.encode("utf-8")),
        },
    )

    page_count = int(requirements.get("coverage_page_count") or 0)
    require(len(pages) == page_count, f"{packet.case_id} page plan/count mismatch")
    for page_index, page in enumerate(pages):
        require(isinstance(page, Mapping), f"{packet.case_id} page row is not an object")
        start = page.get("start_range_index")
        end = page.get("end_range_index_exclusive")
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(required),
                f"{packet.case_id} page bounds are invalid: {page_index}")
        page_argv = _required_page_argv(page_index, req_sha)
        page_body = READER_BODY_PREFIX + json.dumps(
            {"kind": "plan-page", "page_index": page_index, "page_count": page_count},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        page_body += json.dumps(
            {
                "page_index": page_index,
                "page_count": page_count,
                "requirements_sha256": req_sha,
                "rows": required[start:end],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        append(
            "plan-page",
            page_argv,
            page_body,
            {
                "page_index": page_index,
                "start_range_index": start,
                "end_range_index_exclusive": end,
                "rows_sha256": canonical_sha256(required[start:end]),
            },
        )

    identity_keys = (
        "anchor",
        "path",
        "start_line",
        "end_line",
        "file_sha256",
        "snippet_sha256",
        "chunk_size_bytes",
        "snippet_ends_with_newline",
        "chunk_index",
        "chunk_count",
    )
    for range_index, row in enumerate(required):
        require(isinstance(row, Mapping), f"{packet.case_id} range row is not an object")
        source_path = row.get("path")
        require(isinstance(source_path, str) and source_path in packet.sources,
                f"{packet.case_id} read source is outside packet inventory")
        source_text = packet.sources[source_path].read_text(encoding="utf-8")
        lines = source_text.splitlines(keepends=True)
        start = int(row["start_line"])
        end = int(row["end_line"])
        snippet = "".join(lines[start - 1 : end])
        require(_sha256_text(snippet) == row.get("snippet_sha256"),
                f"{packet.case_id} independent read snippet hash mismatch: {range_index}")
        try:
            reader_identity = {key: row[key] for key in identity_keys}
        except KeyError as exc:
            raise QCFailure(
                f"{packet.case_id} range {range_index} lacks reader identity {exc.args[0]}"
            ) from exc
        read_body = READER_BODY_PREFIX + json.dumps(
            {"kind": "read", "identity": reader_identity},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        read_body += snippet
        if not snippet.endswith("\n"):
            read_body += "\n"
        append(
            "read",
            _required_reader_argv(row, req_sha),
            read_body,
            {
                "range_index": range_index,
                "range_sha256": canonical_sha256(row),
                "path": row["path"],
                "logical_aliases": row["logical_aliases"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "file_sha256": row["file_sha256"],
                "snippet_sha256": row["snippet_sha256"],
                "chunk_size_bytes": row["chunk_size_bytes"],
            },
        )
    return operations


def verify_reader_operation_expectations(
    requirements: Mapping[str, Any],
    operation_expectations: Mapping[str, Any],
    packet: PacketView,
) -> list[dict[str, Any]]:
    """Independently bind layer B to layer A and the canonical packet bytes."""

    verify_self_hash(requirements, "requirements_sha256", "coverage requirements")
    verify_self_hash(
        operation_expectations,
        "reader_operation_expectations_sha256",
        "reader operation expectations",
    )
    require(
        set(operation_expectations)
        == {
            "schema_version",
            "production_namespace",
            "case_unit_id",
            "task_id",
            "coverage_requirements_sha256",
            "case_packet_sha256",
            "tokenizer_binding",
            "event_trust_policy",
            "event_shell_carrier",
            "global_order",
            "operation_count",
            "overview_operation_count",
            "header_operation_count",
            "plan_page_operation_count",
            "read_operation_count",
            "operations",
            "operations_sha256",
            "reader_operation_expectations_sha256",
        },
        f"{packet.case_id} reader operation expectations field set is non-exact",
    )
    requirements_sha = requirements["requirements_sha256"]
    require(
        operation_expectations.get("schema_version")
        == READER_OPERATION_EXPECTATIONS_SCHEMA
        and operation_expectations.get("production_namespace") == PRODUCTION_NAMESPACE
        and requirements.get("production_namespace") == PRODUCTION_NAMESPACE
        and operation_expectations.get("coverage_requirements_sha256") == requirements_sha
        and operation_expectations.get("case_unit_id") == packet.case_id
        and operation_expectations.get("task_id") == packet.task_id
        and operation_expectations.get("case_packet_sha256") == packet.packet_sha256
        and exact_json_equal(
            operation_expectations.get("tokenizer_binding"),
            requirements.get("tokenizer_binding"),
        ),
        f"{packet.case_id} reader operation expectations do not bind layer A/packet",
    )
    expected_policy = {
        "accepted_event_type": "item.completed",
        "accepted_output_field": "aggregated_output",
        "same_id_started_completed_pair_required": True,
        "completed_status_required": "completed",
        "completed_exit_code_required": 0,
        "model_supplied_shell_wrapper_pipeline_or_chain_allowed": False,
        "additional_command_count_allowed": 0,
        "terminal_completion_must_be_unique_and_last": True,
        "full_body_and_output_identity_required": True,
        "agent_message_before_or_between_commands_allowed": False,
        "terminal_agent_message_count_required": 1,
        "reasoning_items_allowed_before_terminal_agent_message": True,
        "exact_outer_framing_required": (
            "thread.started_then_turn.started_then_items_then_turn.completed"
        ),
    }
    require(exact_json_equal(
                operation_expectations.get("event_trust_policy"), expected_policy
            ),
            f"{packet.case_id} event trust policy is not exact")
    require(
        exact_json_equal(
            operation_expectations.get("event_shell_carrier"),
            _codex_event_shell_carrier_binding(),
        ),
        f"{packet.case_id} Codex event host-shell carrier binding is not exact",
    )
    require(
        operation_expectations.get("global_order")
        == "overview_then_header_then_all_pages_then_all_ranges",
        f"{packet.case_id} reader global order is not exact",
    )
    observed_operations = operation_expectations.get("operations")
    require(isinstance(observed_operations, list) and observed_operations,
            f"{packet.case_id} layer-B operations are empty")
    require(
        is_exact_int(operation_expectations.get("operation_count"))
        and operation_expectations.get("operation_count") == len(observed_operations)
        and operation_expectations.get("operations_sha256")
        == canonical_sha256(observed_operations),
        f"{packet.case_id} layer-B count/list hash mismatch",
    )
    expected_specs = _expected_reader_operations(requirements, packet)
    expected_kinds = [row["kind"] for row in expected_specs]
    require(len(observed_operations) == len(expected_specs),
            f"{packet.case_id} layer-B operation count differs from independent plan")
    require(
        is_exact_int(operation_expectations.get("overview_operation_count"))
        and operation_expectations.get("overview_operation_count") == 1
        and is_exact_int(operation_expectations.get("header_operation_count"))
        and operation_expectations.get("header_operation_count") == 1
        and is_exact_int(operation_expectations.get("plan_page_operation_count"))
        and operation_expectations.get("plan_page_operation_count")
        == int(requirements["coverage_page_count"])
        and is_exact_int(operation_expectations.get("read_operation_count"))
        and operation_expectations.get("read_operation_count")
        == int(requirements["required_range_count"])
        and [row.get("kind") if isinstance(row, Mapping) else None for row in observed_operations]
        == expected_kinds,
        f"{packet.case_id} layer-B kind counters/order mismatch",
    )
    expected_keys = {
        "operation_index",
        "kind",
        "argv",
        "argv_sha256",
        "semantic_command",
        "exact_command",
        "event_command_sha256",
        "semantic_identity",
        "body_sha256",
        "body_size_bytes",
        "body_line_count",
        "body_ends_with_newline",
        "terminal_completion",
        "expected_full_output_sha256",
        "expected_full_output_size_bytes",
        "expected_full_output_o200k_tokens",
        "max_full_output_size_bytes",
        "max_full_output_o200k_tokens",
        "aggregated_output_must_equal_exact_bytes",
        "operation_sha256",
    }
    for index, (operation, spec) in enumerate(
        zip(observed_operations, expected_specs, strict=True)
    ):
        require(isinstance(operation, Mapping),
                f"{packet.case_id} layer-B operation {index} is not an object")
        require(set(operation) == expected_keys,
                f"{packet.case_id} layer-B operation {index} field set is non-exact")
        operation_core = dict(operation)
        claimed_operation_sha = operation_core.pop("operation_sha256", None)
        kind = spec["kind"]
        max_bytes = (
            MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES
            if kind == "plan-page"
            else MAX_READER_ENVELOPE_BYTES
        )
        max_tokens = (
            MAX_COVERAGE_PLAN_PAGE_TOKENS
            if kind == "plan-page"
            else MAX_READER_ENVELOPE_TOKENS
        )
        output = str(spec["output"])
        body = str(spec["body"])
        token_count = operation.get("expected_full_output_o200k_tokens")
        require(
            is_exact_int(operation.get("operation_index"))
            and operation.get("operation_index") == index
            and operation.get("kind") == kind
            and operation.get("argv") == spec["argv"]
            and operation.get("argv_sha256") == canonical_sha256(spec["argv"])
            and operation.get("semantic_command") == spec["semantic_command"]
            and operation.get("exact_command") == spec["exact_command"]
            and operation.get("event_command_sha256")
            == _sha256_text(spec["exact_command"])
            and exact_json_equal(
                operation.get("semantic_identity"), spec["semantic_identity"]
            )
            and operation.get("body_sha256") == _sha256_text(body)
            and is_exact_int(operation.get("body_size_bytes"))
            and operation.get("body_size_bytes") == len(body.encode("utf-8"))
            and is_exact_int(operation.get("body_line_count"))
            and operation.get("body_line_count") == body.count("\n")
            and operation.get("body_ends_with_newline") is True
            and exact_json_equal(
                operation.get("terminal_completion"), spec["completion"]
            )
            and operation.get("expected_full_output_sha256") == _sha256_text(output)
            and is_exact_int(operation.get("expected_full_output_size_bytes"))
            and operation.get("expected_full_output_size_bytes")
            == len(output.encode("utf-8"))
            and is_exact_int(token_count)
            and 0 < token_count <= max_tokens
            and is_exact_int(operation.get("max_full_output_size_bytes"))
            and operation.get("max_full_output_size_bytes") == max_bytes
            and is_exact_int(operation.get("max_full_output_o200k_tokens"))
            and operation.get("max_full_output_o200k_tokens") == max_tokens
            and operation.get("aggregated_output_must_equal_exact_bytes") is True
            and len(output.encode("utf-8")) <= max_bytes
            and claimed_operation_sha == canonical_sha256(operation_core),
            f"{packet.case_id} layer-B operation {index} differs from independent reconstruction",
        )
    return expected_specs


def _ordered_completed_command_records(
    events: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    require(len(events) >= 5, "Codex event ledger is too short")
    thread_event = events[0]
    turn_started = events[1]
    final_agent_event = events[-2]
    turn_completed = events[-1]
    require(
        set(thread_event) == {"type", "thread_id"}
        and thread_event.get("type") == "thread.started"
        and isinstance(thread_event.get("thread_id"), str)
        and bool(thread_event.get("thread_id")),
        "event framing lacks one exact initial thread.started",
    )
    require(
        set(turn_started) == {"type"}
        and turn_started.get("type") == "turn.started",
        "event framing lacks one exact turn.started after thread.started",
    )
    require(
        set(final_agent_event) == {"type", "item"}
        and final_agent_event.get("type") == "item.completed"
        and isinstance(final_agent_event.get("item"), Mapping),
        "event framing lacks one final agent item",
    )
    final_agent = final_agent_event["item"]
    require(
        set(final_agent) == {"id", "type", "text"}
        and final_agent.get("type") == "agent_message"
        and isinstance(final_agent.get("id"), str)
        and bool(final_agent.get("id"))
        and isinstance(final_agent.get("text"), str)
        and final_agent.get("text") == final_agent.get("text", "").strip(),
        "final agent item is not one exact JSON-only message",
    )
    try:
        final_json = json.loads(final_agent["text"])
    except json.JSONDecodeError as exc:
        raise QCFailure("final agent message contains non-JSON text") from exc
    require(
        isinstance(final_json, Mapping)
        and set(final_json) == {"native", "stronger"},
        "final agent message is not the exact raw draft JSON body",
    )
    required_usage = {
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    }
    usage = turn_completed.get("usage")
    require(
        set(turn_completed) == {"type", "usage"}
        and turn_completed.get("type") == "turn.completed"
        and isinstance(usage, Mapping)
        and set(usage) == required_usage
        and all(is_exact_int(usage.get(key)) and usage[key] >= 0 for key in required_usage)
        and usage["cached_input_tokens"] <= usage["input_tokens"]
        and usage["reasoning_output_tokens"] <= usage["output_tokens"],
        "event framing lacks one exact terminal turn.completed usage record",
    )
    seen_ids: set[str] = set()
    active: tuple[str, str] | None = None
    completed: list[dict[str, str]] = []
    command_item_keys = {
        "aggregated_output",
        "command",
        "exit_code",
        "id",
        "status",
        "type",
    }
    for event in events[2:-2]:
        require(set(event) == {"type", "item"},
                "non-exact event appears inside the item sequence")
        item = event.get("item")
        if isinstance(item, Mapping) and item.get("type") == "reasoning":
            require(
                set(item) == {"id", "type", "text"}
                and event.get("type") in {"item.started", "item.completed"}
                and isinstance(item.get("id"), str)
                and bool(item.get("id"))
                and isinstance(item.get("text"), str)
                and active is None,
                "reasoning item shape/order is not exact",
            )
            continue
        require(isinstance(item, Mapping)
                and set(item) == command_item_keys
                and item.get("type") == "command_execution",
                "non-command/intermediate agent item appears before final JSON")
        item_id = item.get("id")
        command = item.get("command")
        require(isinstance(item_id, str) and item_id
                and isinstance(command, str) and command,
                "command execution event lacks one stable id/exact command")
        event_type = event.get("type")
        if event_type == "item.started":
            require(active is None, "packet-reader command executions overlap")
            require(item_id not in seen_ids, "one command id is reused")
            require(item.get("status") == "in_progress"
                    and item.get("exit_code") is None
                    and item.get("aggregated_output") == "",
                    "command start item shape/status is not exact")
            seen_ids.add(item_id)
            active = (item_id, command)
            continue
        require(event_type == "item.completed",
                "command execution event is neither started nor completed")
        require(active == (item_id, command),
                "command completion lacks its exact active same-id start")
        require(item.get("status") == "completed"
                and type(item.get("exit_code")) is int
                and item.get("exit_code") == 0,
                "packet-reader completion is not exact status=completed/exit_code=0")
        output = item.get("aggregated_output")
        require(isinstance(output, str),
                "packet-reader completion lacks its own aggregated_output")
        completed.append({"id": item_id, "command": command, "output": output})
        active = None
    require(completed and active is None and len(seen_ids) == len(completed),
            "a command id lacks exactly one start and successful completion")
    return completed


def _verify_completed_envelope(
    *, output: str, spec: Mapping[str, Any], requirements_sha256: str
) -> dict[str, Any]:
    require(output.endswith("\n"), "reader aggregated_output lacks terminal newline")
    marker_start = output.rfind("\n" + READER_COMPLETION_PREFIX)
    require(marker_start >= 0, "reader aggregated_output lacks terminal completion marker")
    body = output[: marker_start + 1]
    marker_line = output[marker_start + 1 : -1]
    require(READER_COMPLETION_PREFIX not in body
            and "\n" not in marker_line
            and marker_line.startswith(READER_COMPLETION_PREFIX),
            "reader completion marker is missing, duplicated, or non-terminal")
    try:
        completion = json.loads(marker_line[len(READER_COMPLETION_PREFIX) :])
    except json.JSONDecodeError as exc:
        raise QCFailure("reader terminal completion marker is invalid JSON") from exc
    require(isinstance(completion, dict),
            "reader terminal completion marker is not an object")
    expected_completion = {
        "argv_sha256": canonical_sha256(spec["argv"]),
        "body_sha256": _sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "kind": spec["kind"],
        "requirements_sha256": requirements_sha256,
    }
    require(exact_json_equal(completion, expected_completion),
            "reader terminal proof does not bind exact body/argv")
    require(body == spec["body"] and output == spec["output"],
            "reader aggregated_output differs from independently reconstructed bytes")
    return completion


def verify_event_ledger(
    events: Sequence[Mapping[str, Any]],
    requirements: Mapping[str, Any],
    operation_expectations: Mapping[str, Any],
    receipt: Mapping[str, Any],
    packet: PacketView,
) -> dict[str, Any]:
    """Replay A+B without importing or trusting the generation verifier."""

    specs = verify_reader_operation_expectations(
        requirements, operation_expectations, packet
    )
    operations = list(operation_expectations["operations"])
    records = _ordered_completed_command_records(events)
    require(len(records) == len(operations),
            "completed command count differs from exact layer-B ledger")
    req_sha = str(requirements["requirements_sha256"])
    required = list(requirements["required_ranges"])
    command_ids: list[str] = []
    completed_operations: list[dict[str, Any]] = []
    covered_ranges: list[dict[str, Any]] = []
    for record, operation, spec in zip(records, operations, specs, strict=True):
        observed_argv = _parse_codex_event_command(record["command"])
        require(observed_argv == operation["argv"]
                and record["command"] == operation["exact_command"],
                "reader command differs from layer B; wrappers/chains/pipelines are forbidden")
        completion = _verify_completed_envelope(
            output=record["output"], spec=spec, requirements_sha256=req_sha
        )
        output_sha = _sha256_text(record["output"])
        output_size = len(record["output"].encode("utf-8"))
        require(
            output_sha == operation["expected_full_output_sha256"]
            and output_size == operation["expected_full_output_size_bytes"]
            and output_size <= operation["max_full_output_size_bytes"],
            "completed output differs from layer-B full identity",
        )
        command_ids.append(record["id"])
        completed_operations.append(
            {
                "operation_index": operation["operation_index"],
                "kind": operation["kind"],
                "operation_sha256": operation["operation_sha256"],
                "completed_event_id": record["id"],
                "argv_sha256": operation["argv_sha256"],
                "event_command_sha256": operation["event_command_sha256"],
                "expected_output_sha256": operation["expected_full_output_sha256"],
                "observed_output_sha256": output_sha,
                "observed_output_size_bytes": output_size,
                "completion_proof": completion,
            }
        )
        if operation["kind"] != "read":
            continue
        identity = operation["semantic_identity"]
        range_index = identity.get("range_index")
        require(type(range_index) is int and 0 <= range_index < len(required),
                "read operation has invalid range index")
        row = required[range_index]
        require(identity.get("range_sha256") == canonical_sha256(row),
                "read operation does not bind its exact layer-A row")
        covered_ranges.append(
            {
                "range_index": range_index,
                "anchor": row["anchor"],
                "path": row["path"],
                "logical_aliases": row["logical_aliases"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "file_sha256": row["file_sha256"],
                "snippet_sha256": row["snippet_sha256"],
                "reader_argv_sha256": operation["argv_sha256"],
                "completed_event_id": record["id"],
                "completed_output_sha256": output_sha,
                "completion_proof": completion,
            }
        )
    require([row["range_index"] for row in covered_ranges] == list(range(len(required))),
            "covered ranges are not the exact ordered layer-A sequence")
    require(len(command_ids) == len(set(command_ids)),
            "completed reader command event id is reused")
    expected_receipt: dict[str, Any] = {
        "schema_version": COVERAGE_RECEIPT_SCHEMA,
        "production_namespace": PRODUCTION_NAMESPACE,
        "status": "all_required_reader_operations_completed",
        "case_unit_id": requirements["case_unit_id"],
        "requirements_sha256": req_sha,
        "reader_operation_expectations_sha256": operation_expectations[
            "reader_operation_expectations_sha256"
        ],
        "operations_sha256": operation_expectations["operations_sha256"],
        "required_operation_count": len(operations),
        "completed_operation_count": len(completed_operations),
        "completed_operations": completed_operations,
        "completed_operations_sha256": canonical_sha256(completed_operations),
        "completed_command_event_ids": command_ids,
        "completed_command_event_ids_sha256": canonical_sha256(command_ids),
        "required_range_count": len(required),
        "covered_range_count": len(covered_ranges),
        "covered_ranges": covered_ranges,
        "coverage_page_count": requirements["coverage_page_count"],
        "coverage_pages_read": list(range(int(requirements["coverage_page_count"]))),
        "additional_command_count": 0,
        "global_order": "overview_then_header_then_all_pages_then_all_ranges",
    }
    expected_receipt["coverage_receipt_sha256"] = canonical_sha256(expected_receipt)
    require(exact_json_equal(dict(receipt), expected_receipt),
            "coverage receipt is not the exact independently reconstructed A+B/v2 receipt")
    return {
        "event_count": len(events),
        "command_count": len(records),
        "required_operation_count": len(operations),
        "reader_operation_expectations_sha256": operation_expectations[
            "reader_operation_expectations_sha256"
        ],
        "coverage_receipt_sha256": expected_receipt["coverage_receipt_sha256"],
    }


def _get_one_option(command: Sequence[str], option: str) -> str:
    indices = [index for index, token in enumerate(command) if token == option]
    require(len(indices) == 1 and indices[0] + 1 < len(command), f"Codex command option is non-exact: {option}")
    return command[indices[0] + 1]


def validate_codex_command(
    command: Any,
    runtime: Mapping[str, Any],
    cli_path: Path,
    case_id: str,
    expected_argv_sha256: str,
) -> dict[str, Any]:
    require(isinstance(command, list) and all(isinstance(item, str) for item in command),
            f"{case_id} Codex command is not a string argv")
    require(command[:5] == [str(cli_path.resolve()), "-a", "never", "--strict-config", "exec"],
            f"{case_id} Codex approval/strict-config prefix is not exact")
    require(not {"--sandbox", "-s", "--add-dir", "--search"}.intersection(command),
            f"{case_id} Codex command contains forbidden privilege/search flag")
    require(command[-1:] == ["-"], f"{case_id} Codex command does not use stdin prompt sentinel")
    require(_get_one_option(command, "--model") == runtime.get("model"),
            f"{case_id} Codex command model mismatch")
    workspace = Path(_get_one_option(command, "--cd"))
    require(workspace.name == case_id, f"{case_id} Codex workspace basename mismatch")
    require(Path(_get_one_option(command, "--output-schema")) == workspace / "output_schema.json",
            f"{case_id} Codex output schema path is outside exact case workspace")
    require(Path(_get_one_option(command, "-o")) == workspace / "draft_body.json",
            f"{case_id} Codex structured output path is outside exact case workspace")
    disabled = [command[index + 1] for index, token in enumerate(command[:-1]) if token == "--disable"]
    require(disabled == runtime.get("disabled_features"),
            f"{case_id} Codex disabled-feature sequence mismatch")
    configs = [command[index + 1] for index, token in enumerate(command[:-1]) if token == "-c"]
    require(configs == runtime.get("config_overrides"),
            f"{case_id} Codex config override sequence mismatch")
    for flag in runtime.get("required_flags") or []:
        require(command.count(flag) == 1, f"{case_id} Codex required flag is absent/duplicated: {flag}")
    argv_sha256 = canonical_sha256(command)
    require(
        isinstance(expected_argv_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", expected_argv_sha256) is not None
        and argv_sha256 == expected_argv_sha256,
        f"{case_id} Codex argv differs from the exact prelocked per-case command",
    )
    return {"argv_sha256": argv_sha256, "workspace": str(workspace)}


def _normalized_usage(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    completed = next((event for event in reversed(events) if event.get("type") == "turn.completed"), {})
    usage = completed.get("usage")
    require(isinstance(usage, dict), "turn.completed lacks exact token usage")
    required_fields = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    require(
        set(usage) == set(required_fields)
        and all(is_exact_int(usage.get(field)) and usage[field] >= 0 for field in required_fields)
        and usage["cached_input_tokens"] <= usage["input_tokens"]
        and usage["reasoning_output_tokens"] <= usage["output_tokens"],
        "turn.completed token usage contains missing/non-integer/negative values",
    )
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_tokens_details": {"cached_tokens": usage["cached_input_tokens"]},
        "output_tokens_details": {
            "reasoning_tokens": usage["reasoning_output_tokens"]
        },
    }


def _validated_actual_usage(
    events: Sequence[Mapping[str, Any]], *, max_output_tokens: int
) -> dict[str, Any]:
    """Normalize real Codex 0.144.4 usage and enforce frozen capacity."""

    require(
        is_exact_int(max_output_tokens) and max_output_tokens > 0,
        "frozen maximum output-token capacity is not one positive integer",
    )
    usage = _normalized_usage(events)
    require(
        usage["output_tokens"] <= max_output_tokens
        and usage["total_tokens"] <= MAX_CODEX_TOTAL_TOKENS,
        "actual Codex token usage exceeds the frozen capacity",
    )
    return usage


def _token_usage(usage: Mapping[str, Any]) -> dict[str, int]:
    input_details = usage.get("input_tokens_details")
    output_details = usage.get("output_tokens_details")
    values = {
        "prompt_tokens": usage.get("input_tokens"),
        "completion_tokens": usage.get("output_tokens"),
        "cached_prompt_tokens": (
            input_details.get("cached_tokens")
            if isinstance(input_details, Mapping)
            else None
        ),
        "reasoning_tokens": (
            output_details.get("reasoning_tokens")
            if isinstance(output_details, Mapping)
            else None
        ),
        "total_tokens": usage.get("total_tokens"),
    }
    require(
        all(is_exact_int(value) and value >= 0 for value in values.values()),
        "normalized API token usage contains non-integer/negative values",
    )
    return values  # type: ignore[return-value]


def validate_case_outputs(
    *, case_id: str, task_id: str, case_dir: Path, packet: PacketView,
    requirements: Mapping[str, Any],
    operation_expectations: Mapping[str, Any],
    schema: Mapping[str, Any], runtime: Mapping[str, Any],
    cli_path: Path, expected_case_files: Sequence[str], expected_attempt_index: int,
    expected_codex_argv_sha256: str,
) -> dict[str, Any]:
    require_directory(case_dir, f"{case_id} raw output directory")
    observed: list[str] = []
    for path in sorted(case_dir.rglob("*"), key=lambda item: item.relative_to(case_dir).as_posix()):
        require(not path.is_symlink(), f"{case_id} output contains symlink")
        if path.is_file():
            observed.append(path.relative_to(case_dir).as_posix())
    require(observed == sorted(expected_case_files), f"{case_id} output file namespace differs from expectation")
    prefix = f"attempt_{expected_attempt_index:02d}."
    stable_names = (
        "checklist.yaml", "checklist.json", "api_response.json", "llm_call.json",
        "reasoning_summary.txt", "stderr.log", "stdout.log",
    )
    bindings: dict[str, Any] = {}
    for stable in stable_names:
        stable_path = require_regular(case_dir / stable, f"{case_id} {stable}")
        attempt_path = require_regular(case_dir / f"{prefix}{stable}", f"{case_id} selected-attempt {stable}")
        require(stable_path.read_bytes() == attempt_path.read_bytes(),
                f"{case_id} stable {stable} is not byte-identical to selected attempt")
        bindings[stable] = {"sha256": sha256_file(stable_path), "size_bytes": stable_path.stat().st_size}
    checklist_json_path = case_dir / "checklist.json"
    checklist = load_json(checklist_json_path, f"{case_id} checklist JSON")
    try:
        checklist_yaml = yaml.safe_load((case_dir / "checklist.yaml").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise QCFailure(f"{case_id} checklist YAML cannot be safely parsed: {exc}") from exc
    require(exact_json_equal(checklist_yaml, checklist),
            f"{case_id} checklist YAML/JSON semantic mismatch")
    require(checklist_json_path.read_bytes() == canonical_checklist_json(checklist),
            f"{case_id} checklist JSON bytes are not canonical upstream serialization")
    require((case_dir / "checklist.yaml").read_bytes() == canonical_checklist_yaml(checklist),
            f"{case_id} checklist YAML bytes are not canonical upstream serialization")
    errors = sorted(Draft202012Validator(schema).iter_errors(checklist), key=lambda item: list(item.absolute_path))
    require(not errors, f"{case_id} adapted schema failure: {errors[0].message if errors else ''}")
    require(tuple(checklist.keys()) == ("schema_version", "case_unit_id", "domain", "task_id", "native", "stronger"),
            f"{case_id} checklist top-level keys/order are non-exact")
    require(checklist.get("schema_version") == CHECKLIST_SCHEMA_VERSION
            and checklist.get("case_unit_id") == case_id
            and checklist.get("domain") == "androidworld"
            and checklist.get("task_id") == task_id,
            f"{case_id} checklist identity mismatch")
    support_qc = validate_supports(checklist, packet)
    api = load_json(case_dir / "api_response.json", f"{case_id} API response")
    codex = api.get("codex_cli")
    require(isinstance(codex, dict), f"{case_id} API response lacks Codex receipt")
    require(api.get("provider") == "codex_cli" and api.get("model") == runtime.get("model")
            and api.get("status") == "completed", f"{case_id} API provider/model/status mismatch")
    require(codex.get("auth_mode") == runtime.get("auth_mode")
            and is_exact_int(codex.get("returncode"))
            and codex.get("returncode") == 0
            and is_exact_int(codex.get("timeout_seconds"))
            and codex.get("timeout_seconds") == runtime.get("timeout_seconds")
            and codex.get("sandbox") is None
            and codex.get("permission_profile") == runtime.get("permission_profile")
            and codex.get("permission_profile_workspace_access") == "read"
            and codex.get("permission_profile_network_enabled") is False
            and codex.get("full_canonical_packet_in_readonly_workspace") is True
            and codex.get("full_canonical_packet_in_stdin") is False
            and codex.get("malformed_event_lines") == []
            and codex.get("stderr") == "",
            f"{case_id} Codex auth/isolation/clean-exit receipt mismatch")
    command_qc = validate_codex_command(
        codex.get("command"),
        runtime,
        cli_path,
        case_id,
        expected_codex_argv_sha256,
    )
    events = codex.get("events")
    require(isinstance(events, list) and all(isinstance(row, dict) for row in events),
            f"{case_id} Codex events are not an object list")
    receipt = codex.get("coverage_receipt")
    require(isinstance(receipt, dict), f"{case_id} API response lacks coverage receipt")
    ledger_qc = verify_event_ledger(
        events, requirements, operation_expectations, receipt, packet
    )
    try:
        normalized_usage = _validated_actual_usage(
            events, max_output_tokens=runtime.get("max_output_tokens")
        )
    except QCFailure as exc:
        raise QCFailure(f"{case_id} {exc}") from exc
    require(exact_json_equal(api.get("usage"), normalized_usage),
            f"{case_id} API token usage differs from event ledger")
    output_text = api.get("output_text")
    require(isinstance(output_text, str), f"{case_id} API output_text is absent")
    try:
        body = strip_null_fields(json.loads(output_text))
    except json.JSONDecodeError as exc:
        raise QCFailure(f"{case_id} API output_text is invalid JSON: {exc}") from exc
    require(isinstance(body, dict) and tuple(body.keys()) == ("native", "stronger"),
            f"{case_id} raw model body has non-exact keys")
    reconstructed = {
        "schema_version": CHECKLIST_SCHEMA_VERSION, "case_unit_id": case_id,
        "domain": "androidworld", "task_id": task_id, **body,
    }
    require(exact_json_equal(reconstructed, checklist),
            f"{case_id} checklist is not exact identity injection over raw model body")
    message_texts = [
        content.get("text")
        for item in api.get("output") or [] if isinstance(item, dict) and item.get("type") == "message"
        for content in item.get("content") or [] if isinstance(content, dict) and content.get("type") == "output_text"
    ]
    require(message_texts == [output_text], f"{case_id} API message/output_text provenance mismatch")
    final_messages = [
        event.get("item", {}).get("text") for event in events
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
    ]
    require(final_messages == [output_text], f"{case_id} final agent event differs from API model body")
    reasoning_chunks = []
    for item in api.get("output") or []:
        if isinstance(item, dict) and item.get("type") == "reasoning":
            for child in item.get("summary") or []:
                if isinstance(child, dict) and isinstance(child.get("text"), str) and child["text"].strip():
                    reasoning_chunks.append(child["text"].strip())
    expected_reasoning = "\n\n".join(reasoning_chunks).strip()
    expected_reasoning += "\n" if expected_reasoning else ""
    require((case_dir / "reasoning_summary.txt").read_text(encoding="utf-8") == expected_reasoning,
            f"{case_id} reasoning-summary sidecar differs from API response")
    require((case_dir / "stderr.log").read_bytes() == b"", f"{case_id} attempt stderr is non-empty")
    llm = load_json(case_dir / "llm_call.json", f"{case_id} LLM call record")
    metadata = llm.get("response_metadata")
    require(isinstance(metadata, dict), f"{case_id} LLM response metadata is absent")
    require(llm.get("schema_version") == "llm_call/v1"
            and llm.get("provider") == "codex_cli"
            and llm.get("model") == runtime.get("model")
            and llm.get("model_version") == runtime.get("model")
            and llm.get("api_key_env") == "CODEX_HOME"
            and llm.get("domain") == "androidworld"
            and llm.get("case_unit_id") == case_id
            and llm.get("task_id") == task_id
            and llm.get("phase") == "draft"
            and is_exact_int(llm.get("retry_index"))
            and llm.get("retry_index") == 0
            and type(llm.get("temperature")) is float
            and llm.get("temperature") == 0.0
            and is_exact_int(llm.get("max_tokens"))
            and llm.get("max_tokens") == runtime.get("max_output_tokens")
            and is_exact_int(llm.get("timeout_seconds"))
            and llm.get("timeout_seconds") == runtime.get("timeout_seconds")
            and exact_json_equal(
                llm.get("token_usage"), _token_usage(api.get("usage") or {})
            )
            and metadata.get("response_id") == api.get("id")
            and metadata.get("response_status") == "completed"
            and metadata.get("provider_model") == runtime.get("model")
            and metadata.get("reasoning_effort") == runtime.get("reasoning_effort")
            and metadata.get("auth_mode") == runtime.get("auth_mode")
            and metadata.get("max_output_tokens_enforced") is False,
            f"{case_id} LLM call provenance mismatch")
    raw_api = Path(str(metadata.get("raw_api_response_path") or ""))
    reasoning_path = Path(str(metadata.get("reasoning_summary_path") or ""))
    require(raw_api == case_dir / f"{prefix}api_response.json"
            and reasoning_path == case_dir / f"{prefix}reasoning_summary.txt",
            f"{case_id} LLM sidecar paths do not bind selected attempt")
    return {
        "status": "pass",
        "packet_sha256": packet.packet_sha256,
        "coverage_requirements_sha256": requirements["requirements_sha256"],
        "checklist_sha256": bindings["checklist.json"]["sha256"],
        "outputs_sha256": canonical_sha256(bindings),
        "support_qc": support_qc,
        "command_qc": command_qc,
        "ledger_qc": ledger_qc,
    }


@dataclass
class AuditCollector:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cases: list[dict[str, Any]] = field(default_factory=list)

    def error(self, scope: str, exc: BaseException | str) -> None:
        self.errors.append(f"{scope}: {exc}")


def _exact_direct_namespace(root: Path, expected_dirs: Sequence[str], expected_files: Sequence[str], label: str) -> None:
    require_directory(root, label)
    dirs, files = [], []
    for child in root.iterdir():
        require(not child.is_symlink(), f"symlink in {label}: {child.name}")
        if child.is_dir():
            dirs.append(child.name)
        elif child.is_file():
            files.append(child.name)
        else:
            raise QCFailure(f"non-file/non-directory in {label}: {child.name}")
    require(sorted(dirs) == sorted(expected_dirs), f"{label} case directory namespace mismatch")
    require(sorted(files) == sorted(expected_files), f"{label} global file namespace mismatch")


def _load_batch_results(path: Path) -> list[dict[str, Any]]:
    require_regular(path, "native batch results")
    rows = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise QCFailure(f"native batch result line {index} is invalid JSON") from exc
        require(isinstance(value, dict), f"native batch result line {index} is not an object")
        rows.append(value)
    return rows


def _validate_batch(
    raw_root: Path, order: Sequence[str], expectations: Mapping[str, Any], runtime: Mapping[str, Any]
) -> dict[str, Mapping[str, Any]]:
    summary = load_json(raw_root / "_batch_summary.json", "native batch summary")
    require(is_exact_int(summary.get("total_cases"))
            and summary.get("total_cases") == len(order)
            and is_exact_int(summary.get("completed_cases"))
            and summary.get("completed_cases") == len(order)
            and is_exact_int(summary.get("success_cases"))
            and summary.get("success_cases") == len(order)
            and is_exact_int(summary.get("failed_cases"))
            and summary.get("failed_cases") == 0
            and is_exact_int(summary.get("skipped_cases"))
            and summary.get("skipped_cases") == 0
            and summary.get("provider") == "codex"
            and summary.get("model") == runtime.get("model")
            and summary.get("reasoning_effort") == runtime.get("reasoning_effort")
            and summary.get("codex_sandbox") == runtime.get("native_runner_sandbox_label"),
            "native batch summary is not a clean exact success")
    results = _load_batch_results(raw_root / "_batch_results.jsonl")
    observed = [row.get("case_unit_dir") for row in results]
    require(len(results) == len(order) and len(set(observed)) == len(order) and set(observed) == set(order),
            "native batch results are not exact unique expected cases")
    by_case = {str(row["case_unit_dir"]): row for row in results}
    expected_attempt_index = expectations.get("expected_attempt_index")
    require(is_exact_int(expected_attempt_index) and expected_attempt_index >= 0,
            "expected attempt index is not an exact nonnegative integer")
    for case_id in order:
        row = by_case[case_id]
        require(row.get("status") == "success" and row.get("quality_warnings") == [],
                f"{case_id} native result is not warning-free success")
        attempts = row.get("attempts")
        require(isinstance(attempts, list) and len(attempts) == 1,
                f"{case_id} has other than one fresh attempt")
        attempt = attempts[0]
        require(isinstance(attempt, dict)
                and is_exact_int(attempt.get("attempt_index"))
                and attempt.get("attempt_index") == expected_attempt_index
                and is_exact_int(attempt.get("returncode"))
                and attempt.get("returncode") == 0
                and is_exact_int(attempt.get("max_output_tokens"))
                and attempt.get("max_output_tokens") == runtime.get("max_output_tokens")
                and is_exact_int(attempt.get("codex_timeout_seconds"))
                and attempt.get("codex_timeout_seconds") == runtime.get("timeout_seconds")
                and str(attempt.get("stderr_tail") or "") == "",
                f"{case_id} selected attempt provenance mismatch")
    return by_case


def run_audit(
    *, raw_output_root: Path, packet_root: Path, toolchain_root: Path, schema_path: Path,
    coverage_root: Path, case_order_path: Path, expectations_path: Path,
    expected_count: int = PRODUCTION_CASE_COUNT,
) -> dict[str, Any]:
    collector = AuditCollector()
    roots = {
        "raw_output_root": raw_output_root.resolve(), "packet_root": packet_root.resolve(),
        "toolchain_root": toolchain_root.resolve(), "coverage_root": coverage_root.resolve(),
    }
    control_report: dict[str, Any] = {}
    order: list[str] = []
    expectations: dict[str, Any] = {}
    schema: dict[str, Any] = {}
    binding_paths: dict[str, Path] = {}
    runtime: Mapping[str, Any] = {}
    case_expectations: dict[str, Mapping[str, Any]] = {}
    batch_by_case: dict[str, Mapping[str, Any]] = {}
    try:
        for name, root in roots.items():
            require_directory(root, name)
        require(len(set(roots.values())) == len(roots), "QC roots must be four distinct directories")
        order = load_case_order(case_order_path)
        require(len(order) == expected_count, f"expected exactly {expected_count} ordered cases, got {len(order)}")
        require(len(set(order)) == expected_count, "case order contains duplicates")
        expectations = load_json(expectations_path, "fresh QC expectations")
        require(expectations.get("schema_version") == EXPECTATIONS_SCHEMA,
                "fresh QC expectations schema mismatch")
        verify_self_hash(expectations, "expectations_sha256", "fresh QC expectations")
        require(is_exact_int(expectations.get("expected_case_count"))
                and expectations.get("expected_case_count") == expected_count
                and expectations.get("case_order_sha256") == canonical_sha256(order)
                and expectations.get("domain") == "androidworld",
                "expectations count/order/domain mismatch")
        cases = expectations.get("cases")
        require(isinstance(cases, list)
                and [row.get("case_unit_id") if isinstance(row, dict) else None for row in cases] == order,
                "expectation case sequence differs from frozen case order")
        case_expectations = {str(row["case_unit_id"]): row for row in cases}
        control_bindings = expectations.get("control_bindings")
        require(isinstance(control_bindings, dict)
                and set(control_bindings) == set(REQUIRED_CONTROL_BINDINGS),
                "control bindings must be exact CLI/config/prompt/schema/template set")
        tool_tree = tree_binding(toolchain_root)
        require(exact_json_equal(expectations.get("toolchain_tree"), {
            "file_count": tool_tree["file_count"], "files_sha256": tool_tree["files_sha256"]
        }), "frozen toolchain tree binding mismatch")
        for name in REQUIRED_CONTROL_BINDINGS:
            binding = control_bindings[name]
            require(isinstance(binding, dict), f"control binding {name} is not an object")
            binding_paths[name] = validate_bound_file(
                toolchain_root,
                binding,
                f"frozen control {name}",
                allow_absolute=(name in {"codex_cli", "config"}),
            )
        require(schema_path.resolve(strict=True) == binding_paths["schema"].resolve(strict=True),
                "--schema is not the exact frozen schema binding")
        schema = load_json(schema_path, "adapted checklist schema")
        Draft202012Validator.check_schema(schema)
        config = load_json(binding_paths["config"], "frozen draft config")
        if "config_sha256" in config:
            verify_self_hash(config, "config_sha256", "frozen draft config")
        carried_names = expectations.get("config_must_carry_binding_hashes")
        require(carried_names == ["codex_cli", "prompt", "schema", "template"],
                "config hash-carrier policy is not the exact four generation controls")
        for name in carried_names:
            require(name in control_bindings and _has_scalar(config, control_bindings[name]["sha256"]),
                    f"frozen config does not carry bound {name} hash")
        runtime_value = expectations.get("runtime")
        require(isinstance(runtime_value, dict), "expectations runtime is not an object")
        runtime = runtime_value
        required_runtime_keys = {
            "model", "reasoning_effort", "auth_mode", "permission_profile", "timeout_seconds",
            "max_output_tokens", "native_runner_sandbox_label", "disabled_features",
            "config_overrides", "required_flags",
        }
        require(required_runtime_keys.issubset(runtime), "runtime expectations omit required provenance fields")
        require(
            is_exact_int(runtime.get("timeout_seconds"))
            and runtime.get("timeout_seconds") > 0
            and is_exact_int(runtime.get("max_output_tokens"))
            and runtime.get("max_output_tokens") > 0,
            "runtime token/timeout limits are not exact positive integers",
        )
        require(runtime.get("model") == "gpt-5.6-sol" and runtime.get("reasoning_effort") == "xhigh"
                and runtime.get("auth_mode") == "codex_login"
                and runtime.get("native_runner_sandbox_label") == "read-only",
                "runtime model/reasoning/login mode is not production exact")
        expected_global_files = expectations.get("expected_global_files")
        expected_case_files = expectations.get("expected_case_files")
        coverage_global_files = expectations.get("coverage_global_files")
        require(isinstance(expected_global_files, list) and "_batch_results.jsonl" in expected_global_files
                and "_batch_summary.json" in expected_global_files,
                "expected global namespace omits native batch records")
        require(isinstance(expected_case_files, list), "expected case file namespace is absent")
        require(isinstance(coverage_global_files, list), "coverage global namespace is absent")
        _exact_direct_namespace(raw_output_root, order, expected_global_files, "fresh raw output root")
        _exact_direct_namespace(packet_root, order, [], "canonical packet root")
        _exact_direct_namespace(coverage_root, order, coverage_global_files, "frozen coverage root")
        batch_by_case = _validate_batch(raw_output_root, order, expectations, runtime)
        control_report = {
            "expectations_sha256": expectations["expectations_sha256"],
            "case_order_sha256": canonical_sha256(order),
            "toolchain_tree": {"file_count": tool_tree["file_count"], "files_sha256": tool_tree["files_sha256"]},
            "control_bindings": control_bindings,
            "schema_dialect": schema.get("$schema"),
        }
    except BaseException as exc:
        collector.error("global", exc)

    if not collector.errors:
        for case_id in order:
            try:
                expected = case_expectations[case_id]
                task_id = expected.get("task_id")
                require(isinstance(task_id, str) and task_id, f"{case_id} expectation lacks task_id")
                packet_relative = expected.get("packet_relative_path")
                coverage_relative = expected.get("coverage_relative_path")
                operation_expectations_relative = expected.get(
                    "reader_operation_expectations_relative_path"
                )
                require(packet_relative == f"{case_id}/case_packet.md",
                        f"{case_id} packet relative path is non-canonical")
                require(coverage_relative == f"{case_id}/model_input_coverage.json",
                        f"{case_id} coverage relative path is non-canonical")
                require(
                    operation_expectations_relative
                    == f"{case_id}/reader_operation_expectations.json",
                    f"{case_id} reader operation expectations path is non-canonical",
                )
                packet_path = packet_root / str(packet_relative)
                coverage_path = coverage_root / str(coverage_relative)
                operation_expectations_path = coverage_root / str(
                    operation_expectations_relative
                )
                require(expected.get("packet_sha256") == sha256_file(require_regular(packet_path, "packet")),
                        f"{case_id} packet hash differs from frozen expectation")
                require(expected.get("coverage_sha256") == sha256_file(require_regular(coverage_path, "coverage")),
                        f"{case_id} coverage file hash differs from frozen expectation")
                require(
                    expected.get("reader_operation_expectations_file_sha256")
                    == sha256_file(
                        require_regular(
                            operation_expectations_path,
                            "reader operation expectations",
                        )
                    ),
                    f"{case_id} reader operation expectations file hash differs from frozen expectation",
                )
                packet = parse_packet(packet_path, packet_root / case_id, case_id, task_id)
                requirements = load_json(coverage_path, f"{case_id} coverage requirements")
                operation_expectations = load_json(
                    operation_expectations_path,
                    f"{case_id} reader operation expectations",
                )
                require(requirements.get("case_packet_sha256") == packet.packet_sha256,
                        f"{case_id} coverage does not bind canonical packet hash")
                require(
                    expected.get("reader_operation_expectations_sha256")
                    == operation_expectations.get(
                        "reader_operation_expectations_sha256"
                    ),
                    f"{case_id} inner reader operation expectations hash differs from frozen expectation",
                )
                coverage_qc = validate_coverage(requirements, packet)
                row = batch_by_case[case_id]
                require(row.get("case_packet") == expected.get("recorded_packet_path"),
                        f"{case_id} native result packet path differs from frozen expectation")
                result = validate_case_outputs(
                    case_id=case_id, task_id=task_id, case_dir=raw_output_root / case_id,
                    packet=packet, requirements=requirements,
                    operation_expectations=operation_expectations,
                    schema=schema, runtime=runtime,
                    cli_path=binding_paths["codex_cli"],
                    expected_case_files=expectations["expected_case_files"],
                    expected_attempt_index=int(expectations["expected_attempt_index"]),
                    expected_codex_argv_sha256=str(
                        expected.get("codex_argv_sha256") or ""
                    ),
                )
                result["case_unit_id"] = case_id
                result["task_id"] = task_id
                result["coverage_qc"] = coverage_qc
                collector.cases.append(result)
            except BaseException as exc:
                collector.error(case_id, exc)
                collector.cases.append({"case_unit_id": case_id, "status": "fail", "error": str(exc)})

    passed = (
        not collector.errors
        and not collector.warnings
        and len(collector.cases) == expected_count
        and all(row.get("status") == "pass" for row in collector.cases)
    )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "status": "pass_116_of_116" if passed and expected_count == PRODUCTION_CASE_COUNT else (
            "pass" if passed else "fail_closed"
        ),
        "production_case_count_required": PRODUCTION_CASE_COUNT,
        "audited_case_count": len(collector.cases),
        "passed_case_count": sum(row.get("status") == "pass" for row in collector.cases),
        "case_order": order,
        "case_order_sha256": canonical_sha256(order) if order else None,
        "control": control_report,
        "cases": collector.cases,
        "errors": collector.errors,
        "warnings": collector.warnings,
        "deterministic_gate_passed": passed,
        "freeze_authorized": False,
        "freeze_requires": [
            "independent semantic review accepted 116/116",
            "explicit root per-case acceptance 116/116",
        ],
        "semantic_boundaries_not_claimed": [
            "natural-language checklist claims faithfully paraphrase all decisive source semantics",
            "each cited resolving selector substantively supports the precise prose clause rather than merely existing",
            "stronger conditions are complete, necessary, measurable, and neither missing nor overbroad",
            "retained post-run artifacts named by the draft will actually be available in every execution",
        ],
    }
    report["report_sha256"] = canonical_sha256(report)
    return report


def write_create_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise QCFailure(f"create-once QC report already exists: {path}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-output-root", type=Path, required=True)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--toolchain-root", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--coverage-root", type=Path, required=True)
    parser.add_argument("--case-order", type=Path, required=True)
    parser.add_argument("--expectations", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_audit(
        raw_output_root=args.raw_output_root.resolve(strict=True),
        packet_root=args.packet_root.resolve(strict=True),
        toolchain_root=args.toolchain_root.resolve(strict=True),
        schema_path=args.schema.resolve(strict=True),
        coverage_root=args.coverage_root.resolve(strict=True),
        case_order_path=args.case_order.resolve(strict=True),
        expectations_path=args.expectations.resolve(strict=True),
    )
    write_create_once(args.report, report)
    print(json.dumps({
        "status": report["status"], "passed_case_count": report["passed_case_count"],
        "errors": len(report["errors"]), "warnings": len(report["warnings"]),
        "report_sha256": report["report_sha256"], "freeze_authorized": False,
    }, ensure_ascii=False, indent=2))
    return 0 if report["deterministic_gate_passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QCFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
