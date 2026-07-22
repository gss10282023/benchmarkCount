"""LLM token usage normalization and auditable cost accounting."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

from evidence_system.core.hashing import sha256_object


USD_QUANT = Decimal("0.000000000001")


@dataclass(frozen=True)
class CostSummary:
    call_count: int
    costed_call_count: int
    missing_cost_count: int
    total_cost_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_count": self.call_count,
            "costed_call_count": self.costed_call_count,
            "missing_cost_count": self.missing_cost_count,
            "total_cost_usd": self.total_cost_usd,
        }


def normalize_token_usage(response_payload: Mapping[str, Any] | None) -> dict[str, int]:
    """Return the canonical token usage block for an OpenRouter response."""

    usage = response_payload.get("usage") if isinstance(response_payload, Mapping) else None
    if not isinstance(usage, Mapping):
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cached_prompt_tokens": 0,
            "reasoning_tokens": 0,
            "total_tokens": 0,
        }

    prompt_tokens = _int(usage.get("prompt_tokens") or usage.get("input_tokens"))
    completion_tokens = _int(usage.get("completion_tokens") or usage.get("output_tokens"))
    cached_prompt_tokens = _int(
        usage.get("cached_prompt_tokens")
        or usage.get("cache_read_input_tokens")
        or _nested_int(usage, ("prompt_tokens_details", "cached_tokens"))
    )
    reasoning_tokens = _int(
        usage.get("reasoning_tokens")
        or usage.get("reasoning")
        or _nested_int(usage, ("completion_tokens_details", "reasoning_tokens"))
    )
    total_tokens = _int(usage.get("total_tokens"))
    computed_total = prompt_tokens + completion_tokens + reasoning_tokens
    if total_tokens < computed_total:
        total_tokens = computed_total
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cached_prompt_tokens": cached_prompt_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
    }


def compute_cost(
    response_payload: Mapping[str, Any] | None,
    token_usage: Mapping[str, int],
    *,
    pricing_table: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute the canonical `llm_call.cost` object.

    Provider-reported cost wins. If it is absent and a pricing table is
    configured, the estimate is explicitly marked as `config_estimate`.
    Otherwise cost remains unavailable with a reason.
    """

    provider_cost_payload = _provider_cost_payload(response_payload)
    provider_amount = _provider_amount(provider_cost_payload)
    if provider_amount is not None:
        amount = _to_usd_float(provider_amount)
        return {
            "amount": amount,
            "currency": "USD",
            "pricing_source": "provider_response",
            "pricing_table_id": None,
            "pricing_table_version": None,
            "pricing_source_hash": sha256_object(provider_cost_payload),
            "cost_calculation_method": "provider_reported",
            "missing_cost_reason": None,
            "total_cost_usd": amount,
        }

    if pricing_table:
        amount = _pricing_table_amount(token_usage, pricing_table)
        return {
            "amount": amount,
            "currency": "USD",
            "pricing_source": "config_estimate",
            "pricing_table_id": str(pricing_table.get("pricing_table_id") or pricing_table.get("id") or "openrouter-config"),
            "pricing_table_version": str(pricing_table.get("pricing_table_version") or pricing_table.get("version") or "unversioned"),
            "pricing_source_hash": sha256_object(pricing_table),
            "cost_calculation_method": "tokens_times_config_rate",
            "missing_cost_reason": None,
            "total_cost_usd": amount,
        }

    return {
        "amount": None,
        "currency": "USD",
        "pricing_source": "unavailable",
        "pricing_table_id": None,
        "pricing_table_version": None,
        "pricing_source_hash": None,
        "cost_calculation_method": "unavailable",
        "missing_cost_reason": "provider_cost_unavailable",
        "total_cost_usd": None,
    }


def summarize_costs(records: Iterable[Mapping[str, Any]]) -> CostSummary:
    call_count = 0
    costed = 0
    missing = 0
    total = Decimal("0")
    for record in records:
        call_count += 1
        cost = record.get("cost")
        amount = cost.get("total_cost_usd") if isinstance(cost, Mapping) else None
        if amount is None:
            missing += 1
            continue
        costed += 1
        total += Decimal(str(amount))
    return CostSummary(
        call_count=call_count,
        costed_call_count=costed,
        missing_cost_count=missing,
        total_cost_usd=float(total.quantize(USD_QUANT, rounding=ROUND_HALF_UP)),
    )


