from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import zipfile

import pytest

from evidence_system.adapters import webarena_official_worker
from evidence_system.adapters import webarena_har_sanitization as sanitizer
from evidence_system.adapters.webarena_har_sanitization import (
    HarSanitizationError,
    REDACTION_MARKER,
    load_and_validate_network_sanitization_receipt,
    sanitize_network_artifacts_before_evaluator,
    validate_network_sanitization_receipt,
)


COOKIE_VALUE = "session-cookie-value-123456"
AUTH_VALUE = "Bearer authorization-value-123456"
CSRF_VALUE = "csrf-value-123456"
SET_COOKIE_VALUE = "session=response-cookie-value-123456; HttpOnly"
TRACE_ONLY_VALUE = "seven77"
UNICODE_VALUE = "秘密令牌"


def _har() -> dict[str, Any]:
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "Playwright", "version": "1.56.0"},
            "entries": [
                {
                    "startedDateTime": "2026-07-16T00:00:00.000Z",
                    "time": 17,
                    "request": {
                        "method": "POST",
                        "url": "http://127.0.0.1:8023/api/issues?scope=all",
                        "httpVersion": "HTTP/1.1",
                        "cookies": [
                            {
                                "name": "session",
                                "value": COOKIE_VALUE,
                                "domain": "127.0.0.1",
                            }
                        ],
                        "headers": [
                            {"name": "Accept", "value": "application/json"},
                            {"name": "Cookie", "value": COOKIE_VALUE},
                            {"name": "Authorization", "value": AUTH_VALUE},
                            {"name": "X-CSRF-Token", "value": CSRF_VALUE},
                        ],
                        "headersText": (
                            f"Cookie: {COOKIE_VALUE}\r\n"
                            "Accept: application/json\r\n"
                        ),
                        "queryString": [{"name": "scope", "value": "all"}],
                        "postData": {
                            "mimeType": "application/json",
                            "text": '{"title":"body must remain byte-for-byte"}',
                        },
                        "headersSize": -1,
                        "bodySize": 42,
                    },
                    "response": {
                        "status": 201,
                        "statusText": "Created",
                        "httpVersion": "HTTP/1.1",
                        "cookies": [
                            {
                                "name": "session",
                                "value": SET_COOKIE_VALUE,
                                "httpOnly": True,
                            }
                        ],
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"},
                            {"name": "Set-Cookie", "value": SET_COOKIE_VALUE},
                        ],
                        "content": {
                            "size": 28,
                            "mimeType": "application/json",
                            "text": '{"id":7,"state":"opened"}',
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": 28,
                    },
                    "cache": {},
                    "timings": {"send": 1, "wait": 15, "receive": 1},
                }
            ],
        }
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_trace(path: Path, *, opaque_value: bytes | None = None) -> dict[str, bytes]:
    path.parent.mkdir(parents=True, exist_ok=True)
    trace_event = {
        "type": "resource-snapshot",
        "snapshot": {
            "request": {
                "method": "POST",
                "url": "http://127.0.0.1:8023/api/issues?scope=all",
                "headers": [
                    {"name": "cookie", "value": COOKIE_VALUE},
                    {"name": "authorization", "value": AUTH_VALUE},
                    {"name": "x-auth-token", "value": TRACE_ONLY_VALUE},
                    {"name": "x-csrf-token", "value": CSRF_VALUE},
                    {"name": "accept", "value": "application/json"},
                ],
                "cookies": [{"name": "session", "value": COOKIE_VALUE}],
                "postData": '{"title":"body must remain byte-for-byte"}',
            },
            "response": {
                "status": 201,
                "headers": [
                    {"name": "set-cookie", "value": SET_COOKIE_VALUE},
                    {"name": "content-type", "value": "application/json"},
                ],
                "cookies": [{"name": "session", "value": SET_COOKIE_VALUE}],
                "timing": {"startTime": 1, "responseEnd": 17},
            },
        },
    }
    trace_action = {
        "type": "after",
        "callId": "call@1",
        "url": "http://127.0.0.1:8023/dashboard/issues",
    }
    metadata = {
        "event": {"url": "http://127.0.0.1:8023/dashboard/issues"},
        "businessBody": {
            "authorization": "ordinary business field must remain",
            "cookies": {"preference": "ordinary business value must remain"},
        },
    }
    members = {
        "trace.trace": (
            json.dumps(trace_event, separators=(",", ":"))
            + "\n"
            + json.dumps(trace_action, separators=(",", ":"))
            + "\n"
        ).encode(),
        "trace.network": (json.dumps(trace_event) + "\n").encode(),
        "metadata.json": json.dumps(metadata).encode(),
        "resources/body.bin": (
            opaque_value if opaque_value is not None else b"opaque-resource-body"
        ),
        "resources/screenshot.jpeg": b"\xff\xd8\xff\xe0fake-screenshot\xff\xd9",
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = b"playwright-trace"
        for name, data in members.items():
            archive.writestr(name, data)
    return members


def _artifacts(
    tmp_path: Path, *, opaque_value: bytes | None = None
) -> tuple[Path, Path]:
    har_path = tmp_path / "42" / "network.har"
    trace_path = tmp_path / "traces" / "42.zip"
    _write_json(har_path, _har())
    _write_trace(trace_path, opaque_value=opaque_value)
    return har_path, trace_path


def test_har_and_trace_are_atomically_redacted_without_semantic_drift(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    original_har = _har()
    original_members = _write_trace(tmp_path / "original.zip")

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    receipt_path = har_path.with_name("network_har_sanitization.json")
    assert receipt["status"] == "pass"
    assert receipt["sanitization_completed_before_evaluator"] is True
    assert receipt["trace_sanitized"] is True
    assert receipt["active_original_value_exact_match_count_after_sanitization"] == 0
    assert receipt["counts"]["total_values"] > 0
    serialized_receipt = json.dumps(receipt, sort_keys=True)
    for secret in (
        COOKIE_VALUE,
        AUTH_VALUE,
        CSRF_VALUE,
        SET_COOKIE_VALUE,
        TRACE_ONLY_VALUE,
    ):
        assert secret not in serialized_receipt

    archived_har = json.loads(har_path.read_text(encoding="utf-8"))
    original_entry = original_har["log"]["entries"][0]
    archived_entry = archived_har["log"]["entries"][0]
    assert archived_entry["request"]["method"] == original_entry["request"]["method"]
    assert archived_entry["request"]["url"] == original_entry["request"]["url"]
    assert archived_entry["request"]["postData"] == original_entry["request"]["postData"]
    assert archived_entry["response"]["status"] == original_entry["response"]["status"]
    assert archived_entry["response"]["content"] == original_entry["response"]["content"]
    assert archived_entry["timings"] == original_entry["timings"]
    assert archived_entry["request"]["cookies"][0]["value"] == REDACTION_MARKER
    assert archived_entry["response"]["cookies"][0]["value"] == REDACTION_MARKER
    assert all(
        header["value"] == REDACTION_MARKER
        for side in ("request", "response")
        for header in archived_entry[side]["headers"]
        if header["name"].lower()
        in {"cookie", "set-cookie", "authorization", "x-csrf-token"}
    )

    with zipfile.ZipFile(trace_path) as archive:
        assert archive.testzip() is None
        assert archive.comment == b"playwright-trace"
        assert archive.namelist() == list(original_members)
        assert archive.read("resources/body.bin") == original_members["resources/body.bin"]
        assert archive.read("resources/screenshot.jpeg") == original_members[
            "resources/screenshot.jpeg"
        ]
        archived_bytes = b"".join(archive.read(name) for name in archive.namelist())
        for secret in (
            COOKIE_VALUE,
            AUTH_VALUE,
            CSRF_VALUE,
            SET_COOKIE_VALUE,
            TRACE_ONLY_VALUE,
        ):
            assert secret.encode() not in archived_bytes
        trace_lines = [
            json.loads(line)
            for line in archive.read("trace.trace").decode().splitlines()
        ]
        snapshot = trace_lines[0]["snapshot"]
        assert snapshot["request"]["method"] == "POST"
        assert snapshot["request"]["url"].endswith("/api/issues?scope=all")
        assert snapshot["request"]["postData"] == (
            '{"title":"body must remain byte-for-byte"}'
        )
        assert snapshot["response"]["status"] == 201
        assert snapshot["response"]["timing"] == {
            "startTime": 1,
            "responseEnd": 17,
        }
        assert snapshot["request"]["headers"][0]["value"] == REDACTION_MARKER
        assert snapshot["request"]["cookies"][0]["value"] == REDACTION_MARKER
        metadata = json.loads(archive.read("metadata.json"))
        assert metadata["event"]["url"].endswith("/dashboard/issues")
        assert metadata["businessBody"] == {
            "authorization": "ordinary business field must remain",
            "cookies": {"preference": "ordinary business value must remain"},
        }

    assert os.stat(har_path).st_mode & 0o777 == 0o600
    assert os.stat(trace_path).st_mode & 0o777 == 0o600
    assert os.stat(receipt_path).st_mode & 0o777 == 0o600
    assert receipt["sanitized_har_size_bytes"] == har_path.stat().st_size
    assert receipt["sanitized_trace_size_bytes"] == trace_path.stat().st_size
    assert load_and_validate_network_sanitization_receipt(
        receipt_path,
        har_path=har_path,
        trace_path=trace_path,
    ) == receipt


def test_embedded_business_body_header_named_fields_are_not_rewritten(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    with zipfile.ZipFile(trace_path, "r") as source:
        members = {name: source.read(name) for name in source.namelist()}
    lines = members["trace.trace"].decode().splitlines()
    event = json.loads(lines[0])
    event["snapshot"]["request"]["postData"] = {
        "authorization": "business-auth",
        "cookies": [{"name": "display", "value": "business-cookie"}],
        "requestHeaders": {"x-api-key": "business-display-value"},
        "requestHeadersText": "Authorization: business-display-value\r\n",
    }
    members["trace.trace"] = (
        json.dumps(event) + "\n" + lines[1] + "\n"
    ).encode()
    with zipfile.ZipFile(trace_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
        target.comment = b"playwright-trace"
        for name, data in members.items():
            target.writestr(name, data)

    sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    with zipfile.ZipFile(trace_path) as archive:
        archived = json.loads(archive.read("trace.trace").decode().splitlines()[0])
    assert archived["snapshot"]["request"]["postData"] == {
        "authorization": "business-auth",
        "cookies": [{"name": "display", "value": "business-cookie"}],
        "requestHeaders": {"x-api-key": "business-display-value"},
        "requestHeadersText": "Authorization: business-display-value\r\n",
    }


def test_playwright_context_credentials_and_storage_state_are_redacted(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    secrets = {
        "context_auth": "Bearer CONTEXT-AUTH-987654",
        "http_user": "HTTP-USER-987654",
        "http_password": "HTTP-PASSWORD-987654",
        "proxy_user": "PROXY-USER-987654",
        "proxy_password": "PROXY-PASSWORD-987654",
        "cookie": "TRACEONLYCOOKIE987654",
        "auth_token": "LOCAL-AUTH-TOKEN-987654",
        "session": "LOCAL-SESSION-987654",
        "csrf": "LOCAL-CSRF-987654",
    }
    context_event = {
        "type": "context-options",
        "options": {
            "extraHTTPHeaders": [
                {"name": "Authorization", "value": secrets["context_auth"]},
                {"name": "Accept", "value": "application/json"},
            ],
            "httpCredentials": {
                "username": secrets["http_user"],
                "password": secrets["http_password"],
            },
            "proxy": {
                "server": "http://proxy.example:8080",
                "username": secrets["proxy_user"],
                "password": secrets["proxy_password"],
            },
            "storageState": {
                "cookies": [
                    {"name": "sid", "value": secrets["cookie"]},
                ],
                "origins": [
                    {
                        "origin": "http://example.test",
                        "localStorage": [
                            {"name": "authToken", "value": secrets["auth_token"]},
                            {"name": "session", "value": secrets["session"]},
                            {"name": "csrf_token", "value": secrets["csrf"]},
                            {"name": "theme", "value": "dark"},
                        ],
                    }
                ],
            },
        },
    }
    with zipfile.ZipFile(trace_path, "r") as source:
        members = {name: source.read(name) for name in source.namelist()}
    members["trace.trace"] += (json.dumps(context_event) + "\n").encode()
    with zipfile.ZipFile(trace_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
        target.comment = b"playwright-trace"
        for name, data in members.items():
            target.writestr(name, data)

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    with zipfile.ZipFile(trace_path) as archive:
        archived = json.loads(
            archive.read("trace.trace").decode().splitlines()[-1]
        )["options"]
        all_bytes = b"".join(archive.read(name) for name in archive.namelist())
    assert archived["extraHTTPHeaders"][0]["value"] == REDACTION_MARKER
    assert archived["extraHTTPHeaders"][1]["value"] == "application/json"
    assert set(archived["httpCredentials"].values()) == {REDACTION_MARKER}
    assert archived["proxy"] == {
        "server": "http://proxy.example:8080",
        "username": REDACTION_MARKER,
        "password": REDACTION_MARKER,
    }
    assert archived["storageState"]["cookies"][0]["value"] == REDACTION_MARKER
    storage = archived["storageState"]["origins"][0]["localStorage"]
    assert [item["value"] for item in storage] == [
        REDACTION_MARKER,
        REDACTION_MARKER,
        REDACTION_MARKER,
        "dark",
    ]
    assert receipt["counts"]["trace_context_credential_values"] == 4
    assert receipt["counts"]["trace_storage_values"] == 3
    for secret in secrets.values():
        assert secret.encode() not in all_bytes


def test_unicode_sensitive_value_in_embedded_har_content_is_exactly_redacted(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    payload = json.loads(har_path.read_text(encoding="utf-8"))
    payload["log"]["entries"][0]["request"]["headers"].append(
        {"name": "X-API-Key", "value": UNICODE_VALUE}
    )
    payload["log"]["entries"][0]["response"]["content"]["text"] = (
        f"embedded {UNICODE_VALUE} must remain semantic evidence"
    )
    _write_json(har_path, payload)

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    archived = json.loads(har_path.read_text(encoding="utf-8"))
    assert archived["log"]["entries"][0]["response"]["content"]["text"] == (
        f"embedded {REDACTION_MARKER} must remain semantic evidence"
    )
    assert receipt["status"] == "pass"


def test_obs_fold_sensitive_raw_headers_are_fully_redacted(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    har_payload = json.loads(har_path.read_text(encoding="utf-8"))
    har_payload["log"]["entries"][0]["request"]["headersText"] = (
        "Authorization: Bearer HAR-HEAD-987654\r\n"
        "\tHAR-CONTINUATION-SECRET-987654\r\n"
        "Accept: application/json\r\n"
    )
    _write_json(har_path, har_payload)

    trace_event = {
        "type": "resource-snapshot",
        "snapshot": {
            "request": {
                "method": "GET",
                "url": "http://example.test",
                "headers": [],
                "cookies": [],
                "rawHeaders": (
                    "X-API-Key: TRACE-HEAD-987654\r\n"
                    " TRACE-CONTINUATION-SECRET-987654\r\n"
                ),
            }
        },
    }
    with zipfile.ZipFile(trace_path, "r") as source:
        members = {name: source.read(name) for name in source.namelist()}
    members["trace.trace"] += (json.dumps(trace_event) + "\n").encode()
    with zipfile.ZipFile(trace_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
        target.comment = b"playwright-trace"
        for name, data in members.items():
            target.writestr(name, data)

    sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    archived_har = har_path.read_text(encoding="utf-8")
    with zipfile.ZipFile(trace_path) as archive:
        archived_trace = archive.read("trace.trace").decode()
    for secret in (
        "HAR-HEAD-987654",
        "HAR-CONTINUATION-SECRET-987654",
        "TRACE-HEAD-987654",
        "TRACE-CONTINUATION-SECRET-987654",
    ):
        assert secret not in archived_har
        assert secret not in archived_trace
    assert f"Authorization: {REDACTION_MARKER}\r\n" in json.loads(
        archived_har
    )["log"]["entries"][0]["request"]["headersText"]


def test_worker_sanitizes_before_official_evaluator_reads_har(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    events: list[str] = []

    def fake_evaluator(**kwargs: Any) -> dict[str, Any]:
        del kwargs
        events.append("evaluator")
        archived = har_path.read_text(encoding="utf-8")
        assert REDACTION_MARKER in archived
        assert COOKIE_VALUE not in archived
        with zipfile.ZipFile(trace_path) as archive:
            trace_bytes = b"".join(
                archive.read(name) for name in archive.namelist()
            )
        assert COOKIE_VALUE.encode() not in trace_bytes
        result_dir = tmp_path / "42"
        result_dir.mkdir(parents=True, exist_ok=True)
        (result_dir / "eval_result.json").write_text(
            '{"evaluators_results": []}\n', encoding="utf-8"
        )
        return {"scorer_status": "success", "score": 1.0}

    monkeypatch.setattr(
        webarena_official_worker,
        "_run_webarena_verified_evaluator",
        fake_evaluator,
    )
    summary, sanitization = (
        webarena_official_worker._sanitize_then_evaluate_network_evidence(
            task_id=42,
            task_revision=1,
            output_dir=tmp_path,
            evaluator_config=tmp_path / "runtime.json",
            har_path=har_path,
            trace_path=trace_path,
        )
    )

    assert events == ["evaluator"]
    assert sanitization["sanitization_completed_before_evaluator"] is True
    assert summary["score"] == 1.0


def test_opaque_exact_match_is_redacted_without_other_byte_changes(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(
        tmp_path, opaque_value=COOKIE_VALUE.encode()
    )

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    with zipfile.ZipFile(trace_path) as archive:
        assert archive.read("resources/body.bin") == REDACTION_MARKER.encode()
    assert receipt["status"] == "pass"


def test_trace_only_seven_byte_secret_in_opaque_member_is_exactly_redacted(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(
        tmp_path, opaque_value=TRACE_ONLY_VALUE.encode()
    )

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    with zipfile.ZipFile(trace_path) as archive:
        assert archive.read("resources/body.bin") == REDACTION_MARKER.encode()
    assert receipt["active_original_value_exact_match_count_after_sanitization"] == 0


def test_short_cookie_value_does_not_false_match_ordinary_payload(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    payload = json.loads(har_path.read_text(encoding="utf-8"))
    entry = payload["log"]["entries"][0]
    entry["request"]["cookies"].append(
        {"name": "locale", "value": "en", "domain": "127.0.0.1"}
    )
    entry["response"]["content"]["text"] = (
        '{"content":"ordinary language preference is en"}'
    )
    _write_json(har_path, payload)

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    archived = json.loads(har_path.read_text(encoding="utf-8"))
    assert archived["log"]["entries"][0]["request"]["cookies"][-1][
        "value"
    ] == REDACTION_MARKER
    assert receipt["status"] == "pass"


def test_har_embedded_body_exact_secret_is_redacted_without_other_changes(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    payload = json.loads(har_path.read_text(encoding="utf-8"))
    payload["log"]["entries"][0]["response"]["content"]["text"] = (
        f"body contains {CSRF_VALUE} and must not be silently rewritten"
    )
    _write_json(har_path, payload)

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    archived = json.loads(har_path.read_text(encoding="utf-8"))
    assert archived["log"]["entries"][0]["response"]["content"]["text"] == (
        f"body contains {REDACTION_MARKER} and must not be silently rewritten"
    )
    assert receipt["status"] == "pass"


def test_unparseable_structured_trace_fails_closed_and_removes_trace(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    with zipfile.ZipFile(trace_path, "w") as archive:
        archive.writestr("trace.trace", b"{}\n")
        archive.writestr("trace.network", b"not-json-or-jsonl")

    with pytest.raises(HarSanitizationError, match="JSONL is invalid"):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_path,
            trace_path=trace_path,
        )

    assert not trace_path.exists()
    assert not har_path.exists()


def test_empty_json_response_resource_is_preserved_as_opaque(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    resource_name = "resources/da39a3ee5e6b4b0d3255bfef95601890afd80709.json"
    with zipfile.ZipFile(trace_path, "a") as archive:
        archive.writestr(resource_name, b"")

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    with zipfile.ZipFile(trace_path) as archive:
        assert archive.read(resource_name) == b""
    assert receipt["status"] == "pass"
    assert receipt["trace_text_entry_count"] == 3


def test_empty_core_structured_trace_member_still_fails_closed(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    with zipfile.ZipFile(trace_path, "w") as archive:
        archive.writestr("trace.trace", b"")
        archive.writestr("trace.network", b"{}\n")

    with pytest.raises(
        HarSanitizationError,
        match="structured trace member is empty: trace.trace",
    ):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_path,
            trace_path=trace_path,
        )

    assert not trace_path.exists()
    assert not har_path.exists()


def test_json_response_resource_uses_opaque_exact_redaction(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    resource_name = "resources/credential-bearing-body.json"
    with zipfile.ZipFile(trace_path, "a") as archive:
        archive.writestr(resource_name, COOKIE_VALUE.encode())

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    with zipfile.ZipFile(trace_path) as archive:
        assert archive.read(resource_name) == REDACTION_MARKER.encode()
    assert receipt["status"] == "pass"
    assert receipt["active_original_value_exact_match_count_after_sanitization"] == 0


def test_receipt_tampering_is_rejected(tmp_path: Path) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )
    archived_har = json.loads(har_path.read_text(encoding="utf-8"))
    tampered = json.loads(json.dumps(receipt))
    tampered["counts"]["trace_cookie_values"] += 1
    tampered["counts"]["total_values"] += 1

    with pytest.raises(HarSanitizationError, match="does not bind"):
        validate_network_sanitization_receipt(
            tampered,
            har_payload=archived_har,
            har_path=har_path,
            trace_path=trace_path,
        )


def test_receipt_hash_binds_actual_har_bytes_not_only_parsed_json(
    tmp_path: Path,
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )
    receipt_path = har_path.with_name("network_har_sanitization.json")
    har_path.write_text(
        har_path.read_text(encoding="utf-8") + " ", encoding="utf-8"
    )

    with pytest.raises(HarSanitizationError, match="does not bind"):
        load_and_validate_network_sanitization_receipt(
            receipt_path,
            har_path=har_path,
            trace_path=trace_path,
        )


@pytest.mark.parametrize("unsafe_name", ["../escape", "/absolute", "a\\b"])
def test_unsafe_zip_member_paths_fail_closed(
    tmp_path: Path, unsafe_name: str
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    with zipfile.ZipFile(trace_path, "w") as archive:
        archive.writestr("trace.trace", "{}\n")
        archive.writestr("trace.network", "{}\n")
        archive.writestr(unsafe_name, "unsafe")

    with pytest.raises(HarSanitizationError, match="unsafe member path"):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_path,
            trace_path=trace_path,
        )

    assert not har_path.exists()
    assert not trace_path.exists()


def test_duplicate_and_missing_core_trace_members_fail_closed(tmp_path: Path) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    with zipfile.ZipFile(trace_path, "w") as archive:
        archive.writestr("trace.trace", "{}\n")
        archive.writestr("trace.trace", "{}\n")
        archive.writestr("trace.network", "{}\n")
    with pytest.raises(HarSanitizationError, match="duplicate"):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_path,
            trace_path=trace_path,
        )

    har_path, trace_path = _artifacts(tmp_path / "missing")
    with zipfile.ZipFile(trace_path, "w") as archive:
        archive.writestr("metadata.json", "{}")
    with pytest.raises(HarSanitizationError, match="missing trace.trace"):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_path,
            trace_path=trace_path,
        )


def test_oversize_metadata_is_rejected_before_testzip_or_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    trace_info = zipfile.ZipInfo("trace.trace")
    network_info = zipfile.ZipInfo("trace.network")
    network_info.file_size = sanitizer.MAX_TRACE_MEMBER_UNCOMPRESSED_BYTES + 1

    monkeypatch.setattr(
        zipfile.ZipFile,
        "infolist",
        lambda _self: [trace_info, network_info],
    )

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("decompression occurred before metadata preflight")

    monkeypatch.setattr(zipfile.ZipFile, "testzip", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "read", forbidden)
    with pytest.raises(HarSanitizationError, match="size limit"):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_path,
            trace_path=trace_path,
        )


def test_member_bound_covers_the_existing_total_archive_bound() -> None:
    assert sanitizer.MAX_TRACE_TEXT_MEMBER_UNCOMPRESSED_BYTES == 50_000_000
    assert sanitizer.MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES == 256_000_000
    assert sanitizer.MAX_TRACE_TOTAL_UNCOMPRESSED_BYTES == 512_000_000
    assert (
        sanitizer.MAX_TRACE_MEMBER_UNCOMPRESSED_BYTES
        == sanitizer.MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES
    )


def test_trace_member_larger_than_legacy_50mb_cap_is_sanitized(
    tmp_path: Path,
) -> None:
    har_path = tmp_path / "42" / "network.har"
    _write_json(har_path, _har())
    trace_path = tmp_path / "traces" / "42.zip"
    trace_path.parent.mkdir(parents=True)
    legacy_oversize = b"x" * 50_000_001
    with zipfile.ZipFile(trace_path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("trace.trace", b'{"type":"event"}\n')
        archive.writestr("trace.network", b'{"type":"event"}\n')
        archive.writestr("resources/large.bin", legacy_oversize)

    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    assert receipt["status"] == "pass"
    assert receipt["algorithm_version"] == sanitizer.SANITIZATION_ALGORITHM_VERSION
    with zipfile.ZipFile(trace_path, "r") as archive:
        assert archive.getinfo("resources/large.bin").file_size == len(legacy_oversize)


def test_opaque_secret_crossing_stream_chunk_boundary_is_redacted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sanitizer, "TRACE_STREAM_CHUNK_BYTES", 16)
    prefix = b"p" * 11
    original = prefix + COOKIE_VALUE.encode("utf-8") + b"-public-suffix"
    har_path, trace_path = _artifacts(tmp_path, opaque_value=original)

    sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )

    with zipfile.ZipFile(trace_path, "r") as archive:
        observed = archive.read("resources/body.bin")
    assert COOKIE_VALUE.encode("utf-8") not in observed
    assert observed == (
        prefix + REDACTION_MARKER.encode("utf-8") + b"-public-suffix"
    )


def test_v5_receipt_remains_valid_after_v6_deployment(tmp_path: Path) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    receipt = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )
    receipt["algorithm_version"] = (
        "webarena_verified_har_trace_credential_value_redaction_v5"
    )

    validate_network_sanitization_receipt(
        receipt,
        har_payload=json.loads(har_path.read_text(encoding="utf-8")),
        har_path=har_path,
        trace_path=trace_path,
    )


def test_missing_trace_clears_raw_har_and_stale_receipt(tmp_path: Path) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    trace_path.unlink()
    receipt_path = har_path.with_name("network_har_sanitization.json")
    receipt_path.write_text('{"status":"stale-pass"}\n', encoding="utf-8")

    with pytest.raises(HarSanitizationError, match="trace ZIP is missing"):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_path,
            trace_path=trace_path,
        )

    assert not har_path.exists()
    assert not receipt_path.exists()


def test_symlink_input_is_unlinked_without_touching_target(tmp_path: Path) -> None:
    real_har = tmp_path / "real.har"
    _write_json(real_har, _har())
    har_link = tmp_path / "42" / "network.har"
    har_link.parent.mkdir(parents=True)
    har_link.symlink_to(real_har)
    trace_path = tmp_path / "traces" / "42.zip"
    _write_trace(trace_path)

    with pytest.raises(HarSanitizationError, match="non-symlink regular"):
        sanitize_network_artifacts_before_evaluator(
            har_path=har_link,
            trace_path=trace_path,
        )

    assert real_har.is_file()
    assert not har_link.exists()
    assert not trace_path.exists()


def test_sanitizer_failure_never_calls_official_evaluator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    har_path, trace_path = _artifacts(tmp_path)
    with zipfile.ZipFile(trace_path, "w") as archive:
        archive.writestr("trace.trace", b"{}\n")
        archive.writestr("trace.network", b"not-json-or-jsonl")
    called = False

    def forbidden_evaluator(**_kwargs: Any) -> dict[str, Any]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(
        webarena_official_worker,
        "_run_webarena_verified_evaluator",
        forbidden_evaluator,
    )
    with pytest.raises(HarSanitizationError):
        webarena_official_worker._sanitize_then_evaluate_network_evidence(
            task_id=42,
            task_revision=1,
            output_dir=tmp_path,
            evaluator_config=tmp_path / "runtime.json",
            har_path=har_path,
            trace_path=trace_path,
        )
    assert called is False


def test_evaluator_har_mutation_fails_post_evaluator_receipt_recheck(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    har_path, trace_path = _artifacts(tmp_path)

    def mutating_evaluator(**_kwargs: Any) -> dict[str, Any]:
        har_path.write_text(
            har_path.read_text(encoding="utf-8") + " ", encoding="utf-8"
        )
        result_dir = tmp_path / "42"
        result_dir.mkdir(parents=True, exist_ok=True)
        (result_dir / "eval_result.json").write_text(
            '{"evaluators_results": []}\n', encoding="utf-8"
        )
        return {"scorer_status": "success", "score": 1.0}

    monkeypatch.setattr(
        webarena_official_worker,
        "_run_webarena_verified_evaluator",
        mutating_evaluator,
    )
    with pytest.raises(HarSanitizationError, match="does not bind"):
        webarena_official_worker._sanitize_then_evaluate_network_evidence(
            task_id=42,
            task_revision=1,
            output_dir=tmp_path,
            evaluator_config=tmp_path / "runtime.json",
            har_path=har_path,
            trace_path=trace_path,
        )
