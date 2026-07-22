"""Fail-closed pre-evaluator redaction of WebArena HAR and trace evidence.

Browser output is sanitized before the official evaluator runs so the scored
HAR and the archived HAR are byte-identical.  Sensitive header/cookie values
are replaced in the HAR and structured Playwright trace entries.  Original
values are held only in memory long enough to prove that no ZIP member retains
an exact match; neither values nor value hashes are written to the receipt.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Any
import zipfile


SANITIZATION_SCHEMA_VERSION = (
    "webarena_verified_network_har_trace_sanitization/v1"
)
SANITIZATION_ALGORITHM_VERSION = (
    "webarena_verified_har_trace_credential_value_redaction_v7"
)
LEGACY_SANITIZATION_ALGORITHM_VERSIONS = frozenset(
    {
        "webarena_verified_har_trace_credential_value_redaction_v5",
        "webarena_verified_har_trace_credential_value_redaction_v6",
    }
)
SUPPORTED_SANITIZATION_ALGORITHM_VERSIONS = frozenset(
    {SANITIZATION_ALGORITHM_VERSION, *LEGACY_SANITIZATION_ALGORITHM_VERSIONS}
)
REDACTION_MARKER = "<redacted>"
# Exact-match scanning is a second line of defence after all sensitive fields
# have been structurally redacted.  Very short cookie values (for example a
# locale or UI preference) occur naturally throughout HTML/JSON and therefore
# cannot identify credential duplication by substring.  Seven UTF-8 bytes is
# the locked lower bound; short non-ASCII credentials remain protected too.
MIN_EXACT_CANDIDATE_BYTES = 7
SENSITIVE_HEADER_NAMES = frozenset(
    {
        "api-key",
        "authorization",
        "cookie",
        "csrf-token",
        "proxy-authorization",
        "set-cookie",
        "x-access-token",
        "x-api-key",
        "x-auth-token",
        "x-csrf-token",
        "x-xsrf-token",
        "xsrf-token",
    }
)
TRACE_TEXT_SUFFIXES = (".trace", ".network", ".json", ".jsonl")
REQUIRED_TRACE_BASENAMES = frozenset({"trace.trace", "trace.network"})
MAX_TRACE_ENTRY_COUNT = 5_000
# Structured trace members are still decoded as bounded JSON/JSONL objects.
# Opaque members (notably Playwright's growing ``trace.stacks``) are copied and
# exact-redacted as a stream, so they can safely exceed the former 50 MB common
# cap without creating a correspondingly large in-memory buffer.
MAX_TRACE_TEXT_MEMBER_UNCOMPRESSED_BYTES = 50_000_000
MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES = 256_000_000
MAX_TRACE_MEMBER_UNCOMPRESSED_BYTES = MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES
MAX_TRACE_TOTAL_UNCOMPRESSED_BYTES = 512_000_000
MAX_TRACE_COMPRESSION_RATIO = 200.0
TRACE_STREAM_CHUNK_BYTES = 1_048_576
MAX_EXACT_CANDIDATE_COUNT = 10_000
MAX_EXACT_CANDIDATE_BYTES = 65_536
MAX_EXACT_CANDIDATE_TOTAL_BYTES = 8_388_608
HEADER_CONTAINER_KEYS = frozenset(
    {
        "headers",
        "_headers",
        "extrahttpheaders",
        "httpheaders",
        "requestheaders",
        "responseheaders",
    }
)
COOKIE_CONTAINER_KEYS = frozenset(
    {"cookies", "requestcookies", "responsecookies"}
)
OPAQUE_PAYLOAD_KEYS = frozenset(
    {
        "body",
        "businessbody",
        "content",
        "postdata",
        "postdataentries",
        "requestbody",
        "responsebody",
    }
)
CONTEXT_CREDENTIAL_KEYS = frozenset({"password", "username"})
HAR_COUNT_KEYS = (
    "har_request_header_values",
    "har_response_header_values",
    "har_request_cookie_values",
    "har_response_cookie_values",
    "har_raw_header_text_values",
)
TRACE_COUNT_KEYS = (
    "trace_header_values",
    "trace_cookie_values",
    "trace_raw_header_text_values",
    "trace_context_credential_values",
    "trace_storage_values",
)
COUNT_KEYS = (*HAR_COUNT_KEYS, *TRACE_COUNT_KEYS, "total_values")
RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "algorithm_version",
        "sanitized_at",
        "sanitization_completed_before_evaluator",
        "counts",
        "full_embedded_har_valid_after_sanitization",
        "trace_sanitized",
        "trace_zip_valid_after_sanitization",
        "trace_entry_count",
        "trace_text_entry_count",
        "sanitized_har_sha256",
        "sanitized_har_size_bytes",
        "sanitized_trace_sha256",
        "sanitized_trace_size_bytes",
        "active_sensitive_field_value_count_after_sanitization",
        "active_original_value_exact_match_count_after_sanitization",
        "original_sensitive_values_retained",
        "original_sensitive_value_hashes_retained",
    }
)


class HarSanitizationError(RuntimeError):
    """Network-evidence sanitization failed closed."""


def sanitize_network_artifacts_before_evaluator(
    *,
    har_path: str | Path,
    trace_path: str | Path,
    receipt_path: str | Path | None = None,
) -> dict[str, Any]:
    """Atomically sanitize HAR/trace artifacts before official evaluation."""

    har_destination = Path(har_path)
    trace_destination = Path(trace_path)
    output = (
        Path(receipt_path)
        if receipt_path is not None
        else har_destination.with_name("network_har_sanitization.json")
    )
    try:
        _require_regular_file(har_destination, "network HAR")
        _require_regular_file(trace_destination, "Playwright trace ZIP")
        _reject_unsafe_optional_output(output)
        _unlink_if_regular_file(output)
        har = _load_json_object(har_destination, "network HAR")
        if not _har_is_full_and_embedded(har):
            raise HarSanitizationError("network HAR is not full and embedded")
        counts = {key: 0 for key in COUNT_KEYS}
        original_values: list[str] = []
        _sanitize_har(
            har,
            counts=counts,
            original_values=original_values,
        )
        har_string_candidates = _exact_string_candidates(original_values)
        _redact_exact_string_candidates(har, har_string_candidates)
        har_counts, har_active = _inspect_har(har)
        if har_active != 0 or any(
            har_counts[key] != counts[key] for key in HAR_COUNT_KEYS
        ):
            raise HarSanitizationError("in-memory HAR redaction validation failed")
        har_bytes = _json_bytes(har)
        har_candidates = _exact_candidates(original_values)
        if _semantic_exact_match_count(har, har_string_candidates) or (
            _exact_match_count(har_bytes, har_candidates)
        ):
            raise HarSanitizationError(
                "sanitized HAR retains an original sensitive value outside fields"
            )

        trace_metrics, all_candidates, all_string_candidates = _sanitize_trace_archive(
            trace_destination,
            original_values=original_values,
        )
        if _semantic_exact_match_count(har, all_string_candidates) or (
            _exact_match_count(har_bytes, all_candidates)
        ):
            raise HarSanitizationError(
                "sanitized HAR retains a trace/HAR sensitive value outside fields"
            )
        counts.update(
            {key: int(trace_metrics[key]) for key in TRACE_COUNT_KEYS}
        )
        counts["total_values"] = sum(
            counts[key] for key in COUNT_KEYS if key != "total_values"
        )
        _atomic_write_json(har_destination, har)

        archived_har = _load_json_object(har_destination, "archived HAR")
        archived_har_counts, archived_har_active = _inspect_har(archived_har)
        archived_trace = _inspect_trace_archive(trace_destination)
        if (
            not _har_is_full_and_embedded(archived_har)
            or archived_har_active != 0
            or any(
                archived_har_counts[key] != counts[key] for key in HAR_COUNT_KEYS
            )
            or archived_trace["active_sensitive_field_values"] != 0
            or any(
                archived_trace[key] != counts[key] for key in TRACE_COUNT_KEYS
            )
        ):
            raise HarSanitizationError(
                "sanitized network artifacts failed atomic read-back validation"
            )

        receipt = {
            "schema_version": SANITIZATION_SCHEMA_VERSION,
            "status": "pass",
            "algorithm_version": SANITIZATION_ALGORITHM_VERSION,
            "sanitized_at": _utc_now_iso(),
            "sanitization_completed_before_evaluator": True,
            "counts": counts,
            "full_embedded_har_valid_after_sanitization": True,
            "trace_sanitized": True,
            "trace_zip_valid_after_sanitization": True,
            "trace_entry_count": archived_trace["trace_entry_count"],
            "trace_text_entry_count": archived_trace["trace_text_entry_count"],
            "sanitized_har_sha256": _sha256_file(har_destination),
            "sanitized_har_size_bytes": har_destination.stat().st_size,
            "sanitized_trace_sha256": _sha256_file(trace_destination),
            "sanitized_trace_size_bytes": trace_destination.stat().st_size,
            "active_sensitive_field_value_count_after_sanitization": 0,
            "active_original_value_exact_match_count_after_sanitization": 0,
            "original_sensitive_values_retained": False,
            "original_sensitive_value_hashes_retained": False,
        }
        validate_network_sanitization_receipt(
            receipt,
            har_payload=archived_har,
            har_path=har_destination,
            trace_path=trace_destination,
        )
        _atomic_write_json(output, receipt)
        return receipt
    except Exception:
        # Any uncertainty deletes both raw network artifacts and stale pass
        # receipts before the worker can invoke or sync the evaluator lane.
        _unlink_artifact_path(output)
        _unlink_artifact_path(har_destination)
        _unlink_artifact_path(trace_destination)
        raise


def sanitize_network_har_after_evaluator(
    *,
    har_path: str | Path,
    evaluator_summary: Mapping[str, Any],
    trace_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compatibility entry point that refuses the obsolete unsafe ordering."""

    del har_path, evaluator_summary, trace_path, receipt_path
    raise HarSanitizationError(
        "obsolete post-evaluator sanitizer is disabled; use the locked "
        "pre-evaluator HAR+trace pipeline"
    )


