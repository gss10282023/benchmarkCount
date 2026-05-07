from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

from evidence_system.adapters import appworld_official_worker
from evidence_system.orchestrator.jobs import plan_smoke_jobs


MANIFEST_PATH = "experiments/experiment_manifest.yaml"
SOURCE_BUNDLE_PATH = "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json"
CONTRACTS_DIR = "experiments/evidence_contracts/drafts"
AGENTS_CONFIG_PATH = "configs/agents.yaml"


def test_plan_smoke_jobs_appworld_uses_official_worker(tmp_path: Path) -> None:
    planned = plan_smoke_jobs(
        domain="appworld",
        phase="smoke",
        experiment_type="main",
        case_count=1,
        agent_ids=["Agent A"],
        seed=7,
        manifest_path=MANIFEST_PATH,
        source_bundle_path=SOURCE_BUNDLE_PATH,
        contracts_dir=CONTRACTS_DIR,
        infra_config_path="configs/infra.yaml",
        agents_config_path=AGENTS_CONFIG_PATH,
        jobs_dir=tmp_path,
    )
    assert len(planned) == 1
    item = planned[0]
    assert item.execution_plan["status"] == "runnable"
    assert "evidence_system.adapters.appworld_official_worker" in item.execution_plan["runner_command"]
    assert "--model openai/gpt-5.4" in item.execution_plan["runner_command"]
    assert "--max-steps 50" in item.execution_plan["runner_command"]
    assert "APPWORLD_ROOT=<APPWORLD_OFFICIAL_ROOT>" in item.execution_plan["runner_command"]
    assert "simplified_react_code_agent" in "\n".join(item.execution_plan["notes"])


