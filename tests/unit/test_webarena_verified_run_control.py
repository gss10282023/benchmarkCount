from __future__ import annotations

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

from evidence_system.orchestrator.webarena_verified_full import (
    EXPECTED_AGENT_IDS,
    EXPECTED_ROUTES,
    FullSchedulePlan,
    RESULT_NAMESPACE,
)
from evidence_system.orchestrator import webarena_verified_run_control as control


def test_locked_full_index_has_exact_three_lane_product() -> None:
    jobs, index, _ = control.load_full_jobs()

    assert len(jobs) == 2436
    assert index["job_count"] == 2436
    assert index["result_namespace"] == RESULT_NAMESPACE
    assert [job["record_slot_id"] for job in jobs[:3]] == [
        "wv123-task-000-agent-a",
        "wv123-task-000-agent-b",
        "wv123-task-000-agent-c",
    ]
    for agent_id in EXPECTED_AGENT_IDS:
        lane = [job for job in jobs if job["agent_id"] == agent_id]
        assert len(lane) == 812
        assert [int(job["task_id"]) for job in lane] == list(range(812))
        assert all(job["execution_target"] == EXPECTED_ROUTES[agent_id] for job in lane)
        assert all(job["reset_policy"] == "recreate_task_sites_from_digest_v1" for job in lane)


def test_materialized_full_plan_uses_only_hash_checked_jobs() -> None:
    plan = control.load_materialized_full_plan()

    assert len(plan.jobs) == 2436
    assert plan.acceptance["status"] == "pass"
    assert plan.acceptance["formal_launch_eligible"] is True
    assert plan.acceptance["plan_source"] == "hash_checked_materialized_full_jobs_index"
    assert plan.acceptance["legacy_native_claim_compiler_runtime_dependency"] is False
    assert plan.acceptance["formal_score_draft_provider"] == "neurips_ed_track_minimal"
    assert plan.acceptance["jobs_index"]["jobs_sha256"] == (
        "5c613b729e96ac020b9e2a8d5cdba667371f086be7c5cad4e46292d9a349e704"
    )


def test_pilot_monitor_derives_exact_24_slots_without_writing() -> None:
    snapshot = control.monitor_namespace(mode="pilot", write_outputs=False)

    assert len(snapshot.jobs) == 24
    assert snapshot.progress["counts"]["expected"] == 24
    assert sum(
        snapshot.progress["counts"][key]
        for key in ("canonical_reusable", "pending", "in_progress", "settled_invalid")
    ) == 24
    assert snapshot.progress["monitor_guarantees"] == {
        "slot_result_trees_read_only": True,
        "slot_locks_acquired": 0,
        "workers_stopped_or_killed": 0,
        "scores_changed": 0,
        "reruns_triggered": 0,
        "issues_are_needs_review_only": True,
        "credential_values_or_hashes_recorded": False,
        "dotenv_read": False,
    }


def test_remote_canonical_receipts_feed_full_monitor_semantic_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs, _index, index_path = control.load_full_jobs()
    by_server = {
        str(route["server_id"]): tuple(
            job
            for job in jobs
            if dict(job["execution_target"])["server_id"] == route["server_id"]
        )
        for route in EXPECTED_ROUTES.values()
    }
    index_sha256 = control.sha256_file(index_path)

    def fake_target(job: dict[str, Any], **_: Any) -> SimpleNamespace:
        route = dict(job["execution_target"])
        return SimpleNamespace(
            machine_id=str(route["server_id"]),
            runner_command="python3",
            ssh_user="root",
            ssh_host=str(route["ssh_host"]),
        )

    def fake_remote(target: SimpleNamespace, _command: str, **_: Any) -> Any:
        audits = []
        for job in by_server[target.machine_id]:
            canonical = int(job["task_id"]) == 0
            audit = {
                "status": "pass",
                "state": "canonical_reusable" if canonical else "pending",
                "record_slot_id": job["record_slot_id"],
                "persistent_adapter_root": f"/persistent/{job['record_slot_id']}",
                "verified_over_ssh": True,
            }
            if canonical:
                audit.update(
                    {
                        "remote_slot_acceptance_sha256": "1" * 64,
                        "remote_artifact_manifest_sha256": "2" * 64,
                        "remote_security_acceptance_sha256": "3" * 64,
                        "remote_evaluator_receipt_sha256": "4" * 64,
                        "score": 1.0,
                    }
                )
            audits.append(audit)
        payload = {
            "status": "pass",
            "server_id": target.machine_id,
            "slot_count": 812,
            "jobs_index_sha256": index_sha256,
            "verified_over_ssh": True,
            "artifact_files_rehashed": False,
            "audits": audits,
        }
        return subprocess.CompletedProcess(
            args=(), returncode=0, stdout=json.dumps(payload), stderr=""
        )

    ssh_key = tmp_path / "id_ed25519"
    ssh_key.write_text("unit-test-only\n", encoding="utf-8")
    monkeypatch.setattr(control, "_remote_audit_target", fake_target)
    monkeypatch.setattr(control, "run_remote_blind_command", fake_remote)

    snapshot = control.monitor_namespace(
        mode="full",
        ssh_key_path=ssh_key,
        remote_verify_files=False,
        write_outputs=False,
    )

    assert snapshot.progress["counts"]["canonical_reusable"] == 3
    semantic = snapshot.progress["semantic_case_review"]
    assert semantic["reviewed_slot_count"] == 3
    assert semantic["reviewed_task_count"] == 1
    assert semantic["tasks_reviewed_for_all_three_agents"] == [0]
    assert {
        (receipt["task_id"], receipt["agent_id"])
        for receipt in semantic["review_receipts"]
    } == {(0, agent_id) for agent_id in EXPECTED_AGENT_IDS}


def test_empty_preflight_scaffold_is_not_counted_as_a_slot_attempt(
    tmp_path: Path,
) -> None:
    root = tmp_path / "adapter"
    for relative in ("llm_calls", "logs", "native_run"):
        (root / relative).mkdir(parents=True)

    assert control._is_empty_prelaunch_scaffold(root) is True
    (root / "logs" / "sync.stderr.log").write_text("failed\n", encoding="utf-8")
    assert control._is_empty_prelaunch_scaffold(root) is False


