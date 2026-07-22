from __future__ import annotations

import grp
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from evidence_system.adapters import agentdojo_formal_postprocessor as postprocessor
from evidence_system.adapters import runtime
from evidence_system.adapters.agentdojo_runtime_control import job_identity_sha256
from evidence_system.adapters.runtime import formal_job_binding_sha256
from evidence_system.core.hashing import sha256_object
from evidence_system.core.paths import repo_root


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def _job() -> dict[str, object]:
    path = (
        repo_root()
        / "experiments/agentdojo_full_v1.2.2_direct/jobs/full/"
        "full-agentdojo-v1.2.2-workspace-user_task_1-injection_task_9-agent_a.json"
    )
    job = json.loads(path.read_text(encoding="utf-8"))
    runtime_policy = {
        "schema_version": "agentdojo_openrouter_runtime_policy/test",
        "policy_id": "formal-postprocessor-acceptance-fixture",
    }
    job.update(
        {
            "execution_lock_sha256": "a" * 64,
            "execution_policy_sha256": "b" * 64,
            "openrouter_runtime_policy": runtime_policy,
            "openrouter_runtime_policy_sha256": sha256_object(runtime_policy),
            "openrouter_runtime_policy_file_sha256": "1" * 64,
            "result_namespace": "agentdojo_full_v1.2.2_direct_execution_staging",
            "formal_wall_clock_timeout_seconds": 7200,
        }
    )
    return job


def _execution_context(job: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "agentdojo_formal_execution_context/v1",
        "machine_id": "agentdojo-vultr-64-177-120-135",
        "machine_role": "agentdojo_full_vps",
        "ssh_host": "64.177.120.135",
        "ssh_port": 22,
        "remote_workdir": "/srv/agentdojo-full/repo",
        "runner_workdir": "/srv/agentdojo-full/repo",
        "benchmark_name": "AgentDojo",
        "benchmark_config_hash": job["benchmark_config_hash"],
        "source_bundle_hash": "2" * 64,
        "official_split_hash": "3" * 64,
        "producer_command_sha256": __import__("hashlib").sha256(b"true").hexdigest(),
    }


