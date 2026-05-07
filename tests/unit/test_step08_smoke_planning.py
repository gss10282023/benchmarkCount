from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from evidence_system.orchestrator.jobs import plan_smoke_jobs


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = "experiments/experiment_manifest.yaml"
SOURCE_BUNDLE_PATH = "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json"
CONTRACTS_DIR = "experiments/evidence_contracts/drafts"
AGENTS_CONFIG_PATH = "configs/agents.yaml"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else f"{src}{os.pathsep}{env['PYTHONPATH']}"
    return env


def test_plan_smoke_jobs_tau3_is_runnable_and_uses_smoke_config(tmp_path: Path) -> None:
    planned = plan_smoke_jobs(
        domain="tau3_retail",
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
    assert item.job["domain"] == "tau3_retail"
    assert item.execution_plan["status"] == "runnable"
    assert "openrouter/openai/gpt-5.4" in item.execution_plan["runner_command"]
    assert "--user-llm openrouter/openai/gpt-5.4" in item.execution_plan["runner_command"]
    assert "--task-ids 0" in item.execution_plan["runner_command"]


def test_plan_smoke_jobs_appworld_is_runnable_with_smoke_worker(tmp_path: Path) -> None:
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


def test_plan_smoke_jobs_agentdojo_is_runnable_with_smoke_worker(tmp_path: Path) -> None:
    planned = plan_smoke_jobs(
        domain="agentdojo",
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
    assert "evidence_system.adapters.agentdojo_worker" in item.execution_plan["runner_command"]
    assert "--model-id openai/gpt-5.4" in item.execution_plan["runner_command"]


def test_plan_smoke_jobs_webarena_is_runnable_with_smoke_worker(tmp_path: Path) -> None:
    planned = plan_smoke_jobs(
        domain="webarena_verified",
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
    assert "evidence_system.adapters.webarena_official_worker" in item.execution_plan["runner_command"]
    assert "--shopping-admin-base-url http://127.0.0.1:7780/admin" in item.execution_plan["runner_command"]
    assert "--webarena-repo-dir <WEBARENA_INSTALL_ROOT>" in item.execution_plan["runner_command"]
    assert "--max-steps 30" in item.execution_plan["runner_command"]


def test_run_domain_cli_emits_json_plan(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.run_domain",
            "--domain",
            "tau3_retail",
            "--phase",
            "smoke",
            "--experiment-type",
            "main",
            "--case-count",
            "1",
            "--agent-count",
            "1",
            "--jobs-dir",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        env=_env(),
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "planned"
    assert payload["planned_jobs"][0]["execution_plan"]["status"] == "runnable"
