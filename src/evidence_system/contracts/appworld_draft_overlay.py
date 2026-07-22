"""Atomic, immutable-source materialization for the AppWorld draft overlay.

The formal 485-case generation, the isolated 12-case location repair, and the
two earlier correction rounds are immutable inputs.  This module can only
create the separate ``accepted_cases_location_v1`` tree and its provenance
manifest.  It never promotes into, appends to, or rewrites any input namespace.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from evidence_system.contracts import appworld_draft_candidate_repair as candidate_repair
from evidence_system.contracts.appworld_draft_acceptance import (
    EXPECTED_CANONICAL_SUFFIXES,
    _SECRET_PATTERN_DEFINITIONS,
    _SECRET_PATTERNS,
    _validate_minimal_codex_sidecars,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import repo_root, resolve_repo_path


CORRECTIONS_SCHEMA = "appworld_draft_corrections_location.v1"
SECRET_SCAN_SCHEMA = "appworld_draft_secret_scan.v1"
LOCKED_STATUS = "locked_overlay"

EXPECTED_CASE_COUNT = 485
EXPECTED_LOCATION_CASE_IDS = candidate_repair.EXPECTED_REPAIR_CASE_IDS
EXPECTED_LOCATION_CASE_SET = frozenset(EXPECTED_LOCATION_CASE_IDS)
SECURITY_CASE_ID = "dac78d9_3"
EXPECTED_CORRECTED_CASE_SET = EXPECTED_LOCATION_CASE_SET | {SECURITY_CASE_ID}
EXPECTED_UNCHANGED_CASE_COUNT = 472

DEFAULT_DRAFT_ROOT = Path(
    "experiments/appworld_full_test_extension_v1/draft_runs/codex-gpt-5.4-high-support-v2"
)
DEFAULT_FORMAL_LOCK_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_run_lock.json"
DEFAULT_REPAIR_LOCK_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_repair_lock.json"
DEFAULT_ACCEPTED_CASES_ROOT = DEFAULT_DRAFT_ROOT / "accepted_cases_location_v1"
DEFAULT_CORRECTIONS_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_corrections_location_v1.json"

_FORMAL_BATCH_FILES = frozenset({"_batch_results.jsonl", "_batch_summary.json"})
_CANDIDATE_METADATA_FILES = frozenset(
    {"_candidate_results.jsonl", "_candidate_summary.json", "_candidate_validation.json"}
)
_ATTEMPT_FILE_RE = re.compile(
    r"^attempt_[0-9]{2}\.(?:"
    + "|".join(re.escape(value) for value in EXPECTED_CANONICAL_SUFFIXES)
    + r")$"
)

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "created_at",
        "formal_run",
        "repair",
        "accepted_overlay",
        "corrections",
        "security_incident_inventory",
        "validation",
        "superseded_overlay",
    }
)
_FORMAL_RUN_KEYS = frozenset(
    {
        "pre_run_lock_path",
        "pre_run_lock_sha256",
        "cases_root",
        "cases_tree_sha256",
        "batch_results_path",
        "batch_results_sha256",
        "batch_result_row_count",
        "batch_result_rows_semantic_sha256",
        "batch_summary_path",
        "batch_summary_sha256",
    }
)
_REPAIR_KEYS = frozenset(
    {
        "lock_path",
        "lock_sha256",
        "candidate_root",
        "candidate_tree_sha256",
        "candidate_results_path",
        "candidate_results_sha256",
        "candidate_result_rows_semantic_sha256",
        "candidate_summary_path",
        "candidate_summary_sha256",
        "candidate_validation_path",
        "candidate_validation_sha256",
        "candidate_validation_semantic_sha256",
    }
)
_ACCEPTED_OVERLAY_KEYS = frozenset(
    {
        "root",
        "tree_sha256",
        "file_count",
        "directory_count",
        "size_bytes",
        "case_count",
        "unchanged_case_count",
        "corrected_case_count",
    }
)
_LOCATION_CORRECTION_KEYS = frozenset(
    {
        "case_unit_id",
        "reason",
        "case_packet_path",
        "case_packet_sha256",
        "formal_case_path",
        "formal_case_tree_sha256",
        "source_case_path",
        "source_case_tree_sha256",
        "accepted_case_path",
        "accepted_case_tree_sha256",
        "source_result_row_sha256",
        "canonical_file_sha256",
        "secondary_defect",
        "validation",
    }
)
_LOCATION_VALIDATION_KEYS = frozenset(
    {
        "candidate_strict_validation_passed",
        "support_locations_resolve",
        "source_and_accepted_byte_equal",
        "formal_case_not_authoritative",
    }
)
_SECURITY_CORRECTION_KEYS = frozenset(
    {
        "case_unit_id",
        "reason",
        "case_packet_path",
        "case_packet_sha256",
        "formal_case_path",
        "formal_case_tree_sha256",
        "source_case_path",
        "source_case_tree_sha256",
        "accepted_case_path",
        "accepted_case_tree_sha256",
        "source_batch_results_path",
        "source_batch_results_sha256",
        "source_batch_summary_path",
        "source_batch_summary_sha256",
        "source_result_row_sha256",
        "result_normalization",
        "canonical_file_sha256",
        "secret_scan",
        "validation",
    }
)
_SECURITY_VALIDATION_KEYS = frozenset(
    {
        "codex_generation_valid",
        "support_locations_resolve",
        "source_and_accepted_byte_equal",
        "formal_secret_material_rejected",
        "accepted_secret_scan_passed",
    }
)
_VALIDATION_KEYS = frozenset(
    {
        "location_case_ids",
        "location_case_ids_semantic_sha256",
        "security_case_id",
        "exact_485_accepted_case_dirs",
        "formal_batch_immutable_exact_485",
        "location_candidate_validation_passed",
        "accepted_cases_match_authoritative_sources",
        "formal_secret_case_ids",
        "formal_secret_hit_count",
        "accepted_secret_hit_count",
        "draft_lifecycle_status",
        "human_review_completed",
    }
)
_SUPERSEDED_KEYS = frozenset(
    {
        "status",
        "legacy_manifest_path",
        "legacy_manifest_sha256",
        "legacy_accepted_cases_root",
        "legacy_accepted_cases_tree_sha256",
        "round_01",
        "round_02",
    }
)
_SUPERSEDED_ROUND_KEYS = frozenset(
    {"root", "tree_sha256", "case_ids", "case_ids_semantic_sha256"}
)
_SECURITY_INCIDENT_KEYS = frozenset(
    {
        "scanner_schema",
        "affected_case_ids",
        "formal_hits_by_case",
        "formal_hit_count",
        "accepted_hit_count",
        "credential_values_recorded",
    }
)


@dataclass(frozen=True)
class OverlayInputs:
    """Every validated input needed to build the immutable accepted overlay."""

    formal_lock_path: Path
    formal_lock: dict[str, Any]
    formal_cases_root: Path
    formal_batch_results_path: Path
    formal_batch_summary_path: Path
    formal_batch_rows: tuple[dict[str, Any], ...]
    expected_case_ids: tuple[str, ...]
    packet_root: Path
    repair_lock_path: Path
    repair_lock: dict[str, Any]
    candidate_root: Path
    candidate_results_path: Path
    candidate_summary_path: Path
    candidate_validation_path: Path
    candidate_rows: tuple[dict[str, Any], ...]
    candidate_validation: dict[str, Any]
    candidate_rows_by_id: dict[str, dict[str, Any]]
    security_root: Path
    security_case_dir: Path
    security_batch_results_path: Path
    security_batch_summary_path: Path
    security_result_row: dict[str, Any]
    security_normalization: dict[str, Any]
    legacy_manifest_path: Path
    legacy_accepted_root: Path
    round_01_root: Path
    accepted_root: Path
    corrections_path: Path
    immutable_guards: tuple[tuple[str, Path, str, str], ...]


def prepare_appworld_draft_overlay(
    *,
    formal_lock_path: str | Path = DEFAULT_FORMAL_LOCK_PATH,
    repair_lock_path: str | Path = DEFAULT_REPAIR_LOCK_PATH,
    accepted_cases_root: str | Path = DEFAULT_ACCEPTED_CASES_ROOT,
    corrections_path: str | Path = DEFAULT_CORRECTIONS_PATH,
) -> dict[str, Any]:
    """Run the full read-only preflight and require both outputs to be absent."""

    inputs = _load_overlay_inputs(
        formal_lock_path=formal_lock_path,
        repair_lock_path=repair_lock_path,
        accepted_cases_root=accepted_cases_root,
        corrections_path=corrections_path,
        output_state="absent",
    )
    return {
        "status": "ready_to_materialize",
        "case_count": len(inputs.expected_case_ids),
        "unchanged_case_count": EXPECTED_UNCHANGED_CASE_COUNT,
        "location_correction_count": len(EXPECTED_LOCATION_CASE_IDS),
        "security_correction_count": 1,
        "accepted_cases_root": _repo_relative(inputs.accepted_root),
        "corrections_path": _repo_relative(inputs.corrections_path),
        "formal_cases_tree_sha256": sha256_path(inputs.formal_cases_root),
        "candidate_tree_sha256": sha256_path(inputs.candidate_root),
        "formal_namespace_write_allowed": False,
    }


def materialize_appworld_draft_overlay(
    *,
    formal_lock_path: str | Path = DEFAULT_FORMAL_LOCK_PATH,
    repair_lock_path: str | Path = DEFAULT_REPAIR_LOCK_PATH,
    accepted_cases_root: str | Path = DEFAULT_ACCEPTED_CASES_ROOT,
    corrections_path: str | Path = DEFAULT_CORRECTIONS_PATH,
) -> dict[str, Any]:
    """Atomically create the 485-case accepted tree and exclusive manifest."""

    requested_root = resolve_repo_path(accepted_cases_root).resolve()
    requested_manifest = resolve_repo_path(corrections_path).resolve()
    requested_root.parent.mkdir(parents=True, exist_ok=True)
    requested_manifest.parent.mkdir(parents=True, exist_ok=True)
    lock_path = requested_root.parent / f".{requested_root.name}.materialize.lock"
    lock_identity = _acquire_exclusive_lock(lock_path)
    temp_root: Path | None = None
    root_identity: tuple[int, int] | None = None
    manifest_identity: tuple[int, int] | None = None
    try:
        inputs = _load_overlay_inputs(
            formal_lock_path=formal_lock_path,
            repair_lock_path=repair_lock_path,
            accepted_cases_root=accepted_cases_root,
            corrections_path=corrections_path,
            output_state="absent",
        )
        temp_root = Path(
            tempfile.mkdtemp(
                prefix=f".{inputs.accepted_root.name}.tmp-",
                dir=inputs.accepted_root.parent,
            )
        )
        _copy_authoritative_cases(inputs, temp_root)
        _validate_accepted_tree(inputs, temp_root)
        _assert_immutable_guards(inputs.immutable_guards)

        # The sibling rename is atomic.  A concurrent materializer cannot
        # pass the exclusive sibling lock.  Rechecking both outputs immediately
        # before rename also refuses an independently-created empty directory.
        _require(not inputs.accepted_root.exists(), f"accepted overlay appeared during materialization: {inputs.accepted_root}")
        _require(not inputs.corrections_path.exists(), f"corrections manifest appeared during materialization: {inputs.corrections_path}")
        os.rename(temp_root, inputs.accepted_root)
        temp_root = None
        root_identity = _path_identity(inputs.accepted_root)
        _assert_immutable_guards(inputs.immutable_guards)
        manifest = _build_manifest(inputs, inputs.accepted_root)
        _require(
            _secret_text_hit_count(json.dumps(manifest, ensure_ascii=False, sort_keys=True)) == 0,
            "corrections manifest would contain secret-like material",
        )
        manifest_identity = _write_json_exclusive(inputs.corrections_path, manifest)

        result = validate_appworld_draft_overlay(
            formal_lock_path=inputs.formal_lock_path,
            repair_lock_path=inputs.repair_lock_path,
            accepted_cases_root=inputs.accepted_root,
            corrections_path=inputs.corrections_path,
        )
        return result
    except Exception:
        if manifest_identity is not None:
            _unlink_if_same(requested_manifest, manifest_identity)
        if root_identity is not None:
            _rmtree_if_same(requested_root, root_identity)
        raise
    finally:
        if temp_root is not None and temp_root.exists():
            shutil.rmtree(temp_root)
        _unlink_if_same(lock_path, lock_identity)


def validate_appworld_draft_overlay(
    *,
    formal_lock_path: str | Path = DEFAULT_FORMAL_LOCK_PATH,
    repair_lock_path: str | Path = DEFAULT_REPAIR_LOCK_PATH,
    accepted_cases_root: str | Path = DEFAULT_ACCEPTED_CASES_ROOT,
    corrections_path: str | Path = DEFAULT_CORRECTIONS_PATH,
) -> dict[str, Any]:
    """Recompute the overlay manifest and every transitive immutable binding."""

    inputs = _load_overlay_inputs(
        formal_lock_path=formal_lock_path,
        repair_lock_path=repair_lock_path,
        accepted_cases_root=accepted_cases_root,
        corrections_path=corrections_path,
        output_state="present",
    )
    _validate_accepted_tree(inputs, inputs.accepted_root)
    observed = _load_mapping(inputs.corrections_path, "draft corrections location manifest")
    _validate_manifest_shape(observed)
    _parse_timestamp(observed.get("created_at"), "corrections created_at")
    expected = _build_manifest(
        inputs,
        inputs.accepted_root,
        created_at=_string(observed.get("created_at"), "corrections created_at"),
    )
    _require(observed == expected, "draft corrections location manifest differs from recomputed provenance")
    _assert_immutable_guards(inputs.immutable_guards)
    return {
        "status": LOCKED_STATUS,
        "schema_version": CORRECTIONS_SCHEMA,
        "manifest_path": _repo_relative(inputs.corrections_path),
        "manifest_sha256": sha256_file(inputs.corrections_path),
        "accepted_cases_root": _repo_relative(inputs.accepted_root),
        "accepted_cases_tree_sha256": sha256_path(inputs.accepted_root),
        "case_count": EXPECTED_CASE_COUNT,
        "unchanged_case_count": EXPECTED_UNCHANGED_CASE_COUNT,
        "corrected_case_count": len(EXPECTED_CORRECTED_CASE_SET),
        "accepted_secret_hit_count": 0,
        "formal_namespace_mutated": False,
    }


def _load_overlay_inputs(
    *,
    formal_lock_path: str | Path,
    repair_lock_path: str | Path,
    accepted_cases_root: str | Path,
    corrections_path: str | Path,
    output_state: str,
) -> OverlayInputs:
    _require(output_state in {"absent", "present"}, "invalid overlay output-state gate")
    formal_lock_file = _input_file(formal_lock_path, "formal draft lock")
    formal_lock = _load_mapping(formal_lock_file, "formal draft lock")
    formal_cases_root = _input_directory(
        _string(_mapping(formal_lock.get("execution"), "formal execution").get("output_root"), "formal output root"),
        "formal cases root",
    )
    draft_root = formal_lock_file.parent.parent.resolve()
    _require(formal_cases_root == draft_root / "cases", "formal cases root must remain <draft-root>/cases")

    accepted_root = resolve_repo_path(accepted_cases_root).resolve()
    corrections_file = resolve_repo_path(corrections_path).resolve()
    _require(accepted_root == draft_root / "accepted_cases_location_v1", "accepted overlay root path mismatch")
    _require(
        corrections_file == draft_root / "provenance" / "draft_corrections_location_v1.json",
        "corrections location manifest path mismatch",
    )
    if output_state == "absent":
        _require(not accepted_root.exists(), f"accepted overlay output must be absent: {accepted_root}")
        _require(not corrections_file.exists(), f"corrections manifest output must be absent: {corrections_file}")
    else:
        _input_directory(accepted_root, "accepted overlay root")
        _input_file(corrections_file, "corrections location manifest")

    expected_case_ids, packet_root = _formal_case_ids_and_packet_root(formal_lock)
    _validate_formal_namespace(formal_cases_root, expected_case_ids)
    formal_batch_results = _input_file(formal_cases_root / "_batch_results.jsonl", "formal batch results")
    formal_batch_summary = _input_file(formal_cases_root / "_batch_summary.json", "formal batch summary")
    formal_rows = tuple(_load_jsonl(formal_batch_results, "formal batch results"))
    _require(len(formal_rows) == EXPECTED_CASE_COUNT, "formal batch results must remain exactly 485 rows")
    formal_result_ids = [row.get("case_unit_dir") for row in formal_rows]
    _require(
        len(set(formal_result_ids)) == EXPECTED_CASE_COUNT
        and set(formal_result_ids) == set(expected_case_ids),
        "formal batch results must be one exact 485-case invocation",
    )
    _require(all(row.get("status") == "success" for row in formal_rows), "formal batch must remain 485 successes")

    repair_lock_file = _input_file(repair_lock_path, "candidate repair lock")
    _require(repair_lock_file == formal_lock_file.parent / "draft_repair_lock.json", "repair lock path mismatch")
    repair_lock = _load_mapping(repair_lock_file, "candidate repair lock")
    context = candidate_repair.validate_candidate_repair_lock(
        repair_lock_file,
        require_clean_candidate_root=False,
    )
    _require(context.formal_lock_path == formal_lock_file, "repair lock points to a different formal lock")
    _require(context.formal_cases_root == formal_cases_root, "repair lock points to a different formal cases root")
    _require(tuple(case["case_unit_id"] for case in context.cases) == EXPECTED_LOCATION_CASE_IDS, "repair case order drift")
    _require(
        context.candidate_output_root == draft_root / "repair_location_v1" / "candidates",
        "candidate output root path mismatch",
    )
    strict_validation = candidate_repair.validate_existing_candidates(repair_lock_file)
    expected_validation = {
        "schema_version": candidate_repair.CANDIDATE_VALIDATION_SCHEMA,
        "status": "passed",
        "case_count": len(EXPECTED_LOCATION_CASE_IDS),
        "passed_case_ids": list(EXPECTED_LOCATION_CASE_IDS),
        "failed_cases": [],
        "formal_cases_tree_unchanged": True,
        "promotion_performed": False,
    }
    _require(strict_validation == expected_validation, "read-only candidate revalidation did not pass the exact frozen 12")

    formal_generation = _mapping(repair_lock.get("formal_generation"), "repair formal_generation")
    _require(formal_generation.get("lock_sha256") == sha256_file(formal_lock_file), "repair/formal lock hash mismatch")
    _require(formal_generation.get("cases_tree_sha256") == sha256_path(formal_cases_root), "formal tree differs from repair lock")
    _require(formal_generation.get("batch_results_sha256") == sha256_file(formal_batch_results), "formal results differ from repair lock")
    _require(formal_generation.get("batch_summary_sha256") == sha256_file(formal_batch_summary), "formal summary differs from repair lock")
    original_batch = _mapping(repair_lock.get("original_batch"), "repair original_batch")
    _require(original_batch.get("result_row_count") == EXPECTED_CASE_COUNT, "repair lock formal result-row count mismatch")
    _require(original_batch.get("result_rows_sha256") == sha256_object(list(formal_rows)), "repair lock formal result-row semantic hash mismatch")

    candidate_root = _input_directory(context.candidate_output_root, "location candidate root")
    _validate_candidate_namespace(candidate_root)
    candidate_results = _input_file(candidate_root / "_candidate_results.jsonl", "candidate results")
    candidate_summary = _input_file(candidate_root / "_candidate_summary.json", "candidate summary")
    candidate_validation_path = _input_file(candidate_root / "_candidate_validation.json", "candidate validation")
    candidate_rows = tuple(_load_jsonl(candidate_results, "candidate results"))
    _require(len(candidate_rows) == len(EXPECTED_LOCATION_CASE_IDS), "candidate results must contain exactly 12 rows")
    _require(
        [row.get("case_unit_id") for row in candidate_rows] == list(EXPECTED_LOCATION_CASE_IDS),
        "candidate result order differs from the frozen repair order",
    )
    repair_lock_sha256 = sha256_file(repair_lock_file)
    for case_id, row in zip(EXPECTED_LOCATION_CASE_IDS, candidate_rows, strict=True):
        _require(row.get("schema_version") == candidate_repair.CANDIDATE_RESULTS_SCHEMA, f"candidate result schema mismatch: {case_id}")
        _require(row.get("repair_lock_sha256") == repair_lock_sha256, f"candidate result repair-lock hash mismatch: {case_id}")
        _require(row.get("generation_status") == "success", f"candidate generation is not successful: {case_id}")
        _require(row.get("strict_validation_status") == "passed", f"candidate strict validation did not pass: {case_id}")
        _require(row.get("promotion_performed") is False, f"candidate unexpectedly claims promotion: {case_id}")
        _validate_case_directory(candidate_root / case_id, case_id=case_id)

    saved_summary = _load_mapping(candidate_summary, "candidate summary")
    _validate_candidate_summary(saved_summary, repair_lock_sha256=repair_lock_sha256)
    saved_validation = _load_mapping(candidate_validation_path, "candidate validation")
    _validate_saved_candidate_validation(saved_validation, repair_lock_sha256=repair_lock_sha256)
    _require(_secret_hit_count(candidate_root) == 0, "location candidate namespace contains secret-like material")

    security_root = _input_directory(draft_root / "corrections" / "round_02", "security correction round")
    security_case_dir = _input_directory(security_root / SECURITY_CASE_ID, "security correction case")
    security_results = _input_file(security_root / "_batch_results.jsonl", "security correction batch results")
    security_summary = _input_file(security_root / "_batch_summary.json", "security correction batch summary")
    security_row, normalization = _validate_security_source(
        root=security_root,
        case_dir=security_case_dir,
        results_path=security_results,
        summary_path=security_summary,
        packet_path=packet_root / SECURITY_CASE_ID / "case_packet.md",
        formal_case_dir=formal_cases_root / SECURITY_CASE_ID,
    )
    formal_9ef_hits = sum(_primary_secret_hit_inventory(formal_cases_root / "9ef034e_2").values())
    _require(formal_9ef_hits == 44, "formal 9ef034e_2 secret-like hit count drift")
    _require(_secret_hit_count(formal_cases_root) == 180, "expanded formal secret scanner inventory drift")

    legacy_manifest_path = _input_file(draft_root / "provenance" / "draft_corrections.json", "legacy corrections manifest")
    legacy_accepted_root = _input_directory(draft_root / "accepted_cases", "legacy accepted cases root")
    round_01_root = _input_directory(draft_root / "corrections" / "round_01", "legacy round_01 root")
    _validate_legacy_inputs(
        manifest_path=legacy_manifest_path,
        accepted_root=legacy_accepted_root,
        round_01_root=round_01_root,
        expected_case_ids=expected_case_ids,
    )

    guards = (
        ("formal lock", formal_lock_file, "file", sha256_file(formal_lock_file)),
        ("formal cases", formal_cases_root, "tree", sha256_path(formal_cases_root)),
        ("formal batch results", formal_batch_results, "file", sha256_file(formal_batch_results)),
        ("formal batch summary", formal_batch_summary, "file", sha256_file(formal_batch_summary)),
        ("repair lock", repair_lock_file, "file", sha256_file(repair_lock_file)),
        ("candidate root", candidate_root, "tree", sha256_path(candidate_root)),
        ("security round", security_root, "tree", sha256_path(security_root)),
        ("legacy corrections manifest", legacy_manifest_path, "file", sha256_file(legacy_manifest_path)),
        ("legacy accepted cases", legacy_accepted_root, "tree", sha256_path(legacy_accepted_root)),
        ("legacy round_01", round_01_root, "tree", sha256_path(round_01_root)),
    )
    _assert_immutable_guards(guards)
    return OverlayInputs(
        formal_lock_path=formal_lock_file,
        formal_lock=formal_lock,
        formal_cases_root=formal_cases_root,
        formal_batch_results_path=formal_batch_results,
        formal_batch_summary_path=formal_batch_summary,
        formal_batch_rows=formal_rows,
        expected_case_ids=expected_case_ids,
        packet_root=packet_root,
        repair_lock_path=repair_lock_file,
        repair_lock=repair_lock,
        candidate_root=candidate_root,
        candidate_results_path=candidate_results,
        candidate_summary_path=candidate_summary,
        candidate_validation_path=candidate_validation_path,
        candidate_rows=candidate_rows,
        candidate_validation=saved_validation,
        candidate_rows_by_id={str(row["case_unit_id"]): dict(row) for row in candidate_rows},
        security_root=security_root,
        security_case_dir=security_case_dir,
        security_batch_results_path=security_results,
        security_batch_summary_path=security_summary,
        security_result_row=security_row,
        security_normalization=normalization,
        legacy_manifest_path=legacy_manifest_path,
        legacy_accepted_root=legacy_accepted_root,
        round_01_root=round_01_root,
        accepted_root=accepted_root,
        corrections_path=corrections_file,
        immutable_guards=guards,
    )


def _formal_case_ids_and_packet_root(formal_lock: Mapping[str, Any]) -> tuple[tuple[str, ...], Path]:
    inputs = _mapping(formal_lock.get("inputs"), "formal lock inputs")
    manifest_path = _input_file(_string(inputs.get("manifest_path"), "formal manifest path"), "formal manifest")
    _require(sha256_file(manifest_path) == inputs.get("manifest_sha256"), "formal manifest hash drift")
    manifest = _load_mapping(manifest_path, "formal extension manifest")
    domains = manifest.get("domains")
    _require(isinstance(domains, list) and len(domains) == 1, "formal manifest must contain one AppWorld domain")
    case_units = _mapping(domains[0], "formal AppWorld domain").get("case_units")
    _require(isinstance(case_units, list), "formal AppWorld case_units must be a list")
    case_ids = tuple(_string(_mapping(item, "formal case unit").get("case_unit_id"), "formal case_unit_id") for item in case_units)
    _require(len(case_ids) == EXPECTED_CASE_COUNT and len(set(case_ids)) == EXPECTED_CASE_COUNT, "formal manifest must contain 485 unique cases")
    _require(EXPECTED_CORRECTED_CASE_SET <= set(case_ids), "one or more correction cases are outside the formal manifest")
    packet_root = _input_directory(_string(inputs.get("case_packet_root"), "case packet root"), "case packet root")
    _require_no_symlinks(packet_root, "case packet root")
    return case_ids, packet_root


def _validate_formal_namespace(root: Path, expected_case_ids: Sequence[str]) -> None:
    _require_no_symlinks(root, "formal cases root")
    entries = list(root.iterdir())
    actual_dirs = {path.name for path in entries if path.is_dir() and not path.is_symlink()}
    actual_files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    _require(actual_dirs == set(expected_case_ids), "formal case directory set differs from the frozen 485")
    _require(actual_files == _FORMAL_BATCH_FILES, "formal cases root contains extra or missing batch files")
    _require(len(entries) == EXPECTED_CASE_COUNT + len(_FORMAL_BATCH_FILES), "formal cases root contains unsupported entries")
    for case_id in expected_case_ids:
        _validate_case_directory(root / case_id, case_id=case_id)


def _validate_candidate_namespace(root: Path) -> None:
    _require_no_symlinks(root, "location candidate root")
    entries = list(root.iterdir())
    actual_dirs = {path.name for path in entries if path.is_dir() and not path.is_symlink()}
    actual_files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    _require(actual_dirs == EXPECTED_LOCATION_CASE_SET, "candidate root does not contain exactly the frozen 12 directories")
    _require(actual_files == _CANDIDATE_METADATA_FILES, "candidate root metadata file set mismatch")
    _require(len(entries) == len(EXPECTED_LOCATION_CASE_IDS) + len(_CANDIDATE_METADATA_FILES), "candidate root contains unsupported entries")


def _validate_case_directory(path: Path, *, case_id: str) -> None:
    case_dir = _input_directory(path, f"case directory {case_id}")
    entries = list(case_dir.iterdir())
    _require(entries, f"case directory is empty: {case_id}")
    _require(all(entry.is_file() and not entry.is_symlink() for entry in entries), f"case directory contains a non-file or symlink: {case_id}")
    names = {entry.name for entry in entries}
    canonical = set(EXPECTED_CANONICAL_SUFFIXES)
    _require(canonical <= names, f"case directory is missing canonical files: {case_id}")
    extras = names - canonical
    _require(all(_ATTEMPT_FILE_RE.fullmatch(name) for name in extras), f"case directory contains unsupported files: {case_id}")


def _validate_candidate_summary(summary: Mapping[str, Any], *, repair_lock_sha256: str) -> None:
    _require(summary.get("schema_version") == candidate_repair.CANDIDATE_SUMMARY_SCHEMA, "candidate summary schema mismatch")
    _require(summary.get("status") == "candidate_generated/review_required", "candidate summary status mismatch")
    _require(summary.get("repair_lock_sha256") == repair_lock_sha256, "candidate summary repair-lock hash mismatch")
    expected_values = {
        "case_count": 12,
        "generation_success_count": 12,
        "strict_validation_pass_count": 12,
        "strict_validation_fail_count": 0,
        "regular_case_count": 11,
        "oversized_case_count": 1,
        "provider": "codex",
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "codex_sandbox": "read-only",
        "max_parallel": 8,
        "formal_cases_unchanged": True,
        "promotion_performed": False,
        "automatic_promotion_supported": False,
    }
    for key, value in expected_values.items():
        _require(summary.get(key) == value, f"candidate summary {key} mismatch")


def _validate_saved_candidate_validation(payload: Mapping[str, Any], *, repair_lock_sha256: str) -> None:
    _require(payload.get("schema_version") == candidate_repair.CANDIDATE_VALIDATION_SCHEMA, "candidate validation schema mismatch")
    _require(payload.get("status") == "passed", "saved candidate validation is not passed")
    _require(payload.get("repair_lock_sha256") == repair_lock_sha256, "candidate validation repair-lock hash mismatch")
    _require(payload.get("case_count") == 12, "saved candidate validation count mismatch")
    _require(payload.get("passed_case_ids") == list(EXPECTED_LOCATION_CASE_IDS), "saved candidate validation ID order mismatch")
    _require(payload.get("failed_cases") == [], "saved candidate validation contains failures")
    checks = _mapping(payload.get("checks"), "saved candidate validation checks")
    _require(checks.get("support_paths_in_packet_inventory") is True, "candidate support-path check did not pass")
    _require(checks.get("support_locations_resolve") is True, "candidate support-location check did not pass")
    _require(checks.get("formal_cases_tree_unchanged") is True, "candidate validation reports formal mutation")
    _require(checks.get("promotion_performed") is False, "candidate validation reports promotion")


def _validate_security_source(
    *,
    root: Path,
    case_dir: Path,
    results_path: Path,
    summary_path: Path,
    packet_path: Path,
    formal_case_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _require_no_symlinks(root, "security correction round")
    _require(
        {path.name for path in root.iterdir()} == {SECURITY_CASE_ID, "_batch_results.jsonl", "_batch_summary.json"},
        "security correction round inventory mismatch",
    )
    _validate_case_directory(case_dir, case_id=SECURITY_CASE_ID)
    packet = _input_file(packet_path, "security case packet")
    candidate_repair.validate_candidate_support(
        checklist_path=case_dir / "checklist.json",
        packet_path=packet,
        case_id=SECURITY_CASE_ID,
    )
    checklist_json = _load_mapping(case_dir / "checklist.json", "security checklist JSON")
    checklist_yaml = _load_mapping(case_dir / "checklist.yaml", "security checklist YAML")
    _require(checklist_json == checklist_yaml, "security checklist YAML/JSON mismatch")
    _require(checklist_json.get("schema_version") == "case_checklist_v1", "security checklist schema version mismatch")
    _require(checklist_json.get("domain") == "appworld", "security checklist domain mismatch")
    _require(checklist_json.get("case_unit_id") == SECURITY_CASE_ID, "security checklist identity mismatch")
    _require(checklist_json.get("task_id") == SECURITY_CASE_ID, "security checklist task identity mismatch")
    schema = _load_mapping(
        _input_file("neurips_ed_track_minimal/schemas/case_checklist.schema.json", "case checklist schema"),
        "case checklist schema",
    )
    errors = sorted(Draft202012Validator(schema).iter_errors(checklist_json), key=lambda error: list(error.absolute_path))
    _require(not errors, f"security checklist schema failure: {errors[0].message if errors else ''}")

    summary = _load_mapping(summary_path, "security correction summary")
    expected_summary = {
        "total_cases": 1,
        "completed_cases": 1,
        "success_cases": 1,
        "skipped_cases": 0,
        "failed_cases": 0,
        "warning_count": 0,
        "provider": "codex",
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "codex_sandbox": "read-only",
        "prompt_supplement": "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
        "token_budgets": [12000, 16000, 20000],
        "sort_by": "size",
        "quality_check": "none",
        "large_case_threshold_bytes": 100000,
        "lane_stats": {
            "regular": {"count": 1, "min_bytes": packet.stat().st_size, "max_bytes": packet.stat().st_size},
            "oversized": {"count": 0, "min_bytes": 0, "max_bytes": 0},
        },
        "output_root": _repo_relative(root),
    }
    _require(set(summary) == set(expected_summary) | {"started_at", "updated_at"}, "security correction summary field set mismatch")
    _parse_timestamp(summary.get("started_at"), "security correction started_at")
    _parse_timestamp(summary.get("updated_at"), "security correction updated_at")
    _require({key: summary.get(key) for key in expected_summary} == expected_summary, "security correction summary configuration mismatch")

    rows = _load_jsonl(results_path, "security correction results")
    _require(len(rows) == 1, "security correction must contain exactly one result row")
    row = rows[0]
    expected_row_keys = {
        "case_unit_dir",
        "case_packet",
        "case_packet_size_bytes",
        "lane",
        "status",
        "attempts",
        "quality_warnings",
        "checklist_path",
    }
    _require(set(row) == expected_row_keys, "security correction result field set mismatch")
    _require(row.get("case_unit_dir") == SECURITY_CASE_ID and row.get("status") == "success", "security correction result identity/status mismatch")
    _require(row.get("case_packet_size_bytes") == packet.stat().st_size, "security correction packet size mismatch")
    _require(row.get("lane") == "regular" and row.get("quality_warnings") == [], "security correction result lane/warnings mismatch")
    _require(row.get("checklist_path") == _repo_relative(case_dir / "checklist.yaml"), "security correction checklist pointer mismatch")
    attempts = row.get("attempts")
    _require(isinstance(attempts, list) and len(attempts) == 1, "security correction must contain one attempt")
    attempt = _mapping(attempts[0], "security correction attempt")
    _require(
        set(attempt)
        == {
            "attempt_index",
            "max_output_tokens",
            "http_timeout_seconds",
            "codex_timeout_seconds",
            "returncode",
            "duration_seconds",
            "stderr_tail",
            "validator",
        },
        "security correction attempt field set mismatch",
    )
    _require(attempt.get("attempt_index") == 1, "security correction attempt index mismatch")
    _require(attempt.get("max_output_tokens") == 12000, "security correction token budget mismatch")
    _require(attempt.get("http_timeout_seconds") == 180, "security correction HTTP timeout mismatch")
    _require(attempt.get("codex_timeout_seconds") == 1800, "security correction Codex timeout mismatch")
    _require(attempt.get("returncode") == 0, "security correction Codex return code mismatch")
    _require(str(attempt.get("validator") or "").startswith("checklist valid:"), "security correction validator provenance mismatch")
    _require(
        all(
            (case_dir / suffix).read_bytes() == (case_dir / f"attempt_01.{suffix}").read_bytes()
            for suffix in EXPECTED_CANONICAL_SUFFIXES
        ),
        "security correction canonical files do not match attempt_01",
    )
    _validate_minimal_codex_sidecars(
        case_id=SECURITY_CASE_ID,
        checklist=checklist_json,
        llm_call=_load_mapping(case_dir / "llm_call.json", "security llm_call"),
        api_response=_load_mapping(case_dir / "api_response.json", "security api_response"),
        reasoning_summary=(case_dir / "reasoning_summary.txt").read_text(encoding="utf-8"),
        attempt_prefix="attempt_01",
        attempt_record=attempt,
    )
    original_hits = _primary_secret_hit_inventory(formal_case_dir)
    _require(
        original_hits == {"api_response.json": 20, "attempt_01.api_response.json": 20},
        "formal security defect inventory drift",
    )
    _require(_secret_hit_count(root) == 0, "security correction round still contains secret-like material")
    normalization = {
        "allowed_changed_fields": ["case_packet"],
        "source_case_packet": row.get("case_packet"),
        "normalized_case_packet": _repo_relative(packet),
    }
    _require(isinstance(normalization["source_case_packet"], str), "security source packet pointer is missing")
    normalized = dict(row)
    normalized["case_packet"] = normalization["normalized_case_packet"]
    _require(normalized["case_packet"] == _repo_relative(packet), "security packet normalization failed")
    return dict(row), normalization


def _validate_legacy_inputs(
    *,
    manifest_path: Path,
    accepted_root: Path,
    round_01_root: Path,
    expected_case_ids: Sequence[str],
) -> None:
    _require_no_symlinks(accepted_root, "legacy accepted cases")
    _require_no_symlinks(round_01_root, "legacy round_01")
    manifest = _load_mapping(manifest_path, "legacy corrections manifest")
    _require(manifest.get("schema_version") == "appworld_draft_corrections.v2", "legacy corrections manifest schema drift")
    _require(manifest.get("correction_count") == 2, "legacy corrections count drift")
    legacy_corrections = manifest.get("corrections")
    _require(isinstance(legacy_corrections, list) and len(legacy_corrections) == 2, "legacy corrections inventory drift")
    _require(
        [item.get("case_unit_id") for item in legacy_corrections if isinstance(item, Mapping)]
        == ["9ef034e_2", SECURITY_CASE_ID],
        "legacy correction case order drift",
    )
    _require(resolve_repo_path(_string(manifest.get("accepted_cases_root"), "legacy accepted root")).resolve() == accepted_root, "legacy accepted root pointer mismatch")
    entries = list(accepted_root.iterdir())
    _require(all(path.is_dir() and not path.is_symlink() for path in entries), "legacy accepted root contains unsupported entries")
    _require({path.name for path in entries} == set(expected_case_ids), "legacy accepted root is not the exact 485-case set")
    round_entries = list(round_01_root.iterdir())
    _require(
        {path.name for path in round_entries} == {"9ef034e_2", "_batch_results.jsonl", "_batch_summary.json"},
        "legacy round_01 inventory mismatch",
    )
    _require(_secret_hit_count(accepted_root) == 0, "legacy accepted overlay contains secret-like material")
    _require(_secret_hit_count(round_01_root) == 0, "legacy round_01 contains secret-like material")
    _require(_secret_file_hit_count(manifest_path) == 0, "legacy corrections manifest contains secret-like material")


def _copy_authoritative_cases(inputs: OverlayInputs, destination: Path) -> None:
    _require(destination.is_dir() and not destination.is_symlink(), "temporary accepted root is invalid")
    _require(not any(destination.iterdir()), "temporary accepted root is not empty")
    for case_id in inputs.expected_case_ids:
        source = _authoritative_source(inputs, case_id)
        before = sha256_path(source)
        shutil.copytree(source, destination / case_id, symlinks=False)
        _require(sha256_path(source) == before, f"authoritative source changed while copying: {case_id}")
        _require(sha256_path(destination / case_id) == before, f"accepted copy differs from authoritative source: {case_id}")


def _authoritative_source(inputs: OverlayInputs, case_id: str) -> Path:
    if case_id in EXPECTED_LOCATION_CASE_SET:
        return inputs.candidate_root / case_id
    if case_id == SECURITY_CASE_ID:
        return inputs.security_case_dir
    return inputs.formal_cases_root / case_id


def _validate_accepted_tree(inputs: OverlayInputs, root: Path) -> None:
    accepted = _input_directory(root, "accepted overlay root")
    _require_no_symlinks(accepted, "accepted overlay root")
    entries = list(accepted.iterdir())
    _require(all(path.is_dir() and not path.is_symlink() for path in entries), "accepted root contains files, symlinks, or unsupported entries")
    _require({path.name for path in entries} == set(inputs.expected_case_ids), "accepted root must contain exactly the frozen 485 case directories")
    _require(len(entries) == EXPECTED_CASE_COUNT, "accepted root case count mismatch")
    for case_id in inputs.expected_case_ids:
        source = _authoritative_source(inputs, case_id)
        _require(sha256_path(accepted / case_id) == sha256_path(source), f"accepted case differs from its authoritative source: {case_id}")
    _require(_secret_hit_count(accepted) == 0, "accepted overlay contains secret-like material")


def _build_manifest(
    inputs: OverlayInputs,
    accepted_root: Path,
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    accepted_inventory = _tree_counts(accepted_root)
    location_corrections = []
    for case_id in EXPECTED_LOCATION_CASE_IDS:
        packet = _input_file(inputs.packet_root / case_id / "case_packet.md", f"case packet {case_id}")
        formal_case = inputs.formal_cases_root / case_id
        source_case = inputs.candidate_root / case_id
        accepted_case = accepted_root / case_id
        row = inputs.candidate_rows_by_id[case_id]
        location_corrections.append(
            {
                "case_unit_id": case_id,
                "reason": (
                    "The formal draft contained one or more support locations that failed strict "
                    "source-local resolution; the frozen isolated candidate passed all repair gates."
                ),
                "case_packet_path": _repo_relative(packet),
                "case_packet_sha256": sha256_file(packet),
                "formal_case_path": _repo_relative(formal_case),
                "formal_case_tree_sha256": sha256_path(formal_case),
                "source_case_path": _repo_relative(source_case),
                "source_case_tree_sha256": sha256_path(source_case),
                "accepted_case_path": _repo_relative(accepted_case),
                "accepted_case_tree_sha256": sha256_path(accepted_case),
                "source_result_row_sha256": sha256_object(row),
                "canonical_file_sha256": _canonical_hashes(source_case, case_id=case_id),
                "secondary_defect": (
                    {
                        "kind": "secret_like_material",
                        "formal_hit_count": 44,
                        "accepted_hit_count": 0,
                    }
                    if case_id == "9ef034e_2"
                    else None
                ),
                "validation": {
                    "candidate_strict_validation_passed": True,
                    "support_locations_resolve": True,
                    "source_and_accepted_byte_equal": True,
                    "formal_case_not_authoritative": True,
                },
            }
        )

    security_packet = _input_file(
        inputs.packet_root / SECURITY_CASE_ID / "case_packet.md",
        "security case packet",
    )
    formal_security = inputs.formal_cases_root / SECURITY_CASE_ID
    accepted_security = accepted_root / SECURITY_CASE_ID
    security_correction = {
        "case_unit_id": SECURITY_CASE_ID,
        "reason": (
            "The formal Codex event sidecars contained secret-like sk-prefixed material; "
            "the audited round_02 regeneration contains zero such matches."
        ),
        "case_packet_path": _repo_relative(security_packet),
        "case_packet_sha256": sha256_file(security_packet),
        "formal_case_path": _repo_relative(formal_security),
        "formal_case_tree_sha256": sha256_path(formal_security),
        "source_case_path": _repo_relative(inputs.security_case_dir),
        "source_case_tree_sha256": sha256_path(inputs.security_case_dir),
        "accepted_case_path": _repo_relative(accepted_security),
        "accepted_case_tree_sha256": sha256_path(accepted_security),
        "source_batch_results_path": _repo_relative(inputs.security_batch_results_path),
        "source_batch_results_sha256": sha256_file(inputs.security_batch_results_path),
        "source_batch_summary_path": _repo_relative(inputs.security_batch_summary_path),
        "source_batch_summary_sha256": sha256_file(inputs.security_batch_summary_path),
        "source_result_row_sha256": sha256_object(inputs.security_result_row),
        "result_normalization": dict(inputs.security_normalization),
        "canonical_file_sha256": _canonical_hashes(inputs.security_case_dir, case_id=SECURITY_CASE_ID),
        "secret_scan": {
            "scanner_schema": SECRET_SCAN_SCHEMA,
            "formal_hit_count": 40,
            "source_hit_count": 0,
            "accepted_hit_count": 0,
        },
        "validation": {
            "codex_generation_valid": True,
            "support_locations_resolve": True,
            "source_and_accepted_byte_equal": True,
            "formal_secret_material_rejected": True,
            "accepted_secret_scan_passed": True,
        },
    }
    manifest = {
        "schema_version": CORRECTIONS_SCHEMA,
        "status": LOCKED_STATUS,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "formal_run": {
            "pre_run_lock_path": _repo_relative(inputs.formal_lock_path),
            "pre_run_lock_sha256": sha256_file(inputs.formal_lock_path),
            "cases_root": _repo_relative(inputs.formal_cases_root),
            "cases_tree_sha256": sha256_path(inputs.formal_cases_root),
            "batch_results_path": _repo_relative(inputs.formal_batch_results_path),
            "batch_results_sha256": sha256_file(inputs.formal_batch_results_path),
            "batch_result_row_count": len(inputs.formal_batch_rows),
            "batch_result_rows_semantic_sha256": sha256_object(list(inputs.formal_batch_rows)),
            "batch_summary_path": _repo_relative(inputs.formal_batch_summary_path),
            "batch_summary_sha256": sha256_file(inputs.formal_batch_summary_path),
        },
        "repair": {
            "lock_path": _repo_relative(inputs.repair_lock_path),
            "lock_sha256": sha256_file(inputs.repair_lock_path),
            "candidate_root": _repo_relative(inputs.candidate_root),
            "candidate_tree_sha256": sha256_path(inputs.candidate_root),
            "candidate_results_path": _repo_relative(inputs.candidate_results_path),
            "candidate_results_sha256": sha256_file(inputs.candidate_results_path),
            "candidate_result_rows_semantic_sha256": sha256_object(list(inputs.candidate_rows)),
            "candidate_summary_path": _repo_relative(inputs.candidate_summary_path),
            "candidate_summary_sha256": sha256_file(inputs.candidate_summary_path),
            "candidate_validation_path": _repo_relative(inputs.candidate_validation_path),
            "candidate_validation_sha256": sha256_file(inputs.candidate_validation_path),
            "candidate_validation_semantic_sha256": sha256_object(inputs.candidate_validation),
        },
        "accepted_overlay": {
            "root": _repo_relative(accepted_root),
            "tree_sha256": sha256_path(accepted_root),
            "file_count": accepted_inventory["file_count"],
            "directory_count": accepted_inventory["directory_count"],
            "size_bytes": accepted_inventory["size_bytes"],
            "case_count": EXPECTED_CASE_COUNT,
            "unchanged_case_count": EXPECTED_UNCHANGED_CASE_COUNT,
            "corrected_case_count": len(EXPECTED_CORRECTED_CASE_SET),
        },
        "corrections": {
            "location_corrections": location_corrections,
            "security_correction": security_correction,
        },
        "security_incident_inventory": {
            "scanner_schema": SECRET_SCAN_SCHEMA,
            "affected_case_ids": ["9ef034e_2", SECURITY_CASE_ID],
            "formal_hits_by_case": {"9ef034e_2": 44, SECURITY_CASE_ID: 40},
            "formal_hit_count": 84,
            "accepted_hit_count": 0,
            "credential_values_recorded": False,
        },
        "validation": {
            "location_case_ids": list(EXPECTED_LOCATION_CASE_IDS),
            "location_case_ids_semantic_sha256": sha256_object(list(EXPECTED_LOCATION_CASE_IDS)),
            "security_case_id": SECURITY_CASE_ID,
            "exact_485_accepted_case_dirs": True,
            "formal_batch_immutable_exact_485": True,
            "location_candidate_validation_passed": True,
            "accepted_cases_match_authoritative_sources": True,
            "formal_secret_case_ids": ["9ef034e_2", SECURITY_CASE_ID],
            "formal_secret_hit_count": 84,
            "accepted_secret_hit_count": 0,
            "draft_lifecycle_status": "draft_generated/review_required",
            "human_review_completed": False,
        },
        "superseded_overlay": {
            "status": "superseded_not_authoritative",
            "legacy_manifest_path": _repo_relative(inputs.legacy_manifest_path),
            "legacy_manifest_sha256": sha256_file(inputs.legacy_manifest_path),
            "legacy_accepted_cases_root": _repo_relative(inputs.legacy_accepted_root),
            "legacy_accepted_cases_tree_sha256": sha256_path(inputs.legacy_accepted_root),
            "round_01": {
                "root": _repo_relative(inputs.round_01_root),
                "tree_sha256": sha256_path(inputs.round_01_root),
                "case_ids": ["9ef034e_2"],
                "case_ids_semantic_sha256": sha256_object(["9ef034e_2"]),
            },
            "round_02": {
                "root": _repo_relative(inputs.security_root),
                "tree_sha256": sha256_path(inputs.security_root),
                "case_ids": [SECURITY_CASE_ID],
                "case_ids_semantic_sha256": sha256_object([SECURITY_CASE_ID]),
            },
        },
    }
    _validate_manifest_shape(manifest)
    return manifest


def _validate_manifest_shape(manifest: Mapping[str, Any]) -> None:
    _require(set(manifest) == _TOP_LEVEL_KEYS, "corrections manifest top-level field set mismatch")
    _require(manifest.get("schema_version") == CORRECTIONS_SCHEMA, "corrections manifest schema mismatch")
    _require(manifest.get("status") == LOCKED_STATUS, "corrections manifest status mismatch")
    _require(set(_mapping(manifest.get("formal_run"), "formal_run")) == _FORMAL_RUN_KEYS, "formal_run field set mismatch")
    _require(set(_mapping(manifest.get("repair"), "repair")) == _REPAIR_KEYS, "repair field set mismatch")
    _require(set(_mapping(manifest.get("accepted_overlay"), "accepted_overlay")) == _ACCEPTED_OVERLAY_KEYS, "accepted_overlay field set mismatch")
    corrections = _mapping(manifest.get("corrections"), "corrections")
    _require(set(corrections) == {"location_corrections", "security_correction"}, "corrections field set mismatch")
    locations = corrections.get("location_corrections")
    _require(isinstance(locations, list) and len(locations) == 12, "location corrections must contain exactly 12 entries")
    _require([item.get("case_unit_id") for item in locations if isinstance(item, Mapping)] == list(EXPECTED_LOCATION_CASE_IDS), "location correction order mismatch")
    for item in locations:
        location = _mapping(item, "location correction")
        _require(set(location) == _LOCATION_CORRECTION_KEYS, "location correction field set mismatch")
        _require(set(_mapping(location.get("validation"), "location validation")) == _LOCATION_VALIDATION_KEYS, "location validation field set mismatch")
        _require(set(_mapping(location.get("canonical_file_sha256"), "location canonical hashes")) == set(EXPECTED_CANONICAL_SUFFIXES), "location canonical hash field set mismatch")
    security = _mapping(corrections.get("security_correction"), "security correction")
    _require(set(security) == _SECURITY_CORRECTION_KEYS, "security correction field set mismatch")
    _require(set(_mapping(security.get("validation"), "security validation")) == _SECURITY_VALIDATION_KEYS, "security validation field set mismatch")
    _require(set(_mapping(security.get("canonical_file_sha256"), "security canonical hashes")) == set(EXPECTED_CANONICAL_SUFFIXES), "security canonical hash field set mismatch")
    _require(
        set(_mapping(manifest.get("security_incident_inventory"), "security_incident_inventory"))
        == _SECURITY_INCIDENT_KEYS,
        "security_incident_inventory field set mismatch",
    )
    _require(set(_mapping(manifest.get("validation"), "validation")) == _VALIDATION_KEYS, "validation field set mismatch")
    superseded = _mapping(manifest.get("superseded_overlay"), "superseded_overlay")
    _require(set(superseded) == _SUPERSEDED_KEYS, "superseded_overlay field set mismatch")
    _require(set(_mapping(superseded.get("round_01"), "superseded round_01")) == _SUPERSEDED_ROUND_KEYS, "superseded round_01 field set mismatch")
    _require(set(_mapping(superseded.get("round_02"), "superseded round_02")) == _SUPERSEDED_ROUND_KEYS, "superseded round_02 field set mismatch")


def _canonical_hashes(case_dir: Path, *, case_id: str) -> dict[str, str]:
    return {
        suffix: sha256_file(_input_file(case_dir / suffix, f"{case_id} canonical {suffix}"))
        for suffix in EXPECTED_CANONICAL_SUFFIXES
    }


def _tree_counts(root: Path) -> dict[str, int]:
    files = [path for path in root.rglob("*") if path.is_file() and not path.is_symlink()]
    directories = [path for path in root.rglob("*") if path.is_dir() and not path.is_symlink()]
    return {
        "file_count": len(files),
        "directory_count": len(directories),
        "size_bytes": sum(path.stat().st_size for path in files),
    }


def _secret_hit_inventory(root: Path) -> dict[str, int]:
    hits: dict[str, int] = {}
    for path in sorted(value for value in root.rglob("*") if value.is_file() and not value.is_symlink()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ContractLifecycleError(f"draft artifact is not UTF-8 text: {path}") from exc
        count = sum(len(tuple(pattern.finditer(text))) for pattern in _SECRET_PATTERNS)
        if count:
            hits[path.relative_to(root).as_posix()] = count
    return hits


def _primary_secret_hit_inventory(root: Path) -> dict[str, int]:
    patterns = {
        name: pattern
        for name, pattern in _SECRET_PATTERN_DEFINITIONS
    }
    _require("openai_or_openrouter_sk" in patterns, "primary secret scanner pattern is unavailable")
    pattern = patterns["openai_or_openrouter_sk"]
    hits: dict[str, int] = {}
    for path in sorted(value for value in root.rglob("*") if value.is_file() and not value.is_symlink()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ContractLifecycleError(f"draft artifact is not UTF-8 text: {path}") from exc
        count = len(tuple(pattern.finditer(text)))
        if count:
            hits[path.relative_to(root).as_posix()] = count
    return hits


def _secret_hit_count(root: Path) -> int:
    return sum(_secret_hit_inventory(root).values())


def _secret_text_hit_count(text: str) -> int:
    return sum(len(tuple(pattern.finditer(text))) for pattern in _SECRET_PATTERNS)


def _secret_file_hit_count(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ContractLifecycleError(f"draft artifact is not UTF-8 text: {path}") from exc
    return _secret_text_hit_count(text)


def _assert_immutable_guards(guards: Sequence[tuple[str, Path, str, str]]) -> None:
    for label, path, kind, expected in guards:
        _require(kind in {"file", "tree"}, f"invalid immutable guard kind: {label}")
        observed = sha256_file(path) if kind == "file" else sha256_path(path)
        _require(observed == expected, f"immutable input changed during overlay materialization: {label}")


def _require_no_symlinks(root: Path, label: str) -> None:
    _require(not root.is_symlink(), f"{label} is a symlink")
    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    _require(not symlinks, f"{label} contains symlinks")


def _load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    source = _input_file(path, label)
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(f"{label} line {line_number} is malformed JSON: {exc}") from exc
        _require(isinstance(value, dict), f"{label} line {line_number} is not an object")
        rows.append(value)
    return rows


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> tuple[int, int]:
    _require(not path.exists(), f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.tmp-", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(dict(payload), stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temp_identity = _path_identity(temp_path)
        try:
            os.link(temp_path, path)
        except FileExistsError as exc:
            raise ContractLifecycleError(f"refusing to overwrite artifact: {path}") from exc
        _require(_path_identity(path) == temp_identity, "exclusive manifest link identity mismatch")
        return temp_identity
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _acquire_exclusive_lock(path: Path) -> tuple[int, int]:
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ContractLifecycleError(f"overlay materialization lock already exists: {path}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write("appworld_draft_overlay_materialization\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        if path.exists():
            path.unlink()
        raise
    return _path_identity(path)


def _path_identity(path: Path) -> tuple[int, int]:
    stat = path.stat(follow_symlinks=False)
    return stat.st_dev, stat.st_ino


def _unlink_if_same(path: Path, identity: tuple[int, int]) -> None:
    try:
        if _path_identity(path) == identity and path.is_file() and not path.is_symlink():
            path.unlink()
    except FileNotFoundError:
        return


def _rmtree_if_same(path: Path, identity: tuple[int, int]) -> None:
    try:
        same = _path_identity(path) == identity
    except FileNotFoundError:
        return
    if same and path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)


def _input_file(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path).resolve()
    _require(resolved.is_file() and not resolved.is_symlink(), f"{label} is missing, not regular, or symlinked: {resolved}")
    return resolved


def _input_directory(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path).resolve()
    _require(resolved.is_dir() and not resolved.is_symlink(), f"{label} is missing, not a directory, or symlinked: {resolved}")
    return resolved


def _load_mapping(path: str | Path, label: str) -> dict[str, Any]:
    source = _input_file(path, label)
    try:
        if source.suffix in {".yaml", ".yml"}:
            value = yaml.safe_load(source.read_text(encoding="utf-8"))
        else:
            value = json.loads(source.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, yaml.YAMLError, UnicodeDecodeError) as exc:
        raise ContractLifecycleError(f"failed to parse {label}: {exc}") from exc
    return dict(_mapping(value, label))


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root().resolve()).as_posix()
    except ValueError as exc:
        raise ContractLifecycleError(f"overlay artifact is outside the repository: {resolved}") from exc


def _parse_timestamp(value: Any, label: str) -> datetime:
    text = _string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractLifecycleError(f"{label} is not an ISO timestamp") from exc
    _require(parsed.tzinfo is not None, f"{label} must include a timezone")
    return parsed


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be a mapping")
    return value


def _string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value.strip(), f"{label} must be a nonempty string")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractLifecycleError(message)