def _attempt(root: Path, job: dict[str, object], *, session_id: str = "session-1") -> Path:
    root.mkdir(parents=True, mode=0o700)
    binding = {
        "execution_lock_sha256": job["execution_lock_sha256"],
        "execution_policy_sha256": job["execution_policy_sha256"],
        "job_binding_sha256": formal_job_binding_sha256(job),
        "job_identity_sha256": job_identity_sha256(job),
    }
    _write_json(root / "formal_job_launch_intent.json", {"launch": True})
    _write_json(
        root / "formal_supervisor_spec.json",
        {
            "schema_version": "agentdojo_formal_supervisor_spec/v1",
            "stage_id": "canary-4",
            "session_id": session_id,
            "job_binding_sha256": binding["job_binding_sha256"],
            "stage_authorization_sha256": "c" * 64,
            "formal_wall_clock_timeout_seconds": 7200,
            "kill_grace_seconds": 30,
            "command_sha256": __import__("hashlib").sha256(b"true").hexdigest(),
            "command": "true",
        },
    )
    supervisor_claim = {
        "schema_version": "agentdojo_formal_supervisor_claim/v2",
        "stage_id": "canary-4",
        "session_id": session_id,
        "job_binding_sha256": binding["job_binding_sha256"],
        "stage_authorization_sha256": "c" * 64,
        "supervisor_pid": 999_999_999,
        "supervisor_pgid": 999_999_999,
        "supervisor_session_id": 999_999_999,
        "supervisor_starttime_ticks": 1,
        "host_boot_id": "00000000-0000-0000-0000-000000000001",
        "spec_sha256": postprocessor.sha256_file(
            root / "formal_supervisor_spec.json"
        ),
        "claimed_boottime_seconds": 90.0,
        "bootstrap_deadline_boottime_seconds": 120.0,
    }
    _write_json(root / "formal_supervisor_claim.json", supervisor_claim)
    _write_json(
        root / "formal_job_started.json",
        {
            "schema_version": "agentdojo_formal_job_started/v2",
            "started_at": "2026-07-16T00:00:00+00:00",
            "deadline_at": "2026-07-16T02:00:00+00:00",
            "formal_wall_clock_timeout_seconds": 7200,
            "pid": 12345,
            "linux_starttime_ticks": 1,
            "stage_authorization_sha256": "c" * 64,
            "formal_stage_id": "canary-4",
            "formal_stage_session_id": session_id,
            **binding,
        },
    )
    supervisor_state = {
        "schema_version": "agentdojo_formal_supervisor_state/v2",
        "stage_id": "canary-4",
        "session_id": session_id,
        "job_binding_sha256": binding["job_binding_sha256"],
        "stage_authorization_sha256": "c" * 64,
        "spec_sha256": postprocessor.sha256_file(root / "formal_supervisor_spec.json"),
        "claim_sha256": postprocessor.sha256_file(root / "formal_supervisor_claim.json"),
        "supervisor_pid": 999_999_999,
        "supervisor_pgid": 999_999_999,
        "supervisor_session_id": 999_999_999,
        "supervisor_starttime_ticks": 1,
        "worker_pid": 999_999_998,
        "worker_pgid": 999_999_998,
        "worker_session_id": 999_999_998,
        "worker_starttime_ticks": 2,
        "launched_host_boot_id": "00000000-0000-0000-0000-000000000001",
        "launched_boottime_seconds": 100.0,
        "deadline_boottime_seconds": 7300.0,
        "formal_wall_clock_timeout_seconds": 7200,
        "kill_grace_seconds": 30,
    }
    _write_json(
        root / postprocessor.SUPERVISOR_STATE,
        supervisor_state,
    )
    _write_json(
        root / postprocessor.SUPERVISOR_EXIT,
        {
            "schema_version": "agentdojo_formal_supervisor_exit/v2",
            "stage_id": "canary-4",
            "session_id": session_id,
            "job_binding_sha256": binding["job_binding_sha256"],
            "stage_authorization_sha256": "c" * 64,
            "spec_sha256": supervisor_state["spec_sha256"],
            "claim_sha256": supervisor_state["claim_sha256"],
            "state_sha256": sha256_object(supervisor_state),
            "supervisor_pid": supervisor_state["supervisor_pid"],
            "supervisor_pgid": supervisor_state["supervisor_pgid"],
            "supervisor_session_id": supervisor_state["supervisor_session_id"],
            "supervisor_starttime_ticks": supervisor_state[
                "supervisor_starttime_ticks"
            ],
            "worker_pid": supervisor_state["worker_pid"],
            "worker_pgid": supervisor_state["worker_pgid"],
            "worker_session_id": supervisor_state["worker_session_id"],
            "worker_starttime_ticks": supervisor_state["worker_starttime_ticks"],
            "launched_host_boot_id": supervisor_state["launched_host_boot_id"],
            "finished_host_boot_id": supervisor_state["launched_host_boot_id"],
            "finished_boottime_seconds": 110.0,
            "exit_code": 0,
            "outcome": "worker_exited",
            "timed_out": False,
            "term_sent": False,
            "kill_sent": False,
            "group_gone": True,
            "bootstrap_terminal": False,
        },
    )
    _write_json(
        root / "formal_worker_success.json",
        {
            "schema_version": "agentdojo_formal_worker_success/v1",
            "finished_at": "2026-07-16T00:00:00+00:00",
            **binding,
            "stage_authorization_sha256": "c" * 64,
            "formal_stage_id": "canary-4",
            "formal_stage_session_id": session_id,
            "expected_episode_count": 3,
            "worker_status": "completed",
        },
    )
    for name in postprocessor.SEALED_STREAMS:
        (root / name).write_text("", encoding="utf-8")
        os.chmod(root / name, 0o600)
    _version, suite, user_task, injection_task = str(job["case_unit_id"]).split(":")
    trace_root = root / "trace_logs" / "local" / suite
    _write_json(trace_root / injection_task / "none" / "none.json", {"episode": 1})
    _write_json(trace_root / user_task / "none" / "none.json", {"episode": 2})
    _write_json(
        trace_root / user_task / "direct" / f"{injection_task}.json",
        {"episode": 3},
    )
    _write_json(
        root / "run_summary.json",
        {
            "status": "completed",
            "benign_utility": True,
            "injected_utility": True,
            "injected_security": False,
        },
    )
    _write_json(root / "job.json", job)
    _write_json(root / "source_bundle_entry.json", {"source": "fixture"})
    _write_json(root / "worker_config.json", {"worker": "fixture"})
    _write_json(root / "seed_verification.json", {"seed": job["seed"]})
    _write_json(root / "install_verification.json", {"version": "0.1.35"})
    _write_json(
        root / "runtime_policy_verification.json",
        {
            "execution_lock_sha256": job["execution_lock_sha256"],
            "execution_policy_sha256": job["execution_policy_sha256"],
            "openrouter_runtime_policy_sha256": job[
                "openrouter_runtime_policy_sha256"
            ],
            "openrouter_runtime_policy_file_sha256": job[
                "openrouter_runtime_policy_file_sha256"
            ],
        },
    )
    return root


