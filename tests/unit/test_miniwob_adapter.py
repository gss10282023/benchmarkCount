from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from evidence_system.adapters import miniwob, miniwob_worker, runtime
from evidence_system.adapters.runtime import SmokeExecutionContext
from evidence_system.core.hashing import sha256_file
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator.jobs import resolve_infra_target


ROOT = Path(__file__).resolve().parents[2]


def test_miniwob_remote_result_path_uses_result_namespace() -> None:
    target = SimpleNamespace(remote_workdir="/srv/evidence")
    job = {
        "phase": "full",
        "domain": "miniwob",
        "job_id": "full-miniwob-use-slider-agent_a",
    }

    assert miniwob._remote_output_dir(target, job) == (
        "/srv/evidence/results/full/miniwob/full-miniwob-use-slider-agent_a"
    )
    assert miniwob._remote_output_dir(
        target,
        {**job, "result_namespace": "miniwob_remaining22_browsergym_v1"},
    ) == (
        "/srv/evidence/results/namespaces/miniwob_remaining22_browsergym_v1/full/miniwob/"
        "full-miniwob-use-slider-agent_a"
    )


def test_formal_support_tree_sync_is_delete_exact_and_bounded(monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(runtime, "ensure_remote_directory", lambda *_args: None)
    monkeypatch.setattr(
        runtime,
        "_run_subprocess",
        lambda argv, **kwargs: calls.append((list(argv), dict(kwargs)))
        or subprocess.CompletedProcess(argv, 0, "", ""),
    )
    runtime._SYNCED_SUPPORT_KEYS.clear()
    runtime.sync_repo_support_files(
        _miniwob_target(),
        paths=("src/evidence_system",),
        include_dotenv=False,
        delete_directories=True,
        timeout_seconds=600,
    )

    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[:3] == ["rsync", "-az", "--delete"]
    assert "__pycache__/" in argv
    assert "*.pyc" in argv
    assert kwargs["timeout_seconds"] == 600
    runtime._SYNCED_SUPPORT_KEYS.clear()


def test_plan_smoke_execution_miniwob_uses_remote_worker_and_openrouter_smoke_model() -> None:
    target = _miniwob_target()
    target = replace(
        target,
        benchmark_config={
            **target.benchmark_config,
            "playwright_browsers_path": "/srv/browsergym/browsers",
        },
    )
    job = _job_payload()

    plan = miniwob.plan_smoke_execution(
        job,
        target=target,
        agents_config_path="experiments/smoke/miniwob_agents_gpt54mini.yaml",
        dotenv_path=".env",
        source_bundle_path="experiments/smoke/miniwob_source_bundle.json",
        source_bundle={"sources": [_source_entry()]},
    )

    assert plan["status"] == "runnable"
    assert "evidence_system.adapters.miniwob_worker" in plan["runner_command"]
    assert "PLAYWRIGHT_BROWSERS_PATH=/srv/browsergym/browsers" in plan["runner_command"]
    assert "--task-id miniwob.click-test" in plan["runner_command"]
    assert "--driver openrouter_chat" in plan["runner_command"]
    assert "--base-url http://127.0.0.1:8787/miniwob/" in plan["runner_command"]
    assert "--model openai/gpt-5.4-mini" in plan["runner_command"]
    notes = "\n".join(plan["notes"])
    assert "env.unwrapped.task.validate(page, chat_messages)" in notes
    assert "MiniWoB++ base_url=http://127.0.0.1:8787/miniwob/" in notes


def test_miniwob_worker_run_smoke_job_writes_expected_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(miniwob_worker, "_build_action_set", lambda: FakeActionSet())
    monkeypatch.setattr(
        miniwob_worker,
        "_make_miniwob_env",
        lambda *, config, task_kwargs, action_set: FakeEnv(
            task_kwargs=task_kwargs,
            recordings_root=config.output_dir / "browser_artifacts" / "recordings",
        ),
    )
    monkeypatch.setattr(
        miniwob_worker,
        "request_openrouter_completion",
        lambda **_: {
            "choices": [{"message": {"content": "click('a1')"}}],
            "id": "resp-001",
            "model": "openai/gpt-5.4-mini",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
    )

    config = miniwob_worker.MiniWoBSmokeConfig(
        job=_job_payload(),
        source_entry=_source_entry(),
        output_dir=tmp_path / "worker-output",
        task_id="miniwob.click-test",
        model="openai/gpt-5.4-mini",
        temperature=0.0,
        max_tokens=512,
        timeout_seconds=30,
        retry=0,
        openrouter_api_key_env="OPENROUTER_API_KEY",
        max_steps=3,
        driver=miniwob_worker.DRIVER_OPENROUTER_CHAT,
        base_url="http://127.0.0.1:8787/miniwob/",
    )

    summary = miniwob_worker.run_smoke_job(config)

    assert summary["status"] == "completed"
    assert summary["success"] is True
    assert (config.output_dir / "native_evaluator_input.json").exists()
    assert (config.output_dir / "native_evaluator_output.json").exists()
    assert (config.output_dir / "artifact_manifest.json").exists()
    assert (config.output_dir / "openrouter_calls" / "call-0001.json").exists()
    assert (config.output_dir / "trajectory" / "steps.json").exists()
    assert (config.output_dir / "trajectory" / "observations" / "step_000_reset.json").exists()
    assert (config.output_dir / "browser_artifacts" / "screenshots" / "step_000_reset.png").exists()
    assert (config.output_dir / "browser_artifacts" / "page_html" / "step_001.html").exists()
    assert (config.output_dir / "task_artifacts" / "policy_workflow.json").exists()
    native_output = json.loads((config.output_dir / "native_evaluator_output.json").read_text(encoding="utf-8"))
    assert native_output["success"] is True
    assert native_output["step_count"] == 1
    task_context = json.loads((config.output_dir / "task_context.json").read_text(encoding="utf-8"))
    assert task_context["base_url"] == "http://127.0.0.1:8787/miniwob/"


def test_execute_smoke_job_miniwob_builds_raw_run_and_llm_logs(tmp_path: Path, monkeypatch) -> None:
    controller_root = tmp_path / "controller"

    def resolve_controller_path(path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else controller_root / candidate

    monkeypatch.setattr(runtime, "resolve_repo_path", resolve_controller_path)
    base_target = _miniwob_target()
    remote_root = tmp_path / "remote"
    target = replace(base_target, remote_workdir=str(remote_root), runner_workdir=str(remote_root))
    job = _job_payload()
    execution_plan = miniwob.plan_smoke_execution(
        job,
        target=target,
        agents_config_path="experiments/smoke/miniwob_agents_gpt54mini.yaml",
        dotenv_path=".env",
        source_bundle_path="experiments/smoke/miniwob_source_bundle.json",
        source_bundle={"sources": [_source_entry()]},
    )
    context = SmokeExecutionContext(
        manifest_path=ROOT / "experiments" / "smoke" / "miniwob_manifest.yaml",
        manifest_hash=sha256_file(ROOT / "experiments" / "smoke" / "miniwob_manifest.yaml"),
        source_bundle_path=ROOT / "experiments" / "smoke" / "miniwob_source_bundle.json",
        source_bundle_hash=sha256_file(ROOT / "experiments" / "smoke" / "miniwob_source_bundle.json"),
        official_split_hash="0" * 64,
        agents_config_path=ROOT / "experiments" / "smoke" / "miniwob_agents_gpt54mini.yaml",
        dotenv_path=ROOT / ".env",
    )

    monkeypatch.setattr(miniwob, "_ensure_remote_http_server", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(miniwob, "sync_repo_support_files", lambda *_args, **_kwargs: None)

    def fake_run_remote_command(_target, command: str, *, stdout_path: str | Path, stderr_path: str | Path):
        Path(stdout_path).write_text("worker stdout", encoding="utf-8")
        Path(stderr_path).write_text("", encoding="utf-8")
        worker_output = Path(miniwob._remote_output_dir(target, job))
        if "miniwob_worker" in command:
            (worker_output / "browser_artifacts" / "screenshots").mkdir(parents=True, exist_ok=True)
            (worker_output / "browser_artifacts" / "page_html").mkdir(parents=True, exist_ok=True)
            (worker_output / "task_artifacts").mkdir(parents=True, exist_ok=True)
            (worker_output / "trajectory" / "observations").mkdir(parents=True, exist_ok=True)
            (worker_output / "openrouter_calls").mkdir(parents=True, exist_ok=True)
            (worker_output / "job.json").write_text(json.dumps(job), encoding="utf-8")
            (worker_output / "source_bundle_entry.json").write_text(json.dumps(_source_entry()), encoding="utf-8")
            (worker_output / "worker_config.json").write_text(json.dumps({"task_id": "miniwob.click-test"}), encoding="utf-8")
            (worker_output / "task_context.json").write_text(json.dumps({"goal": "Click the button."}), encoding="utf-8")
            (worker_output / "artifact_manifest.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
            (worker_output / "native_evaluator_input.json").write_text(json.dumps({"validator_method": "env.unwrapped.task.validate(page, chat_messages)"}), encoding="utf-8")
            (worker_output / "native_evaluator_output.json").write_text(json.dumps({"success": True, "reward": 1.0}), encoding="utf-8")
            (worker_output / "run_summary.json").write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "success": True,
                        "env_id": "browsergym/miniwob.click-test",
                        "step_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            (worker_output / "trajectory" / "steps.json").write_text("[]", encoding="utf-8")
            (worker_output / "trajectory" / "observations" / "step_000_reset.json").write_text("{}", encoding="utf-8")
            (worker_output / "browser_artifacts" / "page_html" / "step_001.html").write_text("<html></html>", encoding="utf-8")
            (worker_output / "browser_artifacts" / "screenshots" / "step_001.png").write_bytes(b"png")
            (worker_output / "task_artifacts" / "task_state_final.json").write_text("{}", encoding="utf-8")
            (worker_output / "openrouter_calls" / "call-0001.json").write_text(
                json.dumps(
                    {
                        "call_id": "call-0001",
                        "request_timestamp": "2026-05-05T00:00:00Z",
                        "response_timestamp": "2026-05-05T00:00:01Z",
                        "request_payload": {
                            "model": "openai/gpt-5.4-mini",
                            "messages": [{"role": "user", "content": "Prompt"}],
                            "temperature": 0,
                            "max_tokens": 256,
                        },
                        "response_payload": {
                            "id": "resp-001",
                            "model": "openai/gpt-5.4-mini",
                            "choices": [{"message": {"content": "click('a1')"}}],
                            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                        },
                        "action_text": "click('a1')",
                        "python_code": "click('a1')",
                    }
                ),
                encoding="utf-8",
            )
        else:
            shutil.rmtree(worker_output, ignore_errors=True)
            worker_output.mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(args=["bash", "-lc", "fake"], returncode=0, stdout="worker stdout", stderr="")

    monkeypatch.setattr(miniwob, "run_remote_command", fake_run_remote_command)
    monkeypatch.setattr(
        miniwob,
        "rsync_remote_tree",
        lambda _target, remote_path, local_path: shutil.copytree(Path(remote_path), Path(local_path), dirs_exist_ok=True),
    )

    result = miniwob.execute_smoke_job(
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
    assert "browser_artifact" in artifact_types
    assert "post_state" in artifact_types
    assert "trace" in artifact_types


def test_formal_worker_timeout_or_ssh_loss_is_terminal_and_triggers_kill(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_remote(_target, command: str, **kwargs):
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(
            args=["ssh"],
            returncode=255 if len(calls) == 1 else 0,
            stdout="",
            stderr="Connection reset by peer" if len(calls) == 1 else "",
        )

    monkeypatch.setattr(miniwob, "run_remote_command", fake_remote)
    control = {
        "timeout_seconds": 1860,
        "remote_watchdog_seconds": 1800,
        "transient_retry_attempts": 1,
        "remote_pid_file": "/tmp/miniwob-bridge-deadbeef.pid",
        "remote_timeout_command": "timeout --signal=TERM --kill-after=30s",
        "remote_process_group": "setsid",
        "retry_on_timeout_or_ssh_loss": False,
        "support_files_pre_synced_and_locked": True,
        "artifact_fetch_timeout_seconds": 600,
    }
    with pytest.raises(RuntimeError, match="will not be retried"):
        miniwob._run_worker_command(
            target=_miniwob_target(),
            execution_plan={
                "runner_command": "formal-command",
                "formal_worker_control": control,
            },
            stdout_path=tmp_path / "worker.stdout",
            stderr_path=tmp_path / "worker.stderr",
            termination_stdout_path=tmp_path / "kill.stdout",
            termination_stderr_path=tmp_path / "kill.stderr",
        )

    assert len(calls) == 2
    assert calls[0]["command"] == "formal-command"
    assert calls[0]["timeout_seconds"] == 1860
    assert calls[0]["transient_retry_attempts"] == 1
    assert "kill -TERM" in str(calls[1]["command"])
    assert "kill -KILL" in str(calls[1]["command"])
    assert calls[1]["transient_retry_attempts"] == 1


class FakeActionSet:
    def describe(self, *, with_long_description: bool = True, with_examples: bool = True) -> str:
        del with_long_description, with_examples
        return "click(bid), fill(bid, value), noop()"

    def to_python_code(self, action: str) -> str:
        if "(" not in action:
            raise ValueError("invalid action")
        return action


class FakePage:
    def __init__(self) -> None:
        self.url = "http://127.0.0.1:8787/miniwob/click-test.html"
        self.clicked = False

    def title(self) -> str:
        return "Clicked" if self.clicked else "Click Test"

    def content(self) -> str:
        body = "done" if self.clicked else "ready"
        return f"<html><body>{body}</body></html>"

    def screenshot(self, *, path: str | None = None, type: str | None = None):
        del type
        payload = b"fake-png"
        if path:
            Path(path).write_bytes(payload)
        return payload


class FakeTask:
    def __init__(self, *, base_url: str) -> None:
        self.base_url = base_url
        self.episode_seed = 7
        self.goal = "Click the button."

    def validate(self, page: FakePage, chat_messages: list[dict[str, object]]):
        del chat_messages
        if page.clicked:
            return 1.0, True, "Solved", {"REWARD_GLOBAL": 1, "RAW_REWARD_GLOBAL": 1, "DONE_GLOBAL": True}
        return 0.0, False, "", {"REWARD_GLOBAL": 0, "RAW_REWARD_GLOBAL": 0, "DONE_GLOBAL": False}


class FakeChat:
    def __init__(self) -> None:
        self.messages = [
            {"role": "user", "message": "Click the button."},
        ]


class FakeEnv:
    def __init__(self, *, task_kwargs: dict[str, object], recordings_root: Path) -> None:
        self.task = FakeTask(base_url=str(task_kwargs.get("base_url") or ""))
        self.page = FakePage()
        self.chat = FakeChat()
        self.unwrapped = self
        self.recordings_root = recordings_root

    def reset(self, seed: int):
        del seed
        (self.recordings_root / "task_video").mkdir(parents=True, exist_ok=True)
        (self.recordings_root / "chat_video").mkdir(parents=True, exist_ok=True)
        obs = self._observation(last_action="", last_action_error="")
        info = {
            "task_info": {"REWARD_GLOBAL": 0, "RAW_REWARD_GLOBAL": 0, "DONE_GLOBAL": False},
            "recording_file": str(self.recordings_root / "task_video" / "task.webm"),
            "chat": {"recording_file": str(self.recordings_root / "chat_video" / "chat.webm")},
        }
        return obs, info

    def step(self, action: str):
        if "click('a1')" in action:
            self.page.clicked = True
        obs = self._observation(last_action=action, last_action_error="")
        reward, done, message, task_info = self.task.validate(self.page, self.chat.messages)
        if message:
            self.chat.messages.append({"role": "assistant", "message": message})
        return obs, reward, done, False, {"task_info": task_info}

    def close(self) -> None:
        (self.recordings_root / "task_video" / "task.webm").write_bytes(b"video")
        (self.recordings_root / "chat_video" / "chat.webm").write_bytes(b"video")

    def _observation(self, *, last_action: str, last_action_error: str) -> dict[str, object]:
        return {
            "chat_messages": tuple(self.chat.messages),
            "goal": self.task.goal,
            "goal_object": ({"type": "text", "text": self.task.goal},),
            "open_pages_urls": (self.page.url,),
            "open_pages_titles": (self.page.title(),),
            "active_page_index": [0],
            "url": self.page.url,
            "screenshot": [[0]],
            "dom_object": {"documents": []},
            "axtree_object": {
                "nodes": [
                    {
                        "browsergym_id": "a1",
                        "role": {"value": "button"},
                        "name": {"value": "Button"},
                    }
                ]
            },
            "extra_element_properties": {
                "a1": {"visibility": 1.0, "bbox": [0, 0, 10, 10], "clickable": True, "set_of_marks": True}
            },
            "focused_element_bid": "a1",
            "last_action": last_action,
            "last_action_error": last_action_error,
            "elapsed_time": [0.0],
        }


def _job_payload() -> dict[str, object]:
    return {
        "schema_version": "job/v1",
        "job_id": "smoke-miniwob-click-test-agent_a",
        "domain": "miniwob",
        "domain_display_name": "MiniWoB++",
        "benchmark_name": "MiniWoB++",
        "case_unit_id": "miniwob-click-test-smoke",
        "task_id": "miniwob.click-test",
        "record_slot_id": "slot-miniwob-click-test-agent_a",
        "run_id": "run-miniwob-click-test-agent_a",
        "attempt_id": "attempt-miniwob-click-test-agent_a",
        "final_attempt": True,
        "seed": 7,
        "agent_id": "Agent A",
        "phase": "smoke",
        "experiment_type": "diagnostic",
        "priority": "P3",
        "adapter_module": "evidence_system.adapters.miniwob",
        "agent_config_hash": "a" * 64,
        "benchmark_config_hash": "b" * 64,
        "manifest_hash": "c" * 64,
        "evidence_contract_id": "contract-miniwob-001",
        "evidence_contract_version": "1.0.0",
        "evidence_contract_hash": "d" * 64,
        "contract_id": "contract-miniwob-001",
        "contract_version": "1.0.0",
        "contract_hash": "d" * 64,
        "taxonomy_version": "taxonomy/v1",
        "artifact_contract": {"required_artifacts": []},
        "deterministic_selection": {"selection_rule": "test"},
    }


def _source_entry() -> dict[str, object]:
    return {
        "domain": "MiniWoB++",
        "task_id": "miniwob.click-test",
        "visible_inputs": {
            "native_sources": [{"source_ref": "https://github.com/Farama-Foundation/miniwob-plusplus"}],
            "evaluator_description": {
                "validator": "env.unwrapped.task.validate(page, chat_messages)",
            },
            "task_text": {
                "task_id": "miniwob.click-test",
                "instruction": "Click the button shown in the browser.",
                "runtime_goal_source": "observation.goal",
            },
            "task_kwargs": {
                "base_url": "http://127.0.0.1:8787/miniwob/",
            },
            "available_post_run_artifact_types": [
                "browser_artifact",
                "trace",
                "native_evaluator_output",
            ],
        },
    }


def _miniwob_target():
    infra = load_json_or_yaml("configs/infra.yaml")
    return resolve_infra_target("miniwob", infra)
