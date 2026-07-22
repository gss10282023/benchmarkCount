"""Independent, fail-closed finalization of the completed 24-slot pilot.

This module never executes a benchmark slot.  It consumes the immutable pilot
namespace only after execution, re-derives the canonical 24-job schedule,
reuses the strict run-control audit, and writes controller-owned acceptance
receipts.  Re-running it over unchanged inputs is deterministic and idempotent.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
import zipfile

from evidence_system.adapters.runtime import job_result_relative_dir
from evidence_system.adapters.webarena_har_sanitization import (
    CONTEXT_CREDENTIAL_KEYS,
    COOKIE_CONTAINER_KEYS,
    HEADER_CONTAINER_KEYS,
    HarSanitizationError,
    OPAQUE_PAYLOAD_KEYS,
    REDACTION_MARKER,
    SENSITIVE_HEADER_NAMES,
    MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES,
    MAX_TRACE_TEXT_MEMBER_UNCOMPRESSED_BYTES,
    MAX_TRACE_TOTAL_UNCOMPRESSED_BYTES,
    TRACE_STREAM_CHUNK_BYTES,
    _is_trace_text_member,
    load_and_validate_network_sanitization_receipt,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator.webarena_verified_full import (
    EXPECTED_AGENT_IDS,
    EXPECTED_ROUTES,
)
from evidence_system.orchestrator.webarena_verified_pilot_execution import (
    EXPECTED_PILOT_JOBS_SHA256,
    PILOT_RESULT_NAMESPACE,
    PilotSchedulePlan,
    build_pilot_schedule,
    validate_canonical_pilot_schedule,
)
from evidence_system.orchestrator.webarena_verified_run_control import (
    MonitorSnapshot,
    load_materialized_full_plan,
    monitor_namespace,
)
from evidence_system.webarena_openrouter_capacity import (
    validate_openrouter_capacity_acceptance_file,
)


STEP20_ROOT = Path("experiments/step20/webarena_verified")
DEFAULT_PILOT_ACCEPTANCE = STEP20_ROOT / "pilot_acceptance.json"
DEFAULT_SECURITY_ACCEPTANCE = STEP20_ROOT / "pilot_runtime_security_acceptance.json"
DEFAULT_BUDGET_ACCEPTANCE = STEP20_ROOT / "pilot_cost_runtime_storage_acceptance.json"
DEFAULT_BUDGET_POLICY = STEP20_ROOT / "pilot_budget_policy.json"
DEFAULT_STORAGE_READINESS = STEP20_ROOT / "storage_readiness_acceptance.json"
DEFAULT_CAPACITY_ACCEPTANCE = STEP20_ROOT / "openrouter_capacity_acceptance.json"
DEFAULT_FINALIZATION_ACCEPTANCE = STEP20_ROOT / "pilot_finalization_acceptance.json"
DEFAULT_AGGREGATE = STEP20_ROOT / "acceptance.json"
DEFAULT_PILOT_MANIFEST = STEP20_ROOT / "pilot_manifest.json"
PACKETS_ROOT = Path("experiments/case_packets/webarena_verified")

PILOT_ARTIFACT_KEYS = (
    "structured_final_response",
    "network_har",
    "network_har_sanitization",
    "playwright_trace",
    "native_evaluator_input",
    "native_evaluator_output",
    "raw_run",
    "artifact_manifest",
    "model_calls",
    "reset_receipt",
)
PILOT_GATE_NAMES = (
    "all_24_slots_completed",
    "all_reset_receipts_present",
    "all_har_artifacts_present",
    "all_network_sanitization_receipts_present",
    "all_trace_artifacts_present",
    "all_native_evaluator_io_present",
    "all_raw_runs_present",
    "all_artifact_manifests_present",
    "all_model_call_records_present",
    "structured_final_json_valid",
    "paired_seed_exact",
    "counterbalanced_order_exact",
    "schema_hash_pointer_failures_zero",
    "expected_fallback_zero",
    "active_secret_cookie_credential_leakage_zero",
    "gold_expected_leakage_zero",
)
SECRET_PATTERNS = (
    ("openrouter_key", re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}")),
    ("bearer_credential", re.compile(r"(?i)\bauthorization\s*[:=]\s*bearer\s+\S+")),
    (
        "cookie_header",
        re.compile(
            r"(?i)\b(?:set-cookie|cookie)\s*[:=]\s*"
            r"(?P<value>[^\s\\\"']+=[^\s\\\"']*)"
        ),
    ),
)
SENSITIVE_KEYS = set(SENSITIVE_HEADER_NAMES)
GOLD_KEYS = {
    "answer_key",
    "eval",
    "evaluator",
    "expected_answer",
    "expected",
    "expected_response",
    "gold",
    "gold_answer",
    "reference_answer",
    "evaluator_private",
}


class PilotFinalizationError(RuntimeError):
    """Raised without writing pass receipts when pilot evidence is incomplete."""


def finalize_completed_pilot(
    *,
    active_secret: str | None,
    rebuild_aggregate: bool = True,
) -> dict[str, Any]:
    """Finalize an already-completed namespace; never launch a pilot slot."""

    full = load_materialized_full_plan()
    pilot = build_pilot_schedule(full)
    schedule = validate_canonical_pilot_schedule(pilot)
    observed = monitor_namespace(mode="pilot", write_outputs=True)
    _validate_snapshot(pilot, observed)
    pilot_receipt, metrics = _build_pilot_receipt(
        pilot,
        observed,
        roots=_default_artifact_root,
        active_secret=active_secret,
        canonical_schedule=schedule,
    )
    outputs: dict[str, dict[str, Any]] = {}
    pilot_output = _write_receipt(DEFAULT_PILOT_ACCEPTANCE, pilot_receipt)
    outputs["pilot_acceptance"] = pilot_output
    security_receipt = _build_security_receipt(
        pilot_receipt, pilot_acceptance=pilot_output
    )
    security_output = _write_receipt(DEFAULT_SECURITY_ACCEPTANCE, security_receipt)
    outputs["runtime_security"] = security_output
    budget_receipt, storage_receipt = _build_budget_and_storage_receipts(
        metrics=metrics,
        pilot_receipt=pilot_receipt,
        pilot_acceptance=pilot_output,
        security_acceptance=security_output,
    )
    budget_output = _write_receipt(DEFAULT_BUDGET_ACCEPTANCE, budget_receipt)
    outputs["cost_runtime_storage"] = budget_output
    storage_receipt["pilot_cost_runtime_storage_acceptance"] = budget_output
    outputs["storage_readiness"] = _write_receipt(
        DEFAULT_STORAGE_READINESS, storage_receipt
    )
    aggregate = _rebuild_aggregate() if rebuild_aggregate else None
    if aggregate is not None:
        outputs["step20_aggregate"] = aggregate
    formal_ready = bool(
        aggregate and _load_object(resolve_repo_path(DEFAULT_AGGREGATE)).get(
            "formal_2436_launch_eligible"
        )
        is True
    )
    final = {
        "schema_version": "webarena_verified_pilot_finalization_acceptance/v1",
        "status": "pass" if formal_ready else "blocked",
        "pilot_evidence_status": "pass",
        "formal_2436_launch_eligible": formal_ready,
        "canonical_schedule": schedule,
        "outputs": outputs,
        "gates": {
            "canonical_24_jobs_exact": True,
            "run_control_all_24_reusable": True,
            "pilot_artifact_acceptance_pass": pilot_receipt["status"] == "pass",
            "runtime_security_acceptance_pass": security_receipt["status"] == "pass",
            "cost_runtime_storage_acceptance_pass": budget_receipt["status"] == "pass",
            "storage_projection_acceptance_pass": storage_receipt["status"] == "pass",
            "step20_aggregate_formal_launch_pass": formal_ready,
        },
        "paid_calls_made_by_finalizer": 0,
        "dotenv_read_by_finalizer": False,
        "secret_values_or_hashes_recorded": False,
    }
    path = _write_receipt(DEFAULT_FINALIZATION_ACCEPTANCE, final)
    final["finalization_acceptance"] = path
    return final


def _validate_snapshot(
    plan: PilotSchedulePlan, snapshot: MonitorSnapshot
) -> None:
    expected = tuple(dict(job) for job in plan.jobs)
    if (
        len(snapshot.jobs) != 24
        or tuple(snapshot.jobs) != expected
        or sha256_object(snapshot.jobs) != EXPECTED_PILOT_JOBS_SHA256
    ):
        raise PilotFinalizationError(
            "run-control snapshot is not the canonical 24-job pilot schedule"
        )
    if len(snapshot.audits) != 24:
        raise PilotFinalizationError("run-control did not return exactly 24 slot audits")
    expected_slots = [str(job["record_slot_id"]) for job in expected]
    if [audit.record_slot_id for audit in snapshot.audits] != expected_slots:
        raise PilotFinalizationError("run-control audit order/identity changed")
    not_reusable = [
        audit.record_slot_id for audit in snapshot.audits if not audit.reusable
    ]
    if not_reusable:
        raise PilotFinalizationError(
            f"pilot has {len(not_reusable)} non-reusable slots; first={not_reusable[0]}"
        )
    progress = dict(snapshot.progress)
    binding = dict(progress.get("schedule_binding") or {})
    circuit = dict(progress.get("circuit_breaker") or {})
    counts = dict(progress.get("counts") or {})
    if (
        progress.get("schema_version")
        != "webarena_verified_case_monitor_progress/v1"
        or progress.get("result_namespace") != PILOT_RESULT_NAMESPACE
        or binding.get("kind") != "canonical_pilot_schedule_index"
        or binding.get("job_count") != 24
        or binding.get("jobs_sha256") != EXPECTED_PILOT_JOBS_SHA256
        or counts.get("expected") != 24
        or counts.get("canonical_reusable") != 24
        or circuit.get("tripped") is not False
    ):
        raise PilotFinalizationError("pilot progress/circuit binding is not complete")


def _build_pilot_receipt(
    plan: PilotSchedulePlan,
    snapshot: MonitorSnapshot,
    *,
    roots: Callable[[Mapping[str, Any]], Path],
    active_secret: str | None,
    canonical_schedule: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(active_secret, str) or not active_secret:
        raise PilotFinalizationError(
            "active secret must be supplied in memory for exact-match scanning"
        )
    manifest_path = _regular_file(DEFAULT_PILOT_MANIFEST, "pilot manifest")
    _require_sidecar(manifest_path, "pilot manifest")
    manifest = _load_object(manifest_path)
    expected_manifest_slots = [
        dict(item)
        for item in manifest.get("record_slots") or []
        if isinstance(item, Mapping)
    ]
    if len(expected_manifest_slots) != 24:
        raise PilotFinalizationError("pilot manifest does not contain 24 slots")

    rows: list[dict[str, Any]] = []
    slot_metrics: list[dict[str, Any]] = []
    scan_paths: list[Path] = []
    agent_inputs: list[Path] = []
    for job, expected_manifest_slot, audit in zip(
        plan.jobs, expected_manifest_slots, snapshot.audits, strict=True
    ):
        if audit.record_slot_id != job["record_slot_id"] or not audit.reusable:
            raise PilotFinalizationError("slot audit changed during receipt construction")
        root = roots(job).resolve()
        if roots is _default_artifact_root:
            namespace_root = resolve_repo_path(
                Path("results/namespaces") / PILOT_RESULT_NAMESPACE
            ).resolve()
            if not root.is_relative_to(namespace_root):
                raise PilotFinalizationError("pilot artifact root escaped its namespace")
        task_id = int(job["task_id"])
        native = root / "native_run"
        task_root = native / str(task_id)
        paths = {
            "structured_final_response": task_root / "agent_response.json",
            "network_har": task_root / "network.har",
            "network_har_sanitization": task_root
            / "network_har_sanitization.json",
            "playwright_trace": native / "traces" / f"{task_id}.zip",
            "native_evaluator_input": native / "native_evaluator_input.json",
            "native_evaluator_output": native / "native_evaluator_output.json",
            "raw_run": root / "raw_run.json",
            "artifact_manifest": root / "artifact_manifest.json",
            "model_calls": root / "llm_calls" / "calls.jsonl",
            "reset_receipt": native / "reset_receipt.json",
        }
        if set(paths) != set(PILOT_ARTIFACT_KEYS):
            raise AssertionError("internal pilot artifact mapping changed")
        descriptors = {
            name: _artifact_descriptor(path, label=f"{job['record_slot_id']} {name}")
            for name, path in paths.items()
        }
        for name in (
            "structured_final_response",
            "native_evaluator_input",
            "native_evaluator_output",
            "network_har_sanitization",
            "raw_run",
            "artifact_manifest",
            "reset_receipt",
        ):
            _load_object(paths[name])
        try:
            har = json.loads(paths["network_har"].read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PilotFinalizationError(
                f"invalid HAR JSON for {job['record_slot_id']}"
            ) from exc
        if not isinstance(har, Mapping):
            raise PilotFinalizationError(
                f"HAR is not an object for {job['record_slot_id']}"
            )
        try:
            load_and_validate_network_sanitization_receipt(
                paths["network_har_sanitization"],
                har_path=paths["network_har"],
                trace_path=paths["playwright_trace"],
            )
        except HarSanitizationError as exc:
            raise PilotFinalizationError(
                f"invalid network sanitization receipt for {job['record_slot_id']}"
            ) from exc
        calls = _load_model_calls(paths["model_calls"], job=job)
        call_cost = sum(_extract_call_cost(call) for call in calls)
        raw = _load_object(paths["raw_run"])
        duration = raw.get("duration_seconds")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise PilotFinalizationError(
                f"raw duration is unavailable for {job['record_slot_id']}"
            )
        if float(duration) < 0:
            raise PilotFinalizationError("pilot duration cannot be negative")
        if (
            expected_manifest_slot.get("record_slot_id") != job["record_slot_id"]
            or int(expected_manifest_slot.get("task_id", -1)) != task_id
            or expected_manifest_slot.get("agent_id") != job["agent_id"]
            or expected_manifest_slot.get("model") != job["requested_model"]
            or expected_manifest_slot.get("server_id")
            != dict(job["execution_target"])["server_id"]
            or int(expected_manifest_slot.get("seed", -1)) != int(job["seed"])
        ):
            raise PilotFinalizationError("pilot manifest/job identity mismatch")
        rows.append(
            {
                "record_slot_id": job["record_slot_id"],
                "task_id": task_id,
                "agent_id": job["agent_id"],
                "model": job["requested_model"],
                "server_id": dict(job["execution_target"])["server_id"],
                "seed": int(job["seed"]),
                "status": "completed",
                "artifacts": descriptors,
            }
        )
        total_bytes = sum(
            path.stat().st_size
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        )
        slot_metrics.append(
            {
                "record_slot_id": job["record_slot_id"],
                "agent_id": job["agent_id"],
                "server_id": dict(job["execution_target"])["server_id"],
                "cost_usd": call_cost,
                "runtime_seconds": float(duration),
                "storage_bytes": total_bytes,
                "model_call_count": len(calls),
            }
        )
        scan_paths.extend(
            path
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        )
        agent_inputs.append(
            resolve_repo_path(PACKETS_ROOT / str(task_id) / "agent_input.json")
        )

    security = _scan_runtime_security(
        scan_paths=scan_paths,
        agent_inputs=agent_inputs,
        active_secret=active_secret,
    )
    if security["finding_count"] or security["gold_finding_count"]:
        raise PilotFinalizationError("pilot runtime security/gold scan found leakage")
    per_agent = dict(Counter(str(row["agent_id"]) for row in rows))
    if per_agent != {agent: 8 for agent in EXPECTED_AGENT_IDS}:
        raise PilotFinalizationError("pilot agent counts are not exactly 8/8/8")
    gates = {name: True for name in PILOT_GATE_NAMES}
    receipt = {
        "schema_version": "webarena_verified_pilot_acceptance/v1",
        "status": "pass",
        "result_namespace": PILOT_RESULT_NAMESPACE,
        "canonical_pilot_jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        "canonical_schedule": dict(canonical_schedule),
        "counts": {
            "expected_record_slots": 24,
            "completed_record_slots": 24,
            "per_agent": per_agent,
            "fallback_contracts": 0,
            "schema_hash_pointer_failures": 0,
            "model_calls": sum(item["model_call_count"] for item in slot_metrics),
            "runtime_security_findings": 0,
            "gold_expected_findings": 0,
        },
        "record_slots": rows,
        "runtime_security_scan": security,
        "gates": gates,
        "paid_calls_made_by_finalizer": 0,
        "dotenv_read_by_finalizer": False,
        "secret_values_or_hashes_recorded": False,
    }
    return receipt, {"slots": slot_metrics, "security": security}


def _build_security_receipt(
    pilot_receipt: Mapping[str, Any],
    *,
    pilot_acceptance: Mapping[str, Any],
) -> dict[str, Any]:
    security = dict(pilot_receipt["runtime_security_scan"])
    ok = (
        security.get("finding_count") == 0
        and security.get("gold_finding_count") == 0
        and security.get("active_secret_exact_match_scan_performed") is True
    )
    return {
        "schema_version": "webarena_verified_pilot_runtime_security_acceptance/v1",
        "status": "pass" if ok else "fail",
        "result_namespace": PILOT_RESULT_NAMESPACE,
        "pilot_jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        "pilot_acceptance": dict(pilot_acceptance),
        "scan": security,
        "gates": {
            "active_secret_exact_match_zero": ok,
            "credential_pattern_findings_zero": ok,
            "cookie_and_authorization_findings_zero": ok,
            "model_visible_gold_expected_findings_zero": ok,
        },
        "credential_values_or_hashes_recorded": False,
        "dotenv_read": False,
    }


def _build_budget_and_storage_receipts(
    *,
    metrics: Mapping[str, Any],
    pilot_receipt: Mapping[str, Any],
    pilot_acceptance: Mapping[str, Any],
    security_acceptance: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    del pilot_receipt
    policy_path = _regular_file(DEFAULT_BUDGET_POLICY, "pilot budget policy")
    _require_sidecar(policy_path, "pilot budget policy")
    policy = _load_object(policy_path)
    if (
        policy.get("schema_version")
        != "webarena_verified_pilot_budget_policy/v1"
        or policy.get("status") != "frozen"
        or policy.get("policy_frozen_before_paid_pilot") is not True
    ):
        raise PilotFinalizationError("pilot budget policy is not frozen")
    slots = [dict(item) for item in metrics.get("slots") or []]
    if len(slots) != 24:
        raise PilotFinalizationError("budget input does not account for 24 slots")
    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for slot in slots:
        by_agent[str(slot["agent_id"])].append(slot)
    if {key: len(value) for key, value in by_agent.items()} != {
        agent: 8 for agent in EXPECTED_AGENT_IDS
    }:
        raise PilotFinalizationError("budget per-agent slot counts changed")

    cost_multiplier = _positive_number(
        policy.get("cost_runtime_projection_multiplier"), "cost projection multiplier"
    )
    storage_multiplier = _positive_number(
        policy.get("storage_projection_multiplier"), "storage projection multiplier"
    )
    full_scale = 812 / 8
    cost_by_agent = {
        agent: round(sum(float(item["cost_usd"]) for item in by_agent[agent]), 8)
        for agent in EXPECTED_AGENT_IDS
    }
    runtime_by_agent = {
        agent: round(
            sum(float(item["runtime_seconds"]) for item in by_agent[agent]), 6
        )
        for agent in EXPECTED_AGENT_IDS
    }
    storage_by_agent = {
        agent: sum(int(item["storage_bytes"]) for item in by_agent[agent])
        for agent in EXPECTED_AGENT_IDS
    }
    projected_cost_by_agent = {
        agent: round(cost_by_agent[agent] * full_scale * cost_multiplier, 8)
        for agent in EXPECTED_AGENT_IDS
    }
    projected_runtime_by_agent = {
        agent: round(runtime_by_agent[agent] * full_scale * cost_multiplier, 6)
        for agent in EXPECTED_AGENT_IDS
    }
    projected_storage_by_agent = {
        agent: math.ceil(storage_by_agent[agent] * full_scale * storage_multiplier)
        for agent in EXPECTED_AGENT_IDS
    }
    actual_cost = round(sum(cost_by_agent.values()), 8)
    projected_cost = round(sum(projected_cost_by_agent.values()), 8)
    actual_cost_ok = actual_cost <= _positive_number(
        policy.get("pilot_max_actual_cost_usd"), "pilot cost ceiling"
    )
    actual_runtime_ok = max(runtime_by_agent.values()) <= _positive_number(
        policy.get("pilot_max_lane_runtime_seconds"), "pilot runtime ceiling"
    )
    projected_cost_ok = projected_cost <= _positive_number(
        policy.get("full_max_projected_cost_usd"), "full cost ceiling"
    )
    projected_runtime_ok = max(projected_runtime_by_agent.values()) <= _positive_number(
        policy.get("full_max_projected_lane_runtime_seconds"),
        "full runtime ceiling",
    )

    storage_path = _regular_file(DEFAULT_STORAGE_READINESS, "storage readiness")
    _require_sidecar(storage_path, "storage readiness")
    storage = _load_object(storage_path)
    free = dict(storage.get("free_bytes_by_machine") or {})
    reserve = int(
        _positive_number(
            policy.get("storage_reserve_bytes_per_host"), "storage reserve"
        )
    )
    per_host_projection: dict[str, dict[str, Any]] = {}
    storage_ok = True
    for agent in EXPECTED_AGENT_IDS:
        server_id = str(EXPECTED_ROUTES[agent]["server_id"])
        available = int(free.get(server_id) or 0)
        projected = projected_storage_by_agent[agent]
        fits = available >= projected + reserve
        storage_ok = storage_ok and fits
        per_host_projection[server_id] = {
            "agent_id": agent,
            "pilot_measured_bytes": storage_by_agent[agent],
            "projected_full_bytes_with_safety_multiplier": projected,
            "reserved_free_bytes": reserve,
            "measured_available_bytes": available,
            "projection_plus_reserve_fits": fits,
        }

    capacity = _capacity_gate(
        projected_cost_usd=projected_cost,
        safety_factor=_positive_number(
            policy.get("openrouter_remaining_credit_safety_factor"),
            "OpenRouter credit safety factor",
        ),
    )
    gates = {
        "all_24_slots_accounted": True,
        "actual_cost_within_written_budget": actual_cost_ok and projected_cost_ok,
        "actual_runtime_within_written_budget": (
            actual_runtime_ok and projected_runtime_ok
        ),
        "pilot_storage_measured": sum(storage_by_agent.values()) > 0,
        "full_2436_storage_projected": storage_ok,
        "retention_policy_written": isinstance(policy.get("retention_policy"), Mapping),
        "openrouter_remaining_credit_safety_margin_pass": capacity["status"]
        == "pass",
    }
    budget = {
        "schema_version": "webarena_verified_pilot_cost_runtime_storage_acceptance/v1",
        "status": "pass" if all(gates.values()) else "blocked",
        "pilot_jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        "pilot_acceptance": dict(pilot_acceptance),
        "runtime_security_acceptance": dict(security_acceptance),
        "budget_policy": {
            "path": _display_path(policy_path),
            "sha256": sha256_file(policy_path),
        },
        "counts": {"pilot_slots": 24, "full_projected_slots": 2436},
        "actual": {
            "cost_usd": actual_cost,
            "cost_usd_by_agent": cost_by_agent,
            "runtime_seconds_by_agent": runtime_by_agent,
            "storage_bytes_by_agent": storage_by_agent,
        },
        "projection": {
            "method": "per_agent_8_to_812_with_frozen_safety_multiplier",
            "full_cost_usd": projected_cost,
            "full_cost_usd_by_agent": projected_cost_by_agent,
            "full_lane_runtime_seconds_by_agent": projected_runtime_by_agent,
            "full_storage_bytes_by_agent": projected_storage_by_agent,
            "storage_by_server": per_host_projection,
        },
        "openrouter_capacity": capacity,
        "retention_policy": dict(policy.get("retention_policy") or {}),
        "gates": gates,
        "credential_material_recorded": False,
        "credential_value_hash_recorded": False,
        "response_body_recorded": False,
        "dotenv_read": False,
    }
    updated_storage = dict(storage)
    updated_storage.update(
        {
            "status": "pass" if storage_ok else "fail",
            "pilot_storage_projection_complete": True,
            "full_run_storage_projection_complete": storage_ok,
            "formal_full_run_readiness_status": (
                "pass" if storage_ok else "fail_projection_exceeds_capacity"
            ),
            "blocks_full_2436_launch": not storage_ok,
            "reason": (
                None
                if storage_ok
                else "projected full artifacts plus frozen reserve exceed capacity"
            ),
            "pilot_storage_measurement": {
                "slot_count": 24,
                "total_bytes": sum(storage_by_agent.values()),
                "by_agent": storage_by_agent,
            },
            "full_run_storage_projection": {
                "slot_count": 2436,
                "safety_multiplier": storage_multiplier,
                "by_server": per_host_projection,
                "all_hosts_fit_with_reserve": storage_ok,
            },
            "budget_policy_path": _display_path(policy_path),
            "budget_policy_sha256": sha256_file(policy_path),
            "secret_material_recorded": False,
        }
    )
    return budget, updated_storage


def _capacity_gate(*, projected_cost_usd: float, safety_factor: float) -> dict[str, Any]:
    path = resolve_repo_path(DEFAULT_CAPACITY_ACCEPTANCE)
    required = round(projected_cost_usd * safety_factor, 8)
    if not path.is_file():
        return {
            "status": "pending",
            "receipt_path": _display_path(path),
            "receipt_sha256": None,
            "projected_full_cost_usd": projected_cost_usd,
            "required_remaining_usd_with_safety_margin": required,
            "limit_remaining_usd": None,
            "secret_material_recorded": False,
        }
    try:
        payload = validate_openrouter_capacity_acceptance_file(path)
    except (OSError, RuntimeError, ValueError) as exc:
        raise PilotFinalizationError(
            f"OpenRouter capacity receipt is invalid: {type(exc).__name__}"
        ) from exc
    remaining = payload.get("limit_remaining")
    explicit_cap_ok = (
        payload.get("status") == "pass"
        and payload.get("provider_limit_mode") == "explicit_cap"
        and isinstance(remaining, (int, float))
        and not isinstance(remaining, bool)
        and float(remaining) >= required
    )
    unlimited_waiver_ok = (
        payload.get("status") == "pass"
        and payload.get("provider_limit_mode")
        == "unlimited_no_provider_cap"
        and payload.get("credit_floor_proof_status")
        == "waived_by_user_provider_balance_unavailable"
        and payload.get("credit_floor_waiver_reason")
        == "provider_unlimited_key_exposes_no_limit_remaining_balance"
        and payload.get("unlimited_key_waiver_authorized") is True
        and remaining is None
    )
    ok = explicit_cap_ok or unlimited_waiver_ok
    return {
        "status": "pass" if ok else "fail",
        "receipt_path": _display_path(path),
        "receipt_sha256": sha256_file(path),
        "projected_full_cost_usd": projected_cost_usd,
        "required_remaining_usd_with_safety_margin": required,
        "limit_remaining_usd": float(remaining) if isinstance(remaining, (int, float)) else None,
        "provider_limit_mode": payload.get("provider_limit_mode"),
        "capacity_basis": (
            "verified_provider_key_remaining_credit"
            if explicit_cap_ok
            else "provider_unlimited_key_user_waiver"
            if unlimited_waiver_ok
            else "unverified"
        ),
        "remaining_credit_safety_margin_verified": explicit_cap_ok,
        "unlimited_provider_key_waiver_applied": unlimited_waiver_ok,
        "secret_material_recorded": False,
    }


def _scan_runtime_security(
    *,
    scan_paths: Sequence[Path],
    agent_inputs: Sequence[Path],
    active_secret: str,
) -> dict[str, Any]:
    findings: set[tuple[str, str]] = set()
    gold_findings: set[tuple[str, str]] = set()
    scanned: set[Path] = set()
    exact_matches = 0
    for raw_path in scan_paths:
        path = raw_path.resolve()
        if path in scanned or not path.is_file() or path.name == ".env":
            continue
        scanned.add(path)
        if path.suffix.lower() == ".zip":
            zip_findings, zip_gold, zip_exact = _scan_zip_security(
                path, active_secret=active_secret
            )
            findings.update(zip_findings)
            gold_findings.update(zip_gold)
            exact_matches += zip_exact
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        count = data.count(active_secret.encode("utf-8"))
        if count:
            exact_matches += count
            findings.add((_display_path(path), "active_secret_exact_match"))
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        label = _display_path(path)
        for finding_type in _text_secret_finding_types(text):
            findings.add((label, finding_type))
        if path.suffix == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            for key_path in _sensitive_key_paths(payload):
                findings.add((label, f"sensitive_json_key:{key_path}"))
        elif path.name == "calls.jsonl":
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    call = json.loads(line)
                except json.JSONDecodeError:
                    findings.add((label, "invalid_model_call_json"))
                    continue
                for key_path in _gold_key_paths(call):
                    gold_findings.add((label, f"model_call_gold_key:{key_path}"))

    expected_agent_input_fields = {
        "task_id",
        "intent_template_id",
        "intent",
        "sites",
        "start_urls",
    }
    for path in sorted(set(item.resolve() for item in agent_inputs)):
        payload = _load_object(_regular_file(path, "agent input"))
        label = _display_path(path)
        if set(payload) != expected_agent_input_fields:
            gold_findings.add((label, "unexpected_agent_input_field_set"))
        for key_path in _gold_key_paths(payload):
            gold_findings.add((label, f"agent_input_gold_key:{key_path}"))
    return {
        "schema_version": "webarena_verified_pilot_runtime_security_scan/v1",
        "status": "pass" if not findings and not gold_findings else "fail",
        "scanned_file_count": len(scanned),
        "model_visible_agent_input_count": len(set(agent_inputs)),
        "finding_count": len(findings),
        "gold_finding_count": len(gold_findings),
        "finding_metadata": [
            {"path": path, "finding_type": kind}
            for path, kind in sorted(findings)
        ],
        "gold_finding_metadata": [
            {"path": path, "finding_type": kind}
            for path, kind in sorted(gold_findings)
        ],
        "active_secret_exact_match_scan_performed": True,
        "active_secret_exact_match_count": exact_matches,
        "dotenv_scanned": False,
        "secret_values_or_hashes_recorded": False,
    }


def _scan_zip_security(
    path: Path, *, active_secret: str
) -> tuple[set[tuple[str, str]], set[tuple[str, str]], int]:
    findings: set[tuple[str, str]] = set()
    gold_findings: set[tuple[str, str]] = set()
    exact_matches = 0
    max_entries = 5000
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise PilotFinalizationError(f"invalid Playwright trace ZIP: {path}") from exc
    with archive:
        entries = archive.infolist()
        if len(entries) > max_entries:
            raise PilotFinalizationError("Playwright trace ZIP has too many entries")
        total = 0
        for entry in entries:
            if entry.is_dir():
                continue
            if entry.flag_bits & 0x1:
                raise PilotFinalizationError("encrypted trace ZIP entry is forbidden")
            total += int(entry.file_size)
            # Keep this classification identical to the sanitizer. Playwright
            # puts arbitrary response bodies below ``resources/``; a response
            # body ending in ``.json`` is opaque evidence, not a structured
            # trace document. Treating it as the latter imposed the smaller
            # 50 MB cap and created false-positive JSON-key findings.
            structured = _is_trace_text_member(entry.filename)
            entry_limit = (
                MAX_TRACE_TEXT_MEMBER_UNCOMPRESSED_BYTES
                if structured
                else MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES
            )
            if (
                entry.file_size > entry_limit
                or total > MAX_TRACE_TOTAL_UNCOMPRESSED_BYTES
            ):
                raise PilotFinalizationError("Playwright trace ZIP exceeds scan limits")
            label = f"{_display_path(path)}!/{entry.filename}"
            if not structured:
                opaque_findings, opaque_exact = _scan_opaque_zip_entry(
                    archive,
                    entry,
                    active_secret=active_secret,
                    label=label,
                )
                findings.update(opaque_findings)
                exact_matches += opaque_exact
                continue
            try:
                data = archive.read(entry)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                raise PilotFinalizationError("Playwright trace ZIP entry is unreadable") from exc
            exact = data.count(active_secret.encode("utf-8"))
            if exact:
                exact_matches += exact
                findings.add((label, "active_secret_exact_match"))
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            for finding_type in _text_secret_finding_types(text):
                findings.add((label, finding_type))
            if entry.filename.lower().endswith(".json"):
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                for key_path in _sensitive_key_paths(payload):
                    findings.add((label, f"sensitive_json_key:{key_path}"))
            elif entry.filename.lower().endswith(
                (".jsonl", ".trace", ".network")
            ):
                for line in text.splitlines():
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    for key_path in _sensitive_key_paths(payload):
                        findings.add((label, f"sensitive_json_key:{key_path}"))
                    for key_path in _gold_key_paths(payload):
                        gold_findings.add((label, f"trace_gold_key:{key_path}"))
    return findings, gold_findings, exact_matches


def _scan_opaque_zip_entry(
    archive: zipfile.ZipFile,
    entry: zipfile.ZipInfo,
    *,
    active_secret: str,
    label: str,
) -> tuple[set[tuple[str, str]], int]:
    """Stream-scan large opaque trace members within the v6 sanitizer bounds."""

    findings: set[tuple[str, str]] = set()
    exact_matches = 0
    secret = active_secret.encode("utf-8")
    overlap_bytes = max(65_536, len(secret) - 1)
    tail = b""
    try:
        with archive.open(entry) as stream:
            while True:
                chunk = stream.read(TRACE_STREAM_CHUNK_BYTES)
                if not chunk:
                    break
                combined = tail + chunk
                exact_matches += combined.count(secret) - tail.count(secret)
                try:
                    text = combined.decode("utf-8")
                except UnicodeDecodeError:
                    text = combined.decode("utf-8", errors="ignore")
                for finding_type in _text_secret_finding_types(text):
                    findings.add((label, finding_type))
                tail = combined[-overlap_bytes:]
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise PilotFinalizationError("Playwright trace ZIP entry is unreadable") from exc
    if exact_matches:
        findings.add((label, "active_secret_exact_match"))
    return findings, exact_matches


def _sensitive_key_paths(
    value: Any,
    *,
    prefix: tuple[str, ...] = (),
    context: str | None = None,
) -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        lower_keys = {str(key).lower(): key for key in value}
        if context == "headers":
            name_key = lower_keys.get("name")
            value_key = lower_keys.get("value")
            if name_key is not None and value_key is not None:
                header_name = str(value[name_key])
                if (
                    header_name.lower().replace("_", "-") in SENSITIVE_KEYS
                    and _contains_sensitive_value(value[value_key])
                ):
                    findings.append(
                        ".".join((*prefix, f"header[{header_name}]"))
                    )
            for raw_key, child in value.items():
                key = str(raw_key)
                if raw_key in {name_key, value_key}:
                    continue
                if (
                    key.lower().replace("_", "-") in SENSITIVE_KEYS
                    and _contains_sensitive_value(child)
                ):
                    findings.append(".".join((*prefix, key)))
            return findings
        if context == "cookies":
            value_key = lower_keys.get("value")
            if value_key is not None:
                if _contains_sensitive_value(value[value_key]):
                    cookie_name = str(value.get(lower_keys.get("name"), "cookie"))
                    findings.append(
                        ".".join((*prefix, f"cookie[{cookie_name}]"))
                    )
            else:
                for raw_key, child in value.items():
                    if _contains_sensitive_value(child):
                        findings.append(
                            ".".join((*prefix, f"cookie[{raw_key}]"))
                        )
            return findings
        if context == "context_credentials":
            for raw_key, child in value.items():
                key = str(raw_key)
                if (
                    key.lower() in CONTEXT_CREDENTIAL_KEYS
                    and _contains_sensitive_value(child)
                ):
                    findings.append(".".join((*prefix, key)))
            return findings
        if context == "storage_local_storage":
            name_key = lower_keys.get("name")
            value_key = lower_keys.get("value")
            if (
                name_key is not None
                and value_key is not None
                and _is_sensitive_storage_name(value[name_key])
                and _contains_sensitive_value(value[value_key])
            ):
                findings.append(
                    ".".join((*prefix, f"localStorage[{value[name_key]}]"))
                )
            return findings
        for raw_key, child in value.items():
            key = str(raw_key)
            child_prefix = (*prefix, key)
            lowered = key.lower()
            normalized = lowered.replace("_", "-")
            if lowered in OPAQUE_PAYLOAD_KEYS:
                continue
            if lowered in HEADER_CONTAINER_KEYS:
                findings.extend(
                    _sensitive_key_paths(
                        child, prefix=child_prefix, context="headers"
                    )
                )
            elif lowered in COOKIE_CONTAINER_KEYS:
                findings.extend(
                    _sensitive_key_paths(
                        child, prefix=child_prefix, context="cookies"
                    )
                )
            elif lowered == "storagestate":
                findings.extend(
                    _sensitive_key_paths(
                        child, prefix=child_prefix, context="storage_state"
                    )
                )
            elif context == "storage_state" and lowered == "origins":
                findings.extend(
                    _sensitive_key_paths(
                        child, prefix=child_prefix, context="storage_origins"
                    )
                )
            elif context == "storage_origins" and lowered == "localstorage":
                findings.extend(
                    _sensitive_key_paths(
                        child,
                        prefix=child_prefix,
                        context="storage_local_storage",
                    )
                )
            elif lowered in {"httpcredentials", "proxy"}:
                findings.extend(
                    _sensitive_key_paths(
                        child,
                        prefix=child_prefix,
                        context="context_credentials",
                    )
                )
            elif (
                normalized in SENSITIVE_KEYS
                and normalized not in {"cookie", "set-cookie"}
                and _contains_sensitive_value(child)
            ):
                findings.append(".".join(child_prefix))
            else:
                findings.extend(
                    _sensitive_key_paths(child, prefix=child_prefix)
                )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(
                _sensitive_key_paths(
                    child,
                    prefix=(*prefix, f"[{index}]"),
                    context=context,
                )
            )
    return findings


def _is_sensitive_storage_name(value: Any) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(value).lower())
    return any(
        marker in normalized
        for marker in (
            "apikey",
            "auth",
            "credential",
            "csrf",
            "password",
            "secret",
            "session",
            "token",
            "xsrf",
        )
    )


def _gold_key_paths(value: Any, *, prefix: tuple[str, ...] = ()) -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            child_prefix = (*prefix, key)
            if key.lower() in GOLD_KEYS:
                findings.append(".".join(child_prefix))
            findings.extend(_gold_key_paths(child, prefix=child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_gold_key_paths(child, prefix=(*prefix, f"[{index}]")))
    return findings


def _contains_sensitive_value(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, str) and value.strip().lower() in {
        REDACTION_MARKER,
        "redacted",
        "removed",
        "controller_only",
        "none",
        "not_set",
    }:
        return False
    return True


def _text_secret_finding_types(text: str) -> set[str]:
    findings: set[str] = set()
    for finding_type, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            captured = match.groupdict().get("value")
            if captured == REDACTION_MARKER:
                continue
            findings.add(finding_type)
            break
    return findings


def _load_model_calls(path: Path, *, job: Mapping[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise PilotFinalizationError("model-call log cannot be read") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PilotFinalizationError(
                f"model-call log line {line_number} is invalid JSON"
            ) from exc
        if not isinstance(payload, Mapping):
            raise PilotFinalizationError("model-call record is not an object")
        call = dict(payload)
        model = str(call.get("model") or call.get("model_version") or "")
        requested = str(job["requested_model"])
        if (
            call.get("record_slot_id") != job["record_slot_id"]
            or not (model == requested or model.endswith("/" + requested))
        ):
            raise PilotFinalizationError("model-call record/job binding changed")
        calls.append(call)
    if not calls:
        raise PilotFinalizationError(f"no model calls for {job['record_slot_id']}")
    return calls


def _extract_call_cost(call: Mapping[str, Any]) -> float:
    candidates = (
        _dig(call, "response_metadata", "provider_response", "cost"),
        _dig(call, "response_metadata", "cost"),
        _dig(call, "cost", "total_cost_usd"),
        _dig(call, "cost", "amount"),
        call.get("total_cost_usd"),
    )
    for value in candidates:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            cost = float(value)
            if cost < 0:
                raise PilotFinalizationError("model-call cost cannot be negative")
            return cost
    raise PilotFinalizationError("provider cost is missing from a model-call record")


def _dig(value: Mapping[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _artifact_descriptor(path: Path, *, label: str) -> dict[str, Any]:
    regular = _regular_file(path, label)
    size = regular.stat().st_size
    if size <= 0:
        raise PilotFinalizationError(f"{label} is empty")
    return {
        "path": _display_path(regular),
        "sha256": sha256_file(regular),
        "size_bytes": size,
    }


def _default_artifact_root(job: Mapping[str, Any]) -> Path:
    return resolve_repo_path(job_result_relative_dir(dict(job)) / "adapter")


def _positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PilotFinalizationError(f"{label} is not numeric")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise PilotFinalizationError(f"{label} must be finite and positive")
    return number


def _regular_file(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path)
    if not resolved.is_file() or resolved.is_symlink():
        raise PilotFinalizationError(f"{label} is missing or unsafe: {resolved}")
    return resolved


def _load_object(path: Path) -> dict[str, Any]:
    try:
        payload = load_json_or_yaml(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise PilotFinalizationError(f"invalid JSON object: {path}") from exc
    if not isinstance(payload, Mapping):
        raise PilotFinalizationError(f"not a JSON object: {path}")
    return dict(payload)


def _require_sidecar(path: Path, label: str) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    if not sidecar.is_file() or sidecar.is_symlink():
        raise PilotFinalizationError(f"{label} sidecar is missing")
    parts = sidecar.read_text(encoding="utf-8").strip().split()
    if not parts or parts[0] != sha256_file(path):
        raise PilotFinalizationError(f"{label} sidecar is stale")


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _write_receipt(path_value: str | Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary_fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.tmp-", dir=str(path.parent)
    )
    try:
        with os.fdopen(temporary_fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    os.chmod(path, 0o600)
    digest = sha256_file(path)
    sidecar = path.with_name(path.name + ".sha256")
    sidecar.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    os.chmod(sidecar, 0o600)
    return {
        "path": _display_path(path),
        "sha256": digest,
        "size_bytes": path.stat().st_size,
    }


def _rebuild_aggregate() -> dict[str, Any]:
    script = repo_root() / "scripts" / "build_webarena_verified_step20_acceptance.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--openrouter-credential-status",
            "valid",
        ],
        cwd=repo_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise PilotFinalizationError(
            f"Step20 aggregate rebuild failed with exit {completed.returncode}"
        )
    path = _regular_file(DEFAULT_AGGREGATE, "Step20 aggregate")
    _require_sidecar(path, "Step20 aggregate")
    return {
        "path": _display_path(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
