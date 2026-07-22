#!/usr/bin/env python3
"""Cross-check locally extracted Fable trajectories against Harbor trial rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", required=True, type=Path)
    parser.add_argument("--job-root", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--remote-inventory", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    reference_by_id = {str(row["id"]): row for row in read_jsonl(args.reference)}
    reference = {str(row["trial_name"]): row for row in reference_by_id.values()}
    remote_by_id = {
        str(row["trial_id"]): row for row in read_jsonl(args.remote_inventory)
    }
    remote = {
        str(reference_by_id[trial_id]["trial_name"]): row
        for trial_id, row in remote_by_id.items()
        if trial_id in reference_by_id
    }
    local: dict[str, dict[str, Any]] = {}
    for result_path in args.job_root.rglob("result.json"):
        try:
            result = json.loads(result_path.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(result, dict) or not isinstance(result.get("id"), str):
            continue
        config = result.get("config")
        if not isinstance(config, dict):
            continue
        agent = config.get("agent")
        if not isinstance(agent, dict):
            continue
        kwargs = agent.get("kwargs") if isinstance(agent.get("kwargs"), dict) else {}
        if not (
            agent.get("name") == "claude-code"
            and agent.get("model_name") == "anthropic/claude-fable-5"
            and kwargs.get("reasoning_effort") == "xhigh"
        ):
            continue
        trajectory = result_path.parent / "agent" / "trajectory.json"
        trial_name = str(result.get("trial_name"))
        local[trial_name] = {
            "cohort": "claude-fable-5__xhigh",
            "local_result_id": result["id"],
            "hub_trial_id": None,
            "trial_name": trial_name,
            "task_name": result.get("task_name"),
            "agent": "claude-code",
            "model_name": "anthropic/claude-fable-5",
            "reasoning_effort": "xhigh",
            "local_path": str(trajectory.relative_to(args.benchmark_root))
            if trajectory.is_file()
            else None,
            "bytes": trajectory.stat().st_size if trajectory.is_file() else None,
            "sha256": None,
        }

    paths = [
        args.benchmark_root / str(local[trial_name]["local_path"])
        for trial_name in sorted(local)
        if local[trial_name]["local_path"]
    ]
    names_with_paths = [
        trial_name for trial_name in sorted(local) if local[trial_name]["local_path"]
    ]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        digests = list(executor.map(sha256, paths))
    for trial_name, digest in zip(names_with_paths, digests, strict=True):
        local[trial_name]["sha256"] = digest
    for trial_name in set(reference) & set(local):
        local[trial_name]["hub_trial_id"] = reference[trial_name]["id"]

    reference_names = set(reference)
    local_names = set(local)
    remote_names = set(remote)
    size_mismatches = [
        trial_name
        for trial_name in sorted(reference_names & local_names & remote_names)
        if local[trial_name]["bytes"] != remote[trial_name].get("content_length")
    ]
    rows = [local[trial_name] for trial_name in sorted(local)]
    output_manifest = args.benchmark_root / "fable_local_trajectory_manifest.jsonl"
    output_manifest.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    )
    summary = {
        "schema_version": "terminal_bench_2_1_fable_local_trajectory_audit/v1",
        "matching_key": "trial_name (Hub upload remaps the original local result UUID)",
        "reference_trial_count": len(reference_names),
        "remote_available_trajectory_count": sum(
            row.get("status") == 200 for row in remote.values()
        ),
        "local_selected_trial_count": len(local_names),
        "local_trajectory_count": len(names_with_paths),
        "local_task_count": len({str(row["task_name"]) for row in rows}),
        "local_trajectory_bytes": sum(int(row["bytes"] or 0) for row in rows),
        "missing_local_trial_names": sorted(reference_names - local_names),
        "extra_local_trial_names": sorted(local_names - reference_names),
        "missing_remote_inventory_trial_names": sorted(reference_names - remote_names),
        "size_mismatch_trial_names": size_mismatches,
        "all_checks_pass": (
            reference_names == local_names == remote_names
            and len(names_with_paths) == len(reference_names)
            and not size_mismatches
            and len({str(row["task_name"]) for row in rows}) == 89
        ),
    }
    (args.benchmark_root / "fable_local_trajectory_audit.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
