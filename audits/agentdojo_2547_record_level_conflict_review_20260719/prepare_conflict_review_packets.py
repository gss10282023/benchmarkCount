#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def remove_existing(path: Path) -> None:
    if path.is_symlink() or path.exists():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def replace_materialized(path: Path, target: Path) -> None:
    """Copy inputs into the packet so the read-only sandbox can traverse them.

    Symlinks that leave the packet workspace are deliberately avoided: Codex's
    read-only sandbox may deny those targets even when the invoking OS user can
    read them.  Materializing the files also makes every emitted relative source
    pointer independently resolvable inside the locked packet.
    """
    remove_existing(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved = target.resolve()
    if resolved.is_dir():
        shutil.copytree(resolved, path, symlinks=False)
    else:
        shutil.copy2(resolved, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-root", type=Path, required=True)
    parser.add_argument("--task-plan", type=Path, required=True)
    parser.add_argument("--component-root", type=Path, required=True)
    parser.add_argument("--case-source-root", type=Path, required=True)
    parser.add_argument("--agentdojo-source-root", type=Path, required=True)
    parser.add_argument("--worker-source", type=Path)
    parser.add_argument("--postprocessor-source", type=Path)
    parser.add_argument("--score-resolver-source", type=Path)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--contract-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    job = args.job_root.resolve()
    component_root = args.component_root.resolve()
    case_source_root = args.case_source_root.resolve()
    agentdojo_source_root = args.agentdojo_source_root.resolve()
    audit_root = args.audit_root.resolve()
    contract_root = args.contract_root.resolve()
    plan = load_json(args.task_plan.resolve())
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 2547:
        raise SystemExit(f"expected 2547 tasks, found {len(tasks) if isinstance(tasks, list) else 'invalid'}")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        groups[str(task["case_unit_id"])].append(task)
    if len(groups) != 849 or any(len(items) != 3 for items in groups.values()):
        raise SystemExit("task plan is not exactly 849 cases x 3 records")

    packets_root = audit_root / "packets"
    outputs_root = audit_root / "outputs"
    logs_root = audit_root / "logs"
    packets_root.mkdir(parents=True, exist_ok=True)
    outputs_root.mkdir(parents=True, exist_ok=True)
    logs_root.mkdir(parents=True, exist_ok=True)

    wiring_sources = {
        "agentdojo_worker.py": (args.worker_source or job / "app/src/evidence_system/adapters/agentdojo_worker.py").resolve(),
        "agentdojo_formal_postprocessor.py": (args.postprocessor_source or job / "app/src/evidence_system/adapters/agentdojo_formal_postprocessor.py").resolve(),
        "score_evidence_with_codex.py": (args.score_resolver_source or job / "app/neurips_ed_track_minimal/scripts/score_evidence_with_codex.py").resolve(),
        "official_agentdojo/baseline_attacks.py": agentdojo_source_root / "src/agentdojo/attacks/baseline_attacks.py",
        "official_agentdojo/benchmark.py": agentdojo_source_root / "src/agentdojo/benchmark.py",
    }
    index: list[dict[str, Any]] = []
    packet_locks: list[dict[str, Any]] = []
    for case_index, case_unit_id in enumerate(sorted(groups), start=1):
        version, suite, user_task, injection_task = case_unit_id.split(":")
        case_slug = f"{version}_{suite}_{user_task}_{injection_task}"
        packet = packets_root / case_slug
        packet.mkdir(parents=True, exist_ok=True)
        ordered = sorted(groups[case_unit_id], key=lambda item: str(item["agent_id"]))
        checklist = Path(ordered[0]["checklist_path"]).resolve()
        shutil.copy2(checklist, packet / "checklist.yaml")

        exact_case_source = case_source_root / case_slug
        exact_official = exact_case_source / "raw_case/official"
        exact_manifest = exact_case_source / "raw_case_manifest.json"
        for required in (exact_official / "case_definition.json", exact_official / "evaluator_oracle_excerpts.json", exact_official / "state_schema_excerpts.json", exact_manifest):
            if not required.is_file():
                raise SystemExit(f"missing exact case source: {required}")
        exact_definition = load_json(exact_official / "case_definition.json")
        if exact_definition.get("case_unit_id") != case_unit_id:
            raise SystemExit(f"exact case source binding mismatch for {case_unit_id}: {exact_definition.get('case_unit_id')}")
        replace_materialized(packet / "sources/case/official", exact_official)
        replace_materialized(packet / "sources/case/raw_case_manifest.json", exact_manifest)

        user_key = f"user__{suite}__{user_task}"
        injection_key = f"injection__{suite}__{injection_task}"
        user_input = component_root / "inputs" / user_key / "sources"
        injection_input = component_root / "inputs" / injection_key / "sources"
        user_review = component_root / "outputs" / f"{user_key}.json"
        injection_review = component_root / "outputs" / f"{injection_key}.json"
        for required in (user_input, injection_input, user_review, injection_review):
            if not required.exists():
                raise SystemExit(f"missing component source: {required}")
        replace_materialized(packet / "sources/user", user_input)
        replace_materialized(packet / "sources/injection", injection_input)
        replace_materialized(packet / "sources/user_review.json", user_review)
        replace_materialized(packet / "sources/injection_review.json", injection_review)
        for name, source in wiring_sources.items():
            if not source.is_file():
                raise SystemExit(f"missing wiring source: {source}")
            replace_materialized(packet / "runtime_wiring" / name, source)

        record_inputs = []
        record_locks = []
        for task in ordered:
            agent_id = str(task["agent_id"])
            agent_slug = agent_id.lower().replace(" ", "_")
            record_dir = packet / "records" / agent_slug
            record_dir.mkdir(parents=True, exist_ok=True)
            out_prefix = Path(task["out_prefix"]).resolve()
            score_path = out_prefix.with_suffix(".json")
            manifest_path = out_prefix.parent / f"{out_prefix.name}_manifest.json"
            evidence_dir = Path(task["evidence_dir"]).resolve()
            for required in (score_path, manifest_path, evidence_dir):
                if not required.exists():
                    raise SystemExit(f"missing record input: {required}")
            shutil.copy2(score_path, record_dir / "score.json")
            shutil.copy2(manifest_path, record_dir / "score_manifest.json")
            replace_materialized(record_dir / "evidence", evidence_dir)
            score = load_json(score_path)
            record_inputs.append(
                {
                    "task_index": task["task_index"],
                    "run_dir_name": task["run_dir_name"],
                    "run_id": task["run_id"],
                    "agent_id": agent_id,
                    "released_evaluator_label": score["released_evaluator_label"]["value"],
                    "native_evidence_verdict": score["native"]["verdict"],
                    "stronger_verdict": score["stronger"]["verdict"],
                    "workspace_record_root": f"records/{agent_slug}",
                }
            )
            record_locks.append(
                {
                    "task_index": task["task_index"],
                    "run_dir_name": task["run_dir_name"],
                    "agent_id": agent_id,
                    "evidence_tree_sha256": task["evidence_tree_sha256"],
                    "score_sha256": sha256_file(score_path),
                    "score_manifest_sha256": sha256_file(manifest_path),
                }
            )

        review_input = {
            "schema_version": "agentdojo_record_level_conflict_review_input/v1",
            "case_unit_id": case_unit_id,
            "case_index": case_index,
            "scope": "three separately adjudicated agent records",
            "confirmation_rule": (
                "Confirm only when retained artifacts and explicit source pointers establish that "
                "task, target construction, evaluator/oracle, or reward wiring/aggregation actually "
                "checked an outcome different from the outcome the benchmark appears to claim."
            ),
            "records": record_inputs,
        }
        write_json(packet / "review_input.json", review_input)
        packet_lock = {
            "case_unit_id": case_unit_id,
            "packet": str(packet),
            "checklist_sha256": sha256_file(packet / "checklist.yaml"),
            "exact_case_definition_sha256": sha256_file(packet / "sources/case/official/case_definition.json"),
            "exact_evaluator_oracle_sha256": sha256_file(packet / "sources/case/official/evaluator_oracle_excerpts.json"),
            "exact_state_schema_sha256": sha256_file(packet / "sources/case/official/state_schema_excerpts.json"),
            "user_review_sha256": sha256_file(user_review),
            "injection_review_sha256": sha256_file(injection_review),
            "record_locks": record_locks,
        }
        packet_locks.append(packet_lock)
        index.append(
            {
                "case_unit_id": case_unit_id,
                "workspace": str(packet),
                "output": str(outputs_root / f"{case_slug}.json"),
                "log_prefix": str(logs_root / case_slug),
                "expected_records": record_inputs,
            }
        )

    write_json(audit_root / "index.json", index)
    lock_payload = {
        "schema_version": "agentdojo_record_level_conflict_review_lock/v1",
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "task_plan": str(args.task_plan.resolve()),
        "task_plan_sha256": sha256_file(args.task_plan.resolve()),
        "prompt_sha256": sha256_file(contract_root / "conflict_review.prompt.md"),
        "schema_sha256": sha256_file(contract_root / "conflict_review.schema.json"),
        "case_count": len(index),
        "record_count": sum(len(item["expected_records"]) for item in index),
        "packet_locks": packet_locks,
    }
    write_json(audit_root / "conflict_review_lock.json", lock_payload)
    print(json.dumps({"case_count": len(index), "record_count": 2547, "audit_root": str(audit_root)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
