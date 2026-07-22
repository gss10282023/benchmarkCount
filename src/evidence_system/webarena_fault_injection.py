"""Strict, secret-free fault-injection receipts for WebArena-Verified.

This module deliberately separates fault *observation* from fault execution.
The remote driver may stop a site, force login generation to fail, pass a
known-invalid placeholder credential to an isolated worker process, or feed a
corrupt copy of an evaluator input to the scorer.  Only the normalized facts
defined here are allowed into the public receipt.  Raw stdout, tracebacks,
cookies, storage state, and credentials stay controller-only and are represented
by SHA-256 descriptors.

All four faults are infrastructure faults.  A passing injection therefore
proves that the affected slot is fail-closed as ``INFRA_EXCLUDED`` and its
evidence label is ``UNRESOLVE``; it must never be counted as an agent failure or
fall back to an alternate contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any

from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.webarena_sites import atomic_write_json


FAULT_RECEIPT_SCHEMA = "webarena_verified_fault_injection_receipt/v1"
FAULT_ACCEPTANCE_SCHEMA = "webarena_verified_fault_injection_acceptance/v1"
REMOTE_RAW_EVIDENCE_SCHEMA = "webarena_verified_fault_raw_evidence/v1"
BENCHMARK = "WebArena-Verified"
BENCHMARK_VERSION = "v1.2.3"

FAULT_KINDS = (
    "site_outage",
    "login_failure",
    "invalid_placeholder_api_key",
    "evaluator_error",
)
EXECUTION_MODES = frozenset({"local_simulation", "remote_real"})
ACCEPTANCE_SCOPES = frozenset({"local_harness", "remote_three_host"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MACHINE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# Exact key matches avoid false positives for safe declarations such as
# ``real_secret_loaded: false`` and the fault name ``invalid_placeholder_api_key``.
_FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "api_key",
        "authorization",
        "cookie",
        "cookies",
        "credential",
        "credential_value",
        "openrouter_api_key",
        "password",
        "private_key",
        "secret",
        "secret_value",
        "set-cookie",
        "set_cookie",
        "storage_state",
    }
)
_FORBIDDEN_STRING_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openrouter_key", re.compile(r"sk-or-v1-[A-Za-z0-9_-]{8,}", re.IGNORECASE)),
    ("bearer_authorization", re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE)),
    (
        "private_key_pem",
        re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----", re.IGNORECASE),
    ),
    (
        "serialized_sensitive_field",
        re.compile(
            r"[\"'](?:api_key|authorization|cookie|cookies|credential|"
            r"credential_value|openrouter_api_key|password|private_key|secret|"
            r"secret_value|set-cookie|set_cookie|storage_state)[\"']\s*:",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class FaultDefinition:
    kind: str
    injection_stage: str
    error_code: str
    model_call_started_during_injection: bool
    model_completion_available: bool
    official_evaluator_started: bool
    official_evaluator_result_validated: bool
    recovery_verification_code: str


FAULT_DEFINITIONS: dict[str, FaultDefinition] = {
    "site_outage": FaultDefinition(
        kind="site_outage",
        injection_stage="site_preflight",
        error_code="site_healthcheck_failed",
        model_call_started_during_injection=False,
        model_completion_available=False,
        official_evaluator_started=False,
        official_evaluator_result_validated=False,
        recovery_verification_code="site_recreated_from_pins_and_sentinels_pass",
    ),
    "login_failure": FaultDefinition(
        kind="login_failure",
        injection_stage="authenticated_state_preflight",
        error_code="login_state_generation_failed",
        model_call_started_during_injection=False,
        model_completion_available=False,
        official_evaluator_started=False,
        official_evaluator_result_validated=False,
        recovery_verification_code="fresh_login_state_regenerated_and_deleted",
    ),
    "invalid_placeholder_api_key": FaultDefinition(
        kind="invalid_placeholder_api_key",
        injection_stage="model_transport",
        error_code="provider_authentication_rejected",
        model_call_started_during_injection=True,
        model_completion_available=False,
        official_evaluator_started=False,
        official_evaluator_result_validated=False,
        recovery_verification_code="placeholder_process_isolated_and_destroyed",
    ),
    "evaluator_error": FaultDefinition(
        kind="evaluator_error",
        injection_stage="official_evaluator",
        error_code="official_evaluator_result_unvalidated",
        # The injection reuses a synthetic or already-paid baseline artifact.  It
        # must not make a new model request merely to test scorer failure.
        model_call_started_during_injection=False,
        model_completion_available=True,
        official_evaluator_started=True,
        official_evaluator_result_validated=False,
        recovery_verification_code="corrupt_copy_quarantined_baseline_unchanged",
    ),
}

_SEMANTIC_KEYS = frozenset(
    {
        "fault_observed",
        "error_code",
        "model_call_started_during_injection",
        "model_completion_available",
        "browser_actions_after_fault",
        "official_evaluator_started",
        "official_evaluator_result_validated",
        "execution_status",
        "evidence_label",
        "score_counted",
        "agent_failure_counted",
        "fallback_contract_used",
        "run_quarantined",
    }
)
_RECOVERY_KEYS = frozenset({"attempted", "status", "verification_code"})
_EVIDENCE_KEYS = frozenset(
    {"artifact_kind", "sha256", "controller_only", "relative_reference"}
)
_REMOTE_ATTESTATION_KEYS = frozenset(
    {
        "ssh_host_ed25519_fingerprint",
        "verified_ssh_host_key",
        "controller_machine_id_match",
        "remote_command_executed",
    }
)
_REQUIRED_REMOTE_EVIDENCE_KINDS = frozenset(
    {"fault_observation", "recovery_observation"}
)
_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "receipt_id",
        "benchmark",
        "benchmark_version",
        "execution_mode",
        "machine_id",
        "fault_kind",
        "injection_stage",
        "completed_at",
        "status",
        "expected_semantics",
        "observed_semantics",
        "recovery",
        "remote_attestation",
        "safety",
        "gates",
        "evidence",
        "secret_scan",
        "integrity",
    }
)


class FaultInjectionValidationError(RuntimeError):
    """A fault receipt or its aggregate failed a strict acceptance rule."""


def expected_semantics(kind: str) -> dict[str, Any]:
    """Return the exact terminal semantics required for ``kind``."""

    definition = _fault_definition(kind)
    return {
        "fault_observed": True,
        "error_code": definition.error_code,
        "model_call_started_during_injection": (
            definition.model_call_started_during_injection
        ),
        "model_completion_available": definition.model_completion_available,
        "browser_actions_after_fault": 0,
        "official_evaluator_started": definition.official_evaluator_started,
        "official_evaluator_result_validated": (
            definition.official_evaluator_result_validated
        ),
        "execution_status": "INFRA_EXCLUDED",
        "evidence_label": "UNRESOLVE",
        "score_counted": False,
        "agent_failure_counted": False,
        "fallback_contract_used": False,
        "run_quarantined": True,
    }


def passing_observation(kind: str) -> dict[str, Any]:
    """Create a deterministic test-double observation for the local harness."""

    return expected_semantics(kind)


def passing_recovery(kind: str) -> dict[str, Any]:
    definition = _fault_definition(kind)
    return {
        "attempted": True,
        "status": "pass",
        "verification_code": definition.recovery_verification_code,
    }


def classify_fault_observation(kind: str, facts: Mapping[str, Any]) -> dict[str, Any]:
    """Translate controller-only measured facts into public terminal semantics.

    The caller may retain ``facts`` as the hashed ``fault_observation`` artifact,
    but it must never place the raw mapping in the public receipt.  Exact schemas
    prevent a permissive truthy value from being mistaken for proof.
    """

    raw = dict(facts)
    if kind == "site_outage":
        expected = {
            "probe_kind": "site_status",
            "site_container_stopped": True,
            "sentinel_passed": False,
            "model_worker_started": False,
        }
    elif kind == "login_failure":
        expected = {
            "probe_kind": "official_auto_login",
            "auto_login_exit_nonzero": True,
            "storage_state_created": False,
            "model_worker_started": False,
        }
    elif kind == "invalid_placeholder_api_key":
        if set(raw) != {
            "probe_kind",
            "worker_exit_nonzero",
            "provider_http_status",
            "model_completion_received",
            "credential_scope",
        }:
            raise FaultInjectionValidationError(
                "invalid-key observation fields differ from the locked schema"
            )
        if raw.get("probe_kind") != "openrouter_transport":
            raise FaultInjectionValidationError("invalid-key probe kind mismatch")
        if raw.get("worker_exit_nonzero") is not True:
            raise FaultInjectionValidationError("invalid-key worker did not fail")
        if raw.get("provider_http_status") not in {401, 403}:
            raise FaultInjectionValidationError(
                "invalid-key probe was not rejected as an authentication failure"
            )
        if raw.get("model_completion_received") is not False:
            raise FaultInjectionValidationError(
                "invalid-key probe unexpectedly obtained a model completion"
            )
        if raw.get("credential_scope") != "injected_placeholder_child_only":
            raise FaultInjectionValidationError(
                "invalid-key credential was not isolated to the injected child"
            )
        return expected_semantics(kind)
    elif kind == "evaluator_error":
        expected = {
            "probe_kind": "pinned_official_scorer",
            "scorer_exit_code": 2,
            "scorer_status": "error",
            "official_evaluation_completed": False,
            "integrity_verified": False,
            "mutated_input_is_copy": True,
        }
    else:
        _fault_definition(kind)
        raise AssertionError(kind)  # pragma: no cover
    if raw != expected:
        raise FaultInjectionValidationError(
            f"{kind} observation does not prove the locked fault boundary"
        )
    return expected_semantics(kind)


def classify_recovery_observation(
    kind: str, facts: Mapping[str, Any]
) -> dict[str, Any]:
    """Require exact recovery facts and return the public recovery declaration."""

    raw = dict(facts)
    expected_facts: dict[str, Any]
    if kind == "site_outage":
        expected_facts = {
            "site_recreated_from_pins": True,
            "all_sentinels_passed": True,
        }
    elif kind == "login_failure":
        expected_facts = {
            "fresh_state_regenerated": True,
            "fresh_state_validated": True,
            "sensitive_state_deleted": True,
        }
    elif kind == "invalid_placeholder_api_key":
        expected_facts = {
            "placeholder_child_destroyed": True,
            "parent_environment_unchanged": True,
        }
    elif kind == "evaluator_error":
        expected_facts = {
            "corrupt_copy_quarantined": True,
            "baseline_artifact_hash_unchanged": True,
        }
    else:
        _fault_definition(kind)
        raise AssertionError(kind)  # pragma: no cover
    if raw != expected_facts:
        raise FaultInjectionValidationError(
            f"{kind} recovery facts do not satisfy the locked recovery boundary"
        )
    return passing_recovery(kind)


def local_simulation_facts(kind: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return locked test-double facts; never use these for a remote receipt."""

    if kind == "site_outage":
        return (
            {
                "probe_kind": "site_status",
                "site_container_stopped": True,
                "sentinel_passed": False,
                "model_worker_started": False,
            },
            {"site_recreated_from_pins": True, "all_sentinels_passed": True},
        )
    if kind == "login_failure":
        return (
            {
                "probe_kind": "official_auto_login",
                "auto_login_exit_nonzero": True,
                "storage_state_created": False,
                "model_worker_started": False,
            },
            {
                "fresh_state_regenerated": True,
                "fresh_state_validated": True,
                "sensitive_state_deleted": True,
            },
        )
    if kind == "invalid_placeholder_api_key":
        return (
            {
                "probe_kind": "openrouter_transport",
                "worker_exit_nonzero": True,
                "provider_http_status": 401,
                "model_completion_received": False,
                "credential_scope": "injected_placeholder_child_only",
            },
            {
                "placeholder_child_destroyed": True,
                "parent_environment_unchanged": True,
            },
        )
    if kind == "evaluator_error":
        return (
            {
                "probe_kind": "pinned_official_scorer",
                "scorer_exit_code": 2,
                "scorer_status": "error",
                "official_evaluation_completed": False,
                "integrity_verified": False,
                "mutated_input_is_copy": True,
            },
            {
                "corrupt_copy_quarantined": True,
                "baseline_artifact_hash_unchanged": True,
            },
        )
    _fault_definition(kind)
    raise AssertionError(kind)  # pragma: no cover


