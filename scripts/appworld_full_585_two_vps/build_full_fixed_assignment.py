#!/usr/bin/env python3
"""Extend the immutable 447-task assignment with the 138 tasks selected for rerun."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def dataset_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "test_normal_count": sum(row["dataset_name"] == "test_normal" for row in rows),
        "test_challenge_count": sum(row["dataset_name"] == "test_challenge" for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retention-manifest", type=Path, required=True)
    parser.add_argument("--existing-vps1", type=Path, required=True)
    parser.add_argument("--existing-vps2", type=Path, required=True)
    parser.add_argument("--output-vps1", type=Path, required=True)
    parser.add_argument("--output-vps2", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()

    existing = {"vps1": load_jsonl(args.existing_vps1), "vps2": load_jsonl(args.existing_vps2)}
    existing_sets = {
        vps_id: {str(row["task_id"]) for row in rows} for vps_id, rows in existing.items()
    }
    if len(existing_sets["vps1"]) != 224 or len(existing_sets["vps2"]) != 223:
        raise RuntimeError("the immutable 447-task base assignment changed")
    if existing_sets["vps1"] & existing_sets["vps2"]:
        raise RuntimeError("existing VPS assignments overlap")

    retention = json.loads(args.retention_manifest.read_text(encoding="utf-8"))
    added = [
        {
            "task_id": str(row["task_id"]),
            "dataset_name": str(row["dataset_name"]),
            "global_index": int(row["global_index"]),
        }
        for row in retention["tasks"]
    ]
    added.sort(key=lambda row: int(row["global_index"]))
    added_ids = {str(row["task_id"]) for row in added}
    if len(added_ids) != 138 or added_ids & (existing_sets["vps1"] | existing_sets["vps2"]):
        raise RuntimeError("138-task addition is not exact or overlaps the 447-task base")

    # Keep all 447 previous assignments unchanged. Alternating the ordered 138
    # additions gives each VPS 69 more tasks and preserves a 293/292 split.
    additions = {"vps1": added[::2], "vps2": added[1::2]}
    if len(additions["vps1"]) != 69 or len(additions["vps2"]) != 69:
        raise RuntimeError("added task split must be 69/69")
    combined = {
        vps_id: sorted(existing[vps_id] + additions[vps_id], key=lambda row: int(row["global_index"]))
        for vps_id in ("vps1", "vps2")
    }
    write_jsonl(args.output_vps1, combined["vps1"])
    write_jsonl(args.output_vps2, combined["vps2"])

    final_sets = {
        vps_id: {str(row["task_id"]) for row in rows} for vps_id, rows in combined.items()
    }
    if final_sets["vps1"] & final_sets["vps2"] or len(final_sets["vps1"] | final_sets["vps2"]) != 585:
        raise RuntimeError("full assignment is not a disjoint 585-task partition")
    if not existing_sets["vps1"] <= final_sets["vps1"] or not existing_sets["vps2"] <= final_sets["vps2"]:
        raise RuntimeError("an existing 447-task assignment moved between VPSs")

    output_paths = {"vps1": args.output_vps1, "vps2": args.output_vps2}
    manifest = {
        "schema_version": "appworld_fixed_full_assignment/v2",
        "run_id": str(retention["run_id"]),
        "assignment_rule": (
            "preserve the immutable 447-task assignments and add 69 formerly retained tasks to each VPS"
        ),
        "full_task_count": 585,
        "rerun_task_count": 585,
        "legacy_result_task_count": 0,
        "automatic_lm_attempts": 1,
        "automatic_task_attempts": 1,
        "initial_workers_per_vps": 6,
        "max_workers_per_vps": 72,
        "normal_completions_per_ramp": 12,
        "worker_levels": [6, 12, 24, 36, 48, 60, 72],
        "operator_authorized_low_balance_start": True,
        "operator_authorized_retired_key_start": True,
        "resource_ramp_policy": {
            "minimum_available_memory_after_ramp_gib": 4.0,
            "memory_reserve_per_added_worker_gib": 1.0,
            "maximum_one_minute_load_per_cpu_before_ramp": 2.0,
        },
        "consecutive_error_limit": 1,
        "agents": ["agent_a", "agent_b", "agent_c"],
        "budget_policy": {
            "combined_campaign_cost_cap_usd": 2000.0,
            "minimum_confirmed_shared_balance_usd": 615.0,
            "per_slot_reserve_usd": 3.0,
            "vps1_campaign_cost_cap_usd": 1000.0,
            "vps2_campaign_cost_cap_usd": 1000.0,
        },
        "shards": {},
    }
    for vps_id in ("vps1", "vps2"):
        rows = combined[vps_id]
        manifest["shards"][vps_id] = {
            "path": str(output_paths[vps_id]),
            "sha256": sha256_file(output_paths[vps_id]),
            "task_count": len(rows),
            "record_slot_count": len(rows) * 3,
            "first_global_index": min(int(row["global_index"]) for row in rows),
            "last_global_index": max(int(row["global_index"]) for row in rows),
            "preserved_447_assignment_count": len(existing[vps_id]),
            "added_rerun_task_count": len(additions[vps_id]),
            **dataset_counts(rows),
        }
    args.output_manifest.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
