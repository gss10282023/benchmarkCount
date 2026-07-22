from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.orchestrator.jobs import validate_namespaced_experiment_lock


FULL_NAMESPACE = "agentdojo_full_v1.2.2_direct"
V2_SCHEMA = "agentdojo_full_experiment_lock/v2"
FREEZE_REVISION = "checklist-freeze-v1"
FREEZE_COUNTS = {
    "case_packets": 949,
    "source_entries": 949,
    "valid_drafts": 949,
    "reviewed": 949,
    "locked": 949,
    "unresolved_drafts": 0,
}


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _lock_fixture(
    tmp_path: Path,
    *,
    namespace: str = FULL_NAMESPACE,
    schema_version: str = V2_SCHEMA,
    lock_revision: str | None = FREEZE_REVISION,
    freeze_counts: dict[str, int] | None = None,
) -> tuple[dict[str, Any], Path, Path, Path]:
    manifest_path = _write_json(tmp_path / "experiment_manifest.json", {})
    source_bundle_path = _write_json(tmp_path / "source_bundle.json", {})
    packet_root = tmp_path / "case_packets"
    _write_json(packet_root / "case" / "raw_case_manifest.json", {})

    definition: dict[str, Any] = {
        "result_namespace": namespace,
        "artifacts": {
            "manifest_path": str(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
            "source_bundle_path": str(source_bundle_path),
            "source_bundle_sha256": sha256_file(source_bundle_path),
            "case_packets_root": str(packet_root),
            "case_packets_tree_sha256": sha256_path(packet_root),
        },
        "execution": {"phase": "full", "experiment_type": "appendix"},
        "runtime_code_sha256": {},
        "legacy_artifact_snapshot_sha256": {},
    }
    if lock_revision is not None:
        definition["lock_revision"] = lock_revision
    if freeze_counts is not None:
        definition["checklist_freeze"] = {"counts": freeze_counts}
    lock = {
        "schema_version": schema_version,
        "lock_id": namespace,
        "lock_status": "locked",
        "locked_at": "2026-07-16T00:00:00+00:00",
        **definition,
        "definition_sha256": sha256_object(definition),
    }
    lock_path = _write_json(tmp_path / "experiment_lock.json", lock)
    manifest = {"result_namespace": namespace}
    return manifest, manifest_path, source_bundle_path, lock_path


def _validate(
    manifest: dict[str, Any],
    manifest_path: Path,
    source_bundle_path: Path,
    lock_path: Path,
) -> None:
    validate_namespaced_experiment_lock(
        manifest=manifest,
        manifest_path=manifest_path,
        lock_path=lock_path,
        source_bundle_path=source_bundle_path,
        phase="full",
        experiment_type="appendix",
    )


def test_agentdojo_full_namespace_rejects_pre_freeze_v1_lock(tmp_path: Path) -> None:
    fixture = _lock_fixture(
        tmp_path,
        schema_version="agentdojo_full_experiment_lock/v1",
        lock_revision=None,
        freeze_counts=None,
    )

    with pytest.raises(ValueError, match="requires final checklist-freeze lock schema"):
        _validate(*fixture)


@pytest.mark.parametrize(
    ("revision", "counts", "message"),
    [
        ("stale-revision", FREEZE_COUNTS, "requires lock_revision"),
        (
            FREEZE_REVISION,
            {**FREEZE_COUNTS, "unresolved_drafts": 1},
            "counts must be exactly",
        ),
    ],
)
def test_agentdojo_full_namespace_rejects_incomplete_freeze_definition(
    tmp_path: Path,
    revision: str,
    counts: dict[str, int],
    message: str,
) -> None:
    fixture = _lock_fixture(
        tmp_path,
        lock_revision=revision,
        freeze_counts=counts,
    )

    with pytest.raises(ValueError, match=message):
        _validate(*fixture)


def test_agentdojo_full_namespace_recomputes_freeze_currentness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _lock_fixture(tmp_path, freeze_counts=FREEZE_COUNTS)
    full_experiment = import_module(
        "evidence_system.contracts.agentdojo_full_experiment"
    )
    observed: list[Path] = []

    def verify(*, lock_path: Path) -> SimpleNamespace:
        observed.append(lock_path)
        return SimpleNamespace(snapshot={"counts": FREEZE_COUNTS})

    monkeypatch.setattr(full_experiment, "verify_checklist_freeze_lock", verify)

    _validate(*fixture)

    assert observed == [fixture[3]]


def test_agentdojo_full_namespace_fails_closed_on_stale_freeze(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _lock_fixture(tmp_path, freeze_counts=FREEZE_COUNTS)
    full_experiment = import_module(
        "evidence_system.contracts.agentdojo_full_experiment"
    )

    def reject_currentness(*, lock_path: Path) -> None:
        del lock_path
        raise RuntimeError("review receipt drift")

    monkeypatch.setattr(
        full_experiment,
        "verify_checklist_freeze_lock",
        reject_currentness,
    )

    with pytest.raises(
        ValueError, match="currentness verification failed.*review receipt drift"
    ):
        _validate(*fixture)


def test_other_namespace_keeps_v1_lock_compatibility(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _lock_fixture(
        tmp_path,
        namespace="another_namespaced_experiment",
        schema_version="another_experiment_lock/v1",
        lock_revision=None,
        freeze_counts=None,
    )
    full_experiment = import_module(
        "evidence_system.contracts.agentdojo_full_experiment"
    )

    def must_not_run(**_: Any) -> None:
        raise AssertionError("AgentDojo full freeze verifier must not run")

    monkeypatch.setattr(
        full_experiment,
        "verify_checklist_freeze_lock",
        must_not_run,
    )

    _validate(*fixture)


def test_execution_concurrency_retains_attempted_ramp_and_derives_active_max() -> None:
    execution = import_module(
        "evidence_system.contracts.agentdojo_full_execution"
    )

    ramp, active_maximum = execution._validated_execution_concurrency(
        ramp_workers=(4, 8, 16, 32),
        maximum_workers=None,
        runtime_policy_ramp_stages=(4, 8, 16, 32),
        runtime_policy_maximum_workers=8,
        machine_concurrency=32,
    )

    assert ramp == [4, 8, 16, 32]
    assert active_maximum == 8


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"maximum_workers": 32}, "differs from OpenRouter"),
        ({"maximum_workers": 7}, "one finalized active ceiling"),
        ({"machine_concurrency": 16}, "attempted concurrency-ramp maximum"),
        ({"ramp_workers": (4, 8)}, r"must equal \[4, 8, 16, 32\]"),
    ),
)
def test_execution_concurrency_rejects_inconsistent_active_or_attempted_limits(
    kwargs: dict[str, object], message: str
) -> None:
    execution = import_module(
        "evidence_system.contracts.agentdojo_full_execution"
    )
    arguments: dict[str, object] = {
        "ramp_workers": (4, 8, 16, 32),
        "maximum_workers": None,
        "runtime_policy_ramp_stages": (4, 8, 16, 32),
        "runtime_policy_maximum_workers": 8,
        "machine_concurrency": 32,
    }
    arguments.update(kwargs)

    with pytest.raises(execution.ContractLifecycleError, match=message):
        execution._validated_execution_concurrency(**arguments)