def build_fault_receipt(
    *,
    machine_id: str,
    kind: str,
    execution_mode: str,
    observed_semantics: Mapping[str, Any],
    recovery: Mapping[str, Any],
    remote_attestation: Mapping[str, Any] | None = None,
    evidence: Sequence[Mapping[str, Any]] = (),
    completed_at: str | None = None,
    real_dotenv_read: bool = False,
    real_secret_loaded: bool = False,
    paid_model_calls: int = 0,
) -> dict[str, Any]:
    """Normalize one injection into a hash-bound, secret-free receipt.

    No credential value is accepted by this API.  The invalid-key injection is
    identified only by a public placeholder *identifier*; the placeholder bytes
    themselves are intentionally absent from the receipt.
    """

    definition = _fault_definition(kind)
    _validate_machine_id(machine_id)
    if execution_mode not in EXECUTION_MODES:
        raise FaultInjectionValidationError(
            f"unsupported execution_mode: {execution_mode!r}"
        )
    observed = dict(observed_semantics)
    if set(observed) != _SEMANTIC_KEYS:
        raise FaultInjectionValidationError(
            "observed_semantics fields differ from the locked schema"
        )
    recovery_payload = dict(recovery)
    if set(recovery_payload) != _RECOVERY_KEYS:
        raise FaultInjectionValidationError(
            "recovery fields differ from the locked schema"
        )
    evidence_payload = [_normalize_evidence_descriptor(item) for item in evidence]
    attestation = _normalize_remote_attestation(
        remote_attestation,
        execution_mode=execution_mode,
    )
    timestamp = completed_at or _utc_now_iso()
    _validate_timestamp(timestamp)
    if isinstance(paid_model_calls, bool) or not isinstance(paid_model_calls, int):
        raise FaultInjectionValidationError("paid_model_calls must be an integer")

    expected = expected_semantics(kind)
    gates = {
        "fault_observed": observed.get("fault_observed") is True,
        "semantics_exact": observed == expected,
        "fail_closed_infra_excluded": (
            observed.get("execution_status") == "INFRA_EXCLUDED"
            and observed.get("run_quarantined") is True
        ),
        "unresolve_not_agent_failure": (
            observed.get("evidence_label") == "UNRESOLVE"
            and observed.get("agent_failure_counted") is False
            and observed.get("score_counted") is False
        ),
        "fallback_contract_zero": observed.get("fallback_contract_used") is False,
        "recovery_verified": recovery_payload == passing_recovery(kind),
        "real_dotenv_not_read": real_dotenv_read is False,
        "real_secret_not_loaded": real_secret_loaded is False,
        "paid_model_calls_zero": paid_model_calls == 0,
    }
    payload: dict[str, Any] = {
        "schema_version": FAULT_RECEIPT_SCHEMA,
        "receipt_id": f"wv123-fi-{machine_id}-{kind}",
        "benchmark": BENCHMARK,
        "benchmark_version": BENCHMARK_VERSION,
        "execution_mode": execution_mode,
        "machine_id": machine_id,
        "fault_kind": kind,
        "injection_stage": definition.injection_stage,
        "completed_at": timestamp,
        "status": "pass" if all(gates.values()) else "fail",
        "expected_semantics": expected,
        "observed_semantics": observed,
        "recovery": recovery_payload,
        "remote_attestation": attestation,
        "safety": {
            "real_dotenv_read": bool(real_dotenv_read),
            "real_secret_loaded": bool(real_secret_loaded),
            "paid_model_calls": paid_model_calls,
            "placeholder_credential_identifier": (
                "known_invalid_openrouter_placeholder_v1"
                if kind == "invalid_placeholder_api_key"
                else None
            ),
            "placeholder_value_persisted": False,
            "raw_error_text_persisted": False,
        },
        "gates": gates,
        "evidence": evidence_payload,
        "secret_scan": {"status": "pending", "finding_count": None},
    }
    findings = scan_sensitive_material(payload)
    payload["secret_scan"] = {
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
    }
    if findings:
        # Do not return or write a partially sanitized receipt.  Reporting only
        # detector/path metadata in the exception avoids echoing the secret.
        detectors = ", ".join(
            f"{item['detector']}@{item['path']}" for item in findings
        )
        raise FaultInjectionValidationError(
            f"fault receipt contains sensitive material: {detectors}"
        )
    payload["integrity"] = {
        "algorithm": "sha256_canonical_json",
        "core_sha256": sha256_object(payload),
    }
    validate_fault_receipt(payload)
    return payload


