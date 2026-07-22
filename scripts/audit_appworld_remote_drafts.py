#!/usr/bin/env python3
"""Fail-closed audit for AppWorld checklist drafts returned by a draft VPS.

The cases JSONL is the authoritative selected-case inventory and has one exact,
hash-pinned row shape.  The packet root may contain a superset (useful for
canaries), but the draft root and batch-result rows must match the selected set
exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPO_ROOT, REPO_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from evidence_system.contracts.appworld_checklist_semantics import (  # noqa: E402
    SEMANTIC_REPORT_SCHEMA,
    validate_appworld_packet_checklist_semantics,
)
from evidence_system.contracts.appworld_support_pointers import (  # noqa: E402
    support_location_resolves,
)
from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts import draft_case_checklist as drafter  # noqa: E402


REPORT_SCHEMA = "appworld_remote_draft_audit.v1"
CASE_ID_RE = re.compile(r"^[0-9a-f]{7}_[1-3]$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ATTEMPT_FILE_RE = re.compile(
    r"^attempt_(?P<index>[0-9]{2})\.(?P<suffix>"
    r"api_response\.json|checklist\.json|checklist\.yaml|llm_call\.json|"
    r"reasoning_summary\.txt|stderr\.log|stdout\.log)$"
)
CODEX_WEBSOCKET_RECONNECT_EVENT_RE = re.compile(
    r"^Reconnecting\.\.\. [1-5]/5 \(unexpected status 403 Forbidden: Unknown error, "
    r"url: wss://chatgpt\.com/backend-api/codex/responses, "
    r"cf-ray: [0-9a-f]+-[A-Z]+\)$"
)
CODEX_HTTPS_FALLBACK_ITEM_RE = re.compile(
    r"^Falling back from WebSockets to HTTPS transport\. unexpected status 403 Forbidden: "
    r"Unknown error, url: wss://chatgpt\.com/backend-api/codex/responses, "
    r"cf-ray: [0-9a-f]+-[A-Z]+$"
)
CANONICAL_SUFFIXES = (
    "api_response.json",
    "checklist.json",
    "checklist.yaml",
    "llm_call.json",
    "reasoning_summary.txt",
    "stderr.log",
    "stdout.log",
)
ROOT_BATCH_FILES = frozenset({"_batch_results.jsonl", "_batch_summary.json"})
INVENTORY_FIELDS = frozenset(
    {
        "case_unit_id",
        "task_id",
        "domain",
        "dataset_name",
        "split",
        "source_ref",
        "case_packet_sha256",
        "raw_case_manifest_sha256",
    }
)
TOKEN_BUDGETS = (12_000, 16_000, 20_000)
LARGE_THRESHOLD_BYTES = 100_000
DIRECT_STDIN_POLICY = "direct_stdin_sealed_bundle_v1"
SUPPLEMENT_PATH = (
    REPO_ROOT
    / "neurips_ed_track_minimal/prompts/appworld_gpt56_draft_strict_v3.supplement.md"
)


class AuditError(RuntimeError):
    """A deterministic audit condition failed."""


T = TypeVar("T")


@dataclass(frozen=True)
class CheckValue:
    value: Any
    details: Mapping[str, Any]


@dataclass(frozen=True)
class DraftRuntimeFiles:
    root: Path
    prompt: Path
    supplement: Path
    template: Path
    schema: Path


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be an object")
    return value


def _regular_file(path: Path, label: str) -> Path:
    _require(path.is_file() and not path.is_symlink(), f"{label} is missing or unsafe: {path}")
    return path


def _directory(path: Path, label: str) -> Path:
    _require(path.is_dir() and not path.is_symlink(), f"{label} is missing or unsafe: {path}")
    return path


def _draft_runtime_files(root: Path) -> DraftRuntimeFiles:
    return DraftRuntimeFiles(
        root=root,
        prompt=_regular_file(
            root / "prompts/draft_case_checklist.prompt.md", "runtime base draft prompt"
        ),
        supplement=_regular_file(
            root / "prompts/appworld_gpt56_draft_strict_v3.supplement.md",
            "runtime AppWorld strict-v3 supplement",
        ),
        template=_regular_file(
            root / "templates/case_checklist.template.yaml", "runtime checklist template"
        ),
        schema=_regular_file(
            root / "schemas/case_checklist.schema.json", "runtime checklist schema"
        ),
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_object(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_json(path: Path, label: str) -> Any:
    _regular_file(path, label)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"{label} is not valid UTF-8 JSON: {exc}") from exc


def _load_jsonl(path: Path, label: str) -> list[Mapping[str, Any]]:
    _regular_file(path, label)
    rows: list[Mapping[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise AuditError(f"{label} is not UTF-8: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        _require(line.strip() != "", f"{label} contains a blank line at {line_number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AuditError(f"{label} line {line_number} is malformed JSON: {exc}") from exc
        rows.append(_mapping(value, f"{label} line {line_number}"))
    _require(rows, f"{label} is empty")
    return rows


def _parse_timestamp(value: Any, label: str) -> datetime:
    _require(isinstance(value, str) and value, f"{label} must be a timestamp string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuditError(f"{label} is not ISO-8601: {value}") from exc
    _require(parsed.tzinfo is not None, f"{label} must include a UTC offset")
    return parsed


def _path_ends_with(raw: Any, expected_parts: Sequence[str], label: str) -> None:
    _require(isinstance(raw, str) and raw, f"{label} must be a nonempty path")
    parts = PurePosixPath(raw.replace("\\", "/")).parts
    _require(
        tuple(parts[-len(expected_parts) :]) == tuple(expected_parts),
        f"{label} does not end with {'/'.join(expected_parts)}: {raw}",
    )


def _case_id(row: Mapping[str, Any], label: str) -> str:
    values = [
        row.get(key)
        for key in ("case_unit_id", "case_unit_dir", "task_id", "id")
        if row.get(key) is not None
    ]
    _require(values, f"{label} has no supported case identity field")
    unique = {str(value) for value in values}
    _require(len(unique) == 1, f"{label} has conflicting case identities: {sorted(unique)}")
    case_id = next(iter(unique))
    _require(CASE_ID_RE.fullmatch(case_id) is not None, f"{label} has invalid AppWorld ID: {case_id}")
    return case_id


def _case_rows(path: Path, expected_count: int) -> tuple[list[str], dict[str, Mapping[str, Any]]]:
    rows = _load_jsonl(path, "cases JSONL")
    ids: list[str] = []
    for index, row in enumerate(rows, start=1):
        label = f"cases JSONL row {index}"
        _require(set(row) == INVENTORY_FIELDS, f"{label} field set drift")
        case_id = _case_id(row, label)
        for hash_field in ("case_packet_sha256", "raw_case_manifest_sha256"):
            hash_value = row.get(hash_field)
            _require(
                isinstance(hash_value, str) and SHA256_RE.fullmatch(hash_value) is not None,
                f"{label} {hash_field} must be a lowercase SHA-256 digest",
            )
        ids.append(case_id)
    duplicates = sorted(case_id for case_id, count in Counter(ids).items() if count > 1)
    _require(not duplicates, f"cases JSONL has duplicate case IDs: {duplicates[:10]}")
    _require(
        len(ids) == expected_count,
        f"cases JSONL count {len(ids)} differs from --expected-count {expected_count}",
    )
    return sorted(ids), {case_id: row for case_id, row in zip(ids, rows, strict=True)}


def _audit_draft_root_inventory(draft_root: Path, expected_ids: Sequence[str]) -> CheckValue:
    entries = list(draft_root.iterdir())
    expected_case_names = set(expected_ids)
    expected_names = expected_case_names | set(ROOT_BATCH_FILES)
    names = {entry.name for entry in entries}
    duplicate_names = len(names) != len(entries)
    _require(not duplicate_names, "draft root contains duplicate directory entries")

    unsafe_entries: list[dict[str, str]] = []
    for entry in entries:
        if entry.is_symlink():
            entry_kind = "symlink"
        elif entry.name in expected_case_names and entry.is_dir():
            continue
        elif entry.name in ROOT_BATCH_FILES and entry.is_file():
            continue
        elif entry.is_dir():
            entry_kind = "directory"
        elif entry.is_file():
            entry_kind = "regular_file"
        else:
            entry_kind = "special"
        unsafe_entries.append({"name": entry.name, "kind": entry_kind})

    missing_entries = sorted(expected_names - names)
    extra_entries = sorted(names - expected_names)
    _require(not missing_entries, f"draft root is missing required entries: {missing_entries[:10]}")
    _require(not extra_entries, f"draft root contains extra entries: {extra_entries[:10]}")
    _require(
        not unsafe_entries,
        f"draft root contains wrong-type, symlink, or special entries: {unsafe_entries[:10]}",
    )
    return CheckValue(
        None,
        {
            "case_directory_count": len(expected_case_names),
            "batch_file_count": len(ROOT_BATCH_FILES),
            "allowed_entry_count": len(expected_names),
            "extra_entries": [],
            "missing_entries": [],
            "unsafe_entries": [],
        },
    )


def _iter_support_pointers(node: Any) -> list[str]:
    pointers: list[str] = []
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key == "support" and isinstance(value, list):
                pointers.extend(str(item) for item in value)
            else:
                pointers.extend(_iter_support_pointers(value))
    elif isinstance(node, list):
        for value in node:
            pointers.extend(_iter_support_pointers(value))
    return pointers


def _workspace_files(packet_path: Path, runtime: DraftRuntimeFiles) -> dict[str, str]:
    base = runtime.prompt.read_text(encoding="utf-8")
    supplement = runtime.supplement.read_text(encoding="utf-8")
    template = runtime.template.read_text(encoding="utf-8")
    schema = _mapping(_load_json(runtime.schema, "checklist schema"), "checklist schema")
    return drafter.build_codex_workspace_files(
        instructions=drafter.compose_prompt(base, supplement),
        template_text=template,
        case_packet_text=packet_path.read_text(encoding="utf-8"),
        model_output_schema=drafter.build_model_output_schema(dict(schema)),
    )


class CaseRecorder:
    def __init__(self, case_id: str) -> None:
        self.report: dict[str, Any] = {
            "case_unit_id": case_id,
            "status": "failed",
            "checks": {},
            "errors": [],
            "warnings": [],
        }

    def check(self, name: str, callback: Callable[[], CheckValue]) -> Any | None:
        try:
            result = callback()
        except Exception as exc:  # Each case must retain all independent findings.
            self.report["checks"][name] = {"status": "failed"}
            self.report["errors"].append(
                {"check": name, "error_type": type(exc).__name__, "message": str(exc)}
            )
            return None
        self.report["checks"][name] = {"status": "passed", **dict(result.details)}
        return result.value

    def warn(self, code: str, message: str) -> None:
        self.report["warnings"].append({"code": code, "message": message})

    def finish(self) -> dict[str, Any]:
        self.report["status"] = "passed" if not self.report["errors"] else "failed"
        return self.report


def _audit_packet(
    packet_root: Path,
    case_id: str,
    inventory_row: Mapping[str, Any],
) -> CheckValue:
    packet_dir = _directory(packet_root / case_id, f"packet directory {case_id}")
    packet_path = _regular_file(packet_dir / "case_packet.md", f"case packet {case_id}")
    manifest_path = _regular_file(
        packet_dir / "raw_case_manifest.json", f"raw-case manifest {case_id}"
    )
    manifest = _mapping(_load_json(manifest_path, f"raw-case manifest {case_id}"), "raw-case manifest")
    split = manifest.get("split")
    _require(split in {"test_normal", "test_challenge"}, f"{case_id}: invalid split {split}")
    expected = {
        "case_unit_id": case_id,
        "task_id": case_id,
        "domain": "appworld",
        "dataset_name": split,
        "split": split,
        "source_ref": f"appworld://{split}/{case_id}",
    }
    for key, value in expected.items():
        _require(manifest.get(key) == value, f"{case_id}: raw manifest {key} mismatch")
        _require(
            inventory_row.get(key) == value,
            f"{case_id}: cases JSONL {key} differs from raw manifest",
        )
    _require(
        inventory_row.get("case_packet_sha256") == _sha256_file(packet_path),
        f"{case_id}: cases JSONL case-packet hash mismatch",
    )
    _require(
        inventory_row.get("raw_case_manifest_sha256") == _sha256_file(manifest_path),
        f"{case_id}: cases JSONL raw-manifest hash mismatch",
    )

    files = manifest.get("packet_files")
    hashes = _mapping(manifest.get("sha256_per_file"), f"{case_id}: source hashes")
    _require(
        isinstance(files, list) and files and all(isinstance(value, str) for value in files),
        f"{case_id}: packet_files is invalid",
    )
    _require(set(files) == set(hashes), f"{case_id}: packet source/hash inventory mismatch")
    for relative in files:
        relative_path = Path(relative)
        _require(
            not relative_path.is_absolute() and ".." not in relative_path.parts,
            f"{case_id}: unsafe source path {relative}",
        )
        source = _regular_file(packet_dir / "raw_case" / relative, f"{case_id}: source {relative}")
        _require(
            _sha256_file(source) == hashes[relative],
            f"{case_id}: official source hash mismatch for {relative}",
        )
    return CheckValue(
        (packet_dir, packet_path, dict(manifest)),
        {
            "split": split,
            "case_packet_size_bytes": packet_path.stat().st_size,
            "case_packet_sha256": _sha256_file(packet_path),
            "raw_case_manifest_sha256": _sha256_file(manifest_path),
            "official_source_count": len(files),
        },
    )


def _audit_batch_attempts(
    *,
    case_id: str,
    row: Mapping[str, Any],
    packet_path: Path,
    recorder: CaseRecorder,
) -> CheckValue:
    expected_fields = {
        "case_unit_dir",
        "case_packet",
        "case_packet_size_bytes",
        "lane",
        "status",
        "attempts",
        "quality_warnings",
        "checklist_path",
    }
    _require(set(row) == expected_fields, f"{case_id}: batch-result field set drift")
    _require(row.get("case_unit_dir") == case_id, f"{case_id}: batch identity mismatch")
    _require(row.get("status") == "success", f"{case_id}: batch row is not success")
    packet_size = packet_path.stat().st_size
    _require(row.get("case_packet_size_bytes") == packet_size, f"{case_id}: packet size mismatch")
    expected_lane = "oversized" if packet_size > LARGE_THRESHOLD_BYTES else "regular"
    _require(row.get("lane") == expected_lane, f"{case_id}: batch lane mismatch")
    _path_ends_with(
        row.get("case_packet"),
        ("case_packets", case_id, "case_packet.md"),
        f"{case_id}: batch case_packet",
    )
    _path_ends_with(
        row.get("checklist_path"),
        ("results", case_id, "checklist.yaml"),
        f"{case_id}: batch checklist_path",
    )
    quality_warnings = row.get("quality_warnings")
    _require(
        isinstance(quality_warnings, list)
        and all(isinstance(value, str) for value in quality_warnings),
        f"{case_id}: quality_warnings is invalid",
    )
    for warning in quality_warnings:
        recorder.warn("batch_quality_warning", warning)

    attempts = row.get("attempts")
    _require(
        isinstance(attempts, list) and 1 <= len(attempts) <= len(TOKEN_BUDGETS),
        f"{case_id}: attempt history must contain one to three attempts",
    )
    successful_indices: list[int] = []
    expected_http = 480 if expected_lane == "oversized" else 180
    expected_codex = 3600 if expected_lane == "oversized" else 1800
    for expected_index, raw_attempt in enumerate(attempts, start=1):
        attempt = _mapping(raw_attempt, f"{case_id}: attempt {expected_index}")
        required = {
            "attempt_index",
            "max_output_tokens",
            "http_timeout_seconds",
            "codex_timeout_seconds",
            "returncode",
            "duration_seconds",
            "stderr_tail",
        }
        _require(required <= set(attempt), f"{case_id}: attempt {expected_index} metadata is incomplete")
        _require(
            attempt.get("attempt_index") == expected_index,
            f"{case_id}: attempt index is not contiguous",
        )
        _require(
            attempt.get("max_output_tokens") == TOKEN_BUDGETS[expected_index - 1],
            f"{case_id}: attempt {expected_index} token budget mismatch",
        )
        _require(
            attempt.get("http_timeout_seconds") == expected_http
            and attempt.get("codex_timeout_seconds") == expected_codex,
            f"{case_id}: attempt {expected_index} timeout/lane mismatch",
        )
        _require(
            type(attempt.get("returncode")) is int,
            f"{case_id}: attempt {expected_index} returncode is not an integer",
        )
        duration = attempt.get("duration_seconds")
        _require(
            isinstance(duration, (int, float))
            and not isinstance(duration, bool)
            and math.isfinite(float(duration))
            and float(duration) >= 0,
            f"{case_id}: attempt {expected_index} duration is invalid",
        )
        _require(
            isinstance(attempt.get("stderr_tail"), str),
            f"{case_id}: attempt {expected_index} stderr_tail is invalid",
        )
        validator = attempt.get("validator")
        if attempt.get("returncode") == 0 and isinstance(validator, str) and validator.startswith(
            "checklist valid:"
        ):
            successful_indices.append(expected_index)
    _require(
        successful_indices == [len(attempts)],
        f"{case_id}: exactly the final attempt must be the successful validated attempt",
    )
    if len(attempts) > 1:
        recorder.warn(
            "generation_retried",
            f"{case_id} succeeded on attempt {len(attempts)} after {len(attempts) - 1} rejected attempt(s)",
        )
    return CheckValue(
        (len(attempts), dict(_mapping(attempts[-1], f"{case_id}: successful attempt"))),
        {
            "lane": expected_lane,
            "attempt_count": len(attempts),
            "successful_attempt_index": len(attempts),
            "retry_count": len(attempts) - 1,
            "quality_warning_count": len(quality_warnings),
        },
    )


def _audit_artifact_inventory(case_dir: Path, case_id: str, successful_index: int) -> CheckValue:
    _directory(case_dir, f"draft case directory {case_id}")
    entries = list(case_dir.iterdir())
    _require(
        entries and all(path.is_file() and not path.is_symlink() for path in entries),
        f"{case_id}: draft case contains a directory, symlink, or special file",
    )
    names = {path.name for path in entries}
    canonical = set(CANONICAL_SUFFIXES)
    _require(canonical <= names, f"{case_id}: canonical seven-file bundle is incomplete")
    attempts: dict[int, set[str]] = {}
    for name in names - canonical:
        match = ATTEMPT_FILE_RE.fullmatch(name)
        _require(match is not None, f"{case_id}: unsupported artifact {name}")
        attempts.setdefault(int(match.group("index")), set()).add(match.group("suffix"))
    _require(
        successful_index in attempts,
        f"{case_id}: successful attempt_{successful_index:02d} artifacts are missing",
    )
    _require(
        set(attempts) <= set(range(1, successful_index + 1)),
        f"{case_id}: artifacts exist for an attempt not present in batch metadata",
    )
    _require(
        attempts[successful_index] == canonical,
        f"{case_id}: successful attempt seven-file bundle is incomplete",
    )
    canonical_hashes: dict[str, str] = {}
    for suffix in CANONICAL_SUFFIXES:
        canonical_path = _regular_file(case_dir / suffix, f"{case_id}: canonical {suffix}")
        attempt_path = _regular_file(
            case_dir / f"attempt_{successful_index:02d}.{suffix}",
            f"{case_id}: successful attempt {suffix}",
        )
        canonical_hash = _sha256_file(canonical_path)
        _require(
            canonical_hash == _sha256_file(attempt_path),
            f"{case_id}: canonical {suffix} differs from successful attempt bytes",
        )
        canonical_hashes[suffix] = canonical_hash
    return CheckValue(
        canonical_hashes,
        {
            "canonical_file_count": len(CANONICAL_SUFFIXES),
            "successful_attempt_file_count": len(attempts[successful_index]),
            "preserved_attempt_indices": sorted(attempts),
            "canonical_sha256": canonical_hashes,
        },
    )


def _audit_checklist_pair(case_dir: Path, case_id: str) -> CheckValue:
    yaml_path = _regular_file(case_dir / "checklist.yaml", f"{case_id}: checklist YAML")
    json_path = _regular_file(case_dir / "checklist.json", f"{case_id}: checklist JSON")
    try:
        checklist_yaml = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise AuditError(f"{case_id}: checklist YAML is malformed: {exc}") from exc
    checklist_json = _mapping(_load_json(json_path, f"{case_id}: checklist JSON"), "checklist JSON")
    _require(isinstance(checklist_yaml, Mapping), f"{case_id}: checklist YAML is not an object")
    _require(dict(checklist_yaml) == dict(checklist_json), f"{case_id}: YAML/JSON semantic mismatch")
    for key, expected in (
        ("schema_version", "case_checklist_v1"),
        ("case_unit_id", case_id),
        ("task_id", case_id),
        ("domain", "appworld"),
    ):
        _require(checklist_json.get(key) == expected, f"{case_id}: checklist {key} mismatch")
    return CheckValue(
        dict(checklist_json),
        {
            "checklist_json_sha256": _sha256_file(json_path),
            "checklist_yaml_sha256": _sha256_file(yaml_path),
            "semantic_sha256": _sha256_object(checklist_json),
        },
    )


def _audit_schema(
    checklist: Mapping[str, Any], case_id: str, runtime: DraftRuntimeFiles
) -> CheckValue:
    schema = _mapping(_load_json(runtime.schema, "checklist schema"), "checklist schema")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(checklist),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(value) for value in error.absolute_path) or "<root>"
        raise AuditError(f"{case_id}: schema failure at {location}: {error.message}")
    return CheckValue(None, {"schema_sha256": _sha256_file(runtime.schema)})


def _audit_guardrails(checklist: Mapping[str, Any], packet_path: Path, case_id: str) -> CheckValue:
    packet_text = packet_path.read_text(encoding="utf-8")
    allowed = case_packet_support_paths(packet_text)
    try:
        validate_checklist_guardrails(dict(checklist), allowed_source_paths=allowed)
    except Exception as exc:
        raise AuditError(f"{case_id}: packet-aware checklist guardrails failed: {exc}") from exc
    return CheckValue(None, {"allowed_packet_source_path_count": len(allowed)})


def _audit_support_pointers(
    checklist: Mapping[str, Any],
    packet_dir: Path,
    packet_path: Path,
    manifest: Mapping[str, Any],
    case_id: str,
) -> CheckValue:
    pointers = _iter_support_pointers(checklist)
    _require(pointers, f"{case_id}: checklist has no support pointers")
    hashes = _mapping(manifest.get("sha256_per_file"), f"{case_id}: source hashes")
    for pointer in pointers:
        path_part, separator, location = pointer.partition("::")
        _require(
            separator == "::" and path_part and location and location == location.strip(),
            f"{case_id}: malformed support pointer {pointer}",
        )
        if path_part == "case_packet.md":
            source = packet_path
        else:
            _require(path_part in hashes, f"{case_id}: support path outside packet: {path_part}")
            source = _regular_file(
                packet_dir / "raw_case" / path_part,
                f"{case_id}: support source {path_part}",
            )
            _require(
                _sha256_file(source) == hashes[path_part],
                f"{case_id}: support source hash mismatch: {path_part}",
            )
        _require(
            support_location_resolves(source, location),
            f"{case_id}: support location does not resolve: {pointer}",
        )
    return CheckValue(
        None,
        {
            "support_pointer_count": len(pointers),
            "unique_support_pointer_count": len(set(pointers)),
        },
    )


def _audit_semantics(checklist: Mapping[str, Any], packet_dir: Path, case_id: str) -> CheckValue:
    try:
        audit = validate_appworld_packet_checklist_semantics(
            case_packet_root=packet_dir,
            checklist=checklist,
        )
    except Exception as exc:
        raise AuditError(f"{case_id}: exact native/stronger semantics failed: {exc}") from exc
    _require(
        audit.get("schema_version") == SEMANTIC_REPORT_SCHEMA
        and audit.get("status") == "passed"
        and audit.get("case_id") == case_id,
        f"{case_id}: semantic audit identity mismatch",
    )
    stronger = _mapping(audit.get("stronger_gap_composition"), f"{case_id}: stronger audit")
    return CheckValue(
        None,
        {
            "semantic_report_schema": SEMANTIC_REPORT_SCHEMA,
            "semantic_audit_sha256": _sha256_object(audit),
            "scoring_block_count": audit.get("scoring_block_count"),
            "native_required_field_count": audit.get("native_required_field_count"),
            "stronger_required_field_count": audit.get("stronger_required_field_count"),
            "stronger_gap_count": stronger.get("gap_count"),
        },
    )


def _audit_llm_identity(
    llm_call: Mapping[str, Any],
    api_response: Mapping[str, Any],
    attempt: Mapping[str, Any],
    case_id: str,
    attempt_index: int,
    expected_model: str,
    expected_reasoning: str,
) -> CheckValue:
    expected_fields = {
        "schema_version",
        "provider",
        "model",
        "model_version",
        "api_key_env",
        "domain",
        "case_unit_id",
        "task_id",
        "phase",
        "experiment_type",
        "agent_id_or_role",
        "request_timestamp",
        "response_timestamp",
        "temperature",
        "max_tokens",
        "timeout_seconds",
        "retry_index",
        "token_usage",
        "cost",
        "response_metadata",
    }
    _require(set(llm_call) == expected_fields, f"{case_id}: llm_call field set drift")
    identities = {
        "schema_version": "llm_call/v1",
        "provider": "codex_cli",
        "model": expected_model,
        "model_version": expected_model,
        "api_key_env": "CODEX_HOME",
        "domain": "appworld",
        "case_unit_id": case_id,
        "task_id": case_id,
        "phase": "draft",
        "experiment_type": "minimal_package",
        "agent_id_or_role": "case_checklist_drafter",
        "temperature": 0.0,
        "max_tokens": attempt.get("max_output_tokens"),
        "timeout_seconds": attempt.get("codex_timeout_seconds"),
        "retry_index": 0,
    }
    for key, expected in identities.items():
        _require(llm_call.get(key) == expected, f"{case_id}: llm_call.{key} mismatch")
    requested = _parse_timestamp(llm_call.get("request_timestamp"), f"{case_id}: request timestamp")
    responded = _parse_timestamp(llm_call.get("response_timestamp"), f"{case_id}: response timestamp")
    _require(requested <= responded, f"{case_id}: response precedes request")

    metadata = _mapping(llm_call.get("response_metadata"), f"{case_id}: response metadata")
    metadata_fields = {
        "response_id",
        "response_status",
        "provider_model",
        "reasoning_effort",
        "model_verbosity",
        "service_tier",
        "provider_created_at",
        "provider_completed_at",
        "raw_api_response_path",
        "reasoning_summary_path",
        "auth_mode",
        "max_output_tokens_enforced",
    }
    _require(set(metadata) == metadata_fields, f"{case_id}: response metadata field set drift")
    for key, expected in (
        ("response_status", "completed"),
        ("provider_model", expected_model),
        ("reasoning_effort", expected_reasoning),
        ("model_verbosity", drafter.DEFAULT_DRAFT_VERBOSITY),
        ("auth_mode", "codex_login"),
        ("max_output_tokens_enforced", False),
    ):
        _require(metadata.get(key) == expected, f"{case_id}: response metadata {key} mismatch")
    _require(
        metadata.get("service_tier") is None
        and metadata.get("provider_created_at") is None
        and metadata.get("provider_completed_at") is None,
        f"{case_id}: unavailable provider metadata must remain null",
    )
    _path_ends_with(
        metadata.get("raw_api_response_path"),
        (case_id, f"attempt_{attempt_index:02d}.api_response.json"),
        f"{case_id}: raw API response path",
    )
    _path_ends_with(
        metadata.get("reasoning_summary_path"),
        (case_id, f"attempt_{attempt_index:02d}.reasoning_summary.txt"),
        f"{case_id}: reasoning path",
    )
    _require(
        api_response.get("id") == metadata.get("response_id"),
        f"{case_id}: API/llm_call response identity mismatch",
    )
    _require(
        api_response.get("status") == "completed"
        and api_response.get("provider") == "codex_cli"
        and api_response.get("model") == expected_model,
        f"{case_id}: API provider/model/status mismatch",
    )
    codex = _mapping(api_response.get("codex_cli"), f"{case_id}: codex_cli")
    _require(
        codex.get("timeout_seconds") == llm_call.get("timeout_seconds"),
        f"{case_id}: Codex/llm_call timeout mismatch",
    )
    usage = _mapping(llm_call.get("token_usage"), f"{case_id}: token usage")
    expected_usage_fields = {
        "prompt_tokens",
        "completion_tokens",
        "cached_prompt_tokens",
        "reasoning_tokens",
        "total_tokens",
    }
    _require(set(usage) == expected_usage_fields, f"{case_id}: token usage field set drift")
    _require(
        dict(usage) == drafter.extract_token_usage(dict(api_response)),
        f"{case_id}: llm_call token usage is not the API projection",
    )
    _require(
        all(type(value) is int and value >= 0 for value in usage.values())
        and usage.get("total_tokens") == usage.get("prompt_tokens") + usage.get("completion_tokens"),
        f"{case_id}: token usage values are invalid",
    )
    _require(
        usage.get("prompt_tokens", 0) > 0
        and usage.get("completion_tokens", 0) > 0
        and usage.get("total_tokens", 0) > 0,
        f"{case_id}: readable provider token usage must be nonzero",
    )
    _require(
        usage.get("cached_prompt_tokens", 0) <= usage.get("prompt_tokens", 0)
        and usage.get("reasoning_tokens", 0) <= usage.get("completion_tokens", 0),
        f"{case_id}: token usage detail exceeds its parent count",
    )
    expected_cost = {
        "amount": None,
        "currency": "USD",
        "pricing_source": "provider_usage",
        "pricing_table_id": None,
        "pricing_table_version": None,
        "pricing_source_hash": None,
        "cost_calculation_method": "unavailable",
        "missing_cost_reason": "provider_cost_unavailable",
        "total_cost_usd": None,
        "cost_details": None,
    }
    _require(llm_call.get("cost") == expected_cost, f"{case_id}: cost provenance mismatch")
    return CheckValue(
        None,
        {
            "provider": "codex_cli",
            "model": expected_model,
            "reasoning_effort": expected_reasoning,
            "response_id": metadata.get("response_id"),
            "request_timestamp": llm_call.get("request_timestamp"),
            "response_timestamp": llm_call.get("response_timestamp"),
            "token_usage": dict(usage),
        },
    )


def _audit_codex_runtime_envelope(
    api_response: Mapping[str, Any], case_id: str
) -> CheckValue:
    _require(
        set(api_response)
        == {"id", "status", "model", "provider", "output_text", "output", "usage", "codex_cli"},
        f"{case_id}: API response field set drift",
    )
    codex = _mapping(api_response.get("codex_cli"), f"{case_id}: codex_cli")
    expected_codex_fields = {
        "auth_mode",
        "returncode",
        "timeout_seconds",
        "sandbox",
        "command",
        "stdin_bundle",
        "events",
        "malformed_event_lines",
        "stderr",
    }
    _require(set(codex) == expected_codex_fields, f"{case_id}: codex_cli field set drift")
    _require(
        codex.get("auth_mode") == "codex_login" and codex.get("returncode") == 0,
        f"{case_id}: Codex auth/return code mismatch",
    )
    _require(isinstance(codex.get("stderr"), str), f"{case_id}: Codex stderr is not text")
    return CheckValue(
        dict(codex),
        {
            "auth_mode": "codex_login",
            "returncode": 0,
        },
    )


def _audit_argv(
    codex: Mapping[str, Any],
    case_id: str,
    expected_model: str,
    expected_reasoning: str,
) -> CheckValue:
    command = codex.get("command")
    _require(
        isinstance(command, list) and command and all(isinstance(value, str) for value in command),
        f"{case_id}: Codex argv is not a nonempty string list",
    )
    _require(
        all(re.search(r"[\x00-\x1f\x7f]", value) is None for value in command),
        f"{case_id}: Codex argv contains a control character",
    )
    launcher = command[0]
    _require(
        Path(launcher).name in {"codex", "codex.js"},
        f"{case_id}: unexpected Codex launcher {launcher}",
    )
    _require("--cd" in command, f"{case_id}: Codex argv has no --cd")
    cd_index = command.index("--cd")
    _require(cd_index + 1 < len(command), f"{case_id}: Codex --cd is incomplete")
    workspace = Path(command[cd_index + 1])
    _require(
        workspace.is_absolute()
        and workspace.parent == Path("/tmp")
        and workspace.name.startswith("case-checklist-codex-"),
        f"{case_id}: Codex workspace is not an isolated /tmp directory",
    )
    expected = [
        launcher,
        "exec",
        "--strict-config",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--model",
        expected_model,
        "-c",
        f'model_reasoning_effort="{expected_reasoning}"',
        "-c",
        f'model_verbosity="{drafter.DEFAULT_DRAFT_VERBOSITY}"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(workspace / "output_schema.json"),
        "-o",
        str(workspace / "draft_body.json"),
        "-",
    ]
    _require(command == expected, f"{case_id}: Codex argv flags/tool-disable policy drift")
    _require(
        codex.get("sandbox") == "read-only",
        f"{case_id}: Codex sandbox must be read-only on the draft VPS",
    )
    return CheckValue(
        workspace,
        {
            "launcher": launcher,
            "sandbox": "read-only",
            "shell_tool_disabled": True,
            "unified_exec_disabled": True,
            "stdin_transport": True,
        },
    )


def _audit_stderr_evidence(
    *,
    codex: Mapping[str, Any],
    case_dir: Path,
    successful_attempt: Mapping[str, Any],
    case_id: str,
) -> CheckValue:
    codex_stderr = codex.get("stderr")
    _require(isinstance(codex_stderr, str), f"{case_id}: Codex stderr is not text")
    stderr_path = _regular_file(case_dir / "stderr.log", f"{case_id}: canonical stderr")
    try:
        runner_stderr = stderr_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AuditError(f"{case_id}: canonical stderr is not UTF-8: {exc}") from exc
    expected_tail = (
        runner_stderr.strip().splitlines()[-1] if runner_stderr.strip() else ""
    )
    _require(
        successful_attempt.get("stderr_tail") == expected_tail,
        f"{case_id}: successful batch stderr_tail differs from canonical stderr.log final stripped line",
    )
    return CheckValue(
        (codex_stderr, runner_stderr),
        {
            "batch_stderr_tail_rule": "stderr.strip().splitlines()[-1] if stderr.strip() else ''",
            "batch_stderr_tail": expected_tail,
            "codex_stderr_size_bytes": len(codex_stderr.encode("utf-8")),
            "codex_stderr_sha256": hashlib.sha256(codex_stderr.encode("utf-8")).hexdigest(),
            "runner_stderr_size_bytes": stderr_path.stat().st_size,
            "runner_stderr_sha256": _sha256_file(stderr_path),
        },
    )


def _audit_stdin_bundle(
    codex: Mapping[str, Any],
    packet_path: Path,
    case_id: str,
    runtime: DraftRuntimeFiles,
) -> CheckValue:
    metadata = _mapping(codex.get("stdin_bundle"), f"{case_id}: stdin bundle")
    expected_fields = {
        "schema_version",
        "policy",
        "total_sha256",
        "total_size_bytes",
        "components",
    }
    _require(set(metadata) == expected_fields, f"{case_id}: stdin bundle field set drift")
    try:
        stdin_text, rebuilt = drafter.build_codex_stdin_bundle(
            _workspace_files(packet_path, runtime)
        )
    except Exception as exc:
        raise AuditError(f"{case_id}: could not rebuild direct-stdin bundle: {exc}") from exc
    _require(stdin_text.endswith("\n") and "\r" not in stdin_text, f"{case_id}: rebuilt stdin is not LF text")
    _require(
        rebuilt.get("schema_version") == "codex_direct_stdin_bundle.v1"
        and rebuilt.get("policy") == DIRECT_STDIN_POLICY,
        f"{case_id}: rebuilt stdin identity drift",
    )
    _require(dict(metadata) == rebuilt, f"{case_id}: stored stdin manifest differs from local reconstruction")
    return CheckValue(
        None,
        {
            "policy": DIRECT_STDIN_POLICY,
            "total_sha256": rebuilt["total_sha256"],
            "total_size_bytes": rebuilt["total_size_bytes"],
            "component_count": len(rebuilt["components"]),
            "components": rebuilt["components"],
        },
    )


def _audit_events_and_output(
    *,
    api_response: Mapping[str, Any],
    codex: Mapping[str, Any],
    checklist: Mapping[str, Any],
    reasoning_summary: str,
    case_id: str,
) -> CheckValue:
    _require(codex.get("malformed_event_lines") == [], f"{case_id}: malformed Codex events exist")
    events = codex.get("events")
    _require(
        isinstance(events, list) and events and all(isinstance(event, Mapping) for event in events),
        f"{case_id}: Codex event stream is empty or invalid",
    )
    allowed_events = {
        "thread.started",
        "turn.started",
        "item.started",
        "item.completed",
        "turn.completed",
    }
    item_events: list[tuple[int, Mapping[str, Any]]] = []
    messages: list[tuple[int, Mapping[str, Any]]] = []
    reasoning_count = 0
    websocket_reconnect_event_count = 0
    https_fallback_item_count = 0
    for index, event in enumerate(events):
        event_type = event.get("type")
        if event_type == "error":
            _require(
                set(event) == {"type", "message"}
                and isinstance(event.get("message"), str)
                and CODEX_WEBSOCKET_RECONNECT_EVENT_RE.fullmatch(event["message"]),
                f"{case_id}: forbidden error event",
            )
            websocket_reconnect_event_count += 1
            continue
        _require(event_type in allowed_events, f"{case_id}: forbidden event type {event_type}")
        if str(event_type).startswith("item."):
            item = _mapping(event.get("item"), f"{case_id}: event item {index}")
            item_type = item.get("type")
            if item_type == "error":
                _require(
                    event_type == "item.completed"
                    and set(item) == {"id", "type", "message"}
                    and isinstance(item.get("id"), str)
                    and re.fullmatch(r"item_[0-9]+", item["id"])
                    and isinstance(item.get("message"), str)
                    and CODEX_HTTPS_FALLBACK_ITEM_RE.fullmatch(item["message"]),
                    f"{case_id}: forbidden error item",
                )
                https_fallback_item_count += 1
                continue
            _require(
                item_type in {"reasoning", "agent_message"},
                f"{case_id}: forbidden tool/item event {item_type}",
            )
            _require(
                event_type == "item.completed",
                f"{case_id}: direct-stdin item must be completed-only",
            )
            item_events.append((index, item))
            if item_type == "agent_message":
                messages.append((index, item))
            else:
                reasoning_count += 1
        else:
            _require(event.get("item") is None, f"{case_id}: non-item event contains item data")

    thread_started = [event for event in events if event.get("type") == "thread.started"]
    turn_started = [event for event in events if event.get("type") == "turn.started"]
    turn_completed = [event for event in events if event.get("type") == "turn.completed"]
    _require(
        len(thread_started) == 1
        and events[0] is thread_started[0]
        and thread_started[0].get("thread_id") == api_response.get("id"),
        f"{case_id}: thread.started lifecycle/identity mismatch",
    )
    _require(len(turn_started) == 1, f"{case_id}: turn.started must be unique")
    first_item_index = item_events[0][0] if item_events else len(events)
    _require(
        0 < events.index(turn_started[0]) < first_item_index,
        f"{case_id}: turn.started does not precede all item events",
    )
    _require(
        len(turn_completed) == 1 and events[-1] is turn_completed[0],
        f"{case_id}: turn.completed must be unique and final",
    )
    _require(len(messages) == 1, f"{case_id}: exactly one final agent_message is required")
    _require(
        item_events and messages[0][0] == item_events[-1][0],
        f"{case_id}: agent_message is not the final item event",
    )

    output_text = api_response.get("output_text")
    _require(isinstance(output_text, str), f"{case_id}: output_text is not text")
    try:
        body = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise AuditError(f"{case_id}: output_text is malformed JSON: {exc}") from exc
    _require(isinstance(body, dict), f"{case_id}: output_text JSON is not an object")
    recovered = drafter.recover_json_output_from_events([dict(event) for event in events])
    _require(recovered == body, f"{case_id}: output_text is not the final agent_message projection")
    expected_body = {
        key: value
        for key, value in checklist.items()
        if key not in {"schema_version", "case_unit_id", "domain", "task_id"}
    }
    _require(
        drafter.strip_null_fields(body) == expected_body,
        f"{case_id}: final agent message differs from canonical checklist content",
    )
    _require(
        drafter.extract_json_text(dict(api_response)) == body,
        f"{case_id}: API JSON extraction differs from output_text",
    )
    reasoning_fragments = drafter.extract_codex_reasoning_fragments(
        [dict(event) for event in events]
    )
    expected_output = [
        {
            "type": "reasoning",
            "summary": [
                {"type": "summary_text", "text": text} for text in reasoning_fragments
            ],
        },
        {"type": "message", "content": [{"type": "output_text", "text": output_text}]},
    ]
    _require(api_response.get("output") == expected_output, f"{case_id}: API output projection mismatch")
    extracted_reasoning = drafter.extract_reasoning_summary_text(dict(api_response))
    _require(
        reasoning_summary == extracted_reasoning + ("\n" if extracted_reasoning else ""),
        f"{case_id}: reasoning summary sidecar mismatch",
    )
    normalized_usage = drafter.normalize_codex_usage([dict(event) for event in events])
    _require(api_response.get("usage") == normalized_usage, f"{case_id}: API usage/event mismatch")
    return CheckValue(
        None,
        {
            "event_count": len(events),
            "item_event_count": len(item_events),
            "reasoning_item_count": reasoning_count,
            "agent_message_count": len(messages),
            "tool_item_count": 0,
            "command_event_count": 0,
            "websocket_reconnect_event_count": websocket_reconnect_event_count,
            "https_fallback_item_count": https_fallback_item_count,
            "final_agent_message_event_index": messages[0][0],
            "output_body_sha256": _sha256_object(body),
        },
    )


def _audit_case(
    *,
    case_id: str,
    inventory_row: Mapping[str, Any],
    packet_root: Path,
    draft_root: Path,
    batch_row: Mapping[str, Any] | None,
    expected_model: str,
    expected_reasoning: str,
    runtime: DraftRuntimeFiles,
) -> dict[str, Any]:
    recorder = CaseRecorder(case_id)
    packet_result = recorder.check(
        "packet_identity_and_sources",
        lambda: _audit_packet(packet_root, case_id, inventory_row),
    )
    packet_dir: Path | None = None
    packet_path: Path | None = None
    manifest: Mapping[str, Any] | None = None
    if packet_result is not None:
        packet_dir, packet_path, manifest = packet_result

    attempt_result: tuple[int, Mapping[str, Any]] | None = None
    if batch_row is None:
        recorder.report["checks"]["batch_success_and_attempt_metadata"] = {"status": "failed"}
        recorder.report["errors"].append(
            {
                "check": "batch_success_and_attempt_metadata",
                "error_type": "AuditError",
                "message": f"{case_id}: batch-result row is missing",
            }
        )
    elif packet_path is not None:
        attempt_result = recorder.check(
            "batch_success_and_attempt_metadata",
            lambda: _audit_batch_attempts(
                case_id=case_id,
                row=batch_row,
                packet_path=packet_path,
                recorder=recorder,
            ),
        )

    case_dir = draft_root / case_id
    successful_index: int | None = attempt_result[0] if attempt_result is not None else None
    successful_attempt: Mapping[str, Any] | None = (
        attempt_result[1] if attempt_result is not None else None
    )
    if successful_index is not None:
        recorder.check(
            "canonical_and_successful_attempt_bytes",
            lambda: _audit_artifact_inventory(case_dir, case_id, successful_index),
        )

    checklist = recorder.check(
        "yaml_json_consistency",
        lambda: _audit_checklist_pair(case_dir, case_id),
    )
    if checklist is not None:
        recorder.check(
            "json_schema", lambda: _audit_schema(checklist, case_id, runtime)
        )
        if packet_path is not None:
            recorder.check(
                "packet_aware_guardrails",
                lambda: _audit_guardrails(checklist, packet_path, case_id),
            )
        if packet_dir is not None and packet_path is not None and manifest is not None:
            recorder.check(
                "support_pointers",
                lambda: _audit_support_pointers(
                    checklist, packet_dir, packet_path, manifest, case_id
                ),
            )
            recorder.check(
                "exact_native_and_stronger_semantics",
                lambda: _audit_semantics(checklist, packet_dir, case_id),
            )

    if successful_index is not None and successful_attempt is not None:
        llm_path = case_dir / "llm_call.json"
        api_path = case_dir / "api_response.json"
        reasoning_path = case_dir / "reasoning_summary.txt"
        llm_call: Mapping[str, Any] | None = None
        api_response: Mapping[str, Any] | None = None
        try:
            llm_call = _mapping(_load_json(llm_path, f"{case_id}: llm_call"), "llm_call")
            api_response = _mapping(
                _load_json(api_path, f"{case_id}: API response"), "API response"
            )
        except Exception as exc:
            recorder.report["checks"]["llm_call_identity"] = {"status": "failed"}
            recorder.report["errors"].append(
                {
                    "check": "llm_call_identity",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
        if llm_call is not None and api_response is not None:
            recorder.check(
                "llm_call_identity",
                lambda: _audit_llm_identity(
                    llm_call,
                    api_response,
                    successful_attempt,
                    case_id,
                    successful_index,
                    expected_model,
                    expected_reasoning,
                ),
            )
            codex = recorder.check(
                "codex_runtime_envelope",
                lambda: _audit_codex_runtime_envelope(api_response, case_id),
            )
            if codex is not None:
                recorder.check(
                    "tool_disabled_argv",
                    lambda: _audit_argv(codex, case_id, expected_model, expected_reasoning),
                )
                if packet_path is not None:
                    recorder.check(
                        "direct_stdin_bundle_reconstruction",
                        lambda: _audit_stdin_bundle(
                            codex, packet_path, case_id, runtime
                        ),
                    )
                stderr_evidence = recorder.check(
                    "stderr_and_batch_tail",
                    lambda: _audit_stderr_evidence(
                        codex=codex,
                        case_dir=case_dir,
                        successful_attempt=successful_attempt,
                        case_id=case_id,
                    ),
                )
                if stderr_evidence is not None:
                    codex_stderr, runner_stderr = stderr_evidence
                    if codex_stderr.strip():
                        recorder.warn(
                            "codex_stderr_nonempty",
                            f"{case_id}: successful Codex call retained nonempty stderr",
                        )
                    if runner_stderr.strip():
                        recorder.warn(
                            "runner_stderr_nonempty",
                            f"{case_id}: successful draft runner retained nonempty stderr",
                        )
            try:
                reasoning_summary = _regular_file(
                    reasoning_path, f"{case_id}: reasoning summary"
                ).read_text(encoding="utf-8")
            except Exception as exc:
                recorder.report["checks"]["events_lifecycle_and_final_message"] = {
                    "status": "failed"
                }
                recorder.report["errors"].append(
                    {
                        "check": "events_lifecycle_and_final_message",
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    }
                )
            else:
                if codex is not None:
                    recorder.check(
                        "events_lifecycle_and_final_message",
                        lambda: _audit_events_and_output(
                            api_response=api_response,
                            codex=codex,
                            checklist=checklist or {},
                            reasoning_summary=reasoning_summary,
                            case_id=case_id,
                        ),
                    )
    return recorder.finish()


def _audit_batch_summary(
    *,
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    expected_count: int,
    expected_model: str,
    expected_reasoning: str,
) -> dict[str, Any]:
    required_fields = {
        "started_at",
        "updated_at",
        "total_cases",
        "completed_cases",
        "success_cases",
        "skipped_cases",
        "failed_cases",
        "not_run_case_count",
        "not_run_case_ids",
        "warning_count",
        "provider",
        "model",
        "reasoning_effort",
        "codex_sandbox",
        "prompt_supplement",
        "token_budgets",
        "sort_by",
        "quality_check",
        "large_case_threshold_bytes",
        "lane_stats",
        "output_root",
    }
    _require(required_fields <= set(summary), "batch summary is missing required fields")
    started = _parse_timestamp(summary.get("started_at"), "batch started_at")
    updated = _parse_timestamp(summary.get("updated_at"), "batch updated_at")
    _require(started <= updated, "batch updated_at predates started_at")
    expected_values = {
        "total_cases": expected_count,
        "completed_cases": expected_count,
        "success_cases": expected_count,
        "skipped_cases": 0,
        "failed_cases": 0,
        "not_run_case_count": 0,
        "not_run_case_ids": [],
        "provider": "codex",
        "model": expected_model,
        "reasoning_effort": expected_reasoning,
        "codex_sandbox": "read-only",
        "token_budgets": list(TOKEN_BUDGETS),
        "sort_by": "size",
        "quality_check": "none",
        "large_case_threshold_bytes": LARGE_THRESHOLD_BYTES,
    }
    for key, expected in expected_values.items():
        _require(summary.get(key) == expected, f"batch summary {key} mismatch")
    _path_ends_with(
        summary.get("prompt_supplement"),
        ("neurips_ed_track_minimal", "prompts", SUPPLEMENT_PATH.name),
        "batch prompt_supplement",
    )
    _require(len(rows) == expected_count, "batch-result row count differs from expected count")
    warning_count = sum(
        len(row.get("quality_warnings", []))
        for row in rows
        if isinstance(row.get("quality_warnings"), list)
    )
    _require(summary.get("warning_count") == warning_count, "batch warning count mismatch")
    lane_counts = Counter(str(row.get("lane")) for row in rows)
    lane_stats = _mapping(summary.get("lane_stats"), "batch lane_stats")
    for lane in ("regular", "oversized"):
        stats = _mapping(lane_stats.get(lane), f"batch {lane} lane stats")
        _require(stats.get("count") == lane_counts[lane], f"batch {lane} lane count mismatch")
    return {
        "status": "passed",
        "started_at": summary.get("started_at"),
        "updated_at": summary.get("updated_at"),
        "total_cases": expected_count,
        "success_cases": expected_count,
        "warning_count": warning_count,
        "lane_counts": dict(sorted(lane_counts.items())),
    }


def _write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit AppWorld drafts fetched from the sealed direct-stdin draft VPS."
    )
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--cases-jsonl", type=Path, required=True)
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=REPO_ROOT / "neurips_ed_track_minimal",
        help="Generation-time neurips_ed_track_minimal runtime snapshot.",
    )
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--expected-model", required=True)
    parser.add_argument("--expected-reasoning", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    packet_root = args.packet_root.expanduser().resolve()
    draft_root = args.draft_root.expanduser().resolve()
    cases_jsonl = args.cases_jsonl.expanduser().resolve()
    runtime_root = args.runtime_root.expanduser().resolve()
    report_path = args.report_json.expanduser().resolve()
    global_errors: list[dict[str, str]] = []
    case_reports: list[dict[str, Any]] = []

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "status": "failed",
        "inputs": {
            "packet_root": str(packet_root),
            "draft_root": str(draft_root),
            "cases_jsonl": str(cases_jsonl),
            "runtime_root": str(runtime_root),
            "expected_count": args.expected_count,
            "expected_model": args.expected_model,
            "expected_reasoning": args.expected_reasoning,
        },
        "draft_root": {"status": "failed"},
        "case_set": {},
        "batch": {"status": "failed"},
        "summary": {},
        "global_errors": global_errors,
        "cases": case_reports,
    }

    expected_ids: list[str] = []
    inventory: dict[str, Mapping[str, Any]] = {}
    runtime: DraftRuntimeFiles | None = None
    try:
        _require(args.expected_count > 0, "--expected-count must be positive")
        _directory(packet_root, "packet root")
        _directory(draft_root, "draft root")
        runtime = _draft_runtime_files(_directory(runtime_root, "draft runtime root"))
        expected_ids, inventory = _case_rows(cases_jsonl, args.expected_count)
        report["inputs"]["cases_jsonl_sha256"] = _sha256_file(cases_jsonl)
        report["inputs"]["runtime_file_sha256"] = {
            "prompt": _sha256_file(runtime.prompt),
            "supplement": _sha256_file(runtime.supplement),
            "template": _sha256_file(runtime.template),
            "schema": _sha256_file(runtime.schema),
        }
    except Exception as exc:
        global_errors.append(
            {"check": "inputs", "error_type": type(exc).__name__, "message": str(exc)}
        )

    result_rows: list[Mapping[str, Any]] = []
    batch_by_id: dict[str, Mapping[str, Any]] = {}
    if expected_ids and runtime is not None:
        expected_set = set(expected_ids)
        try:
            draft_root_audit = _audit_draft_root_inventory(draft_root, expected_ids)
            report["draft_root"] = {
                "status": "passed",
                **dict(draft_root_audit.details),
            }
        except Exception as exc:
            global_errors.append(
                {
                    "check": "draft_root_inventory",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
        try:
            summary_path = _regular_file(draft_root / "_batch_summary.json", "batch summary")
            results_path = _regular_file(draft_root / "_batch_results.jsonl", "batch results")
            summary = _mapping(_load_json(summary_path, "batch summary"), "batch summary")
            result_rows = _load_jsonl(results_path, "batch results")
            batch_ids = [
                _case_id(row, f"batch-result row {index}")
                for index, row in enumerate(result_rows, start=1)
            ]
            duplicates = sorted(
                case_id for case_id, count in Counter(batch_ids).items() if count > 1
            )
            _require(not duplicates, f"batch results contain duplicates: {duplicates[:10]}")
            batch_by_id = {
                case_id: row for case_id, row in zip(batch_ids, result_rows, strict=True)
            }
            batch_audit = _audit_batch_summary(
                summary=summary,
                rows=result_rows,
                expected_count=args.expected_count,
                expected_model=args.expected_model,
                expected_reasoning=args.expected_reasoning,
            )
            report["batch"] = {
                **batch_audit,
                "summary_sha256": _sha256_file(summary_path),
                "results_sha256": _sha256_file(results_path),
                "result_rows_semantic_sha256": _sha256_object(result_rows),
            }
        except Exception as exc:
            global_errors.append(
                {"check": "batch", "error_type": type(exc).__name__, "message": str(exc)}
            )

        draft_dirs = {
            path.name
            for path in draft_root.iterdir()
            if path.is_dir() and not path.is_symlink()
        }
        unsafe_draft_dirs = sorted(
            path.name for path in draft_root.iterdir() if path.is_dir() and path.is_symlink()
        )
        packet_ids = {
            path.parent.name
            for path in packet_root.glob("*/case_packet.md")
            if path.is_file() and not path.is_symlink() and not path.parent.is_symlink()
        }
        batch_set = set(batch_by_id)
        missing_packets = sorted(expected_set - packet_ids)
        missing_drafts = sorted(expected_set - draft_dirs)
        extra_drafts = sorted(draft_dirs - expected_set)
        missing_batch_rows = sorted(expected_set - batch_set)
        extra_batch_rows = sorted(batch_set - expected_set)
        case_set_ok = not (
            missing_packets
            or missing_drafts
            or extra_drafts
            or missing_batch_rows
            or extra_batch_rows
            or unsafe_draft_dirs
        )
        report["case_set"] = {
            "status": "passed" if case_set_ok else "failed",
            "expected_count": len(expected_ids),
            "expected_case_ids_sha256": _sha256_object(expected_ids),
            "packet_root_case_count": len(packet_ids),
            "packet_root_is_allowed_superset": True,
            "packet_root_extra_case_count": len(packet_ids - expected_set),
            "draft_case_directory_count": len(draft_dirs),
            "batch_result_row_count": len(batch_set),
            "missing_packet_case_ids": missing_packets,
            "missing_draft_case_ids": missing_drafts,
            "extra_draft_case_ids": extra_drafts,
            "missing_batch_case_ids": missing_batch_rows,
            "extra_batch_case_ids": extra_batch_rows,
            "unsafe_draft_directory_names": unsafe_draft_dirs,
        }
        if not case_set_ok:
            global_errors.append(
                {
                    "check": "exact_case_set",
                    "error_type": "AuditError",
                    "message": "packet availability, draft directories, or batch rows do not match the selected case set",
                }
            )

        for case_id in expected_ids:
            case_reports.append(
                _audit_case(
                    case_id=case_id,
                    inventory_row=inventory[case_id],
                    packet_root=packet_root,
                    draft_root=draft_root,
                    batch_row=batch_by_id.get(case_id),
                    expected_model=args.expected_model,
                    expected_reasoning=args.expected_reasoning,
                    runtime=runtime,
                )
            )

    passed_cases = sum(case.get("status") == "passed" for case in case_reports)
    failed_cases = len(case_reports) - passed_cases
    error_count = len(global_errors) + sum(len(case["errors"]) for case in case_reports)
    warning_count = sum(len(case["warnings"]) for case in case_reports)
    all_passed = (
        not global_errors
        and len(case_reports) == args.expected_count
        and failed_cases == 0
        and report.get("batch", {}).get("status") == "passed"
        and report.get("draft_root", {}).get("status") == "passed"
        and report.get("case_set", {}).get("status") == "passed"
    )
    report["status"] = "passed" if all_passed else "failed"
    report["summary"] = {
        "expected_case_count": args.expected_count,
        "audited_case_count": len(case_reports),
        "passed_case_count": passed_cases,
        "failed_case_count": failed_cases,
        "case_with_warning_count": sum(bool(case["warnings"]) for case in case_reports),
        "error_count": error_count,
        "warning_count": warning_count,
        "exit_code": 0 if all_passed else 1,
    }
    report["report_semantic_sha256"] = _sha256_object(
        {key: value for key, value in report.items() if key != "report_semantic_sha256"}
    )
    try:
        _write_report(report_path, report)
    except Exception as exc:
        print(f"could not write audit report {report_path}: {exc}", file=sys.stderr)
        return 1
    print(
        f"AppWorld remote draft audit: {report['status']} "
        f"({passed_cases}/{args.expected_count} cases passed, "
        f"{error_count} errors, {warning_count} warnings); report={report_path}"
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
