from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from evidence_system.adapters import agentdojo, agentdojo_worker, runtime
from evidence_system.cli import run_full
from evidence_system.contracts.common import load_mapping
from evidence_system.core.schemas import validate_object
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.contracts.agentdojo_execution_namespace import (
    FORMAL_STAGE_AUTHORIZATION_FIELDS,
    assert_formal_stage_authorization_current,
    verify_formal_stage_authorization,
)
from evidence_system.adapters.agentdojo_runtime_control import (
    execution_runtime_snapshot,
)
from evidence_system.adapters.runtime import (
    formal_job_binding_sha256,
    formal_job_file_sha256,
)
from evidence_system.orchestrator.jobs import (
    PlannedJob,
    _formal_effective_worker_count,
    execute_planned_jobs,
    plan_smoke_jobs,
    resolve_result_namespace,
    validate_namespaced_manifest_inputs,
)
from neurips_ed_track_minimal.scripts import run_agentdojo_score_batch as score_batch
from neurips_ed_track_minimal.scripts import export_agentdojo_scores_csv as score_export


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("remaining_count", [1, 3, 5, 31])
def test_formal_recovery_effective_workers_allow_non_ramp_remaining_counts(
    remaining_count: int,
) -> None:
    assert _formal_effective_worker_count(
        remaining_count=remaining_count, requested_ceiling=32
    ) == remaining_count


def test_formal_recovery_effective_workers_cap_at_authorized_ceiling() -> None:
    assert _formal_effective_worker_count(
        remaining_count=949, requested_ceiling=32
    ) == 32


