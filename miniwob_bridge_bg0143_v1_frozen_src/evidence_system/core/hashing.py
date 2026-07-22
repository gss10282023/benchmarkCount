"""Hashing helpers used by later manifest and provenance gates."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def sha256_path(path: str | Path) -> str:
    """Hash a file or a directory tree with stable relative file names."""

    resolved = Path(path)
    if resolved.is_file():
        return sha256_file(resolved)
    if not resolved.is_dir():
        raise FileNotFoundError(path)
    entries = []
    for file_path in sorted(p for p in resolved.rglob("*") if p.is_file()):
        if "__pycache__" in file_path.parts or file_path.suffix == ".pyc":
            continue
        entries.append(
            {
                "path": file_path.relative_to(resolved).as_posix(),
                "sha256": sha256_file(file_path),
            }
        )
    return sha256_object(entries)


def canonical_json_bytes(payload: Any) -> bytes:
    """Return the repository canonical JSON representation for hash inputs."""

    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_object(payload: Any) -> str:
    return sha256_bytes(canonical_json_bytes(payload))
