from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from evidence_system.cli import agentdojo_remaining_849_monitor as monitor
from evidence_system.core.hashing import sha256_object


HEX = "a" * 64


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _plan(tmp_path: Path, *, a_count: int = 5) -> tuple[Path, dict[str, list[str]]]:
    lanes = {
        "Agent A": [sha256_object({"lane": "A", "ordinal": value}) for value in range(a_count)],
        "Agent B": [sha256_object({"lane": "B", "ordinal": 0})],
        "Agent C": [sha256_object({"lane": "C", "ordinal": 0})],
    }
    entries = [
        {
            "vps_id": "vps1",
            "agent_id": agent_id,
            "job_identity_sha256": identity,
        }
        for agent_id in monitor.EXPECTED_AGENTS
        for identity in lanes[agent_id]
    ]
    payload = {
        "schema_version": "agentdojo_remaining_849_campaign_plan_index/v1",
        "execution_lock_sha256": "1" * 64,
        "execution_policy_sha256": "2" * 64,
        "entries": entries,
        "entries_sha256": sha256_object(entries),
        "job_count": len(entries),
        "record_slot_count": len(entries),
    }
    path = tmp_path / "plan.json"
    _write_json(path, payload)
    return path, lanes


def _args(tmp_path: Path, plan_path: Path) -> argparse.Namespace:
    blind_root = tmp_path / "blind"
    runtime_root = tmp_path / "runtime"
    blind_root.mkdir()
    runtime_root.mkdir()
    return argparse.Namespace(
        campaign_plan_index=plan_path,
        blind_root=blind_root,
        runtime_root=runtime_root,
        state_output=tmp_path / "state" / "integrity.json",
        issue_ledger=blind_root / "issues.jsonl",
        pause_request=runtime_root / "pause.json",
        vps_id="vps1",
        poll_interval=1.0,
        once=True,
    )


def _health_args(tmp_path: Path, plan_path: Path) -> argparse.Namespace:
    args = _args(tmp_path, plan_path)
    args.state_output = tmp_path / "state" / "health.json"
    args.controller_identity = args.runtime_root / "controller.json"
    args.minimum_free_bytes = 0
    args.minimum_free_inodes = 0
    args.maximum_memory_percent = 100.0
    return args


def _failure(identity: str, *, ordinal: int) -> dict[str, object]:
    session = f"session-test-{ordinal}"
    binding = sha256_object({"binding": identity})
    return {
        "schema_version": monitor.FAILED_SCHEMA,
        "sealed_at": "2026-07-17T00:00:00+00:00",
        "execution_lock_sha256": "1" * 64,
        "execution_policy_sha256": "2" * 64,
        "job_binding_sha256": binding,
        "job_identity_sha256": identity,
        "stage_authorization_sha256": "3" * 64,
        "formal_stage_id": "Agent-A",
        "formal_stage_session_id": session,
        "failure_category": "worker_error",
        "worker_exit_code": 1,
        "attempt_tree_sha256": "4" * 64,
        "attempt_file_count": 1,
        "attempt_total_bytes": 10,
        "blind_only": True,
        monitor._FALSE_CONTENT_MARKER: False,
        "archive_relative_path": f"{binding}/{session}",
        "attempt_failure_marker_sha256": "5" * 64,
        "archive_tree_sha256": "6" * 64,
        "archive_file_count": 2,
        "archive_total_bytes": 20,
        "attempt_identity_sha256": sha256_object(
            {"identity": identity, "ordinal": ordinal}
        ),
    }


def _completion(identity: str) -> dict[str, object]:
    binding = sha256_object({"binding": identity})
    return {
        "schema_version": monitor.COMPLETION_SCHEMA,
        "recorded_at": "2026-07-17T00:00:00+00:00",
        "execution_lock_sha256": "1" * 64,
        "execution_policy_sha256": "2" * 64,
        "job_binding_sha256": binding,
        "job_identity_sha256": identity,
        "stage_authorization_sha256": "3" * 64,
        "formal_stage_id": "Agent-A",
        "formal_stage_session_id": "session-test-success",
        "formal_execution_context_sha256": "4" * 64,
        "artifact_file_count": 5,
        "artifact_tree_sha256": "5" * 64,
        "artifact_total_bytes": 50,
        "native_episode_count": 3,
        "attempt_tree_sha256": "6" * 64,
        "attempt_file_count": 6,
        "attempt_total_bytes": 60,
        "supervisor_exit_receipt_sha256": "7" * 64,
        "canonical_job_relative_path": binding,
        "completion_marker_relative_path": (
            f"{binding}/adapter/formal_job_completion.json"
        ),
        "completion_marker_file_sha256": "8" * 64,
        "completion_marker_semantic_sha256": "9" * 64,
        "blind_only": True,
        monitor._FALSE_CONTENT_MARKER: False,
    }