def validate_network_sanitization_receipt(
    payload: Mapping[str, Any],
    *,
    har_payload: Mapping[str, Any],
    har_path: str | Path,
    trace_path: str | Path,
) -> None:
    """Bind a public-safe receipt to the archived HAR and trace structure."""

    if set(payload) != RECEIPT_KEYS:
        raise HarSanitizationError("network sanitization receipt schema mismatch")
    if (
        payload.get("schema_version") != SANITIZATION_SCHEMA_VERSION
        or payload.get("status") != "pass"
        or payload.get("algorithm_version")
        not in SUPPORTED_SANITIZATION_ALGORITHM_VERSIONS
        or payload.get("sanitization_completed_before_evaluator") is not True
        or payload.get("full_embedded_har_valid_after_sanitization") is not True
        or payload.get("trace_sanitized") is not True
        or payload.get("trace_zip_valid_after_sanitization") is not True
        or payload.get("active_sensitive_field_value_count_after_sanitization") != 0
        or payload.get(
            "active_original_value_exact_match_count_after_sanitization"
        )
        != 0
        or payload.get("original_sensitive_values_retained") is not False
        or payload.get("original_sensitive_value_hashes_retained") is not False
    ):
        raise HarSanitizationError("network sanitization receipt semantics mismatch")
    _validate_timestamp(payload.get("sanitized_at"))
    counts = payload.get("counts")
    if not isinstance(counts, Mapping) or set(counts) != set(COUNT_KEYS):
        raise HarSanitizationError("network sanitization counts schema mismatch")
    if any(
        isinstance(counts.get(key), bool)
        or not isinstance(counts.get(key), int)
        or int(counts[key]) < 0
        for key in COUNT_KEYS
    ):
        raise HarSanitizationError("network sanitization counts are invalid")
    if counts["total_values"] != sum(
        counts[key] for key in COUNT_KEYS if key != "total_values"
    ):
        raise HarSanitizationError("network sanitization total is inconsistent")

    har_counts, har_active = _inspect_har(har_payload)
    har_destination = Path(har_path)
    trace_destination = Path(trace_path)
    trace_metrics = _inspect_trace_archive(trace_destination)
    if (
        not _har_is_full_and_embedded(har_payload)
        or har_active != 0
        or trace_metrics["active_sensitive_field_values"] != 0
        or any(har_counts[key] != counts[key] for key in HAR_COUNT_KEYS)
        or any(trace_metrics[key] != counts[key] for key in TRACE_COUNT_KEYS)
        or payload.get("trace_entry_count") != trace_metrics["trace_entry_count"]
        or payload.get("trace_text_entry_count")
        != trace_metrics["trace_text_entry_count"]
        or payload.get("sanitized_har_sha256") != _sha256_file(har_destination)
        or payload.get("sanitized_har_size_bytes") != har_destination.stat().st_size
        or payload.get("sanitized_trace_sha256") != _sha256_file(trace_destination)
        or payload.get("sanitized_trace_size_bytes")
        != trace_destination.stat().st_size
    ):
        raise HarSanitizationError(
            "network sanitization receipt does not bind archived artifacts"
        )


