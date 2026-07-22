from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from neurips_ed_track_minimal.scripts import package_miniwob_case_bundle as packager


AGENTS = ("Agent A", "Agent B", "Agent C")
SCORE_PROTOCOL = {
    "model": "gpt-5.4",
    "reasoning_effort": "high",
    "service_tier": "fast",
    "score_prompt_sha256": "prompt-current",
    "score_schema_sha256": "schema-current",
}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _cohort(tmp_path: Path, name: str, cases: list[str]) -> packager.CohortSpec:
    root = tmp_path / "cohorts" / name
    selected = root / "miniwob_selected_task_sources.json"
    catalog = root / "miniwob_official_task_catalog_122.json"
    manifest = root / f"{name}_manifest.yaml"
    source_bundle = root / f"{name}_source_bundle.json"
    packet_root = root / "case_packets" / "miniwob"
    items = [{"case_unit_id": case_id, "task_id": case_id} for case_id in cases]
    _write_json(selected, {"selected_count": len(items), "items": items})
    _write_json(catalog, {"items": items})
    _write_json(manifest, {"agents": [{"agent_id": agent} for agent in AGENTS]})
    _write_json(source_bundle, {"sources": []})
    for case_id in cases:
        case_packet = packet_root / case_id
        case_packet.mkdir(parents=True)
        (case_packet / "case_packet.md").write_text(case_id, encoding="utf-8")
    return packager.CohortSpec(
        name=name,
        selected_sources=selected,
        task_catalog=catalog,
        appendix_manifest=manifest,
        source_bundle=source_bundle,
        case_packet_root=packet_root,
        expected_case_count=len(cases),
    )


def _package_fixture(tmp_path: Path) -> tuple[packager.PackageConfig, dict[str, list[str]]]:
    cases = {
        "first50": ["miniwob.first"],
        "second50": ["miniwob.second"],
        "remaining22": ["miniwob.remaining"],
    }
    cohorts = tuple(_cohort(tmp_path, name, case_ids) for name, case_ids in cases.items())
    legacy_full = tmp_path / "results" / "full" / "miniwob"
    namespace_full = tmp_path / "results" / "namespaces" / "remaining22" / "full" / "miniwob"
    legacy_drafts = legacy_full / "drafts"
    namespace_drafts = namespace_full / "drafts"
    score_root = tmp_path / "results" / "scores" / "full" / "miniwob"

    for case_id in cases["first50"] + cases["second50"]:
        draft_dir = legacy_drafts / "legacy-batch" / case_id
        draft_dir.mkdir(parents=True)
        (draft_dir / "checklist.yaml").write_text("schema_version: test\n", encoding="utf-8")
    for case_id in cases["remaining22"]:
        draft_dir = namespace_drafts / "remaining-batch" / case_id
        draft_dir.mkdir(parents=True)
        (draft_dir / "checklist.yaml").write_text("schema_version: test\n", encoding="utf-8")

    all_cases = cases["first50"] + cases["second50"] + cases["remaining22"]
    for case_id in all_cases:
        full_root = namespace_full if case_id in cases["remaining22"] else legacy_full
        for agent in AGENTS:
            agent_slug = agent.lower().replace(" ", "_")
            run_name = f"full-miniwob-{case_id}-{agent_slug}"
            full_dir = full_root / run_name
            full_dir.mkdir(parents=True)
            (full_dir / "raw_run.json").write_text("{}", encoding="utf-8")
            score_dir = score_root / run_name / "checklist" / "scorer"
            _write_json(
                score_dir / "score_manifest.json",
                {
                    "case_unit_id": case_id,
                    "run_dir_name": run_name,
                    "agent_id": agent,
                    **SCORE_PROTOCOL,
                },
            )

    (score_root / "miniwob_scores_flat.csv").write_text("case_unit_id\n", encoding="utf-8")
    batch_dir = score_root / "_batch_runs" / "complete"
    _write_json(
        batch_dir / "summary.json",
        {"task_count": 9, "completed": 9, "updated_at": "2026-01-01T00:00:00Z"},
    )
    (batch_dir / "results.jsonl").write_text("{}\n", encoding="utf-8")

    config = packager.PackageConfig(
        cohorts=cohorts,
        expected_case_count=3,
        expected_runs_per_case=3,
        full_roots=(legacy_full, namespace_full),
        drafts_roots=(legacy_drafts, namespace_drafts),
        score_roots=(score_root,),
        profile="test-full122",
    )
    return config, cases


def _manifest_for(config: packager.PackageConfig, case_id: str, agent_slug: str) -> Path:
    run_dir = config.score_roots[0] / f"full-miniwob-{case_id}-{agent_slug}"
    manifests = list(run_dir.glob("**/score_manifest.json"))
    assert len(manifests) == 1
    return manifests[0]


def test_built_in_profiles_preserve_current100_and_add_full122() -> None:
    current, current_count = packager.built_in_cohorts("current100")
    full, full_count = packager.built_in_cohorts("full122")

    assert current_count == 100
    assert [(item.name, item.expected_case_count) for item in current] == [
        ("first50", 50),
        ("second50", 50),
    ]
    assert full_count == 122
    assert [(item.name, item.expected_case_count) for item in full] == [
        ("first50", 50),
        ("second50", 50),
        ("remaining22", 22),
    ]


