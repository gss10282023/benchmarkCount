#!/usr/bin/env python3
"""Shared, stdlib-only trust helpers for the candidate116 wave_004 v6_clean gate."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping


CASE_COUNT = 116
PARALLELISM = 6
GENERATION_ID = "wave_004_v6_clean"
PRELOCK_SCHEMA = "androidworld_candidate116_codex_draft_prelock/v6_clean"
CONFIG_SCHEMA = "androidworld_candidate116_codex_draft_config/v6_clean"
SNAPSHOT_SCHEMA = "androidworld_candidate116_draft_toolchain_snapshot/v6_clean"
EXPECTED_MODEL = "gpt-5.6-sol"
EXPECTED_REASONING = "xhigh"
EXPECTED_SANDBOX = "read-only"
EXPECTED_CODEX_VERSION = "codex-cli 0.144.4"
EXPECTED_FREEZE_SHA256 = (
    "fe2018595bf1ef44de803fffe82c81dd55f5368b8fde47d1a10a7958bdd8a9e4"
)
CASE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")


class Wave004V6CleanError(RuntimeError):
    """Raised whenever a v6_clean trust assertion cannot be proven."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Wave004V6CleanError(f"cannot load {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise Wave004V6CleanError(f"{label} is not a JSON object")
    return value


def add_self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result.pop(field, None)
    result[field] = canonical_sha256(result)
    return result


def verify_self_hash(value: Mapping[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if not isinstance(claimed, str) or claimed != canonical_sha256(core):
        raise Wave004V6CleanError(f"{label} self-hash mismatch")


def write_json_create_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise Wave004V6CleanError(f"create-once destination already exists: {path}") from exc


def regular_file_binding(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise Wave004V6CleanError(f"regular binding refuses symlink: {path}")
    resolved = path.resolve(strict=True)
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise Wave004V6CleanError(f"not a regular file: {path}")
    return {
        "path": str(resolved),
        "kind": "regular_file",
        "sha256": sha256_file(resolved),
        "size_bytes": metadata.st_size,
        "mode": stat.S_IMODE(metadata.st_mode),
    }


def executable_binding(path: Path) -> dict[str, Any]:
    """Bind an executable path, including both symlink identity and target bytes."""

    absolute = path.absolute()
    metadata = absolute.lstat()
    resolved = absolute.resolve(strict=True)
    if not resolved.is_file():
        raise Wave004V6CleanError(f"executable target is not a file: {path}")
    binding = {
        "path": str(absolute),
        "kind": "symlink" if stat.S_ISLNK(metadata.st_mode) else "regular_file",
        "resolved_path": str(resolved),
        "resolved_sha256": sha256_file(resolved),
        "resolved_size_bytes": resolved.stat().st_size,
        "mode": stat.S_IMODE(metadata.st_mode),
    }
    if stat.S_ISLNK(metadata.st_mode):
        binding["link_target"] = os.readlink(absolute)
    return binding


def verify_regular_file_binding(binding: Mapping[str, Any], label: str) -> Path:
    path = Path(str(binding.get("path") or ""))
    if not path.is_absolute() or binding.get("kind") != "regular_file":
        raise Wave004V6CleanError(f"{label} binding identity is invalid")
    if path.is_symlink() or not path.is_file():
        raise Wave004V6CleanError(f"{label} is missing, non-regular, or symlinked")
    metadata = path.lstat()
    if (
        path.resolve(strict=True) != path
        or metadata.st_size != binding.get("size_bytes")
        or stat.S_IMODE(metadata.st_mode) != binding.get("mode")
        or sha256_file(path) != binding.get("sha256")
    ):
        raise Wave004V6CleanError(f"{label} physical binding mismatch")
    return path


def verify_executable_binding(binding: Mapping[str, Any], label: str) -> Path:
    path = Path(str(binding.get("path") or ""))
    if not path.is_absolute() or not path.exists():
        raise Wave004V6CleanError(f"{label} executable path is missing")
    metadata = path.lstat()
    kind = "symlink" if stat.S_ISLNK(metadata.st_mode) else "regular_file"
    if kind != binding.get("kind") or stat.S_IMODE(metadata.st_mode) != binding.get("mode"):
        raise Wave004V6CleanError(f"{label} executable link identity changed")
    if kind == "symlink" and os.readlink(path) != binding.get("link_target"):
        raise Wave004V6CleanError(f"{label} executable symlink target changed")
    resolved = path.resolve(strict=True)
    if (
        str(resolved) != binding.get("resolved_path")
        or resolved.stat().st_size != binding.get("resolved_size_bytes")
        or sha256_file(resolved) != binding.get("resolved_sha256")
    ):
        raise Wave004V6CleanError(f"{label} executable target bytes changed")
    return path


def require_safe_case_id(case_id: Any, label: str = "case_unit_id") -> str:
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        raise Wave004V6CleanError(f"unsafe {label}: {case_id!r}")
    return case_id


def relative_to(path: Path, root: Path, label: str) -> str:
    try:
        return path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()
    except ValueError as exc:
        raise Wave004V6CleanError(f"{label} escapes required root: {path}") from exc


def verify_exact_directory_files(
    root: Path, expected: list[Mapping[str, Any]], *, label: str
) -> None:
    if root.is_symlink() or not root.is_dir():
        raise Wave004V6CleanError(f"{label} root is missing or symlinked")
    observed: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            raise Wave004V6CleanError(f"symlink in {label}: {path}")
        if path.is_file():
            observed.append(
                {
                    "relative_path": path.relative_to(root).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    if observed != list(expected):
        raise Wave004V6CleanError(f"{label} exact file namespace changed")


def require_empty_or_absent(path: Path, label: str) -> None:
    if path.is_symlink():
        raise Wave004V6CleanError(f"{label} is symlinked")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise Wave004V6CleanError(f"{label} must be absent or an empty directory")
