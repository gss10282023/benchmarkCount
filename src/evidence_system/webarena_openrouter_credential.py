"""Strict, secret-free OpenRouter credential acceptance for WebArena Step 20.

The acceptance performs exactly one minimal paid chat-completion request for
each frozen WebArena agent model.  Credential material, authorization headers,
response bodies, response IDs, and generated model content are deliberately
excluded from the receipt.  A request succeeds only when OpenRouter returns the
exact requested model, positive usage, and positive billed cost.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any, Protocol
import urllib.error
import urllib.request
import uuid

from evidence_system.core.hashing import sha256_file, sha256_object


SCHEMA_VERSION = "webarena_verified_openrouter_credential_acceptance/v1"
OPENROUTER_CHAT_COMPLETIONS_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)
REQUIRED_MODELS = (
    "openai/gpt-5.4",
    "anthropic/claude-opus-4.7",
    "deepseek/deepseek-v4-pro",
)
MAX_TOKENS = 1

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ATTEMPT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{8,}", re.IGNORECASE),
    re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE),
    re.compile(
        r'"(?:api_key|authorization|credential_value|credential_hash|'
        r'openrouter_api_key|response_body|response_content)"\s*:',
        re.IGNORECASE,
    ),
)

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "generated_at",
        "attempt_id",
        "previous_attempt_sha256",
        "required_models",
        "model_probe_count",
        "successful_model_probe_count",
        "paid_model_probe_count",
        "fallback_model_probe_count",
        "request_attempt_count",
        "total_cost_credits",
        "material_retained",
        "credential_material_retained",
        "credential_value_hash_retained",
        "authorization_header_retained",
        "response_body_retained",
        "model_content_retained",
        "probes",
        "gates",
        "secret_scan",
        "integrity",
    }
)
_PROBE_KEYS = frozenset(
    {
        "model_id",
        "http_status",
        "success",
        "started_at",
        "completed_at",
        "elapsed_ms",
        "usage",
        "cost_credits",
        "paid",
        "request_semantics_sha256",
        "response_model_exact",
        "fallback_used",
    }
)
_USAGE_KEYS = frozenset(
    {"prompt_tokens", "completion_tokens", "total_tokens"}
)
_GATE_KEYS = frozenset(
    {
        "exact_required_model_order",
        "one_attempt_per_model",
        "all_http_200",
        "all_response_models_exact",
        "all_usage_positive",
        "all_costs_positive",
        "exactly_three_paid_model_probes",
        "fallback_model_count_zero",
        "tools_requested_zero",
        "plugins_requested_zero",
        "response_material_retained_zero",
        "credential_material_retained_zero",
        "secret_scan_finding_count_zero",
    }
)


class CredentialAcceptanceError(RuntimeError):
    """The credential acceptance receipt or execution is invalid."""


class CredentialProbeTransportError(RuntimeError):
    """A sanitized transport failure that never contains response material."""

    def __init__(self, *, http_status: int | None) -> None:
        self.http_status = http_status
        super().__init__("OpenRouter credential probe transport failed")


class ProbeTransport(Protocol):
    def post_json(
        self,
        *,
        api_key: str,
        payload: Mapping[str, Any],
        timeout_seconds: int,
    ) -> tuple[int, Mapping[str, Any]]:
        """Send one request and return only an in-memory decoded response."""


class UrllibProbeTransport:
    """Minimal transport that never exposes an error response body."""

    def post_json(
        self,
        *,
        api_key: str,
        payload: Mapping[str, Any],
        timeout_seconds: int,
    ) -> tuple[int, Mapping[str, Any]]:
        request = urllib.request.Request(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            data=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status = int(response.status)
                raw = response.read()
        except urllib.error.HTTPError as exc:
            # Deliberately do not read, stringify, or retain the error body.
            raise CredentialProbeTransportError(http_status=int(exc.code)) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise CredentialProbeTransportError(http_status=None) from None
        try:
            loaded = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise CredentialProbeTransportError(http_status=status) from None
        if not isinstance(loaded, Mapping):
            raise CredentialProbeTransportError(http_status=status)
        return status, loaded


@dataclass(frozen=True)
class _NormalizedResponse:
    response_model_exact: bool
    usage: dict[str, int | None]
    cost_credits: float | None
    has_choice: bool
    has_error: bool


def build_openrouter_credential_acceptance(
    *,
    api_key: str,
    transport: ProbeTransport | None = None,
    timeout_seconds: int = 180,
    nonce_factory: Callable[[], str] | None = None,
    attempt_id: str | None = None,
    previous_attempt_sha256: str | None = None,
) -> dict[str, Any]:
    """Execute the exact three-model probe and return a public-safe receipt.

    There are no retries: exactly three HTTP attempts are made, preventing a
    transient failure from silently creating additional paid requests.
    """

    if not isinstance(api_key, str) or not api_key.strip():
        raise CredentialAcceptanceError("OPENROUTER_API_KEY is not set")
    if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise CredentialAcceptanceError("timeout_seconds must be positive")
    selected_transport = transport or UrllibProbeTransport()
    make_nonce = nonce_factory or (lambda: uuid.uuid4().hex)
    selected_attempt_id = attempt_id or f"credential-{uuid.uuid4().hex}"
    if _ATTEMPT_ID_RE.fullmatch(selected_attempt_id) is None:
        raise CredentialAcceptanceError("attempt_id is invalid")
    if previous_attempt_sha256 is not None and _SHA256_RE.fullmatch(
        previous_attempt_sha256
    ) is None:
        raise CredentialAcceptanceError("previous_attempt_sha256 is invalid")

    probes: list[dict[str, Any]] = []
    for model_id in REQUIRED_MODELS:
        nonce = str(make_nonce())
        if not nonce or len(nonce) > 256:
            raise CredentialAcceptanceError("probe nonce is invalid")
        request_payload = _request_payload(model_id=model_id, nonce=nonce)
        started_at = _utc_now_iso()
        started_clock = time.monotonic()
        http_status: int | None = None
        response_payload: Mapping[str, Any] | None = None
        try:
            http_status, response_payload = selected_transport.post_json(
                api_key=api_key,
                payload=request_payload,
                timeout_seconds=timeout_seconds,
            )
        except CredentialProbeTransportError as exc:
            http_status = exc.http_status
        except Exception:
            # Third-party transport doubles must not leak exception text either.
            http_status = None
        elapsed_ms = max(0, int(round((time.monotonic() - started_clock) * 1000)))
        completed_at = _utc_now_iso()

        normalized = _normalize_response(model_id, response_payload)
        success = bool(
            http_status == 200
            and normalized.response_model_exact
            and normalized.has_choice
            and not normalized.has_error
            and _usage_is_positive(normalized.usage)
            and normalized.cost_credits is not None
            and normalized.cost_credits > 0
        )
        accepted_response_shape = bool(
            normalized.response_model_exact
            and normalized.has_choice
            and not normalized.has_error
        )
        probes.append(
            {
                "model_id": model_id,
                "http_status": http_status,
                "success": success,
                "started_at": started_at,
                "completed_at": completed_at,
                "elapsed_ms": elapsed_ms,
                "usage": normalized.usage,
                "cost_credits": normalized.cost_credits,
                "paid": bool(
                    normalized.cost_credits is not None
                    and normalized.cost_credits > 0
                ),
                "request_semantics_sha256": request_semantics_sha256(model_id),
                # A response with an embedded error or no completion choice is
                # not accepted as an exact-model completion.
                "response_model_exact": accepted_response_shape,
                # Model fallback is absent from the request, provider failover is
                # disabled, and a successful response must echo the exact model.
                "fallback_used": False,
            }
        )

    successful_count = sum(item["success"] is True for item in probes)
    paid_count = sum(item["paid"] is True for item in probes)
    fallback_count = sum(item["fallback_used"] is True for item in probes)
    total_cost = round(
        sum(float(item["cost_credits"] or 0.0) for item in probes), 12
    )
    core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "blocked",
        "generated_at": _utc_now_iso(),
        "attempt_id": selected_attempt_id,
        "previous_attempt_sha256": previous_attempt_sha256,
        "required_models": list(REQUIRED_MODELS),
        "model_probe_count": len(probes),
        "successful_model_probe_count": successful_count,
        "paid_model_probe_count": paid_count,
        "fallback_model_probe_count": fallback_count,
        "request_attempt_count": len(probes),
        "total_cost_credits": total_cost,
        "material_retained": False,
        "credential_material_retained": False,
        "credential_value_hash_retained": False,
        "authorization_header_retained": False,
        "response_body_retained": False,
        "model_content_retained": False,
        "probes": probes,
    }
    core["secret_scan"] = {
        "status": "pass",
        "finding_count": _secret_finding_count(core),
    }
    core["secret_scan"]["status"] = (
        "pass" if core["secret_scan"]["finding_count"] == 0 else "fail"
    )
    core["gates"] = _build_gates(core)
    core["status"] = (
        "pass" if all(value is True for value in core["gates"].values()) else "blocked"
    )
    receipt = dict(core)
    receipt["integrity"] = {
        "algorithm": "sha256_canonical_json",
        "core_sha256": sha256_object(core),
    }
    validate_openrouter_credential_acceptance(receipt)
    return receipt


def validate_openrouter_credential_acceptance(payload: Mapping[str, Any]) -> None:
    """Validate the receipt with exact schemas and fail-closed semantics."""

    if set(payload) != _TOP_LEVEL_KEYS:
        raise CredentialAcceptanceError("credential receipt top-level schema mismatch")
    core = {key: value for key, value in payload.items() if key != "integrity"}
    integrity = payload.get("integrity")
    if (
        not isinstance(integrity, Mapping)
        or set(integrity) != {"algorithm", "core_sha256"}
        or integrity.get("algorithm") != "sha256_canonical_json"
        or integrity.get("core_sha256") != sha256_object(core)
    ):
        raise CredentialAcceptanceError("credential receipt integrity mismatch")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise CredentialAcceptanceError("credential receipt schema version mismatch")
    _validate_timestamp(payload.get("generated_at"))
    if _ATTEMPT_ID_RE.fullmatch(str(payload.get("attempt_id") or "")) is None:
        raise CredentialAcceptanceError("credential receipt attempt ID is invalid")
    previous_sha = payload.get("previous_attempt_sha256")
    if previous_sha is not None and _SHA256_RE.fullmatch(str(previous_sha)) is None:
        raise CredentialAcceptanceError(
            "credential receipt previous-attempt hash is invalid"
        )
    if payload.get("required_models") != list(REQUIRED_MODELS):
        raise CredentialAcceptanceError("credential receipt model order mismatch")

    probes = payload.get("probes")
    if not isinstance(probes, list) or len(probes) != len(REQUIRED_MODELS):
        raise CredentialAcceptanceError("credential receipt probe count mismatch")
    for model_id, raw_probe in zip(REQUIRED_MODELS, probes, strict=True):
        _validate_probe(raw_probe, model_id)

    for key in (
        "model_probe_count",
        "successful_model_probe_count",
        "paid_model_probe_count",
        "fallback_model_probe_count",
        "request_attempt_count",
    ):
        if isinstance(payload.get(key), bool) or not isinstance(payload.get(key), int):
            raise CredentialAcceptanceError(f"credential receipt {key} is invalid")
    if payload.get("model_probe_count") != len(probes):
        raise CredentialAcceptanceError("credential receipt model count mismatch")
    if payload.get("request_attempt_count") != len(probes):
        raise CredentialAcceptanceError("credential receipt request count mismatch")
    if payload.get("successful_model_probe_count") != sum(
        probe["success"] is True for probe in probes
    ):
        raise CredentialAcceptanceError("credential receipt success count mismatch")
    if payload.get("paid_model_probe_count") != sum(
        probe["paid"] is True for probe in probes
    ):
        raise CredentialAcceptanceError("credential receipt paid count mismatch")
    if payload.get("fallback_model_probe_count") != sum(
        probe["fallback_used"] is True for probe in probes
    ):
        raise CredentialAcceptanceError("credential receipt fallback count mismatch")
    expected_total_cost = round(
        sum(float(probe["cost_credits"] or 0.0) for probe in probes), 12
    )
    if payload.get("total_cost_credits") != expected_total_cost:
        raise CredentialAcceptanceError("credential receipt total cost mismatch")

    for key in (
        "material_retained",
        "credential_material_retained",
        "credential_value_hash_retained",
        "authorization_header_retained",
        "response_body_retained",
        "model_content_retained",
    ):
        if payload.get(key) is not False:
            raise CredentialAcceptanceError(f"credential receipt retained {key}")
    secret_scan = payload.get("secret_scan")
    if secret_scan != {"status": "pass", "finding_count": 0}:
        raise CredentialAcceptanceError("credential receipt secret scan failed")
    if _secret_finding_count({k: v for k, v in core.items() if k != "secret_scan"}):
        raise CredentialAcceptanceError("credential receipt contains sensitive material")

    gates = payload.get("gates")
    if not isinstance(gates, Mapping) or set(gates) != _GATE_KEYS:
        raise CredentialAcceptanceError("credential receipt gate schema mismatch")
    expected_gates = _build_gates(
        {key: value for key, value in core.items() if key != "gates"}
    )
    if dict(gates) != expected_gates:
        raise CredentialAcceptanceError("credential receipt gates mismatch")
    passed = all(value is True for value in gates.values())
    if payload.get("status") != ("pass" if passed else "blocked"):
        raise CredentialAcceptanceError("credential receipt status/gates mismatch")


def write_openrouter_credential_acceptance(
    path: str | Path, payload: Mapping[str, Any]
) -> str:
    """Atomically write a mode-0600 receipt and SHA-256 sidecar."""

    validate_openrouter_credential_acceptance(payload)
    destination = Path(path)
    encoded = json.dumps(
        payload, ensure_ascii=True, indent=2, sort_keys=True
    ) + "\n"
    _atomic_write_text(destination, encoded)
    digest = sha256_file(destination)
    _atomic_write_text(
        destination.with_name(destination.name + ".sha256"),
        f"{digest}  {destination.name}\n",
    )
    return digest


def validate_openrouter_credential_acceptance_file(path: str | Path) -> dict[str, Any]:
    destination = Path(path)
    try:
        payload = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CredentialAcceptanceError("credential receipt is not readable JSON") from exc
    if not isinstance(payload, Mapping):
        raise CredentialAcceptanceError("credential receipt root must be an object")
    validate_openrouter_credential_acceptance(payload)
    sidecar = destination.with_name(destination.name + ".sha256")
    expected = f"{sha256_file(destination)}  {destination.name}\n"
    try:
        actual = sidecar.read_text(encoding="utf-8")
    except OSError as exc:
        raise CredentialAcceptanceError("credential receipt sidecar is missing") from exc
    if actual != expected:
        raise CredentialAcceptanceError("credential receipt sidecar mismatch")
    if os.stat(destination).st_mode & 0o777 != 0o600:
        raise CredentialAcceptanceError("credential receipt mode is not 0600")
    if os.stat(sidecar).st_mode & 0o777 != 0o600:
        raise CredentialAcceptanceError("credential sidecar mode is not 0600")
    return dict(payload)


def request_semantics_sha256(model_id: str) -> str:
    if model_id not in REQUIRED_MODELS:
        raise CredentialAcceptanceError(f"unapproved probe model: {model_id}")
    return sha256_object(
        {
            "endpoint": OPENROUTER_CHAT_COMPLETIONS_URL,
            "method": "POST",
            "model": model_id,
            "message_roles": ["user"],
            "prompt_class": "fixed_non_sensitive_probe_with_unique_nonce/v1",
            "max_tokens": MAX_TOKENS,
            "stream": False,
            "provider": {
                "allow_fallbacks": False,
            },
            "models_parameter_present": False,
            "fallbacks_parameter_present": False,
            "tools_parameter_present": False,
            "plugins_parameter_present": False,
            "retry_count": 0,
        }
    )


def _request_payload(*, model_id: str, nonce: str) -> dict[str, Any]:
    return {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": f"Reply with one token. Probe nonce: {nonce}",
            }
        ],
        "max_tokens": MAX_TOKENS,
        "stream": False,
        "provider": {
            "allow_fallbacks": False,
        },
    }


def _normalize_response(
    requested_model: str, payload: Mapping[str, Any] | None
) -> _NormalizedResponse:
    empty_usage: dict[str, int | None] = {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
    }
    if not isinstance(payload, Mapping):
        return _NormalizedResponse(False, empty_usage, None, False, False)
    usage_raw = payload.get("usage")
    usage = dict(empty_usage)
    if isinstance(usage_raw, Mapping):
        for key in _USAGE_KEYS:
            value = usage_raw.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                usage[key] = value
    cost = None
    if isinstance(usage_raw, Mapping):
        raw_cost = usage_raw.get("cost")
        if (
            isinstance(raw_cost, (int, float))
            and not isinstance(raw_cost, bool)
            and math.isfinite(float(raw_cost))
            and float(raw_cost) >= 0
        ):
            cost = round(float(raw_cost), 12)
    choices = payload.get("choices")
    return _NormalizedResponse(
        response_model_exact=payload.get("model") == requested_model,
        usage=usage,
        cost_credits=cost,
        has_choice=isinstance(choices, list) and len(choices) > 0,
        has_error="error" in payload,
    )


def _usage_is_positive(usage: Mapping[str, int | None]) -> bool:
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    return bool(
        isinstance(prompt, int)
        and not isinstance(prompt, bool)
        and prompt > 0
        and isinstance(completion, int)
        and not isinstance(completion, bool)
        and completion >= 0
        and isinstance(total, int)
        and not isinstance(total, bool)
        and total == prompt + completion
        and total > 0
    )


def _build_gates(payload: Mapping[str, Any]) -> dict[str, bool]:
    probes_raw = payload.get("probes")
    probes: Sequence[Mapping[str, Any]] = (
        probes_raw
        if isinstance(probes_raw, list)
        and all(isinstance(item, Mapping) for item in probes_raw)
        else []
    )
    required = payload.get("required_models")
    return {
        "exact_required_model_order": required == list(REQUIRED_MODELS),
        "one_attempt_per_model": (
            len(probes) == len(REQUIRED_MODELS)
            and [probe.get("model_id") for probe in probes] == list(REQUIRED_MODELS)
            and payload.get("request_attempt_count") == len(REQUIRED_MODELS)
        ),
        "all_http_200": bool(probes)
        and all(probe.get("http_status") == 200 for probe in probes),
        "all_response_models_exact": bool(probes)
        and all(probe.get("response_model_exact") is True for probe in probes),
        "all_usage_positive": bool(probes)
        and all(_usage_is_positive(probe.get("usage") or {}) for probe in probes),
        "all_costs_positive": bool(probes)
        and all(
            isinstance(probe.get("cost_credits"), (int, float))
            and not isinstance(probe.get("cost_credits"), bool)
            and float(probe["cost_credits"]) > 0
            for probe in probes
        ),
        "exactly_three_paid_model_probes": payload.get("paid_model_probe_count") == 3,
        "fallback_model_count_zero": payload.get("fallback_model_probe_count") == 0
        and all(probe.get("fallback_used") is False for probe in probes),
        "tools_requested_zero": True,
        "plugins_requested_zero": True,
        "response_material_retained_zero": all(
            payload.get(key) is False
            for key in (
                "response_body_retained",
                "model_content_retained",
                "material_retained",
            )
        ),
        "credential_material_retained_zero": all(
            payload.get(key) is False
            for key in (
                "credential_material_retained",
                "credential_value_hash_retained",
                "authorization_header_retained",
            )
        ),
        "secret_scan_finding_count_zero": payload.get("secret_scan")
        == {"status": "pass", "finding_count": 0},
    }


def _validate_probe(raw_probe: Any, model_id: str) -> None:
    if not isinstance(raw_probe, Mapping) or set(raw_probe) != _PROBE_KEYS:
        raise CredentialAcceptanceError("credential probe schema mismatch")
    if raw_probe.get("model_id") != model_id:
        raise CredentialAcceptanceError("credential probe model mismatch")
    status = raw_probe.get("http_status")
    if status is not None and (
        isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599
    ):
        raise CredentialAcceptanceError("credential probe HTTP status is invalid")
    for key in ("success", "paid", "response_model_exact", "fallback_used"):
        if not isinstance(raw_probe.get(key), bool):
            raise CredentialAcceptanceError(f"credential probe {key} is invalid")
    for key in ("started_at", "completed_at"):
        _validate_timestamp(raw_probe.get(key))
    elapsed = raw_probe.get("elapsed_ms")
    if isinstance(elapsed, bool) or not isinstance(elapsed, int) or elapsed < 0:
        raise CredentialAcceptanceError("credential probe elapsed_ms is invalid")
    usage = raw_probe.get("usage")
    if not isinstance(usage, Mapping) or set(usage) != _USAGE_KEYS:
        raise CredentialAcceptanceError("credential probe usage schema mismatch")
    for value in usage.values():
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise CredentialAcceptanceError("credential probe usage value is invalid")
    cost = raw_probe.get("cost_credits")
    if cost is not None and (
        isinstance(cost, bool)
        or not isinstance(cost, (int, float))
        or not math.isfinite(float(cost))
        or float(cost) < 0
    ):
        raise CredentialAcceptanceError("credential probe cost is invalid")
    if raw_probe.get("paid") is not (cost is not None and float(cost) > 0):
        raise CredentialAcceptanceError("credential probe paid/cost mismatch")
    if raw_probe.get("fallback_used") is not False:
        raise CredentialAcceptanceError("credential probe used a fallback")
    if raw_probe.get("request_semantics_sha256") != request_semantics_sha256(
        model_id
    ):
        raise CredentialAcceptanceError("credential probe request semantics mismatch")
    success_expected = bool(
        status == 200
        and raw_probe.get("response_model_exact") is True
        and _usage_is_positive(usage)
        and cost is not None
        and float(cost) > 0
    )
    if raw_probe.get("success") is not success_expected:
        raise CredentialAcceptanceError("credential probe success semantics mismatch")


def _secret_finding_count(payload: Mapping[str, Any]) -> int:
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return sum(bool(pattern.search(serialized)) for pattern in _SECRET_PATTERNS)


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str):
        raise CredentialAcceptanceError("credential receipt timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CredentialAcceptanceError("credential receipt timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise CredentialAcceptanceError("credential receipt timestamp has no timezone")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
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
