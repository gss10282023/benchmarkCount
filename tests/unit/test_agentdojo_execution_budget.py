from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evidence_system.adapters.agentdojo_runtime_control import load_runtime_policy
from evidence_system.contracts.agentdojo_execution_budget import (
    DEFAULT_BUDGET_PLAN,
    build_budget_definition,
    validate_budget_plan_payload,
    verify_budget_plan,
)
from evidence_system.contracts.agentdojo_full_execution import (
    DEFAULT_RUNTIME_INFRA_OVERLAY,
    DEFAULT_RUNTIME_POLICY,
    _output_precondition,
    _canary_case_ids,
    _concurrency_promotion_policy,
    _strict_agentdojo_infra_snapshot,
    _validate_final_credential_after_ramp,
    _validate_budget_bindings,
    _validate_vps_provision_receipt,
    _validated_case_refs,
    build_execution_definition,
    build_locked_job_entries,
    verify_job_binding,
    ExecutionLockResult,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_CATALOG,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_BUNDLE,
)
from evidence_system.contracts.common import ContractLifecycleError, load_mapping
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.schemas import validate_object
from evidence_system.orchestrator.agentdojo_locked_runner import (
    LockedEvidencePlan,
    LockedStage,
    _health_parent,
    _locked_target_promotion_decision,
    _stage_health_decision,
    run_locked_stage,
)


ROOT = Path(__file__).resolve().parents[2]


def test_budget_plan_is_metadata_only_current_and_exact() -> None:
    payload = verify_budget_plan(DEFAULT_BUDGET_PLAN)
    definition = payload["definition"]

    assert definition["historical_observation"]["case_units"] == 100
    assert definition["historical_observation"]["record_slots"] == 300
    assert definition["full_projection"]["case_units"] == 949
    assert definition["full_projection"]["record_slots"] == 2847
    assert definition["budget_guard"] == {
        "projected_cost_usd": 527.18,
        "credit_floor_usd": 650.0,
        "maximum_run_cost_usd": 650.0,
        "headroom_usd": 122.82,
        "cost_cap_action": "block_new_requests",
    }
    assert definition["preflight_projection"] == {
        "concurrency_stages_per_agent": [4, 8, 16, 32],
        "model_concurrency_substage_count_per_round": 12,
        "stage_receipt_count_per_round": 13,
        "per_model_ramp_slots_per_agent_per_round": 60,
        "independent_mixed_canary_slots_per_agent_per_round": 4,
        "independent_mixed_canary_record_slots_per_round": 12,
        "slots_per_agent_per_round": 64,
        "record_slots_per_round": 192,
        "rounds": ["measurement", "final_hash_validation"],
        "round_count": 2,
        "agent_cost_usd_per_round": {
            "Agent A": 2.391,
            "Agent B": 30.809,
            "Agent C": 2.352,
        },
        "cost_usd_per_round": 35.553,
        "two_round_cost_usd": 71.106,
        "credential_and_mixed_canary_margin_usd": 78.894,
        "preflight_reserve_usd": 150.0,
        "recommended_initial_credit_usd": 800.0,
        "required_post_ramp_credit_usd": 650.0,
        "formal_maximum_run_cost_usd": 650.0,
        "credit_gate": (
            "require_initial_credit_at_least_800_and_after_disposable_ramp_"
            "require_remaining_credit_at_least_650"
        ),
    }
    source = definition["source"]
    assert source["calls_log_file_count"] == 300
    assert all(
        source[field] is False
        for field in (
            "response_content_included",
            "prompt_content_included",
            "trajectory_content_included",
            "evaluator_labels_included",
            "secret_material_included",
        )
    )


def test_budget_plan_rejects_a_rehashed_but_stale_source_snapshot() -> None:
    payload = deepcopy(verify_budget_plan(DEFAULT_BUDGET_PLAN))
    payload["definition"]["source"]["source_tree_sha256"] = "0" * 64
    payload["definition_sha256"] = sha256_object(payload["definition"])
    validate_budget_plan_payload(payload)
    assert build_budget_definition() != payload["definition"]