def _formal_authorization_fixture(
    tmp_path: Path,
) -> tuple[dict[str, object], Path, dict[str, object], str, str, str]:
    lock_sha = "1" * 64
    execution_policy_sha = "2" * 64
    plan_sha = "3" * 64
    runtime_policy_sha = "4" * 64
    runtime_policy_file_sha = "5" * 64
    runtime_state_root = tmp_path / "runtime-state"
    runtime_state_root.mkdir()
    job: dict[str, object] = {
        "phase": "full",
        "result_namespace": "formal-test",
        "execution_lock_sha256": lock_sha,
        "execution_policy_sha256": execution_policy_sha,
        "agent_id": "Agent A",
        "job_id": "formal-job-a",
        "record_slot_id": "slot-a",
    }
    namespace = {
        "schema_version": "agentdojo_formal_execution_namespace_init_receipt/v2",
        "status": "initialized_empty_namespaces",
        "definition": {
            "execution_lock": {"path": "lock.json", "sha256": lock_sha},
            "execution_policy_sha256": execution_policy_sha,
            "plan_index": {"path": "plan.json", "sha256": plan_sha},
            "runtime_state_root": str(runtime_state_root),
            "runtime_sync_after_init_forbidden": True,
        },
    }
    namespace_path = tmp_path / "namespace-init.json"
    namespace_path.write_text(json.dumps(namespace) + "\n", encoding="utf-8")
    model_sha = "6" * 64
    binding = formal_job_binding_sha256(job)
    payload: dict[str, object] = {
        "schema_version": "agentdojo_formal_stage_authorization/v1",
        "status": "authorized",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_lock_sha256": lock_sha,
        "execution_policy_sha256": execution_policy_sha,
        "plan_index_sha256": plan_sha,
        "namespace_init_receipt": {
            "path": str(namespace_path),
            "sha256": sha256_file(namespace_path),
        },
        "stage_id": "canary",
        "session_id": "session-unit-test",
        "stage_order_index": 0,
        "locked_workers": 4,
        "workers": 4,
        "record_slot_count": 1,
        "record_slot_ids_sha256": sha256_object(["slot-a"]),
        "allowed_job_binding_sha256": [binding],
        "allowed_job_bindings_sha256": sha256_object([binding]),
        "allowed_job_file_sha256": [formal_job_file_sha256(job)],
        "allowed_job_files_sha256": sha256_object(
            [formal_job_file_sha256(job)]
        ),
        "allowed_model_config_sha256": [model_sha],
        "allowed_model_configs_sha256": sha256_object([model_sha]),
        "runtime_policy_semantic_sha256": runtime_policy_sha,
        "runtime_policy_file_sha256": runtime_policy_file_sha,
        "runtime_infra_file_sha256": "7" * 64,
        "runtime_state_root": str(runtime_state_root),
        "runtime_snapshot": execution_runtime_snapshot(),
        "previous_health_receipt": None,
        "formal_wall_clock_timeout_seconds": 7_200,
        "kill_grace_seconds": 30,
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    assert set(payload) == FORMAL_STAGE_AUTHORIZATION_FIELDS
    authorization_path = tmp_path / "stage-authorization.json"
    authorization_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    authorization_path.chmod(0o600)
    return (
        job,
        authorization_path,
        payload,
        runtime_policy_sha,
        runtime_policy_file_sha,
        model_sha,
    )


def _verify_fixture_authorization(
    fixture: tuple[dict[str, object], Path, dict[str, object], str, str, str]
):
    job, path, _payload, runtime_policy_sha, runtime_policy_file_sha, _model = fixture
    return verify_formal_stage_authorization(
        path=path,
        expected_sha256=sha256_file(path),
        job=job,
        expected_runtime_policy_semantic_sha256=runtime_policy_sha,
        expected_runtime_policy_file_sha256=runtime_policy_file_sha,
        expected_runtime_state_dir=str(path.parent / "runtime-state"),
    )


def test_formal_worker_rejects_missing_stage_authorization(tmp_path: Path) -> None:
    fixture = _formal_authorization_fixture(tmp_path)
    job, _path, _payload, policy_sha, policy_file_sha, _model = fixture
    with pytest.raises(RuntimeError, match="requires a stage authorization"):
        verify_formal_stage_authorization(
            path=None,
            expected_sha256="0" * 64,
            job=job,
            expected_runtime_policy_semantic_sha256=policy_sha,
            expected_runtime_policy_file_sha256=policy_file_sha,
            expected_runtime_state_dir=tmp_path / "runtime-state",
        )


def test_formal_worker_rejects_closed_stage_authorization(tmp_path: Path) -> None:
    fixture = _formal_authorization_fixture(tmp_path)
    job, path, payload, policy_sha, policy_file_sha, _model = fixture
    payload["status"] = "closed"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="status/schema"):
        verify_formal_stage_authorization(
            path=path,
            expected_sha256=sha256_file(path),
            job=job,
            expected_runtime_policy_semantic_sha256=policy_sha,
            expected_runtime_policy_file_sha256=policy_file_sha,
            expected_runtime_state_dir=tmp_path / "runtime-state",
        )


def test_formal_worker_rechecks_stage_authorization_before_request(
    tmp_path: Path,
) -> None:
    fixture = _formal_authorization_fixture(tmp_path)
    job, path, payload, policy_sha, _policy_file_sha, model_sha = fixture
    authorization = _verify_fixture_authorization(fixture)
    payload["status"] = "closed"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    policy = SimpleNamespace(semantic_sha256=policy_sha)
    with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
        assert_formal_stage_authorization_current(
            authorization,
            job=job,
            policy=policy,
            model_config_sha256=model_sha,
        )


def test_formal_worker_rejects_job_outside_stage_authorization(
    tmp_path: Path,
) -> None:
    fixture = _formal_authorization_fixture(tmp_path)
    job, path, payload, policy_sha, policy_file_sha, _model = fixture
    outside = formal_job_binding_sha256({**job, "job_id": "outside"})
    payload["allowed_job_binding_sha256"] = [outside]
    payload["allowed_job_bindings_sha256"] = sha256_object([outside])
    payload["allowed_job_file_sha256"] = [
        formal_job_file_sha256({**job, "job_id": "outside"})
    ]
    payload["allowed_job_files_sha256"] = sha256_object(
        payload["allowed_job_file_sha256"]
    )
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not a member"):
        verify_formal_stage_authorization(
            path=path,
            expected_sha256=sha256_file(path),
            job=job,
            expected_runtime_policy_semantic_sha256=policy_sha,
            expected_runtime_policy_file_sha256=policy_file_sha,
            expected_runtime_state_dir=tmp_path / "runtime-state",
        )


