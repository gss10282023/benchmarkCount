"""Blind, cross-process runtime control for AgentDojo OpenRouter calls.

This module deliberately never accepts prompts, responses, trajectories, case
identifiers, or evaluator outputs.  The mutable SQLite state and JSONL health
ledger therefore remain safe for an operations-only monitor to inspect while
the checklist branch is still blinded to evidence.
"""

from __future__ import annotations

from contextlib import contextmanager
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import grp
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sqlite3
import stat
import threading
import time
from typing import Any, Callable, Iterator, Mapping, Sequence
import uuid

from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import validate_object
from evidence_system.core.schemas import load_json_or_yaml


RUNTIME_POLICY_SCHEMA_VERSION = "agentdojo_openrouter_runtime_policy/v1"
BLIND_HEALTH_SCHEMA_VERSION = "agentdojo_openrouter_blind_health/v1"
SEALED_INCIDENT_SCHEMA_VERSION = "agentdojo_openrouter_sealed_incident/v1"
CREDENTIAL_PROBE_RECEIPT_SCHEMA_VERSION = (
    "agentdojo_openrouter_credential_probe_receipt/v1"
)
DISPOSABLE_RAMP_RECEIPT_SCHEMA_VERSION = (
    "agentdojo_openrouter_disposable_ramp_receipt/v1"
)
RAMP_STAGE_RECEIPT_SCHEMA_VERSION = "agentdojo_openrouter_ramp_stage_receipt/v2"
RAMP_RESOURCE_SAMPLE_SCHEMA_VERSION = "agentdojo_openrouter_ramp_resource_sample/v2"
FORMAL_STAGE_HEALTH_RECEIPT_SCHEMA_VERSION = (
    "agentdojo_formal_stage_health_receipt/v1"
)
RATE_MEASUREMENT_RECEIPT_SCHEMA_VERSION = (
    "agentdojo_openrouter_rate_measurement_receipt/v1"
)
POLICY_FINALIZATION_RECEIPT_SCHEMA_VERSION = (
    "agentdojo_openrouter_policy_finalization_receipt/v1"
)
REQUIRED_MODELS = (
    "openai/gpt-5.4",
    "anthropic/claude-opus-4.7",
    "deepseek/deepseek-v4-pro",
)
REQUIRED_AGENT_IDS = ("Agent A", "Agent B", "Agent C")
REQUIRED_SUITES = ("banking", "slack", "travel", "workspace")
FORMAL_BUDGET_ADMISSION_OVERRIDE_SCHEMA_VERSION = (
    "agentdojo_formal_budget_admission_override/v1"
)
FORMAL_BUDGET_ADMISSION_OVERRIDE_RELATIVE_PATH = Path(
    "formal-control/operator-overrides/formal-budget-admission-override.v1.json"
)


def resource_worker_process_binding_sha256(
    *,
    execution_scope_sha256: str,
    stage_id: str,
    session_id: str,
    stage_binding_sha256: str,
) -> str:
    """Derive the opaque command-line token used by the procfs sampler."""

    normalized_stage = str(stage_id)
    if not normalized_stage or len(normalized_stage) > 64:
        raise RuntimePolicyError("resource worker stage_id is invalid")
    return sha256_object(
        {
            "schema_version": "agentdojo_resource_worker_process_binding/v1",
            "execution_scope_sha256": _validate_digest(
                execution_scope_sha256, "resource execution_scope_sha256"
            ),
            "stage_id": normalized_stage,
            "session_id": _validate_session_id(session_id),
            "stage_binding_sha256": _validate_digest(
                stage_binding_sha256, "resource stage_binding_sha256"
            ),
        }
    )
AGENTDOJO_LOCAL_LLM_TOP_P = 0.9
AGENTDOJO_LOCAL_LLM_SEED_POLICY = {
    "schema_version": "agentdojo_local_llm_seed_policy/v1",
    "source": "agentdojo==0.1.35 LocalLLM.chat_completion_request",
    "source_git_commit": "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b",
    "source_git_tree": "3c74b60f2bad4ff321d864e0c0483f256cc8f8d2",
    "per_call_seed": "python_random_randint_from_job_seeded_process",
    "job_seed_application": ["PYTHONHASHSEED_before_process", "random.seed", "numpy.random.seed_mod_2pow32_if_available"],
    "provider_determinism_claimed": False,
}
AGENTDOJO_LOCAL_LLM_SEED_POLICY_SHA256 = sha256_object(
    AGENTDOJO_LOCAL_LLM_SEED_POLICY
)
AGENTDOJO_PROXY_REQUEST_TRANSFORM = {
    "schema_version": "agentdojo_openrouter_proxy_transform/v1",
    "incoming_exact_fields": ["model", "messages", "temperature", "top_p", "seed"],
    "validated_sources": {
        "temperature": "frozen_agent_config",
        "top_p": "agentdojo_0.1.35_local_llm",
        "seed": "agentdojo_0.1.35_local_llm_from_locked_job_seed",
    },
    "injected_fields": {"model": "frozen_agent_model", "max_tokens": "frozen_agent_config"},
    "tool_protocol": {
        "delivery": "serialized_into_system_prompt_by_agentdojo_0.1.35",
        "native_tools_request_field": "absent",
        "native_tool_choice_request_field": "absent",
        "tool_delimiter_and_output_format": "locked_by_execution_lock",
    },
    "provider_routing": {
        "request_field": "absent",
        "semantics": "openrouter_default_dynamic_routing",
        "fixed_upstream_provider_claimed": False,
    },
    "serialization": "canonical_json_ensure_ascii_sort_keys_compact_utf8",
}
AGENTDOJO_PROXY_REQUEST_TRANSFORM_SHA256 = sha256_object(
    AGENTDOJO_PROXY_REQUEST_TRANSFORM
)
REQUIRED_PREFLIGHT_START_CREDIT_USD = 800.0
REQUIRED_FORMAL_START_REMAINING_USD = 650.0
REQUIRED_PREFLIGHT_COST_CAP_USD = 120.0
REQUIRED_MEASUREMENT_PHASE_COST_CAP_USD = 70.0
REQUIRED_FINAL_VALIDATION_BUDGET_USD = 70.0
REQUIRED_TWO_ROUND_PREFLIGHT_COST_CAP_USD = 120.0

# This definition is part of the frozen runtime semantics.  One reserved prompt
# token per serialized UTF-8 byte is deliberately much more conservative than
# the common ``characters / 4`` observation and does not depend on a mutable
# provider tokenizer.  The requested completion ceiling is then added in full.
PROMPT_TOKEN_RESERVATION_DEFINITION = {
    "schema_version": "agentdojo_prompt_token_reservation/v1",
    "method": "canonical_request_json_utf8_byte_upper_bound_plus_max_tokens",
    "serialization": {
        "format": "json",
        "ensure_ascii": True,
        "sort_keys": True,
        "separators": [",", ":"],
        "encoding": "utf-8",
    },
    "prompt_reservation": "max(1, serialized_utf8_byte_length)",
    "completion_reservation": "request_max_tokens",
}
PROMPT_TOKEN_RESERVATION_DEFINITION_SHA256 = sha256_object(
    PROMPT_TOKEN_RESERVATION_DEFINITION
)
TOKEN_RATE_UNITS_DEFINITION = {
    "schema_version": "agentdojo_openrouter_token_rate_units/v1",
    "tokens_per_minute_policy_unit": "admission_reservation_units",
    "admission_reservation_unit": (
        "one_tokenizer_independent_reserved_token_upper_bound_unit"
    ),
    "request_window_accounting": (
        "retain_admission_reservation_for_full_rate_window_after_release"
    ),
    "provider_actual_tokens_per_minute": "separate_observational_telemetry_only",
    "provider_actual_tokens_never_substitute_for_admission_reservation": True,
}
TOKEN_RATE_UNITS_DEFINITION_SHA256 = sha256_object(TOKEN_RATE_UNITS_DEFINITION)
RATE_MEASUREMENT_SAFE_MARGIN_DEFINITION = {
    "schema_version": "agentdojo_rate_measurement_safe_margin/v1",
    "algorithm": "floor_observed_admission_reservation_rate_times_0_80",
    "multiplier": 0.8,
    "minimum": 1,
    "concurrency": "highest_stage_passing_locked_health_thresholds",
}
RATE_MEASUREMENT_SAFE_MARGIN_DEFINITION_SHA256 = sha256_object(
    RATE_MEASUREMENT_SAFE_MARGIN_DEFINITION
)
LIMITER_CLOCK_DEFINITION = {
    "schema_version": "agentdojo_limiter_clock/v1",
    "basis": "linux_monotonic_since_boot/v1",
    "utc_usage": "audit_timestamps_only",
    "boot_binding": "sqlite_metadata_host_boot_id",
}
LIMITER_CLOCK_DEFINITION_SHA256 = sha256_object(LIMITER_CLOCK_DEFINITION)
FORMAL_SINGLE_MODEL_SCHEDULING_INVARIANT = {
    "schema_version": "agentdojo_formal_single_model_scheduling/v1",
    "formal_model_batches": "strictly_serial_no_cross_model_overlap",
    "multi_model_canary_coverage": "all_three_models_four_slots_each",
    "multi_model_canary_scheduling": (
        "three_serial_four_slot_single_model_subbatches"
    ),
    "multi_model_canary_applies_to": ["disposable", "formal"],
    "global_concurrency_derivation": (
        "max_per_model_safe_under_single_model_serial_invariant"
    ),
    "global_rate_derivation": "max_per_model_safe_rate_under_single_model_serial_invariant",
}
FORMAL_SINGLE_MODEL_SCHEDULING_INVARIANT_SHA256 = sha256_object(
    FORMAL_SINGLE_MODEL_SCHEDULING_INVARIANT
)
OPENROUTER_REQUIRED_DECLARED_PARAMETERS = (
    "temperature",
    "top_p",
)
OPENROUTER_SEED_PARAMETER = "seed"
OPENROUTER_MAX_TOKENS_PARAMETER = "max_tokens"
OPENROUTER_SUCCESS_PARAMETER_HEALTH_FIELDS = (
    "temperature_parameter_present",
    "top_p_parameter_present",
    "max_tokens_parameter_present",
    "seed_parameter_present",
    "native_tools_parameter_absent",
    "native_tool_choice_parameter_absent",
)
OPENROUTER_ACCOUNT_INVENTORY_MATCH_FIELDS = (
    "creator_user_id",
    "label",
    "limit",
    "limit_remaining",
    "limit_reset",
    "usage",
    "expires_at",
)
OPENROUTER_ACCOUNT_INVENTORY_PAGE_SIZE = 100
OPENROUTER_ACCOUNT_INVENTORY_MAX_PAGES = 100
OPENROUTER_ACCOUNT_INVENTORY_FLOAT_ABS_TOLERANCE = 1e-9
OPENROUTER_ACCOUNT_INVENTORY_FLOAT_REL_TOLERANCE = 1e-12
OPENROUTER_KEY_FINGERPRINT_DOMAIN = b"agentdojo-openrouter-key/v1\0"
OPENROUTER_MANAGEMENT_AUDIT_FINGERPRINT_DOMAIN = (
    b"agentdojo-openrouter-management-audit-key/v1\0"
)


def openrouter_key_fingerprint(api_key: str | bytes) -> str:
    """Return a domain-separated key identity without persisting key material."""

    key_bytes = api_key.encode("utf-8") if isinstance(api_key, str) else bytes(api_key)
    if not key_bytes or b"\x00" in key_bytes:
        raise RuntimePolicyError("OpenRouter key material is empty or malformed")
    return hashlib.sha256(OPENROUTER_KEY_FINGERPRINT_DOMAIN + key_bytes).hexdigest()


def openrouter_management_audit_fingerprint(api_key: str | bytes) -> str:
    """Identify the local-only management audit key without storing it."""

    key_bytes = api_key.encode("utf-8") if isinstance(api_key, str) else bytes(api_key)
    if not key_bytes or b"\x00" in key_bytes:
        raise RuntimePolicyError("OpenRouter management key material is empty or malformed")
    return hashlib.sha256(
        OPENROUTER_MANAGEMENT_AUDIT_FINGERPRINT_DOMAIN + key_bytes
    ).hexdigest()


