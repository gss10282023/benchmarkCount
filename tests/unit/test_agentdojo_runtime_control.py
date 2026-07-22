from __future__ import annotations

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from email.utils import format_datetime
from io import BytesIO
import grp
import json
import multiprocessing
import os
from pathlib import Path
import queue
from types import SimpleNamespace
import threading
import time
import urllib.error

import pytest

from evidence_system.adapters import agentdojo_runtime_control as runtime_control
from evidence_system.adapters import agentdojo
from evidence_system.adapters import agentdojo_worker
from evidence_system.cli import agentdojo_runtime_preflight


def _acquire_in_child(
    payload: dict[str, object], state_dir: str, output: object, release: object
) -> None:
    policy = runtime_control.load_runtime_policy(payload)
    limiter = runtime_control.GlobalRateLimiter(policy, state_dir=state_dir)
    lease = limiter.acquire(
        reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
    )
    output.put("acquired")
    release.wait(timeout=5)
    lease.release(actual_tokens=5, actual_cost_usd=0.0)


def _policy_payload(
    *, concurrency: int = 32, finalized: bool = False
) -> dict[str, object]:
    # Reduced-concurrency fixtures exercise limiter mechanics, not the locked
    # exploratory envelope (which is intentionally fixed at 32).
    finalized = finalized or concurrency != 32
    stages = (
        list(range(1, concurrency + 1))
        if concurrency < 4
        else sorted({4, 8, 16, 32, concurrency})
    )
    return {
        "schema_version": "agentdojo_openrouter_runtime_policy/v1",
        "policy_id": "unit-test-policy",
        "lifecycle": {
            "status": "finalized" if finalized else "provisional",
            "measurement_receipt_path": "measurement.json" if finalized else None,
            "measurement_receipt_sha256": "e" * 64 if finalized else None,
        },
        "execution_eligibility": {
            "mode": "finalized_validation" if finalized else "exploratory_measurement",
            "formal_execution_allowed": bool(finalized),
            "requested_measurement_envelope": {
                "requests_per_minute": 1000,
                "tokens_per_minute": 5_000_000,
                "concurrent_requests": 32,
            },
            "safe_margin_algorithm": (
                "floor_observed_admission_reservation_rate_times_0_80"
            ),
            "safe_margin_definition_sha256": (
                runtime_control.RATE_MEASUREMENT_SAFE_MARGIN_DEFINITION_SHA256
            ),
        },
        "clock": {
            **runtime_control.LIMITER_CLOCK_DEFINITION,
            "definition_sha256": runtime_control.LIMITER_CLOCK_DEFINITION_SHA256,
        },
        "token_rate_units": {
            **runtime_control.TOKEN_RATE_UNITS_DEFINITION,
            "definition_sha256": (
                runtime_control.TOKEN_RATE_UNITS_DEFINITION_SHA256
            ),
        },
        "operational_override": {
            "scope": "scheduling_only_no_request_semantics",
            "allowed_fields": [
                "rate_limit.requests_per_minute",
                "rate_limit.tokens_per_minute",
                "rate_limit.concurrent_requests",
            ],
            "base_agents_config_file_sha256": "a" * 64,
            "base_values": {
                "requests_per_minute": 30,
                "tokens_per_minute": 60_000,
                "concurrent_requests_per_agent": 1,
            },
            "effective_values": {
                "requests_per_minute": 1000,
                "tokens_per_minute": 5_000_000,
                "global_concurrent_requests": concurrency,
            },
            "per_model_safe_limits": (
                [
                    {
                        "model_id": model_id,
                        "requests_per_minute": 1000,
                        "tokens_per_minute": 5_000_000,
                        "concurrent_requests": concurrency,
                    }
                    for model_id in runtime_control.REQUIRED_MODELS
                ]
                if finalized
                else None
            ),
            "execution_key_fingerprint_sha256": (
                runtime_control.openrouter_key_fingerprint(
                    "unit-test-openrouter-key"
                )
                if finalized
                else None
            ),
            "formal_scheduling_invariant": {
                **runtime_control.FORMAL_SINGLE_MODEL_SCHEDULING_INVARIANT,
                "definition_sha256": (
                    runtime_control.FORMAL_SINGLE_MODEL_SCHEDULING_INVARIANT_SHA256
                ),
            },
            "reason": "unit-test scheduling override",
        },
        "scope": "single_openrouter_api_key_across_all_agentdojo_workers",
        "max_concurrent_requests": concurrency,
        "requests_per_minute": 1000,
        "tokens_per_minute": 5_000_000,
        "rate_window_seconds": 60,
        "prompt_token_reservation": {
            "method": "canonical_request_json_utf8_byte_upper_bound_plus_max_tokens",
            "version": "v1",
            "definition_sha256": (
                runtime_control.PROMPT_TOKEN_RESERVATION_DEFINITION_SHA256
            ),
        },
        "prompt_chars_per_token": 4.0,
        "completion_token_reservation": "request_max_tokens",
        "lease_timeout_seconds": 30,
        "acquire_poll_seconds": 0.01,
        "retry": {
            "max_attempts": 3,
            "retryable_http_statuses": [408, 409, 425, 429, 500, 502, 503, 504],
            "retry_transport_errors": True,
            "retry_invalid_json": True,
            "respect_retry_after": True,
            "base_delay_seconds": 2.0,
            "multiplier": 2.0,
            "max_backoff_seconds": 60.0,
            "max_retry_after_seconds": 300.0,
            "jitter_fraction": 0.25,
        },
        "budget": {
            "minimum_preflight_start_credit_usd": 800.0,
            "minimum_formal_start_remaining_usd": 650.0,
            "maximum_preflight_cost_usd": 120.0,
            "maximum_final_validation_cost_usd": 70.0,
            "maximum_run_cost_usd": 650.0,
            "maximum_single_request_cost_usd": 5.0,
            "cost_cap_action": "block_new_requests",
            "unknown_actual_cost_action": "charge_full_reservation",
        },
        "ramp": {
            "worker_concurrency_stages": stages,
            "promotion_requires": {
                "credential_probe_http_200": True,
                "four_suite_canary_complete": True,
                "unresolved_http_429_or_503": 0,
                "worker_failures": 0,
                "sustained_swap": False,
                "max_cpu_percent": 80.0,
                "max_memory_percent": 85.0,
                "minimum_resource_samples": 3,
                "minimum_active_request_fraction": 1.0,
                "minimum_active_worker_fraction": 1.0,
                "max_recovered_429_503_fraction": 0.1,
                "max_consecutive_429_503": 2,
                "max_retry_delay_seconds_per_chain": 60.0,
                "threshold_breach_action": "downgrade_and_continue",
            },
        },
        "health": {
            "blind_monitoring_only_before_checklist_freeze": True,
            "forbidden_fields": [
                "case_id",
                "prompt",
                "response",
                "trajectory",
                "evaluator",
                "label",
            ],
        },
    }


def _model_catalog() -> list[dict[str, object]]:
    return [
        {
            "id": model,
            "context_length": 200_000,
            "pricing": {
                "prompt": "0.000001",
                "completion": "0.000002",
                "request": "0",
                "internal_reasoning": "0.000001",
            },
            "supported_parameters": [
                "tools",
                "tool_choice",
                "temperature",
                "top_p",
                "seed",
            ],
        }
        for model in runtime_control.REQUIRED_MODELS
    ]


def _same_account_proof(
    tmp_path: Path, *, limit: float, remaining: float, usage: float
) -> dict[str, object]:
    projection = {
        "creator_user_id": "unit-test-user",
        "label": "unit-test-execution-key",
        "limit": limit,
        "limit_remaining": remaining,
        "limit_reset": None,
        "usage": usage,
        "expires_at": None,
    }
    return runtime_control.build_same_account_inventory_proof(
        execution_key_projection=projection,
        inventory_key_projections=[projection],
        page_receipts=[
            {
                "offset": 0,
                "count": 1,
                "canonical_response_sha256": "f" * 64,
            }
        ],
        auth_lifecycle_lock_path=tmp_path / "controller-auth.lock",
    )


def _stage_workload(
    stage: int, model_ordinal: int | None = 0
) -> dict[str, object]:
    return runtime_control.build_ramp_stage_workload_from_sources(
        worker_concurrency=stage,
        model_ordinal=model_ordinal,
        manifest_path="experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml",
        agents_config_path="configs/agents.yaml",
        source_bundle_path=(
            "experiments/agentdojo_full_v1.2.2_direct/"
            "source_bundles/case_packet_source_bundle.json"
        ),
        result_namespace="unit_test_disposable_preflight",
    )


