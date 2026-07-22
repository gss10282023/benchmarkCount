from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from neurips_ed_track_minimal.scripts import score_evidence_blind_with_codex as blind
from scripts import audit_join_appworld68_blind_scores as audit


REPO_ROOT = Path(__file__).resolve().parents[2]
FREEZE_ROOT = (
    REPO_ROOT
    / "experiments"
    / "appworld_test_normal_68_system_design_v3_gpt54_high_v1"
    / "claim_freeze"
    / "checklists"
)


def test_frozen_denominators_are_exact() -> None:
    checklist_paths = sorted(FREEZE_ROOT.glob("*/checklist.yaml"))
    assert len(checklist_paths) == audit.EXPECTED_CASES
    native = 0
    stronger = 0
    for path in checklist_paths:
        checklist = yaml.safe_load(path.read_text(encoding="utf-8"))
        native += len(audit.registered_test_ids(checklist)) * len(audit.EXPECTED_AGENTS)
        stronger += len(checklist["stronger"]["additional_conditions"]) * len(
            audit.EXPECTED_AGENTS
        )
    assert native == audit.EXPECTED_NATIVE_CHECKS == 1_407
    assert stronger == audit.EXPECTED_STRONGER_CHECKS == 132


@pytest.mark.parametrize(
    ("statuses", "empty", "expected"),
    [
        (["supported", "supported"], "U", "S"),
        (["supported", "undecided"], "U", "U"),
        (["undecided", "contradicted"], "U", "F"),
        ([], "NA", "NA"),
    ],
)
def test_deterministic_aggregation(
    statuses: list[str], empty: str, expected: str
) -> None:
    assert audit.aggregate(statuses, no_items=empty) == expected


def test_pointer_resolution_and_forbidden_result_rejection(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "evidence").mkdir(parents=True)
    (task / "checklist.yaml").write_text(
        "native:\n  success_if:\n    - text: ok\n", encoding="utf-8"
    )
    (task / "evidence" / "state.json").write_text(
        json.dumps({"rows": [{"ok": True}]}) + "\n", encoding="utf-8"
    )
    (task / "evidence" / "trace.jsonl").write_text(
        '{"event": 1}\n{"event": 2}\n', encoding="utf-8"
    )
    assert (
        audit.validate_pointer(
            task, "evidence/state.json::$.rows[0].ok", "test"
        )
        == "evidence/state.json"
    )
    assert (
        audit.validate_pointer(task, "evidence/trace.jsonl::L2", "test")
        == "evidence/trace.jsonl"
    )
    (task / "evidence" / "native_evaluator_output.json").write_text(
        '{"tracker":{"success":true}}\n', encoding="utf-8"
    )
    with pytest.raises(audit.AuditError, match="forbidden"):
        audit.validate_pointer(
            task,
            "evidence/native_evaluator_output.json::$.tracker.success",
            "test",
        )


def test_joined_mismatch_is_only_a_review_route() -> None:
    value = audit.joined_record(
        task_id="abc_1__agent_a",
        record={"case_unit_id": "abc_1", "agent_id": "agent_a"},
        score={
            "native": {
                "verdict": "U",
                "reason": "insufficient",
                "pointers": ["checklist.yaml::native.undecided_if[0]"],
                "test_checks": [],
            },
            "stronger": {
                "verdict": "F",
                "reason": "independent",
                "pointers": ["checklist.yaml::stronger.additional_conditions[0]"],
                "condition_checks": [],
            },
        },
        label={"value": "success"},
        score_sha="0" * 64,
    )
    assert value["comparison"]["status"] == "mismatch"
    assert value["benchmark_conflict_review"]["status"] == "not_assessed"
    assert value["benchmark_conflict_review"]["automatic_inference_prohibited"]


def test_exact_execution_config_is_fail_closed() -> None:
    valid = {
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "service_tier": "default",
        "fast_mode": False,
        "sandbox": "read-only",
        "max_parallel": 34,
        "auth_mode": "codex_login",
    }
    audit.validate_scoring_config(valid, "test")
    with pytest.raises(audit.AuditError, match="fast_mode"):
        audit.validate_scoring_config({**valid, "fast_mode": True}, "test")
    with pytest.raises(audit.AuditError, match="parallelism"):
        audit.validate_scoring_config({**valid, "max_parallel": 33}, "test")


