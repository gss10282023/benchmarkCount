"""Immutable post-review freeze for the 949-case AgentDojo checklist branch.

This module deliberately sits *after* the live draft/review lifecycle.  It does
not mutate drafts, reviews, lifecycle receipts, or the batch lock produced by
``update_case_locks_batch.py``.  Instead it independently revalidates the
existing lifecycle, materializes a complete per-case digest graph, and publishes
one destination-absent JSON file with atomic no-replace semantics.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import tempfile
import threading
from typing import Any
import uuid

from jsonschema import Draft202012Validator, FormatChecker

from evidence_system.contracts import agentdojo_full_experiment as freeze_v1
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import (
    sha256_bytes,
    sha256_file,
    sha256_object,
    sha256_path,
)
from evidence_system.core.paths import repo_root


CHECKLIST_FREEZE_V2_SCHEMA_VERSION = "agentdojo_full_checklist_freeze/v2"
CHECKLIST_FREEZE_V2_DEFINITION_SCHEMA_VERSION = (
    "agentdojo_full_checklist_freeze_definition/v2"
)
CHECKLIST_FREEZE_V2_INVALIDATION_SCHEMA_VERSION = (
    "agentdojo_full_checklist_freeze_invalidation/v1"
)
CHECKLIST_REVIEW_PREFLIGHT_SCHEMA_VERSION = (
    "agentdojo_full_checklist_review_currentness_preflight/v1"
)
CHECKLIST_REVIEW_PREFLIGHT_RECEIPT_SCHEMA_VERSION = (
    "agentdojo_full_checklist_review_currentness_preflight_receipt/v1"
)
CHECKLIST_REVIEW_QUIESCENCE_SCHEMA_VERSION = (
    "agentdojo_full_checklist_review_quiescence/v1"
)
CHECKLIST_REVIEW_POST_LOCK_QUIESCENCE_SCHEMA_VERSION = (
    "agentdojo_full_checklist_review_quiescence/v2"
)
CHECKLIST_REVIEW_POST_LOCK_GATE_MODE = "post_lock_checklist_freeze_snapshot"
CHECKLIST_FREEZE_V2_ID = "agentdojo_full_v1.2.2_direct/checklist_freeze/v2"

DEFAULT_CHECKLIST_FREEZE_V2 = (
    freeze_v1.EXPERIMENT_ROOT / "checklist_freeze/v2/checklist_freeze.json"
)
DEFAULT_REVIEW_QUIESCENCE_RECEIPT = (
    freeze_v1.EXPERIMENT_ROOT / "checklist_freeze/v2/review_quiescence.json"
)
DEFAULT_REVIEW_PREFLIGHT_RECEIPT = (
    freeze_v1.EXPERIMENT_ROOT / "checklist_freeze/v2/review_preflight.json"
)

DEFAULT_QUIESCENCE_MAX_AGE_SECONDS = 300

_REVIEW_PROCESS_POLICY = (
    "run_agentdojo_full_draft_review.py",
    "review_case_checklist_with_codex.py",
    "codex_exec_case_checklist_review",
)
_REVIEW_COMMAND_PATTERN_DEFINITION = {
    "run_agentdojo_full_draft_review.py": "python process containing exact script basename",
    "review_case_checklist_with_codex.py": "python process containing exact script basename",
    "codex_exec_case_checklist_review": (
        "codex exec process containing a checklist-review output/schema marker"
    ),
    "diagnostic_processes_excluded": ["rg", "grep", "ps"],
    "scanner_and_ancestor_processes_excluded": True,
}
_REVIEW_COMMAND_PATTERN_SHA256 = sha256_object(_REVIEW_COMMAND_PATTERN_DEFINITION)
_LIFECYCLE_CODE_CONTEXT_GUARD = threading.Lock()
_DRAFT_RETRY_CODEX_CONTEXT_GUARD = threading.Lock()
_CANONICAL_REVIEW_RUN_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{12}Z$")

_REVIEW_ATTEMPT_COMMON_FIELDS = frozenset(
    {
        "round",
        "started_at",
        "finished_at",
        "returncode",
        "input_checklist_path",
        "input_checklist_sha256",
        "review_prompt_path",
        "review_prompt_sha256",
        "deterministic_review",
    }
)
_REVIEW_ATTEMPT_MODEL_FIELDS = frozenset(
    {"decision", "model_review_path", "model_review_sha256"}
)
_DETERMINISTIC_REJECT_ERROR = (
    "model accepted despite deterministic blocking findings"
)
_REVIEW_ATTEMPT_OUTCOMES = frozenset(
    {
        "failed_call",
        "deterministically_rejected_accept",
        "successful_revise",
        "successful_accept",
    }
)
_GENERATION_ATTEMPT_COMMON_FIELDS = frozenset(
    {
        "attempt_index",
        "max_output_tokens",
        "http_timeout_seconds",
        "codex_timeout_seconds",
        "returncode",
        "duration_seconds",
        "stderr_tail",
    }
)

_V2_CODE_PATHS = (
    "src/evidence_system/contracts/agentdojo_checklist_freeze_v2.py",
    "src/evidence_system/cli/freeze_agentdojo_full_checklists_v2.py",
)

_EXPECTED_COUNTS = {
    "case_packets": freeze_v1.EXPECTED_CASE_COUNT,
    "source_entries": freeze_v1.EXPECTED_CASE_COUNT,
    "valid_drafts": freeze_v1.EXPECTED_CASE_COUNT,
    "accepted_drafts": freeze_v1.EXPECTED_CASE_COUNT,
    "reviewed": freeze_v1.EXPECTED_CASE_COUNT,
    "locked": freeze_v1.EXPECTED_CASE_COUNT,
    "unresolved_drafts": 0,
}

_PROMPT_SCHEMA_PREFIXES = (
    "draft_prompt",
    "review_prompt",
    "score_prompt",
    "checklist_schema",
    "review_schema",
    "score_schema",
)


@dataclass(frozen=True)
class ChecklistFreezeV2Result:
    """A successfully published or verified immutable checklist freeze."""

    freeze_path: Path
    freeze_sha256: str
    definition: dict[str, Any]


class _PublishedOutputError(ContractLifecycleError):
    """Publication failed after the destination link became visible."""


def checklist_freeze_v2_invalidation_path(
    freeze_path: str | Path,
) -> Path:
    """Return the durable fail-closed marker paired with a v2 freeze."""

    output = _absolute_path(freeze_path)
    return output.with_name(f"{output.stem}.invalidated.json")


def _absolute_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root() / path
    return path.absolute()


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _reject_symlink_ancestors(path: Path, label: str) -> None:
    absolute = _absolute_path(path)
    for ancestor in (absolute, *absolute.parents):
        if _lexists(ancestor) and ancestor.is_symlink():
            raise ContractLifecycleError(
                f"{label} has a symlinked ancestor: {ancestor}"
            )


def _require_regular_file(value: str | Path, label: str) -> Path:
    path = _absolute_path(value)
    _reject_symlink_ancestors(path, label)
    resolved = path.resolve()
    try:
        metadata = os.lstat(resolved)
    except OSError as exc:
        raise ContractLifecycleError(f"{label} is missing: {path}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ContractLifecycleError(f"{label} is missing: {path}")
    if metadata.st_nlink != 1:
        raise ContractLifecycleError(
            f"{label} must have exactly one hard link: {path} nlink={metadata.st_nlink}"
        )
    return resolved


def _require_regular_directory(value: str | Path, label: str) -> Path:
    path = _absolute_path(value)
    _reject_symlink_ancestors(path, label)
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ContractLifecycleError(f"{label} is missing: {path}")
    return resolved


def _audit_tree_file_safety(root: Path, label: str) -> None:
    _reject_symlink_ancestors(root, label)
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ContractLifecycleError(f"{label} contains a symlink: {path}")
        if path.is_file():
            metadata = os.lstat(path)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ContractLifecycleError(
                    f"{label} contains a non-regular or multiply-linked input: {path}"
                )


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _resolve_declared_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ContractLifecycleError(f"{label} must be a non-empty path")
    return _require_regular_file(value.strip(), label)


def _load_json_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractLifecycleError(f"failed to read {label}: {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError(f"{label} must be a JSON object: {path}")
    return dict(payload)


def _load_lock_lines(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        lines = path.read_bytes().splitlines(keepends=True)
    except OSError as exc:
        raise ContractLifecycleError(f"failed to read case lock JSONL: {exc}") from exc
    entries: list[dict[str, Any]] = []
    line_hashes: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.endswith(b"\n") or not line.strip():
            raise ContractLifecycleError(
                f"case lock JSONL line {line_number} is blank or lacks a newline"
            )
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(
                f"case lock JSONL line {line_number} is invalid: {exc}"
            ) from exc
        if not isinstance(value, Mapping):
            raise ContractLifecycleError(
                f"case lock JSONL line {line_number} is not an object"
            )
        entries.append(dict(value))
        line_hashes.append(sha256_bytes(line))
    return entries, line_hashes


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ContractLifecycleError(
            f"{label} differs: expected={expected!r}, actual={actual!r}"
        )


def _aware_timestamp(value: str | None, label: str) -> str:
    timestamp = value or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ContractLifecycleError(f"{label} must be a timezone-aware timestamp")
    try:
        parsed = datetime.fromisoformat(timestamp.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractLifecycleError(f"{label} is not ISO-8601: {timestamp!r}") from exc
    if parsed.tzinfo is None:
        raise ContractLifecycleError(f"{label} must include a timezone")
    return timestamp.strip()


def _normalized_snapshot_overrides(overrides: Mapping[str, Any]) -> dict[str, Any]:
    normalized = freeze_v1._production_snapshot_overrides(overrides)
    supplied_suites = normalized.get(
        "expected_suite_counts", freeze_v1.EXPECTED_SUITE_COUNTS
    )
    if (
        not isinstance(supplied_suites, Mapping)
        or dict(supplied_suites) != freeze_v1.EXPECTED_SUITE_COUNTS
    ):
        raise ContractLifecycleError(
            "the v2 checklist freeze suite denominator cannot be overridden"
        )
    if normalized.get("require_empty_formal_outputs", True) is not True:
        raise ContractLifecycleError(
            "the v2 checklist freeze requires empty formal score outputs"
        )
    if normalized.get("frozen_formal_output_precondition") is not None:
        raise ContractLifecycleError(
            "the v2 checklist freeze cannot accept a caller-supplied output precondition"
        )
    normalized["expected_suite_counts"] = dict(freeze_v1.EXPECTED_SUITE_COUNTS)
    normalized["require_empty_formal_outputs"] = True
    normalized.pop("frozen_formal_output_precondition", None)
    return normalized


def _canonical_lifecycle_relative_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ContractLifecycleError(f"{label} must be a non-empty relative path")
    raw = value.strip()
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != raw:
        raise ContractLifecycleError(f"{label} is not a canonical relative path")
    return relative


def _build_lifecycle_code_snapshot_binding(
    *, snapshot_root: str | Path, resolved_config_path: str | Path
) -> dict[str, Any]:
    root = _require_regular_directory(snapshot_root, "lifecycle-code snapshot root")
    _audit_tree_file_safety(root, "lifecycle-code snapshot root")
    config_path = _require_regular_file(
        resolved_config_path, "lifecycle-code snapshot resolved config"
    )
    config = _load_json_mapping(config_path, "lifecycle-code snapshot resolved config")
    raw_locks = config.get("lifecycle_code")
    if not isinstance(raw_locks, list) or not raw_locks:
        raise ContractLifecycleError(
            "lifecycle-code snapshot config has no lifecycle_code locks"
        )

    files: list[dict[str, str]] = []
    snapshot_file_count = 0
    for position, raw_lock in enumerate(raw_locks):
        if not isinstance(raw_lock, Mapping):
            raise ContractLifecycleError(
                f"lifecycle-code lock {position} is not a mapping"
            )
        relative = _canonical_lifecycle_relative_path(
            raw_lock.get("path"), f"lifecycle-code lock {position}.path"
        )
        locked_sha256 = _require_sha256(
            raw_lock.get("sha256"), f"lifecycle-code lock {position}.sha256"
        )
        current = _require_regular_file(
            repo_root() / relative,
            f"current lifecycle-code file {relative.as_posix()}",
        )
        snapshot_candidate = root.joinpath(*relative.parts)
        if sha256_file(current) != locked_sha256:
            selected = _require_regular_file(
                snapshot_candidate,
                f"lifecycle-code snapshot file {relative.as_posix()}",
            )
            source = "snapshot"
            snapshot_file_count += 1
        else:
            selected = current
            source = "repository"
        _assert_equal(
            sha256_file(selected),
            locked_sha256,
            f"locked lifecycle-code hash {relative.as_posix()}",
        )
        files.append(
            {
                "declared_path": relative.as_posix(),
                "locked_sha256": locked_sha256,
                "resolved_path": _display(selected),
                "source": source,
            }
        )
    if snapshot_file_count == 0:
        raise ContractLifecycleError(
            "lifecycle-code snapshot root does not provide any declared locked file"
        )
    declared_paths = [entry["declared_path"] for entry in files]
    resolved_paths = [entry["resolved_path"] for entry in files]
    if len(set(declared_paths)) != len(files) or len(set(resolved_paths)) != len(files):
        raise ContractLifecycleError(
            "lifecycle-code snapshot produces duplicate declared/resolved paths"
        )
    return {
        "root": {
            "path": _display(root),
            "tree_sha256": sha256_path(root),
        },
        "resolved_config": {
            "path": _display(config_path),
            "sha256": sha256_file(config_path),
        },
        "snapshot_file_count": snapshot_file_count,
        "file_count": len(files),
        "files_sha256": sha256_object(files),
        "files": files,
    }


def _recheck_lifecycle_code_snapshot_binding(binding: Mapping[str, Any]) -> None:
    expected_fields = {
        "root",
        "resolved_config",
        "snapshot_file_count",
        "file_count",
        "files_sha256",
        "files",
    }
    _assert_equal(set(binding), expected_fields, "lifecycle-code snapshot fields")
    root_binding = binding.get("root")
    if not isinstance(root_binding, Mapping) or set(root_binding) != {
        "path",
        "tree_sha256",
    }:
        raise ContractLifecycleError(
            "lifecycle-code snapshot root binding is malformed"
        )
    root = _require_regular_directory(
        root_binding.get("path"), "lifecycle-code snapshot root"
    )
    _audit_tree_file_safety(root, "lifecycle-code snapshot root")
    _assert_equal(
        root_binding.get("tree_sha256"),
        sha256_path(root),
        "lifecycle-code snapshot tree hash",
    )
    config_binding = binding.get("resolved_config")
    if not isinstance(config_binding, Mapping) or set(config_binding) != {
        "path",
        "sha256",
    }:
        raise ContractLifecycleError(
            "lifecycle-code snapshot config binding is malformed"
        )
    config_path = _resolve_declared_path(
        config_binding.get("path"), "lifecycle-code snapshot config"
    )
    _assert_equal(
        config_binding.get("sha256"),
        sha256_file(config_path),
        "lifecycle-code snapshot config hash",
    )
    files = binding.get("files")
    if not isinstance(files, list) or not files:
        raise ContractLifecycleError(
            "lifecycle-code snapshot file bindings are missing"
        )
    _assert_equal(binding.get("file_count"), len(files), "lifecycle-code file count")
    _assert_equal(
        binding.get("files_sha256"),
        sha256_object(files),
        "lifecycle-code file-binding hash",
    )
    observed_snapshot_count = 0
    for position, raw_entry in enumerate(files):
        if not isinstance(raw_entry, Mapping) or set(raw_entry) != {
            "declared_path",
            "locked_sha256",
            "resolved_path",
            "source",
        }:
            raise ContractLifecycleError(
                f"lifecycle-code snapshot file {position} is malformed"
            )
        relative = _canonical_lifecycle_relative_path(
            raw_entry.get("declared_path"),
            f"lifecycle-code snapshot file {position}.declared_path",
        )
        source = raw_entry.get("source")
        if source not in {"snapshot", "repository"}:
            raise ContractLifecycleError(
                f"lifecycle-code snapshot file {position}.source is invalid"
            )
        expected_path = (
            root / relative if source == "snapshot" else repo_root() / relative
        )
        selected = _resolve_declared_path(
            raw_entry.get("resolved_path"),
            f"lifecycle-code snapshot file {position}",
        )
        _assert_equal(selected, expected_path.resolve(), "lifecycle-code resolved path")
        locked_sha256 = _require_sha256(
            raw_entry.get("locked_sha256"),
            f"lifecycle-code snapshot file {position}.locked_sha256",
        )
        _assert_equal(
            sha256_file(selected),
            locked_sha256,
            f"lifecycle-code snapshot file {position} hash",
        )
        if source == "snapshot":
            observed_snapshot_count += 1
    _assert_equal(
        binding.get("snapshot_file_count"),
        observed_snapshot_count,
        "lifecycle-code snapshot-file count",
    )


def _derive_case_review_run(
    *, case_unit_id: str, case_dir: Path, lifecycle: Mapping[str, Any]
) -> dict[str, str]:
    _assert_equal(
        lifecycle.get("case_unit_id"), case_unit_id, "derived review-run case ID"
    )
    _assert_equal(lifecycle.get("status"), "accepted", "derived review-run status")
    rounds = lifecycle.get("review_rounds")
    attempts = lifecycle.get("attempts")
    if not isinstance(rounds, int) or rounds < 1:
        raise ContractLifecycleError(
            f"accepted lifecycle has no rounds: {case_unit_id}"
        )
    if not isinstance(attempts, list) or len(attempts) != rounds:
        raise ContractLifecycleError(
            f"accepted lifecycle attempt count differs: {case_unit_id}"
        )
    canonical_case_dir = _require_regular_directory(
        case_dir, f"derived review-run case directory {case_unit_id}"
    )
    review_root = _require_regular_directory(
        canonical_case_dir / "review_attempts",
        f"derived review-run root {case_unit_id}",
    )
    run_ids: set[str] = set()
    final_model_review: Path | None = None
    for position, raw_attempt in enumerate(attempts, start=1):
        if not isinstance(raw_attempt, Mapping):
            raise ContractLifecycleError(
                f"derived review-run attempt {position} is malformed: {case_unit_id}"
            )
        error_only = (
            "error" in raw_attempt or "revision_validation_error" in raw_attempt
        )
        decision = raw_attempt.get("decision")
        model_value = raw_attempt.get("model_review_path")
        if (
            not error_only
            and decision in {"accept", "revise"}
            and not isinstance(model_value, str)
        ):
            raise ContractLifecycleError(
                f"accepted/revise attempt omits model_review_path: {case_unit_id}"
            )
        for field, value in raw_attempt.items():
            if not field.endswith("_path") or not isinstance(value, str):
                continue
            declared = _absolute_path(value)
            _reject_symlink_ancestors(
                declared, f"derived review-run {case_unit_id}.{field}"
            )
            resolved = declared.resolve()
            try:
                relative = resolved.relative_to(review_root)
            except ValueError:
                continue
            selected = _require_regular_file(
                resolved, f"derived review-run {case_unit_id}.{field}"
            )
            if len(relative.parts) != 2:
                raise ContractLifecycleError(
                    f"review-attempt path is not directly under one run: {case_unit_id}"
                )
            run_id = relative.parts[0]
            if _CANONICAL_REVIEW_RUN_ID_RE.fullmatch(run_id) is None:
                raise ContractLifecycleError(
                    f"review-attempt run ID is non-canonical: {case_unit_id}"
                )
            run_ids.add(run_id)
            if field == "model_review_path" and position == rounds:
                final_model_review = selected
        if (
            not error_only
            and decision in {"accept", "revise"}
            and model_value is not None
        ):
            model_path = _require_regular_file(
                _absolute_path(str(model_value)),
                f"derived review-run model review {case_unit_id} round {position}",
            )
            try:
                model_path.relative_to(review_root)
            except ValueError as exc:
                raise ContractLifecycleError(
                    f"model review is outside review_attempts: {case_unit_id}"
                ) from exc
    if len(run_ids) != 1:
        raise ContractLifecycleError(
            f"accepted lifecycle does not bind exactly one review run: {case_unit_id}"
        )
    actual_run_id = next(iter(run_ids))
    active_root = _require_regular_directory(
        review_root / actual_run_id, f"derived active review run {case_unit_id}"
    )
    _audit_tree_file_safety(active_root, f"derived active review run {case_unit_id}")
    final_attempt = attempts[-1]
    assert isinstance(final_attempt, Mapping)
    _assert_equal(
        final_attempt.get("decision"),
        "accept",
        f"derived final review decision {case_unit_id}",
    )
    if final_model_review is None or final_model_review.parent != active_root:
        raise ContractLifecycleError(
            f"final accepted model review is outside the active run: {case_unit_id}"
        )
    return {
        "case_unit_id": case_unit_id,
        "actual_run_id": actual_run_id,
        "tree_sha256": sha256_path(active_root),
    }


def _per_case_review_run_binding(
    entries: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    ordered = [dict(entry) for entry in entries]
    if len(ordered) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            "derived review-run binding must contain exactly 949 cases"
        )
    case_ids = [entry.get("case_unit_id") for entry in ordered]
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ContractLifecycleError(
            "derived review-run binding has a malformed case ID"
        )
    if len(set(case_ids)) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("derived review-run case IDs are not unique")
    for entry in ordered:
        _assert_equal(
            set(entry),
            {"case_unit_id", "actual_run_id", "tree_sha256"},
            "derived review-run entry fields",
        )
        if _CANONICAL_REVIEW_RUN_ID_RE.fullmatch(str(entry["actual_run_id"])) is None:
            raise ContractLifecycleError("derived review-run ID is non-canonical")
        _require_sha256(entry["tree_sha256"], "derived review-run tree")
    return {
        "expected_count": freeze_v1.EXPECTED_CASE_COUNT,
        "entry_order_sha256": sha256_object(ordered),
        "entry_set_sha256": sha256_object(
            sorted(ordered, key=lambda entry: str(entry["case_unit_id"]))
        ),
        "entries": ordered,
    }


def _recheck_per_case_review_runs(base: Mapping[str, Any]) -> None:
    binding = base.get("per_case_review_runs")
    if not isinstance(binding, Mapping) or set(binding) != {
        "expected_count",
        "entry_order_sha256",
        "entry_set_sha256",
        "entries",
    }:
        raise ContractLifecycleError("per-case review-run binding is malformed")
    entries = binding.get("entries")
    if not isinstance(entries, list):
        raise ContractLifecycleError("per-case review-run entries are missing")
    _assert_equal(
        dict(binding),
        _per_case_review_run_binding(entries),
        "stored per-case review-run binding",
    )
    inputs = base.get("inputs")
    if not isinstance(inputs, Mapping) or not isinstance(
        inputs.get("draft_root"), Mapping
    ):
        raise ContractLifecycleError("per-case review-run draft binding is missing")
    drafts = _require_regular_directory(
        inputs["draft_root"].get("path"), "per-case review-run draft root"
    )
    recomputed: list[dict[str, str]] = []
    for position, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, Mapping):
            raise ContractLifecycleError(
                f"per-case review-run entry {position} is malformed"
            )
        case_unit_id = raw_entry.get("case_unit_id")
        if (
            not isinstance(case_unit_id, str)
            or freeze_v1.CASE_ID_RE.fullmatch(case_unit_id) is None
        ):
            raise ContractLifecycleError(
                f"per-case review-run entry {position} has a non-canonical case ID"
            )
        case_dir = _require_regular_directory(
            drafts / freeze_v1._safe_case_dir_name(case_unit_id),
            f"per-case review-run case directory {case_unit_id}",
        )
        lifecycle = _load_json_mapping(
            _require_regular_file(
                case_dir / "review_lifecycle.json",
                f"per-case review-run lifecycle {case_unit_id}",
            ),
            f"per-case review-run lifecycle {case_unit_id}",
        )
        recomputed.append(
            _derive_case_review_run(
                case_unit_id=case_unit_id,
                case_dir=case_dir,
                lifecycle=lifecycle,
            )
        )
    expected = _per_case_review_run_binding(recomputed)
    _assert_equal(dict(binding), expected, "current per-case review-run binding")


def _classify_review_attempt(
    attempt: Mapping[str, Any], *, context: str
) -> str:
    """Classify exactly the four outcomes emitted by the locked review producer."""

    returncode = attempt.get("returncode")
    if type(returncode) is not int:
        raise ContractLifecycleError(f"{context} returncode is malformed")
    if "revision_validation_error" in attempt:
        raise ContractLifecycleError(
            f"{context} contains an unresolved revision validation error"
        )
    deterministic = attempt.get("deterministic_review")
    if not isinstance(deterministic, Mapping):
        raise ContractLifecycleError(f"{context} deterministic review is malformed")

    fields = frozenset(attempt)
    if returncode != 0:
        _assert_equal(
            fields,
            _REVIEW_ATTEMPT_COMMON_FIELDS | {"error"},
            f"{context} failed-call fields",
        )
        error = attempt.get("error")
        if not isinstance(error, str) or not error.strip():
            raise ContractLifecycleError(f"{context} failed call has no error")
        return "failed_call"

    error = attempt.get("error")
    if error is not None:
        _assert_equal(
            error,
            _DETERMINISTIC_REJECT_ERROR,
            f"{context} rejected-attempt error",
        )
        _assert_equal(
            fields,
            _REVIEW_ATTEMPT_COMMON_FIELDS | _REVIEW_ATTEMPT_MODEL_FIELDS | {"error"},
            f"{context} deterministic-rejection fields",
        )
        _assert_equal(
            attempt.get("decision"),
            "accept",
            f"{context} deterministic-rejection decision",
        )
        if deterministic == {"status": "pass", "findings": []}:
            raise ContractLifecycleError(
                f"{context} rejects an accept despite a passing deterministic review"
            )
        return "deterministically_rejected_accept"

    _assert_equal(
        fields,
        _REVIEW_ATTEMPT_COMMON_FIELDS | _REVIEW_ATTEMPT_MODEL_FIELDS,
        f"{context} successful-attempt fields",
    )
    decision = attempt.get("decision")
    if decision == "revise":
        return "successful_revise"
    if decision == "accept":
        _assert_equal(
            deterministic,
            {"status": "pass", "findings": []},
            f"{context} accepted deterministic review",
        )
        return "successful_accept"
    raise ContractLifecycleError(f"{context} decision is invalid: {decision!r}")


def _review_attempt_binding(
    *,
    case_unit_id: str,
    active_root: Path,
    attempt: Mapping[str, Any],
    position: int,
    outcome: str,
) -> dict[str, Any]:
    """Bind one attempt receipt to its exact, outcome-specific sidecar set."""

    context = f"{case_unit_id} review attempt {position}"
    _assert_equal(attempt.get("round"), position, f"{context} number")
    started = freeze_v1._parse_aware_timestamp(
        attempt.get("started_at"), f"{context}.started_at"
    )
    finished = freeze_v1._parse_aware_timestamp(
        attempt.get("finished_at"), f"{context}.finished_at"
    )
    if finished < started:
        raise ContractLifecycleError(f"{context} finishes before it starts")

    prefix = f"round_{position:02d}."
    artifact_paths = sorted(
        path for path in active_root.iterdir() if path.name.startswith(prefix)
    )
    artifact_hashes: dict[str, str] = {}
    for artifact in artifact_paths:
        selected = _require_regular_file(artifact, f"{context} sidecar")
        artifact_hashes[selected.name] = sha256_file(selected)

    expected_names = {
        f"round_{position:02d}.stdout.log",
        f"round_{position:02d}.stderr.log",
    }
    deterministic = attempt["deterministic_review"]
    assert isinstance(deterministic, Mapping)
    if outcome != "failed_call":
        expected_names.update(
            {
                f"round_{position:02d}.model_review.json",
                f"round_{position:02d}.model_review.api_response.json",
                f"round_{position:02d}.model_review.llm_call.json",
                f"round_{position:02d}.model_review.reasoning_summary.txt",
            }
        )
    if deterministic != {"status": "pass", "findings": []}:
        expected_names.add(f"round_{position:02d}.review_prompt.md")
    if outcome == "successful_revise":
        expected_names.add(f"round_{position:02d}.revised_checklist.yaml")
    _assert_equal(
        set(artifact_hashes), expected_names, f"{context} exact sidecar set"
    )

    input_hash = _require_sha256(
        attempt.get("input_checklist_sha256"), f"{context} input checklist"
    )
    prompt_hash = _require_sha256(
        attempt.get("review_prompt_sha256"), f"{context} review prompt"
    )
    model_hash: str | None = None
    if outcome != "failed_call":
        model_hash = _require_sha256(
            attempt.get("model_review_sha256"), f"{context} model review"
        )
        _assert_equal(
            artifact_hashes[f"round_{position:02d}.model_review.json"],
            model_hash,
            f"{context} model-review sidecar hash",
        )
    revision_hash = (
        artifact_hashes.get(f"round_{position:02d}.revised_checklist.yaml")
        if outcome == "successful_revise"
        else None
    )
    error_hash = (
        sha256_object(attempt["error"])
        if outcome
        in {"failed_call", "deterministically_rejected_accept"}
        else None
    )
    return {
        "round": position,
        "outcome": outcome,
        "returncode": attempt["returncode"],
        "started_at": attempt["started_at"],
        "finished_at": attempt["finished_at"],
        "attempt_receipt_sha256": sha256_object(dict(attempt)),
        "input_checklist_sha256": input_hash,
        "review_prompt_sha256": prompt_hash,
        "model_review_sha256": model_hash,
        "revision_checklist_sha256": revision_hash,
        "error_sha256": error_hash,
        "artifact_hashes": artifact_hashes,
        "artifact_hashes_sha256": sha256_object(artifact_hashes),
    }


def _review_attempt_state_machine_entry(
    *, case_unit_id: str, attempts: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    outcomes = [str(attempt["outcome"]) for attempt in attempts]
    failed_calls = outcomes.count("failed_call")
    deterministic_rejections = outcomes.count(
        "deterministically_rejected_accept"
    )
    rejected = failed_calls + deterministic_rejections
    revisions = outcomes.count("successful_revise")
    accepts = outcomes.count("successful_accept")
    return {
        "case_unit_id": case_unit_id,
        "total_attempts": len(attempts),
        "successful_revision_attempts": revisions,
        "failed_call_attempts": failed_calls,
        "deterministically_rejected_attempts": deterministic_rejections,
        "rejected_intermediate_attempts": rejected,
        "accepted_attempts": accepts,
        "unresolved_attempts": 0,
        "final_outcome": outcomes[-1] if outcomes else None,
        "attempts_sha256": sha256_object(list(attempts)),
        "attempts": [dict(attempt) for attempt in attempts],
    }


def _review_attempt_state_machine_binding(
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    ordered = [dict(entry) for entry in entries]
    if len(ordered) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            "review-attempt state-machine binding must contain exactly 949 cases"
        )
    case_ids = [entry.get("case_unit_id") for entry in ordered]
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ContractLifecycleError("review-attempt state-machine case ID is malformed")
    if len(set(case_ids)) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            "review-attempt state-machine case IDs are not unique"
        )
    rejected_cases = sum(
        int(entry.get("rejected_intermediate_attempts", -1)) > 0
        for entry in ordered
    )
    return {
        "expected_count": freeze_v1.EXPECTED_CASE_COUNT,
        "accepted_cases": sum(
            entry.get("final_outcome") == "successful_accept" for entry in ordered
        ),
        "rejected_intermediate_cases": rejected_cases,
        "rejected_intermediate_attempts": sum(
            int(entry.get("rejected_intermediate_attempts", -1))
            for entry in ordered
        ),
        "unresolved_cases": sum(
            int(entry.get("unresolved_attempts", -1)) > 0 for entry in ordered
        ),
        "total_attempts": sum(int(entry.get("total_attempts", -1)) for entry in ordered),
        "case_id_order_sha256": sha256_object(case_ids),
        "case_id_set_sha256": sha256_object(sorted(case_ids)),
        "entries_sha256": sha256_object(ordered),
        "entries": ordered,
    }


def _validate_review_attempt_state_machine_binding(
    binding: Mapping[str, Any],
) -> None:
    expected_fields = {
        "expected_count",
        "accepted_cases",
        "rejected_intermediate_cases",
        "rejected_intermediate_attempts",
        "unresolved_cases",
        "total_attempts",
        "case_id_order_sha256",
        "case_id_set_sha256",
        "entries_sha256",
        "entries",
    }
    _assert_equal(set(binding), expected_fields, "review-attempt state-machine fields")
    entries = binding.get("entries")
    if not isinstance(entries, list):
        raise ContractLifecycleError("review-attempt state-machine entries are missing")
    entry_fields = {
        "case_unit_id",
        "total_attempts",
        "successful_revision_attempts",
        "failed_call_attempts",
        "deterministically_rejected_attempts",
        "rejected_intermediate_attempts",
        "accepted_attempts",
        "unresolved_attempts",
        "final_outcome",
        "attempts_sha256",
        "attempts",
    }
    attempt_fields = {
        "round",
        "outcome",
        "returncode",
        "started_at",
        "finished_at",
        "attempt_receipt_sha256",
        "input_checklist_sha256",
        "review_prompt_sha256",
        "model_review_sha256",
        "revision_checklist_sha256",
        "error_sha256",
        "artifact_hashes",
        "artifact_hashes_sha256",
    }
    for entry_position, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, Mapping):
            raise ContractLifecycleError(
                f"review-attempt state-machine entry {entry_position} is malformed"
            )
        entry = dict(raw_entry)
        _assert_equal(set(entry), entry_fields, "review-attempt state-machine entry")
        case_unit_id = entry.get("case_unit_id")
        if (
            not isinstance(case_unit_id, str)
            or freeze_v1.CASE_ID_RE.fullmatch(case_unit_id) is None
        ):
            raise ContractLifecycleError(
                "review-attempt state-machine case ID is non-canonical"
            )
        attempts = entry.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            raise ContractLifecycleError(
                f"review-attempt state-machine has no attempts: {case_unit_id}"
            )
        previous_finished: datetime | None = None
        outcomes: list[str] = []
        for position, raw_attempt in enumerate(attempts, start=1):
            if not isinstance(raw_attempt, Mapping):
                raise ContractLifecycleError(
                    f"review-attempt binding is malformed: {case_unit_id} round {position}"
                )
            attempt = dict(raw_attempt)
            _assert_equal(set(attempt), attempt_fields, "review-attempt binding fields")
            _assert_equal(attempt.get("round"), position, "review-attempt binding order")
            outcome = attempt.get("outcome")
            if outcome not in _REVIEW_ATTEMPT_OUTCOMES:
                raise ContractLifecycleError("review-attempt outcome is invalid")
            outcomes.append(str(outcome))
            started = freeze_v1._parse_aware_timestamp(
                attempt.get("started_at"), "review-attempt binding started_at"
            )
            finished = freeze_v1._parse_aware_timestamp(
                attempt.get("finished_at"), "review-attempt binding finished_at"
            )
            if finished < started or (
                previous_finished is not None and started <= previous_finished
            ):
                raise ContractLifecycleError("review-attempt binding time order differs")
            previous_finished = finished
            for field in (
                "attempt_receipt_sha256",
                "input_checklist_sha256",
                "review_prompt_sha256",
            ):
                _require_sha256(attempt.get(field), f"review-attempt {field}")
            model_hash = attempt.get("model_review_sha256")
            revision_hash = attempt.get("revision_checklist_sha256")
            error_hash = attempt.get("error_sha256")
            returncode = attempt.get("returncode")
            if type(returncode) is not int:
                raise ContractLifecycleError("review-attempt returncode is malformed")
            if outcome == "failed_call":
                if returncode == 0 or model_hash is not None or revision_hash is not None:
                    raise ContractLifecycleError("failed review-call binding is invalid")
                _require_sha256(error_hash, "failed review-call error")
            else:
                if returncode != 0:
                    raise ContractLifecycleError("model review binding has nonzero return")
                _require_sha256(model_hash, "model review binding")
                if outcome == "successful_revise":
                    _require_sha256(revision_hash, "review revision binding")
                    if error_hash is not None:
                        raise ContractLifecycleError("successful revision binds an error")
                elif revision_hash is not None:
                    raise ContractLifecycleError("non-revision attempt binds a revision")
                if outcome == "deterministically_rejected_accept":
                    _require_sha256(error_hash, "deterministic-rejection error")
                elif error_hash is not None:
                    raise ContractLifecycleError("successful attempt binds an error")
            artifacts = attempt.get("artifact_hashes")
            if not isinstance(artifacts, Mapping) or not artifacts:
                raise ContractLifecycleError("review-attempt artifact map is missing")
            for digest in artifacts.values():
                _require_sha256(digest, "review-attempt artifact")
            _assert_equal(
                attempt.get("artifact_hashes_sha256"),
                sha256_object(artifacts),
                "review-attempt artifact aggregate",
            )
        if outcomes[-1] != "successful_accept" or outcomes.count(
            "successful_accept"
        ) != 1:
            raise ContractLifecycleError(
                f"review-attempt state machine has no unique final accept: {case_unit_id}"
            )
        expected_entry = _review_attempt_state_machine_entry(
            case_unit_id=case_unit_id, attempts=attempts
        )
        _assert_equal(entry, expected_entry, "review-attempt state-machine entry")
    _assert_equal(
        dict(binding),
        _review_attempt_state_machine_binding(entries),
        "review-attempt state-machine aggregate",
    )
    _assert_equal(
        binding.get("accepted_cases"),
        freeze_v1.EXPECTED_CASE_COUNT,
        "review-attempt accepted denominator",
    )
    _assert_equal(binding.get("unresolved_cases"), 0, "review-attempt unresolved cases")


def _review_revised_semantics_binding(
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    ordered = [dict(entry) for entry in entries]
    case_ids = [entry.get("case_unit_id") for entry in ordered]
    if len(set(case_ids)) != len(case_ids):
        raise ContractLifecycleError(
            "active-run revised-semantics case IDs are not unique"
        )
    for entry in ordered:
        _assert_equal(
            set(entry),
            {"case_unit_id", "lifecycle_revised", "generated_to_final_changed"},
            "active-run revised-semantics entry",
        )
        case_unit_id = entry.get("case_unit_id")
        if (
            not isinstance(case_unit_id, str)
            or freeze_v1.CASE_ID_RE.fullmatch(case_unit_id) is None
        ):
            raise ContractLifecycleError(
                "active-run revised-semantics case ID is non-canonical"
            )
        _assert_equal(
            entry.get("lifecycle_revised"),
            False,
            "active-run lifecycle revised flag",
        )
        _assert_equal(
            entry.get("generated_to_final_changed"),
            True,
            "active-run generated/final delta",
        )
    return {
        "case_count": len(ordered),
        "case_id_order_sha256": sha256_object(case_ids),
        "case_id_set_sha256": sha256_object(sorted(str(item) for item in case_ids)),
        "entries_sha256": sha256_object(ordered),
        "entries": ordered,
    }


def _validate_resume_report_compatibility(binding: Mapping[str, Any]) -> None:
    _assert_equal(
        set(binding),
        {
            "actual_review_results_sha256",
            "normalized_review_results_sha256",
            "reused_review_count",
            "freshly_accepted_count",
            "reused_case_id_order_sha256",
            "reused_case_id_set_sha256",
        },
        "draft resume-report compatibility fields",
    )
    for field in (
        "actual_review_results_sha256",
        "normalized_review_results_sha256",
        "reused_case_id_order_sha256",
        "reused_case_id_set_sha256",
    ):
        _require_sha256(binding.get(field), f"draft resume-report {field}")
    _assert_equal(
        binding.get("reused_review_count"),
        948,
        "draft resume-report reused denominator",
    )
    _assert_equal(
        binding.get("freshly_accepted_count"),
        1,
        "draft resume-report fresh denominator",
    )


def _generation_attempt_state_machine_entry(
    *, case_unit_id: str, attempts: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    outcomes = [str(attempt["outcome"]) for attempt in attempts]
    return {
        "case_unit_id": case_unit_id,
        "total_attempts": len(attempts),
        "failed_intermediate_attempts": outcomes.count("failed_call"),
        "accepted_attempts": outcomes.count("successful_generation"),
        "unresolved_attempts": 0,
        "final_outcome": outcomes[-1] if outcomes else None,
        "attempts_sha256": sha256_object(list(attempts)),
        "attempts": [dict(attempt) for attempt in attempts],
    }


def _generation_attempt_state_machine_binding(
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    ordered = [dict(entry) for entry in entries]
    if len(ordered) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            "generation-attempt state-machine binding must contain exactly 949 cases"
        )
    case_ids = [entry.get("case_unit_id") for entry in ordered]
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ContractLifecycleError(
            "generation-attempt state-machine case ID is malformed"
        )
    if len(set(case_ids)) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            "generation-attempt state-machine case IDs are not unique"
        )
    return {
        "expected_count": freeze_v1.EXPECTED_CASE_COUNT,
        "accepted_cases": sum(
            entry.get("final_outcome") == "successful_generation"
            for entry in ordered
        ),
        "retried_cases": sum(
            int(entry.get("failed_intermediate_attempts", -1)) > 0
            for entry in ordered
        ),
        "failed_intermediate_attempts": sum(
            int(entry.get("failed_intermediate_attempts", -1))
            for entry in ordered
        ),
        "unresolved_cases": sum(
            int(entry.get("unresolved_attempts", -1)) > 0 for entry in ordered
        ),
        "total_attempts": sum(int(entry.get("total_attempts", -1)) for entry in ordered),
        "case_id_order_sha256": sha256_object(case_ids),
        "case_id_set_sha256": sha256_object(sorted(case_ids)),
        "entries_sha256": sha256_object(ordered),
        "entries": ordered,
    }


def _validate_generation_attempt_state_machine_binding(
    binding: Mapping[str, Any],
) -> None:
    _assert_equal(
        set(binding),
        {
            "expected_count",
            "accepted_cases",
            "retried_cases",
            "failed_intermediate_attempts",
            "unresolved_cases",
            "total_attempts",
            "case_id_order_sha256",
            "case_id_set_sha256",
            "entries_sha256",
            "entries",
        },
        "generation-attempt state-machine fields",
    )
    entries = binding.get("entries")
    if not isinstance(entries, list):
        raise ContractLifecycleError(
            "generation-attempt state-machine entries are missing"
        )
    for raw_entry in entries:
        if not isinstance(raw_entry, Mapping):
            raise ContractLifecycleError(
                "generation-attempt state-machine entry is malformed"
            )
        entry = dict(raw_entry)
        _assert_equal(
            set(entry),
            {
                "case_unit_id",
                "total_attempts",
                "failed_intermediate_attempts",
                "accepted_attempts",
                "unresolved_attempts",
                "final_outcome",
                "attempts_sha256",
                "attempts",
            },
            "generation-attempt state-machine entry fields",
        )
        attempts = entry.get("attempts")
        case_unit_id = entry.get("case_unit_id")
        if (
            not isinstance(case_unit_id, str)
            or freeze_v1.CASE_ID_RE.fullmatch(case_unit_id) is None
            or not isinstance(attempts, list)
            or not attempts
        ):
            raise ContractLifecycleError(
                "generation-attempt state-machine entry is malformed"
            )
        for position, raw_attempt in enumerate(attempts, start=1):
            if not isinstance(raw_attempt, Mapping):
                raise ContractLifecycleError("generation-attempt binding is malformed")
            attempt = dict(raw_attempt)
            _assert_equal(
                set(attempt),
                {
                    "attempt_index",
                    "outcome",
                    "returncode",
                    "max_output_tokens",
                    "http_timeout_seconds",
                    "codex_timeout_seconds",
                    "duration_seconds",
                    "attempt_receipt_sha256",
                    "validator_sha256",
                    "stderr_tail_sha256",
                    "artifact_hashes",
                    "artifact_hashes_sha256",
                },
                "generation-attempt binding fields",
            )
            _assert_equal(
                attempt.get("attempt_index"), position, "generation-attempt order"
            )
            outcome = attempt.get("outcome")
            if outcome not in {"failed_call", "successful_generation"}:
                raise ContractLifecycleError("generation-attempt outcome is invalid")
            returncode = attempt.get("returncode")
            if (
                type(returncode) is not int
                or type(attempt.get("max_output_tokens")) is not int
                or int(attempt["max_output_tokens"]) <= 0
                or type(attempt.get("http_timeout_seconds")) is not int
                or int(attempt["http_timeout_seconds"]) <= 0
                or type(attempt.get("codex_timeout_seconds")) is not int
                or int(attempt["codex_timeout_seconds"]) <= 0
                or isinstance(attempt.get("duration_seconds"), bool)
                or not isinstance(attempt.get("duration_seconds"), (int, float))
                or float(attempt["duration_seconds"]) <= 0
            ):
                raise ContractLifecycleError(
                    "generation-attempt runtime fields are malformed"
                )
            validator_hash = attempt.get("validator_sha256")
            if outcome == "failed_call":
                if returncode == 0 or validator_hash is not None:
                    raise ContractLifecycleError(
                        "failed generation-attempt binding is invalid"
                    )
            else:
                if returncode != 0:
                    raise ContractLifecycleError(
                        "successful generation-attempt has nonzero return"
                    )
                _require_sha256(validator_hash, "generation validator")
            for field in (
                "attempt_receipt_sha256",
                "stderr_tail_sha256",
            ):
                _require_sha256(attempt.get(field), f"generation-attempt {field}")
            artifacts = attempt.get("artifact_hashes")
            if not isinstance(artifacts, Mapping) or not artifacts:
                raise ContractLifecycleError(
                    "generation-attempt artifact map is missing"
                )
            for digest in artifacts.values():
                _require_sha256(digest, "generation-attempt artifact")
            _assert_equal(
                attempt.get("artifact_hashes_sha256"),
                sha256_object(artifacts),
                "generation-attempt artifact aggregate",
            )
        if attempts[-1].get("outcome") != "successful_generation" or sum(
            attempt.get("outcome") == "successful_generation"
            for attempt in attempts
            if isinstance(attempt, Mapping)
        ) != 1:
            raise ContractLifecycleError(
                "generation-attempt state machine has no unique final success"
            )
        _assert_equal(
            entry,
            _generation_attempt_state_machine_entry(
                case_unit_id=case_unit_id, attempts=attempts
            ),
            "generation-attempt state-machine entry",
        )
    _assert_equal(
        dict(binding),
        _generation_attempt_state_machine_binding(entries),
        "generation-attempt state-machine aggregate",
    )
    _assert_equal(
        binding.get("accepted_cases"),
        freeze_v1.EXPECTED_CASE_COUNT,
        "generation-attempt accepted denominator",
    )
    _assert_equal(
        binding.get("unresolved_cases"), 0, "generation-attempt unresolved cases"
    )


def _validate_generation_case_provenance_state_machine(
    *,
    case: Any,
    packet: Any,
    case_dir: Path,
    paths: Mapping[str, Path],
    batch_result: Mapping[str, Any],
    config: Mapping[str, Any],
    config_paths: Mapping[str, Path],
    input_lock_time: datetime,
    response_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate the locked draft producer's retry state without rewriting it."""

    generation_config = config.get("generation")
    if not isinstance(generation_config, Mapping):
        raise ContractLifecycleError("generation configuration is malformed")
    attempt_records = batch_result.get("attempts")
    if not isinstance(attempt_records, list) or not attempt_records:
        raise ContractLifecycleError(
            f"generation has no attempts: {case.case_unit_id}"
        )
    token_budgets = generation_config.get("token_budgets")
    if not isinstance(token_budgets, list) or len(attempt_records) > len(token_budgets):
        raise ContractLifecycleError(
            f"generation attempt budget differs: {case.case_unit_id}"
        )

    for field, expected in (
        ("case_unit_dir", case_dir.name),
        ("case_packet_size_bytes", packet.case_packet_path.stat().st_size),
    ):
        freeze_v1._assert_exact(
            batch_result.get(field), expected, f"generation batch {case.case_unit_id}.{field}"
        )
    freeze_v1._assert_exact(
        freeze_v1._resolve_declared_artifact_path(
            batch_result.get("case_packet"),
            f"generation batch {case.case_unit_id}.case_packet",
        ),
        packet.case_packet_path,
        f"generation batch packet {case.case_unit_id}",
    )
    freeze_v1._assert_exact(
        freeze_v1._resolve_declared_artifact_path(
            batch_result.get("checklist_path"),
            f"generation batch {case.case_unit_id}.checklist_path",
        ),
        case_dir / "checklist.yaml",
        f"generation promoted checklist path {case.case_unit_id}",
    )

    attempt_bindings: list[dict[str, Any]] = []
    final_paths: dict[str, Path] | None = None
    for position, raw_attempt in enumerate(attempt_records, start=1):
        if not isinstance(raw_attempt, Mapping):
            raise ContractLifecycleError(
                f"generation attempt is malformed: {case.case_unit_id}"
            )
        attempt = dict(raw_attempt)
        context = f"generation {case.case_unit_id} attempt {position}"
        freeze_v1._assert_exact(
            attempt.get("attempt_index"), position, f"{context} index"
        )
        freeze_v1._assert_exact(
            attempt.get("max_output_tokens"),
            token_budgets[position - 1],
            f"{context} retry label",
        )
        freeze_v1._assert_exact(
            attempt.get("codex_timeout_seconds"),
            generation_config["timeout_seconds"],
            f"{context} timeout",
        )
        http_timeout = attempt.get("http_timeout_seconds")
        duration = attempt.get("duration_seconds")
        if (
            type(http_timeout) is not int
            or http_timeout <= 0
            or isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or duration <= 0
        ):
            raise ContractLifecycleError(f"{context} timing fields are malformed")
        returncode = attempt.get("returncode")
        if type(returncode) is not int:
            raise ContractLifecycleError(f"{context} returncode is malformed")
        is_success = returncode == 0 and "validator" in attempt
        if is_success:
            if position != len(attempt_records):
                raise ContractLifecycleError(f"{context} succeeds before final attempt")
            freeze_v1._assert_exact(
                set(attempt),
                _GENERATION_ATTEMPT_COMMON_FIELDS | {"validator"},
                f"{context} fields",
            )
            validator = attempt.get("validator")
            if not isinstance(validator, str) or not validator.strip():
                raise ContractLifecycleError(f"{context} validator is missing")
            outcome = "successful_generation"
        else:
            if returncode == 0 or position == len(attempt_records):
                raise ContractLifecycleError(f"{context} unresolved failure")
            freeze_v1._assert_exact(
                set(attempt), _GENERATION_ATTEMPT_COMMON_FIELDS, f"{context} fields"
            )
            validator = None
            outcome = "failed_call"

        prefix = case_dir / f"attempt_{position:02d}"
        expected_names = {
            f"attempt_{position:02d}.stdout.log",
            f"attempt_{position:02d}.stderr.log",
        }
        if is_success:
            expected_names.update(
                {
                    f"attempt_{position:02d}.checklist.yaml",
                    f"attempt_{position:02d}.checklist.json",
                    f"attempt_{position:02d}.api_response.json",
                    f"attempt_{position:02d}.llm_call.json",
                    f"attempt_{position:02d}.reasoning_summary.txt",
                }
            )
        artifact_paths = sorted(
            path for path in case_dir.iterdir() if path.name.startswith(f"attempt_{position:02d}.")
        )
        artifact_hashes = {
            path.name: sha256_file(_require_regular_file(path, f"{context} sidecar"))
            for path in artifact_paths
        }
        _assert_equal(set(artifact_hashes), expected_names, f"{context} sidecar set")
        stderr_text = prefix.with_suffix(".stderr.log").read_text(encoding="utf-8")
        stderr_tail = stderr_text.strip().splitlines()[-1] if stderr_text.strip() else ""
        freeze_v1._assert_exact(
            attempt.get("stderr_tail"), stderr_tail, f"{context} stderr tail"
        )
        if is_success:
            assert isinstance(validator, str)
            checklist_path = prefix.with_suffix(".checklist.yaml")
            if not validator.rstrip().endswith(str(checklist_path)):
                raise ContractLifecycleError(f"{context} validator path differs")
            final_paths = {
                "checklist": checklist_path,
                "checklist_json": prefix.with_suffix(".checklist.json"),
                "api_response": prefix.with_suffix(".api_response.json"),
                "llm_call": prefix.with_suffix(".llm_call.json"),
                "reasoning_summary": prefix.with_suffix(".reasoning_summary.txt"),
            }
        attempt_bindings.append(
            {
                "attempt_index": position,
                "outcome": outcome,
                "returncode": returncode,
                "max_output_tokens": attempt["max_output_tokens"],
                "http_timeout_seconds": http_timeout,
                "codex_timeout_seconds": attempt["codex_timeout_seconds"],
                "duration_seconds": duration,
                "attempt_receipt_sha256": sha256_object(attempt),
                "validator_sha256": (
                    sha256_object(validator) if validator is not None else None
                ),
                "stderr_tail_sha256": sha256_object(stderr_tail),
                "artifact_hashes": artifact_hashes,
                "artifact_hashes_sha256": sha256_object(artifact_hashes),
            }
        )

    if final_paths is None:
        raise ContractLifecycleError(
            f"generation has no final success: {case.case_unit_id}"
        )
    for canonical_key, attempt_key in (
        ("generated_checklist", "checklist"),
        ("generated_checklist_json", "checklist_json"),
        ("api_response", "api_response"),
        ("llm_call", "llm_call"),
        ("reasoning_summary", "reasoning_summary"),
    ):
        freeze_v1._assert_exact(
            paths[canonical_key].read_bytes(),
            final_paths[attempt_key].read_bytes(),
            f"promoted generation {canonical_key} for {case.case_unit_id}",
        )
    attempt_checklist = freeze_v1._load_mapping(
        final_paths["checklist"], "generation final-attempt checklist"
    )
    attempt_json = freeze_v1._load_mapping(
        final_paths["checklist_json"], "generation final-attempt checklist JSON"
    )
    freeze_v1._assert_exact(
        attempt_json,
        attempt_checklist,
        f"generation attempt YAML/JSON semantics {case.case_unit_id}",
    )
    final_attempt = attempt_records[-1]
    assert isinstance(final_attempt, Mapping)
    actual_llm_call = freeze_v1._load_mapping(
        final_paths["llm_call"], "generation retry LLM call"
    )
    freeze_v1._assert_exact(
        actual_llm_call.get("max_tokens"),
        final_attempt.get("max_output_tokens"),
        f"generation retry label binding {case.case_unit_id}",
    )
    if not _DRAFT_RETRY_CODEX_CONTEXT_GUARD.acquire(blocking=False):
        raise ContractLifecycleError(
            "draft-retry Codex provenance validation is already active"
        )
    original_loader = freeze_v1._load_mapping
    llm_path = final_paths["llm_call"].resolve()

    def load_with_v1_draft_label(path: Any, label: str) -> dict[str, Any]:
        loaded = original_loader(path, label)
        if Path(path).resolve() == llm_path:
            loaded = {**loaded, "max_tokens": 12000}
        return loaded

    freeze_v1._load_mapping = load_with_v1_draft_label
    try:
        api_response, _, response_id = freeze_v1._validate_codex_call_provenance(
            api_response_path=final_paths["api_response"],
            llm_call_path=final_paths["llm_call"],
            reasoning_summary_path=final_paths["reasoning_summary"],
            case_unit_id=case.case_unit_id,
            task_id=case.task_id,
            phase="draft",
            model=str(generation_config["model"]),
            reasoning_effort=str(generation_config["reasoning_effort"]),
            timeout_seconds=int(generation_config["timeout_seconds"]),
            input_lock_time=input_lock_time,
            response_ids=response_ids,
        )
    finally:
        if freeze_v1._load_mapping is not load_with_v1_draft_label:
            freeze_v1._load_mapping = original_loader
            _DRAFT_RETRY_CODEX_CONTEXT_GUARD.release()
            raise ContractLifecycleError(
                "draft-retry Codex provenance loader changed during validation"
            )
        freeze_v1._load_mapping = original_loader
        _DRAFT_RETRY_CODEX_CONTEXT_GUARD.release()
    try:
        from neurips_ed_track_minimal.scripts.draft_case_checklist import (
            extract_json_text,
            strip_null_fields,
        )

        generated_body = strip_null_fields(extract_json_text(api_response))
    except Exception as exc:
        raise ContractLifecycleError(
            f"generation body reconstruction failed for {case.case_unit_id}: {exc}"
        ) from exc
    expected_body = {
        key: value
        for key, value in attempt_checklist.items()
        if key not in {"schema_version", "case_unit_id", "domain", "task_id"}
    }
    freeze_v1._assert_exact(
        generated_body,
        expected_body,
        f"generation API body/checklist binding {case.case_unit_id}",
    )
    for field, expected in (
        ("schema_version", "case_checklist_v1"),
        ("case_unit_id", case.case_unit_id),
        ("domain", "agentdojo"),
        ("task_id", case.task_id),
    ):
        freeze_v1._assert_exact(
            attempt_checklist.get(field),
            expected,
            f"generation attempt identity {case.case_unit_id}.{field}",
        )

    state_entry = _generation_attempt_state_machine_entry(
        case_unit_id=case.case_unit_id, attempts=attempt_bindings
    )
    result = {
        "case_unit_id": case.case_unit_id,
        "response_id": response_id,
        "attempt_checklist_sha256": sha256_file(final_paths["checklist"]),
        "attempt_checklist_json_sha256": sha256_file(final_paths["checklist_json"]),
        "attempt_api_response_sha256": sha256_file(final_paths["api_response"]),
        "attempt_llm_call_sha256": sha256_file(final_paths["llm_call"]),
        "attempt_reasoning_summary_sha256": sha256_file(
            final_paths["reasoning_summary"]
        ),
        "case_packet_sha256": sha256_file(packet.case_packet_path),
        "composed_draft_prompt_sha256": sha256_file(
            config_paths["composed_draft_prompt"]
        ),
        "checklist_schema_sha256": sha256_file(config_paths["checklist_schema"]),
        "generation_attempt_state_machine_sha256": sha256_object(state_entry),
    }
    return result, state_entry


