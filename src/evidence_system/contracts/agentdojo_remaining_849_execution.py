"""Local execution contract for the 849 not-yet-paper AgentDojo cases.

This module deliberately does not extend or relax the formal 949-case
execution contract.  It only builds and verifies an immutable local campaign
manifest and lock for the exact set difference between the full 949 packet
tree and the historical paper 100 packet tree.  It performs no network,
deployment, execution, or evidence-retrieval operation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
import os
from pathlib import Path
import re
import stat
from typing import Any

from evidence_system.adapters.agentdojo_runtime_control import load_runtime_policy
from evidence_system.adapters.runtime import (
    formal_job_binding_sha256,
    formal_job_file_sha256,
)
from evidence_system.contracts.common import (
    ContractLifecycleError,
    display_path,
    load_mapping,
    utc_now_iso,
    write_json,
)
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import resolve_repo_path


SCHEMA_VERSION = "agentdojo_remaining_849_execution_manifest/v1"
LOCK_SCHEMA_VERSION = "agentdojo_remaining_849_execution_lock/v1"
CAMPAIGN_ID = "agentdojo_v1.2.2_remaining_849_two_vps"
LOCK_ID = f"{CAMPAIGN_ID}_execution"

EXPECTED_FULL_CASE_COUNT = 949
EXPECTED_PAPER_CASE_COUNT = 100
EXPECTED_REMAINING_CASE_COUNT = 849
EXPECTED_AGENTS = ("Agent A", "Agent B", "Agent C")
EXPECTED_JOB_COUNT = EXPECTED_REMAINING_CASE_COUNT * len(EXPECTED_AGENTS)
EXPECTED_FULL_JOB_COUNT = EXPECTED_FULL_CASE_COUNT * len(EXPECTED_AGENTS)
SUITE_ORDER = ("workspace", "travel", "banking", "slack")
EXPECTED_FULL_SUITE_COUNTS = {
    "workspace": 560,
    "travel": 140,
    "banking": 144,
    "slack": 105,
}
EXPECTED_PAPER_SUITE_COUNTS = {
    "workspace": 54,
    "travel": 13,
    "banking": 18,
    "slack": 15,
}
EXPECTED_REMAINING_SUITE_COUNTS = {
    "workspace": 506,
    "travel": 127,
    "banking": 126,
    "slack": 90,
}
EXPECTED_SHARD_QUOTAS = {
    "vps1": {
        "workspace": 253,
        "travel": 63,
        "banking": 63,
        "slack": 45,
    },
    "vps2": {
        "workspace": 253,
        "travel": 64,
        "banking": 63,
        "slack": 45,
    },
}
EXPECTED_SHARD_CASE_COUNTS = {"vps1": 424, "vps2": 425}
EXPECTED_SHARD_JOB_COUNTS = {"vps1": 1_272, "vps2": 1_275}
CONSECUTIVE_PROBLEM_CASE_THRESHOLD = 4
FINALIZED_POLICY_BASENAME = "openrouter_runtime_policy.finalized.v14.json"
HOST_POLICY_SCHEMA_VERSION = "agentdojo_openrouter_runtime_policy/v1"
EXPECTED_HOST_LIMITS = {
    "max_concurrent_requests": 8,
    "requests_per_minute": 48,
    "tokens_per_minute": 957_376,
    "per_model_concurrent_requests_by_agent_lane": {
        "Agent A": 8,
        "Agent B": 4,
        "Agent C": 4,
    },
    "maximum_run_cost_usd": 325.0,
}
EXPECTED_HOST_PER_MODEL_LIMITS = [
    {
        "model_id": "openai/gpt-5.4",
        "requests_per_minute": 48,
        "tokens_per_minute": 957_376,
        "concurrent_requests": 8,
    },
    {
        "model_id": "anthropic/claude-opus-4.7",
        "requests_per_minute": 24,
        "tokens_per_minute": 465_797,
        "concurrent_requests": 4,
    },
    {
        "model_id": "deepseek/deepseek-v4-pro",
        "requests_per_minute": 33,
        "tokens_per_minute": 633_265,
        "concurrent_requests": 4,
    },
]

EXPERIMENT_ROOT = Path("experiments/agentdojo_full_v1.2.2_direct")
DEFAULT_FULL_CASE_PACKETS_ROOT = EXPERIMENT_ROOT / "case_packets/agentdojo"
DEFAULT_PAPER_CASE_PACKETS_ROOT = Path("experiments/case_packets/agentdojo")
DEFAULT_JOBS_ROOT = EXPERIMENT_ROOT / "jobs/full"
DEFAULT_FINALIZED_POLICY = (
    EXPERIMENT_ROOT / "runtime/openrouter_runtime_policy.finalized.v14.json"
)
DEFAULT_SOURCE_FILES = {
    "full_manifest": EXPERIMENT_ROOT / "experiment_manifest.yaml",
    "full_catalog": (
        EXPERIMENT_ROOT / "official_splits/agentdojo_selected_task_sources.json"
    ),
    "full_source_bundle": (
        EXPERIMENT_ROOT / "source_bundles/case_packet_source_bundle.json"
    ),
    "agents_config": Path("configs/agents.yaml"),
}
DEFAULT_OUTPUT_MANIFEST = EXPERIMENT_ROOT / "remaining_849/campaign_manifest.json"
DEFAULT_OUTPUT_LOCK = EXPERIMENT_ROOT / "remaining_849/execution_lock.json"

_CASE_ID_RE = re.compile(
    r"^v1\.2\.2:(workspace|travel|banking|slack):"
    r"user_task_(\d+):injection_task_(\d+)$"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_SOURCE_FILE_LABELS = frozenset(DEFAULT_SOURCE_FILES)
_REMOTE_ROOT_FIELDS = (
    "remote_raw_root",
    "blind_aggregate_root",
    "runtime_state_root",
    "failed_attempt_archive_root",
    "retrieval_snapshot_root",
)


@dataclass(frozen=True)
class Remaining849ExecutionLockResult:
    manifest_path: Path
    manifest_sha256: str
    lock_path: Path
    lock_sha256: str
    manifest: dict[str, Any]
    lock: dict[str, Any]
    created: bool


def build_remaining_849_execution_manifest(
    *,
    infra_paths: Sequence[str | Path],
    host_policy_paths: Sequence[str | Path],
    full_case_packets_root: str | Path = DEFAULT_FULL_CASE_PACKETS_ROOT,
    paper_case_packets_root: str | Path = DEFAULT_PAPER_CASE_PACKETS_ROOT,
    jobs_root: str | Path = DEFAULT_JOBS_ROOT,
    finalized_policy_path: str | Path = DEFAULT_FINALIZED_POLICY,
    source_files: Mapping[str, str | Path] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build the exact local 849-case campaign manifest without writing it."""

    source_file_paths = dict(source_files or DEFAULT_SOURCE_FILES)
    if set(source_file_paths) != _REQUIRED_SOURCE_FILE_LABELS:
        raise ContractLifecycleError(
            "remaining-849 source file labels must be exactly "
            f"{sorted(_REQUIRED_SOURCE_FILE_LABELS)}"
        )
    source_bindings = {
        label: _file_binding(path, label=f"source file {label}")
        for label, path in sorted(source_file_paths.items())
    }

    full_root = _regular_directory(full_case_packets_root, "full case-packet root")
    paper_root = _regular_directory(
        paper_case_packets_root, "paper case-packet root"
    )
    if full_root == paper_root:
        raise ContractLifecycleError("full and paper case-packet roots must differ")
    full_packets = _packet_index(
        full_root,
        label="full case-packet tree",
        expected_count=EXPECTED_FULL_CASE_COUNT,
        expected_suite_counts=EXPECTED_FULL_SUITE_COUNTS,
    )
    paper_packets = _packet_index(
        paper_root,
        label="paper case-packet tree",
        expected_count=EXPECTED_PAPER_CASE_COUNT,
        expected_suite_counts=EXPECTED_PAPER_SUITE_COUNTS,
    )
    full_ids = set(full_packets)
    paper_ids = set(paper_packets)
    if not paper_ids.issubset(full_ids):
        outside = sorted(paper_ids - full_ids, key=_case_sort_key)
        raise ContractLifecycleError(
            f"paper case-packet set is not a subset of full set: {outside[:3]}"
        )
    remaining_ids = sorted(full_ids - paper_ids, key=_case_sort_key)
    _require_case_set_counts(
        remaining_ids,
        expected_count=EXPECTED_REMAINING_CASE_COUNT,
        expected_suite_counts=EXPECTED_REMAINING_SUITE_COUNTS,
        label="remaining full-minus-paper case set",
    )

    shard_by_case = deterministic_two_vps_shards(remaining_ids)
    case_entries = [
        {
            "case_unit_id": case_id,
            "task_id": full_packets[case_id]["task_id"],
            "suite": _case_parts(case_id)[0],
            "packet_dir_name": full_packets[case_id]["directory_name"],
            "shard_id": shard_by_case[case_id],
        }
        for case_id in remaining_ids
    ]

    job_root = _regular_directory(jobs_root, "full source job root")
    all_jobs = _job_index(job_root, full_ids=full_ids)
    job_entries = _remaining_job_entries(
        all_jobs,
        case_entries=case_entries,
        shard_by_case=shard_by_case,
    )
    shard_entries = _shard_entries(case_entries, job_entries)

    policy_binding = _finalized_policy_binding(finalized_policy_path)
    host_policy_bindings = _two_host_policy_bindings(
        host_policy_paths,
        base_policy_binding=policy_binding,
    )
    infra_bindings = _two_infra_bindings(infra_paths)
    shard_runtime_bindings = [
        {
            "shard_id": shard_id,
            "infra_file_sha256": infra_bindings[index]["file_sha256"],
            "host_policy_file_sha256": host_policy_bindings[index][
                "file_sha256"
            ],
            "host_policy_semantic_sha256": host_policy_bindings[index][
                "semantic_sha256"
            ],
        }
        for index, shard_id in enumerate(("vps1", "vps2"))
    ]
    runtime = {
        "base_finalized_v14_policy": policy_binding,
        "base_policy_is_reference_only": True,
        "host_must_not_load_base_policy_directly": True,
        "host_conservative_policies": host_policy_bindings,
        "infra": infra_bindings,
        "shard_runtime_bindings": shard_runtime_bindings,
        "two_host_static_partition": {
            "per_host": EXPECTED_HOST_LIMITS,
            "aggregate_concurrent_requests": 16,
            "aggregate_requests_per_minute": 96,
            "aggregate_tokens_per_minute": 1_914_752,
            "aggregate_maximum_run_cost_usd": 650.0,
            "rate_partition": "two_equal_host_local_sqlite_partitions",
        },
        "agent_batch_order": list(EXPECTED_AGENTS),
        "cross_agent_model_overlap_forbidden": True,
    }

    definition = {
        "inputs": {
            "source_files": source_bindings,
            "full_case_packets": _tree_binding(full_root),
            "paper_case_packets": _tree_binding(paper_root),
            "full_jobs": _tree_binding(job_root),
        },
        "selection": {
            "method": "exact_top_level_packet_directory_set_difference",
            "expression": "full_949_case_packet_dirs_minus_paper_100_case_packet_dirs",
            "full_case_count": len(full_ids),
            "paper_case_count": len(paper_ids),
            "remaining_case_count": len(remaining_ids),
            "full_suite_counts": _ordered_suite_counts(full_ids),
            "paper_suite_counts": _ordered_suite_counts(paper_ids),
            "remaining_suite_counts": _ordered_suite_counts(remaining_ids),
            "full_case_ids_sha256": sha256_object(
                sorted(full_ids, key=_case_sort_key)
            ),
            "excluded_paper_case_ids_sha256": sha256_object(
                sorted(paper_ids, key=_case_sort_key)
            ),
            "excluded_paper_case_ids": sorted(paper_ids, key=_case_sort_key),
            "remaining_case_entries_sha256": sha256_object(case_entries),
            "remaining_case_entries": case_entries,
        },
        "sharding": {
            "method": "per_suite_natural_sort_alternating_with_exact_quotas",
            "suite_order": list(SUITE_ORDER),
            "shard_order": ["vps1", "vps2"],
            "exact_suite_quotas": EXPECTED_SHARD_QUOTAS,
            "case_counts": EXPECTED_SHARD_CASE_COUNTS,
            "job_counts": EXPECTED_SHARD_JOB_COUNTS,
            "case_assignment_sha256": sha256_object(
                [
                    {
                        "case_unit_id": row["case_unit_id"],
                        "shard_id": row["shard_id"],
                    }
                    for row in case_entries
                ]
            ),
            "shards_sha256": sha256_object(shard_entries),
            "shards": shard_entries,
            "all_three_agents_for_a_case_must_share_one_vps": True,
        },
        "job_plan": {
            "ordering": "agent_batch_then_suite_then_natural_case",
            "agents": list(EXPECTED_AGENTS),
            "case_count": EXPECTED_REMAINING_CASE_COUNT,
            "job_count": len(job_entries),
            "entries_sha256": sha256_object(job_entries),
            "entries": job_entries,
            "exact_source_job_payload_required": True,
            "exact_source_job_file_sha256_required": True,
            "exact_job_binding_sha256_required": True,
        },
        "runtime": runtime,
        "monitoring_policy": _monitoring_policy(),
        "sealed_evidence_policy": _sealed_evidence_policy(),
    }
    _validate_definition_invariants(definition)
    return {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": CAMPAIGN_ID,
        "created_at": created_at or utc_now_iso(),
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }


