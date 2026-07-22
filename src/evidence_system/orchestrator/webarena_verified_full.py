"""Fail-closed planner for the frozen WebArena-Verified v1.2.3 full run.

This module deliberately does not reuse :func:`plan_smoke_jobs`.  The generic
planner can synthesize a fallback evidence contract and selects one machine per
domain, while the frozen WebArena study requires exactly 812 locked contracts
and an Agent A/B/C to VPS one-to-one route for all 2,436 record slots.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

import jsonschema

from evidence_system.contracts.common import contract_content_hash
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object


EXPECTED_CASE_COUNT = 812
EXPECTED_AGENT_IDS = ("Agent A", "Agent B", "Agent C")
EXPECTED_RECORD_SLOT_COUNT = EXPECTED_CASE_COUNT * len(EXPECTED_AGENT_IDS)
RESULT_NAMESPACE = "webarena_verified_v1_2_3_full_812"
MANIFEST_SCHEMA_VERSION = "webarena_verified_full_812_manifest/v1"
SOURCE_BUNDLE_SCHEMA_VERSION = "contract_source_bundle.v2"
NATIVE_CLAIM_INDEX_SCHEMA_VERSION = "webarena_verified_native_claim_index/v1"
NATIVE_CLAIM_ACCEPTANCE_SCHEMA_VERSION = (
    "webarena_verified_native_claim_acceptance/v1"
)
SCHEDULE_ACCEPTANCE_SCHEMA_VERSION = (
    "webarena_verified_full_812_scheduler_acceptance/v1"
)
SCHEDULE_INDEX_SCHEMA_VERSION = "webarena_verified_full_812_schedule_index/v1"
ARTIFACT_RETENTION_MODE = "vps_persistent_remote_v1"

EXPECTED_MANIFEST_SHA256 = (
    "86671e213ef0149f98240830ef20a2c38585c3c8d0529e6ae77d9d36d6597c35"
)
EXPECTED_SOURCE_SHA256 = (
    "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
)
EXPECTED_TASK_CONTRACT_INDEX_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
EXPECTED_SOURCE_BUNDLE_SHA256 = (
    "3009541e335bb309bccbe37f3c54581e5b3024bc2d78e35f16ba9392c3e2bd6b"
)

DEFAULT_MANIFEST = Path(
    "experiments/step19/webarena_verified_full_812_manifest.json"
)
DEFAULT_SOURCE_BUNDLE = Path(
    "experiments/evidence_contracts/source_bundles/"
    "webarena_verified_full_812_source_bundle.json"
)
DEFAULT_TASK_CONTRACT_INDEX = Path(
    "experiments/case_packets/webarena_verified/task_contract_index.json"
)
DEFAULT_AGENTS_CONFIG = Path("configs/agents.yaml")
DEFAULT_SITE_LOCK = Path("configs/webarena_verified_sites.lock.json")
DEFAULT_REMOTE_WORKDIR = "/opt/evidence-system/webarena_verified_full_812"
DEFAULT_NATIVE_CLAIM_ROOT = Path(
    "experiments/step20/webarena_verified/native_claims"
)
DEFAULT_NATIVE_CLAIM_INDEX = DEFAULT_NATIVE_CLAIM_ROOT / "index.json"
DEFAULT_NATIVE_CLAIM_ACCEPTANCE = DEFAULT_NATIVE_CLAIM_ROOT / "acceptance.json"
DEFAULT_LOCKED_CONTRACTS_ROOT = DEFAULT_NATIVE_CLAIM_ROOT / "locked/contracts"
DEFAULT_OPERATOR_WAIVER = Path(
    "experiments/step20/webarena_verified/operator_waiver.json"
)
DEFAULT_JOBS_ROOT = Path("experiments/step20/webarena_verified/jobs/full")
DEFAULT_DRY_RUN_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/full_scheduler_dry_run_acceptance.json"
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_LOCKED_COUNT_FIELDS = (
    "native_ir",
    "draft_contracts",
    "draft_checklists",
    "machine_validated",
    "human_signed",
    "locked_contracts",
    "locked_checklists",
)
_FORMAL_GATE_FIELDS = (
    "input_set_exact",
    "source_hashes_valid",
    "native_semantics_complete",
    "contracts_schema_valid",
    "checklists_schema_valid",
    "machine_validation_complete",
    "human_signoff_complete",
    "formal_locks_complete",
    "agent_input_tree_unchanged",
)
_WEBARENA_SITES = {
    "shopping",
    "shopping_admin",
    "reddit",
    "gitlab",
    "wikipedia",
    "map",
}

# Execution-transport identity is intentionally locked outside the Step 19
# task/source manifest. It is copied into every formal execution target and is
# therefore covered by every job and schedule hash without changing the
# task/evaluator evidence chain.
EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT = (
    "SHA256:rcKcDTJ+/mpnVGDcwUP5SIPho8K9E1qu+QBqj9JY1es"
)

EXPECTED_ROUTES: dict[str, dict[str, Any]] = {
    "Agent A": {
        "server_id": "webarena-gpt54-ord",
        "ssh_host": "45.76.67.186",
        "ssh_user": "root",
        "ssh_host_ed25519_fingerprint": (
            "SHA256:ObgyygktdU2dhYU1CA+rf9PSgmLkv47xxN9FnL1+iYo"
        ),
        "controller_ssh_public_key_fingerprint": (
            EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT
        ),
        "model": "openai/gpt-5.4",
        "concurrency": 1,
    },
    "Agent B": {
        "server_id": "webarena-claude47-ord",
        "ssh_host": "66.42.108.130",
        "ssh_user": "root",
        "ssh_host_ed25519_fingerprint": (
            "SHA256:3hhiish7icTf+jeSmfN6anqb37YhX3qwnhZKloHuPMM"
        ),
        "controller_ssh_public_key_fingerprint": (
            EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT
        ),
        "model": "anthropic/claude-opus-4.7",
        "concurrency": 1,
    },
    "Agent C": {
        "server_id": "webarena-deepseek-v4pro-ord",
        "ssh_host": "149.28.79.226",
        "ssh_user": "root",
        "ssh_host_ed25519_fingerprint": (
            "SHA256:r01stp+Wa+34Y/dxjscF+LpB47u9fuB/3h4MuF/K3AE"
        ),
        "controller_ssh_public_key_fingerprint": (
            EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT
        ),
        "model": "deepseek/deepseek-v4-pro",
        "concurrency": 1,
    },
}


class WebArenaFullScheduleError(RuntimeError):
    """Raised before any formal job is written when a frozen input is invalid."""


@dataclass(frozen=True)
class FullSchedulePlan:
    jobs: tuple[dict[str, Any], ...]
    acceptance: dict[str, Any]


def plan_full_schedule(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    task_contract_index_path: str | Path = DEFAULT_TASK_CONTRACT_INDEX,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    site_lock_path: str | Path = DEFAULT_SITE_LOCK,
    native_claim_index_path: str | Path = DEFAULT_NATIVE_CLAIM_INDEX,
    native_claim_acceptance_path: str | Path = DEFAULT_NATIVE_CLAIM_ACCEPTANCE,
    locked_contracts_root: str | Path = DEFAULT_LOCKED_CONTRACTS_ROOT,
    expected_manifest_sha256: str | None = EXPECTED_MANIFEST_SHA256,
    expected_source_bundle_sha256: str | None = EXPECTED_SOURCE_BUNDLE_SHA256,
) -> FullSchedulePlan:
    """Validate every formal input and return the exact frozen 2,436-slot plan."""

    manifest_file = _regular_file(manifest_path, "Step 19 manifest")
    source_bundle_file = _regular_file(source_bundle_path, "source bundle")
    task_contract_file = _regular_file(
        task_contract_index_path, "task contract index"
    )
    agents_file = _regular_file(agents_config_path, "agents config")
    site_lock_file = _regular_file(site_lock_path, "WebArena site lock")
    native_index_file = _regular_file(native_claim_index_path, "native claim index")
    native_acceptance_file = _regular_file(
        native_claim_acceptance_path, "native claim acceptance"
    )
    contracts_root = resolve_repo_path(locked_contracts_root)

    _validate_sha_sidecar(manifest_file)
    _validate_sha_sidecar(source_bundle_file)
    _validate_sha_sidecar(task_contract_file)
    _validate_sha_sidecar(native_index_file)
    _validate_sha_sidecar(native_acceptance_file)
    _require_equal(
        "frozen task contract index SHA-256",
        sha256_file(task_contract_file),
        EXPECTED_TASK_CONTRACT_INDEX_SHA256,
    )

    manifest_hash = sha256_file(manifest_file)
    if expected_manifest_sha256 is not None:
        _require_equal(
            "frozen Step 19 manifest SHA-256",
            manifest_hash,
            expected_manifest_sha256,
        )
    manifest = _mapping(manifest_file, "Step 19 manifest")
    cases, slots = _validate_manifest(manifest)

    task_contract_index = _mapping(task_contract_file, "task contract index")
    task_contracts = _validate_task_contract_index(task_contract_index, cases)

    source_bundle_hash = sha256_file(source_bundle_file)
    if expected_source_bundle_sha256 is not None:
        _require_equal(
            "frozen WebArena source bundle SHA-256",
            source_bundle_hash,
            expected_source_bundle_sha256,
        )
    source_bundle = _mapping(source_bundle_file, "source bundle")
    source_entries = _validate_source_bundle(
        source_bundle,
        source_bundle_file=source_bundle_file,
        manifest_file=manifest_file,
        cases=cases,
    )

    role_configs = _validate_agents_config(agents_file)
    native_index = _mapping(native_index_file, "native claim index")
    native_acceptance = _mapping(native_acceptance_file, "native claim acceptance")
    launch_policy = _validate_native_claim_acceptance(
        index=native_index,
        index_file=native_index_file,
        acceptance=native_acceptance,
    )
    contracts_root = _directory(contracts_root, "locked contracts root")
    claim_cases = _validate_native_claim_gate(
        index=native_index,
        index_file=native_index_file,
        acceptance=native_acceptance,
        acceptance_file=native_acceptance_file,
        contracts_root=contracts_root,
        cases=cases,
        launch_policy=launch_policy,
    )
    contracts = _validate_locked_contracts(
        contracts_root=contracts_root,
        cases=cases,
        source_entries=source_entries,
        claim_cases=claim_cases,
        manifest_hash=manifest_hash,
        launch_policy=launch_policy,
    )

    jobs = _build_jobs(
        manifest=manifest,
        manifest_hash=manifest_hash,
        source_bundle_hash=source_bundle_hash,
        native_claim_index_hash=sha256_file(native_index_file),
        native_claim_acceptance_hash=sha256_file(native_acceptance_file),
        cases=cases,
        slots=slots,
        source_entries=source_entries,
        claim_cases=claim_cases,
        task_contracts=task_contracts,
        contracts=contracts,
        role_configs=role_configs,
        site_lock_sha256=sha256_file(site_lock_file),
        launch_policy=launch_policy,
    )
    summary = _validate_planned_jobs(jobs, slots=slots)

    acceptance = {
        "schema_version": SCHEDULE_ACCEPTANCE_SCHEMA_VERSION,
        "status": "pass",
        "formal_launch_eligible": True,
        "dry_run": True,
        "result_namespace": RESULT_NAMESPACE,
        "inputs": {
            "step19_manifest_path": _display_path(manifest_file),
            "step19_manifest_sha256": manifest_hash,
            "source_bundle_path": _display_path(source_bundle_file),
            "source_bundle_sha256": source_bundle_hash,
            "task_contract_index_path": _display_path(task_contract_file),
            "task_contract_index_sha256": sha256_file(task_contract_file),
            "agents_config_path": _display_path(agents_file),
            "agents_config_sha256": sha256_file(agents_file),
            "site_lock_path": _display_path(site_lock_file),
            "site_lock_sha256": sha256_file(site_lock_file),
            "native_claim_index_path": _display_path(native_index_file),
            "native_claim_index_sha256": sha256_file(native_index_file),
            "native_claim_acceptance_path": _display_path(native_acceptance_file),
            "native_claim_acceptance_sha256": sha256_file(native_acceptance_file),
            "locked_contracts_root": _display_path(contracts_root),
            **(
                {
                    "operator_waiver_path": launch_policy["operator_waiver_path"],
                    "operator_waiver_sha256": launch_policy["operator_waiver_sha256"],
                }
                if launch_policy["basis"] == "operator_machine_only_waiver"
                else {}
            ),
        },
        "counts": {
            "requested_cases": EXPECTED_CASE_COUNT,
            "requested_record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "requested_per_agent": summary["requested_per_agent"],
            "planned_cases": EXPECTED_CASE_COUNT,
            "planned_record_slots": len(jobs),
            "planned_per_agent": summary["planned_per_agent"],
            "unique_record_slot_ids": summary["unique_record_slot_ids"],
            "locked_contracts": len(contracts),
            "fallback_contracts": 0,
        },
        "routing": {
            "policy": "one_locked_vps_per_agent_concurrency_1",
            "cross_server_parallelism": 3,
            "routes": EXPECTED_ROUTES,
            "planned_per_server": summary["planned_per_server"],
        },
        "transport_identity": {
            "boundary": "execution_transport_independent_of_case_source_chain",
            "controller_key_algorithm": "ssh-ed25519",
            "controller_ssh_public_key_fingerprint": (
                EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT
            ),
            "route_count": len(EXPECTED_ROUTES),
            "planned_job_count": len(jobs),
            "all_routes_explicitly_bound": True,
            "all_jobs_explicitly_bound": True,
            "step19_source_manifest_unchanged": True,
        },
        "schedule": {
            "order": "exact Step 19 record_slots order",
            "record_slots_sha256": sha256_object(
                [job["record_slot_id"] for job in jobs]
            ),
            "jobs_sha256": sha256_object(jobs),
            "first_record_slot_id": jobs[0]["record_slot_id"],
            "last_record_slot_id": jobs[-1]["record_slot_id"],
        },
        "launch_authorization": launch_policy,
        "gates": {
            "step19_manifest_frozen_and_self_consistent": True,
            "source_bundle_exact_812": True,
            "native_claim_formal_launch_eligible": True,
            **(
                {"operator_machine_only_waiver_valid": True}
                if launch_policy["basis"] == "operator_machine_only_waiver"
                else {"human_signoff_lock_valid": True}
            ),
            "locked_contract_set_exact_812": True,
            "locked_contract_fallback_disabled": True,
            "requested_equals_planned_per_agent": True,
            "record_slot_ids_exact_and_unique": True,
            "paired_seed_policy_exact": True,
            "agent_model_server_route_exact": True,
            "controller_ssh_public_key_transport_lock_exact": True,
            "remote_dotenv_sync_allowed": False,
        },
        "secret_transport": {
            "remote_dotenv_sync_allowed": False,
            "api_key_persisted_on_vps_by_scheduler": False,
            "mechanism": "single-line SSH stdin to per-process environment",
        },
        "blocking_reasons": [],
    }
    return FullSchedulePlan(jobs=tuple(jobs), acceptance=acceptance)


def blocked_dry_run_acceptance(
    reason: str,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    task_contract_index_path: str | Path = DEFAULT_TASK_CONTRACT_INDEX,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    site_lock_path: str | Path = DEFAULT_SITE_LOCK,
    native_claim_index_path: str | Path = DEFAULT_NATIVE_CLAIM_INDEX,
    native_claim_acceptance_path: str | Path = DEFAULT_NATIVE_CLAIM_ACCEPTANCE,
    locked_contracts_root: str | Path = DEFAULT_LOCKED_CONTRACTS_ROOT,
) -> dict[str, Any]:
    """Return a non-launchable, secret-free receipt for a failed dry run."""

    def descriptor(path: str | Path) -> dict[str, Any]:
        resolved = resolve_repo_path(path)
        return {
            "path": _display_path(resolved),
            "exists": resolved.exists(),
            "sha256": sha256_file(resolved) if resolved.is_file() else None,
        }

    return {
        "schema_version": SCHEDULE_ACCEPTANCE_SCHEMA_VERSION,
        "status": "blocked",
        "formal_launch_eligible": False,
        "dry_run": True,
        "result_namespace": RESULT_NAMESPACE,
        "inputs": {
            "step19_manifest": descriptor(manifest_path),
            "source_bundle": descriptor(source_bundle_path),
            "task_contract_index": descriptor(task_contract_index_path),
            "agents_config": descriptor(agents_config_path),
            "site_lock": descriptor(site_lock_path),
            "native_claim_index": descriptor(native_claim_index_path),
            "native_claim_acceptance": descriptor(native_claim_acceptance_path),
            "locked_contracts_root": {
                "path": _display_path(resolve_repo_path(locked_contracts_root)),
                "exists": resolve_repo_path(locked_contracts_root).is_dir(),
            },
        },
        "counts": {
            "requested_cases": EXPECTED_CASE_COUNT,
            "requested_record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "planned_record_slots": 0,
            "fallback_contracts": 0,
        },
        "gates": {
            "no_jobs_written_before_all_gates_pass": True,
            "locked_contract_fallback_disabled": True,
            "remote_dotenv_sync_allowed": False,
        },
        "blocking_reasons": [str(reason)],
    }


def write_jobs(
    plan: FullSchedulePlan,
    *,
    output_root: str | Path = DEFAULT_JOBS_ROOT,
    replace: bool = False,
) -> dict[str, Any]:
    """Atomically materialize an already accepted schedule."""

    if plan.acceptance.get("formal_launch_eligible") is not True:
        raise WebArenaFullScheduleError("refusing to write a non-launchable schedule")
    output = resolve_repo_path(output_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not replace:
        raise WebArenaFullScheduleError(
            f"jobs output already exists; pass replace=True explicitly: {output}"
        )
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=str(output.parent))
    )
    try:
        entries: list[dict[str, Any]] = []
        for position, job in enumerate(plan.jobs):
            path = temporary / f"{position:04d}-{job['record_slot_id']}.json"
            _write_json(path, job)
            entries.append(
                {
                    "position": position,
                    "record_slot_id": job["record_slot_id"],
                    "job_id": job["job_id"],
                    "path": path.name,
                    "sha256": sha256_file(path),
                }
            )
        index = {
            "schema_version": SCHEDULE_INDEX_SCHEMA_VERSION,
            "result_namespace": RESULT_NAMESPACE,
            "job_count": len(entries),
            "jobs_sha256": sha256_object(plan.jobs),
            "launch_authorization": dict(
                plan.acceptance.get("launch_authorization") or {}
            ),
            "entries": entries,
        }
        index_path = temporary / "index.json"
        _write_json(index_path, index)
        _write_sha_sidecar(index_path)
        if output.exists():
            shutil.rmtree(output)
        os.replace(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "jobs_root": _display_path(output),
        "job_count": len(plan.jobs),
        "index_path": _display_path(output / "index.json"),
        "index_sha256": sha256_file(output / "index.json"),
    }


def write_acceptance(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output = resolve_repo_path(path)
    _write_json(output, payload)
    _write_sha_sidecar(output)
    return output


def _validate_manifest(
    manifest: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require_equal("manifest schema", manifest.get("schema_version"), MANIFEST_SCHEMA_VERSION)
    _require_equal("manifest status", manifest.get("status"), "frozen")
    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        raise WebArenaFullScheduleError("manifest integrity block is missing")
    core = dict(manifest)
    core.pop("integrity", None)
    _require_equal("manifest core SHA-256", integrity.get("core_sha256"), sha256_object(core))

    benchmark = manifest.get("benchmark")
    if not isinstance(benchmark, Mapping):
        raise WebArenaFullScheduleError("manifest benchmark block is missing")
    expected_benchmark = {
        "name": "WebArena-Verified",
        "version": "v1.2.3",
        "split": "full",
        "case_count": EXPECTED_CASE_COUNT,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "task_id_range": [0, 811],
        "task_ids_unique": True,
    }
    for field, expected in expected_benchmark.items():
        _require_equal(f"manifest benchmark.{field}", benchmark.get(field), expected)

    policy = manifest.get("common_run_policy")
    if not isinstance(policy, Mapping):
        raise WebArenaFullScheduleError("manifest common_run_policy is missing")
    expected_policy = {
        "base_seed": 123000,
        "case_order": "ascending_numeric_task_id",
        "seed_policy": "same seed for all three models on a task",
        "concurrency_per_server": 1,
        "cross_server_parallelism": 3,
        "max_steps": 30,
        "timeout_seconds": 120,
        "retry_count": 2,
        "observation_type": "accessibility_tree",
        "action_set": "id_accessibility_tree",
        "same_agent_scaffold": True,
        "reset_environment_before_each_case": True,
    }
    for field, expected in expected_policy.items():
        _require_equal(f"manifest common_run_policy.{field}", policy.get(field), expected)

    cases_raw = manifest.get("cases")
    if not isinstance(cases_raw, list) or len(cases_raw) != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("manifest must contain exactly 812 cases")
    cases = [dict(item) for item in cases_raw if isinstance(item, Mapping)]
    if len(cases) != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("manifest contains a non-object case")
    _require_equal(
        "manifest case task order",
        [int(case.get("task_id", -1)) for case in cases],
        list(range(EXPECTED_CASE_COUNT)),
    )
    _require_equal(
        "manifest case ordinals",
        [int(case.get("ordinal", -1)) for case in cases],
        list(range(1, EXPECTED_CASE_COUNT + 1)),
    )
    _require_equal("manifest cases SHA-256", manifest.get("cases_sha256"), sha256_object(cases))

    slots_raw = manifest.get("record_slots")
    if not isinstance(slots_raw, list) or len(slots_raw) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("manifest must contain exactly 2,436 record slots")
    slots = [dict(item) for item in slots_raw if isinstance(item, Mapping)]
    if len(slots) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("manifest contains a non-object record slot")
    _require_equal(
        "manifest record_slots SHA-256",
        manifest.get("record_slots_sha256"),
        sha256_object(slots),
    )
    expected_slot_ids = [
        f"wv123-task-{task_id:03d}-agent-{agent[-1].lower()}"
        for task_id in range(EXPECTED_CASE_COUNT)
        for agent in EXPECTED_AGENT_IDS
    ]
    _require_equal(
        "manifest record slot order", [slot.get("record_slot_id") for slot in slots], expected_slot_ids
    )
    if len(set(expected_slot_ids)) != EXPECTED_RECORD_SLOT_COUNT:
        raise AssertionError("internal expected record-slot IDs are not unique")

    _validate_routes(manifest)
    by_task = {int(case["task_id"]): case for case in cases}
    for position, slot in enumerate(slots):
        task_id = position // len(EXPECTED_AGENT_IDS)
        agent_id = EXPECTED_AGENT_IDS[position % len(EXPECTED_AGENT_IDS)]
        route = EXPECTED_ROUTES[agent_id]
        case = by_task[task_id]
        expected = {
            "record_slot_id": expected_slot_ids[position],
            "task_id": task_id,
            "revision": int(case["revision"]),
            "agent_id": agent_id,
            "model": route["model"],
            "server_id": route["server_id"],
            "seed": 123000 + task_id,
        }
        _require_equal(f"manifest record slot {position}", slot, expected)
    return cases, slots


def _validate_routes(manifest: Mapping[str, Any]) -> None:
    servers = manifest.get("servers")
    if not isinstance(servers, list) or len(servers) != 3:
        raise WebArenaFullScheduleError("manifest must define exactly three servers")
    by_agent = {
        str(server.get("agent_id")): server
        for server in servers
        if isinstance(server, Mapping)
    }
    _require_equal("manifest server agent set", set(by_agent), set(EXPECTED_AGENT_IDS))
    for agent_id, expected in EXPECTED_ROUTES.items():
        server = by_agent[agent_id]
        observed = {
            "server_id": server.get("server_id"),
            "ssh_host": server.get("host"),
            "ssh_user": server.get("ssh_user"),
            "ssh_host_ed25519_fingerprint": server.get("ssh_ed25519_fingerprint"),
            "model": server.get("model"),
            "concurrency": 1,
        }
        # The controller public key is an execution-transport lock, not a
        # benchmark-source property, so it is deliberately absent from the
        # immutable Step 19 source manifest.
        expected_source_route = {
            key: value
            for key, value in expected.items()
            if key != "controller_ssh_public_key_fingerprint"
        }
        _require_equal(
            f"manifest route for {agent_id}", observed, expected_source_route
        )
        _require_equal(
            f"controller SSH public-key transport lock for {agent_id}",
            expected.get("controller_ssh_public_key_fingerprint"),
            EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT,
        )
        probe = server.get("openrouter_probe")
        if not isinstance(probe, Mapping):
            raise WebArenaFullScheduleError(f"{agent_id} has no OpenRouter probe")
        _require_equal(f"{agent_id} probe HTTP status", probe.get("http_status"), 200)
        _require_equal(f"{agent_id} probe response model", probe.get("response_model"), expected["model"])
        _require_equal(f"{agent_id} probe response", probe.get("exact_response"), "OK")


def _validate_task_contract_index(
    payload: Mapping[str, Any], cases: Sequence[Mapping[str, Any]]
) -> dict[int, dict[str, Any]]:
    _require_equal(
        "task contract index SHA-pinned schema",
        payload.get("schema_version"),
        "webarena_verified_task_contract_index/v1",
    )
    _require_equal("task contract count", payload.get("task_count"), EXPECTED_CASE_COUNT)
    entries = payload.get("entries")
    if not isinstance(entries, list) or len(entries) != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("task contract index must contain exactly 812 entries")
    result: dict[int, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise WebArenaFullScheduleError("task contract index contains a non-object entry")
        task_id = _int(entry.get("task_id"), "task contract task_id")
        if task_id in result:
            raise WebArenaFullScheduleError(f"duplicate task contract for task {task_id}")
        result[task_id] = dict(entry)
    _require_equal("task contract IDs", sorted(result), list(range(EXPECTED_CASE_COUNT)))
    for case in cases:
        task_id = int(case["task_id"])
        sites = case.get("sites")
        if (
            not isinstance(sites, list)
            or not sites
            or len(sites) != len(set(sites))
            or not set(sites) <= _WEBARENA_SITES
        ):
            raise WebArenaFullScheduleError(
                f"manifest task {task_id} has invalid task sites: {sites!r}"
            )
        task_id = int(case["task_id"])
        contract = result[task_id]
        _require_equal(
            f"task {task_id} revision against task contract",
            int(case["revision"]),
            contract.get("task_revision"),
        )
        artifacts = contract.get("required_run_artifacts")
        _require_equal(
            f"task {task_id} native run artifacts",
            artifacts,
            ["agent_response.json", "network.har"],
        )
    return result


def _validate_source_bundle(
    payload: Mapping[str, Any],
    *,
    source_bundle_file: Path,
    manifest_file: Path,
    cases: Sequence[Mapping[str, Any]],
) -> dict[int, dict[str, Any]]:
    del source_bundle_file
    _require_equal("source bundle schema", payload.get("schema_version"), SOURCE_BUNDLE_SCHEMA_VERSION)
    _require_equal("source bundle count", payload.get("source_count"), EXPECTED_CASE_COUNT)
    _require_equal("source bundle manifest SHA-256", payload.get("manifest_sha256"), sha256_file(manifest_file))
    sources = payload.get("sources")
    if not isinstance(sources, list) or len(sources) != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("source bundle must contain exactly 812 sources")
    result: dict[int, dict[str, Any]] = {}
    expected_case_hashes = {int(case["task_id"]): case["source_task_sha256"] for case in cases}
    for position, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise WebArenaFullScheduleError("source bundle contains a non-object source")
        task_id = _int(source.get("task_id"), "source bundle task_id")
        _require_equal(f"source bundle order at {position}", task_id, position)
        if task_id in result:
            raise WebArenaFullScheduleError(f"duplicate source bundle task {task_id}")
        expected_contract_id = f"ec_webarena_verified_{task_id}_contract_v1_0_0"
        _require_equal(f"source bundle task {task_id} domain", source.get("domain"), "webarena_verified")
        _require_equal(f"source bundle task {task_id} case ID", str(source.get("case_unit_id")), str(task_id))
        _require_equal(f"source bundle task {task_id} contract ID", source.get("contract_id"), expected_contract_id)
        draft_input = source.get("draft_input")
        if not isinstance(draft_input, Mapping):
            raise WebArenaFullScheduleError(f"source bundle task {task_id} has no draft_input")
        for field in ("case_packet_sha256", "raw_case_manifest_sha256"):
            _require_sha256(draft_input.get(field), f"source bundle task {task_id} {field}")
        # The task hash is bound through the frozen manifest and checked again in
        # the native-claim index; retaining it here makes that join explicit.
        source_copy = dict(source)
        source_copy["source_task_sha256"] = expected_case_hashes[task_id]
        result[task_id] = source_copy
    return result


def _validate_agents_config(path: Path) -> dict[str, dict[str, Any]]:
    payload = _mapping(path, "agents config")
    roles = payload.get("experimental_agents")
    if not isinstance(roles, Mapping):
        raise WebArenaFullScheduleError("agents config has no experimental_agents mapping")
    configured_map = payload.get("main_domain_agent_map")
    if not isinstance(configured_map, Mapping):
        raise WebArenaFullScheduleError("agents config has no main_domain_agent_map")
    _require_equal(
        "WebArena agent order",
        configured_map.get("webarena_verified"),
        list(EXPECTED_AGENT_IDS),
    )
    result: dict[str, dict[str, Any]] = {}
    for agent_id, route in EXPECTED_ROUTES.items():
        role = roles.get(agent_id)
        if not isinstance(role, Mapping):
            raise WebArenaFullScheduleError(f"agents config is missing {agent_id}")
        _require_equal(f"{agent_id} provider", role.get("provider"), "openrouter")
        _require_equal(f"{agent_id} model", role.get("model"), route["model"])
        _require_equal(f"{agent_id} API key env", role.get("api_key_env"), "OPENROUTER_API_KEY")
        _require_equal(f"{agent_id} temperature", role.get("temperature"), 0)
        result[agent_id] = dict(role)
    return result


def _validate_native_claim_gate(
    *,
    index: Mapping[str, Any],
    index_file: Path,
    acceptance: Mapping[str, Any],
    acceptance_file: Path,
    contracts_root: Path,
    cases: Sequence[Mapping[str, Any]],
    launch_policy: Mapping[str, Any],
) -> dict[int, dict[str, Any]]:
    del acceptance_file
    _require_equal("native claim index schema", index.get("schema_version"), NATIVE_CLAIM_INDEX_SCHEMA_VERSION)
    _require_equal("native claim index domain", index.get("domain"), "webarena_verified")
    _require_equal("native claim index benchmark version", index.get("benchmark_version"), "v1.2.3")
    _require_equal("native claim index expected count", index.get("expected_count"), EXPECTED_CASE_COUNT)
    _require_equal(
        "native claim index path scope",
        index.get("path_scope"),
        "repository_relative",
    )
    input_lock_sha256 = _require_sha256(index.get("input_lock_sha256"), "native claim input lock")
    compiler = index.get("compiler")
    if not isinstance(compiler, Mapping):
        raise WebArenaFullScheduleError("native claim index compiler block is missing")
    for field in ("id", "version", "source_path"):
        if not isinstance(compiler.get(field), str) or not str(compiler[field]).strip():
            raise WebArenaFullScheduleError(f"native claim compiler.{field} is missing")
    _require_sha256(compiler.get("source_sha256"), "native claim compiler source hash")
    waiver_mode = launch_policy.get("basis") == "operator_machine_only_waiver"
    _require_exact_812_counts(
        index.get("counts"),
        "native claim index",
        human_signed_expected=0 if waiver_mode else EXPECTED_CASE_COUNT,
    )

    index_cases = index.get("cases")
    if not isinstance(index_cases, list) or len(index_cases) != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("native claim index must contain exactly 812 cases")
    result: dict[int, dict[str, Any]] = {}
    manifest_cases = {int(case["task_id"]): case for case in cases}
    for position, raw in enumerate(index_cases):
        if not isinstance(raw, Mapping):
            raise WebArenaFullScheduleError("native claim index contains a non-object case")
        item = dict(raw)
        task_id = _int(item.get("task_id"), "native claim task_id")
        _require_equal(f"native claim case order {position}", task_id, position)
        if task_id in result:
            raise WebArenaFullScheduleError(f"duplicate native claim task {task_id}")
        case = manifest_cases[task_id]
        _require_equal(f"native claim task {task_id} domain", item.get("domain"), "webarena_verified")
        _require_equal(f"native claim task {task_id} case ID", str(item.get("case_unit_id")), str(task_id))
        _require_equal(
            f"native claim task {task_id} revision",
            item.get("task_revision"),
            case.get("revision"),
        )
        _require_equal(
            f"native claim task {task_id} manifest source hash",
            item.get("manifest_source_task_sha256"),
            case.get("source_task_sha256"),
        )
        packet_task = _mapping(
            _regular_file(
                Path("experiments/case_packets/webarena_verified")
                / str(task_id)
                / "raw_case/derived/task.json",
                f"task {task_id} packet-derived task",
            ),
            f"task {task_id} packet-derived task",
        )
        packet_source_sha256 = hashlib.sha256(
            json.dumps(
                packet_task,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        _require_equal(
            f"native claim task {task_id} packet source hash",
            item.get("packet_source_task_sha256"),
            packet_source_sha256,
        )
        _require_equal(
            f"native claim task {task_id} human signoff status",
            item.get("human_signoff_status"),
            "waived_not_signed" if waiver_mode else "approved",
        )
        for field in (
            "evaluator_config_sha256",
            "native_ir_sha256",
            "draft_contract_sha256",
            "draft_checklist_sha256",
            "machine_review_sha256",
            "locked_contract_sha256",
            "locked_checklist_sha256",
        ):
            _require_sha256(item.get(field), f"native claim task {task_id} {field}")
        for path_field, hash_field in (
            ("native_ir_path", "native_ir_sha256"),
            ("draft_contract_path", "draft_contract_sha256"),
            ("draft_checklist_path", "draft_checklist_sha256"),
            ("machine_review_path", "machine_review_sha256"),
        ):
            referenced = _resolve_reference(
                item.get(path_field),
                label=f"native claim task {task_id} {path_field}",
                anchors=(index_file.parent,),
            )
            _require_equal(
                f"native claim task {task_id} {hash_field}",
                item.get(hash_field),
                sha256_file(referenced),
            )
        if waiver_mode:
            _require_equal(
                f"native claim task {task_id} formal lock basis",
                item.get("formal_lock_basis"),
                "operator_machine_only_waiver",
            )
            _require_equal(
                f"native claim task {task_id} contract review path",
                item.get("contract_review_path"),
                None,
            )
            _require_equal(
                f"native claim task {task_id} contract review hash",
                item.get("contract_review_sha256"),
                None,
            )
            policy_lock_sha256 = _require_sha256(
                item.get("policy_lock_record_sha256"),
                f"native claim task {task_id} policy lock hash",
            )
            policy_lock = _resolve_reference(
                item.get("policy_lock_record_path"),
                label=f"native claim task {task_id} policy lock path",
                anchors=(index_file.parent,),
            )
            _require_equal(
                f"native claim task {task_id} policy lock file hash",
                policy_lock_sha256,
                sha256_file(policy_lock),
            )
            _validate_case_policy_lock(
                _mapping(policy_lock, f"native claim task {task_id} policy lock"),
                task_id=task_id,
                item=item,
                launch_policy=launch_policy,
            )
        else:
            _require_sha256(
                item.get("contract_review_sha256"),
                f"native claim task {task_id} contract review hash",
            )
            contract_review = _resolve_reference(
                item.get("contract_review_path"),
                label=f"native claim task {task_id} contract review path",
                anchors=(index_file.parent,),
            )
            _require_equal(
                f"native claim task {task_id} contract review file hash",
                item.get("contract_review_sha256"),
                sha256_file(contract_review),
            )
        expected_contract_path = contracts_root / str(task_id) / "evidence_contract.json"
        referenced_contract = _resolve_reference(
            item.get("locked_contract_path"),
            label=f"native claim task {task_id} locked contract path",
            anchors=(index_file.parent,),
        )
        _require_equal(
            f"native claim task {task_id} locked contract path",
            referenced_contract.resolve(),
            expected_contract_path.resolve(),
        )
        _require_equal(
            f"native claim task {task_id} locked contract hash",
            item.get("locked_contract_sha256"),
            sha256_file(expected_contract_path),
        )
        referenced_checklist = _resolve_reference(
            item.get("locked_checklist_path"),
            label=f"native claim task {task_id} locked checklist path",
            anchors=(index_file.parent,),
        )
        _require_equal(
            f"native claim task {task_id} locked checklist hash",
            item.get("locked_checklist_sha256"),
            sha256_file(referenced_checklist),
        )
        result[task_id] = item

    _require_equal(
        "native claim launch policy input lock",
        launch_policy.get("input_lock_sha256"),
        input_lock_sha256,
    )
    return result


def _validate_operator_waiver_binding(
    *,
    index: Mapping[str, Any],
    index_file: Path,
    acceptance: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the transparent non-human launch authorization and its lock."""

    waiver_input = _resolve_reference(
        index.get("operator_waiver_input_path"),
        label="native claim operator waiver input path",
        anchors=(index_file.parent,),
    )
    waiver_input_sha256 = _require_sha256(
        index.get("operator_waiver_input_sha256"),
        "native claim operator waiver input hash",
    )
    _require_equal(
        "native claim operator waiver input file hash",
        waiver_input_sha256,
        sha256_file(waiver_input),
    )
    _validate_sha_sidecar(waiver_input)

    waiver_lock = _resolve_reference(
        index.get("operator_waiver_lock_path"),
        label="native claim operator waiver lock path",
        anchors=(index_file.parent,),
    )
    waiver_lock_sha256 = _require_sha256(
        index.get("operator_waiver_lock_sha256"),
        "native claim operator waiver lock hash",
    )
    _require_equal(
        "native claim operator waiver lock file hash",
        waiver_lock_sha256,
        sha256_file(waiver_lock),
    )
    _validate_sha_sidecar(waiver_lock)

    waiver = _mapping(waiver_input, "operator waiver")
    waiver_schema_path = _regular_file(
        "schemas/webarena_verified_operator_waiver.schema.json",
        "operator waiver schema",
    )
    try:
        jsonschema.Draft202012Validator(
            _mapping(waiver_schema_path, "operator waiver schema")
        ).validate(waiver)
    except jsonschema.ValidationError as exc:
        raise WebArenaFullScheduleError(
            f"operator waiver schema validation failed: {exc.message}"
        ) from exc
    _require_equal("operator waiver schema", waiver.get("schema_version"), "webarena_verified_operator_waiver/v1")
    _require_equal("operator waiver status", waiver.get("status"), "authorized")
    _require_equal(
        "operator waiver scope",
        waiver.get("scope"),
        "webarena_verified_v1.2.3_full_812_machine_only",
    )
    _require_equal("operator waiver authorization source", waiver.get("authorization_source"), "current_user_message")
    _require_equal("operator waiver authorized role", waiver.get("authorized_by_role"), "workspace_user_experiment_operator")
    _require_equal("operator waiver human signoff claim", waiver.get("human_signoff_claimed"), False)
    _require_equal(
        "operator waiver reviewer identity/signature claim",
        waiver.get("reviewer_identity_or_signature_claimed"),
        False,
    )
    _require_equal("operator waiver human signed count", waiver.get("human_signed"), 0)
    _require_equal("operator waiver machine validated count", waiver.get("machine_validated"), EXPECTED_CASE_COUNT)
    _require_equal("operator waiver fallback count", waiver.get("fallback_contracts"), 0)
    _require_equal("operator waiver human requirement waived", waiver.get("human_signoff_requirement_waived"), True)
    _require_equal("operator waiver formal policy lock authorization", waiver.get("formal_machine_only_policy_lock_authorized"), True)

    execution_binding = waiver.get("execution_binding")
    if not isinstance(execution_binding, Mapping):
        raise WebArenaFullScheduleError("operator waiver execution_binding is missing")
    expected_agents = [
        {
            "agent_id": agent_id,
            "model": route["model"],
            "server_id": route["server_id"],
            "ssh_host": route["ssh_host"],
            "ssh_user": route["ssh_user"],
            "ssh_host_ed25519_fingerprint": route[
                "ssh_host_ed25519_fingerprint"
            ],
        }
        for agent_id, route in EXPECTED_ROUTES.items()
    ]
    _require_equal("operator waiver execution agents", execution_binding.get("agents"), expected_agents)
    _require_equal("operator waiver reset policy", execution_binding.get("reset_policy"), "recreate_task_sites_from_digest_v1")
    _require_equal("operator waiver pilot slots", execution_binding.get("pilot_record_slots"), 24)
    _require_equal("operator waiver full slots", execution_binding.get("full_record_slots"), EXPECTED_RECORD_SLOT_COUNT)
    _require_equal("operator waiver launch order", execution_binding.get("launch_order"), "pilot_must_pass_before_full")

    input_lock_path = _resolve_reference(
        index.get("input_lock_path"),
        label="native claim input lock path",
        anchors=(index_file.parent,),
    )
    _require_equal(
        "native claim input lock file hash",
        index.get("input_lock_sha256"),
        sha256_file(input_lock_path),
    )
    input_lock = _mapping(input_lock_path, "native claim input lock")
    source_binding = waiver.get("source_binding")
    if not isinstance(source_binding, Mapping):
        raise WebArenaFullScheduleError("operator waiver source_binding is missing")
    case_artifact_fields = (
        "case_unit_id",
        "task_id",
        "task_revision",
        "native_ir_sha256",
        "draft_contract_sha256",
        "draft_checklist_sha256",
        "machine_review_sha256",
    )
    index_cases = index.get("cases")
    if not isinstance(index_cases, list):
        raise WebArenaFullScheduleError("native claim index cases are missing")
    native_case_artifacts_sha256 = sha256_object(
        [
            {field: item.get(field) for field in case_artifact_fields}
            for item in sorted(
                (item for item in index_cases if isinstance(item, Mapping)),
                key=lambda item: int(str(item.get("case_unit_id"))),
            )
        ]
    )
    expected_source_binding = {
        "official_source_sha256": input_lock.get("official_source_sha256"),
        "source_bundle_sha256": input_lock.get("source_bundle_sha256"),
        "step19_manifest_sha256": input_lock.get("step19_manifest_sha256"),
        "packet_index_sha256": input_lock.get("packet_index_sha256"),
        "packet_index_core_sha256": input_lock.get("packet_index_core_sha256"),
        "packet_index_agent_input_tree_sha256": input_lock.get(
            "packet_index_agent_input_tree_sha256"
        ),
        "native_input_lock_sha256": index.get("input_lock_sha256"),
        "native_case_inventory_sha256": input_lock.get("case_inventory_sha256"),
        "native_case_artifacts_sha256": native_case_artifacts_sha256,
        "native_machine_lock_sha256": index.get("machine_lock_sha256"),
    }
    _require_equal("operator waiver source binding", dict(source_binding), expected_source_binding)

    waiver_descriptor = acceptance.get("operator_waiver")
    if not isinstance(waiver_descriptor, Mapping):
        raise WebArenaFullScheduleError("native claim acceptance operator_waiver block is missing")
    for field, expected in {
        "status": "active",
        "input_path": index.get("operator_waiver_input_path"),
        "input_sha256": waiver_input_sha256,
        "lock_path": index.get("operator_waiver_lock_path"),
        "lock_sha256": waiver_lock_sha256,
        "requirement_waived": True,
    }.items():
        _require_equal(f"native claim acceptance operator waiver {field}", waiver_descriptor.get(field), expected)

    waiver_lock_payload = _mapping(waiver_lock, "operator waiver lock")
    _require_equal(
        "operator waiver lock schema",
        waiver_lock_payload.get("schema_version"),
        "webarena_verified_operator_waiver_lock/v1",
    )
    _require_equal("operator waiver lock status", waiver_lock_payload.get("status"), "active")
    _require_equal("operator waiver lock basis", waiver_lock_payload.get("formal_lock_basis"), "operator_machine_only_waiver")
    _require_equal("operator waiver lock input hash", waiver_lock_payload.get("waiver_input_sha256"), waiver_input_sha256)
    _require_equal("operator waiver lock human signoff claim", waiver_lock_payload.get("human_signoff_claimed"), False)

    return {
        "basis": "operator_machine_only_waiver",
        "status": "authorized_machine_only_not_human_signoff",
        "human_signoff_claimed": False,
        "human_signed_count": 0,
        "human_review_requirement_waived": True,
        "operator_waiver_path": _display_path(waiver_input),
        "operator_waiver_sha256": waiver_input_sha256,
        "operator_waiver_lock_path": _display_path(waiver_lock),
        "operator_waiver_lock_sha256": waiver_lock_sha256,
        "input_lock_sha256": str(index["input_lock_sha256"]),
    }