def _write_passing_stage_ledgers(
    tmp_path: Path,
    *,
    policy: runtime_control.RuntimePolicy,
    stage: int,
    workload: dict[str, object],
) -> tuple[Path, Path]:
    raw_model_ordinal = workload["generation"]["model_ordinal"]  # type: ignore[index]
    model_ordinal = "mixed" if raw_model_ordinal is None else str(int(raw_model_ordinal))
    session_id = f"session-ramp-stage-{stage}-model-{model_ordinal}"
    boot_id = "12345678-1234-1234-1234-123456789abc"
    health_path = tmp_path / f"health-{stage}-model-{model_ordinal}.jsonl"
    credential_fingerprint = (
        policy.execution_key_fingerprint_sha256
        or runtime_control.openrouter_key_fingerprint("unit-test-openrouter-key")
    )
    ledger = runtime_control.BlindHealthLedger(
        (health_path,),
        policy_sha256=policy.semantic_sha256,
        session_id=session_id,
        host_boot_id=boot_id,
        credential_fingerprint_sha256=credential_fingerprint,
    )
    for workload_job in workload["jobs"]:  # type: ignore[index]
        job_digest = workload_job["job_identity_sha256"]
        model_digest = workload_job["model_config_sha256"]
        ledger.record(
            event_type="request_attempt",
            outcome="success",
            http_status=200,
            attempt_index=1,
            max_attempts=3,
            reserved_tokens=100,
            actual_total_tokens=80,
            active_requests=stage,
            requests_in_window=1,
            tokens_in_window=100,
            actual_cost_usd=0.01,
            reserved_cost_usd=5.0,
            cumulative_cost_usd=0.01,
            pending_reserved_cost_usd=0.0,
            job_identity_sha256=job_digest,
            model_config_sha256=model_digest,
            request_chain_id="req-" + str(job_digest)[:32],
            returned_model_identity_sha256=runtime_control.sha256_object(
                {
                    "provider": "unit-test-provider",
                    "model_config_sha256": model_digest,
                }
            ),
            temperature_parameter_present=1,
            top_p_parameter_present=1,
            max_tokens_parameter_present=1,
            seed_parameter_present=1,
            native_tools_parameter_absent=1,
            native_tool_choice_parameter_absent=1,
        )
        ledger.record(
            event_type="worker_completion",
            outcome="success",
            job_identity_sha256=job_digest,
            model_config_sha256=model_digest,
        )
    resource_path = tmp_path / f"resources-{stage}-model-{model_ordinal}.jsonl"
    resources = runtime_control.RampResourceLedger(resource_path)
    for _ in range(policy.ramp_minimum_resource_samples):
        resources.record(
            worker_concurrency=stage,
            cpu_percent=20.0,
            memory_percent=30.0,
            swap_used_bytes=0,
            active_worker_processes=stage,
            active_openrouter_leases=stage,
            budget_scope="disposable_preflight",
            runtime_database_path_sha256="b" * 64,
            stage_binding_sha256="c" * 64,
            worker_process_binding_sha256="d" * 64,
            expected_worker_uid=1000,
            minimum_worker_starttime_ticks=1,
            worker_process_set_sha256="e" * 64,
            foreign_agentdojo_worker_processes=0,
            stale_agentdojo_worker_processes=0,
            session_id=session_id,
            host_boot_id=boot_id,
        )
    return health_path, resource_path


def _replace_first_job_with_non_request_completion(
    health_path: Path,
    *,
    policy: runtime_control.RuntimePolicy,
    workload: dict[str, object],
    outcome: str,
) -> dict[str, object]:
    rows = [
        json.loads(line)
        for line in health_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    first_job = workload["jobs"][0]  # type: ignore[index]
    job_digest = str(first_job["job_identity_sha256"])
    rows = [
        row
        for row in rows
        if str(row.get("job_identity_sha256") or "") != job_digest
    ]
    health_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    binding = rows[0]
    runtime_control.BlindHealthLedger(
        (health_path,),
        policy_sha256=policy.semantic_sha256,
        session_id=str(binding["session_id"]),
        host_boot_id=str(binding["host_boot_id"]),
        credential_fingerprint_sha256=str(
            binding["credential_fingerprint_sha256"]
        ),
    ).record(
        event_type="worker_completion",
        outcome=outcome,
        job_identity_sha256=job_digest,
        model_config_sha256=str(first_job["model_config_sha256"]),
    )
    return first_job


def _control(
    tmp_path: Path, *, retry_invalid_json: bool = True
) -> agentdojo_worker.OpenRouterRuntimeControl:
    payload = _policy_payload()
    payload["retry"]["retry_invalid_json"] = retry_invalid_json  # type: ignore[index]
    policy = runtime_control.load_runtime_policy(payload)
    limiter = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path / "state")
    ledger = runtime_control.BlindHealthLedger(
        (tmp_path / "health.jsonl",),
        policy_sha256=policy.semantic_sha256,
        credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-openrouter-key"
        ),
    )
    job = {
        "job_id": "opaque-job-1",
        "case_unit_id": "v1.2.2:banking:user_task_0:injection_task_0",
        "record_slot_id": "record-slot-1",
    }
    sealed = runtime_control.SealedIncidentLedger(
        tmp_path / "sealed" / "incidents.jsonl",
        policy_sha256=policy.semantic_sha256,
    )
    return agentdojo_worker.OpenRouterRuntimeControl(
        policy=policy,
        limiter=limiter,
        ledger=ledger,
        sealed_incidents=sealed,
        job=job,
        job_identity_sha256=runtime_control.job_identity_sha256(job),
        model_config_sha256="d" * 64,
        credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-openrouter-key"
        ),
    )


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _valid_openrouter_response() -> dict[str, object]:
    return {
        "model": runtime_control.REQUIRED_MODELS[0],
        "provider": "unit-test-provider",
        "choices": [{"message": {"role": "assistant", "content": "ok"}}],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "cost": 0.01,
        },
    }


@pytest.mark.parametrize(
    ("mutation", "error_match"),
    [
        ({"error": {"message": "quota"}}, "contains an error"),
        ({"choices": []}, "non-empty choices"),
        ({"choices": [{}]}, "message object"),
        (
            {"choices": [{"message": {"role": "assistant", "content": ""}}]},
            "missing or empty",
        ),
        (
            {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 16,
                    "cost": 0.01,
                }
            },
            "differs from its components",
        ),
    ],
)
def test_openrouter_http_200_malformed_payload_is_not_a_success(
    mutation: dict[str, object], error_match: str
) -> None:
    payload = _valid_openrouter_response()
    payload.update(mutation)
    with pytest.raises(runtime_control.RuntimePolicyError, match=error_match) as exc_info:
        agentdojo_worker._validated_response_usage_and_model(
            payload,
            requested_model_id=runtime_control.REQUIRED_MODELS[0],
        )
    assert isinstance(
        exc_info.value, agentdojo_worker._OpenRouterResponseContractError
    )
    assert exc_info.value.retryable is True


def test_openrouter_returned_model_identity_drift_is_typed_nonretryable() -> None:
    payload = _valid_openrouter_response()
    payload["model"] = runtime_control.REQUIRED_MODELS[1]
    with pytest.raises(
        agentdojo_worker._OpenRouterResponseContractError,
        match="outside the locked canonical mapping",
    ) as exc_info:
        agentdojo_worker._validated_response_usage_and_model(
            payload,
            requested_model_id=runtime_control.REQUIRED_MODELS[0],
        )
    assert exc_info.value.retryable is False