def test_appworld_official_worker_run_official_job_writes_expected_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    install_fake_official_appworld(monkeypatch, tmp_path)
    appworld_root = tmp_path / "appworld-root"
    (appworld_root / "data").mkdir(parents=True, exist_ok=True)
    (appworld_root / "data" / "version.txt").write_text("0.1.0", encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("APPWORLD_ROOT", str(appworld_root))

    config = appworld_official_worker.AppWorldOfficialConfig(
        job={"job_id": "smoke-appworld-024c982_1-agent_a", "task_id": "024c982_1", "seed": 7},
        source_entry={
            "domain": "AppWorld",
            "task_id": "024c982_1",
            "source_ref": "appworld://test_normal/024c982_1",
        },
        output_dir=tmp_path / "worker-output",
        experiment_name="smoke_job_001",
        provider="openrouter",
        model="openai/gpt-5.4-mini",
        temperature=0.0,
        max_tokens=1024,
        openrouter_api_key_env="OPENROUTER_API_KEY",
        max_steps=50,
        lm_retry_after_seconds=15,
        lm_max_retries=100,
    )

    summary = appworld_official_worker.run_official_job(config)

    assert summary["status"] == "completed"
    assert summary["success"] is True
    assert summary["data_version"] == "0.1.0"
    assert summary["official_agent_name"] == "simplified_react_code_agent"
    assert (config.output_dir / "native_evaluator_input.json").exists()
    assert (config.output_dir / "native_evaluator_output.json").exists()
    assert (config.output_dir / "official_runner_config.json").exists()
    assert (config.output_dir / "artifact_manifest.json").exists()
    assert (config.output_dir / "appworld_task_output" / "logs" / "api_calls.jsonl").exists()
    assert (config.output_dir / "appworld_task_output" / "logs" / "environment_io.md").exists()
    assert (config.output_dir / "appworld_task_output" / "logs" / "lm_calls.jsonl").exists()
    assert (config.output_dir / "appworld_task_output" / "evaluation" / "report.md").exists()

    runner_config = json.loads((config.output_dir / "official_runner_config.json").read_text(encoding="utf-8"))
    assert runner_config["agent"]["type"] == "simplified_react_code_agent"
    assert runner_config["agent"]["prompt_file_path"].endswith("/react_code_agent/instructions.txt")
    assert runner_config["dataset"] == "test_normal"

    native_input = json.loads((config.output_dir / "native_evaluator_input.json").read_text(encoding="utf-8"))
    assert native_input["official_agent_name"] == "simplified_react_code_agent"
    assert native_input["source_ref"] == "appworld://test_normal/024c982_1"

    import appworld.common.constants as constants
    import appworld.environment as environment_module
    import appworld.evaluator as evaluator_module
    import appworld.task as task_module

    assert constants.DB_VERSION == "0.1.0"
    assert environment_module.DB_VERSION == "0.1.0"
    assert evaluator_module.DB_VERSION == "0.1.0"
    assert "0.1.0" in constants.COMPATIBLE_DATA_VERSIONS
    assert "0.1.0" in constants.COMPATIBLE_DB_VERSIONS
    assert "0.1.0" in task_module.COMPATIBLE_DB_VERSIONS


def install_fake_official_appworld(monkeypatch, tmp_path: Path) -> None:
    package = ModuleType("appworld")
    common_module = ModuleType("appworld.common")
    constants_module = ModuleType("appworld.common.constants")
    constants_module.COMPATIBLE_DATA_VERSIONS = ["0.2.0"]
    constants_module.COMPATIBLE_DB_VERSIONS = ["0.2.0"]
    constants_module.DB_VERSION = "0.2.0"
    path_store_module = ModuleType("appworld.common.path_store")
    path_store_module.path_store = SimpleNamespace(experiment_prompts=str(tmp_path / "prompts"))
    environment_module = ModuleType("appworld.environment")
    environment_module.DB_VERSION = "0.2.0"
    evaluator_module = ModuleType("appworld.evaluator")
    evaluator_module.DB_VERSION = "0.2.0"
    task_module = ModuleType("appworld.task")
    task_module.COMPATIBLE_DB_VERSIONS = ["0.2.0"]

    class FakeTracker:
        def to_dict(self, stats_only: bool = False):
            assert stats_only is False
            return {
                "success": True,
                "difficulty": 1,
                "passes": [{"requirement": "assert answers match.", "label": "no_op_fail"}],
                "failures": [],
            }

    def fake_run_experiment(
        *,
        experiment_name: str,
        runner_config: dict[str, object],
        task_id: str | None = None,
        num_processes: int = 1,
        process_index: int = 0,
    ) -> None:
        assert experiment_name == "smoke_job_001"
        assert task_id == "024c982_1"
        assert num_processes == 1
        assert process_index == 0
        assert runner_config["dataset"] == "test_normal"
        agent_config = runner_config["agent"]
        assert isinstance(agent_config, dict)
        assert agent_config["type"] == "simplified_react_code_agent"
        assert str(agent_config["prompt_file_path"]).endswith("/react_code_agent/instructions.txt")

        root = Path(os.environ["APPWORLD_ROOT"]) / "experiments" / "outputs" / experiment_name / "tasks" / str(task_id)
        (root / "logs").mkdir(parents=True, exist_ok=True)
        (root / "dbs").mkdir(parents=True, exist_ok=True)
        (root / "misc").mkdir(parents=True, exist_ok=True)
        (root / "logs" / "api_calls.jsonl").write_text('{"app":"venmo","api":"create_payment_request"}\n', encoding="utf-8")
        (root / "logs" / "environment_io.md").write_text(
            "### Environment Interaction 1\n"
            "----------------------------------------\n"
            "```python\napis.supervisor.complete_task()\n```\n\n"
            "```\nExecution successful.\n```\n",
            encoding="utf-8",
        )
        (root / "logs" / "lm_calls.jsonl").write_text('{"request":{},"response":{"id":"resp-1"}}\n', encoding="utf-8")
        (root / "dbs" / "snapshot.txt").write_text("db snapshot", encoding="utf-8")
        (root / "misc" / "usage.json").write_text('{"total_cost": 0}', encoding="utf-8")
        (root / "misc" / "finished").write_text("", encoding="utf-8")

    def fake_evaluate_task(
        *,
        task_id: str,
        experiment_name: str,
        suppress_errors: bool,
        save_report: bool,
    ) -> FakeTracker:
        assert task_id == "024c982_1"
        assert experiment_name == "smoke_job_001"
        assert suppress_errors is True
        assert save_report is True
        root = Path(os.environ["APPWORLD_ROOT"]) / "experiments" / "outputs" / experiment_name / "tasks" / task_id / "evaluation"
        root.mkdir(parents=True, exist_ok=True)
        (root / "report.md").write_text("evaluation report", encoding="utf-8")
        return FakeTracker()

    evaluator_module.evaluate_task = fake_evaluate_task
    package.common = common_module
    package.environment = environment_module
    package.evaluator = evaluator_module
    package.task = task_module
    common_module.constants = constants_module
    common_module.path_store = path_store_module

    run_module = ModuleType("appworld_agents.code.simplified.run")
    run_module.run_experiment = fake_run_experiment
    simplified_module = ModuleType("appworld_agents.code.simplified")
    simplified_module.run = run_module
    code_module = ModuleType("appworld_agents.code")
    code_module.simplified = simplified_module
    agents_module = ModuleType("appworld_agents")
    agents_module.code = code_module

    monkeypatch.setitem(sys.modules, "appworld", package)
    monkeypatch.setitem(sys.modules, "appworld.common", common_module)
    monkeypatch.setitem(sys.modules, "appworld.common.constants", constants_module)
    monkeypatch.setitem(sys.modules, "appworld.common.path_store", path_store_module)
    monkeypatch.setitem(sys.modules, "appworld.environment", environment_module)
    monkeypatch.setitem(sys.modules, "appworld.evaluator", evaluator_module)
    monkeypatch.setitem(sys.modules, "appworld.task", task_module)
    monkeypatch.setitem(sys.modules, "appworld_agents", agents_module)
    monkeypatch.setitem(sys.modules, "appworld_agents.code", code_module)
    monkeypatch.setitem(sys.modules, "appworld_agents.code.simplified", simplified_module)
    monkeypatch.setitem(sys.modules, "appworld_agents.code.simplified.run", run_module)
