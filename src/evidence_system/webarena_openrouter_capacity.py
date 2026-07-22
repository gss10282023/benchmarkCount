"""Secret-free, read-only OpenRouter key-capacity probe for WebArena.

The probe performs one GET of OpenRouter's current-key endpoint.  The response
is parsed in memory and discarded.  Its receipt is deliberately limited to a
timestamp, HTTP status, three numeric capacity fields, and explicit
secret-retention flags.  Credential values, credential hashes, Authorization
headers, endpoint response bodies, and response metadata are never retained.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Protocol
import urllib.error
import urllib.request

from evidence_system.core.hashing import sha256_file


SCHEMA_VERSION = "webarena_verified_openrouter_capacity_acceptance/v2"
OPENROUTER_CURRENT_KEY_URL = "https://openrouter.ai/api/v1/key"
UNLIMITED_KEY_WAIVER_REASON = (
    "provider_unlimited_key_exposes_no_limit_remaining_balance"
)

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "timestamp",
        "http_status",
        "limit",
        "usage",
        "limit_remaining",
        "provider_limit_mode",
        "credit_floor_proof_status",
        "credit_floor_waiver_reason",
        "unlimited_key_waiver_authorized",
        "credential_material_retained",
        "credential_value_hash_retained",
        "authorization_header_retained",
        "response_body_retained",
    }
)
_SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{8,}", re.IGNORECASE),
    re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE),
    re.compile(
        r'"(?:api_key|authorization|credential_value|credential_hash|'
        r'openrouter_api_key|response_body)"\s*:',
        re.IGNORECASE,
    ),
)


class OpenRouterCapacityError(RuntimeError):
    """The capacity probe or its public-safe receipt is invalid."""


class OpenRouterCapacityTransportError(RuntimeError):
    """A sanitized transport failure that contains no response material."""

    def __init__(self, *, http_status: int | None) -> None:
        self.http_status = http_status
        super().__init__("OpenRouter current-key capacity probe failed")


class CapacityProbeTransport(Protocol):
    def get_current_key(
        self, *, api_key: str, timeout_seconds: int
    ) -> tuple[int, Mapping[str, Any]]:
        """Return an in-memory decoded current-key response."""


class UrllibCapacityProbeTransport:
    """One read-only GET; HTTP error bodies are neither read nor exposed."""

    def get_current_key(
        self, *, api_key: str, timeout_seconds: int
    ) -> tuple[int, Mapping[str, Any]]:
        request = urllib.request.Request(
            OPENROUTER_CURRENT_KEY_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status = int(response.status)
                raw = response.read()
        except urllib.error.HTTPError as exc:
            # Deliberately do not read, stringify, or retain the error body.
            raise OpenRouterCapacityTransportError(
                http_status=int(exc.code)
            ) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise OpenRouterCapacityTransportError(http_status=None) from None
        try:
            loaded = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise OpenRouterCapacityTransportError(http_status=status) from None
        if not isinstance(loaded, Mapping):
            raise OpenRouterCapacityTransportError(http_status=status)
        return status, loaded


def build_openrouter_capacity_acceptance(
    *,
    api_key: str,
    transport: CapacityProbeTransport | None = None,
    timeout_seconds: int = 30,
    allow_unlimited_key_waiver: bool = False,
) -> dict[str, Any]:
    """Perform exactly one read-only current-key probe and return its receipt."""

    if not isinstance(api_key, str) or not api_key.strip():
        raise OpenRouterCapacityError("OPENROUTER_API_KEY is not set")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int):
        raise OpenRouterCapacityError("timeout_seconds must be an integer")
    if timeout_seconds <= 0:
        raise OpenRouterCapacityError("timeout_seconds must be positive")
    if not isinstance(allow_unlimited_key_waiver, bool):
        raise OpenRouterCapacityError(
            "allow_unlimited_key_waiver must be boolean"
        )

    selected_transport = transport or UrllibCapacityProbeTransport()
    http_status: int | None = None
    payload: Mapping[str, Any] | None = None
    try:
        http_status, payload = selected_transport.get_current_key(
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
    except OpenRouterCapacityTransportError as exc:
        http_status = exc.http_status
    except Exception:
        # Third-party test transports must not leak exception text or material.
        http_status = None

    limit, usage, limit_remaining = _capacity_numbers(payload)
    explicit_cap_valid = bool(
        http_status == 200
        and limit is not None
        and usage is not None
        and limit_remaining is not None
        and _capacity_is_consistent(limit, usage, limit_remaining)
    )
    unlimited_key_valid = bool(
        http_status == 200
        and limit is None
        and usage is not None
        and limit_remaining is None
        and _payload_declares_unlimited_key(payload)
    )
    provider_limit_mode = (
        "explicit_cap"
        if explicit_cap_valid
        else "unlimited_no_provider_cap"
        if unlimited_key_valid
        else "invalid"
    )
    unlimited_waiver = bool(
        unlimited_key_valid and allow_unlimited_key_waiver
    )
    passed = explicit_cap_valid or unlimited_waiver
    credit_floor_proof_status = (
        "verified_from_provider_key_cap"
        if explicit_cap_valid
        else "waived_by_user_provider_balance_unavailable"
        if unlimited_waiver
        else "unavailable"
    )
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if passed else "blocked",
        "timestamp": _utc_now_iso(),
        "http_status": http_status,
        "limit": limit,
        "usage": usage,
        "limit_remaining": limit_remaining,
        "provider_limit_mode": provider_limit_mode,
        "credit_floor_proof_status": credit_floor_proof_status,
        "credit_floor_waiver_reason": (
            UNLIMITED_KEY_WAIVER_REASON if unlimited_waiver else None
        ),
        "unlimited_key_waiver_authorized": unlimited_waiver,
        "credential_material_retained": False,
        "credential_value_hash_retained": False,
        "authorization_header_retained": False,
        "response_body_retained": False,
    }
    validate_openrouter_capacity_acceptance(receipt)
    return receipt


def validate_openrouter_capacity_acceptance(payload: Mapping[str, Any]) -> None:
    """Fail closed unless a receipt has the exact secret-free schema."""

    if set(payload) != _TOP_LEVEL_KEYS:
        raise OpenRouterCapacityError("capacity receipt top-level schema mismatch")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise OpenRouterCapacityError("capacity receipt schema version mismatch")
    _validate_timestamp(payload.get("timestamp"))

    http_status = payload.get("http_status")
    if http_status is not None and (
        isinstance(http_status, bool)
        or not isinstance(http_status, int)
        or not 100 <= http_status <= 599
    ):
        raise OpenRouterCapacityError("capacity receipt HTTP status is invalid")

    numeric = {
        key: _validated_optional_number(payload.get(key), key)
        for key in ("limit", "usage", "limit_remaining")
    }
    provider_limit_mode = payload.get("provider_limit_mode")
    if provider_limit_mode not in {
        "explicit_cap",
        "unlimited_no_provider_cap",
        "invalid",
    }:
        raise OpenRouterCapacityError("capacity receipt limit mode is invalid")
    proof_status = payload.get("credit_floor_proof_status")
    if proof_status not in {
        "verified_from_provider_key_cap",
        "waived_by_user_provider_balance_unavailable",
        "unavailable",
    }:
        raise OpenRouterCapacityError(
            "capacity receipt credit-floor proof status is invalid"
        )
    waiver_reason = payload.get("credit_floor_waiver_reason")
    if waiver_reason is not None and waiver_reason != UNLIMITED_KEY_WAIVER_REASON:
        raise OpenRouterCapacityError(
            "capacity receipt credit-floor waiver reason is invalid"
        )
    waiver_authorized = payload.get("unlimited_key_waiver_authorized")
    if not isinstance(waiver_authorized, bool):
        raise OpenRouterCapacityError(
            "capacity receipt unlimited-key waiver flag is invalid"
        )
    for key in (
        "credential_material_retained",
        "credential_value_hash_retained",
        "authorization_header_retained",
        "response_body_retained",
    ):
        if payload.get(key) is not False:
            raise OpenRouterCapacityError(f"capacity receipt retained {key}")

    explicit_cap_valid = bool(
        http_status == 200
        and all(value is not None for value in numeric.values())
        and _capacity_is_consistent(
            numeric["limit"],
            numeric["usage"],
            numeric["limit_remaining"],
        )
    )
    unlimited_key_valid = bool(
        http_status == 200
        and numeric["limit"] is None
        and numeric["usage"] is not None
        and numeric["limit_remaining"] is None
    )
    if explicit_cap_valid:
        expected_mode = "explicit_cap"
        expected_proof = "verified_from_provider_key_cap"
        expected_waiver = False
        expected_reason = None
    elif unlimited_key_valid:
        expected_mode = "unlimited_no_provider_cap"
        expected_waiver = waiver_authorized
        expected_proof = (
            "waived_by_user_provider_balance_unavailable"
            if expected_waiver
            else "unavailable"
        )
        expected_reason = (
            UNLIMITED_KEY_WAIVER_REASON if expected_waiver else None
        )
    else:
        expected_mode = "invalid"
        expected_proof = "unavailable"
        expected_waiver = False
        expected_reason = None
    if (
        provider_limit_mode != expected_mode
        or proof_status != expected_proof
        or waiver_authorized is not expected_waiver
        or waiver_reason != expected_reason
    ):
        raise OpenRouterCapacityError(
            "capacity receipt limit-mode/waiver fields are inconsistent"
        )
    expected_pass = explicit_cap_valid or (
        unlimited_key_valid and expected_waiver
    )
    if payload.get("status") != ("pass" if expected_pass else "blocked"):
        raise OpenRouterCapacityError("capacity receipt status mismatch")

    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    if any(pattern.search(serialized) for pattern in _SECRET_PATTERNS):
        raise OpenRouterCapacityError("capacity receipt contains sensitive material")


def write_openrouter_capacity_acceptance(
    path: str | Path, payload: Mapping[str, Any]
) -> str:
    """Atomically write a mode-0600 receipt and artifact-hash sidecar."""

    validate_openrouter_capacity_acceptance(payload)
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


def validate_openrouter_capacity_acceptance_file(
    path: str | Path,
) -> dict[str, Any]:
    destination = Path(path)
    try:
        loaded = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OpenRouterCapacityError(
            "capacity receipt is not readable JSON"
        ) from exc
    if not isinstance(loaded, Mapping):
        raise OpenRouterCapacityError("capacity receipt root must be an object")
    validate_openrouter_capacity_acceptance(loaded)

    sidecar = destination.with_name(destination.name + ".sha256")
    expected = f"{sha256_file(destination)}  {destination.name}\n"
    try:
        actual = sidecar.read_text(encoding="utf-8")
    except OSError as exc:
        raise OpenRouterCapacityError("capacity receipt sidecar is missing") from exc
    if actual != expected:
        raise OpenRouterCapacityError("capacity receipt sidecar mismatch")
    if os.stat(destination).st_mode & 0o777 != 0o600:
        raise OpenRouterCapacityError("capacity receipt mode is not 0600")
    if os.stat(sidecar).st_mode & 0o777 != 0o600:
        raise OpenRouterCapacityError("capacity sidecar mode is not 0600")
    return dict(loaded)


def _capacity_numbers(
    payload: Mapping[str, Any] | None,
) -> tuple[float | None, float | None, float | None]:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    if not isinstance(data, Mapping):
        return None, None, None
    return (
        _optional_number(data.get("limit")),
        _optional_number(data.get("usage")),
        _optional_number(data.get("limit_remaining")),
    )


def _optional_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        return None
    return normalized


def _payload_declares_unlimited_key(
    payload: Mapping[str, Any] | None,
) -> bool:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    return bool(
        isinstance(data, Mapping)
        and "limit" in data
        and data.get("limit") is None
        and "usage" in data
        and "limit_remaining" in data
        and data.get("limit_remaining") is None
    )


def _validated_optional_number(value: Any, label: str) -> float | None:
    if value is None:
        return None
    normalized = _optional_number(value)
    if normalized is None or not isinstance(value, (int, float)):
        raise OpenRouterCapacityError(f"capacity receipt {label} is invalid")
    return normalized


def _capacity_is_consistent(
    limit: float | None,
    usage: float | None,
    limit_remaining: float | None,
) -> bool:
    if limit is None or usage is None or limit_remaining is None:
        return False
    if usage > limit + 1e-9 or limit_remaining > limit + 1e-9:
        return False
    return abs((limit - usage) - limit_remaining) <= 0.02


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise OpenRouterCapacityError("capacity receipt timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise OpenRouterCapacityError(
            "capacity receipt timestamp is invalid"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise OpenRouterCapacityError("capacity receipt timestamp is not UTC")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.tmp-", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


__all__ = [
    "CapacityProbeTransport",
    "OPENROUTER_CURRENT_KEY_URL",
    "OpenRouterCapacityError",
    "OpenRouterCapacityTransportError",
    "SCHEMA_VERSION",
    "UNLIMITED_KEY_WAIVER_REASON",
    "UrllibCapacityProbeTransport",
    "build_openrouter_capacity_acceptance",
    "validate_openrouter_capacity_acceptance",
    "validate_openrouter_capacity_acceptance_file",
    "write_openrouter_capacity_acceptance",
]
