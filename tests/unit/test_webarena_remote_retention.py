from __future__ import annotations

from pathlib import Path
import json

import pytest

from evidence_system.adapters import webarena_remote_retention as retention
from evidence_system.core.hashing import sha256_file, sha256_object


def _job() -> dict[str, object]:
    return {
        "artifact_retention_mode": retention.RETENTION_MODE,
        "result_namespace": "remote-canary",
        "phase": "preflight",
        "domain": "webarena_verified",
        "job_id": "job-a",
        "record_slot_id": "slot-a",
        "agent_id": "Agent A",
        "execution_target": {"server_id": "server-a"},
    }


def test_prepare_preserves_partial_remote_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retention, "PERSISTENT_RESULTS_ROOT", tmp_path)
    job = _job()
    root = retention._expected_adapter_root(job)
    root.mkdir(parents=True)
    (root / "partial.log").write_text("keep me\n", encoding="utf-8")

    prepared = retention.prepare_slot(job=job, adapter_root=root)

    assert prepared["status"] == "prepared"
    assert prepared["action"] == "preserved_partial_then_created"
    assert prepared["remote_directory_deleted"] is False
    preserved = list(root.parent.glob("adapter.preserved-*"))
    assert len(preserved) == 1
    assert preserved[0].joinpath("partial.log").read_text(encoding="utf-8") == "keep me\n"
    preservation = prepared["partial_preservation"]
    assert preservation["status"] == "pass"
    assert preservation["preserved_directory_name"] == preserved[0].name
    assert preservation["file_count"] == 1
    assert preservation["total_size_bytes"] == len(b"keep me\n")
    assert len(preservation["tree_sha256"]) == 64
    assert preservation["remote_directory_deleted"] is False
    assert preservation["secret_material_recorded"] is False
    on_disk = json.loads(
        (root / "logs" / "partial_preservation_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    assert on_disk == preservation


def test_prepare_rejects_unsafe_partial_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retention, "PERSISTENT_RESULTS_ROOT", tmp_path)
    job = _job()
    root = retention._expected_adapter_root(job)
    root.mkdir(parents=True)
    target = root / "target.log"
    target.write_text("keep me\n", encoding="utf-8")
    (root / "unsafe-link").symlink_to(target)

    with pytest.raises(retention.RemoteRetentionError, match="non-regular"):
        retention.prepare_slot(job=job, adapter_root=root)

    assert root.is_dir()
    assert list(root.parent.glob("adapter.preserved-*")) == []


def test_verify_reports_terminal_worker_failure_without_exposing_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retention, "PERSISTENT_RESULTS_ROOT", tmp_path)
    job = _job()
    root = retention._expected_adapter_root(job)
    summary = root / "native_run" / "run_summary.json"
    summary.parent.mkdir(parents=True)
    summary.write_text(
        json.dumps(
            {
                "status": "error",
                "error_type": "HarSanitizationError",
                "error_message": "Playwright trace ZIP member exceeds the size limit",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    observed = retention.verify_slot(job=job, adapter_root=root)

    assert observed["state"] == "in_progress"
    assert observed["terminal_failure_observed"] is True
    assert observed["terminal_failure_code"] == (
        "playwright_trace_security_scan_failed"
    )
    assert observed["run_summary_sha256"] == sha256_file(summary)
    assert "error_message" not in observed


def test_verify_reports_completed_unsealed_runtime_without_exposing_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retention, "PERSISTENT_RESULTS_ROOT", tmp_path)
    job = _job()
    root = retention._expected_adapter_root(job)
    summary = root / "native_run" / "run_summary.json"
    summary.parent.mkdir(parents=True)
    summary.write_text('{"status":"completed","secret":"not-forwarded"}\n', encoding="utf-8")

    observed = retention.verify_slot(job=job, adapter_root=root)

    assert observed["state"] == "in_progress"
    assert observed["runtime_completed_unsealed"] is True
    assert observed["run_summary_sha256"] == sha256_file(summary)
    assert "secret" not in observed


@pytest.mark.parametrize(
    ("message", "expected"),
    (
        ("OpenRouter HTTP 402: insufficient credit", "credential_or_billing_failure"),
        ("OpenRouter HTTP 429: rate limit", "openrouter_rate_limited"),
        ("response content missing", "openrouter_empty_response"),
        ("auto_login renewal failed", "official_auto_login_failed"),
        (
            "'Page' object has no attribute 'client'",
            "playwright_page_client_incompatible",
        ),
    ),
)
def test_public_error_codes_preserve_bounded_root_cause(
    message: str, expected: str
) -> None:
    assert retention._public_error_code(RuntimeError(message)) == expected


def test_verify_rehashes_every_manifest_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retention, "PERSISTENT_RESULTS_ROOT", tmp_path)
    job = _job()
    root = retention._expected_adapter_root(job)
    native = root / "native_run"
    logs = root / "logs"
    native.mkdir(parents=True)
    logs.mkdir()
    artifact = native / "run_summary.json"
    artifact.write_text('{"status":"completed"}\n', encoding="utf-8")
    (logs / "worker.log").write_text("complete\n", encoding="utf-8")
    inventory = retention._inventory(root)
    binding = sha256_object(job)
    manifest = {
        "schema_version": retention.MANIFEST_SCHEMA,
        "status": "pass",
        "job_binding_sha256": binding,
        "record_slot_id": "slot-a",
        "artifact_retention_mode": retention.RETENTION_MODE,
        "persistent_adapter_root": str(root),
        "file_count": len(inventory),
        "total_size_bytes": sum(item["size_bytes"] for item in inventory),
        "inventory_sha256": sha256_object(inventory),
        "files": inventory,
        "remote_directory_cleanup_performed": False,
        "full_evidence_synced_to_controller": False,
    }
    retention._write_json(root / "remote_artifact_manifest.json", manifest)
    security = {
        "schema_version": retention.SECURITY_SCHEMA,
        "status": "pass",
        "job_binding_sha256": binding,
        "scan": {"finding_count": 0, "gold_finding_count": 0},
    }
    retention._write_json(root / "remote_security_acceptance.json", security)
    evaluator = {
        "schema_version": retention.EVALUATOR_SCHEMA,
        "status": "pass",
        "job_binding_sha256": binding,
    }
    retention._write_json(root / "remote_evaluator_receipt.json", evaluator)
    slot = {
        "schema_version": retention.SLOT_SCHEMA,
        "status": "pass",
        "job_binding_sha256": binding,
        "record_slot_id": "slot-a",
        "server_id": "server-a",
        "artifact_retention_mode": retention.RETENTION_MODE,
        "persistent_adapter_root": str(root),
        "remote_artifact_manifest_sha256": sha256_file(root / "remote_artifact_manifest.json"),
        "remote_security_acceptance_sha256": sha256_file(root / "remote_security_acceptance.json"),
        "remote_evaluator_receipt_sha256": sha256_file(root / "remote_evaluator_receipt.json"),
    }
    retention._write_json(root / "remote_slot_acceptance.json", slot)

    assert retention.verify_slot(job=job, adapter_root=root)["state"] == "canonical_reusable"
    artifact.write_text('{"status":"tampered"}\n', encoding="utf-8")
    with pytest.raises(retention.RemoteRetentionError, match="hash or size changed"):
        retention.verify_slot(job=job, adapter_root=root)
