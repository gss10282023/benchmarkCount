"""Thin AgentDojo smoke worker with a local OpenAI-compatible OpenRouter proxy."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
from importlib.metadata import PackageNotFoundError, version as distribution_version
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import stat
import threading
import time
import traceback
from typing import Any, Mapping
import urllib.error
import urllib.request
import uuid

from evidence_system.adapters.agentdojo_runtime_control import (
    AGENTDOJO_LOCAL_LLM_SEED_POLICY,
    AGENTDOJO_LOCAL_LLM_SEED_POLICY_SHA256,
    AGENTDOJO_LOCAL_LLM_TOP_P,
    AGENTDOJO_PROXY_REQUEST_TRANSFORM_SHA256,
    BlindHealthLedger,
    GlobalRateLimiter,
    RuntimeBudgetExceeded,
    RuntimePolicy,
    RuntimePolicyError,
    SealedIncidentLedger,
    agentdojo_model_config_sha256,
    estimate_request_tokens,
    job_identity_sha256,
    linux_host_boot_id,
    load_runtime_policy,
    openrouter_key_fingerprint,
    resource_worker_process_binding_sha256,
    retry_after_seconds,
    retry_delay_seconds,
)
from evidence_system.adapters.runtime import (
    FORMAL_JOB_LAUNCH_MARKER,
    FORMAL_JOB_STARTED_MARKER,
    FORMAL_JOB_WORKER_SUCCESS_MARKER,
    formal_job_binding_sha256,
)
from evidence_system.contracts.agentdojo_execution_namespace import (
    FormalStageAuthorization,
    assert_formal_stage_authorization_current as _shared_assert_formal_stage_authorization_current,
    verify_formal_stage_authorization as _shared_verify_formal_stage_authorization,
)
from evidence_system.core.hashing import sha256_object


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
FORMAL_SEALED_STREAM_FILES = (
    "sealed_worker.stderr.log",
    "sealed_worker.stdout.log",
)
FORMAL_SUPERVISOR_PRESTART_FILES = (
    "formal_supervisor_claim.json",
    "formal_supervisor_spec.json",
    "formal_supervisor_state.json",
)


class _OpenRouterResponseContractError(RuntimePolicyError):
    """Typed HTTP-200 provider response-contract failure."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass(frozen=True)
class AgentDojoSmokeConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    suite: str
    user_task: str
    injection_task: str
    agentdojo_package_version: str
    agentdojo_git_commit: str
    agentdojo_git_tree: str
    agentdojo_source_lock: dict[str, Any]
    benchmark_version: str
    model_id: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    openrouter_api_key_env: str
    secret_env_path: Path | None
    tool_delimiter: str
    tool_output_format: str
    system_message_name: str | None
    system_message_sha256: str
    defense: str | None
    attack: str
    openrouter_runtime_policy: dict[str, Any]
    openrouter_runtime_policy_sha256: str
    openrouter_runtime_policy_file_sha256: str
    runtime_state_dir: Path | None
    blind_aggregate_root: Path | None
    blind_group: str | None
    stage_authorization_path: Path | None
    stage_authorization_sha256: str
    resource_stage_token: str
    disposable_blind_health_path: Path | None = None


@dataclass(frozen=True)
class OpenRouterRuntimeControl:
    policy: RuntimePolicy
    limiter: GlobalRateLimiter
    ledger: BlindHealthLedger
    sealed_incidents: SealedIncidentLedger
    job: Mapping[str, Any]
    job_identity_sha256: str
    model_config_sha256: str
    credential_fingerprint_sha256: str
    formal_stage_authorization: FormalStageAuthorization | None = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", default="{}")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--user-task", required=True)
    parser.add_argument("--injection-task", required=True)
    parser.add_argument("--agentdojo-package-version", default="0.1.35")
    parser.add_argument(
        "--agentdojo-git-commit",
        default="a75aba7631d3ca5fb7ab938965c97ead2f9ff84b",
    )
    parser.add_argument(
        "--agentdojo-git-tree",
        default="3c74b60f2bad4ff321d864e0c0483f256cc8f8d2",
    )
    parser.add_argument("--agentdojo-source-lock-json", default="{}")
    parser.add_argument("--benchmark-version", default="v1.2.2")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--secret-env-path", type=_optional_path, default=None)
    parser.add_argument("--tool-delimiter", default="tool")
    parser.add_argument("--tool-output-format", choices=("yaml", "json"), default="yaml")
    parser.add_argument("--system-message-name", type=_optional_string, default=None)
    parser.add_argument(
        "--system-message-sha256",
        default="a021a92b114c523250d0e52b18adc0aa7b41db7c7628b579b2b8db1df9361837",
    )
    parser.add_argument("--defense", type=_optional_string, default=None)
    parser.add_argument("--attack", default="direct")
    parser.add_argument("--openrouter-runtime-policy-json", default="{}")
    parser.add_argument("--openrouter-runtime-policy-sha256", default="")
    parser.add_argument("--openrouter-runtime-policy-file-sha256", default="")
    parser.add_argument("--runtime-state-dir", type=_optional_path, default=None)
    parser.add_argument("--blind-aggregate-root", type=_optional_path, default=None)
    parser.add_argument("--blind-group", type=_optional_string, default=None)
    parser.add_argument("--stage-authorization", type=_optional_path, default=None)
    parser.add_argument("--stage-authorization-sha256", default="")
    parser.add_argument("--resource-stage-token", default="")
    parser.add_argument(
        "--disposable-blind-health-path", type=_optional_path, default=None
    )
    args = parser.parse_args(argv)
    config = AgentDojoSmokeConfig(
        job=_loads_json_object(args.job_json),
        source_entry=_loads_json_object(args.source_entry_json),
        output_dir=Path(args.output_dir),
        suite=args.suite,
        user_task=args.user_task,
        injection_task=args.injection_task,
        agentdojo_package_version=args.agentdojo_package_version,
        agentdojo_git_commit=args.agentdojo_git_commit,
        agentdojo_git_tree=args.agentdojo_git_tree,
        agentdojo_source_lock=_loads_json_object(args.agentdojo_source_lock_json),
        benchmark_version=args.benchmark_version,
        model_id=args.model_id,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
        retry=args.retry,
        openrouter_api_key_env=args.openrouter_api_key_env,
        secret_env_path=args.secret_env_path,
        tool_delimiter=args.tool_delimiter,
        tool_output_format=args.tool_output_format,
        system_message_name=args.system_message_name,
        system_message_sha256=args.system_message_sha256,
        defense=args.defense,
        attack=args.attack,
        openrouter_runtime_policy=_loads_json_object(args.openrouter_runtime_policy_json),
        openrouter_runtime_policy_sha256=args.openrouter_runtime_policy_sha256,
        openrouter_runtime_policy_file_sha256=args.openrouter_runtime_policy_file_sha256,
        runtime_state_dir=args.runtime_state_dir,
        blind_aggregate_root=args.blind_aggregate_root,
        blind_group=args.blind_group,
        stage_authorization_path=args.stage_authorization,
        stage_authorization_sha256=args.stage_authorization_sha256,
        resource_stage_token=args.resource_stage_token,
        disposable_blind_health_path=args.disposable_blind_health_path,
    )
    try:
        summary = run_smoke_job(config)
    except Exception as exc:  # pragma: no cover - exercised by remote runs.
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 1
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if summary.get("status") != "error" else 1


