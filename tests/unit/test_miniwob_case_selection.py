from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evidence_system.cli import build_miniwob_case_selection as selection_cli
from evidence_system.contracts import miniwob_case_selection as selection_module
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.miniwob_case_selection import (
    CandidateCase,
    _default_manifest_id,
    _manifest_agent_entries,
    _manifest_payload,
    _miniwob_candidate_pool,
    _miniwob_config,
    _selected_payload,
    _select_cases,
    _validate_result_namespace,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.schemas import validate_object


def _candidate_pool(task_ids: list[str]) -> dict[str, object]:
    return {
        "items": [
            {
                "case_unit_id": task_id,
                "task_id": task_id,
                "selection_order_key": f"key-{index:03d}",
            }
            for index, task_id in enumerate(task_ids)
        ]
    }


def _locked_agent_rationale(*, style: str = "browsergym_single_action") -> dict[str, object]:
    return {
        "non_redundant_measurement_probe": True,
        "spans_source_openness": "locked_source_lineage",
        "spans_scale": "locked_scale",
        "spans_tool_use_style": style,
        "leaderboard_interpretation": False,
    }


def test_select_cases_supports_offset_window() -> None:
    candidate_pool = _candidate_pool(
        [
            "miniwob.task-3",
            "miniwob.task-1",
            "miniwob.task-4",
            "miniwob.task-2",
        ]
    )
    # The helper sorts by selection_order_key, not input order.
    first_window = _select_cases(candidate_pool, selected_count=2, selection_offset=0)
    second_window = _select_cases(candidate_pool, selected_count=2, selection_offset=2)

    assert [item.task_id for item in first_window] == ["miniwob.task-3", "miniwob.task-1"]
    assert [item.task_id for item in second_window] == ["miniwob.task-4", "miniwob.task-2"]
    assert {item.task_id for item in first_window}.isdisjoint({item.task_id for item in second_window})


def test_select_cases_rejects_invalid_windows() -> None:
    candidate_pool = _candidate_pool(["miniwob.task-1", "miniwob.task-2"])

    with pytest.raises(ContractLifecycleError, match="selected_count must be positive"):
        _select_cases(candidate_pool, selected_count=0, selection_offset=0)
    with pytest.raises(ContractLifecycleError, match="selection_offset must be non-negative"):
        _select_cases(candidate_pool, selected_count=1, selection_offset=-1)
    with pytest.raises(ContractLifecycleError, match="candidate pool too small"):
        _select_cases(candidate_pool, selected_count=2, selection_offset=1)


def test_default_manifest_id_uses_window_when_nondefault() -> None:
    assert _default_manifest_id(selected_count=50, selection_offset=0) == "miniwob-diagnostic-50-manifest"
    assert _default_manifest_id(selected_count=50, selection_offset=50) == "miniwob-diagnostic-window-051-100-manifest"


def test_miniwob_candidate_discovery_uses_requested_infra_config(tmp_path: Path) -> None:
    infra_path = tmp_path / "locked-infra.json"
    infra_path.write_text(
        json.dumps(
            {
                "machines": [
                    {
                        "enabled": True,
                        "benchmarks": {
                            "MiniWoB++": {
                                "python_bin": "/locked/venv/bin/python",
                                "install_dir": "/locked/browsergym",
                                "assets_path": "/locked/miniwob/html",
                            }
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    class FakeRemote:
        miniwob_machine = object()

        def __init__(self) -> None:
            self.commands: list[str] = []

        def run(self, _machine: object, command: str) -> str:
            self.commands.append(command)
            return json.dumps(
                {
                    "install_dir": "/locked/browsergym",
                    "items": [
                        {
                            "case_unit_id": "miniwob.custom-task",
                            "task_id": "miniwob.custom-task",
                        }
                    ],
                }
            )

    remote = FakeRemote()
    payload = _miniwob_candidate_pool(remote, infra_config_path=infra_path)  # type: ignore[arg-type]

    assert _miniwob_config(infra_path) == {
        "python_bin": "/locked/venv/bin/python",
        "install_dir": "/locked/browsergym",
        "html_root": "/locked/miniwob/html",
    }
    assert len(remote.commands) == 1
    assert "/locked/venv/bin/python" in remote.commands[0]
    assert 'Path("/locked/miniwob/html")' in remote.commands[0]
    assert payload["catalog_count"] == 1
    assert payload["candidate_count"] == 1


def test_local_candidate_discovery_uses_locked_paths_without_ssh(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    python_bin = tmp_path / "venv/bin/python"
    install_dir = tmp_path / "browsergym-install"
    html_root = tmp_path / "miniwob/html"
    python_bin.parent.mkdir(parents=True)
    python_bin.symlink_to("/bin/sh")
    install_dir.mkdir()
    html_root.mkdir(parents=True)
    infra_path = tmp_path / "locked-local-infra.json"
    infra_path.write_text(
        json.dumps(
            {
                "machines": [
                    {
                        "enabled": True,
                        "benchmarks": {
                            "MiniWoB++": {
                                "python_bin": str(python_bin),
                                "install_dir": str(install_dir),
                                "assets_path": str(html_root),
                            }
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    calls: list[dict[str, object]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append({"argv": argv, **kwargs})
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "install_dir": str(install_dir),
                    "items": [
                        {
                            "case_unit_id": "miniwob.local-task",
                            "task_id": "miniwob.local-task",
                        }
                    ],
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(selection_module.subprocess, "run", fake_run)

    payload = _miniwob_candidate_pool(
        None,
        infra_config_path=infra_path,
        source_mode="local",
    )

    assert len(calls) == 1
    assert calls[0]["argv"][:2] == ["/bin/bash", "-lc"]
    assert str(python_bin) in calls[0]["argv"][2]
    assert str(html_root) in calls[0]["argv"][2]
    assert payload["source_mode"] == "local"
    assert payload["catalog_count"] == 1


def test_local_selected_payload_hashes_files_and_fails_closed(tmp_path: Path) -> None:
    install_dir = tmp_path / "locked-install"
    venv_dir = tmp_path / "locked-venv"
    source_files = [
        venv_dir / "lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
        venv_dir / "lib/python3.12/site-packages/browsergym/miniwob/all.py",
        venv_dir / "lib/python3.12/site-packages/browsergym/miniwob/base.py",
        install_dir / "miniwob/html/miniwob/local-task.html",
        install_dir / "miniwob/html/core/core.js",
    ]
    for index, path in enumerate(source_files):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"locked-source-{index}\n", encoding="utf-8")
    item = {
        "case_unit_id": "miniwob.local-task",
        "task_id": "miniwob.local-task",
        "source_file": str(source_files[1]),
        "base_source_file": str(source_files[2]),
        "html_file": str(source_files[3]),
        "html_asset_files": [str(source_files[4])],
    }
    selected = [
        CandidateCase(
            domain="miniwob",
            case_unit_id="miniwob.local-task",
            task_id="miniwob.local-task",
            payload=item,
        )
    ]
    candidate_pool = {
        "install_dir": str(install_dir),
        "registry_file": str(source_files[0]),
        "_materialization_roots": {
            "install_root": str(install_dir),
            "venv_root": str(venv_dir),
        },
    }

    payload = _selected_payload(
        candidate_pool=candidate_pool,
        candidate_pool_path="catalog.json",
        selected=selected,
        remote=None,
        source_mode="local",
    )

    official_files = payload["items"][0]["official_files"]
    assert payload["source_mode"] == "local"
    assert len(official_files) == len(source_files)
    assert [descriptor["source_path"] for descriptor in official_files] == [
        "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/__init__.py",
        "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py",
        "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/base.py",
        "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/local-task.html",
        "<MINIWOB_INSTALL_ROOT>/miniwob/html/core/core.js",
    ]
    assert [descriptor["materialization_path"] for descriptor in official_files] == [
        str(path) for path in source_files
    ]
    assert [descriptor["sha256"] for descriptor in official_files] == [
        sha256_file(path) for path in source_files
    ]
    assert payload["items"][0]["source_file"].startswith("<MINIWOB_VENV_ROOT>/")
    assert payload["items"][0]["html_file"].startswith("<MINIWOB_INSTALL_ROOT>/")

    source_files[-1].unlink()
    with pytest.raises(ContractLifecycleError, match="official source file is missing"):
        _selected_payload(
            candidate_pool=candidate_pool,
            candidate_pool_path="catalog.json",
            selected=selected,
            remote=None,
            source_mode="local",
        )


def test_manifest_binds_requested_configs_namespace_and_agent_roles(tmp_path: Path) -> None:
    infra_path = tmp_path / "locked-infra.json"
    agents_path = tmp_path / "locked-agents.json"
    candidate_pool_path = tmp_path / "catalog.json"
    infra_path.write_text('{"locked": "infra-v2"}\n', encoding="utf-8")
    roles = {
        agent_id: {
            "provider": "test",
            "model": f"{agent_id.lower().replace(' ', '-')}-v2",
            "agent_probe_rationale": _locked_agent_rationale(
                style=f"browsergym_single_action_{agent_id[-1].lower()}"
            ),
        }
        for agent_id in ("Agent A", "Agent B", "Agent C")
    }
    agents_config = {"experimental_agents": roles}
    agents_path.write_text(json.dumps(agents_config), encoding="utf-8")
    candidate_pool_path.write_text('{"catalog": 122}\n', encoding="utf-8")
    main_manifest = {
        "agents": [
            {
                "agent_id": agent_id,
                "config_hash": "0" * 64,
                "agent_probe_rationale": {
                    "non_redundant_measurement_probe": True,
                    "spans_source_openness": "test",
                    "spans_scale": "test",
                    "spans_tool_use_style": "test",
                    "leaderboard_interpretation": False,
                },
            }
            for agent_id in ("Agent A", "Agent B", "Agent C")
        ]
    }
    selected = [
        CandidateCase(
            domain="miniwob",
            case_unit_id="miniwob.custom-task",
            task_id="miniwob.custom-task",
            payload={},
        )
    ]
    excluded_smoke = [
        "miniwob.click-button",
        "miniwob.click-test",
        "miniwob.enter-text",
    ]

    payload = _manifest_payload(
        main_manifest=main_manifest,
        candidate_pool_path=candidate_pool_path,
        candidate_pool={
            "candidate_count": 122,
            "eligible_case_unit_set_hash": "1" * 64,
            "smoke_exclusion_hash": sha256_object(excluded_smoke),
            "case_selection_order_hash": "3" * 64,
            "excluded_smoke_case_units": excluded_smoke,
        },
        selected=selected,
        source_bundle_hash="0" * 64,
        created_at="2026-07-16T00:00:00+00:00",
        manifest_id="miniwob-remaining22",
        infra_config_path=infra_path,
        agents_config_path=agents_path,
        agents_config=agents_config,
        result_namespace="miniwob_remaining22_browsergym_v1",
    )

    assert payload["infra_config_hash"] == sha256_file(infra_path)
    assert payload["agents_config_hash"] == sha256_file(agents_path)
    assert payload["agents"][0]["config_hash"] == sha256_object(roles["Agent A"])
    assert payload["agents"][0]["agent_probe_rationale"] == roles["Agent A"]["agent_probe_rationale"]
    assert payload["result_namespace"] == "miniwob_remaining22_browsergym_v1"
    assert payload["domains"][0]["record_slot_count"] == 3
    assert validate_object("experiment_manifest", payload, raise_on_error=False).ok


def test_manifest_agent_entries_fail_closed_on_unlocked_rationale() -> None:
    main_manifest = {
        "agents": [
            {
                "agent_id": "Agent A",
                "config_hash": "0" * 64,
                "agent_probe_rationale": _locked_agent_rationale(style="stale_main_value"),
            }
        ]
    }

    with pytest.raises(ContractLifecycleError, match="missing agent_probe_rationale mapping"):
        _manifest_agent_entries(
            main_manifest=main_manifest,
            agents_config={"experimental_agents": {"Agent A": {"model": "locked"}}},
        )

    placeholder_rationale = _locked_agent_rationale(
        style="tool_use_style_pending_formal_lock"
    )
    with pytest.raises(ContractLifecycleError, match="spans_tool_use_style contains a placeholder"):
        _manifest_agent_entries(
            main_manifest=main_manifest,
            agents_config={
                "experimental_agents": {
                    "Agent A": {
                        "model": "locked",
                        "agent_probe_rationale": placeholder_rationale,
                    }
                }
            },
        )

    invalid_boolean_rationale = _locked_agent_rationale()
    invalid_boolean_rationale["leaderboard_interpretation"] = True
    with pytest.raises(ContractLifecycleError, match="leaderboard_interpretation must be false"):
        _manifest_agent_entries(
            main_manifest=main_manifest,
            agents_config={
                "experimental_agents": {
                    "Agent A": {
                        "model": "locked",
                        "agent_probe_rationale": invalid_boolean_rationale,
                    }
                }
            },
        )


def test_local_build_never_constructs_remote_sources_and_forwards_packet_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    agent_ids = ("Agent A", "Agent B", "Agent C")
    main_manifest_path = tmp_path / "main-manifest.json"
    agents_path = tmp_path / "agents.json"
    infra_path = tmp_path / "infra.json"
    source_infra_path = tmp_path / "source-infra.json"
    main_manifest_path.write_text(
        json.dumps(
            {
                "agents": [
                    {
                        "agent_id": agent_id,
                        "config_hash": "0" * 64,
                        "agent_probe_rationale": {
                            "non_redundant_measurement_probe": True,
                            "spans_source_openness": "test",
                            "spans_scale": "test",
                            "spans_tool_use_style": "test",
                            "leaderboard_interpretation": False,
                        },
                    }
                    for agent_id in agent_ids
                ]
            }
        ),
        encoding="utf-8",
    )
    agents_path.write_text(
        json.dumps(
            {
                "experimental_agents": {
                    agent_id: {
                        "provider": "test",
                        "model": agent_id,
                        "agent_probe_rationale": _locked_agent_rationale(),
                    }
                    for agent_id in agent_ids
                }
            }
        ),
        encoding="utf-8",
    )
    infra_path.write_text('{"locked": "local"}\n', encoding="utf-8")
    source_infra_path.write_text('{"locked": "source-materialization"}\n', encoding="utf-8")
    excluded_smoke = [
        "miniwob.click-button",
        "miniwob.click-test",
        "miniwob.enter-text",
    ]
    candidate_pool = {
        "candidate_count": 1,
        "items": [
            {
                "case_unit_id": "miniwob.local-task",
                "task_id": "miniwob.local-task",
                "selection_order_key": "0" * 64,
            }
        ],
        "eligible_case_unit_set_hash": "1" * 64,
        "case_selection_order_hash": "2" * 64,
        "excluded_smoke_case_units": excluded_smoke,
        "smoke_exclusion_hash": sha256_object(excluded_smoke),
    }
    observed: dict[str, object] = {}

    def forbid_remote(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("local source mode must not construct RemoteCaseSources")

    def fake_candidate_pool(
        remote: object,
        *,
        infra_config_path: str | Path,
        source_mode: str,
    ) -> dict[str, object]:
        assert remote is None
        assert infra_config_path == source_infra_path
        assert source_mode == "local"
        return candidate_pool

    def fake_selected_payload(**kwargs: object) -> dict[str, object]:
        assert kwargs["remote"] is None
        assert kwargs["source_mode"] == "local"
        return {"schema_version": "test", "items": candidate_pool["items"]}

    def fake_build_packets(**kwargs: object) -> list[SimpleNamespace]:
        observed.update(kwargs)
        return [SimpleNamespace(to_dict=lambda: {"case_unit_id": "miniwob.local-task"})]

    def fake_build_bundle(**kwargs: object) -> Path:
        output_path = Path(kwargs["output_path"])
        output_path.write_text('{"source_count": 1}\n', encoding="utf-8")
        return output_path

    monkeypatch.setattr(selection_module, "RemoteCaseSources", forbid_remote)
    monkeypatch.setattr(selection_module, "_miniwob_candidate_pool", fake_candidate_pool)
    monkeypatch.setattr(selection_module, "_selected_payload", fake_selected_payload)
    monkeypatch.setattr(selection_module, "build_case_packets", fake_build_packets)
    monkeypatch.setattr(selection_module, "build_case_packet_source_bundle", fake_build_bundle)

    official_root = tmp_path / "official"
    manifest_path = tmp_path / "appendix/miniwob-remaining22.json"
    selected_sources_path = official_root / "miniwob_selected_task_sources.json"
    source_bundle_path = tmp_path / "bundles/miniwob-remaining22.json"
    packets_root = tmp_path / "packets"
    result = selection_module.build_miniwob_case_selection(
        infra_config_path=infra_path,
        source_infra_config_path=source_infra_path,
        agents_config_path=agents_path,
        source_mode="local",
        main_manifest_path=main_manifest_path,
        official_splits_root=official_root,
        manifest_path=manifest_path,
        selected_sources_path=selected_sources_path,
        source_bundle_path=source_bundle_path,
        case_packets_root=packets_root,
        selected_count=1,
        result_namespace="miniwob_remaining22_local_v1",
    )

    assert observed["source_mode"] == "local"
    assert observed["infra_config_path"] == source_infra_path
    assert observed["output_root"] == packets_root
    assert result["source_mode"] == "local"
    assert result["built_count"] == 1
    assert result["manifest_path"] == str(manifest_path)
    assert result["selected_sources_path"] == str(selected_sources_path)
    assert result["source_bundle_path"] == str(source_bundle_path)
    assert result["source_infra_config_path"] == str(source_infra_path)
    assert result["source_infra_config_hash"] == sha256_file(source_infra_path)
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["infra_config_hash"] == sha256_file(infra_path)


def test_local_build_publishes_only_anonymized_paths_and_remains_rerunnable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    materialization_root = tmp_path / "private-miniwob-materialization"
    install_root = materialization_root / "miniwob-plusplus"
    venv_root = materialization_root / "venv"
    registry_file = venv_root / "lib/python3.12/site-packages/browsergym/miniwob/__init__.py"
    task_source = venv_root / "lib/python3.12/site-packages/browsergym/miniwob/all.py"
    base_source = venv_root / "lib/python3.12/site-packages/browsergym/miniwob/base.py"
    html_file = install_root / "miniwob/html/miniwob/local-task.html"
    html_asset = install_root / "miniwob/html/core/core.js"
    actual_sources = [registry_file, task_source, base_source, html_file, html_asset]
    for index, path in enumerate(actual_sources):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"public-safe-source-{index}\n", encoding="utf-8")

    excluded_smoke = [
        "miniwob.click-button",
        "miniwob.click-test",
        "miniwob.enter-text",
    ]
    item = {
        "case_unit_id": "miniwob.local-task",
        "task_id": "miniwob.local-task",
        "class_name": "LocalTask",
        "module": "browsergym.miniwob.all",
        "source_file": str(task_source),
        "base_class_name": "AbstractMiniwobTask",
        "base_module": "browsergym.miniwob.base",
        "base_source_file": str(base_source),
        "subdomain": "local-task",
        "nondeterministic": False,
        "html_file": str(html_file),
        "html_asset_files": [str(html_asset)],
        "html_title": "Local Task",
        "static_query_text": "Test local public paths.",
        "selection_order_key": "0" * 64,
        "selection_rank": 0,
    }
    candidate_pool = {
        "schema_version": "official_case_source.miniwob_candidates.v1",
        "benchmark": "MiniWoB++",
        "install_dir": str(install_root),
        "package_root": str(registry_file.parent),
        "html_root": str(html_file.parent),
        "registry_file": str(registry_file),
        "catalog_count": 1,
        "candidate_count": 1,
        "items": [item],
        "selection_hash_function": "sha256",
        "selection_salt_hash": "4" * 64,
        "excluded_smoke_case_units": excluded_smoke,
        "smoke_exclusion_hash": sha256_object(excluded_smoke),
        "eligible_case_unit_set_hash": "1" * 64,
        "case_selection_order_hash": "2" * 64,
        "eligibility_policy": "test",
        "source_mode": "local",
        "_materialization_roots": {
            "install_root": str(install_root),
            "venv_root": str(venv_root),
        },
    }

    agent_ids = ("Agent A", "Agent B", "Agent C")
    main_manifest_path = tmp_path / "inputs/main-manifest.json"
    agents_path = tmp_path / "inputs/agents.json"
    infra_path = tmp_path / "inputs/infra.json"
    main_manifest_path.parent.mkdir(parents=True)
    main_manifest_path.write_text(
        json.dumps(
            {
                "agents": [
                    {
                        "agent_id": agent_id,
                        "config_hash": "0" * 64,
                        "agent_probe_rationale": {
                            "non_redundant_measurement_probe": True,
                            "spans_source_openness": "test",
                            "spans_scale": "test",
                            "spans_tool_use_style": "test",
                            "leaderboard_interpretation": False,
                        },
                    }
                    for agent_id in agent_ids
                ]
            }
        ),
        encoding="utf-8",
    )
    agents_path.write_text(
        json.dumps(
            {
                "experimental_agents": {
                    agent_id: {
                        "provider": "test",
                        "model": agent_id,
                        "agent_probe_rationale": _locked_agent_rationale(),
                    }
                    for agent_id in agent_ids
                }
            }
        ),
        encoding="utf-8",
    )
    infra_path.write_text('{"locked": "local"}\n', encoding="utf-8")

    def forbid_remote(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("local source mode must not construct RemoteCaseSources")

    def fake_candidate_pool(
        remote: object,
        *,
        infra_config_path: str | Path,
        source_mode: str,
    ) -> dict[str, object]:
        assert remote is None
        assert infra_config_path == infra_path
        assert source_mode == "local"
        return candidate_pool

    monkeypatch.setattr(selection_module, "RemoteCaseSources", forbid_remote)
    monkeypatch.setattr(selection_module, "_miniwob_candidate_pool", fake_candidate_pool)

    official_root = tmp_path / "outputs/official"
    manifest_path = tmp_path / "outputs/miniwob-manifest.json"
    selected_sources_path = official_root / "miniwob_selected_task_sources.json"
    source_bundle_path = tmp_path / "outputs/miniwob-source-bundle.json"
    packets_root = tmp_path / "outputs/case-packets"
    kwargs = {
        "infra_config_path": infra_path,
        "agents_config_path": agents_path,
        "source_mode": "local",
        "main_manifest_path": main_manifest_path,
        "official_splits_root": official_root,
        "manifest_path": manifest_path,
        "selected_sources_path": selected_sources_path,
        "source_bundle_path": source_bundle_path,
        "case_packets_root": packets_root,
        "selected_count": 1,
        "result_namespace": "miniwob_local_public_v1",
    }

    first = selection_module.build_miniwob_case_selection(**kwargs)
    case_dir = packets_root / "miniwob/miniwob.local-task"
    first_selected = selected_sources_path.read_bytes()
    first_derived = (case_dir / "raw_case/derived/selected_task_source.json").read_bytes()
    first_raw_manifest = (case_dir / "raw_case_manifest.json").read_bytes()
    second = selection_module.build_miniwob_case_selection(**kwargs)

    assert first["built_count"] == second["built_count"] == 1
    assert selected_sources_path.read_bytes() == first_selected
    assert (case_dir / "raw_case/derived/selected_task_source.json").read_bytes() == first_derived
    assert (case_dir / "raw_case_manifest.json").read_bytes() == first_raw_manifest

    public_files = [
        official_root / "miniwob_official_task_catalog_1.json",
        selected_sources_path,
        case_dir / "raw_case/derived/selected_task_source.json",
        case_dir / "raw_case_manifest.json",
        case_dir / "case_packet.md",
    ]
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_files)
    assert str(materialization_root) not in public_text
    assert "materialization_path" not in public_text
    assert "<MINIWOB_INSTALL_ROOT>/miniwob/html/miniwob/local-task.html" in public_text
    assert "<MINIWOB_VENV_ROOT>/lib/python3.12/site-packages/browsergym/miniwob/all.py" in public_text

    selected_payload = json.loads(selected_sources_path.read_text(encoding="utf-8"))
    for descriptor in selected_payload["items"][0]["official_files"]:
        copied = case_dir / "raw_case" / descriptor["archive_path"]
        assert copied.is_file()
        assert sha256_file(copied) == descriptor["sha256"]


@pytest.mark.parametrize("value", ["../full", "full/miniwob", "", "white space"])
def test_result_namespace_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ContractLifecycleError, match="result_namespace must match"):
        _validate_result_namespace(value)


def test_cli_forwards_locked_configs_and_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_build(**kwargs: object) -> dict[str, str]:
        captured.update(kwargs)
        return {"status": "ok"}

    monkeypatch.setattr(selection_cli, "build_miniwob_case_selection", fake_build)

    assert selection_cli.main(
        [
            "--infra-config",
            "configs/locked-infra.yaml",
            "--source-infra-config",
            "configs/locked-source-infra.yaml",
            "--agents-config",
            "configs/locked-agents.yaml",
            "--source-mode",
            "local",
            "--result-namespace",
            "miniwob_remaining22_browsergym_v1",
        ]
    ) == 0
    assert captured["infra_config_path"] == "configs/locked-infra.yaml"
    assert captured["source_infra_config_path"] == "configs/locked-source-infra.yaml"
    assert captured["agents_config_path"] == "configs/locked-agents.yaml"
    assert captured["source_mode"] == "local"
    assert captured["result_namespace"] == "miniwob_remaining22_browsergym_v1"


def test_cli_source_mode_defaults_to_remote() -> None:
    assert selection_cli.build_parser().parse_args([]).source_mode == "remote"


def test_cli_source_infra_defaults_to_execution_infra(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_build(**kwargs: object) -> dict[str, str]:
        captured.update(kwargs)
        return {"status": "ok"}

    monkeypatch.setattr(selection_cli, "build_miniwob_case_selection", fake_build)

    assert selection_cli.main(["--infra-config", "configs/execution-infra.yaml"]) == 0
    assert captured["infra_config_path"] == "configs/execution-infra.yaml"
    assert captured["source_infra_config_path"] == "configs/execution-infra.yaml"
