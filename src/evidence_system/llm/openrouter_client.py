"""OpenRouter-backed LLM client with audit logging and secret safety."""

from __future__ import annotations

import json
import hashlib
import os
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping, Protocol

from evidence_system.contracts.common import normalize_domain, parse_timestamp, utc_now_iso
from evidence_system.core.dotenv import load_project_dotenv
from evidence_system.core.errors import EvidenceSystemError
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import SchemaValidationError, load_json_or_yaml, validate_object
from evidence_system.llm.cost import compute_cost, normalize_token_usage
from evidence_system.llm.logging import LLMCallLogger, LoggedCall, make_llm_call_record, redact_secrets


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
PLACEHOLDER_MARKERS = ("需要从", "placeholder", "tbd", "todo", "not_implemented")
AGENT_ROLES = ("Agent A", "Agent B", "Agent C")


class LLMClientError(EvidenceSystemError):
    """Raised when LLM configuration, transport, or logging fails closed."""


class LLMTransportError(LLMClientError):
    """Raised when the transport fails after all retry attempts are logged."""


class OpenRouterTransport(Protocol):
    def post_json(self, url: str, headers: Mapping[str, str], payload: Mapping[str, Any], timeout_seconds: int) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class LLMRoleConfig:
    role: str
    provider: str
    model: str
    model_version: str
    api_key_env: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    rate_limit: Mapping[str, Any]
    prompt_version: str
    config_prompt_hash: str | None
    save_response_metadata: bool
    cost_tracking: bool
    pricing_table: Mapping[str, Any] | None
    config_hash: str
    manifest_hash: str

    @property
    def rate_limit_bucket(self) -> str:
        concurrent = self.rate_limit.get("concurrent_requests") if isinstance(self.rate_limit, Mapping) else None
        rpm = self.rate_limit.get("requests_per_minute") if isinstance(self.rate_limit, Mapping) else None
        return f"{self.role}:rpm={rpm or 'default'}:concurrency={concurrent or 'default'}"


@dataclass(frozen=True)
class LLMCallContext:
    call_id: str
    domain: str
    phase: str
    experiment_type: str
    priority: str
    prompt_hash: str
    prompt_version: str | None = None
    manifest_hash: str | None = None
    run_id: str | None = None
    record_slot_id: str | None = None
    attempt_id: str | None = None
    case_unit_id: str | None = None
    task_id: str | None = None
    evidence_contract_id: str | None = None
    contract_version: str | None = None
    contract_draft_id: str | None = None
    contract_template_version: str | None = None
    contract_template_hash: str | None = None
    source_bundle_hash: str | None = None
    visible_input_hash: str | None = None
    hidden_input_assertion_hash: str | None = None
    forbidden_input_assertion_hash: str | None = None


@dataclass(frozen=True)
class OpenRouterCompletion:
    content: str
    response_payload: Mapping[str, Any]
    successful_log: LoggedCall
    attempt_logs: tuple[LoggedCall, ...]


