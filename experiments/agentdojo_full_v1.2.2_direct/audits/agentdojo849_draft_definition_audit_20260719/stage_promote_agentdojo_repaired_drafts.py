#!/usr/bin/env python3
"""Stage and atomically promote outcome-blind AgentDojo checklist repairs."""

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

import yaml


EXPECTED_CASES = 849
EXPECTED_TARGETS = 460


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-final-audit", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--repaired-root", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--backup-root", type=Path)
    parser.add_argument("--use-existing-stage", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_mapping(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
    else:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping: {path}")
    return value


def read_audit(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            name = row["directory_name"]
            if name in rows:
                raise ValueError(f"duplicate audit row: {name}")
            rows[name] = row
    if len(rows) != EXPECTED_CASES:
        raise ValueError(f"expected {EXPECTED_CASES} audit rows, found {len(rows)}")
    return rows


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def write_json_atomic(value: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    audit = read_audit(args.original_final_audit)
    targets = {name for name, row in audit.items() if row.get("final_status") == "noncompliant"}
    if len(targets) != EXPECTED_TARGETS:
        raise ValueError(f"expected {EXPECTED_TARGETS} repair targets, found {len(targets)}")

    draft_names = {path.name for path in args.draft_root.iterdir() if path.is_dir()}
    if draft_names != set(audit):
        raise ValueError("draft root case set does not match the locked 849-case audit")
    repaired_names = {
        path.parent.name for path in args.repaired_root.glob("*/checklist.yaml")
    }
    if repaired_names != targets:
        raise ValueError(
            f"repaired set mismatch: expected={len(targets)} actual={len(repaired_names)} "
            f"missing={sorted(targets-repaired_names)[:5]} extra={sorted(repaired_names-targets)[:5]}"
        )

    if args.use_existing_stage:
        stage_names = {path.name for path in args.stage_root.iterdir() if path.is_dir()}
        if stage_names != set(audit):
            raise ValueError("existing stage root does not contain the locked 849-case set")
    else:
        if args.stage_root.exists() and any(args.stage_root.iterdir()):
            raise ValueError(f"stage root must be absent or empty: {args.stage_root}")
        args.stage_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for name in sorted(audit):
        original_dir = args.draft_root / name
        original_yaml = original_dir / "checklist.yaml"
        original_json = original_dir / "checklist.json"
        if sha256(original_yaml) != audit[name]["checklist_sha256"]:
            raise ValueError(f"locked original YAML hash mismatch: {name}")
        original_value = read_mapping(original_yaml)
        if original_value != read_mapping(original_json):
            raise ValueError(f"original YAML/JSON semantic mismatch: {name}")

        source_yaml = (
            args.repaired_root / name / "checklist.yaml" if name in targets else original_yaml
        )
        source_value = read_mapping(source_yaml)
        stage_dir = args.stage_root / name
        if args.use_existing_stage:
            if sha256(stage_dir / "checklist.yaml") != sha256(source_yaml):
                raise ValueError(f"existing staged YAML no longer matches its source: {name}")
        else:
            stage_dir.mkdir(parents=True, exist_ok=False)
            shutil.copyfile(source_yaml, stage_dir / "checklist.yaml")
            write_json_atomic(source_value, stage_dir / "checklist.json")
        if read_mapping(stage_dir / "checklist.yaml") != read_mapping(stage_dir / "checklist.json"):
            raise ValueError(f"staged YAML/JSON semantic mismatch: {name}")

        rows.append(
            {
                "case_unit_id": audit[name]["case_unit_id"],
                "directory_name": name,
                "targeted_for_repair": name in targets,
                "original_yaml_sha256": sha256(original_yaml),
                "original_json_sha256": sha256(original_json),
                "original_yaml_bytes": original_yaml.stat().st_size,
                "original_json_bytes": original_json.stat().st_size,
                "staged_yaml_sha256": sha256(stage_dir / "checklist.yaml"),
                "staged_json_sha256": sha256(stage_dir / "checklist.json"),
                "staged_yaml_bytes": (stage_dir / "checklist.yaml").stat().st_size,
                "staged_json_bytes": (stage_dir / "checklist.json").stat().st_size,
            }
        )

    if args.promote:
        if args.backup_root is None:
            raise ValueError("--backup-root is required with --promote")
        if args.backup_root.exists():
            raise ValueError(f"backup root already exists: {args.backup_root}")
        args.backup_root.mkdir(parents=True)
        by_name = {row["directory_name"]: row for row in rows}
        for name in sorted(targets):
            destination_dir = args.draft_root / name
            backup_dir = args.backup_root / name
            backup_dir.mkdir(parents=True)
            shutil.copyfile(destination_dir / "checklist.yaml", backup_dir / "checklist.yaml")
            shutil.copyfile(destination_dir / "checklist.json", backup_dir / "checklist.json")
        for name in sorted(targets):
            destination_dir = args.draft_root / name
            atomic_copy(args.stage_root / name / "checklist.yaml", destination_dir / "checklist.yaml")
            atomic_copy(args.stage_root / name / "checklist.json", destination_dir / "checklist.json")
            if sha256(destination_dir / "checklist.yaml") != by_name[name]["staged_yaml_sha256"]:
                raise ValueError(f"promoted YAML hash mismatch: {name}")
            if sha256(destination_dir / "checklist.json") != by_name[name]["staged_json_sha256"]:
                raise ValueError(f"promoted JSON hash mismatch: {name}")
        for name in sorted(set(audit) - targets):
            if sha256(args.draft_root / name / "checklist.yaml") != audit[name]["checklist_sha256"]:
                raise ValueError(f"protected non-target YAML changed: {name}")

    manifest = {
        "schema_version": "agentdojo849_draft_repair_promotion/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_outcomes_read": False,
        "score_artifacts_read": False,
        "case_count": len(rows),
        "repair_target_count": len(targets),
        "protected_unchanged_count": len(rows) - len(targets),
        "promoted": bool(args.promote),
        "original_final_audit": str(args.original_final_audit),
        "draft_root": str(args.draft_root),
        "repaired_root": str(args.repaired_root),
        "stage_root": str(args.stage_root),
        "backup_root": str(args.backup_root) if args.backup_root else None,
        "used_existing_stage": bool(args.use_existing_stage),
        "cases": rows,
    }
    write_json_atomic(manifest, args.manifest)
    print(
        json.dumps(
            {
                "case_count": len(rows),
                "repair_target_count": len(targets),
                "protected_unchanged_count": len(rows) - len(targets),
                "promoted": bool(args.promote),
                "manifest": str(args.manifest),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
