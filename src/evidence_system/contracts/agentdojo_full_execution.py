"""Pre-run execution freeze for the AgentDojo v1.2.2 full evidence branch.

This lock is deliberately independent from the checklist freeze.  It allows
raw trajectories to be collected while checklist review remains blind, but it
does not authorize scoring.  The later checklist/join locks remain separate
gates.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from evidence_system.contracts.agentdojo_execution_budget import (
    DEFAULT_BUDGET_PLAN,
    EXPECTED_CREDIT_FLOOR_USD,
    EXPECTED_MAXIMUM_COST_CAP_USD,
    EXPECTED_PREFLIGHT_RESERVE_USD,
    EXPECTED_PREFLIGHT_TWO_ROUND_COST_USD,
    EXPECTED_PROJECTED_COST_USD,
    EXPECTED_RECOMMENDED_INITIAL_CREDIT_USD,
    verify_budget_plan,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    AGENTDOJO_COMMIT,
    AGENTDOJO_PACKAGE_VERSION,
    AGENTDOJO_TREE,
    AGENTDOJO_WHEEL,
    AGENTDOJO_WHEEL_SHA256,
    ATTACK,
    BENCHMARK_VERSION,
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_CASE_PACKETS,
    DEFAULT_CATALOG,
    DEFAULT_MANIFEST,
    DEFAULT_SCORE_NAMESPACE_ROOTS,
    DEFAULT_SOURCE_BUNDLE,
    DEFENSE,
    EXPECTED_AGENTS,
    EXPECTED_CASE_COUNT,
    EXPECTED_RECORD_SLOT_COUNT,
    EXPECTED_SUITE_COUNTS,
    EXPERIMENT_ROOT,
    RESULT_NAMESPACE,
    SYSTEM_MESSAGE_SHA256,
    TOOL_DELIMITER,
    TOOL_OUTPUT_FORMAT,
)
from evidence_system.contracts.agentdojo_execution_namespace import (
    DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT,
    DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
    verify_final_runtime_deployment_receipt,
    verify_remote_output_precondition_receipt,
)
from evidence_system.contracts.common import ContractLifecycleError, load_mapping
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import validate_object


EXECUTION_LOCK_SCHEMA_VERSION = "agentdojo_full_execution_lock/v1"
EXECUTION_LOCK_ID = "agentdojo_full_v1.2.2_direct_execution"
EXECUTION_STAGING_NAMESPACE = f"{RESULT_NAMESPACE}_execution_staging"
DEFAULT_EXECUTION_LOCK = EXPERIMENT_ROOT / "lock/execution_lock.json"
DEFAULT_RUNTIME_INFRA_OVERLAY = EXPERIMENT_ROOT / "runtime/infra.vultr.yaml"
DEFAULT_RUNTIME_POLICY = EXPERIMENT_ROOT / "runtime/openrouter_runtime_policy.json"
DEFAULT_CREDENTIAL_PROBE_RECEIPT = (
    EXPERIMENT_ROOT / "runtime/preflight/credential_probe_receipt.json"
)
DEFAULT_DISPOSABLE_RAMP_RECEIPT = (
    EXPERIMENT_ROOT / "runtime/preflight/disposable_ramp_receipt.json"
)
DEFAULT_VPS_PROVISION_RECEIPT = EXPERIMENT_ROOT / "provenance/vps_provision_receipt.json"
DEFAULT_STAGING_RAW_RESULT_ROOT = (
    Path("results/namespaces") / EXECUTION_STAGING_NAMESPACE / "full/agentdojo"
)
DEFAULT_STAGING_NAMESPACE_ROOT = Path("results/namespaces") / EXECUTION_STAGING_NAMESPACE
DEFAULT_LOCAL_BLIND_METADATA_ROOT = (
    DEFAULT_STAGING_NAMESPACE_ROOT / "provenance/remote_blind_metadata"
)
REMOTE_INVENTORY_HELPER = Path(
    "src/evidence_system/adapters/agentdojo_remote_inventory.py"
)
DEFAULT_FORMAL_RAW_RESULT_ROOT = (
    Path("results/namespaces") / RESULT_NAMESPACE / "full/agentdojo"
)
DEFAULT_FORMAL_NAMESPACE_ROOT = Path("results/namespaces") / RESULT_NAMESPACE
DEFAULT_FORMAL_NAMESPACE_RESERVATION = (
    DEFAULT_FORMAL_NAMESPACE_ROOT / "NAMESPACE_LOCK.json"
)
DEFAULT_BLIND_FAILURE_LEDGER = (
    Path("results/namespaces")
    / EXECUTION_STAGING_NAMESPACE
    / "provenance/job_execution_failures.jsonl"
)
DEFAULT_FORMAL_KILL_GRACE_SECONDS = 30
DEFAULT_CREDIT_FLOOR_USD = 650.0
DEFAULT_RAMP_WORKERS = (4, 8, 16, 32)
DEFAULT_FORMAL_WALL_CLOCK_TIMEOUT_SECONDS = 7_200

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")
_PLACEHOLDER_RE = re.compile(
    r"(?:<[^>]+>|\b(?:todo|tbd|pending|replace[_ -]?me|example)\b)", re.IGNORECASE
)


@dataclass(frozen=True)
class ExecutionLockResult:
    lock_path: Path
    lock_sha256: str
    definition: dict[str, Any]
    created: bool


def _validated_execution_concurrency(
    *,
    ramp_workers: Sequence[int],
    maximum_workers: int | None,
    runtime_policy_ramp_stages: Sequence[int],
    runtime_policy_maximum_workers: int,
    machine_concurrency: int,
) -> tuple[list[int], int]:
    """Separate immutable attempted targets from the finalized active ceiling."""

    ramp = [int(value) for value in ramp_workers]
    if ramp != list(DEFAULT_RAMP_WORKERS):
        raise ContractLifecycleError(
            "execution-lock attempted concurrency ramp must equal [4, 8, 16, 32]"
        )
    if tuple(ramp) != tuple(int(value) for value in runtime_policy_ramp_stages):
        raise ContractLifecycleError(
            "execution-lock concurrency ramp differs from OpenRouter runtime policy"
        )
    active_maximum = (
        int(runtime_policy_maximum_workers)
        if maximum_workers is None
        else int(maximum_workers)
    )
    if active_maximum not in ramp:
        raise ContractLifecycleError(
            "maximum_workers must be one finalized active ceiling from the "
            "attempted concurrency ramp"
        )
    if active_maximum != int(runtime_policy_maximum_workers):
        raise ContractLifecycleError(
            "maximum_workers differs from OpenRouter global concurrency policy"
        )
    if ramp[-1] > int(machine_concurrency):
        raise ContractLifecycleError(
            "attempted concurrency-ramp maximum exceeds locked runtime-infra "
            "machine concurrency"
        )
    return ramp, active_maximum


def build_execution_definition(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    catalog_path: str | Path = DEFAULT_CATALOG,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    case_packets_root: str | Path = DEFAULT_CASE_PACKETS / "agentdojo",
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    runtime_infra_path: str | Path = DEFAULT_RUNTIME_INFRA_OVERLAY,
    runtime_policy_path: str | Path = DEFAULT_RUNTIME_POLICY,
    credential_probe_receipt_path: str | Path = DEFAULT_CREDENTIAL_PROBE_RECEIPT,
    disposable_ramp_receipt_path: str | Path = DEFAULT_DISPOSABLE_RAMP_RECEIPT,
    vps_provision_receipt_path: str | Path = DEFAULT_VPS_PROVISION_RECEIPT,
    remote_output_precondition_receipt_path: str
    | Path = DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
    final_runtime_deployment_receipt_path: str
    | Path = DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT,
    base_seed: int = 7,
    ramp_workers: Sequence[int] = DEFAULT_RAMP_WORKERS,
    maximum_workers: int | None = None,
    retry_transient_model_attempts: int = 2,
    continue_on_job_error: bool = True,
    budget_plan_path: str | Path = DEFAULT_BUDGET_PLAN,
    credit_preflight_receipt_path: str | Path | None = None,
    credit_floor_usd: float = DEFAULT_CREDIT_FLOOR_USD,
    require_outputs_empty: bool = True,
    locked_output_precondition: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Recompute every immutable input needed to authorize raw collection."""

    manifest_file = _regular_file(manifest_path, "manifest")
    catalog_file = _regular_file(catalog_path, "catalog")
    source_bundle_file = _regular_file(source_bundle_path, "source bundle")
    packets_root = _regular_dir(case_packets_root, "AgentDojo case packets")
    agents_file = _regular_file(agents_config_path, "agents config")
    infra_file = _regular_file(runtime_infra_path, "runtime infra overlay")
    runtime_policy_file = _regular_file(runtime_policy_path, "OpenRouter runtime policy")
    credential_receipt_file = _regular_file(
        credential_probe_receipt_path, "OpenRouter credential probe receipt"
    )
    ramp_receipt_file = _regular_file(
        disposable_ramp_receipt_path, "disposable concurrency-ramp receipt"
    )
    provision_receipt_file = _regular_file(
        vps_provision_receipt_path, "VPS provision receipt"
    )
    remote_precondition = verify_remote_output_precondition_receipt(
        remote_output_precondition_receipt_path,
        runtime_infra_path=infra_file,
        require_fresh=require_outputs_empty,
    )
    final_deployment = verify_final_runtime_deployment_receipt(
        final_runtime_deployment_receipt_path,
        runtime_infra_path=infra_file,
    )
    budget_plan_file = _regular_file(budget_plan_path, "execution budget plan")
    credit_preflight_file = _regular_file(
        credit_preflight_receipt_path or credential_receipt_file,
        "credit preflight receipt",
    )
    if credit_preflight_file != credential_receipt_file:
        raise ContractLifecycleError(
            "credit preflight receipt must be the same passing content-free credential receipt"
        )
    _require_independent_runtime_overlay(infra_file)

    manifest = load_mapping(manifest_file)
    catalog = load_mapping(catalog_file)
    source_bundle = load_mapping(source_bundle_file)
    agents = load_mapping(agents_file)
    infra = load_mapping(infra_file)
    runtime_policy_payload = load_mapping(runtime_policy_file)
    validate_object("infra_config", infra, raise_on_error=True)
    from evidence_system.adapters.agentdojo_runtime_control import (
        execution_runtime_snapshot,
        load_credential_probe_receipt,
        load_disposable_ramp_receipt,
        load_runtime_policy,
        rate_only_override_snapshot,
    )

    runtime_policy = load_runtime_policy(runtime_policy_payload)
    if runtime_policy.lifecycle_status != "finalized":
        raise ContractLifecycleError(
            "execution lock cannot publish from a provisional runtime policy"
        )
    override_definition = dict(runtime_policy.raw["operational_override"])
    if override_definition.get("base_agents_config_file_sha256") != sha256_file(
        agents_file
    ):
        raise ContractLifecycleError(
            "runtime operational override is not bound to the frozen agents config"
        )
    infra_file_sha256 = sha256_file(infra_file)
    credential_receipt = load_credential_probe_receipt(
        credential_receipt_file,
        expected_policy_sha256=runtime_policy.semantic_sha256,
        expected_runtime_infra_file_sha256=infra_file_sha256,
    )

    case_refs = _validated_case_refs(manifest, catalog, source_bundle)
    case_ids = [row["case_unit_id"] for row in case_refs]
    job_entries = build_locked_job_entries(case_refs, base_seed=base_seed)
    if len(job_entries) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError(
            f"execution job plan must contain {EXPECTED_RECORD_SLOT_COUNT} entries"
        )

    if manifest.get("result_namespace") != RESULT_NAMESPACE:
        raise ContractLifecycleError("manifest result namespace is not the reserved AgentDojo full namespace")
    if manifest.get("source_bundle_hash") != sha256_file(source_bundle_file):
        raise ContractLifecycleError("manifest source_bundle_hash is stale")
    if manifest.get("agents_config_hash") != sha256_file(agents_file):
        raise ContractLifecycleError("manifest agents_config_hash is stale")

    infra_snapshot = _strict_agentdojo_infra_snapshot(infra)
    ramp, active_maximum_workers = _validated_execution_concurrency(
        ramp_workers=ramp_workers,
        maximum_workers=maximum_workers,
        runtime_policy_ramp_stages=runtime_policy.ramp_stages,
        runtime_policy_maximum_workers=runtime_policy.max_concurrent_requests,
        machine_concurrency=infra_snapshot["machine_concurrency"],
    )
    if retry_transient_model_attempts < 0:
        raise ContractLifecycleError("retry_transient_model_attempts must be non-negative")
    if base_seed < 0:
        raise ContractLifecycleError("base_seed must be non-negative")
    if credit_floor_usd <= 0:
        raise ContractLifecycleError("credit_floor_usd must be positive")
    if (
        float(credit_floor_usd)
        != runtime_policy.budget.minimum_formal_start_remaining_usd
    ):
        raise ContractLifecycleError(
            "credit_floor_usd differs from OpenRouter runtime budget policy"
        )
    ramp_receipt = load_disposable_ramp_receipt(
        ramp_receipt_file,
        expected_policy_sha256=runtime_policy.semantic_sha256,
        expected_stages=tuple(ramp),
        expected_runtime_infra_file_sha256=infra_file_sha256,
    )
    pre_ramp_credential_ref = dict(
        ramp_receipt.get("pre_ramp_credential_receipt") or {}
    )
    pre_ramp_credential_receipt = load_credential_probe_receipt(
        _regular_file(
            str(pre_ramp_credential_ref.get("path") or ""),
            "pre-ramp credential probe receipt",
        ),
        expected_policy_sha256=runtime_policy.semantic_sha256,
        expected_runtime_infra_file_sha256=infra_file_sha256,
        expected_probe_phase="pre_ramp",
    )
    _validate_final_credential_after_ramp(credential_receipt, ramp_receipt)
    budget_plan = verify_budget_plan(budget_plan_file)
    _validate_budget_bindings(
        budget_plan,
        runtime_policy=runtime_policy,
        pre_ramp_credit_receipt=pre_ramp_credential_receipt,
        credit_receipt=credential_receipt,
        credit_floor_usd=float(credit_floor_usd),
    )
    provision_receipt = load_mapping(provision_receipt_file)
    _validate_vps_provision_receipt(
        provision_receipt,
        infra=infra,
        infra_snapshot=infra_snapshot,
        credential_receipt=credential_receipt,
    )

    canaries = _canary_case_ids(case_ids)
    concurrency_policy = {
        "canary_case_ids": canaries,
        "ramp_workers": ramp,
        "maximum_workers": active_maximum_workers,
        "promotion_policy": _concurrency_promotion_policy(job_entries, canaries),
        "health_thresholds": {
            "max_error_rate": 0.05,
            "max_http_429_rate": 0.02,
            "max_http_503_rate": 0.02,
            "max_cpu_percent": 80.0,
            "max_memory_percent": 85.0,
        },
    }
    failure_policy = {
        "continue_on_job_error": bool(continue_on_job_error),
        "fail_fast": not bool(continue_on_job_error),
        "retry_transient_model_attempts": int(retry_transient_model_attempts),
        "rerun_completed": False,
        "never_rerun_completed": True,
        "rerun_failed_after_all_agents": True,
        "failure_recovery_rounds": 1,
        "worker_kill_grace_seconds": DEFAULT_FORMAL_KILL_GRACE_SECONDS,
        "blind_failure_ledger_path": _repo_relative(
            resolve_repo_path(DEFAULT_BLIND_FAILURE_LEDGER)
        ),
        "blind_health_fields_only": True,
    }
    models = _model_snapshot(agents)
    rate_only_override = rate_only_override_snapshot(
        dict(agents.get("experimental_agents") or {}), runtime_policy
    )
    if not runtime_policy.retry.respect_retry_after or runtime_policy.retry.multiplier <= 1:
        raise ContractLifecycleError(
            "runtime policy must honor Retry-After and use exponential backoff"
        )
    rate_limit_policy = {
        "source": "agents_config_and_runtime_policy",
        "agent_limits": {
            agent_id: dict(models[agent_id]["rate_limit"])
            for agent_id in EXPECTED_AGENTS
        },
        "runtime_limits": {
            "requests_per_minute": runtime_policy.requests_per_minute,
            "tokens_per_minute": runtime_policy.tokens_per_minute,
            "concurrent_requests": runtime_policy.max_concurrent_requests,
        },
        "override_mode": "runtime_policy_overrides_agents_rate_limit_fields_only",
        "overridden_agents_config_fields": [
            "experimental_agents.*.rate_limit.requests_per_minute",
            "experimental_agents.*.rate_limit.tokens_per_minute",
            "experimental_agents.*.rate_limit.concurrent_requests",
        ],
        "preserved_agents_config_fields": [
            "provider",
            "model",
            "model_version",
            "api_key_env",
            "temperature",
            "max_tokens",
            "timeout_seconds",
            "retry",
            "save_response_metadata",
            "cost_tracking",
        ],
        "override_rationale": (
            "The cross-process runtime controller applies only the measured RPM, "
            "TPM, and global concurrency scheduling overlay; provider, model, "
            "version, sampling, request, system-message, and tool semantics remain "
            "authoritative in configs/agents.yaml."
        ),
        "runtime_policy_semantic_sha256": runtime_policy.semantic_sha256,
        "operational_definition_sha256": runtime_policy.operational_definition_sha256,
        "runtime_policy_lifecycle_status": runtime_policy.lifecycle_status,
        "measurement_receipt": {
            "path": str(runtime_policy.measurement_receipt_path),
            "sha256": str(runtime_policy.measurement_receipt_sha256),
        },
        "finalized_after_disposable_ramp": True,
        "override": rate_only_override,
        "global_limiter_required": True,
        "honor_retry_after": True,
        "exponential_backoff": True,
    }
    execution_policy_sha256 = sha256_object(
        {
            "concurrency_policy": concurrency_policy,
            "failure_policy": failure_policy,
            "rate_limit_policy": rate_limit_policy,
        }
    )

    if require_outputs_empty:
        output_precondition = _output_precondition()
    else:
        if not isinstance(locked_output_precondition, Mapping):
            raise ContractLifecycleError(
                "verification requires the output precondition captured before execution"
            )
        output_precondition = dict(locked_output_precondition)

    runtime_snapshot = execution_runtime_snapshot()
    known_hosts_file = _regular_file(
        infra_snapshot["ssh_known_hosts_file"], "pinned SSH known_hosts file"
    )
    inventory_helper = _regular_file(
        REMOTE_INVENTORY_HELPER, "remote evidence inventory helper"
    )
    controller_public_key = _regular_file(
        f"{infra_snapshot['ssh_key_path']}.pub", "controller SSH public key"
    )
    controller_public_fingerprint = _ed25519_public_key_fingerprint(
        controller_public_key
    )
    if controller_public_fingerprint != infra_snapshot[
        "ssh_public_key_fingerprint"
    ]:
        raise ContractLifecycleError(
            "controller SSH public-key fingerprint differs from runtime infra"
        )

    return {
        "formal_result_namespace": RESULT_NAMESPACE,
        "staging_result_namespace": EXECUTION_STAGING_NAMESPACE,
        "manifest": _path_lock(manifest_file),
        "catalog": _path_lock(catalog_file),
        "source_bundle": _path_lock(source_bundle_file),
        "case_packets": {
            "path": _repo_relative(packets_root),
            "tree_sha256": sha256_path(packets_root),
        },
        "agents_config": _path_lock(agents_file),
        "runtime_infra_overlay": _path_lock(infra_file),
        "remote_output_precondition_receipt": _path_lock(
            remote_precondition.path
        ),
        "final_runtime_deployment_receipt": _path_lock(final_deployment.path),
        "sealed_remote_evidence": {
            "enabled": True,
            "ssh_host": infra_snapshot["ssh_host"],
            "ssh_port": infra_snapshot["ssh_port"],
            "ssh_host_ed25519_fingerprint": infra_snapshot[
                "ssh_host_ed25519_fingerprint"
            ],
            "ssh_known_hosts_file": _path_lock(known_hosts_file),
            "controller_ssh_public_key": {
                "path": _repo_relative(controller_public_key),
                "fingerprint": controller_public_fingerprint,
            },
            "execution_user": infra_snapshot["execution_user"],
            "monitor_user": infra_snapshot["monitor_user"],
            "monitor_access_mode": "controller_ssh_sudo_u_locked_health_cli",
            "blind_group": infra_snapshot["blind_group"],
            "secret_env_path": infra_snapshot["secret_env_path"],
            "secret_parent_mode": infra_snapshot["secret_parent_mode"],
            "secret_file_mode": infra_snapshot["secret_file_mode"],
            "runtime_state_root": infra_snapshot["runtime_state_root"],
            "runtime_state_parent_mode": infra_snapshot[
                "runtime_state_parent_mode"
            ],
            "runtime_state_mode": infra_snapshot["runtime_state_mode"],
            "runtime_state_initialization": (
                "atomic_create_once_then_reuse_exact_identity"
            ),
            "remote_raw_root": infra_snapshot["remote_raw_root"],
            "remote_raw_parent_mode": infra_snapshot["remote_raw_parent_mode"],
            "remote_raw_mode": infra_snapshot["remote_raw_mode"],
            "failed_attempt_archive_root": infra_snapshot[
                "failed_attempt_archive_root"
            ],
            "failed_attempt_archive_parent_mode": infra_snapshot[
                "failed_attempt_archive_parent_mode"
            ],
            "failed_attempt_archive_mode": infra_snapshot[
                "failed_attempt_archive_mode"
            ],
            "blind_aggregate_root": infra_snapshot["blind_aggregate_root"],
            "blind_aggregate_dir_mode": infra_snapshot[
                "blind_aggregate_dir_mode"
            ],
            "blind_aggregate_file_mode": infra_snapshot[
                "blind_aggregate_file_mode"
            ],
            "retrieval_snapshot_root": infra_snapshot[
                "retrieval_snapshot_root"
            ],
            "retrieval_snapshot_parent_mode": infra_snapshot[
                "retrieval_snapshot_parent_mode"
            ],
            "retrieval_snapshot_mode": infra_snapshot[
                "retrieval_snapshot_mode"
            ],
            "retrieval_lifecycle_lock": (
                f"{infra_snapshot['blind_aggregate_root'].rstrip('/')}"
                "/.canonical-lifecycle.lock"
            ),
            "remote_inventory_helper": {
                "path": _repo_relative(inventory_helper),
                "remote_path": (
                    f"{infra_snapshot['remote_workdir'].rstrip('/')}"
                    "/src/evidence_system/adapters/agentdojo_remote_inventory.py"
                ),
                "sha256": sha256_file(inventory_helper),
            },
            "raw_evidence_controller_sync_before_checklist_freeze": False,
            "retrieval_requires_checklist_freeze_v2": True,
            "retrieval_publication": (
                "same_filesystem_temp_verify_fsync_atomic_rename_destination_absent"
            ),
            "local_canonical_staging_root": _repo_relative(
                resolve_repo_path(DEFAULT_STAGING_RAW_RESULT_ROOT)
            ),
            "local_blind_metadata_root": _repo_relative(
                resolve_repo_path(DEFAULT_LOCAL_BLIND_METADATA_ROOT)
            ),
            "post_lock_namespace_init_required": True,
        },
        "runtime_policy": _path_lock(runtime_policy_file),
        "credential_probe_receipt": _path_lock(credential_receipt_file),
        "disposable_ramp_receipt": _path_lock(ramp_receipt_file),
        "vps_provision_receipt": _path_lock(provision_receipt_file),
        "benchmark": {
            "package_version": AGENTDOJO_PACKAGE_VERSION,
            "git_commit": AGENTDOJO_COMMIT,
            "git_tree": AGENTDOJO_TREE,
            "benchmark_version": BENCHMARK_VERSION,
            "attack": ATTACK,
            "defense": DEFENSE,
            "tool_delimiter": TOOL_DELIMITER,
            "tool_output_format": TOOL_OUTPUT_FORMAT,
            "system_message_sha256": SYSTEM_MESSAGE_SHA256,
        },
        "models": models,
        "case_set": {
            "case_count": len(case_ids),
            "case_id_order_sha256": sha256_object(case_ids),
            "case_id_set_sha256": sha256_object(sorted(case_ids)),
            "suite_case_counts": dict(sorted(Counter(_suite(case_id) for case_id in case_ids).items())),
        },
        "job_plan": {
            "base_seed": int(base_seed),
            "seed_policy": "base_seed_plus_case_index_minus_one_same_across_agents",
            "job_count": len(job_entries),
            "mapping_sha256": sha256_object(job_entries),
            "entries": job_entries,
        },
        "concurrency_policy": concurrency_policy,
        "failure_policy": failure_policy,
        "rate_limit_policy": rate_limit_policy,
        "execution_policy_sha256": execution_policy_sha256,
        "budget_control": {
            "budget_plan": _path_lock(budget_plan_file),
            "projected_cost_usd": float(EXPECTED_PROJECTED_COST_USD),
            "preflight_two_round_cost_usd": float(
                EXPECTED_PREFLIGHT_TWO_ROUND_COST_USD
            ),
            "preflight_reserve_usd": float(EXPECTED_PREFLIGHT_RESERVE_USD),
            "recommended_initial_credit_usd": float(
                EXPECTED_RECOMMENDED_INITIAL_CREDIT_USD
            ),
            "credit_floor_usd": float(credit_floor_usd),
            "maximum_run_cost_usd": float(EXPECTED_MAXIMUM_COST_CAP_USD),
            "credit_preflight_receipt": _path_lock(credit_preflight_file),
            "secret_material_locked": False,
            "credit_snapshot_bound": True,
        },
        "execution_runtime_snapshot": runtime_snapshot,
        "output_precondition": output_precondition,
    }


