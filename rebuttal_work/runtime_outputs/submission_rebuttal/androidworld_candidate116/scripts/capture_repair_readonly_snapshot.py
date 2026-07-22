#!/usr/bin/env python3
"""Capture a v2 repair read-only snapshot with a stdlib-only trust anchor."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[5]
HELPER = SCRIPT.parent / "readonly_snapshot_helper.py"
OUTER_SCHEMA = "androidworld_checklist_repair_readonly_snapshot/v2"
INVALIDATION_SCHEMA = "androidworld_checklist_repair_readonly_snapshot_invalidation/v1"


class CaptureError(RuntimeError):
    """Raised when the v2 snapshot cannot be proven."""


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


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise CaptureError(f"path is outside repository: {path}") from exc


def file_binding(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise CaptureError(f"bound file is missing: {path}")
    return {
        "path": repo_relative(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def verify_self_hash(value: Mapping[str, Any], key: str, label: str) -> None:
    claimed = value.get(key)
    body = dict(value)
    body.pop(key, None)
    observed = object_sha256(body)
    if claimed != observed:
        raise CaptureError(f"{label} self-hash mismatch")


def add_self_hash(value: Mapping[str, Any], key: str) -> dict[str, Any]:
    result = dict(value)
    result.pop(key, None)
    result[key] = object_sha256(result)
    return result


def load_helper(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("candidate116_dedicated_readonly_helper", path)
    if spec is None or spec.loader is None:
        raise CaptureError(f"cannot load dedicated read-only helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("readonly_operation_snapshot", "readonly_snapshot_core", "compare_gate"):
        if not callable(getattr(module, name, None)):
            raise CaptureError(f"dedicated read-only helper lacks {name}")
    return module


def load_invalidation(path: Path) -> dict[str, Any]:
    path = path.resolve()
    try:
        path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise CaptureError("invalidation incident must be inside candidate116") from exc
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != INVALIDATION_SCHEMA:
        raise CaptureError("invalidation incident schema is invalid")
    verify_self_hash(value, "incident_sha256", "invalidation incident")
    if path.stem != value["incident_sha256"]:
        raise CaptureError("invalidation incident filename is not its content address")
    if (
        value.get("status") != "invalidated_before_repair_prelock"
        or value.get("promotion_forbidden") is not True
        or value.get("model_calls_started") is not False
    ):
        raise CaptureError("invalidation incident does not prove a pre-call invalidation")
    return file_binding(path) | {"incident_sha256": value["incident_sha256"]}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invalidated-pre-snapshot-incident", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def capture(phase: str, invalidation_path: Path) -> dict[str, Any]:
    helper = load_helper(HELPER)
    readonly = helper.readonly_operation_snapshot(
        phase=phase, repo_root=REPO_ROOT, work_root=WORK_ROOT
    )
    core = helper.readonly_snapshot_core(readonly)
    record = {
        "schema_version": OUTER_SCHEMA,
        "phase": phase,
        "snapshot_helper": file_binding(HELPER),
        "supersedes_invalidated_pre_snapshot": load_invalidation(invalidation_path),
        "readonly_snapshot": readonly,
        "readonly_core_sha256": object_sha256(core),
        "trust_policy": "snapshot semantics come exclusively from the bound stdlib-only helper",
    }
    return add_self_hash(record, "snapshot_sha256")


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
            raise CaptureError(f"refusing to overwrite read-only snapshot: {path}") from exc
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


def main() -> int:
    args = parse_args()
    record = capture(args.phase, args.invalidated_pre_snapshot_incident)
    output = args.output.resolve()
    try:
        output.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise CaptureError("repair read-only snapshot output must be inside candidate116") from exc
    result = {
        "status": "dry_run_pass" if args.dry_run else "captured",
        "phase": args.phase,
        "snapshot_sha256": record["snapshot_sha256"],
        "root_count": len(record["readonly_snapshot"]["roots"]),
        "output": str(output),
    }
    if not args.dry_run:
        write_once(output, record)
        result["snapshot"] = file_binding(output) | {
            "snapshot_sha256": record["snapshot_sha256"]
        }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CaptureError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
