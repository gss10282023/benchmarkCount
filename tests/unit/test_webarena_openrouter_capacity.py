from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import pytest

from evidence_system.webarena_openrouter_capacity import (
    OpenRouterCapacityError,
    OpenRouterCapacityTransportError,
    build_openrouter_capacity_acceptance,
    validate_openrouter_capacity_acceptance,
    validate_openrouter_capacity_acceptance_file,
    write_openrouter_capacity_acceptance,
)


SECRET = "sk-or-v1-this-capacity-secret-must-never-be-retained"
PRIVATE_BODY_VALUE = "private-current-key-response-value"


class FakeTransport:
    def __init__(
        self,
        *,
        status: int = 200,
        payload: Mapping[str, Any] | None = None,
        failure_status: int | None = None,
    ) -> None:
        self.status = status
        self.payload = payload or {
            "data": {
                "limit": 1000.0,
                "usage": 125.25,
                "limit_remaining": 874.75,
                "label": PRIVATE_BODY_VALUE,
            }
        }
        self.failure_status = failure_status
        self.calls: list[dict[str, Any]] = []

    def get_current_key(
        self, *, api_key: str, timeout_seconds: int
    ) -> tuple[int, Mapping[str, Any]]:
        self.calls.append(
            {"api_key": api_key, "timeout_seconds": timeout_seconds}
        )
        if self.failure_status is not None:
            raise OpenRouterCapacityTransportError(
                http_status=self.failure_status
            )
        return self.status, self.payload


def test_synthetic_capacity_response_is_reduced_to_exact_safe_fields() -> None:
    transport = FakeTransport()

    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=transport,
        timeout_seconds=12,
    )

    assert receipt["status"] == "pass"
    assert receipt["http_status"] == 200
    assert receipt["limit"] == 1000.0
    assert receipt["usage"] == 125.25
    assert receipt["limit_remaining"] == 874.75
    assert transport.calls == [{"api_key": SECRET, "timeout_seconds": 12}]
    assert set(receipt) == {
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
    serialized = json.dumps(receipt, sort_keys=True)
    assert SECRET not in serialized
    assert PRIVATE_BODY_VALUE not in serialized
    assert "Authorization" not in serialized
    assert "credential_hash" not in serialized
    assert receipt["credential_material_retained"] is False
    assert receipt["credential_value_hash_retained"] is False
    assert receipt["authorization_header_retained"] is False
    assert receipt["response_body_retained"] is False
    validate_openrouter_capacity_acceptance(receipt)


def test_unlimited_key_requires_and_records_explicit_waiver() -> None:
    payload = {
        "data": {
            "limit": None,
            "usage": 125.25,
            "limit_remaining": None,
        }
    }
    blocked = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=FakeTransport(payload=payload),
    )
    assert blocked["status"] == "blocked"
    assert blocked["provider_limit_mode"] == "unlimited_no_provider_cap"
    assert blocked["credit_floor_proof_status"] == "unavailable"
    assert blocked["unlimited_key_waiver_authorized"] is False
    validate_openrouter_capacity_acceptance(blocked)

    waived = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=FakeTransport(payload=payload),
        allow_unlimited_key_waiver=True,
    )
    assert waived["status"] == "pass"
    assert waived["provider_limit_mode"] == "unlimited_no_provider_cap"
    assert (
        waived["credit_floor_proof_status"]
        == "waived_by_user_provider_balance_unavailable"
    )
    assert (
        waived["credit_floor_waiver_reason"]
        == "provider_unlimited_key_exposes_no_limit_remaining_balance"
    )
    assert waived["unlimited_key_waiver_authorized"] is True
    validate_openrouter_capacity_acceptance(waived)