def test_issue_id_and_ledger_are_idempotent() -> None:
    job = _job(0, "Agent A")
    first = control._issue(
        job,
        classification="potential_case_issue",
        circuit_class="none",
        signature="example_case_question",
        summary="case requires human review",
        evidence_paths=(),
    )
    second = control._issue(
        job,
        classification="potential_case_issue",
        circuit_class="none",
        signature="example_case_question",
        summary="case requires human review",
        evidence_paths=(),
    )

    assert first == second
    assert control._ledger_bytes((first,)) == control._ledger_bytes((second,))
    assert first["needs_review"] is True
    assert first["case_defect_concluded"] is False
    assert first["interrupt_requested"] is False
    assert first["score_mutation_requested"] is False
    assert first["rerun_requested"] is False


def test_paid_full_confirmation_is_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(control.WebArenaRunControlError, match="exact confirmation"):
        control.execute_resumable_full_schedule(
            FullSchedulePlan(jobs=(), acceptance={}),
            ssh_key_path=tmp_path / "unused",
            confirm_paid_full="wrong",
        )


def test_resumable_wrapper_continues_after_one_isolated_infra_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, agent) for task_id, agent in enumerate(EXPECTED_AGENT_IDS))
    snapshot = _snapshot(jobs, reusable={jobs[1]["record_slot_id"], jobs[2]["record_slot_id"]})
    real_calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None)

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            result = adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
            assert result["status"] == "completed"
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_planner(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        return {"status": "runnable", "runner_command": "fake"}

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        real_calls.append(str(job["record_slot_id"]))
        raise TimeoutError("worker timed out")

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=fake_planner,
        adapter_executor=fake_executor,
    )

    assert real_calls == [jobs[0]["record_slot_id"]]
    assert result["status"] == "partial_resumable"
    assert result["execution_counts"] == {
        "reused": 2,
        "runtime_issue": 1,
    }
    assert result["in_flight_worker_interrupted"] is False
    assert result["score_mutation_performed"] is False


def test_post_run_remote_audit_outage_is_deferred_without_stopping_lanes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent A") for task_id in range(2))
    snapshot = _snapshot(jobs, reusable=set())
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        control,
        "audit_remote_slot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("transient ssh")),
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            result = adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
            assert result["status"] == "completed"
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(job["record_slot_id"]))
        return {"status": "completed", "record_slot_id": job["record_slot_id"]}

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=fake_executor,
    )

    assert calls == [job["record_slot_id"] for job in jobs]
    assert result["execution_counts"] == {"post_run_remote_audit_deferred": 2}


def test_resumable_wrapper_records_three_consecutive_infra_below_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent A") for task_id in range(3))
    snapshot = _snapshot(jobs, reusable=set())
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None)

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(job["record_slot_id"]))
        raise TimeoutError("worker timed out")

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=fake_executor,
    )

    assert calls == [job["record_slot_id"] for job in jobs]
    assert result["status"] == "partial_resumable"
    assert result["execution_counts"] == {"runtime_issue": 3}
    assert control.CONSECUTIVE_LANE_FAILURE_THRESHOLD == 4


def test_four_consecutive_runtime_failures_open_shared_circuit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent A") for task_id in range(5))
    snapshot = _snapshot(jobs, reusable=set())
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(job["record_slot_id"]))
        raise TimeoutError("worker timed out")

    with pytest.raises(control.WebArenaRunControlError, match="circuit opened"):
        control.execute_resumable_full_schedule(
            FullSchedulePlan(jobs=jobs, acceptance={}),
            ssh_key_path="unused",
            confirm_paid_full=control.PAID_FULL_CONFIRMATION,
            adapter_planner=lambda _job, **_kwargs: {
                "status": "runnable",
                "runner_command": "fake",
            },
            adapter_executor=fake_executor,
        )

    assert calls == [job["record_slot_id"] for job in jobs[:4]]


def test_single_reset_failure_is_recorded_without_opening_shared_circuit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent B") for task_id in range(3))
    snapshot = _snapshot(jobs, reusable=set())
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        control,
        "audit_remote_slot",
        lambda job, **_: control.SlotAudit(
            record_slot_id=str(job["record_slot_id"]),
            state="canonical_reusable",
            reusable=True,
            issues=(),
            artifact_root="unused",
        ),
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(job["record_slot_id"]))
        if int(job["task_id"]) == 0:
            raise RuntimeError("slot reset receipt status=fail")
        return {"status": "completed"}

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=fake_executor,
    )

    assert calls == [job["record_slot_id"] for job in jobs]
    assert result["status"] == "partial_resumable"
    assert result["execution_counts"] == {
        "executed_canonical": 2,
        "runtime_issue": 1,
    }
    assert "reset" not in control.IMMEDIATE_CIRCUIT_CLASSES
    assert control.CONSECUTIVE_CONTROLLER_FAILURE_THRESHOLD == 3


def test_three_controller_preflight_failures_open_shared_circuit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent A") for task_id in range(4))
    snapshot = _snapshot(jobs, reusable=set())
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(control, "_existing_slot_evidence_paths", lambda _job: ())

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fail_before_evidence(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(job["record_slot_id"]))
        raise RuntimeError("controller support snapshot failed")

    with pytest.raises(control.WebArenaRunControlError, match="circuit opened"):
        control.execute_resumable_full_schedule(
            FullSchedulePlan(jobs=jobs, acceptance={}),
            ssh_key_path="unused",
            confirm_paid_full=control.PAID_FULL_CONFIRMATION,
            adapter_planner=lambda _job, **_kwargs: {
                "status": "runnable",
                "runner_command": "fake",
            },
            adapter_executor=fail_before_evidence,
        )

    assert calls == [job["record_slot_id"] for job in jobs[:3]]


def test_resume_skips_previously_recorded_issue_without_paid_rerun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent B") for task_id in range(2))
    issue = control._issue(
        jobs[0],
        classification="infra",
        circuit_class="reset",
        signature="slot_reset_failure",
        summary="mandatory pre-slot environment reset failed",
        evidence_paths=(),
    )
    base = _snapshot(jobs, reusable=set())
    audits = list(base.audits)
    audits[0] = control.SlotAudit(
        record_slot_id=str(jobs[0]["record_slot_id"]),
        state="in_progress",
        reusable=False,
        issues=(issue,),
        artifact_root="remote",
    )
    snapshot = control.MonitorSnapshot(
        jobs=jobs,
        audits=tuple(audits),
        issues=(issue,),
        progress=base.progress,
    )
    real_executor_calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        real_executor_calls.append(str(job["record_slot_id"]))
        raise TimeoutError("worker timed out")

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=fake_executor,
    )

    assert real_executor_calls == [jobs[1]["record_slot_id"]]
    assert result["execution_counts"] == {
        "record_only_issue_skipped": 1,
        "runtime_issue": 1,
    }


