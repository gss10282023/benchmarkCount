"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root based on the installed source layout."""

    return Path(__file__).resolve().parents[3]


def resolve_repo_path(path: str | Path) -> Path:
    """Resolve a path relative to the repository root when needed."""

    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return repo_root() / candidate
