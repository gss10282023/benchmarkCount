from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from evidence_system.webarena_fault_injection import (
    FAULT_KINDS,
    FaultInjectionValidationError,
    build_fault_acceptance,
    build_fault_receipt,
    build_local_simulation_receipts,
    classify_fault_observation,
    classify_recovery_observation,
    expected_semantics,
    local_simulation_facts,
    passing_observation,
    passing_recovery,
    scan_sensitive_material,
    validate_fault_acceptance,
    validate_fault_receipt,
    write_fault_acceptance,
    write_fault_receipt,
)


TIMESTAMP = "2026-07-16T00:00:00Z"


def _receipt(kind: str = "site_outage", **overrides):
    values = {
        "machine_id": "local-harness",
        "kind": kind,
        "execution_mode": "local_simulation",
        "observed_semantics": passing_observation(kind),
        "recovery": passing_recovery(kind),
        "completed_at": TIMESTAMP,
    }
    values.update(overrides)
    return build_fault_receipt(**values)


def _write_remote_raw_evidence(
    *,
    path: Path,
    machine_id: str,
    kind: str,
    artifact_kind: str,
    fingerprint: str,
) -> None:
    from evidence_system.core.hashing import sha256_object

    observation, recovery = local_simulation_facts(kind)
    facts = observation if artifact_kind == "fault_observation" else recovery
    payload = {
        "schema_version": "webarena_verified_fault_raw_evidence/v1",
        "benchmark": "WebArena-Verified",
        "benchmark_version": "v1.2.3",
        "execution_mode": "remote_real",
        "machine_id": machine_id,
        "agent_id": "Agent A",
        "fault_kind": kind,
        "phase": artifact_kind,
        "measured_at": TIMESTAMP,
        "ssh_host_ed25519_fingerprint": fingerprint,
        "executor_source_sha256": "a" * 64,
        "site_lock_core_sha256": "b" * 64,
        "facts": facts,
        "measurements": {"test_double": True},
        "raw_stdout_or_stderr_persisted": False,
        "provider_environment_absence_verified": True,
        "provider_environment_probe": {
            "returncode": 0,
            "stdout_sha256": "c" * 64,
            "stderr_sha256": "d" * 64,
            "stdout_bytes": 32,
            "stderr_bytes": 0,
            "raw_output_persisted": False,
        },
        "real_credential_loaded": False,
        "paid_model_calls": 0,
    }
    payload["integrity"] = {
        "algorithm": "sha256_canonical_json",
        "core_sha256": sha256_object(payload),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    path.chmod(0o600)


@pytest.mark.parametrize("kind", FAULT_KINDS)
def test_every_fault_is_infra_excluded_unresolve_and_never_counted(kind: str) -> None:
    receipt = _receipt(kind)

    validate_fault_receipt(receipt)
    observed = receipt["observed_semantics"]
    assert receipt["status"] == "pass"
    assert observed == expected_semantics(kind)
    assert observed["execution_status"] == "INFRA_EXCLUDED"
    assert observed["evidence_label"] == "UNRESOLVE"
    assert observed["score_counted"] is False
    assert observed["agent_failure_counted"] is False
    assert observed["fallback_contract_used"] is False
    assert receipt["safety"]["paid_model_calls"] == 0
    assert receipt["secret_scan"] == {"status": "pass", "finding_count": 0}


def test_fault_stage_controls_model_and_evaluator_boundaries() -> None:
    site = expected_semantics("site_outage")
    login = expected_semantics("login_failure")
    invalid_key = expected_semantics("invalid_placeholder_api_key")
    evaluator = expected_semantics("evaluator_error")

    assert site["model_call_started_during_injection"] is False
    assert login["model_call_started_during_injection"] is False
    assert invalid_key["model_call_started_during_injection"] is True
    assert invalid_key["model_completion_available"] is False
    assert evaluator["model_call_started_during_injection"] is False
    assert evaluator["model_completion_available"] is True
    assert evaluator["official_evaluator_started"] is True
    assert evaluator["official_evaluator_result_validated"] is False


@pytest.mark.parametrize("kind", FAULT_KINDS)
def test_measured_fact_classifiers_are_exact_and_fail_closed(kind: str) -> None:
    observation, recovery = local_simulation_facts(kind)
    assert classify_fault_observation(kind, observation) == expected_semantics(kind)
    assert classify_recovery_observation(kind, recovery) == passing_recovery(kind)

    bad_observation = dict(observation)
    first_key = next(iter(bad_observation))
    bad_observation[first_key] = "tampered"
    with pytest.raises(FaultInjectionValidationError):
        classify_fault_observation(kind, bad_observation)

    bad_recovery = dict(recovery)
    first_key = next(iter(bad_recovery))
    bad_recovery[first_key] = False
    with pytest.raises(FaultInjectionValidationError):
        classify_recovery_observation(kind, bad_recovery)


def test_receipt_write_is_atomic_mode_600_and_hash_bound(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    receipt = _receipt()
    write_fault_receipt(path, receipt)

    assert json.loads(path.read_text(encoding="utf-8")) == receipt
    assert os.stat(path).st_mode & 0o777 == 0o600
    assert os.stat(path.with_suffix(".json.sha256")).st_mode & 0o777 == 0o600
    validate_fault_receipt(receipt)

    tampered = copy.deepcopy(receipt)
    tampered["observed_semantics"]["score_counted"] = True
    with pytest.raises(FaultInjectionValidationError):
        validate_fault_receipt(tampered)


@pytest.mark.parametrize(
    "unsafe",
    [
        {"note": "sk-or-v1-thismustneverappear"},
        {"authorization": "redacted"},
        {"note": "Bearer placeholder-but-still-forbidden"},
        {"storage_state": {}},
    ],
)
def test_secret_scanner_reports_only_detector_and_path(unsafe: dict[str, object]) -> None:
    findings = scan_sensitive_material(unsafe)

    assert findings
    serialized = json.dumps(findings)
    assert "thismustneverappear" not in serialized
    assert "placeholder-but-still-forbidden" not in serialized


def test_builder_does_not_accept_or_persist_credential_values() -> None:
    receipt = _receipt("invalid_placeholder_api_key")
    serialized = json.dumps(receipt, sort_keys=True)

    assert "credential_value" not in serialized
    assert "sk-or-v1-" not in serialized.lower()
    assert receipt["safety"]["placeholder_credential_identifier"] == (
        "known_invalid_openrouter_placeholder_v1"
    )


def test_local_harness_exact_four_passes_without_claiming_remote_gate(
    tmp_path: Path,
) -> None:
    root = tmp_path / "receipts"
    paths = build_local_simulation_receipts(root=root, completed_at=TIMESTAMP)
    acceptance = build_fault_acceptance(
        receipts_root=root,
        scope="local_harness",
    )

    assert len(paths) == 4
    assert acceptance["status"] == "pass"
    assert acceptance["counts"]["validated_receipts"] == 4
    assert acceptance["counts"]["fallback_contracts"] == 0
    assert acceptance["counts"]["score_counted"] == 0
    assert acceptance["counts"]["agent_failures_counted"] == 0
    assert acceptance["counts"]["paid_model_calls"] == 0
    assert acceptance["local_implementation_gate_satisfied"] is True
    assert acceptance["formal_step20_fault_gate_satisfied"] is False
    validate_fault_acceptance(acceptance)


def test_acceptance_blocks_missing_extra_tampered_or_wrong_mode(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    paths = build_local_simulation_receipts(root=root, completed_at=TIMESTAMP)
    paths[0].unlink()
    acceptance = build_fault_acceptance(receipts_root=root, scope="local_harness")
    assert acceptance["status"] == "blocked"

    build_local_simulation_receipts(root=root, completed_at=TIMESTAMP)
    extra = root / "unexpected" / "site_outage" / "receipt.json"
    extra.parent.mkdir(parents=True)
    extra.write_text("{}\n", encoding="utf-8")
    acceptance = build_fault_acceptance(receipts_root=root, scope="local_harness")
    assert acceptance["status"] == "blocked"
    extra.unlink()

    first = root / "local-harness" / "site_outage" / "receipt.json"
    payload = json.loads(first.read_text(encoding="utf-8"))
    payload["execution_mode"] = "remote_real"
    first.write_text(json.dumps(payload), encoding="utf-8")
    acceptance = build_fault_acceptance(receipts_root=root, scope="local_harness")
    assert acceptance["status"] == "blocked"


def test_remote_exact_twelve_is_the_only_formal_fault_gate(tmp_path: Path) -> None:
    root = tmp_path / "remote"
    machine_ids = ("server-a", "server-b", "server-c")
    fingerprints = {
        machine_id: f"SHA256:{machine_id}-locked-fingerprint"
        for machine_id in machine_ids
    }
    for machine_id in machine_ids:
        for kind in FAULT_KINDS:
            evidence = []
            for artifact_kind in ("fault_observation", "recovery_observation"):
                artifact = root / "private" / machine_id / kind / f"{artifact_kind}.json"
                _write_remote_raw_evidence(
                    path=artifact,
                    machine_id=machine_id,
                    kind=kind,
                    artifact_kind=artifact_kind,
                    fingerprint=fingerprints[machine_id],
                )
                from evidence_system.core.hashing import sha256_file

                evidence.append(
                    {
                        "artifact_kind": artifact_kind,
                        "sha256": sha256_file(artifact),
                        "controller_only": True,
                        "relative_reference": artifact.relative_to(root).as_posix(),
                    }
                )
            receipt = build_fault_receipt(
                machine_id=machine_id,
                kind=kind,
                execution_mode="remote_real",
                observed_semantics=passing_observation(kind),
                recovery=passing_recovery(kind),
                remote_attestation={
                    "ssh_host_ed25519_fingerprint": fingerprints[machine_id],
                    "verified_ssh_host_key": True,
                    "controller_machine_id_match": True,
                    "remote_command_executed": True,
                },
                evidence=evidence,
                completed_at=TIMESTAMP,
            )
            write_fault_receipt(root / machine_id / kind / "receipt.json", receipt)

    acceptance = build_fault_acceptance(
        receipts_root=root,
        scope="remote_three_host",
        machine_ids=machine_ids,
        ssh_host_fingerprints=fingerprints,
    )
    assert acceptance["status"] == "pass"
    assert acceptance["counts"]["validated_receipts"] == 12
    assert acceptance["real_remote_execution"] is True
    assert acceptance["formal_step20_fault_gate_satisfied"] is True
    assert acceptance["local_implementation_gate_satisfied"] is False
    validate_fault_acceptance(acceptance)


def test_remote_gate_blocks_missing_hashed_evidence_or_wrong_fingerprint(
    tmp_path: Path,
) -> None:
    root = tmp_path / "remote"
    machine_ids = ("server-a", "server-b", "server-c")
    fingerprints = {machine_id: f"SHA256:{machine_id}" for machine_id in machine_ids}
    for machine_id in machine_ids:
        for kind in FAULT_KINDS:
            evidence = []
            for artifact_kind in ("fault_observation", "recovery_observation"):
                path = root / "private" / machine_id / kind / f"{artifact_kind}.json"
                _write_remote_raw_evidence(
                    path=path,
                    machine_id=machine_id,
                    kind=kind,
                    artifact_kind=artifact_kind,
                    fingerprint=fingerprints[machine_id],
                )
                from evidence_system.core.hashing import sha256_file

                evidence.append(
                    {
                        "artifact_kind": artifact_kind,
                        "sha256": sha256_file(path),
                        "controller_only": True,
                        "relative_reference": path.relative_to(root).as_posix(),
                    }
                )
            receipt = build_fault_receipt(
                machine_id=machine_id,
                kind=kind,
                execution_mode="remote_real",
                observed_semantics=passing_observation(kind),
                recovery=passing_recovery(kind),
                remote_attestation={
                    "ssh_host_ed25519_fingerprint": fingerprints[machine_id],
                    "verified_ssh_host_key": True,
                    "controller_machine_id_match": True,
                    "remote_command_executed": True,
                },
                evidence=evidence,
                completed_at=TIMESTAMP,
            )
            write_fault_receipt(root / machine_id / kind / "receipt.json", receipt)

    (root / "private" / "server-a" / "site_outage" / "fault_observation.json").write_text(
        "tampered\n", encoding="utf-8"
    )
    acceptance = build_fault_acceptance(
        receipts_root=root,
        scope="remote_three_host",
        machine_ids=machine_ids,
        ssh_host_fingerprints={**fingerprints, "server-b": "SHA256:wrong"},
    )
    assert acceptance["status"] == "blocked"
    assert acceptance["formal_step20_fault_gate_satisfied"] is False
    assert acceptance["counts"]["evidence_hash_failures"] == 1
    assert acceptance["counts"]["attestation_failures"] == 4


def test_acceptance_write_is_hash_bound(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    build_local_simulation_receipts(root=root, completed_at=TIMESTAMP)
    acceptance = build_fault_acceptance(receipts_root=root, scope="local_harness")
    output = tmp_path / "acceptance.json"

    write_fault_acceptance(output, acceptance)
    validate_fault_acceptance(json.loads(output.read_text(encoding="utf-8")))
    assert output.with_suffix(".json.sha256").is_file()

    tampered = copy.deepcopy(acceptance)
    tampered["formal_step20_fault_gate_satisfied"] = True
    with pytest.raises(FaultInjectionValidationError):
        validate_fault_acceptance(tampered)