def run_smoke_job(config: AgentDojoSmokeConfig) -> dict[str, Any]:
    config = _normalize_config(config)
    seed_verification = _apply_and_verify_locked_job_seed(config.job)
    formal_job = _is_formal_job(config.job)
    if formal_job and os.environ.get("PYTHONHASHSEED") != str(config.job["seed"]):
        raise RuntimeError(
            "formal worker PYTHONHASHSEED differs from the locked job seed"
        )
    formal_authorization: FormalStageAuthorization | None = None
    if formal_job:
        formal_authorization = _verify_formal_stage_authorization(config)
        _prepare_formal_worker_directory(config, formal_authorization)
    else:
        if config.output_dir.exists():
            shutil.rmtree(config.output_dir)
        config.output_dir.mkdir(parents=True, exist_ok=True)
    proxy_calls_dir = config.output_dir / "proxy_calls"
    proxy_calls_dir.mkdir(parents=True, exist_ok=True)
    _write_json(config.output_dir / "job.json", config.job)
    _write_json(config.output_dir / "source_bundle_entry.json", config.source_entry)
    _write_json(config.output_dir / "worker_config.json", _jsonable(asdict(config)))
    _write_json(config.output_dir / "seed_verification.json", seed_verification)
    install_verification = _verify_agentdojo_install(config)
    _write_json(config.output_dir / "install_verification.json", install_verification)

    strict_secret_job = formal_job or str(
        config.job.get("runtime_scope") or ""
    ) == "disposable_preflight"
    if strict_secret_job:
        if config.secret_env_path is None:
            raise RuntimeError(
                "locked AgentDojo execution requires secret_env_path"
            )
        api_key = _load_strict_secret_env_value(
            config.secret_env_path, key=config.openrouter_api_key_env
        )
    else:
        api_key = os.environ.get(config.openrouter_api_key_env)
    if not api_key:
        raise RuntimeError(f"missing environment variable {config.openrouter_api_key_env}")
    runtime_control = _build_runtime_control(
        config,
        api_key=api_key,
        formal_stage_authorization=formal_authorization,
    )
    if runtime_control is not None:
        _write_json(
            config.output_dir / "runtime_policy_verification.json",
            {
                "schema_version": "agentdojo_openrouter_runtime_policy_verification/v1",
                "policy_id": runtime_control.policy.policy_id,
                "openrouter_runtime_policy_sha256": runtime_control.policy.semantic_sha256,
                "openrouter_runtime_policy_file_sha256": config.openrouter_runtime_policy_file_sha256,
                "execution_lock_sha256": str(
                    config.job.get("execution_lock_sha256") or ""
                ),
                "execution_policy_sha256": str(
                    config.job.get("execution_policy_sha256") or ""
                ),
                "state_database_name": runtime_control.limiter.database_path.name,
                "limiter_clock_basis": runtime_control.limiter.clock_basis,
                "host_boot_id": runtime_control.limiter.host_boot_id,
                "seed_policy_sha256": AGENTDOJO_LOCAL_LLM_SEED_POLICY_SHA256,
                "proxy_request_transform_sha256": (
                    AGENTDOJO_PROXY_REQUEST_TRANSFORM_SHA256
                ),
                "policy": runtime_control.policy.raw,
            },
        )

    proxy = OpenRouterProxyServer(
        host="127.0.0.1",
        # Bind directly to port zero.  A separate probe-then-close socket has
        # a TOCTOU race when 32 workers start together.
        port=0,
        api_key=api_key,
        model_id=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
        retry=config.retry,
        log_dir=proxy_calls_dir,
        runtime_control=runtime_control,
    )
    os.environ["LOCAL_LLM_PORT"] = str(proxy.port)
    proxy.start()
    try:
        try:
            summary = _run_agentdojo_benchmark(config)
            error_calls = _proxy_error_calls(proxy_calls_dir)
            if error_calls:
                first = error_calls[0]
                raise RuntimeError(
                    f"OpenRouter proxy recorded {len(error_calls)} failed LLM call(s); "
                    f"first={first['path']}: {first['error_message']}"
                )
        except Exception as exc:
            if runtime_control is not None:
                _record_worker_incident(runtime_control, exc)
            summary = {
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            _write_json(config.output_dir / "run_summary.json", summary)
            raise
    finally:
        proxy.stop()
    if runtime_control is not None:
        runtime_control.ledger.record(
            event_type="worker_completion",
            outcome="success",
            job_identity_sha256=runtime_control.job_identity_sha256,
            model_config_sha256=runtime_control.model_config_sha256,
        )
    _write_json(config.output_dir / "run_summary.json", summary)
    if formal_job:
        if formal_authorization is None:  # pragma: no cover - defensive invariant
            raise RuntimeError("formal stage authorization was not loaded")
        _assert_formal_stage_authorization_current(
            formal_authorization,
            job=config.job,
            policy=runtime_control.policy,
            model_config_sha256=runtime_control.model_config_sha256,
        )
        _write_json_exclusive(
            config.output_dir / FORMAL_JOB_WORKER_SUCCESS_MARKER,
            {
                "schema_version": "agentdojo_formal_worker_success/v1",
                "finished_at": _utc_now_iso(),
                **_formal_marker_binding(config.job),
                "stage_authorization_sha256": formal_authorization.file_sha256,
                "formal_stage_id": str(formal_authorization.payload["stage_id"]),
                "formal_stage_session_id": str(
                    formal_authorization.payload["session_id"]
                ),
                "expected_episode_count": 3,
                "worker_status": "completed",
            },
        )
    return summary


def _run_agentdojo_benchmark(config: AgentDojoSmokeConfig) -> dict[str, Any]:
    from agentdojo.agent_pipeline.agent_pipeline import AgentPipeline, PipelineConfig, load_system_message
    from agentdojo.attacks.attack_registry import load_attack
    from agentdojo.benchmark import run_task_with_injection_tasks, run_task_without_injection_tasks
    from agentdojo.logging import OutputLogger
    from agentdojo.models import ModelsEnum
    from agentdojo.task_suite.load_suites import get_suite

    system_message = load_system_message(config.system_message_name)
    actual_system_message_sha256 = hashlib.sha256(system_message.encode("utf-8")).hexdigest()
    if actual_system_message_sha256 != config.system_message_sha256:
        raise RuntimeError(
            "AgentDojo system message hash mismatch: "
            f"expected={config.system_message_sha256} actual={actual_system_message_sha256}"
        )
    suite = get_suite(config.benchmark_version, config.suite)
    pipeline = AgentPipeline.from_config(
        PipelineConfig(
            llm=ModelsEnum.LOCAL,
            model_id=config.model_id,
            defense=config.defense,
            tool_delimiter=config.tool_delimiter,
            system_message_name=config.system_message_name,
            system_message=None,
            tool_output_format=config.tool_output_format,
        )
    )
    attack = load_attack(config.attack, suite, pipeline)
    logdir = config.output_dir / "trace_logs"

    user_task = suite.get_user_task_by_id(config.user_task)
    injection_task = suite.get_injection_task_by_id(config.injection_task)
    with OutputLogger(logdir=str(logdir)):
        benign_utility, benign_security = run_task_without_injection_tasks(
            suite,
            pipeline,
            user_task,
            logdir=logdir,
            force_rerun=True,
            benchmark_version=config.benchmark_version,
        )
        injection_task_utility, injection_task_security = run_task_without_injection_tasks(
            suite,
            pipeline,
            injection_task,
            logdir=logdir,
            force_rerun=True,
            benchmark_version=config.benchmark_version,
        )
        utility_results, security_results = run_task_with_injection_tasks(
            suite,
            pipeline,
            user_task,
            attack,
            logdir=logdir,
            force_rerun=True,
            injection_tasks=[config.injection_task],
            benchmark_version=config.benchmark_version,
        )
    injected_key = (config.user_task, config.injection_task)
    injected_utility = bool(utility_results[injected_key])
    injected_security = bool(security_results[injected_key])

    native_output = {
        "schema_version": "agentdojo_native_evaluator_output/v1",
        "suite_name": config.suite,
        "user_task_id": config.user_task,
        "injection_task_id": config.injection_task,
        "agentdojo_package_version": config.agentdojo_package_version,
        "attack_name": config.attack,
        "defense_name": config.defense,
        "benchmark_version": config.benchmark_version,
        "pipeline_config": {
            "llm": "LOCAL",
            "model_id": config.model_id,
            "tool_delimiter": config.tool_delimiter,
            "tool_output_format": config.tool_output_format,
            "system_message_name": config.system_message_name,
            "system_message_sha256": actual_system_message_sha256,
        },
        "benign": {
            "utility": bool(benign_utility),
            "security": bool(benign_security),
        },
        "injection_task_as_user_task": {
            "utility": bool(injection_task_utility),
            "security": bool(injection_task_security),
        },
        "injected": {
            "utility": injected_utility,
            "security": injected_security,
        },
    }
    _write_json(config.output_dir / "native_evaluator_output.json", native_output)
    _write_json(
        config.output_dir / "native_evaluator_input.json",
        {
            "schema_version": "agentdojo_native_evaluator_input/v1",
            "suite_name": config.suite,
            "user_task_id": config.user_task,
            "injection_task_id": config.injection_task,
            "agentdojo_package_version": config.agentdojo_package_version,
            "attack_name": config.attack,
            "defense_name": config.defense,
            "tool_delimiter": config.tool_delimiter,
            "tool_output_format": config.tool_output_format,
            "system_message_sha256": actual_system_message_sha256,
            "source_entry": config.source_entry,
        },
    )
    return {
        "status": "completed",
        "suite_name": config.suite,
        "user_task_id": config.user_task,
        "injection_task_id": config.injection_task,
        "agentdojo_package_version": config.agentdojo_package_version,
        "attack_name": config.attack,
        "defense_name": config.defense,
        "tool_delimiter": config.tool_delimiter,
        "tool_output_format": config.tool_output_format,
        "system_message_sha256": actual_system_message_sha256,
        "benign_utility": bool(benign_utility),
        "injection_task_utility": bool(injection_task_utility),
        "injected_utility": injected_utility,
        "injected_security": injected_security,
    }


class OpenRouterProxyServer:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        api_key: str,
        model_id: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: int,
        retry: int,
        log_dir: Path,
        runtime_control: OpenRouterRuntimeControl | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.api_key = api_key
        self.model_id = model_id
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout_seconds = timeout_seconds
        self.retry = retry
        self.log_dir = log_dir
        self.runtime_control = runtime_control
        self._counter = 0
        handler = self._build_handler()
        self.server = ThreadingHTTPServer((host, port), handler)
        self.port = int(self.server.server_address[1])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _build_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover - noisy stdlib hook
                return

            def do_GET(self) -> None:
                if self.path.rstrip("/") != "/v1/models":
                    self.send_error(404)
                    return
                payload = {
                    "object": "list",
                    "data": [
                        {
                            "id": outer.model_id,
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "openrouter-proxy",
                        }
                    ],
                }
                self._send_json(200, payload)

            def do_POST(self) -> None:
                if self.path.rstrip("/") != "/v1/chat/completions":
                    self.send_error(404)
                    return
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length)
                request_payload = json.loads(raw_body.decode("utf-8"))
                forwarded = _transform_agentdojo_local_request(
                    request_payload,
                    model_id=outer.model_id,
                    temperature=outer.temperature,
                    max_tokens=outer.max_tokens,
                )
                request_at = _utc_now_iso()
                response_payload = None
                error_message = None
                try:
                    response_payload = _request_openrouter(
                        api_key=outer.api_key,
                        payload=forwarded,
                        timeout_seconds=outer.timeout_seconds,
                        retry=outer.retry,
                        runtime_control=outer.runtime_control,
                    )
                except Exception as exc:  # pragma: no cover - remote-only path
                    error_message = str(exc)
                    self._send_json(500, {"error": {"message": error_message}})
                else:
                    self._send_json(200, response_payload)
                finally:
                    outer._counter += 1
                    response_at = _utc_now_iso()
                    _write_json(
                        outer.log_dir / f"{outer._counter:04d}.json",
                        {
                            "call_id": f"agentdojo-proxy-{outer._counter:04d}",
                            "request_timestamp": request_at,
                            "response_timestamp": response_at,
                            "request_payload": request_payload,
                            "forwarded_payload": forwarded,
                            "response_payload": response_payload,
                            "error_message": error_message,
                        },
                    )

            def _send_json(self, status_code: int, payload: Mapping[str, Any]) -> None:
                encoded = json.dumps(payload, ensure_ascii=True).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return Handler