def _validate_case_policy_lock(
    payload: Mapping[str, Any],
    *,
    task_id: int,
    item: Mapping[str, Any],
    launch_policy: Mapping[str, Any],
) -> None:
    _require_equal(
        f"native claim task {task_id} policy lock schema",
        payload.get("schema_version"),
        "webarena_verified_native_claim_policy_lock/v1",
    )
    _require_equal(f"native claim task {task_id} policy lock status", payload.get("status"), "formal_policy_locked")
    _require_equal(f"native claim task {task_id} policy lock basis", payload.get("formal_lock_basis"), "operator_machine_only_waiver")
    _require_equal(f"native claim task {task_id} policy lock task ID", str(payload.get("task_id")), str(task_id))
    _require_equal(f"native claim task {task_id} policy lock case ID", str(payload.get("case_unit_id")), str(task_id))
    _require_equal(f"native claim task {task_id} policy lock human signoff claim", payload.get("human_signoff_claimed"), False)
    _require_equal(
        f"native claim task {task_id} policy lock waiver hash",
        payload.get("operator_waiver_input_sha256"),
        launch_policy.get("operator_waiver_sha256"),
    )
    _require_equal(
        f"native claim task {task_id} policy lock waiver-lock hash",
        payload.get("operator_waiver_lock_sha256"),
        launch_policy.get("operator_waiver_lock_sha256"),
    )
    for field, expected in {
        "reviewer_identity_or_signature_claimed": False,
        "human_signoff_requirement_waived": True,
        "human_signed": 0,
        "machine_validation_status": "accepted",
        "formal_human_locked": False,
        "formal_policy_locked": True,
    }.items():
        _require_equal(
            f"native claim task {task_id} policy lock {field}",
            payload.get(field),
            expected,
        )
    for policy_field, case_field in (
        ("input_lock_sha256", None),
        ("native_ir_sha256", "native_ir_sha256"),
        ("draft_contract_sha256", "draft_contract_sha256"),
        ("draft_checklist_sha256", "draft_checklist_sha256"),
        ("machine_review_sha256", "machine_review_sha256"),
    ):
        expected = (
            launch_policy.get("input_lock_sha256")
            if case_field is None
            else item.get(case_field)
        )
        _require_equal(
            f"native claim task {task_id} policy lock {policy_field}",
            payload.get(policy_field),
            expected,
        )


