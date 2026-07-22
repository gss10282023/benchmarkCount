from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence_system.contracts import miniwob_runtime_lock as runtime_lock
from evidence_system.contracts.miniwob_runtime_lock import (
    EXPECTED_SMOKE_TASKS,
    MiniWoBExecutionInfra,
    MiniWoBLocalRuntime,
    MiniWoBRuntimeLockError,
    _audit_formal_execution_infra,
    _audit_official_files,
    _audit_old_selection_windows,
    _audit_optional_baseline,
    _audit_release_component_hashes,
    _audit_source_execution_protocol,
    _catalog_matches_fingerprint,
    load_execution_infra,
    load_local_runtime,
    registry_fingerprint,
    _sanitize_local_paths,
)
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path


def _catalog() -> dict:
    return json.loads(
        resolve_repo_path("experiments/official_splits/miniwob_official_task_catalog_122.json").read_text(
            encoding="utf-8"
        )
    )


def _selected(path: str) -> dict:
    return json.loads(resolve_repo_path(path).read_text(encoding="utf-8"))


def test_registry_fingerprint_reproduces_frozen_122_hashes() -> None:
    catalog = _catalog()
    task_ids = [str(item["case_unit_id"]) for item in catalog["items"]] + list(EXPECTED_SMOKE_TASKS)

    actual = registry_fingerprint(task_ids)

    assert actual["catalog_count"] == 125
    assert actual["candidate_count"] == 122
    assert actual["eligible_case_unit_set_hash"] == catalog["eligible_case_unit_set_hash"]
    assert actual["case_selection_order_hash"] == catalog["case_selection_order_hash"]
    assert actual["smoke_exclusion_hash"] == catalog["smoke_exclusion_hash"]
    assert _catalog_matches_fingerprint(catalog, actual) is True


def test_registry_fingerprint_fails_closed_on_duplicate_task() -> None:
    with pytest.raises(MiniWoBRuntimeLockError, match="duplicate"):
        registry_fingerprint(["miniwob.a", "miniwob.a", *EXPECTED_SMOKE_TASKS])


