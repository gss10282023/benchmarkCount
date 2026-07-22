#!/usr/bin/env python3
"""Inventory, download, and verify exact public Harbor trajectory cohorts."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from harbor.auth.client import create_authenticated_client
from harbor.auth.constants import SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL
from harbor.auth.tokens import get_access_token


COHORTS = {
    "gpt-5.5__xhigh": {
        "job_id": "10e2e56b-ed31-5f65-a489-69f78b902adf",
        "model_name": "openai/gpt-5.5",
        "reasoning_effort": "xhigh",
        "agents": {"codex", "terminus-2"},
    },
    "claude-fable-5__xhigh": {
        "job_id": "f9d0318d-30f9-5d6f-bd7f-0ad5acf780d7",
        "model_name": "anthropic/claude-fable-5",
        "reasoning_effort": "xhigh",
        "agents": {"claude-code"},
    },
    "gemini-3.1-pro-preview__high": {
        "job_id": "42cd19c9-42ad-5d79-b033-adf4f879423d",
        "model_name": "gemini/gemini-3.1-pro-preview",
        "reasoning_effort": "high",
        "agents": {"gemini-cli", "terminus-2"},
    },
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


async def query_job_trials(job_id: str) -> list[dict[str, Any]]:
    client = await create_authenticated_client()
    rows: list[dict[str, Any]] = []
    start = 0
    page_size = 1000
    select = (
        "id,job_id,trial_name,task_name,task_content_hash,trajectory_path,"
        "archive_path,config,started_at,finished_at,exception_type"
    )
    while True:
        response = await (
            client.table("trial")
            .select(select)
            .eq("job_id", job_id)
            .order("id")
            .range(start, start + page_size - 1)
            .execute()
        )
        page = list(response.data or [])
        rows.extend(page)
        if len(page) < page_size:
            return rows
        start += page_size


def matches(row: dict[str, Any], spec: dict[str, Any]) -> bool:
    config = row.get("config")
    if not isinstance(config, dict):
        return False
    agent = config.get("agent")
    if not isinstance(agent, dict):
        return False
    kwargs = agent.get("kwargs") if isinstance(agent.get("kwargs"), dict) else {}
    return (
        agent.get("name") in spec["agents"]
        and agent.get("model_name") == spec["model_name"]
        and kwargs.get("reasoning_effort") == spec["reasoning_effort"]
    )


def enrich(row: dict[str, Any], cohort: str) -> dict[str, Any]:
    config = row["config"]
    agent = config["agent"]
    kwargs = agent.get("kwargs") if isinstance(agent.get("kwargs"), dict) else {}
    return {
        "cohort": cohort,
        "id": row["id"],
        "job_id": row["job_id"],
        "trial_name": row["trial_name"],
        "task_name": row["task_name"],
        "task_content_hash": row["task_content_hash"],
        "trajectory_path": row.get("trajectory_path"),
        "archive_path": row.get("archive_path"),
        "agent": agent.get("name"),
        "agent_version": kwargs.get("version"),
        "model_name": agent.get("model_name"),
        "reasoning_effort": kwargs.get("reasoning_effort"),
        "started_at": row.get("started_at"),
        "finished_at": row.get("finished_at"),
        "exception_type": row.get("exception_type"),
    }


def storage_url(remote_path: str) -> str:
    return (
        f"{SUPABASE_URL}/storage/v1/object/authenticated/results/"
        f"{urllib.parse.quote(remote_path, safe='/')}"
    )


def headers(token: str) -> dict[str, str]:
    return {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {token}",
    }


def head_one(row: dict[str, Any], token: str) -> dict[str, Any]:
    remote_path = str(row["trajectory_path"])
    request = urllib.request.Request(
        storage_url(remote_path), headers=headers(token), method="HEAD"
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return {
                "cohort": row["cohort"],
                "trial_id": row["id"],
                "trajectory_path": remote_path,
                "status": response.status,
                "content_length": int(response.headers.get("Content-Length", "0")),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    except urllib.error.HTTPError as exc:
        return {
            "cohort": row["cohort"],
            "trial_id": row["id"],
            "trajectory_path": remote_path,
            "status": exc.code,
            "error": exc.read(500).decode("utf-8", errors="replace"),
        }


def safe_piece(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


def local_path(root: Path, row: dict[str, Any]) -> Path:
    task = safe_piece(str(row["task_name"]).rsplit("/", 1)[-1])
    agent = safe_piece(str(row["agent"]))
    return (
        root
        / "direct_trajectories"
        / str(row["cohort"])
        / agent
        / task
        / str(row["id"])
        / "trajectory.json"
    )


def download_one(
    root: Path,
    row: dict[str, Any],
    remote: dict[str, Any],
    token: str,
) -> dict[str, Any]:
    target = local_path(root, row)
    expected = int(remote["content_length"])
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".json.part")
    if target.exists() and target.stat().st_size == expected:
        status = "existing"
    else:
        offset = partial.stat().st_size if partial.exists() else 0
        if offset > expected:
            partial.unlink()
            offset = 0
        request_headers = headers(token)
        if offset:
            request_headers["Range"] = f"bytes={offset}-"
        request = urllib.request.Request(
            storage_url(str(row["trajectory_path"])), headers=request_headers
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            if offset and response.status != 206:
                partial.unlink(missing_ok=True)
                return download_one(root, row, remote, token)
            with partial.open("ab" if offset else "wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
        if partial.stat().st_size != expected:
            raise RuntimeError(
                f"Size mismatch for {row['id']}: {partial.stat().st_size} != {expected}"
            )
        os.replace(partial, target)
        status = "downloaded"
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return {
        "cohort": row["cohort"],
        "trial_id": row["id"],
        "local_path": str(target.relative_to(root)),
        "bytes": target.stat().st_size,
        "sha256": digest.hexdigest(),
        "status": status,
    }


def parallel(items: list[Any], worker, workers: int, label: str) -> list[Any]:
    results: list[Any] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker, item) for item in items]
        for index, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if index % 100 == 0 or index == len(futures):
                print(f"{label}: {index}/{len(futures)}", flush=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--mode", choices=("inventory", "download", "verify"), required=True)
    parser.add_argument("--cohort", action="append", choices=sorted(COHORTS))
    parser.add_argument("--workers", type=int, default=24)
    args = parser.parse_args()
    selected_names = args.cohort or sorted(COHORTS)
    args.output_root.mkdir(parents=True, exist_ok=True)

    selected_rows: list[dict[str, Any]] = []
    selection_summary: dict[str, Any] = {}
    for cohort in selected_names:
        spec = COHORTS[cohort]
        rows = asyncio.run(query_job_trials(str(spec["job_id"])))
        picked = [enrich(row, cohort) for row in rows if matches(row, spec)]
        picked.sort(key=lambda row: str(row["id"]))
        tasks = {str(row["task_name"]) for row in picked}
        paths = [str(row["trajectory_path"]) for row in picked if row["trajectory_path"]]
        if len(paths) != len(set(paths)):
            raise RuntimeError(f"Duplicate trajectory_path values in {cohort}")
        selection_summary[cohort] = {
            "job_trial_row_count": len(rows),
            "selected_trial_count": len(picked),
            "selected_task_count": len(tasks),
            "trajectory_path_count": len(paths),
            "missing_trajectory_path_count": len(picked) - len(paths),
            "selected_trials_by_agent": {
                agent: sum(row["agent"] == agent for row in picked)
                for agent in sorted(spec["agents"])
            },
        }
        write_jsonl(args.output_root / "index" / f"{cohort}.selected_trials.jsonl", picked)
        selected_rows.extend(picked)
    write_json(args.output_root / "index" / "direct_selection_summary.json", selection_summary)

    rows_with_path = [row for row in selected_rows if row["trajectory_path"]]
    token = asyncio.run(get_access_token())
    if args.mode == "inventory":
        remote_rows = parallel(
            rows_with_path,
            lambda row: head_one(row, token),
            args.workers,
            "HEAD",
        )
        remote_rows.sort(key=lambda row: (str(row["cohort"]), str(row["trial_id"])))
        write_jsonl(args.output_root / "direct_remote_trajectory_inventory.jsonl", remote_rows)
        summary = {
            "object_count": len(remote_rows),
            "available_count": sum(row["status"] == 200 for row in remote_rows),
            "known_content_bytes": sum(
                int(row.get("content_length", 0)) for row in remote_rows
            ),
            "status_counts": {
                str(status): sum(row["status"] == status for row in remote_rows)
                for status in sorted({int(row["status"]) for row in remote_rows})
            },
        }
        write_json(args.output_root / "direct_remote_trajectory_summary.json", summary)
        print(json.dumps({"selection": selection_summary, "remote": summary}, indent=2))
        return

    remote_rows = [
        json.loads(line)
        for line in (args.output_root / "direct_remote_trajectory_inventory.jsonl")
        .read_text()
        .splitlines()
        if line
    ]
    remote_by_id = {str(row["trial_id"]): row for row in remote_rows}
    missing_inventory = [row["id"] for row in rows_with_path if row["id"] not in remote_by_id]
    if missing_inventory:
        raise RuntimeError(f"Remote inventory missing {len(missing_inventory)} selected rows")
    bad_remote = [row for row in remote_rows if row["status"] != 200]
    if bad_remote:
        raise RuntimeError(f"Remote inventory has {len(bad_remote)} unavailable objects")

    if args.mode == "download":
        required = sum(int(remote_by_id[row["id"]]["content_length"]) for row in rows_with_path)
        free = os.statvfs(args.output_root).f_bavail * os.statvfs(args.output_root).f_frsize
        if required + 128 * 1024 * 1024 > free:
            raise RuntimeError(f"Insufficient disk: need {required}, have {free}")
        started = time.monotonic()
        downloaded = parallel(
            rows_with_path,
            lambda row: download_one(args.output_root, row, remote_by_id[row["id"]], token),
            args.workers,
            "GET",
        )
        downloaded.sort(key=lambda row: (str(row["cohort"]), str(row["trial_id"])))
        write_jsonl(args.output_root / "direct_trajectory_download_manifest.jsonl", downloaded)
        summary = {
            "object_count": len(downloaded),
            "bytes": sum(int(row["bytes"]) for row in downloaded),
            "downloaded_count": sum(row["status"] == "downloaded" for row in downloaded),
            "existing_count": sum(row["status"] == "existing" for row in downloaded),
            "seconds": round(time.monotonic() - started, 3),
        }
        write_json(args.output_root / "direct_trajectory_download_summary.json", summary)
        print(json.dumps(summary, indent=2))
        return

    manifest_rows = [
        json.loads(line)
        for line in (args.output_root / "direct_trajectory_download_manifest.jsonl")
        .read_text()
        .splitlines()
        if line
    ]
    failures: list[dict[str, Any]] = []
    for row in manifest_rows:
        path = args.output_root / row["local_path"]
        if not path.is_file() or path.stat().st_size != int(row["bytes"]):
            failures.append({"trial_id": row["trial_id"], "reason": "missing_or_size"})
            continue
        if sha256_file(path) != row["sha256"]:
            failures.append({"trial_id": row["trial_id"], "reason": "sha256"})
    summary = {
        "object_count": len(manifest_rows),
        "pass_count": len(manifest_rows) - len(failures),
        "fail_count": len(failures),
        "failures": failures,
    }
    write_json(args.output_root / "direct_trajectory_verification_summary.json", summary)
    print(json.dumps(summary, indent=2))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