def test_result_namespace_adds_namespaced_full_and_draft_roots() -> None:
    args = packager.parse_args(["--profile", "full122", "--result-namespace", "remaining22_v1"])
    config = packager.config_from_args(args)

    namespace_full = (
        packager.REPO_ROOT / "results" / "namespaces" / "remaining22_v1" / "full" / "miniwob"
    ).resolve()
    assert packager.FULL_ROOT.resolve() in config.full_roots
    assert namespace_full in config.full_roots
    assert namespace_full / "drafts" in config.drafts_roots
    assert config.strict_score_protocol is True


def test_custom_cohort_config_replaces_built_in_profile(tmp_path: Path) -> None:
    cohort = _cohort(tmp_path, "extension", ["miniwob.extension"])
    config_path = tmp_path / "cohorts.json"
    _write_json(
        config_path,
        {
            "expected_case_count": 1,
            "cohorts": [
                {
                    "name": cohort.name,
                    "selected_sources": str(cohort.selected_sources),
                    "task_catalog": str(cohort.task_catalog),
                    "appendix_manifest": str(cohort.appendix_manifest),
                    "source_bundle": str(cohort.source_bundle),
                    "case_packet_root": str(cohort.case_packet_root),
                    "expected_case_count": 1,
                }
            ],
        },
    )

    args = packager.parse_args(["--cohort-config", str(config_path)])
    config = packager.config_from_args(args)

    assert config.profile == "custom"
    assert config.expected_case_count == 1
    assert [item.name for item in config.cohorts] == ["extension"]


def test_build_bundle_spec_combines_legacy_and_namespaced_results(tmp_path: Path) -> None:
    config, _ = _package_fixture(tmp_path)

    spec = packager.build_bundle_spec("bundle", config=config)

    manifest = spec["manifest"]
    assert manifest["case_count"] == 3
    assert manifest["full_run_count"] == 9
    assert manifest["score_run_count"] == 9
    assert [item["name"] for item in manifest["cohorts"]] == [
        "first50",
        "second50",
        "remaining22",
    ]
    remaining = next(item for item in spec["case_specs"] if item["case_unit_id"] == "miniwob.remaining")
    assert all("results/namespaces/remaining22" in str(path) for path in remaining["full_run_srcs"])
    assert remaining["case_bucket"]["selected_cohort"] == "remaining22"


def test_selected_cohort_overlap_is_rejected(tmp_path: Path) -> None:
    first = _cohort(tmp_path, "first50", ["miniwob.duplicate"])
    second = _cohort(tmp_path, "second50", ["miniwob.duplicate"])
    config = packager.PackageConfig(
        cohorts=(first, second),
        expected_case_count=2,
        expected_runs_per_case=3,
        full_roots=(tmp_path / "full",),
        drafts_roots=(tmp_path / "drafts",),
        score_roots=(tmp_path / "scores",),
    )

    with pytest.raises(packager.PackageMiniwobError, match="overlap across selected cohorts"):
        packager.load_cohort_data(config)


def test_duplicate_full_run_across_legacy_and_namespace_is_rejected(tmp_path: Path) -> None:
    config, cases = _package_fixture(tmp_path)
    case_id = cases["first50"][0]
    run_name = f"full-miniwob-{case_id}-agent_a"
    duplicate = config.full_roots[1] / run_name
    duplicate.mkdir(parents=True)

    with pytest.raises(packager.PackageMiniwobError, match="Duplicate full run"):
        packager.build_bundle_spec("bundle", config=config)


def test_missing_score_slot_is_rejected(tmp_path: Path) -> None:
    config, cases = _package_fixture(tmp_path)
    case_id = cases["remaining22"][0]
    score_run = config.score_roots[0] / f"full-miniwob-{case_id}-agent_c"
    for path in sorted(score_run.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        else:
            path.rmdir()
    score_run.rmdir()

    with pytest.raises(packager.PackageMiniwobError, match="Unexpected score run count"):
        packager.build_bundle_spec("bundle", config=config)


def test_full122_rejects_mixed_score_prompt_hashes(tmp_path: Path) -> None:
    config, cases = _package_fixture(tmp_path)
    config = replace(config, profile="full122", strict_score_protocol=True)
    manifest_path = _manifest_for(config, cases["remaining22"][0], "agent_c")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["score_prompt_sha256"] = "prompt-legacy"
    _write_json(manifest_path, manifest)

    with pytest.raises(packager.PackageMiniwobError, match="Score protocol mismatch"):
        packager.build_bundle_spec("bundle", config=config)


def test_full122_rejects_missing_score_protocol_field(tmp_path: Path) -> None:
    config, cases = _package_fixture(tmp_path)
    config = replace(config, profile="full122", strict_score_protocol=True)
    manifest_path = _manifest_for(config, cases["remaining22"][0], "agent_c")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["service_tier"]
    _write_json(manifest_path, manifest)

    with pytest.raises(packager.PackageMiniwobError, match="missing non-empty protocol field service_tier"):
        packager.build_bundle_spec("bundle", config=config)


def test_current100_allows_historical_mixed_score_prompt_hashes(tmp_path: Path) -> None:
    config, cases = _package_fixture(tmp_path)
    config = replace(config, profile="current100", strict_score_protocol=False)
    manifest_path = _manifest_for(config, cases["first50"][0], "agent_a")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["score_prompt_sha256"] = "prompt-legacy"
    _write_json(manifest_path, manifest)

    spec = packager.build_bundle_spec("bundle", config=config)

    assert spec["manifest"]["case_count"] == 3
    assert spec["manifest"]["strict_score_protocol"] is False
    assert spec["manifest"]["score_protocol"] is None