def _request_openrouter(
    *,
    api_key: str,
    payload: Mapping[str, Any],
    timeout_seconds: int,
    retry: int,
    runtime_control: OpenRouterRuntimeControl | None = None,
) -> dict[str, Any]:
    body = json.dumps(
        dict(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error: Exception | None = None
    retry_policy = runtime_control.policy.retry if runtime_control is not None else None
    max_attempts = retry_policy.max_attempts if retry_policy is not None else retry + 1
    reserved_tokens = (
        estimate_request_tokens(payload, runtime_control.policy)
        if runtime_control is not None
        else 0
    )
    request_chain_id = f"req-{uuid.uuid4().hex}"
    for attempt_index in range(1, max_attempts + 1):
        loaded: Any = None
        attempt_error: Exception | None = None
        lease = None
        if runtime_control is not None:
            def assert_current() -> None:
                if runtime_control.formal_stage_authorization is None:
                    return
                _assert_formal_stage_authorization_current(
                    runtime_control.formal_stage_authorization,
                    job=runtime_control.job,
                    policy=runtime_control.policy,
                    model_config_sha256=runtime_control.model_config_sha256,
                )
            assert_current()
            try:
                lease = runtime_control.limiter.acquire(
                    reserved_tokens=reserved_tokens,
                    model_id=str(payload.get("model") or ""),
                    currentness_check=assert_current,
                )
            except RuntimeBudgetExceeded:
                incident_id = f"inc-{uuid.uuid4().hex}"
                runtime_control.sealed_incidents.record(
                    incident_id=incident_id,
                    job=runtime_control.job,
                    error_category="budget",
                    error_origin="controller",
                    attempt_index=attempt_index,
                )
                runtime_control.ledger.record(
                    event_type="incident",
                    outcome="blocked",
                    attempt_index=attempt_index,
                    max_attempts=max_attempts,
                    incident_id=incident_id,
                    job_identity_sha256=runtime_control.job_identity_sha256,
                    model_config_sha256=runtime_control.model_config_sha256,
                    request_chain_id=request_chain_id,
                )
                raise
            try:
                # A waiter can acquire only after an earlier request releases
                # capacity; re-check at the final HTTP boundary so a closed
                # stage never turns that admission into network traffic.
                assert_current()
            except BaseException:
                lease.cancel()
                raise
        started = time.monotonic()
        retry_after = None
        http_status: int | None = None
        actual_tokens: int | None = None
        actual_cost_usd: float | None = None
        returned_model_identity_sha256: str | None = None
        retryable = False
        request = urllib.request.Request(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                # urllib exposes successful HTTP responses without raising.  Keep
                # the 200 boundary in the blind ledger even when JSON decoding or
                # the response-contract validation below fails.
                http_status = int(getattr(response, "status", 200))
                loaded = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            http_status = int(exc.code)
            error_body = exc.read().decode("utf-8", errors="replace")
            attempt_error = RuntimeError(f"OpenRouter HTTP {exc.code}: {error_body[:500]}")
            last_error = attempt_error
            if retry_policy is not None:
                retry_after = retry_after_seconds(
                    exc.headers.get("Retry-After") if exc.headers is not None else None,
                    maximum_seconds=retry_policy.max_retry_after_seconds,
                )
                retryable = http_status in retry_policy.retryable_http_statuses
            else:
                retryable = True
        except urllib.error.URLError as exc:
            attempt_error = RuntimeError(f"OpenRouter transport error: {exc.reason}")
            last_error = attempt_error
            retryable = retry_policy is None or retry_policy.retry_transport_errors
        except (TimeoutError, OSError) as exc:
            attempt_error = RuntimeError(f"OpenRouter transport error: {type(exc).__name__}")
            last_error = attempt_error
            retryable = retry_policy is None or retry_policy.retry_transport_errors
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            attempt_error = RuntimeError(f"OpenRouter invalid JSON response: {type(exc).__name__}")
            last_error = attempt_error
            retryable = retry_policy is None or retry_policy.retry_invalid_json
        else:
            if not isinstance(loaded, dict):
                attempt_error = RuntimeError("OpenRouter response must be a JSON object")
                last_error = attempt_error
                retryable = retry_policy is None or retry_policy.retry_invalid_json
            else:
                try:
                    (
                        actual_tokens,
                        actual_cost_usd,
                        returned_model_identity_sha256,
                    ) = _validated_response_usage_and_model(
                        loaded,
                        requested_model_id=str(payload.get("model") or ""),
                    )
                except _OpenRouterResponseContractError as exc:
                    attempt_error = exc
                    last_error = exc
                    retryable = bool(
                        exc.retryable
                        and (
                            retry_policy is None
                            or retry_policy.retry_invalid_json
                        )
                    )
                except RuntimePolicyError as exc:
                    attempt_error = exc
                    last_error = exc
                    retryable = False
        latency = max(0.0, time.monotonic() - started)
        released_snapshot = None
        if lease is not None:
            released_snapshot = lease.release(
                actual_tokens=actual_tokens,
                actual_cost_usd=actual_cost_usd,
            )
        if isinstance(loaded, dict) and attempt_error is None:
            if runtime_control is not None and lease is not None and released_snapshot is not None:
                runtime_control.ledger.record(
                    event_type="request_attempt",
                    outcome="success",
                    http_status=200,
                    attempt_index=attempt_index,
                    max_attempts=max_attempts,
                    latency_seconds=round(latency, 6),
                    limiter_wait_seconds=round(lease.waited_seconds, 6),
                    reserved_tokens=reserved_tokens,
                    actual_total_tokens=actual_tokens,
                    actual_cost_usd=actual_cost_usd,
                    reserved_cost_usd=lease.reserved_cost_usd,
                    cumulative_cost_usd=round(released_snapshot.cumulative_cost_usd, 8),
                    pending_reserved_cost_usd=round(
                        released_snapshot.pending_reserved_cost_usd, 8
                    ),
                    # Concurrency must be measured at admission.  The release
                    # snapshot is necessarily lower and cannot prove that a
                    # 4/8/16/32 stage actually reached its requested load.
                    active_requests=lease.snapshot.active_requests,
                    requests_in_window=released_snapshot.requests_in_window,
                    tokens_in_window=released_snapshot.tokens_in_window,
                    model_active_requests=lease.snapshot.model_active_requests,
                    model_requests_in_window=released_snapshot.model_requests_in_window,
                    model_tokens_in_window=released_snapshot.model_tokens_in_window,
                    job_identity_sha256=runtime_control.job_identity_sha256,
                    model_config_sha256=runtime_control.model_config_sha256,
                    request_chain_id=request_chain_id,
                    returned_model_identity_sha256=(
                        returned_model_identity_sha256
                    ),
                    **_request_semantics_health_fields(payload),
                )
            return loaded
        can_retry = retryable and attempt_index < max_attempts
        delay = 0.0
        if can_retry:
            delay = (
                retry_delay_seconds(
                    retry_policy,
                    attempt_index=attempt_index,
                    retry_after=retry_after,
                )
                if retry_policy is not None
                else min(float(attempt_index), 3.0)
            )
        if runtime_control is not None and lease is not None and released_snapshot is not None:
            incident_id = f"inc-{uuid.uuid4().hex}"
            error_category, error_origin = _classify_runtime_incident(
                http_status=http_status,
                error=attempt_error,
            )
            runtime_control.sealed_incidents.record(
                incident_id=incident_id,
                job=runtime_control.job,
                error_category=error_category,
                error_origin=error_origin,
                http_status=http_status,
                attempt_index=attempt_index,
            )
            runtime_control.ledger.record(
                event_type="request_attempt",
                outcome="retryable_error" if can_retry else "fatal_error",
                http_status=http_status,
                attempt_index=attempt_index,
                max_attempts=max_attempts,
                retry_after_seconds=retry_after,
                retry_delay_seconds=round(delay, 6),
                latency_seconds=round(latency, 6),
                limiter_wait_seconds=round(lease.waited_seconds, 6),
                reserved_tokens=reserved_tokens,
                actual_total_tokens=actual_tokens,
                actual_cost_usd=actual_cost_usd,
                reserved_cost_usd=lease.reserved_cost_usd,
                cumulative_cost_usd=round(released_snapshot.cumulative_cost_usd, 8),
                pending_reserved_cost_usd=round(
                    released_snapshot.pending_reserved_cost_usd, 8
                ),
                active_requests=lease.snapshot.active_requests,
                requests_in_window=released_snapshot.requests_in_window,
                tokens_in_window=released_snapshot.tokens_in_window,
                model_active_requests=lease.snapshot.model_active_requests,
                model_requests_in_window=released_snapshot.model_requests_in_window,
                model_tokens_in_window=released_snapshot.model_tokens_in_window,
                incident_id=incident_id,
                job_identity_sha256=runtime_control.job_identity_sha256,
                model_config_sha256=runtime_control.model_config_sha256,
                request_chain_id=request_chain_id,
                **_request_semantics_health_fields(payload),
            )
        if not can_retry:
            break
        time.sleep(delay)
    raise last_error or RuntimeError("OpenRouter request failed")


def _request_semantics_health_fields(payload: Mapping[str, Any]) -> dict[str, int]:
    """Evidence-free proof of the exact parameter surface sent upstream."""

    return {
        "temperature_parameter_present": int(
            isinstance(payload.get("temperature"), (int, float))
            and not isinstance(payload.get("temperature"), bool)
        ),
        "top_p_parameter_present": int(
            isinstance(payload.get("top_p"), (int, float))
            and not isinstance(payload.get("top_p"), bool)
        ),
        "max_tokens_parameter_present": int(
            isinstance(payload.get("max_tokens"), int)
            and not isinstance(payload.get("max_tokens"), bool)
            and int(payload["max_tokens"]) > 0
        ),
        "seed_parameter_present": int(
            isinstance(payload.get("seed"), int)
            and not isinstance(payload.get("seed"), bool)
        ),
        "native_tools_parameter_absent": int("tools" not in payload),
        "native_tool_choice_parameter_absent": int("tool_choice" not in payload),
    }


def _loads_json_object(value: str) -> dict[str, Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError("expected a JSON object")
    return loaded


def _normalize_chat_messages(messages: Any) -> list[dict[str, str]]:
    if not isinstance(messages, list):
        return [{"role": "user", "content": _message_content_to_text(messages)}]

    normalized: list[dict[str, str]] = []
    for item in messages:
        if not isinstance(item, Mapping):
            role = "user"
            content = _message_content_to_text(item)
            prefix = ""
        else:
            source_role = str(item.get("role") or "user")
            content = _message_content_to_text(item.get("content"))
            prefix = ""
            if source_role in {"tool", "function"}:
                role = "user"
                name = item.get("name")
                label = "Tool result" if source_role == "tool" else "Function result"
                prefix = f"{label} ({name}):\n" if name else f"{label}:\n"
            elif source_role in {"system", "user", "assistant"}:
                role = source_role
                if not content and item.get("tool_calls"):
                    content = _message_content_to_text(item.get("tool_calls"))
            else:
                role = "user"
                prefix = f"{source_role} message:\n"

        content = f"{prefix}{content}".strip()
        if not content:
            continue
        if normalized and normalized[-1]["role"] == role:
            normalized[-1]["content"] = f"{normalized[-1]['content']}\n\n{content}"
        else:
            normalized.append({"role": role, "content": content})
    return normalized or [{"role": "user", "content": ""}]


def _message_content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, Mapping):
                if isinstance(item.get("text"), str):
                    parts.append(str(item["text"]))
                elif isinstance(item.get("content"), str):
                    parts.append(str(item["content"]))
                else:
                    parts.append(json.dumps(_jsonable(item), ensure_ascii=True, sort_keys=True))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return json.dumps(_jsonable(content), ensure_ascii=True, sort_keys=True)


def _normalize_config(config: AgentDojoSmokeConfig) -> AgentDojoSmokeConfig:
    model_id = config.model_id.removeprefix("openrouter/")
    if model_id == config.model_id:
        return config
    payload = asdict(config)
    payload["model_id"] = model_id
    return AgentDojoSmokeConfig(**payload)


_STRICT_SECRET_ENV_LINE = re.compile(r"^([A-Z][A-Z0-9_]*)=([!-~]+)$")


def _load_strict_secret_env_value(path: Path, *, key: str) -> str:
    """Read one literal ASCII KEY=VALUE line without invoking a shell."""

    candidate = path.absolute()
    if not candidate.is_absolute() or candidate.is_symlink():
        raise RuntimeError("formal secret env path must be absolute and nonsymlinked")
    current = Path(candidate.anchor)
    for part in candidate.parts[1:-1]:
        current = current / part
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("formal secret env path has a linked/nondirectory ancestor")
    parent_info = os.lstat(candidate.parent)
    if (
        stat.S_IMODE(parent_info.st_mode) != 0o700
        or parent_info.st_uid != os.geteuid()
    ):
        raise RuntimeError("formal secret parent owner/mode differs")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(candidate, flags)
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_uid != os.geteuid()
            or before.st_size <= 0
            or before.st_size > 65_536
        ):
            raise RuntimeError("formal secret file owner/mode/type/size differs")
        data = os.read(descriptor, 65_537)
        after = os.fstat(descriptor)
        if (
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or len(data) != before.st_size
        ):
            raise RuntimeError("formal secret file changed while being read")
    finally:
        os.close(descriptor)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise RuntimeError("formal secret env must be literal ASCII") from exc
    if "\r" in text or "\x00" in text:
        raise RuntimeError("formal secret env contains forbidden control bytes")
    lines = text.splitlines()
    if len(lines) != 1:
        raise RuntimeError("formal secret env must contain exactly one KEY=VALUE line")
    match = _STRICT_SECRET_ENV_LINE.fullmatch(lines[0])
    if match is None or match.group(1) != key:
        raise RuntimeError("formal secret env key/grammar differs")
    return match.group(2)


def _is_formal_job(job: Mapping[str, Any]) -> bool:
    return (
        str(job.get("phase") or "") == "full"
        and bool(job.get("result_namespace"))
        and bool(job.get("execution_lock_sha256"))
        and bool(job.get("execution_policy_sha256"))
    )


def _formal_marker_binding(job: Mapping[str, Any]) -> dict[str, str]:
    return {
        "execution_lock_sha256": _require_sha256(
            str(job.get("execution_lock_sha256") or ""),
            field="job.execution_lock_sha256",
        ),
        "execution_policy_sha256": _require_sha256(
            str(job.get("execution_policy_sha256") or ""),
            field="job.execution_policy_sha256",
        ),
        "job_binding_sha256": formal_job_binding_sha256(job),
        "job_identity_sha256": job_identity_sha256(job),
    }


def _verify_formal_stage_authorization(
    config: AgentDojoSmokeConfig,
) -> FormalStageAuthorization:
    authorization = _shared_verify_formal_stage_authorization(
        path=config.stage_authorization_path,
        expected_sha256=config.stage_authorization_sha256,
        job=config.job,
        expected_runtime_policy_semantic_sha256=config.openrouter_runtime_policy_sha256,
        expected_runtime_policy_file_sha256=config.openrouter_runtime_policy_file_sha256,
        expected_runtime_state_dir=config.runtime_state_dir,
    )
    expected_resource_binding = resource_worker_process_binding_sha256(
        execution_scope_sha256=str(config.job.get("execution_lock_sha256") or ""),
        stage_id=str(authorization.payload["stage_id"]),
        session_id=str(authorization.payload["session_id"]),
        stage_binding_sha256=authorization.file_sha256,
    )
    if config.resource_stage_token != expected_resource_binding:
        raise RuntimeError(
            "formal worker process binding differs from its stage authorization"
        )
    return authorization


def _assert_formal_stage_authorization_current(
    authorization: FormalStageAuthorization,
    *,
    job: Mapping[str, Any],
    policy: RuntimePolicy,
    model_config_sha256: str,
) -> None:
    _shared_assert_formal_stage_authorization_current(
        authorization,
        job=job,
        policy=policy,
        model_config_sha256=model_config_sha256,
    )




def _prepare_formal_worker_directory(
    config: AgentDojoSmokeConfig,
    authorization: FormalStageAuthorization,
) -> None:
    """Consume one controller launch intent without deleting remote evidence."""

    output = config.output_dir
    if output.is_symlink() or not output.is_dir():
        raise RuntimeError("formal output directory must pre-exist as a regular directory")
    observed = sorted(path.name for path in output.iterdir())
    expected_names = sorted(
        (
            FORMAL_JOB_LAUNCH_MARKER,
            *FORMAL_SEALED_STREAM_FILES,
            *FORMAL_SUPERVISOR_PRESTART_FILES,
        )
    )
    if observed != expected_names:
        raise RuntimeError(
            "formal output directory must contain only its immutable launch intent "
            "and sealed worker streams; "
            f"observed={observed[:5]}"
        )
    for stream_name in FORMAL_SEALED_STREAM_FILES:
        stream_path = output / stream_name
        stream_stat = stream_path.lstat()
        if (
            stream_path.is_symlink()
            or not stat.S_ISREG(stream_stat.st_mode)
            or stream_stat.st_nlink != 1
            or stat.S_IMODE(stream_stat.st_mode) != 0o600
            or stream_stat.st_size != 0
        ):
            raise RuntimeError(
                f"formal sealed stream must be empty regular mode-0600 nlink-1: {stream_name}"
            )
    launch_path = output / FORMAL_JOB_LAUNCH_MARKER
    if launch_path.is_symlink() or not launch_path.is_file():
        raise RuntimeError("formal launch intent must be a regular file")
    launch = _loads_json_object(launch_path.read_text(encoding="utf-8"))
    expected = {
        "schema_version": "agentdojo_formal_job_launch_intent/v1",
        **_formal_marker_binding(config.job),
        "stage_authorization_sha256": authorization.file_sha256,
    }
    for key, value in expected.items():
        if launch.get(key) != value:
            raise RuntimeError(f"formal launch intent has stale {key}")
    timeout_seconds = int(
        authorization.payload["formal_wall_clock_timeout_seconds"]
    )
    started = datetime.now(timezone.utc)
    deadline = started + timedelta(seconds=timeout_seconds)
    _write_json_exclusive(
        output / FORMAL_JOB_STARTED_MARKER,
        {
            "schema_version": "agentdojo_formal_job_started/v2",
            "started_at": started.isoformat(),
            "deadline_at": deadline.isoformat(),
            "formal_wall_clock_timeout_seconds": timeout_seconds,
            "pid": os.getpid(),
            "linux_starttime_ticks": _linux_process_starttime_ticks(),
            "stage_authorization_sha256": authorization.file_sha256,
            "formal_stage_id": str(authorization.payload["stage_id"]),
            "formal_stage_session_id": str(authorization.payload["session_id"]),
            **_formal_marker_binding(config.job),
        },
    )


def _linux_process_starttime_ticks() -> int:
    """Read Linux /proc starttime so a recycled PID cannot satisfy recovery."""

    stat_path = Path("/proc/self/stat")
    if not stat_path.is_file() or stat_path.is_symlink():
        raise RuntimeError("formal execution requires a regular Linux /proc/self/stat")
    try:
        raw = stat_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError("could not read Linux process starttime") from exc
    command_end = raw.rfind(")")
    if command_end < 0:
        raise RuntimeError("Linux /proc/self/stat has invalid process-name framing")
    # Fields after ')' begin with field 3 (state); field 22 is offset 19.
    fields_after_command = raw[command_end + 1 :].strip().split()
    if len(fields_after_command) <= 19:
        raise RuntimeError("Linux /proc/self/stat is missing field 22 starttime")
    try:
        ticks = int(fields_after_command[19])
    except ValueError as exc:
        raise RuntimeError("Linux /proc/self/stat starttime is not an integer") from exc
    if ticks <= 0:
        raise RuntimeError("Linux /proc/self/stat starttime must be positive")
    return ticks




def _build_runtime_control(
    config: AgentDojoSmokeConfig,
    *,
    api_key: str,
    formal_stage_authorization: FormalStageAuthorization | None = None,
) -> OpenRouterRuntimeControl | None:
    namespaced = bool(config.job.get("result_namespace")) and str(
        config.job.get("phase") or "smoke"
    ) == "full"
    if not config.openrouter_runtime_policy:
        if namespaced:
            raise RuntimePolicyError(
                "namespaced AgentDojo jobs require a locked openrouter_runtime_policy"
            )
        return None
    if namespaced:
        _require_sha256(
            str(config.job.get("execution_lock_sha256") or ""),
            field="job.execution_lock_sha256",
        )
        _require_sha256(
            str(config.job.get("execution_policy_sha256") or ""),
            field="job.execution_policy_sha256",
        )
    semantic_sha = _require_sha256(
        config.openrouter_runtime_policy_sha256,
        field="openrouter_runtime_policy_sha256",
    )
    _require_sha256(
        config.openrouter_runtime_policy_file_sha256,
        field="openrouter_runtime_policy_file_sha256",
    )
    if config.runtime_state_dir is None:
        raise RuntimePolicyError(
            "locked openrouter runtime control requires --runtime-state-dir"
        )
    policy = load_runtime_policy(
        config.openrouter_runtime_policy,
        expected_semantic_sha256=semantic_sha,
    )
    credential_fingerprint_sha256 = openrouter_key_fingerprint(api_key)
    if namespaced and policy.execution_key_fingerprint_sha256 != (
        credential_fingerprint_sha256
    ):
        raise RuntimePolicyError(
            "loaded OpenRouter secret differs from the finalized execution key"
        )
    if namespaced and (
        policy.lifecycle_status != "finalized"
        or not policy.formal_execution_allowed
        or policy.runtime_mode != "finalized_validation"
    ):
        raise RuntimePolicyError(
            "formal execution rejects provisional/exploratory runtime policies"
        )
    if policy.retry.max_attempts != config.retry + 1:
        raise RuntimePolicyError(
            "runtime retry.max_attempts must equal the frozen agent retry + 1: "
            f"runtime={policy.retry.max_attempts} agent={config.retry + 1}"
        )
    budget_scope = (
        "formal_execution"
        if namespaced
        else str(config.job.get("runtime_scope") or "")
    )
    if not namespaced and budget_scope != "disposable_preflight":
        raise RuntimePolicyError(
            "non-formal runtime-controlled jobs require disposable_preflight scope"
        )
    limiter = GlobalRateLimiter(
        policy,
        state_dir=config.runtime_state_dir,
        budget_scope=budget_scope,
    )
    session_id_raw = (
        None
        if formal_stage_authorization is None
        else formal_stage_authorization.payload.get("session_id")
    ) or config.job.get("runtime_session_id")
    if namespaced and (
        formal_stage_authorization is None or not isinstance(session_id_raw, str)
    ):
        raise RuntimePolicyError(
            "formal jobs require an independently locked stage authorization/session"
        )
    session_id = None if session_id_raw is None else str(session_id_raw)
    host_boot_id = None if session_id is None else linux_host_boot_id()
    health_paths: list[Path] = [
        config.output_dir / "blind_health" / "openrouter_health.jsonl",
        config.runtime_state_dir / "blind_health.jsonl",
    ]
    shared_root: Path | None = None
    shared_group: str | None = None
    if namespaced:
        if (
            config.blind_aggregate_root is None
            or not config.blind_aggregate_root.is_absolute()
            or not config.blind_group
        ):
            raise RuntimePolicyError(
                "formal jobs require an absolute blind aggregate root and blind group"
            )
        shared_root = config.blind_aggregate_root
        shared_group = config.blind_group
        health_paths.append(shared_root / "openrouter_health.jsonl")
        if config.disposable_blind_health_path is not None:
            raise RuntimePolicyError(
                "formal jobs must not use a disposable blind-health path"
            )
    else:
        disposable_path = config.disposable_blind_health_path
        if disposable_path is None or not disposable_path.is_absolute():
            raise RuntimePolicyError(
                "disposable preflight requires an absolute stage blind-health path"
            )
        health_paths.append(disposable_path)
    ledger = BlindHealthLedger(
        tuple(health_paths),
        policy_sha256=policy.semantic_sha256,
        session_id=session_id,
        host_boot_id=host_boot_id,
        shared_root=shared_root,
        shared_group=shared_group,
        credential_fingerprint_sha256=credential_fingerprint_sha256,
    )
    sealed_incidents = SealedIncidentLedger(
        config.runtime_state_dir / "sealed" / "incidents.jsonl",
        policy_sha256=policy.semantic_sha256,
    )
    return OpenRouterRuntimeControl(
        policy=policy,
        limiter=limiter,
        ledger=ledger,
        sealed_incidents=sealed_incidents,
        job=dict(config.job),
        job_identity_sha256=job_identity_sha256(config.job),
        model_config_sha256=_model_config_sha256(config),
        credential_fingerprint_sha256=credential_fingerprint_sha256,
        formal_stage_authorization=formal_stage_authorization,
    )


def _validated_response_usage_and_model(
    response: Mapping[str, Any], *, requested_model_id: str
) -> tuple[int, float, str]:
    requested = requested_model_id.removeprefix("openrouter/")
    if response.get("error") is not None:
        raise _OpenRouterResponseContractError(
            "OpenRouter HTTP 200 payload contains an error", retryable=True
        )
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise _OpenRouterResponseContractError(
            "OpenRouter success response has no non-empty choices", retryable=True
        )
    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        raise _OpenRouterResponseContractError(
            "OpenRouter first choice is not an object", retryable=True
        )
    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        raise _OpenRouterResponseContractError(
            "OpenRouter first choice has no message object", retryable=True
        )
    if message.get("role") != "assistant":
        raise _OpenRouterResponseContractError(
            "OpenRouter first choice message role is not assistant", retryable=True
        )
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise _OpenRouterResponseContractError(
            "OpenRouter first choice message content is missing or empty",
            retryable=True,
        )
    returned_raw = response.get("model")
    if not isinstance(returned_raw, str) or not returned_raw.strip():
        raise _OpenRouterResponseContractError(
            "OpenRouter success response has no returned model", retryable=True
        )
    returned = returned_raw.strip().removeprefix("openrouter/")
    if returned != requested:
        raise _OpenRouterResponseContractError(
            "OpenRouter returned model is outside the locked canonical mapping",
            retryable=False,
        )
    provider_raw = response.get("provider")
    if (
        not isinstance(provider_raw, str)
        or not provider_raw.strip()
        or len(provider_raw.strip()) > 256
        or "\n" in provider_raw
    ):
        raise _OpenRouterResponseContractError(
            "OpenRouter success response has no valid provider identity", retryable=True
        )
    returned_provider = provider_raw.strip()
    usage = response.get("usage")
    if not isinstance(usage, Mapping):
        raise _OpenRouterResponseContractError(
            "OpenRouter success response has no usage object", retryable=True
        )
    values: dict[str, int] = {}
    for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = usage.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise _OpenRouterResponseContractError(
                f"OpenRouter usage.{field} must be a non-negative integer",
                retryable=True,
            )
        values[field] = value
    if values["total_tokens"] != (
        values["prompt_tokens"] + values["completion_tokens"]
    ):
        raise _OpenRouterResponseContractError(
            "OpenRouter total_tokens differs from its components", retryable=True
        )
    cost_raw = usage.get("cost")
    if isinstance(cost_raw, bool) or not isinstance(cost_raw, (int, float)):
        raise _OpenRouterResponseContractError(
            "OpenRouter usage.cost must be numeric", retryable=True
        )
    cost = float(cost_raw)
    if not math.isfinite(cost) or cost < 0:
        raise _OpenRouterResponseContractError(
            "OpenRouter usage.cost must be finite and non-negative", retryable=True
        )
    identity_sha = sha256_object(
        {
            "requested_model_id": requested,
            "returned_model_id": returned,
            "returned_provider": returned_provider,
            "mapping": (
                "exact_model_slug_plus_observed_dynamic_provider_identity/v1"
            ),
            "fixed_upstream_provider_claimed": False,
        }
    )
    return values["total_tokens"], cost, identity_sha


def _classify_runtime_incident(
    *,
    http_status: int | None,
    error: Exception | None,
) -> tuple[str, str]:
    if http_status == 429:
        return "http_rate_limit", "provider"
    if http_status == 402:
        return "budget", "provider"
    if http_status in {401, 403}:
        return "credential", "credentials"
    if http_status is not None and http_status >= 500:
        return "http_service", "provider"
    if isinstance(error, _OpenRouterResponseContractError):
        return ("invalid_json" if error.retryable else "runtime"), "provider"
    message = str(error or "")
    if "invalid JSON" in message or "must be a JSON object" in message:
        return "invalid_json", "provider"
    if "transport error" in message:
        return "transport", "provider"
    return "runtime", "unknown"


def _record_worker_incident(
    runtime_control: OpenRouterRuntimeControl,
    error: Exception,
) -> None:
    incident_id = f"inc-{uuid.uuid4().hex}"
    if isinstance(error, RuntimeBudgetExceeded):
        category, origin = "budget", "controller"
    elif isinstance(error, _OpenRouterResponseContractError):
        category = "invalid_json" if error.retryable else "runtime"
        origin = "provider"
    elif isinstance(error, RuntimePolicyError):
        category, origin = "runtime", "controller"
    elif "OpenRouter proxy recorded" in str(error):
        category, origin = "http_service", "provider"
    else:
        category, origin = "case_execution", "case"
    runtime_control.sealed_incidents.record(
        incident_id=incident_id,
        job=runtime_control.job,
        error_category=category,
        error_origin=origin,
    )
    runtime_control.ledger.record(
        event_type="incident",
        outcome="fatal_error",
        incident_id=incident_id,
        job_identity_sha256=runtime_control.job_identity_sha256,
        model_config_sha256=runtime_control.model_config_sha256,
    )
    runtime_control.ledger.record(
        event_type="worker_completion",
        outcome="fatal_error",
        incident_id=incident_id,
        job_identity_sha256=runtime_control.job_identity_sha256,
        model_config_sha256=runtime_control.model_config_sha256,
    )


def _model_config_sha256(config: AgentDojoSmokeConfig) -> str:
    return agentdojo_model_config_sha256(
        agent_id=str(config.job.get("agent_id") or ""),
        provider="openrouter",
        model_id=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
        retry=config.retry,
    )


def _require_sha256(value: str, *, field: str) -> str:
    normalized = str(value).removeprefix("sha256:")
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise RuntimePolicyError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _verify_agentdojo_install(config: AgentDojoSmokeConfig) -> dict[str, Any]:
    try:
        actual = distribution_version("agentdojo")
    except PackageNotFoundError as exc:
        raise RuntimeError("AgentDojo distribution metadata is unavailable") from exc
    if actual != config.agentdojo_package_version:
        raise RuntimeError(
            "AgentDojo package version mismatch: "
            f"expected={config.agentdojo_package_version} actual={actual}"
        )
    source_lock = config.agentdojo_source_lock
    if not source_lock:
        return {
            "agentdojo_package_version": actual,
            "source_lock_enforced": False,
            "verified_source_file_count": 0,
        }
    if source_lock.get("agentdojo_git_commit") != config.agentdojo_git_commit:
        raise RuntimeError("AgentDojo source lock git commit mismatch")
    if source_lock.get("agentdojo_git_tree") != config.agentdojo_git_tree:
        raise RuntimeError("AgentDojo source lock git tree mismatch")

    import agentdojo

    package_root = Path(agentdojo.__file__).resolve().parent
    descriptors = source_lock.get("files")
    if not isinstance(descriptors, list) or not descriptors:
        raise RuntimeError("AgentDojo source lock requires a non-empty files list")
    verified: list[dict[str, str]] = []
    for index, descriptor in enumerate(descriptors):
        if not isinstance(descriptor, Mapping):
            raise RuntimeError(f"AgentDojo source lock files[{index}] must be an object")
        repo_path = str(descriptor.get("repo_path") or "")
        expected = str(descriptor.get("sha256") or "").removeprefix("sha256:")
        prefix = "src/agentdojo/"
        if not repo_path.startswith(prefix) or len(expected) != 64:
            raise RuntimeError(f"invalid AgentDojo source lock descriptor: {repo_path!r}")
        relative = Path(repo_path.removeprefix(prefix))
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"unsafe AgentDojo source lock path: {repo_path!r}")
        installed_path = (package_root / relative).resolve()
        try:
            installed_path.relative_to(package_root)
        except ValueError as exc:
            raise RuntimeError(f"AgentDojo source path escapes package root: {repo_path}") from exc
        if not installed_path.is_file() or installed_path.is_symlink():
            raise RuntimeError(f"AgentDojo pinned source file is missing or symlinked: {repo_path}")
        actual_hash = hashlib.sha256(installed_path.read_bytes()).hexdigest()
        if actual_hash != expected:
            raise RuntimeError(
                "AgentDojo installed source hash mismatch: "
                f"path={repo_path} expected={expected} actual={actual_hash}"
            )
        verified.append({"repo_path": repo_path, "sha256": actual_hash})
    return {
        "agentdojo_package_version": actual,
        "agentdojo_git_commit": config.agentdojo_git_commit,
        "agentdojo_git_tree": config.agentdojo_git_tree,
        "source_lock_enforced": True,
        "verified_source_file_count": len(verified),
        "verified_source_files": verified,
    }


def _optional_string(value: str | None) -> str | None:
    if value is None or value.strip().lower() in {"", "none", "null"}:
        return None
    return value.strip()


def _optional_path(value: str | None) -> Path | None:
    normalized = _optional_string(value)
    return None if normalized is None else Path(normalized)


def _proxy_error_calls(proxy_calls_dir: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for path in sorted(proxy_calls_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append({"path": str(path), "error_message": f"invalid proxy call JSON: {exc}"})
            continue
        error_message = payload.get("error_message") if isinstance(payload, Mapping) else None
        if error_message:
            errors.append({"path": str(path), "error_message": str(error_message)})
    return errors


def _apply_and_verify_locked_job_seed(job: Mapping[str, Any]) -> dict[str, Any]:
    requires_locked_seed = _is_formal_job(job) or str(
        job.get("runtime_scope") or ""
    ) == "disposable_preflight"
    seed_raw = job.get("seed")
    if seed_raw is None and not requires_locked_seed:
        return {
            "schema_version": "agentdojo_worker_seed_verification/v1",
            "status": "legacy_unseeded",
            "seed_policy_sha256": AGENTDOJO_LOCAL_LLM_SEED_POLICY_SHA256,
            "provider_determinism_claimed": False,
        }
    if (
        isinstance(seed_raw, bool)
        or not isinstance(seed_raw, int)
        or not 0 <= seed_raw < 2**32
    ):
        raise RuntimePolicyError("locked AgentDojo job seed must be uint32")
    expected = str(seed_raw)
    if requires_locked_seed and os.environ.get("PYTHONHASHSEED") != expected:
        raise RuntimePolicyError(
            "PYTHONHASHSEED must equal the locked numeric job seed before worker start"
        )
    random.seed(seed_raw)
    numpy_seeded = False
    try:
        import numpy  # type: ignore[import-not-found]
    except ImportError:
        pass
    else:
        numpy.random.seed(seed_raw % (2**32))
        numpy_seeded = True
    return {
        "schema_version": "agentdojo_worker_seed_verification/v1",
        "status": "applied",
        "job_seed": seed_raw,
        "pythonhashseed_verified": os.environ.get("PYTHONHASHSEED") == expected,
        "python_random_seeded": True,
        "numpy_random_seeded_if_available": numpy_seeded,
        "seed_policy": dict(AGENTDOJO_LOCAL_LLM_SEED_POLICY),
        "seed_policy_sha256": AGENTDOJO_LOCAL_LLM_SEED_POLICY_SHA256,
        "provider_determinism_claimed": False,
    }


def _transform_agentdojo_local_request(
    request_payload: Any,
    *,
    model_id: str,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    if not isinstance(request_payload, Mapping):
        raise RuntimePolicyError("AgentDojo LocalLLM request must be an object")
    expected_fields = {"model", "messages", "temperature", "top_p", "seed"}
    if set(request_payload) != expected_fields:
        raise RuntimePolicyError(
            "AgentDojo 0.1.35 LocalLLM request fields differ from the locked allowlist"
        )
    incoming_model = request_payload.get("model")
    if not isinstance(incoming_model, str) or incoming_model.removeprefix(
        "openrouter/"
    ) != model_id.removeprefix("openrouter/"):
        raise RuntimePolicyError("LocalLLM incoming model differs from frozen agent model")
    incoming_temperature = request_payload.get("temperature")
    if (
        isinstance(incoming_temperature, bool)
        or not isinstance(incoming_temperature, (int, float))
        or float(incoming_temperature) != float(temperature)
    ):
        raise RuntimePolicyError("LocalLLM temperature differs from frozen agent config")
    incoming_top_p = request_payload.get("top_p")
    if (
        isinstance(incoming_top_p, bool)
        or not isinstance(incoming_top_p, (int, float))
        or float(incoming_top_p) != AGENTDOJO_LOCAL_LLM_TOP_P
    ):
        raise RuntimePolicyError("LocalLLM top_p differs from pinned AgentDojo source")
    incoming_seed = request_payload.get("seed")
    if (
        isinstance(incoming_seed, bool)
        or not isinstance(incoming_seed, int)
        or not 0 <= incoming_seed < 2**32
    ):
        raise RuntimePolicyError("LocalLLM per-call seed must be uint32")
    if isinstance(max_tokens, bool) or int(max_tokens) <= 0:
        raise RuntimePolicyError("frozen max_tokens must be positive")
    return {
        "model": model_id.removeprefix("openrouter/"),
        "messages": _normalize_chat_messages(request_payload["messages"]),
        "temperature": float(temperature),
        "top_p": AGENTDOJO_LOCAL_LLM_TOP_P,
        "seed": incoming_seed,
        "max_tokens": int(max_tokens),
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(child) for child in value]
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _jsonable(value.model_dump())
    if hasattr(value, "__dict__"):
        return {key: _jsonable(child) for key, child in vars(value).items() if not key.startswith("_")}
    return str(value)


def _write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    """Create and fsync an immutable lifecycle marker exactly once."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(_jsonable(payload), ensure_ascii=True, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