def _validate_review_case_provenance_state_machine(
    *,
    case: Any,
    packet: Any,
    case_dir: Path,
    generated_checklist_path: Path,
    final_checklist_path: Path,
    review_receipt: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    report_run_id: str,
    config: Mapping[str, Any],
    config_paths: Mapping[str, Path],
    review_schema: Mapping[str, Any],
    checklist_validator: Draft202012Validator,
    input_lock_time: datetime,
    response_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate the producer's retrying review state machine without rewriting it."""

    from neurips_ed_track_minimal.scripts import update_case_locks_batch as batch
    from neurips_ed_track_minimal.scripts.case_checklist_review import (
        review_agentdojo_checklist,
    )
    from neurips_ed_track_minimal.scripts.review_case_checklist_with_codex import (
        extract_json_text,
        normalize_provider_model_review,
        strip_null_fields,
        validate_model_review_body,
    )

    review_config = config.get("review")
    if not isinstance(review_config, Mapping):
        raise ContractLifecycleError("review configuration is malformed")
    attempts = lifecycle.get("attempts")
    rounds = lifecycle.get("review_rounds")
    if not isinstance(rounds, int) or rounds < 1:
        raise ContractLifecycleError(
            f"accepted review has no attempts: {case.case_unit_id}"
        )
    if not isinstance(attempts, list) or len(attempts) != rounds:
        raise ContractLifecycleError(
            f"review attempt denominator differs: {case.case_unit_id}"
        )

    review_root = case_dir / "review_attempts"
    active_root = freeze_v1._require_regular_directory(
        review_root / report_run_id, f"active review run for {case.case_unit_id}"
    )
    stale_runs: list[dict[str, str]] = []
    for run_dir in sorted(path for path in review_root.iterdir() if path.is_dir()):
        if run_dir != active_root:
            stale_runs.append(
                {"run_id": run_dir.name, "tree_sha256": sha256_path(run_dir)}
            )

    generated_hash = sha256_file(generated_checklist_path)
    final_hash = sha256_file(final_checklist_path)
    first_attempt = attempts[0]
    assert isinstance(first_attempt, Mapping)
    first_input_hash = first_attempt.get("input_checklist_sha256")
    if first_input_hash == generated_hash:
        current_input_path = generated_checklist_path
        initial_input_origin = "generated_checklist"
    elif first_input_hash == final_hash:
        current_input_path = final_checklist_path
        initial_input_origin = "preexisting_reviewed_checklist"
    else:
        raise ContractLifecycleError(
            f"active review input is neither generated nor preexisting final: "
            f"{case.case_unit_id}"
        )
    current_declared_input_path = (case_dir / "checklist.yaml").resolve()
    current_input_hash = str(first_input_hash)
    previous_finished: datetime | None = None
    successful_decisions: list[str] = []
    active_expected_files: set[Path] = set()
    attempt_components: list[dict[str, Any]] = []

    for round_index, raw_attempt in enumerate(attempts, start=1):
        if not isinstance(raw_attempt, Mapping):
            raise ContractLifecycleError(
                f"review attempt {round_index} is malformed: {case.case_unit_id}"
            )
        attempt = dict(raw_attempt)
        context = f"review {case.case_unit_id} round {round_index}"
        freeze_v1._assert_exact(
            attempt.get("round"), round_index, f"{context} number"
        )
        outcome = _classify_review_attempt(attempt, context=context)
        if round_index == rounds:
            _assert_equal(
                outcome,
                "successful_accept",
                f"{context} final outcome",
            )
        elif outcome == "successful_accept":
            raise ContractLifecycleError(f"{context} accepts before the final attempt")

        started = freeze_v1._parse_aware_timestamp(
            attempt.get("started_at"), f"{context}.started_at"
        )
        finished = freeze_v1._parse_aware_timestamp(
            attempt.get("finished_at"), f"{context}.finished_at"
        )
        if finished < started:
            raise ContractLifecycleError(f"{context} finishes before it starts")
        if previous_finished is not None and started <= previous_finished:
            raise ContractLifecycleError(
                f"{context} is not a fresh call after the previous attempt"
            )
        previous_finished = finished

        declared_input = freeze_v1._resolve_declared_artifact_path(
            attempt.get("input_checklist_path"), f"{context}.input_checklist_path"
        )
        freeze_v1._assert_exact(
            declared_input,
            current_declared_input_path,
            f"{context} input checklist path",
        )
        freeze_v1._assert_exact(
            attempt.get("input_checklist_sha256"),
            current_input_hash,
            f"{context} input checklist hash",
        )
        current_checklist = freeze_v1._load_mapping(
            current_input_path, f"{context} immutable input checklist"
        )
        deterministic = review_agentdojo_checklist(
            current_checklist, case_packet_path=packet.case_packet_path
        )
        freeze_v1._assert_exact(
            attempt.get("deterministic_review"),
            deterministic,
            f"{context} deterministic review",
        )

        prefix = active_root / f"round_{round_index:02d}"
        if deterministic == {"status": "pass", "findings": []}:
            prompt_path = config_paths["review_prompt"]
        else:
            prompt_path = freeze_v1._require_regular_file(
                prefix.with_suffix(".review_prompt.md"),
                f"{context} review prompt",
            )
            expected_prompt = (
                config_paths["review_prompt"].read_text(encoding="utf-8").rstrip()
            )
            expected_prompt += (
                "\n\n## Deterministic blocking findings\n\n"
                "Treat every item below as blocking. Return `revise` and a complete "
                "corrected checklist.\n\n"
                "```json\n"
                + json.dumps(
                    deterministic.get("findings", []), indent=2, ensure_ascii=False
                )
                + "\n```\n"
            )
            freeze_v1._assert_exact(
                prompt_path.read_text(encoding="utf-8"),
                expected_prompt,
                f"{context} deterministic review prompt",
            )
        freeze_v1._assert_exact(
            freeze_v1._resolve_declared_artifact_path(
                attempt.get("review_prompt_path"), f"{context}.review_prompt_path"
            ),
            prompt_path,
            f"{context} review prompt path",
        )
        freeze_v1._assert_exact(
            attempt.get("review_prompt_sha256"),
            sha256_file(prompt_path),
            f"{context} review prompt hash",
        )

        component = _review_attempt_binding(
            case_unit_id=case.case_unit_id,
            active_root=active_root,
            attempt=attempt,
            position=round_index,
            outcome=outcome,
        )
        for artifact_name in component["artifact_hashes"]:
            active_expected_files.add((active_root / artifact_name).resolve())

        if outcome == "failed_call":
            stdout_text = (prefix.with_suffix(".stdout.log")).read_text(
                encoding="utf-8"
            )
            stderr_text = (prefix.with_suffix(".stderr.log")).read_text(
                encoding="utf-8"
            )
            expected_error = (
                stderr_text or stdout_text or "reviewer produced no output"
            ).strip()[-4000:]
            freeze_v1._assert_exact(
                attempt.get("error"), expected_error, f"{context} failed-call error"
            )
            attempt_components.append(component)
            continue

        model_review_path = prefix.with_suffix(".model_review.json")
        freeze_v1._assert_exact(
            freeze_v1._resolve_declared_artifact_path(
                attempt.get("model_review_path"), f"{context}.model_review_path"
            ),
            model_review_path,
            f"{context} model review path",
        )
        model_review_path = freeze_v1._require_regular_file(
            model_review_path, f"{context} model review"
        )
        freeze_v1._assert_exact(
            attempt.get("model_review_sha256"),
            sha256_file(model_review_path),
            f"{context} model review hash",
        )
        model_review = freeze_v1._load_mapping(
            model_review_path, f"{context} model review"
        )
        try:
            validated_model_review = validate_model_review_body(
                model_review, review_schema
            )
        except Exception as exc:
            raise ContractLifecycleError(
                f"{context} model-review body is invalid: {exc}"
            ) from exc
        freeze_v1._assert_exact(
            validated_model_review,
            model_review,
            f"{context} model-review materialization",
        )
        decision = str(model_review.get("decision") or "")
        freeze_v1._assert_exact(
            attempt.get("decision"), decision, f"{context} decision"
        )

        api_path = prefix.with_suffix(".model_review.api_response.json")
        llm_path = prefix.with_suffix(".model_review.llm_call.json")
        reasoning_path = prefix.with_suffix(".model_review.reasoning_summary.txt")
        api_response, _, _ = freeze_v1._validate_codex_call_provenance(
            api_response_path=api_path,
            llm_call_path=llm_path,
            reasoning_summary_path=reasoning_path,
            case_unit_id=case.case_unit_id,
            task_id=case.task_id,
            phase="checklist_model_review",
            model=str(review_config["model"]),
            reasoning_effort=str(review_config["reasoning_effort"]),
            timeout_seconds=int(review_config["timeout_seconds"]),
            input_lock_time=input_lock_time,
            response_ids=response_ids,
            codex_cli_version=str(config["codex_cli_version"]),
            attempt_started=started,
            attempt_finished=finished,
        )
        try:
            api_model_review = strip_null_fields(
                normalize_provider_model_review(extract_json_text(api_response))
            )
        except Exception as exc:
            raise ContractLifecycleError(
                f"{context} raw model review reconstruction failed: {exc}"
            ) from exc
        freeze_v1._assert_exact(
            api_model_review,
            model_review,
            f"{context} API/model-review body binding",
        )

        if outcome == "deterministically_rejected_accept":
            freeze_v1._assert_exact(
                decision, "accept", f"{context} rejected model decision"
            )
            attempt_components.append(component)
            continue

        successful_decisions.append(decision)
        if outcome == "successful_revise":
            freeze_v1._assert_exact(
                decision, "revise", f"{context} successful revision decision"
            )
            revision_path = freeze_v1._require_regular_file(
                prefix.with_suffix(".revised_checklist.yaml"),
                f"{context} revised checklist",
            )
            expected_revision = freeze_v1._materialize_review_revision(
                model_review,
                case_unit_id=case.case_unit_id,
                task_id=case.task_id,
            )
            freeze_v1._assert_exact(
                freeze_v1._load_mapping(
                    revision_path, f"{context} revised checklist"
                ),
                expected_revision,
                f"{context} revised checklist body",
            )
            expected_revision_bytes = freeze_v1.yaml.safe_dump(
                expected_revision,
                sort_keys=False,
                allow_unicode=True,
                width=1000,
            ).encode("utf-8")
            freeze_v1._assert_exact(
                revision_path.read_bytes(),
                expected_revision_bytes,
                f"{context} canonical revised checklist bytes",
            )
            try:
                batch._validate_checklist(
                    revision_path,
                    packet=packet,
                    checklist_validator=checklist_validator,
                )
            except batch.BatchCaseLockError as exc:
                raise ContractLifecycleError(str(exc)) from exc
            revision_hash = sha256_file(revision_path)
            if revision_hash == current_input_hash:
                raise ContractLifecycleError(
                    f"{context} revise decision did not change the checklist"
                )
            freeze_v1._assert_exact(
                component.get("revision_checklist_sha256"),
                revision_hash,
                f"{context} revision binding",
            )
            current_input_path = revision_path
            current_declared_input_path = revision_path.resolve()
            current_input_hash = revision_hash
        else:
            freeze_v1._assert_exact(
                decision, "accept", f"{context} successful acceptance decision"
            )
        attempt_components.append(component)

    freeze_v1._assert_exact(
        current_input_hash,
        final_hash,
        f"final accepted review input {case.case_unit_id}",
    )
    expected_revised = "revise" in successful_decisions
    freeze_v1._assert_exact(
        lifecycle.get("revised"),
        expected_revised,
        f"review revised flag {case.case_unit_id}",
    )
    freeze_v1._assert_exact(
        "revise" in successful_decisions,
        expected_revised,
        f"review decision/checklist revision equivalence {case.case_unit_id}",
    )
    freeze_v1._assert_exact(
        review_receipt.get("model_review"),
        freeze_v1._load_mapping(
            active_root / f"round_{rounds:02d}.model_review.json",
            "final model review",
        ),
        f"final review receipt/model sidecar {case.case_unit_id}",
    )
    freeze_v1._assert_exact(
        review_receipt.get("deterministic_review"),
        {"status": "pass", "findings": []},
        f"final review deterministic result {case.case_unit_id}",
    )
    freeze_v1._assert_exact(
        review_receipt.get("decision"),
        "accept",
        f"final review decision {case.case_unit_id}",
    )
    freeze_v1._assert_exact(
        review_receipt.get("unresolved_findings"),
        [],
        f"final review unresolved findings {case.case_unit_id}",
    )

    actual_active_files = {
        path.resolve() for path in active_root.iterdir() if path.is_file()
    }
    freeze_v1._assert_exact(
        actual_active_files,
        active_expected_files,
        f"active review artifact set {case.case_unit_id}",
    )
    state_entry = _review_attempt_state_machine_entry(
        case_unit_id=case.case_unit_id, attempts=attempt_components
    )
    result = {
        "case_unit_id": case.case_unit_id,
        "run_id": report_run_id,
        "generated_checklist_sha256": generated_hash,
        "final_checklist_sha256": final_hash,
        "revised": expected_revised,
        "initial_input_origin": initial_input_origin,
        "generated_to_final_changed": generated_hash != final_hash,
        "review_rounds": rounds,
        "attempts_sha256": sha256_object(attempt_components),
        "active_review_tree_sha256": sha256_path(active_root),
        "excluded_stale_review_runs": stale_runs,
        "review_attempt_state_machine_sha256": sha256_object(state_entry),
    }
    return result, state_entry


@contextmanager
def _lifecycle_code_snapshot_validation_context(
    binding: Mapping[str, Any] | None,
    *,
    derive_per_case_review_run: bool = False,
    derive_review_attempt_state_machine: bool = False,
    attempt_state_machine_entries: list[dict[str, Any]] | None = None,
    derive_generation_attempt_state_machine: bool = False,
    generation_attempt_state_machine_entries: list[dict[str, Any]] | None = None,
    revised_semantics_entries: list[dict[str, Any]] | None = None,
    resume_report_compatibility_entries: list[dict[str, Any]] | None = None,
) -> Any:
    if derive_review_attempt_state_machine and not derive_per_case_review_run:
        raise ContractLifecycleError(
            "review-attempt state-machine compatibility requires per-case review runs"
        )
    if not _LIFECYCLE_CODE_CONTEXT_GUARD.acquire(blocking=False):
        raise ContractLifecycleError(
            "lifecycle-code snapshot validation is already active in this process"
        )
    original_validator = freeze_v1._validate_draft_review_config
    original_generation_validator = freeze_v1._validate_generation_case_provenance
    original_review_validator = freeze_v1._validate_review_case_provenance
    original_assert_exact = freeze_v1._assert_exact
    original_loader = freeze_v1._load_mapping
    calls = 0
    files = binding.get("files") if binding is not None else None
    if binding is not None:
        assert isinstance(files, list)
    review_run_entries: list[dict[str, str]] = []
    state_machine_entries = (
        attempt_state_machine_entries
        if attempt_state_machine_entries is not None
        else []
    )
    generation_state_machine_entries = (
        generation_attempt_state_machine_entries
        if generation_attempt_state_machine_entries is not None
        else []
    )
    active_run_revised_entries = (
        revised_semantics_entries if revised_semantics_entries is not None else []
    )
    resume_report_entries = (
        resume_report_compatibility_entries
        if resume_report_compatibility_entries is not None
        else []
    )

    def load_with_resume_report_compatibility(
        path: Any, label: str
    ) -> dict[str, Any]:
        loaded = original_loader(path, label)
        if label != "draft lifecycle report":
            return loaded
        if resume_report_entries:
            raise ContractLifecycleError(
                "draft resume-report compatibility was invoked more than once"
            )
        raw_results = loaded.get("review_results")
        if not isinstance(raw_results, list):
            raise ContractLifecycleError(
                "draft resume report review_results are malformed"
            )
        index_path = freeze_v1._resolve_declared_artifact_path(
            loaded.get("index_path"), "draft resume report index"
        )
        lifecycle_index = original_loader(index_path, "draft resume lifecycle index")
        index_entries = lifecycle_index.get("entries")
        if not isinstance(index_entries, list) or len(index_entries) != len(raw_results):
            raise ContractLifecycleError(
                "draft resume report/index denominators differ"
            )
        normalized_results: list[dict[str, Any]] = []
        reused_case_ids: list[str] = []
        accepted_count = 0
        for position, (raw_result, raw_index) in enumerate(
            zip(raw_results, index_entries)
        ):
            if not isinstance(raw_result, Mapping) or not isinstance(
                raw_index, Mapping
            ):
                raise ContractLifecycleError(
                    f"draft resume result {position} is malformed"
                )
            case_unit_id = raw_result.get("case_unit_id")
            _assert_equal(
                case_unit_id,
                raw_index.get("case_unit_id"),
                f"draft resume result/index case {position}",
            )
            status = raw_result.get("status")
            if status == "reused_review":
                reused_case_ids.append(str(case_unit_id))
                normalized_results.append(
                    {
                        "case_unit_id": case_unit_id,
                        "status": "accepted",
                        "review_rounds": raw_index.get("review_rounds"),
                        "revised": raw_index.get("revised"),
                    }
                )
            elif status == "accepted":
                accepted_count += 1
                normalized_results.append(dict(raw_result))
            else:
                raise ContractLifecycleError(
                    f"draft resume result has invalid status: {case_unit_id}"
                )
        resume_report_entries.append(
            {
                "actual_review_results_sha256": sha256_object(raw_results),
                "normalized_review_results_sha256": sha256_object(
                    normalized_results
                ),
                "reused_review_count": len(reused_case_ids),
                "freshly_accepted_count": accepted_count,
                "reused_case_id_order_sha256": sha256_object(reused_case_ids),
                "reused_case_id_set_sha256": sha256_object(
                    sorted(reused_case_ids)
                ),
            }
        )
        return {**loaded, "review_results": normalized_results}

    def assert_active_run_revised_semantics(
        actual: Any, expected: Any, label: str
    ) -> None:
        prefix = "review lifecycle revised/hash equivalence "
        if label.startswith(prefix) and actual is False and expected is True:
            case_unit_id = label.removeprefix(prefix)
            if any(
                entry["case_unit_id"] == case_unit_id
                for entry in active_run_revised_entries
            ):
                raise ContractLifecycleError(
                    f"active-run revised-semantics case repeated: {case_unit_id}"
                )
            active_run_revised_entries.append(
                {
                    "case_unit_id": case_unit_id,
                    "lifecycle_revised": False,
                    "generated_to_final_changed": True,
                }
            )
            return
        original_assert_exact(actual, expected, label)

    def validate_with_snapshot(config: Mapping[str, Any], **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls != 1:
            raise ContractLifecycleError(
                "lifecycle-code snapshot validator was invoked more than once"
            )
        assert isinstance(files, list)
        raw_locks = config.get("lifecycle_code")
        if not isinstance(raw_locks, list) or len(raw_locks) != len(files):
            raise ContractLifecycleError(
                "in-memory lifecycle-code locks differ from the snapshot plan"
            )
        patched_locks: list[dict[str, Any]] = []
        for position, (raw_lock, raw_file) in enumerate(zip(raw_locks, files)):
            if not isinstance(raw_lock, Mapping) or not isinstance(raw_file, Mapping):
                raise ContractLifecycleError(
                    f"in-memory lifecycle-code lock {position} is malformed"
                )
            _assert_equal(
                raw_lock.get("path"),
                raw_file.get("declared_path"),
                f"in-memory lifecycle-code path {position}",
            )
            _assert_equal(
                raw_lock.get("sha256"),
                raw_file.get("locked_sha256"),
                f"in-memory lifecycle-code hash {position}",
            )
            patched_locks.append(
                {**dict(raw_lock), "path": str(raw_file["resolved_path"])}
            )
        patched_config = {**dict(config), "lifecycle_code": patched_locks}
        return original_validator(patched_config, **kwargs)

    def validate_generation_state_machine(*args: Any, **kwargs: Any) -> Any:
        if args:
            raise ContractLifecycleError(
                "generation-attempt state-machine validator requires keyword arguments"
            )
        case = kwargs.get("case")
        case_unit_id = getattr(case, "case_unit_id", None)
        if not isinstance(case_unit_id, str) or not case_unit_id:
            raise ContractLifecycleError(
                "generation-attempt state-machine case ID is missing"
            )
        result, state_entry = _validate_generation_case_provenance_state_machine(
            **kwargs
        )
        if any(
            entry["case_unit_id"] == case_unit_id
            for entry in generation_state_machine_entries
        ):
            raise ContractLifecycleError(
                f"generation-attempt state-machine case was validated twice: {case_unit_id}"
            )
        generation_state_machine_entries.append(state_entry)
        return result

    def validate_with_derived_review_run(*args: Any, **kwargs: Any) -> Any:
        if args:
            raise ContractLifecycleError(
                "derived review-run validator requires keyword arguments"
            )
        case = kwargs.get("case")
        case_unit_id = getattr(case, "case_unit_id", None)
        if not isinstance(case_unit_id, str) or not case_unit_id:
            raise ContractLifecycleError("derived review-run case ID is missing")
        case_dir = kwargs.get("case_dir")
        lifecycle = kwargs.get("lifecycle")
        if not isinstance(case_dir, Path) or not isinstance(lifecycle, Mapping):
            raise ContractLifecycleError(
                f"derived review-run inputs are malformed: {case_unit_id}"
            )
        derived = _derive_case_review_run(
            case_unit_id=case_unit_id,
            case_dir=case_dir,
            lifecycle=lifecycle,
        )
        if any(entry["case_unit_id"] == case_unit_id for entry in review_run_entries):
            raise ContractLifecycleError(
                f"derived review-run case was validated twice: {case_unit_id}"
            )
        patched_kwargs = {**kwargs, "report_run_id": derived["actual_run_id"]}
        if derive_review_attempt_state_machine:
            result, state_entry = _validate_review_case_provenance_state_machine(
                **patched_kwargs
            )
            if any(
                entry["case_unit_id"] == case_unit_id
                for entry in state_machine_entries
            ):
                raise ContractLifecycleError(
                    f"review-attempt state-machine case was validated twice: {case_unit_id}"
                )
            state_machine_entries.append(state_entry)
        else:
            result = original_review_validator(**patched_kwargs)
        if not isinstance(result, Mapping):
            raise ContractLifecycleError(
                f"derived review-run v1 result is malformed: {case_unit_id}"
            )
        _assert_equal(
            result.get("case_unit_id"), case_unit_id, "derived review-run result case"
        )
        _assert_equal(
            result.get("run_id"),
            derived["actual_run_id"],
            "derived review-run result run ID",
        )
        _assert_equal(
            result.get("active_review_tree_sha256"),
            derived["tree_sha256"],
            "derived review-run result tree",
        )
        review_run_entries.append(derived)
        return result

    if binding is not None:
        freeze_v1._validate_draft_review_config = validate_with_snapshot
    if derive_generation_attempt_state_machine:
        freeze_v1._validate_generation_case_provenance = (
            validate_generation_state_machine
        )
    if derive_per_case_review_run:
        freeze_v1._validate_review_case_provenance = validate_with_derived_review_run
    if derive_review_attempt_state_machine:
        freeze_v1._assert_exact = assert_active_run_revised_semantics
        freeze_v1._load_mapping = load_with_resume_report_compatibility
    context_error: ContractLifecycleError | None = None
    try:
        yield review_run_entries
        if binding is not None and calls != 1:
            context_error = ContractLifecycleError(
                "lifecycle-code snapshot validator was not invoked exactly once"
            )
    finally:
        if binding is not None and (
            freeze_v1._validate_draft_review_config is not validate_with_snapshot
        ):
            context_error = ContractLifecycleError(
                "lifecycle-code snapshot validator changed during guarded validation"
            )
        if derive_per_case_review_run and (
            freeze_v1._validate_review_case_provenance
            is not validate_with_derived_review_run
        ):
            context_error = ContractLifecycleError(
                "derived review-run validator changed during guarded validation"
            )
        if derive_generation_attempt_state_machine and (
            freeze_v1._validate_generation_case_provenance
            is not validate_generation_state_machine
        ):
            context_error = ContractLifecycleError(
                "generation-attempt state-machine validator changed during guarded validation"
            )
        if derive_review_attempt_state_machine and (
            freeze_v1._assert_exact is not assert_active_run_revised_semantics
        ):
            context_error = ContractLifecycleError(
                "active-run revised-semantics validator changed during guarded validation"
            )
        if derive_review_attempt_state_machine and (
            freeze_v1._load_mapping is not load_with_resume_report_compatibility
        ):
            context_error = ContractLifecycleError(
                "draft resume-report compatibility loader changed during validation"
            )
        freeze_v1._validate_draft_review_config = original_validator
        freeze_v1._validate_generation_case_provenance = original_generation_validator
        freeze_v1._validate_review_case_provenance = original_review_validator
        freeze_v1._assert_exact = original_assert_exact
        freeze_v1._load_mapping = original_loader
        _LIFECYCLE_CODE_CONTEXT_GUARD.release()
    if context_error is not None:
        raise context_error


def _build_v1_snapshot(
    *,
    normalized: Mapping[str, Any],
    lifecycle_code_snapshot_root: str | Path | None,
    derive_per_case_review_run: bool = False,
    derive_review_attempt_state_machine: bool = False,
    derive_generation_attempt_state_machine: bool = False,
) -> dict[str, Any]:
    if derive_review_attempt_state_machine and not derive_per_case_review_run:
        raise ContractLifecycleError(
            "review-attempt state-machine compatibility requires per-case review runs"
        )
    if (
        derive_generation_attempt_state_machine
        and not derive_review_attempt_state_machine
    ):
        raise ContractLifecycleError(
            "generation-attempt compatibility requires review-attempt compatibility"
        )
    if (
        lifecycle_code_snapshot_root is None
        and not derive_per_case_review_run
        and not derive_review_attempt_state_machine
        and not derive_generation_attempt_state_machine
    ):
        return freeze_v1.build_checklist_freeze_snapshot(**dict(normalized))
    binding: dict[str, Any] | None = None
    if lifecycle_code_snapshot_root is not None:
        config_path = normalized.get(
            "resolved_config_path", freeze_v1.DEFAULT_DRAFT_REVIEW_CONFIG
        )
        binding = _build_lifecycle_code_snapshot_binding(
            snapshot_root=lifecycle_code_snapshot_root,
            resolved_config_path=config_path,
        )
    state_machine_entries: list[dict[str, Any]] = []
    generation_state_machine_entries: list[dict[str, Any]] = []
    revised_semantics_entries: list[dict[str, Any]] = []
    resume_report_compatibility_entries: list[dict[str, Any]] = []
    with _lifecycle_code_snapshot_validation_context(
        binding,
        derive_per_case_review_run=derive_per_case_review_run,
        derive_review_attempt_state_machine=derive_review_attempt_state_machine,
        attempt_state_machine_entries=state_machine_entries,
        derive_generation_attempt_state_machine=(
            derive_generation_attempt_state_machine
        ),
        generation_attempt_state_machine_entries=generation_state_machine_entries,
        revised_semantics_entries=revised_semantics_entries,
        resume_report_compatibility_entries=resume_report_compatibility_entries,
    ) as review_run_entries:
        snapshot = freeze_v1.build_checklist_freeze_snapshot(**dict(normalized))
    if binding is not None:
        runtime = snapshot.get("runtime_code_sha256")
        if not isinstance(runtime, Mapping):
            raise ContractLifecycleError("v1 snapshot runtime digest map is missing")
        rewritten_runtime = dict(runtime)
        files = binding["files"]
        assert isinstance(files, list)
        for raw_file in files:
            assert isinstance(raw_file, Mapping)
            declared_path = str(raw_file["declared_path"])
            if declared_path not in rewritten_runtime:
                raise ContractLifecycleError(
                    f"v1 runtime map does not bind lifecycle-code path {declared_path}"
                )
            rewritten_runtime.pop(declared_path)
            resolved_path = str(raw_file["resolved_path"])
            if resolved_path in rewritten_runtime:
                raise ContractLifecycleError(
                    f"lifecycle-code snapshot runtime path collides: {resolved_path}"
                )
            rewritten_runtime[resolved_path] = str(raw_file["locked_sha256"])
        snapshot["runtime_code_sha256"] = rewritten_runtime
        snapshot["lifecycle_code_snapshot"] = binding
        _recheck_lifecycle_code_snapshot_binding(binding)
    if derive_per_case_review_run:
        snapshot["per_case_review_runs"] = _per_case_review_run_binding(
            review_run_entries
        )
    if derive_review_attempt_state_machine:
        snapshot["review_attempt_state_machines"] = (
            _review_attempt_state_machine_binding(state_machine_entries)
        )
        _validate_review_attempt_state_machine_binding(
            snapshot["review_attempt_state_machines"]
        )
        snapshot["review_active_run_revised_semantics"] = (
            _review_revised_semantics_binding(revised_semantics_entries)
        )
        if len(resume_report_compatibility_entries) != 1:
            raise ContractLifecycleError(
                "draft resume-report compatibility binding is missing"
            )
        snapshot["review_resume_report_compatibility"] = dict(
            resume_report_compatibility_entries[0]
        )
    if derive_generation_attempt_state_machine:
        snapshot["generation_attempt_state_machines"] = (
            _generation_attempt_state_machine_binding(
                generation_state_machine_entries
            )
        )
        _validate_generation_attempt_state_machine_binding(
            snapshot["generation_attempt_state_machines"]
        )
    return snapshot


def _input_path(
    normalized: Mapping[str, Any], name: str, default: str | Path, label: str
) -> Path:
    return _require_regular_file(normalized.get(name, default), label)


def _input_directory(
    normalized: Mapping[str, Any], name: str, default: str | Path, label: str
) -> Path:
    root = _require_regular_directory(normalized.get(name, default), label)
    _audit_tree_file_safety(root, label)
    return root


def _validate_base_snapshot(base: Mapping[str, Any]) -> None:
    _assert_equal(
        base.get("schema_version"),
        freeze_v1.CHECKLIST_FREEZE_SCHEMA_VERSION,
        "validated v1 snapshot schema",
    )
    _assert_equal(
        base.get("expected_count"),
        freeze_v1.EXPECTED_CASE_COUNT,
        "validated v1 snapshot denominator",
    )
    expected_v1_counts = dict(_EXPECTED_COUNTS)
    expected_v1_counts.pop("accepted_drafts")
    _assert_equal(base.get("counts"), expected_v1_counts, "validated v1 counts")
    case_identity = base.get("case_identity")
    if not isinstance(case_identity, Mapping):
        raise ContractLifecycleError("validated v1 case identity is missing")
    _assert_equal(
        case_identity.get("suite_case_counts"),
        freeze_v1.EXPECTED_SUITE_COUNTS,
        "validated v1 suite counts",
    )
    lifecycle_snapshot = base.get("lifecycle_code_snapshot")
    if lifecycle_snapshot is not None:
        if not isinstance(lifecycle_snapshot, Mapping):
            raise ContractLifecycleError(
                "validated v1 lifecycle-code snapshot binding is malformed"
            )
        _recheck_lifecycle_code_snapshot_binding(lifecycle_snapshot)
    if base.get("per_case_review_runs") is not None:
        _recheck_per_case_review_runs(base)
    attempt_state_machines = base.get("review_attempt_state_machines")
    if attempt_state_machines is not None:
        if not isinstance(attempt_state_machines, Mapping):
            raise ContractLifecycleError(
                "validated v1 review-attempt state-machine binding is malformed"
            )
        _validate_review_attempt_state_machine_binding(attempt_state_machines)
    generation_state_machines = base.get("generation_attempt_state_machines")
    if generation_state_machines is not None:
        if not isinstance(generation_state_machines, Mapping):
            raise ContractLifecycleError(
                "validated v1 generation-attempt state-machine binding is malformed"
            )
        _validate_generation_attempt_state_machine_binding(
            generation_state_machines
        )
    revised_semantics = base.get("review_active_run_revised_semantics")
    if revised_semantics is not None:
        if not isinstance(revised_semantics, Mapping) or not isinstance(
            revised_semantics.get("entries"), list
        ):
            raise ContractLifecycleError(
                "validated v1 active-run revised-semantics binding is malformed"
            )
        _assert_equal(
            dict(revised_semantics),
            _review_revised_semantics_binding(revised_semantics["entries"]),
            "validated v1 active-run revised-semantics binding",
        )
    resume_compatibility = base.get("review_resume_report_compatibility")
    if resume_compatibility is not None:
        if not isinstance(resume_compatibility, Mapping):
            raise ContractLifecycleError(
                "validated v1 draft resume-report compatibility is malformed"
            )
        _validate_resume_report_compatibility(resume_compatibility)


def _current_path_binding(
    mapping: Mapping[str, Any], prefix: str, *, context: str
) -> dict[str, str]:
    path = _resolve_declared_path(mapping.get(f"{prefix}_path"), f"{context}.{prefix}")
    digest = sha256_file(path)
    _assert_equal(mapping.get(f"{prefix}_sha256"), digest, f"{context}.{prefix}_sha256")
    return {"path": _display(path), "sha256": digest}


def _index_file_binding(
    entry: Mapping[str, Any], prefix: str, *, case_unit_id: str
) -> dict[str, str]:
    path = _resolve_declared_path(
        entry.get(f"{prefix}_path"), f"{case_unit_id}.{prefix}_path"
    )
    digest = sha256_file(path)
    _assert_equal(
        entry.get(f"{prefix}_sha256"),
        digest,
        f"{case_unit_id}.{prefix}_sha256",
    )
    return {"path": _display(path), "sha256": digest}


def _review_round_bindings(
    *,
    case_unit_id: str,
    case_dir: Path,
    lifecycle: Mapping[str, Any],
    run_id: str,
    derive_review_attempt_state_machine: bool = False,
) -> tuple[list[dict[str, Any]], str, list[dict[str, str]]]:
    rounds = lifecycle.get("review_rounds")
    attempts = lifecycle.get("attempts")
    if not isinstance(rounds, int) or rounds < 1:
        raise ContractLifecycleError(f"{case_unit_id} has no accepted review rounds")
    if not isinstance(attempts, list) or len(attempts) != rounds:
        raise ContractLifecycleError(f"{case_unit_id} review attempt count differs")

    review_root = _require_regular_directory(
        case_dir / "review_attempts", f"{case_unit_id} review root"
    )
    active_root = _require_regular_directory(
        review_root / run_id, f"{case_unit_id} active review run"
    )
    round_bindings: list[dict[str, Any]] = []
    if derive_review_attempt_state_machine:
        previous_finished: datetime | None = None
        for expected_round, raw_attempt in enumerate(attempts, start=1):
            if not isinstance(raw_attempt, Mapping):
                raise ContractLifecycleError(
                    f"{case_unit_id} round {expected_round} receipt is malformed"
                )
            attempt = dict(raw_attempt)
            outcome = _classify_review_attempt(
                attempt, context=f"{case_unit_id} review attempt {expected_round}"
            )
            if expected_round == rounds:
                _assert_equal(
                    outcome,
                    "successful_accept",
                    f"{case_unit_id} final review outcome",
                )
            elif outcome == "successful_accept":
                raise ContractLifecycleError(
                    f"{case_unit_id} accepts before the final review attempt"
                )
            started = freeze_v1._parse_aware_timestamp(
                attempt.get("started_at"),
                f"{case_unit_id} round {expected_round}.started_at",
            )
            finished = freeze_v1._parse_aware_timestamp(
                attempt.get("finished_at"),
                f"{case_unit_id} round {expected_round}.finished_at",
            )
            if finished < started or (
                previous_finished is not None and started <= previous_finished
            ):
                raise ContractLifecycleError(
                    f"{case_unit_id} review-attempt time order differs"
                )
            previous_finished = finished
            round_bindings.append(
                _review_attempt_binding(
                    case_unit_id=case_unit_id,
                    active_root=active_root,
                    attempt=attempt,
                    position=expected_round,
                    outcome=outcome,
                )
            )
    else:
        for expected_round, raw_attempt in enumerate(attempts, start=1):
            if not isinstance(raw_attempt, Mapping):
                raise ContractLifecycleError(
                    f"{case_unit_id} round {expected_round} receipt is malformed"
                )
            attempt = dict(raw_attempt)
            _assert_equal(
                attempt.get("round"), expected_round, f"{case_unit_id} review round"
            )
            decision = attempt.get("decision")
            expected_decision = "accept" if expected_round == rounds else "revise"
            _assert_equal(
                decision,
                expected_decision,
                f"{case_unit_id} round {expected_round} decision",
            )
            prefix = f"round_{expected_round:02d}."
            artifact_paths = sorted(
                path for path in active_root.iterdir() if path.name.startswith(prefix)
            )
            if not artifact_paths:
                raise ContractLifecycleError(
                    f"{case_unit_id} round {expected_round} has no sidecars"
                )
            artifact_hashes: dict[str, str] = {}
            for artifact in artifact_paths:
                artifact = _require_regular_file(
                    artifact, f"{case_unit_id} round {expected_round} sidecar"
                )
                artifact_hashes[artifact.name] = sha256_file(artifact)
            revisions = {
                name: digest
                for name, digest in artifact_hashes.items()
                if name.endswith(".revised_checklist.yaml")
            }
            if expected_decision == "revise" and len(revisions) != 1:
                raise ContractLifecycleError(
                    f"{case_unit_id} round {expected_round} revision sidecar differs"
                )
            if expected_decision == "accept" and revisions:
                raise ContractLifecycleError(
                    f"{case_unit_id} accepted round contains a revision sidecar"
                )
            round_bindings.append(
                {
                    "round": expected_round,
                    "decision": expected_decision,
                    "attempt_receipt_sha256": sha256_object(attempt),
                    "input_checklist_sha256": attempt.get("input_checklist_sha256"),
                    "review_prompt_sha256": attempt.get("review_prompt_sha256"),
                    "model_review_sha256": attempt.get("model_review_sha256"),
                    "revision_checklist_sha256": next(
                        iter(revisions.values()), None
                    ),
                    "artifact_hashes": artifact_hashes,
                    "artifact_hashes_sha256": sha256_object(artifact_hashes),
                }
            )

    stale_runs: list[dict[str, str]] = []
    for path in sorted(item for item in review_root.iterdir() if item.is_dir()):
        if path.resolve() != active_root:
            stale_runs.append({"run_id": path.name, "tree_sha256": sha256_path(path)})
    return round_bindings, sha256_path(active_root), stale_runs


def _recheck_base_currentness(base: Mapping[str, Any]) -> None:
    inputs = base.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ContractLifecycleError("validated v1 snapshot inputs are missing")
    for name, raw_binding in inputs.items():
        if not isinstance(raw_binding, Mapping) or "path" not in raw_binding:
            continue
        path_value = raw_binding.get("path")
        if "sha256" in raw_binding:
            path = _resolve_declared_path(path_value, f"v1 input {name}")
            _assert_equal(
                sha256_file(path), raw_binding.get("sha256"), f"v1 input {name}"
            )
        elif "tree_sha256" in raw_binding:
            path = _require_regular_directory(path_value, f"v1 input tree {name}")
            _audit_tree_file_safety(path, f"v1 input tree {name}")
            _assert_equal(
                sha256_path(path),
                raw_binding.get("tree_sha256"),
                f"v1 input tree {name}",
            )

    runtime = base.get("runtime_code_sha256")
    if not isinstance(runtime, Mapping):
        raise ContractLifecycleError("validated v1 runtime digest map is missing")
    for raw_path, expected_hash in runtime.items():
        path = _require_regular_file(str(raw_path), f"v1 runtime input {raw_path}")
        _assert_equal(sha256_file(path), expected_hash, f"v1 runtime input {raw_path}")
    formal_output = base.get("formal_output_precondition")
    if not isinstance(formal_output, Mapping):
        raise ContractLifecycleError("validated v1 formal-output gate is missing")
    freeze_v1._recheck_empty_formal_outputs(formal_output)
    lifecycle_snapshot = base.get("lifecycle_code_snapshot")
    if lifecycle_snapshot is not None:
        if not isinstance(lifecycle_snapshot, Mapping):
            raise ContractLifecycleError(
                "validated v1 lifecycle-code snapshot binding is malformed"
            )
        _recheck_lifecycle_code_snapshot_binding(lifecycle_snapshot)
    if base.get("per_case_review_runs") is not None:
        _recheck_per_case_review_runs(base)
    attempt_state_machines = base.get("review_attempt_state_machines")
    if attempt_state_machines is not None:
        if not isinstance(attempt_state_machines, Mapping):
            raise ContractLifecycleError(
                "validated v1 review-attempt state-machine binding is malformed"
            )
        _validate_review_attempt_state_machine_binding(attempt_state_machines)
    generation_state_machines = base.get("generation_attempt_state_machines")
    if generation_state_machines is not None:
        if not isinstance(generation_state_machines, Mapping):
            raise ContractLifecycleError(
                "validated v1 generation-attempt state-machine binding is malformed"
            )
        _validate_generation_attempt_state_machine_binding(
            generation_state_machines
        )
    revised_semantics = base.get("review_active_run_revised_semantics")
    if revised_semantics is not None:
        if not isinstance(revised_semantics, Mapping) or not isinstance(
            revised_semantics.get("entries"), list
        ):
            raise ContractLifecycleError(
                "validated v1 active-run revised-semantics binding is malformed"
            )
        _assert_equal(
            dict(revised_semantics),
            _review_revised_semantics_binding(revised_semantics["entries"]),
            "validated v1 active-run revised-semantics binding",
        )
    resume_compatibility = base.get("review_resume_report_compatibility")
    if resume_compatibility is not None:
        if not isinstance(resume_compatibility, Mapping):
            raise ContractLifecycleError(
                "validated v1 draft resume-report compatibility is malformed"
            )
        _validate_resume_report_compatibility(resume_compatibility)


def post_lock_agentdojo_full_review_currentness(
    **snapshot_overrides: Any,
) -> dict[str, Any]:
    """Run the complete locked-checklist snapshot twice and reject input drift.

    Unlike the legacy review preflight, this gate deliberately requires the
    already-published 949-entry case lock and lock-acceptance receipt.  It also
    reuses the v1 full-snapshot validator, so formal result and score namespaces
    must still be empty before a draft tree can be sealed.
    """

    supplied = dict(snapshot_overrides)
    supplied.pop("review_quiescence_receipt_path", None)
    lifecycle_code_snapshot_root = supplied.pop("lifecycle_code_snapshot_root", None)
    derive_per_case_review_run = supplied.pop("derive_per_case_review_run", False)
    derive_review_attempt_state_machine = supplied.pop(
        "derive_review_attempt_state_machine", False
    )
    derive_generation_attempt_state_machine = supplied.pop(
        "derive_generation_attempt_state_machine", False
    )
    if not isinstance(derive_per_case_review_run, bool):
        raise ContractLifecycleError("derive_per_case_review_run must be boolean")
    if not isinstance(derive_review_attempt_state_machine, bool):
        raise ContractLifecycleError(
            "derive_review_attempt_state_machine must be boolean"
        )
    if not isinstance(derive_generation_attempt_state_machine, bool):
        raise ContractLifecycleError(
            "derive_generation_attempt_state_machine must be boolean"
        )
    normalized = _normalized_snapshot_overrides(supplied)
    first = _build_v1_snapshot(
        normalized=normalized,
        lifecycle_code_snapshot_root=lifecycle_code_snapshot_root,
        derive_per_case_review_run=derive_per_case_review_run,
        derive_review_attempt_state_machine=derive_review_attempt_state_machine,
        derive_generation_attempt_state_machine=(
            derive_generation_attempt_state_machine
        ),
    )
    _validate_base_snapshot(first)
    _recheck_base_currentness(first)
    second = _build_v1_snapshot(
        normalized=normalized,
        lifecycle_code_snapshot_root=lifecycle_code_snapshot_root,
        derive_per_case_review_run=derive_per_case_review_run,
        derive_review_attempt_state_machine=derive_review_attempt_state_machine,
        derive_generation_attempt_state_machine=(
            derive_generation_attempt_state_machine
        ),
    )
    _validate_base_snapshot(second)
    _recheck_base_currentness(second)
    if first != second:
        raise ContractLifecycleError(
            "post-lock checklist inputs changed between currentness validation passes"
        )
    return second


def _validate_definition(definition: Mapping[str, Any]) -> None:
    _assert_equal(
        definition.get("schema_version"),
        CHECKLIST_FREEZE_V2_DEFINITION_SCHEMA_VERSION,
        "v2 freeze definition schema",
    )
    _assert_equal(definition.get("freeze_id"), CHECKLIST_FREEZE_V2_ID, "v2 freeze id")
    for field, expected in (
        ("status", "accepted_for_immutable_freeze"),
        ("benchmark_version", freeze_v1.BENCHMARK_VERSION),
        ("attack", freeze_v1.ATTACK),
        ("defense", freeze_v1.DEFENSE),
    ):
        _assert_equal(definition.get(field), expected, f"v2 freeze {field}")
    _assert_equal(
        definition.get("expected_count"),
        freeze_v1.EXPECTED_CASE_COUNT,
        "v2 freeze denominator",
    )
    _assert_equal(definition.get("counts"), _EXPECTED_COUNTS, "v2 freeze counts")
    case_bindings = definition.get("case_bindings")
    if (
        not isinstance(case_bindings, list)
        or len(case_bindings) != freeze_v1.EXPECTED_CASE_COUNT
    ):
        raise ContractLifecycleError("v2 freeze requires exactly 949 case bindings")
    case_ids = [
        entry.get("case_unit_id") if isinstance(entry, Mapping) else None
        for entry in case_bindings
    ]
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ContractLifecycleError("v2 freeze contains a malformed case binding")
    if len(set(case_ids)) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("v2 freeze case IDs are not unique")
    if any(
        freeze_v1.CASE_ID_RE.fullmatch(str(case_id)) is None for case_id in case_ids
    ):
        raise ContractLifecycleError("v2 freeze contains a non-canonical case ID")

    prompt_schema_bindings = definition.get("prompt_schema_bindings")
    if not isinstance(prompt_schema_bindings, Mapping) or set(
        prompt_schema_bindings
    ) != set(_PROMPT_SCHEMA_PREFIXES):
        raise ContractLifecycleError("v2 freeze prompt/schema bindings are incomplete")
    _assert_equal(
        definition.get("prompt_schema_bindings_sha256"),
        sha256_object(prompt_schema_bindings),
        "v2 prompt/schema aggregate",
    )
    for prefix, binding in prompt_schema_bindings.items():
        _validate_digest_binding(binding, f"v2 prompt/schema {prefix}")

    validated_v1_for_attempts = definition.get("validated_v1_snapshot")
    if not isinstance(validated_v1_for_attempts, Mapping):
        raise ContractLifecycleError("v2 validated-v1 snapshot is missing")
    raw_attempt_state_machines = validated_v1_for_attempts.get(
        "review_attempt_state_machines"
    )
    attempt_state_by_case: dict[str, Mapping[str, Any]] = {}
    if raw_attempt_state_machines is not None:
        if not isinstance(raw_attempt_state_machines, Mapping):
            raise ContractLifecycleError(
                "v2 review-attempt state-machine binding is malformed"
            )
        _validate_review_attempt_state_machine_binding(raw_attempt_state_machines)
        raw_attempt_entries = raw_attempt_state_machines.get("entries")
        assert isinstance(raw_attempt_entries, list)
        attempt_state_by_case = {
            str(item["case_unit_id"]): item
            for item in raw_attempt_entries
            if isinstance(item, Mapping)
        }

    required_case_fields = {
        "position",
        "case_unit_id",
        "task_id",
        "suite",
        "case_packet",
        "raw_case_manifest",
        "generated_checklist",
        "generation_receipt",
        "final_checklist",
        "final_checklist_json",
        "review_receipt",
        "review_lifecycle_receipt",
        "prompt_schema_bindings",
        "prompt_schema_bindings_sha256",
        "review_revision_receipts",
        "review_revision_receipts_sha256",
        "batch_acceptance_case_sha256",
        "case_lock_entry_sha256",
        "case_lock_line_sha256",
    }
    for position, raw_entry in enumerate(case_bindings):
        assert isinstance(raw_entry, Mapping)
        entry = dict(raw_entry)
        _assert_equal(set(entry), required_case_fields, "v2 per-case binding fields")
        _assert_equal(entry.get("position"), position, "v2 per-case position")
        task_id = entry.get("task_id")
        suite = entry.get("suite")
        if not isinstance(task_id, str) or not task_id:
            raise ContractLifecycleError("v2 per-case task_id is missing")
        if not isinstance(suite, str) or suite not in freeze_v1.EXPECTED_SUITE_COUNTS:
            raise ContractLifecycleError("v2 per-case suite is invalid")
        for field in (
            "case_packet",
            "raw_case_manifest",
            "generated_checklist",
            "generation_receipt",
            "final_checklist",
            "final_checklist_json",
            "review_receipt",
            "review_lifecycle_receipt",
        ):
            _validate_digest_binding(entry.get(field), f"v2 per-case {field}")
        _assert_equal(
            entry.get("prompt_schema_bindings"),
            prompt_schema_bindings,
            "v2 per-case prompt/schema bindings",
        )
        _assert_equal(
            entry.get("prompt_schema_bindings_sha256"),
            definition.get("prompt_schema_bindings_sha256"),
            "v2 per-case prompt/schema digest",
        )
        receipts = entry.get("review_revision_receipts")
        if not isinstance(receipts, Mapping):
            raise ContractLifecycleError(
                "v2 review/revision receipt binding is missing"
            )
        _assert_equal(
            entry.get("review_revision_receipts_sha256"),
            sha256_object(receipts),
            "v2 review/revision receipt digest",
        )
        actual_review_run_id = receipts.get("actual_review_run_id")
        if actual_review_run_id is not None and (
            not isinstance(actual_review_run_id, str)
            or _CANONICAL_REVIEW_RUN_ID_RE.fullmatch(actual_review_run_id) is None
        ):
            raise ContractLifecycleError("v2 actual review-run ID is invalid")
        rounds = receipts.get("review_rounds")
        if not isinstance(rounds, list) or not rounds:
            raise ContractLifecycleError("v2 review/revision rounds are missing")
        case_unit_id = str(entry["case_unit_id"])
        if attempt_state_by_case:
            state_entry = attempt_state_by_case.get(case_unit_id)
            if state_entry is None:
                raise ContractLifecycleError(
                    f"v2 review-attempt state-machine case is missing: {case_unit_id}"
                )
            _assert_equal(
                rounds,
                state_entry.get("attempts"),
                "v2 review-attempt state-machine rounds",
            )
            _assert_equal(
                receipts.get("review_attempt_state_machine_sha256"),
                sha256_object(state_entry),
                "v2 review-attempt state-machine digest",
            )
        else:
            for round_position, round_binding in enumerate(rounds, start=1):
                if not isinstance(round_binding, Mapping):
                    raise ContractLifecycleError(
                        "v2 review/revision round is malformed"
                    )
                _assert_equal(
                    round_binding.get("round"),
                    round_position,
                    "v2 review round order",
                )
                expected_decision = (
                    "accept" if round_position == len(rounds) else "revise"
                )
                _assert_equal(
                    round_binding.get("decision"),
                    expected_decision,
                    "v2 review decision chain",
                )
                for field in (
                    "attempt_receipt_sha256",
                    "input_checklist_sha256",
                    "review_prompt_sha256",
                    "model_review_sha256",
                ):
                    _require_sha256(
                        round_binding.get(field), f"v2 review round {field}"
                    )
                revision_hash = round_binding.get("revision_checklist_sha256")
                if expected_decision == "revise":
                    _require_sha256(revision_hash, "v2 review revision checklist")
                elif revision_hash is not None:
                    raise ContractLifecycleError(
                        "v2 accepted review round must not bind a revision checklist"
                    )
                artifacts = round_binding.get("artifact_hashes")
                if not isinstance(artifacts, Mapping) or not artifacts:
                    raise ContractLifecycleError(
                        "v2 review artifact hash map is missing"
                    )
                for digest in artifacts.values():
                    _require_sha256(digest, "v2 review artifact")
                _assert_equal(
                    round_binding.get("artifact_hashes_sha256"),
                    sha256_object(artifacts),
                    "v2 review artifact aggregate",
                )
        for field in (
            "review_receipt_sha256",
            "review_lifecycle_receipt_sha256",
            "review_lifecycle_object_sha256",
            "active_review_tree_sha256",
        ):
            _require_sha256(receipts.get(field), f"v2 receipt {field}")
        for field in (
            "review_revision_receipts_sha256",
            "batch_acceptance_case_sha256",
            "case_lock_entry_sha256",
            "case_lock_line_sha256",
        ):
            _require_sha256(entry.get(field), f"v2 per-case {field}")
        stale_runs = receipts.get("stale_review_runs")
        if not isinstance(stale_runs, list):
            raise ContractLifecycleError("v2 stale review-run index is malformed")
        for stale in stale_runs:
            if (
                not isinstance(stale, Mapping)
                or not isinstance(stale.get("run_id"), str)
                or not stale.get("run_id")
            ):
                raise ContractLifecycleError("v2 stale review-run binding is malformed")
            _require_sha256(stale.get("tree_sha256"), "v2 stale review-run tree")

    observed_suite_counts = Counter(str(entry["suite"]) for entry in case_bindings)
    _assert_equal(
        dict(observed_suite_counts),
        freeze_v1.EXPECTED_SUITE_COUNTS,
        "v2 per-case suite denominator",
    )

    case_identity = definition.get("case_identity")
    if not isinstance(case_identity, Mapping):
        raise ContractLifecycleError("v2 case identity is missing")
    _assert_equal(
        case_identity.get("suite_case_counts"),
        freeze_v1.EXPECTED_SUITE_COUNTS,
        "v2 case identity suite denominator",
    )
    validated_v1 = validated_v1_for_attempts
    if not isinstance(validated_v1, Mapping):
        raise ContractLifecycleError("v2 validated-v1 snapshot is missing")
    _validate_base_snapshot(validated_v1)
    _assert_equal(
        definition.get("validated_v1_snapshot_sha256"),
        sha256_object(validated_v1),
        "v2 validated-v1 snapshot digest",
    )
    per_case_review_runs = validated_v1.get("per_case_review_runs")
    if per_case_review_runs is not None:
        assert isinstance(per_case_review_runs, Mapping)
        run_entries = per_case_review_runs.get("entries")
        assert isinstance(run_entries, list)
        _assert_equal(
            [entry.get("case_unit_id") for entry in run_entries],
            [entry.get("case_unit_id") for entry in case_bindings],
            "v2 derived review-run/case order",
        )
        for case_binding, run_entry in zip(case_bindings, run_entries):
            assert isinstance(case_binding, Mapping)
            assert isinstance(run_entry, Mapping)
            receipts = case_binding.get("review_revision_receipts")
            assert isinstance(receipts, Mapping)
            _assert_equal(
                receipts.get("actual_review_run_id"),
                run_entry.get("actual_run_id"),
                "v2 derived review-run ID binding",
            )
            _assert_equal(
                receipts.get("active_review_tree_sha256"),
                run_entry.get("tree_sha256"),
                "v2 derived review-run tree binding",
            )
    elif any(
        isinstance(entry.get("review_revision_receipts"), Mapping)
        and "actual_review_run_id" in entry["review_revision_receipts"]
        for entry in case_bindings
    ):
        raise ContractLifecycleError(
            "v2 case binding has an unbound derived review-run ID"
        )
    attempt_state_machines = validated_v1.get("review_attempt_state_machines")
    if attempt_state_machines is not None:
        assert isinstance(attempt_state_machines, Mapping)
        attempt_entries = attempt_state_machines.get("entries")
        assert isinstance(attempt_entries, list)
        _assert_equal(
            [entry.get("case_unit_id") for entry in attempt_entries],
            [entry.get("case_unit_id") for entry in case_bindings],
            "v2 review-attempt state-machine/case order",
        )
    elif any(
        isinstance(entry.get("review_revision_receipts"), Mapping)
        and "review_attempt_state_machine_sha256"
        in entry["review_revision_receipts"]
        for entry in case_bindings
    ):
        raise ContractLifecycleError(
            "v2 case binding has an unbound review-attempt state machine"
        )
    generation_state_machines = validated_v1.get(
        "generation_attempt_state_machines"
    )
    if generation_state_machines is not None:
        assert isinstance(generation_state_machines, Mapping)
        generation_entries = generation_state_machines.get("entries")
        assert isinstance(generation_entries, list)
        _assert_equal(
            [entry.get("case_unit_id") for entry in generation_entries],
            [entry.get("case_unit_id") for entry in case_bindings],
            "v2 generation-attempt state-machine/case order",
        )
    publisher_code = definition.get("publisher_code_sha256")
    if not isinstance(publisher_code, Mapping) or set(publisher_code) != set(
        _V2_CODE_PATHS
    ):
        raise ContractLifecycleError("v2 publisher code digest map is incomplete")
    for digest in publisher_code.values():
        _require_sha256(digest, "v2 publisher code")
    quiescence = definition.get("review_quiescence_receipt")
    legacy_quiescence_fields = {
        "path",
        "sha256",
        "created_at",
        "capture_session_id",
        "host_session",
        "draft_tree_sha256",
    }
    post_lock_quiescence_fields = legacy_quiescence_fields | {
        "currentness_gate_mode",
        "currentness_gate_sha256",
    }
    snapshot_quiescence_fields = post_lock_quiescence_fields | {
        "lifecycle_code_snapshot_root",
        "lifecycle_code_snapshot_tree_sha256",
    }
    if not isinstance(quiescence, Mapping):
        raise ContractLifecycleError("v2 review quiescence binding is incomplete")
    quiescence_fields = frozenset(quiescence)
    if quiescence_fields not in {
        frozenset(legacy_quiescence_fields),
        frozenset(post_lock_quiescence_fields),
        frozenset(snapshot_quiescence_fields),
    }:
        raise ContractLifecycleError("v2 review quiescence binding is incomplete")
    _validate_digest_binding(quiescence, "v2 review quiescence receipt")
    _aware_timestamp(quiescence.get("created_at"), "v2 quiescence created_at")
    capture_session_id = quiescence.get("capture_session_id")
    if (
        not isinstance(capture_session_id, str)
        or len(capture_session_id) != 32
        or any(character not in "0123456789abcdef" for character in capture_session_id)
    ):
        raise ContractLifecycleError("v2 quiescence capture session is invalid")
    host_session = quiescence.get("host_session")
    if not isinstance(host_session, Mapping) or set(host_session) != {
        "hostname",
        "boot_id",
        "hostname_sha256",
        "boot_id_sha256",
    }:
        raise ContractLifecycleError("v2 quiescence host session is malformed")
    for field in ("hostname", "boot_id"):
        if not isinstance(host_session.get(field), str) or not host_session.get(field):
            raise ContractLifecycleError(f"v2 quiescence host {field} is missing")
    for field in ("hostname_sha256", "boot_id_sha256"):
        _require_sha256(host_session.get(field), "v2 quiescence host session")
    _assert_equal(
        host_session.get("hostname_sha256"),
        sha256_object(host_session.get("hostname")),
        "v2 quiescence hostname hash",
    )
    _assert_equal(
        host_session.get("boot_id_sha256"),
        sha256_object(host_session.get("boot_id")),
        "v2 quiescence boot-id hash",
    )
    _require_sha256(quiescence.get("draft_tree_sha256"), "v2 quiescence draft tree")
    if quiescence_fields in {
        frozenset(post_lock_quiescence_fields),
        frozenset(snapshot_quiescence_fields),
    }:
        _assert_equal(
            quiescence.get("currentness_gate_mode"),
            CHECKLIST_REVIEW_POST_LOCK_GATE_MODE,
            "v2 quiescence currentness-gate mode",
        )
        _require_sha256(
            quiescence.get("currentness_gate_sha256"),
            "v2 quiescence currentness-gate digest",
        )
    if quiescence_fields == frozenset(snapshot_quiescence_fields):
        lifecycle_snapshot = validated_v1.get("lifecycle_code_snapshot")
        if not isinstance(lifecycle_snapshot, Mapping) or not isinstance(
            lifecycle_snapshot.get("root"), Mapping
        ):
            raise ContractLifecycleError(
                "v2 validated-v1 lifecycle-code snapshot binding is missing"
            )
        lifecycle_root = lifecycle_snapshot["root"]
        _assert_equal(
            quiescence.get("lifecycle_code_snapshot_root"),
            lifecycle_root.get("path"),
            "v2 quiescence lifecycle-code snapshot root",
        )
        _assert_equal(
            quiescence.get("lifecycle_code_snapshot_tree_sha256"),
            lifecycle_root.get("tree_sha256"),
            "v2 quiescence lifecycle-code snapshot tree",
        )
        _require_sha256(
            quiescence.get("lifecycle_code_snapshot_tree_sha256"),
            "v2 quiescence lifecycle-code snapshot tree",
        )
    elif validated_v1.get("lifecycle_code_snapshot") is not None:
        raise ContractLifecycleError(
            "v2 quiescence omits the validated lifecycle-code snapshot binding"
        )
    validated_inputs = validated_v1.get("inputs")
    if not isinstance(validated_inputs, Mapping) or not isinstance(
        validated_inputs.get("draft_root"), Mapping
    ):
        raise ContractLifecycleError("v2 validated-v1 draft tree binding is missing")
    _assert_equal(
        quiescence.get("draft_tree_sha256"),
        validated_inputs["draft_root"].get("tree_sha256"),
        "v2 quiescence/v1 draft tree binding",
    )
    for field, expected_count_field in (
        ("batch_lock", "entry_count"),
        ("batch_lock_acceptance", "accepted_case_count"),
    ):
        binding = definition.get(field)
        _validate_digest_binding(binding, f"v2 {field}")
        assert isinstance(binding, Mapping)
        _assert_equal(
            binding.get(expected_count_field),
            freeze_v1.EXPECTED_CASE_COUNT,
            f"v2 {field} denominator",
        )
    aggregates = definition.get("aggregate_sha256")
    if not isinstance(aggregates, Mapping):
        raise ContractLifecycleError("v2 freeze aggregate hashes are missing")
    expected_aggregates = _aggregate_hashes(case_bindings)
    _assert_equal(aggregates, expected_aggregates, "v2 freeze aggregate hashes")
    _assert_equal(
        case_identity.get("case_id_order_sha256"),
        expected_aggregates["case_id_order_sha256"],
        "v2 case identity order",
    )
    _assert_equal(
        case_identity.get("case_id_set_sha256"),
        expected_aggregates["case_id_set_sha256"],
        "v2 case identity set",
    )


def _require_sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContractLifecycleError(f"{label} is not a lowercase SHA-256 digest")
    return value


def _validate_digest_binding(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractLifecycleError(f"{label} must be a path/hash mapping")
    path = value.get("path")
    if not isinstance(path, str) or not path:
        raise ContractLifecycleError(f"{label}.path is missing")
    _require_sha256(value.get("sha256"), f"{label}.sha256")


def _require_planned_destination_absent(value: str | Path, label: str) -> Path:
    path = _absolute_path(value)
    _reject_symlink_ancestors(path, label)
    if _lexists(path):
        raise ContractLifecycleError(
            f"{label} must be destination-absent before batch locking: {path}"
        )
    return path


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _current_host_session() -> dict[str, str]:
    """Return non-sensitive hashes that identify this host boot session."""

    hostname = socket.gethostname().strip()
    if not hostname:
        raise ContractLifecycleError("could not identify the checklist review host")
    boot_material: str | None = None
    linux_boot_id = Path("/proc/sys/kernel/random/boot_id")
    if linux_boot_id.is_file():
        boot_material = linux_boot_id.read_text(encoding="utf-8").strip()
    elif sys.platform == "darwin":
        completed = subprocess.run(
            ["sysctl", "-n", "kern.boottime"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            boot_material = completed.stdout.strip()
    else:
        completed = subprocess.run(
            ["ps", "-o", "lstart=", "-p", "1"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            boot_material = completed.stdout.strip()
    if not boot_material:
        raise ContractLifecycleError("could not identify the host boot session")
    return {
        "hostname": hostname,
        "boot_id": boot_material,
        "hostname_sha256": sha256_object(hostname),
        "boot_id_sha256": sha256_object(boot_material),
    }


def _review_process_snapshot_from_text(text: str) -> dict[str, Any]:
    matched: dict[str, set[int]] = {name: set() for name in _REVIEW_PROCESS_POLICY}
    records: list[tuple[int, int, str]] = []
    codex_exec_pattern = re.compile(r"(?:^|[/\s])codex(?:\s|$).*?\bexec\b", re.I)
    diagnostic_pattern = re.compile(r"(?:^|[/\s])(?:rg|grep|ps)(?:\s|$)", re.I)
    codex_review_markers = (
        "case-checklist-review",
        "case_checklist_review",
        "model_review",
        "review_agentdojo_full_checklist",
    )
    for raw_line in text.splitlines():
        parts = raw_line.strip().split(maxsplit=2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            parent_pid = int(parts[1])
        except ValueError:
            continue
        records.append((pid, parent_pid, parts[2]))

    parent_by_pid = {pid: parent for pid, parent, _command in records}
    excluded_pids = {os.getpid()}
    cursor = os.getpid()
    while cursor in parent_by_pid:
        cursor = parent_by_pid[cursor]
        if cursor <= 0 or cursor in excluded_pids:
            break
        excluded_pids.add(cursor)

    scanned = 0
    for pid, _parent_pid, command in records:
        if pid in excluded_pids or diagnostic_pattern.search(command):
            continue
        scanned += 1
        if "run_agentdojo_full_draft_review.py" in command:
            matched["run_agentdojo_full_draft_review.py"].add(pid)
        if "review_case_checklist_with_codex.py" in command:
            matched["review_case_checklist_with_codex.py"].add(pid)
        lowered = command.lower()
        if codex_exec_pattern.search(command) and any(
            marker in lowered for marker in codex_review_markers
        ):
            matched["codex_exec_case_checklist_review"].add(pid)
    counts = {name: len(pids) for name, pids in matched.items()}
    return {
        "policy": list(_REVIEW_PROCESS_POLICY),
        "command_pattern_sha256": _REVIEW_COMMAND_PATTERN_SHA256,
        "scanned_process_count": scanned,
        "matched_process_count": sum(len(pids) for pids in matched.values()),
        "matched_by_policy": counts,
    }


def _assert_review_process_quiescence() -> dict[str, Any]:
    completed = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ContractLifecycleError("could not capture the local review process table")
    snapshot = _review_process_snapshot_from_text(completed.stdout)
    if snapshot["matched_process_count"] != 0:
        raise ContractLifecycleError(
            "checklist review processes are not quiescent: "
            f"{snapshot['matched_by_policy']}"
        )
    return snapshot


def _seal_tree_read_only(root: Path) -> None:
    paths = sorted(root.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    if any(path.is_symlink() for path in paths):
        raise ContractLifecycleError("review draft tree contains symlinks")
    for path in (*paths, root):
        mode = path.stat().st_mode
        os.chmod(path, mode & ~0o222)


def _review_tree_inventory(
    *, draft_root: Path, expected_count: int = freeze_v1.EXPECTED_CASE_COUNT
) -> dict[str, Any]:
    paths = [draft_root, *draft_root.rglob("*")]
    symlinks = [path for path in paths if path.is_symlink()]
    if symlinks:
        raise ContractLifecycleError(
            f"review draft tree contains symlinks: {symlinks[:3]}"
        )
    multiply_linked = [
        path for path in paths if path.is_file() and os.lstat(path).st_nlink != 1
    ]
    if multiply_linked:
        raise ContractLifecycleError(
            "review draft tree contains multiply-linked files; "
            f"count={len(multiply_linked)}"
        )
    writable = [path for path in paths if path.stat().st_mode & 0o222]
    if writable:
        raise ContractLifecycleError(
            "review draft tree is not filesystem-read-only; "
            f"writable_entries={len(writable)}"
        )
    case_directories = sorted(path for path in draft_root.iterdir() if path.is_dir())
    checklist_files = sorted(draft_root.glob("*/checklist.yaml"))
    review_files = sorted(draft_root.glob("*/review.json"))
    lifecycle_files = sorted(draft_root.glob("*/review_lifecycle.json"))
    counts = {
        "case_directories": len(case_directories),
        "checklists": len(checklist_files),
        "reviews": len(review_files),
        "review_lifecycles": len(lifecycle_files),
    }
    _assert_equal(
        counts,
        {
            "case_directories": expected_count,
            "checklists": expected_count,
            "reviews": expected_count,
            "review_lifecycles": expected_count,
        },
        "review quiescence tree denominator",
    )
    return {
        **counts,
        "filesystem_read_only": True,
        "tree_sha256": sha256_path(draft_root),
    }


def capture_review_quiescence_receipt(
    *,
    output_path: str | Path,
    draft_root: str | Path = freeze_v1.DEFAULT_DRAFT_ROOT,
    lifecycle_report_path: str | Path = freeze_v1.DEFAULT_DRAFT_REVIEW_REPORT,
    lifecycle_index_path: str | Path = freeze_v1.DEFAULT_DRAFT_REVIEW_INDEX,
    seal_draft_tree_read_only: bool = False,
    review_preflight_receipt_path: str | Path | None = None,
    post_lock_currentness_seal: bool = False,
    post_lock_snapshot_overrides: Mapping[str, Any] | None = None,
    freeze_output_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
) -> Path:
    """Capture a destination-absent, machine-generated local quiescence receipt."""

    if post_lock_currentness_seal and not seal_draft_tree_read_only:
        raise ContractLifecycleError(
            "post-lock currentness is only valid with read-only tree sealing"
        )
    if post_lock_currentness_seal and review_preflight_receipt_path is not None:
        raise ContractLifecycleError(
            "post-lock sealing cannot also consume the legacy pre-lock receipt"
        )

    drafts = _require_regular_directory(draft_root, "review quiescence draft root")
    output = _absolute_path(output_path)
    _reject_symlink_ancestors(output, "review quiescence output")
    if _lexists(output):
        raise ContractLifecycleError(
            f"review quiescence destination already exists: {output}"
        )
    try:
        output.relative_to(drafts)
    except ValueError:
        pass
    else:
        raise ContractLifecycleError(
            "review quiescence receipt must be outside the frozen draft tree"
        )
    report_path = _require_regular_file(
        lifecycle_report_path, "review quiescence lifecycle report"
    )
    index_path = _require_regular_file(
        lifecycle_index_path, "review quiescence lifecycle index"
    )
    index = _load_json_mapping(index_path, "review quiescence lifecycle index")
    entries = index.get("entries")
    if not isinstance(entries, list) or len(entries) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            "review quiescence lifecycle index must contain exactly 949 entries"
        )
    if index.get("case_count") != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("review quiescence lifecycle index count differs")

    before = _assert_review_process_quiescence()
    currentness_gate: dict[str, Any] | None = None
    post_lock_snapshot: dict[str, Any] | None = None
    if seal_draft_tree_read_only:
        freeze_output = _absolute_path(freeze_output_path)
        if _lexists(freeze_output) or _lexists(
            checklist_freeze_v2_invalidation_path(freeze_output)
        ):
            raise ContractLifecycleError(
                "read-only sealing is forbidden after a freeze/invalidation exists"
            )
        if post_lock_currentness_seal:
            post_lock_snapshot = post_lock_agentdojo_full_review_currentness(
                **dict(post_lock_snapshot_overrides or {})
            )
            post_lock_inputs = post_lock_snapshot.get("inputs")
            if not isinstance(post_lock_inputs, Mapping):
                raise ContractLifecycleError(
                    "post-lock currentness snapshot inputs are missing"
                )
            snapshot_draft = post_lock_inputs.get("draft_root")
            if not isinstance(snapshot_draft, Mapping):
                raise ContractLifecycleError(
                    "post-lock currentness draft-root binding is missing"
                )
            _assert_equal(
                _require_regular_directory(
                    snapshot_draft.get("path"), "post-lock sealing draft root"
                ),
                drafts,
                "post-lock sealing draft root",
            )
            currentness_gate = {
                "mode": CHECKLIST_REVIEW_POST_LOCK_GATE_MODE,
                "snapshot_schema_version": freeze_v1.CHECKLIST_FREEZE_SCHEMA_VERSION,
                "snapshot_sha256": sha256_object(post_lock_snapshot),
            }
            lifecycle_snapshot = post_lock_snapshot.get("lifecycle_code_snapshot")
            if lifecycle_snapshot is not None:
                assert isinstance(lifecycle_snapshot, Mapping)
                lifecycle_root = lifecycle_snapshot.get("root")
                assert isinstance(lifecycle_root, Mapping)
                currentness_gate.update(
                    {
                        "lifecycle_code_snapshot_root": lifecycle_root["path"],
                        "lifecycle_code_snapshot_tree_sha256": lifecycle_root[
                            "tree_sha256"
                        ],
                    }
                )
        else:
            if review_preflight_receipt_path is None:
                raise ContractLifecycleError(
                    "read-only sealing requires a passed review preflight receipt"
                )
            preflight = verify_review_currentness_preflight_receipt(
                receipt_path=review_preflight_receipt_path,
                require_planned_outputs_absent=True,
            )
            preflight_inputs = preflight.get("inputs")
            assert isinstance(preflight_inputs, Mapping)
            _assert_equal(
                _require_regular_directory(
                    preflight_inputs.get("draft_root"), "sealing preflight draft root"
                ),
                drafts,
                "sealing preflight draft root",
            )
        _seal_tree_read_only(drafts)
    inventory = _review_tree_inventory(draft_root=drafts)
    report_hash = sha256_file(report_path)
    index_hash = sha256_file(index_path)
    if post_lock_snapshot is not None:
        post_lock_inputs = post_lock_snapshot["inputs"]
        assert isinstance(post_lock_inputs, Mapping)
        for input_name, expected_path, expected_hash, hash_field in (
            ("draft_root", drafts, inventory["tree_sha256"], "tree_sha256"),
            ("draft_review_report", report_path, report_hash, "sha256"),
            ("draft_review_index", index_path, index_hash, "sha256"),
        ):
            binding = post_lock_inputs.get(input_name)
            if not isinstance(binding, Mapping):
                raise ContractLifecycleError(
                    f"post-lock currentness {input_name} binding is missing"
                )
            current_path = (
                _require_regular_directory(
                    binding.get("path"), f"post-lock currentness {input_name}"
                )
                if hash_field == "tree_sha256"
                else _resolve_declared_path(
                    binding.get("path"), f"post-lock currentness {input_name}"
                )
            )
            _assert_equal(
                current_path,
                expected_path,
                f"post-lock currentness {input_name} path",
            )
            _assert_equal(
                binding.get(hash_field),
                expected_hash,
                f"post-lock currentness {input_name} hash",
            )
        _recheck_base_currentness(post_lock_snapshot)
    after = _assert_review_process_quiescence()
    receipt = {
        "schema_version": (
            CHECKLIST_REVIEW_POST_LOCK_QUIESCENCE_SCHEMA_VERSION
            if currentness_gate is not None
            else CHECKLIST_REVIEW_QUIESCENCE_SCHEMA_VERSION
        ),
        "status": "quiescent",
        "created_at": _utc_now().replace(microsecond=0).isoformat(),
        "capture_session_id": uuid.uuid4().hex,
        "host_session": _current_host_session(),
        "process_observations": {"before": before, "after": after},
        "draft_root": {
            "path": _display(drafts),
            "tree_sha256": inventory["tree_sha256"],
            "filesystem_read_only": True,
        },
        "tree_inventory": inventory,
        "lifecycle_report": {
            "path": _display(report_path),
            "sha256": report_hash,
        },
        "lifecycle_index": {
            "path": _display(index_path),
            "sha256": index_hash,
            "case_count": freeze_v1.EXPECTED_CASE_COUNT,
        },
    }
    if currentness_gate is not None:
        receipt["currentness_gate"] = currentness_gate
    _exclusive_publish_json(output, receipt)
    return output.resolve()


def verify_review_quiescence_receipt(
    *,
    receipt_path: str | Path,
    max_age_seconds: int | None = DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    expected_draft_tree_sha256: str | None = None,
    require_process_quiescence: bool = True,
    post_lock_snapshot_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify receipt integrity, freshness, host session, tree, and live processes."""

    receipt_file = _require_regular_file(receipt_path, "review quiescence receipt")
    receipt = _load_json_mapping(receipt_file, "review quiescence receipt")
    schema_version = receipt.get("schema_version")
    if schema_version not in {
        CHECKLIST_REVIEW_QUIESCENCE_SCHEMA_VERSION,
        CHECKLIST_REVIEW_POST_LOCK_QUIESCENCE_SCHEMA_VERSION,
    }:
        raise ContractLifecycleError(
            f"review quiescence schema differs: actual={schema_version!r}"
        )
    post_lock_gate = (
        schema_version == CHECKLIST_REVIEW_POST_LOCK_QUIESCENCE_SCHEMA_VERSION
    )
    expected_fields = {
        "schema_version",
        "status",
        "created_at",
        "capture_session_id",
        "host_session",
        "process_observations",
        "draft_root",
        "tree_inventory",
        "lifecycle_report",
        "lifecycle_index",
    }
    if post_lock_gate:
        expected_fields.add("currentness_gate")
    _assert_equal(set(receipt), expected_fields, "review quiescence receipt fields")
    _assert_equal(receipt.get("status"), "quiescent", "review quiescence status")
    session_id = receipt.get("capture_session_id")
    if (
        not isinstance(session_id, str)
        or len(session_id) != 32
        or any(character not in "0123456789abcdef" for character in session_id)
    ):
        raise ContractLifecycleError("review quiescence capture_session_id is invalid")
    captured_text = _aware_timestamp(receipt.get("created_at"), "quiescence.created_at")
    captured = datetime.fromisoformat(captured_text.replace("Z", "+00:00"))
    now = _utc_now()
    if (
        captured > now.replace(microsecond=now.microsecond)
        and (captured - now).total_seconds() > 5
    ):
        raise ContractLifecycleError("review quiescence receipt is from the future")
    if max_age_seconds is not None:
        if not isinstance(max_age_seconds, int) or max_age_seconds <= 0:
            raise ContractLifecycleError("quiescence max age must be positive")
        if (now - captured).total_seconds() > max_age_seconds:
            raise ContractLifecycleError("review quiescence receipt is stale")
    _assert_equal(
        receipt.get("host_session"),
        _current_host_session(),
        "review quiescence host/boot session",
    )
    observations = receipt.get("process_observations")
    if not isinstance(observations, Mapping) or set(observations) != {
        "before",
        "after",
    }:
        raise ContractLifecycleError(
            "review quiescence process observations are missing"
        )
    for phase, snapshot in observations.items():
        if not isinstance(snapshot, Mapping):
            raise ContractLifecycleError(
                f"review quiescence {phase} process snapshot is malformed"
            )
        _assert_equal(
            snapshot.get("policy"),
            list(_REVIEW_PROCESS_POLICY),
            f"review quiescence {phase} process policy",
        )
        _assert_equal(
            snapshot.get("command_pattern_sha256"),
            _REVIEW_COMMAND_PATTERN_SHA256,
            f"review quiescence {phase} command-pattern hash",
        )
        _assert_equal(
            snapshot.get("matched_process_count"),
            0,
            f"review quiescence {phase} process count",
        )
        _assert_equal(
            snapshot.get("matched_by_policy"),
            {name: 0 for name in _REVIEW_PROCESS_POLICY},
            f"review quiescence {phase} process classes",
        )

    draft_binding = receipt.get("draft_root")
    if not isinstance(draft_binding, Mapping):
        raise ContractLifecycleError("review quiescence draft binding is missing")
    drafts = _require_regular_directory(
        draft_binding.get("path"), "review quiescence draft root"
    )
    _assert_equal(
        draft_binding.get("filesystem_read_only"),
        True,
        "review quiescence read-only flag",
    )
    inventory = _review_tree_inventory(draft_root=drafts)
    _assert_equal(receipt.get("tree_inventory"), inventory, "review tree inventory")
    _assert_equal(
        draft_binding.get("tree_sha256"),
        inventory["tree_sha256"],
        "review quiescence draft tree hash",
    )
    if expected_draft_tree_sha256 is not None:
        _assert_equal(
            inventory["tree_sha256"],
            expected_draft_tree_sha256,
            "review quiescence expected draft tree",
        )
    for field in ("lifecycle_report", "lifecycle_index"):
        binding = receipt.get(field)
        if not isinstance(binding, Mapping):
            raise ContractLifecycleError(f"review quiescence {field} is missing")
        path = _resolve_declared_path(binding.get("path"), f"quiescence {field}")
        _assert_equal(
            binding.get("sha256"), sha256_file(path), f"quiescence {field} hash"
        )
    index_binding = receipt["lifecycle_index"]
    assert isinstance(index_binding, Mapping)
    _assert_equal(
        index_binding.get("case_count"),
        freeze_v1.EXPECTED_CASE_COUNT,
        "quiescence lifecycle-index denominator",
    )
    if require_process_quiescence:
        _assert_review_process_quiescence()
    gate_binding: dict[str, str] = {}
    if post_lock_gate:
        raw_gate = receipt.get("currentness_gate")
        base_gate_fields = {
            "mode",
            "snapshot_schema_version",
            "snapshot_sha256",
        }
        snapshot_gate_fields = base_gate_fields | {
            "lifecycle_code_snapshot_root",
            "lifecycle_code_snapshot_tree_sha256",
        }
        if not isinstance(raw_gate, Mapping) or set(raw_gate) not in (
            base_gate_fields,
            snapshot_gate_fields,
        ):
            raise ContractLifecycleError(
                "post-lock quiescence currentness gate is malformed"
            )
        _assert_equal(
            raw_gate.get("mode"),
            CHECKLIST_REVIEW_POST_LOCK_GATE_MODE,
            "post-lock quiescence gate mode",
        )
        _assert_equal(
            raw_gate.get("snapshot_schema_version"),
            freeze_v1.CHECKLIST_FREEZE_SCHEMA_VERSION,
            "post-lock quiescence snapshot schema",
        )
        gate_sha256 = _require_sha256(
            raw_gate.get("snapshot_sha256"), "post-lock quiescence snapshot"
        )
        if post_lock_snapshot_overrides is None:
            raise ContractLifecycleError(
                "post-lock quiescence verification requires full snapshot inputs"
            )
        current_snapshot = post_lock_agentdojo_full_review_currentness(
            **dict(post_lock_snapshot_overrides)
        )
        _assert_equal(
            sha256_object(current_snapshot),
            gate_sha256,
            "post-lock quiescence currentness gate digest",
        )
        current_inputs = current_snapshot.get("inputs")
        if not isinstance(current_inputs, Mapping) or not isinstance(
            current_inputs.get("draft_root"), Mapping
        ):
            raise ContractLifecycleError(
                "post-lock quiescence current draft binding is missing"
            )
        _assert_equal(
            current_inputs["draft_root"].get("tree_sha256"),
            inventory["tree_sha256"],
            "post-lock quiescence current draft tree",
        )
        gate_binding = {
            "currentness_gate_mode": CHECKLIST_REVIEW_POST_LOCK_GATE_MODE,
            "currentness_gate_sha256": gate_sha256,
        }
        if set(raw_gate) == snapshot_gate_fields:
            lifecycle_snapshot = current_snapshot.get("lifecycle_code_snapshot")
            if not isinstance(lifecycle_snapshot, Mapping) or not isinstance(
                lifecycle_snapshot.get("root"), Mapping
            ):
                raise ContractLifecycleError(
                    "post-lock quiescence lifecycle-code snapshot is missing"
                )
            lifecycle_root = lifecycle_snapshot["root"]
            _assert_equal(
                raw_gate.get("lifecycle_code_snapshot_root"),
                lifecycle_root.get("path"),
                "post-lock quiescence lifecycle-code snapshot root",
            )
            _assert_equal(
                raw_gate.get("lifecycle_code_snapshot_tree_sha256"),
                lifecycle_root.get("tree_sha256"),
                "post-lock quiescence lifecycle-code snapshot tree",
            )
            gate_binding.update(
                {
                    "lifecycle_code_snapshot_root": str(lifecycle_root["path"]),
                    "lifecycle_code_snapshot_tree_sha256": str(
                        lifecycle_root["tree_sha256"]
                    ),
                }
            )
        elif current_snapshot.get("lifecycle_code_snapshot") is not None:
            raise ContractLifecycleError(
                "post-lock quiescence receipt omits lifecycle-code snapshot binding"
            )
    return {
        "path": _display(receipt_file),
        "sha256": sha256_file(receipt_file),
        "created_at": captured_text,
        "capture_session_id": session_id,
        "host_session": dict(receipt["host_session"]),
        "draft_tree_sha256": inventory["tree_sha256"],
        **gate_binding,
    }


def _validate_preflight_lifecycle_acceptance(
    *,
    case_unit_id: str,
    lifecycle: Mapping[str, Any],
    final_checklist_sha256: str,
    final_review_sha256: str,
) -> None:
    """Reject a model-level accept unless the deterministic lifecycle accepted it."""

    for field, expected in (
        ("schema_version", "case_checklist_review_lifecycle/v1"),
        ("case_unit_id", case_unit_id),
        ("status", "accepted"),
        ("final_checklist_sha256", final_checklist_sha256),
        ("final_review_sha256", final_review_sha256),
    ):
        _assert_equal(
            lifecycle.get(field),
            expected,
            f"preflight lifecycle {case_unit_id}.{field}",
        )
    rounds = lifecycle.get("review_rounds")
    attempts = lifecycle.get("attempts")
    if not isinstance(rounds, int) or rounds < 1:
        raise ContractLifecycleError(
            f"preflight lifecycle has no accepted round: {case_unit_id}"
        )
    if not isinstance(attempts, list) or len(attempts) != rounds:
        raise ContractLifecycleError(
            f"preflight lifecycle attempt denominator differs: {case_unit_id}"
        )
    decisions: list[str] = []
    for position, raw_attempt in enumerate(attempts, start=1):
        if not isinstance(raw_attempt, Mapping):
            raise ContractLifecycleError(
                f"preflight lifecycle round {position} is malformed: {case_unit_id}"
            )
        if "error" in raw_attempt or "revision_validation_error" in raw_attempt:
            raise ContractLifecycleError(
                f"preflight lifecycle contains an unresolved round: {case_unit_id}"
            )
        _assert_equal(
            raw_attempt.get("round"),
            position,
            f"preflight lifecycle round {case_unit_id}",
        )
        expected_decision = "accept" if position == rounds else "revise"
        _assert_equal(
            raw_attempt.get("decision"),
            expected_decision,
            f"preflight lifecycle decision chain {case_unit_id}",
        )
        deterministic = raw_attempt.get("deterministic_review")
        if expected_decision == "accept":
            _assert_equal(
                deterministic,
                {"status": "pass", "findings": []},
                f"preflight accepted deterministic review {case_unit_id}",
            )
        decisions.append(expected_decision)
    revised = lifecycle.get("revised")
    if not isinstance(revised, bool):
        raise ContractLifecycleError(
            f"preflight lifecycle revised flag is malformed: {case_unit_id}"
        )
    _assert_equal(
        revised,
        "revise" in decisions,
        f"preflight lifecycle revised/decision equivalence {case_unit_id}",
    )


def _preflight_input_lock_time(
    *,
    input_lock_path: Path,
    manifest_path: Path,
    source_bundle_path: Path,
    config_path: Path,
    packet_root: Path,
    case_ids: Sequence[str],
) -> Any:
    input_lock = _load_json_mapping(input_lock_path, "draft input lock")
    _assert_equal(
        input_lock.get("schema_version"),
        "agentdojo_draft_input_lock/v1",
        "preflight input-lock schema",
    )
    _assert_equal(
        input_lock.get("case_count"),
        freeze_v1.EXPECTED_CASE_COUNT,
        "preflight input-lock denominator",
    )
    from neurips_ed_track_minimal.scripts import update_case_locks_batch as batch

    _assert_equal(
        input_lock.get("case_id_order_sha256"),
        batch._sha256_object(list(case_ids)),
        "preflight input-lock case order",
    )
    _assert_equal(
        input_lock.get("case_id_set_sha256"),
        batch._sha256_object(sorted(case_ids)),
        "preflight input-lock case set",
    )
    for field, expected_path in (
        ("manifest", manifest_path),
        ("source_bundle", source_bundle_path),
        ("resolved_config", config_path),
    ):
        binding = input_lock.get(field)
        if not isinstance(binding, Mapping):
            raise ContractLifecycleError(f"preflight input-lock {field} is missing")
        path = _resolve_declared_path(binding.get("path"), f"input-lock {field}")
        _assert_equal(path, expected_path, f"preflight input-lock {field} path")
        _assert_equal(
            binding.get("sha256"),
            sha256_file(expected_path),
            f"preflight input-lock {field} hash",
        )
    declared_packet_root = freeze_v1._resolve_declared_artifact_path(
        input_lock.get("case_packet_root"), "preflight input-lock packet root"
    )
    _assert_equal(declared_packet_root, packet_root, "preflight input-lock packet root")
    return freeze_v1._parse_aware_timestamp(
        input_lock.get("locked_at"), "preflight input-lock locked_at"
    )


def build_review_currentness_preflight(**snapshot_overrides: Any) -> dict[str, Any]:
    """Read-only 949-case review gate that runs before the legacy batch locker."""

    from neurips_ed_track_minimal.scripts import update_case_locks_batch as batch
    from neurips_ed_track_minimal.scripts.case_checklist_review import (
        review_agentdojo_checklist,
    )

    normalized = dict(snapshot_overrides)
    supplied_count = normalized.pop("expected_count", freeze_v1.EXPECTED_CASE_COUNT)
    if supplied_count != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("review preflight denominator is fixed at 949")
    manifest_path = _input_path(
        normalized, "manifest_path", freeze_v1.DEFAULT_MANIFEST, "preflight manifest"
    )
    source_bundle_path = _input_path(
        normalized,
        "source_bundle_path",
        freeze_v1.DEFAULT_SOURCE_BUNDLE,
        "preflight source bundle",
    )
    packet_root = _input_directory(
        normalized,
        "case_packet_root",
        freeze_v1.DEFAULT_CASE_PACKETS / "agentdojo",
        "preflight case-packet root",
    )
    draft_root = _input_directory(
        normalized, "draft_root", freeze_v1.DEFAULT_DRAFT_ROOT, "preflight draft root"
    )
    config_path = _input_path(
        normalized,
        "resolved_config_path",
        freeze_v1.DEFAULT_DRAFT_REVIEW_CONFIG,
        "preflight review config",
    )
    input_lock_path = _input_path(
        normalized,
        "input_lock_path",
        freeze_v1.DEFAULT_DRAFT_INPUT_LOCK,
        "preflight input lock",
    )
    report_path = _input_path(
        normalized,
        "lifecycle_report_path",
        freeze_v1.DEFAULT_DRAFT_REVIEW_REPORT,
        "preflight lifecycle report",
    )
    index_path = _input_path(
        normalized,
        "lifecycle_index_path",
        freeze_v1.DEFAULT_DRAFT_REVIEW_INDEX,
        "preflight lifecycle index",
    )
    score_prompt_path = _input_path(
        normalized,
        "score_prompt_path",
        freeze_v1.DEFAULT_SCORE_PROMPT,
        "preflight score prompt",
    )
    score_schema_path = _input_path(
        normalized,
        "score_schema_path",
        freeze_v1.DEFAULT_SCORE_SCHEMA,
        "preflight score schema",
    )
    planned_case_lock = _require_planned_destination_absent(
        normalized.get("case_lock_path", freeze_v1.DEFAULT_CASE_CHECKLIST_LOCK),
        "planned case-lock output",
    )
    planned_acceptance = _require_planned_destination_absent(
        normalized.get(
            "lock_acceptance_path", freeze_v1.DEFAULT_CASE_CHECKLIST_LOCK_ACCEPTANCE
        ),
        "planned case-lock acceptance output",
    )

    try:
        manifest, cases = batch._load_manifest_cases(
            manifest_path,
            domain="agentdojo",
            expected_count=freeze_v1.EXPECTED_CASE_COUNT,
        )
        packets = batch._discover_packets(packet_root, freeze_v1.EXPECTED_CASE_COUNT)
    except batch.BatchCaseLockError as exc:
        raise ContractLifecycleError(str(exc)) from exc
    case_ids = [case.case_unit_id for case in cases]
    if set(packets) != set(case_ids):
        raise ContractLifecycleError("preflight packet set differs from manifest")
    for case in cases:
        if packets[case.case_unit_id].metadata != case:
            raise ContractLifecycleError(
                f"preflight packet metadata differs: {case.case_unit_id}"
            )
    _assert_equal(
        dict(Counter(case.case_unit_id.split(":")[1] for case in cases)),
        freeze_v1.EXPECTED_SUITE_COUNTS,
        "preflight suite denominator",
    )
    try:
        batch._validate_source_bundle(
            source_bundle_path,
            manifest_path=manifest_path,
            manifest=manifest,
            cases=cases,
            packets=packets,
        )
    except batch.BatchCaseLockError as exc:
        raise ContractLifecycleError(str(exc)) from exc

    config = _load_json_mapping(config_path, "draft review config")
    config_paths = freeze_v1._validate_draft_review_config(
        config,
        expected_count=freeze_v1.EXPECTED_CASE_COUNT,
        config_path=config_path,
        case_lock_path=planned_case_lock,
        lock_acceptance_path=planned_acceptance,
        score_prompt_path=score_prompt_path,
        score_schema_path=score_schema_path,
    )
    for name, path in tuple(config_paths.items()):
        config_paths[name] = _require_regular_file(
            path, f"preflight locked config input {name}"
        )
    config_hash = sha256_file(config_path)
    input_lock_time = _preflight_input_lock_time(
        input_lock_path=input_lock_path,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        config_path=config_path,
        packet_root=packet_root,
        case_ids=case_ids,
    )
    input_lock_hash = sha256_file(input_lock_path)

    report = _load_json_mapping(report_path, "draft lifecycle report")
    report_run_id = report.get("run_id")
    if not isinstance(report_run_id, str) or not report_run_id.strip():
        raise ContractLifecycleError("preflight lifecycle report.run_id is missing")
    report_run_id = report_run_id.strip()
    for field, expected in (
        ("schema_version", "agentdojo_draft_review_report/v1"),
        ("mode", "full"),
        ("full_denominator", freeze_v1.EXPECTED_CASE_COUNT),
        ("selected_case_count", freeze_v1.EXPECTED_CASE_COUNT),
        ("resolved_config_sha256", config_hash),
        ("input_lock_sha256", input_lock_hash),
        ("unresolved_drafts", []),
    ):
        _assert_equal(report.get(field), expected, f"preflight report.{field}")
    expected_report_counts = {
        "case_packets": 949,
        "source_entries": 949,
        "valid_drafts": 949,
        "reviewed": 949,
        "lock_eligible": 949,
        "locked": 0,
        "unresolved_drafts": 0,
    }
    _assert_equal(
        report.get("counts"), expected_report_counts, "preflight report counts"
    )
    review_results = report.get("review_results")
    if not isinstance(review_results, list) or len(review_results) != 949:
        raise ContractLifecycleError("preflight report must contain 949 review results")
    _assert_equal(
        [
            result.get("case_unit_id")
            for result in review_results
            if isinstance(result, Mapping)
        ],
        case_ids,
        "preflight review-result order",
    )
    if any(
        not isinstance(result, Mapping) or result.get("status") != "accepted"
        for result in review_results
    ):
        raise ContractLifecycleError(
            "preflight requires 949 fresh accepted review results; reused/unresolved is forbidden"
        )

    lifecycle_index = _load_json_mapping(index_path, "draft lifecycle index")
    index_entries = lifecycle_index.get("entries")
    if not isinstance(index_entries, list) or len(index_entries) != 949:
        raise ContractLifecycleError(
            "preflight lifecycle index must contain 949 entries"
        )
    for field, expected in (
        ("schema_version", "agentdojo_draft_review_index/v1"),
        ("mode", "full"),
        ("case_count", 949),
        ("full_denominator", 949),
        ("case_id_order_sha256", batch._sha256_object(case_ids)),
        ("case_id_set_sha256", batch._sha256_object(sorted(case_ids))),
        ("resolved_config_sha256", config_hash),
        ("input_lock_sha256", input_lock_hash),
    ):
        _assert_equal(lifecycle_index.get(field), expected, f"preflight index.{field}")
    _assert_equal(
        lifecycle_index.get("entries_sha256"),
        batch._sha256_object(index_entries),
        "preflight index entries hash",
    )

    expected_directories = {
        packets[case_id].case_packet_path.parent.name for case_id in case_ids
    }
    actual_directories = {
        path.name
        for path in draft_root.iterdir()
        if path.is_dir() and not path.is_symlink()
    }
    _assert_equal(
        actual_directories, expected_directories, "preflight draft directory set"
    )

    checklist_schema = _load_json_mapping(
        config_paths["checklist_schema"], "checklist schema"
    )
    review_schema = _load_json_mapping(config_paths["review_schema"], "review schema")
    Draft202012Validator.check_schema(checklist_schema)
    Draft202012Validator.check_schema(review_schema)
    checklist_validator = Draft202012Validator(checklist_schema)
    review_validator = Draft202012Validator(
        review_schema, format_checker=FormatChecker()
    )
    generation_results, generation_batch = (
        freeze_v1._validate_generation_batch_provenance(
            drafts=draft_root,
            cases=cases,
            packets=packets,
            config=config,
            config_paths=config_paths,
            input_lock_time=input_lock_time,
        )
    )
    generation_config = dict(config["generation"])
    review_config = dict(config["review"])
    expected_reviewer_config = {
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "codex_cli_version": config["codex_cli_version"],
        "model": generation_config["model"],
        "reasoning_effort": generation_config["reasoning_effort"],
        "sandbox": review_config["sandbox"],
        "ephemeral": True,
        "ignore_user_config": True,
        "model_verbosity": "low",
        "timeout_seconds": review_config["timeout_seconds"],
    }

    response_ids: set[str] = set()
    per_case: list[dict[str, Any]] = []
    total_review_rounds = 0
    for position, case in enumerate(cases):
        packet = packets[case.case_unit_id]
        case_dir = draft_root / packet.case_packet_path.parent.name
        paths = {
            name: _require_regular_file(
                case_dir / filename, f"preflight {case.case_unit_id} {name}"
            )
            for name, filename in {
                "checklist": "checklist.yaml",
                "checklist_json": "checklist.json",
                "generated_checklist": "generated_checklist.yaml",
                "generated_checklist_json": "generated_checklist.json",
                "generation": "generation.json",
                "llm_call": "llm_call.json",
                "api_response": "api_response.json",
                "reasoning_summary": "reasoning_summary.txt",
                "review": "review.json",
                "review_lifecycle": "review_lifecycle.json",
            }.items()
        }
        try:
            final_checklist = batch._validate_checklist(
                paths["checklist"],
                packet=packet,
                checklist_validator=checklist_validator,
            )
            generated_checklist = batch._validate_checklist(
                paths["generated_checklist"],
                packet=packet,
                checklist_validator=checklist_validator,
            )
        except batch.BatchCaseLockError as exc:
            raise ContractLifecycleError(str(exc)) from exc
        _assert_equal(
            _load_json_mapping(paths["checklist_json"], "final checklist JSON"),
            final_checklist,
            f"preflight final YAML/JSON {case.case_unit_id}",
        )
        _assert_equal(
            _load_json_mapping(
                paths["generated_checklist_json"], "generated checklist JSON"
            ),
            generated_checklist,
            f"preflight generated YAML/JSON {case.case_unit_id}",
        )
        deterministic = review_agentdojo_checklist(
            final_checklist, case_packet_path=packet.case_packet_path
        )
        _assert_equal(
            deterministic,
            {"status": "pass", "findings": []},
            f"preflight deterministic review {case.case_unit_id}",
        )
        generation_receipt = _load_json_mapping(
            paths["generation"], f"generation receipt {case.case_unit_id}"
        )
        for field, expected in (
            ("schema_version", "case_checklist_generation/v1"),
            ("case_unit_id", case.case_unit_id),
            ("case_packet_sha256", sha256_file(packet.case_packet_path)),
            (
                "checklist_sha256",
                sha256_file(paths["generated_checklist"]),
            ),
            (
                "composed_draft_prompt_sha256",
                sha256_file(config_paths["composed_draft_prompt"]),
            ),
            (
                "checklist_schema_sha256",
                sha256_file(config_paths["checklist_schema"]),
            ),
            ("resolved_config_sha256", config_hash),
            ("input_lock_sha256", input_lock_hash),
            ("provider", "codex_cli"),
            ("auth_mode", "codex_login"),
            ("model", "gpt-5.6-sol"),
            ("reasoning_effort", "xhigh"),
        ):
            _assert_equal(
                generation_receipt.get(field),
                expected,
                f"preflight generation {case.case_unit_id}.{field}",
            )
        for path_field, expected_path in (
            ("case_packet_path", packet.case_packet_path),
            ("checklist_path", paths["generated_checklist"]),
            ("checklist_json_path", paths["generated_checklist_json"]),
            ("llm_call_path", paths["llm_call"]),
            ("api_response_path", paths["api_response"]),
            ("reasoning_summary_path", paths["reasoning_summary"]),
            ("composed_draft_prompt_path", config_paths["composed_draft_prompt"]),
            ("checklist_schema_path", config_paths["checklist_schema"]),
        ):
            declared = freeze_v1._resolve_declared_artifact_path(
                generation_receipt.get(path_field),
                f"preflight generation {case.case_unit_id}.{path_field}",
            )
            _assert_equal(
                declared,
                expected_path,
                f"preflight generation {case.case_unit_id}.{path_field}",
            )
            hash_field = path_field.removesuffix("_path") + "_sha256"
            _assert_equal(
                generation_receipt.get(hash_field),
                sha256_file(expected_path),
                f"preflight generation {case.case_unit_id}.{hash_field}",
            )
        generation_component = freeze_v1._validate_generation_case_provenance(
            case=case,
            packet=packet,
            case_dir=case_dir,
            paths=paths,
            batch_result=generation_results[case_dir.name],
            config=config,
            config_paths=config_paths,
            input_lock_time=input_lock_time,
            response_ids=response_ids,
        )
        try:
            review = batch._validate_review(
                paths["review"],
                case_unit_id=case.case_unit_id,
                packet_path=packet.case_packet_path,
                checklist_path=paths["checklist"],
                draft_prompt_path=config_paths["composed_draft_prompt"],
                checklist_schema_path=config_paths["checklist_schema"],
                review_prompt_path=config_paths["review_prompt"],
                review_schema_path=config_paths["review_schema"],
                review_validator=review_validator,
            )
        except batch.BatchCaseLockError as exc:
            raise ContractLifecycleError(str(exc)) from exc
        _assert_equal(
            review.get("reviewer_config"),
            expected_reviewer_config,
            f"preflight reviewer config {case.case_unit_id}",
        )
        lifecycle = _load_json_mapping(
            paths["review_lifecycle"], f"review lifecycle {case.case_unit_id}"
        )
        _validate_preflight_lifecycle_acceptance(
            case_unit_id=case.case_unit_id,
            lifecycle=lifecycle,
            final_checklist_sha256=sha256_file(paths["checklist"]),
            final_review_sha256=sha256_file(paths["review"]),
        )
        review_component = freeze_v1._validate_review_case_provenance(
            case=case,
            packet=packet,
            case_dir=case_dir,
            generated_checklist_path=paths["generated_checklist"],
            final_checklist_path=paths["checklist"],
            review_receipt=review,
            lifecycle=lifecycle,
            report_run_id=report_run_id,
            config=config,
            config_paths=config_paths,
            review_schema=review_schema,
            checklist_validator=checklist_validator,
            input_lock_time=input_lock_time,
            response_ids=response_ids,
        )
        total_review_rounds += int(lifecycle["review_rounds"])
        expected_index_entry = {
            "case_unit_id": case.case_unit_id,
            "task_id": case.task_id,
            "suite": case.case_unit_id.split(":")[1],
            "case_packet_path": _display(packet.case_packet_path),
            "case_packet_sha256": sha256_file(packet.case_packet_path),
            "generated_checklist_path": _display(paths["generated_checklist"]),
            "generated_checklist_sha256": sha256_file(paths["generated_checklist"]),
            "generation_receipt_path": _display(paths["generation"]),
            "generation_receipt_sha256": sha256_file(paths["generation"]),
            "checklist_path": _display(paths["checklist"]),
            "checklist_sha256": sha256_file(paths["checklist"]),
            "checklist_json_path": _display(paths["checklist_json"]),
            "checklist_json_sha256": sha256_file(paths["checklist_json"]),
            "review_path": _display(paths["review"]),
            "review_sha256": sha256_file(paths["review"]),
            "review_lifecycle_path": _display(paths["review_lifecycle"]),
            "review_lifecycle_sha256": sha256_file(paths["review_lifecycle"]),
            "revised": lifecycle["revised"],
            "review_rounds": lifecycle["review_rounds"],
        }
        _assert_equal(
            index_entries[position],
            expected_index_entry,
            f"preflight lifecycle index entry {case.case_unit_id}",
        )
        _assert_equal(
            review_results[position].get("review_rounds"),
            lifecycle["review_rounds"],
            f"preflight report review rounds {case.case_unit_id}",
        )
        _assert_equal(
            review_results[position].get("revised"),
            lifecycle["revised"],
            f"preflight report revised flag {case.case_unit_id}",
        )
        per_case.append(
            {
                "case_unit_id": case.case_unit_id,
                "checklist_sha256": sha256_file(paths["checklist"]),
                "review_sha256": sha256_file(paths["review"]),
                "review_lifecycle_sha256": sha256_file(paths["review_lifecycle"]),
                "generation_provenance_sha256": sha256_object(generation_component),
                "review_revision_provenance_sha256": sha256_object(review_component),
                "review_rounds": lifecycle["review_rounds"],
                "revised": lifecycle["revised"],
            }
        )

    _assert_equal(
        len(response_ids),
        949 + total_review_rounds,
        "preflight unique Codex response-id denominator",
    )
    _require_planned_destination_absent(planned_case_lock, "planned case-lock output")
    _require_planned_destination_absent(
        planned_acceptance, "planned case-lock acceptance output"
    )
    snapshot = {
        "schema_version": CHECKLIST_REVIEW_PREFLIGHT_SCHEMA_VERSION,
        "status": "ready_for_batch_lock",
        "expected_count": 949,
        "counts": {
            "case_packets": 949,
            "source_entries": 949,
            "valid_drafts": 949,
            "accepted_reviews": 949,
            "lock_eligible": 949,
            "unresolved_drafts": 0,
        },
        "case_identity": {
            "case_id_order_sha256": sha256_object(case_ids),
            "case_id_set_sha256": sha256_object(sorted(case_ids)),
            "suite_case_counts": dict(freeze_v1.EXPECTED_SUITE_COUNTS),
        },
        "inputs": {
            "manifest_path": _display(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
            "source_bundle_path": _display(source_bundle_path),
            "source_bundle_sha256": sha256_file(source_bundle_path),
            "case_packet_root": _display(packet_root),
            "case_packet_tree_sha256": sha256_path(packet_root),
            "draft_root": _display(draft_root),
            "draft_tree_sha256": sha256_path(draft_root),
            "resolved_config_path": _display(config_path),
            "resolved_config_sha256": config_hash,
            "input_lock_path": _display(input_lock_path),
            "input_lock_sha256": input_lock_hash,
            "lifecycle_report_path": _display(report_path),
            "lifecycle_report_sha256": sha256_file(report_path),
            "lifecycle_index_path": _display(index_path),
            "lifecycle_index_sha256": sha256_file(index_path),
            "generation_batch": generation_batch,
        },
        "planned_outputs": {
            "case_lock_path": _display(planned_case_lock),
            "case_lock_destination_absent": True,
            "lock_acceptance_path": _display(planned_acceptance),
            "lock_acceptance_destination_absent": True,
        },
        "case_entries_sha256": sha256_object(per_case),
        "case_entries": per_case,
    }
    return snapshot


def preflight_agentdojo_full_review_currentness(
    **snapshot_overrides: Any,
) -> dict[str, Any]:
    """Run the review-only pre-lock gate twice and reject any currentness drift."""

    first = build_review_currentness_preflight(**snapshot_overrides)
    second = build_review_currentness_preflight(**snapshot_overrides)
    if first != second:
        raise ContractLifecycleError(
            "review-currentness inputs changed between preflight validation passes"
        )
    return second


def publish_review_currentness_preflight_receipt(
    *, snapshot: Mapping[str, Any], output_path: str | Path
) -> Path:
    """Durably publish a passed pre-lock review preflight without replacement."""

    _assert_equal(
        snapshot.get("schema_version"),
        CHECKLIST_REVIEW_PREFLIGHT_SCHEMA_VERSION,
        "review preflight snapshot schema",
    )
    _assert_equal(snapshot.get("status"), "ready_for_batch_lock", "preflight status")
    _assert_equal(
        snapshot.get("counts"),
        {
            "case_packets": 949,
            "source_entries": 949,
            "valid_drafts": 949,
            "accepted_reviews": 949,
            "lock_eligible": 949,
            "unresolved_drafts": 0,
        },
        "review preflight receipt counts",
    )
    payload = {
        "schema_version": CHECKLIST_REVIEW_PREFLIGHT_RECEIPT_SCHEMA_VERSION,
        "status": "passed",
        "created_at": _utc_now().replace(microsecond=0).isoformat(),
        "snapshot_sha256": sha256_object(snapshot),
        "snapshot": dict(snapshot),
    }
    output = _absolute_path(output_path)
    _exclusive_publish_json(output, payload)
    return output.resolve()


def verify_review_currentness_preflight_receipt(
    *, receipt_path: str | Path, require_planned_outputs_absent: bool = True
) -> dict[str, Any]:
    """Verify a machine-published preflight receipt before optional tree sealing."""

    path = _require_regular_file(receipt_path, "review preflight receipt")
    payload = _load_json_mapping(path, "review preflight receipt")
    _assert_equal(
        set(payload),
        {"schema_version", "status", "created_at", "snapshot_sha256", "snapshot"},
        "review preflight receipt fields",
    )
    _assert_equal(
        payload.get("schema_version"),
        CHECKLIST_REVIEW_PREFLIGHT_RECEIPT_SCHEMA_VERSION,
        "review preflight receipt schema",
    )
    _assert_equal(payload.get("status"), "passed", "review preflight receipt status")
    _aware_timestamp(payload.get("created_at"), "review preflight receipt.created_at")
    snapshot = payload.get("snapshot")
    if not isinstance(snapshot, Mapping):
        raise ContractLifecycleError("review preflight receipt snapshot is missing")
    _assert_equal(
        payload.get("snapshot_sha256"),
        sha256_object(snapshot),
        "review preflight snapshot hash",
    )
    _assert_equal(
        snapshot.get("schema_version"),
        CHECKLIST_REVIEW_PREFLIGHT_SCHEMA_VERSION,
        "review preflight snapshot schema",
    )
    _assert_equal(snapshot.get("status"), "ready_for_batch_lock", "preflight status")
    counts = snapshot.get("counts")
    if not isinstance(counts, Mapping):
        raise ContractLifecycleError("review preflight counts are missing")
    for field, expected in (
        ("case_packets", 949),
        ("source_entries", 949),
        ("valid_drafts", 949),
        ("accepted_reviews", 949),
        ("lock_eligible", 949),
        ("unresolved_drafts", 0),
    ):
        _assert_equal(counts.get(field), expected, f"review preflight count {field}")
    inputs = snapshot.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ContractLifecycleError("review preflight input digests are missing")
    for prefix in (
        "manifest",
        "source_bundle",
        "resolved_config",
        "input_lock",
        "lifecycle_report",
        "lifecycle_index",
    ):
        current_path = _resolve_declared_path(
            inputs.get(f"{prefix}_path"), f"review preflight {prefix}"
        )
        _assert_equal(
            inputs.get(f"{prefix}_sha256"),
            sha256_file(current_path),
            f"review preflight {prefix} hash",
        )
    for prefix, hash_field in (
        ("case_packet_root", "case_packet_tree_sha256"),
        ("draft_root", "draft_tree_sha256"),
    ):
        current_root = _require_regular_directory(
            inputs.get(prefix), f"review preflight {prefix}"
        )
        _audit_tree_file_safety(current_root, f"review preflight {prefix}")
        _assert_equal(
            inputs.get(hash_field),
            sha256_path(current_root),
            f"review preflight {prefix} hash",
        )
    draft_root_value = snapshot.get("case_entries")
    if not isinstance(draft_root_value, list) or len(draft_root_value) != 949:
        raise ContractLifecycleError("review preflight case entries are incomplete")
    _assert_equal(
        snapshot.get("case_entries_sha256"),
        sha256_object(draft_root_value),
        "review preflight case-entry hash",
    )
    if require_planned_outputs_absent:
        planned = snapshot.get("planned_outputs")
        if not isinstance(planned, Mapping):
            raise ContractLifecycleError("review preflight planned outputs are missing")
        _require_planned_destination_absent(
            planned.get("case_lock_path"), "preflight planned case lock"
        )
        _require_planned_destination_absent(
            planned.get("lock_acceptance_path"), "preflight planned acceptance"
        )
    return dict(snapshot)


def _aggregate_hashes(case_bindings: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    ordered = [dict(entry) for entry in case_bindings]
    by_id = sorted(ordered, key=lambda entry: str(entry["case_unit_id"]))
    lock_order = [
        {
            "case_unit_id": entry["case_unit_id"],
            "case_lock_entry_sha256": entry["case_lock_entry_sha256"],
            "case_lock_line_sha256": entry["case_lock_line_sha256"],
        }
        for entry in ordered
    ]
    review_order = [
        {
            "case_unit_id": entry["case_unit_id"],
            "review_revision_receipts_sha256": entry["review_revision_receipts_sha256"],
        }
        for entry in ordered
    ]
    return {
        "case_binding_order_sha256": sha256_object(ordered),
        "case_binding_set_sha256": sha256_object(by_id),
        "case_id_order_sha256": sha256_object(
            [entry["case_unit_id"] for entry in ordered]
        ),
        "case_id_set_sha256": sha256_object(
            sorted(str(entry["case_unit_id"]) for entry in ordered)
        ),
        "case_lock_entry_order_sha256": sha256_object(lock_order),
        "case_lock_entry_set_sha256": sha256_object(
            sorted(lock_order, key=lambda entry: str(entry["case_unit_id"]))
        ),
        "review_revision_receipt_order_sha256": sha256_object(review_order),
        "review_revision_receipt_set_sha256": sha256_object(
            sorted(review_order, key=lambda entry: str(entry["case_unit_id"]))
        ),
    }


def build_checklist_freeze_v2_definition(**snapshot_overrides: Any) -> dict[str, Any]:
    """Revalidate and materialize the deterministic 949-case v2 digest graph."""

    supplied = dict(snapshot_overrides)
    quiescence_receipt_path = supplied.pop(
        "review_quiescence_receipt_path", DEFAULT_REVIEW_QUIESCENCE_RECEIPT
    )
    lifecycle_code_snapshot_root = supplied.pop("lifecycle_code_snapshot_root", None)
    derive_per_case_review_run = supplied.pop("derive_per_case_review_run", False)
    derive_review_attempt_state_machine = supplied.pop(
        "derive_review_attempt_state_machine", False
    )
    derive_generation_attempt_state_machine = supplied.pop(
        "derive_generation_attempt_state_machine", False
    )
    if not isinstance(derive_per_case_review_run, bool):
        raise ContractLifecycleError("derive_per_case_review_run must be boolean")
    if not isinstance(derive_review_attempt_state_machine, bool):
        raise ContractLifecycleError(
            "derive_review_attempt_state_machine must be boolean"
        )
    if not isinstance(derive_generation_attempt_state_machine, bool):
        raise ContractLifecycleError(
            "derive_generation_attempt_state_machine must be boolean"
        )
    normalized = _normalized_snapshot_overrides(supplied)
    base = _build_v1_snapshot(
        normalized=normalized,
        lifecycle_code_snapshot_root=lifecycle_code_snapshot_root,
        derive_per_case_review_run=derive_per_case_review_run,
        derive_review_attempt_state_machine=derive_review_attempt_state_machine,
        derive_generation_attempt_state_machine=(
            derive_generation_attempt_state_machine
        ),
    )
    _validate_base_snapshot(base)

    packet_root = _input_directory(
        normalized,
        "case_packet_root",
        freeze_v1.DEFAULT_CASE_PACKETS / "agentdojo",
        "v2 case-packet root",
    )
    draft_root = _input_directory(
        normalized, "draft_root", freeze_v1.DEFAULT_DRAFT_ROOT, "v2 draft root"
    )
    quiescence_binding = verify_review_quiescence_receipt(
        receipt_path=quiescence_receipt_path,
        max_age_seconds=None,
        expected_draft_tree_sha256=base["inputs"]["draft_root"]["tree_sha256"],
        require_process_quiescence=True,
        post_lock_snapshot_overrides={
            **normalized,
            **(
                {"lifecycle_code_snapshot_root": lifecycle_code_snapshot_root}
                if lifecycle_code_snapshot_root is not None
                else {}
            ),
            **(
                {"derive_per_case_review_run": True}
                if derive_per_case_review_run
                else {}
            ),
            **(
                {"derive_review_attempt_state_machine": True}
                if derive_review_attempt_state_machine
                else {}
            ),
            **(
                {"derive_generation_attempt_state_machine": True}
                if derive_generation_attempt_state_machine
                else {}
            ),
        },
    )
    if "currentness_gate_sha256" in quiescence_binding:
        _assert_equal(
            quiescence_binding["currentness_gate_sha256"],
            sha256_object(base),
            "post-lock quiescence/current v1 snapshot digest",
        )
    lifecycle_index_path = _input_path(
        normalized,
        "lifecycle_index_path",
        freeze_v1.DEFAULT_DRAFT_REVIEW_INDEX,
        "v2 lifecycle index",
    )
    lifecycle_report_path = _input_path(
        normalized,
        "lifecycle_report_path",
        freeze_v1.DEFAULT_DRAFT_REVIEW_REPORT,
        "v2 lifecycle report",
    )
    case_lock_path = _input_path(
        normalized,
        "case_lock_path",
        freeze_v1.DEFAULT_CASE_CHECKLIST_LOCK,
        "v2 case lock",
    )
    acceptance_path = _input_path(
        normalized,
        "lock_acceptance_path",
        freeze_v1.DEFAULT_CASE_CHECKLIST_LOCK_ACCEPTANCE,
        "v2 case-lock acceptance",
    )

    lifecycle_index = _load_json_mapping(lifecycle_index_path, "lifecycle index")
    index_entries = lifecycle_index.get("entries")
    if (
        not isinstance(index_entries, list)
        or len(index_entries) != freeze_v1.EXPECTED_CASE_COUNT
    ):
        raise ContractLifecycleError("lifecycle index must contain exactly 949 entries")
    acceptance = _load_json_mapping(acceptance_path, "case-lock acceptance")
    accepted_cases = acceptance.get("accepted_cases")
    if (
        not isinstance(accepted_cases, list)
        or len(accepted_cases) != freeze_v1.EXPECTED_CASE_COUNT
    ):
        raise ContractLifecycleError("batch acceptance must contain exactly 949 cases")
    _assert_equal(
        acceptance.get("counts", {}).get("valid_drafts")
        if isinstance(acceptance.get("counts"), Mapping)
        else None,
        freeze_v1.EXPECTED_CASE_COUNT,
        "batch acceptance valid denominator",
    )
    _assert_equal(
        acceptance.get("counts", {}).get("reviewed")
        if isinstance(acceptance.get("counts"), Mapping)
        else None,
        freeze_v1.EXPECTED_CASE_COUNT,
        "batch acceptance reviewed denominator",
    )
    _assert_equal(
        acceptance.get("counts", {}).get("locked")
        if isinstance(acceptance.get("counts"), Mapping)
        else None,
        freeze_v1.EXPECTED_CASE_COUNT,
        "batch acceptance locked denominator",
    )
    _assert_equal(
        acceptance.get("unresolved_drafts"), [], "batch acceptance unresolved cases"
    )

    acceptance_inputs = acceptance.get("inputs")
    if not isinstance(acceptance_inputs, Mapping):
        raise ContractLifecycleError(
            "batch acceptance prompt/schema inputs are missing"
        )
    prompt_schema_bindings = {
        prefix: _current_path_binding(
            acceptance_inputs, prefix, context="batch acceptance inputs"
        )
        for prefix in _PROMPT_SCHEMA_PREFIXES
    }
    prompt_schema_sha256 = sha256_object(prompt_schema_bindings)

    report = _load_json_mapping(lifecycle_report_path, "lifecycle report")
    run_id = report.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ContractLifecycleError("lifecycle report.run_id is missing")
    run_id = run_id.strip()
    per_case_review_runs = base.get("per_case_review_runs")
    derived_run_entries: list[Mapping[str, Any]] = []
    derived_runs_by_case: dict[str, Mapping[str, Any]] = {}
    if per_case_review_runs is not None:
        assert isinstance(per_case_review_runs, Mapping)
        raw_derived_entries = per_case_review_runs.get("entries")
        assert isinstance(raw_derived_entries, list)
        derived_run_entries = [
            entry for entry in raw_derived_entries if isinstance(entry, Mapping)
        ]
        if len(derived_run_entries) != freeze_v1.EXPECTED_CASE_COUNT:
            raise ContractLifecycleError("v2 per-case review-run index is incomplete")
        derived_runs_by_case = {
            str(entry["case_unit_id"]): entry for entry in derived_run_entries
        }
    attempt_state_machine_entries: list[Mapping[str, Any]] = []
    attempt_state_machines_by_case: dict[str, Mapping[str, Any]] = {}
    attempt_state_machine_binding = base.get("review_attempt_state_machines")
    if derive_review_attempt_state_machine:
        if not isinstance(attempt_state_machine_binding, Mapping):
            raise ContractLifecycleError(
                "v2 review-attempt state-machine index is missing"
            )
        raw_state_entries = attempt_state_machine_binding.get("entries")
        if not isinstance(raw_state_entries, list):
            raise ContractLifecycleError(
                "v2 review-attempt state-machine entries are missing"
            )
        attempt_state_machine_entries = [
            item for item in raw_state_entries if isinstance(item, Mapping)
        ]
        if len(attempt_state_machine_entries) != freeze_v1.EXPECTED_CASE_COUNT:
            raise ContractLifecycleError(
                "v2 review-attempt state-machine index is incomplete"
            )
        attempt_state_machines_by_case = {
            str(item["case_unit_id"]): item
            for item in attempt_state_machine_entries
        }
    elif attempt_state_machine_binding is not None:
        raise ContractLifecycleError(
            "v2 snapshot has an unrequested review-attempt state-machine binding"
        )

    lock_entries, lock_line_hashes = _load_lock_lines(case_lock_path)
    if len(lock_entries) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("case lock JSONL must contain exactly 949 entries")

    case_bindings: list[dict[str, Any]] = []
    for position, raw_index_entry in enumerate(index_entries):
        if not isinstance(raw_index_entry, Mapping):
            raise ContractLifecycleError(
                f"lifecycle index entry {position} is malformed"
            )
        entry = dict(raw_index_entry)
        case_unit_id = entry.get("case_unit_id")
        if not isinstance(case_unit_id, str) or not case_unit_id:
            raise ContractLifecycleError(
                f"lifecycle index entry {position} lacks an ID"
            )
        accepted_case = accepted_cases[position]
        if not isinstance(accepted_case, Mapping):
            raise ContractLifecycleError(f"accepted case {position} is malformed")
        _assert_equal(
            accepted_case.get("case_unit_id"), case_unit_id, "accepted case order"
        )
        lock_entry = lock_entries[position]
        _assert_equal(lock_entry.get("case_unit_id"), case_unit_id, "case lock order")

        packet_binding = _index_file_binding(
            entry, "case_packet", case_unit_id=case_unit_id
        )
        packet_path = _resolve_declared_path(
            packet_binding["path"], f"{case_unit_id} packet"
        )
        if packet_path.parent.parent != packet_root:
            raise ContractLifecycleError(
                f"{case_unit_id} packet is outside the canonical packet root"
            )
        raw_manifest_path = _require_regular_file(
            packet_path.parent / "raw_case_manifest.json",
            f"{case_unit_id} raw-case manifest",
        )
        raw_manifest_hash = sha256_file(raw_manifest_path)
        _assert_equal(
            accepted_case.get("raw_case_manifest_sha256"),
            raw_manifest_hash,
            f"{case_unit_id} raw-case manifest",
        )

        checklist_binding = _index_file_binding(
            entry, "checklist", case_unit_id=case_unit_id
        )
        checklist_json_binding = _index_file_binding(
            entry, "checklist_json", case_unit_id=case_unit_id
        )
        generated_binding = _index_file_binding(
            entry, "generated_checklist", case_unit_id=case_unit_id
        )
        generation_binding = _index_file_binding(
            entry, "generation_receipt", case_unit_id=case_unit_id
        )
        review_binding = _index_file_binding(entry, "review", case_unit_id=case_unit_id)
        lifecycle_binding = _index_file_binding(
            entry, "review_lifecycle", case_unit_id=case_unit_id
        )
        lifecycle_path = _resolve_declared_path(
            lifecycle_binding["path"], f"{case_unit_id} review lifecycle"
        )
        case_dir = lifecycle_path.parent
        if case_dir.parent != draft_root:
            raise ContractLifecycleError(
                f"{case_unit_id} lifecycle is outside the canonical draft root"
            )
        lifecycle = _load_json_mapping(
            lifecycle_path, f"{case_unit_id} review lifecycle"
        )
        _assert_equal(
            lifecycle.get("case_unit_id"), case_unit_id, "review lifecycle case ID"
        )
        _assert_equal(
            lifecycle.get("status"), "accepted", f"{case_unit_id} lifecycle status"
        )
        actual_run_id = run_id
        derived_run = derived_runs_by_case.get(case_unit_id)
        if derived_runs_by_case:
            if derived_run is None:
                raise ContractLifecycleError(
                    f"v2 per-case review run is missing: {case_unit_id}"
                )
            actual_run_id = str(derived_run["actual_run_id"])
        round_bindings, active_tree_hash, stale_runs = _review_round_bindings(
            case_unit_id=case_unit_id,
            case_dir=case_dir,
            lifecycle=lifecycle,
            run_id=actual_run_id,
            derive_review_attempt_state_machine=derive_review_attempt_state_machine,
        )
        if derived_run is not None:
            _assert_equal(
                active_tree_hash,
                derived_run.get("tree_sha256"),
                f"{case_unit_id} derived active review tree",
            )
        review_revision_receipts = {
            "review_receipt_sha256": review_binding["sha256"],
            "review_lifecycle_receipt_sha256": lifecycle_binding["sha256"],
            "review_lifecycle_object_sha256": sha256_object(lifecycle),
            "active_review_tree_sha256": active_tree_hash,
            "review_rounds": round_bindings,
            "stale_review_runs": stale_runs,
        }
        state_machine_entry = attempt_state_machines_by_case.get(case_unit_id)
        if derive_review_attempt_state_machine:
            if state_machine_entry is None:
                raise ContractLifecycleError(
                    f"review-attempt state-machine case is missing: {case_unit_id}"
                )
            _assert_equal(
                state_machine_entry.get("attempts"),
                round_bindings,
                f"{case_unit_id} review-attempt state-machine rounds",
            )
            review_revision_receipts["review_attempt_state_machine_sha256"] = (
                sha256_object(state_machine_entry)
            )
        if derived_run is not None:
            review_revision_receipts["actual_review_run_id"] = actual_run_id

        case_bindings.append(
            {
                "position": position,
                "case_unit_id": case_unit_id,
                "task_id": entry.get("task_id"),
                "suite": entry.get("suite"),
                "case_packet": packet_binding,
                "raw_case_manifest": {
                    "path": _display(raw_manifest_path),
                    "sha256": raw_manifest_hash,
                },
                "generated_checklist": generated_binding,
                "generation_receipt": generation_binding,
                "final_checklist": checklist_binding,
                "final_checklist_json": checklist_json_binding,
                "review_receipt": review_binding,
                "review_lifecycle_receipt": lifecycle_binding,
                "prompt_schema_bindings": prompt_schema_bindings,
                "prompt_schema_bindings_sha256": prompt_schema_sha256,
                "review_revision_receipts": review_revision_receipts,
                "review_revision_receipts_sha256": sha256_object(
                    review_revision_receipts
                ),
                "batch_acceptance_case_sha256": sha256_object(dict(accepted_case)),
                "case_lock_entry_sha256": sha256_object(lock_entry),
                "case_lock_line_sha256": lock_line_hashes[position],
            }
        )

    case_ids = [str(entry["case_unit_id"]) for entry in case_bindings]
    if len(set(case_ids)) != freeze_v1.EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("v2 case binding IDs are not exactly unique")
    _assert_equal(
        [entry.get("case_unit_id") for entry in lock_entries],
        case_ids,
        "v2 case lock order",
    )
    _assert_equal(
        [entry.get("case_unit_id") for entry in accepted_cases],
        case_ids,
        "v2 batch acceptance order",
    )
    if derived_run_entries:
        _assert_equal(
            [entry.get("case_unit_id") for entry in derived_run_entries],
            case_ids,
            "v2 per-case review-run order",
        )
    if attempt_state_machine_entries:
        _assert_equal(
            [entry.get("case_unit_id") for entry in attempt_state_machine_entries],
            case_ids,
            "v2 review-attempt state-machine order",
        )

    _recheck_base_currentness(base)
    _assert_equal(
        sha256_path(packet_root),
        base["inputs"]["case_packet_root"]["tree_sha256"],
        "packet tree currentness",
    )
    _assert_equal(
        sha256_path(draft_root),
        base["inputs"]["draft_root"]["tree_sha256"],
        "draft tree currentness",
    )

    publisher_code = {
        path: sha256_file(_require_regular_file(path, f"v2 publisher code {path}"))
        for path in _V2_CODE_PATHS
    }
    definition: dict[str, Any] = {
        "schema_version": CHECKLIST_FREEZE_V2_DEFINITION_SCHEMA_VERSION,
        "freeze_id": CHECKLIST_FREEZE_V2_ID,
        "status": "accepted_for_immutable_freeze",
        "benchmark_version": freeze_v1.BENCHMARK_VERSION,
        "attack": freeze_v1.ATTACK,
        "defense": freeze_v1.DEFENSE,
        "expected_count": freeze_v1.EXPECTED_CASE_COUNT,
        "counts": dict(_EXPECTED_COUNTS),
        "case_identity": dict(base["case_identity"]),
        "prompt_schema_bindings": prompt_schema_bindings,
        "prompt_schema_bindings_sha256": prompt_schema_sha256,
        "batch_lock": {
            "path": _display(case_lock_path),
            "sha256": sha256_file(case_lock_path),
            "entry_count": len(lock_entries),
        },
        "batch_lock_acceptance": {
            "path": _display(acceptance_path),
            "sha256": sha256_file(acceptance_path),
            "accepted_case_count": len(accepted_cases),
        },
        "validated_v1_snapshot_sha256": sha256_object(base),
        "validated_v1_snapshot": dict(base),
        "publisher_code_sha256": publisher_code,
        "review_quiescence_receipt": quiescence_binding,
        "case_bindings": case_bindings,
        "aggregate_sha256": _aggregate_hashes(case_bindings),
    }
    _validate_definition(definition)
    return definition


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _exclusive_publish_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Publish one JSON file via same-directory hard-link, never replacing a name."""

    path = _absolute_path(path)
    parent = path.parent
    _reject_symlink_ancestors(parent, "freeze output parent")
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        raise ContractLifecycleError(f"freeze output parent is unsafe: {parent}")
    path = parent.resolve() / path.name
    if _lexists(path):
        raise ContractLifecycleError(f"immutable destination already exists: {path}")
    data = (
        json.dumps(dict(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    staged: Path | None = None
    linked = False
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=parent,
            delete=False,
        ) as handle:
            staged = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fchmod(handle.fileno(), 0o444)
            os.fsync(handle.fileno())
        try:
            os.link(staged, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise ContractLifecycleError(
                f"immutable destination appeared concurrently: {path}"
            ) from exc
        linked = True
        _fsync_directory(parent)
        staged.unlink()
        staged = None
        _fsync_directory(parent)
        _require_regular_file(path, "new immutable publication")
    except ContractLifecycleError as exc:
        if linked:
            raise _PublishedOutputError(
                f"immutable destination became visible but final validation failed: {path}"
            ) from exc
        raise
    except OSError as exc:
        if linked:
            raise _PublishedOutputError(
                f"freeze destination became visible but durability failed: {path}"
            ) from exc
        raise ContractLifecycleError(
            f"failed to publish immutable freeze {path}: {exc}"
        ) from exc
    finally:
        if staged is not None:
            try:
                staged.unlink(missing_ok=True)
            except OSError:
                pass
    return sha256_bytes(data)


def _publish_invalidation(
    *,
    freeze_path: Path,
    expected_definition_sha256: str,
    reason_code: str,
    observed_definition_sha256: str | None,
) -> Path:
    invalidation_path = checklist_freeze_v2_invalidation_path(freeze_path)
    receipt = {
        "schema_version": CHECKLIST_FREEZE_V2_INVALIDATION_SCHEMA_VERSION,
        "status": "invalidated",
        "reason_code": reason_code,
        "detected_at": _aware_timestamp(None, "invalidation detected_at"),
        "freeze_path": _display(freeze_path),
        "freeze_sha256": sha256_file(freeze_path),
        "expected_definition_sha256": expected_definition_sha256,
        "observed_definition_sha256": observed_definition_sha256,
    }
    if _lexists(invalidation_path):
        return invalidation_path
    _exclusive_publish_json(invalidation_path, receipt)
    return invalidation_path


def freeze_agentdojo_full_checklists_v2(
    *,
    output_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    frozen_at: str | None = None,
    quiescence_max_age_seconds: int = DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    **snapshot_overrides: Any,
) -> ChecklistFreezeV2Result:
    """Validate twice, publish without replacement, then revalidate immediately."""

    output = _absolute_path(output_path)
    invalidation = checklist_freeze_v2_invalidation_path(output)
    if _lexists(output):
        raise ContractLifecycleError(f"immutable freeze already exists: {output}")
    if _lexists(invalidation):
        raise ContractLifecycleError(
            f"a prior invalidation receipt blocks publication: {invalidation}"
        )

    quiescence_receipt_path = snapshot_overrides.get(
        "review_quiescence_receipt_path", DEFAULT_REVIEW_QUIESCENCE_RECEIPT
    )
    verify_review_quiescence_receipt(
        receipt_path=quiescence_receipt_path,
        max_age_seconds=quiescence_max_age_seconds,
        require_process_quiescence=True,
        post_lock_snapshot_overrides=snapshot_overrides,
    )

    first = build_checklist_freeze_v2_definition(**snapshot_overrides)
    second = build_checklist_freeze_v2_definition(**snapshot_overrides)
    if first != second:
        raise ContractLifecycleError(
            "checklist inputs changed between the two pre-publication validations"
        )
    _validate_definition(second)
    definition_sha256 = sha256_object(second)
    payload = {
        "schema_version": CHECKLIST_FREEZE_V2_SCHEMA_VERSION,
        "freeze_id": CHECKLIST_FREEZE_V2_ID,
        "lock_status": "locked",
        "frozen_at": _aware_timestamp(frozen_at, "freeze.frozen_at"),
        "definition_sha256": definition_sha256,
        "definition": second,
    }
    verify_review_quiescence_receipt(
        receipt_path=quiescence_receipt_path,
        max_age_seconds=quiescence_max_age_seconds,
        expected_draft_tree_sha256=second["review_quiescence_receipt"][
            "draft_tree_sha256"
        ],
        require_process_quiescence=True,
        post_lock_snapshot_overrides=snapshot_overrides,
    )
    try:
        published_hash = _exclusive_publish_json(output, payload)
    except _PublishedOutputError:
        if output.is_file():
            _publish_invalidation(
                freeze_path=output,
                expected_definition_sha256=definition_sha256,
                observed_definition_sha256=None,
                reason_code="publication_durability_failure",
            )
        raise

    try:
        post = build_checklist_freeze_v2_definition(**snapshot_overrides)
    except Exception as exc:
        _publish_invalidation(
            freeze_path=output,
            expected_definition_sha256=definition_sha256,
            observed_definition_sha256=None,
            reason_code="post_publish_revalidation_failed",
        )
        raise ContractLifecycleError(
            "published checklist freeze was invalidated because post-publication "
            "revalidation failed"
        ) from exc
    if post != second:
        observed_hash = sha256_object(post)
        _publish_invalidation(
            freeze_path=output,
            expected_definition_sha256=definition_sha256,
            observed_definition_sha256=observed_hash,
            reason_code="post_publish_input_drift",
        )
        raise ContractLifecycleError(
            "published checklist freeze was invalidated by post-publication input drift"
        )

    if sha256_file(output) != published_hash:
        _publish_invalidation(
            freeze_path=output,
            expected_definition_sha256=definition_sha256,
            observed_definition_sha256=sha256_object(post),
            reason_code="published_freeze_readback_drift",
        )
        raise ContractLifecycleError(
            "published checklist freeze changed after creation"
        )
    if _lexists(invalidation):
        raise ContractLifecycleError(
            f"checklist freeze has an invalidation receipt: {invalidation}"
        )
    return ChecklistFreezeV2Result(output.resolve(), published_hash, second)


def verify_checklist_freeze_v2(
    *,
    freeze_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    **snapshot_overrides: Any,
) -> ChecklistFreezeV2Result:
    """Fail closed unless the immutable freeze is uninvalidated and fully current."""

    output = _require_regular_file(freeze_path, "v2 checklist freeze")
    invalidation = checklist_freeze_v2_invalidation_path(output)
    invalidation_was_present = _lexists(invalidation)
    initial_hash = sha256_file(output)
    payload = _load_json_mapping(output, "v2 checklist freeze")
    _assert_equal(
        set(payload),
        {
            "schema_version",
            "freeze_id",
            "lock_status",
            "frozen_at",
            "definition_sha256",
            "definition",
        },
        "v2 checklist freeze fields",
    )
    _assert_equal(
        payload.get("schema_version"),
        CHECKLIST_FREEZE_V2_SCHEMA_VERSION,
        "v2 checklist freeze schema",
    )
    _assert_equal(payload.get("freeze_id"), CHECKLIST_FREEZE_V2_ID, "freeze id")
    _assert_equal(payload.get("lock_status"), "locked", "freeze lock status")
    _aware_timestamp(payload.get("frozen_at"), "freeze.frozen_at")
    definition = payload.get("definition")
    if not isinstance(definition, Mapping):
        raise ContractLifecycleError("v2 checklist freeze definition is missing")
    definition = dict(definition)
    _validate_definition(definition)
    _assert_equal(
        payload.get("definition_sha256"),
        sha256_object(definition),
        "v2 checklist freeze definition hash",
    )

    current = build_checklist_freeze_v2_definition(**snapshot_overrides)
    _assert_equal(current, definition, "current v2 checklist freeze definition")
    if invalidation_was_present or _lexists(invalidation):
        raise ContractLifecycleError(
            f"v2 checklist freeze is invalidated: {invalidation}"
        )
    _assert_equal(sha256_file(output), initial_hash, "immutable freeze readback hash")
    _assert_equal(
        _load_json_mapping(output, "v2 checklist freeze readback"),
        payload,
        "immutable freeze readback payload",
    )
    return ChecklistFreezeV2Result(output, initial_hash, definition)