def test_sealed_incident_ledger_rejects_hardlinked_target(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text("", encoding="utf-8")
    sealed_path = tmp_path / "sealed" / "incidents.jsonl"
    sealed_path.parent.mkdir()
    os.link(source, sealed_path)
    ledger = runtime_control.SealedIncidentLedger(
        sealed_path, policy_sha256="a" * 64
    )
    with pytest.raises(
        runtime_control.RuntimePolicyError, match="single-link regular file"
    ):
        ledger.record(
            incident_id="inc-hardlink",
            job={
                "job_id": "job-1",
                "case_unit_id": "v1.2.2:banking:user_task_0:injection_task_0",
                "record_slot_id": "slot-1",
            },
            error_category="runtime",
            error_origin="controller",
        )


def test_shared_blind_ledger_rejects_symlink_ancestor(tmp_path: Path) -> None:
    shared_root = tmp_path / "blind"
    real_session = shared_root / "real-session"
    real_session.mkdir(parents=True)
    (shared_root / "linked-session").symlink_to(real_session, target_is_directory=True)
    ledger = runtime_control.BlindHealthLedger(
        (shared_root / "linked-session" / "health.jsonl",),
        policy_sha256="a" * 64,
        shared_root=shared_root,
        shared_group=grp.getgrgid(os.getgid()).gr_name,
    )
    with pytest.raises(runtime_control.RuntimePolicyError, match="symlink"):
        ledger.record(event_type="ramp_health", outcome="passed")


def test_proxy_transform_forwards_locked_seed_top_p_and_forces_max_tokens() -> None:
    transformed = agentdojo_worker._transform_agentdojo_local_request(
        {
            "model": runtime_control.REQUIRED_MODELS[0],
            "messages": [{"role": "user", "content": "opaque-test"}],
            "temperature": 0.0,
            "top_p": 0.9,
            "seed": 12345,
        },
        model_id=runtime_control.REQUIRED_MODELS[0],
        temperature=0.0,
        max_tokens=4096,
    )
    assert transformed["top_p"] == 0.9
    assert transformed["seed"] == 12345
    assert transformed["max_tokens"] == 4096
    assert set(transformed) == {
        "model",
        "messages",
        "temperature",
        "top_p",
        "seed",
        "max_tokens",
    }
    with pytest.raises(runtime_control.RuntimePolicyError, match="allowlist"):
        agentdojo_worker._transform_agentdojo_local_request(
            {
                "model": runtime_control.REQUIRED_MODELS[0],
                "messages": [],
                "temperature": 0.0,
                "top_p": 0.9,
                "seed": 1,
                "max_tokens": 4096,
            },
            model_id=runtime_control.REQUIRED_MODELS[0],
            temperature=0.0,
            max_tokens=4096,
        )


def test_locked_job_seed_replays_local_llm_seed_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = {"runtime_scope": "disposable_preflight", "seed": 123456}
    monkeypatch.setenv("PYTHONHASHSEED", "123456")
    first_receipt = agentdojo_worker._apply_and_verify_locked_job_seed(job)
    first = [agentdojo_worker.random.randint(0, 2**32 - 1) for _ in range(20)]
    second_receipt = agentdojo_worker._apply_and_verify_locked_job_seed(job)
    second = [agentdojo_worker.random.randint(0, 2**32 - 1) for _ in range(20)]
    assert first == second
    assert first_receipt == second_receipt
    assert first_receipt["provider_determinism_claimed"] is False


def test_thirty_two_proxy_servers_bind_unique_ephemeral_ports(tmp_path: Path) -> None:
    def make(index: int) -> agentdojo_worker.OpenRouterProxyServer:
        server = agentdojo_worker.OpenRouterProxyServer(
            host="127.0.0.1",
            port=0,
            api_key="never-sent",
            model_id=runtime_control.REQUIRED_MODELS[0],
            temperature=0.0,
            max_tokens=4096,
            timeout_seconds=1,
            retry=0,
            log_dir=tmp_path / str(index),
        )
        return server

    servers: list[agentdojo_worker.OpenRouterProxyServer] = []
    bind_denied = False
    with ThreadPoolExecutor(max_workers=32) as pool:
        futures = [pool.submit(make, index) for index in range(32)]
        for future in futures:
            try:
                servers.append(future.result())
            except PermissionError:
                bind_denied = True
    if bind_denied:
        for server in servers:
            server.server.server_close()
        pytest.skip("sandbox forbids loopback socket binding")
    try:
        ports = [server.port for server in servers]
        assert all(port > 0 for port in ports)
        assert len(set(ports)) == 32
    finally:
        for server in servers:
            server.server.server_close()


@pytest.mark.parametrize(
    ("status", "retry_after", "minimum_delay"),
    [(429, "7", 7.0), (503, None, 2.0)],
)
def test_openrouter_retries_429_and_503_with_locked_backoff_and_blind_health(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    retry_after: str | None,
    minimum_delay: float,
) -> None:
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    responses: list[object] = [
        urllib.error.HTTPError(
            url="https://openrouter.invalid",
            code=status,
            msg="transient",
            hdrs=headers,
            fp=BytesIO(b'{"error":"redacted-test-body"}'),
        ),
        _Response(
            {
                "model": runtime_control.REQUIRED_MODELS[0],
                "provider": "unit-test-provider",
                "choices": [
                    {"message": {"role": "assistant", "content": "ok"}}
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": 0.01},
            }
        ),
    ]

    def fake_urlopen(*_args: object, **_kwargs: object) -> object:
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    sleeps: list[float] = []
    monkeypatch.setattr(agentdojo_worker.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(agentdojo_worker.time, "sleep", sleeps.append)
    monkeypatch.setattr(runtime_control.random, "random", lambda: 0.5)

    result = agentdojo_worker._request_openrouter(
        api_key="not-logged",
        payload={
            "model": runtime_control.REQUIRED_MODELS[0],
            "messages": [{"role": "user", "content": "secret"}],
            "max_tokens": 20,
        },
        timeout_seconds=5,
        retry=2,
        runtime_control=_control(tmp_path),
    )

    assert result["usage"]["total_tokens"] == 15
    assert len(sleeps) == 1
    assert sleeps[0] >= minimum_delay
    rows = [json.loads(line) for line in (tmp_path / "health.jsonl").read_text().splitlines()]
    assert [row["http_status"] for row in rows] == [status, 200]
    assert [row["outcome"] for row in rows] == ["retryable_error", "success"]
    serialized = json.dumps(rows)
    for forbidden in ("secret", "redacted-test-body", "prompt", "response", "trajectory", "evaluator", "label"):
        assert forbidden not in serialized
    assert rows[0]["incident_id"].startswith("inc-")
    assert len(rows[0]["job_identity_sha256"]) == 64
    sealed_path = tmp_path / "sealed" / "incidents.jsonl"
    sealed = json.loads(sealed_path.read_text().strip())
    assert sealed["incident_id"] == rows[0]["incident_id"]
    assert sealed["case_unit_id"].startswith("v1.2.2:banking:")
    assert sealed_path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "mutation",
    [
        {"error": {"message": "provider failure"}},
        {"choices": []},
        {"choices": [{"message": {"role": "assistant", "content": ""}}]},
        {"provider": None},
        {"usage": None},
        {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 16,
                "cost": 0.01,
            }
        },
    ],
)
def test_openrouter_retries_transient_http_200_response_contract_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: dict[str, object],
) -> None:
    malformed = _valid_openrouter_response()
    malformed.update(mutation)
    responses = [_Response(malformed), _Response(_valid_openrouter_response())]

    monkeypatch.setattr(
        agentdojo_worker.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: responses.pop(0),
    )
    sleeps: list[float] = []
    monkeypatch.setattr(agentdojo_worker.time, "sleep", sleeps.append)
    monkeypatch.setattr(runtime_control.random, "random", lambda: 0.5)

    result = agentdojo_worker._request_openrouter(
        api_key="not-logged",
        payload={
            "model": runtime_control.REQUIRED_MODELS[0],
            "messages": [{"role": "user", "content": "secret"}],
            "max_tokens": 20,
        },
        timeout_seconds=5,
        retry=2,
        runtime_control=_control(tmp_path),
    )

    assert result["usage"]["total_tokens"] == 15
    assert len(sleeps) == 1
    rows = [
        json.loads(line)
        for line in (tmp_path / "health.jsonl").read_text().splitlines()
    ]
    assert [row["http_status"] for row in rows] == [200, 200]
    assert [row["attempt_index"] for row in rows] == [1, 2]
    assert len({row["request_chain_id"] for row in rows}) == 1
    assert [row["outcome"] for row in rows] == ["retryable_error", "success"]
    assert "secret" not in json.dumps(rows)
    sealed = json.loads((tmp_path / "sealed" / "incidents.jsonl").read_text())
    assert sealed["error_category"] == "invalid_json"
    assert sealed["error_origin"] == "provider"


def test_openrouter_http_200_response_contract_retries_exhaust_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    malformed = _valid_openrouter_response()
    malformed["choices"] = []
    responses = [_Response(dict(malformed)) for _ in range(3)]
    monkeypatch.setattr(
        agentdojo_worker.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: responses.pop(0),
    )
    sleeps: list[float] = []
    monkeypatch.setattr(agentdojo_worker.time, "sleep", sleeps.append)
    monkeypatch.setattr(runtime_control.random, "random", lambda: 0.5)

    with pytest.raises(
        runtime_control.RuntimePolicyError, match="non-empty choices"
    ):
        agentdojo_worker._request_openrouter(
            api_key="not-logged",
            payload={
                "model": runtime_control.REQUIRED_MODELS[0],
                "messages": [],
                "max_tokens": 20,
            },
            timeout_seconds=5,
            retry=2,
            runtime_control=_control(tmp_path),
        )

    assert len(sleeps) == 2
    rows = [
        json.loads(line)
        for line in (tmp_path / "health.jsonl").read_text().splitlines()
    ]
    assert [row["attempt_index"] for row in rows] == [1, 2, 3]
    assert [row["http_status"] for row in rows] == [200, 200, 200]
    assert [row["outcome"] for row in rows] == [
        "retryable_error",
        "retryable_error",
        "fatal_error",
    ]
    assert len({row["request_chain_id"] for row in rows}) == 1
    sealed_rows = [
        json.loads(line)
        for line in (tmp_path / "sealed" / "incidents.jsonl").read_text().splitlines()
    ]
    assert len(sealed_rows) == 3
    assert {row["error_category"] for row in sealed_rows} == {"invalid_json"}


def test_openrouter_http_200_response_contract_respects_retry_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    malformed = _valid_openrouter_response()
    malformed["choices"] = []
    responses = [_Response(malformed), _Response(_valid_openrouter_response())]
    monkeypatch.setattr(
        agentdojo_worker.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: responses.pop(0),
    )
    sleeps: list[float] = []
    monkeypatch.setattr(agentdojo_worker.time, "sleep", sleeps.append)

    with pytest.raises(
        runtime_control.RuntimePolicyError, match="non-empty choices"
    ):
        agentdojo_worker._request_openrouter(
            api_key="not-logged",
            payload={
                "model": runtime_control.REQUIRED_MODELS[0],
                "messages": [],
                "max_tokens": 20,
            },
            timeout_seconds=5,
            retry=2,
            runtime_control=_control(tmp_path, retry_invalid_json=False),
        )

    assert sleeps == []
    assert len(responses) == 1
    row = json.loads((tmp_path / "health.jsonl").read_text().strip())
    assert row["outcome"] == "fatal_error"
    assert row["http_status"] == 200


@pytest.mark.parametrize("controlled", [True, False])
def test_openrouter_never_retries_returned_model_identity_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, controlled: bool
) -> None:
    mismatched = _valid_openrouter_response()
    mismatched["model"] = runtime_control.REQUIRED_MODELS[1]
    responses = [_Response(mismatched), _Response(_valid_openrouter_response())]
    monkeypatch.setattr(
        agentdojo_worker.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: responses.pop(0),
    )
    sleeps: list[float] = []
    monkeypatch.setattr(agentdojo_worker.time, "sleep", sleeps.append)

    with pytest.raises(
        runtime_control.RuntimePolicyError,
        match="outside the locked canonical mapping",
    ):
        agentdojo_worker._request_openrouter(
            api_key="not-logged",
            payload={
                "model": runtime_control.REQUIRED_MODELS[0],
                "messages": [],
                "max_tokens": 20,
            },
            timeout_seconds=5,
            retry=2,
            runtime_control=_control(tmp_path) if controlled else None,
        )

    assert sleeps == []
    assert len(responses) == 1
    if controlled:
        row = json.loads((tmp_path / "health.jsonl").read_text().strip())
        assert row["outcome"] == "fatal_error"
        assert row["http_status"] == 200


def test_non_retryable_http_error_fails_without_sleep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = urllib.error.HTTPError(
        url="https://openrouter.invalid",
        code=401,
        msg="unauthorized",
        hdrs={},
        fp=BytesIO(b'{"error":"credential detail"}'),
    )
    monkeypatch.setattr(
        agentdojo_worker.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )
    sleeps: list[float] = []
    monkeypatch.setattr(agentdojo_worker.time, "sleep", sleeps.append)
    with pytest.raises(RuntimeError, match="OpenRouter HTTP 401"):
        agentdojo_worker._request_openrouter(
            api_key="not-logged",
            payload={
                "model": runtime_control.REQUIRED_MODELS[0],
                "messages": [],
                "max_tokens": 20,
            },
            timeout_seconds=5,
            retry=2,
            runtime_control=_control(tmp_path),
        )
    assert sleeps == []
    row = json.loads((tmp_path / "health.jsonl").read_text().strip())
    assert row["outcome"] == "fatal_error"
    assert row["http_status"] == 401
    assert "credential detail" not in json.dumps(row)
    sealed = json.loads((tmp_path / "sealed" / "incidents.jsonl").read_text())
    assert sealed["error_category"] == "credential"
    assert sealed["error_origin"] == "credentials"