def test_record_lock_chain_and_pointer_audit_integration(tmp_path: Path) -> None:
    input_task = tmp_path / "input" / "case_1__agent_a"
    score_dir = tmp_path / "scores" / "case_1__agent_a"
    (input_task / "evidence").mkdir(parents=True)
    score_dir.mkdir(parents=True)
    checklist = {
        "schema_version": "case_checklist_v1",
        "case_unit_id": "case_1",
        "domain": "appworld",
        "task_id": "case_1",
        "native": {
            "success_if": [{"text": "[appworld_test_001_aaaa] passes"}],
            "fail_if": [{"text": "[appworld_test_001_aaaa] fails"}],
            "undecided_if": [{"text": "missing evidence"}],
        },
        "stronger": {"additional_conditions": []},
    }
    checklist_path = input_task / "checklist.yaml"
    checklist_path.write_text(
        yaml.safe_dump(checklist, sort_keys=False), encoding="utf-8"
    )
    evidence_path = input_task / "evidence" / "run" / "state.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text('{"ok":true}\n', encoding="utf-8")
    pointers = [
        "checklist.yaml::native.success_if[0]",
        "evidence/run/state.json::$.ok",
    ]
    native = {
        "verdict": "S",
        "reason": "retained evidence supports the registered test",
        "pointers": pointers,
        "test_checks": [
            {
                "id": "appworld_test_001_aaaa",
                "status": "supported",
                "reason": "retained evidence supports the registered test",
                "pointers": pointers,
            }
        ],
    }
    stronger = {
        "verdict": "NA",
        "reason": "no stronger conditions",
        "pointers": ["checklist.yaml::stronger.additional_conditions"],
        "condition_checks": [],
    }
    score = {
        "schema_version": "blind_evidence_score_v1",
        "case_unit_id": "case_1",
        "blind_mode": True,
        "native": native,
        "stronger": stronger,
    }

    def write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    write_json(score_dir / "score.json", score)
    (score_dir / "score.yaml").write_text(
        yaml.safe_dump(score, sort_keys=False), encoding="utf-8"
    )
    write_json(score_dir / "score.native.blind.json", {"native": native})
    write_json(score_dir / "score.stronger.blind.json", {"stronger": stronger})
    for stage in ("native", "stronger"):
        write_json(score_dir / f"score.{stage}.output_schema.json", {"type": "object"})

    identity = blind.RestrictedIdentity(
        username="score-blind", uid=1234, groupname="score-blind", gid=1234
    )
    evidence_sha = blind.sha256_tree(input_task / "evidence")
    for stage, prompt in (
        ("native", blind.NATIVE_PROMPT_PATH),
        ("stronger", blind.STRONGER_PROMPT_PATH),
    ):
        lock = blind.build_stage_lock(
            stage=stage,
            stage_score_path=score_dir / f"score.{stage}.blind.json",
            checklist_path=checklist_path,
            evidence_dir=input_task / "evidence",
            evidence_tree_sha256=evidence_sha,
            prompt_path=prompt,
            schema_path=score_dir / f"score.{stage}.output_schema.json",
            model="gpt-5.4",
            reasoning_effort="high",
            service_tier="default",
            restricted_identity=identity,
        )
        write_json(score_dir / f"score.{stage}.lock.json", lock)

    bind = lambda path: blind.artifact_binding(path, relative_to=score_dir)
    final_lock = {
        "schema_version": "blind_score_lock_v1",
        "case_unit_id": "case_1",
        "blind_mode": True,
        "released_evaluator_label_resolved": False,
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "service_tier": "default",
        "fast_mode": False,
        "auth_mode": "codex_login",
        "sandbox": "read-only",
        "model_stage_isolation": {
            "invocation_order": ["stronger", "native"],
            "stage_outputs_published_after_all_model_invocations": True,
            "cross_stage_output_visibility": False,
        },
        "score": bind(score_dir / "score.json"),
        "score_yaml": bind(score_dir / "score.yaml"),
        "native_stage_lock": bind(score_dir / "score.native.lock.json"),
        "stronger_stage_lock": bind(score_dir / "score.stronger.lock.json"),
        "checklist": bind(checklist_path),
        "evidence_tree_sha256": evidence_sha,
        "final_schema": bind(blind.FINAL_SCHEMA_PATH),
    }
    write_json(score_dir / "score.blind_lock.json", final_lock)
    auth = {
        "mode": "codex_login",
        "isolated_codex_home": True,
        "auth_json_present": True,
        "api_credential_environment_present": False,
        "batch_login_marker_verified": True,
        "restricted_os_user": identity.username,
        "restricted_uid": identity.uid,
        "restricted_group": identity.groupname,
        "restricted_gid": identity.gid,
        "forbidden_root_canary_count": 3,
        "forbidden_root_canary_passed": True,
    }
    stage_isolation = {
        "invocation_order": ["stronger", "native"],
        "separate_temporary_workspaces": True,
        "temporary_stage_outputs_deleted_before_next_invocation": True,
        "final_score_directory_empty_during_model_invocations": True,
        "all_stage_artifacts_published_after_all_model_invocations": True,
        "stronger_received_native_output": False,
        "native_received_stronger_output": False,
    }
    manifest = {
        "schema_version": "blind_score_manifest_v1",
        "case_unit_id": "case_1",
        "task_id": "case_1",
        "score_task_id": "case_1__agent_a",
        "agent_id": "agent_a",
        "blind_mode": True,
        "released_label_handling": {
            "required_by_scorer": False,
            "resolved_before_or_during_scoring": False,
            "included_in_model_workspaces": False,
            "included_in_score": False,
        },
        "model_stage_isolation": stage_isolation,
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "service_tier": "default",
        "fast_mode": False,
        "auth": auth,
        "checklist": bind(checklist_path),
        "evidence": {"tree_sha256": evidence_sha},
        "prompts": {
            "native": bind(blind.NATIVE_PROMPT_PATH),
            "stronger": bind(blind.STRONGER_PROMPT_PATH),
        },
        "schemas": {
            "native_model_output": bind(
                score_dir / "score.native.output_schema.json"
            ),
            "stronger_model_output": bind(
                score_dir / "score.stronger.output_schema.json"
            ),
            "final_blind_score": bind(blind.FINAL_SCHEMA_PATH),
        },
        "stages": {
            stage: {
                "score": bind(score_dir / f"score.{stage}.blind.json"),
                "lock": bind(score_dir / f"score.{stage}.lock.json"),
            }
            for stage in ("native", "stronger")
        },
        "outputs": {
            "json": bind(score_dir / "score.json"),
            "yaml": bind(score_dir / "score.yaml"),
            "blind_lock": bind(score_dir / "score.blind_lock.json"),
        },
    }
    write_json(score_dir / "score_manifest.json", manifest)
    restricted = {
        "username": identity.username,
        "uid": identity.uid,
        "groupname": identity.groupname,
        "gid": identity.gid,
        "orchestrator_uid": 0,
    }
    transfer = {
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "service_tier": "default",
        "fast_mode": False,
        "sandbox": "read-only",
        "max_parallel": 34,
        "auth_mode": "codex_login",
        "restricted_model_identity": restricted,
        "score_prompts": {
            "native": bind(blind.NATIVE_PROMPT_PATH),
            "stronger": bind(blind.STRONGER_PROMPT_PATH),
        },
        "score_schema": bind(blind.FINAL_SCHEMA_PATH),
    }
    checked, native_count, stronger_count = audit.validate_record_score(
        task_id="case_1__agent_a",
        task_dir=score_dir,
        input_task_dir=input_task,
        record={"case_unit_id": "case_1", "agent_id": "agent_a"},
        transfer=transfer,
        expected_evidence_sha=evidence_sha,
    )
    assert checked == score
    assert (native_count, stronger_count) == (1, 0)
