from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence_system.adapters import agentdojo_formal_supervisor as supervisor
from evidence_system.core.hashing import sha256_file, sha256_object


def _write(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)


def _controls(root: Path, *, with_state: bool) -> tuple[dict[str, object], ...]:
    root.mkdir(mode=0o700)
    (root / supervisor.LAUNCH_INTENT).write_text("{}\n", encoding="utf-8")
    spec: dict[str, object] = {
        "schema_version": "agentdojo_formal_supervisor_spec/v1",
        "stage_id": "recovery-a",
        "session_id": "session-supervisor-test",
        "job_binding_sha256": "a" * 64,
        "stage_authorization_sha256": "b" * 64,
        "formal_wall_clock_timeout_seconds": 7200,
        "kill_grace_seconds": 30,
        "command_sha256": __import__("hashlib").sha256(b"true").hexdigest(),
        "command": "true",
    }
    _write(root / supervisor.SPEC, spec)
    claim: dict[str, object] = {
        "schema_version": "agentdojo_formal_supervisor_claim/v2",
        "stage_id": spec["stage_id"],
        "session_id": spec["session_id"],
        "job_binding_sha256": spec["job_binding_sha256"],
        "stage_authorization_sha256": spec["stage_authorization_sha256"],
        "supervisor_pid": 900001,
        "supervisor_pgid": 900001,
        "supervisor_session_id": 900001,
        "supervisor_starttime_ticks": 100,
        "host_boot_id": "00000000-0000-0000-0000-000000000001",
        "spec_sha256": sha256_file(root / supervisor.SPEC),
        "claimed_boottime_seconds": 10.0,
        "bootstrap_deadline_boottime_seconds": 40.0,
    }
    _write(root / supervisor.CLAIM, claim)
    if not with_state:
        return spec, claim
    state: dict[str, object] = {
        "schema_version": "agentdojo_formal_supervisor_state/v2",
        "stage_id": spec["stage_id"],
        "session_id": spec["session_id"],
        "job_binding_sha256": spec["job_binding_sha256"],
        "stage_authorization_sha256": spec["stage_authorization_sha256"],
        "spec_sha256": sha256_file(root / supervisor.SPEC),
        "claim_sha256": sha256_file(root / supervisor.CLAIM),
        "supervisor_pid": claim["supervisor_pid"],
        "supervisor_pgid": claim["supervisor_pgid"],
        "supervisor_session_id": claim["supervisor_session_id"],
        "supervisor_starttime_ticks": claim["supervisor_starttime_ticks"],
        "worker_pid": 900002,
        "worker_pgid": 900002,
        "worker_session_id": 900002,
        "worker_starttime_ticks": 101,
        "launched_host_boot_id": claim["host_boot_id"],
        "launched_boottime_seconds": 20.0,
        "deadline_boottime_seconds": 7220.0,
        "formal_wall_clock_timeout_seconds": 7200,
        "kill_grace_seconds": 30,
    }
    _write(root / supervisor.STATE, state)
    return spec, claim, state


def _normal_exit(root: Path, state: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "agentdojo_formal_supervisor_exit/v2",
        "stage_id": state["stage_id"],
        "session_id": state["session_id"],
        "job_binding_sha256": state["job_binding_sha256"],
        "stage_authorization_sha256": state["stage_authorization_sha256"],
        "spec_sha256": state["spec_sha256"],
        "claim_sha256": state["claim_sha256"],
        "state_sha256": sha256_object(state),
        "supervisor_pid": state["supervisor_pid"],
        "supervisor_pgid": state["supervisor_pgid"],
        "supervisor_session_id": state["supervisor_session_id"],
        "supervisor_starttime_ticks": state["supervisor_starttime_ticks"],
        "worker_pid": state["worker_pid"],
        "worker_pgid": state["worker_pgid"],
        "worker_session_id": state["worker_session_id"],
        "worker_starttime_ticks": state["worker_starttime_ticks"],
        "launched_host_boot_id": state["launched_host_boot_id"],
        "finished_host_boot_id": state["launched_host_boot_id"],
        "finished_boottime_seconds": 21.0,
        "exit_code": 0,
        "outcome": "worker_exited",
        "timed_out": False,
        "term_sent": False,
        "kill_sent": False,
        "group_gone": True,
        "bootstrap_terminal": False,
    }


def test_supervisor_crash_before_state_becomes_terminal_after_bootstrap_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "attempt"
    _spec, claim = _controls(root, with_state=False)
    monkeypatch.setattr(supervisor, "_boot_id", lambda: claim["host_boot_id"])
    monkeypatch.setattr(supervisor, "_boottime", lambda: 41.0)
    monkeypatch.setattr(supervisor, "_claim_supervisor_alive", lambda _claim: False)

    result = supervisor.status_only(root, session_id=str(claim["session_id"]))

    assert result["status"] == "exited"
    assert result["outcome"] == "bootstrap_deadline_expired"
    assert result["group_gone"] is True


def test_supervisor_pid_reuse_before_state_is_terminal_without_signal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "attempt"
    _spec, claim = _controls(root, with_state=False)
    monkeypatch.setattr(supervisor, "_boot_id", lambda: claim["host_boot_id"])
    monkeypatch.setattr(supervisor, "_boottime", lambda: 41.0)

    def conflict(_claim: object) -> bool:
        raise supervisor.ProcessIdentityConflict("reused")

    monkeypatch.setattr(supervisor, "_claim_supervisor_alive", conflict)
    result = supervisor.status_only(root, session_id=str(claim["session_id"]))
    assert result["status"] == "exited"
    assert result["outcome"] == "supervisor_identity_conflict_before_state"


def test_supervisor_boot_change_before_state_is_terminal_without_signal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "attempt"
    _spec, claim = _controls(root, with_state=False)
    monkeypatch.setattr(
        supervisor, "_boot_id", lambda: "00000000-0000-0000-0000-000000000002"
    )
    monkeypatch.setattr(supervisor, "_boottime", lambda: 1.0)
    result = supervisor.status_only(root, session_id=str(claim["session_id"]))
    assert result["status"] == "exited"
    assert result["outcome"] == "boot_changed_before_state"


def test_supervisor_state_rejects_pid_identity_and_spec_hash_tamper(
    tmp_path: Path,
) -> None:
    root = tmp_path / "attempt"
    _spec, claim, state = _controls(root, with_state=True)
    state["supervisor_starttime_ticks"] = 999
    _write(root / supervisor.STATE, state)
    with pytest.raises(supervisor.SupervisorError, match="supervisor identity"):
        supervisor._verify_state(
            root / supervisor.STATE, expected_session_id=str(claim["session_id"])
        )


def test_supervisor_exit_rejects_state_hash_and_group_gone_tamper(
    tmp_path: Path,
) -> None:
    root = tmp_path / "attempt"
    _spec, claim, state = _controls(root, with_state=True)
    receipt = _normal_exit(root, state)
    receipt["state_sha256"] = "f" * 64
    _write(root / supervisor.EXIT, receipt)
    with pytest.raises(supervisor.SupervisorError, match="state hash"):
        supervisor._verify_exit(
            root / supervisor.EXIT, expected_session_id=str(claim["session_id"])
        )
    (root / supervisor.EXIT).unlink()
    receipt = _normal_exit(root, state)
    receipt["group_gone"] = False
    _write(root / supervisor.EXIT, receipt)
    with pytest.raises(supervisor.SupervisorError, match="process group gone"):
        supervisor.status_only(root, session_id=str(claim["session_id"]))
