#!/usr/bin/env python3
"""Strictly validate and atomically lock a complete checklist batch.

The runner is fail closed: it validates the exact manifest/source order, every
packet and checklist, and a current accepted model-review receipt before it
publishes either the dedicated lock JSONL or its acceptance receipt.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator, FormatChecker


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PACKAGE_ROOT = ROOT_DIR.parent

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts.case_checklist_review import (  # noqa: E402
    validate_model_review_body,
)
from neurips_ed_track_minimal.scripts import update_case_locks as case_locks  # noqa: E402


DEFAULT_DRAFT_PROMPT = ROOT_DIR / "prompts" / "draft_case_checklist.prompt.md"
DEFAULT_SCORE_PROMPT = ROOT_DIR / "prompts" / "score_evidence_with_codex.prompt.md"
DEFAULT_REVIEW_PROMPT = ROOT_DIR / "prompts" / "review_agentdojo_full_checklist.prompt.md"
DEFAULT_CHECKLIST_SCHEMA = ROOT_DIR / "schemas" / "case_checklist.schema.json"
DEFAULT_SCORE_SCHEMA = ROOT_DIR / "schemas" / "evidence_score.schema.json"
DEFAULT_REVIEW_SCHEMA = ROOT_DIR / "schemas" / "case_checklist_review.schema.json"
REVIEW_SCHEMA_VERSION = "case_checklist_model_review/v1"
ACCEPTANCE_SCHEMA_VERSION = "agentdojo_case_checklist_lock_acceptance/v1"

_PACKET_METADATA_PATTERNS = {
    "domain": re.compile(r"^-\s*domain:\s*`([^`]+)`\s*$", re.MULTILINE),
    "case_unit_id": re.compile(r"^-\s*case_unit_id:\s*`([^`]+)`\s*$", re.MULTILINE),
    "task_id": re.compile(r"^-\s*task_id:\s*`([^`]+)`\s*$", re.MULTILINE),
}


class BatchCaseLockError(RuntimeError):
    """Raised when the full batch cannot be accepted without ambiguity."""


@dataclass(frozen=True)
class ManifestCase:
    domain: str
    case_unit_id: str
    task_id: str


@dataclass(frozen=True)
class PacketCase:
    metadata: ManifestCase
    case_packet_path: Path
    raw_case_manifest_path: Path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-bundle", type=Path, required=True)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument(
        "--lock-file",
        type=Path,
        required=True,
        help="Dedicated experiment lock JSONL; the legacy shared lock is rejected.",
    )
    parser.add_argument("--acceptance-output", type=Path, required=True)
    parser.add_argument(
        "--writer-lock",
        type=Path,
        default=None,
        help="Stable advisory mutex path (default: beside --lock-file).",
    )
    parser.add_argument("--expected-count", type=int, default=949)
    parser.add_argument("--domain", default="agentdojo")
    parser.add_argument("--draft-prompt", type=Path, default=DEFAULT_DRAFT_PROMPT)
    parser.add_argument("--score-prompt", type=Path, default=DEFAULT_SCORE_PROMPT)
    parser.add_argument("--review-prompt", type=Path, default=DEFAULT_REVIEW_PROMPT)
    parser.add_argument("--checklist-schema", type=Path, default=DEFAULT_CHECKLIST_SCHEMA)
    parser.add_argument("--score-schema", type=Path, default=DEFAULT_SCORE_SCHEMA)
    parser.add_argument("--review-schema", type=Path, default=DEFAULT_REVIEW_SCHEMA)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BatchCaseLockError(f"Failed to hash {path}: {exc}") from exc
    return digest.hexdigest()


def _canonical_json_bytes(value: Any, *, newline: bool = False) -> bytes:
    suffix = "\n" if newline else ""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + suffix
    ).encode("utf-8")


def _sha256_object(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _require_file(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise BatchCaseLockError(f"{label} must not be a symlink: {path}")
    resolved = path.resolve()
    if not resolved.is_file():
        raise BatchCaseLockError(f"{label} is missing or not a regular file: {path}")
    return resolved


def _require_directory(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise BatchCaseLockError(f"{label} must not be a symlink: {path}")
    resolved = path.resolve()
    if not resolved.is_dir():
        raise BatchCaseLockError(f"{label} is missing or not a directory: {path}")
    return resolved


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BatchCaseLockError(f"Failed to read {label} {path}: {exc}") from exc


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_read_text(path, label))
    except json.JSONDecodeError as exc:
        raise BatchCaseLockError(f"Failed to parse {label} JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BatchCaseLockError(f"{label} must be a JSON object: {path}")
    return value


def _load_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(_read_text(path, label))
    except yaml.YAMLError as exc:
        raise BatchCaseLockError(f"Failed to parse {label} YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BatchCaseLockError(f"{label} must parse to a mapping: {path}")
    return value


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PACKAGE_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _resolve_declared_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise BatchCaseLockError(f"{field} must be a non-empty path string")
    path = Path(value)
    return (path if path.is_absolute() else PACKAGE_ROOT / path).resolve()


def _required_string(mapping: Mapping[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BatchCaseLockError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _load_manifest_cases(
    manifest_path: Path,
    *,
    domain: str,
    expected_count: int,
) -> tuple[dict[str, Any], list[ManifestCase]]:
    manifest = _load_yaml_mapping(manifest_path, "experiment manifest")
    blocks = manifest.get("domains")
    if not isinstance(blocks, list):
        raise BatchCaseLockError("experiment manifest requires a domains list")
    matching = [block for block in blocks if isinstance(block, dict) and block.get("domain") == domain]
    if len(matching) != 1:
        raise BatchCaseLockError(
            f"experiment manifest must contain exactly one {domain!r} domain block; found {len(matching)}"
        )
    block = matching[0]
    raw_cases = block.get("case_units")
    if not isinstance(raw_cases, list):
        raise BatchCaseLockError(f"manifest domain {domain} requires a case_units list")
    if block.get("case_unit_count") != len(raw_cases):
        raise BatchCaseLockError(
            f"manifest case_unit_count mismatch: declared={block.get('case_unit_count')!r}, "
            f"actual={len(raw_cases)}"
        )
    if block.get("case_unit_target") != expected_count:
        raise BatchCaseLockError(
            f"manifest case_unit_target mismatch: expected={expected_count}, "
            f"actual={block.get('case_unit_target')!r}"
        )
    cases: list[ManifestCase] = []
    for index, item in enumerate(raw_cases):
        if not isinstance(item, dict):
            raise BatchCaseLockError(f"manifest case_units[{index}] must be a mapping")
        cases.append(
            ManifestCase(
                domain=domain,
                case_unit_id=_required_string(item, "case_unit_id", f"manifest case_units[{index}]"),
                task_id=_required_string(item, "task_id", f"manifest case_units[{index}]"),
            )
        )
    if len(cases) != expected_count:
        raise BatchCaseLockError(
            f"manifest case count mismatch: expected={expected_count}, actual={len(cases)}"
        )
    ids = [case.case_unit_id for case in cases]
    if len(set(ids)) != len(ids):
        raise BatchCaseLockError("manifest contains duplicate case_unit_id values")
    return manifest, cases


def _extract_packet_metadata(text: str, path: Path) -> ManifestCase:
    values: dict[str, str] = {}
    for field, pattern in _PACKET_METADATA_PATTERNS.items():
        matches = [match.strip() for match in pattern.findall(text)]
        if len(matches) != 1:
            raise BatchCaseLockError(
                f"case packet must contain exactly one {field} metadata value: {path}"
            )
        values[field] = matches[0]
    return ManifestCase(**values)


def _discover_packets(root: Path, expected_count: int) -> dict[str, PacketCase]:
    direct_entries = sorted(root.iterdir())
    if any(not path.is_dir() or path.is_symlink() for path in direct_entries):
        raise BatchCaseLockError(
            "case packet root must contain only non-symlink case directories"
        )
    if len(direct_entries) != expected_count:
        raise BatchCaseLockError(
            f"case packet directory count mismatch: expected={expected_count}, "
            f"actual={len(direct_entries)}"
        )
    packet_paths = sorted(root.glob("*/case_packet.md"))
    if len(packet_paths) != expected_count:
        raise BatchCaseLockError(
            f"case packet count mismatch: expected={expected_count}, actual={len(packet_paths)}"
        )
    packets: dict[str, PacketCase] = {}
    for packet_path in packet_paths:
        packet_path = _require_file(packet_path, "case packet")
        metadata = _extract_packet_metadata(_read_text(packet_path, "case packet"), packet_path)
        if metadata.case_unit_id in packets:
            raise BatchCaseLockError(f"duplicate case packet case_unit_id: {metadata.case_unit_id}")
        raw_manifest = _require_file(packet_path.parent / "raw_case_manifest.json", "raw case manifest")
        packets[metadata.case_unit_id] = PacketCase(metadata, packet_path, raw_manifest)
    return packets


def _validate_source_bundle(
    bundle_path: Path,
    *,
    manifest_path: Path,
    manifest: Mapping[str, Any],
    cases: Sequence[ManifestCase],
    packets: Mapping[str, PacketCase],
) -> dict[str, Any]:
    bundle = _load_json(bundle_path, "source bundle")
    if bundle.get("schema_version") != "contract_source_bundle.v2":
        raise BatchCaseLockError(
            f"source bundle schema_version mismatch: {bundle.get('schema_version')!r}"
        )
    if manifest.get("source_bundle_hash") != _sha256_file(bundle_path):
        raise BatchCaseLockError("manifest source_bundle_hash does not match the supplied source bundle")
    declared_manifest = _resolve_declared_path(bundle.get("manifest_path"), "source_bundle.manifest_path")
    if declared_manifest != manifest_path:
        raise BatchCaseLockError("source bundle manifest_path does not resolve to the supplied manifest")
    definition = dict(manifest)
    definition.pop("source_bundle_hash", None)
    if bundle.get("manifest_definition_sha256") != _sha256_object(definition):
        raise BatchCaseLockError("source bundle manifest_definition_sha256 is stale")
    if bundle.get("manifest_definition_sha256_scope") != "canonical_mapping_without_source_bundle_hash":
        raise BatchCaseLockError("source bundle manifest_definition_sha256_scope is invalid")
    if bundle.get("manifest_definition_excluded_fields") != ["source_bundle_hash"]:
        raise BatchCaseLockError("source bundle manifest_definition_excluded_fields is invalid")

    sources = bundle.get("sources")
    if not isinstance(sources, list):
        raise BatchCaseLockError("source bundle requires a sources list")
    if bundle.get("source_count") != len(sources) or len(sources) != len(cases):
        raise BatchCaseLockError(
            f"source bundle count mismatch: expected={len(cases)}, "
            f"declared={bundle.get('source_count')!r}, actual={len(sources)}"
        )
    expected_tuples = [(case.domain, case.case_unit_id, case.task_id) for case in cases]
    actual_tuples: list[tuple[str, str, str]] = []
    contract_ids: list[str] = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise BatchCaseLockError(f"source bundle sources[{index}] must be a mapping")
        actual_tuples.append(
            (
                _required_string(source, "domain", f"source bundle sources[{index}]"),
                _required_string(source, "case_unit_id", f"source bundle sources[{index}]"),
                _required_string(source, "task_id", f"source bundle sources[{index}]"),
            )
        )
        contract_ids.append(
            _required_string(source, "contract_id", f"source bundle sources[{index}]")
        )
    if len(set(contract_ids)) != len(contract_ids):
        raise BatchCaseLockError("source bundle contains duplicate contract_id values")
    if actual_tuples != expected_tuples:
        if set(actual_tuples) == set(expected_tuples):
            raise BatchCaseLockError("source bundle case order does not exactly match manifest order")
        raise BatchCaseLockError("source bundle case/domain/task set does not exactly match manifest")

    for index, (case, source) in enumerate(zip(cases, sources, strict=True)):
        packet = packets[case.case_unit_id]
        draft_input = source.get("draft_input")
        if not isinstance(draft_input, dict):
            raise BatchCaseLockError(f"source bundle sources[{index}].draft_input must be a mapping")
        bindings = (
            ("case_packet_path", "case_packet_sha256", packet.case_packet_path),
            ("raw_case_manifest_path", "raw_case_manifest_sha256", packet.raw_case_manifest_path),
        )
        for path_field, hash_field, expected_path in bindings:
            declared_path = _resolve_declared_path(
                draft_input.get(path_field), f"source bundle sources[{index}].draft_input.{path_field}"
            )
            if declared_path != expected_path:
                raise BatchCaseLockError(
                    f"source bundle {path_field} does not resolve to canonical packet file for "
                    f"{case.case_unit_id}"
                )
            if draft_input.get(hash_field) != _sha256_file(expected_path):
                raise BatchCaseLockError(f"source bundle {hash_field} is stale for {case.case_unit_id}")
    return bundle


def _format_validation_errors(errors: Sequence[Any]) -> str:
    parts: list[str] = []
    for error in errors:
        pointer = ".".join(str(item) for item in error.absolute_path) or "<root>"
        parts.append(f"{pointer}: {error.message}")
    return "; ".join(parts)


def _validate_checklist(
    checklist_path: Path,
    *,
    packet: PacketCase,
    checklist_validator: Draft202012Validator,
) -> dict[str, Any]:
    checklist = _load_yaml_mapping(checklist_path, "checklist")
    errors = sorted(
        checklist_validator.iter_errors(checklist),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        raise BatchCaseLockError(
            f"checklist schema validation failed for {packet.metadata.case_unit_id}: "
            f"{_format_validation_errors(errors)}"
        )
    for field in ("domain", "case_unit_id", "task_id"):
        if checklist.get(field) != getattr(packet.metadata, field):
            raise BatchCaseLockError(
                f"checklist {field} mismatch for {packet.metadata.case_unit_id}: "
                f"expected={getattr(packet.metadata, field)!r}, actual={checklist.get(field)!r}"
            )
    try:
        validate_checklist_guardrails(
            checklist,
            allowed_source_paths=case_packet_support_paths(
                _read_text(packet.case_packet_path, "case packet")
            ),
        )
    except ChecklistGuardrailError as exc:
        raise BatchCaseLockError(
            f"checklist guardrails failed for {packet.metadata.case_unit_id}: {exc}"
        ) from exc
    return checklist


def _require_current_receipt_binding(
    receipt: Mapping[str, Any],
    *,
    path_field: str,
    hash_field: str,
    expected_path: Path,
    case_unit_id: str,
) -> None:
    declared_path = _resolve_declared_path(receipt.get(path_field), f"review.{path_field}")
    if declared_path != expected_path:
        raise BatchCaseLockError(f"review {path_field} is not canonical/current for {case_unit_id}")
    if receipt.get(hash_field) != _sha256_file(expected_path):
        raise BatchCaseLockError(f"review {hash_field} is stale for {case_unit_id}")


def _validate_review(
    review_path: Path,
    *,
    case_unit_id: str,
    packet_path: Path,
    checklist_path: Path,
    draft_prompt_path: Path,
    checklist_schema_path: Path,
    review_prompt_path: Path,
    review_schema_path: Path,
    review_validator: Draft202012Validator,
) -> dict[str, Any]:
    receipt = _load_json(review_path, "model review receipt")
    errors = sorted(
        review_validator.iter_errors(receipt),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        raise BatchCaseLockError(
            f"model review schema validation failed for {case_unit_id}: "
            f"{_format_validation_errors(errors)}"
        )
    if receipt.get("schema_version") != REVIEW_SCHEMA_VERSION:
        raise BatchCaseLockError(f"review schema_version mismatch for {case_unit_id}")
    if receipt.get("case_unit_id") != case_unit_id:
        raise BatchCaseLockError(f"review case_unit_id mismatch for {case_unit_id}")
    if receipt.get("decision") != "accept" or receipt.get("unresolved_findings") != []:
        raise BatchCaseLockError(f"review is not accepted with zero unresolved findings: {case_unit_id}")
    deterministic = receipt.get("deterministic_review")
    if (
        not isinstance(deterministic, dict)
        or deterministic.get("status") != "pass"
        or deterministic.get("findings") != []
    ):
        raise BatchCaseLockError(f"deterministic review did not pass cleanly: {case_unit_id}")
    model_review = receipt.get("model_review")
    if (
        not isinstance(model_review, dict)
        or model_review.get("decision") != "accept"
        or model_review.get("blocking_findings") != []
        or not isinstance(model_review.get("checklist_items"), list)
        or not model_review.get("checklist_items")
    ):
        raise BatchCaseLockError(f"model review did not accept all checklist items: {case_unit_id}")
    model_review_errors = validate_model_review_body(model_review)
    if model_review_errors:
        raise BatchCaseLockError(
            f"model review body is internally inconsistent for {case_unit_id}: "
            + "; ".join(model_review_errors)
        )
    if not isinstance(receipt.get("reviewer_config"), dict) or not receipt.get("reviewer_config"):
        raise BatchCaseLockError(f"review reviewer_config must be a non-empty mapping: {case_unit_id}")
    if not isinstance(receipt.get("reviewed_at"), str) or not receipt["reviewed_at"].strip():
        raise BatchCaseLockError(f"review reviewed_at must be non-empty: {case_unit_id}")

    for path_field, hash_field, expected_path in (
        ("case_packet_path", "case_packet_sha256", packet_path),
        ("checklist_path", "checklist_sha256", checklist_path),
        ("draft_prompt_path", "draft_prompt_sha256", draft_prompt_path),
        ("checklist_schema_path", "checklist_schema_sha256", checklist_schema_path),
        ("review_prompt_path", "review_prompt_sha256", review_prompt_path),
        ("review_schema_path", "review_schema_sha256", review_schema_path),
    ):
        _require_current_receipt_binding(
            receipt,
            path_field=path_field,
            hash_field=hash_field,
            expected_path=expected_path,
            case_unit_id=case_unit_id,
        )
    return receipt


def _stage_bytes(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            return Path(handle.name)
    except OSError as exc:
        raise BatchCaseLockError(f"Failed to stage output for {path}: {exc}") from exc


def _restore_path(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
        return
    staged = _stage_bytes(path, previous)
    try:
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


@contextmanager
def _advisory_writer_lock(path: Path, payload: bytes) -> Iterator[None]:
    """Acquire a non-blocking stable mutex for one lock/acceptance pair."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise BatchCaseLockError(f"writer lock must not be a symlink: {path}")
    flags = os.O_RDWR | os.O_CREAT
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        file_descriptor = os.open(path, flags, 0o644)
    except OSError as exc:
        raise BatchCaseLockError(f"Failed to open advisory writer lock {path}: {exc}") from exc
    acquired = False
    try:
        try:
            fcntl.flock(file_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError as exc:
            raise BatchCaseLockError(
                f"Another batch runner holds advisory writer lock: {path}"
            ) from exc
        try:
            os.lseek(file_descriptor, 0, os.SEEK_SET)
            os.ftruncate(file_descriptor, 0)
            remaining = memoryview(payload)
            while remaining:
                written = os.write(file_descriptor, remaining)
                if written <= 0:
                    raise OSError("zero-byte write while recording writer-lock provenance")
                remaining = remaining[written:]
            os.fsync(file_descriptor)
        except OSError as exc:
            raise BatchCaseLockError(
                f"Failed to write advisory writer-lock provenance {path}: {exc}"
            ) from exc
        yield
    finally:
        if acquired:
            try:
                fcntl.flock(file_descriptor, fcntl.LOCK_UN)
            except OSError:
                pass
        try:
            os.close(file_descriptor)
        except OSError:
            pass


def _atomic_publish_pair(
    lock_path: Path,
    lock_bytes: bytes,
    acceptance_path: Path,
    acceptance_bytes: bytes,
) -> None:
    try:
        previous_lock = lock_path.read_bytes() if lock_path.exists() else None
        previous_acceptance = acceptance_path.read_bytes() if acceptance_path.exists() else None
    except OSError as exc:
        raise BatchCaseLockError(f"Failed to snapshot existing batch lock outputs: {exc}") from exc
    staged_lock: Path | None = None
    staged_acceptance: Path | None = None
    try:
        staged_lock = _stage_bytes(lock_path, lock_bytes)
        staged_acceptance = _stage_bytes(acceptance_path, acceptance_bytes)
        os.replace(staged_lock, lock_path)
        try:
            os.replace(staged_acceptance, acceptance_path)
        except BaseException:
            _restore_path(lock_path, previous_lock)
            raise
        try:
            readback_matches = (
                lock_path.read_bytes() == lock_bytes
                and acceptance_path.read_bytes() == acceptance_bytes
            )
        except OSError:
            readback_matches = False
        if not readback_matches:
            _restore_path(lock_path, previous_lock)
            _restore_path(acceptance_path, previous_acceptance)
            raise BatchCaseLockError("post-publication readback verification failed")
    except OSError as exc:
        raise BatchCaseLockError(f"Failed to atomically publish batch lock outputs: {exc}") from exc
    finally:
        if staged_lock is not None:
            staged_lock.unlink(missing_ok=True)
        if staged_acceptance is not None:
            staged_acceptance.unlink(missing_ok=True)


def build_and_publish_batch(args: argparse.Namespace) -> dict[str, Any]:
    if args.expected_count <= 0:
        raise BatchCaseLockError("expected-count must be positive")

    manifest_path = _require_file(args.manifest, "experiment manifest")
    source_bundle_path = _require_file(args.source_bundle, "source bundle")
    packet_root = _require_directory(args.case_packet_root, "case packet root")
    draft_root = _require_directory(args.draft_root, "draft root")
    draft_prompt_path = _require_file(args.draft_prompt, "draft prompt")
    score_prompt_path = _require_file(args.score_prompt, "score prompt")
    review_prompt_path = _require_file(args.review_prompt, "review prompt")
    checklist_schema_path = _require_file(args.checklist_schema, "checklist schema")
    score_schema_path = _require_file(args.score_schema, "score schema")
    review_schema_path = _require_file(args.review_schema, "review schema")

    lock_path = args.lock_file.resolve()
    acceptance_path = args.acceptance_output.resolve()
    writer_lock_path = (
        args.writer_lock.resolve()
        if args.writer_lock is not None
        else lock_path.with_name(f"{lock_path.name}.writer.lock")
    )
    if lock_path == case_locks.DEFAULT_LOCK_FILE.resolve():
        raise BatchCaseLockError(
            "batch lock requires a dedicated experiment lock file; the legacy shared cases.jsonl is rejected"
        )
    if lock_path == acceptance_path:
        raise BatchCaseLockError("lock-file and acceptance-output must be distinct paths")
    if writer_lock_path in {lock_path, acceptance_path}:
        raise BatchCaseLockError("writer-lock must be distinct from both published outputs")

    manifest, cases = _load_manifest_cases(
        manifest_path,
        domain=args.domain,
        expected_count=args.expected_count,
    )
    packets = _discover_packets(packet_root, args.expected_count)
    expected_ids = [case.case_unit_id for case in cases]
    if set(packets) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(packets))
        extra = sorted(set(packets) - set(expected_ids))
        raise BatchCaseLockError(
            f"case packet ID set mismatch: missing={missing[:10]}, extra={extra[:10]}"
        )
    for case in cases:
        if packets[case.case_unit_id].metadata != case:
            raise BatchCaseLockError(
                f"case packet metadata does not match manifest for {case.case_unit_id}"
            )

    source_bundle = _validate_source_bundle(
        source_bundle_path,
        manifest_path=manifest_path,
        manifest=manifest,
        cases=cases,
        packets=packets,
    )

    checklist_schema = _load_json(checklist_schema_path, "checklist schema")
    review_schema = _load_json(review_schema_path, "review schema")
    try:
        Draft202012Validator.check_schema(checklist_schema)
        Draft202012Validator.check_schema(review_schema)
    except Exception as exc:
        raise BatchCaseLockError(f"Supplied JSON schema is invalid: {exc}") from exc
    checklist_validator = Draft202012Validator(checklist_schema)
    review_validator = Draft202012Validator(review_schema, format_checker=FormatChecker())

    checklist_paths = sorted(draft_root.glob("*/checklist.yaml"))
    review_paths = sorted(draft_root.glob("*/review.json"))
    if len(checklist_paths) != args.expected_count:
        raise BatchCaseLockError(
            f"checklist count mismatch: expected={args.expected_count}, actual={len(checklist_paths)}"
        )
    if len(review_paths) != args.expected_count:
        raise BatchCaseLockError(
            f"review receipt count mismatch: expected={args.expected_count}, actual={len(review_paths)}"
        )

    lock_entries: list[dict[str, str]] = []
    accepted_cases: list[dict[str, str]] = []
    observed_checklist_paths: set[Path] = set()
    observed_review_paths: set[Path] = set()
    canonical_reviewer_config: dict[str, Any] | None = None
    for case in cases:
        packet = packets[case.case_unit_id]
        case_dir_name = packet.case_packet_path.parent.name
        case_draft_dir = draft_root / case_dir_name
        if case_draft_dir.is_symlink():
            raise BatchCaseLockError(
                f"draft case directory must not be a symlink: {case.case_unit_id}"
            )
        checklist_path = _require_file(
            case_draft_dir / "checklist.yaml", f"checklist for {case.case_unit_id}"
        )
        review_path = _require_file(
            case_draft_dir / "review.json", f"review receipt for {case.case_unit_id}"
        )
        observed_checklist_paths.add(checklist_path)
        observed_review_paths.add(review_path)
        _validate_checklist(
            checklist_path,
            packet=packet,
            checklist_validator=checklist_validator,
        )
        review_receipt = _validate_review(
            review_path,
            case_unit_id=case.case_unit_id,
            packet_path=packet.case_packet_path,
            checklist_path=checklist_path,
            draft_prompt_path=draft_prompt_path,
            checklist_schema_path=checklist_schema_path,
            review_prompt_path=review_prompt_path,
            review_schema_path=review_schema_path,
            review_validator=review_validator,
        )
        reviewer_config = dict(review_receipt["reviewer_config"])
        if canonical_reviewer_config is None:
            canonical_reviewer_config = dict(reviewer_config)
        elif reviewer_config != canonical_reviewer_config:
            raise BatchCaseLockError(
                f"reviewer_config differs across accepted receipts: {case.case_unit_id}"
            )
        try:
            entry = case_locks.build_lock_entry(
                case_packet_path=packet.case_packet_path,
                checklist_path=checklist_path,
                draft_prompt_path=draft_prompt_path,
                score_prompt_path=score_prompt_path,
                checklist_schema_path=checklist_schema_path,
                score_schema_path=score_schema_path,
            )
        except case_locks.CaseLockError as exc:
            raise BatchCaseLockError(str(exc)) from exc
        lock_entries.append(entry)
        accepted_cases.append(
            {
                "case_unit_id": case.case_unit_id,
                "case_packet_sha256": _sha256_file(packet.case_packet_path),
                "raw_case_manifest_sha256": _sha256_file(packet.raw_case_manifest_path),
                "checklist_sha256": _sha256_file(checklist_path),
                "review_sha256": _sha256_file(review_path),
            }
        )

    if observed_checklist_paths != {path.resolve() for path in checklist_paths}:
        raise BatchCaseLockError("checklist file set contains non-canonical or duplicate case directories")
    if observed_review_paths != {path.resolve() for path in review_paths}:
        raise BatchCaseLockError("review receipt set contains non-canonical or duplicate case directories")
    if canonical_reviewer_config is None:
        raise BatchCaseLockError("accepted batch has no reviewer_config")

    lock_bytes = b"".join(_canonical_json_bytes(entry, newline=True) for entry in lock_entries)
    writer_lock_definition = {
        "schema_version": "case_checklist_batch_writer_lock/v1",
        "lock_file_path": _display_path(lock_path),
        "acceptance_output_path": _display_path(acceptance_path),
    }
    writer_lock_bytes = _canonical_json_bytes(writer_lock_definition, newline=True)
    acceptance: dict[str, Any] = {
        "schema_version": ACCEPTANCE_SCHEMA_VERSION,
        "status": "accepted",
        "domain": args.domain,
        "expected_count": args.expected_count,
        "counts": {
            "manifest_cases": len(cases),
            "source_entries": len(source_bundle["sources"]),
            "case_packets": len(packets),
            "valid_drafts": len(lock_entries),
            "reviewed": len(lock_entries),
            "locked": len(lock_entries),
            "unresolved_drafts": 0,
        },
        "manifest_path": _display_path(manifest_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "source_bundle_path": _display_path(source_bundle_path),
        "source_bundle_sha256": _sha256_file(source_bundle_path),
        "case_packet_root": _display_path(packet_root),
        "draft_root": _display_path(draft_root),
        "lock_file_path": _display_path(lock_path),
        "lock_file_sha256": _sha256_bytes(lock_bytes),
        "writer_lock_path": _display_path(writer_lock_path),
        "writer_lock_sha256": _sha256_bytes(writer_lock_bytes),
        "case_id_order_sha256": _sha256_object(expected_ids),
        "case_id_set_sha256": _sha256_object(sorted(expected_ids)),
        "accepted_cases_sha256": _sha256_object(accepted_cases),
        "accepted_cases": accepted_cases,
        "reviewer_config": canonical_reviewer_config,
        "reviewer_config_sha256": _sha256_object(canonical_reviewer_config),
        "inputs": {
            "draft_prompt_path": _display_path(draft_prompt_path),
            "draft_prompt_sha256": _sha256_file(draft_prompt_path),
            "score_prompt_path": _display_path(score_prompt_path),
            "score_prompt_sha256": _sha256_file(score_prompt_path),
            "review_prompt_path": _display_path(review_prompt_path),
            "review_prompt_sha256": _sha256_file(review_prompt_path),
            "checklist_schema_path": _display_path(checklist_schema_path),
            "checklist_schema_sha256": _sha256_file(checklist_schema_path),
            "score_schema_path": _display_path(score_schema_path),
            "score_schema_sha256": _sha256_file(score_schema_path),
            "review_schema_path": _display_path(review_schema_path),
            "review_schema_sha256": _sha256_file(review_schema_path),
        },
        "unresolved_drafts": [],
    }
    acceptance_bytes = _canonical_json_bytes(acceptance, newline=True)
    with _advisory_writer_lock(writer_lock_path, writer_lock_bytes):
        _atomic_publish_pair(lock_path, lock_bytes, acceptance_path, acceptance_bytes)
    return acceptance


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        acceptance = build_and_publish_batch(args)
    except BatchCaseLockError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(acceptance, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"accepted and locked {acceptance['counts']['locked']} cases: "
            f"{acceptance['lock_file_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