def test_integrity_watch_records_isolated_failure_without_pausing(tmp_path: Path) -> None:
    plan_path, lanes = _plan(tmp_path)
    args = _args(tmp_path, plan_path)
    _append_jsonl(
        args.blind_root / monitor.FAILED_JOURNAL,
        _failure(lanes["Agent A"][0], ordinal=0),
    )

    result = monitor.run_integrity_cycle(args)

    assert result["status"] == "issues_recorded"
    assert result["terminal_counts"]["failed"] == 1
    assert result["pause_requested"] is False
    assert not args.pause_request.exists()
    assert result["raw_evidence_files_opened"] == 0
    assert result[monitor._FALSE_CONTENT_MARKER] is False


def test_integrity_watch_requests_pause_only_after_four_ordered_failures(
    tmp_path: Path,
) -> None:
    plan_path, lanes = _plan(tmp_path)
    args = _args(tmp_path, plan_path)
    journal = args.blind_root / monitor.FAILED_JOURNAL
    for ordinal, identity in enumerate(lanes["Agent A"][:3]):
        _append_jsonl(journal, _failure(identity, ordinal=ordinal))

    before = monitor.run_integrity_cycle(args)

    assert before["pause_requested"] is False
    assert before["agent_lanes"][0]["consecutive_terminal_failure_streak"] == 3

    _append_jsonl(journal, _failure(lanes["Agent A"][3], ordinal=3))
    after = monitor.run_integrity_cycle(args)

    assert after["status"] == "admission_pause_requested"
    assert after["pause_requested"] is True
    assert after["agent_lanes"][0]["consecutive_terminal_failure_streak"] == 4
    pause = json.loads(args.pause_request.read_text(encoding="utf-8"))
    assert pause["controller_action"] == "pause_new_admissions_only"
    assert pause["kill_worker_requested"] is False
    assert pause["consecutive_failure_threshold"] == 4


def test_integrity_watch_success_resets_ordered_failure_streak(tmp_path: Path) -> None:
    plan_path, lanes = _plan(tmp_path)
    args = _args(tmp_path, plan_path)
    failed = args.blind_root / monitor.FAILED_JOURNAL
    completed = args.blind_root / monitor.COMPLETION_JOURNAL
    for ordinal, identity in enumerate(lanes["Agent A"][:3]):
        _append_jsonl(failed, _failure(identity, ordinal=ordinal))
    _append_jsonl(completed, _completion(lanes["Agent A"][3]))
    _append_jsonl(failed, _failure(lanes["Agent A"][4], ordinal=4))

    result = monitor.run_integrity_cycle(args)

    assert result["pause_requested"] is False
    assert result["agent_lanes"][0]["settled_prefix"] == 5
    assert result["agent_lanes"][0]["consecutive_terminal_failure_streak"] == 1


def test_monitor_rejects_evidence_bearing_output_keys() -> None:
    try:
        monitor._assert_blind_output({"case_prompt": "do not emit"})
    except monitor.MonitorError as exc:
        assert "forbidden output key" in str(exc)
    else:  # pragma: no cover - explicit failure is clearer than pytest magic here
        raise AssertionError("evidence-bearing key was accepted")


def _missing_receipt_supervisors() -> dict[str, object]:
    return {
        "attempt_count": 1,
        "status_counts": {"exit_receipt_missing": 1},
        "attempts": [
            {
                "job_binding_sha256": "b" * 64,
                "session_id": "session-test-receipt-grace",
                "status": "exit_receipt_missing",
            }
        ],
    }


def test_exit_receipt_missing_is_pending_before_grace() -> None:
    state: dict[str, object] = {}

    matured = monitor._debounce_exit_receipt_missing(
        state,
        _missing_receipt_supervisors(),
        observed_at="2026-07-18T00:00:00+00:00",
        grace_seconds=30.0,
    )

    assert matured == set()
    observations = state["exit_receipt_missing_observations"]
    assert isinstance(observations, dict)
    assert len(observations) == 1
    assert next(iter(observations.values()))["observation_count"] == 1


