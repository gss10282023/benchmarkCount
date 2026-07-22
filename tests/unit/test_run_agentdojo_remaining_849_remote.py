from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evidence_system.cli import run_agentdojo_remaining_849_remote as runner
from evidence_system.adapters.runtime import ArtifactDescriptor
from evidence_system.adapters.agentdojo_runtime_control import job_identity_sha256
from evidence_system.core.hashing import sha256_file, sha256_object


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _job(agent: str, ordinal: int) -> dict[str, object]:
    return {
        "job_id": f"job-{agent[-1].lower()}-{ordinal}",
        "case_unit_id": f"v1.2.2:workspace:user_task_{ordinal}:injection_task_0",
        "record_slot_id": f"slot-{agent[-1].lower()}-{ordinal}",
        "agent_id": agent,
    }


def test_load_locked_entries_filters_exact_host_and_lane(tmp_path: Path) -> None:
    entries = []
    expected = []
    for ordinal, (host, agent) in enumerate(
        (("vps1", "Agent A"), ("vps2", "Agent A"), ("vps1", "Agent B"))
    ):
        job = _job(agent, ordinal)
        path = tmp_path / f"job-{ordinal}.json"
        _write(path, job)
        row = {
            "shard_id": host,
            "agent_id": agent,
            "path": str(path),
            "sha256": sha256_file(path),
            "job_identity_sha256": job_identity_sha256(job),
        }
        entries.append(row)
        if host == "vps1" and agent == "Agent A":
            expected.append(job)
    plan = {
        "schema_version": "agentdojo_remaining_849_remote_plan_index/v1",
        "entries": entries,
        "entries_sha256": sha256_object(entries),
    }
    plan_path = tmp_path / "plan.json"
    _write(plan_path, plan)

    _payload, loaded = runner.load_locked_entries(
        plan_path, vps_id="vps1", agent_id="Agent A"
    )

    assert [item.job for item in loaded] == expected


@pytest.mark.parametrize(
    ("agent", "requested", "expected"),
    (
        ("Agent A", None, 8),
        ("Agent A", 16, 8),
        ("Agent B", None, 4),
        ("Agent C", 2, 2),
    ),
)
def test_effective_workers_never_exceeds_locked_lane(
    agent: str, requested: int | None, expected: int
) -> None:
    assert runner.effective_workers(agent, requested) == expected


def test_effective_workers_rejects_zero() -> None:
    with pytest.raises(runner.RunnerError, match="positive"):
        runner.effective_workers("Agent A", 0)


def test_load_locked_entries_rejects_changed_job_bytes(tmp_path: Path) -> None:
    job = _job("Agent A", 0)
    job_path = tmp_path / "job.json"
    _write(job_path, job)
    entry = {
        "shard_id": "vps1",
        "agent_id": "Agent A",
        "path": str(job_path),
        "sha256": "0" * 64,
    }
    plan_path = tmp_path / "plan.json"
    _write(plan_path, {"entries": [entry], "entries_sha256": sha256_object([entry])})

    with pytest.raises(runner.RunnerError, match="bytes differ"):
        runner.load_locked_entries(plan_path, vps_id="vps1", agent_id="Agent A")


def test_publish_controller_identity_binds_live_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "runtime" / "controller.json"
    monkeypatch.setattr(runner, "_linux_boot_id", lambda: "1" * 36)
    monkeypatch.setattr(runner, "_linux_starttime_ticks", lambda _pid: 123)

    payload = runner.publish_controller_identity(
        path, campaign_plan_sha256="a" * 64, vps_id="vps1"
    )

    assert payload["schema_version"] == (
        "agentdojo_remaining_849_controller_identity/v1"
    )
    assert payload["campaign_plan_sha256"] == "a" * 64
    assert payload["vps_id"] == "vps1"
    assert payload["pid"] > 0
    assert payload["starttime_ticks"] > 0
    assert json.loads(path.read_text(encoding="utf-8")) == payload

    resumed = runner.publish_controller_identity(
        path, campaign_plan_sha256="a" * 64, vps_id="vps1"
    )
    assert resumed == payload


def test_controller_identity_rejects_different_live_controller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "runtime" / "controller.json"
    monkeypatch.setattr(runner, "_linux_boot_id", lambda: "1" * 36)
    monkeypatch.setattr(runner, "_linux_starttime_ticks", lambda _pid: 123)
    runner.publish_controller_identity(
        path, campaign_plan_sha256="a" * 64, vps_id="vps1"
    )

    monkeypatch.setattr(runner, "_linux_starttime_ticks", lambda _pid: 456)
    with pytest.raises(runner.RunnerError, match="different controller"):
        runner.publish_controller_identity(
            path, campaign_plan_sha256="a" * 64, vps_id="vps1"
        )


def test_initial_validation_size_is_validation_admissions_alias() -> None:
    args = runner.build_parser().parse_args(
        [
            "--campaign-plan-index", "plan.json",
            "--vps-id", "vps1",
            "--agent", "Agent A",
            "--infra-config", "infra.yaml",
            "--agents-config", "agents.yaml",
            "--source-bundle", "bundle.json",
            "--stage-authorization", "auth.json",
            "--pause-request", "pause.json",
            "--issue-ledger", "issues.jsonl",
            "--controller-identity", "controller.json",
            "--barrier-root", "barriers",
            "--initial-validation-size", "4",
        ]
    )

    assert args.validation_admissions == 4


def test_repository_commit_hash_is_strictly_normalized() -> None:
    value = "9e44f5f816c3910cb18175cf3fd360bff1483ed2e3e285f96ccb2ea56b14382f"

    assert runner._normalize_repository_commit_hash(value) == value
    with pytest.raises(runner.RunnerError, match="lowercase SHA-256"):
        runner._normalize_repository_commit_hash("4a29e3dda49e7b3b52c8ef37979a078ae92097a2")


