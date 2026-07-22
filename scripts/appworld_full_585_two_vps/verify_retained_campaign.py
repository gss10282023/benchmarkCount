#!/usr/bin/env python3
"""Verify one pruned AppWorld campaign root against its exact retained task set."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any


AGENTS = ("agent_a", "agent_b", "agent_c")
REQUIRED_ARTIFACTS = (
    "run_summary.json",
    "native_evaluator_input.json",
    "native_evaluator_output.json",
    "official_runner_config.json",
    "artifact_manifest.json",
    "appworld_task_output/logs/lm_calls.jsonl",
)
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SENSITIVE_KEYS = {"api_key", "apikey", "authorization", "x-api-key"}


def has_sensitive_field(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in SENSITIVE_KEYS or has_sensitive_field(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(has_sensitive_field(child) for child in value)
    return False


def task_dirs(output_root: Path, agent: str) -> set[str]:
    root = output_root / agent
    return {
        path.name
        for path in root.iterdir()
        if path.is_dir() and SAFE_ID.fullmatch(path.name)
    }


def read_lm_log(path: Path) -> tuple[float, int]:
    cost = 0.0
    calls = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if has_sensitive_field(payload):
            raise RuntimeError(f"sensitive field remains in {path}:{line_number}")
        cost += float(((payload.get("output") or {}).get("usage") or {}).get("cost") or 0.0)
        calls += 1
    return cost, calls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--appworld-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--retention-manifest", type=Path, required=True)
    parser.add_argument("--vps-id", required=True, choices=("vps1", "vps2"))
    parser.add_argument("--expected-task-count", type=int, required=True)
    args = parser.parse_args()

    campaign_root = args.campaign_root.resolve()
    appworld_root = args.appworld_root.resolve()
    manifest = json.loads(args.retention_manifest.read_text(encoding="utf-8"))
    retained = {
        str(item["task_id"])
        for item in manifest["tasks"]
        if str(item["vps_id"]) == args.vps_id
    }
    if len(retained) != args.expected_task_count:
        raise RuntimeError(f"retained manifest count={len(retained)}")

    output_root = campaign_root / "outputs"
    versions: Counter[str] = Counter()
    record_count = 0
    lm_call_count = 0
    billed_cost_usd = 0.0
    for agent in AGENTS:
        present = task_dirs(output_root, agent)
        if present != retained:
            raise RuntimeError(
                f"{agent} output mismatch: missing={len(retained - present)}, "
                f"unexpected={len(present - retained)}"
            )
        for task_id in sorted(retained):
            record_root = output_root / agent / task_id
            missing = [relative for relative in REQUIRED_ARTIFACTS if not (record_root / relative).is_file()]
            if missing:
                raise RuntimeError(f"{agent}/{task_id} missing artifacts: {missing}")
            summary = json.loads((record_root / "run_summary.json").read_text(encoding="utf-8"))
            if summary.get("status") != "completed" or str(summary.get("task_id")) != task_id:
                raise RuntimeError(f"invalid summary for {agent}/{task_id}")
            version_path = record_root / "appworld_task_output" / "version" / "data.txt"
            versions[version_path.read_text(encoding="utf-8").strip()] += 1
            cost, calls = read_lm_log(record_root / "appworld_task_output" / "logs" / "lm_calls.jsonl")
            billed_cost_usd += cost
            lm_call_count += calls
            record_count += 1

    worker_root = campaign_root / "logs" / "workers"
    unexpected_worker_logs: list[str] = []
    for agent in AGENTS:
        root = worker_root / agent
        if not root.is_dir():
            continue
        for path in root.iterdir():
            task_id = path.name.split(".attempt_", 1)[0]
            if task_id not in retained:
                unexpected_worker_logs.append(str(path))
    if unexpected_worker_logs:
        raise RuntimeError(f"worker logs remain for non-retained tasks: {len(unexpected_worker_logs)}")

    experiment_root = appworld_root / "experiments" / "outputs"
    expected_experiments = {
        f"{args.run_id}_{agent}_{task_id}" for agent in AGENTS for task_id in retained
    }
    present_experiments = {
        path.name
        for path in experiment_root.iterdir()
        if path.is_dir() and path.name.startswith(f"{args.run_id}_")
    }
    if present_experiments != expected_experiments:
        raise RuntimeError(
            "AppWorld experiment mismatch: "
            f"missing={len(expected_experiments - present_experiments)}, "
            f"unexpected={len(present_experiments - expected_experiments)}"
        )
    for agent in AGENTS:
        for task_id in retained:
            read_lm_log(
                experiment_root
                / f"{args.run_id}_{agent}_{task_id}"
                / "tasks"
                / task_id
                / "logs"
                / "lm_calls.jsonl"
            )

    print(
        json.dumps(
            {
                "status": "passed",
                "vps_id": args.vps_id,
                "retained_task_count": len(retained),
                "record_count": record_count,
                "lm_call_count": lm_call_count,
                "billed_cost_usd": round(billed_cost_usd, 12),
                "data_versions": dict(sorted(versions.items())),
                "appworld_experiment_count": len(present_experiments),
                "unexpected_worker_log_count": 0,
                "sensitive_field_count": 0,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