class _OpenRouterAuthLifecycleHandle:
    """One process-held side of the execution/credential lifecycle barrier."""

    def __init__(self, descriptor: int) -> None:
        self._descriptor = descriptor
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            fcntl.flock(self._descriptor, fcntl.LOCK_UN)
        finally:
            os.close(self._descriptor)

    def __enter__(self) -> "_OpenRouterAuthLifecycleHandle":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class OpenRouterAuthLifecycleLock:
    """Cross-process barrier between inference and credential/account audits.

    Inference requests hold a shared lock from immediately before admission
    until provider usage has been durably released.  Credential probes hold an
    exclusive lock across ``/key``, the management ``/keys`` inventory walk,
    ``/credits``, and model-catalog reads.  Consequently the execution-key
    ``usage`` value cannot change inside the same-account matching critical
    section.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def acquire(self, *, exclusive: bool) -> _OpenRouterAuthLifecycleHandle:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        _assert_directory_chain_no_symlinks(self.path.parent)
        descriptor = os.open(
            self.path,
            os.O_RDWR
            | os.O_CREAT
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                raise RuntimePolicyError(
                    "OpenRouter auth lifecycle lock must be a single-link regular file"
                )
            os.fchmod(descriptor, 0o600)
            fcntl.flock(
                descriptor,
                fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH,
            )
        except BaseException:
            os.close(descriptor)
            raise
        return _OpenRouterAuthLifecycleHandle(descriptor)

    @contextmanager
    def hold(self, *, exclusive: bool) -> Iterator[None]:
        handle = self.acquire(exclusive=exclusive)
        try:
            yield
        finally:
            handle.close()

_ALLOWED_HEALTH_FIELDS = frozenset(
    {
        "schema_version",
        "timestamp",
        "event_type",
        "policy_sha256",
        "outcome",
        "http_status",
        "attempt_index",
        "max_attempts",
        "retry_after_seconds",
        "retry_delay_seconds",
        "latency_seconds",
        "limiter_wait_seconds",
        "reserved_tokens",
        "actual_total_tokens",
        "active_requests",
        "requests_in_window",
        "tokens_in_window",
        "model_active_requests",
        "model_requests_in_window",
        "model_tokens_in_window",
        "actual_cost_usd",
        "reserved_cost_usd",
        "cumulative_cost_usd",
        "pending_reserved_cost_usd",
        "credit_balance_usd",
        "credit_floor_usd",
        "incident_id",
        "job_identity_sha256",
        "model_config_sha256",
        "request_chain_id",
        "session_id",
        "host_boot_id",
        "returned_model_identity_sha256",
        "credential_fingerprint_sha256",
        "temperature_parameter_present",
        "top_p_parameter_present",
        "max_tokens_parameter_present",
        "seed_parameter_present",
        "native_tools_parameter_absent",
        "native_tool_choice_parameter_absent",
    }
)
_ALLOWED_HEALTH_EVENT_TYPES = frozenset(
    {
        "request_attempt",
        "worker_completion",
        "credential_probe",
        "budget_probe",
        "ramp_health",
        "incident",
    }
)
_ALLOWED_HEALTH_OUTCOMES = frozenset(
    {"success", "passed", "retryable_error", "fatal_error", "blocked", "warning"}
)
_SEALED_INCIDENT_CATEGORIES = frozenset(
    {
        "credential",
        "http_rate_limit",
        "http_service",
        "transport",
        "invalid_json",
        "runtime",
        "case_execution",
        "artifact",
        "budget",
        "unknown",
    }
)
_SEALED_INCIDENT_ORIGINS = frozenset(
    {"case", "controller", "vps", "provider", "credentials", "unknown"}
)


class RuntimePolicyError(ValueError):
    """Raised when a runtime-control policy or health record is invalid."""


class RuntimeBudgetExceeded(RuntimeError):
    """Raised before a request when a locked hard cost cap is exhausted."""


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    retryable_http_statuses: tuple[int, ...]
    retry_transport_errors: bool
    retry_invalid_json: bool
    respect_retry_after: bool
    base_delay_seconds: float
    multiplier: float
    max_backoff_seconds: float
    max_retry_after_seconds: float
    jitter_fraction: float


@dataclass(frozen=True)
class BudgetPolicy:
    minimum_preflight_start_credit_usd: float
    minimum_formal_start_remaining_usd: float
    maximum_preflight_cost_usd: float
    maximum_final_validation_cost_usd: float
    maximum_run_cost_usd: float
    maximum_single_request_cost_usd: float
    cost_cap_action: str
    unknown_actual_cost_action: str


@dataclass(frozen=True)
class RuntimePolicy:
    raw: Mapping[str, Any]
    semantic_sha256: str
    operational_definition_sha256: str
    policy_id: str
    lifecycle_status: str
    measurement_receipt_path: str | None
    measurement_receipt_sha256: str | None
    execution_key_fingerprint_sha256: str | None
    per_model_safe_limits: Mapping[str, Mapping[str, int]] | None
    runtime_mode: str
    formal_execution_allowed: bool
    limiter_clock_definition_sha256: str
    token_rate_units_definition_sha256: str
    max_concurrent_requests: int
    requests_per_minute: int
    tokens_per_minute: int
    rate_window_seconds: float
    prompt_token_reservation_definition_sha256: str
    prompt_chars_per_token: float
    completion_token_reservation: str
    lease_timeout_seconds: float
    acquire_poll_seconds: float
    retry: RetryPolicy
    budget: BudgetPolicy
    ramp_stages: tuple[int, ...]
    ramp_max_cpu_percent: float
    ramp_max_memory_percent: float
    ramp_minimum_resource_samples: int
    ramp_minimum_active_request_fraction: float
    ramp_minimum_active_worker_fraction: float
    ramp_max_recovered_429_503_fraction: float
    ramp_max_consecutive_429_503: int
    ramp_max_retry_delay_seconds_per_chain: float


@dataclass(frozen=True)
class LimiterSnapshot:
    active_requests: int
    requests_in_window: int
    tokens_in_window: int
    model_active_requests: int
    model_requests_in_window: int
    model_tokens_in_window: int
    cumulative_cost_usd: float
    pending_reserved_cost_usd: float


@dataclass(frozen=True)
class BudgetStateSnapshot:
    budget_scope: str
    clock_basis: str
    host_boot_id: str
    hard_blocked: bool
    reservation_violation_count: int
    violation_event_id: str | None
    cumulative_cost_usd: float
    pending_reserved_cost_usd: float
    active_leases: int
    expired_unknown_cost_count: int


@dataclass(frozen=True)
class SharedPreflightBudgetSnapshot:
    host_boot_id: str
    measurement_cost_usd: float
    validation_cost_usd: float
    aggregate_cost_usd: float
    pending_reserved_cost_usd: float
    active_leases: int
    expired_or_boot_recovered_unknown_cost_count: int
    hard_blocked: bool


def load_runtime_policy(
    payload: Mapping[str, Any],
    *,
    expected_semantic_sha256: str | None = None,
) -> RuntimePolicy:
    """Validate a frozen runtime policy and return its typed representation."""

    raw = json.loads(json.dumps(dict(payload), ensure_ascii=True))
    if raw.get("schema_version") != RUNTIME_POLICY_SCHEMA_VERSION:
        raise RuntimePolicyError(
            f"runtime policy schema_version must be {RUNTIME_POLICY_SCHEMA_VERSION!r}"
        )
    _require_exact_keys(
        raw,
        {
            "schema_version",
            "policy_id",
            "lifecycle",
            "operational_override",
            "execution_eligibility",
            "clock",
            "token_rate_units",
            "scope",
            "max_concurrent_requests",
            "requests_per_minute",
            "tokens_per_minute",
            "rate_window_seconds",
            "prompt_token_reservation",
            "prompt_chars_per_token",
            "completion_token_reservation",
            "lease_timeout_seconds",
            "acquire_poll_seconds",
            "retry",
            "budget",
            "ramp",
            "health",
        },
        field="runtime policy",
    )
    semantic_sha256 = sha256_object(raw)
    operational_definition = dict(raw)
    operational_definition.pop("lifecycle", None)
    operational_definition_sha256 = sha256_object(operational_definition)
    if expected_semantic_sha256 is not None:
        expected = str(expected_semantic_sha256).removeprefix("sha256:")
        if semantic_sha256 != expected:
            raise RuntimePolicyError(
                "runtime policy semantic SHA-256 mismatch: "
                f"expected={expected} actual={semantic_sha256}"
            )

    policy_id = _required_string(raw, "policy_id")
    eligibility = _required_mapping(raw, "execution_eligibility")
    _require_exact_keys(
        eligibility,
        {
            "mode",
            "formal_execution_allowed",
            "requested_measurement_envelope",
            "safe_margin_algorithm",
            "safe_margin_definition_sha256",
        },
        field="runtime policy execution_eligibility",
    )
    runtime_mode = _required_string(eligibility, "mode")
    formal_execution_allowed = _required_bool(
        eligibility, "formal_execution_allowed"
    )
    clock_definition = _required_mapping(raw, "clock")
    _require_exact_keys(
        clock_definition,
        {"schema_version", "basis", "utc_usage", "boot_binding", "definition_sha256"},
        field="runtime policy clock",
    )
    expected_clock = {
        **LIMITER_CLOCK_DEFINITION,
        "definition_sha256": LIMITER_CLOCK_DEFINITION_SHA256,
    }
    if dict(clock_definition) != expected_clock:
        raise RuntimePolicyError("runtime limiter clock definition/hash differs")
    token_rate_units = _required_mapping(raw, "token_rate_units")
    expected_token_rate_units = {
        **TOKEN_RATE_UNITS_DEFINITION,
        "definition_sha256": TOKEN_RATE_UNITS_DEFINITION_SHA256,
    }
    if dict(token_rate_units) != expected_token_rate_units:
        raise RuntimePolicyError("runtime token-rate unit definition/hash differs")
    envelope = _required_mapping(eligibility, "requested_measurement_envelope")
    _require_exact_keys(
        envelope,
        {"requests_per_minute", "tokens_per_minute", "concurrent_requests"},
        field="requested measurement envelope",
    )
    if (
        _required_string(eligibility, "safe_margin_algorithm")
        != RATE_MEASUREMENT_SAFE_MARGIN_DEFINITION["algorithm"]
        or _validate_digest(
            _required_string(eligibility, "safe_margin_definition_sha256"),
            "safe_margin_definition_sha256",
        )
        != RATE_MEASUREMENT_SAFE_MARGIN_DEFINITION_SHA256
    ):
        raise RuntimePolicyError("runtime policy safe-margin algorithm/hash differs")
    lifecycle = _required_mapping(raw, "lifecycle")
    _require_exact_keys(
        lifecycle,
        {"status", "measurement_receipt_path", "measurement_receipt_sha256"},
        field="runtime policy lifecycle",
    )
    lifecycle_status = _required_string(lifecycle, "status")
    if lifecycle_status not in {"provisional", "finalized"}:
        raise RuntimePolicyError("runtime policy lifecycle.status is invalid")
    measurement_path_raw = lifecycle.get("measurement_receipt_path")
    measurement_sha_raw = lifecycle.get("measurement_receipt_sha256")
    if lifecycle_status == "provisional":
        if measurement_path_raw is not None or measurement_sha_raw is not None:
            raise RuntimePolicyError(
                "provisional runtime policy must not claim a measurement receipt"
            )
        measurement_path = None
        measurement_sha = None
        if runtime_mode != "exploratory_measurement" or formal_execution_allowed:
            raise RuntimePolicyError(
                "provisional policy must be exploratory-only and forbidden for formal execution"
            )
    else:
        if not isinstance(measurement_path_raw, str) or not measurement_path_raw.strip():
            raise RuntimePolicyError(
                "finalized runtime policy requires measurement_receipt_path"
            )
        measurement_path = measurement_path_raw.strip()
        measurement_sha = _validate_digest(
            str(measurement_sha_raw or ""), "lifecycle.measurement_receipt_sha256"
        )
        if runtime_mode != "finalized_validation" or not formal_execution_allowed:
            raise RuntimePolicyError(
                "finalized policy must explicitly authorize validated formal execution"
            )

    override = _required_mapping(raw, "operational_override")
    _require_exact_keys(
        override,
        {
            "scope",
            "allowed_fields",
            "base_agents_config_file_sha256",
            "base_values",
            "effective_values",
            "per_model_safe_limits",
            "execution_key_fingerprint_sha256",
            "formal_scheduling_invariant",
            "reason",
        },
        field="runtime policy operational_override",
    )
    if _required_string(override, "scope") != "scheduling_only_no_request_semantics":
        raise RuntimePolicyError("operational override scope is invalid")
    allowed_fields = override.get("allowed_fields")
    expected_override_fields = [
        "rate_limit.requests_per_minute",
        "rate_limit.tokens_per_minute",
        "rate_limit.concurrent_requests",
    ]
    if allowed_fields != expected_override_fields:
        raise RuntimePolicyError(
            f"operational override allowed_fields must equal {expected_override_fields!r}"
        )
    _validate_digest(
        str(override.get("base_agents_config_file_sha256") or ""),
        "operational_override.base_agents_config_file_sha256",
    )
    base_values = _required_mapping(override, "base_values")
    _require_exact_keys(
        base_values,
        {"requests_per_minute", "tokens_per_minute", "concurrent_requests_per_agent"},
        field="operational override base_values",
    )
    _required_int(base_values, "requests_per_minute", minimum=1)
    _required_int(base_values, "tokens_per_minute", minimum=1)
    _required_int(base_values, "concurrent_requests_per_agent", minimum=1)
    effective_values = _required_mapping(override, "effective_values")
    _require_exact_keys(
        effective_values,
        {"requests_per_minute", "tokens_per_minute", "global_concurrent_requests"},
        field="operational override effective_values",
    )
    effective_rpm = _required_int(effective_values, "requests_per_minute", minimum=1)
    effective_tpm = _required_int(effective_values, "tokens_per_minute", minimum=1)
    effective_concurrency = _required_int(
        effective_values, "global_concurrent_requests", minimum=1
    )
    per_model_limits_raw = override.get("per_model_safe_limits")
    scheduling_invariant = _required_mapping(
        override, "formal_scheduling_invariant"
    )
    expected_scheduling_invariant = {
        **FORMAL_SINGLE_MODEL_SCHEDULING_INVARIANT,
        "definition_sha256": FORMAL_SINGLE_MODEL_SCHEDULING_INVARIANT_SHA256,
    }
    if dict(scheduling_invariant) != expected_scheduling_invariant:
        raise RuntimePolicyError("formal single-model scheduling invariant differs")
    key_fingerprint_raw = override.get("execution_key_fingerprint_sha256")
    normalized_model_limits: dict[str, dict[str, int]] | None = None
    if lifecycle_status == "provisional":
        if per_model_limits_raw is not None:
            raise RuntimePolicyError(
                "provisional runtime policy must not claim per-model safe limits"
            )
        if key_fingerprint_raw is not None:
            raise RuntimePolicyError(
                "provisional runtime policy must not pre-claim an execution key"
            )
        key_fingerprint = None
    else:
        key_fingerprint = _validate_digest(
            str(key_fingerprint_raw or ""),
            "operational_override.execution_key_fingerprint_sha256",
        )
        if not isinstance(per_model_limits_raw, list) or len(per_model_limits_raw) != 3:
            raise RuntimePolicyError(
                "finalized runtime policy requires three per-model safe limits"
            )
        normalized_model_limits = {}
        for required_model, row in zip(REQUIRED_MODELS, per_model_limits_raw, strict=True):
            if not isinstance(row, Mapping):
                raise RuntimePolicyError("per-model safe-limit row must be an object")
            _require_exact_keys(
                row,
                {
                    "model_id",
                    "requests_per_minute",
                    "tokens_per_minute",
                    "concurrent_requests",
                },
                field="per-model safe limit",
            )
            if row.get("model_id") != required_model:
                raise RuntimePolicyError("per-model safe limits use the wrong model order")
            normalized_model_limits[required_model] = {
                "requests_per_minute": _required_int(
                    row, "requests_per_minute", minimum=1
                ),
                "tokens_per_minute": _required_int(
                    row, "tokens_per_minute", minimum=1
                ),
                "concurrent_requests": _required_int(
                    row, "concurrent_requests", minimum=1
                ),
            }
    if not _required_string(override, "reason").strip():
        raise RuntimePolicyError("operational override reason must be non-empty")
    if _required_string(raw, "scope") != "single_openrouter_api_key_across_all_agentdojo_workers":
        raise RuntimePolicyError("runtime policy scope is not the supported global API-key scope")
    max_concurrent = _required_int(raw, "max_concurrent_requests", minimum=1)
    rpm = _required_int(raw, "requests_per_minute", minimum=1)
    tpm = _required_int(raw, "tokens_per_minute", minimum=1)
    requested_envelope = {
        "requests_per_minute": _required_int(
            envelope, "requests_per_minute", minimum=300
        ),
        "tokens_per_minute": _required_int(
            envelope, "tokens_per_minute", minimum=1_000_000
        ),
        "concurrent_requests": _required_int(
            envelope, "concurrent_requests", minimum=32
        ),
    }
    if requested_envelope["concurrent_requests"] != 32:
        raise RuntimePolicyError("exploratory measurement concurrency envelope must be 32")
    if lifecycle_status == "provisional" and (rpm, tpm, max_concurrent) != (
        requested_envelope["requests_per_minute"],
        requested_envelope["tokens_per_minute"],
        requested_envelope["concurrent_requests"],
    ):
        raise RuntimePolicyError(
            "provisional policy must use its full locked exploratory measurement envelope"
        )
    if (max_concurrent, rpm, tpm) != (
        effective_concurrency,
        effective_rpm,
        effective_tpm,
    ):
        raise RuntimePolicyError(
            "runtime limits differ from operational_override.effective_values"
        )
    rate_window = _required_float(raw, "rate_window_seconds", minimum=1.0)
    prompt_reservation_raw = _required_mapping(raw, "prompt_token_reservation")
    _require_exact_keys(
        prompt_reservation_raw,
        {"method", "version", "definition_sha256"},
        field="runtime policy prompt_token_reservation",
    )
    if _required_string(prompt_reservation_raw, "method") != str(
        PROMPT_TOKEN_RESERVATION_DEFINITION["method"]
    ):
        raise RuntimePolicyError("unsupported prompt token reservation method")
    if _required_string(prompt_reservation_raw, "version") != "v1":
        raise RuntimePolicyError("unsupported prompt token reservation version")
    prompt_reservation_definition_sha = _validate_digest(
        _required_string(prompt_reservation_raw, "definition_sha256"),
        "prompt_token_reservation.definition_sha256",
    )
    if (
        prompt_reservation_definition_sha
        != PROMPT_TOKEN_RESERVATION_DEFINITION_SHA256
    ):
        raise RuntimePolicyError(
            "prompt token reservation definition SHA-256 does not match the locked implementation"
        )
    # Retained solely as an observational diagnostic.  Admission never uses it.
    chars_per_token = _required_float(raw, "prompt_chars_per_token", minimum=0.1)
    completion_reservation = _required_string(raw, "completion_token_reservation")
    if completion_reservation != "request_max_tokens":
        raise RuntimePolicyError(
            "completion_token_reservation must be 'request_max_tokens'"
        )
    lease_timeout = _required_float(raw, "lease_timeout_seconds", minimum=1.0)
    acquire_poll = _required_float(raw, "acquire_poll_seconds", minimum=0.01)

    retry_raw = _required_mapping(raw, "retry")
    _require_exact_keys(
        retry_raw,
        {
            "max_attempts",
            "retryable_http_statuses",
            "retry_transport_errors",
            "retry_invalid_json",
            "respect_retry_after",
            "base_delay_seconds",
            "multiplier",
            "max_backoff_seconds",
            "max_retry_after_seconds",
            "jitter_fraction",
        },
        field="runtime policy retry",
    )
    statuses_raw = retry_raw.get("retryable_http_statuses")
    if not isinstance(statuses_raw, list) or not statuses_raw:
        raise RuntimePolicyError("retry.retryable_http_statuses must be a non-empty list")
    statuses = tuple(sorted({_coerce_http_status(value) for value in statuses_raw}))
    retry = RetryPolicy(
        max_attempts=_required_int(retry_raw, "max_attempts", minimum=1),
        retryable_http_statuses=statuses,
        retry_transport_errors=_required_bool(retry_raw, "retry_transport_errors"),
        retry_invalid_json=_required_bool(retry_raw, "retry_invalid_json"),
        respect_retry_after=_required_bool(retry_raw, "respect_retry_after"),
        base_delay_seconds=_required_float(retry_raw, "base_delay_seconds", minimum=0.0),
        multiplier=_required_float(retry_raw, "multiplier", minimum=1.0),
        max_backoff_seconds=_required_float(retry_raw, "max_backoff_seconds", minimum=0.0),
        max_retry_after_seconds=_required_float(
            retry_raw, "max_retry_after_seconds", minimum=0.0
        ),
        jitter_fraction=_required_float(retry_raw, "jitter_fraction", minimum=0.0),
    )
    if retry.jitter_fraction > 1.0:
        raise RuntimePolicyError("retry.jitter_fraction must be <= 1.0")
    if retry.max_backoff_seconds < retry.base_delay_seconds:
        raise RuntimePolicyError(
            "retry.max_backoff_seconds must be >= retry.base_delay_seconds"
        )

    budget_raw = _required_mapping(raw, "budget")
    _require_exact_keys(
        budget_raw,
        {
            "minimum_preflight_start_credit_usd",
            "minimum_formal_start_remaining_usd",
            "maximum_preflight_cost_usd",
            "maximum_final_validation_cost_usd",
            "maximum_run_cost_usd",
            "maximum_single_request_cost_usd",
            "cost_cap_action",
            "unknown_actual_cost_action",
        },
        field="runtime policy budget",
    )
    budget = BudgetPolicy(
        minimum_preflight_start_credit_usd=_required_float(
            budget_raw, "minimum_preflight_start_credit_usd", minimum=0.0
        ),
        minimum_formal_start_remaining_usd=_required_float(
            budget_raw, "minimum_formal_start_remaining_usd", minimum=0.0
        ),
        maximum_preflight_cost_usd=_required_float(
            budget_raw, "maximum_preflight_cost_usd", minimum=0.01
        ),
        maximum_final_validation_cost_usd=_required_float(
            budget_raw, "maximum_final_validation_cost_usd", minimum=0.01
        ),
        maximum_run_cost_usd=_required_float(
            budget_raw, "maximum_run_cost_usd", minimum=0.01
        ),
        maximum_single_request_cost_usd=_required_float(
            budget_raw, "maximum_single_request_cost_usd", minimum=0.000001
        ),
        cost_cap_action=_required_string(budget_raw, "cost_cap_action"),
        unknown_actual_cost_action=_required_string(
            budget_raw, "unknown_actual_cost_action"
        ),
    )
    if budget.cost_cap_action not in {"record_only", "block_new_requests"}:
        raise RuntimePolicyError(
            "budget.cost_cap_action must be 'record_only' or 'block_new_requests'"
        )
    if budget.unknown_actual_cost_action != "charge_full_reservation":
        raise RuntimePolicyError(
            "budget.unknown_actual_cost_action must be 'charge_full_reservation'"
        )
    if budget.maximum_single_request_cost_usd > budget.maximum_run_cost_usd:
        raise RuntimePolicyError(
            "budget.maximum_single_request_cost_usd must not exceed maximum_run_cost_usd"
        )
    if budget.maximum_preflight_cost_usd > 120.0:
        raise RuntimePolicyError("budget.maximum_preflight_cost_usd must be <= 120")
    if (
        budget.maximum_final_validation_cost_usd
        > budget.maximum_preflight_cost_usd
    ):
        raise RuntimePolicyError(
            "final-validation budget must not exceed total preflight cap"
        )
    if (
        budget.minimum_preflight_start_credit_usd,
        budget.minimum_formal_start_remaining_usd,
        budget.maximum_preflight_cost_usd,
        budget.maximum_final_validation_cost_usd,
    ) != (
        REQUIRED_PREFLIGHT_START_CREDIT_USD,
        REQUIRED_FORMAL_START_REMAINING_USD,
        REQUIRED_PREFLIGHT_COST_CAP_USD,
        REQUIRED_FINAL_VALIDATION_BUDGET_USD,
    ):
        raise RuntimePolicyError(
            "runtime credit/preflight budgets differ from the locked AgentDojo envelope"
        )
    if (
        budget.minimum_preflight_start_credit_usd
        < budget.minimum_formal_start_remaining_usd
        + budget.maximum_preflight_cost_usd
    ):
        raise RuntimePolicyError(
            "preflight starting credit must preserve the formal floor after the full preflight cap"
        )

    ramp_raw = _required_mapping(raw, "ramp")
    _require_exact_keys(
        ramp_raw,
        {"worker_concurrency_stages", "promotion_requires"},
        field="runtime policy ramp",
    )
    stages_raw = ramp_raw.get("worker_concurrency_stages")
    if not isinstance(stages_raw, list) or not stages_raw:
        raise RuntimePolicyError("ramp.worker_concurrency_stages must be a non-empty list")
    stages = tuple(_coerce_positive_int(value, "ramp.worker_concurrency_stages") for value in stages_raw)
    if tuple(sorted(set(stages))) != stages:
        raise RuntimePolicyError(
            "ramp.worker_concurrency_stages must be unique and strictly increasing"
        )
    if lifecycle_status == "provisional":
        if stages[-1] != max_concurrent:
            raise RuntimePolicyError(
                "the provisional policy's final ramp.worker_concurrency_stages "
                "value must equal max_concurrent_requests"
            )
    else:
        if max_concurrent not in stages:
            raise RuntimePolicyError(
                "finalized max_concurrent_requests must be one locked attempted "
                "ramp stage"
            )
        if normalized_model_limits is None:
            raise RuntimePolicyError(
                "finalized runtime policy requires per-model safe limits"
            )
        if any(
            int(row["concurrent_requests"]) not in stages
            for row in normalized_model_limits.values()
        ):
            raise RuntimePolicyError(
                "per-model safe concurrency must be one locked ramp stage"
            )
        derived_global_concurrency = max(
            int(row["concurrent_requests"])
            for row in normalized_model_limits.values()
        )
        if max_concurrent != derived_global_concurrency:
            raise RuntimePolicyError(
                "finalized max_concurrent_requests must equal the maximum "
                "per-model safe concurrency under the locked serial-model invariant"
            )
    promotion = _required_mapping(ramp_raw, "promotion_requires")
    _require_exact_keys(
        promotion,
        {
            "credential_probe_http_200",
            "four_suite_canary_complete",
            "unresolved_http_429_or_503",
            "worker_failures",
            "sustained_swap",
            "max_cpu_percent",
            "max_memory_percent",
            "minimum_resource_samples",
            "minimum_active_request_fraction",
            "minimum_active_worker_fraction",
            "max_recovered_429_503_fraction",
            "max_consecutive_429_503",
            "max_retry_delay_seconds_per_chain",
            "threshold_breach_action",
        },
        field="runtime policy ramp.promotion_requires",
    )
    if not _required_bool(promotion, "credential_probe_http_200"):
        raise RuntimePolicyError("ramp promotion must require a successful credential probe")
    if not _required_bool(promotion, "four_suite_canary_complete"):
        raise RuntimePolicyError("ramp promotion must require four-suite canary completion")
    if _required_int(promotion, "unresolved_http_429_or_503", minimum=0) != 0:
        raise RuntimePolicyError("ramp promotion unresolved_http_429_or_503 must be zero")
    if _required_int(promotion, "worker_failures", minimum=0) != 0:
        raise RuntimePolicyError("ramp promotion worker_failures must be zero")
    if _required_bool(promotion, "sustained_swap"):
        raise RuntimePolicyError("ramp promotion sustained_swap must be false")
    ramp_max_cpu = _required_float(promotion, "max_cpu_percent", minimum=0.01)
    ramp_max_memory = _required_float(promotion, "max_memory_percent", minimum=0.01)
    if ramp_max_cpu > 100.0 or ramp_max_memory > 100.0:
        raise RuntimePolicyError("ramp CPU and memory thresholds must be <= 100")
    ramp_minimum_resource_samples = _required_int(
        promotion, "minimum_resource_samples", minimum=1
    )
    ramp_minimum_active_request_fraction = _required_float(
        promotion, "minimum_active_request_fraction", minimum=0.01
    )
    ramp_minimum_active_worker_fraction = _required_float(
        promotion, "minimum_active_worker_fraction", minimum=0.01
    )
    if (
        ramp_minimum_active_request_fraction > 1.0
        or ramp_minimum_active_worker_fraction > 1.0
    ):
        raise RuntimePolicyError("ramp active-utilization fractions must be <= 1.0")
    ramp_max_recovered_fraction = _required_float(
        promotion, "max_recovered_429_503_fraction", minimum=0.0
    )
    if ramp_max_recovered_fraction > 1.0:
        raise RuntimePolicyError("max_recovered_429_503_fraction must be <= 1.0")
    ramp_max_consecutive = _required_int(
        promotion, "max_consecutive_429_503", minimum=0
    )
    ramp_max_retry_delay_per_chain = _required_float(
        promotion, "max_retry_delay_seconds_per_chain", minimum=0.0
    )
    if _required_string(promotion, "threshold_breach_action") != "downgrade_and_continue":
        raise RuntimePolicyError(
            "ramp threshold_breach_action must be 'downgrade_and_continue'"
        )

    health = _required_mapping(raw, "health")
    _require_exact_keys(
        health,
        {"blind_monitoring_only_before_checklist_freeze", "forbidden_fields"},
        field="runtime policy health",
    )
    if not _required_bool(health, "blind_monitoring_only_before_checklist_freeze"):
        raise RuntimePolicyError("runtime health monitoring must remain blinded")
    forbidden = health.get("forbidden_fields")
    expected_forbidden = ["case_id", "prompt", "response", "trajectory", "evaluator", "label"]
    if forbidden != expected_forbidden:
        raise RuntimePolicyError(
            f"runtime health forbidden_fields must equal {expected_forbidden!r}"
        )

    return RuntimePolicy(
        raw=raw,
        semantic_sha256=semantic_sha256,
        operational_definition_sha256=operational_definition_sha256,
        policy_id=policy_id,
        lifecycle_status=lifecycle_status,
        measurement_receipt_path=measurement_path,
        measurement_receipt_sha256=measurement_sha,
        execution_key_fingerprint_sha256=key_fingerprint,
        per_model_safe_limits=normalized_model_limits,
        runtime_mode=runtime_mode,
        formal_execution_allowed=formal_execution_allowed,
        limiter_clock_definition_sha256=LIMITER_CLOCK_DEFINITION_SHA256,
        token_rate_units_definition_sha256=TOKEN_RATE_UNITS_DEFINITION_SHA256,
        max_concurrent_requests=max_concurrent,
        requests_per_minute=rpm,
        tokens_per_minute=tpm,
        rate_window_seconds=rate_window,
        prompt_token_reservation_definition_sha256=(
            prompt_reservation_definition_sha
        ),
        prompt_chars_per_token=chars_per_token,
        completion_token_reservation=completion_reservation,
        lease_timeout_seconds=lease_timeout,
        acquire_poll_seconds=acquire_poll,
        retry=retry,
        budget=budget,
        ramp_stages=stages,
        ramp_max_cpu_percent=ramp_max_cpu,
        ramp_max_memory_percent=ramp_max_memory,
        ramp_minimum_resource_samples=ramp_minimum_resource_samples,
        ramp_minimum_active_request_fraction=ramp_minimum_active_request_fraction,
        ramp_minimum_active_worker_fraction=ramp_minimum_active_worker_fraction,
        ramp_max_recovered_429_503_fraction=ramp_max_recovered_fraction,
        ramp_max_consecutive_429_503=ramp_max_consecutive,
        ramp_max_retry_delay_seconds_per_chain=ramp_max_retry_delay_per_chain,
    )


def estimate_request_tokens(payload: Mapping[str, Any], policy: RuntimePolicy) -> int:
    """Reserve a tokenizer-independent UTF-8 byte upper bound plus output ceiling."""

    if (
        policy.prompt_token_reservation_definition_sha256
        != PROMPT_TOKEN_RESERVATION_DEFINITION_SHA256
    ):
        raise RuntimePolicyError("prompt token reservation implementation drift")
    try:
        serialized = json.dumps(
            dict(payload),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RuntimePolicyError("request payload is not canonically JSON serializable") from exc
    prompt_tokens = max(1, len(serialized))
    try:
        max_tokens = max(0, int(payload.get("max_tokens") or 0))
    except (TypeError, ValueError) as exc:
        raise RuntimePolicyError("request max_tokens must be an integer") from exc
    reservation = prompt_tokens + max_tokens
    if reservation > policy.tokens_per_minute:
        raise RuntimePolicyError(
            "single request token reservation exceeds locked tokens_per_minute: "
            f"reservation={reservation} limit={policy.tokens_per_minute}"
        )
    return reservation


def agentdojo_model_config_sha256(
    *,
    agent_id: str,
    provider: str,
    model_id: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
    retry: int,
) -> str:
    """Canonical model/request configuration identity shared by plan and worker."""

    if provider != "openrouter":
        raise RuntimePolicyError("AgentDojo ramp model provider must be openrouter")
    return sha256_object(
        {
            "agent_id": agent_id,
            "provider": provider,
            "model_id": model_id.removeprefix("openrouter/"),
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "timeout_seconds": int(timeout_seconds),
            "retry": int(retry),
            "agentdojo_local_llm_top_p": AGENTDOJO_LOCAL_LLM_TOP_P,
            "agentdojo_local_llm_seed_policy_sha256": (
                AGENTDOJO_LOCAL_LLM_SEED_POLICY_SHA256
            ),
            "proxy_request_transform_sha256": (
                AGENTDOJO_PROXY_REQUEST_TRANSFORM_SHA256
            ),
        }
    )


def validate_starting_credit(
    policy: RuntimePolicy,
    *,
    available_credit_usd: float,
    probe_phase: str = "pre_ramp",
) -> float:
    """Fail a preflight before episodes if the locked credit floor is unmet."""

    required = required_credit_floor(policy, probe_phase=probe_phase)
    if available_credit_usd < required:
        raise RuntimeBudgetExceeded(
            "OpenRouter available credit is below the locked starting floor: "
            f"available={available_credit_usd:.2f} "
            f"required={required:.2f} phase={probe_phase}"
        )
    return required


def required_credit_floor(policy: RuntimePolicy, *, probe_phase: str) -> float:
    floors = {
        "pre_ramp": policy.budget.minimum_preflight_start_credit_usd,
        "pre_final_validation": (
            policy.budget.minimum_formal_start_remaining_usd
            + policy.budget.maximum_final_validation_cost_usd
        ),
        "post_ramp": policy.budget.minimum_formal_start_remaining_usd,
        "formal_start": policy.budget.minimum_formal_start_remaining_usd,
    }
    if probe_phase not in floors:
        raise RuntimePolicyError("credit probe phase is invalid")
    return float(floors[probe_phase])


def rate_only_override_snapshot(
    agent_roles: Mapping[str, Any],
    policy: RuntimePolicy,
    *,
    expected_agent_ids: Sequence[str] = ("Agent A", "Agent B", "Agent C"),
) -> dict[str, Any]:
    """Prove the runtime overlay changes concurrency and no model semantics.

    The immutable agent file supplies request semantics.  A separate runtime
    overlay may replace only RPM, TPM, and concurrency scheduling values.
    """

    source_concurrency: dict[str, int] = {}
    for agent_id in expected_agent_ids:
        role = agent_roles.get(agent_id)
        if not isinstance(role, Mapping):
            raise RuntimePolicyError(f"missing frozen agent role {agent_id}")
        rate_limit = role.get("rate_limit")
        if not isinstance(rate_limit, Mapping):
            raise RuntimePolicyError(f"{agent_id}.rate_limit must be an object")
        _require_exact_keys(
            rate_limit,
            {"requests_per_minute", "tokens_per_minute", "concurrent_requests"},
            field=f"{agent_id}.rate_limit",
        )
        base_values = dict(policy.raw["operational_override"]["base_values"])
        if _required_int(rate_limit, "requests_per_minute", minimum=1) != int(
            base_values["requests_per_minute"]
        ):
            raise RuntimePolicyError(f"{agent_id} base RPM differs from locked base snapshot")
        if _required_int(rate_limit, "tokens_per_minute", minimum=1) != int(
            base_values["tokens_per_minute"]
        ):
            raise RuntimePolicyError(f"{agent_id} base TPM differs from locked base snapshot")
        source_concurrency[agent_id] = _required_int(
            rate_limit, "concurrent_requests", minimum=1
        )
        if source_concurrency[agent_id] != int(
            base_values["concurrent_requests_per_agent"]
        ):
            raise RuntimePolicyError(
                f"{agent_id} base concurrency differs from locked base snapshot"
            )
    return {
        "schema_version": "agentdojo_openrouter_rate_only_override/v1",
        "override_fields": list(
            policy.raw["operational_override"]["allowed_fields"]
        ),
        "unchanged_fields": [
            "provider",
            "model",
            "model_version",
            "temperature",
            "max_tokens",
            "timeout_seconds",
            "retry",
        ],
        "source_concurrent_requests": source_concurrency,
        "effective_global_concurrent_requests": policy.max_concurrent_requests,
        "requests_per_minute": policy.requests_per_minute,
        "tokens_per_minute": policy.tokens_per_minute,
        "base_agents_config_file_sha256": policy.raw["operational_override"][
            "base_agents_config_file_sha256"
        ],
        "reason": policy.raw["operational_override"]["reason"],
        "runtime_policy_semantic_sha256": policy.semantic_sha256,
    }


def _normalize_openrouter_account_key_projection(
    payload: Mapping[str, Any], *, execution_key: bool
) -> dict[str, Any]:
    """Normalize only documented cross-endpoint fields used for account proof."""

    _require_exact_keys(
        payload,
        set(OPENROUTER_ACCOUNT_INVENTORY_MATCH_FIELDS),
        field="OpenRouter account-key projection",
    )
    normalized: dict[str, Any] = {}
    for field in ("creator_user_id", "label"):
        value = payload.get(field)
        if value is None and not execution_key:
            normalized[field] = None
        elif (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 512
            or "\n" in value
        ):
            raise RuntimePolicyError(
                f"OpenRouter account-key projection {field} is invalid"
            )
        else:
            normalized[field] = value.strip()
    for field in ("limit", "limit_remaining", "usage"):
        value = payload.get(field)
        if value is None and not execution_key:
            normalized[field] = None
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimePolicyError(
                f"OpenRouter account-key projection {field} must be numeric"
            )
        numeric = float(value)
        if not math.isfinite(numeric) or numeric < 0:
            raise RuntimePolicyError(
                f"OpenRouter account-key projection {field} is invalid"
            )
        normalized[field] = numeric
    reset = payload.get("limit_reset")
    if reset not in {None, "daily", "weekly", "monthly"}:
        raise RuntimePolicyError(
            "OpenRouter account-key projection limit_reset is invalid"
        )
    normalized["limit_reset"] = reset
    expires_at = payload.get("expires_at")
    if expires_at is not None and (
        not isinstance(expires_at, str)
        or not expires_at.strip()
        or len(expires_at) > 128
        or "\n" in expires_at
    ):
        raise RuntimePolicyError(
            "OpenRouter account-key projection expires_at is invalid"
        )
    normalized["expires_at"] = None if expires_at is None else expires_at.strip()
    if execution_key:
        if normalized["limit_reset"] is not None:
            raise RuntimePolicyError(
                "dedicated execution key inventory projection requires limit_reset=null"
            )
        if float(normalized["limit_remaining"]) > float(normalized["limit"]) + (
            OPENROUTER_ACCOUNT_INVENTORY_FLOAT_ABS_TOLERANCE
        ):
            raise RuntimePolicyError(
                "execution key inventory projection has remaining above limit"
            )
    return normalized


def _openrouter_account_projections_match(
    expected: Mapping[str, Any], observed: Mapping[str, Any]
) -> bool:
    for field in OPENROUTER_ACCOUNT_INVENTORY_MATCH_FIELDS:
        left = expected[field]
        right = observed[field]
        if field in {"limit", "limit_remaining", "usage"}:
            if left is None or right is None:
                if left is not right:
                    return False
            elif not math.isclose(
                float(left),
                float(right),
                rel_tol=OPENROUTER_ACCOUNT_INVENTORY_FLOAT_REL_TOLERANCE,
                abs_tol=OPENROUTER_ACCOUNT_INVENTORY_FLOAT_ABS_TOLERANCE,
            ):
                return False
        elif left != right:
            return False
    return True


def _normalize_openrouter_inventory_pages(
    page_receipts: Sequence[Mapping[str, Any]], *, expected_inventory_count: int
) -> list[dict[str, Any]]:
    if (
        not page_receipts
        or len(page_receipts) > OPENROUTER_ACCOUNT_INVENTORY_MAX_PAGES
    ):
        raise RuntimePolicyError(
            "OpenRouter management key inventory pagination is empty or exceeds its hard limit"
        )
    pages: list[dict[str, Any]] = []
    expected_offset = 0
    seen_page_digests: set[str] = set()
    for page_ordinal, raw_page in enumerate(page_receipts):
        _require_exact_keys(
            raw_page,
            {"offset", "count", "canonical_response_sha256"},
            field="OpenRouter account inventory page receipt",
        )
        offset = _strict_nonnegative_int(
            raw_page.get("offset"), "OpenRouter inventory offset"
        )
        count = _strict_nonnegative_int(
            raw_page.get("count"), "OpenRouter inventory page count"
        )
        if count > OPENROUTER_ACCOUNT_INVENTORY_PAGE_SIZE:
            raise RuntimePolicyError(
                "OpenRouter management inventory page exceeds the documented 100-row page"
            )
        if offset != expected_offset:
            raise RuntimePolicyError(
                "OpenRouter management inventory offsets are not contiguous"
            )
        if page_ordinal < len(page_receipts) - 1 and count != (
            OPENROUTER_ACCOUNT_INVENTORY_PAGE_SIZE
        ):
            raise RuntimePolicyError(
                "OpenRouter inventory pagination continued after a short page"
            )
        page_digest = _validate_digest(
            str(raw_page.get("canonical_response_sha256") or ""),
            "OpenRouter inventory canonical response SHA-256",
        )
        if page_digest in seen_page_digests:
            raise RuntimePolicyError(
                "OpenRouter management inventory repeated a canonical page"
            )
        seen_page_digests.add(page_digest)
        pages.append(
            {
                "offset": offset,
                "count": count,
                "canonical_response_sha256": page_digest,
            }
        )
        expected_offset += count
    if pages[-1]["count"] >= OPENROUTER_ACCOUNT_INVENTORY_PAGE_SIZE:
        raise RuntimePolicyError(
            "OpenRouter management inventory did not reach a terminating short page"
        )
    if expected_offset != expected_inventory_count:
        raise RuntimePolicyError(
            "OpenRouter management inventory count differs from its page receipts"
        )
    return pages


def build_same_account_inventory_proof(
    *,
    execution_key_projection: Mapping[str, Any],
    inventory_key_projections: Sequence[Mapping[str, Any]],
    page_receipts: Sequence[Mapping[str, Any]],
    auth_lifecycle_lock_path: str | Path,
) -> dict[str, Any]:
    """Build a content-free proof that both credentials address one account."""

    execution_projection = _normalize_openrouter_account_key_projection(
        execution_key_projection, execution_key=True
    )
    normalized_inventory = [
        _normalize_openrouter_account_key_projection(row, execution_key=False)
        for row in inventory_key_projections
    ]
    pages = _normalize_openrouter_inventory_pages(
        page_receipts, expected_inventory_count=len(normalized_inventory)
    )
    matching = [
        row
        for row in normalized_inventory
        if _openrouter_account_projections_match(execution_projection, row)
    ]
    if not matching:
        raise RuntimePolicyError(
            "execution key is absent from the default management workspace inventory; "
            "a default-workspace management key is required"
        )
    if len(matching) != 1:
        raise RuntimePolicyError(
            "execution key projection is not unique in the management account inventory"
        )
    execution_projection_sha = sha256_object(execution_projection)
    matched_projection_sha = sha256_object(matching[0])
    match_core = {
        "execution_key_projection_sha256": execution_projection_sha,
        "matched_inventory_projection_sha256": matched_projection_sha,
        "page_receipts": pages,
        "inventory_entry_count": len(normalized_inventory),
        "unique_match_count": 1,
    }
    proof = {
        "schema_version": "agentdojo_openrouter_same_account_inventory_proof/v1",
        "method": "management_get_keys_inventory_unique_projection_match/v1",
        "endpoint": "GET /api/v1/keys?offset={offset}&include_disabled=true",
        "default_workspace_required": True,
        "default_workspace_unique_match_verified": True,
        "include_disabled": True,
        "page_size": OPENROUTER_ACCOUNT_INVENTORY_PAGE_SIZE,
        "hard_page_limit": OPENROUTER_ACCOUNT_INVENTORY_MAX_PAGES,
        "pagination_termination": "offset_plus_equals_len_page_until_len_page_lt_100",
        "repeated_page_detection": True,
        "page_count": len(pages),
        "inventory_entry_count": len(normalized_inventory),
        "page_receipts": pages,
        "match_fields": list(OPENROUTER_ACCOUNT_INVENTORY_MATCH_FIELDS),
        "float_match_tolerance": {
            "absolute": OPENROUTER_ACCOUNT_INVENTORY_FLOAT_ABS_TOLERANCE,
            "relative": OPENROUTER_ACCOUNT_INVENTORY_FLOAT_REL_TOLERANCE,
        },
        "execution_key_projection_sha256": execution_projection_sha,
        "matched_inventory_projection_sha256": matched_projection_sha,
        "unique_match_count": 1,
        "match_digest_sha256": sha256_object(match_core),
        "provider_or_raw_key_hash_comparison_used": False,
        "inventory_rows_labels_or_provider_key_hashes_recorded": False,
        "critical_section": {
            "controller_lifecycle_lock_path": _portable_path(
                Path(auth_lifecycle_lock_path)
            ),
            "lock_mode": "exclusive",
            "covers_execution_key_inventory_credits_and_catalog_queries": True,
            "controller_stage_launch_and_supervisor_lifecycle_blocked": True,
            "remote_inference_blocked_by_controller_flock": False,
            "remote_quiescence_receipts_required": True,
            "execution_usage_quiescence_requires_bound_remote_receipts": True,
        },
    }
    return validate_same_account_inventory_proof(proof)


def validate_same_account_inventory_proof(
    proof: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_keys(
        proof,
        {
            "schema_version",
            "method",
            "endpoint",
            "default_workspace_required",
            "default_workspace_unique_match_verified",
            "include_disabled",
            "page_size",
            "hard_page_limit",
            "pagination_termination",
            "repeated_page_detection",
            "page_count",
            "inventory_entry_count",
            "page_receipts",
            "match_fields",
            "float_match_tolerance",
            "execution_key_projection_sha256",
            "matched_inventory_projection_sha256",
            "unique_match_count",
            "match_digest_sha256",
            "provider_or_raw_key_hash_comparison_used",
            "inventory_rows_labels_or_provider_key_hashes_recorded",
            "critical_section",
        },
        field="OpenRouter same-account inventory proof",
    )
    constants = {
        "schema_version": "agentdojo_openrouter_same_account_inventory_proof/v1",
        "method": "management_get_keys_inventory_unique_projection_match/v1",
        "endpoint": "GET /api/v1/keys?offset={offset}&include_disabled=true",
        "default_workspace_required": True,
        "default_workspace_unique_match_verified": True,
        "include_disabled": True,
        "page_size": OPENROUTER_ACCOUNT_INVENTORY_PAGE_SIZE,
        "hard_page_limit": OPENROUTER_ACCOUNT_INVENTORY_MAX_PAGES,
        "pagination_termination": "offset_plus_equals_len_page_until_len_page_lt_100",
        "repeated_page_detection": True,
        "match_fields": list(OPENROUTER_ACCOUNT_INVENTORY_MATCH_FIELDS),
        "float_match_tolerance": {
            "absolute": OPENROUTER_ACCOUNT_INVENTORY_FLOAT_ABS_TOLERANCE,
            "relative": OPENROUTER_ACCOUNT_INVENTORY_FLOAT_REL_TOLERANCE,
        },
        "unique_match_count": 1,
        "provider_or_raw_key_hash_comparison_used": False,
        "inventory_rows_labels_or_provider_key_hashes_recorded": False,
    }
    for field, expected in constants.items():
        if proof.get(field) != expected:
            raise RuntimePolicyError(
                f"OpenRouter same-account inventory proof {field} differs"
            )
    page_count = _strict_nonnegative_int(
        proof.get("page_count"), "OpenRouter inventory page_count", minimum=1
    )
    inventory_count = _strict_nonnegative_int(
        proof.get("inventory_entry_count"),
        "OpenRouter inventory entry count",
        minimum=1,
    )
    raw_pages = proof.get("page_receipts")
    if not isinstance(raw_pages, list) or len(raw_pages) != page_count:
        raise RuntimePolicyError(
            "OpenRouter inventory page_count differs from page receipts"
        )
    pages = _normalize_openrouter_inventory_pages(
        raw_pages, expected_inventory_count=inventory_count
    )
    critical = proof.get("critical_section")
    if not isinstance(critical, Mapping):
        raise RuntimePolicyError("OpenRouter inventory critical section is invalid")
    _require_exact_keys(
        critical,
        {
            "controller_lifecycle_lock_path",
            "lock_mode",
            "covers_execution_key_inventory_credits_and_catalog_queries",
            "controller_stage_launch_and_supervisor_lifecycle_blocked",
            "remote_inference_blocked_by_controller_flock",
            "remote_quiescence_receipts_required",
            "execution_usage_quiescence_requires_bound_remote_receipts",
        },
        field="OpenRouter inventory critical section",
    )
    lock_path = critical.get("controller_lifecycle_lock_path")
    if (
        not isinstance(lock_path, str)
        or not lock_path
        or critical.get("lock_mode") != "exclusive"
        or critical.get("covers_execution_key_inventory_credits_and_catalog_queries")
        is not True
        or critical.get(
            "controller_stage_launch_and_supervisor_lifecycle_blocked"
        )
        is not True
        or critical.get("remote_inference_blocked_by_controller_flock") is not False
        or critical.get("remote_quiescence_receipts_required") is not True
        or critical.get(
            "execution_usage_quiescence_requires_bound_remote_receipts"
        )
        is not True
    ):
        raise RuntimePolicyError(
            "OpenRouter inventory critical-section semantics differ"
        )
    execution_sha = _validate_digest(
        str(proof.get("execution_key_projection_sha256") or ""),
        "execution key projection SHA-256",
    )
    matched_sha = _validate_digest(
        str(proof.get("matched_inventory_projection_sha256") or ""),
        "matched inventory projection SHA-256",
    )
    expected_match_digest = sha256_object(
        {
            "execution_key_projection_sha256": execution_sha,
            "matched_inventory_projection_sha256": matched_sha,
            "page_receipts": pages,
            "inventory_entry_count": inventory_count,
            "unique_match_count": 1,
        }
    )
    if proof.get("match_digest_sha256") != expected_match_digest:
        raise RuntimePolicyError("OpenRouter inventory match digest is inconsistent")
    return json.loads(json.dumps(dict(proof), ensure_ascii=True))


def build_credential_probe_receipt(
    policy: RuntimePolicy,
    *,
    runtime_infra_file_sha256: str,
    http_status: int,
    key_limit_usd: float | None,
    key_limit_remaining_usd: float | None,
    key_usage_usd: float,
    key_is_free_tier: bool,
    key_is_management: bool,
    key_is_provisioning: bool,
    key_disabled: bool | None,
    key_disabled_field_present: bool,
    key_limit_reset_policy: str | None,
    key_expires_at: str | None,
    model_catalog_entries: Sequence[Mapping[str, Any]],
    credential_fingerprint_sha256: str,
    provider_limit_mode: str | None = None,
    management_audit_fingerprint_sha256: str | None = None,
    management_key_identity_sha256: str | None = None,
    management_key_is_management: bool | None = None,
    management_key_is_provisioning: bool | None = None,
    management_key_disabled: bool | None = None,
    same_account_inventory_proof: Mapping[str, Any] | None = None,
    account_total_credits_usd: float | None = None,
    account_total_usage_usd: float | None = None,
    management_audit_status: str | None = None,
    round_plan_path: str | Path | None = None,
    probe_phase: str = "pre_ramp",
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a content-free passing receipt; failed probes never create one."""

    inferred_limit_mode = (
        "unlimited_no_provider_cap"
        if key_limit_usd is None and key_limit_remaining_usd is None
        else "explicit_cap"
        if key_limit_usd is not None and key_limit_remaining_usd is not None
        else "invalid"
    )
    if provider_limit_mode is None:
        provider_limit_mode = inferred_limit_mode
    if (
        provider_limit_mode
        not in {"explicit_cap", "unlimited_no_provider_cap"}
        or provider_limit_mode != inferred_limit_mode
    ):
        raise RuntimePolicyError(
            "provider limit mode differs from limit/limit_remaining nullability"
        )
    if provider_limit_mode == "explicit_cap":
        assert key_limit_remaining_usd is not None
        key_cap_floor: float | None = validate_starting_credit(
            policy,
            available_credit_usd=key_limit_remaining_usd,
            probe_phase=probe_phase,
        )
        credit_floor_proof_status = "verified_from_provider_key_cap"
        credit_floor_waiver_reason = None
    else:
        key_cap_floor = None
        credit_floor_proof_status = "waived_by_user_provider_balance_unavailable"
        credit_floor_waiver_reason = (
            "provider_unlimited_key_exposes_no_limit_remaining_balance"
        )
    if management_audit_status is None:
        management_audit_status = (
            "performed"
            if management_key_identity_sha256 is not None
            else "waived_by_user"
        )
    if management_audit_status not in {"waived_by_user", "performed"}:
        raise RuntimePolicyError("management_audit_status is invalid")
    performed_management_audit = management_audit_status == "performed"
    if performed_management_audit:
        if account_total_credits_usd is None or account_total_usage_usd is None:
            raise RuntimePolicyError(
                "performed management audit requires account credit fields"
            )
        account_remaining_usd: float | None = float(
            account_total_credits_usd
        ) - float(account_total_usage_usd)
        account_floor: float | None = validate_starting_credit(
            policy,
            available_credit_usd=account_remaining_usd,
            probe_phase=probe_phase,
        )
    else:
        account_remaining_usd = None
        account_floor = None
    if key_is_free_tier is not False:
        raise RuntimePolicyError("OpenRouter credential must not be a free-tier key")
    if key_is_management is not False or key_is_provisioning is not False:
        raise RuntimePolicyError(
            "OpenRouter execution credential must be neither management nor provisioning"
        )
    if performed_management_audit:
        if (
            management_key_is_management is not True
            or management_key_is_provisioning is not False
        ):
            raise RuntimePolicyError(
                "OpenRouter account audit requires a management-only, non-provisioning key"
            )
        if management_key_disabled is True:
            raise RuntimePolicyError("OpenRouter management audit credential is disabled")
    elif any(
        value is not None
        for value in (
            management_audit_fingerprint_sha256,
            management_key_identity_sha256,
            management_key_is_management,
            management_key_is_provisioning,
            management_key_disabled,
            same_account_inventory_proof,
            account_total_credits_usd,
            account_total_usage_usd,
        )
    ):
        raise RuntimePolicyError(
            "waived management audit must not contain management-key/account claims"
        )
    if key_disabled is True:
        raise RuntimePolicyError("OpenRouter execution credential is disabled")
    if bool(key_disabled_field_present) != (key_disabled is not None):
        raise RuntimePolicyError("OpenRouter disabled-field presence/value is inconsistent")
    if key_limit_reset_policy not in {None, "daily", "weekly", "monthly"}:
        raise RuntimePolicyError("OpenRouter key limit_reset policy is invalid")
    if key_limit_reset_policy is not None:
        raise RuntimePolicyError(
            "dedicated execution key must use limit_reset=null for run-stable funding"
        )
    for label, value in (("key_usage_usd", key_usage_usd),):
        if not math.isfinite(float(value)) or float(value) < 0:
            raise RuntimePolicyError(f"{label} must be finite and non-negative")
    if provider_limit_mode == "explicit_cap":
        assert key_limit_usd is not None and key_limit_remaining_usd is not None
        for label, value in (
            ("key_limit_usd", key_limit_usd),
            ("key_limit_remaining_usd", key_limit_remaining_usd),
        ):
            if not math.isfinite(float(value)) or float(value) < 0:
                raise RuntimePolicyError(f"{label} must be finite and non-negative")
        if key_limit_remaining_usd > key_limit_usd + 1e-9:
            raise RuntimePolicyError(
                "OpenRouter key limit_remaining exceeds its explicit limit"
            )
        if abs((key_limit_usd - key_usage_usd) - key_limit_remaining_usd) > 0.02:
            raise RuntimePolicyError(
                "OpenRouter key limit/usage/limit_remaining fields are inconsistent"
            )
    expires_at = _optional_future_timestamp(key_expires_at, field="key_expires_at")
    catalog = _normalize_required_model_catalog(model_catalog_entries)
    execution_fingerprint = _validate_digest(
        credential_fingerprint_sha256, "credential_fingerprint_sha256"
    )
    management_identity: str | None = None
    management_fingerprint: str | None = None
    account_inventory_proof: dict[str, Any] | None = None
    if performed_management_audit:
        management_identity = _validate_digest(
            str(management_key_identity_sha256 or ""),
            "management_key_identity_sha256",
        )
        management_fingerprint = _validate_digest(
            str(management_audit_fingerprint_sha256 or ""),
            "management_audit_fingerprint_sha256",
        )
        if execution_fingerprint == management_identity:
            raise RuntimePolicyError(
                "execution and management audit keys must be distinct"
            )
        account_inventory_proof = validate_same_account_inventory_proof(
            dict(same_account_inventory_proof or {})
        )
    round_plan_ref: dict[str, str] | None = None
    if round_plan_path is not None:
        from evidence_system.contracts.agentdojo_rate_lifecycle import (
            load_disposable_round_plan,
        )

        round_plan_file = _regular_nonsymlink_file(
            round_plan_path, "credential round plan"
        )
        round_plan = load_disposable_round_plan(round_plan_file)
        round_definition = dict(round_plan["definition"])
        expected_kind = (
            "exploratory_measurement"
            if probe_phase == "pre_ramp"
            else "finalized_validation"
        )
        if (
            round_definition["round_kind"] != expected_kind
            or round_definition["runtime_policy"]["semantic_sha256"]
            != policy.semantic_sha256
            or round_definition["runtime_infra"]["sha256"]
            != runtime_infra_file_sha256.removeprefix("sha256:")
        ):
            raise RuntimePolicyError("credential probe uses the wrong disposable round")
        if performed_management_audit and account_inventory_proof is not None and account_inventory_proof["critical_section"][
            "controller_lifecycle_lock_path"
        ] != str(round_plan["artifact_namespace"]["controller_lifecycle_lock"]):
            raise RuntimePolicyError(
                "credential account proof used a different auth lifecycle lock"
            )
        round_plan_ref = {
            **_locked_file_ref(round_plan_file),
            "definition_sha256": str(round_plan["definition_sha256"]),
        }
    if int(http_status) != 200:
        raise RuntimePolicyError("credential probe receipt requires HTTP 200")
    if probe_phase not in {"pre_ramp", "pre_final_validation", "post_ramp"}:
        raise RuntimePolicyError("credential probe_phase is invalid")
    _validate_digest(runtime_infra_file_sha256, "runtime_infra_file_sha256")
    payload = {
        "schema_version": CREDENTIAL_PROBE_RECEIPT_SCHEMA_VERSION,
        "status": "passed",
        "created_at": _validated_timestamp(created_at),
        "probe_phase": probe_phase,
        "http_status": 200,
        "secret_material_recorded": False,
        "response_body_recorded": False,
        "credential_fingerprint_algorithm": (
            "sha256(agentdojo-openrouter-key/v1\\0 || utf8_key_bytes)"
        ),
        "credential_fingerprint_sha256": _validate_digest(
            execution_fingerprint,
            "credential_fingerprint_sha256",
        ),
        "management_audit_status": management_audit_status,
        "management_audit_waiver_reason": (
            None
            if performed_management_audit
            else "waived_by_user_execution_key_only"
        ),
        "management_audit_fingerprint_algorithm": (
            "sha256(agentdojo-openrouter-management-audit-key/v1\\0 || utf8_key_bytes)"
            if performed_management_audit
            else None
        ),
        "management_audit_fingerprint_sha256": management_fingerprint,
        "management_key_identity_sha256": management_identity,
        "round_plan": round_plan_ref,
        "runtime_policy_semantic_sha256": policy.semantic_sha256,
        "runtime_infra_file_sha256": runtime_infra_file_sha256.removeprefix("sha256:"),
        "provider_limit_mode": provider_limit_mode,
        "key_limit_usd": (
            None if key_limit_usd is None else float(key_limit_usd)
        ),
        "key_limit_remaining_usd": (
            None
            if key_limit_remaining_usd is None
            else float(key_limit_remaining_usd)
        ),
        "key_usage_usd": float(key_usage_usd),
        "key_limit_remaining_floor_usd": key_cap_floor,
        "key_limit_remaining_floor_formula": (
            {
                "pre_ramp": "minimum_preflight_start_credit_usd",
                "pre_final_validation": (
                    "minimum_formal_start_remaining_usd + maximum_final_validation_cost_usd"
                ),
                "post_ramp": "minimum_formal_start_remaining_usd",
            }[probe_phase]
            if provider_limit_mode == "explicit_cap"
            else None
        ),
        "credit_floor_proof_status": credit_floor_proof_status,
        "credit_floor_waiver_reason": credit_floor_waiver_reason,
        "local_software_run_cost_cap_usd": float(
            policy.budget.maximum_run_cost_usd
        ),
        "local_software_cost_cap_action": policy.budget.cost_cap_action,
        "budget_policy": {
            "minimum_preflight_start_credit_usd": (
                policy.budget.minimum_preflight_start_credit_usd
            ),
            "minimum_formal_start_remaining_usd": (
                policy.budget.minimum_formal_start_remaining_usd
            ),
            "maximum_preflight_cost_usd": policy.budget.maximum_preflight_cost_usd,
            "maximum_final_validation_cost_usd": (
                policy.budget.maximum_final_validation_cost_usd
            ),
            "maximum_formal_run_cost_usd": policy.budget.maximum_run_cost_usd,
        },
        "budget_policy_sha256": sha256_object(dict(policy.raw["budget"])),
        "key_is_free_tier": False,
        "key_is_management": False,
        "key_is_provisioning": False,
        "key_disabled": key_disabled,
        "key_disabled_field_present": bool(key_disabled_field_present),
        "key_limit_reset_policy": None,
        "key_expires_at": expires_at,
        "account_total_funding_independently_observable": performed_management_audit,
        "funding_semantics": (
            "execution_key_cap_plus_management_key_account_credits/v1"
            if performed_management_audit
            else "execution_key_limit_only_user_waiver/v1"
        ),
        "account_balance_endpoint": (
            "GET /api/v1/credits" if performed_management_audit else None
        ),
        "account_total_credits_usd": (
            float(account_total_credits_usd)
            if account_total_credits_usd is not None
            else None
        ),
        "account_total_usage_usd": (
            float(account_total_usage_usd)
            if account_total_usage_usd is not None
            else None
        ),
        "account_remaining_usd": account_remaining_usd,
        "account_remaining_floor_usd": account_floor,
        "account_balance_verified": performed_management_audit,
        "management_key_is_management": management_key_is_management,
        "management_key_is_provisioning": management_key_is_provisioning,
        "management_key_disabled": management_key_disabled,
        "management_key_local_probe_only": True,
        "management_key_deployed_to_vps": False,
        "same_account_inventory_proof": account_inventory_proof,
        "successful_non_402_canary_required": True,
        "deprecated_rate_limit_used": False,
        "models_available": list(REQUIRED_MODELS),
        "model_catalog": catalog,
        "model_catalog_sha256": sha256_object(catalog),
    }
    validate_object("agentdojo_openrouter_credential_probe_receipt", payload)
    return payload