def deterministic_two_vps_shards(case_ids: Sequence[str]) -> dict[str, str]:
    """Assign sorted cases alternately while satisfying the locked suite quotas."""

    normalized = [str(case_id) for case_id in case_ids]
    if len(normalized) != len(set(normalized)):
        raise ContractLifecycleError("remaining case IDs must be unique before sharding")
    _require_case_set_counts(
        normalized,
        expected_count=EXPECTED_REMAINING_CASE_COUNT,
        expected_suite_counts=EXPECTED_REMAINING_SUITE_COUNTS,
        label="sharding input",
    )
    by_suite: dict[str, list[str]] = defaultdict(list)
    for case_id in normalized:
        by_suite[_case_parts(case_id)[0]].append(case_id)
    assignment: dict[str, str] = {}
    for suite in SUITE_ORDER:
        ordered = sorted(by_suite[suite], key=_case_sort_key)
        quotas = {
            shard_id: EXPECTED_SHARD_QUOTAS[shard_id][suite]
            for shard_id in ("vps1", "vps2")
        }
        # The shard with the extra odd-suite case starts; equal quotas begin at
        # vps1.  This preserves strict alternation until both quotas are met.
        next_shard = "vps2" if quotas["vps2"] > quotas["vps1"] else "vps1"
        used = {"vps1": 0, "vps2": 0}
        for case_id in ordered:
            other = "vps2" if next_shard == "vps1" else "vps1"
            shard_id = next_shard if used[next_shard] < quotas[next_shard] else other
            if used[shard_id] >= quotas[shard_id]:
                raise ContractLifecycleError(
                    f"shard quota exhausted early for suite {suite}"
                )
            assignment[case_id] = shard_id
            used[shard_id] += 1
            next_shard = "vps2" if shard_id == "vps1" else "vps1"
        if used != quotas:
            raise ContractLifecycleError(
                f"shard suite quota mismatch for {suite}: {used} != {quotas}"
            )
    _validate_shard_assignment(assignment)
    return assignment