def validate_fault_receipt(payload: Mapping[str, Any]) -> None:
    """Raise if a receipt cannot be used as fault-injection evidence."""

    receipt = dict(payload)
    if set(receipt) != _RECEIPT_KEYS:
        raise FaultInjectionValidationError(
            "fault receipt fields differ from the locked schema"
        )
    if receipt.get("schema_version") != FAULT_RECEIPT_SCHEMA:
        raise FaultInjectionValidationError("fault receipt schema version mismatch")
    if receipt.get("benchmark") != BENCHMARK or receipt.get(
        "benchmark_version"
    ) != BENCHMARK_VERSION:
        raise FaultInjectionValidationError("fault receipt benchmark identity mismatch")
    machine_id = str(receipt.get("machine_id") or "")
    _validate_machine_id(machine_id)
    kind = str(receipt.get("fault_kind") or "")
    definition = _fault_definition(kind)
    if receipt.get("receipt_id") != f"wv123-fi-{machine_id}-{kind}":
        raise FaultInjectionValidationError("fault receipt ID mismatch")
    if receipt.get("execution_mode") not in EXECUTION_MODES:
        raise FaultInjectionValidationError("fault receipt execution mode mismatch")
    if receipt.get("injection_stage") != definition.injection_stage:
        raise FaultInjectionValidationError("fault receipt injection stage mismatch")
    _validate_timestamp(str(receipt.get("completed_at") or ""))

    expected = receipt.get("expected_semantics")
    observed = receipt.get("observed_semantics")
    if not isinstance(expected, Mapping) or set(expected) != _SEMANTIC_KEYS:
        raise FaultInjectionValidationError("expected_semantics schema mismatch")
    if dict(expected) != expected_semantics(kind):
        raise FaultInjectionValidationError("expected_semantics changed")
    if not isinstance(observed, Mapping) or set(observed) != _SEMANTIC_KEYS:
        raise FaultInjectionValidationError("observed_semantics schema mismatch")

    recovery = receipt.get("recovery")
    if not isinstance(recovery, Mapping) or set(recovery) != _RECOVERY_KEYS:
        raise FaultInjectionValidationError("recovery schema mismatch")
    evidence = receipt.get("evidence")
    if not isinstance(evidence, list):
        raise FaultInjectionValidationError("evidence must be an array")
    for item in evidence:
        _normalize_evidence_descriptor(item)
    _normalize_remote_attestation(
        receipt.get("remote_attestation"),
        execution_mode=str(receipt["execution_mode"]),
    )

    safety = receipt.get("safety")
    expected_safety_keys = {
        "real_dotenv_read",
        "real_secret_loaded",
        "paid_model_calls",
        "placeholder_credential_identifier",
        "placeholder_value_persisted",
        "raw_error_text_persisted",
    }
    if not isinstance(safety, Mapping) or set(safety) != expected_safety_keys:
        raise FaultInjectionValidationError("safety schema mismatch")
    if safety.get("real_dotenv_read") is not False:
        raise FaultInjectionValidationError("fault injection read the real dotenv")
    if safety.get("real_secret_loaded") is not False:
        raise FaultInjectionValidationError("fault injection loaded a real secret")
    if safety.get("paid_model_calls") != 0:
        raise FaultInjectionValidationError("fault injection made a paid model call")
    if safety.get("placeholder_value_persisted") is not False or safety.get(
        "raw_error_text_persisted"
    ) is not False:
        raise FaultInjectionValidationError("fault receipt persisted unsafe raw material")
    expected_placeholder = (
        "known_invalid_openrouter_placeholder_v1"
        if kind == "invalid_placeholder_api_key"
        else None
    )
    if safety.get("placeholder_credential_identifier") != expected_placeholder:
        raise FaultInjectionValidationError("placeholder credential declaration mismatch")

    expected_gates = {
        "fault_observed": observed.get("fault_observed") is True,
        "semantics_exact": dict(observed) == dict(expected),
        "fail_closed_infra_excluded": (
            observed.get("execution_status") == "INFRA_EXCLUDED"
            and observed.get("run_quarantined") is True
        ),
        "unresolve_not_agent_failure": (
            observed.get("evidence_label") == "UNRESOLVE"
            and observed.get("agent_failure_counted") is False
            and observed.get("score_counted") is False
        ),
        "fallback_contract_zero": observed.get("fallback_contract_used") is False,
        "recovery_verified": dict(recovery) == passing_recovery(kind),
        "real_dotenv_not_read": safety.get("real_dotenv_read") is False,
        "real_secret_not_loaded": safety.get("real_secret_loaded") is False,
        "paid_model_calls_zero": safety.get("paid_model_calls") == 0,
    }
    gates = receipt.get("gates")
    if not isinstance(gates, Mapping) or dict(gates) != expected_gates:
        raise FaultInjectionValidationError("fault receipt gates are stale or forged")
    expected_status = "pass" if all(expected_gates.values()) else "fail"
    if receipt.get("status") != expected_status:
        raise FaultInjectionValidationError("fault receipt status disagrees with gates")
    secret_scan = receipt.get("secret_scan")
    if secret_scan != {"status": "pass", "finding_count": 0}:
        raise FaultInjectionValidationError("fault receipt secret scan did not pass")
    if scan_sensitive_material(_without_integrity(receipt)):
        raise FaultInjectionValidationError("fault receipt contains sensitive material")
    integrity = receipt.get("integrity")
    if not isinstance(integrity, Mapping) or set(integrity) != {
        "algorithm",
        "core_sha256",
    }:
        raise FaultInjectionValidationError("fault receipt integrity schema mismatch")
    if integrity.get("algorithm") != "sha256_canonical_json":
        raise FaultInjectionValidationError("fault receipt integrity algorithm mismatch")
    if integrity.get("core_sha256") != sha256_object(_without_integrity(receipt)):
        raise FaultInjectionValidationError("fault receipt integrity hash mismatch")