def load_credential_probe_receipt(
    path: str | Path,
    *,
    expected_policy_sha256: str,
    expected_runtime_infra_file_sha256: str | None = None,
    expected_probe_phase: str | None = None,
) -> dict[str, Any]:
    receipt = _load_receipt(path, "agentdojo_openrouter_credential_probe_receipt")
    _require_receipt_binding(
        receipt,
        expected_policy_sha256=expected_policy_sha256,
        expected_runtime_infra_file_sha256=expected_runtime_infra_file_sha256,
    )
    if expected_probe_phase is not None and receipt.get("probe_phase") != expected_probe_phase:
        raise RuntimePolicyError("credential receipt probe phase mismatch")
    if tuple(receipt["models_available"]) != REQUIRED_MODELS:
        raise RuntimePolicyError("credential receipt frozen model list/order mismatch")
    if receipt.get("credential_fingerprint_algorithm") != (
        "sha256(agentdojo-openrouter-key/v1\\0 || utf8_key_bytes)"
    ):
        raise RuntimePolicyError("credential fingerprint algorithm differs")
    _validate_digest(
        str(receipt.get("credential_fingerprint_sha256") or ""),
        "credential_fingerprint_sha256",
    )
    round_plan_ref = receipt.get("round_plan")
    management_status = str(receipt.get("management_audit_status") or "")
    if management_status not in {"waived_by_user", "performed"}:
        raise RuntimePolicyError("credential receipt management audit status is invalid")
    performed_management_audit = management_status == "performed"
    inventory_proof = (
        validate_same_account_inventory_proof(
            dict(receipt.get("same_account_inventory_proof") or {})
        )
        if performed_management_audit
        else None
    )
    if round_plan_ref is not None:
        if not isinstance(round_plan_ref, Mapping):
            raise RuntimePolicyError("credential round_plan reference is invalid")
        from evidence_system.contracts.agentdojo_rate_lifecycle import (
            load_disposable_round_plan,
        )

        round_plan_path = _regular_nonsymlink_file(
            str(round_plan_ref.get("path") or ""), "credential round plan"
        )
        if round_plan_ref.get("sha256") != sha256_file(round_plan_path):
            raise RuntimePolicyError("credential round-plan file hash is stale")
        round_plan = load_disposable_round_plan(round_plan_path)
        if round_plan_ref.get("definition_sha256") != round_plan["definition_sha256"]:
            raise RuntimePolicyError("credential round-plan definition hash differs")
        if performed_management_audit and inventory_proof is not None and inventory_proof["critical_section"][
            "controller_lifecycle_lock_path"
        ] != str(round_plan["artifact_namespace"]["controller_lifecycle_lock"]):
            raise RuntimePolicyError(
                "credential account proof auth lock differs from its round plan"
            )
    provider_limit_mode = str(receipt.get("provider_limit_mode") or "")
    if provider_limit_mode not in {"explicit_cap", "unlimited_no_provider_cap"}:
        raise RuntimePolicyError("credential receipt provider limit mode is invalid")
    phase = str(receipt.get("probe_phase") or "")
    expected_floors = {
        "pre_ramp": REQUIRED_PREFLIGHT_START_CREDIT_USD,
        "pre_final_validation": (
            REQUIRED_FORMAL_START_REMAINING_USD
            + REQUIRED_FINAL_VALIDATION_BUDGET_USD
        ),
        "post_ramp": REQUIRED_FORMAL_START_REMAINING_USD,
    }
    expected_formulas = {
        "pre_ramp": "minimum_preflight_start_credit_usd",
        "pre_final_validation": (
            "minimum_formal_start_remaining_usd + maximum_final_validation_cost_usd"
        ),
        "post_ramp": "minimum_formal_start_remaining_usd",
    }
    if phase not in expected_floors:
        raise RuntimePolicyError("credential receipt probe phase is invalid")
    if provider_limit_mode == "explicit_cap":
        if (
            float(receipt["key_limit_remaining_usd"])
            < float(receipt["key_limit_remaining_floor_usd"])
            or float(receipt["key_limit_remaining_floor_usd"])
            != float(expected_floors[phase])
            or receipt.get("key_limit_remaining_floor_formula")
            != expected_formulas[phase]
            or receipt.get("credit_floor_proof_status")
            != "verified_from_provider_key_cap"
            or receipt.get("credit_floor_waiver_reason") is not None
        ):
            raise RuntimePolicyError(
                "credential receipt explicit-cap floor proof differs"
            )
    elif (
        receipt.get("key_limit_usd") is not None
        or receipt.get("key_limit_remaining_usd") is not None
        or receipt.get("key_limit_remaining_floor_usd") is not None
        or receipt.get("key_limit_remaining_floor_formula") is not None
        or receipt.get("credit_floor_proof_status")
        != "waived_by_user_provider_balance_unavailable"
        or receipt.get("credit_floor_waiver_reason")
        != "provider_unlimited_key_exposes_no_limit_remaining_balance"
    ):
        raise RuntimePolicyError(
            "credential receipt unlimited-key waiver semantics differ"
        )
    expected_budget = {
        "minimum_preflight_start_credit_usd": REQUIRED_PREFLIGHT_START_CREDIT_USD,
        "minimum_formal_start_remaining_usd": REQUIRED_FORMAL_START_REMAINING_USD,
        "maximum_preflight_cost_usd": REQUIRED_PREFLIGHT_COST_CAP_USD,
        "maximum_final_validation_cost_usd": REQUIRED_FINAL_VALIDATION_BUDGET_USD,
        "maximum_formal_run_cost_usd": REQUIRED_FORMAL_START_REMAINING_USD,
    }
    if receipt.get("budget_policy") != expected_budget:
        raise RuntimePolicyError("credential receipt budget-policy projection differs")
    if (
        float(receipt.get("local_software_run_cost_cap_usd") or 0)
        != REQUIRED_FORMAL_START_REMAINING_USD
        or receipt.get("local_software_cost_cap_action") != "block_new_requests"
    ):
        raise RuntimePolicyError("credential receipt local software cost cap differs")
    _validate_digest(
        str(receipt.get("budget_policy_sha256") or ""),
        "credential budget_policy_sha256",
    )
    if receipt.get("key_is_free_tier") is not False:
        raise RuntimePolicyError("credential receipt is free-tier")
    if (
        receipt.get("key_is_management") is not False
        or receipt.get("key_is_provisioning") is not False
        or receipt.get("key_disabled") is True
        or receipt.get("key_limit_reset_policy") is not None
        or receipt.get("management_key_local_probe_only") is not True
        or receipt.get("management_key_deployed_to_vps") is not False
        or receipt.get("successful_non_402_canary_required") is not True
    ):
        raise RuntimePolicyError("credential receipt execution-key semantics differ")
    if performed_management_audit:
        if (
            receipt.get("management_audit_waiver_reason") is not None
            or receipt.get("management_audit_fingerprint_algorithm")
            != "sha256(agentdojo-openrouter-management-audit-key/v1\\0 || utf8_key_bytes)"
            or receipt.get("account_total_funding_independently_observable") is not True
            or receipt.get("funding_semantics")
            != "execution_key_cap_plus_management_key_account_credits/v1"
            or receipt.get("account_balance_verified") is not True
            or receipt.get("account_balance_endpoint") != "GET /api/v1/credits"
            or receipt.get("management_key_is_management") is not True
            or receipt.get("management_key_is_provisioning") is not False
            or receipt.get("management_key_disabled") is True
        ):
            raise RuntimePolicyError("performed management audit semantics differ")
        _validate_digest(
            str(receipt.get("management_audit_fingerprint_sha256") or ""),
            "management_audit_fingerprint_sha256",
        )
        management_identity = _validate_digest(
            str(receipt.get("management_key_identity_sha256") or ""),
            "management_key_identity_sha256",
        )
        if management_identity == receipt["credential_fingerprint_sha256"]:
            raise RuntimePolicyError(
                "execution and management audit keys must be distinct"
            )
    else:
        if (
            receipt.get("management_audit_waiver_reason")
            != "waived_by_user_execution_key_only"
            or receipt.get("management_audit_fingerprint_algorithm") is not None
            or receipt.get("management_audit_fingerprint_sha256") is not None
            or receipt.get("management_key_identity_sha256") is not None
            or receipt.get("account_total_funding_independently_observable") is not False
            or receipt.get("funding_semantics")
            != "execution_key_limit_only_user_waiver/v1"
            or receipt.get("account_balance_endpoint") is not None
            or receipt.get("account_total_credits_usd") is not None
            or receipt.get("account_total_usage_usd") is not None
            or receipt.get("account_remaining_usd") is not None
            or receipt.get("account_remaining_floor_usd") is not None
            or receipt.get("account_balance_verified") is not False
            or receipt.get("management_key_is_management") is not None
            or receipt.get("management_key_is_provisioning") is not None
            or receipt.get("management_key_disabled") is not None
            or receipt.get("same_account_inventory_proof") is not None
        ):
            raise RuntimePolicyError(
                "waived management audit contains a false account/management claim"
            )
    usage_value = float(receipt["key_usage_usd"])
    if not math.isfinite(usage_value) or usage_value < 0:
        raise RuntimePolicyError("credential receipt key funding fields are inconsistent")
    if provider_limit_mode == "explicit_cap":
        limit_value = float(receipt["key_limit_usd"])
        remaining_value = float(receipt["key_limit_remaining_usd"])
        if (
            not all(
                math.isfinite(value) and value >= 0
                for value in (limit_value, remaining_value)
            )
            or remaining_value > limit_value + 1e-9
            or abs((limit_value - usage_value) - remaining_value) > 0.02
        ):
            raise RuntimePolicyError(
                "credential receipt explicit key funding fields are inconsistent"
            )
    if performed_management_audit:
        total_credits = float(receipt["account_total_credits_usd"])
        total_usage = float(receipt["account_total_usage_usd"])
        account_remaining = float(receipt["account_remaining_usd"])
        if (
            not all(
                math.isfinite(value) and value >= 0
                for value in (total_credits, total_usage, account_remaining)
            )
            or abs((total_credits - total_usage) - account_remaining) > 1e-9
            or account_remaining < float(receipt["account_remaining_floor_usd"])
            or float(receipt["account_remaining_floor_usd"])
            != expected_floors[phase]
        ):
            raise RuntimePolicyError(
                "credential receipt account balance/floor is invalid"
            )
    catalog = _normalize_required_model_catalog(list(receipt.get("model_catalog") or []))
    if receipt.get("model_catalog_sha256") != sha256_object(catalog):
        raise RuntimePolicyError("credential receipt model-catalog hash mismatch")
    _optional_future_timestamp(receipt.get("key_expires_at"), field="key_expires_at")
    return receipt


def validate_ramp_stage_workload(
    payload: Mapping[str, Any], *, expected_stage: int | None = None
) -> dict[str, Any]:
    """Validate one opaque, machine-generated disposable stage workload.

    A stage needs at least as many unique jobs as workers.  Four-suite and
    three-model coverage are properties of the whole stage, rather than an
    artificial fixed 4x3 matrix that could never exercise 16/32 workers.
    """

    _require_exact_keys(
        payload,
        {
            "schema_version",
            "worker_concurrency",
            "planned_job_count",
            "generation",
            "jobs",
        },
        field="ramp stage workload",
    )
    if payload.get("schema_version") != "agentdojo_openrouter_ramp_stage_workload/v2":
        raise RuntimePolicyError("ramp stage workload schema_version mismatch")
    stage = _strict_nonnegative_int(
        payload.get("worker_concurrency"), "workload worker_concurrency", minimum=1
    )
    if expected_stage is not None and stage != int(expected_stage):
        raise RuntimePolicyError("ramp workload belongs to a different stage")
    planned_count = _strict_nonnegative_int(
        payload.get("planned_job_count"), "workload planned_job_count", minimum=stage
    )
    generation = payload.get("generation")
    if not isinstance(generation, Mapping):
        raise RuntimePolicyError("ramp workload generation must be an object")
    _require_exact_keys(
        generation,
        {
            "algorithm",
            "manifest_path",
            "manifest_file_sha256",
            "agents_config_path",
            "agents_config_file_sha256",
            "source_bundle_path",
            "source_bundle_file_sha256",
            "selection_seed_sha256",
            "workload_kind",
            "model_ordinal",
            "model_batch_schedule",
            "result_namespace",
        },
        field="ramp workload generation",
    )
    if generation.get("algorithm") != "agentdojo_disposable_stage_round_robin/v1":
        raise RuntimePolicyError("ramp workload generation algorithm is invalid")
    normalized_generation = dict(generation)
    for field in (
        "manifest_file_sha256",
        "agents_config_file_sha256",
        "source_bundle_file_sha256",
        "selection_seed_sha256",
    ):
        normalized_generation[field] = _validate_digest(
            str(generation.get(field) or ""), f"generation.{field}"
        )
    for field in ("manifest_path", "agents_config_path", "source_bundle_path"):
        value = generation.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RuntimePolicyError(f"generation.{field} must be a non-empty path")
        normalized_generation[field] = value.strip()
    namespace = generation.get("result_namespace")
    if (
        not isinstance(namespace, str)
        or not namespace.endswith("_disposable_preflight")
        or len(namespace) > 128
    ):
        raise RuntimePolicyError(
            "ramp workload result_namespace must be a dedicated disposable-preflight namespace"
        )
    workload_kind = str(generation.get("workload_kind") or "")
    if workload_kind not in {"global_mixed_canary", "per_model_ramp"}:
        raise RuntimePolicyError("generation.workload_kind is invalid")
    normalized_generation["workload_kind"] = workload_kind
    model_ordinal_raw = generation.get("model_ordinal")
    if workload_kind == "global_mixed_canary":
        if stage != 4 or model_ordinal_raw is not None:
            raise RuntimePolicyError(
                "global mixed workload must be stage 4 with null model_ordinal"
            )
        model_ordinal: int | None = None
        expected_batch_schedule: list[dict[str, int]] | None = [
            {
                "model_ordinal": ordinal,
                "start_ordinal": ordinal * stage,
                "job_count": stage,
            }
            for ordinal in range(len(REQUIRED_MODELS))
        ]
    else:
        model_ordinal = _strict_nonnegative_int(
            model_ordinal_raw, "generation.model_ordinal"
        )
        if model_ordinal >= len(REQUIRED_MODELS):
            raise RuntimePolicyError("generation.model_ordinal is outside the frozen model set")
        expected_batch_schedule = None
    normalized_generation["model_ordinal"] = model_ordinal
    if generation.get("model_batch_schedule") != expected_batch_schedule:
        raise RuntimePolicyError(
            "generation model-batch schedule differs from the locked model-serial plan"
        )
    normalized_generation["model_batch_schedule"] = expected_batch_schedule

    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != planned_count:
        raise RuntimePolicyError("ramp workload jobs length differs from planned_job_count")
    normalized_jobs: list[dict[str, Any]] = []
    seen_jobs: set[str] = set()
    suites: set[str] = set()
    models: set[str] = set()
    model_counts: Counter[str] = Counter()
    for expected_ordinal, job in enumerate(jobs):
        if not isinstance(job, Mapping):
            raise RuntimePolicyError("ramp workload job must be an object")
        _require_exact_keys(
            job,
            {
                "ordinal",
                "suite",
                "opaque_case_identity_sha256",
                "model_config_sha256",
                "job_identity_sha256",
            },
            field="ramp workload job",
        )
        ordinal = _strict_nonnegative_int(job.get("ordinal"), "workload job ordinal")
        if ordinal != expected_ordinal:
            raise RuntimePolicyError("ramp workload job ordinals must be contiguous and ordered")
        suite = str(job.get("suite") or "")
        if suite not in REQUIRED_SUITES:
            raise RuntimePolicyError("ramp workload job suite is invalid")
        case_digest = _validate_digest(
            str(job.get("opaque_case_identity_sha256") or ""),
            "workload opaque_case_identity_sha256",
        )
        model_digest = _validate_digest(
            str(job.get("model_config_sha256") or ""),
            "workload model_config_sha256",
        )
        job_digest = _validate_digest(
            str(job.get("job_identity_sha256") or ""),
            "workload job_identity_sha256",
        )
        if job_digest in seen_jobs:
            raise RuntimePolicyError("ramp workload job identities must be unique")
        seen_jobs.add(job_digest)
        suites.add(suite)
        models.add(model_digest)
        model_counts[model_digest] += 1
        normalized_jobs.append(
            {
                "ordinal": ordinal,
                "suite": suite,
                "opaque_case_identity_sha256": case_digest,
                "model_config_sha256": model_digest,
                "job_identity_sha256": job_digest,
            }
        )
    if suites != set(REQUIRED_SUITES):
        raise RuntimePolicyError("ramp workload must cover all four suites")
    expected_model_count = 3 if workload_kind == "global_mixed_canary" else 1
    if len(models) != expected_model_count:
        raise RuntimePolicyError(
            "ramp workload model coverage differs from its workload_kind"
        )
    if workload_kind == "global_mixed_canary":
        if planned_count != stage * len(REQUIRED_MODELS) or set(
            model_counts.values()
        ) != {stage}:
            raise RuntimePolicyError(
                "global mixed workload must contain four jobs per model in a "
                "distinct twelve-job workload"
            )
    elif planned_count != stage or set(model_counts.values()) != {stage}:
        raise RuntimePolicyError(
            "per-model ramp workload must contain exactly one job per worker"
        )
    return {
        "schema_version": "agentdojo_openrouter_ramp_stage_workload/v2",
        "worker_concurrency": stage,
        "planned_job_count": planned_count,
        "generation": normalized_generation,
        "jobs": normalized_jobs,
    }


def build_ramp_stage_workload_from_sources(
    *,
    worker_concurrency: int,
    model_ordinal: int | None,
    manifest_path: str | Path,
    agents_config_path: str | Path,
    source_bundle_path: str | Path,
    result_namespace: str,
) -> dict[str, Any]:
    """Derive, rather than accept, every opaque stage workload identity."""

    workload, _, _ = _materialize_disposable_stage(
        worker_concurrency=worker_concurrency,
        model_ordinal=model_ordinal,
        manifest_path=manifest_path,
        agents_config_path=agents_config_path,
        source_bundle_path=source_bundle_path,
        result_namespace=result_namespace,
    )
    return workload


