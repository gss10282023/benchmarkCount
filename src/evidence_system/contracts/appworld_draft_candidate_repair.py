"""Candidate-only repair orchestration for the AppWorld draft subset.

The formal 485-case generation namespace is immutable input to this workflow.
This module can freeze a separate repair lock and generate new drafts only in a
clean candidate namespace.  It deliberately provides no promotion operation.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from evidence_system.contracts.appworld_draft_acceptance import (
    DEFAULT_LOCK_PATH as DEFAULT_FORMAL_LOCK_PATH,
    EXPECTED_CANONICAL_SUFFIXES,
    _attempt_tree_sha256,
    _iter_support_pointers,
    _load_mapping,
    _validate_lock,
    _validate_locked_inputs,
    _validate_minimal_codex_sidecars,
    _validate_no_secret_material,
    _validate_support_inventory,
    _SECRET_PATTERNS,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import repo_root, resolve_repo_path
from neurips_ed_track_minimal.scripts import draft_case_checklist as minimal_drafter
from neurips_ed_track_minimal.scripts import run_draft_batch


REPAIR_LOCK_SCHEMA = "appworld_draft_repair_lock.v1"
CANDIDATE_RESULTS_SCHEMA = "appworld_draft_candidate_results.v1"
CANDIDATE_SUMMARY_SCHEMA = "appworld_draft_candidate_summary.v1"
CANDIDATE_VALIDATION_SCHEMA = "appworld_draft_candidate_validation.v1"

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

DEFAULT_REPAIR_SUPPLEMENT = Path(
    "neurips_ed_track_minimal/prompts/draft_source_pointer_repair_v1.supplement.md"
)
DEFAULT_SCHEMA_PATH = Path("neurips_ed_track_minimal/schemas/case_checklist.schema.json")

EXPECTED_REPAIR_SUPPLEMENT_SHA256 = (
    "f565f7b2ca21ab52db4b6bc71f9c7995a0b29699222b11258d17f28112c537b7"
)
EXPECTED_EFFECTIVE_PROMPT_SHA256 = (
    "9db2f83202968e18a14c21461676589369d06e2888d6cd18c0f7806dde4a4828"
)
EXPECTED_PROVIDER = "codex"
EXPECTED_MODEL = "gpt-5.4"
EXPECTED_REASONING_EFFORT = "high"
EXPECTED_CODEX_SANDBOX = "read-only"
EXPECTED_TOKEN_BUDGETS = (12000, 16000, 20000)
EXPECTED_MAX_PARALLEL = 8
EXPECTED_LARGE_THRESHOLD_BYTES = 100_000
EXPECTED_REGULAR_HTTP_TIMEOUT_SECONDS = 180
EXPECTED_OVERSIZED_HTTP_TIMEOUT_SECONDS = 480
EXPECTED_REGULAR_CODEX_TIMEOUT_SECONDS = 1800
EXPECTED_OVERSIZED_CODEX_TIMEOUT_SECONDS = 3600
EXPECTED_SLEEP_SECONDS = 2.0

_RESULTS_NAME = "_candidate_results.jsonl"
_SUMMARY_NAME = "_candidate_summary.json"
_VALIDATION_NAME = "_candidate_validation.json"
_ROOT_METADATA_NAMES = frozenset({_RESULTS_NAME, _SUMMARY_NAME, _VALIDATION_NAME})
_ATTEMPT_STAGE_SUFFIXES = (
    "api_response.json",
    "reasoning_summary.txt",
    "llm_call.json",
    "checklist.yaml",
    "checklist.json",
)
_ATTEMPT_LOG_SUFFIXES = frozenset({"stderr.log", "stdout.log"})
_MINIMAL_ENV_ALLOWLIST = (
    "PATH",
    "PYTHONPATH",
    "PYTHONDONTWRITEBYTECODE",
    "HOME",
    "CODEX_HOME",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "NO_PROXY",
)
_CODEX_EVENT_COMMAND_POLICY = "temp_workspace_relative_reads_only_v1"


@dataclass(frozen=True)
class CandidateRepairContext:
    """Fully validated immutable inputs for one candidate run."""

    repair_lock_path: Path
    repair_lock_sha256: str
    formal_lock_path: Path
    formal_cases_root: Path
    formal_cases_tree_sha256: str
    formal_cases_strict_tree_sha256: str
    formal_cases_file_count: int
    formal_cases_directory_count: int
    formal_cases_size_bytes: int
    case_packet_root: Path
    candidate_output_root: Path
    prompt_supplement: Path
    cases: tuple[dict[str, Any], ...]


def load_repair_case_ids(path: str | Path) -> tuple[str, ...]:
    """Load and fail closed unless the file names exactly the frozen 12 IDs."""

    ids_path = _input_file(path, "repair subset IDs")
    text = ids_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raw_ids: Any = [line.strip() for line in text.splitlines() if line.strip()]
    else:
        raw_ids = payload.get("case_ids") if isinstance(payload, Mapping) else payload
    _require(isinstance(raw_ids, list), "repair subset IDs must be a newline list, JSON list, or {case_ids: [...]} object")
    _require(all(isinstance(value, str) and value for value in raw_ids), "repair subset IDs must be nonempty strings")
    _require(len(raw_ids) == len(set(raw_ids)), "repair subset IDs contain duplicates")
    actual_set = frozenset(raw_ids)
    missing = sorted(EXPECTED_REPAIR_CASE_SET - actual_set)
    extra = sorted(actual_set - EXPECTED_REPAIR_CASE_SET)
    _require(not missing and not extra, f"repair subset must be the exact frozen 12 IDs; missing={missing}, extra={extra}")
    _require(tuple(raw_ids) == EXPECTED_REPAIR_CASE_IDS, "repair subset IDs must use the frozen deterministic order")
    return EXPECTED_REPAIR_CASE_IDS


def prepare_candidate_repair_lock(
    *,
    subset_ids_path: str | Path,
    repair_lock_path: str | Path,
    candidate_output_root: str | Path,
    formal_lock_path: str | Path = DEFAULT_FORMAL_LOCK_PATH,
    prompt_supplement_path: str | Path = DEFAULT_REPAIR_SUPPLEMENT,
) -> dict[str, Any]:
    """Freeze a separate pre-run lock without modifying the formal draft run."""

    subset_file = _input_file(subset_ids_path, "repair subset IDs")
    case_ids = load_repair_case_ids(subset_file)
    formal_lock_file = _input_file(formal_lock_path, "formal draft lock")
    formal_lock = _load_mapping(formal_lock_file, "formal draft lock")
    formal_cases_root = resolve_repo_path(
        _string(_mapping(formal_lock.get("execution"), "formal execution").get("output_root"), "formal execution.output_root")
    ).resolve()
    _validate_lock(lock_file=formal_lock_file, lock=formal_lock, cases_root=formal_cases_root)
    _, manifest_cases = _validate_locked_inputs(formal_lock)

    candidate_root = resolve_repo_path(candidate_output_root).resolve()
    repair_lock_file = resolve_repo_path(repair_lock_path).resolve()
    supplement = _input_file(prompt_supplement_path, "repair prompt supplement")
    packet_root = resolve_repo_path(
        _string(_mapping(formal_lock.get("inputs"), "formal inputs").get("case_packet_root"), "formal inputs.case_packet_root")
    ).resolve()

    _validate_output_separation(
        candidate_root=candidate_root,
        repair_lock_file=repair_lock_file,
        formal_cases_root=formal_cases_root,
        formal_lock_file=formal_lock_file,
    )
    _require_repair_lock_location(repair_lock_file, formal_lock_file)
    _require(repair_lock_file.name == "draft_repair_lock.json", "repair lock filename must be draft_repair_lock.json")
    _require(not repair_lock_file.exists(), f"repair lock already exists; refusing to overwrite: {repair_lock_file}")
    preexisting = candidate_root.exists()
    _require(not preexisting, f"candidate output root must be absent when the repair is locked: {candidate_root}")
    entry_count = 0
    _require_no_symlinks(formal_cases_root, "formal cases root")
    _require_no_symlinks(packet_root, "case packet root")

    _validate_repair_prompt(formal_lock=formal_lock, supplement=supplement)
    manifest_by_id = {str(case["case_unit_id"]): case for case in manifest_cases}
    selected_cases: list[dict[str, Any]] = []
    packet_hashes: dict[str, str] = {}
    formal_case_hashes: dict[str, dict[str, str]] = {}
    original_cases: list[dict[str, Any]] = []
    backup_root = candidate_root.parent / "backups"
    _require(not backup_root.exists(), f"repair backup root must be absent when locked: {backup_root}")
    for case_id in case_ids:
        _require(case_id in manifest_by_id, f"repair case is not in the frozen extension manifest: {case_id}")
        case = manifest_by_id[case_id]
        packet_path = _input_file(packet_root / case_id / "case_packet.md", f"case packet {case_id}")
        formal_case_dir = _input_directory(formal_cases_root / case_id, f"formal case {case_id}")
        packet_hashes[case_id] = sha256_file(packet_path)
        formal_case_hashes[case_id] = _canonical_hashes(formal_case_dir, case_id=case_id)
        original_cases.append(
            {
                "case_unit_id": case_id,
                "canonical_file_sha256": formal_case_hashes[case_id],
                "attempt_tree_sha256": _attempt_tree_sha256(formal_case_dir),
                "backup_path": _repo_relative(backup_root / case_id),
            }
        )
        selected_cases.append(
            {
                "case_unit_id": case_id,
                "task_id": str(case["task_id"]),
                "dataset_name": str(case["dataset_name"]),
                "case_packet": _repo_relative(packet_path),
                "case_packet_size_bytes": packet_path.stat().st_size,
            }
        )

    formal_tree_hash = sha256_path(formal_cases_root)
    formal_inventory = _strict_tree_inventory(formal_cases_root, label="formal cases root")
    batch_results = _input_file(formal_cases_root / "_batch_results.jsonl", "formal batch results")
    batch_summary = _input_file(formal_cases_root / "_batch_summary.json", "formal batch summary")
    original_rows = _load_jsonl(batch_results)
    _require(len(original_rows) == 485, f"formal batch must have exactly 485 pre-repair result rows, found {len(original_rows)}")
    base_prompt = _input_file(
        "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md",
        "base draft prompt",
    )
    codex_runtime = _codex_runtime()
    formal_runtime = _mapping(formal_lock.get("runtime"), "formal runtime")
    _require(codex_runtime["codex_cli_version"] == formal_runtime.get("codex_cli_version"), "Codex CLI version differs from the formal run")
    _require(codex_runtime["codex_executable_sha256"] == formal_runtime.get("codex_executable_sha256"), "Codex executable differs from the formal run")
    login_status = _codex_login_status()
    _require(login_status == "Logged in using ChatGPT", f"Codex CLI is not in the locked ChatGPT-login state: {login_status!r}")

    lock = {
        "schema_version": REPAIR_LOCK_SCHEMA,
        "status": "locked_pre_repair",
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "draft_run_id": _string(formal_lock.get("draft_run_id"), "formal draft_run_id"),
        "formal_draft_run_lock_path": _repo_relative(formal_lock_file),
        "formal_draft_run_lock_sha256": sha256_file(formal_lock_file),
        "cases_root": _repo_relative(formal_cases_root),
        "formal_cases_pre_repair_tree_sha256": formal_tree_hash,
        "formal_cases_pre_repair_strict_tree_sha256": formal_inventory["tree_sha256"],
        "original_cases": original_cases,
        "original_batch": {
            "batch_summary_path": _repo_relative(batch_summary),
            "batch_summary_sha256": sha256_file(batch_summary),
            "result_row_count": 485,
            "result_rows_sha256": sha256_object(original_rows),
        },
        "repair_inputs": {
            "case_ids_path": _repo_relative(subset_file),
            "case_count": len(case_ids),
            "case_ids_sha256": sha256_file(subset_file),
            "case_ids_semantic_sha256": sha256_object(list(case_ids)),
            "repair_supplement_path": _repo_relative(supplement),
            "repair_supplement_sha256": sha256_file(supplement),
            "effective_composed_prompt_sha256": _effective_prompt_sha256(base_prompt, supplement),
        },
        "repair_reason": (
            "The frozen drafts for exactly these 12 cases contain support locations that fail the "
            "strict packet inventory/location resolver. Generate isolated replacement candidates only."
        ),
        "case_ids": list(case_ids),
        "case_ids_semantic_sha256": sha256_object(list(case_ids)),
        "subset_ids_path": _repo_relative(subset_file),
        "subset_ids_file_sha256": sha256_file(subset_file),
        "formal_generation": {
            "lock_path": _repo_relative(formal_lock_file),
            "lock_sha256": sha256_file(formal_lock_file),
            "cases_root": _repo_relative(formal_cases_root),
            "cases_tree_sha256": formal_tree_hash,
            "strict_tree_sha256": formal_inventory["tree_sha256"],
            "file_count": formal_inventory["file_count"],
            "directory_count": formal_inventory["directory_count"],
            "size_bytes": formal_inventory["size_bytes"],
            "batch_results_sha256": sha256_file(batch_results),
            "batch_summary_sha256": sha256_file(batch_summary),
            "selected_case_canonical_hashes": formal_case_hashes,
            "mutation_allowed": False,
        },
        "inputs": {
            "case_packet_root": _repo_relative(packet_root),
            "case_packet_sha256_by_case": packet_hashes,
            "cases": selected_cases,
        },
        "prompt_deviation": {
            "base_prompt_path": _repo_relative(base_prompt),
            "base_prompt_sha256": sha256_file(base_prompt),
            "formal_supplement_path": "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
            "formal_supplement_sha256": formal_lock["implementation_hashes"]["draft_source_pointer_strict_v2.supplement.md"],
            "repair_supplement_path": _repo_relative(supplement),
            "repair_supplement_sha256": sha256_file(supplement),
            "effective_composed_prompt_sha256": _effective_prompt_sha256(base_prompt, supplement),
            "scope": "support-pointer location syntax and resolvability only",
        },
        "execution": {
            "candidate_output_root": _repo_relative(candidate_root),
            "backup_root": _repo_relative(backup_root),
            "pre_run_candidate_output_root_exists": False,
            "pre_run_output_root_exists": preexisting,
            "pre_run_output_entry_count": entry_count,
            "provider": EXPECTED_PROVIDER,
            "llm_call_provider": "codex_cli",
            "model": EXPECTED_MODEL,
            "reasoning_effort": EXPECTED_REASONING_EFFORT,
            "auth_mode": "codex_login",
            "codex_sandbox": EXPECTED_CODEX_SANDBOX,
            "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
            "max_parallel": EXPECTED_MAX_PARALLEL,
            "large_max_parallel": EXPECTED_MAX_PARALLEL,
            "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
            "regular_http_timeout_seconds": EXPECTED_REGULAR_HTTP_TIMEOUT_SECONDS,
            "oversized_http_timeout_seconds": EXPECTED_OVERSIZED_HTTP_TIMEOUT_SECONDS,
            "regular_codex_timeout_seconds": EXPECTED_REGULAR_CODEX_TIMEOUT_SECONDS,
            "oversized_codex_timeout_seconds": EXPECTED_OVERSIZED_CODEX_TIMEOUT_SECONDS,
            "sleep_seconds": EXPECTED_SLEEP_SECONDS,
            "quality_check": "none",
            "force": False,
            "lane_execution": "regular then oversized",
            "subprocess_environment_allowlist": list(_MINIMAL_ENV_ALLOWLIST),
            "codex_event_command_policy": _CODEX_EVENT_COMMAND_POLICY,
        },
        "runtime": {
            **codex_runtime,
            "auth_mode": "codex_login",
            "login_status_at_lock": login_status,
        },
        "implementation_hashes": {
            "run_draft_batch.py": sha256_file(resolve_repo_path("neurips_ed_track_minimal/scripts/run_draft_batch.py")),
            "draft_case_checklist.py": sha256_file(resolve_repo_path("neurips_ed_track_minimal/scripts/draft_case_checklist.py")),
            "checklist_guardrails.py": sha256_file(resolve_repo_path("neurips_ed_track_minimal/checklist_guardrails.py")),
            "checklist_validator.py": sha256_file(resolve_repo_path("neurips_ed_track_minimal/scripts/checklist_validator.py")),
            "appworld_draft_acceptance.py": sha256_file(Path(__file__).with_name("appworld_draft_acceptance.py")),
            "appworld_draft_candidate_repair.py": sha256_file(Path(__file__)),
            "repair_appworld_draft_candidates.py": sha256_file(
                Path(__file__).parent.parent / "cli" / "repair_appworld_draft_candidates.py"
            ),
        },
        "lifecycle": {
            "output_status": "candidate_generated/review_required",
            "promotion_performed": False,
            "automatic_promotion_supported": False,
            "formal_namespace_write_allowed": False,
        },
    }
    _write_json_exclusive(repair_lock_file, lock)
    return {
        "status": "locked_pre_repair",
        "repair_lock_path": _repo_relative(repair_lock_file),
        "repair_lock_sha256": sha256_file(repair_lock_file),
        "case_count": len(case_ids),
        "formal_cases_tree_sha256": formal_tree_hash,
        "candidate_output_root": _repo_relative(candidate_root),
        "promotion_performed": False,
    }


def validate_candidate_repair_lock(
    repair_lock_path: str | Path,
    *,
    require_clean_candidate_root: bool = True,
) -> CandidateRepairContext:
    """Validate every frozen input and return resolved paths for execution."""

    lock_file = _input_file(repair_lock_path, "candidate repair lock")
    _require(lock_file.name == "draft_repair_lock.json", "repair lock filename must be draft_repair_lock.json")
    lock = _load_mapping(lock_file, "candidate repair lock")
    expected_lock_fields = {
        "schema_version",
        "status",
        "locked_at",
        "draft_run_id",
        "formal_draft_run_lock_path",
        "formal_draft_run_lock_sha256",
        "cases_root",
        "formal_cases_pre_repair_tree_sha256",
        "formal_cases_pre_repair_strict_tree_sha256",
        "original_cases",
        "original_batch",
        "repair_inputs",
        "repair_reason",
        "case_ids",
        "case_ids_semantic_sha256",
        "subset_ids_path",
        "subset_ids_file_sha256",
        "formal_generation",
        "inputs",
        "prompt_deviation",
        "execution",
        "runtime",
        "implementation_hashes",
        "lifecycle",
    }
    _require(set(lock) == expected_lock_fields, "repair lock top-level field set drift")
    _require(lock.get("schema_version") == REPAIR_LOCK_SCHEMA, f"repair lock schema must be {REPAIR_LOCK_SCHEMA}")
    _require(lock.get("status") == "locked_pre_repair", "repair lock status must remain locked_pre_repair")
    _parse_timestamp(lock.get("locked_at"), "repair lock locked_at")
    _require(lock.get("case_ids") == list(EXPECTED_REPAIR_CASE_IDS), "repair lock case IDs drift")
    _require(lock.get("case_ids_semantic_sha256") == sha256_object(list(EXPECTED_REPAIR_CASE_IDS)), "repair lock case ID hash drift")

    subset_file = _input_file(_string(lock.get("subset_ids_path"), "subset_ids_path"), "repair subset IDs")
    _require(sha256_file(subset_file) == lock.get("subset_ids_file_sha256"), "repair subset IDs file hash drift")
    _require(load_repair_case_ids(subset_file) == EXPECTED_REPAIR_CASE_IDS, "repair subset IDs drift")

    formal = _mapping(lock.get("formal_generation"), "formal_generation")
    _require(
        set(formal)
        == {
            "lock_path",
            "lock_sha256",
            "cases_root",
            "cases_tree_sha256",
            "strict_tree_sha256",
            "file_count",
            "directory_count",
            "size_bytes",
            "batch_results_sha256",
            "batch_summary_sha256",
            "selected_case_canonical_hashes",
            "mutation_allowed",
        },
        "formal_generation field set drift",
    )
    formal_lock_file = _input_file(_string(formal.get("lock_path"), "formal_generation.lock_path"), "formal draft lock")
    _require(sha256_file(formal_lock_file) == formal.get("lock_sha256"), "formal draft lock hash drift")
    formal_lock = _load_mapping(formal_lock_file, "formal draft lock")
    formal_cases_root = _input_directory(_string(formal.get("cases_root"), "formal_generation.cases_root"), "formal cases root")
    _validate_lock(lock_file=formal_lock_file, lock=formal_lock, cases_root=formal_cases_root)
    _require_no_symlinks(formal_cases_root, "formal cases root")
    _require(sha256_path(formal_cases_root) == formal.get("cases_tree_sha256"), "formal cases tree hash drift before candidate generation")
    formal_inventory = _strict_tree_inventory(formal_cases_root, label="formal cases root")
    _require(formal_inventory["tree_sha256"] == formal.get("strict_tree_sha256"), "formal strict tree hash drift")
    _require(formal_inventory["file_count"] == formal.get("file_count"), "formal cases file count drift")
    _require(formal_inventory["directory_count"] == formal.get("directory_count"), "formal cases directory count drift")
    _require(formal_inventory["size_bytes"] == formal.get("size_bytes"), "formal cases size drift")
    _require(sha256_file(formal_cases_root / "_batch_results.jsonl") == formal.get("batch_results_sha256"), "formal batch results hash drift")
    _require(sha256_file(formal_cases_root / "_batch_summary.json") == formal.get("batch_summary_sha256"), "formal batch summary hash drift")
    _require(formal.get("mutation_allowed") is False, "repair lock must forbid formal generation mutation")

    _require(lock.get("draft_run_id") == formal_lock.get("draft_run_id"), "repair lock draft_run_id mismatch")
    _require(lock.get("formal_draft_run_lock_path") == _repo_relative(formal_lock_file), "repair lock formal lock pointer mismatch")
    _require(lock.get("formal_draft_run_lock_sha256") == sha256_file(formal_lock_file), "repair lock formal lock hash mismatch")
    _require(lock.get("cases_root") == _repo_relative(formal_cases_root), "repair lock formal cases root mismatch")
    _require(lock.get("formal_cases_pre_repair_tree_sha256") == formal.get("cases_tree_sha256"), "repair lock pre-repair cases tree mismatch")
    _require(
        lock.get("formal_cases_pre_repair_strict_tree_sha256") == formal.get("strict_tree_sha256"),
        "repair lock pre-repair strict tree mismatch",
    )
    original_batch = _mapping(lock.get("original_batch"), "original_batch")
    original_rows = _load_jsonl(formal_cases_root / "_batch_results.jsonl")
    expected_original_batch = {
        "batch_summary_path": _repo_relative(formal_cases_root / "_batch_summary.json"),
        "batch_summary_sha256": sha256_file(formal_cases_root / "_batch_summary.json"),
        "result_row_count": 485,
        "result_rows_sha256": sha256_object(original_rows),
    }
    _require(len(original_rows) == 485, "formal batch no longer has the locked 485-row pre-repair prefix")
    _require(dict(original_batch) == expected_original_batch, "repair lock original batch binding drift")

    inputs = _mapping(lock.get("inputs"), "inputs")
    _require(set(inputs) == {"case_packet_root", "case_packet_sha256_by_case", "cases"}, "repair inputs field set drift")
    packet_root = _input_directory(_string(inputs.get("case_packet_root"), "inputs.case_packet_root"), "case packet root")
    _require_no_symlinks(packet_root, "case packet root")
    packet_hashes = _mapping(inputs.get("case_packet_sha256_by_case"), "case packet hashes")
    locked_cases = inputs.get("cases")
    _require(isinstance(locked_cases, list) and len(locked_cases) == len(EXPECTED_REPAIR_CASE_IDS), "repair lock case records mismatch")
    cases: list[dict[str, Any]] = []
    for expected_id, raw_case in zip(EXPECTED_REPAIR_CASE_IDS, locked_cases, strict=True):
        case = _mapping(raw_case, f"repair case {expected_id}")
        _require(case.get("case_unit_id") == expected_id and case.get("task_id") == expected_id, f"repair case identity drift: {expected_id}")
        packet_path = _input_file(packet_root / expected_id / "case_packet.md", f"case packet {expected_id}")
        _require(_repo_relative(packet_path) == case.get("case_packet"), f"repair packet path drift: {expected_id}")
        _require(packet_path.stat().st_size == case.get("case_packet_size_bytes"), f"repair packet size drift: {expected_id}")
        _require(sha256_file(packet_path) == packet_hashes.get(expected_id), f"repair packet hash drift: {expected_id}")
        cases.append(dict(case))

    canonical_hashes = _mapping(formal.get("selected_case_canonical_hashes"), "selected formal hashes")
    execution = _mapping(lock.get("execution"), "execution")
    backup_root = resolve_repo_path(_string(execution.get("backup_root"), "backup root")).resolve()
    _require(not backup_root.exists(), f"repair backup root must remain absent before promotion: {backup_root}")
    raw_original_cases = lock.get("original_cases")
    _require(isinstance(raw_original_cases, list) and len(raw_original_cases) == len(EXPECTED_REPAIR_CASE_IDS), "repair original_cases inventory mismatch")
    original_by_id = {
        _string(_mapping(item, "original case").get("case_unit_id"), "original case ID"): _mapping(item, "original case")
        for item in raw_original_cases
    }
    _require(set(original_by_id) == EXPECTED_REPAIR_CASE_SET, "repair original_cases ID set mismatch")
    for case_id in EXPECTED_REPAIR_CASE_IDS:
        observed_canonical = _canonical_hashes(formal_cases_root / case_id, case_id=case_id)
        _require(observed_canonical == canonical_hashes.get(case_id), f"formal canonical draft hash drift: {case_id}")
        original = original_by_id[case_id]
        expected_original = {
            "case_unit_id": case_id,
            "canonical_file_sha256": observed_canonical,
            "attempt_tree_sha256": _attempt_tree_sha256(formal_cases_root / case_id),
            "backup_path": _repo_relative(backup_root / case_id),
        }
        _require(dict(original) == expected_original, f"repair original case lock drift: {case_id}")

    prompt = _mapping(lock.get("prompt_deviation"), "prompt_deviation")
    _require(
        set(prompt)
        == {
            "base_prompt_path",
            "base_prompt_sha256",
            "formal_supplement_path",
            "formal_supplement_sha256",
            "repair_supplement_path",
            "repair_supplement_sha256",
            "effective_composed_prompt_sha256",
            "scope",
        },
        "prompt_deviation field set drift",
    )
    supplement = _input_file(_string(prompt.get("repair_supplement_path"), "repair supplement path"), "repair prompt supplement")
    base_prompt = _input_file(_string(prompt.get("base_prompt_path"), "base prompt path"), "base draft prompt")
    _require(sha256_file(base_prompt) == prompt.get("base_prompt_sha256"), "base prompt hash drift")
    _require(sha256_file(supplement) == prompt.get("repair_supplement_sha256"), "repair supplement hash drift")
    _require(prompt.get("repair_supplement_sha256") == EXPECTED_REPAIR_SUPPLEMENT_SHA256, "unexpected repair supplement")
    _require(_effective_prompt_sha256(base_prompt, supplement) == prompt.get("effective_composed_prompt_sha256"), "effective repair prompt hash drift")
    _require(prompt.get("effective_composed_prompt_sha256") == EXPECTED_EFFECTIVE_PROMPT_SHA256, "unexpected effective repair prompt")
    _require(prompt.get("scope") == "support-pointer location syntax and resolvability only", "repair prompt scope drift")
    _validate_repair_prompt(formal_lock=formal_lock, supplement=supplement)
    repair_inputs = _mapping(lock.get("repair_inputs"), "repair_inputs")
    expected_repair_inputs = {
        "case_ids_path": _repo_relative(subset_file),
        "case_count": len(EXPECTED_REPAIR_CASE_IDS),
        "case_ids_sha256": sha256_file(subset_file),
        "case_ids_semantic_sha256": sha256_object(list(EXPECTED_REPAIR_CASE_IDS)),
        "repair_supplement_path": _repo_relative(supplement),
        "repair_supplement_sha256": sha256_file(supplement),
        "effective_composed_prompt_sha256": EXPECTED_EFFECTIVE_PROMPT_SHA256,
    }
    _require(dict(repair_inputs) == expected_repair_inputs, "repair_inputs drift from promotion-gate schema")

    _validate_execution_config(execution)
    runtime = _mapping(lock.get("runtime"), "runtime")
    current_runtime = _codex_runtime()
    expected_runtime = {
        **current_runtime,
        "auth_mode": "codex_login",
        "login_status_at_lock": runtime.get("login_status_at_lock"),
    }
    _require(dict(runtime) == expected_runtime, "repair Codex runtime drift")
    _require(
        runtime.get("login_status_at_lock") == "Logged in using ChatGPT",
        "repair lock does not prove ChatGPT-login Codex auth at freeze time",
    )
    candidate_root = resolve_repo_path(_string(execution.get("candidate_output_root"), "candidate output root")).resolve()
    _validate_output_separation(
        candidate_root=candidate_root,
        repair_lock_file=lock_file,
        formal_cases_root=formal_cases_root,
        formal_lock_file=formal_lock_file,
    )
    _require_repair_lock_location(lock_file, formal_lock_file)
    if require_clean_candidate_root:
        _require(not candidate_root.exists(), f"candidate output root must remain absent before generation: {candidate_root}")

    implementation = _mapping(lock.get("implementation_hashes"), "implementation_hashes")
    implementation_paths = {
        "run_draft_batch.py": resolve_repo_path("neurips_ed_track_minimal/scripts/run_draft_batch.py"),
        "draft_case_checklist.py": resolve_repo_path("neurips_ed_track_minimal/scripts/draft_case_checklist.py"),
        "checklist_guardrails.py": resolve_repo_path("neurips_ed_track_minimal/checklist_guardrails.py"),
        "checklist_validator.py": resolve_repo_path("neurips_ed_track_minimal/scripts/checklist_validator.py"),
        "appworld_draft_acceptance.py": Path(__file__).with_name("appworld_draft_acceptance.py"),
        "appworld_draft_candidate_repair.py": Path(__file__),
        "repair_appworld_draft_candidates.py": Path(__file__).parent.parent / "cli" / "repair_appworld_draft_candidates.py",
    }
    _require(set(implementation) == set(implementation_paths), "repair implementation hash inventory drift")
    for name, path in implementation_paths.items():
        _require(sha256_file(path) == implementation.get(name), f"repair implementation hash drift: {name}")
    # The actual generator must still be the implementation frozen in the formal lock.
    for name in ("run_draft_batch.py", "draft_case_checklist.py", "checklist_guardrails.py", "checklist_validator.py"):
        _require(implementation[name] == formal_lock["implementation_hashes"][name], f"repair generator differs from frozen formal implementation: {name}")

    lifecycle = _mapping(lock.get("lifecycle"), "lifecycle")
    _require(
        dict(lifecycle)
        == {
            "output_status": "candidate_generated/review_required",
            "promotion_performed": False,
            "automatic_promotion_supported": False,
            "formal_namespace_write_allowed": False,
        },
        "candidate lifecycle field/value drift",
    )

    return CandidateRepairContext(
        repair_lock_path=lock_file,
        repair_lock_sha256=sha256_file(lock_file),
        formal_lock_path=formal_lock_file,
        formal_cases_root=formal_cases_root,
        formal_cases_tree_sha256=_string(formal.get("cases_tree_sha256"), "formal cases tree hash"),
        formal_cases_strict_tree_sha256=_string(formal.get("strict_tree_sha256"), "formal strict tree hash"),
        formal_cases_file_count=_integer(formal.get("file_count"), "formal file count"),
        formal_cases_directory_count=_integer(formal.get("directory_count"), "formal directory count"),
        formal_cases_size_bytes=_integer(formal.get("size_bytes"), "formal size bytes"),
        case_packet_root=packet_root,
        candidate_output_root=candidate_root,
        prompt_supplement=supplement,
        cases=tuple(cases),
    )


def run_candidate_repairs(
    repair_lock_path: str | Path,
    *,
    expected_repair_lock_sha256: str | None = None,
    process_case_fn: Callable[..., dict[str, Any]] = run_draft_batch.process_case,
    codex_status_fn: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Generate and strictly validate candidates; never write formal artifacts."""

    repair_lock_anchor = _resolve_repair_lock_anchor(repair_lock_path, expected_repair_lock_sha256)
    context = validate_candidate_repair_lock(repair_lock_path, require_clean_candidate_root=True)
    _require(context.repair_lock_sha256 == repair_lock_anchor, "repair lock changed while entering candidate generation")
    case_infos = [
        run_draft_batch.CasePacketInfo(
            path=context.case_packet_root / case["case_unit_id"] / "case_packet.md",
            size_bytes=int(case["case_packet_size_bytes"]),
        )
        for case in context.cases
    ]
    regular, oversized = run_draft_batch.split_lanes(case_infos, EXPECTED_LARGE_THRESHOLD_BYTES)
    ordered_lanes = (
        ("regular", regular, EXPECTED_REGULAR_HTTP_TIMEOUT_SECONDS, EXPECTED_REGULAR_CODEX_TIMEOUT_SECONDS),
        ("oversized", oversized, EXPECTED_OVERSIZED_HTTP_TIMEOUT_SECONDS, EXPECTED_OVERSIZED_CODEX_TIMEOUT_SECONDS),
    )
    results: list[dict[str, Any]] = []

    with _minimal_subprocess_environment():
        login_status = (codex_status_fn or _codex_login_status)()
        _require(login_status == "Logged in using ChatGPT", f"Codex CLI is not in the locked ChatGPT-login state: {login_status!r}")
        context.candidate_output_root.mkdir(parents=True, exist_ok=False)
        _require(not context.candidate_output_root.is_symlink(), "candidate output root became a symlink")

        for lane, lane_cases, http_timeout, codex_timeout in ordered_lanes:
            if not lane_cases:
                continue
            with concurrent.futures.ThreadPoolExecutor(max_workers=EXPECTED_MAX_PARALLEL) as executor:
                futures = {
                    executor.submit(
                        process_case_fn,
                        case_info=case_info,
                        lane=lane,
                        output_root=context.candidate_output_root,
                        provider=EXPECTED_PROVIDER,
                        model=EXPECTED_MODEL,
                        reasoning_effort=EXPECTED_REASONING_EFFORT,
                        token_budgets=list(EXPECTED_TOKEN_BUDGETS),
                        http_timeout_seconds=http_timeout,
                        codex_timeout_seconds=codex_timeout,
                        codex_sandbox=EXPECTED_CODEX_SANDBOX,
                        prompt_supplement=context.prompt_supplement,
                        sleep_seconds=EXPECTED_SLEEP_SECONDS,
                        force=False,
                        warning_fn=lambda _: [],
                    ): case_info
                    for case_info in lane_cases
                }
                for future in concurrent.futures.as_completed(futures):
                    case_info = futures[future]
                    case_id = case_info.path.parent.name
                    try:
                        generation = future.result()
                    except Exception as exc:  # pragma: no cover - process boundary defense
                        generation = {
                            "case_unit_dir": case_id,
                            "case_packet": _repo_relative(case_info.path),
                            "case_packet_size_bytes": case_info.size_bytes,
                            "lane": lane,
                            "status": "failed",
                            "attempts": [],
                            "quality_warnings": [f"candidate_runner_exception: {type(exc).__name__}"],
                        }
                    candidate_result = _strict_candidate_result(
                        context=context,
                        generation=generation,
                        case_id=case_id,
                    )
                    results.append(candidate_result)

            _validate_formal_snapshot(context, label=f"after {lane} candidate lane")

    results.sort(key=lambda item: EXPECTED_REPAIR_CASE_IDS.index(str(item["case_unit_id"])))
    _require({str(item["case_unit_id"]) for item in results} == EXPECTED_REPAIR_CASE_SET, "candidate result set mismatch")
    formal_inventory = _validate_formal_snapshot(context, label="after candidate generation")

    result_rows = [
        {
            "schema_version": CANDIDATE_RESULTS_SCHEMA,
            "repair_lock_sha256": context.repair_lock_sha256,
            **result,
        }
        for result in results
    ]
    _validate_no_secret_payload(result_rows, label="candidate results")
    results_path = context.candidate_output_root / _RESULTS_NAME
    _write_jsonl_exclusive(results_path, result_rows)
    _validate_no_secret_material([results_path], case_id="candidate_root")
    results_ref = _artifact_reference(results_path, semantic_payload=result_rows, row_count=len(result_rows))
    candidate_inventory = _candidate_cases_inventory(context.candidate_output_root, require_metadata=False)
    validation = _build_candidate_validation(
        context=context,
        results=results,
        candidate_inventory=candidate_inventory,
        results_ref=results_ref,
        formal_inventory=formal_inventory,
    )
    _validate_no_secret_payload(validation, label="candidate validation")
    validation_path = context.candidate_output_root / _VALIDATION_NAME
    _write_json_exclusive(validation_path, validation)
    _validate_no_secret_material([validation_path], case_id="candidate_root")
    validation_ref = _artifact_reference(validation_path, semantic_payload=validation)
    summary = _build_candidate_summary(
        context=context,
        results=results,
        validation=validation,
        candidate_inventory=candidate_inventory,
        results_ref=results_ref,
        validation_ref=validation_ref,
        regular_count=len(regular),
        oversized_count=len(oversized),
        formal_inventory=formal_inventory,
    )
    _validate_no_secret_payload(summary, label="candidate summary")
    summary_path = context.candidate_output_root / _SUMMARY_NAME
    _write_json_exclusive(summary_path, summary)
    _validate_no_secret_material([results_path, validation_path, summary_path], case_id="candidate_root")
    if validation["status"] == "passed":
        _require(candidate_inventory["exact_layout"] is True, "passed candidate run lacks the exact 12-case layout")
        _validate_candidate_root_exact(context.candidate_output_root)
    _validate_formal_snapshot(context, label="after candidate metadata write")
    return summary


