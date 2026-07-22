"""Canonical, source-local support-pointer validation for AppWorld."""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any


def canonical_archive_path(value: str, *, require_official: bool = True) -> str | None:
    """Return an exact canonical POSIX archive path, or ``None`` when unsafe."""

    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        return None
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    if require_official and (not path.parts or path.parts[0] != "official"):
        return None
    return value


def _json_tokens(location: str) -> list[str | int] | None:
    if location == "$":
        return []
    if not location.startswith("$"):
        return None
    tokens: list[str | int] = []
    index = 1
    while index < len(location):
        if location[index] == ".":
            match = re.match(r"\.([^\.\[\]\s]+)", location[index:])
            if match is None:
                return None
            tokens.append(match.group(1))
        elif location[index] == "[":
            match = re.match(r"\[(0|[1-9][0-9]*)\]", location[index:])
            if match is None:
                return None
            tokens.append(int(match.group(1)))
        else:
            return None
        index += len(match.group(0))
    return tokens


def json_location_resolves(document: Any, location: str) -> bool:
    """Resolve the exact ``$`` JSON-pointer dialect used by the draft protocol."""

    tokens = _json_tokens(location)
    if tokens is None:
        return False
    current = document
    for token in tokens:
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                return False
            current = current[token]
        else:
            if not isinstance(current, Mapping) or token not in current:
                return False
            current = current[token]
    return True


def _python_definition_paths(source: str) -> list[str]:
    tree = ast.parse(source, filename="support.py")
    found: list[str] = []

    def visit(node: ast.AST, parents: tuple[str, ...] = ()) -> None:
        child_parents = parents
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            child_parents = (*parents, node.name)
            found.append(".".join(child_parents))
        for child in ast.iter_child_nodes(node):
            visit(child, child_parents)

    visit(tree)
    return found


def support_location_resolves(path: Path, location: str) -> bool:
    """Validate one exact source-local location without whitespace coercion."""

    if not isinstance(location, str) or not location or location != location.strip():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if path.suffix == ".json":
        try:
            return json_location_resolves(json.loads(text), location)
        except json.JSONDecodeError:
            return False
    lines = text.splitlines()
    line_match = re.fullmatch(r"L([1-9][0-9]*)(?:-L([1-9][0-9]*))?", location)
    if line_match:
        start = int(line_match.group(1))
        end = int(line_match.group(2) or line_match.group(1))
        return start <= end <= len(lines)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", location) is None:
        return False
    if path.suffix == ".py":
        try:
            return _python_definition_paths(text).count(location) == 1
        except SyntaxError:
            return False
    matches = re.findall(
        rf"(?<![A-Za-z0-9_]){re.escape(location)}(?![A-Za-z0-9_])", text
    )
    return len(matches) == 1


def official_pointer_resolves(
    *, task_dir: Path, pointer: str, inventory_paths: set[str]
) -> bool:
    """Validate one packet-policy pointer against its case-scoped inventory."""

    if not isinstance(pointer, str) or pointer.count("::") != 1:
        return False
    path_text, location = pointer.split("::", 1)
    if canonical_archive_path(path_text) != path_text:
        return False
    if path_text == "official/ground_truth/answer.json" or path_text not in inventory_paths:
        return False
    if not task_dir.is_dir() or task_dir.is_symlink():
        return False
    task_root = task_dir.resolve()
    candidate = task_root / path_text.removeprefix("official/")
    relative_parts = PurePosixPath(path_text.removeprefix("official/")).parts
    cursor = task_root
    for part in relative_parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return False
    source = candidate.resolve()
    try:
        source.relative_to(task_root)
    except ValueError:
        return False
    return source.is_file() and not source.is_symlink() and support_location_resolves(source, location)


__all__ = [
    "canonical_archive_path",
    "json_location_resolves",
    "official_pointer_resolves",
    "support_location_resolves",
]