def publish_execution_lock(
    *,
    output_path: str | Path = DEFAULT_EXECUTION_LOCK,
    locked_at: str | None = None,
    **definition_kwargs: Any,
) -> ExecutionLockResult:
    """Publish once, atomically; a differing existing lock is never overwritten."""

    output_file = resolve_repo_path(output_path)
    definition = build_execution_definition(**definition_kwargs)
    timestamp = locked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _require_aware_timestamp(timestamp)
    payload = {
        "schema_version": EXECUTION_LOCK_SCHEMA_VERSION,
        "lock_id": EXECUTION_LOCK_ID,
        "lock_status": "locked",
        "locked_at": timestamp,
        "result_namespace": EXECUTION_STAGING_NAMESPACE,
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }
    validate_execution_lock_payload(payload)

    if output_file.exists():
        existing = load_mapping(output_file)
        validate_execution_lock_payload(existing)
        if existing.get("definition") != definition:
            raise ContractLifecycleError(
                "execution lock already exists and differs; it is immutable once published"
            )
        return ExecutionLockResult(
            lock_path=output_file,
            lock_sha256=sha256_file(output_file),
            definition=dict(existing["definition"]),
            created=False,
        )

    _atomic_write_json(output_file, payload)
    return ExecutionLockResult(
        lock_path=output_file,
        lock_sha256=sha256_file(output_file),
        definition=definition,
        created=True,
    )