def test_wait_for_pause_release_never_admits_and_observes_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pause = tmp_path / "pause.json"
    pause.write_text("{}\n", encoding="utf-8")
    polls: list[float] = []

    def release(seconds: float) -> None:
        polls.append(seconds)
        pause.unlink()

    monkeypatch.setattr(runner.time, "sleep", release)

    runner._wait_for_pause_release(pause, poll_seconds=0.25)

    assert polls == [0.25]


def test_wait_for_pause_release_rejects_symlink(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    pause = tmp_path / "pause.json"
    pause.symlink_to(target)

    with pytest.raises(runner.HardFatal, match="regular file"):
        runner._wait_for_pause_release(pause, poll_seconds=0.25)


def test_execution_context_reuses_verified_sealed_command_hash(
    tmp_path: Path,
) -> None:
    source_bundle = tmp_path / "source-bundle.json"
    source_bundle.write_text("{}\n", encoding="utf-8")
    sealed_hash = "b" * 64
    entry = runner.LockedEntry(
        ordinal=0,
        vps_id="vps1",
        agent_id="Agent A",
        job_path=tmp_path / "job.json",
        job_file_sha256="a" * 64,
        job={
            "benchmark_config_hash": "c" * 64,
            "benchmark_name": "agentdojo",
            "official_split_hash": "d" * 64,
        },
    )
    target = SimpleNamespace(
        machine_id="machine",
        machine_role="runner",
        ssh_host="127.0.0.1",
        ssh_port=22,
        remote_workdir="/remote",
        runner_workdir="/runner",
        benchmark_name="agentdojo",
    )

    context = runner._execution_context(
        target=target,
        entry=entry,
        source_bundle_path=source_bundle,
        command="a newly reconstructed command",
        producer_command_sha256=sealed_hash,
    )

    assert context["producer_command_sha256"] == sealed_hash


def test_formal_descriptor_compatibility_is_targeted_and_idempotent() -> None:
    evaluator = ArtifactDescriptor(
        local_path=Path("native_evaluator_output.json"),
        artifact_type="native_evaluator_output",
        producer_role="official_evaluator",
        producer_name="agentdojo-0.1.35",
        producer_version="0.1.35",
        official_runner=True,
        official_evaluator=True,
    )
    trace = ArtifactDescriptor(
        local_path=Path("trace_logs"),
        artifact_type="trace",
        producer_role="official_runner",
        producer_name="agentdojo-0.1.35",
        producer_version="0.1.35",
        official_runner=True,
        official_evaluator=False,
    )

    first = runner._map_formal_descriptor_contract_ids((evaluator, trace))
    second = runner._map_formal_descriptor_contract_ids(first)

    assert first == second
    assert first[0].artifact_contract_requirement_ids == (
        "smoke-native-evaluator-output",
    )
    assert first[1] is trace


def test_wait_for_supervisor_process_exit_handles_exit_receipt_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed = iter((123, 123))
    monkeypatch.setattr(
        runner.supervisor,
        "_verify_state",
        lambda *_args, **_kwargs: {
            "supervisor_pid": 99,
            "supervisor_starttime_ticks": 123,
        },
    )

    def starttime(_pid: int) -> int:
        try:
            return next(observed)
        except StopIteration as exc:
            raise FileNotFoundError from exc

    monkeypatch.setattr(runner, "_linux_starttime_ticks", starttime)
    monkeypatch.setattr(runner, "_linux_process_state", lambda _pid: "R")
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)

    runner._wait_for_supervisor_process_exit(
        tmp_path, session_id="session-test", maximum_wait_seconds=1.0
    )


def test_wait_for_supervisor_process_exit_reaps_owned_zombie(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        runner.supervisor,
        "_verify_state",
        lambda *_args, **_kwargs: {
            "supervisor_pid": 99,
            "supervisor_starttime_ticks": 123,
        },
    )
    monkeypatch.setattr(runner, "_linux_starttime_ticks", lambda _pid: 123)
    monkeypatch.setattr(runner, "_linux_process_state", lambda _pid: "Z")
    reaped: list[tuple[int, int]] = []
    monkeypatch.setattr(
        runner.os,
        "waitpid",
        lambda pid, flags: reaped.append((pid, flags)) or (pid, 0),
    )

    runner._wait_for_supervisor_process_exit(
        tmp_path, session_id="session-test", maximum_wait_seconds=1.0
    )

    assert reaped == [(99, runner.os.WNOHANG)]


def test_repair_prematurely_sealed_stream_modes_restores_only_streams(
    tmp_path: Path,
) -> None:
    untouched = tmp_path / "worker-success.json"
    untouched.write_text("control metadata\n", encoding="utf-8")
    untouched.chmod(0o400)
    streams = [tmp_path / name for name in runner.postprocessor.SEALED_STREAMS]
    for stream in streams:
        stream.write_text("not inspected\n", encoding="utf-8")
        stream.chmod(0o400)

    runner._repair_prematurely_sealed_stream_modes(tmp_path)

    assert [stream.stat().st_mode & 0o777 for stream in streams] == [0o600, 0o600]
    assert untouched.stat().st_mode & 0o777 == 0o400


def test_repair_prematurely_sealed_stream_modes_rejects_unsafe_mode(
    tmp_path: Path,
) -> None:
    streams = [tmp_path / name for name in runner.postprocessor.SEALED_STREAMS]
    for stream in streams:
        stream.write_text("not inspected\n", encoding="utf-8")
        stream.chmod(0o600)
    streams[0].chmod(0o644)

    with pytest.raises(runner.HardFatal, match="metadata is unsafe"):
        runner._repair_prematurely_sealed_stream_modes(tmp_path)
