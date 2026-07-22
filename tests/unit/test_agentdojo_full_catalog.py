from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path

import pytest

from evidence_system.cli.build_agentdojo_full_catalog import build_parser
from evidence_system.contracts.agentdojo_full_catalog import (
    AGENTDOJO_BENCHMARK_VERSION,
    AGENTDOJO_EXPECTED_CASE_COUNT,
    AGENTDOJO_EXPECTED_SUITE_COUNTS,
    AGENTDOJO_GIT_COMMIT,
    AGENTDOJO_GIT_TAG,
    AGENTDOJO_PACKAGE_VERSION,
    DEFAULT_PAIRED_CANDIDATES_PATH,
    DEFAULT_SELECTED_SOURCES_PATH,
    _legacy_item_hash,
    _source_file_descriptor,
    _validate_catalog_identity,
    build_agentdojo_full_catalog,
)
from evidence_system.contracts.case_packets import OfficialCaseSources
from evidence_system.contracts.common import ContractLifecycleError


ROOT = Path(__file__).resolve().parents[2]


def test_full_catalog_constants_lock_official_release_and_case_count() -> None:
    assert AGENTDOJO_PACKAGE_VERSION == "0.1.35"
    assert AGENTDOJO_GIT_TAG == "v0.1.35"
    assert AGENTDOJO_GIT_COMMIT == "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b"
    assert AGENTDOJO_BENCHMARK_VERSION == "v1.2.2"
    assert AGENTDOJO_EXPECTED_CASE_COUNT == 949
    assert (
        sum(block["case_units"] for block in AGENTDOJO_EXPECTED_SUITE_COUNTS.values())
        == 949
    )


def test_cli_defaults_use_disjoint_full_coverage_namespace() -> None:
    args = build_parser().parse_args([])
    assert args.paired_candidates == DEFAULT_PAIRED_CANDIDATES_PATH
    assert args.output == DEFAULT_SELECTED_SOURCES_PATH
    assert args.output.startswith("experiments/agentdojo_full_v1.2.2_direct/")


def test_source_file_descriptor_is_repo_relative_and_content_locked(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src" / "agentdojo" / "task.py"
    source.parent.mkdir(parents=True)
    source.write_text("class Task: ...\n", encoding="utf-8")

    descriptor = _source_file_descriptor(source, tmp_path)

    assert descriptor == {
        "repo_path": "src/agentdojo/task.py",
        "sha256": f"sha256:{hashlib.sha256(source.read_bytes()).hexdigest()}",
    }


def test_catalog_identity_rejects_same_count_with_different_ids() -> None:
    ids = [f"case-{index}" for index in range(AGENTDOJO_EXPECTED_CASE_COUNT)]
    candidates = list(ids)
    candidates[-1] = "different-case"

    with pytest.raises(ContractLifecycleError, match="do not equal"):
        _validate_catalog_identity(ids, candidates, AGENTDOJO_EXPECTED_SUITE_COUNTS)


def test_catalog_identity_rejects_order_drift() -> None:
    ids = [f"case-{index}" for index in range(AGENTDOJO_EXPECTED_CASE_COUNT)]
    candidates = list(ids)
    candidates[0], candidates[1] = candidates[1], candidates[0]

    with pytest.raises(ContractLifecycleError, match="order"):
        _validate_catalog_identity(ids, candidates, AGENTDOJO_EXPECTED_SUITE_COUNTS)


def test_item_hash_matches_existing_selected_source_convention() -> None:
    payload = json.loads(
        (
            ROOT / "experiments/official_splits/agentdojo_selected_task_sources.json"
        ).read_text()
    )
    item = dict(payload["items"][0])
    expected = item.pop("source_sha256").removeprefix("sha256:")
    assert _legacy_item_hash(item) == expected


def test_official_checkout_builds_exact_949_item_catalog(tmp_path: Path) -> None:
    try:
        if importlib.metadata.version("agentdojo") != AGENTDOJO_PACKAGE_VERSION:
            pytest.skip("pinned AgentDojo package is not installed")
        module = importlib.import_module("agentdojo")
    except (importlib.metadata.PackageNotFoundError, ImportError):
        pytest.skip("pinned AgentDojo package is not installed")

    module_path = Path(module.__file__).resolve()
    repo_root = next(
        (parent for parent in module_path.parents if (parent / ".git").exists()), None
    )
    if repo_root is None:
        pytest.skip("AgentDojo package is not installed from an official git checkout")
    try:
        module_path.relative_to((repo_root / "src" / "agentdojo").resolve())
    except ValueError:
        pytest.skip("AgentDojo is installed as a wheel, not from the detected checkout")

    output = tmp_path / "official_splits" / "agentdojo_selected_task_sources.json"
    result = build_agentdojo_full_catalog(
        paired_candidates_path=ROOT / DEFAULT_PAIRED_CANDIDATES_PATH,
        output_path=output,
        agentdojo_repo_path=repo_root,
    )

    assert result["selected_count"] == 949
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert (
        len(payload["items"])
        == len({item["case_unit_id"] for item in payload["items"]})
        == 949
    )
    assert payload["provenance"]["agentdojo_git_commit"] == AGENTDOJO_GIT_COMMIT
    assert payload["provenance"]["attack_strategy"] == "direct"
    assert payload["provenance"]["defense"] is None
    first = payload["items"][0]
    assert first["agentdojo_package_version"] == "0.1.35"
    assert first["user_task"]["source_file"]["repo_path"].startswith("src/agentdojo/")
    assert first["injection_task"]["source_file"]["sha256"].startswith("sha256:")
    assert first["source_files"]["tool_implementation_files"]
    assert first["source_files"]["environment_data_files"]

    sources = OfficialCaseSources(output.parent)
    loaded = sources.agentdojo_item(first["case_unit_id"])
    assert loaded["case_unit_id"] == first["case_unit_id"]
