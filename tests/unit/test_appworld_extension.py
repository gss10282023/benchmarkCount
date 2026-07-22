from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from evidence_system.adapters.appworld import _source_ref
from evidence_system.adapters.appworld_official_worker import resolve_dataset_name
from evidence_system.contracts.appworld_extension import (
    APPWORLD_DATA_VERSION,
    APPWORLD_GIT_COMMIT,
    EXPECTED_CHALLENGE_COUNT,
    EXPECTED_EXTENSION_COUNT,
    EXPECTED_FILES_PER_TASK,
    EXPECTED_NORMAL_EXTENSION_COUNT,
    EXPECTED_RECORD_SLOT_COUNT,
    build_appworld_extension,
    validate_extension_packets,
    validate_extension_source_bundle,
    write_acceptance_report,
)
from evidence_system.contracts.case_packets import build_case_packets
from evidence_system.contracts.common import ContractLifecycleError


ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = (
    ROOT / "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
)


def test_frozen_extension_definition_is_exact_and_disjoint() -> None:
    manifest = _load_json(EXTENSION_ROOT / "experiment_manifest.json")
    catalog = _load_json(EXTENSION_ROOT / "official_splits/appworld_selected_task_sources.json")
    scope = _load_json(EXTENSION_ROOT / "frozen_scope.json")
    cases = manifest["domains"][0]["case_units"]
    items = catalog["items"]

    assert len(cases) == len(items) == EXPECTED_EXTENSION_COUNT
    assert manifest["domains"][0]["case_unit_count"] == EXPECTED_EXTENSION_COUNT
    assert manifest["domains"][0]["record_slot_count"] == EXPECTED_RECORD_SLOT_COUNT
    assert catalog["selected_count_by_dataset"] == {
        "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
        "test_challenge": EXPECTED_CHALLENGE_COUNT,
    }
    assert [case["case_unit_id"] for case in cases] == [item["task_id"] for item in items]
    assert len({case["case_unit_id"] for case in cases}) == EXPECTED_EXTENSION_COUNT
    assert all(
        item["source_ref"] == f"appworld://{item['dataset_name']}/{item['task_id']}"
        and item["case_unit_id"] == item["task_id"]
        and item["file_count"] == EXPECTED_FILES_PER_TASK
        for item in items
    )
    assert scope["appworld"]["git_commit"] == APPWORLD_GIT_COMMIT
    assert scope["appworld"]["data_version"] == APPWORLD_DATA_VERSION
    assert scope["scope"]["completed_case_count"] == 100
    assert scope["scope"]["full_test_case_count"] == 585
    assert "需要从 locked manifest 确认" not in json.dumps(scope["contract_drafter"])
    assert scope["contract_drafter"]["resolved_config"]["reasoning_effort"] == "high"
    assert manifest["completed_cohort"]["rule_sha256"]


def test_materialized_packets_pass_full_strict_gate() -> None:
    audit = validate_extension_packets(output_root=EXTENSION_ROOT)

    assert audit["packet_count"] == EXPECTED_EXTENSION_COUNT
    assert audit["packet_count_by_dataset"] == {"test_normal": 68, "test_challenge": 417}
    assert audit["verified_official_file_count"] == EXPECTED_EXTENSION_COUNT * EXPECTED_FILES_PER_TASK
    assert audit["verified_official_byte_count"] == 18_497_868
    assert audit["packet_source_tree_sha256"] == "d04327a4eeaabcf20d04b6b7edb813e2388c9679a0ab8e2829bebb68caaf4931"


def test_materialized_source_bundle_has_exact_split_routing() -> None:
    audit = validate_extension_source_bundle(output_root=EXTENSION_ROOT)
    bundle = _load_json(EXTENSION_ROOT / "source_bundles/case_packet_source_bundle.json")

    assert audit["source_count"] == EXPECTED_EXTENSION_COUNT
    assert audit["routing_metadata_verified"] is True
    assert bundle["manifest_sha256"] == hashlib.sha256(
        (EXTENSION_ROOT / "experiment_manifest.json").read_bytes()
    ).hexdigest()
    assert {source["dataset_name"] for source in bundle["sources"]} == {"test_normal", "test_challenge"}
    assert all(
        source["source_ref"] == f"appworld://{source['dataset_name']}/{source['task_id']}"
        for source in bundle["sources"]
    )


