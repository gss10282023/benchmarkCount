#!/usr/bin/env python3
"""Fail-closed automatic QC for candidate116 full-packet wave_003 drafts.

This program deliberately stops short of semantic acceptance.  A per-case
``status=passed`` means only that the frozen-input, provenance, schema,
source-inventory pointer, and deterministic policy checks implemented here
passed.  It is not
an independent human judgment that the checklist correctly captures every
task/evaluator nuance, and it is never sufficient on its own to promote or
freeze canonical drafts/contracts.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
DEFAULT_PRELOCK = (
    WORK_ROOT
    / "draft_generation"
    / "freeze"
    / "androidworld_candidate116_codex_cli_draft_prelock_v3.json"
)
DEFAULT_WAVE_ROOT = WORK_ROOT / "draft_generation" / "waves" / "wave_003"
DEFAULT_REPORT_ROOT = WORK_ROOT / "draft_generation" / "automatic_qc_v3"
EXPECTED_PACKET_ROOT = WORK_ROOT / "case_packets" / "androidworld"

EXPECTED_CASE_COUNT = 116
EXPECTED_MODEL = "gpt-5.6-sol"
EXPECTED_REASONING_EFFORT = "xhigh"
EXPECTED_SANDBOX = "read-only"
EXPECTED_AUTH_MODE = "codex_login"
EXPECTED_PARALLELISM = 6

CASE_REPORT_SCHEMA_VERSION = "androidworld_checklist_automatic_qc/v2"
SUMMARY_SCHEMA_VERSION = "androidworld_checklist_automatic_qc_summary/v2"
PREFLIGHT_SCHEMA_VERSION = "androidworld_checklist_automatic_qc_preflight/v1"

REQUIRED_CANONICAL_SIDECARS = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stdout.log",
    "stderr.log",
)

CHECK_NAMES = (
    "identity",
    "schema",
    "guardrails",
    "support_paths",
    "llm_provenance",
    "frozen_packet_input",
    "required_sidecars",
    "yaml_json_consistency",
    "batch_result",
    "sfu_done_gate",
    "no_absolute_paths",
    "no_hidden_oracle",
    "no_source_as_run_evidence",
)

HIDDEN_ORACLE_RE = re.compile(
    r"(?ix)\b("
    r"hidden\s+(?:state|reasoning|intent|memory|oracle)|"
    r"internal\s+(?:state|reasoning|intent|memory)|"
    r"private\s+(?:state|reasoning|intent|memory)|"
    r"latent\s+(?:state|reasoning|intent|memory)|"
    r"unobserved\s+(?:state|reasoning|intent|memory)|"
    r"counterfactual|ground[- ]truth|scratchpad|"
    r"gold(?:en)?\s+(?:answer|trajectory|action|tool\s*call|label)|"
    r"reference\s+(?:trajectory|action|tool\s*call)|"
    r"(?:another|second|extra)\s+(?:judge|model)"
    r")\b"
)
SOURCE_AS_EVIDENCE_RE = re.compile(
    r"(?ix)\b(?:source\s+(?:code|file|material)|implementation|"
    r"task_metadata(?:\.json)?|case[_ -]?packet|compact[_ -]?packet)\b"
    r"[^.\n]{0,100}\b(?:proves?|confirms?|demonstrates?|shows?|establishes?|"
    r"is\s+(?:the\s+)?(?:run\s+)?evidence)\b"
)
SOURCE_ARTIFACT_RE = re.compile(
    r"(?ix)(?:\.py\b|\.textproto\b|task_metadata|case[_ -]?packet|"
    r"source[_ -]?(?:code|file|material)|evaluator[_ -]?implementation|"
    r"schema[_ -]?(?:source|file))"
)
DONE_RE = re.compile(r"(?i)\b(?:interaction_results\s*\.\s*)?done\b")
THRESHOLD_RE = re.compile(
    r"(?ix)(?:"
    r">\s*0?\.5|"
    r"(?:greater|higher|more)\s+than\s+0?\.5|"
    r"above\s+0?\.5|"
    r"(?:at\s+or\s+)?below\s+0?\.5|"
    r"(?:at\s+or\s+)?under\s+0?\.5|"
    r"(?:<=|<)\s*0?\.5|"
    r"(?:exceeds?|exceeded|exceeding)\s+0?\.5|"
    r"(?:does\s+not|doesn't|not)\s+(?:exceed|exceeds)\s+0?\.5|"
    r"0?\.5\s+(?:threshold|cutoff)"
    r")"
)
RAW_SCORE_RE = re.compile(
    r"(?ix)(?:\b(?:is_successful|raw\s+(?:score|result)|task(?:_successful)?\s+score|"
    r"native\s+(?:success|failure|evaluator)|"
    r"evaluator|accepts?|rejects?|passes?|fails?)\b|"
    r"\bvalidate_[A-Za-z0-9_]+\b|\.validate_[A-Za-z0-9_]+\b)"
)
MISSING_EVIDENCE_RE = re.compile(
    r"(?ix)(?:\b(?:missing|omits?|omitted|unavailable|absent|lacks?|incomplete|"
    r"insufficient|corrupt(?:ed)?|unreadable|unbound|cannot\s+be\s+bound|"
    r"does\s+not\s+(?:retain|establish|show|record|link|bind)|not\s+retained|"
    r"ambiguous|conflicts?|inconsistent)\b|"
    r"\bcannot\s+be\s+(?:determined|established|reconstructed)\b|"
    r"\bprevent(?:s|ing|ed)?\s+(?:determination|reconstruction)\b)"
)
ORDINARY_FAILURE_IN_UNDECIDED_RE = re.compile(
    r"(?ix)(?:"
    r"\bdone\s+(?:is|=|was)\s+false\b|"
    r"\b(?:score|agent_successful)\s*(?:<=|<|=)\s*0?\.5\b|"
    r"\bis_successful\s+(?:returns?|returned)\s+(?:false|0|failure)\b|"
    r"\bevaluator\s+(?:returns?|returned|reports?|reported)\s+(?:failure|false|0)\b"
    r")"
)
ABSOLUTE_WINDOWS_RE = re.compile(r"^[A-Za-z]:[\\/]")
LINE_SPAN_RE = re.compile(
    r"^(?:lines?\s*)?[Ll]?(\d+)(?:\s*(?:-|:)\s*[Ll]?(\d+))?$",
    re.IGNORECASE,
)
JSON_PATH_TOKEN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)(?:\[(\d+)\])?")


class QcFatalError(RuntimeError):
    """Raised when global inputs cannot be safely interpreted."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave-root", type=Path, default=DEFAULT_WAVE_ROOT)
    parser.add_argument("--prelock", type=Path, default=DEFAULT_PRELOCK)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument(
        "--skip-live-login-check",
        action="store_true",
        help=(
            "Do not query the current Codex login. Historical per-call Codex-login "
            "provenance remains mandatory."
        ),
    )
    parser.add_argument(
        "--diagnostic-exit-zero",
        action="store_true",
        help="Write a fail/partial report but return zero; never changes reported status.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help=(
            "Validate the v3 prelock/config/snapshot and all 116 full packet inputs, "
            "write only preflight.json, and do not inspect or write the raw wave."
        ),
    )
    return parser.parse_args()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QcFatalError(f"cannot load JSON {path}: {exc}") from exc


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise QcFatalError(f"cannot load YAML {path}: {exc}") from exc


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def resolve_repo_path(raw: str) -> Path | None:
    path = Path(raw)
    if path.is_absolute() or ABSOLUTE_WINDOWS_RE.match(raw) or raw.startswith("~"):
        return None
    candidate = (REPO_ROOT / path).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError:
        return None
    return candidate


def issue(
    code: str,
    message: str,
    *,
    check: str,
    field: str | None = None,
    detail: Any = None,
) -> dict[str, Any]:
    # Internally normalize the v2-era call-site name so reports expose the
    # accurate v3 full-packet gate without changing the number of gates.
    if check == "frozen_compact_input":
        check = "frozen_packet_input"
    payload: dict[str, Any] = {
        "severity": "error",
        "code": code,
        "check": check,
        "message": message,
    }
    if field is not None:
        payload["field"] = field
    if detail is not None:
        payload["detail"] = detail
    return payload


def warning(
    code: str,
    message: str,
    *,
    check: str,
    field: str | None = None,
    detail: Any = None,
) -> dict[str, Any]:
    payload = issue(code, message, check=check, field=field, detail=detail)
    payload["severity"] = "warning"
    return payload


