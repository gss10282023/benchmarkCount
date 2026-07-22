from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from evidence_system.webarena_openrouter_credential import (
    REQUIRED_MODELS,
    build_openrouter_credential_acceptance,
    write_openrouter_credential_acceptance,
)


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "build_webarena_verified_step20_acceptance.py"
SPEC = importlib.util.spec_from_file_location("wv_step20_acceptance", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

EXPECTED_AGENT_INPUT_TREE_SHA256 = (
    "98f4f404cae6e794bd2fa1d0c152d43b7fa5d6ee5bffea143a0c9c39ddd4c975"
)
EXPECTED_TASK_CONTRACT_INDEX_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
CURRENT_APPROXIMATE_FREE_GB = {
    "webarena-gpt54-ord": 248.0,
    "webarena-claude47-ord": 248.0,
    "webarena-deepseek-v4pro-ord": 248.0,
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _force_missing_operational_receipts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(MODULE, "SITE_DEPLOYMENT_RECEIPTS", tmp_path / "sites")
    monkeypatch.setattr(MODULE, "BROWSER_ACCEPTANCE_ROOT", tmp_path / "browser")
    monkeypatch.setattr(
        MODULE, "BROWSER_ACCEPTANCE", tmp_path / "browser" / "acceptance.json"
    )
    monkeypatch.setattr(MODULE, "BROWSER_ARTIFACT_ROOT", tmp_path / "browser-artifacts")
    monkeypatch.setattr(MODULE, "EXTENDED_RESET_ACCEPTANCE", tmp_path / "extended.json")
    monkeypatch.setattr(MODULE, "PILOT_ACCEPTANCE", tmp_path / "pilot.json")
    monkeypatch.setattr(MODULE, "FAULT_ACCEPTANCE", tmp_path / "fault.json")
    monkeypatch.setattr(MODULE, "PILOT_BUDGET_ACCEPTANCE", tmp_path / "budget.json")
    monkeypatch.setattr(MODULE, "STORAGE_ACCEPTANCE", tmp_path / "storage.json")
    monkeypatch.setattr(MODULE, "CREDENTIAL_ACCEPTANCE", tmp_path / "credential.json")
    monkeypatch.setattr(MODULE, "PILOT_RESULT_ROOT", tmp_path / "pilot-results")
    monkeypatch.setattr(
        MODULE,
        "validate_formal_run_control",
        lambda: {"status": "pending", "formal_paid_launch_ready": False},
    )


def test_step20_aggregate_is_machine_pass_but_launch_blocked(
    monkeypatch, tmp_path: Path
) -> None:
    _force_missing_operational_receipts(monkeypatch, tmp_path)
    result = MODULE.build_acceptance(
        openrouter_credential_status="invalid_401_user_not_found",
        observed_free_gb=CURRENT_APPROXIMATE_FREE_GB,
        historical_secret_file_count=148,
        historical_secret_occurrence_count=2304,
        active_key_exact_match_count=0,
    )

    assert result["schema_version"] == "webarena_verified_step20_aggregate_acceptance/v2"
    assert result["status"] == "blocked"
    assert result["step20_complete"] is False
    assert result["pilot_launch_eligible"] is False
    assert result["formal_2436_launch_eligible"] is False
    assert result["machine_validation_status"] == "pass"

    machine = result["machine_gates"]
    assert all(gate["status"] == "pass" for gate in machine.values())
    assert machine["native_contract_machine_validation"]["machine_validated_count"] == 812
    assert machine["native_contract_machine_validation"]["fallback_contract_count"] == 0
    assert machine["native_human_review_queue"]["status"] == "pass"
    assert machine["native_human_review_queue"]["queue_item_count"] == 0
    assert machine["native_human_review_queue"]["human_signed_count"] == 0
    assert machine["native_human_review_queue"][
        "human_review_requirement_waived"
    ] is True
    schedule = machine["scheduler_exact_812x3_machine_proof"]
    assert schedule["case_count"] == 812
    assert schedule["record_slot_count"] == 2436
    assert schedule["per_agent"] == {"Agent A": 812, "Agent B": 812, "Agent C": 812}
    assert schedule["fallback_contract_count"] == 0
    assert schedule["formal_launch_eligible"] is False
    assert machine["scheduler_prelock_fail_closed"]["jobs_written"] is True
    assert machine["official_cli_adapter_golden_parity"][
        "exact_cli_adapter_comparison_count"
    ] == 18
    assert machine["three_host_site_data_lock"]["status"] == "pass"
    assert machine["real_four_site_reset_smoke"]["covered_site_count"] == 4
    assert machine["real_four_site_reset_smoke"]["all_six_sites_covered"] is False
    assert machine["local_fault_classification"]["status"] == "pass"
    assert machine["local_fault_classification"]["validated_fault_kind_count"] == 4
    assert machine["local_fault_classification"][
        "formal_step20_fault_gate_satisfied"
    ] is False

    operational = result["operational_gates"]
    assert operational["native_contract_human_signoff"]["status"] == "waived"
    assert operational["native_contract_human_signoff"]["signed_count"] == 0
    assert operational["native_contract_human_signoff"]["required_count"] == 812
    assert operational["native_contract_human_signoff"][
        "human_signoff_claimed"
    ] is False
    assert operational["native_contract_operator_waiver"]["status"] == "pass"
    assert operational["native_contract_operator_waiver"][
        "reviewer_identity_or_signature_claimed"
    ] is False
    assert operational["scheduler_formal_812x3_jobs"]["status"] == "pass"
    assert operational["scheduler_formal_812x3_jobs"][
        "materialized_record_slot_count"
    ] == 2436
    assert operational["scheduler_formal_812x3_jobs"][
        "fallback_contract_count"
    ] == 0
    assert operational["six_site_deployment_and_login"]["status"] == "pending"
    assert operational["full_six_site_per_slot_reset_coverage"]["status"] == "pending"
    reset_coverage = operational["full_six_site_per_slot_reset_coverage"]
    assert reset_coverage["base_validated_receipt_count"] == 12
    assert reset_coverage["extended_validated_receipt_count"] == 0
    assert reset_coverage["covered_sites"] == [
        "gitlab",
        "reddit",
        "shopping",
        "shopping_admin",
    ]
    assert reset_coverage["all_six_sites_covered"] is False
    assert operational["openrouter_credential"]["status"] == "fail"
    assert operational["openrouter_credential"]["credential_value_read"] is False
    assert operational["openrouter_credential"]["credential_value_retained"] is False
    assert operational["real_abc_pilot_and_artifacts"]["status"] == "pending"
    assert operational["fault_injection"]["status"] == "pending"
    assert operational["pilot_runtime_secret_and_gold_scan"]["status"] == "pending"
    assert operational["pilot_cost_runtime_storage_budget"]["status"] == "pending"
    assert operational["storage_readiness"]["status"] == "fail"
    assert operational["storage_readiness"]["configured_min_free_gb"] == 350
    assert operational["storage_readiness"]["all_three_thresholds_satisfied"] is False
    assert {
        item["margin_gb"] for item in operational["storage_readiness"]["machines"]
    } == {-102.0}
    assert operational["pilot_storage_capacity_preflight"]["status"] == "pending"
    assert operational["pilot_storage_capacity_preflight"][
        "formal_2436_storage_ready"
    ] is False
    assert len(result["blocking_reasons"]) == 10
    assert len(result["pre_pilot_blocking_reasons"]) == 5

    assert machine["static_publication_secret_scan"]["status"] == "pass"
    assert machine["static_publication_secret_scan"]["finding_count"] == 0
    assert machine["static_publication_secret_scan"]["dotenv_read"] is False
    assert machine["static_model_input_gold_isolation"]["status"] == "pass"
    assert machine["static_model_input_gold_isolation"][
        "model_visible_agent_input_count"
    ] == 812
    assert machine["static_model_input_gold_isolation"][
        "gold_or_evaluator_field_finding_count"
    ] == 0
    assert result["security_attestation"] == {
        "dotenv_read_by_builder": False,
        "credential_values_recorded": False,
        "credential_value_hashes_recorded": False,
        "machine_pass_does_not_imply_human_signoff": True,
        "machine_preview_does_not_authorize_execution": True,
        "operator_waiver_is_not_human_signoff": True,
        "human_signed_count_under_operator_waiver": 0,
    }
    hygiene = result["non_blocking_repository_hygiene"]
    assert hygiene["status"] == "warning"
    assert hygiene["blocks_webarena_step20"] is False
    assert hygiene["historical_secret_pattern_file_count"] == 148
    assert hygiene["historical_secret_pattern_occurrence_count"] == 2304
    assert hygiene["active_key_exact_match_count"] == 0
    assert hygiene["credential_values_or_hashes_recorded"] is False

    scope = result["requested_scope"]
    assert scope["identical_three_vps_environment"]["status"] == "pass"
    assert scope["identical_three_vps_environment"]["server_count"] == 3
    assert scope["official_evaluator_deployed_and_routed"]["status"] == "pass"
    assert (
        scope["official_evaluator_deployed_and_routed"][
            "legacy_evaluation_harness_allowed"
        ]
        is False
    )
    packets = scope["full_812_case_packets"]
    assert packets["status"] == "pass"
    assert packets["packet_count"] == 812
    assert packets["drafter_ready_packet_count"] == 812
    assert packets["draft_case_packet_file_count"] == 0
    assert packets["agent_input_tree_sha256"] == EXPECTED_AGENT_INPUT_TREE_SHA256
    assert packets["agent_input_total_bytes"] == 235_617
    assert packets["private_evaluator_payloads_in_model_inputs"] == 0
    assert packets["task_contract_index_sha256"] == EXPECTED_TASK_CONTRACT_INDEX_SHA256
    source_bundle_path = ROOT / packets["source_bundle_path"]
    assert packets["source_bundle_sha256"] == _sha256_file(source_bundle_path)


def test_secret_scanner_reports_metadata_without_secret_value(tmp_path: Path) -> None:
    secret = "sk-or-v1-" + "A" * 48
    artifact = tmp_path / "receipt.json"
    artifact.write_text(json.dumps({"api_key": secret}), encoding="utf-8")

    findings = MODULE.secret_scan_paths([artifact])

    assert {item["finding_type"] for item in findings} == {
        "openrouter_api_key",
        "sensitive_json_value",
    }
    encoded = json.dumps(findings, sort_keys=True)
    assert secret not in encoded
    assert hashlib.sha256(secret.encode()).hexdigest() not in encoded


def test_storage_350gb_is_a_hard_gate_not_a_warning(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(MODULE, "STORAGE_ACCEPTANCE", tmp_path / "missing.json")

    below = MODULE.validate_storage_readiness(CURRENT_APPROXIMATE_FREE_GB)
    assert below["status"] == "fail"
    assert below["gate_semantics"] == "hard_pre_launch_minimum_free_space_per_vps"
    assert below["blocks_paid_pilot_and_full_launch"] is True
    assert all(item["threshold_satisfied"] is False for item in below["machines"])

    unreceipted_above = MODULE.validate_storage_readiness(
        {machine_id: 351 for machine_id in CURRENT_APPROXIMATE_FREE_GB}
    )
    assert unreceipted_above["status"] == "pending"
    assert unreceipted_above["all_three_thresholds_satisfied"] is True
    assert unreceipted_above["blocks_paid_pilot_and_full_launch"] is True


def test_formal_run_control_accepts_hash_bound_recovery_without_rewriting_raw_circuit(
    monkeypatch, tmp_path: Path
) -> None:
    path = tmp_path / "full_run_control_acceptance.json"
    payload = {
        "schema_version": "webarena_verified_full_run_control_acceptance/v1",
        "status": "pass",
        "dry_run": True,
        "formal_paid_launch_ready": True,
        "launch_gates": {
            "formal_jobs_vps_persistent_retention_locked": True,
            "remote_retention_three_host_canary": {"status": "pending"},
            "circuit_recovery_authorization": {
                "status": "pass",
                "raw_circuit_history_preserved": True,
            },
            "raw_monitor_circuit_clear": False,
            "monitor_circuit_clear": True,
            "effective_execution_circuit_clear": True,
            "effective_remote_retention_canary_clear": True,
        },
    }
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    path.with_name(path.name + ".sha256").write_text(
        f"{_sha256_file(path)}  {path.name}\n", encoding="ascii"
    )
    monkeypatch.setattr(MODULE, "FORMAL_RUN_CONTROL_ACCEPTANCE", path)

    observed = MODULE.validate_formal_run_control()

    assert observed["status"] == "pass"
    assert observed["raw_monitor_circuit_clear"] is False
    assert observed["effective_execution_circuit_clear"] is True
    assert observed["circuit_recovery_authorization"]["status"] == "pass"


def test_provisioned_storage_and_measured_projection_release_full() -> None:
    provisioning = MODULE.validate_storage_provisioning_acceptance()
    storage = MODULE.validate_storage_readiness(None)
    pilot = MODULE.validate_pilot_storage_capacity_preflight(storage)

    assert provisioning["status"] == "pass"
    assert provisioning["host_count"] == 3
    assert provisioning["available_bytes_per_host"] == 895_944_495_104
    assert provisioning["mount_a_persistence_verified"] is True
    assert storage["status"] == "pass"
    assert storage["pilot_capacity_gate_satisfied"] is True
    assert storage["blocks_paid_pilot_for_capacity"] is False
    assert storage["blocks_full_2436_launch"] is False
    assert pilot["status"] == "pass"
    assert pilot["pilot_launch_capacity_available"] is True
    assert pilot["formal_2436_storage_ready"] is True
    assert pilot["destructive_provisioning_completed_under_scoped_authorization"] is True


def test_valid_credential_declaration_cannot_bypass_missing_receipt(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(MODULE, "CREDENTIAL_ACCEPTANCE", tmp_path / "missing.json")

    result = MODULE.validate_openrouter_credential("valid")

    assert result["status"] == "pending"
    assert result["machine_verifiable_from_repository"] is False
    assert result["blocks_paid_pilot"] is True
    assert result["credential_value_read"] is False
    assert result["credential_value_hash_retained"] is False


def test_valid_credential_requires_exact_paid_no_fallback_secret_free_receipt(
    monkeypatch, tmp_path: Path
) -> None:
    class Transport:
        def post_json(self, *, api_key, payload, timeout_seconds):
            del api_key, timeout_seconds
            model = payload["model"]
            return 200, {
                "model": model,
                "choices": [{"message": {"content": "discarded"}}],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 1,
                    "total_tokens": 5,
                    "cost": 0.000001,
                },
            }

    path = tmp_path / "credential.json"
    receipt = build_openrouter_credential_acceptance(
        api_key="test-only-secret",
        transport=Transport(),
        nonce_factory=lambda: "nonce",
    )
    write_openrouter_credential_acceptance(path, receipt)
    monkeypatch.setattr(MODULE, "CREDENTIAL_ACCEPTANCE", path)

    result = MODULE.validate_openrouter_credential("valid")

    assert result["status"] == "pass"
    assert result["machine_verifiable_from_repository"] is True
    assert result["required_models"] == list(REQUIRED_MODELS)
    assert result["exact_model_set_verified"] is True
    assert result["model_probe_count"] == 3
    assert result["successful_model_probe_count"] == 3
    assert result["paid_model_probe_count"] == 3
    assert result["fallback_model_probe_count"] == 0
    assert result["secret_scan_finding_count"] == 0
    assert result["blocks_paid_pilot"] is False


def test_legacy_broad_credential_shape_cannot_bypass_strict_validator(
    monkeypatch, tmp_path: Path
) -> None:
    path = tmp_path / "credential.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "webarena_verified_openrouter_credential_acceptance/v1",
                "status": "pass",
                "credential_material_retained": False,
                "model_probe_count": 3,
                "successful_model_probe_count": 3,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(MODULE, "CREDENTIAL_ACCEPTANCE", path)

    result = MODULE.validate_openrouter_credential("valid")

    assert result["status"] == "fail"
    assert result["machine_verifiable_from_repository"] is False
    assert result["blocks_paid_pilot"] is True


def test_partial_site_deployment_receipts_remain_pending(
    monkeypatch, tmp_path: Path
) -> None:
    root = tmp_path / "site-deployment"
    root.mkdir()
    (root / "webarena-gpt54-ord.json").write_text("{}\n", encoding="utf-8")
    diagnostic = root / "attempt-1-failed-map-env-ctrl"
    diagnostic.mkdir()
    for machine_id in CURRENT_APPROXIMATE_FREE_GB:
        (diagnostic / f"{machine_id}.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(MODULE, "SITE_DEPLOYMENT_RECEIPTS", root)

    result = MODULE.validate_site_deployment_aggregate()

    assert result["status"] == "pending"
    assert result["present_receipt_count"] == 1
    assert result["validated_host_count"] == 0
    assert result["login_verification_complete"] is False
    assert result["canonical_receipts_only"] is True
    assert result["ignored_nonpassing_diagnostic_receipt_count"] == 3


def _write_extended_acceptance(
    path: Path,
    *,
    passing: bool,
) -> None:
    machine_ids = sorted(CURRENT_APPROXIMATE_FREE_GB)
    task_scopes = {
        97: ["wikipedia", "map"],
        759: ["shopping_admin", "map"],
    }
    gate_names = (
        "locked_task_sources_and_scopes_exact",
        "receipt_set_exact_6",
        "all_receipts_clean_pass",
        "all_receipts_schema_identity_and_lock_valid",
        "all_two_site_scope_and_row_order_exact",
        "all_exclusive_locks_complete",
        "all_digest_and_loopback_bindings_valid",
        "all_map_wiki_admin_sentinels_pass",
        "all_container_transitions_fresh",
        "cross_host_digest_and_sentinels_identical",
        "cross_host_container_ids_unique",
        "all_12_after_container_ids_globally_unique",
    )
    gates = {name: True for name in gate_names}
    if not passing:
        gates["all_map_wiki_admin_sentinels_pass"] = False
    payload = {
        "schema_version": "webarena_verified_extended_real_reset_acceptance/v1",
        "status": "pass" if passing else "blocked",
        "expected": {
            "machine_ids": machine_ids,
            "tasks": [
                {"task_id": task_id, "reset_scope": scope}
                for task_id, scope in task_scopes.items()
            ],
        },
        "counts": {
            "expected_receipts": 6,
            "observed_receipts": 6,
            "validated_receipts": 6,
            "expected_site_rows": 12,
            "observed_validated_site_rows": 12,
            "blocking_reasons": 0 if passing else 1,
        },
        "gates": gates,
        "entries": [
            {
                "machine_id": machine_id,
                "task_id": task_id,
                "status": "pass",
                "expected_reset_scope": scope,
                "sites": [{"site": site} for site in scope],
                "flags": {
                    "clean_pass": True,
                    "schema_identity_lock": True,
                    "scope_order": True,
                    "exclusive_lock": True,
                    "digest_loopback": True,
                    "sentinels": True,
                    "fresh": True,
                },
            }
            for machine_id in machine_ids
            for task_id, scope in task_scopes.items()
        ],
        "cross_host_consistency": [
            {
                "task_id": task_id,
                "site": site,
                "host_count": 3,
                "digest_and_sentinels_identical": True,
                "fresh_container_ids_unique_across_hosts": True,
            }
            for task_id, scope in task_scopes.items()
            for site in scope
        ],
        "blocking_reasons": [] if passing else ["injected sentinel failure"],
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_name(path.name + ".sha256").write_text(
        f"{digest}  {path.name}\n",
        encoding="utf-8",
    )


def test_full_six_site_reset_coverage_passes_only_with_both_receipts(
    monkeypatch, tmp_path: Path
) -> None:
    extended_path = tmp_path / "extended.json"
    _write_extended_acceptance(extended_path, passing=True)
    monkeypatch.setattr(MODULE, "EXTENDED_RESET_ACCEPTANCE", extended_path)

    base = MODULE.validate_reset_smoke_aggregate()
    extended = MODULE.validate_extended_reset_aggregate()
    combined = MODULE.validate_full_six_site_reset_coverage(base, extended)

    assert base["status"] == "pass"
    assert extended["status"] == "pass"
    assert extended["validated_receipt_count"] == 6
    assert extended["task_ids"] == [97, 759]
    assert combined["status"] == "pass"
    assert combined["base_validated_receipt_count"] == 12
    assert combined["extended_validated_receipt_count"] == 6
    assert combined["covered_site_count"] == 6
    assert combined["all_six_sites_covered"] is True


def test_full_six_site_reset_coverage_stays_pending_without_extended_receipt(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(MODULE, "EXTENDED_RESET_ACCEPTANCE", tmp_path / "missing.json")

    base = MODULE.validate_reset_smoke_aggregate()
    extended = MODULE.validate_extended_reset_aggregate()
    combined = MODULE.validate_full_six_site_reset_coverage(base, extended)

    assert base["status"] == "pass"
    assert extended["status"] == "pending"
    assert combined["status"] == "pending"
    assert combined["all_six_sites_covered"] is False


def test_full_six_site_reset_coverage_fails_for_complete_but_invalid_extended_receipt(
    monkeypatch, tmp_path: Path
) -> None:
    extended_path = tmp_path / "extended.json"
    _write_extended_acceptance(extended_path, passing=False)
    monkeypatch.setattr(MODULE, "EXTENDED_RESET_ACCEPTANCE", extended_path)

    base = MODULE.validate_reset_smoke_aggregate()
    extended = MODULE.validate_extended_reset_aggregate()
    combined = MODULE.validate_full_six_site_reset_coverage(base, extended)

    assert base["status"] == "pass"
    assert extended["status"] == "fail"
    assert combined["status"] == "fail"
    assert "invalid acceptance receipt" in combined["reason"]


def test_real_browser_acceptance_is_required_and_strict() -> None:
    deployment = MODULE.validate_site_deployment_aggregate()
    browser = MODULE.validate_real_browser_acceptance()
    combined = MODULE.validate_six_site_deployment_and_browser(deployment, browser)

    assert deployment["status"] == "pass"
    assert browser["status"] == "pass"
    assert browser["validated_host_count"] == 3
    assert browser["validated_http_probe_count"] == 18
    assert browser["validated_real_browser_probe_count"] == 18
    assert browser["validated_authenticated_page_probe_count"] == 36
    assert browser["validated_artifact_count"] > 0
    assert combined["status"] == "pass"
    assert combined["real_browser_verification_complete"] is True


def test_six_site_gate_does_not_pass_without_real_browser_receipt(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(MODULE, "BROWSER_ACCEPTANCE", tmp_path / "missing.json")
    deployment = MODULE.validate_site_deployment_aggregate()
    browser = MODULE.validate_real_browser_acceptance()
    combined = MODULE.validate_six_site_deployment_and_browser(deployment, browser)

    assert deployment["status"] == "pass"
    assert browser["status"] == "pending"
    assert combined["status"] == "pending"
    assert combined["real_browser_verification_complete"] is False


def test_scheduler_separates_preview_prelock_and_formal_jobs() -> None:
    result = MODULE.validate_retired_compiler_and_materialized_schedule()[
        "scheduler"
    ]

    assert result["scheduler_exact_812x3_machine_proof"]["status"] == "pass"
    assert result["scheduler_exact_812x3_machine_proof"][
        "all_2436_slots_declare_reset"
    ] is True
    assert result["scheduler_prelock_fail_closed"]["status"] == "pass"
    assert result["scheduler_formal_812x3_jobs"]["status"] == "pass"
    assert result["scheduler_formal_812x3_jobs"][
        "materialized_record_slot_count"
    ] == 2436
    assert result["scheduler_formal_812x3_jobs"]["formal_launch_eligible"] is True
    assert result["scheduler_formal_812x3_jobs"][
        "all_2436_jobs_bind_operator_waiver"
    ] is True
    assert result["scheduler_formal_812x3_jobs"]["human_signed_count"] == 0


def test_remote_fault_gate_requires_exact_matrix_and_clean_postflight() -> None:
    result = MODULE.validate_remote_fault_acceptance()

    assert result["status"] == "pass"
    assert result["validated_receipt_count"] == 12
    assert result["exact_three_by_four_matrix"] is True
    assert result["postflight_status"] == "pass"
    assert result["postflight_six_sites_per_host"] is True
    assert result["postflight_no_slot_locks_or_workers"] is True


def test_claimed_pilot_gates_without_slot_artifacts_fail_closed(
    monkeypatch, tmp_path: Path
) -> None:
    path = tmp_path / "pilot.json"
    payload = {
        "schema_version": "webarena_verified_pilot_acceptance/v1",
        "status": "pass",
        "gates": {
            name: True
            for name in (
                "all_24_slots_completed",
                "all_reset_receipts_present",
                "all_har_artifacts_present",
                "all_trace_artifacts_present",
                "all_native_evaluator_io_present",
                "all_raw_runs_present",
                "all_artifact_manifests_present",
                "all_model_call_records_present",
                "structured_final_json_valid",
                "paired_seed_exact",
                "counterbalanced_order_exact",
                "schema_hash_pointer_failures_zero",
                "expected_fallback_zero",
                "active_secret_cookie_credential_leakage_zero",
                "gold_expected_leakage_zero",
            )
        },
    }
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    path.with_name(path.name + ".sha256").write_text(
        f"{_sha256_file(path)}  {path.name}\n", encoding="utf-8"
    )
    monkeypatch.setattr(MODULE, "PILOT_ACCEPTANCE", path)

    result = MODULE.validate_real_pilot_acceptance()

    assert result["status"] == "fail"
    assert result["validated_record_slot_count"] == 0
    assert result["validated_artifact_count"] == 0