def test_execution_budget_accepts_honest_unlimited_key_waiver_with_local_cap() -> None:
    receipt = {
        "provider_limit_mode": "unlimited_no_provider_cap",
        "key_limit_usd": None,
        "key_limit_remaining_usd": None,
        "credit_floor_proof_status": (
            "waived_by_user_provider_balance_unavailable"
        ),
        "credit_floor_waiver_reason": (
            "provider_unlimited_key_exposes_no_limit_remaining_balance"
        ),
        "budget_policy": {"maximum_formal_run_cost_usd": 650.0},
        "local_software_run_cost_cap_usd": 650.0,
        "local_software_cost_cap_action": "block_new_requests",
    }
    runtime_policy = SimpleNamespace(
        budget=SimpleNamespace(
            minimum_formal_start_remaining_usd=650.0,
            maximum_run_cost_usd=650.0,
            cost_cap_action="block_new_requests",
        )
    )
    _validate_budget_bindings(
        verify_budget_plan(DEFAULT_BUDGET_PLAN),
        runtime_policy=runtime_policy,
        pre_ramp_credit_receipt=receipt,
        credit_receipt=receipt,
        credit_floor_usd=650.0,
    )
    broken = deepcopy(receipt)
    broken["local_software_run_cost_cap_usd"] = 649.0
    with pytest.raises(ContractLifecycleError, match=r"local \$650 software cap"):
        _validate_budget_bindings(
            verify_budget_plan(DEFAULT_BUDGET_PLAN),
            runtime_policy=runtime_policy,
            pre_ramp_credit_receipt=receipt,
            credit_receipt=broken,
            credit_floor_usd=650.0,
        )


