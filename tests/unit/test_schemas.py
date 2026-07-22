from __future__ import annotations

import json
import os
import subprocess
import sys
import hashlib
from copy import deepcopy
from pathlib import Path

import yaml

from evidence_system.core.schemas import (
    REQUIRED_SCHEMA_FILES,
    SchemaValidationError,
    check_schema_files,
    load_schema,
    validate_cross_object_consistency,
    validate_object,
    validate_paper_mapping_coverage,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def annotate_fixture(name: str, payload: dict | None = None) -> dict:
    path = FIXTURES / name
    annotated = deepcopy(payload if payload is not None else load_fixture(name))
    annotated["__path"] = str(path.relative_to(ROOT))
    annotated["__abs_path"] = str(path)
    annotated["__sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return annotated


def canonical_string_list_hash(values: list[str]) -> str:
    canonical = json.dumps([str(value) for value in values], ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def planned_record_slot_ids(domain_id: str, count: int) -> list[str]:
    return [f"{domain_id}-slot-{index:03d}" for index in range(count)]


def planned_record_slot_ids_hash(domain_id: str, count: int) -> str:
    return canonical_string_list_hash(planned_record_slot_ids(domain_id, count))


def assert_valid(schema_name: str, payload: dict, *, formal: bool = False, labels: set[str] | None = None) -> None:
    report = validate_object(
        schema_name,
        payload,
        formal=formal,
        paper_mapping_labels=labels,
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()


def assert_invalid(schema_name: str, payload: dict, expected_fragment: str, *, formal: bool = False) -> None:
    report = validate_object(schema_name, payload, formal=formal, raise_on_error=False)
    assert not report.ok
    text = json.dumps(report.to_dict(), sort_keys=True)
    assert expected_fragment in text


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else f"{src}{os.pathsep}{env['PYTHONPATH']}"
    return env


def make_denominator_audit_for_domain(domain_entry: dict) -> dict:
    domain_id = domain_entry["domain"]
    attempted = domain_entry["record_slot_count"]
    slot_ids = planned_record_slot_ids(domain_id, attempted)
    audit = load_fixture("valid_denominator_audit.json")
    audit.update(
        {
            "audit_id": f"den-audit-{domain_id}",
            "domain": domain_id,
            "domain_display_name": domain_entry["domain_display_name"],
            "attempted_record_slots": attempted,
            "completed_records": 1,
            "infra_excluded": 1,
            "formally_documented_missing_or_blocked": attempted - 2,
            "attempted_record_slot_ids": slot_ids,
            "completed_record_ids": [slot_ids[0]],
            "infra_exclusion_record_ids": [slot_ids[1]],
            "formally_blocked_record_slot_ids": slot_ids[2:],
            "attempted_record_slot_ids_hash": canonical_string_list_hash(slot_ids),
            "formally_blocked_record_slot_ids_hash": canonical_string_list_hash(slot_ids[2:]),
            "infra_exclusion_records_hash": canonical_string_list_hash([slot_ids[1]]),
            "official_split_exception_id": domain_entry.get("official_split_exception_id"),
            "official_split_exception_case_units": (
                domain_entry["case_unit_count"] if domain_entry.get("official_split_exception_id") else None
            ),
            "__path": f"results/audits/{domain_id}.json",
            "__abs_path": str(ROOT / "results" / "audits" / f"{domain_id}.json"),
            "__sha256": hashlib.sha256(domain_id.encode("utf-8")).hexdigest(),
        }
    )
    return audit


def refresh_denominator_audit_hashes(audit: dict) -> None:
    audit["attempted_record_slot_ids_hash"] = canonical_string_list_hash(audit["attempted_record_slot_ids"])
    audit["formally_blocked_record_slot_ids_hash"] = canonical_string_list_hash(audit["formally_blocked_record_slot_ids"])
    audit["infra_exclusion_records_hash"] = canonical_string_list_hash(audit["infra_exclusion_record_ids"])


def bind_aggregate_to_audit(aggregate: dict, audit: dict) -> None:
    aggregate["denominator_audit_ref"] = audit["__path"]
    aggregate["denominator_audit_sha256"] = audit["__sha256"]


def paper_mapping_labels() -> set[str]:
    labels_payload = load_fixture("valid_paper_mapping.json")
    labels = set().union(*labels_payload["labels"].values())
    labels.add("Formal Definitions")
    return labels


def native_decisive_support_payload(*, artifact_path: str, artifact_sha: str) -> dict:
    artifact_manifest = load_fixture("valid_artifact_manifest.json")
    artifact = artifact_manifest["artifacts"][0]
    evidence_contract = load_fixture("valid_evidence_contract.json")
    required_artifact = evidence_contract["required_artifacts"][0]
    return {
        "artifact_id": artifact["artifact_id"],
        "artifact_manifest_path": artifact_path,
        "artifact_manifest_sha256": artifact_sha,
        "artifact_sha256": artifact["sha256"],
        "contract_requirement_id": required_artifact["contract_requirement_id"],
        "locked_artifact_mapping": True,
        "official_provenance": True,
        "verified_evaluator_output_object_hash": artifact["verified_evaluator_output_object_hash"],
        "verified_object_or_direct_artifact_read": True,
    }


def aggregate_source_record_set_hash(*records: dict) -> str:
    entries = []
    for record in records:
        entries.append(
            {
                "record_id": record["record_id"],
                "record_slot_id": record["record_slot_id"],
                "source_path": record["__path"],
                "source_sha256": record["__sha256"],
            }
        )
    canonical = json.dumps(sorted(entries, key=lambda item: item["record_id"]), ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_schema_registry_files_are_formal_not_placeholders() -> None:
    status = check_schema_files()
    assert status.ok, status.missing
    for filename in REQUIRED_SCHEMA_FILES:
        schema = load_schema(filename)
        assert schema["x-step"] == "Step 3 Schema / Provenance / Validator"
        assert "Placeholder" not in schema["description"]
        assert "not_implemented_in_step_2" not in json.dumps(schema)
        fixture_name = f"valid_{filename.removesuffix('.schema.json')}.json"
        assert (FIXTURES / fixture_name).exists(), fixture_name


def test_valid_core_fixtures_pass() -> None:
    cases = [
        ("scored_record", "valid_scored_record.json"),
        ("scored_record", "valid_scored_unresolve.json"),
        ("infra_exclusion_record", "valid_infra_exclusion_record.json"),
        ("raw_run", "valid_raw_run.json"),
        ("job", "valid_job.json"),
        ("artifact_manifest", "valid_artifact_manifest.json"),
        ("aggregate_metrics", "valid_aggregate_metrics.json"),
        ("aggregate_metrics", "valid_aggregate_no_counted.json"),
        ("paper_mapping", "valid_paper_mapping.json"),
        ("experiment_manifest", "valid_experiment_manifest.json"),
        ("evidence_contract", "valid_evidence_contract.json"),
        ("contract_review", "valid_contract_review.json"),
        ("agent_config", "valid_agent_config.json"),
        ("infra_config", "valid_infra_config.json"),
        ("llm_call", "valid_llm_call.json"),
        ("llm_call", "valid_llm_call_missing_cost.json"),
        ("human_review", "valid_human_review.json"),
        ("human_time", "valid_human_time.json"),
        ("audit_item", "valid_audit_item.json"),
        ("audit_label", "valid_audit_label.json"),
        ("audit_sampling_plan", "valid_audit_sampling_plan.json"),
        ("bootstrap_plan", "valid_bootstrap_plan.json"),
        ("deployment_manifest", "valid_deployment_manifest.json"),
        ("failure_record", "valid_failure_record.json"),
        ("pairwise_matrix", "valid_pairwise_matrix.json"),
        ("prediction_outcome", "valid_prediction_outcome.json"),
        ("release_artifact", "valid_release_artifact.json"),
        ("rerun_record", "valid_rerun_record.json"),
        ("rerun_subset", "valid_rerun_subset.json"),
        ("stats_plan", "valid_stats_plan.json"),
        ("freeze_manifest", "valid_freeze_manifest.json"),
        ("denominator_audit", "valid_denominator_audit.json"),
        ("paper_output", "valid_paper_output.json"),
    ]
    labels = paper_mapping_labels()
    for schema_name, fixture_name in cases:
        assert_valid(schema_name, load_fixture(fixture_name), labels=labels)


def test_completed_scored_record_requires_contract_hash() -> None:
    payload = load_fixture("valid_scored_record.json")
    del payload["contract_hash"]
    assert_invalid("scored_record", payload, "contract_hash")


def test_unresolve_requires_fixed_reason_and_level() -> None:
    payload = load_fixture("valid_scored_unresolve.json")
    payload["unresolve_reason"] = None
    assert_invalid("scored_record", payload, "R1-R7")

    for legacy_reason in (
        "R5 Paired-arm asymmetry",
        "R6 Evaluator output ambiguity",
        "R7 Claim-scope mismatch",
    ):
        payload = load_fixture("valid_scored_unresolve.json")
        payload["unresolve_reason"] = legacy_reason
        assert_invalid("scored_record", payload, legacy_reason)


def test_success_fail_cannot_carry_unresolve_metadata() -> None:
    payload = load_fixture("valid_scored_record.json")
    payload["unresolve_reason"] = "R1"
    payload["unresolve_level"] = "trace_level"
    assert_invalid("scored_record", payload, "SUCCESS/FAIL cannot carry")


def test_infra_excluded_cannot_carry_evidence_label_and_stays_in_audit() -> None:
    payload = load_fixture("valid_infra_exclusion_record.json")
    payload["evidence_label"] = "UNRESOLVE"
    payload["unresolve_reason"] = "R1"
    assert_invalid("infra_exclusion_record", payload, "INFRA_EXCLUDED must not carry")

    payload = load_fixture("valid_infra_exclusion_record.json")
    payload["entered_denominator_audit"] = False
    assert_invalid("infra_exclusion_record", payload, "denominator audit")


def test_denominator_final_state_records_must_be_final_attempts() -> None:
    payload = load_fixture("valid_scored_record.json")
    payload["final_attempt"] = False
    assert_invalid("scored_record", payload, "final_attempt=true")

    payload = load_fixture("valid_infra_exclusion_record.json")
    payload["final_attempt"] = False
    assert_invalid("infra_exclusion_record", payload, "final_attempt=true")


def test_counted_only_score_is_null_when_no_counted_records() -> None:
    payload = load_fixture("valid_aggregate_no_counted.json")
    assert_valid("aggregate_metrics", payload)

    for bad_value in (0, 1, ""):
        bad = deepcopy(payload)
        bad["counted_only_score"] = bad_value
        assert_invalid("aggregate_metrics", bad, "must be null")

    bad = deepcopy(payload)
    bad["counted_only_score_undefined_reason"] = None
    assert_invalid("aggregate_metrics", bad, "no_counted_records")


def test_aggregate_metric_arithmetic_is_derived_from_counts() -> None:
    payload = load_fixture("valid_aggregate_no_counted.json")
    payload.update(
        {
            "N_completed_scored_records": 4,
            "SUCCESS": 2,
            "FAIL": 1,
            "UNRESOLVE": 1,
            "counted_only_score": 2 / 3,
            "counted_only_score_undefined_reason": None,
            "coverage": 0.75,
            "lower": 0.5,
            "upper": 0.75,
            "width": 0.25,
        }
    )
    assert_valid("aggregate_metrics", payload)

    for field, bad_value in (
        ("counted_only_score", 0.5),
        ("coverage", 0.5),
        ("lower", 0.25),
        ("upper", 1.0),
        ("width", 0.75),
    ):
        bad = deepcopy(payload)
        bad[field] = bad_value
        assert_invalid("aggregate_metrics", bad, f"{field} must equal derived aggregate value")

    empty = deepcopy(payload)
    empty.update(
        {
            "N_completed_scored_records": 0,
            "SUCCESS": 0,
            "FAIL": 0,
            "UNRESOLVE": 0,
            "counted_only_score": None,
            "counted_only_score_undefined_reason": "no_counted_records",
            "coverage": 0.0,
            "lower": 0.0,
            "upper": 0.0,
            "width": 0.0,
            "source_scored_record_ids": [],
            "source_scored_record_set_hash": aggregate_source_record_set_hash(),
        }
    )
    assert_valid("aggregate_metrics", empty)

    bad_empty = deepcopy(empty)
    bad_empty["upper"] = 1.0
    assert_invalid("aggregate_metrics", bad_empty, "upper must equal derived aggregate value")


def test_stronger_measurement_requires_mapping_and_cannot_enter_main_envelope() -> None:
    payload = load_fixture("valid_scored_record.json")
    payload["claim_scope"] = "stronger_measurement"
    assert_invalid("scored_record", payload, "sidecar/appendix/manifest")

    payload["stronger_measurement_mapping"] = {
        "mapping_type": "sidecar",
        "mapping_id": "sidecar-001",
        "path": "results/appendix/sidecar.json",
        "sha256": "a" * 64,
        "enters_native_aligned_main_envelope": True,
    }
    assert_invalid("scored_record", payload, "must not enter native-aligned main envelope")


def test_native_aligned_allows_non_entering_stronger_measurement_sidecar_mapping() -> None:
    payload = load_fixture("valid_evidence_contract.json")
    payload["claim_scope"] = "native_aligned"
    payload["stronger_measurement_mapping"] = {
        "mapping_type": "appendix",
        "mapping_id": "stronger-measurement-contract-001",
        "path": "experiments/evidence_contracts/stronger_measurement/contract-001.json",
        "sha256": "0" * 64,
        "enters_native_aligned_main_envelope": False,
    }

    assert_valid("evidence_contract", payload)


def test_canonical_domain_and_phase_experiment_type_are_fail_closed() -> None:
    payload = load_fixture("valid_job.json")
    payload["domain"] = "AgentDojo"
    assert_invalid("job", payload, "canonical")

    payload = load_fixture("valid_job.json")
    payload["phase"] = "appendix"
    assert_invalid("job", payload, "phase")

    payload = load_fixture("valid_job.json")
    payload["phase"] = "full"
    payload["experiment_type"] = "appendix"
    payload["priority"] = "P2"
    payload["domain"] = "androidworld"
    assert_valid("job", payload)


def test_job_and_raw_contract_hash_mismatch_fails() -> None:
    payload = load_fixture("valid_job.json")
    payload["evidence_contract_hash"] = "9" * 64
    assert_invalid("job", payload, "contract_hash must equal evidence_contract_hash")

    payload = load_fixture("valid_raw_run.json")
    payload["evidence_contract_hash"] = "9" * 64
    assert_invalid("raw_run", payload, "contract_hash must equal evidence_contract_hash")


def test_cross_object_locked_contract_map_mismatch_fails() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    scored = load_fixture("valid_scored_record.json")
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("scored", scored)],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    scored["contract_hash"] = "9" * 64
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("scored", scored)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "locked contract canonical hash" in json.dumps(report.to_dict())


def test_draft_evidence_contract_cannot_be_registry_lock_source() -> None:
    contract = load_fixture("valid_evidence_contract.json")
    contract["contract_status"] = "draft"
    scored = load_fixture("valid_scored_record.json")
    report = validate_cross_object_consistency(
        [("evidence_contract", contract), ("scored", scored)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "registry sources must be locked" in json.dumps(report.to_dict())


def test_evidence_contract_must_be_authorized_by_manifest_lock() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    contract = load_fixture("valid_evidence_contract.json")
    manifest["contract_locks"] = []
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("evidence_contract", contract)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "loaded manifest contract_locks entry" in json.dumps(report.to_dict())

    manifest = load_fixture("valid_experiment_manifest.json")
    contract = load_fixture("valid_evidence_contract.json")
    contract["manifest_contract_lock_ref"] = "manifest-001:contract-999:1.0.0"
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("evidence_contract", contract)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "manifest_contract_lock_ref" in json.dumps(report.to_dict())


def test_artifact_manifest_contract_hash_is_checked_against_locked_registry() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    artifact_manifest = load_fixture("valid_artifact_manifest.json")
    artifact_manifest["evidence_contract_hash"] = "9" * 64
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("artifact_manifest", artifact_manifest)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "locked contract canonical hash" in json.dumps(report.to_dict())


def test_osworld_evaluator_unstable_is_diagnostic_not_unresolve() -> None:
    payload = load_fixture("valid_scored_unresolve.json")
    payload["domain"] = "osworld_verified"
    payload["domain_display_name"] = "OSWorld-Verified"
    payload["experiment_type"] = "appendix"
    payload["priority"] = "P2"
    payload["diagnostic_status"] = "evaluator_unstable"
    payload["appendix_failure_class"] = "evaluator_unstable"
    assert_invalid("scored_record", payload, "must not carry evidence SUCCESS/FAIL/UNRESOLVE")

    payload = load_fixture("valid_scored_record.json")
    payload["domain"] = "osworld_verified"
    payload["domain_display_name"] = "OSWorld-Verified"
    payload["experiment_type"] = "appendix"
    payload["priority"] = "P2"
    payload["diagnostic_status"] = "evaluator_unstable"
    payload["appendix_failure_class"] = "evaluator_unstable"
    payload["evidence_label"] = "SUCCESS"
    assert_invalid("scored_record", payload, "must not carry evidence SUCCESS/FAIL/UNRESOLVE")

    payload = load_fixture("valid_scored_record.json")
    payload["diagnostic_status"] = "evaluator_unstable"
    payload["appendix_failure_class"] = "evaluator_failure"
    assert_invalid("scored_record", payload, "diagnostic_status and appendix_failure_class mismatch")

    raw = load_fixture("valid_raw_run.json")
    raw["status"] = "EVALUATOR_UNSTABLE"
    raw["diagnostic_status"] = "completed"
    raw["appendix_failure_class"] = "none"
    assert_invalid("raw_run", raw, "EVALUATOR_UNSTABLE requires")


def test_osworld_status_matrix_rejects_inconsistent_diagnostics() -> None:
    raw = load_fixture("valid_raw_run.json")
    raw["status"] = "COMPLETED"
    raw["diagnostic_status"] = "evaluator_failure"
    raw["appendix_failure_class"] = "evaluator_failure"
    assert_invalid("raw_run", raw, "COMPLETED requires diagnostic_status=completed")

    scored = load_fixture("valid_scored_record.json")
    scored["appendix_failure_class"] = "evaluator_failure"
    assert_invalid("scored_record", scored, "COMPLETED diagnostic records")

    scored = load_fixture("valid_scored_record.json")
    scored["status"] = "INFRA_EXCLUDED"
    scored["completed_record"] = False
    scored["infra_exclusion_record"] = True
    scored["entered_evidence_denominator"] = False
    scored["evidence_label"] = None
    scored["diagnostic_status"] = "completed"
    scored["appendix_failure_class"] = "none"
    assert_invalid("scored_record", scored, "INFRA_EXCLUDED requires diagnostic_status=infra_excluded")


def test_manifest_requires_agent_rationale_and_records_short_split_exception() -> None:
    payload = load_fixture("valid_experiment_manifest.json")
    del payload["agents"][0]["agent_probe_rationale"]
    assert_invalid("experiment_manifest", payload, "agent_probe_rationale")

    payload = load_fixture("valid_experiment_manifest.json")
    payload["agents"][0]["agent_id"] = "Agent B"
    assert_invalid("experiment_manifest", payload, "exactly one each of Agent A-C")

    payload = load_fixture("valid_experiment_manifest.json")
    payload["agents"].append(deepcopy(payload["agents"][0]))
    assert_invalid("experiment_manifest", payload, "exactly one each of Agent A-C")

    payload = load_fixture("valid_experiment_manifest.json")
    payload["domains"][0]["official_split_eligible_case_units"] = 99
    assert_invalid("experiment_manifest", payload, "recorded exception")

    payload["official_split_exceptions"] = [
        {
            "exception_id": "short-agentdojo",
            "domain": "agentdojo",
            "eligible_case_units": 99,
            "required_case_units": 100,
            "official_split_hash": "e" * 64,
            "exception_recorded_before_scoring": True,
            "exception_reason": "official verified split has fewer than 100 eligible case units",
        }
    ]
    payload["domains"][0]["official_split_exception_id"] = "short-agentdojo"
    assert_valid("experiment_manifest", payload)

    payload["official_split_exceptions"][0]["official_split_hash"] = "9" * 64
    assert_invalid("experiment_manifest", payload, "hash mismatch")


def test_formal_manifest_enforces_declared_p0_main_denominator() -> None:
    payload = load_fixture("valid_experiment_manifest.json")
    assert_valid("experiment_manifest", payload, formal=True, labels=paper_mapping_labels())

    missing_llm_roles = deepcopy(payload)
    del missing_llm_roles["llm_roles"]
    assert_invalid("experiment_manifest", missing_llm_roles, "formal manifest requires locked llm_roles", formal=True)

    missing_drafter_prompt = deepcopy(payload)
    del missing_drafter_prompt["llm_roles"]["contract_drafter"]["prompt_hash"]
    assert_invalid("experiment_manifest", missing_drafter_prompt, "LLM role config field is required", formal=True)

    overlarge_official_split = deepcopy(payload)
    overlarge_official_split["domains"][0]["official_split_eligible_case_units"] = 812
    overlarge_official_split["domains"][0]["case_unit_count"] = 100
    overlarge_official_split["domains"][0]["record_slot_count"] = 300
    assert_valid("experiment_manifest", overlarge_official_split, formal=True, labels=paper_mapping_labels())

    missing_domain = deepcopy(payload)
    missing_domain["domains"] = [d for d in missing_domain["domains"] if d["domain"] != "tau3_retail"]
    assert_invalid("experiment_manifest", missing_domain, "missing required P0 main domain", formal=True)

    low_denominator = deepcopy(payload)
    low_denominator["domains"][0]["record_slot_count"] = 3
    assert_invalid("experiment_manifest", low_denominator, "record_slot_count must equal case_unit_count x 3", formal=True)

    case_mismatch = deepcopy(payload)
    case_mismatch["domains"][0]["case_unit_target"] = 100
    case_mismatch["domains"][0]["case_unit_count"] = 90
    assert_invalid("experiment_manifest", case_mismatch, "case_unit_count must match planned eligible case units", formal=True)

    split_exception = deepcopy(payload)
    split_exception["domains"][0]["case_unit_count"] = 99
    split_exception["domains"][0]["official_split_eligible_case_units"] = 99
    split_exception["domains"][0]["record_slot_count"] = 297
    split_exception["domains"][0]["official_split_exception_id"] = "short-agentdojo"
    split_exception["official_split_exceptions"] = [
        {
            "exception_id": "short-agentdojo",
            "domain": "agentdojo",
            "eligible_case_units": 99,
            "required_case_units": 100,
            "official_split_hash": split_exception["domains"][0]["official_split_hash"],
            "exception_recorded_before_scoring": True,
            "exception_reason": "official verified split has fewer than 100 eligible case units",
        }
    ]
    assert_valid("experiment_manifest", split_exception, formal=True, labels=paper_mapping_labels())

    parameterized_target = deepcopy(payload)
    for domain in parameterized_target["domains"]:
        domain["case_unit_target"] = 120
        domain["case_unit_count"] = 120
        domain["official_split_eligible_case_units"] = 812
        domain["record_slot_count"] = 360
    assert_valid(
        "experiment_manifest",
        parameterized_target,
        formal=True,
        labels=paper_mapping_labels(),
    )


def test_formal_agent_config_fails_on_unresolved_probe_rationale_placeholders() -> None:
    current = yaml.safe_load((ROOT / "configs" / "agents.yaml").read_text(encoding="utf-8"))
    assert_invalid("agent_config", current, "unresolved placeholder", formal=True)


def test_agent_config_requires_exact_fixed_agent_universe() -> None:
    payload = load_fixture("valid_agent_config.json")
    payload["experimental_agents"]["Agent E"] = deepcopy(payload["experimental_agents"]["Agent A"])
    assert_invalid("agent_config", payload, "exactly Agent A-C", formal=True)

    payload = load_fixture("valid_agent_config.json")
    del payload["experimental_agents"]["Agent C"]
    assert_invalid("agent_config", payload, "exactly Agent A-C", formal=True)

    payload = load_fixture("valid_agent_config.json")
    payload["main_domain_agent_map"]["agentdojo"] = ["Agent A", "Agent B", "Agent C"]
    assert_valid("agent_config", payload, formal=True)

    payload = load_fixture("valid_agent_config.json")
    payload["main_domain_agent_map"]["agentdojo"] = ["Agent A", "Agent B", "Agent C", "Agent C"]
    assert_invalid("agent_config", payload, "P0 main domains must map to exactly Agent A-C", formal=True)

    payload = load_fixture("valid_agent_config.json")
    del payload["main_domain_agent_map"]["appworld"]
    assert_invalid("agent_config", payload, "missing P0 main domain agent map", formal=True)


def test_formal_infra_config_requires_canonical_domain_ids() -> None:
    payload = load_fixture("valid_infra_config.json")
    assert_valid("infra_config", payload, formal=True)

    bad_constraints = load_fixture("valid_infra_config.json")
    bad_constraints["domain_machine_constraints"]["AgentDojo"] = bad_constraints["domain_machine_constraints"].pop("agentdojo")
    assert_invalid("infra_config", bad_constraints, "domain keys must use canonical identifiers", formal=True)

    bad_allowed = load_fixture("valid_infra_config.json")
    bad_allowed["machines"][0]["allowed_domains"][0] = "AgentDojo"
    assert_invalid("infra_config", bad_allowed, "allowed_domains must use canonical identifiers", formal=True)

    bad_benchmark = load_fixture("valid_infra_config.json")
    bad_benchmark["machines"][0]["benchmarks"]["AgentDojo"] = bad_benchmark["machines"][0]["benchmarks"].pop("agentdojo")
    assert_invalid("infra_config", bad_benchmark, "benchmark keys must use canonical identifiers", formal=True)


def test_paper_mapping_missing_required_label_fails_coverage() -> None:
    payload = load_fixture("valid_paper_mapping.json")
    payload["labels"]["table_labels"].remove("tab:views")
    payload["mappings"] = [item for item in payload["mappings"] if item["label"] != "tab:views"]
    report = validate_paper_mapping_coverage(payload, raise_on_error=False)
    assert not report.ok
    assert "tab:views" in json.dumps(report.to_dict())

    payload = load_fixture("valid_paper_mapping.json")
    payload["mappings"] = [item for item in payload["mappings"] if item["label"] != "tab:views"]
    report = validate_paper_mapping_coverage(payload, raise_on_error=False)
    assert not report.ok
    assert "missing required paper label mapping: tab:views" in json.dumps(report.to_dict())


def test_native_evaluator_artifact_requires_official_provenance() -> None:
    payload = load_fixture("valid_artifact_manifest.json")
    del payload["artifacts"][0]["producer_command_hash"]
    assert_invalid("artifact_manifest", payload, "producer_command_hash")

    payload = load_fixture("valid_artifact_manifest.json")
    payload["artifacts"][0]["verified_evaluator_output_object_hash"] = None
    assert_invalid("artifact_manifest", payload, "verified_evaluator_output_object_hash")

    payload = load_fixture("valid_artifact_manifest.json")
    payload["artifacts"][0]["official_runner"] = False
    assert_invalid("artifact_manifest", payload, "official_runner=true")


def test_raw_native_label_decisive_use_requires_artifact_mapping() -> None:
    payload = load_fixture("valid_raw_run.json")
    payload["native_label_used_as_decisive_evidence"] = True
    assert_invalid("raw_run", payload, "decisive native evidence")

    payload["native_decisive_support"] = native_decisive_support_payload(
        artifact_path="results/artifacts/run-001/manifest.json",
        artifact_sha="a" * 64,
    )
    assert_valid("raw_run", payload)


def test_missing_deterministic_selection_fields_fail_manifest_and_stats_plan() -> None:
    payload = load_fixture("valid_experiment_manifest.json")
    del payload["deterministic_selection"]["hash_function"]
    assert_invalid("experiment_manifest", payload, "hash_function")

    payload = load_fixture("valid_experiment_manifest.json")
    payload["deterministic_selection"]["smoke_exclusion_hash"] = "9" * 64
    assert_invalid("experiment_manifest", payload, "smoke_exclusion_hash must equal")

    payload = load_fixture("valid_job.json")
    del payload["deterministic_selection"]["hash_function"]
    assert_invalid("job", payload, "hash_function")

    payload = load_fixture("valid_stats_plan.json")
    del payload["deterministic_selection"]["hash_function"]
    assert_invalid("stats_plan", payload, "hash_function")

    payload = load_fixture("valid_freeze_manifest.json")
    del payload["hash_function"]
    assert_invalid("freeze_manifest", payload, "hash_function")

    payload = load_fixture("valid_freeze_manifest.json")
    payload["smoke_exclusion_hash"] = "8" * 64
    assert_invalid("freeze_manifest", payload, "smoke_exclusion_hash must equal")

    manifest = load_fixture("valid_experiment_manifest.json")
    job = load_fixture("valid_job.json")
    job["deterministic_selection"]["bootstrap_seed"] = 999
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("job", job)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "deterministic selection drift" in json.dumps(report.to_dict())


def test_formal_context_actual_hashes_must_close() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    freeze = load_fixture("valid_freeze_manifest.json")
    paper_mapping = load_fixture("valid_paper_mapping.json")
    contract = load_fixture("valid_evidence_contract.json")
    manifest["__sha256"] = hashlib.sha256((FIXTURES / "valid_experiment_manifest.json").read_bytes()).hexdigest()
    freeze["__sha256"] = hashlib.sha256((FIXTURES / "valid_freeze_manifest.json").read_bytes()).hexdigest()
    paper_mapping["__sha256"] = hashlib.sha256((FIXTURES / "valid_paper_mapping.json").read_bytes()).hexdigest()

    report = validate_cross_object_consistency(
        [("manifest", manifest), ("freeze", freeze), ("paper_mapping", paper_mapping), ("evidence_contract", contract)],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    bad_freeze = deepcopy(freeze)
    bad_freeze["manifest_hash"] = "9" * 64
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("freeze", bad_freeze), ("paper_mapping", paper_mapping), ("evidence_contract", contract)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "manifest_hash must match loaded experiment_manifest" in json.dumps(report.to_dict())

    bad_manifest = deepcopy(manifest)
    bad_manifest["paper_mapping_sha256"] = "8" * 64
    report = validate_cross_object_consistency(
        [("manifest", bad_manifest), ("freeze", freeze), ("paper_mapping", paper_mapping), ("evidence_contract", contract)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "paper_mapping sha256" in json.dumps(report.to_dict())

    bad_contract = deepcopy(contract)
    bad_contract["manifest_hash"] = "7" * 64
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("freeze", freeze), ("paper_mapping", paper_mapping), ("evidence_contract", bad_contract)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "evidence_contract manifest_hash" in json.dumps(report.to_dict())


def test_llm_call_requires_token_usage_and_missing_cost_reason() -> None:
    payload = load_fixture("valid_llm_call_missing_cost.json")
    del payload["token_usage"]
    assert_invalid("llm_call", payload, "token_usage")

    payload = load_fixture("valid_llm_call_missing_cost.json")
    payload["cost"]["missing_cost_reason"] = None
    assert_invalid("llm_call", payload, "missing cost amount requires")

    payload = load_fixture("valid_llm_call_missing_cost.json")
    payload["cost"].update(
        {
            "amount": 0.01,
            "total_cost_usd": 0.01,
            "pricing_source": "config_estimate",
            "cost_calculation_method": "tokens_times_config_rate",
            "missing_cost_reason": None,
            "pricing_table_id": None,
        }
    )
    assert_invalid("llm_call", payload, "pricing table metadata")

    payload = load_fixture("valid_llm_call_missing_cost.json")
    payload["response_timestamp"] = payload["request_timestamp"]
    assert_invalid("llm_call", payload, "response_timestamp must be after request_timestamp")


def test_llm_cost_pricing_source_method_policy_is_fail_closed() -> None:
    payload = load_fixture("valid_llm_call_missing_cost.json")
    payload["cost"].update(
        {
            "amount": 0.01,
            "total_cost_usd": 0.01,
            "pricing_source": "provider_response",
            "cost_calculation_method": "unavailable",
            "missing_cost_reason": None,
            "pricing_source_hash": "a" * 64,
        }
    )
    assert_invalid("llm_call", payload, "provider_response requires provider_reported")

    payload = load_fixture("valid_llm_call_missing_cost.json")
    payload["cost"].update(
        {
            "amount": None,
            "total_cost_usd": None,
            "pricing_source": "config_estimate",
            "cost_calculation_method": "tokens_times_config_rate",
            "missing_cost_reason": "provider_cost_unavailable",
            "pricing_table_id": "openrouter-test",
            "pricing_table_version": "v1",
            "pricing_source_hash": "a" * 64,
        }
    )
    assert_invalid("llm_call", payload, "config_estimate must produce amount")

    payload = load_fixture("valid_llm_call_missing_cost.json")
    payload["cost"].update(
        {
            "amount": 0.01,
            "total_cost_usd": 0.01,
            "pricing_source": "provider_response",
            "cost_calculation_method": "provider_reported",
            "missing_cost_reason": None,
            "pricing_source_hash": None,
        }
    )
    assert_invalid("llm_call", payload, "provider response/source hash")


def test_human_time_distinguishes_cost_table_activity_and_time_order() -> None:
    payload = load_fixture("valid_human_time.json")
    assert_valid("human_time", payload)
    payload["finished_at"] = payload["started_at"]
    assert_invalid("human_time", payload, "must be after")

    payload = load_fixture("valid_human_time.json")
    payload["no_llm_cost_included"] = False
    assert_invalid("human_time", payload, "exclude non-human costs")

    payload = load_fixture("valid_human_time.json")
    payload["no_benchmark_execution_compute_included"] = False
    assert_invalid("human_time", payload, "exclude non-human costs")

    payload = load_fixture("valid_human_time.json")
    payload["activity_type"] = "release_review"
    assert_invalid("human_time", payload, "tab:cost human-time inputs")

    payload = load_fixture("valid_human_time.json")
    payload["duration_minutes"] = 1.0
    assert_invalid("human_time", payload, "duration_minutes must match")


def test_human_and_contract_review_duration_must_match_timestamps() -> None:
    payload = load_fixture("valid_human_review.json")
    payload["duration_seconds"] = 1
    assert_invalid("human_review", payload, "duration_seconds must match")

    payload = load_fixture("valid_contract_review.json")
    payload["duration_minutes"] = 1.0
    assert_invalid("contract_review", payload, "duration_minutes must match")


def test_deployment_and_failure_provenance_are_required() -> None:
    payload = load_fixture("valid_deployment_manifest.json")
    del payload["command_hash"]
    assert_invalid("deployment_manifest", payload, "command_hash")

    payload = load_fixture("valid_failure_record.json")
    del payload["provenance"]
    assert_invalid("failure_record", payload, "provenance")

    payload = load_fixture("valid_failure_record.json")
    payload["provenance"] = {}
    assert_invalid("failure_record", payload, "failure provenance field is required")

    payload = load_fixture("valid_failure_record.json")
    payload["deployment_manifest_path"] = None
    assert_invalid("failure_record", payload, "deployment manifest provenance")

    payload = load_fixture("valid_failure_record.json")
    payload["provenance"]["failure_linkage"]["deployment_manifest_path"] = None
    assert_invalid("failure_record", payload, "deployment manifest provenance")

    payload = load_fixture("valid_failure_record.json")
    payload["provenance"]["failure_linkage"]["deployment_manifest_path"] = "results/manifests/other-deploy.json"
    assert_invalid("failure_record", payload, "must match top-level deployment_manifest_path")

    payload = load_fixture("valid_failure_record.json")
    payload["collect_results_manifest_path"] = None
    assert_invalid("failure_record", payload, "collect_results_manifest_path")

    payload = load_fixture("valid_failure_record.json")
    payload["workflow_stage"] = "resume_failed"
    payload["provenance"]["workflow_stage"] = "resume_failed"
    payload["resume_manifest_path"] = None
    assert_invalid("failure_record", payload, "resume_manifest_path")


def test_deploy_collect_resume_failure_records_require_loaded_deployment_manifest() -> None:
    failure = load_fixture("valid_failure_record.json")
    missing_report = validate_cross_object_consistency(
        [("failure_record", failure)],
        raise_on_error=False,
    )
    assert not missing_report.ok
    assert "require loaded deployment_manifest artifact" in json.dumps(missing_report.to_dict())

    deployment = annotate_fixture("valid_deployment_manifest.json")
    deployment["__path"] = "results/manifests/deploy.json"
    deployment["__abs_path"] = str(ROOT / "results" / "manifests" / "deploy.json")
    valid_report = validate_cross_object_consistency(
        [("deployment_manifest", deployment), ("failure_record", failure)],
        raise_on_error=False,
    )
    assert valid_report.ok, valid_report.to_dict()

    mismatched = deepcopy(deployment)
    mismatched["machine_id"] = "different-machine"
    mismatch_report = validate_cross_object_consistency(
        [("deployment_manifest", mismatched), ("failure_record", failure)],
        raise_on_error=False,
    )
    assert not mismatch_report.ok
    assert "deployment manifest linkage field mismatch" in json.dumps(mismatch_report.to_dict())


def test_step3_auxiliary_schema_fixtures_have_fail_closed_semantics() -> None:
    audit_item = load_fixture("valid_audit_item.json")
    audit_item["forbidden_input_assertion_hash"] = None
    assert_invalid("audit_item", audit_item, "forbidden-input assertion")

    audit_label = load_fixture("valid_audit_label.json")
    audit_label["evidence_label"] = "FAIL"
    audit_label["unresolve_reason"] = "R1"
    assert_invalid("audit_label", audit_label, "SUCCESS/FAIL cannot carry")

    audit_plan = load_fixture("valid_audit_sampling_plan.json")
    audit_plan["strata"] = ["counted_records", "unresolve_records"]
    assert_invalid("audit_sampling_plan", audit_plan, "native_evidence_disagreement")

    bootstrap_plan = load_fixture("valid_bootstrap_plan.json")
    bootstrap_plan["cluster_unit"] = "attempt"
    assert_invalid("bootstrap_plan", bootstrap_plan, "case_unit")

    prediction = load_fixture("valid_prediction_outcome.json")
    prediction["ci_lower"] = prediction["threshold"]
    prediction["outcome"] = "supported"
    assert_invalid("prediction_outcome", prediction, "touching threshold")

    rerun_record = load_fixture("valid_rerun_record.json")
    rerun_record["original_unresolve_reason"] = "R1"
    assert_invalid("rerun_record", rerun_record, "counted original rerun labels")

    rerun_subset = load_fixture("valid_rerun_subset.json")
    rerun_subset["agent_id"] = "Agent B"
    assert_invalid("rerun_subset", rerun_subset, "Agent A")

    release_artifact = load_fixture("valid_release_artifact.json")
    release_artifact["release_status"] = "access_controlled"
    assert_invalid("release_artifact", release_artifact, "release_status must match visibility")


def test_contract_review_full_ordering_fails_when_lock_after_scoring() -> None:
    payload = load_fixture("valid_contract_review.json")
    payload["locked_at"] = "2026-05-04T00:30:00+00:00"
    assert_invalid("contract_review", payload, "first_scoring_started_at must be after locked_at")

    payload = load_fixture("valid_contract_review.json")
    payload["locked_at"] = payload["first_scoring_started_at"]
    assert_invalid("contract_review", payload, "first_scoring_started_at must be after locked_at")

    payload = load_fixture("valid_contract_review.json")
    payload["locked_at"] = "not-a-timestamp"
    assert_invalid("contract_review", payload, "timestamp field must be parseable")


def test_evidence_contract_requires_canonical_hash_linkage() -> None:
    payload = load_fixture("valid_evidence_contract.json")
    payload["canonical_hash"] = "9" * 64
    assert_invalid("evidence_contract", payload, "canonical_hash must equal contract_hash")

    payload = load_fixture("valid_evidence_contract.json")
    payload["required_artifacts"][0]["contract_requirement_id"] = None
    assert_invalid("evidence_contract", payload, "contract_requirement_id")


def test_paper_output_cost_and_native_aligned_source_constraints() -> None:
    payload = load_fixture("valid_paper_output.json")
    payload["label"] = "tab:cost"
    payload["paper_mapping_label"] = "tab:views"
    payload["source_mapping"][0]["source_type"] = "static_text"
    assert_invalid("paper_output", payload, "paper_output.label must exactly equal paper_mapping_label")

    payload = load_fixture("valid_paper_output.json")
    payload["label"] = "tab:main-results-A"
    payload["paper_mapping_label"] = "tab:views"
    payload["source_mapping"][0]["source_type"] = "aggregate_metrics"
    payload["source_mapping"][0]["claim_scope"] = "stronger_measurement"
    assert_invalid("paper_output", payload, "paper_output.label must exactly equal paper_mapping_label")

    payload = load_fixture("valid_paper_output.json")
    payload["label"] = "tab:cost"
    payload["paper_mapping_label"] = "tab:cost"
    payload["source_mapping"][0]["source_type"] = "llm_call"
    assert_invalid("paper_output", payload, "tab:cost may only use human_time")

    payload = load_fixture("valid_paper_output.json")
    payload["label"] = "app:cost"
    payload["paper_mapping_label"] = "app:cost"
    payload["source_mapping"][0]["source_type"] = "llm_call"
    assert_invalid("paper_output", payload, "app:cost may only use human_time")

    payload = load_fixture("valid_paper_output.json")
    payload["label"] = "tab:main-results-A"
    payload["paper_mapping_label"] = "tab:main-results-A"
    payload["source_mapping"][0]["source_type"] = "aggregate_metrics"
    payload["source_mapping"][0]["claim_scope"] = "stronger_measurement"
    assert_invalid("paper_output", payload, "stronger_measurement sources")

    payload["source_mapping"][0]["claim_scope"] = None
    assert_invalid("paper_output", payload, "claim_scope=native_aligned")


def test_paper_mapping_cost_labels_disallow_llm_or_compute_sources() -> None:
    for bad_sources in (
        ["llm_calls"],
        ["aggregate_metrics"],
        ["scored_records"],
        ["manifest"],
        ["static_text"],
        ["human_time", "aggregate_metrics"],
    ):
        mapping = load_fixture("valid_paper_mapping.json")
        for entry in mapping["mappings"]:
            if entry["label"] == "app:cost":
                entry["provenance_sources"] = bad_sources
            if entry["label"] == "tab:cost" and bad_sources == ["aggregate_metrics"]:
                entry["provenance_sources"] = bad_sources
        report = validate_paper_mapping_coverage(mapping, raise_on_error=False)
        assert not report.ok
        assert "cost mapping must use only human_time provenance" in json.dumps(report.to_dict())


def test_paper_mapping_rejects_unmapped_duplicate_and_undeclared_labels() -> None:
    mapping = load_fixture("valid_paper_mapping.json")
    mapping["labels"]["table_labels"].append("tab:extra")
    report = validate_paper_mapping_coverage(mapping, raise_on_error=False)
    assert not report.ok
    assert "declared paper label has no mapping: tab:extra" in json.dumps(report.to_dict())

    mapping = load_fixture("valid_paper_mapping.json")
    mapping["mappings"].append(deepcopy(mapping["mappings"][0]))
    report = validate_paper_mapping_coverage(mapping, raise_on_error=False)
    assert not report.ok
    assert "duplicate paper label mapping: tab:views" in json.dumps(report.to_dict())

    mapping = load_fixture("valid_paper_mapping.json")
    mapping["mappings"][0]["label"] = "tab:not-declared"
    report = validate_paper_mapping_coverage(mapping, raise_on_error=False)
    assert not report.ok
    text = json.dumps(report.to_dict())
    assert "mapping label is not declared: tab:not-declared" in text
    assert "declared paper label has no mapping: tab:views" in text

    mapping = load_fixture("valid_paper_mapping.json")
    mapping["mappings"][0]["source_path"] = ""
    report = validate_paper_mapping_coverage(mapping, raise_on_error=False)
    assert not report.ok
    assert "paper mapping source_path is required" in json.dumps(report.to_dict())


def test_p0_pairwise_matrix_requires_exact_fixed_agent_universe() -> None:
    payload = {
        "schema_version": "pairwise_matrix/v1",
        "matrix_id": "pairwise-001",
        "domain": "agentdojo",
        "domain_display_name": "AgentDojo",
        "phase": "full",
        "experiment_type": "main",
        "priority": "P0",
        "agents": ["Agent A", "Agent B"],
        "pairwise_equality_tolerance": 1e-12,
        "cells": [
            {
                "agent_i": "Agent A",
                "agent_j": "Agent B",
                "relation": "=",
                "margin": 0,
                "bootstrap_lower": None,
            }
        ],
        "source_aggregate_metrics_hash": "a" * 64,
        "bootstrap_plan_hash": "b" * 64,
    }
    assert_invalid("pairwise_matrix", payload, "exactly one each of Agent A-C")


def test_paper_output_formal_sources_must_resolve_and_match_paper_mapping() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    paper_mapping = annotate_fixture("valid_paper_mapping.json")
    human_time = annotate_fixture("valid_human_time.json")
    human_time["contract_hash"] = None

    payload = load_fixture("valid_paper_output.json")
    payload["label"] = "tab:cost"
    payload["paper_mapping_label"] = "tab:cost"
    payload["paper_mapping_hash"] = paper_mapping["__sha256"]
    payload["source_mapping"] = [
        {
            "source_type": "human_time",
            "source_path": human_time["__path"],
            "source_sha256": human_time["__sha256"],
            "source_object_id": human_time["activity_id"],
        }
    ]
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", paper_mapping),
            ("human_time", human_time),
            ("paper_output", payload),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    bad_sha = deepcopy(payload)
    bad_sha["source_mapping"][0]["source_sha256"] = "9" * 64
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", paper_mapping),
            ("human_time", human_time),
            ("paper_output", bad_sha),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "must resolve to a loaded artifact by source_path and source_sha256" in json.dumps(report.to_dict())

    bad_mapping_hash = deepcopy(payload)
    bad_mapping_hash["paper_mapping_hash"] = "8" * 64
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", paper_mapping),
            ("human_time", human_time),
            ("paper_output", bad_mapping_hash),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "paper_output.paper_mapping_hash must match" in json.dumps(report.to_dict())

    unmapped_label_mapping = annotate_fixture("valid_paper_mapping.json")
    unmapped_label_mapping["labels"]["table_labels"].append("tab:extra")
    unmapped_payload = deepcopy(payload)
    unmapped_payload["label"] = "tab:extra"
    unmapped_payload["paper_mapping_label"] = "tab:extra"
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", unmapped_label_mapping),
            ("human_time", human_time),
            ("paper_output", unmapped_payload),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "paper_output label must resolve to exactly one loaded paper_mapping entry" in json.dumps(report.to_dict())

    bad_counts = annotate_fixture("valid_human_time.json")
    bad_counts["counts_for_cost_table"] = False
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", paper_mapping),
            ("human_time", bad_counts),
            ("paper_output", payload),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "counts_for_cost_table=true" in json.dumps(report.to_dict())

    denominator_payload = load_fixture("valid_paper_output.json")
    denominator_payload["label"] = "tab:denominator-audit"
    denominator_payload["paper_mapping_label"] = "tab:denominator-audit"
    denominator_payload["paper_mapping_hash"] = paper_mapping["__sha256"]
    denominator_payload["source_mapping"] = [
        {
            "source_type": "denominator_audit",
            "source_path": audits[0]["__path"],
            "source_sha256": audits[0]["__sha256"],
            "source_object_id": audits[0]["audit_id"],
        }
    ]
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", paper_mapping),
            ("paper_output", denominator_payload),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    wrong_denominator_sha = deepcopy(denominator_payload)
    wrong_denominator_sha["source_mapping"][0]["source_sha256"] = "7" * 64
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", paper_mapping),
            ("paper_output", wrong_denominator_sha),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    text = json.dumps(report.to_dict())
    assert "paper_output denominator_audit source must resolve to a loaded denominator_audit/v1 artifact" in text
    assert "paper_output denominator_audit source must resolve to a loaded artifact by source_path and source_sha256" in text

    wrong_denominator_path = deepcopy(denominator_payload)
    wrong_denominator_path["source_mapping"][0]["source_path"] = "results/audits/not-loaded.json"
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("paper_mapping", paper_mapping),
            ("paper_output", wrong_denominator_path),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    text = json.dumps(report.to_dict())
    assert "paper_output denominator_audit source must resolve to a loaded denominator_audit/v1 artifact" in text
    assert "paper_output denominator_audit source must resolve to a loaded artifact by source_path and source_sha256" in text


def test_cross_object_freeze_drift_fails() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    freeze = annotate_fixture("valid_freeze_manifest.json")
    scored = load_fixture("valid_scored_record.json")
    scored["scorer_version"] = "scorer-drift-2"
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("freeze", freeze), ("scored", scored)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "scorer_version drift from freeze manifest" in json.dumps(report.to_dict())

    aggregate = load_fixture("valid_aggregate_no_counted.json")
    aggregate["freeze_manifest_hash"] = "9" * 64
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    bind_aggregate_to_audit(aggregate, next(audit for audit in audits if audit["domain"] == "agentdojo"))
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("freeze", freeze), ("aggregate_metrics", aggregate), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)]],
        raise_on_error=False,
    )
    assert not report.ok
    assert "aggregate freeze_manifest_hash does not match" in json.dumps(report.to_dict())


def test_denominator_audit_requires_exact_final_state_partition() -> None:
    payload = load_fixture("valid_denominator_audit.json")
    assert_valid("denominator_audit", payload)

    payload = load_fixture("valid_denominator_audit.json")
    payload["formally_blocked_record_slot_ids"] = []
    assert_invalid("denominator_audit", payload, "attempted record slots missing final state")

    payload = load_fixture("valid_denominator_audit.json")
    payload["completed_record_ids"].append("slot-002")
    payload["completed_records"] = 2
    assert_invalid("denominator_audit", payload, "duplicate record slots")

    payload = load_fixture("valid_denominator_audit.json")
    payload["attempted_record_slot_ids_hash"] = "9" * 64
    assert_invalid("denominator_audit", payload, "attempted_record_slot_ids_hash")

    payload = load_fixture("valid_denominator_audit.json")
    payload["formally_blocked_record_slot_ids_hash"] = "8" * 64
    assert_invalid("denominator_audit", payload, "formally_blocked_record_slot_ids_hash")

    payload = load_fixture("valid_denominator_audit.json")
    payload["infra_exclusion_records_hash"] = "7" * 64
    assert_invalid("denominator_audit", payload, "infra_exclusion_records_hash")

    payload = load_fixture("valid_denominator_audit.json")
    payload["agent_caused_failures"] = 2
    assert_invalid("denominator_audit", payload, "agent_caused_failures cannot exceed completed_records")


def test_denominator_audit_cross_checks_manifest_planned_slots() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]

    report = validate_cross_object_consistency(
        [("manifest", manifest), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)]],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    split_manifest = deepcopy(manifest)
    split_manifest["domains"][0]["case_unit_count"] = 99
    split_manifest["domains"][0]["official_split_eligible_case_units"] = 99
    split_manifest["domains"][0]["record_slot_count"] = 297
    split_manifest["domains"][0]["official_split_exception_id"] = "short-agentdojo"
    split_manifest["domains"][0]["planned_record_slot_ids_hash"] = planned_record_slot_ids_hash("agentdojo", 297)
    split_manifest["official_split_exceptions"] = [
        {
            "exception_id": "short-agentdojo",
            "domain": "agentdojo",
            "eligible_case_units": 99,
            "required_case_units": 100,
            "official_split_hash": split_manifest["domains"][0]["official_split_hash"],
            "exception_recorded_before_scoring": True,
            "exception_reason": "official verified split has fewer than 100 eligible case units",
        }
    ]
    split_audits = [make_denominator_audit_for_domain(domain) for domain in split_manifest["domains"]]
    report = validate_cross_object_consistency(
        [("manifest", split_manifest), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(split_audits)]],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    unreported_split_audits = deepcopy(split_audits)
    unreported_split_audits[0]["official_split_exception_id"] = None
    unreported_split_audits[0]["official_split_exception_case_units"] = None
    report = validate_cross_object_consistency(
        [
            ("manifest", split_manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(unreported_split_audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "denominator audit must report manifest official split exception" in json.dumps(report.to_dict())

    unmanifested_exception_audits = deepcopy(audits)
    unmanifested_exception_audits[0]["official_split_exception_id"] = "unmanifested-short-split"
    unmanifested_exception_audits[0]["official_split_exception_case_units"] = 99
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(unmanifested_exception_audits)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "denominator audit reports unmanifested official split exception" in json.dumps(report.to_dict())

    audit = deepcopy(audits[0])
    audit["attempted_record_slots"] = 3
    audit["attempted_record_slot_ids"] = audit["attempted_record_slot_ids"][:3]
    audit["completed_record_ids"] = audit["attempted_record_slot_ids"][:1]
    audit["infra_exclusion_record_ids"] = audit["attempted_record_slot_ids"][1:2]
    audit["formally_blocked_record_slot_ids"] = audit["attempted_record_slot_ids"][2:]
    audit["formally_documented_missing_or_blocked"] = 1
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("denominator_audit", audit)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "manifest planned record_slot_count" in json.dumps(report.to_dict())

    bad_hash_audits = deepcopy(audits)
    bad_hash_audits[0]["attempted_record_slot_ids_hash"] = "9" * 64
    report = validate_cross_object_consistency(
        [("manifest", manifest), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(bad_hash_audits)]],
        raise_on_error=False,
    )
    assert not report.ok
    assert "planned_record_slot_ids_hash" in json.dumps(report.to_dict())

    missing_domain_audits = audits[:-1]
    report = validate_cross_object_consistency(
        [("manifest", manifest), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(missing_domain_audits)]],
        raise_on_error=False,
    )
    assert not report.ok
    assert "missing P0 denominator audit" in json.dumps(report.to_dict())


def test_formal_result_artifacts_require_loaded_denominator_audits() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    aggregate = load_fixture("valid_aggregate_no_counted.json")
    bind_aggregate_to_audit(aggregate, next(audit for audit in audits if audit["domain"] == "agentdojo"))

    report = validate_cross_object_consistency(
        [("manifest", manifest), ("aggregate_metrics", aggregate)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "formal P0 result validation requires loaded denominator_audit artifacts" in json.dumps(report.to_dict())

    report = validate_cross_object_consistency(
        [("manifest", manifest), ("aggregate_metrics", aggregate), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)]],
        raise_on_error=False,
    )
    assert not report.ok
    assert "formal P0 aggregate_metrics with source scored records require loaded scored_record/v1 artifacts" in json.dumps(report.to_dict())

    scored_payload = load_fixture("valid_scored_unresolve.json")
    scored_payload["record_slot_id"] = "agentdojo-slot-000"
    scored = annotate_fixture("valid_scored_unresolve.json", scored_payload)
    aggregate["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored)
    artifact_manifest = annotate_fixture("valid_artifact_manifest.json")
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("aggregate_metrics", aggregate),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    missing_one_audit = audits[:-1]
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("aggregate_metrics", aggregate),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(missing_one_audit)],
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "missing P0 denominator audit" in json.dumps(report.to_dict())

    dangling_ref = deepcopy(aggregate)
    dangling_ref["denominator_audit_ref"] = "results/audits/not-loaded.json"
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("aggregate_metrics", dangling_ref), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)]],
        raise_on_error=False,
    )
    assert not report.ok
    assert "denominator_audit_ref and denominator_audit_sha256 must resolve" in json.dumps(report.to_dict())

    dangling_sha = deepcopy(aggregate)
    dangling_sha["denominator_audit_sha256"] = "6" * 64
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("aggregate_metrics", dangling_sha), *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)]],
        raise_on_error=False,
    )
    assert not report.ok
    assert "denominator_audit_ref and denominator_audit_sha256 must resolve" in json.dumps(report.to_dict())

    paper = load_fixture("valid_paper_output.json")
    paper["label"] = "tab:main-results-A"
    paper["paper_mapping_label"] = "tab:main-results-A"
    paper["source_mapping"] = [
        {
            "source_type": "aggregate_metrics",
            "source_path": "results/aggregates/main.json",
            "source_sha256": "1" * 64,
            "source_object_id": "agentdojo:all",
            "claim_scope": "native_aligned",
        }
    ]
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("paper_output", paper)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "formal P0 result validation requires loaded denominator_audit artifacts" in json.dumps(report.to_dict())


