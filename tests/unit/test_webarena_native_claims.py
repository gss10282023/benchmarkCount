from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from evidence_system.contracts import webarena_native as native
from evidence_system.contracts.validate import validate_contracts


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "experiments/step20/webarena_verified/native_claims"


def _ir(task_id: int) -> dict:
    return json.loads(
        (PACKAGE / f"drafts/ir/{task_id}/native_claim_ir.json").read_text(encoding="utf-8")
    )


def test_full_812_machine_package_is_strictly_policy_locked_without_fake_human_review() -> None:
    report = native.validate_native_claim_package(PACKAGE, current_source_check=True)
    assert report == {
        "schema_version": "webarena_verified_native_claim_validation_report/v1",
        "status": "ok",
        "issue_count": 0,
        "issues": [],
    }

    acceptance = json.loads((PACKAGE / "acceptance.json").read_text(encoding="utf-8"))
    assert acceptance["counts"] == {
        "native_ir": 812,
        "draft_contracts": 812,
        "draft_checklists": 812,
        "machine_validated": 812,
        "human_signed": 0,
        "policy_locked": 812,
        "locked_contracts": 812,
        "locked_checklists": 812,
    }
    assert acceptance["machine_contract_gate"] == {
        "machine_locked": True,
        "machine_locked_count": 812,
        "native_contract_count": 812,
        "fallback_contract_count": 0,
        "formal_human_locked": False,
        "formal_policy_locked": True,
        "authorizes_formal_launch": True,
    }
    assert acceptance["status"] == "accepted_machine_only_operator_waiver"
    assert acceptance["formal_launch_eligible"] is True
    assert acceptance["human_signoff"] == {
        "status": "waived_not_signed",
        "required_count": 812,
        "signed_count": 0,
        "lock_path": None,
        "lock_sha256": None,
    }
    assert acceptance["operator_waiver"] == {
        "status": "active",
        "requirement_waived": True,
        "human_signoff_claimed": False,
        "reviewer_identity_or_signature_claimed": False,
        "input_path": "experiments/step20/webarena_verified/operator_waiver.json",
        "input_sha256": native.file_sha256(
            ROOT / "experiments/step20/webarena_verified/operator_waiver.json"
        ),
        "lock_path": (
            "experiments/step20/webarena_verified/native_claims/locked/operator_waiver.json"
        ),
        "lock_sha256": native.file_sha256(PACKAGE / "locked/operator_waiver.json"),
    }
    assert acceptance["packet_index_agent_input_tree_sha256"] == (
        "98f4f404cae6e794bd2fa1d0c152d43b7fa5d6ee5bffea143a0c9c39ddd4c975"
    )
    assert acceptance["agent_input_tree_sha256_before"] == acceptance["agent_input_tree_sha256_after"]
    assert len(list((PACKAGE / "locked/contracts").glob("*/evidence_contract.json"))) == 812
    assert len(list((PACKAGE / "locked/checklists").glob("*/case_checklist.yaml"))) == 812
    assert len(list((PACKAGE / "locked/policy_locks").glob("*/policy_lock.json"))) == 812
    assert not (PACKAGE / "locked/reviews").exists()