def load_and_validate_network_sanitization_receipt(
    path: str | Path,
    *,
    har_path: str | Path,
    trace_path: str | Path,
) -> dict[str, Any]:
    receipt = _load_json_object(Path(path), "network sanitization receipt")
    har = _load_json_object(Path(har_path), "archived HAR")
    validate_network_sanitization_receipt(
        receipt,
        har_payload=har,
        har_path=har_path,
        trace_path=trace_path,
    )
    return receipt


def _sanitize_har(
    payload: dict[str, Any],
    *,
    counts: dict[str, int],
    original_values: list[str],
) -> None:
    for entry in payload["log"]["entries"]:
        _sanitize_har_message(
            entry["request"],
            header_key="har_request_header_values",
            cookie_key="har_request_cookie_values",
            counts=counts,
            original_values=original_values,
        )
        _sanitize_har_message(
            entry["response"],
            header_key="har_response_header_values",
            cookie_key="har_response_cookie_values",
            counts=counts,
            original_values=original_values,
        )


def _sanitize_har_message(
    message: dict[str, Any],
    *,
    header_key: str,
    cookie_key: str,
    counts: dict[str, int],
    original_values: list[str],
) -> None:
    headers = message.get("headers")
    if not isinstance(headers, list):
        raise HarSanitizationError("HAR headers must be an array")
    for header in headers:
        if not isinstance(header, dict):
            raise HarSanitizationError("HAR header must be an object")
        name = str(header.get("name") or "").strip().lower()
        if name not in SENSITIVE_HEADER_NAMES:
            continue
        if "value" not in header:
            raise HarSanitizationError("sensitive HAR header has no value")
        _capture_original(header.get("value"), original_values)
        header["value"] = REDACTION_MARKER
        counts[header_key] += 1

    cookies = message.get("cookies")
    if not isinstance(cookies, list):
        raise HarSanitizationError("HAR cookies must be an array")
    for cookie in cookies:
        if not isinstance(cookie, dict) or "value" not in cookie:
            raise HarSanitizationError("HAR cookie must expose a value")
        _capture_original(cookie.get("value"), original_values)
        cookie["value"] = REDACTION_MARKER
        counts[cookie_key] += 1

    if isinstance(message.get("headersText"), str):
        sanitized, redacted, captured = _redact_headers_text(
            str(message["headersText"])
        )
        message["headersText"] = sanitized
        counts["har_raw_header_text_values"] += redacted
        original_values.extend(captured)


def _inspect_har(payload: Mapping[str, Any]) -> tuple[dict[str, int], int]:
    counts = {key: 0 for key in HAR_COUNT_KEYS}
    active = 0
    if not _har_is_full_and_embedded(payload):
        return counts, 1
    for entry in payload["log"]["entries"]:
        for side, header_key, cookie_key in (
            ("request", "har_request_header_values", "har_request_cookie_values"),
            ("response", "har_response_header_values", "har_response_cookie_values"),
        ):
            message = entry[side]
            for header in message["headers"]:
                name = str(header.get("name") or "").strip().lower()
                if name not in SENSITIVE_HEADER_NAMES:
                    continue
                if header.get("value") == REDACTION_MARKER:
                    counts[header_key] += 1
                else:
                    active += 1
            for cookie in message["cookies"]:
                if cookie.get("value") == REDACTION_MARKER:
                    counts[cookie_key] += 1
                else:
                    active += 1
            headers_text = message.get("headersText")
            if isinstance(headers_text, str):
                marked, live = _inspect_headers_text(headers_text)
                counts["har_raw_header_text_values"] += marked
                active += live
    return counts, active