def materialize_disposable_stage_jobs(
    workload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Rebuild executable disposable jobs and sources from a verified workload."""

    normalized = validate_ramp_stage_workload(workload)
    generation = dict(normalized["generation"])
    rebuilt, jobs, source_by_case = _materialize_disposable_stage(
        worker_concurrency=int(normalized["worker_concurrency"]),
        model_ordinal=(
            None
            if generation["model_ordinal"] is None
            else int(generation["model_ordinal"])
        ),
        manifest_path=str(generation["manifest_path"]),
        agents_config_path=str(generation["agents_config_path"]),
        source_bundle_path=str(generation["source_bundle_path"]),
        result_namespace=str(generation["result_namespace"]),
    )
    if normalized != rebuilt:
        raise RuntimePolicyError(
            "ramp workload is not the deterministic projection of its frozen sources"
        )
    return [
        {
            "job": job,
            "source_entry": source_by_case[str(job["case_unit_id"])],
        }
        for job in jobs
    ]


def _materialize_disposable_stage(
    *,
    worker_concurrency: int,
    model_ordinal: int | None,
    manifest_path: str | Path,
    agents_config_path: str | Path,
    source_bundle_path: str | Path,
    result_namespace: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    stage = int(worker_concurrency)
    if stage not in {4, 8, 16, 32}:
        raise RuntimePolicyError("disposable workload stage must be 4, 8, 16, or 32")
    model_index = None if model_ordinal is None else int(model_ordinal)
    if model_index is not None and not 0 <= model_index < len(REQUIRED_MODELS):
        raise RuntimePolicyError("disposable workload model_ordinal must be 0, 1, or 2")
    workload_kind = (
        "global_mixed_canary" if model_index is None else "per_model_ramp"
    )
    if workload_kind == "global_mixed_canary" and stage != 4:
        raise RuntimePolicyError("global mixed canary must use worker concurrency 4")
    manifest_file = _regular_nonsymlink_file(manifest_path, "ramp manifest")
    agents_file = _regular_nonsymlink_file(agents_config_path, "ramp agents config")
    source_file = _regular_nonsymlink_file(source_bundle_path, "ramp source bundle")
    manifest = load_json_or_yaml(manifest_file)
    agents = load_json_or_yaml(agents_file)
    source_bundle = load_json_or_yaml(source_file)
    if not isinstance(manifest, Mapping) or not isinstance(agents, Mapping) or not isinstance(source_bundle, Mapping):
        raise RuntimePolicyError("ramp source documents must be objects")
    if str(manifest.get("agents_config_hash") or "") != sha256_file(agents_file):
        raise RuntimePolicyError("manifest agents_config_hash differs from the frozen agents file")
    domains = manifest.get("domains")
    if not isinstance(domains, list) or len(domains) != 1 or not isinstance(domains[0], Mapping):
        raise RuntimePolicyError("ramp manifest must contain exactly one domain")
    domain = domains[0]
    if str(domain.get("domain") or "").lower() != "agentdojo":
        raise RuntimePolicyError("ramp manifest domain is not AgentDojo")
    case_rows = domain.get("case_units")
    if not isinstance(case_rows, list) or len(case_rows) != 949:
        raise RuntimePolicyError("ramp manifest must contain exactly 949 case units")
    case_units: list[dict[str, str]] = []
    seen_cases: set[str] = set()
    by_suite: dict[str, list[dict[str, str]]] = {suite: [] for suite in REQUIRED_SUITES}
    for row in case_rows:
        if not isinstance(row, Mapping):
            raise RuntimePolicyError("ramp manifest case unit is not an object")
        case_id = str(row.get("case_unit_id") or "")
        task_id = str(row.get("task_id") or "")
        bits = case_id.split(":")
        if len(bits) != 4 or bits[0] != "v1.2.2" or bits[1] not in REQUIRED_SUITES:
            raise RuntimePolicyError("ramp manifest contains an invalid AgentDojo case ID")
        if case_id in seen_cases or task_id != ":".join(bits[1:]):
            raise RuntimePolicyError("ramp manifest case IDs are duplicate or task mapping is invalid")
        seen_cases.add(case_id)
        item = {"case_unit_id": case_id, "task_id": task_id, "suite": bits[1]}
        case_units.append(item)
        by_suite[bits[1]].append(item)
    if any(not by_suite[suite] for suite in REQUIRED_SUITES):
        raise RuntimePolicyError("ramp manifest does not cover all four suites")

    source_rows = source_bundle.get("sources")
    if not isinstance(source_rows, list) or len(source_rows) != 949:
        raise RuntimePolicyError("ramp source bundle must contain exactly 949 entries")
    source_by_case: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        if not isinstance(row, Mapping):
            raise RuntimePolicyError("ramp source-bundle entry is not an object")
        case_id = str(row.get("case_unit_id") or "")
        if case_id in source_by_case:
            raise RuntimePolicyError("ramp source bundle contains duplicate case IDs")
        source_by_case[case_id] = dict(row)
    if set(source_by_case) != seen_cases:
        raise RuntimePolicyError("ramp manifest/source-bundle case sets differ")

    roles = agents.get("experimental_agents")
    manifest_agents = manifest.get("agents")
    if not isinstance(roles, Mapping) or not isinstance(manifest_agents, list):
        raise RuntimePolicyError("ramp agents configuration is missing")
    if [str(row.get("agent_id") or "") for row in manifest_agents if isinstance(row, Mapping)] != list(REQUIRED_AGENT_IDS):
        raise RuntimePolicyError("ramp manifest agent order differs from the frozen three agents")
    normalized_roles: list[dict[str, Any]] = []
    for agent_id, required_model, manifest_agent in zip(
        REQUIRED_AGENT_IDS, REQUIRED_MODELS, manifest_agents, strict=True
    ):
        role = roles.get(agent_id)
        if not isinstance(role, Mapping) or not isinstance(manifest_agent, Mapping):
            raise RuntimePolicyError(f"ramp agent role is missing: {agent_id}")
        if sha256_object(dict(role)) != str(manifest_agent.get("config_hash") or ""):
            raise RuntimePolicyError(f"ramp manifest role hash differs for {agent_id}")
        if str(role.get("provider") or "") != "openrouter" or str(role.get("model") or "") != required_model:
            raise RuntimePolicyError(f"ramp model binding differs for {agent_id}")
        normalized_roles.append(dict(role))

    manifest_sha = sha256_file(manifest_file)
    agents_sha = sha256_file(agents_file)
    source_sha = sha256_file(source_file)
    selection_seed = sha256_object(
        {
            "algorithm": "agentdojo_disposable_stage_round_robin/v1",
            "manifest_file_sha256": manifest_sha,
            "agents_config_file_sha256": agents_sha,
            "source_bundle_file_sha256": source_sha,
            "worker_concurrency": stage,
            "model_ordinal": model_index,
            "workload_kind": workload_kind,
            "result_namespace": result_namespace,
        }
    )
    generation = {
        "algorithm": "agentdojo_disposable_stage_round_robin/v1",
        "manifest_path": _portable_path(manifest_file),
        "manifest_file_sha256": manifest_sha,
        "agents_config_path": _portable_path(agents_file),
        "agents_config_file_sha256": agents_sha,
        "source_bundle_path": _portable_path(source_file),
        "source_bundle_file_sha256": source_sha,
        "selection_seed_sha256": selection_seed,
        "workload_kind": workload_kind,
        "model_ordinal": model_index,
        "model_batch_schedule": (
            [
                {
                    "model_ordinal": ordinal,
                    "start_ordinal": ordinal * stage,
                    "job_count": stage,
                }
                for ordinal in range(len(REQUIRED_MODELS))
            ]
            if workload_kind == "global_mixed_canary"
            else None
        ),
        "result_namespace": result_namespace,
    }
    jobs: list[dict[str, Any]] = []
    opaque_jobs: list[dict[str, Any]] = []
    suite_positions = {suite: 0 for suite in REQUIRED_SUITES}
    # The multi-model canary is an independent twelve-job workload: four jobs
    # per frozen model, executed as three serial single-model four-worker
    # subbatches.  It cannot
    # be conflated with any of the three per-model stage-4 workloads because
    # those exercise four concurrent requests for one model, whereas this
    # workload exercises four concurrent requests across the model mix.
    planned_job_count = (
        stage * len(REQUIRED_MODELS)
        if workload_kind == "global_mixed_canary"
        else stage
    )
    for ordinal in range(planned_job_count):
        suite = REQUIRED_SUITES[ordinal % len(REQUIRED_SUITES)]
        case = by_suite[suite][suite_positions[suite]]
        suite_positions[suite] += 1
        agent_index = ordinal // stage if model_index is None else model_index
        agent_id = REQUIRED_AGENT_IDS[agent_index]
        role = normalized_roles[agent_index]
        job = {
            "job_id": f"disposable-agentdojo-model-{model_index if model_index is not None else 'mixed'}-stage-{stage}-{ordinal:04d}",
            "case_unit_id": case["case_unit_id"],
            "record_slot_id": f"disposable-slot-model-{model_index if model_index is not None else 'mixed'}-stage-{stage}-{ordinal:04d}",
            "task_id": case["task_id"],
            "agent_id": agent_id,
            "domain": "agentdojo",
            "phase": "smoke",
            "experiment_type": "appendix",
            "priority": "P1",
            "result_namespace": result_namespace,
            "runtime_scope": "disposable_preflight",
            "seed": (int(selection_seed[:8], 16) + ordinal) % (2**32),
        }
        model_digest = agentdojo_model_config_sha256(
            agent_id=agent_id,
            provider=str(role["provider"]),
            model_id=str(role["model"]),
            temperature=float(role["temperature"]),
            max_tokens=int(role["max_tokens"]),
            timeout_seconds=int(role["timeout_seconds"]),
            retry=int(role["retry"]),
        )
        jobs.append(job)
        opaque_jobs.append(
            {
                "ordinal": ordinal,
                "suite": suite,
                "opaque_case_identity_sha256": sha256_object(
                    {"case_unit_id": case["case_unit_id"]}
                ),
                "model_config_sha256": model_digest,
                "job_identity_sha256": job_identity_sha256(job),
            }
        )
    workload = validate_ramp_stage_workload(
        {
            "schema_version": "agentdojo_openrouter_ramp_stage_workload/v2",
            "worker_concurrency": stage,
            "planned_job_count": len(jobs),
            "generation": generation,
            "jobs": opaque_jobs,
        },
        expected_stage=stage,
    )
    return workload, jobs, source_by_case


class RampResourceLedger:
    """Durable, evidence-free host samples used by machine stage verification."""

    def __init__(self, path: str | Path, *, shared_group: str | None = None) -> None:
        self.path = Path(path)
        try:
            self.shared_gid = (
                None
                if shared_group is None
                else int(grp.getgrnam(shared_group).gr_gid)
            )
        except KeyError as exc:
            raise RuntimePolicyError("resource shared group does not exist") from exc
        self._thread_lock = threading.Lock()

    def record(
        self,
        *,
        worker_concurrency: int,
        cpu_percent: float,
        memory_percent: float,
        swap_used_bytes: int,
        active_worker_processes: int,
        active_openrouter_leases: int,
        budget_scope: str,
        runtime_database_path_sha256: str,
        stage_binding_sha256: str,
        worker_process_binding_sha256: str,
        expected_worker_uid: int,
        minimum_worker_starttime_ticks: int,
        worker_process_set_sha256: str,
        foreign_agentdojo_worker_processes: int,
        stale_agentdojo_worker_processes: int,
        session_id: str,
        host_boot_id: str,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "schema_version": RAMP_RESOURCE_SAMPLE_SCHEMA_VERSION,
            "timestamp": _validated_timestamp(timestamp),
            "source": "linux_procfs",
            "worker_concurrency": int(worker_concurrency),
            "cpu_percent": float(cpu_percent),
            "memory_percent": float(memory_percent),
            "swap_used_bytes": int(swap_used_bytes),
            "active_worker_processes": int(active_worker_processes),
            "active_openrouter_leases": int(active_openrouter_leases),
            "budget_scope": str(budget_scope),
            "runtime_database_path_sha256": str(runtime_database_path_sha256),
            "stage_binding_sha256": str(stage_binding_sha256),
            "worker_process_binding_sha256": str(worker_process_binding_sha256),
            "expected_worker_uid": int(expected_worker_uid),
            "minimum_worker_starttime_ticks": int(minimum_worker_starttime_ticks),
            "worker_process_set_sha256": str(worker_process_set_sha256),
            "foreign_agentdojo_worker_processes": int(
                foreign_agentdojo_worker_processes
            ),
            "stale_agentdojo_worker_processes": int(
                stale_agentdojo_worker_processes
            ),
            "session_id": _validate_session_id(session_id),
            "host_boot_id": _validate_host_boot_id(host_boot_id),
        }
        validate_ramp_resource_sample(record)
        encoded = json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        with self._thread_lock:
            if self.shared_gid is None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            elif self.path.parent.is_symlink() or not self.path.parent.is_dir():
                raise RuntimePolicyError(
                    "shared resource ledger parent must be pre-provisioned"
                )
            descriptor = os.open(
                self.path,
                os.O_APPEND
                | os.O_CREAT
                | os.O_WRONLY
                | getattr(os, "O_NOFOLLOW", 0),
                0o640 if self.shared_gid is not None else 0o600,
            )
            try:
                os.fchmod(descriptor, 0o640 if self.shared_gid is not None else 0o600)
                if self.shared_gid is not None:
                    os.fchown(descriptor, -1, self.shared_gid)
                with os.fdopen(
                    descriptor, "a", encoding="utf-8", closefd=False
                ) as handle:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    try:
                        handle.write(encoded + "\n")
                        handle.flush()
                        os.fsync(handle.fileno())
                    finally:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
        return record


def sample_linux_host_resources(
    *,
    sample_seconds: float = 0.25,
    worker_process_binding_sha256: str,
    expected_worker_uid: int,
    minimum_worker_starttime_ticks: int,
    proc_root: str | Path = "/proc",
) -> dict[str, Any]:
    """Read evidence-free host telemetry for exactly one authorized stage.

    Every visible ``agentdojo_worker`` process must carry the exact opaque
    stage-binding argument, run under the locked UID, and have started no
    earlier than the controller's stage boundary.  A foreign or stale worker
    therefore fails the sample instead of silently contaminating its count.
    ``proc_root`` exists solely to permit deterministic procfs fixture tests.
    """

    if not math.isfinite(sample_seconds) or not 0.05 <= sample_seconds <= 5.0:
        raise RuntimePolicyError("resource sample_seconds must be between 0.05 and 5")
    binding = _validate_digest(
        worker_process_binding_sha256, "worker_process_binding_sha256"
    )
    uid = _strict_nonnegative_int(expected_worker_uid, "expected_worker_uid")
    minimum_starttime = _strict_nonnegative_int(
        minimum_worker_starttime_ticks,
        "minimum_worker_starttime_ticks",
        minimum=1,
    )
    proc = Path(proc_root)
    if not (proc / "stat").is_file() or not (proc / "meminfo").is_file():
        raise RuntimePolicyError("machine resource sampling requires Linux procfs")

    def cpu_totals() -> tuple[int, int]:
        first = (proc / "stat").read_text(encoding="utf-8").splitlines()[0].split()
        if not first or first[0] != "cpu" or len(first) < 5:
            raise RuntimePolicyError("Linux /proc/stat CPU row is invalid")
        values = [int(value) for value in first[1:]]
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        return sum(values), idle

    total_before, idle_before = cpu_totals()
    time.sleep(sample_seconds)
    total_after, idle_after = cpu_totals()
    total_delta = total_after - total_before
    idle_delta = idle_after - idle_before
    if total_delta <= 0 or idle_delta < 0:
        raise RuntimePolicyError("Linux CPU counters did not advance monotonically")
    cpu_percent = 100.0 * (1.0 - (idle_delta / total_delta))

    meminfo: dict[str, int] = {}
    for line in (proc / "meminfo").read_text(encoding="utf-8").splitlines():
        key, _, raw = line.partition(":")
        parts = raw.strip().split()
        if parts and parts[0].isdigit():
            meminfo[key] = int(parts[0]) * 1024
    total_memory = meminfo.get("MemTotal", 0)
    available_memory = meminfo.get("MemAvailable", 0)
    if total_memory <= 0 or not 0 <= available_memory <= total_memory:
        raise RuntimePolicyError("Linux /proc/meminfo memory values are invalid")
    memory_percent = 100.0 * (1.0 - (available_memory / total_memory))
    swap_total = meminfo.get("SwapTotal", 0)
    swap_free = meminfo.get("SwapFree", 0)
    swap_used = max(0, swap_total - swap_free)

    active_worker_identities: list[dict[str, Any]] = []
    foreign_workers = 0
    stale_workers = 0
    for child in proc.iterdir():
        if not child.name.isdigit():
            continue
        try:
            raw_command = (child / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        argv = [part.decode("utf-8", errors="surrogateescape") for part in raw_command.split(b"\x00") if part]
        if "evidence_system.adapters.agentdojo_worker" not in argv:
            continue
        try:
            process_uid = _procfs_process_uid(child)
            starttime_ticks = _procfs_process_starttime_ticks(child)
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        matches = [
            index
            for index, argument in enumerate(argv[:-1])
            if argument == "--resource-stage-token" and argv[index + 1] == binding
        ]
        token_arguments = sum(
            argument == "--resource-stage-token" for argument in argv
        )
        if token_arguments != 1 or len(matches) != 1 or process_uid != uid:
            foreign_workers += 1
            continue
        if starttime_ticks < minimum_starttime:
            stale_workers += 1
            continue
        active_worker_identities.append(
            {
                "pid": int(child.name),
                "uid": process_uid,
                "starttime_ticks": starttime_ticks,
                "cmdline_sha256": hashlib.sha256(raw_command).hexdigest(),
            }
        )
    if foreign_workers:
        raise RuntimePolicyError(
            "foreign AgentDojo worker process is visible during the stage sample"
        )
    if stale_workers:
        raise RuntimePolicyError(
            "stale AgentDojo worker process is visible during the stage sample"
        )
    active_worker_identities.sort(
        key=lambda row: (int(row["pid"]), int(row["starttime_ticks"]))
    )
    return {
        "cpu_percent": round(cpu_percent, 6),
        "memory_percent": round(memory_percent, 6),
        "swap_used_bytes": swap_used,
        "active_worker_processes": len(active_worker_identities),
        "worker_process_binding_sha256": binding,
        "expected_worker_uid": uid,
        "minimum_worker_starttime_ticks": minimum_starttime,
        "worker_process_set_sha256": sha256_object(active_worker_identities),
        "foreign_agentdojo_worker_processes": foreign_workers,
        "stale_agentdojo_worker_processes": stale_workers,
    }


def _procfs_process_uid(process_root: Path) -> int:
    for line in (process_root / "status").read_text(encoding="utf-8").splitlines():
        if line.startswith("Uid:"):
            values = line.removeprefix("Uid:").split()
            if len(values) != 4 or any(not value.isdigit() for value in values):
                break
            return int(values[0])
    raise RuntimePolicyError("Linux process Uid row is invalid")


def _procfs_process_starttime_ticks(process_root: Path) -> int:
    value = (process_root / "stat").read_text(encoding="utf-8").strip()
    command_end = value.rfind(")")
    if command_end < 2:
        raise RuntimePolicyError("Linux process stat row is invalid")
    fields_after_command = value[command_end + 1 :].split()
    # The first value after ``comm`` is field 3 (state); starttime is field 22.
    if len(fields_after_command) <= 19:
        raise RuntimePolicyError("Linux process stat row lacks starttime")
    try:
        starttime_ticks = int(fields_after_command[19])
    except ValueError as exc:
        raise RuntimePolicyError("Linux process starttime is invalid") from exc
    if starttime_ticks <= 0:
        raise RuntimePolicyError("Linux process starttime must be positive")
    return starttime_ticks


def validate_ramp_resource_sample(record: Mapping[str, Any]) -> None:
    expected_keys = {
            "schema_version",
            "timestamp",
            "source",
            "worker_concurrency",
            "cpu_percent",
            "memory_percent",
            "swap_used_bytes",
            "active_worker_processes",
            "active_openrouter_leases",
            "budget_scope",
            "runtime_database_path_sha256",
            "stage_binding_sha256",
            "worker_process_binding_sha256",
            "expected_worker_uid",
            "minimum_worker_starttime_ticks",
            "worker_process_set_sha256",
            "foreign_agentdojo_worker_processes",
            "stale_agentdojo_worker_processes",
            "session_id",
            "host_boot_id",
    }
    _require_exact_keys(record, expected_keys, field="ramp resource sample")
    if record.get("schema_version") != RAMP_RESOURCE_SAMPLE_SCHEMA_VERSION:
        raise RuntimePolicyError("ramp resource sample schema_version mismatch")
    if record.get("source") != "linux_procfs":
        raise RuntimePolicyError("ramp resource sample source must be linux_procfs")
    _parse_aware_timestamp(str(record.get("timestamp") or ""), "resource timestamp")
    worker_concurrency = _strict_nonnegative_int(
        record.get("worker_concurrency"), "resource worker_concurrency", minimum=1
    )
    active_workers = _strict_nonnegative_int(
        record.get("active_worker_processes"), "resource active_worker_processes"
    )
    active_leases = _strict_nonnegative_int(
        record.get("active_openrouter_leases"), "resource active_openrouter_leases"
    )
    if active_workers > worker_concurrency:
        raise RuntimePolicyError("active worker processes exceed the stage concurrency")
    if active_leases > worker_concurrency:
        raise RuntimePolicyError("active OpenRouter leases exceed the stage concurrency")
    _finite_percentage(record.get("cpu_percent"), "resource cpu_percent")
    _finite_percentage(record.get("memory_percent"), "resource memory_percent")
    _strict_nonnegative_int(record.get("swap_used_bytes"), "resource swap_used_bytes")
    if record.get("budget_scope") not in {
        "formal_execution",
        "disposable_preflight",
    }:
        raise RuntimePolicyError("resource budget_scope is invalid")
    for field in (
        "runtime_database_path_sha256",
        "stage_binding_sha256",
        "worker_process_binding_sha256",
        "worker_process_set_sha256",
    ):
        _validate_digest(str(record.get(field) or ""), f"resource {field}")
    _strict_nonnegative_int(record.get("expected_worker_uid"), "resource expected_worker_uid")
    _strict_nonnegative_int(
        record.get("minimum_worker_starttime_ticks"),
        "resource minimum_worker_starttime_ticks",
        minimum=1,
    )
    if _strict_nonnegative_int(
        record.get("foreign_agentdojo_worker_processes"),
        "resource foreign_agentdojo_worker_processes",
    ) != 0:
        raise RuntimePolicyError("resource sample contains a foreign AgentDojo worker")
    if _strict_nonnegative_int(
        record.get("stale_agentdojo_worker_processes"),
        "resource stale_agentdojo_worker_processes",
    ) != 0:
        raise RuntimePolicyError("resource sample contains a stale AgentDojo worker")
    _validate_session_id(str(record["session_id"]))
    _validate_host_boot_id(str(record["host_boot_id"]))


def build_formal_locked_stage_workload(
    *,
    execution_lock_sha256: str,
    execution_policy_sha256: str,
    plan_index_sha256: str,
    stage_id: str,
    workers: int,
    record_slot_ids_sha256: str,
    record_slot_count: int,
    agent_models: Sequence[Mapping[str, Any]],
    target_agent_id: str | None = None,
) -> dict[str, Any]:
    """Build a content-free formal-stage health workload binding."""

    normalized_stage = str(stage_id)
    if not normalized_stage or len(normalized_stage) > 64:
        raise RuntimePolicyError("formal health stage_id is invalid")
    normalized_workers = _strict_nonnegative_int(
        workers, "formal health workers", minimum=1
    )
    normalized_count = _strict_nonnegative_int(
        record_slot_count, "formal health record_slot_count", minimum=1
    )
    if target_agent_id is not None and target_agent_id not in REQUIRED_AGENT_IDS:
        raise RuntimePolicyError("formal health target_agent_id is invalid")
    normalized_models = _normalize_formal_agent_models(
        agent_models, expected_record_slot_count=normalized_count
    )
    if target_agent_id is not None:
        target_rows = [
            row for row in normalized_models if row["agent_id"] == target_agent_id
        ]
        if target_rows[0]["record_slot_count"] != normalized_count:
            raise RuntimePolicyError(
                "single-agent formal health workload must bind every slot to its target agent"
            )
    return {
        "schema_version": "agentdojo_formal_stage_health_workload/v1",
        "execution_lock_sha256": _validate_digest(
            execution_lock_sha256, "execution_lock_sha256"
        ),
        "execution_policy_sha256": _validate_digest(
            execution_policy_sha256, "execution_policy_sha256"
        ),
        "plan_index_sha256": _validate_digest(
            plan_index_sha256, "plan_index_sha256"
        ),
        "stage_id": normalized_stage,
        "workers": normalized_workers,
        "record_slot_count": normalized_count,
        "record_slot_ids_sha256": _validate_digest(
            record_slot_ids_sha256, "record_slot_ids_sha256"
        ),
        "target_agent_id": target_agent_id,
        "agent_models": normalized_models,
    }


def build_formal_stage_health_receipt(
    policy: RuntimePolicy,
    *,
    stage_workload: Mapping[str, Any],
    runtime_infra_file_sha256: str,
    blind_health_ledger_path: str | Path,
    resource_ledger_path: str | Path,
    session_id: str,
    host_boot_id: str,
    session_started_at: str,
    session_ended_at: str,
    prior_safe_workers: int,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Seal formal health without aborting on operational threshold failures."""

    workload = _validate_formal_stage_workload(stage_workload)
    workers = int(workload["workers"])
    if workers not in policy.ramp_stages:
        raise RuntimePolicyError("formal health workers are outside the locked ramp")
    prior_safe = _strict_nonnegative_int(
        prior_safe_workers, "formal health prior_safe_workers", minimum=1
    )
    if prior_safe not in policy.ramp_stages or prior_safe > workers:
        raise RuntimePolicyError("formal health prior_safe_workers is invalid")
    normalized_session = _validate_session_id(session_id)
    normalized_boot = _validate_host_boot_id(host_boot_id)
    started = _parse_aware_timestamp(session_started_at, "formal session_started_at")
    ended = _parse_aware_timestamp(session_ended_at, "formal session_ended_at")
    if ended < started:
        raise RuntimePolicyError("formal health session ends before it starts")
    health_path = _regular_nonsymlink_file(
        blind_health_ledger_path, "formal blind health ledger"
    )
    resource_path = _regular_nonsymlink_file(
        resource_ledger_path, "formal resource ledger"
    )
    health_rows = _read_formal_health_session_rows(
        health_path,
        expected_policy_sha256=policy.semantic_sha256,
        expected_session_id=normalized_session,
        expected_host_boot_id=normalized_boot,
        started_at=started,
        ended_at=ended,
    )
    resource_rows = _read_formal_resource_session_rows(
        resource_path,
        expected_workers=workers,
        expected_session_id=normalized_session,
        expected_host_boot_id=normalized_boot,
        started_at=started,
        ended_at=ended,
    )
    request_rows = [row for row in health_rows if row["event_type"] == "request_attempt"]
    completion_rows = [
        row for row in health_rows if row["event_type"] == "worker_completion"
    ]
    known_models = {
        str(row["model_config_sha256"]): row for row in workload["agent_models"]
    }
    if any(str(row.get("model_config_sha256") or "") not in known_models for row in request_rows + completion_rows):
        raise RuntimePolicyError("formal health ledger contains an unknown model binding")

    resource_samples_ok = len(resource_rows) >= policy.ramp_minimum_resource_samples
    max_cpu = max((float(row["cpu_percent"]) for row in resource_rows), default=0.0)
    max_memory = max(
        (float(row["memory_percent"]) for row in resource_rows), default=0.0
    )
    max_swap = max((int(row["swap_used_bytes"]) for row in resource_rows), default=0)
    max_active_workers = max(
        (int(row["active_worker_processes"]) for row in resource_rows), default=0
    )
    max_active_leases = max(
        (int(row["active_openrouter_leases"]) for row in resource_rows), default=0
    )
    required_active_workers = math.ceil(
        workers * policy.ramp_minimum_active_worker_fraction
    )
    required_active_requests = math.ceil(
        workers * policy.ramp_minimum_active_request_fraction
    )
    resource_ok = (
        resource_samples_ok
        and max_cpu <= policy.ramp_max_cpu_percent
        and max_memory <= policy.ramp_max_memory_percent
        and max_swap == 0
        and max_active_workers >= required_active_workers
        and max_active_leases >= required_active_requests
    )

    model_decisions: list[dict[str, Any]] = []
    for model in workload["agent_models"]:
        model_digest = str(model["model_config_sha256"])
        model_requests = [
            row
            for row in request_rows
            if str(row.get("model_config_sha256") or "") == model_digest
        ]
        model_completions = {
            str(row.get("job_identity_sha256") or "")
            for row in completion_rows
            if str(row.get("model_config_sha256") or "") == model_digest
            and row.get("outcome") == "success"
        }
        model_expected = int(model["record_slot_count"])
        model_failures = max(0, model_expected - len(model_completions))
        request_metrics = _formal_request_health_metrics(model_requests, policy)
        involved = model_expected > 0
        authorized = bool(
            involved
            and resource_ok
            and model_failures == 0
            and request_metrics["thresholds_passed"]
        )
        model_decisions.append(
            {
                "agent_id": str(model["agent_id"]),
                "model_id": str(model["model_id"]),
                "model_config_sha256": model_digest,
                "record_slot_count": model_expected,
                "request_attempt_count": len(model_requests),
                "successful_worker_completion_count": len(model_completions),
                "worker_failure_count": model_failures,
                "promotion_authorized": authorized,
                "safe_workers": workers if authorized else prior_safe,
                "request_health": request_metrics,
            }
        )
    target_agent = workload.get("target_agent_id")
    relevant = [
        row
        for row in model_decisions
        if (
            row["agent_id"] == target_agent
            if target_agent is not None
            else int(row["record_slot_count"]) > 0
        )
    ]
    promotion_authorized = bool(relevant) and all(
        bool(row["promotion_authorized"]) for row in relevant
    )
    safe_workers = workers if promotion_authorized else prior_safe
    payload = {
        "schema_version": FORMAL_STAGE_HEALTH_RECEIPT_SCHEMA_VERSION,
        "status": "passed_health_gate" if promotion_authorized else "valid_hold_or_downgrade",
        "created_at": _validated_timestamp(created_at),
        "stage_workload": workload,
        "stage_workload_sha256": sha256_object(workload),
        "runtime_policy_semantic_sha256": policy.semantic_sha256,
        "runtime_policy": dict(policy.raw),
        "runtime_infra_file_sha256": _validate_digest(
            runtime_infra_file_sha256, "runtime_infra_file_sha256"
        ),
        "runtime_snapshot": execution_runtime_snapshot(),
        "session": {
            "session_id": normalized_session,
            "host_boot_id": normalized_boot,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
        },
        "blind_health_ledger": _locked_file_ref(health_path),
        "resource_ledger": _locked_file_ref(resource_path),
        "observed": {
            "health_record_count": len(health_rows),
            "resource_sample_count": len(resource_rows),
            "request_attempt_count": len(request_rows),
            "worker_completion_count": len(completion_rows),
            "max_cpu_percent": round(max_cpu, 6),
            "max_memory_percent": round(max_memory, 6),
            "max_swap_used_bytes": max_swap,
            "max_active_worker_processes": max_active_workers,
            "max_active_openrouter_leases": max_active_leases,
            "minimum_required_active_worker_processes": required_active_workers,
            "minimum_required_active_openrouter_leases": required_active_requests,
            "resource_thresholds_passed": resource_ok,
        },
        "model_decisions": model_decisions,
        "promotion_authorized": promotion_authorized,
        "safe_workers": safe_workers,
        "prior_safe_workers": prior_safe,
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    validate_object("agentdojo_formal_stage_health_receipt", payload)
    return payload


def load_formal_stage_health_receipt(
    path: str | Path,
    *,
    expected_execution_lock_sha256: str,
    expected_execution_policy_sha256: str,
    expected_stage_id: str,
    expected_workers: int,
    expected_record_slot_count: int,
    expected_record_slot_ids_sha256: str,
    expected_plan_index_sha256: str | None = None,
    expected_workload_sha256: str | None = None,
    expected_runtime_infra_file_sha256: str | None = None,
    expected_session_id: str | None = None,
) -> dict[str, Any]:
    """Rebuild a formal health receipt and reject stale session/ledger/code state."""

    receipt = _load_receipt(path, "agentdojo_formal_stage_health_receipt")
    workload = _validate_formal_stage_workload(
        dict(receipt.get("stage_workload") or {})
    )
    expected_bindings = {
        "execution_lock_sha256": _validate_digest(
            expected_execution_lock_sha256, "expected_execution_lock_sha256"
        ),
        "execution_policy_sha256": _validate_digest(
            expected_execution_policy_sha256, "expected_execution_policy_sha256"
        ),
        "stage_id": str(expected_stage_id),
        "workers": int(expected_workers),
        "record_slot_count": int(expected_record_slot_count),
        "record_slot_ids_sha256": _validate_digest(
            expected_record_slot_ids_sha256, "expected_record_slot_ids_sha256"
        ),
    }
    for field, expected in expected_bindings.items():
        if workload.get(field) != expected:
            raise RuntimePolicyError(f"formal health workload {field} binding mismatch")
    if expected_plan_index_sha256 is not None and workload.get(
        "plan_index_sha256"
    ) != _validate_digest(expected_plan_index_sha256, "expected_plan_index_sha256"):
        raise RuntimePolicyError("formal health plan-index binding mismatch")
    workload_sha = sha256_object(workload)
    if receipt.get("stage_workload_sha256") != workload_sha:
        raise RuntimePolicyError("formal health workload SHA-256 mismatch")
    if expected_workload_sha256 is not None and workload_sha != _validate_digest(
        expected_workload_sha256, "expected_workload_sha256"
    ):
        raise RuntimePolicyError("formal health expected workload SHA-256 mismatch")
    if expected_runtime_infra_file_sha256 is not None and receipt.get(
        "runtime_infra_file_sha256"
    ) != _validate_digest(
        expected_runtime_infra_file_sha256,
        "expected_runtime_infra_file_sha256",
    ):
        raise RuntimePolicyError("formal health runtime-infra binding mismatch")
    if receipt.get("runtime_snapshot") != execution_runtime_snapshot():
        raise RuntimePolicyError("formal health runtime snapshot is stale")
    session = dict(receipt.get("session") or {})
    if expected_session_id is not None and session.get("session_id") != _validate_session_id(
        expected_session_id
    ):
        raise RuntimePolicyError("formal health session binding mismatch")
    health_ref = dict(receipt.get("blind_health_ledger") or {})
    resource_ref = dict(receipt.get("resource_ledger") or {})
    health_path = _regular_nonsymlink_file(
        str(health_ref.get("path") or ""), "formal blind health ledger"
    )
    resource_path = _regular_nonsymlink_file(
        str(resource_ref.get("path") or ""), "formal resource ledger"
    )
    if health_ref.get("sha256") != sha256_file(health_path) or resource_ref.get(
        "sha256"
    ) != sha256_file(resource_path):
        raise RuntimePolicyError("formal health ledger hash is stale")
    policy = load_runtime_policy(
        dict(receipt.get("runtime_policy") or {}),
        expected_semantic_sha256=str(receipt.get("runtime_policy_semantic_sha256") or ""),
    )
    rebuilt = build_formal_stage_health_receipt(
        policy,
        stage_workload=workload,
        runtime_infra_file_sha256=str(receipt["runtime_infra_file_sha256"]),
        blind_health_ledger_path=health_path,
        resource_ledger_path=resource_path,
        session_id=str(session.get("session_id") or ""),
        host_boot_id=str(session.get("host_boot_id") or ""),
        session_started_at=str(session.get("started_at") or ""),
        session_ended_at=str(session.get("ended_at") or ""),
        prior_safe_workers=int(receipt["prior_safe_workers"]),
        created_at=str(receipt["created_at"]),
    )
    if receipt != rebuilt:
        raise RuntimePolicyError("formal health receipt differs from recomputed ledgers")
    return receipt


def _normalize_formal_agent_models(
    rows: Sequence[Mapping[str, Any]], *, expected_record_slot_count: int
) -> list[dict[str, Any]]:
    if not isinstance(rows, Sequence) or len(rows) != len(REQUIRED_AGENT_IDS):
        raise RuntimePolicyError("formal health requires exactly three agent-model rows")
    normalized: list[dict[str, Any]] = []
    for row, expected_agent, expected_model in zip(
        rows, REQUIRED_AGENT_IDS, REQUIRED_MODELS, strict=True
    ):
        if not isinstance(row, Mapping):
            raise RuntimePolicyError("formal health agent-model row is not an object")
        _require_exact_keys(
            row,
            {
                "agent_id",
                "model_id",
                "model_config_sha256",
                "record_slot_count",
            },
            field="formal health agent-model row",
        )
        if row.get("agent_id") != expected_agent or row.get("model_id") != expected_model:
            raise RuntimePolicyError("formal health agent/model order differs")
        normalized.append(
            {
                "agent_id": expected_agent,
                "model_id": expected_model,
                "model_config_sha256": _validate_digest(
                    str(row.get("model_config_sha256") or ""),
                    "formal model_config_sha256",
                ),
                "record_slot_count": _strict_nonnegative_int(
                    row.get("record_slot_count"),
                    "formal model record_slot_count",
                ),
            }
        )
    if sum(int(row["record_slot_count"]) for row in normalized) != int(
        expected_record_slot_count
    ):
        raise RuntimePolicyError("formal agent-model slot counts differ from stage total")
    return normalized


def _validate_formal_stage_workload(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_keys(
        payload,
        {
            "schema_version",
            "execution_lock_sha256",
            "execution_policy_sha256",
            "plan_index_sha256",
            "stage_id",
            "workers",
            "record_slot_count",
            "record_slot_ids_sha256",
            "target_agent_id",
            "agent_models",
        },
        field="formal stage health workload",
    )
    if payload.get("schema_version") != "agentdojo_formal_stage_health_workload/v1":
        raise RuntimePolicyError("formal stage health workload schema mismatch")
    rows = payload.get("agent_models")
    if not isinstance(rows, list):
        raise RuntimePolicyError("formal stage health agent_models must be a list")
    return build_formal_locked_stage_workload(
        execution_lock_sha256=str(payload.get("execution_lock_sha256") or ""),
        execution_policy_sha256=str(payload.get("execution_policy_sha256") or ""),
        plan_index_sha256=str(payload.get("plan_index_sha256") or ""),
        stage_id=str(payload.get("stage_id") or ""),
        workers=_strict_nonnegative_int(payload.get("workers"), "formal workers", minimum=1),
        record_slot_ids_sha256=str(payload.get("record_slot_ids_sha256") or ""),
        record_slot_count=_strict_nonnegative_int(
            payload.get("record_slot_count"), "formal record_slot_count", minimum=1
        ),
        agent_models=rows,
        target_agent_id=(
            None
            if payload.get("target_agent_id") is None
            else str(payload.get("target_agent_id"))
        ),
    )


def _read_formal_health_session_rows(
    path: Path,
    *,
    expected_policy_sha256: str,
    expected_session_id: str,
    expected_host_boot_id: str,
    started_at: datetime,
    ended_at: datetime,
) -> list[dict[str, Any]]:
    expected_policy = _validate_digest(
        expected_policy_sha256, "formal expected_policy_sha256"
    )
    selected: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            lines = handle.read().splitlines()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimePolicyError(
                f"formal health line {line_number} is invalid JSON"
            ) from exc
        if not isinstance(row, dict):
            raise RuntimePolicyError("formal health ledger contains a non-object")
        validate_blind_health_record(row)
        if str(row.get("policy_sha256") or "") != expected_policy:
            raise RuntimePolicyError("formal health ledger policy binding differs")
        if row.get("session_id") != expected_session_id:
            continue
        if row.get("host_boot_id") != expected_host_boot_id:
            raise RuntimePolicyError("formal health session crosses a host boot")
        timestamp = _row_timestamp(row)
        if timestamp < started_at or timestamp > ended_at:
            raise RuntimePolicyError("formal health row falls outside its session window")
        selected.append(row)
    return selected


def _read_formal_resource_session_rows(
    path: Path,
    *,
    expected_workers: int,
    expected_session_id: str,
    expected_host_boot_id: str,
    started_at: datetime,
    ended_at: datetime,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            lines = handle.read().splitlines()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimePolicyError(
                f"formal resource line {line_number} is invalid JSON"
            ) from exc
        if not isinstance(row, dict):
            raise RuntimePolicyError("formal resource ledger contains a non-object")
        validate_ramp_resource_sample(row)
        if row.get("session_id") != expected_session_id:
            continue
        if row.get("host_boot_id") != expected_host_boot_id:
            raise RuntimePolicyError("formal resource session crosses a host boot")
        if row.get("budget_scope") != "formal_execution":
            raise RuntimePolicyError("formal resource row uses a non-formal budget scope")
        if int(row["worker_concurrency"]) != expected_workers:
            raise RuntimePolicyError("formal resource row uses different workers")
        timestamp = _parse_aware_timestamp(
            str(row["timestamp"]), "formal resource timestamp"
        )
        if timestamp < started_at or timestamp > ended_at:
            raise RuntimePolicyError("formal resource row falls outside its session window")
        selected.append(row)
    binding_fields = (
        "runtime_database_path_sha256",
        "stage_binding_sha256",
        "worker_process_binding_sha256",
        "expected_worker_uid",
        "minimum_worker_starttime_ticks",
    )
    for field in binding_fields:
        if len({row[field] for row in selected}) > 1:
            raise RuntimePolicyError(
                f"formal resource session crosses a different {field}"
            )
    return selected


def _formal_request_health_metrics(
    request_rows: Sequence[Mapping[str, Any]], policy: RuntimePolicy
) -> dict[str, Any]:
    chains: dict[str, list[Mapping[str, Any]]] = {}
    for row in request_rows:
        chain_id = str(row.get("request_chain_id") or "")
        if not chain_id:
            raise RuntimePolicyError("formal request health row is missing its chain")
        chains.setdefault(chain_id, []).append(row)
    unresolved = 0
    recovered = 0
    max_consecutive = 0
    max_retry_delay = 0.0
    for rows in chains.values():
        ordered = sorted(
            rows,
            key=lambda row: (int(row.get("attempt_index") or 0), _row_timestamp(row)),
        )
        chain_recovered_status = False
        consecutive = 0
        chain_delay = 0.0
        for row in ordered:
            chain_delay += float(row.get("retry_delay_seconds") or 0.0)
            if int(row.get("http_status") or 0) in {429, 503}:
                chain_recovered_status = True
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        latest = ordered[-1]
        if latest.get("outcome") != "success" or int(latest.get("http_status") or 0) != 200:
            unresolved += 1
        elif chain_recovered_status:
            recovered += 1
        max_retry_delay = max(max_retry_delay, chain_delay)
    recovered_fraction = recovered / len(chains) if chains else 0.0
    max_rpm, max_reservation_units, max_provider_actual_tokens = (
        _observed_rate_maxima(request_rows, window_seconds=policy.rate_window_seconds)
        if request_rows
        else (0, 0, 0)
    )
    thresholds_passed = bool(
        request_rows
        and unresolved == 0
        and recovered_fraction <= policy.ramp_max_recovered_429_503_fraction + 1e-12
        and max_consecutive <= policy.ramp_max_consecutive_429_503
        and max_retry_delay <= policy.ramp_max_retry_delay_seconds_per_chain + 1e-12
        and max_rpm <= policy.requests_per_minute
        and max_reservation_units <= policy.tokens_per_minute
    )
    return {
        "request_chain_count": len(chains),
        "unresolved_request_chain_count": unresolved,
        "recovered_429_503_chain_count": recovered,
        "recovered_429_503_fraction": round(recovered_fraction, 9),
        "max_consecutive_429_503": max_consecutive,
        "max_retry_delay_seconds_per_chain": round(max_retry_delay, 6),
        "max_rolling_rpm": max_rpm,
        "max_rolling_admission_reservation_units_per_minute": (
            max_reservation_units
        ),
        "max_rolling_provider_actual_tokens_per_minute": (
            max_provider_actual_tokens
        ),
        "thresholds_passed": thresholds_passed,
    }


def build_ramp_stage_receipt(
    policy: RuntimePolicy,
    *,
    scope: str,
    worker_concurrency: int,
    effective_worker_concurrency: int | None = None,
    prior_safe_workers: int = 4,
    runtime_infra_file_sha256: str,
    blind_health_ledger_path: str | Path,
    resource_ledger_path: str | Path,
    stage_workload: Mapping[str, Any],
    created_at: str | None = None,
) -> dict[str, Any]:
    """Recompute a stage receipt from durable ledgers; no health counters are accepted."""

    if scope not in {
        "disposable_preflight",
        "exploratory_measurement",
        "formal_execution",
    }:
        raise RuntimePolicyError("ramp stage scope is invalid")
    exploratory = scope == "exploratory_measurement"
    thresholds_passed = True
    stage = int(worker_concurrency)
    if stage not in policy.ramp_stages:
        raise RuntimePolicyError("ramp stage concurrency is outside the locked policy")
    effective_stage = (
        stage
        if effective_worker_concurrency is None
        else int(effective_worker_concurrency)
    )
    if effective_stage not in policy.ramp_stages or effective_stage > stage:
        raise RuntimePolicyError(
            "ramp effective concurrency must be a locked stage no greater than locked workers"
        )
    prior_safe = int(prior_safe_workers)
    if prior_safe not in policy.ramp_stages or prior_safe > effective_stage:
        raise RuntimePolicyError("ramp prior-safe workers are invalid")
    infra_sha = _validate_digest(
        runtime_infra_file_sha256, "runtime_infra_file_sha256"
    )
    workload = validate_ramp_stage_workload(stage_workload, expected_stage=stage)
    workload_sha = sha256_object(workload)
    health_path = _regular_nonsymlink_file(
        blind_health_ledger_path, "blind health ledger"
    )
    resource_path = _regular_nonsymlink_file(resource_ledger_path, "resource ledger")
    health_rows = _read_blind_health_records(
        health_path, expected_policy_sha256=policy.semantic_sha256
    )
    resource_rows = _read_resource_records(
        resource_path, expected_stage=effective_stage
    )
    if len(resource_rows) < policy.ramp_minimum_resource_samples:
        raise RuntimePolicyError("ramp stage has too few machine resource samples")
    health_sessions = {
        (str(row.get("session_id") or ""), str(row.get("host_boot_id") or ""))
        for row in health_rows
    }
    resource_sessions = {
        (str(row.get("session_id") or ""), str(row.get("host_boot_id") or ""))
        for row in resource_rows
    }
    if (
        len(health_sessions) != 1
        or len(resource_sessions) != 1
        or health_sessions != resource_sessions
    ):
        raise RuntimePolicyError(
            "ramp health/resource ledgers must bind one identical session and host boot"
        )
    runtime_session_id, runtime_host_boot_id = next(iter(health_sessions))
    runtime_session_id = _validate_session_id(runtime_session_id)
    runtime_host_boot_id = _validate_host_boot_id(runtime_host_boot_id)
    credential_fingerprints = {
        str(row.get("credential_fingerprint_sha256") or "")
        for row in health_rows
    }
    if len(credential_fingerprints) != 1 or "" in credential_fingerprints:
        raise RuntimePolicyError(
            "ramp stage health ledger is missing one stable credential fingerprint"
        )
    credential_fingerprint_sha256 = _validate_digest(
        next(iter(credential_fingerprints)),
        "ramp credential_fingerprint_sha256",
    )
    if (
        policy.execution_key_fingerprint_sha256 is not None
        and policy.execution_key_fingerprint_sha256
        != credential_fingerprint_sha256
    ):
        raise RuntimePolicyError("ramp stage used a different OpenRouter key")

    expected_jobs: dict[str, str] = {}
    expected_models: list[str] = []
    for workload_job in workload["jobs"]:
        model_digest = str(workload_job["model_config_sha256"])
        job_digest = str(workload_job["job_identity_sha256"])
        expected_jobs[job_digest] = model_digest
        if model_digest not in expected_models:
            expected_models.append(model_digest)

    request_rows = [row for row in health_rows if row["event_type"] == "request_attempt"]
    if not request_rows:
        raise RuntimePolicyError("ramp stage contains no real OpenRouter request attempts")
    request_counts: Counter[str] = Counter()
    success_counts: Counter[str] = Counter()
    successful_job_models: set[tuple[str, str]] = set()
    returned_identities: dict[str, set[str]] = {
        digest: set() for digest in expected_models
    }
    request_chains: dict[str, list[Mapping[str, Any]]] = {}
    observed_job_models: dict[str, str] = {}
    for row in request_rows:
        job_digest = str(row.get("job_identity_sha256") or "")
        model_digest = str(row.get("model_config_sha256") or "")
        chain_id = str(row.get("request_chain_id") or "")
        if job_digest not in expected_jobs:
            raise RuntimePolicyError("ramp stage contains a request outside the locked stage workload")
        if model_digest not in expected_models:
            raise RuntimePolicyError("ramp request uses a model outside the frozen three-model set")
        if job_digest in expected_jobs and expected_jobs[job_digest] != model_digest:
            raise RuntimePolicyError("ramp request model/job binding differs from canary matrix")
        previous_model = observed_job_models.setdefault(job_digest, model_digest)
        if previous_model != model_digest:
            raise RuntimePolicyError("one ramp job identity is bound to multiple models")
        if not chain_id:
            raise RuntimePolicyError("ramp request is missing request_chain_id")
        request_counts[model_digest] += 1
        if row.get("outcome") == "success" and int(row.get("http_status") or 0) == 200:
            returned_identity = str(
                row.get("returned_model_identity_sha256") or ""
            )
            if not returned_identity:
                raise RuntimePolicyError(
                    "successful ramp request is missing returned provider/model identity"
                )
            missing_request_semantics = [
                field
                for field in OPENROUTER_SUCCESS_PARAMETER_HEALTH_FIELDS
                if int(row.get(field) or 0) != 1
            ]
            if missing_request_semantics:
                raise RuntimePolicyError(
                    "successful ramp request did not prove the locked request semantics: "
                    f"{missing_request_semantics!r}"
                )
            returned_identities[model_digest].add(returned_identity)
            success_counts[model_digest] += 1
            successful_job_models.add((job_digest, model_digest))
        request_chains.setdefault(chain_id, []).append(row)
    expected_workload_pairs = set(expected_jobs.items())
    missing_successful_jobs = len(expected_workload_pairs - successful_job_models)
    if missing_successful_jobs:
        if not exploratory:
            raise RuntimePolicyError(
                "ramp stage did not produce a successful real request for every planned job"
            )
        thresholds_passed = False
    if successful_job_models - expected_workload_pairs:
        raise RuntimePolicyError("ramp stage contains an extra successful job")
    if set(request_counts) != set(expected_models):
        raise RuntimePolicyError("ramp stage model coverage differs from frozen three-model set")
    if not exploratory and any(
        not returned_identities[digest] for digest in expected_models
    ):
        raise RuntimePolicyError(
            "one model config has no returned provider/model identity"
        )

    latest_completion: dict[str, Mapping[str, Any]] = {}
    non_request_failed_jobs: set[str] = set()
    for row in health_rows:
        if row["event_type"] != "worker_completion":
            continue
        job_digest = str(row.get("job_identity_sha256") or "")
        model_digest = str(row.get("model_config_sha256") or "")
        if job_digest not in expected_jobs:
            raise RuntimePolicyError("ramp stage contains an unexpected worker completion")
        if model_digest not in expected_models:
            raise RuntimePolicyError("worker completion uses an unexpected model config")
        if job_digest in expected_jobs and expected_jobs[job_digest] != model_digest:
            raise RuntimePolicyError("worker completion model/job binding differs from canary matrix")
        request_model = observed_job_models.get(job_digest)
        if request_model is None:
            # A worker can fail before its first OpenRouter request (for
            # example during case setup).  Exploratory measurement must seal
            # that opaque failure as a threshold breach so the adaptive
            # controller can hold/downgrade and continue.  A successful
            # completion without a request, or the same condition in a
            # finalized/non-exploratory round, remains fail-closed because it
            # cannot prove a real model invocation.
            if not exploratory or row.get("outcome") not in {
                "fatal_error",
                "blocked",
            }:
                raise RuntimePolicyError(
                    "worker completion has no consistently bound request"
                )
            non_request_failed_jobs.add(job_digest)
            thresholds_passed = False
        elif request_model != model_digest:
            raise RuntimePolicyError(
                "worker completion has no consistently bound request"
            )
        latest_completion[job_digest] = row
    if set(latest_completion) != set(observed_job_models):
        if not exploratory:
            raise RuntimePolicyError("ramp stage request/completion job sets differ")
        thresholds_passed = False
    worker_failures = sum(
        row.get("outcome") != "success" for row in latest_completion.values()
    )
    if worker_failures:
        if not exploratory:
            raise RuntimePolicyError(
                f"ramp stage has {worker_failures} unresolved worker failures"
            )
        thresholds_passed = False

    http_429 = sum(int(row.get("http_status") or 0) == 429 for row in request_rows)
    http_503 = sum(int(row.get("http_status") or 0) == 503 for row in request_rows)
    unresolved_request_chains = 0
    recovered_429_503_chains = 0
    max_consecutive_429_503 = 0
    max_retry_delay_per_chain = 0.0
    for chain_rows in request_chains.values():
        ordered_chain = sorted(
            chain_rows,
            key=lambda row: (
                int(row.get("attempt_index") or 0),
                _row_timestamp(row),
            ),
        )
        latest = ordered_chain[-1]
        chain_had_429_503 = False
        consecutive = 0
        chain_retry_delay = 0.0
        for row in ordered_chain:
            chain_retry_delay += float(row.get("retry_delay_seconds") or 0.0)
            if int(row.get("http_status") or 0) in {429, 503}:
                chain_had_429_503 = True
                consecutive += 1
                max_consecutive_429_503 = max(max_consecutive_429_503, consecutive)
            else:
                consecutive = 0
        max_retry_delay_per_chain = max(max_retry_delay_per_chain, chain_retry_delay)
        if int(latest.get("http_status") or 0) in {429, 503} or latest.get(
            "outcome"
        ) in {"fatal_error", "blocked"}:
            unresolved_request_chains += 1
        elif chain_had_429_503:
            recovered_429_503_chains += 1
    # This legacy promotion counter predates the more precise companion
    # fields below.  It intentionally includes a fatal/blocked completion
    # that has no request chain, without inventing an HTTP status or request
    # attempt for that failure.
    unresolved = unresolved_request_chains + len(non_request_failed_jobs)
    if unresolved:
        if not exploratory:
            raise RuntimePolicyError(
                f"ramp stage has {unresolved} unresolved request chains"
            )
        thresholds_passed = False
    recovered_fraction = recovered_429_503_chains / len(request_chains)
    if recovered_fraction > policy.ramp_max_recovered_429_503_fraction + 1e-12:
        if not exploratory:
            raise RuntimePolicyError(
                "ramp stage recovered 429/503 fraction exceeds the locked threshold"
            )
        thresholds_passed = False
    if max_consecutive_429_503 > policy.ramp_max_consecutive_429_503:
        if not exploratory:
            raise RuntimePolicyError(
                "ramp stage consecutive 429/503 count exceeds the locked threshold"
            )
        thresholds_passed = False
    if (
        max_retry_delay_per_chain
        > policy.ramp_max_retry_delay_seconds_per_chain + 1e-12
    ):
        if not exploratory:
            raise RuntimePolicyError(
                "ramp stage retry delay per chain exceeds the locked threshold"
            )
        thresholds_passed = False

    max_rpm, max_reservation_units, max_provider_actual_tokens = _observed_rate_maxima(
        request_rows, window_seconds=policy.rate_window_seconds
    )
    if (
        max_rpm > policy.requests_per_minute
        or max_reservation_units > policy.tokens_per_minute
    ):
        if not exploratory:
            raise RuntimePolicyError(
                "ramp stage observed RPM/TPM exceeds the locked global policy"
            )
        thresholds_passed = False

    measurement_started = min(_row_timestamp(row).timestamp() for row in request_rows)
    measurement_ended = max(
        _row_timestamp(row).timestamp() + float(row.get("latency_seconds") or 0.0)
        for row in request_rows
    )
    measurement_duration = measurement_ended - measurement_started
    if measurement_duration <= 0.0:
        raise RuntimePolicyError(
            "ramp stage request ledger has no positive measurement duration"
        )
    achieved_successful_jobs = len(successful_job_models)
    requested_job_throughput = len(expected_jobs) * 60.0 / measurement_duration
    achieved_job_throughput = (
        achieved_successful_jobs * 60.0 / measurement_duration
    )
    achieved_admission_reservation_units_throughput = (
        sum(int(row.get("reserved_tokens") or 0) for row in request_rows)
        * 60.0
        / measurement_duration
    )
    provider_error_categories = {
        # OpenRouter documents that a 429 can originate at either its own
        # gateway or an upstream provider.  The blind ledger intentionally
        # stores neither response bodies nor trajectories, so origin remains
        # explicitly unknown instead of being guessed.
        "http_429_openrouter_or_upstream_unspecified": http_429,
        "http_503_service_origin_unspecified": http_503,
        "transport_or_non_http": sum(
            row.get("http_status") is None and row.get("outcome") != "success"
            for row in request_rows
        )
        + len(non_request_failed_jobs),
    }
    max_active_requests = max(int(row.get("active_requests") or 0) for row in request_rows)
    if max_active_requests > effective_stage:
        raise RuntimePolicyError("ramp stage active requests exceed worker concurrency")
    minimum_active_requests = math.ceil(
        effective_stage * policy.ramp_minimum_active_request_fraction
    )
    if max_active_requests < minimum_active_requests:
        if not exploratory:
            raise RuntimePolicyError(
                "ramp stage did not reach the locked minimum active-request threshold"
            )
        thresholds_passed = False

    max_cpu = max(float(row["cpu_percent"]) for row in resource_rows)
    max_memory = max(float(row["memory_percent"]) for row in resource_rows)
    max_swap = max(int(row["swap_used_bytes"]) for row in resource_rows)
    max_active_workers = max(int(row["active_worker_processes"]) for row in resource_rows)
    max_simultaneous_workers_and_requests = max(
        min(
            int(row["active_worker_processes"]),
            int(row["active_openrouter_leases"]),
        )
        for row in resource_rows
    )
    if max_cpu > policy.ramp_max_cpu_percent:
        if not exploratory:
            raise RuntimePolicyError("ramp stage CPU threshold exceeded")
        thresholds_passed = False
    if max_memory > policy.ramp_max_memory_percent:
        if not exploratory:
            raise RuntimePolicyError("ramp stage memory threshold exceeded")
        thresholds_passed = False
    if max_swap != 0:
        if not exploratory:
            raise RuntimePolicyError("ramp stage observed swap usage")
        thresholds_passed = False
    minimum_active_workers = math.ceil(
        effective_stage * policy.ramp_minimum_active_worker_fraction
    )
    if max_active_workers < minimum_active_workers:
        if not exploratory:
            raise RuntimePolicyError(
                "ramp stage did not reach the locked minimum active-worker threshold"
            )
        thresholds_passed = False
    minimum_simultaneous_load = max(minimum_active_workers, minimum_active_requests)
    if max_simultaneous_workers_and_requests < minimum_simultaneous_load:
        if not exploratory:
            raise RuntimePolicyError(
                "ramp resource samples never observed the locked worker/request load simultaneously"
            )
        thresholds_passed = False

    runtime_code = runtime_control_code_snapshot()
    ran_at_locked_target = effective_stage == stage
    resulting_safe = (
        stage if thresholds_passed and ran_at_locked_target else prior_safe
    )
    payload = {
        "schema_version": RAMP_STAGE_RECEIPT_SCHEMA_VERSION,
        "status": (
            "passed"
            if thresholds_passed and effective_stage == stage
            else (
                "held_at_prior_safe"
                if thresholds_passed
                else "measured_with_threshold_breach"
            )
        ),
        "created_at": _validated_timestamp(created_at),
        "scope": scope,
        "worker_concurrency": stage,
        "locked_workers": stage,
        "effective_workers": effective_stage,
        "ran_at_locked_target": ran_at_locked_target,
        "prior_safe_workers": prior_safe,
        "resulting_safe_workers": resulting_safe,
        "runtime_policy_semantic_sha256": policy.semantic_sha256,
        "runtime_policy": dict(policy.raw),
        "runtime_infra_file_sha256": infra_sha,
        "runtime_session": {
            "session_id": runtime_session_id,
            "host_boot_id": runtime_host_boot_id,
        },
        "credential_fingerprint_sha256": credential_fingerprint_sha256,
        "runtime_code": runtime_code,
        "stage_workload": workload,
        "stage_workload_sha256": workload_sha,
        "blind_health_ledger": _locked_file_ref(health_path),
        "resource_ledger": _locked_file_ref(resource_path),
        "observed": {
            "request_attempts": len(request_rows),
            "planned_jobs": len(expected_jobs),
            "unique_completed_jobs": len(latest_completion),
            "worker_completions": len(latest_completion),
            "worker_failures": worker_failures,
            "missing_successful_jobs": missing_successful_jobs,
            "http_429": http_429,
            "http_503": http_503,
            "unresolved_http_429_or_503": unresolved,
            "unresolved_request_chains": unresolved_request_chains,
            "non_request_worker_failures": len(non_request_failed_jobs),
            "recovered_429_503_chains": recovered_429_503_chains,
            "recovered_429_503_fraction": round(recovered_fraction, 9),
            "max_consecutive_429_503": max_consecutive_429_503,
            "max_retry_delay_seconds_per_chain": round(max_retry_delay_per_chain, 6),
            "max_rolling_rpm": max_rpm,
            "max_rolling_admission_reservation_units_per_minute": (
                max_reservation_units
            ),
            "max_rolling_provider_actual_tokens_per_minute": (
                max_provider_actual_tokens
            ),
            "measurement_duration_seconds": round(measurement_duration, 6),
            "requested_job_throughput_per_minute": round(
                requested_job_throughput, 6
            ),
            "achieved_successful_job_throughput_per_minute": round(
                achieved_job_throughput, 6
            ),
            "achieved_admission_reservation_units_throughput_per_minute": round(
                achieved_admission_reservation_units_throughput, 6
            ),
            "provider_error_categories": provider_error_categories,
            "max_active_requests": max_active_requests,
            "minimum_required_active_requests": minimum_active_requests,
            "resource_samples": len(resource_rows),
            "max_cpu_percent": round(max_cpu, 6),
            "max_memory_percent": round(max_memory, 6),
            "max_swap_used_bytes": max_swap,
            "max_active_worker_processes": max_active_workers,
            "minimum_required_active_worker_processes": minimum_active_workers,
            "max_simultaneous_active_workers_and_requests": max_simultaneous_workers_and_requests,
            "minimum_required_simultaneous_load": minimum_simultaneous_load,
            "thresholds_passed": thresholds_passed,
            "per_model": [
                {
                    "model_config_sha256": model_digest,
                    "returned_provider_model_identity_sha256s": sorted(
                        returned_identities[model_digest]
                    ),
                    "request_count": request_counts[model_digest],
                    "success_count": success_counts[model_digest],
                    "successful_request_parameter_proof": {
                        "temperature_present": bool(success_counts[model_digest]),
                        "top_p_present": bool(success_counts[model_digest]),
                        "max_tokens_present": bool(success_counts[model_digest]),
                        "seed_present": bool(success_counts[model_digest]),
                        "native_tools_absent": bool(success_counts[model_digest]),
                        "native_tool_choice_absent": bool(
                            success_counts[model_digest]
                        ),
                        "prompt_based_tool_protocol": True,
                    },
                }
                for model_digest in expected_models
            ],
        },
        "blind_only": True,
    }
    validate_object("agentdojo_openrouter_ramp_stage_receipt", payload)
    return payload


def load_ramp_stage_receipt(
    path: str | Path,
    *,
    expected_policy_sha256: str,
    expected_runtime_infra_file_sha256: str | None = None,
    expected_scope: str | None = None,
    expected_host_boot_id: str | None = None,
) -> dict[str, Any]:
    receipt = _load_receipt(path, "agentdojo_openrouter_ramp_stage_receipt")
    _require_receipt_binding(
        receipt,
        expected_policy_sha256=expected_policy_sha256,
        expected_runtime_infra_file_sha256=expected_runtime_infra_file_sha256,
    )
    if expected_scope is not None and receipt.get("scope") != expected_scope:
        raise RuntimePolicyError("ramp stage receipt scope mismatch")
    if (
        int(receipt.get("locked_workers") or 0)
        != int(receipt["worker_concurrency"])
        or int(receipt.get("effective_workers") or 0)
        > int(receipt["locked_workers"])
        or bool(receipt.get("ran_at_locked_target"))
        != (
            int(receipt.get("effective_workers") or 0)
            == int(receipt["locked_workers"])
        )
    ):
        raise RuntimePolicyError("ramp locked/effective worker semantics differ")
    expected_status = (
        "passed"
        if receipt["observed"]["thresholds_passed"]
        and receipt["ran_at_locked_target"]
        else (
            "held_at_prior_safe"
            if receipt["observed"]["thresholds_passed"]
            else "measured_with_threshold_breach"
        )
    )
    if receipt["status"] != expected_status:
        raise RuntimePolicyError("ramp status overclaims its effective worker target")
    expected_resulting_safe = (
        int(receipt["locked_workers"])
        if receipt["status"] == "passed" and receipt["ran_at_locked_target"]
        else int(receipt["prior_safe_workers"])
    )
    if (
        int(receipt["prior_safe_workers"]) > int(receipt["effective_workers"])
        or int(receipt["resulting_safe_workers"]) != expected_resulting_safe
    ):
        raise RuntimePolicyError("ramp prior/resulting safe-worker chain differs")
    runtime_session = dict(receipt.get("runtime_session") or {})
    _validate_session_id(str(runtime_session.get("session_id") or ""))
    receipt_boot_id = _validate_host_boot_id(
        str(runtime_session.get("host_boot_id") or "")
    )
    if expected_host_boot_id is not None and receipt_boot_id != _validate_host_boot_id(
        expected_host_boot_id
    ):
        raise RuntimePolicyError("ramp stage receipt belongs to a stale host boot")
    if receipt.get("runtime_code") != runtime_control_code_snapshot():
        raise RuntimePolicyError("ramp stage runtime code is stale")
    workload = validate_ramp_stage_workload(
        dict(receipt.get("stage_workload") or {}),
        expected_stage=int(receipt["worker_concurrency"]),
    )
    if receipt.get("stage_workload_sha256") != sha256_object(workload):
        raise RuntimePolicyError("ramp stage workload hash mismatch")
    # Re-open and hash the frozen manifest/agents/source bundle, then derive
    # every case/model/job digest.  Arbitrary syntactically valid hashes are
    # never accepted as provenance.
    materialize_disposable_stage_jobs(workload)
    locked_paths: dict[str, Path] = {}
    for field in ("blind_health_ledger", "resource_ledger"):
        ref = dict(receipt.get(field) or {})
        locked_path = _regular_nonsymlink_file(str(ref.get("path") or ""), field)
        if ref.get("sha256") != sha256_file(locked_path):
            raise RuntimePolicyError(f"ramp stage {field} hash is stale")
        locked_paths[field] = locked_path
    policy = load_runtime_policy(
        dict(receipt.get("runtime_policy") or {}),
        expected_semantic_sha256=expected_policy_sha256,
    )
    rebuilt = build_ramp_stage_receipt(
        policy,
        scope=str(receipt["scope"]),
        worker_concurrency=int(receipt["worker_concurrency"]),
        effective_worker_concurrency=int(receipt["effective_workers"]),
        prior_safe_workers=int(receipt["prior_safe_workers"]),
        runtime_infra_file_sha256=str(receipt["runtime_infra_file_sha256"]),
        blind_health_ledger_path=locked_paths["blind_health_ledger"],
        resource_ledger_path=locked_paths["resource_ledger"],
        stage_workload=workload,
        created_at=str(receipt["created_at"]),
    )
    if receipt != rebuilt:
        raise RuntimePolicyError("ramp stage receipt differs from recomputed ledgers")
    observed = dict(receipt.get("observed") or {})
    if receipt.get("scope") != "exploratory_measurement" and (
        observed.get("worker_failures") != 0
        or observed.get("unresolved_http_429_or_503") != 0
        or observed.get("unresolved_request_chains") != 0
        or observed.get("non_request_worker_failures") != 0
        or observed.get("thresholds_passed") is not True
    ):
        raise RuntimePolicyError("ramp stage receipt contains unresolved failures")
    return receipt


def build_disposable_ramp_receipt(
    policy: RuntimePolicy,
    *,
    runtime_infra_file_sha256: str,
    stage_receipt_paths: Sequence[str | Path],
    global_mixed_canary_receipt_path: str | Path,
    pre_ramp_credential_receipt_path: str | Path,
    post_ramp_credential_receipt_path: str | Path,
    validation_round_plan_path: str | Path,
    measurement_receipt_path: str | Path,
    policy_finalization_receipt_path: str | Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build the final receipt solely by re-verifying four machine stage receipts."""

    infra_sha = _validate_digest(
        runtime_infra_file_sha256, "runtime_infra_file_sha256"
    )
    if policy.lifecycle_status != "finalized":
        raise RuntimePolicyError(
            "a provisional runtime policy cannot produce a passing disposable ramp receipt"
        )
    from evidence_system.contracts.agentdojo_rate_lifecycle import (
        load_disposable_round_plan,
    )

    validation_plan_file = _regular_nonsymlink_file(
        validation_round_plan_path, "validation round plan"
    )
    validation_plan = load_disposable_round_plan(validation_plan_file)
    validation_definition = dict(validation_plan["definition"])
    validation_artifacts = dict(validation_plan["artifact_namespace"])
    measurement_file = _regular_nonsymlink_file(
        measurement_receipt_path, "measurement aggregate receipt"
    )
    finalization_file = _regular_nonsymlink_file(
        policy_finalization_receipt_path, "policy finalization receipt"
    )
    if (
        validation_definition["round_kind"] != "finalized_validation"
        or validation_definition["runtime_policy"]["semantic_sha256"]
        != policy.semantic_sha256
        or validation_definition["bridge"]["measurement_receipt"]["sha256"]
        != sha256_file(measurement_file)
        or validation_definition["bridge"]["policy_finalization_receipt"]["sha256"]
        != sha256_file(finalization_file)
    ):
        raise RuntimePolicyError("final validation round bridge differs")
    finalization = load_policy_finalization_receipt(finalization_file)
    if (
        finalization["measurement_receipt"]["sha256"]
        != sha256_file(measurement_file)
        or finalization["finalized_runtime_policy"]["semantic_sha256"]
        != policy.semantic_sha256
    ):
        raise RuntimePolicyError("final validation bridge is cross-policy")
    pre_path = _regular_nonsymlink_file(
        pre_ramp_credential_receipt_path, "pre-ramp credential receipt"
    )
    post_path = _regular_nonsymlink_file(
        post_ramp_credential_receipt_path, "post-ramp credential receipt"
    )
    pre_probe = load_credential_probe_receipt(
        pre_path,
        expected_policy_sha256=policy.semantic_sha256,
        expected_runtime_infra_file_sha256=infra_sha,
        expected_probe_phase="pre_final_validation",
    )
    post_probe = load_credential_probe_receipt(
        post_path,
        expected_policy_sha256=policy.semantic_sha256,
        expected_runtime_infra_file_sha256=infra_sha,
        expected_probe_phase="post_ramp",
    )
    for label, probe in (("pre", pre_probe), ("post", post_probe)):
        round_ref = probe.get("round_plan")
        if (
            not isinstance(round_ref, Mapping)
            or round_ref.get("sha256") != sha256_file(validation_plan_file)
            or round_ref.get("definition_sha256")
            != validation_plan["definition_sha256"]
        ):
            raise RuntimePolicyError(
                f"final validation {label} credential is not bound to its round plan"
            )
    measurement_raw = json.loads(measurement_file.read_text(encoding="utf-8"))
    credential_fingerprints = {
        str(pre_probe["credential_fingerprint_sha256"]),
        str(post_probe["credential_fingerprint_sha256"]),
        str(measurement_raw.get("credential_fingerprint_sha256") or ""),
    }
    if len(credential_fingerprints) != 1 or "" in credential_fingerprints:
        raise RuntimePolicyError(
            "measurement and final-validation rounds used different OpenRouter keys"
        )
    credential_fingerprint_sha256 = next(iter(credential_fingerprints))
    management_statuses = {
        str(pre_probe["management_audit_status"]),
        str(post_probe["management_audit_status"]),
        str(measurement_raw.get("management_audit_status") or ""),
    }
    if len(management_statuses) != 1 or "" in management_statuses:
        raise RuntimePolicyError(
            "measurement and final-validation management-audit statuses differ"
        )
    management_audit_status = next(iter(management_statuses))
    management_values = {
        pre_probe["management_audit_fingerprint_sha256"],
        post_probe["management_audit_fingerprint_sha256"],
        measurement_raw.get("management_audit_fingerprint_sha256"),
    }
    if len(management_values) != 1 or (
        management_audit_status == "performed" and None in management_values
    ):
        raise RuntimePolicyError(
            "measurement and final-validation management audit bindings differ"
        )
    management_audit_fingerprint_sha256 = next(iter(management_values))
    if (
        _portable_path(pre_path) != validation_artifacts["pre_credential_receipt"]
        or _portable_path(post_path) != validation_artifacts["post_credential_receipt"]
    ):
        raise RuntimePolicyError(
            "final validation credential receipts are outside the SHA-derived round namespace"
        )
    mixed_path = _regular_nonsymlink_file(
        global_mixed_canary_receipt_path, "global mixed-canary receipt"
    )
    mixed_stage = load_ramp_stage_receipt(
        mixed_path,
        expected_policy_sha256=policy.semantic_sha256,
        expected_runtime_infra_file_sha256=infra_sha,
        expected_scope="disposable_preflight",
    )
    if (
        int(mixed_stage["worker_concurrency"]) != 4
        or int(mixed_stage["effective_workers"]) != 4
        or mixed_stage["stage_workload"]["generation"]["workload_kind"]
        != "global_mixed_canary"
        or len(mixed_stage["observed"]["per_model"]) != 3
    ):
        raise RuntimePolicyError("global mixed-canary receipt coverage is invalid")
    planned_stages = list(validation_definition["stages"])
    if mixed_stage["stage_workload_sha256"] != planned_stages[0][
        "workload_sha256"
    ]:
        raise RuntimePolicyError("validation mixed receipt differs from its plan")
    if _portable_path(mixed_path) != validation_artifacts["stages"][0][
        "stage_receipt"
    ]:
        raise RuntimePolicyError("validation mixed receipt path is outside its round")
    expected_substage_count = len(policy.ramp_stages) * len(REQUIRED_MODELS)
    if len(stage_receipt_paths) != expected_substage_count:
        raise RuntimePolicyError(
            "disposable ramp requires exactly twelve per-model stage receipts"
        )
    stages: list[dict[str, Any]] = []
    refs: list[dict[str, Any]] = []
    expected_order = [
        (stage_value, model_ordinal)
        for stage_value in policy.ramp_stages
        for model_ordinal in range(len(REQUIRED_MODELS))
    ]
    validation_safe_by_model = {
        ordinal: 4 for ordinal in range(len(REQUIRED_MODELS))
    }
    for plan_index, ((expected_stage, expected_model_ordinal), stage_path) in enumerate(zip(
        expected_order, stage_receipt_paths, strict=True
    ), start=1):
        resolved = _regular_nonsymlink_file(stage_path, "ramp stage receipt")
        stage = load_ramp_stage_receipt(
            resolved,
            expected_policy_sha256=policy.semantic_sha256,
            expected_runtime_infra_file_sha256=infra_sha,
            expected_scope="disposable_preflight",
        )
        if int(stage["worker_concurrency"]) != expected_stage:
            raise RuntimePolicyError("disposable ramp stage order mismatch")
        if stage["stage_workload_sha256"] != planned_stages[plan_index][
            "workload_sha256"
        ]:
            raise RuntimePolicyError("validation stage receipt differs from its plan")
        expected_artifact = validation_artifacts["stages"][plan_index]
        if int(stage["effective_workers"]) != int(
            planned_stages[plan_index]["effective_workers"]
        ):
            raise RuntimePolicyError(
                "validation stage effective workers differ from finalized plan"
            )
        if int(stage["prior_safe_workers"]) != validation_safe_by_model[
            expected_model_ordinal
        ]:
            raise RuntimePolicyError("validation prior-safe worker chain differs")
        if stage["status"] == "passed" and stage["ran_at_locked_target"] is True:
            validation_safe_by_model[expected_model_ordinal] = expected_stage
        if int(stage["resulting_safe_workers"]) != validation_safe_by_model[
            expected_model_ordinal
        ]:
            raise RuntimePolicyError("validation resulting-safe worker chain differs")
        if (
            _portable_path(resolved) != expected_artifact["stage_receipt"]
            or stage["blind_health_ledger"]["path"]
            != expected_artifact["blind_health_ledger"]
            or stage["resource_ledger"]["path"]
            != expected_artifact["resource_ledger"]
        ):
            raise RuntimePolicyError(
                "validation stage artifacts are outside the SHA-derived round namespace"
            )
        observed_model_ordinal = int(
            stage["stage_workload"]["generation"]["model_ordinal"]
        )
        if observed_model_ordinal != expected_model_ordinal:
            raise RuntimePolicyError("disposable ramp model-substage order mismatch")
        stages.append(stage)
        refs.append(
            {
                "path": _portable_path(resolved),
                "sha256": sha256_file(resolved),
                "worker_concurrency": expected_stage,
                "effective_workers": int(stage["effective_workers"]),
                "model_ordinal": expected_model_ordinal,
            }
        )
    ledger_paths = [str(stage["blind_health_ledger"]["path"]) for stage in stages]
    resource_paths = [str(stage["resource_ledger"]["path"]) for stage in stages]
    ledger_paths.append(str(mixed_stage["blind_health_ledger"]["path"]))
    resource_paths.append(str(mixed_stage["resource_ledger"]["path"]))
    if len(set(ledger_paths)) != len(ledger_paths) or len(set(resource_paths)) != len(
        resource_paths
    ):
        raise RuntimePolicyError("each disposable stage must use distinct frozen ledgers")
    runtime_code = stages[0]["runtime_code"]
    if mixed_stage["runtime_code"] != runtime_code:
        raise RuntimePolicyError("runtime code differs between mixed and per-model ramp")
    if any(stage["runtime_code"] != runtime_code for stage in stages):
        raise RuntimePolicyError("runtime code changed during disposable ramp")
    stage_workload_shas = [str(stage["stage_workload_sha256"]) for stage in stages]
    if len(set(stage_workload_shas)) != len(stages):
        raise RuntimePolicyError("each disposable stage requires a distinct workload")
    all_stage_receipts = [mixed_stage, *stages]
    if {
        str(stage.get("credential_fingerprint_sha256") or "")
        for stage in all_stage_receipts
    } != {credential_fingerprint_sha256}:
        raise RuntimePolicyError(
            "final validation stages and credential probes used different keys"
        )
    latest_stage_at = max(
        _parse_aware_timestamp(str(stage["created_at"]), "stage created_at")
        for stage in all_stage_receipts
    )
    if _parse_aware_timestamp(
        str(pre_probe["created_at"]), "pre-ramp credential created_at"
    ) >= min(
        _parse_aware_timestamp(str(stage["created_at"]), "first stage created_at")
        for stage in all_stage_receipts
    ):
        raise RuntimePolicyError("pre-ramp credential probe was not created before the ramp")
    if _parse_aware_timestamp(
        str(post_probe["created_at"]), "post-ramp credential created_at"
    ) <= latest_stage_at:
        raise RuntimePolicyError("post-ramp credential probe was not created after the ramp")
    model_totals: Counter[str] = Counter()
    model_successes: Counter[str] = Counter()
    model_returned_identities: dict[str, set[str]] = {}
    for stage in stages:
        for row in stage["observed"]["per_model"]:
            digest = str(row["model_config_sha256"])
            model_totals[digest] += int(row["request_count"])
            model_successes[digest] += int(row["success_count"])
            if row.get("successful_request_parameter_proof") != {
                "temperature_present": True,
                "top_p_present": True,
                "max_tokens_present": True,
                "seed_present": True,
                "native_tools_absent": True,
                "native_tool_choice_absent": True,
                "prompt_based_tool_protocol": True,
            }:
                raise RuntimePolicyError(
                    "final validation did not prove the locked request-parameter surface"
                )
            model_returned_identities.setdefault(digest, set()).update(
                str(value)
                for value in row["returned_provider_model_identity_sha256s"]
            )
    minimum_model_jobs = sum(policy.ramp_stages)
    if len(model_totals) != 3 or any(
        model_successes[digest] < minimum_model_jobs for digest in model_totals
    ):
        raise RuntimePolicyError("final ramp does not prove all three models across all stages")
    model_digest_by_ordinal: list[str] = []
    for model_ordinal in range(len(REQUIRED_MODELS)):
        digests = {
            str(stage["observed"]["per_model"][0]["model_config_sha256"])
            for stage in stages
            if int(stage["stage_workload"]["generation"]["model_ordinal"])
            == model_ordinal
        }
        if len(digests) != 1:
            raise RuntimePolicyError("one frozen model ordinal maps to multiple config hashes")
        model_digest_by_ordinal.append(next(iter(digests)))
    payload = {
        "schema_version": DISPOSABLE_RAMP_RECEIPT_SCHEMA_VERSION,
        "status": "passed",
        "created_at": _validated_timestamp(created_at),
        "stages": list(policy.ramp_stages),
        "model_substage_count": expected_substage_count,
        "stage_receipts": refs,
        "global_mixed_canary_receipt": _locked_file_ref(mixed_path),
        "global_mixed_canary_observed": {
            "worker_concurrency": 4,
            "max_rolling_rpm": int(mixed_stage["observed"]["max_rolling_rpm"]),
            "max_rolling_admission_reservation_units_per_minute": int(
                mixed_stage["observed"][
                    "max_rolling_admission_reservation_units_per_minute"
                ]
            ),
            "max_rolling_provider_actual_tokens_per_minute": int(
                mixed_stage["observed"][
                    "max_rolling_provider_actual_tokens_per_minute"
                ]
            ),
            "max_active_requests": int(mixed_stage["observed"]["max_active_requests"]),
            "per_model": list(mixed_stage["observed"]["per_model"]),
        },
        "suite_canaries": list(REQUIRED_SUITES),
        "four_suite_canary_complete": True,
        "stage_workload_sha256s": stage_workload_shas,
        "unresolved_http_429_or_503": 0,
        "max_observed_recovered_429_503_fraction": max(
            float(stage["observed"]["recovered_429_503_fraction"])
            for stage in all_stage_receipts
        ),
        "max_observed_consecutive_429_503": max(
            int(stage["observed"]["max_consecutive_429_503"])
            for stage in all_stage_receipts
        ),
        "max_observed_retry_delay_seconds_per_chain": max(
            float(stage["observed"]["max_retry_delay_seconds_per_chain"])
            for stage in all_stage_receipts
        ),
        "worker_failures": 0,
        "runtime_policy_semantic_sha256": policy.semantic_sha256,
        "runtime_infra_file_sha256": infra_sha,
        "runtime_code": runtime_code,
        "credential_fingerprint_sha256": credential_fingerprint_sha256,
        "management_audit_fingerprint_sha256": (
            management_audit_fingerprint_sha256
        ),
        "management_audit_status": management_audit_status,
        "validation_round_plan": {
            **_locked_file_ref(validation_plan_file),
            "definition_sha256": str(validation_plan["definition_sha256"]),
        },
        "measurement_receipt": _locked_file_ref(measurement_file),
        "policy_finalization_receipt": _locked_file_ref(finalization_file),
        "pre_ramp_credential_receipt": _locked_file_ref(pre_path),
        "post_ramp_credential_receipt": _locked_file_ref(post_path),
        "blind_health_ledgers": [
            mixed_stage["blind_health_ledger"],
            *[stage["blind_health_ledger"] for stage in stages],
        ],
        "resource_ledgers": [
            mixed_stage["resource_ledger"],
            *[stage["resource_ledger"] for stage in stages],
        ],
        "per_model": [
            {
                "model_ordinal": model_ordinal,
                "model_config_sha256": digest,
                "returned_provider_model_identity_sha256s": sorted(
                    model_returned_identities[digest]
                ),
                "request_count": model_totals[digest],
                "success_count": model_successes[digest],
                "successful_request_parameter_proof": {
                    "temperature_present": True,
                    "top_p_present": True,
                    "max_tokens_present": True,
                    "seed_present": True,
                    "native_tools_absent": True,
                    "native_tool_choice_absent": True,
                    "prompt_based_tool_protocol": True,
                },
                "safe_concurrency": int(
                    policy.per_model_safe_limits[
                        REQUIRED_MODELS[model_ordinal]
                    ]["concurrent_requests"]
                ),
                "stage_observations": [
                    {
                        "worker_concurrency": int(stage["worker_concurrency"]),
                        "effective_workers": int(stage["effective_workers"]),
                        "ran_at_locked_target": bool(
                            stage["ran_at_locked_target"]
                        ),
                        "max_rolling_rpm": int(stage["observed"]["max_rolling_rpm"]),
                        "max_rolling_admission_reservation_units_per_minute": int(
                            stage["observed"][
                                "max_rolling_admission_reservation_units_per_minute"
                            ]
                        ),
                        "max_rolling_provider_actual_tokens_per_minute": int(
                            stage["observed"][
                                "max_rolling_provider_actual_tokens_per_minute"
                            ]
                        ),
                        "max_active_requests": int(stage["observed"]["max_active_requests"]),
                        "max_active_worker_processes": int(
                            stage["observed"]["max_active_worker_processes"]
                        ),
                        "recovered_429_503_fraction": float(
                            stage["observed"]["recovered_429_503_fraction"]
                        ),
                        "max_consecutive_429_503": int(
                            stage["observed"]["max_consecutive_429_503"]
                        ),
                        "max_retry_delay_seconds_per_chain": float(
                            stage["observed"]["max_retry_delay_seconds_per_chain"]
                        ),
                    }
                    for stage in stages
                    if int(stage["stage_workload"]["generation"]["model_ordinal"])
                    == model_ordinal
                ],
            }
            for model_ordinal, digest in enumerate(model_digest_by_ordinal)
        ],
        "blind_only": True,
        "formal_results_written": False,
        "score_results_written": False,
    }
    validate_object("agentdojo_openrouter_disposable_ramp_receipt", payload)
    return payload


def load_disposable_ramp_receipt(
    path: str | Path,
    *,
    expected_policy_sha256: str,
    expected_stages: Sequence[int] = (4, 8, 16, 32),
    expected_runtime_infra_file_sha256: str | None = None,
) -> dict[str, Any]:
    from evidence_system.contracts.agentdojo_rate_lifecycle import (
        load_disposable_round_plan,
    )

    receipt = _load_receipt(path, "agentdojo_openrouter_disposable_ramp_receipt")
    _require_receipt_binding(
        receipt,
        expected_policy_sha256=expected_policy_sha256,
        expected_runtime_infra_file_sha256=expected_runtime_infra_file_sha256,
    )
    if tuple(receipt["stages"]) != tuple(expected_stages):
        raise RuntimePolicyError("disposable ramp receipt stage order mismatch")
    if tuple(receipt["suite_canaries"]) != REQUIRED_SUITES:
        raise RuntimePolicyError("disposable ramp receipt suite coverage mismatch")
    refs = list(receipt.get("stage_receipts") or [])
    expected_order = [
        (int(stage), model_ordinal)
        for stage in expected_stages
        for model_ordinal in range(len(REQUIRED_MODELS))
    ]
    if len(refs) != len(expected_order):
        raise RuntimePolicyError("disposable ramp receipt model-substage count mismatch")
    loaded_stages: list[dict[str, Any]] = []
    for (expected_stage, expected_model_ordinal), ref in zip(
        expected_order, refs, strict=True
    ):
        stage_path = _regular_nonsymlink_file(str(ref.get("path") or ""), "stage receipt")
        if ref.get("sha256") != sha256_file(stage_path):
            raise RuntimePolicyError("disposable stage receipt hash is stale")
        if int(ref.get("worker_concurrency") or 0) != int(expected_stage):
            raise RuntimePolicyError("disposable stage receipt order mismatch")
        if int(ref.get("model_ordinal") if ref.get("model_ordinal") is not None else -1) != expected_model_ordinal:
            raise RuntimePolicyError("disposable model-substage receipt order mismatch")
        loaded_stages.append(
            load_ramp_stage_receipt(
                stage_path,
                expected_policy_sha256=expected_policy_sha256,
                expected_runtime_infra_file_sha256=expected_runtime_infra_file_sha256,
                expected_scope="disposable_preflight",
            )
        )
        if int(ref.get("effective_workers") or 0) != int(
            loaded_stages[-1]["effective_workers"]
        ):
            raise RuntimePolicyError("disposable stage effective-worker ref differs")
    if list(receipt.get("stage_workload_sha256s") or []) != [
        stage.get("stage_workload_sha256") for stage in loaded_stages
    ]:
        raise RuntimePolicyError("disposable ramp workload binding mismatch")
    policy = load_runtime_policy(
        dict(loaded_stages[0].get("runtime_policy") or {}),
        expected_semantic_sha256=expected_policy_sha256,
    )
    pre_ref = dict(receipt.get("pre_ramp_credential_receipt") or {})
    post_ref = dict(receipt.get("post_ramp_credential_receipt") or {})
    mixed_ref = dict(receipt.get("global_mixed_canary_receipt") or {})
    validation_plan_ref = dict(receipt.get("validation_round_plan") or {})
    measurement_ref = dict(receipt.get("measurement_receipt") or {})
    finalization_ref = dict(receipt.get("policy_finalization_receipt") or {})
    pre_path = _regular_nonsymlink_file(str(pre_ref.get("path") or ""), "pre-ramp credential receipt")
    post_path = _regular_nonsymlink_file(str(post_ref.get("path") or ""), "post-ramp credential receipt")
    mixed_path = _regular_nonsymlink_file(str(mixed_ref.get("path") or ""), "global mixed-canary receipt")
    validation_plan_path = _regular_nonsymlink_file(
        str(validation_plan_ref.get("path") or ""), "validation round plan"
    )
    measurement_path = _regular_nonsymlink_file(
        str(measurement_ref.get("path") or ""), "measurement aggregate receipt"
    )
    finalization_path = _regular_nonsymlink_file(
        str(finalization_ref.get("path") or ""), "policy finalization receipt"
    )
    if (
        pre_ref.get("sha256") != sha256_file(pre_path)
        or post_ref.get("sha256") != sha256_file(post_path)
        or mixed_ref.get("sha256") != sha256_file(mixed_path)
        or validation_plan_ref.get("sha256") != sha256_file(validation_plan_path)
        or validation_plan_ref.get("definition_sha256")
        != load_disposable_round_plan(validation_plan_path)["definition_sha256"]
        or measurement_ref.get("sha256") != sha256_file(measurement_path)
        or finalization_ref.get("sha256") != sha256_file(finalization_path)
    ):
        raise RuntimePolicyError("disposable ramp credential receipt hash is stale")
    rebuilt = build_disposable_ramp_receipt(
        policy,
        runtime_infra_file_sha256=str(receipt["runtime_infra_file_sha256"]),
        stage_receipt_paths=[str(ref["path"]) for ref in refs],
        global_mixed_canary_receipt_path=mixed_path,
        pre_ramp_credential_receipt_path=pre_path,
        post_ramp_credential_receipt_path=post_path,
        validation_round_plan_path=validation_plan_path,
        measurement_receipt_path=measurement_path,
        policy_finalization_receipt_path=finalization_path,
        created_at=str(receipt["created_at"]),
    )
    if receipt != rebuilt:
        raise RuntimePolicyError("disposable ramp receipt differs from recomputed stages")
    if receipt.get("runtime_code") != runtime_control_code_snapshot():
        raise RuntimePolicyError("disposable ramp runtime code is stale")
    if receipt.get("worker_failures") != 0 or receipt.get(
        "unresolved_http_429_or_503"
    ) != 0:
        raise RuntimePolicyError("disposable ramp receipt has unresolved failures")
    return receipt


def build_rate_measurement_receipt(
    candidate_policy: RuntimePolicy,
    *,
    candidate_policy_path: str | Path,
    runtime_infra_path: str | Path,
    agents_config_path: str | Path,
    global_mixed_canary_receipt_path: str | Path,
    stage_receipt_paths: Sequence[str | Path],
    pre_ramp_credential_receipt_path: str | Path,
    measurement_round_plan_path: str | Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Derive conservative rate recommendations from provisional real-request stages."""

    if candidate_policy.lifecycle_status != "provisional":
        raise RuntimePolicyError("rate measurement requires a provisional candidate policy")
    from evidence_system.contracts.agentdojo_rate_lifecycle import (
        load_disposable_round_plan,
    )

    round_plan_file = _regular_nonsymlink_file(
        measurement_round_plan_path, "measurement round plan"
    )
    round_plan = load_disposable_round_plan(round_plan_file)
    round_definition = dict(round_plan["definition"])
    round_artifacts = dict(round_plan["artifact_namespace"])
    if (
        round_definition["round_kind"] != "exploratory_measurement"
        or round_definition["runtime_policy"]["semantic_sha256"]
        != candidate_policy.semantic_sha256
    ):
        raise RuntimePolicyError("measurement aggregate uses the wrong round plan")
    candidate_file = _regular_nonsymlink_file(
        candidate_policy_path, "candidate runtime policy"
    )
    if load_runtime_policy(
        json.loads(candidate_file.read_text(encoding="utf-8")),
        expected_semantic_sha256=candidate_policy.semantic_sha256,
    ).raw != candidate_policy.raw:
        raise RuntimePolicyError("candidate runtime policy file differs from memory")
    infra_file = _regular_nonsymlink_file(runtime_infra_path, "runtime infra")
    agents_file = _regular_nonsymlink_file(agents_config_path, "agents config")
    agent_models = _measurement_agent_models(agents_file)
    if (
        round_definition["runtime_infra"]["sha256"] != sha256_file(infra_file)
        or round_definition["agents_config"]["sha256"] != sha256_file(agents_file)
    ):
        raise RuntimePolicyError("measurement round-plan infra/agents binding differs")
    credential_file = _regular_nonsymlink_file(
        pre_ramp_credential_receipt_path, "pre-ramp credential receipt"
    )
    credential = load_credential_probe_receipt(
        credential_file,
        expected_policy_sha256=candidate_policy.semantic_sha256,
        expected_runtime_infra_file_sha256=sha256_file(infra_file),
        expected_probe_phase="pre_ramp",
    )
    credential_round_ref = credential.get("round_plan")
    if (
        not isinstance(credential_round_ref, Mapping)
        or credential_round_ref.get("sha256") != sha256_file(round_plan_file)
        or credential_round_ref.get("definition_sha256")
        != round_plan["definition_sha256"]
    ):
        raise RuntimePolicyError(
            "measurement credential is not bound to its round plan"
        )
    if _portable_path(credential_file) != round_artifacts["pre_credential_receipt"]:
        raise RuntimePolicyError(
            "measurement credential receipt is outside the SHA-derived round namespace"
        )
    mixed_file = _regular_nonsymlink_file(
        global_mixed_canary_receipt_path, "measurement mixed-canary receipt"
    )
    mixed = load_ramp_stage_receipt(
        mixed_file,
        expected_policy_sha256=candidate_policy.semantic_sha256,
        expected_runtime_infra_file_sha256=sha256_file(infra_file),
        expected_scope="exploratory_measurement",
    )
    if (
        int(mixed["worker_concurrency"]) != 4
        or mixed["stage_workload"]["generation"]["workload_kind"]
        != "global_mixed_canary"
        or int(mixed["stage_workload"]["planned_job_count"])
        != 4 * len(REQUIRED_MODELS)
        or mixed["observed"]["thresholds_passed"] is not True
    ):
        raise RuntimePolicyError("measurement mixed canary is invalid")
    planned_stages = list(round_definition["stages"])
    if mixed["stage_workload_sha256"] != planned_stages[0]["workload_sha256"]:
        raise RuntimePolicyError("measurement mixed receipt differs from its plan")
    if _portable_path(mixed_file) != round_artifacts["stages"][0]["stage_receipt"]:
        raise RuntimePolicyError("measurement mixed receipt path is outside its round")
    expected_order = [
        (stage, model_ordinal)
        for stage in candidate_policy.ramp_stages
        for model_ordinal in range(len(REQUIRED_MODELS))
    ]
    if len(stage_receipt_paths) != len(expected_order):
        raise RuntimePolicyError("rate measurement requires exactly twelve substages")
    stage_refs: list[dict[str, Any]] = []
    per_model_observations: dict[int, list[Mapping[str, Any]]] = {
        ordinal: [] for ordinal in range(len(REQUIRED_MODELS))
    }
    prior_safe_by_model = {ordinal: 4 for ordinal in range(len(REQUIRED_MODELS))}
    promotion_open_by_model = {
        ordinal: True for ordinal in range(len(REQUIRED_MODELS))
    }
    for plan_index, ((expected_stage, expected_model), raw_path) in enumerate(zip(
        expected_order, stage_receipt_paths, strict=True
    ), start=1):
        stage_file = _regular_nonsymlink_file(raw_path, "measurement stage receipt")
        stage = load_ramp_stage_receipt(
            stage_file,
            expected_policy_sha256=candidate_policy.semantic_sha256,
            expected_runtime_infra_file_sha256=sha256_file(infra_file),
            expected_scope="exploratory_measurement",
        )
        generation = stage["stage_workload"]["generation"]
        if (
            int(stage["worker_concurrency"]) != expected_stage
            or int(generation["model_ordinal"]) != expected_model
            or generation["workload_kind"] != "per_model_ramp"
        ):
            raise RuntimePolicyError("measurement stage/model order differs")
        expected_effective = (
            expected_stage
            if promotion_open_by_model[expected_model]
            else prior_safe_by_model[expected_model]
        )
        if int(stage["effective_workers"]) != expected_effective:
            raise RuntimePolicyError(
                "measurement stage violated the prior-safe adaptive hold rule"
            )
        if int(stage["prior_safe_workers"]) != prior_safe_by_model[expected_model]:
            raise RuntimePolicyError("measurement prior-safe worker chain differs")
        if stage["status"] == "passed" and stage["ran_at_locked_target"] is True:
            prior_safe_by_model[expected_model] = expected_stage
        else:
            promotion_open_by_model[expected_model] = False
        if int(stage["resulting_safe_workers"]) != prior_safe_by_model[expected_model]:
            raise RuntimePolicyError("measurement resulting-safe worker chain differs")
        if stage["stage_workload_sha256"] != planned_stages[plan_index][
            "workload_sha256"
        ]:
            raise RuntimePolicyError("measurement stage receipt differs from its plan")
        expected_artifact = round_artifacts["stages"][plan_index]
        if (
            _portable_path(stage_file) != expected_artifact["stage_receipt"]
            or stage["blind_health_ledger"]["path"]
            != expected_artifact["blind_health_ledger"]
            or stage["resource_ledger"]["path"]
            != expected_artifact["resource_ledger"]
        ):
            raise RuntimePolicyError(
                "measurement stage artifacts are outside the SHA-derived round namespace"
            )
        per_model_observations[expected_model].append(stage)
        stage_refs.append(
            {
                **_locked_file_ref(stage_file),
                "worker_concurrency": expected_stage,
                "effective_workers": int(stage["effective_workers"]),
                "model_ordinal": expected_model,
            }
        )
    if {
        str(stage.get("credential_fingerprint_sha256") or "")
        for observations in per_model_observations.values()
        for stage in observations
    } | {str(mixed.get("credential_fingerprint_sha256") or "")} != {
        str(credential["credential_fingerprint_sha256"])
    }:
        raise RuntimePolicyError(
            "measurement stages and pre-ramp credential probe used different keys"
        )
    per_model: list[dict[str, Any]] = []
    for ordinal, model in enumerate(agent_models):
        observations = per_model_observations[ordinal]
        safe_prefix: list[Mapping[str, Any]] = []
        for stage in observations:
            if (
                stage["status"] == "passed"
                and stage["observed"]["thresholds_passed"] is True
            ):
                safe_prefix.append(stage)
            else:
                break
        if not safe_prefix:
            raise RuntimePolicyError(
                f"model ordinal {ordinal} has no passing stage-4 measurement"
            )
        maximum_concurrency = int(safe_prefix[-1]["worker_concurrency"])
        attempted_measured_rpm = max(
            int(stage["observed"]["max_rolling_rpm"]) for stage in observations
        )
        attempted_measured_reservation_units = max(
            int(
                stage["observed"][
                    "max_rolling_admission_reservation_units_per_minute"
                ]
            )
            for stage in observations
        )
        attempted_provider_actual_tokens = max(
            int(
                stage["observed"][
                    "max_rolling_provider_actual_tokens_per_minute"
                ]
            )
            for stage in observations
        )
        measured_rpm = max(
            int(stage["observed"]["max_rolling_rpm"]) for stage in safe_prefix
        )
        measured_reservation_units = max(
            int(
                stage["observed"][
                    "max_rolling_admission_reservation_units_per_minute"
                ]
            )
            for stage in safe_prefix
        )
        measured_provider_actual_tokens = max(
            int(
                stage["observed"][
                    "max_rolling_provider_actual_tokens_per_minute"
                ]
            )
            for stage in safe_prefix
        )
        if measured_rpm <= 0 or measured_reservation_units <= 0:
            raise RuntimePolicyError(
                "measurement stage observed no usable RPM/admission reservation rate"
            )
        per_model.append(
            {
                **model,
                "measured_max_rolling_rpm": measured_rpm,
                "measured_max_rolling_admission_reservation_units_per_minute": (
                    measured_reservation_units
                ),
                "measured_max_rolling_provider_actual_tokens_per_minute": (
                    measured_provider_actual_tokens
                ),
                "attempted_max_rolling_rpm": attempted_measured_rpm,
                "attempted_max_rolling_admission_reservation_units_per_minute": (
                    attempted_measured_reservation_units
                ),
                "attempted_max_rolling_provider_actual_tokens_per_minute": (
                    attempted_provider_actual_tokens
                ),
                "maximum_validated_concurrency": maximum_concurrency,
                "recommended_requests_per_minute": min(
                    candidate_policy.requests_per_minute,
                    max(1, math.floor(measured_rpm * 0.8)),
                ),
                "recommended_admission_reservation_units_per_minute": min(
                    candidate_policy.tokens_per_minute,
                    max(1, math.floor(measured_reservation_units * 0.8)),
                ),
                "recommended_concurrent_requests": maximum_concurrency,
                "stage_outcomes": [
                    {
                        "worker_concurrency": int(stage["worker_concurrency"]),
                        "effective_workers": int(stage["effective_workers"]),
                        "ran_at_locked_target": bool(
                            stage["ran_at_locked_target"]
                        ),
                        "status": str(stage["status"]),
                        "thresholds_passed": bool(
                            stage["observed"]["thresholds_passed"]
                        ),
                        "achieved_successful_job_throughput_per_minute": float(
                            stage["observed"][
                                "achieved_successful_job_throughput_per_minute"
                            ]
                        ),
                        "achieved_admission_reservation_units_throughput_per_minute": float(
                            stage["observed"][
                                "achieved_admission_reservation_units_throughput_per_minute"
                            ]
                        ),
                    }
                    for stage in observations
                ],
            }
        )
    # Formal execution is locked to serial, single-model batches.  Therefore
    # one slower model must not collapse the independently demonstrated safe
    # rate/concurrency of the other two.  The global limiter may use the
    # maximum per-model ceiling only because it separately rejects cross-model
    # lease overlap in formal scope; each active model remains subject to its
    # own limiter row.  Mixed execution is confined to the independent
    # disposable four-worker canary.
    global_rpm = max(int(row["recommended_requests_per_minute"]) for row in per_model)
    global_reservation_units = max(
        int(row["recommended_admission_reservation_units_per_minute"])
        for row in per_model
    )
    global_concurrency = max(
        int(row["recommended_concurrent_requests"]) for row in per_model
    )
    payload = {
        "schema_version": RATE_MEASUREMENT_RECEIPT_SCHEMA_VERSION,
        "status": "measured",
        "created_at": _validated_timestamp(created_at),
        "candidate_runtime_policy": {
            **_locked_file_ref(candidate_file),
            "semantic_sha256": candidate_policy.semantic_sha256,
            "operational_definition_sha256": (
                candidate_policy.operational_definition_sha256
            ),
        },
        "runtime_infra": _locked_file_ref(infra_file),
        "base_agents_config": _locked_file_ref(agents_file),
        "model_catalog_sha256": str(credential["model_catalog_sha256"]),
        "credential_fingerprint_sha256": str(
            credential["credential_fingerprint_sha256"]
        ),
        "management_audit_fingerprint_sha256": credential[
            "management_audit_fingerprint_sha256"
        ],
        "management_audit_status": credential["management_audit_status"],
        "pre_ramp_credential_receipt": _locked_file_ref(credential_file),
        "measurement_round_plan": {
            **_locked_file_ref(round_plan_file),
            "definition_sha256": str(round_plan["definition_sha256"]),
        },
        "global_mixed_canary_receipt": _locked_file_ref(mixed_file),
        "stage_receipts": stage_refs,
        "global": {
            "measured_max_rolling_rpm": max(
                max(int(row["attempted_max_rolling_rpm"]) for row in per_model),
                int(mixed["observed"]["max_rolling_rpm"]),
            ),
            "measured_max_rolling_admission_reservation_units_per_minute": max(
                max(
                    int(
                        row[
                            "attempted_max_rolling_admission_reservation_units_per_minute"
                        ]
                    )
                    for row in per_model
                ),
                int(
                    mixed["observed"][
                        "max_rolling_admission_reservation_units_per_minute"
                    ]
                ),
            ),
            "measured_max_rolling_provider_actual_tokens_per_minute": max(
                max(
                    int(
                        row[
                            "attempted_max_rolling_provider_actual_tokens_per_minute"
                        ]
                    )
                    for row in per_model
                ),
                int(
                    mixed["observed"][
                        "max_rolling_provider_actual_tokens_per_minute"
                    ]
                ),
            ),
            "maximum_validated_concurrency": global_concurrency,
            "recommended_requests_per_minute": global_rpm,
            "recommended_admission_reservation_units_per_minute": (
                global_reservation_units
            ),
            "recommended_concurrent_requests": global_concurrency,
        },
        "per_model": per_model,
        "recommendation_algorithm": (
            "floor_observed_admission_reservation_rate_times_0_80"
        ),
        "recommendation_definition_sha256": (
            RATE_MEASUREMENT_SAFE_MARGIN_DEFINITION_SHA256
        ),
        "requested_exploratory_envelope": dict(
            candidate_policy.raw["execution_eligibility"][
                "requested_measurement_envelope"
            ]
        ),
        "provider_error_totals": {
            "http_429": sum(
                int(stage["observed"]["http_429"])
                for stages in per_model_observations.values()
                for stage in stages
            )
            + int(mixed["observed"]["http_429"]),
            "http_503": sum(
                int(stage["observed"]["http_503"])
                for stages in per_model_observations.values()
                for stage in stages
            )
            + int(mixed["observed"]["http_503"]),
            "http_429_openrouter_or_upstream_unspecified": sum(
                int(
                    stage["observed"]["provider_error_categories"][
                        "http_429_openrouter_or_upstream_unspecified"
                    ]
                )
                for stages in per_model_observations.values()
                for stage in stages
            )
            + int(
                mixed["observed"]["provider_error_categories"][
                    "http_429_openrouter_or_upstream_unspecified"
                ]
            ),
            "http_503_service_origin_unspecified": sum(
                int(
                    stage["observed"]["provider_error_categories"][
                        "http_503_service_origin_unspecified"
                    ]
                )
                for stages in per_model_observations.values()
                for stage in stages
            )
            + int(
                mixed["observed"]["provider_error_categories"][
                    "http_503_service_origin_unspecified"
                ]
            ),
            "transport_or_non_http": sum(
                int(
                    stage["observed"]["provider_error_categories"][
                        "transport_or_non_http"
                    ]
                )
                for stages in per_model_observations.values()
                for stage in stages
            )
            + int(
                mixed["observed"]["provider_error_categories"][
                    "transport_or_non_http"
                ]
            ),
        },
        "runtime_snapshot": execution_runtime_snapshot(),
        "blind_only": True,
        "contains_prompt_response_trajectory_evaluator_or_label": False,
    }
    validate_object("agentdojo_openrouter_rate_measurement_receipt", payload)
    return payload


def load_rate_measurement_receipt(
    path: str | Path,
    *,
    expected_candidate_operational_definition_sha256: str,
    expected_runtime_infra_file_sha256: str,
    expected_agents_config_file_sha256: str,
) -> dict[str, Any]:
    receipt = _load_receipt(path, "agentdojo_openrouter_rate_measurement_receipt")
    candidate_ref = dict(receipt["candidate_runtime_policy"])
    if candidate_ref["operational_definition_sha256"] != _validate_digest(
        expected_candidate_operational_definition_sha256,
        "expected_candidate_operational_definition_sha256",
    ):
        raise RuntimePolicyError("measurement candidate operational definition differs")
    if receipt["runtime_infra"]["sha256"] != _validate_digest(
        expected_runtime_infra_file_sha256,
        "expected_runtime_infra_file_sha256",
    ) or receipt["base_agents_config"]["sha256"] != _validate_digest(
        expected_agents_config_file_sha256,
        "expected_agents_config_file_sha256",
    ):
        raise RuntimePolicyError("measurement infra/agents binding differs")
    refs = [
        receipt["candidate_runtime_policy"],
        receipt["runtime_infra"],
        receipt["base_agents_config"],
        receipt["pre_ramp_credential_receipt"],
        receipt["measurement_round_plan"],
        receipt["global_mixed_canary_receipt"],
        *receipt["stage_receipts"],
    ]
    for ref in refs:
        current = _regular_nonsymlink_file(str(ref["path"]), "measurement source")
        if ref["sha256"] != sha256_file(current):
            raise RuntimePolicyError("measurement source reference is stale")
    from evidence_system.contracts.agentdojo_rate_lifecycle import (
        load_disposable_round_plan,
    )

    measurement_plan = load_disposable_round_plan(
        str(receipt["measurement_round_plan"]["path"])
    )
    if receipt["measurement_round_plan"]["definition_sha256"] != measurement_plan[
        "definition_sha256"
    ]:
        raise RuntimePolicyError("measurement round-plan definition hash differs")
    candidate_file = _regular_nonsymlink_file(
        str(candidate_ref["path"]), "candidate policy"
    )
    candidate = load_runtime_policy(
        json.loads(candidate_file.read_text(encoding="utf-8")),
        expected_semantic_sha256=str(candidate_ref["semantic_sha256"]),
    )
    rebuilt = build_rate_measurement_receipt(
        candidate,
        candidate_policy_path=candidate_file,
        runtime_infra_path=str(receipt["runtime_infra"]["path"]),
        agents_config_path=str(receipt["base_agents_config"]["path"]),
        global_mixed_canary_receipt_path=str(
            receipt["global_mixed_canary_receipt"]["path"]
        ),
        stage_receipt_paths=[str(ref["path"]) for ref in receipt["stage_receipts"]],
        pre_ramp_credential_receipt_path=str(
            receipt["pre_ramp_credential_receipt"]["path"]
        ),
        measurement_round_plan_path=str(
            receipt["measurement_round_plan"]["path"]
        ),
        created_at=str(receipt["created_at"]),
    )
    if receipt != rebuilt:
        raise RuntimePolicyError("rate measurement receipt differs from source stages")
    return receipt


def derive_finalized_runtime_policy(
    candidate_policy: RuntimePolicy,
    *,
    measurement_receipt_path: str | Path,
) -> dict[str, Any]:
    if candidate_policy.lifecycle_status != "provisional":
        raise RuntimePolicyError("only a provisional policy can be finalized")
    measurement_file = _regular_nonsymlink_file(
        measurement_receipt_path, "rate measurement receipt"
    )
    measurement = load_rate_measurement_receipt(
        measurement_file,
        expected_candidate_operational_definition_sha256=(
            candidate_policy.operational_definition_sha256
        ),
        expected_runtime_infra_file_sha256=str(
            json.loads(measurement_file.read_text(encoding="utf-8"))["runtime_infra"][
                "sha256"
            ]
        ),
        expected_agents_config_file_sha256=str(
            json.loads(measurement_file.read_text(encoding="utf-8"))[
                "base_agents_config"
            ]["sha256"]
        ),
    )
    finalized = json.loads(json.dumps(dict(candidate_policy.raw), ensure_ascii=True))
    global_limits = dict(measurement["global"])
    finalized["lifecycle"] = {
        "status": "finalized",
        "measurement_receipt_path": _portable_path(measurement_file),
        "measurement_receipt_sha256": sha256_file(measurement_file),
    }
    finalized["execution_eligibility"]["mode"] = "finalized_validation"
    finalized["execution_eligibility"]["formal_execution_allowed"] = True
    effective = finalized["operational_override"]["effective_values"]
    effective["requests_per_minute"] = int(
        global_limits["recommended_requests_per_minute"]
    )
    effective["tokens_per_minute"] = int(
        global_limits["recommended_admission_reservation_units_per_minute"]
    )
    effective["global_concurrent_requests"] = int(
        global_limits["recommended_concurrent_requests"]
    )
    finalized["max_concurrent_requests"] = effective["global_concurrent_requests"]
    finalized["requests_per_minute"] = effective["requests_per_minute"]
    finalized["tokens_per_minute"] = effective["tokens_per_minute"]
    finalized["operational_override"]["per_model_safe_limits"] = [
        {
            "model_id": row["model_id"],
            "requests_per_minute": int(row["recommended_requests_per_minute"]),
            "tokens_per_minute": int(
                row["recommended_admission_reservation_units_per_minute"]
            ),
            "concurrent_requests": int(row["recommended_concurrent_requests"]),
        }
        for row in measurement["per_model"]
    ]
    finalized["operational_override"]["execution_key_fingerprint_sha256"] = str(
        measurement["credential_fingerprint_sha256"]
    )
    return dict(load_runtime_policy(finalized).raw)


def build_policy_finalization_receipt(
    *,
    candidate_policy_path: str | Path,
    measurement_receipt_path: str | Path,
    finalized_policy_path: str | Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    candidate_file = _regular_nonsymlink_file(candidate_policy_path, "candidate policy")
    measurement_file = _regular_nonsymlink_file(
        measurement_receipt_path, "measurement receipt"
    )
    finalized_file = _regular_nonsymlink_file(finalized_policy_path, "finalized policy")
    candidate = load_runtime_policy(
        json.loads(candidate_file.read_text(encoding="utf-8"))
    )
    expected_finalized = derive_finalized_runtime_policy(
        candidate, measurement_receipt_path=measurement_file
    )
    finalized = load_runtime_policy(
        json.loads(finalized_file.read_text(encoding="utf-8"))
    )
    if finalized.raw != expected_finalized:
        raise RuntimePolicyError("finalized runtime policy differs from measurement")
    payload = {
        "schema_version": POLICY_FINALIZATION_RECEIPT_SCHEMA_VERSION,
        "status": "finalized_from_measurement",
        "created_at": _validated_timestamp(created_at),
        "candidate_runtime_policy": {
            **_locked_file_ref(candidate_file),
            "semantic_sha256": candidate.semantic_sha256,
            "operational_definition_sha256": candidate.operational_definition_sha256,
        },
        "measurement_receipt": _locked_file_ref(measurement_file),
        "finalized_runtime_policy": {
            **_locked_file_ref(finalized_file),
            "semantic_sha256": finalized.semantic_sha256,
            "operational_definition_sha256": finalized.operational_definition_sha256,
        },
        "runtime_snapshot": execution_runtime_snapshot(),
        "secret_material_recorded": False,
    }
    validate_object("agentdojo_openrouter_policy_finalization_receipt", payload)
    return payload


def load_policy_finalization_receipt(path: str | Path) -> dict[str, Any]:
    receipt = _load_receipt(path, "agentdojo_openrouter_policy_finalization_receipt")
    for field in (
        "candidate_runtime_policy",
        "measurement_receipt",
        "finalized_runtime_policy",
    ):
        ref = dict(receipt[field])
        current = _regular_nonsymlink_file(str(ref["path"]), field)
        if ref["sha256"] != sha256_file(current):
            raise RuntimePolicyError(f"policy finalization {field} is stale")
    rebuilt = build_policy_finalization_receipt(
        candidate_policy_path=str(receipt["candidate_runtime_policy"]["path"]),
        measurement_receipt_path=str(receipt["measurement_receipt"]["path"]),
        finalized_policy_path=str(receipt["finalized_runtime_policy"]["path"]),
        created_at=str(receipt["created_at"]),
    )
    if receipt != rebuilt or receipt["runtime_snapshot"] != execution_runtime_snapshot():
        raise RuntimePolicyError("policy finalization receipt differs or is stale")
    return receipt


def _measurement_agent_models(agents_file: Path) -> list[dict[str, str]]:
    agents = load_json_or_yaml(agents_file)
    if not isinstance(agents, Mapping) or not isinstance(
        agents.get("experimental_agents"), Mapping
    ):
        raise RuntimePolicyError("measurement agents config is invalid")
    roles = agents["experimental_agents"]
    rows: list[dict[str, str]] = []
    for agent_id, model_id in zip(REQUIRED_AGENT_IDS, REQUIRED_MODELS, strict=True):
        role = roles.get(agent_id)
        if not isinstance(role, Mapping) or role.get("provider") != "openrouter" or role.get(
            "model"
        ) != model_id:
            raise RuntimePolicyError("measurement agent/model mapping differs")
        rows.append(
            {
                "agent_id": agent_id,
                "model_id": model_id,
                "model_config_sha256": agentdojo_model_config_sha256(
                    agent_id=agent_id,
                    provider=str(role["provider"]),
                    model_id=str(role["model"]),
                    temperature=float(role["temperature"]),
                    max_tokens=int(role["max_tokens"]),
                    timeout_seconds=int(role["timeout_seconds"]),
                    retry=int(role["retry"]),
                ),
            }
        )
    return rows


class BlindHealthLedger:
    """Append-only JSONL restricted to non-evidence operational metadata."""

    def __init__(
        self,
        paths: Sequence[str | Path],
        *,
        policy_sha256: str,
        session_id: str | None = None,
        host_boot_id: str | None = None,
        shared_root: str | Path | None = None,
        shared_group: str | None = None,
        credential_fingerprint_sha256: str | None = None,
    ) -> None:
        self.paths = tuple(Path(path) for path in paths)
        if not self.paths:
            raise RuntimePolicyError("blind health ledger requires at least one path")
        self.policy_sha256 = policy_sha256.removeprefix("sha256:")
        if (session_id is None) != (host_boot_id is None):
            raise RuntimePolicyError(
                "blind health session_id and host_boot_id must be supplied together"
            )
        self.session_id = (
            None if session_id is None else _validate_session_id(session_id)
        )
        self.host_boot_id = (
            None if host_boot_id is None else _validate_host_boot_id(host_boot_id)
        )
        self.credential_fingerprint_sha256 = (
            None
            if credential_fingerprint_sha256 is None
            else _validate_digest(
                credential_fingerprint_sha256,
                "blind health credential_fingerprint_sha256",
            )
        )
        if (shared_root is None) != (shared_group is None):
            raise RuntimePolicyError(
                "blind health shared_root and shared_group must be supplied together"
            )
        self.shared_root = None if shared_root is None else Path(shared_root).absolute()
        try:
            self.shared_gid = (
                None if shared_group is None else int(grp.getgrnam(shared_group).gr_gid)
            )
        except KeyError as exc:
            raise RuntimePolicyError("blind health shared group does not exist") from exc
        self._thread_lock = threading.Lock()

    def record(self, *, event_type: str, outcome: str, **fields: Any) -> dict[str, Any]:
        record = {
            "schema_version": BLIND_HEALTH_SCHEMA_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": str(event_type),
            "policy_sha256": self.policy_sha256,
            "outcome": str(outcome),
            **fields,
        }
        if self.session_id is not None:
            record["session_id"] = self.session_id
            record["host_boot_id"] = self.host_boot_id
        if self.credential_fingerprint_sha256 is not None:
            record["credential_fingerprint_sha256"] = (
                self.credential_fingerprint_sha256
            )
        validate_blind_health_record(record)
        line = json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        with self._thread_lock:
            for path in self.paths:
                shared = self._is_shared_path(path)
                if shared:
                    _assert_directory_chain_no_symlinks(
                        path.parent, anchor=self.shared_root
                    )
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(
                    os, "O_NOFOLLOW", 0
                )
                descriptor = os.open(path, flags, 0o640 if shared else 0o600)
                try:
                    file_stat = os.fstat(descriptor)
                    if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                        raise RuntimePolicyError(
                            "blind health ledger must be a single-link regular file"
                        )
                    if shared:
                        os.fchmod(descriptor, 0o640)
                        os.fchown(descriptor, -1, int(self.shared_gid))
                    else:
                        os.fchmod(descriptor, 0o600)
                    with os.fdopen(
                        descriptor, "a", encoding="utf-8", closefd=False
                    ) as handle:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                        try:
                            handle.write(line + "\n")
                            handle.flush()
                            os.fsync(handle.fileno())
                        finally:
                            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)
        return record

    def _is_shared_path(self, path: Path) -> bool:
        if self.shared_root is None:
            return False
        try:
            path.parent.absolute().relative_to(self.shared_root.absolute())
        except ValueError:
            return False
        return True


class SealedIncidentLedger:
    """Restricted incident-to-job mapping that is joined only after checklist freeze."""

    def __init__(self, path: str | Path, *, policy_sha256: str) -> None:
        self.path = Path(path)
        self.policy_sha256 = policy_sha256.removeprefix("sha256:")
        self._thread_lock = threading.Lock()

    def record(
        self,
        *,
        incident_id: str,
        job: Mapping[str, Any],
        error_category: str,
        error_origin: str,
        http_status: int | None = None,
        attempt_index: int | None = None,
    ) -> dict[str, Any]:
        record = {
            "schema_version": SEALED_INCIDENT_SCHEMA_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_id": incident_id,
            "job_identity_sha256": job_identity_sha256(job),
            "policy_sha256": self.policy_sha256,
            "job_id": _safe_identity_value(job, "job_id"),
            "case_unit_id": _safe_identity_value(job, "case_unit_id"),
            "record_slot_id": _safe_identity_value(job, "record_slot_id"),
            "error_category": error_category,
            "error_origin": error_origin,
            "http_status": http_status,
            "attempt_index": attempt_index,
        }
        validate_sealed_incident_record(record)
        line = json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        with self._thread_lock:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            _assert_directory_chain_no_symlinks(self.path.parent)
            os.chmod(self.path.parent, 0o700)
            descriptor = os.open(
                self.path,
                os.O_APPEND
                | os.O_CREAT
                | os.O_WRONLY
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            try:
                file_stat = os.fstat(descriptor)
                if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                    raise RuntimePolicyError(
                        "sealed incident ledger must be a single-link regular file"
                    )
                os.fchmod(descriptor, 0o600)
                with os.fdopen(descriptor, "a", encoding="utf-8", closefd=False) as handle:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    try:
                        handle.write(line + "\n")
                        handle.flush()
                        os.fsync(handle.fileno())
                    finally:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
            directory_descriptor = os.open(
                self.path.parent,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        return record


def job_identity_sha256(job: Mapping[str, Any]) -> str:
    """Hash the minimal join identity; the blind ledger never stores its source fields."""

    identity = {
        key: _safe_identity_value(job, key)
        for key in ("job_id", "case_unit_id", "record_slot_id")
    }
    return sha256_object(identity)


def validate_sealed_incident_record(record: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "timestamp",
        "incident_id",
        "job_identity_sha256",
        "policy_sha256",
        "job_id",
        "case_unit_id",
        "record_slot_id",
        "error_category",
        "error_origin",
        "http_status",
        "attempt_index",
    }
    _require_exact_keys(record, expected, field="sealed incident record")
    if record.get("schema_version") != SEALED_INCIDENT_SCHEMA_VERSION:
        raise RuntimePolicyError("sealed incident schema_version mismatch")
    if record.get("error_category") not in _SEALED_INCIDENT_CATEGORIES:
        raise RuntimePolicyError("sealed incident error_category is not allowed")
    if record.get("error_origin") not in _SEALED_INCIDENT_ORIGINS:
        raise RuntimePolicyError("sealed incident error_origin is not allowed")
    for key in (
        "timestamp",
        "incident_id",
        "job_identity_sha256",
        "policy_sha256",
        "job_id",
        "case_unit_id",
        "record_slot_id",
    ):
        value = record.get(key)
        if not isinstance(value, str) or not value or len(value) > 512 or "\n" in value:
            raise RuntimePolicyError(f"sealed incident {key} is invalid")
    for key in ("job_identity_sha256", "policy_sha256"):
        digest = str(record[key]).removeprefix("sha256:")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise RuntimePolicyError(f"sealed incident {key} is invalid")


def validate_blind_health_record(record: Mapping[str, Any]) -> None:
    extras = sorted(set(record) - _ALLOWED_HEALTH_FIELDS)
    if extras:
        raise RuntimePolicyError(
            f"blind health record contains forbidden field(s): {', '.join(extras)}"
        )
    if record.get("schema_version") != BLIND_HEALTH_SCHEMA_VERSION:
        raise RuntimePolicyError("blind health record schema_version mismatch")
    for key in ("timestamp", "event_type", "policy_sha256", "outcome"):
        if not isinstance(record.get(key), str) or not str(record[key]).strip():
            raise RuntimePolicyError(f"blind health record requires non-empty {key}")
    if record["event_type"] not in _ALLOWED_HEALTH_EVENT_TYPES:
        raise RuntimePolicyError("blind health event_type is not allowed")
    if record["outcome"] not in _ALLOWED_HEALTH_OUTCOMES:
        raise RuntimePolicyError("blind health outcome is not allowed")
    if record.get("incident_id") is not None:
        incident_id = record["incident_id"]
        if not isinstance(incident_id, str) or not incident_id or len(incident_id) > 128:
            raise RuntimePolicyError("blind health incident_id is invalid")
    for key in (
        "job_identity_sha256",
        "model_config_sha256",
        "returned_model_identity_sha256",
        "credential_fingerprint_sha256",
    ):
        if record.get(key) is not None:
            value_digest = str(record[key]).removeprefix("sha256:")
            if len(value_digest) != 64 or any(
                char not in "0123456789abcdef" for char in value_digest
            ):
                raise RuntimePolicyError(f"blind health {key} is invalid")
    if record.get("request_chain_id") is not None:
        chain_id = record["request_chain_id"]
        if (
            not isinstance(chain_id, str)
            or not chain_id.startswith("req-")
            or len(chain_id) != 36
            or any(char not in "0123456789abcdef" for char in chain_id[4:])
        ):
            raise RuntimePolicyError("blind health request_chain_id is invalid")
    digest = str(record["policy_sha256"]).removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RuntimePolicyError("blind health policy_sha256 is invalid")
    try:
        datetime.fromisoformat(str(record["timestamp"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimePolicyError("blind health timestamp is invalid") from exc
    forbidden_markers = ("prompt", "response", "trajectory", "evaluator", "label", "case")
    for key in record:
        lowered = key.lower()
        if any(marker in lowered for marker in forbidden_markers):
            raise RuntimePolicyError(f"blind health field is evidence-bearing: {key}")
    for key, value in record.items():
        if key in {
            "schema_version",
            "timestamp",
            "event_type",
            "policy_sha256",
            "outcome",
            "incident_id",
            "job_identity_sha256",
            "model_config_sha256",
            "returned_model_identity_sha256",
            "credential_fingerprint_sha256",
            "request_chain_id",
            "session_id",
            "host_boot_id",
        }:
            continue
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise RuntimePolicyError(f"blind health counter {key} must be numeric or null")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0:
                raise RuntimePolicyError(
                    f"blind health counter {key} must be finite and non-negative"
                )
    if record.get("http_status") is not None and not 100 <= int(record["http_status"]) <= 599:
        raise RuntimePolicyError("blind health http_status must be 100..599")
    if (record.get("session_id") is None) != (record.get("host_boot_id") is None):
        raise RuntimePolicyError(
            "blind health session_id and host_boot_id must appear together"
        )
    if record.get("session_id") is not None:
        _validate_session_id(str(record["session_id"]))
        _validate_host_boot_id(str(record["host_boot_id"]))


def summarize_blind_health(path: str | Path) -> dict[str, Any]:
    """Aggregate a ledger without exposing individual evidence or response bodies."""

    counts: dict[str, int] = {}
    http_status_counts: dict[str, int] = {}
    retry_delay_seconds = 0.0
    max_latency_seconds = 0.0
    records = 0
    with Path(path).open("r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            lines = handle.read().splitlines()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        loaded = json.loads(line)
        if not isinstance(loaded, Mapping):
            raise RuntimePolicyError(f"blind health line {line_number} is not an object")
        validate_blind_health_record(loaded)
        records += 1
        outcome = str(loaded["outcome"])
        counts[outcome] = counts.get(outcome, 0) + 1
        if loaded.get("http_status") is not None:
            status = str(int(loaded["http_status"]))
            http_status_counts[status] = http_status_counts.get(status, 0) + 1
        retry_delay_seconds += float(loaded.get("retry_delay_seconds") or 0.0)
        max_latency_seconds = max(
            max_latency_seconds, float(loaded.get("latency_seconds") or 0.0)
        )
    return {
        "schema_version": "agentdojo_openrouter_blind_health_summary/v1",
        "record_count": records,
        "outcome_counts": dict(sorted(counts.items())),
        "http_status_counts": dict(sorted(http_status_counts.items())),
        "retry_delay_seconds": round(retry_delay_seconds, 6),
        "max_latency_seconds": round(max_latency_seconds, 6),
    }


_EXECUTION_RUNTIME_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "src/evidence_system/adapters/agentdojo_runtime_control.py",
    "src/evidence_system/adapters/agentdojo_disposable_controller.py",
    "src/evidence_system/adapters/agentdojo_worker.py",
    "src/evidence_system/adapters/agentdojo.py",
    "src/evidence_system/adapters/agentdojo_formal_postprocessor.py",
    "src/evidence_system/adapters/agentdojo_formal_supervisor.py",
    "src/evidence_system/adapters/agentdojo_remote_inventory.py",
    "src/evidence_system/adapters/runtime.py",
    "src/evidence_system/adapters/base.py",
    "src/evidence_system/orchestrator/jobs.py",
    "src/evidence_system/orchestrator/agentdojo_locked_runner.py",
    "src/evidence_system/contracts/agentdojo_full_execution.py",
    "src/evidence_system/contracts/agentdojo_full_evidence.py",
    "src/evidence_system/contracts/agentdojo_execution_namespace.py",
    "src/evidence_system/contracts/agentdojo_full_experiment.py",
    "src/evidence_system/contracts/agentdojo_execution_budget.py",
    "src/evidence_system/contracts/agentdojo_rate_lifecycle.py",
    "src/evidence_system/contracts/case_packets.py",
    "src/evidence_system/contracts/appworld_checklist_semantics.py",
    "src/evidence_system/contracts/appworld_stronger_gaps.py",
    "src/evidence_system/contracts/common.py",
    "src/evidence_system/contracts/draft.py",
    "src/evidence_system/core/hashing.py",
    "src/evidence_system/core/paths.py",
    "src/evidence_system/core/errors.py",
    "src/evidence_system/core/dotenv.py",
    "src/evidence_system/core/schemas.py",
    "src/evidence_system/llm/openrouter_client.py",
    "src/evidence_system/llm/cost.py",
    "src/evidence_system/llm/logging.py",
    "src/evidence_system/cli/agentdojo_runtime_health.py",
    "src/evidence_system/cli/agentdojo_runtime_preflight.py",
    "src/evidence_system/cli/agentdojo_disposable_controller.py",
    "src/evidence_system/cli/agentdojo_namespace_control.py",
    "src/evidence_system/cli/agentdojo_vps_provision.py",
    "src/evidence_system/cli/build_agentdojo_execution_budget.py",
    "src/evidence_system/cli/lock_agentdojo_full_execution.py",
    "src/evidence_system/cli/run_agentdojo_locked_evidence.py",
    "src/evidence_system/cli/run_full.py",
    "src/evidence_system/cli/finalize_agentdojo_full_evidence.py",
    "src/evidence_system/cli/promote_agentdojo_full_evidence.py",
    "src/evidence_system/cli/retrieve_agentdojo_full_evidence.py",
    "schemas/agentdojo_full_execution_lock.schema.json",
    "schemas/agentdojo_full_evidence_acceptance_index.schema.json",
    "schemas/agentdojo_full_evidence_promotion_receipt.schema.json",
    "schemas/agentdojo_full_prescore_join_lock.schema.json",
    "schemas/agentdojo_sealed_evidence_retrieval_receipt.schema.json",
    "schemas/agentdojo_remote_output_precondition_receipt.schema.json",
    "schemas/agentdojo_formal_execution_namespace_init_receipt.schema.json",
    "schemas/agentdojo_final_runtime_deployment_receipt.schema.json",
    "schemas/agentdojo_formal_stage_health_receipt.schema.json",
    "schemas/agentdojo_openrouter_rate_measurement_receipt.schema.json",
    "schemas/agentdojo_openrouter_policy_finalization_receipt.schema.json",
    "schemas/agentdojo_openrouter_disposable_round_plan.schema.json",
    "schemas/agentdojo_vps_provision_receipt.schema.json",
    "schemas/agentdojo_execution_budget_plan.schema.json",
    "schemas/agentdojo_openrouter_credential_probe_receipt.schema.json",
    "schemas/agentdojo_openrouter_disposable_ramp_receipt.schema.json",
    "schemas/agentdojo_openrouter_ramp_stage_receipt.schema.json",
    "schemas/experiment_manifest.schema.json",
    "schemas/agent_config.schema.json",
    "schemas/job.schema.json",
    "schemas/raw_run.schema.json",
    "schemas/artifact_manifest.schema.json",
    "schemas/infra_config.schema.json",
)


def execution_runtime_snapshot() -> dict[str, Any]:
    """One shared code/schema identity for execution locks and ramp receipts."""

    files: dict[str, str] = {}
    for relative in _EXECUTION_RUNTIME_PATHS:
        path = resolve_repo_path(relative)
        if path.is_symlink() or not path.is_file():
            raise RuntimePolicyError(f"execution-runtime file is missing: {relative}")
        files[relative] = sha256_file(path)
    return {
        "schema_version": "agentdojo_execution_runtime_snapshot/v1",
        "files": files,
        "aggregate_sha256": sha256_object(files),
    }


def runtime_control_code_snapshot() -> dict[str, Any]:
    """Compatibility alias; all callers receive the shared execution snapshot."""

    return execution_runtime_snapshot()


def _assert_directory_chain_no_symlinks(
    directory: str | Path, *, anchor: str | Path | None = None
) -> None:
    """Validate an already-created directory chain without resolving links.

    Shared monitor files are security boundaries.  A lexical containment check
    plus lstat on the anchor and every descendant prevents an attacker from
    redirecting a supposedly blind path through an in-tree symlink.
    """

    target = Path(directory).absolute()
    if anchor is None:
        chain = [target]
    else:
        root = Path(anchor).absolute()
        try:
            relative = target.relative_to(root)
        except ValueError as exc:
            raise RuntimePolicyError(
                "shared ledger directory is outside its locked root"
            ) from exc
        chain = [root]
        current = root
        for part in relative.parts:
            current = current / part
            chain.append(current)
    for component in chain:
        try:
            component_stat = os.lstat(component)
        except FileNotFoundError as exc:
            raise RuntimePolicyError(
                "ledger directory chain must be pre-provisioned"
            ) from exc
        if stat.S_ISLNK(component_stat.st_mode) or not stat.S_ISDIR(
            component_stat.st_mode
        ):
            raise RuntimePolicyError(
                "ledger directory chain contains a symlink or non-directory"
            )


def _regular_nonsymlink_file(path: str | Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = resolve_repo_path(candidate)
    if candidate.is_symlink() or not candidate.is_file():
        raise RuntimePolicyError(f"{label} must be a regular, non-symlink file")
    return candidate.resolve()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _locked_file_ref(path: Path) -> dict[str, str]:
    return {"path": _portable_path(path), "sha256": sha256_file(path)}


def _parse_aware_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimePolicyError(f"{field} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise RuntimePolicyError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _row_timestamp(row: Mapping[str, Any]) -> datetime:
    return _parse_aware_timestamp(str(row.get("timestamp") or ""), "health timestamp")


def _strict_nonnegative_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RuntimePolicyError(f"{field} must be an integer >= {minimum}")
    return value


def _finite_percentage(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimePolicyError(f"{field} must be numeric")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 100.0:
        raise RuntimePolicyError(f"{field} must be finite and between 0 and 100")
    return number


def _read_blind_health_records(
    path: Path, *, expected_policy_sha256: str
) -> list[dict[str, Any]]:
    expected = _validate_digest(expected_policy_sha256, "expected_policy_sha256")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            lines = handle.read().splitlines()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimePolicyError(
                f"blind health line {line_number} is invalid JSON"
            ) from exc
        if not isinstance(row, dict):
            raise RuntimePolicyError(f"blind health line {line_number} is not an object")
        validate_blind_health_record(row)
        if str(row.get("policy_sha256") or "").removeprefix("sha256:") != expected:
            raise RuntimePolicyError(
                f"blind health line {line_number} belongs to a different runtime policy"
            )
        records.append(row)
    if not records:
        raise RuntimePolicyError("blind health ledger is empty")
    return records


def _read_resource_records(path: Path, *, expected_stage: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            lines = handle.read().splitlines()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimePolicyError(
                f"resource ledger line {line_number} is invalid JSON"
            ) from exc
        if not isinstance(row, dict):
            raise RuntimePolicyError(f"resource line {line_number} is not an object")
        validate_ramp_resource_sample(row)
        if row.get("budget_scope") != "disposable_preflight":
            raise RuntimePolicyError(
                "disposable resource row uses a non-preflight budget scope"
            )
        if int(row["worker_concurrency"]) != expected_stage:
            raise RuntimePolicyError("resource sample belongs to a different ramp stage")
        records.append(row)
    for field in (
        "session_id",
        "host_boot_id",
        "runtime_database_path_sha256",
        "stage_binding_sha256",
        "worker_process_binding_sha256",
        "expected_worker_uid",
        "minimum_worker_starttime_ticks",
    ):
        if len({row[field] for row in records}) > 1:
            raise RuntimePolicyError(
                f"resource ledger crosses a different {field}"
            )
    return records


def _observed_rate_maxima(
    rows: Sequence[Mapping[str, Any]], *, window_seconds: float
) -> tuple[int, int, int]:
    ordered = sorted(
        (
            (
                _row_timestamp(row).timestamp(),
                int(row.get("reserved_tokens") or 0),
                int(row.get("actual_total_tokens") or 0),
            )
            for row in rows
        ),
        key=lambda item: item[0],
    )
    active: deque[tuple[float, int, int]] = deque()
    active_reservation_units = 0
    active_provider_tokens = 0
    max_requests = 0
    max_reservation_units = 0
    max_provider_tokens = 0
    for timestamp, reservation_units, provider_tokens in ordered:
        threshold = timestamp - window_seconds
        while active and active[0][0] <= threshold:
            _, expired_reservation_units, expired_provider_tokens = active.popleft()
            active_reservation_units -= expired_reservation_units
            active_provider_tokens -= expired_provider_tokens
        active.append((timestamp, reservation_units, provider_tokens))
        active_reservation_units += reservation_units
        active_provider_tokens += provider_tokens
        max_requests = max(max_requests, len(active))
        max_reservation_units = max(
            max_reservation_units, active_reservation_units
        )
        max_provider_tokens = max(max_provider_tokens, active_provider_tokens)
    return max_requests, max_reservation_units, max_provider_tokens


class SharedPreflightBudgetLedger:
    """Crash-conservative cost cap shared by both disposable rounds.

    The measurement and validation rounds use independent rate-limit databases,
    so neither database can enforce their combined cap.  This small SQLite
    ledger reserves every request across both rounds, applies a 70 USD cap to
    each phase and a 120 USD aggregate cap, and charges the full reservation
    after a lease timeout or host reboot.
    """

    PHASES = ("exploratory_measurement", "finalized_validation")

    def __init__(
        self,
        path: str | Path,
        *,
        policy_sha256: str,
        lease_timeout_seconds: float,
        clock: Callable[[], float] | None = None,
        host_boot_id: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.policy_sha256 = _validate_digest(
            policy_sha256, "shared preflight budget policy_sha256"
        )
        self.lease_timeout_seconds = float(lease_timeout_seconds)
        if (
            not math.isfinite(self.lease_timeout_seconds)
            or self.lease_timeout_seconds < 1.0
        ):
            raise RuntimePolicyError(
                "shared preflight budget lease timeout is invalid"
            )
        self.clock = time.monotonic if clock is None else clock
        self.host_boot_id = (
            _default_limiter_host_boot_id()
            if host_boot_id is None
            else _validate_host_boot_id(host_boot_id)
        )
        self._initialize()

    def acquire(
        self, *, phase: str, reserved_cost_usd: float
    ) -> "SharedPreflightBudgetLease":
        normalized_phase = self._phase(phase)
        reservation = float(reserved_cost_usd)
        if not math.isfinite(reservation) or reservation <= 0:
            raise RuntimePolicyError(
                "shared preflight budget reservation must be positive and finite"
            )
        now = self.clock()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._recover_unknown(db, now=now, recover_all=False)
            state = db.execute(
                "SELECT hard_blocked FROM shared_state WHERE singleton_id = 1"
            ).fetchone()
            if state is None or int(state[0]) != 0:
                db.rollback()
                raise RuntimeBudgetExceeded(
                    "shared two-round preflight budget is hard-blocked"
                )
            phase_total = float(
                db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0.0) FROM shared_cost "
                    "WHERE phase = ?",
                    (normalized_phase,),
                ).fetchone()[0]
            ) + float(
                db.execute(
                    "SELECT COALESCE(SUM(reserved_cost_usd), 0.0) "
                    "FROM shared_leases WHERE phase = ?",
                    (normalized_phase,),
                ).fetchone()[0]
            )
            aggregate_total = float(
                db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0.0) FROM shared_cost"
                ).fetchone()[0]
            ) + float(
                db.execute(
                    "SELECT COALESCE(SUM(reserved_cost_usd), 0.0) "
                    "FROM shared_leases"
                ).fetchone()[0]
            )
            if (
                phase_total + reservation
                > self._phase_cap(normalized_phase) + 1e-12
                or aggregate_total + reservation
                > REQUIRED_TWO_ROUND_PREFLIGHT_COST_CAP_USD + 1e-12
            ):
                db.rollback()
                raise RuntimeBudgetExceeded(
                    "shared two-round preflight phase/aggregate cost cap cannot "
                    "admit the next reserved request"
                )
            lease_id = uuid.uuid4().hex
            event_id = uuid.uuid4().hex
            db.execute(
                "INSERT INTO shared_leases(lease_id, event_id, phase, "
                "reserved_cost_usd, expires_at, host_boot_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    lease_id,
                    event_id,
                    normalized_phase,
                    reservation,
                    now + self.lease_timeout_seconds,
                    self.host_boot_id,
                ),
            )
            db.commit()
        return SharedPreflightBudgetLease(
            ledger=self,
            lease_id=lease_id,
            event_id=event_id,
            phase=normalized_phase,
            reserved_cost_usd=reservation,
        )

    def refresh(self, *, lease_id: str, event_id: str) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            updated = db.execute(
                "UPDATE shared_leases SET expires_at = ? "
                "WHERE lease_id = ? AND event_id = ? AND host_boot_id = ?",
                (
                    self.clock() + self.lease_timeout_seconds,
                    lease_id,
                    event_id,
                    self.host_boot_id,
                ),
            )
            if updated.rowcount != 1:
                db.rollback()
                raise RuntimeBudgetExceeded(
                    "shared preflight budget lease expired before provider admission"
                )
            db.commit()

    def cancel(self, *, lease_id: str, event_id: str) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            deleted = db.execute(
                "DELETE FROM shared_leases WHERE lease_id = ? AND event_id = ?",
                (lease_id, event_id),
            )
            if deleted.rowcount != 1:
                db.rollback()
                raise RuntimePolicyError(
                    "shared preflight admission changed before cancellation"
                )
            db.commit()

    def release(
        self,
        *,
        lease_id: str,
        event_id: str,
        phase: str,
        reserved_cost_usd: float,
        actual_cost_usd: float | None,
    ) -> SharedPreflightBudgetSnapshot:
        normalized_phase = self._phase(phase)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT phase, reserved_cost_usd FROM shared_leases "
                "WHERE lease_id = ? AND event_id = ?",
                (lease_id, event_id),
            ).fetchone()
            if row is None:
                db.rollback()
                raise RuntimePolicyError("shared preflight budget lease is missing")
            locked_reservation = float(row[1])
            if (
                str(row[0]) != normalized_phase
                or abs(locked_reservation - float(reserved_cost_usd)) > 1e-12
            ):
                db.rollback()
                raise RuntimePolicyError(
                    "shared preflight budget lease binding differs"
                )
            cost = (
                locked_reservation
                if actual_cost_usd is None
                else float(actual_cost_usd)
            )
            if not math.isfinite(cost) or cost < 0:
                db.rollback()
                raise RuntimePolicyError(
                    "shared preflight actual cost must be finite and non-negative"
                )
            violated = cost > locked_reservation + 1e-12
            db.execute(
                "DELETE FROM shared_leases WHERE lease_id = ? AND event_id = ?",
                (lease_id, event_id),
            )
            db.execute(
                "INSERT INTO shared_cost(event_id, phase, cost_usd, charge_kind, "
                "charged_at) VALUES (?, ?, ?, ?, ?)",
                (
                    event_id,
                    normalized_phase,
                    cost,
                    (
                        "unknown_full_reservation"
                        if actual_cost_usd is None
                        else "provider_reported_actual"
                    ),
                    self.clock(),
                ),
            )
            if violated:
                db.execute(
                    "UPDATE shared_state SET hard_blocked = 1, "
                    "reservation_violation_count = reservation_violation_count + 1 "
                    "WHERE singleton_id = 1"
                )
            db.commit()
        snapshot = self.snapshot()
        if violated:
            raise RuntimeBudgetExceeded(
                "provider cost exceeded the shared preflight reservation"
            )
        return snapshot

    def snapshot(self) -> SharedPreflightBudgetSnapshot:
        now = self.clock()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._recover_unknown(db, now=now, recover_all=False)
            costs = {
                str(phase): float(cost)
                for phase, cost in db.execute(
                    "SELECT phase, COALESCE(SUM(cost_usd), 0.0) "
                    "FROM shared_cost GROUP BY phase"
                ).fetchall()
            }
            pending = float(
                db.execute(
                    "SELECT COALESCE(SUM(reserved_cost_usd), 0.0) "
                    "FROM shared_leases"
                ).fetchone()[0]
            )
            active = int(
                db.execute("SELECT COUNT(*) FROM shared_leases").fetchone()[0]
            )
            unknown = int(
                db.execute(
                    "SELECT COUNT(*) FROM shared_cost WHERE charge_kind IN "
                    "('expired_unknown_full_reservation', "
                    "'boot_recovered_unknown_full_reservation')"
                ).fetchone()[0]
            )
            hard_blocked = bool(
                int(
                    db.execute(
                        "SELECT hard_blocked FROM shared_state "
                        "WHERE singleton_id = 1"
                    ).fetchone()[0]
                )
            )
            db.commit()
        measurement = costs.get("exploratory_measurement", 0.0)
        validation = costs.get("finalized_validation", 0.0)
        return SharedPreflightBudgetSnapshot(
            host_boot_id=self.host_boot_id,
            measurement_cost_usd=measurement,
            validation_cost_usd=validation,
            aggregate_cost_usd=measurement + validation,
            pending_reserved_cost_usd=pending,
            active_leases=active,
            expired_or_boot_recovered_unknown_cost_count=unknown,
            hard_blocked=hard_blocked,
        )

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "CREATE TABLE IF NOT EXISTS shared_metadata "
                "(singleton_id INTEGER PRIMARY KEY CHECK(singleton_id = 1), "
                "policy_sha256 TEXT NOT NULL, host_boot_id TEXT NOT NULL, "
                "measurement_cap_usd REAL NOT NULL, validation_cap_usd REAL NOT NULL, "
                "aggregate_cap_usd REAL NOT NULL, boot_epoch INTEGER NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS shared_leases "
                "(lease_id TEXT PRIMARY KEY, event_id TEXT NOT NULL UNIQUE, "
                "phase TEXT NOT NULL, reserved_cost_usd REAL NOT NULL, "
                "expires_at REAL NOT NULL, host_boot_id TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS shared_cost "
                "(event_id TEXT PRIMARY KEY, phase TEXT NOT NULL, cost_usd REAL NOT NULL, "
                "charge_kind TEXT NOT NULL, charged_at REAL NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS shared_state "
                "(singleton_id INTEGER PRIMARY KEY CHECK(singleton_id = 1), "
                "hard_blocked INTEGER NOT NULL CHECK(hard_blocked IN (0, 1)), "
                "reservation_violation_count INTEGER NOT NULL)"
            )
            db.execute(
                "INSERT OR IGNORE INTO shared_state(singleton_id, hard_blocked, "
                "reservation_violation_count) VALUES (1, 0, 0)"
            )
            metadata = db.execute(
                "SELECT policy_sha256, host_boot_id, measurement_cap_usd, "
                "validation_cap_usd, aggregate_cap_usd, boot_epoch "
                "FROM shared_metadata WHERE singleton_id = 1"
            ).fetchone()
            expected_caps = (
                REQUIRED_MEASUREMENT_PHASE_COST_CAP_USD,
                REQUIRED_FINAL_VALIDATION_BUDGET_USD,
                REQUIRED_TWO_ROUND_PREFLIGHT_COST_CAP_USD,
            )
            if metadata is None:
                db.execute(
                    "INSERT INTO shared_metadata(singleton_id, policy_sha256, "
                    "host_boot_id, measurement_cap_usd, validation_cap_usd, "
                    "aggregate_cap_usd, boot_epoch) VALUES (1, ?, ?, ?, ?, ?, 0)",
                    (self.policy_sha256, self.host_boot_id, *expected_caps),
                )
            else:
                if str(metadata[0]) != self.policy_sha256 or tuple(
                    float(value) for value in metadata[2:5]
                ) != expected_caps:
                    db.rollback()
                    raise RuntimePolicyError(
                        "shared preflight budget metadata policy/caps differ"
                    )
                if str(metadata[1]) != self.host_boot_id:
                    self._recover_unknown(db, now=self.clock(), recover_all=True)
                    db.execute(
                        "UPDATE shared_metadata SET host_boot_id = ?, "
                        "boot_epoch = boot_epoch + 1 WHERE singleton_id = 1",
                        (self.host_boot_id,),
                    )
            db.commit()

    def _recover_unknown(
        self, db: sqlite3.Connection, *, now: float, recover_all: bool
    ) -> int:
        rows = db.execute(
            "SELECT lease_id, event_id, phase, reserved_cost_usd FROM shared_leases "
            + ("ORDER BY lease_id" if recover_all else "WHERE expires_at <= ? ORDER BY lease_id"),
            () if recover_all else (now,),
        ).fetchall()
        charge_kind = (
            "boot_recovered_unknown_full_reservation"
            if recover_all
            else "expired_unknown_full_reservation"
        )
        for lease_id, event_id, phase, reservation in rows:
            self._phase(str(phase))
            cost = float(reservation)
            if not math.isfinite(cost) or cost <= 0:
                raise RuntimePolicyError(
                    "shared preflight recovered reservation is invalid"
                )
            db.execute(
                "INSERT INTO shared_cost(event_id, phase, cost_usd, charge_kind, "
                "charged_at) VALUES (?, ?, ?, ?, ?)",
                (str(event_id), str(phase), cost, charge_kind, now),
            )
            deleted = db.execute(
                "DELETE FROM shared_leases WHERE lease_id = ? AND event_id = ?",
                (str(lease_id), str(event_id)),
            )
            if deleted.rowcount != 1:
                raise RuntimePolicyError(
                    "shared preflight recovered lease changed during charging"
                )
        return len(rows)

    @staticmethod
    def _phase(value: str) -> str:
        phase = str(value)
        if phase not in SharedPreflightBudgetLedger.PHASES:
            raise RuntimePolicyError("shared preflight budget phase is invalid")
        return phase

    @staticmethod
    def _phase_cap(phase: str) -> float:
        return (
            REQUIRED_MEASUREMENT_PHASE_COST_CAP_USD
            if phase == "exploratory_measurement"
            else REQUIRED_FINAL_VALIDATION_BUDGET_USD
        )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=30000")
            yield db
        finally:
            db.close()


class SharedPreflightBudgetLease:
    def __init__(
        self,
        *,
        ledger: SharedPreflightBudgetLedger,
        lease_id: str,
        event_id: str,
        phase: str,
        reserved_cost_usd: float,
    ) -> None:
        self.ledger = ledger
        self.lease_id = lease_id
        self.event_id = event_id
        self.phase = phase
        self.reserved_cost_usd = reserved_cost_usd
        self._closed = False

    def refresh(self) -> None:
        if self._closed:
            raise RuntimePolicyError("shared preflight budget lease is closed")
        self.ledger.refresh(lease_id=self.lease_id, event_id=self.event_id)

    def cancel(self) -> None:
        if self._closed:
            raise RuntimePolicyError("shared preflight budget lease is closed")
        self._closed = True
        self.ledger.cancel(lease_id=self.lease_id, event_id=self.event_id)

    def release(
        self, *, actual_cost_usd: float | None
    ) -> SharedPreflightBudgetSnapshot:
        if self._closed:
            raise RuntimePolicyError("shared preflight budget lease is closed")
        self._closed = True
        return self.ledger.release(
            lease_id=self.lease_id,
            event_id=self.event_id,
            phase=self.phase,
            reserved_cost_usd=self.reserved_cost_usd,
            actual_cost_usd=actual_cost_usd,
        )


def _formal_budget_cost_cap_action(
    *, policy: RuntimePolicy, state_dir: Path, budget_scope: str
) -> tuple[str, str | None]:
    """Load an explicit, blind operator receipt that makes the formal cap record-only.

    The immutable runtime policy and accumulated cost ledger remain unchanged.  The
    override is deliberately narrow: it can only stop the *formal execution* run
    cap from blocking new admissions.  Per-request cost reservations, RPM/TPM,
    concurrency, lease expiry, and reservation-violation hard blocks still apply.
    """

    if budget_scope != "formal_execution":
        return policy.budget.cost_cap_action, None
    path = state_dir / FORMAL_BUDGET_ADMISSION_OVERRIDE_RELATIVE_PATH
    try:
        info = path.lstat()
    except FileNotFoundError:
        return policy.budget.cost_cap_action, None
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_size <= 0
        or info.st_size > 16_384
        or stat.S_IMODE(info.st_mode) & 0o022
    ):
        raise RuntimePolicyError(
            "formal budget admission override is linked, unsafe, or oversized"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimePolicyError(
            "formal budget admission override is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(payload, Mapping):
        raise RuntimePolicyError("formal budget admission override is not an object")
    expected_keys = {
        "schema_version",
        "status",
        "created_at",
        "runtime_policy_semantic_sha256",
        "budget_scope",
        "original_cost_cap_action",
        "override_cost_cap_action",
        "original_maximum_run_cost_usd",
        "preserved_maximum_single_request_cost_usd",
        "reason_code",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
    if set(payload) != expected_keys:
        raise RuntimePolicyError("formal budget admission override fields differ")
    if (
        payload.get("schema_version")
        != FORMAL_BUDGET_ADMISSION_OVERRIDE_SCHEMA_VERSION
        or payload.get("status") != "authorized"
        or payload.get("budget_scope") != "formal_execution"
        or payload.get("original_cost_cap_action")
        != policy.budget.cost_cap_action
        or payload.get("override_cost_cap_action") != "record_only"
        or payload.get("reason_code")
        != "operator_removed_local_formal_run_cost_gate"
        or payload.get("blind_only") is not True
        or payload.get(
            "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
        )
        is not False
    ):
        raise RuntimePolicyError("formal budget admission override binding differs")
    if _validate_digest(
        str(payload.get("runtime_policy_semantic_sha256") or ""),
        "formal budget admission override runtime policy",
    ) != policy.semantic_sha256:
        raise RuntimePolicyError("formal budget admission override policy differs")
    for field, expected in (
        ("original_maximum_run_cost_usd", policy.budget.maximum_run_cost_usd),
        (
            "preserved_maximum_single_request_cost_usd",
            policy.budget.maximum_single_request_cost_usd,
        ),
    ):
        value = payload.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isclose(float(value), float(expected), abs_tol=1e-12)
        ):
            raise RuntimePolicyError(
                f"formal budget admission override {field} differs"
            )
    created_at = payload.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        raise RuntimePolicyError("formal budget admission override timestamp is invalid")
    try:
        parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimePolicyError(
            "formal budget admission override timestamp is invalid"
        ) from exc
    if parsed_created_at.tzinfo is None:
        raise RuntimePolicyError("formal budget admission override timestamp is naive")
    return "record_only", sha256_file(path)


class GlobalRateLimiter:
    """SQLite-backed concurrency/RPM/TPM/cost guard shared by worker processes."""

    def __init__(
        self,
        policy: RuntimePolicy,
        *,
        state_dir: str | Path,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        budget_scope: str = "formal_execution",
        host_boot_id: str | None = None,
        auth_lifecycle_lock_path: str | Path | None = None,
    ) -> None:
        self.policy = policy
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if budget_scope not in {"formal_execution", "disposable_preflight"}:
            raise RuntimePolicyError("limiter budget_scope is invalid")
        self.budget_scope = budget_scope
        (
            self.local_cost_cap_action,
            self.formal_budget_admission_override_sha256,
        ) = _formal_budget_cost_cap_action(
            policy=policy,
            state_dir=self.state_dir,
            budget_scope=budget_scope,
        )
        self.maximum_scope_cost_usd = (
            policy.budget.maximum_run_cost_usd
            if budget_scope == "formal_execution"
            else policy.budget.maximum_preflight_cost_usd
        )
        self.database_path = self.state_dir / (
            f"openrouter-{budget_scope}-{policy.semantic_sha256[:16]}.sqlite3"
        )
        self.auth_lifecycle_lock = OpenRouterAuthLifecycleLock(
            self.state_dir / "openrouter_auth.lock"
            if auth_lifecycle_lock_path is None
            else auth_lifecycle_lock_path
        )
        self.auth_lifecycle_lock_path = self.auth_lifecycle_lock.path
        self.clock_basis = str(LIMITER_CLOCK_DEFINITION["basis"])
        self.clock = time.monotonic if clock is None else clock
        self.sleep = sleep
        self.host_boot_id = (
            _default_limiter_host_boot_id()
            if host_boot_id is None
            else _validate_host_boot_id(host_boot_id)
        )
        self._initialize()

    def acquire(
        self,
        *,
        reserved_tokens: int,
        model_id: str,
        reserved_cost_usd: float | None = None,
        currentness_check: Callable[[], None] | None = None,
    ) -> "RateLimitLease":
        if reserved_tokens <= 0:
            raise RuntimePolicyError("reserved_tokens must be positive")
        if reserved_tokens > self.policy.tokens_per_minute:
            raise RuntimePolicyError("reserved_tokens exceeds tokens_per_minute")
        normalized_model_id = model_id.removeprefix("openrouter/")
        if normalized_model_id not in REQUIRED_MODELS:
            raise RuntimePolicyError("model_id is outside the frozen AgentDojo model set")
        model_limits = (
            self.policy.per_model_safe_limits or {}
        ).get(normalized_model_id) or {
            "requests_per_minute": self.policy.requests_per_minute,
            "tokens_per_minute": self.policy.tokens_per_minute,
            "concurrent_requests": self.policy.max_concurrent_requests,
        }
        if reserved_tokens > int(model_limits["tokens_per_minute"]):
            raise RuntimePolicyError("reserved_tokens exceeds the current model TPM limit")
        reserved_cost = (
            self.policy.budget.maximum_single_request_cost_usd
            if reserved_cost_usd is None
            else float(reserved_cost_usd)
        )
        if (
            not math.isfinite(reserved_cost)
            or reserved_cost <= 0
            or reserved_cost > self.policy.budget.maximum_single_request_cost_usd
        ):
            raise RuntimePolicyError(
                "reserved_cost_usd must be positive, finite, and no greater than the locked single-request ceiling"
            )
        wait_started = self.clock()
        while True:
            if currentness_check is not None:
                currentness_check()
            # Do not hold the shared barrier while merely sleeping for rate
            # capacity.  Once held, however, it spans admission, the provider
            # request, and durable release through the returned lease.
            auth_handle = self.auth_lifecycle_lock.acquire(exclusive=False)
            try:
                if currentness_check is not None:
                    currentness_check()
                acquired = self._try_acquire(
                    reserved_tokens=reserved_tokens,
                    reserved_cost_usd=reserved_cost,
                    model_id=normalized_model_id,
                )
            except BaseException:
                auth_handle.close()
                raise
            if acquired is not None:
                lease_id, event_id, snapshot = acquired
                lease = RateLimitLease(
                    limiter=self,
                    lease_id=lease_id,
                    event_id=event_id,
                    reserved_tokens=reserved_tokens,
                    reserved_cost_usd=reserved_cost,
                    model_id=normalized_model_id,
                    waited_seconds=max(0.0, self.clock() - wait_started),
                    snapshot=snapshot,
                    auth_lifecycle_handle=auth_handle,
                )
                if currentness_check is not None:
                    try:
                        currentness_check()
                    except BaseException:
                        lease.cancel()
                        raise
                return lease
            auth_handle.close()
            self.sleep(self.policy.acquire_poll_seconds)

    def cancel_admission(
        self,
        *,
        lease_id: str,
        event_id: str,
        model_id: str,
    ) -> None:
        """Atomically erase an authorized-but-not-sent admission.

        Cancellation is intentionally distinct from release: it creates no
        RPM/TPM window entry, no cost charge, and no provider-usage fiction.
        """

        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT event_id, model_id FROM leases WHERE lease_id = ?",
                (lease_id,),
            ).fetchone()
            if row is None or str(row[0]) != event_id or str(row[1]) != model_id:
                db.rollback()
                raise RuntimePolicyError(
                    "rate-limit admission changed before atomic cancellation"
                )
            if db.execute(
                "SELECT 1 FROM run_cost WHERE event_id = ?", (event_id,)
            ).fetchone() is not None:
                db.rollback()
                raise RuntimePolicyError("sent/charged request admission cannot be cancelled")
            if db.execute(
                "DELETE FROM leases WHERE lease_id = ? AND event_id = ?",
                (lease_id, event_id),
            ).rowcount != 1 or db.execute(
                "DELETE FROM request_window WHERE event_id = ?", (event_id,)
            ).rowcount != 1:
                db.rollback()
                raise RuntimePolicyError("atomic admission cancellation was incomplete")
            db.commit()

    def _try_acquire(
        self, *, reserved_tokens: int, reserved_cost_usd: float, model_id: str
    ) -> tuple[str, str, LimiterSnapshot] | None:
        now = self.clock()
        threshold = now - self.policy.rate_window_seconds
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._expire_leases(db, now=now)
            run_state = db.execute(
                "SELECT hard_blocked, reservation_violation_count FROM run_state "
                "WHERE singleton_id = 1"
            ).fetchone()
            if run_state is None:
                db.rollback()
                raise RuntimePolicyError("runtime budget state is missing")
            if int(run_state[0]) != 0 or int(run_state[1]) != 0:
                db.rollback()
                raise RuntimeBudgetExceeded(
                    "locked OpenRouter runtime is hard-blocked by a prior cost-reservation violation"
                )
            db.execute(
                "DELETE FROM request_window WHERE started_at <= ? "
                "AND event_id NOT IN (SELECT event_id FROM leases)",
                (threshold,),
            )
            active = int(db.execute("SELECT COUNT(*) FROM leases").fetchone()[0])
            if self.budget_scope == "formal_execution" and active:
                active_models = {
                    str(row[0])
                    for row in db.execute(
                        "SELECT DISTINCT model_id FROM leases"
                    ).fetchall()
                }
                if active_models != {model_id}:
                    db.rollback()
                    raise RuntimePolicyError(
                        "formal limiter forbids cross-model concurrent leases"
                    )
            model_active = int(
                db.execute(
                    "SELECT COUNT(*) FROM leases WHERE model_id = ?", (model_id,)
                ).fetchone()[0]
            )
            pending_reserved_cost = float(
                db.execute(
                    "SELECT COALESCE(SUM(reserved_cost_usd), 0.0) FROM leases"
                ).fetchone()[0]
            )
            row = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens), 0), COALESCE(SUM(cost_usd), 0.0) "
                "FROM request_window"
            ).fetchone()
            requests_in_window = int(row[0])
            tokens_in_window = int(row[1])
            model_row = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM request_window "
                "WHERE model_id = ?",
                (model_id,),
            ).fetchone()
            model_requests_in_window = int(model_row[0])
            model_tokens_in_window = int(model_row[1])
            cumulative_cost = float(
                db.execute("SELECT COALESCE(SUM(cost_usd), 0.0) FROM run_cost").fetchone()[0]
            )
            hard_cost_block = (
                self.local_cost_cap_action == "block_new_requests"
                and cumulative_cost + pending_reserved_cost + reserved_cost_usd
                > self.maximum_scope_cost_usd
            )
            if hard_cost_block:
                db.rollback()
                raise RuntimeBudgetExceeded(
                    f"locked OpenRouter {self.budget_scope} cost cap cannot admit the next reserved request"
                )
            model_limits = (self.policy.per_model_safe_limits or {}).get(model_id) or {
                "requests_per_minute": self.policy.requests_per_minute,
                "tokens_per_minute": self.policy.tokens_per_minute,
                "concurrent_requests": self.policy.max_concurrent_requests,
            }
            if (
                active >= self.policy.max_concurrent_requests
                or requests_in_window >= self.policy.requests_per_minute
                or tokens_in_window + reserved_tokens > self.policy.tokens_per_minute
                or model_active >= int(model_limits["concurrent_requests"])
                or model_requests_in_window >= int(model_limits["requests_per_minute"])
                or model_tokens_in_window + reserved_tokens
                > int(model_limits["tokens_per_minute"])
            ):
                db.commit()
                return None
            lease_id = uuid.uuid4().hex
            event_id = uuid.uuid4().hex
            db.execute(
                "INSERT INTO leases(lease_id, event_id, expires_at, reserved_cost_usd, model_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    lease_id,
                    event_id,
                    now + self.policy.lease_timeout_seconds,
                    reserved_cost_usd,
                    model_id,
                ),
            )
            db.execute(
                "INSERT INTO request_window(event_id, started_at, tokens, cost_usd, model_id) "
                "VALUES (?, ?, ?, 0.0, ?)",
                (event_id, now, reserved_tokens, model_id),
            )
            db.commit()
        return (
            lease_id,
            event_id,
            LimiterSnapshot(
                active_requests=active + 1,
                requests_in_window=requests_in_window + 1,
                tokens_in_window=tokens_in_window + reserved_tokens,
                model_active_requests=model_active + 1,
                model_requests_in_window=model_requests_in_window + 1,
                model_tokens_in_window=model_tokens_in_window + reserved_tokens,
                cumulative_cost_usd=cumulative_cost,
                pending_reserved_cost_usd=pending_reserved_cost + reserved_cost_usd,
            ),
        )

    def release(
        self,
        *,
        lease_id: str,
        event_id: str,
        actual_tokens: int | None,
        actual_cost_usd: float | None,
        reserved_cost_usd: float,
        model_id: str,
    ) -> LimiterSnapshot:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            lease_row = db.execute(
                "SELECT event_id, reserved_cost_usd, model_id FROM leases "
                "WHERE lease_id = ?",
                (lease_id,),
            ).fetchone()
            if lease_row is None:
                db.rollback()
                raise RuntimePolicyError("rate-limit lease is missing or expired")
            if str(lease_row[0]) != event_id:
                db.rollback()
                raise RuntimePolicyError("rate-limit lease request-event binding mismatch")
            locked_reservation = float(lease_row[1])
            if str(lease_row[2]) != model_id:
                db.rollback()
                raise RuntimePolicyError("rate-limit lease model binding mismatch")
            if abs(locked_reservation - float(reserved_cost_usd)) > 1e-12:
                db.rollback()
                raise RuntimePolicyError("rate-limit lease cost reservation mismatch")
            token_row = db.execute(
                "SELECT tokens FROM request_window WHERE event_id = ?", (event_id,)
            ).fetchone()
            if token_row is None:
                db.rollback()
                raise RuntimePolicyError("request event is missing during release")
            locked_reserved_tokens = int(token_row[0])
            deleted = db.execute(
                "DELETE FROM leases WHERE lease_id = ? AND event_id = ?",
                (lease_id, event_id),
            )
            if deleted.rowcount != 1:
                db.rollback()
                raise RuntimePolicyError("rate-limit lease changed during release")
            token_reservation_exceeded = False
            normalized_actual_tokens: int | None = None
            if actual_tokens is not None:
                normalized_actual_tokens = max(0, int(actual_tokens))
                token_reservation_exceeded = (
                    normalized_actual_tokens > locked_reserved_tokens
                )
                # Keep the conservative admission reservation in the rate
                # window for its full lifetime.  Provider actual tokens are
                # recorded separately in the blind health ledger and must
                # never replace admission units in limiter accounting.
            cost_reservation_exceeded = False
            if actual_cost_usd is None:
                cost = locked_reservation
            else:
                cost = float(actual_cost_usd)
                if not math.isfinite(cost) or cost < 0:
                    db.rollback()
                    raise RuntimePolicyError("actual_cost_usd must be finite and non-negative")
                if cost > locked_reservation + 1e-12:
                    cost_reservation_exceeded = True
            updated_cost = db.execute(
                "UPDATE request_window SET cost_usd = ? WHERE event_id = ?",
                (cost, event_id),
            )
            if updated_cost.rowcount != 1:
                db.rollback()
                raise RuntimePolicyError("request event is missing during cost release")
            charge_kind = (
                "unknown_full_reservation"
                if actual_cost_usd is None
                else "provider_reported_actual"
            )
            try:
                db.execute(
                    "INSERT INTO run_cost(event_id, model_id, cost_usd, charge_kind, charged_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (event_id, model_id, cost, charge_kind, self.clock()),
                )
            except sqlite3.IntegrityError as exc:
                db.rollback()
                raise RuntimePolicyError(
                    "request event already has a durable cost charge"
                ) from exc
            if cost_reservation_exceeded or token_reservation_exceeded:
                db.execute(
                    "UPDATE run_state SET hard_blocked = 1, "
                    "reservation_violation_count = reservation_violation_count + 1, "
                    "violation_event_id = ?, violation_model_id = ?, violation_kind = ?, "
                    "violation_reserved_cost_usd = ?, violation_actual_cost_usd = ?, "
                    "violation_reserved_tokens = ?, violation_actual_tokens = ?, "
                    "violation_at = ? WHERE singleton_id = 1",
                    (
                        event_id,
                        model_id,
                        (
                            "cost_and_token_reservation"
                            if cost_reservation_exceeded
                            and token_reservation_exceeded
                            else (
                                "cost_reservation"
                                if cost_reservation_exceeded
                                else "token_reservation"
                            )
                        ),
                        locked_reservation,
                        cost,
                        locked_reserved_tokens,
                        normalized_actual_tokens,
                        self.clock(),
                    ),
                )
            active = int(db.execute("SELECT COUNT(*) FROM leases").fetchone()[0])
            row = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM request_window"
            ).fetchone()
            model_row = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM request_window "
                "WHERE model_id = ?",
                (model_id,),
            ).fetchone()
            model_active = int(
                db.execute(
                    "SELECT COUNT(*) FROM leases WHERE model_id = ?", (model_id,)
                ).fetchone()[0]
            )
            cumulative_cost = float(
                db.execute("SELECT COALESCE(SUM(cost_usd), 0.0) FROM run_cost").fetchone()[0]
            )
            pending_reserved_cost = float(
                db.execute(
                    "SELECT COALESCE(SUM(reserved_cost_usd), 0.0) FROM leases"
                ).fetchone()[0]
            )
            db.commit()
        if cost_reservation_exceeded or token_reservation_exceeded:
            raise RuntimeBudgetExceeded(
                "provider-reported request usage exceeded its locked token and/or "
                "cost reservation; actual usage was durably accounted and all new "
                "requests are hard-blocked"
            )
        return LimiterSnapshot(
            active_requests=active,
            requests_in_window=int(row[0]),
            tokens_in_window=int(row[1]),
            model_active_requests=model_active,
            model_requests_in_window=int(model_row[0]),
            model_tokens_in_window=int(model_row[1]),
            cumulative_cost_usd=cumulative_cost,
            pending_reserved_cost_usd=pending_reserved_cost,
        )

    def snapshot(self, *, model_id: str | None = None) -> LimiterSnapshot:
        """Read a transactionally consistent, evidence-free limiter snapshot."""

        now = self.clock()
        threshold = now - self.policy.rate_window_seconds
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._expire_leases(db, now=now)
            db.execute(
                "DELETE FROM request_window WHERE started_at <= ? "
                "AND event_id NOT IN (SELECT event_id FROM leases)",
                (threshold,),
            )
            active = int(db.execute("SELECT COUNT(*) FROM leases").fetchone()[0])
            pending = float(
                db.execute(
                    "SELECT COALESCE(SUM(reserved_cost_usd), 0.0) FROM leases"
                ).fetchone()[0]
            )
            row = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM request_window"
            ).fetchone()
            if model_id is None:
                model_active = active
                model_row = row
            else:
                normalized_model = model_id.removeprefix("openrouter/")
                if normalized_model not in REQUIRED_MODELS:
                    db.rollback()
                    raise RuntimePolicyError("snapshot model_id is outside the frozen set")
                model_active = int(
                    db.execute(
                        "SELECT COUNT(*) FROM leases WHERE model_id = ?",
                        (normalized_model,),
                    ).fetchone()[0]
                )
                model_row = db.execute(
                    "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM request_window "
                    "WHERE model_id = ?",
                    (normalized_model,),
                ).fetchone()
            cumulative = float(
                db.execute("SELECT COALESCE(SUM(cost_usd), 0.0) FROM run_cost").fetchone()[0]
            )
            db.commit()
        return LimiterSnapshot(
            active_requests=active,
            requests_in_window=int(row[0]),
            tokens_in_window=int(row[1]),
            model_active_requests=model_active,
            model_requests_in_window=int(model_row[0]),
            model_tokens_in_window=int(model_row[1]),
            cumulative_cost_usd=cumulative,
            pending_reserved_cost_usd=pending,
        )

    def budget_state_snapshot(self) -> BudgetStateSnapshot:
        """Return the durable, evidence-free hard-cap state for final acceptance."""

        # Trigger expiry accounting before reading totals.
        limiter_snapshot = self.snapshot()
        with self._connect() as db:
            row = db.execute(
                "SELECT hard_blocked, reservation_violation_count, violation_event_id "
                "FROM run_state WHERE singleton_id = 1"
            ).fetchone()
            if row is None:
                raise RuntimePolicyError("runtime budget state is missing")
            expired_count = int(
                db.execute("SELECT COUNT(*) FROM lease_expiry").fetchone()[0]
            )
        return BudgetStateSnapshot(
            budget_scope=self.budget_scope,
            clock_basis=self.clock_basis,
            host_boot_id=self.host_boot_id,
            hard_blocked=bool(int(row[0])),
            reservation_violation_count=int(row[1]),
            violation_event_id=None if row[2] is None else str(row[2]),
            cumulative_cost_usd=limiter_snapshot.cumulative_cost_usd,
            pending_reserved_cost_usd=limiter_snapshot.pending_reserved_cost_usd,
            active_leases=limiter_snapshot.active_requests,
            expired_unknown_cost_count=expired_count,
        )

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS runtime_metadata "
                "(singleton_id INTEGER PRIMARY KEY CHECK(singleton_id = 1), "
                "runtime_policy_semantic_sha256 TEXT NOT NULL, "
                "budget_scope TEXT NOT NULL, clock_basis TEXT NOT NULL, "
                "host_boot_id TEXT NOT NULL, boot_epoch INTEGER NOT NULL)"
            )
            metadata = db.execute(
                "SELECT runtime_policy_semantic_sha256, budget_scope, clock_basis, "
                "host_boot_id, boot_epoch FROM runtime_metadata WHERE singleton_id = 1"
            ).fetchone()
            expected_metadata = (
                self.policy.semantic_sha256,
                self.budget_scope,
                self.clock_basis,
                self.host_boot_id,
            )
            if metadata is None:
                legacy_tables = {
                    str(row[0])
                    for row in db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                } - {"runtime_metadata"}
                if legacy_tables:
                    raise RuntimePolicyError(
                        "limiter database lacks locked clock/boot metadata; explicit "
                        "audited recovery or a new preflight namespace is required"
                    )
                db.execute(
                    "INSERT INTO runtime_metadata(singleton_id, "
                    "runtime_policy_semantic_sha256, budget_scope, clock_basis, "
                    "host_boot_id, boot_epoch) VALUES (1, ?, ?, ?, ?, 0)",
                    expected_metadata,
                )
            elif tuple(metadata[:4]) != expected_metadata:
                if str(metadata[3]) != self.host_boot_id:
                    raise RuntimePolicyError(
                        "limiter database belongs to a different host boot; ordinary "
                        "workers may not reset monotonic state"
                    )
                raise RuntimePolicyError(
                    "limiter database policy/scope/clock metadata differs"
                )
            db.execute(
                "CREATE TABLE IF NOT EXISTS leases "
                "(lease_id TEXT PRIMARY KEY, event_id TEXT NOT NULL, expires_at REAL NOT NULL, "
                "reserved_cost_usd REAL NOT NULL, model_id TEXT NOT NULL)"
            )
            lease_columns = {
                str(row[1]) for row in db.execute("PRAGMA table_info(leases)").fetchall()
            }
            if "reserved_cost_usd" not in lease_columns:
                db.execute(
                    "ALTER TABLE leases ADD COLUMN reserved_cost_usd REAL NOT NULL DEFAULT 0.0"
                )
            if "model_id" not in lease_columns:
                db.execute(
                    "ALTER TABLE leases ADD COLUMN model_id TEXT NOT NULL DEFAULT ''"
                )
            if "event_id" not in lease_columns:
                db.execute(
                    "ALTER TABLE leases ADD COLUMN event_id TEXT NOT NULL DEFAULT ''"
                )
            legacy_active = int(
                db.execute(
                    "SELECT COUNT(*) FROM leases WHERE event_id = '' OR model_id = ''"
                ).fetchone()[0]
            )
            if legacy_active:
                raise RuntimePolicyError(
                    "legacy active rate-limit leases lack request/model bindings"
                )
            db.execute(
                "CREATE TABLE IF NOT EXISTS request_window "
                "(event_id TEXT PRIMARY KEY, started_at REAL NOT NULL, "
                "tokens INTEGER NOT NULL, cost_usd REAL NOT NULL, model_id TEXT NOT NULL)"
            )
            request_columns = {
                str(row[1])
                for row in db.execute("PRAGMA table_info(request_window)").fetchall()
            }
            if "model_id" not in request_columns:
                db.execute(
                    "ALTER TABLE request_window ADD COLUMN model_id TEXT NOT NULL DEFAULT ''"
                )
            db.execute(
                "CREATE TABLE IF NOT EXISTS run_cost "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, model_id TEXT, "
                "cost_usd REAL NOT NULL, charge_kind TEXT, charged_at REAL)"
            )
            cost_columns = {
                str(row[1]) for row in db.execute("PRAGMA table_info(run_cost)").fetchall()
            }
            for column, definition in (
                ("event_id", "TEXT"),
                ("model_id", "TEXT"),
                ("charge_kind", "TEXT"),
                ("charged_at", "REAL"),
            ):
                if column not in cost_columns:
                    db.execute(f"ALTER TABLE run_cost ADD COLUMN {column} {definition}")
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS run_cost_event_id_unique "
                "ON run_cost(event_id) WHERE event_id IS NOT NULL AND event_id <> ''"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS lease_expiry "
                "(event_id TEXT PRIMARY KEY, lease_id TEXT NOT NULL UNIQUE, "
                "model_id TEXT NOT NULL, reserved_cost_usd REAL NOT NULL, "
                "expired_at REAL NOT NULL, charged_at REAL NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS run_state "
                "(singleton_id INTEGER PRIMARY KEY CHECK(singleton_id = 1), "
                "hard_blocked INTEGER NOT NULL CHECK(hard_blocked IN (0, 1)), "
                "reservation_violation_count INTEGER NOT NULL, "
                "violation_event_id TEXT, violation_model_id TEXT, "
                "violation_kind TEXT, "
                "violation_reserved_cost_usd REAL, violation_actual_cost_usd REAL, "
                "violation_reserved_tokens INTEGER, violation_actual_tokens INTEGER, "
                "violation_at REAL)"
            )
            run_state_columns = {
                str(row[1])
                for row in db.execute("PRAGMA table_info(run_state)").fetchall()
            }
            for column, definition in (
                ("violation_kind", "TEXT"),
                ("violation_reserved_tokens", "INTEGER"),
                ("violation_actual_tokens", "INTEGER"),
            ):
                if column not in run_state_columns:
                    db.execute(
                        f"ALTER TABLE run_state ADD COLUMN {column} {definition}"
                    )
            db.execute(
                "INSERT OR IGNORE INTO run_state(singleton_id, hard_blocked, "
                "reservation_violation_count) VALUES (1, 0, 0)"
            )

    def _expire_leases(self, db: sqlite3.Connection, *, now: float) -> int:
        """Atomically charge unknown-cost reservations before deleting stale leases."""

        rows = db.execute(
            "SELECT lease_id, event_id, model_id, reserved_cost_usd, expires_at "
            "FROM leases WHERE expires_at <= ? ORDER BY lease_id",
            (now,),
        ).fetchall()
        for lease_id, event_id, model_id, reservation, expires_at in rows:
            event_text = str(event_id)
            model_text = str(model_id)
            cost = float(reservation)
            if not event_text or model_text not in REQUIRED_MODELS:
                raise RuntimePolicyError(
                    "expired rate-limit lease lacks a valid request/model binding"
                )
            if not math.isfinite(cost) or cost <= 0:
                raise RuntimePolicyError("expired rate-limit lease has invalid reservation")
            if db.execute(
                "SELECT 1 FROM run_cost WHERE event_id = ?", (event_text,)
            ).fetchone() is not None:
                raise RuntimePolicyError(
                    "expired rate-limit lease request event was already charged"
                )
            updated = db.execute(
                "UPDATE request_window SET cost_usd = ? WHERE event_id = ?",
                (cost, event_text),
            )
            if updated.rowcount != 1:
                raise RuntimePolicyError(
                    "expired rate-limit lease is missing its request-window event"
                )
            db.execute(
                "INSERT INTO run_cost(event_id, model_id, cost_usd, charge_kind, charged_at) "
                "VALUES (?, ?, ?, 'expired_unknown_full_reservation', ?)",
                (event_text, model_text, cost, now),
            )
            db.execute(
                "INSERT INTO lease_expiry(event_id, lease_id, model_id, "
                "reserved_cost_usd, expired_at, charged_at) VALUES (?, ?, ?, ?, ?, ?)",
                (event_text, str(lease_id), model_text, cost, float(expires_at), now),
            )
            deleted = db.execute(
                "DELETE FROM leases WHERE lease_id = ? AND event_id = ?",
                (str(lease_id), event_text),
            )
            if deleted.rowcount != 1:
                raise RuntimePolicyError("expired rate-limit lease changed during charging")
        return len(rows)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.database_path, timeout=30.0, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=30000")
            yield db
        finally:
            db.close()