def test_local_packet_builder_rejects_catalog_file_hash_drift(tmp_path: Path) -> None:
    catalog = _load_json(EXTENSION_ROOT / "official_splits/appworld_selected_task_sources.json")
    item = dict(catalog["items"][0])
    item["files"] = {key: dict(value) for key, value in item["files"].items()}
    item["files"]["specs.json"]["sha256"] = "sha256:" + "0" * 64
    isolated_catalog = {
        "schema_version": catalog["schema_version"],
        "benchmark": "AppWorld",
        "selected_count": 1,
        "items": [item],
    }
    official_splits = tmp_path / "official_splits"
    official_splits.mkdir()
    (official_splits / "appworld_selected_task_sources.json").write_text(
        json.dumps(isolated_catalog, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "domains": [
            {
                "domain": "appworld",
                "case_unit_count": 1,
                "case_units": [
                    {
                        "case_unit_id": item["task_id"],
                        "task_id": item["task_id"],
                        "dataset_name": item["dataset_name"],
                        "source_ref": item["source_ref"],
                    }
                ],
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="catalog hash mismatch"):
        build_case_packets(
            manifest_path=manifest_path,
            official_splits_path=official_splits,
            output_root=tmp_path / "packets",
            source_mode="local",
        )


def test_extension_builder_rejects_input_output_overlap_before_writing(tmp_path: Path) -> None:
    output_root = tmp_path / "extension"
    overlapping_normal_split = output_root / "normal.txt"

    with pytest.raises(ContractLifecycleError, match="must be disjoint"):
        build_appworld_extension(
            output_root=output_root,
            normal_split_path=overlapping_normal_split,
        )

    assert not output_root.exists()


def test_extension_builder_rejects_split_membership_swap(tmp_path: Path) -> None:
    normal_ids = (ROOT / "experiments/official_splits/appworld_test_normal.txt").read_text(encoding="utf-8").splitlines()
    challenge_ids = (
        ROOT / "experiments/official_splits/appworld_test_challenge.not_selected.txt"
    ).read_text(encoding="utf-8").splitlines()
    normal_ids[0], challenge_ids[0] = challenge_ids[0], normal_ids[0]
    normal_path = tmp_path / "normal.txt"
    challenge_path = tmp_path / "challenge.txt"
    normal_path.write_text("\n".join(normal_ids) + "\n", encoding="utf-8")
    challenge_path.write_text("\n".join(challenge_ids) + "\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="canonical AppWorld .* split hash mismatch"):
        build_appworld_extension(
            output_root=tmp_path / "extension",
            normal_split_path=normal_path,
            challenge_split_path=challenge_path,
        )


def test_packet_gate_rejects_extra_raw_manifest_fields(tmp_path: Path) -> None:
    packet_copy = tmp_path / "case_packets"
    shutil.copytree(EXTENSION_ROOT / "case_packets", packet_copy, copy_function=os.link)
    first_case_id = _load_json(EXTENSION_ROOT / "experiment_manifest.json")["domains"][0]["case_units"][0][
        "case_unit_id"
    ]
    manifest_path = packet_copy / "appworld" / first_case_id / "raw_case_manifest.json"
    payload = _load_json(manifest_path)
    payload["native_score"] = 1
    manifest_path.unlink()
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="exact catalog-derived manifest"):
        validate_extension_packets(output_root=EXTENSION_ROOT, case_packets_root=packet_copy)


def test_acceptance_report_cannot_escape_extension_provenance_root(tmp_path: Path) -> None:
    forbidden = tmp_path / "agents.yaml"
    forbidden.write_text("sentinel\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="must be a JSON file inside"):
        write_acceptance_report(output_root=EXTENSION_ROOT, report_path=forbidden)

    assert forbidden.read_text(encoding="utf-8") == "sentinel\n"


def test_appworld_worker_prefers_explicit_bundle_routing_metadata() -> None:
    entry = {
        "task_id": "abcdef0_1",
        "dataset_name": "test_challenge",
        "source_ref": "appworld://test_challenge/abcdef0_1",
    }

    assert _source_ref(entry) == entry["source_ref"]
    assert resolve_dataset_name(task_id="abcdef0_1", source_entry=entry) == "test_challenge"
    with pytest.raises(RuntimeError, match="dataset_name/source_ref mismatch"):
        resolve_dataset_name(
            task_id="abcdef0_1",
            source_entry={**entry, "dataset_name": "test_normal"},
        )
    with pytest.raises(RuntimeError, match="source_ref task mismatch"):
        resolve_dataset_name(
            task_id="abcdef0_2",
            source_entry={**entry, "task_id": "abcdef0_2"},
        )


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