def test_exit_receipt_missing_becomes_fatal_only_after_grace() -> None:
    state: dict[str, object] = {}
    supervisors = _missing_receipt_supervisors()
    monitor._debounce_exit_receipt_missing(
        state,
        supervisors,
        observed_at="2026-07-18T00:00:00+00:00",
        grace_seconds=30.0,
    )

    before = monitor._debounce_exit_receipt_missing(
        state,
        supervisors,
        observed_at="2026-07-18T00:00:29.999999+00:00",
        grace_seconds=30.0,
    )
    after = monitor._debounce_exit_receipt_missing(
        state,
        supervisors,
        observed_at="2026-07-18T00:00:30+00:00",
        grace_seconds=30.0,
    )

    assert before == set()
    assert len(after) == 1


def test_exit_receipt_missing_pending_state_clears_when_receipt_appears() -> None:
    state: dict[str, object] = {}
    monitor._debounce_exit_receipt_missing(
        state,
        _missing_receipt_supervisors(),
        observed_at="2026-07-18T00:00:00+00:00",
        grace_seconds=30.0,
    )

    matured = monitor._debounce_exit_receipt_missing(
        state,
        {"attempt_count": 1, "status_counts": {"exited": 1}, "attempts": []},
        observed_at="2026-07-18T00:00:05+00:00",
        grace_seconds=30.0,
    )

    assert matured == set()
    assert state["exit_receipt_missing_observations"] == {}


def test_health_watch_pauses_only_when_missing_receipt_outlives_grace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path, _ = _plan(tmp_path)
    args = _health_args(tmp_path, plan_path)
    args.supervisor_exit_receipt_grace_seconds = 30.0
    now = {"value": "2026-07-18T00:00:00+00:00"}
    monkeypatch.setattr(monitor, "_utc_now", lambda: now["value"])
    monkeypatch.setattr(monitor, "_live_boot_id", lambda: "live-boot")
    monkeypatch.setattr(
        monitor,
        "_controller_snapshot",
        lambda *args, **kwargs: {
            "present": True,
            "alive": True,
            "pid": 123,
            "starttime_ticks": 456,
            "identity_matches": True,
            "boot_matches": True,
        },
    )
    monkeypatch.setattr(
        monitor,
        "_memory_snapshot",
        lambda: {
            "memory_total_bytes": 1_000,
            "memory_available_bytes": 900,
            "memory_used_percent_milli": 10_000,
            "swap_total_bytes": 0,
            "swap_used_bytes": 0,
        },
    )
    monkeypatch.setattr(
        monitor,
        "readonly_supervisor_peek",
        lambda *_args, **_kwargs: _missing_receipt_supervisors(),
    )

    pending = monitor.run_health_cycle(args)
    assert pending["status"] == "healthy"
    assert pending["exit_receipt_missing_pending_count"] == 1
    assert pending["hard_fatal_issues_this_cycle"] == 0
    assert not args.pause_request.exists()

    now["value"] = "2026-07-18T00:00:30+00:00"
    fatal = monitor.run_health_cycle(args)

    assert fatal["status"] == "admission_pause_requested"
    assert fatal["hard_fatal_issues_this_cycle"] == 1
    assert args.pause_request.exists()


def test_health_watch_requests_pause_for_provider_authentication_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path, _ = _plan(tmp_path)
    args = _health_args(tmp_path, plan_path)
    _append_jsonl(
        args.blind_root / monitor.HEALTH_LEDGER,
        {
            "schema_version": "agentdojo_openrouter_blind_health/v1",
            "timestamp": "2026-07-17T00:00:00+00:00",
            "event_type": "credential_probe",
            "policy_sha256": "4" * 64,
            "outcome": "fatal_error",
            "http_status": 401,
        },
    )
    monkeypatch.setattr(monitor, "_live_boot_id", lambda: "live-boot")
    monkeypatch.setattr(
        monitor,
        "_controller_snapshot",
        lambda *args, **kwargs: {
            "present": True,
            "alive": True,
            "pid": 123,
            "starttime_ticks": 456,
            "identity_matches": True,
            "boot_matches": True,
        },
    )
    monkeypatch.setattr(
        monitor,
        "_memory_snapshot",
        lambda: {
            "memory_total_bytes": 1_000,
            "memory_available_bytes": 900,
            "memory_used_percent_milli": 10_000,
            "swap_total_bytes": 0,
            "swap_used_bytes": 0,
        },
    )
    monkeypatch.setattr(
        monitor,
        "readonly_supervisor_peek",
        lambda *args, **kwargs: {
            "attempt_count": 0,
            "status_counts": {},
            "attempts": [],
        },
    )

    result = monitor.run_health_cycle(args)

    assert result["status"] == "admission_pause_requested"
    assert result["pause_requested"] is True
    assert result["hard_fatal_issues_this_cycle"] == 1
    assert result["new_health_record_count"] == 1
