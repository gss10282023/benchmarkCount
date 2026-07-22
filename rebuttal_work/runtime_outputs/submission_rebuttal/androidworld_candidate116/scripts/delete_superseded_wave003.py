#!/usr/bin/env python3
"""Delete only the fully bound superseded wave_003 tree."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
WAVE_ROOT = WORK_ROOT / "draft_generation" / "waves" / "wave_003"
INCIDENT = (
    WORK_ROOT
    / "draft_generation"
    / "incidents"
    / "wave_003_superseded_full_regeneration.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def main() -> int:
    incident = json.loads(INCIDENT.read_text(encoding="utf-8"))
    claimed = incident.get("incident_sha256")
    core = dict(incident)
    core.pop("incident_sha256", None)
    if claimed != canonical_sha256(core):
        raise RuntimeError("supersession incident self-hash mismatch")
    if incident.get("status") != "superseded_user_requested_full_regeneration":
        raise RuntimeError("wave_003 does not have the required superseded status")
    scope = incident.get("deletion_authorization_scope") or {}
    if (
        scope.get("authorized_by") != "user"
        or scope.get("delete_only_old_wave_root") is not True
        or scope.get("exact_root") != repo_path(WAVE_ROOT)
    ):
        raise RuntimeError("wave_003 deletion scope is invalid")
    if WAVE_ROOT.is_symlink() or not WAVE_ROOT.is_dir():
        raise RuntimeError("wave_003 target is missing or is a symlink")

    observed = []
    for path in sorted(candidate for candidate in WAVE_ROOT.rglob("*") if candidate.is_file()):
        if path.is_symlink():
            raise RuntimeError(f"symlink appeared in wave_003: {path}")
        observed.append(
            {
                "path": repo_path(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    if (
        observed != incident.get("old_wave_files")
        or len(observed) != incident.get("old_wave_file_count")
        or canonical_sha256(observed) != incident.get("old_wave_files_sha256")
    ):
        raise RuntimeError("wave_003 changed after its deletion inventory was frozen")

    shutil.rmtree(WAVE_ROOT)
    if WAVE_ROOT.exists() or WAVE_ROOT.is_symlink():
        raise RuntimeError("wave_003 still exists after deletion")
    print(
        json.dumps(
            {
                "status": "deleted",
                "deleted_root": scope["exact_root"],
                "deleted_file_count": len(observed),
                "incident_sha256": claimed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