def test_resume_runs_pending_controller_only_issue_without_paid_rerun_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _job(250, "Agent A")
    issue = control._issue(
        job,
        classification="infra",
        circuit_class="infra",
        signature="unclassified_runtime_failure",
        summary="historical controller failure before remote slot evidence",
        evidence_paths=(),
    )
    base = _snapshot((job,), reusable=set())
    pending = control.SlotAudit(
        record_slot_id=str(job["record_slot_id"]),
        state="pending",
        reusable=False,
        issues=(),
        artifact_root="remote",
    )
    snapshot = control.MonitorSnapshot(
        jobs=(job,),
        audits=(pending,),
        issues=(issue,),
        progress=base.progress,
    )
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control,
        "audit_remote_slot",
        lambda planned_job, **_: control.SlotAudit(
            record_slot_id=str(planned_job["record_slot_id"]),
            state="canonical_reusable",
            reusable=True,
            issues=(),
            artifact_root="remote",
        ),
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        execution_plan = adapter_planner(plan.jobs[0], target=object())
        adapter_executor(
            plan.jobs[0],
            target=object(),
            execution_plan=execution_plan,
            context=object(),
        )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=(job,), acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda planned_job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=lambda planned_job, **_kwargs: calls.append(
            str(planned_job["record_slot_id"])
        )
        or {"status": "completed"},
    )

    assert calls == [job["record_slot_id"]]
    assert result["execution_counts"] == {"executed_canonical": 1}


def test_resumable_wrapper_does_not_combine_infra_failures_across_lanes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, agent) for task_id, agent in enumerate(EXPECTED_AGENT_IDS))
    snapshot = _snapshot(jobs, reusable=set())
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None)

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(job["record_slot_id"]))
        raise TimeoutError("worker timed out")

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=fake_executor,
    )

    assert calls == [job["record_slot_id"] for job in jobs]
    assert result["status"] == "partial_resumable"
    assert result["execution_counts"] == {"runtime_issue": 3}


def test_canonical_slot_resets_same_lane_failure_streak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent A") for task_id in range(3))
    snapshot = _snapshot(jobs, reusable=set())
    calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        control,
        "audit_remote_slot",
        lambda job, **_: control.SlotAudit(
            record_slot_id=str(job["record_slot_id"]),
            state="canonical_reusable",
            reusable=True,
            issues=(),
            artifact_root="unused",
        ),
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for job in plan.jobs:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fake_executor(job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(job["record_slot_id"]))
        if int(job["task_id"]) in {0, 2}:
            raise TimeoutError("worker timed out")
        return {"status": "completed"}

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=fake_executor,
    )

    assert calls == [job["record_slot_id"] for job in jobs]
    assert result["execution_counts"] == {
        "executed_canonical": 1,
        "runtime_issue": 2,
    }


def test_semantic_review_clusters_common_anomaly_without_circuit_action() -> None:
    jobs = tuple(_job(0, agent) for agent in EXPECTED_AGENT_IDS)
    issues = tuple(
        control._issue(
            job,
            classification="potential_case_issue",
            circuit_class="none",
            signature="locked_start_url_not_found",
            summary="review-only start URL observation",
            evidence_paths=(),
            details={"semantic_category": "start_page_reachability"},
        )
        for job in jobs
    )
    audits = tuple(
        control.SlotAudit(
            record_slot_id=str(job["record_slot_id"]),
            state="canonical_reusable",
            reusable=True,
            issues=(issue,),
            artifact_root="unused",
            semantic_review={
                "task_id": 0,
                "agent_id": job["agent_id"],
                "review_receipt_sha256": str(index) * 64,
            },
        )
        for index, (job, issue) in enumerate(zip(jobs, issues, strict=True), start=1)
    )

    progress = control._semantic_review_progress(audits, issues)

    assert progress["reviewed_slot_count"] == 3
    assert progress["tasks_reviewed_for_all_three_agents"] == [0]
    assert progress["semantic_findings_trip_executor_circuit"] is False
    assert progress["case_defect_concluded_by_monitor"] is False
    clusters = progress["cross_agent_common_anomaly_clusters"]
    assert len(clusters) == 1
    assert clusters[0]["observed_in_all_three_agents"] is True
    assert clusters[0]["needs_review"] is True
    assert clusters[0]["interrupt_requested"] is False
    assert clusters[0]["score_mutation_requested"] is False
    assert clusters[0]["rerun_requested"] is False


def test_remote_terminal_failure_becomes_resumable_infra_issue() -> None:
    job = _job(63, "Agent B")
    issue = control._remote_terminal_failure_issue(
        job,
        {
            "terminal_failure_observed": True,
            "terminal_failure_code": "playwright_trace_security_scan_failed",
            "run_summary_sha256": "a" * 64,
        },
    )

    assert issue is not None
    assert issue["record_slot_id"] == job["record_slot_id"]
    assert issue["classification"] == "infra"
    assert issue["circuit_class"] == "infra"
    assert issue["signature"] == "unclassified_runtime_failure"
    assert issue["details"] == {
        "remote_terminal_failure_code": "playwright_trace_security_scan_failed",
        "remote_run_summary_sha256": "a" * 64,
    }


def test_remote_billing_failure_opens_immediate_credential_circuit() -> None:
    job = _job(63, "Agent B")
    issue = control._remote_terminal_failure_issue(
        job,
        {
            "terminal_failure_observed": True,
            "terminal_failure_code": "credential_or_billing_failure",
            "run_summary_sha256": "a" * 64,
        },
    )

    assert issue is not None
    assert issue["classification"] == "systemic"
    assert issue["circuit_class"] == "credential"
    assert issue["signature"] == "credential_or_billing_failure"


def test_remote_terminal_failure_rejects_malformed_public_envelope() -> None:
    issue = control._remote_terminal_failure_issue(
        _job(63, "Agent B"),
        {
            "terminal_failure_observed": True,
            "terminal_failure_code": "unsafe value with spaces",
            "run_summary_sha256": "not-a-hash",
        },
    )

    assert issue is not None
    assert issue["classification"] == "systemic"
    assert issue["circuit_class"] == "systemic"
    assert issue["signature"] == "remote_terminal_failure_envelope_invalid"


