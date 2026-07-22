#!/usr/bin/env python3
"""Validate a drafted checklist with schema checks plus deterministic guardrails."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PACKAGE_ROOT = ROOT_DIR.parent
SCHEMA_PATH = ROOT_DIR / "schemas" / "case_checklist.schema.json"
LINE_POINTER_RE = re.compile(
    r"^(?:"
    r"L\s*(?P<label_start>\d+)(?:\s*-\s*L\s*(?P<label_end>\d+))?"
    r"|(?:lines?|line_span)\s*:?\s*(?P<word_start>\d+)"
    r"(?:\s*[-:]\s*(?P<word_end>\d+))?"
    r"|(?P<legacy_start>\d+)\s*-\s*(?P<legacy_end>\d+)"
    r")$",
    re.IGNORECASE,
)
PATH_TOKEN_RE = re.compile(r"^([^\[\]]*)((?:\[[^\]]+\])*)$")
BRACKET_RE = re.compile(r"\[([^\]]+)\]")
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
YAML_SUFFIXES = frozenset({".yaml", ".yml"})

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
    validate_checklist_guardrails,
)


class ChecklistValidationError(RuntimeError):
    """Raised when a checklist fails validation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checklist", type=Path, help="Path to a drafted checklist YAML or JSON file")
    parser.add_argument(
        "--case-packet",
        type=Path,
        default=None,
        help=(
            "Optional matching case_packet.md. When supplied, support pointers are "
            "restricted to case_packet.md and its exact Source Inventory paths."
        ),
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ChecklistValidationError(f"Failed to read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ChecklistValidationError(f"Failed to parse JSON from {path}: {exc}") from exc


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ChecklistValidationError(f"Failed to read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ChecklistValidationError(f"Failed to parse YAML from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ChecklistValidationError(
            f"Checklist must parse to a mapping, found {type(data).__name__} in {path}"
        )
    return data


def load_checklist(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        return load_json(path)
    return load_yaml(path)


def _iter_supports(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    """Yield every support pointer and its checklist location."""

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key == "support" and isinstance(child, list):
                for index, pointer in enumerate(child):
                    yield f"{child_path}[{index}]", str(pointer)
            else:
                yield from _iter_supports(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_supports(child, f"{path}[{index}]")


def _resolve_structured_selector(document: Any, selector: str) -> Any:
    """Resolve a small JSON/YAML path subset and return the selected value."""

    current = document
    target = selector.strip()
    if target == "$":
        return current
    if target.startswith("$"):
        remainder = target[1:]
        if remainder.startswith("."):
            target = remainder[1:]
        elif remainder.startswith("["):
            target = remainder
        else:
            raise ValueError("JSON root '$' must be followed by '.' or '['")
    if not target:
        raise ValueError("structured selector is empty")

    for token in target.split("."):
        if not token:
            raise ValueError("structured selector contains an empty token")
        match = PATH_TOKEN_RE.fullmatch(token)
        if match is None:
            raise ValueError(f"invalid structured selector token {token!r}")
        key, brackets = match.groups()
        if key:
            if not isinstance(current, dict) or key not in current:
                raise ValueError(f"missing key {key!r}")
            current = current[key]
        elif not brackets:
            raise ValueError(f"invalid structured selector token {token!r}")
        for bracket in BRACKET_RE.findall(brackets):
            if ":" in bracket or ".." in bracket:
                raise ValueError(f"slice/range selector is not allowed: [{bracket}]")
            if bracket.isdigit():
                if not isinstance(current, list) or int(bracket) >= len(current):
                    raise ValueError(f"array index out of bounds: [{bracket}]")
                current = current[int(bracket)]
                continue
            if "=" not in bracket or not isinstance(current, list):
                raise ValueError(f"unsupported selector [{bracket}]")
            filter_key, expected = bracket.split("=", 1)
            expected = expected.strip("'\"")
            matches = [
                item
                for item in current
                if isinstance(item, dict) and str(item.get(filter_key)) == expected
            ]
            if len(matches) != 1:
                raise ValueError(f"filter [{bracket}] resolved to {len(matches)} items")
            current = matches[0]
    return current


def _validate_line_span(text: str, selector: str) -> bool:
    """Validate a supported line selector and return whether it matched the grammar."""

    match = LINE_POINTER_RE.fullmatch(selector.strip())
    if match is None:
        return False
    lines = text.splitlines()
    start_text = (
        match.group("label_start")
        or match.group("word_start")
        or match.group("legacy_start")
    )
    end_text = (
        match.group("label_end")
        or match.group("word_end")
        or match.group("legacy_end")
    )
    assert start_text is not None
    start = int(start_text)
    end = int(end_text or start)
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"line span {start}-{end} is outside 1-{len(lines)}")
    if not any(line.strip() for line in lines[start - 1 : end]):
        raise ValueError(f"line span {start}-{end} is empty")
    return True


def _validate_text_selector(text: str, selector: str, *, markdown: bool) -> None:
    """Resolve line spans, exact Markdown headings, or source symbols."""

    target = selector.strip()
    if _validate_line_span(text, target):
        return
    if markdown:
        headings: set[str] = set()
        for line in text.splitlines():
            match = re.match(r"^\s*#{1,6}\s+(.+?)\s*#*\s*$", line)
            if match is not None:
                headings.add(match.group(1).strip())
        if target not in headings:
            raise ValueError(f"heading {selector!r} not found")
        return

    # Non-Markdown source pointers use symbols. Require either the literal
    # selector or every dotted identifier to occur in the source text. This
    # keeps Python-style pointers such as ClassName.FIELD useful without
    # pretending that a language-specific AST is available for every source.
    if target in text:
        return
    identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", target)
    if identifiers and all(re.search(rf"\b{re.escape(item)}\b", text) for item in identifiers):
        return
    raise ValueError(f"symbol {selector!r} not found")


def _load_structured_source(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"failed to read source: {exc}") from exc
    try:
        if path.suffix.lower() == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"failed to parse structured source: {exc}") from exc


def validate_support_pointer(case_packet_path: Path, pointer: str) -> None:
    """Resolve one pointer against the packet or its exact raw_case source tree."""

    if "::" not in pointer:
        raise ValueError("missing :: separator")
    relative, selector = pointer.split("::", 1)
    if not relative or not selector:
        raise ValueError("path and selector must both be non-empty")

    packet_path = case_packet_path.resolve()
    raw_root = (packet_path.parent / "raw_case").resolve()
    if relative == "case_packet.md":
        source_path = packet_path
    else:
        source_path = (raw_root / relative).resolve()
        if not source_path.is_relative_to(raw_root):
            raise ValueError(f"source path escapes raw_case: {relative}")
    if not source_path.is_file():
        raise ValueError(f"source path is missing: {relative}")

    suffix = source_path.suffix.lower()
    try:
        text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"failed to read source: {exc}") from exc
    if _validate_line_span(text, selector):
        return
    if suffix == ".json" or suffix in YAML_SUFFIXES:
        structured_selector, separator, embedded_selector = selector.partition("::")
        try:
            selected = _resolve_structured_selector(
                _load_structured_source(source_path), structured_selector
            )
        except ValueError:
            if suffix not in YAML_SUFFIXES or separator:
                raise
            _validate_text_selector(text, selector, markdown=False)
            return
        if separator:
            if not isinstance(selected, str):
                raise ValueError(
                    "embedded symbol selector requires the structured path to resolve to text"
                )
            _validate_text_selector(selected, embedded_selector, markdown=False)
        return
    _validate_text_selector(text, selector, markdown=suffix in MARKDOWN_SUFFIXES)


def validate_support_pointers(checklist: dict[str, Any], case_packet_path: Path) -> None:
    """Fail closed when any checklist support pointer cannot be resolved."""

    failures: list[str] = []
    for location, pointer in _iter_supports(checklist):
        try:
            validate_support_pointer(case_packet_path, pointer)
        except ValueError as exc:
            failures.append(f"{location} pointer {pointer!r}: {exc}")
    if failures:
        raise ChecklistValidationError(
            "Checklist has unresolvable support pointers:\n- " + "\n- ".join(failures)
        )


def validate_packet_required_stronger_conditions(
    checklist: dict[str, Any],
    case_packet_path: Path,
) -> None:
    """Enforce a packet's pre-run source-supported stronger freeze basis."""

    context_path = case_packet_path.parent / "raw_case" / "derived" / "drafting_context.json"
    if not context_path.is_file():
        return
    context = load_json(context_path)
    if context.get("schema_version") != "miniwob_pre_run_drafting_context/v1":
        return
    stronger_basis = context.get("stronger_measurement")
    if not isinstance(stronger_basis, dict):
        raise ChecklistValidationError(
            "MiniWoB drafting context has no stronger_measurement mapping"
        )
    required = stronger_basis.get("required_additional_conditions")
    if not isinstance(required, list):
        raise ChecklistValidationError(
            "MiniWoB drafting context has no required_additional_conditions list"
        )
    checklist_stronger = checklist.get("stronger")
    observed = (
        checklist_stronger.get("additional_conditions")
        if isinstance(checklist_stronger, dict)
        else None
    )
    if not isinstance(observed, list):
        raise ChecklistValidationError(
            "Checklist has no stronger.additional_conditions list"
        )
    required_ids = [
        str(item.get("id") or "") for item in required if isinstance(item, dict)
    ]
    observed_ids = [
        str(item.get("id") or "") for item in observed if isinstance(item, dict)
    ]
    if len(required_ids) != len(required) or observed_ids != required_ids:
        raise ChecklistValidationError(
            "Checklist stronger conditions differ from the locked MiniWoB packet basis: "
            f"required={required_ids}, observed={observed_ids}"
        )
    for index, (expected, actual) in enumerate(zip(required, observed, strict=True)):
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            raise ChecklistValidationError(
                f"MiniWoB stronger condition {index} must be a mapping"
            )
        for field in ("id", "text", "rationale", "support"):
            if actual.get(field) != expected.get(field):
                raise ChecklistValidationError(
                    "Checklist stronger condition does not preserve the locked MiniWoB "
                    f"packet field at stronger.additional_conditions[{index}].{field}"
                )


def main() -> int:
    args = parse_args()
    checklist = load_checklist(args.checklist)
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(checklist), key=lambda e: list(e.absolute_path))
    if errors:
        lines = ["Checklist failed schema validation:"]
        for err in errors:
            path = ".".join(str(p) for p in err.absolute_path) or "<root>"
            lines.append(f"- {path}: {err.message}")
        raise ChecklistValidationError("\n".join(lines))

    allowed_source_paths: set[str] | None = None
    if args.case_packet is not None:
        try:
            case_packet_text = args.case_packet.read_text(encoding="utf-8")
        except OSError as exc:
            raise ChecklistValidationError(
                f"Failed to read case packet {args.case_packet}: {exc}"
            ) from exc
        try:
            allowed_source_paths = case_packet_support_paths(case_packet_text)
        except ChecklistGuardrailError as exc:
            raise ChecklistValidationError(str(exc)) from exc

    try:
        validate_checklist_guardrails(
            checklist,
            allowed_source_paths=allowed_source_paths,
        )
    except ChecklistGuardrailError as exc:
        raise ChecklistValidationError(str(exc)) from exc

    if args.case_packet is not None:
        validate_support_pointers(checklist, args.case_packet)
        validate_packet_required_stronger_conditions(checklist, args.case_packet)

    print(f"checklist valid: {args.checklist}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ChecklistValidationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