def verify_execution_lock(
    *,
    lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    manifest_path: str | Path | None = None,
    source_bundle_path: str | Path | None = None,
    agents_config_path: str | Path | None = None,
    runtime_infra_path: str | Path | None = None,
) -> ExecutionLockResult:
    """Verify the execution lock for formal runner admission.

    This is intentionally the strict lifecycle gate: the formal namespace may
    still contain only its immutable reservation file.  Post-promotion and
    pre-score consumers must use :func:`verify_execution_lock_envelope` and
    independently verify the promotion/join receipts that authorize their
    lifecycle phase.
    """

    return _verify_execution_lock(
        lock_path=lock_path,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        agents_config_path=agents_config_path,
        runtime_infra_path=runtime_infra_path,
        enforce_formal_namespace_reservation=True,
    )


def verify_execution_lock_envelope(
    *,
    lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    manifest_path: str | Path | None = None,
    source_bundle_path: str | Path | None = None,
    agents_config_path: str | Path | None = None,
    runtime_infra_path: str | Path | None = None,
) -> ExecutionLockResult:
    """Verify immutable execution inputs without asserting lifecycle emptiness.

    This API does *not* authorize execution.  It exists for evidence retrieval,
    promotion, and join verification after the formal namespace has legitimately
    grown.  Those callers must separately verify their phase-specific immutable
    receipt before accepting any evidence.
    """

    return _verify_execution_lock(
        lock_path=lock_path,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        agents_config_path=agents_config_path,
        runtime_infra_path=runtime_infra_path,
        enforce_formal_namespace_reservation=False,
    )


