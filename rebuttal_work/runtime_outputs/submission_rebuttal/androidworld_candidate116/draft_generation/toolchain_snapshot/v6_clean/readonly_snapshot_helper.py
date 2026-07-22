#!/usr/bin/env python3
"""Stdlib-only trust anchor for candidate116 repair read-only snapshots.

This module deliberately imports no project package and reads no project
manifest to discover its scope.  The protected paths are explicit constants.
Callers must pass the repository and candidate workspace roots.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Mapping


SNAPSHOT_SCHEMA = "androidworld_checklist_repair_dedicated_readonly_snapshot/v1"
CONTENT_TREE_HASH_ALGORITHM = "sha256-content-tree-v2:path-kind-size-content-or-link-target"
METADATA_TREE_HASH_ALGORITHM = (
    "sha256-metadata-tree-v1:path-kind-mode-uid-gid-flags-size-mtime_ns-ctime_ns"
)
ROOT_PATHS = (
    "neurips_ed_track_minimal",
    "paper_result_packages",
    "paper_result_packages/androidworld_both_agents_scored_cases_official_full100",
    "results",
)
PROTECTED_ROOT_PATHS = (
    "paper_result_packages",
    "paper_result_packages/androidworld_both_agents_scored_cases_official_full100",
    "results",
)
NONBINDING_LIVE_TOOL_ROOT = "neurips_ed_track_minimal"
OFFICIAL100_PATH = (
    "experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json"
)
POLICY = (
    "this repair flow writes only under the candidate workspace and requires exact pre/post "
    "content-and-metadata endpoint equality for results, paper_result_packages, the submitted "
    "official100 package, and the official100 selector; this endpoint comparison does not prove "
    "that a malicious write-and-restore never happened inside the window; neurips_ed_track_minimal "
    "is recorded but nonbinding because execution uses a prelocked tool snapshot"
)


class ReadonlySnapshotError(RuntimeError):
    """Raised when the dedicated read-only snapshot contract is not proven."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ReadonlySnapshotError(f"path is outside repository: {resolved}") from exc