class RateLimitLease:
    def __init__(
        self,
        *,
        limiter: GlobalRateLimiter,
        lease_id: str,
        event_id: str,
        reserved_tokens: int,
        reserved_cost_usd: float,
        model_id: str,
        waited_seconds: float,
        snapshot: LimiterSnapshot,
        auth_lifecycle_handle: _OpenRouterAuthLifecycleHandle,
    ) -> None:
        self.limiter = limiter
        self.lease_id = lease_id
        self.event_id = event_id
        self.reserved_tokens = reserved_tokens
        self.reserved_cost_usd = reserved_cost_usd
        self.model_id = model_id
        self.waited_seconds = waited_seconds
        self.snapshot = snapshot
        self._auth_lifecycle_handle = auth_lifecycle_handle
        self._released = False

    def release(
        self,
        *,
        actual_tokens: int | None = None,
        actual_cost_usd: float | None = None,
    ) -> LimiterSnapshot:
        if self._released:
            raise RuntimePolicyError("rate-limit lease was already released")
        self._released = True
        try:
            return self.limiter.release(
                lease_id=self.lease_id,
                event_id=self.event_id,
                actual_tokens=actual_tokens,
                actual_cost_usd=actual_cost_usd,
                reserved_cost_usd=self.reserved_cost_usd,
                model_id=self.model_id,
            )
        finally:
            self._auth_lifecycle_handle.close()

    def cancel(self) -> None:
        if self._released:
            raise RuntimePolicyError("rate-limit lease was already released or cancelled")
        self._released = True
        try:
            self.limiter.cancel_admission(
                lease_id=self.lease_id,
                event_id=self.event_id,
                model_id=self.model_id,
            )
        finally:
            self._auth_lifecycle_handle.close()


