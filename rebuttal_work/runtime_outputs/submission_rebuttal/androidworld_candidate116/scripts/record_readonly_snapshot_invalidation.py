#!/usr/bin/env python3
"""Invalidate the v1 repair pre-snapshot without deleting historical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[5]
REPLACEMENT_HELPER = SCRIPT.parent / "readonly_snapshot_helper.py"
SCHEMA = "androidworld_checklist_repair_readonly_snapshot_invalidation/v1"


class InvalidationError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def binding(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise InvalidationError(f"bound file is missing: {path}")
    return {"path": relative(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def verify_self_hash(value: Mapping[str, Any], key: str) -> None:
    body = dict(value)
    claimed = body.pop(key, None)
    if claimed != object_sha256(body):
        raise InvalidationError(f"{key} mismatch")


def write_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise InvalidationError(f"refusing to overwrite invalidation incident: {path}") from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        raise
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-pre-snapshot", type=Path, required=True)
    parser.add_argument("--repair-id", required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=WORK_ROOT / "repair_generation/incidents/readonly_snapshot_invalidations",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    old_path = args.old_pre_snapshot.resolve()
    old = json.loads(old_path.read_text(encoding="utf-8"))
    if old.get("schema_version") != "androidworld_checklist_repair_readonly_snapshot/v1":
        raise InvalidationError("old pre-snapshot is not the affected v1 schema")
    verify_self_hash(old, "snapshot_sha256")
    if old.get("snapshot_sha256") != "4907901ab5e436f9177543e445d69c2b5dffee7b2c680891091278f7a00a48c1":
        raise InvalidationError("old pre-snapshot is not the known affected snapshot")
    old_helper_path = REPO_ROOT / old["snapshot_helper"]["path"]
    if binding(old_helper_path) != old["snapshot_helper"]:
        raise InvalidationError("old pre-snapshot helper binding changed")
    new_prelock = WORK_ROOT / f"repair_generation/freeze/{args.repair_id}.prelock.json"
    model_output = WORK_ROOT / f"repair_generation/waves/{args.repair_id}"
    if new_prelock.exists() or model_output.exists():
        raise InvalidationError("cannot attest pre-prelock/pre-model invalidation")
    incident = {
        "schema_version": SCHEMA,
        "status": "invalidated_before_repair_prelock",
        "repair_id": args.repair_id,
        "reason_code": "unbound_live_project_import_closure",
        "reason": (
            "v1 loaded live build_and_validate.py; only that file was bound while its live project "
            "import closure was not, so it is not an acceptable read-only trust anchor"
        ),
        "promotion_forbidden": True,
        "model_calls_started": False,
        "repair_prelock_created": False,
        "invalidated_pre_snapshot": binding(old_path)
        | {"snapshot_sha256": old["snapshot_sha256"]},
        "invalidated_helper": old["snapshot_helper"],
        "replacement_helper": binding(REPLACEMENT_HELPER),
        "required_replacement": {
            "outer_snapshot_schema": "androidworld_checklist_repair_readonly_snapshot/v2",
            "dedicated_helper_schema": "androidworld_checklist_repair_dedicated_readonly_snapshot/v1",
            "stdlib_only_helper": True,
            "new_create_once_pre_snapshot": True,
            "new_generation_prelock": True,
        },
        "preservation_policy": "the v1 pre-snapshot remains preserved invalidated historical evidence",
    }
    incident["incident_sha256"] = object_sha256(incident)
    output_root = args.output_root.resolve()
    output_root.relative_to(WORK_ROOT.resolve())
    output = output_root / f"{incident['incident_sha256']}.json"
    if args.dry_run:
        print(json.dumps({"status": "dry_run_pass", "incident": incident}, indent=2))
        return 0
    write_once(output, incident)
    print(
        json.dumps(
            {
                "status": incident["status"],
                "incident": binding(output) | {"incident_sha256": incident["incident_sha256"]},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InvalidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