def _sanitize_trace_archive(
    path: Path, *, original_values: list[str]
) -> tuple[dict[str, int], set[bytes], set[str]]:
    if not path.is_file():
        raise HarSanitizationError("Playwright trace ZIP is missing")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.sanitize-", dir=str(path.parent)
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(path, "r") as source:
            source_infos = source.infolist()
            _validate_trace_infos(source_infos)
            trace_original_values: list[str] = []
            for info in source_infos:
                if info.is_dir() or not _is_trace_text_member(info.filename):
                    continue
                _, documents = _decode_trace_text(
                    source.read(info), label=info.filename
                )
                scratch = {key: 0 for key in TRACE_COUNT_KEYS}
                for document in documents:
                    _walk_trace_value(
                        document,
                        context=None,
                        mutate=False,
                        counts=scratch,
                        captured_values=trace_original_values,
                    )
            all_original_values = [*original_values, *trace_original_values]
            candidates = _exact_candidates(all_original_values)
            string_candidates = _exact_string_candidates(all_original_values)
            with zipfile.ZipFile(temporary, "w") as target:
                target.comment = source.comment
                for info in source_infos:
                    if info.is_dir():
                        target.writestr(info, b"")
                        continue
                    if _is_trace_text_member(info.filename):
                        data = source.read(info)
                        data, _ = _sanitize_trace_text(data, label=info.filename)
                        data = _redact_exact_candidates(data, candidates)
                        _, sanitized_documents = _decode_trace_text(
                            data, label=info.filename
                        )
                        if _semantic_exact_match_count(
                            sanitized_documents, string_candidates
                        ):
                            raise HarSanitizationError(
                                "Playwright trace retains an original sensitive value"
                            )
                        if _exact_match_count(data, candidates):
                            raise HarSanitizationError(
                                "Playwright trace retains an original sensitive value"
                            )
                        target.writestr(info, data)
                        continue
                    # Playwright stores response bodies, screenshots and the
                    # potentially large trace.stacks member as opaque ZIP
                    # members.  Preserve every non-secret byte while applying
                    # exact redactions across fixed-size chunk boundaries.
                    declared_size = info.file_size
                    with source.open(info, "r") as source_member, target.open(
                        info, "w", force_zip64=True
                    ) as target_member:
                        observed, _ = _stream_redact_exact_candidates(
                            source_member,
                            target_member,
                            candidates,
                        )
                    if observed != declared_size:
                        raise HarSanitizationError(
                            "Playwright trace ZIP member size disagrees with metadata"
                        )
        _fsync_file(temporary)
        _validate_trace_rewrite(
            original=path,
            sanitized=temporary,
            original_value_bytes=candidates,
            original_value_strings=string_candidates,
        )
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        metrics = _inspect_trace_archive(path)
        if metrics["active_sensitive_field_values"] != 0:
            raise HarSanitizationError("sanitized trace retains active field values")
        return metrics, candidates, string_candidates
    finally:
        if temporary.exists():
            temporary.unlink()


def _validate_trace_rewrite(
    *,
    original: Path,
    sanitized: Path,
    original_value_bytes: set[bytes],
    original_value_strings: set[str],
) -> None:
    with zipfile.ZipFile(original, "r") as source, zipfile.ZipFile(
        sanitized, "r"
    ) as target:
        source_infos = source.infolist()
        target_infos = target.infolist()
        _validate_trace_infos(source_infos)
        _validate_trace_infos(target_infos)
        if [item.filename for item in source_infos] != [
            item.filename for item in target_infos
        ] or source.comment != target.comment:
            raise HarSanitizationError("sanitized trace ZIP structure changed")
        for source_info, target_info in zip(source_infos, target_infos, strict=True):
            if source_info.is_dir():
                continue
            if not _is_trace_text_member(source_info.filename):
                with tempfile.SpooledTemporaryFile(
                    max_size=8_388_608, mode="w+b"
                ) as expected:
                    with source.open(source_info, "r") as source_member:
                        observed, _ = _stream_redact_exact_candidates(
                            source_member,
                            expected,
                            original_value_bytes,
                        )
                    if observed != source_info.file_size:
                        raise HarSanitizationError(
                            "original trace ZIP member size disagrees with metadata"
                        )
                    expected.seek(0)
                    with target.open(target_info, "r") as target_member:
                        if not _streams_equal(expected, target_member):
                            raise HarSanitizationError(
                                "sanitized trace changed bytes outside exact redactions"
                            )
                with target.open(target_info, "r") as target_member:
                    if _stream_exact_match_count(
                        target_member, original_value_bytes
                    ):
                        raise HarSanitizationError(
                            "sanitized trace has an exact original-value match"
                        )
                continue
            target_data = target.read(target_info)
            if _exact_match_count(target_data, original_value_bytes):
                raise HarSanitizationError(
                    "sanitized trace has an exact original-value match"
                )
            if _is_trace_text_member(source_info.filename):
                _, documents = _decode_trace_text(
                    target_data, label=target_info.filename
                )
                if _semantic_exact_match_count(
                    documents, original_value_strings
                ):
                    raise HarSanitizationError(
                        "sanitized trace has a semantic original-value match"
                    )
                counts = {key: 0 for key in TRACE_COUNT_KEYS}
                active = sum(
                    _walk_trace_value(document, context=None, mutate=False, counts=counts)
                    for document in documents
                )
                if active:
                    raise HarSanitizationError(
                        "sanitized trace text retains active sensitive fields"
                    )


def _inspect_trace_archive(path: Path) -> dict[str, int]:
    metrics = {
        **{key: 0 for key in TRACE_COUNT_KEYS},
        "trace_entry_count": 0,
        "trace_text_entry_count": 0,
        "active_sensitive_field_values": 0,
    }
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            _validate_trace_infos(infos)
            metrics["trace_entry_count"] = len(infos)
            for info in infos:
                if info.is_dir():
                    continue
                if not _is_trace_text_member(info.filename):
                    with archive.open(info, "r") as member:
                        observed = _drain_stream(member)
                    if observed != info.file_size:
                        raise HarSanitizationError(
                            "trace ZIP member size disagrees with metadata"
                        )
                    continue
                metrics["trace_text_entry_count"] += 1
                _, documents = _decode_trace_text(
                    archive.read(info), label=info.filename
                )
                for document in documents:
                    metrics["active_sensitive_field_values"] += _walk_trace_value(
                        document,
                        context=None,
                        mutate=False,
                        counts=metrics,
                    )
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        if isinstance(exc, HarSanitizationError):
            raise
        raise HarSanitizationError("trace ZIP is unreadable") from exc
    return metrics


def _sanitize_trace_text(data: bytes, *, label: str) -> tuple[bytes, dict[str, int]]:
    mode, documents = _decode_trace_text(data, label=label)
    counts = {key: 0 for key in TRACE_COUNT_KEYS}
    for document in documents:
        active = _walk_trace_value(
            document,
            context=None,
            mutate=True,
            counts=counts,
        )
        if active:
            raise HarSanitizationError(f"trace sanitizer left active fields: {label}")
    if mode == "json":
        encoded = json.dumps(
            documents[0], ensure_ascii=True, separators=(",", ":")
        ).encode("utf-8")
    else:
        encoded = (
            "\n".join(
                json.dumps(item, ensure_ascii=True, separators=(",", ":"))
                for item in documents
            )
            + "\n"
        ).encode("utf-8")
    return encoded, counts