def test_prelock_full_job_set_cannot_reach_adapter_or_ssh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"adapter": 0, "ssh": 0}

    def adapter_call(*_args, **_kwargs):
        calls["adapter"] += 1
        raise AssertionError("adapter must not be reached")

    def ssh_call(*_args, **_kwargs):
        calls["ssh"] += 1
        raise AssertionError("SSH must not be reached")

    monkeypatch.setattr(agentdojo, "execute_smoke_job", adapter_call)
    monkeypatch.setattr(runtime, "_run_subprocess", ssh_call)
    old_job = PlannedJob(
        job={
            "domain": "agentdojo",
            "phase": "full",
            "result_namespace": "agentdojo_full_v1.2.2_direct",
            "job_id": "prelock-job",
        },
        job_path=tmp_path / "prelock-job.json",
        official_split_hash="0" * 64,
        execution_plan={"status": "runnable"},
    )
    with pytest.raises(ValueError, match="pre-lock.*mapping input only"):
        execute_planned_jobs(
            [old_job],
            manifest_path=tmp_path / "not-read.json",
            source_bundle_path=tmp_path / "not-read.json",
            infra_config_path=tmp_path / "not-read.json",
            agents_config_path=tmp_path / "not-read.json",
        )
    assert calls == {"adapter": 0, "ssh": 0}


def test_agentdojo_adapter_never_syncs_controller_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[bool] = []

    class StopAfterSync(RuntimeError):
        pass

    def sync(_target, **kwargs):
        observed.append(bool(kwargs.get("include_dotenv")))
        raise StopAfterSync

    monkeypatch.setattr(agentdojo, "sync_repo_support_files", sync)
    monkeypatch.setattr(
        runtime, "resolve_repo_path", lambda path: tmp_path / Path(path)
    )
    with pytest.raises(StopAfterSync):
        agentdojo.execute_smoke_job(
            {"phase": "smoke", "domain": "agentdojo", "job_id": "no-dotenv"},
            target=SimpleNamespace(),
            execution_plan={},
            context=SimpleNamespace(),
        )
    assert observed == [False]


def test_legacy_and_namespaced_result_paths_are_disjoint(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        runtime, "resolve_repo_path", lambda path: tmp_path / Path(path)
    )
    base_job = {
        "phase": "full",
        "domain": "agentdojo",
        "job_id": "full-agentdojo-case-agent_a",
    }

    legacy = runtime.build_job_paths(base_job)
    marker = legacy.root / "must-survive.txt"
    marker.write_text("legacy", encoding="utf-8")
    namespaced = runtime.build_job_paths(
        {**base_job, "result_namespace": "agentdojo_full_v1.2.2_direct"}
    )

    assert (
        legacy.root
        == tmp_path / "results/full/agentdojo/full-agentdojo-case-agent_a/adapter"
    )
    assert namespaced.root == (
        tmp_path
        / "results/namespaces/agentdojo_full_v1.2.2_direct/full/agentdojo"
        / "full-agentdojo-case-agent_a/adapter"
    )
    assert legacy.root not in namespaced.root.parents
    assert marker.read_text(encoding="utf-8") == "legacy"


def test_agentdojo_remote_result_path_uses_same_namespace_layout() -> None:
    target = SimpleNamespace(remote_workdir="/srv/evidence")
    base_job = {
        "phase": "full",
        "domain": "agentdojo",
        "job_id": "full-agentdojo-case-agent_a",
    }

    assert agentdojo._remote_output_dir(target, base_job) == (
        "/srv/evidence/results/full/agentdojo/full-agentdojo-case-agent_a"
    )
    assert agentdojo._remote_output_dir(
        target,
        {**base_job, "result_namespace": "agentdojo_full_v1.2.2_direct"},
    ) == (
        "/srv/evidence/results/namespaces/agentdojo_full_v1.2.2_direct/full/agentdojo/"
        "full-agentdojo-case-agent_a"
    )


