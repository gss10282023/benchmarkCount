from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Mapping

import pytest

from evidence_system.core.hashing import sha256_object
from evidence_system.webarena_openrouter_credential import (
    CredentialAcceptanceError,
    CredentialProbeTransportError,
    MAX_TOKENS,
    REQUIRED_MODELS,
    build_openrouter_credential_acceptance,
    request_semantics_sha256,
    validate_openrouter_credential_acceptance,
    validate_openrouter_credential_acceptance_file,
    write_openrouter_credential_acceptance,
)


SECRET = "sk-or-v1-this-secret-must-never-be-retained"
MODEL_CONTENT = "private model content that must not be retained"


class FakeTransport:
    def __init__(
        self,
        *,
        response_model_overrides: Mapping[str, str] | None = None,
        zero_cost_models: set[str] | None = None,
        http_failures: Mapping[str, int | None] | None = None,
    ) -> None:
        self.response_model_overrides = dict(response_model_overrides or {})
        self.zero_cost_models = set(zero_cost_models or set())
        self.http_failures = dict(http_failures or {})
        self.calls: list[dict[str, Any]] = []

    def post_json(
        self,
        *,
        api_key: str,
        payload: Mapping[str, Any],
        timeout_seconds: int,
    ) -> tuple[int, Mapping[str, Any]]:
        model = str(payload["model"])
        self.calls.append(
            {
                "api_key": api_key,
                "payload": copy.deepcopy(dict(payload)),
                "timeout_seconds": timeout_seconds,
            }
        )
        if model in self.http_failures:
            raise CredentialProbeTransportError(
                http_status=self.http_failures[model]
            )
        return 200, {
            "id": "response-id-must-not-be-retained",
            "model": self.response_model_overrides.get(model, model),
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": MODEL_CONTENT,
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 1,
                "total_tokens": 11,
                "cost": 0.0 if model in self.zero_cost_models else 0.000001,
            },
        }


def _passing_receipt() -> tuple[dict[str, Any], FakeTransport]:
    transport = FakeTransport()
    receipt = build_openrouter_credential_acceptance(
        api_key=SECRET,
        transport=transport,
        nonce_factory=lambda: "test-nonce",
    )
    return receipt, transport


def test_exact_three_model_paid_probe_is_secret_and_content_free() -> None:
    receipt, transport = _passing_receipt()

    assert receipt["status"] == "pass"
    assert receipt["required_models"] == list(REQUIRED_MODELS)
    assert receipt["model_probe_count"] == 3
    assert receipt["successful_model_probe_count"] == 3
    assert receipt["paid_model_probe_count"] == 3
    assert receipt["fallback_model_probe_count"] == 0
    assert receipt["request_attempt_count"] == 3
    assert receipt["secret_scan"] == {"status": "pass", "finding_count": 0}
    assert all(receipt["gates"].values())
    assert len(transport.calls) == 3

    for expected_model, call, probe in zip(
        REQUIRED_MODELS, transport.calls, receipt["probes"], strict=True
    ):
        request = call["payload"]
        assert request["model"] == expected_model
        assert request["max_tokens"] == MAX_TOKENS == 1
        assert request["stream"] is False
        assert request["provider"] == {
            "allow_fallbacks": False,
        }
        assert "temperature" not in request
        assert "models" not in request
        assert "fallbacks" not in request
        assert "tools" not in request
        assert "plugins" not in request
        assert probe["request_semantics_sha256"] == request_semantics_sha256(
            expected_model
        )

    serialized = json.dumps(receipt, sort_keys=True)
    assert SECRET not in serialized
    assert MODEL_CONTENT not in serialized
    assert "response-id-must-not-be-retained" not in serialized
    assert "Authorization" not in serialized
    assert receipt["credential_value_hash_retained"] is False
    assert "credential_value_hash_sha256" not in serialized
    validate_openrouter_credential_acceptance(receipt)