@pytest.fixture
def blind_group() -> str:
    return grp.getgrgid(os.getgid()).gr_name


@pytest.fixture(autouse=True)
def portable_noreplace(monkeypatch: pytest.MonkeyPatch) -> None:
    def rename(source: Path, destination: Path) -> None:
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        os.rename(source, destination)

    monkeypatch.setattr(postprocessor, "_rename_noreplace", rename)


def test_postprocessor_publishes_exact_canonical_tree_and_reuses_it(
    tmp_path: Path, blind_group: str
) -> None:
    job = _job()
    attempt = _attempt(tmp_path / "attempt", job)
    raw_parent = tmp_path / "raw"
    raw_parent.mkdir(mode=0o700)
    blind = tmp_path / "blind"
    blind.mkdir(mode=0o700)
    canonical = raw_parent / formal_job_binding_sha256(job)

    published = postprocessor.publish_or_verify_success(
        job=job,
        attempt_root=attempt,
        canonical_root=canonical,
        completion_index=blind / "completed.jsonl",
        authorization_sha256="c" * 64,
        stage_id="canary-4",
        session_id="session-1",
        blind_group=blind_group,
        execution_context=_execution_context(job),
        lifecycle_lock=blind / ".canonical-lifecycle.lock",
    )
    assert published["status"] == "canonical_published"
    assert published["native_episode_count"] == 3
    assert {path.name for path in canonical.iterdir()} == {"adapter"}
    verified = postprocessor.verify_canonical_job(canonical, job=job)
    assert verified["marker"]["native_episode_count"] == 3

    reused = postprocessor.publish_or_verify_success(
        job=job,
        attempt_root=attempt,
        canonical_root=canonical,
        completion_index=blind / "completed.jsonl",
        authorization_sha256="c" * 64,
        stage_id="canary-4",
        session_id="session-1",
        blind_group=blind_group,
        execution_context=_execution_context(job),
        lifecycle_lock=blind / ".canonical-lifecycle.lock",
    )
    assert reused["status"] == "canonical_reused"
    assert len((blind / "completed.jsonl").read_text().splitlines()) == 1