def test_global_limiter_is_shared_across_independent_instances(tmp_path: Path) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(concurrency=1))
    first = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    second = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    lease = first.acquire(
        reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
    )
    acquired = threading.Event()
    release_second = threading.Event()

    def acquire_second() -> None:
        other = second.acquire(
            reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
        )
        acquired.set()
        release_second.wait(timeout=2)
        other.release(actual_tokens=5, actual_cost_usd=0.0)

    thread = threading.Thread(target=acquire_second)
    thread.start()
    time.sleep(0.05)
    assert not acquired.is_set()
    lease.release(actual_tokens=5, actual_cost_usd=0.0)
    assert acquired.wait(timeout=2)
    release_second.set()
    thread.join(timeout=2)
    assert not thread.is_alive()


def test_formal_limiter_rejects_cross_model_parallel_overlap(tmp_path: Path) -> None:
    policy = runtime_control.load_runtime_policy(
        _policy_payload(finalized=True, concurrency=32)
    )
    limiter = runtime_control.GlobalRateLimiter(
        policy,
        state_dir=tmp_path / "formal-single-model",
        budget_scope="formal_execution",
    )
    first = limiter.acquire(
        reserved_tokens=10,
        reserved_cost_usd=0.01,
        model_id=runtime_control.REQUIRED_MODELS[0],
    )
    try:
        with pytest.raises(
            runtime_control.RuntimePolicyError,
            match="forbids cross-model concurrent leases",
        ):
            limiter.acquire(
                reserved_tokens=10,
                reserved_cost_usd=0.01,
                model_id=runtime_control.REQUIRED_MODELS[1],
            )
    finally:
        first.cancel()


def test_global_limiter_is_shared_across_processes(tmp_path: Path) -> None:
    context = multiprocessing.get_context("fork")
    payload = _policy_payload(concurrency=1)
    policy = runtime_control.load_runtime_policy(payload)
    parent_limiter = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    parent_lease = parent_limiter.acquire(
        reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
    )
    output = context.Queue()
    release = context.Event()
    process = context.Process(
        target=_acquire_in_child,
        args=(payload, str(tmp_path), output, release),
    )
    process.start()
    with pytest.raises(queue.Empty):
        output.get(timeout=0.1)
    parent_lease.release(actual_tokens=5, actual_cost_usd=0.0)
    assert output.get(timeout=3) == "acquired"
    release.set()
    process.join(timeout=3)
    assert process.exitcode == 0


def test_global_limiter_reserves_pending_cost_before_concurrent_admission(
    tmp_path: Path,
) -> None:
    payload = _policy_payload(concurrency=2)
    payload["budget"]["maximum_run_cost_usd"] = 9.0  # type: ignore[index]
    payload["budget"]["maximum_single_request_cost_usd"] = 5.0  # type: ignore[index]
    policy = runtime_control.load_runtime_policy(payload)
    limiter = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    first = limiter.acquire(
        reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
    )
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="cannot admit"):
        limiter.acquire(
            reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
        )
    snapshot = first.release(actual_tokens=5, actual_cost_usd=1.0)
    assert snapshot.cumulative_cost_usd == 1.0
    assert snapshot.pending_reserved_cost_usd == 0.0
    second = limiter.acquire(
        reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
    )
    second.release(actual_tokens=5, actual_cost_usd=None)
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="cannot admit"):
        limiter.acquire(
            reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
        )


def test_formal_budget_admission_override_records_cost_without_run_cap_block(
    tmp_path: Path,
) -> None:
    payload = _policy_payload(concurrency=2)
    payload["budget"]["maximum_run_cost_usd"] = 9.0  # type: ignore[index]
    payload["budget"]["maximum_single_request_cost_usd"] = 5.0  # type: ignore[index]
    policy = runtime_control.load_runtime_policy(payload)
    override_path = (
        tmp_path / runtime_control.FORMAL_BUDGET_ADMISSION_OVERRIDE_RELATIVE_PATH
    )
    override_path.parent.mkdir(parents=True)
    override_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    runtime_control.FORMAL_BUDGET_ADMISSION_OVERRIDE_SCHEMA_VERSION
                ),
                "status": "authorized",
                "created_at": "2026-07-18T00:00:00+00:00",
                "runtime_policy_semantic_sha256": policy.semantic_sha256,
                "budget_scope": "formal_execution",
                "original_cost_cap_action": "block_new_requests",
                "override_cost_cap_action": "record_only",
                "original_maximum_run_cost_usd": 9.0,
                "preserved_maximum_single_request_cost_usd": 5.0,
                "reason_code": "operator_removed_local_formal_run_cost_gate",
                "blind_only": True,
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    override_path.chmod(0o600)

    limiter = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    assert limiter.local_cost_cap_action == "record_only"
    assert limiter.formal_budget_admission_override_sha256 is not None
    first = limiter.acquire(
        reserved_tokens=10,
        reserved_cost_usd=5.0,
        model_id=runtime_control.REQUIRED_MODELS[0],
    )
    second = limiter.acquire(
        reserved_tokens=10,
        reserved_cost_usd=5.0,
        model_id=runtime_control.REQUIRED_MODELS[0],
    )
    first.release(actual_tokens=5, actual_cost_usd=4.75)
    snapshot = second.release(actual_tokens=5, actual_cost_usd=4.75)
    assert snapshot.cumulative_cost_usd == pytest.approx(9.5)
    assert snapshot.pending_reserved_cost_usd == 0.0
    with pytest.raises(runtime_control.RuntimePolicyError, match="single-request ceiling"):
        limiter.acquire(
            reserved_tokens=10,
            reserved_cost_usd=5.01,
            model_id=runtime_control.REQUIRED_MODELS[0],
        )


def test_formal_budget_admission_override_never_changes_preflight_cap(
    tmp_path: Path,
) -> None:
    payload = _policy_payload(concurrency=32)
    policy = runtime_control.load_runtime_policy(payload)
    override_path = (
        tmp_path / runtime_control.FORMAL_BUDGET_ADMISSION_OVERRIDE_RELATIVE_PATH
    )
    override_path.parent.mkdir(parents=True)
    override_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    runtime_control.FORMAL_BUDGET_ADMISSION_OVERRIDE_SCHEMA_VERSION
                ),
                "status": "authorized",
                "created_at": "2026-07-18T00:00:00+00:00",
                "runtime_policy_semantic_sha256": policy.semantic_sha256,
                "budget_scope": "formal_execution",
                "original_cost_cap_action": "block_new_requests",
                "override_cost_cap_action": "record_only",
                "original_maximum_run_cost_usd": 650.0,
                "preserved_maximum_single_request_cost_usd": 5.0,
                "reason_code": "operator_removed_local_formal_run_cost_gate",
                "blind_only": True,
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    override_path.chmod(0o600)

    limiter = runtime_control.GlobalRateLimiter(
        policy, state_dir=tmp_path, budget_scope="disposable_preflight"
    )
    assert limiter.local_cost_cap_action == "block_new_requests"
    assert limiter.formal_budget_admission_override_sha256 is None


def test_expired_leases_charge_all_unknown_reservations_before_budget_admission(
    tmp_path: Path,
) -> None:
    payload = _policy_payload(concurrency=32)
    payload["budget"]["maximum_single_request_cost_usd"] = 21.0  # type: ignore[index]
    clock = [1_000.0]
    policy = runtime_control.load_runtime_policy(payload)
    limiter = runtime_control.GlobalRateLimiter(
        policy,
        state_dir=tmp_path,
        clock=lambda: clock[0],
        sleep=lambda _seconds: None,
    )
    reservation = 650.0 / 32.0
    leases = [
        limiter.acquire(
            reserved_tokens=10,
            reserved_cost_usd=reservation,
            model_id=runtime_control.REQUIRED_MODELS[0],
        )
        for _ in range(32)
    ]
    assert len({lease.event_id for lease in leases}) == 32
    clock[0] += policy.lease_timeout_seconds + 1.0
    snapshot = limiter.snapshot()
    assert snapshot.active_requests == 0
    assert snapshot.pending_reserved_cost_usd == 0.0
    assert snapshot.cumulative_cost_usd == pytest.approx(650.0)
    with limiter._connect() as db:
        assert db.execute("SELECT COUNT(*) FROM run_cost").fetchone()[0] == 32
        assert db.execute("SELECT COUNT(*) FROM lease_expiry").fetchone()[0] == 32
        assert {
            row[0]
            for row in db.execute("SELECT DISTINCT charge_kind FROM run_cost")
        } == {"expired_unknown_full_reservation"}
        assert db.execute(
            "SELECT COUNT(DISTINCT event_id) FROM run_cost"
        ).fetchone()[0] == 32
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="cannot admit"):
        limiter.acquire(
            reserved_tokens=10,
            reserved_cost_usd=1.0,
            model_id=runtime_control.REQUIRED_MODELS[0],
        )


def test_actual_cost_above_reservation_persistently_hard_blocks_run(
    tmp_path: Path,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(concurrency=2))
    limiter = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    lease = limiter.acquire(
        reserved_tokens=10,
        reserved_cost_usd=5.0,
        model_id=runtime_control.REQUIRED_MODELS[0],
    )
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="exceeded"):
        lease.release(actual_tokens=5, actual_cost_usd=5.01)
    state = limiter.budget_state_snapshot()
    assert state.hard_blocked is True
    assert state.reservation_violation_count == 1
    assert state.violation_event_id == lease.event_id
    assert state.cumulative_cost_usd == pytest.approx(5.01)
    assert state.pending_reserved_cost_usd == 0.0
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="hard-blocked"):
        limiter.acquire(
            reserved_tokens=10,
            reserved_cost_usd=1.0,
            model_id=runtime_control.REQUIRED_MODELS[1],
        )


