#!/usr/bin/env python3
"""Create the fail-closed clean5 hardened prelock for a fresh canonical-only wave_004.

This command performs no model call.  It is intentionally create-once: a partial
or complete prior claim requires a human audit rather than an automatic rewrite.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from wave004_v6_clean2_hardened_common import (
    CASE_COUNT,
    CANDIDATE_REVIEW_SCHEMA,
    CONFIG_SCHEMA,
    EXPECTED_CODEX_VERSION,
    EXPECTED_FREEZE_SHA256,
    EXPECTED_MODEL,
    EXPECTED_EFFECTIVE_CONTEXT_LIMIT,
    EXPECTED_MODEL_CONTEXT_WINDOW,
    EXPECTED_PERMISSION_PROFILE,
    EXPECTED_REASONING,
    EXPECTED_SANDBOX,
    GENERATION_ID,
    NONCE_SHA256_RE,
    OWNER_NONCE_ENV,
    PARALLELISM,
    PRELOCK_SCHEMA,
    PRELOCK_CLAIM_SCHEMA,
    SNAPSHOT_SCHEMA,
    Wave004V6Clean2HardenedError,
    add_self_hash,
    canonical_json_equal,
    canonical_sha256,
    consume_and_verify_nonce,
    executable_binding,
    load_json,
    load_sealed_json_0444,
    read_regular_bytes_bound,
    regular_file_binding,
    require_empty_or_absent,
    require_safe_case_id,
    sha256_file,
    verify_self_hash,
    write_json_create_once,
)
from wave004_v6_clean2_hardened_staging import (
    DISABLED_CODEX_FEATURES,
    MAX_COVERAGE_CHUNK_BYTES,
    MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES,
    MAX_COVERAGE_PLAN_PAGE_TOKENS,
    MAX_COVERAGE_PLAN_ROW_BYTES,
    MAX_READER_ENVELOPE_BYTES,
    MAX_READER_ENVELOPE_TOKENS,
    PERMISSION_PROFILE_NAME,
    PRODUCTION_NAMESPACE,
    build_coverage_requirements,
    build_reader_operation_expectations,
    load_frozen_o200k_token_counter,
    parse_packet_sources,
    render_header_output_for_audit,
    render_overview_output_for_audit,
    staged_prompt,
    verify_reader_operation_expectations_binding,
)


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
GEN_ROOT = WORK_ROOT / "draft_generation"
PACKET_ROOT = WORK_ROOT / "case_packets" / "androidworld"
OLD_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
PACKET_INDEX = WORK_ROOT / "indexes" / "androidworld_candidate116_packet_index.json"
STATIC_ACCEPTANCE = WORK_ROOT / "validation" / "strict_acceptance_report.json"
AGENTS_CONFIG = (
    WORK_ROOT / "draft_config" / "androidworld_candidate116_drafter_config.json"
)
SOURCE_BUNDLE = (
    WORK_ROOT / "source_bundles" / "androidworld_candidate116_source_bundle.json"
)
READONLY_HELPER = WORK_ROOT / "scripts" / "readonly_snapshot_helper.py"
LIVE_COMMON = WORK_ROOT / "scripts" / "wave004_v6_clean2_hardened_common.py"
LIVE_LAUNCHER = WORK_ROOT / "scripts" / "run_fresh_draft_wave_v6_clean2_hardened.py"
STAGING_HELPER = WORK_ROOT / "scripts" / "wave004_v6_clean2_hardened_staging.py"
LIVE_NEURIPS = REPO_ROOT / "neurips_ed_track_minimal"
CLEAN_SUPPLEMENT = (
    GEN_ROOT / "prompts" / "androidworld_fresh_canonical_v7.supplement.md"
)
EXPECTED_SUPPLEMENT_SHA256 = (
    "9416598acacbe1c1a464d6628097b9bbc669d5d1bca21aecf624a612269fe794"
)
SUPERSESSION_INCIDENT = (
    GEN_ROOT / "incidents" / "wave_003_superseded_full_regeneration.json"
)
REVOKED_V6_INCIDENT = (
    GEN_ROOT / "incidents" / "wave_004_v6_clean_prelock_revoked_before_model.json"
)
ABORTED_CLEAN2_INCIDENT = (
    GEN_ROOT
    / "incidents"
    / "wave_004_v6_clean2_hardened_prelock_aborted_namespace_package.json"
)
CLEAN3_REVOCATION_INCIDENT = (
    GEN_ROOT
    / "incidents"
    / "wave_004_v6_clean3_hardened_unattributed_candidate_review_revoked.json"
)
CLEAN3_PRELOCK_ABORT_INCIDENT = (
    GEN_ROOT
    / "incidents"
    / "wave_004_v6_clean3_hardened_prelock_aborted_snapshot_rename.json"
)
CLEAN4_MIXED_TIME_REVOCATION_INCIDENT = (
    GEN_ROOT
    / "incidents"
    / "wave_004_v6_clean4_hardened_unattributed_mixed_time_prelock_revoked.json"
)
WAVE003_ROOT = GEN_ROOT / "waves" / "wave_003"
WAVE004_ROOT = GEN_ROOT / "waves" / GENERATION_ID
CANONICAL_DRAFTS = WORK_ROOT / "drafts"
CANONICAL_CONTRACTS = WORK_ROOT / "contracts" / "drafts"

CLAIM_ROOT = GEN_ROOT / "prelock_claims" / "wave_004_v6_clean5_hardened"
FROZEN_COVERAGE_ROOT = CLAIM_ROOT / "frozen_reader_coverage"
FROZEN_COVERAGE_INDEX = CLAIM_ROOT / "frozen_reader_coverage_index.json"
SNAPSHOT_ROOT = GEN_ROOT / "toolchain_snapshot" / "v6_clean5_hardened"
SNAPSHOT_MANIFEST = SNAPSHOT_ROOT / "snapshot_manifest.json"
CONFIG_PATH = (
    GEN_ROOT
    / "config"
    / "androidworld_candidate116_codex_cli_draft_config_v6_clean5_hardened.json"
)
CONFIG_STAGE_PATH = CLAIM_ROOT / "config.prepublish.stage.json"
PRELOCK_PATH = (
    GEN_ROOT
    / "freeze"
    / "androidworld_candidate116_codex_cli_draft_prelock_v6_clean5_hardened.json"
)
PRELOCK_STAGE_PATH = CLAIM_ROOT / "prelock.prepublish.stage.json"


def exact_json_int(value: Any, expected: int) -> bool:
    """Require a JSON integer without accepting Python booleans."""

    return type(value) is int and value == expected


READONLY_BEFORE = (
    GEN_ROOT
    / "validation"
    / "pre_generation_wave_004_v6_clean5_hardened_readonly_snapshot.json"
)
REAL_HOME = Path.home().resolve()
ORIGINAL_CODEX_HOME = REAL_HOME / ".codex"
ISOLATED_AUTH_HOME = REAL_HOME / ".codex-wave004-v6-clean5-hardened-auth"
ISOLATED_CHILD_HOME = (
    Path(os.environ.get("TMPDIR") or tempfile.gettempdir()).resolve()
    / "androidworld-wave004-v6-clean5-hardened-home"
)
WAVE_TMP_ROOT = (
    Path(os.environ.get("TMPDIR") or tempfile.gettempdir()).resolve()
    / "androidworld-wave004-v6-clean5-hardened-tmp"
)
MODELS_CACHE = ORIGINAL_CODEX_HOME / "models_cache.json"
TIKTOKEN_ROOT = GEN_ROOT / "tokenizer" / "tiktoken_0_12_0_py312"
TIKTOKEN_BPE_CACHE = (
    TIKTOKEN_ROOT / "encoding_cache" / "fb374d419588a4632f3f557e76b4b70aebbca790"
)
EXPECTED_TIKTOKEN_BPE_SHA256 = (
    "446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d"
)

EXPECTED_ENV_KEYS = (
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONHASHSEED",
    "PYTHONNOUSERSITE",
    "TMPDIR",
    "TZ",
)
RUNTIME_DISTRIBUTIONS = (
    "PyYAML",
    "attrs",
    "certifi",
    "charset-normalizer",
    "idna",
    "jsonschema",
    "jsonschema-specifications",
    "referencing",
    "requests",
    "rpds-py",
    "urllib3",
)
ALLOWED_LOGIN_WARNING = (
    "WARNING: proceeding, even though we could not create PATH aliases: "
    "Operation not permitted (os error 1)"
)

NEURIPS_COPY_MAP = {
    "hardened_staging": (
        STAGING_HELPER,
        "neurips_ed_track_minimal/hardened_staging.py",
    ),
    "checklist_guardrails": (
        LIVE_NEURIPS / "checklist_guardrails.py",
        "neurips_ed_track_minimal/checklist_guardrails.py",
    ),
    "drafter": (
        LIVE_NEURIPS / "scripts" / "draft_case_checklist.py",
        "neurips_ed_track_minimal/scripts/draft_case_checklist.py",
    ),
    "batch_runner": (
        LIVE_NEURIPS / "scripts" / "run_draft_batch.py",
        "neurips_ed_track_minimal/scripts/run_draft_batch.py",
    ),
    "validator": (
        LIVE_NEURIPS / "scripts" / "checklist_validator.py",
        "neurips_ed_track_minimal/scripts/checklist_validator.py",
    ),
    "draft_prompt": (
        LIVE_NEURIPS / "prompts" / "draft_case_checklist.prompt.md",
        "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md",
    ),
    "draft_template": (
        LIVE_NEURIPS / "templates" / "case_checklist.template.yaml",
        "neurips_ed_track_minimal/templates/case_checklist.template.yaml",
    ),
    "checklist_schema": (
        LIVE_NEURIPS / "schemas" / "case_checklist.schema.json",
        "neurips_ed_track_minimal/schemas/case_checklist.schema.json",
    ),
    "requirements": (
        LIVE_NEURIPS / "requirements.txt",
        "neurips_ed_track_minimal/requirements.txt",
    ),
}


def core_input_paths() -> dict[str, Path]:
    paths = {
        "old_packet_source_freeze": OLD_FREEZE,
        "packet_index": PACKET_INDEX,
        "static_acceptance": STATIC_ACCEPTANCE,
        "agents_config": AGENTS_CONFIG,
        "source_bundle": SOURCE_BUNDLE,
        "readonly_helper": READONLY_HELPER,
        "prompt_supplement": CLEAN_SUPPLEMENT,
        "wave003_supersession": SUPERSESSION_INCIDENT,
        "clean2_abort": ABORTED_CLEAN2_INCIDENT,
        "clean3_revocation": CLEAN3_REVOCATION_INCIDENT,
        "clean3_prelock_abort": CLEAN3_PRELOCK_ABORT_INCIDENT,
        "clean4_mixed_time_revocation": CLEAN4_MIXED_TIME_REVOCATION_INCIDENT,
        "models_cache": MODELS_CACHE,
        "pyvenv_cfg": REPO_ROOT / ".venv" / "pyvenv.cfg",
    }
    paths.update(
        {
            f"neurips:{name}": origin
            for name, (origin, _relative) in NEURIPS_COPY_MAP.items()
        }
    )
    return paths


def capture_core_input_bindings() -> dict[str, dict[str, Any]]:
    return {
        name: regular_file_binding(path)
        for name, path in sorted(core_input_paths().items())
    }


def verify_core_input_bindings_unchanged(
    expected: Mapping[str, Mapping[str, Any]],
) -> None:
    current = capture_core_input_bindings()
    normalized = {name: dict(binding) for name, binding in expected.items()}
    if not canonical_json_equal(current, normalized):
        raise Wave004V6Clean2HardenedError(
            "prompt/core prelock inputs changed during preparation"
        )


def capture_snapshot_origin_payloads(
    core_bindings: Mapping[str, Mapping[str, Any]],
    script_bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    specs: dict[str, tuple[Path, Mapping[str, Any]]] = {
        name: (origin, core_bindings[f"neurips:{name}"])
        for name, (origin, _relative) in NEURIPS_COPY_MAP.items()
    }
    specs.update(
        {
            "prompt_supplement": (
                CLEAN_SUPPLEMENT,
                core_bindings["prompt_supplement"],
            ),
            "frozen_wrapper": (LIVE_LAUNCHER, script_bindings["launcher"]),
            "wave004_v6_clean5_hardened_common": (
                LIVE_COMMON,
                script_bindings["common"],
            ),
            "wave004_v6_clean5_hardened_staging": (
                STAGING_HELPER,
                script_bindings["staging"],
            ),
            "readonly_snapshot_helper": (
                READONLY_HELPER,
                core_bindings["readonly_helper"],
            ),
        }
    )
    payloads: dict[str, dict[str, Any]] = {}
    for name, (path, binding) in sorted(specs.items()):
        data, observed = read_regular_bytes_bound(
            path,
            label=f"snapshot origin {name}",
            expected_binding=binding,
        )
        payloads[name] = {"binding": observed, "bytes": data}
    return payloads


def verify_snapshot_origins_unchanged(
    payloads: Mapping[str, Mapping[str, Any]],
) -> None:
    specs = {name: origin for name, (origin, _relative) in NEURIPS_COPY_MAP.items()}
    specs.update(
        {
            "prompt_supplement": CLEAN_SUPPLEMENT,
            "frozen_wrapper": LIVE_LAUNCHER,
            "wave004_v6_clean5_hardened_common": LIVE_COMMON,
            "wave004_v6_clean5_hardened_staging": STAGING_HELPER,
            "readonly_snapshot_helper": READONLY_HELPER,
        }
    )
    if set(specs) != set(payloads):
        raise Wave004V6Clean2HardenedError("snapshot origin set changed")
    for name, path in sorted(specs.items()):
        _data, binding = read_regular_bytes_bound(
            path,
            label=f"snapshot origin final readback {name}",
            expected_binding=payloads[name]["binding"],
        )
        if not canonical_json_equal(binding, payloads[name]["binding"]):
            raise Wave004V6Clean2HardenedError(
                f"snapshot origin changed during preparation: {name}"
            )


def future_regular_file_binding(stage_path: Path, final_path: Path) -> dict[str, Any]:
    """Map a complete sealed stage file binding to its same-filesystem final path."""

    binding = regular_file_binding(stage_path)
    final_parent = final_path.parent.resolve(strict=True)
    if stage_path.stat().st_dev != final_parent.stat().st_dev:
        raise Wave004V6Clean2HardenedError(
            "prepublication stage/final paths are not on one filesystem"
        )
    binding["path"] = str(final_parent / final_path.name)
    return binding


def discard_prepublication_stage() -> None:
    for path in (CONFIG_STAGE_PATH, PRELOCK_STAGE_PATH):
        if path.is_symlink():
            raise Wave004V6Clean2HardenedError(
                f"refusing symlinked prepublication stage cleanup: {path}"
            )
        if path.exists():
            if not path.is_file():
                raise Wave004V6Clean2HardenedError(
                    f"refusing non-file prepublication stage cleanup: {path}"
                )
            os.chmod(path, 0o600)
            path.unlink()


def verify_clean5_namespace_plan() -> None:
    """Prove every create-later production namespace is the fresh clean5 path."""

    expected = (
        (CLAIM_ROOT, GEN_ROOT / "prelock_claims" / GENERATION_ID),
        (
            FROZEN_COVERAGE_ROOT,
            GEN_ROOT / "prelock_claims" / GENERATION_ID / "frozen_reader_coverage",
        ),
        (
            FROZEN_COVERAGE_INDEX,
            GEN_ROOT
            / "prelock_claims"
            / GENERATION_ID
            / "frozen_reader_coverage_index.json",
        ),
        (
            CONFIG_STAGE_PATH,
            GEN_ROOT
            / "prelock_claims"
            / GENERATION_ID
            / "config.prepublish.stage.json",
        ),
        (
            PRELOCK_STAGE_PATH,
            GEN_ROOT
            / "prelock_claims"
            / GENERATION_ID
            / "prelock.prepublish.stage.json",
        ),
        (SNAPSHOT_ROOT, GEN_ROOT / "toolchain_snapshot" / "v6_clean5_hardened"),
        (
            CONFIG_PATH,
            GEN_ROOT
            / "config"
            / "androidworld_candidate116_codex_cli_draft_config_v6_clean5_hardened.json",
        ),
        (
            PRELOCK_PATH,
            GEN_ROOT
            / "freeze"
            / "androidworld_candidate116_codex_cli_draft_prelock_v6_clean5_hardened.json",
        ),
        (
            READONLY_BEFORE,
            GEN_ROOT
            / "validation"
            / "pre_generation_wave_004_v6_clean5_hardened_readonly_snapshot.json",
        ),
        (WAVE004_ROOT, GEN_ROOT / "waves" / GENERATION_ID),
        (ISOLATED_AUTH_HOME, REAL_HOME / ".codex-wave004-v6-clean5-hardened-auth"),
        (
            ISOLATED_CHILD_HOME,
            Path(os.environ.get("TMPDIR") or tempfile.gettempdir()).resolve()
            / "androidworld-wave004-v6-clean5-hardened-home",
        ),
        (
            WAVE_TMP_ROOT,
            Path(os.environ.get("TMPDIR") or tempfile.gettempdir()).resolve()
            / "androidworld-wave004-v6-clean5-hardened-tmp",
        ),
    )
    if any(actual != planned for actual, planned in expected):
        raise Wave004V6Clean2HardenedError(
            "clean5 production namespace plan is not exact"
        )
    identity_values = (
        GENERATION_ID,
        PRELOCK_SCHEMA,
        CONFIG_SCHEMA,
        SNAPSHOT_SCHEMA,
        CANDIDATE_REVIEW_SCHEMA,
        PRELOCK_CLAIM_SCHEMA,
        *(str(path) for pair in expected for path in pair),
    )
    if any(
        legacy in value
        for value in identity_values
        for legacy in ("clean2", "clean3", "clean4")
    ) or any("clean5" not in value for value in identity_values):
        raise Wave004V6Clean2HardenedError(
            "a legacy namespace leaked into a clean5 production identity"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=EXPECTED_MODEL)
    parser.add_argument("--reasoning-effort", default=EXPECTED_REASONING)
    parser.add_argument("--max-parallel", type=int, default=PARALLELISM)
    parser.add_argument(
        "--token-budgets",
        default="32000",
        help="Frozen single attempt budget; retries in the formal wave are forbidden.",
    )
    parser.add_argument("--codex-timeout-seconds", type=int, default=3600)
    parser.add_argument("--large-codex-timeout-seconds", type=int, default=5400)
    parser.add_argument(
        "--reviewed-candidate-approval",
        type=Path,
        required=True,
        help=(
            "Create-once root review artifact for this uniquely named candidate. "
            "This script never creates or self-asserts that approval."
        ),
    )
    return parser.parse_args()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Wave004V6Clean2HardenedError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_closed_environment() -> dict[str, str]:
    environment = {
        "CODEX_HOME": str(ISOLATED_AUTH_HOME),
        "HOME": str(ISOLATED_CHILD_HOME),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "TMPDIR": str(WAVE_TMP_ROOT),
        "TZ": "UTC",
    }
    if tuple(sorted(environment)) != tuple(sorted(EXPECTED_ENV_KEYS)):
        raise Wave004V6Clean2HardenedError(
            "internal closed-environment key set changed"
        )
    planned = [Path(environment[key]) for key in ("CODEX_HOME", "HOME", "TMPDIR")]
    if len(set(planned)) != 3 or any(
        path.exists() or path.is_symlink() for path in planned
    ):
        raise Wave004V6Clean2HardenedError(
            "planned CODEX_HOME/HOME/TMP roots must be distinct and absent at prelock"
        )
    return environment


def live_script_bindings() -> dict[str, dict[str, Any]]:
    return {
        "preparer": regular_file_binding(SCRIPT),
        "launcher": regular_file_binding(LIVE_LAUNCHER),
        "common": regular_file_binding(LIVE_COMMON),
        "staging": regular_file_binding(STAGING_HELPER),
    }


def verify_reviewed_candidate_approval(
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    approval, approval_file_binding = load_sealed_json_0444(
        path, "reviewed hardened candidate approval"
    )
    verify_self_hash(
        approval, "approval_sha256", "reviewed hardened candidate approval"
    )
    expected_scripts = live_script_bindings()
    if (
        set(approval)
        != {
            "approval_sha256",
            "candidate_generation_id",
            "independent_final_go",
            "model_call_count",
            "owner_nonce_sha256",
            "schema_version",
            "scripts",
            "status",
        }
        or approval.get("schema_version") != CANDIDATE_REVIEW_SCHEMA
        or approval.get("status") != "approved_for_create_once_candidate_prelock"
        or approval.get("candidate_generation_id") != GENERATION_ID
        or not canonical_json_equal(approval.get("scripts"), expected_scripts)
        or not isinstance(approval.get("owner_nonce_sha256"), str)
        or not NONCE_SHA256_RE.fullmatch(approval["owner_nonce_sha256"])
        or approval.get("independent_final_go") is not False
        or not exact_json_int(approval.get("model_call_count"), 0)
    ):
        raise Wave004V6Clean2HardenedError(
            "candidate approval is absent, stale, self-asserted, or improperly claims final GO"
        )
    return approval, approval_file_binding


def verify_candidate_gate_unchanged(
    path: Path,
    *,
    expected_approval: Mapping[str, Any],
    expected_approval_file_binding: Mapping[str, Any],
    expected_script_bindings: Mapping[str, Mapping[str, Any]],
) -> None:
    """Re-read the sealed approval and all four scripts before config/prelock."""

    approval, approval_file_binding = load_sealed_json_0444(
        path, "reviewed hardened candidate approval final readback"
    )
    verify_self_hash(
        approval,
        "approval_sha256",
        "reviewed hardened candidate approval final readback",
    )
    if (
        not canonical_json_equal(approval, expected_approval)
        or not canonical_json_equal(
            approval_file_binding, expected_approval_file_binding
        )
        or not canonical_json_equal(
            live_script_bindings(),
            {name: dict(binding) for name, binding in expected_script_bindings.items()},
        )
        or not canonical_json_equal(approval.get("scripts"), expected_script_bindings)
    ):
        raise Wave004V6Clean2HardenedError(
            "candidate approval or one of four live scripts changed during preparation"
        )


def planned_isolated_runtime_roots() -> dict[str, Any]:
    """Bind absent roots; only the final-GO launcher may create or destroy them."""

    planned = (ISOLATED_AUTH_HOME, ISOLATED_CHILD_HOME, WAVE_TMP_ROOT)
    if len(set(planned)) != 3 or any(
        path.exists() or path.is_symlink() for path in planned
    ):
        raise Wave004V6Clean2HardenedError(
            "isolated runtime plan paths are not distinct/absent"
        )
    source_auth = ORIGINAL_CODEX_HOME / "auth.json"
    source_stat = source_auth.lstat()
    if source_auth.is_symlink() or stat.S_IMODE(source_stat.st_mode) != 0o600:
        raise Wave004V6Clean2HardenedError("original Codex auth.json is not mode 0600")
    return {
        "creation_policy": (
            "launcher_O_EXCL_after_independent_final_go_and_fresh_ps_zero_foreign_codex"
        ),
        "destruction_policy": "launcher_finally_remove_auth_and_all_three_roots",
        "roots_created_at_prelock": False,
        "auth_home": {
            "path": str(ISOLATED_AUTH_HOME),
            "mode": 0o700,
            "namespace": ["auth.json"],
        },
        "isolated_auth": {
            "path": str(ISOLATED_AUTH_HOME / "auth.json"),
            "mode": 0o600,
            "parent_mode": 0o700,
            "byte_equal_must_be_verified_in_memory_at_launch": True,
        },
        "original_auth_at_copy": {
            "path": str(source_auth.resolve(strict=True)),
            "mode": 0o600,
            "read_only_host_source_for_launch_copy": True,
        },
        "isolated_home": {
            "path": str(ISOLATED_CHILD_HOME),
            "mode": 0o700,
            "namespace": [],
            "namespace_sha256": canonical_sha256([]),
            "initially_empty": True,
        },
        "real_home": {
            "path": str(REAL_HOME),
            "access_for_model": "deny",
        },
        "wave_tmp_root": {
            "path": str(WAVE_TMP_ROOT),
            "mode": 0o700,
            "initially_empty": True,
        },
    }


def exact_codex_version(executable: Path, environment: Mapping[str, str]) -> str:
    version = subprocess.run(
        [str(executable), "--version"],
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if (
        version.returncode != 0
        or version.stdout.strip() != EXPECTED_CODEX_VERSION
        or version.stderr.strip()
    ):
        raise Wave004V6Clean2HardenedError(
            f"Codex version is not exact: rc={version.returncode}, "
            f"stdout={version.stdout!r}, stderr={version.stderr!r}"
        )
    return version.stdout.strip()


def codex_feature_surface_binding(
    executable: Path, environment: Mapping[str, str]
) -> dict[str, Any]:
    """Bind the CLI feature registry and prove every deny flag parses offline."""

    listed = subprocess.run(
        [str(executable), "features", "list"],
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if listed.returncode != 0 or listed.stderr.strip() or not listed.stdout.strip():
        raise Wave004V6Clean2HardenedError(
            "Codex feature list could not be bound exactly"
        )
    rows = []
    for line in listed.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[-1] not in {"true", "false"}:
            raise Wave004V6Clean2HardenedError(
                f"unparseable Codex feature row: {line!r}"
            )
        rows.append(
            {
                "name": parts[0],
                "stage": " ".join(parts[1:-1]),
                "default_enabled": parts[-1] == "true",
            }
        )
    by_name = {row["name"]: row for row in rows}
    if len(by_name) != len(rows) or any(
        name not in by_name for name in DISABLED_CODEX_FEATURES
    ):
        raise Wave004V6Clean2HardenedError(
            "disabled Codex feature set is absent from registry"
        )
    parse_command = [str(executable), "-a", "never", "--strict-config", "exec"]
    for name in DISABLED_CODEX_FEATURES:
        parse_command.extend(("--disable", name))
    parse_command.append("--help")
    parsed = subprocess.run(
        parse_command,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if parsed.returncode != 0 or parsed.stderr.strip():
        raise Wave004V6Clean2HardenedError(
            "strict-config rejected the frozen feature deny set"
        )
    payload = {
        "schema_version": "androidworld_candidate116_codex_feature_surface/v1",
        "production_namespace": GENERATION_ID,
        "codex_version": EXPECTED_CODEX_VERSION,
        "rows": rows,
        "rows_sha256": canonical_sha256(rows),
        "disabled_features": list(DISABLED_CODEX_FEATURES),
        "disabled_features_sha256": canonical_sha256(list(DISABLED_CODEX_FEATURES)),
        "strict_config_parse_status": "pass_no_model_call",
        "allowed_execution_surface": ["shell_tool", "unified_exec"],
    }
    return add_self_hash(payload, "feature_surface_sha256")


def verify_frozen_inputs() -> (
    tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[str]]
):
    freeze = load_json(OLD_FREEZE, "fe2018 packet/source freeze")
    verify_self_hash(freeze, "freeze_sha256", "fe2018 packet/source freeze")
    if (
        freeze.get("schema_version") != "contract_draft_input_freeze/v1"
        or freeze.get("status") != "frozen"
        or freeze.get("freeze_sha256") != EXPECTED_FREEZE_SHA256
        or not exact_json_int(freeze.get("source_count"), CASE_COUNT)
    ):
        raise Wave004V6Clean2HardenedError(
            "fe2018 packet/source freeze identity is invalid"
        )

    case_order = list((freeze.get("case_order") or {}).get("case_unit_ids") or [])
    if (
        len(case_order) != CASE_COUNT
        or len(set(case_order)) != CASE_COUNT
        or any(require_safe_case_id(case_id) != case_id for case_id in case_order)
        or (freeze.get("case_order") or {}).get("case_unit_ids_hash")
        != canonical_sha256(case_order)
    ):
        raise Wave004V6Clean2HardenedError(
            "frozen case order is not exactly 116 unique safe cases"
        )

    index = load_json(PACKET_INDEX, "packet index")
    rows = list(index.get("items") or [])
    if (
        not exact_json_int(index.get("candidate_count"), CASE_COUNT)
        or len(rows) != CASE_COUNT
    ):
        raise Wave004V6Clean2HardenedError(
            "packet index does not contain exactly 116 rows"
        )
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = require_safe_case_id(row.get("case_unit_id"))
        if case_id in by_id:
            raise Wave004V6Clean2HardenedError(
                f"duplicate packet-index case: {case_id}"
            )
        by_id[case_id] = row

    discovered = sorted(PACKET_ROOT.glob("*/case_packet.md"))
    discovered_ids = [path.parent.name for path in discovered]
    if len(discovered) != CASE_COUNT or set(discovered_ids) != set(case_order):
        raise Wave004V6Clean2HardenedError(
            "canonical packet root is not the exact frozen 116-case set"
        )

    packet_inputs: list[dict[str, Any]] = []
    metadata_patterns = {
        "domain": re.compile(r"-\s*domain:\s*`([^`]+)`"),
        "case_unit_id": re.compile(r"-\s*case_unit_id:\s*`([^`]+)`"),
        "task_id": re.compile(r"-\s*task_id:\s*`([^`]+)`"),
    }
    for rank, case_id in enumerate(case_order):
        row = by_id.get(case_id)
        if row is None or not exact_json_int(row.get("selection_rank"), rank):
            raise Wave004V6Clean2HardenedError(
                f"packet index rank mismatch for {case_id}"
            )
        packet = PACKET_ROOT / case_id / "case_packet.md"
        expected_relative = packet.relative_to(REPO_ROOT).as_posix()
        if row.get("case_packet_path") != expected_relative:
            raise Wave004V6Clean2HardenedError(
                f"packet index path mismatch for {case_id}"
            )
        binding = regular_file_binding(packet)
        if row.get("case_packet_sha256") != binding["sha256"]:
            raise Wave004V6Clean2HardenedError(
                f"packet index byte hash mismatch for {case_id}"
            )
        text = packet.read_text(encoding="utf-8")
        metadata: dict[str, str] = {}
        for name, pattern in metadata_patterns.items():
            match = pattern.search(text)
            if match is None:
                raise Wave004V6Clean2HardenedError(
                    f"canonical packet lacks {name}: {case_id}"
                )
            metadata[name] = match.group(1).strip()
        if (
            metadata["domain"] != "androidworld"
            or metadata["case_unit_id"] != case_id
            or metadata["task_id"] != str(row.get("task_id"))
        ):
            raise Wave004V6Clean2HardenedError(
                f"canonical packet metadata mismatch for {case_id}"
            )
        packet_inputs.append(
            {
                "selection_rank": rank,
                "case_unit_id": case_id,
                "task_id": metadata["task_id"],
                "group": row.get("group"),
                "input_kind": "canonical_full_case_packet",
                "packet": binding,
                "source_closure_sha256": row.get("source_closure_sha256"),
                "semantic_source_context_sha256": row.get(
                    "semantic_source_context_sha256"
                ),
            }
        )

    agents_binding = regular_file_binding(AGENTS_CONFIG)
    if agents_binding["sha256"] != freeze.get("agents_config_hash") or agents_binding[
        "sha256"
    ] != ((freeze.get("artifact_bindings") or {}).get("agents_config") or {}).get(
        "sha256"
    ):
        raise Wave004V6Clean2HardenedError(
            "frozen agents config binding is inconsistent"
        )
    llm = freeze.get("llm") or {}
    llm_roles = llm.get("llm_roles")
    if (
        not isinstance(llm_roles, dict)
        or "contract_drafter" not in llm_roles
        or llm.get("llm_roles_sha256") != canonical_sha256(llm_roles)
    ):
        raise Wave004V6Clean2HardenedError("frozen llm_roles binding is invalid")
    static = load_json(STATIC_ACCEPTANCE, "strict static acceptance")
    if static.get("status") != "pass" or not exact_json_int(
        static.get("case_count"), CASE_COUNT
    ):
        raise Wave004V6Clean2HardenedError(
            "strict packet acceptance is not 116/116 pass"
        )
    return freeze, index, packet_inputs, case_order


def verify_prepublication_inputs_unchanged(
    *,
    approval_path: Path,
    approval: Mapping[str, Any],
    approval_file_binding: Mapping[str, Any],
    script_bindings: Mapping[str, Mapping[str, Any]],
    core_bindings: Mapping[str, Mapping[str, Any]],
    snapshot_origin_payloads: Mapping[str, Mapping[str, Any]],
    tokenizer: Mapping[str, Any],
    freeze: Mapping[str, Any],
    packet_index: Mapping[str, Any],
    packet_inputs: list[Mapping[str, Any]],
    case_order: list[str],
    snapshot_manifest: Mapping[str, Any],
) -> None:
    """Re-prove every start-captured input before publishing config/prelock."""

    verify_candidate_gate_unchanged(
        approval_path,
        expected_approval=approval,
        expected_approval_file_binding=approval_file_binding,
        expected_script_bindings=script_bindings,
    )
    verify_core_input_bindings_unchanged(core_bindings)
    verify_snapshot_origins_unchanged(snapshot_origin_payloads)
    if not canonical_json_equal(tokenizer_tree_binding(), tokenizer):
        raise Wave004V6Clean2HardenedError(
            "tokenizer closure changed during preparation"
        )
    current_freeze, current_index, current_packets, current_order = (
        verify_frozen_inputs()
    )
    if (
        not canonical_json_equal(current_freeze, freeze)
        or not canonical_json_equal(current_index, packet_index)
        or not canonical_json_equal(current_packets, packet_inputs)
        or not canonical_json_equal(current_order, case_order)
    ):
        raise Wave004V6Clean2HardenedError(
            "packet/freeze/index inputs changed during preparation"
        )
    manifest_origins = {
        str(row.get("name") or ""): row.get("live_origin")
        for row in snapshot_manifest.get("live_origins") or []
    }
    expected_origins = {
        name: dict(payload["binding"])
        for name, payload in snapshot_origin_payloads.items()
    }
    if not canonical_json_equal(manifest_origins, expected_origins):
        raise Wave004V6Clean2HardenedError(
            "snapshot live-origin bindings do not equal start capture"
        )


def tokenizer_tree_binding() -> dict[str, Any]:
    if TIKTOKEN_ROOT.is_symlink() or not TIKTOKEN_ROOT.is_dir():
        raise Wave004V6Clean2HardenedError(
            "frozen local tiktoken root is missing/symlinked"
        )
    files: list[dict[str, Any]] = []
    for path in sorted(
        TIKTOKEN_ROOT.rglob("*"),
        key=lambda item: item.relative_to(TIKTOKEN_ROOT).as_posix(),
    ):
        if path.is_symlink():
            raise Wave004V6Clean2HardenedError(f"symlink in tokenizer closure: {path}")
        if path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts:
            files.append(
                {
                    "relative_path": path.relative_to(TIKTOKEN_ROOT).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    if not files:
        raise Wave004V6Clean2HardenedError("tokenizer closure is empty")
    bpe = regular_file_binding(TIKTOKEN_BPE_CACHE)
    if bpe["sha256"] != EXPECTED_TIKTOKEN_BPE_SHA256:
        raise Wave004V6Clean2HardenedError("o200k_base merge table hash is not exact")
    return {
        "encoding": "o200k_base",
        "tiktoken_version": "0.12.0",
        "python_abi": "cp312",
        "root": str(TIKTOKEN_ROOT.resolve(strict=True)),
        "file_count": len(files),
        "files": files,
        "files_sha256": canonical_sha256(files),
        "merge_table": bpe,
    }


def model_capacity_binding(
    expected_models_cache_binding: Mapping[str, Any],
) -> dict[str, Any]:
    cache_bytes, models_cache_binding = read_regular_bytes_bound(
        MODELS_CACHE,
        label="Codex models cache",
        expected_binding=expected_models_cache_binding,
    )
    try:
        cache = json.loads(cache_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Wave004V6Clean2HardenedError(
            f"cannot load Codex models cache: {exc}"
        ) from exc
    if not isinstance(cache, dict):
        raise Wave004V6Clean2HardenedError("Codex models cache is not an object")
    rows = [
        row for row in cache.get("models") or [] if row.get("slug") == EXPECTED_MODEL
    ]
    if len(rows) != 1:
        raise Wave004V6Clean2HardenedError(
            "models cache lacks exactly one gpt-5.6-sol row"
        )
    row = rows[0]
    if (
        not exact_json_int(row.get("context_window"), EXPECTED_MODEL_CONTEXT_WINDOW)
        or not exact_json_int(
            row.get("max_context_window"), EXPECTED_MODEL_CONTEXT_WINDOW
        )
        or not exact_json_int(row.get("effective_context_window_percent"), 95)
        or EXPECTED_REASONING
        not in {
            item.get("effort") for item in row.get("supported_reasoning_levels") or []
        }
        or EXPECTED_EFFECTIVE_CONTEXT_LIMIT != EXPECTED_MODEL_CONTEXT_WINDOW * 95 // 100
    ):
        raise Wave004V6Clean2HardenedError(
            "gpt-5.6-sol context/reasoning metadata is not exact"
        )
    return {
        "models_cache": models_cache_binding,
        "models_cache_fetched_at": cache.get("fetched_at"),
        "model_row_sha256": canonical_sha256(row),
        "context_window": EXPECTED_MODEL_CONTEXT_WINDOW,
        "effective_context_window_percent": 95,
        "effective_context_limit": EXPECTED_EFFECTIVE_CONTEXT_LIMIT,
    }


def build_capacity_manifest(
    *,
    packet_inputs: list[Mapping[str, Any]],
    case_order: list[str],
    max_output_tokens: int,
    core_bindings: Mapping[str, Mapping[str, Any]],
    expected_tokenizer: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Tokenize both unsafe full packets and the exact staged read path with o200k."""

    tokenizer = tokenizer_tree_binding()
    if not canonical_json_equal(tokenizer, expected_tokenizer):
        raise Wave004V6Clean2HardenedError(
            "tokenizer closure changed before capacity build"
        )
    token_counter, tokenizer_binding = load_frozen_o200k_token_counter(
        tokenizer_root=TIKTOKEN_ROOT,
        merge_table_path=TIKTOKEN_BPE_CACHE,
    )
    base_bytes, _base_binding = read_regular_bytes_bound(
        LIVE_NEURIPS / "prompts" / "draft_case_checklist.prompt.md",
        label="frozen base draft prompt",
        expected_binding=core_bindings["neurips:draft_prompt"],
    )
    supplement_bytes, _supplement_binding = read_regular_bytes_bound(
        CLEAN_SUPPLEMENT,
        label="frozen clean supplement",
        expected_binding=core_bindings["prompt_supplement"],
    )
    base = base_bytes.decode("utf-8")
    supplement = supplement_bytes.decode("utf-8")
    instructions = base.rstrip() + "\n\n" + supplement.strip() + "\n"
    template_bytes, _template_binding = read_regular_bytes_bound(
        LIVE_NEURIPS / "templates" / "case_checklist.template.yaml",
        label="frozen draft template",
        expected_binding=core_bindings["neurips:draft_template"],
    )
    schema_bytes, _schema_binding = read_regular_bytes_bound(
        LIVE_NEURIPS / "schemas" / "case_checklist.schema.json",
        label="frozen checklist schema",
        expected_binding=core_bindings["neurips:checklist_schema"],
    )
    template = template_bytes.decode("utf-8")
    schema = json.loads(schema_bytes.decode("utf-8"))
    if not isinstance(schema, dict):
        raise Wave004V6Clean2HardenedError("checklist schema is not an object")
    by_id = {str(row["case_unit_id"]): row for row in packet_inputs}
    cases: list[dict[str, Any]] = []
    coverage_documents: dict[str, dict[str, Any]] = {}
    for case_id in case_order:
        packet_path = Path(str(by_id[case_id]["packet"]["path"]))
        packet_bytes, packet_binding = read_regular_bytes_bound(
            packet_path,
            label=f"canonical packet {case_id}",
            expected_binding=by_id[case_id]["packet"],
        )
        packet_text = packet_bytes.decode("utf-8")
        parsed = parse_packet_sources(packet_text)
        requirements = build_coverage_requirements(
            parsed,
            token_counter=token_counter,
            tokenizer_binding=tokenizer_binding,
        )
        requirements["case_packet_sha256"] = packet_binding["sha256"]
        requirements["source_inventory"] = [
            {
                key: parsed["sources"][path][key]
                for key in ("path", "sha256", "size_bytes", "line_count")
            }
            for path in parsed["inventory"]
        ]
        requirements.pop("requirements_sha256", None)
        requirements["requirements_sha256"] = canonical_sha256(requirements)
        operation_expectations = build_reader_operation_expectations(
            case_packet_text=packet_text,
            parsed=parsed,
            requirements=requirements,
            token_counter=token_counter,
        )
        verify_reader_operation_expectations_binding(
            requirements, operation_expectations
        )
        coverage_documents[case_id] = {
            "requirements": requirements,
            "reader_operation_expectations": operation_expectations,
        }
        prompt = staged_prompt(
            instructions=instructions,
            template_text=template,
            manifest={
                "coverage_requirements": requirements,
                "reader_operation_expectations": operation_expectations,
            },
        )
        header = packet_text.split("## Packet Source Files\n", 1)[0]
        overview = render_overview_output_for_audit(requirements)
        header_output = render_header_output_for_audit(
            header_text=header,
            case_packet_sha256=requirements["case_packet_sha256"],
            requirements_sha256=requirements["requirements_sha256"],
        )
        operation_rows = operation_expectations["operations"]
        page_rows = [row for row in operation_rows if row["kind"] == "plan-page"]
        read_rows = [row for row in operation_rows if row["kind"] == "read"]
        page_token_counts = [
            row["expected_full_output_o200k_tokens"] for row in page_rows
        ]
        read_token_counts = [
            row["expected_full_output_o200k_tokens"] for row in read_rows
        ]
        page_byte_counts = [row["expected_full_output_size_bytes"] for row in page_rows]
        read_byte_counts = [row["expected_full_output_size_bytes"] for row in read_rows]
        row_byte_counts = [
            len(
                json.dumps(
                    row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            )
            for row in requirements["required_ranges"]
        ]
        if (
            not page_rows
            or not read_rows
            or max(page_token_counts) > MAX_COVERAGE_PLAN_PAGE_TOKENS
            or max(page_byte_counts) > MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES
            or max(read_token_counts) > MAX_READER_ENVELOPE_TOKENS
            or max(read_byte_counts) > MAX_READER_ENVELOPE_BYTES
            or max(row_byte_counts) > MAX_COVERAGE_PLAN_ROW_BYTES
        ):
            raise Wave004V6Clean2HardenedError(
                f"exact reader byte/token envelope audit failed for {case_id}"
            )
        full_packet_tokens = token_counter(packet_text)
        raw_closure_tokens = sum(
            token_counter(parsed["sources"][row["path"]]["text"])
            for row in requirements["raw_official_source_closure"]
        )
        staged_input_tokens = (
            token_counter(prompt)
            + token_counter(overview)
            + sum(page_token_counts)
            + token_counter(header_output)
            + sum(read_token_counts)
            + token_counter(json.dumps(schema, ensure_ascii=False, sort_keys=True))
        )
        protocol_and_output_reserve = 40_000
        conservative_total = (
            staged_input_tokens + max_output_tokens + protocol_and_output_reserve
        )
        cases.append(
            {
                "case_unit_id": case_id,
                "packet_sha256": sha256_file(packet_path),
                "full_canonical_packet_o200k_tokens": full_packet_tokens,
                "full_packet_exceeds_effective_context": (
                    full_packet_tokens > EXPECTED_EFFECTIVE_CONTEXT_LIMIT
                ),
                "raw_official_closure_file_count": len(
                    requirements["raw_official_source_closure"]
                ),
                "raw_official_inventory_member_count": requirements[
                    "raw_official_inventory_member_count"
                ],
                "raw_official_distinct_sha_count": requirements[
                    "raw_official_distinct_sha_count"
                ],
                "raw_official_omitted_count": requirements[
                    "raw_official_omitted_count"
                ],
                "raw_official_closure_o200k_tokens": raw_closure_tokens,
                "coverage_chunk_count": len(requirements["required_ranges"]),
                "coverage_page_count": len(page_rows),
                "reader_operation_count": operation_expectations["operation_count"],
                "reader_operation_expectations_sha256": operation_expectations[
                    "reader_operation_expectations_sha256"
                ],
                "max_plan_row_serialized_bytes": max(row_byte_counts),
                "max_plan_page_output_bytes": max(page_byte_counts),
                "max_plan_page_o200k_tokens": max(page_token_counts),
                "max_reader_envelope_bytes": max(read_byte_counts),
                "max_reader_envelope_o200k_tokens": max(read_token_counts),
                "exact_staged_input_o200k_tokens": staged_input_tokens,
                "reserved_output_tokens": max_output_tokens,
                "additional_dynamic_command_reserve_tokens": 0,
                "protocol_and_system_safety_margin_tokens": protocol_and_output_reserve,
                "conservative_total_o200k_tokens": conservative_total,
                "within_effective_context": (
                    conservative_total <= EXPECTED_EFFECTIVE_CONTEXT_LIMIT
                ),
                "requirements_sha256": requirements["requirements_sha256"],
            }
        )
    failed_capacity = [
        row for row in cases if row["within_effective_context"] is not True
    ]
    if (
        len(cases) != CASE_COUNT
        or [row["case_unit_id"] for row in cases] != case_order
        or failed_capacity
    ):
        failure_summary = [
            {
                "case_unit_id": row["case_unit_id"],
                "conservative_total_o200k_tokens": row[
                    "conservative_total_o200k_tokens"
                ],
                "over_by_tokens": row["conservative_total_o200k_tokens"]
                - EXPECTED_EFFECTIVE_CONTEXT_LIMIT,
                "exact_staged_input_o200k_tokens": row[
                    "exact_staged_input_o200k_tokens"
                ],
            }
            for row in failed_capacity
        ]
        raise Wave004V6Clean2HardenedError(
            "staged capacity gate is not 116/116 pass: "
            + json.dumps(failure_summary, ensure_ascii=False, sort_keys=True)
        )
    payload = {
        "schema_version": "androidworld_candidate116_staged_capacity/v1",
        "production_namespace": GENERATION_ID,
        "status": "pass_116_of_116",
        "encoding": "o200k_base",
        "tokenizer": tokenizer,
        "model_capacity": model_capacity_binding(core_bindings["models_cache"]),
        "case_count": len(cases),
        "case_order_sha256": canonical_sha256(case_order),
        "max_coverage_chunk_bytes": MAX_COVERAGE_CHUNK_BYTES,
        "max_reader_envelope_bytes_limit": MAX_READER_ENVELOPE_BYTES,
        "max_reader_envelope_o200k_tokens_limit": MAX_READER_ENVELOPE_TOKENS,
        "max_plan_row_serialized_bytes_limit": MAX_COVERAGE_PLAN_ROW_BYTES,
        "max_plan_page_output_bytes_limit": MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES,
        "max_plan_page_o200k_tokens_limit": MAX_COVERAGE_PLAN_PAGE_TOKENS,
        "max_full_packet_tokens": max(
            row["full_canonical_packet_o200k_tokens"] for row in cases
        ),
        "full_packet_over_effective_context_count": sum(
            bool(row["full_packet_exceeds_effective_context"]) for row in cases
        ),
        "max_raw_official_closure_tokens": max(
            row["raw_official_closure_o200k_tokens"] for row in cases
        ),
        "max_observed_reader_envelope_bytes": max(
            row["max_reader_envelope_bytes"] for row in cases
        ),
        "max_observed_reader_envelope_o200k_tokens": max(
            row["max_reader_envelope_o200k_tokens"] for row in cases
        ),
        "max_observed_plan_page_output_bytes": max(
            row["max_plan_page_output_bytes"] for row in cases
        ),
        "max_observed_plan_page_o200k_tokens": max(
            row["max_plan_page_o200k_tokens"] for row in cases
        ),
        "raw_official_omitted_total": sum(
            row["raw_official_omitted_count"] for row in cases
        ),
        "max_conservative_total_tokens": max(
            row["conservative_total_o200k_tokens"] for row in cases
        ),
        "cases": cases,
        "cases_sha256": canonical_sha256(cases),
    }
    return add_self_hash(payload, "capacity_sha256"), coverage_documents


def write_frozen_reader_coverage(
    *,
    coverage_documents: Mapping[str, Mapping[str, Any]],
    case_order: list[str],
) -> dict[str, Any]:
    """Create the exact clean5 A/B coverage tree once, then seal it read-only."""

    if FROZEN_COVERAGE_ROOT.exists() or FROZEN_COVERAGE_ROOT.is_symlink():
        raise Wave004V6Clean2HardenedError(
            "clean5 frozen reader coverage root already exists"
        )
    if list(coverage_documents) != case_order:
        raise Wave004V6Clean2HardenedError(
            "clean5 frozen reader coverage order differs from case order"
        )
    os.mkdir(FROZEN_COVERAGE_ROOT, 0o700)
    rows: list[dict[str, Any]] = []
    for case_id in case_order:
        require_safe_case_id(case_id)
        documents = coverage_documents[case_id]
        requirements = documents.get("requirements")
        operations = documents.get("reader_operation_expectations")
        if not isinstance(requirements, Mapping) or not isinstance(operations, Mapping):
            raise Wave004V6Clean2HardenedError(
                f"clean5 A/B documents are absent for {case_id}"
            )
        verify_reader_operation_expectations_binding(requirements, operations)
        case_root = FROZEN_COVERAGE_ROOT / case_id
        os.mkdir(case_root, 0o700)
        requirements_path = case_root / "model_input_coverage.json"
        operations_path = case_root / "reader_operation_expectations.json"
        write_json_create_once(requirements_path, requirements)
        write_json_create_once(operations_path, operations)
        os.chmod(requirements_path, 0o444)
        os.chmod(operations_path, 0o444)
        os.chmod(case_root, 0o555)
        rows.append(
            {
                "case_unit_id": case_id,
                "task_id": requirements["task_id"],
                "requirements": regular_file_binding(requirements_path)
                | {"requirements_sha256": requirements["requirements_sha256"]},
                "reader_operation_expectations": regular_file_binding(operations_path)
                | {
                    "reader_operation_expectations_sha256": operations[
                        "reader_operation_expectations_sha256"
                    ],
                    "operations_sha256": operations["operations_sha256"],
                },
            }
        )
    os.chmod(FROZEN_COVERAGE_ROOT, 0o555)
    index = {
        "schema_version": (
            "androidworld_candidate116_frozen_reader_coverage_index/"
            "v6_clean5_hardened"
        ),
        "production_namespace": GENERATION_ID,
        "status": "frozen_A_and_B_before_first_model_call",
        "root_absolute": str(FROZEN_COVERAGE_ROOT),
        "case_count": len(rows),
        "case_order": case_order,
        "case_order_sha256": canonical_sha256(case_order),
        "expected_case_files": [
            "model_input_coverage.json",
            "reader_operation_expectations.json",
        ],
        "cases": rows,
        "cases_sha256": canonical_sha256(rows),
    }
    index = add_self_hash(index, "coverage_index_sha256")
    write_json_create_once(FROZEN_COVERAGE_INDEX, index)
    os.chmod(FROZEN_COVERAGE_INDEX, 0o444)
    return index


STRICT_SUPPORT_INSERT = """    native = checklist.get("native", {})
    for singleton_name in ("user_goal", "benchmark_success", "checked_by"):
        singleton = native.get(singleton_name)
        support = singleton.get("support") if isinstance(singleton, dict) else None
        if not isinstance(support, list) or not support or any(
            not isinstance(pointer, str) or not pointer.strip() for pointer in support
        ):
            violations.append(f"native.{singleton_name}.support must be a non-empty source-pointer list")
    for list_name in ("success_if", "fail_if", "undecided_if", "decisive_artifacts"):
        values = native.get(list_name)
        if not isinstance(values, list) or not values:
            violations.append(f"native.{list_name} must be a non-empty list")
            continue
        for index, item in enumerate(values):
            support = item.get("support") if isinstance(item, dict) else None
            if not isinstance(support, list) or not support or any(
                not isinstance(pointer, str) or not pointer.strip() for pointer in support
            ):
                violations.append(
                    f"native.{list_name}[{index}].support must be a non-empty source-pointer list"
                )
    stronger_items = checklist.get("stronger", {}).get("additional_conditions", [])
    for index, item in enumerate(stronger_items):
        support = item.get("support") if isinstance(item, dict) else None
        if not isinstance(support, list) or not support or any(
            not isinstance(pointer, str) or not pointer.strip() for pointer in support
        ):
            violations.append(
                f"stronger.additional_conditions[{index}].support must be a non-empty source-pointer list"
            )
        for artifact_index, artifact in enumerate(
            item.get("decisive_artifacts", []) if isinstance(item, dict) else []
        ):
            artifact_support = artifact.get("support") if isinstance(artifact, dict) else None
            if not isinstance(artifact_support, list) or not artifact_support or any(
                not isinstance(pointer, str) or not pointer.strip()
                for pointer in artifact_support
            ):
                violations.append(
                    "stronger.additional_conditions"
                    f"[{index}].decisive_artifacts[{artifact_index}].support "
                    "must be a non-empty source-pointer list"
                )

    for field_name, pointers in _iter_support_pointer_lists(checklist):
        raw_paths = [
            pointer.strip().replace("\\\\", "/").partition(SOURCE_POINTER_SPLIT)[0]
            for pointer in pointers
            if isinstance(pointer, str)
        ]
        if not any(path.startswith("official/") for path in raw_paths):
            violations.append(
                f"{field_name} must include at least one raw official/... source pointer"
            )

"""


def adapt_guardrail_text(origin: str) -> str:
    replacements = (
        ('    allowed = {"case_packet.md"}\n', "    allowed: set[str] = set()\n"),
        (
            "    if len(allowed) == 1:\n",
            "    if not allowed:\n",
        ),
        (
            'f"{field_name} must cite case_packet.md or an exact Source Inventory path: {pointer}"',
            'f"{field_name} must cite an exact Source Inventory path: {pointer}"',
        ),
        (
            "    violations: list[str] = []\n\n    for field_name, pointers in _iter_support_pointer_lists(checklist):",
            "    violations: list[str] = []\n\n"
            + STRICT_SUPPORT_INSERT
            + "    for field_name, pointers in _iter_support_pointer_lists(checklist):",
        ),
    )
    adapted = origin
    for old, new in replacements:
        if adapted.count(old) != 1:
            raise Wave004V6Clean2HardenedError(
                f"guardrail controlled-adaptation anchor count is {adapted.count(old)}, expected 1"
            )
        adapted = adapted.replace(old, new, 1)
    return adapted


def adapt_validator_text(origin: str) -> str:
    old = '"restricted to case_packet.md and its exact Source Inventory paths."\n'
    new = '"restricted to exact Source Inventory paths; case_packet.md is forbidden."\n'
    if origin.count(old) != 1:
        raise Wave004V6Clean2HardenedError(
            "validator controlled-adaptation anchor is not exact"
        )
    return origin.replace(old, new, 1)


def adapt_schema_text(origin: str) -> str:
    """Make raw support structurally mandatory for every JustifiedText value."""

    try:
        schema = json.loads(origin)
    except json.JSONDecodeError as exc:
        raise Wave004V6Clean2HardenedError(
            "checklist schema origin is invalid JSON"
        ) from exc
    justified = (schema.get("$defs") or {}).get("JustifiedText")
    if not isinstance(justified, dict):
        raise Wave004V6Clean2HardenedError("checklist schema lacks $defs.JustifiedText")
    if not canonical_json_equal(justified.get("required"), ["text"]) or (
        "anyOf" not in justified
    ):
        raise Wave004V6Clean2HardenedError(
            "JustifiedText support/rationale origin shape changed"
        )
    support = (justified.get("properties") or {}).get("support")
    if not isinstance(support, dict) or not exact_json_int(support.get("minItems"), 1):
        raise Wave004V6Clean2HardenedError("JustifiedText support minimum is not one")
    justified["required"] = ["text", "support"]
    del justified["anyOf"]
    adapted = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
    roundtrip = json.loads(adapted)["$defs"]["JustifiedText"]
    if not canonical_json_equal(roundtrip.get("required"), ["text", "support"]) or (
        "anyOf" in roundtrip
    ):
        raise Wave004V6Clean2HardenedError(
            "JustifiedText support adaptation did not round-trip"
        )
    return adapted


def adapt_template_text(origin: str) -> str:
    """Remove the rationale-only template path rejected by the frozen schema."""

    old = """  undecided_if:
    - text: ""
      rationale: ""
"""
    new = """  undecided_if:
    - text: ""
      support: []
"""
    if origin.count(old) != 1:
        raise Wave004V6Clean2HardenedError(
            "draft template undecided_if anchor is not exact"
        )
    adapted = origin.replace(old, new, 1)
    if 'undecided_if:\n    - text: ""\n      rationale:' in adapted:
        raise Wave004V6Clean2HardenedError(
            "rationale-only undecided template survived adaptation"
        )
    return adapted


def adapt_drafter_text(origin: str) -> str:
    """Stage canonical sources and isolate every model tool runtime."""

    old_import = """from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
    validate_checklist_guardrails,
)
"""
    new_import = (
        old_import
        + """from neurips_ed_track_minimal.hardened_staging import (  # noqa: E402
    StagingError as HardenedStagingError,
    build_codex_exec_argv as build_hardened_codex_exec_argv,
    coverage_receipt_from_events,
    exact_case_workspace,
    load_frozen_o200k_token_counter,
    materialize_case_workspace,
    staged_prompt,
    unseal_case_workspace_for_cleanup,
    verify_case_workspace,
    verify_workspace_against_frozen_reader_coverage,
)
"""
    )

    old_command = """    return [
        codex_executable,
        "exec",
        "--cd",
        str(workspace_root),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        sandbox,
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]
"""
    new_command = (
        """    if sandbox != "read-only":
        raise DraftChecklistError(
            "clean5 hardened requires the custom read-only permission profile"
        )
    try:
        return build_hardened_codex_exec_argv(
            codex_executable=Path(codex_executable),
            workspace_root=workspace_root,
            schema_path=schema_path,
            output_path=output_path,
            model=model,
            reasoning_effort=reasoning_effort,
            repository_root=Path("""
        + repr(str(REPO_ROOT.resolve()))
        + """),
            wave_tmp_root=Path(os.environ["TMPDIR"]),
            auth_home=Path(os.environ["CODEX_HOME"]),
            original_codex_home=Path("""
        + repr(str(ORIGINAL_CODEX_HOME.resolve()))
        + """),
            isolated_home=Path(os.environ["HOME"]),
            real_home=Path("""
        + repr(str(REAL_HOME))
        + """),
        )
    except HardenedStagingError as exc:
        raise DraftChecklistError(f"invalid isolated Codex command: {exc}") from exc
"""
    )
    old_workspace = """        instructions_path = workspace_root / "draft_instructions.md"
        template_path = workspace_root / "template.yaml"
        case_packet_path = workspace_root / "case_packet.md"
        schema_path = workspace_root / "output_schema.json"
        output_path = workspace_root / "draft_body.json"
        workspace_files = build_codex_workspace_files(
            instructions=instructions,
            template_text=template_text,
            case_packet_text=case_packet_text,
            model_output_schema=model_output_schema,
        )
        instructions_path.write_text(
            workspace_files["draft_instructions.md"], encoding="utf-8"
        )
        template_path.write_text(workspace_files["template.yaml"], encoding="utf-8")
        case_packet_path.write_text(
            workspace_files["case_packet.md"], encoding="utf-8"
        )
        schema_path.write_text(workspace_files["output_schema.json"], encoding="utf-8")

        prompt = build_codex_stdin_prompt(build_codex_read_plan(workspace_files))
"""
    new_workspace = (
        """        try:
            token_counter, tokenizer_binding = load_frozen_o200k_token_counter(
                tokenizer_root=Path("""
        + repr(str(TIKTOKEN_ROOT.resolve()))
        + """),
                merge_table_path=Path("""
        + repr(str(TIKTOKEN_BPE_CACHE.resolve()))
        + """),
            )
            materialization = materialize_case_workspace(
                workspace_root,
                case_packet_text=case_packet_text,
                model_output_schema=model_output_schema,
                token_counter=token_counter,
                tokenizer_binding=tokenizer_binding,
            )
            frozen_coverage_readback = verify_workspace_against_frozen_reader_coverage(
                workspace_root,
                Path("""
        + repr(str(FROZEN_COVERAGE_ROOT))
        + """)
                / materialization["case_unit_id"],
                materialization,
            )
        except HardenedStagingError as exc:
            raise DraftChecklistError(f"canonical packet staging failed: {exc}") from exc
        schema_path = workspace_root / "output_schema.json"
        output_path = workspace_root / "draft_body.json"
        prompt = staged_prompt(
            instructions=instructions,
            template_text=template_text,
            manifest=materialization,
        )
"""
    )
    old_tempdir = """    with tempfile.TemporaryDirectory(prefix="case-checklist-codex-") as temp_dir:
"""
    new_tempdir = """    with exact_case_workspace(
        Path(os.environ["TMPDIR"]),
        extract_case_metadata(case_packet_text)["case_unit_id"],
    ) as temp_dir:
"""
    old_command_call = """        command = build_codex_command(
            workspace_root=workspace_root,
            schema_path=schema_path,
            output_path=output_path,
            model=model,
            reasoning_effort=reasoning_effort,
            sandbox=sandbox,
        )
"""
    new_command_call = """        try:
            command = build_codex_command(
                workspace_root=workspace_root,
                schema_path=schema_path,
                output_path=output_path,
                model=model,
                reasoning_effort=reasoning_effort,
                sandbox=sandbox,
            )
        except BaseException:
            unseal_case_workspace_for_cleanup(workspace_root)
            raise
"""
    old_launch_error = """        except OSError as exc:
            raise DraftChecklistError(f"Failed to launch Codex CLI: {exc}") from exc
"""
    new_launch_error = """        except OSError as exc:
            unseal_case_workspace_for_cleanup(workspace_root)
            raise DraftChecklistError(f"Failed to launch Codex CLI: {exc}") from exc
"""
    old_after = """        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        events, malformed_lines = load_jsonl_objects(stdout)
"""
    new_after = """        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        events, malformed_lines = load_jsonl_objects(stdout)
        try:
            verify_case_workspace(
                workspace_root,
                materialization,
                require_output=completed.returncode == 0,
            )
            coverage_receipt = (
                coverage_receipt_from_events(
                    events,
                    materialization["coverage_requirements"],
                    materialization["reader_operation_expectations"],
                )
                if completed.returncode == 0
                else None
            )
        except HardenedStagingError as exc:
            raise DraftChecklistError(f"staged source coverage/readback failed: {exc}") from exc
        finally:
            unseal_case_workspace_for_cleanup(workspace_root)
"""
    old_receipt = """                "sandbox": sandbox,
                "command": command,
"""
    new_receipt = """                "sandbox": None,
                "permission_profile": "candidate_draft_isolated",
                "permission_profile_workspace_access": "read",
                "permission_profile_network_enabled": False,
                "full_canonical_packet_in_readonly_workspace": True,
                "full_canonical_packet_in_stdin": False,
                "instructions_template_protocol_in_stdin": True,
                "materialization_sha256": materialization["materialization_sha256"],
                "requirements_sha256": materialization["requirements_sha256"],
                "reader_operation_expectations_sha256": materialization[
                    "reader_operation_expectations_sha256"
                ],
                "frozen_coverage_readback": frozen_coverage_readback,
                "materialized_source_count": materialization["materialized_source_count"],
                "coverage_receipt": coverage_receipt,
                "command": command,
"""
    adapted = origin
    for old, new, label in (
        (old_import, new_import, "hardened staging import"),
        (old_command, new_command, "Codex command"),
        (old_tempdir, new_tempdir, "dedicated TMP workspace"),
        (old_workspace, new_workspace, "materialized staged workspace"),
        (
            old_command_call,
            new_command_call,
            "sealed workspace command failure cleanup",
        ),
        (old_launch_error, new_launch_error, "sealed workspace launch failure cleanup"),
        (old_after, new_after, "workspace namespace readback"),
        (old_receipt, new_receipt, "permission receipt"),
    ):
        if adapted.count(old) != 1:
            raise Wave004V6Clean2HardenedError(
                f"drafter controlled-adaptation anchor {label} count is {adapted.count(old)}, expected 1"
            )
        adapted = adapted.replace(old, new, 1)
    return adapted


def runtime_environment_payload(python_path: Path) -> dict[str, Any]:
    probe = r"""
import importlib.metadata as metadata
import json
import pathlib
import sys
names = json.loads(sys.argv[1])
rows = []
for name in names:
    dist = metadata.distribution(name)
    files = []
    for item in sorted(dist.files or [], key=lambda value: str(value)):
        path = pathlib.Path(dist.locate_file(item))
        if path.suffix == ".pyc" or "__pycache__" in path.parts or not path.exists():
            continue
        if path.is_file() or path.is_symlink():
            files.append(str(path.absolute()))
    rows.append({"name": name, "version": dist.version, "files": files})
print(json.dumps({"sys_executable": sys.executable, "version": sys.version, "distributions": rows}))
"""
    completed = subprocess.run(
        [str(python_path), "-I", "-c", probe, json.dumps(RUNTIME_DISTRIBUTIONS)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0 or completed.stderr.strip():
        raise Wave004V6Clean2HardenedError(
            f"runtime closure probe failed: rc={completed.returncode}, stderr={completed.stderr}"
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise Wave004V6Clean2HardenedError(
            "runtime closure probe emitted invalid JSON"
        ) from exc
    distributions = []
    for row in result.get("distributions") or []:
        files = []
        for raw in row.get("files") or []:
            path = Path(raw)
            files.append(
                executable_binding(path)
                if path.is_symlink()
                else regular_file_binding(path)
            )
        if not files:
            raise Wave004V6Clean2HardenedError(
                f"runtime distribution has no bound files: {row}"
            )
        distributions.append(
            {"name": row["name"], "version": row["version"], "files": files}
        )
    if tuple(row["name"] for row in distributions) != RUNTIME_DISTRIBUTIONS:
        raise Wave004V6Clean2HardenedError(
            "runtime distribution closure order/set changed"
        )
    payload = {
        "schema_version": "androidworld_candidate116_python_runtime_closure/v1",
        "production_namespace": GENERATION_ID,
        "status": "fully_byte_bound",
        "python_invocation": executable_binding(python_path),
        "python_version": result.get("version"),
        "pyvenv_cfg": regular_file_binding(REPO_ROOT / ".venv" / "pyvenv.cfg"),
        "distributions": distributions,
        "distribution_count": len(distributions),
        "policy": (
            "all non-stdlib distributions imported by the frozen drafter, validator, "
            "and batch runner are versioned and every installed non-pyc file is byte-bound"
        ),
    }
    return add_self_hash(payload, "runtime_closure_sha256")


def build_snapshot(
    stage: Path,
    python_path: Path,
    origin_payloads: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    stage.mkdir(mode=0o700)
    origins: list[dict[str, Any]] = []
    adaptations: list[dict[str, Any]] = []
    for name, (origin, relative) in NEURIPS_COPY_MAP.items():
        origin_payload = origin_payloads.get(name) or {}
        origin_binding = origin_payload.get("binding")
        origin_bytes = origin_payload.get("bytes")
        if not isinstance(origin_binding, Mapping) or not isinstance(
            origin_bytes, bytes
        ):
            raise Wave004V6Clean2HardenedError(
                f"missing start-captured snapshot origin: {name}"
            )
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        origin_text: str | None = None
        adapted_text: str | None = None
        if name == "checklist_guardrails":
            origin_text = origin_bytes.decode("utf-8")
            adapted_text = adapt_guardrail_text(origin_text)
        elif name == "validator":
            origin_text = origin_bytes.decode("utf-8")
            adapted_text = adapt_validator_text(origin_text)
        elif name == "drafter":
            origin_text = origin_bytes.decode("utf-8")
            adapted_text = adapt_drafter_text(origin_text)
        elif name == "checklist_schema":
            origin_text = origin_bytes.decode("utf-8")
            adapted_text = adapt_schema_text(origin_text)
        elif name == "draft_template":
            origin_text = origin_bytes.decode("utf-8")
            adapted_text = adapt_template_text(origin_text)
        if adapted_text is None:
            destination.write_bytes(origin_bytes)
        else:
            destination.write_text(adapted_text, encoding="utf-8")
            diff = "".join(
                difflib.unified_diff(
                    origin_text.splitlines(keepends=True),
                    adapted_text.splitlines(keepends=True),
                    fromfile=f"live/{origin.name}",
                    tofile=f"snapshot/{origin.name}",
                )
            )
            diff_path = stage / "controlled_adaptations" / f"{name}.diff"
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            diff_path.write_text(diff, encoding="utf-8")
            adaptations.append(
                {
                    "name": name,
                    "policy": (
                        "minimum fail-closed adaptation: schema/template/guardrail/validator "
                        "require exact non-empty raw-official support and forbid the "
                        "case_packet.md alias; drafter keeps the full packet byte-exact in a "
                        "sealed workspace, binds every raw official Inventory member (same-SHA "
                        "aliases read once), enforces ordered tail-hashed bounded receipts, and "
                        "uses a custom read-only/network-disabled deny profile"
                    ),
                    "origin_sha256": origin_binding["sha256"],
                    "adapted_sha256": sha256_file(destination),
                    "diff_relative_path": diff_path.relative_to(stage).as_posix(),
                    "diff_sha256": sha256_file(diff_path),
                }
            )
        origins.append(
            {
                "name": name,
                "live_origin": dict(origin_binding),
                "snapshot_relative_path": relative,
                "snapshot_sha256": sha256_file(destination),
                "byte_identical": origin_binding["sha256"] == sha256_file(destination),
            }
        )

    supplement_destination = (
        stage
        / "neurips_ed_track_minimal"
        / "prompts"
        / "androidworld_fresh_canonical_v7.supplement.md"
    )
    supplement_payload = origin_payloads.get("prompt_supplement") or {}
    supplement_binding = supplement_payload.get("binding")
    supplement_bytes = supplement_payload.get("bytes")
    if (
        not isinstance(supplement_binding, Mapping)
        or not isinstance(supplement_bytes, bytes)
        or supplement_binding.get("sha256") != EXPECTED_SUPPLEMENT_SHA256
    ):
        raise Wave004V6Clean2HardenedError(
            "reviewed canonical v7 supplement hash changed"
        )
    supplement_destination.write_bytes(supplement_bytes)
    origins.append(
        {
            "name": "prompt_supplement",
            "live_origin": dict(supplement_binding),
            "snapshot_relative_path": supplement_destination.relative_to(
                stage
            ).as_posix(),
            "snapshot_sha256": sha256_file(supplement_destination),
            "byte_identical": True,
            "reviewed_sha256": EXPECTED_SUPPLEMENT_SHA256,
        }
    )

    wrapper_dir = stage / "wave004_v6_clean5_hardened"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    for name, origin in (
        ("frozen_wrapper", LIVE_LAUNCHER),
        ("wave004_v6_clean5_hardened_common", LIVE_COMMON),
        ("wave004_v6_clean5_hardened_staging", STAGING_HELPER),
        ("readonly_snapshot_helper", READONLY_HELPER),
    ):
        origin_payload = origin_payloads.get(name) or {}
        origin_binding = origin_payload.get("binding")
        origin_bytes = origin_payload.get("bytes")
        if not isinstance(origin_binding, Mapping) or not isinstance(
            origin_bytes, bytes
        ):
            raise Wave004V6Clean2HardenedError(
                f"missing start-captured wrapper origin: {name}"
            )
        destination = wrapper_dir / origin.name
        destination.write_bytes(origin_bytes)
        origins.append(
            {
                "name": name,
                "live_origin": dict(origin_binding),
                "snapshot_relative_path": destination.relative_to(stage).as_posix(),
                "snapshot_sha256": sha256_file(destination),
                "byte_identical": True,
            }
        )

    runtime_payload = runtime_environment_payload(python_path)
    runtime_path = stage / "runtime_environment_manifest.json"
    write_json_create_once(runtime_path, runtime_payload)

    forbidden_names = {
        "draft_source_pointer_strict_v2.supplement.md",
        "androidworld_full_regeneration_v5.supplement.md",
        "androidworld_fresh_canonical_v6.supplement.md",
        "androidworld_source_pointer_strict_v3.supplement.md",
    }
    if any(path.name in forbidden_names for path in stage.rglob("*")):
        raise Wave004V6Clean2HardenedError(
            "snapshot contains a forbidden legacy/wrapper supplement"
        )

    files = []
    for path in sorted(
        stage.rglob("*"), key=lambda item: item.relative_to(stage).as_posix()
    ):
        if path.is_symlink():
            raise Wave004V6Clean2HardenedError(f"snapshot contains symlink: {path}")
        if path.is_file() and path.name != "snapshot_manifest.json":
            files.append(
                {
                    "relative_path": path.relative_to(stage).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    manifest = {
        "schema_version": SNAPSHOT_SCHEMA,
        "production_namespace": GENERATION_ID,
        "status": "frozen_create_once",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "snapshot_root_absolute": str(SNAPSHOT_ROOT),
        "file_count": len(files),
        "files": files,
        "files_sha256": canonical_sha256(files),
        "live_origins": origins,
        "controlled_adaptations": adaptations,
        "runtime_environment_manifest_relative": runtime_path.relative_to(
            stage
        ).as_posix(),
        "runtime_environment_manifest_sha256": sha256_file(runtime_path),
        "effective_prompt_policy": (
            "exactly frozen live base draft prompt plus reviewed staged canonical v7 supplement; "
            "no legacy pointer supplement and no historical draft/warning packet"
        ),
        "permission_policy": "all files 0444 and all directories 0555 after finalization",
    }
    manifest = add_self_hash(manifest, "snapshot_sha256")
    write_json_create_once(stage / "snapshot_manifest.json", manifest)
    return manifest


def make_snapshot_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            path.chmod(0o444)
    for path in sorted(
        (item for item in root.rglob("*") if item.is_dir()), reverse=True
    ):
        path.chmod(0o555)
    root.chmod(0o555)


def native_batch_command(
    *,
    python_path: Path,
    tool_bindings: Mapping[str, Mapping[str, Any]],
    packet_inputs: list[Mapping[str, Any]],
    case_order: list[str],
    token_budgets: str,
    codex_timeout: int,
    large_codex_timeout: int,
) -> list[str]:
    max_packet_size = max(int(row["packet"]["size_bytes"]) for row in packet_inputs)
    return [
        str(python_path.absolute()),
        str(tool_bindings["batch_runner"]["path"]),
        "--case-packet-root",
        str(PACKET_ROOT.resolve()),
        "--output-root",
        str(WAVE004_ROOT),
        "--provider",
        "codex",
        "--model",
        EXPECTED_MODEL,
        "--reasoning-effort",
        EXPECTED_REASONING,
        "--token-budgets",
        token_budgets,
        "--max-parallel",
        str(PARALLELISM),
        "--large-max-parallel",
        str(PARALLELISM),
        "--large-case-threshold-bytes",
        str(max_packet_size + 1),
        "--http-timeout-seconds",
        "180",
        "--large-http-timeout-seconds",
        "480",
        "--codex-timeout-seconds",
        str(codex_timeout),
        "--large-codex-timeout-seconds",
        str(large_codex_timeout),
        "--codex-sandbox",
        EXPECTED_SANDBOX,
        "--prompt-supplement",
        str(tool_bindings["prompt_supplement"]["path"]),
        "--sort-by",
        "name",
        "--sleep-seconds",
        "2.0",
        "--quality-check",
        "none",
        "--case-ids",
        ",".join(case_order),
    ]


def main() -> int:
    args = parse_args()
    if PRODUCTION_NAMESPACE != GENERATION_ID:
        raise Wave004V6Clean2HardenedError(
            "staging/common production namespaces are not the exact clean5 identity"
        )
    verify_clean5_namespace_plan()
    approval, approval_file_binding = verify_reviewed_candidate_approval(
        args.reviewed_candidate_approval
    )
    owner_nonce_verification = consume_and_verify_nonce(
        approval,
        hash_field="owner_nonce_sha256",
        environment_variable=OWNER_NONCE_ENV,
        label="clean5 candidate owner",
    )
    initial_script_bindings = {
        name: dict(binding) for name, binding in approval["scripts"].items()
    }
    initial_core_bindings = capture_core_input_bindings()
    snapshot_origin_payloads = capture_snapshot_origin_payloads(
        initial_core_bindings, initial_script_bindings
    )
    initial_tokenizer = tokenizer_tree_binding()
    if PERMISSION_PROFILE_NAME != EXPECTED_PERMISSION_PROFILE:
        raise Wave004V6Clean2HardenedError(
            "staging/common permission profile names differ"
        )
    if (
        args.model != EXPECTED_MODEL
        or args.reasoning_effort != EXPECTED_REASONING
        or args.max_parallel != PARALLELISM
        or args.codex_timeout_seconds < 1800
        or args.large_codex_timeout_seconds < args.codex_timeout_seconds
    ):
        raise Wave004V6Clean2HardenedError(
            "clean5 hardened model/reasoning/concurrency/timeout policy is immutable"
        )
    try:
        budgets = [int(value) for value in args.token_budgets.split(",")]
    except ValueError as exc:
        raise Wave004V6Clean2HardenedError("token budgets are not integers") from exc
    if budgets != [32_000]:
        raise Wave004V6Clean2HardenedError(
            "formal wave requires exactly one 32000-token attempt per case; retries are forbidden"
        )

    for path, label in (
        (SNAPSHOT_ROOT, "clean5 hardened toolchain snapshot"),
        (CONFIG_PATH, "clean5 hardened draft config"),
        (PRELOCK_PATH, "clean5 hardened prelock"),
        (READONLY_BEFORE, "clean5 hardened read-only snapshot"),
        (CLAIM_ROOT, "clean5 hardened prelock claim"),
        (WAVE004_ROOT, "wave_004 raw output"),
    ):
        if path.exists() or path.is_symlink():
            raise Wave004V6Clean2HardenedError(
                f"{label} already exists; refusing rewrite: {path}"
            )
    require_empty_or_absent(CANONICAL_DRAFTS, "canonical drafts")
    require_empty_or_absent(CANONICAL_CONTRACTS, "canonical contracts/drafts")
    if WAVE003_ROOT.exists() or WAVE003_ROOT.is_symlink():
        raise Wave004V6Clean2HardenedError("superseded wave_003 bytes still exist")

    incident = load_json(SUPERSESSION_INCIDENT, "wave_003 supersession incident")
    verify_self_hash(incident, "incident_sha256", "wave_003 supersession incident")
    if (
        incident.get("promotion_forbidden") is not True
        or incident.get("old_draft_reuse_forbidden") is not True
        or incident.get("replacement_generation_id") != "wave_004"
    ):
        raise Wave004V6Clean2HardenedError(
            "wave_003 supersession incident does not forbid reuse"
        )
    prior_abort = load_json(ABORTED_CLEAN2_INCIDENT, "clean2 prelock abort incident")
    verify_self_hash(prior_abort, "incident_sha256", "clean2 prelock abort incident")
    if (
        prior_abort.get("candidate_generation_id") != "wave_004_v6_clean2_hardened"
        or prior_abort.get("replacement_generation_id") != "wave_004_v6_clean3_hardened"
        or prior_abort.get("reuse_forbidden") is not True
        or not exact_json_int(prior_abort.get("model_call_count"), 0)
        or prior_abort.get("status")
        != "aborted_before_snapshot_config_prelock_or_model_call"
    ):
        raise Wave004V6Clean2HardenedError("clean2 abort lineage is not exact")
    clean3_revocation = load_json(
        CLEAN3_REVOCATION_INCIDENT, "clean3 unattributed candidate-review revocation"
    )
    verify_self_hash(
        clean3_revocation,
        "incident_sha256",
        "clean3 unattributed candidate-review revocation",
    )
    effects = clean3_revocation.get("effects_at_revocation") or {}
    if (
        clean3_revocation.get("schema_version")
        != "androidworld_candidate116_candidate_review_provenance_incident/v1"
        or clean3_revocation.get("status") != "revoked_before_prelock_or_model_call"
        or clean3_revocation.get("candidate_generation_id")
        != "wave_004_v6_clean3_hardened"
        or clean3_revocation.get("replacement_generation_id")
        != "wave_004_v6_clean4_hardened"
        or clean3_revocation.get("reuse_forbidden") is not True
        or not exact_json_int(effects.get("model_call_count"), 0)
        or any(
            effects.get(name) is not False
            for name in (
                "draft_config_created",
                "isolated_runtime_roots_created",
                "prelock_created",
                "raw_wave_created",
                "toolchain_snapshot_created",
            )
        )
    ):
        raise Wave004V6Clean2HardenedError("clean3 revocation lineage is not exact")
    clean3_abort = load_json(
        CLEAN3_PRELOCK_ABORT_INCIDENT, "clean3 prelock abort incident"
    )
    verify_self_hash(clean3_abort, "incident_sha256", "clean3 prelock abort incident")
    if (
        clean3_abort.get("schema_version")
        != "androidworld_candidate116_prelock_abort_incident/v1"
        or clean3_abort.get("status") != "aborted_before_config_prelock_or_model_call"
        or clean3_abort.get("candidate_generation_id") != "wave_004_v6_clean3_hardened"
        or clean3_abort.get("replacement_generation_id")
        != "wave_004_v6_clean4_hardened"
        or clean3_abort.get("reuse_forbidden") is not True
        or not exact_json_int(clean3_abort.get("model_call_count"), 0)
    ):
        raise Wave004V6Clean2HardenedError("clean3 prelock abort lineage is not exact")
    clean4_revocation = load_json(
        CLEAN4_MIXED_TIME_REVOCATION_INCIDENT,
        "clean4 unattributed mixed-time prelock revocation",
    )
    verify_self_hash(
        clean4_revocation,
        "incident_sha256",
        "clean4 unattributed mixed-time prelock revocation",
    )
    clean4_effects = clean4_revocation.get("effects_at_revocation") or {}
    if (
        clean4_revocation.get("schema_version")
        != "androidworld_candidate116_unattributed_mixed_time_prelock_incident/v1"
        or clean4_revocation.get("status") != "revoked_before_first_model_call"
        or clean4_revocation.get("candidate_generation_id")
        != "wave_004_v6_clean4_hardened"
        or clean4_revocation.get("replacement_generation_id") != GENERATION_ID
        or clean4_revocation.get("reuse_forbidden") is not True
        or not exact_json_int(clean4_effects.get("model_call_count"), 0)
        or clean4_effects.get("raw_wave_launched") is not False
        or not exact_json_int(clean4_effects.get("raw_draft_file_count"), 0)
        or not exact_json_int(clean4_effects.get("canonical_draft_file_count"), 0)
        or not exact_json_int(clean4_effects.get("canonical_contract_file_count"), 0)
        or clean4_effects.get("first_model_call_authorized") is not False
        or not clean4_revocation.get("live_script_hash_mismatches")
    ):
        raise Wave004V6Clean2HardenedError(
            "clean4 mixed-time prelock revocation lineage is not exact"
        )

    freeze, packet_index, packet_inputs, case_order = verify_frozen_inputs()
    capacity, coverage_documents = build_capacity_manifest(
        packet_inputs=packet_inputs,
        case_order=case_order,
        max_output_tokens=max(budgets),
        core_bindings=initial_core_bindings,
        expected_tokenizer=initial_tokenizer,
    )
    runtime_roots = planned_isolated_runtime_roots()
    environment = exact_closed_environment()
    codex_path_raw = shutil.which("codex", path=environment["PATH"])
    if codex_path_raw != "/opt/homebrew/bin/codex":
        raise Wave004V6Clean2HardenedError(
            f"Codex CLI did not resolve exactly: {codex_path_raw}"
        )
    codex_path = Path(codex_path_raw)
    host_probe_environment = dict(environment)
    host_probe_environment.update(
        {
            "CODEX_HOME": str(ORIGINAL_CODEX_HOME),
            "HOME": str(REAL_HOME),
            "TMPDIR": str(
                Path(os.environ.get("TMPDIR") or tempfile.gettempdir()).resolve()
            ),
        }
    )
    version = exact_codex_version(codex_path, host_probe_environment)
    feature_surface = codex_feature_surface_binding(codex_path, host_probe_environment)
    codex_binding = executable_binding(codex_path)
    python_path = REPO_ROOT / ".venv" / "bin" / "python"
    python_binding = executable_binding(python_path)

    CLAIM_ROOT.parent.mkdir(parents=True, exist_ok=True)
    os.mkdir(CLAIM_ROOT, 0o700)
    coverage_index = write_frozen_reader_coverage(
        coverage_documents=coverage_documents,
        case_order=case_order,
    )
    capacity_path = CLAIM_ROOT / "staged_capacity.json"
    write_json_create_once(capacity_path, capacity)
    os.chmod(capacity_path, 0o444)
    stage_snapshot = CLAIM_ROOT / "toolchain_snapshot.stage"
    manifest = build_snapshot(
        stage_snapshot,
        python_path,
        snapshot_origin_payloads,
    )
    SNAPSHOT_ROOT.parent.mkdir(parents=True, exist_ok=True)
    os.replace(stage_snapshot, SNAPSHOT_ROOT)
    make_snapshot_read_only(SNAPSHOT_ROOT)

    snapshot_package = SNAPSHOT_ROOT / "neurips_ed_track_minimal"
    tool_paths = {
        "draft_prompt": snapshot_package / "prompts" / "draft_case_checklist.prompt.md",
        "prompt_supplement": snapshot_package
        / "prompts"
        / "androidworld_fresh_canonical_v7.supplement.md",
        "draft_template": snapshot_package
        / "templates"
        / "case_checklist.template.yaml",
        "checklist_schema": snapshot_package / "schemas" / "case_checklist.schema.json",
        "checklist_guardrails": snapshot_package / "checklist_guardrails.py",
        "hardened_staging": snapshot_package / "hardened_staging.py",
        "drafter": snapshot_package / "scripts" / "draft_case_checklist.py",
        "batch_runner": snapshot_package / "scripts" / "run_draft_batch.py",
        "validator": snapshot_package / "scripts" / "checklist_validator.py",
    }
    tool_bindings = {
        name: regular_file_binding(path) for name, path in sorted(tool_paths.items())
    }
    effective_prompt = (
        tool_paths["draft_prompt"].read_text(encoding="utf-8").rstrip()
        + "\n\n"
        + tool_paths["prompt_supplement"].read_text(encoding="utf-8").strip()
        + "\n"
    )
    prompt_composition = {
        "ordered_components": [
            tool_bindings["draft_prompt"],
            tool_bindings["prompt_supplement"],
        ],
        "separator": "base.rstrip() + two newlines + supplement.strip() + newline",
        "effective_prompt_sha256": canonical_sha256({"prompt": effective_prompt}),
        "legacy_supplements_included": [],
        "historical_draft_or_warning_input_included": False,
    }
    prompt_composition["composition_sha256"] = canonical_sha256(prompt_composition)

    readonly_helper = load_module(
        READONLY_HELPER, "wave004_v6_clean5_hardened_readonly_preparer"
    )
    readonly = readonly_helper.readonly_operation_snapshot(
        phase="before_candidate116_wave004_v6_clean5_hardened",
        repo_root=REPO_ROOT,
        work_root=WORK_ROOT,
    )
    readonly["snapshot_sha256"] = canonical_sha256(readonly)
    write_json_create_once(READONLY_BEFORE, readonly)

    snapshot_binding = regular_file_binding(SNAPSHOT_MANIFEST)
    snapshot_binding["snapshot_sha256"] = manifest["snapshot_sha256"]
    frozen_reader_coverage = {
        "root_absolute": str(FROZEN_COVERAGE_ROOT),
        "case_count": coverage_index["case_count"],
        "case_order_sha256": coverage_index["case_order_sha256"],
        "expected_case_files": coverage_index["expected_case_files"],
        "index": regular_file_binding(FROZEN_COVERAGE_INDEX)
        | {"coverage_index_sha256": coverage_index["coverage_index_sha256"]},
    }
    command = native_batch_command(
        python_path=python_path,
        tool_bindings=tool_bindings,
        packet_inputs=packet_inputs,
        case_order=case_order,
        token_budgets=args.token_budgets,
        codex_timeout=args.codex_timeout_seconds,
        large_codex_timeout=args.large_codex_timeout_seconds,
    )
    frozen_wrapper = regular_file_binding(
        SNAPSHOT_ROOT / "wave004_v6_clean5_hardened" / LIVE_LAUNCHER.name
    )
    frozen_common = regular_file_binding(
        SNAPSHOT_ROOT / "wave004_v6_clean5_hardened" / LIVE_COMMON.name
    )
    frozen_readonly_helper = regular_file_binding(
        SNAPSHOT_ROOT / "wave004_v6_clean5_hardened" / READONLY_HELPER.name
    )
    auth_receipt = {
        "schema_version": "androidworld_candidate116_codex_auth_prelock/v1",
        "production_namespace": GENERATION_ID,
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "version": version,
        "login_status": "deferred_until_final_go_launcher_isolation",
        "isolated_auth_copy_state": "not_created_at_prelock",
        "closed_environment_sha256": canonical_sha256(environment),
    }
    auth_receipt["auth_receipt_sha256"] = canonical_sha256(auth_receipt)

    def revalidate_prepublication_inputs() -> None:
        verify_prepublication_inputs_unchanged(
            approval_path=args.reviewed_candidate_approval,
            approval=approval,
            approval_file_binding=approval_file_binding,
            script_bindings=initial_script_bindings,
            core_bindings=initial_core_bindings,
            snapshot_origin_payloads=snapshot_origin_payloads,
            tokenizer=initial_tokenizer,
            freeze=freeze,
            packet_index=packet_index,
            packet_inputs=packet_inputs,
            case_order=case_order,
            snapshot_manifest=manifest,
        )

    frozen_llm_roles = dict((freeze.get("llm") or {}).get("llm_roles") or {})
    config = {
        "schema_version": CONFIG_SCHEMA,
        "status": "prelocked_before_first_model_call",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_id": GENERATION_ID,
        "provider": "codex_cli",
        "auth_mode": "codex_login_chatgpt",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "model_verbosity": "low",
        "sandbox": EXPECTED_SANDBOX,
        "ephemeral": True,
        "ignore_user_config": True,
        "max_parallel": PARALLELISM,
        "large_max_parallel": PARALLELISM,
        "sample_interval_seconds": 0.1,
        "token_budgets": budgets,
        "attempt_policy": {
            "expected_attempt_index": 1,
            "attempts_per_case": 1,
            "implicit_retry_allowed": False,
            "failed_case_followup": "separate_same_input_repair_generation_namespace_only",
        },
        "codex_timeout_seconds": args.codex_timeout_seconds,
        "large_codex_timeout_seconds": args.large_codex_timeout_seconds,
        "codex_cli": codex_binding,
        "python_runtime": python_binding,
        "child_environment": environment,
        "child_environment_sha256": canonical_sha256(environment),
        "isolated_runtime_roots": runtime_roots,
        "toolchain_snapshot": snapshot_binding,
        "tool_bindings": tool_bindings,
        "reviewed_candidate_approval": dict(approval_file_binding)
        | {"approval_sha256": approval["approval_sha256"]},
        "owner_nonce_verification": owner_nonce_verification,
        "staged_capacity": regular_file_binding(capacity_path)
        | {"capacity_sha256": capacity["capacity_sha256"]},
        "frozen_reader_coverage": frozen_reader_coverage,
        "prior_candidate_abort": dict(initial_core_bindings["clean2_abort"])
        | {"incident_sha256": prior_abort["incident_sha256"]},
        "prior_clean3_revocation": dict(initial_core_bindings["clean3_revocation"])
        | {"incident_sha256": clean3_revocation["incident_sha256"]},
        "prior_clean3_prelock_abort": dict(
            initial_core_bindings["clean3_prelock_abort"]
        )
        | {"incident_sha256": clean3_abort["incident_sha256"]},
        "prior_clean4_mixed_time_revocation": dict(
            initial_core_bindings["clean4_mixed_time_revocation"]
        )
        | {"incident_sha256": clean4_revocation["incident_sha256"]},
        "frozen_wrapper": frozen_wrapper,
        "frozen_common": frozen_common,
        "frozen_readonly_helper": frozen_readonly_helper,
        "prompt_composition": prompt_composition,
        "native_batch_command": command,
        "native_batch_command_sha256": canonical_sha256(command),
        "repository_root_absolute": str(REPO_ROOT),
        "work_root_absolute": str(WORK_ROOT),
        "original_codex_home_absolute": str(ORIGINAL_CODEX_HOME),
        "real_home_absolute": str(REAL_HOME),
        "snapshot_root_absolute": str(SNAPSHOT_ROOT),
        "canonical_packet_root_absolute": str(PACKET_ROOT.resolve()),
        "output_root_absolute": str(WAVE004_ROOT),
        "concurrency_samples_absolute": str(
            WAVE004_ROOT / "_concurrency_samples.jsonl"
        ),
        "canonical_drafts_absolute": str(CANONICAL_DRAFTS),
        "canonical_contracts_absolute": str(CANONICAL_CONTRACTS),
        "model_input_policy": {
            "packet_kind": "canonical_full_case_packet",
            "packet_count": CASE_COUNT,
            "packet_wrapper_used": False,
            "model_delivery": "sealed_staged_raw_source_reader",
            "full_packet_in_readonly_workspace": True,
            "full_packet_in_stdin": False,
            "raw_official_inventory_trust_boundary": "all_members_mandatory",
            "same_sha_alias_physical_read_policy": "one_read_only_after_all_aliases_bound",
            "ast_and_navigation_role": "cross_audit_never_exclusion_filter",
            "dynamic_reader_command_allowed": False,
            "reader_receipt_binding": "ordered_same_id_item_completed_terminal_envelope",
            "coverage_receipt_required_per_case": True,
            "provider_output_fields": ["native", "stronger"],
            "wrapper_injected_fields": [
                "schema_version",
                "domain",
                "case_unit_id",
                "task_id",
            ],
            "historical_draft_bytes_used": False,
            "historical_qc_or_warning_text_used": False,
            "effective_prompt_components": [
                "frozen_base_prompt",
                "clean_canonical_v7_staged",
            ],
        },
        "frozen_context_agents_config": dict(initial_core_bindings["agents_config"]),
        "frozen_context_llm_roles": frozen_llm_roles,
        "frozen_context_llm_roles_sha256": canonical_sha256(frozen_llm_roles),
        "context_role_note": (
            "the fe2018 agents config/llm_roles are bound provenance context; the "
            "actual fresh drafter is independently and explicitly locked above to Codex CLI"
        ),
        "codex_auth_at_prelock": auth_receipt,
        "codex_feature_surface": feature_surface,
    }
    config = add_self_hash(config, "config_sha256")
    revalidate_prepublication_inputs()
    write_json_create_once(CONFIG_STAGE_PATH, config)
    os.chmod(CONFIG_STAGE_PATH, 0o444)
    config_final_binding = future_regular_file_binding(CONFIG_STAGE_PATH, CONFIG_PATH)

    prelock = {
        "schema_version": PRELOCK_SCHEMA,
        "status": "frozen_before_first_model_call",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_id": GENERATION_ID,
        "case_count": CASE_COUNT,
        "case_order": case_order,
        "case_order_sha256": canonical_sha256(case_order),
        "packet_inputs": packet_inputs,
        "packet_inputs_sha256": canonical_sha256(packet_inputs),
        "packet_index": dict(initial_core_bindings["packet_index"]),
        "packet_index_payload_sha256": canonical_sha256(packet_index),
        "old_packet_source_freeze": dict(
            initial_core_bindings["old_packet_source_freeze"]
        )
        | {"freeze_sha256": freeze["freeze_sha256"]},
        "static_acceptance": dict(initial_core_bindings["static_acceptance"]),
        "source_bundle": dict(initial_core_bindings["source_bundle"]),
        "agents_config": dict(initial_core_bindings["agents_config"]),
        "llm_roles": frozen_llm_roles,
        "llm_roles_sha256": canonical_sha256(frozen_llm_roles),
        "tool_bindings": tool_bindings,
        "toolchain_snapshot": snapshot_binding,
        "reviewed_candidate_approval": config["reviewed_candidate_approval"],
        "owner_nonce_verification": config["owner_nonce_verification"],
        "staged_capacity": config["staged_capacity"],
        "frozen_reader_coverage": frozen_reader_coverage,
        "isolated_runtime_roots": runtime_roots,
        "codex_feature_surface": feature_surface,
        "draft_config": config_final_binding
        | {"config_sha256": config["config_sha256"]},
        "readonly_before_snapshot": regular_file_binding(READONLY_BEFORE)
        | {"snapshot_sha256": readonly["snapshot_sha256"]},
        "wave003_supersession": dict(initial_core_bindings["wave003_supersession"])
        | {"incident_sha256": incident["incident_sha256"]},
        "prior_candidate_abort": config["prior_candidate_abort"],
        "prior_clean3_revocation": config["prior_clean3_revocation"],
        "prior_clean3_prelock_abort": config["prior_clean3_prelock_abort"],
        "prior_clean4_mixed_time_revocation": config[
            "prior_clean4_mixed_time_revocation"
        ],
        "canonical_output_gate": {
            "raw_wave": str(WAVE004_ROOT),
            "canonical_drafts": str(CANONICAL_DRAFTS),
            "canonical_contracts": str(CANONICAL_CONTRACTS),
            "raw_wave_create_once": True,
            "canonical_outputs_must_remain_empty_until_qc_semantic_root_116_of_116": True,
        },
        "first_model_call_authorized": False,
        "first_model_call_authorization_status": "pending_independent_prelock_audit",
        "launch_requires_separate_create_once_final_go": True,
        "freeze_authorized": False,
        "freeze_requires": (
            "deterministic QC, independent semantic review, and explicit root acceptance 116/116"
        ),
    }
    prelock = add_self_hash(prelock, "prelock_sha256")
    try:
        revalidate_prepublication_inputs()
    except BaseException:
        discard_prepublication_stage()
        raise
    write_json_create_once(PRELOCK_STAGE_PATH, prelock)
    os.chmod(PRELOCK_STAGE_PATH, 0o444)
    prelock_final_binding = future_regular_file_binding(
        PRELOCK_STAGE_PATH, PRELOCK_PATH
    )
    try:
        revalidate_prepublication_inputs()
        if CONFIG_PATH.exists() or PRELOCK_PATH.exists():
            raise Wave004V6Clean2HardenedError(
                "config/prelock final path appeared before atomic publication"
            )
    except BaseException:
        discard_prepublication_stage()
        raise
    os.replace(CONFIG_STAGE_PATH, CONFIG_PATH)
    try:
        os.replace(PRELOCK_STAGE_PATH, PRELOCK_PATH)
    except BaseException:
        if canonical_json_equal(
            regular_file_binding(CONFIG_PATH), config_final_binding
        ):
            os.chmod(CONFIG_PATH, 0o600)
            CONFIG_PATH.unlink()
        discard_prepublication_stage()
        raise
    if not canonical_json_equal(
        regular_file_binding(CONFIG_PATH), config_final_binding
    ) or not canonical_json_equal(
        regular_file_binding(PRELOCK_PATH), prelock_final_binding
    ):
        raise Wave004V6Clean2HardenedError(
            "atomically published config/prelock bindings differ from stage"
        )

    claim_receipt = add_self_hash(
        {
            "schema_version": PRELOCK_CLAIM_SCHEMA,
            "status": "complete_no_model_call",
            "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "prelock": prelock_final_binding
            | {"prelock_sha256": prelock["prelock_sha256"]},
            "config": config_final_binding | {"config_sha256": config["config_sha256"]},
            "toolchain_snapshot": snapshot_binding,
            "reviewed_candidate_approval": config["reviewed_candidate_approval"],
            "owner_nonce_verification": config["owner_nonce_verification"],
            "staged_capacity": config["staged_capacity"],
            "frozen_reader_coverage": frozen_reader_coverage,
            "prior_candidate_abort": config["prior_candidate_abort"],
            "prior_clean3_revocation": config["prior_clean3_revocation"],
            "prior_clean3_prelock_abort": config["prior_clean3_prelock_abort"],
            "prior_clean4_mixed_time_revocation": config[
                "prior_clean4_mixed_time_revocation"
            ],
            "isolated_runtime_roots": runtime_roots,
            "readonly_before": regular_file_binding(READONLY_BEFORE)
            | {"snapshot_sha256": readonly["snapshot_sha256"]},
            "model_call_count": 0,
        },
        "claim_receipt_sha256",
    )
    write_json_create_once(CLAIM_ROOT / "claim_receipt.json", claim_receipt)
    os.chmod(CLAIM_ROOT / "claim_receipt.json", 0o444)
    print(
        json.dumps(
            {
                "status": "prelocked_no_model_call",
                "prelock": str(PRELOCK_PATH),
                "prelock_sha256": prelock["prelock_sha256"],
                "frozen_launcher": frozen_wrapper["path"],
                "launch_command": [
                    str(python_path.absolute()),
                    frozen_wrapper["path"],
                    "--prelock",
                    str(PRELOCK_PATH),
                    "--launch-approval",
                    "<create-once-independent-final-go.json>",
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Wave004V6Clean2HardenedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