def _validate_native_claim_acceptance(
    *,
    index: Mapping[str, Any],
    index_file: Path,
    acceptance: Mapping[str, Any],
) -> dict[str, Any]:
    """Reject pending native-claim work before touching the locked tree.

    Keeping this check ahead of locked-file traversal makes a dry-run receipt
    report the actual formal blocker (for example, human signoff is pending)
    instead of a secondary missing-directory error.
    """

    _require_equal(
        "native claim acceptance schema",
        acceptance.get("schema_version"),
        NATIVE_CLAIM_ACCEPTANCE_SCHEMA_VERSION,
    )
    status = acceptance.get("status")
    waiver_mode = status == "accepted_machine_only_operator_waiver"
    if not waiver_mode:
        _require_equal("native claim acceptance status", status, "accepted")
    _require_equal(
        "native claim formal launch flag",
        acceptance.get("formal_launch_eligible"),
        True,
    )
    _require_equal(
        "native claim acceptance count",
        acceptance.get("expected_count"),
        EXPECTED_CASE_COUNT,
    )
    input_lock_sha256 = _require_sha256(
        index.get("input_lock_sha256"), "native claim input lock"
    )
    _require_equal(
        "native claim acceptance input lock",
        acceptance.get("input_lock_sha256"),
        input_lock_sha256,
    )
    _require_equal(
        "native claim acceptance index hash",
        acceptance.get("index_sha256"),
        sha256_file(index_file),
    )
    referenced_index = _resolve_reference(
        acceptance.get("index_path"),
        label="native claim acceptance index path",
        anchors=(index_file.parent,),
    )
    _require_equal(
        "native claim acceptance index path",
        referenced_index.resolve(),
        index_file.resolve(),
    )
    _require_exact_812_counts(
        acceptance.get("counts"),
        "native claim acceptance",
        human_signed_expected=0 if waiver_mode else EXPECTED_CASE_COUNT,
    )
    gates = acceptance.get("gates")
    if not isinstance(gates, Mapping):
        raise WebArenaFullScheduleError("native claim acceptance gates are missing")
    for field in _FORMAL_GATE_FIELDS:
        expected = False if waiver_mode and field == "human_signoff_complete" else True
        _require_equal(f"native claim gate {field}", gates.get(field), expected)
    if waiver_mode:
        for field in (
            "human_signoff_requirement_waived",
            "operator_waiver_valid",
            "formal_policy_locks_complete",
        ):
            _require_equal(f"native claim gate {field}", gates.get(field), True)
    signoff = acceptance.get("human_signoff")
    if not isinstance(signoff, Mapping):
        raise WebArenaFullScheduleError("native claim human_signoff block is missing")
    _require_equal(
        "native claim required signoffs",
        signoff.get("required_count"),
        EXPECTED_CASE_COUNT,
    )
    _require_equal(
        "native claim completed signoffs",
        signoff.get("signed_count"),
        0 if waiver_mode else EXPECTED_CASE_COUNT,
    )
    _require_equal(
        "native claim human signoff status",
        signoff.get("status"),
        "waived_not_signed" if waiver_mode else "complete",
    )
    if waiver_mode:
        _require_equal("native claim human signoff lock path", signoff.get("lock_path"), None)
        _require_equal("native claim human signoff lock hash", signoff.get("lock_sha256"), None)
    machine_gate = acceptance.get("machine_contract_gate")
    if not isinstance(machine_gate, Mapping):
        raise WebArenaFullScheduleError("native claim machine_contract_gate is missing")
    for field, expected in {
        "machine_locked": True,
        "machine_locked_count": EXPECTED_CASE_COUNT,
        "native_contract_count": EXPECTED_CASE_COUNT,
        "fallback_contract_count": 0,
        "formal_human_locked": not waiver_mode,
        "authorizes_formal_launch": True,
    }.items():
        _require_equal(
            f"native claim machine contract gate {field}",
            machine_gate.get(field),
            expected,
        )
    if waiver_mode:
        _require_equal(
            "native claim machine contract gate formal policy lock",
            machine_gate.get("formal_policy_locked"),
            True,
        )
    _require_equal("native claim blockers", acceptance.get("blockers"), [])
    if waiver_mode:
        return _validate_operator_waiver_binding(
            index=index,
            index_file=index_file,
            acceptance=acceptance,
        )
    return {
        "basis": "human_signoff",
        "human_signoff_claimed": True,
        "human_signed_count": EXPECTED_CASE_COUNT,
        "input_lock_sha256": input_lock_sha256,
    }