def test_completed_unsealed_remote_runtime_is_deferred_without_circuit() -> None:
    job = _job(63, "Agent B")
    issue = control._remote_completed_unsealed_issue(
        job,
        {
            "runtime_completed_unsealed": True,
            "run_summary_sha256": "a" * 64,
        },
    )

    assert issue is not None
    assert issue["classification"] == "infra"
    assert issue["circuit_class"] == "none"
    assert issue["signature"] == "post_run_audit_deferred_for_full_sweep"


def test_resumable_wrapper_seals_completed_slot_without_paid_rerun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _job(63, "Agent B")
    issue = control._remote_completed_unsealed_issue(
        job,
        {
            "runtime_completed_unsealed": True,
            "run_summary_sha256": "a" * 64,
        },
    )
    assert issue is not None
    audit = control.SlotAudit(
        record_slot_id=str(job["record_slot_id"]),
        state="in_progress",
        reusable=False,
        issues=(issue,),
        artifact_root="remote",
    )
    progress = _snapshot((job,), reusable=set()).progress
    snapshot = control.MonitorSnapshot(
        jobs=(job,), audits=(audit,), issues=(issue,), progress=progress
    )
    planner_calls: list[str] = []
    executor_calls: list[str] = []
    reconciler_calls: list[str] = []

    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        execution_plan = adapter_planner(plan.jobs[0], target=object())
        result = adapter_executor(
            plan.jobs[0],
            target=object(),
            execution_plan=execution_plan,
            context=object(),
        )
        assert result["paid_runtime_replayed"] is False
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=(job,), acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        adapter_planner=lambda planned_job, **_kwargs: planner_calls.append(
            str(planned_job["record_slot_id"])
        )
        or {"status": "runnable", "runner_command": "paid"},
        adapter_executor=lambda planned_job, **_kwargs: executor_calls.append(
            str(planned_job["record_slot_id"])
        )
        or {"status": "completed"},
        adapter_reconciler=lambda planned_job, **_kwargs: reconciler_calls.append(
            str(planned_job["record_slot_id"])
        )
        or {
            "status": "completed",
            "paid_runtime_replayed": False,
            "post_run_reconciliation": "sealed_completed_runtime",
        },
    )

    assert planner_calls == [str(job["record_slot_id"])]
    assert executor_calls == []
    assert reconciler_calls == [str(job["record_slot_id"])]
    assert result["execution_counts"] == {"post_run_reconciled": 1}


def test_circuit_recovery_receipt_preserves_raw_history_and_is_hash_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs, _index, index_path = control.load_full_jobs()
    job = dict(jobs[0])
    issue = control._issue(
        job,
        classification="infra",
        circuit_class="infra",
        signature="unclassified_runtime_failure",
        summary="terminal remote worker failure requires recovery",
        evidence_paths=(),
    )
    circuit = {
        "tripped": True,
        "tripped_lanes": ["Agent A"],
        "immediate_classes_observed": [],
        "consecutive_lane_failure_streaks": [
            {
                "agent_id": "Agent A",
                "count": 3,
                "record_slot_ids": [job["record_slot_id"]],
            }
        ],
    }
    progress = {
        "counts": {
            "canonical_reusable": 163,
            "expected": 2436,
            "pending": 2268,
            "in_progress": 1,
            "settled_invalid": 4,
            "issues": 1,
        },
        "circuit_breaker": circuit,
        "ledger": {"sha256": "a" * 64, "entry_count": 1},
    }
    snapshot = control.MonitorSnapshot(
        jobs=(job,),
        audits=(
            control.SlotAudit(
                record_slot_id=str(job["record_slot_id"]),
                state="in_progress",
                reusable=False,
                issues=(issue,),
                artifact_root="remote",
            ),
        ),
        issues=(issue,),
        progress=progress,
    )
    canary_path = _receipt(tmp_path / "trace-heavy-canary.json", {"status": "pass"})
    junit_path = tmp_path / "targeted.xml"
    junit_path.write_text(
        '<testsuite tests="3" failures="0" errors="0">'
        + "".join(
            f'<testcase name="{name}"/>'
            for name in sorted(control.REQUIRED_RECOVERY_TEST_CASES)
        )
        + "</testsuite>\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        control,
        "_trace_heavy_recovery_canary_gate",
        lambda path: {
            "status": "pass",
            "path": control._display_path(control.resolve_repo_path(path)),
            "sha256": control.sha256_file(control.resolve_repo_path(path)),
        },
    )
    monkeypatch.setattr(
        control,
        "_live_quiescence",
        lambda **_: _quiescence_receipt(),
    )
    receipt_path = tmp_path / "recovery.json"

    issued = control.build_circuit_recovery_receipt(
        snapshot=snapshot,
        jobs_index_path=index_path,
        trace_heavy_canary_acceptance_path=canary_path,
        junit_report_path=junit_path,
        ssh_key_path=tmp_path / "unused-key",
        confirmation=control.CIRCUIT_RECOVERY_ISSUE_CONFIRMATION,
        output_path=receipt_path,
    )

    assert issued["trigger"]["raw_circuit_breaker"] == circuit
    assert issued["policy"]["raw_circuit_history_preserved"] is True
    assert issued["policy"]["issue_ledger_preserved"] is True
    assert control._circuit_recovery_gate(
        path_value=receipt_path,
        snapshot=snapshot,
        jobs_index_path=index_path,
    )["status"] == "pass"

    stale_progress = dict(progress)
    stale_progress["ledger"] = {"sha256": "b" * 64, "entry_count": 2}
    stale_snapshot = control.MonitorSnapshot(
        jobs=snapshot.jobs,
        audits=snapshot.audits,
        issues=snapshot.issues,
        progress=stale_progress,
    )
    assert control._circuit_recovery_gate(
        path_value=receipt_path,
        snapshot=stale_snapshot,
        jobs_index_path=index_path,
    )["status"] == "fail"


