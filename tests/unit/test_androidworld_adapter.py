from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import numpy as np

from evidence_system.adapters import androidworld, androidworld_worker
from evidence_system.adapters.runtime import SmokeExecutionContext
from evidence_system.core.hashing import sha256_file
from evidence_system.orchestrator.jobs import InfraBenchmarkTarget
from evidence_system.contracts.common import load_mapping


ROOT = Path(__file__).resolve().parents[2]


def test_plan_smoke_execution_androidworld_uses_local_worker_and_openrouter_smoke_model() -> None:
    target = _androidworld_target()
    job = _job_payload()

    plan = androidworld.plan_smoke_execution(
        job,
        target=target,
        agents_config_path="experiments/smoke/agents_smoke_gpt54mini.yaml",
        dotenv_path=".env",
        source_bundle_path="experiments/smoke/source_bundle_3_per_domain.json",
        source_bundle={"sources": []},
    )

    assert plan["status"] == "runnable"
    assert "evidence_system.adapters.androidworld_worker" in plan["runner_command"]
    assert "--install-dir <ANDROIDWORLD_INSTALL_ROOT>" in plan["runner_command"]
    assert "--task-name ClockStopWatchRunning" in plan["runner_command"]
    assert "--model openai/gpt-5.4-mini" in plan["runner_command"]
    assert "gRPC exposed on port 8554" in "\n".join(plan["notes"])