def _validate_locked_contracts(
    *,
    contracts_root: Path,
    cases: Sequence[Mapping[str, Any]],
    source_entries: Mapping[int, Mapping[str, Any]],
    claim_cases: Mapping[int, Mapping[str, Any]],
    manifest_hash: str,
    launch_policy: Mapping[str, Any],
) -> dict[int, dict[str, Any]]:
    expected_paths = {
        (contracts_root / str(task_id) / "evidence_contract.json").resolve()
        for task_id in range(EXPECTED_CASE_COUNT)
    }
    actual_paths = {
        path.resolve()
        for path in contracts_root.rglob("*.json")
        if path.is_file() and not path.is_symlink()
    }
    if actual_paths != expected_paths:
        missing = sorted(str(path) for path in expected_paths - actual_paths)[:5]
        extra = sorted(str(path) for path in actual_paths - expected_paths)[:5]
        raise WebArenaFullScheduleError(
            "locked contract tree must contain exactly 812 canonical "
            f"<task>/evidence_contract.json files; missing={missing}, extra={extra}"
        )
    if any(path.is_symlink() for path in contracts_root.rglob("*")):
        raise WebArenaFullScheduleError("locked contract tree must not contain symlinks")

    case_by_id = {int(case["task_id"]): case for case in cases}
    result: dict[int, dict[str, Any]] = {}
    seen_contract_ids: set[str] = set()
    seen_hashes: set[str] = set()
    for task_id in range(EXPECTED_CASE_COUNT):
        path = contracts_root / str(task_id) / "evidence_contract.json"
        contract = _mapping(path, f"task {task_id} locked contract")
        report = validate_object(
            "evidence_contract", contract, formal=True, raise_on_error=False
        )
        if not report.ok:
            raise WebArenaFullScheduleError(
                f"task {task_id} locked contract schema invalid: {report.to_dict()}"
            )
        _require_equal(f"task {task_id} contract schema", contract.get("schema_version"), "evidence_contract/v1")
        _require_equal(f"task {task_id} contract domain", contract.get("domain"), "webarena_verified")
        _require_equal(f"task {task_id} contract case ID", str(contract.get("case_unit_id")), str(task_id))
        _require_equal(f"task {task_id} contract task ID", str(contract.get("task_id")), str(task_id))
        _require_equal(f"task {task_id} contract status", contract.get("contract_status"), "locked")
        _require_equal(f"task {task_id} contract main eligibility", contract.get("main_result_eligible"), True)
        _require_equal(f"task {task_id} contract claim scope", contract.get("claim_scope"), "native_aligned")
        _require_equal(
            f"task {task_id} contract ID",
            contract.get("contract_id"),
            source_entries[task_id].get("contract_id"),
        )
        _require_equal(
            f"task {task_id} contract manifest hash",
            contract.get("manifest_hash"),
            manifest_hash,
        )
        if not isinstance(contract.get("locked_at"), str) or not contract["locked_at"]:
            raise WebArenaFullScheduleError(f"task {task_id} contract has no locked_at")
        if not isinstance(contract.get("locked_by"), str) or not contract["locked_by"]:
            raise WebArenaFullScheduleError(f"task {task_id} contract has no locked_by")
        if launch_policy.get("basis") == "operator_machine_only_waiver":
            _require_equal(
                f"task {task_id} native claim formal lock basis",
                claim_cases[task_id].get("formal_lock_basis"),
                "operator_machine_only_waiver",
            )
            _require_equal(
                f"task {task_id} machine-only waiver lock actor",
                contract.get("locked_by"),
                "operator-machine-only-waiver-no-human-review",
            )
        artifacts = contract.get("required_artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise WebArenaFullScheduleError(
                f"task {task_id} locked contract required_artifacts is empty"
            )
        requirement_ids = [
            str(item.get("contract_requirement_id") or "")
            for item in artifacts
            if isinstance(item, Mapping)
        ]
        if len(requirement_ids) != len(artifacts) or any(not item for item in requirement_ids):
            raise WebArenaFullScheduleError(
                f"task {task_id} locked contract has an invalid artifact requirement"
            )
        if len(requirement_ids) != len(set(requirement_ids)):
            raise WebArenaFullScheduleError(
                f"task {task_id} locked contract has duplicate artifact requirements"
            )
        expected_hash = contract_content_hash(contract)
        _require_equal(f"task {task_id} contract hash", contract.get("contract_hash"), expected_hash)
        _require_equal(f"task {task_id} canonical hash", contract.get("canonical_hash"), expected_hash)
        _require_equal(
            f"task {task_id} contract file hash against native claim index",
            sha256_file(path),
            claim_cases[task_id].get("locked_contract_sha256"),
        )
        # The revision/source binding is independently frozen in the Step 19
        # case and native-claim index, and must remain identical here.
        _require_equal(
            f"task {task_id} native claim revision",
            claim_cases[task_id].get("task_revision"),
            case_by_id[task_id].get("revision"),
        )
        contract_id = str(contract["contract_id"])
        contract_hash = str(contract["contract_hash"])
        if contract_id in seen_contract_ids:
            raise WebArenaFullScheduleError(f"duplicate locked contract ID: {contract_id}")
        if contract_hash in seen_hashes:
            raise WebArenaFullScheduleError(
                f"duplicate locked contract content hash: {contract_hash}"
            )
        seen_contract_ids.add(contract_id)
        seen_hashes.add(contract_hash)
        result[task_id] = contract
    return result


