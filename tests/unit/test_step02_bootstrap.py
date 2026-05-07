from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from evidence_system.core.schemas import REQUIRED_SCHEMA_FILES, check_schema_files


ROOT = Path(__file__).resolve().parents[2]


REQUIRED_DIRS = [
    "src/evidence_system",
    "src/evidence_system/cli",
    "src/evidence_system/contracts",
    "src/evidence_system/llm",
    "src/evidence_system/adapters",
    "src/evidence_system/orchestrator",
    "src/evidence_system/audit",
    "src/evidence_system/stats",
    "src/evidence_system/paper",
    "src/evidence_system/release",
    "tests",
    "schemas",
    "reviews/packets",
    "reviews/gpt_pro",
]


CANONICAL_CLI_MODULES = [
    "validate_config",
    "validate_manifest",
    "check_infra",
    "deploy_all",
    "deploy_webarena",
    "deploy_osworld",
    "deploy_other_vps",
    "deploy_local_androidworld",
    "monitor",
    "collect_results",
    "resume_failed",
    "validate_contracts",
    "draft_contracts",
    "review_contracts",
    "lock_contracts",
    "record_contract_clarification",
    "update_manifest_contract_locks",
    "freeze_predictions",
    "run_preflight",
    "run_full",
    "run_domain",
    "score_records",
    "aggregate_results",
    "aggregate",
    "run_audit",
    "run_rerun",
    "make_paper_outputs",
    "make_tables",
    "make_figures",
    "make_appendix",
    "final_report",
    "validate_results",
    "make_release",
]


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else f"{src}{os.pathsep}{env['PYTHONPATH']}"
    return env


def test_required_bootstrap_files_and_dirs_exist() -> None:
    for path in ["pyproject.toml", "README.md", ".gitignore", ".env.example"]:
        assert (ROOT / path).is_file(), path
    for path in REQUIRED_DIRS:
        assert (ROOT / path).is_dir(), path


def test_pyproject_is_parseable() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "evidence-system"
    assert data["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_schema_registry_files_exist() -> None:
    status = check_schema_files()
    assert status.ok, status.missing
    for filename in REQUIRED_SCHEMA_FILES:
        path = ROOT / "schemas" / filename
        assert path.is_file(), filename


def test_validate_config_cli_reads_checked_in_configs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "evidence_system.cli.validate_config", "--json"],
        cwd=ROOT,
        env=_subprocess_env(),
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert '"schema_version": "infra/v1"' in result.stdout
    assert '"schema_version": "agents/v1"' in result.stdout


def test_canonical_cli_modules_exist_and_bootstrap_check() -> None:
    implemented_after_bootstrap = {
        "validate_contracts",
        "draft_contracts",
        "review_contracts",
        "lock_contracts",
        "record_contract_clarification",
        "update_manifest_contract_locks",
    }
    for module_name in CANONICAL_CLI_MODULES:
        importlib.import_module(f"evidence_system.cli.{module_name}")
        if module_name == "validate_config":
            continue
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                f"evidence_system.cli.{module_name}",
                "--bootstrap-check",
                "--json",
            ],
            cwd=ROOT,
            env=_subprocess_env(),
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, f"{module_name}: {result.stderr}"
        if module_name == "draft_contracts":
            expected = "implemented_step_6_openrouter_transport_available"
        elif module_name == "freeze_predictions":
            expected = "implemented_step_5_check_only"
        elif module_name == "run_full":
            expected = "implemented_step_8_controlled_raw_collection"
        else:
            expected = "implemented_step_4" if module_name in implemented_after_bootstrap else "not_implemented_in_step_2"
        assert f'"formal_logic": "{expected}"' in result.stdout


def test_formal_actions_fail_closed_by_default() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "evidence_system.cli.check_infra", "--json"],
        cwd=ROOT,
        env=_subprocess_env(),
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 2
    assert '"status": "blocked"' in result.stdout


def test_no_script_wrappers_with_unique_logic() -> None:
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return
    for path in scripts_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "evidence_system.cli" in text, path


def test_env_example_contains_no_secret_values() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        _, value = line.split("=", 1)
        assert value.strip() in {"", "configs", "results"}, line


def test_new_src_contains_no_legacy_formal_scaffold_markers() -> None:
    forbidden_fragments = ["mock" + "_result", "old runner scaffold"]
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_fragments:
            assert fragment not in text, path