@pytest.mark.parametrize(
    "payload",
    [
        {"data": {"limit": 100.0, "usage": 10.0}},
        {"data": {"limit": "100", "usage": 10.0, "limit_remaining": 90.0}},
        {"data": {"limit": 100.0, "usage": 10.0, "limit_remaining": 95.0}},
        {"data": {"limit": 100.0, "usage": -1.0, "limit_remaining": 101.0}},
    ],
)
def test_missing_non_numeric_or_inconsistent_capacity_fails_closed(
    payload: Mapping[str, Any],
) -> None:
    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=FakeTransport(payload=payload),
    )

    assert receipt["status"] == "blocked"
    validate_openrouter_capacity_acceptance(receipt)


def test_http_failure_retains_only_status_and_no_error_body() -> None:
    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=FakeTransport(failure_status=401),
    )

    assert receipt["status"] == "blocked"
    assert receipt["http_status"] == 401
    assert receipt["limit"] is None
    assert receipt["usage"] is None
    assert receipt["limit_remaining"] is None
    serialized = json.dumps(receipt, sort_keys=True)
    assert SECRET not in serialized
    assert "error_body" not in serialized
    assert "error_message" not in serialized


def test_receipt_and_sidecar_are_mode_600_and_hash_bound(tmp_path: Path) -> None:
    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=FakeTransport(),
    )
    output = tmp_path / "capacity.json"

    digest = write_openrouter_capacity_acceptance(output, receipt)

    sidecar = output.with_name(output.name + ".sha256")
    assert sidecar.read_text(encoding="utf-8") == f"{digest}  {output.name}\n"
    assert os.stat(output).st_mode & 0o777 == 0o600
    assert os.stat(sidecar).st_mode & 0o777 == 0o600
    assert validate_openrouter_capacity_acceptance_file(output) == receipt


def test_tampering_extra_fields_secret_flags_and_sidecar_are_rejected(
    tmp_path: Path,
) -> None:
    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=FakeTransport(),
    )

    extra = dict(receipt)
    extra["credential_hash"] = "not-allowed"
    with pytest.raises(OpenRouterCapacityError, match="schema"):
        validate_openrouter_capacity_acceptance(extra)

    retained = dict(receipt)
    retained["response_body_retained"] = True
    with pytest.raises(OpenRouterCapacityError, match="retained"):
        validate_openrouter_capacity_acceptance(retained)

    output = tmp_path / "capacity.json"
    write_openrouter_capacity_acceptance(output, receipt)
    output.write_text(output.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(OpenRouterCapacityError, match="sidecar"):
        validate_openrouter_capacity_acceptance_file(output)


def test_cli_stdout_and_receipt_never_contain_dotenv_secret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from evidence_system.cli import webarena_openrouter_capacity as cli

    receipt = build_openrouter_capacity_acceptance(
        api_key=SECRET,
        transport=FakeTransport(),
    )
    dotenv = tmp_path / ".env"
    dotenv.write_text(f"OPENROUTER_API_KEY={SECRET}\n", encoding="utf-8")
    output = tmp_path / "capacity.json"
    observed: dict[str, Any] = {}

    def fake_build(
        *,
        api_key: str,
        timeout_seconds: int,
        allow_unlimited_key_waiver: bool,
    ) -> dict[str, Any]:
        observed["api_key"] = api_key
        observed["timeout_seconds"] = timeout_seconds
        observed["allow_unlimited_key_waiver"] = (
            allow_unlimited_key_waiver
        )
        return receipt

    monkeypatch.setattr(cli, "build_openrouter_capacity_acceptance", fake_build)
    code = cli.main(
        [
            "probe",
            "--dotenv",
            str(dotenv),
            "--output",
            str(output),
        ]
    )
    stdout = capsys.readouterr().out

    assert code == 0
    assert observed == {
        "api_key": SECRET,
        "timeout_seconds": 30,
        "allow_unlimited_key_waiver": False,
    }
    assert SECRET not in stdout
    assert SECRET not in output.read_text(encoding="utf-8")
    assert PRIVATE_BODY_VALUE not in output.read_text(encoding="utf-8")
    public_stdout = json.loads(stdout)
    assert public_stdout["credential_value_hash_printed"] is False
    assert public_stdout["response_body_printed"] is False