def test_operator_waiver_receipt_is_hash_bound_and_reusable_by_scheduler() -> None:
    index = json.loads((PACKAGE / "index.json").read_text(encoding="utf-8"))
    input_lock = json.loads((PACKAGE / "input_lock.json").read_text(encoding="utf-8"))
    waiver = native.validate_operator_waiver_receipt(
        ROOT / "experiments/step20/webarena_verified/operator_waiver.json",
        input_lock=input_lock,
        input_lock_sha256=native.file_sha256(PACKAGE / "input_lock.json"),
        machine_lock_sha256=native.file_sha256(PACKAGE / "locks/machine_locks.jsonl"),
        entries=index["cases"],
    )
    assert waiver["human_signoff_claimed"] is False
    assert waiver["reviewer_identity_or_signature_claimed"] is False
    assert waiver["human_signed"] == 0
    assert waiver["machine_validated"] == 812
    assert waiver["fallback_contracts"] == 0
    assert waiver["execution_binding"] == native.EXPECTED_EXECUTION_BINDING

    first = index["cases"][0]
    assert first["human_signoff_status"] == "waived_not_signed"
    assert first["formal_lock_basis"] == native.OPERATOR_WAIVER_BASIS
    assert first["contract_review_path"] is None
    assert first["policy_lock_record_path"].endswith("/0/policy_lock.json")
    locked = json.loads(
        (PACKAGE / "locked/contracts/0/evidence_contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert locked["contract_status"] == "locked"
    assert locked["main_result_eligible"] is True
    assert locked["locked_by"] == "operator-machine-only-waiver-no-human-review"
    assert locked["source_support"]["formal_lock_basis"] == native.OPERATOR_WAIVER_BASIS
    assert locked["source_support"]["human_source_check_complete"] is False
    assert locked["source_support"]["human_signoff_claimed"] is False


@pytest.mark.parametrize(
    ("field_path", "replacement", "expected"),
    [
        (("human_signoff_claimed",), True, "violates schema"),
        (("human_signed",), 812, "violates schema"),
        (
            ("source_binding", "native_machine_lock_sha256"),
            "0" * 64,
            "source/machine binding mismatch",
        ),
        (
            ("execution_binding", "agents", 0, "model"),
            "openai/not-the-locked-model",
            "model/route/reset binding mismatch",
        ),
    ],
)
def test_operator_waiver_negative_controls_fail_closed(
    tmp_path: Path,
    field_path: tuple[str | int, ...],
    replacement: object,
    expected: str,
) -> None:
    waiver_path = ROOT / "experiments/step20/webarena_verified/operator_waiver.json"
    waiver = json.loads(waiver_path.read_text(encoding="utf-8"))
    target = waiver
    for part in field_path[:-1]:
        target = target[part]
    target[field_path[-1]] = replacement
    mutated = tmp_path / "mutated-waiver.json"
    mutated.write_text(json.dumps(waiver), encoding="utf-8")
    index = json.loads((PACKAGE / "index.json").read_text(encoding="utf-8"))
    input_lock = json.loads((PACKAGE / "input_lock.json").read_text(encoding="utf-8"))
    with pytest.raises(native.WebArenaNativeClaimError, match=expected):
        native.validate_operator_waiver_receipt(
            mutated,
            input_lock=input_lock,
            input_lock_sha256=native.file_sha256(PACKAGE / "input_lock.json"),
            machine_lock_sha256=native.file_sha256(
                PACKAGE / "locks/machine_locks.jsonl"
            ),
            entries=index["cases"],
        )


def test_full_812_ir_covers_every_agent_response_and_network_event_config() -> None:
    index = json.loads((PACKAGE / "index.json").read_text(encoding="utf-8"))
    assert index["path_scope"] == "repository_relative"
    assert index["package_root"] == "experiments/step20/webarena_verified/native_claims"
    assert [entry["case_unit_id"] for entry in index["cases"]] == [str(value) for value in range(812)]

    response_count = 0
    network_count = 0
    network_task_count = 0
    for task_id in range(812):
        ir = _ir(task_id)
        assert native.validate_native_ir(ir) == []
        evaluators = ir["native_semantics"]["evaluators"]
        names = [item["name"] for item in evaluators]
        response_count += names.count("AgentResponseEvaluator")
        network_count += names.count("NetworkEventEvaluator")
        network_task_count += "NetworkEventEvaluator" in names
        assert ir["native_semantics"]["evaluator_names_in_order"] == names
        assert ir["native_semantics"]["evaluator_count"] == len(evaluators)
        assert ir["native_semantics"]["composition"] == "all_evaluator_scores_must_equal_1.0"
    assert response_count == 812
    assert network_count == 663
    assert network_task_count == 488


def test_rendered_contract_and_checklist_preserve_network_semantics() -> None:
    ir = _ir(44)
    network = ir["native_semantics"]["evaluators"][1]
    assert network["name"] == "NetworkEventEvaluator"
    assert network["semantics"]["last_event_only"] is True
    assert network["semantics"]["should_not_exist"] is False
    assert network["semantics"]["decode_base64_query"] is False

    contract = json.loads(
        (PACKAGE / "drafts/contracts/44/evidence_contract.json").read_text(encoding="utf-8")
    )
    assert contract["schema_version"] == "evidence_contract/v1"
    assert contract["claim_scope"] == "native_aligned"
    assert contract["contract_status"] == "draft"
    assert contract["main_result_eligible"] is False
    assert len(contract["required_artifacts"]) == 4
    assert contract["source_support"]["task_revision"] == 2
    assert contract["source_support"]["evaluator_config_sha256"] == ir["source_binding"]["evaluator_config_sha256"]
    assert "every configured evaluator scores 1.0" in contract["claim_text"]
    assert "UNRESOLVE, never agent FAIL" in contract["unresolve_rule"]

    checklist = yaml.safe_load(
        (PACKAGE / "drafts/checklists/44/case_checklist.yaml").read_text(encoding="utf-8")
    )
    assert checklist["schema_version"] == "case_checklist_v1"
    assert len(checklist["native"]["success_if"]) == 3
    assert len(checklist["native"]["fail_if"]) == 3
    assert any("last_event_only=true" in item["text"] for item in checklist["native"]["success_if"])
    assert any("TaskEvalResult" in item["text"] for item in checklist["native"]["undecided_if"])
    assert checklist["stronger"]["additional_conditions"] == []


def test_general_contract_validator_accepts_pinned_deterministic_provenance_without_fake_llm_call() -> None:
    report = validate_contracts(
        contracts=[PACKAGE / "drafts/contracts/0/evidence_contract.json"],
        source_bundle_path=ROOT
        / "experiments/evidence_contracts/source_bundles/webarena_verified_full_812_source_bundle.json",
        llm_calls=[],
        formal=False,
    )
    assert report.status == "ok", [issue.to_dict() for issue in report.issues]
    assert report.llm_call_count == 0


def test_human_signed_deterministic_contract_can_formally_validate_without_fake_llm_call(
    tmp_path: Path,
) -> None:
    ir = _ir(0)
    signoff = {
        "review_id": "real-source-review-0",
        "reviewer_id": "reviewer-0",
        "review_started_at": "2026-07-16T00:00:00+00:00",
        "review_finished_at": "2026-07-16T00:10:00+00:00",
        "locked_at": "2026-07-16T00:11:00+00:00",
        "first_scoring_started_at": "2026-07-17T00:00:00+00:00",
    }
    contract_path = tmp_path / "locked.json"
    contract = native.render_contract(
        ir,
        output_path="experiments/step20/webarena_verified/native_claims/locked/contracts/0/evidence_contract.json",
        locked=signoff,
    )
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    review = native._contract_review(
        contract,
        signoff,
        source_bundle_hash=native.EXPECTED_SOURCE_BUNDLE_SHA256,
    )
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(review), encoding="utf-8")

    report = validate_contracts(
        contracts=[contract_path],
        review_records=[review_path],
        llm_calls=[],
        formal=True,
    )
    assert report.status == "ok", [issue.to_dict() for issue in report.issues]
    assert report.locked_contract_count == 1
    assert report.review_record_count == 1
    assert report.llm_call_count == 0


@pytest.mark.parametrize(
    ("mutator", "expected_issue"),
    [
        (
            lambda ir: ir["native_semantics"].__setitem__("composition", "any_evaluator_may_pass"),
            "all-evaluator AND composition is missing",
        ),
        (
            lambda ir: ir["native_semantics"]["evaluators"][1]["semantics"].__setitem__(
                "should_not_exist", True
            ),
            "lost NetworkEvent should_not_exist",
        ),
        (
            lambda ir: ir["native_semantics"]["evaluators"][0].__setitem__(
                "config_sha256", "0" * 64
            ),
            "config hash mismatch",
        ),
        (
            lambda ir: ir.__setitem__("required_artifacts", []),
            "required_artifacts must be nonempty",
        ),
    ],
)
def test_semantic_negative_controls_fail_closed(mutator, expected_issue: str) -> None:
    ir = copy.deepcopy(_ir(44))
    mutator(ir)
    assert any(expected_issue in issue for issue in native.validate_native_ir(ir))


def test_machine_record_cannot_be_submitted_as_human_signoff(tmp_path: Path) -> None:
    entry = {
        "case_unit_id": "0",
        "task_id": "0",
        "task_revision": 2,
        "native_ir_sha256": "1" * 64,
        "draft_contract_sha256": "2" * 64,
        "draft_checklist_sha256": "3" * 64,
        "machine_review_sha256": "4" * 64,
    }
    fake = {
        "schema_version": native.HUMAN_SIGNOFF_SCHEMA_VERSION,
        "domain": native.DOMAIN,
        "case_unit_id": "0",
        "task_id": "0",
        "task_revision": 2,
        "input_lock_sha256": "5" * 64,
        "native_ir_sha256": "1" * 64,
        "draft_contract_sha256": "2" * 64,
        "draft_checklist_sha256": "3" * 64,
        "machine_review_sha256": "4" * 64,
        "decision": "approve",
        "source_check_complete": False,
        "evaluator_semantics_complete": True,
        "artifact_requirements_accepted": True,
        "review_id": "machine-review",
        "reviewer_id": "machine",
        "review_started_at": "2026-07-16T00:00:00+00:00",
        "review_finished_at": "2026-07-16T00:01:00+00:00",
        "locked_at": "2026-07-16T00:02:00+00:00",
        "first_scoring_started_at": "2026-07-17T00:00:00+00:00",
    }
    path = tmp_path / "fake.jsonl"
    path.write_text(json.dumps(fake) + "\n", encoding="utf-8")
    with pytest.raises(native.WebArenaNativeClaimError, match="violates schema"):
        native._load_human_signoffs(path, [entry], "5" * 64)


def test_agent_input_start_url_drift_fails_closed(tmp_path: Path) -> None:
    task = {
        "intent": "Open my todos page",
        "intent_template_id": 303,
        "sites": ["gitlab"],
        "start_urls": ["__GITLAB__"],
        "task_id": 44,
    }
    payload = {
        "intent": task["intent"],
        "intent_template_id": task["intent_template_id"],
        "sites": task["sites"],
        "start_urls": ["http://attacker.invalid"],
        "task_id": 44,
    }
    path = tmp_path / "agent_input.json"
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(native.WebArenaNativeClaimError, match="field start_urls"):
        native._validate_agent_input(
            path,
            task,
            resolved_start_urls=["http://127.0.0.1:3000"],
            expected_file_sha256=native.file_sha256(path),
        )


def test_pinned_input_hash_drift_blocks_before_generation(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(native, "EXPECTED_PACKET_INDEX_SHA256", "0" * 64)
    with pytest.raises(native.WebArenaNativeClaimError, match="pinned canonical input hash mismatch"):
        native.build_native_claim_package(output_root=tmp_path / "must-not-be-created")
    assert not (tmp_path / "must-not-be-created").exists()


def test_incomplete_human_signoff_denominator_is_rejected(tmp_path: Path) -> None:
    base_entry = {
        "case_unit_id": "0",
        "task_id": "0",
        "task_revision": 2,
        "native_ir_sha256": "1" * 64,
        "draft_contract_sha256": "2" * 64,
        "draft_checklist_sha256": "3" * 64,
        "machine_review_sha256": "4" * 64,
    }
    second_entry = dict(base_entry, case_unit_id="1", task_id="1")
    signoff = {
        "schema_version": native.HUMAN_SIGNOFF_SCHEMA_VERSION,
        "domain": native.DOMAIN,
        "case_unit_id": "0",
        "task_id": "0",
        "task_revision": 2,
        "input_lock_sha256": "5" * 64,
        "native_ir_sha256": "1" * 64,
        "draft_contract_sha256": "2" * 64,
        "draft_checklist_sha256": "3" * 64,
        "machine_review_sha256": "4" * 64,
        "decision": "approve",
        "source_check_complete": True,
        "evaluator_semantics_complete": True,
        "artifact_requirements_accepted": True,
        "review_id": "review-0",
        "reviewer_id": "reviewer-0",
        "review_started_at": "2026-07-16T00:00:00+00:00",
        "review_finished_at": "2026-07-16T00:01:00+00:00",
        "locked_at": "2026-07-16T00:02:00+00:00",
        "first_scoring_started_at": "2026-07-17T00:00:00+00:00",
    }
    path = tmp_path / "one-of-two.jsonl"
    path.write_text(json.dumps(signoff) + "\n", encoding="utf-8")
    with pytest.raises(native.WebArenaNativeClaimError, match="exact human signoff denominator 2"):
        native._load_human_signoffs(path, [base_entry, second_entry], "5" * 64)
