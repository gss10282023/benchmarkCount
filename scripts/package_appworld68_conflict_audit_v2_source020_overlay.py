#!/usr/bin/env python3
"""Package the AppWorld-68 v5/0.2.0 source overlay for conflict adjudication."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
V4 = (
    ROOT
    / "experiments"
    / "appworld_test_normal_68_system_design_v4_runtime_semantics_gpt54_high_v1"
)
V5 = (
    ROOT
    / "experiments"
    / "appworld_test_normal_68_system_design_v5_data_0_2_0_hotfix_gpt54_high_v1"
)
OUTPUT = ROOT / "transfer/appworld68_conflict_audit_v2_source020_overlay"
EXPECTED_CASE_IDS_SHA256 = (
    "2b54ce295ac44589ff9ceb689ea52daf69c64dfb0c76118db34af2b3e1da7c96"
)
EXPECTED_DATA_BUNDLE_SHA256 = (
    "c9299e6cafe92bce4592a3c117c047c973d1554a667c21dd81537e78ab2f532e"
)


class PackageError(RuntimeError):
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
    return sha_bytes(path.read_bytes())


def sha_obj(value: Any) -> str:
    return sha_bytes(canonical(value))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_records(root: Path, *, omit: set[str] | None = None) -> list[dict[str, Any]]:
    omitted = omit or set()
    records: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in omitted:
            continue
        records.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha_file(path),
            }
        )
    return records


def copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise PackageError(f"missing or unsafe source file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def build(destination: Path) -> dict[str, Any]:
    if destination.exists():
        raise PackageError(f"refusing to overwrite: {destination}")
    v5_manifest = load_json(V5 / "experiment_manifest.json")
    ids = list(v5_manifest.get("scope", {}).get("case_ids", []))
    if len(ids) != 68 or len(set(ids)) != 68 or sha_obj(ids) != EXPECTED_CASE_IDS_SHA256:
        raise PackageError("v5 cohort drift")
    source_lock = load_json(V5 / "task_source_lock.json")
    if (
        source_lock.get("data_version") != "0.2.0"
        or source_lock.get("db_version") != "0.2.0"
        or source_lock.get("official_data_bundle_sha256")
        != EXPECTED_DATA_BUNDLE_SHA256
    ):
        raise PackageError("v5 source lock drift")

    case_records: list[dict[str, Any]] = []
    for case_id in ids:
        v4_packet = V4 / "case_packets/appworld" / case_id
        v5_packet = V5 / "case_packets/appworld" / case_id
        v5_result = V5 / "results" / case_id
        case_out = destination / case_id
        current_raw_manifest = load_json(v5_packet / "raw_case_manifest.json")
        historical_specs = load_json(v4_packet / "raw_case/official/specs.json")
        current_specs = load_json(v5_packet / "raw_case/official/specs.json")
        if historical_specs.get("db_version") != "0.1.0":
            raise PackageError(f"{case_id}: historical v4 version drift")
        if current_specs.get("db_version") != "0.2.0":
            raise PackageError(f"{case_id}: current v5 version drift")

        copy_file(v5_packet / "case_packet.md", case_out / "case_packet.md")
        copy_file(v5_result / "checklist.yaml", case_out / "checklist.yaml")
        copy_file(v5_result / "checklist.json", case_out / "checklist.json")
        copy_file(
            v5_packet / "raw_case_manifest.json", case_out / "raw_case_manifest.json"
        )
        copy_file(
            v5_result / "repair_record.json", case_out / "source_hotfix_record.json"
        )
        shutil.copytree(v5_packet / "raw_case/official", case_out / "official")

        case_task_lock = current_raw_manifest.get("task_source_lock")
        if not isinstance(case_task_lock, dict):
            raise PackageError(f"{case_id}: task source lock missing")
        task_source_lock = {
            "schema_version": "appworld_conflict_audit_task_source_lock/v2",
            "case_unit_id": case_id,
            "authority": "official_appworld_data_0_2_0_bundle",
            **case_task_lock,
        }
        (case_out / "task_source_lock.json").write_bytes(json_bytes(task_source_lock))

        official_records = [
            {
                "path": relative,
                "sha256": digest,
            }
            for relative, digest in sorted(
                current_raw_manifest.get("sha256_per_file", {}).items()
            )
            if relative.startswith("official/")
        ]
        source_lock_record = {
            "schema_version": "appworld68_record_level_conflict_source_lock/v2_data_0_2_0",
            "case_unit_id": case_id,
            "authoritative_current_source": {
                "data_version": "0.2.0",
                "db_version": "0.2.0",
                "runtime_code_version": source_lock["runtime_code_version"],
                "runtime_commit": source_lock["runtime_commit"],
                "official_data_bundle_url": source_lock["official_data_bundle_url"],
                "official_data_bundle_sha256": source_lock[
                    "official_data_bundle_sha256"
                ],
                "task_files_sha256": case_task_lock["task_files_sha256"],
                "official_files": official_records,
                "case_packet_sha256": sha_file(v5_packet / "case_packet.md"),
                "checklist_json_sha256": sha_file(v5_result / "checklist.json"),
                "checklist_yaml_sha256": sha_file(v5_result / "checklist.yaml"),
                "raw_case_manifest_sha256": sha_file(
                    v5_packet / "raw_case_manifest.json"
                ),
            },
            "historical_superseded_v4_source": {
                "data_version": "0.1.0",
                "db_version": "0.1.0",
                "case_packet_sha256": sha_file(v4_packet / "case_packet.md"),
                "checklist_json_sha256": sha_file(
                    V4 / "results" / case_id / "checklist.json"
                ),
                "checklist_yaml_sha256": sha_file(
                    V4 / "results" / case_id / "checklist.yaml"
                ),
                "raw_case_manifest_sha256": sha_file(
                    v4_packet / "raw_case_manifest.json"
                ),
                "specs_sha256": sha_file(v4_packet / "raw_case/official/specs.json"),
                "historical_score_set_status": "invalid_wrong_source_version_not_relabelled",
            },
            "native_evaluator_non_import_semantics_changed_from_v4": case_id
            == "bde252e_2",
            "outcome_or_released_result_inputs_read": [],
        }
        (case_out / "SOURCE_LOCK.json").write_bytes(json_bytes(source_lock_record))

        records = file_records(case_out)
        case_records.append(
            {
                "case_unit_id": case_id,
                "file_count": len(records),
                "files_sha256": sha_obj(records),
                "files": records,
            }
        )

    manifest = {
        "schema_version": "appworld68_conflict_audit_source020_overlay/v1",
        "created_date": "2026-07-22",
        "case_count": len(case_records),
        "case_ids_sha256": EXPECTED_CASE_IDS_SHA256,
        "official_data_bundle_sha256": EXPECTED_DATA_BUNDLE_SHA256,
        "source_bundle": V5.relative_to(ROOT).as_posix(),
        "historical_bundle": V4.relative_to(ROOT).as_posix(),
        "cases": case_records,
        "cases_sha256": sha_obj(case_records),
        "outcome_or_released_result_inputs_read": [],
    }
    (destination / "OVERLAY_MANIFEST.json").write_bytes(json_bytes(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output == ROOT or output == ROOT / "transfer":
        raise PackageError("unsafe broad output root")
    if output.exists():
        raise PackageError(f"refusing to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage_parent = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent)
    )
    stage = stage_parent / output.name
    try:
        manifest = build(stage)
        os.replace(stage, output)
    finally:
        if stage_parent.exists():
            shutil.rmtree(stage_parent, ignore_errors=True)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output_root": str(output),
                "case_count": manifest["case_count"],
                "cases_sha256": manifest["cases_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PackageError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
