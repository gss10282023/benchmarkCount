#!/usr/bin/env python3
"""Promote staged AgentDojo YAML/JSON files using only a locked hash manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_CASES = 849
EXPECTED_TARGETS = 460


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_copy(source: Path, destination: Path) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = manifest.get("cases")
    if not isinstance(rows, list) or len(rows) != EXPECTED_CASES:
        raise ValueError(f"manifest must contain {EXPECTED_CASES} cases")
    targets = [row for row in rows if row.get("targeted_for_repair")]
    if len(targets) != EXPECTED_TARGETS:
        raise ValueError(f"manifest must contain {EXPECTED_TARGETS} targets")
    if args.backup_root.exists():
        raise ValueError(f"backup root already exists: {args.backup_root}")

    for row in rows:
        name = row["directory_name"]
        local_dir = args.draft_root / name
        stage_dir = args.stage_root / name
        if sha256(local_dir / "checklist.yaml") != row["original_yaml_sha256"]:
            raise ValueError(f"local original YAML hash mismatch: {name}")
        if sha256(local_dir / "checklist.json") != row["original_json_sha256"]:
            raise ValueError(f"local original JSON hash mismatch: {name}")
        expected_yaml = (
            row["staged_yaml_sha256"]
            if row.get("targeted_for_repair")
            else row["original_yaml_sha256"]
        )
        expected_json = (
            row["staged_json_sha256"]
            if row.get("targeted_for_repair")
            else row["original_json_sha256"]
        )
        if sha256(stage_dir / "checklist.yaml") != expected_yaml:
            raise ValueError(f"staged YAML hash mismatch: {name}")
        if sha256(stage_dir / "checklist.json") != expected_json:
            raise ValueError(f"staged JSON hash mismatch: {name}")

    args.backup_root.mkdir(parents=True)
    for row in targets:
        name = row["directory_name"]
        local_dir = args.draft_root / name
        backup_dir = args.backup_root / name
        backup_dir.mkdir(parents=True)
        shutil.copyfile(local_dir / "checklist.yaml", backup_dir / "checklist.yaml")
        shutil.copyfile(local_dir / "checklist.json", backup_dir / "checklist.json")

    for row in targets:
        name = row["directory_name"]
        local_dir = args.draft_root / name
        stage_dir = args.stage_root / name
        atomic_copy(stage_dir / "checklist.yaml", local_dir / "checklist.yaml")
        atomic_copy(stage_dir / "checklist.json", local_dir / "checklist.json")

    for row in rows:
        name = row["directory_name"]
        local_dir = args.draft_root / name
        expected_yaml = (
            row["staged_yaml_sha256"]
            if row.get("targeted_for_repair")
            else row["original_yaml_sha256"]
        )
        expected_json = (
            row["staged_json_sha256"]
            if row.get("targeted_for_repair")
            else row["original_json_sha256"]
        )
        if sha256(local_dir / "checklist.yaml") != expected_yaml:
            raise ValueError(f"final local YAML hash mismatch: {name}")
        if sha256(local_dir / "checklist.json") != expected_json:
            raise ValueError(f"final local JSON hash mismatch: {name}")

    receipt = {
        "schema_version": "agentdojo849_local_hash_manifest_promotion/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "repair_target_count": len(targets),
        "protected_unchanged_count": len(rows) - len(targets),
        "agent_outcomes_read": False,
        "score_artifacts_read": False,
        "source_manifest": str(args.manifest),
        "source_manifest_sha256": sha256(args.manifest),
        "stage_root": str(args.stage_root),
        "draft_root": str(args.draft_root),
        "backup_root": str(args.backup_root),
        "status": "promoted_and_verified",
    }
    write_json(args.receipt, receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