def test_postprocessor_common_tree_passes_blind_acceptance_validator(
    tmp_path: Path,
    blind_group: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evidence_system.contracts import agentdojo_full_evidence as acceptance
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    job = _job()
    execution_lock_file = fake_repo / "lock/execution_lock.json"
    _write_json(execution_lock_file, {"definition": {"job_plan": {"entries": []}}})
    job["execution_lock_path"] = "lock/execution_lock.json"
    attempt = _attempt(tmp_path / "attempt", job)
    remote_raw = tmp_path / "remote-raw"
    remote_raw.mkdir(mode=0o700)
    blind = tmp_path / "blind"
    blind.mkdir(mode=0o700)
    binding = formal_job_binding_sha256(job)
    remote_canonical = remote_raw / binding
    journal = blind / "completed.jsonl"
    postprocessor.publish_or_verify_success(
        job=job,
        attempt_root=attempt,
        canonical_root=remote_canonical,
        completion_index=journal,
        authorization_sha256="c" * 64,
        stage_id="canary-4",
        session_id="session-1",
        blind_group=blind_group,
        execution_context=_execution_context(job),
        lifecycle_lock=blind / ".canonical-lifecycle.lock",
    )
    real_resolve = acceptance.resolve_repo_path

    def resolve_fake_results(value: str | Path) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute() and candidate.parts[0] in {"results", "lock"}:
            return fake_repo / candidate
        return real_resolve(candidate)

    monkeypatch.setattr(acceptance, "resolve_repo_path", resolve_fake_results)
    monkeypatch.setattr(acceptance, "repo_root", lambda: fake_repo)
    monkeypatch.setattr(acceptance, "verify_job_binding", lambda *_args, **_kwargs: None)

    staging_root = (
        fake_repo
        / "results/namespaces"
        / str(job["result_namespace"])
        / "full/agentdojo"
    )
    staging_root.mkdir(parents=True)
    local_job_root = staging_root / str(job["job_id"])
    os.rename(remote_canonical, local_job_root)
    inventory = acceptance._tree_inventory(staging_root)
    inventory_by_path = inventory.by_path()
    job_inventory = tuple(
        item
        for item in inventory.files
        if str(item["relative_path"]).startswith(f"{job['job_id']}/")
    )
    journal_entry = json.loads(journal.read_text(encoding="utf-8"))
    remote_entry = {
        key: value for key, value in journal_entry.items() if key != "recorded_at"
    }
    remote_entry["schema_version"] = (
        "agentdojo_formal_remote_completion_index_entry/v2"
    )
    expected = {
        field: job[field]
        for field in (
            "job_id",
            "case_unit_id",
            "task_id",
            "record_slot_id",
            "run_id",
            "attempt_id",
            "seed",
            "agent_id",
        )
    }
    accepted = acceptance._validate_staging_job(
        staging_root=staging_root,
        inventory=inventory,
        inventory_by_path=inventory_by_path,
        job_inventory_files=job_inventory,
        expected=expected,
        execution_lock_file=execution_lock_file,
        execution_lock_payload={"definition": {"job_plan": {"entries": []}}},
        execution_lock_sha=str(job["execution_lock_sha256"]),
        execution_policy_sha=str(job["execution_policy_sha256"]),
        runtime_policy_semantic_sha=str(job["openrouter_runtime_policy_sha256"]),
        runtime_policy_file_sha=str(
            job["openrouter_runtime_policy_file_sha256"]
        ),
        source_bundle_sha="2" * 64,
        manifest_sha=str(job["manifest_hash"]),
        staging_namespace=str(job["result_namespace"]),
        remote_entries_by_binding={binding: remote_entry},
    )
    assert accepted["job_binding_sha256"] == binding
    assert accepted["native_trajectory_file_count"] == 3
    assert accepted["formal_completion_marker_sha256"] == remote_entry[
        "completion_marker_file_sha256"
    ]


def test_postprocessor_rejects_canonical_artifact_mutation(
    tmp_path: Path, blind_group: str
) -> None:
    job = _job()
    attempt = _attempt(tmp_path / "attempt", job)
    raw_parent = tmp_path / "raw"
    raw_parent.mkdir(mode=0o700)
    blind = tmp_path / "blind"
    blind.mkdir(mode=0o700)
    canonical = raw_parent / formal_job_binding_sha256(job)
    postprocessor.publish_or_verify_success(
        job=job,
        attempt_root=attempt,
        canonical_root=canonical,
        completion_index=blind / "completed.jsonl",
        authorization_sha256="c" * 64,
        stage_id="canary-4",
        session_id="session-1",
        blind_group=blind_group,
        execution_context=_execution_context(job),
        lifecycle_lock=blind / ".canonical-lifecycle.lock",
    )
    trace = (
        canonical
        / "adapter/native_run/trace_logs/local/workspace/user_task_1/direct/injection_task_9.json"
    )
    _write_json(trace, {"episode": "tampered"})
    with pytest.raises(RuntimeError, match="artifact (digest|manifest|tree)"):
        postprocessor.verify_canonical_job(canonical, job=job)


def test_failed_attempt_is_sealed_without_canonical_publication(
    tmp_path: Path, blind_group: str
) -> None:
    job = _job()
    attempt = _attempt(tmp_path / "attempt", job)
    exit_path = attempt / postprocessor.SUPERVISOR_EXIT
    exited = json.loads(exit_path.read_text())
    exited["exit_code"] = 17
    _write_json(exit_path, exited)
    blind = tmp_path / "blind"
    blind.mkdir(mode=0o700)
    raw = tmp_path / "raw"
    raw.mkdir(mode=0o700)
    failed_archive = tmp_path / "failed-archive"
    failed_archive.mkdir(mode=0o700)

    result = postprocessor.archive_failed_attempt(
        job=job,
        attempt_root=attempt,
        failed_attempt_index=blind / "failed.jsonl",
        authorization_sha256="c" * 64,
        stage_id="canary-4",
        session_id="session-1",
        failure_category="worker_error",
        worker_exit_code=17,
        blind_group=blind_group,
        canonical_root=raw / formal_job_binding_sha256(job),
        failed_archive_root=failed_archive,
        lifecycle_lock=blind / ".canonical-lifecycle.lock",
    )
    assert result["status"] == "failed_attempt_archived"
    assert not attempt.exists()
    archived = (
        failed_archive / formal_job_binding_sha256(job) / "session-1"
    )
    assert (archived / postprocessor.ATTEMPT_FAILURE).is_file()
    entry = json.loads((blind / "failed.jsonl").read_text())
    assert entry["contains_case_agent_prompt_response_trajectory_evaluator_or_label"] is False


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO requires POSIX")
def test_formal_inventories_reject_fifo(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    os.mkfifo(root / "untrusted.fifo", 0o600)

    with pytest.raises(RuntimeError, match="special"):
        postprocessor._inventory(root, excluded=set())
    with pytest.raises(runtime.AdapterRuntimeError, match="special inode"):
        runtime.formal_native_tree_inventory(root)


def test_formal_inventories_reject_hardlink(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    original = root / "original.json"
    original.write_text("{}\n", encoding="utf-8")
    os.link(original, root / "alias.json")

    with pytest.raises(RuntimeError, match="hard-linked"):
        postprocessor._inventory(root, excluded=set())
    with pytest.raises(runtime.AdapterRuntimeError, match="hard-linked"):
        runtime.formal_native_tree_inventory(root)


def test_formal_inventories_reject_simulated_device_inode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    device = root / "device"
    device.write_bytes(b"")
    real_lstat = os.lstat

    def simulated_lstat(path: object) -> object:
        if Path(path) == device:
            return SimpleNamespace(st_mode=stat.S_IFCHR | 0o600, st_nlink=1)
        return real_lstat(path)

    monkeypatch.setattr(postprocessor.os, "lstat", simulated_lstat)
    with pytest.raises(RuntimeError, match="special"):
        postprocessor._inventory(root, excluded=set())

    monkeypatch.setattr(runtime.os, "lstat", simulated_lstat)
    with pytest.raises(runtime.AdapterRuntimeError, match="special inode"):
        runtime.formal_native_tree_inventory(root)
