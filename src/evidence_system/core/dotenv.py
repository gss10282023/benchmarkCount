"""Minimal local dotenv loading for private runtime secrets."""

from __future__ import annotations

import os
import re
from collections.abc import Sequence
from pathlib import Path

from evidence_system.core.paths import repo_root


_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DEFAULT_DOTENV_FILES = (".env", "secrets/.env")


def load_project_dotenv(*, override: bool = False, paths: Sequence[str | Path] | None = None) -> dict[str, str]:
    """Load private .env files without requiring python-dotenv.

    The loader intentionally ignores .env.example files. Those are templates and
    may be committed; real API keys belong in ignored .env files.
    """

    loaded: dict[str, str] = {}
    candidates = [Path(path) for path in paths] if paths is not None else [repo_root() / name for name in _DEFAULT_DOTENV_FILES]
    for path in candidates:
        if not path.is_absolute():
            path = repo_root() / path
        if not path.exists() or not path.is_file():
            continue
        for key, value in _iter_dotenv_pairs(path):
            if not override and key in os.environ:
                continue
            os.environ[key] = value
            loaded[key] = str(path)
    return loaded


def _iter_dotenv_pairs(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not _KEY_RE.match(key):
            continue
        pairs.append((key, _parse_dotenv_value(value)))
    return pairs


def _parse_dotenv_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value