def _build_jobs(
    *,
    manifest: Mapping[str, Any],
    manifest_hash: str,
    source_bundle_hash: str,
    native_claim_index_hash: str,
    native_claim_acceptance_hash: str,
    cases: Sequence[Mapping[str, Any]],
    slots: Sequence[Mapping[str, Any]],
    source_entries: Mapping[int, Mapping[str, Any]],
    claim_cases: Mapping[int, Mapping[str, Any]],
    task_contracts: Mapping[int, Mapping[str, Any]],
    contracts: Mapping[int, Mapping[str, Any]],
    role_configs: Mapping[str, Mapping[str, Any]],
    site_lock_sha256: str,
    launch_policy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    case_by_id = {int(case["task_id"]): case for case in cases}
    case_ids = [str(case["task_id"]) for case in cases]
    deterministic_selection = {
        "hash_function": "sha256",
        "hash_salt_hash": sha256_object("webarena-verified-v1.2.3-full-812"),
        "eligible_case_unit_set_hash": sha256_object(sorted(case_ids, key=int)),
        "excluded_smoke_case_units": [],
        "smoke_exclusion_hash": sha256_object([]),
        "case_selection_order_hash": sha256_object(case_ids),
        "bootstrap_seed": 123000,
        "bootstrap_resample_count": 1000,
        "audit_sample_seed": 123456,
        "rerun_subset_selection_rule": (
            "no outcome-based rerun; exact frozen Step 19 record slot order"
        ),
    }
    jobs: list[dict[str, Any]] = []
    for slot in slots:
        task_id = int(slot["task_id"])
        agent_id = str(slot["agent_id"])
        route = EXPECTED_ROUTES[agent_id]
        contract = contracts[task_id]
        task_contract = task_contracts[task_id]
        record_slot_id = str(slot["record_slot_id"])
        job = {
            "schema_version": "job/v1",
            "job_id": f"full-webarena_verified-{task_id:03d}-agent_{agent_id[-1].lower()}",
            "domain": "webarena_verified",
            "domain_display_name": "WebArena-Verified",
            "benchmark_name": "WebArena-Verified",
            "case_unit_id": str(task_id),
            "task_id": str(task_id),
            "task_revision": int(case_by_id[task_id]["revision"]),
            "task_sites": list(case_by_id[task_id]["sites"]),
            "reset_policy": "recreate_task_sites_from_digest_v1",
            "reset_receipt_relative_path": "reset_receipt.json",
            "record_slot_id": record_slot_id,
            "run_id": f"run-{record_slot_id}",
            "attempt_id": f"attempt-{record_slot_id}-001",
            "final_attempt": True,
            "seed": int(slot["seed"]),
            "agent_id": agent_id,
            "requested_model": route["model"],
            "execution_target": dict(route),
            "phase": "full",
            "experiment_type": "appendix",
            "priority": "P0",
            "adapter_module": "evidence_system.adapters.webarena_verified",
            "agent_config_hash": sha256_object(role_configs[agent_id]),
            "benchmark_config_hash": sha256_object(
                formal_benchmark_config(
                    route=route,
                    common_run_policy=manifest["common_run_policy"],
                    source_bundle_sha256=source_bundle_hash,
                    native_claim_index_sha256=native_claim_index_hash,
                    site_lock_sha256=site_lock_sha256,
                )
            ),
            "manifest_hash": manifest_hash,
            "evidence_contract_id": contract["contract_id"],
            "evidence_contract_version": contract["contract_version"],
            "evidence_contract_hash": contract["contract_hash"],
            "contract_id": contract["contract_id"],
            "contract_version": contract["contract_version"],
            "contract_hash": contract["contract_hash"],
            "taxonomy_version": contract["taxonomy_version"],
            "artifact_contract": {
                "required_artifacts": list(contract["required_artifacts"]),
                "native_run_artifacts": list(task_contract["required_run_artifacts"]),
            },
            "deterministic_selection": deterministic_selection,
            "result_namespace": RESULT_NAMESPACE,
            "artifact_retention_mode": ARTIFACT_RETENTION_MODE,
        }
        if launch_policy.get("basis") == "operator_machine_only_waiver":
            draft_input = source_entries[task_id].get("draft_input")
            if not isinstance(draft_input, Mapping):
                raise WebArenaFullScheduleError(
                    f"source bundle task {task_id} has no draft_input for policy lock"
                )
            job["formal_policy_lock"] = {
                "schema_version": "webarena_verified_job_formal_policy_lock/v1",
                "basis": "operator_machine_only_waiver",
                "operator_waiver_path": launch_policy["operator_waiver_path"],
                "operator_waiver_sha256": launch_policy["operator_waiver_sha256"],
                "human_signoff_claimed": False,
                "human_signed_count": 0,
                "step19_manifest_sha256": manifest_hash,
                "source_bundle_sha256": source_bundle_hash,
                "native_claim_index_sha256": native_claim_index_hash,
                "native_claim_acceptance_sha256": native_claim_acceptance_hash,
                "case_packet_sha256": _require_sha256(
                    draft_input.get("case_packet_sha256"),
                    f"source bundle task {task_id} case packet hash",
                ),
                "locked_contract_file_sha256": _require_sha256(
                    claim_cases[task_id].get("locked_contract_sha256"),
                    f"native claim task {task_id} locked contract file hash",
                ),
                "model": route["model"],
                "server_id": route["server_id"],
                "reset_policy": "recreate_task_sites_from_digest_v1",
            }
        report = validate_object("job", job, formal=True, raise_on_error=False)
        if not report.ok:
            raise WebArenaFullScheduleError(
                f"generated job {record_slot_id} failed schema validation: {report.to_dict()}"
            )
        jobs.append(job)
    return jobs


def formal_benchmark_config(
    *,
    route: Mapping[str, Any],
    common_run_policy: Mapping[str, Any],
    source_bundle_sha256: str,
    native_claim_index_sha256: str,
    site_lock_sha256: str,
) -> dict[str, Any]:
    """Return the one canonical runtime config hashed by both plan and executor."""

    runner_root = (
        "/opt/webarena-runner/"
        "dce04686a56253aefba7b18a4fa0937cf1dc987b/source"
    )
    return {
        "schema_version": "webarena_verified_formal_runtime_config/v1",
        "route": dict(route),
        "remote_workdir": DEFAULT_REMOTE_WORKDIR,
        "install_dir": runner_root,
        "python_bin": f"{runner_root}/.venv/bin/python",
        "official_evaluator_config": (
            "/opt/webarena-verified/v1.2.3/runtime/"
            "webarena_verified_runtime_urls.json"
        ),
        "max_steps": 30,
        "environment": {
            "health_urls": {
                "shopping": "http://127.0.0.1:7770",
                "shopping_admin": "http://127.0.0.1:7780/admin",
                "reddit": "http://127.0.0.1:9999",
                "gitlab": "http://127.0.0.1:8023",
                "wikipedia": (
                    "http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/"
                    "A/User:The_other_Kiwix_guy/Landing"
                ),
                "map": "http://127.0.0.1:3030",
            },
            "max_steps": 30,
        },
        "site_controller": {
            "site_lock_path": DEFAULT_SITE_LOCK.as_posix(),
            "site_lock_sha256": site_lock_sha256,
            "ssh_host_fingerprint": route[
                "ssh_host_ed25519_fingerprint"
            ],
            "reset_policy": "recreate_task_sites_from_digest_v1",
            "reset_receipt_relative_path": "reset_receipt.json",
        },
        "common_run_policy": dict(common_run_policy),
        "locks": {
            "task_contract_index_sha256": EXPECTED_TASK_CONTRACT_INDEX_SHA256,
            "source_bundle_sha256": source_bundle_sha256,
            "native_claim_index_sha256": native_claim_index_sha256,
        },
    }


def _validate_planned_jobs(
    jobs: Sequence[Mapping[str, Any]], *, slots: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if len(jobs) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("planned job count is not exactly 2,436")
    slot_ids = [str(job.get("record_slot_id")) for job in jobs]
    requested_slot_ids = [str(slot.get("record_slot_id")) for slot in slots]
    _require_equal("planned record-slot order", slot_ids, requested_slot_ids)
    if len(set(slot_ids)) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("planned record-slot IDs are not unique")
    job_ids = [str(job.get("job_id")) for job in jobs]
    if len(set(job_ids)) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("planned job IDs are not unique")

    requested_per_agent = Counter(str(slot["agent_id"]) for slot in slots)
    planned_per_agent = Counter(str(job["agent_id"]) for job in jobs)
    expected_per_agent = Counter({agent: EXPECTED_CASE_COUNT for agent in EXPECTED_AGENT_IDS})
    _require_equal("requested jobs per agent", requested_per_agent, expected_per_agent)
    _require_equal("planned jobs per agent", planned_per_agent, expected_per_agent)

    per_server = Counter(str(job["execution_target"]["server_id"]) for job in jobs)
    expected_per_server = Counter(
        {route["server_id"]: EXPECTED_CASE_COUNT for route in EXPECTED_ROUTES.values()}
    )
    _require_equal("planned jobs per server", per_server, expected_per_server)
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    policy_lock_hashes: set[str] = set()
    for job in jobs:
        grouped[int(job["task_id"])].append(job)
        agent_id = str(job["agent_id"])
        _require_equal(
            f"planned route for {job['record_slot_id']}",
            job.get("execution_target"),
            EXPECTED_ROUTES[agent_id],
        )
        _require_equal(
            f"planned model for {job['record_slot_id']}",
            job.get("requested_model"),
            EXPECTED_ROUTES[agent_id]["model"],
        )
        _require_equal(
            (
                "planned controller SSH public-key transport lock for "
                f"{job['record_slot_id']}"
            ),
            dict(job.get("execution_target") or {}).get(
                "controller_ssh_public_key_fingerprint"
            ),
            EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT,
        )
        required = job.get("artifact_contract", {}).get("required_artifacts")
        if not isinstance(required, list) or not required:
            raise WebArenaFullScheduleError(
                f"planned job {job['record_slot_id']} has an empty artifact contract"
            )
        _require_equal(
            f"planned reset policy for {job['record_slot_id']}",
            job.get("reset_policy"),
            "recreate_task_sites_from_digest_v1",
        )
        _require_equal(
            f"planned reset receipt destination for {job['record_slot_id']}",
            job.get("reset_receipt_relative_path"),
            "reset_receipt.json",
        )
        _require_equal(
            f"planned artifact retention for {job['record_slot_id']}",
            job.get("artifact_retention_mode"),
            ARTIFACT_RETENTION_MODE,
        )
        sites = job.get("task_sites")
        if (
            not isinstance(sites, list)
            or not sites
            or len(sites) != len(set(sites))
            or not set(sites) <= _WEBARENA_SITES
        ):
            raise WebArenaFullScheduleError(
                f"planned job {job['record_slot_id']} has invalid task sites"
            )
        formal_policy_lock = job.get("formal_policy_lock")
        if formal_policy_lock is not None:
            if not isinstance(formal_policy_lock, Mapping):
                raise WebArenaFullScheduleError(
                    f"planned job {job['record_slot_id']} has invalid formal policy lock"
                )
            expected_policy_fields = {
                "schema_version": "webarena_verified_job_formal_policy_lock/v1",
                "basis": "operator_machine_only_waiver",
                "human_signoff_claimed": False,
                "human_signed_count": 0,
                "model": EXPECTED_ROUTES[agent_id]["model"],
                "server_id": EXPECTED_ROUTES[agent_id]["server_id"],
                "reset_policy": "recreate_task_sites_from_digest_v1",
            }
            for field, expected in expected_policy_fields.items():
                _require_equal(
                    f"planned policy lock {job['record_slot_id']} {field}",
                    formal_policy_lock.get(field),
                    expected,
                )
            policy_lock_hashes.add(
                _require_sha256(
                    formal_policy_lock.get("operator_waiver_sha256"),
                    f"planned policy lock {job['record_slot_id']} waiver hash",
                )
            )
    _require_equal("planned task set", sorted(grouped), list(range(EXPECTED_CASE_COUNT)))
    for task_id, task_jobs in grouped.items():
        _require_equal(
            f"task {task_id} paired agent order",
            [job["agent_id"] for job in task_jobs],
            list(EXPECTED_AGENT_IDS),
        )
        _require_equal(
            f"task {task_id} paired seed",
            {int(job["seed"]) for job in task_jobs},
            {123000 + task_id},
        )
    if policy_lock_hashes and (
        len(policy_lock_hashes) != 1
        or any(job.get("formal_policy_lock") is None for job in jobs)
    ):
        raise WebArenaFullScheduleError(
            "formal policy lock must bind one waiver hash across all 2,436 jobs"
        )
    return {
        "requested_per_agent": dict(requested_per_agent),
        "planned_per_agent": dict(planned_per_agent),
        "planned_per_server": dict(per_server),
        "unique_record_slot_ids": len(set(slot_ids)),
        "operator_waiver_sha256": (
            next(iter(policy_lock_hashes)) if policy_lock_hashes else None
        ),
    }


def _require_exact_812_counts(
    value: Any,
    label: str,
    *,
    human_signed_expected: int = EXPECTED_CASE_COUNT,
) -> None:
    if not isinstance(value, Mapping):
        raise WebArenaFullScheduleError(f"{label} counts are missing")
    for field in _LOCKED_COUNT_FIELDS:
        expected = (
            human_signed_expected if field == "human_signed" else EXPECTED_CASE_COUNT
        )
        _require_equal(f"{label} counts.{field}", value.get(field), expected)


def _validate_sha_sidecar(path: Path) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    if not sidecar.is_file() or sidecar.is_symlink():
        raise WebArenaFullScheduleError(f"SHA-256 sidecar is missing or unsafe: {sidecar}")
    expected = f"{sha256_file(path)}  {path.name}\n"
    _require_equal(f"SHA-256 sidecar for {path.name}", sidecar.read_text(encoding="utf-8"), expected)


def _write_sha_sidecar(path: Path) -> None:
    path.with_name(path.name + ".sha256").write_text(
        f"{sha256_file(path)}  {path.name}\n", encoding="utf-8"
    )


def _resolve_reference(
    value: Any, *, label: str, anchors: Sequence[Path]
) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise WebArenaFullScheduleError(f"{label} is missing")
    raw = Path(value)
    if raw.is_absolute():
        candidates = (raw,)
    else:
        candidates = (repo_root() / raw, *(anchor / raw for anchor in anchors))
    existing = [path for path in candidates if path.is_file() and not path.is_symlink()]
    if not existing:
        raise WebArenaFullScheduleError(f"{label} does not resolve to a regular file: {value}")
    resolved = {path.resolve() for path in existing}
    if len(resolved) != 1:
        raise WebArenaFullScheduleError(f"{label} is ambiguous: {value}")
    return next(iter(resolved))


def _regular_file(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path)
    if not resolved.is_file() or resolved.is_symlink():
        raise WebArenaFullScheduleError(f"{label} is missing or unsafe: {resolved}")
    return resolved


def _directory(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path)
    if not resolved.is_dir() or resolved.is_symlink():
        raise WebArenaFullScheduleError(f"{label} is missing or unsafe: {resolved}")
    return resolved


def _mapping(path: Path, label: str) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        raise WebArenaFullScheduleError(f"{label} must contain a mapping: {path}")
    return dict(payload)


def _int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise WebArenaFullScheduleError(f"{label} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise WebArenaFullScheduleError(f"{label} must be an integer") from exc


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise WebArenaFullScheduleError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise WebArenaFullScheduleError(
            f"{label} mismatch: expected={expected!r}, actual={actual!r}"
        )


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