def test_androidworld_worker_run_smoke_job_writes_expected_artifacts(tmp_path: Path, monkeypatch) -> None:
    fake_constants = SimpleNamespace(
        EpisodeConstants=SimpleNamespace(
            GOAL="goal",
            TASK_TEMPLATE="task_template",
            INSTANCE_ID="instance_id",
            IS_SUCCESSFUL="is_successful",
            EPISODE_LENGTH="episode_length",
            RUN_TIME="run_time",
            FINISH_DTIME="finish_dtime",
            AUX_DATA="aux_data",
            EXCEPTION_INFO="exception_info",
            SCREEN_CONFIG="screen_config",
            SEED="seed",
            EPISODE_DATA="episode_data",
        )
    )
    checkpoint_dir = tmp_path / "official-checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (checkpoint_dir / "ClockStopWatchRunning_0.pkl.gz").write_bytes(b"checkpoint")

    episode = {
        "goal": "Start the stopwatch and leave it running.",
        "task_template": "ClockStopWatchRunning",
        "instance_id": 0,
        "is_successful": 1,
        "episode_length": 1,
        "run_time": 2.5,
        "finish_dtime": "2026-05-05T00:00:00+00:00",
        "aux_data": {"post_run_note": "done"},
        "exception_info": None,
        "screen_config": {"width": 1080, "height": 2400},
        "seed": 7,
        "episode_data": {
            "before_screenshot": [np.zeros((4, 4, 3), dtype=np.uint8)],
            "after_screenshot": [np.ones((4, 4, 3), dtype=np.uint8) * 255],
            "before_element_list": [[{"text": "Clock"}]],
            "after_element_list": [[{"text": "Stopwatch"}]],
            "action_prompt": ["Choose the stopwatch tab."],
            "action_output": ['Reason: start\nAction: {"action_type":"click","index":0}'],
            "action_raw_response": [{"id": "resp-action-1"}],
            "summary_prompt": ["Summarize the step."],
            "summary": ["Opened Stopwatch and tapped Start."],
            "summary_raw_response": [{"id": "resp-summary-1"}],
            "step_number": [0],
        },
    }

    monkeypatch.setattr(androidworld_worker, "_capture_device_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(androidworld_worker, "_capture_system_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(androidworld_worker, "_assert_emulator_ready", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        androidworld_worker,
        "_run_androidworld_task",
        lambda config: {
            "constants": fake_constants,
            "suite_family": "android_world",
            "task_name": "ClockStopWatchRunning",
            "goal": "Start the stopwatch and leave it running.",
            "params": {"target": "stopwatch"},
            "episodes": [episode],
            "episode": episode,
            "agent_name": "t3a_openrouter",
            "checkpoint_dir": checkpoint_dir,
        },
    )

    config = androidworld_worker.AndroidWorldSmokeConfig(
        job={"job_id": "smoke-androidworld-clock-agent_a", "task_id": "ClockStopWatchRunning", "seed": 7},
        source_entry={"domain": "AndroidWorld", "task_id": "ClockStopWatchRunning"},
        output_dir=tmp_path / "worker-output",
        install_dir=tmp_path / "android_world",
        task_name="ClockStopWatchRunning",
        model="openai/gpt-5.4-mini",
        temperature=0.0,
        max_tokens=1024,
        timeout_seconds=30,
        retry=0,
        openrouter_api_key_env="OPENROUTER_API_KEY",
        console_port=5554,
        grpc_port=8554,
    )

    summary = androidworld_worker.run_smoke_job(config)

    assert summary["status"] == "completed"
    assert summary["success"] is True
    assert (config.output_dir / "native_evaluator_input.json").exists()
    assert (config.output_dir / "native_evaluator_output.json").exists()
    assert (config.output_dir / "artifact_manifest.json").exists()
    assert (config.output_dir / "observations" / "step_001_before.png").exists()
    assert (config.output_dir / "trajectories" / "steps.json").exists()
    assert (config.output_dir / "actions" / "actions.json").exists()
    assert (config.output_dir / "messages" / "messages.json").exists()
    assert (config.output_dir / "evaluator_artifacts" / "checkpoint_dir" / "ClockStopWatchRunning_0.pkl.gz").exists()


def test_execute_smoke_job_androidworld_builds_raw_run_and_llm_logs(tmp_path: Path, monkeypatch) -> None:
    base_target = _androidworld_target()
    target = replace(base_target, remote_workdir=str(tmp_path), runner_workdir=str(tmp_path))
    job = _job_payload()
    execution_plan = androidworld.plan_smoke_execution(
        job,
        target=target,
        agents_config_path="experiments/smoke/agents_smoke_gpt54mini.yaml",
        dotenv_path=".env",
        source_bundle_path="experiments/smoke/source_bundle_3_per_domain.json",
        source_bundle={"sources": []},
    )
    context = SmokeExecutionContext(
        manifest_path=ROOT / "experiments" / "smoke" / "experiment_manifest_3_per_domain.yaml",
        manifest_hash=sha256_file(ROOT / "experiments" / "smoke" / "experiment_manifest_3_per_domain.yaml"),
        source_bundle_path=ROOT / "experiments" / "smoke" / "source_bundle_3_per_domain.json",
        source_bundle_hash=sha256_file(ROOT / "experiments" / "smoke" / "source_bundle_3_per_domain.json"),
        official_split_hash="0" * 64,
        agents_config_path=ROOT / "experiments" / "smoke" / "agents_smoke_gpt54mini.yaml",
        dotenv_path=ROOT / ".env",
    )

    def fake_run_local_command(command: str, *, cwd: str | Path, stdout_path: str | Path, stderr_path: str | Path):
        assert "evidence_system.adapters.androidworld_worker" in command
        Path(stdout_path).write_text("worker stdout", encoding="utf-8")
        Path(stderr_path).write_text("", encoding="utf-8")
        worker_output = Path(androidworld._worker_output_dir(target, job))
        (worker_output / "openrouter_calls").mkdir(parents=True, exist_ok=True)
        (worker_output / "device_state").mkdir(parents=True, exist_ok=True)
        (worker_output / "system_state").mkdir(parents=True, exist_ok=True)
        (worker_output / "evaluator_artifacts").mkdir(parents=True, exist_ok=True)
        (worker_output / "trajectories").mkdir(parents=True, exist_ok=True)
        (worker_output / "observations").mkdir(parents=True, exist_ok=True)
        (worker_output / "actions").mkdir(parents=True, exist_ok=True)
        (worker_output / "messages").mkdir(parents=True, exist_ok=True)
        (worker_output / "post_run_artifacts").mkdir(parents=True, exist_ok=True)
        (worker_output / "job.json").write_text(json.dumps(job), encoding="utf-8")
        (worker_output / "source_bundle_entry.json").write_text("{}", encoding="utf-8")
        (worker_output / "worker_config.json").write_text(json.dumps({"task_name": "ClockStopWatchRunning"}), encoding="utf-8")
        (worker_output / "task_context.json").write_text(json.dumps({"goal": "Start the stopwatch"}), encoding="utf-8")
        (worker_output / "artifact_manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")
        (worker_output / "native_evaluator_input.json").write_text(json.dumps({"task_name": "ClockStopWatchRunning"}), encoding="utf-8")
        (worker_output / "native_evaluator_output.json").write_text(json.dumps({"success": 1}), encoding="utf-8")
        (worker_output / "run_summary.json").write_text(
            json.dumps(
                {
                    "status": "completed",
                    "success": True,
                    "task_name": "ClockStopWatchRunning",
                    "instance_id": 0,
                }
            ),
            encoding="utf-8",
        )
        (worker_output / "trajectories" / "steps.json").write_text("[]", encoding="utf-8")
        (worker_output / "actions" / "actions.json").write_text("[]", encoding="utf-8")
        (worker_output / "messages" / "messages.json").write_text("[]", encoding="utf-8")
        (worker_output / "post_run_artifacts" / "episode_metadata.json").write_text("{}", encoding="utf-8")
        (worker_output / "openrouter_calls" / "call-0001.json").write_text(
            json.dumps(
                {
                    "call_id": "call-0001",
                    "request_timestamp": "2026-05-05T00:00:00Z",
                    "response_timestamp": "2026-05-05T00:00:01Z",
                    "request_payload": {
                        "model": "openai/gpt-5.4-mini",
                        "messages": [{"role": "user", "content": "Hello"}],
                        "temperature": 0,
                        "max_tokens": 256,
                    },
                    "response_payload": {
                        "id": "resp-001",
                        "model": "openai/gpt-5.4-mini",
                        "choices": [{"message": {"content": "Reason: ok\nAction: {\"action_type\":\"status\",\"goal_status\":\"complete\"}"}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                    },
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(args=["bash", "-lc", "fake"], returncode=0, stdout="worker stdout", stderr="")

    monkeypatch.setattr(androidworld, "_run_local_command", fake_run_local_command)

    result = androidworld.execute_smoke_job(
        job,
        target=target,
        execution_plan=execution_plan,
        context=context,
    )

    assert result["status"] == "completed"
    raw_run = json.loads(Path(result["raw_run_path"]).read_text(encoding="utf-8"))
    assert raw_run["status"] == "COMPLETED"
    assert raw_run["native_label"] == "success"
    assert raw_run["llm_calls_log_path"].endswith("calls.jsonl")
    manifest = json.loads(Path(result["artifact_manifest_path"]).read_text(encoding="utf-8"))
    artifact_types = {artifact["artifact_type"] for artifact in manifest["artifacts"]}
    assert "native_evaluator_output" in artifact_types
    assert "llm_call_log" in artifact_types


def test_prepare_task_environment_runs_targeted_preflight(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    fake_adb_utils = SimpleNamespace(
        set_root_if_needed=lambda controller: calls.append(("root", controller)),
    )
    fake_setup_device = SimpleNamespace(
        get_app_mapping=lambda app_name: f"setup:{app_name}",
        setup_app=lambda app_setup, env: calls.append(("setup", app_setup)),
    )
    modules = SimpleNamespace(
        adb_utils=fake_adb_utils,
        setup_device_setup=fake_setup_device,
        app_snapshot=SimpleNamespace(),
    )
    env = SimpleNamespace(controller="controller")
    task_instance = SimpleNamespace(app_names=("broccoli app", "clipper", "markor", "clock"))

    monkeypatch.setattr(
        androidworld_worker,
        "_verify_required_device_paths",
        lambda config_obj, modules_obj, env_obj, app_name: calls.append(("verify_paths", app_name)),
    )
    monkeypatch.setattr(
        androidworld_worker,
        "_verify_clipper_access",
        lambda modules_obj, env_obj: calls.append(("verify_clipper", "clipper")),
    )
    monkeypatch.setattr(
        androidworld_worker,
        "_ensure_device_directory",
        lambda modules_obj, env_obj, path: calls.append(("ensure_dir", path)),
    )

    androidworld_worker._prepare_task_environment(
        config=None,  # type: ignore[arg-type]
        modules=modules,  # type: ignore[arg-type]
        env=env,
        task_instance=task_instance,
    )

    assert calls == [
        ("root", "controller"),
        ("ensure_dir", "/storage/emulated/0/Documents/Markor"),
        ("verify_paths", "broccoli app"),
        ("verify_clipper", "clipper"),
    ]


def test_extract_response_content_accepts_non_typed_text_blocks() -> None:
    response_payload = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"text": "Reason: ok\n"},
                        {"content": "Action: {\"action_type\":\"status\",\"goal_status\":\"complete\"}"},
                    ]
                }
            }
        ]
    }

    assert (
        androidworld_worker.extract_response_content(response_payload)
        == 'Reason: ok\nAction: {"action_type":"status","goal_status":"complete"}'
    )


def test_extract_response_content_accepts_reasoning_fallback() -> None:
    response_payload = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "reasoning": "Reason: ok\nAction: {\"action_type\":\"status\",\"goal_status\":\"complete\"}",
                }
            }
        ]
    }

    assert (
        androidworld_worker.extract_response_content(response_payload)
        == 'Reason: ok\nAction: {"action_type":"status","goal_status":"complete"}'
    )


