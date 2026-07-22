#!/usr/bin/env python3
"""Inventory, download, and verify selected public DeepSWE v1.1 cohorts.

The input is the official post-lock ``trials.json`` release index.  The script
selects the three model/effort cohorts requested for the paper, mirrors every
published trajectory, patch, agent log, and verifier file, and writes a
content-length plus SHA-256 manifest.  Downloads are resumable and idempotent.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


COHORTS = (
    ("gpt-5-5", "xhigh"),
    ("claude-fable-5", "xhigh"),
    ("gemini-3-1-pro-preview", "high"),
)
EXPECTED_TASKS = 113
EXPECTED_ROLLOUTS_PER_COHORT = 452
USER_AGENT = "DeepSWE-v1.1-public-artifact-mirror/1.0"


@dataclass(frozen=True)
class RemoteObject:
    cohort: str
    trial_name: str
    task_name: str
    relative_path: str
    url: str
    destination: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("inventory", "download", "verify"), required=True)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=5)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cohort_id(model: str, effort: str) -> str:
    return f"{model}__{effort}"


def select_rows(index: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw_rows = index.get("rows")
    if not isinstance(raw_rows, list):
        raise RuntimeError("trials index has no rows list")
    selected: dict[str, list[dict[str, Any]]] = {}
    for model, effort in COHORTS:
        key = cohort_id(model, effort)
        rows = [
            dict(row)
            for row in raw_rows
            if isinstance(row, dict)
            and row.get("source") == "deep-swe"
            and row.get("eval_scope") == "full"
            and row.get("model") == model
            and row.get("reasoning_effort") == effort
        ]
        tasks = {str(row.get("task_name") or "") for row in rows}
        trials = {str(row.get("trial_name") or "") for row in rows}
        if len(rows) != EXPECTED_ROLLOUTS_PER_COHORT:
            raise RuntimeError(f"{key}: expected 452 rows, found {len(rows)}")
        if len(tasks) != EXPECTED_TASKS or "" in tasks:
            raise RuntimeError(f"{key}: expected 113 nonempty task names, found {len(tasks)}")
        if len(trials) != len(rows) or "" in trials:
            raise RuntimeError(f"{key}: trial names are missing or duplicated")
        selected[key] = sorted(rows, key=lambda row: str(row["trial_name"]))
    return selected


def published_paths(row: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    if row.get("has_trajectory") is True:
        paths.append("agent/trajectory.json")
    if row.get("has_model_patch") is True:
        paths.append("artifacts/model.patch")
    if row.get("has_agent_log") is True:
        paths.append("agent/mini-swe-agent.txt")
    verifier_files = row.get("verifier_files")
    if isinstance(verifier_files, list):
        for name in verifier_files:
            normalized = str(name).lstrip("/")
            if normalized:
                paths.append(f"verifier/{normalized}")
    if row.get("has_verifier_output") is True and "verifier/test-stdout.txt" not in paths:
        paths.append("verifier/test-stdout.txt")
    return list(dict.fromkeys(paths))


def build_objects(
    selected: dict[str, list[dict[str, Any]]],
    release: dict[str, Any],
    output_root: Path,
) -> list[RemoteObject]:
    base = str(release.get("artifact_base_url") or "").rstrip("/")
    prefix = str(release.get("artifact_key_prefix") or "").strip("/")
    if not base.startswith("https://") or not prefix:
        raise RuntimeError("release manifest has invalid artifact origin/prefix")
    objects: list[RemoteObject] = []
    seen: set[tuple[str, str, str]] = set()
    for cohort, rows in selected.items():
        for row in rows:
            trial_name = str(row["trial_name"])
            task_name = str(row["task_name"])
            for relative_path in published_paths(row):
                identity = (cohort, trial_name, relative_path)
                if identity in seen:
                    continue
                seen.add(identity)
                quoted_trial = urllib.parse.quote(trial_name, safe="-_.~")
                quoted_path = "/".join(
                    urllib.parse.quote(part, safe="-_.~")
                    for part in relative_path.split("/")
                )
                objects.append(
                    RemoteObject(
                        cohort=cohort,
                        trial_name=trial_name,
                        task_name=task_name,
                        relative_path=relative_path,
                        url=f"{base}/{prefix}/{quoted_trial}/{quoted_path}",
                        destination=(
                            output_root / "cohorts" / cohort / "trials" / trial_name / relative_path
                        ),
                    )
                )
    return sorted(objects, key=lambda item: (item.cohort, item.trial_name, item.relative_path))


def request_with_retries(
    request: urllib.request.Request,
    *,
    timeout: float,
    retries: int,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(min(8.0, 0.5 * (2**attempt)))
    assert last_error is not None
    raise last_error


def head_one(item: RemoteObject, *, timeout: float, retries: int) -> dict[str, Any]:
    request = urllib.request.Request(
        item.url,
        method="HEAD",
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    try:
        with request_with_retries(request, timeout=timeout, retries=retries) as response:
            length = response.headers.get("Content-Length")
            return {
                "cohort": item.cohort,
                "trial_name": item.trial_name,
                "task_name": item.task_name,
                "relative_path": item.relative_path,
                "url": item.url,
                "status": int(response.status),
                "content_length": int(length) if length is not None else None,
                "content_type": response.headers.get("Content-Type"),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    except urllib.error.HTTPError as exc:
        return {
            "cohort": item.cohort,
            "trial_name": item.trial_name,
            "task_name": item.task_name,
            "relative_path": item.relative_path,
            "url": item.url,
            "status": int(exc.code),
            "content_length": None,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "cohort": item.cohort,
            "trial_name": item.trial_name,
            "task_name": item.task_name,
            "relative_path": item.relative_path,
            "url": item.url,
            "status": None,
            "content_length": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def parallel_map(
    items: list[RemoteObject],
    function: Any,
    *,
    workers: int,
    label: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    lock = threading.Lock()
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(function, item): item for item in items}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            with lock:
                results.append(result)
                completed += 1
                if completed % 250 == 0 or completed == len(items):
                    failures = sum(row.get("status") not in (200, 206, "downloaded", "existing") for row in results)
                    print(
                        f"{label}: {completed}/{len(items)} complete; failures={failures}",
                        flush=True,
                    )
    return results


def load_inventory(path: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (str(row["cohort"]), str(row["trial_name"]), str(row["relative_path"]))
        rows[key] = row
    return rows


def download_one(
    item: RemoteObject,
    *,
    expected_size: int,
    timeout: float,
    retries: int,
) -> dict[str, Any]:
    destination = item.destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size == expected_size:
        return {
            "cohort": item.cohort,
            "trial_name": item.trial_name,
            "task_name": item.task_name,
            "relative_path": item.relative_path,
            "status": "existing",
            "size_bytes": expected_size,
            "sha256": sha256_file(destination),
        }

    partial = destination.with_name(destination.name + ".part")
    start = partial.stat().st_size if partial.is_file() else 0
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    if start:
        headers["Range"] = f"bytes={start}-"
    request = urllib.request.Request(item.url, headers=headers)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                append = start > 0 and int(response.status) == 206
                if start > 0 and not append:
                    start = 0
                with partial.open("ab" if append else "wb") as handle:
                    shutil.copyfileobj(response, handle, length=1024 * 1024)
            if partial.stat().st_size != expected_size:
                raise IOError(
                    f"size mismatch: expected {expected_size}, got {partial.stat().st_size}"
                )
            os.replace(partial, destination)
            return {
                "cohort": item.cohort,
                "trial_name": item.trial_name,
                "task_name": item.task_name,
                "relative_path": item.relative_path,
                "status": "downloaded",
                "size_bytes": expected_size,
                "sha256": sha256_file(destination),
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            start = partial.stat().st_size if partial.is_file() else 0
            headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
            if start:
                headers["Range"] = f"bytes={start}-"
            request = urllib.request.Request(item.url, headers=headers)
            if attempt + 1 < retries:
                time.sleep(min(8.0, 0.5 * (2**attempt)))
    return {
        "cohort": item.cohort,
        "trial_name": item.trial_name,
        "task_name": item.task_name,
        "relative_path": item.relative_path,
        "status": "failed",
        "expected_size": expected_size,
        "partial_size": partial.stat().st_size if partial.is_file() else 0,
        "error": f"{type(last_error).__name__}: {last_error}",
    }


def summarize_selected(selected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        cohort: {
            "trial_count": len(rows),
            "task_count": len({str(row["task_name"]) for row in rows}),
            "trajectory_count": sum(row.get("has_trajectory") is True for row in rows),
            "model_patch_count": sum(row.get("has_model_patch") is True for row in rows),
            "agent_log_count": sum(row.get("has_agent_log") is True for row in rows),
            "verifier_output_count": sum(row.get("has_verifier_output") is True for row in rows),
            "errored_trial_count": sum(row.get("errored") is True for row in rows),
        }
        for cohort, rows in selected.items()
    }


def main() -> int:
    args = parse_args()
    if args.workers < 1 or args.retries < 1 or args.timeout_seconds <= 0:
        raise RuntimeError("workers, retries, and timeout must be positive")
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    release = read_json(args.release)
    index = read_json(args.index)
    selected = select_rows(index)
    objects = build_objects(selected, release, output_root)
    write_json(
        output_root / "selected_cohorts.json",
        {
            "schema_version": "deepswe_v1_1_selected_public_cohorts/v1",
            "release": release,
            "cohorts": summarize_selected(selected),
            "expected_object_count": len(objects),
        },
    )
    for cohort, rows in selected.items():
        write_jsonl(output_root / "cohorts" / cohort / "selected_trials.jsonl", rows)

    inventory_path = output_root / "remote_object_inventory.jsonl"
    if args.mode == "inventory":
        rows = parallel_map(
            objects,
            lambda item: head_one(
                item, timeout=args.timeout_seconds, retries=args.retries
            ),
            workers=args.workers,
            label="HEAD",
        )
        rows.sort(key=lambda row: (row["cohort"], row["trial_name"], row["relative_path"]))
        write_jsonl(inventory_path, rows)
        status_counts = Counter(str(row.get("status")) for row in rows)
        known_bytes = sum(int(row.get("content_length") or 0) for row in rows)
        summary = {
            "schema_version": "deepswe_v1_1_remote_inventory_summary/v1",
            "object_count": len(rows),
            "status_counts": dict(status_counts),
            "known_content_bytes": known_bytes,
            "all_objects_available": status_counts == Counter({"200": len(rows)}),
        }
        write_json(output_root / "remote_inventory_summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
        return 0 if summary["all_objects_available"] else 1

    if not inventory_path.is_file():
        raise RuntimeError("run --mode inventory successfully before download/verify")
    inventory = load_inventory(inventory_path)
    missing_inventory = [
        item
        for item in objects
        if (item.cohort, item.trial_name, item.relative_path) not in inventory
    ]
    if missing_inventory:
        raise RuntimeError(f"inventory is missing {len(missing_inventory)} selected objects")
    unavailable = [
        row
        for row in inventory.values()
        if row.get("status") != 200 or not isinstance(row.get("content_length"), int)
    ]
    if unavailable:
        raise RuntimeError(f"inventory has {len(unavailable)} unavailable/unsized objects")

    if args.mode == "download":
        results = parallel_map(
            objects,
            lambda item: download_one(
                item,
                expected_size=int(
                    inventory[(item.cohort, item.trial_name, item.relative_path)][
                        "content_length"
                    ]
                ),
                timeout=args.timeout_seconds,
                retries=args.retries,
            ),
            workers=args.workers,
            label="GET",
        )
        results.sort(key=lambda row: (row["cohort"], row["trial_name"], row["relative_path"]))
        write_jsonl(output_root / "download_manifest.jsonl", results)
        failures = [row for row in results if row.get("status") not in ("downloaded", "existing")]
        summary = {
            "schema_version": "deepswe_v1_1_public_download_summary/v1",
            "object_count": len(results),
            "complete_count": len(results) - len(failures),
            "failed_count": len(failures),
            "bytes": sum(int(row.get("size_bytes") or 0) for row in results),
            "status_counts": dict(Counter(str(row.get("status")) for row in results)),
        }
        write_json(output_root / "download_summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
        return 0 if not failures else 1

    verification: list[dict[str, Any]] = []
    for index_number, item in enumerate(objects, 1):
        expected_size = int(
            inventory[(item.cohort, item.trial_name, item.relative_path)]["content_length"]
        )
        exists = item.destination.is_file()
        actual_size = item.destination.stat().st_size if exists else None
        verification.append(
            {
                "cohort": item.cohort,
                "trial_name": item.trial_name,
                "task_name": item.task_name,
                "relative_path": item.relative_path,
                "status": "pass" if exists and actual_size == expected_size else "fail",
                "expected_size": expected_size,
                "actual_size": actual_size,
                "sha256": sha256_file(item.destination) if exists and actual_size == expected_size else None,
            }
        )
        if index_number % 250 == 0 or index_number == len(objects):
            print(f"VERIFY: {index_number}/{len(objects)}", flush=True)
    write_jsonl(output_root / "verification_manifest.jsonl", verification)
    failures = [row for row in verification if row["status"] != "pass"]
    summary = {
        "schema_version": "deepswe_v1_1_public_verification_summary/v1",
        "object_count": len(verification),
        "pass_count": len(verification) - len(failures),
        "fail_count": len(failures),
        "bytes": sum(int(row.get("actual_size") or 0) for row in verification),
    }
    write_json(output_root / "verification_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