def retry_after_seconds(
    value: str | None,
    *,
    now_timestamp: float | None = None,
    maximum_seconds: float | None = None,
) -> float | None:
    """Parse Retry-After delta-seconds or HTTP-date and optionally clamp it."""

    if value is None or not str(value).strip():
        return None
    text = str(value).strip()
    try:
        parsed = max(0.0, float(text))
    except ValueError:
        try:
            date = parsedate_to_datetime(text)
        except (TypeError, ValueError, OverflowError):
            return None
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        now = time.time() if now_timestamp is None else now_timestamp
        parsed = max(0.0, date.timestamp() - now)
    if maximum_seconds is not None:
        parsed = min(parsed, maximum_seconds)
    return parsed


def retry_delay_seconds(
    policy: RetryPolicy,
    *,
    attempt_index: int,
    retry_after: float | None,
    random_value: float | None = None,
) -> float:
    """Return locked exponential backoff with symmetric bounded jitter."""

    if attempt_index < 1:
        raise RuntimePolicyError("attempt_index is one-based")
    exponential = min(
        policy.max_backoff_seconds,
        policy.base_delay_seconds * (policy.multiplier ** (attempt_index - 1)),
    )
    sample = random.random() if random_value is None else float(random_value)
    if not 0.0 <= sample <= 1.0:
        raise RuntimePolicyError("random_value must be between 0 and 1")
    jitter = exponential * policy.jitter_fraction * ((2.0 * sample) - 1.0)
    delayed = max(0.0, exponential + jitter)
    if policy.respect_retry_after and retry_after is not None:
        delayed = max(delayed, min(retry_after, policy.max_retry_after_seconds))
    return delayed