def test_credential_only_circuit_can_recover_after_current_three_host_canary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs, _index, index_path = control.load_full_jobs()
    job = dict(jobs[0])
    issue = control._issue(
        job,
        classification="systemic",
        circuit_class="credential",
        signature="credential_or_billing_failure",
        summary="historical credential failure",
        evidence_paths=(),
    )
    circuit = {
        "tripped": True,
        "tripped_lanes": [],
        "immediate_classes_observed": ["credential"],
        "consecutive_lane_failure_streaks": [],
    }
    progress = {
        "counts": {
            "canonical_reusable": 1,
            "expected": 2436,
            "pending": 2434,
            "in_progress": 1,
            "settled_invalid": 0,
            "issues": 1,
        },
        "circuit_breaker": circuit,
        "ledger": {"sha256": "a" * 64, "entry_count": 1},
    }
    snapshot = control.MonitorSnapshot(
        jobs=(job,),
        audits=(
            control.SlotAudit(
                record_slot_id=str(job["record_slot_id"]),
                state="in_progress",
                reusable=False,
                issues=(issue,),
                artifact_root="remote",
            ),
        ),
        issues=(issue,),
        progress=progress,
    )
    trace_path = _receipt(tmp_path / "trace-heavy-canary.json", {"status": "pass"})
    credential_path = _receipt(
        tmp_path / "three-host-credential-canary.json", {"status": "pass"}
    )
    junit_path = tmp_path / "targeted.xml"
    junit_path.write_text(
        '<testsuite tests="3" failures="0" errors="0">'
        + "".join(
            f'<testcase name="{name}"/>'
            for name in sorted(control.REQUIRED_RECOVERY_TEST_CASES)
        )
        + "</testsuite>\n",
        encoding="utf-8",
    )

    def passing_gate(path: str | Path) -> dict[str, Any]:
        resolved = control.resolve_repo_path(path)
        return {
            "status": "pass",
            "path": control._display_path(resolved),
            "sha256": control.sha256_file(resolved),
        }

    monkeypatch.setattr(control, "_trace_heavy_recovery_canary_gate", passing_gate)
    monkeypatch.setattr(control, "_remote_retention_canary_gate", passing_gate)
    monkeypatch.setattr(control, "_live_quiescence", lambda **_: _quiescence_receipt())
    receipt_path = tmp_path / "credential-recovery.json"

    issued = control.build_circuit_recovery_receipt(
        snapshot=snapshot,
        jobs_index_path=index_path,
        trace_heavy_canary_acceptance_path=trace_path,
        credential_recovery_canary_acceptance_path=credential_path,
        junit_report_path=junit_path,
        ssh_key_path=tmp_path / "unused-key",
        confirmation=control.CIRCUIT_RECOVERY_ISSUE_CONFIRMATION,
        output_path=receipt_path,
    )

    assert issued["diagnosis_and_remediation"]["recovery_mode"] == (
        "credential_only_current_paid_canary"
    )
    assert issued["authorization"]["new_failure_streak_epoch_agent_ids"] == [
        "Agent A"
    ]
    assert control._circuit_recovery_gate(
        path_value=receipt_path,
        snapshot=snapshot,
        jobs_index_path=index_path,
    )["status"] == "pass"


def test_open_circuit_requires_exact_recovery_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _job(62, "Agent A")
    snapshot = _snapshot((job,), reusable=set())
    snapshot.progress["circuit_breaker"] = {
        "tripped": True,
        "tripped_lanes": ["Agent A"],
        "immediate_classes_observed": [],
        "consecutive_lane_failure_streaks": [],
    }
    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control,
        "_circuit_recovery_gate",
        lambda **_: {
            "status": "pass",
            "recovery_id": "c" * 64,
            "authorized_agent_ids": ["Agent A"],
        },
    )

    with pytest.raises(control.WebArenaRunControlError, match="exact circuit-recovery"):
        control.execute_resumable_full_schedule(
            FullSchedulePlan(jobs=(job,), acceptance={}),
            ssh_key_path="unused",
            confirm_paid_full=control.PAID_FULL_CONFIRMATION,
            confirm_circuit_recovery="wrong",
        )


def test_live_quiescence_treats_no_matching_worker_as_zero_and_binds_runtime_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(0, agent) for agent in EXPECTED_AGENT_IDS)
    runtime_hashes = _quiescence_receipt()["expected_runtime_code_sha256"]
    commands: list[str] = []
    monkeypatch.setattr(control, "load_site_lock", lambda _path: {})
    monkeypatch.setattr(
        control,
        "_remote_audit_target",
        lambda job, **_: SimpleNamespace(
            machine_id=str(job["execution_target"]["server_id"]),
            remote_workdir="/opt/evidence-system/webarena_verified_full_812",
        ),
    )

    def fake_remote(_target: Any, command: str, **_: Any) -> Any:
        commands.append(command)
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {"active_worker_count": 0, **runtime_hashes},
                sort_keys=True,
            ),
            stderr="",
        )

    monkeypatch.setattr(control, "run_remote_blind_command", fake_remote)

    observed = control._live_quiescence(
        jobs=jobs,
        ssh_key_path="unused",
        site_lock_path="unused",
    )

    assert observed["status"] == "pass"
    assert observed["active_worker_count"] == 0
    assert len(observed["hosts"]) == 3
    assert all("pgrep -f '[w]ebarena_official_worker' || true" in item for item in commands)