def publish_host_conservative_policies(
    *,
    base_policy_path: str | Path = DEFAULT_FINALIZED_POLICY,
    output_paths: Sequence[str | Path],
    execution_key_fingerprint_sha256: str,
) -> dict[str, Any]:
    """Create two parser-compatible 8-worker policies, or accept identical files."""

    base_binding = _finalized_policy_binding(base_policy_path)
    base_file = _regular_file(base_policy_path, "base finalized-v14 policy")
    base_payload = load_mapping(base_file)
    derived = derive_host_conservative_policy_payload(
        base_payload,
        execution_key_fingerprint_sha256=execution_key_fingerprint_sha256,
    )
    # The derivation helper already parses the payload.  Parse it once more at
    # the publication boundary so future refactors cannot bypass worker
    # compatibility by returning an unchecked mapping.
    parsed = load_runtime_policy(derived)
    if parsed.semantic_sha256 != sha256_object(derived):
        raise ContractLifecycleError("derived host policy semantic hash differs")
    if len(output_paths) != 2:
        raise ContractLifecycleError(
            "host policy publication requires exactly two output paths"
        )
    outputs = [resolve_repo_path(path) for path in output_paths]
    if len({path.absolute() for path in outputs}) != 2:
        raise ContractLifecycleError("host policy output paths must be distinct")
    if any(path.resolve() == base_file for path in outputs):
        raise ContractLifecycleError(
            "host policy output must not replace the base finalized-v14 policy"
        )
    # Preflight every existing destination before the first write, avoiding a
    # partial two-policy publication when the second path conflicts.
    for path in outputs:
        if path.exists() or path.is_symlink():
            existing = load_mapping(_regular_file(path, "host policy output"))
            if existing != derived:
                raise ContractLifecycleError(
                    f"refusing to replace a non-identical host policy: {path}"
                )
    created = [_write_new_or_identical(path, derived) for path in outputs]
    bindings = _two_host_policy_bindings(
        outputs,
        base_policy_binding=base_binding,
    )
    return {
        "base_policy": base_binding,
        "host_policies": bindings,
        "created": created,
        "worker_parser_accepted": True,
    }


def publish_remaining_849_execution_lock(
    *,
    infra_paths: Sequence[str | Path],
    host_policy_paths: Sequence[str | Path],
    manifest_path: str | Path = DEFAULT_OUTPUT_MANIFEST,
    lock_path: str | Path = DEFAULT_OUTPUT_LOCK,
    full_case_packets_root: str | Path = DEFAULT_FULL_CASE_PACKETS_ROOT,
    paper_case_packets_root: str | Path = DEFAULT_PAPER_CASE_PACKETS_ROOT,
    jobs_root: str | Path = DEFAULT_JOBS_ROOT,
    finalized_policy_path: str | Path = DEFAULT_FINALIZED_POLICY,
    source_files: Mapping[str, str | Path] | None = None,
    created_at: str | None = None,
    locked_at: str | None = None,
) -> Remaining849ExecutionLockResult:
    """Publish a new local manifest and lock, or accept byte-identical files."""

    manifest = build_remaining_849_execution_manifest(
        infra_paths=infra_paths,
        host_policy_paths=host_policy_paths,
        full_case_packets_root=full_case_packets_root,
        paper_case_packets_root=paper_case_packets_root,
        jobs_root=jobs_root,
        finalized_policy_path=finalized_policy_path,
        source_files=source_files,
        created_at=created_at,
    )
    manifest_file = resolve_repo_path(manifest_path)
    manifest_created = _write_new_or_identical(manifest_file, manifest)
    lock = _build_lock_payload(
        manifest_file,
        manifest,
        locked_at=locked_at or utc_now_iso(),
    )
    lock_file = resolve_repo_path(lock_path)
    lock_created = _write_new_or_identical(lock_file, lock)
    return Remaining849ExecutionLockResult(
        manifest_path=manifest_file,
        manifest_sha256=sha256_file(manifest_file),
        lock_path=lock_file,
        lock_sha256=sha256_file(lock_file),
        manifest=manifest,
        lock=lock,
        created=manifest_created or lock_created,
    )


