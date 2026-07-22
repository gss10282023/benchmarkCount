#!/usr/bin/env python3
"""Validate and re-manifest source-corrected AppWorld conflict-audit workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any


class RefreshError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_obj(value: Any) -> str:
    return sha_bytes(canonical(value))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def records(root: Path, *, omit: set[str] | None = None) -> list[dict[str, Any]]:
    omitted = omit or set()
    result: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in omitted:
            continue
        result.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha_file(path),
            }
        )
    return result


def public_modes(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        if path.is_symlink():
            raise RefreshError(f"symlink forbidden in adjudication workspace: {path}")
        if path.is_dir():
            path.chmod(0o755)
        elif path.is_file():
            path.chmod(0o644)
        else:
            raise RefreshError(f"special file forbidden in adjudication workspace: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--overlay-manifest", type=Path, required=True)
    args = parser.parse_args()
    audit_root = args.audit_root.resolve()
    overlay_path = args.overlay_manifest.resolve()
    index = load_json(audit_root / "index.json")
    overlay = load_json(overlay_path)
    if not isinstance(index, list) or len(index) != 68:
        raise RefreshError("audit index must contain 68 cases")
    overlay_cases = {item["case_unit_id"]: item for item in overlay.get("cases", [])}
    ids = [item["case_unit_id"] for item in index]
    if set(ids) != set(overlay_cases) or len(set(ids)) != 68:
        raise RefreshError("overlay/index case closure mismatch")

    root_records: list[dict[str, Any]] = []
    for item in index:
        case_id = str(item["case_unit_id"])
        workspace_value = Path(str(item["workspace"]))
        workspace = (
            workspace_value
            if workspace_value.is_absolute()
            else audit_root / workspace_value
        ).resolve()
        if audit_root not in workspace.parents or not workspace.is_dir():
            raise RefreshError(f"unsafe or missing workspace: {workspace}")
        if not (workspace / "HISTORICAL_V4_SOURCE_LOCK.json").is_file():
            raise RefreshError(f"{case_id}: historical v4 source lock missing")
        for record in overlay_cases[case_id]["files"]:
            path = workspace / record["path"]
            if (
                not path.is_file()
                or path.stat().st_size != record["size_bytes"]
                or sha_file(path) != record["sha256"]
            ):
                raise RefreshError(f"{case_id}: overlay file mismatch: {record['path']}")

        task_lock = load_json(workspace / "task_source_lock.json")
        receipt = load_json(workspace / "actual_run_receipt.json")
        if (
            task_lock.get("data_version") != "0.2.0"
            or task_lock.get("db_version") != "0.2.0"
            or any(
                row.get("actual_run_versions", {}).get("db_version") != "0.2.0"
                for row in receipt.get("agents", [])
            )
        ):
            raise RefreshError(f"{case_id}: source/run version binding mismatch")

        manifest_path = workspace / "WORKSPACE_MANIFEST.json"
        workspace_records = records(workspace, omit={"WORKSPACE_MANIFEST.json"})
        manifest = {
            "schema_version": "appworld68_record_level_conflict_workspace_manifest/v2_source020",
            "case_unit_id": case_id,
            "data_version": "0.2.0",
            "db_version": "0.2.0",
            "historical_v4_source_lock_retained": True,
            "v5_source_hotfix_record_retained": True,
            "file_count_excluding_this_manifest": len(workspace_records),
            "files": workspace_records,
            "files_sha256": sha_obj(workspace_records),
        }
        manifest_path.write_bytes(json_bytes(manifest))
        public_modes(workspace)
        root_records.append(
            {
                "case_unit_id": case_id,
                "workspace": workspace.relative_to(audit_root).as_posix(),
                "workspace_manifest_sha256": sha_file(manifest_path),
                "files_sha256": manifest["files_sha256"],
                "file_count_excluding_manifest": manifest[
                    "file_count_excluding_this_manifest"
                ],
            }
        )

    root_manifest = {
        "schema_version": "appworld68_record_level_conflict_audit/v2_source020",
        "case_count": len(root_records),
        "record_count": len(root_records) * 3,
        "data_version": "0.2.0",
        "db_version": "0.2.0",
        "overlay_manifest_sha256": sha_file(overlay_path),
        "workspaces": root_records,
        "workspaces_sha256": sha_obj(root_records),
        "historical_v4_scores_relabelled": False,
    }
    output = audit_root / "AUDIT_V2_SOURCE020_MANIFEST.json"
    output.write_bytes(json_bytes(root_manifest))
    output.chmod(0o644)
    print(
        json.dumps(
            {
                "status": "PASS",
                "case_count": len(root_records),
                "record_count": len(root_records) * 3,
                "workspaces_sha256": root_manifest["workspaces_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RefreshError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