def test_actual_tokens_above_reservation_persistently_hard_blocks_run(
    tmp_path: Path,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(concurrency=2))
    limiter = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    lease = limiter.acquire(
        reserved_tokens=10,
        reserved_cost_usd=5.0,
        model_id=runtime_control.REQUIRED_MODELS[0],
    )
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="token and/or"):
        lease.release(actual_tokens=11, actual_cost_usd=0.01)
    state = limiter.budget_state_snapshot()
    assert state.hard_blocked is True
    assert state.reservation_violation_count == 1
    assert state.violation_event_id == lease.event_id
    assert state.cumulative_cost_usd == pytest.approx(0.01)
    assert state.pending_reserved_cost_usd == 0.0
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="hard-blocked"):
        limiter.acquire(
            reserved_tokens=10,
            reserved_cost_usd=1.0,
            model_id=runtime_control.REQUIRED_MODELS[1],
        )


def test_stage_closure_after_admission_cancels_without_usage_or_dangling_lease(
    tmp_path: Path,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(concurrency=2))
    limiter = runtime_control.GlobalRateLimiter(policy, state_dir=tmp_path)
    checks = 0

    def closes_between_admission_and_send() -> None:
        nonlocal checks
        checks += 1
        if checks >= 2:
            raise runtime_control.RuntimePolicyError("stage closed")

    with pytest.raises(runtime_control.RuntimePolicyError, match="stage closed"):
        limiter.acquire(
            reserved_tokens=10,
            reserved_cost_usd=1.0,
            model_id=runtime_control.REQUIRED_MODELS[0],
            currentness_check=closes_between_admission_and_send,
        )
    snapshot = limiter.snapshot(model_id=runtime_control.REQUIRED_MODELS[0])
    state = limiter.budget_state_snapshot()
    assert snapshot.active_requests == 0
    assert snapshot.requests_in_window == 0
    assert snapshot.tokens_in_window == 0
    assert state.cumulative_cost_usd == 0
    assert state.pending_reserved_cost_usd == 0
    assert state.active_leases == 0


def test_preflight_and_formal_cost_states_are_physically_and_logically_separate(
    tmp_path: Path,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(concurrency=32))
    preflight = runtime_control.GlobalRateLimiter(
        policy,
        state_dir=tmp_path,
        budget_scope="disposable_preflight",
    )
    formal = runtime_control.GlobalRateLimiter(
        policy,
        state_dir=tmp_path,
        budget_scope="formal_execution",
    )
    assert preflight.database_path != formal.database_path
    leases = [
        preflight.acquire(
            reserved_tokens=10,
            reserved_cost_usd=5.0,
            model_id=runtime_control.REQUIRED_MODELS[index % 3],
        )
        for index in range(24)
    ]
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="cost cap"):
        preflight.acquire(
            reserved_tokens=10,
            reserved_cost_usd=5.0,
            model_id=runtime_control.REQUIRED_MODELS[0],
        )
    for lease in leases:
        lease.release(actual_tokens=5, actual_cost_usd=None)
    preflight_state = preflight.budget_state_snapshot()
    formal_state = formal.budget_state_snapshot()
    assert preflight_state.budget_scope == "disposable_preflight"
    assert preflight_state.cumulative_cost_usd == pytest.approx(120.0)
    assert preflight_state.pending_reserved_cost_usd == 0.0
    assert formal_state.budget_scope == "formal_execution"
    assert formal_state.cumulative_cost_usd == 0.0
    assert formal_state.pending_reserved_cost_usd == 0.0


def test_two_layer_limiter_enforces_model_and_global_concurrency(
    tmp_path: Path,
) -> None:
    payload = _policy_payload(concurrency=2, finalized=True)
    model_rows = payload["operational_override"]["per_model_safe_limits"]  # type: ignore[index]
    model_rows[0]["concurrent_requests"] = 1
    policy = runtime_control.load_runtime_policy(payload)
    limiter = runtime_control.GlobalRateLimiter(
        policy, state_dir=tmp_path, budget_scope="disposable_preflight"
    )
    first = limiter.acquire(
        reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[0]
    )
    assert limiter._try_acquire(
        reserved_tokens=10,
        reserved_cost_usd=1.0,
        model_id=runtime_control.REQUIRED_MODELS[0],
    ) is None
    second = limiter.acquire(
        reserved_tokens=10, model_id=runtime_control.REQUIRED_MODELS[1]
    )
    assert second.snapshot.active_requests == 2
    assert second.snapshot.model_active_requests == 1
    assert limiter._try_acquire(
        reserved_tokens=10,
        reserved_cost_usd=1.0,
        model_id=runtime_control.REQUIRED_MODELS[2],
    ) is None
    first.release(actual_tokens=5, actual_cost_usd=0.0)
    second.release(actual_tokens=5, actual_cost_usd=0.0)


def _fake_procfs_worker(
    proc_root: Path,
    *,
    pid: int,
    uid: int,
    starttime_ticks: int,
    binding: str,
) -> None:
    proc_root.mkdir(parents=True, exist_ok=True)
    (proc_root / "stat").write_text(
        "cpu 100 0 0 100 0 0 0 0\n", encoding="utf-8"
    )
    (proc_root / "meminfo").write_text(
        "MemTotal: 1000 kB\nMemAvailable: 750 kB\n"
        "SwapTotal: 0 kB\nSwapFree: 0 kB\n",
        encoding="utf-8",
    )
    process = proc_root / str(pid)
    process.mkdir()
    process.joinpath("cmdline").write_bytes(
        b"python\x00-m\x00evidence_system.adapters.agentdojo_worker\x00"
        b"--resource-stage-token\x00"
        + binding.encode("ascii")
        + b"\x00"
    )
    process.joinpath("status").write_text(
        f"Name:\tpython\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n",
        encoding="utf-8",
    )
    fields_after_command = ["S", *(["0"] * 49)]
    fields_after_command[19] = str(starttime_ticks)
    process.joinpath("stat").write_text(
        f"{pid} (python worker) {' '.join(fields_after_command)}\n",
        encoding="utf-8",
    )


def _advance_fake_procfs_cpu(proc_root: Path) -> None:
    proc_root.joinpath("stat").write_text(
        "cpu 200 0 0 150 0 0 0 0\n", encoding="utf-8"
    )


def test_resource_sampler_counts_only_exact_stage_bound_workers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binding = "a" * 64
    proc_root = tmp_path / "proc"
    _fake_procfs_worker(
        proc_root,
        pid=101,
        uid=1234,
        starttime_ticks=200,
        binding=binding,
    )
    monkeypatch.setattr(
        runtime_control.time,
        "sleep",
        lambda _seconds: _advance_fake_procfs_cpu(proc_root),
    )
    observed = runtime_control.sample_linux_host_resources(
        sample_seconds=0.05,
        worker_process_binding_sha256=binding,
        expected_worker_uid=1234,
        minimum_worker_starttime_ticks=150,
        proc_root=proc_root,
    )
    assert observed["active_worker_processes"] == 1
    assert observed["foreign_agentdojo_worker_processes"] == 0
    assert observed["stale_agentdojo_worker_processes"] == 0
    assert len(observed["worker_process_set_sha256"]) == 64


@pytest.mark.parametrize(
    ("observed_binding", "starttime_ticks", "message"),
    [
        ("b" * 64, 200, "foreign AgentDojo worker"),
        ("a" * 64, 100, "stale AgentDojo worker"),
    ],
)
def test_resource_sampler_rejects_foreign_or_stale_workers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    observed_binding: str,
    starttime_ticks: int,
    message: str,
) -> None:
    proc_root = tmp_path / "proc"
    _fake_procfs_worker(
        proc_root,
        pid=101,
        uid=1234,
        starttime_ticks=starttime_ticks,
        binding=observed_binding,
    )
    monkeypatch.setattr(
        runtime_control.time,
        "sleep",
        lambda _seconds: _advance_fake_procfs_cpu(proc_root),
    )
    with pytest.raises(runtime_control.RuntimePolicyError, match=message):
        runtime_control.sample_linux_host_resources(
            sample_seconds=0.05,
            worker_process_binding_sha256="a" * 64,
            expected_worker_uid=1234,
            minimum_worker_starttime_ticks=150,
            proc_root=proc_root,
        )


def test_shared_preflight_budget_caps_each_phase_and_two_round_aggregate(
    tmp_path: Path,
) -> None:
    shared_path = tmp_path / "shared-preflight-budget.sqlite3"
    ledger = runtime_control.SharedPreflightBudgetLedger(
        shared_path,
        policy_sha256="a" * 64,
        lease_timeout_seconds=180,
        host_boot_id="11111111-1111-1111-1111-111111111111",
    )
    for phase in ("exploratory_measurement", "finalized_validation"):
        for _ in range(12):
            ledger.acquire(phase=phase, reserved_cost_usd=5.0).release(
                actual_cost_usd=None
            )
    snapshot = ledger.snapshot()
    assert snapshot.measurement_cost_usd == 60.0
    assert snapshot.validation_cost_usd == 60.0
    assert snapshot.aggregate_cost_usd == 120.0
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="aggregate"):
        ledger.acquire(
            phase="exploratory_measurement", reserved_cost_usd=0.01
        )