def write_fault_receipt(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Validate and atomically write one mode-0600 receipt plus hash sidecar."""

    validate_fault_receipt(payload)
    destination = Path(path)
    atomic_write_json(destination, payload)
    _atomic_write_text(
        destination.with_suffix(destination.suffix + ".sha256"),
        f"{sha256_file(destination)}  {destination.name}\n",
    )


def build_local_simulation_receipts(
    *, root: str | Path, completed_at: str | None = None
) -> list[Path]:
    """Materialize four non-production local harness receipts.

    This is deliberately labelled ``local_simulation``.  It validates the
    receipt and aggregation machinery but cannot satisfy the three-host Step-20
    production gate.
    """

    output_root = Path(root)
    paths: list[Path] = []
    timestamp = completed_at or _utc_now_iso()
    for kind in FAULT_KINDS:
        observation_facts, recovery_facts = local_simulation_facts(kind)
        payload = build_fault_receipt(
            machine_id="local-harness",
            kind=kind,
            execution_mode="local_simulation",
            observed_semantics=classify_fault_observation(kind, observation_facts),
            recovery=classify_recovery_observation(kind, recovery_facts),
            completed_at=timestamp,
        )
        path = output_root / "local-harness" / kind / "receipt.json"
        write_fault_receipt(path, payload)
        paths.append(path)
    return paths


def build_fault_acceptance(
    *,
    receipts_root: str | Path,
    scope: str,
    machine_ids: Sequence[str] | None = None,
    ssh_host_fingerprints: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Aggregate an exact local-4 or remote-three-host×4 receipt matrix."""

    if scope not in ACCEPTANCE_SCOPES:
        raise FaultInjectionValidationError(f"unsupported acceptance scope: {scope!r}")
    if scope == "local_harness":
        expected_machines = ("local-harness",)
        expected_mode = "local_simulation"
        expected_fingerprints: dict[str, str] = {}
    else:
        if machine_ids is None or len(tuple(machine_ids)) != 3:
            raise FaultInjectionValidationError(
                "remote_three_host acceptance requires exactly three machine IDs"
            )
        expected_machines = tuple(str(item) for item in machine_ids)
        if len(set(expected_machines)) != 3:
            raise FaultInjectionValidationError("remote machine IDs must be unique")
        for machine_id in expected_machines:
            _validate_machine_id(machine_id)
        expected_mode = "remote_real"
        if ssh_host_fingerprints is None or set(ssh_host_fingerprints) != set(
            expected_machines
        ):
            raise FaultInjectionValidationError(
                "remote_three_host acceptance requires one SSH fingerprint per machine"
            )
        expected_fingerprints = {
            str(machine_id): str(ssh_host_fingerprints[machine_id])
            for machine_id in expected_machines
        }
        if any(
            not fingerprint.startswith("SHA256:")
            for fingerprint in expected_fingerprints.values()
        ):
            raise FaultInjectionValidationError(
                "remote SSH fingerprints must use SHA256 notation"
            )

    root = Path(receipts_root)
    expected_paths = {
        f"{machine_id}/{kind}/receipt.json"
        for machine_id in expected_machines
        for kind in FAULT_KINDS
    }
    observed_paths = (
        {
            path.relative_to(root).as_posix()
            for path in root.rglob("receipt.json")
            if path.is_file()
        }
        if root.is_dir()
        else set()
    )
    blockers: list[str] = []
    missing = sorted(expected_paths - observed_paths)
    extras = sorted(observed_paths - expected_paths)
    if missing:
        blockers.append(f"missing receipts: {', '.join(missing)}")
    if extras:
        blockers.append(f"unexpected receipts: {', '.join(extras)}")

    entries: list[dict[str, Any]] = []
    invalid = 0
    completion_times: list[str] = []
    evidence_hash_failures = 0
    attestation_failures = 0
    for machine_id in expected_machines:
        for kind in FAULT_KINDS:
            relative = f"{machine_id}/{kind}/receipt.json"
            path = root / relative
            if not path.is_file():
                continue
            try:
                raw = path.read_bytes()
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, Mapping):
                    raise FaultInjectionValidationError("receipt is not a JSON object")
                validate_fault_receipt(payload)
                if payload.get("machine_id") != machine_id:
                    raise FaultInjectionValidationError("receipt machine/path mismatch")
                if payload.get("fault_kind") != kind:
                    raise FaultInjectionValidationError("receipt fault/path mismatch")
                if payload.get("execution_mode") != expected_mode:
                    raise FaultInjectionValidationError("receipt execution mode mismatch")
                evidence_verified = _verify_aggregate_evidence(
                    payload,
                    receipts_root=root,
                    require_remote_evidence=scope == "remote_three_host",
                )
                attestation_verified = _verify_aggregate_attestation(
                    payload,
                    expected_fingerprint=expected_fingerprints.get(machine_id),
                    require_remote_attestation=scope == "remote_three_host",
                )
            except (
                OSError,
                UnicodeError,
                json.JSONDecodeError,
                FaultInjectionValidationError,
            ) as exc:
                invalid += 1
                blockers.append(f"{relative}: {type(exc).__name__}")
                continue
            if not evidence_verified:
                evidence_hash_failures += 1
                blockers.append(f"{relative}: evidence hashes or permissions invalid")
            if not attestation_verified:
                attestation_failures += 1
                blockers.append(f"{relative}: remote machine attestation invalid")
            completion_times.append(str(payload["completed_at"]))
            observed = dict(payload["observed_semantics"])
            entries.append(
                {
                    "machine_id": machine_id,
                    "fault_kind": kind,
                    "receipt_path": relative,
                    "receipt_sha256": hashlib.sha256(raw).hexdigest(),
                    "receipt_core_sha256": payload["integrity"]["core_sha256"],
                    "status": payload["status"],
                    "execution_status": observed["execution_status"],
                    "evidence_label": observed["evidence_label"],
                    "score_counted": observed["score_counted"],
                    "agent_failure_counted": observed["agent_failure_counted"],
                    "fallback_contract_used": observed["fallback_contract_used"],
                    "paid_model_calls": payload["safety"]["paid_model_calls"],
                    "secret_scan_status": payload["secret_scan"]["status"],
                    "recovery_status": payload["recovery"]["status"],
                    "evidence_descriptor_count": len(payload["evidence"]),
                    "evidence_hashes_verified": evidence_verified,
                    "remote_attestation_verified": attestation_verified,
                }
            )

    expected_count = len(expected_paths)
    gates = {
        "receipt_matrix_exact": observed_paths == expected_paths,
        "all_receipts_valid": len(entries) == expected_count and invalid == 0,
        "all_fault_kinds_covered_per_machine": all(
            {
                entry["fault_kind"]
                for entry in entries
                if entry["machine_id"] == machine_id
            }
            == set(FAULT_KINDS)
            for machine_id in expected_machines
        ),
        "all_fail_closed_infra_excluded": len(entries) == expected_count
        and all(entry["execution_status"] == "INFRA_EXCLUDED" for entry in entries),
        "all_unresolve_not_agent_failure": len(entries) == expected_count
        and all(
            entry["evidence_label"] == "UNRESOLVE"
            and entry["score_counted"] is False
            and entry["agent_failure_counted"] is False
            for entry in entries
        ),
        "fallback_contracts_zero": len(entries) == expected_count
        and all(entry["fallback_contract_used"] is False for entry in entries),
        "paid_model_calls_zero": len(entries) == expected_count
        and sum(int(entry["paid_model_calls"]) for entry in entries) == 0,
        "all_recovery_checks_pass": len(entries) == expected_count
        and all(entry["recovery_status"] == "pass" for entry in entries),
        "all_public_receipts_secret_free": len(entries) == expected_count
        and all(entry["secret_scan_status"] == "pass" for entry in entries),
        "all_evidence_requirements_verified_for_scope": len(entries)
        == expected_count
        and evidence_hash_failures == 0
        and all(entry["evidence_hashes_verified"] for entry in entries),
        "all_machine_attestations_match_scope": len(entries) == expected_count
        and attestation_failures == 0
        and all(entry["remote_attestation_verified"] for entry in entries),
    }
    if not all(gates.values()) and not blockers:
        blockers.append("one or more fault-injection acceptance gates failed")
    passed = all(gates.values()) and not blockers
    aggregate: dict[str, Any] = {
        "schema_version": FAULT_ACCEPTANCE_SCHEMA,
        "status": "pass" if passed else "blocked",
        "generated_at": max(completion_times) if completion_times else "1970-01-01T00:00:00Z",
        "scope": scope,
        "real_remote_execution": scope == "remote_three_host",
        "local_implementation_gate_satisfied": scope == "local_harness" and passed,
        "formal_step20_fault_gate_satisfied": scope == "remote_three_host" and passed,
        "inputs": {
            "receipts_root": str(root),
            "expected_execution_mode": expected_mode,
        },
        "expected": {
            "machine_ids": list(expected_machines),
            "fault_kinds": list(FAULT_KINDS),
            "receipt_count": expected_count,
        },
        "counts": {
            "expected_receipts": expected_count,
            "observed_receipts": len(observed_paths),
            "validated_receipts": len(entries),
            "invalid_receipts": invalid,
            "evidence_hash_failures": evidence_hash_failures,
            "attestation_failures": attestation_failures,
            "fallback_contracts": sum(
                1 for entry in entries if entry["fallback_contract_used"] is True
            ),
            "score_counted": sum(
                1 for entry in entries if entry["score_counted"] is True
            ),
            "agent_failures_counted": sum(
                1 for entry in entries if entry["agent_failure_counted"] is True
            ),
            "paid_model_calls": sum(
                int(entry["paid_model_calls"]) for entry in entries
            ),
            "blocking_reasons": len(blockers),
        },
        "gates": gates,
        "entries": entries,
        "blocking_reasons": blockers,
    }
    aggregate["integrity"] = {
        "algorithm": "sha256_canonical_json",
        "core_sha256": sha256_object(aggregate),
    }
    return aggregate


