"""Materialize the execution-bound two-VPS AgentDojo remaining-849 controls.

This command is deliberately local-only.  It converts the immutable campaign
lock into one create-once job plan, namespace receipt, and A/B/C stage
authorization per VPS.  Network deployment and episode execution remain
separate operations.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from evidence_system.adapters.agentdojo_runtime_control import (
    agentdojo_model_config_sha256,
    execution_runtime_snapshot,
    job_identity_sha256,
    load_runtime_policy,
)
from evidence_system.adapters.runtime import (
    formal_job_binding_sha256,
    formal_job_file_sha256,
)
from evidence_system.contracts.agentdojo_remaining_849_execution import (
    EXPECTED_AGENTS,
    EXPECTED_SHARD_JOB_COUNTS,
    verify_remaining_849_execution_lock,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path


SCHEMA_VERSION = "agentdojo_remaining_849_remote_deployment_manifest/v1"
PLAN_SCHEMA_VERSION = "agentdojo_remaining_849_remote_plan_index/v1"
NAMESPACE_SCHEMA_VERSION = "agentdojo_formal_execution_namespace_init_receipt/v2"
AUTHORIZATION_SCHEMA_VERSION = "agentdojo_formal_stage_authorization/v1"
DEFAULT_CAMPAIGN_LOCK = Path(
    "experiments/agentdojo_full_v1.2.2_direct/remaining_849/execution_lock.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "experiments/agentdojo_full_v1.2.2_direct/remaining_849/remote"
)
DEFAULT_AGENTS_CONFIG = Path("configs/agents.yaml")
DEFAULT_FORMAL_WALL_CLOCK_TIMEOUT_SECONDS = 7_200
DEFAULT_KILL_GRACE_SECONDS = 30
WORKERS_BY_AGENT = {"Agent A": 8, "Agent B": 4, "Agent C": 4}
STAGE_ID_BY_AGENT = {
    "Agent A": "agent-a",
    "Agent B": "agent-b",
    "Agent C": "agent-c",
}
REMOTE_REPO_ROOT = "/srv/agentdojo-full/repo"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_identical_or_new(path: Path, payload: Mapping[str, Any]) -> bool:
    encoded = _canonical_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ContractLifecycleError(f"remote campaign control is symlinked: {path}")
    if path.exists():
        if not path.is_file() or path.read_bytes() != encoded:
            raise ContractLifecycleError(
                f"remote campaign control already exists with different bytes: {path}"
            )
        return False
    path.write_bytes(encoded)
    return True


def _load_json(path: str | Path, label: str) -> dict[str, Any]:
    candidate = resolve_repo_path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise ContractLifecycleError(f"{label} is missing or symlinked")
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractLifecycleError(f"{label} is not a JSON object")
    return payload


def _infra_benchmark(path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    infra = _load_json(path, "remaining-849 infra overlay")
    machines = list(infra.get("machines") or [])
    if len(machines) != 1 or not isinstance(machines[0], Mapping):
        raise ContractLifecycleError("remaining-849 infra must contain one machine")
    machine = dict(machines[0])
    benchmark = dict(dict(machine.get("benchmarks") or {}).get("AgentDojo") or {})
    required = (
        "runtime_state_root",
        "remote_raw_root",
        "blind_aggregate_root",
        "failed_attempt_archive_root",
    )
    if any(not str(benchmark.get(field) or "").startswith("/") for field in required):
        raise ContractLifecycleError("remaining-849 infra sealed roots are incomplete")
    return machine, benchmark


def _agent_model_hashes(agents_path: str | Path) -> dict[str, str]:
    candidate = resolve_repo_path(agents_path)
    payload = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    agents = dict(dict(payload or {}).get("experimental_agents") or {})
    result: dict[str, str] = {}
    for agent_id in EXPECTED_AGENTS:
        row = dict(agents.get(agent_id) or {})
        try:
            result[agent_id] = agentdojo_model_config_sha256(
                agent_id=agent_id,
                provider=str(row["provider"]),
                model_id=str(row["model"]),
                temperature=float(row["temperature"]),
                max_tokens=int(row["max_tokens"]),
                timeout_seconds=int(row["timeout_seconds"]),
                retry=int(row["retry"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractLifecycleError(
                f"AgentDojo model config is incomplete for {agent_id}"
            ) from exc
    return result


def _execution_policy_sha256(lock_payload: Mapping[str, Any]) -> str:
    definition = dict(lock_payload.get("definition") or {})
    return sha256_object(
        {
            "schema_version": "agentdojo_remaining_849_execution_policy/v1",
            "campaign_lock_definition_sha256": lock_payload.get("definition_sha256"),
            "job_plan_sha256": definition.get("job_plan_sha256"),
            "runtime_sha256": definition.get("runtime_sha256"),
            "monitoring_policy_sha256": definition.get("monitoring_policy_sha256"),
            "sealed_evidence_policy_sha256": definition.get(
                "sealed_evidence_policy_sha256"
            ),
            "continue_on_isolated_job_error": True,
            "consecutive_terminal_case_failure_pause_threshold": 4,
            "cross_agent_model_overlap_forbidden": True,
        }
    )


def _runtime_binding_for_shard(
    campaign_definition: Mapping[str, Any], shard_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime = dict(campaign_definition.get("runtime") or {})
    policies = {
        str(row.get("shard_id")): dict(row)
        for row in list(runtime.get("host_conservative_policies") or [])
        if isinstance(row, Mapping)
    }
    infras = {
        str(row.get("shard_id")): dict(row)
        for row in list(runtime.get("infra") or [])
        if isinstance(row, Mapping)
    }
    if shard_id not in policies or shard_id not in infras:
        raise ContractLifecycleError(f"campaign runtime binding is missing: {shard_id}")
    return policies[shard_id], infras[shard_id]


def _remote_control_path(shard_id: str, local_path: Path) -> str:
    return f"{REMOTE_REPO_ROOT}/experiments/agentdojo_full_v1.2.2_direct/remaining_849/remote/{shard_id}/{local_path.name}"


def materialize_remaining_849_remote_controls(
    *,
    campaign_lock_path: str | Path = DEFAULT_CAMPAIGN_LOCK,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Publish exact local controls for both shards and all three agent lanes."""

    verified = verify_remaining_849_execution_lock(campaign_lock_path)
    lock_payload = _load_json(verified.lock_path, "remaining-849 execution lock")
    manifest = verified.manifest
    definition = dict(manifest.get("definition") or {})
    entries = list(dict(definition.get("job_plan") or {}).get("entries") or [])
    if len(entries) != 2_547:
        raise ContractLifecycleError("remaining-849 campaign job denominator differs")
    output = resolve_repo_path(output_root)
    # Use the immutable campaign-lock timestamp by default so an interrupted
    # controller can re-run this materializer and verify identical bytes.
    timestamp = created_at or str(lock_payload.get("locked_at") or _utc_now())
    model_hashes = _agent_model_hashes(agents_config_path)
    execution_policy_sha = _execution_policy_sha256(lock_payload)
    runtime_snapshot = execution_runtime_snapshot()
    host_manifests: list[dict[str, Any]] = []

    for shard_id in ("vps1", "vps2"):
        shard_root = output / shard_id
        jobs_root = shard_root / "jobs"
        shard_lock_path = shard_root / "execution_lock.json"
        _write_identical_or_new(shard_lock_path, lock_payload)
        if sha256_file(shard_lock_path) != verified.lock_sha256:
            raise ContractLifecycleError("shard execution-lock bytes differ")
        policy_binding, infra_binding = _runtime_binding_for_shard(definition, shard_id)
        policy_path = resolve_repo_path(str(policy_binding["path"]))
        policy_payload = _load_json(policy_path, f"{shard_id} host policy")
        parsed_policy = load_runtime_policy(
            policy_payload,
            expected_semantic_sha256=str(policy_binding["semantic_sha256"]),
        )
        if sha256_file(policy_path) != str(policy_binding["file_sha256"]):
            raise ContractLifecycleError(f"{shard_id} host policy file hash differs")
        infra_path = resolve_repo_path(str(infra_binding["path"]))
        if sha256_file(infra_path) != str(infra_binding["file_sha256"]):
            raise ContractLifecycleError(f"{shard_id} infra file hash differs")
        machine, benchmark = _infra_benchmark(infra_path)

        shard_entries = [
            dict(row)
            for row in entries
            if isinstance(row, Mapping) and row.get("shard_id") == shard_id
        ]
        if len(shard_entries) != EXPECTED_SHARD_JOB_COUNTS[shard_id]:
            raise ContractLifecycleError(f"{shard_id} campaign denominator differs")
        shard_entries.sort(
            key=lambda row: (EXPECTED_AGENTS.index(str(row["agent_id"])), int(row["ordinal"]))
        )
        plan_entries: list[dict[str, Any]] = []
        jobs_by_agent: dict[str, list[tuple[dict[str, Any], Path]]] = {
            agent: [] for agent in EXPECTED_AGENTS
        }
        for row in shard_entries:
            agent_id = str(row["agent_id"])
            job = dict(row["job_payload"])
            job.update(
                {
                    "result_namespace": (
                        f"agentdojo_remaining_849_v1.2.2_direct_{shard_id}"
                    ),
                    "execution_lock_sha256": verified.lock_sha256,
                    "execution_policy_sha256": execution_policy_sha,
                    "openrouter_runtime_policy": policy_payload,
                    "openrouter_runtime_policy_sha256": parsed_policy.semantic_sha256,
                    "openrouter_runtime_policy_file_sha256": sha256_file(policy_path),
                    "force_rerun": False,
                    "rerun_completed": False,
                    "formal_wall_clock_timeout_seconds": (
                        DEFAULT_FORMAL_WALL_CLOCK_TIMEOUT_SECONDS
                    ),
                }
            )
            job_path = jobs_root / f"{job['job_id']}.json"
            _write_identical_or_new(job_path, job)
            if sha256_file(job_path) != formal_job_file_sha256(job):
                raise ContractLifecycleError("materialized job bytes are noncanonical")
            binding = formal_job_binding_sha256(job)
            identity = job_identity_sha256(job)
            plan_entries.append(
                {
                    "ordinal": len(plan_entries),
                    "shard_id": shard_id,
                    "agent_id": agent_id,
                    "job_identity_sha256": identity,
                    "job_binding_sha256": binding,
                    "path": (
                        f"{REMOTE_REPO_ROOT}/experiments/agentdojo_full_v1.2.2_direct/"
                        f"remaining_849/remote/{shard_id}/jobs/{job_path.name}"
                    ),
                    "sha256": sha256_file(job_path),
                }
            )
            jobs_by_agent[agent_id].append((job, job_path))

        plan = {
            "schema_version": PLAN_SCHEMA_VERSION,
            "created_at": timestamp,
            "shard_id": shard_id,
            "machine_id": str(machine["machine_id"]),
            "execution_lock_sha256": verified.lock_sha256,
            "execution_policy_sha256": execution_policy_sha,
            "job_count": len(plan_entries),
            "record_slot_count": len(plan_entries),
            "agent_batch_order": list(EXPECTED_AGENTS),
            "entries_sha256": sha256_object(plan_entries),
            "entries": plan_entries,
        }
        plan_path = shard_root / "plan_index.json"
        _write_identical_or_new(plan_path, plan)
        plan_sha = sha256_file(plan_path)

        namespace_payload = {
            "schema_version": NAMESPACE_SCHEMA_VERSION,
            "status": "initialized_empty_namespaces",
            "created_at": timestamp,
            "definition": {
                "execution_lock": {
                    "path": _remote_control_path(shard_id, Path("execution_lock.json")),
                    "sha256": verified.lock_sha256,
                },
                "execution_policy_sha256": execution_policy_sha,
                "plan_index": {
                    "path": _remote_control_path(shard_id, plan_path),
                    "sha256": plan_sha,
                },
                "runtime_state_root": str(benchmark["runtime_state_root"]),
                "remote_raw_root": str(benchmark["remote_raw_root"]),
                "blind_aggregate_root": str(benchmark["blind_aggregate_root"]),
                "failed_attempt_archive_root": str(
                    benchmark["failed_attempt_archive_root"]
                ),
                "runtime_sync_after_init_forbidden": True,
                "initial_remote_namespace_state": "empty",
            },
        }
        namespace_path = shard_root / "namespace_init_receipt.json"
        _write_identical_or_new(namespace_path, namespace_payload)
        namespace_sha = sha256_file(namespace_path)
        namespace_remote_path = (
            f"{str(benchmark['runtime_state_root']).rstrip('/')}/formal-control/"
            f"namespace-init/{namespace_sha}.json"
        )

        authorization_rows: list[dict[str, Any]] = []
        for stage_index, agent_id in enumerate(EXPECTED_AGENTS):
            jobs = jobs_by_agent[agent_id]
            job_payloads = [item[0] for item in jobs]
            job_paths = [item[1] for item in jobs]
            bindings = [formal_job_binding_sha256(job) for job in job_payloads]
            file_hashes = [sha256_file(path) for path in job_paths]
            slot_ids = [str(job["record_slot_id"]) for job in job_payloads]
            stage_id = STAGE_ID_BY_AGENT[agent_id]
            session_id = f"session-{shard_id}-{stage_id}-{verified.lock_sha256[:16]}"
            authorization = {
                "schema_version": AUTHORIZATION_SCHEMA_VERSION,
                "status": "authorized",
                "created_at": timestamp,
                "execution_lock_sha256": verified.lock_sha256,
                "execution_policy_sha256": execution_policy_sha,
                "plan_index_sha256": plan_sha,
                "namespace_init_receipt": {
                    "path": namespace_remote_path,
                    "sha256": namespace_sha,
                },
                "stage_id": stage_id,
                "session_id": session_id,
                "stage_order_index": stage_index,
                "locked_workers": WORKERS_BY_AGENT[agent_id],
                "workers": WORKERS_BY_AGENT[agent_id],
                "record_slot_count": len(job_payloads),
                "record_slot_ids_sha256": sha256_object(slot_ids),
                "allowed_job_binding_sha256": bindings,
                "allowed_job_bindings_sha256": sha256_object(bindings),
                "allowed_job_file_sha256": file_hashes,
                "allowed_job_files_sha256": sha256_object(file_hashes),
                "allowed_model_config_sha256": [model_hashes[agent_id]],
                "allowed_model_configs_sha256": sha256_object(
                    [model_hashes[agent_id]]
                ),
                "runtime_policy_semantic_sha256": parsed_policy.semantic_sha256,
                "runtime_policy_file_sha256": sha256_file(policy_path),
                "runtime_infra_file_sha256": sha256_file(infra_path),
                "runtime_state_root": str(benchmark["runtime_state_root"]),
                "runtime_snapshot": runtime_snapshot,
                "previous_health_receipt": None,
                "formal_wall_clock_timeout_seconds": (
                    DEFAULT_FORMAL_WALL_CLOCK_TIMEOUT_SECONDS
                ),
                "kill_grace_seconds": DEFAULT_KILL_GRACE_SECONDS,
                "blind_only": True,
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
            }
            auth_path = shard_root / f"stage_authorization.{stage_id}.json"
            _write_identical_or_new(auth_path, authorization)
            auth_sha = sha256_file(auth_path)
            authorization_rows.append(
                {
                    "agent_id": agent_id,
                    "stage_id": stage_id,
                    "session_id": session_id,
                    "workers": WORKERS_BY_AGENT[agent_id],
                    "record_slot_count": len(job_payloads),
                    "local_path": str(auth_path),
                    "remote_path": (
                        f"{str(benchmark['runtime_state_root']).rstrip('/')}/formal-control/"
                        f"stage-authorizations/{stage_id}-{session_id}.json"
                    ),
                    "sha256": auth_sha,
                }
            )

        host_manifest = {
            "shard_id": shard_id,
            "machine_id": str(machine["machine_id"]),
            "job_count": len(plan_entries),
            "jobs_root": str(jobs_root),
            "plan_index": {"path": str(plan_path), "sha256": plan_sha},
            "namespace_init_receipt": {
                "local_path": str(namespace_path),
                "remote_path": namespace_remote_path,
                "sha256": namespace_sha,
            },
            "runtime_policy": {
                "path": str(policy_path),
                "semantic_sha256": parsed_policy.semantic_sha256,
                "file_sha256": sha256_file(policy_path),
            },
            "runtime_infra": {
                "path": str(infra_path),
                "file_sha256": sha256_file(infra_path),
            },
            "stage_authorizations": authorization_rows,
        }
        host_manifest_path = shard_root / "deployment_manifest.json"
        _write_identical_or_new(host_manifest_path, host_manifest)
        host_manifest["path"] = str(host_manifest_path)
        host_manifest["sha256"] = sha256_file(host_manifest_path)
        host_manifests.append(host_manifest)

    deployment = {
        "schema_version": SCHEMA_VERSION,
        "created_at": timestamp,
        "campaign_lock": {
            "path": str(verified.lock_path),
            "sha256": verified.lock_sha256,
        },
        "execution_policy_sha256": execution_policy_sha,
        "agent_batch_order": list(EXPECTED_AGENTS),
        "cross_agent_model_overlap_forbidden": True,
        "continue_on_isolated_job_error": True,
        "consecutive_terminal_case_failure_pause_threshold": 4,
        "hosts": host_manifests,
    }
    deployment_path = output / "deployment_manifest.json"
    _write_identical_or_new(deployment_path, deployment)
    return {
        "status": "prepared",
        "deployment_manifest_path": str(deployment_path),
        "deployment_manifest_sha256": sha256_file(deployment_path),
        "execution_lock_sha256": verified.lock_sha256,
        "execution_policy_sha256": execution_policy_sha,
        "host_job_counts": {
            row["shard_id"]: row["job_count"] for row in host_manifests
        },
        "formal_episode_started": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-lock", type=Path, default=DEFAULT_CAMPAIGN_LOCK)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--agents-config", type=Path, default=DEFAULT_AGENTS_CONFIG)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = materialize_remaining_849_remote_controls(
            campaign_lock_path=args.campaign_lock,
            output_root=args.output_root,
            agents_config_path=args.agents_config,
        )
    except (ContractLifecycleError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "formal_episode_started": False,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