def test_exact_response_model_mismatch_fails_closed_without_substitution() -> None:
    model = REQUIRED_MODELS[1]
    transport = FakeTransport(response_model_overrides={model: "some/alias"})

    receipt = build_openrouter_credential_acceptance(
        api_key=SECRET,
        transport=transport,
        nonce_factory=lambda: "test-nonce",
    )

    assert receipt["status"] == "blocked"
    assert receipt["successful_model_probe_count"] == 2
    assert receipt["paid_model_probe_count"] == 3
    assert receipt["fallback_model_probe_count"] == 0
    failed = next(probe for probe in receipt["probes"] if probe["model_id"] == model)
    assert failed["success"] is False
    assert failed["response_model_exact"] is False
    assert failed["fallback_used"] is False
    validate_openrouter_credential_acceptance(receipt)


def test_zero_cost_is_not_accepted_as_a_paid_probe() -> None:
    model = REQUIRED_MODELS[2]
    transport = FakeTransport(zero_cost_models={model})

    receipt = build_openrouter_credential_acceptance(
        api_key=SECRET,
        transport=transport,
        nonce_factory=lambda: "test-nonce",
    )

    assert receipt["status"] == "blocked"
    assert receipt["paid_model_probe_count"] == 2
    assert receipt["successful_model_probe_count"] == 2
    assert receipt["gates"]["exactly_three_paid_model_probes"] is False
    assert receipt["gates"]["all_costs_positive"] is False


def test_http_failure_is_recorded_without_error_body_or_exception_text() -> None:
    model = REQUIRED_MODELS[0]
    transport = FakeTransport(http_failures={model: 401})

    receipt = build_openrouter_credential_acceptance(
        api_key=SECRET,
        transport=transport,
        nonce_factory=lambda: "test-nonce",
    )

    failed = receipt["probes"][0]
    assert receipt["status"] == "blocked"
    assert failed["http_status"] == 401
    assert failed["success"] is False
    serialized = json.dumps(receipt, sort_keys=True)
    assert SECRET not in serialized
    assert "error_body" not in serialized
    assert "error_message" not in serialized


def test_write_is_mode_600_hash_bound_and_sidecar_valid(tmp_path: Path) -> None:
    receipt, _ = _passing_receipt()
    path = tmp_path / "credential.json"

    digest = write_openrouter_credential_acceptance(path, receipt)

    assert os.stat(path).st_mode & 0o777 == 0o600
    assert os.stat(path.with_name(path.name + ".sha256")).st_mode & 0o777 == 0o600
    assert path.with_name(path.name + ".sha256").read_text(encoding="utf-8") == (
        f"{digest}  {path.name}\n"
    )
    assert validate_openrouter_credential_acceptance_file(path) == receipt


def test_tampering_extra_fields_and_sensitive_material_are_rejected() -> None:
    receipt, _ = _passing_receipt()

    tampered = copy.deepcopy(receipt)
    tampered["probes"][0]["http_status"] = 201
    with pytest.raises(CredentialAcceptanceError, match="integrity"):
        validate_openrouter_credential_acceptance(tampered)

    extra = copy.deepcopy(receipt)
    extra["credential_value"] = SECRET
    core = {key: value for key, value in extra.items() if key != "integrity"}
    extra["integrity"] = {
        "algorithm": "sha256_canonical_json",
        "core_sha256": sha256_object(core),
    }
    with pytest.raises(CredentialAcceptanceError, match="schema"):
        validate_openrouter_credential_acceptance(extra)


def test_cli_stdout_never_contains_dotenv_secret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from evidence_system.cli import webarena_openrouter_credential_acceptance as cli

    receipt, _ = _passing_receipt()
    dotenv = tmp_path / ".env"
    dotenv.write_text(f"OPENROUTER_API_KEY={SECRET}\n", encoding="utf-8")
    output = tmp_path / "receipt.json"
    observed: dict[str, str] = {}

    def fake_build(
        *,
        api_key: str,
        timeout_seconds: int,
        attempt_id: str | None,
        previous_attempt_sha256: str | None,
    ) -> dict[str, Any]:
        observed["api_key"] = api_key
        assert timeout_seconds == 180
        assert attempt_id is None
        assert previous_attempt_sha256 is None
        return receipt

    monkeypatch.setattr(cli, "build_openrouter_credential_acceptance", fake_build)
    code = cli.main(
        ["probe", "--dotenv", str(dotenv), "--output", str(output)]
    )
    stdout = capsys.readouterr().out

    assert code == 0
    assert observed["api_key"] == SECRET
    assert SECRET not in stdout
    assert MODEL_CONTENT not in stdout
    assert output.is_file()