def test_load_local_runtime_rejects_placeholder_paths(tmp_path: Path) -> None:
    infra = tmp_path / "infra.json"
    infra.write_text(
        json.dumps(
            {
                "machines": [
                    {
                        "machine_id": "locked",
                        "benchmarks": {
                            "MiniWoB++": {
                                "python_bin": "<MINIWOB_VENV>/bin/python",
                                "install_dir": "<MINIWOB_INSTALL>",
                                "assets_path": "<MINIWOB_INSTALL>/miniwob/html/miniwob",
                            }
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(MiniWoBRuntimeLockError, match="placeholders"):
        load_local_runtime(infra)


def test_old_selection_windows_are_exact_first_and_second_50() -> None:
    catalog = _catalog()
    task_ids = [str(item["case_unit_id"]) for item in catalog["items"]] + list(EXPECTED_SMOKE_TASKS)
    fingerprint = registry_fingerprint(task_ids)
    first = _selected("experiments/official_splits/miniwob_selected_task_sources.json")
    second = _selected("experiments/official_splits/miniwob_second50/miniwob_selected_task_sources.json")

    audit = _audit_old_selection_windows([first, second], fingerprint)

    assert audit["ok"] is True
    assert audit["union_count"] == 100
    assert audit["overlap"] == []


def test_official_file_audit_requires_every_hash_to_match(tmp_path: Path) -> None:
    install = tmp_path / "install"
    package = tmp_path / "site-packages" / "browsergym" / "miniwob"
    html = install / "miniwob" / "html" / "miniwob" / "task.html"
    core = package / "all.py"
    html.parent.mkdir(parents=True)
    package.mkdir(parents=True)
    html.write_text("<title>locked</title>", encoding="utf-8")
    core.write_text("ALL_MINIWOB_TASKS = []\n", encoding="utf-8")
    payload = {
        "items": [
            {
                "case_unit_id": "miniwob.task",
                "official_files": [
                    {
                        "archive_path": "official/python/browsergym/miniwob/all.py",
                        "sha256": sha256_file(core),
                    },
                    {
                        "archive_path": "official/install/miniwob/html/miniwob/task.html",
                        "sha256": sha256_file(html),
                    },
                ],
            }
        ]
    }

    assert _audit_official_files([payload], install_dir=install, package_root=package)["ok"] is True

    payload["items"][0]["official_files"][1]["sha256"] = "0" * 64
    failed = _audit_official_files([payload], install_dir=install, package_root=package)
    assert failed["ok"] is False
    assert failed["mismatches"][0]["archive_path"].endswith("task.html")


def test_missing_release_baselines_are_unproven_not_passed() -> None:
    current = {
        "src/evidence_system/adapters/miniwob.py": {
            "path": "src/evidence_system/adapters/miniwob.py",
            "sha256": "a" * 64,
        }
    }

    component_audit = _audit_release_component_hashes(current, {})
    chromium_audit = _audit_optional_baseline(
        actual={"sha256": "b" * 64, "version": "1"},
        expected={"sha256": None, "version": None},
    )

    assert component_audit["status"] == "unproven"
    assert component_audit["missing_baselines"] == ["src/evidence_system/adapters/miniwob.py"]
    assert chromium_audit["status"] == "unproven"


def test_formal_execution_infra_requires_non_dry_run_namespaced_roots(tmp_path: Path) -> None:
    namespace = "miniwob_remaining22_test"
    root = f"results/namespaces/{namespace}"
    benchmark = {
        "runner_command": "/remote/venv/bin/python",
        "python_bin": "/remote/venv/bin/python",
        "install_dir": "/remote/miniwob",
        "assets_path": "/remote/miniwob/miniwob/html/miniwob",
        "base_url": "http://127.0.0.1:8787/miniwob/",
        "http_server_dir": "/remote/miniwob/miniwob/html",
        "playwright_browsers_path": "/remote/tmp/miniwob-browsergym-0.14.3/browsers",
        "adapter_module": "evidence_system.adapters.miniwob",
        "worker_module": "evidence_system.adapters.miniwob_worker",
        "driver": "openrouter_chat",
        "native_evaluator": "env.unwrapped.task.validate(page, chat_messages)",
    }
    infra_path = tmp_path / "execution.json"
    infra_path.write_text(
        json.dumps(
            {
                "dry_run": False,
                "paths": {
                    "results_root": root,
                    "dry_run_results_root": f"{root}/preflight",
                    "full_results_root": f"{root}/full",
                    "logs_dir": f"{root}/logs",
                },
                "machines": [
                    {
                        "machine_id": "remote",
                        "enabled": True,
                        "benchmarks": {"miniwob": benchmark},
                        "results_dir": f"{root}/full/miniwob",
                        "logs_dir": f"{root}/logs",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    execution = load_execution_infra(infra_path)
    audit = _audit_formal_execution_infra(execution)

    assert execution.result_namespace == namespace
    assert audit["ok"] is True

    execution.infra_config["dry_run"] = True
    assert _audit_formal_execution_infra(execution)["ok"] is False


def test_source_runtime_and_execution_protocol_include_runtime_pins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "7fd85d71a4b60325c6585396ec4f48377d049838"
    common = {
        "base_url": "http://127.0.0.1:8787/miniwob/",
        "http_server_port": 8787,
        "full_max_steps": 30,
        "headless": True,
        "record_video": True,
        "timeout_seconds": 120,
        "retry": 2,
        "playwright_browsers_path": "tmp/miniwob-browsergym-test/browsers",
        "base_seed": 7,
        "adapter_module": "evidence_system.adapters.miniwob",
        "worker_module": "evidence_system.adapters.miniwob_worker",
        "driver": "openrouter_chat",
        "action_set": {"class": "HighLevelActionSet", "multiaction": False, "strict": False},
        "native_evaluator": "env.unwrapped.task.validate(page, chat_messages)",
    }
    source_machine = {
        "benchmark_assets": {
            "browsergym_distribution": "browsergym-miniwob==0.14.3",
            "miniwob_git_commit": commit,
            "playwright_distribution": "playwright==1.44.0",
            "chromium_revision": "1117",
            "chromium_version": "125.0.6422.26",
        }
    }
    execution_benchmark = {
        **common,
        "browsergym_version": "0.14.3",
        "miniwob_git_commit": commit,
        "playwright_version": "1.44.0",
        "chromium_revision": "1117",
        "chromium_version": "125.0.6422.26",
    }
    source = MiniWoBLocalRuntime(
        python_bin=tmp_path / "python",
        install_dir=tmp_path / "install",
        html_root=tmp_path / "install" / "miniwob" / "html" / "miniwob",
        benchmark_config=common,
        machine_id="source",
        machine_config=source_machine,
        infra_config={},
    )
    execution = MiniWoBExecutionInfra(
        benchmark_config=execution_benchmark,
        machine_id="remote",
        machine_config={},
        infra_config={"dry_run": False},
        result_namespace="remaining22",
    )
    probe = {
        "distributions": {"browsergym-miniwob": "0.14.3", "playwright": "1.44.0"},
        "chromium": {
            "browser_version": "125.0.6422.26",
            "browsers_json_chromium": [{"name": "chromium", "revision": "1117"}],
        },
        "playwright_browsers_path": str(
            resolve_repo_path("tmp/miniwob-browsergym-test/browsers").resolve()
        ),
        "action_set": {"class": "HighLevelActionSet", "multiaction": False, "strict": False},
    }
    monkeypatch.setattr(runtime_lock, "_git_commit", lambda _path: commit)

    assert _audit_source_execution_protocol(
        runtime=source,
        execution=execution,
        probe=probe,
        cli_base_seed=7,
    )["ok"] is True

    execution.benchmark_config["retry"] = 3
    failed = _audit_source_execution_protocol(
        runtime=source,
        execution=execution,
        probe=probe,
        cli_base_seed=7,
    )
    assert failed["ok"] is False
    assert failed["protocol_mismatches"] == [
        {"field": "retry", "source": 2, "execution": 3}
    ]

    execution.benchmark_config["retry"] = 2
    seed_failed = _audit_source_execution_protocol(
        runtime=source,
        execution=execution,
        probe=probe,
        cli_base_seed=8,
    )
    assert seed_failed["ok"] is False
    assert [
        item for item in seed_failed["expected_protocol_mismatches"] if item["field"] == "base_seed"
    ] == [
        {"side": "source", "field": "base_seed", "expected": 8, "actual": 7},
        {"side": "execution", "field": "base_seed", "expected": 8, "actual": 7},
    ]


def test_persisted_runtime_lock_paths_are_workstation_neutral() -> None:
    repo = str(resolve_repo_path(".").resolve())
    home = str(Path.home().resolve())
    payload = {
        "repo_path": f"{repo}/tmp/miniwob/file.json",
        "home_path": f"{home}/Library/Caches/ms-playwright/chromium",
        "remote_path": "/root/revised_agent_benchmark_paper_package/tmp/miniwob",
    }

    sanitized = _sanitize_local_paths(payload)

    serialized = json.dumps(sanitized)
    assert "/Users/gss" not in serialized
    assert sanitized["repo_path"] == "<REPO_ROOT>/tmp/miniwob/file.json"
    assert sanitized["home_path"].startswith("<LOCAL_HOME>/")
    assert sanitized["remote_path"].startswith("/root/")
