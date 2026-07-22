#!/usr/bin/env python3
"""Create post-run local retrieval and checklist provenance receipts for MiniWoB."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
from typing import Any

from evidence_system.adapters.runtime import build_job_paths, run_remote_blind_command
from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.hashing import sha256_file, sha256_path
from evidence_system.core.paths import resolve_repo_path
from evidence_system.orchestrator.jobs import resolve_infra_target

from resume_miniwob_remaining22_vps2_after_provider_recovery import _plan_all
from run_miniwob_remaining22_vps2_campaign import (
    BUNDLE,
    CONTROL,
    EXPERIMENT_LOCK,
    INFRA,
    NAMESPACE,
    _audit_job,
    _mapping,
)


RESULT_ROOT = f"results/namespaces/{NAMESPACE}/full/miniwob"
INFRA_ATTEMPTS_ROOT = f"results/namespaces/{NAMESPACE}/infra_attempts"
COMPLETION = f"results/namespaces/{NAMESPACE}/campaign_control/final-completion-receipt.json"


def _tree_stats(root: Path) -> dict[str, Any]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return {
        "path": str(root.relative_to(resolve_repo_path("."))),
        "file_count": len(files),
        "size_bytes": sum(path.stat().st_size for path in files),
        "tree_sha256": sha256_path(root),
    }


def main() -> int:
    target = resolve_infra_target("miniwob", _mapping(resolve_repo_path(INFRA)))
    formal = _plan_all(target)
    audits = [_audit_job(item, {"status": "skipped_completed"}) for item in formal]
    if len(audits) != 66:
        raise RuntimeError("post-run audit did not cover all 66 slots")

    manifest = _mapping(resolve_repo_path(
        "experiments/appendix/miniwob_remaining22_vps2_20260719_manifest.yaml"
    ))
    bundle = _mapping(resolve_repo_path(BUNDLE))
    sources = {str(row["case_unit_id"]): dict(row) for row in bundle["sources"]}
    locks = {}
    for row in manifest["contract_locks"]:
        checklist_path = resolve_repo_path(str(row["canonical_hash_source"]))
        case_id = checklist_path.parent.name
        if sha256_file(checklist_path) != row["contract_hash"]:
            raise RuntimeError(f"checklist hash drift: {case_id}")
        locks[case_id] = {**dict(row), "checklist_path": str(checklist_path.relative_to(resolve_repo_path('.')))}
    if set(locks) != set(sources) or len(locks) != 22:
        raise RuntimeError("manifest/source checklist identity sets differ")

    joins = []
    for item, audit in zip(formal, audits, strict=True):
        case_id = str(item.job["case_unit_id"])
        lock = locks[case_id]
        source = sources[case_id]
        if source["contract_id"] != lock["contract_id"]:
            raise RuntimeError(f"source/manifest contract id mismatch: {case_id}")
        paths = build_job_paths(item.job)
        joins.append(
            {
                "job_id": item.job["job_id"],
                "case_unit_id": case_id,
                "agent_id": item.job["agent_id"],
                "seed": item.job["seed"],
                "contract_id": lock["contract_id"],
                "contract_version": lock["contract_version"],
                "contract_hash": lock["contract_hash"],
                "checklist_path": lock["checklist_path"],
                "source_bundle_contract_id": source["contract_id"],
                "native_label": audit["native_label"],
                "native_run_path": str(paths.native_run_dir.relative_to(resolve_repo_path('.'))),
                "raw_run_path": str(paths.raw_run_path.relative_to(resolve_repo_path('.'))),
                "remote_inventory_sha256": audit["remote_inventory_sha256"],
            }
        )
    control = resolve_repo_path(CONTROL)
    join_receipt = {
        "schema_version": "miniwob_checklist_result_join/v1",
        "status": "accepted",
        "created_at": utc_now_iso(),
        "record_count": 66,
        "case_count": 22,
        "read_only_join": True,
        "raw_run_files_modified": False,
        "note": "Correct contract identity is joined from the frozen manifest/source bundle because legacy planner job JSON serialized absent canonical checklist metadata as the string 'None'.",
        "records": joins,
    }
    join_path = control / "provenance-join-index.json"
    write_json(join_path, join_receipt)

    remote_root = f"{target.remote_workdir}/{RESULT_ROOT}"
    remote_command = (
        f"root={shlex.quote(remote_root)}; "
        "test -d \"$root\"; "
        "printf 'job_dirs=%s\\n' \"$(find \"$root\" -mindepth 1 -maxdepth 1 -type d | wc -l)\"; "
        "printf 'run_summaries=%s\\n' \"$(find \"$root\" -mindepth 2 -maxdepth 2 -name run_summary.json -type f | wc -l)\"; "
        "printf 'tree_receipts=%s\\n' \"$(find \"$root\" -mindepth 2 -maxdepth 2 -name remote_tree_receipt.json -type f | wc -l)\""
    )
    remote = run_remote_blind_command(
        target, remote_command, timeout_seconds=60, transient_retry_attempts=1
    )
    if remote.returncode != 0:
        raise RuntimeError("remote final inventory count failed")
    remote_counts = {}
    for line in (remote.stdout or "").splitlines():
        key, value = line.split("=", 1)
        remote_counts[key] = int(value.strip())
    if remote_counts != {"job_dirs": 66, "run_summaries": 66, "tree_receipts": 66}:
        raise RuntimeError(f"remote final inventory count differs: {remote_counts}")

    result_root = resolve_repo_path(RESULT_ROOT)
    infra_root = resolve_repo_path(INFRA_ATTEMPTS_ROOT)
    canonical_retry_attempts = len(
        list(result_root.glob("*/adapter/native_run/openrouter_calls/retry_attempts/*.json"))
    )
    completion_path = resolve_repo_path(COMPLETION)
    completion = _mapping(completion_path)
    if completion.get("status") != "accepted" or completion.get("slot_count") != 66:
        raise RuntimeError("full completion receipt is not accepted")
    preserved_infra_attempt_tree = _tree_stats(infra_root) if infra_root.is_dir() else None
    retrieval = {
        "schema_version": "miniwob_vps2_local_retrieval/v1",
        "status": "accepted",
        "created_at": utc_now_iso(),
        "namespace": NAMESPACE,
        "remote_counts": remote_counts,
        "local_result_tree": _tree_stats(result_root),
        "preserved_infra_attempt_tree": preserved_infra_attempt_tree,
        "error_attempt_artifacts_retained": preserved_infra_attempt_tree is not None,
        "canonical_slot_count": 66,
        "local_audited_slot_count": len(audits),
        "canonical_provider_retry_attempt_files": canonical_retry_attempts,
        "all_remote_local_per_job_inventories_verified": True,
        "all_artifacts_pulled_to_local": True,
        "completion_receipt_path": COMPLETION,
        "completion_receipt_sha256": sha256_file(completion_path),
        "provenance_join_path": str(join_path.relative_to(resolve_repo_path('.'))),
        "provenance_join_sha256": sha256_file(join_path),
        "experiment_lock_path": EXPERIMENT_LOCK,
        "experiment_lock_sha256": sha256_file(resolve_repo_path(EXPERIMENT_LOCK)),
    }
    retrieval_path = control / "local-retrieval-acceptance.json"
    write_json(retrieval_path, retrieval)
    print(json.dumps(retrieval, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