def test_device_path_exists_prefers_host_adb_probe(monkeypatch) -> None:
    config = androidworld_worker.AndroidWorldSmokeConfig(
        job={},
        source_entry={},
        output_dir=ROOT / "tmp" / "androidworld-test-output",
        install_dir=ROOT,
        task_name="Task",
        model="openai/gpt-5.4-mini",
        temperature=0.0,
        max_tokens=128,
        timeout_seconds=30,
        retry=0,
        openrouter_api_key_env="OPENROUTER_API_KEY",
        console_port=5554,
        grpc_port=8554,
        adb_path="/fake/adb",
    )
    modules = SimpleNamespace(adb_utils=SimpleNamespace(issue_generic_request=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("controller probe should not be used when host adb succeeds"))))
    env = SimpleNamespace(controller="controller")

    monkeypatch.setattr(androidworld_worker, "_resolve_adb_path", lambda *_args, **_kwargs: "/fake/adb")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=0, stdout="/data/data/app.db\n", stderr=""),
    )

    assert androidworld_worker._device_path_exists(config, modules, env, "/data/data/app.db") is True


def _job_payload() -> dict[str, object]:
    return {
        "schema_version": "job/v1",
        "job_id": "smoke-androidworld-clock-agent_a",
        "domain": "androidworld",
        "domain_display_name": "AndroidWorld",
        "benchmark_name": "AndroidWorld",
        "case_unit_id": "androidworld:ClockStopWatchRunning",
        "task_id": "ClockStopWatchRunning",
        "record_slot_id": "slot-androidworld-clock-agent_a",
        "run_id": "run-androidworld-clock-agent_a",
        "attempt_id": "attempt-androidworld-clock-agent_a",
        "final_attempt": True,
        "seed": 7,
        "agent_id": "Agent A",
        "phase": "smoke",
        "experiment_type": "appendix",
        "priority": "P2",
        "adapter_module": "evidence_system.adapters.androidworld",
        "agent_config_hash": "a" * 64,
        "benchmark_config_hash": "b" * 64,
        "manifest_hash": "c" * 64,
        "evidence_contract_id": "contract-androidworld-001",
        "evidence_contract_version": "1.0.0",
        "evidence_contract_hash": "d" * 64,
        "contract_id": "contract-androidworld-001",
        "contract_version": "1.0.0",
        "contract_hash": "d" * 64,
        "taxonomy_version": "taxonomy/v1",
        "artifact_contract": {"required_artifacts": []},
        "deterministic_selection": {"selection_rule": "test"},
    }


def _androidworld_target() -> InfraBenchmarkTarget:
    infra = load_mapping("configs/infra.yaml")
    machine = next(
        candidate
        for candidate in infra["machines"]
        if candidate.get("role") == "local_androidworld"
    )
    benchmark_config = dict(machine["benchmarks"]["AndroidWorld"])
    return InfraBenchmarkTarget(
        machine_id=str(machine["machine_id"]),
        machine_role=str(machine["role"]),
        ssh_host="",
        ssh_user="",
        ssh_port=22,
        ssh_key_path="",
        remote_workdir=str(machine["remote_workdir"]),
        runner_workdir=str(machine["runner_workdir"]),
        benchmark_name="AndroidWorld",
        benchmark_config=benchmark_config,
        benchmark_config_hash="infra-hash-test",
        runner_command=str(benchmark_config["runner_command"]),
        machine_concurrency=int(machine.get("concurrency") or 1),
    )
