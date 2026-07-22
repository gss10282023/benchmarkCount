"""Canonical fail-closed acceptance for the AppWorld GPT-5.6 Sol draft run.

This is intentionally independent of the historical GPT-5.4 acceptance and
repair overlay.  The formal run is immutable, corrections are forbidden, and
the publication candidate is an atomic, byte-identical materialization of the
485 formal case directories after every formal gate passes.
"""

from __future__ import annotations

import importlib.metadata
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
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
from evidence_system.contracts.appworld_checklist_semantics import (
    SEMANTIC_REPORT_SCHEMA as APPWORLD_SEMANTIC_REPORT_SCHEMA,
    appworld_packet_registered_test_registry,
    validate_appworld_packet_checklist_semantics,
    validate_appworld_packet_evaluator_semantics,
)
from evidence_system.contracts.appworld_stronger_gaps import (
    parse_packet_stronger_gap_registry,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object, sha256_path
from evidence_system.contracts.appworld_support_pointers import support_location_resolves
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from neurips_ed_track_minimal.checklist_guardrails import (
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts import draft_case_checklist as minimal_drafter


MATERIALIZATION_ROOT = Path(
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
)
DEFAULT_DRAFT_ROOT = MATERIALIZATION_ROOT / (
    "draft_runs/codex-gpt-5.6-sol-xhigh-support-v3"
)
DEFAULT_LOCK_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_run_lock.json"
DEFAULT_CASES_ROOT = DEFAULT_DRAFT_ROOT / "cases"
DEFAULT_ACCEPTED_CASES_ROOT = DEFAULT_DRAFT_ROOT / "accepted_cases"
DEFAULT_CORRECTIONS_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_corrections.json"
DEFAULT_HASH_INDEX_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_hash_index.json"
DEFAULT_ACCEPTANCE_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_acceptance_report.json"
DEFAULT_FINAL_LOCK_PATH = DEFAULT_DRAFT_ROOT / "provenance/draft_run_final_lock.json"
DEFAULT_CANARY_ACCEPTANCE_PATH = DEFAULT_DRAFT_ROOT / "provenance/canary_acceptance.json"
DEFAULT_PREFLIGHT_ROOT = MATERIALIZATION_ROOT / (
    "draft_preflights/codex-gpt-5.6-sol-xhigh-support-v3-consecutive"
)

LOCK_SCHEMA = "appworld_draft_run_lock.v5"
CANARY_ACCEPTANCE_SCHEMA = "appworld_draft_canary_acceptance.v1"
PHASE_START_SCHEMA = "appworld_draft_phase_start.v1"
PHASE_TERMINAL_SCHEMA = "appworld_draft_phase_terminal.v1"
CORRECTIONS_SCHEMA = "appworld_draft_corrections_zero.v1"
HASH_INDEX_SCHEMA = "appworld_draft_hash_index_v56.v1"
ACCEPTANCE_SCHEMA = "appworld_draft_acceptance_v56.v1"
FINAL_LOCK_SCHEMA = "appworld_draft_run_final_lock_v56.v1"
EXPECTED_EXPERIMENT_ID = "appworld_full_test_extension_v1"
EXPECTED_DRAFT_RUN_ID = "appworld-extension-485-codex-gpt-5.6-sol-xhigh-support-v3"
EXPECTED_MODEL = "gpt-5.6-sol"
EXPECTED_REASONING_EFFORT = "xhigh"
EXPECTED_MODEL_VERBOSITY = "low"
EXPECTED_CODEX_SANDBOX = "danger-full-access"
EXPECTED_TOKEN_BUDGETS = (12000, 16000, 20000)
EXPECTED_LANE_COUNTS = {"regular": 414, "oversized": 71}
EXPECTED_MAX_PARALLEL = 8
EXPECTED_LARGE_THRESHOLD_BYTES = 100_000
EXPECTED_REGISTERED_TEST_COUNT = 3_817
ENVIRONMENT_POLICY = "env_i_explicit_allowlist_v1"
EVENT_COMMAND_POLICY = "direct_stdin_sealed_bundle_v1"
RUNTIME_GATE_SCHEMA = "appworld_v56_attempt_runtime_gate.v5"
INFRA_RETRY_SCHEMA = "appworld_v56_infra_retry_classification.v1"
QUARANTINE_SCHEMA = "appworld_v56_attempt_quarantine.v1"
QUARANTINE_REF_SCHEMA = "appworld_v56_attempt_quarantine_ref.v1"
LIFECYCLE = "draft_generated/review_required"
EXPECTED_PREFLIGHT_ROUNDS = ("round_01", "round_02", "round_03")
EXPECTED_PREFLIGHT_CASE_IDS = (
    "6b6ca61_1",  # test_normal, regular, reviewed gap, max native tests
    "dac78d9_3",  # test_normal, regular, reviewed no-gap
    "986aa4e_1",  # test_normal, oversized, reviewed gap, two conditions
    "d18139b_3",  # test_normal, oversized, reviewed no-gap, largest packet
    "988af8e_2",  # test_challenge, regular, reviewed gap, max native tests
    "476b213_2",  # test_challenge, regular, reviewed no-gap
    "953b296_2",  # test_challenge, oversized, reviewed gap, largest challenge packet
    "d8e490b_3",  # test_challenge, oversized, reviewed no-gap
)
EXPECTED_PREFLIGHT_CASE_COUNT_BY_DATASET = {"test_normal": 4, "test_challenge": 4}
EXPECTED_PREFLIGHT_LANE_COUNTS = {"regular": 4, "oversized": 4}
FAILED_V2_DRAFT_ROOT = Path(
    "experiments/appworld_full_test_extension_v1/draft_runs/"
    "codex-gpt-5.6-sol-xhigh-support-v2"
)
FAILED_V2_DIAGNOSTIC_PATH = Path(
    "experiments/appworld_full_test_extension_v1/provenance/"
    "failed_draft_run_codex-gpt-5.6-sol-xhigh-support-v2.json"
)
EXPECTED_FAILED_V2_TREE_SHA256 = "1a00c231542ccd0f4623b041e5e19325558a37153042cde47ade9e31be882da8"
EXPECTED_FAILED_V2_DIAGNOSTIC_SHA256 = "ed07906dce731645226b32d948a852a56c09e0f9a0ef23577c1738dd10f06362"
FAILED_V3_CANARY_ROOT = Path(
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v2"
)
FAILED_V3_CANARY_DIAGNOSTIC_PATH = Path(
    "experiments/appworld_full_test_extension_v1/provenance/"
    "failed_gpt56_strict_v3_lockfix_v2_canary.json"
)
EXPECTED_FAILED_V3_CANARY_TREE_SHA256 = (
    "7ff53b7fb95253c8a15a864ad725a1be8d8e82a2c15b0c6855819ef44c049f4c"
)
EXPECTED_FAILED_V3_CANARY_DIAGNOSTIC_SHA256 = (
    "82c5c46f404b48b46e53d525dc5bf3b9d372b9576b45e13b12da1dcdbe8e024c"
)
FAILED_V3_GUARDRAIL_ROOT = Path(
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v3"
)
FAILED_V3_GUARDRAIL_DIAGNOSTIC_PATH = Path(
    "experiments/appworld_full_test_extension_v1/provenance/"
    "failed_gpt56_strict_v3_lockfix_v3_canary.json"
)
FAILED_V4_FORMAL_ROOT = Path(
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v4"
)
FAILED_V4_FORMAL_DIAGNOSTIC_PATH = Path(
    "experiments/appworld_full_test_extension_v1/provenance/"
    "failed_gpt56_strict_v3_lockfix_v4_formal.json"
)
EXPECTED_FAILED_V4_FORMAL_TREE_SHA256 = (
    "508bf65c8e50b67b5a902f1985f119711c56c1f60186f1c114300b2660689a77"
)
EXPECTED_FAILED_V4_FORMAL_DIAGNOSTIC_SHA256 = (
    "9dea7dbc6d8b0dfc879b65123c59d1ffdc3d47408168bd2c577d96fabed1a814"
)
EXPECTED_FAILED_V4_FORMAL_RESPONSE_IDS_SHA256 = (
    "af31b7a02cef9778df16bcb722a1fd1fc98764d83f61929f7a6c773e3b3b7ca6"
)
FAILED_V5_CANARY_ROOT = Path(
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v5"
)
FAILED_V5_CANARY_DIAGNOSTIC_PATH = Path(
    "experiments/appworld_full_test_extension_v1/provenance/"
    "failed_gpt56_strict_v3_lockfix_v5_canary.json"
)
EXPECTED_FAILED_V5_CANARY_TREE_SHA256 = (
    "0de0e2b35963e5ab7a1a4ed779fc876bac3f2a212b719669bc67fc016f5b10bc"
)
EXPECTED_FAILED_V5_CANARY_DIAGNOSTIC_SHA256 = (
    "28fc556d2aaab182f22ff750da97148b2d8de91bf58ff99eb809d6ec7226befa"
)
EXPECTED_FAILED_V5_CANARY_RESPONSE_IDS_SHA256 = (
    "0ae5a826959f40c6d5c4fd933053979b9b8497b23648c6627a829ebb03f8eb6f"
)
EXPECTED_FAILED_V3_GUARDRAIL_TREE_SHA256 = (
    "203826cdee3bef277082d3f9729b12b3c4ed7c796ba22c619843eb68cc1dfc4d"
)
EXPECTED_FAILED_V3_GUARDRAIL_DIAGNOSTIC_SHA256 = (
    "9a691df69289846dd32233e83d263e68556d4153ec0dd4b0f2abcd64a2a8a859"
)
# Historical-only inputs retained so the legacy diagnostic verifier remains
# readable.  The v4 lock builder and every v3 canary/formal gate ignore them.
DEFAULT_PREFLIGHT_ORIGINAL_ROOT = Path(
    "experiments/appworld_full_test_extension_v1/draft_preflights/"
    "codex-gpt-5.6-sol-xhigh-support-v2-relocated-stale-20260716"
)
DEFAULT_PREFLIGHT_RESOLUTION_PATH = Path(
    "experiments/appworld_full_test_extension_v1/draft_preflights/"
    "codex-gpt-5.6-sol-xhigh-support-v2.resolution.json"
)
DEFAULT_PREFLIGHT_FRESH_CHALLENGE_ROOT = Path(
    "experiments/appworld_full_test_extension_v1/draft_preflights/"
    "codex-gpt-5.6-sol-xhigh-support-v2-fresh-challenge-source-20260716"
)
EXPECTED_PREFLIGHT_ORIGINAL_TREE_SHA256 = "4cb211abf4b051ea97f175fcf207d465cd2c11762b489f98cbefcc732eae9218"
EXPECTED_PREFLIGHT_TREE_SHA256 = "00f5cb2825de4e301ade31b9b71ebd759d07aa7c47d5e15ed63f49ef1ec98ff5"
EXPECTED_PREFLIGHT_RESOLUTION_SHA256 = "bc2f9a2deff929dffc1b5d544eae68dbd0017c7420431ee5b3401c4f0e168e57"
EXPECTED_PREFLIGHT_FRESH_CHALLENGE_TREE_SHA256 = "7879810cf8e4cef197341db65ad59b1ef7facbad102e0282bc50d07dcf269147"
EXPECTED_FROZEN_SCOPE_SHA256 = "bc95435346c320dcc1da16661adb125302b09d1ffb6e21b0474e37f7a0d619c8"
EXPECTED_EXTENSION_MANIFEST_SHA256 = "4c1f74b933907824ced0f30e695adb3dc16436a121d8bf663c068f16ef4fb5ad"
EXPECTED_PACKET_ACCEPTANCE_SHA256 = "ec56244d77a8c517b91de49e9e7e549ddbfe217322959989068f3cca11c1bdc5"
EXPECTED_ATTACHMENT_PROMPT_SHA256 = "83ea70f0518686f49b0b88cfa51aae2f1df3ff1d77e2b82851b2cdc8ffda42a6"
_ATTACHMENT_PROMPT_PATH = Path(
    "/Users/gss/.codex/attachments/4c5a5b1c-131d-45c6-80c1-2afc5587c559/pasted-text.txt"
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
_ATTEMPT_STAGE_SUFFIXES = (
    "api_response.json",
    "reasoning_summary.txt",
    "llm_call.json",
    "checklist.yaml",
    "checklist.json",
)
_ATTEMPT_LOG_SUFFIXES = frozenset({"stderr.log", "stdout.log"})
_ROOT_BATCH_FILES = frozenset({"_batch_results.jsonl", "_batch_summary.json"})
_ATTEMPT_RE = re.compile(
    r"^attempt_(?P<index>[0-9]{2})\.(?P<suffix>"
    + "|".join(re.escape(value) for value in CANONICAL_SUFFIXES)
    + r")$"
)


def appworld_v56_runtime_gate_rejection(
    *, status: str, reason: str, error: BaseException | None = None
) -> dict[str, str]:
    """Return the only accepted fail/not-run runtime-gate record shape."""

    _require(status in {"failed", "not_run"}, "runtime gate rejection status must be failed/not_run")
    _require(isinstance(reason, str) and reason.strip(), "runtime gate rejection reason must be nonempty")
    payload = {
        "schema_version": RUNTIME_GATE_SCHEMA,
        "status": status,
        "policy": EVENT_COMMAND_POLICY,
        "reason": reason,
    }
    if status == "failed":
        _require(error is not None, "failed runtime gate record requires an exception audit")
        payload.update(
            {
                "error_type": type(error).__name__,
                "error_message_sha256": sha256_bytes(str(error).encode("utf-8")),
            }
        )
    else:
        _require(error is None, "not-run runtime gate record cannot contain an exception audit")
    return payload

_INPUT_PATHS = {
    "manifest": MATERIALIZATION_ROOT / "experiment_manifest.json",
    "source_bundle": MATERIALIZATION_ROOT
    / "source_bundles/case_packet_source_bundle.json",
    "packet_acceptance_report": MATERIALIZATION_ROOT
    / "provenance/acceptance_report.json",
    "frozen_scope": MATERIALIZATION_ROOT / "frozen_scope.json",
    "source_catalog": MATERIALIZATION_ROOT
    / "official_splits/appworld_selected_task_sources.json",
    "all_extension_ids": MATERIALIZATION_ROOT
    / "official_splits/appworld_extension_all.txt",
    "normal_extension_ids": MATERIALIZATION_ROOT
    / "official_splits/appworld_test_normal_extension.txt",
    "challenge_ids": MATERIALIZATION_ROOT
    / "official_splits/appworld_test_challenge.txt",
    "definition_refreeze": MATERIALIZATION_ROOT
    / "provenance/definition_refreeze_gpt56_strict_v3.json",
    "stronger_gap_registry": Path(
        "experiments/appworld_full_test_extension_v1/official_splits/"
        "appworld_stronger_gap_registry.gpt56.v2.json"
    ),
    "stronger_gap_review_policy": Path(
        "experiments/appworld_full_test_extension_v1/official_splits/"
        "appworld_stronger_gap_review_policy.gpt56.v1.json"
    ),
    "stronger_gap_review_receipt": Path(
        "experiments/appworld_full_test_extension_v1/official_splits/"
        "appworld_stronger_gap_review_receipt.gpt56.v1.json"
    ),
}
_PACKET_ROOT = MATERIALIZATION_ROOT / "case_packets/appworld"
_IMPLEMENTATION_PATHS = {
    "run_draft_batch.py": Path("neurips_ed_track_minimal/scripts/run_draft_batch.py"),
    "draft_case_checklist.py": Path("neurips_ed_track_minimal/scripts/draft_case_checklist.py"),
    "draft_case_checklist.prompt.md": Path(
        "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md"
    ),
    "appworld_gpt56_draft_strict_v3.supplement.md": Path(
        "neurips_ed_track_minimal/prompts/appworld_gpt56_draft_strict_v3.supplement.md"
    ),
    "case_checklist.schema.json": Path(
        "neurips_ed_track_minimal/schemas/case_checklist.schema.json"
    ),
    "case_checklist.template.yaml": Path(
        "neurips_ed_track_minimal/templates/case_checklist.template.yaml"
    ),
    "checklist_guardrails.py": Path("neurips_ed_track_minimal/checklist_guardrails.py"),
    "checklist_validator.py": Path(
        "neurips_ed_track_minimal/scripts/checklist_validator.py"
    ),
    "appworld_draft_acceptance_v56.py": Path(
        "src/evidence_system/contracts/appworld_draft_acceptance_v56.py"
    ),
    "appworld_checklist_semantics.py": Path(
        "src/evidence_system/contracts/appworld_checklist_semantics.py"
    ),
    "appworld_stronger_gaps.py": Path(
        "src/evidence_system/contracts/appworld_stronger_gaps.py"
    ),
    "appworld_support_pointers.py": Path(
        "src/evidence_system/contracts/appworld_support_pointers.py"
    ),
    "build_appworld_stronger_gap_registry.py": Path(
        "src/evidence_system/cli/build_appworld_stronger_gap_registry.py"
    ),
    "validate_appworld_drafts_v56.py": Path(
        "src/evidence_system/cli/validate_appworld_drafts_v56.py"
    ),
    "appworld_extension.py": Path(
        "src/evidence_system/contracts/appworld_extension.py"
    ),
    "case_packets.py": Path("src/evidence_system/contracts/case_packets.py"),
    "schemas.py": Path("src/evidence_system/core/schemas.py"),
    "common.py": Path("src/evidence_system/contracts/common.py"),
    "hashing.py": Path("src/evidence_system/core/hashing.py"),
    "paths.py": Path("src/evidence_system/core/paths.py"),
    "errors.py": Path("src/evidence_system/core/errors.py"),
    "cli_common.py": Path("src/evidence_system/cli/_common.py"),
}
_ENV_ALLOWLIST = (
    "HOME",
    "CODEX_HOME",
    "PATH",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONPATH",
)
_APPROVED_ENV_VALUES = {
    "HOME": "/private/tmp/appworld_codex_draft_home_56",
    "CODEX_HOME": "/Users/gss/.codex",
    "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
    "TMPDIR": "/private/tmp",
    "LANG": "en_US.UTF-8",
    "LC_ALL": "en_US.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": ".",
}
_SHELL_TOOL_NAMES = ("wc", "sed", "rg", "awk")
_CODEX_PATH_WARNING_RE = re.compile(
    r"^WARNING: proceeding, even though we could not create PATH aliases: "
    r"Operation not permitted \(os error 1\)$"
)
_INFRA_RETRY_PATTERNS = (
    (
        "provider_rate_limit",
        re.compile(
            r"(?i)(?:\brate[ -]?limit(?:ed|ing)?\b|\btoo many requests\b|"
            r"\bHTTP\s*429\b|\bplease try again in\s+[0-9]+(?:\.[0-9]+)?s\b)"
        ),
    ),
    (
        "provider_service_unavailable",
        re.compile(
            r"(?i)(?:\bservice unavailable\b|\btemporarily unavailable\b|"
            r"\boverloaded\b|\binternal server error\b|\bbad gateway\b|"
            r"\bgateway timeout\b|\bHTTP\s*(?:500|502|503|504)\b)"
        ),
    ),
    (
        "transport_disconnect",
        re.compile(
            r"(?i)(?:\bconnection (?:reset|closed|refused)\b|\bfailed to connect\b|"
            r"\bnetwork (?:error|unreachable)\b|\bstream (?:disconnected|closed)\b|"
            r"\bDNS (?:error|failure|lookup)\b|\bTLS handshake\b|"
            r"\brequest timed out\b)"
        ),
    ),
)
_SECRET_PATTERNS = (
    ("provider_api_key", re.compile(
        r"(?i)(?:OPENAI|OPENROUTER|ANTHROPIC)_API_KEY\s*[:=]\s*['\"]?[^\s'\"]{20,}"
    )),
    ("authorization_bearer", re.compile(r"(?i)Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~-]{20,}")),
    ("provider_sk", re.compile(r"\bsk-[A-Za-z0-9._-]{20,}\b")),
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("slack_token", re.compile(r"\bxox(?:b|p|a|r|s)-[A-Za-z0-9-]{20,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("stripe_live_secret", re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
)


def _prepare_appworld_draft_run_lock_legacy_v2(
    *,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
    cases_root: str | Path = DEFAULT_CASES_ROOT,
    case_packet_root: str | Path = _PACKET_ROOT,
) -> dict[str, Any]:
    """Exclusively freeze the clean 5.6-Sol formal run before generation."""

    lock_file = resolve_repo_path(lock_path).resolve()
    formal_root = resolve_repo_path(cases_root).resolve()
    packet_root = _input_directory(case_packet_root, "case packet root")
    preflight_root = _input_directory(DEFAULT_PREFLIGHT_ROOT, "approved preflight root")
    preflight_original_root = _input_directory(DEFAULT_PREFLIGHT_ORIGINAL_ROOT, "original preflight snapshot")
    preflight_resolution = _input_file(DEFAULT_PREFLIGHT_RESOLUTION_PATH, "preflight resolution manifest")
    preflight_fresh_challenge = _input_directory(DEFAULT_PREFLIGHT_FRESH_CHALLENGE_ROOT, "fresh challenge source snapshot")
    _require(lock_file.name == DEFAULT_LOCK_PATH.name, "pre-run lock filename must be draft_run_lock.json")
    _require(not lock_file.exists(), f"pre-run lock already exists: {lock_file}")
    _require(not formal_root.exists(), f"formal cases root must be absent at lock time: {formal_root}")
    quarantine_root = formal_root.parent / "quarantine"
    _require(not quarantine_root.exists(), f"formal quarantine root must be absent at lock time: {quarantine_root}")
    _require(not resolve_repo_path(DEFAULT_ACCEPTED_CASES_ROOT).exists(), "accepted_cases must be absent at lock time")

    preflight_entries = sorted(path.name for path in preflight_root.iterdir())
    _require(preflight_entries == sorted(EXPECTED_PREFLIGHT_CASE_IDS), "preflight case directory set drift")
    _require(sha256_path(preflight_root) == EXPECTED_PREFLIGHT_TREE_SHA256, "approved preflight tree hash drift")
    _require(sha256_path(preflight_original_root) == EXPECTED_PREFLIGHT_ORIGINAL_TREE_SHA256, "original preflight snapshot hash drift")
    _require(sha256_file(preflight_resolution) == EXPECTED_PREFLIGHT_RESOLUTION_SHA256, "preflight resolution manifest hash drift")
    _require(sha256_path(preflight_fresh_challenge) == EXPECTED_PREFLIGHT_FRESH_CHALLENGE_TREE_SHA256, "fresh challenge source snapshot hash drift")
    resolution_audit = _validate_preflight_resolution_legacy_v2(
        original_root=preflight_original_root,
        stable_root=preflight_root,
        fresh_challenge_root=preflight_fresh_challenge,
        manifest_path=preflight_resolution,
    )
    preflight_audit = _validate_preflight_root_legacy_v2(preflight_root=preflight_root, packet_root=packet_root)

    inputs, cases = _freeze_inputs(packet_root)
    prompt = _freeze_prompt()
    runtime = _live_runtime()
    login = _codex_login_status(runtime["codex_executable"])
    _require(login == "Logged in using ChatGPT", f"Codex CLI is not logged in with ChatGPT: {login!r}")
    environment = _freeze_environment()
    command_argv = _expected_batch_argv(packet_root=packet_root, cases_root=formal_root)
    lock = {
        "schema_version": LOCK_SCHEMA,
        "status": "locked_pre_run",
        "locked_at": _utc_now(),
        "experiment_id": EXPECTED_EXPERIMENT_ID,
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "authorization": {
            "requested_by_user": True,
            "provider_change": (
                "user-authorized replacement of the deleted/aborted Codex-login gpt-5.4/high "
                "draft attempt with Codex-login gpt-5.6-sol/xhigh; historical OpenRouter "
                "baseline remains separate and nonauthoritative"
            ),
            "external_case_packet_transfer_approved": True,
            "approved_case_count": EXPECTED_EXTENSION_COUNT,
            "approved_concurrency": 8,
        },
        "scope_deviation": {
            "predecessor_reuse_allowed": False,
            "historical_gpt54_drafts_authoritative": False,
            "new_namespace_required": True,
            "estimand": "68 test_normal extension plus 417 test_challenge cases",
            "authorized_scope_lock_sha256": EXPECTED_FROZEN_SCOPE_SHA256,
            "legacy_scope_drafter_authoritative": False,
            "provider_model_reasoning": "legacy OpenRouter gpt-5.4/high -> Codex login gpt-5.6-sol/xhigh",
            "oversized_concurrency": "legacy 2 -> formal upper bound 8",
            "runtime_gate_and_quarantine_added": True,
            "formal_codex_launcher_hardened_to_frozen_absolute_executable": True,
        },
        "repository": {
            "base_commit": _git_commit(),
            "reproducibility_rule": "Every uncommitted executable/input byte is frozen by SHA-256 below.",
        },
        "inputs": inputs,
        "preflight": {
            "root": _repo_relative(preflight_root),
            "tree_sha256": EXPECTED_PREFLIGHT_TREE_SHA256,
            "original_snapshot_root": _repo_relative(preflight_original_root),
            "original_snapshot_tree_sha256": EXPECTED_PREFLIGHT_ORIGINAL_TREE_SHA256,
            "fresh_challenge_source_root": _repo_relative(preflight_fresh_challenge),
            "fresh_challenge_source_tree_sha256": EXPECTED_PREFLIGHT_FRESH_CHALLENGE_TREE_SHA256,
            "resolution_manifest_path": _repo_relative(preflight_resolution),
            "resolution_manifest_sha256": EXPECTED_PREFLIGHT_RESOLUTION_SHA256,
            "resolution_validation_semantic_sha256": sha256_object(resolution_audit),
            "case_ids": list(EXPECTED_PREFLIGHT_CASE_IDS),
            "case_count_by_dataset": {"test_normal": 2, "test_challenge": 1},
            "includes_max_oversized_packet": True,
            "required_gates": [
                "model_auth_reasoning",
                "schema",
                "source_local_support_locations",
                "event_command_confinement",
                "secret_scan",
            ],
            "all_required_gates_passed": True,
            "validation_semantic_sha256": sha256_object(preflight_audit),
        },
        "prompt": prompt,
        "runtime": {**runtime, "login_status_at_lock": login, "auth_mode": "codex_login"},
        "environment": environment,
        "drafter": {
            "provider": "codex",
            "llm_call_provider": "codex_cli",
            "auth_mode": "codex_login",
            "requested_model_alias": EXPECTED_MODEL,
            "backend_model_revision": None,
            "reasoning_effort": EXPECTED_REASONING_EFFORT,
            "model_verbosity": EXPECTED_MODEL_VERBOSITY,
            "temperature_recorded": 0.0,
            "temperature_enforced": False,
            "codex_sandbox": EXPECTED_CODEX_SANDBOX,
            "max_output_token_budgets": list(EXPECTED_TOKEN_BUDGETS),
            "max_output_tokens_enforced": False,
            "regular_codex_timeout_seconds": 1800,
            "oversized_codex_timeout_seconds": 3600,
            "regular_http_timeout_seconds": 180,
            "oversized_http_timeout_seconds": 480,
            "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
            "regular_max_parallel": EXPECTED_MAX_PARALLEL,
            "oversized_max_parallel": EXPECTED_MAX_PARALLEL,
            "lane_execution": "regular then oversized",
            "sort_by": "size",
            "quality_check": "none",
            "pre_promotion_runtime_gate": RUNTIME_GATE_SCHEMA,
            "resume_allowed": False,
            "skipped_existing_allowed": False,
            "interruption_or_any_final_failure_invalidates_namespace": True,
            "retry_rule": (
                "Retry after nonzero drafter exit, checklist-validator failure, or AppWorld v56 "
                "runtime-policy failure; quarantine every rejected attempt with hashes/reason and "
                "promote the first attempt that passes both validator and runtime policy."
            ),
        },
        "execution": {
            "output_root": _repo_relative(formal_root),
            "quarantine_root": _repo_relative(quarantine_root),
            "pre_run_output_root_exists": False,
            "pre_run_output_entry_count": 0,
            "pre_run_quarantine_root_exists": False,
            "environment_policy": ENVIRONMENT_POLICY,
            "command_argv": command_argv,
            "command_semantic_sha256": sha256_object(command_argv),
        },
        "acceptance": {
            "required_case_count": EXPECTED_EXTENSION_COUNT,
            "required_case_count_by_dataset": {
                "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
                "test_challenge": EXPECTED_CHALLENGE_COUNT,
            },
            "required_lane_counts": EXPECTED_LANE_COUNTS,
            "required_schema": "case_checklist_v1",
            "required_identity_match": ["domain", "case_unit_id", "task_id", "split", "source_ref"],
            "required_final_status": LIFECYCLE,
            "formal_repairs_allowed": False,
            "correction_count": 0,
            "require_exact_case_directory_set": True,
            "require_exact_final_seven_file_bundle": True,
            "require_final_bundle_matches_one_successful_attempt": True,
            "require_runtime_policy_gate_before_promotion": True,
            "require_rejected_attempt_quarantine": True,
            "require_accepted_tree_excludes_rejected_attempts": True,
            "require_yaml_json_semantic_equality": True,
            "require_json_schema_validation": True,
            "require_strict_guardrail_validation": True,
            "require_support_pointer_locations_resolvable": True,
            "require_official_source_hash_match": True,
            "require_codex_login_provenance": True,
            "require_provider_model_reasoning_match": True,
            "require_successful_codex_event_stream": True,
            "require_nonzero_token_usage": True,
            "require_promoted_event_command_confinement": True,
            "require_rejected_attempt_policy_evidence": True,
            "require_no_environment_enumeration": True,
            "require_no_symlinks": True,
            "require_no_secret_material": True,
            "require_identity_accepted_materialization": True,
            "require_hash_lock_after_validation": True,
        },
    }
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    _write_json_exclusive(lock_file, lock)
    return {
        "schema_version": LOCK_SCHEMA,
        "status": "locked_pre_run",
        "lock_path": _repo_relative(lock_file),
        "lock_sha256": sha256_file(lock_file),
        "case_count": len(cases),
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "regular_max_parallel": EXPECTED_MAX_PARALLEL,
        "oversized_max_parallel": EXPECTED_MAX_PARALLEL,
        "environment_policy": ENVIRONMENT_POLICY,
        "command_argv": command_argv,
    }


def _failed_v2_snapshot_audit() -> dict[str, Any]:
    """Bind the rejected predecessor as diagnostics-only and forbid every reuse path."""

    root = _input_directory(FAILED_V2_DRAFT_ROOT, "failed v2 diagnostic draft root")
    manifest_path = _input_file(FAILED_V2_DIAGNOSTIC_PATH, "failed v2 diagnostic manifest")
    _require(
        sha256_path(root) == EXPECTED_FAILED_V2_TREE_SHA256,
        "failed v2 diagnostic snapshot tree drifted",
    )
    _require(
        sha256_file(manifest_path) == EXPECTED_FAILED_V2_DIAGNOSTIC_SHA256,
        "failed v2 diagnostic manifest drifted",
    )
    manifest = _load_mapping(manifest_path, "failed v2 diagnostic manifest")
    _require(
        manifest.get("schema_version") == "appworld_failed_draft_run_snapshot.v1"
        and manifest.get("status") == "invalid_preserved_for_diagnostics_only",
        "failed v2 diagnostic identity drift",
    )
    _require(
        manifest.get("draft_run_root") == _repo_relative(root)
        and manifest.get("draft_run_tree_sha256") == EXPECTED_FAILED_V2_TREE_SHA256,
        "failed v2 manifest/tree binding drift",
    )
    for key in ("reuse_prohibited", "resume_prohibited", "promotion_prohibited"):
        _require(manifest.get(key) is True, f"failed v2 diagnostic policy disabled: {key}")
    return {
        "root": _repo_relative(root),
        "tree_sha256": EXPECTED_FAILED_V2_TREE_SHA256,
        "manifest_path": _repo_relative(manifest_path),
        "manifest_sha256": EXPECTED_FAILED_V2_DIAGNOSTIC_SHA256,
        "status": "diagnostics_only",
        "reuse_prohibited": True,
        "resume_prohibited": True,
        "promotion_prohibited": True,
    }


def _failed_v3_canary_snapshot_audit() -> dict[str, Any]:
    """Bind the failed strict-v3 canary materialization as diagnostics-only."""

    root = _input_directory(FAILED_V3_CANARY_ROOT, "failed v3 canary materialization")
    manifest_path = _input_file(
        FAILED_V3_CANARY_DIAGNOSTIC_PATH,
        "failed v3 canary diagnostic manifest",
    )
    _require(
        sha256_path(root) == EXPECTED_FAILED_V3_CANARY_TREE_SHA256,
        "failed v3 canary materialization tree drifted",
    )
    _require(
        sha256_file(manifest_path) == EXPECTED_FAILED_V3_CANARY_DIAGNOSTIC_SHA256,
        "failed v3 canary diagnostic manifest drifted",
    )
    manifest = _load_mapping(manifest_path, "failed v3 canary diagnostic manifest")
    canary = _mapping(manifest.get("canary"), "failed v3 canary record")
    _require(
        manifest.get("schema_version") == "appworld_gpt56_failed_namespace.v1"
        and manifest.get("status") == "diagnostic_only"
        and manifest.get("reuse_permitted") is False,
        "failed v3 canary diagnostic identity/policy drift",
    )
    _require(
        manifest.get("materialization_root") == _repo_relative(root)
        and manifest.get("root_tree_sha256_at_audit")
        == EXPECTED_FAILED_V3_CANARY_TREE_SHA256,
        "failed v3 canary manifest/tree binding drift",
    )
    _require(
        canary.get("terminal_status") == "invalid_complete"
        and canary.get("infra_retry_permitted") is False
        and canary.get("failed_case_id") == "988af8e_2",
        "failed v3 canary terminal classification drift",
    )
    return {
        "root": _repo_relative(root),
        "tree_sha256": EXPECTED_FAILED_V3_CANARY_TREE_SHA256,
        "manifest_path": _repo_relative(manifest_path),
        "manifest_sha256": EXPECTED_FAILED_V3_CANARY_DIAGNOSTIC_SHA256,
        "status": "diagnostics_only",
        "reuse_prohibited": True,
        "terminal_status": "invalid_complete",
        "failed_case_id": "988af8e_2",
    }


def _failed_v3_guardrail_snapshot_audit() -> dict[str, Any]:
    """Bind the second failed strict-v3 canary materialization."""

    root = _input_directory(
        FAILED_V3_GUARDRAIL_ROOT,
        "failed v3 guardrail materialization",
    )
    manifest_path = _input_file(
        FAILED_V3_GUARDRAIL_DIAGNOSTIC_PATH,
        "failed v3 guardrail diagnostic manifest",
    )
    _require(
        sha256_path(root) == EXPECTED_FAILED_V3_GUARDRAIL_TREE_SHA256,
        "failed v3 guardrail materialization tree drifted",
    )
    _require(
        sha256_file(manifest_path) == EXPECTED_FAILED_V3_GUARDRAIL_DIAGNOSTIC_SHA256,
        "failed v3 guardrail diagnostic manifest drifted",
    )
    manifest = _load_mapping(manifest_path, "failed v3 guardrail diagnostic manifest")
    canary = _mapping(manifest.get("canary"), "failed v3 guardrail canary record")
    _require(
        manifest.get("schema_version") == "appworld_gpt56_failed_namespace.v1"
        and manifest.get("status") == "diagnostic_only"
        and manifest.get("reuse_permitted") is False,
        "failed v3 guardrail diagnostic identity/policy drift",
    )
    _require(
        manifest.get("materialization_root") == _repo_relative(root)
        and manifest.get("root_tree_sha256_at_audit")
        == EXPECTED_FAILED_V3_GUARDRAIL_TREE_SHA256,
        "failed v3 guardrail manifest/tree binding drift",
    )
    _require(
        canary.get("terminal_status") == "invalid_complete"
        and canary.get("infra_retry_permitted") is False
        and canary.get("failed_case_id") == "d18139b_3",
        "failed v3 guardrail terminal classification drift",
    )
    return {
        "root": _repo_relative(root),
        "tree_sha256": EXPECTED_FAILED_V3_GUARDRAIL_TREE_SHA256,
        "manifest_path": _repo_relative(manifest_path),
        "manifest_sha256": EXPECTED_FAILED_V3_GUARDRAIL_DIAGNOSTIC_SHA256,
        "status": "diagnostics_only",
        "reuse_prohibited": True,
        "terminal_status": "invalid_complete",
        "failed_case_id": "d18139b_3",
    }


def _failed_v4_formal_snapshot_audit() -> dict[str, Any]:
    """Bind the stopped v4 formal run as immutable diagnostics-only input."""

    root = _input_directory(FAILED_V4_FORMAL_ROOT, "failed v4 formal materialization")
    manifest_path = _input_file(
        FAILED_V4_FORMAL_DIAGNOSTIC_PATH,
        "failed v4 formal diagnostic manifest",
    )
    _require(
        sha256_path(root) == EXPECTED_FAILED_V4_FORMAL_TREE_SHA256,
        "failed v4 formal materialization tree drifted",
    )
    _require(
        sha256_file(manifest_path) == EXPECTED_FAILED_V4_FORMAL_DIAGNOSTIC_SHA256,
        "failed v4 formal diagnostic manifest drifted",
    )
    manifest = _load_mapping(manifest_path, "failed v4 formal diagnostic manifest")
    formal = _mapping(manifest.get("formal_run"), "failed v4 formal run record")
    _require(
        manifest.get("schema_version") == "appworld_gpt56_failed_namespace.v1"
        and manifest.get("status") == "diagnostic_only"
        and manifest.get("materialization_root") == _repo_relative(root)
        and manifest.get("root_tree_sha256_at_audit")
        == EXPECTED_FAILED_V4_FORMAL_TREE_SHA256
        and manifest.get("reuse_permitted") is False
        and manifest.get("resume_permitted") is False
        and manifest.get("promotion_permitted") is False,
        "failed v4 formal diagnostic identity/policy drift",
    )
    _require(
        formal.get("terminal_status") == "invalid_partial"
        and formal.get("termination_reason") == "strict_realtime_content_audit_p1"
        and formal.get("infra_retry_permitted") is False
        and formal.get("failed_case_id") == "258796c_3"
        and formal.get("completed_case_count") == 34
        and formal.get("successful_case_count") == 34
        and formal.get("initiated_case_count") == 50
        and formal.get("interrupted_partial_attempt_count") == 16
        and formal.get("queued_empty_case_count") == 8
        and formal.get("response_id_count") == 34
        and formal.get("unique_response_id_count") == 34
        and formal.get("sorted_response_ids_sha256")
        == EXPECTED_FAILED_V4_FORMAL_RESPONSE_IDS_SHA256,
        "failed v4 formal terminal/count classification drift",
    )
    return {
        "root": _repo_relative(root),
        "tree_sha256": EXPECTED_FAILED_V4_FORMAL_TREE_SHA256,
        "manifest_path": _repo_relative(manifest_path),
        "manifest_sha256": EXPECTED_FAILED_V4_FORMAL_DIAGNOSTIC_SHA256,
        "status": "diagnostics_only",
        "reuse_prohibited": True,
        "resume_prohibited": True,
        "promotion_prohibited": True,
        "terminal_status": "invalid_partial",
        "failed_case_id": "258796c_3",
        "response_id_count": 34,
    }


def _failed_v5_canary_snapshot_audit() -> dict[str, Any]:
    """Bind the invalid v5 round-01 canary as immutable diagnostics only."""

    root = _input_directory(FAILED_V5_CANARY_ROOT, "failed v5 canary materialization")
    manifest_path = _input_file(
        FAILED_V5_CANARY_DIAGNOSTIC_PATH,
        "failed v5 canary diagnostic manifest",
    )
    _require(
        sha256_path(root) == EXPECTED_FAILED_V5_CANARY_TREE_SHA256,
        "failed v5 canary materialization tree drifted",
    )
    _require(
        sha256_file(manifest_path) == EXPECTED_FAILED_V5_CANARY_DIAGNOSTIC_SHA256,
        "failed v5 canary diagnostic manifest drifted",
    )
    manifest = _load_mapping(manifest_path, "failed v5 canary diagnostic manifest")
    canary = _mapping(manifest.get("canary"), "failed v5 canary record")
    finding = _mapping(manifest.get("finding"), "failed v5 canary finding")
    _require(
        manifest.get("schema_version") == "appworld_gpt56_failed_namespace.v1"
        and manifest.get("status") == "diagnostic_only"
        and manifest.get("materialization_root") == _repo_relative(root)
        and manifest.get("root_tree_sha256_at_audit")
        == EXPECTED_FAILED_V5_CANARY_TREE_SHA256
        and manifest.get("reuse_permitted") is False
        and manifest.get("resume_permitted") is False
        and manifest.get("promotion_permitted") is False,
        "failed v5 canary diagnostic identity/policy drift",
    )
    _require(
        canary.get("round_id") == "round_01"
        and canary.get("terminal_status") == "invalid_complete"
        and canary.get("termination_reason") == "strict_runtime_read_plan_p1"
        and canary.get("infra_retry_permitted") is False
        and canary.get("failed_case_id") == "d18139b_3"
        and canary.get("completed_case_count") == 8
        and canary.get("successful_case_count") == 7
        and canary.get("failed_case_count") == 1
        and canary.get("response_id_count") == 8
        and canary.get("unique_response_id_count") == 8
        and canary.get("sorted_response_ids_sha256")
        == EXPECTED_FAILED_V5_CANARY_RESPONSE_IDS_SHA256,
        "failed v5 canary terminal/count classification drift",
    )
    _require(
        finding.get("severity") == "P1"
        and finding.get("category") == "mandatory_read_plan_duplicate_invocation"
        and finding.get("expected_read_invocation_count") == 33
        and finding.get("observed_read_invocation_count") == 34
        and finding.get("duplicated_command_execution_count") == 2
        and finding.get("codex_returncode") == 0
        and finding.get("checklist_validator_status") == "passed"
        and finding.get("runtime_policy_gate_status") == "failed"
        and finding.get("runtime_policy_error_sha256")
        == "4ac081d6971d13711374f7d52da23fa658bcf56ca06d185e9e1d885492037b8a",
        "failed v5 canary P1 classification drift",
    )
    return {
        "root": _repo_relative(root),
        "tree_sha256": EXPECTED_FAILED_V5_CANARY_TREE_SHA256,
        "manifest_path": _repo_relative(manifest_path),
        "manifest_sha256": EXPECTED_FAILED_V5_CANARY_DIAGNOSTIC_SHA256,
        "status": "diagnostics_only",
        "reuse_prohibited": True,
        "resume_prohibited": True,
        "promotion_prohibited": True,
        "terminal_status": "invalid_complete",
        "failed_case_id": "d18139b_3",
        "response_id_count": 8,
    }


def _locked_canary_plan(*, cases: Sequence[Mapping[str, str]], packet_root: Path) -> dict[str, Any]:
    by_id = {case["case_unit_id"]: case for case in cases}
    _require(
        set(EXPECTED_PREFLIGHT_CASE_IDS) <= set(by_id),
        "one or more frozen canary IDs are absent from the 485-case manifest",
    )
    case_records: list[dict[str, Any]] = []
    lane_counts: Counter[str] = Counter()
    dataset_counts: Counter[str] = Counter()
    composition_counts: Counter[tuple[str, str, str]] = Counter()
    for case_id in EXPECTED_PREFLIGHT_CASE_IDS:
        case = by_id[case_id]
        packet = _input_file(packet_root / case_id / "case_packet.md", f"canary packet {case_id}")
        lane = "oversized" if packet.stat().st_size > EXPECTED_LARGE_THRESHOLD_BYTES else "regular"
        dataset = _string(case.get("dataset_name"), f"canary dataset {case_id}")
        _require(dataset in {"test_normal", "test_challenge"}, f"canary split is off-scope: {case_id}")
        lane_counts[lane] += 1
        dataset_counts[dataset] += 1
        registry = appworld_packet_registered_test_registry(
            packet.read_text(encoding="utf-8")
        )
        gap_registry = parse_packet_stronger_gap_registry(
            packet.read_text(encoding="utf-8")
        )
        gap_status = _string(
            _mapping(gap_registry.get("case"), f"canary stronger-gap case {case_id}").get(
                "review_status"
            ),
            f"canary stronger-gap review status {case_id}",
        )
        _require(
            gap_status in {"reviewed_gap", "reviewed_no_gap"},
            f"canary stronger-gap status is invalid: {case_id}",
        )
        composition_counts[(dataset, lane, gap_status)] += 1
        registered_tests = registry.get("registered_tests")
        _require(
            isinstance(registered_tests, list) and registered_tests,
            f"canary packet has no registered-test registry: {case_id}",
        )
        case_records.append(
            {
                "case_unit_id": case_id,
                "dataset_name": dataset,
                "lane": lane,
                "stronger_gap_review_status": gap_status,
                "packet_size_bytes": packet.stat().st_size,
                "case_packet_sha256": sha256_file(packet),
                "registered_test_count": len(registered_tests),
            }
        )
    _require(dict(dataset_counts) == EXPECTED_PREFLIGHT_CASE_COUNT_BY_DATASET, "canary split coverage drift")
    _require(dict(lane_counts) == EXPECTED_PREFLIGHT_LANE_COUNTS, "canary lane coverage drift")
    _require(
        Counter((record["dataset_name"], record["lane"]) for record in case_records)
        == Counter(
            {
                ("test_normal", "regular"): 2,
                ("test_normal", "oversized"): 2,
                ("test_challenge", "regular"): 2,
                ("test_challenge", "oversized"): 2,
            }
        ),
        "canary cases must cover the split-by-lane cross product",
    )
    _require(
        composition_counts
        == Counter(
            {
                (dataset, lane, review_status): 1
                for dataset in ("test_normal", "test_challenge")
                for lane in ("regular", "oversized")
                for review_status in ("reviewed_gap", "reviewed_no_gap")
            }
        ),
        "canary cases must cover the split-by-lane-by-gap-status cross product",
    )
    max_registered_test_count_by_dataset: dict[str, int] = {}
    for dataset in ("test_normal", "test_challenge"):
        counts: list[int] = []
        for case in cases:
            if case["dataset_name"] != dataset:
                continue
            case_id = case["case_unit_id"]
            packet = _input_file(
                packet_root / case_id / "case_packet.md",
                f"composition audit packet {case_id}",
            )
            registry = appworld_packet_registered_test_registry(
                packet.read_text(encoding="utf-8")
            )
            registered_tests = registry.get("registered_tests")
            _require(
                isinstance(registered_tests, list) and registered_tests,
                f"packet has no registered-test registry: {case_id}",
            )
            counts.append(len(registered_tests))
        _require(counts, f"canary composition audit split is empty: {dataset}")
        max_registered_test_count_by_dataset[dataset] = max(counts)
    _require(
        next(
            record
            for record in case_records
            if record["case_unit_id"] == "6b6ca61_1"
        )["registered_test_count"]
        == max_registered_test_count_by_dataset["test_normal"],
        "normal regular canary no longer has the maximum registered-test composition",
    )
    _require(
        next(
            record
            for record in case_records
            if record["case_unit_id"] == "988af8e_2"
        )["registered_test_count"]
        == max_registered_test_count_by_dataset["test_challenge"],
        "challenge regular canary no longer has the maximum registered-test composition",
    )
    _require(
        next(record for record in case_records if record["case_unit_id"] == "d18139b_3")["packet_size_bytes"]
        == max((packet_root / case["case_unit_id"] / "case_packet.md").stat().st_size for case in cases),
        "normal canary no longer contains the maximum extension packet",
    )
    _require(
        next(record for record in case_records if record["case_unit_id"] == "953b296_2")["packet_size_bytes"]
        == max(
            (packet_root / case["case_unit_id"] / "case_packet.md").stat().st_size
            for case in cases
            if case["dataset_name"] == "test_challenge"
        ),
        "challenge canary no longer contains the maximum challenge packet",
    )
    rounds: list[dict[str, Any]] = []
    formal_root = resolve_repo_path(DEFAULT_CASES_ROOT).resolve()
    failed_roots = (
        resolve_repo_path(FAILED_V2_DRAFT_ROOT).resolve(),
        resolve_repo_path(FAILED_V3_CANARY_ROOT).resolve(),
        resolve_repo_path(FAILED_V3_GUARDRAIL_ROOT).resolve(),
        resolve_repo_path(FAILED_V4_FORMAL_ROOT).resolve(),
        resolve_repo_path(FAILED_V5_CANARY_ROOT).resolve(),
    )
    for round_id in EXPECTED_PREFLIGHT_ROUNDS:
        output_root = resolve_repo_path(DEFAULT_PREFLIGHT_ROOT / round_id / "cases").resolve()
        _require(
            output_root != formal_root
            and output_root != packet_root
            and all(failed_root not in output_root.parents for failed_root in failed_roots)
            and all(output_root not in failed_root.parents for failed_root in failed_roots)
            and packet_root not in output_root.parents
            and output_root not in packet_root.parents,
            f"canary output root overlaps formal, packet, or failed namespace: {round_id}",
        )
        rounds.append(
            {
                "round_id": round_id,
                "output_root": _repo_relative(output_root),
                "quarantine_root": _repo_relative(output_root.parent / "quarantine"),
                "command_argv": _expected_canary_batch_argv(
                    packet_root=packet_root,
                    cases_root=output_root,
                    round_id=round_id,
                ),
                "command_semantic_sha256": sha256_object(
                    _expected_canary_batch_argv(
                        packet_root=packet_root,
                        cases_root=output_root,
                        round_id=round_id,
                    )
                ),
                "case_ids": list(EXPECTED_PREFLIGHT_CASE_IDS),
                "case_count": len(EXPECTED_PREFLIGHT_CASE_IDS),
                "case_count_by_dataset": dict(EXPECTED_PREFLIGHT_CASE_COUNT_BY_DATASET),
                "lane_counts": dict(EXPECTED_PREFLIGHT_LANE_COUNTS),
            }
        )
    return {
        "schema_version": "appworld_draft_canary_plan.v1",
        "root": _repo_relative(resolve_repo_path(DEFAULT_PREFLIGHT_ROOT).resolve()),
        "round_ids": list(EXPECTED_PREFLIGHT_ROUNDS),
        "round_count": len(EXPECTED_PREFLIGHT_ROUNDS),
        "case_ids": list(EXPECTED_PREFLIGHT_CASE_IDS),
        "case_count_per_round": len(EXPECTED_PREFLIGHT_CASE_IDS),
        "case_count_by_dataset_per_round": dict(EXPECTED_PREFLIGHT_CASE_COUNT_BY_DATASET),
        "lane_counts_per_round": dict(EXPECTED_PREFLIGHT_LANE_COUNTS),
        "case_records": case_records,
        "max_registered_test_count_by_dataset": max_registered_test_count_by_dataset,
        "rounds": rounds,
        "pre_run_root_exists": False,
        "fresh_round_namespaces_required": True,
        "rounds_must_be_nonoverlapping_and_consecutive": True,
        "same_locked_inputs_required_for_every_round": True,
        "acceptance_receipt_path": _repo_relative(
            resolve_repo_path(DEFAULT_CANARY_ACCEPTANCE_PATH).resolve()
        ),
        "acceptance_required_before_formal_run": True,
        "required_gates": [
            "model_auth_reasoning",
            "json_schema_and_guardrails",
            "source_local_support_locations_v3",
            "single_command_event_confinement_v2",
            "appworld_testtracker_evaluator_composition",
            "official_source_hashes",
            "secret_scan",
        ],
    }


def prepare_appworld_draft_run_lock_v56(
    *,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
    cases_root: str | Path = DEFAULT_CASES_ROOT,
    case_packet_root: str | Path = _PACKET_ROOT,
) -> dict[str, Any]:
    """Freeze immutable v3 inputs and a three-round canary plan before any generation."""

    lock_file = resolve_repo_path(lock_path).resolve()
    formal_root = resolve_repo_path(cases_root).resolve()
    draft_root = formal_root.parent
    packet_root = _input_directory(case_packet_root, "case packet root")
    canary_root = resolve_repo_path(DEFAULT_PREFLIGHT_ROOT).resolve()
    canary_acceptance_path = draft_root / "provenance" / DEFAULT_CANARY_ACCEPTANCE_PATH.name
    _require(
        formal_root == resolve_repo_path(DEFAULT_CASES_ROOT).resolve()
        and draft_root == resolve_repo_path(DEFAULT_DRAFT_ROOT).resolve(),
        "formal draft root must use the canonical clean support-v3 namespace",
    )
    _require(lock_file == draft_root / "provenance" / DEFAULT_LOCK_PATH.name, "pre-run lock must be inside the new draft namespace provenance directory")
    _require(not lock_file.exists(), f"pre-run lock already exists: {lock_file}")
    _require(not draft_root.exists(), f"new draft namespace must be wholly absent at lock time: {draft_root}")
    _require(not canary_root.exists(), f"new canary namespace must be wholly absent at lock time: {canary_root}")
    _require(not canary_acceptance_path.exists(), "canary acceptance must not pre-exist the input lock")

    predecessor = {
        "failed_v2": _failed_v2_snapshot_audit(),
        "failed_v3_canary": _failed_v3_canary_snapshot_audit(),
        "failed_v3_guardrail": _failed_v3_guardrail_snapshot_audit(),
        "failed_v4_formal": _failed_v4_formal_snapshot_audit(),
        "failed_v5_canary": _failed_v5_canary_snapshot_audit(),
    }
    inputs, cases = _freeze_inputs(packet_root)
    prompt = _freeze_prompt()
    runtime = _live_runtime()
    login = _codex_login_status(runtime["codex_executable"])
    _require(login == "Logged in using ChatGPT", f"Codex CLI is not logged in with ChatGPT: {login!r}")
    environment = _freeze_environment()
    canary_plan = _locked_canary_plan(cases=cases, packet_root=packet_root)
    command_argv = _expected_batch_argv(packet_root=packet_root, cases_root=formal_root)
    quarantine_root = formal_root.parent / "quarantine"
    lock = {
        "schema_version": LOCK_SCHEMA,
        "status": "locked_pre_run",
        "locked_at": _utc_now(),
        "experiment_id": EXPECTED_EXPERIMENT_ID,
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "authorization": {
            "requested_by_user": True,
            "external_case_packet_transfer_approved": True,
            "approved_case_count": EXPECTED_EXTENSION_COUNT,
            "approved_concurrency": EXPECTED_MAX_PARALLEL,
            "provider_model_reasoning": "Codex CLI ChatGPT login / gpt-5.6-sol / xhigh",
        },
        "scope_deviation": {
            "estimand": "68 test_normal extension plus 417 test_challenge cases",
            "authorized_scope_lock_sha256": EXPECTED_FROZEN_SCOPE_SHA256,
            "new_namespace_required": True,
            "predecessor_snapshot": predecessor,
            "predecessor_artifact_reuse_allowed": False,
            "formal_repairs_allowed": False,
        },
        "repository": {
            "base_commit": _git_commit(),
            "reproducibility_rule": "Every uncommitted executable/input byte is frozen by SHA-256 below.",
        },
        "inputs": inputs,
        "preflight": canary_plan,
        "prompt": prompt,
        "runtime": {**runtime, "login_status_at_lock": login, "auth_mode": "codex_login"},
        "environment": environment,
        "drafter": {
            "provider": "codex",
            "llm_call_provider": "codex_cli",
            "auth_mode": "codex_login",
            "requested_model_alias": EXPECTED_MODEL,
            "backend_model_revision": None,
            "reasoning_effort": EXPECTED_REASONING_EFFORT,
            "model_verbosity": EXPECTED_MODEL_VERBOSITY,
            "temperature_recorded": 0.0,
            "temperature_enforced": False,
            "codex_sandbox": EXPECTED_CODEX_SANDBOX,
            "max_output_token_budgets": list(EXPECTED_TOKEN_BUDGETS),
            "max_output_tokens_enforced": False,
            "regular_codex_timeout_seconds": 1800,
            "oversized_codex_timeout_seconds": 3600,
            "regular_http_timeout_seconds": 180,
            "oversized_http_timeout_seconds": 480,
            "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
            "regular_max_parallel": EXPECTED_MAX_PARALLEL,
            "oversized_max_parallel": EXPECTED_MAX_PARALLEL,
            "lane_execution": "regular then oversized",
            "sort_by": "size",
            "quality_check": "none",
            "pre_promotion_runtime_gate": RUNTIME_GATE_SCHEMA,
            "appworld_semantic_gate": "appworld_checklist_evaluator_semantics.v1",
            "resume_allowed": False,
            "skipped_existing_allowed": False,
            "interruption_or_any_final_failure_invalidates_namespace": True,
            "retry_rule": (
                "Retry only after an auditable, allowlisted Codex infrastructure failure "
                "that produced no agent_message; checklist-validator, AppWorld semantic, "
                "and runtime/tool-policy failures invalidate the case and namespace. "
                "Quarantine every rejected attempt and promote only the first fully passing "
                "attempt after an infrastructure-only retry."
            ),
        },
        "execution": {
            "output_root": _repo_relative(formal_root),
            "quarantine_root": _repo_relative(quarantine_root),
            "pre_run_output_root_exists": False,
            "pre_run_output_entry_count": 0,
            "pre_run_quarantine_root_exists": False,
            "environment_policy": ENVIRONMENT_POLICY,
            "command_argv": command_argv,
            "command_semantic_sha256": sha256_object(command_argv),
            "canary_acceptance_path": _repo_relative(canary_acceptance_path),
            "canary_acceptance_required": True,
        },
        "acceptance": {
            "required_case_count": EXPECTED_EXTENSION_COUNT,
            "required_case_count_by_dataset": {
                "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
                "test_challenge": EXPECTED_CHALLENGE_COUNT,
            },
            "required_lane_counts": EXPECTED_LANE_COUNTS,
            "required_schema": "case_checklist_v1",
            "required_identity_match": ["domain", "case_unit_id", "task_id", "split", "source_ref"],
            "required_final_status": LIFECYCLE,
            "formal_repairs_allowed": False,
            "correction_count": 0,
            "require_three_consecutive_canary_rounds": True,
            "require_canary_acceptance_before_formal": True,
            "require_appworld_evaluator_composition_gate": True,
            "require_non_scoring_dynamic_fields_excluded": True,
            "require_exact_case_directory_set": True,
            "require_exact_final_seven_file_bundle": True,
            "require_final_bundle_matches_one_successful_attempt": True,
            "require_runtime_policy_gate_before_promotion": True,
            "require_rejected_attempt_quarantine": True,
            "require_accepted_tree_excludes_rejected_attempts": True,
            "require_yaml_json_semantic_equality": True,
            "require_json_schema_validation": True,
            "require_strict_guardrail_validation": True,
            "require_support_pointer_locations_resolvable": True,
            "require_official_source_hash_match": True,
            "require_codex_login_provenance": True,
            "require_provider_model_reasoning_match": True,
            "require_successful_codex_event_stream": True,
            "require_nonzero_token_usage": True,
            "require_promoted_event_command_confinement": True,
            "require_rejected_attempt_policy_evidence": True,
            "require_rejected_attempts_infra_only": True,
            "require_no_environment_enumeration": True,
            "require_no_symlinks": True,
            "require_no_secret_material": True,
            "require_identity_accepted_materialization": True,
            "require_hash_lock_after_validation": True,
            "require_failed_v2_snapshot_not_reused": True,
            "require_failed_v3_canary_snapshot_not_reused": True,
            "require_failed_v3_guardrail_snapshot_not_reused": True,
            "require_failed_v4_formal_snapshot_not_reused": True,
            "require_failed_v5_canary_snapshot_not_reused": True,
        },
    }
    # The clean materialization intentionally contains neither ``draft_runs``
    # nor this run leaf.  Claim the leaf exclusively while allowing pathlib to
    # create its previously absent container.
    draft_root.mkdir(parents=True, exist_ok=False)
    lock_file.parent.mkdir(parents=False, exist_ok=False)
    _write_json_exclusive(lock_file, lock)
    return {
        "schema_version": LOCK_SCHEMA,
        "status": "locked_pre_run",
        "lock_path": _repo_relative(lock_file),
        "lock_sha256": sha256_file(lock_file),
        "case_count": len(cases),
        "canary_round_count": len(EXPECTED_PREFLIGHT_ROUNDS),
        "canary_case_count_per_round": len(EXPECTED_PREFLIGHT_CASE_IDS),
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "regular_max_parallel": EXPECTED_MAX_PARALLEL,
        "oversized_max_parallel": EXPECTED_MAX_PARALLEL,
        "environment_policy": ENVIRONMENT_POLICY,
        "command_argv": command_argv,
    }


def _freeze_inputs(packet_root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    files = {key: _input_file(path, key.replace("_", " ")) for key, path in _INPUT_PATHS.items()}
    scope_binding = _validate_extension_scope_cross_binding(files)
    cases = _manifest_cases(files["manifest"])
    packet_sha256 = {}
    raw_manifest_sha256 = {}
    evaluator_audit_sha256: dict[str, str] = {}
    registered_test_count = 0
    scoring_block_count = 0
    non_scoring_assignment_count = 0
    for case in cases:
        case_id = case["case_unit_id"]
        packet_path = _input_file(
            packet_root / case_id / "case_packet.md", f"packet {case_id}"
        )
        packet_sha256[case_id] = sha256_file(packet_path)
        raw_manifest_sha256[case_id] = sha256_file(
            _input_file(packet_root / case_id / "raw_case_manifest.json", f"raw manifest {case_id}")
        )
        evaluator_audit = validate_appworld_packet_evaluator_semantics(
            case_packet_root=packet_root / case_id
        )
        _require(
            evaluator_audit.get("case_id") == case_id
            and evaluator_audit.get("status") == "passed",
            f"packet evaluator audit identity/status drift: {case_id}",
        )
        evaluator_audit_sha256[case_id] = _string(
            evaluator_audit.get("audit_semantic_sha256"),
            f"packet evaluator audit hash {case_id}",
        )
        registered_test_count += int(evaluator_audit["test_data_requirement_count"])
        scoring_block_count += int(evaluator_audit["scoring_block_count"])
        assignments = evaluator_audit["non_scoring_test_assignments"]
        _require(
            isinstance(assignments, list)
            and len(assignments) == 1
            and assignments[0].get("attribute") == "task_completed",
            f"packet non-scoring task_completed composition drift: {case_id}",
        )
        non_scoring_assignment_count += len(assignments)
    _require(
        registered_test_count == scoring_block_count == EXPECTED_REGISTERED_TEST_COUNT
        and non_scoring_assignment_count == EXPECTED_EXTENSION_COUNT,
        "full packet evaluator composition totals drift",
    )
    payload: dict[str, Any] = {
        "case_packet_root": _repo_relative(packet_root),
        "case_packet_tree_sha256": sha256_path(packet_root),
        "expected_case_count": EXPECTED_EXTENSION_COUNT,
        "expected_case_count_by_dataset": {
            "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
            "test_challenge": EXPECTED_CHALLENGE_COUNT,
        },
        "case_ids_semantic_sha256": sha256_object([case["case_unit_id"] for case in cases]),
        "case_records_semantic_sha256": sha256_object(cases),
        "case_packet_sha256_by_case": packet_sha256,
        "raw_case_manifest_sha256_by_case": raw_manifest_sha256,
        "packet_evaluator_semantics": {
            "schema_version": "appworld_packet_evaluator_batch.v1",
            "case_count": EXPECTED_EXTENSION_COUNT,
            "registered_test_count": registered_test_count,
            "scoring_block_count": scoring_block_count,
            "non_scoring_task_completed_assignment_count": non_scoring_assignment_count,
            "audit_semantic_sha256_by_case": evaluator_audit_sha256,
            "aggregate_semantic_sha256": sha256_object(evaluator_audit_sha256),
        },
    }
    for key, file in files.items():
        payload[f"{key}_path"] = _repo_relative(file)
        payload[f"{key}_sha256"] = sha256_file(file)
    packet_audit = validate_extension_packets(
        output_root=files["manifest"].parent,
        case_packets_root=packet_root.parent,
    )
    bundle_audit = validate_extension_source_bundle(
        output_root=files["manifest"].parent,
        case_packets_root=packet_root.parent,
        source_bundle_path=files["source_bundle"],
    )
    payload["packet_index_sha256"] = packet_audit["packet_index_sha256"]
    payload["official_source_tree_sha256"] = packet_audit["packet_source_tree_sha256"]
    payload["source_bundle_semantic_sha256"] = sha256_object(bundle_audit)
    payload["extension_scope_cross_binding"] = scope_binding
    return payload, cases


def _validate_extension_scope_cross_binding(files: Mapping[str, Path]) -> dict[str, Any]:
    """Bind the authorized v56 deviation to the immutable 485-case packet scope."""

    scope_file = files["frozen_scope"]
    manifest_file = files["manifest"]
    acceptance_file = files["packet_acceptance_report"]
    _require(sha256_file(scope_file) == EXPECTED_FROZEN_SCOPE_SHA256, "authorized extension frozen_scope hash drift")
    _require(sha256_file(manifest_file) == EXPECTED_EXTENSION_MANIFEST_SHA256, "authorized extension manifest hash drift")
    _require(sha256_file(acceptance_file) == EXPECTED_PACKET_ACCEPTANCE_SHA256, "packet acceptance report hash drift")
    scope = _load_mapping(scope_file, "authorized frozen scope")
    manifest = _load_mapping(manifest_file, "authorized extension manifest")
    acceptance = _load_mapping(acceptance_file, "packet acceptance report")
    _require(manifest.get("scope_lock_path") == _repo_relative(scope_file), "manifest scope-lock path drift")
    manifest_scope_sha = _string(manifest.get("scope_lock_sha256"), "manifest scope-lock hash").removeprefix("sha256:")
    _require(manifest_scope_sha == EXPECTED_FROZEN_SCOPE_SHA256, "manifest scope-lock hash cross-binding drift")
    artifacts = _mapping(acceptance.get("artifact_hashes"), "packet acceptance artifact hashes")
    _require(artifacts.get("scope_lock_sha256") == EXPECTED_FROZEN_SCOPE_SHA256, "acceptance/scope hash cross-binding drift")
    _require(artifacts.get("manifest_sha256") == EXPECTED_EXTENSION_MANIFEST_SHA256, "acceptance/manifest hash cross-binding drift")
    _require(artifacts.get("catalog_sha256") == sha256_file(files["source_catalog"]), "acceptance/catalog hash cross-binding drift")
    frozen_scope = _mapping(scope.get("scope"), "frozen extension scope counts")
    _require(frozen_scope.get("extension_case_count") == 485, "frozen extension scope count drift")
    _require(frozen_scope.get("extension_case_count_by_dataset") == {"test_normal": 68, "test_challenge": 417}, "frozen extension split counts drift")
    acceptance_scope_sha = _string(artifacts.get("scope_lock_sha256"), "acceptance scope-lock hash").removeprefix("sha256:")
    _require(manifest_scope_sha == acceptance_scope_sha, "manifest/acceptance scope-lock disagreement")
    return {
        "status": "verified_authorized_drafter_scope_deviation",
        "frozen_scope_sha256": EXPECTED_FROZEN_SCOPE_SHA256,
        "manifest_sha256": EXPECTED_EXTENSION_MANIFEST_SHA256,
        "packet_acceptance_report_sha256": EXPECTED_PACKET_ACCEPTANCE_SHA256,
        "catalog_sha256": artifacts["catalog_sha256"],
        "case_count": 485,
        "case_count_by_dataset": {"test_normal": 68, "test_challenge": 417},
        "legacy_drafter_configuration_authoritative": False,
    }


def _freeze_prompt() -> dict[str, Any]:
    paths = {key: _input_file(path, f"implementation {key}") for key, path in _IMPLEMENTATION_PATHS.items()}
    base = paths["draft_case_checklist.prompt.md"].read_text(encoding="utf-8")
    supplement = paths["appworld_gpt56_draft_strict_v3.supplement.md"].read_text(encoding="utf-8")
    effective = minimal_drafter.compose_prompt(base, supplement)
    attachment = _input_file(_ATTACHMENT_PROMPT_PATH, "user-supplied draft prompt attachment")
    attachment_text = attachment.read_text(encoding="utf-8")
    _require(sha256_file(attachment) == EXPECTED_ATTACHMENT_PROMPT_SHA256, "user prompt attachment bytes drifted")
    normalize_whitespace = lambda value: re.sub(r"\s+", " ", value).strip()  # noqa: E731
    attachment_normalized = normalize_whitespace(attachment_text)
    base_normalized = normalize_whitespace(base)
    _require(attachment_normalized == base_normalized, "attachment differs from repository base beyond whitespace")
    return {
        "attachment_prompt_path": str(attachment),
        "attachment_prompt_sha256": sha256_file(attachment),
        "attachment_prompt_size_bytes": attachment.stat().st_size,
        "attachment_normalized_text_sha256": sha256_bytes(attachment_normalized.encode("utf-8")),
        "base_prompt_path": _repo_relative(paths["draft_case_checklist.prompt.md"]),
        "base_prompt_sha256": sha256_file(paths["draft_case_checklist.prompt.md"]),
        "base_prompt_size_bytes": paths["draft_case_checklist.prompt.md"].stat().st_size,
        "base_normalized_text_sha256": sha256_bytes(base_normalized.encode("utf-8")),
        "attachment_matches_base_after_whitespace_normalization": True,
        "attachment_is_byte_identical_to_base": sha256_file(attachment) == sha256_file(paths["draft_case_checklist.prompt.md"]),
        "supplement_path": _repo_relative(paths["appworld_gpt56_draft_strict_v3.supplement.md"]),
        "supplement_sha256": sha256_file(paths["appworld_gpt56_draft_strict_v3.supplement.md"]),
        "supplement_size_bytes": paths["appworld_gpt56_draft_strict_v3.supplement.md"].stat().st_size,
        "effective_composed_prompt_sha256": sha256_bytes(effective.encode("utf-8")),
        "effective_composed_prompt_size_bytes": len(effective.encode("utf-8")),
        "implementation_sha256": {key: sha256_file(path) for key, path in paths.items()},
    }


def _expected_codex_workspace_files(*, packet_path: Path) -> dict[str, str]:
    base = _input_file(
        _IMPLEMENTATION_PATHS["draft_case_checklist.prompt.md"],
        "base draft prompt",
    ).read_text(encoding="utf-8")
    supplement = _input_file(
        _IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"],
        "AppWorld draft prompt supplement",
    ).read_text(encoding="utf-8")
    template = _input_file(
        _IMPLEMENTATION_PATHS["case_checklist.template.yaml"],
        "checklist template",
    ).read_text(encoding="utf-8")
    full_schema = dict(
        _load_mapping(
            _IMPLEMENTATION_PATHS["case_checklist.schema.json"],
            "checklist schema",
        )
    )
    return minimal_drafter.build_codex_workspace_files(
        instructions=minimal_drafter.compose_prompt(base, supplement),
        template_text=template,
        case_packet_text=packet_path.read_text(encoding="utf-8"),
        model_output_schema=minimal_drafter.build_model_output_schema(full_schema),
    )


def _freeze_environment() -> dict[str, Any]:
    injected_name = "__CF_USER_TEXT_ENCODING"
    extra = set(os.environ) - set(_ENV_ALLOWLIST)
    _require(extra <= {injected_name}, f"lock builder rejects non-allowlisted environment variables: {sorted(extra)}")
    _require(set(_ENV_ALLOWLIST) <= set(os.environ), f"lock builder requires all explicit env -i variables: {list(_ENV_ALLOWLIST)}")
    injected = os.environ.get(injected_name)
    if injected is not None:
        _require(re.fullmatch(r"0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+:0x[0-9A-Fa-f]+", injected) is not None, "macOS-injected __CF_USER_TEXT_ENCODING has an invalid format")
    explicit = {name: os.environ[name] for name in _ENV_ALLOWLIST}
    _require(explicit == _APPROVED_ENV_VALUES, "formal env -i values differ from the exact approved runtime environment")
    _require(not any("API_KEY" in name or "TOKEN" in name for name in explicit), "provider key/token variables are forbidden")
    home = Path(explicit["HOME"])
    _require(home.is_absolute() and home.is_dir() and not home.is_symlink(), "HOME must be an absolute, real safe directory")
    _require(not any(home.iterdir()), "safe HOME must be empty at lock time")
    codex_home = Path(explicit["CODEX_HOME"])
    _require(codex_home.is_absolute() and codex_home.is_dir() and not codex_home.is_symlink(), "CODEX_HOME must be an absolute, real directory")
    hashes = {name: sha256_bytes(value.encode("utf-8")) for name, value in sorted(explicit.items())}
    return {
        "policy": ENVIRONMENT_POLICY,
        "env_command": "env -i",
        "allowlist": list(_ENV_ALLOWLIST),
        "explicit_variable_names": sorted(explicit),
        "value_sha256_by_name": hashes,
        "environment_semantic_sha256": sha256_object(hashes),
        "values_recorded": False,
        "provider_api_key_variables_allowed": False,
        "event_command_policy": EVENT_COMMAND_POLICY,
        "shell_toolchain": _current_shell_toolchain(),
        "platform_injected_variable": (
            {"name": injected_name, "value_sha256": sha256_bytes(injected.encode("utf-8"))}
            if injected is not None else None
        ),
    }


def _current_shell_toolchain() -> dict[str, Any]:
    script = (
        'print -r -- "PATH=$PATH"; '
        f'for x in {" ".join(_SHELL_TOOL_NAMES)}; do '
        'print -r -- "$x|$(whence -w $x)|$(whence -p $x)"; done'
    )
    probe = subprocess.run(
        ["/bin/zsh", "-lc", script],
        env=dict(_APPROVED_ENV_VALUES),
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    _require(probe.returncode == 0 and probe.stderr == "", "could not resolve exact zsh-login shell toolchain")
    lines = probe.stdout.splitlines()
    _require(len(lines) == 1 + len(_SHELL_TOOL_NAMES) and lines[0].startswith("PATH="), "zsh-login toolchain probe output drift")
    effective_path = lines[0].removeprefix("PATH=")
    executables: dict[str, dict[str, str]] = {}
    for expected_name, line in zip(_SHELL_TOOL_NAMES, lines[1:], strict=True):
        parts = line.split("|", 2)
        _require(len(parts) == 3 and parts[0] == expected_name, f"zsh-login toolchain probe identity drift: {expected_name}")
        name, classification, raw_path = parts
        _require(classification == f"{name}: command", f"zsh resolves {name} as a non-command shell object")
        path = _input_file(Path(raw_path).resolve(), f"effective zsh-login tool {name}")
        executables[name] = {
            "classification": classification,
            "path": str(path),
            "sha256": sha256_file(path),
        }
    zsh = _input_file(Path("/bin/zsh").resolve(), "zsh executable")
    startup_files: dict[str, dict[str, Any]] = {}
    for raw in (
        "/etc/zshenv", "/etc/zprofile", "/etc/zshrc", "/etc/zlogin",
        "/usr/libexec/path_helper", "/etc/paths",
    ):
        path = Path(raw)
        startup_files[raw] = (
            {"exists": True, "sha256": sha256_file(_input_file(path, f"zsh startup input {raw}"))}
            if path.exists()
            else {"exists": False, "sha256": None}
        )
    paths_d = _input_directory("/etc/paths.d", "zsh path_helper paths.d")
    _validate_no_symlinks(paths_d)
    paths_d_inventory = _strict_tree_inventory(paths_d)
    return {
        "zsh": {"path": str(zsh), "sha256": sha256_file(zsh)},
        "effective_path": effective_path,
        "effective_path_sha256": sha256_bytes(effective_path.encode("utf-8")),
        "executables": executables,
        "startup_files": startup_files,
        "paths_d": {
            "path": str(paths_d),
            "tree_sha256": sha256_path(paths_d),
            "strict_tree_sha256": paths_d_inventory["tree_sha256"],
            "file_count": paths_d_inventory["file_count"],
        },
    }


def _expected_batch_argv(*, packet_root: Path, cases_root: Path) -> list[str]:
    return [
        ".venv/bin/python",
        "neurips_ed_track_minimal/scripts/run_draft_batch.py",
        "--case-packet-root", _repo_relative(packet_root),
        "--output-root", _repo_relative(cases_root),
        "--provider", "codex",
        "--model", EXPECTED_MODEL,
        "--reasoning-effort", EXPECTED_REASONING_EFFORT,
        "--token-budgets", ",".join(str(value) for value in EXPECTED_TOKEN_BUDGETS),
        "--max-parallel", "8",
        "--large-max-parallel", "8",
        "--large-case-threshold-bytes", "100000",
        "--http-timeout-seconds", "180",
        "--large-http-timeout-seconds", "480",
        "--codex-timeout-seconds", "1800",
        "--large-codex-timeout-seconds", "3600",
        "--codex-sandbox", EXPECTED_CODEX_SANDBOX,
        "--prompt-supplement", _repo_relative(_IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"]),
        "--sort-by", "size",
        "--sleep-seconds", "2.0",
        "--quality-check", "none",
        "--appworld-v56-runtime-gate",
        "--fail-fast",
    ]


def _expected_canary_batch_argv(
    *, packet_root: Path, cases_root: Path, round_id: str
) -> list[str]:
    _require(round_id in EXPECTED_PREFLIGHT_ROUNDS, f"unknown canary round: {round_id}")
    return [
        *_expected_batch_argv(packet_root=packet_root, cases_root=cases_root),
        "--case-ids",
        ",".join(EXPECTED_PREFLIGHT_CASE_IDS),
        "--appworld-v56-canary-round",
        round_id,
    ]


def _phase_receipt_paths(*, run_kind: str, round_id: str | None) -> tuple[Path, Path]:
    _require(run_kind in {"formal", "canary"}, "phase run kind must be formal/canary")
    if run_kind == "formal":
        _require(round_id is None, "formal phase cannot name a canary round")
        stem = "phase_formal"
    else:
        _require(round_id in EXPECTED_PREFLIGHT_ROUNDS, "canary phase round is invalid")
        stem = f"phase_canary_{round_id}"
    provenance = resolve_repo_path(DEFAULT_DRAFT_ROOT / "provenance").resolve()
    return provenance / f"{stem}_start.json", provenance / f"{stem}_terminal.json"


def _expected_phase_argv(
    *, lock: Mapping[str, Any], run_kind: str, round_id: str | None
) -> list[str]:
    if run_kind == "formal":
        execution = _mapping(lock.get("execution"), "phase execution lock")
        return list(execution.get("command_argv") or [])
    rounds = {
        _string(_mapping(item, "phase canary round").get("round_id"), "phase canary round ID"):
        _mapping(item, "phase canary round")
        for item in _mapping(lock.get("preflight"), "phase canary plan").get("rounds", [])
        if isinstance(item, Mapping)
    }
    _require(round_id in rounds, f"phase canary round is not locked: {round_id}")
    return list(rounds[str(round_id)].get("command_argv") or [])


def _validate_phase_start_provenance_inventory(
    *, run_kind: str, round_id: str | None
) -> None:
    provenance = _input_directory(DEFAULT_DRAFT_ROOT / "provenance", "draft provenance")
    expected = {DEFAULT_LOCK_PATH.name}
    completed_rounds: Sequence[str]
    if run_kind == "canary":
        _require(round_id in EXPECTED_PREFLIGHT_ROUNDS, "canary phase round is invalid")
        completed_rounds = EXPECTED_PREFLIGHT_ROUNDS[
            : EXPECTED_PREFLIGHT_ROUNDS.index(str(round_id))
        ]
    else:
        completed_rounds = EXPECTED_PREFLIGHT_ROUNDS
    for completed_round in completed_rounds:
        start, terminal = _phase_receipt_paths(
            run_kind="canary", round_id=completed_round
        )
        expected.update(
            {
                start.name,
                terminal.name,
                _canary_round_receipt_path(completed_round).name,
            }
        )
    if run_kind == "formal":
        expected.add(DEFAULT_CANARY_ACCEPTANCE_PATH.name)
    actual = {path.name for path in provenance.iterdir()}
    _require(
        actual == expected
        and all(path.is_file() and not path.is_symlink() for path in provenance.iterdir()),
        f"{run_kind} phase-start provenance inventory is not exact",
    )
    _validate_draft_root_inventory(stage="phase_start")
    _validate_preflight_parent_inventory(completed_rounds=completed_rounds)


def _completed_phase_provenance_names() -> set[str]:
    names = {DEFAULT_LOCK_PATH.name, DEFAULT_CANARY_ACCEPTANCE_PATH.name}
    for round_id in EXPECTED_PREFLIGHT_ROUNDS:
        start, terminal = _phase_receipt_paths(run_kind="canary", round_id=round_id)
        names.update(
            {start.name, terminal.name, _canary_round_receipt_path(round_id).name}
        )
    formal_start, formal_terminal = _phase_receipt_paths(
        run_kind="formal", round_id=None
    )
    names.update({formal_start.name, formal_terminal.name})
    return names


def _validate_completed_provenance_inventory(*, final: bool) -> None:
    provenance = _input_directory(DEFAULT_DRAFT_ROOT / "provenance", "draft provenance")
    expected = _completed_phase_provenance_names()
    if final:
        expected.update(
            {
                DEFAULT_CORRECTIONS_PATH.name,
                DEFAULT_HASH_INDEX_PATH.name,
                DEFAULT_ACCEPTANCE_PATH.name,
                DEFAULT_FINAL_LOCK_PATH.name,
            }
        )
    actual_entries = list(provenance.iterdir())
    _require(
        {path.name for path in actual_entries} == expected
        and all(path.is_file() and not path.is_symlink() for path in actual_entries),
        "draft provenance inventory is not exact for the requested lifecycle stage",
    )
    _validate_preflight_parent_inventory(
        completed_rounds=EXPECTED_PREFLIGHT_ROUNDS
    )


def _validate_draft_root_inventory(*, stage: str) -> None:
    _require(
        stage in {"phase_start", "pre_acceptance", "final"},
        "unknown draft-root inventory stage",
    )
    root = _input_directory(DEFAULT_DRAFT_ROOT, "draft namespace root")
    expected = {"provenance"}
    if stage in {"pre_acceptance", "final"}:
        expected.add("cases")
        if (root / "quarantine").exists():
            expected.add("quarantine")
    if stage == "final":
        expected.add("accepted_cases")
    entries = list(root.iterdir())
    _require(
        {path.name for path in entries} == expected
        and all(path.is_dir() and not path.is_symlink() for path in entries),
        f"draft namespace top-level inventory is not exact at stage {stage}",
    )


def _validate_preflight_parent_inventory(
    *, completed_rounds: Sequence[str]
) -> None:
    expected = list(completed_rounds)
    _require(
        expected == list(EXPECTED_PREFLIGHT_ROUNDS[: len(expected)]),
        "preflight completed-round sequence is not a strict prefix",
    )
    root = resolve_repo_path(DEFAULT_PREFLIGHT_ROOT).resolve()
    if not expected:
        _require(
            not root.exists(),
            "fresh canary namespace already exists before round_01",
        )
        return
    preflight = _input_directory(root, "consecutive canary namespace")
    entries = list(preflight.iterdir())
    _require(
        {path.name for path in entries} == set(expected)
        and all(path.is_dir() and not path.is_symlink() for path in entries),
        "consecutive canary parent inventory is not exact",
    )
    for round_id in expected:
        round_root = _input_directory(preflight / round_id, f"{round_id} namespace")
        round_entries = list(round_root.iterdir())
        _require(
            {path.name for path in round_entries} == {"cases"}
            and round_entries[0].is_dir()
            and not round_entries[0].is_symlink(),
            f"{round_id} namespace contains an unexpected entry",
        )


def _validate_canary_acceptance_namespace(*, receipt_exists: bool) -> None:
    """Require the exact post-round namespace before/after sequence locking."""

    provenance = _input_directory(DEFAULT_DRAFT_ROOT / "provenance", "draft provenance")
    expected = {DEFAULT_LOCK_PATH.name}
    for round_id in EXPECTED_PREFLIGHT_ROUNDS:
        start, terminal = _phase_receipt_paths(
            run_kind="canary", round_id=round_id
        )
        expected.update(
            {
                start.name,
                terminal.name,
                _canary_round_receipt_path(round_id).name,
            }
        )
    if receipt_exists:
        expected.add(DEFAULT_CANARY_ACCEPTANCE_PATH.name)
    entries = list(provenance.iterdir())
    _require(
        {path.name for path in entries} == expected
        and all(path.is_file() and not path.is_symlink() for path in entries),
        "canary-acceptance provenance inventory is not exact",
    )
    _validate_draft_root_inventory(stage="phase_start")
    _validate_preflight_parent_inventory(
        completed_rounds=EXPECTED_PREFLIGHT_ROUNDS
    )


def _live_runtime() -> dict[str, Any]:
    executable = shutil.which("codex")
    _require(executable is not None, "Codex CLI is not on PATH")
    codex = _input_file(Path(executable).resolve(), "Codex executable")
    version = subprocess.run([str(codex), "--version"], capture_output=True, text=True, check=False)
    _require(version.returncode == 0, "could not query Codex CLI version")
    python_executable = _input_file(Path(sys.executable).resolve(), "Python executable")
    return {
        "python_executable": _repo_relative(python_executable),
        "python_executable_sha256": sha256_file(python_executable),
        "python_version": sys.version.split()[0],
        "pyyaml_version": importlib.metadata.version("PyYAML"),
        "jsonschema_version": importlib.metadata.version("jsonschema"),
        "requests_version": importlib.metadata.version("requests"),
        "uv_lock_path": "uv.lock",
        "uv_lock_sha256": sha256_file(_input_file("uv.lock", "uv lock")),
        "codex_executable": str(codex),
        "codex_cli_version": version.stdout.strip().removeprefix("codex-cli ").removeprefix("codex "),
        "codex_executable_sha256": sha256_file(codex),
    }


def _codex_login_status(codex_executable: str | Path | None = None) -> str:
    if codex_executable is None:
        resolved = shutil.which("codex")
        _require(resolved is not None, "Codex CLI is not on PATH for login-status verification")
        executable = _input_file(Path(resolved).resolve(), "Codex login-status executable")
    else:
        executable = _input_file(Path(codex_executable).resolve(), "Codex login-status executable")
    proc = subprocess.run([str(executable), "login", "status"], capture_output=True, text=True, check=False)
    _require(proc.returncode == 0, "could not query Codex login status")
    lines = [line.strip() for line in "\n".join((proc.stdout, proc.stderr)).splitlines() if line.strip()]
    _require(lines.count("Logged in using ChatGPT") == 1, f"unexpected Codex login status output: {lines!r}")
    _require(all(line == "Logged in using ChatGPT" or _CODEX_PATH_WARNING_RE.fullmatch(line) for line in lines), f"unrecognized Codex login diagnostic: {lines!r}")
    return "Logged in using ChatGPT"


def _git_commit() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root(), capture_output=True, text=True, check=False
    )
    _require(proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}\n?", proc.stdout) is not None, "could not freeze Git commit")
    return proc.stdout.strip()


def validate_appworld_draft_formal_run_v56(
    *,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
    cases_root: str | Path | None = None,
) -> dict[str, Any]:
    """Read-only validation of the immutable 485-case formal namespace."""

    _validate_draft_root_inventory(stage="pre_acceptance")
    _validate_completed_provenance_inventory(final=False)
    report, _ = _validate_formal_run_v56(lock_path=lock_path, cases_root=cases_root)
    return report


def _validate_preflight_root_legacy_v2(*, preflight_root: Path, packet_root: Path) -> dict[str, Any]:
    """Revalidate stable-root canaries; moved/stale sidecar pointers fail closed."""

    _validate_no_symlinks(preflight_root)
    entries = list(preflight_root.iterdir())
    _require({path.name for path in entries if path.is_dir()} == set(EXPECTED_PREFLIGHT_CASE_IDS), "preflight case set mismatch")
    _require(all(path.is_dir() and not path.is_symlink() for path in entries), "preflight root contains non-case entries")
    schema = _load_mapping(_IMPLEMENTATION_PATHS["case_checklist.schema.json"], "checklist schema")
    validator = Draft202012Validator(schema)
    base_prompt = _input_file(_IMPLEMENTATION_PATHS["draft_case_checklist.prompt.md"], "base draft prompt").read_text(encoding="utf-8")
    supplement = _input_file(_IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"], "draft prompt supplement").read_text(encoding="utf-8")
    effective_prompt = minimal_drafter.compose_prompt(base_prompt, supplement)
    template_text = _input_file(_IMPLEMENTATION_PATHS["case_checklist.template.yaml"], "checklist template").read_text(encoding="utf-8")
    manifest_by_id = {case["case_unit_id"]: case for case in _manifest_cases(_input_file(_INPUT_PATHS["manifest"], "manifest"))}
    records: list[dict[str, Any]] = []
    for case_id in EXPECTED_PREFLIGHT_CASE_IDS:
        case = manifest_by_id[case_id]
        case_dir = _input_directory(preflight_root / case_id, f"preflight case {case_id}")
        expected_files = {"api_response.json", "checklist.yaml", "llm_call.json", "reasoning_summary.txt"}
        if case_id == "476b213_2":
            expected_files.add("checklist.json")
        _require({path.name for path in case_dir.iterdir()} == expected_files, f"preflight file inventory mismatch: {case_id}")
        packet_dir = _input_directory(packet_root / case_id, f"packet {case_id}")
        packet = _input_file(packet_dir / "case_packet.md", f"packet {case_id}")
        raw_manifest = _load_mapping(packet_dir / "raw_case_manifest.json", f"raw manifest {case_id}")
        _validate_raw_source_hashes(packet_dir=packet_dir, raw_manifest=raw_manifest, case_id=case_id)
        checklist = _load_mapping(case_dir / "checklist.yaml", f"preflight checklist {case_id}")
        if case_id == "476b213_2":
            _require(checklist == _load_mapping(case_dir / "checklist.json", f"preflight checklist JSON {case_id}"), "fresh challenge canary YAML/JSON semantic mismatch")
        for key, expected in (("schema_version", "case_checklist_v1"), ("domain", "appworld"), ("case_unit_id", case_id), ("task_id", case_id)):
            _require(checklist.get(key) == expected, f"preflight checklist {key} mismatch: {case_id}")
        errors = list(validator.iter_errors(checklist))
        _require(not errors, f"preflight checklist schema failure: {case_id}")
        support_count = _validate_support(checklist=checklist, packet_path=packet, raw_manifest=raw_manifest, case_id=case_id)
        llm_call = _load_mapping(case_dir / "llm_call.json", f"preflight llm_call {case_id}")
        metadata = _mapping(llm_call.get("response_metadata"), f"preflight metadata {case_id}")
        _require(metadata.get("raw_api_response_path") == _repo_relative(case_dir / "api_response.json"), f"preflight raw-response path is stale/noncanonical: {case_id}")
        _require(metadata.get("reasoning_summary_path") == _repo_relative(case_dir / "reasoning_summary.txt"), f"preflight reasoning path is stale/noncanonical: {case_id}")
        timeout = 3600 if packet.stat().st_size > EXPECTED_LARGE_THRESHOLD_BYTES else 1800
        api_response = _load_mapping(case_dir / "api_response.json", f"preflight API {case_id}")
        usage, event_count, stderr_warning_count, read_audit = _validate_codex_sidecars(
            case_id=case_id, checklist=checklist, llm_call=llm_call,
            api_response=api_response,
            reasoning_summary=(case_dir / "reasoning_summary.txt").read_text(encoding="utf-8"),
            attempt_prefix="", attempt_record={"max_output_tokens": 12000, "codex_timeout_seconds": timeout},
            canonical_sidecar_paths=True,
            expected_workspace_files=_expected_codex_workspace_files(
                packet_path=packet
            ),
        )
        event_outputs = [
            str(item.get("aggregated_output") or "")
            for event in api_response["codex_cli"]["events"]
            if isinstance((item := event.get("item")), Mapping)
            and item.get("type") == "command_execution"
            and item.get("status") == "completed"
        ]
        _require(
            sum(effective_prompt in output and template_text in output for output in event_outputs) == 1,
            f"preflight event stream is not byte-bound to the effective prompt/template: {case_id}",
        )
        _validate_no_secret_material(list(case_dir.iterdir()), case_id=case_id)
        records.append({
            "case_unit_id": case_id, "dataset_name": case["dataset_name"],
            "case_packet_size_bytes": packet.stat().st_size, "case_tree_sha256": sha256_path(case_dir),
            "support_pointer_count": support_count, "command_event_count": event_count,
            "token_usage": usage,
            "codex_stderr_warning_count": stderr_warning_count,
            "workspace_read_audit_sha256": read_audit[
                "read_plan_semantic_sha256"
            ],
            "effective_prompt_event_sha256": sha256_bytes(effective_prompt.encode("utf-8")),
            "template_event_sha256": sha256_bytes(template_text.encode("utf-8")),
        })
    _require(sum(record["case_packet_size_bytes"] == 688300 for record in records) == 1, "preflight must contain the 688300-byte max oversized canary")
    return {
        "status": "passed", "case_ids": list(EXPECTED_PREFLIGHT_CASE_IDS),
        "case_count": 3, "tree_sha256": sha256_path(preflight_root), "records": records,
        "all_required_gates_passed": True,
    }


def _validate_preflight_resolution_legacy_v2(
    *, original_root: Path, stable_root: Path, fresh_challenge_root: Path, manifest_path: Path
) -> dict[str, Any]:
    """Verify one fresh challenge replacement plus two metadata-only rebases."""

    for root in (original_root, stable_root, fresh_challenge_root):
        _validate_no_symlinks(root)
    _require(sha256_path(original_root) == EXPECTED_PREFLIGHT_ORIGINAL_TREE_SHA256, "original preflight tree drift")
    _require(sha256_path(stable_root) == EXPECTED_PREFLIGHT_TREE_SHA256, "stable preflight tree drift")
    _require(sha256_path(fresh_challenge_root) == EXPECTED_PREFLIGHT_FRESH_CHALLENGE_TREE_SHA256, "fresh challenge source tree drift")
    _require(sha256_file(manifest_path) == EXPECTED_PREFLIGHT_RESOLUTION_SHA256, "preflight resolution manifest drift")
    manifest = _load_mapping(manifest_path, "preflight resolution manifest")
    _require(set(manifest) == {
        "schema_version", "created_at", "reason", "policy", "original_snapshot",
        "fresh_challenge_source_snapshot", "stable_snapshot", "fresh_replacement",
        "metadata_rebases",
    }, "preflight resolution manifest field set drift")
    _require(manifest.get("schema_version") == "appworld_draft_preflight_resolution.v2", "preflight resolution schema drift")
    _parse_timestamp(manifest.get("created_at"), "preflight resolution created_at")
    _string(manifest.get("reason"), "preflight resolution reason")
    expected_policy = {
        "hard_gate_downgraded": False, "stable_preflight_must_pass_all_gates": True,
        "source_snapshots_preserved": True, "fresh_replacement_case_count": 1,
        "metadata_rebase_case_count": 2, "metadata_json_value_change_count": 4,
        "original_to_stable_modified_file_count": 5,
        "original_to_stable_added_file_count": 1,
        "original_to_stable_removed_file_count": 0,
        "original_to_stable_unchanged_file_count": 7,
    }
    _require(dict(_mapping(manifest.get("policy"), "resolution policy")) == expected_policy, "preflight resolution policy drift")
    _require(manifest.get("original_snapshot") == {
        "root": _repo_relative(original_root), "tree_sha256": EXPECTED_PREFLIGHT_ORIGINAL_TREE_SHA256,
    }, "resolution original snapshot binding drift")
    _require(manifest.get("stable_snapshot") == {
        "root": _repo_relative(stable_root), "tree_sha256": EXPECTED_PREFLIGHT_TREE_SHA256,
        "authoritative": True,
    }, "resolution stable snapshot binding drift")

    source_case = _input_directory(fresh_challenge_root / "476b213_2", "fresh challenge source case")
    stable_case = _input_directory(stable_root / "476b213_2", "stable challenge canary")
    original_case = _input_directory(original_root / "476b213_2", "original challenge canary")
    source_case_hash = sha256_path(source_case)
    stable_case_hash = sha256_path(stable_case)
    source_ref = _mapping(manifest.get("fresh_challenge_source_snapshot"), "fresh challenge source snapshot")
    _require(dict(source_ref) == {
        "root": _repo_relative(fresh_challenge_root),
        "tree_sha256": EXPECTED_PREFLIGHT_FRESH_CHALLENGE_TREE_SHA256,
        "case_unit_id": "476b213_2", "case_tree_sha256": source_case_hash,
        "file_count": 5, "completed_before_batch_rejection": True,
        "authoritative_source_for_case": True,
    }, "fresh challenge source binding drift")
    replacement = _mapping(manifest.get("fresh_replacement"), "fresh replacement")
    replacement_keys = {
        "case_unit_id", "dataset_name", "original_case_tree_sha256",
        "source_case_tree_sha256", "stable_case_tree_sha256",
        "source_and_stable_byte_identical", "original_disqualification",
        "required_fresh_gates", "all_required_fresh_gates_passed", "file_sha256",
    }
    _require(set(replacement) == replacement_keys, "fresh replacement field set drift")
    _require(replacement.get("case_unit_id") == "476b213_2" and replacement.get("dataset_name") == "test_challenge", "fresh replacement identity drift")
    _require(replacement.get("original_case_tree_sha256") == sha256_path(original_case), "fresh replacement original hash drift")
    _require(replacement.get("source_case_tree_sha256") == source_case_hash == stable_case_hash == replacement.get("stable_case_tree_sha256"), "fresh/stable challenge case hash drift")
    _require(replacement.get("source_and_stable_byte_identical") is True, "fresh challenge source is not byte-identical to stable")
    _require(replacement.get("original_disqualification") == {
        "policy": EVENT_COMMAND_POLICY,
        "reason": "workspace_external_interpreter_read_attempt",
        "executables": ["python", "python3"], "terminal_exit_codes": [127, 1],
    }, "original challenge disqualification drift")
    _require(replacement.get("required_fresh_gates") == [
        "identity", "schema", "yaml_json_semantic_equality", "official_source_hashes",
        "source_local_support_locations", "model_auth_reasoning",
        "successful_codex_event_stream", "nonzero_token_usage",
        "event_command_confinement", "secret_scan",
    ] and replacement.get("all_required_fresh_gates_passed") is True, "fresh challenge gate declaration drift")
    source_files = {path.name: sha256_file(path) for path in source_case.iterdir() if path.is_file()}
    _require(replacement.get("file_sha256") == source_files and len(source_files) == 5, "fresh challenge file hash inventory drift")
    _require(source_case_hash == stable_case_hash, "stable challenge canary differs from preserved fresh source")

    raw_rebases = manifest.get("metadata_rebases")
    _require(isinstance(raw_rebases, list) and len(raw_rebases) == 2, "metadata rebases must contain exactly two normal cases")
    rebase_ids = ["d18139b_3", "dac78d9_3"]
    _require([_mapping(value, "metadata rebase").get("case_unit_id") for value in raw_rebases] == rebase_ids, "metadata rebase order/set drift")
    rebase_audits: list[dict[str, str]] = []
    for case_id, raw in zip(rebase_ids, raw_rebases, strict=True):
        entry = _mapping(raw, f"metadata rebase {case_id}")
        _require(set(entry) == {"case_unit_id", "path", "before_sha256", "after_sha256", "changes"}, f"metadata rebase fields drift: {case_id}")
        relative = f"{case_id}/llm_call.json"
        before_file = _input_file(original_root / relative, f"original llm_call {case_id}")
        after_file = _input_file(stable_root / relative, f"stable llm_call {case_id}")
        _require(entry.get("path") == relative and entry.get("before_sha256") == sha256_file(before_file) and entry.get("after_sha256") == sha256_file(after_file), f"metadata rebase file binding drift: {case_id}")
        before_api = f"experiments/appworld_full_test_extension_v1/draft_runs/codex-gpt-5.6-sol-xhigh-support-v2/preflight/{case_id}/api_response.json"
        before_reasoning = before_api.removesuffix("api_response.json") + "reasoning_summary.txt"
        after_api = _repo_relative(stable_root / case_id / "api_response.json")
        after_reasoning = _repo_relative(stable_root / case_id / "reasoning_summary.txt")
        expected_changes = [
            {"json_path": "response_metadata.raw_api_response_path", "before": before_api, "after": after_api},
            {"json_path": "response_metadata.reasoning_summary_path", "before": before_reasoning, "after": after_reasoning},
        ]
        _require(entry.get("changes") == expected_changes, f"metadata rebase value ledger drift: {case_id}")
        before = _load_mapping(before_file, f"original llm_call {case_id}")
        after = _load_mapping(after_file, f"stable llm_call {case_id}")
        normalized = json.loads(json.dumps(before))
        normalized["response_metadata"]["raw_api_response_path"] = after_api
        normalized["response_metadata"]["reasoning_summary_path"] = after_reasoning
        _require(normalized == after, f"metadata rebase changed more than two path values: {case_id}")
        for filename in ("api_response.json", "checklist.yaml", "reasoning_summary.txt"):
            _require(sha256_file(_input_file(original_root / case_id / filename, "original normal canary file")) == sha256_file(_input_file(stable_root / case_id / filename, "stable normal canary file")), f"metadata rebase changed forbidden file: {case_id}/{filename}")
        rebase_audits.append({"case_unit_id": case_id, "before_sha256": sha256_file(before_file), "after_sha256": sha256_file(after_file)})

    original_files = _relative_file_hashes(original_root)
    stable_files = _relative_file_hashes(stable_root)
    added = sorted(set(stable_files) - set(original_files))
    removed = sorted(set(original_files) - set(stable_files))
    modified = sorted(path for path in set(original_files) & set(stable_files) if original_files[path] != stable_files[path])
    unchanged = sorted(path for path in set(original_files) & set(stable_files) if original_files[path] == stable_files[path])
    _require(added == ["476b213_2/checklist.json"] and removed == [], "preflight resolution added/removed file set drift")
    _require(modified == sorted([
        "476b213_2/api_response.json", "476b213_2/checklist.yaml", "476b213_2/llm_call.json",
        "d18139b_3/llm_call.json", "dac78d9_3/llm_call.json",
    ]), "preflight resolution modified-file set drift")
    _require(len(unchanged) == 7, "preflight resolution unchanged-file count drift")
    return {
        "status": "verified_preflight_resolution_v2",
        "manifest_sha256": sha256_file(manifest_path),
        "original_tree_sha256": sha256_path(original_root),
        "fresh_challenge_source_tree_sha256": sha256_path(fresh_challenge_root),
        "stable_tree_sha256": sha256_path(stable_root),
        "fresh_replacement_case_id": "476b213_2",
        "fresh_replacement_case_tree_sha256": stable_case_hash,
        "metadata_rebase_case_ids": rebase_ids,
        "metadata_rebases": rebase_audits,
        "hard_gate_downgraded": False,
    }


def _relative_file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in root.rglob("*") if path.is_file() and not path.is_symlink()
    }


def _validate_formal_run_v56(
    *,
    lock_path: str | Path,
    cases_root: str | Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    lock_file = _input_file(lock_path, "v4 pre-run lock")
    _require(
        lock_file == resolve_repo_path(DEFAULT_LOCK_PATH).resolve(),
        "formal validation lock path is noncanonical",
    )
    lock = _load_mapping(lock_file, "v4 pre-run lock")
    lock_audit = _validate_lock_v56(lock_file, lock)
    cases, input_audit = _validate_locked_inputs_v56(lock)
    canary_acceptance = validate_appworld_v56_canary_acceptance()
    locked_root = resolve_repo_path(_string(_mapping(lock.get("execution"), "execution").get("output_root"), "execution.output_root")).resolve()
    formal_root = resolve_repo_path(cases_root).resolve() if cases_root is not None else locked_root
    _require(formal_root == locked_root, "formal cases root differs from the v4 pre-run lock")
    formal_root = _input_directory(formal_root, "formal cases root")
    _validate_no_symlinks(formal_root)
    batch, rows = _validate_batch(formal_root=formal_root, cases=cases, lock=lock)

    packet_root = _input_directory(_mapping(lock.get("inputs"), "inputs")["case_packet_root"], "packet root")
    quarantine_root = resolve_repo_path(
        _string(_mapping(lock.get("execution"), "execution").get("quarantine_root"), "execution.quarantine_root")
    ).resolve()
    rows_by_id = {str(row["case_unit_dir"]): row for row in rows}
    case_entries: list[dict[str, Any]] = []
    token_usage = Counter()
    command_event_count = 0
    successful_attempt_counts: Counter[int] = Counter()
    for case in cases:
        case_id = case["case_unit_id"]
        entry, usage, event_count = _validate_case(
            case=case,
            case_dir=formal_root / case_id,
            packet_dir=packet_root / case_id,
            result_row=rows_by_id[case_id],
            quarantine_root=quarantine_root,
        )
        case_entries.append(entry)
        token_usage.update(usage)
        command_event_count += event_count
        successful_attempt_counts[entry["successful_attempt_index"]] += 1

    batch_started = _utc_timestamp(batch["started_at"], "formal batch started_at")
    batch_updated = _utc_timestamp(batch["updated_at"], "formal batch updated_at")
    available_call_window_count = 0
    unavailable_call_window_count = 0
    for entry in case_entries:
        for window in entry["attempt_call_windows"]:
            if window["request_timestamp"] is None:
                unavailable_call_window_count += 1
                continue
            requested = _utc_timestamp(
                window["request_timestamp"],
                f"formal request {entry['case_unit_id']}/{window['attempt_index']}",
            )
            responded = _utc_timestamp(
                window["response_timestamp"],
                f"formal response {entry['case_unit_id']}/{window['attempt_index']}",
            )
            _require(
                batch_started <= requested <= responded <= batch_updated,
                f"formal call lies outside its immutable batch window: {entry['case_unit_id']}/{window['attempt_index']}",
            )
            available_call_window_count += 1

    rejected_attempt_count = sum(entry["quarantined_attempt_count"] for entry in case_entries)
    _require(rejected_attempt_count == batch["rejected_attempt_count"], "case/quarantine rejected-attempt count mismatch")
    quarantined_case_ids = sorted(
        entry["case_unit_id"] for entry in case_entries if entry["quarantined_attempt_count"]
    )
    if rejected_attempt_count:
        quarantine_root = _input_directory(quarantine_root, "formal quarantine root")
        _validate_no_symlinks(quarantine_root)
        quarantine_entries = list(quarantine_root.iterdir())
        _require(
            all(path.is_dir() and not path.is_symlink() for path in quarantine_entries),
            "formal quarantine root may contain only case directories",
        )
        _require(
            sorted(path.name for path in quarantine_entries) == quarantined_case_ids,
            "formal quarantine case directory set mismatch",
        )
        _require(not _secret_scan_tree(quarantine_root), "formal quarantine tree contains secret-like material")
        quarantine_inventory = _strict_tree_inventory(quarantine_root)
        quarantine_audit = {
            "root": _repo_relative(quarantine_root),
            "exists": True,
            "tree_sha256": sha256_path(quarantine_root),
            "strict_tree_sha256": quarantine_inventory["tree_sha256"],
            "file_count": quarantine_inventory["file_count"],
            "directory_count": quarantine_inventory["directory_count"],
            "size_bytes": quarantine_inventory["size_bytes"],
            "case_count": len(quarantined_case_ids),
            "case_ids": quarantined_case_ids,
            "rejected_attempt_count": rejected_attempt_count,
        }
    else:
        _require(not quarantine_root.exists(), "quarantine root exists even though no attempt was rejected")
        quarantine_audit = {
            "root": _repo_relative(quarantine_root),
            "exists": False,
            "tree_sha256": None,
            "strict_tree_sha256": None,
            "file_count": 0,
            "directory_count": 0,
            "size_bytes": 0,
            "case_count": 0,
            "case_ids": [],
            "rejected_attempt_count": 0,
        }

    promoted_attempt_api_paths = sorted(formal_root.glob("*/attempt_*.api_response.json"))
    _require(
        len(promoted_attempt_api_paths) == EXPECTED_EXTENSION_COUNT,
        "formal promoted-attempt API-response count drift",
    )
    quarantined_attempt_with_api_count = sum(
        1
        for case_entry in case_entries
        for attempt in case_entry["quarantined_attempts"]
        if f"attempt_{attempt['attempt_index']:02d}.api_response.json"
        in attempt["entry_names"]
    )
    _require(
        available_call_window_count
        == EXPECTED_EXTENSION_COUNT + rejected_attempt_count
        and quarantined_attempt_with_api_count == rejected_attempt_count
        and unavailable_call_window_count == 0,
        "formal attempt call-window availability does not match quarantine API stages",
    )
    quarantined_attempt_api_paths = (
        sorted(quarantine_root.glob("*/attempt_*.api_response.json"))
        if quarantine_root.exists()
        else []
    )
    _require(
        len(quarantined_attempt_api_paths) == quarantined_attempt_with_api_count,
        "formal quarantined-attempt API-response count differs from its ledgers",
    )
    formal_attempt_api_paths = promoted_attempt_api_paths + quarantined_attempt_api_paths
    formal_response_ids = [
        _string(_load_mapping(path, f"formal attempt API {path.name}").get("id"), f"formal response ID {path.name}")
        for path in formal_attempt_api_paths
    ]
    _require(
        len(formal_response_ids)
        == EXPECTED_EXTENSION_COUNT + quarantined_attempt_with_api_count,
        "formal API-bearing logical-attempt response-ID count drift",
    )
    _require(len(set(formal_response_ids)) == len(formal_response_ids), "formal attempt response IDs are not globally unique")
    _require(set(formal_response_ids).isdisjoint(set(canary_acceptance["response_ids"])), "formal run reuses a canary response ID")
    _require(
        set(formal_response_ids).isdisjoint(_failed_response_ids()),
        "formal run reuses a failed diagnostic response ID",
    )

    secret_findings = _secret_scan_tree(formal_root)
    _require(not secret_findings, "formal cases tree contains secret-like material")
    inventory = _strict_tree_inventory(formal_root)
    validator_hashes = _acceptance_validator_hashes()
    hash_index = {
        "schema_version": HASH_INDEX_SCHEMA,
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "pre_run_lock": {"path": _repo_relative(lock_file), "sha256": sha256_file(lock_file)},
        "canary_acceptance": {
            "path": canary_acceptance["receipt_path"],
            "sha256": canary_acceptance["receipt_sha256"],
            "round_count": canary_acceptance["round_count"],
            "first_attempt_pass_count": canary_acceptance["first_attempt_pass_count"],
        },
        "formal_cases": {
            "root": _repo_relative(formal_root),
            "tree_sha256": sha256_path(formal_root),
            "strict_tree_sha256": inventory["tree_sha256"],
            "file_count": inventory["file_count"],
            "directory_count": inventory["directory_count"],
            "size_bytes": inventory["size_bytes"],
        },
        "batch": batch,
        "quarantine": quarantine_audit,
        "case_count": EXPECTED_EXTENSION_COUNT,
        "case_count_by_dataset": {
            "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
            "test_challenge": EXPECTED_CHALLENGE_COUNT,
        },
        "acceptance_validator": validator_hashes,
        "cases": case_entries,
        "formal_response_ids_semantic_sha256": sha256_object(formal_response_ids),
        "formal_response_id_count": len(formal_response_ids),
        "quarantined_attempt_with_api_response_count": quarantined_attempt_with_api_count,
        "available_call_window_count": available_call_window_count,
        "unavailable_pre_api_call_window_count": unavailable_call_window_count,
    }
    report = {
        "schema_version": ACCEPTANCE_SCHEMA,
        "status": "formal_validated",
        "draft_lifecycle_status": LIFECYCLE,
        "human_review_completed": False,
        "all_promoted_draft_hard_gates_passed": True,
        "lock": lock_audit,
        "inputs": input_audit,
        "canary_acceptance": hash_index["canary_acceptance"],
        "formal_cases": hash_index["formal_cases"],
        "quarantine": quarantine_audit,
        "batch": batch,
        "drafts": {
            "case_count": EXPECTED_EXTENSION_COUNT,
            "case_count_by_dataset": hash_index["case_count_by_dataset"],
            "successful_attempt_index_counts": {
                str(key): value for key, value in sorted(successful_attempt_counts.items())
            },
            "token_usage": dict(sorted(token_usage.items())),
            "codex_command_event_count": command_event_count,
            "event_command_policy": EVENT_COMMAND_POLICY,
            "promoted_attempts_all_runtime_policy_passed": True,
            "promoted_attempt_count": 485,
            "rejected_attempt_count": rejected_attempt_count,
            "rejected_attempt_with_api_response_count": quarantined_attempt_with_api_count,
            "available_call_window_count": available_call_window_count,
            "unavailable_pre_api_call_window_count": unavailable_call_window_count,
            "rejected_attempt_policy_failure_count": batch["runtime_policy_gate_counts"]["failed"],
            "rejected_attempt_policy_not_run_count": batch["runtime_policy_gate_counts"]["not_run"],
        },
        "security": {
            "scanner_schema": "appworld_draft_secret_scan_expanded.v1",
            "finding_count": 0,
            "credential_values_recorded": False,
            "promoted_attempt_policy_violation_count": 0,
            "rejected_attempt_policy_violation_count": batch["runtime_policy_gate_counts"]["failed"],
        },
        "acceptance_validator": validator_hashes,
        "draft_hash_index_content_sha256": sha256_object(hash_index),
        "artifacts_written": False,
    }
    return report, hash_index


def _validate_lock_v56(lock_file: Path, lock: Mapping[str, Any]) -> dict[str, Any]:
    expected_top = {
        "schema_version", "status", "locked_at", "experiment_id", "draft_run_id",
        "authorization", "scope_deviation", "repository", "inputs", "preflight",
        "prompt", "runtime", "environment", "drafter", "execution", "acceptance",
    }
    _require(set(lock) == expected_top, "v4 pre-run lock top-level field set drift")
    _require(lock.get("schema_version") == LOCK_SCHEMA, f"pre-run lock schema must be {LOCK_SCHEMA}")
    _require(lock.get("status") == "locked_pre_run", "pre-run lock status drift")
    _require(lock.get("experiment_id") == EXPECTED_EXPERIMENT_ID, "experiment ID drift")
    _require(lock.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID, "draft run ID drift")
    _parse_timestamp(lock.get("locked_at"), "locked_at")
    authorization = _mapping(lock.get("authorization"), "authorization")
    _require(dict(authorization) == {
        "requested_by_user": True,
        "external_case_packet_transfer_approved": True,
        "approved_case_count": 485,
        "approved_concurrency": 8,
        "provider_model_reasoning": "Codex CLI ChatGPT login / gpt-5.6-sol / xhigh",
    }, "user authorization scope drift")
    scope = _mapping(lock.get("scope_deviation"), "scope_deviation")
    _require(dict(scope) == {
        "estimand": "68 test_normal extension plus 417 test_challenge cases",
        "authorized_scope_lock_sha256": EXPECTED_FROZEN_SCOPE_SHA256,
        "new_namespace_required": True,
        "predecessor_snapshot": {
            "failed_v2": _failed_v2_snapshot_audit(),
            "failed_v3_canary": _failed_v3_canary_snapshot_audit(),
            "failed_v3_guardrail": _failed_v3_guardrail_snapshot_audit(),
            "failed_v4_formal": _failed_v4_formal_snapshot_audit(),
            "failed_v5_canary": _failed_v5_canary_snapshot_audit(),
        },
        "predecessor_artifact_reuse_allowed": False,
        "formal_repairs_allowed": False,
    }, "scope deviation drift")

    repository = _mapping(lock.get("repository"), "repository")
    _require(set(repository) == {"base_commit", "reproducibility_rule"}, "repository lock field set drift")
    _require(re.fullmatch(r"[0-9a-f]{40}", str(repository.get("base_commit") or "")) is not None, "base commit is not frozen")
    _require(repository.get("base_commit") == _git_commit(), "repository HEAD drifted after pre-run lock")
    _require("SHA-256" in _string(repository.get("reproducibility_rule"), "reproducibility rule"), "reproducibility rule drift")

    preflight = _mapping(lock.get("preflight"), "preflight")
    packet_root = _input_directory(
        _string(_mapping(lock.get("inputs"), "inputs").get("case_packet_root"), "inputs.case_packet_root"),
        "packet root",
    )
    current_cases = _manifest_cases(_input_file(_INPUT_PATHS["manifest"], "extension manifest"))
    _require(
        dict(preflight) == _locked_canary_plan(cases=current_cases, packet_root=packet_root),
        "locked three-round canary plan drift",
    )

    prompt = _mapping(lock.get("prompt"), "prompt")
    _require(dict(prompt) == _freeze_prompt(), "prompt/implementation hashes drifted from the pre-run lock")
    runtime = _mapping(lock.get("runtime"), "runtime")
    _require(set(runtime) == {
        "python_executable", "python_executable_sha256", "python_version",
        "pyyaml_version", "jsonschema_version", "requests_version",
        "uv_lock_path", "uv_lock_sha256", "codex_executable",
        "codex_cli_version", "codex_executable_sha256",
        "login_status_at_lock", "auth_mode",
    }, "runtime lock field set drift")
    _require(runtime.get("auth_mode") == "codex_login" and runtime.get("login_status_at_lock") == "Logged in using ChatGPT", "Codex login lock drift")
    _require(runtime.get("python_version") == sys.version.split()[0], "Python version drift")
    _require(runtime.get("pyyaml_version") == importlib.metadata.version("PyYAML"), "PyYAML version drift")
    _require(runtime.get("jsonschema_version") == importlib.metadata.version("jsonschema"), "jsonschema version drift")
    _require(runtime.get("requests_version") == importlib.metadata.version("requests"), "requests version drift")
    _require(sha256_file(_input_file(runtime.get("codex_executable"), "locked Codex executable")) == runtime.get("codex_executable_sha256"), "Codex executable hash drift")
    _require(sha256_file(_input_file(runtime.get("python_executable"), "locked Python executable")) == runtime.get("python_executable_sha256"), "Python executable hash drift")
    current_codex = shutil.which("codex")
    _require(current_codex is not None and Path(current_codex).resolve() == Path(_string(runtime.get("codex_executable"), "locked Codex executable")).resolve(), "current PATH resolves Codex to a different executable than the lock")
    _require(Path(sys.executable).resolve() == Path(_string(runtime.get("python_executable"), "locked Python executable")).resolve(), "current Python executable differs from the lock")
    _require(sha256_file(_input_file(runtime.get("uv_lock_path"), "locked uv.lock")) == runtime.get("uv_lock_sha256"), "uv.lock hash drift")

    environment = _mapping(lock.get("environment"), "environment")
    _require(set(environment) == {
        "policy", "env_command", "allowlist", "explicit_variable_names",
        "value_sha256_by_name", "environment_semantic_sha256", "values_recorded",
        "provider_api_key_variables_allowed", "event_command_policy",
        "platform_injected_variable", "shell_toolchain",
    }, "environment lock field set drift")
    _require(environment.get("policy") == ENVIRONMENT_POLICY, "environment policy drift")
    _require(environment.get("allowlist") == list(_ENV_ALLOWLIST), "environment allowlist drift")
    names = environment.get("explicit_variable_names")
    _require(names == sorted(_ENV_ALLOWLIST), "formal environment variable set must be the exact allowlist")
    hashes = _mapping(environment.get("value_sha256_by_name"), "environment value hashes")
    _require(set(hashes) == set(_ENV_ALLOWLIST), "formal environment value-hash set drift")
    _require(all(re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in hashes.values()), "invalid environment value hash")
    _require(environment.get("environment_semantic_sha256") == sha256_object(dict(sorted(hashes.items()))), "environment semantic hash drift")
    approved_hashes = {name: sha256_bytes(value.encode("utf-8")) for name, value in sorted(_APPROVED_ENV_VALUES.items())}
    _require(dict(hashes) == approved_hashes, "formal environment values are not the exact approved values")
    _require(environment.get("values_recorded") is False and environment.get("provider_api_key_variables_allowed") is False, "environment secret policy drift")
    _require(environment.get("event_command_policy") == EVENT_COMMAND_POLICY, "event command policy drift")
    _require(environment.get("shell_toolchain") == _current_shell_toolchain(), "frozen read-only shell toolchain path/hash drift")
    injected = environment.get("platform_injected_variable")
    if injected is not None:
        injected_map = _mapping(injected, "platform injected variable")
        _require(set(injected_map) == {"name", "value_sha256"}, "platform injected variable field set drift")
        _require(injected_map.get("name") == "__CF_USER_TEXT_ENCODING", "unknown platform-injected variable")
        _require(re.fullmatch(r"[0-9a-f]{64}", str(injected_map.get("value_sha256") or "")) is not None, "platform injected variable hash invalid")
        current = os.environ.get("__CF_USER_TEXT_ENCODING")
        exact_explicit_environment = all(os.environ.get(name) == value for name, value in _APPROVED_ENV_VALUES.items())
        no_unexpected_environment = (set(os.environ) - set(_ENV_ALLOWLIST)) <= {"__CF_USER_TEXT_ENCODING"}
        if exact_explicit_environment and no_unexpected_environment and current is not None:
            _require(injected_map.get("value_sha256") == sha256_bytes(current.encode("utf-8")), "platform injected variable value drift under env-i validation")

    drafter = _mapping(lock.get("drafter"), "drafter")
    expected_drafter = {
        "provider": "codex", "llm_call_provider": "codex_cli", "auth_mode": "codex_login",
        "requested_model_alias": EXPECTED_MODEL, "backend_model_revision": None,
        "reasoning_effort": EXPECTED_REASONING_EFFORT, "model_verbosity": EXPECTED_MODEL_VERBOSITY,
        "temperature_recorded": 0.0, "temperature_enforced": False, "codex_sandbox": EXPECTED_CODEX_SANDBOX,
        "max_output_token_budgets": list(EXPECTED_TOKEN_BUDGETS), "max_output_tokens_enforced": False,
        "regular_codex_timeout_seconds": 1800, "oversized_codex_timeout_seconds": 3600,
        "regular_http_timeout_seconds": 180, "oversized_http_timeout_seconds": 480,
        "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
        "regular_max_parallel": 8, "oversized_max_parallel": 8,
        "lane_execution": "regular then oversized", "sort_by": "size", "quality_check": "none",
        "pre_promotion_runtime_gate": RUNTIME_GATE_SCHEMA,
        "appworld_semantic_gate": "appworld_checklist_evaluator_semantics.v1",
        "resume_allowed": False, "skipped_existing_allowed": False,
        "interruption_or_any_final_failure_invalidates_namespace": True,
        "retry_rule": (
            "Retry only after an auditable, allowlisted Codex infrastructure failure "
            "that produced no agent_message; checklist-validator, AppWorld semantic, "
            "and runtime/tool-policy failures invalidate the case and namespace. "
            "Quarantine every rejected attempt and promote only the first fully passing "
            "attempt after an infrastructure-only retry."
        ),
    }
    _require(dict(drafter) == expected_drafter, "drafter configuration drift (including mandatory 8/8 concurrency)")
    execution = _mapping(lock.get("execution"), "execution")
    _require(set(execution) == {
        "output_root", "quarantine_root", "pre_run_output_root_exists", "pre_run_output_entry_count",
        "pre_run_quarantine_root_exists",
        "environment_policy", "command_argv", "command_semantic_sha256",
        "canary_acceptance_path", "canary_acceptance_required",
    }, "execution lock field set drift")
    locked_root = resolve_repo_path(_string(execution.get("output_root"), "execution.output_root")).resolve()
    locked_quarantine = resolve_repo_path(_string(execution.get("quarantine_root"), "execution.quarantine_root")).resolve()
    _require(locked_quarantine == locked_root.parent / "quarantine", "formal quarantine root is not the required output-root sibling")
    expected_argv = _expected_batch_argv(packet_root=resolve_repo_path(_mapping(lock.get("inputs"), "inputs")["case_packet_root"]).resolve(), cases_root=locked_root)
    _require(execution.get("command_argv") == expected_argv, "batch execution argv drift")
    python_launcher = _input_file(resolve_repo_path(expected_argv[0]).resolve(), "formal Python launcher")
    _require(python_launcher == Path(_string(runtime.get("python_executable"), "locked Python executable")).resolve(), "formal argv Python launcher differs from locked Python executable")
    _require(execution.get("command_semantic_sha256") == sha256_object(expected_argv), "batch argv hash drift")
    _require(execution.get("environment_policy") == ENVIRONMENT_POLICY, "execution environment policy drift")
    _require(
        resolve_repo_path(_string(execution.get("canary_acceptance_path"), "canary acceptance path")).resolve()
        == resolve_repo_path(DEFAULT_CANARY_ACCEPTANCE_PATH).resolve()
        and execution.get("canary_acceptance_required") is True,
        "formal canary-acceptance binding drift",
    )
    _require(
        execution.get("pre_run_output_root_exists") is False
        and execution.get("pre_run_output_entry_count") == 0
        and execution.get("pre_run_quarantine_root_exists") is False,
        "clean formal/quarantine namespaces were not frozen",
    )
    acceptance = _mapping(lock.get("acceptance"), "acceptance")
    _require(set(acceptance) == {
        "required_case_count", "required_case_count_by_dataset", "required_lane_counts",
        "required_schema", "required_identity_match", "required_final_status",
        "formal_repairs_allowed", "correction_count",
        "require_exact_case_directory_set", "require_exact_final_seven_file_bundle",
        "require_final_bundle_matches_one_successful_attempt", "require_yaml_json_semantic_equality",
        "require_runtime_policy_gate_before_promotion", "require_rejected_attempt_quarantine",
        "require_accepted_tree_excludes_rejected_attempts",
        "require_json_schema_validation", "require_strict_guardrail_validation",
        "require_support_pointer_locations_resolvable", "require_official_source_hash_match",
        "require_codex_login_provenance", "require_provider_model_reasoning_match",
        "require_successful_codex_event_stream", "require_nonzero_token_usage",
        "require_promoted_event_command_confinement", "require_rejected_attempt_policy_evidence",
        "require_rejected_attempts_infra_only",
        "require_no_environment_enumeration",
        "require_no_symlinks", "require_no_secret_material",
        "require_identity_accepted_materialization", "require_hash_lock_after_validation",
        "require_three_consecutive_canary_rounds", "require_canary_acceptance_before_formal",
        "require_appworld_evaluator_composition_gate", "require_non_scoring_dynamic_fields_excluded",
        "require_failed_v2_snapshot_not_reused",
        "require_failed_v3_canary_snapshot_not_reused",
        "require_failed_v3_guardrail_snapshot_not_reused",
        "require_failed_v4_formal_snapshot_not_reused",
        "require_failed_v5_canary_snapshot_not_reused",
    }, "acceptance lock field set drift")
    _require(acceptance.get("required_case_count") == 485 and acceptance.get("required_lane_counts") == EXPECTED_LANE_COUNTS, "acceptance cardinality drift")
    _require(acceptance.get("formal_repairs_allowed") is False and acceptance.get("correction_count") == 0, "formal correction policy drift")
    _require(acceptance.get("required_case_count_by_dataset") == {"test_normal": 68, "test_challenge": 417}, "acceptance split counts drift")
    _require(acceptance.get("required_schema") == "case_checklist_v1" and acceptance.get("required_final_status") == LIFECYCLE, "acceptance schema/lifecycle drift")
    _require(acceptance.get("required_identity_match") == ["domain", "case_unit_id", "task_id", "split", "source_ref"], "acceptance identity rule drift")
    _require(all(value is True for key, value in acceptance.items() if key.startswith("require_")), "one or more required hard gates are disabled")
    return {
        "schema_version": LOCK_SCHEMA,
        "status": "verified",
        "lock_path": _repo_relative(lock_file),
        "lock_sha256": sha256_file(lock_file),
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "regular_max_parallel": 8,
        "oversized_max_parallel": 8,
        "environment_policy": ENVIRONMENT_POLICY,
    }


def validate_appworld_draft_pre_run_lock_v56(
    *, lock_path: str | Path = DEFAULT_LOCK_PATH
) -> dict[str, Any]:
    """Recompute the v4 lock closure without requiring formal outputs."""

    lock_file = _input_file(lock_path, "v4 pre-run lock")
    _require(
        lock_file == resolve_repo_path(DEFAULT_LOCK_PATH).resolve(),
        "pre-run validation lock path is noncanonical",
    )
    lock = _load_mapping(lock_file, "v4 pre-run lock")
    audit = _validate_lock_v56(lock_file, lock)
    cases, inputs = _validate_locked_inputs_v56(lock)
    return {
        **audit,
        "status": "verified_pre_run_lock",
        "case_count": len(cases),
        "inputs": inputs,
        "formal_cases_root": _mapping(lock.get("execution"), "execution")["output_root"],
    }


def _validate_v56_parsed_config_legacy_v2(
    config: Mapping[str, Any], *, lock: Mapping[str, Any], require_clean_roots: bool
) -> dict[str, Any]:
    expected_keys = {
        "case_packet_root", "output_root", "provider", "model", "reasoning_effort",
        "token_budgets", "max_parallel", "large_max_parallel", "large_case_threshold_bytes",
        "http_timeout_seconds", "large_http_timeout_seconds", "codex_timeout_seconds",
        "large_codex_timeout_seconds", "codex_sandbox", "prompt_supplement", "sort_by",
        "sleep_seconds", "quality_check", "limit", "force", "fail_fast", "dry_run",
        "total_case_count", "regular_case_count", "oversized_case_count",
    }
    _require(set(config) == expected_keys, "formal runner parsed-config field set drift")
    execution = _mapping(lock.get("execution"), "parsed-config execution lock")
    inputs = _mapping(lock.get("inputs"), "parsed-config input lock")
    normalized = dict(config)
    for key in ("case_packet_root", "output_root", "prompt_supplement"):
        normalized[key] = _repo_relative(
            resolve_repo_path(_string(config.get(key), f"parsed config {key}")).resolve()
        )
    expected = {
        "case_packet_root": _string(inputs.get("case_packet_root"), "locked packet root"),
        "output_root": _string(execution.get("output_root"), "locked output root"),
        "provider": "codex", "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "max_parallel": 8, "large_max_parallel": 8,
        "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
        "http_timeout_seconds": 180, "large_http_timeout_seconds": 480,
        "codex_timeout_seconds": 1800, "large_codex_timeout_seconds": 3600,
        "codex_sandbox": EXPECTED_CODEX_SANDBOX,
        "prompt_supplement": _repo_relative(
            resolve_repo_path(_IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"]).resolve()
        ),
        "sort_by": "size", "sleep_seconds": 2.0, "quality_check": "none",
        "limit": None, "force": False, "fail_fast": False, "dry_run": False,
        "total_case_count": 485,
        "regular_case_count": EXPECTED_LANE_COUNTS["regular"],
        "oversized_case_count": EXPECTED_LANE_COUNTS["oversized"],
    }
    _require(normalized == expected, "formal runner parsed config differs from the complete canonical map")
    if require_clean_roots:
        output_root = resolve_repo_path(expected["output_root"]).resolve()
        _require(not output_root.exists(), "formal output root must still be absent at batch start")
        _require(not (output_root.parent / "quarantine").exists(), "formal quarantine root must still be absent at batch start")
    return normalized


def _validate_appworld_v56_batch_start_legacy_v2(config: Mapping[str, Any]) -> dict[str, Any]:
    """Fail before the first model call unless the parsed formal config is exact."""

    expected_keys = {
        "case_packet_root", "output_root", "provider", "model", "reasoning_effort",
        "token_budgets", "max_parallel", "large_max_parallel", "large_case_threshold_bytes",
        "http_timeout_seconds", "large_http_timeout_seconds", "codex_timeout_seconds",
        "large_codex_timeout_seconds", "codex_sandbox", "prompt_supplement", "sort_by",
        "sleep_seconds", "quality_check", "limit", "force", "fail_fast", "dry_run",
        "total_case_count", "regular_case_count", "oversized_case_count",
    }
    _require(set(config) == expected_keys, "formal runner parsed-config field set drift")
    expected_scalars = {
        "provider": "codex", "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "max_parallel": 8, "large_max_parallel": 8,
        "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
        "http_timeout_seconds": 180, "large_http_timeout_seconds": 480,
        "codex_timeout_seconds": 1800, "large_codex_timeout_seconds": 3600,
        "codex_sandbox": EXPECTED_CODEX_SANDBOX, "sort_by": "size", "sleep_seconds": 2.0,
        "quality_check": "none", "limit": None, "force": False,
        "fail_fast": False, "dry_run": False,
        "total_case_count": 485,
        "regular_case_count": EXPECTED_LANE_COUNTS["regular"],
        "oversized_case_count": EXPECTED_LANE_COUNTS["oversized"],
    }
    for key, expected in expected_scalars.items():
        _require(config.get(key) == expected, f"formal runner parsed config drift: {key}")
    lock_audit = validate_appworld_draft_pre_run_lock_v56(lock_path=DEFAULT_LOCK_PATH)
    lock = _load_mapping(_input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock"), "v4 pre-run lock")
    canonical_config = _validate_v56_parsed_config(
        config, lock=lock, require_clean_roots=True
    )
    packet_root = resolve_repo_path(_string(config.get("case_packet_root"), "runner packet root")).resolve()
    output_root = resolve_repo_path(_string(config.get("output_root"), "runner output root")).resolve()
    supplement = resolve_repo_path(_string(config.get("prompt_supplement"), "runner prompt supplement")).resolve()
    _require(packet_root == resolve_repo_path(lock_audit["inputs"]["case_packet_root"]).resolve(), "runner packet root differs from lock")
    _require(output_root == resolve_repo_path(lock_audit["formal_cases_root"]).resolve(), "runner output root differs from lock")
    _require(supplement == resolve_repo_path(_IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"]).resolve(), "runner supplement differs from lock")
    current_environment = _freeze_environment()
    _require(dict(_mapping(lock.get("environment"), "locked environment")) == current_environment, "batch-start env-i environment differs from pre-run lock")
    runtime = _mapping(lock.get("runtime"), "batch-start locked runtime")
    locked_codex = _input_file(_string(runtime.get("codex_executable"), "locked Codex executable"), "locked Codex executable")
    locked_python = _input_file(_string(runtime.get("python_executable"), "locked Python executable"), "locked Python executable")
    _require(Path(sys.executable).resolve() == locked_python, "batch-start Python executable resolution differs from lock")
    _require(sha256_file(locked_python) == runtime.get("python_executable_sha256"), "batch-start Python executable hash differs from lock")
    current_codex = shutil.which("codex")
    _require(current_codex is not None and Path(current_codex).resolve() == locked_codex, "batch-start Codex PATH resolution differs from lock")
    _require(sha256_file(locked_codex) == runtime.get("codex_executable_sha256"), "batch-start Codex executable hash differs from lock")
    current_login = _codex_login_status(locked_codex)
    _require(current_login == "Logged in using ChatGPT", "Codex CLI login is not active at batch start")
    semantic = dict(sorted(canonical_config.items()))
    return {
        "schema_version": "appworld_v56_batch_start_validation.v1",
        "status": "passed",
        "pre_run_lock_sha256": lock_audit["lock_sha256"],
        "parsed_config_semantic_sha256": sha256_object(semantic),
        "parsed_config": semantic,
        "login_status_at_batch_start": current_login,
        "environment_semantic_sha256": current_environment["environment_semantic_sha256"],
        "python_executable_sha256": sha256_file(locked_python),
        "codex_executable_sha256": sha256_file(locked_codex),
    }


def _parsed_config_keys() -> set[str]:
    return {
        "case_packet_root", "output_root", "provider", "model", "reasoning_effort",
        "token_budgets", "max_parallel", "large_max_parallel", "large_case_threshold_bytes",
        "http_timeout_seconds", "large_http_timeout_seconds", "codex_timeout_seconds",
        "large_codex_timeout_seconds", "codex_sandbox", "prompt_supplement", "sort_by",
        "sleep_seconds", "quality_check", "limit", "case_ids", "canary_round", "run_kind",
        "force", "fail_fast", "dry_run", "total_case_count", "regular_case_count",
        "oversized_case_count",
    }


def _validate_v56_parsed_config(
    config: Mapping[str, Any], *, lock: Mapping[str, Any], require_clean_roots: bool
) -> dict[str, Any]:
    """Validate the complete formal or canary runner map without implicit mode inference."""

    _require(set(config) == _parsed_config_keys(), "runner parsed-config field set drift")
    run_kind = _string(config.get("run_kind"), "parsed config run_kind")
    _require(run_kind in {"formal", "canary"}, "runner run_kind must be formal/canary")
    inputs = _mapping(lock.get("inputs"), "parsed-config input lock")
    execution = _mapping(lock.get("execution"), "parsed-config execution lock")
    normalized = dict(config)
    for key in ("case_packet_root", "output_root", "prompt_supplement"):
        normalized[key] = _repo_relative(
            resolve_repo_path(_string(config.get(key), f"parsed config {key}")).resolve()
        )

    common = {
        "case_packet_root": _string(inputs.get("case_packet_root"), "locked packet root"),
        "provider": "codex",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "max_parallel": EXPECTED_MAX_PARALLEL,
        "large_max_parallel": EXPECTED_MAX_PARALLEL,
        "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
        "http_timeout_seconds": 180,
        "large_http_timeout_seconds": 480,
        "codex_timeout_seconds": 1800,
        "large_codex_timeout_seconds": 3600,
        "codex_sandbox": EXPECTED_CODEX_SANDBOX,
        "prompt_supplement": _repo_relative(
            resolve_repo_path(_IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"]).resolve()
        ),
        "sort_by": "size",
        "sleep_seconds": 2.0,
        "quality_check": "none",
        "limit": None,
        "force": False,
        "fail_fast": True,
        "dry_run": False,
    }
    if run_kind == "formal":
        expected = {
            **common,
            "output_root": _string(execution.get("output_root"), "locked formal output root"),
            "case_ids": None,
            "canary_round": None,
            "run_kind": "formal",
            "total_case_count": EXPECTED_EXTENSION_COUNT,
            "regular_case_count": EXPECTED_LANE_COUNTS["regular"],
            "oversized_case_count": EXPECTED_LANE_COUNTS["oversized"],
        }
    else:
        round_id = _string(config.get("canary_round"), "parsed config canary_round")
        rounds = {
            _string(item.get("round_id"), "locked canary round ID"): _mapping(item, "locked canary round")
            for item in _mapping(lock.get("preflight"), "locked canary plan").get("rounds", [])
            if isinstance(item, Mapping)
        }
        _require(round_id in rounds, f"canary round is not locked: {round_id}")
        round_plan = rounds[round_id]
        expected = {
            **common,
            "output_root": _string(round_plan.get("output_root"), "locked canary output root"),
            "case_ids": list(EXPECTED_PREFLIGHT_CASE_IDS),
            "canary_round": round_id,
            "run_kind": "canary",
            "total_case_count": len(EXPECTED_PREFLIGHT_CASE_IDS),
            "regular_case_count": EXPECTED_PREFLIGHT_LANE_COUNTS["regular"],
            "oversized_case_count": EXPECTED_PREFLIGHT_LANE_COUNTS["oversized"],
        }
    _require(normalized == expected, f"{run_kind} runner parsed config differs from the complete canonical map")
    if require_clean_roots:
        output_root = resolve_repo_path(expected["output_root"]).resolve()
        _require(not output_root.exists(), f"{run_kind} output root must be absent at batch start")
        _require(not (output_root.parent / "quarantine").exists(), f"{run_kind} quarantine root must be absent at batch start")
    return normalized


def validate_appworld_v56_batch_start(
    config: Mapping[str, Any], *, invocation_argv: Sequence[str]
) -> dict[str, Any]:
    """Fail before model calls unless the selected immutable phase is fully authorized."""

    _require(set(config) == _parsed_config_keys(), "runner parsed-config field set drift")
    lock_audit = validate_appworld_draft_pre_run_lock_v56(lock_path=DEFAULT_LOCK_PATH)
    lock = _load_mapping(_input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock"), "v4 pre-run lock")
    canonical_config = _validate_v56_parsed_config(config, lock=lock, require_clean_roots=True)
    run_kind = _string(canonical_config.get("run_kind"), "canonical run kind")
    round_id = (
        _string(canonical_config.get("canary_round"), "canonical canary round")
        if run_kind == "canary"
        else None
    )
    _validate_phase_start_provenance_inventory(run_kind=run_kind, round_id=round_id)
    phase_start_path, phase_terminal_path = _phase_receipt_paths(
        run_kind=run_kind, round_id=round_id
    )
    _require(not phase_start_path.exists(), f"phase-start receipt already exists: {phase_start_path}")
    _require(not phase_terminal_path.exists(), f"phase-terminal receipt pre-exists: {phase_terminal_path}")
    actual_invocation = list(invocation_argv)
    _require(
        actual_invocation
        and all(isinstance(value, str) for value in actual_invocation)
        and actual_invocation == _expected_phase_argv(
            lock=lock, run_kind=run_kind, round_id=round_id
        ),
        f"{run_kind} runner invocation argv differs byte-for-byte from the locked command",
    )

    prior_receipt_sha256: str | None = None
    canary_acceptance_sha256: str | None = None
    if run_kind == "canary":
        assert round_id is not None
        round_index = EXPECTED_PREFLIGHT_ROUNDS.index(round_id)
        _require(
            not _canary_round_receipt_path(round_id).exists(),
            f"current canary receipt pre-exists its batch: {round_id}",
        )
        for later in EXPECTED_PREFLIGHT_ROUNDS[round_index + 1 :]:
            _require(
                not _canary_round_receipt_path(later).exists(),
                f"later canary receipt pre-exists {round_id}: {later}",
            )
        _require(not DEFAULT_CANARY_ACCEPTANCE_PATH.exists(), "canary sequence receipt pre-exists an unfinished round")
        if round_index:
            prior = validate_appworld_v56_canary_round_receipt(
                round_id=EXPECTED_PREFLIGHT_ROUNDS[round_index - 1]
            )
            prior_receipt_sha256 = prior["receipt_sha256"]
    else:
        accepted = validate_appworld_v56_canary_acceptance()
        canary_acceptance_sha256 = accepted["receipt_sha256"]

    current_environment = _freeze_environment()
    _require(dict(_mapping(lock.get("environment"), "locked environment")) == current_environment, "batch-start environment differs from pre-run lock")
    runtime = _mapping(lock.get("runtime"), "batch-start locked runtime")
    locked_codex = _input_file(_string(runtime.get("codex_executable"), "locked Codex executable"), "locked Codex executable")
    locked_python = _input_file(_string(runtime.get("python_executable"), "locked Python executable"), "locked Python executable")
    _require(Path(sys.executable).resolve() == locked_python, "batch-start Python executable resolution differs from lock")
    _require(sha256_file(locked_python) == runtime.get("python_executable_sha256"), "batch-start Python executable hash differs from lock")
    current_codex = shutil.which("codex")
    _require(current_codex is not None and Path(current_codex).resolve() == locked_codex, "batch-start Codex PATH resolution differs from lock")
    _require(sha256_file(locked_codex) == runtime.get("codex_executable_sha256"), "batch-start Codex executable bytes differ from lock")
    current_login = _codex_login_status(locked_codex)
    _require(current_login == "Logged in using ChatGPT", "Codex CLI login is not active at batch start")
    semantic = dict(sorted(canonical_config.items()))
    core_audit = {
        "schema_version": "appworld_v56_batch_start_validation.v2",
        "status": "passed",
        "run_kind": run_kind,
        "canary_round": canonical_config.get("canary_round"),
        "pre_run_lock_sha256": lock_audit["lock_sha256"],
        "prior_round_receipt_sha256": prior_receipt_sha256,
        "canary_acceptance_sha256": canary_acceptance_sha256,
        "parsed_config_semantic_sha256": sha256_object(semantic),
        "parsed_config": semantic,
        "login_status_at_batch_start": current_login,
        "environment_semantic_sha256": current_environment["environment_semantic_sha256"],
        "python_executable_sha256": sha256_file(locked_python),
        "codex_executable_sha256": sha256_file(locked_codex),
    }
    phase_start = {
        "schema_version": PHASE_START_SCHEMA,
        "status": "started_locked",
        "started_at": _utc_now(),
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "run_kind": run_kind,
        "canary_round": round_id,
        "pre_run_lock": {
            "path": _repo_relative(_input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")),
            "sha256": lock_audit["lock_sha256"],
        },
        "output_root": canonical_config["output_root"],
        "quarantine_root": _repo_relative(
            resolve_repo_path(_string(canonical_config["output_root"], "phase output root")).resolve().parent
            / "quarantine"
        ),
        "invocation_argv": actual_invocation,
        "invocation_argv_semantic_sha256": sha256_object(actual_invocation),
        "batch_start_validation": core_audit,
        "batch_start_validation_semantic_sha256": sha256_object(core_audit),
    }
    _write_json_exclusive(phase_start_path, phase_start)
    return {
        **core_audit,
        "phase_start_receipt_path": _repo_relative(phase_start_path),
        "phase_start_receipt_sha256": sha256_file(phase_start_path),
        "invocation_argv_semantic_sha256": sha256_object(actual_invocation),
    }


def _validate_phase_start_receipt(
    *, run_kind: str, round_id: str | None
) -> dict[str, Any]:
    start_path, _ = _phase_receipt_paths(run_kind=run_kind, round_id=round_id)
    start_file = _input_file(start_path, f"{run_kind} phase-start receipt")
    receipt = _load_mapping(start_file, f"{run_kind} phase-start receipt")
    _require(
        set(receipt)
        == {
            "schema_version",
            "status",
            "started_at",
            "draft_run_id",
            "run_kind",
            "canary_round",
            "pre_run_lock",
            "output_root",
            "quarantine_root",
            "invocation_argv",
            "invocation_argv_semantic_sha256",
            "batch_start_validation",
            "batch_start_validation_semantic_sha256",
        },
        f"{run_kind} phase-start receipt field set drift",
    )
    _require(
        receipt.get("schema_version") == PHASE_START_SCHEMA
        and receipt.get("status") == "started_locked"
        and receipt.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID
        and receipt.get("run_kind") == run_kind
        and receipt.get("canary_round") == round_id,
        f"{run_kind} phase-start receipt identity drift",
    )
    started_at = _utc_timestamp(receipt.get("started_at"), f"{run_kind} phase started_at")
    lock_file = _input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")
    lock = _load_mapping(lock_file, "v4 pre-run lock")
    _require(
        receipt.get("pre_run_lock")
        == {"path": _repo_relative(lock_file), "sha256": sha256_file(lock_file)},
        f"{run_kind} phase-start lock binding drift",
    )
    _require(
        _utc_timestamp(lock.get("locked_at"), "pre-run locked_at") <= started_at,
        f"{run_kind} phase started before the pre-run lock",
    )
    core = _mapping(receipt.get("batch_start_validation"), f"{run_kind} batch-start core")
    _require(
        set(core)
        == {
            "schema_version",
            "status",
            "run_kind",
            "canary_round",
            "pre_run_lock_sha256",
            "prior_round_receipt_sha256",
            "canary_acceptance_sha256",
            "parsed_config_semantic_sha256",
            "parsed_config",
            "login_status_at_batch_start",
            "environment_semantic_sha256",
            "python_executable_sha256",
            "codex_executable_sha256",
        },
        f"{run_kind} batch-start core field set drift",
    )
    _require(
        core.get("schema_version") == "appworld_v56_batch_start_validation.v2"
        and core.get("status") == "passed"
        and core.get("run_kind") == run_kind
        and core.get("canary_round") == round_id
        and core.get("pre_run_lock_sha256") == sha256_file(lock_file),
        f"{run_kind} batch-start core identity drift",
    )
    config = _mapping(core.get("parsed_config"), f"{run_kind} phase parsed config")
    canonical_config = _validate_v56_parsed_config(
        config, lock=lock, require_clean_roots=False
    )
    _require(
        dict(config) == canonical_config
        and core.get("parsed_config_semantic_sha256") == sha256_object(dict(config)),
        f"{run_kind} phase parsed-config binding drift",
    )
    expected_output = _string(canonical_config.get("output_root"), "phase output root")
    expected_quarantine = _repo_relative(
        resolve_repo_path(expected_output).resolve().parent / "quarantine"
    )
    _require(
        receipt.get("output_root") == expected_output
        and receipt.get("quarantine_root") == expected_quarantine,
        f"{run_kind} phase output/quarantine root drift",
    )
    invocation = receipt.get("invocation_argv")
    _require(
        isinstance(invocation, list)
        and all(isinstance(value, str) for value in invocation)
        and invocation == _expected_phase_argv(
            lock=lock, run_kind=run_kind, round_id=round_id
        )
        and receipt.get("invocation_argv_semantic_sha256")
        == sha256_object(invocation),
        f"{run_kind} phase invocation binding drift",
    )
    environment = _mapping(lock.get("environment"), "phase locked environment")
    runtime = _mapping(lock.get("runtime"), "phase locked runtime")
    _require(
        core.get("login_status_at_batch_start") == "Logged in using ChatGPT"
        and core.get("environment_semantic_sha256")
        == environment.get("environment_semantic_sha256")
        and core.get("python_executable_sha256")
        == runtime.get("python_executable_sha256")
        and core.get("codex_executable_sha256")
        == runtime.get("codex_executable_sha256"),
        f"{run_kind} phase login/environment/runtime binding drift",
    )
    if run_kind == "canary":
        assert round_id is not None
        index = EXPECTED_PREFLIGHT_ROUNDS.index(round_id)
        expected_prior = None
        if index:
            previous = validate_appworld_v56_canary_round_receipt(
                round_id=EXPECTED_PREFLIGHT_ROUNDS[index - 1]
            )
            expected_prior = previous["receipt_sha256"]
            _require(
                _utc_timestamp(previous["validated_at"], "previous canary receipt")
                < started_at,
                f"{round_id} phase did not start after its predecessor receipt",
            )
        _require(
            core.get("prior_round_receipt_sha256") == expected_prior
            and core.get("canary_acceptance_sha256") is None,
            f"{round_id} phase predecessor binding drift",
        )
    else:
        accepted = validate_appworld_v56_canary_acceptance()
        _require(
            core.get("prior_round_receipt_sha256") is None
            and core.get("canary_acceptance_sha256") == accepted["receipt_sha256"],
            "formal phase canary-acceptance binding drift",
        )
        accepted_payload = _load_mapping(
            _input_file(DEFAULT_CANARY_ACCEPTANCE_PATH, "canary acceptance"),
            "canary acceptance",
        )
        _require(
            _utc_timestamp(accepted_payload.get("validated_at"), "canary acceptance validated_at")
            < started_at,
            "formal phase did not start after canary acceptance",
        )
    _require(
        receipt.get("batch_start_validation_semantic_sha256") == sha256_object(core),
        f"{run_kind} batch-start core hash drift",
    )
    public_audit = {
        **dict(core),
        "phase_start_receipt_path": _repo_relative(start_file),
        "phase_start_receipt_sha256": sha256_file(start_file),
        "invocation_argv_semantic_sha256": sha256_object(invocation),
    }
    return {
        "receipt_path": _repo_relative(start_file),
        "receipt_sha256": sha256_file(start_file),
        "started_at": receipt["started_at"],
        "output_root": expected_output,
        "quarantine_root": expected_quarantine,
        "batch_start_validation": public_audit,
    }


def finalize_appworld_v56_phase(
    *, run_kind: str, round_id: str | None, exit_code: int
) -> dict[str, Any]:
    """Seal a normally returned runner phase; missing terminal means interrupted/invalid."""

    _require(type(exit_code) is int and exit_code in {0, 1}, "phase exit code must be 0/1")
    start = _validate_phase_start_receipt(run_kind=run_kind, round_id=round_id)
    _, terminal_path = _phase_receipt_paths(run_kind=run_kind, round_id=round_id)
    _require(not terminal_path.exists(), f"phase-terminal receipt already exists: {terminal_path}")
    output_root = _input_directory(start["output_root"], f"{run_kind} phase output root")
    summary_path = _input_file(output_root / "_batch_summary.json", f"{run_kind} batch summary")
    results_path = _input_file(output_root / "_batch_results.jsonl", f"{run_kind} batch results")
    summary = _load_mapping(summary_path, f"{run_kind} batch summary")
    rows = _load_jsonl(results_path, f"{run_kind} batch results")
    expected_total = (
        len(EXPECTED_PREFLIGHT_CASE_IDS)
        if run_kind == "canary"
        else EXPECTED_EXTENSION_COUNT
    )
    passed = exit_code == 0
    if passed:
        _require(
            summary.get("total_cases") == expected_total
            and summary.get("completed_cases") == expected_total
            and summary.get("success_cases") == expected_total
            and summary.get("skipped_cases") == 0
            and summary.get("failed_cases") == 0
            and summary.get("warning_count") == 0
            and len(rows) == expected_total
            and all(row.get("status") == "success" for row in rows),
            f"{run_kind} zero exit does not have an exact all-success batch",
        )
    quarantine_root = resolve_repo_path(start["quarantine_root"]).resolve()
    if quarantine_root.exists():
        quarantine_dir = _input_directory(quarantine_root, f"{run_kind} phase quarantine")
        _validate_no_symlinks(quarantine_dir)
        quarantine_ref = {
            "root": _repo_relative(quarantine_dir),
            "exists": True,
            "tree_sha256": sha256_path(quarantine_dir),
        }
    else:
        quarantine_ref = {
            "root": _repo_relative(quarantine_root),
            "exists": False,
            "tree_sha256": None,
        }
    if passed and run_kind == "canary":
        _require(not quarantine_ref["exists"], "passing canary phase has quarantine evidence")
    receipt = {
        "schema_version": PHASE_TERMINAL_SCHEMA,
        "status": "passed_complete" if passed else "invalid_complete",
        "completed_at": _utc_now(),
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "run_kind": run_kind,
        "canary_round": round_id,
        "exit_code": exit_code,
        "phase_start_receipt": {
            "path": start["receipt_path"],
            "sha256": start["receipt_sha256"],
        },
        "output_root": start["output_root"],
        "output_tree_sha256": sha256_path(output_root),
        "quarantine": quarantine_ref,
        "batch_summary": {
            "path": _repo_relative(summary_path),
            "sha256": sha256_file(summary_path),
        },
        "batch_results": {
            "path": _repo_relative(results_path),
            "sha256": sha256_file(results_path),
            "row_count": len(rows),
        },
    }
    _write_json_exclusive(terminal_path, receipt)
    return {
        "status": receipt["status"],
        "receipt_path": _repo_relative(terminal_path),
        "receipt_sha256": sha256_file(terminal_path),
    }


def _validate_phase_terminal_receipt(
    *, run_kind: str, round_id: str | None, require_passed: bool
) -> dict[str, Any]:
    start = _validate_phase_start_receipt(run_kind=run_kind, round_id=round_id)
    _, terminal_path = _phase_receipt_paths(run_kind=run_kind, round_id=round_id)
    terminal_file = _input_file(terminal_path, f"{run_kind} phase-terminal receipt")
    receipt = _load_mapping(terminal_file, f"{run_kind} phase-terminal receipt")
    _require(
        set(receipt)
        == {
            "schema_version",
            "status",
            "completed_at",
            "draft_run_id",
            "run_kind",
            "canary_round",
            "exit_code",
            "phase_start_receipt",
            "output_root",
            "output_tree_sha256",
            "quarantine",
            "batch_summary",
            "batch_results",
        },
        f"{run_kind} phase-terminal field set drift",
    )
    expected_status = "passed_complete" if receipt.get("exit_code") == 0 else "invalid_complete"
    _require(
        receipt.get("schema_version") == PHASE_TERMINAL_SCHEMA
        and receipt.get("status") == expected_status
        and receipt.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID
        and receipt.get("run_kind") == run_kind
        and receipt.get("canary_round") == round_id
        and type(receipt.get("exit_code")) is int
        and receipt.get("exit_code") in {0, 1},
        f"{run_kind} phase-terminal identity drift",
    )
    if require_passed:
        _require(receipt.get("status") == "passed_complete", f"{run_kind} phase did not terminate successfully")
    completed_at = _utc_timestamp(receipt.get("completed_at"), f"{run_kind} phase completed_at")
    _require(
        _utc_timestamp(start["started_at"], f"{run_kind} phase started_at")
        <= completed_at,
        f"{run_kind} phase terminal predates start",
    )
    _require(
        receipt.get("phase_start_receipt")
        == {"path": start["receipt_path"], "sha256": start["receipt_sha256"]}
        and receipt.get("output_root") == start["output_root"],
        f"{run_kind} phase terminal start/output binding drift",
    )
    output_root = _input_directory(start["output_root"], f"{run_kind} phase output root")
    _require(
        receipt.get("output_tree_sha256") == sha256_path(output_root),
        f"{run_kind} phase output changed after terminal receipt",
    )
    quarantine_root = resolve_repo_path(start["quarantine_root"]).resolve()
    if quarantine_root.exists():
        quarantine_dir = _input_directory(quarantine_root, f"{run_kind} phase quarantine")
        _validate_no_symlinks(quarantine_dir)
        expected_quarantine = {
            "root": _repo_relative(quarantine_dir),
            "exists": True,
            "tree_sha256": sha256_path(quarantine_dir),
        }
    else:
        expected_quarantine = {
            "root": _repo_relative(quarantine_root),
            "exists": False,
            "tree_sha256": None,
        }
    _require(
        receipt.get("quarantine") == expected_quarantine,
        f"{run_kind} phase quarantine changed after terminal receipt",
    )
    if require_passed and run_kind == "canary":
        _require(not expected_quarantine["exists"], "passing canary phase has quarantine evidence")
    summary_path = _input_file(output_root / "_batch_summary.json", f"{run_kind} summary")
    results_path = _input_file(output_root / "_batch_results.jsonl", f"{run_kind} results")
    rows = _load_jsonl(results_path, f"{run_kind} results")
    _require(
        receipt.get("batch_summary")
        == {"path": _repo_relative(summary_path), "sha256": sha256_file(summary_path)}
        and receipt.get("batch_results")
        == {
            "path": _repo_relative(results_path),
            "sha256": sha256_file(results_path),
            "row_count": len(rows),
        },
        f"{run_kind} phase terminal batch-file binding drift",
    )
    summary = _load_mapping(summary_path, f"{run_kind} summary")
    _require(
        _utc_timestamp(summary.get("updated_at"), f"{run_kind} summary updated_at")
        <= completed_at,
        f"{run_kind} phase terminal predates batch completion",
    )
    return {
        "status": receipt["status"],
        "receipt_path": _repo_relative(terminal_file),
        "receipt_sha256": sha256_file(terminal_file),
        "completed_at": receipt["completed_at"],
        "phase_start": start,
        "quarantine": expected_quarantine,
    }


def _validate_locked_inputs_v56(lock: Mapping[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    inputs = _mapping(lock.get("inputs"), "inputs")
    packet_root = _input_directory(_string(inputs.get("case_packet_root"), "inputs.case_packet_root"), "packet root")
    fresh, cases = _freeze_inputs(packet_root)
    _require(dict(inputs) == fresh, "one or more frozen input, packet, source, or manifest hashes drifted")
    return cases, {
        "case_count": 485,
        "case_count_by_dataset": {"test_normal": 68, "test_challenge": 417},
        "case_packet_root": _repo_relative(packet_root),
        "case_packet_tree_sha256": inputs["case_packet_tree_sha256"],
        "case_ids_semantic_sha256": inputs["case_ids_semantic_sha256"],
        "all_input_hashes_recomputed": True,
        "official_source_hashes_recomputed": True,
    }


def _validate_batch(
    *, formal_root: Path, cases: Sequence[Mapping[str, str]], lock: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_ids = [case["case_unit_id"] for case in cases]
    expected_set = set(expected_ids)
    entries = list(formal_root.iterdir())
    directories = {path.name for path in entries if path.is_dir() and not path.is_symlink()}
    files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    _require(directories == expected_set, f"formal case directory set mismatch: missing={sorted(expected_set-directories)[:5]}, extra={sorted(directories-expected_set)[:5]}")
    _require(files == _ROOT_BATCH_FILES, "formal root must contain only the two canonical batch files")
    terminal = _validate_phase_terminal_receipt(
        run_kind="formal", round_id=None, require_passed=True
    )
    summary_path = _input_file(formal_root / "_batch_summary.json", "batch summary")
    results_path = _input_file(formal_root / "_batch_results.jsonl", "batch results")
    summary = _load_mapping(summary_path, "batch summary")
    _require(set(summary) == {
        "started_at", "updated_at", "total_cases", "completed_cases", "success_cases",
        "skipped_cases", "failed_cases", "warning_count", "provider", "model",
        "reasoning_effort", "codex_sandbox", "prompt_supplement", "token_budgets",
        "sort_by", "quality_check", "large_case_threshold_bytes", "lane_stats",
        "output_root", "appworld_v56_runtime_gate", "runtime_policy_gate_schema",
        "runtime_policy_gate_policy", "runtime_policy_gate_counts",
        "regular_max_parallel", "oversized_max_parallel",
        "parsed_config_semantic_sha256", "batch_start_validation",
        "quarantined_attempt_count", "quarantine_root",
    }, "batch summary field set drift")
    batch_started = _utc_timestamp(summary.get("started_at"), "batch started_at")
    batch_updated = _utc_timestamp(summary.get("updated_at"), "batch updated_at")
    _require(
        _utc_timestamp(terminal["phase_start"]["started_at"], "formal phase started_at")
        <= batch_started
        <= batch_updated
        <= _utc_timestamp(terminal["completed_at"], "formal phase completed_at"),
        "formal phase/batch time order is invalid",
    )
    expected_summary = {
        "total_cases": 485, "completed_cases": 485, "success_cases": 485,
        "skipped_cases": 0, "failed_cases": 0, "warning_count": 0,
        "provider": "codex", "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT, "codex_sandbox": EXPECTED_CODEX_SANDBOX,
        "prompt_supplement": _repo_relative(_IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"]),
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS), "sort_by": "size",
        "quality_check": "none", "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
        "output_root": _repo_relative(formal_root),
        "appworld_v56_runtime_gate": True,
        "runtime_policy_gate_schema": RUNTIME_GATE_SCHEMA,
        "runtime_policy_gate_policy": EVENT_COMMAND_POLICY,
        "quarantine_root": _string(_mapping(lock.get("execution"), "execution").get("quarantine_root"), "execution.quarantine_root"),
        "regular_max_parallel": 8,
        "oversized_max_parallel": 8,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"batch summary {key} mismatch")
    lane_stats = _mapping(summary.get("lane_stats"), "batch lane_stats")
    _require(
        _mapping(lane_stats.get("regular"), "regular lane").get("count")
        == EXPECTED_LANE_COUNTS["regular"],
        "regular lane count differs from the frozen lane split",
    )
    _require(
        _mapping(lane_stats.get("oversized"), "oversized lane").get("count")
        == EXPECTED_LANE_COUNTS["oversized"],
        "oversized lane count differs from the frozen lane split",
    )

    rows = _load_jsonl(results_path, "batch results")
    _require(len(rows) == 485, "batch results must contain exactly 485 rows")
    ids = [str(row.get("case_unit_dir")) for row in rows]
    _require(len(set(ids)) == 485 and set(ids) == expected_set, "batch rows are duplicated, missing, or off-list")
    _require(Counter(str(row.get("status")) for row in rows) == Counter({"success": 485}), "all formal rows must be first-class successes")
    lane_counts = Counter(str(row.get("lane")) for row in rows)
    _require(
        lane_counts == Counter(EXPECTED_LANE_COUNTS),
        "formal result lane counts differ from the frozen lane split",
    )
    gate_counts: Counter[str] = Counter()
    for row in rows:
        attempts = row.get("attempts")
        _require(isinstance(attempts, list) and attempts, "every successful batch row must have attempts")
        for raw_attempt in attempts:
            attempt = _mapping(raw_attempt, "batch attempt")
            gate = _mapping(attempt.get("runtime_policy_gate"), "batch runtime policy gate")
            _require(gate.get("schema_version") == RUNTIME_GATE_SCHEMA, "batch runtime policy gate schema drift")
            _require(gate.get("policy") == EVENT_COMMAND_POLICY, "batch runtime policy gate policy drift")
            status = _string(gate.get("status"), "batch runtime policy gate status")
            _require(status in {"passed", "failed", "not_run"}, "batch runtime policy gate status is invalid")
            gate_counts[status] += 1
    _require(gate_counts["passed"] == 485, "exactly 485 promoted attempts must pass runtime policy")
    expected_gate_counts = {
        "passed": gate_counts["passed"],
        "failed": gate_counts["failed"],
        "not_run": gate_counts["not_run"],
    }
    _require(summary.get("runtime_policy_gate_counts") == expected_gate_counts, "batch runtime policy gate counts mismatch")
    rejected_count = gate_counts["failed"] + gate_counts["not_run"]
    _require(summary.get("quarantined_attempt_count") == rejected_count, "batch quarantined-attempt count mismatch")
    start_audit = _mapping(summary.get("batch_start_validation"), "batch start validation")
    _require(set(start_audit) == {
        "schema_version", "status", "run_kind", "canary_round", "pre_run_lock_sha256",
        "prior_round_receipt_sha256", "canary_acceptance_sha256",
        "parsed_config_semantic_sha256", "parsed_config",
        "login_status_at_batch_start", "environment_semantic_sha256",
        "python_executable_sha256", "codex_executable_sha256",
        "phase_start_receipt_path", "phase_start_receipt_sha256",
        "invocation_argv_semantic_sha256",
    }, "batch start validation field set drift")
    _require(
        dict(start_audit) == terminal["phase_start"]["batch_start_validation"],
        "formal batch-start audit differs from its immutable phase-start receipt",
    )
    _require(
        start_audit.get("schema_version") == "appworld_v56_batch_start_validation.v2"
        and start_audit.get("status") == "passed"
        and start_audit.get("run_kind") == "formal"
        and start_audit.get("canary_round") is None
        and start_audit.get("prior_round_receipt_sha256") is None,
        "formal batch start validation did not pass with the exact phase identity",
    )
    _require(start_audit.get("pre_run_lock_sha256") == sha256_file(_input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")), "batch start lock binding drift")
    _require(start_audit.get("login_status_at_batch_start") == "Logged in using ChatGPT", "batch-start Codex login provenance drift")
    _require(start_audit.get("environment_semantic_sha256") == _mapping(lock.get("environment"), "locked environment").get("environment_semantic_sha256"), "batch-start environment binding drift")
    locked_runtime = _mapping(lock.get("runtime"), "locked runtime")
    _require(start_audit.get("python_executable_sha256") == locked_runtime.get("python_executable_sha256"), "batch-start Python hash binding drift")
    _require(start_audit.get("codex_executable_sha256") == locked_runtime.get("codex_executable_sha256"), "batch-start Codex hash binding drift")
    canary_acceptance = validate_appworld_v56_canary_acceptance()
    _require(
        start_audit.get("canary_acceptance_sha256") == canary_acceptance["receipt_sha256"],
        "formal batch-start canary acceptance binding drift",
    )
    canary_payload = _load_mapping(DEFAULT_CANARY_ACCEPTANCE_PATH, "canary sequence receipt")
    _require(
        _utc_timestamp(canary_payload.get("validated_at"), "canary sequence validated_at")
        < _utc_timestamp(summary.get("started_at"), "formal batch started_at"),
        "formal batch did not start strictly after canary sequence acceptance",
    )
    parsed_config = _mapping(start_audit.get("parsed_config"), "batch parsed config")
    _require(start_audit.get("parsed_config_semantic_sha256") == sha256_object(dict(parsed_config)), "batch parsed config semantic hash drift")
    canonical_config = _validate_v56_parsed_config(
        parsed_config, lock=lock, require_clean_roots=False
    )
    _require(dict(parsed_config) == canonical_config, "stored parsed config differs from independent full-map validation")
    _require(summary.get("parsed_config_semantic_sha256") == start_audit.get("parsed_config_semantic_sha256"), "batch summary/config hash mismatch")
    _require(parsed_config.get("max_parallel") == 8 and parsed_config.get("large_max_parallel") == 8, "parsed concurrency upper bounds are not 8/8")
    _require(
        parsed_config.get("total_case_count") == 485
        and parsed_config.get("regular_case_count")
        == EXPECTED_LANE_COUNTS["regular"]
        and parsed_config.get("oversized_case_count")
        == EXPECTED_LANE_COUNTS["oversized"],
        "parsed case/lane counts drift",
    )
    _require(parsed_config.get("provider") == "codex" and parsed_config.get("model") == EXPECTED_MODEL and parsed_config.get("reasoning_effort") == EXPECTED_REASONING_EFFORT, "parsed provider/model/reasoning drift")
    return ({
        "summary_path": _repo_relative(summary_path), "summary_sha256": sha256_file(summary_path),
        "results_path": _repo_relative(results_path), "results_sha256": sha256_file(results_path),
        "started_at": summary["started_at"], "updated_at": summary["updated_at"],
        "result_rows_semantic_sha256": sha256_object(rows), "result_row_count": 485,
        "status_counts": {"success": 485, "skipped_existing": 0, "failed": 0},
        "lane_counts": EXPECTED_LANE_COUNTS, "formal_repairs_applied": False,
        "runtime_policy_gate_counts": expected_gate_counts,
        "promoted_runtime_policy_pass_count": 485,
        "rejected_attempt_count": rejected_count,
        "phase_start_receipt": {
            "path": terminal["phase_start"]["receipt_path"],
            "sha256": terminal["phase_start"]["receipt_sha256"],
        },
        "phase_terminal_receipt": {
            "path": terminal["receipt_path"],
            "sha256": terminal["receipt_sha256"],
        },
    }, rows)


def _validate_case(
    *,
    case: Mapping[str, str],
    case_dir: Path,
    packet_dir: Path,
    result_row: Mapping[str, Any],
    quarantine_root: Path,
) -> tuple[dict[str, Any], dict[str, int], int]:
    case_id = case["case_unit_id"]
    case_dir = _input_directory(case_dir, f"formal case {case_id}")
    packet_dir = _input_directory(packet_dir, f"packet directory {case_id}")
    packet_path = _input_file(packet_dir / "case_packet.md", f"packet {case_id}")
    raw_manifest_path = _input_file(packet_dir / "raw_case_manifest.json", f"raw manifest {case_id}")
    raw_manifest = _load_mapping(raw_manifest_path, f"raw manifest {case_id}")
    for key, expected in (
        ("case_unit_id", case_id), ("task_id", case_id),
        ("domain", "appworld"), ("dataset_name", case["dataset_name"]),
        ("split", case["split"]), ("source_ref", case["source_ref"]),
    ):
        _require(raw_manifest.get(key) == expected, f"raw manifest {key} mismatch: {case_id}")
    _validate_raw_source_hashes(packet_dir=packet_dir, raw_manifest=raw_manifest, case_id=case_id)

    _require(result_row.get("case_unit_dir") == case_id, f"batch result identity mismatch: {case_id}")
    _require(set(result_row) == {
        "case_unit_dir", "case_packet", "case_packet_size_bytes", "lane", "status",
        "attempts", "quality_warnings", "checklist_path",
    }, f"batch result field set drift: {case_id}")
    _require(result_row.get("case_packet") == _repo_relative(packet_path), f"batch packet pointer mismatch: {case_id}")
    _require(result_row.get("case_packet_size_bytes") == packet_path.stat().st_size, f"batch packet size mismatch: {case_id}")
    expected_lane = "oversized" if packet_path.stat().st_size > EXPECTED_LARGE_THRESHOLD_BYTES else "regular"
    _require(result_row.get("lane") == expected_lane, f"batch lane mismatch: {case_id}")
    _require(result_row.get("status") == "success", f"formal row is not success: {case_id}")
    _require(result_row.get("quality_warnings") == [], f"quality warnings are nonempty: {case_id}")
    expected_checklist_path = _repo_relative(case_dir / "checklist.yaml")
    _require(result_row.get("checklist_path") == expected_checklist_path, f"checklist result pointer mismatch: {case_id}")

    attempts = result_row.get("attempts")
    _require(isinstance(attempts, list) and 1 <= len(attempts) <= len(EXPECTED_TOKEN_BUDGETS), f"attempt history invalid: {case_id}")
    successful_index = len(attempts)
    quarantined_attempts: list[dict[str, Any]] = []
    for expected_index, raw_attempt in enumerate(attempts, start=1):
        attempt = _mapping(raw_attempt, f"attempt {case_id}/{expected_index}")
        _require(attempt.get("attempt_index") == expected_index, f"attempt index mismatch: {case_id}")
        _require(attempt.get("max_output_tokens") == EXPECTED_TOKEN_BUDGETS[expected_index - 1], f"attempt token label mismatch: {case_id}")
        _require(attempt.get("http_timeout_seconds") == (480 if expected_lane == "oversized" else 180), f"attempt HTTP timeout mismatch: {case_id}")
        _require(attempt.get("codex_timeout_seconds") == (3600 if expected_lane == "oversized" else 1800), f"attempt Codex timeout mismatch: {case_id}")
        gate = _mapping(attempt.get("runtime_policy_gate"), f"runtime policy gate {case_id}/{expected_index}")
        _require(gate.get("schema_version") == RUNTIME_GATE_SCHEMA and gate.get("policy") == EVENT_COMMAND_POLICY, f"runtime policy gate identity drift: {case_id}/{expected_index}")
        duration = attempt.get("duration_seconds")
        _require(
            isinstance(duration, (int, float)) and not isinstance(duration, bool)
            and math.isfinite(float(duration)) and float(duration) >= 0,
            f"attempt duration is not finite/nonnegative: {case_id}/{expected_index}",
        )
        _require(isinstance(attempt.get("stderr_tail"), str), f"attempt stderr_tail is not a string: {case_id}/{expected_index}")
        if expected_index == successful_index:
            _require(set(attempt) == {
                "attempt_index", "max_output_tokens", "http_timeout_seconds",
                "codex_timeout_seconds", "returncode", "duration_seconds", "stderr_tail",
                "validator", "runtime_policy_gate",
            }, f"promoted attempt field set drift: {case_id}/{expected_index}")
            _require(attempt.get("returncode") == 0, f"promoted attempt return code mismatch: {case_id}")
            _require(str(attempt.get("validator") or "").startswith("checklist valid:"), f"promoted attempt validator did not pass: {case_id}")
            _require(gate.get("status") == "passed", f"promoted attempt runtime policy did not pass: {case_id}")
            _require("quarantine" not in attempt, f"promoted attempt cannot be quarantined: {case_id}")
        else:
            _require(
                gate.get("status") == "not_run"
                and gate.get("reason") == "drafter_nonzero_or_checklist_missing",
                f"only an audited infrastructure failure may be retried before "
                f"promotion: {case_id}/{expected_index}",
            )
            expected_attempt_fields = {
                "attempt_index", "max_output_tokens", "http_timeout_seconds",
                "codex_timeout_seconds", "returncode", "duration_seconds", "stderr_tail",
                "runtime_policy_gate", "quarantine",
            }
            _require(set(attempt) == expected_attempt_fields, f"rejected attempt field set drift: {case_id}/{expected_index}")
            quarantine_record = _validate_quarantined_attempt(
                    quarantine_root=quarantine_root,
                    case_id=case_id,
                    attempt_prefix=f"attempt_{expected_index:02d}",
                    attempt_record=attempt,
                    case_packet_path=packet_path,
                )
            _require(
                attempt.get("stderr_tail")
                == _stderr_tail(quarantine_root / case_id / f"attempt_{expected_index:02d}.stderr.log"),
                f"quarantined attempt stderr_tail binding drift: {case_id}/{expected_index}",
            )
            quarantined_attempts.append(quarantine_record)

    actual_names = {path.name for path in case_dir.iterdir()}
    _require(
        all(path.is_file() and not path.is_symlink() for path in case_dir.iterdir()),
        f"formal case contains a directory, symlink, or special file: {case_id}",
    )
    canonical_names = set(CANONICAL_SUFFIXES)
    successful_attempt_names = {
        f"attempt_{successful_index:02d}.{suffix}" for suffix in CANONICAL_SUFFIXES
    }
    _require(
        actual_names == canonical_names | successful_attempt_names,
        f"formal case must contain only canonical files and the promoted attempt: {case_id}",
    )
    attempt_groups: dict[int, set[str]] = {}
    for name in actual_names - canonical_names:
        match = _ATTEMPT_RE.fullmatch(name)
        _require(match is not None, f"unsupported formal artifact: {case_id}/{name}")
        attempt_groups.setdefault(int(match.group("index")), set()).add(match.group("suffix"))
    _require(set(attempt_groups) == {successful_index}, f"only the promoted attempt may remain in formal case dir: {case_id}")
    _require(attempt_groups[successful_index] == canonical_names, f"successful attempt seven-file bundle incomplete: {case_id}")
    for suffix in CANONICAL_SUFFIXES:
        _require(
            sha256_file(case_dir / suffix) == sha256_file(case_dir / f"attempt_{successful_index:02d}.{suffix}"),
            f"canonical file differs from promoted attempt: {case_id}/{suffix}",
        )
    _validate_no_symlinks(case_dir)
    _validate_no_secret_material(list(case_dir.iterdir()), case_id=case_id)
    _require(
        _mapping(attempts[-1], f"successful attempt {case_id}").get("stderr_tail")
        == _stderr_tail(case_dir / f"attempt_{successful_index:02d}.stderr.log"),
        f"promoted attempt stderr_tail binding drift: {case_id}",
    )

    quarantine_dir = quarantine_root / case_id
    if quarantined_attempts:
        _require(quarantine_dir.is_dir() and not quarantine_dir.is_symlink(), f"quarantine case directory missing: {case_id}")
        expected_quarantine_names = {
            name
            for record in quarantined_attempts
            for name in record["entry_names"]
        }
        _require(
            {path.name for path in quarantine_dir.iterdir()} == expected_quarantine_names,
            f"quarantine case inventory has extra/missing evidence: {case_id}",
        )
    else:
        _require(not quarantine_dir.exists(), f"case has quarantine evidence but no rejected attempt record: {case_id}")

    attempt_prefix = f"attempt_{successful_index:02d}"
    gate_audit = validate_appworld_v56_attempt_runtime_policy(
        case_packet_path=packet_path,
        case_dir=case_dir,
        attempt_prefix=attempt_prefix,
        attempt_record=_mapping(attempts[-1], f"successful attempt {case_id}"),
    )
    _require(
        _mapping(attempts[-1], f"successful attempt {case_id}").get("runtime_policy_gate")
        == gate_audit,
        f"stored promoted runtime-gate audit differs from independent recomputation: {case_id}",
    )
    support_count = int(gate_audit["support_pointer_count"])
    command_events = int(gate_audit["command_event_count"])
    usage = {key: int(value) for key, value in _mapping(gate_audit["token_usage"], "gate token usage").items()}
    canonical_hashes = {suffix: sha256_file(case_dir / suffix) for suffix in CANONICAL_SUFFIXES}
    attempt_hashes = {
        name: sha256_file(case_dir / name) for name in sorted(actual_names - canonical_names)
    }
    attempt_call_windows: list[dict[str, Any]] = []
    for rejected in quarantined_attempts:
        transport = _mapping(
            rejected.get("transport_audit"),
            f"rejected transport audit {case_id}/{rejected['attempt_index']}",
        )
        attempt_call_windows.append(
            {
                "attempt_index": rejected["attempt_index"],
                "response_id": transport.get("response_id"),
                "request_timestamp": transport.get("request_timestamp"),
                "response_timestamp": transport.get("response_timestamp"),
            }
        )
    promoted_llm = _load_mapping(
        case_dir / f"{attempt_prefix}.llm_call.json",
        f"promoted llm_call {case_id}",
    )
    promoted_metadata = _mapping(
        promoted_llm.get("response_metadata"), f"promoted metadata {case_id}"
    )
    attempt_call_windows.append(
        {
            "attempt_index": successful_index,
            "response_id": _string(
                promoted_metadata.get("response_id"), f"promoted response ID {case_id}"
            ),
            "request_timestamp": _string(
                promoted_llm.get("request_timestamp"), f"promoted request timestamp {case_id}"
            ),
            "response_timestamp": _string(
                promoted_llm.get("response_timestamp"), f"promoted response timestamp {case_id}"
            ),
        }
    )
    _require(
        [window["attempt_index"] for window in attempt_call_windows]
        == list(range(1, successful_index + 1)),
        f"attempt call-window indices are not contiguous: {case_id}",
    )
    previous_response: datetime | None = None
    for window in attempt_call_windows:
        request_value = window["request_timestamp"]
        response_value = window["response_timestamp"]
        if request_value is None or response_value is None:
            _require(
                request_value is None
                and response_value is None
                and window["response_id"] is None,
                f"attempt call window is partially unavailable: {case_id}/{window['attempt_index']}",
            )
            continue
        requested = _utc_timestamp(
            request_value, f"attempt request {case_id}/{window['attempt_index']}"
        )
        responded = _utc_timestamp(
            response_value, f"attempt response {case_id}/{window['attempt_index']}"
        )
        _require(requested <= responded, f"attempt response predates request: {case_id}")
        if previous_response is not None:
            _require(
                previous_response <= requested,
                f"attempt call windows overlap or run out of order: {case_id}",
            )
        previous_response = responded
    payload = {
        "case_unit_id": case_id,
        "task_id": case_id,
        "dataset_name": case["dataset_name"],
        "split": case["split"],
        "source_ref": case["source_ref"],
        "case_packet_sha256": sha256_file(packet_path),
        "raw_case_manifest_sha256": sha256_file(raw_manifest_path),
        "successful_attempt_index": successful_index,
        "promoted_runtime_policy_gate_sha256": sha256_object(gate_audit),
        "quarantined_attempt_count": len(quarantined_attempts),
        "quarantined_attempts": quarantined_attempts,
        "attempt_call_windows": attempt_call_windows,
        "support_pointer_count": support_count,
        "codex_command_event_count": command_events,
        "canonical_files": canonical_hashes,
        "attempt_files": attempt_hashes,
        "case_tree_sha256": sha256_path(case_dir),
    }
    return ({**payload, "case_draft_sha256": sha256_object(payload)}, usage, command_events)


def _canary_round_receipt_path(round_id: str) -> Path:
    _require(round_id in EXPECTED_PREFLIGHT_ROUNDS, f"unknown canary round: {round_id}")
    return resolve_repo_path(
        DEFAULT_DRAFT_ROOT / "provenance" / f"canary_{round_id}_receipt.json"
    ).resolve()


def _utc_timestamp(value: Any, label: str) -> datetime:
    parsed = _parse_timestamp(value, label)
    _require(
        parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0,
        f"{label} must use UTC",
    )
    _require(parsed <= datetime.now(timezone.utc), f"{label} is in the future")
    return parsed.astimezone(timezone.utc)


def _failed_v2_response_ids() -> set[str]:
    root = _input_directory(FAILED_V2_DRAFT_ROOT, "failed v2 diagnostic draft root")
    response_ids: set[str] = set()
    for path in sorted(root.rglob("*.api_response.json")):
        if path.is_symlink() or not path.is_file():
            continue
        payload = _load_mapping(path, f"failed v2 API response {path.name}")
        value = payload.get("id")
        if isinstance(value, str) and value:
            _require(value not in response_ids, f"failed v2 snapshot contains duplicate response ID: {value}")
            response_ids.add(value)
    _require(response_ids, "failed v2 diagnostic snapshot has no response IDs")
    return response_ids


def _failed_v3_canary_response_ids() -> set[str]:
    root = _input_directory(FAILED_V3_CANARY_ROOT, "failed v3 canary materialization")
    response_ids: set[str] = set()
    for path in sorted(root.rglob("attempt_*.api_response.json")):
        if path.is_symlink() or not path.is_file():
            continue
        payload = _load_mapping(path, f"failed v3 canary API response {path.name}")
        value = payload.get("id")
        if isinstance(value, str) and value:
            _require(
                value not in response_ids,
                f"failed v3 canary snapshot contains duplicate response ID: {value}",
            )
            response_ids.add(value)
    _require(
        len(response_ids) == 2,
        "failed v3 canary diagnostic snapshot must bind exactly two response IDs",
    )
    return response_ids


def _failed_v3_guardrail_response_ids() -> set[str]:
    root = _input_directory(
        FAILED_V3_GUARDRAIL_ROOT,
        "failed v3 guardrail materialization",
    )
    response_ids: set[str] = set()
    for path in sorted(root.rglob("attempt_*.api_response.json")):
        if path.is_symlink() or not path.is_file():
            continue
        payload = _load_mapping(path, f"failed v3 guardrail API response {path.name}")
        value = payload.get("id")
        if isinstance(value, str) and value:
            _require(
                value not in response_ids,
                f"failed v3 guardrail snapshot contains duplicate response ID: {value}",
            )
            response_ids.add(value)
    _require(
        len(response_ids) == 4,
        "failed v3 guardrail diagnostic snapshot must bind exactly four response IDs",
    )
    return response_ids


def _failed_v4_formal_response_ids() -> set[str]:
    root = _input_directory(FAILED_V4_FORMAL_ROOT, "failed v4 formal materialization")
    formal_cases_root = _input_directory(
        root
        / "draft_runs"
        / "codex-gpt-5.6-sol-xhigh-support-v3"
        / "cases",
        "failed v4 formal cases materialization",
    )
    response_ids: set[str] = set()
    # The failed namespace also contains 12 accepted canary responses under
    # draft_preflights.  Those are diagnostics, but they are not part of the
    # stopped 34-case formal run bound by the failure receipt.
    for path in sorted(formal_cases_root.rglob("attempt_*.api_response.json")):
        if path.is_symlink() or not path.is_file():
            continue
        payload = _load_mapping(path, f"failed v4 formal API response {path.name}")
        value = payload.get("id")
        if isinstance(value, str) and value:
            _require(
                value not in response_ids,
                f"failed v4 formal snapshot contains duplicate response ID: {value}",
            )
            response_ids.add(value)
    _require(
        len(response_ids) == 34,
        "failed v4 formal diagnostic snapshot must bind exactly 34 response IDs",
    )
    canonical_response_ids = "\n".join(sorted(response_ids)) + "\n"
    _require(
        sha256_bytes(canonical_response_ids.encode("utf-8"))
        == EXPECTED_FAILED_V4_FORMAL_RESPONSE_IDS_SHA256,
        "failed v4 formal response-ID set drifted",
    )
    return response_ids


def _failed_v5_canary_response_ids() -> set[str]:
    root = _input_directory(FAILED_V5_CANARY_ROOT, "failed v5 canary materialization")
    round_root = _input_directory(
        root
        / "draft_preflights"
        / "codex-gpt-5.6-sol-xhigh-support-v3-consecutive"
        / "round_01",
        "failed v5 canary round materialization",
    )
    response_ids: set[str] = set()
    for path in sorted(round_root.rglob("attempt_*.api_response.json")):
        if path.is_symlink() or not path.is_file():
            continue
        payload = _load_mapping(path, f"failed v5 canary API response {path.name}")
        value = payload.get("id")
        if isinstance(value, str) and value:
            _require(
                value not in response_ids,
                f"failed v5 canary snapshot contains duplicate response ID: {value}",
            )
            response_ids.add(value)
    _require(
        len(response_ids) == 8,
        "failed v5 canary diagnostic snapshot must bind exactly eight response IDs",
    )
    canonical_response_ids = "\n".join(sorted(response_ids)) + "\n"
    _require(
        sha256_bytes(canonical_response_ids.encode("utf-8"))
        == EXPECTED_FAILED_V5_CANARY_RESPONSE_IDS_SHA256,
        "failed v5 canary response-ID set drifted",
    )
    return response_ids


def _failed_response_ids() -> set[str]:
    failed_v2 = _failed_v2_response_ids()
    failed_v3 = _failed_v3_canary_response_ids()
    failed_v3_guardrail = _failed_v3_guardrail_response_ids()
    failed_v4_formal = _failed_v4_formal_response_ids()
    failed_v5_canary = _failed_v5_canary_response_ids()
    _require(
        failed_v2.isdisjoint(failed_v3)
        and failed_v2.isdisjoint(failed_v3_guardrail)
        and failed_v3.isdisjoint(failed_v3_guardrail),
        "failed diagnostic namespaces reuse a response ID",
    )
    predecessor_sets = (
        failed_v2,
        failed_v3,
        failed_v3_guardrail,
        failed_v4_formal,
        failed_v5_canary,
    )
    _require(
        all(
            left.isdisjoint(right)
            for index, left in enumerate(predecessor_sets)
            for right in predecessor_sets[index + 1 :]
        ),
        "failed diagnostic namespaces reuse a response ID",
    )
    return (
        failed_v2
        | failed_v3
        | failed_v3_guardrail
        | failed_v4_formal
        | failed_v5_canary
    )


def _validate_canary_round_output(*, round_id: str, lock: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute one strict eight-case, first-attempt-only canary round."""

    _require(round_id in EXPECTED_PREFLIGHT_ROUNDS, f"unknown canary round: {round_id}")
    plan = _mapping(lock.get("preflight"), "locked canary plan")
    round_plans = {
        _string(_mapping(item, "canary round plan").get("round_id"), "canary round ID"):
        _mapping(item, "canary round plan")
        for item in plan.get("rounds", [])
        if isinstance(item, Mapping)
    }
    round_plan = round_plans[round_id]
    cases_root = _input_directory(
        _string(round_plan.get("output_root"), f"{round_id} output root"),
        f"{round_id} output root",
    )
    quarantine_root = resolve_repo_path(
        _string(round_plan.get("quarantine_root"), f"{round_id} quarantine root")
    ).resolve()
    _require(not quarantine_root.exists(), f"{round_id} must have zero quarantine artifacts")
    _validate_no_symlinks(cases_root)

    entries = list(cases_root.iterdir())
    directories = {path.name for path in entries if path.is_dir() and not path.is_symlink()}
    files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    _require(directories == set(EXPECTED_PREFLIGHT_CASE_IDS), f"{round_id} canary case directory set mismatch")
    _require(files == _ROOT_BATCH_FILES, f"{round_id} canary root file inventory mismatch")
    terminal = _validate_phase_terminal_receipt(
        run_kind="canary", round_id=round_id, require_passed=True
    )
    summary_path = _input_file(cases_root / "_batch_summary.json", f"{round_id} batch summary")
    results_path = _input_file(cases_root / "_batch_results.jsonl", f"{round_id} batch results")
    summary = _load_mapping(summary_path, f"{round_id} batch summary")
    expected_summary_fields = {
        "started_at", "updated_at", "total_cases", "completed_cases", "success_cases",
        "skipped_cases", "failed_cases", "warning_count", "provider", "model",
        "reasoning_effort", "codex_sandbox", "prompt_supplement", "token_budgets",
        "sort_by", "quality_check", "large_case_threshold_bytes", "lane_stats",
        "output_root", "appworld_v56_runtime_gate", "runtime_policy_gate_schema",
        "runtime_policy_gate_policy", "runtime_policy_gate_counts",
        "regular_max_parallel", "oversized_max_parallel", "parsed_config_semantic_sha256",
        "batch_start_validation", "quarantined_attempt_count", "quarantine_root",
    }
    _require(set(summary) == expected_summary_fields, f"{round_id} batch summary field set drift")
    started = _utc_timestamp(summary.get("started_at"), f"{round_id} started_at")
    completed = _utc_timestamp(summary.get("updated_at"), f"{round_id} updated_at")
    _require(
        _utc_timestamp(terminal["phase_start"]["started_at"], f"{round_id} phase started_at")
        <= started
        <= completed
        <= _utc_timestamp(terminal["completed_at"], f"{round_id} phase completed_at"),
        f"{round_id} phase/batch time order is invalid",
    )
    expected_summary = {
        "total_cases": len(EXPECTED_PREFLIGHT_CASE_IDS),
        "completed_cases": len(EXPECTED_PREFLIGHT_CASE_IDS),
        "success_cases": len(EXPECTED_PREFLIGHT_CASE_IDS),
        "skipped_cases": 0,
        "failed_cases": 0,
        "warning_count": 0,
        "provider": "codex",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "codex_sandbox": EXPECTED_CODEX_SANDBOX,
        "prompt_supplement": _repo_relative(
            _IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"]
        ),
        "token_budgets": list(EXPECTED_TOKEN_BUDGETS),
        "sort_by": "size",
        "quality_check": "none",
        "large_case_threshold_bytes": EXPECTED_LARGE_THRESHOLD_BYTES,
        "output_root": _repo_relative(cases_root),
        "appworld_v56_runtime_gate": True,
        "runtime_policy_gate_schema": RUNTIME_GATE_SCHEMA,
        "runtime_policy_gate_policy": EVENT_COMMAND_POLICY,
        "runtime_policy_gate_counts": {
            "passed": len(EXPECTED_PREFLIGHT_CASE_IDS),
            "failed": 0,
            "not_run": 0,
        },
        "regular_max_parallel": 8,
        "oversized_max_parallel": 8,
        "quarantined_attempt_count": 0,
        "quarantine_root": _repo_relative(quarantine_root),
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"{round_id} batch summary {key} mismatch")
    lane_stats = _mapping(summary.get("lane_stats"), f"{round_id} lane stats")
    _require(
        _mapping(lane_stats.get("regular"), f"{round_id} regular lane").get("count")
        == EXPECTED_PREFLIGHT_LANE_COUNTS["regular"]
        and _mapping(lane_stats.get("oversized"), f"{round_id} oversized lane").get("count")
        == EXPECTED_PREFLIGHT_LANE_COUNTS["oversized"],
        f"{round_id} canary lane counts drift",
    )

    start_audit = _mapping(summary.get("batch_start_validation"), f"{round_id} batch start validation")
    _require(set(start_audit) == {
        "schema_version", "status", "run_kind", "canary_round", "pre_run_lock_sha256",
        "prior_round_receipt_sha256", "canary_acceptance_sha256",
        "parsed_config_semantic_sha256", "parsed_config", "login_status_at_batch_start",
        "environment_semantic_sha256", "python_executable_sha256", "codex_executable_sha256",
        "phase_start_receipt_path", "phase_start_receipt_sha256",
        "invocation_argv_semantic_sha256",
    }, f"{round_id} batch-start audit field set drift")
    _require(
        dict(start_audit) == terminal["phase_start"]["batch_start_validation"],
        f"{round_id} batch-start audit differs from its immutable phase-start receipt",
    )
    _require(
        start_audit.get("schema_version") == "appworld_v56_batch_start_validation.v2"
        and start_audit.get("status") == "passed"
        and start_audit.get("run_kind") == "canary"
        and start_audit.get("canary_round") == round_id
        and start_audit.get("canary_acceptance_sha256") is None,
        f"{round_id} batch-start phase identity drift",
    )
    _require(
        start_audit.get("pre_run_lock_sha256") == sha256_file(_input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")),
        f"{round_id} batch-start lock binding drift",
    )
    round_index = EXPECTED_PREFLIGHT_ROUNDS.index(round_id)
    expected_prior = (
        sha256_file(_input_file(_canary_round_receipt_path(EXPECTED_PREFLIGHT_ROUNDS[round_index - 1]), "prior canary receipt"))
        if round_index
        else None
    )
    _require(start_audit.get("prior_round_receipt_sha256") == expected_prior, f"{round_id} predecessor receipt binding drift")
    parsed_config = _mapping(start_audit.get("parsed_config"), f"{round_id} parsed config")
    canonical_config = _validate_v56_parsed_config(parsed_config, lock=lock, require_clean_roots=False)
    _require(dict(parsed_config) == canonical_config, f"{round_id} stored parsed config drift")
    _require(
        start_audit.get("parsed_config_semantic_sha256") == sha256_object(dict(parsed_config))
        == summary.get("parsed_config_semantic_sha256"),
        f"{round_id} parsed config hash drift",
    )

    rows = _load_jsonl(results_path, f"{round_id} batch results")
    _require(
        len(rows) == len(EXPECTED_PREFLIGHT_CASE_IDS),
        f"{round_id} canary result count drift",
    )
    by_id = {_string(row.get("case_unit_dir"), f"{round_id} row case ID"): row for row in rows}
    _require(
        len(by_id) == len(EXPECTED_PREFLIGHT_CASE_IDS)
        and set(by_id) == set(EXPECTED_PREFLIGHT_CASE_IDS),
        f"{round_id} result IDs drift",
    )
    _require(all(row.get("status") == "success" for row in rows), f"{round_id} contains a non-success row")
    _require(Counter(str(row.get("lane")) for row in rows) == Counter(EXPECTED_PREFLIGHT_LANE_COUNTS), f"{round_id} result lane counts drift")
    for row in rows:
        attempts = row.get("attempts")
        _require(isinstance(attempts, list) and len(attempts) == 1, f"{round_id} is not a first-attempt-only pass")
        gate = _mapping(_mapping(attempts[0], f"{round_id} first attempt").get("runtime_policy_gate"), f"{round_id} first gate")
        _require(gate.get("status") == "passed", f"{round_id} first attempt did not pass the runtime/semantic gate")

    manifest_cases = _manifest_cases(_input_file(_INPUT_PATHS["manifest"], "extension manifest"))
    manifest_by_id = {case["case_unit_id"]: case for case in manifest_cases}
    packet_root = _input_directory(_mapping(lock.get("inputs"), "locked inputs")["case_packet_root"], "packet root")
    records: list[dict[str, Any]] = []
    response_ids: list[str] = []
    request_times: list[datetime] = []
    response_times: list[datetime] = []
    for case_id in EXPECTED_PREFLIGHT_CASE_IDS:
        record, _, _ = _validate_case(
            case=manifest_by_id[case_id],
            case_dir=cases_root / case_id,
            packet_dir=packet_root / case_id,
            result_row=by_id[case_id],
            quarantine_root=quarantine_root,
        )
        records.append(record)
        api = _load_mapping(cases_root / case_id / "api_response.json", f"{round_id} API {case_id}")
        response_id = _string(api.get("id"), f"{round_id} response ID {case_id}")
        response_ids.append(response_id)
        llm = _load_mapping(cases_root / case_id / "llm_call.json", f"{round_id} llm_call {case_id}")
        request_at = _utc_timestamp(llm.get("request_timestamp"), f"{round_id}/{case_id} request_timestamp")
        response_at = _utc_timestamp(llm.get("response_timestamp"), f"{round_id}/{case_id} response_timestamp")
        _require(started <= request_at <= response_at <= completed, f"{round_id}/{case_id} call lies outside its batch window")
        request_times.append(request_at)
        response_times.append(response_at)
    _require(
        len(response_ids) == len(EXPECTED_PREFLIGHT_CASE_IDS)
        and len(set(response_ids)) == len(EXPECTED_PREFLIGHT_CASE_IDS),
        f"{round_id} response/thread IDs are not unique",
    )
    _require(
        set(response_ids).isdisjoint(_failed_response_ids()),
        f"{round_id} reuses a failed diagnostic response ID",
    )
    return {
        "schema_version": "appworld_draft_canary_round_validation.v1",
        "status": "passed",
        "round_id": round_id,
        "started_at": summary["started_at"],
        "completed_at": summary["updated_at"],
        "output_root": _repo_relative(cases_root),
        "output_tree_sha256": sha256_path(cases_root),
        "quarantine_root": _repo_relative(quarantine_root),
        "quarantine_absent": True,
        "summary_path": _repo_relative(summary_path),
        "summary_sha256": sha256_file(summary_path),
        "results_path": _repo_relative(results_path),
        "results_sha256": sha256_file(results_path),
        "case_ids": list(EXPECTED_PREFLIGHT_CASE_IDS),
        "case_count_by_dataset": dict(EXPECTED_PREFLIGHT_CASE_COUNT_BY_DATASET),
        "lane_counts": dict(EXPECTED_PREFLIGHT_LANE_COUNTS),
        "first_attempt_pass_count": len(EXPECTED_PREFLIGHT_CASE_IDS),
        "rejected_attempt_count": 0,
        "response_ids": response_ids,
        "earliest_request_at": min(request_times).isoformat(),
        "latest_response_at": max(response_times).isoformat(),
        "case_records": records,
        "case_records_semantic_sha256": sha256_object(records),
        "phase_start_receipt": {
            "path": terminal["phase_start"]["receipt_path"],
            "sha256": terminal["phase_start"]["receipt_sha256"],
        },
        "phase_terminal_receipt": {
            "path": terminal["receipt_path"],
            "sha256": terminal["receipt_sha256"],
        },
    }


def write_appworld_v56_canary_round_receipt(*, round_id: str) -> dict[str, Any]:
    """Exclusively lock one completed round; a failed round can never be rewritten."""

    receipt_path = _canary_round_receipt_path(round_id)
    _require(not receipt_path.exists(), f"canary round receipt already exists: {receipt_path}")
    _require(not resolve_repo_path(DEFAULT_CANARY_ACCEPTANCE_PATH).exists(), "sequence receipt already exists")
    lock_path = _input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")
    lock = _load_mapping(lock_path, "v4 pre-run lock")
    validate_appworld_draft_pre_run_lock_v56(lock_path=lock_path)
    index = EXPECTED_PREFLIGHT_ROUNDS.index(round_id)
    previous_ref: dict[str, str] | None = None
    if index:
        previous = validate_appworld_v56_canary_round_receipt(
            round_id=EXPECTED_PREFLIGHT_ROUNDS[index - 1]
        )
        previous_ref = {
            "path": previous["receipt_path"],
            "sha256": previous["receipt_sha256"],
        }
    for later in EXPECTED_PREFLIGHT_ROUNDS[index + 1 :]:
        _require(not _canary_round_receipt_path(later).exists(), f"later canary receipt pre-exists {round_id}: {later}")
    validation = _validate_canary_round_output(round_id=round_id, lock=lock)
    locked_at = _utc_timestamp(lock.get("locked_at"), "pre-run locked_at")
    started = _utc_timestamp(validation["started_at"], f"{round_id} started_at")
    _require(locked_at <= started, f"{round_id} started before the immutable lock")
    if index:
        previous_payload = _load_mapping(_canary_round_receipt_path(EXPECTED_PREFLIGHT_ROUNDS[index - 1]), "previous canary receipt")
        previous_validated = _utc_timestamp(previous_payload.get("validated_at"), "previous receipt validated_at")
        _require(previous_validated < started, f"{round_id} did not start strictly after the previous receipt")
    receipt = {
        "schema_version": "appworld_draft_canary_round_receipt.v1",
        "status": "passed_locked",
        "validated_at": _utc_now(),
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "lock_path": _repo_relative(lock_path),
        "lock_sha256": sha256_file(lock_path),
        "round_id": round_id,
        "previous_round_receipt": previous_ref,
        "round_validation": validation,
        "round_validation_semantic_sha256": sha256_object(validation),
    }
    _write_json_exclusive(receipt_path, receipt)
    return {
        "status": "passed_locked",
        "round_id": round_id,
        "receipt_path": _repo_relative(receipt_path),
        "receipt_sha256": sha256_file(receipt_path),
        "output_tree_sha256": validation["output_tree_sha256"],
    }


def validate_appworld_v56_canary_round_receipt(*, round_id: str) -> dict[str, Any]:
    receipt_path = _input_file(_canary_round_receipt_path(round_id), f"{round_id} canary receipt")
    receipt = _load_mapping(receipt_path, f"{round_id} canary receipt")
    _require(set(receipt) == {
        "schema_version", "status", "validated_at", "draft_run_id", "lock_path", "lock_sha256",
        "round_id", "previous_round_receipt", "round_validation", "round_validation_semantic_sha256",
    }, f"{round_id} receipt field set drift")
    _require(
        receipt.get("schema_version") == "appworld_draft_canary_round_receipt.v1"
        and receipt.get("status") == "passed_locked"
        and receipt.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID
        and receipt.get("round_id") == round_id,
        f"{round_id} receipt identity drift",
    )
    validated_at = _utc_timestamp(receipt.get("validated_at"), f"{round_id} receipt validated_at")
    lock_path = _input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")
    _require(
        receipt.get("lock_path") == _repo_relative(lock_path)
        and receipt.get("lock_sha256") == sha256_file(lock_path),
        f"{round_id} receipt lock binding drift",
    )
    lock = _load_mapping(lock_path, "v4 pre-run lock")
    index = EXPECTED_PREFLIGHT_ROUNDS.index(round_id)
    if index:
        previous = validate_appworld_v56_canary_round_receipt(
            round_id=EXPECTED_PREFLIGHT_ROUNDS[index - 1]
        )
        _require(receipt.get("previous_round_receipt") == {
            "path": previous["receipt_path"], "sha256": previous["receipt_sha256"]
        }, f"{round_id} previous receipt reference drift")
        previous_payload = _load_mapping(_canary_round_receipt_path(EXPECTED_PREFLIGHT_ROUNDS[index - 1]), "previous canary receipt")
        _require(
            _utc_timestamp(previous_payload.get("validated_at"), "previous receipt validated_at")
            < _utc_timestamp(_mapping(receipt.get("round_validation"), "stored round validation").get("started_at"), f"{round_id} stored started_at"),
            f"{round_id} is not strictly consecutive after its predecessor receipt",
        )
    else:
        _require(receipt.get("previous_round_receipt") is None, "round_01 cannot reference a predecessor")
    current = _validate_canary_round_output(round_id=round_id, lock=lock)
    stored = _mapping(receipt.get("round_validation"), f"{round_id} stored validation")
    _require(dict(stored) == current, f"{round_id} output validation drifted after receipt")
    _require(receipt.get("round_validation_semantic_sha256") == sha256_object(current), f"{round_id} validation hash drift")
    _require(_utc_timestamp(current["completed_at"], f"{round_id} completed_at") <= validated_at, f"{round_id} receipt predates completion")
    return {
        "status": "verified",
        "round_id": round_id,
        "receipt_path": _repo_relative(receipt_path),
        "receipt_sha256": sha256_file(receipt_path),
        "output_tree_sha256": current["output_tree_sha256"],
        "started_at": current["started_at"],
        "completed_at": current["completed_at"],
        "validated_at": receipt["validated_at"],
        "response_ids": current["response_ids"],
    }


def write_appworld_v56_canary_acceptance(
    *, receipt_path: str | Path = DEFAULT_CANARY_ACCEPTANCE_PATH
) -> dict[str, Any]:
    """Lock the three-round consecutive sequence before the formal namespace can start."""

    output = resolve_repo_path(receipt_path).resolve()
    _require(output == resolve_repo_path(DEFAULT_CANARY_ACCEPTANCE_PATH).resolve(), "canary sequence receipt path is noncanonical")
    _require(not output.exists(), f"canary sequence receipt already exists: {output}")
    _require(not resolve_repo_path(DEFAULT_CASES_ROOT).exists(), "formal cases root exists before canary acceptance")
    lock_path = _input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")
    validate_appworld_draft_pre_run_lock_v56(lock_path=lock_path)
    _validate_canary_acceptance_namespace(receipt_exists=False)
    rounds = [validate_appworld_v56_canary_round_receipt(round_id=value) for value in EXPECTED_PREFLIGHT_ROUNDS]
    response_ids = [value for record in rounds for value in record["response_ids"]]
    expected_response_count = len(EXPECTED_PREFLIGHT_CASE_IDS) * len(
        EXPECTED_PREFLIGHT_ROUNDS
    )
    _require(
        len(response_ids) == expected_response_count
        and len(set(response_ids)) == expected_response_count,
        "canary response IDs are not globally unique",
    )
    _require(
        set(response_ids).isdisjoint(_failed_response_ids()),
        "canary sequence reuses a failed diagnostic response ID",
    )
    receipt = {
        "schema_version": CANARY_ACCEPTANCE_SCHEMA,
        "status": "passed_locked",
        "validated_at": _utc_now(),
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "lock_path": _repo_relative(lock_path),
        "lock_sha256": sha256_file(lock_path),
        "round_ids": list(EXPECTED_PREFLIGHT_ROUNDS),
        "round_receipts": rounds,
        "round_receipts_semantic_sha256": sha256_object(rounds),
        "response_ids": response_ids,
        "response_ids_semantic_sha256": sha256_object(response_ids),
        "first_attempt_pass_count": expected_response_count,
        "rejected_attempt_count": 0,
        "all_required_gates_passed": True,
    }
    _write_json_exclusive(output, receipt)
    return {
        "status": "passed_locked",
        "receipt_path": _repo_relative(output),
        "receipt_sha256": sha256_file(output),
        "round_count": len(EXPECTED_PREFLIGHT_ROUNDS),
        "first_attempt_pass_count": expected_response_count,
    }


def validate_appworld_v56_canary_acceptance(
    *, receipt_path: str | Path = DEFAULT_CANARY_ACCEPTANCE_PATH
) -> dict[str, Any]:
    output = _input_file(receipt_path, "canary sequence receipt")
    _require(output == resolve_repo_path(DEFAULT_CANARY_ACCEPTANCE_PATH).resolve(), "canary sequence receipt path is noncanonical")
    _validate_canary_acceptance_namespace(receipt_exists=True)
    receipt = _load_mapping(output, "canary sequence receipt")
    _require(set(receipt) == {
        "schema_version", "status", "validated_at", "draft_run_id", "lock_path", "lock_sha256",
        "round_ids", "round_receipts", "round_receipts_semantic_sha256", "response_ids",
        "response_ids_semantic_sha256", "first_attempt_pass_count", "rejected_attempt_count",
        "all_required_gates_passed",
    }, "canary sequence receipt field set drift")
    _require(
        receipt.get("schema_version") == CANARY_ACCEPTANCE_SCHEMA
        and receipt.get("status") == "passed_locked"
        and receipt.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID
        and receipt.get("round_ids") == list(EXPECTED_PREFLIGHT_ROUNDS)
        and receipt.get("first_attempt_pass_count")
        == len(EXPECTED_PREFLIGHT_CASE_IDS) * len(EXPECTED_PREFLIGHT_ROUNDS)
        and receipt.get("rejected_attempt_count") == 0
        and receipt.get("all_required_gates_passed") is True,
        "canary sequence receipt identity/count drift",
    )
    validated_at = _utc_timestamp(receipt.get("validated_at"), "canary sequence validated_at")
    lock_path = _input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")
    _require(receipt.get("lock_path") == _repo_relative(lock_path) and receipt.get("lock_sha256") == sha256_file(lock_path), "canary sequence lock binding drift")
    rounds = [validate_appworld_v56_canary_round_receipt(round_id=value) for value in EXPECTED_PREFLIGHT_ROUNDS]
    _require(receipt.get("round_receipts") == rounds, "canary sequence round receipts drift")
    _require(receipt.get("round_receipts_semantic_sha256") == sha256_object(rounds), "canary round-receipt aggregate hash drift")
    response_ids = [value for record in rounds for value in record["response_ids"]]
    expected_response_count = len(EXPECTED_PREFLIGHT_CASE_IDS) * len(
        EXPECTED_PREFLIGHT_ROUNDS
    )
    _require(
        receipt.get("response_ids") == response_ids
        and len(response_ids) == expected_response_count
        and len(set(response_ids)) == expected_response_count,
        "canary sequence response identity drift",
    )
    _require(receipt.get("response_ids_semantic_sha256") == sha256_object(response_ids), "canary response-ID hash drift")
    _require(
        set(response_ids).isdisjoint(_failed_response_ids()),
        "canary sequence reuses failed diagnostic response identity",
    )
    _require(_utc_timestamp(rounds[-1]["validated_at"], "round_03 receipt validated_at") <= validated_at, "canary sequence receipt predates round_03 receipt")
    return {
        "status": "verified",
        "receipt_path": _repo_relative(output),
        "receipt_sha256": sha256_file(output),
        "round_count": 3,
        "first_attempt_pass_count": expected_response_count,
        "response_ids": response_ids,
    }


def _classify_audited_infra_retry(
    *,
    api_response: Mapping[str, Any],
    attempt_record: Mapping[str, Any],
    suffixes: frozenset[str],
    case_id: str,
    attempt_prefix: str,
) -> dict[str, Any]:
    """Classify only pre-result Codex transport failures as retryable infra.

    Schema, checklist, AppWorld semantic, tool-policy, and completed-model-output
    failures are deliberately not retryable.  This helper is called both before
    a runner retry and again from final acceptance over quarantined bytes.
    """

    expected_suffixes = frozenset(
        {
            "api_response.json",
            "llm_call.json",
            "reasoning_summary.txt",
            "stderr.log",
            "stdout.log",
        }
    )
    gate = _mapping(
        attempt_record.get("runtime_policy_gate"),
        f"infra-retry runtime gate {case_id}/{attempt_prefix}",
    )
    _require(
        gate
        == {
            "schema_version": RUNTIME_GATE_SCHEMA,
            "status": "not_run",
            "policy": EVENT_COMMAND_POLICY,
            "reason": "drafter_nonzero_or_checklist_missing",
        },
        f"infra retry requires an exact pre-validator drafter rejection: "
        f"{case_id}/{attempt_prefix}",
    )
    codex = _mapping(
        api_response.get("codex_cli"),
        f"infra-retry Codex transport {case_id}/{attempt_prefix}",
    )
    events = codex.get("events")
    _require(
        isinstance(events, list) and all(isinstance(event, Mapping) for event in events),
        f"infra-retry event stream is invalid: {case_id}/{attempt_prefix}",
    )
    agent_message_count = sum(
        1
        for event in events
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), Mapping)
        and _mapping(
            event.get("item"), f"infra-retry event item {case_id}"
        ).get("type")
        == "agent_message"
    )
    codex_returncode = codex.get("returncode")
    stderr = codex.get("stderr")
    _require(
        isinstance(stderr, str),
        f"infra-retry Codex stderr is not text: {case_id}/{attempt_prefix}",
    )
    reason: str | None = None
    if codex_returncode == 124:
        reason = "codex_subprocess_timeout"
    else:
        reason = next(
            (
                label
                for label, pattern in _INFRA_RETRY_PATTERNS
                if pattern.search(stderr)
            ),
            None,
        )
    retryable = (
        api_response.get("status") == "failed"
        and type(attempt_record.get("returncode")) is int
        and attempt_record.get("returncode") != 0
        and type(codex_returncode) is int
        and codex_returncode != 0
        and suffixes == expected_suffixes
        and api_response.get("output_text") == "{}"
        and agent_message_count == 0
        and reason is not None
    )
    payload = {
        "schema_version": INFRA_RETRY_SCHEMA,
        "status": "retryable_infrastructure_failure" if retryable else "not_retryable",
        "retryable": retryable,
        "reason": reason or "not_allowlisted_infrastructure_failure",
        "case_unit_id": case_id,
        "attempt_prefix": attempt_prefix,
        "drafter_returncode": attempt_record.get("returncode"),
        "codex_returncode": codex_returncode,
        "response_status": api_response.get("status"),
        "agent_message_count": agent_message_count,
        "artifact_suffixes": sorted(suffixes),
        "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
    }
    return {**payload, "classification_semantic_sha256": sha256_object(payload)}


def classify_appworld_v56_infra_retry(
    *,
    case_packet_path: str | Path,
    case_dir: str | Path,
    attempt_prefix: str,
    attempt_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit and classify one rejected live attempt before allowing a retry."""

    match = re.fullmatch(r"attempt_([0-9]{2})", attempt_prefix)
    _require(match is not None, "infra-retry attempt prefix must be attempt_NN")
    attempt_index = int(match.group(1))
    _require(
        attempt_record.get("attempt_index") == attempt_index,
        "infra-retry attempt record index mismatch",
    )
    packet_path = _input_file(case_packet_path, "infra-retry case packet")
    packet_dir = packet_path.parent
    raw_manifest_path = _input_file(
        packet_dir / "raw_case_manifest.json", "infra-retry raw manifest"
    )
    raw_manifest = _load_mapping(raw_manifest_path, "infra-retry raw manifest")
    case_id = _string(raw_manifest.get("case_unit_id"), "infra-retry case ID")
    output_dir = _input_directory(case_dir, f"infra-retry output {case_id}")
    _require(
        packet_path.name == "case_packet.md"
        and packet_dir.name == output_dir.name == case_id,
        f"infra-retry packet/output identity mismatch: {case_id}",
    )
    lock_binding = _validate_runtime_gate_lock_binding(
        case_id=case_id,
        packet_path=packet_path,
        raw_manifest_path=raw_manifest_path,
        output_dir=output_dir,
        allow_nonformal_output=False,
    )
    prefixed = sorted(output_dir.glob(f"{attempt_prefix}.*"), key=lambda path: path.name)
    _require(
        prefixed
        and all(path.is_file() and not path.is_symlink() for path in prefixed),
        f"infra-retry attempt artifacts are missing or unsafe: {case_id}/{attempt_prefix}",
    )
    suffixes: set[str] = set()
    for path in prefixed:
        parsed = _ATTEMPT_RE.fullmatch(path.name)
        _require(
            parsed is not None and path.name.startswith(f"{attempt_prefix}."),
            f"infra-retry attempt artifact is unsupported: {case_id}/{path.name}",
        )
        suffixes.add(_string(parsed.group("suffix"), "infra-retry suffix"))
    frozen_suffixes = frozenset(suffixes)
    _validate_no_secret_material(prefixed, case_id=case_id)
    transport = _validate_rejected_codex_transport(
        expected_dir=output_dir,
        sidecar_origin_dir=Path(lock_binding["sidecar_origin_case_dir"]),
        case_id=case_id,
        attempt_prefix=attempt_prefix,
        attempt_record=attempt_record,
        suffixes=frozen_suffixes,
        case_packet_path=packet_path,
    )
    api_response = _load_mapping(
        output_dir / f"{attempt_prefix}.api_response.json",
        f"infra-retry API {case_id}/{attempt_prefix}",
    )
    classification = _classify_audited_infra_retry(
        api_response=api_response,
        attempt_record=attempt_record,
        suffixes=frozen_suffixes,
        case_id=case_id,
        attempt_prefix=attempt_prefix,
    )
    payload = {
        **classification,
        "transport_audit_sha256": transport["transport_audit_sha256"],
        "pre_run_lock_sha256": lock_binding["pre_run_lock_sha256"],
    }
    return {**payload, "audit_semantic_sha256": sha256_object(payload)}


def _validate_rejected_codex_transport(
    *,
    expected_dir: Path,
    sidecar_origin_dir: Path,
    case_id: str,
    attempt_prefix: str,
    attempt_record: Mapping[str, Any],
    suffixes: frozenset[str],
    case_packet_path: Path,
) -> dict[str, Any]:
    """Audit every preserved Codex event stream, independent of checklist validity."""

    api_suffix = "api_response.json"
    if api_suffix not in suffixes:
        raise ContractLifecycleError(
            f"rejected attempt has no auditable Codex API/event sidecar; the namespace "
            f"cannot be accepted: {case_id}/{attempt_prefix}"
        )
    api_path = _input_file(
        expected_dir / f"{attempt_prefix}.api_response.json",
        f"rejected API response {case_id}/{attempt_prefix}",
    )
    api_response = _load_mapping(api_path, f"rejected API response {case_id}/{attempt_prefix}")
    _require(
        set(api_response)
        == {"id", "status", "model", "provider", "output_text", "output", "usage", "codex_cli"},
        f"rejected API sidecar field set drift: {case_id}/{attempt_prefix}",
    )
    response_id = _string(api_response.get("id"), f"rejected response ID {case_id}/{attempt_prefix}")
    response_status = _string(api_response.get("status"), f"rejected response status {case_id}/{attempt_prefix}")
    _require(
        response_status in {"completed", "failed"}
        and api_response.get("provider") == "codex_cli"
        and api_response.get("model") == EXPECTED_MODEL,
        f"rejected API provider/model/status drift: {case_id}/{attempt_prefix}",
    )
    codex = _mapping(api_response.get("codex_cli"), f"rejected codex_cli {case_id}/{attempt_prefix}")
    _require(
        set(codex)
        == {
            "auth_mode",
            "returncode",
            "timeout_seconds",
            "sandbox",
            "command",
            "stdin_bundle",
            "events",
            "malformed_event_lines",
            "stderr",
        },
        f"rejected Codex transport field set drift: {case_id}/{attempt_prefix}",
    )
    _require(
        codex.get("auth_mode") == "codex_login"
        and codex.get("sandbox") == EXPECTED_CODEX_SANDBOX
        and codex.get("timeout_seconds") == attempt_record.get("codex_timeout_seconds")
        and type(codex.get("returncode")) is int
        and codex.get("malformed_event_lines") == []
        and isinstance(codex.get("stderr"), str),
        f"rejected Codex transport provenance drift: {case_id}/{attempt_prefix}",
    )
    if response_status == "completed":
        _require(codex.get("returncode") == 0, f"completed rejected Codex call has nonzero return: {case_id}/{attempt_prefix}")
    events = codex.get("events")
    _require(
        isinstance(events, list) and events and all(isinstance(event, Mapping) for event in events),
        f"rejected Codex event stream is empty/invalid: {case_id}/{attempt_prefix}",
    )
    _validate_codex_event_type_policy(events=events, case_id=case_id)
    _validate_codex_argv(codex.get("command"), case_id=case_id)
    stdin_bundle = _validate_direct_stdin_bundle(
        metadata=_mapping(codex.get("stdin_bundle"), f"rejected stdin bundle {case_id}"),
        expected_workspace_files=_expected_codex_workspace_files(
            packet_path=case_packet_path
        ),
        case_id=case_id,
    )
    thread_started = [event for event in events if event.get("type") == "thread.started"]
    _require(
        len(thread_started) == 1
        and events[0] is thread_started[0]
        and thread_started[0].get("thread_id") == response_id,
        f"rejected Codex thread identity/lifecycle drift: {case_id}/{attempt_prefix}",
    )
    if response_status == "completed":
        _validate_codex_event_lifecycle(
            events=events, response_id=response_id, case_id=case_id
        )
        event_audit = _validate_direct_stdin_events(events=events, case_id=case_id)
        command_event_count = 0
    else:
        item_events = [
            event for event in events if str(event.get("type")).startswith("item.")
        ]
        command_event_count = 0
        event_audit = {
            "policy": EVENT_COMMAND_POLICY,
            "event_count": len(events),
            "item_event_count": len(item_events),
            "agent_message_count": sum(
                1
                for event in item_events
                if _mapping(event.get("item"), f"rejected item {case_id}").get("type")
                == "agent_message"
            ),
            "tool_item_count": 0,
            "command_event_count": 0,
            "turn_completed": any(
                event.get("type") == "turn.completed" for event in events
            ),
        }
        event_audit = {
            **event_audit,
            "event_semantic_sha256": sha256_object(event_audit),
        }

    reasoning_fragments = minimal_drafter.extract_codex_reasoning_fragments(
        [dict(event) for event in events]
    )
    output_text = _string(api_response.get("output_text"), f"rejected output_text {case_id}")
    _require(
        api_response.get("output")
        == [
            {
                "type": "reasoning",
                "summary": [
                    {"type": "summary_text", "text": text}
                    for text in reasoning_fragments
                ],
            },
            {
                "type": "message",
                "content": [{"type": "output_text", "text": output_text}],
            },
        ]
        and _mapping(api_response.get("usage"), f"rejected usage {case_id}")
        == minimal_drafter.normalize_codex_usage([dict(event) for event in events]),
        f"rejected API response is not the exact event projection: {case_id}/{attempt_prefix}",
    )

    request_timestamp: str | None = None
    response_timestamp: str | None = None
    llm_required = {"llm_call.json", "reasoning_summary.txt"}
    if llm_required <= suffixes:
        llm_path = _input_file(
            expected_dir / f"{attempt_prefix}.llm_call.json",
            f"rejected llm_call {case_id}/{attempt_prefix}",
        )
        reasoning_path = _input_file(
            expected_dir / f"{attempt_prefix}.reasoning_summary.txt",
            f"rejected reasoning {case_id}/{attempt_prefix}",
        )
        llm_call = _load_mapping(llm_path, f"rejected llm_call {case_id}/{attempt_prefix}")
        _require(
            set(llm_call)
            == {
                "schema_version", "provider", "model", "model_version", "api_key_env",
                "domain", "case_unit_id", "task_id", "phase", "experiment_type",
                "agent_id_or_role", "request_timestamp", "response_timestamp", "temperature",
                "max_tokens", "timeout_seconds", "retry_index", "token_usage", "cost",
                "response_metadata",
            },
            f"rejected llm_call field set drift: {case_id}/{attempt_prefix}",
        )
        for key, expected in (
            ("schema_version", "llm_call/v1"),
            ("provider", "codex_cli"),
            ("model", EXPECTED_MODEL),
            ("model_version", EXPECTED_MODEL),
            ("api_key_env", "CODEX_HOME"),
            ("domain", "appworld"),
            ("case_unit_id", case_id),
            ("task_id", case_id),
            ("phase", "draft"),
            ("experiment_type", "minimal_package"),
            ("agent_id_or_role", "case_checklist_drafter"),
            ("temperature", 0.0),
            ("max_tokens", attempt_record.get("max_output_tokens")),
            ("timeout_seconds", attempt_record.get("codex_timeout_seconds")),
            ("retry_index", 0),
        ):
            _require(llm_call.get(key) == expected, f"rejected llm_call.{key} drift: {case_id}/{attempt_prefix}")
        requested = _utc_timestamp(llm_call.get("request_timestamp"), f"rejected request {case_id}/{attempt_prefix}")
        responded = _utc_timestamp(llm_call.get("response_timestamp"), f"rejected response {case_id}/{attempt_prefix}")
        _require(requested <= responded, f"rejected response predates request: {case_id}/{attempt_prefix}")
        request_timestamp = str(llm_call["request_timestamp"])
        response_timestamp = str(llm_call["response_timestamp"])
        metadata = _mapping(llm_call.get("response_metadata"), f"rejected metadata {case_id}")
        _require(
            metadata.get("response_id") == response_id
            and metadata.get("response_status") == response_status
            and metadata.get("provider_model") == EXPECTED_MODEL
            and metadata.get("reasoning_effort") == EXPECTED_REASONING_EFFORT
            and metadata.get("auth_mode") == "codex_login"
            and metadata.get("raw_api_response_path")
            == str(sidecar_origin_dir / f"{attempt_prefix}.api_response.json")
            and metadata.get("reasoning_summary_path")
            == str(sidecar_origin_dir / f"{attempt_prefix}.reasoning_summary.txt"),
            f"rejected llm_call metadata/path binding drift: {case_id}/{attempt_prefix}",
        )
        _require(
            dict(_mapping(llm_call.get("token_usage"), f"rejected token usage {case_id}"))
            == minimal_drafter.extract_token_usage(dict(api_response))
            and dict(_mapping(llm_call.get("cost"), f"rejected cost {case_id}"))
            == minimal_drafter.extract_cost_payload(dict(api_response)),
            f"rejected llm_call usage/cost drift: {case_id}/{attempt_prefix}",
        )
        expected_reasoning = "\n\n".join(reasoning_fragments).strip()
        _require(
            reasoning_path.read_text(encoding="utf-8")
            == expected_reasoning + ("\n" if expected_reasoning else ""),
            f"rejected reasoning sidecar drift: {case_id}/{attempt_prefix}",
        )
    else:
        raise ContractLifecycleError(
            f"API-bearing rejected transport lacks its llm/reasoning pair: {case_id}/{attempt_prefix}"
        )
    payload = {
        "status": "audited",
        "response_id": response_id,
        "response_status": response_status,
        "request_timestamp": request_timestamp,
        "response_timestamp": response_timestamp,
        "event_count": len(events),
        "command_event_count": command_event_count,
        "direct_stdin_audit": {
            "policy": EVENT_COMMAND_POLICY,
            "stdin_bundle": stdin_bundle,
            "events": event_audit,
        },
        "api_response_sha256": sha256_file(api_path),
    }
    return {**payload, "transport_audit_sha256": sha256_object(payload)}


def _validate_quarantined_attempt(
    *,
    quarantine_root: Path,
    case_id: str,
    attempt_prefix: str,
    attempt_record: Mapping[str, Any],
    case_packet_path: Path,
) -> dict[str, Any]:
    """Verify the immutable evidence ledger for one rejected attempt."""

    quarantine = _mapping(attempt_record.get("quarantine"), f"quarantine ref {case_id}/{attempt_prefix}")
    expected_root = quarantine_root.resolve()
    expected_dir = expected_root / case_id
    ledger_path = expected_dir / f"{attempt_prefix}.quarantine.json"
    _require(set(quarantine) == {
        "schema_version", "root", "ledger_path", "ledger_sha256",
        "artifact_count", "artifact_sha256",
    }, f"quarantine ref field set drift: {case_id}/{attempt_prefix}")
    _require(quarantine.get("schema_version") == QUARANTINE_REF_SCHEMA, f"quarantine ref schema drift: {case_id}/{attempt_prefix}")
    _require(quarantine.get("root") == _repo_relative(expected_root), f"quarantine root pointer drift: {case_id}/{attempt_prefix}")
    _require(quarantine.get("ledger_path") == _repo_relative(ledger_path), f"quarantine ledger pointer drift: {case_id}/{attempt_prefix}")
    ledger_file = _input_file(ledger_path, f"quarantine ledger {case_id}/{attempt_prefix}")
    _require(quarantine.get("ledger_sha256") == sha256_file(ledger_file), f"quarantine ledger hash drift: {case_id}/{attempt_prefix}")
    ledger = _load_mapping(ledger_file, f"quarantine ledger {case_id}/{attempt_prefix}")
    _require(set(ledger) == {
        "schema_version", "case_unit_id", "attempt_prefix", "attempt_index",
        "rejection_stage", "rejection_reason", "runtime_policy_gate", "artifacts",
    }, f"quarantine ledger field set drift: {case_id}/{attempt_prefix}")
    expected_index = int(attempt_prefix.removeprefix("attempt_"))
    _require(ledger.get("schema_version") == QUARANTINE_SCHEMA, f"quarantine ledger schema drift: {case_id}/{attempt_prefix}")
    _require(ledger.get("case_unit_id") == case_id and ledger.get("attempt_prefix") == attempt_prefix, f"quarantine identity drift: {case_id}/{attempt_prefix}")
    _require(ledger.get("attempt_index") == expected_index == attempt_record.get("attempt_index"), f"quarantine attempt index drift: {case_id}/{attempt_prefix}")
    gate = _mapping(attempt_record.get("runtime_policy_gate"), f"rejected gate {case_id}/{attempt_prefix}")
    _require(ledger.get("runtime_policy_gate") == gate, f"quarantine gate ledger drift: {case_id}/{attempt_prefix}")
    status = gate.get("status")
    if status == "failed":
        _require(ledger.get("rejection_stage") == "runtime_policy", f"failed gate rejection stage drift: {case_id}/{attempt_prefix}")
        _require(ledger.get("rejection_reason") == "runtime_policy_validation_failed", f"failed gate rejection reason drift: {case_id}/{attempt_prefix}")
        _require(set(gate) == {
            "schema_version", "status", "policy", "reason", "error_type", "error_message_sha256",
        }, f"failed gate field set drift: {case_id}/{attempt_prefix}")
        _require(gate.get("reason") == "runtime_policy_validation_failed", f"failed gate reason drift: {case_id}/{attempt_prefix}")
    else:
        _require(status == "not_run", f"quarantined gate status invalid: {case_id}/{attempt_prefix}")
        _require(set(gate) == {"schema_version", "status", "policy", "reason"}, f"not-run gate field set drift: {case_id}/{attempt_prefix}")
        reason = gate.get("reason")
        _require(reason in {"drafter_nonzero_or_checklist_missing", "checklist_validator_failed"}, f"not-run rejection reason drift: {case_id}/{attempt_prefix}")
        expected_stage = "drafter" if reason == "drafter_nonzero_or_checklist_missing" else "checklist_validator"
        _require(ledger.get("rejection_stage") == expected_stage and ledger.get("rejection_reason") == reason, f"not-run rejection ledger drift: {case_id}/{attempt_prefix}")
        if reason == "drafter_nonzero_or_checklist_missing":
            _require(attempt_record.get("returncode") != 0 or not (expected_dir / f"{attempt_prefix}.checklist.yaml").exists(), f"drafter rejection does not reproduce: {case_id}/{attempt_prefix}")
        else:
            _require(attempt_record.get("returncode") == 0, f"validator rejection has nonzero drafter return: {case_id}/{attempt_prefix}")
            _require(not str(attempt_record.get("validator") or "").startswith("checklist valid:"), f"validator rejection now claims pass: {case_id}/{attempt_prefix}")

    raw_artifacts = ledger.get("artifacts")
    _require(isinstance(raw_artifacts, list) and raw_artifacts, f"quarantine artifact ledger empty: {case_id}/{attempt_prefix}")
    artifacts: list[dict[str, Any]] = []
    names: list[str] = []
    for raw in raw_artifacts:
        artifact = dict(_mapping(raw, f"quarantine artifact {case_id}/{attempt_prefix}"))
        _require(set(artifact) == {"name", "size_bytes", "sha256"}, f"quarantine artifact fields drift: {case_id}/{attempt_prefix}")
        name = _string(artifact.get("name"), f"quarantine artifact name {case_id}/{attempt_prefix}")
        match = _ATTEMPT_RE.fullmatch(name)
        _require(match is not None and name.startswith(f"{attempt_prefix}."), f"unsupported quarantine artifact name: {case_id}/{name}")
        path = _input_file(expected_dir / name, f"quarantine artifact {case_id}/{name}")
        _require(artifact.get("size_bytes") == path.stat().st_size, f"quarantine artifact size drift: {case_id}/{name}")
        _require(artifact.get("sha256") == sha256_file(path), f"quarantine artifact hash drift: {case_id}/{name}")
        artifacts.append(artifact)
        names.append(name)
    _require(names == sorted(names) and len(names) == len(set(names)), f"quarantine artifact order/uniqueness drift: {case_id}/{attempt_prefix}")
    suffixes = frozenset(name.removeprefix(f"{attempt_prefix}.") for name in names)
    complete_suffixes = frozenset(CANONICAL_SUFFIXES)
    if status == "failed" or gate.get("reason") == "checklist_validator_failed":
        _require(suffixes == complete_suffixes, f"policy/validator-rejected attempt must preserve seven files: {case_id}/{attempt_prefix}")
    else:
        allowed_stages = {
            _ATTEMPT_LOG_SUFFIXES | frozenset(_ATTEMPT_STAGE_SUFFIXES[:count])
            for count in range(len(_ATTEMPT_STAGE_SUFFIXES) + 1)
        }
        _require(suffixes in allowed_stages, f"drafter-rejected attempt artifact stage invalid: {case_id}/{attempt_prefix}")
    artifact_hashes = {item["name"]: item["sha256"] for item in artifacts}
    _require(quarantine.get("artifact_count") == len(artifacts), f"quarantine artifact count drift: {case_id}/{attempt_prefix}")
    _require(quarantine.get("artifact_sha256") == artifact_hashes, f"quarantine artifact hash map drift: {case_id}/{attempt_prefix}")
    _validate_no_secret_material([expected_dir / name for name in names] + [ledger_file], case_id=case_id)
    packet_dir = case_packet_path.parent
    raw_manifest_path = _input_file(
        packet_dir / "raw_case_manifest.json",
        f"quarantined raw manifest {case_id}",
    )
    raw_manifest = _load_mapping(raw_manifest_path, f"quarantined raw manifest {case_id}")
    lock_binding = _validate_runtime_gate_lock_binding(
        case_id=case_id,
        packet_path=case_packet_path,
        raw_manifest_path=raw_manifest_path,
        output_dir=expected_dir,
        allow_nonformal_output=True,
    )
    _require(
        raw_manifest.get("case_unit_id") == case_id,
        f"quarantined raw-manifest identity drift: {case_id}/{attempt_prefix}",
    )
    transport_audit = _validate_rejected_codex_transport(
        expected_dir=expected_dir,
        sidecar_origin_dir=Path(lock_binding["sidecar_origin_case_dir"]),
        case_id=case_id,
        attempt_prefix=attempt_prefix,
        attempt_record=attempt_record,
        suffixes=suffixes,
        case_packet_path=case_packet_path,
    )
    _require(
        status == "not_run"
        and gate.get("reason") == "drafter_nonzero_or_checklist_missing",
        f"only audited infrastructure failures may precede a promoted formal "
        f"attempt: {case_id}/{attempt_prefix}",
    )
    infra_retry_classification = _classify_audited_infra_retry(
        api_response=_load_mapping(
            expected_dir / f"{attempt_prefix}.api_response.json",
            f"quarantined infra-retry API {case_id}/{attempt_prefix}",
        ),
        attempt_record=attempt_record,
        suffixes=suffixes,
        case_id=case_id,
        attempt_prefix=attempt_prefix,
    )
    _require(
        infra_retry_classification.get("retryable") is True,
        f"quarantined predecessor is not an allowlisted infrastructure retry: "
        f"{case_id}/{attempt_prefix}",
    )
    if status == "not_run" and gate.get("reason") == "checklist_validator_failed":
        validator_proc = subprocess.run(
            [
                sys.executable,
                str(_input_file(_IMPLEMENTATION_PATHS["checklist_validator.py"], "official checklist validator")),
                str(_input_file(expected_dir / f"{attempt_prefix}.checklist.yaml", "quarantined checklist")),
                "--case-packet",
                str(case_packet_path),
            ],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        _require(validator_proc.returncode != 0, f"quarantined checklist-validator rejection now passes: {case_id}/{attempt_prefix}")
    if status == "failed":
        try:
            validate_appworld_v56_attempt_runtime_policy(
                case_packet_path=case_packet_path,
                case_dir=expected_dir,
                attempt_prefix=attempt_prefix,
                attempt_record=attempt_record,
                acceptance_recheck=True,
            )
        except ContractLifecycleError as exc:
            recomputed = appworld_v56_runtime_gate_rejection(
                status="failed", reason="runtime_policy_validation_failed", error=exc
            )
            _require(dict(gate) == recomputed, f"rejected runtime-policy failure is not reproducible: {case_id}/{attempt_prefix}")
        else:
            raise ContractLifecycleError(f"quarantined runtime-policy attempt now passes: {case_id}/{attempt_prefix}")
    payload = {
        "attempt_index": expected_index,
        "runtime_policy_gate": dict(gate),
        "ledger_sha256": sha256_file(ledger_file),
        "artifact_sha256": artifact_hashes,
        "entry_names": names + [ledger_file.name],
        "transport_audit": transport_audit,
        "infra_retry_classification": infra_retry_classification,
    }
    return {**payload, "quarantine_evidence_sha256": sha256_object(payload)}


def _stderr_tail(path: Path) -> str:
    text = _input_file(path, "attempt stderr log").read_text(encoding="utf-8")
    stripped = text.strip()
    return stripped.splitlines()[-1] if stripped else ""


def validate_appworld_v56_attempt_runtime_policy(
    *,
    case_packet_path: str | Path,
    case_dir: str | Path,
    attempt_prefix: str,
    attempt_record: Mapping[str, Any],
    acceptance_recheck: bool = False,
) -> dict[str, Any]:
    """Validate one same-source attempt before the batch runner may promote it.

    This is the sole implementation of the v56 schema, source, support, Codex,
    event-command, token, and secret policy used both at generation time and by
    final acceptance.
    """

    match = re.fullmatch(r"attempt_([0-9]{2})", attempt_prefix)
    _require(match is not None, "runtime gate attempt prefix must be attempt_NN")
    attempt_index = int(match.group(1))
    _require(1 <= attempt_index <= len(EXPECTED_TOKEN_BUDGETS), "runtime gate attempt index is outside the frozen retry schedule")
    _require(attempt_record.get("attempt_index") == attempt_index, "runtime gate attempt record index mismatch")
    _require(attempt_record.get("returncode") == 0, "runtime gate requires a zero drafter return code")
    _require(str(attempt_record.get("validator") or "").startswith("checklist valid:"), "runtime gate requires the official checklist validator to pass first")
    _require(
        attempt_record.get("max_output_tokens") == EXPECTED_TOKEN_BUDGETS[attempt_index - 1],
        "runtime gate token-budget label differs from the frozen retry schedule",
    )

    packet_path = _input_file(case_packet_path, "runtime-gate case packet")
    _require(packet_path.name == "case_packet.md", "runtime gate packet filename must be case_packet.md")
    packet_dir = packet_path.parent
    raw_manifest_path = _input_file(packet_dir / "raw_case_manifest.json", "runtime-gate raw manifest")
    raw_manifest = _load_mapping(raw_manifest_path, "runtime-gate raw manifest")
    case_id = _string(raw_manifest.get("case_unit_id"), "runtime-gate case ID")
    output_dir = _input_directory(case_dir, f"runtime-gate attempt directory {case_id}")
    _require(output_dir.name == case_id == packet_dir.name, "runtime gate packet/output case identity mismatch")
    lock_binding = _validate_runtime_gate_lock_binding(
        case_id=case_id,
        packet_path=packet_path,
        raw_manifest_path=raw_manifest_path,
        output_dir=output_dir,
        allow_nonformal_output=acceptance_recheck,
    )
    split = _string(raw_manifest.get("split"), f"runtime-gate split {case_id}")
    _require(split in {"test_normal", "test_challenge"}, f"runtime gate split is off-scope: {case_id}")
    for key, expected in (
        ("task_id", case_id),
        ("domain", "appworld"),
        ("dataset_name", split),
        ("source_ref", f"appworld://{split}/{case_id}"),
    ):
        _require(raw_manifest.get(key) == expected, f"runtime gate raw manifest {key} mismatch: {case_id}")
    _validate_raw_source_hashes(packet_dir=packet_dir, raw_manifest=raw_manifest, case_id=case_id)

    attempt_paths = {
        suffix: output_dir / f"{attempt_prefix}.{suffix}" for suffix in CANONICAL_SUFFIXES
    }
    prefixed_entries = sorted(output_dir.glob(f"{attempt_prefix}.*"), key=lambda path: path.name)
    ledger_name = f"{attempt_prefix}.quarantine.json"
    if acceptance_recheck:
        _require(
            all(path.name in {value.name for value in attempt_paths.values()} | {ledger_name} for path in prefixed_entries),
            f"runtime gate acceptance recheck found an unsupported prefixed artifact: {case_id}/{attempt_prefix}",
        )
        actual_attempt_entries = [path for path in prefixed_entries if path.name != ledger_name]
    else:
        actual_attempt_entries = prefixed_entries
    _require(
        {path.name for path in actual_attempt_entries}
        == {path.name for path in attempt_paths.values()},
        f"runtime gate requires the exact seven-file attempt bundle: {case_id}/{attempt_prefix}",
    )
    _require(
        all(path.is_file() and not path.is_symlink() for path in actual_attempt_entries),
        f"runtime gate attempt contains a directory, symlink, or special file: {case_id}/{attempt_prefix}",
    )
    _validate_no_secret_material(actual_attempt_entries, case_id=case_id)

    checklist_yaml = _load_mapping(attempt_paths["checklist.yaml"], f"runtime-gate checklist YAML {case_id}")
    checklist_json = _load_mapping(attempt_paths["checklist.json"], f"runtime-gate checklist JSON {case_id}")
    _require(checklist_yaml == checklist_json, f"runtime gate YAML/JSON semantic mismatch: {case_id}")
    for key, expected in (
        ("schema_version", "case_checklist_v1"),
        ("domain", "appworld"),
        ("case_unit_id", case_id),
        ("task_id", case_id),
    ):
        _require(checklist_json.get(key) == expected, f"runtime gate checklist {key} mismatch: {case_id}")
    schema = _load_mapping(_IMPLEMENTATION_PATHS["case_checklist.schema.json"], "checklist schema")
    errors = sorted(Draft202012Validator(schema).iter_errors(checklist_json), key=lambda error: list(error.absolute_path))
    if errors:
        error = errors[0]
        location = ".".join(str(value) for value in error.absolute_path) or "<root>"
        raise ContractLifecycleError(f"runtime gate checklist schema failure {case_id} at {location}: {error.message}")
    support_count = _validate_support(
        checklist=checklist_json,
        packet_path=packet_path,
        raw_manifest=raw_manifest,
        case_id=case_id,
    )
    semantic_audit = validate_appworld_packet_checklist_semantics(
        case_packet_root=packet_dir,
        checklist=checklist_json,
    )
    _require(
        semantic_audit.get("schema_version") == APPWORLD_SEMANTIC_REPORT_SCHEMA
        and semantic_audit.get("status") == "passed"
        and semantic_audit.get("case_id") == case_id,
        f"AppWorld evaluator-composition audit identity mismatch: {case_id}",
    )
    usage, command_event_count, stderr_warning_count, direct_input_audit = _validate_codex_sidecars(
        case_id=case_id,
        checklist=checklist_json,
        llm_call=_load_mapping(attempt_paths["llm_call.json"], f"runtime-gate llm_call {case_id}"),
        api_response=_load_mapping(attempt_paths["api_response.json"], f"runtime-gate API response {case_id}"),
        reasoning_summary=attempt_paths["reasoning_summary.txt"].read_text(encoding="utf-8"),
        attempt_prefix=attempt_prefix,
        attempt_record=attempt_record,
        expected_sidecar_dir=Path(lock_binding["sidecar_origin_case_dir"]),
        expected_workspace_files=_expected_codex_workspace_files(
            packet_path=packet_path
        ),
    )
    expected_timeout = 3600 if packet_path.stat().st_size > EXPECTED_LARGE_THRESHOLD_BYTES else 1800
    expected_http_timeout = 480 if packet_path.stat().st_size > EXPECTED_LARGE_THRESHOLD_BYTES else 180
    _require(attempt_record.get("codex_timeout_seconds") == expected_timeout, f"runtime gate Codex timeout mismatch: {case_id}")
    _require(attempt_record.get("http_timeout_seconds") == expected_http_timeout, f"runtime gate HTTP timeout mismatch: {case_id}")
    payload: dict[str, Any] = {
        "schema_version": RUNTIME_GATE_SCHEMA,
        "status": "passed",
        "policy": EVENT_COMMAND_POLICY,
        "case_unit_id": case_id,
        "attempt_index": attempt_index,
        "case_packet_sha256": sha256_file(packet_path),
        "raw_case_manifest_sha256": sha256_file(raw_manifest_path),
        "pre_run_lock_sha256": lock_binding["pre_run_lock_sha256"],
        "implementation_semantic_sha256": lock_binding["implementation_semantic_sha256"],
        "support_pointer_count": support_count,
        "appworld_semantic_gate_schema": APPWORLD_SEMANTIC_REPORT_SCHEMA,
        "appworld_semantic_audit_sha256": sha256_object(semantic_audit),
        "appworld_scoring_block_count": semantic_audit["scoring_block_count"],
        "appworld_non_scoring_native_requirement_count": semantic_audit[
            "non_scoring_native_requirement_count"
        ],
        "command_event_count": command_event_count,
        "direct_stdin_audit": direct_input_audit,
        "direct_stdin_audit_sha256": direct_input_audit[
            "audit_semantic_sha256"
        ],
        "codex_stderr_warning_count": stderr_warning_count,
        "token_usage": usage,
        "artifact_sha256": {
            suffix: sha256_file(path) for suffix, path in sorted(attempt_paths.items())
        },
    }
    return {**payload, "audit_semantic_sha256": sha256_object(payload)}


def _validate_runtime_gate_lock_binding(
    *,
    case_id: str,
    packet_path: Path,
    raw_manifest_path: Path,
    output_dir: Path,
    allow_nonformal_output: bool,
) -> dict[str, str]:
    lock_file = _input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock")
    lock = _load_mapping(lock_file, "v4 pre-run lock")
    _require(lock.get("schema_version") == LOCK_SCHEMA and lock.get("status") == "locked_pre_run", "runtime gate pre-run lock identity drift")
    inputs = _mapping(lock.get("inputs"), "runtime gate locked inputs")
    packet_hashes = _mapping(inputs.get("case_packet_sha256_by_case"), "locked packet hashes")
    manifest_hashes = _mapping(inputs.get("raw_case_manifest_sha256_by_case"), "locked raw-manifest hashes")
    _require(packet_hashes.get(case_id) == sha256_file(packet_path), f"runtime gate packet differs from pre-run lock: {case_id}")
    _require(manifest_hashes.get(case_id) == sha256_file(raw_manifest_path), f"runtime gate raw manifest differs from pre-run lock: {case_id}")
    execution = _mapping(lock.get("execution"), "runtime gate execution lock")
    locked_root = resolve_repo_path(_string(execution.get("output_root"), "locked output root")).resolve()
    preflight = _mapping(lock.get("preflight"), "locked canary plan")
    phase_pairs = [
        (
            locked_root,
            resolve_repo_path(
            _string(execution.get("quarantine_root"), "locked formal quarantine root")
            ).resolve(),
        ),
        *[
            (
                resolve_repo_path(
                _string(_mapping(item, "locked canary round").get("output_root"), "locked canary output root")
                ).resolve(),
                resolve_repo_path(
                _string(_mapping(item, "locked canary round").get("quarantine_root"), "locked canary quarantine root")
                ).resolve(),
            )
            for item in preflight.get("rounds", [])
            if isinstance(item, Mapping)
        ],
    ]
    case_phase_roots = [case_root for case_root, _ in phase_pairs]
    quarantine_phase_roots = [quarantine_root for _, quarantine_root in phase_pairs]
    _require(
        len(case_phase_roots) == 4
        and len(set(case_phase_roots)) == 4
        and len(set(quarantine_phase_roots)) == 4
        and set(case_phase_roots).isdisjoint(quarantine_phase_roots),
        "runtime gate phase case/quarantine roots are not unique and disjoint",
    )
    phase_root_pairs = dict(phase_pairs)
    allowed_case_roots = set(phase_root_pairs)
    allowed_quarantine_roots = set(phase_root_pairs.values())
    allowed_roots = (
        allowed_case_roots | allowed_quarantine_roots
        if allow_nonformal_output
        else allowed_case_roots
    )
    _require(
        output_dir.parent.resolve() in allowed_roots,
        f"runtime gate output directory is outside the lock-authorized phase roots: {case_id}",
    )
    current_parent = output_dir.parent.resolve()
    if current_parent in allowed_case_roots:
        sidecar_origin_root = current_parent
    else:
        matches = [
            case_root
            for case_root, quarantine_root in phase_root_pairs.items()
            if quarantine_root == current_parent
        ]
        _require(
            allow_nonformal_output and len(matches) == 1,
            f"runtime gate quarantine root has no unique locked source phase: {case_id}",
        )
        sidecar_origin_root = matches[0]
    frozen_prompt = _mapping(lock.get("prompt"), "runtime gate prompt/implementation lock")
    current_prompt = _freeze_prompt()
    _require(dict(frozen_prompt) == current_prompt, f"runtime gate prompt/implementation bytes drifted: {case_id}")
    runtime = _mapping(lock.get("runtime"), "runtime gate runtime lock")
    current_python = _input_file(Path(sys.executable).resolve(), "runtime-gate Python executable")
    locked_python = _input_file(_string(runtime.get("python_executable"), "locked Python executable"), "locked Python executable")
    _require(current_python == locked_python, f"runtime gate Python executable resolution drift: {case_id}")
    _require(sha256_file(current_python) == runtime.get("python_executable_sha256"), f"runtime gate Python executable bytes drift: {case_id}")
    return {
        "pre_run_lock_sha256": sha256_file(lock_file),
        "implementation_semantic_sha256": sha256_object(current_prompt["implementation_sha256"]),
        "sidecar_origin_case_dir": str(sidecar_origin_root / case_id),
    }


def _validate_raw_source_hashes(*, packet_dir: Path, raw_manifest: Mapping[str, Any], case_id: str) -> None:
    files = raw_manifest.get("packet_files")
    hashes = _mapping(raw_manifest.get("sha256_per_file"), f"source hashes {case_id}")
    _require(isinstance(files, list) and files and all(isinstance(value, str) for value in files), f"raw packet file inventory invalid: {case_id}")
    _require(set(files) == set(hashes), f"raw packet hash inventory mismatch: {case_id}")
    for relative in files:
        _require(not Path(relative).is_absolute() and ".." not in Path(relative).parts, f"unsafe raw source path: {case_id}/{relative}")
        source = _input_file(packet_dir / "raw_case" / relative, f"raw source {case_id}/{relative}")
        _require(sha256_file(source) == hashes[relative], f"official source hash mismatch: {case_id}/{relative}")


def _validate_support(
    *, checklist: Mapping[str, Any], packet_path: Path, raw_manifest: Mapping[str, Any], case_id: str
) -> int:
    packet_text = packet_path.read_text(encoding="utf-8")
    try:
        allowed = case_packet_support_paths(packet_text)
        validate_checklist_guardrails(dict(checklist), allowed_source_paths=allowed)
    except Exception as exc:
        raise ContractLifecycleError(f"official packet-aware guardrail failure {case_id}: {exc}") from exc
    pointers = _iter_support_pointers(checklist)
    _require(pointers, f"checklist has no support pointers: {case_id}")
    hashes = _mapping(raw_manifest.get("sha256_per_file"), f"source hashes {case_id}")
    for pointer in pointers:
        path_part, separator, location = pointer.partition("::")
        _require(
            separator == "::"
            and path_part
            and location
            and location == location.strip(),
            f"malformed support pointer: {case_id}/{pointer}",
        )
        if path_part == "case_packet.md":
            source = packet_path
        else:
            _require(path_part in hashes, f"support path is outside official packet inventory: {case_id}/{path_part}")
            source = _input_file(packet_path.parent / "raw_case" / path_part, f"support source {case_id}/{path_part}")
            _require(sha256_file(source) == hashes[path_part], f"support source hash differs from official manifest: {case_id}/{path_part}")
        _require(
            support_location_resolves(source, location),
            f"support location does not resolve source-locally: {case_id}/{pointer}",
        )
    return len(pointers)


def _iter_support_pointers(node: Any) -> list[str]:
    values: list[str] = []
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key == "support" and isinstance(value, list):
                values.extend(str(item) for item in value)
            else:
                values.extend(_iter_support_pointers(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(_iter_support_pointers(value))
    return values


def _validate_codex_sidecars(
    *,
    case_id: str,
    checklist: Mapping[str, Any],
    llm_call: Mapping[str, Any],
    api_response: Mapping[str, Any],
    reasoning_summary: str,
    attempt_prefix: str,
    attempt_record: Mapping[str, Any],
    canonical_sidecar_paths: bool = False,
    expected_sidecar_dir: Path | None = None,
    expected_workspace_files: Mapping[str, str],
) -> tuple[dict[str, int], int, int, dict[str, Any]]:
    expected_llm_fields = {
        "schema_version", "provider", "model", "model_version", "api_key_env", "domain",
        "case_unit_id", "task_id", "phase", "experiment_type", "agent_id_or_role",
        "request_timestamp", "response_timestamp", "temperature", "max_tokens", "timeout_seconds",
        "retry_index", "token_usage", "cost", "response_metadata",
    }
    _require(set(llm_call) == expected_llm_fields, f"llm_call field set mismatch: {case_id}")
    expected_values = {
        "schema_version": "llm_call/v1", "provider": "codex_cli", "model": EXPECTED_MODEL,
        "model_version": EXPECTED_MODEL, "api_key_env": "CODEX_HOME", "domain": "appworld",
        "case_unit_id": case_id, "task_id": case_id, "phase": "draft",
        "experiment_type": "minimal_package", "agent_id_or_role": "case_checklist_drafter",
        "temperature": 0.0, "max_tokens": attempt_record["max_output_tokens"],
        "timeout_seconds": attempt_record["codex_timeout_seconds"], "retry_index": 0,
    }
    for key, expected in expected_values.items():
        _require(llm_call.get(key) == expected, f"llm_call.{key} mismatch: {case_id}")
    requested = _utc_timestamp(llm_call.get("request_timestamp"), f"request timestamp {case_id}")
    responded = _utc_timestamp(llm_call.get("response_timestamp"), f"response timestamp {case_id}")
    _require(responded >= requested, f"response precedes request: {case_id}")
    metadata = _mapping(llm_call.get("response_metadata"), f"response metadata {case_id}")
    _require(set(metadata) == {
        "response_id", "response_status", "provider_model", "reasoning_effort",
        "service_tier", "provider_created_at", "provider_completed_at",
        "raw_api_response_path", "reasoning_summary_path", "auth_mode",
        "max_output_tokens_enforced",
    }, f"response metadata field set mismatch: {case_id}")
    for key, expected in (
        ("response_status", "completed"), ("provider_model", EXPECTED_MODEL),
        ("reasoning_effort", EXPECTED_REASONING_EFFORT), ("auth_mode", "codex_login"),
        ("max_output_tokens_enforced", False),
    ):
        _require(metadata.get(key) == expected, f"response metadata {key} mismatch: {case_id}")
    _require(
        metadata.get("service_tier") is None
        and metadata.get("provider_created_at") is None
        and metadata.get("provider_completed_at") is None,
        f"Codex-unavailable provider metadata must remain null: {case_id}",
    )
    api_name = "api_response.json" if canonical_sidecar_paths else f"{attempt_prefix}.api_response.json"
    reasoning_name = "reasoning_summary.txt" if canonical_sidecar_paths else f"{attempt_prefix}.reasoning_summary.txt"
    _validate_exact_sidecar_metadata_paths(
        metadata=metadata,
        case_id=case_id,
        api_name=api_name,
        reasoning_name=reasoning_name,
        canonical_sidecar_paths=canonical_sidecar_paths,
        expected_sidecar_dir=expected_sidecar_dir,
    )

    _require(set(api_response) == {"id", "status", "model", "provider", "output_text", "output", "usage", "codex_cli"}, f"API sidecar field set mismatch: {case_id}")
    _require(api_response.get("status") == "completed" and api_response.get("provider") == "codex_cli", f"API completion/provider mismatch: {case_id}")
    _require(api_response.get("model") == EXPECTED_MODEL, f"API model mismatch: {case_id}")
    response_id = _string(api_response.get("id"), f"API response ID {case_id}")
    _require(metadata.get("response_id") == response_id, f"response ID mismatch: {case_id}")
    codex = _mapping(api_response.get("codex_cli"), f"codex_cli {case_id}")
    expected_codex_fields = {
        "auth_mode", "returncode", "timeout_seconds", "sandbox", "command",
        "events", "malformed_event_lines", "stderr",
    }
    if not canonical_sidecar_paths:
        expected_codex_fields.add("stdin_bundle")
    _require(
        set(codex) == expected_codex_fields,
        f"Codex sidecar field set mismatch: {case_id}",
    )
    _require(codex.get("auth_mode") == "codex_login", f"Codex auth mismatch: {case_id}")
    _require(codex.get("returncode") == 0 and codex.get("sandbox") == EXPECTED_CODEX_SANDBOX, f"Codex return/sandbox mismatch: {case_id}")
    _require(codex.get("timeout_seconds") == llm_call.get("timeout_seconds"), f"Codex timeout mismatch: {case_id}")
    _require(codex.get("malformed_event_lines") == [], f"malformed Codex event lines: {case_id}")
    stderr_raw = codex.get("stderr")
    _require(isinstance(stderr_raw, str), f"Codex stderr must be a string: {case_id}")
    stderr_lines = [line.strip() for line in stderr_raw.splitlines() if line.strip()]
    _require(
        len(stderr_lines) <= 1
        and all(_CODEX_PATH_WARNING_RE.fullmatch(line) for line in stderr_lines),
        f"successful Codex attempt emitted unrecognized stderr: {case_id}",
    )
    workspace = _validate_codex_argv(
        codex.get("command"),
        case_id=case_id,
        allow_legacy_launcher=canonical_sidecar_paths,
    )
    events = codex.get("events")
    _require(isinstance(events, list) and events and all(isinstance(event, Mapping) for event in events), f"Codex event stream invalid: {case_id}")
    _validate_codex_event_type_policy(
        events=events,
        case_id=case_id,
        allow_legacy_commands=canonical_sidecar_paths,
    )
    turn_completed_event = _validate_codex_event_lifecycle(
        events=events, response_id=response_id, case_id=case_id
    )
    if canonical_sidecar_paths:
        input_audit = _validate_event_commands(
            events=events,
            workspace=workspace,
            case_id=case_id,
            expected_workspace_files=expected_workspace_files,
        )
        _validate_single_agent_message_after_reads(
            events=events,
            read_audit=input_audit,
            case_id=case_id,
        )
        command_count = int(input_audit["command_event_count"])
    else:
        input_audit = _validate_direct_stdin_bundle(
            metadata=_mapping(codex.get("stdin_bundle"), f"Codex stdin bundle {case_id}"),
            expected_workspace_files=expected_workspace_files,
            case_id=case_id,
        )
        event_audit = _validate_direct_stdin_events(events=events, case_id=case_id)
        input_audit = {
            "policy": EVENT_COMMAND_POLICY,
            "stdin_bundle": input_audit,
            "events": event_audit,
        }
        input_audit = {
            **input_audit,
            "audit_semantic_sha256": sha256_object(input_audit),
        }
        command_count = 0

    output_text = _string(api_response.get("output_text"), f"output_text {case_id}")
    try:
        body = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise ContractLifecycleError(f"Codex output_text is malformed JSON: {case_id}") from exc
    _require(isinstance(body, dict), f"Codex output body is not a mapping: {case_id}")
    recovered_body = minimal_drafter.recover_json_output_from_events([dict(event) for event in events])
    _require(recovered_body == body, f"Codex output_text is not bound to the final parseable agent_message event: {case_id}")
    normalized = minimal_drafter.strip_null_fields(body)
    expected_body = {key: value for key, value in checklist.items() if key not in {"schema_version", "case_unit_id", "domain", "task_id"}}
    _require(normalized == expected_body, f"Codex body differs from canonical checklist: {case_id}")
    _require(minimal_drafter.extract_json_text(dict(api_response)) == body, f"Codex extraction differs from output_text: {case_id}")
    extracted_reasoning = minimal_drafter.extract_reasoning_summary_text(dict(api_response))
    event_reasoning_fragments = minimal_drafter.extract_codex_reasoning_fragments(
        [dict(event) for event in events]
    )
    expected_output = [
        {
            "type": "reasoning",
            "summary": [
                {"type": "summary_text", "text": text}
                for text in event_reasoning_fragments
            ],
        },
        {
            "type": "message",
            "content": [{"type": "output_text", "text": output_text}],
        },
    ]
    _require(api_response.get("output") == expected_output, f"Codex API output array is not the exact event/output_text projection: {case_id}")
    _require(
        extracted_reasoning == "\n\n".join(event_reasoning_fragments).strip(),
        f"Codex reasoning sidecar is not bound to event reasoning fragments: {case_id}",
    )
    _require(reasoning_summary == extracted_reasoning + ("\n" if extracted_reasoning else ""), f"reasoning summary extraction mismatch: {case_id}")

    api_usage = _mapping(api_response.get("usage"), f"API usage {case_id}")
    _require(
        dict(api_usage) == minimal_drafter.normalize_codex_usage([dict(event) for event in events]),
        f"API usage is not the exact turn.completed projection: {case_id}",
    )
    _require(set(api_usage) == {
        "input_tokens", "output_tokens", "total_tokens",
        "input_tokens_details", "output_tokens_details",
    }, f"API usage field set drift: {case_id}")
    input_details = _mapping(api_usage.get("input_tokens_details"), f"API input usage details {case_id}")
    output_details = _mapping(api_usage.get("output_tokens_details"), f"API output usage details {case_id}")
    _require(set(input_details) == {"cached_tokens"} and set(output_details) == {"reasoning_tokens"}, f"API usage detail field set drift: {case_id}")
    _require(
        all(
            type(value) is int and value >= 0
            for value in (
                api_usage.get("input_tokens"), api_usage.get("output_tokens"),
                api_usage.get("total_tokens"), input_details.get("cached_tokens"),
                output_details.get("reasoning_tokens"),
            )
        ),
        f"API usage contains a non-integer/negative value: {case_id}",
    )
    _require(api_usage["total_tokens"] == api_usage["input_tokens"] + api_usage["output_tokens"], f"API token total mismatch: {case_id}")

    usage = _mapping(llm_call.get("token_usage"), f"token usage {case_id}")
    usage_keys = {"prompt_tokens", "completion_tokens", "cached_prompt_tokens", "reasoning_tokens", "total_tokens"}
    _require(set(usage) == usage_keys, f"token usage field set mismatch: {case_id}")
    _require(dict(usage) == minimal_drafter.extract_token_usage(dict(api_response)), f"token usage sidecar mismatch: {case_id}")
    _require(all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in usage.values()), f"invalid token usage: {case_id}")
    _require(usage["prompt_tokens"] > 0 and usage["completion_tokens"] > 0 and usage["total_tokens"] > 0, f"zero token usage: {case_id}")
    _require(usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"], f"token total mismatch: {case_id}")
    event_usage = _mapping(turn_completed_event.get("usage"), f"turn.completed usage {case_id}")
    _require(set(event_usage) == {
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
    }, f"turn.completed usage field set drift: {case_id}")
    _require(all(type(value) is int and value >= 0 for value in event_usage.values()), f"turn.completed usage contains invalid values: {case_id}")
    _require(int(event_usage.get("input_tokens", -1)) == usage["prompt_tokens"], f"event input-token mismatch: {case_id}")
    _require(int(event_usage.get("output_tokens", -1)) == usage["completion_tokens"], f"event output-token mismatch: {case_id}")
    cost = _mapping(llm_call.get("cost"), f"cost {case_id}")
    _require(set(cost) == {
        "amount", "currency", "pricing_source", "pricing_table_id",
        "pricing_table_version", "pricing_source_hash", "cost_calculation_method",
        "missing_cost_reason", "total_cost_usd", "cost_details",
    }, f"cost field set mismatch: {case_id}")
    _require(dict(cost) == {
        "amount": None, "currency": "USD", "pricing_source": "provider_usage",
        "pricing_table_id": None, "pricing_table_version": None,
        "pricing_source_hash": None, "cost_calculation_method": "unavailable",
        "missing_cost_reason": "provider_cost_unavailable", "total_cost_usd": None,
        "cost_details": None,
    }, f"Codex cost provenance must be the exact unavailable projection: {case_id}")
    return (
        {key: int(value) for key, value in usage.items()},
        command_count,
        len(stderr_lines),
        input_audit,
    )


def _validate_exact_sidecar_metadata_paths(
    *,
    metadata: Mapping[str, Any],
    case_id: str,
    api_name: str,
    reasoning_name: str,
    canonical_sidecar_paths: bool,
    expected_sidecar_dir: Path | None,
) -> None:
    if expected_sidecar_dir is None:
        _require(canonical_sidecar_paths, f"runtime sidecar root is not explicitly bound: {case_id}")
        _require(str(metadata.get("raw_api_response_path") or "").replace("\\", "/").endswith(f"/{case_id}/{api_name}"), f"raw response pointer mismatch: {case_id}")
        _require(str(metadata.get("reasoning_summary_path") or "").replace("\\", "/").endswith(f"/{case_id}/{reasoning_name}"), f"reasoning pointer mismatch: {case_id}")
        return
    origin = expected_sidecar_dir.resolve()
    _require(origin.name == case_id, f"runtime sidecar root case identity mismatch: {case_id}")
    _require(metadata.get("raw_api_response_path") == str(origin / api_name), f"raw response pointer is outside the exact locked phase root: {case_id}")
    _require(metadata.get("reasoning_summary_path") == str(origin / reasoning_name), f"reasoning pointer is outside the exact locked phase root: {case_id}")


def _validate_codex_event_type_policy(
    *,
    events: Sequence[Mapping[str, Any]],
    case_id: str,
    allow_legacy_commands: bool = False,
) -> None:
    allowed_event_types = {
        "thread.started", "turn.started", "item.started", "item.completed", "turn.completed"
    }
    for event in events:
        event_type = _string(event.get("type"), f"Codex event type {case_id}")
        _require(event_type in allowed_event_types, f"Codex event type is not fail-closed allowed: {case_id}/{event_type}")
        item = event.get("item")
        if event_type.startswith("item."):
            item_map = _mapping(item, f"Codex event item {case_id}")
            item_type = _string(item_map.get("type"), f"Codex item type {case_id}")
            allowed_item_types = {"agent_message", "reasoning"}
            if allow_legacy_commands:
                allowed_item_types.add("command_execution")
            _require(
                item_type in allowed_item_types,
                f"Codex tool/item type is forbidden: {case_id}/{item_type}",
            )
            if item_type == "agent_message":
                _require(event_type == "item.completed", f"agent_message may appear only as item.completed: {case_id}")
            if item_type == "reasoning":
                _require(event_type == "item.completed", f"reasoning may appear only as item.completed: {case_id}")
        else:
            _require(item is None, f"non-item Codex event unexpectedly contains an item: {case_id}/{event_type}")


def _validate_direct_stdin_bundle(
    *,
    metadata: Mapping[str, Any],
    expected_workspace_files: Mapping[str, str],
    case_id: str,
) -> dict[str, Any]:
    """Rebuild and byte-bind the exact four-input direct Codex stdin bundle."""

    expected_fields = {
        "schema_version",
        "policy",
        "total_sha256",
        "total_size_bytes",
        "components",
    }
    _require(
        set(metadata) == expected_fields,
        f"Codex stdin bundle field set mismatch: {case_id}",
    )
    expected_files = dict(expected_workspace_files)
    _require(
        tuple(expected_files) == minimal_drafter.CODEX_WORKSPACE_FILE_ORDER,
        f"expected Codex stdin component inventory/order drift: {case_id}",
    )
    try:
        stdin_text, rebuilt = minimal_drafter.build_codex_stdin_bundle(expected_files)
    except minimal_drafter.DraftChecklistError as exc:
        raise ContractLifecycleError(
            f"could not reconstruct the sealed Codex stdin bundle: {case_id}: {exc}"
        ) from exc
    _require(
        isinstance(stdin_text, str) and stdin_text.endswith("\n") and "\r" not in stdin_text,
        f"rebuilt Codex stdin is not canonical LF text: {case_id}",
    )
    rebuilt_map = _mapping(rebuilt, f"rebuilt Codex stdin bundle {case_id}")
    _require(
        set(rebuilt_map) == expected_fields,
        f"rebuilt Codex stdin bundle field set drift: {case_id}",
    )
    _require(
        rebuilt_map.get("schema_version") == "codex_direct_stdin_bundle.v1"
        and rebuilt_map.get("policy") == EVENT_COMMAND_POLICY,
        f"rebuilt Codex stdin bundle identity drift: {case_id}",
    )
    stdin_bytes = stdin_text.encode("utf-8")
    _require(
        rebuilt_map.get("total_sha256") == sha256_bytes(stdin_bytes)
        and rebuilt_map.get("total_size_bytes") == len(stdin_bytes),
        f"rebuilt Codex stdin total byte/hash metadata drift: {case_id}",
    )
    components = rebuilt_map.get("components")
    _require(
        isinstance(components, list)
        and len(components) == len(minimal_drafter.CODEX_WORKSPACE_FILE_ORDER),
        f"rebuilt Codex stdin component count drift: {case_id}",
    )
    for component, (name, text) in zip(
        components, expected_files.items(), strict=True
    ):
        component_map = _mapping(component, f"Codex stdin component {case_id}/{name}")
        _require(
            set(component_map) == {"name", "sha256", "size_bytes", "line_count"},
            f"Codex stdin component field set drift: {case_id}/{name}",
        )
        encoded = text.encode("utf-8")
        _require(
            component_map
            == {
                "name": name,
                "sha256": sha256_bytes(encoded),
                "size_bytes": len(encoded),
                "line_count": len(text.splitlines()),
            },
            f"Codex stdin component byte/hash/line metadata drift: {case_id}/{name}",
        )
    _require(
        dict(metadata) == dict(rebuilt_map),
        f"Codex stdin bundle differs from frozen four-input reconstruction: {case_id}",
    )
    return dict(rebuilt_map)


def _validate_direct_stdin_events(
    *, events: Sequence[Mapping[str, Any]], case_id: str
) -> dict[str, Any]:
    """Require a tool-free one-message turn over the already sealed stdin input."""

    item_events: list[tuple[int, Mapping[str, Any]]] = []
    messages: list[tuple[int, Mapping[str, Any]]] = []
    reasoning_count = 0
    for index, event in enumerate(events):
        if not str(event.get("type")).startswith("item."):
            continue
        item = _mapping(event.get("item"), f"direct stdin event item {case_id}")
        item_type = _string(item.get("type"), f"direct stdin item type {case_id}")
        item_events.append((index, item))
        _require(
            item_type in {"agent_message", "reasoning"},
            f"direct stdin Codex turn emitted a forbidden tool item: {case_id}/{item_type}",
        )
        _require(
            event.get("type") == "item.completed",
            f"direct stdin non-tool item is not completed-only: {case_id}/{item_type}",
        )
        if item_type == "agent_message":
            messages.append((index, item))
        else:
            reasoning_count += 1
    _require(
        len(messages) == 1,
        f"Codex turn must emit exactly one final agent_message: {case_id}",
    )
    _require(
        item_events and messages[0][0] == item_events[-1][0],
        f"Codex final agent_message is not the last item event: {case_id}",
    )
    audit = {
        "policy": EVENT_COMMAND_POLICY,
        "event_count": len(events),
        "item_event_count": len(item_events),
        "reasoning_item_count": reasoning_count,
        "agent_message_count": len(messages),
        "final_agent_message_event_index": messages[0][0],
        "tool_item_count": 0,
        "command_event_count": 0,
    }
    return {**audit, "event_semantic_sha256": sha256_object(audit)}


def _validate_codex_event_lifecycle(
    *, events: Sequence[Mapping[str, Any]], response_id: Any, case_id: str
) -> Mapping[str, Any]:
    thread_started = [event for event in events if event.get("type") == "thread.started"]
    turn_started = [event for event in events if event.get("type") == "turn.started"]
    turn_completed = [event for event in events if event.get("type") == "turn.completed"]
    _require(len(thread_started) == 1 and events[0] is thread_started[0] and thread_started[0].get("thread_id") == response_id, f"thread.started must be unique, first, and identity-bound: {case_id}")
    _require(len(turn_started) == 1, f"turn.started must be unique: {case_id}")
    turn_started_index = events.index(turn_started[0])
    first_item_index = next((index for index, event in enumerate(events) if str(event.get("type")).startswith("item.")), len(events))
    _require(0 < turn_started_index < first_item_index, f"turn.started must precede all item events: {case_id}")
    _require(len(turn_completed) == 1 and events[-1] is turn_completed[0], f"turn.completed must be unique and final: {case_id}")
    return turn_completed[0]


def _validate_codex_argv(
    raw: Any, *, case_id: str, allow_legacy_launcher: bool = False
) -> Path:
    _require(isinstance(raw, list) and all(isinstance(value, str) for value in raw), f"Codex argv is not a string list: {case_id}")
    command = list(raw)
    _require(
        all(re.search(r"[\x00-\x1f\x7f]", value) is None for value in command),
        f"Codex argv contains a forbidden control character: {case_id}",
    )
    _require("--cd" in command, f"Codex argv lacks --cd: {case_id}")
    try:
        workspace = Path(command[command.index("--cd") + 1])
    except IndexError as exc:
        raise ContractLifecycleError(f"Codex argv has incomplete --cd: {case_id}") from exc
    _require(
        workspace.is_absolute()
        and workspace.parent == Path(_APPROVED_ENV_VALUES["TMPDIR"])
        and workspace.name.startswith("case-checklist-codex-"),
        f"Codex workspace is not the frozen TMPDIR isolation directory: {case_id}",
    )
    launcher = command[0]
    common_tail = [
        "--cd", str(workspace), "--skip-git-repo-check", "--ephemeral",
        "--ignore-user-config", "--sandbox", EXPECTED_CODEX_SANDBOX,
        "--model", EXPECTED_MODEL,
        "-c", f'model_reasoning_effort="{EXPECTED_REASONING_EFFORT}"',
        "-c", f'model_verbosity="{EXPECTED_MODEL_VERBOSITY}"',
        "--color", "never", "--json",
        "--output-schema", str(workspace / "output_schema.json"),
        "-o", str(workspace / "draft_body.json"), "-",
    ]
    expected = (
        [launcher, "exec", *common_tail]
        if allow_legacy_launcher
        else [
            launcher,
            "exec",
            "--strict-config",
            "--disable",
            "shell_tool",
            "--disable",
            "unified_exec",
            *common_tail,
        ]
    )
    _require(command == expected, f"Codex argv flags drift: {case_id}")
    if allow_legacy_launcher:
        _require(launcher == "codex", f"legacy canary Codex launcher drift: {case_id}")
    else:
        current = shutil.which("codex")
        _require(current is not None, f"Codex executable disappeared before runtime validation: {case_id}")
        current_path = _input_file(Path(current).resolve(), f"current Codex executable {case_id}")
        lock = _load_mapping(_input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock"), "v4 pre-run lock")
        runtime = _mapping(lock.get("runtime"), "locked runtime")
        locked_path = _input_file(_string(runtime.get("codex_executable"), "locked Codex executable"), "locked Codex executable")
        _require(current_path == locked_path and launcher == str(locked_path), f"Codex launcher resolution drifted after pre-run lock: {case_id}")
        _require(sha256_file(current_path) == runtime.get("codex_executable_sha256"), f"Codex executable bytes drifted after pre-run lock: {case_id}")
    return workspace


def _validate_event_commands(
    *,
    events: Sequence[Mapping[str, Any]],
    workspace: Path,
    case_id: str,
    expected_workspace_files: Mapping[str, str],
    enforce_locked_toolchain: bool = False,
) -> dict[str, Any]:
    if enforce_locked_toolchain:
        lock = _load_mapping(_input_file(DEFAULT_LOCK_PATH, "v4 pre-run lock"), "v4 pre-run lock")
        environment = _mapping(lock.get("environment"), "locked command environment")
        _require(environment.get("shell_toolchain") == _current_shell_toolchain(), f"read-only shell toolchain drifted before attempt validation: {case_id}")
    workspace_text = os.path.normpath(str(workspace))
    command_events: list[Mapping[str, Any]] = []
    by_id: dict[str, list[tuple[int, str, Mapping[str, Any], list[str]]]] = {}
    for event_index, event in enumerate(events):
        item = event.get("item")
        if not isinstance(item, Mapping) or item.get("type") != "command_execution":
            continue
        command_events.append(item)
        _require(
            set(item)
            == {
                "id",
                "type",
                "command",
                "aggregated_output",
                "exit_code",
                "status",
            },
            f"command event field set drift: {case_id}",
        )
        item_id = _string(item.get("id"), f"command event ID {case_id}")
        raw = _string(item.get("command"), f"command event payload {case_id}")
        outer_event_type = _string(event.get("type"), f"command outer event type {case_id}")
        output = item.get("aggregated_output")
        _require(isinstance(output, str), f"command aggregated_output is not text: {case_id}")
        tokens = _validate_command_payload(
            raw=raw,
            workspace_text=workspace_text,
            case_id=case_id,
        )
        by_id.setdefault(item_id, []).append(
            (event_index, outer_event_type, item, tokens)
        )
    invocations: list[dict[str, Any]] = []
    previous_terminal_index = -1
    for item_id, records in by_id.items():
        _require(len(records) == 2, f"command ID must have exactly one start and one terminal event: {case_id}/{item_id}")
        started = [
            record
            for record in records
            if record[1] == "item.started"
            and record[2].get("status") == "in_progress"
            and record[2].get("exit_code") is None
            and record[2].get("aggregated_output") == ""
        ]
        terminal_records = [
            record
            for record in records
            if record[1] == "item.completed"
            and record[2].get("status") == "completed"
            and type(record[2].get("exit_code")) is int
            and record[2].get("exit_code") == 0
        ]
        _require(len(started) == 1 and len(terminal_records) == 1, f"command ID outer/start/terminal pairing invalid: {case_id}/{item_id}")
        _require(records[0] == started[0] and records[1] == terminal_records[0], f"command terminal event precedes its start: {case_id}/{item_id}")
        _require(
            len({_string(record[2].get("command"), "command") for record in records})
            == 1,
            f"command text changed between start and terminal events: {case_id}/{item_id}",
        )
        _require(
            started[0][3] == terminal_records[0][3],
            f"command tokenization changed between start and terminal events: {case_id}/{item_id}",
        )
        _require(
            previous_terminal_index < started[0][0] < terminal_records[0][0],
            f"command invocations overlap or run out of order: {case_id}/{item_id}",
        )
        previous_terminal_index = terminal_records[0][0]
        invocations.append(
            {
                "id": item_id,
                "tokens": started[0][3],
                "output": terminal_records[0][2]["aggregated_output"],
            }
        )

    expected_files = dict(expected_workspace_files)
    _require(
        tuple(expected_files) == minimal_drafter.CODEX_WORKSPACE_FILE_ORDER,
        f"expected Codex workspace inventory/order drift: {case_id}",
    )
    try:
        expected_plan = minimal_drafter.build_codex_read_plan(expected_files)
    except minimal_drafter.DraftChecklistError as exc:
        raise ContractLifecycleError(
            f"could not reconstruct the mandatory Codex read plan: {case_id}: {exc}"
        ) from exc
    _require(
        len(invocations) == len(expected_plan),
        f"successful draft did not execute the exact mandatory read-plan length: {case_id}",
    )
    chunk_counts: Counter[str] = Counter()
    read_plan_records: list[dict[str, Any]] = []
    for invocation, expected in zip(invocations, expected_plan, strict=True):
        expected_tokens = _shell_tokens(str(expected["command"]), case_id=case_id)
        _require(
            invocation["tokens"] == expected_tokens,
            f"successful draft command differs from the exact mandatory read plan: {case_id}",
        )
        _require(
            invocation["output"] == expected["expected_output"],
            f"successful draft command output differs from frozen workspace bytes: {case_id}",
        )
        filename = str(expected["file"])
        chunk_counts[filename] += 1
        read_plan_records.append(
            {
                "command_id": invocation["id"],
                "file": filename,
                "start_line": expected["start_line"],
                "end_line": expected["end_line"],
                "command": expected["command"],
                "output_sha256": sha256_bytes(
                    str(expected["expected_output"]).encode("utf-8")
                ),
            }
        )
    file_audits = {
        name: {
            "line_count": len(text.splitlines()),
            "size_bytes": len(text.encode("utf-8")),
            "sha256": sha256_bytes(text.encode("utf-8")),
            "read_chunk_count": chunk_counts[name],
        }
        for name, text in expected_files.items()
    }
    audit = {
        "policy": EVENT_COMMAND_POLICY,
        "command_event_count": len(command_events),
        "command_invocation_count": len(invocations),
        "last_command_terminal_event_index": previous_terminal_index,
        "workspace_files": file_audits,
        "read_plan": read_plan_records,
    }
    return {**audit, "read_plan_semantic_sha256": sha256_object(audit)}


def _validate_single_agent_message_after_reads(
    *,
    events: Sequence[Mapping[str, Any]],
    read_audit: Mapping[str, Any],
    case_id: str,
) -> Mapping[str, Any]:
    messages = [
        (index, event)
        for index, event in enumerate(events)
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), Mapping)
        and _mapping(event.get("item"), f"agent message item {case_id}").get("type")
        == "agent_message"
    ]
    _require(
        len(messages) == 1,
        f"Codex turn must emit exactly one final agent_message: {case_id}",
    )
    message_index, message_event = messages[0]
    last_command_index = read_audit.get("last_command_terminal_event_index")
    _require(
        type(last_command_index) is int and message_index > last_command_index,
        f"Codex agent_message was emitted before mandatory reads completed: {case_id}",
    )
    item_indices = [
        index for index, event in enumerate(events) if str(event.get("type")).startswith("item.")
    ]
    _require(
        item_indices and message_index == item_indices[-1],
        f"Codex final agent_message is not the last item event: {case_id}",
    )
    return _mapping(message_event.get("item"), f"final agent message {case_id}")


def _validate_command_payload(
    *, raw: str, workspace_text: str, case_id: str
) -> list[str]:
    try:
        outer = shlex.split(raw)
    except ValueError as exc:
        raise ContractLifecycleError(f"command wrapper is not shell-parseable: {case_id}") from exc
    _require(len(outer) == 3 and outer[0] == "/bin/zsh" and outer[1] == "-lc", f"command wrapper is not the exact /bin/zsh -lc form: {case_id}")
    payload = outer[2]
    _require(not _has_forbidden_shell_expansion(payload), f"command uses forbidden expansion: {case_id}")
    tokens = _shell_tokens(payload, case_id=case_id)
    _validate_read_only_shell_tokens(tokens, case_id=case_id)
    for token in tokens:
        cleaned = token.lstrip("<>|;&(")
        _require(not cleaned.startswith("="), f"command uses forbidden zsh EQUALS expansion: {case_id}")
        path_candidates = [cleaned]
        if "=" in cleaned:
            path_candidates.append(cleaned.split("=", 1)[1])
        for candidate in path_candidates:
            _require(re.search(r"(^|/)\.\.($|/)", candidate) is None, f"command uses parent traversal: {case_id}")
            _require(not candidate.startswith("~"), f"command uses home expansion: {case_id}")
            if candidate.startswith("/"):
                normalized = os.path.normpath(candidate)
                _require(normalized == workspace_text or normalized.startswith(workspace_text + os.sep), f"command reads outside isolated temp workspace: {case_id}")
    return tokens


def _has_forbidden_shell_expansion(payload: str) -> bool:
    """Reject expansions except characters protected by a shell single quote."""

    state = "plain"
    index = 0
    while index < len(payload):
        char = payload[index]
        if ord(char) < 32 or ord(char) == 127:
            return True
        if state == "single":
            if char == "'":
                state = "plain"
            index += 1
            continue
        if char == "\\":
            if state == "plain" and index + 1 < len(payload):
                next_char = payload[index + 1]
                if ord(next_char) < 32 or ord(next_char) == 127:
                    return True
            index += 2
            continue
        if state == "double" and char == '"':
            state = "plain"
            index += 1
            continue
        if state == "plain" and char == "'":
            state = "single"
            index += 1
            continue
        if state == "plain" and char == '"':
            state = "double"
            index += 1
            continue
        if char in {"`", "$"}:
            return True
        if state == "plain" and char in {"{", "}", "*", "?", "[", "]"}:
            return True
        index += 1
    return False


def _shell_tokens(payload: str, *, case_id: str) -> list[str]:
    try:
        lexer = shlex.shlex(payload, posix=True, punctuation_chars="();<>|&")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError as exc:
        raise ContractLifecycleError(f"command payload is not shell-parseable: {case_id}") from exc


def _validate_read_only_shell_tokens(tokens: Sequence[str], *, case_id: str) -> None:
    _require(tokens, f"empty command payload: {case_id}")
    punctuation = set("();<>|&")
    _require(
        not any(token and all(char in punctuation for char in token) for token in tokens),
        f"pipelines, redirections, grouping, and shell control operators are forbidden: {case_id}",
    )
    executable = tokens[0]
    allowed = {"wc", "sed", "rg", "awk"}
    _require(executable in allowed, f"command executable is not in the strict read-only allowlist: {case_id}/{executable}")
    arguments = list(tokens[1:])
    allowed_files = {"draft_instructions.md", "template.yaml", "case_packet.md", "output_schema.json"}
    if executable == "wc":
        option_count = 1 if arguments and arguments[0] in {"-l", "--lines"} else 0
        operands = arguments[option_count:]
        _require(operands and all(arg in allowed_files for arg in operands), f"wc operands are outside the frozen workspace files: {case_id}")
    elif executable == "sed":
        program_match = (
            re.fullmatch(r"([1-9][0-9]*)(?:,([1-9][0-9]*))?p", arguments[1])
            if len(arguments) >= 2
            else None
        )
        _require(
            len(arguments) >= 3
            and arguments[0] == "-n"
            and program_match is not None
            and int(program_match.group(1))
            <= int(program_match.group(2) or program_match.group(1)),
            f"sed is restricted to the exact `sed -n N[,M]p FILE...` form: {case_id}",
        )
        _require(all(arg in allowed_files for arg in arguments[2:]), f"sed operands are outside the frozen workspace files: {case_id}")
    elif executable == "awk":
        program = " ".join(arguments)
        _require(not any(arg.startswith("-") for arg in arguments), f"awk options are forbidden: {case_id}")
        _require(len(arguments) >= 2 and all(arg in allowed_files for arg in arguments[1:]), f"awk must have one program and frozen workspace file operands: {case_id}")
        _require(re.search(r"\b(?:system|getline|close|ENVIRON|ARGV|ARGC)\b|@(?:include|load)\b", program) is None, f"awk external I/O/environment/argv access is forbidden: {case_id}")
        _require("@" not in program and re.search(r"\b(?:FUNCTAB|SYMTAB|PROCINFO)\b", program) is None, f"awk dynamic/runtime symbol access is forbidden: {case_id}")
        _require(">" not in program and "|" not in program, f"awk output/external pipe is forbidden: {case_id}")
    elif executable == "rg":
        safe_rg_options = {"-n", "--line-number", "-i", "--ignore-case", "-F", "--fixed-strings"}
        option_count = 0
        while option_count < len(arguments) and arguments[option_count] in safe_rg_options:
            option_count += 1
        positional = arguments[option_count:]
        _require(
            len(positional) >= 2
            and not positional[0].startswith("-")
            and all(arg in allowed_files for arg in positional[1:]),
            f"rg must use only leading allowed options, one pattern, and frozen workspace file operands: {case_id}",
        )


def _looks_like_path(value: str) -> bool:
    return value in {".", "-"} or "/" in value or bool(Path(value).suffix)


def _validate_no_secret_material(paths: Sequence[Path], *, case_id: str) -> None:
    findings = _secret_scan_paths(paths)
    _require(not findings, f"secret-like material in formal artifacts for {case_id}: {findings[0]['path'] if findings else ''}")


def _secret_scan_tree(root: Path) -> list[dict[str, Any]]:
    return _secret_scan_paths(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())


def _secret_scan_paths(paths: Sequence[Path] | Any) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ContractLifecycleError(f"draft artifact is not UTF-8 text: {path}") from exc
        for name, pattern in _SECRET_PATTERNS:
            matches = list(pattern.finditer(text))
            if matches:
                findings.append({"path": _repo_relative(path), "pattern": name, "count": len(matches)})
    return findings


def _strict_tree_inventory(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    directories: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda value: value.relative_to(root).as_posix()):
        _require(not path.is_symlink(), f"tree contains symlink: {path}")
        if path.is_dir():
            directories.append(path.relative_to(root).as_posix())
        else:
            _require(path.is_file(), f"tree contains unsupported entry: {path}")
            files.append({
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    return {
        "tree_sha256": sha256_object({"directories": directories, "files": files}),
        "file_count": len(files), "directory_count": len(directories),
        "size_bytes": sum(value["size_bytes"] for value in files),
        "directories": directories, "files": files,
    }


def _validate_no_symlinks(root: Path) -> None:
    _require(not root.is_symlink(), f"tree root is symlinked: {root}")
    for path in root.rglob("*"):
        _require(not path.is_symlink(), f"tree contains a symlink: {path}")


def _load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(f"{label} line {line_number} is malformed JSON") from exc
        rows.append(dict(_mapping(value, f"{label} line {line_number}")))
    return rows


def _parse_timestamp(value: Any, label: str) -> datetime:
    text = _string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractLifecycleError(f"{label} is not ISO-8601") from exc
    _require(parsed.tzinfo is not None, f"{label} lacks timezone")
    return parsed


def _acceptance_validator_hashes() -> dict[str, str]:
    module = Path(__file__).resolve()
    cli = resolve_repo_path("src/evidence_system/cli/validate_appworld_drafts_v56.py").resolve()
    return {
        "contract_module_path": _repo_relative(module),
        "contract_module_sha256": sha256_file(module),
        "cli_path": _repo_relative(cli),
        "cli_sha256": sha256_file(cli),
    }


def write_appworld_draft_acceptance_v56(
    *,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
    cases_root: str | Path | None = None,
    accepted_cases_root: str | Path = DEFAULT_ACCEPTED_CASES_ROOT,
    corrections_path: str | Path = DEFAULT_CORRECTIONS_PATH,
    hash_index_path: str | Path = DEFAULT_HASH_INDEX_PATH,
    report_path: str | Path = DEFAULT_ACCEPTANCE_PATH,
    final_lock_path: str | Path = DEFAULT_FINAL_LOCK_PATH,
) -> dict[str, Any]:
    """Validate formal artifacts, atomically materialize identity acceptance, and lock it."""

    lock_file = _input_file(lock_path, "v4 pre-run lock")
    _require(
        lock_file == resolve_repo_path(DEFAULT_LOCK_PATH).resolve(),
        "acceptance writer lock path is noncanonical",
    )
    provenance = lock_file.parent.resolve()
    _validate_draft_root_inventory(stage="pre_acceptance")
    _validate_completed_provenance_inventory(final=False)
    formal_report, formal_index = _validate_formal_run_v56(lock_path=lock_file, cases_root=cases_root)
    formal_root = _input_directory(formal_report["formal_cases"]["root"], "formal cases root")
    accepted_root = resolve_repo_path(accepted_cases_root).resolve()
    corrections_file = _provenance_output(corrections_path, provenance, DEFAULT_CORRECTIONS_PATH.name, "zero-correction manifest")
    index_file = _provenance_output(hash_index_path, provenance, DEFAULT_HASH_INDEX_PATH.name, "hash index")
    report_file = _provenance_output(report_path, provenance, DEFAULT_ACCEPTANCE_PATH.name, "acceptance report")
    final_file = _provenance_output(final_lock_path, provenance, DEFAULT_FINAL_LOCK_PATH.name, "final lock")
    _require(accepted_root == resolve_repo_path(DEFAULT_ACCEPTED_CASES_ROOT).resolve(), "accepted root must be the canonical 5.6 identity namespace")
    _require(accepted_root != formal_root and accepted_root.parent == formal_root.parent, "accepted root must be a formal-root sibling")
    _require(not accepted_root.exists(), f"accepted root already exists; refusing overwrite: {accepted_root}")
    for file in (corrections_file, index_file, report_file, final_file):
        _require(not file.exists(), f"acceptance output already exists; refusing overwrite: {file}")

    transaction_lock = accepted_root.parent / ".accepted_cases.materialize.lock"
    lock_fd = os.open(transaction_lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    os.close(lock_fd)
    temp_root: Path | None = None
    created: list[Path] = []
    try:
        temp_root = Path(tempfile.mkdtemp(prefix=".accepted_cases.tmp-", dir=accepted_root.parent))
        expected_ids = sorted(path.name for path in formal_root.iterdir() if path.is_dir())
        _require(len(expected_ids) == 485, "formal root no longer has 485 case directories")
        for case_id in expected_ids:
            shutil.copytree(formal_root / case_id, temp_root / case_id, copy_function=shutil.copy2)
        _validate_no_symlinks(temp_root)
        _require(not _secret_scan_tree(temp_root), "identity accepted staging tree contains secret-like material")
        for case_id in expected_ids:
            _require(sha256_path(temp_root / case_id) == sha256_path(formal_root / case_id), f"identity materialization differs from formal case: {case_id}")
        os.replace(temp_root, accepted_root)
        created.append(accepted_root)
        accepted_inventory = _strict_tree_inventory(accepted_root)
        accepted_tree_sha256 = sha256_path(accepted_root)

        corrections = {
            "schema_version": CORRECTIONS_SCHEMA,
            "status": "locked_zero_corrections",
            "created_at": _utc_now(),
            "draft_run_id": EXPECTED_DRAFT_RUN_ID,
            "pre_run_lock": {"path": _repo_relative(lock_file), "sha256": sha256_file(lock_file)},
            "formal_cases": {"root": _repo_relative(formal_root), "tree_sha256": sha256_path(formal_root)},
            "accepted_cases": {"root": _repo_relative(accepted_root), "tree_sha256": accepted_tree_sha256},
            "correction_count": 0,
            "corrected_case_ids": [],
            "identity_case_count": 485,
            "identity_materialization": True,
            "formal_repairs_applied": False,
        }
        _write_json_exclusive(corrections_file, corrections)
        created.append(corrections_file)
        accepted_ref = {
            "root": _repo_relative(accepted_root), "tree_sha256": accepted_tree_sha256,
            "strict_tree_sha256": accepted_inventory["tree_sha256"],
            "case_count": 485, "test_normal_count": 68, "test_challenge_count": 417,
            "file_count": accepted_inventory["file_count"],
            "directory_count": accepted_inventory["directory_count"],
            "size_bytes": accepted_inventory["size_bytes"],
            "identity_to_formal": True, "correction_count": 0,
        }
        hash_index = {
            **formal_index,
            "accepted_cases": accepted_ref,
            "zero_correction_manifest": {
                "path": _repo_relative(corrections_file), "sha256": sha256_file(corrections_file),
            },
        }
        _write_json_exclusive(index_file, hash_index)
        created.append(index_file)
        report = {
            **formal_report,
            "status": "accepted",
            "all_promoted_hard_gates_passed": True,
            "accepted_at": _utc_now(),
            "accepted_cases": accepted_ref,
            "corrections": {
                "manifest_path": _repo_relative(corrections_file),
                "manifest_sha256": sha256_file(corrections_file),
                "correction_count": 0,
                "formal_repairs_applied": False,
            },
            "draft_hash_index_content_sha256": sha256_object(hash_index),
            "draft_hash_index_path": _repo_relative(index_file),
            "draft_hash_index_file_sha256": sha256_file(index_file),
            "artifacts_written": True,
        }
        _write_json_exclusive(report_file, report)
        created.append(report_file)
        closure = {
            "pre_run_lock": {"path": _repo_relative(lock_file), "sha256": sha256_file(lock_file)},
            "canary_acceptance": formal_report["canary_acceptance"],
            "formal_cases": formal_report["formal_cases"],
            "quarantine": formal_report["quarantine"],
            "formal_batch": formal_report["batch"],
            "accepted_cases": accepted_ref,
            "zero_correction_manifest": {"path": _repo_relative(corrections_file), "sha256": sha256_file(corrections_file)},
            "acceptance_validator": formal_report["acceptance_validator"],
            "draft_hash_index": {"path": _repo_relative(index_file), "sha256": sha256_file(index_file), "content_sha256": sha256_object(hash_index)},
            "acceptance_report": {"path": _repo_relative(report_file), "sha256": sha256_file(report_file)},
        }
        final_lock = {
            "schema_version": FINAL_LOCK_SCHEMA,
            "status": "locked_post_acceptance",
            "draft_lifecycle_status": LIFECYCLE,
            "human_review_completed": False,
            "created_at": _utc_now(),
            "draft_run_id": EXPECTED_DRAFT_RUN_ID,
            **closure,
            "transitive_closure_sha256": sha256_object(closure),
        }
        _write_json_exclusive(final_file, final_lock)
        created.append(final_file)
        if transaction_lock.exists():
            transaction_lock.chmod(0o644)
            transaction_lock.unlink()
        verification = validate_appworld_draft_final_lock_v56(final_lock_path=final_file, lock_path=lock_file)
        return {
            **report,
            "report_path": _repo_relative(report_file), "report_sha256": sha256_file(report_file),
            "final_lock_path": _repo_relative(final_file), "final_lock_sha256": sha256_file(final_file),
            "final_lock_verification": verification,
        }
    except BaseException:
        for path in reversed(created):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.chmod(0o644)
                path.unlink()
        if temp_root is not None and temp_root.exists():
            shutil.rmtree(temp_root)
        raise
    finally:
        if transaction_lock.exists():
            transaction_lock.chmod(0o644)
            transaction_lock.unlink()


def validate_appworld_draft_final_lock_v56(
    *,
    final_lock_path: str | Path = DEFAULT_FINAL_LOCK_PATH,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
) -> dict[str, Any]:
    """Recompute the complete immutable formal/identity-accepted closure."""

    lock_file = _input_file(lock_path, "v4 pre-run lock")
    final_file = _input_file(final_lock_path, "v56 final lock")
    _require(
        lock_file == resolve_repo_path(DEFAULT_LOCK_PATH).resolve()
        and final_file == resolve_repo_path(DEFAULT_FINAL_LOCK_PATH).resolve(),
        "final-lock validation uses a noncanonical authority path",
    )
    _require(final_file.parent == lock_file.parent and final_file.name == DEFAULT_FINAL_LOCK_PATH.name, "final lock path drift")
    _validate_draft_root_inventory(stage="final")
    _validate_completed_provenance_inventory(final=True)
    final = _load_mapping(final_file, "v56 final lock")
    expected_keys = {
        "schema_version", "status", "draft_lifecycle_status", "human_review_completed",
        "created_at", "draft_run_id", "pre_run_lock", "formal_cases", "formal_batch",
        "quarantine", "canary_acceptance",
        "accepted_cases", "zero_correction_manifest", "acceptance_validator",
        "draft_hash_index", "acceptance_report", "transitive_closure_sha256",
    }
    _require(set(final) == expected_keys, "final lock field set drift")
    _require(final.get("schema_version") == FINAL_LOCK_SCHEMA and final.get("status") == "locked_post_acceptance", "final lock schema/status drift")
    _require(final.get("draft_lifecycle_status") == LIFECYCLE and final.get("human_review_completed") is False, "final lifecycle incorrectly claims review")
    _require(final.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID, "final run ID drift")
    _parse_timestamp(final.get("created_at"), "final lock timestamp")
    _require(final.get("pre_run_lock") == {"path": _repo_relative(lock_file), "sha256": sha256_file(lock_file)}, "final pre-run binding drift")

    fresh_report, fresh_formal_index = _validate_formal_run_v56(lock_path=lock_file, cases_root=None)
    _require(final.get("canary_acceptance") == fresh_report["canary_acceptance"], "final canary acceptance binding drift")
    _require(final.get("formal_cases") == fresh_report["formal_cases"], "final formal tree binding drift")
    _require(final.get("quarantine") == fresh_report["quarantine"], "final quarantine tree binding drift")
    _require(final.get("formal_batch") == fresh_report["batch"], "final formal batch binding drift")
    _require(final.get("acceptance_validator") == _acceptance_validator_hashes(), "final validator hash drift")
    accepted_ref = _mapping(final.get("accepted_cases"), "final accepted_cases")
    accepted_root = _input_directory(_string(accepted_ref.get("root"), "accepted root"), "accepted cases")
    _require(accepted_root == resolve_repo_path(DEFAULT_ACCEPTED_CASES_ROOT).resolve(), "final accepted root is noncanonical")
    _validate_identity_accepted(formal_root=_input_directory(fresh_report["formal_cases"]["root"], "formal root"), accepted_root=accepted_root)
    accepted_inventory = _strict_tree_inventory(accepted_root)
    expected_accepted_ref = {
        "root": _repo_relative(accepted_root), "tree_sha256": sha256_path(accepted_root),
        "strict_tree_sha256": accepted_inventory["tree_sha256"],
        "case_count": 485, "test_normal_count": 68, "test_challenge_count": 417,
        "file_count": accepted_inventory["file_count"], "directory_count": accepted_inventory["directory_count"],
        "size_bytes": accepted_inventory["size_bytes"], "identity_to_formal": True, "correction_count": 0,
    }
    _require(dict(accepted_ref) == expected_accepted_ref, "final accepted inventory drift")

    correction_ref = _mapping(final.get("zero_correction_manifest"), "final zero-correction ref")
    correction_file = _validate_canonical_final_artifact_ref(
        correction_ref,
        canonical_file=lock_file.parent / DEFAULT_CORRECTIONS_PATH.name,
        label="zero-correction manifest",
    )
    _validate_zero_corrections(correction_file, lock_file=lock_file, formal_root=_input_directory(fresh_report["formal_cases"]["root"], "formal root"), accepted_root=accepted_root)
    index_ref = _mapping(final.get("draft_hash_index"), "final hash index ref")
    index_candidate = _input_file(_string(index_ref.get("path"), "hash index path"), "draft hash index")
    _require(index_candidate == (lock_file.parent / DEFAULT_HASH_INDEX_PATH.name).resolve(), "draft hash index path is noncanonical")
    index_file = index_candidate
    index = _load_mapping(index_file, "draft hash index")
    expected_index = {
        **fresh_formal_index, "accepted_cases": expected_accepted_ref,
        "zero_correction_manifest": {"path": _repo_relative(correction_file), "sha256": sha256_file(correction_file)},
    }
    _require(index == expected_index, "stored hash index differs from fresh transitive validation")
    _validate_canonical_final_artifact_ref(
        index_ref,
        canonical_file=lock_file.parent / DEFAULT_HASH_INDEX_PATH.name,
        label="draft hash index",
        content_sha256=sha256_object(index),
    )
    report_ref = _mapping(final.get("acceptance_report"), "final report ref")
    report_file = _validate_canonical_final_artifact_ref(
        report_ref,
        canonical_file=lock_file.parent / DEFAULT_ACCEPTANCE_PATH.name,
        label="acceptance report",
    )
    report = _load_mapping(report_file, "acceptance report")
    accepted_at = _string(report.get("accepted_at"), "acceptance report accepted_at")
    _parse_timestamp(accepted_at, "acceptance report accepted_at")
    expected_report = {
        **fresh_report,
        "status": "accepted",
        "all_promoted_hard_gates_passed": True,
        "accepted_at": accepted_at,
        "accepted_cases": expected_accepted_ref,
        "corrections": {
            "manifest_path": _repo_relative(correction_file),
            "manifest_sha256": sha256_file(correction_file),
            "correction_count": 0,
            "formal_repairs_applied": False,
        },
        "draft_hash_index_content_sha256": sha256_object(index),
        "draft_hash_index_path": _repo_relative(index_file),
        "draft_hash_index_file_sha256": sha256_file(index_file),
        "artifacts_written": True,
    }
    _require(dict(report) == expected_report, "stored acceptance report differs from full fresh recomputation")
    closure = {key: final[key] for key in (
        "pre_run_lock", "canary_acceptance", "formal_cases", "quarantine", "formal_batch", "accepted_cases",
        "zero_correction_manifest", "acceptance_validator", "draft_hash_index", "acceptance_report",
    )}
    _require(final.get("transitive_closure_sha256") == sha256_object(closure), "final transitive closure hash drift")
    publication_findings = _secret_scan_tree(accepted_root) + _secret_scan_paths([correction_file, index_file, report_file, final_file])
    _require(not publication_findings, "accepted publication closure contains secret-like material")
    return {
        "schema_version": FINAL_LOCK_SCHEMA, "status": "verified",
        "draft_lifecycle_status": LIFECYCLE, "human_review_completed": False,
        "final_lock_path": _repo_relative(final_file), "final_lock_sha256": sha256_file(final_file),
        "accepted_cases_tree_sha256": sha256_path(accepted_root),
        "transitive_closure_sha256": final["transitive_closure_sha256"],
        "correction_count": 0, "all_file_bindings_verified": True,
    }


def _validate_canonical_final_artifact_ref(
    value: Mapping[str, Any],
    *,
    canonical_file: Path,
    label: str,
    content_sha256: str | None = None,
) -> Path:
    """Require an exact, canonical final-closure file reference."""

    ref = dict(_mapping(value, f"final {label} ref"))
    candidate = _input_file(_string(ref.get("path"), f"{label} path"), label)
    expected_file = canonical_file.resolve()
    _require(candidate == expected_file, f"{label} path is noncanonical")
    expected_ref = {
        "path": _repo_relative(expected_file),
        "sha256": sha256_file(expected_file),
    }
    if content_sha256 is not None:
        expected_ref["content_sha256"] = content_sha256
    _require(ref == expected_ref, f"final {label} reference field/value drift")
    return candidate


def _validate_identity_accepted(*, formal_root: Path, accepted_root: Path) -> None:
    _validate_no_symlinks(accepted_root)
    formal_ids = {path.name for path in formal_root.iterdir() if path.is_dir()}
    accepted_entries = list(accepted_root.iterdir())
    accepted_ids = {path.name for path in accepted_entries if path.is_dir() and not path.is_symlink()}
    _require(len(formal_ids) == 485 and accepted_ids == formal_ids, "accepted identity case set mismatch")
    _require(all(path.is_dir() and not path.is_symlink() for path in accepted_entries), "accepted root contains non-case entries")
    for case_id in sorted(formal_ids):
        _require(sha256_path(accepted_root / case_id) == sha256_path(formal_root / case_id), f"accepted case is not byte-identical to formal: {case_id}")
    _require(not _secret_scan_tree(accepted_root), "accepted identity tree contains secret-like material")


def _validate_zero_corrections(path: Path, *, lock_file: Path, formal_root: Path, accepted_root: Path) -> None:
    value = _load_mapping(path, "zero-correction manifest")
    expected_keys = {
        "schema_version", "status", "created_at", "draft_run_id", "pre_run_lock",
        "formal_cases", "accepted_cases", "correction_count", "corrected_case_ids",
        "identity_case_count", "identity_materialization", "formal_repairs_applied",
    }
    _require(set(value) == expected_keys, "zero-correction manifest field set drift")
    _require(value.get("schema_version") == CORRECTIONS_SCHEMA and value.get("status") == "locked_zero_corrections", "zero-correction schema/status drift")
    _parse_timestamp(value.get("created_at"), "zero-correction timestamp")
    _require(value.get("draft_run_id") == EXPECTED_DRAFT_RUN_ID, "zero-correction run ID drift")
    _require(value.get("pre_run_lock") == {"path": _repo_relative(lock_file), "sha256": sha256_file(lock_file)}, "zero-correction lock binding drift")
    _require(value.get("formal_cases") == {"root": _repo_relative(formal_root), "tree_sha256": sha256_path(formal_root)}, "zero-correction formal binding drift")
    _require(value.get("accepted_cases") == {"root": _repo_relative(accepted_root), "tree_sha256": sha256_path(accepted_root)}, "zero-correction accepted binding drift")
    _require(value.get("correction_count") == 0 and value.get("corrected_case_ids") == [], "corrections are not exactly zero")
    _require(value.get("identity_case_count") == 485 and value.get("identity_materialization") is True and value.get("formal_repairs_applied") is False, "identity materialization policy drift")


def _provenance_output(path: str | Path, root: Path, expected_name: str, label: str) -> Path:
    value = resolve_repo_path(path).resolve()
    _require(value.parent == root and value.name == expected_name and value.suffix == ".json", f"{label} must be provenance/{expected_name}")
    return value


def _manifest_cases(path: Path) -> list[dict[str, str]]:
    manifest = _load_mapping(path, "extension manifest")
    domains = manifest.get("domains")
    _require(isinstance(domains, list) and len(domains) == 1, "extension manifest must have one domain")
    raw_cases = _mapping(domains[0], "manifest domain").get("case_units")
    _require(isinstance(raw_cases, list) and len(raw_cases) == EXPECTED_EXTENSION_COUNT, "manifest must have 485 cases")
    cases: list[dict[str, str]] = []
    for index, raw in enumerate(raw_cases):
        case = _mapping(raw, f"manifest case {index}")
        case_id = _string(case.get("case_unit_id"), f"manifest case {index} ID")
        split = _string(case.get("dataset_name"), f"manifest case {index} dataset")
        _require(case.get("task_id") == case_id, f"manifest task identity mismatch: {case_id}")
        _require(case.get("split") == split and split in {"test_normal", "test_challenge"}, f"manifest split mismatch: {case_id}")
        source_ref = f"appworld://{split}/{case_id}"
        _require(case.get("source_ref") == source_ref, f"manifest source_ref mismatch: {case_id}")
        cases.append({
            "domain": "appworld",
            "case_unit_id": case_id,
            "task_id": case_id,
            "dataset_name": split,
            "split": split,
            "source_ref": source_ref,
        })
    ids = [case["case_unit_id"] for case in cases]
    _require(len(set(ids)) == EXPECTED_EXTENSION_COUNT, "manifest contains duplicate case IDs")
    _require(Counter(case["dataset_name"] for case in cases) == Counter({
        "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
        "test_challenge": EXPECTED_CHALLENGE_COUNT,
    }), "manifest split counts mismatch")
    return cases


def _input_file(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    _require(candidate.is_file() and not candidate.is_symlink(), f"{label} is missing, irregular, or symlinked: {candidate}")
    return candidate.resolve()


def _input_directory(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    _require(candidate.is_dir() and not candidate.is_symlink(), f"{label} is missing, irregular, or symlinked: {candidate}")
    return candidate.resolve()


def _load_mapping(path: str | Path, label: str) -> dict[str, Any]:
    try:
        return dict(_mapping(load_json_or_yaml(path), label))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ContractLifecycleError(f"could not load {label}: {exc}") from exc


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be a mapping")
    return value


def _string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value.strip(), f"{label} must be a nonempty string")
    return value


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path).resolve()
    try:
        return resolved.relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    data = (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            _require(written > 0, f"short write while creating exclusive JSON: {path}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractLifecycleError(message)