def validate_fault_acceptance(payload: Mapping[str, Any]) -> None:
    """Validate an aggregate's self-hash and non-claiming scope flags."""

    aggregate = dict(payload)
    if aggregate.get("schema_version") != FAULT_ACCEPTANCE_SCHEMA:
        raise FaultInjectionValidationError("fault acceptance schema mismatch")
    integrity = aggregate.pop("integrity", None)
    if not isinstance(integrity, Mapping) or integrity.get(
        "algorithm"
    ) != "sha256_canonical_json":
        raise FaultInjectionValidationError("fault acceptance integrity missing")
    if integrity.get("core_sha256") != sha256_object(aggregate):
        raise FaultInjectionValidationError("fault acceptance integrity hash mismatch")
    scope = aggregate.get("scope")
    passed = aggregate.get("status") == "pass"
    gates = aggregate.get("gates")
    if not isinstance(gates, Mapping) or passed is not all(
        value is True for value in gates.values()
    ):
        raise FaultInjectionValidationError("fault acceptance status/gates mismatch")
    counts = aggregate.get("counts")
    if not isinstance(counts, Mapping):
        raise FaultInjectionValidationError("fault acceptance counts missing")
    if passed and any(
        counts.get(key) != 0
        for key in (
            "invalid_receipts",
            "evidence_hash_failures",
            "attestation_failures",
            "fallback_contracts",
            "score_counted",
            "agent_failures_counted",
            "paid_model_calls",
            "blocking_reasons",
        )
    ):
        raise FaultInjectionValidationError("passing fault acceptance has nonzero failures")
    if aggregate.get("formal_step20_fault_gate_satisfied") is not (
        scope == "remote_three_host" and passed
    ):
        raise FaultInjectionValidationError("formal Step-20 gate scope is overstated")
    if aggregate.get("local_implementation_gate_satisfied") is not (
        scope == "local_harness" and passed
    ):
        raise FaultInjectionValidationError("local harness gate scope is inconsistent")
    if scan_sensitive_material(aggregate):
        raise FaultInjectionValidationError("fault acceptance contains sensitive material")