def _verify_execution_lock(
    *,
    lock_path: str | Path,
    manifest_path: str | Path | None,
    source_bundle_path: str | Path | None,
    agents_config_path: str | Path | None,
    runtime_infra_path: str | Path | None,
    enforce_formal_namespace_reservation: bool,
) -> ExecutionLockResult:
    """Shared immutable-input verifier; never exported as an execution gate."""

    lock_file = _regular_file(lock_path, "execution lock")
    payload = load_mapping(lock_file)
    validate_execution_lock_payload(payload)
    locked = dict(payload["definition"])
    reservation_lock = dict(
        dict(locked.get("output_precondition") or {}).get(
            "formal_namespace_reservation"
        )
        or {}
    )
    reservation_path = _regular_file(
        str(reservation_lock.get("path") or ""), "formal namespace reservation"
    )
    if sha256_file(reservation_path) != reservation_lock.get("sha256"):
        raise ContractLifecycleError("formal namespace reservation hash drifted")
    if enforce_formal_namespace_reservation:
        _validated_formal_namespace_reservation(
            reservation_path.parent, reservation_path
        )

    def locked_path(name: str) -> str:
        value = locked.get(name)
        if not isinstance(value, Mapping) or not value.get("path"):
            raise ContractLifecycleError(f"execution lock {name}.path is missing")
        return str(value["path"])

    supplied = {
        "manifest": manifest_path,
        "source_bundle": source_bundle_path,
        "agents_config": agents_config_path,
        "runtime_infra_overlay": runtime_infra_path,
    }
    for name, value in supplied.items():
        if value is None:
            continue
        if resolve_repo_path(value).resolve() != resolve_repo_path(locked_path(name)).resolve():
            raise ContractLifecycleError(f"{name} path differs from execution lock")

    budget = dict(locked["budget_control"])
    job_plan = dict(locked["job_plan"])
    failure = dict(locked["failure_policy"])
    concurrency = dict(locked["concurrency_policy"])
    recomputed = build_execution_definition(
        manifest_path=locked_path("manifest"),
        catalog_path=locked_path("catalog"),
        source_bundle_path=locked_path("source_bundle"),
        case_packets_root=str(dict(locked["case_packets"])["path"]),
        agents_config_path=locked_path("agents_config"),
        runtime_infra_path=locked_path("runtime_infra_overlay"),
        runtime_policy_path=locked_path("runtime_policy"),
        credential_probe_receipt_path=locked_path("credential_probe_receipt"),
        disposable_ramp_receipt_path=locked_path("disposable_ramp_receipt"),
        vps_provision_receipt_path=locked_path("vps_provision_receipt"),
        remote_output_precondition_receipt_path=locked_path(
            "remote_output_precondition_receipt"
        ),
        final_runtime_deployment_receipt_path=locked_path(
            "final_runtime_deployment_receipt"
        ),
        base_seed=int(job_plan["base_seed"]),
        ramp_workers=list(concurrency["ramp_workers"]),
        maximum_workers=int(concurrency["maximum_workers"]),
        retry_transient_model_attempts=int(failure["retry_transient_model_attempts"]),
        continue_on_job_error=bool(failure["continue_on_job_error"]),
        budget_plan_path=str(dict(budget["budget_plan"])["path"]),
        credit_preflight_receipt_path=str(
            dict(budget["credit_preflight_receipt"])["path"]
        ),
        credit_floor_usd=float(budget["credit_floor_usd"]),
        require_outputs_empty=False,
        locked_output_precondition=dict(locked["output_precondition"]),
    )
    if recomputed != locked:
        raise ContractLifecycleError(
            "execution lock currentness verification failed: an immutable input drifted"
        )
    return ExecutionLockResult(
        lock_path=lock_file,
        lock_sha256=sha256_file(lock_file),
        definition=locked,
        created=False,
    )


def validate_execution_lock_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_full_execution_lock", dict(payload), raise_on_error=False
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"execution lock schema validation failed: {report.to_dict()}"
        )
    definition = payload.get("definition")
    if not isinstance(definition, Mapping):
        raise ContractLifecycleError("execution lock definition is missing")
    if payload.get("definition_sha256") != sha256_object(definition):
        raise ContractLifecycleError("execution lock definition_sha256 mismatch")
    _require_aware_timestamp(str(payload.get("locked_at") or ""))

    job_plan = dict(definition.get("job_plan") or {})
    entries = list(job_plan.get("entries") or [])
    if job_plan.get("mapping_sha256") != sha256_object(entries):
        raise ContractLifecycleError("execution lock job-plan mapping hash mismatch")
    identities = [
        (entry.get("case_unit_id"), entry.get("agent_id"))
        for entry in entries
        if isinstance(entry, Mapping)
    ]
    slots = [entry.get("record_slot_id") for entry in entries if isinstance(entry, Mapping)]
    jobs = [entry.get("job_id") for entry in entries if isinstance(entry, Mapping)]
    if len(set(identities)) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("execution lock job plan has duplicate case/agent identities")
    if len(set(slots)) != EXPECTED_RECORD_SLOT_COUNT or len(set(jobs)) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("execution lock job plan has duplicate job or record-slot IDs")

    concurrency = dict(definition.get("concurrency_policy") or {})
    failure = dict(definition.get("failure_policy") or {})
    rate_limit = dict(definition.get("rate_limit_policy") or {})
    expected_policy_sha = sha256_object(
        {
            "concurrency_policy": concurrency,
            "failure_policy": failure,
            "rate_limit_policy": rate_limit,
        }
    )
    if definition.get("execution_policy_sha256") != expected_policy_sha:
        raise ContractLifecycleError("execution policy hash mismatch")
    if bool(failure.get("continue_on_job_error")) == bool(failure.get("fail_fast")):
        raise ContractLifecycleError("exactly one of continue_on_job_error/fail_fast must be true")
    ramp = list(concurrency.get("ramp_workers") or [])
    if ramp != list(DEFAULT_RAMP_WORKERS):
        raise ContractLifecycleError(
            "locked attempted concurrency ramp must equal [4, 8, 16, 32]"
        )
    active_maximum_workers = concurrency.get("maximum_workers")
    if (
        not isinstance(active_maximum_workers, int)
        or isinstance(active_maximum_workers, bool)
        or active_maximum_workers not in ramp
    ):
        raise ContractLifecycleError(
            "locked maximum_workers is not an active ceiling from the attempted ramp"
        )
    for suite, case_id in dict(concurrency.get("canary_case_ids") or {}).items():
        if _suite(str(case_id)) != suite:
            raise ContractLifecycleError(f"canary case does not belong to suite {suite}")
    _validate_concurrency_promotion_policy(entries, concurrency)
    if failure.get("never_rerun_completed") is not True or failure.get("rerun_completed") is not False:
        raise ContractLifecycleError("execution policy must never rerun completed slots")
    if failure.get("rerun_failed_after_all_agents") is not True:
        raise ContractLifecycleError("failed slots must be retried only after all agent batches")
    if failure.get("failure_recovery_rounds") != 1:
        raise ContractLifecycleError("execution policy must lock exactly one failure-recovery round")
    if failure.get("worker_kill_grace_seconds") != DEFAULT_FORMAL_KILL_GRACE_SECONDS:
        raise ContractLifecycleError("formal worker kill grace must be exactly 30 seconds")


def _validate_concurrency_promotion_policy(
    entries: Sequence[Mapping[str, Any]], concurrency: Mapping[str, Any]
) -> None:
    promotion = dict(concurrency.get("promotion_policy") or {})
    if promotion.get("agent_batch_order") != list(EXPECTED_AGENTS):
        raise ContractLifecycleError("execution agent batches must be ordered Agent A, B, C")
    if promotion.get("complete_each_agent_before_next") is not True:
        raise ContractLifecycleError("each agent batch must complete before the next")
    if promotion.get("promotion_inputs") != "blind_runtime_health_only":
        raise ContractLifecycleError("concurrency promotion may use only blind runtime health")
    if (
        promotion.get("on_stage_failure")
        != "return_to_previous_safe_concurrency_and_continue"
        or promotion.get("interrupt_batch_on_stage_failure") is not False
    ):
        raise ContractLifecycleError("concurrency-stage failure policy is not fail-continuing")

    expected_agent_order = [
        agent_id for agent_id in EXPECTED_AGENTS for _ in range(EXPECTED_CASE_COUNT)
    ]
    if [entry.get("agent_id") for entry in entries] != expected_agent_order:
        raise ContractLifecycleError("job-plan order must be sequential Agent A, then B, then C")
    slot_index = {str(entry.get("record_slot_id")): dict(entry) for entry in entries}
    canary_cases = set(dict(concurrency.get("canary_case_ids") or {}).values())
    expected_canary_slots = {
        str(entry["record_slot_id"])
        for entry in entries
        if entry.get("case_unit_id") in canary_cases
    }
    canary = dict(promotion.get("canary") or {})
    canary_slots = list(canary.get("record_slot_ids") or [])
    if (
        canary.get("workers") != 4
        or canary.get("suite_count") != 4
        or canary.get("agent_count") != 3
        or canary.get("record_slot_count") != 12
        or len(canary_slots) != 12
        or len(set(canary_slots)) != 12
        or set(canary_slots) != expected_canary_slots
        or canary.get("record_slot_ids_sha256") != sha256_object(canary_slots)
    ):
        raise ContractLifecycleError("four-suite three-agent canary promotion sample is invalid")

    ramp_by_agent = promotion.get("agent_ramp_stages")
    if not isinstance(ramp_by_agent, Mapping) or set(ramp_by_agent) != set(
        EXPECTED_AGENTS
    ):
        raise ContractLifecycleError("each agent must have its own locked ramp stages")
    used = set(canary_slots)
    for agent_id in EXPECTED_AGENTS:
        stages = list(ramp_by_agent.get(agent_id) or [])
        if len(stages) != 3:
            raise ContractLifecycleError(
                f"{agent_id} ramp must contain exactly 8/16/32 stages"
            )
        for stage, (workers, count) in zip(
            stages, ((8, 32), (16, 64), (32, 128)), strict=True
        ):
            if not isinstance(stage, Mapping):
                raise ContractLifecycleError(f"{agent_id} ramp stage is not an object")
            slots = list(stage.get("record_slot_ids") or [])
            if (
                stage.get("workers") != workers
                or stage.get("agent_id") != agent_id
                or stage.get("new_distinct_slot_count") != count
                or len(slots) != count
                or len(set(slots)) != count
                or stage.get("record_slot_ids_sha256") != sha256_object(slots)
            ):
                raise ContractLifecycleError(
                    f"{agent_id} workers={workers} ramp sample is invalid"
                )
            if used.intersection(slots):
                raise ContractLifecycleError(
                    "concurrency promotion samples must be globally disjoint"
                )
            for slot in slots:
                entry = slot_index.get(str(slot))
                if entry is None or entry.get("agent_id") != agent_id:
                    raise ContractLifecycleError(
                        f"ramp sample contains a non-{agent_id} locked slot"
                    )
            used.update(slots)
    expected_stage_order = [
        "canary",
        "ramp-a-8",
        "ramp-a-16",
        "ramp-a-32",
        "remaining-a",
        "ramp-b-8",
        "ramp-b-16",
        "ramp-b-32",
        "remaining-b",
        "ramp-c-8",
        "ramp-c-16",
        "ramp-c-32",
        "remaining-c",
        "recovery-a",
        "recovery-b",
        "recovery-c",
    ]
    if promotion.get("formal_stage_order") != expected_stage_order:
        raise ContractLifecycleError("formal per-agent stage order is invalid")


