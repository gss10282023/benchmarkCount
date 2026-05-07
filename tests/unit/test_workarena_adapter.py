from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

from evidence_system.adapters import workarena, workarena_worker
from evidence_system.adapters.runtime import SmokeExecutionContext
from evidence_system.core.hashing import sha256_file
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator.jobs import resolve_infra_target


ROOT = Path(__file__).resolve().parents[2]


def test_plan_smoke_execution_workarena_uses_remote_worker_and_openrouter_smoke_model() -> None:
    target = _workarena_target()
    job = _job_payload()

    plan = workarena.plan_smoke_execution(
        job,
        target=target,
        agents_config_path="experiments/smoke/agents_smoke_gpt54mini.yaml",
        dotenv_path=".env",
        source_bundle_path="experiments/smoke/source_bundle_3_per_domain.json",
        source_bundle={"sources": [_source_entry()]},
    )

    assert plan["status"] == "runnable"
    assert "evidence_system.adapters.workarena_worker" in plan["runner_command"]
    assert "--task-id workarena.servicenow.all-menu" in plan["runner_command"]
    assert "--driver openrouter_chat" in plan["runner_command"]
    assert "--model openai/gpt-5.4-mini" in plan["runner_command"]
    notes = "\n".join(plan["notes"])
    assert "env.task.validate(page, chat_messages)" in notes
    assert '"application": "Self-Service"' in notes