def verify_remaining_849_execution_lock(
    lock_path: str | Path = DEFAULT_OUTPUT_LOCK,
    *,
    manifest_path: str | Path | None = None,
) -> Remaining849ExecutionLockResult:
    """Recompute every local input and reject any manifest or lock drift."""

    lock_file = _regular_file(lock_path, "remaining-849 execution lock")
    lock = load_mapping(lock_file)
    _validate_lock_shape(lock)
    definition = dict(lock["definition"])
    manifest_ref = dict(definition["manifest"])
    manifest_file = _regular_file(
        manifest_path or str(manifest_ref["path"]),
        "remaining-849 campaign manifest",
    )
    if manifest_path is not None and manifest_file != resolve_repo_path(
        str(manifest_ref["path"])
    ).resolve():
        raise ContractLifecycleError("explicit manifest path differs from execution lock")
    if manifest_ref["file_sha256"] != sha256_file(manifest_file):
        raise ContractLifecycleError("campaign manifest file SHA-256 is stale")
    manifest = load_mapping(manifest_file)
    _validate_manifest_shape(manifest)
    if manifest_ref["semantic_sha256"] != sha256_object(manifest):
        raise ContractLifecycleError("campaign manifest semantic SHA-256 is stale")

    inputs = dict(dict(manifest["definition"])["inputs"])
    runtime = dict(dict(manifest["definition"])["runtime"])
    source_refs = dict(inputs["source_files"])
    rebuilt = build_remaining_849_execution_manifest(
        infra_paths=[row["path"] for row in list(runtime["infra"])],
        host_policy_paths=[
            row["path"]
            for row in list(runtime["host_conservative_policies"])
        ],
        full_case_packets_root=dict(inputs["full_case_packets"])["path"],
        paper_case_packets_root=dict(inputs["paper_case_packets"])["path"],
        jobs_root=dict(inputs["full_jobs"])["path"],
        finalized_policy_path=dict(runtime["base_finalized_v14_policy"])["path"],
        source_files={
            label: dict(binding)["path"]
            for label, binding in source_refs.items()
        },
        created_at=str(manifest["created_at"]),
    )
    if rebuilt != manifest:
        raise ContractLifecycleError(
            "remaining-849 campaign manifest differs from recomputed local inputs"
        )
    expected_lock = _build_lock_payload(
        manifest_file,
        manifest,
        locked_at=str(lock["locked_at"]),
    )
    if expected_lock != lock:
        raise ContractLifecycleError(
            "remaining-849 execution lock differs from recomputed manifest bindings"
        )
    return Remaining849ExecutionLockResult(
        manifest_path=manifest_file,
        manifest_sha256=sha256_file(manifest_file),
        lock_path=lock_file,
        lock_sha256=sha256_file(lock_file),
        manifest=manifest,
        lock=lock,
        created=False,
    )


def _packet_index(
    root: Path,
    *,
    label: str,
    expected_count: int,
    expected_suite_counts: Mapping[str, int],
) -> dict[str, dict[str, str]]:
    entries = sorted(root.iterdir(), key=lambda path: path.name)
    if len(entries) != expected_count:
        raise ContractLifecycleError(
            f"{label} must contain exactly {expected_count} top-level directories; "
            f"found {len(entries)}"
        )
    result: dict[str, dict[str, str]] = {}
    for directory in entries:
        if directory.is_symlink() or not directory.is_dir():
            raise ContractLifecycleError(
                f"{label} contains a non-directory or symlink: {directory.name}"
            )
        raw_manifest = _regular_file(
            directory / "raw_case_manifest.json",
            f"{label} raw-case manifest",
        )
        payload = load_mapping(raw_manifest)
        case_id = str(payload.get("case_unit_id") or "")
        suite, _user, _injection = _case_parts(case_id)
        expected_name = case_id.replace(":", "_")
        if directory.name != expected_name:
            raise ContractLifecycleError(
                f"packet directory name differs from case ID: {directory.name}"
            )
        task_id = str(payload.get("task_id") or "")
        if task_id != case_id.removeprefix("v1.2.2:"):
            raise ContractLifecycleError(f"packet task ID differs for {case_id}")
        if case_id in result:
            raise ContractLifecycleError(f"duplicate packet case ID: {case_id}")
        result[case_id] = {
            "task_id": task_id,
            "suite": suite,
            "directory_name": directory.name,
        }
    _require_case_set_counts(
        list(result),
        expected_count=expected_count,
        expected_suite_counts=expected_suite_counts,
        label=label,
    )
    return result


def _job_index(
    root: Path,
    *,
    full_ids: set[str],
) -> dict[tuple[str, str], tuple[Path, dict[str, Any]]]:
    paths = sorted(root.iterdir(), key=lambda path: path.name)
    if len(paths) != EXPECTED_FULL_JOB_COUNT:
        raise ContractLifecycleError(
            "full source job root must contain exactly "
            f"{EXPECTED_FULL_JOB_COUNT} files; found {len(paths)}"
        )
    result: dict[tuple[str, str], tuple[Path, dict[str, Any]]] = {}
    for path in paths:
        file_path = _regular_file(path, "full source job file")
        if file_path.suffix != ".json":
            raise ContractLifecycleError(f"source job is not JSON: {file_path.name}")
        payload = load_mapping(file_path)
        case_id = str(payload.get("case_unit_id") or "")
        agent_id = str(payload.get("agent_id") or "")
        _case_parts(case_id)
        if case_id not in full_ids or agent_id not in EXPECTED_AGENTS:
            raise ContractLifecycleError(
                f"source job is outside the full case/agent product: {file_path.name}"
            )
        if payload.get("domain") != "agentdojo" or payload.get("phase") != "full":
            raise ContractLifecycleError(f"source job scope differs: {file_path.name}")
        if payload.get("experiment_type") != "appendix":
            raise ContractLifecycleError(
                f"source job experiment type differs: {file_path.name}"
            )
        if str(payload.get("task_id") or "") != case_id.removeprefix("v1.2.2:"):
            raise ContractLifecycleError(f"source job task differs: {file_path.name}")
        if str(payload.get("job_id") or "") + ".json" != file_path.name:
            raise ContractLifecycleError(f"source job filename differs: {file_path.name}")
        if sha256_file(file_path) != formal_job_file_sha256(payload):
            raise ContractLifecycleError(
                f"source job file is not canonical sorted JSON: {file_path.name}"
            )
        key = (case_id, agent_id)
        if key in result:
            raise ContractLifecycleError(f"duplicate source job mapping: {key}")
        result[key] = (file_path, payload)
    expected = {(case_id, agent) for case_id in full_ids for agent in EXPECTED_AGENTS}
    if set(result) != expected:
        raise ContractLifecycleError("source jobs do not equal the full case/agent product")
    return result


def _remaining_job_entries(
    all_jobs: Mapping[tuple[str, str], tuple[Path, dict[str, Any]]],
    *,
    case_entries: Sequence[Mapping[str, Any]],
    shard_by_case: Mapping[str, str],
) -> list[dict[str, Any]]:
    cases = [str(row["case_unit_id"]) for row in case_entries]
    entries: list[dict[str, Any]] = []
    ordinal = 0
    for agent_id in EXPECTED_AGENTS:
        for case_id in cases:
            path, payload = all_jobs[(case_id, agent_id)]
            payload_sha = formal_job_binding_sha256(payload)
            file_sha = sha256_file(path)
            shard_id = shard_by_case[case_id]
            campaign_binding = {
                "campaign_id": CAMPAIGN_ID,
                "case_unit_id": case_id,
                "agent_id": agent_id,
                "shard_id": shard_id,
                "source_job_payload_sha256": payload_sha,
                "source_job_file_sha256": file_sha,
            }
            entries.append(
                {
                    "ordinal": ordinal,
                    "case_unit_id": case_id,
                    "task_id": str(payload["task_id"]),
                    "agent_id": agent_id,
                    "shard_id": shard_id,
                    "source_job_path": display_path(path),
                    "job_payload": payload,
                    "job_payload_sha256": payload_sha,
                    "job_file_sha256": file_sha,
                    "job_file_canonical_sha256": formal_job_file_sha256(payload),
                    "job_binding_sha256": payload_sha,
                    "campaign_job_binding_sha256": sha256_object(
                        campaign_binding
                    ),
                }
            )
            ordinal += 1
    if len(entries) != EXPECTED_JOB_COUNT:
        raise ContractLifecycleError(
            f"remaining job plan must contain exactly {EXPECTED_JOB_COUNT} entries"
        )
    return entries


