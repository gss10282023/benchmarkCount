"""Fail-closed acceptance gates for the AppWorld 485-case generation run.

This module validates the artifacts emitted by ``neurips_ed_track_minimal``'s
Codex CLI draft path.  Its ``llm_call.json`` check is intentionally a dedicated
minimal-sidecar protocol check.  It does *not* claim that those sidecars satisfy
the evidence system's core ``llm_call`` schema.

Validation is read-only.  The deterministic hash index and acceptance report
are written only through :func:`write_appworld_draft_acceptance`.
"""

from __future__ import annotations

import json
import re
import shlex
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from evidence_system.contracts.appworld_extension import (
    EXPECTED_CHALLENGE_COUNT,
    EXPECTED_EXTENSION_COUNT,
    EXPECTED_NORMAL_EXTENSION_COUNT,
    validate_extension_packets,
    validate_extension_source_bundle,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from neurips_ed_track_minimal.checklist_guardrails import (
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts import draft_case_checklist as minimal_drafter


DEFAULT_DRAFT_ROOT = Path(
    "experiments/appworld_full_test_extension_v1/draft_runs/codex-gpt-5.4-high-support-v2"
)
DEFAULT_LOCK_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_run_lock.json"
DEFAULT_CASES_ROOT = DEFAULT_DRAFT_ROOT / "cases"
DEFAULT_ACCEPTED_CASES_ROOT = DEFAULT_DRAFT_ROOT / "accepted_cases"
DEFAULT_CORRECTIONS_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_corrections.json"
LOCATION_REPAIR_ACCEPTED_CASES_ROOT = DEFAULT_DRAFT_ROOT / "accepted_cases_location_v1"
LOCATION_REPAIR_CORRECTIONS_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_corrections_location_v1.json"
LEGACY_ACCEPTED_CASES_ROOT = DEFAULT_DRAFT_ROOT / "accepted_cases"
LEGACY_CORRECTIONS_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_corrections.json"
DEFAULT_HASH_INDEX_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_generation_hash_index.json"
DEFAULT_ACCEPTANCE_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_generation_acceptance_report.json"
DEFAULT_FINAL_LOCK_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_generation_run_final_lock.json"
DEFAULT_REPAIR_REPORT_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_repair_report.json"

LOCK_SCHEMA = "appworld_draft_run_lock.v2"
HASH_INDEX_SCHEMA = "appworld_draft_hash_index.v1"
ACCEPTANCE_SCHEMA = "appworld_draft_acceptance.v1"
CORRECTIONS_SCHEMA = "appworld_draft_corrections.v2"
LOCATION_REPAIR_CORRECTIONS_SCHEMA = "appworld_draft_corrections_location.v1"
LEGACY_CORRECTIONS_SCHEMA = "appworld_draft_corrections.v2"
FINAL_LOCK_SCHEMA = "appworld_draft_run_final_lock.v1"
REPAIR_REPORT_SCHEMA = "appworld_draft_repair_report.v1"
REPAIR_LOCK_SCHEMA = "appworld_draft_repair_lock.v1"
EXPECTED_REPAIR_CASE_COUNT = 12
EXPECTED_EXPERIMENT_ID = "appworld_full_test_extension_v1"
EXPECTED_DRAFT_RUN_ID = "appworld-extension-485-codex-gpt-5.4-high-support-v2"
EXPECTED_MODEL = "gpt-5.4"
EXPECTED_REASONING_EFFORT = "high"
EXPECTED_MODEL_VERBOSITY = "low"
EXPECTED_TOKEN_BUDGETS = (12000, 16000, 20000)
EXPECTED_CORRECTION_CASE_IDS = ("9ef034e_2", "dac78d9_3")
EXPECTED_INVALID_ORIGINAL_POINTER = "official/dbs/supervisor.jsonl::18"
EXPECTED_INVALID_ORIGINAL_POINTER = "official/dbs/supervisor.jsonl::18"
EXPECTED_REPAIR_CASE_IDS = (
    "652485c_2",
    "d9987f6_1",
    "f6be291_3",
    "432dc7a_1",
    "efc3cea_3",
    "fa327a6_1",
    "9ef034e_2",
    "ba46d91_2",
    "d8e490b_3",
    "a53a8fd_3",
    "4ac4a8d_2",
    "af84964_2",
)
EXPECTED_REPAIR_CASE_SET = frozenset(EXPECTED_REPAIR_CASE_IDS)
EXPECTED_SECURITY_CORRECTION_CASE_ID = "dac78d9_3"
EXPECTED_CORRECTED_CASE_SET = EXPECTED_REPAIR_CASE_SET | {
    EXPECTED_SECURITY_CORRECTION_CASE_ID
}
EXPECTED_CANONICAL_SUFFIXES = (
    "api_response.json",
    "checklist.json",
    "checklist.yaml",
    "llm_call.json",
    "reasoning_summary.txt",
    "stderr.log",
    "stdout.log",
)
_ATTEMPT_STAGE_SUFFIXES = (
    "api_response.json",
    "reasoning_summary.txt",
    "llm_call.json",
    "checklist.yaml",
    "checklist.json",
)
_ATTEMPT_LOG_SUFFIXES = frozenset({"stderr.log", "stdout.log"})
_ROOT_BATCH_FILES = frozenset({"_batch_results.jsonl", "_batch_summary.json"})
_ATTEMPT_FILE_RE = re.compile(
    r"^attempt_(?P<index>[0-9]{2})\.(?P<suffix>"
    + "|".join(re.escape(value) for value in EXPECTED_CANONICAL_SUFFIXES)
    + r")$"
)
_SECRET_PATTERN_DEFINITIONS = (
    (
        "quoted_provider_api_key",
        re.compile(
            r"(?i)(?:\"|')?(?:OPENAI|OPENROUTER|ANTHROPIC)_API_KEY(?:\"|')?"
            r"\s*[:=]\s*(?:\"|')?[^\s\"']{20,}"
        ),
    ),
    (
        "authorization_bearer",
        re.compile(
            r"(?i)(?:\"|')?Authorization(?:\"|')?\s*:\s*(?:\"|')?Bearer\s+"
            r"[A-Za-z0-9._~-]{20,}"
        ),
    ),
    ("openai_or_openrouter_sk", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("slack_token", re.compile(r"\bxox(?:b|p|a|r|s)-[A-Za-z0-9-]{20,}\b")),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("stripe_live_secret", re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b")),
    (
        "pem_private_key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ),
)
_SECRET_PATTERNS = tuple(pattern for _, pattern in _SECRET_PATTERN_DEFINITIONS)

_IMPLEMENTATION_PATHS = {
    "run_draft_batch.py": Path("neurips_ed_track_minimal/scripts/run_draft_batch.py"),
    "draft_case_checklist.py": Path("neurips_ed_track_minimal/scripts/draft_case_checklist.py"),
    "draft_case_checklist.prompt.md": Path("neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md"),
    "draft_source_pointer_strict_v2.supplement.md": Path(
        "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md"
    ),
    "case_checklist.schema.json": Path("neurips_ed_track_minimal/schemas/case_checklist.schema.json"),
    "case_checklist.template.yaml": Path("neurips_ed_track_minimal/templates/case_checklist.template.yaml"),
    "checklist_guardrails.py": Path("neurips_ed_track_minimal/checklist_guardrails.py"),
    # New locks may include this thin official validator as well.  Old locks did
    # not, so it is known but not part of the legacy required subset.
    "checklist_validator.py": Path("neurips_ed_track_minimal/scripts/checklist_validator.py"),
}
_REQUIRED_IMPLEMENTATION_KEYS = frozenset(
    {
        "run_draft_batch.py",
        "draft_case_checklist.py",
        "draft_case_checklist.prompt.md",
        "draft_source_pointer_strict_v2.supplement.md",
        "effective_composed_prompt_sha256",
        "case_checklist.schema.json",
        "case_checklist.template.yaml",
        "checklist_guardrails.py",
        "checklist_validator.py",
    }
)


def validate_appworld_draft_run(
    *,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
    cases_root: str | Path | None = None,
    accepted_cases_root: str | Path | None = None,
    corrections_path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate the immutable formal run plus the locked accepted overlay."""

    report, _ = _validate_appworld_draft_run(
        lock_path=lock_path,
        cases_root=cases_root,
        accepted_cases_root=accepted_cases_root,
        corrections_path=corrections_path,
    )
    return report


def write_appworld_draft_acceptance(
    *,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
    cases_root: str | Path | None = None,
    accepted_cases_root: str | Path | None = None,
    corrections_path: str | Path | None = None,
    hash_index_path: str | Path | None = None,
    report_path: str | Path | None = None,
    final_lock_path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate, then write the hash index, report, and post-run lock.

    All outputs are constrained to the lock's ``provenance`` directory.  No
    formal, correction-candidate, or accepted draft artifact is modified.
    """

    lock_file = _input_file(lock_path, "draft run lock")
    provenance_root = lock_file.parent.resolve()
    index_file = _provenance_output(
        hash_index_path or provenance_root / DEFAULT_HASH_INDEX_PATH.name,
        provenance_root=provenance_root,
        label="draft hash index",
    )
    report_file = _provenance_output(
        report_path or provenance_root / DEFAULT_ACCEPTANCE_PATH.name,
        provenance_root=provenance_root,
        label="draft acceptance report",
    )
    final_lock_file = _provenance_output(
        final_lock_path or provenance_root / DEFAULT_FINAL_LOCK_PATH.name,
        provenance_root=provenance_root,
        label="draft final lock",
    )
    output_files = {index_file, report_file, final_lock_file}
    _require(len(output_files) == 3, "draft hash index, acceptance report, and final lock paths must differ")
    _require(lock_file not in output_files, "acceptance outputs must not overwrite the pre-run lock")

    report, hash_index = _validate_appworld_draft_run(
        lock_path=lock_file,
        cases_root=cases_root,
        accepted_cases_root=accepted_cases_root,
        corrections_path=corrections_path,
    )
    _write_json_atomic(index_file, hash_index)
    report = {
        **report,
        "draft_hash_index_path": _repo_relative(index_file),
        "draft_hash_index_file_sha256": sha256_file(index_file),
        "artifacts_written": True,
    }
    _write_json_atomic(report_file, report)
    final_lock = {
        "schema_version": FINAL_LOCK_SCHEMA,
        "status": "locked_post_acceptance",
        "draft_lifecycle_status": "draft_generated/review_required",
        "human_review_completed": False,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "pre_run_lock": {
            "path": _repo_relative(lock_file),
            "sha256": sha256_file(lock_file),
        },
        "corrections_manifest": {
            "path": report["corrections"]["manifest_path"],
            "sha256": report["corrections"]["manifest_sha256"],
        },
        "formal_batch": {
            "summary_path": report["batch"]["batch_summary_path"],
            "summary_sha256": report["batch"]["batch_summary_sha256"],
            "results_path": report["batch"]["batch_results_jsonl_path"],
            "results_sha256": report["batch"]["batch_results_jsonl_sha256"],
        },
        "accepted_cases": {
            "root": report["accepted_materialization"]["root"],
            "case_count": EXPECTED_EXTENSION_COUNT,
            "test_normal_count": EXPECTED_NORMAL_EXTENSION_COUNT,
            "test_challenge_count": EXPECTED_CHALLENGE_COUNT,
            "file_count": report["accepted_materialization"]["file_count"],
            "directory_count": report["accepted_materialization"]["directory_count"],
            "size_bytes": report["accepted_materialization"]["size_bytes"],
            "tree_sha256": report["accepted_materialization"]["tree_sha256"],
        },
        "acceptance_validator": report["acceptance_validator"],
        "draft_hash_index": {
            "path": _repo_relative(index_file),
            "file_sha256": sha256_file(index_file),
            "content_sha256": report["draft_hash_index_content_sha256"],
        },
        "acceptance_report": {
            "path": _repo_relative(report_file),
            "sha256": sha256_file(report_file),
        },
    }
    _write_json_atomic(final_lock_file, final_lock)
    final_lock_audit = validate_appworld_draft_final_lock(
        final_lock_path=final_lock_file,
        lock_path=lock_file,
    )
    return {
        **report,
        "report_path": _repo_relative(report_file),
        "report_sha256": sha256_file(report_file),
        "final_lock_path": _repo_relative(final_lock_file),
        "final_lock_sha256": sha256_file(final_lock_file),
        "final_lock": final_lock_audit,
        "artifacts_written": True,
    }


def validate_appworld_draft_final_lock(
    *,
    final_lock_path: str | Path = DEFAULT_FINAL_LOCK_PATH,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
) -> dict[str, Any]:
    """Recompute every file binding in an already-written post-run lock."""

    pre_run_lock = _input_file(lock_path, "draft pre-run lock")
    final_lock_file = _input_file(final_lock_path, "draft final lock")
    _require(
        final_lock_file.parent == pre_run_lock.parent and final_lock_file.name == DEFAULT_FINAL_LOCK_PATH.name,
        "draft final lock must be provenance/draft_run_final_lock.json beside the pre-run lock",
    )
    payload = _load_mapping(final_lock_file, "draft final lock")
    _require(
        set(payload)
        == {
            "schema_version",
            "status",
            "draft_lifecycle_status",
            "human_review_completed",
            "created_at",
            "draft_run_id",
            "pre_run_lock",
            "corrections_manifest",
            "formal_batch",
            "accepted_cases",
            "acceptance_validator",
            "draft_hash_index",
            "acceptance_report",
        },
        "final lock field set mismatch",
    )
    _require(payload.get("schema_version") == FINAL_LOCK_SCHEMA, f"final lock schema must be {FINAL_LOCK_SCHEMA}")
    _require(payload.get("status") == "locked_post_acceptance", "final lock status mismatch")
    _require(payload.get("draft_lifecycle_status") == "draft_generated/review_required", "final lock lifecycle mismatch")
    _require(payload.get("human_review_completed") is False, "final lock must not claim completed human review")
    _parse_iso_timestamp(payload.get("created_at"), "final lock created_at")
    _require(payload.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID, "final lock draft_run_id mismatch")

    pre_ref = _mapping(payload.get("pre_run_lock"), "final lock pre_run_lock")
    _require(set(pre_ref) == {"path", "sha256"}, "final lock pre_run_lock field set mismatch")
    _require(pre_ref.get("path") == _repo_relative(pre_run_lock), "final lock pre-run path mismatch")
    _require(pre_ref.get("sha256") == sha256_file(pre_run_lock), "final lock pre-run hash mismatch")

    corrections_ref = _mapping(payload.get("corrections_manifest"), "final lock corrections_manifest")
    _require(set(corrections_ref) == {"path", "sha256"}, "final lock corrections_manifest field set mismatch")
    corrections_file = _input_file(_string(corrections_ref.get("path"), "corrections manifest path"), "corrections manifest")
    _require(corrections_file.parent == pre_run_lock.parent, "final lock corrections manifest must stay in provenance")
    _require(corrections_ref.get("sha256") == sha256_file(corrections_file), "final lock corrections hash mismatch")

    formal_batch = _mapping(payload.get("formal_batch"), "final lock formal_batch")
    _require(
        set(formal_batch) == {"summary_path", "summary_sha256", "results_path", "results_sha256"},
        "final lock formal_batch field set mismatch",
    )
    for path_key, hash_key, label in (
        ("summary_path", "summary_sha256", "formal batch summary"),
        ("results_path", "results_sha256", "formal batch results"),
    ):
        file = _input_file(_string(formal_batch.get(path_key), f"formal_batch.{path_key}"), label)
        _require(formal_batch.get(hash_key) == sha256_file(file), f"final lock {label} hash mismatch")

    accepted = _mapping(payload.get("accepted_cases"), "final lock accepted_cases")
    _require(
        set(accepted)
        == {
            "root",
            "case_count",
            "test_normal_count",
            "test_challenge_count",
            "file_count",
            "directory_count",
            "size_bytes",
            "tree_sha256",
        },
        "final lock accepted_cases field set mismatch",
    )
    accepted_root = resolve_repo_path(_string(accepted.get("root"), "accepted_cases.root")).resolve()
    _require(accepted_root.is_dir() and not accepted_root.is_symlink(), "final lock accepted root is missing or symlinked")
    tree = _tree_inventory(accepted_root)
    _require(accepted.get("case_count") == EXPECTED_EXTENSION_COUNT, "final lock accepted case count mismatch")
    _require(accepted.get("test_normal_count") == EXPECTED_NORMAL_EXTENSION_COUNT, "final lock normal count mismatch")
    _require(accepted.get("test_challenge_count") == EXPECTED_CHALLENGE_COUNT, "final lock challenge count mismatch")
    for key in ("file_count", "directory_count", "size_bytes", "tree_sha256"):
        _require(accepted.get(key) == tree[key], f"final lock accepted {key} mismatch")

    validator_ref = _mapping(payload.get("acceptance_validator"), "final lock acceptance_validator")
    _validate_acceptance_validator_hashes(validator_ref)

    hash_ref = _mapping(payload.get("draft_hash_index"), "final lock draft_hash_index")
    _require(set(hash_ref) == {"path", "file_sha256", "content_sha256"}, "final lock draft_hash_index field set mismatch")
    hash_file = _input_file(_string(hash_ref.get("path"), "draft_hash_index.path"), "draft hash index")
    _require(
        hash_file.parent == pre_run_lock.parent and hash_file.name == DEFAULT_HASH_INDEX_PATH.name,
        "draft hash index must be provenance/draft_hash_index.json",
    )
    _require(hash_ref.get("file_sha256") == sha256_file(hash_file), "final lock hash-index file hash mismatch")
    hash_payload = _load_mapping(hash_file, "draft hash index")
    _require(hash_ref.get("content_sha256") == sha256_object(hash_payload), "final lock hash-index content hash mismatch")

    report_ref = _mapping(payload.get("acceptance_report"), "final lock acceptance_report")
    _require(set(report_ref) == {"path", "sha256"}, "final lock acceptance_report field set mismatch")
    report_file = _input_file(_string(report_ref.get("path"), "acceptance_report.path"), "draft acceptance report")
    _require(
        report_file.parent == pre_run_lock.parent and report_file.name == DEFAULT_ACCEPTANCE_PATH.name,
        "draft acceptance report must be provenance/draft_acceptance_report.json",
    )
    _require(report_ref.get("sha256") == sha256_file(report_file), "final lock acceptance report hash mismatch")
    report = _load_mapping(report_file, "draft acceptance report")
    _require(report.get("status") == "accepted" and report.get("all_hard_gates_passed") is True, "locked report is not accepted")
    _require(report.get("draft_lifecycle_status") == "draft_generated/review_required", "locked report lifecycle mismatch")
    _require(report.get("draft_hash_index_file_sha256") == sha256_file(hash_file), "report/hash-index binding mismatch")
    _require(report.get("accepted_materialization", {}).get("tree_sha256") == tree["tree_sha256"], "report/accepted-tree binding mismatch")

    # Re-run the entire fail-closed validator so the final lock covers the
    # transitive closure of packet, correction-candidate, batch, sidecar, and
    # accepted-case inputs rather than merely their immediate manifest files.
    fresh_report, fresh_hash_index = _validate_appworld_draft_run(
        lock_path=pre_run_lock,
        cases_root=None,
        accepted_cases_root=accepted_root,
        corrections_path=corrections_file,
    )
    _require(fresh_hash_index == hash_payload, "locked draft hash index differs from a fresh full validation")
    stored_core_report = dict(report)
    stored_core_report.pop("draft_hash_index_path", None)
    stored_core_report.pop("draft_hash_index_file_sha256", None)
    stored_core_report["artifacts_written"] = False
    _require(stored_core_report == fresh_report, "locked acceptance report differs from a fresh full validation")
    _require(
        fresh_report["corrections"]["manifest_sha256"] == corrections_ref["sha256"],
        "fresh correction audit differs from the final lock",
    )
    _require(
        fresh_report["batch"]["batch_summary_sha256"] == formal_batch["summary_sha256"]
        and fresh_report["batch"]["batch_results_jsonl_sha256"] == formal_batch["results_sha256"],
        "fresh formal batch audit differs from the final lock",
    )
    _require(
        fresh_report["batch"]["batch_summary_path"] == formal_batch["summary_path"]
        and fresh_report["batch"]["batch_results_jsonl_path"] == formal_batch["results_path"],
        "fresh formal batch paths differ from the final lock",
    )
    return {
        "schema_version": FINAL_LOCK_SCHEMA,
        "status": "verified",
        "draft_lifecycle_status": "draft_generated/review_required",
        "final_lock_path": _repo_relative(final_lock_file),
        "final_lock_sha256": sha256_file(final_lock_file),
        "accepted_cases_tree_sha256": tree["tree_sha256"],
        "all_file_bindings_verified": True,
    }


def _validate_appworld_draft_run(
    *,
    lock_path: str | Path,
    cases_root: str | Path | None,
    accepted_cases_root: str | Path | None,
    corrections_path: str | Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    lock_file = _input_file(lock_path, "draft run lock")
    lock = _load_mapping(lock_file, "draft run lock")
    locked_cases_root = resolve_repo_path(_string(lock.get("execution", {}).get("output_root"), "execution.output_root"))
    formal_cases_root = resolve_repo_path(cases_root).resolve() if cases_root is not None else locked_cases_root.resolve()
    accepted_root = resolve_repo_path(accepted_cases_root or DEFAULT_ACCEPTED_CASES_ROOT).resolve()
    corrections_file = _input_file(corrections_path or DEFAULT_CORRECTIONS_PATH, "draft corrections manifest")
    _require(formal_cases_root == locked_cases_root.resolve(), "formal cases root must equal the lock's execution.output_root")
    _require(formal_cases_root.is_dir(), f"formal draft cases root is missing: {formal_cases_root}")
    _require(not formal_cases_root.is_symlink(), f"formal draft cases root must not be a symlink: {formal_cases_root}")
    _require(accepted_root.is_dir(), f"accepted draft cases root is missing: {accepted_root}")
    _require(not accepted_root.is_symlink(), f"accepted draft cases root must not be a symlink: {accepted_root}")
    _require(accepted_root != formal_cases_root, "accepted materialization must be separate from the immutable formal run")

    lock_audit = _validate_lock(lock_file=lock_file, lock=lock, cases_root=formal_cases_root)
    input_audit, manifest_cases = _validate_locked_inputs(lock)
    expected_ids = [case["case_unit_id"] for case in manifest_cases]
    packet_root = resolve_repo_path(_string(lock["inputs"]["case_packet_root"], "inputs.case_packet_root"))
    _validate_no_symlinks(formal_cases_root)
    batch_audit, histories, authoritative_rows = _validate_batch_artifacts(
        cases_root=formal_cases_root,
        expected_ids=expected_ids,
        lock=lock,
        repair_report_path=lock_file.parent / DEFAULT_REPAIR_REPORT_PATH.name,
        formal_lock_path=lock_file,
    )
    corrections_audit, correction_histories, correction_rows = _validate_generation_corrections_overlay(
        corrections_file=corrections_file,
        lock_file=lock_file,
        formal_cases_root=formal_cases_root,
        accepted_cases_root=accepted_root,
        expected_ids=expected_ids,
        packet_root=packet_root,
        lock=lock,
    )

    schema = _load_mapping(
        resolve_repo_path(_IMPLEMENTATION_PATHS["case_checklist.schema.json"]),
        "official case checklist schema",
    )
    validator = Draft202012Validator(schema)
    case_entries: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    canonical_file_count = 0
    attempt_file_count = 0
    successful_attempt_counts: Counter[int] = Counter()
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_reasoning_tokens = 0
    total_tokens = 0

    for case in manifest_cases:
        case_id = case["case_unit_id"]
        split_counts[case["dataset_name"]] += 1
        result_history = correction_histories.get(case_id, histories[case_id])
        authoritative_row = correction_rows.get(case_id, authoritative_rows[case_id])
        case_entry, usage = _validate_case_draft(
            case=case,
            case_dir=accepted_root / case_id,
            packet_path=packet_root / case_id / "case_packet.md",
            result_history=result_history,
            authoritative_row=authoritative_row,
            lock=lock,
            validator=validator,
        )
        repair_entry = batch_audit["repair_provenance"]["latest_repairs_by_case"].get(case_id)
        if repair_entry is not None:
            _require(
                case_entry["canonical_files"] == repair_entry["canonical_file_sha256"],
                f"{case_id} canonical files differ from the locked latest repair",
            )
        case_entries.append(case_entry)
        canonical_file_count += len(case_entry["canonical_files"])
        attempt_file_count += len(case_entry["attempt_files"])
        successful_attempt_counts[int(case_entry["successful_attempt_index"])] += 1
        total_prompt_tokens += usage["prompt_tokens"]
        total_completion_tokens += usage["completion_tokens"]
        total_reasoning_tokens += usage["reasoning_tokens"]
        total_tokens += usage["total_tokens"]

    _require(
        dict(split_counts) == {
            "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
            "test_challenge": EXPECTED_CHALLENGE_COUNT,
        },
        f"draft split counts mismatch: {dict(split_counts)}",
    )
    _require(canonical_file_count == EXPECTED_EXTENSION_COUNT * len(EXPECTED_CANONICAL_SUFFIXES), "canonical file count mismatch")

    hash_index = {
        "schema_version": HASH_INDEX_SCHEMA,
        "lock_path": _repo_relative(lock_file),
        "lock_sha256": sha256_file(lock_file),
        "manifest_path": input_audit["manifest_path"],
        "manifest_sha256": input_audit["manifest_sha256"],
        "formal_cases_root": _repo_relative(formal_cases_root),
        "accepted_cases_root": _repo_relative(accepted_root),
        "accepted_cases_tree_sha256": corrections_audit["accepted_cases_tree_sha256"],
        "corrections_manifest_path": corrections_audit["manifest_path"],
        "corrections_manifest_sha256": corrections_audit["manifest_sha256"],
        "case_count": EXPECTED_EXTENSION_COUNT,
        "canonical_file_count": canonical_file_count,
        "attempt_file_count": attempt_file_count,
        "batch_summary_sha256": batch_audit["batch_summary_sha256"],
        "batch_results_jsonl_sha256": batch_audit["batch_results_jsonl_sha256"],
        "acceptance_validator": _acceptance_validator_hashes(),
        "cases": case_entries,
    }
    index_content_sha256 = sha256_object(hash_index)
    report = {
        "schema_version": ACCEPTANCE_SCHEMA,
        "status": "accepted",
        "draft_lifecycle_status": "draft_generated/review_required",
        "all_hard_gates_passed": True,
        "lock_path": _repo_relative(lock_file),
        "lock_sha256": sha256_file(lock_file),
        "formal_cases_root": _repo_relative(formal_cases_root),
        "cases_root": _repo_relative(accepted_root),
        "accepted_materialization": {
            "root": _repo_relative(accepted_root),
            "case_count": EXPECTED_EXTENSION_COUNT,
            "unchanged_case_count": EXPECTED_EXTENSION_COUNT - len(correction_rows),
            "corrected_case_count": len(correction_rows),
            "file_count": corrections_audit["accepted_file_count"],
            "directory_count": corrections_audit["accepted_directory_count"],
            "size_bytes": corrections_audit["accepted_size_bytes"],
            "tree_sha256": corrections_audit["accepted_cases_tree_sha256"],
        },
        "corrections": corrections_audit,
        "inputs": input_audit,
        "lock": lock_audit,
        "batch": batch_audit,
        "drafts": {
            "case_count": EXPECTED_EXTENSION_COUNT,
            "case_count_by_dataset": dict(sorted(split_counts.items())),
            "canonical_file_count": canonical_file_count,
            "attempt_file_count": attempt_file_count,
            "successful_attempt_index_counts": {
                str(key): value for key, value in sorted(successful_attempt_counts.items())
            },
            "token_usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "reasoning_tokens": total_reasoning_tokens,
                "total_tokens": total_tokens,
            },
        },
        "llm_call_validation_protocol": {
            "name": "neurips_ed_track_minimal_codex_cli_sidecar.v1",
            "core_llm_call_schema_claimed": False,
            "core_llm_call_schema_invoked": False,
            "provider": "codex_cli",
            "model": EXPECTED_MODEL,
            "reasoning_effort": EXPECTED_REASONING_EFFORT,
            "auth_mode": "codex_login",
            "max_output_tokens_enforced": False,
        },
        "acceptance_validator": _acceptance_validator_hashes(),
        "draft_hash_index_content_sha256": index_content_sha256,
        "artifacts_written": False,
        "checks": {
            "exact_485_manifest_case_directories": True,
            "no_symlinks": True,
            "canonical_yaml_json_semantically_equal": True,
            "case_identity_matches_manifest": True,
            "official_schema_and_guardrails_pass": True,
            "support_paths_in_case_packet_inventory": True,
            "minimal_codex_sidecar_protocol_pass": True,
            "codex_command_and_event_provenance_pass": True,
            "canonical_files_match_one_successful_attempt": True,
            "all_current_attempt_files_inventoried": True,
            "append_aware_latest_per_case_pass": True,
            "targeted_repair_provenance_pass": True,
            "formal_run_preserved_byte_for_byte": True,
            "two_correction_overlay_locked": True,
            "accepted_483_cases_match_formal_run": True,
            "corrected_cases_match_candidates": True,
            "known_invalid_original_pointer_rejected": True,
            "secret_like_event_log_material_removed_by_regeneration": True,
            "locked_inputs_and_implementation_hashes_pass": True,
        },
    }
    return report, hash_index


def _validate_generation_corrections_overlay(
    *,
    corrections_file: Path,
    lock_file: Path,
    formal_cases_root: Path,
    accepted_cases_root: Path,
    expected_ids: Sequence[str],
    packet_root: Path,
    lock: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    """Bind the two audited regenerated cases into a separate accepted tree."""

    provenance_root = lock_file.parent.resolve()
    draft_root = provenance_root.parent.resolve()
    _require(
        corrections_file.parent == provenance_root and corrections_file.name == DEFAULT_CORRECTIONS_PATH.name,
        "corrections manifest must be provenance/draft_corrections.json beside the pre-run lock",
    )
    manifest = _load_mapping(corrections_file, "draft corrections manifest")
    expected_manifest_keys = {
        "schema_version",
        "created_at",
        "pre_run_lock_path",
        "pre_run_lock_sha256",
        "base_cases_root",
        "accepted_cases_root",
        "accepted_cases_tree_sha256",
        "accepted_case_count",
        "unchanged_case_count",
        "correction_count",
        "corrections",
    }
    _require(set(manifest) == expected_manifest_keys, "corrections manifest field set mismatch")
    _require(manifest.get("schema_version") == CORRECTIONS_SCHEMA, f"corrections schema must be {CORRECTIONS_SCHEMA}")
    _parse_iso_timestamp(manifest.get("created_at"), "corrections created_at")
    _require(manifest.get("pre_run_lock_path") == _repo_relative(lock_file), "corrections pre-run lock path mismatch")
    _require(manifest.get("pre_run_lock_sha256") == sha256_file(lock_file), "corrections pre-run lock hash mismatch")
    _require(manifest.get("base_cases_root") == _repo_relative(formal_cases_root), "corrections base cases root mismatch")
    _require(manifest.get("accepted_cases_root") == _repo_relative(accepted_cases_root), "corrections accepted cases root mismatch")
    _require(manifest.get("accepted_case_count") == EXPECTED_EXTENSION_COUNT, "corrections accepted count mismatch")
    _require(
        manifest.get("unchanged_case_count") == EXPECTED_EXTENSION_COUNT - len(EXPECTED_CORRECTION_CASE_IDS),
        "corrections unchanged count mismatch",
    )
    _require(
        manifest.get("correction_count") == len(EXPECTED_CORRECTION_CASE_IDS),
        "correction count mismatch",
    )

    root_entries = list(accepted_cases_root.iterdir())
    actual_dirs = {path.name for path in root_entries if path.is_dir() and not path.is_symlink()}
    unsupported = [path.name for path in root_entries if not path.is_dir() or path.is_symlink()]
    _require(not unsupported, f"accepted cases root contains files, symlinks, or unsupported entries: {sorted(unsupported)}")
    _require(actual_dirs == set(expected_ids), "accepted cases root must contain exactly the 485 manifest directories")
    _validate_no_symlinks(accepted_cases_root)
    accepted_tree = _tree_inventory(accepted_cases_root)
    _require(
        manifest.get("accepted_cases_tree_sha256") == accepted_tree["tree_sha256"],
        "accepted cases tree hash differs from the correction manifest",
    )

    raw_corrections = manifest.get("corrections")
    _require(
        isinstance(raw_corrections, list) and len(raw_corrections) == len(EXPECTED_CORRECTION_CASE_IDS),
        "corrections entry count mismatch",
    )
    correction_audits: list[dict[str, Any]] = []
    correction_histories: dict[str, list[dict[str, Any]]] = {}
    correction_rows: dict[str, dict[str, Any]] = {}
    for index, raw_correction in enumerate(raw_corrections, start=1):
        correction = _mapping(raw_correction, f"correction entry {index}")
        expected_case_id = EXPECTED_CORRECTION_CASE_IDS[index - 1]
        correction_audit, normalized_result = _validate_one_correction(
            correction=correction,
            expected_case_id=expected_case_id,
            expected_round=f"round_{index:02d}",
            draft_root=draft_root,
            formal_cases_root=formal_cases_root,
            accepted_cases_root=accepted_cases_root,
            packet_root=packet_root,
            expected_ids=expected_ids,
            lock=lock,
        )
        correction_audits.append(correction_audit)
        correction_histories[expected_case_id] = [normalized_result]
        correction_rows[expected_case_id] = normalized_result

    unchanged_ids = [value for value in expected_ids if value not in set(EXPECTED_CORRECTION_CASE_IDS)]
    for unchanged_id in unchanged_ids:
        formal_tree = _tree_inventory(formal_cases_root / unchanged_id)
        copied_tree = _tree_inventory(accepted_cases_root / unchanged_id)
        _require(formal_tree == copied_tree, f"accepted unchanged case differs from formal run: {unchanged_id}")

    audit = {
        "schema_version": CORRECTIONS_SCHEMA,
        "manifest_path": _repo_relative(corrections_file),
        "manifest_sha256": sha256_file(corrections_file),
        "correction_count": len(correction_audits),
        "corrected_case_ids": list(EXPECTED_CORRECTION_CASE_IDS),
        "unchanged_case_count": len(unchanged_ids),
        "accepted_cases_tree_sha256": accepted_tree["tree_sha256"],
        "accepted_file_count": accepted_tree["file_count"],
        "accepted_directory_count": accepted_tree["directory_count"],
        "accepted_size_bytes": accepted_tree["size_bytes"],
        "formal_cases_tree_sha256": _tree_inventory(formal_cases_root)["tree_sha256"],
        "corrections": correction_audits,
        "all_483_unchanged_cases_byte_equal": True,
        "corrected_candidates_and_accepted_cases_byte_equal": True,
    }
    return audit, correction_histories, correction_rows


def _validate_one_correction(
    *,
    correction: Mapping[str, Any],
    expected_case_id: str,
    expected_round: str,
    draft_root: Path,
    formal_cases_root: Path,
    accepted_cases_root: Path,
    packet_root: Path,
    expected_ids: Sequence[str],
    lock: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected_keys = {
        "case_unit_id",
        "correction_type",
        "reason",
        "defect_evidence",
        "case_packet_path",
        "case_packet_sha256",
        "base_original_case_path",
        "base_original_case_tree_sha256",
        "correction_source_case_path",
        "correction_source_case_tree_sha256",
        "accepted_case_path",
        "accepted_case_tree_sha256",
        "correction_batch_summary_path",
        "correction_batch_summary_sha256",
        "correction_batch_results_path",
        "correction_batch_results_sha256",
        "result_normalization",
        "generation_configuration",
        "validation",
    }
    _require(set(correction) == expected_keys, f"{expected_case_id} correction field set mismatch")
    case_id = _string(correction.get("case_unit_id"), "correction case_unit_id")
    _require(case_id == expected_case_id, f"correction order/identity mismatch: {case_id}")
    _require(case_id in set(expected_ids), "correction case is outside the frozen manifest")
    expected_type = "invalid_support_pointer" if case_id == "9ef034e_2" else "secret_like_event_log_material"
    _require(correction.get("correction_type") == expected_type, f"{case_id} correction type mismatch")
    _string(correction.get("reason"), f"{case_id} correction reason")

    packet_path = _input_file(correction.get("case_packet_path"), f"{case_id} corrected case packet")
    _require(packet_path == (packet_root / case_id / "case_packet.md").resolve(), f"{case_id} packet path mismatch")
    _require(correction.get("case_packet_sha256") == sha256_file(packet_path), f"{case_id} packet hash mismatch")
    base_case = resolve_repo_path(_string(correction.get("base_original_case_path"), "base original case path")).resolve()
    candidate_case = resolve_repo_path(_string(correction.get("correction_source_case_path"), "correction source case path")).resolve()
    accepted_case = resolve_repo_path(_string(correction.get("accepted_case_path"), "accepted case path")).resolve()
    _require(base_case == formal_cases_root / case_id, f"{case_id} base case path mismatch")
    _require(candidate_case == draft_root / "corrections" / expected_round / case_id, f"{case_id} candidate path mismatch")
    _require(accepted_case == accepted_cases_root / case_id, f"{case_id} accepted case path mismatch")
    for path, label in ((base_case, "base"), (candidate_case, "candidate"), (accepted_case, "accepted")):
        _require(path.is_dir() and not path.is_symlink(), f"{case_id} {label} case is missing or symlinked")
        _validate_no_symlinks(path)
    base_tree = _tree_inventory(base_case)
    candidate_tree = _tree_inventory(candidate_case)
    accepted_tree = _tree_inventory(accepted_case)
    for key, observed in (
        ("base_original_case_tree_sha256", base_tree["tree_sha256"]),
        ("correction_source_case_tree_sha256", candidate_tree["tree_sha256"]),
        ("accepted_case_tree_sha256", accepted_tree["tree_sha256"]),
    ):
        _require(correction.get(key) == observed, f"{case_id} {key} mismatch")
    _require(candidate_tree == accepted_tree, f"{case_id} accepted case is not byte-identical to its candidate")
    _require(base_tree["tree_sha256"] != accepted_tree["tree_sha256"], f"{case_id} correction did not change the case tree")

    defect = _mapping(correction.get("defect_evidence"), f"{case_id} defect evidence")
    if expected_type == "invalid_support_pointer":
        expected_defect = {
            "type": "unresolved_support_pointer",
            "pointer": EXPECTED_INVALID_ORIGINAL_POINTER,
            "original_unresolved_pointer_count": 1,
            "accepted_unresolved_pointer_count": 0,
        }
        _require(dict(defect) == expected_defect, f"{case_id} defect evidence mismatch")
        original_pointers = _iter_support_pointers(_load_mapping(base_case / "checklist.json", f"{case_id} original checklist"))
        accepted_pointers = _iter_support_pointers(_load_mapping(accepted_case / "checklist.json", f"{case_id} accepted checklist"))
        _require(_unresolved_support_pointers(original_pointers, packet_path) == [EXPECTED_INVALID_ORIGINAL_POINTER], "original pointer defect drift")
        _require(_unresolved_support_pointers(accepted_pointers, packet_path) == [], "accepted pointer defect remains unresolved")
    else:
        expected_defect = {
            "type": "secret_like_event_log_material",
            "pattern_class": "configured-secret-pattern-matches",
            "original_hit_count": 84,
            "original_files": {"api_response.json": 42, "attempt_01.api_response.json": 42},
            "accepted_hit_count": 0,
        }
        _require(dict(defect) == expected_defect, f"{case_id} defect evidence mismatch")
        original_hits = _secret_like_hit_inventory(base_case)
        accepted_hits = _secret_like_hit_inventory(accepted_case)
        _require(original_hits == {"api_response.json": 42, "attempt_01.api_response.json": 42}, "original secret-like hit inventory drift")
        _require(accepted_hits == {}, "accepted secret-like material remains")

    summary_path = _input_file(correction.get("correction_batch_summary_path"), f"{case_id} correction summary")
    results_path = _input_file(correction.get("correction_batch_results_path"), f"{case_id} correction results")
    correction_root = candidate_case.parent.resolve()
    _require(summary_path.parent == correction_root and results_path.parent == correction_root, f"{case_id} correction batch paths mismatch")
    _require(correction.get("correction_batch_summary_sha256") == sha256_file(summary_path), f"{case_id} correction summary hash mismatch")
    _require(correction.get("correction_batch_results_sha256") == sha256_file(results_path), f"{case_id} correction results hash mismatch")
    _validate_no_symlinks(correction_root)
    _require(
        {path.name for path in correction_root.iterdir()} == {case_id, "_batch_results.jsonl", "_batch_summary.json"},
        f"{case_id} correction root inventory mismatch",
    )
    summary = _load_mapping(summary_path, f"{case_id} correction batch summary")
    for timestamp_key in ("started_at", "updated_at"):
        _parse_iso_timestamp(summary.get(timestamp_key), f"{case_id} correction summary {timestamp_key}")
    expected_summary = {
        "total_cases": 1,
        "completed_cases": 1,
        "success_cases": 1,
        "skipped_cases": 0,
        "failed_cases": 0,
        "warning_count": 0,
        "provider": "codex",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "codex_sandbox": "read-only",
        "prompt_supplement": "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "sort_by": "size",
        "quality_check": "none",
        "large_case_threshold_bytes": 100000,
        "lane_stats": {
            "regular": {"count": 1, "min_bytes": packet_path.stat().st_size, "max_bytes": packet_path.stat().st_size},
            "oversized": {"count": 0, "min_bytes": 0, "max_bytes": 0},
        },
        "output_root": _repo_relative(correction_root),
    }
    _require(set(summary) == set(expected_summary) | {"started_at", "updated_at"}, f"{case_id} correction summary field set mismatch")
    _require({key: summary.get(key) for key in expected_summary} == expected_summary, f"{case_id} correction summary mismatch")

    result_lines = [line for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    _require(len(result_lines) == 1, f"{case_id} correction results must contain one row")
    try:
        raw_result = dict(_mapping(json.loads(result_lines[0]), f"{case_id} correction result"))
    except json.JSONDecodeError as exc:
        raise ContractLifecycleError(f"{case_id} correction result is malformed JSON: {exc}") from exc
    _require(
        set(raw_result)
        == {"case_unit_dir", "case_packet", "case_packet_size_bytes", "lane", "status", "attempts", "quality_warnings", "checklist_path"},
        f"{case_id} correction result field set mismatch",
    )
    _require(raw_result.get("case_unit_dir") == case_id and raw_result.get("status") == "success", f"{case_id} correction result identity/status mismatch")
    _require(raw_result.get("checklist_path") == _repo_relative(candidate_case / "checklist.yaml"), f"{case_id} correction checklist path mismatch")
    attempts = raw_result.get("attempts")
    _require(isinstance(attempts, list) and len(attempts) == 1, f"{case_id} correction must contain one attempt")
    attempt = _mapping(attempts[0], f"{case_id} correction attempt")
    _require(
        set(attempt) == {"attempt_index", "max_output_tokens", "http_timeout_seconds", "codex_timeout_seconds", "returncode", "duration_seconds", "stderr_tail", "validator"},
        f"{case_id} correction attempt field set mismatch",
    )

    normalization = _mapping(correction.get("result_normalization"), f"{case_id} result normalization")
    _require(set(normalization) == {"allowed_changed_fields", "source_case_packet", "normalized_case_packet"}, f"{case_id} normalization field set mismatch")
    _require(normalization.get("allowed_changed_fields") == ["case_packet"], f"{case_id} may normalize only case_packet")
    _require(raw_result.get("case_packet") == normalization.get("source_case_packet"), f"{case_id} normalization source mismatch")
    _require(normalization.get("normalized_case_packet") == _repo_relative(packet_path), f"{case_id} normalization target mismatch")
    normalized_result = dict(raw_result)
    normalized_result["case_packet"] = normalization["normalized_case_packet"]
    _require(
        [key for key in normalized_result if normalized_result.get(key) != raw_result.get(key)] == ["case_packet"],
        f"{case_id} normalization changed more than case_packet",
    )

    expected_generation = {
        "provider": "codex",
        "llm_call_provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "codex_sandbox": "read-only",
        "prompt_supplement": "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "large_case_threshold_bytes": 100000,
        "regular_codex_timeout_seconds": 1800,
        "oversized_codex_timeout_seconds": 3600,
    }
    _require(dict(_mapping(correction.get("generation_configuration"), f"{case_id} generation configuration")) == expected_generation, f"{case_id} generation configuration mismatch")
    expected_validation = {
        "official_schema_pass": True,
        "packet_allowlist_guardrail_pass": True,
        "all_support_locations_resolve": True,
        "canonical_yaml_json_equal": True,
        "candidate_source_and_accepted_copy_byte_equal": True,
        "no_secret_like_material": True,
    }
    _require(dict(_mapping(correction.get("validation"), f"{case_id} validation")) == expected_validation, f"{case_id} validation claims mismatch")
    _validate_result_row(normalized_result, case_id=case_id, packet_path=packet_path, lock=lock)
    return (
        {
            "case_unit_id": case_id,
            "correction_type": expected_type,
            "defect_evidence": dict(defect),
            "base_original_case_tree_sha256": base_tree["tree_sha256"],
            "correction_source_case_tree_sha256": candidate_tree["tree_sha256"],
            "accepted_case_tree_sha256": accepted_tree["tree_sha256"],
            "correction_batch_summary_sha256": sha256_file(summary_path),
            "correction_batch_results_sha256": sha256_file(results_path),
            "normalized_result_fields": ["case_packet"],
        },
        normalized_result,
    )


def _unresolved_support_pointers(pointers: Sequence[str], packet_path: Path) -> list[str]:
    unresolved: list[str] = []
    for pointer in pointers:
        pointer_path, _, pointer_location = pointer.partition("::")
        pointer_source = packet_path if pointer_path == "case_packet.md" else packet_path.parent / "raw_case" / pointer_path
        if not pointer_source.is_file() or not _support_location_resolves(
            pointer_source,
            pointer_location,
            packet_path=packet_path if pointer_path != "case_packet.md" else None,
            packet_source_path=pointer_path if pointer_path != "case_packet.md" else None,
        ):
            unresolved.append(pointer)
    return unresolved


def _validate_location_corrections_overlay(
    *,
    corrections_file: Path,
    lock_file: Path,
    formal_cases_root: Path,
    accepted_cases_root: Path,
    expected_ids: Sequence[str],
    packet_root: Path,
    lock: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    """Validate the separate immutable 485-run plus 13-case location overlay.

    The formal namespace is never promoted or rewritten.  Twelve location
    repairs are authoritative only from the locked candidate namespace; the
    thirteenth case is the independently regenerated security correction.
    """

    from evidence_system.contracts.appworld_draft_candidate_repair import (
        CANDIDATE_RESULTS_SCHEMA,
        CANDIDATE_SUMMARY_SCHEMA,
        CANDIDATE_VALIDATION_SCHEMA,
        EXPECTED_REPAIR_CASE_IDS as CANDIDATE_REPAIR_CASE_IDS,
        validate_candidate_repair_lock,
        validate_existing_candidates,
    )

    provenance_root = lock_file.parent.resolve()
    draft_root = provenance_root.parent.resolve()
    expected_set = set(expected_ids)
    _require(
        corrections_file.resolve()
        == (provenance_root / "draft_corrections_location_v1.json").resolve(),
        "location corrections manifest must be provenance/draft_corrections_location_v1.json",
    )
    _require(
        accepted_cases_root.resolve()
        == (draft_root / "accepted_cases_location_v1").resolve(),
        "accepted overlay must be accepted_cases_location_v1",
    )
    _require(
        tuple(CANDIDATE_REPAIR_CASE_IDS) == EXPECTED_REPAIR_CASE_IDS,
        "candidate module repair-case contract differs from acceptance",
    )
    _require(EXPECTED_CORRECTED_CASE_SET <= expected_set, "correction case is outside the frozen manifest")

    manifest = _load_mapping(corrections_file, "location corrections manifest")
    top_keys = {
        "schema_version",
        "status",
        "created_at",
        "formal_run",
        "repair",
        "accepted_overlay",
        "corrections",
        "validation",
        "superseded_overlay",
        "security_incident_inventory",
    }
    _require(set(manifest) == top_keys, "location corrections manifest field set mismatch")
    _require(manifest.get("schema_version") == CORRECTIONS_SCHEMA, f"corrections schema must be {CORRECTIONS_SCHEMA}")
    _require(manifest.get("status") == "locked_overlay", "corrections status must be locked_overlay")
    _parse_iso_timestamp(manifest.get("created_at"), "corrections created_at")

    formal_results_path = _input_file(formal_cases_root / "_batch_results.jsonl", "formal batch results")
    formal_summary_path = _input_file(formal_cases_root / "_batch_summary.json", "formal batch summary")
    formal_rows = _load_jsonl_records(formal_results_path, "formal batch results")
    _require(len(formal_rows) == EXPECTED_EXTENSION_COUNT, "formal batch must remain exactly 485 rows")
    _require(
        Counter(str(row.get("status")) for row in formal_rows)
        == Counter({"success": EXPECTED_EXTENSION_COUNT}),
        "formal batch must remain exactly 485 successes",
    )
    _require(
        {str(row.get("case_unit_dir")) for row in formal_rows} == expected_set,
        "formal batch case set differs from the frozen manifest",
    )
    formal_tree_sha256 = sha256_path(formal_cases_root)
    formal_ref = _mapping(manifest.get("formal_run"), "corrections formal_run")
    formal_keys = {
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
    _require(set(formal_ref) == formal_keys, "corrections formal_run field set mismatch")
    expected_formal_ref = {
        "pre_run_lock_path": _repo_relative(lock_file),
        "pre_run_lock_sha256": sha256_file(lock_file),
        "cases_root": _repo_relative(formal_cases_root),
        "cases_tree_sha256": formal_tree_sha256,
        "batch_results_path": _repo_relative(formal_results_path),
        "batch_results_sha256": sha256_file(formal_results_path),
        "batch_result_row_count": EXPECTED_EXTENSION_COUNT,
        "batch_result_rows_semantic_sha256": sha256_object(formal_rows),
        "batch_summary_path": _repo_relative(formal_summary_path),
        "batch_summary_sha256": sha256_file(formal_summary_path),
    }
    _require(dict(formal_ref) == expected_formal_ref, "corrections formal_run binding mismatch")

    repair_lock_path = _input_file(provenance_root / "draft_repair_lock.json", "location repair lock")
    repair_context = validate_candidate_repair_lock(
        repair_lock_path,
        require_clean_candidate_root=False,
    )
    candidate_root = repair_context.candidate_output_root.resolve()
    _require(
        candidate_root == (draft_root / "repair_location_v1/candidates").resolve(),
        "repair candidate root must be repair_location_v1/candidates",
    )
    _require(
        repair_context.formal_cases_root.resolve() == formal_cases_root.resolve()
        and repair_context.formal_cases_tree_sha256 == formal_tree_sha256,
        "repair lock does not bind the immutable formal tree",
    )
    fresh_candidate_validation = validate_existing_candidates(repair_lock_path)
    _require(fresh_candidate_validation.get("status") == "passed", "fresh candidate validation did not pass")
    _require(
        fresh_candidate_validation.get("passed_case_ids") == list(EXPECTED_REPAIR_CASE_IDS),
        "fresh candidate validation case order/set mismatch",
    )

    candidate_results_path = _input_file(candidate_root / "_candidate_results.jsonl", "candidate results")
    candidate_summary_path = _input_file(candidate_root / "_candidate_summary.json", "candidate summary")
    candidate_validation_path = _input_file(candidate_root / "_candidate_validation.json", "candidate validation")
    candidate_rows = _load_jsonl_records(candidate_results_path, "candidate results")
    _require(len(candidate_rows) == EXPECTED_REPAIR_CASE_COUNT, "candidate results must contain exactly 12 rows")
    _require(
        [row.get("case_unit_id") for row in candidate_rows] == list(EXPECTED_REPAIR_CASE_IDS),
        "candidate result order/identity mismatch",
    )
    candidate_by_id: dict[str, dict[str, Any]] = {}
    for position, row in enumerate(candidate_rows, start=1):
        case_id = EXPECTED_REPAIR_CASE_IDS[position - 1]
        _require(
            set(row)
            == {
                "schema_version",
                "repair_lock_sha256",
                "case_unit_id",
                "generation_status",
                "generation",
                "strict_validation_status",
                "promotion_performed",
                "strict_validation",
            },
            f"candidate result field set mismatch: {case_id}",
        )
        _require(row.get("schema_version") == CANDIDATE_RESULTS_SCHEMA, f"candidate result schema mismatch: {case_id}")
        _require(row.get("repair_lock_sha256") == sha256_file(repair_lock_path), f"candidate result lock hash mismatch: {case_id}")
        _require(row.get("generation_status") == "success", f"candidate generation failed: {case_id}")
        _require(row.get("strict_validation_status") == "passed", f"candidate strict validation failed: {case_id}")
        _require(row.get("promotion_performed") is False, f"candidate row claims promotion: {case_id}")
        candidate_by_id[case_id] = row

    candidate_summary = _load_mapping(candidate_summary_path, "candidate summary")
    _require(candidate_summary.get("schema_version") == CANDIDATE_SUMMARY_SCHEMA, "candidate summary schema mismatch")
    _require(candidate_summary.get("status") == "candidate_generated/review_required", "candidate summary status mismatch")
    _require(candidate_summary.get("case_count") == EXPECTED_REPAIR_CASE_COUNT, "candidate summary case count mismatch")
    _require(candidate_summary.get("generation_success_count") == EXPECTED_REPAIR_CASE_COUNT, "candidate generation count mismatch")
    _require(candidate_summary.get("strict_validation_pass_count") == EXPECTED_REPAIR_CASE_COUNT, "candidate pass count mismatch")
    _require(candidate_summary.get("strict_validation_fail_count") == 0, "candidate failure count mismatch")
    _require(candidate_summary.get("formal_cases_unchanged") is True, "candidate summary does not preserve formal cases")
    _require(candidate_summary.get("promotion_performed") is False, "candidate summary claims promotion")
    _require(candidate_summary.get("max_parallel") == 8, "candidate concurrency mismatch")
    candidate_validation = _load_mapping(candidate_validation_path, "candidate validation")
    expected_candidate_validation = {
        "schema_version": CANDIDATE_VALIDATION_SCHEMA,
        "status": "passed",
        "repair_lock_path": _repo_relative(repair_lock_path),
        "repair_lock_sha256": sha256_file(repair_lock_path),
        "case_count": EXPECTED_REPAIR_CASE_COUNT,
        "passed_case_ids": list(EXPECTED_REPAIR_CASE_IDS),
        "failed_cases": [],
        "checks": {
            "support_paths_in_packet_inventory": True,
            "support_locations_resolve": True,
            "formal_cases_tree_unchanged": True,
            "formal_cases_tree_sha256": formal_tree_sha256,
            "promotion_performed": False,
        },
    }
    _require(candidate_validation == expected_candidate_validation, "persisted candidate validation mismatch")

    candidate_entries = list(candidate_root.iterdir())
    candidate_dirs = {path.name for path in candidate_entries if path.is_dir() and not path.is_symlink()}
    candidate_files = {path.name for path in candidate_entries if path.is_file() and not path.is_symlink()}
    _require(candidate_dirs == EXPECTED_REPAIR_CASE_SET, "candidate directory set mismatch")
    _require(
        candidate_files == {"_candidate_results.jsonl", "_candidate_summary.json", "_candidate_validation.json"},
        "candidate root file inventory mismatch",
    )
    _validate_no_symlinks(candidate_root)
    candidate_tree_sha256 = sha256_path(candidate_root)
    repair_ref = _mapping(manifest.get("repair"), "corrections repair")
    repair_keys = {
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
    _require(set(repair_ref) == repair_keys, "corrections repair field set mismatch")
    expected_repair_ref = {
        "lock_path": _repo_relative(repair_lock_path),
        "lock_sha256": sha256_file(repair_lock_path),
        "candidate_root": _repo_relative(candidate_root),
        "candidate_tree_sha256": candidate_tree_sha256,
        "candidate_results_path": _repo_relative(candidate_results_path),
        "candidate_results_sha256": sha256_file(candidate_results_path),
        "candidate_result_rows_semantic_sha256": sha256_object(candidate_rows),
        "candidate_summary_path": _repo_relative(candidate_summary_path),
        "candidate_summary_sha256": sha256_file(candidate_summary_path),
        "candidate_validation_path": _repo_relative(candidate_validation_path),
        "candidate_validation_sha256": sha256_file(candidate_validation_path),
        "candidate_validation_semantic_sha256": sha256_object(candidate_validation),
    }
    _require(dict(repair_ref) == expected_repair_ref, "corrections repair binding mismatch")

    accepted_entries = list(accepted_cases_root.iterdir())
    accepted_dirs = {path.name for path in accepted_entries if path.is_dir() and not path.is_symlink()}
    accepted_other = [path.name for path in accepted_entries if not path.is_dir() or path.is_symlink()]
    _require(not accepted_other, f"accepted overlay contains unsupported entries: {sorted(accepted_other)}")
    _require(accepted_dirs == expected_set, "accepted overlay must contain exactly 485 case directories")
    _validate_no_symlinks(accepted_cases_root)
    accepted_inventory = _tree_inventory(accepted_cases_root)
    accepted_tree_sha256 = sha256_path(accepted_cases_root)
    accepted_ref = _mapping(manifest.get("accepted_overlay"), "corrections accepted_overlay")
    accepted_keys = {
        "root",
        "tree_sha256",
        "file_count",
        "directory_count",
        "size_bytes",
        "case_count",
        "unchanged_case_count",
        "corrected_case_count",
    }
    _require(set(accepted_ref) == accepted_keys, "accepted_overlay field set mismatch")
    expected_accepted_ref = {
        "root": _repo_relative(accepted_cases_root),
        "tree_sha256": accepted_tree_sha256,
        "file_count": accepted_inventory["file_count"],
        "directory_count": accepted_inventory["directory_count"],
        "size_bytes": accepted_inventory["size_bytes"],
        "case_count": EXPECTED_EXTENSION_COUNT,
        "unchanged_case_count": EXPECTED_EXTENSION_COUNT - len(EXPECTED_CORRECTED_CASE_SET),
        "corrected_case_count": len(EXPECTED_CORRECTED_CASE_SET),
    }
    _require(dict(accepted_ref) == expected_accepted_ref, "accepted_overlay binding mismatch")

    corrections = _mapping(manifest.get("corrections"), "corrections entries")
    _require(set(corrections) == {"location_corrections", "security_correction"}, "corrections entry groups mismatch")
    raw_location = corrections.get("location_corrections")
    _require(isinstance(raw_location, list) and len(raw_location) == EXPECTED_REPAIR_CASE_COUNT, "location corrections must contain 12 entries")
    correction_histories: dict[str, list[dict[str, Any]]] = {}
    correction_rows: dict[str, dict[str, Any]] = {}
    location_audits: list[dict[str, Any]] = []
    location_keys = {
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
        "validation",
        "secondary_defect",
    }
    location_validation = {
        "candidate_strict_validation_passed": True,
        "support_locations_resolve": True,
        "source_and_accepted_byte_equal": True,
        "formal_case_not_authoritative": True,
    }
    for index, raw_entry in enumerate(raw_location):
        case_id = EXPECTED_REPAIR_CASE_IDS[index]
        entry = _mapping(raw_entry, f"location correction {case_id}")
        _require(set(entry) == location_keys, f"location correction field set mismatch: {case_id}")
        _require(entry.get("case_unit_id") == case_id, f"location correction order/identity mismatch: {case_id}")
        _string(entry.get("reason"), f"location correction reason {case_id}")
        packet_path = _input_file(packet_root / case_id / "case_packet.md", f"case packet {case_id}")
        formal_case = _input_directory(formal_cases_root / case_id, f"formal case {case_id}")
        source_case = _input_directory(candidate_root / case_id, f"candidate case {case_id}")
        accepted_case = _input_directory(accepted_cases_root / case_id, f"accepted case {case_id}")
        formal_case_hash = sha256_path(formal_case)
        source_case_hash = sha256_path(source_case)
        accepted_case_hash = sha256_path(accepted_case)
        candidate_row = candidate_by_id[case_id]
        strict = _mapping(candidate_row.get("strict_validation"), f"candidate strict validation {case_id}")
        canonical = _canonical_hash_mapping(entry.get("canonical_file_sha256"), label=f"location canonical hashes {case_id}")
        expected_entry_values = {
            "case_packet_path": _repo_relative(packet_path),
            "case_packet_sha256": sha256_file(packet_path),
            "formal_case_path": _repo_relative(formal_case),
            "formal_case_tree_sha256": formal_case_hash,
            "source_case_path": _repo_relative(source_case),
            "source_case_tree_sha256": source_case_hash,
            "accepted_case_path": _repo_relative(accepted_case),
            "accepted_case_tree_sha256": accepted_case_hash,
            "source_result_row_sha256": sha256_object(candidate_row),
        }
        for key, value in expected_entry_values.items():
            _require(entry.get(key) == value, f"location correction {case_id} {key} mismatch")
        _require(source_case_hash == accepted_case_hash, f"accepted location correction differs from candidate: {case_id}")
        _require(formal_case_hash != accepted_case_hash, f"location correction did not change case: {case_id}")
        _require(canonical == strict.get("canonical_sha256"), f"location canonical hashes differ from candidate validation: {case_id}")
        _require(
            canonical == {suffix: sha256_file(accepted_case / suffix) for suffix in EXPECTED_CANONICAL_SUFFIXES},
            f"accepted canonical hashes differ from manifest: {case_id}",
        )
        _require(dict(_mapping(entry.get("validation"), f"location validation {case_id}")) == location_validation, f"location validation mismatch: {case_id}")
        if case_id == "9ef034e_2":
            _require(
                entry.get("secondary_defect")
                == {"kind": "secret_like_material", "formal_hit_count": 44, "accepted_hit_count": 0},
                "9ef034e_2 secondary defect inventory mismatch",
            )
        else:
            _require(entry.get("secondary_defect") is None, f"unexpected secondary defect: {case_id}")
        generation = dict(_mapping(candidate_row.get("generation"), f"candidate generation {case_id}"))
        _validate_result_row(generation, case_id=case_id, packet_path=packet_path, lock=lock)
        correction_histories[case_id] = [generation]
        correction_rows[case_id] = generation
        location_audits.append(
            {
                "case_unit_id": case_id,
                "case_packet_sha256": sha256_file(packet_path),
                "formal_case_tree_sha256": formal_case_hash,
                "source_case_tree_sha256": source_case_hash,
                "accepted_case_tree_sha256": accepted_case_hash,
                "source_result_row_sha256": sha256_object(candidate_row),
            }
        )

    security_entry = _mapping(corrections.get("security_correction"), "security correction")
    security_keys = {
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
    _require(set(security_entry) == security_keys, "security correction field set mismatch")
    security_id = EXPECTED_SECURITY_CORRECTION_CASE_ID
    _require(security_entry.get("case_unit_id") == security_id, "security correction case mismatch")
    _string(security_entry.get("reason"), "security correction reason")
    security_packet = _input_file(packet_root / security_id / "case_packet.md", "security case packet")
    security_formal = _input_directory(formal_cases_root / security_id, "security formal case")
    security_source_root = _input_directory(draft_root / "corrections/round_02", "security correction round")
    security_source = _input_directory(security_source_root / security_id, "security correction source")
    security_accepted = _input_directory(accepted_cases_root / security_id, "security accepted case")
    security_results_path = _input_file(security_source_root / "_batch_results.jsonl", "security source results")
    security_summary_path = _input_file(security_source_root / "_batch_summary.json", "security source summary")
    _require(
        {path.name for path in security_source_root.iterdir()}
        == {security_id, "_batch_results.jsonl", "_batch_summary.json"},
        "security correction round inventory mismatch",
    )
    security_rows = _load_jsonl_records(security_results_path, "security source results")
    _require(len(security_rows) == 1, "security source results must contain one row")
    raw_security_row = security_rows[0]
    _require(raw_security_row.get("case_unit_dir") == security_id and raw_security_row.get("status") == "success", "security source result mismatch")
    normalization = _mapping(security_entry.get("result_normalization"), "security result_normalization")
    expected_normalization = {
        "allowed_changed_fields": ["case_packet"],
        "source_case_packet": raw_security_row.get("case_packet"),
        "normalized_case_packet": _repo_relative(security_packet),
    }
    _require(dict(normalization) == expected_normalization, "security result normalization mismatch")
    normalized_security_row = dict(raw_security_row)
    normalized_security_row["case_packet"] = normalization["normalized_case_packet"]
    _validate_result_row(normalized_security_row, case_id=security_id, packet_path=security_packet, lock=lock)
    security_formal_hash = sha256_path(security_formal)
    security_source_hash = sha256_path(security_source)
    security_accepted_hash = sha256_path(security_accepted)
    expected_security_values = {
        "case_packet_path": _repo_relative(security_packet),
        "case_packet_sha256": sha256_file(security_packet),
        "formal_case_path": _repo_relative(security_formal),
        "formal_case_tree_sha256": security_formal_hash,
        "source_case_path": _repo_relative(security_source),
        "source_case_tree_sha256": security_source_hash,
        "accepted_case_path": _repo_relative(security_accepted),
        "accepted_case_tree_sha256": security_accepted_hash,
        "source_batch_results_path": _repo_relative(security_results_path),
        "source_batch_results_sha256": sha256_file(security_results_path),
        "source_batch_summary_path": _repo_relative(security_summary_path),
        "source_batch_summary_sha256": sha256_file(security_summary_path),
        "source_result_row_sha256": sha256_object(raw_security_row),
    }
    for key, value in expected_security_values.items():
        _require(security_entry.get(key) == value, f"security correction {key} mismatch")
    _require(security_source_hash == security_accepted_hash, "accepted security correction differs from round_02")
    _require(security_formal_hash != security_accepted_hash, "security correction did not change the case")
    security_canonical = _canonical_hash_mapping(security_entry.get("canonical_file_sha256"), label="security canonical hashes")
    _require(
        security_canonical == {suffix: sha256_file(security_accepted / suffix) for suffix in EXPECTED_CANONICAL_SUFFIXES},
        "security canonical hashes differ from accepted case",
    )
    expected_security_scan = {
        "scanner_schema": "appworld_draft_secret_scan.v1",
        "formal_hit_count": 40,
        "source_hit_count": 0,
        "accepted_hit_count": 0,
    }
    _require(dict(_mapping(security_entry.get("secret_scan"), "security secret_scan")) == expected_security_scan, "security correction secret scan mismatch")
    expected_security_validation = {
        "codex_generation_valid": True,
        "support_locations_resolve": True,
        "source_and_accepted_byte_equal": True,
        "formal_secret_material_rejected": True,
        "accepted_secret_scan_passed": True,
    }
    _require(dict(_mapping(security_entry.get("validation"), "security validation")) == expected_security_validation, "security validation mismatch")
    correction_histories[security_id] = [normalized_security_row]
    correction_rows[security_id] = normalized_security_row

    unchanged_ids = [case_id for case_id in expected_ids if case_id not in EXPECTED_CORRECTED_CASE_SET]
    _require(len(unchanged_ids) == 472, "unchanged overlay case count mismatch")
    for case_id in unchanged_ids:
        _require(
            sha256_path(formal_cases_root / case_id) == sha256_path(accepted_cases_root / case_id),
            f"accepted unchanged case differs from formal run: {case_id}",
        )

    legacy_manifest = _input_file(draft_root / "provenance/draft_corrections.json", "legacy corrections manifest")
    legacy_accepted = _input_directory(draft_root / "accepted_cases", "legacy accepted cases")
    round_01_root = _input_directory(draft_root / "corrections/round_01", "superseded round_01")
    round_02_root = _input_directory(draft_root / "corrections/round_02", "superseded round_02 overlay source")
    superseded = _mapping(manifest.get("superseded_overlay"), "superseded_overlay")
    superseded_keys = {
        "status",
        "legacy_manifest_path",
        "legacy_manifest_sha256",
        "legacy_accepted_cases_root",
        "legacy_accepted_cases_tree_sha256",
        "round_01",
        "round_02",
    }
    _require(set(superseded) == superseded_keys, "superseded_round_01 field set mismatch")
    expected_superseded = {
        "status": "superseded_not_authoritative",
        "legacy_manifest_path": _repo_relative(legacy_manifest),
        "legacy_manifest_sha256": sha256_file(legacy_manifest),
        "legacy_accepted_cases_root": _repo_relative(legacy_accepted),
        "legacy_accepted_cases_tree_sha256": sha256_path(legacy_accepted),
        "round_01": {
            "root": _repo_relative(round_01_root),
            "tree_sha256": sha256_path(round_01_root),
            "case_ids": ["9ef034e_2"],
            "case_ids_semantic_sha256": sha256_object(["9ef034e_2"]),
        },
        "round_02": {
            "root": _repo_relative(round_02_root),
            "tree_sha256": sha256_path(round_02_root),
            "case_ids": ["dac78d9_3"],
            "case_ids_semantic_sha256": sha256_object(["dac78d9_3"]),
        },
    }
    _require(dict(superseded) == expected_superseded, "superseded_overlay binding mismatch")

    formal_secret_findings = _secret_scan_tree(formal_cases_root)
    accepted_secret_findings = _secret_scan_tree(accepted_cases_root)
    candidate_secret_findings = _secret_scan_tree(candidate_root)
    security_source_findings = _secret_scan_tree(security_source_root)
    manifest_secret_findings = _secret_scan_paths([corrections_file])
    formal_secret_by_case = _secret_counts_by_case(formal_secret_findings, formal_cases_root)
    _require(formal_secret_by_case == {"9ef034e_2": 44, "dac78d9_3": 40}, "formal secret incident inventory drift")
    _require(not accepted_secret_findings, "accepted overlay contains secret-like material")
    _require(not candidate_secret_findings, "location candidate namespace contains secret-like material")
    _require(not security_source_findings, "security correction source contains secret-like material")
    _require(not manifest_secret_findings, "corrections manifest contains secret-like material")
    security_inventory = _mapping(manifest.get("security_incident_inventory"), "security_incident_inventory")
    expected_security_inventory = {
        "scanner_schema": "appworld_draft_secret_scan.v1",
        "affected_case_ids": ["9ef034e_2", "dac78d9_3"],
        "formal_hits_by_case": {"9ef034e_2": 44, "dac78d9_3": 40},
        "formal_hit_count": 84,
        "accepted_hit_count": 0,
        "credential_values_recorded": False,
    }
    _require(dict(security_inventory) == expected_security_inventory, "security incident inventory mismatch")

    validation = _mapping(manifest.get("validation"), "corrections validation")
    validation_keys = {
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
    _require(set(validation) == validation_keys, "corrections validation field set mismatch")
    expected_validation = {
        "location_case_ids": list(EXPECTED_REPAIR_CASE_IDS),
        "location_case_ids_semantic_sha256": sha256_object(list(EXPECTED_REPAIR_CASE_IDS)),
        "security_case_id": security_id,
        "exact_485_accepted_case_dirs": True,
        "formal_batch_immutable_exact_485": True,
        "location_candidate_validation_passed": True,
        "accepted_cases_match_authoritative_sources": True,
        "formal_secret_case_ids": ["9ef034e_2", "dac78d9_3"],
        "formal_secret_hit_count": 84,
        "accepted_secret_hit_count": 0,
        "draft_lifecycle_status": "draft_generated/review_required",
        "human_review_completed": False,
    }
    _require(dict(validation) == expected_validation, "corrections validation claims mismatch")

    audit = {
        "schema_version": CORRECTIONS_SCHEMA,
        "manifest_path": _repo_relative(corrections_file),
        "manifest_sha256": sha256_file(corrections_file),
        "correction_count": len(EXPECTED_CORRECTED_CASE_SET),
        "location_correction_count": EXPECTED_REPAIR_CASE_COUNT,
        "security_correction_count": 1,
        "corrected_case_ids": list(EXPECTED_REPAIR_CASE_IDS) + [security_id],
        "unchanged_case_count": len(unchanged_ids),
        "formal_cases_tree_sha256": formal_tree_sha256,
        "accepted_cases_tree_sha256": accepted_tree_sha256,
        "accepted_file_count": accepted_inventory["file_count"],
        "accepted_directory_count": accepted_inventory["directory_count"],
        "accepted_size_bytes": accepted_inventory["size_bytes"],
        "repair_lock_path": _repo_relative(repair_lock_path),
        "repair_lock_sha256": sha256_file(repair_lock_path),
        "candidate_root": _repo_relative(candidate_root),
        "candidate_tree_sha256": candidate_tree_sha256,
        "candidate_results_path": _repo_relative(candidate_results_path),
        "candidate_results_sha256": sha256_file(candidate_results_path),
        "candidate_summary_path": _repo_relative(candidate_summary_path),
        "candidate_summary_sha256": sha256_file(candidate_summary_path),
        "candidate_validation_path": _repo_relative(candidate_validation_path),
        "candidate_validation_sha256": sha256_file(candidate_validation_path),
        "location_corrections": location_audits,
        "security_correction": {
            "case_unit_id": security_id,
            "case_packet_sha256": sha256_file(security_packet),
            "formal_case_tree_sha256": security_formal_hash,
            "source_case_tree_sha256": security_source_hash,
            "accepted_case_tree_sha256": security_accepted_hash,
            "source_result_row_sha256": sha256_object(raw_security_row),
        },
        "superseded_overlay": dict(superseded),
        "security_incident_inventory": {
            **expected_security_inventory,
            "formal_findings": formal_secret_findings,
            "accepted_findings": [],
        },
        "transitive_closure_sha256": sha256_object(
            {
                "formal_run": expected_formal_ref,
                "repair": expected_repair_ref,
                "accepted_overlay": expected_accepted_ref,
                "superseded_overlay": expected_superseded,
                "security_incident_inventory": expected_security_inventory,
                "corrections": manifest["corrections"],
            }
        ),
    }
    return audit, correction_histories, correction_rows


def _load_jsonl_records(path: Path, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(f"{label} line {line_number} is malformed JSON: {exc}") from exc
        _require(isinstance(value, dict), f"{label} line {line_number} is not an object")
        rows.append(value)
    return rows


def _input_directory(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path).resolve()
    _require(resolved.is_dir() and not resolved.is_symlink(), f"{label} is missing or symlinked: {resolved}")
    return resolved


def _secret_scan_tree(root: Path) -> list[dict[str, Any]]:
    return _secret_scan_paths(path for path in sorted(root.rglob("*")) if path.is_file())


def _secret_scan_paths(paths: Sequence[Path] | Any) -> list[dict[str, Any]]:
    """Return high-confidence finding metadata without credential values/hashes."""

    findings: list[dict[str, Any]] = []
    for path in paths:
        _require(path.is_file() and not path.is_symlink(), f"secret-scan input is missing or symlinked: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern_name, pattern in _SECRET_PATTERN_DEFINITIONS:
                count = len(pattern.findall(line))
                if count:
                    findings.append(
                        {
                            "case_unit_id": next(
                                (part for part in path.parts if re.fullmatch(r"[0-9a-f]{7}_[123]", part)),
                                None,
                            ),
                            "path": _repo_relative(path),
                            "pattern": pattern_name,
                            "count": count,
                            "line": line_number,
                        }
                    )
    return findings


def _secret_counts_by_case(findings: Sequence[Mapping[str, Any]], root: Path) -> dict[str, int]:
    del root
    counts: Counter[str] = Counter()
    for finding in findings:
        case_id = finding.get("case_unit_id")
        _require(isinstance(case_id, str), "formal secret finding is not attributable to a case")
        counts[case_id] += _integer(finding.get("count"), "secret finding count")
    return dict(counts)


def _secret_like_hit_inventory(root: Path) -> dict[str, int]:
    hits: dict[str, int] = {}
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.is_symlink():
            continue
        text = path.read_text(encoding="utf-8")
        count = sum(len(list(pattern.finditer(text))) for pattern in _SECRET_PATTERNS)
        if count:
            hits[path.name] = count
    return hits


def _tree_inventory(root: Path) -> dict[str, Any]:
    """Hash a tree from sorted relative paths, byte sizes, and file hashes."""

    _require(root.is_dir() and not root.is_symlink(), f"tree root is missing or symlinked: {root}")
    files: list[dict[str, Any]] = []
    directories: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        _require(not path.is_symlink(), f"tree contains a symlink: {path}")
        if path.is_dir():
            directories.append(path.relative_to(root).as_posix())
            continue
        _require(path.is_file(), f"tree contains an unsupported entry: {path}")
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "tree_sha256": sha256_object(files),
        "file_count": len(files),
        "directory_count": len(directories),
        "size_bytes": sum(int(item["size_bytes"]) for item in files),
        "directories": directories,
        "files": files,
    }


def _acceptance_validator_hashes() -> dict[str, str]:
    module_path = Path(__file__).resolve()
    cli_path = resolve_repo_path("src/evidence_system/cli/validate_appworld_generation_drafts.py").resolve()
    return {
        "contract_module_path": _repo_relative(module_path),
        "contract_module_sha256": sha256_file(module_path),
        "cli_path": _repo_relative(cli_path),
        "cli_sha256": sha256_file(cli_path),
    }


def _validate_acceptance_validator_hashes(value: Mapping[str, Any]) -> None:
    expected = _acceptance_validator_hashes()
    _require(dict(value) == expected, "acceptance validator implementation hashes drifted")


def _validate_lock(*, lock_file: Path, lock: Mapping[str, Any], cases_root: Path) -> dict[str, Any]:
    _require(lock.get("schema_version") == LOCK_SCHEMA, f"draft lock schema must be {LOCK_SCHEMA}")
    _require(lock.get("status") == "locked_pre_run", "draft lock status must remain locked_pre_run")
    _require(lock.get("experiment_id") == EXPECTED_EXPERIMENT_ID, "draft lock experiment_id mismatch")
    _require(lock.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID, "draft lock draft_run_id mismatch")
    _parse_iso_timestamp(lock.get("locked_at"), "locked_at")
    repository = _mapping(lock.get("repository"), "repository")
    _require(
        re.fullmatch(r"[0-9a-f]{40}", str(repository.get("base_commit") or "")) is not None,
        "repository base commit is not frozen",
    )
    _require(repository.get("implementation_files_uncommitted") is True, "uncommitted implementation state must be explicit")
    _require("SHA-256" in _string(repository.get("reproducibility_rule"), "repository.reproducibility_rule"), "repository reproducibility rule mismatch")
    scope_deviation = _mapping(lock.get("scope_deviation"), "scope_deviation")
    _require(scope_deviation.get("requested_by_user") is True, "Codex provider scope deviation is not authorized")
    _require(scope_deviation.get("predecessor_reuse_allowed") is False, "quarantined predecessor reuse must be forbidden")
    _require(
        scope_deviation.get("quarantined_predecessor")
        == "experiments/appworld_full_test_extension_v1/draft_runs/codex-gpt-5.4-high",
        "quarantined predecessor pointer mismatch",
    )

    drafter = _mapping(lock.get("drafter"), "drafter")
    expected_drafter = {
        "provider": "codex",
        "llm_call_provider": "codex_cli",
        "auth_mode": "codex_login",
        "requested_model_alias": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "model_verbosity": EXPECTED_MODEL_VERBOSITY,
        "temperature_recorded": 0.0,
        "temperature_enforced": False,
        "codex_sandbox": "read-only",
        "max_output_token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "max_output_tokens_enforced": False,
        "token_budget_semantics": "Retry-attempt labels only for Codex CLI; they are not output caps.",
        "regular_codex_timeout_seconds": 1800,
        "oversized_codex_timeout_seconds": 3600,
        "large_case_threshold_bytes": 100000,
        "regular_max_parallel": 8,
        "oversized_max_parallel": 8,
        "lane_execution": "regular then oversized",
        "sort_by": "size",
        "quality_check": "none",
    }
    for key, expected in expected_drafter.items():
        _require(drafter.get(key) == expected, f"drafter.{key} mismatch: {drafter.get(key)!r}")
    _require(
        drafter.get("retry_rule")
        == "Retry after nonzero drafter exit or schema/strict-guardrail-invalid draft; preserve every attempt and promote the first valid attempt.",
        "draft retry rule mismatch",
    )
    _require(_string(drafter.get("login_status_at_lock"), "drafter.login_status_at_lock"), "login status is missing")
    _require(drafter.get("backend_model_revision") is None, "backend model revision must not be invented")
    _require(
        drafter.get("backend_model_revision_unavailable_reason")
        == "Codex CLI does not expose a verifiable backend snapshot in this workflow.",
        "backend model revision limitation is not frozen",
    )

    acceptance = _mapping(lock.get("acceptance"), "acceptance")
    _require(acceptance.get("required_case_count") == EXPECTED_EXTENSION_COUNT, "acceptance case count mismatch")
    for key in (
        "require_json_schema_validation",
        "require_strict_guardrail_validation",
        "require_yaml_json_semantic_equality",
        "require_support_pointer_locations_resolvable",
        "require_official_source_hash_match",
        "require_exact_case_directory_set",
        "require_exact_final_seven_file_bundle",
        "require_final_bundle_matches_one_successful_attempt",
        "require_codex_login_provenance",
        "require_provider_model_reasoning_match",
        "require_successful_codex_event_stream",
        "require_nonzero_token_usage",
        "require_no_symlinks",
        "require_no_secret_material",
        "require_external_draft_call_provenance",
        "require_hash_lock_after_validation",
    ):
        _require(acceptance.get(key) is True, f"acceptance.{key} must be true")
    _require(
        acceptance.get("required_identity_match")
        == ["domain", "case_unit_id", "task_id", "split", "source_ref"],
        "acceptance identity fields mismatch",
    )
    _require(acceptance.get("required_schema") == "case_checklist_v1", "acceptance checklist schema mismatch")
    _require(
        acceptance.get("required_final_status") == "draft_generated/review_required",
        "acceptance draft lifecycle status mismatch",
    )
    _require(
        acceptance.get("required_case_count_by_dataset")
        == {"test_normal": EXPECTED_NORMAL_EXTENSION_COUNT, "test_challenge": EXPECTED_CHALLENGE_COUNT},
        "acceptance split counts mismatch",
    )
    _require(
        acceptance.get("support_pointer_allowlist")
        == "case_packet.md or exact paths under the packet's Source Inventory heading",
        "acceptance support allowlist mismatch",
    )
    _require(
        acceptance.get("forbidden_support_pointer_paths")
        == ["draft_instructions.md", "template.yaml", "output_schema.json", "draft_body.json"],
        "acceptance forbidden support paths mismatch",
    )

    implementation_hashes = _mapping(lock.get("implementation_hashes"), "implementation_hashes")
    observed_keys = set(implementation_hashes)
    _require(_REQUIRED_IMPLEMENTATION_KEYS <= observed_keys, "draft lock is missing required implementation hashes")
    allowed_implementation_keys = set(_IMPLEMENTATION_PATHS) | {"effective_composed_prompt_sha256"}
    _require(observed_keys <= allowed_implementation_keys, f"unknown implementation hash keys: {sorted(observed_keys - allowed_implementation_keys)}")
    for key, locked_hash in implementation_hashes.items():
        if key == "effective_composed_prompt_sha256":
            continue
        path = _input_file(_IMPLEMENTATION_PATHS[key], f"implementation {key}")
        _require(sha256_file(path) == locked_hash, f"implementation hash drift: {key}")
    base_prompt = _input_file(_IMPLEMENTATION_PATHS["draft_case_checklist.prompt.md"], "base draft prompt").read_text(encoding="utf-8")
    supplement = _input_file(
        _IMPLEMENTATION_PATHS["draft_source_pointer_strict_v2.supplement.md"],
        "strict draft prompt supplement",
    ).read_text(encoding="utf-8")
    effective_prompt = minimal_drafter.compose_prompt(base_prompt, supplement)
    _require(
        sha256_bytes(effective_prompt.encode("utf-8"))
        == implementation_hashes["effective_composed_prompt_sha256"],
        "effective composed prompt hash drift",
    )

    runtime = _mapping(lock.get("runtime"), "runtime")
    _require(sha256_file(_input_file("uv.lock", "uv lock")) == runtime.get("uv_lock_sha256"), "uv.lock hash drift")
    codex_executable = _input_file(_string(runtime.get("codex_executable"), "runtime.codex_executable"), "Codex executable")
    _require(sha256_file(codex_executable) == runtime.get("codex_executable_sha256"), "Codex executable hash drift")
    _require(runtime.get("codex_cli_version") == "0.144.4", "Codex CLI version lock mismatch")

    execution = _mapping(lock.get("execution"), "execution")
    _require(resolve_repo_path(_string(execution.get("output_root"), "execution.output_root")).resolve() == cases_root, "execution output root mismatch")
    _require(execution.get("pre_run_output_root_exists") is False, "clean namespace pre-run state is not frozen")
    _require(execution.get("pre_run_output_entry_count") == 0, "clean namespace was not empty before the run")
    _validate_execution_command(lock)
    return {
        "schema_version": LOCK_SCHEMA,
        "status": "locked_pre_run",
        "implementation_hash_count": len(implementation_hashes),
        "implementation_hashes_verified": True,
        "runtime_hashes_verified": True,
        "execution_command_verified": True,
        "lock_file_sha256": sha256_file(lock_file),
    }


def _validate_locked_inputs(lock: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    inputs = _mapping(lock.get("inputs"), "inputs")
    _require(inputs.get("expected_case_count") == EXPECTED_EXTENSION_COUNT, "locked input case count mismatch")
    _require(
        inputs.get("expected_case_count_by_dataset")
        == {"test_normal": EXPECTED_NORMAL_EXTENSION_COUNT, "test_challenge": EXPECTED_CHALLENGE_COUNT},
        "locked split counts mismatch",
    )
    manifest_path = _input_file(_string(inputs.get("manifest_path"), "inputs.manifest_path"), "extension manifest")
    source_bundle_path = _input_file(_string(inputs.get("source_bundle_path"), "inputs.source_bundle_path"), "source bundle")
    packet_report_path = _input_file(
        _string(inputs.get("packet_acceptance_report_path"), "inputs.packet_acceptance_report_path"),
        "packet acceptance report",
    )
    frozen_scope_path = _input_file(
        _string(inputs.get("frozen_scope_path"), "inputs.frozen_scope_path"),
        "frozen extension scope",
    )
    source_catalog_path = _input_file(
        _string(inputs.get("source_catalog_path"), "inputs.source_catalog_path"),
        "extension source catalog",
    )
    all_ids_path = _input_file(
        _string(inputs.get("all_extension_ids_path"), "inputs.all_extension_ids_path"),
        "all extension IDs",
    )
    normal_ids_path = _input_file(source_catalog_path.parent / "appworld_test_normal_extension.txt", "normal extension IDs")
    challenge_ids_path = _input_file(source_catalog_path.parent / "appworld_test_challenge.txt", "challenge IDs")
    packet_root = resolve_repo_path(_string(inputs.get("case_packet_root"), "inputs.case_packet_root"))
    _require(packet_root.is_dir() and not packet_root.is_symlink(), "locked case packet root is missing or symlinked")
    _require(sha256_file(manifest_path) == inputs.get("manifest_sha256"), "locked manifest hash drift")
    _require(sha256_file(source_bundle_path) == inputs.get("source_bundle_sha256"), "locked source bundle hash drift")
    _require(sha256_file(packet_report_path) == inputs.get("packet_acceptance_report_sha256"), "locked packet report hash drift")
    _require(sha256_file(frozen_scope_path) == inputs.get("frozen_scope_sha256"), "locked frozen scope hash drift")
    _require(sha256_file(source_catalog_path) == inputs.get("source_catalog_sha256"), "locked source catalog hash drift")
    _require(sha256_file(all_ids_path) == inputs.get("all_extension_ids_sha256"), "locked all-extension ID file hash drift")
    _require(sha256_file(normal_ids_path) == inputs.get("normal_extension_ids_sha256"), "locked normal-extension ID file hash drift")
    _require(sha256_file(challenge_ids_path) == inputs.get("challenge_ids_sha256"), "locked challenge ID file hash drift")

    extension_root = manifest_path.parent
    packet_audit = validate_extension_packets(output_root=extension_root, case_packets_root=packet_root.parent)
    bundle_audit = validate_extension_source_bundle(
        output_root=extension_root,
        case_packets_root=packet_root.parent,
        source_bundle_path=source_bundle_path,
    )
    _require(packet_audit.get("packet_index_sha256") == inputs.get("case_packet_index_sha256"), "locked packet index hash drift")
    _require(packet_audit.get("packet_source_tree_sha256") == inputs.get("official_source_tree_sha256"), "locked source tree hash drift")
    _require(bundle_audit.get("source_count") == EXPECTED_EXTENSION_COUNT, "extension source bundle count mismatch")
    frozen_scope = _load_mapping(frozen_scope_path, "frozen extension scope")
    _require(
        _mapping(frozen_scope.get("scope"), "frozen scope.scope").get("extension_case_count")
        == EXPECTED_EXTENSION_COUNT,
        "frozen extension scope count mismatch",
    )

    manifest = _load_mapping(manifest_path, "extension manifest")
    domains = manifest.get("domains")
    _require(isinstance(domains, list) and len(domains) == 1, "extension manifest must contain exactly one domain")
    raw_cases = _mapping(domains[0], "manifest domain").get("case_units")
    _require(isinstance(raw_cases, list) and len(raw_cases) == EXPECTED_EXTENSION_COUNT, "manifest case list mismatch")
    manifest_cases: list[dict[str, str]] = []
    for index, raw_case in enumerate(raw_cases):
        case = _mapping(raw_case, f"manifest case {index}")
        case_id = _string(case.get("case_unit_id"), f"manifest case {index}.case_unit_id")
        task_id = _string(case.get("task_id"), f"manifest case {index}.task_id")
        dataset_name = _string(case.get("dataset_name"), f"manifest case {index}.dataset_name")
        _require(case_id == task_id, f"manifest case identity mismatch: {case_id}")
        _require(dataset_name in {"test_normal", "test_challenge"}, f"manifest split mismatch: {case_id}")
        _require(case.get("split") == dataset_name, f"manifest split/dataset mismatch: {case_id}")
        _require(case.get("source_ref") == f"appworld://{dataset_name}/{case_id}", f"manifest source_ref mismatch: {case_id}")
        manifest_cases.append({"case_unit_id": case_id, "task_id": task_id, "dataset_name": dataset_name})
    case_ids = [case["case_unit_id"] for case in manifest_cases]
    _require(len(set(case_ids)) == EXPECTED_EXTENSION_COUNT, "manifest case IDs are duplicated")
    _require(sha256_object(case_ids) == inputs.get("case_ids_sha256"), "locked case ID hash drift")
    _require(all_ids_path.read_text(encoding="utf-8").splitlines() == case_ids, "all-extension ID file order differs from manifest")
    normal_ids = normal_ids_path.read_text(encoding="utf-8").splitlines()
    challenge_ids = challenge_ids_path.read_text(encoding="utf-8").splitlines()
    _require(
        normal_ids + challenge_ids == case_ids
        and len(normal_ids) == EXPECTED_NORMAL_EXTENSION_COUNT
        and len(challenge_ids) == EXPECTED_CHALLENGE_COUNT,
        "split ID files do not exactly partition the manifest order",
    )

    packet_report = _load_mapping(packet_report_path, "packet acceptance report")
    _require(packet_report.get("status") == "accepted" and packet_report.get("all_hard_gates_passed") is True, "packet acceptance report is not accepted")
    return (
        {
            "manifest_path": _repo_relative(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
            "source_bundle_path": _repo_relative(source_bundle_path),
            "source_bundle_sha256": sha256_file(source_bundle_path),
            "packet_acceptance_report_path": _repo_relative(packet_report_path),
            "packet_acceptance_report_sha256": sha256_file(packet_report_path),
            "frozen_scope_path": _repo_relative(frozen_scope_path),
            "frozen_scope_sha256": sha256_file(frozen_scope_path),
            "source_catalog_path": _repo_relative(source_catalog_path),
            "source_catalog_sha256": sha256_file(source_catalog_path),
            "all_extension_ids_path": _repo_relative(all_ids_path),
            "all_extension_ids_sha256": sha256_file(all_ids_path),
            "normal_extension_ids_sha256": sha256_file(normal_ids_path),
            "challenge_ids_sha256": sha256_file(challenge_ids_path),
            "case_ids_sha256": sha256_object(case_ids),
            "case_packet_index_sha256": packet_audit["packet_index_sha256"],
            "official_source_tree_sha256": packet_audit["packet_source_tree_sha256"],
            "frozen_scope_hash_verified": True,
            "packets_recomputed": True,
            "source_bundle_recomputed": True,
        },
        manifest_cases,
    )


def _validate_batch_artifacts(
    *,
    cases_root: Path,
    expected_ids: Sequence[str],
    lock: Mapping[str, Any],
    repair_report_path: Path | None = None,
    formal_lock_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    expected_set = set(expected_ids)
    root_entries = list(cases_root.iterdir())
    actual_dirs = {path.name for path in root_entries if path.is_dir() and not path.is_symlink()}
    root_files = {path.name for path in root_entries if path.is_file() and not path.is_symlink()}
    other_entries = [path.name for path in root_entries if path.name not in actual_dirs | root_files]
    _require(not other_entries, f"unsupported or symlinked draft-root entries: {sorted(other_entries)}")
    _require(actual_dirs == expected_set, f"draft case directory set mismatch: missing={sorted(expected_set - actual_dirs)[:5]}, extra={sorted(actual_dirs - expected_set)[:5]}")
    _require(root_files == _ROOT_BATCH_FILES, f"draft root batch-file set mismatch: {sorted(root_files)}")

    summary_path = cases_root / "_batch_summary.json"
    results_path = cases_root / "_batch_results.jsonl"
    summary = _load_mapping(summary_path, "draft batch summary")
    expected_summary_fields = {
        "total_cases": EXPECTED_EXTENSION_COUNT,
        "completed_cases": EXPECTED_EXTENSION_COUNT,
        "failed_cases": 0,
        "provider": "codex",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "codex_sandbox": "read-only",
        "prompt_supplement": "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "sort_by": "size",
        "quality_check": "none",
        "large_case_threshold_bytes": 100000,
    }
    for key, expected in expected_summary_fields.items():
        _require(summary.get(key) == expected, f"batch summary {key} mismatch: {summary.get(key)!r}")
    success_count = _integer(summary.get("success_cases"), "summary.success_cases")
    skipped_count = _integer(summary.get("skipped_cases"), "summary.skipped_cases")
    failed_count = _integer(summary.get("failed_cases"), "summary.failed_cases")
    _require(success_count == EXPECTED_EXTENSION_COUNT, "original batch summary must preserve 485 successes")
    _require(skipped_count == 0, "original batch summary must preserve zero skipped cases")
    _require(failed_count == 0, "original batch summary must preserve zero failed cases")
    _require(summary.get("warning_count") == 0, "batch summary warning_count must be zero")
    drafter = _mapping(lock.get("drafter"), "drafter")
    expected_lane_stats = {
        "regular": {"count": 439, "min_bytes": 15265, "max_bytes": 99789},
        "oversized": {"count": 46, "min_bytes": 100147, "max_bytes": 688300},
    }
    _require(summary.get("lane_stats") == expected_lane_stats, "batch lane statistics drift")
    _require(summary.get("output_root") == _repo_relative(cases_root), "batch summary output_root mismatch")
    _require(drafter.get("regular_max_parallel") == 8 and drafter.get("oversized_max_parallel") == 8, "locked concurrency mismatch")

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(results_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(f"batch results line {line_number} is malformed JSON: {exc}") from exc
        row = _mapping(raw, f"batch results line {line_number}")
        case_id = _string(row.get("case_unit_dir"), f"batch results line {line_number}.case_unit_dir")
        _require(case_id in expected_set, f"batch results line {line_number} has off-list case: {case_id}")
        _require(row.get("status") in {"success", "skipped_existing", "failed"}, f"batch results line {line_number} has invalid status")
        rows.append(dict(row))
    _require(
        len(rows) == EXPECTED_EXTENSION_COUNT,
        f"immutable formal batch results must contain exactly 485 rows, found {len(rows)}",
    )
    _require(
        repair_report_path is None or not repair_report_path.exists(),
        "formal namespace is immutable; a promotion-style repair report is forbidden",
    )
    original_ids = [_string(row.get("case_unit_dir"), "formal batch case_unit_dir") for row in rows]
    _require(
        len(set(original_ids)) == EXPECTED_EXTENSION_COUNT and set(original_ids) == expected_set,
        "original batch results are not one exact 485-case invocation",
    )
    original_counts = Counter(str(row.get("status")) for row in rows)
    _require(
        original_counts == Counter({"success": EXPECTED_EXTENSION_COUNT}),
        "original batch results must preserve exactly 485 success rows",
    )

    histories: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in expected_ids}
    authoritative: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = str(row["case_unit_dir"])
        histories[case_id].append(row)
        authoritative[case_id] = row
    _require(set(authoritative) == expected_set, "latest-per-case batch authority is incomplete")
    _require(all(len(history) == 1 for history in histories.values()), "formal batch contains duplicate case rows")
    return (
        {
            "total_cases": EXPECTED_EXTENSION_COUNT,
            "success_cases": success_count,
            "skipped_cases": skipped_count,
            "failed_cases": 0,
            "warning_count": 0,
            "historical_result_row_count": len(rows),
            "original_result_row_count": len(rows),
            "appended_repair_row_count": 0,
            "authoritative_case_count": len(authoritative),
            "superseded_result_row_count": 0,
            "historically_superseded_case_count": 0,
            "append_semantics": "forbidden_immutable_exact_485",
            "repair_provenance": {
                "repair_applied": False,
                "repair_case_count": 0,
                "repair_row_count": 0,
                "latest_repairs_by_case": {},
            },
            "batch_summary_path": _repo_relative(summary_path),
            "batch_summary_sha256": sha256_file(summary_path),
            "batch_results_jsonl_path": _repo_relative(results_path),
            "batch_results_jsonl_sha256": sha256_file(results_path),
        },
        histories,
        authoritative,
    )


def _validate_repair_report(
    *,
    repair_report_path: Path | None,
    formal_lock_path: Path | None,
    cases_root: Path,
    summary_path: Path,
    results_path: Path,
    rows: Sequence[Mapping[str, Any]],
    original_rows: Sequence[Mapping[str, Any]],
    appended_rows: Sequence[Mapping[str, Any]],
    authoritative_indices: Mapping[str, int],
) -> dict[str, Any]:
    """Validate the post-generation lock for every appended repair row.

    The original pre-run lock remains immutable.  Repairs are instead bound by
    a separate pre-repair lock and a post-repair report in the same provenance
    directory.  With no appended rows, neither artifact is required.
    """

    if not appended_rows:
        _require(
            repair_report_path is None or not repair_report_path.exists(),
            "repair report exists but the batch JSONL has no appended repair rows",
        )
        return {
            "repair_applied": False,
            "repair_case_count": 0,
            "repair_row_count": 0,
            "latest_repairs_by_case": {},
        }

    _require(repair_report_path is not None, "appended repair rows require a repair report path")
    _require(formal_lock_path is not None, "appended repair rows require the formal draft lock path")
    report_path = _input_file(repair_report_path, "draft repair report")
    formal_lock_file = _input_file(formal_lock_path, "formal draft run lock")
    _require(
        report_path.parent == formal_lock_file.parent
        and report_path.name == DEFAULT_REPAIR_REPORT_PATH.name,
        "draft repair report must be provenance/draft_repair_report.json beside the formal lock",
    )
    report = _load_mapping(report_path, "draft repair report")
    _require(report.get("schema_version") == REPAIR_REPORT_SCHEMA, f"repair report schema must be {REPAIR_REPORT_SCHEMA}")
    _require(report.get("status") == "locked_post_repair", "repair report status must be locked_post_repair")
    _require(report.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID, "repair report draft_run_id mismatch")
    _parse_iso_timestamp(report.get("created_at"), "repair report created_at")
    _require(report.get("cases_root") == _repo_relative(cases_root), "repair report cases_root mismatch")
    _require(report.get("formal_draft_run_lock_path") == _repo_relative(formal_lock_file), "repair report formal lock path mismatch")
    _require(report.get("formal_draft_run_lock_sha256") == sha256_file(formal_lock_file), "repair report formal lock hash mismatch")

    original_batch = _mapping(report.get("original_batch"), "repair report original_batch")
    expected_original_batch = {
        "batch_summary_path": _repo_relative(summary_path),
        "batch_summary_sha256": sha256_file(summary_path),
        "result_row_count": EXPECTED_EXTENSION_COUNT,
        "result_rows_sha256": sha256_object(list(original_rows)),
    }
    _require(dict(original_batch) == expected_original_batch, "repair report original batch binding mismatch")

    repaired_batch = _mapping(report.get("repaired_batch"), "repair report repaired_batch")
    expected_repaired_batch = {
        "batch_results_jsonl_path": _repo_relative(results_path),
        "batch_results_jsonl_sha256": sha256_file(results_path),
        "total_result_row_count": len(rows),
        "appended_success_row_count": len(appended_rows),
    }
    _require(dict(repaired_batch) == expected_repaired_batch, "repair report appended batch binding mismatch")

    repair_lock_ref = _mapping(report.get("repair_lock"), "repair report repair_lock")
    repair_lock_path = _input_file(_string(repair_lock_ref.get("path"), "repair_lock.path"), "draft repair lock")
    _require(
        repair_lock_path.parent == report_path.parent and repair_lock_path.name == "draft_repair_lock.json",
        "repair lock must be provenance/draft_repair_lock.json",
    )
    _require(repair_lock_ref.get("sha256") == sha256_file(repair_lock_path), "repair lock hash mismatch")

    repair_inputs = _mapping(report.get("repair_inputs"), "repair report repair_inputs")
    subset_path = _input_file(_string(repair_inputs.get("case_ids_path"), "repair_inputs.case_ids_path"), "repair subset IDs")
    subset_ids = _load_repair_case_ids(subset_path)
    _require(len(subset_ids) == EXPECTED_REPAIR_CASE_COUNT, f"repair subset must contain exactly {EXPECTED_REPAIR_CASE_COUNT} cases")
    _require(len(set(subset_ids)) == len(subset_ids), "repair subset IDs are duplicated")
    _require(repair_inputs.get("case_count") == EXPECTED_REPAIR_CASE_COUNT, "repair subset case_count mismatch")
    _require(repair_inputs.get("case_ids_sha256") == sha256_file(subset_path), "repair subset file hash mismatch")
    _require(repair_inputs.get("case_ids_semantic_sha256") == sha256_object(subset_ids), "repair subset semantic hash mismatch")
    _require(
        len(appended_rows) == EXPECTED_REPAIR_CASE_COUNT,
        f"formal repair must append exactly {EXPECTED_REPAIR_CASE_COUNT} successful rows",
    )

    supplement_path = _input_file(
        _string(repair_inputs.get("repair_supplement_path"), "repair_inputs.repair_supplement_path"),
        "repair prompt supplement",
    )
    _require(repair_inputs.get("repair_supplement_sha256") == sha256_file(supplement_path), "repair supplement hash mismatch")
    base_prompt = _input_file(_IMPLEMENTATION_PATHS["draft_case_checklist.prompt.md"], "base draft prompt").read_text(encoding="utf-8")
    repair_supplement = supplement_path.read_text(encoding="utf-8")
    effective_prompt_sha256 = sha256_bytes(
        minimal_drafter.compose_prompt(base_prompt, repair_supplement).encode("utf-8")
    )
    _require(
        repair_inputs.get("effective_composed_prompt_sha256") == effective_prompt_sha256,
        "repair effective composed prompt hash mismatch",
    )

    candidate = _mapping(report.get("candidate"), "repair report candidate")
    candidate_root = resolve_repo_path(_string(candidate.get("output_root"), "candidate.output_root")).resolve()
    _require(candidate_root.is_dir() and not candidate_root.is_symlink(), "repair candidate output root is missing or symlinked")
    _require(candidate_root != cases_root and not _path_is_within(candidate_root, cases_root), "repair candidate output must be outside formal cases")
    _validate_no_symlinks(candidate_root)
    _require(candidate.get("tree_sha256") == sha256_path(candidate_root), "repair candidate output tree hash mismatch")

    configuration = _mapping(report.get("repair_configuration"), "repair report configuration")
    expected_configuration = {
        "provider": "codex",
        "llm_call_provider": "codex_cli",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "auth_mode": "codex_login",
        "codex_sandbox": "read-only",
        "max_parallel": 8,
    }
    _require(dict(configuration) == expected_configuration, "repair execution configuration mismatch")

    repair_lock = _load_mapping(repair_lock_path, "draft repair lock")
    original_locked_cases = _validate_repair_lock(
        lock=repair_lock,
        formal_lock_file=formal_lock_file,
        cases_root=cases_root,
        original_batch=expected_original_batch,
        repair_inputs=repair_inputs,
        candidate_root=candidate_root,
        configuration=configuration,
    )
    formal_cases_tree = _mapping(report.get("formal_cases_tree"), "repair report formal_cases_tree")
    _require(
        formal_cases_tree.get("pre_repair_sha256") == repair_lock.get("formal_cases_pre_repair_tree_sha256"),
        "repair report pre-repair formal cases tree hash differs from repair lock",
    )
    _require(
        formal_cases_tree.get("post_repair_sha256") == sha256_path(cases_root),
        "repair report post-repair formal cases tree hash mismatch",
    )

    raw_repairs = report.get("repairs")
    _require(isinstance(raw_repairs, list), "repair report repairs must be a list")
    _require(len(raw_repairs) == len(appended_rows), "repair report must inventory every appended result row")
    original_index_by_case = {
        _string(row.get("case_unit_dir"), "original case_unit_dir"): index
        for index, row in enumerate(original_rows, start=1)
    }
    prior_index_by_case = dict(original_index_by_case)
    prior_new_hashes_by_case: dict[str, Mapping[str, Any]] = {}
    repair_case_ids: list[str] = []
    normalized_repairs: list[dict[str, Any]] = []
    latest_repairs: dict[str, dict[str, Any]] = {}
    for offset, (raw_repair, appended_row) in enumerate(zip(raw_repairs, appended_rows), start=1):
        repair = _mapping(raw_repair, f"repair report entry {offset}")
        row_index = EXPECTED_EXTENSION_COUNT + offset
        case_id = _string(repair.get("case_unit_id"), f"repair entry {offset}.case_unit_id")
        _require(case_id == appended_row.get("case_unit_dir"), f"repair entry {offset} case identity mismatch")
        _require(case_id in subset_ids, f"repair entry {offset} is outside the locked repair subset")
        _require(repair.get("repair_row_index") == row_index, f"repair entry {offset} row index mismatch")
        superseded_index = prior_index_by_case.get(case_id)
        _require(repair.get("superseded_row_index") == superseded_index, f"repair entry {offset} supersession chain mismatch")
        _require(repair.get("repair_row_sha256") == sha256_object(appended_row), f"repair entry {offset} row hash mismatch")
        _require(
            repair.get("superseded_row_sha256") == sha256_object(rows[superseded_index - 1]),
            f"repair entry {offset} superseded row hash mismatch",
        )
        _string(repair.get("reason"), f"repair entry {offset}.reason")

        original_hashes = _canonical_hash_mapping(
            repair.get("original_canonical_file_sha256"),
            label=f"repair entry {offset} original canonical hashes",
        )
        new_hashes = _canonical_hash_mapping(
            repair.get("canonical_file_sha256"),
            label=f"repair entry {offset} new canonical hashes",
        )
        locked_original = original_locked_cases.get(case_id)
        _require(locked_original is not None, f"repair entry {offset} is absent from the pre-repair case lock")
        _require(
            original_hashes == locked_original["canonical_file_sha256"],
            f"repair entry {offset} original canonical hashes differ from the pre-repair lock",
        )
        if case_id in prior_new_hashes_by_case:
            _require(original_hashes == prior_new_hashes_by_case[case_id], f"repair entry {offset} canonical hash chain mismatch")

        backup_root = resolve_repo_path(_string(repair.get("backup_path"), f"repair entry {offset}.backup_path")).resolve()
        _require(backup_root.is_dir() and not backup_root.is_symlink(), f"repair entry {offset} backup is missing or symlinked")
        _require(not _path_is_within(backup_root, cases_root), f"repair entry {offset} backup must be outside formal cases")
        _validate_no_symlinks(backup_root)
        observed_backup_hashes = {
            suffix: sha256_file(_input_file(backup_root / suffix, f"repair backup {case_id} {suffix}"))
            for suffix in EXPECTED_CANONICAL_SUFFIXES
        }
        _require(observed_backup_hashes == original_hashes, f"repair entry {offset} backup canonical hashes mismatch")
        _require(
            repair.get("original_attempt_tree_sha256") == _attempt_tree_sha256(backup_root),
            f"repair entry {offset} backup attempt tree hash mismatch",
        )
        _require(
            repair.get("original_attempt_tree_sha256") == locked_original["attempt_tree_sha256"],
            f"repair entry {offset} original attempt tree hash differs from the pre-repair lock",
        )
        _require(
            _repo_relative(backup_root) == locked_original["backup_path"],
            f"repair entry {offset} backup path differs from the pre-repair lock",
        )

        normalized = {
            "case_unit_id": case_id,
            "superseded_row_index": superseded_index,
            "repair_row_index": row_index,
            "superseded_row_sha256": repair["superseded_row_sha256"],
            "repair_row_sha256": repair["repair_row_sha256"],
            "reason": repair["reason"],
            "backup_path": _repo_relative(backup_root),
            "original_canonical_file_sha256": original_hashes,
            "original_attempt_tree_sha256": repair["original_attempt_tree_sha256"],
            "canonical_file_sha256": new_hashes,
        }
        normalized_repairs.append(normalized)
        latest_repairs[case_id] = normalized
        repair_case_ids.append(case_id)
        prior_index_by_case[case_id] = row_index
        prior_new_hashes_by_case[case_id] = new_hashes

    _require(
        len(set(repair_case_ids)) == EXPECTED_REPAIR_CASE_COUNT and set(repair_case_ids) == set(subset_ids),
        "appended repair rows must cover each locked repair case exactly once",
    )
    _require(
        {case_id: prior_index_by_case[case_id] for case_id in set(repair_case_ids)}
        == {case_id: authoritative_indices[case_id] for case_id in set(repair_case_ids)},
        "repair report does not terminate at the latest authoritative row per repaired case",
    )
    return {
        "repair_applied": True,
        "repair_report_path": _repo_relative(report_path),
        "repair_report_sha256": sha256_file(report_path),
        "repair_lock_path": _repo_relative(repair_lock_path),
        "repair_lock_sha256": sha256_file(repair_lock_path),
        "repair_case_count": len(set(repair_case_ids)),
        "repair_row_count": len(normalized_repairs),
        "repair_case_ids": subset_ids,
        "repair_case_ids_semantic_sha256": sha256_object(subset_ids),
        "candidate_output_root": _repo_relative(candidate_root),
        "candidate_output_tree_sha256": sha256_path(candidate_root),
        "repairs": normalized_repairs,
        "latest_repairs_by_case": latest_repairs,
    }


def _validate_repair_lock(
    *,
    lock: Mapping[str, Any],
    formal_lock_file: Path,
    cases_root: Path,
    original_batch: Mapping[str, Any],
    repair_inputs: Mapping[str, Any],
    candidate_root: Path,
    configuration: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    _require(lock.get("schema_version") == REPAIR_LOCK_SCHEMA, f"repair lock schema must be {REPAIR_LOCK_SCHEMA}")
    _require(lock.get("status") == "locked_pre_repair", "repair lock status must remain locked_pre_repair")
    _require(lock.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID, "repair lock draft_run_id mismatch")
    _parse_iso_timestamp(lock.get("locked_at"), "repair lock locked_at")
    _require(lock.get("formal_draft_run_lock_path") == _repo_relative(formal_lock_file), "repair lock formal lock path mismatch")
    _require(lock.get("formal_draft_run_lock_sha256") == sha256_file(formal_lock_file), "repair lock formal lock hash mismatch")
    _require(lock.get("cases_root") == _repo_relative(cases_root), "repair lock cases_root mismatch")
    _require(dict(_mapping(lock.get("original_batch"), "repair lock original_batch")) == dict(original_batch), "repair lock original batch binding mismatch")
    _require(dict(_mapping(lock.get("repair_inputs"), "repair lock repair_inputs")) == dict(repair_inputs), "repair lock inputs differ from repair report")
    execution = _mapping(lock.get("execution"), "repair lock execution")
    _require(execution.get("candidate_output_root") == _repo_relative(candidate_root), "repair lock candidate output root mismatch")
    for key, value in configuration.items():
        _require(execution.get(key) == value, f"repair lock execution.{key} mismatch")
    _require(execution.get("pre_run_candidate_output_root_exists") is False, "repair candidate namespace was not frozen as absent")
    pre_tree_sha256 = lock.get("formal_cases_pre_repair_tree_sha256")
    _require(
        isinstance(pre_tree_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", pre_tree_sha256) is not None,
        "repair lock pre-repair formal cases tree hash is invalid",
    )
    raw_original_cases = lock.get("original_cases")
    _require(
        isinstance(raw_original_cases, list) and len(raw_original_cases) == EXPECTED_REPAIR_CASE_COUNT,
        f"repair lock must inventory exactly {EXPECTED_REPAIR_CASE_COUNT} original cases",
    )
    original_cases: dict[str, dict[str, Any]] = {}
    for index, raw_case in enumerate(raw_original_cases, start=1):
        item = _mapping(raw_case, f"repair lock original case {index}")
        case_id = _string(item.get("case_unit_id"), f"repair lock original case {index}.case_unit_id")
        _require(case_id not in original_cases, f"repair lock duplicates original case {case_id}")
        attempt_tree_sha256 = item.get("attempt_tree_sha256")
        _require(
            isinstance(attempt_tree_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", attempt_tree_sha256) is not None,
            f"repair lock original case {case_id} attempt tree hash is invalid",
        )
        original_cases[case_id] = {
            "canonical_file_sha256": _canonical_hash_mapping(
                item.get("canonical_file_sha256"),
                label=f"repair lock original case {case_id} canonical hashes",
            ),
            "attempt_tree_sha256": attempt_tree_sha256,
            "backup_path": _string(item.get("backup_path"), f"repair lock original case {case_id}.backup_path"),
        }
    subset_ids = _load_repair_case_ids(
        _input_file(_string(repair_inputs.get("case_ids_path"), "repair_inputs.case_ids_path"), "repair subset IDs")
    )
    _require(set(original_cases) == set(subset_ids), "repair lock original case inventory differs from repair subset")
    return original_cases


def _canonical_hash_mapping(value: Any, *, label: str) -> dict[str, str]:
    mapping = _mapping(value, label)
    _require(set(mapping) == set(EXPECTED_CANONICAL_SUFFIXES), f"{label} file set mismatch")
    normalized: dict[str, str] = {}
    for suffix in EXPECTED_CANONICAL_SUFFIXES:
        digest = mapping.get(suffix)
        _require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, f"{label}.{suffix} is not SHA-256")
        normalized[suffix] = digest
    return normalized


def _attempt_tree_sha256(root: Path) -> str:
    inventory = [
        {"path": path.name, "sha256": sha256_file(path)}
        for path in sorted(root.iterdir(), key=lambda item: item.name)
        if path.is_file() and _ATTEMPT_FILE_RE.fullmatch(path.name)
    ]
    _require(inventory, f"repair backup has no attempt artifacts: {root}")
    return sha256_object(inventory)


def _load_repair_case_ids(path: Path) -> list[str]:
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(f"repair subset JSON is malformed: {exc}") from exc
        if isinstance(payload, Mapping):
            payload = next(
                (payload.get(key) for key in ("case_ids", "repair_case_ids", "selected_case_ids") if key in payload),
                None,
            )
        _require(isinstance(payload, list), "repair subset JSON must be a list or contain a case_ids list")
        values = payload
    else:
        values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    _require(all(isinstance(value, str) and value.strip() for value in values), "repair subset contains an invalid case ID")
    return [str(value).strip() for value in values]


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_case_draft(
    *,
    case: Mapping[str, str],
    case_dir: Path,
    packet_path: Path,
    result_history: Sequence[Mapping[str, Any]],
    authoritative_row: Mapping[str, Any],
    lock: Mapping[str, Any],
    validator: Draft202012Validator,
) -> tuple[dict[str, Any], dict[str, int]]:
    case_id = case["case_unit_id"]
    _require(case_dir.is_dir() and not case_dir.is_symlink(), f"draft case directory missing or symlinked: {case_id}")
    _require(packet_path.is_file() and not packet_path.is_symlink(), f"case packet missing or symlinked: {case_id}")
    entries = list(case_dir.iterdir())
    _require(all(path.is_file() and not path.is_symlink() for path in entries), f"{case_id} contains a directory, symlink, or unsupported entry")
    _validate_no_secret_material(entries, case_id=case_id)
    file_names = {path.name for path in entries}
    canonical_names = set(EXPECTED_CANONICAL_SUFFIXES)
    _require(canonical_names <= file_names, f"{case_id} is missing canonical files: {sorted(canonical_names - file_names)}")
    attempt_groups: dict[int, set[str]] = {}
    for name in sorted(file_names - canonical_names):
        match = _ATTEMPT_FILE_RE.fullmatch(name)
        _require(match is not None, f"{case_id} contains an unsupported file: {name}")
        index = int(match.group("index"))
        _require(index > 0, f"{case_id} attempt indices must start at 01")
        attempt_groups.setdefault(index, set()).add(match.group("suffix"))
    _require(attempt_groups, f"{case_id} has no attempt artifacts")
    _require(sorted(attempt_groups) == list(range(1, max(attempt_groups) + 1)), f"{case_id} attempt indices are not consecutive")
    _require(max(attempt_groups) <= len(EXPECTED_TOKEN_BUDGETS), f"{case_id} has more attempts than locked token budgets")
    allowed_stage_sets = [
        _ATTEMPT_LOG_SUFFIXES | frozenset(_ATTEMPT_STAGE_SUFFIXES[:stage_count])
        for stage_count in range(len(_ATTEMPT_STAGE_SUFFIXES) + 1)
    ]
    for index, suffixes in attempt_groups.items():
        _require(frozenset(suffixes) in allowed_stage_sets, f"{case_id} attempt_{index:02d} has an impossible partial-write inventory: {sorted(suffixes)}")

    current = authoritative_row
    _validate_result_row(current, case_id=case_id, packet_path=packet_path, lock=lock)
    _require(current.get("status") in {"success", "skipped_existing"}, f"{case_id} authoritative result is not successful")
    success_record = next((row for row in reversed(result_history) if row.get("status") == "success"), None)
    _require(success_record is not None, f"{case_id} has no successful result provenance in the append log")
    _validate_result_row(success_record, case_id=case_id, packet_path=packet_path, lock=lock)
    attempts = success_record.get("attempts")
    _require(isinstance(attempts, list) and attempts, f"{case_id} successful result has no attempt records")
    attempt_records: dict[int, Mapping[str, Any]] = {}
    for position, raw_attempt in enumerate(attempts, start=1):
        attempt = _mapping(raw_attempt, f"{case_id} attempt result {position}")
        index = _integer(attempt.get("attempt_index"), f"{case_id} attempt_index")
        _require(index == position, f"{case_id} result attempt indices are not consecutive")
        _require(attempt.get("max_output_tokens") == EXPECTED_TOKEN_BUDGETS[index - 1], f"{case_id} attempt {index} token budget mismatch")
        _require(attempt.get("http_timeout_seconds") in {180, 480}, f"{case_id} attempt {index} HTTP timeout mismatch")
        expected_codex_timeout = 3600 if success_record.get("lane") == "oversized" else 1800
        _require(attempt.get("codex_timeout_seconds") == expected_codex_timeout, f"{case_id} attempt {index} Codex timeout mismatch")
        _integer(attempt.get("returncode"), f"{case_id} attempt {index}.returncode")
        attempt_records[index] = attempt
    _require(set(attempt_records) == set(attempt_groups), f"{case_id} current attempt inventory/result records mismatch")

    matching_indices: list[int] = []
    for index, suffixes in attempt_groups.items():
        if suffixes != canonical_names:
            continue
        if all(
            (case_dir / suffix).read_bytes() == (case_dir / f"attempt_{index:02d}.{suffix}").read_bytes()
            for suffix in EXPECTED_CANONICAL_SUFFIXES
        ):
            matching_indices.append(index)
    _require(len(matching_indices) == 1, f"{case_id} canonical files must byte-match exactly one complete attempt; matches={matching_indices}")
    successful_index = matching_indices[0]
    successful_record = attempt_records[successful_index]
    _require(successful_record.get("returncode") == 0, f"{case_id} promoted attempt did not exit zero")
    _require(
        _string(successful_record.get("validator"), f"{case_id} successful validator output").startswith("checklist valid:"),
        f"{case_id} promoted attempt lacks successful official validator provenance",
    )
    for index in range(1, successful_index):
        earlier = attempt_records[index]
        _require(
            earlier.get("returncode") != 0 or not str(earlier.get("validator") or "").startswith("checklist valid:"),
            f"{case_id} runner failed to promote the first valid attempt",
        )
    _require(successful_index == max(attempt_groups), f"{case_id} contains attempts after the promoted success")

    checklist_yaml = _load_mapping(case_dir / "checklist.yaml", f"{case_id} checklist YAML")
    checklist_json = _load_mapping(case_dir / "checklist.json", f"{case_id} checklist JSON")
    _require(checklist_yaml == checklist_json, f"{case_id} canonical YAML/JSON are not semantically equal")
    _require(checklist_json.get("schema_version") == "case_checklist_v1", f"{case_id} checklist schema mismatch")
    _require(checklist_json.get("domain") == "appworld", f"{case_id} checklist domain mismatch")
    _require(checklist_json.get("case_unit_id") == case_id, f"{case_id} checklist case_unit_id mismatch")
    _require(checklist_json.get("task_id") == case["task_id"], f"{case_id} checklist task_id mismatch")
    errors = sorted(validator.iter_errors(checklist_json), key=lambda error: list(error.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.absolute_path) or "<root>"
        raise ContractLifecycleError(f"{case_id} failed official checklist schema at {location}: {first.message}")
    _validate_support_inventory(checklist_json, packet_path=packet_path, case_id=case_id)

    attempt_prefix = f"attempt_{successful_index:02d}"
    llm_call = _load_mapping(case_dir / "llm_call.json", f"{case_id} llm_call sidecar")
    api_response = _load_mapping(case_dir / "api_response.json", f"{case_id} API response sidecar")
    usage = _validate_minimal_codex_sidecars(
        case_id=case_id,
        checklist=checklist_json,
        llm_call=llm_call,
        api_response=api_response,
        reasoning_summary=(case_dir / "reasoning_summary.txt").read_text(encoding="utf-8"),
        attempt_prefix=attempt_prefix,
        attempt_record=successful_record,
    )

    canonical_hashes = {suffix: sha256_file(case_dir / suffix) for suffix in EXPECTED_CANONICAL_SUFFIXES}
    attempt_hashes = {
        name: sha256_file(case_dir / name)
        for name in sorted(file_names - canonical_names)
    }
    case_hash_payload = {
        "case_unit_id": case_id,
        "dataset_name": case["dataset_name"],
        "successful_attempt_index": successful_index,
        "canonical_files": canonical_hashes,
        "attempt_files": attempt_hashes,
        "external_call_provenance": {
            "protocol": "neurips_ed_track_minimal_codex_cli_sidecar.v1",
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "requested_model_alias": EXPECTED_MODEL,
            "backend_model_revision": None,
            "reasoning_effort": EXPECTED_REASONING_EFFORT,
            "sandbox": "read-only",
            "response_id": api_response["id"],
            "request_timestamp": llm_call["request_timestamp"],
            "response_timestamp": llm_call["response_timestamp"],
            "turn_completed": True,
            "max_output_tokens_enforced": False,
        },
    }
    return ({**case_hash_payload, "case_draft_sha256": sha256_object(case_hash_payload)}, usage)


def _validate_result_row(
    row: Mapping[str, Any],
    *,
    case_id: str,
    packet_path: Path,
    lock: Mapping[str, Any],
) -> None:
    _require(row.get("case_unit_dir") == case_id, f"{case_id} result identity mismatch")
    _require(row.get("case_packet") == _repo_relative(packet_path), f"{case_id} result packet pointer mismatch")
    _require(row.get("case_packet_size_bytes") == packet_path.stat().st_size, f"{case_id} result packet size mismatch")
    threshold = _integer(_mapping(lock.get("drafter"), "drafter").get("large_case_threshold_bytes"), "large threshold")
    expected_lane = "oversized" if packet_path.stat().st_size > threshold else "regular"
    _require(row.get("lane") == expected_lane, f"{case_id} result lane mismatch")
    warnings = row.get("quality_warnings")
    _require(warnings == [], f"{case_id} result contains quality warnings")


def _validate_minimal_codex_sidecars(
    *,
    case_id: str,
    checklist: Mapping[str, Any],
    llm_call: Mapping[str, Any],
    api_response: Mapping[str, Any],
    reasoning_summary: str,
    attempt_prefix: str,
    attempt_record: Mapping[str, Any],
) -> dict[str, int]:
    expected_llm_fields = {
        "schema_version", "provider", "model", "model_version", "api_key_env", "domain",
        "case_unit_id", "task_id", "phase", "experiment_type", "agent_id_or_role",
        "request_timestamp", "response_timestamp", "temperature", "max_tokens", "timeout_seconds",
        "retry_index", "token_usage", "cost", "response_metadata",
    }
    _require(set(llm_call) == expected_llm_fields, f"{case_id} minimal llm_call field set mismatch")
    expected_llm_values = {
        "schema_version": "llm_call/v1",
        "provider": "codex_cli",
        "model": EXPECTED_MODEL,
        "model_version": EXPECTED_MODEL,
        "api_key_env": "CODEX_HOME",
        "domain": "appworld",
        "case_unit_id": case_id,
        "task_id": case_id,
        "phase": "draft",
        "experiment_type": "minimal_package",
        "agent_id_or_role": "case_checklist_drafter",
        "temperature": 0.0,
        "max_tokens": attempt_record["max_output_tokens"],
        "timeout_seconds": attempt_record["codex_timeout_seconds"],
        "retry_index": 0,
    }
    for key, expected in expected_llm_values.items():
        _require(llm_call.get(key) == expected, f"{case_id} llm_call.{key} mismatch: {llm_call.get(key)!r}")
    requested_at = _parse_iso_timestamp(llm_call.get("request_timestamp"), f"{case_id} request_timestamp")
    responded_at = _parse_iso_timestamp(llm_call.get("response_timestamp"), f"{case_id} response_timestamp")
    _require(responded_at >= requested_at, f"{case_id} response timestamp precedes request")

    metadata = _mapping(llm_call.get("response_metadata"), f"{case_id} response_metadata")
    expected_metadata = {
        "response_status": "completed",
        "provider_model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "auth_mode": "codex_login",
        "max_output_tokens_enforced": False,
    }
    for key, expected in expected_metadata.items():
        _require(metadata.get(key) == expected, f"{case_id} response_metadata.{key} mismatch")
    _require(str(metadata.get("raw_api_response_path") or "").replace("\\", "/").endswith(f"/{case_id}/{attempt_prefix}.api_response.json"), f"{case_id} raw API response pointer mismatch")
    _require(str(metadata.get("reasoning_summary_path") or "").replace("\\", "/").endswith(f"/{case_id}/{attempt_prefix}.reasoning_summary.txt"), f"{case_id} reasoning summary pointer mismatch")

    expected_api_fields = {"id", "status", "model", "provider", "output_text", "output", "usage", "codex_cli"}
    _require(set(api_response) == expected_api_fields, f"{case_id} Codex API sidecar field set mismatch")
    _require(api_response.get("status") == "completed", f"{case_id} API response is not completed")
    _require(api_response.get("provider") == "codex_cli", f"{case_id} API provider mismatch")
    _require(api_response.get("model") == EXPECTED_MODEL, f"{case_id} API model mismatch")
    _require(metadata.get("response_id") == api_response.get("id"), f"{case_id} response ID mismatch")
    codex = _mapping(api_response.get("codex_cli"), f"{case_id} codex_cli")
    _require(codex.get("auth_mode") == "codex_login", f"{case_id} Codex auth mode mismatch")
    _require(codex.get("returncode") == 0, f"{case_id} Codex returncode is not zero")
    _require(codex.get("sandbox") == "read-only", f"{case_id} Codex sandbox mismatch")
    _require(codex.get("timeout_seconds") == llm_call.get("timeout_seconds"), f"{case_id} timeout sidecars mismatch")
    _require(codex.get("malformed_event_lines") == [], f"{case_id} Codex event stream contains malformed lines")
    _validate_codex_command(codex.get("command"), case_id=case_id)
    events = codex.get("events")
    _require(isinstance(events, list) and events and all(isinstance(event, Mapping) for event in events), f"{case_id} Codex events must be a nonempty mapping list")
    completed_events = [event for event in events if event.get("type") == "turn.completed"]
    _require(len(completed_events) == 1 and events[-1].get("type") == "turn.completed", f"{case_id} must contain exactly one final turn.completed event")

    output_text = _string(api_response.get("output_text"), f"{case_id} output_text")
    try:
        body = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise ContractLifecycleError(f"{case_id} Codex output_text is malformed JSON: {exc}") from exc
    _require(isinstance(body, dict), f"{case_id} Codex output body must be a mapping")
    normalized_body = minimal_drafter.strip_null_fields(body)
    expected_body = {key: value for key, value in checklist.items() if key not in {"schema_version", "case_unit_id", "domain", "task_id"}}
    _require(normalized_body == expected_body, f"{case_id} Codex output body differs from canonical checklist body after the drafter's null stripping")
    _require(minimal_drafter.extract_json_text(dict(api_response)) == body, f"{case_id} provider output extraction differs from output_text")
    expected_reasoning = minimal_drafter.extract_reasoning_summary_text(dict(api_response))
    expected_reasoning = expected_reasoning + ("\n" if expected_reasoning else "")
    _require(reasoning_summary == expected_reasoning, f"{case_id} reasoning summary is not the exact extractor output")

    usage = _mapping(llm_call.get("token_usage"), f"{case_id} token_usage")
    expected_usage_keys = {"prompt_tokens", "completion_tokens", "cached_prompt_tokens", "reasoning_tokens", "total_tokens"}
    _require(set(usage) == expected_usage_keys, f"{case_id} token usage field set mismatch")
    normalized_usage = minimal_drafter.extract_token_usage(dict(api_response))
    _require(dict(usage) == normalized_usage, f"{case_id} llm_call/API token usage mismatch")
    for key, value in usage.items():
        _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{case_id} token usage {key} is invalid")
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        _require(usage[key] > 0, f"{case_id} token usage {key} must be nonzero")
    _require(usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"], f"{case_id} token total mismatch")
    completed_usage = _mapping(completed_events[0].get("usage"), f"{case_id} turn.completed usage")
    _require(int(completed_usage.get("input_tokens", 0) or 0) == usage["prompt_tokens"], f"{case_id} event/API input token mismatch")
    _require(int(completed_usage.get("output_tokens", 0) or 0) == usage["completion_tokens"], f"{case_id} event/API output token mismatch")

    cost = _mapping(llm_call.get("cost"), f"{case_id} cost")
    _require(cost.get("amount") is None and cost.get("total_cost_usd") is None, f"{case_id} Codex login cost must be unavailable")
    _require(cost.get("cost_calculation_method") == "unavailable" and cost.get("missing_cost_reason") == "provider_cost_unavailable", f"{case_id} Codex cost provenance mismatch")
    return {key: int(value) for key, value in usage.items()}


def _validate_codex_command(raw_command: Any, *, case_id: str) -> None:
    _require(isinstance(raw_command, list) and all(isinstance(item, str) for item in raw_command), f"{case_id} Codex command must be a string list")
    command = list(raw_command)
    _require(len(command) >= 4 and command[:2] == ["codex", "exec"], f"{case_id} Codex command prefix mismatch")
    try:
        cd_index = command.index("--cd")
        workspace = command[cd_index + 1]
    except (ValueError, IndexError) as exc:
        raise ContractLifecycleError(f"{case_id} Codex command lacks --cd workspace") from exc
    expected = [
        "codex", "exec", "--cd", workspace, "--skip-git-repo-check", "--ephemeral",
        "--ignore-user-config", "--sandbox", "read-only", "--model", EXPECTED_MODEL,
        "-c", f'model_reasoning_effort="{EXPECTED_REASONING_EFFORT}"',
        "-c", f'model_verbosity="{EXPECTED_MODEL_VERBOSITY}"',
        "--color", "never", "--json", "--output-schema", str(Path(workspace) / "output_schema.json"),
        "-o", str(Path(workspace) / "draft_body.json"), "-",
    ]
    _require(command == expected, f"{case_id} Codex command flags drift")


def _validate_support_inventory(checklist: Mapping[str, Any], *, packet_path: Path, case_id: str) -> None:
    """Run the same packet-aware guardrail gate as the official CLI."""

    try:
        packet_text = packet_path.read_text(encoding="utf-8")
        allowed_paths = case_packet_support_paths(packet_text)
        validate_checklist_guardrails(
            dict(checklist),
            allowed_source_paths=allowed_paths,
        )
        for pointer in _iter_support_pointers(checklist):
            path_part, _, location = pointer.partition("::")
            if path_part == "case_packet.md":
                source_path = packet_path
            else:
                source_path = packet_path.parent / "raw_case" / path_part
            _require(
                source_path.is_file() and not source_path.is_symlink(),
                f"{case_id} support source is missing from the materialized packet: {path_part}",
            )
            _require(
                _support_location_resolves(
                    source_path,
                    location,
                    packet_path=packet_path if path_part != "case_packet.md" else None,
                    packet_source_path=path_part if path_part != "case_packet.md" else None,
                ),
                f"{case_id} support location does not resolve in {path_part}: {location}",
            )
    except Exception as exc:
        # The broad catch is deliberate: the official helper raises its own
        # ChecklistGuardrailError, which is normalized into this lifecycle gate.
        raise ContractLifecycleError(
            f"{case_id} failed official packet-aware checklist guardrails: {exc}"
        ) from exc


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


def _support_location_resolves(
    path: Path,
    location: str,
    *,
    packet_path: Path | None = None,
    packet_source_path: str | None = None,
) -> bool:
    location = location.strip()
    if not location:
        return False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    line_match = re.fullmatch(
        r"(?:(?:lines?|L)\s*)?([1-9][0-9]*)"
        r"(?:\s*-\s*(?:L\s*)?([1-9][0-9]*))?",
        location,
        re.IGNORECASE,
    )
    if line_match:
        start = int(line_match.group(1))
        end = int(line_match.group(2) or start)
        if start <= end <= len(lines):
            return True
        if packet_path is not None and packet_source_path is not None:
            return _packet_section_span_resolves(
                packet_path=packet_path,
                packet_source_path=packet_source_path,
                start=start,
                end=end,
            )
        return False
    if path.suffix == ".json":
        try:
            payload: Any = json.loads(text)
        except json.JSONDecodeError:
            return False
        # ``$`` is the standard JSONPath expression for the document root;
        # ``root`` is the explicit human-readable root label emitted by the
        # drafter.  Both remain resolvable when the root is a scalar or null.
        if location in {"$", "root"}:
            return True
        if not isinstance(payload, (Mapping, list)) and location == json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ):
            return True
        tokens = _json_location_tokens(location)
        if tokens is not None and _json_tokens_resolve(payload, tokens):
            return True
    # Python symbols, JSONL model/table labels, and prose headings are all
    # resolvable when the asserted location occurs as a bounded literal.
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(location)}(?![A-Za-z0-9_])", text) is not None


def _packet_section_span_resolves(
    *,
    packet_path: Path,
    packet_source_path: str,
    start: int,
    end: int,
) -> bool:
    if start < 1 or end < start or not packet_path.is_file() or packet_path.is_symlink():
        return False
    packet_lines = packet_path.read_text(encoding="utf-8").splitlines()
    heading = f"### `{packet_source_path}`"
    heading_lines = [index for index, line in enumerate(packet_lines, start=1) if line == heading]
    if len(heading_lines) != 1:
        return False
    heading_line = heading_lines[0]
    next_heading = next(
        (
            index
            for index, line in enumerate(packet_lines[heading_line:], start=heading_line + 1)
            if line.startswith("### `") and line.endswith("`")
        ),
        len(packet_lines) + 1,
    )
    return heading_line <= start <= end < next_heading


def _json_location_tokens(location: str) -> list[str | int] | None:
    """Parse the small, unambiguous JSON-location subset emitted by drafts.

    Supported forms include dotted or slash-separated object keys, numeric
    list segments, and standard JSONPath-style numeric brackets.  Quoted
    bracket keys, wildcards, filters, recursive descent, and empty segments are
    deliberately rejected so acceptance remains fail-closed.
    """

    expression = location.strip()
    if expression.startswith("$"):
        expression = expression[1:]
        if expression.startswith((".", "/")):
            expression = expression[1:]
    if not expression:
        return None

    tokens: list[str | int] = []
    index = 0
    expecting_segment = True
    while index < len(expression):
        character = expression[index]
        if character in "./":
            if expecting_segment:
                return None
            expecting_segment = True
            index += 1
            continue
        if character == "[":
            if expecting_segment and index != 0:
                return None
            close = expression.find("]", index + 1)
            if close < 0:
                return None
            raw_index = expression[index + 1 : close]
            if not raw_index.isdigit():
                return None
            tokens.append(int(raw_index))
            expecting_segment = False
            index = close + 1
            continue
        if character == "]":
            return None

        if not expecting_segment:
            return None

        end = index
        while end < len(expression) and expression[end] not in "./[]":
            end += 1
        raw_token = expression[index:end]
        if not raw_token:
            return None
        tokens.append(raw_token)
        expecting_segment = False
        index = end

    return None if expecting_segment or not tokens else tokens


def _json_tokens_resolve(payload: Any, tokens: Sequence[str | int]) -> bool:
    current = payload
    for token in tokens:
        if isinstance(token, str) and isinstance(current, Mapping) and token in current:
            current = current[token]
        elif (
            (isinstance(token, int) and not isinstance(token, bool) or isinstance(token, str) and token.isdigit())
            and isinstance(current, list)
            and 0 <= int(token) < len(current)
        ):
            current = current[int(token)]
        else:
            return False
    return True


def _validate_no_secret_material(paths: Sequence[Path], *, case_id: str) -> None:
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ContractLifecycleError(f"{case_id} draft artifact is not UTF-8 text: {path.name}") from exc
        for pattern in _SECRET_PATTERNS:
            _require(pattern.search(text) is None, f"{case_id} draft artifact contains secret-like material: {path.name}")


def _validate_execution_command(lock: Mapping[str, Any]) -> None:
    inputs = _mapping(lock.get("inputs"), "inputs")
    execution = _mapping(lock.get("execution"), "execution")
    command = shlex.split(_string(execution.get("command"), "execution.command"))
    expected = [
        "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=.", ".venv/bin/python",
        "neurips_ed_track_minimal/scripts/run_draft_batch.py",
        "--case-packet-root", _string(inputs.get("case_packet_root"), "inputs.case_packet_root"),
        "--output-root", _string(execution.get("output_root"), "execution.output_root"),
        "--provider", "codex", "--model", EXPECTED_MODEL, "--reasoning-effort", EXPECTED_REASONING_EFFORT,
        "--token-budgets", ",".join(str(value) for value in EXPECTED_TOKEN_BUDGETS),
        "--max-parallel", "8", "--large-max-parallel", "8", "--large-case-threshold-bytes", "100000",
        "--codex-timeout-seconds", "1800", "--large-codex-timeout-seconds", "3600",
        "--codex-sandbox", "read-only", "--prompt-supplement",
        "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
        "--sort-by", "size", "--sleep-seconds", "2.0",
        "--quality-check", "none",
    ]
    _require(command == expected, "locked draft execution command drift")


def _validate_no_symlinks(root: Path) -> None:
    for path in root.rglob("*"):
        _require(not path.is_symlink(), f"draft artifact tree contains a symlink: {path}")


def _input_file(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path)
    _require(resolved.is_file(), f"{label} is missing: {resolved}")
    _require(not resolved.is_symlink(), f"{label} must not be a symlink: {resolved}")
    return resolved.resolve()


def _provenance_output(path: str | Path, *, provenance_root: Path, label: str) -> Path:
    resolved = resolve_repo_path(path).resolve()
    _require(resolved.suffix == ".json" and resolved.parent == provenance_root, f"{label} must be a JSON file directly inside {provenance_root}")
    return resolved


def _load_mapping(path: str | Path, label: str) -> dict[str, Any]:
    try:
        payload = load_json_or_yaml(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ContractLifecycleError(f"failed to load {label} from {path}: {exc}") from exc
    return dict(_mapping(payload, label))


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be a mapping")
    return value


def _string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value.strip(), f"{label} must be a nonempty string")
    return value


def _integer(value: Any, label: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{label} must be an integer")
    return value


def _parse_iso_timestamp(value: Any, label: str) -> datetime:
    text = _string(value, label)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractLifecycleError(f"{label} is not an ISO-8601 timestamp: {text}") from exc


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path).resolve()
    try:
        return resolved.relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractLifecycleError(message)