def test_recovered_lane_starts_new_failure_streak_epoch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _job(65, "Agent A")
    snapshot = _snapshot((job,), reusable=set())
    snapshot.progress["circuit_breaker"] = {
        "tripped": True,
        "tripped_lanes": ["Agent A"],
        "immediate_classes_observed": [],
        "consecutive_lane_failure_streaks": [
            {
                "agent_id": "Agent A",
                "count": 3,
                "record_slot_ids": [
                    "wv123-task-062-agent-a",
                    "wv123-task-063-agent-a",
                    "wv123-task-064-agent-a",
                ],
            }
        ],
    }
    calls: list[str] = []
    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control,
        "_circuit_recovery_gate",
        lambda **_: {
            "status": "pass",
            "recovery_id": "d" * 64,
            "authorized_agent_ids": ["Agent A"],
        },
    )
    monkeypatch.setattr(
        control,
        "_live_quiescence",
        lambda **_: {"status": "pass", "active_worker_count": 0, "hosts": []},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        **_: Any,
    ) -> list[Any]:
        for planned_job in plan.jobs:
            execution_plan = adapter_planner(planned_job, target=object())
            adapter_executor(
                planned_job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    def fail_once(planned_job: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(str(planned_job["record_slot_id"]))
        raise TimeoutError("worker timed out")

    recovery_id = "d" * 64
    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=(job,), acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        confirm_circuit_recovery=(
            control.CIRCUIT_RECOVERY_CONFIRMATION_PREFIX + recovery_id
        ),
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=fail_once,
    )

    assert calls == [job["record_slot_id"]]
    assert result["execution_counts"] == {"runtime_issue": 1}
    assert result["circuit_recovery_used"] is True
    assert result["circuit_recovery_id"] == recovery_id


def test_recovered_lane_retries_exact_failure_tail_as_prelude(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent A") for task_id in range(556, 561))
    issues = tuple(
        control._issue(
            job,
            classification="infra",
            circuit_class="infra",
            signature="trace_sanitization_failure",
            summary="historical trace sanitization failure",
            evidence_paths=(),
        )
        for job in jobs[:4]
    )
    base = _snapshot(jobs, reusable=set())
    audits = tuple(
        control.SlotAudit(
            record_slot_id=str(job["record_slot_id"]),
            state="in_progress" if index < 4 else "pending",
            reusable=False,
            issues=(issues[index],) if index < 4 else (),
            artifact_root="remote",
        )
        for index, job in enumerate(jobs)
    )
    snapshot = control.MonitorSnapshot(
        jobs=jobs,
        audits=audits,
        issues=issues,
        progress={
            **base.progress,
            "circuit_breaker": {
                "tripped": True,
                "tripped_lanes": ["Agent A"],
                "immediate_classes_observed": [],
                "consecutive_lane_failure_streaks": [
                    {
                        "agent_id": "Agent A",
                        "count": 4,
                        "record_slot_ids": [
                            str(job["record_slot_id"]) for job in jobs[:4]
                        ],
                    }
                ],
            },
        },
    )
    observed: list[str] = []
    passed_prelude: list[str] = []
    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control,
        "_circuit_recovery_gate",
        lambda **_: {
            "status": "pass",
            "recovery_id": "e" * 64,
            "authorized_agent_ids": ["Agent A"],
        },
    )
    monkeypatch.setattr(
        control,
        "_live_quiescence",
        lambda **_: {"status": "pass", "active_worker_count": 0, "hosts": []},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        control,
        "audit_remote_slot",
        lambda job, **_: control.SlotAudit(
            record_slot_id=str(job["record_slot_id"]),
            state="canonical_reusable",
            reusable=True,
            issues=(),
            artifact_root="remote",
        ),
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        recovery_prelude_slot_ids: Any,
        **_: Any,
    ) -> list[Any]:
        passed_prelude.extend(recovery_prelude_slot_ids)
        ordered = [
            *(
                job
                for slot_id in recovery_prelude_slot_ids
                for job in plan.jobs
                if job["record_slot_id"] == slot_id
            ),
            *(job for job in plan.jobs if job["record_slot_id"] not in recovery_prelude_slot_ids),
        ]
        for job in ordered:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        confirm_circuit_recovery=control.CIRCUIT_RECOVERY_CONFIRMATION_PREFIX + "e" * 64,
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=lambda job, **_: observed.append(str(job["record_slot_id"]))
        or {"status": "completed"},
    )

    expected = [str(job["record_slot_id"]) for job in jobs[:4]]
    assert passed_prelude == expected
    assert observed[:4] == expected
    assert result["recovery_prelude_slot_ids"] == expected