def sanitize_structured_credential_values(payload: dict[str, Any]) -> int:
    """Redact credential-bearing header/cookie fields in a JSON object in place.

    This uses the same context-aware walker as Playwright trace sanitization and
    deliberately ignores opaque business payload fields.  It is used for
    controller-only official evaluator JSON emitted after the HAR/trace pass.
    """

    counts = {key: 0 for key in TRACE_COUNT_KEYS}
    active = _walk_trace_value(
        payload,
        context=None,
        mutate=True,
        counts=counts,
    )
    if active:
        raise HarSanitizationError(
            "structured credential sanitizer left active fields"
        )
    verification_counts = {key: 0 for key in TRACE_COUNT_KEYS}
    remaining = _walk_trace_value(
        payload,
        context=None,
        mutate=False,
        counts=verification_counts,
    )
    if remaining:
        raise HarSanitizationError(
            "structured credential sanitizer verification failed"
        )
    return sum(counts.values())


def _decode_trace_text(data: bytes, *, label: str) -> tuple[str, list[Any]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HarSanitizationError(
            f"structured trace member is not UTF-8: {label}"
        ) from exc
    try:
        return "json", [json.loads(text)]
    except json.JSONDecodeError:
        documents: list[Any] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise HarSanitizationError(
                    f"structured trace JSONL is invalid: {label}:{line_number}"
                ) from exc
        if not documents:
            raise HarSanitizationError(f"structured trace member is empty: {label}")
        return "jsonl", documents


def _walk_trace_value(
    value: Any,
    *,
    context: str | None,
    mutate: bool,
    counts: dict[str, int],
    captured_values: list[str] | None = None,
) -> int:
    active = 0
    if isinstance(value, list):
        for item in value:
            active += _walk_trace_value(
                item,
                context=context,
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        return active
    if not isinstance(value, dict):
        return 0

    lower_keys = {str(key).lower(): key for key in value}
    if context == "headers":
        name_key = lower_keys.get("name")
        value_key = lower_keys.get("value")
        if name_key is not None and value_key is not None:
            name = str(value[name_key]).strip().lower()
            if name in SENSITIVE_HEADER_NAMES:
                active += _redact_or_inspect_mapping_value(
                    value,
                    value_key,
                    mutate=mutate,
                    count_key="trace_header_values",
                    counts=counts,
                    captured_values=captured_values,
                )
        for key, child in list(value.items()):
            lowered = str(key).lower()
            if key == value_key and name_key is not None:
                continue
            if lowered in SENSITIVE_HEADER_NAMES:
                active += _redact_or_inspect_mapping_value(
                    value,
                    key,
                    mutate=mutate,
                    count_key="trace_header_values",
                    counts=counts,
                    captured_values=captured_values,
                )
            elif key != name_key:
                active += _walk_trace_value(
                    child,
                    context=None,
                    mutate=mutate,
                    counts=counts,
                    captured_values=captured_values,
                )
        return active

    if context == "cookies":
        value_key = lower_keys.get("value")
        if value_key is not None:
            active += _redact_or_inspect_mapping_value(
                value,
                value_key,
                mutate=mutate,
                count_key="trace_cookie_values",
                counts=counts,
                captured_values=captured_values,
            )
            for key, child in list(value.items()):
                if key != value_key:
                    active += _walk_trace_value(
                        child,
                        context=None,
                        mutate=mutate,
                        counts=counts,
                        captured_values=captured_values,
                    )
            return active
        for key in list(value):
            active += _redact_or_inspect_mapping_value(
                value,
                key,
                mutate=mutate,
                count_key="trace_cookie_values",
                counts=counts,
                captured_values=captured_values,
            )
        return active

    if context == "context_credentials":
        for key, child in list(value.items()):
            if str(key).lower() in CONTEXT_CREDENTIAL_KEYS:
                active += _redact_or_inspect_mapping_value(
                    value,
                    key,
                    mutate=mutate,
                    count_key="trace_context_credential_values",
                    counts=counts,
                    captured_values=captured_values,
                )
            else:
                active += _walk_trace_value(
                    child,
                    context=None,
                    mutate=mutate,
                    counts=counts,
                    captured_values=captured_values,
                )
        return active

    if context == "storage_local_storage":
        name_key = lower_keys.get("name")
        value_key = lower_keys.get("value")
        sensitive = name_key is not None and _is_sensitive_storage_name(
            value[name_key]
        )
        if sensitive:
            if value_key is None:
                raise HarSanitizationError(
                    "sensitive storageState localStorage item has no value"
                )
            active += _redact_or_inspect_mapping_value(
                value,
                value_key,
                mutate=mutate,
                count_key="trace_storage_values",
                counts=counts,
                captured_values=captured_values,
            )
        for key, child in list(value.items()):
            if key not in {name_key, value_key}:
                active += _walk_trace_value(
                    child,
                    context=None,
                    mutate=mutate,
                    counts=counts,
                    captured_values=captured_values,
                )
        return active

    for key, child in list(value.items()):
        lowered = str(key).lower()
        if lowered in OPAQUE_PAYLOAD_KEYS:
            # Embedded payloads are benchmark evidence, not transport
            # metadata.  Never recursively rewrite header/cookie-shaped
            # business fields inside them; the exact-zero gate below still
            # fails closed if an actual credential is duplicated there.
            continue
        if lowered in HEADER_CONTAINER_KEYS:
            active += _walk_trace_value(
                child,
                context="headers",
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        elif lowered in COOKIE_CONTAINER_KEYS:
            active += _walk_trace_value(
                child,
                context="cookies",
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        elif lowered == "storagestate":
            active += _walk_trace_value(
                child,
                context="storage_state",
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        elif context == "storage_state" and lowered == "origins":
            active += _walk_trace_value(
                child,
                context="storage_origins",
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        elif context == "storage_origins" and lowered == "localstorage":
            active += _walk_trace_value(
                child,
                context="storage_local_storage",
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        elif lowered in {"httpcredentials", "proxy"}:
            active += _walk_trace_value(
                child,
                context="context_credentials",
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        elif context == "network_message" and lowered in {
            "headerstext",
            "rawheaders",
            "rawheaderstext",
        }:
            if not isinstance(child, str):
                raise HarSanitizationError("trace raw headers are not text")
            if mutate:
                sanitized, marked, originals = _redact_headers_text(child)
                value[key] = sanitized
                counts["trace_raw_header_text_values"] += marked
                if captured_values is not None:
                    captured_values.extend(originals)
            else:
                marked, live = _inspect_headers_text(child)
                counts["trace_raw_header_text_values"] += marked
                active += live
                if captured_values is not None:
                    _, _, originals = _redact_headers_text(child)
                    captured_values.extend(originals)
        elif context == "network_message" and lowered in {
            "requestheaderstext",
            "responseheaderstext",
        }:
            if not isinstance(child, str):
                raise HarSanitizationError("trace raw headers are not text")
            if mutate:
                sanitized, marked, originals = _redact_headers_text(child)
                value[key] = sanitized
                counts["trace_raw_header_text_values"] += marked
                if captured_values is not None:
                    captured_values.extend(originals)
            else:
                marked, live = _inspect_headers_text(child)
                counts["trace_raw_header_text_values"] += marked
                active += live
                if captured_values is not None:
                    _, _, originals = _redact_headers_text(child)
                    captured_values.extend(originals)
        elif lowered in {"request", "response"} and _looks_like_network_message(
            child, kind=lowered
        ):
            active += _walk_trace_value(
                child,
                context="network_message",
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
        else:
            active += _walk_trace_value(
                child,
                context=None,
                mutate=mutate,
                counts=counts,
                captured_values=captured_values,
            )
    return active


def _is_sensitive_storage_name(value: Any) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(value).lower())
    return any(
        marker in normalized
        for marker in (
            "apikey",
            "auth",
            "credential",
            "csrf",
            "password",
            "secret",
            "session",
            "token",
            "xsrf",
        )
    )


def _redact_or_inspect_mapping_value(
    container: dict[str, Any],
    key: Any,
    *,
    mutate: bool,
    count_key: str,
    counts: dict[str, int],
    captured_values: list[str] | None,
) -> int:
    current = container[key]
    if isinstance(current, (dict, list)):
        raise HarSanitizationError("sensitive trace field has a non-scalar value")
    if mutate:
        if (
            captured_values is not None
            and isinstance(current, str)
            and current
            and current != REDACTION_MARKER
        ):
            captured_values.append(current)
        container[key] = REDACTION_MARKER
        counts[count_key] += 1
        return 0
    if current == REDACTION_MARKER:
        counts[count_key] += 1
        return 0
    if captured_values is not None and isinstance(current, str) and current:
        captured_values.append(current)
    return 1


def _looks_like_network_message(value: Any, *, kind: str) -> bool:
    if not isinstance(value, Mapping):
        return False
    keys = {str(key).lower() for key in value}
    has_evidence_container = bool(
        keys.intersection(HEADER_CONTAINER_KEYS | COOKIE_CONTAINER_KEYS)
        or keys.intersection({"headerstext", "rawheaders", "rawheaderstext"})
    )
    if not has_evidence_container:
        return False
    if kind == "request":
        return bool(keys.intersection({"url", "method", "headers", "cookies"}))
    return bool(keys.intersection({"status", "statuscode", "headers", "cookies"}))


def _redact_headers_text(value: str) -> tuple[str, int, list[str]]:
    pattern = re.compile(r"^([^:\r\n]+):(.*)$")
    output: list[str] = []
    count = 0
    originals: list[str] = []
    current_sensitive = False
    for line in value.splitlines(keepends=True):
        body, ending = _split_line_ending(line)
        if body.startswith((" ", "\t")):
            if not current_sensitive:
                output.append(line)
                continue
            prefix = body[: len(body) - len(body.lstrip(" \t"))]
            original = body[len(prefix) :].strip()
            if original and original != REDACTION_MARKER:
                originals.append(original)
            output.append(f"{prefix}{REDACTION_MARKER}{ending}")
            continue
        match = pattern.match(body)
        current_sensitive = bool(
            match
            and match.group(1).strip().lower() in SENSITIVE_HEADER_NAMES
        )
        if not current_sensitive or match is None:
            output.append(line)
            continue
        original = match.group(2).strip()
        if original and original != REDACTION_MARKER:
            originals.append(original)
        output.append(f"{match.group(1)}: {REDACTION_MARKER}{ending}")
        count += 1
    return "".join(output), count, originals


def _inspect_headers_text(value: str) -> tuple[int, int]:
    marked = 0
    active = 0
    current_sensitive = False
    current_active = False
    for line in value.splitlines(keepends=True):
        body, _ = _split_line_ending(line)
        if body.startswith((" ", "\t")):
            if (
                current_sensitive
                and body.strip()
                and body.strip() != REDACTION_MARKER
                and not current_active
            ):
                marked -= 1
                active += 1
                current_active = True
            continue
        current_sensitive = False
        current_active = False
        if ":" not in body:
            continue
        name, raw = body.split(":", 1)
        current_sensitive = name.strip().lower() in SENSITIVE_HEADER_NAMES
        if not current_sensitive:
            continue
        if raw.strip() == REDACTION_MARKER:
            marked += 1
        else:
            active += 1
            current_active = True
    return marked, active


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1]
    return line, ""


def _har_is_full_and_embedded(payload: Mapping[str, Any]) -> bool:
    log = payload.get("log")
    if not isinstance(log, Mapping) or log.get("version") != "1.2":
        return False
    creator = log.get("creator")
    if not isinstance(creator, Mapping) or "playwright" not in str(
        creator.get("name") or ""
    ).lower():
        return False
    entries = log.get("entries")
    if not isinstance(entries, list) or not entries:
        return False
    embedded = 0
    for entry in entries:
        if not isinstance(entry, Mapping):
            return False
        request = entry.get("request")
        response = entry.get("response")
        if not isinstance(request, Mapping) or not isinstance(response, Mapping):
            return False
        if not isinstance(request.get("headers"), list) or not isinstance(
            request.get("cookies"), list
        ):
            return False
        if not isinstance(response.get("headers"), list) or not isinstance(
            response.get("cookies"), list
        ):
            return False
        content = response.get("content")
        if not isinstance(content, Mapping) or "_file" in content or "_sha1" in content:
            return False
        if "text" in content:
            embedded += 1
    return embedded > 0


def _is_trace_text_member(name: str) -> bool:
    pure = PurePosixPath(str(name))
    # Playwright stores response bodies and screenshots under ``resources/``.
    # Their suffix reflects the HTTP content type, not the trace container
    # format, so an empty JSON response body is a valid opaque member rather
    # than an empty structured trace document.  Keep this subtree on the
    # streaming exact-redaction path regardless of filename extension.
    if pure.parts and pure.parts[0].lower() == "resources":
        return False
    return str(name).lower().endswith(TRACE_TEXT_SUFFIXES)


def _capture_original(value: Any, output: list[str]) -> None:
    if isinstance(value, str) and value and value != REDACTION_MARKER:
        output.append(value)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HarSanitizationError(f"{label} is not readable JSON") from exc
    if not isinstance(loaded, dict):
        raise HarSanitizationError(f"{label} root is not an object")
    return loaded


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise HarSanitizationError("network sanitization timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise HarSanitizationError(
            "network sanitization timestamp is invalid"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise HarSanitizationError("network sanitization timestamp is not UTC")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (
        json.dumps(dict(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.tmp-", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _validate_trace_infos(infos: list[zipfile.ZipInfo]) -> None:
    if not infos:
        raise HarSanitizationError("Playwright trace ZIP is empty")
    if len(infos) > MAX_TRACE_ENTRY_COUNT:
        raise HarSanitizationError("Playwright trace ZIP exceeds the entry limit")
    names = [info.filename for info in infos]
    if len(names) != len(set(names)):
        raise HarSanitizationError("Playwright trace ZIP has duplicate members")
    basenames = {PurePosixPath(name).name for name in names}
    if not REQUIRED_TRACE_BASENAMES.issubset(basenames):
        raise HarSanitizationError(
            "Playwright trace ZIP is missing trace.trace or trace.network"
        )
    total = 0
    for info in infos:
        name = info.filename
        pure = PurePosixPath(name)
        if (
            not name
            or "\x00" in name
            or "\\" in name
            or name.startswith("/")
            or "//" in name
            or pure.is_absolute()
            or any(part in {"", ".", ".."} for part in pure.parts)
            or (pure.parts and ":" in pure.parts[0])
        ):
            raise HarSanitizationError("Playwright trace ZIP has an unsafe member path")
        unix_mode = (info.external_attr >> 16) & 0o170000
        if unix_mode == 0o120000:
            raise HarSanitizationError("Playwright trace ZIP contains a symlink")
        if info.flag_bits & 0x1:
            raise HarSanitizationError("Playwright trace ZIP contains encryption")
        if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise HarSanitizationError(
                "Playwright trace ZIP uses an unsupported compression method"
            )
        member_limit = (
            MAX_TRACE_TEXT_MEMBER_UNCOMPRESSED_BYTES
            if _is_trace_text_member(name)
            else MAX_TRACE_OPAQUE_MEMBER_UNCOMPRESSED_BYTES
        )
        if info.file_size < 0 or info.file_size > member_limit:
            raise HarSanitizationError(
                "Playwright trace ZIP member exceeds the size limit: "
                f"member={name!r} size_bytes={info.file_size} "
                f"limit_bytes={member_limit}"
            )
        total += info.file_size
        if total > MAX_TRACE_TOTAL_UNCOMPRESSED_BYTES:
            raise HarSanitizationError(
                "Playwright trace ZIP exceeds the total size limit"
            )
        if info.file_size > 0:
            if info.compress_size <= 0:
                raise HarSanitizationError(
                    "Playwright trace ZIP member has an invalid compression ratio"
                )
            ratio = info.file_size / info.compress_size
            if ratio > MAX_TRACE_COMPRESSION_RATIO:
                raise HarSanitizationError(
                    "Playwright trace ZIP exceeds the compression-ratio limit"
                )


def _exact_candidates(values: list[str]) -> set[bytes]:
    candidates: set[bytes] = set()
    for value in _exact_string_candidates(values):
        candidates.add(value.encode("utf-8"))
        # Structured JSON members may serialize a Unicode or control-character
        # credential as an escape sequence.  Scan both raw UTF-8 and the two
        # JSON string-content representations in every opaque ZIP member.
        for ensure_ascii in (False, True):
            encoded = json.dumps(value, ensure_ascii=ensure_ascii)[1:-1].encode(
                "utf-8"
            )
            if encoded:
                candidates.add(encoded)
    _validate_candidate_bounds(candidates)
    return candidates


def _exact_string_candidates(values: list[str]) -> set[str]:
    candidates = {
        value
        for value in values
        if value
        and value != REDACTION_MARKER
        and len(value.encode("utf-8")) >= MIN_EXACT_CANDIDATE_BYTES
    }
    _validate_candidate_bounds(
        {candidate.encode("utf-8") for candidate in candidates}
    )
    return candidates


def _validate_candidate_bounds(candidates: set[bytes]) -> None:
    sizes = [len(candidate) for candidate in candidates]
    if len(candidates) > MAX_EXACT_CANDIDATE_COUNT:
        raise HarSanitizationError("trace exact-candidate count exceeds the limit")
    if sizes and max(sizes) > MAX_EXACT_CANDIDATE_BYTES:
        raise HarSanitizationError("trace exact-candidate size exceeds the limit")
    if sum(sizes) > MAX_EXACT_CANDIDATE_TOTAL_BYTES:
        raise HarSanitizationError(
            "trace exact-candidate total size exceeds the limit"
        )


def _stream_redact_exact_candidates(
    source: Any,
    target: Any,
    candidates: set[bytes],
) -> tuple[int, int]:
    """Copy one opaque member with leftmost-longest exact redaction.

    At most one input chunk plus ``max_candidate_length - 1`` bytes are held
    in memory, which preserves matches spanning adjacent chunks.  Candidate
    values and hashes are never emitted.
    """

    ordered = tuple(
        candidate
        for candidate in sorted(candidates, key=lambda item: (-len(item), item))
        if candidate
    )
    maximum = max((len(candidate) for candidate in ordered), default=1)
    marker = REDACTION_MARKER.encode("utf-8")
    buffer = b""
    observed = 0
    written = 0

    def write(data: bytes) -> None:
        nonlocal written
        if not data:
            return
        count = target.write(data)
        if count is not None and count != len(data):
            raise HarSanitizationError("trace ZIP member write was incomplete")
        written += len(data)

    def flush(*, final: bool) -> None:
        nonlocal buffer
        while buffer:
            safe_limit = len(buffer) if final else len(buffer) - (maximum - 1)
            if safe_limit <= 0:
                return
            best_position: int | None = None
            best_candidate: bytes | None = None
            for candidate in ordered:
                position = buffer.find(candidate)
                if position < 0 or position >= safe_limit:
                    continue
                if (
                    best_position is None
                    or position < best_position
                    or (
                        position == best_position
                        and best_candidate is not None
                        and len(candidate) > len(best_candidate)
                    )
                ):
                    best_position = position
                    best_candidate = candidate
            if best_position is None or best_candidate is None:
                write(buffer[:safe_limit])
                buffer = buffer[safe_limit:]
                continue
            write(buffer[:best_position])
            write(marker)
            buffer = buffer[best_position + len(best_candidate) :]

    while True:
        chunk = source.read(TRACE_STREAM_CHUNK_BYTES)
        if not chunk:
            break
        observed += len(chunk)
        buffer += chunk
        flush(final=False)
    flush(final=True)
    return observed, written


def _stream_exact_match_count(source: Any, candidates: set[bytes]) -> int:
    ordered = tuple(candidate for candidate in candidates if candidate)
    maximum = max((len(candidate) for candidate in ordered), default=1)
    tail = b""
    while True:
        chunk = source.read(TRACE_STREAM_CHUNK_BYTES)
        if not chunk:
            return 0
        combined = tail + chunk
        if any(candidate in combined for candidate in ordered):
            return 1
        tail = combined[-(maximum - 1) :] if maximum > 1 else b""


def _drain_stream(source: Any) -> int:
    observed = 0
    while True:
        chunk = source.read(TRACE_STREAM_CHUNK_BYTES)
        if not chunk:
            return observed
        observed += len(chunk)


def _streams_equal(left: Any, right: Any) -> bool:
    def digest(source: Any) -> tuple[int, bytes]:
        total = 0
        value = hashlib.sha256()
        while True:
            chunk = source.read(TRACE_STREAM_CHUNK_BYTES)
            if not chunk:
                return total, value.digest()
            total += len(chunk)
            value.update(chunk)

    return digest(left) == digest(right)


def _semantic_exact_match_count(value: Any, candidates: set[str]) -> int:
    if isinstance(value, str):
        return sum(value.count(candidate) for candidate in candidates)
    if isinstance(value, list):
        return sum(
            _semantic_exact_match_count(item, candidates) for item in value
        )
    if isinstance(value, Mapping):
        return sum(
            _semantic_exact_match_count(item, candidates)
            for item in value.values()
        )
    return 0


def _redact_exact_string_candidates(value: Any, candidates: set[str]) -> Any:
    if isinstance(value, str):
        redacted = value
        for candidate in sorted(candidates, key=lambda item: (-len(item), item)):
            redacted = redacted.replace(candidate, REDACTION_MARKER)
        return redacted
    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = _redact_exact_string_candidates(item, candidates)
        return value
    if isinstance(value, dict):
        for key, item in list(value.items()):
            value[key] = _redact_exact_string_candidates(item, candidates)
        return value
    return value


def _exact_match_count(data: bytes, candidates: set[bytes]) -> int:
    return sum(data.count(candidate) for candidate in candidates)


def _redact_exact_candidates(data: bytes, candidates: set[bytes]) -> bytes:
    redacted = data
    marker = REDACTION_MARKER.encode("utf-8")
    for candidate in sorted(candidates, key=lambda item: (-len(item), item)):
        if candidate:
            redacted = redacted.replace(candidate, marker)
    return redacted


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unlink_if_regular_file(path: Path) -> None:
    try:
        if path.is_file() and not path.is_symlink():
            path.unlink()
    except OSError:
        pass


def _unlink_artifact_path(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError:
        return
    if stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        try:
            path.unlink()
        except OSError:
            pass


def _require_regular_file(path: Path, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise HarSanitizationError(f"{label} is missing") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise HarSanitizationError(f"{label} must be a non-symlink regular file")


def _reject_unsafe_optional_output(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise HarSanitizationError(
            "network sanitization receipt path is unreadable"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise HarSanitizationError(
            "network sanitization receipt path is not a regular file"
        )


__all__ = [
    "HarSanitizationError",
    "REDACTION_MARKER",
    "SANITIZATION_ALGORITHM_VERSION",
    "SANITIZATION_SCHEMA_VERSION",
    "SENSITIVE_HEADER_NAMES",
    "load_and_validate_network_sanitization_receipt",
    "sanitize_network_artifacts_before_evaluator",
    "sanitize_network_har_after_evaluator",
    "sanitize_structured_credential_values",
    "validate_network_sanitization_receipt",
]