def test_shared_preflight_budget_recovers_pending_as_unknown_after_boot(
    tmp_path: Path,
) -> None:
    shared_path = tmp_path / "shared-preflight-budget.sqlite3"
    first = runtime_control.SharedPreflightBudgetLedger(
        shared_path,
        policy_sha256="a" * 64,
        lease_timeout_seconds=180,
        host_boot_id="11111111-1111-1111-1111-111111111111",
    )
    first.acquire(
        phase="exploratory_measurement", reserved_cost_usd=5.0
    )
    recovered = runtime_control.SharedPreflightBudgetLedger(
        shared_path,
        policy_sha256="a" * 64,
        lease_timeout_seconds=180,
        host_boot_id="22222222-2222-2222-2222-222222222222",
    ).snapshot()
    assert recovered.active_leases == 0
    assert recovered.pending_reserved_cost_usd == 0.0
    assert recovered.measurement_cost_usd == 5.0
    assert recovered.expired_or_boot_recovered_unknown_cost_count == 1


def test_token_admission_uses_locked_utf8_byte_upper_bound() -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload())
    payload = {
        "model": runtime_control.REQUIRED_MODELS[0],
        "messages": [
            {
                "role": "user",
                "content": "转账前解析这个 JSON：{\"工具\":\"查询\",\"值\":\"🔐\"}",
            }
        ],
        "tools": [{"type": "function", "function": {"name": "查余额"}}],
        "max_tokens": 50,
    }
    serialized = json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert runtime_control.estimate_request_tokens(payload, policy) == len(serialized) + 50
    assert len(serialized) > len(json.dumps(payload, ensure_ascii=False)) / 4


def test_token_admission_rejects_definition_hash_drift() -> None:
    payload = _policy_payload(finalized=True)
    payload["prompt_token_reservation"]["definition_sha256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(runtime_control.RuntimePolicyError, match="definition SHA-256"):
        runtime_control.load_runtime_policy(payload)


def test_formal_health_failure_seals_valid_downgrade_receipt(
    tmp_path: Path,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(finalized=True))
    session_id = "session-formal-health-failure"
    boot_id = "12345678-1234-1234-1234-123456789abc"
    model_rows = [
        {
            "agent_id": agent_id,
            "model_id": model_id,
            "model_config_sha256": chr(ord("a") + index) * 64,
            "record_slot_count": 1 if index == 0 else 0,
        }
        for index, (agent_id, model_id) in enumerate(
            zip(
                runtime_control.REQUIRED_AGENT_IDS,
                runtime_control.REQUIRED_MODELS,
                strict=True,
            )
        )
    ]
    workload = runtime_control.build_formal_locked_stage_workload(
        execution_lock_sha256="d" * 64,
        execution_policy_sha256="e" * 64,
        plan_index_sha256="f" * 64,
        stage_id="ramp-a-8",
        workers=8,
        record_slot_ids_sha256="1" * 64,
        record_slot_count=1,
        agent_models=model_rows,
        target_agent_id="Agent A",
    )
    health_path = tmp_path / "formal-health.jsonl"
    runtime_control.BlindHealthLedger(
        (health_path,),
        policy_sha256=policy.semantic_sha256,
        session_id=session_id,
        host_boot_id=boot_id,
    ).record(
        event_type="request_attempt",
        outcome="fatal_error",
        http_status=503,
        attempt_index=3,
        max_attempts=3,
        reserved_tokens=100,
        active_requests=1,
        requests_in_window=1,
        tokens_in_window=100,
        reserved_cost_usd=5.0,
        cumulative_cost_usd=5.0,
        pending_reserved_cost_usd=0.0,
        job_identity_sha256="9" * 64,
        model_config_sha256="a" * 64,
        request_chain_id="req-" + "8" * 32,
    )
    resource_path = tmp_path / "formal-resources.jsonl"
    resources = runtime_control.RampResourceLedger(resource_path)
    for _ in range(policy.ramp_minimum_resource_samples):
        resources.record(
            worker_concurrency=8,
            cpu_percent=20.0,
            memory_percent=30.0,
            swap_used_bytes=0,
            active_worker_processes=8,
            active_openrouter_leases=8,
            budget_scope="formal_execution",
            runtime_database_path_sha256="b" * 64,
            stage_binding_sha256="c" * 64,
            worker_process_binding_sha256="d" * 64,
            expected_worker_uid=1000,
            minimum_worker_starttime_ticks=1,
            worker_process_set_sha256="e" * 64,
            foreign_agentdojo_worker_processes=0,
            stale_agentdojo_worker_processes=0,
            session_id=session_id,
            host_boot_id=boot_id,
        )
    receipt = runtime_control.build_formal_stage_health_receipt(
        policy,
        stage_workload=workload,
        runtime_infra_file_sha256="2" * 64,
        blind_health_ledger_path=health_path,
        resource_ledger_path=resource_path,
        session_id=session_id,
        host_boot_id=boot_id,
        session_started_at="2020-01-01T00:00:00+00:00",
        session_ended_at="2099-01-01T00:00:00+00:00",
        prior_safe_workers=4,
    )
    assert receipt["status"] == "valid_hold_or_downgrade"
    assert receipt["promotion_authorized"] is False
    assert receipt["safe_workers"] == 4
    assert receipt["model_decisions"][0]["worker_failure_count"] == 1
    assert receipt["model_decisions"][0]["promotion_authorized"] is False


def test_retry_after_supports_http_date_and_clamps() -> None:
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)
    later = datetime(2026, 7, 16, 0, 10, tzinfo=timezone.utc)
    assert runtime_control.retry_after_seconds(
        format_datetime(later),
        now_timestamp=now.timestamp(),
        maximum_seconds=300,
    ) == 300


def test_blind_health_rejects_evidence_bearing_fields(tmp_path: Path) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload())
    ledger = runtime_control.BlindHealthLedger(
        (tmp_path / "health.jsonl",), policy_sha256=policy.semantic_sha256
    )
    with pytest.raises(runtime_control.RuntimePolicyError, match="forbidden field"):
        ledger.record(
            event_type="incident",
            outcome="warning",
            prompt="must never be accepted",
        )


def test_policy_hash_and_credit_floor_fail_closed() -> None:
    payload = _policy_payload()
    with pytest.raises(runtime_control.RuntimePolicyError, match="semantic SHA-256 mismatch"):
        runtime_control.load_runtime_policy(payload, expected_semantic_sha256="0" * 64)
    policy = runtime_control.load_runtime_policy(payload)
    with pytest.raises(runtime_control.RuntimeBudgetExceeded, match="below the locked"):
        runtime_control.validate_starting_credit(policy, available_credit_usd=649.99)


def test_finalized_policy_preserves_attempted_ramp_above_active_ceiling() -> None:
    policy = runtime_control.load_runtime_policy(
        _policy_payload(concurrency=8, finalized=True)
    )

    assert policy.ramp_stages == (4, 8, 16, 32)
    assert policy.max_concurrent_requests == 8
    assert policy.per_model_safe_limits is not None
    assert {
        int(row["concurrent_requests"])
        for row in policy.per_model_safe_limits.values()
    } == {8}


def test_finalized_policy_rejects_active_ceiling_outside_attempted_ramp() -> None:
    payload = _policy_payload(concurrency=8, finalized=True)
    payload["max_concurrent_requests"] = 7
    payload["operational_override"]["effective_values"][  # type: ignore[index]
        "global_concurrent_requests"
    ] = 7

    with pytest.raises(
        runtime_control.RuntimePolicyError,
        match="must be one locked attempted ramp stage",
    ):
        runtime_control.load_runtime_policy(payload)


def test_finalized_policy_rejects_global_ceiling_not_derived_from_models() -> None:
    payload = _policy_payload(concurrency=8, finalized=True)
    model_rows = payload["operational_override"][  # type: ignore[index]
        "per_model_safe_limits"
    ]
    for row in model_rows:
        row["concurrent_requests"] = 4

    with pytest.raises(
        runtime_control.RuntimePolicyError,
        match="must equal the maximum per-model safe concurrency",
    ):
        runtime_control.load_runtime_policy(payload)


def test_provisional_policy_still_requires_ramp_to_end_at_full_envelope() -> None:
    payload = _policy_payload()
    payload["ramp"]["worker_concurrency_stages"] = [4, 8, 16]  # type: ignore[index]

    with pytest.raises(
        runtime_control.RuntimePolicyError,
        match="provisional policy's final ramp.*must equal",
    ):
        runtime_control.load_runtime_policy(payload)


def test_formal_planner_injects_locked_policy_and_shared_state_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _policy_payload(finalized=True)
    policy = runtime_control.load_runtime_policy(payload)
    monkeypatch.setattr(agentdojo, "_agentdojo_install_source_lock", lambda _entry: {})
    target = SimpleNamespace(
        machine_id="vps-1",
        machine_role="benchmark_runner",
        benchmark_name="AgentDojo",
        remote_workdir="/srv/agentdojo/repo",
        runner_workdir="/srv/agentdojo/repo",
        benchmark_config={
            "install_dir": "/srv/agentdojo/repo",
            "remote_raw_root": "/srv/agentdojo/sealed/raw",
            "blind_aggregate_root": "/srv/agentdojo/blind",
            "runtime_state_root": "/srv/agentdojo/runtime-state/formal",
            "secret_env_path": "/srv/agentdojo/secrets/openrouter.env",
        },
    )
    job = {
        "job_id": "job-1",
        "domain": "agentdojo",
        "task_id": "v1.2.2:banking:user_task_0:injection_task_0",
        "case_unit_id": "v1.2.2:banking:user_task_0:injection_task_0",
        "agent_id": "Agent A",
        "phase": "full",
        "result_namespace": "agentdojo_full_v1.2.2_direct",
        "execution_lock_sha256": "e" * 64,
        "execution_policy_sha256": "f" * 64,
        "seed": 101,
        "openrouter_runtime_policy": payload,
        "openrouter_runtime_policy_sha256": policy.semantic_sha256,
        "openrouter_runtime_policy_file_sha256": "a" * 64,
    }
    source = {"task_id": job["task_id"], "domain": "agentdojo"}
    plan = agentdojo.plan_smoke_execution(
        job,
        target=target,
        agents_config_path="configs/agents.yaml",
        dotenv_path=".env",
        source_bundle_path="bundle.json",
        source_bundle={"sources": [source]},
    )
    assert plan["status"] == "runnable"
    command = plan["runner_command"]
    assert "--openrouter-runtime-policy-json" in command
    assert f"--openrouter-runtime-policy-sha256 {policy.semantic_sha256}" in command
    assert "--openrouter-runtime-policy-file-sha256 " + ("a" * 64) in command
    assert "--runtime-state-dir /srv/agentdojo/runtime-state/formal" in command
    assert "/repo/results/runtime_state/" not in command