def test_retry_exhaustion_receipt_keeps_consumed_retry_out_of_prelude(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tuple(_job(task_id, "Agent A") for task_id in (62, 63, 64))
    issues = tuple(
        control._issue(
            job,
            classification="infra",
            circuit_class="infra",
            signature="official_evaluator_validation_failed",
            summary="official evaluator infrastructure failure",
            evidence_paths=(),
        )
        for job in jobs[:2]
    )
    base = _snapshot(jobs, reusable=set())
    snapshot = control.MonitorSnapshot(
        jobs=jobs,
        audits=tuple(
            control.SlotAudit(
                record_slot_id=str(job["record_slot_id"]),
                state="in_progress" if index < 2 else "pending",
                reusable=False,
                issues=(issues[index],) if index < 2 else (),
                artifact_root="remote",
            )
            for index, job in enumerate(jobs)
        ),
        issues=issues,
        progress={
            **base.progress,
            "circuit_breaker": {
                "tripped": True,
                "tripped_lanes": ["Agent A"],
                "immediate_classes_observed": [],
                "consecutive_lane_failure_streaks": [
                    {
                        "agent_id": "Agent A",
                        "count": 2,
                        "record_slot_ids": [
                            str(job["record_slot_id"]) for job in jobs[:2]
                        ],
                    }
                ],
            },
        },
    )
    consumed = str(jobs[0]["record_slot_id"])
    replayed: list[str] = []
    passed_prelude: list[str] = []
    monkeypatch.setattr(control, "monitor_namespace", lambda **_: snapshot)
    monkeypatch.setattr(
        control,
        "build_full_run_control_acceptance",
        lambda **_: {"formal_paid_launch_ready": True},
    )
    monkeypatch.setattr(
        control,
        "_circuit_recovery_gate",
        lambda **_: {
            "status": "pass",
            "recovery_id": "f" * 64,
            "sha256": "e" * 64,
            "authorized_agent_ids": ["Agent A"],
        },
    )
    monkeypatch.setattr(
        control,
        "_retry_exhausted_slots_gate",
        lambda **_: {"status": "pass", "slot_ids": [consumed]},
    )
    monkeypatch.setattr(
        control,
        "_live_quiescence",
        lambda **_: {"status": "pass", "active_worker_count": 0, "hosts": []},
    )
    monkeypatch.setattr(
        control, "_merge_runtime_issue_into_ledger", lambda *_args, **_kwargs: None
    )

    def fake_full_executor(
        plan: FullSchedulePlan,
        *,
        adapter_planner: Any,
        adapter_executor: Any,
        recovery_prelude_slot_ids: Any,
        **_: Any,
    ) -> list[Any]:
        passed_prelude.extend(recovery_prelude_slot_ids)
        ordered = [
            *(job for job in plan.jobs if job["record_slot_id"] in recovery_prelude_slot_ids),
            *(job for job in plan.jobs if job["record_slot_id"] not in recovery_prelude_slot_ids),
        ]
        for job in ordered:
            execution_plan = adapter_planner(job, target=object())
            adapter_executor(
                job,
                target=object(),
                execution_plan=execution_plan,
                context=object(),
            )
        return []

    monkeypatch.setattr(control, "execute_full_schedule", fake_full_executor)

    result = control.execute_resumable_full_schedule(
        FullSchedulePlan(jobs=jobs, acceptance={}),
        ssh_key_path="unused",
        confirm_paid_full=control.PAID_FULL_CONFIRMATION,
        confirm_circuit_recovery=(
            control.CIRCUIT_RECOVERY_CONFIRMATION_PREFIX + "f" * 64
        ),
        retry_exhausted_receipt_path="unused-receipt",
        adapter_planner=lambda _job, **_kwargs: {
            "status": "runnable",
            "runner_command": "fake",
        },
        adapter_executor=lambda job, **_: replayed.append(str(job["record_slot_id"]))
        or {"status": "completed"},
    )

    assert passed_prelude == [str(jobs[1]["record_slot_id"])]
    assert consumed not in replayed
    assert result["retry_exhausted_slot_ids"] == [consumed]
    assert result["execution_counts"]["record_only_issue_skipped"] == 1


def test_semantic_review_emits_hashed_receipt_for_healthy_slot(
    tmp_path: Path,
) -> None:
    packet_root = Path("experiments/case_packets/webarena_verified/0")
    agent_input = json.loads(
        packet_root.joinpath("agent_input.json").read_text(encoding="utf-8")
    )
    native_root = tmp_path / "native_run"
    task_dir = native_root / "0"
    attempts = native_root / "llm_attempts"
    traces = native_root / "traces"
    task_dir.mkdir(parents=True)
    attempts.mkdir()
    traces.mkdir()
    paths = {
        "official_task": task_dir / "official_task_config.json",
        "solver_trace": task_dir / "solver_trace.json",
        "network_har": task_dir / "network.har",
        "network_har_sanitization": task_dir / "network_har_sanitization.json",
        "playwright_trace": traces / "0.zip",
        "eval_result": task_dir / "eval_result.json",
        "eval_summary": task_dir / "eval_summary.json",
        "agent_response": task_dir / "agent_response.json",
        "reset_receipt": native_root / "reset_receipt.json",
    }
    _json_file(
        paths["official_task"],
        {
            "task_id": 0,
            "revision": 2,
            "intent_template_id": agent_input["intent_template_id"],
            "intent": agent_input["intent"],
            "sites": agent_input["sites"],
            "start_url": " |AND| ".join(agent_input["start_urls"]),
        },
    )
    _json_file(
        paths["solver_trace"],
        {
            "steps": [
                {
                    "step": 0,
                    "page_url_before": agent_input["start_urls"][0],
                    "action": {"action_type": "STOP"},
                    "fail_error": "",
                }
            ],
            "response_protocol_source": "stop_action_json_payload",
            "final_response_source": "official_stop_action",
        },
    )
    _json_file(
        paths["network_har"],
        {
            "log": {
                "entries": [
                    {
                        "request": {"url": agent_input["start_urls"][0]},
                        "response": {"status": 200},
                    }
                ]
            }
        },
    )
    _json_file(
        paths["network_har_sanitization"],
        {"status": "pass", "sanitization_completed_before_evaluator": True},
    )
    _json_file(
        paths["eval_result"],
        {
            "status": "success",
            "evaluators_results": [
                {"evaluator_name": "AgentResponseEvaluator", "status": "success"}
            ],
        },
    )
    _json_file(paths["eval_summary"], {"status": "success"})
    _json_file(
        paths["agent_response"],
        {
            "task_type": "RETRIEVE",
            "status": "SUCCESS",
            "retrieved_data": ["publicly observed value"],
            "error_details": None,
        },
    )
    _json_file(paths["reset_receipt"], {"status": "pass"})
    _json_file(
        attempts / "01_prompt.json",
        {"model": "test", "messages": [{"role": "user", "content": "public"}]},
    )
    paths["playwright_trace"].write_bytes(b"PK\x03\x04")
    job = _job(0, "Agent A")
    job["task_revision"] = 2

    receipt, issues = control._semantic_case_review(job, paths)

    assert issues == []
    assert len(receipt["review_receipt_sha256"]) == 64
    assert receipt["needs_review"] is False
    assert receipt["private_evaluator_payload_recorded"] is False
    assert set(receipt["category_status"].values()) == {
        "reviewed_no_deterministic_indicator"
    }
    assert receipt["har_summary"]["entry_count"] == 1
    assert receipt["solver_trace_summary"]["step_count"] == 1


def test_full_launch_requires_pilot_budget_and_capacity_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs = tuple(_job(index, agent) for index, agent in enumerate(EXPECTED_AGENT_IDS))
    plan = FullSchedulePlan(jobs=jobs, acceptance={})
    index_path = tmp_path / "index.json"
    index_path.write_text("{}\n", encoding="utf-8")
    index = {"jobs_sha256": "locked-jobs", "launch_authorization": {}}
    snapshot = _snapshot(jobs, reusable=set())
    monkeypatch.setattr(
        control,
        "load_full_jobs",
        lambda _path: (jobs, index, index_path),
    )
    monkeypatch.setattr(control, "DEFAULT_JOBS_INDEX", index_path)
    monkeypatch.setattr(control, "execution_input_hash", lambda _plan: "locked-jobs")

    pilot = _receipt(tmp_path / "pilot.json", {"status": "pass", "gates": {"a": True}})
    storage = _receipt(
        tmp_path / "storage.json",
        {
            "status": "pass",
            "all_three_capacity_thresholds_satisfied": True,
            "pilot_storage_projection_complete": True,
            "full_run_storage_projection_complete": True,
        },
    )
    credential = _receipt(tmp_path / "credential.json", {"status": "pass"})
    budget = tmp_path / "budget.json"
    host_receipts = []
    for agent in EXPECTED_AGENT_IDS:
        server_id = EXPECTED_ROUTES[agent]["server_id"]
        host_path = _receipt(
            tmp_path / f"host-{server_id}.json",
            {
                "status": "pass",
                "server_id": server_id,
                "slot_count": 1,
                "security_finding_count": 0,
                "gold_finding_count": 0,
                "remote_directory_cleanup_performed": False,
                "full_evidence_synced_to_controller": False,
            },
        )
        host_receipts.append(
            {
                "agent_id": agent,
                "server_id": server_id,
                "path": str(host_path),
                "sha256": control.sha256_file(host_path),
            }
        )
    canary = _receipt(
        tmp_path / "remote-canary.json",
        {
            "schema_version": "webarena_verified_three_host_task0_canary_acceptance/v1",
            "status": "pass",
            "artifact_retention_mode": "vps_persistent_remote_v1",
            "paid_slot_count": 3,
            "required_artifact_audit_pass_count": 3,
            "remote_file_and_hash_verification_over_ssh": True,
            "security_scan_and_finalization_executed_on_each_vps": True,
            "full_evidence_synced_to_controller": False,
            "remote_directory_cleanup_performed": False,
            "results": [
                {
                    "agent_id": agent,
                    "audit_state": "canonical_reusable",
                    "security_finding_count": 0,
                    "gold_finding_count": 0,
                }
                for agent in EXPECTED_AGENT_IDS
            ],
            "remote_host_finalization_receipts": host_receipts,
            "control_bindings": {
                "schema_version": "webarena_verified_canary_control_bindings/v1",
                "materialized_full_jobs_index_path": control._display_path(
                    index_path
                ),
                "materialized_full_jobs_index_sha256": control.sha256_file(
                    index_path
                ),
                "materialized_full_jobs_sha256": (
                    "5c613b729e96ac020b9e2a8d5cdba667371f086be7c5cad4e46292d9a349e704"
                ),
                "materialized_full_job_count": 2436,
                "legacy_native_claim_compiler_runtime_dependency": False,
                "formal_score_draft_provider": "neurips_ed_track_minimal",
                    "critical_code_sha256": {
                        path: control.sha256_file(control.resolve_repo_path(path))
                        for path in control.RECOVERY_CRITICAL_CODE_PATHS
                    },
            },
        },
    )

    blocked = control.build_full_run_control_acceptance(
        plan=plan,
        jobs_index_path=index_path,
        snapshot=snapshot,
        pilot_acceptance_path=pilot,
        storage_acceptance_path=storage,
        credential_acceptance_path=credential,
        pilot_budget_capacity_acceptance_path=budget,
        remote_retention_canary_acceptance_path=canary,
    )
    assert blocked["formal_paid_launch_ready"] is False
    assert blocked["launch_gates"]["pilot_budget_and_openrouter_capacity"][
        "status"
    ] == "pending"

    _receipt(
        budget,
        {
            "status": "pass",
            "gates": {
                "pilot_cost_measured": True,
                "openrouter_remaining_credit_safety_margin_pass": True,
            },
        },
    )
    ready = control.build_full_run_control_acceptance(
        plan=plan,
        jobs_index_path=index_path,
        snapshot=snapshot,
        pilot_acceptance_path=pilot,
        storage_acceptance_path=storage,
        credential_acceptance_path=credential,
        pilot_budget_capacity_acceptance_path=budget,
        remote_retention_canary_acceptance_path=canary,
    )
    assert ready["formal_paid_launch_ready"] is True
    assert ready["launch_gates"]["pilot_budget_and_openrouter_capacity"][
        "status"
    ] == "pass"


def test_audit_slot_promotes_openrouter_401_to_immediate_credential_circuit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(control, "job_result_relative_dir", lambda _job: tmp_path)
    root = tmp_path / "adapter"
    native = root / "native_run"
    native.mkdir(parents=True)
    _json_file(root / "raw_run.json", {"status": "INFRA_EXCLUDED"})
    _json_file(
        native / "run_summary.json",
        {
            "status": "error",
            "error_type": "RuntimeError",
            "error_message": (
                'OpenRouter HTTP 401: {"error":{"message":"User not found."}}'
            ),
        },
    )

    audited = control.audit_slot(_job(0, "Agent A"), site_lock={})

    assert audited.state == "settled_invalid"
    assert audited.reusable is False
    assert len(audited.issues) == 1
    issue = audited.issues[0]
    assert issue["classification"] == "systemic"
    assert issue["circuit_class"] == "credential"
    assert issue["signature"] == "credential_or_billing_failure"


def _job(task_id: int, agent_id: str) -> dict[str, Any]:
    suffix = agent_id[-1].lower()
    return {
        "schema_version": "job/v1",
        "domain": "webarena_verified",
        "phase": "full",
        "job_id": f"full-webarena_verified-{task_id:03d}-agent_{suffix}",
        "record_slot_id": f"wv123-task-{task_id:03d}-agent-{suffix}",
        "task_id": str(task_id),
        "task_revision": 1,
        "agent_id": agent_id,
        "result_namespace": RESULT_NAMESPACE,
        "execution_target": EXPECTED_ROUTES[agent_id],
        "artifact_retention_mode": "vps_persistent_remote_v1",
    }


def _snapshot(
    jobs: tuple[dict[str, Any], ...], *, reusable: set[str]
) -> control.MonitorSnapshot:
    audits = tuple(
        control.SlotAudit(
            record_slot_id=str(job["record_slot_id"]),
            state=("canonical_reusable" if job["record_slot_id"] in reusable else "pending"),
            reusable=job["record_slot_id"] in reusable,
            issues=(),
            artifact_root="unused",
        )
        for job in jobs
    )
    return control.MonitorSnapshot(
        jobs=jobs,
        audits=audits,
        issues=(),
        progress={
            "counts": {
                "canonical_reusable": len(reusable),
                "expected": len(jobs),
                "pending": len(jobs) - len(reusable),
                "in_progress": 0,
                "settled_invalid": 0,
                "issues": 0,
            },
            "circuit_breaker": {"tripped": False},
            "ledger": {"sha256": "0" * 64},
        },
    )


def _receipt(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    control._write_sidecar(path)
    return path


def _quiescence_receipt() -> dict[str, Any]:
    runtime_hashes = {
        "webarena_har_sanitization.py": control.sha256_file(
            control.resolve_repo_path(
                "src/evidence_system/adapters/webarena_har_sanitization.py"
            )
        ),
        "webarena_remote_retention.py": control.sha256_file(
            control.resolve_repo_path(
                "src/evidence_system/adapters/webarena_remote_retention.py"
            )
        ),
    }
    return {
        "status": "pass",
        "active_worker_count": 0,
        "hosts": [
            {
                "agent_id": agent,
                "active_worker_count": 0,
                "runtime_code_sha256": runtime_hashes,
                "verified_over_ssh": True,
            }
            for agent in EXPECTED_AGENT_IDS
        ],
        "expected_runtime_code_sha256": runtime_hashes,
        "workers_stopped_or_killed_by_check": 0,
    }


def _json_file(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path
