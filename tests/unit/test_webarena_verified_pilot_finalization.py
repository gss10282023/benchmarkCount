from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from evidence_system.adapters.webarena_har_sanitization import (
    sanitize_network_artifacts_before_evaluator,
)
from evidence_system.orchestrator.webarena_verified_pilot_execution import (
    EXPECTED_PILOT_JOBS_SHA256,
    PILOT_RESULT_NAMESPACE,
    build_pilot_schedule,
)
from evidence_system.orchestrator.webarena_verified_pilot_finalization import (
    PilotFinalizationError,
    _build_budget_and_storage_receipts,
    _build_pilot_receipt,
    _scan_runtime_security,
    _validate_snapshot,
    _write_receipt,
)
from evidence_system.orchestrator.webarena_verified_run_control import (
    MonitorSnapshot,
    SlotAudit,
    load_materialized_full_plan,
)
from evidence_system.webarena_openrouter_capacity import (
    build_openrouter_capacity_acceptance,
    write_openrouter_capacity_acceptance,
)


SECRET = "sk-or-v1-synthetic-finalizer-secret-never-real"


class _CapacityTransport:
    def get_current_key(self, *, api_key: str, timeout_seconds: int):
        del api_key, timeout_seconds
        return 200, {
            "data": {"limit": 1000.0, "usage": 100.0, "limit_remaining": 900.0}
        }


class _UnlimitedCapacityTransport:
    def get_current_key(self, *, api_key: str, timeout_seconds: int):
        del api_key, timeout_seconds
        return 200, {
            "data": {"limit": None, "usage": 100.0, "limit_remaining": None}
        }


@pytest.fixture(scope="module")
def pilot_plan():
    return build_pilot_schedule(load_materialized_full_plan())


def _complete_snapshot(plan) -> MonitorSnapshot:
    audits = tuple(
        SlotAudit(
            record_slot_id=str(job["record_slot_id"]),
            state="canonical_reusable",
            reusable=True,
            issues=(),
            artifact_root="synthetic",
        )
        for job in plan.jobs
    )
    return MonitorSnapshot(
        jobs=tuple(plan.jobs),
        audits=audits,
        issues=(),
        progress={
            "schema_version": "webarena_verified_case_monitor_progress/v1",
            "result_namespace": PILOT_RESULT_NAMESPACE,
            "schedule_binding": {
                "kind": "canonical_pilot_schedule_index",
                "job_count": 24,
                "jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
            },
            "counts": {"expected": 24, "canonical_reusable": 24},
            "circuit_breaker": {"tripped": False},
        },
    )