def _required_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise RuntimePolicyError(f"runtime policy {key} must be an object")
    return value


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimePolicyError(f"runtime policy {key} must be a non-empty string")
    return value.strip()


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise RuntimePolicyError(f"runtime policy {key} must be boolean")
    return value


def _required_int(payload: Mapping[str, Any], key: str, *, minimum: int) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RuntimePolicyError(f"runtime policy {key} must be an integer >= {minimum}")
    return value


def _required_float(payload: Mapping[str, Any], key: str, *, minimum: float) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) < minimum:
        raise RuntimePolicyError(f"runtime policy {key} must be a number >= {minimum}")
    return float(value)


def _coerce_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RuntimePolicyError(f"{field} values must be positive integers")
    return value


def _coerce_http_status(value: Any) -> int:
    status = _coerce_positive_int(value, "retry.retryable_http_statuses")
    if status < 100 or status > 599:
        raise RuntimePolicyError("retry.retryable_http_statuses values must be 100..599")
    return status


def _safe_identity_value(job: Mapping[str, Any], key: str) -> str:
    value = job.get(key)
    if not isinstance(value, str) or not value or len(value) > 512 or "\n" in value:
        raise RuntimePolicyError(f"sealed incident requires safe non-empty job.{key}")
    return value


def _require_exact_keys(
    payload: Mapping[str, Any], expected: set[str], *, field: str
) -> None:
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimePolicyError(
            f"{field} key mismatch: missing={missing!r} extra={extra!r}"
        )