def test_locked_job_mapping_is_exact_949_by_three() -> None:
    refs = _validated_case_refs(
        load_mapping(DEFAULT_MANIFEST),
        load_mapping(DEFAULT_CATALOG),
        load_mapping(DEFAULT_SOURCE_BUNDLE),
    )
    entries = build_locked_job_entries(refs, base_seed=7)

    assert len(refs) == 949
    assert len(entries) == 2847
    assert len({row["job_id"] for row in entries}) == 2847
    assert len({row["record_slot_id"] for row in entries}) == 2847
    assert len({(row["case_unit_id"], row["agent_id"]) for row in entries}) == 2847
    assert [row["agent_id"] for row in entries[:949]] == ["Agent A"] * 949
    assert [row["agent_id"] for row in entries[949:1898]] == ["Agent B"] * 949
    assert [row["agent_id"] for row in entries[1898:]] == ["Agent C"] * 949
    first_case = [row for row in entries if row["case_unit_id"] == refs[0]["case_unit_id"]]
    assert {row["seed"] for row in first_case} == {7}
    promotion = _concurrency_promotion_policy(
        entries, _canary_case_ids([row["case_unit_id"] for row in refs])
    )
    assert promotion["agent_batch_order"] == ["Agent A", "Agent B", "Agent C"]
    assert promotion["canary"]["record_slot_count"] == 12
    assert promotion["formal_stage_order"] == [
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
    for agent_id in ("Agent A", "Agent B", "Agent C"):
        stages = promotion["agent_ramp_stages"][agent_id]
        assert [row["agent_id"] for row in stages] == [agent_id] * 3
        assert [row["new_distinct_slot_count"] for row in stages] == [32, 64, 128]
        assert len({slot for row in stages for slot in row["record_slot_ids"]}) == 224


def test_output_precondition_allows_only_the_explicit_namespace_reservation() -> None:
    observed = _output_precondition()
    assert observed["staging_namespace_file_count"] == 0
    assert observed["formal_raw_result_file_count"] == 0
    assert observed["score_result_file_count"] == 0
    assert observed["formal_namespace_allowed_file_count"] == 1
    assert observed["formal_namespace_reservation"]["path"].endswith(
        "/NAMESPACE_LOCK.json"
    )


def test_final_credit_probe_must_follow_disposable_ramp() -> None:
    with pytest.raises(ContractLifecycleError, match="after disposable ramp"):
        _validate_final_credential_after_ramp(
            {"created_at": "2026-07-16T10:00:00+00:00"},
            {"completed_at": "2026-07-16T10:01:00+00:00"},
        )
    _validate_final_credential_after_ramp(
        {"created_at": "2026-07-16T10:02:00+00:00"},
        {"completed_at": "2026-07-16T10:01:00+00:00"},
    )


def test_execution_definition_fails_closed_without_final_receipts(
    tmp_path: Path,
) -> None:
    with pytest.raises(ContractLifecycleError, match="credential probe receipt"):
        build_execution_definition(
            credential_probe_receipt_path=tmp_path / "missing-credential.json",
            disposable_ramp_receipt_path=tmp_path / "missing-ramp.json",
        )


def test_run_stage_without_namespace_init_never_calls_executor(tmp_path: Path) -> None:
    lock_path = tmp_path / "execution_lock.json"
    lock_path.write_text("{}\n", encoding="utf-8")
    execution = ExecutionLockResult(
        lock_path=lock_path,
        lock_sha256="1" * 64,
        definition={
            "execution_policy_sha256": "2" * 64,
            "failure_policy": {"retry_transient_model_attempts": 0},
            "concurrency_policy": {"ramp_workers": [4, 8, 16, 32]},
        },
        created=False,
    )
    plan = LockedEvidencePlan(
        execution=execution,
        lock_payload={},
        planned=(),
        by_slot={},
        plan_index_path=tmp_path / "plan.json",
        plan_index_sha256="3" * 64,
    )
    stage = LockedStage(
        stage_id="canary",
        workers=4,
        planned=(),
        record_slot_ids_sha256=sha256_object([]),
        sequence_predecessor_stage_id=None,
        health_parent_stage_id=None,
        health_parent_agent_id=None,
    )
    calls = 0

    def executor(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return []

    def missing_namespace(*_args, **_kwargs):
        raise ContractLifecycleError("namespace-init receipt is missing")

    with pytest.raises(ContractLifecycleError, match="namespace-init"):
        run_locked_stage(
            plan,
            stage,
            infra_config_path=tmp_path / "infra.yaml",
            executor=executor,
            receipt_root=tmp_path / "receipts",
            execution_observation_root=tmp_path / "observations",
            namespace_init_receipt_path=tmp_path / "missing-init.json",
            namespace_verifier=missing_namespace,
        )
    assert calls == 0


def test_formal_health_parent_is_per_agent_not_sequence_predecessor() -> None:
    assert _health_parent("ramp-a-8") == ("canary", "Agent A")
    assert _health_parent("ramp-b-8") == ("canary", "Agent B")
    assert _health_parent("ramp-c-8") == ("canary", "Agent C")
    assert _health_parent("ramp-b-16") == ("ramp-b-8", "Agent B")
    assert _health_parent("ramp-c-32") == ("ramp-c-16", "Agent C")
    assert _health_parent("remaining-a") == ("ramp-a-32", "Agent A")
    assert _health_parent("recovery-c") == ("remaining-c", "Agent C")
    canary = {
        "stage_id": "canary",
        "model_decisions": [
            {"agent_id": "Agent A", "promotion_authorized": True, "safe_workers": 4},
            {"agent_id": "Agent B", "promotion_authorized": False, "safe_workers": 4},
            {"agent_id": "Agent C", "promotion_authorized": True, "safe_workers": 4},
        ],
    }
    assert _stage_health_decision(
        canary, parent_stage_id="canary", agent_id="Agent A"
    )["promotion_authorized"] is True
    assert _stage_health_decision(
        canary, parent_stage_id="canary", agent_id="Agent B"
    )["promotion_authorized"] is False


def test_fallback_health_cannot_promote_from_effective_8_to_locked_32() -> None:
    reported, ran_locked, authorized = _locked_target_promotion_decision(
        {"promotion_authorized": True, "safe_workers": 8},
        locked_workers=32,
        effective_workers=8,
    )
    assert reported is True
    assert ran_locked is False
    assert authorized is False
    assert _locked_target_promotion_decision(
        {"promotion_authorized": True, "safe_workers": 8},
        locked_workers=8,
        effective_workers=8,
    ) == (True, True, True)


def _current_ready_vps_receipt() -> tuple[dict, dict, dict]:
    receipt = load_mapping(
        ROOT
        / "experiments/agentdojo_full_v1.2.2_direct/provenance/vps_provision_receipt.json"
    )
    infra = load_mapping(DEFAULT_RUNTIME_INFRA_OVERLAY)
    snapshot = _strict_agentdojo_infra_snapshot(infra)
    src = ROOT / "src"
    files = sorted(
        path
        for path in src.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and not any(part.endswith(".egg-info") for part in path.parts)
    )
    receipt["runtime"]["deployed_src_file_count"] = len(files)
    receipt["runtime"]["deployed_src_tree_sha256"] = sha256_object(
        [
            {
                "path": path.relative_to(src).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in files
        ]
    )
    receipt["runtime"]["final_execution_freeze_resync_required"] = False
    receipt["schema_version"] = "agentdojo_vps_provision_receipt/v2"
    source_closure = {
        "schema_version": "agentdojo_runtime_source_closure/v1",
        "package_name": "agentdojo",
        "package_version": "0.1.35",
        "official_git_commit": "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b",
        "official_git_tree": "3c74b60f2bad4ff321d864e0c0483f256cc8f8d2",
        "wheel_filename": "agentdojo-0.1.35-py3-none-any.whl",
        "wheel_sha256": "364bea4219716b716bf639f504d195943f7f6a5535d312ca41d7098704a2affd",
        "wheel_file_path": "/srv/agentdojo-full/tooling/wheels/agentdojo-0.1.35-py3-none-any.whl",
        "dist_info_record_relative_path": "agentdojo-0.1.35.dist-info/RECORD",
        "dist_info_record_sha256": "1" * 64,
        "installed_file_count": 2,
        "installed_path_set_sha256": "2" * 64,
        "installed_content_manifest_sha256": "3" * 64,
        "record_entry_count": 2,
        "record_verified_file_count": 1,
        "record_unhashed_entry_count": 1,
        "record_verification": "all_hashed_entries_match_paths_contained_no_links_or_special_inodes",
        "imported_package_root": "/srv/agentdojo-full/repo/.venv/lib/python3.12/site-packages/agentdojo",
        "upstream_repository_root": "/srv/agentdojo-full/agentdojo-upstream-v0.1.35",
        "upstream_head_matches_official_commit": True,
        "upstream_tree_matches_official_tree": True,
        "installed_source_matches_upstream_tree": True,
        "closure_verified": True,
        "secret_material_recorded": False,
    }
    receipt["agentdojo_runtime_source_closure"] = source_closure
    receipt["agentdojo_runtime_source_closure_sha256"] = sha256_object(
        source_closure
    )
    receipt["preliminary_receipt_supersession"] = {
        "path": "experiments/agentdojo_full_v1.2.2_direct/provenance/preliminary/vps_provision_receipt.json",
        "sha256": "4" * 64,
    }
    receipt["recorded_at_utc"] = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()
    receipt["run_readiness"]["blocking_reasons"] = [
        "OPENROUTER_API_KEY credential validation is pending"
    ]
    return receipt, infra, snapshot


def test_vps_receipt_cross_checks_overlay_and_later_credential_proof() -> None:
    receipt, infra, snapshot = _current_ready_vps_receipt()
    _validate_vps_provision_receipt(
        receipt,
        infra=infra,
        infra_snapshot=snapshot,
        credential_receipt={"status": "passed"},
    )

    receipt["host_identity"]["fingerprint_sha256"] = (
        "SHA256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    )
    with pytest.raises(ContractLifecycleError, match="fingerprint"):
        _validate_vps_provision_receipt(
            receipt,
            infra=infra,
            infra_snapshot=snapshot,
            credential_receipt={"status": "passed"},
        )


def test_job_binding_rejects_replaced_runtime_policy(tmp_path: Path) -> None:
    policy_payload = load_mapping(DEFAULT_RUNTIME_POLICY)
    policy = load_runtime_policy(policy_payload)
    entry = {
        "job_id": "job",
        "case_unit_id": "v1.2.2:banking:user_task_0:injection_task_0",
        "task_id": "v1.2.2:banking:user_task_0:injection_task_0",
        "record_slot_id": "slot",
        "run_id": "run",
        "attempt_id": "attempt",
        "seed": 7,
        "agent_id": "Agent A",
    }
    execution_policy_sha = "1" * 64
    lock = {
        "definition": {
            "job_plan": {"entries": [entry]},
            "execution_policy_sha256": execution_policy_sha,
            "runtime_policy": {
                "path": str(DEFAULT_RUNTIME_POLICY),
                "sha256": sha256_file(DEFAULT_RUNTIME_POLICY),
            },
            "rate_limit_policy": {
                "runtime_policy_semantic_sha256": policy.semantic_sha256
            },
        }
    }
    lock_path = tmp_path / "execution_lock.json"
    lock_path.write_text(json.dumps(lock, sort_keys=True) + "\n", encoding="utf-8")
    lock_sha = sha256_file(lock_path)
    job = {
        **entry,
        "domain": "agentdojo",
        "phase": "full",
        "experiment_type": "appendix",
        "result_namespace": "agentdojo_full_v1.2.2_direct_execution_staging",
        "execution_lock_path": str(lock_path),
        "execution_lock_sha256": lock_sha,
        "execution_policy_sha256": execution_policy_sha,
        "openrouter_runtime_policy": policy_payload,
        "openrouter_runtime_policy_sha256": policy.semantic_sha256,
        "openrouter_runtime_policy_file_sha256": sha256_file(DEFAULT_RUNTIME_POLICY),
    }
    verify_job_binding(job, lock, lock_path=lock_path, lock_sha256=lock_sha)

    replaced = deepcopy(job)
    replaced["openrouter_runtime_policy"]["max_concurrent_requests"] = 31
    with pytest.raises(ContractLifecycleError, match="was replaced"):
        verify_job_binding(
            replaced, lock, lock_path=lock_path, lock_sha256=lock_sha
        )


@pytest.mark.parametrize(
    ("schema_name", "fixture_name"),
    (
        ("raw_run", "valid_raw_run.json"),
        ("artifact_manifest", "valid_artifact_manifest.json"),
    ),
)
def test_execution_artifacts_require_all_four_hash_bindings(
    schema_name: str, fixture_name: str
) -> None:
    payload = load_mapping(ROOT / "tests/fixtures" / fixture_name)
    payload["execution_lock_sha256"] = "1" * 64
    report = validate_object(schema_name, payload, raise_on_error=False)
    assert not report.ok
    assert "must be present together" in json.dumps(report.to_dict())

    payload.update(
        {
            "execution_policy_sha256": "2" * 64,
            "openrouter_runtime_policy_sha256": "3" * 64,
            "openrouter_runtime_policy_file_sha256": "4" * 64,
        }
    )
    assert validate_object(schema_name, payload, raise_on_error=False).ok