def test_runtime_override_is_limited_to_concurrency_rate_field() -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload())
    roles = {
        agent_id: {
            "provider": "openrouter",
            "model": model,
            "temperature": 0,
            "rate_limit": {
                "requests_per_minute": 30,
                "tokens_per_minute": 60_000,
                "concurrent_requests": 1,
            },
        }
        for agent_id, model in (
            ("Agent A", "model-a"),
            ("Agent B", "model-b"),
            ("Agent C", "model-c"),
        )
    }
    snapshot = runtime_control.rate_only_override_snapshot(roles, policy)
    assert snapshot["override_fields"] == [
        "rate_limit.requests_per_minute",
        "rate_limit.tokens_per_minute",
        "rate_limit.concurrent_requests",
    ]
    assert snapshot["effective_global_concurrent_requests"] == 32
    assert snapshot["source_concurrent_requests"] == {
        "Agent A": 1,
        "Agent B": 1,
        "Agent C": 1,
    }
    roles["Agent A"]["rate_limit"]["tokens_per_minute"] = 59_999
    with pytest.raises(runtime_control.RuntimePolicyError, match="base TPM differs"):
        runtime_control.rate_only_override_snapshot(roles, policy)


def test_probe_and_ramp_receipts_bind_policy_infra_and_blind_health(tmp_path: Path) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(finalized=True))
    infra_sha = "b" * 64
    credential = runtime_control.build_credential_probe_receipt(
        policy,
        runtime_infra_file_sha256=infra_sha,
        http_status=200,
        key_limit_usd=1000.0,
        key_limit_remaining_usd=730.0,
        key_usage_usd=270.0,
        key_is_free_tier=False,
        key_is_management=False,
        key_is_provisioning=False,
        key_disabled=False,
        key_disabled_field_present=True,
        key_limit_reset_policy=None,
        key_expires_at=None,
        model_catalog_entries=_model_catalog(),
        credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-openrouter-key"
        ),
        management_audit_fingerprint_sha256=(
            runtime_control.openrouter_management_audit_fingerprint(
                "unit-test-management-key"
            )
        ),
        management_key_identity_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-management-key"
        ),
        management_key_is_management=True,
        management_key_is_provisioning=False,
        management_key_disabled=False,
        same_account_inventory_proof=_same_account_proof(
            tmp_path, limit=1000.0, remaining=730.0, usage=270.0
        ),
        account_total_credits_usd=1000.0,
        account_total_usage_usd=100.0,
        probe_phase="pre_final_validation",
    )
    credential_path = tmp_path / "credential_probe_receipt.json"
    credential_path.write_text(json.dumps(credential), encoding="utf-8")
    loaded_credential = runtime_control.load_credential_probe_receipt(
        credential_path,
        expected_policy_sha256=policy.semantic_sha256,
        expected_runtime_infra_file_sha256=infra_sha,
    )
    assert loaded_credential["secret_material_recorded"] is False
    assert loaded_credential["models_available"] == list(runtime_control.REQUIRED_MODELS)

    stage_paths: list[Path] = []
    mixed_workload = _stage_workload(4, None)
    mixed_health, mixed_resources = _write_passing_stage_ledgers(
        tmp_path, policy=policy, stage=4, workload=mixed_workload
    )
    mixed_receipt = runtime_control.build_ramp_stage_receipt(
        policy,
        scope="disposable_preflight",
        worker_concurrency=4,
        runtime_infra_file_sha256=infra_sha,
        blind_health_ledger_path=mixed_health,
        resource_ledger_path=mixed_resources,
        stage_workload=mixed_workload,
    )
    mixed_path = tmp_path / "stage-4-model-mixed.json"
    mixed_path.write_text(json.dumps(mixed_receipt), encoding="utf-8")
    for stage in policy.ramp_stages:
        for model_ordinal in range(3):
            workload = _stage_workload(stage, model_ordinal)
            health_path, resource_path = _write_passing_stage_ledgers(
                tmp_path, policy=policy, stage=stage, workload=workload
            )
            stage_receipt = runtime_control.build_ramp_stage_receipt(
                policy,
                scope="disposable_preflight",
                worker_concurrency=stage,
                runtime_infra_file_sha256=infra_sha,
                blind_health_ledger_path=health_path,
                resource_ledger_path=resource_path,
                stage_workload=workload,
            )
            stage_path = tmp_path / f"stage-{stage}-model-{model_ordinal}.json"
            stage_path.write_text(json.dumps(stage_receipt), encoding="utf-8")
            stage_paths.append(stage_path)
    post_credential = runtime_control.build_credential_probe_receipt(
        policy,
        runtime_infra_file_sha256=infra_sha,
        http_status=200,
        key_limit_usd=1000.0,
        key_limit_remaining_usd=690.0,
        key_usage_usd=310.0,
        key_is_free_tier=False,
        key_is_management=False,
        key_is_provisioning=False,
        key_disabled=False,
        key_disabled_field_present=True,
        key_limit_reset_policy=None,
        key_expires_at=None,
        model_catalog_entries=_model_catalog(),
        credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-openrouter-key"
        ),
        management_audit_fingerprint_sha256=(
            runtime_control.openrouter_management_audit_fingerprint(
                "unit-test-management-key"
            )
        ),
        management_key_identity_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-management-key"
        ),
        management_key_is_management=True,
        management_key_is_provisioning=False,
        management_key_disabled=False,
        same_account_inventory_proof=_same_account_proof(
            tmp_path, limit=1000.0, remaining=690.0, usage=310.0
        ),
        account_total_credits_usd=1000.0,
        account_total_usage_usd=100.0,
        probe_phase="post_ramp",
    )
    post_credential_path = tmp_path / "post_credential_probe_receipt.json"
    post_credential_path.write_text(json.dumps(post_credential), encoding="utf-8")
    assert len(stage_paths) == 12
    assert post_credential["same_account_inventory_proof"][
        "default_workspace_unique_match_verified"
    ] is True


@pytest.mark.parametrize("outcome", ["fatal_error", "blocked"])
def test_exploratory_ramp_seals_non_request_worker_failure_as_threshold_breach(
    tmp_path: Path,
    outcome: str,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload())
    workload = _stage_workload(4)
    health_path, resource_path = _write_passing_stage_ledgers(
        tmp_path, policy=policy, stage=4, workload=workload
    )
    _replace_first_job_with_non_request_completion(
        health_path,
        policy=policy,
        workload=workload,
        outcome=outcome,
    )

    receipt = runtime_control.build_ramp_stage_receipt(
        policy,
        scope="exploratory_measurement",
        worker_concurrency=4,
        runtime_infra_file_sha256="b" * 64,
        blind_health_ledger_path=health_path,
        resource_ledger_path=resource_path,
        stage_workload=workload,
    )

    observed = receipt["observed"]
    assert receipt["schema_version"] == "agentdojo_openrouter_ramp_stage_receipt/v2"
    assert receipt["status"] == "measured_with_threshold_breach"
    assert receipt["resulting_safe_workers"] == 4
    assert observed["planned_jobs"] == 4
    assert observed["unique_completed_jobs"] == 4
    assert observed["worker_failures"] == 1
    assert observed["missing_successful_jobs"] == 1
    assert observed["unresolved_request_chains"] == 0
    assert observed["non_request_worker_failures"] == 1
    assert observed["unresolved_http_429_or_503"] == 1
    assert observed["http_429"] == 0
    assert observed["http_503"] == 0
    assert observed["provider_error_categories"] == {
        "http_429_openrouter_or_upstream_unspecified": 0,
        "http_503_service_origin_unspecified": 0,
        "transport_or_non_http": 1,
    }
    assert observed["thresholds_passed"] is False


def test_exploratory_ramp_rejects_success_completion_without_request(
    tmp_path: Path,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload())
    workload = _stage_workload(4)
    health_path, resource_path = _write_passing_stage_ledgers(
        tmp_path, policy=policy, stage=4, workload=workload
    )
    _replace_first_job_with_non_request_completion(
        health_path,
        policy=policy,
        workload=workload,
        outcome="success",
    )

    with pytest.raises(
        runtime_control.RuntimePolicyError,
        match="worker completion has no consistently bound request",
    ):
        runtime_control.build_ramp_stage_receipt(
            policy,
            scope="exploratory_measurement",
            worker_concurrency=4,
            runtime_infra_file_sha256="b" * 64,
            blind_health_ledger_path=health_path,
            resource_ledger_path=resource_path,
            stage_workload=workload,
        )


def test_finalized_validation_rejects_fatal_completion_without_request(
    tmp_path: Path,
) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(finalized=True))
    workload = _stage_workload(4)
    health_path, resource_path = _write_passing_stage_ledgers(
        tmp_path, policy=policy, stage=4, workload=workload
    )
    _replace_first_job_with_non_request_completion(
        health_path,
        policy=policy,
        workload=workload,
        outcome="fatal_error",
    )

    with pytest.raises(
        runtime_control.RuntimePolicyError,
        match="did not produce a successful real request for every planned job",
    ):
        runtime_control.build_ramp_stage_receipt(
            policy,
            scope="disposable_preflight",
            worker_concurrency=4,
            runtime_infra_file_sha256="b" * 64,
            blind_health_ledger_path=health_path,
            resource_ledger_path=resource_path,
            stage_workload=workload,
        )


