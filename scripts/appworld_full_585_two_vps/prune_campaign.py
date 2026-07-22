#!/usr/bin/env python3
"""Retain an exact AppWorld task set and permanently prune all listed others."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
from typing import Iterable


AGENTS = ("agent_a", "agent_b", "agent_c")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SENSITIVE_KEYS = {"api_key", "apikey", "authorization", "x-api-key"}


def load_ids(path: Path) -> set[str]:
    values = {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    unsafe = sorted(value for value in values if not SAFE_ID.fullmatch(value))
    if unsafe:
        raise RuntimeError(f"unsafe task IDs in {path}: {unsafe[:5]}")
    return values


def task_dirs(output_root: Path, agent: str) -> set[str]:
    root = output_root / agent
    if not root.is_dir():
        return set()
    return {path.name for path in root.iterdir() if path.is_dir() and SAFE_ID.fullmatch(path.name)}


def worker_logs_for(logs_root: Path, agent: str, task_id: str) -> Iterable[Path]:
    root = logs_root / "workers" / agent
    if not root.is_dir():
        return ()
    return tuple(root.glob(f"{task_id}.attempt_*.stdout.log")) + tuple(
        root.glob(f"{task_id}.attempt_*.stderr.log")
    )


def retained_lm_logs(
    campaign_roots: Iterable[Path],
    appworld_roots: Iterable[Path],
    run_id: str,
    retained: set[str],
) -> list[Path]:
    paths: set[Path] = set()
    for root in campaign_roots:
        for agent in AGENTS:
            for task_id in retained:
                path = root / "outputs" / agent / task_id / "appworld_task_output" / "logs" / "lm_calls.jsonl"
                if path.is_file():
                    paths.add(path)
    for root in appworld_roots:
        experiment_outputs = root / "experiments" / "outputs"
        for agent in AGENTS:
            for task_id in retained:
                path = (
                    experiment_outputs
                    / f"{run_id}_{agent}_{task_id}"
                    / "tasks"
                    / task_id
                    / "logs"
                    / "lm_calls.jsonl"
                )
                if path.is_file():
                    paths.add(path)
    return sorted(paths)


def redact_sensitive_fields(value: object) -> tuple[object, int]:
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        removed = 0
        for key, child in value.items():
            if key.lower() in SENSITIVE_KEYS:
                removed += 1
                continue
            clean_child, child_removed = redact_sensitive_fields(child)
            redacted[key] = clean_child
            removed += child_removed
        return redacted, removed
    if isinstance(value, list):
        redacted_list: list[object] = []
        removed = 0
        for child in value:
            clean_child, child_removed = redact_sensitive_fields(child)
            redacted_list.append(clean_child)
            removed += child_removed
        return redacted_list, removed
    return value, 0


def inspect_lm_log(path: Path) -> tuple[list[str], int]:
    clean_lines: list[str] = []
    removed = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            document = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid JSON in {path}:{line_number}: {exc}") from exc
        clean_document, document_removed = redact_sensitive_fields(document)
        removed += document_removed
        clean_lines.append(json.dumps(clean_document, ensure_ascii=False, separators=(",", ":")))
    return clean_lines, removed


def replace_lm_log(path: Path, clean_lines: list[str]) -> None:
    temporary = path.with_name(f".{path.name}.sanitizing.{os.getpid()}")
    temporary.write_text("\n".join(clean_lines) + ("\n" if clean_lines else ""), encoding="utf-8")
    os.chmod(temporary, path.stat().st_mode)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--duplicate-campaign-root", type=Path, action="append", default=[])
    parser.add_argument("--appworld-root", type=Path, action="append", default=[])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--retained-task-file", type=Path, required=True)
    parser.add_argument("--deleted-task-file", type=Path, required=True)
    parser.add_argument("--expected-retained-count", type=int, required=True)
    parser.add_argument("--expected-deleted-count", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    campaign_root = args.campaign_root.resolve()
    if campaign_root == Path("/") or not campaign_root.is_dir():
        raise RuntimeError(f"unsafe or missing campaign root: {campaign_root}")
    global_retained = load_ids(args.retained_task_file)
    global_deleted = load_ids(args.deleted_task_file)
    if global_retained & global_deleted:
        raise RuntimeError("retained and deleted task sets overlap")

    campaign_roots = [campaign_root]
    campaign_roots.extend(path.resolve() for path in args.duplicate_campaign_root if path.exists())
    appworld_roots = [path.resolve() for path in args.appworld_root if path.exists()]
    planned_output_dirs: list[Path] = []
    planned_logs: list[Path] = []
    planned_experiments: list[Path] = []
    planned_retained_log_sanitizations: list[tuple[Path, list[str], int]] = []

    primary_outputs = campaign_root / "outputs"
    primary_sets = {agent: task_dirs(primary_outputs, agent) for agent in AGENTS}
    primary_universe = primary_sets[AGENTS[0]]
    for agent, present in primary_sets.items():
        if present != primary_universe:
            raise RuntimeError(
                f"primary {agent} task set differs from the other agents: "
                f"missing={len(primary_universe - present)}, unexpected={len(present - primary_universe)}"
            )
    global_universe = global_retained | global_deleted
    unexpected_primary = primary_universe - global_universe
    if unexpected_primary:
        raise RuntimeError(f"primary output contains tasks absent from global manifests: {len(unexpected_primary)}")
    retained = global_retained & primary_universe
    deleted = global_deleted & primary_universe
    if retained | deleted != primary_universe:
        raise RuntimeError("scoped retained/deleted sets do not cover the primary output")
    if len(retained) != args.expected_retained_count or len(deleted) != args.expected_deleted_count:
        raise RuntimeError(
            f"scoped task count mismatch: retained={len(retained)}, deleted={len(deleted)}"
        )

    for root in campaign_roots:
        for agent in AGENTS:
            for task_id in deleted:
                output_dir = root / "outputs" / agent / task_id
                if output_dir.is_dir():
                    planned_output_dirs.append(output_dir)
                planned_logs.extend(worker_logs_for(root / "logs", agent, task_id))

    for root in appworld_roots:
        experiment_outputs = root / "experiments" / "outputs"
        for agent in AGENTS:
            for task_id in deleted:
                experiment_dir = experiment_outputs / f"{args.run_id}_{agent}_{task_id}"
                if experiment_dir.is_dir():
                    planned_experiments.append(experiment_dir)

    for path in retained_lm_logs(campaign_roots, appworld_roots, args.run_id, retained):
        clean_lines, removed = inspect_lm_log(path)
        if removed:
            planned_retained_log_sanitizations.append((path, clean_lines, removed))

    report = {
        "mode": "apply" if args.apply else "dry_run",
        "global_retained_task_count": len(global_retained),
        "global_deleted_task_count": len(global_deleted),
        "retained_task_count": len(retained),
        "deleted_task_count": len(deleted),
        "planned_output_directory_deletions": len(planned_output_dirs),
        "planned_worker_log_deletions": len(planned_logs),
        "planned_appworld_experiment_deletions": len(planned_experiments),
        "planned_retained_lm_log_sanitizations": len(planned_retained_log_sanitizations),
        "planned_sensitive_field_removals": sum(
            removed for _, _, removed in planned_retained_log_sanitizations
        ),
        "campaign_roots": [str(path) for path in campaign_roots],
        "appworld_roots": [str(path) for path in appworld_roots],
    }
    if not args.apply:
        print(json.dumps(report, ensure_ascii=True, sort_keys=True))
        return 0

    for path in planned_output_dirs:
        shutil.rmtree(path)
    for path in planned_logs:
        path.unlink(missing_ok=True)
    for path in planned_experiments:
        shutil.rmtree(path)
    for path, clean_lines, _ in planned_retained_log_sanitizations:
        replace_lm_log(path, clean_lines)

    for agent in AGENTS:
        remaining = task_dirs(primary_outputs, agent)
        if remaining != retained:
            raise RuntimeError(
                f"post-prune {agent} task set mismatch: "
                f"missing={len(retained - remaining)}, unexpected={len(remaining - retained)}"
            )
    report["post_prune_primary_record_count"] = sum(
        len(task_dirs(primary_outputs, agent)) for agent in AGENTS
    )
    report["post_prune_primary_task_count"] = len(
        set.intersection(*(task_dirs(primary_outputs, agent) for agent in AGENTS))
    )
    report["status"] = "completed"
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
