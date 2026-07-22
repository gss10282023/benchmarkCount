#!/usr/bin/env python3
"""Fail-closed, zero-LM preflight for an AppWorld campaign shard."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import traceback
from typing import Any


REQUIRED_API_DOCS = (
    "standard/api_docs.json",
    "function_calling/api_docs.json",
    "openapi/api_docs.json",
)
SCHEMA_REQUIREMENTS = {
    "amazon.db": {"users": {"track_browsing_history"}},
    "gmail.db": {"users": {"status"}, "users_fts": set()},
    "venmo.db": {"payment_requests_fts": set()},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        task_id = str(payload["task_id"])
        dataset_name = str(payload["dataset_name"])
        if dataset_name not in {"test_normal", "test_challenge"}:
            raise RuntimeError(f"invalid dataset at shard line {line_number}: {dataset_name}")
        cases.append({"task_id": task_id, "dataset_name": dataset_name})
    if not cases:
        raise RuntimeError("preflight shard is empty")
    if len({item["task_id"] for item in cases}) != len(cases):
        raise RuntimeError("preflight shard contains duplicate task IDs")
    return cases


def read_version(path: Path, label: str) -> str:
    if not path.is_file():
        raise RuntimeError(f"missing {label}: {path}")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError(f"empty {label}: {path}")
    return value


def validate_api_docs(data_root: Path) -> None:
    for relative in REQUIRED_API_DOCS:
        path = data_root / "api_docs" / relative
        if not path.is_file():
            raise RuntimeError(f"missing pre-generated AppWorld API docs: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not payload:
            raise RuntimeError(f"empty pre-generated AppWorld API docs: {path}")


def validate_base_db_schema(data_root: Path) -> None:
    for db_name, table_requirements in SCHEMA_REQUIREMENTS.items():
        path = data_root / "base_dbs" / db_name
        if not path.is_file():
            raise RuntimeError(f"missing AppWorld base DB: {path}")
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            tables = {
                str(row[0])
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            for table_name, required_columns in table_requirements.items():
                if table_name not in tables:
                    raise RuntimeError(f"{db_name} is missing required table {table_name}")
                if required_columns:
                    columns = {
                        str(row[1]) for row in connection.execute(f'PRAGMA table_info("{table_name}")')
                    }
                    missing = required_columns - columns
                    if missing:
                        raise RuntimeError(
                            f"{db_name}.{table_name} is missing required columns {sorted(missing)}"
                        )
        finally:
            connection.close()


def validate_task_metadata(data_root: Path, cases: list[dict[str, Any]], db_version: str) -> None:
    dataset_members: dict[str, set[str]] = {}
    for dataset_name in {str(item["dataset_name"]) for item in cases}:
        dataset_path = data_root / "datasets" / f"{dataset_name}.txt"
        if not dataset_path.is_file():
            raise RuntimeError(f"missing AppWorld dataset file: {dataset_path}")
        dataset_members[dataset_name] = {
            line.strip() for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()
        }
    for item in cases:
        task_id = str(item["task_id"])
        dataset_name = str(item["dataset_name"])
        if task_id not in dataset_members[dataset_name]:
            raise RuntimeError(f"task {task_id} is not in data/datasets/{dataset_name}.txt")
        task_root = data_root / "tasks" / task_id
        specs_path = task_root / "specs.json"
        if not specs_path.is_file() or not (task_root / "dbs").is_dir():
            raise RuntimeError(f"task {task_id} is incomplete under {task_root}")
        specs = json.loads(specs_path.read_text(encoding="utf-8"))
        if str(specs.get("db_version")) != db_version:
            raise RuntimeError(
                f"task {task_id} DB version={specs.get('db_version')!r}; expected {db_version!r}"
            )


def initialize_every_task(appworld_root: Path, cases: list[dict[str, Any]], shard_sha256: str) -> None:
    from appworld import AppWorld

    experiment_name = f"preflight_{shard_sha256[:16]}"
    lock_path = appworld_root / "experiments" / f".{experiment_name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        lock_handle.close()
        raise RuntimeError(f"another preflight already holds {lock_path}") from exc
    output_root = appworld_root / "experiments" / "outputs" / experiment_name
    if output_root.exists():
        shutil.rmtree(output_root)
    try:
        for item in cases:
            with AppWorld(
                task_id=str(item["task_id"]),
                experiment_name=experiment_name,
                load_ground_truth=False,
                raise_on_extra_parameters=True,
                random_seed=7,
            ):
                pass
    finally:
        if output_root.exists():
            shutil.rmtree(output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appworld-root", type=Path, required=True)
    parser.add_argument("--shard-file", type=Path, required=True)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()

    appworld_root = args.appworld_root.resolve()
    data_root = appworld_root / "data"
    os.environ["APPWORLD_ROOT"] = str(appworld_root)
    cases = read_cases(args.shard_file)
    data_version = read_version(data_root / "version.txt", "AppWorld data version")
    db_version = read_version(data_root / "base_dbs" / "version.txt", "AppWorld DB version")

    from appworld.common import constants

    if data_version != str(constants.DATA_VERSION):
        raise RuntimeError(
            f"AppWorld data={data_version}; installed code requires {constants.DATA_VERSION}"
        )
    if db_version != str(constants.DB_VERSION):
        raise RuntimeError(f"AppWorld DB={db_version}; installed code requires {constants.DB_VERSION}")
    if data_version not in {str(value) for value in constants.COMPATIBLE_DATA_VERSIONS}:
        raise RuntimeError(f"AppWorld data version {data_version} is not officially compatible")
    if db_version not in {str(value) for value in constants.COMPATIBLE_DB_VERSIONS}:
        raise RuntimeError(f"AppWorld DB version {db_version} is not officially compatible")

    validate_api_docs(data_root)
    validate_base_db_schema(data_root)
    validate_task_metadata(data_root, cases, db_version)
    shard_sha256 = sha256_file(args.shard_file)
    if not args.metadata_only:
        initialize_every_task(appworld_root, cases, shard_sha256)

    print(
        json.dumps(
            {
                "status": "passed",
                "lm_requests_made": 0,
                "task_count": len(cases),
                "data_version": data_version,
                "db_version": db_version,
                "shard_sha256": shard_sha256,
                "initialized_every_task": not args.metadata_only,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except BaseException:
        traceback.print_exc()
        exit_code = 1
    # AppWorld can leave expensive cyclic object cleanup for interpreter
    # shutdown after every task has already closed. The preflight has no
    # persistent in-process state, so exit immediately after flushing its
    # final zero-LM receipt.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