@pytest.mark.parametrize("value", ["../full", "full/agentdojo", ".", "", "white space"])
def test_result_namespace_rejects_unsafe_or_aliasing_values(value: str) -> None:
    with pytest.raises(ValueError, match="result_namespace must match"):
        runtime.normalize_result_namespace(value)


def test_manifest_result_namespace_is_injected_without_changing_legacy_job_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # This test isolates job construction. The synthetic v1/v2/currentness behavior
    # of the formal execution gate is covered by test_agentdojo_full_execution_gate.
    monkeypatch.setattr(
        "evidence_system.orchestrator.jobs.validate_namespaced_manifest_inputs",
        lambda **_: None,
    )
    full_root = ROOT / "experiments/agentdojo_full_v1.2.2_direct"
    planned = plan_smoke_jobs(
        domain="agentdojo",
        phase="full",
        experiment_type="appendix",
        case_count=1,
        agent_ids=["Agent A"],
        seed=7,
        manifest_path=full_root / "experiment_manifest.yaml",
        source_bundle_path=full_root / "source_bundles/case_packet_source_bundle.json",
        contracts_dir=full_root / "evidence_contracts/drafts",
        infra_config_path=ROOT / "configs/infra.yaml",
        agents_config_path=ROOT / "configs/agents.yaml",
        jobs_dir=tmp_path / "namespaced_jobs",
    )[0]

    assert planned.job["result_namespace"] == "agentdojo_full_v1.2.2_direct"
    assert "agentdojo_full_v1.2.2_direct" not in planned.job["job_id"]
    # A legacy test bypass of the manifest/checklist gate must still not create
    # a runnable full command without the independent execution/runtime lock.
    assert planned.execution_plan["runner_command"] is None
    assert planned.execution_plan["status"] == "blocked"
    assert "frozen openrouter_runtime_policy" in str(
        planned.execution_plan["blocking_reason"]
    )
    assert validate_object("job", planned.job, raise_on_error=False).ok


def test_explicit_namespace_must_match_locked_manifest_value() -> None:
    with pytest.raises(ValueError, match="does not match manifest"):
        resolve_result_namespace(
            manifest={"result_namespace": "locked_run_set"},
            requested="different_run_set",
        )


def test_namespaced_manifest_input_hashes_fail_closed(tmp_path: Path) -> None:
    source_bundle = tmp_path / "source_bundle.json"
    infra_config = tmp_path / "infra.yaml"
    agents_config = tmp_path / "agents.yaml"
    source_bundle.write_text("{}\n", encoding="utf-8")
    infra_config.write_text("machines: []\n", encoding="utf-8")
    agents_config.write_text("agents: []\n", encoding="utf-8")
    manifest = {
        "source_bundle_hash": "0" * 64,
        "infra_config_hash": sha256_file(infra_config),
        "agents_config_hash": sha256_file(agents_config),
    }

    with pytest.raises(ValueError, match="source_bundle_hash"):
        validate_namespaced_manifest_inputs(
            manifest=manifest,
            source_bundle_path=source_bundle,
            infra_config_path=infra_config,
            agents_config_path=agents_config,
        )


def test_full_manifest_copy_cannot_bypass_experiment_lock(tmp_path: Path) -> None:
    full_root = ROOT / "experiments/agentdojo_full_v1.2.2_direct"
    manifest = load_mapping(full_root / "experiment_manifest.yaml")
    copied_manifest = tmp_path / "copied_manifest.json"
    copied_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="manifest_path mismatch"):
        validate_namespaced_manifest_inputs(
            manifest=manifest,
            manifest_path=copied_manifest,
            source_bundle_path=full_root
            / "source_bundles/case_packet_source_bundle.json",
            infra_config_path=ROOT / "configs/infra.yaml",
            agents_config_path=ROOT / "configs/agents.yaml",
            phase="full",
            experiment_type="appendix",
        )