def test_workarena_worker_run_smoke_job_writes_expected_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(workarena_worker, "_build_action_set", lambda: FakeActionSet())
    monkeypatch.setattr(
        workarena_worker,
        "_make_workarena_env",
        lambda *, config, task_kwargs, action_set: FakeEnv(task_kwargs=task_kwargs, recordings_root=config.output_dir / "browser_artifacts" / "recordings"),
    )
    monkeypatch.setattr(
        workarena_worker,
        "request_openrouter_completion",
        lambda **_: {
            "choices": [{"message": {"content": "click('a1')"}}],
            "id": "resp-001",
            "model": "openai/gpt-5.4-mini",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
    )

    config = workarena_worker.WorkArenaSmokeConfig(
        job=_job_payload(),
        source_entry=_source_entry(),
        output_dir=tmp_path / "worker-output",
        task_id="workarena.servicenow.all-menu",
        model="openai/gpt-5.4-mini",
        temperature=0.0,
        max_tokens=512,
        timeout_seconds=30,
        retry=0,
        openrouter_api_key_env="OPENROUTER_API_KEY",
        max_steps=3,
        driver=workarena_worker.DRIVER_OPENROUTER_CHAT,
    )

    summary = workarena_worker.run_smoke_job(config)

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
    policy_workflow = json.loads((config.output_dir / "task_artifacts" / "policy_workflow.json").read_text(encoding="utf-8"))
    assert policy_workflow["fixed_config"]["module"] == "Knowledge"


def test_execute_smoke_job_workarena_builds_raw_run_and_llm_logs(tmp_path: Path, monkeypatch) -> None:
    base_target = _workarena_target()
    target = replace(base_target, remote_workdir=str(tmp_path), runner_workdir=str(tmp_path))
    job = _job_payload()
    execution_plan = workarena.plan_smoke_execution(
        job,
        target=target,
        agents_config_path="experiments/smoke/agents_smoke_gpt54mini.yaml",
        dotenv_path=".env",
        source_bundle_path="experiments/smoke/source_bundle_3_per_domain.json",
        source_bundle={"sources": [_source_entry()]},
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

    monkeypatch.setattr(workarena, "sync_repo_support_files", lambda *_args, **_kwargs: None)

    def fake_run_remote_command(_target, command: str, *, stdout_path: str | Path, stderr_path: str | Path):
        Path(stdout_path).write_text("worker stdout", encoding="utf-8")
        Path(stderr_path).write_text("", encoding="utf-8")
        worker_output = Path(workarena._remote_output_dir(target, job))
        if "workarena_worker" in command:
            (worker_output / "browser_artifacts" / "screenshots").mkdir(parents=True, exist_ok=True)
            (worker_output / "browser_artifacts" / "page_html").mkdir(parents=True, exist_ok=True)
            (worker_output / "task_artifacts").mkdir(parents=True, exist_ok=True)
            (worker_output / "trajectory" / "observations").mkdir(parents=True, exist_ok=True)
            (worker_output / "openrouter_calls").mkdir(parents=True, exist_ok=True)
            (worker_output / "job.json").write_text(json.dumps(job), encoding="utf-8")
            (worker_output / "source_bundle_entry.json").write_text(json.dumps(_source_entry()), encoding="utf-8")
            (worker_output / "worker_config.json").write_text(json.dumps({"task_id": "workarena.servicenow.all-menu"}), encoding="utf-8")
            (worker_output / "task_context.json").write_text(json.dumps({"goal": "Navigate to Knowledge"}), encoding="utf-8")
            (worker_output / "artifact_manifest.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
            (worker_output / "native_evaluator_input.json").write_text(json.dumps({"validator_method": "env.task.validate(page, chat_messages)"}), encoding="utf-8")
            (worker_output / "native_evaluator_output.json").write_text(json.dumps({"success": True, "reward": 1.0}), encoding="utf-8")
            (worker_output / "run_summary.json").write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "success": True,
                        "env_id": "browsergym/workarena.servicenow.all-menu",
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

    monkeypatch.setattr(workarena, "run_remote_command", fake_run_remote_command)
    monkeypatch.setattr(
        workarena,
        "rsync_remote_tree",
        lambda _target, remote_path, local_path: shutil.copytree(Path(remote_path), Path(local_path), dirs_exist_ok=True),
    )

    result = workarena.execute_smoke_job(
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


class FakeActionSet:
    def describe(self, *, with_long_description: bool = True, with_examples: bool = True) -> str:
        del with_long_description, with_examples
        return "click(bid), fill(bid, value), send_msg_to_user(text)"

    def to_python_code(self, action: str) -> str:
        if "(" not in action:
            raise ValueError("invalid action")
        return action


class FakePage:
    def __init__(self, *, start_url: str, final_url: str) -> None:
        self.url = start_url
        self._final_url = final_url

    def title(self) -> str:
        return "Knowledge" if self.url == self._final_url else "Home"

    def content(self) -> str:
        body = "Knowledge" if self.url == self._final_url else "Home"
        return f"<html><body>{body}</body></html>"

    def screenshot(self, *, path: str | None = None, type: str | None = None):
        del type
        payload = b"fake-png"
        if path:
            Path(path).write_bytes(payload)
        return payload


class FakeTask:
    def __init__(self, *, fixed_config: dict[str, object] | None = None) -> None:
        self.instance = SimpleNamespace(
            snow_url="https://example.service-now.com",
            snow_credentials=("demo-user", "secret-password"),
        )
        self.module = dict(fixed_config or {})
        self.start_url = self.instance.snow_url + "/now/nav/ui/home"
        self.final_url = self.instance.snow_url + str(self.module.get("url") or "/now/nav/ui/classic/params/target/%24knowledge.do")
        self.goal = 'Navigate to the "Knowledge" module of the "Self-Service" application.'
        self.user_roles = ["admin"]

    def validate(self, page: FakePage, chat_messages: list[dict[str, object]]):
        if page.url == self.final_url:
            return 1.0, True, "Nice work, thank you!", {"message": "Correct module reached."}
        return 0.0, False, "", {"message": "Not at expected URL."}

    def get_pretty_printed_description(self) -> str:
        return '- Navigate to the "Knowledge" module of the "Self-Service" application.'


class FakeChat:
    def __init__(self) -> None:
        self.messages = [
            {"role": "assistant", "message": "Hi!"},
            {"role": "user", "message": 'Navigate to the "Knowledge" module.'},
        ]


class FakeEnv:
    def __init__(self, *, task_kwargs: dict[str, object], recordings_root: Path) -> None:
        fixed_config = dict(task_kwargs.get("fixed_config") or {})
        self.task = FakeTask(fixed_config=fixed_config)
        self.page = FakePage(start_url=self.task.start_url, final_url=self.task.final_url)
        self.chat = FakeChat()
        self.unwrapped = self
        self.recordings_root = recordings_root
        self.closed = False

    def reset(self, seed: int):
        del seed
        (self.recordings_root / "task_video").mkdir(parents=True, exist_ok=True)
        (self.recordings_root / "chat_video").mkdir(parents=True, exist_ok=True)
        obs = self._observation(last_action="", last_action_error="")
        info = {
            "task_info": {"message": "Need the Self-Service > Knowledge module."},
            "recording_file": str(self.recordings_root / "task_video" / "page.webm"),
            "chat": {"recording_file": str(self.recordings_root / "chat_video" / "chat.webm")},
        }
        return obs, info

    def step(self, action: str):
        if "click('a1')" in action:
            self.page.url = self.task.final_url
        obs = self._observation(last_action=action, last_action_error="")
        reward, done, message, task_info = self.task.validate(self.page, self.chat.messages)
        if message:
            self.chat.messages.append({"role": "user", "message": message})
        return obs, reward, done, False, {"task_info": task_info}

    def close(self) -> None:
        (self.recordings_root / "task_video" / "page.webm").write_bytes(b"video")
        (self.recordings_root / "chat_video" / "chat.webm").write_bytes(b"video")
        self.closed = True

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
                        "name": {"value": "Knowledge"},
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
        "job_id": "smoke-workarena-all-menu-agent_a",
        "domain": "workarena",
        "domain_display_name": "WorkArena",
        "benchmark_name": "WorkArena",
        "case_unit_id": "workarena.servicenow.all-menu:self-service-knowledge",
        "task_id": "workarena.servicenow.all-menu",
        "record_slot_id": "slot-workarena-all-menu-agent_a",
        "run_id": "run-workarena-all-menu-agent_a",
        "attempt_id": "attempt-workarena-all-menu-agent_a",
        "final_attempt": True,
        "seed": 7,
        "agent_id": "Agent A",
        "phase": "smoke",
        "experiment_type": "appendix",
        "priority": "P2",
        "adapter_module": "evidence_system.adapters.workarena",
        "agent_config_hash": "a" * 64,
        "benchmark_config_hash": "b" * 64,
        "manifest_hash": "c" * 64,
        "evidence_contract_id": "contract-workarena-001",
        "evidence_contract_version": "1.0.0",
        "evidence_contract_hash": "d" * 64,
        "contract_id": "contract-workarena-001",
        "contract_version": "1.0.0",
        "contract_hash": "d" * 64,
        "taxonomy_version": "taxonomy/v1",
        "artifact_contract": {"required_artifacts": []},
        "deterministic_selection": {"selection_rule": "test"},
    }


def _source_entry() -> dict[str, object]:
    return {
        "domain": "WorkArena",
        "task_id": "workarena.servicenow.all-menu",
        "visible_inputs": {
            "native_sources": [{"source_ref": "workarena://workarena.servicenow.all-menu/self-service-knowledge"}],
            "official_policy": "Use the ServiceNow All menu to navigate to the requested application/module.",
            "evaluator_description": {
                "validator": "env.task.validate(page, chat_messages)",
                "success_condition": "Current URL matches the task's final_url.",
            },
            "task_text": {
                "task_id": "workarena.servicenow.all-menu",
                "workflow_description": 'Navigate to the "Knowledge" module of the "Self-Service" application.',
                "fixed_config": {
                    "application": "Self-Service",
                    "module": "Knowledge",
                    "url": "/now/nav/ui/classic/params/target/%24knowledge.do",
                },
            },
            "available_post_run_artifact_types": [
                "browser state",
                "task trajectory",
                "validator inputs",
                "validator outputs",
            ],
        },
    }


def _workarena_target():
    infra = load_json_or_yaml("configs/infra.yaml")
    return resolve_infra_target("workarena", infra)