def write_fault_acceptance(path: str | Path, payload: Mapping[str, Any]) -> None:
    validate_fault_acceptance(payload)
    destination = Path(path)
    atomic_write_json(destination, payload)
    _atomic_write_text(
        destination.with_suffix(destination.suffix + ".sha256"),
        f"{sha256_file(destination)}  {destination.name}\n",
    )


def machine_ids_from_infra(path: str | Path) -> tuple[str, str, str]:
    """Read the exact ordered three WebArena VPS machine IDs, never their secrets."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FaultInjectionValidationError("infra config is not readable JSON") from exc
    machines = payload.get("machines") if isinstance(payload, Mapping) else None
    if not isinstance(machines, list):
        raise FaultInjectionValidationError("infra config has no machines array")
    ids = tuple(
        str(machine.get("machine_id") or "")
        for machine in machines
        if isinstance(machine, Mapping) and machine.get("role") == "webarena_vps"
    )
    if len(ids) != 3 or len(set(ids)) != 3:
        raise FaultInjectionValidationError(
            "infra config must define exactly three unique WebArena VPS machines"
        )
    for machine_id in ids:
        _validate_machine_id(machine_id)
    return ids  # type: ignore[return-value]


def machine_targets_from_infra(path: str | Path) -> dict[str, str]:
    """Return the three machine IDs bound to their pinned ED25519 fingerprints."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FaultInjectionValidationError("infra config is not readable JSON") from exc
    machines = payload.get("machines") if isinstance(payload, Mapping) else None
    if not isinstance(machines, list):
        raise FaultInjectionValidationError("infra config has no machines array")
    targets: dict[str, str] = {}
    for machine in machines:
        if not isinstance(machine, Mapping) or machine.get("role") != "webarena_vps":
            continue
        machine_id = str(machine.get("machine_id") or "")
        _validate_machine_id(machine_id)
        fingerprint = str(
            dict(machine.get("site_controller") or {}).get("ssh_host_fingerprint")
            or ""
        )
        if not fingerprint.startswith("SHA256:"):
            raise FaultInjectionValidationError(
                f"WebArena machine {machine_id} has no pinned SSH fingerprint"
            )
        if machine_id in targets:
            raise FaultInjectionValidationError("duplicate WebArena machine ID")
        targets[machine_id] = fingerprint
    if len(targets) != 3:
        raise FaultInjectionValidationError(
            "infra config must define exactly three WebArena VPS targets"
        )
    return targets