def _load_receipt(path: str | Path, schema_name: str) -> dict[str, Any]:
    receipt_path = Path(path)
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise RuntimePolicyError(f"{schema_name} must be a regular, non-symlink file")
    try:
        loaded = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimePolicyError(f"could not load {schema_name}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise RuntimePolicyError(f"{schema_name} must contain a JSON object")
    validate_object(schema_name, loaded)
    return loaded


def _require_receipt_binding(
    receipt: Mapping[str, Any],
    *,
    expected_policy_sha256: str,
    expected_runtime_infra_file_sha256: str | None,
) -> None:
    expected_policy = expected_policy_sha256.removeprefix("sha256:")
    _validate_digest(expected_policy, "expected_policy_sha256")
    if receipt.get("runtime_policy_semantic_sha256") != expected_policy:
        raise RuntimePolicyError("receipt runtime-policy binding mismatch")
    if expected_runtime_infra_file_sha256 is not None:
        expected_infra = expected_runtime_infra_file_sha256.removeprefix("sha256:")
        _validate_digest(expected_infra, "expected_runtime_infra_file_sha256")
        if receipt.get("runtime_infra_file_sha256") != expected_infra:
            raise RuntimePolicyError("receipt runtime-infra binding mismatch")


def _validate_digest(value: str, field: str) -> str:
    digest = str(value).removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RuntimePolicyError(f"{field} must be a lowercase SHA-256 digest")
    return digest


def _validate_session_id(value: str) -> str:
    normalized = str(value)
    if (
        not normalized.startswith("session-")
        or not 9 <= len(normalized) <= 128
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for character in normalized)
    ):
        raise RuntimePolicyError("runtime session_id is invalid")
    return normalized


def _validate_host_boot_id(value: str) -> str:
    normalized = str(value).lower()
    compact = normalized.replace("-", "")
    if len(compact) != 32 or any(character not in "0123456789abcdef" for character in compact):
        raise RuntimePolicyError("host_boot_id must be a Linux boot UUID")
    return normalized


def linux_host_boot_id() -> str:
    path = Path("/proc/sys/kernel/random/boot_id")
    if path.is_symlink() or not path.is_file():
        raise RuntimePolicyError("formal runtime requires Linux boot_id from procfs")
    return _validate_host_boot_id(path.read_text(encoding="utf-8").strip())


def _default_limiter_host_boot_id() -> str:
    """Use Linux boot identity in production, with a stable non-Linux test sentinel."""

    path = Path("/proc/sys/kernel/random/boot_id")
    if path.is_file():
        return _validate_host_boot_id(path.read_text(encoding="utf-8").strip())
    # The benchmark worker is Linux-only.  This sentinel exists solely so the
    # deterministic limiter unit tests can run on the macOS development host.
    return "00000000-0000-0000-0000-000000000000"


def _normalize_required_model_catalog(
    entries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise RuntimePolicyError("model_catalog entries must be objects")
        model_id = str(entry.get("id") or entry.get("model_id") or "")
        if model_id in by_id:
            raise RuntimePolicyError(f"duplicate model_catalog entry: {model_id}")
        by_id[model_id] = entry
    if set(by_id) != set(REQUIRED_MODELS):
        raise RuntimePolicyError(
            "model_catalog must contain exactly the three frozen models"
        )
    normalized: list[dict[str, Any]] = []
    for model_id in REQUIRED_MODELS:
        row = by_id[model_id]
        context_length = row.get("context_length")
        if (
            isinstance(context_length, bool)
            or not isinstance(context_length, int)
            or context_length <= 0
        ):
            raise RuntimePolicyError(f"{model_id} context_length must be positive")
        pricing_raw = row.get("pricing")
        if not isinstance(pricing_raw, Mapping):
            raise RuntimePolicyError(f"{model_id} pricing must be an object")
        pricing: dict[str, float] = {}
        overrides_raw = pricing_raw.get("overrides", [])
        if not isinstance(overrides_raw, list):
            raise RuntimePolicyError(f"{model_id} pricing.overrides must be a list")
        for key, raw_value in pricing_raw.items():
            name = str(key)
            if (
                not name
                or len(name) > 64
                or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_" for char in name)
            ):
                raise RuntimePolicyError(f"{model_id} has unsafe pricing key {name!r}")
            if name == "overrides":
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise RuntimePolicyError(
                    f"{model_id} pricing.{name} must be numeric"
                ) from exc
            if not math.isfinite(value) or value < 0:
                raise RuntimePolicyError(
                    f"{model_id} pricing.{name} must be finite and non-negative"
                )
            pricing[name] = value
        # OpenRouter may publish token-threshold price tiers in an ``overrides``
        # list (for example, a higher price above a large prompt threshold).
        # Freeze the maximum scalar price from every tier so the receipt is a
        # conservative cost envelope without retaining the provider response.
        for ordinal, override_raw in enumerate(overrides_raw):
            if not isinstance(override_raw, Mapping):
                raise RuntimePolicyError(
                    f"{model_id} pricing.overrides[{ordinal}] must be an object"
                )
            threshold = override_raw.get("min_prompt_tokens")
            if (
                isinstance(threshold, bool)
                or not isinstance(threshold, int)
                or threshold <= 0
            ):
                raise RuntimePolicyError(
                    f"{model_id} pricing.overrides[{ordinal}].min_prompt_tokens "
                    "must be a positive integer"
                )
            for key, raw_value in override_raw.items():
                name = str(key)
                if name == "min_prompt_tokens":
                    continue
                if (
                    not name
                    or len(name) > 64
                    or any(
                        char not in "abcdefghijklmnopqrstuvwxyz0123456789_"
                        for char in name
                    )
                ):
                    raise RuntimePolicyError(
                        f"{model_id} has unsafe pricing override key {name!r}"
                    )
                try:
                    value = float(raw_value)
                except (TypeError, ValueError) as exc:
                    raise RuntimePolicyError(
                        f"{model_id} pricing.overrides[{ordinal}].{name} "
                        "must be numeric"
                    ) from exc
                if not math.isfinite(value) or value < 0:
                    raise RuntimePolicyError(
                        f"{model_id} pricing.overrides[{ordinal}].{name} "
                        "must be finite and non-negative"
                    )
                pricing[name] = max(pricing.get(name, 0.0), value)
        for required in ("prompt", "completion"):
            if required not in pricing:
                raise RuntimePolicyError(
                    f"{model_id} pricing must include {required!r}"
                )
        for optional in ("request", "internal_reasoning"):
            pricing.setdefault(optional, 0.0)
        pricing = dict(sorted(pricing.items()))
        supported_raw = row.get("supported_parameters")
        if not isinstance(supported_raw, list) or any(
            not isinstance(value, str)
            or not value
            or len(value) > 64
            or any(
                char not in "abcdefghijklmnopqrstuvwxyz0123456789_-"
                for char in value
            )
            for value in supported_raw
        ):
            raise RuntimePolicyError(
                f"{model_id} supported_parameters must be a string list"
            )
        supported_parameters = sorted(set(supported_raw))
        request_semantics_support = {
            parameter: (
                "declared_by_openrouter_models_catalog"
                if parameter in supported_parameters
                else "requires_successful_real_request_canary"
            )
            for parameter in OPENROUTER_REQUIRED_DECLARED_PARAMETERS
        }
        request_semantics_support.update(
            {
                "model": "openai_compatible_protocol_base_field",
                "messages": "openai_compatible_protocol_base_field",
                "max_tokens": (
                    "declared_by_openrouter_models_catalog"
                    if OPENROUTER_MAX_TOKENS_PARAMETER in supported_parameters
                    else "requires_successful_real_request_canary"
                ),
                "seed": (
                    "declared_by_openrouter_models_catalog"
                    if OPENROUTER_SEED_PARAMETER in supported_parameters
                    else "requires_successful_real_request_canary"
                ),
                "tool_protocol": "prompt_serialized_by_agentdojo_0.1.35",
                "native_tools": "request_field_absent",
                "native_tool_choice": "request_field_absent",
            }
        )
        normalized.append(
            {
                "model_id": model_id,
                "context_length": context_length,
                "pricing": pricing,
                "pricing_sha256": sha256_object(pricing),
                "supported_parameters": supported_parameters,
                "supported_parameters_sha256": sha256_object(
                    supported_parameters
                ),
                "request_semantics_support": request_semantics_support,
                "request_semantics_support_sha256": sha256_object(
                    request_semantics_support
                ),
            }
        )
    return normalized


def _optional_future_timestamp(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RuntimePolicyError(f"{field} must be null or an ISO-8601 timestamp")
    timestamp = value.strip()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimePolicyError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise RuntimePolicyError(f"{field} must include a timezone")
    if parsed <= datetime.now(timezone.utc):
        raise RuntimePolicyError(f"{field} is not in the future")
    return timestamp


def _validated_timestamp(value: str | None) -> str:
    timestamp = value or datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimePolicyError("receipt created_at is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise RuntimePolicyError("receipt created_at must include a timezone")
    return timestamp