def test_aggregate_metrics_cross_check_denominator_and_loaded_scored_records() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    agentdojo_audit = next(audit for audit in audits if audit["domain"] == "agentdojo")
    agentdojo_audit["completed_records"] = 1
    agentdojo_audit["completed_record_ids"] = ["slot-001"]
    agentdojo_audit["infra_excluded"] = agentdojo_audit["attempted_record_slots"] - 1
    agentdojo_audit["infra_exclusion_record_ids"] = agentdojo_audit["attempted_record_slot_ids"][1:]
    agentdojo_audit["formally_documented_missing_or_blocked"] = 0
    agentdojo_audit["formally_blocked_record_slot_ids"] = []
    refresh_denominator_audit_hashes(agentdojo_audit)

    aggregate = load_fixture("valid_aggregate_no_counted.json")
    bind_aggregate_to_audit(aggregate, agentdojo_audit)
    scored = annotate_fixture("valid_scored_unresolve.json")
    aggregate["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored)
    artifact_manifest = annotate_fixture("valid_artifact_manifest.json")

    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", aggregate),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    bad_scalar = deepcopy(aggregate)
    bad_scalar["upper"] = 0.5
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", bad_scalar),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "upper must equal derived aggregate value" in json.dumps(report.to_dict())

    bad_n = deepcopy(aggregate)
    bad_n["N_completed_scored_records"] = 2
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", bad_n),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "N_completed_scored_records must match denominator_audit completed_records" in json.dumps(report.to_dict())

    bad_ids = deepcopy(aggregate)
    bad_ids["source_scored_record_ids"] = ["record-missing"]
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", bad_ids),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "source_scored_record_ids must resolve" in json.dumps(report.to_dict())

    bad_label_count = deepcopy(aggregate)
    bad_label_count["UNRESOLVE"] = 0
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", bad_label_count),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "aggregate UNRESOLVE count must match loaded scored_record evidence labels" in json.dumps(report.to_dict())


def test_aggregate_metrics_requires_exact_source_record_slot_set_and_unique_bindings() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    agentdojo_audit = next(audit for audit in audits if audit["domain"] == "agentdojo")
    agentdojo_audit["completed_records"] = 2
    agentdojo_audit["completed_record_ids"] = ["slot-001", "slot-002"]
    agentdojo_audit["infra_excluded"] = max(agentdojo_audit["attempted_record_slots"] - 2, 0)
    agentdojo_audit["infra_exclusion_record_ids"] = agentdojo_audit["attempted_record_slot_ids"][2:]
    agentdojo_audit["formally_documented_missing_or_blocked"] = 0
    agentdojo_audit["formally_blocked_record_slot_ids"] = []
    refresh_denominator_audit_hashes(agentdojo_audit)

    aggregate = load_fixture("valid_aggregate_no_counted.json")
    aggregate.update(
        {
            "N_completed_scored_records": 2,
            "SUCCESS": 2,
            "FAIL": 0,
            "UNRESOLVE": 0,
            "counted_only_score": 1.0,
            "counted_only_score_undefined_reason": None,
            "coverage": 1.0,
            "lower": 1.0,
            "upper": 1.0,
            "width": 0.0,
            "source_scored_record_ids": ["record-001", "record-003"],
        }
    )
    bind_aggregate_to_audit(aggregate, agentdojo_audit)

    scored_a = annotate_fixture("valid_scored_record.json")
    scored_b_payload = load_fixture("valid_scored_record.json")
    scored_b_payload["record_id"] = "record-003"
    scored_b_payload["record_slot_id"] = "slot-002"
    scored_b_payload["raw_source_path"] = "results/raw_runs/run-002.json"
    scored_b = annotate_fixture("valid_scored_record.json", scored_b_payload)
    aggregate["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored_a, scored_b)
    artifact_manifest = annotate_fixture("valid_artifact_manifest.json")

    base_objects = [
        ("manifest", manifest),
        *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
        ("aggregate_metrics", aggregate),
        ("artifact_manifest", artifact_manifest),
        ("scored_record[0]", scored_a),
        ("scored_record[1]", scored_b),
    ]
    report = validate_cross_object_consistency(base_objects, raise_on_error=False)
    assert report.ok, report.to_dict()

    duplicate_source_ids = deepcopy(aggregate)
    duplicate_source_ids["source_scored_record_ids"] = ["record-001", "record-001"]
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", duplicate_source_ids),
            ("artifact_manifest", artifact_manifest),
            ("scored_record[0]", scored_a),
            ("scored_record[1]", scored_b),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "aggregate source_scored_record_ids must be unique" in json.dumps(report.to_dict())

    duplicate_resolved_slot = deepcopy(scored_b)
    duplicate_resolved_slot["record_slot_id"] = "slot-001"
    duplicate_slot_hash = deepcopy(aggregate)
    duplicate_slot_hash["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored_a, duplicate_resolved_slot)
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", duplicate_slot_hash),
            ("artifact_manifest", artifact_manifest),
            ("scored_record[0]", scored_a),
            ("scored_record[1]", duplicate_resolved_slot),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    text = json.dumps(report.to_dict())
    assert "aggregate resolved scored_record record_slot_id values must be unique" in text
    assert "aggregate resolved scored_record slot set must exactly match denominator_audit completed_record_ids" in text

    duplicate_loaded_record_id = deepcopy(scored_b)
    duplicate_loaded_record_id["record_id"] = "record-001"
    duplicate_record_hash = deepcopy(aggregate)
    duplicate_record_hash["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored_a, duplicate_loaded_record_id)
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", duplicate_record_hash),
            ("artifact_manifest", artifact_manifest),
            ("scored_record[0]", scored_a),
            ("scored_record[1]", duplicate_loaded_record_id),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "loaded scored_record artifacts must not duplicate record_id" in json.dumps(report.to_dict())

    extra_duplicate_slot = deepcopy(scored_b)
    extra_duplicate_slot["record_id"] = "record-004"
    extra_duplicate_slot["record_slot_id"] = "slot-001"
    extra_duplicate_hash = deepcopy(aggregate)
    extra_duplicate_hash["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored_a, scored_b)
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", extra_duplicate_hash),
            ("artifact_manifest", artifact_manifest),
            ("scored_record[0]", scored_a),
            ("scored_record[1]", scored_b),
            ("scored_record[2]", extra_duplicate_slot),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "loaded scored_record artifacts must not include multiple final completed scored records for the same record_slot_id" in json.dumps(report.to_dict())

    missing_loaded_scores = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", aggregate),
        ],
        raise_on_error=False,
    )
    assert not missing_loaded_scores.ok
    assert "formal P0 aggregate_metrics with source scored records require loaded scored_record/v1 artifacts" in json.dumps(missing_loaded_scores.to_dict())


def test_aggregate_metrics_empty_source_set_hash_is_fail_closed() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    agentdojo_audit = next(audit for audit in audits if audit["domain"] == "agentdojo")
    agentdojo_audit["completed_records"] = 0
    agentdojo_audit["completed_record_ids"] = []
    agentdojo_audit["infra_excluded"] = 1
    agentdojo_audit["infra_exclusion_record_ids"] = [agentdojo_audit["attempted_record_slot_ids"][0]]
    agentdojo_audit["formally_documented_missing_or_blocked"] = agentdojo_audit["attempted_record_slots"] - 1
    agentdojo_audit["formally_blocked_record_slot_ids"] = agentdojo_audit["attempted_record_slot_ids"][1:]
    refresh_denominator_audit_hashes(agentdojo_audit)

    aggregate = deepcopy(load_fixture("valid_aggregate_no_counted.json"))
    aggregate.update(
        {
            "N_completed_scored_records": 0,
            "SUCCESS": 0,
            "FAIL": 0,
            "UNRESOLVE": 0,
            "counted_only_score": None,
            "counted_only_score_undefined_reason": "no_counted_records",
            "coverage": 0.0,
            "lower": 0.0,
            "upper": 0.0,
            "width": 0.0,
            "source_scored_record_ids": [],
            "source_scored_record_set_hash": aggregate_source_record_set_hash(),
        }
    )
    bind_aggregate_to_audit(aggregate, agentdojo_audit)
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", aggregate),
        ],
        raise_on_error=False,
    )
    assert report.ok, report.to_dict()

    bad_hash = deepcopy(aggregate)
    bad_hash["source_scored_record_set_hash"] = "4" * 64
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            *[(f"denominator_audit[{i}]", audit) for i, audit in enumerate(audits)],
            ("aggregate_metrics", bad_hash),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "canonical empty source-record set hash" in json.dumps(report.to_dict())


def test_validate_results_formal_aggregate_requires_denominator_audit_context(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--aggregate-metrics",
            str(FIXTURES / "valid_aggregate_no_counted.json"),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "formal P0 result validation requires loaded denominator_audit artifacts" in result.stdout

    paper_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--paper-output",
            str(FIXTURES / "valid_paper_output.json"),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert paper_result.returncode == 1
    assert "formal P0 result validation requires loaded denominator_audit artifacts" in paper_result.stdout

    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    audit_paths: dict[str, Path] = {}
    for audit in audits:
        audit_path = tmp_path / f"{audit['domain']}_audit.json"
        audit_paths[audit["domain"]] = audit_path
        persisted = {key: value for key, value in audit.items() if not key.startswith("__")}
        audit_path.write_text(json.dumps(persisted, indent=2), encoding="utf-8")

    scored = load_fixture("valid_scored_unresolve.json")
    scored["record_slot_id"] = "agentdojo-slot-000"
    scored_path = tmp_path / "valid_scored_unresolve.json"
    scored_path.write_text(json.dumps(scored, indent=2), encoding="utf-8")
    scored_annotated = {
        **scored,
        "__path": str(scored_path),
        "__abs_path": str(scored_path),
        "__sha256": hashlib.sha256(scored_path.read_bytes()).hexdigest(),
    }

    aggregate = load_fixture("valid_aggregate_no_counted.json")
    aggregate["denominator_audit_ref"] = str(audit_paths["agentdojo"])
    aggregate["denominator_audit_sha256"] = hashlib.sha256(audit_paths["agentdojo"].read_bytes()).hexdigest()
    aggregate["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored_annotated)
    aggregate_path = tmp_path / "valid_aggregate.json"
    aggregate_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")

    base_command = [
        sys.executable,
        "-m",
        "evidence_system.cli.validate_results",
        "--formal",
        "--aggregate-metrics",
        str(aggregate_path),
        "--manifest",
        str(FIXTURES / "valid_experiment_manifest.json"),
        "--freeze-manifest",
        str(FIXTURES / "valid_freeze_manifest.json"),
        "--evidence-contract",
        str(FIXTURES / "valid_evidence_contract.json"),
        "--paper-mapping",
        str(FIXTURES / "valid_paper_mapping.json"),
    ]
    for audit_path in audit_paths.values():
        base_command.extend(["--denominator-audit", str(audit_path)])

    missing_scored = subprocess.run(
        [*base_command, "--json"],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing_scored.returncode == 1
    assert "formal P0 aggregate_metrics with source scored records require loaded scored_record/v1 artifacts" in missing_scored.stdout

    valid_result = subprocess.run(
        [
            *base_command,
            "--scored-record",
            str(scored_path),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert valid_result.returncode == 0, valid_result.stderr + valid_result.stdout

    bad_denominator_sha_aggregate = deepcopy(aggregate)
    bad_denominator_sha_aggregate["denominator_audit_sha256"] = "6" * 64
    bad_denominator_sha_path = tmp_path / "bad_denominator_sha_aggregate.json"
    bad_denominator_sha_path.write_text(json.dumps(bad_denominator_sha_aggregate, indent=2), encoding="utf-8")
    bad_denominator_sha_result = subprocess.run(
        [
            *base_command[:5],
            str(bad_denominator_sha_path),
            *base_command[6:],
            "--scored-record",
            str(scored_path),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert bad_denominator_sha_result.returncode == 1
    assert "denominator_audit_ref and denominator_audit_sha256 must resolve" in bad_denominator_sha_result.stdout

    bad_hash_aggregate = deepcopy(aggregate)
    bad_hash_aggregate["source_scored_record_set_hash"] = "9" * 64
    bad_hash_path = tmp_path / "bad_hash_aggregate.json"
    bad_hash_path.write_text(json.dumps(bad_hash_aggregate, indent=2), encoding="utf-8")
    bad_hash_result = subprocess.run(
        [
            *base_command[:5],
            str(bad_hash_path),
            *base_command[6:],
            "--scored-record",
            str(scored_path),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert bad_hash_result.returncode == 1
    assert "source_scored_record_set_hash must match loaded scored_record artifacts" in bad_hash_result.stdout

    wrong_domain = deepcopy(scored)
    wrong_domain["domain"] = "appworld"
    wrong_domain["domain_display_name"] = "AppWorld"
    wrong_domain_path = tmp_path / "wrong_domain_scored.json"
    wrong_domain_path.write_text(json.dumps(wrong_domain, indent=2), encoding="utf-8")
    wrong_domain_annotated = {
        **wrong_domain,
        "__path": str(wrong_domain_path),
        "__abs_path": str(wrong_domain_path),
        "__sha256": hashlib.sha256(wrong_domain_path.read_bytes()).hexdigest(),
    }
    wrong_domain_aggregate = deepcopy(aggregate)
    wrong_domain_aggregate["source_scored_record_set_hash"] = aggregate_source_record_set_hash(wrong_domain_annotated)
    wrong_domain_aggregate_path = tmp_path / "wrong_domain_aggregate.json"
    wrong_domain_aggregate_path.write_text(json.dumps(wrong_domain_aggregate, indent=2), encoding="utf-8")
    wrong_domain_result = subprocess.run(
        [
            *base_command[:5],
            str(wrong_domain_aggregate_path),
            *base_command[6:],
            "--scored-record",
            str(wrong_domain_path),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert wrong_domain_result.returncode == 1
    assert "aggregate source scored records must match aggregate domain" in wrong_domain_result.stdout

    label_drift_aggregate = deepcopy(aggregate)
    label_drift_aggregate["UNRESOLVE"] = 0
    label_drift_aggregate["SUCCESS"] = 1
    label_drift_aggregate["counted_only_score"] = 1.0
    label_drift_aggregate["counted_only_score_undefined_reason"] = None
    label_drift_path = tmp_path / "label_drift_aggregate.json"
    label_drift_path.write_text(json.dumps(label_drift_aggregate, indent=2), encoding="utf-8")
    label_drift_result = subprocess.run(
        [
            *base_command[:5],
            str(label_drift_path),
            *base_command[6:],
            "--scored-record",
            str(scored_path),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert label_drift_result.returncode == 1
    assert "aggregate UNRESOLVE count must match loaded scored_record evidence labels" in label_drift_result.stdout

    duplicate_slot_audit = deepcopy(audits)
    agentdojo_duplicate = next(audit for audit in duplicate_slot_audit if audit["domain"] == "agentdojo")
    agentdojo_duplicate["completed_records"] = 2
    agentdojo_duplicate["completed_record_ids"] = [agentdojo_duplicate["attempted_record_slot_ids"][0], agentdojo_duplicate["attempted_record_slot_ids"][1]]
    agentdojo_duplicate["infra_excluded"] = agentdojo_duplicate["attempted_record_slots"] - 2
    agentdojo_duplicate["infra_exclusion_record_ids"] = agentdojo_duplicate["attempted_record_slot_ids"][2:]
    agentdojo_duplicate["formally_documented_missing_or_blocked"] = 0
    agentdojo_duplicate["formally_blocked_record_slot_ids"] = []
    refresh_denominator_audit_hashes(agentdojo_duplicate)
    duplicate_audit_paths: dict[str, Path] = {}
    for audit in duplicate_slot_audit:
        audit_path = tmp_path / f"dup_{audit['domain']}_audit.json"
        duplicate_audit_paths[audit["domain"]] = audit_path
        persisted = {key: value for key, value in audit.items() if not key.startswith("__")}
        audit_path.write_text(json.dumps(persisted, indent=2), encoding="utf-8")

    duplicate_slot_scored = deepcopy(load_fixture("valid_scored_record.json"))
    duplicate_slot_scored["record_id"] = "record-003"
    duplicate_slot_scored["record_slot_id"] = "agentdojo-slot-000"
    duplicate_slot_scored_path = tmp_path / "duplicate_slot_scored.json"
    duplicate_slot_scored_path.write_text(json.dumps(duplicate_slot_scored, indent=2), encoding="utf-8")
    duplicate_slot_annotated = {
        **duplicate_slot_scored,
        "__path": str(duplicate_slot_scored_path),
        "__abs_path": str(duplicate_slot_scored_path),
        "__sha256": hashlib.sha256(duplicate_slot_scored_path.read_bytes()).hexdigest(),
    }

    duplicate_slot_aggregate = deepcopy(aggregate)
    duplicate_slot_aggregate["N_completed_scored_records"] = 2
    duplicate_slot_aggregate["SUCCESS"] = 1
    duplicate_slot_aggregate["FAIL"] = 0
    duplicate_slot_aggregate["UNRESOLVE"] = 1
    duplicate_slot_aggregate["counted_only_score"] = 1.0
    duplicate_slot_aggregate["counted_only_score_undefined_reason"] = None
    duplicate_slot_aggregate["coverage"] = 0.5
    duplicate_slot_aggregate["lower"] = 0.5
    duplicate_slot_aggregate["upper"] = 1.0
    duplicate_slot_aggregate["width"] = 0.5
    duplicate_slot_aggregate["source_scored_record_ids"] = ["record-002", "record-003"]
    duplicate_slot_aggregate["denominator_audit_ref"] = str(duplicate_audit_paths["agentdojo"])
    duplicate_slot_aggregate["denominator_audit_sha256"] = hashlib.sha256(duplicate_audit_paths["agentdojo"].read_bytes()).hexdigest()
    duplicate_slot_aggregate["source_scored_record_set_hash"] = aggregate_source_record_set_hash(scored_annotated, duplicate_slot_annotated)
    duplicate_slot_aggregate_path = tmp_path / "duplicate_slot_aggregate.json"
    duplicate_slot_aggregate_path.write_text(json.dumps(duplicate_slot_aggregate, indent=2), encoding="utf-8")

    duplicate_slot_command = [
        sys.executable,
        "-m",
        "evidence_system.cli.validate_results",
        "--formal",
        "--aggregate-metrics",
        str(duplicate_slot_aggregate_path),
        "--manifest",
        str(FIXTURES / "valid_experiment_manifest.json"),
        "--freeze-manifest",
        str(FIXTURES / "valid_freeze_manifest.json"),
        "--evidence-contract",
        str(FIXTURES / "valid_evidence_contract.json"),
        "--paper-mapping",
        str(FIXTURES / "valid_paper_mapping.json"),
    ]
    for audit_path in duplicate_audit_paths.values():
        duplicate_slot_command.extend(["--denominator-audit", str(audit_path)])
    duplicate_slot_command.extend(
        [
            "--scored-record",
            str(scored_path),
            "--scored-record",
            str(duplicate_slot_scored_path),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--json",
        ]
    )
    duplicate_slot_result = subprocess.run(
        duplicate_slot_command,
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert duplicate_slot_result.returncode == 1
    assert "multiple final completed scored records for the same record_slot_id" in duplicate_slot_result.stdout


def test_validate_results_formal_paper_output_denominator_audit_source_path(tmp_path: Path) -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    audits = [make_denominator_audit_for_domain(domain) for domain in manifest["domains"]]
    audit_paths: dict[str, Path] = {}
    for audit in audits:
        audit_path = tmp_path / f"{audit['domain']}_audit.json"
        audit_paths[audit["domain"]] = audit_path
        persisted = {key: value for key, value in audit.items() if not key.startswith("__")}
        audit_path.write_text(json.dumps(persisted, indent=2), encoding="utf-8")

    agentdojo_audit_sha = hashlib.sha256(audit_paths["agentdojo"].read_bytes()).hexdigest()
    paper = deepcopy(load_fixture("valid_paper_output.json"))
    paper["label"] = "tab:denominator-audit"
    paper["paper_mapping_label"] = "tab:denominator-audit"
    paper["source_mapping"] = [
        {
            "source_type": "denominator_audit",
            "source_path": str(audit_paths["agentdojo"]),
            "source_sha256": agentdojo_audit_sha,
            "source_object_id": "den-audit-agentdojo",
        }
    ]
    paper_path = tmp_path / "paper_denominator_output.json"
    paper_path.write_text(json.dumps(paper, indent=2), encoding="utf-8")

    base_command = [
        sys.executable,
        "-m",
        "evidence_system.cli.validate_results",
        "--formal",
        "--paper-output",
        str(paper_path),
        "--manifest",
        str(FIXTURES / "valid_experiment_manifest.json"),
        "--freeze-manifest",
        str(FIXTURES / "valid_freeze_manifest.json"),
        "--evidence-contract",
        str(FIXTURES / "valid_evidence_contract.json"),
        "--paper-mapping",
        str(FIXTURES / "valid_paper_mapping.json"),
    ]
    for audit_path in audit_paths.values():
        base_command.extend(["--denominator-audit", str(audit_path)])

    ok_result = subprocess.run(
        [*base_command, "--json"],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert ok_result.returncode == 0, ok_result.stderr + ok_result.stdout

    wrong_sha_payload = deepcopy(paper)
    wrong_sha_payload["source_mapping"][0]["source_sha256"] = "6" * 64
    wrong_sha_path = tmp_path / "paper_denominator_wrong_sha.json"
    wrong_sha_path.write_text(json.dumps(wrong_sha_payload, indent=2), encoding="utf-8")
    wrong_sha_result = subprocess.run(
        [
            *base_command[:5],
            str(wrong_sha_path),
            *base_command[6:],
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert wrong_sha_result.returncode == 1
    assert "paper_output denominator_audit source must resolve to a loaded denominator_audit/v1 artifact" in wrong_sha_result.stdout

    wrong_path_payload = deepcopy(paper)
    wrong_path_payload["source_mapping"][0]["source_path"] = str(tmp_path / "not_loaded_audit.json")
    wrong_path = tmp_path / "paper_denominator_wrong_path.json"
    wrong_path.write_text(json.dumps(wrong_path_payload, indent=2), encoding="utf-8")
    wrong_path_result = subprocess.run(
        [
            *base_command[:5],
            str(wrong_path),
            *base_command[6:],
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert wrong_path_result.returncode == 1
    assert "paper_output denominator_audit source must resolve to a loaded denominator_audit/v1 artifact" in wrong_path_result.stdout


def test_validate_manifest_cli_checks_paper_mapping_coverage() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_manifest",
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_validate_manifest_cli_accepts_yaml_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "valid_experiment_manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(load_fixture("valid_experiment_manifest.json"), sort_keys=False),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_manifest",
            "--formal",
            "--manifest",
            str(manifest_path),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert '"schema_version": "experiment_manifest/v1"' in result.stdout


def test_formal_cli_rejects_markdown_paper_mapping(tmp_path: Path) -> None:
    markdown_mapping = tmp_path / "paper_mapping.md"
    labels_payload = load_fixture("valid_paper_mapping.json")
    labels = []
    for values in labels_payload["labels"].values():
        labels.extend(values)
    markdown_mapping.write_text("\n".join(labels), encoding="utf-8")

    manifest_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_manifest",
            "--formal",
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--paper-mapping",
            str(markdown_mapping),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert manifest_result.returncode == 1
    assert "structured paper_mapping JSON" in manifest_result.stdout

    results_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(FIXTURES / "valid_scored_record.json"),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(markdown_mapping),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert results_result.returncode == 1
    assert "structured paper_mapping JSON" in results_result.stdout


def test_formal_cli_rejects_placeholder_in_structured_paper_mapping(tmp_path: Path) -> None:
    mapping = load_fixture("valid_paper_mapping.json")
    mapping["mappings"][0]["source_path"] = "TBD"
    mapping_path = tmp_path / "paper_mapping_placeholder.json"
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")

    manifest_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_manifest",
            "--formal",
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--paper-mapping",
            str(mapping_path),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert manifest_result.returncode == 1
    assert "unresolved placeholder" in manifest_result.stdout

    results_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(FIXTURES / "valid_scored_record.json"),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(mapping_path),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert results_result.returncode == 1
    assert "unresolved placeholder" in results_result.stdout


def test_validate_results_cli_requires_paper_mapping_for_paper_outputs() -> None:
    ok = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--paper-output",
            str(FIXTURES / "valid_paper_output.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert ok.returncode == 0, ok.stderr + ok.stdout

    missing = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--paper-output",
            str(FIXTURES / "valid_paper_output.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing.returncode == 1
    assert "paper outputs require --paper-mapping" in missing.stdout


def test_validate_results_formal_requires_and_uses_cross_object_context() -> None:
    missing_context = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(FIXTURES / "valid_scored_record.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing_context.returncode == 1
    assert "formal validation requires" in missing_context.stdout

    missing_artifact = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(FIXTURES / "valid_scored_record.json"),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing_artifact.returncode == 1
    assert "requires matching artifact_manifest input" in missing_artifact.stdout

    ok = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(FIXTURES / "valid_scored_record.json"),
            "--artifact-manifest",
            str(FIXTURES / "valid_artifact_manifest.json"),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert ok.returncode == 0, ok.stderr + ok.stdout


def test_validate_results_formal_failure_record_requires_deployment_manifest_context() -> None:
    missing_deployment = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--failure-record",
            str(FIXTURES / "valid_failure_record.json"),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing_deployment.returncode == 1
    assert "require loaded deployment_manifest artifact" in missing_deployment.stdout


def test_formal_native_decisive_evidence_requires_loaded_artifact_manifest(tmp_path: Path) -> None:
    artifact_manifest_path = FIXTURES / "valid_artifact_manifest.json"
    artifact_manifest_sha = hashlib.sha256(artifact_manifest_path.read_bytes()).hexdigest()
    scored = load_fixture("valid_scored_record.json")
    scored["native_label_used_as_decisive_evidence"] = True
    scored["artifact_manifest_path"] = str(artifact_manifest_path)
    scored["artifact_manifest_sha256"] = artifact_manifest_sha
    scored["native_decisive_support"] = native_decisive_support_payload(
        artifact_path=str(artifact_manifest_path),
        artifact_sha=artifact_manifest_sha,
    )
    scored_path = tmp_path / "native_decisive_scored.json"
    scored_path.write_text(json.dumps(scored), encoding="utf-8")

    missing_artifact = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(scored_path),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing_artifact.returncode == 1
    assert "requires matching artifact_manifest input" in missing_artifact.stdout

    mismatched_artifact = tmp_path / "valid_artifact_manifest.json"
    mismatched_artifact.write_text(json.dumps(load_fixture("valid_artifact_manifest.json"), indent=4), encoding="utf-8")
    scored["native_decisive_support"]["artifact_manifest_path"] = str(mismatched_artifact)
    scored_path.write_text(json.dumps(scored), encoding="utf-8")
    same_path_wrong_hash = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(scored_path),
            "--artifact-manifest",
            str(mismatched_artifact),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert same_path_wrong_hash.returncode == 1
    assert "path and sha256 must match" in same_path_wrong_hash.stdout

    scored["native_decisive_support"]["artifact_manifest_path"] = str(artifact_manifest_path)
    scored_path.write_text(json.dumps(scored), encoding="utf-8")

    with_artifact = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--scored-record",
            str(scored_path),
            "--artifact-manifest",
            str(artifact_manifest_path),
            "--manifest",
            str(FIXTURES / "valid_experiment_manifest.json"),
            "--freeze-manifest",
            str(FIXTURES / "valid_freeze_manifest.json"),
            "--evidence-contract",
            str(FIXTURES / "valid_evidence_contract.json"),
            "--paper-mapping",
            str(FIXTURES / "valid_paper_mapping.json"),
            "--json",
        ],
        cwd=ROOT,
        env=subprocess_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert with_artifact.returncode == 0, with_artifact.stderr + with_artifact.stdout


def test_native_decisive_evidence_must_match_locked_contract_required_artifacts() -> None:
    manifest = load_fixture("valid_experiment_manifest.json")
    evidence_contract = load_fixture("valid_evidence_contract.json")
    artifact_manifest = load_fixture("valid_artifact_manifest.json")
    artifact_path = str(FIXTURES / "valid_artifact_manifest.json")
    artifact_sha = hashlib.sha256((FIXTURES / "valid_artifact_manifest.json").read_bytes()).hexdigest()
    artifact_manifest["__path"] = artifact_path
    artifact_manifest["__abs_path"] = artifact_path
    artifact_manifest["__sha256"] = artifact_sha
    scored = load_fixture("valid_scored_record.json")
    scored["native_label_used_as_decisive_evidence"] = True
    scored["artifact_manifest_path"] = artifact_path
    scored["artifact_manifest_sha256"] = artifact_sha
    scored["native_decisive_support"] = native_decisive_support_payload(
        artifact_path=artifact_path,
        artifact_sha=artifact_sha,
    )

    base_objects = [
        ("manifest", manifest),
        ("evidence_contract", evidence_contract),
        ("artifact_manifest", artifact_manifest),
        ("scored_record", scored),
    ]
    report = validate_cross_object_consistency(base_objects, raise_on_error=False)
    assert report.ok, report.to_dict()

    wrong_requirement = deepcopy(artifact_manifest)
    wrong_requirement["artifacts"][0]["artifact_contract_requirement_ids"] = ["wrong-requirement"]
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("evidence_contract", evidence_contract),
            ("artifact_manifest", wrong_requirement),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "native decisive support must match the loaded artifact_manifest artifact binding" in json.dumps(report.to_dict())

    wrong_contract_artifact = deepcopy(evidence_contract)
    wrong_contract_artifact["required_artifacts"][0]["artifact_id"] = "unrelated-official-artifact"
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("evidence_contract", wrong_contract_artifact),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "native decisive support must match a loaded evidence_contract required_artifact binding" in json.dumps(report.to_dict())

    missing_requirement_id = deepcopy(evidence_contract)
    missing_requirement_id["required_artifacts"][0]["contract_requirement_id"] = None
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("evidence_contract", missing_requirement_id),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "native decisive required artifacts must declare contract_requirement_id" in json.dumps(report.to_dict())

    removed_required_artifacts = deepcopy(evidence_contract)
    removed_required_artifacts["required_artifacts"] = []
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("evidence_contract", removed_required_artifacts),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "native decisive support must match a loaded evidence_contract required_artifact binding" in json.dumps(report.to_dict())

    unrelated_official_artifact = deepcopy(artifact_manifest)
    unrelated_official_artifact["artifacts"][0]["artifact_id"] = "unrelated-official-artifact"
    unrelated_official_artifact["artifacts"][0]["artifact_contract_requirement_ids"] = ["unrelated-requirement"]
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("evidence_contract", evidence_contract),
            ("artifact_manifest", unrelated_official_artifact),
            ("scored_record", scored),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "native decisive support must match the loaded artifact_manifest artifact binding" in json.dumps(report.to_dict())

    missing_support_requirement = deepcopy(scored)
    del missing_support_requirement["native_decisive_support"]["contract_requirement_id"]
    assert_invalid("scored_record", missing_support_requirement, "contract_requirement_id")

    wrong_support_requirement = deepcopy(scored)
    wrong_support_requirement["native_decisive_support"]["contract_requirement_id"] = "wrong-requirement"
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("evidence_contract", evidence_contract),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", wrong_support_requirement),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "native decisive support must match a loaded evidence_contract required_artifact binding" in json.dumps(report.to_dict())

    wrong_support_artifact = deepcopy(scored)
    wrong_support_artifact["native_decisive_support"]["artifact_id"] = "wrong-artifact"
    report = validate_cross_object_consistency(
        [
            ("manifest", manifest),
            ("evidence_contract", evidence_contract),
            ("artifact_manifest", artifact_manifest),
            ("scored_record", wrong_support_artifact),
        ],
        raise_on_error=False,
    )
    assert not report.ok
    assert "native decisive support must match a loaded evidence_contract required_artifact binding" in json.dumps(report.to_dict())


def test_schema_validation_raises_by_default() -> None:
    payload = load_fixture("valid_scored_record.json")
    del payload["contract_hash"]
    try:
        validate_object("scored_record", payload)
    except SchemaValidationError as exc:
        assert "contract_hash" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected SchemaValidationError")