def validate_existing_candidates(
    repair_lock_path: str | Path,
    *,
    expected_repair_lock_sha256: str | None = None,
) -> dict[str, Any]:
    """Re-run strict candidate gates read-only after generation."""

    repair_lock_anchor = _resolve_repair_lock_anchor(repair_lock_path, expected_repair_lock_sha256)
    context = validate_candidate_repair_lock(repair_lock_path, require_clean_candidate_root=False)
    _require(context.repair_lock_sha256 == repair_lock_anchor, "repair lock changed while entering candidate revalidation")
    _validate_candidate_root_exact(context.candidate_output_root)
    metadata_paths = [context.candidate_output_root / name for name in sorted(_ROOT_METADATA_NAMES)]
    _validate_no_secret_material(metadata_paths, case_id="candidate_root")
    rows = _load_jsonl(context.candidate_output_root / _RESULTS_NAME)
    _require(len(rows) == len(EXPECTED_REPAIR_CASE_IDS), "candidate results row count mismatch")
    by_id = {str(row.get("case_unit_id")): row for row in rows}
    _require(len(by_id) == len(rows) and set(by_id) == EXPECTED_REPAIR_CASE_SET, "candidate results ID set/uniqueness mismatch")
    results: list[dict[str, Any]] = []
    for case_id in EXPECTED_REPAIR_CASE_IDS:
        stored = by_id[case_id]
        _require(stored.get("schema_version") == CANDIDATE_RESULTS_SCHEMA, f"candidate result schema mismatch: {case_id}")
        _require(stored.get("repair_lock_sha256") == context.repair_lock_sha256, f"candidate result repair-lock hash mismatch: {case_id}")
        generation = _mapping(stored.get("generation"), f"candidate generation {case_id}")
        recomputed = _strict_candidate_result(context=context, generation=dict(generation), case_id=case_id)
        expected_row = {
            "schema_version": CANDIDATE_RESULTS_SCHEMA,
            "repair_lock_sha256": context.repair_lock_sha256,
            **recomputed,
        }
        _require(dict(stored) == expected_row, f"candidate result row semantic drift: {case_id}")
        results.append(recomputed)
    formal_inventory = _validate_formal_snapshot(context, label="during candidate revalidation")
    candidate_inventory = _candidate_cases_inventory(context.candidate_output_root, require_metadata=True)
    _require(candidate_inventory["exact_layout"] is True, "candidate root layout is not exact")
    results_path = context.candidate_output_root / _RESULTS_NAME
    results_ref = _artifact_reference(results_path, semantic_payload=rows, row_count=len(rows))
    expected_validation = _build_candidate_validation(
        context=context,
        results=results,
        candidate_inventory=candidate_inventory,
        results_ref=results_ref,
        formal_inventory=formal_inventory,
    )
    stored_validation = _load_mapping(context.candidate_output_root / _VALIDATION_NAME, "candidate validation")
    _require(dict(stored_validation) == expected_validation, "candidate validation artifact drift")
    validation_ref = _artifact_reference(
        context.candidate_output_root / _VALIDATION_NAME,
        semantic_payload=expected_validation,
    )
    regular, oversized = run_draft_batch.split_lanes(
        [
            run_draft_batch.CasePacketInfo(
                path=context.case_packet_root / case["case_unit_id"] / "case_packet.md",
                size_bytes=int(case["case_packet_size_bytes"]),
            )
            for case in context.cases
        ],
        EXPECTED_LARGE_THRESHOLD_BYTES,
    )
    expected_summary = _build_candidate_summary(
        context=context,
        results=results,
        validation=expected_validation,
        candidate_inventory=candidate_inventory,
        results_ref=results_ref,
        validation_ref=validation_ref,
        regular_count=len(regular),
        oversized_count=len(oversized),
        formal_inventory=formal_inventory,
    )
    stored_summary = _load_mapping(context.candidate_output_root / _SUMMARY_NAME, "candidate summary")
    _require(dict(stored_summary) == expected_summary, "candidate summary artifact drift")
    root_inventory = _strict_tree_inventory(context.candidate_output_root, label="candidate output root")
    failed = [result for result in results if result["strict_validation_status"] != "passed"]
    return {
        "schema_version": CANDIDATE_VALIDATION_SCHEMA,
        "status": "passed" if not failed else "failed",
        "case_count": len(results),
        "passed_case_ids": [result["case_unit_id"] for result in results if result["strict_validation_status"] == "passed"],
        "failed_cases": [
            {"case_unit_id": result["case_unit_id"], "reason": result.get("strict_validation_error")}
            for result in failed
        ],
        "formal_cases_tree_unchanged": True,
        "formal_cases_strict_tree_sha256": formal_inventory["tree_sha256"],
        "candidate_cases_tree_sha256": candidate_inventory["tree_sha256"],
        "candidate_output_tree_sha256": root_inventory["tree_sha256"],
        "candidate_results_sha256": results_ref["sha256"],
        "candidate_validation_sha256": validation_ref["sha256"],
        "candidate_summary_sha256": sha256_file(context.candidate_output_root / _SUMMARY_NAME),
        "promotion_performed": False,
    }