def build_locked_job_entries(
    case_refs: Sequence[Mapping[str, str]],
    *,
    base_seed: int,
    formal_wall_clock_timeout_seconds: int = DEFAULT_FORMAL_WALL_CLOCK_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    if formal_wall_clock_timeout_seconds <= 0:
        raise ContractLifecycleError("formal wall-clock timeout must be positive")
    entries: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENTS:
        for case_index, row in enumerate(case_refs, start=1):
            case_unit_id = str(row["case_unit_id"])
            task_id = str(row["task_id"])
            safe_case = _safe_id(case_unit_id)
            safe_agent = _safe_id(agent_id.lower().replace(" ", "_"))
            entries.append(
                {
                    "job_id": f"full-agentdojo-{safe_case}-{safe_agent}",
                    "case_unit_id": case_unit_id,
                    "task_id": task_id,
                    "record_slot_id": f"slot-agentdojo-{safe_case}-{safe_agent}",
                    "run_id": f"run-agentdojo-{safe_case}-{safe_agent}",
                    "attempt_id": f"attempt-agentdojo-{safe_case}-{safe_agent}",
                    "seed": int(base_seed) + case_index - 1,
                    "agent_id": agent_id,
                    "force_rerun": False,
                    "rerun_completed": False,
                    "formal_wall_clock_timeout_seconds": int(
                        formal_wall_clock_timeout_seconds
                    ),
                }
            )
    return entries


def expected_job_index(lock: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    definition = dict(lock.get("definition") or {})
    entries = list(dict(definition.get("job_plan") or {}).get("entries") or [])
    return {
        (str(entry["case_unit_id"]), str(entry["agent_id"])): dict(entry)
        for entry in entries
        if isinstance(entry, Mapping)
    }


def verify_job_binding(
    job: Mapping[str, Any],
    lock: Mapping[str, Any],
    *,
    lock_path: str | Path | None = None,
    lock_sha256: str | None = None,
) -> None:
    key = (str(job.get("case_unit_id") or ""), str(job.get("agent_id") or ""))
    expected = expected_job_index(lock).get(key)
    if expected is None:
        raise ContractLifecycleError(f"job is outside the locked case/agent product: {key}")
    for field, expected_value in expected.items():
        if job.get(field) != expected_value:
            raise ContractLifecycleError(
                f"job {field} differs from execution lock: expected={expected_value!r}, actual={job.get(field)!r}"
            )
    if job.get("domain") != "agentdojo" or job.get("phase") != "full":
        raise ContractLifecycleError("execution lock only authorizes full AgentDojo raw jobs")
    if job.get("experiment_type") != "appendix":
        raise ContractLifecycleError("execution lock only authorizes appendix jobs")
    if job.get("result_namespace") != EXECUTION_STAGING_NAMESPACE:
        raise ContractLifecycleError("execution lock only authorizes the sealed staging namespace")
    definition = dict(lock.get("definition") or {})
    expected_execution_policy = str(definition.get("execution_policy_sha256") or "")
    if job.get("execution_policy_sha256") != expected_execution_policy:
        raise ContractLifecycleError("job execution_policy_sha256 differs from execution lock")
    rate_limit = dict(definition.get("rate_limit_policy") or {})
    expected_runtime_semantic = str(
        rate_limit.get("runtime_policy_semantic_sha256") or ""
    )
    runtime_policy = job.get("openrouter_runtime_policy")
    if not isinstance(runtime_policy, Mapping):
        raise ContractLifecycleError("job embedded OpenRouter runtime policy is missing")
    if sha256_object(dict(runtime_policy)) != expected_runtime_semantic:
        raise ContractLifecycleError("job embedded OpenRouter runtime policy was replaced")
    if job.get("openrouter_runtime_policy_sha256") != expected_runtime_semantic:
        raise ContractLifecycleError(
            "job OpenRouter runtime-policy semantic hash differs from execution lock"
        )
    expected_runtime_file_sha = str(
        dict(definition.get("runtime_policy") or {}).get("sha256") or ""
    )
    if job.get("openrouter_runtime_policy_file_sha256") != expected_runtime_file_sha:
        raise ContractLifecycleError(
            "job OpenRouter runtime-policy file hash differs from execution lock"
        )

    bound_path = _regular_file(
        lock_path or str(job.get("execution_lock_path") or ""), "bound execution lock"
    )
    if load_mapping(bound_path) != dict(lock):
        raise ContractLifecycleError("job execution_lock_path does not contain this lock")
    actual_lock_sha = sha256_file(bound_path)
    expected_lock_sha = lock_sha256 or actual_lock_sha
    if actual_lock_sha != expected_lock_sha or job.get("execution_lock_sha256") != actual_lock_sha:
        raise ContractLifecycleError("job execution_lock_sha256 differs from execution lock")
    if resolve_repo_path(str(job.get("execution_lock_path") or "")).resolve() != bound_path:
        raise ContractLifecycleError("job execution_lock_path differs from planned lock path")


def _validated_case_refs(
    manifest: Mapping[str, Any],
    catalog: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
) -> list[dict[str, str]]:
    domains = list(manifest.get("domains") or [])
    domain = next(
        (
            item
            for item in domains
            if isinstance(item, Mapping) and item.get("domain") == "agentdojo"
        ),
        None,
    )
    if not isinstance(domain, Mapping):
        raise ContractLifecycleError("manifest has no AgentDojo domain")
    manifest_refs = [
        {"case_unit_id": str(row["case_unit_id"]), "task_id": str(row["task_id"])}
        for row in list(domain.get("case_units") or [])
        if isinstance(row, Mapping)
    ]
    catalog_refs = [
        {"case_unit_id": str(row["case_unit_id"]), "task_id": str(row["task_id"])}
        for row in list(catalog.get("items") or [])
        if isinstance(row, Mapping)
    ]
    source_refs = [
        {"case_unit_id": str(row["case_unit_id"]), "task_id": str(row["task_id"])}
        for row in list(source_bundle.get("sources") or [])
        if isinstance(row, Mapping)
    ]
    if manifest_refs != catalog_refs or manifest_refs != source_refs:
        raise ContractLifecycleError("manifest, catalog and source-bundle case/task order differ")
    if len(manifest_refs) != EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            f"execution lock requires exactly {EXPECTED_CASE_COUNT} case IDs"
        )
    ids = [row["case_unit_id"] for row in manifest_refs]
    if len(set(ids)) != EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("case IDs are not unique")
    counts = Counter(_suite(case_id) for case_id in ids)
    if dict(counts) != EXPECTED_SUITE_COUNTS:
        raise ContractLifecycleError(
            f"suite counts differ: expected={EXPECTED_SUITE_COUNTS}, actual={dict(counts)}"
        )
    return manifest_refs


def _model_snapshot(config: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    roles = config.get("experimental_agents")
    if not isinstance(roles, Mapping):
        raise ContractLifecycleError("agents config missing experimental_agents")
    fields = (
        "provider",
        "model",
        "model_version",
        "api_key_env",
        "temperature",
        "max_tokens",
        "timeout_seconds",
        "retry",
        "rate_limit",
        "save_response_metadata",
        "cost_tracking",
    )
    result: dict[str, dict[str, Any]] = {}
    for agent_id in EXPECTED_AGENTS:
        role = roles.get(agent_id)
        if not isinstance(role, Mapping):
            raise ContractLifecycleError(f"agents config missing {agent_id}")
        snapshot = {field: role.get(field) for field in fields}
        if snapshot["provider"] != "openrouter" or not snapshot.get("model"):
            raise ContractLifecycleError(f"{agent_id} must use a locked OpenRouter model")
        if not isinstance(snapshot.get("rate_limit"), Mapping):
            raise ContractLifecycleError(f"{agent_id} is missing rate_limit")
        snapshot["rate_limit"] = dict(snapshot["rate_limit"])
        snapshot["config_sha256"] = sha256_object(dict(role))
        result[agent_id] = snapshot
    return result


def _validate_final_credential_after_ramp(
    credential_receipt: Mapping[str, Any], ramp_receipt: Mapping[str, Any]
) -> None:
    credential_time = _parse_aware_timestamp(
        str(credential_receipt.get("created_at") or ""),
        "credential probe receipt created_at",
    )
    ramp_time = _parse_aware_timestamp(
        str(
            ramp_receipt.get("completed_at")
            or ramp_receipt.get("created_at")
            or ""
        ),
        "disposable ramp receipt completion timestamp",
    )
    if credential_time <= ramp_time:
        raise ContractLifecycleError(
            "final credential probe receipt must be created after disposable ramp completion"
        )


def _validate_budget_bindings(
    budget_plan: Mapping[str, Any],
    *,
    runtime_policy: Any,
    pre_ramp_credit_receipt: Mapping[str, Any],
    credit_receipt: Mapping[str, Any],
    credit_floor_usd: float,
) -> None:
    definition = budget_plan.get("definition")
    if not isinstance(definition, Mapping):
        raise ContractLifecycleError("execution budget plan definition is missing")
    guard = definition.get("budget_guard")
    if not isinstance(guard, Mapping):
        raise ContractLifecycleError("execution budget guard is missing")
    expected = {
        "projected_cost_usd": float(EXPECTED_PROJECTED_COST_USD),
        "credit_floor_usd": float(EXPECTED_CREDIT_FLOOR_USD),
        "maximum_run_cost_usd": float(EXPECTED_MAXIMUM_COST_CAP_USD),
        "cost_cap_action": "block_new_requests",
    }
    for field, value in expected.items():
        if guard.get(field) != value:
            raise ContractLifecycleError(
                f"execution budget plan {field} differs from the reviewed budget"
            )
    preflight = definition.get("preflight_projection")
    if not isinstance(preflight, Mapping):
        raise ContractLifecycleError("execution preflight budget projection is missing")
    expected_preflight = {
        "two_round_cost_usd": float(EXPECTED_PREFLIGHT_TWO_ROUND_COST_USD),
        "preflight_reserve_usd": float(EXPECTED_PREFLIGHT_RESERVE_USD),
        "recommended_initial_credit_usd": float(
            EXPECTED_RECOMMENDED_INITIAL_CREDIT_USD
        ),
        "required_post_ramp_credit_usd": float(EXPECTED_CREDIT_FLOOR_USD),
        "formal_maximum_run_cost_usd": float(EXPECTED_MAXIMUM_COST_CAP_USD),
    }
    for field, value in expected_preflight.items():
        if preflight.get(field) != value:
            raise ContractLifecycleError(
                f"execution preflight budget {field} differs from the reviewed budget"
            )
    if float(credit_floor_usd) != float(EXPECTED_CREDIT_FLOOR_USD):
        raise ContractLifecycleError("execution credit floor must be exactly $650")
    if (
        float(runtime_policy.budget.minimum_formal_start_remaining_usd)
        != float(EXPECTED_CREDIT_FLOOR_USD)
        or float(runtime_policy.budget.maximum_run_cost_usd)
        != float(EXPECTED_MAXIMUM_COST_CAP_USD)
        or runtime_policy.budget.cost_cap_action != "block_new_requests"
    ):
        raise ContractLifecycleError(
            "runtime budget policy differs from the locked $650 floor/cap"
        )
    for label, receipt in (
        ("pre-ramp", pre_ramp_credit_receipt),
        ("post-ramp", credit_receipt),
    ):
        budget = receipt.get("budget_policy")
        if (
            not isinstance(budget, Mapping)
            or float(budget.get("maximum_formal_run_cost_usd") or 0)
            != float(EXPECTED_MAXIMUM_COST_CAP_USD)
            or float(receipt.get("local_software_run_cost_cap_usd") or 0)
            != float(EXPECTED_MAXIMUM_COST_CAP_USD)
            or receipt.get("local_software_cost_cap_action")
            != "block_new_requests"
        ):
            raise ContractLifecycleError(
                f"{label} credential receipt does not bind the local $650 software cap"
            )
    limit_modes = {
        str(pre_ramp_credit_receipt.get("provider_limit_mode") or ""),
        str(credit_receipt.get("provider_limit_mode") or ""),
    }
    if len(limit_modes) != 1:
        raise ContractLifecycleError(
            "credential provider-limit mode changed across the disposable ramp"
        )
    limit_mode = next(iter(limit_modes))
    if limit_mode == "explicit_cap":
        if float(
            pre_ramp_credit_receipt.get("key_limit_remaining_usd") or 0
        ) < float(EXPECTED_RECOMMENDED_INITIAL_CREDIT_USD):
            raise ContractLifecycleError(
                "pre-ramp credential receipt does not prove the recommended $800 initial credit"
            )
        if float(credit_receipt.get("key_limit_remaining_usd") or 0) < float(
            EXPECTED_CREDIT_FLOOR_USD
        ):
            raise ContractLifecycleError(
                "credential receipt does not prove the $650 provider-key floor"
            )
    elif limit_mode == "unlimited_no_provider_cap":
        for label, receipt in (
            ("pre-ramp", pre_ramp_credit_receipt),
            ("post-ramp", credit_receipt),
        ):
            if (
                receipt.get("key_limit_usd") is not None
                or receipt.get("key_limit_remaining_usd") is not None
                or receipt.get("credit_floor_proof_status")
                != "waived_by_user_provider_balance_unavailable"
                or receipt.get("credit_floor_waiver_reason")
                != "provider_unlimited_key_exposes_no_limit_remaining_balance"
            ):
                raise ContractLifecycleError(
                    f"{label} unlimited-key receipt has inconsistent waiver semantics"
                )
    else:
        raise ContractLifecycleError("credential provider-limit mode is invalid")


def _validate_vps_provision_receipt(
    receipt: Mapping[str, Any],
    *,
    infra: Mapping[str, Any],
    infra_snapshot: Mapping[str, Any],
    credential_receipt: Mapping[str, Any],
) -> None:
    report = validate_object(
        "agentdojo_vps_provision_receipt", dict(receipt), raise_on_error=False
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"VPS provision receipt schema validation failed: {report.to_dict()}"
        )
    _require_aware_timestamp(str(receipt.get("recorded_at_utc") or ""))
    endpoint = dict(receipt.get("endpoint") or {})
    expected_endpoint = {
        "host": infra_snapshot["ssh_host"],
        "port": infra_snapshot["ssh_port"],
        "user": infra_snapshot["ssh_user"],
    }
    if endpoint != expected_endpoint:
        raise ContractLifecycleError("VPS provision endpoint differs from runtime overlay")
    identity = dict(receipt.get("host_identity") or {})
    if (
        identity.get("fingerprint_sha256")
        != infra_snapshot["ssh_host_ed25519_fingerprint"]
        or identity.get("local_known_hosts_match") is not True
        or identity.get("remote_public_key_match") is not True
    ):
        raise ContractLifecycleError(
            "VPS provision SSH fingerprint proof differs from runtime overlay"
        )
    paths = dict(receipt.get("paths") or {})
    if paths.get("repo_root") != infra_snapshot["remote_workdir"]:
        raise ContractLifecycleError("VPS provision repo_root differs from runtime overlay")
    if paths.get("python") != infra_snapshot["python_bin"]:
        raise ContractLifecycleError("VPS provision Python path differs from runtime overlay")

    platform = dict(receipt.get("platform") or {})
    if int(platform.get("vcpu_count") or 0) < int(infra_snapshot["cpu_limit"]):
        raise ContractLifecycleError("VPS provision CPU is below the runtime overlay")
    required_memory_kib = int(infra_snapshot["memory_gb"]) * 1024 * 1024
    if int(platform.get("memory_kib") or 0) < required_memory_kib:
        raise ContractLifecycleError("VPS provision memory is below the runtime overlay")
    required_disk_bytes = int(infra_snapshot["disk_free_gb_min"]) * 1_000_000_000
    if int(platform.get("root_disk_available_bytes") or 0) < required_disk_bytes:
        raise ContractLifecycleError("VPS provision free disk is below the runtime overlay")

    benchmark = dict(receipt.get("agentdojo") or {})
    expected_benchmark = {
        "package_version": AGENTDOJO_PACKAGE_VERSION,
        "git_commit": AGENTDOJO_COMMIT,
        "git_tree": AGENTDOJO_TREE,
        "benchmark_version": BENCHMARK_VERSION,
        "case_count": EXPECTED_CASE_COUNT,
        "suite_case_counts": dict(EXPECTED_SUITE_COUNTS),
    }
    for field, value in expected_benchmark.items():
        if benchmark.get(field) != value:
            raise ContractLifecycleError(
                f"VPS provision AgentDojo {field} differs from the execution definition"
            )
    if (
        benchmark.get("upstream_worktree_clean") is not True
        or benchmark.get("installed_source_matches_upstream_tree") is not True
    ):
        raise ContractLifecycleError("VPS provision does not prove a clean pinned AgentDojo tree")

    closure = receipt.get("agentdojo_runtime_source_closure")
    if not isinstance(closure, Mapping) or receipt.get(
        "agentdojo_runtime_source_closure_sha256"
    ) != sha256_object(dict(closure)):
        raise ContractLifecycleError(
            "VPS provision AgentDojo source-closure hash differs"
        )
    expected_closure = {
        "schema_version": "agentdojo_runtime_source_closure/v1",
        "package_name": "agentdojo",
        "package_version": AGENTDOJO_PACKAGE_VERSION,
        "official_git_commit": AGENTDOJO_COMMIT,
        "official_git_tree": AGENTDOJO_TREE,
        "wheel_filename": AGENTDOJO_WHEEL,
        "wheel_sha256": AGENTDOJO_WHEEL_SHA256,
        "upstream_head_matches_official_commit": True,
        "upstream_tree_matches_official_tree": True,
        "installed_source_matches_upstream_tree": True,
        "closure_verified": True,
        "secret_material_recorded": False,
        "record_verification": (
            "all_hashed_entries_match_paths_contained_no_links_or_special_inodes"
        ),
    }
    for field, value in expected_closure.items():
        if closure.get(field) != value:
            raise ContractLifecycleError(
                f"VPS provision AgentDojo source closure {field} differs"
            )
    if int(closure.get("installed_file_count") or 0) != int(
        closure.get("record_entry_count") or -1
    ):
        raise ContractLifecycleError(
            "VPS provision AgentDojo RECORD/install denominator differs"
        )
    if int(closure.get("record_verified_file_count") or 0) + int(
        closure.get("record_unhashed_entry_count") or 0
    ) != int(closure.get("record_entry_count") or -1):
        raise ContractLifecycleError(
            "VPS provision AgentDojo RECORD verification denominator differs"
        )

    runtime = dict(receipt.get("runtime") or {})
    if runtime.get("pyproject_sha256") != sha256_file(resolve_repo_path("pyproject.toml")):
        raise ContractLifecycleError("VPS provision pyproject hash is stale")
    if runtime.get("uv_lock_sha256") != sha256_file(resolve_repo_path("uv.lock")):
        raise ContractLifecycleError("VPS provision uv.lock hash is stale")
    local_src = resolve_repo_path("src")
    local_src_files = sorted(
        path
        for path in local_src.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and not any(part.endswith(".egg-info") for part in path.parts)
    )
    local_src_tree_sha256 = sha256_object(
        [
            {
                "path": path.relative_to(local_src).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in local_src_files
        ]
    )
    if runtime.get("deployed_src_tree_sha256") != local_src_tree_sha256:
        raise ContractLifecycleError("VPS provision deployed src tree hash is stale")
    if int(runtime.get("deployed_src_file_count") or 0) != len(local_src_files):
        raise ContractLifecycleError("VPS provision deployed src file count is stale")
    if runtime.get("local_remote_src_match_at_recording") is not True:
        raise ContractLifecycleError("VPS provision does not prove local/remote source equality")
    if runtime.get("final_execution_freeze_resync_required") is not False:
        raise ContractLifecycleError(
            "VPS provision receipt still requires the final execution-freeze resync"
        )
    recorded_at = _parse_aware_timestamp(
        str(receipt.get("recorded_at_utc") or ""), "VPS provision recorded_at_utc"
    )
    from evidence_system.adapters.agentdojo_runtime_control import (
        execution_runtime_snapshot,
    )

    runtime_files = [
        resolve_repo_path(path)
        for path in dict(execution_runtime_snapshot()["files"])
    ]
    latest_runtime_mtime = datetime.fromtimestamp(
        max(path.stat().st_mtime for path in runtime_files), tz=timezone.utc
    )
    if recorded_at < latest_runtime_mtime:
        raise ContractLifecycleError(
            "VPS provision receipt predates the final locked runtime-code modification"
        )

    credentials = dict(receipt.get("credentials") or {})
    if credentials.get("secret_material_recorded") is not False:
        raise ContractLifecycleError("VPS provision receipt must not contain secret material")
    status = receipt.get("status")
    readiness = dict(receipt.get("run_readiness") or {})
    if status == "provisioned":
        if readiness.get("formal_run_authorized") is not True:
            raise ContractLifecycleError("provisioned VPS receipt must authorize formal execution")
    elif status == "provisioned_blocked_on_credentials":
        if credential_receipt.get("status") != "passed":
            raise ContractLifecycleError(
                "credential-blocked VPS receipt requires a later passing credential receipt"
            )
        reasons = [str(value).lower() for value in readiness.get("blocking_reasons") or []]
        if any("credential" not in reason and "openrouter" not in reason for reason in reasons):
            raise ContractLifecycleError(
                "credential-blocked VPS receipt still contains a non-credential blocker"
            )
    else:
        raise ContractLifecycleError("VPS provision receipt status is not execution-ready")

    machines = list(infra.get("machines") or [])
    if len(machines) != 1:
        raise ContractLifecycleError("runtime overlay must remain single-machine")


def _strict_agentdojo_infra_snapshot(config: Mapping[str, Any]) -> dict[str, Any]:
    matches: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for machine in list(config.get("machines") or []):
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
            f"runtime infra overlay must contain exactly one enabled AgentDojo target; found {len(matches)}"
        )
    machine, benchmark = matches[0]
    ssh = machine.get("ssh")
    if machine.get("connection") != "ssh" or not isinstance(ssh, Mapping):
        raise ContractLifecycleError("AgentDojo runtime target must use SSH")
    fingerprint = str(
        ssh.get("ed25519_fingerprint")
        or ssh.get("host_ed25519_fingerprint")
        or ""
    )
    required_strings = {
        "machine_id": machine.get("machine_id"),
        "machine_role": machine.get("role"),
        "ssh_host": ssh.get("host"),
        "ssh_user": ssh.get("user"),
        "ssh_key_path": ssh.get("key_path"),
        "ssh_public_key_fingerprint": ssh.get("public_key_fingerprint"),
        "ssh_known_hosts_file": ssh.get("known_hosts_file"),
        "remote_workdir": machine.get("remote_workdir"),
        "runner_workdir": machine.get("runner_workdir") or machine.get("remote_workdir"),
        "install_dir": benchmark.get("install_dir"),
        "runner_command": benchmark.get("runner_command"),
        "python_bin": dict(machine.get("python") or {}).get("python_bin"),
        "python_env_path": dict(machine.get("python") or {}).get("env_path"),
        "results_dir": machine.get("results_dir"),
        "execution_user": benchmark.get("execution_user"),
        "monitor_user": benchmark.get("monitor_user"),
        "blind_group": benchmark.get("blind_group"),
        "secret_env_path": benchmark.get("secret_env_path"),
        "runtime_state_root": benchmark.get("runtime_state_root"),
        "remote_raw_root": benchmark.get("remote_raw_root"),
        "failed_attempt_archive_root": benchmark.get(
            "failed_attempt_archive_root"
        ),
        "blind_aggregate_root": benchmark.get("blind_aggregate_root"),
        "retrieval_snapshot_root": benchmark.get("retrieval_snapshot_root"),
    }
    for field, value in required_strings.items():
        text = str(value or "")
        if not text or _PLACEHOLDER_RE.search(text):
            raise ContractLifecycleError(f"runtime infra {field} is missing or a placeholder")
    if not fingerprint.startswith("SHA256:"):
        raise ContractLifecycleError("runtime infra must pin the SSH ED25519 host fingerprint")
    for field in (
        "remote_workdir",
        "runner_workdir",
        "install_dir",
        "python_bin",
        "python_env_path",
        "remote_raw_root",
        "failed_attempt_archive_root",
        "blind_aggregate_root",
        "retrieval_snapshot_root",
        "secret_env_path",
        "runtime_state_root",
    ):
        if not str(required_strings[field]).startswith("/"):
            raise ContractLifecycleError(f"runtime infra {field} must be absolute")
    if not Path(str(required_strings["ssh_key_path"])).expanduser().is_absolute():
        raise ContractLifecycleError("runtime infra ssh_key_path must be absolute")
    if not Path(str(required_strings["ssh_known_hosts_file"])).expanduser().is_absolute():
        raise ContractLifecycleError("runtime infra ssh_known_hosts_file must be absolute")
    if not str(required_strings["ssh_public_key_fingerprint"]).startswith("SHA256:"):
        raise ContractLifecycleError(
            "runtime infra must pin the controller SSH public-key fingerprint"
        )
    if required_strings["execution_user"] != required_strings["ssh_user"]:
        raise ContractLifecycleError("runtime execution user must equal the SSH execution user")
    if required_strings["monitor_user"] == required_strings["execution_user"]:
        raise ContractLifecycleError("runtime monitor and execution users must be distinct")
    remote_raw_root = Path(str(required_strings["remote_raw_root"]))
    failed_archive_root = Path(
        str(required_strings["failed_attempt_archive_root"])
    )
    blind_root = Path(str(required_strings["blind_aggregate_root"]))
    retrieval_snapshot_root = Path(
        str(required_strings["retrieval_snapshot_root"])
    )
    secret_path = Path(str(required_strings["secret_env_path"]))
    runtime_state_root = Path(str(required_strings["runtime_state_root"]))
    remote_repo = Path(str(required_strings["remote_workdir"]))
    control_roots = (
        remote_raw_root,
        blind_root,
        runtime_state_root,
        failed_archive_root,
        retrieval_snapshot_root,
    )
    if len(set(control_roots)) != len(control_roots):
        raise ContractLifecycleError(
            "formal evidence/control roots must be pairwise distinct"
        )
    for position, first in enumerate(control_roots):
        for second in control_roots[position + 1 :]:
            if _is_path_within(first, second) or _is_path_within(second, first):
                raise ContractLifecycleError(
                    "formal evidence/control roots must not overlap by ancestry"
                )
    for candidate, label in (
        (remote_raw_root, "sealed raw root"),
        (blind_root, "blind aggregate root"),
        (runtime_state_root, "runtime-state root"),
        (failed_archive_root, "failed-attempt archive root"),
        (retrieval_snapshot_root, "retrieval snapshot root"),
        (secret_path, "secret environment path"),
    ):
        if _is_path_within(candidate, remote_repo) or _is_path_within(remote_repo, candidate):
            raise ContractLifecycleError(
                f"runtime {label} must be outside the repository sync tree"
            )
    expected_modes = {
        "remote_raw_parent_mode": "0700",
        "remote_raw_mode": "0700",
        "failed_attempt_archive_parent_mode": "0700",
        "failed_attempt_archive_mode": "0700",
        "blind_aggregate_dir_mode": "0750",
        "blind_aggregate_file_mode": "0640",
        "retrieval_snapshot_parent_mode": "0700",
        "retrieval_snapshot_mode": "0700",
        "secret_parent_mode": "0700",
        "secret_file_mode": "0600",
        "runtime_state_parent_mode": "0700",
        "runtime_state_mode": "0700",
    }
    for field, expected in expected_modes.items():
        if str(benchmark.get(field) or "") != expected:
            raise ContractLifecycleError(
                f"runtime infra {field} must be locked to {expected}"
            )
    if (
        benchmark.get("runtime_state_initialization")
        != "atomic_create_once_then_reuse_exact_identity"
    ):
        raise ContractLifecycleError(
            "runtime-state initialization must be atomic create-once exact reuse"
        )
    concurrency = int(machine.get("concurrency") or 0)
    if concurrency < 1:
        raise ContractLifecycleError("runtime infra concurrency must be positive")
    resources = machine.get("resources")
    if not isinstance(resources, Mapping):
        raise ContractLifecycleError("runtime infra AgentDojo resources are missing")
    cpu_limit = int(resources.get("cpu_limit") or 0)
    memory_gb = int(resources.get("memory_gb") or 0)
    disk_free_gb_min = int(machine.get("disk_free_gb_min") or 0)
    if cpu_limit < 1 or memory_gb < 1 or disk_free_gb_min < 1:
        raise ContractLifecycleError("runtime infra CPU, memory, and disk limits must be positive")
    if resources.get("gpu") is not False:
        raise ContractLifecycleError("AgentDojo runtime infra must explicitly declare gpu=false")
    return {
        **{key: str(value) for key, value in required_strings.items()},
        "ssh_port": int(ssh.get("port") or 22),
        "ssh_host_ed25519_fingerprint": fingerprint,
        "machine_concurrency": concurrency,
        "cpu_limit": cpu_limit,
        "memory_gb": memory_gb,
        "disk_free_gb_min": disk_free_gb_min,
        "benchmark_config_sha256": sha256_object(dict(benchmark)),
        **expected_modes,
    }


def _ed25519_public_key_fingerprint(path: Path) -> str:
    """Return OpenSSH SHA256 fingerprint without reading the private key."""

    try:
        fields = path.read_text(encoding="ascii").strip().split()
        if len(fields) < 2 or fields[0] != "ssh-ed25519":
            raise ValueError("not an ED25519 OpenSSH public key")
        blob = base64.b64decode(fields[1], validate=True)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractLifecycleError(
            "controller SSH public key is not a valid ED25519 OpenSSH key"
        ) from exc
    return "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode(
        "ascii"
    ).rstrip("=")


def _require_independent_runtime_overlay(path: Path) -> None:
    shared = resolve_repo_path("configs/infra.yaml").resolve()
    if path == shared:
        raise ContractLifecycleError(
            "AgentDojo full execution must use an independent runtime infra overlay, not configs/infra.yaml"
        )
    expected_root = resolve_repo_path(EXPERIMENT_ROOT / "runtime").resolve()
    if expected_root not in path.parents:
        raise ContractLifecycleError(
            f"runtime infra overlay must live below {_repo_relative(expected_root)}"
        )


def _is_path_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


def _output_precondition() -> dict[str, Any]:
    staging_namespace_root = resolve_repo_path(DEFAULT_STAGING_NAMESPACE_ROOT)
    staging_root = resolve_repo_path(DEFAULT_STAGING_RAW_RESULT_ROOT)
    formal_namespace_root = resolve_repo_path(DEFAULT_FORMAL_NAMESPACE_ROOT)
    reservation_file = resolve_repo_path(DEFAULT_FORMAL_NAMESPACE_RESERVATION)
    raw_root = resolve_repo_path(DEFAULT_FORMAL_RAW_RESULT_ROOT)
    score_roots = [resolve_repo_path(path) for path in DEFAULT_SCORE_NAMESPACE_ROOTS]
    staging_namespace_count = _file_count(staging_namespace_root)
    staging_count = _file_count(staging_root)
    reservation_lock = _validated_formal_namespace_reservation(
        formal_namespace_root, reservation_file
    )
    raw_count = _file_count(raw_root)
    score_count = sum(_file_count(path) for path in score_roots)
    if staging_namespace_count or staging_count or raw_count or score_count:
        raise ContractLifecycleError(
            "execution lock must be published before staging/formal raw results or scores exist: "
            f"staging_namespace_files={staging_namespace_count}, "
            f"staging_raw_files={staging_count}, formal_files={raw_count}, "
            f"score_files={score_count}"
        )
    return {
        "staging_namespace_root": _repo_relative(staging_namespace_root),
        "staging_namespace_file_count": 0,
        "staging_raw_result_root": _repo_relative(staging_root),
        "staging_raw_result_file_count": 0,
        "formal_namespace_root": _repo_relative(formal_namespace_root),
        "formal_namespace_allowed_file_count": 1,
        "formal_namespace_reservation": reservation_lock,
        "formal_raw_result_root": _repo_relative(raw_root),
        "formal_raw_result_file_count": 0,
        "score_result_roots": [_repo_relative(path) for path in score_roots],
        "score_result_file_count": 0,
        "evidence_visibility": "sealed_from_checklist_review_until_join_lock",
    }


def _validated_formal_namespace_reservation(
    namespace_root: Path, reservation_file: Path
) -> dict[str, str]:
    if namespace_root.is_symlink() or not namespace_root.is_dir():
        raise ContractLifecycleError(
            "formal namespace root must exist as a non-symlink directory before execution lock"
        )
    files = sorted(path for path in namespace_root.rglob("*") if path.is_file())
    if any(path.is_symlink() for path in namespace_root.rglob("*")):
        raise ContractLifecycleError("formal namespace root contains a symlink")
    if files != [reservation_file]:
        relative = [path.relative_to(namespace_root).as_posix() for path in files]
        raise ContractLifecycleError(
            "formal namespace may contain only NAMESPACE_LOCK.json before execution; "
            f"observed={relative}"
        )
    payload = load_mapping(reservation_file)
    expected = {
        "schema_version": "result_namespace_lock/v1",
        "result_namespace": RESULT_NAMESPACE,
        "experiment_manifest_path": _repo_relative(resolve_repo_path(DEFAULT_MANIFEST)),
        "formal_result_root": _repo_relative(resolve_repo_path(DEFAULT_FORMAL_RAW_RESULT_ROOT)),
        "legacy_result_root": "results/full/agentdojo",
        "legacy_result_root_must_not_be_modified": True,
        "status": "reserved_no_formal_runs_yet",
    }
    if payload != expected:
        raise ContractLifecycleError("formal namespace reservation metadata is stale or invalid")
    return _path_lock(reservation_file)


def _file_count(path: Path) -> int:
    if path.is_symlink():
        raise ContractLifecycleError(f"formal output root must not be a symlink: {path}")
    if not path.exists():
        return 0
    if not path.is_dir():
        raise ContractLifecycleError(f"formal output root must be a directory: {path}")
    if any(child.is_symlink() for child in path.rglob("*")):
        raise ContractLifecycleError(f"formal output root contains symlinks: {path}")
    return sum(1 for child in path.rglob("*") if child.is_file())


def _canary_case_ids(case_ids: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for case_id in case_ids:
        result.setdefault(_suite(case_id), case_id)
    if set(result) != set(EXPECTED_SUITE_COUNTS):
        raise ContractLifecycleError("could not select exactly one canary from each suite")
    return dict(sorted(result.items()))


def _concurrency_promotion_policy(
    job_entries: Sequence[Mapping[str, Any]], canaries: Mapping[str, str]
) -> dict[str, Any]:
    by_identity = {
        (str(entry["case_unit_id"]), str(entry["agent_id"])): dict(entry)
        for entry in job_entries
    }
    canary_slots = [
        str(by_identity[(case_id, agent_id)]["record_slot_id"])
        for case_id in canaries.values()
        for agent_id in EXPECTED_AGENTS
    ]
    canary_cases = set(canaries.values())
    stage_specs = ((8, 32), (16, 64), (32, 128))
    ramp_by_agent: dict[str, list[dict[str, Any]]] = {}
    for agent_id in EXPECTED_AGENTS:
        available = [
            str(entry["record_slot_id"])
            for entry in job_entries
            if entry.get("agent_id") == agent_id
            and entry.get("case_unit_id") not in canary_cases
        ]
        offset = 0
        stages: list[dict[str, Any]] = []
        for workers, sample_count in stage_specs:
            slots = available[offset : offset + sample_count]
            if len(slots) != sample_count:
                raise ContractLifecycleError(
                    f"cannot lock {sample_count} distinct {agent_id} ramp slots "
                    f"at workers={workers}"
                )
            stages.append(
                {
                    "workers": workers,
                    "agent_id": agent_id,
                    "new_distinct_slot_count": sample_count,
                    "record_slot_ids": slots,
                    "record_slot_ids_sha256": sha256_object(slots),
                }
            )
            offset += sample_count
        ramp_by_agent[agent_id] = stages
    return {
        "agent_batch_order": list(EXPECTED_AGENTS),
        "complete_each_agent_before_next": True,
        "canary": {
            "workers": 4,
            "suite_count": 4,
            "agent_count": 3,
            "record_slot_count": 12,
            "record_slot_ids": canary_slots,
            "record_slot_ids_sha256": sha256_object(canary_slots),
        },
        "agent_ramp_stages": ramp_by_agent,
        "formal_stage_order": [
            "canary",
            "ramp-a-8",
            "ramp-a-16",
            "ramp-a-32",
            "remaining-a",
            "ramp-b-8",
            "ramp-b-16",
            "ramp-b-32",
            "remaining-b",
            "ramp-c-8",
            "ramp-c-16",
            "ramp-c-32",
            "remaining-c",
            "recovery-a",
            "recovery-b",
            "recovery-c",
        ],
        "promotion_inputs": "blind_runtime_health_only",
        "on_stage_failure": "return_to_previous_safe_concurrency_and_continue",
        "interrupt_batch_on_stage_failure": False,
    }


def _suite(case_id: str) -> str:
    bits = case_id.split(":")
    if len(bits) != 4 or bits[0] != BENCHMARK_VERSION:
        raise ContractLifecycleError(f"invalid AgentDojo case ID: {case_id!r}")
    return bits[1]


def _safe_id(value: str) -> str:
    return _SAFE_ID_RE.sub("-", value).strip("-") or "x"


def _regular_file(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise ContractLifecycleError(f"{label} is missing, not regular, or symlinked: {candidate}")
    return candidate.resolve()


def _regular_dir(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    if candidate.is_symlink() or not candidate.is_dir():
        raise ContractLifecycleError(f"{label} is missing, not regular, or symlinked: {candidate}")
    if any(child.is_symlink() for child in candidate.rglob("*")):
        raise ContractLifecycleError(f"{label} contains symlinks: {candidate}")
    return candidate.resolve()


def _path_lock(path: Path) -> dict[str, str]:
    return {"path": _repo_relative(path), "sha256": sha256_file(path)}


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _require_aware_timestamp(value: str) -> None:
    _parse_aware_timestamp(value, "locked_at")


def _parse_aware_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractLifecycleError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ContractLifecycleError(f"{label} must include a timezone")
    return parsed


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    if path.is_symlink():
        raise ContractLifecycleError(f"refusing to replace symlinked lock: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode("utf-8")
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
        ) as handle:
            staged = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
        staged = None
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
