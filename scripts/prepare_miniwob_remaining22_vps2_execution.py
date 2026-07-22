#!/usr/bin/env python3
"""Create a runtime-only derived lock for the frozen MiniWoB remaining-22 cohort.

The checklist and case-packet trees are inputs and are never modified.  This
script derives a new execution namespace for VPS2, records the host/ramp policy,
and emits the ordinary namespaced experiment lock expected by ``run_full``.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_NAMESPACE = "miniwob_remaining22_bg0143_v1"
NAMESPACE = "miniwob_remaining22_bg0143_vps2_20260719_v1"
BASE_MANIFEST = ROOT / "experiments/appendix/miniwob_remaining22_manifest.yaml"
BASE_BUNDLE = ROOT / "experiments/evidence_contracts/source_bundles/miniwob_remaining22_case_units_source_bundle.json"
BASE_INFRA = ROOT / "configs/miniwob_browsergym_0_14_3_execution.locked.yaml"
BASE_AGENTS = ROOT / "configs/miniwob_browsergym_0_14_3_agents.locked.yaml"
BASE_FREEZE = ROOT / "experiments/evidence_contracts/locked/miniwob_remaining22_bg0143_v1/provenance/freeze_receipt.json"
CHECKLIST_ROOT = ROOT / "experiments/evidence_contracts/locked/miniwob_remaining22_bg0143_v1/checklists"
PACKET_ROOT = ROOT / "experiments/case_packets_extensions/miniwob_remaining22/miniwob"

MANIFEST_REL = "experiments/appendix/miniwob_remaining22_vps2_20260719_manifest.yaml"
BUNDLE_REL = "experiments/evidence_contracts/source_bundles/miniwob_remaining22_vps2_20260719_case_units_source_bundle.json"
INFRA_REL = "configs/miniwob_browsergym_0_14_3_vps2_20260719_execution.locked.yaml"
AGENTS_REL = "configs/miniwob_browsergym_0_14_3_vps2_20260719_agents.locked.yaml"
LOCK_REL = "experiments/evidence_contracts/runtime_locks/miniwob_remaining22_vps2_20260719_experiment_lock.json"
DERIVATION_REL = "experiments/evidence_contracts/runtime_locks/miniwob_remaining22_vps2_20260719_derivation_receipt.json"
KNOWN_HOSTS_REL = "experiments/evidence_contracts/runtime_locks/miniwob_vps2_20260719_known_hosts.ed25519"

HOST = "207.148.81.191"
HOST_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOg4yFPKXBJPZWMXofIe79z9YKM//dV+yjZmQ+nImc34"
HOST_FINGERPRINT = "SHA256:olcxZYCxN4pGGBdk/o6c6mKGCvJx1byndAzd1nXxVUM"
CONTROLLER_KEY_FINGERPRINT = "SHA256:rcKcDTJ+/mpnVGDcwUP5SIPho8K9E1qu+QBqj9JY1es"
RAMP = [1, 2, 4, 6, 8, 10]
RUNTIME_CODE = (
    "src/evidence_system/adapters/miniwob.py",
    "src/evidence_system/adapters/miniwob_remote_receipt.py",
    "src/evidence_system/adapters/miniwob_worker.py",
    "src/evidence_system/adapters/workarena_worker.py",
    "src/evidence_system/adapters/runtime.py",
    "src/evidence_system/orchestrator/jobs.py",
    "scripts/run_miniwob_remaining22_vps2_campaign.py",
    "scripts/retry_miniwob_remaining22_vps2_infra.py",
    "scripts/resume_miniwob_remaining22_vps2_after_provider_recovery.py",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    data = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def tree_sha(root: Path) -> str:
    records = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            records.append({"path": path.relative_to(root).as_posix(), "sha256": sha_file(path)})
    return canonical_sha(records)


def write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> None:
    manifest_path = ROOT / MANIFEST_REL
    bundle_path = ROOT / BUNDLE_REL
    infra_path = ROOT / INFRA_REL
    agents_path = ROOT / AGENTS_REL
    lock_path = ROOT / LOCK_REL
    derivation_path = ROOT / DERIVATION_REL
    known_hosts_path = ROOT / KNOWN_HOSTS_REL
    locked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
    known_hosts_path.write_text(f"{HOST} {HOST_KEY}\n", encoding="utf-8")

    infra = deepcopy(load(BASE_INFRA))
    infra["paths"] = {
        key: str(value).replace(BASE_NAMESPACE, NAMESPACE)
        for key, value in dict(infra["paths"]).items()
    }
    infra["domain_machine_constraints"] = {"miniwob": ["miniwob_vps"]}
    machine = infra["machines"][0]
    machine["machine_id"] = "agentdojo-vps2-miniwob-01"
    machine["role"] = "miniwob_vps"
    machine["ssh"] = {
        "host": HOST,
        "user": "root",
        "port": 22,
        "key_path": "/Users/gss/.ssh/id_ed25519",
        "known_hosts_file": KNOWN_HOSTS_REL,
        "ed25519_fingerprint": HOST_FINGERPRINT,
        "public_key_fingerprint": CONTROLLER_KEY_FINGERPRINT,
    }
    machine["concurrency"] = 10
    machine["resources"] = {"gpu": False, "cpu_limit": 8, "memory_gb": 31}
    machine["logs_dir"] = str(machine["logs_dir"]).replace(BASE_NAMESPACE, NAMESPACE)
    machine["results_dir"] = str(machine["results_dir"]).replace(BASE_NAMESPACE, NAMESPACE)
    machine["benchmark_assets"]["browser_artifacts"] = str(
        machine["benchmark_assets"]["browser_artifacts"]
    ).replace(BASE_NAMESPACE, NAMESPACE)
    machine["allowed_domains"] = ["miniwob"]
    machine["benchmarks"]["miniwob"]["openrouter_provider_only_by_model"] = {
        "deepseek/deepseek-v4-pro": "baidu/fp8"
    }
    machine["concurrency_ramp"] = {
        "workers": RAMP,
        "promotion_requires": [
            "zero_infra_excluded",
            "official_evaluator_output_present",
            "run_summary_completed",
            "artifact_inventory_complete",
            "http_and_browser_health_ok",
            "host_resource_health_ok",
        ],
        "stop_on_failure": True,
    }
    write(infra_path, infra)

    agents = deepcopy(load(BASE_AGENTS))
    for role in agents["experimental_agents"].values():
        role["rate_limit"] = {**role["rate_limit"], "concurrent_requests": 10}
    write(agents_path, agents)

    manifest = deepcopy(load(BASE_MANIFEST))
    manifest["manifest_version"] = "1.0.1-vps2-runtime"
    manifest["result_namespace"] = NAMESPACE
    manifest["infra_config_hash"] = sha_file(infra_path)
    manifest["agents_config_hash"] = sha_file(agents_path)
    manifest["experiment_lock_path"] = LOCK_REL
    roles = agents["experimental_agents"]
    for entry in manifest["agents"]:
        entry["config_hash"] = canonical_sha(roles[entry["agent_id"]])
    manifest["source_bundle_hash"] = "0" * 64

    bundle = deepcopy(load(BASE_BUNDLE))
    bundle["manifest_path"] = MANIFEST_REL
    definition = deepcopy(manifest)
    definition.pop("source_bundle_hash", None)
    bundle["manifest_definition_sha256"] = canonical_sha(definition)
    write(bundle_path, bundle)
    manifest["source_bundle_hash"] = sha_file(bundle_path)
    write(manifest_path, manifest)

    lock = {
        "schema_version": "miniwob_namespaced_experiment_lock/v1",
        "lock_id": "miniwob-remaining22-vps2-20260719-runtime-lock-v1",
        "lock_status": "locked",
        "locked_at": locked_at,
        "result_namespace": NAMESPACE,
        "artifacts": {
            "manifest_path": MANIFEST_REL,
            "manifest_sha256": sha_file(manifest_path),
            "source_bundle_path": BUNDLE_REL,
            "source_bundle_sha256": sha_file(bundle_path),
            "case_packets_root": rel(PACKET_ROOT),
            "case_packets_tree_sha256": tree_sha(PACKET_ROOT),
            "checklists_root": rel(CHECKLIST_ROOT),
            "checklists_tree_sha256": tree_sha(CHECKLIST_ROOT),
            "base_checklist_freeze_path": rel(BASE_FREEZE),
            "base_checklist_freeze_sha256": sha_file(BASE_FREEZE),
        },
        "execution": {
            "phase": "full",
            "experiment_type": "diagnostic",
            "record_slots": 66,
            "case_count": 22,
            "agent_count": 3,
            "host": HOST,
            "concurrency_ramp": RAMP,
            "max_workers": 10,
            "formal_case_slots_must_not_be_used_for_smoke": True,
        },
        "runtime_inputs": {
            "infra_config_path": INFRA_REL,
            "infra_config_sha256": sha_file(infra_path),
            "agents_config_path": AGENTS_REL,
            "agents_config_sha256": sha_file(agents_path),
            "known_hosts_path": KNOWN_HOSTS_REL,
            "known_hosts_sha256": sha_file(known_hosts_path),
            "host_ed25519_fingerprint": HOST_FINGERPRINT,
        },
        "runtime_code_sha256": {path: sha_file(ROOT / path) for path in RUNTIME_CODE},
        "legacy_artifact_snapshot_sha256": {},
    }
    definition = {
        key: value
        for key, value in lock.items()
        if key not in {"schema_version", "lock_id", "lock_status", "locked_at", "definition_sha256"}
    }
    lock["definition_sha256"] = canonical_sha(definition)
    write(lock_path, lock)

    receipt = {
        "schema_version": "miniwob_runtime_derivation_receipt/v1",
        "status": "amended_for_health_gated_provider_recovery",
        "created_at": locked_at,
        "formal_cohort_outcomes_observed_before_derivation": 59,
        "formal_cohort_slots_accepted_before_retry_amendment": 48,
        "formal_cohort_infra_attempts_preserved": 11,
        "nonformal_preflight_outcome_allowed": True,
        "runtime_amendment": {
            "scope": "controller_artifact_audit_only",
            "reason": "Use recursive WebM discovery for BrowserGym task_video/chat_video subdirectories and accept audited skip_completed reuse without rerunning the completed slot.",
            "benchmark_worker_or_evaluator_changed": False,
            "completed_slot_rerun_authorized": False,
            "superseded_controller_sha256": "c7ceba904eb3b0be27fa40a5a525fe933f67cd781d54b8e597acab9374648a4f",
            "superseded_experiment_lock_sha256": "ef5d38a4e3e6b31a6e977ee73e2157767b623891a3c72978044d7497d8fe7a21"
        },
        "teardown_amendment": {
            "scope": "environment_close_and_video_flush_only",
            "reason": "Three preserved second attempts completed their official episode and evaluator artifacts but Chromium video finalization exceeded the former 20-second env.close window.",
            "old_timeout_seconds": 20,
            "intermediate_timeout_seconds": 60,
            "new_timeout_seconds": 180,
            "superseded_worker_sha256": "73af6cb520ecdf1515a43fbf0eaec70e02d4ff2f76f06b64e758400f6f20e5e2",
            "superseded_experiment_lock_sha256": "075703608444ad92b606935a299f5f2a436a65bad69b28980c8d9b9c562e4b3a",
            "intermediate_60s_worker_sha256": "42120aa49f5e6319c3daa31c6c4be1c78c51e59e37e70ef931147f0e5ad65806",
            "intermediate_60s_experiment_lock_sha256": "a24b7cdbea663d72c29923cfa998c182e34f5ec6a0a9c2f98ec52354822968f8",
            "task_or_seed_changed": False,
            "model_or_prompt_changed": False,
            "action_budget_changed": False,
            "released_evaluator_or_success_derivation_changed": False,
            "prior_attempts_preserved": True,
            "completed_accepted_slots_rerun_authorized": False
        },
        "provider_recovery_amendment": {
            "scope": "Agent C OpenRouter endpoint health and malformed-response handling",
            "model": "deepseek/deepseek-v4-pro",
            "model_identity_changed": False,
            "provider_before": "OpenRouter default dynamic routing",
            "unhealthy_endpoint_observed": "StreamLake",
            "provider_only_after": "baidu/fp8",
            "provider_health_gate_path": "results/namespaces/miniwob_remaining22_bg0143_vps2_20260719_v1/campaign_control/agent-c-provider-recovery-health.json",
            "locked_per_call_retry_count": 2,
            "malformed_empty_content_is_retryable": True,
            "all_provider_attempts_retained": True,
            "task_or_seed_changed": False,
            "prompt_or_action_budget_changed": False,
            "released_evaluator_or_success_derivation_changed": False,
            "prior_attempts_preserved": True,
            "accepted_slots_rerun_authorized": False
        },
        "retry_amendment": {
            "scope": "eleven_preserved_infra_attempts_across_four_affected_slots",
            "authorized_by_locked_agent_retry": 2,
            "episode_retries_are_infra_recovery_not_agent_api_retry": True,
            "empty_openrouter_content_attempts": 6,
            "environment_close_timeout_attempts": 5,
            "provider_recovery_repair_workers": 1,
            "native_failure_labels_assigned": 0,
            "failed_attempts_preserved": True
        },
        "base": {
            "namespace": BASE_NAMESPACE,
            "manifest_path": rel(BASE_MANIFEST),
            "manifest_sha256": sha_file(BASE_MANIFEST),
            "infra_path": rel(BASE_INFRA),
            "infra_sha256": sha_file(BASE_INFRA),
            "agents_path": rel(BASE_AGENTS),
            "agents_sha256": sha_file(BASE_AGENTS),
            "freeze_path": rel(BASE_FREEZE),
            "freeze_sha256": sha_file(BASE_FREEZE),
        },
        "derived": {
            "namespace": NAMESPACE,
            "manifest_path": MANIFEST_REL,
            "manifest_sha256": sha_file(manifest_path),
            "source_bundle_path": BUNDLE_REL,
            "source_bundle_sha256": sha_file(bundle_path),
            "infra_path": INFRA_REL,
            "infra_sha256": sha_file(infra_path),
            "agents_path": AGENTS_REL,
            "agents_sha256": sha_file(agents_path),
            "experiment_lock_path": LOCK_REL,
            "experiment_lock_sha256": sha_file(lock_path),
        },
        "immutability": {
            "checklists_tree_sha256": tree_sha(CHECKLIST_ROOT),
            "case_packets_tree_sha256": tree_sha(PACKET_ROOT),
            "checklist_content_changed": False,
            "case_packet_content_changed": False,
        },
        "authorized_runtime_changes": {
            "host": HOST,
            "capacity": {"cpu": 8, "memory_gb": 31, "max_workers": 10},
            "concurrency_ramp": RAMP,
            "agent_model_identity_changed": False,
            "agent_rate_limit_concurrent_requests": 10,
        },
    }
    write(derivation_path, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