def test_receipts_fail_closed_on_credential_or_ramp_failure(tmp_path: Path) -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload())
    with pytest.raises(runtime_control.RuntimeBudgetExceeded):
        runtime_control.build_credential_probe_receipt(
            policy,
            runtime_infra_file_sha256="b" * 64,
            http_status=200,
            key_limit_usd=1000.0,
            key_limit_remaining_usd=649.0,
            key_usage_usd=351.0,
            key_is_free_tier=False,
            key_is_management=False,
            key_is_provisioning=False,
            key_disabled=False,
            key_disabled_field_present=True,
            key_limit_reset_policy=None,
            key_expires_at=None,
            model_catalog_entries=_model_catalog(),
            credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
                "unit-test-openrouter-key"
            ),
            management_audit_fingerprint_sha256=(
                runtime_control.openrouter_management_audit_fingerprint(
                    "unit-test-management-key"
                )
            ),
            management_key_identity_sha256=(
                runtime_control.openrouter_key_fingerprint(
                    "unit-test-management-key"
                )
            ),
            management_key_is_management=True,
            management_key_is_provisioning=False,
            management_key_disabled=False,
            same_account_inventory_proof=_same_account_proof(
                tmp_path, limit=1000.0, remaining=649.0, usage=351.0
            ),
            account_total_credits_usd=1000.0,
            account_total_usage_usd=100.0,
        )
    workload = _stage_workload(4)
    health_path, resource_path = _write_passing_stage_ledgers(
        tmp_path, policy=policy, stage=4, workload=workload
    )
    first_job = workload["jobs"][0]  # type: ignore[index]
    runtime_control.BlindHealthLedger(
        (health_path,),
        policy_sha256=policy.semantic_sha256,
        session_id="session-ramp-stage-4-model-0",
        host_boot_id="12345678-1234-1234-1234-123456789abc",
        credential_fingerprint_sha256=(
            policy.execution_key_fingerprint_sha256
            or runtime_control.openrouter_key_fingerprint("unit-test-openrouter-key")
        ),
    ).record(
        event_type="request_attempt",
        outcome="fatal_error",
        http_status=503,
        attempt_index=3,
        max_attempts=3,
        reserved_tokens=100,
        job_identity_sha256=first_job["job_identity_sha256"],
        model_config_sha256=first_job["model_config_sha256"],
        request_chain_id="req-" + "f" * 32,
    )
    with pytest.raises(runtime_control.RuntimePolicyError, match="unresolved request"):
        runtime_control.build_ramp_stage_receipt(
            policy,
            scope="disposable_preflight",
            worker_concurrency=4,
            runtime_infra_file_sha256="b" * 64,
            blind_health_ledger_path=health_path,
            resource_ledger_path=resource_path,
            stage_workload=workload,
        )


def test_management_inventory_paginates_and_persists_only_page_digests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection = {
        "creator_user_id": "user-1",
        "label": "execution",
        "limit": 1000.0,
        "limit_remaining": 900.0,
        "limit_reset": None,
        "usage": 100.0,
        "expires_at": None,
    }
    first_page = [dict(projection, label=f"other-{index}") for index in range(100)]
    final_page = [projection]

    def fake_get(url: str, **_kwargs: object) -> tuple[int, dict[str, object]]:
        return 200, {"data": final_page if "offset=100" in url else first_page}

    monkeypatch.setattr(agentdojo_runtime_preflight, "_get_json", fake_get)
    rows, pages = agentdojo_runtime_preflight._management_key_inventory(
        management_api_key="local-only-management-key", timeout=30
    )
    assert [page["offset"] for page in pages] == [0, 100]
    proof = runtime_control.build_same_account_inventory_proof(
        execution_key_projection=projection,
        inventory_key_projections=rows,
        page_receipts=pages,
        auth_lifecycle_lock_path="/tmp/controller.lock",
    )
    encoded = json.dumps(proof, sort_keys=True)
    assert proof["unique_match_count"] == 1
    assert '"label": "execution"' not in encoded
    assert "other-" not in encoded
    assert "provider_or_raw_key_hash_comparison_used" in encoded


def test_management_inventory_rejects_repeated_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {
        "creator_user_id": "user-1",
        "label": "same",
        "limit": None,
        "limit_remaining": None,
        "limit_reset": None,
        "usage": 0.0,
        "expires_at": None,
    }
    monkeypatch.setattr(
        agentdojo_runtime_preflight,
        "_get_json",
        lambda *_args, **_kwargs: (200, {"data": [row] * 100}),
    )
    with pytest.raises(runtime_control.RuntimePolicyError, match="repeated"):
        agentdojo_runtime_preflight._management_key_inventory(
            management_api_key="local-only-management-key", timeout=30
        )


def test_execution_key_only_probe_preserves_provider_unlimited_nulls(
    tmp_path: Path,
) -> None:
    funding = agentdojo_runtime_preflight._key_funding(
        {
            "data": {
                "limit": None,
                "limit_remaining": None,
                "usage": 12.5,
            }
        }
    )
    assert funding == {
        "limit": None,
        "limit_remaining": None,
        "usage": 12.5,
        "provider_limit_mode": "unlimited_no_provider_cap",
    }
    policy = runtime_control.load_runtime_policy(_policy_payload(finalized=True))
    receipt = runtime_control.build_credential_probe_receipt(
        policy,
        runtime_infra_file_sha256="b" * 64,
        http_status=200,
        key_limit_usd=None,
        key_limit_remaining_usd=None,
        key_usage_usd=12.5,
        provider_limit_mode="unlimited_no_provider_cap",
        key_is_free_tier=False,
        key_is_management=False,
        key_is_provisioning=False,
        key_disabled=False,
        key_disabled_field_present=True,
        key_limit_reset_policy=None,
        key_expires_at=None,
        model_catalog_entries=_model_catalog(),
        credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-unlimited-execution-key"
        ),
        management_audit_status="waived_by_user",
        probe_phase="post_ramp",
    )
    path = tmp_path / "unlimited-credential.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    loaded = runtime_control.load_credential_probe_receipt(
        path,
        expected_policy_sha256=policy.semantic_sha256,
        expected_runtime_infra_file_sha256="b" * 64,
        expected_probe_phase="post_ramp",
    )
    assert loaded["key_limit_usd"] is None
    assert loaded["key_limit_remaining_usd"] is None
    assert loaded["credit_floor_proof_status"] == (
        "waived_by_user_provider_balance_unavailable"
    )
    assert loaded["local_software_run_cost_cap_usd"] == 650.0


def test_model_catalog_uses_conservative_price_tier_envelope() -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(finalized=True))
    catalog = _model_catalog()
    catalog[0]["pricing"]["overrides"] = [
        {
            "min_prompt_tokens": 272_000,
            "prompt": "0.000005",
            "completion": "0.0000225",
            "input_cache_read": "0.0000005",
        }
    ]
    receipt = runtime_control.build_credential_probe_receipt(
        policy,
        runtime_infra_file_sha256="b" * 64,
        http_status=200,
        key_limit_usd=None,
        key_limit_remaining_usd=None,
        key_usage_usd=0.0,
        provider_limit_mode="unlimited_no_provider_cap",
        key_is_free_tier=False,
        key_is_management=False,
        key_is_provisioning=False,
        key_disabled=False,
        key_disabled_field_present=True,
        key_limit_reset_policy=None,
        key_expires_at=None,
        model_catalog_entries=catalog,
        credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-unlimited-execution-key"
        ),
        management_audit_status="waived_by_user",
        probe_phase="post_ramp",
    )
    normalized = receipt["model_catalog"][0]["pricing"]
    assert normalized["prompt"] == 0.000005
    assert normalized["completion"] == 0.0000225
    assert normalized["input_cache_read"] == 0.0000005


def test_model_catalog_canary_binds_parameters_not_declared_by_provider() -> None:
    policy = runtime_control.load_runtime_policy(_policy_payload(finalized=True))
    catalog = _model_catalog()
    catalog[0]["supported_parameters"] = ["max_tokens", "seed", "tools"]
    receipt = runtime_control.build_credential_probe_receipt(
        policy,
        runtime_infra_file_sha256="b" * 64,
        http_status=200,
        key_limit_usd=None,
        key_limit_remaining_usd=None,
        key_usage_usd=0.0,
        provider_limit_mode="unlimited_no_provider_cap",
        key_is_free_tier=False,
        key_is_management=False,
        key_is_provisioning=False,
        key_disabled=False,
        key_disabled_field_present=True,
        key_limit_reset_policy=None,
        key_expires_at=None,
        model_catalog_entries=catalog,
        credential_fingerprint_sha256=runtime_control.openrouter_key_fingerprint(
            "unit-test-unlimited-execution-key"
        ),
        management_audit_status="waived_by_user",
        probe_phase="post_ramp",
    )
    support = receipt["model_catalog"][0]["request_semantics_support"]
    assert support["temperature"] == "requires_successful_real_request_canary"
    assert support["top_p"] == "requires_successful_real_request_canary"


def test_key_funding_rejects_half_null_provider_limit() -> None:
    with pytest.raises(
        runtime_control.RuntimePolicyError,
        match="both be numeric or both null",
    ):
        agentdojo_runtime_preflight._key_funding(
            {"data": {"limit": None, "limit_remaining": 10, "usage": 0}}
        )


def test_execution_runtime_snapshot_binds_case_packet_direct_imports() -> None:
    files = runtime_control.execution_runtime_snapshot()["files"]
    assert "src/evidence_system/contracts/case_packets.py" in files
    assert "src/evidence_system/contracts/appworld_checklist_semantics.py" in files
    assert "src/evidence_system/contracts/appworld_stronger_gaps.py" in files