def iter_strings(value: Any, field: str = "<root>") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from iter_strings(child, f"{field}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_strings(child, f"{field}[{index}]")
    elif isinstance(value, str):
        yield field, value


def iter_supports(value: Any, field: str = "<root>") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_field = f"{field}.{key}"
            if key == "support" and isinstance(child, list):
                for index, pointer in enumerate(child):
                    if isinstance(pointer, str):
                        yield f"{child_field}[{index}]", pointer
            yield from iter_supports(child, child_field)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_supports(child, f"{field}[{index}]")


def parse_full_case_packet(text: str) -> dict[str, Any]:
    """Parse one rendered full packet without materializing source files.

    Source Inventory paths are archive names inside the packet.  They are not
    expected to exist as paths at the repository root; their authoritative
    bytes are the fenced blocks under ``## Packet Source Files``.
    """

    lines = text.splitlines(keepends=True)
    stripped = [line.rstrip("\r\n") for line in lines]
    try:
        metadata_start = stripped.index("## Case Metadata")
        inventory_start = stripped.index("## Source Inventory")
        sources_start = stripped.index("## Packet Source Files")
    except ValueError as exc:
        raise QcFatalError(f"full packet is missing a required top-level section: {exc}") from exc
    if not (metadata_start < inventory_start < sources_start):
        raise QcFatalError("full packet top-level sections are out of order")

    identity: dict[str, str] = {}
    for line in stripped[metadata_start + 1 : inventory_start]:
        match = re.fullmatch(r"- ([a-z_]+): `([^`]*)`", line.strip())
        if match:
            identity[match.group(1)] = match.group(2)

    inventory: list[str] = []
    for line in stripped[inventory_start + 1 : sources_start]:
        match = re.fullmatch(r"- `([^`]+)`", line.strip())
        if match:
            inventory.append(match.group(1).replace("\\", "/"))

    section_starts: list[tuple[int, str]] = []
    for index in range(sources_start + 1, len(stripped)):
        match = re.fullmatch(r"### `([^`]+)`", stripped[index])
        if match:
            section_starts.append((index, match.group(1).replace("\\", "/")))
    sections: dict[str, dict[str, Any]] = {}
    duplicate_sections: list[str] = []
    for position, (heading_index, archive_path) in enumerate(section_starts):
        next_heading = (
            section_starts[position + 1][0]
            if position + 1 < len(section_starts)
            else len(lines)
        )
        fence_start: int | None = None
        language = ""
        for index in range(heading_index + 1, next_heading):
            match = re.fullmatch(r"```([^`]*)", stripped[index])
            if match:
                fence_start = index
                language = match.group(1).strip()
                break
        if fence_start is None:
            raise QcFatalError(f"packet source section has no fenced body: {archive_path}")
        fence_end: int | None = None
        for index in range(fence_start + 1, next_heading):
            if stripped[index] == "```":
                fence_end = index
                break
        if fence_end is None:
            raise QcFatalError(f"packet source section has no closing fence: {archive_path}")
        content = "".join(lines[fence_start + 1 : fence_end])
        if archive_path in sections:
            duplicate_sections.append(archive_path)
            continue
        sections[archive_path] = {
            "archive_path": archive_path,
            "language": language,
            "content": content,
            "heading_packet_line": heading_index + 1,
            "content_packet_line_start": fence_start + 2,
            "source_line_count": len(content.splitlines()),
        }

    return {
        "identity": identity,
        "inventory": inventory,
        "sections": sections,
        "duplicate_sections": duplicate_sections,
        "packet_line_count": len(lines),
    }


def parse_embedded_json(section: dict[str, Any], archive_path: str) -> Any:
    try:
        return json.loads(str(section.get("content") or ""))
    except json.JSONDecodeError as exc:
        raise QcFatalError(f"embedded JSON is invalid for {archive_path}: {exc}") from exc


def validate_full_packet_structure(
    *,
    packet: dict[str, Any],
    packet_record: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate packet identity, complete inventory, closure, and embedded bytes."""

    problems: list[dict[str, Any]] = []
    case_id = str(packet_record.get("case_unit_id") or "")
    rank = packet_record.get("selection_rank")
    identity = packet.get("identity") or {}
    if identity != {
        "domain": "androidworld",
        "case_unit_id": case_id,
        "task_id": case_id,
    }:
        problems.append(
            issue(
                "full_packet_identity_mismatch",
                "full case packet metadata differs from the frozen case identity",
                check="identity",
                detail={"case_unit_id": case_id, "selection_rank": rank, "identity": identity},
            )
        )

    inventory = packet.get("inventory") or []
    sections = packet.get("sections") or {}
    if not inventory:
        problems.append(
            issue(
                "full_packet_source_inventory_empty",
                "full case packet has no Source Inventory entries",
                check="frozen_compact_input",
                detail=case_id,
            )
        )
    if len(inventory) != len(set(inventory)):
        problems.append(
            issue(
                "full_packet_source_inventory_duplicate",
                "full case packet Source Inventory contains duplicate paths",
                check="frozen_compact_input",
                detail=case_id,
            )
        )
    if packet.get("duplicate_sections"):
        problems.append(
            issue(
                "full_packet_duplicate_source_sections",
                "full case packet contains duplicate Packet Source Files headings",
                check="frozen_compact_input",
                detail=packet.get("duplicate_sections"),
            )
        )
    inventory_set = set(inventory)
    section_set = set(sections)
    if inventory_set != section_set:
        problems.append(
            issue(
                "full_packet_inventory_section_mismatch",
                "every Source Inventory path must have exactly one embedded source section and vice versa",
                check="frozen_compact_input",
                detail={
                    "case_unit_id": case_id,
                    "missing_sections": sorted(inventory_set - section_set),
                    "unlisted_sections": sorted(section_set - inventory_set),
                },
            )
        )
    empty_sections = sorted(
        path for path, section in sections.items() if not str(section.get("content") or "")
    )
    if empty_sections:
        problems.append(
            issue(
                "full_packet_empty_source_sections",
                "full case packet contains empty embedded source files",
                check="frozen_compact_input",
                detail={"case_unit_id": case_id, "paths": empty_sections},
            )
        )

    required_derived = {
        "derived/selected_task_source.json",
        "derived/source_closure.json",
        "derived/canonical_task_semantics.json",
    }
    missing_derived = sorted(required_derived - section_set)
    if missing_derived:
        problems.append(
            issue(
                "full_packet_required_derived_sources_missing",
                "full packet is missing required derived semantic/closure sources",
                check="frozen_compact_input",
                detail={"case_unit_id": case_id, "paths": missing_derived},
            )
        )

    closure: dict[str, Any] = {}
    closure_section = sections.get("derived/source_closure.json")
    if closure_section is not None:
        try:
            loaded = parse_embedded_json(closure_section, "derived/source_closure.json")
            if isinstance(loaded, dict):
                closure = loaded
            else:
                raise QcFatalError("embedded source closure is not an object")
        except QcFatalError as exc:
            problems.append(
                issue(
                    "full_packet_source_closure_invalid",
                    str(exc),
                    check="frozen_compact_input",
                    detail=case_id,
                )
            )
    if closure:
        if (
            closure.get("case_unit_id") != case_id
            or closure.get("task_id") != case_id
            or closure.get("closure_sha256") != packet_record.get("source_closure_sha256")
        ):
            problems.append(
                issue(
                    "full_packet_source_closure_binding_mismatch",
                    "embedded source closure identity/hash differs from the v3 packet input binding",
                    check="frozen_compact_input",
                    detail={
                        "case_unit_id": case_id,
                        "embedded_case_unit_id": closure.get("case_unit_id"),
                        "embedded_task_id": closure.get("task_id"),
                        "embedded_closure_sha256": closure.get("closure_sha256"),
                        "prelocked_closure_sha256": packet_record.get("source_closure_sha256"),
                    },
                )
            )
        closure_files = closure.get("files") or []
        if (
            not isinstance(closure_files, list)
            or closure.get("closure_file_count") != len(closure_files)
        ):
            problems.append(
                issue(
                    "full_packet_source_closure_count_mismatch",
                    "embedded source closure file count is invalid",
                    check="frozen_compact_input",
                    detail=case_id,
                )
            )
            closure_files = []
        closure_paths: set[str] = set()
        for binding in closure_files:
            if not isinstance(binding, dict):
                problems.append(
                    issue(
                        "full_packet_source_closure_record_invalid",
                        "source closure file binding is not an object",
                        check="frozen_compact_input",
                        detail=case_id,
                    )
                )
                continue
            archive_path = str(binding.get("archive_path") or "")
            closure_paths.add(archive_path)
            section = sections.get(archive_path)
            if section is None:
                continue
            observed = hashlib.sha256(str(section.get("content") or "").encode("utf-8")).hexdigest()
            if observed != binding.get("sha256"):
                problems.append(
                    issue(
                        "full_packet_embedded_source_hash_mismatch",
                        "embedded source bytes do not match the source closure binding",
                        check="frozen_compact_input",
                        detail={
                            "case_unit_id": case_id,
                            "path": archive_path,
                            "expected": binding.get("sha256"),
                            "observed": observed,
                        },
                    )
                )
        expected_inventory = closure_paths | required_derived
        if closure_paths and inventory_set != expected_inventory:
            problems.append(
                issue(
                    "full_packet_inventory_not_complete_closure",
                    "Source Inventory is not exactly the complete closure plus three derived records",
                    check="frozen_compact_input",
                    detail={
                        "case_unit_id": case_id,
                        "missing": sorted(expected_inventory - inventory_set),
                        "extra": sorted(inventory_set - expected_inventory),
                    },
                )
            )
        if closure.get("unresolved_internal_imports") not in ([], None):
            problems.append(
                issue(
                    "full_packet_unresolved_internal_imports",
                    "source closure retains unresolved internal AndroidWorld imports",
                    check="frozen_compact_input",
                    detail={
                        "case_unit_id": case_id,
                        "unresolved": closure.get("unresolved_internal_imports"),
                    },
                )
            )

    for archive_path in (
        "derived/selected_task_source.json",
        "derived/canonical_task_semantics.json",
    ):
        section = sections.get(archive_path)
        if section is None:
            continue
        try:
            value = parse_embedded_json(section, archive_path)
        except QcFatalError as exc:
            problems.append(
                issue(
                    "full_packet_derived_json_invalid",
                    str(exc),
                    check="frozen_compact_input",
                    detail=case_id,
                )
            )
            continue
        if not isinstance(value, dict) or value.get("case_unit_id") != case_id:
            problems.append(
                issue(
                    "full_packet_derived_identity_mismatch",
                    "derived semantic source does not bind the frozen case identity",
                    check="identity",
                    detail={"case_unit_id": case_id, "path": archive_path},
                )
            )

    diagnostic = {
        "case_unit_id": case_id,
        "selection_rank": rank,
        "source_inventory_count": len(inventory),
        "embedded_source_section_count": len(sections),
        "source_closure_file_count": closure.get("closure_file_count"),
        "source_closure_sha256": closure.get("closure_sha256"),
    }
    return problems, diagnostic


def json_path_lookup(value: Any, raw_path: str) -> tuple[bool, Any]:
    current = value
    if not raw_path:
        return False, None
    for raw_token in raw_path.split("."):
        match = JSON_PATH_TOKEN_RE.fullmatch(raw_token)
        if not match:
            return False, None
        key, index = match.groups()
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
        if index is not None:
            if not isinstance(current, list) or int(index) >= len(current):
                return False, None
            current = current[int(index)]
    return True, current


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def node_children(node: ast.AST) -> list[ast.AST]:
    return list(getattr(node, "body", []))


def ast_named_line_span(node: ast.AST, parts: list[str]) -> tuple[int, int] | None:
    if not parts:
        return None
    first, remaining = parts[0], parts[1:]
    for child in node_children(node):
        name = getattr(child, "name", None)
        if name == first and isinstance(
            child,
            (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            if not remaining:
                return child.lineno, getattr(child, "end_lineno", child.lineno)
            found = ast_named_line_span(child, remaining)
            if found:
                return found

        if isinstance(child, (ast.Assign, ast.AnnAssign)):
            targets = child.targets if isinstance(child, ast.Assign) else [child.target]
            target_names = [target.id for target in targets if isinstance(target, ast.Name)]
            if first in target_names and not remaining:
                return child.lineno, getattr(child, "end_lineno", child.lineno)
    return None


def resolve_python_symbol_text(
    source_text: str,
    location: str,
    *,
    filename: str,
) -> tuple[int, int] | None:
    try:
        tree = ast.parse(source_text, filename=filename)
    except (SyntaxError, UnicodeDecodeError):
        return None
    cleaned = location.strip().strip("`")
    if cleaned.endswith("()"):
        cleaned = cleaned[:-2]
    raw_parts = [part for part in cleaned.split(".") if part]
    candidates = [raw_parts[index:] for index in range(len(raw_parts))]
    seen: set[tuple[str, ...]] = set()
    for parts in candidates:
        key = tuple(parts)
        if not parts or key in seen:
            continue
        seen.add(key)
        found = ast_named_line_span(tree, parts)
        if found:
            return found
    return None


def resolve_text_symbol_text(
    source_text: str,
    location: str,
) -> tuple[tuple[int, int] | None, str | None]:
    lines = source_text.splitlines()
    cleaned = location.strip().strip("`")
    needles = [cleaned]
    if "." in cleaned:
        needles.append(cleaned.split(".")[-1])
    for needle in needles:
        if not needle:
            continue
        matches = [index for index, text in enumerate(lines, start=1) if needle in text]
        if matches:
            return (matches[0], matches[-1]), needle
    return None, None


def resolve_pointer(
    *,
    pointer: str,
    packet_path: Path,
    packet_text: str,
    packet: dict[str, Any],
    allowed_source_paths: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    problems: list[dict[str, Any]] = []
    record: dict[str, Any] = {"pointer": pointer, "resolved": False}
    normalized = pointer.strip().replace("\\", "/")
    path_part, separator, location = normalized.partition("::")
    if separator != "::" or not path_part or not location:
        problems.append(
            issue(
                "support_pointer_format",
                "support pointer must be <relative_path>::<location>",
                check="support_paths",
                detail=pointer,
            )
        )
        return record, problems

    if path_part not in allowed_source_paths:
        problems.append(
            issue(
                "support_pointer_not_allowed_by_frozen_guardrail",
                "support pointer path is not in the exact allowlist derived by the prelocked guardrail",
                check="support_paths",
                detail={
                    "pointer": pointer,
                    "allowed_source_paths": sorted(allowed_source_paths),
                },
            )
        )

    if (
        path_part.startswith("/")
        or path_part.startswith("~")
        or ABSOLUTE_WINDOWS_RE.match(path_part)
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", path_part)
    ):
        problems.append(
            issue(
                "support_pointer_absolute_or_url",
                "support pointer path must be repository-relative, not absolute/URL",
                check="support_paths",
                detail=pointer,
            )
        )
        return record, problems

    alias_used = path_part == "case_packet.md"
    if alias_used:
        source_text = packet_text
        source_line_count = len(packet_text.splitlines())
        embedded_packet_line_start = 1
        language = "markdown"
    else:
        section = (packet.get("sections") or {}).get(path_part)
        if not isinstance(section, dict):
            problems.append(
                issue(
                    "support_pointer_missing_inventory_section",
                    "support pointer path has no embedded source section in the frozen full packet",
                    check="support_paths",
                    detail=pointer,
                )
            )
            return record, problems
        source_text = str(section.get("content") or "")
        source_line_count = int(section.get("source_line_count") or 0)
        embedded_packet_line_start = int(section.get("content_packet_line_start") or 0)
        language = str(section.get("language") or "")
    record["packet_path"] = repo_relative(packet_path)
    record["archive_path"] = path_part
    record["location"] = location
    record["case_packet_alias"] = alias_used
    record["embedded_source"] = not alias_used
    record["source_language"] = language
    record["source_line_count"] = source_line_count

    span_match = LINE_SPAN_RE.fullmatch(location.strip())
    span: tuple[int, int] | None = None
    location_kind = "symbol"
    if span_match:
        start = int(span_match.group(1))
        end = int(span_match.group(2) or start)
        location_kind = "line_span"
        if start < 1 or end < start or end > source_line_count:
            problems.append(
                issue(
                    "support_pointer_bad_line_span",
                    "support pointer line span is outside the embedded source file",
                    check="support_paths",
                    detail={
                        "pointer": pointer,
                        "start": start,
                        "end": end,
                        "file_lines": source_line_count,
                    },
                )
            )
        else:
            span = (start, end)
    elif alias_used and location.startswith("source_context"):
        location_kind = "rejected_compact_json_path"
        problems.append(
            issue(
                "support_pointer_legacy_compact_json_path",
                "wave_003 support must cite the full packet/source inventory, not a wave_002 compact source_context path",
                check="support_paths",
                detail=pointer,
            )
        )
    elif not alias_used and path_part.endswith(".py"):
        span = resolve_python_symbol_text(source_text, location, filename=path_part)
        if span is None:
            problems.append(
                issue(
                    "support_pointer_unresolved_python_symbol",
                    "Python support symbol does not exist in the cited embedded source file",
                    check="support_paths",
                    detail=pointer,
                )
            )
    elif not alias_used and path_part.endswith(".json") and location.startswith("$."):
        location_kind = "json_path"
        try:
            json_value = json.loads(source_text)
        except json.JSONDecodeError:
            json_value = None
        found, _ = json_path_lookup(json_value, location[2:])
        if not found:
            problems.append(
                issue(
                    "support_pointer_unresolved_json_path",
                    "JSON support path does not exist in the cited embedded source file",
                    check="support_paths",
                    detail=pointer,
                )
            )
    else:
        span, matched_text = resolve_text_symbol_text(source_text, location)
        record["matched_text"] = matched_text
        if span is None:
            problems.append(
                issue(
                    "support_pointer_unresolved_location",
                    "support symbol/location does not occur in the cited frozen packet source",
                    check="support_paths",
                    detail=pointer,
                )
            )

    record["location_kind"] = location_kind
    if span is not None:
        record["resolved_line_start"] = span[0]
        record["resolved_line_end"] = span[1]
        record["embedded_packet_line_start"] = embedded_packet_line_start + span[0] - 1
        record["embedded_packet_line_end"] = embedded_packet_line_start + span[1] - 1
    record["resolved"] = not problems
    return record, problems


def check_sfu_done_gate(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    native = checklist.get("native", {}) if isinstance(checklist, dict) else {}
    benchmark = str((native.get("benchmark_success") or {}).get("text") or "")
    success_items = native.get("success_if") or []
    fail_items = native.get("fail_if") or []
    undecided_items = native.get("undecided_if") or []
    success = "\n".join(str(item.get("text") or "") for item in success_items if isinstance(item, dict))
    failure = "\n".join(str(item.get("text") or "") for item in fail_items if isinstance(item, dict))
    undecided = "\n".join(str(item.get("text") or "") for item in undecided_items if isinstance(item, dict))

    required_patterns = (
        (benchmark, DONE_RE, "benchmark_missing_done_gate", "native.benchmark_success"),
        (benchmark, THRESHOLD_RE, "benchmark_missing_threshold", "native.benchmark_success"),
        (benchmark, RAW_SCORE_RE, "benchmark_missing_raw_evaluator", "native.benchmark_success"),
        (success, DONE_RE, "success_missing_done_gate", "native.success_if"),
        (success, THRESHOLD_RE, "success_missing_threshold", "native.success_if"),
        (success, RAW_SCORE_RE, "success_missing_raw_evaluator", "native.success_if"),
        (failure, DONE_RE, "failure_missing_done_gate", "native.fail_if"),
        (failure, THRESHOLD_RE, "failure_missing_threshold", "native.fail_if"),
        (failure, RAW_SCORE_RE, "failure_missing_raw_evaluator", "native.fail_if"),
        (undecided, MISSING_EVIDENCE_RE, "undecided_not_evidence_gap", "native.undecided_if"),
    )
    for text, pattern, code, field in required_patterns:
        if not pattern.search(text):
            problems.append(
                issue(
                    code,
                    "S/F/U rule set does not explicitly encode the required native evaluator/done gate semantics",
                    check="sfu_done_gate",
                    field=field,
                )
            )
    if ORDINARY_FAILURE_IN_UNDECIDED_RE.search(undecided):
        problems.append(
            issue(
                "ordinary_failure_marked_undecided",
                "undecided_if appears to move an ordinary benchmark-counted failure into undecided",
                check="sfu_done_gate",
                field="native.undecided_if",
            )
        )
    return problems


def checklist_policy_checks(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    for field, text in iter_strings(checklist):
        if field.endswith(".support") or ".support[" in field:
            continue
        stripped = text.strip()
        if (
            stripped.startswith("/")
            or stripped.startswith("~ /")
            or stripped.startswith("~/")
            or ABSOLUTE_WINDOWS_RE.match(stripped)
            or "file://" in stripped
        ):
            problems.append(
                issue(
                    "absolute_path_in_checklist",
                    "checklist contains an absolute/local path",
                    check="no_absolute_paths",
                    field=field,
                    detail=text,
                )
            )
        if HIDDEN_ORACLE_RE.search(text):
            problems.append(
                issue(
                    "hidden_oracle_dependency",
                    "checklist text refers to hidden/non-post-run oracle material",
                    check="no_hidden_oracle",
                    field=field,
                    detail=text,
                )
            )
        if SOURCE_AS_EVIDENCE_RE.search(text):
            problems.append(
                issue(
                    "source_treated_as_run_evidence",
                    "source material is being treated as evidence of what happened in a run",
                    check="no_source_as_run_evidence",
                    field=field,
                    detail=text,
                )
            )

    native = checklist.get("native", {}) if isinstance(checklist, dict) else {}
    artifacts: list[tuple[str, dict[str, Any]]] = []
    for index, artifact in enumerate(native.get("decisive_artifacts") or []):
        if isinstance(artifact, dict):
            artifacts.append((f"native.decisive_artifacts[{index}]", artifact))
    for condition_index, condition in enumerate(
        (checklist.get("stronger", {}) or {}).get("additional_conditions") or []
    ):
        if not isinstance(condition, dict):
            continue
        for artifact_index, artifact in enumerate(condition.get("decisive_artifacts") or []):
            if isinstance(artifact, dict):
                artifacts.append(
                    (
                        f"stronger.additional_conditions[{condition_index}]."
                        f"decisive_artifacts[{artifact_index}]",
                        artifact,
                    )
                )
    for field, artifact in artifacts:
        name = str(artifact.get("artifact") or "")
        question = str(artifact.get("question") or "")
        if SOURCE_ARTIFACT_RE.search(name):
            problems.append(
                issue(
                    "source_named_as_decisive_run_artifact",
                    "decisive artifact names source/packet/schema material rather than retained run output",
                    check="no_source_as_run_evidence",
                    field=f"{field}.artifact",
                    detail=name,
                )
            )
        if SOURCE_AS_EVIDENCE_RE.search(question):
            problems.append(
                issue(
                    "source_question_used_as_run_evidence",
                    "decisive question asks source material to establish a run outcome",
                    check="no_source_as_run_evidence",
                    field=f"{field}.question",
                    detail=question,
                )
            )
    return problems


def load_guardrail_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("candidate116_prelocked_guardrails", path)
    if spec is None or spec.loader is None:
        raise QcFatalError(f"cannot import guardrails from {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def normalized_role(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def manifest_named_bindings(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    raw = manifest.get("tool_bindings")
    if isinstance(raw, dict):
        return [
            (str(name), dict(binding))
            for name, binding in raw.items()
            if isinstance(binding, dict)
        ]
    files = manifest.get("files") or raw or []
    if not isinstance(files, list):
        return []
    result: list[tuple[str, dict[str, Any]]] = []
    for index, binding in enumerate(files):
        if not isinstance(binding, dict):
            continue
        name = str(
            binding.get("logical_name")
            or binding.get("name")
            or binding.get("role")
            or Path(str(binding.get("path") or "")).name
            or index
        )
        result.append((name, dict(binding)))
    return result


def command_path_pair_matches(command: list[Any], flag: str, expected: Path) -> bool:
    for index in range(len(command) - 1):
        if command[index] != flag:
            continue
        raw = str(command[index + 1])
        candidate = Path(raw)
        resolved = (candidate if candidate.is_absolute() else REPO_ROOT / candidate).resolve()
        if resolved == expected.resolve():
            return True
    return False


def validate_v3_snapshot_toolchain(
    *,
    prelock: dict[str, Any],
    config: dict[str, Any],
    problems: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify the immutable full-packet wave_003 snapshot and native runner wiring."""

    binding = (
        prelock.get("toolchain_snapshot")
        or prelock.get("toolchain_snapshot_manifest")
        or prelock.get("snapshot_toolchain")
    )
    if not isinstance(binding, dict):
        problems.append(
            issue(
                "v3_snapshot_manifest_binding_missing",
                "v3 prelock does not bind a toolchain snapshot manifest",
                check="frozen_compact_input",
            )
        )
        return {}
    manifest_path = resolve_repo_path(str(binding.get("path") or ""))
    if manifest_path is None or not manifest_path.is_file():
        problems.append(
            issue(
                "v3_snapshot_manifest_missing",
                "v3 prelock snapshot manifest path is missing/invalid",
                check="frozen_compact_input",
                detail=binding,
            )
        )
        return {}
    if binding.get("sha256") != sha256_file(manifest_path):
        problems.append(
            issue(
                "v3_snapshot_manifest_hash_mismatch",
                "v3 snapshot manifest bytes differ from the prelock binding",
                check="frozen_compact_input",
            )
        )
    config_snapshot_binding = config.get("toolchain_snapshot")
    if not isinstance(config_snapshot_binding, dict) or any(
        config_snapshot_binding.get(key) != binding.get(key)
        for key in ("path", "sha256", "snapshot_sha256", "file_count")
    ):
        problems.append(
            issue(
                "v3_config_snapshot_binding_mismatch",
                "generation config and prelock do not bind the identical snapshot manifest",
                check="frozen_compact_input",
            )
        )
    if binding.get("size_bytes") is not None and binding.get("size_bytes") != manifest_path.stat().st_size:
        problems.append(
            issue(
                "v3_snapshot_manifest_size_mismatch",
                "v3 snapshot manifest size differs from the prelock binding",
                check="frozen_compact_input",
            )
        )

    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        problems.append(
            issue(
                "v3_snapshot_manifest_not_object",
                "v3 snapshot manifest is not a JSON object",
                check="frozen_compact_input",
            )
        )
        return {}
    if manifest.get("status") not in {"frozen", "snapshotted_before_first_model_call"}:
        problems.append(
            issue(
                "v3_snapshot_not_frozen",
                "snapshot manifest is not marked frozen before the first wave_003 model call",
                check="frozen_compact_input",
                detail=manifest.get("status"),
            )
        )
    schema_version = str(manifest.get("schema_version") or "")
    if schema_version != "androidworld_candidate116_draft_toolchain_snapshot/v1":
        problems.append(
            issue(
                "v3_snapshot_schema_invalid",
                "snapshot manifest schema_version is missing or unexpected",
                check="frozen_compact_input",
                detail=schema_version,
            )
        )
    for hash_key in ("snapshot_sha256", "manifest_sha256"):
        if hash_key not in manifest:
            continue
        core = dict(manifest)
        claimed = core.pop(hash_key)
        if claimed != canonical_sha256(core):
            problems.append(
                issue(
                    "v3_snapshot_self_hash_mismatch",
                    f"snapshot manifest {hash_key} does not verify",
                    check="frozen_compact_input",
                )
            )

    snapshot_root = manifest_path.parent.resolve()
    expected_snapshot_root = (
        WORK_ROOT / "draft_generation" / "toolchain_snapshot" / "v3"
    ).resolve()
    if snapshot_root != expected_snapshot_root or manifest.get("snapshot_root") != repo_relative(
        expected_snapshot_root
    ):
        problems.append(
            issue(
                "v3_snapshot_root_mismatch",
                "snapshot manifest is not rooted at the dedicated immutable v3 directory",
                check="frozen_compact_input",
                detail={
                    "manifest_parent": repo_relative(snapshot_root),
                    "declared": manifest.get("snapshot_root"),
                    "expected": repo_relative(expected_snapshot_root),
                },
            )
        )
    named_bindings = manifest_named_bindings(manifest)
    if not named_bindings:
        problems.append(
            issue(
                "v3_snapshot_empty",
                "snapshot manifest contains no tool file bindings",
                check="frozen_compact_input",
            )
        )
        return {"manifest": manifest, "manifest_path": manifest_path}
    if manifest.get("file_count") != len(named_bindings) or len(named_bindings) != 11:
        problems.append(
            issue(
                "v3_snapshot_file_count_mismatch",
                "snapshot manifest file_count differs from its file-binding list",
                check="frozen_compact_input",
                detail={
                    "declared": manifest.get("file_count"),
                    "observed": len(named_bindings),
                    "required_v3_count": 11,
                },
            )
        )
    raw_files = manifest.get("files")
    if isinstance(raw_files, list) and manifest.get("files_sha256") != canonical_sha256(raw_files):
        problems.append(
            issue(
                "v3_snapshot_files_hash_mismatch",
                "snapshot aggregate files_sha256 does not verify",
                check="frozen_compact_input",
            )
        )
    observed_paths: dict[str, Path] = {}
    normalized_names: dict[str, Path] = {}
    for name, file_binding in named_bindings:
        path = resolve_repo_path(str(file_binding.get("path") or ""))
        if path is None or not path.is_file():
            problems.append(
                issue(
                    "v3_snapshot_file_missing",
                    "snapshot-bound tool file is missing",
                    check="frozen_compact_input",
                    detail={"role": name, "binding": file_binding},
                )
            )
            continue
        try:
            path.resolve().relative_to(snapshot_root)
        except ValueError:
            problems.append(
                issue(
                    "v3_snapshot_file_outside_snapshot",
                    "snapshot manifest points back to a mutable/non-snapshot tool path",
                    check="frozen_compact_input",
                    detail={"role": name, "path": repo_relative(path)},
                )
            )
        if file_binding.get("sha256") != sha256_file(path):
            problems.append(
                issue(
                    "v3_snapshot_file_hash_mismatch",
                    "snapshot-bound tool file hash changed",
                    check="frozen_compact_input",
                    detail={"role": name, "path": repo_relative(path)},
                )
            )
        if file_binding.get("size_bytes") is not None and file_binding.get("size_bytes") != path.stat().st_size:
            problems.append(
                issue(
                    "v3_snapshot_file_size_mismatch",
                    "snapshot-bound tool file size changed",
                    check="frozen_compact_input",
                    detail={"role": name, "path": repo_relative(path)},
                )
            )
        observed_paths[repo_relative(path)] = path
        normalized_names[normalized_role(name)] = path

    expected_snapshot_files = {path.resolve() for path in observed_paths.values()}
    actual_snapshot_files = {
        path.resolve()
        for path in snapshot_root.rglob("*")
        if path.is_file() and path.resolve() != manifest_path.resolve()
    }
    if actual_snapshot_files != expected_snapshot_files:
        problems.append(
            issue(
                "v3_snapshot_file_set_mismatch",
                "snapshot directory contains undeclared files or omits manifest-declared files",
                check="frozen_compact_input",
                detail={
                    "undeclared": [
                        repo_relative(path)
                        for path in sorted(actual_snapshot_files - expected_snapshot_files)
                    ],
                    "missing": [
                        repo_relative(path)
                        for path in sorted(expected_snapshot_files - actual_snapshot_files)
                    ],
                },
            )
        )

    writable_snapshot_paths = [
        repo_relative(path)
        for path in [manifest_path, *sorted(expected_snapshot_files)]
        if path.stat().st_mode & 0o222
    ]
    writable_snapshot_dirs = [
        repo_relative(path)
        for path in snapshot_root.rglob("*")
        if path.is_dir() and path.stat().st_mode & 0o222
    ]
    if snapshot_root.stat().st_mode & 0o222:
        writable_snapshot_dirs.insert(0, repo_relative(snapshot_root))
    if writable_snapshot_paths or writable_snapshot_dirs:
        problems.append(
            issue(
                "v3_snapshot_not_filesystem_readonly",
                "snapshot files/directories remain writable after the v3 prelock",
                check="frozen_compact_input",
                detail={
                    "writable_files": writable_snapshot_paths,
                    "writable_directories": writable_snapshot_dirs,
                },
            )
        )

    role_groups = {
        "draft_prompt": (
            "draft_prompt",
            "draft_case_checklist_prompt_md",
        ),
        "semantic_strict_supplement": (
            "semantic_strict_supplement",
            "prompt_supplement",
            "strict_supplement",
            "androidworld_full_packet_semantic_strict_v4_supplement_md",
        ),
        "checklist_schema": ("checklist_schema", "case_checklist_schema_json"),
        "checklist_guardrails": (
            "checklist_guardrails",
            "guardrails",
            "checklist_guardrails_py",
        ),
        "drafter": ("drafter", "draft_case_checklist_py"),
        "batch_runner": ("batch_runner", "run_draft_batch_py"),
        "draft_template": ("draft_template", "case_checklist_template_yaml"),
        "validator": ("validator", "checklist_validator_py"),
    }
    role_paths: dict[str, Path] = {}
    for required, alternatives in role_groups.items():
        matches = [
            path
            for observed_name, path in normalized_names.items()
            if observed_name in alternatives
        ]
        if len(matches) != 1:
            problems.append(
                issue(
                    "v3_snapshot_role_missing_or_ambiguous",
                    "snapshot must bind exactly one file for every required drafting role",
                    check="frozen_compact_input",
                    detail={"required_role": required, "match_count": len(matches)},
                )
            )
        else:
            role_paths[required] = matches[0]

    supplement_path = role_paths.get("semantic_strict_supplement")
    if supplement_path is not None:
        if supplement_path.name != "androidworld_full_packet_semantic_strict_v4.supplement.md":
            problems.append(
                issue(
                    "v3_semantic_supplement_not_full_v4",
                    "v3 snapshot semantic supplement is not the required full-packet v4 file",
                    check="frozen_compact_input",
                    detail=repo_relative(supplement_path),
                )
            )
        supplement_text = supplement_path.read_text(encoding="utf-8")
        required_supplement_phrases = (
            "complete frozen source closure",
            "literal, independently reviewable conditions",
            "suffix addition",
            "interaction_results.done",
            "agent_successful > 0.5",
            "stronger.additional_conditions",
            "retained post-run state",
            "## Source Inventory",
        )
        missing_phrases = [
            phrase for phrase in required_supplement_phrases if phrase not in supplement_text
        ]
        if missing_phrases:
            problems.append(
                issue(
                    "v3_full_semantic_v4_supplement_incomplete",
                    "full-packet semantic v4 supplement omits required fail-closed instructions",
                    check="frozen_compact_input",
                    detail=missing_phrases,
                )
            )

    runner_command = config.get("runner_command") or []
    if not isinstance(runner_command, list):
        runner_command = []
    if config.get("runner_command_sha256") != canonical_sha256(runner_command):
        problems.append(
            issue(
                "v3_runner_command_hash_mismatch",
                "wave_003 runner command canonical hash does not verify",
                check="llm_provenance",
            )
        )
    batch_runner = role_paths.get("batch_runner")
    if batch_runner is not None:
        runner_text = batch_runner.read_text(encoding="utf-8")
        if (
            batch_runner.name != "run_draft_batch.py"
            or "case_packet.md" not in runner_text
            or "compact_case_packet.md" in runner_text
            or "run_compact_draft_batch" in runner_text
        ):
            problems.append(
                issue(
                    "v3_snapshot_runner_is_not_native_full_packet_runner",
                    "snapshot batch runner is not the native full case_packet.md run_draft_batch.py",
                    check="frozen_compact_input",
                    detail=repo_relative(batch_runner),
                )
            )
        resolved_command_paths: list[Path] = []
        for raw in runner_command:
            text = str(raw)
            if not text.endswith(".py"):
                continue
            candidate = Path(text)
            resolved_command_paths.append(
                (candidate if candidate.is_absolute() else REPO_ROOT / candidate).resolve()
            )
        if batch_runner.resolve() not in resolved_command_paths:
            problems.append(
                issue(
                    "v3_runner_not_using_native_snapshot_runner",
                    "prelocked runner command does not invoke the snapshotted native run_draft_batch.py",
                    check="llm_provenance",
                    detail=[str(path) for path in resolved_command_paths],
                )
            )
        live_origins = manifest.get("live_origins_at_snapshot") or []
        runner_origins = [
            item
            for item in live_origins
            if isinstance(item, dict) and item.get("name") == "batch_runner"
        ]
        if len(runner_origins) != 1:
            problems.append(
                issue(
                    "v3_native_runner_origin_missing_or_ambiguous",
                    "snapshot must retain exactly one live-origin record for the native batch runner",
                    check="frozen_compact_input",
                )
            )
        else:
            origin = runner_origins[0]
            live_path = resolve_repo_path(str(origin.get("live_path") or ""))
            if (
                origin.get("live_path") != "neurips_ed_track_minimal/scripts/run_draft_batch.py"
                or origin.get("byte_identical") is not True
                or origin.get("snapshot_sha256") != sha256_file(batch_runner)
                or origin.get("live_sha256_at_snapshot") != sha256_file(batch_runner)
                or live_path is None
                or not live_path.is_file()
                or sha256_file(live_path) != sha256_file(batch_runner)
            ):
                problems.append(
                    issue(
                        "v3_native_runner_origin_mismatch",
                        "snapshot runner is not byte-identical to the native NeurIPS run_draft_batch.py origin",
                        check="frozen_compact_input",
                        detail=origin,
                    )
                )
    if supplement_path is not None and not command_path_pair_matches(
        runner_command,
        "--prompt-supplement",
        supplement_path,
    ):
        problems.append(
            issue(
                "v3_runner_missing_full_semantic_v4_supplement",
                "prelocked runner command does not pass the snapshotted strict semantic supplement",
                check="llm_provenance",
                detail=repo_relative(supplement_path),
            )
        )
    if not command_path_pair_matches(runner_command, "--output-root", DEFAULT_WAVE_ROOT):
        problems.append(
            issue(
                "v3_runner_output_not_wave_003",
                "prelocked runner command does not write exactly to wave_003",
                check="llm_provenance",
            )
        )
    if not command_path_pair_matches(runner_command, "--case-packet-root", EXPECTED_PACKET_ROOT):
        problems.append(
            issue(
                "v3_runner_packet_root_not_full_candidate116_root",
                "native runner command does not read the frozen candidate116 full case_packet root",
                check="llm_provenance",
                detail=repo_relative(EXPECTED_PACKET_ROOT),
            )
        )
    if any(
        rejected in str(item)
        for item in runner_command
        for rejected in ("wave_001", "wave_002", "compact_case_packet", "run_compact")
    ):
        problems.append(
            issue(
                "v3_runner_references_rejected_or_compact_input",
                "wave_003 runner command references rejected wave_001/wave_002 or compact tooling",
                check="llm_provenance",
            )
        )

    manifest_paths = set(observed_paths)
    for binding_owner, raw_tool_bindings in (
        ("prelock", prelock.get("tool_bindings") or {}),
        ("config", config.get("tool_bindings") or {}),
    ):
        for name, tool_binding in raw_tool_bindings.items():
            if not isinstance(tool_binding, dict):
                continue
            declared = str(tool_binding.get("path") or "")
            if declared and declared not in manifest_paths:
                problems.append(
                    issue(
                        "v3_tool_not_in_snapshot_manifest",
                        "prelock/config tool binding is not one of the frozen snapshot files",
                        check="frozen_compact_input",
                        detail={
                            "binding_owner": binding_owner,
                            "role": name,
                            "path": declared,
                        },
                    )
                )

    config_supplement = config.get("prompt_supplement") or {}
    prelock_supplement = prelock.get("prompt_supplement") or {}
    supplement_bindings = (config_supplement, prelock_supplement)
    if supplement_path is not None and any(
        not isinstance(candidate, dict)
        or resolve_repo_path(str(candidate.get("path") or "")) != supplement_path.resolve()
        or candidate.get("sha256") != sha256_file(supplement_path)
        or candidate.get("size_bytes") != supplement_path.stat().st_size
        for candidate in supplement_bindings
    ):
        problems.append(
            issue(
                "v3_supplement_binding_mismatch",
                "prelock/config do not both exactly bind the snapshotted full semantic v4 supplement",
                check="frozen_compact_input",
            )
        )

    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "role_paths": role_paths,
    }


def validate_prelock(
    prelock_path: Path,
    *,
    skip_live_login_check: bool,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    prelock = load_json(prelock_path)
    if not isinstance(prelock, dict):
        raise QcFatalError("prelock must be a JSON object")
    problems: list[dict[str, Any]] = []

    schema_version = str(prelock.get("schema_version") or "")
    generation_id = str(prelock.get("generation_id") or "")
    if schema_version != "androidworld_candidate116_codex_draft_prelock/v3":
        rejected = generation_id in {"wave_001", "wave_002"} or schema_version.endswith(
            ("/v1", "/v2")
        )
        reason = (
            "wave_001 and wave_002 are explicitly aborted and promotion-forbidden"
            if rejected
            else "only the exact full-packet wave_003 /v3 prelock is accepted"
        )
        raise QcFatalError(f"rejected prelock {prelock_path}: {reason}")
    if generation_id != "wave_003" or prelock.get("input_kind") != "full_case_packet":
        raise QcFatalError(
            "v3 QC requires generation_id=wave_003 and input_kind=full_case_packet"
        )
    if prelock.get("status") != "frozen_before_first_model_call":
        problems.append(
            issue(
                "prelock_wave_003_status_invalid",
                "v3 prelock is not marked frozen before the first wave_003 model call",
                check="frozen_compact_input",
                detail=prelock.get("status"),
            )
        )
    declared_raw_wave = resolve_repo_path(
        str((prelock.get("canonical_output_gate") or {}).get("raw_wave") or "")
    )
    if declared_raw_wave != DEFAULT_WAVE_ROOT.resolve():
        problems.append(
            issue(
                "prelock_raw_wave_not_wave_003",
                "v3 prelock canonical raw-wave target is not exactly wave_003",
                check="frozen_compact_input",
                detail=str(declared_raw_wave) if declared_raw_wave else None,
            )
        )

    claimed_prelock_sha = prelock.get("prelock_sha256")
    canonical_prelock = dict(prelock)
    canonical_prelock.pop("prelock_sha256", None)
    observed_prelock_sha = canonical_sha256(canonical_prelock)
    if claimed_prelock_sha != observed_prelock_sha:
        problems.append(
            issue(
                "prelock_self_hash_mismatch",
                "prelock canonical self-hash does not verify",
                check="frozen_compact_input",
                detail={"claimed": claimed_prelock_sha, "observed": observed_prelock_sha},
            )
        )

    case_order = prelock.get("case_order")
    if not isinstance(case_order, list):
        raise QcFatalError("prelock case_order is not a list")
    if (
        prelock.get("case_count") != EXPECTED_CASE_COUNT
        or len(case_order) != EXPECTED_CASE_COUNT
        or len(set(case_order)) != EXPECTED_CASE_COUNT
        or any(not isinstance(case_id, str) or not case_id for case_id in case_order)
    ):
        problems.append(
            issue(
                "prelock_case_universe_invalid",
                "prelock is not exactly 116 unique non-empty case ids",
                check="frozen_compact_input",
            )
        )
    if prelock.get("case_order_sha256") != canonical_sha256(case_order):
        problems.append(
            issue(
                "prelock_case_order_hash_mismatch",
                "prelock case-order hash does not verify",
                check="frozen_compact_input",
            )
        )

    packet_inputs = prelock.get("packet_inputs")
    if not isinstance(packet_inputs, list):
        raise QcFatalError("v3 prelock packet_inputs is not a list")
    if prelock.get("packet_inputs_sha256") != canonical_sha256(packet_inputs):
        problems.append(
            issue(
                "full_packet_input_index_hash_mismatch",
                "full packet input index hash does not verify",
                check="frozen_compact_input",
            )
        )
    if len(packet_inputs) != EXPECTED_CASE_COUNT:
        problems.append(
            issue(
                "full_packet_input_count_mismatch",
                "v3 prelock does not bind exactly 116 full packet inputs",
                check="frozen_compact_input",
                detail=len(packet_inputs),
            )
        )

    packet_diagnostics: list[dict[str, Any]] = []
    observed_packet_paths: set[Path] = set()
    for rank, item in enumerate(packet_inputs):
        if not isinstance(item, dict):
            problems.append(
                issue(
                    "full_packet_input_record_invalid",
                    "full packet input record is not an object",
                    check="frozen_compact_input",
                    detail=rank,
                )
            )
            continue
        expected_case = case_order[rank] if rank < len(case_order) else None
        if (
            item.get("selection_rank") != rank
            or item.get("case_unit_id") != expected_case
            or item.get("task_id") != expected_case
            or item.get("input_kind") != "full_case_packet"
            or not isinstance(item.get("source_closure_sha256"), str)
            or len(item.get("source_closure_sha256") or "") != 64
        ):
            problems.append(
                issue(
                    "full_packet_input_identity_or_order_mismatch",
                    "full packet record does not match frozen identity/rank/input kind",
                    check="frozen_compact_input",
                    detail={"rank": rank, "record": item},
                )
            )
        resolved = resolve_repo_path(str(item.get("path") or ""))
        if resolved is None or not resolved.is_file():
            problems.append(
                issue(
                    "full_packet_input_missing",
                    "frozen full case_packet.md path is missing or invalid",
                    check="frozen_compact_input",
                    detail=item,
                )
            )
            continue
        expected_path = (EXPECTED_PACKET_ROOT / str(expected_case) / "case_packet.md").resolve()
        if resolved != expected_path:
            problems.append(
                issue(
                    "full_packet_input_path_not_canonical",
                    "v3 packet input is not the canonical full case_packet.md for its case",
                    check="frozen_compact_input",
                    detail={
                        "case_unit_id": expected_case,
                        "observed": repo_relative(resolved),
                        "expected": repo_relative(expected_path),
                    },
                )
            )
        if resolved in observed_packet_paths:
            problems.append(
                issue(
                    "full_packet_input_path_duplicate",
                    "more than one frozen case binds the same full packet path",
                    check="frozen_compact_input",
                    detail=repo_relative(resolved),
                )
            )
        observed_packet_paths.add(resolved)
        if sha256_file(resolved) != item.get("sha256") or resolved.stat().st_size != item.get("size_bytes"):
            problems.append(
                issue(
                    "full_packet_input_content_changed",
                    "full case packet bytes/size no longer match the v3 prelock",
                    check="frozen_compact_input",
                    detail=item.get("case_unit_id"),
                )
            )
            continue
        try:
            packet = parse_full_case_packet(resolved.read_text(encoding="utf-8"))
            packet_problems, packet_diagnostic = validate_full_packet_structure(
                packet=packet,
                packet_record=item,
            )
            problems.extend(packet_problems)
            packet_diagnostic.update(
                {
                    "path": repo_relative(resolved),
                    "sha256": item.get("sha256"),
                    "size_bytes": item.get("size_bytes"),
                    "status": "pass" if not packet_problems else "fail",
                }
            )
            packet_diagnostics.append(packet_diagnostic)
        except (OSError, UnicodeDecodeError, QcFatalError) as exc:
            problems.append(
                issue(
                    "full_packet_parse_failed",
                    str(exc),
                    check="frozen_compact_input",
                    detail=item.get("case_unit_id"),
                )
            )
            packet_diagnostics.append(
                {
                    "case_unit_id": item.get("case_unit_id"),
                    "selection_rank": rank,
                    "path": repo_relative(resolved),
                    "status": "fail",
                    "parse_error": str(exc),
                }
            )

    def verify_bound_file(binding: Any, code: str, check: str) -> Path | None:
        if not isinstance(binding, dict):
            problems.append(issue(code, "prelock file binding is missing", check=check))
            return None
        path = resolve_repo_path(str(binding.get("path") or ""))
        if path is None or not path.is_file():
            problems.append(issue(code, "prelock-bound file is missing", check=check, detail=binding))
            return None
        if binding.get("sha256") and sha256_file(path) != binding.get("sha256"):
            problems.append(issue(code, "prelock-bound file hash changed", check=check, detail=binding))
        if binding.get("file_sha256") and sha256_file(path) != binding.get("file_sha256"):
            problems.append(issue(code, "prelock-bound file hash changed", check=check, detail=binding))
        return path

    verify_bound_file(prelock.get("static_acceptance"), "static_acceptance_binding_invalid", "frozen_compact_input")
    verify_bound_file(
        prelock.get("readonly_before_snapshot"),
        "readonly_before_snapshot_binding_invalid",
        "frozen_compact_input",
    )
    old_freeze_path = verify_bound_file(
        prelock.get("old_packet_source_freeze"),
        "old_freeze_binding_invalid",
        "frozen_compact_input",
    )
    if old_freeze_path is not None:
        old_freeze = load_json(old_freeze_path)
        if old_freeze.get("freeze_sha256") != prelock["old_packet_source_freeze"].get("freeze_sha256"):
            problems.append(
                issue(
                    "old_freeze_internal_hash_mismatch",
                    "old packet/source freeze id does not match the prelock",
                    check="frozen_compact_input",
                )
            )

    config_path = verify_bound_file(
        prelock.get("draft_config"),
        "draft_config_binding_invalid",
        "llm_provenance",
    )
    if config_path is None:
        raise QcFatalError("cannot continue without the prelocked draft config")
    config = load_json(config_path)
    if not isinstance(config, dict):
        raise QcFatalError("draft config is not an object")
    if (
        prelock.get("generation_id") != "wave_003"
        or config.get("generation_id") != "wave_003"
        or prelock.get("input_kind") != "full_case_packet"
        or config.get("input_kind") != "full_case_packet"
    ):
        problems.append(
            issue(
                "wave_003_generation_or_input_kind_mismatch",
                "v3 prelock/config must both bind wave_003 full_case_packet generation",
                check="frozen_compact_input",
                detail={
                    "prelock": prelock.get("generation_id"),
                    "config": config.get("generation_id"),
                    "prelock_input_kind": prelock.get("input_kind"),
                    "config_input_kind": config.get("input_kind"),
                },
            )
        )
    if config.get("schema_version") != "androidworld_candidate116_codex_draft_config/v3":
        problems.append(
            issue(
                "draft_config_is_not_v3",
                "only the wave_003 full-packet /v3 generation config is accepted",
                check="llm_provenance",
                detail=config.get("schema_version"),
            )
        )
    if config.get("status") != "prelocked":
        problems.append(
            issue(
                "draft_config_status_invalid",
                "wave_003 generation config status is not prelocked",
                check="llm_provenance",
                detail=config.get("status"),
            )
        )
    canonical_config = dict(config)
    claimed_config_sha = canonical_config.pop("config_sha256", None)
    observed_config_sha = canonical_sha256(canonical_config)
    if claimed_config_sha != observed_config_sha or prelock["draft_config"].get("config_sha256") != claimed_config_sha:
        problems.append(
            issue(
                "draft_config_self_hash_mismatch",
                "draft config canonical hash does not verify against itself and the prelock",
                check="llm_provenance",
            )
        )

    expected_config = {
        "provider": "codex_cli",
        "auth_mode": EXPECTED_AUTH_MODE,
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "sandbox": EXPECTED_SANDBOX,
        "max_parallel": EXPECTED_PARALLELISM,
        "large_max_parallel": EXPECTED_PARALLELISM,
        "ephemeral": True,
        "ignore_user_config": True,
        "quality_check": "none",
    }
    for field, expected in expected_config.items():
        if config.get(field) != expected:
            problems.append(
                issue(
                    "draft_config_policy_mismatch",
                    f"draft config {field} is not the required value",
                    check="llm_provenance",
                    field=field,
                    detail={"expected": expected, "observed": config.get(field)},
                )
            )

    login_at_prelock = str((config.get("codex_cli") or {}).get("login_status_at_prelock") or "")
    if "logged in" not in login_at_prelock.lower():
        problems.append(
            issue(
                "codex_not_logged_in_at_prelock",
                "prelock did not record an active Codex login",
                check="llm_provenance",
                detail=login_at_prelock,
            )
        )

    for name, binding in (prelock.get("tool_bindings") or {}).items():
        if not isinstance(binding, dict):
            problems.append(
                issue(
                    "tool_binding_invalid",
                    "tool binding is not an object",
                    check="frozen_compact_input",
                    detail=name,
                )
            )
            continue
        path = resolve_repo_path(str(binding.get("path") or ""))
        if path is None or not path.is_file():
            problems.append(
                issue(
                    "tool_binding_missing",
                    "prelocked drafting tool is missing",
                    check="frozen_compact_input",
                    detail=name,
                )
            )
            continue
        if sha256_file(path) != binding.get("sha256") or path.stat().st_size != binding.get("size_bytes"):
            problems.append(
                issue(
                    "tool_binding_changed",
                    "prelocked drafting tool bytes/size changed",
                    check="frozen_compact_input",
                    detail=name,
                )
            )

    supersedes = prelock.get("supersedes") or []
    if (
        not isinstance(supersedes, list)
        or [item.get("generation_id") for item in supersedes if isinstance(item, dict)]
        != ["wave_001", "wave_002"]
        or config.get("supersedes_generation_ids") != ["wave_001", "wave_002"]
    ):
        problems.append(
            issue(
                "rejected_wave_supersession_set_invalid",
                "v3 prelock/config do not explicitly supersede exactly wave_001 and wave_002",
                check="frozen_compact_input",
                detail={
                    "prelock": supersedes,
                    "config": config.get("supersedes_generation_ids"),
                },
            )
        )
    for superseded in supersedes if isinstance(supersedes, list) else []:
        if not isinstance(superseded, dict):
            continue
        rejected_generation = superseded.get("generation_id")
        incident_path = resolve_repo_path(str(superseded.get("incident_path") or ""))
        if (
            rejected_generation not in {"wave_001", "wave_002"}
            or incident_path is None
            or not incident_path.is_file()
            or superseded.get("incident_sha256") != (
                sha256_file(incident_path)
                if incident_path is not None and incident_path.is_file()
                else None
            )
        ):
            problems.append(
                issue(
                    "rejected_wave_abort_binding_invalid",
                    "v3 prelock does not exactly bind an aborted wave incident file",
                    check="frozen_compact_input",
                    detail=superseded,
                )
            )
            continue
        incident = load_json(incident_path)
        if not isinstance(incident, dict):
            problems.append(
                issue(
                    "rejected_wave_abort_record_not_object",
                    "aborted wave incident record is not an object",
                    check="frozen_compact_input",
                    detail=rejected_generation,
                )
            )
            continue
        incident_core = dict(incident)
        claimed_incident = incident_core.pop("incident_sha256", None)
        if (
            incident.get("status") != "aborted_not_eligible"
            or incident.get("promotion_forbidden") is not True
            or incident.get("wave_output_eligible") is not False
            or incident.get("generation_id") != rejected_generation
            or claimed_incident != canonical_sha256(incident_core)
            or (
                superseded.get("incident_record_sha256") is not None
                and claimed_incident != superseded.get("incident_record_sha256")
            )
        ):
            problems.append(
                issue(
                    "rejected_wave_abort_record_invalid",
                    "rejected wave incident record is not internally valid/fail-closed",
                    check="frozen_compact_input",
                    detail=rejected_generation,
                )
            )

    snapshot_info = validate_v3_snapshot_toolchain(
        prelock=prelock,
        config=config,
        problems=problems,
    )

    live_login: dict[str, Any] = {"checked": not skip_live_login_check}
    if not skip_live_login_check:
        codex = shutil.which("codex")
        if not codex:
            problems.append(
                issue(
                    "codex_cli_missing_at_qc",
                    "Codex CLI is unavailable during QC",
                    check="llm_provenance",
                )
            )
            live_login.update({"active": False, "detail": "codex not found"})
        else:
            completed = subprocess.run(
                [codex, "login", "status"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            detail = "\n".join(
                part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
            )
            active = completed.returncode == 0 and "logged in" in detail.lower()
            live_login.update(
                {
                    "active": active,
                    "returncode": completed.returncode,
                    "detail": detail,
                    "binary": str(Path(codex).resolve()),
                }
            )
            if not active:
                problems.append(
                    issue(
                        "codex_login_inactive_at_qc",
                        "current Codex login status is not active",
                        check="llm_provenance",
                        detail=live_login,
                    )
                )

    context = {
        "prelock": prelock,
        "config": config,
        "case_order": case_order,
        "packet_by_case": {
            item.get("case_unit_id"): item for item in packet_inputs if isinstance(item, dict)
        },
        "packet_diagnostics": packet_diagnostics,
        "live_login": live_login,
        "declared_raw_wave": declared_raw_wave,
        "snapshot_info": snapshot_info,
    }
    return prelock, context, problems


def load_batch_records(wave_root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    path = wave_root / "_batch_results.jsonl"
    problems: list[dict[str, Any]] = []
    records: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return records, [
            issue(
                "batch_results_missing",
                "raw wave has no _batch_results.jsonl",
                check="batch_result",
            )
        ]
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            problems.append(
                issue(
                    "batch_results_invalid_jsonl",
                    "batch result line is invalid JSON",
                    check="batch_result",
                    detail={"line": line_number, "error": str(exc)},
                )
            )
            continue
        case_id = record.get("case_unit_dir") if isinstance(record, dict) else None
        if not isinstance(case_id, str) or not case_id:
            problems.append(
                issue(
                    "batch_result_missing_case_id",
                    "batch result line has no case_unit_dir",
                    check="batch_result",
                    detail=line_number,
                )
            )
            continue
        if case_id in records:
            problems.append(
                issue(
                    "duplicate_batch_result",
                    "case appears more than once in batch results",
                    check="batch_result",
                    detail=case_id,
                )
            )
        records[case_id] = record
    return records, problems


def successful_attempt(record: dict[str, Any]) -> dict[str, Any] | None:
    attempts = record.get("attempts") or []
    for attempt in reversed(attempts):
        if (
            isinstance(attempt, dict)
            and attempt.get("returncode") == 0
            and str(attempt.get("validator") or "").startswith("checklist valid:")
        ):
            return attempt
    return None


def command_has_pair(command: list[Any], flag: str, value: str) -> bool:
    for index in range(len(command) - 1):
        if command[index] == flag and command[index + 1] == value:
            return True
    return False


def check_llm_provenance(
    *,
    case_id: str,
    api: dict[str, Any],
    llm_call: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    expected_api = {
        "provider": "codex_cli",
        "model": EXPECTED_MODEL,
        "status": "completed",
    }
    for field, expected in expected_api.items():
        if api.get(field) != expected:
            problems.append(
                issue(
                    "api_provenance_mismatch",
                    f"api_response.{field} is not the prelocked value",
                    check="llm_provenance",
                    field=f"api_response.{field}",
                    detail={"expected": expected, "observed": api.get(field)},
                )
            )
    cli = api.get("codex_cli") or {}
    for field, expected in {
        "auth_mode": EXPECTED_AUTH_MODE,
        "returncode": 0,
        "sandbox": EXPECTED_SANDBOX,
    }.items():
        if cli.get(field) != expected:
            problems.append(
                issue(
                    "codex_cli_provenance_mismatch",
                    f"api_response.codex_cli.{field} is not the required value",
                    check="llm_provenance",
                    field=f"api_response.codex_cli.{field}",
                    detail={"expected": expected, "observed": cli.get(field)},
                )
            )
    command = cli.get("command") or []
    command_requirements = {
        "codex_exec": len(command) >= 2 and command[0:2] == ["codex", "exec"],
        "ephemeral": "--ephemeral" in command,
        "ignore_user_config": "--ignore-user-config" in command,
        "read_only": command_has_pair(command, "--sandbox", EXPECTED_SANDBOX),
        "model": command_has_pair(command, "--model", EXPECTED_MODEL),
        "reasoning_effort": any(
            str(item).replace("'", '"') == 'model_reasoning_effort="xhigh"' for item in command
        ),
        "json": "--json" in command,
        "output_schema": "--output-schema" in command,
    }
    for name, passed in command_requirements.items():
        if not passed:
            problems.append(
                issue(
                    "codex_command_policy_missing",
                    f"Codex command does not prove required setting: {name}",
                    check="llm_provenance",
                    field="api_response.codex_cli.command",
                )
            )
    if cli.get("malformed_event_lines") not in ([], None):
        problems.append(
            issue(
                "codex_malformed_events",
                "Codex response contains malformed event lines",
                check="llm_provenance",
                detail=cli.get("malformed_event_lines"),
            )
        )
    event_types = [event.get("type") for event in cli.get("events") or [] if isinstance(event, dict)]
    if "thread.started" not in event_types or "turn.completed" not in event_types:
        problems.append(
            issue(
                "codex_event_sequence_incomplete",
                "Codex event stream lacks thread.started or turn.completed",
                check="llm_provenance",
            )
        )

    expected_llm = {
        "schema_version": "llm_call/v1",
        "provider": "codex_cli",
        "model": EXPECTED_MODEL,
        "model_version": EXPECTED_MODEL,
        "api_key_env": "CODEX_HOME",
        "domain": "androidworld",
        "case_unit_id": case_id,
        "task_id": case_id,
        "phase": "draft",
        "agent_id_or_role": "case_checklist_drafter",
    }
    for field, expected in expected_llm.items():
        if llm_call.get(field) != expected:
            problems.append(
                issue(
                    "llm_call_provenance_mismatch",
                    f"llm_call.{field} is not the required value",
                    check="llm_provenance",
                    field=f"llm_call.{field}",
                    detail={"expected": expected, "observed": llm_call.get(field)},
                )
            )
    metadata = llm_call.get("response_metadata") or {}
    for field, expected in {
        "response_status": "completed",
        "provider_model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "auth_mode": EXPECTED_AUTH_MODE,
    }.items():
        if metadata.get(field) != expected:
            problems.append(
                issue(
                    "llm_response_metadata_mismatch",
                    f"llm_call.response_metadata.{field} is not the required value",
                    check="llm_provenance",
                    field=f"llm_call.response_metadata.{field}",
                    detail={"expected": expected, "observed": metadata.get(field)},
                )
            )
    if metadata.get("response_id") != api.get("id"):
        problems.append(
            issue(
                "response_id_mismatch",
                "llm_call response id does not match api_response id",
                check="llm_provenance",
            )
        )
    usage = llm_call.get("token_usage") or {}
    if not isinstance(usage.get("total_tokens"), int) or usage.get("total_tokens", 0) <= 0:
        problems.append(
            issue(
                "token_usage_missing",
                "llm_call does not retain positive total token usage",
                check="llm_provenance",
            )
        )
    if config.get("model") != api.get("model") or config.get("reasoning_effort") != metadata.get("reasoning_effort"):
        problems.append(
            issue(
                "case_call_differs_from_prelock",
                "per-case LLM call differs from the prelocked model/reasoning configuration",
                check="llm_provenance",
            )
        )
    return problems


def per_case_qc(
    *,
    case_id: str,
    rank: int,
    packet_record: dict[str, Any] | None,
    wave_root: Path,
    batch_record: dict[str, Any] | None,
    schema: dict[str, Any],
    guardrail_module: Any,
    config: dict[str, Any],
    global_input_failed_checks: set[str],
) -> dict[str, Any]:
    problems: list[dict[str, Any]] = []
    checks = {name: True for name in CHECK_NAMES}
    for name in global_input_failed_checks:
        if name in checks:
            checks[name] = False

    report: dict[str, Any] = {
        "schema_version": CASE_REPORT_SCHEMA_VERSION,
        "case_unit_id": case_id,
        "task_id": case_id,
        "status": "failed",
        "checklist_path": repo_relative(wave_root / case_id / "checklist.yaml"),
        "checklist_sha256": None,
        "selection_rank": rank,
        "checks": checks,
        "issues": problems,
        "support_pointer_resolutions": [],
        "automatic_qc_scope": "mechanical_and_deterministic_only",
        "human_semantic_review": {
            "status": "required_not_performed_by_this_script",
            "promotion_authorized": False,
        },
    }
    for name in sorted(global_input_failed_checks):
        if name in checks:
            problems.append(
                issue(
                    "global_qc_precondition_failed",
                    f"global raw-wave/prelock check failed: {name}",
                    check=name,
                )
            )

    if packet_record is None:
        problems.append(
            issue(
                "case_missing_from_prelocked_full_packet_index",
                "case has no full packet input record in the v3 prelock",
                check="frozen_compact_input",
            )
        )
        checks["frozen_packet_input"] = False
        return report
    packet_path = resolve_repo_path(str(packet_record.get("path") or ""))
    if packet_path is None or not packet_path.is_file():
        problems.append(
            issue(
                "full_packet_missing",
                "case full case_packet.md is missing",
                check="frozen_compact_input",
            )
        )
        checks["frozen_packet_input"] = False
        return report
    report["packet_path"] = repo_relative(packet_path)
    report["packet_sha256"] = sha256_file(packet_path)
    if (
        report["packet_sha256"] != packet_record.get("sha256")
        or packet_path.stat().st_size != packet_record.get("size_bytes")
    ):
        problems.append(
            issue(
                "full_packet_hash_mismatch",
                "case full packet does not match the v3 prelock",
                check="frozen_compact_input",
            )
        )
        checks["frozen_packet_input"] = False
    packet_text = packet_path.read_text(encoding="utf-8")
    try:
        packet = parse_full_case_packet(packet_text)
    except QcFatalError as exc:
        problems.append(
            issue(
                "full_packet_payload_invalid",
                str(exc),
                check="frozen_compact_input",
            )
        )
        checks["frozen_packet_input"] = False
        return report
    packet_problems, packet_diagnostic = validate_full_packet_structure(
        packet=packet,
        packet_record=packet_record,
    )
    report["full_packet_diagnostic"] = packet_diagnostic
    problems.extend(packet_problems)

    case_dir = wave_root / case_id
    missing_sidecars = [name for name in REQUIRED_CANONICAL_SIDECARS if not (case_dir / name).is_file()]
    if missing_sidecars:
        problems.append(
            issue(
                "required_sidecars_missing",
                "canonical raw-wave sidecars are missing",
                check="required_sidecars",
                detail=missing_sidecars,
            )
        )
        checks["required_sidecars"] = False

    if batch_record is None:
        problems.append(
            issue(
                "case_batch_result_missing",
                "case has no batch result record",
                check="batch_result",
            )
        )
        checks["batch_result"] = False
        return report
    if batch_record.get("status") != "success":
        problems.append(
            issue(
                "case_batch_not_success",
                "fresh raw-wave case was not recorded as success",
                check="batch_result",
                detail=batch_record.get("status"),
            )
        )
        checks["batch_result"] = False
    raw_batch_packet = str(batch_record.get("case_packet") or "")
    batch_packet_candidate = Path(raw_batch_packet)
    batch_packet_path = (
        batch_packet_candidate
        if batch_packet_candidate.is_absolute()
        else REPO_ROOT / batch_packet_candidate
    ).resolve()
    if (
        batch_packet_path != packet_path.resolve()
        or batch_record.get("case_packet_size_bytes") != packet_record.get("size_bytes")
    ):
        problems.append(
            issue(
                "batch_full_packet_input_mismatch",
                "batch record does not bind the expected frozen full packet path/size",
                check="batch_result",
                detail={
                    "batch_packet": raw_batch_packet,
                    "expected_packet": repo_relative(packet_path),
                    "batch_size": batch_record.get("case_packet_size_bytes"),
                    "expected_size": packet_record.get("size_bytes"),
                },
            )
        )
        checks["batch_result"] = False

    accepted_attempt = successful_attempt(batch_record)
    if accepted_attempt is None:
        problems.append(
            issue(
                "accepted_attempt_missing",
                "batch record has no returncode=0, validator-accepted attempt",
                check="batch_result",
            )
        )
        checks["batch_result"] = False
    else:
        attempt_index = accepted_attempt.get("attempt_index")
        prefix = f"attempt_{attempt_index:02d}"
        attempt_missing = [
            f"{prefix}.{name}" for name in REQUIRED_CANONICAL_SIDECARS if not (case_dir / f"{prefix}.{name}").is_file()
        ]
        if attempt_missing:
            problems.append(
                issue(
                    "accepted_attempt_sidecars_missing",
                    "accepted attempt sidecars are incomplete",
                    check="required_sidecars",
                    detail=attempt_missing,
                )
            )
            checks["required_sidecars"] = False
        for name in REQUIRED_CANONICAL_SIDECARS:
            canonical = case_dir / name
            attempted = case_dir / f"{prefix}.{name}"
            if canonical.is_file() and attempted.is_file() and sha256_file(canonical) != sha256_file(attempted):
                problems.append(
                    issue(
                        "promoted_sidecar_differs_from_accepted_attempt",
                        "canonical sidecar bytes differ from the validator-accepted attempt",
                        check="required_sidecars",
                        detail=name,
                    )
                )
                checks["required_sidecars"] = False

    checklist_yaml_path = case_dir / "checklist.yaml"
    checklist_json_path = case_dir / "checklist.json"
    checklist: dict[str, Any] | None = None
    if checklist_yaml_path.is_file():
        report["checklist_sha256"] = sha256_file(checklist_yaml_path)
    if checklist_yaml_path.is_file() and checklist_json_path.is_file():
        try:
            yaml_value = load_yaml(checklist_yaml_path)
            json_value = load_json(checklist_json_path)
            if yaml_value != json_value:
                problems.append(
                    issue(
                        "yaml_json_content_mismatch",
                        "canonical checklist YAML and JSON do not represent the same object",
                        check="yaml_json_consistency",
                    )
                )
                checks["yaml_json_consistency"] = False
            if isinstance(json_value, dict):
                checklist = json_value
            else:
                problems.append(
                    issue(
                        "checklist_not_object",
                        "checklist JSON is not an object",
                        check="schema",
                    )
                )
                checks["schema"] = False
        except QcFatalError as exc:
            problems.append(
                issue(
                    "checklist_parse_failed",
                    str(exc),
                    check="yaml_json_consistency",
                )
            )
            checks["yaml_json_consistency"] = False

    if checklist is not None:
        identity_values = {
            "schema_version": "case_checklist_v1",
            "case_unit_id": case_id,
            "domain": "androidworld",
            "task_id": case_id,
        }
        for field, expected in identity_values.items():
            if checklist.get(field) != expected:
                problems.append(
                    issue(
                        "checklist_identity_mismatch",
                        f"checklist {field} differs from the frozen case identity",
                        check="identity",
                        field=field,
                        detail={"expected": expected, "observed": checklist.get(field)},
                    )
                )
                checks["identity"] = False

        validator = Draft202012Validator(schema)
        schema_errors = sorted(
            validator.iter_errors(checklist),
            key=lambda error: [str(part) for part in error.absolute_path],
        )
        for error in schema_errors:
            field = ".".join(str(part) for part in error.absolute_path) or "<root>"
            problems.append(
                issue(
                    "checklist_schema_violation",
                    error.message,
                    check="schema",
                    field=field,
                )
            )
            checks["schema"] = False

        try:
            allowed_source_paths = guardrail_module.case_packet_support_paths(packet_text)
            expected_source_paths = {"case_packet.md", *packet.get("inventory", [])}
            if allowed_source_paths != expected_source_paths:
                problems.append(
                    issue(
                        "guardrail_full_inventory_allowlist_mismatch",
                        "snapshotted guardrail did not derive the exact complete Source Inventory allowlist",
                        check="guardrails",
                        detail={
                            "missing": sorted(expected_source_paths - allowed_source_paths),
                            "extra": sorted(allowed_source_paths - expected_source_paths),
                        },
                    )
                )
                checks["guardrails"] = False
            guardrail_violations = guardrail_module.collect_checklist_guardrail_violations(
                checklist,
                allowed_source_paths=allowed_source_paths,
            )
        except Exception as exc:  # defensive: a guardrail crash must fail closed
            allowed_source_paths = set()
            guardrail_violations = [f"guardrail module raised {type(exc).__name__}: {exc}"]
        for violation in guardrail_violations:
            problems.append(
                issue(
                    "checklist_guardrail_violation",
                    str(violation),
                    check="guardrails",
                )
            )
            checks["guardrails"] = False

        for field, pointer in iter_supports(checklist):
            resolution, pointer_problems = resolve_pointer(
                pointer=pointer,
                packet_path=packet_path,
                packet_text=packet_text,
                packet=packet,
                allowed_source_paths=allowed_source_paths,
            )
            resolution["field"] = field
            report["support_pointer_resolutions"].append(resolution)
            for problem in pointer_problems:
                problem["field"] = field
                problems.append(problem)
                checks["support_paths"] = False

        for problem in check_sfu_done_gate(checklist):
            problems.append(problem)
            checks["sfu_done_gate"] = False

        for problem in checklist_policy_checks(checklist):
            problems.append(problem)
            checks[problem["check"]] = False

    if all((case_dir / name).is_file() for name in ("api_response.json", "llm_call.json")):
        try:
            api = load_json(case_dir / "api_response.json")
            llm_call = load_json(case_dir / "llm_call.json")
            if not isinstance(api, dict) or not isinstance(llm_call, dict):
                raise QcFatalError("api_response/llm_call must be objects")
            for problem in check_llm_provenance(
                case_id=case_id,
                api=api,
                llm_call=llm_call,
                config=config,
            ):
                problems.append(problem)
                checks["llm_provenance"] = False
        except QcFatalError as exc:
            problems.append(
                issue(
                    "llm_sidecar_parse_failed",
                    str(exc),
                    check="llm_provenance",
                )
            )
            checks["llm_provenance"] = False
    else:
        checks["llm_provenance"] = False

    # Any error assigned to a check is authoritative even if a code path forgot
    # to toggle it above.
    for problem in problems:
        if problem.get("severity") == "error" and problem.get("check") in checks:
            checks[problem["check"]] = False
    report["status"] = (
        "passed"
        if all(checks.values()) and not any(item["severity"] == "error" for item in problems)
        else "failed"
    )
    return report


def validate_batch_summary(
    wave_root: Path,
    *,
    case_order: list[str],
    records: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    summary_path = wave_root / "_batch_summary.json"
    if not summary_path.is_file():
        return [
            issue(
                "batch_summary_missing",
                "raw wave has no _batch_summary.json",
                check="batch_result",
            )
        ]
    summary = load_json(summary_path)
    expected_fields = {
        "total_cases": EXPECTED_CASE_COUNT,
        "completed_cases": EXPECTED_CASE_COUNT,
        "success_cases": EXPECTED_CASE_COUNT,
        "skipped_cases": 0,
        "failed_cases": 0,
        "provider": "codex",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "codex_sandbox": EXPECTED_SANDBOX,
        "quality_check": "none",
    }
    for field, expected in expected_fields.items():
        if summary.get(field) != expected:
            problems.append(
                issue(
                    "batch_summary_policy_mismatch",
                    f"batch summary {field} is not the required final value",
                    check="batch_result",
                    field=field,
                    detail={"expected": expected, "observed": summary.get(field)},
                )
            )
    expected_set = set(case_order)
    observed_dirs = {
        path.name for path in wave_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    } if wave_root.is_dir() else set()
    if observed_dirs != expected_set:
        problems.append(
            issue(
                "raw_wave_case_set_mismatch",
                "raw-wave case directories are not exactly the frozen 116-set",
                check="batch_result",
                detail={
                    "missing": sorted(expected_set - observed_dirs),
                    "extra": sorted(observed_dirs - expected_set),
                },
            )
        )
    if set(records) != expected_set:
        problems.append(
            issue(
                "batch_result_case_set_mismatch",
                "batch result records are not exactly the frozen 116-set",
                check="batch_result",
                detail={
                    "missing": sorted(expected_set - set(records)),
                    "extra": sorted(set(records) - expected_set),
                },
            )
        )
    return problems


def main() -> int:
    args = parse_args()
    wave_root = args.wave_root.resolve()
    prelock_path = args.prelock.resolve()
    report_root = args.report_root.resolve()
    generated_at = utc_now()

    if wave_root.name in {"wave_001", "wave_002"}:
        raise QcFatalError(
            f"raw {wave_root.name} is explicitly aborted, promotion-forbidden, and rejected by v3 QC"
        )

    prelock, context, global_problems = validate_prelock(
        prelock_path,
        skip_live_login_check=args.skip_live_login_check,
    )
    case_order: list[str] = context["case_order"]
    packet_by_case: dict[str, dict[str, Any]] = context["packet_by_case"]
    config: dict[str, Any] = context["config"]

    if args.preflight_only:
        packet_diagnostics = context.get("packet_diagnostics") or []
        error_count = sum(item.get("severity") == "error" for item in global_problems)
        passed_packets = [
            item.get("case_unit_id")
            for item in packet_diagnostics
            if item.get("status") == "pass"
        ]
        failed_packets = [
            item.get("case_unit_id")
            for item in packet_diagnostics
            if item.get("status") != "pass"
        ]
        passed = (
            error_count == 0
            and len(packet_diagnostics) == EXPECTED_CASE_COUNT
            and len(passed_packets) == EXPECTED_CASE_COUNT
            and not failed_packets
        )
        preflight = {
            "schema_version": PREFLIGHT_SCHEMA_VERSION,
            "generated_at": generated_at,
            "status": "pass" if passed else "fail",
            "generation_id": "wave_003",
            "input_kind": "full_case_packet",
            "prelock_path": repo_relative(prelock_path),
            "prelock_file_sha256": sha256_file(prelock_path),
            "prelock_sha256": prelock.get("prelock_sha256"),
            "config_path": (prelock.get("draft_config") or {}).get("path"),
            "config_sha256": config.get("config_sha256"),
            "snapshot_manifest": (prelock.get("toolchain_snapshot") or {}).get("path"),
            "snapshot_sha256": (prelock.get("toolchain_snapshot") or {}).get(
                "snapshot_sha256"
            ),
            "full_semantic_v4_supplement": prelock.get("prompt_supplement"),
            "native_runner": (prelock.get("tool_bindings") or {}).get("batch_runner"),
            "case_count": EXPECTED_CASE_COUNT,
            "validated_packet_count": len(packet_diagnostics),
            "passed_packet_count": len(passed_packets),
            "failed_packet_count": len(failed_packets),
            "failed_packets": failed_packets,
            "packet_diagnostics": packet_diagnostics,
            "issues": global_problems,
            "error_count": error_count,
            "live_codex_login_at_qc": context["live_login"],
            "execution_safety": {
                "model_invoked": False,
                "wave_inspected": False,
                "wave_written": False,
                "only_diagnostic_written": True,
            },
            "post_generation_automatic_gates": {
                "count": len(CHECK_NAMES),
                "names": list(CHECK_NAMES),
                "status": "deferred_until_wave_003_is_complete",
            },
            "promotion_gate": {
                "preflight_passed": passed,
                "automatic_wave_qc_still_required": True,
                "independent_human_semantic_review_still_required": True,
                "contracts_or_drafts_may_be_frozen_from_this_report_alone": False,
            },
        }
        preflight["preflight_sha256"] = canonical_sha256(preflight)
        write_json_atomic(report_root / "preflight.json", preflight)
        print(
            json.dumps(
                {
                    "status": preflight["status"],
                    "validated_packets": len(packet_diagnostics),
                    "packet_failures": len(failed_packets),
                    "global_error_count": error_count,
                    "preflight": repo_relative(report_root / "preflight.json"),
                    "model_invoked": False,
                    "wave_inspected": False,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        if passed or args.diagnostic_exit_zero:
            return 0
        return 1

    if wave_root != DEFAULT_WAVE_ROOT.resolve() or wave_root != context.get("declared_raw_wave"):
        global_problems.append(
            issue(
                "qc_input_is_not_prelocked_wave_003",
                "QC input wave must be exactly the raw wave_003 target bound by the v3 prelock",
                check="batch_result",
                detail={
                    "qc_wave": str(wave_root),
                    "expected_wave": str(DEFAULT_WAVE_ROOT.resolve()),
                    "prelock_wave": str(context.get("declared_raw_wave")),
                },
            )
        )

    batch_records, batch_record_problems = load_batch_records(wave_root)
    global_problems.extend(batch_record_problems)
    global_problems.extend(
        validate_batch_summary(wave_root, case_order=case_order, records=batch_records)
    )

    snapshot_roles = (context.get("snapshot_info") or {}).get("role_paths") or {}
    schema_path = snapshot_roles.get("checklist_schema")
    guardrail_path = snapshot_roles.get("checklist_guardrails")
    if schema_path is None or not schema_path.is_file():
        raise QcFatalError("snapshotted/prelocked checklist schema cannot be loaded")
    if guardrail_path is None or not guardrail_path.is_file():
        raise QcFatalError("snapshotted/prelocked checklist guardrails cannot be loaded")
    schema = load_json(schema_path)
    guardrail_module = load_guardrail_module(guardrail_path)

    global_failed_checks = {
        item["check"]
        for item in global_problems
        if item.get("severity") == "error" and item.get("check") in CHECK_NAMES
    }
    reports: list[dict[str, Any]] = []
    for rank, case_id in enumerate(case_order):
        report = per_case_qc(
            case_id=case_id,
            rank=rank,
            packet_record=packet_by_case.get(case_id),
            wave_root=wave_root,
            batch_record=batch_records.get(case_id),
            schema=schema,
            guardrail_module=guardrail_module,
            config=config,
            global_input_failed_checks=global_failed_checks,
        )
        report["generated_at"] = generated_at
        write_json_atomic(report_root / case_id / "qc.json", report)
        reports.append(report)

    passed = [report["case_unit_id"] for report in reports if report["status"] == "passed"]
    failed = [report["case_unit_id"] for report in reports if report["status"] == "failed"]
    all_automatic_passed = (
        len(passed) == EXPECTED_CASE_COUNT
        and not failed
        and not any(item.get("severity") == "error" for item in global_problems)
    )
    summary_issues = list(global_problems)
    summary_issues.extend(
        {
            "severity": "error",
            "code": "case_automatic_qc_failed",
            "check": "case_reports",
            "message": "per-case automatic QC did not pass",
            "case_unit_id": report["case_unit_id"],
            "case_issue_count": sum(
                item.get("severity") == "error" for item in report["issues"]
            ),
        }
        for report in reports
        if report["status"] != "passed"
    )
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "pass" if all_automatic_passed else "fail",
        "automatic_status": (
            "automatic_pass_human_semantic_review_required"
            if all_automatic_passed
            else "automatic_failed_or_incomplete"
        ),
        "case_count": EXPECTED_CASE_COUNT,
        "passed_count": len(passed),
        "failed_count": len(failed),
        "issues": summary_issues,
        "prelock_path": repo_relative(prelock_path),
        "prelock_file_sha256": sha256_file(prelock_path),
        "prelock_sha256": prelock.get("prelock_sha256"),
        "wave_root": repo_relative(wave_root),
        "report_root": repo_relative(report_root),
        "expected_case_count": EXPECTED_CASE_COUNT,
        "reported_case_count": len(reports),
        "automatic_passed_count": len(passed),
        "automatic_failed_count": len(failed),
        "automatic_passed_cases": passed,
        "automatic_failed_cases": failed,
        "global_issues": global_problems,
        "required_configuration": {
            "auth_mode": EXPECTED_AUTH_MODE,
            "model": EXPECTED_MODEL,
            "reasoning_effort": EXPECTED_REASONING_EFFORT,
            "sandbox": EXPECTED_SANDBOX,
            "parallelism": EXPECTED_PARALLELISM,
        },
        "live_codex_login_at_qc": context["live_login"],
        "case_report_schema_version": CASE_REPORT_SCHEMA_VERSION,
        "case_report_index": [
            {
                "selection_rank": report["selection_rank"],
                "case_unit_id": report["case_unit_id"],
                "status": report["status"],
                "path": repo_relative(report_root / report["case_unit_id"] / "qc.json"),
            }
            for report in reports
        ],
        "promotion_gate": {
            "automatic_gate_passed": all_automatic_passed,
            "human_semantic_review_required": True,
            "human_semantic_reviews_completed": 0,
            "contracts_or_drafts_may_be_frozen_from_this_report_alone": False,
            "reason": (
                "This script checks deterministic/mechanical properties only. Each of the 116 "
                "checklists still requires an independent, source-grounded human semantic decision."
            ),
        },
    }
    summary["summary_sha256"] = canonical_sha256(summary)
    write_json_atomic(report_root / "summary.json", summary)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "automatic_status": summary["automatic_status"],
                "automatic_passed": len(passed),
                "automatic_failed": len(failed),
                "global_error_count": sum(
                    item.get("severity") == "error" for item in global_problems
                ),
                "summary": repo_relative(report_root / "summary.json"),
                "human_semantic_review_required": True,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if all_automatic_passed or args.diagnostic_exit_zero:
        return 0
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QcFatalError as exc:
        print(f"strict automatic QC fatal error: {exc}", file=sys.stderr)
        raise SystemExit(2)
