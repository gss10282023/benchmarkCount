"""Fail-closed JSON/JSONL logging for LLM audit records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import validate_object


SECRET_KEY_NAMES = (
    "api_key",
    "apikey",
    "authorization",
    "access_token",
    "refresh_token",
    "bearer_token",
    "secret",
    "password",
)


class LLMLoggingError(RuntimeError):
    """Raised when an LLM log would be incomplete or leak a secret."""


@dataclass(frozen=True)
class LoggedCall:
    jsonl_path: str
    record_path: str | None
    record: dict[str, Any]


class LLMCallLogger:
    """Append complete `llm_call/v1` records to JSONL and optional JSON files."""

    def __init__(
        self,
        jsonl_path: str | Path,
        *,
        per_call_dir: str | Path | None = None,
        secret_values: Iterable[str | None] = (),
    ) -> None:
        self.jsonl_path = resolve_repo_path(jsonl_path)
        self.per_call_dir = resolve_repo_path(per_call_dir) if per_call_dir is not None else None
        self.secret_values = tuple(secret for secret in secret_values if secret)

    @classmethod
    def from_dir(
        cls,
        log_dir: str | Path,
        *,
        filename: str = "calls.jsonl",
        secret_values: Iterable[str | None] = (),
        per_call_json: bool = True,
    ) -> "LLMCallLogger":
        resolved = resolve_repo_path(log_dir)
        return cls(
            resolved / filename,
            per_call_dir=resolved if per_call_json else None,
            secret_values=secret_values,
        )

    def log(self, record: Mapping[str, Any]) -> LoggedCall:
        sanitized = redact_secrets(record, self.secret_values)
        sanitized["redaction_status"] = "no_secret_logged"
        _assert_no_secret_values(sanitized, self.secret_values)
        validate_object("llm_call", sanitized, raise_on_error=True)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sanitized, ensure_ascii=True, sort_keys=True) + "\n")

        record_path: Path | None = None
        if self.per_call_dir is not None:
            self.per_call_dir.mkdir(parents=True, exist_ok=True)
            retry_index = int(sanitized.get("retry_index") or 0)
            suffix = "" if retry_index == 0 else f".retry-{retry_index}"
            record_path = self.per_call_dir / f"{_safe_filename(sanitized['call_id'])}{suffix}.json"
            record_path.write_text(json.dumps(sanitized, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return LoggedCall(
            jsonl_path=str(self.jsonl_path),
            record_path=str(record_path) if record_path is not None else None,
            record=dict(sanitized),
        )


def redact_secrets(payload: Any, secret_values: Iterable[str | None]) -> Any:
    """Return a deep copy with explicit secret values removed from strings."""

    secrets = tuple(secret for secret in secret_values if secret)
    if isinstance(payload, Mapping):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            key_text = str(key)
            if _looks_secret_key(key_text):
                redacted[key_text] = "[REDACTED_SECRET]"
            else:
                redacted[key_text] = redact_secrets(value, secrets)
        return redacted
    if isinstance(payload, list):
        return [redact_secrets(value, secrets) for value in payload]
    if isinstance(payload, tuple):
        return [redact_secrets(value, secrets) for value in payload]
    if isinstance(payload, str):
        value = payload
        for secret in secrets:
            value = value.replace(secret, "[REDACTED_SECRET]")
        return value
    return payload


def make_llm_call_record(
    *,
    call_id: str,
    domain: str,
    phase: str,
    experiment_type: str,
    priority: str,
    agent_id_or_role: str,
    provider: str,
    model: str,
    model_version: str,
    api_key_env: str,
    prompt_version: str,
    prompt_hash: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
    retry_index: int,
    rate_limit_bucket: str,
    request_timestamp: str,
    response_timestamp: str,
    response_metadata: Mapping[str, Any],
    token_usage: Mapping[str, int],
    cost: Mapping[str, Any],
    config_hash: str,
    manifest_hash: str,
    run_id: str | None = None,
    record_slot_id: str | None = None,
    attempt_id: str | None = None,
    case_unit_id: str | None = None,
    task_id: str | None = None,
    evidence_contract_id: str | None = None,
    contract_version: str | None = None,
    contract_draft_id: str | None = None,
    contract_template_version: str | None = None,
    contract_template_hash: str | None = None,
    source_bundle_hash: str | None = None,
    visible_input_hash: str | None = None,
    hidden_input_assertion_hash: str | None = None,
    forbidden_input_assertion_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "llm_call/v1",
        "call_id": call_id,
        "domain": domain,
        "phase": phase,
        "experiment_type": experiment_type,
        "priority": priority,
        "agent_id_or_role": agent_id_or_role,
        "provider": provider,
        "model": model,
        "model_version": model_version,
        "api_key_env": api_key_env,
        "prompt_version": prompt_version,
        "prompt_hash": prompt_hash,
        "prompt_hash_method": "sha256",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout_seconds": timeout_seconds,
        "retry_index": retry_index,
        "rate_limit_bucket": rate_limit_bucket,
        "request_timestamp": request_timestamp,
        "response_timestamp": response_timestamp,
        "response_metadata": dict(response_metadata),
        "token_usage": {
            "prompt_tokens": int(token_usage.get("prompt_tokens", 0)),
            "completion_tokens": int(token_usage.get("completion_tokens", 0)),
            "cached_prompt_tokens": int(token_usage.get("cached_prompt_tokens", 0)),
            "reasoning_tokens": int(token_usage.get("reasoning_tokens", 0)),
            "total_tokens": int(token_usage.get("total_tokens", 0)),
        },
        "cost": dict(cost),
        "config_hash": config_hash,
        "manifest_hash": manifest_hash,
        "redaction_status": "no_secret_logged",
        "run_id": run_id,
        "record_slot_id": record_slot_id,
        "attempt_id": attempt_id,
        "case_unit_id": case_unit_id,
        "task_id": task_id,
        "evidence_contract_id": evidence_contract_id,
        "contract_version": contract_version,
        "contract_draft_id": contract_draft_id,
        "contract_template_version": contract_template_version,
        "contract_template_hash": contract_template_hash,
        "source_bundle_hash": source_bundle_hash,
        "visible_input_hash": visible_input_hash,
        "hidden_input_assertion_hash": hidden_input_assertion_hash,
        "forbidden_input_assertion_hash": forbidden_input_assertion_hash,
    }


def _assert_no_secret_values(payload: Mapping[str, Any], secret_values: Iterable[str | None]) -> None:
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    for secret in secret_values:
        if secret and secret in text:
            raise LLMLoggingError("secret value would be written to LLM log")


def _looks_secret_key(key: str) -> bool:
    lowered = key.lower()
    return lowered in SECRET_KEY_NAMES


def _safe_filename(value: Any) -> str:
    text = str(value)
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in text).strip("-") or "llm-call"