class UrllibOpenRouterTransport:
    """Minimal stdlib transport for OpenRouter chat completions."""

    def post_json(self, url: str, headers: Mapping[str, str], payload: Mapping[str, Any], timeout_seconds: int) -> Mapping[str, Any]:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise LLMTransportError(f"OpenRouter HTTP {exc.code}: {error_body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise LLMTransportError(f"OpenRouter transport error: {exc.reason}") from exc
        loaded = json.loads(response_body)
        if not isinstance(loaded, Mapping):
            raise LLMTransportError("OpenRouter response must be a JSON object")
        return loaded


class OpenRouterClient:
    def __init__(
        self,
        role_config: LLMRoleConfig,
        *,
        logger: LLMCallLogger,
        transport: OpenRouterTransport | None = None,
        api_key: str | None = None,
        sleep_seconds: float = 0.0,
    ) -> None:
        if role_config.provider != "openrouter":
            raise LLMClientError(f"unsupported LLM provider for OpenRouter client: {role_config.provider}")
        self.role_config = role_config
        self.logger = logger
        self.transport = transport or UrllibOpenRouterTransport()
        self.api_key = api_key if api_key is not None else _api_key_from_env(role_config.api_key_env)
        self.sleep_seconds = sleep_seconds

    def chat_completion(
        self,
        *,
        messages: Sequence[Mapping[str, str]],
        context: LLMCallContext,
        extra_body: Mapping[str, Any] | None = None,
    ) -> OpenRouterCompletion:
        payload = {
            "model": self.role_config.model,
            "messages": [dict(message) for message in messages],
            "temperature": self.role_config.temperature,
            "max_tokens": self.role_config.max_tokens,
        }
        if extra_body:
            payload.update(dict(extra_body))
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logs: list[LoggedCall] = []
        last_error: Exception | None = None
        for retry_index in range(self.role_config.retry + 1):
            request_at = utc_now_iso()
            try:
                response = self.transport.post_json(
                    OPENROUTER_CHAT_COMPLETIONS_URL,
                    headers,
                    payload,
                    self.role_config.timeout_seconds,
                )
                response_at = _response_timestamp_after(request_at)
                token_usage = normalize_token_usage(response)
                cost = compute_cost(
                    response,
                    token_usage,
                    pricing_table=self.role_config.pricing_table if self.role_config.cost_tracking else None,
                )
                content = _extract_content(response)
                response_metadata = self._response_metadata(response, status="success")
                logged = self._log_attempt(
                    context=context,
                    retry_index=retry_index,
                    request_timestamp=request_at,
                    response_timestamp=response_at,
                    response_metadata=response_metadata,
                    token_usage=token_usage,
                    cost=cost,
                )
                logs.append(logged)
                return OpenRouterCompletion(
                    content=content,
                    response_payload=response,
                    successful_log=logged,
                    attempt_logs=tuple(logs),
                )
            except Exception as exc:
                last_error = exc
                response_at = _response_timestamp_after(request_at)
                logged = self._log_attempt(
                    context=context,
                    retry_index=retry_index,
                    request_timestamp=request_at,
                    response_timestamp=response_at,
                    response_metadata={
                        "transport": "openrouter",
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                    token_usage={
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cached_prompt_tokens": 0,
                        "reasoning_tokens": 0,
                        "total_tokens": 0,
                    },
                    cost=compute_cost(None, {}, pricing_table=None),
                )
                logs.append(logged)
                if retry_index < self.role_config.retry and self.sleep_seconds > 0:
                    time.sleep(self.sleep_seconds)
        raise LLMTransportError(f"OpenRouter call failed after {len(logs)} attempts: {last_error}") from last_error

    def _log_attempt(
        self,
        *,
        context: LLMCallContext,
        retry_index: int,
        request_timestamp: str,
        response_timestamp: str,
        response_metadata: Mapping[str, Any],
        token_usage: Mapping[str, int],
        cost: Mapping[str, Any],
        ) -> LoggedCall:
        prompt_version = context.prompt_version or self.role_config.prompt_version
        resolved_model_version = _resolved_model_version(
            response_metadata,
            configured_model_version=self.role_config.model_version,
            configured_model=self.role_config.model,
        )
        record = make_llm_call_record(
            call_id=context.call_id,
            domain=normalize_domain(context.domain),
            phase=context.phase,
            experiment_type=context.experiment_type,
            priority=context.priority,
            agent_id_or_role=self.role_config.role,
            provider=self.role_config.provider,
            model=self.role_config.model,
            model_version=resolved_model_version,
            api_key_env=self.role_config.api_key_env,
            prompt_version=prompt_version,
            prompt_hash=context.prompt_hash,
            temperature=self.role_config.temperature,
            max_tokens=self.role_config.max_tokens,
            timeout_seconds=self.role_config.timeout_seconds,
            retry_index=retry_index,
            rate_limit_bucket=self.role_config.rate_limit_bucket,
            request_timestamp=request_timestamp,
            response_timestamp=response_timestamp,
            response_metadata=redact_secrets(response_metadata, (self.api_key,)),
            token_usage=token_usage,
            cost=cost,
            config_hash=self.role_config.config_hash,
            manifest_hash=context.manifest_hash or self.role_config.manifest_hash,
            run_id=context.run_id,
            record_slot_id=context.record_slot_id,
            attempt_id=context.attempt_id,
            case_unit_id=context.case_unit_id,
            task_id=context.task_id,
            evidence_contract_id=context.evidence_contract_id,
            contract_version=context.contract_version,
            contract_draft_id=context.contract_draft_id,
            contract_template_version=context.contract_template_version,
            contract_template_hash=context.contract_template_hash,
            source_bundle_hash=context.source_bundle_hash,
            visible_input_hash=context.visible_input_hash,
            hidden_input_assertion_hash=context.hidden_input_assertion_hash,
            forbidden_input_assertion_hash=context.forbidden_input_assertion_hash,
        )
        return self.logger.log(record)

    def _response_metadata(self, response: Mapping[str, Any], *, status: str) -> Mapping[str, Any]:
        metadata: dict[str, Any] = {
            "transport": "openrouter",
            "status": status,
            "response_id": response.get("id"),
            "provider_model": response.get("model"),
            "finish_reason": _finish_reason(response),
        }
        if self.role_config.save_response_metadata:
            metadata["provider_response"] = response
        return metadata


def create_client(
    *,
    role: str,
    agents_config_path: str | Path = "configs/agents.yaml",
    locked_manifest_path: str | Path | None = None,
    log_dir: str | Path = "results/logs/llm_calls",
    formal: bool = False,
    transport: OpenRouterTransport | None = None,
    api_key: str | None = None,
) -> OpenRouterClient:
    role_config = load_role_config(
        role,
        agents_config_path=agents_config_path,
        locked_manifest_path=locked_manifest_path,
        formal=formal,
    )
    load_project_dotenv()
    logger = LLMCallLogger.from_dir(log_dir, secret_values=(api_key or os.environ.get(role_config.api_key_env),))
    return OpenRouterClient(role_config, logger=logger, transport=transport, api_key=api_key)


def load_role_config(
    role: str,
    *,
    agents_config_path: str | Path = "configs/agents.yaml",
    locked_manifest_path: str | Path | None = None,
    formal: bool = False,
    prompt_version_fallback: str | None = None,
) -> LLMRoleConfig:
    agents_config = _load_mapping(agents_config_path, "agents config")
    role_payload = _role_payload(agents_config, role)
    config_hash = _hash_path(agents_config_path)
    manifest: Mapping[str, Any] | None = None
    manifest_hash = "0" * 64
    if locked_manifest_path is not None:
        manifest = _load_mapping(locked_manifest_path, "locked manifest")
        manifest_hash = _hash_path(locked_manifest_path)
    if formal:
        if manifest is None:
            raise LLMClientError("formal LLM calls require a locked manifest")
        _validate_formal_manifest(manifest, config_hash, role, role_payload)

    prompt_version = _resolved_string(role_payload.get("prompt_version"), prompt_version_fallback or f"{_safe_role(role)}/prompt")
    config_prompt_hash = _optional_hash(role_payload.get("prompt_hash"))
    config = LLMRoleConfig(
        role=role,
        provider=_required_string(role_payload, "provider", formal=formal),
        model=_required_string(role_payload, "model", formal=formal),
        model_version=_required_string(role_payload, "model_version", formal=formal),
        api_key_env=_required_string(role_payload, "api_key_env", formal=formal),
        temperature=float(role_payload.get("temperature", 0)),
        max_tokens=int(role_payload.get("max_tokens", 1)),
        timeout_seconds=int(role_payload.get("timeout_seconds", 60)),
        retry=int(role_payload.get("retry", 0)),
        rate_limit=dict(role_payload.get("rate_limit") or {}),
        prompt_version=prompt_version,
        config_prompt_hash=config_prompt_hash,
        save_response_metadata=bool(role_payload.get("save_response_metadata", True)),
        cost_tracking=bool(role_payload.get("cost_tracking", True)),
        pricing_table=_pricing_table(role_payload),
        config_hash=config_hash,
        manifest_hash=manifest_hash,
    )
    if formal:
        load_project_dotenv()
    if formal and not os.environ.get(config.api_key_env):
        raise LLMClientError(f"formal LLM call requires env var {config.api_key_env}")
    return config


def _validate_formal_manifest(
    manifest: Mapping[str, Any],
    config_hash: str,
    role: str,
    role_payload: Mapping[str, Any],
) -> None:
    try:
        validate_object("experiment_manifest", manifest, formal=True, raise_on_error=True)
    except SchemaValidationError as exc:
        raise LLMClientError(f"locked manifest failed formal experiment_manifest validation: {exc}") from exc
    status = str(manifest.get("status") or "")
    if status not in {"locked", "frozen", "formal_ready"}:
        raise LLMClientError("formal LLM calls require locked/frozen/formal_ready manifest status")
    manifest_config_hash = manifest.get("agents_config_hash")
    if str(manifest_config_hash) != config_hash:
        raise LLMClientError("agents_config_hash disagrees with locked manifest")
    for field in _formal_required_fields(role):
        _required_formal_value(role_payload, role, field)
    manifest_role = _manifest_role_config(manifest, role)
    if manifest_role is None:
        raise LLMClientError(f"locked manifest missing formal LLM config for {role}")
    compare_fields = set(_formal_required_fields(role))
    compare_fields.add("pricing_table")
    for optional_prompt_field in ("prompt_version", "prompt_hash", "prompt_hash_method"):
        if optional_prompt_field in role_payload or optional_prompt_field in manifest_role:
            compare_fields.add(optional_prompt_field)
    for field in sorted(compare_fields):
        if field == "pricing_table" and field not in role_payload and field not in manifest_role:
            continue
        if field != "pricing_table":
            _required_formal_value(manifest_role, role, field)
        manifest_value = manifest_role.get(field)
        config_value = role_payload.get(field)
        if _contains_placeholder(config_value) or _contains_placeholder(manifest_value):
            raise LLMClientError(f"formal LLM config for {role} has unresolved {field}")
        if not _values_equal(config_value, manifest_value):
            raise LLMClientError(f"formal LLM config mismatch for {role}.{field}")


def _formal_required_fields(role: str) -> tuple[str, ...]:
    fields = (
        "provider",
        "model",
        "model_version",
        "api_key_env",
        "temperature",
        "max_tokens",
        "timeout_seconds",
        "retry",
        "rate_limit",
        "save_response_metadata",
        "cost_tracking",
    )
    if role in {"contract_drafter", "judge_only"}:
        fields += ("prompt_version", "prompt_hash", "prompt_hash_method")
    return fields


def _manifest_role_config(manifest: Mapping[str, Any], role: str) -> Mapping[str, Any] | None:
    container = manifest.get("llm_roles")
    if isinstance(container, Mapping):
        role_config = container.get(role)
        if isinstance(role_config, Mapping):
            return role_config
    return None


def _role_payload(agents_config: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    if role in AGENT_ROLES:
        agents = agents_config.get("experimental_agents")
        if isinstance(agents, Mapping) and isinstance(agents.get(role), Mapping):
            return agents[role]
    payload = agents_config.get(role)
    if isinstance(payload, Mapping):
        return payload
    raise LLMClientError(f"agents config has no LLM role: {role}")


def _required_string(payload: Mapping[str, Any], field: str, *, formal: bool) -> str:
    value = payload.get(field)
    if value is None or str(value) == "":
        raise LLMClientError(f"LLM role config requires {field}")
    if formal and _is_placeholder(value):
        raise LLMClientError(f"formal LLM role config has unresolved {field}")
    return str(value)


def _required_formal_value(payload: Mapping[str, Any], role: str, field: str) -> Any:
    if field not in payload:
        raise LLMClientError(f"formal LLM config for {role} requires {field}")
    value = payload.get(field)
    if value is None or (isinstance(value, str) and not value):
        raise LLMClientError(f"formal LLM config for {role} requires {field}")
    if field == "rate_limit" and not isinstance(value, Mapping):
        raise LLMClientError(f"formal LLM config for {role} requires rate_limit mapping")
    if _contains_placeholder(value):
        raise LLMClientError(f"formal LLM config for {role} has unresolved {field}")
    return value


def _resolved_string(value: Any, fallback: str) -> str:
    if value is None or str(value) == "" or _is_placeholder(value):
        return fallback
    return str(value)


def _optional_hash(value: Any) -> str | None:
    if value is None or str(value) == "" or _is_placeholder(value):
        return None
    return str(value)


def _is_placeholder(value: Any) -> bool:
    text = str(value).strip().lower()
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_placeholder(child) for child in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_placeholder(child) for child in value)
    if isinstance(value, str):
        return _is_placeholder(value)
    return False


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return float(left) == float(right)
    if isinstance(left, Mapping) or isinstance(right, Mapping) or isinstance(left, list) or isinstance(right, list):
        return json.dumps(left, ensure_ascii=True, sort_keys=True) == json.dumps(right, ensure_ascii=True, sort_keys=True)
    return str(left) == str(right)


def _pricing_table(role_payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    pricing = role_payload.get("pricing_table")
    if isinstance(pricing, Mapping):
        return pricing
    openrouter = role_payload.get("openrouter")
    if isinstance(openrouter, Mapping) and isinstance(openrouter.get("pricing_table"), Mapping):
        return openrouter["pricing_table"]
    return None


def _api_key_from_env(api_key_env: str) -> str:
    load_project_dotenv()
    value = os.environ.get(api_key_env)
    if not value:
        raise LLMClientError(f"missing LLM API key environment variable: {api_key_env}")
    return value


def _resolved_model_version(
    response_metadata: Mapping[str, Any],
    *,
    configured_model_version: str,
    configured_model: str,
) -> str:
    provider_response = response_metadata.get("provider_response")
    provider_model = response_metadata.get("provider_model")
    if isinstance(provider_model, str) and provider_model and not _is_placeholder(provider_model):
        return provider_model
    if isinstance(provider_response, Mapping):
        response_model = provider_response.get("model")
        if isinstance(response_model, str) and response_model and not _is_placeholder(response_model):
            return response_model
    if configured_model_version and not _is_placeholder(configured_model_version):
        return configured_model_version
    return configured_model


def _extract_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if isinstance(choices, Sequence) and choices:
        first = choices[0]
        if isinstance(first, Mapping):
            message = first.get("message")
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                return message["content"]
            if isinstance(first.get("text"), str):
                return first["text"]
    if isinstance(response.get("content"), str):
        return str(response["content"])
    raise LLMTransportError("OpenRouter response has no message content")


def _finish_reason(response: Mapping[str, Any]) -> Any:
    choices = response.get("choices")
    if isinstance(choices, Sequence) and choices and isinstance(choices[0], Mapping):
        return choices[0].get("finish_reason")
    return None


def _response_timestamp_after(request_timestamp: str) -> str:
    now = utc_now_iso()
    try:
        duration = parse_timestamp(request_timestamp, "request_timestamp")
        parsed_now = parse_timestamp(now, "response_timestamp")
    except Exception:
        return now
    if parsed_now <= duration:
        return (duration.replace(microsecond=0) + timedelta(seconds=1)).isoformat()
    return now


def _load_mapping(path: str | Path, name: str) -> dict[str, Any]:
    loaded = load_json_or_yaml(resolve_repo_path(path))
    if not isinstance(loaded, Mapping):
        raise LLMClientError(f"{name} must be a mapping")
    return dict(loaded)


def _hash_path(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    if not resolved.exists():
        return "0" * 64
    return hashlib.sha256(resolved.read_bytes()).hexdigest()


def _safe_role(role: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in role.lower()).strip("_") or "llm"