def content_tree_snapshot(root: Path, repo_root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise ReadonlySnapshotError(f"read-only snapshot root is missing: {root}")
    digest = hashlib.sha256()
    file_count = 0
    directory_count = 0
    symlink_count = 0
    other_count = 0
    total_file_bytes = 0
    immutable_flag = getattr(stat, "UF_IMMUTABLE", 0)
    unlocked: list[str] = []
    metadata_rows: list[list[Any]] = []

    def metadata_row(relative: str, metadata: os.stat_result, kind: str) -> list[Any]:
        return [
            relative,
            kind,
            metadata.st_mode,
            metadata.st_uid,
            metadata.st_gid,
            int(getattr(metadata, "st_flags", 0)),
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        ]

    root_metadata = root.lstat()
    metadata_rows.append(metadata_row(".", root_metadata, "D"))
    entries = sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())
    for path in entries:
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if immutable_flag and not metadata.st_flags & immutable_flag:
            unlocked.append(relative)
        if stat.S_ISLNK(metadata.st_mode):
            symlink_count += 1
            kind = "L"
            row: list[Any] = ["L", relative, os.readlink(path)]
        elif stat.S_ISDIR(metadata.st_mode):
            directory_count += 1
            kind = "D"
            row = ["D", relative]
        elif stat.S_ISREG(metadata.st_mode):
            file_count += 1
            total_file_bytes += metadata.st_size
            kind = "F"
            row = ["F", relative, metadata.st_size, sha256_file(path)]
        else:
            other_count += 1
            kind = "O"
            row = ["O", relative, metadata.st_mode]
        metadata_rows.append(metadata_row(relative, metadata, kind))
        digest.update(json.dumps(row, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    if immutable_flag and not root_metadata.st_flags & immutable_flag:
        unlocked.insert(0, ".")
    return {
        "path": repo_relative(root, repo_root),
        "hash_algorithm": CONTENT_TREE_HASH_ALGORITHM,
        "content_tree_sha256": digest.hexdigest(),
        "metadata_hash_algorithm": METADATA_TREE_HASH_ALGORITHM,
        "metadata_tree_sha256": object_sha256(metadata_rows),
        "recursive_entry_count_excluding_root": len(entries),
        "recursive_entry_count_including_root": len(entries) + 1,
        "file_count": file_count,
        "directory_count": directory_count,
        "symlink_count": symlink_count,
        "other_entry_count": other_count,
        "total_file_bytes": total_file_bytes,
        "all_entries_uf_immutable": not unlocked,
        "unlocked_entry_count_including_root": len(unlocked),
        "unlocked_entries": unlocked,
    }


def readonly_operation_snapshot(
    *, phase: str, repo_root: Path, work_root: Path
) -> dict[str, Any]:
    if not phase or any(character.isspace() for character in phase):
        raise ReadonlySnapshotError("snapshot phase must be a token without whitespace")
    repo_root = repo_root.resolve()
    work_root = work_root.resolve()
    try:
        work_root.relative_to(repo_root)
    except ValueError as exc:
        raise ReadonlySnapshotError("candidate work root is outside repository") from exc
    official100 = repo_root / OFFICIAL100_PATH
    if not official100.is_file():
        raise ReadonlySnapshotError(f"official100 selector is missing: {official100}")
    official_metadata = official100.lstat()
    official_stat = {
        "kind": "symlink" if official100.is_symlink() else "regular_file",
        "mode": official_metadata.st_mode,
        "uid": official_metadata.st_uid,
        "gid": official_metadata.st_gid,
        "flags": int(getattr(official_metadata, "st_flags", 0)),
        "size_bytes": official_metadata.st_size,
        "mtime_ns": official_metadata.st_mtime_ns,
        "ctime_ns": official_metadata.st_ctime_ns,
    }
    return {
        "schema_version": SNAPSHOT_SCHEMA,
        "phase": phase,
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "write_scope": repo_relative(work_root, repo_root),
        "policy": POLICY,
        "roots": {
            relative: content_tree_snapshot(repo_root / relative, repo_root)
            for relative in ROOT_PATHS
        },
        "official100": {
            "path": OFFICIAL100_PATH,
            "file_count": 1,
            "size_bytes": official100.stat().st_size,
            "sha256": sha256_file(official100),
            "stat": official_stat,
            "stat_sha256": object_sha256(official_stat),
            "uf_immutable": bool(
                getattr(stat, "UF_IMMUTABLE", 0)
                and official_metadata.st_flags & getattr(stat, "UF_IMMUTABLE", 0)
            ),
        },
    }


def readonly_snapshot_core(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA:
        raise ReadonlySnapshotError("dedicated read-only snapshot schema is invalid")
    roots = snapshot.get("roots")
    if not isinstance(roots, Mapping) or tuple(roots) != ROOT_PATHS:
        raise ReadonlySnapshotError("dedicated read-only snapshot roots/order are invalid")
    return {
        "write_scope": snapshot.get("write_scope"),
        "policy": snapshot.get("policy"),
        "roots": dict(roots),
        "official100": snapshot.get("official100"),
    }


def compare_gate(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, Any]:
    before_core = readonly_snapshot_core(before)
    after_core = readonly_snapshot_core(after)
    protected = {
        root: before_core["roots"].get(root) == after_core["roots"].get(root)
        for root in PROTECTED_ROOT_PATHS
    }
    official_equal = before_core["official100"] == after_core["official100"]
    return {
        "protected_root_equality": protected,
        "protected_roots_unchanged": all(protected.values()),
        "official100_equal": official_equal,
        "status": "pass" if all(protected.values()) and official_equal else "fail",
        "nonbinding_live_tool_root": NONBINDING_LIVE_TOOL_ROOT,
        "nonbinding_live_tool_root_equal": (
            before_core["roots"].get(NONBINDING_LIVE_TOOL_ROOT)
            == after_core["roots"].get(NONBINDING_LIVE_TOOL_ROOT)
        ),
    }