def scan_sensitive_material(payload: Any) -> list[dict[str, str]]:
    """Return detector/path metadata without ever returning the matched value."""

    findings: list[dict[str, str]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_text = str(key)
                child_path = f"{path}.{key_text}" if path else key_text
                if key_text.lower() in _FORBIDDEN_PUBLIC_KEYS:
                    findings.append(
                        {"path": child_path, "detector": "forbidden_field_name"}
                    )
                visit(child, child_path)
            return
        if isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
            return
        if isinstance(value, str):
            for detector, pattern in _FORBIDDEN_STRING_PATTERNS:
                if pattern.search(value):
                    findings.append({"path": path, "detector": detector})

    visit(payload, "")
    return findings


def _fault_definition(kind: str) -> FaultDefinition:
    try:
        return FAULT_DEFINITIONS[kind]
    except KeyError as exc:
        raise FaultInjectionValidationError(
            f"unsupported fault kind: {kind!r}"
        ) from exc


def _normalize_evidence_descriptor(item: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(item, Mapping) or set(item) != _EVIDENCE_KEYS:
        raise FaultInjectionValidationError(
            "fault evidence descriptor fields differ from the locked schema"
        )
    payload = dict(item)
    if not isinstance(payload.get("artifact_kind"), str) or not payload[
        "artifact_kind"
    ]:
        raise FaultInjectionValidationError("fault evidence artifact_kind is missing")
    if not isinstance(payload.get("relative_reference"), str) or not payload[
        "relative_reference"
    ]:
        raise FaultInjectionValidationError("fault evidence relative reference is missing")
    reference = str(payload["relative_reference"])
    if reference.startswith(("/", "~")) or ".." in Path(reference).parts:
        raise FaultInjectionValidationError("fault evidence reference must be relative")
    if _SHA256_RE.fullmatch(str(payload.get("sha256") or "")) is None:
        raise FaultInjectionValidationError("fault evidence SHA-256 is invalid")
    if payload.get("controller_only") is not True:
        raise FaultInjectionValidationError(
            "raw fault evidence must remain controller-only"
        )
    return payload


def _normalize_remote_attestation(
    value: Mapping[str, Any] | None,
    *,
    execution_mode: str,
) -> dict[str, Any]:
    if value is None:
        payload: dict[str, Any] = {
            "ssh_host_ed25519_fingerprint": None,
            "verified_ssh_host_key": False,
            "controller_machine_id_match": False,
            "remote_command_executed": False,
        }
    elif isinstance(value, Mapping) and set(value) == _REMOTE_ATTESTATION_KEYS:
        payload = dict(value)
    else:
        raise FaultInjectionValidationError("remote attestation schema mismatch")
    if execution_mode == "local_simulation":
        expected_local = {
            "ssh_host_ed25519_fingerprint": None,
            "verified_ssh_host_key": False,
            "controller_machine_id_match": False,
            "remote_command_executed": False,
        }
        if payload != expected_local:
            raise FaultInjectionValidationError(
                "local simulation must not claim a remote attestation"
            )
    elif execution_mode == "remote_real":
        fingerprint = payload.get("ssh_host_ed25519_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint.startswith("SHA256:"):
            raise FaultInjectionValidationError("remote attestation fingerprint missing")
        if any(
            payload.get(key) is not True
            for key in (
                "verified_ssh_host_key",
                "controller_machine_id_match",
                "remote_command_executed",
            )
        ):
            raise FaultInjectionValidationError("remote attestation is incomplete")
    else:
        raise FaultInjectionValidationError("remote attestation mode mismatch")
    return payload


def _verify_aggregate_attestation(
    payload: Mapping[str, Any],
    *,
    expected_fingerprint: str | None,
    require_remote_attestation: bool,
) -> bool:
    attestation = dict(payload.get("remote_attestation") or {})
    if not require_remote_attestation:
        return attestation == {
            "ssh_host_ed25519_fingerprint": None,
            "verified_ssh_host_key": False,
            "controller_machine_id_match": False,
            "remote_command_executed": False,
        }
    return (
        attestation.get("ssh_host_ed25519_fingerprint") == expected_fingerprint
        and attestation.get("verified_ssh_host_key") is True
        and attestation.get("controller_machine_id_match") is True
        and attestation.get("remote_command_executed") is True
    )


def _verify_aggregate_evidence(
    payload: Mapping[str, Any],
    *,
    receipts_root: Path,
    require_remote_evidence: bool,
) -> bool:
    descriptors = list(payload.get("evidence") or [])
    if not require_remote_evidence:
        return not descriptors
    if {
        str(item.get("artifact_kind"))
        for item in descriptors
        if isinstance(item, Mapping)
    } != _REQUIRED_REMOTE_EVIDENCE_KINDS:
        return False
    if len(descriptors) != len(_REQUIRED_REMOTE_EVIDENCE_KINDS):
        return False
    root = receipts_root.resolve()
    for raw in descriptors:
        if not isinstance(raw, Mapping):
            return False
        descriptor = _normalize_evidence_descriptor(raw)
        artifact = (receipts_root / descriptor["relative_reference"]).resolve()
        try:
            artifact.relative_to(root)
        except ValueError:
            return False
        if not artifact.is_file() or sha256_file(artifact) != descriptor["sha256"]:
            return False
        if stat.S_IMODE(artifact.stat().st_mode) & 0o077:
            return False
        try:
            raw = json.loads(artifact.read_text(encoding="utf-8"))
            if not isinstance(raw, Mapping):
                return False
            _validate_remote_raw_evidence(
                raw,
                receipt=payload,
                artifact_kind=str(descriptor["artifact_kind"]),
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            FaultInjectionValidationError,
        ):
            return False
    return True


def _validate_remote_raw_evidence(
    raw: Mapping[str, Any],
    *,
    receipt: Mapping[str, Any],
    artifact_kind: str,
) -> None:
    required_keys = {
        "schema_version",
        "benchmark",
        "benchmark_version",
        "execution_mode",
        "machine_id",
        "agent_id",
        "fault_kind",
        "phase",
        "measured_at",
        "ssh_host_ed25519_fingerprint",
        "executor_source_sha256",
        "site_lock_core_sha256",
        "facts",
        "measurements",
        "raw_stdout_or_stderr_persisted",
        "provider_environment_absence_verified",
        "provider_environment_probe",
        "real_credential_loaded",
        "paid_model_calls",
        "integrity",
    }
    if set(raw) != required_keys:
        raise FaultInjectionValidationError("remote raw evidence schema fields mismatch")
    expected_phase = {
        "fault_observation": "fault_observation",
        "recovery_observation": "recovery_observation",
    }.get(artifact_kind)
    if expected_phase is None or raw.get("phase") != expected_phase:
        raise FaultInjectionValidationError("remote raw evidence phase mismatch")
    if (
        raw.get("schema_version") != REMOTE_RAW_EVIDENCE_SCHEMA
        or raw.get("benchmark") != BENCHMARK
        or raw.get("benchmark_version") != BENCHMARK_VERSION
        or raw.get("execution_mode") != "remote_real"
        or raw.get("machine_id") != receipt.get("machine_id")
        or raw.get("fault_kind") != receipt.get("fault_kind")
        or raw.get("ssh_host_ed25519_fingerprint")
        != dict(receipt.get("remote_attestation") or {}).get(
            "ssh_host_ed25519_fingerprint"
        )
    ):
        raise FaultInjectionValidationError("remote raw evidence identity mismatch")
    if not isinstance(raw.get("agent_id"), str) or not raw["agent_id"]:
        raise FaultInjectionValidationError("remote raw evidence agent identity missing")
    _validate_timestamp(str(raw.get("measured_at") or ""))
    for hash_key in ("executor_source_sha256", "site_lock_core_sha256"):
        if _SHA256_RE.fullmatch(str(raw.get(hash_key) or "")) is None:
            raise FaultInjectionValidationError(
                f"remote raw evidence {hash_key} is invalid"
            )
    facts = raw.get("facts")
    if not isinstance(facts, Mapping):
        raise FaultInjectionValidationError("remote raw evidence facts are missing")
    if artifact_kind == "fault_observation":
        classify_fault_observation(str(receipt["fault_kind"]), facts)
    else:
        classify_recovery_observation(str(receipt["fault_kind"]), facts)
    if not isinstance(raw.get("measurements"), Mapping):
        raise FaultInjectionValidationError("remote raw measurements are missing")
    if (
        raw.get("raw_stdout_or_stderr_persisted") is not False
        or raw.get("provider_environment_absence_verified") is not True
        or raw.get("real_credential_loaded") is not False
        or raw.get("paid_model_calls") != 0
    ):
        raise FaultInjectionValidationError("remote raw safety declaration failed")
    provider_probe = raw.get("provider_environment_probe")
    if not isinstance(provider_probe, Mapping) or set(provider_probe) != {
        "returncode",
        "stdout_sha256",
        "stderr_sha256",
        "stdout_bytes",
        "stderr_bytes",
        "raw_output_persisted",
    }:
        raise FaultInjectionValidationError(
            "remote provider-environment probe metadata mismatch"
        )
    if (
        provider_probe.get("returncode") != 0
        or provider_probe.get("raw_output_persisted") is not False
        or _SHA256_RE.fullmatch(str(provider_probe.get("stdout_sha256") or ""))
        is None
        or _SHA256_RE.fullmatch(str(provider_probe.get("stderr_sha256") or ""))
        is None
    ):
        raise FaultInjectionValidationError(
            "remote provider-environment probe did not pass"
        )
    if scan_sensitive_material(_without_integrity(raw)):
        raise FaultInjectionValidationError("remote raw evidence contains a secret")
    integrity = raw.get("integrity")
    if (
        not isinstance(integrity, Mapping)
        or integrity.get("algorithm") != "sha256_canonical_json"
        or integrity.get("core_sha256") != sha256_object(_without_integrity(raw))
    ):
        raise FaultInjectionValidationError("remote raw evidence integrity mismatch")


def _without_integrity(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "integrity"}


def _validate_machine_id(machine_id: str) -> None:
    if _MACHINE_ID_RE.fullmatch(machine_id) is None:
        raise FaultInjectionValidationError(f"invalid machine ID: {machine_id!r}")


def _validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FaultInjectionValidationError("completed_at is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise FaultInjectionValidationError("completed_at must include a timezone")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
