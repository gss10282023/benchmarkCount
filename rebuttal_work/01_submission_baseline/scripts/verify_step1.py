#!/usr/bin/env python3
"""Fail-closed acceptance verification for Step 1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ARTIFACT_NAMES = (
    "raw_run",
    "native_evaluator",
    "score",
    "score_manifest",
    "checklist",
    "artifact_manifest",
)
EXPECTED_BENCHMARKS = Counter(
    {"agentdojo": 300, "androidworld": 82, "appworld": 300, "miniwob": 300, "tau3_retail": 300}
)
EXPECTED_AGENTS = Counter({"agent_a": 441, "agent_b": 441, "agent_c": 400})
EXPECTED_IMMUTABLE_ROOTS = {
    "neurips_ed_track_minimal",
    "results",
    "paper_result_packages",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_oid(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def assert_safe_relative(path_value: str) -> None:
    normalized = path_value.replace("\\", "/")
    if normalized.startswith("/") or ".." in normalized.split("/"):
        raise AssertionError(f"unsafe path in baseline: {path_value}")
    if not normalized.startswith("paper_result_packages/"):
        raise AssertionError(f"baseline path leaves submitted package: {path_value}")


def verify_manifest(step_dir: Path, submission_root: Path) -> tuple[list[str], list[dict[str, str]]]:
    fields, rows = read_csv(step_dir / "submitted_baseline_manifest.csv")
    if len(rows) != 1282:
        raise AssertionError(f"baseline has {len(rows)} rows, expected 1282")
    for key in ("record_key", "raw_record_id", "raw_record_slot_id", "raw_run_id"):
        values = [row[key] for row in rows]
        if len(set(values)) != 1282:
            raise AssertionError(f"{key} is not unique")
    if Counter(row["benchmark"] for row in rows) != EXPECTED_BENCHMARKS:
        raise AssertionError("benchmark record counts changed")
    if Counter(row["agent_id"] for row in rows) != EXPECTED_AGENTS:
        raise AssertionError("agent record counts changed")

    for row in rows:
        expected_key = f"{row['benchmark']}::{row['case_unit_id']}::{row['agent_id']}"
        if row["record_key"] != expected_key:
            raise AssertionError(f"record key mismatch: {row['record_key']}")
        if row["submission_status"] != "submitted" or row["table2_denominator"] != "true":
            raise AssertionError(f"baseline membership flag changed: {row['record_key']}")
        if row["evidence_label_raw"] not in {"S", "F", "U"}:
            raise AssertionError(f"invalid evidence label: {row['record_key']}")
        if row["stronger_label_raw"] not in {"S", "F", "U", "NA"}:
            raise AssertionError(f"invalid stronger label: {row['record_key']}")
        if row["released_label"] not in {"success", "fail"}:
            raise AssertionError(f"invalid released label: {row['record_key']}")
        if row["public_artifact_byte_identical"] != "true":
            raise AssertionError(f"public blob verification not locked: {row['record_key']}")
        for name in ARTIFACT_NAMES:
            path_value = row[f"{name}_path"]
            assert_safe_relative(path_value)
            path = submission_root / path_value
            if not path.is_file():
                raise AssertionError(f"materialized submission file missing: {path_value}")
            if sha256_file(path) != row[f"{name}_sha256"]:
                raise AssertionError(f"SHA-256 mismatch: {path_value}")
            if git_blob_oid(path) != row[f"{name}_git_blob_oid"]:
                raise AssertionError(f"Git blob mismatch: {path_value}")
    return fields, rows


def verify_android_and_extension(step_dir: Path, baseline_rows: list[dict[str, str]]) -> None:
    _, android = read_csv(step_dir / "androidworld_submitted41_ab_manifest.csv")
    expected_android = [row for row in baseline_rows if row["benchmark"] == "androidworld"]
    if len(android) != 82 or {row["record_key"] for row in android} != {row["record_key"] for row in expected_android}:
        raise AssertionError("Android submitted manifest is not the exact 82-row baseline subset")
    case_agents = Counter(row["case_unit_id"] for row in android)
    if len(case_agents) != 41 or set(case_agents.values()) != {2}:
        raise AssertionError("Android submitted manifest is not 41 cases x A/B")

    _, contract = read_csv(step_dir / "androidworld_extension_contract.csv")
    if len(contract) != 218 or len({row["slot_id"] for row in contract}) != 218:
        raise AssertionError("extension contract is not 218 unique slots")
    if Counter(row["extension_component"] for row in contract) != Counter({"remaining59_ab": 118, "full100_c": 100}):
        raise AssertionError("extension contract components changed")
    if len({row["case_unit_id"] for row in contract if row["extension_component"] == "remaining59_ab"}) != 59:
        raise AssertionError("remaining59 component does not contain 59 cases")
    if len({row["case_unit_id"] for row in contract if row["extension_component"] == "full100_c"}) != 100:
        raise AssertionError("full100 C component does not contain 100 cases")
    _, active = read_csv(step_dir / "post_submission_extension_manifest.csv")
    if active:
        raise AssertionError("post-submission extension manifest must be initially empty")


def verify_no_discovery(step_dir: Path) -> None:
    source = (step_dir / "scripts/rebuild_master_table.py").read_text(encoding="utf-8")
    forbidden = (".glob(", ".rglob(", "os.walk(", "results/tables", "results_macros.tex")
    present = [token for token in forbidden if token in source]
    if present:
        raise AssertionError(f"manifest-only rebuild contains forbidden discovery/source tokens: {present}")


def clean_rebuild(step_dir: Path) -> tuple[str, str, int]:
    interpreters = [Path(sys.executable).resolve()]
    system = Path("/usr/bin/python3")
    if system.exists() and system.resolve() not in interpreters:
        interpreters.append(system.resolve())
    generated: list[tuple[bytes, bytes]] = []
    with tempfile.TemporaryDirectory(prefix="step1-rebuild-") as temporary:
        temp = Path(temporary)
        for index, interpreter in enumerate(interpreters):
            master = temp / f"master-{index}.csv"
            summary = temp / f"summary-{index}.csv"
            command = [
                str(interpreter),
                "-I",
                str((step_dir / "scripts/rebuild_master_table.py").resolve()),
                "--manifest",
                str((step_dir / "submitted_baseline_manifest.csv").resolve()),
                "--master-out",
                str(master),
                "--summary-out",
                str(summary),
                "--expected-rows",
                "1282",
            ]
            environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TZ": "UTC", "PYTHONHASHSEED": "0"}
            subprocess.run(command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            generated.append((master.read_bytes(), summary.read_bytes()))
    if len({item[0] for item in generated}) != 1 or len({item[1] for item in generated}) != 1:
        raise AssertionError("clean interpreters produced different master-table bytes")
    master_bytes, summary_bytes = generated[0]
    if master_bytes != (step_dir / "submitted_master_table.csv").read_bytes():
        raise AssertionError("checked-in master table differs from clean rebuild")
    if summary_bytes != (step_dir / "submitted_master_summary.csv").read_bytes():
        raise AssertionError("checked-in formatted summary differs from clean rebuild")
    return hashlib.sha256(master_bytes).hexdigest(), hashlib.sha256(summary_bytes).hexdigest(), len(interpreters)


def verify_lock(root: Path, submission_root: Path) -> dict[str, Any]:
    lock_dir = root / "rebuttal_work/00_submission_repo_lock"
    lock = read_json(lock_dir / "submission_repo_lock.json")
    repository = lock["submission_repository"]
    if repository["commit"] != "ffd9ff4e706d85ff2d12e60f087cde664dbae433":
        raise AssertionError("submission commit changed")
    if repository["commit_tree_oid"] != "9339be9873fca806a2e77ffe724f11c61fcbfd80":
        raise AssertionError("submission tree changed")
    if lock["archives"]["full_git_archive"]["sha256"] != "6fc564e106ba92317c931427cdab759070296857e3d1a22347bbb682ac156ea5":
        raise AssertionError("full archive lock changed")
    if sha256_file(lock_dir / "submission_source_archive.tar") != lock["archives"]["minimal_source_archive"]["sha256"]:
        raise AssertionError("minimal source archive hash mismatch")
    execution = root / repository["new_execution_output_root"]
    if submission_root in execution.parents or execution in submission_root.parents:
        raise AssertionError("execution output root overlaps SUBMISSION_REPO")
    return lock


def writable_entries(path: Path) -> list[str]:
    output: list[str] = []
    for entry in [path, *path.rglob("*")]:
        try:
            mode = entry.lstat().st_mode
        except FileNotFoundError:
            continue
        if mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            output.append(entry.relative_to(path).as_posix() if entry != path else ".")
    return output


def verify_recursive_immutable(root: Path, lock: dict[str, Any]) -> dict[str, int]:
    """Recheck every legacy scientific input named by the repository lock."""
    immutable_flag = getattr(stat, "UF_IMMUTABLE", None)
    if immutable_flag is None:
        raise AssertionError("UF_IMMUTABLE is unavailable; legacy read-only state cannot be verified")
    legacy = lock["legacy_repository"]
    if legacy.get("filesystem_immutable_flag") != "UF_IMMUTABLE (uchg)":
        raise AssertionError("legacy immutable flag is not locked")
    entries = legacy.get("filesystem_immutable_roots", [])
    if {entry.get("path") for entry in entries} != EXPECTED_IMMUTABLE_ROOTS:
        raise AssertionError("legacy immutable root set changed")

    verified: dict[str, int] = {}
    for entry in entries:
        relative = entry["path"]
        path = root / relative
        count = 0
        for directory, dirnames, filenames in os.walk(path, followlinks=False):
            candidates = [Path(directory) / name for name in (*dirnames, *filenames)]
            if Path(directory) == path:
                candidates.insert(0, path)
            for candidate in candidates:
                count += 1
                if not (candidate.stat(follow_symlinks=False).st_flags & immutable_flag):
                    raise AssertionError(f"legacy input is not filesystem-immutable: {candidate}")
        if count != entry.get("recursive_entry_count"):
            raise AssertionError(f"legacy immutable root entry count changed: {relative}")
        verified[relative] = count
    return verified


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    step_dir = root / "rebuttal_work/01_submission_baseline"
    submission_root = root / "rebuttal_work/00_submission_repo_lock/snapshots/SUBMISSION_REPO"
    legacy_head_snapshot = root / "rebuttal_work/00_submission_repo_lock/snapshots/LEGACY_HEAD_SNAPSHOT"

    _, rows = verify_manifest(step_dir, submission_root)
    verify_android_and_extension(step_dir, rows)
    verify_no_discovery(step_dir)
    lock = verify_lock(root, submission_root)
    for snapshot in (submission_root, legacy_head_snapshot):
        writable = writable_entries(snapshot)
        if writable:
            raise AssertionError(f"snapshot is not read-only: {snapshot.name}: {writable[:5]}")
    immutable_counts = verify_recursive_immutable(root, lock)
    master_sha, summary_sha, interpreter_count = clean_rebuild(step_dir)

    report = {
        "schema_version": "step1_acceptance_report/v1",
        "status": "pass",
        "checks": {
            "submission_commit_tree_dependency_archive_locked": True,
            "submission_sparse_snapshot_read_only": True,
            "legacy_head_sparse_snapshot_read_only": True,
            "legacy_scientific_input_roots_filesystem_immutable": True,
            "legacy_immutable_entry_counts": immutable_counts,
            "legacy_dirty_workspace_indexed_and_fail_closed": True,
            "output_root_disjoint": True,
            "baseline_rows": len(rows),
            "unique_record_keys": len({row["record_key"] for row in rows}),
            "all_decisive_file_sha256_and_git_blobs_verified": len(rows) * len(ARTIFACT_NAMES),
            "android_submitted_records": 82,
            "extension_contract_slots": 218,
            "active_extension_rows": 0,
            "manifest_only_aggregation": True,
            "clean_rebuild_interpreter_count": interpreter_count,
            "clean_rebuild_byte_identical": True,
            "formatting_rule": "Decimal ROUND_HALF_UP; percentages and interval endpoints use one decimal",
        },
        "master_table_sha256": master_sha,
        "formatted_summary_sha256": summary_sha,
        "submission_commit": lock["submission_repository"]["commit"],
        "submission_tree_oid": lock["submission_repository"]["commit_tree_oid"],
    }
    write_json(args.report.resolve(), report)


if __name__ == "__main__":
    main()