def _shard_entries(
    case_entries: Sequence[Mapping[str, Any]],
    job_entries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for shard_id in ("vps1", "vps2"):
        cases = [
            str(row["case_unit_id"])
            for row in case_entries
            if row["shard_id"] == shard_id
        ]
        jobs = [
            str(row["campaign_job_binding_sha256"])
            for row in job_entries
            if row["shard_id"] == shard_id
        ]
        result.append(
            {
                "shard_id": shard_id,
                "case_count": len(cases),
                "job_count": len(jobs),
                "suite_counts": _ordered_suite_counts(cases),
                "case_ids_sha256": sha256_object(cases),
                "case_ids": cases,
                "campaign_job_bindings_sha256": sha256_object(jobs),
            }
        )
    return result


def _finalized_policy_binding(path: str | Path) -> dict[str, Any]:
    policy_file = _regular_file(path, "finalized v14 runtime policy")
    if policy_file.name != FINALIZED_POLICY_BASENAME:
        raise ContractLifecycleError(
            f"runtime policy must be {FINALIZED_POLICY_BASENAME}"
        )
    payload = load_mapping(policy_file)
    try:
        parsed = load_runtime_policy(payload)
    except (TypeError, ValueError) as exc:
        raise ContractLifecycleError(
            "base finalized-v14 policy is not accepted by the worker parser"
        ) from exc
    if parsed.lifecycle_status != "finalized":
        raise ContractLifecycleError("runtime policy is not finalized")
    if parsed.formal_execution_allowed is not True:
        raise ContractLifecycleError("runtime policy does not allow formal execution")
    if parsed.max_concurrent_requests != 16:
        raise ContractLifecycleError("finalized v14 policy concurrency must equal 16")
    base_key_fingerprint = str(parsed.execution_key_fingerprint_sha256 or "")
    if _SHA256_RE.fullmatch(base_key_fingerprint) is None:
        raise ContractLifecycleError(
            "finalized v14 policy execution key fingerprint is invalid"
        )
    return {
        "path": display_path(policy_file),
        "file_sha256": sha256_file(policy_file),
        "semantic_sha256": parsed.semantic_sha256,
        "schema_version": str(payload.get("schema_version") or ""),
        "revision": "finalized.v14",
        "lifecycle_status": "finalized",
        "formal_execution_allowed": True,
        "max_concurrent_requests": parsed.max_concurrent_requests,
        "execution_key_fingerprint_sha256": base_key_fingerprint,
    }


def _two_host_policy_bindings(
    paths: Sequence[str | Path],
    *,
    base_policy_binding: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if len(paths) != 2:
        raise ContractLifecycleError(
            "remaining-849 campaign requires exactly two host-derived policies"
        )
    resolved = [
        _regular_file(path, "host-derived conservative runtime policy")
        for path in paths
    ]
    if len(set(resolved)) != 2:
        raise ContractLifecycleError(
            "the two host-derived runtime policy files must be distinct"
        )
    base_path = resolve_repo_path(str(base_policy_binding["path"])).resolve()
    if base_path in resolved:
        raise ContractLifecycleError(
            "a VPS must not load the complete base finalized-v14 policy directly"
        )
    base_payload = load_mapping(base_path)
    bindings = [
        _host_policy_binding(
            path,
            shard_id=f"vps{index}",
            base_policy_binding=base_policy_binding,
            base_policy_payload=base_payload,
        )
        for index, path in enumerate(resolved, start=1)
    ]
    fingerprints = {
        str(binding["execution_key_fingerprint_sha256"])
        for binding in bindings
    }
    if len(fingerprints) != 1:
        raise ContractLifecycleError(
            "two host policies must bind the same statically partitioned execution key"
        )
    base_fingerprint = str(
        base_policy_binding["execution_key_fingerprint_sha256"]
    )
    if _SHA256_RE.fullmatch(base_fingerprint) is None:
        raise ContractLifecycleError("base policy execution key fingerprint is invalid")
    return bindings


def _host_policy_binding(
    path: Path,
    *,
    shard_id: str,
    base_policy_binding: Mapping[str, Any],
    base_policy_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = load_mapping(path)
    try:
        parsed = load_runtime_policy(payload)
    except (TypeError, ValueError) as exc:
        raise ContractLifecycleError(
            f"{shard_id} host policy is not accepted by the worker parser"
        ) from exc
    if payload.get("schema_version") != HOST_POLICY_SCHEMA_VERSION:
        raise ContractLifecycleError(f"{shard_id} host policy schema differs")
    if parsed.lifecycle_status != "finalized":
        raise ContractLifecycleError(f"{shard_id} host policy is not finalized")
    if parsed.formal_execution_allowed is not True:
        raise ContractLifecycleError(
            f"{shard_id} host policy does not allow formal execution"
        )
    fingerprint = str(parsed.execution_key_fingerprint_sha256 or "")
    if _SHA256_RE.fullmatch(fingerprint) is None:
        raise ContractLifecycleError(
            f"{shard_id} host policy execution key fingerprint is invalid"
        )
    expected_payload = derive_host_conservative_policy_payload(
        base_policy_payload,
        execution_key_fingerprint_sha256=fingerprint,
    )
    if payload != expected_payload:
        raise ContractLifecycleError(
            f"{shard_id} host policy is not the exact conservative base-v14 derivation"
        )
    model_limits = parsed.per_model_safe_limits or {}
    observed_limits = {
        "max_concurrent_requests": parsed.max_concurrent_requests,
        "requests_per_minute": parsed.requests_per_minute,
        "tokens_per_minute": parsed.tokens_per_minute,
        "per_model_concurrent_requests_by_agent_lane": {
            agent_id: int(model_limits[model_id]["concurrent_requests"])
            for agent_id, model_id in zip(
                EXPECTED_AGENTS,
                (row["model_id"] for row in EXPECTED_HOST_PER_MODEL_LIMITS),
                strict=True,
            )
        },
        "maximum_run_cost_usd": parsed.budget.maximum_run_cost_usd,
    }
    if observed_limits != EXPECTED_HOST_LIMITS:
        raise ContractLifecycleError(
            f"{shard_id} host policy limits differ: "
            f"{observed_limits} != {EXPECTED_HOST_LIMITS}"
        )
    return {
        "shard_id": shard_id,
        "path": display_path(path),
        "file_sha256": sha256_file(path),
        "semantic_sha256": parsed.semantic_sha256,
        "schema_version": HOST_POLICY_SCHEMA_VERSION,
        "execution_key_fingerprint_sha256": fingerprint,
        "limits": EXPECTED_HOST_LIMITS,
        "per_model_safe_limits": EXPECTED_HOST_PER_MODEL_LIMITS,
        "worker_parser_accepted": True,
        "derivation": "deep_copy_base_v14_with_only_locked_host_partition_fields_changed",
        "base_policy_file_sha256": base_policy_binding["file_sha256"],
        "base_policy_semantic_sha256": base_policy_binding["semantic_sha256"],
    }


def derive_host_conservative_policy_payload(
    base_policy: Mapping[str, Any],
    *,
    execution_key_fingerprint_sha256: str,
) -> dict[str, Any]:
    """Return a worker-compatible 8-worker policy derived from finalized v14."""

    fingerprint = str(execution_key_fingerprint_sha256)
    if _SHA256_RE.fullmatch(fingerprint) is None:
        raise ContractLifecycleError("host policy execution key fingerprint is invalid")
    try:
        parsed_base = load_runtime_policy(base_policy)
    except (TypeError, ValueError) as exc:
        raise ContractLifecycleError(
            "host policy base is not accepted by the worker parser"
        ) from exc
    if (
        parsed_base.lifecycle_status != "finalized"
        or parsed_base.formal_execution_allowed is not True
        or parsed_base.max_concurrent_requests != 16
    ):
        raise ContractLifecycleError(
            "host policy base must be the finalized 16-worker v14 policy"
        )
    derived = copy.deepcopy(dict(parsed_base.raw))
    derived["max_concurrent_requests"] = 8
    derived["requests_per_minute"] = 48
    derived["tokens_per_minute"] = 957_376
    override = derived["operational_override"]
    override["effective_values"] = {
        "global_concurrent_requests": 8,
        "requests_per_minute": 48,
        "tokens_per_minute": 957_376,
    }
    override["per_model_safe_limits"] = copy.deepcopy(
        EXPECTED_HOST_PER_MODEL_LIMITS
    )
    override["execution_key_fingerprint_sha256"] = fingerprint
    derived["budget"]["maximum_run_cost_usd"] = 325.0
    try:
        return dict(load_runtime_policy(derived).raw)
    except (TypeError, ValueError) as exc:
        raise ContractLifecycleError(
            "derived host policy is not accepted by the worker parser"
        ) from exc


def _two_infra_bindings(paths: Sequence[str | Path]) -> list[dict[str, Any]]:
    if len(paths) != 2:
        raise ContractLifecycleError("remaining-849 campaign requires exactly two infra files")
    resolved = [_regular_file(path, "VPS infra file") for path in paths]
    if resolved[0] == resolved[1]:
        raise ContractLifecycleError("the two VPS infra files must be distinct")
    bindings = [
        _infra_binding(path, shard_id=f"vps{index}")
        for index, path in enumerate(resolved, start=1)
    ]
    machine_ids = [str(row["machine_id"]) for row in bindings]
    endpoints = [(str(row["ssh_host"]), int(row["ssh_port"])) for row in bindings]
    if len(set(machine_ids)) != 2 or len(set(endpoints)) != 2:
        raise ContractLifecycleError("VPS infra files must identify two distinct machines")
    return bindings


def _infra_binding(path: Path, *, shard_id: str) -> dict[str, Any]:
    payload = load_mapping(path)
    matches: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for machine in list(payload.get("machines") or []):
        if not isinstance(machine, Mapping) or machine.get("enabled") is False:
            continue
        benchmarks = machine.get("benchmarks")
        if not isinstance(benchmarks, Mapping):
            continue
        for name, benchmark in benchmarks.items():
            if str(name).lower() == "agentdojo" and isinstance(benchmark, Mapping):
                matches.append((machine, benchmark))
    if len(matches) != 1:
        raise ContractLifecycleError(
            f"infra {path} must contain exactly one enabled AgentDojo target"
        )
    machine, benchmark = matches[0]
    ssh = machine.get("ssh")
    if machine.get("connection") != "ssh" or not isinstance(ssh, Mapping):
        raise ContractLifecycleError(f"infra {path} AgentDojo target must use SSH")
    machine_id = str(machine.get("machine_id") or "")
    host = str(ssh.get("host") or "")
    user = str(ssh.get("user") or "")
    fingerprint = str(
        ssh.get("ed25519_fingerprint")
        or ssh.get("host_ed25519_fingerprint")
        or ""
    )
    if not machine_id or not host or not user or not fingerprint.startswith("SHA256:"):
        raise ContractLifecycleError(f"infra {path} SSH identity is incomplete")
    concurrency = machine.get("concurrency")
    if (
        not isinstance(concurrency, int)
        or isinstance(concurrency, bool)
        or concurrency < 8
    ):
        raise ContractLifecycleError(f"infra {path} must support at least 8 workers")
    roots = {field: str(benchmark.get(field) or "") for field in _REMOTE_ROOT_FIELDS}
    if any(not value.startswith("/") for value in roots.values()):
        raise ContractLifecycleError(f"infra {path} sealed roots must be absolute")
    root_paths = [Path(value) for value in roots.values()]
    if len(set(root_paths)) != len(root_paths):
        raise ContractLifecycleError(f"infra {path} sealed roots must be distinct")
    for position, first in enumerate(root_paths):
        for second in root_paths[position + 1 :]:
            if _path_contains(first, second) or _path_contains(second, first):
                raise ContractLifecycleError(
                    f"infra {path} sealed roots must not overlap by ancestry"
                )
    return {
        "shard_id": shard_id,
        "path": display_path(path),
        "file_sha256": sha256_file(path),
        "semantic_sha256": sha256_object(payload),
        "machine_id": machine_id,
        "ssh_host": host,
        "ssh_port": int(ssh.get("port") or 22),
        "ssh_host_ed25519_fingerprint": fingerprint,
        "machine_concurrency": concurrency,
        "sealed_roots_sha256": sha256_object(roots),
    }


def _monitoring_policy() -> dict[str, Any]:
    return {
        "watchers_per_vps": 2,
        "watcher_roles": ["blind_runtime_health", "sealed_artifact_integrity"],
        "individual_problem_action": "append_only_record_and_continue",
        "consecutive_problem_case_threshold": CONSECUTIVE_PROBLEM_CASE_THRESHOLD,
        "consecutive_scope": "same_vps_and_same_agent_lane_distinct_cases",
        "threshold_action": "pause_new_admission_then_request_user_direction",
        "hard_blocker_action": "pause_new_admission_then_request_user_direction",
        "hard_blockers": [
            "authentication_or_authorization_failure",
            "budget_or_credit_exhaustion",
            "disk_below_locked_minimum",
            "ssh_host_key_identity_change",
            "host_boot_changed_with_unknown_worker_outcome",
            "sealed_tree_or_lock_binding_mismatch",
            "controller_dead_and_not_crash_resumable",
            "complete_run_can_no_longer_be_produced",
        ],
        "blind_only": True,
        "case_result_semantics_before_draft_freeze_forbidden": True,
        "incident_identity": "opaque_job_binding_sha256",
    }


def _sealed_evidence_policy() -> dict[str, Any]:
    return {
        "sealed_remote_output_required": True,
        "raw_evidence_stays_on_assigned_vps": True,
        "raw_evidence_synced_to_controller_during_run": False,
        "raw_evidence_retrieval_before_draft_freeze_forbidden": True,
        "controller_may_retrieve_blind_health_metadata_only": True,
        "retrieval_requires_later_explicit_post_freeze_gate": True,
        "completed_evidence_must_not_be_rerun": True,
        "completed_evidence_must_not_be_deleted": True,
        "three_native_episodes_per_job_required": True,
        "per_vps_raw_blind_runtime_failed_snapshot_roots_disjoint": True,
    }


def _validate_definition_invariants(definition: Mapping[str, Any]) -> None:
    selection = dict(definition.get("selection") or {})
    if (
        selection.get("full_case_count") != EXPECTED_FULL_CASE_COUNT
        or selection.get("paper_case_count") != EXPECTED_PAPER_CASE_COUNT
        or selection.get("remaining_case_count") != EXPECTED_REMAINING_CASE_COUNT
        or selection.get("remaining_suite_counts")
        != EXPECTED_REMAINING_SUITE_COUNTS
    ):
        raise ContractLifecycleError("remaining-849 manifest selection counts differ")
    sharding = dict(definition.get("sharding") or {})
    if (
        sharding.get("exact_suite_quotas") != EXPECTED_SHARD_QUOTAS
        or sharding.get("case_counts") != EXPECTED_SHARD_CASE_COUNTS
        or sharding.get("job_counts") != EXPECTED_SHARD_JOB_COUNTS
        or sharding.get("all_three_agents_for_a_case_must_share_one_vps") is not True
    ):
        raise ContractLifecycleError("remaining-849 manifest shard invariants differ")
    jobs = list(dict(definition.get("job_plan") or {}).get("entries") or [])
    if len(jobs) != EXPECTED_JOB_COUNT:
        raise ContractLifecycleError("remaining-849 manifest job denominator differs")
    by_case: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in jobs:
        if not isinstance(row, Mapping):
            raise ContractLifecycleError("remaining-849 job entry is not an object")
        by_case[str(row.get("case_unit_id") or "")].append(row)
        payload = row.get("job_payload")
        source_path = _regular_file(
            str(row.get("source_job_path") or ""), "bound source job"
        )
        if not isinstance(payload, Mapping):
            raise ContractLifecycleError("bound source job payload is missing")
        payload_dict = dict(payload)
        if (
            row.get("job_payload_sha256")
            != formal_job_binding_sha256(payload_dict)
            or row.get("job_binding_sha256")
            != formal_job_binding_sha256(payload_dict)
            or row.get("job_file_canonical_sha256")
            != formal_job_file_sha256(payload_dict)
            or row.get("job_file_sha256") != sha256_file(source_path)
            or row.get("job_file_sha256")
            != row.get("job_file_canonical_sha256")
            or load_mapping(source_path) != payload_dict
        ):
            raise ContractLifecycleError("bound source job payload/file hash differs")
        campaign_binding = {
            "campaign_id": CAMPAIGN_ID,
            "case_unit_id": row.get("case_unit_id"),
            "agent_id": row.get("agent_id"),
            "shard_id": row.get("shard_id"),
            "source_job_payload_sha256": row.get("job_payload_sha256"),
            "source_job_file_sha256": row.get("job_file_sha256"),
        }
        if row.get("campaign_job_binding_sha256") != sha256_object(
            campaign_binding
        ):
            raise ContractLifecycleError("campaign job binding SHA-256 differs")
    if len(by_case) != EXPECTED_REMAINING_CASE_COUNT:
        raise ContractLifecycleError("remaining-849 job cases differ")
    for case_id, rows in by_case.items():
        agents = [str(row["agent_id"]) for row in rows]
        shards = {str(row["shard_id"]) for row in rows}
        if sorted(agents) != sorted(EXPECTED_AGENTS) or len(shards) != 1:
            raise ContractLifecycleError(
                f"case agents are incomplete or cross VPS shards: {case_id}"
            )
    if dict(definition.get("monitoring_policy") or {}) != _monitoring_policy():
        raise ContractLifecycleError("remaining-849 monitoring policy differs")
    if dict(definition.get("sealed_evidence_policy") or {}) != _sealed_evidence_policy():
        raise ContractLifecycleError("remaining-849 sealed evidence policy differs")


def _validate_shard_assignment(assignment: Mapping[str, str]) -> None:
    if len(assignment) != EXPECTED_REMAINING_CASE_COUNT:
        raise ContractLifecycleError("shard assignment case denominator differs")
    for shard_id in ("vps1", "vps2"):
        selected = [case_id for case_id, value in assignment.items() if value == shard_id]
        if len(selected) != EXPECTED_SHARD_CASE_COUNTS[shard_id]:
            raise ContractLifecycleError(f"{shard_id} case count differs")
        counts = _ordered_suite_counts(selected)
        if counts != EXPECTED_SHARD_QUOTAS[shard_id]:
            raise ContractLifecycleError(f"{shard_id} suite quotas differ")
    if set(assignment.values()) != {"vps1", "vps2"}:
        raise ContractLifecycleError("shard assignment contains an unknown VPS")


def _build_lock_payload(
    manifest_path: Path,
    manifest: Mapping[str, Any],
    *,
    locked_at: str,
) -> dict[str, Any]:
    _validate_manifest_shape(manifest)
    definition = dict(manifest["definition"])
    lock_definition = {
        "manifest": {
            "path": display_path(manifest_path),
            "file_sha256": sha256_file(manifest_path),
            "semantic_sha256": sha256_object(dict(manifest)),
            "definition_sha256": str(manifest["definition_sha256"]),
        },
        "case_selection_sha256": sha256_object(definition["selection"]),
        "two_vps_sharding_sha256": sha256_object(definition["sharding"]),
        "job_plan_sha256": sha256_object(definition["job_plan"]),
        "runtime_sha256": sha256_object(definition["runtime"]),
        "source_bindings_sha256": sha256_object(definition["inputs"]),
        "monitoring_policy_sha256": sha256_object(
            definition["monitoring_policy"]
        ),
        "sealed_evidence_policy_sha256": sha256_object(
            definition["sealed_evidence_policy"]
        ),
        "case_count": EXPECTED_REMAINING_CASE_COUNT,
        "job_count": EXPECTED_JOB_COUNT,
        "consecutive_problem_case_threshold": (
            CONSECUTIVE_PROBLEM_CASE_THRESHOLD
        ),
        "sealed_remote_output_required": True,
        "raw_evidence_retrieval_before_draft_freeze_forbidden": True,
    }
    return {
        "schema_version": LOCK_SCHEMA_VERSION,
        "lock_id": LOCK_ID,
        "lock_status": "locked",
        "locked_at": locked_at,
        "definition": lock_definition,
        "definition_sha256": sha256_object(lock_definition),
    }


def _validate_manifest_shape(manifest: Mapping[str, Any]) -> None:
    if set(manifest) != {
        "schema_version",
        "campaign_id",
        "created_at",
        "definition",
        "definition_sha256",
    }:
        raise ContractLifecycleError("remaining-849 manifest field set differs")
    definition = manifest.get("definition")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("campaign_id") != CAMPAIGN_ID
        or not isinstance(definition, Mapping)
        or manifest.get("definition_sha256") != sha256_object(dict(definition or {}))
    ):
        raise ContractLifecycleError("remaining-849 manifest schema/hash differs")
    _validate_definition_invariants(dict(definition))


def _validate_lock_shape(lock: Mapping[str, Any]) -> None:
    if set(lock) != {
        "schema_version",
        "lock_id",
        "lock_status",
        "locked_at",
        "definition",
        "definition_sha256",
    }:
        raise ContractLifecycleError("remaining-849 execution lock field set differs")
    definition = lock.get("definition")
    if (
        lock.get("schema_version") != LOCK_SCHEMA_VERSION
        or lock.get("lock_id") != LOCK_ID
        or lock.get("lock_status") != "locked"
        or not isinstance(definition, Mapping)
        or lock.get("definition_sha256") != sha256_object(dict(definition or {}))
    ):
        raise ContractLifecycleError("remaining-849 execution lock schema/hash differs")
    expected_fields = {
        "manifest",
        "case_selection_sha256",
        "two_vps_sharding_sha256",
        "job_plan_sha256",
        "runtime_sha256",
        "source_bindings_sha256",
        "monitoring_policy_sha256",
        "sealed_evidence_policy_sha256",
        "case_count",
        "job_count",
        "consecutive_problem_case_threshold",
        "sealed_remote_output_required",
        "raw_evidence_retrieval_before_draft_freeze_forbidden",
    }
    if set(definition) != expected_fields:
        raise ContractLifecycleError("remaining-849 execution lock definition fields differ")
    if (
        definition.get("case_count") != EXPECTED_REMAINING_CASE_COUNT
        or definition.get("job_count") != EXPECTED_JOB_COUNT
        or definition.get("consecutive_problem_case_threshold")
        != CONSECUTIVE_PROBLEM_CASE_THRESHOLD
        or definition.get("sealed_remote_output_required") is not True
        or definition.get(
            "raw_evidence_retrieval_before_draft_freeze_forbidden"
        )
        is not True
    ):
        raise ContractLifecycleError("remaining-849 execution lock invariants differ")
    manifest_ref = definition.get("manifest")
    if not isinstance(manifest_ref, Mapping) or set(manifest_ref) != {
        "path",
        "file_sha256",
        "semantic_sha256",
        "definition_sha256",
    }:
        raise ContractLifecycleError("remaining-849 lock manifest binding differs")
    for field in ("file_sha256", "semantic_sha256", "definition_sha256"):
        if _SHA256_RE.fullmatch(str(manifest_ref.get(field) or "")) is None:
            raise ContractLifecycleError(f"remaining-849 lock {field} is invalid")


def _require_case_set_counts(
    case_ids: Sequence[str],
    *,
    expected_count: int,
    expected_suite_counts: Mapping[str, int],
    label: str,
) -> None:
    if len(case_ids) != expected_count:
        raise ContractLifecycleError(
            f"{label} must contain exactly {expected_count} cases; found {len(case_ids)}"
        )
    counts = _ordered_suite_counts(case_ids)
    if counts != dict(expected_suite_counts):
        raise ContractLifecycleError(
            f"{label} suite counts differ: {counts} != {dict(expected_suite_counts)}"
        )


def _ordered_suite_counts(case_ids: Sequence[str] | set[str]) -> dict[str, int]:
    counts = Counter(_case_parts(case_id)[0] for case_id in case_ids)
    return {suite: int(counts.get(suite, 0)) for suite in SUITE_ORDER}


def _case_parts(case_id: str) -> tuple[str, int, int]:
    match = _CASE_ID_RE.fullmatch(str(case_id))
    if match is None:
        raise ContractLifecycleError(f"invalid AgentDojo paired case ID: {case_id!r}")
    return match.group(1), int(match.group(2)), int(match.group(3))


def _case_sort_key(case_id: str) -> tuple[int, int, int, str]:
    suite, user_task, injection_task = _case_parts(case_id)
    return (
        SUITE_ORDER.index(suite),
        user_task,
        injection_task,
        str(case_id),
    )


def _file_binding(path: str | Path, *, label: str) -> dict[str, str]:
    resolved = _regular_file(path, label)
    return {"path": display_path(resolved), "sha256": sha256_file(resolved)}


def _tree_binding(path: Path) -> dict[str, str]:
    _reject_unsafe_tree(path)
    return {"path": display_path(path), "tree_sha256": sha256_path(path)}


def _regular_file(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    try:
        info = os.lstat(candidate)
    except OSError as exc:
        raise ContractLifecycleError(f"{label} is missing: {candidate}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ContractLifecycleError(f"{label} is not a regular non-symlink file")
    if info.st_nlink != 1:
        raise ContractLifecycleError(f"{label} must not be hard-linked")
    return candidate.resolve()


def _regular_directory(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    try:
        info = os.lstat(candidate)
    except OSError as exc:
        raise ContractLifecycleError(f"{label} is missing: {candidate}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ContractLifecycleError(f"{label} is not a regular non-symlink directory")
    return candidate.resolve()


def _reject_unsafe_tree(root: Path) -> None:
    for path in root.rglob("*"):
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode) or not (
            stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
        ):
            raise ContractLifecycleError(
                f"bound source tree contains a symlink or special entry: {path}"
            )


def _path_contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _write_new_or_identical(path: Path, payload: Mapping[str, Any]) -> bool:
    if path.exists() or path.is_symlink():
        existing = load_mapping(_regular_file(path, "published lock artifact"))
        if existing != dict(payload):
            raise ContractLifecycleError(
                f"refusing to replace a non-identical lock artifact: {path}"
            )
        return False
    write_json(path, payload)
    return True