def load_llm_call_records(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    """Load LLM call records from JSON files or JSONL logs."""

    records: list[dict[str, Any]] = []
    for path_like in paths:
        path = Path(path_like)
        if path.suffix == ".jsonl":
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped:
                    loaded = json.loads(stripped)
                    if isinstance(loaded, dict):
                        records.append(loaded)
            continue
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            records.append(loaded)
    return records


def summarize_cost_files(paths: Iterable[str | Path]) -> CostSummary:
    return summarize_costs(load_llm_call_records(paths))


def _provider_cost_payload(response_payload: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not isinstance(response_payload, Mapping):
        return None
    for key in ("cost", "cost_usd", "total_cost_usd"):
        if key in response_payload:
            return {"source_key": key, "value": response_payload[key]}
    usage = response_payload.get("usage")
    if isinstance(usage, Mapping):
        for key in ("cost", "cost_usd", "total_cost_usd"):
            if key in usage:
                return {"source_key": f"usage.{key}", "value": usage[key]}
    metadata = response_payload.get("metadata")
    if isinstance(metadata, Mapping):
        for key in ("cost", "cost_usd", "total_cost_usd"):
            if key in metadata:
                return {"source_key": f"metadata.{key}", "value": metadata[key]}
    return None


def _provider_amount(payload: Mapping[str, Any] | None) -> Decimal | None:
    if not isinstance(payload, Mapping):
        return None
    value = payload.get("value")
    if isinstance(value, Mapping):
        for key in ("total_cost_usd", "amount", "cost", "usd"):
            if key in value:
                return _decimal_or_none(value[key])
        return None
    return _decimal_or_none(value)


def _pricing_table_amount(token_usage: Mapping[str, int], pricing_table: Mapping[str, Any]) -> float:
    input_tokens = Decimal(str(token_usage.get("prompt_tokens", 0)))
    output_tokens = Decimal(str(token_usage.get("completion_tokens", 0)))
    cached_tokens = Decimal(str(token_usage.get("cached_prompt_tokens", 0)))
    reasoning_tokens = Decimal(str(token_usage.get("reasoning_tokens", 0)))
    total = (
        input_tokens * _rate(pricing_table, "input")
        + output_tokens * _rate(pricing_table, "output")
        + cached_tokens * _rate(pricing_table, "cached_input")
        + reasoning_tokens * _rate(pricing_table, "reasoning")
    )
    return float(total.quantize(USD_QUANT, rounding=ROUND_HALF_UP))


def _rate(pricing_table: Mapping[str, Any], kind: str) -> Decimal:
    per_token_keys = (f"{kind}_cost_per_token", f"{kind}_rate_per_token")
    per_1k_keys = (f"{kind}_cost_per_1k_tokens", f"{kind}_rate_per_1k_tokens")
    per_1m_keys = (f"{kind}_cost_per_1m_tokens", f"{kind}_rate_per_1m_tokens")
    for key in per_token_keys:
        if key in pricing_table:
            return Decimal(str(pricing_table[key]))
    for key in per_1k_keys:
        if key in pricing_table:
            return Decimal(str(pricing_table[key])) / Decimal("1000")
    for key in per_1m_keys:
        if key in pricing_table:
            return Decimal(str(pricing_table[key])) / Decimal("1000000")
    return Decimal("0")


def _nested_int(payload: Mapping[str, Any], path: tuple[str, ...]) -> int:
    value: Any = payload
    for key in path:
        if not isinstance(value, Mapping):
            return 0
        value = value.get(key)
    return _int(value)


def _int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _decimal_or_none(value: Any) -> Decimal | None:
    try:
        parsed = Decimal(str(value))
    except Exception:
        return None
    if parsed < 0:
        return None
    return parsed


def _to_usd_float(value: Decimal) -> float:
    return float(value.quantize(USD_QUANT, rounding=ROUND_HALF_UP))