def test_run_full_defaults_to_all_manifest_cases_and_isolates_default_jobs_dir() -> (
    None
):
    args = run_full.build_parser().parse_args(["--domain", "agentdojo"])
    assert args.case_count is None
    assert run_full._default_jobs_dir(None) == "results/jobs/full"
    assert run_full._default_jobs_dir("agentdojo_full_v1.2.2_direct") == (
        "results/jobs/full/namespaces/agentdojo_full_v1.2.2_direct"
    )


def test_run_full_infers_and_enforces_manifest_experiment_type() -> None:
    manifest = {
        "domains": [
            {"domain": "agentdojo", "experiment_type": "appendix"},
        ]
    }
    assert (
        run_full._resolve_experiment_type(
            manifest,
            domains=["agentdojo"],
            requested=None,
        )
        == "appendix"
    )
    with pytest.raises(ValueError, match="does not match manifest"):
        run_full._resolve_experiment_type(
            manifest,
            domains=["agentdojo"],
            requested="main",
        )


def test_score_batch_infers_full_coverage_tasks_per_slot_and_keeps_explicit_gate() -> (
    None
):
    assert (
        score_batch.resolve_tasks_per_key(
            task_count=949 * 3,
            key_count=3,
            requested=None,
        )
        == 949
    )
    assert (
        score_batch.resolve_tasks_per_key(
            task_count=300,
            key_count=3,
            requested=100,
        )
        == 100
    )
    with pytest.raises(
        score_batch.AgentDojoBatchScoreError, match="Expected exactly 300"
    ):
        score_batch.resolve_tasks_per_key(
            task_count=2_847,
            key_count=3,
            requested=100,
        )
    with pytest.raises(
        score_batch.AgentDojoBatchScoreError, match="Cannot evenly shard"
    ):
        score_batch.resolve_tasks_per_key(
            task_count=2_847,
            key_count=4,
            requested=None,
        )


def test_score_batch_cli_omits_strict_task_count_by_default(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_agentdojo_score_batch.py"])
    assert score_batch.parse_args().tasks_per_key is None


def test_score_export_accepts_full_coverage_denominator() -> None:
    args = score_export.parse_args(["--tasks-per-key", "949", "--slot-count", "3"])
    assert args.tasks_per_key == 949
    assert args.slot_count == 3


def test_worker_rejects_installed_agentdojo_source_hash_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_root = tmp_path / "agentdojo"
    package_root.mkdir()
    init_file = package_root / "__init__.py"
    init_file.write_text("__version__ = '0.1.35'\n", encoding="utf-8")
    source_file = package_root / "locked.py"
    source_file.write_text("LOCKED = True\n", encoding="utf-8")
    monkeypatch.setattr(
        agentdojo_worker, "distribution_version", lambda _name: "0.1.35"
    )
    monkeypatch.setitem(
        sys.modules, "agentdojo", SimpleNamespace(__file__=str(init_file))
    )
    config = SimpleNamespace(
        agentdojo_package_version="0.1.35",
        agentdojo_git_commit="a75aba7631d3ca5fb7ab938965c97ead2f9ff84b",
        agentdojo_git_tree="3c74b60f2bad4ff321d864e0c0483f256cc8f8d2",
        agentdojo_source_lock={
            "agentdojo_git_commit": "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b",
            "agentdojo_git_tree": "3c74b60f2bad4ff321d864e0c0483f256cc8f8d2",
            "files": [
                {
                    "repo_path": "src/agentdojo/locked.py",
                    "sha256": sha256_file(source_file),
                }
            ],
        },
    )
    report = agentdojo_worker._verify_agentdojo_install(config)
    assert report["source_lock_enforced"] is True
    assert report["verified_source_file_count"] == 1

    source_file.write_text("LOCKED = False\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="installed source hash mismatch"):
        agentdojo_worker._verify_agentdojo_install(config)