def test_execution_lock_cli_derives_active_maximum_by_default() -> None:
    cli = import_module("evidence_system.cli.lock_agentdojo_full_execution")

    assert cli.build_parser().parse_args([]).maximum_workers is None


def test_execution_lock_schema_accepts_active_max_below_attempted_ramp() -> None:
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / (
        "agentdojo_full_execution_lock.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    concurrency = schema["properties"]["definition"]["properties"][
        "concurrency_policy"
    ]["properties"]
    maximum_validator = Draft202012Validator(concurrency["maximum_workers"])
    ramp_validator = Draft202012Validator(concurrency["ramp_workers"])

    assert list(maximum_validator.iter_errors(8)) == []
    assert list(maximum_validator.iter_errors(7))
    assert list(ramp_validator.iter_errors([4, 8, 16, 32])) == []
    assert list(ramp_validator.iter_errors([4, 8]))


def test_execution_envelope_is_not_runner_admission_after_namespace_growth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    execution = import_module(
        "evidence_system.contracts.agentdojo_full_execution"
    )
    namespace = tmp_path / "formal"
    namespace.mkdir()
    reservation = namespace / "NAMESPACE_LOCK.json"
    reservation_payload = {
        "schema_version": "result_namespace_lock/v1",
        "result_namespace": execution.RESULT_NAMESPACE,
        "experiment_manifest_path": execution._repo_relative(
            execution.resolve_repo_path(execution.DEFAULT_MANIFEST)
        ),
        "formal_result_root": execution._repo_relative(
            execution.resolve_repo_path(execution.DEFAULT_FORMAL_RAW_RESULT_ROOT)
        ),
        "legacy_result_root": "results/full/agentdojo",
        "legacy_result_root_must_not_be_modified": True,
        "status": "reserved_no_formal_runs_yet",
    }
    _write_json(reservation, reservation_payload)
    _write_json(namespace / "promoted-evidence.json", {"status": "promoted"})
    definition = {
        **{
            name: {"path": f"{name}.json", "sha256": "0" * 64}
            for name in (
                "manifest",
                "catalog",
                "source_bundle",
                "agents_config",
                "runtime_infra_overlay",
                "runtime_policy",
                "credential_probe_receipt",
                "disposable_ramp_receipt",
                "vps_provision_receipt",
                "remote_output_precondition_receipt",
                "final_runtime_deployment_receipt",
            )
        },
        "case_packets": {"path": "case_packets", "tree_sha256": "0" * 64},
        "output_precondition": {
            "formal_namespace_reservation": {
                "path": str(reservation),
                "sha256": sha256_file(reservation),
            }
        },
        "budget_control": {
            "budget_plan": {"path": "budget.json"},
            "credit_preflight_receipt": {"path": "credit.json"},
            "credit_floor_usd": 1.0,
        },
        "job_plan": {"base_seed": 7},
        "failure_policy": {
            "retry_transient_model_attempts": 2,
            "continue_on_job_error": True,
        },
        "concurrency_policy": {"ramp_workers": [4, 8, 16, 32], "maximum_workers": 32},
    }
    lock_payload = {
        "schema_version": "test",
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }
    lock_path = _write_json(tmp_path / "execution_lock.json", lock_payload)
    monkeypatch.setattr(execution, "validate_execution_lock_payload", lambda _value: None)
    monkeypatch.setattr(execution, "build_execution_definition", lambda **_kwargs: definition)

    with pytest.raises(
        execution.ContractLifecycleError, match="may contain only NAMESPACE_LOCK"
    ):
        execution.verify_execution_lock(lock_path=lock_path)

    verified = execution.verify_execution_lock_envelope(lock_path=lock_path)
    assert verified.definition == definition