def _build_candidate_validation(
    *,
    context: CandidateRepairContext,
    results: Sequence[Mapping[str, Any]],
    candidate_inventory: Mapping[str, Any],
    results_ref: Mapping[str, Any],
    formal_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    passed = [str(item["case_unit_id"]) for item in results if item["strict_validation_status"] == "passed"]
    failed = [
        {"case_unit_id": str(item["case_unit_id"]), "reason": str(item.get("strict_validation_error") or "unknown failure")}
        for item in results
        if item["strict_validation_status"] != "passed"
    ]
    all_passed = len(passed) == len(EXPECTED_REPAIR_CASE_IDS) and not failed and candidate_inventory.get("exact_layout") is True
    return {
        "schema_version": CANDIDATE_VALIDATION_SCHEMA,
        "status": "passed" if all_passed else "failed",
        "repair_lock_path": _repo_relative(context.repair_lock_path),
        "repair_lock_sha256": context.repair_lock_sha256,
        "case_count": len(results),
        "passed_case_ids": passed,
        "failed_cases": failed,
        "candidate_cases_inventory": dict(candidate_inventory),
        "candidate_results": dict(results_ref),
        "checks": {
            "all_generation_results_exact": all_passed,
            "all_case_artifact_inventories_exact": all_passed,
            "support_paths_in_packet_inventory": all_passed,
            "support_locations_resolve": all_passed,
            "codex_event_commands_confined": all_passed,
            "no_secret_material": all_passed,
            "candidate_root_exact_layout": candidate_inventory.get("exact_layout") is True,
            "formal_cases_tree_unchanged": True,
            "formal_cases_tree_sha256": context.formal_cases_tree_sha256,
            "formal_cases_strict_tree_sha256": formal_inventory["tree_sha256"],
            "formal_cases_file_count": formal_inventory["file_count"],
            "formal_cases_directory_count": formal_inventory["directory_count"],
            "formal_cases_size_bytes": formal_inventory["size_bytes"],
            "promotion_performed": False,
        },
    }


def _build_candidate_summary(
    *,
    context: CandidateRepairContext,
    results: Sequence[Mapping[str, Any]],
    validation: Mapping[str, Any],
    candidate_inventory: Mapping[str, Any],
    results_ref: Mapping[str, Any],
    validation_ref: Mapping[str, Any],
    regular_count: int,
    oversized_count: int,
    formal_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": CANDIDATE_SUMMARY_SCHEMA,
        "status": "candidate_generated/review_required" if validation["status"] == "passed" else "candidate_generation_failed_validation",
        "repair_lock_path": _repo_relative(context.repair_lock_path),
        "repair_lock_sha256": context.repair_lock_sha256,
        "case_count": len(results),
        "generation_success_count": sum(item["generation_status"] == "success" for item in results),
        "strict_validation_pass_count": len(validation["passed_case_ids"]),
        "strict_validation_fail_count": len(validation["failed_cases"]),
        "regular_case_count": regular_count,
        "oversized_case_count": oversized_count,
        "provider": EXPECTED_PROVIDER,
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "auth_mode": "codex_login_chatgpt",
        "codex_sandbox": EXPECTED_CODEX_SANDBOX,
        "max_parallel": EXPECTED_MAX_PARALLEL,
        "large_max_parallel": EXPECTED_MAX_PARALLEL,
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "subprocess_environment_allowlist": list(_MINIMAL_ENV_ALLOWLIST),
        "codex_event_command_policy": _CODEX_EVENT_COMMAND_POLICY,
        "prompt_supplement": _repo_relative(context.prompt_supplement),
        "prompt_supplement_sha256": sha256_file(context.prompt_supplement),
        "formal_cases_tree_before_sha256": context.formal_cases_tree_sha256,
        "formal_cases_tree_after_sha256": context.formal_cases_tree_sha256,
        "formal_cases_strict_tree_before_sha256": context.formal_cases_strict_tree_sha256,
        "formal_cases_strict_tree_after_sha256": formal_inventory["tree_sha256"],
        "formal_cases_file_count": formal_inventory["file_count"],
        "formal_cases_directory_count": formal_inventory["directory_count"],
        "formal_cases_size_bytes": formal_inventory["size_bytes"],
        "formal_cases_unchanged": True,
        "candidate_cases_inventory": dict(candidate_inventory),
        "candidate_results": dict(results_ref),
        "candidate_validation": dict(validation_ref),
        "promotion_performed": False,
        "automatic_promotion_supported": False,
        "backup_root": _repo_relative(context.candidate_output_root.parent / "backups"),
    }


def _artifact_reference(
    path: Path,
    *,
    semantic_payload: Any,
    row_count: int | None = None,
) -> dict[str, Any]:
    reference: dict[str, Any] = {
        "path": _repo_relative(path),
        "sha256": sha256_file(path),
        "semantic_sha256": sha256_object(semantic_payload),
    }
    if row_count is not None:
        reference["row_count"] = row_count
    return reference


def _candidate_cases_inventory(candidate_root: Path, *, require_metadata: bool) -> dict[str, Any]:
    _require(candidate_root.is_dir() and not candidate_root.is_symlink(), "candidate output root is missing or symlinked")
    root_entries = list(candidate_root.iterdir())
    symlinks = sorted(path.name for path in root_entries if path.is_symlink())
    _require(not symlinks, f"candidate output root contains symlinks: {symlinks}")
    actual_dirs = sorted(path.name for path in root_entries if path.is_dir())
    root_files = {path.name for path in root_entries if path.is_file()}
    metadata_files = root_files & _ROOT_METADATA_NAMES
    unexpected_root_files = sorted(root_files - _ROOT_METADATA_NAMES)
    unsupported = sorted(path.name for path in root_entries if not path.is_dir() and not path.is_file())
    if require_metadata:
        _require(metadata_files == _ROOT_METADATA_NAMES, "candidate root metadata file set mismatch")
    case_records: list[dict[str, Any]] = []
    empty_case_dirs: list[str] = []
    nested_directory_count = 0
    for case_id in actual_dirs:
        inventory = _strict_tree_inventory(candidate_root / case_id, label=f"candidate case {case_id}")
        if inventory["file_count"] == 0:
            empty_case_dirs.append(case_id)
        nested_directory_count += int(inventory["directory_count"])
        case_records.append({"case_unit_id": case_id, **inventory})
    missing = sorted(EXPECTED_REPAIR_CASE_SET - set(actual_dirs))
    extra = sorted(set(actual_dirs) - EXPECTED_REPAIR_CASE_SET)
    exact_layout = not missing and not extra and not unexpected_root_files and not unsupported and not empty_case_dirs and nested_directory_count == 0
    return {
        "expected_case_count": len(EXPECTED_REPAIR_CASE_IDS),
        "actual_case_count": len(actual_dirs),
        "expected_case_ids": list(EXPECTED_REPAIR_CASE_IDS),
        "actual_case_ids": actual_dirs,
        "missing_case_ids": missing,
        "extra_case_ids": extra,
        "unexpected_root_files": unexpected_root_files,
        "unsupported_root_entries": unsupported,
        "empty_case_directories": empty_case_dirs,
        "nested_directory_count": nested_directory_count,
        "file_count": sum(int(item["file_count"]) for item in case_records),
        "directory_count": len(actual_dirs) + nested_directory_count,
        "size_bytes": sum(int(item["size_bytes"]) for item in case_records),
        "tree_sha256": sha256_object(case_records),
        "exact_layout": exact_layout,
        "required_root_metadata": sorted(_ROOT_METADATA_NAMES),
    }


def _validate_candidate_root_exact(candidate_root: Path) -> None:
    inventory = _candidate_cases_inventory(candidate_root, require_metadata=True)
    _require(inventory["exact_layout"] is True, "candidate output root must contain exactly 12 nonempty flat case directories")
    entries = list(candidate_root.iterdir())
    dirs = {path.name for path in entries if path.is_dir() and not path.is_symlink()}
    files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    _require(dirs == EXPECTED_REPAIR_CASE_SET, "candidate root case directory set mismatch")
    _require(files == _ROOT_METADATA_NAMES, "candidate root must contain exactly three metadata files")


def _strict_tree_inventory(root: Path, *, label: str) -> dict[str, Any]:
    _require(root.is_dir() and not root.is_symlink(), f"{label} is missing or symlinked")
    entries: list[dict[str, Any]] = []
    file_count = 0
    directory_count = 0
    size_bytes = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        _require(not path.is_symlink(), f"{label} contains a symlink: {relative}")
        if path.is_dir():
            directory_count += 1
            entries.append({"path": relative, "type": "directory"})
        elif path.is_file():
            size = path.stat().st_size
            file_count += 1
            size_bytes += size
            entries.append({"path": relative, "type": "file", "size_bytes": size, "sha256": sha256_file(path)})
        else:
            raise ContractLifecycleError(f"{label} contains an unsupported entry: {relative}")
    return {
        "tree_sha256": sha256_object(entries),
        "file_count": file_count,
        "directory_count": directory_count,
        "size_bytes": size_bytes,
    }


def _validate_formal_snapshot(context: CandidateRepairContext, *, label: str) -> dict[str, Any]:
    _require(sha256_path(context.formal_cases_root) == context.formal_cases_tree_sha256, f"formal cases content hash changed {label}")
    inventory = _strict_tree_inventory(context.formal_cases_root, label="formal cases root")
    _require(inventory["tree_sha256"] == context.formal_cases_strict_tree_sha256, f"formal strict tree changed {label}")
    _require(inventory["file_count"] == context.formal_cases_file_count, f"formal file count changed {label}")
    _require(inventory["directory_count"] == context.formal_cases_directory_count, f"formal directory count changed {label}")
    _require(inventory["size_bytes"] == context.formal_cases_size_bytes, f"formal byte size changed {label}")
    return inventory


def _validate_no_secret_payload(payload: Any, *, label: str) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    _require(not any(pattern.search(text) for pattern in _SECRET_PATTERNS), f"{label} contains secret-like material")


@contextmanager
def _minimal_subprocess_environment() -> Any:
    original = dict(os.environ)
    sanitized = {name: original[name] for name in _MINIMAL_ENV_ALLOWLIST if original.get(name)}
    _require("PATH" in sanitized and "HOME" in sanitized, "minimal Codex environment lacks PATH or HOME")
    os.environ.clear()
    os.environ.update(sanitized)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


def validate_candidate_support(*, checklist_path: str | Path, packet_path: str | Path, case_id: str) -> int:
    """Apply the authoritative packet inventory and location resolver."""

    checklist = _load_mapping(_input_file(checklist_path, "candidate checklist"), "candidate checklist")
    packet = _input_file(packet_path, "candidate case packet")
    _validate_support_inventory(checklist, packet_path=packet, case_id=case_id)
    return len(_iter_support_pointers(checklist))


def _strict_candidate_result(
    *,
    context: CandidateRepairContext,
    generation: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "case_unit_id": case_id,
        "generation_status": generation.get("status"),
        "generation": dict(generation),
        "strict_validation_status": "failed",
        "promotion_performed": False,
    }
    if generation.get("status") != "success":
        result["strict_validation_error"] = "candidate generator did not return success"
        return result
    try:
        audit = _validate_candidate_case(context=context, generation=generation, case_id=case_id)
    except (ContractLifecycleError, OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        result["strict_validation_error"] = str(exc)
        return result
    result["strict_validation_status"] = "passed"
    result["strict_validation"] = audit
    return result


def _validate_candidate_case(
    *,
    context: CandidateRepairContext,
    generation: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    case_dir = _input_directory(context.candidate_output_root / case_id, f"candidate case {case_id}")
    packet_path = _input_file(context.case_packet_root / case_id / "case_packet.md", f"case packet {case_id}")
    entries = list(case_dir.iterdir())
    _require(all(path.is_file() and not path.is_symlink() for path in entries), f"candidate case contains a non-file or symlink: {case_id}")
    _validate_no_secret_material(entries, case_id=case_id)
    attempts = _validate_generation_result(
        generation=generation,
        case_id=case_id,
        case_dir=case_dir,
        packet_path=packet_path,
    )
    _validate_candidate_attempt_inventory(case_dir=case_dir, attempts=attempts, case_id=case_id)
    file_names = {path.name for path in entries}
    canonical_names = set(EXPECTED_CANONICAL_SUFFIXES)
    _require(canonical_names <= file_names, f"candidate case is missing canonical files: {sorted(canonical_names - file_names)}")

    yaml_checklist = _load_mapping(case_dir / "checklist.yaml", f"candidate YAML {case_id}")
    json_checklist = _load_mapping(case_dir / "checklist.json", f"candidate JSON {case_id}")
    _require(yaml_checklist == json_checklist, f"candidate YAML/JSON mismatch: {case_id}")
    _require(json_checklist.get("schema_version") == "case_checklist_v1", f"candidate checklist schema mismatch: {case_id}")
    _require(json_checklist.get("domain") == "appworld", f"candidate domain mismatch: {case_id}")
    _require(json_checklist.get("case_unit_id") == case_id, f"candidate case_unit_id mismatch: {case_id}")
    _require(json_checklist.get("task_id") == case_id, f"candidate task_id mismatch: {case_id}")
    schema = _load_mapping(_input_file(DEFAULT_SCHEMA_PATH, "case checklist schema"), "case checklist schema")
    errors = sorted(Draft202012Validator(schema).iter_errors(json_checklist), key=lambda error: list(error.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(value) for value in first.absolute_path) or "<root>"
        raise ContractLifecycleError(f"candidate schema failure at {location}: {first.message}")

    pointer_count = validate_candidate_support(
        checklist_path=case_dir / "checklist.json",
        packet_path=packet_path,
        case_id=case_id,
    )
    matching: list[tuple[int, Mapping[str, Any]]] = []
    for raw_attempt in attempts:
        attempt = _mapping(raw_attempt, f"candidate attempt {case_id}")
        index = attempt.get("attempt_index")
        if not isinstance(index, int) or isinstance(index, bool):
            continue
        prefix = f"attempt_{index:02d}"
        if all(
            (case_dir / f"{prefix}.{suffix}").is_file()
            and (case_dir / suffix).read_bytes() == (case_dir / f"{prefix}.{suffix}").read_bytes()
            for suffix in EXPECTED_CANONICAL_SUFFIXES
        ):
            matching.append((index, attempt))
    _require(len(matching) == 1, f"candidate canonical files must match exactly one attempt: {case_id}")
    successful_index, attempt_record = matching[0]
    _require(attempt_record.get("returncode") == 0, f"candidate promoted attempt is nonzero: {case_id}")
    _require(
        str(attempt_record.get("validator") or "").startswith("checklist valid:"),
        f"candidate promoted attempt lacks official validator provenance: {case_id}",
    )
    _require(successful_index == len(attempts), f"candidate contains attempts after promoted success: {case_id}")
    api_response = _load_mapping(case_dir / "api_response.json", f"candidate API response {case_id}")
    usage = _validate_minimal_codex_sidecars(
        case_id=case_id,
        checklist=json_checklist,
        llm_call=_load_mapping(case_dir / "llm_call.json", f"candidate llm_call {case_id}"),
        api_response=api_response,
        reasoning_summary=(case_dir / "reasoning_summary.txt").read_text(encoding="utf-8"),
        attempt_prefix=f"attempt_{successful_index:02d}",
        attempt_record=attempt_record,
    )
    command_count = _validate_codex_event_commands(api_response=api_response, case_id=case_id)
    return {
        "support_pointer_count": pointer_count,
        "support_paths_in_packet_inventory": True,
        "support_locations_resolve": True,
        "schema_valid": True,
        "yaml_json_semantically_equal": True,
        "codex_sidecars_valid": True,
        "codex_event_commands_confined": True,
        "codex_event_command_count": command_count,
        "no_secret_material": True,
        "artifact_inventory_exact": True,
        "successful_attempt_index": successful_index,
        "token_usage": usage,
        "canonical_sha256": _canonical_hashes(case_dir, case_id=case_id),
    }


def _validate_generation_result(
    *,
    generation: Mapping[str, Any],
    case_id: str,
    case_dir: Path,
    packet_path: Path,
) -> list[Mapping[str, Any]]:
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
    _require(set(generation) == expected_fields, f"candidate generation field set mismatch: {case_id}")
    _require(generation.get("case_unit_dir") == case_id, f"candidate generation identity mismatch: {case_id}")
    _require(generation.get("case_packet") == _repo_relative(packet_path), f"candidate generation packet path mismatch: {case_id}")
    _require(generation.get("case_packet_size_bytes") == packet_path.stat().st_size, f"candidate generation packet size mismatch: {case_id}")
    expected_lane = "oversized" if packet_path.stat().st_size > EXPECTED_LARGE_THRESHOLD_BYTES else "regular"
    _require(generation.get("lane") == expected_lane, f"candidate generation lane mismatch: {case_id}")
    _require(generation.get("status") == "success", f"candidate generation status mismatch: {case_id}")
    _require(generation.get("quality_warnings") == [], f"candidate generation contains quality warnings: {case_id}")
    _require(generation.get("checklist_path") == _repo_relative(case_dir / "checklist.yaml"), f"candidate checklist path mismatch: {case_id}")
    raw_attempts = generation.get("attempts")
    _require(isinstance(raw_attempts, list) and 1 <= len(raw_attempts) <= len(EXPECTED_TOKEN_BUDGETS), f"candidate attempt count mismatch: {case_id}")
    attempts: list[Mapping[str, Any]] = []
    expected_http_timeout = EXPECTED_OVERSIZED_HTTP_TIMEOUT_SECONDS if expected_lane == "oversized" else EXPECTED_REGULAR_HTTP_TIMEOUT_SECONDS
    expected_codex_timeout = EXPECTED_OVERSIZED_CODEX_TIMEOUT_SECONDS if expected_lane == "oversized" else EXPECTED_REGULAR_CODEX_TIMEOUT_SECONDS
    base_fields = {
        "attempt_index",
        "max_output_tokens",
        "http_timeout_seconds",
        "codex_timeout_seconds",
        "returncode",
        "duration_seconds",
        "stderr_tail",
    }
    for expected_index, raw_attempt in enumerate(raw_attempts, start=1):
        attempt = _mapping(raw_attempt, f"candidate attempt {case_id}/{expected_index}")
        _require(frozenset(attempt) in {frozenset(base_fields), frozenset(base_fields | {"validator"})}, f"candidate attempt field set mismatch: {case_id}/{expected_index}")
        _require(attempt.get("attempt_index") == expected_index, f"candidate attempt index mismatch: {case_id}/{expected_index}")
        _require(attempt.get("max_output_tokens") == EXPECTED_TOKEN_BUDGETS[expected_index - 1], f"candidate token-budget label mismatch: {case_id}/{expected_index}")
        _require(attempt.get("http_timeout_seconds") == expected_http_timeout, f"candidate HTTP timeout mismatch: {case_id}/{expected_index}")
        _require(attempt.get("codex_timeout_seconds") == expected_codex_timeout, f"candidate Codex timeout mismatch: {case_id}/{expected_index}")
        _require(isinstance(attempt.get("returncode"), int) and not isinstance(attempt.get("returncode"), bool), f"candidate returncode is invalid: {case_id}/{expected_index}")
        duration = attempt.get("duration_seconds")
        _require(isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration >= 0, f"candidate duration is invalid: {case_id}/{expected_index}")
        _require(isinstance(attempt.get("stderr_tail"), str), f"candidate stderr_tail is invalid: {case_id}/{expected_index}")
        if "validator" in attempt:
            _require(isinstance(attempt.get("validator"), str) and bool(attempt.get("validator")), f"candidate validator provenance is invalid: {case_id}/{expected_index}")
        attempts.append(attempt)
    for attempt in attempts[:-1]:
        _require(
            attempt.get("returncode") != 0 or not str(attempt.get("validator") or "").startswith("checklist valid:"),
            f"candidate runner did not promote the first valid attempt: {case_id}",
        )
    return attempts


def _validate_candidate_attempt_inventory(
    *,
    case_dir: Path,
    attempts: Sequence[Mapping[str, Any]],
    case_id: str,
) -> None:
    canonical = set(EXPECTED_CANONICAL_SUFFIXES)
    actual = {path.name for path in case_dir.iterdir()}
    attempt_groups: dict[int, set[str]] = {}
    pattern = re.compile(r"^attempt_([0-9]{2})\.(.+)$")
    for name in actual - canonical:
        match = pattern.fullmatch(name)
        _require(match is not None, f"candidate case contains an unsupported file: {case_id}/{name}")
        attempt_groups.setdefault(int(match.group(1)), set()).add(match.group(2))
    _require(sorted(attempt_groups) == list(range(1, len(attempts) + 1)), f"candidate attempt artifact indices mismatch: {case_id}")
    allowed_stage_sets = [
        _ATTEMPT_LOG_SUFFIXES | frozenset(_ATTEMPT_STAGE_SUFFIXES[:stage_count])
        for stage_count in range(len(_ATTEMPT_STAGE_SUFFIXES) + 1)
    ]
    for index, suffixes in attempt_groups.items():
        _require(frozenset(suffixes) in allowed_stage_sets, f"candidate attempt artifact stage is invalid: {case_id}/{index}")
    _require(attempt_groups[len(attempts)] == canonical, f"candidate promoted attempt is incomplete: {case_id}")


def _validate_codex_event_commands(*, api_response: Mapping[str, Any], case_id: str) -> int:
    codex = _mapping(api_response.get("codex_cli"), f"candidate codex_cli {case_id}")
    command = codex.get("command")
    _require(isinstance(command, list) and "--cd" in command, f"candidate Codex command lacks workspace: {case_id}")
    workspace = Path(str(command[command.index("--cd") + 1]))
    _require(workspace.is_absolute() and workspace.name.startswith("case-checklist-codex-"), f"candidate Codex workspace is not an isolated temp directory: {case_id}")
    workspace_text = os.path.normpath(str(workspace))
    events = codex.get("events")
    _require(isinstance(events, list), f"candidate Codex events are invalid: {case_id}")
    command_count = 0
    for event in events:
        item = event.get("item") if isinstance(event, Mapping) else None
        if not isinstance(item, Mapping) or item.get("type") != "command_execution":
            continue
        command_count += 1
        raw = item.get("command")
        _require(isinstance(raw, str) and raw, f"candidate command event is malformed: {case_id}")
        try:
            outer = shlex.split(raw)
        except ValueError as exc:
            raise ContractLifecycleError(f"candidate command event is not shell-parseable: {case_id}") from exc
        _require(len(outer) == 3 and outer[0] in {"/bin/zsh", "/bin/bash", "zsh", "bash"} and outer[1] == "-lc", f"candidate command wrapper is not allowed: {case_id}")
        payload = outer[2]
        _require("$HOME" not in payload and "${HOME}" not in payload, f"candidate command reads HOME: {case_id}")
        try:
            tokens = shlex.split(payload)
        except ValueError as exc:
            raise ContractLifecycleError(f"candidate command payload is not shell-parseable: {case_id}") from exc
        _require(not any(Path(token).name in {"env", "printenv"} for token in tokens), f"candidate command enumerates the process environment: {case_id}")
        for token in tokens:
            cleaned = token.lstrip("<>|;&(")
            _require(re.search(r"(^|/)\.\.($|/)", cleaned) is None, f"candidate command uses parent traversal: {case_id}")
            _require(not cleaned.startswith("~"), f"candidate command uses a home expansion: {case_id}")
            if cleaned.startswith("/"):
                normalized = os.path.normpath(cleaned)
                _require(
                    normalized == workspace_text or normalized.startswith(workspace_text + os.sep),
                    f"candidate command reads outside the isolated workspace: {case_id}",
                )
            if "/" in cleaned:
                components = {part.lower() for part in cleaned.split("/") if part}
                _require(not ({"workspace", "results"} & components), f"candidate command references a forbidden workspace/results path: {case_id}")
    return command_count


def _validate_repair_prompt(*, formal_lock: Mapping[str, Any], supplement: Path) -> None:
    _require(sha256_file(supplement) == EXPECTED_REPAIR_SUPPLEMENT_SHA256, "repair supplement hash does not match the approved combined prompt")
    base_prompt = _input_file(
        "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md",
        "base draft prompt",
    )
    _require(_effective_prompt_sha256(base_prompt, supplement) == EXPECTED_EFFECTIVE_PROMPT_SHA256, "repair composed prompt hash mismatch")
    _require(
        sha256_file(base_prompt) == formal_lock["implementation_hashes"]["draft_case_checklist.prompt.md"],
        "base draft prompt differs from the formal generation lock",
    )


def _validate_execution_config(execution: Mapping[str, Any]) -> None:
    expected = {
        "provider": EXPECTED_PROVIDER,
        "llm_call_provider": "codex_cli",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "auth_mode": "codex_login",
        "codex_sandbox": EXPECTED_CODEX_SANDBOX,
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "max_parallel": EXPECTED_MAX_PARALLEL,
        "large_max_parallel": EXPECTED_MAX_PARALLEL,
        "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
        "regular_http_timeout_seconds": EXPECTED_REGULAR_HTTP_TIMEOUT_SECONDS,
        "oversized_http_timeout_seconds": EXPECTED_OVERSIZED_HTTP_TIMEOUT_SECONDS,
        "regular_codex_timeout_seconds": EXPECTED_REGULAR_CODEX_TIMEOUT_SECONDS,
        "oversized_codex_timeout_seconds": EXPECTED_OVERSIZED_CODEX_TIMEOUT_SECONDS,
        "sleep_seconds": EXPECTED_SLEEP_SECONDS,
        "quality_check": "none",
        "force": False,
        "lane_execution": "regular then oversized",
        "subprocess_environment_allowlist": list(_MINIMAL_ENV_ALLOWLIST),
        "codex_event_command_policy": _CODEX_EVENT_COMMAND_POLICY,
    }
    for key, value in expected.items():
        _require(execution.get(key) == value, f"repair execution config drift: {key}")
    _require(
        set(execution)
        == set(expected)
        | {
            "candidate_output_root",
            "backup_root",
            "pre_run_candidate_output_root_exists",
            "pre_run_output_root_exists",
            "pre_run_output_entry_count",
        },
        "repair execution field set drift",
    )
    _require(_string(execution.get("candidate_output_root"), "candidate output root"), "candidate output root missing")
    _require(execution.get("pre_run_output_entry_count") == 0, "candidate output was not empty when locked")
    _require(isinstance(execution.get("pre_run_output_root_exists"), bool), "candidate pre-run existence flag is invalid")
    _require(execution.get("pre_run_candidate_output_root_exists") is False, "candidate output must have been absent when locked")


def _validate_output_separation(
    *,
    candidate_root: Path,
    repair_lock_file: Path,
    formal_cases_root: Path,
    formal_lock_file: Path,
) -> None:
    candidate_root = candidate_root.resolve()
    formal_cases_root = formal_cases_root.resolve()
    repair_lock_file = repair_lock_file.resolve()
    formal_lock_file = formal_lock_file.resolve()
    _require(candidate_root != formal_cases_root, "candidate output root cannot equal the formal cases root")
    _require(not _is_relative_to(candidate_root, formal_cases_root), "candidate output root cannot be inside the formal cases root")
    _require(not _is_relative_to(formal_cases_root, candidate_root), "candidate output root cannot contain the formal cases root")
    _require(repair_lock_file != formal_lock_file, "repair lock cannot overwrite the formal lock")
    _require(not _is_relative_to(repair_lock_file, candidate_root), "repair lock must be outside the clean candidate output root")
    _require(not _is_relative_to(repair_lock_file, formal_cases_root), "repair lock cannot be written inside formal cases")
    formal_provenance_root = formal_lock_file.parent
    _require(not _is_relative_to(candidate_root, formal_provenance_root), "candidate output root cannot be inside formal provenance")


def _require_repair_lock_location(repair_lock_file: Path, formal_lock_file: Path) -> None:
    expected = formal_lock_file.resolve().parent / "draft_repair_lock.json"
    _require(
        repair_lock_file.resolve() == expected,
        f"repair lock must be the separate formal provenance lock: {expected}",
    )


def _canonical_hashes(case_dir: Path, *, case_id: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for suffix in EXPECTED_CANONICAL_SUFFIXES:
        path = _input_file(case_dir / suffix, f"{case_id} canonical {suffix}")
        _require(not path.is_symlink(), f"canonical artifact is a symlink: {case_id}/{suffix}")
        hashes[suffix] = sha256_file(path)
    return hashes


def _effective_prompt_sha256(base_prompt: Path, supplement: Path) -> str:
    composed = minimal_drafter.compose_prompt(
        base_prompt.read_text(encoding="utf-8"),
        supplement.read_text(encoding="utf-8"),
    )
    return sha256_bytes(composed.encode("utf-8"))


def _codex_login_status() -> str:
    executable = shutil.which("codex")
    _require(executable is not None, "Codex CLI is not on PATH")
    proc = subprocess.run(
        [executable, "login", "status"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip()).strip()
    _require(proc.returncode == 0, f"Codex login status failed: {output}")
    return output


def _codex_runtime() -> dict[str, str]:
    executable = shutil.which("codex")
    _require(executable is not None, "Codex CLI is not on PATH")
    executable_path = Path(executable).resolve()
    proc = subprocess.run(
        [str(executable_path), "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip()).strip()
    _require(proc.returncode == 0 and output, f"Codex version check failed: {output}")
    match = output.rsplit(" ", 1)[-1]
    _require(re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", match) is not None, f"unexpected Codex version output: {output}")
    return {
        "codex_executable": str(executable_path),
        "codex_cli_version": match,
        "codex_executable_sha256": sha256_file(executable_path),
    }


def _require_no_symlinks(root: Path, label: str) -> None:
    _require(not root.is_symlink(), f"{label} is a symlink: {root}")
    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    _require(not symlinks, f"{label} contains symlinks: {[str(path) for path in symlinks[:5]]}")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    source = _input_file(path, "candidate results")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(f"candidate results JSONL line {line_number} is malformed: {exc}") from exc
        _require(isinstance(value, dict), f"candidate results JSONL line {line_number} is not an object")
        rows.append(value)
    return rows


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    _require(not path.exists(), f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp_name, path)
        except FileExistsError as exc:
            raise ContractLifecycleError(f"refusing to overwrite concurrently-created artifact: {path}") from exc
        os.unlink(temp_name)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _write_jsonl_exclusive(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    _require(not path.exists(), f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp_name, path)
        except FileExistsError as exc:
            raise ContractLifecycleError(f"refusing to overwrite concurrently-created artifact: {path}") from exc
        os.unlink(temp_name)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _input_file(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path).resolve()
    _require(resolved.is_file() and not resolved.is_symlink(), f"{label} is missing, not regular, or symlinked: {resolved}")
    return resolved


def _input_directory(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path).resolve()
    _require(resolved.is_dir() and not resolved.is_symlink(), f"{label} is missing, not a directory, or symlinked: {resolved}")
    return resolved


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be a mapping")
    return value


def _string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label} must be a nonempty string")
    return value


def _integer(value: Any, label: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{label} must be a nonnegative integer")
    return int(value)


def _resolve_repair_lock_anchor(
    repair_lock_path: str | Path,
    expected_repair_lock_sha256: str | None,
) -> str:
    """Bind the call to the bytes at the caller-selected, fixed repair-lock path."""

    lock_file = _input_file(repair_lock_path, "candidate repair lock")
    actual_sha256 = sha256_file(lock_file)
    if expected_repair_lock_sha256 is not None:
        _require_sha256(expected_repair_lock_sha256, "expected repair lock SHA-256")
        _require(
            actual_sha256 == expected_repair_lock_sha256,
            "repair lock differs from the caller-anchored pre-lock hash",
        )
    return actual_sha256


def _require_sha256(value: Any, label: str) -> str:
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None, f"{label} is invalid")
    return str(value)


def _parse_timestamp(value: Any, label: str) -> datetime:
    _require(isinstance(value, str) and value, f"{label} must be a timestamp")
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractLifecycleError(f"{label} is invalid") from exc
    _require(parsed.tzinfo is not None, f"{label} must include a timezone")
    return parsed


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractLifecycleError(message)