def test_snapshot_requires_all_24_canonical_reusable_slots(pilot_plan) -> None:
    snapshot = _complete_snapshot(pilot_plan)
    _validate_snapshot(pilot_plan, snapshot)
    broken = MonitorSnapshot(
        jobs=snapshot.jobs,
        audits=(
            SlotAudit(
                snapshot.audits[0].record_slot_id,
                "settled_invalid",
                False,
                (),
                "synthetic",
            ),
            *snapshot.audits[1:],
        ),
        issues=(),
        progress=snapshot.progress,
    )
    with pytest.raises(PilotFinalizationError, match="non-reusable"):
        _validate_snapshot(pilot_plan, broken)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _synthetic_roots(tmp_path: Path, plan) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for job in plan.jobs:
        slot = str(job["record_slot_id"])
        task = int(job["task_id"])
        root = tmp_path / slot / "adapter"
        native = root / "native_run"
        task_root = native / str(task)
        for path in (
            task_root / "agent_response.json",
            native / "native_evaluator_input.json",
            native / "native_evaluator_output.json",
            root / "artifact_manifest.json",
            native / "reset_receipt.json",
        ):
            _write_json(path, {"status": "synthetic"})
        _write_json(root / "raw_run.json", {"duration_seconds": 10.0})
        har = task_root / "network.har"
        _write_json(
            har,
            {
                "log": {
                    "version": "1.2",
                    "creator": {"name": "Playwright", "version": "1.56.0"},
                    "entries": [
                        {
                            "request": {"headers": [], "cookies": []},
                            "response": {
                                "headers": [],
                                "cookies": [],
                                "content": {"text": "synthetic"},
                            },
                        }
                    ],
                }
            },
        )
        trace = native / "traces" / f"{task}.zip"
        trace.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(trace, "w") as archive:
            archive.writestr("trace.trace", '{"type":"event"}\n')
            archive.writestr("trace.network", '{"type":"resource"}\n')
        sanitize_network_artifacts_before_evaluator(
            har_path=har,
            trace_path=trace,
        )
        calls = root / "llm_calls" / "calls.jsonl"
        calls.parent.mkdir(parents=True, exist_ok=True)
        calls.write_text(
            json.dumps(
                {
                    "record_slot_id": slot,
                    "model": job["requested_model"],
                    "response_metadata": {"provider_response": {"cost": 0.1}},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        roots[slot] = root
    return roots


def test_artifact_builder_emits_exact_24_by_9_and_real_metrics(
    tmp_path: Path, pilot_plan
) -> None:
    roots = _synthetic_roots(tmp_path, pilot_plan)
    receipt, metrics = _build_pilot_receipt(
        pilot_plan,
        _complete_snapshot(pilot_plan),
        roots=lambda job: roots[str(job["record_slot_id"])],
        active_secret=SECRET,
        canonical_schedule={
            "status": "pass",
            "job_count": 24,
            "jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        },
    )
    assert receipt["status"] == "pass"
    assert len(receipt["record_slots"]) == 24
    assert all(len(row["artifacts"]) == 10 for row in receipt["record_slots"])
    assert receipt["counts"]["per_agent"] == {
        "Agent A": 8,
        "Agent B": 8,
        "Agent C": 8,
    }
    assert len(metrics["slots"]) == 24
    assert sum(row["cost_usd"] for row in metrics["slots"]) == pytest.approx(2.4)


def test_trace_zip_scanner_detects_cookie_csrf_gold_and_active_secret(
    tmp_path: Path,
) -> None:
    trace = tmp_path / "trace.zip"
    with zipfile.ZipFile(trace, "w") as archive:
        archive.writestr(
            "trace.trace",
            json.dumps(
                {
                    "headers": [
                        {"name": "Cookie", "value": "session=private"},
                        {"name": "x-csrf-token", "value": "csrf-private"},
                    ],
                    "gold_answer": "private",
                    "body": SECRET,
                }
            )
            + "\n",
        )
    agent_input = tmp_path / "agent_input.json"
    _write_json(
        agent_input,
        {
            "task_id": 1,
            "intent_template_id": "x",
            "intent": "x",
            "sites": [],
            "start_urls": [],
        },
    )
    result = _scan_runtime_security(
        scan_paths=[trace], agent_inputs=[agent_input], active_secret=SECRET
    )
    kinds = {item["finding_type"] for item in result["finding_metadata"]}
    assert "active_secret_exact_match" in kinds
    assert any("header[Cookie]" in kind for kind in kinds)
    assert any("header[x-csrf-token]" in kind for kind in kinds)
    assert result["gold_finding_count"] == 1


def test_runtime_security_accepts_only_the_canonical_redaction_marker(
    tmp_path: Path,
) -> None:
    credential = "sanitized-cookie-secret-987654"
    har = tmp_path / "network.har"
    _write_json(
        har,
        {
            "log": {
                "version": "1.2",
                "creator": {"name": "Playwright", "version": "1.56.0"},
                "entries": [
                    {
                        "request": {
                            "headers": [{"name": "Cookie", "value": credential}],
                            "cookies": [{"name": "sid", "value": credential}],
                            "headersText": f"Cookie: {credential}\r\n",
                        },
                        "response": {
                            "headers": [
                                {"name": "Set-Cookie", "value": credential}
                            ],
                            "cookies": [{"name": "sid", "value": credential}],
                            "headersText": f"Set-Cookie: {credential}\r\n",
                            "content": {"text": "safe evidence"},
                        },
                    }
                ],
            }
        },
    )
    event = {
        "type": "resource-snapshot",
        "snapshot": {
            "request": {
                "method": "GET",
                "url": "http://example.test",
                "headers": [{"name": "Cookie", "value": credential}],
                "cookies": [{"name": "sid", "value": credential}],
            },
            "response": {
                "status": 200,
                "headers": [{"name": "Set-Cookie", "value": credential}],
                "cookies": [{"name": "sid", "value": credential}],
            },
        },
    }
    trace = tmp_path / "trace.zip"
    with zipfile.ZipFile(trace, "w") as archive:
        archive.writestr("trace.trace", json.dumps(event) + "\n")
        archive.writestr("trace.network", json.dumps(event) + "\n")
        archive.writestr(
            "metadata.json",
            json.dumps(
                {
                    "businessBody": {
                        "authorization": "ordinary business field",
                        "cookies": {"display": "ordinary business cookie"},
                    }
                }
            ),
        )
    receipt = tmp_path / "network_har_sanitization.json"
    sanitize_network_artifacts_before_evaluator(
        har_path=har,
        trace_path=trace,
        receipt_path=receipt,
    )
    agent_input = tmp_path / "agent_input.json"
    _write_json(
        agent_input,
        {
            "task_id": 1,
            "intent_template_id": "x",
            "intent": "x",
            "sites": [],
            "start_urls": [],
        },
    )

    result = _scan_runtime_security(
        scan_paths=[har, trace, receipt],
        agent_inputs=[agent_input],
        active_secret=SECRET,
    )

    assert result["status"] == "pass"
    assert result["finding_count"] == 0
    assert result["gold_finding_count"] == 0

    with zipfile.ZipFile(trace, "r") as source:
        members = {name: source.read(name) for name in source.namelist()}
    trace_event = json.loads(members["trace.trace"])
    trace_event["snapshot"]["request"]["headers"][0]["value"] = (
        "tampered-live-cookie"
    )
    members["trace.trace"] = (json.dumps(trace_event) + "\n").encode()
    with zipfile.ZipFile(trace, "w") as target:
        for name, data in members.items():
            target.writestr(name, data)

    tampered = _scan_runtime_security(
        scan_paths=[har, trace, receipt],
        agent_inputs=[agent_input],
        active_secret=SECRET,
    )
    assert tampered["status"] == "fail"
    assert any(
        "header[Cookie]" in item["finding_type"]
        for item in tampered["finding_metadata"]
    )


def test_runtime_security_stream_scans_large_opaque_trace_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import evidence_system.orchestrator.webarena_verified_pilot_finalization as module

    monkeypatch.setattr(module, "MAX_TRACE_TEXT_MEMBER_UNCOMPRESSED_BYTES", 64)
    monkeypatch.setattr(module, "MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES", 1024)
    monkeypatch.setattr(module, "MAX_TRACE_TOTAL_UNCOMPRESSED_BYTES", 4096)
    monkeypatch.setattr(module, "TRACE_STREAM_CHUNK_BYTES", 16)
    trace = tmp_path / "trace.zip"
    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("trace.trace", '{"type":"event"}\n')
        archive.writestr("trace.network", '{"type":"event"}\n')
        archive.writestr("resources/large.bin", b"x" * 128)
    agent_input = tmp_path / "agent_input.json"
    _write_json(
        agent_input,
        {
            "task_id": 1,
            "intent_template_id": "x",
            "intent": "x",
            "sites": [],
            "start_urls": [],
        },
    )

    clean = _scan_runtime_security(
        scan_paths=[trace], agent_inputs=[agent_input], active_secret=SECRET
    )
    assert clean["status"] == "pass"

    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("trace.trace", '{"type":"event"}\n')
        archive.writestr("trace.network", '{"type":"event"}\n')
        archive.writestr("resources/large.bin", b"x" * 11 + SECRET.encode() + b"x" * 80)
    leaked = _scan_runtime_security(
        scan_paths=[trace], agent_inputs=[agent_input], active_secret=SECRET
    )
    assert leaked["status"] == "fail"
    assert leaked["active_secret_exact_match_count"] == 1


def test_runtime_security_treats_json_resources_as_opaque_trace_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import evidence_system.orchestrator.webarena_verified_pilot_finalization as module

    monkeypatch.setattr(module, "MAX_TRACE_TEXT_MEMBER_UNCOMPRESSED_BYTES", 64)
    monkeypatch.setattr(module, "MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES", 1024)
    monkeypatch.setattr(module, "MAX_TRACE_TOTAL_UNCOMPRESSED_BYTES", 4096)
    monkeypatch.setattr(module, "TRACE_STREAM_CHUNK_BYTES", 16)
    trace = tmp_path / "trace.zip"
    agent_input = tmp_path / "agent_input.json"
    _write_json(
        agent_input,
        {
            "task_id": 1,
            "intent_template_id": "x",
            "intent": "x",
            "sites": [],
            "start_urls": [],
        },
    )

    # A JSON-suffixed response body may be larger than a structured trace
    # member. It must use the sanitizer's streaming opaque-member path.
    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("trace.trace", '{"type":"event"}\n')
        archive.writestr("trace.network", '{"type":"event"}\n')
        archive.writestr("resources/large-response.json", b"x" * 128)
    clean = _scan_runtime_security(
        scan_paths=[trace], agent_inputs=[agent_input], active_secret=SECRET
    )
    assert clean["status"] == "pass"

    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("trace.trace", '{"type":"event"}\n')
        archive.writestr("trace.network", '{"type":"event"}\n')
        archive.writestr(
            "resources/large-response.json", b"x" * 11 + SECRET.encode() + b"x" * 80
        )
    leaked = _scan_runtime_security(
        scan_paths=[trace], agent_inputs=[agent_input], active_secret=SECRET
    )
    assert leaked["status"] == "fail"
    assert leaked["active_secret_exact_match_count"] == 1


def test_budget_projection_is_pending_without_capacity_then_passes_with_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import evidence_system.orchestrator.webarena_verified_pilot_finalization as module

    slots = []
    for agent, server in (
        ("Agent A", "webarena-gpt54-ord"),
        ("Agent B", "webarena-claude47-ord"),
        ("Agent C", "webarena-deepseek-v4pro-ord"),
    ):
        for index in range(8):
            slots.append(
                {
                    "record_slot_id": f"{agent}-{index}",
                    "agent_id": agent,
                    "server_id": server,
                    "cost_usd": 0.1,
                    "runtime_seconds": 10.0,
                    "storage_bytes": 1000,
                    "model_call_count": 1,
                }
            )
    capacity = tmp_path / "capacity.json"
    monkeypatch.setattr(module, "DEFAULT_CAPACITY_ACCEPTANCE", capacity)
    budget, storage = _build_budget_and_storage_receipts(
        metrics={"slots": slots},
        pilot_receipt={},
        pilot_acceptance={"path": "pilot.json", "sha256": "a" * 64},
        security_acceptance={"path": "security.json", "sha256": "b" * 64},
    )
    assert budget["status"] == "blocked"
    assert budget["openrouter_capacity"]["status"] == "pending"
    assert storage["full_run_storage_projection_complete"] is True

    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET, transport=_CapacityTransport()
    )
    write_openrouter_capacity_acceptance(capacity, receipt)
    budget, _ = _build_budget_and_storage_receipts(
        metrics={"slots": slots},
        pilot_receipt={},
        pilot_acceptance={"path": "pilot.json", "sha256": "a" * 64},
        security_acceptance={"path": "security.json", "sha256": "b" * 64},
    )
    assert budget["status"] == "pass"
    assert all(budget["gates"].values())


def test_capacity_gate_transparently_accepts_authorized_unlimited_key_waiver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import evidence_system.orchestrator.webarena_verified_pilot_finalization as module

    capacity = tmp_path / "capacity.json"
    monkeypatch.setattr(module, "DEFAULT_CAPACITY_ACCEPTANCE", capacity)
    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=_UnlimitedCapacityTransport(),
        allow_unlimited_key_waiver=True,
    )
    write_openrouter_capacity_acceptance(capacity, receipt)

    gate = module._capacity_gate(
        projected_cost_usd=433.0,
        safety_factor=1.2,
    )

    assert gate["status"] == "pass"
    assert gate["capacity_basis"] == "provider_unlimited_key_user_waiver"
    assert gate["limit_remaining_usd"] is None
    assert gate["remaining_credit_safety_margin_verified"] is False
    assert gate["unlimited_provider_key_waiver_applied"] is True


def test_receipt_writer_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    first = _write_receipt(path, {"schema_version": "synthetic/v1", "status": "pass"})
    second = _write_receipt(path, {"schema_version": "synthetic/v1", "status": "pass"})
    assert first == second
