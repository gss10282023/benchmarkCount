from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from evidence_system.contracts import appworld_draft_overlay as overlay
from evidence_system.contracts.appworld_draft_overlay import (
    CORRECTIONS_SCHEMA,
    EXPECTED_LOCATION_CASE_IDS,
    LOCKED_STATUS,
    OverlayInputs,
    SECURITY_CASE_ID,
    materialize_appworld_draft_overlay,
    validate_appworld_draft_overlay,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _case(path: Path, marker: str, *, canonical: bool = False) -> None:
    path.mkdir(parents=True)
    _write(path / "marker.txt", marker)
    if canonical:
        for suffix in overlay.EXPECTED_CANONICAL_SUFFIXES:
            _write(path / suffix, f"{marker}:{suffix}\n")


def _guard(label: str, path: Path, kind: str) -> tuple[str, Path, str, str]:
    return (label, path, kind, sha256_file(path) if kind == "file" else sha256_path(path))


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> OverlayInputs:
    monkeypatch.setattr(overlay, "repo_root", lambda: tmp_path)
    draft_root = tmp_path / "draft"
    provenance = draft_root / "provenance"
    formal = draft_root / "cases"
    candidate = draft_root / "repair_location_v1" / "candidates"
    security_root = draft_root / "corrections" / "round_02"
    legacy_root = draft_root / "accepted_cases"
    round_01 = draft_root / "corrections" / "round_01"
    packet_root = tmp_path / "packets"

    unchanged = tuple(f"unchanged_{index:03d}" for index in range(472))
    case_ids = (*EXPECTED_LOCATION_CASE_IDS, SECURITY_CASE_ID, *unchanged)
    assert len(case_ids) == 485 and len(set(case_ids)) == 485

    formal.mkdir(parents=True)
    for case_id in case_ids:
        _case(formal / case_id, f"formal:{case_id}")
    formal_results = formal / "_batch_results.jsonl"
    formal_rows = tuple(
        {"case_unit_dir": case_id, "status": "success"}
        for case_id in reversed(case_ids)
    )
    _write(formal_results, "".join(json.dumps(row, sort_keys=True) + "\n" for row in formal_rows))
    formal_summary = formal / "_batch_summary.json"
    _write(formal_summary, json.dumps({"success_cases": 485}) + "\n")
    formal_lock = provenance / "draft_run_lock.json"
    _write(formal_lock, json.dumps({"schema_version": "appworld_draft_run_lock.v2"}) + "\n")

    candidate.mkdir(parents=True)
    candidate_rows = []
    for case_id in EXPECTED_LOCATION_CASE_IDS:
        _case(candidate / case_id, f"candidate:{case_id}", canonical=True)
        _write(packet_root / case_id / "case_packet.md", f"packet:{case_id}\n")
        candidate_rows.append(
            {
                "schema_version": "appworld_draft_candidate_results.v1",
                "case_unit_id": case_id,
                "generation_status": "success",
                "strict_validation_status": "passed",
                "promotion_performed": False,
            }
        )
    candidate_results = candidate / "_candidate_results.jsonl"
    _write(candidate_results, "".join(json.dumps(row, sort_keys=True) + "\n" for row in candidate_rows))
    candidate_summary = candidate / "_candidate_summary.json"
    _write(candidate_summary, json.dumps({"status": "candidate_generated/review_required"}) + "\n")
    candidate_validation = candidate / "_candidate_validation.json"
    validation_payload = {"schema_version": "appworld_draft_candidate_validation.v1", "status": "passed"}
    _write(candidate_validation, json.dumps(validation_payload) + "\n")
    repair_lock = provenance / "draft_repair_lock.json"
    _write(repair_lock, json.dumps({"schema_version": "appworld_draft_repair_lock.v1"}) + "\n")

    security_case = security_root / SECURITY_CASE_ID
    _case(security_case, "security-candidate", canonical=True)
    _write(packet_root / SECURITY_CASE_ID / "case_packet.md", "packet:security\n")
    security_results = security_root / "_batch_results.jsonl"
    security_row = {
        "case_unit_dir": SECURITY_CASE_ID,
        "case_packet": "/private/tmp/security/case_packet.md",
        "status": "success",
    }
    _write(security_results, json.dumps(security_row, sort_keys=True) + "\n")
    security_summary = security_root / "_batch_summary.json"
    _write(security_summary, json.dumps({"success_cases": 1}) + "\n")

    legacy_root.mkdir(parents=True)
    for case_id in case_ids:
        _case(legacy_root / case_id, f"legacy:{case_id}")
    legacy_manifest = provenance / "draft_corrections.json"
    _write(
        legacy_manifest,
        json.dumps(
            {
                "schema_version": "appworld_draft_corrections.v2",
                "correction_count": 2,
                "corrections": [
                    {"case_unit_id": "9ef034e_2"},
                    {"case_unit_id": SECURITY_CASE_ID},
                ],
            }
        )
        + "\n",
    )
    _case(round_01 / "9ef034e_2", "round-01")
    _write(round_01 / "_batch_results.jsonl", "{}\n")
    _write(round_01 / "_batch_summary.json", "{}\n")

    accepted = draft_root / "accepted_cases_location_v1"
    corrections = provenance / "draft_corrections_location_v1.json"
    guards = (
        _guard("formal lock", formal_lock, "file"),
        _guard("formal cases", formal, "tree"),
        _guard("repair lock", repair_lock, "file"),
        _guard("candidate root", candidate, "tree"),
        _guard("security round", security_root, "tree"),
        _guard("legacy manifest", legacy_manifest, "file"),
        _guard("legacy accepted", legacy_root, "tree"),
        _guard("round 01", round_01, "tree"),
    )
    return OverlayInputs(
        formal_lock_path=formal_lock,
        formal_lock={"schema_version": "appworld_draft_run_lock.v2"},
        formal_cases_root=formal,
        formal_batch_results_path=formal_results,
        formal_batch_summary_path=formal_summary,
        formal_batch_rows=formal_rows,
        expected_case_ids=case_ids,
        packet_root=packet_root,
        repair_lock_path=repair_lock,
        repair_lock={"schema_version": "appworld_draft_repair_lock.v1"},
        candidate_root=candidate,
        candidate_results_path=candidate_results,
        candidate_summary_path=candidate_summary,
        candidate_validation_path=candidate_validation,
        candidate_rows=tuple(candidate_rows),
        candidate_validation=validation_payload,
        candidate_rows_by_id={str(row["case_unit_id"]): row for row in candidate_rows},
        security_root=security_root,
        security_case_dir=security_case,
        security_batch_results_path=security_results,
        security_batch_summary_path=security_summary,
        security_result_row=security_row,
        security_normalization={
            "allowed_changed_fields": ["case_packet"],
            "source_case_packet": security_row["case_packet"],
            "normalized_case_packet": packet_root.joinpath(SECURITY_CASE_ID, "case_packet.md").relative_to(tmp_path).as_posix(),
        },
        legacy_manifest_path=legacy_manifest,
        legacy_accepted_root=legacy_root,
        round_01_root=round_01,
        accepted_root=accepted,
        corrections_path=corrections,
        immutable_guards=guards,
    )


def _install_loader(monkeypatch: pytest.MonkeyPatch, inputs: OverlayInputs) -> None:
    def fake_loader(**kwargs: Any) -> OverlayInputs:
        state = kwargs["output_state"]
        if state == "absent":
            if inputs.accepted_root.exists() or inputs.corrections_path.exists():
                raise ContractLifecycleError("outputs already exist")
        else:
            if not inputs.accepted_root.is_dir() or not inputs.corrections_path.is_file():
                raise ContractLifecycleError("outputs are missing")
        return inputs

    monkeypatch.setattr(overlay, "_load_overlay_inputs", fake_loader)


def _materialize(inputs: OverlayInputs) -> dict[str, Any]:
    return materialize_appworld_draft_overlay(
        formal_lock_path=inputs.formal_lock_path,
        repair_lock_path=inputs.repair_lock_path,
        accepted_cases_root=inputs.accepted_root,
        corrections_path=inputs.corrections_path,
    )


def _validate(inputs: OverlayInputs) -> dict[str, Any]:
    return validate_appworld_draft_overlay(
        formal_lock_path=inputs.formal_lock_path,
        repair_lock_path=inputs.repair_lock_path,
        accepted_cases_root=inputs.accepted_root,
        corrections_path=inputs.corrections_path,
    )


def test_atomic_materialization_uses_472_formal_12_location_and_one_security_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture(tmp_path, monkeypatch)
    _install_loader(monkeypatch, inputs)
    input_hashes = [(path, kind, digest) for _, path, kind, digest in inputs.immutable_guards]

    result = _materialize(inputs)

    assert result["status"] == LOCKED_STATUS
    assert len(list(inputs.accepted_root.iterdir())) == 485
    assert (inputs.accepted_root / EXPECTED_LOCATION_CASE_IDS[0] / "marker.txt").read_text().startswith("candidate:")
    assert (inputs.accepted_root / SECURITY_CASE_ID / "marker.txt").read_text() == "security-candidate"
    assert (inputs.accepted_root / "unchanged_000" / "marker.txt").read_text().startswith("formal:")
    manifest = json.loads(inputs.corrections_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == CORRECTIONS_SCHEMA
    assert set(manifest) == overlay._TOP_LEVEL_KEYS
    assert manifest["accepted_overlay"]["case_count"] == 485
    assert manifest["accepted_overlay"]["unchanged_case_count"] == 472
    assert manifest["accepted_overlay"]["corrected_case_count"] == 13
    assert [item["case_unit_id"] for item in manifest["corrections"]["location_corrections"]] == list(EXPECTED_LOCATION_CASE_IDS)
    assert manifest["corrections"]["security_correction"]["case_unit_id"] == SECURITY_CASE_ID
    assert manifest["security_incident_inventory"] == {
        "scanner_schema": "appworld_draft_secret_scan.v1",
        "affected_case_ids": ["9ef034e_2", SECURITY_CASE_ID],
        "formal_hits_by_case": {"9ef034e_2": 44, SECURITY_CASE_ID: 40},
        "formal_hit_count": 84,
        "accepted_hit_count": 0,
        "credential_values_recorded": False,
    }
    location_by_id = {
        item["case_unit_id"]: item
        for item in manifest["corrections"]["location_corrections"]
    }
    assert location_by_id["9ef034e_2"]["secondary_defect"] == {
        "kind": "secret_like_material",
        "formal_hit_count": 44,
        "accepted_hit_count": 0,
    }
    assert all(
        item["secondary_defect"] is None
        for case_id, item in location_by_id.items()
        if case_id != "9ef034e_2"
    )
    for path, kind, digest in input_hashes:
        assert (sha256_file(path) if kind == "file" else sha256_path(path)) == digest

    with pytest.raises(ContractLifecycleError, match="outputs already exist"):
        _materialize(inputs)


def test_copy_failure_cleans_temporary_and_final_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture(tmp_path, monkeypatch)
    _install_loader(monkeypatch, inputs)
    real_copytree = overlay.shutil.copytree
    calls = 0

    def failing_copytree(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise OSError("injected copy failure")
        return real_copytree(*args, **kwargs)

    monkeypatch.setattr(overlay.shutil, "copytree", failing_copytree)
    with pytest.raises(OSError, match="injected copy failure"):
        _materialize(inputs)
    assert not inputs.accepted_root.exists()
    assert not inputs.corrections_path.exists()
    assert not list(inputs.accepted_root.parent.glob(f".{inputs.accepted_root.name}.tmp-*"))


def test_validation_fails_closed_after_accepted_case_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture(tmp_path, monkeypatch)
    _install_loader(monkeypatch, inputs)
    _materialize(inputs)
    _write(inputs.accepted_root / "unchanged_001" / "marker.txt", "tampered\n")

    with pytest.raises(ContractLifecycleError, match="authoritative source"):
        _validate(inputs)


def test_secret_like_material_blocks_materialization_without_leaving_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture(tmp_path, monkeypatch)
    secret_source = inputs.formal_cases_root / "unchanged_002" / "marker.txt"
    _write(secret_source, "sk-" + "x" * 24)
    guards = tuple(
        _guard(label, path, kind)
        for label, path, kind, _ in inputs.immutable_guards
    )
    inputs = replace(inputs, immutable_guards=guards)
    _install_loader(monkeypatch, inputs)

    with pytest.raises(ContractLifecycleError, match="secret-like material"):
        _materialize(inputs)
    assert not inputs.accepted_root.exists()
    assert not inputs.corrections_path.exists()


def test_exclusive_manifest_writer_refuses_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "manifest.json"
    _write(target, "{\"owner\": \"existing\"}\n")
    with pytest.raises(ContractLifecycleError, match="overwrite"):
        overlay._write_json_exclusive(target, {"owner": "new"})
    assert json.loads(target.read_text(encoding="utf-8")) == {"owner": "existing"}


def test_concurrent_empty_destination_is_preserved_and_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture(tmp_path, monkeypatch)
    _install_loader(monkeypatch, inputs)
    real_copy = overlay._copy_authoritative_cases

    def copy_then_race(current: OverlayInputs, destination: Path) -> None:
        real_copy(current, destination)
        current.accepted_root.mkdir()

    monkeypatch.setattr(overlay, "_copy_authoritative_cases", copy_then_race)
    with pytest.raises(ContractLifecycleError, match="appeared during materialization"):
        _materialize(inputs)
    assert inputs.accepted_root.is_dir()
    assert not any(inputs.accepted_root.iterdir())
    assert not inputs.corrections_path.exists()
    assert not (inputs.accepted_root.parent / f".{inputs.accepted_root.name}.materialize.lock").exists()


def test_existing_sibling_lock_blocks_without_touching_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture(tmp_path, monkeypatch)
    _install_loader(monkeypatch, inputs)
    lock_path = inputs.accepted_root.parent / f".{inputs.accepted_root.name}.materialize.lock"
    _write(lock_path, "other owner\n")

    with pytest.raises(ContractLifecycleError, match="lock already exists"):
        _materialize(inputs)
    assert lock_path.read_text(encoding="utf-8") == "other owner\n"
    assert not inputs.accepted_root.exists()
    assert not inputs.corrections_path.exists()


def test_failure_cleanup_never_deletes_concurrently_replaced_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture(tmp_path, monkeypatch)
    _install_loader(monkeypatch, inputs)

    def replace_outputs_then_fail(**_: Any) -> dict[str, Any]:
        shutil.rmtree(inputs.accepted_root)
        inputs.accepted_root.mkdir()
        _write(inputs.accepted_root / "external-owner.txt", "external root\n")
        inputs.corrections_path.unlink()
        _write(inputs.corrections_path, '{"owner":"external"}\n')
        raise ContractLifecycleError("injected post-commit validation failure")

    monkeypatch.setattr(overlay, "validate_appworld_draft_overlay", replace_outputs_then_fail)
    with pytest.raises(ContractLifecycleError, match="post-commit"):
        _materialize(inputs)
    assert (inputs.accepted_root / "external-owner.txt").read_text(encoding="utf-8") == "external root\n"
    assert json.loads(inputs.corrections_path.read_text(encoding="utf-8")) == {"owner": "external"}
    assert not (inputs.accepted_root.parent / f".{inputs.accepted_root.name}.materialize.lock").exists()
