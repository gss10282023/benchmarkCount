from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence_system.cli.build_case_packet_source_bundle import (
    ManifestCase,
    main,
    validate_source_bundle_strict,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file


def test_cli_builds_bundle_only_after_exact_set_and_hash_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_temporary_repo(tmp_path, monkeypatch)
    cases = _write_fixture(tmp_path)

    result = main(
        [
            "--manifest",
            "experiment/manifest.json",
            "--case-packets-root",
            "experiment/case_packets",
            "--output",
            "experiment/source_bundles/bundle.json",
            "--expected-count",
            "2",
            "--expected-domain",
            "agentdojo",
            "--allow-generated-contract-ids",
            "--json",
        ]
    )

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "ok"
    assert report["exact_case_id_set_verified"] is True
    assert report["packet_directory_set_verified"] is True
    assert report["verified_file_hash_count"] == 4
    bundle_path = tmp_path / "experiment/source_bundles/bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert [source["case_unit_id"] for source in bundle["sources"]] == [case.case_unit_id for case in cases]
    for source in bundle["sources"]:
        draft_input = source["draft_input"]
        assert draft_input["case_packet_sha256"] == sha256_file(tmp_path / draft_input["case_packet_path"])
        assert draft_input["raw_case_manifest_sha256"] == sha256_file(
            tmp_path / draft_input["raw_case_manifest_path"]
        )


def test_cli_rejects_extra_packet_directory_and_does_not_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_temporary_repo(tmp_path, monkeypatch)
    _write_fixture(tmp_path)
    extra = tmp_path / "experiment/case_packets/agentdojo/extra_case"
    extra.mkdir(parents=True)
    output = tmp_path / "experiment/source_bundles/bundle.json"

    result = main(
        [
            "--manifest",
            "experiment/manifest.json",
            "--case-packets-root",
            "experiment/case_packets",
            "--output",
            "experiment/source_bundles/bundle.json",
            "--expected-count",
            "2",
            "--allow-generated-contract-ids",
            "--json",
        ]
    )

    assert result == 2
    assert "case-packet directory set mismatch" in json.loads(capsys.readouterr().err)["reason"]
    assert not output.exists()


def test_cli_rejects_count_mismatch_before_replacing_existing_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_temporary_repo(tmp_path, monkeypatch)
    _write_fixture(tmp_path)
    output = tmp_path / "experiment/source_bundles/bundle.json"
    output.parent.mkdir(parents=True)
    output.write_text('{"sentinel": true}\n', encoding="utf-8")

    result = main(
        [
            "--manifest",
            "experiment/manifest.json",
            "--case-packets-root",
            "experiment/case_packets",
            "--output",
            "experiment/source_bundles/bundle.json",
            "--expected-count",
            "949",
            "--allow-generated-contract-ids",
            "--json",
        ]
    )

    assert result == 2
    assert "manifest case count mismatch: expected=949, actual=2" in json.loads(capsys.readouterr().err)["reason"]
    assert json.loads(output.read_text(encoding="utf-8")) == {"sentinel": True}


def test_strict_validation_detects_packet_mutation_after_bundle_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_temporary_repo(tmp_path, monkeypatch)
    cases = _write_fixture(tmp_path)
    assert (
        main(
            [
                "--manifest",
                "experiment/manifest.json",
                "--case-packets-root",
                "experiment/case_packets",
                "--output",
                "experiment/source_bundles/bundle.json",
                "--expected-count",
                "2",
                "--allow-generated-contract-ids",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    packet = tmp_path / "experiment/case_packets/agentdojo/v1.2.2_banking_user_task_0_injection_task_0/case_packet.md"
    packet.write_text("mutated\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="case_packet_sha256 does not match local file"):
        validate_source_bundle_strict(
            source_bundle_path="experiment/source_bundles/bundle.json",
            manifest_path="experiment/manifest.json",
            case_packets_root="experiment/case_packets",
            expected_cases=cases,
            expected_count=2,
            expected_domains=["agentdojo"],
        )


def test_strict_validation_rejects_non_exact_bundle_case_id_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_temporary_repo(tmp_path, monkeypatch)
    cases = _write_fixture(tmp_path)
    assert (
        main(
            [
                "--manifest",
                "experiment/manifest.json",
                "--case-packets-root",
                "experiment/case_packets",
                "--output",
                "experiment/source_bundles/bundle.json",
                "--expected-count",
                "2",
                "--allow-generated-contract-ids",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    bundle_path = tmp_path / "experiment/source_bundles/bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["sources"][0]["case_unit_id"] = "v1.2.2:banking:user_task_99:injection_task_99"
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="source bundle case ID set mismatch"):
        validate_source_bundle_strict(
            source_bundle_path="experiment/source_bundles/bundle.json",
            manifest_path="experiment/manifest.json",
            case_packets_root="experiment/case_packets",
            expected_cases=cases,
            expected_count=2,
            expected_domains=["agentdojo"],
        )


def test_manifest_source_bundle_hash_cycle_uses_stable_definition_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_temporary_repo(tmp_path, monkeypatch)
    _write_fixture(tmp_path)
    manifest_path = tmp_path / "experiment/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_bundle_hash"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    argv = [
        "--manifest",
        "experiment/manifest.json",
        "--case-packets-root",
        "experiment/case_packets",
        "--output",
        "experiment/source_bundles/bundle.json",
        "--expected-count",
        "2",
        "--allow-generated-contract-ids",
        "--json",
    ]

    assert main(argv) == 0
    capsys.readouterr()
    bundle_path = tmp_path / "experiment/source_bundles/bundle.json"
    first_bytes = bundle_path.read_bytes()
    bundle = json.loads(first_bytes)
    assert "manifest_sha256" not in bundle
    assert bundle["manifest_definition_sha256_scope"] == "canonical_mapping_without_source_bundle_hash"
    assert bundle["manifest_definition_excluded_fields"] == ["source_bundle_hash"]

    manifest["source_bundle_hash"] = sha256_file(bundle_path)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    assert main(argv) == 0
    capsys.readouterr()
    assert bundle_path.read_bytes() == first_bytes


def test_strict_validation_detects_raw_case_inventory_hash_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_temporary_repo(tmp_path, monkeypatch)
    cases = _write_fixture(tmp_path)
    case = cases[0]
    case_dir = tmp_path / "experiment/case_packets" / case.domain / re_safe(case.case_unit_id)
    raw_dir = case_dir / "raw_case"
    raw_dir.mkdir(exist_ok=True)
    raw_file = raw_dir / "selected_task_source.json"
    raw_file.write_text('{"locked": true}\n', encoding="utf-8")
    raw_manifest_path = case_dir / "raw_case_manifest.json"
    raw_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
    raw_manifest.update(
        {
            "copied_files": [raw_file.name],
            "official_files": [raw_file.name],
            "packet_files": [raw_file.name],
            "sha256_per_file": {raw_file.name: sha256_file(raw_file)},
        }
    )
    raw_manifest_path.write_text(json.dumps(raw_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    argv = [
        "--manifest",
        "experiment/manifest.json",
        "--case-packets-root",
        "experiment/case_packets",
        "--output",
        "experiment/source_bundles/bundle.json",
        "--expected-count",
        "2",
        "--allow-generated-contract-ids",
        "--json",
    ]
    assert main(argv) == 0
    capsys.readouterr()
    raw_file.write_text('{"locked": false}\n', encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="sha256_per_file"):
        validate_source_bundle_strict(
            source_bundle_path="experiment/source_bundles/bundle.json",
            manifest_path="experiment/manifest.json",
            case_packets_root="experiment/case_packets",
            expected_cases=cases,
            expected_count=2,
            expected_domains=["agentdojo"],
        )


def _use_temporary_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("evidence_system.core.paths.repo_root", lambda: tmp_path)


def _write_fixture(root: Path) -> list[ManifestCase]:
    cases = [
        ManifestCase(
            domain="agentdojo",
            case_unit_id="v1.2.2:banking:user_task_0:injection_task_0",
            task_id="banking:user_task_0:injection_task_0",
        ),
        ManifestCase(
            domain="agentdojo",
            case_unit_id="v1.2.2:slack:user_task_1:injection_task_2",
            task_id="slack:user_task_1:injection_task_2",
        ),
    ]
    manifest = {
        "domains": [
            {
                "domain": "agentdojo",
                "case_unit_count": len(cases),
                "case_units": [
                    {"case_unit_id": case.case_unit_id, "task_id": case.task_id}
                    for case in cases
                ],
            }
        ]
    }
    manifest_path = root / "experiment/manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for case in cases:
        directory_name = re_safe(case.case_unit_id)
        case_dir = root / "experiment/case_packets" / case.domain / directory_name
        case_dir.mkdir(parents=True)
        (case_dir / "raw_case").mkdir()
        (case_dir / "case_packet.md").write_text(f"# {case.case_unit_id}\n", encoding="utf-8")
        raw_manifest = {
            "domain": case.domain,
            "case_unit_id": case.case_unit_id,
            "task_id": case.task_id,
            "source_refs": [f"agentdojo://{case.case_unit_id}"],
            "copied_files": [],
            "official_files": [],
            "derived_files": [],
            "packet_files": [],
            "sha256_per_file": {},
        }
        (case_dir / "raw_case_manifest.json").write_text(
            json.dumps(raw_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return cases


def re_safe(case_unit_id: str) -> str:
    return case_unit_id.replace(":", "_")
