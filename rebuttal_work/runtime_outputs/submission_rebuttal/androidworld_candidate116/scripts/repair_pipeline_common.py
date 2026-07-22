#!/usr/bin/env python3
"""Shared fail-closed primitives for candidate116 checklist repair."""

from __future__ import annotations

import copy
import base64
import importlib
import importlib.metadata
import json
import os
import platform
import pwd
import re
import shutil
import site
import stat
import sys
import sysconfig
import tempfile
import zlib
from pathlib import Path
from typing import Any, Iterable, Mapping

from semantic_review_common import (
    EXPECTED_CASE_COUNT,
    EXPECTED_PARALLELISM,
    REPO_ROOT,
    WORK_ROOT,
    SemanticReviewError,
    add_self_hash,
    file_binding,
    load_json,
    load_yaml_mapping,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    utc_now,
    verify_file_binding,
    verify_self_hash,
)


REPAIR_PRELOCK_SCHEMA = "androidworld_checklist_repair_prelock/v1"
REPAIR_CONFIG_SCHEMA = "androidworld_checklist_repair_config/v1"
REPAIR_SELECTION_SCHEMA = "androidworld_checklist_repair_selection/v2"
REPAIR_ISSUE_SCHEMA = "androidworld_checklist_repair_issue/v2"
EFFECTIVE_MANIFEST_SCHEMA = "androidworld_effective_checklist_wave/v1"
PROMOTION_HANDOFF_SCHEMA = "androidworld_repair_aware_promotion_handoff/v1"
REQUIRED_CASE_SIDECARS = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stdout.log",
    "stderr.log",
)
ISSUE_FIELDS = (
    "schema_version",
    "issue_id",
    "source_issue_id",
    "source_issue_ordinal",
    "severity",
    "source_kind",
    "check",
    "field",
    "description",
    "required_fix",
    "detail",
    "evidence",
    "issue_sha256",
)
DIRECT_REQUIRED_PYTHON_MODULES = (
    ("requests", "requests"),
    ("PyYAML", "yaml"),
    ("jsonschema", "jsonschema"),
)
RUNTIME_INTROSPECTION_DISTRIBUTION = "packaging"
FORBIDDEN_CHILD_PYTHON_ENVIRONMENT = (
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONSAFEPATH",
    "PYTHONUSERBASE",
)
CLOSED_CHILD_PATH = "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
CLOSED_CHILD_ENVIRONMENT_KEYS = frozenset(
    {
        "PATH",
        "HOME",
        "CODEX_HOME",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "TZ",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONNOUSERSITE",
    }
)
CODEX_LOGIN_SUCCESS_LINE = "Logged in using ChatGPT"
CODEX_PATH_ALIAS_WARNING = (
    "WARNING: proceeding, even though we could not create PATH aliases: "
    "Operation not permitted (os error 1)"
)
AUTOMATIC_QC_CHECK_KEYS = frozenset(
    {
        "batch_result",
        "frozen_packet_input",
        "guardrails",
        "identity",
        "llm_provenance",
        "no_absolute_paths",
        "no_hidden_oracle",
        "no_source_as_run_evidence",
        "required_sidecars",
        "schema",
        "sfu_done_gate",
        "support_paths",
        "yaml_json_consistency",
    }
)
REPAIR_CONCURRENCY_CASE_COUNT = 80
REPAIR_LARGE_CASE_THRESHOLD_BYTES = 180000
REPAIR_ORDER_SEMANTICS = {
    "candidate_case_order": "source/prelock audit order for all 116 cases",
    "repair_selection_order": "80 repair cases projected from candidate source order",
    "repair_execution_order": (
        "deterministic frozen batch submission plan: name-sorted regular lane, "
        "then name-sorted oversized lane"
    ),
    "wall_clock_order": (
        "not deterministic under six workers; source order does not control model-call "
        "start/completion and _batch_results.jsonl is as_completed order"
    ),
}
REPAIR_CONCURRENCY_SAMPLE_SCHEMA = "androidworld_checklist_repair_concurrency_sample/v1"
REPAIR_CONCURRENCY_SUMMARY_SCHEMA = "androidworld_checklist_repair_concurrency_audit/v1"
REPAIR_CONCURRENCY_EVIDENCE_SCHEMA = (
    "androidworld_checklist_repair_concurrency_evidence_binding/v1"
)
RUNTIME_SOURCE_SNAPSHOT_SCHEMA = "androidworld_repair_runtime_source_snapshot/v1"
REPAIR_CONCURRENCY_GATE_KEYS = frozenset(
    {
        "foreign_process_preflight_pass",
        "immediate_foreign_preflight_pass",
        "foreign_processes_absent_during_run",
        "monitor_error_free",
        "sample_count_positive",
        "observed_peak_equals_six",
        "at_least_one_six_way_overlap_sample",
        "never_exceeded_six",
        "all_repair_cases_observed",
        "batch_returncode_zero",
        "batch_process_group_postflight_passed",
        "no_cleanup_required",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PRELOCK_FILE_SHA256_PLACEHOLDER = "__PRELOCK_FILE_SHA256__"
PRELOCK_INTERNAL_SHA256_PLACEHOLDER = "__PRELOCK_INTERNAL_SHA256__"
EXACT_TREE_SCHEMA = "androidworld_exact_snapshot_tree/v1"
ISOLATED_BOOTSTRAP_SCHEMA = "androidworld_isolated_snapshot_bootstrap/v1"
ATTEMPT_ROOT_CLAIM_SCHEMA = "androidworld_checklist_repair_attempt_root_claim/v1"
ATTEMPT_LAYOUT_ROLES = ("wave", "evidence", "scratch")


class RepairPipelineError(SemanticReviewError):
    """Raised when a repair/effective-wave invariant is not proven."""


def closed_child_environment() -> dict[str, str]:
    """Build the exact, ambient-free environment admitted to Codex/drafter children.

    The account database, rather than the caller's ``HOME`` variable, identifies
    the current user's home.  Both HOME and CODEX_HOME are required to be real,
    owned directories before their lexical absolute paths are frozen.
    """

    account_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    if not account_home.is_absolute() or account_home.is_symlink() or not account_home.is_dir():
        raise RepairPipelineError(
            f"current account home is not a real absolute directory: {account_home}"
        )
    home_stat = account_home.stat()
    if home_stat.st_uid != os.getuid():
        raise RepairPipelineError(
            f"current account home is not owned by uid {os.getuid()}: {account_home}"
        )
    codex_home = account_home / ".codex"
    if codex_home.is_symlink() or not codex_home.is_dir():
        raise RepairPipelineError(
            f"required Codex login home is not a real directory: {codex_home}"
        )
    if codex_home.stat().st_uid != os.getuid():
        raise RepairPipelineError(
            f"required Codex login home is not owned by uid {os.getuid()}: {codex_home}"
        )
    environment = {
        "PATH": CLOSED_CHILD_PATH,
        "HOME": str(account_home),
        "CODEX_HOME": str(codex_home),
        "TMPDIR": "/private/tmp",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    if set(environment) != CLOSED_CHILD_ENVIRONMENT_KEYS:
        raise RepairPipelineError("closed child environment key set is internally inconsistent")
    return environment


def verify_closed_child_environment(
    environment: Mapping[str, Any], label: str
) -> dict[str, str]:
    """Require exact key-set and value equality with the closed child environment."""

    expected = closed_child_environment()
    if not isinstance(environment, Mapping) or dict(environment) != expected:
        extra = sorted(set(environment) - set(expected)) if isinstance(environment, Mapping) else []
        missing = sorted(set(expected) - set(environment)) if isinstance(environment, Mapping) else []
        raise RepairPipelineError(
            f"{label} is not the exact closed environment: extra={extra}, missing={missing}"
        )
    return expected


def verify_attempt_root_claim(
    claim: Mapping[str, Any],
    *,
    repair_id: str,
    attempt_root: Path,
    expected_layout: Mapping[str, Path],
    label: str,
) -> dict[str, Any]:
    """Revalidate a self-hashed, exclusive attempt namespace claim by inode."""

    if not isinstance(claim, Mapping):
        raise RepairPipelineError(f"{label} is not an object")
    verify_self_hash(claim, "claim_sha256", label)
    expected_fields = {
        "schema_version",
        "repair_id",
        "claimed_at",
        "monotonic_ns",
        "attempt_root",
        "root_identity",
        "layout",
        "layout_identities",
        "layout_sha256",
        "root_created_with_exclusive_mkdir",
        "root_mkdir_mode",
        "all_layout_directories_precreated_before_final_foreign_preflight",
        "all_paths_contained_in_attempt_root",
        "no_symlinks",
        "directory_fds_held_until_final_verification",
        "appworld_v56_runtime_gate",
        "claim_sha256",
    }
    root = Path(os.path.abspath(attempt_root))
    layout = {role: str(Path(os.path.abspath(expected_layout[role]))) for role in ATTEMPT_LAYOUT_ROLES}
    if (
        set(claim) != expected_fields
        or claim.get("schema_version") != ATTEMPT_ROOT_CLAIM_SCHEMA
        or claim.get("repair_id") != repair_id
        or not isinstance(claim.get("claimed_at"), str)
        or not claim.get("claimed_at")
        or not isinstance(claim.get("monotonic_ns"), int)
        or isinstance(claim.get("monotonic_ns"), bool)
        or claim.get("monotonic_ns") <= 0
        or claim.get("attempt_root") != str(root)
        or claim.get("layout") != layout
        or claim.get("layout_sha256") != object_sha256(layout)
        or claim.get("root_created_with_exclusive_mkdir") is not True
        or claim.get("root_mkdir_mode") != "0700"
        or claim.get("all_layout_directories_precreated_before_final_foreign_preflight")
        is not True
        or claim.get("all_paths_contained_in_attempt_root") is not True
        or claim.get("no_symlinks") is not True
        or claim.get("directory_fds_held_until_final_verification") is not True
        or claim.get("appworld_v56_runtime_gate") is not False
    ):
        raise RepairPipelineError(f"{label} contract differs")
    identity = claim.get("root_identity")
    if not isinstance(identity, Mapping) or set(identity) != {
        "st_dev",
        "st_ino",
        "st_uid",
        "st_gid",
        "mode",
        "st_nlink",
    }:
        raise RepairPipelineError(f"{label} root identity is invalid")
    try:
        metadata = root.lstat()
    except OSError as exc:
        raise RepairPipelineError(f"{label} attempt root cannot be lstat'ed: {exc}") from exc
    observed_identity = {
        "st_dev": metadata.st_dev,
        "st_ino": metadata.st_ino,
        "st_uid": metadata.st_uid,
        "st_gid": metadata.st_gid,
        "mode": stat.S_IMODE(metadata.st_mode),
        "st_nlink": metadata.st_nlink,
    }
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or root.is_symlink()
        or observed_identity != dict(identity)
        or observed_identity["mode"] != 0o700
        or observed_identity["st_uid"] != os.getuid()
    ):
        raise RepairPipelineError(f"{label} attempt-root inode/mode changed")
    layout_identities = claim.get("layout_identities")
    if not isinstance(layout_identities, Mapping) or set(layout_identities) != set(
        ATTEMPT_LAYOUT_ROLES
    ):
        raise RepairPipelineError(f"{label} layout identities are invalid")
    for role, raw_path in layout.items():
        path = Path(raw_path)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise RepairPipelineError(f"{label} {role} escapes attempt root") from exc
        try:
            item = path.lstat()
        except OSError as exc:
            raise RepairPipelineError(f"{label} {role} is missing: {exc}") from exc
        if path.is_symlink() or not stat.S_ISDIR(item.st_mode):
            raise RepairPipelineError(f"{label} {role} is not a real directory")
        claimed_layout_identity = layout_identities.get(role)
        if not isinstance(claimed_layout_identity, Mapping) or set(
            claimed_layout_identity
        ) != {"st_dev", "st_ino", "st_uid", "st_gid", "mode", "st_nlink"}:
            raise RepairPipelineError(f"{label} {role} identity is invalid")
        observed_stable = {
            "st_dev": item.st_dev,
            "st_ino": item.st_ino,
            "st_uid": item.st_uid,
            "st_gid": item.st_gid,
            "mode": stat.S_IMODE(item.st_mode),
        }
        claimed_stable = {
            key: claimed_layout_identity[key]
            for key in ("st_dev", "st_ino", "st_uid", "st_gid", "mode")
        }
        if (
            observed_stable != claimed_stable
            or observed_stable["mode"] != 0o700
            or observed_stable["st_uid"] != os.getuid()
            or not isinstance(claimed_layout_identity.get("st_nlink"), int)
            or claimed_layout_identity["st_nlink"] < 1
            or item.st_nlink < claimed_layout_identity["st_nlink"]
        ):
            raise RepairPipelineError(f"{label} {role} inode/mode changed")
    return dict(claim)


def parse_codex_login_status(stdout: str, stderr: str, label: str) -> dict[str, Any]:
    """Accept only the exact login line, optionally preceded by one sandbox warning."""

    lines = [
        line.strip()
        for stream in (stdout, stderr)
        for line in str(stream or "").splitlines()
        if line.strip()
    ]
    if not lines or lines[-1] != CODEX_LOGIN_SUCCESS_LINE:
        raise RepairPipelineError(f"{label} did not end in the exact ChatGPT login status")
    warnings = lines[:-1]
    if warnings not in ([], [CODEX_PATH_ALIAS_WARNING]):
        raise RepairPipelineError(f"{label} emitted unrecognized output before login status: {warnings}")
    warning = warnings[0] if warnings else None
    return {
        "login_status": CODEX_LOGIN_SUCCESS_LINE,
        "path_alias_warning_present": warning is not None,
        "path_alias_warning": warning,
        "path_alias_warning_sha256": object_sha256(warning) if warning is not None else None,
    }


def _distribution_record(distribution_name: str) -> tuple[str, dict[str, Any]]:
    """Bind every installed regular file named by a distribution's RECORD index."""

    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise RepairPipelineError(
            f"required Python distribution is missing: {distribution_name}"
        ) from exc
    canonical_name = str(distribution.metadata.get("Name") or distribution_name)
    record_paths = sorted(distribution.files or (), key=lambda item: str(item))
    if not record_paths:
        raise RepairPipelineError(
            f"required distribution has no RECORD entries: {canonical_name}"
        )
    files: list[dict[str, Any]] = []
    for package_path in record_paths:
        portable = str(package_path).replace(os.sep, "/")
        installed = Path(distribution.locate_file(package_path))
        if not installed.exists() or not installed.is_file():
            raise RepairPipelineError(
                f"RECORD-listed path is missing or non-regular for {canonical_name}: {installed}"
            )
        absolute = Path(os.path.abspath(installed))
        files.append(
            {
                "distribution_path": portable,
                "installed_path": str(absolute),
                "entry_kind": "symlink" if absolute.is_symlink() else "regular_file",
                "symlink_target": os.readlink(absolute) if absolute.is_symlink() else None,
                "size_bytes": absolute.stat().st_size,
                "sha256": sha256_file(absolute),
            }
        )
    record_files = [row for row in files if row["distribution_path"].endswith(".dist-info/RECORD")]
    if len(record_files) != 1:
        raise RepairPipelineError(
            f"distribution {canonical_name} must expose exactly one .dist-info/RECORD file"
        )
    value = {
        "distribution": canonical_name,
        "distribution_version": distribution.version,
        "declared_requirements": sorted(distribution.requires or []),
        "record_entry_count": len(record_paths),
        "record_entries_sha256": object_sha256([str(item).replace(os.sep, "/") for item in record_paths]),
        "distribution_file_count": len(files),
        "distribution_total_bytes": sum(item["size_bytes"] for item in files),
        "distribution_files_sha256": object_sha256(files),
        "record_file": record_files[0],
        "distribution_files": files,
    }
    return canonical_name, value


def _canonical_runtime_tree(
    root: Path,
    *,
    excluded_directory_names: frozenset[str] = frozenset(),
    excluded_suffixes: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Bind a runtime tree without following directory symlinks."""

    root = Path(os.path.abspath(root))
    if not root.is_dir():
        raise RepairPipelineError(f"runtime tree root is missing: {root}")
    rows: list[dict[str, Any]] = []

    def visit(directory: Path, relative_directory: Path) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise RepairPipelineError(f"cannot enumerate runtime tree {directory}: {exc}") from exc
        for entry in entries:
            relative = relative_directory / entry.name
            if entry.name in excluded_directory_names and entry.is_dir(follow_symlinks=False):
                continue
            if relative.suffix.casefold() in excluded_suffixes and entry.is_file(
                follow_symlinks=False
            ):
                continue
            absolute = Path(entry.path)
            metadata = absolute.lstat()
            portable = relative.as_posix()
            if absolute.is_symlink():
                rows.append(
                    {
                        "path": portable,
                        "kind": "symlink",
                        "target": os.readlink(absolute),
                    }
                )
            elif absolute.is_dir():
                rows.append({"path": portable, "kind": "directory"})
                visit(absolute, relative)
            elif absolute.is_file():
                rows.append(
                    {
                        "path": portable,
                        "kind": "regular_file",
                        "size_bytes": metadata.st_size,
                        "sha256": sha256_file(absolute),
                    }
                )
            else:
                raise RepairPipelineError(
                    f"unsupported special file in runtime tree: {absolute}"
                )

    visit(root, Path())
    return {
        "root": str(root),
        "entry_count": len(rows),
        "regular_file_count": sum(row["kind"] == "regular_file" for row in rows),
        "directory_count": sum(row["kind"] == "directory" for row in rows),
        "symlink_count": sum(row["kind"] == "symlink" for row in rows),
        "total_regular_file_bytes": sum(
            int(row.get("size_bytes") or 0) for row in rows if row["kind"] == "regular_file"
        ),
        "tree_sha256": object_sha256(rows),
        "entries": rows,
    }


def canonical_runtime_tree(root: Path) -> dict[str, Any]:
    """Return the complete, non-following runtime-tree byte index for ``root``."""

    return _canonical_runtime_tree(root)


def verify_runtime_source_snapshot_binding(
    binding: Mapping[str, Any],
    label: str,
    *,
    runtime: Mapping[str, Any] | None = None,
    repair_exact_tree: Mapping[str, Any] | None = None,
    runtime_source_exact_tree: Mapping[str, Any] | None = None,
    expected_source_root: Path | None = None,
) -> dict[str, Any]:
    """Verify the captured editable ``repo/src`` replacement and its import isolation.

    The source capture deliberately includes every byte present at capture time,
    including pre-existing ``.pyc``/``.pyo`` files.  The immutable copy is then
    admitted through ``sys.path`` in place of the mutable editable-install path.
    """

    if not isinstance(binding, Mapping):
        raise RepairPipelineError(f"{label} binding is not an object")
    verify_self_hash(binding, "runtime_source_snapshot_sha256", label)
    expected_fields = {
        "schema_version",
        "source_root_absolute_path",
        "content_root_absolute_path",
        "snapshot_root_absolute_path",
        "source_entry_count",
        "source_regular_file_count",
        "source_directory_count",
        "source_total_regular_file_bytes",
        "source_pre_tree_sha256",
        "source_post_tree_sha256",
        "snapshot_tree_sha256",
        "source_content_id_sha256",
        "source_pre_tree",
        "source_post_tree",
        "snapshot_tree",
        "bytecode_file_count",
        "bytecode_files_sha256",
        "bytecode_policy",
        "copy_policy",
        "source_endpoint_equality_required",
        "source_endpoint_equality_observed",
        "snapshot_all_bytes_equal_source",
        "snapshot_symlink_count",
        "live_source_excluded_from_runtime_sys_path",
        "sys_path_substitution",
        "live_editable_pth_policy",
        "outer_and_nested_preimport_verification_required",
        "staged_copy_promoted_atomically",
        "staging_policy",
        "post_freeze_live_source_drift_nonbinding",
        "dont_write_bytecode_required",
        "threat_model_limit",
        "runtime_source_snapshot_sha256",
    }
    if set(binding) != expected_fields:
        raise RepairPipelineError(
            f"{label} fields differ: {sorted(set(binding) ^ expected_fields)}"
        )
    if binding.get("schema_version") != RUNTIME_SOURCE_SNAPSHOT_SCHEMA:
        raise RepairPipelineError(f"{label} schema is invalid")
    source_root = Path(str(binding.get("source_root_absolute_path") or ""))
    content_root = Path(str(binding.get("content_root_absolute_path") or ""))
    snapshot_root = Path(str(binding.get("snapshot_root_absolute_path") or ""))
    # Never stat or resolve the mutable live source after capture.  Its canonical
    # lexical location is a historical claim; only the frozen copy remains a gate.
    required_source_root = Path(
        os.path.abspath(
            expected_source_root
            if expected_source_root is not None
            else REPO_ROOT / "src"
        )
    )
    if (
        not source_root.is_absolute()
        or source_root != required_source_root
        or not content_root.is_absolute()
        or not snapshot_root.is_absolute()
        or snapshot_root != content_root / "src"
        or content_root.name != binding.get("source_content_id_sha256")
        or snapshot_root.is_symlink()
        or not snapshot_root.is_dir()
    ):
        raise RepairPipelineError(f"{label} source/snapshot roots are invalid")
    observed = _canonical_runtime_tree(snapshot_root)
    bytecode_files = [
        {
            "path": row["path"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
        }
        for row in observed["entries"]
        if row["kind"] == "regular_file"
        and Path(str(row["path"])).suffix.casefold() in {".pyc", ".pyo"}
    ]
    expected_source_tree = {**observed, "root": str(source_root)}
    if (
        observed["symlink_count"] != 0
        or binding.get("snapshot_symlink_count") != 0
        or binding.get("source_entry_count") != observed["entry_count"]
        or binding.get("source_regular_file_count") != observed["regular_file_count"]
        or binding.get("source_directory_count") != observed["directory_count"]
        or binding.get("source_total_regular_file_bytes")
        != observed["total_regular_file_bytes"]
        or binding.get("source_pre_tree_sha256") != observed["tree_sha256"]
        or binding.get("source_post_tree_sha256") != observed["tree_sha256"]
        or binding.get("snapshot_tree_sha256") != observed["tree_sha256"]
        or binding.get("source_content_id_sha256")
        != object_sha256(observed["entries"])
        or binding.get("source_pre_tree") != expected_source_tree
        or binding.get("source_post_tree") != expected_source_tree
        or binding.get("snapshot_tree") != observed
        or binding.get("bytecode_file_count") != len(bytecode_files)
        or binding.get("bytecode_files_sha256") != object_sha256(bytecode_files)
        or binding.get("source_endpoint_equality_required") is not True
        or binding.get("source_endpoint_equality_observed") is not True
        or binding.get("snapshot_all_bytes_equal_source") is not True
        or binding.get("live_source_excluded_from_runtime_sys_path") is not True
        or binding.get("sys_path_substitution")
        != {
            "captured_live_editable_path": str(source_root),
            "frozen_snapshot_path": str(snapshot_root),
            "required_replacement_count": 1,
            "live_path_allowed_after_substitution": False,
        }
        or binding.get("live_editable_pth_policy")
        != (
            "never execute site or editable-install .pth files in generation; bind their "
            "capture-time effect explicitly by replacing only live repo/src with runtime_src"
        )
        or binding.get("outer_and_nested_preimport_verification_required") is not True
        or binding.get("staged_copy_promoted_atomically") is not True
        or binding.get("staging_policy")
        != (
            "copy and compare under a hidden sibling; write a create-once manifest; atomically "
            "rename to the canonical-entry SHA-256 content address"
        )
        or binding.get("post_freeze_live_source_drift_nonbinding") is not True
        or binding.get("dont_write_bytecode_required") is not True
        or binding.get("bytecode_policy")
        != (
            "copy and bind every pre-existing .pyc/.pyo byte; create no new bytecode; "
            "reject every post-freeze namespace or byte change"
        )
        or binding.get("copy_policy")
        != (
            "pre-index live repo/src, copy every directory and regular file with copy2, "
            "then require source post-index and snapshot index to equal the pre-index"
        )
    ):
        raise RepairPipelineError(f"{label} tree/capture policy differs")
    if runtime is not None:
        expected_sys_path = list(runtime.get("expected_runner_sys_path") or [])
        capture_sys_path = list(runtime.get("observed_capture_sys_path") or [])
        snapshot_text = str(snapshot_root)
        source_text = str(source_root)
        extra_entries = list(runtime.get("extra_sys_path_entries") or [])
        matching_extras = [
            item
            for item in extra_entries
            if isinstance(item, Mapping) and item.get("path") == snapshot_text
        ]
        if (
            expected_sys_path.count(snapshot_text) != 1
            or capture_sys_path.count(snapshot_text) != 1
            or source_text in expected_sys_path
            or source_text in capture_sys_path
            or len(matching_extras) != 1
            or matching_extras[0].get("kind") != "directory_tree"
            or matching_extras[0].get("tree") != observed
        ):
            raise RepairPipelineError(f"{label} is not the sole frozen editable source path")
    if repair_exact_tree is not None:
        repair_root = Path(
            str(repair_exact_tree.get("root_absolute_path") or "")
        )
        if content_root.parent != repair_root / "runtime_source":
            raise RepairPipelineError(f"{label} is outside the repair exact snapshot")
    if runtime_source_exact_tree is not None:
        if content_root != Path(
            str(runtime_source_exact_tree.get("root_absolute_path") or "")
        ):
            raise RepairPipelineError(f"{label} differs from its exact-tree root")
        manifest_descriptor = runtime_source_exact_tree.get("manifest") or {}
        manifest_path = Path(str(manifest_descriptor.get("absolute_path") or ""))
        manifest_payload = load_json(manifest_path, f"{label} manifest")
        verify_self_hash(
            manifest_payload,
            "snapshot_manifest_sha256",
            f"{label} manifest",
        )
        expected_manifest_files = [
            {
                "path": f"src/{row['path']}",
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
            }
            for row in observed["entries"]
            if row["kind"] == "regular_file"
        ]
        if (
            set(manifest_payload)
            != {
                "schema_version",
                "repair_id",
                "source_content_id_sha256",
                "runtime_source_snapshot",
                "files",
                "file_count",
                "files_sha256",
                "snapshot_manifest_sha256",
            }
            or manifest_payload.get("schema_version")
            != "androidworld_repair_runtime_source_snapshot_manifest/v1"
            or not safe_id(str(manifest_payload.get("repair_id") or ""))
            or manifest_payload.get("runtime_source_snapshot") != dict(binding)
            or manifest_payload.get("source_content_id_sha256")
            != binding.get("source_content_id_sha256")
            or manifest_payload.get("files") != expected_manifest_files
            or manifest_payload.get("file_count") != len(expected_manifest_files)
            or manifest_payload.get("files_sha256")
            != object_sha256(expected_manifest_files)
        ):
            raise RepairPipelineError(f"{label} differs from its create-once manifest")
    return observed


def verify_immediate_foreign_preflight_evidence(
    record: Mapping[str, Any],
    *,
    audit: Mapping[str, Any],
    early_foreign_preflight: Mapping[str, Any],
    deterministic_generation_preflight: Mapping[str, Any],
    attempt_claim: Mapping[str, Any],
    label: str,
    require_zero: bool = True,
) -> dict[str, Any]:
    """Verify the exact foreign-process observation captured beside batch Popen."""

    if not isinstance(record, Mapping):
        raise RepairPipelineError(f"{label} is not an object")
    verify_self_hash(record, "immediate_preflight_sha256", label)
    verify_self_hash(
        early_foreign_preflight,
        "preflight_sha256",
        f"{label} early preflight",
    )
    verify_self_hash(
        deterministic_generation_preflight,
        "generation_preflight_sha256",
        f"{label} deterministic preflight",
    )
    verify_self_hash(attempt_claim, "claim_sha256", f"{label} attempt claim")
    expected_fields = {
        "schema_version",
        "phase",
        "captured_at",
        "monotonic_ns",
        "ps_binary",
        "ps_command",
        "patterns",
        "excluded_runner_pid",
        "excluded_runner_ancestor_pids",
        "foreign_processes",
        "foreign_process_count",
        "status",
        "early_foreign_preflight_sha256",
        "deterministic_generation_preflight_sha256",
        "attempt_root_claim_sha256",
        "popen_must_not_occur_if_nonzero",
        "binding_policy",
        "immediate_preflight_sha256",
    }
    ancestors = record.get("excluded_runner_ancestor_pids")
    runner_pid = record.get("excluded_runner_pid")
    foreign_processes = record.get("foreign_processes")
    early_ancestors = early_foreign_preflight.get("excluded_runner_ancestor_pids")
    early_runner_pid = early_foreign_preflight.get("excluded_runner_pid")
    early_monotonic_ns = early_foreign_preflight.get("monotonic_ns")
    deterministic_monotonic_ns = deterministic_generation_preflight.get(
        "monotonic_ns"
    )
    if (
        set(record) != expected_fields
        or record.get("schema_version")
        != "androidworld_checklist_repair_immediate_foreign_preflight/v1"
        or record.get("phase")
        != "after_attempt_root_claim_inside_signal_block_before_batch_popen"
        or not isinstance(record.get("captured_at"), str)
        or not record["captured_at"]
        or not isinstance(record.get("monotonic_ns"), int)
        or isinstance(record.get("monotonic_ns"), bool)
        or record["monotonic_ns"] <= 0
        or not isinstance(early_monotonic_ns, int)
        or isinstance(early_monotonic_ns, bool)
        or early_monotonic_ns <= 0
        or not isinstance(deterministic_monotonic_ns, int)
        or isinstance(deterministic_monotonic_ns, bool)
        or deterministic_monotonic_ns < early_monotonic_ns
        or record["monotonic_ns"] < deterministic_monotonic_ns
        or record.get("ps_binary") != audit.get("ps_binary")
        or record.get("ps_command") != audit.get("ps_command")
        or record.get("patterns") != audit.get("foreign_process_patterns")
        or not isinstance(runner_pid, int)
        or isinstance(runner_pid, bool)
        or runner_pid <= 0
        or not isinstance(ancestors, list)
        or any(
            not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0
            for pid in (ancestors or [])
        )
        or ancestors != sorted(set(ancestors or []))
        or runner_pid in (ancestors or [])
        or runner_pid != early_runner_pid
        or ancestors != early_ancestors
        or not isinstance(foreign_processes, list)
        or any(
            not isinstance(item, Mapping)
            or set(item)
            != {
                "pid",
                "ppid",
                "pgid",
                "matched_patterns",
                "command_sha256",
            }
            or any(
                not isinstance(item.get(field), int)
                or isinstance(item.get(field), bool)
                or item[field] <= 0
                for field in ("pid", "ppid", "pgid")
            )
            or not isinstance(item.get("matched_patterns"), list)
            or not item.get("matched_patterns")
            or item.get("matched_patterns")
            != sorted(set(item.get("matched_patterns") or []))
            or any(
                not isinstance(pattern, str)
                or pattern not in (audit.get("foreign_process_patterns") or [])
                for pattern in (item.get("matched_patterns") or [])
            )
            or not SHA256_RE.fullmatch(str(item.get("command_sha256") or ""))
            for item in (foreign_processes or [])
        )
        or record.get("foreign_process_count") != len(foreign_processes or [])
        or record.get("status") != ("pass" if not foreign_processes else "fail")
        or (require_zero and foreign_processes != [])
        or record.get("early_foreign_preflight_sha256")
        != early_foreign_preflight.get("preflight_sha256")
        or record.get("deterministic_generation_preflight_sha256")
        != deterministic_generation_preflight.get("generation_preflight_sha256")
        or record.get("popen_must_not_occur_if_nonzero") is not True
        or record.get("attempt_root_claim_sha256")
        != attempt_claim.get("claim_sha256")
        or record.get("binding_policy")
        != (
            "after the exclusive attempt-root claim, layout creation, and every deterministic "
            "tree/runtime recheck while wrapper signals are blocked, require a fresh /bin/ps "
            "observation with zero foreign drafting processes; batch Popen is the immediately "
            "following state-changing operation"
        )
    ):
        raise RepairPipelineError(f"{label} exact zero-foreign evidence is invalid")
    return dict(record)


def exact_snapshot_tree_descriptor(
    root: Path,
    *,
    label: str,
    manifest_path: Path,
    manifest_self_hash_field: str,
) -> dict[str, Any]:
    """Describe the *entire* non-symlink snapshot namespace.

    A file index is not an exact-tree gate: an attacker could add an unlisted
    ``json.py``, ``__pycache__/x.pyc``, package directory, or symlink and Python
    could execute it while every listed file still matches.  This descriptor
    binds every relative directory and regular file, every file byte hash, and
    the snapshot manifest's own bytes/self-hash.  Symlinks and special files are
    forbidden rather than followed.
    """

    raw_root = Path(os.path.abspath(root))
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise RepairPipelineError(f"{label} root is missing or a symlink: {raw_root}")
    root_path = raw_root.resolve(strict=True)
    tree = _canonical_runtime_tree(root_path)
    if tree["symlink_count"]:
        symlinks = [row["path"] for row in tree["entries"] if row["kind"] == "symlink"]
        raise RepairPipelineError(f"{label} contains forbidden symlinks: {symlinks}")

    raw_manifest = Path(os.path.abspath(manifest_path))
    if raw_manifest.is_symlink() or not raw_manifest.is_file():
        raise RepairPipelineError(f"{label} manifest is missing or a symlink: {raw_manifest}")
    manifest = raw_manifest.resolve(strict=True)
    try:
        manifest_relative = manifest.relative_to(root_path).as_posix()
    except ValueError as exc:
        raise RepairPipelineError(f"{label} manifest is outside the exact tree") from exc
    manifest_payload = load_json(manifest, f"{label} manifest")
    verify_self_hash(
        manifest_payload,
        manifest_self_hash_field,
        f"{label} manifest",
    )
    manifest_binding = file_binding(manifest)
    payload = {
        "schema_version": EXACT_TREE_SCHEMA,
        "label": label,
        "root_path": repo_relative(root_path),
        "root_absolute_path": str(root_path),
        "entry_count": tree["entry_count"],
        "regular_file_count": tree["regular_file_count"],
        "directory_count": tree["directory_count"],
        "total_regular_file_bytes": tree["total_regular_file_bytes"],
        "entries_sha256": tree["tree_sha256"],
        "entries": tree["entries"],
        "manifest": {
            "relative_path": manifest_relative,
            "absolute_path": str(manifest),
            "binding": manifest_binding,
            "self_hash_field": manifest_self_hash_field,
            "self_hash_value": manifest_payload[manifest_self_hash_field],
        },
        "namespace_policy": (
            "exact relative directory+regular-file set; every regular file byte hash bound; "
            "symlinks and special files forbidden"
        ),
        "threat_model_limit": (
            "endpoint exact-tree checks reject persistent drift but cannot prevent a malicious "
            "writer from modifying and restoring bytes during a verification-to-import gap"
        ),
    }
    return add_self_hash(payload, "descriptor_sha256")


def verify_exact_snapshot_tree_descriptor(
    expected: Mapping[str, Any], label: str
) -> dict[str, Any]:
    """Re-enumerate an exact snapshot tree and require descriptor equality."""

    if not isinstance(expected, Mapping):
        raise RepairPipelineError(f"{label} exact-tree descriptor is not an object")
    verify_self_hash(expected, "descriptor_sha256", f"{label} exact-tree descriptor")
    if expected.get("schema_version") != EXACT_TREE_SCHEMA:
        raise RepairPipelineError(f"{label} exact-tree schema is invalid")
    manifest = expected.get("manifest")
    if not isinstance(manifest, Mapping):
        raise RepairPipelineError(f"{label} exact-tree manifest binding is missing")
    observed = exact_snapshot_tree_descriptor(
        Path(str(expected.get("root_absolute_path") or "")),
        label=str(expected.get("label") or ""),
        manifest_path=Path(str(manifest.get("absolute_path") or "")),
        manifest_self_hash_field=str(manifest.get("self_hash_field") or ""),
    )
    if observed != dict(expected):
        changed = [
            key
            for key in sorted(set(observed) | set(expected))
            if observed.get(key) != expected.get(key)
        ]
        raise RepairPipelineError(f"{label} exact-tree descriptor changed at fields: {changed}")
    return observed


_ISOLATED_BOOTSTRAP_SOURCE = r'''# stdlib-only trust bootstrap; invoked exclusively by: python -I -S -c <encoded payload>
import sys
if not sys.dont_write_bytecode:
    raise SystemExit("ISOLATED_BOOTSTRAP_ERROR: bytecode writes were not disabled before bootstrap imports")
import hashlib
import json
import os
import stat

def fail(message):
    raise SystemExit("ISOLATED_BOOTSTRAP_ERROR: " + message)

def sha_file(path):
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        fail("cannot hash %s: %s" % (path, exc))
    return digest.hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def object_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def load_json(path, label):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError) as exc:
        fail("cannot load %s: %s" % (label, exc))
    if not isinstance(value, dict):
        fail(label + " is not an object")
    return value

def verify_self_hash(value, field, label):
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if not isinstance(claimed, str) or len(claimed) != 64 or claimed != object_sha(core):
        fail(label + " self hash mismatch")

def resolve_binding(binding, repo_root, label):
    if not isinstance(binding, dict):
        fail(label + " binding is not an object")
    raw = str(binding.get("path") or "")
    path = raw if os.path.isabs(raw) else os.path.join(repo_root, raw)
    path = os.path.abspath(path)
    if os.path.commonpath((repo_root, path)) != repo_root:
        fail(label + " escapes repository")
    if os.path.islink(path) or not os.path.isfile(path):
        fail(label + " is missing, non-regular, or a symlink")
    if os.path.getsize(path) != binding.get("size_bytes") or sha_file(path) != binding.get("sha256"):
        fail(label + " byte binding mismatch")
    return path

def enumerate_tree(root, excluded_names=()):
    root = os.path.abspath(root)
    if os.path.islink(root) or not os.path.isdir(root):
        fail("exact-tree root missing or symlink: " + root)
    rows = []
    def visit(directory, relative):
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            fail("cannot enumerate %s: %s" % (directory, exc))
        for entry in entries:
            rel = entry.name if not relative else relative + "/" + entry.name
            if entry.name in excluded_names and entry.is_dir(follow_symlinks=False):
                continue
            path = entry.path
            try:
                mode = os.lstat(path).st_mode
            except OSError as exc:
                fail("cannot stat %s: %s" % (path, exc))
            if stat.S_ISLNK(mode):
                rows.append({"path": rel, "kind": "symlink", "target": os.readlink(path)})
            elif stat.S_ISDIR(mode):
                rows.append({"path": rel, "kind": "directory"})
                visit(path, rel)
            elif stat.S_ISREG(mode):
                rows.append({"path": rel, "kind": "regular_file", "size_bytes": os.lstat(path).st_size, "sha256": sha_file(path)})
            else:
                fail("special file in exact tree: " + path)
    visit(root, "")
    return rows

def verify_exact_tree(descriptor, expected_hash, label):
    if not isinstance(descriptor, dict):
        fail(label + " descriptor missing")
    verify_self_hash(descriptor, "descriptor_sha256", label + " descriptor")
    if descriptor.get("schema_version") != "androidworld_exact_snapshot_tree/v1":
        fail(label + " descriptor schema mismatch")
    if descriptor.get("descriptor_sha256") != expected_hash:
        fail(label + " descriptor trust-anchor mismatch")
    rows = enumerate_tree(str(descriptor.get("root_absolute_path") or ""))
    if any(row.get("kind") == "symlink" for row in rows):
        fail(label + " contains forbidden symlink")
    expected = descriptor.get("entries")
    if rows != expected:
        fail(label + " exact file/directory namespace mismatch")
    regular = [row for row in rows if row["kind"] == "regular_file"]
    directories = [row for row in rows if row["kind"] == "directory"]
    if (descriptor.get("entry_count") != len(rows)
            or descriptor.get("regular_file_count") != len(regular)
            or descriptor.get("directory_count") != len(directories)
            or descriptor.get("total_regular_file_bytes") != sum(row["size_bytes"] for row in regular)
            or descriptor.get("entries_sha256") != object_sha(rows)):
        fail(label + " exact-tree aggregate mismatch")
    manifest = descriptor.get("manifest")
    if not isinstance(manifest, dict):
        fail(label + " manifest descriptor missing")
    manifest_path = str(manifest.get("absolute_path") or "")
    root = str(descriptor.get("root_absolute_path") or "")
    if os.path.commonpath((os.path.abspath(root), os.path.abspath(manifest_path))) != os.path.abspath(root):
        fail(label + " manifest escapes exact tree")
    binding = manifest.get("binding")
    if (not isinstance(binding, dict) or os.path.islink(manifest_path)
            or not os.path.isfile(manifest_path)
            or os.path.getsize(manifest_path) != binding.get("size_bytes")
            or sha_file(manifest_path) != binding.get("sha256")):
        fail(label + " manifest byte binding mismatch")
    manifest_value = load_json(manifest_path, label + " manifest")
    field = str(manifest.get("self_hash_field") or "")
    verify_self_hash(manifest_value, field, label + " manifest")
    if manifest_value.get(field) != manifest.get("self_hash_value"):
        fail(label + " manifest internal hash differs")

def verify_runtime_tree(expected, excluded_names=()):
    if not isinstance(expected, dict):
        fail("runtime tree descriptor missing")
    rows = enumerate_tree(str(expected.get("root") or ""), excluded_names)
    observed = {
        "root": os.path.abspath(str(expected.get("root") or "")),
        "entry_count": len(rows),
        "regular_file_count": sum(row["kind"] == "regular_file" for row in rows),
        "directory_count": sum(row["kind"] == "directory" for row in rows),
        "symlink_count": sum(row["kind"] == "symlink" for row in rows),
        "total_regular_file_bytes": sum(row.get("size_bytes", 0) for row in rows if row["kind"] == "regular_file"),
        "tree_sha256": object_sha(rows),
        "entries": rows,
    }
    if observed != expected:
        fail("runtime tree changed: " + str(expected.get("root")))

def verify_runtime(runtime):
    if not isinstance(runtime, dict):
        fail("python runtime binding missing")
    required_environment = runtime.get("required_environment")
    expected_environment_keys = {
        "PATH", "HOME", "CODEX_HOME", "TMPDIR", "LANG", "LC_ALL", "TZ",
        "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE",
    }
    if (not isinstance(required_environment, dict)
            or set(required_environment) != expected_environment_keys
            or required_environment.get("PATH") != "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            or required_environment.get("TMPDIR") != "/private/tmp"
            or required_environment.get("LANG") != "C"
            or required_environment.get("LC_ALL") != "C"
            or required_environment.get("TZ") != "UTC"
            or required_environment.get("PYTHONDONTWRITEBYTECODE") != "1"
            or required_environment.get("PYTHONNOUSERSITE") != "1"
            or runtime.get("semantic_environment_sha256") != object_sha(required_environment)):
        fail("closed child environment binding mismatch")
    home = str(required_environment.get("HOME") or "")
    codex_home = str(required_environment.get("CODEX_HOME") or "")
    if (not os.path.isabs(home) or os.path.islink(home) or not os.path.isdir(home)
            or codex_home != os.path.join(home, ".codex")
            or os.path.islink(codex_home) or not os.path.isdir(codex_home)):
        fail("closed child HOME/CODEX_HOME binding mismatch")
    # The parent passes exactly this dictionary to execve.  macOS may synthesize
    # __CF_USER_TEXT_ENCODING during process startup; it is not inherited
    # ambient state.  Every prelocked key/value must nevertheless remain exact.
    if any(os.environ.get(key) != value for key, value in required_environment.items()):
        fail("closed child environment values changed before bootstrap")
    flags = runtime.get("required_execution_flags")
    observed_flags = {
        "isolated": int(sys.flags.isolated),
        "no_site": int(sys.flags.no_site),
        "ignore_environment": int(sys.flags.ignore_environment),
        "safe_path": bool(getattr(sys.flags, "safe_path", False)),
    }
    if observed_flags != flags or observed_flags != {"isolated": 1, "no_site": 1, "ignore_environment": 1, "safe_path": True}:
        fail("interpreter was not started with exact -I -S isolation")
    if (runtime.get("required_execution_state") != {"dont_write_bytecode": True}
            or (runtime.get("python_startup_security") or {}).get("required_execution_state") != runtime.get("required_execution_state")
            or not sys.dont_write_bytecode):
        fail("bytecode-write execution state differs")
    invocation = os.path.abspath(sys.executable)
    if invocation != runtime.get("invocation_path"):
        fail("Python invocation path changed")
    resolved = os.path.realpath(invocation)
    if resolved != runtime.get("resolved_binary_path") or sha_file(resolved) != runtime.get("resolved_binary_sha256"):
        fail("Python executable bytes changed")
    site_trees = runtime.get("site_packages_trees")
    if not isinstance(site_trees, dict) or object_sha(site_trees) != runtime.get("site_packages_trees_sha256"):
        fail("site-packages tree index mismatch")
    for tree in site_trees.values():
        verify_runtime_tree(tree)
    library_trees = runtime.get("stdlib_platstdlib_trees")
    if not isinstance(library_trees, dict) or object_sha(library_trees) != runtime.get("stdlib_platstdlib_trees_sha256"):
        fail("stdlib tree index mismatch")
    for item in library_trees.values():
        if not isinstance(item, dict):
            fail("stdlib tree item invalid")
        verify_runtime_tree(item.get("tree"), ("site-packages", "dist-packages"))
    extras = runtime.get("extra_sys_path_entries")
    if not isinstance(extras, list) or object_sha(extras) != runtime.get("extra_sys_path_entries_sha256"):
        fail("extra sys.path index mismatch")
    for item in extras:
        path = str(item.get("path") or "")
        kind = item.get("kind")
        if kind == "covered_by_runtime_tree":
            if not os.path.exists(path):
                fail("covered sys.path entry disappeared: " + path)
        elif kind == "regular_file":
            if os.path.islink(path) or not os.path.isfile(path) or os.path.getsize(path) != item.get("size_bytes") or sha_file(path) != item.get("sha256"):
                fail("extra sys.path file changed: " + path)
        elif kind == "directory_tree":
            verify_runtime_tree(item.get("tree"))
        elif kind == "expected_absent":
            if os.path.lexists(path):
                fail("expected-absent sys.path entry appeared: " + path)
        else:
            fail("unknown extra sys.path entry kind")
    codex_path = str(runtime.get("codex_invocation_path") or "")
    if os.path.islink(codex_path):
        codex_resolved = os.path.realpath(codex_path)
    else:
        codex_resolved = codex_path
    if not os.path.isfile(codex_path) or sha_file(codex_resolved) != runtime.get("codex_invocation_sha256"):
        fail("Codex invocation bytes changed")

def bound_target(prelock, repo_root, mode, requested):
    if mode == "outer":
        binding = (prelock.get("repair_tool_bindings") or {}).get("repair_runner")
    elif mode == "batch":
        binding = (prelock.get("original_v3_tool_bindings") or {}).get("batch_runner")
    elif mode == "script":
        tools = prelock.get("original_v3_tool_bindings") or {}
        allowed = [tools.get("drafter"), tools.get("validator")]
        paths = [resolve_binding(item, repo_root, "nested tool") for item in allowed if isinstance(item, dict)]
        requested_abs = os.path.abspath(requested)
        if requested_abs not in paths:
            fail("unrecognized nested Python script target")
        return requested_abs
    else:
        fail("unknown bootstrap mode")
    path = resolve_binding(binding, repo_root, mode + " target")
    if os.path.abspath(requested) != path:
        fail(mode + " target differs from frozen binding")
    return path

def bootstrap_command(runtime, payload, prelock_path, prelock_file_hash, prelock_internal_hash, repair_tree_hash, source_tree_hash, runtime_source_tree_hash, mode, target, args):
    return [runtime["invocation_path"], "-I", "-S", "-c", payload, prelock_path, prelock_file_hash, prelock_internal_hash, repair_tree_hash, source_tree_hash, runtime_source_tree_hash, mode, target, "--"] + list(args)

def main():
    if len(sys.argv) < 10 or sys.argv[9] != "--":
        fail("invalid bootstrap argv")
    prelock_path, expected_prelock_file_hash, expected_prelock_internal_hash, repair_tree_hash, source_tree_hash, runtime_source_tree_hash, mode, requested_target = sys.argv[1:9]
    target_args = sys.argv[10:]
    if len(expected_prelock_file_hash) != 64 or sha_file(prelock_path) != expected_prelock_file_hash:
        fail("repair prelock external hash mismatch")
    prelock = load_json(prelock_path, "repair prelock")
    verify_self_hash(prelock, "prelock_sha256", "repair prelock")
    if (len(expected_prelock_internal_hash) != 64
            or prelock.get("prelock_sha256") != expected_prelock_internal_hash):
        fail("repair prelock internal/external hash mismatch")
    repo_root = os.path.abspath(str(prelock.get("repository_root_absolute") or ""))
    if not os.path.isdir(repo_root):
        fail("bound repository root missing")
    config_path = resolve_binding(prelock.get("repair_config"), repo_root, "repair config")
    config = load_json(config_path, "repair config")
    verify_self_hash(config, "config_sha256", "repair config")
    if config.get("config_sha256") != (prelock.get("repair_config") or {}).get("config_sha256"):
        fail("repair config internal hash differs from prelock")
    trees = prelock.get("snapshot_exact_trees")
    if (not isinstance(trees, dict) or trees != config.get("snapshot_exact_trees")
            or set(trees) != {"repair", "source_v3", "runtime_source"}):
        fail("exact-tree descriptors differ across config/prelock")
    repair_tree = trees.get("repair")
    source_tree = trees.get("source_v3")
    runtime_source_tree = trees.get("runtime_source")
    verify_exact_tree(repair_tree, repair_tree_hash, "repair snapshot")
    verify_exact_tree(source_tree, source_tree_hash, "source v3 snapshot")
    verify_exact_tree(runtime_source_tree, runtime_source_tree_hash, "runtime source snapshot")
    runtime_source = prelock.get("runtime_source_snapshot")
    if not isinstance(runtime_source, dict) or runtime_source != config.get("runtime_source_snapshot"):
        fail("runtime source snapshot differs across config/prelock")
    verify_self_hash(runtime_source, "runtime_source_snapshot_sha256", "runtime source snapshot")
    repair_root = os.path.abspath(str((repair_tree or {}).get("root_absolute_path") or ""))
    runtime_source_content_root = os.path.abspath(str(runtime_source.get("content_root_absolute_path") or ""))
    runtime_source_root = os.path.abspath(str(runtime_source.get("snapshot_root_absolute_path") or ""))
    live_source_root = os.path.abspath(str(runtime_source.get("source_root_absolute_path") or ""))
    runtime_source_content_id = str(runtime_source.get("source_content_id_sha256") or "")
    runtime_source_manifest = load_json(str(((runtime_source_tree or {}).get("manifest") or {}).get("absolute_path") or ""), "runtime source snapshot manifest")
    source_pre_tree = runtime_source.get("source_pre_tree")
    source_post_tree = runtime_source.get("source_post_tree")
    copied_source_tree = runtime_source.get("snapshot_tree")
    normalized_copied_tree = dict(copied_source_tree) if isinstance(copied_source_tree, dict) else {}
    normalized_copied_tree["root"] = live_source_root
    expected_runtime_source_files = [
        {"path": "src/" + str(row.get("path") or ""), "size_bytes": row.get("size_bytes"), "sha256": row.get("sha256")}
        for row in list((copied_source_tree or {}).get("entries") or [])
        if isinstance(row, dict) and row.get("kind") == "regular_file"
    ] if isinstance(copied_source_tree, dict) else []
    if (runtime_source.get("schema_version") != "androidworld_repair_runtime_source_snapshot/v1"
            or runtime_source_content_root != os.path.abspath(str((runtime_source_tree or {}).get("root_absolute_path") or ""))
            or os.path.dirname(runtime_source_content_root) != os.path.join(repair_root, "runtime_source")
            or runtime_source_root != os.path.join(runtime_source_content_root, "src")
            or live_source_root != os.path.join(repo_root, "src")
            or len(runtime_source_content_id) != 64
            or os.path.basename(runtime_source_content_root) != runtime_source_content_id
            or runtime_source.get("source_pre_tree_sha256") != runtime_source_content_id
            or runtime_source.get("source_post_tree_sha256") != runtime_source_content_id
            or runtime_source.get("snapshot_tree_sha256") != runtime_source_content_id
            or not isinstance(source_pre_tree, dict)
            or source_pre_tree != source_post_tree
            or normalized_copied_tree != source_pre_tree
            or runtime_source_manifest.get("source_content_id_sha256") != runtime_source_content_id
            or runtime_source_manifest.get("runtime_source_snapshot") != runtime_source
            or set(runtime_source_manifest) != {"schema_version", "repair_id", "source_content_id_sha256", "runtime_source_snapshot", "files", "file_count", "files_sha256", "snapshot_manifest_sha256"}
            or runtime_source_manifest.get("schema_version") != "androidworld_repair_runtime_source_snapshot_manifest/v1"
            or runtime_source_manifest.get("repair_id") != prelock.get("repair_id")
            or runtime_source_manifest.get("files") != expected_runtime_source_files
            or runtime_source_manifest.get("file_count") != len(expected_runtime_source_files)
            or runtime_source_manifest.get("files_sha256") != object_sha(expected_runtime_source_files)
            or runtime_source.get("source_endpoint_equality_observed") is not True
            or runtime_source.get("snapshot_all_bytes_equal_source") is not True
            or runtime_source.get("snapshot_symlink_count") != 0
            or runtime_source.get("live_source_excluded_from_runtime_sys_path") is not True
            or runtime_source.get("outer_and_nested_preimport_verification_required") is not True
            or runtime_source.get("staged_copy_promoted_atomically") is not True
            or runtime_source.get("post_freeze_live_source_drift_nonbinding") is not True
            or runtime_source.get("dont_write_bytecode_required") is not True):
        fail("runtime source snapshot policy/path is invalid")
    bootstrap = prelock.get("isolated_bootstrap")
    if not isinstance(bootstrap, dict) or bootstrap != config.get("isolated_bootstrap"):
        fail("bootstrap binding differs across config/prelock")
    bootstrap_payload = bootstrap.get("payload")
    if (not isinstance(bootstrap_payload, str) or any(character.isspace() for character in bootstrap_payload)
            or bootstrap.get("payload_sha256") != object_sha(bootstrap_payload)):
        fail("bootstrap payload binding mismatch")
    runtime = (prelock.get("runner_execution") or {}).get("python_runtime")
    if runtime != config.get("python_runtime"):
        fail("python runtime differs across config/prelock")
    verify_runtime(runtime)
    expected_tail = list(runtime.get("expected_runner_sys_path") or [])[1:]
    capture_tail = list(runtime.get("observed_capture_sys_path") or [])[1:]
    matching_extra = [item for item in list(runtime.get("extra_sys_path_entries") or [])
                      if isinstance(item, dict) and item.get("path") == runtime_source_root]
    if (expected_tail.count(runtime_source_root) != 1
            or capture_tail.count(runtime_source_root) != 1
            or live_source_root in expected_tail
            or live_source_root in capture_tail
            or len(matching_extra) != 1
            or matching_extra[0].get("kind") != "directory_tree"
            or (matching_extra[0].get("tree") or {}).get("tree_sha256") != runtime_source.get("snapshot_tree_sha256")):
        fail("runtime sys.path is not isolated to the frozen source snapshot")
    target = bound_target(prelock, repo_root, mode, requested_target)

    required_environment = dict(runtime.get("required_environment") or {})
    if object_sha(required_environment) != runtime.get("semantic_environment_sha256"):
        fail("closed child environment hash changed before target admission")
    # macOS may synthesize __CF_USER_TEXT_ENCODING during interpreter startup.
    # Remove it (and every other non-contract key) before any frozen Python tool
    # or descendant subprocess can observe the environment.
    os.environ.clear()
    os.environ.update(required_environment)
    if os.environ != required_environment:
        fail("failed to normalize exact closed child environment")

    # Only now may site-packages and either snapshot script directory enter
    # sys.path.  We never import site, execute .pth files, or import snapshot
    # modules before all three exact-tree gates above have passed.
    sys.prefix = runtime["sys_prefix"]
    sys.exec_prefix = runtime["sys_exec_prefix"]
    sys.base_prefix = runtime["sys_base_prefix"]
    sys.base_exec_prefix = runtime["sys_base_exec_prefix"]
    sys.path[:] = [os.path.dirname(target)] + list(runtime["expected_runner_sys_path"])[1:]
    sys.argv[:] = [target] + target_args
    sys._androidworld_isolated_bootstrap_admission = expected_prelock_internal_hash
    sys._androidworld_isolated_bootstrap_prelock_file_sha256 = expected_prelock_file_hash
    sys._androidworld_closed_child_environment_sha256 = object_sha(required_environment)

    import runpy
    if mode == "batch":
        import subprocess
        real_run = subprocess.run
        tools = prelock.get("original_v3_tool_bindings") or {}
        drafter = resolve_binding(tools.get("drafter"), repo_root, "nested drafter")
        validator = resolve_binding(tools.get("validator"), repo_root, "nested validator")
        allowed = {drafter, validator}
        python = runtime["invocation_path"]
        def guarded_run(*popenargs, **kwargs):
            if not popenargs:
                fail("subprocess.run called without argv")
            command = popenargs[0]
            if isinstance(command, (list, tuple)) and command:
                first = os.path.abspath(str(command[0]))
                if first == python:
                    if len(command) < 2 or os.path.abspath(str(command[1])) not in allowed:
                        fail("unrecognized Python child invocation")
                    nested_target = os.path.abspath(str(command[1]))
                    rewritten = bootstrap_command(runtime, bootstrap_payload, prelock_path, expected_prelock_file_hash, expected_prelock_internal_hash, repair_tree_hash, source_tree_hash, runtime_source_tree_hash, "script", nested_target, list(command[2:]))
                    popenargs = (rewritten,) + popenargs[1:]
            elif isinstance(command, str) and python in command:
                fail("string-form Python child invocation is forbidden")
            supplied_environment = kwargs.get("env")
            if supplied_environment is not None and dict(supplied_environment) != required_environment:
                fail("batch child supplied a non-contract environment")
            kwargs["env"] = dict(required_environment)
            return real_run(*popenargs, **kwargs)
        subprocess.run = guarded_run
    elif mode == "script":
        import subprocess
        real_run = subprocess.run
        def guarded_script_run(*popenargs, **kwargs):
            supplied_environment = kwargs.get("env")
            if supplied_environment is not None and dict(supplied_environment) != required_environment:
                fail("nested tool supplied a non-contract environment")
            kwargs["env"] = dict(required_environment)
            return real_run(*popenargs, **kwargs)
        subprocess.run = guarded_script_run
    runpy.run_path(target, run_name="__main__")

if __name__ == "__main__":
    main()
'''


def isolated_bootstrap_payload() -> str:
    """Return a whitespace-free ``-c`` payload containing the stdlib bootstrap."""

    compressed = zlib.compress(_ISOLATED_BOOTSTRAP_SOURCE.encode("utf-8"), level=9)
    encoded = base64.b64encode(compressed).decode("ascii")
    payload = (
        "setattr(__import__('sys'),'dont_write_bytecode',True);"
        "exec(__import__('zlib').decompress("
        f"__import__('base64').b64decode('{encoded}')))"
    )
    if any(character.isspace() for character in payload):
        raise RepairPipelineError("isolated bootstrap -c payload contains whitespace")
    return payload


def isolated_bootstrap_record() -> dict[str, Any]:
    payload = isolated_bootstrap_payload()
    return {
        "schema_version": ISOLATED_BOOTSTRAP_SCHEMA,
        "launch_flags": ["-I", "-S", "-c"],
        "dont_write_bytecode_set_before_decoder_imports": True,
        "payload": payload,
        "payload_sha256": object_sha256(payload),
        "preimport_policy": (
            "CPython -I -S starts without cwd/script/site paths; stdlib-only inline bootstrap "
            "verifies runtime, all three exact snapshot trees, and the copied repo/src binding before "
            "constructing frozen sys.path without the live editable source path"
        ),
        "nested_python_policy": (
            "batch subprocess.run rewrites only the exact frozen drafter/validator scripts "
            "through the same -I -S bootstrap and rejects every other Python child target"
        ),
        "threat_model_limit": (
            "endpoint hashes cannot prevent a malicious writer from modify+restore activity "
            "inside a verification-to-import gap"
        ),
    }


def isolated_bootstrap_command(
    *,
    runtime: Mapping[str, Any],
    prelock_path: Path,
    prelock_file_sha256: str,
    prelock_internal_sha256: str,
    repair_tree_sha256: str,
    source_tree_sha256: str,
    runtime_source_tree_sha256: str,
    mode: str,
    target: Path,
    target_args: Iterable[str],
) -> list[str]:
    if mode not in {"outer", "batch", "script"}:
        raise RepairPipelineError(f"invalid isolated bootstrap mode: {mode}")
    if (
        prelock_file_sha256 != PRELOCK_FILE_SHA256_PLACEHOLDER
        and not SHA256_RE.fullmatch(prelock_file_sha256)
    ):
        raise RepairPipelineError("isolated bootstrap physical prelock hash is invalid")
    if (
        prelock_internal_sha256 != PRELOCK_INTERNAL_SHA256_PLACEHOLDER
        and not SHA256_RE.fullmatch(prelock_internal_sha256)
    ):
        raise RepairPipelineError("isolated bootstrap internal prelock hash is invalid")
    if (
        not SHA256_RE.fullmatch(repair_tree_sha256)
        or not SHA256_RE.fullmatch(source_tree_sha256)
        or not SHA256_RE.fullmatch(runtime_source_tree_sha256)
    ):
        raise RepairPipelineError("isolated bootstrap exact-tree hash is invalid")
    command = [
        str(runtime["invocation_path"]),
        "-I",
        "-S",
        "-c",
        isolated_bootstrap_payload(),
        str(Path(os.path.abspath(prelock_path))),
        prelock_file_sha256,
        prelock_internal_sha256,
        repair_tree_sha256,
        source_tree_sha256,
        runtime_source_tree_sha256,
        mode,
        str(Path(os.path.abspath(target))),
        "--",
        *[str(item) for item in target_args],
    ]
    if any(not item or any(character.isspace() for character in item) for item in command):
        raise RepairPipelineError("isolated bootstrap argv contains empty/whitespace arguments")
    return command


def expand_prelock_sha256(
    command: Iterable[str], *, file_sha256: str, internal_sha256: str
) -> list[str]:
    if not SHA256_RE.fullmatch(file_sha256) or not SHA256_RE.fullmatch(internal_sha256):
        raise RepairPipelineError("cannot expand invalid repair prelock hashes")
    result = [
        file_sha256
        if item == PRELOCK_FILE_SHA256_PLACEHOLDER
        else internal_sha256
        if item == PRELOCK_INTERNAL_SHA256_PLACEHOLDER
        else item
        for item in command
    ]
    if (
        PRELOCK_FILE_SHA256_PLACEHOLDER in result
        or PRELOCK_INTERNAL_SHA256_PLACEHOLDER in result
    ):
        raise RepairPipelineError("repair prelock hash placeholder expansion failed")
    return result


def python_runtime_binding(
    *,
    expected_runner_script_directory: Path | None = None,
    codex_invocation_path: Path | None = None,
    execution_requires_isolated_bootstrap: bool = False,
) -> dict[str, Any]:
    """Capture the exact Python invocation without collapsing a venv symlink.

    ``sys.executable`` is intentionally made absolute but never resolved for
    invocation.  Resolving a uv/venv Python symlink before execution can change
    ``sys.prefix`` and therefore the import environment.  The resolved binary is
    bound separately for executable-byte integrity.
    """

    invocation_path = Path(os.path.abspath(sys.executable))
    if not invocation_path.is_file():
        raise RepairPipelineError(f"current Python invocation path is not a file: {invocation_path}")
    resolved_binary = invocation_path.resolve(strict=True)
    dependencies: dict[str, Any] = {}
    importlib.invalidate_caches()
    try:
        from packaging.markers import default_environment
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
    except Exception as exc:
        raise RepairPipelineError(
            f"required Python dependency-introspection package cannot be imported: packaging: {exc}"
        ) from exc

    direct_modules: dict[str, dict[str, Any]] = {}
    for distribution, module_name in DIRECT_REQUIRED_PYTHON_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            raise RepairPipelineError(
                f"required Python module cannot be imported: {module_name}: {exc}"
            ) from exc
        module_file_raw = getattr(module, "__file__", None)
        if not isinstance(module_file_raw, str) or not module_file_raw:
            raise RepairPipelineError(f"required module has no file: {module_name}")
        module_file = Path(os.path.abspath(module_file_raw))
        if not module_file.is_file():
            raise RepairPipelineError(f"required module file is missing: {module_file}")
        direct_modules[distribution] = {
            "distribution": distribution,
            "import_module": module_name,
            "module_file_path": str(module_file),
            "module_file_sha256": sha256_file(module_file),
            "module_file_resolved_path": str(module_file.resolve(strict=True)),
        }

    # Freeze the complete active dependency closure, not only the three direct
    # imports.  Markers are evaluated for this exact interpreter with no extras.
    environment = default_environment()
    environment["extra"] = ""
    queued = [name for name, _ in DIRECT_REQUIRED_PYTHON_MODULES]
    queued.append(RUNTIME_INTROSPECTION_DISTRIBUTION)
    seen: set[str] = set()
    edges: list[dict[str, Any]] = []
    while queued:
        requested_name = queued.pop(0)
        canonical_requested = canonicalize_name(requested_name)
        if canonical_requested in seen:
            continue
        installed_name, binding = _distribution_record(requested_name)
        installed_canonical = canonicalize_name(installed_name)
        if installed_canonical != canonical_requested:
            # Alias spelling is fine, but the installed canonical identity is
            # the only identity used for closure de-duplication.
            canonical_requested = installed_canonical
        if canonical_requested in seen:
            continue
        seen.add(canonical_requested)
        binding["canonical_distribution_name"] = canonical_requested
        requirements: list[dict[str, Any]] = []
        for raw_requirement in binding["declared_requirements"]:
            try:
                requirement = Requirement(raw_requirement)
            except Exception as exc:
                raise RepairPipelineError(
                    f"cannot parse dependency requirement for {installed_name}: {raw_requirement}: {exc}"
                ) from exc
            marker_applies = requirement.marker is None or requirement.marker.evaluate(environment)
            dependency_name = canonicalize_name(requirement.name)
            row = {
                "raw": raw_requirement,
                "name": requirement.name,
                "canonical_name": dependency_name,
                "marker": str(requirement.marker) if requirement.marker is not None else None,
                "marker_applies": marker_applies,
                "specifier": str(requirement.specifier),
                "url": requirement.url,
            }
            requirements.append(row)
            if marker_applies:
                try:
                    installed_dependency = importlib.metadata.distribution(requirement.name)
                except importlib.metadata.PackageNotFoundError as exc:
                    raise RepairPipelineError(
                        f"active dependency is missing: {installed_name} -> {requirement.name}"
                    ) from exc
                if requirement.specifier and not requirement.specifier.contains(
                    installed_dependency.version, prereleases=True
                ):
                    raise RepairPipelineError(
                        f"active dependency version mismatch: {installed_name} requires "
                        f"{requirement}, observed {installed_dependency.version}"
                    )
                queued.append(requirement.name)
                edges.append(
                    {
                        "from": canonical_requested,
                        "to": dependency_name,
                        "requirement": raw_requirement,
                        "observed_version": installed_dependency.version,
                    }
                )
        binding["evaluated_requirements"] = requirements
        binding["evaluated_requirements_sha256"] = object_sha256(requirements)
        dependencies[canonical_requested] = binding

    dependencies = {name: dependencies[name] for name in sorted(dependencies)}
    for distribution, module_name in DIRECT_REQUIRED_PYTHON_MODULES:
        canonical_name = canonicalize_name(distribution)
        if canonical_name not in dependencies:
            raise RepairPipelineError(f"direct distribution escaped dependency closure: {distribution}")
        direct_modules[distribution]["canonical_distribution_name"] = canonical_name
        direct_modules[distribution]["distribution_version"] = dependencies[canonical_name][
            "distribution_version"
        ]
    site_roots = sorted(
        {
            str(Path(os.path.abspath(path)))
            for path in (sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))
            if path
        }
    )
    # Python may import an existing bytecode-only module.  PYTHONDONTWRITEBYTECODE
    # prevents new cache writes; it does not make existing .pyc/.pyo files
    # unreadable.  Therefore every runtime tree below includes all cache
    # directories and bytecode files.
    site_packages = {
        root: _canonical_runtime_tree(Path(root))
        for root in site_roots
    }
    library_roots: dict[str, dict[str, Any]] = {}
    for role in ("stdlib", "platstdlib"):
        raw_root = sysconfig.get_path(role)
        if not raw_root:
            raise RepairPipelineError(f"sysconfig path is missing: {role}")
        absolute_root = str(Path(os.path.abspath(raw_root)))
        if absolute_root in library_roots:
            library_roots[absolute_root]["roles"].append(role)
            continue
        tree = _canonical_runtime_tree(
            Path(absolute_root),
            # site/dist-packages are bound independently above.  Cache entries
            # belonging to the stdlib itself remain included here.
            excluded_directory_names=frozenset({"site-packages", "dist-packages"}),
        )
        library_roots[absolute_root] = {"roles": [role], "tree": tree}

    observed_sys_path = [str(item) for item in sys.path]
    expected_sys_path = list(observed_sys_path)
    if expected_runner_script_directory is not None:
        if not expected_sys_path:
            raise RepairPipelineError("Python sys.path unexpectedly has no script entry")
        expected_sys_path[0] = str(Path(os.path.abspath(expected_runner_script_directory)))
    covered_roots = [Path(path) for path in list(site_packages) + list(library_roots)]
    extra_sys_path_entries: list[dict[str, Any]] = []
    for index, raw_entry in enumerate(expected_sys_path[1:], 1):
        if not raw_entry:
            raise RepairPipelineError(f"unexpected empty non-script sys.path entry at index {index}")
        entry = Path(os.path.abspath(raw_entry))
        covered_by = next(
            (
                str(root)
                for root in covered_roots
                if entry == root or root in entry.parents
            ),
            None,
        )
        if covered_by is not None:
            extra_sys_path_entries.append(
                {"index": index, "path": str(entry), "kind": "covered_by_runtime_tree", "root": covered_by}
            )
        elif entry.is_file():
            extra_sys_path_entries.append(
                {
                    "index": index,
                    "path": str(entry),
                    "kind": "regular_file",
                    "size_bytes": entry.stat().st_size,
                    "sha256": sha256_file(entry),
                }
            )
        elif entry.is_dir():
            extra_sys_path_entries.append(
                {
                    "index": index,
                    "path": str(entry),
                    "kind": "directory_tree",
                    "tree": _canonical_runtime_tree(entry),
                }
            )
        else:
            # CPython commonly includes a versioned stdlib zip candidate even
            # when no zip is installed.  Its required absence is itself bound.
            extra_sys_path_entries.append(
                {"index": index, "path": str(entry), "kind": "expected_absent"}
            )

    if codex_invocation_path is None:
        raw_codex = shutil.which("codex")
        if not raw_codex:
            raise RepairPipelineError("codex is absent while freezing the Python runtime")
        codex_invocation_path = Path(os.path.abspath(raw_codex))
    else:
        codex_invocation_path = Path(os.path.abspath(codex_invocation_path))
    if not codex_invocation_path.is_file():
        raise RepairPipelineError(
            f"Codex invocation path is missing while freezing runtime: {codex_invocation_path}"
        )
    required_environment = closed_child_environment()
    if shutil.which("codex", path=required_environment["PATH"]) != str(
        codex_invocation_path
    ):
        raise RepairPipelineError(
            "closed child PATH does not resolve the frozen Codex invocation"
        )
    capture_flags = {
        "isolated": int(sys.flags.isolated),
        "no_site": int(sys.flags.no_site),
        "ignore_environment": int(sys.flags.ignore_environment),
        "safe_path": bool(getattr(sys.flags, "safe_path", False)),
    }
    required_execution_flags = (
        {"isolated": 1, "no_site": 1, "ignore_environment": 1, "safe_path": True}
        if execution_requires_isolated_bootstrap
        else capture_flags
    )
    startup_names = {"sitecustomize.py", "usercustomize.py", "_virtualenv.py"}
    startup_surface: list[dict[str, Any]] = []
    for root, tree in site_packages.items():
        for row in tree["entries"]:
            path = str(row["path"])
            name = Path(path).name
            if path.endswith(".pth") or name in startup_names:
                startup_surface.append({"site_root": root, **row})
    startup_surface.sort(key=lambda row: (row["site_root"], row["path"]))
    startup_security = {
        "capture_flags": capture_flags,
        "required_execution_flags": required_execution_flags,
        "required_execution_state": {"dont_write_bytecode": True},
        "execution_requires_isolated_bootstrap": execution_requires_isolated_bootstrap,
        "python_safe_path_environment_required_absent": True,
        "python_safe_path_environment_observed_at_capture": os.environ.get("PYTHONSAFEPATH"),
        "site_enable_user_site_at_capture": site.ENABLE_USER_SITE,
        "required_execution_site_enable_user_site": (
            None if execution_requires_isolated_bootstrap else site.ENABLE_USER_SITE
        ),
        "startup_surface": startup_surface,
        "startup_surface_sha256": object_sha256(startup_surface),
        "startup_surface_policy": (
            "python -I -S admits no cwd/script/site path; the inline stdlib bootstrap "
            "verifies all site .pth/startup-hook bytes and all three exact snapshot namespaces "
            "before constructing the frozen sys.path without executing site or .pth files"
        ),
        "security_claim_limit": (
            "endpoint byte/tree equality detects persistent drift but cannot prevent a "
            "malicious writer from modify+restore activity during a verification-to-import gap"
        ),
    }
    return {
        "invocation_path": str(invocation_path),
        "invocation_path_is_symlink": invocation_path.is_symlink(),
        "invocation_path_symlink_target": os.readlink(invocation_path)
        if invocation_path.is_symlink()
        else None,
        "resolved_binary_path": str(resolved_binary),
        "resolved_binary_sha256": sha256_file(resolved_binary),
        "sys_prefix": sys.prefix,
        "sys_base_prefix": sys.base_prefix,
        "sys_exec_prefix": sys.exec_prefix,
        "sys_base_exec_prefix": sys.base_exec_prefix,
        "version": sys.version,
        "version_info": list(sys.version_info[:5]),
        "implementation": platform.python_implementation(),
        "python_build": list(platform.python_build()),
        "python_compiler": platform.python_compiler(),
        "codex_invocation_path": str(codex_invocation_path),
        "codex_invocation_sha256": sha256_file(codex_invocation_path.resolve(strict=True)),
        "expected_runner_sys_path": expected_sys_path,
        "observed_capture_sys_path": observed_sys_path,
        "expected_runner_script_directory": expected_sys_path[0],
        "required_execution_flags": required_execution_flags,
        "required_execution_state": {"dont_write_bytecode": True},
        "sys_path_tail_sha256": object_sha256(expected_sys_path[1:]),
        "extra_sys_path_entries": extra_sys_path_entries,
        "extra_sys_path_entries_sha256": object_sha256(extra_sys_path_entries),
        "python_startup_security": startup_security,
        "site_packages_trees": site_packages,
        "site_packages_trees_sha256": object_sha256(site_packages),
        "stdlib_platstdlib_trees": library_roots,
        "stdlib_platstdlib_trees_sha256": object_sha256(library_roots),
        "direct_required_modules": direct_modules,
        "direct_required_distributions": [name for name, _ in DIRECT_REQUIRED_PYTHON_MODULES],
        "dependency_introspection_distribution": RUNTIME_INTROSPECTION_DISTRIBUTION,
        "dependency_marker_environment": environment,
        "dependency_edges": sorted(
            edges, key=lambda row: (row["from"], row["to"], row["requirement"])
        ),
        "dependency_closure_count": len(dependencies),
        "dependency_closure_names": list(dependencies),
        "dependency_closure_sha256": object_sha256(dependencies),
        "dependencies": dependencies,
        "forbidden_child_python_environment": list(FORBIDDEN_CHILD_PYTHON_ENVIRONMENT),
        "required_environment": required_environment,
        "semantic_environment_sha256": object_sha256(required_environment),
    }


def verify_python_runtime_binding(expected: Mapping[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(expected, Mapping):
        raise RepairPipelineError(f"{label} is not an object")
    expected_script_directory = Path(
        str(expected.get("expected_runner_script_directory") or "")
    )
    if not sys.path:
        raise RepairPipelineError(f"{label} current sys.path has no script entry")
    observed_script_directory = Path(os.path.abspath(sys.path[0]))
    if observed_script_directory != expected_script_directory:
        raise RepairPipelineError(
            f"{label} runner script directory changed: "
            f"{observed_script_directory} != {expected_script_directory}"
        )
    security = expected.get("python_startup_security")
    if not isinstance(security, Mapping):
        raise RepairPipelineError(f"{label} startup-security binding is missing")
    required_flags = security.get("required_execution_flags")
    current_flags = {
        "isolated": int(sys.flags.isolated),
        "no_site": int(sys.flags.no_site),
        "ignore_environment": int(sys.flags.ignore_environment),
        "safe_path": bool(getattr(sys.flags, "safe_path", False)),
    }
    if current_flags != required_flags or expected.get("required_execution_flags") != required_flags:
        raise RepairPipelineError(
            f"{label} interpreter isolation flags differ: {current_flags} != {required_flags}"
        )
    if (
        expected.get("required_execution_state") != {"dont_write_bytecode": True}
        or security.get("required_execution_state")
        != expected.get("required_execution_state")
        or not sys.dont_write_bytecode
    ):
        raise RepairPipelineError(f"{label} bytecode-write state differs")
    if site.ENABLE_USER_SITE != security.get("required_execution_site_enable_user_site"):
        raise RepairPipelineError(f"{label} user-site execution state differs")
    observed = python_runtime_binding(
        expected_runner_script_directory=expected_script_directory,
        codex_invocation_path=Path(str(expected.get("codex_invocation_path") or "")),
        execution_requires_isolated_bootstrap=bool(
            security.get("execution_requires_isolated_bootstrap")
        ),
    )
    # Capture location is intentionally different in the live prepare script and
    # frozen runner.  The runner path itself is frozen above; only the expected
    # runner sys.path is a gate.
    observed["observed_capture_sys_path"] = expected.get("observed_capture_sys_path")
    observed_security = observed.get("python_startup_security") or {}
    observed_security["capture_flags"] = security.get("capture_flags")
    observed_security["site_enable_user_site_at_capture"] = security.get(
        "site_enable_user_site_at_capture"
    )
    observed_security["python_safe_path_environment_observed_at_capture"] = security.get(
        "python_safe_path_environment_observed_at_capture"
    )
    if observed != dict(expected):
        changed = [
            key
            for key in sorted(set(observed) | set(expected))
            if observed.get(key) != expected.get(key)
        ]
        raise RepairPipelineError(f"{label} changed at fields: {changed}")
    return observed


def safe_id(value: str) -> bool:
    return bool(value) and bool(re.fullmatch(r"[A-Za-z0-9_.-]+", value))


def verify_binding_tree(value: Any, label: str, *, inside_candidate: bool = True) -> None:
    if isinstance(value, Mapping) and {"path", "sha256", "size_bytes"}.issubset(value):
        verify_file_binding(value, label, inside_candidate=inside_candidate)
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            verify_binding_tree(nested, f"{label}.{key}", inside_candidate=inside_candidate)
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            verify_binding_tree(nested, f"{label}[{index}]", inside_candidate=inside_candidate)
        return
    raise RepairPipelineError(f"{label} is not a file-binding tree")


def packet_rows(prelock: Mapping[str, Any]) -> list[dict[str, Any]]:
    for key in ("packet_inputs", "case_packet_inputs", "compact_packet_inputs"):
        rows = prelock.get(key)
        if isinstance(rows, list):
            result: list[dict[str, Any]] = []
            for raw in rows:
                if not isinstance(raw, Mapping):
                    raise RepairPipelineError(f"{key} contains a non-object")
                row = dict(raw)
                row.setdefault("path", row.get("packet_path") or row.get("case_packet_path"))
                result.append(row)
            return result
    raise RepairPipelineError("draft prelock has no packet input list")


def load_source_prelock(path: Path) -> dict[str, Any]:
    path = path.resolve()
    try:
        path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("source draft prelock must be inside candidate116") from exc
    value = load_json(path, "source draft prelock")
    verify_self_hash(value, "prelock_sha256", "source draft prelock")
    if value.get("generation_id") != "wave_003":
        raise RepairPipelineError("repair source generation must be wave_003")
    if value.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("source prelock is not exactly 116 cases")
    order = list(value.get("case_order") or [])
    if len(order) != EXPECTED_CASE_COUNT or len(set(order)) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("source prelock case order is invalid")
    if value.get("case_order_sha256") != object_sha256(order):
        raise RepairPipelineError("source prelock case-order hash fails")
    rows = packet_rows(value)
    if len(rows) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("source prelock does not bind 116 packets")
    return value


def verify_source_context_freeze(source_prelock: Mapping[str, Any]) -> dict[str, Any]:
    binding = source_prelock.get("old_packet_source_freeze")
    if not isinstance(binding, Mapping):
        raise RepairPipelineError("source prelock has no old_packet_source_freeze binding")
    freeze_path = resolve_repo_path(binding.get("path"), inside_candidate=True)
    if not freeze_path.is_file() or sha256_file(freeze_path) != binding.get("file_sha256"):
        raise RepairPipelineError("old packet/source freeze file binding changed")
    freeze = load_json(freeze_path, "old packet/source freeze")
    verify_self_hash(freeze, "freeze_sha256", "old packet/source freeze")
    if freeze.get("freeze_sha256") != binding.get("freeze_sha256"):
        raise RepairPipelineError("old packet/source freeze internal hash differs from source prelock")
    agents_hash = freeze.get("agents_config_hash")
    agents_binding = (freeze.get("artifact_bindings") or {}).get("agents_config")
    if not isinstance(agents_binding, Mapping) or agents_binding.get("sha256") != agents_hash:
        raise RepairPipelineError("source-context agents config binding/hash is invalid")
    agents_path = resolve_repo_path(agents_binding.get("path"), inside_candidate=True)
    if not agents_path.is_file() or sha256_file(agents_path) != agents_hash:
        raise RepairPipelineError("source-context agents config bytes changed")
    drafter_config = load_json(agents_path, "packet/source-context contract drafter config")
    llm = freeze.get("llm")
    if not isinstance(llm, Mapping) or not isinstance(llm.get("llm_roles"), Mapping):
        raise RepairPipelineError("old packet/source freeze llm_roles are missing")
    if object_sha256(llm["llm_roles"]) != llm.get("llm_roles_sha256"):
        raise RepairPipelineError("old packet/source freeze llm_roles hash fails")
    if (
        object_sha256(drafter_config)
        != llm.get("contract_drafter_config_canonical_payload_sha256")
    ):
        raise RepairPipelineError("source-context drafter config canonical payload hash fails")
    contract_drafter = drafter_config.get("contract_drafter")
    frozen_role = llm["llm_roles"].get("contract_drafter")
    if not isinstance(contract_drafter, Mapping) or not isinstance(frozen_role, Mapping):
        raise RepairPipelineError("source-context contract_drafter role is missing")
    if object_sha256(frozen_role) != llm.get("contract_drafter_role_sha256"):
        raise RepairPipelineError("source-context contract_drafter role hash fails")
    if any(contract_drafter.get(key) != value for key, value in frozen_role.items()):
        raise RepairPipelineError("source-context frozen llm role differs from drafter config")
    current_agents_path = REPO_ROOT / "configs" / "agents.yaml"
    if not current_agents_path.is_file():
        raise RepairPipelineError("current future-runtime configs/agents.yaml is missing")
    return {
        "freeze": file_binding(freeze_path) | {"freeze_sha256": freeze["freeze_sha256"]},
        "packet_source_context_contract_drafter_config": file_binding(agents_path)
        | {"agents_config_hash": agents_hash},
        "packet_source_context_contract_drafter_config_canonical_payload_sha256": llm[
            "contract_drafter_config_canonical_payload_sha256"
        ],
        "packet_source_context_llm_roles": dict(llm["llm_roles"]),
        "packet_source_context_llm_roles_sha256": llm["llm_roles_sha256"],
        "packet_source_context_contract_drafter_role_sha256": llm[
            "contract_drafter_role_sha256"
        ],
        "current_future_runtime_agents_config": file_binding(current_agents_path),
        "authority": {
            "packet_source_context_only": True,
            "old_agents_config_controls_this_repair_drafter": False,
            "old_llm_roles_control_this_repair_drafter": False,
            "current_configs_agents_yaml_controls_this_repair_drafter": False,
            "new_repair_config_is_drafter_authority": True,
        },
    }


def source_wave(prelock: Mapping[str, Any]) -> Path:
    raw = (prelock.get("canonical_output_gate") or {}).get("raw_wave")
    path = resolve_repo_path(raw, inside_candidate=True)
    expected = WORK_ROOT / "draft_generation" / "waves" / "wave_003"
    if path != expected.resolve():
        raise RepairPipelineError("source prelock raw wave is not wave_003")
    return path


def tool_binding(prelock: Mapping[str, Any], *names: str) -> tuple[str, dict[str, Any], Path]:
    tools = prelock.get("tool_bindings")
    if not isinstance(tools, Mapping):
        raise RepairPipelineError("prelock has no tool_bindings")
    normalized = {
        re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_"): (str(key), value)
        for key, value in tools.items()
    }
    for requested in names:
        key = re.sub(r"[^a-z0-9]+", "_", requested.casefold()).strip("_")
        if key in normalized:
            original, binding = normalized[key]
            if not isinstance(binding, Mapping):
                raise RepairPipelineError(f"tool binding {original} is not an object")
            path = verify_file_binding(binding, f"tool {original}", inside_candidate=True)
            return original, dict(binding), path
    raise RepairPipelineError(f"missing tool binding alternatives {names}")


def case_file_bindings(case_dir: Path) -> dict[str, Any]:
    bindings = {name: file_binding(case_dir / name) for name in REQUIRED_CASE_SIDECARS}
    return bindings


def tree_record(root: Path) -> dict[str, Any]:
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
    ]
    return {
        "path": repo_relative(root),
        "file_count": len(files),
        "tree_sha256": object_sha256(files),
        "files": files,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RepairPipelineError(f"cannot read JSONL {path}: {exc}") from exc
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RepairPipelineError(f"invalid JSONL {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise RepairPipelineError(f"JSONL row {path}:{number} is not an object")
        rows.append(value)
    return rows


def _context_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _evidence_strings(value: Any) -> list[str]:
    if value is None:
        return []
    rows = value if isinstance(value, list) else [value]
    return [_context_string(item) for item in rows]


def validate_normalized_issue(value: Mapping[str, Any], case_id: str, index: int) -> dict[str, Any]:
    if set(value) != set(ISSUE_FIELDS):
        raise RepairPipelineError(
            f"{case_id} issue {index} fields differ from fixed {REPAIR_ISSUE_SCHEMA} schema"
        )
    if value.get("schema_version") != REPAIR_ISSUE_SCHEMA:
        raise RepairPipelineError(f"{case_id} issue {index} schema_version is invalid")
    if value.get("source_issue_ordinal") != index:
        raise RepairPipelineError(f"{case_id} issue {index} ordinal differs")
    if value.get("severity") not in {"error", "warning"}:
        raise RepairPipelineError(f"{case_id} issue {index} severity is invalid")
    for field in (
        "issue_id",
        "source_issue_id",
        "source_kind",
        "check",
        "field",
        "description",
        "required_fix",
        "detail",
    ):
        if not isinstance(value.get(field), str):
            raise RepairPipelineError(f"{case_id} issue {index} {field} must be a string")
    for field in ("issue_id", "source_issue_id", "source_kind", "check", "description", "required_fix"):
        if not value.get(field):
            raise RepairPipelineError(f"{case_id} issue {index} {field} must be non-empty")
    if not isinstance(value.get("evidence"), list) or any(
        not isinstance(item, str) for item in value.get("evidence")
    ):
        raise RepairPipelineError(f"{case_id} issue {index} evidence must be a string list")
    verify_self_hash(value, "issue_sha256", f"{case_id} issue {index}")
    return dict(value)


def normalized_issue(raw: Mapping[str, Any], case_id: str, index: int) -> dict[str, Any]:
    if raw.get("schema_version") == REPAIR_ISSUE_SCHEMA:
        return validate_normalized_issue(raw, case_id, index)
    description = str(raw.get("description") or raw.get("message") or "").strip()
    check = str(raw.get("check") or raw.get("field") or "semantic").strip()
    source_kind = str(raw.get("source_kind") or "manual_audit").strip()
    source_issue_id = str(
        raw.get("source_issue_id") or raw.get("code") or raw.get("issue_id") or f"issue_{index:03d}"
    ).strip()
    field = str(raw.get("field") or "").strip()
    detail = _context_string(raw.get("detail"))
    evidence = _evidence_strings(raw.get("evidence"))
    fingerprint_core = {
        "source_issue_id": source_issue_id,
        "source_issue_ordinal": index,
        "source_kind": source_kind,
        "check": check,
        "field": field,
        "description": description,
        "required_fix": str(
            raw.get("required_fix")
            or raw.get("fix")
            or (f"Resolve the bound {check} failure: {description}" if description else "")
        ).strip(),
        "detail": detail,
        "evidence": evidence,
    }
    safe_source = re.sub(r"[^a-z0-9_]+", "_", source_issue_id.casefold()).strip("_") or "issue"
    safe_kind = re.sub(r"[^a-z0-9_]+", "_", source_kind.casefold()).strip("_") or "source"
    result = {
        "schema_version": REPAIR_ISSUE_SCHEMA,
        "issue_id": (
            f"{safe_source}__{safe_kind}__{index:03d}__{object_sha256(fingerprint_core)[:12]}"
        ),
        "source_issue_id": source_issue_id,
        "source_issue_ordinal": index,
        "severity": str(raw.get("severity") or "error").strip().casefold(),
        "source_kind": source_kind,
        "check": check,
        "field": field,
        "description": description,
        "required_fix": fingerprint_core["required_fix"],
        "detail": detail,
        "evidence": evidence,
    }
    if result["severity"] not in {"error", "warning"}:
        raise RepairPipelineError(f"{case_id} issue {result['issue_id']} has invalid severity")
    for field_name in ("source_issue_id", "source_kind", "check", "description", "required_fix"):
        if not result[field_name]:
            raise RepairPipelineError(f"{case_id} issue {index} {field_name} is incomplete")
    result = add_self_hash(result, "issue_sha256")
    return validate_normalized_issue(result, case_id, index)


def require_unique_issue_ids(issues: Iterable[Mapping[str, Any]], case_id: str) -> None:
    issue_ids = [str(item.get("issue_id") or "") for item in issues]
    if any(not issue_id for issue_id in issue_ids) or len(issue_ids) != len(set(issue_ids)):
        raise RepairPipelineError(f"{case_id} has duplicate or empty normalized issue_id values")


def load_audit_selection(
    path: Path,
    *,
    case_order: list[str],
    automatic_qc_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selection = load_json(path.resolve(), "repair selection")
    if selection.get("schema_version") != REPAIR_SELECTION_SCHEMA:
        raise RepairPipelineError("repair selection schema_version is invalid")
    verify_self_hash(selection, "selection_sha256", "repair selection")
    if selection.get("source_generation_id") != "wave_003" or selection.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("repair selection source/count is invalid")
    rows = list(selection.get("cases") or [])
    if len(rows) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("repair selection must contain exactly 116 rows")
    normalized_rows: list[dict[str, Any]] = []
    for rank, (case_id, raw) in enumerate(zip(case_order, rows, strict=True)):
        if not isinstance(raw, Mapping):
            raise RepairPipelineError(f"repair selection row {rank} is not an object")
        if raw.get("selection_rank") != rank or raw.get("case_unit_id") != case_id or raw.get("task_id") != case_id:
            raise RepairPipelineError(f"repair selection identity/order mismatch at {case_id}")
        disposition = str(raw.get("disposition") or "")
        if disposition not in {"retain", "repair"}:
            raise RepairPipelineError(f"{case_id} disposition must be retain or repair")
        manual_issues = [
            normalized_issue(issue, case_id, index)
            for index, issue in enumerate(raw.get("issues") or [], 1)
            if isinstance(issue, Mapping)
        ]
        if len(manual_issues) != len(raw.get("issues") or []):
            raise RepairPipelineError(f"{case_id} contains a non-object manual issue")
        source_bindings: list[dict[str, Any]] = []
        for source_index, binding in enumerate(raw.get("audit_sources") or []):
            if not isinstance(binding, Mapping):
                raise RepairPipelineError(f"{case_id} audit source {source_index} is not a binding")
            verify_file_binding(binding, f"{case_id} audit source {source_index}", inside_candidate=True)
            source_bindings.append(dict(binding))
        qc_path = automatic_qc_root / case_id / "qc.json"
        qc = load_json(qc_path, f"{case_id} automatic QC")
        if qc.get("case_unit_id") != case_id or qc.get("task_id") != case_id:
            raise RepairPipelineError(f"{case_id} automatic QC identity differs")
        qc_checks = qc.get("checks")
        qc_raw_issues = qc.get("issues")
        if (
            not isinstance(qc_checks, Mapping)
            or set(qc_checks) != AUTOMATIC_QC_CHECK_KEYS
            or any(not isinstance(value, bool) for value in qc_checks.values())
            or not isinstance(qc_raw_issues, list)
            or any(not isinstance(issue, Mapping) for issue in qc_raw_issues)
        ):
            raise RepairPipelineError(f"{case_id} automatic QC checks/issues are invalid")
        qc_passed = all(qc_checks.values()) and not qc_raw_issues
        if qc.get("status") != ("passed" if qc_passed else "failed"):
            raise RepairPipelineError(f"{case_id} automatic QC status is inconsistent")
        if not qc_passed and (
            not qc_raw_issues
            or not any(issue.get("severity") == "error" for issue in qc_raw_issues)
        ):
            raise RepairPipelineError(
                f"{case_id} failed automatic QC lacks a bound error issue"
            )
        automatic_issues = [
            normalized_issue(dict(issue) | {"source_kind": "automatic_qc"}, case_id, index)
            for index, issue in enumerate(qc_raw_issues, 1)
            if isinstance(issue, Mapping) and issue.get("severity", "error") in {"error", "warning"}
        ]
        all_issues = automatic_issues + manual_issues
        require_unique_issue_ids(all_issues, case_id)
        required_disposition = "repair" if all_issues else "retain"
        if disposition != required_disposition:
            raise RepairPipelineError(
                f"{case_id} disposition={disposition}, but bound issues require {required_disposition}"
            )
        if disposition == "repair" and not any(item["severity"] == "error" for item in all_issues):
            raise RepairPipelineError(f"{case_id} repair requires at least one error-severity issue")
        row = {
            "selection_rank": rank,
            "case_unit_id": case_id,
            "task_id": case_id,
            "disposition": disposition,
            "issues": all_issues,
            "automatic_qc": file_binding(qc_path),
            "audit_sources": source_bindings,
        }
        row["audit_case_sha256"] = object_sha256(row)
        normalized_rows.append(row)
    return selection, normalized_rows


def load_repair_prelock(path: Path) -> dict[str, Any]:
    prelock = load_json(path.resolve(), "repair prelock")
    if prelock.get("schema_version") != REPAIR_PRELOCK_SCHEMA:
        raise RepairPipelineError("repair prelock schema is invalid")
    if prelock.get("status") != "frozen_before_first_repair_model_call":
        raise RepairPipelineError("repair prelock status is invalid")
    verify_self_hash(prelock, "prelock_sha256", "repair prelock")
    if prelock.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("repair prelock does not cover 116 effective cases")
    repair_inputs = list(prelock.get("repair_inputs") or [])
    if prelock.get("repair_count") != len(repair_inputs) or not repair_inputs:
        raise RepairPipelineError("repair prelock repair input count is invalid")
    if prelock.get("repair_inputs_sha256") != object_sha256(repair_inputs):
        raise RepairPipelineError("repair prelock input hash fails")
    for row in repair_inputs:
        verify_binding_tree(row.get("bindings"), f"{row.get('case_unit_id')} repair bindings")
    verify_repair_order_bindings(prelock)
    return prelock


def verify_repair_order_bindings(
    prelock: Mapping[str, Any], label: str = "repair prelock"
) -> dict[str, Any]:
    """Recompute candidate, selection, and lane-aware batch submission orders."""

    candidate = list(prelock.get("case_order") or [])
    repair_inputs = list(prelock.get("repair_inputs") or [])
    if (
        len(candidate) != EXPECTED_CASE_COUNT
        or len(set(candidate)) != EXPECTED_CASE_COUNT
        or prelock.get("case_order_sha256") != object_sha256(candidate)
        or prelock.get("candidate_case_order") != candidate
        or prelock.get("candidate_case_order_sha256") != object_sha256(candidate)
    ):
        raise RepairPipelineError(f"{label} candidate/source case order binding is invalid")
    repair_selection = [str(row.get("case_unit_id") or "") for row in repair_inputs]
    if (
        len(repair_selection) != REPAIR_CONCURRENCY_CASE_COUNT
        or len(set(repair_selection)) != REPAIR_CONCURRENCY_CASE_COUNT
        or any(
            row.get("task_id") != row.get("case_unit_id")
            or row.get("selection_rank") != candidate.index(row.get("case_unit_id"))
            for row in repair_inputs
        )
        or repair_selection
        != [case_id for case_id in candidate if case_id in set(repair_selection)]
        or prelock.get("repair_selection_order") != repair_selection
        or prelock.get("repair_selection_order_sha256") != object_sha256(repair_selection)
    ):
        raise RepairPipelineError(f"{label} source-projected repair selection order is invalid")
    by_case = {row["case_unit_id"]: row for row in repair_inputs}
    name_sorted = sorted(repair_selection)
    regular: list[str] = []
    oversized: list[str] = []
    for case_id in name_sorted:
        packet_path = verify_file_binding(
            (by_case[case_id].get("bindings") or {}).get("batch_packet"),
            f"{case_id} {label} execution packet",
            inside_candidate=True,
        )
        target = (
            oversized
            if packet_path.stat().st_size > REPAIR_LARGE_CASE_THRESHOLD_BYTES
            else regular
        )
        target.append(case_id)
    execution_order = regular + oversized
    execution_plan = [
        {
            "execution_rank": rank,
            "case_unit_id": case_id,
            "selection_rank": by_case[case_id]["selection_rank"],
            "lane": "regular" if case_id in set(regular) else "oversized",
        }
        for rank, case_id in enumerate(execution_order)
    ]
    if (
        prelock.get("repair_execution_order") != execution_order
        or prelock.get("repair_execution_order_sha256") != object_sha256(execution_order)
        or prelock.get("repair_execution_plan") != execution_plan
        or prelock.get("repair_execution_plan_sha256") != object_sha256(execution_plan)
        or prelock.get("order_semantics") != REPAIR_ORDER_SEMANTICS
    ):
        raise RepairPipelineError(f"{label} lane-aware repair execution plan is invalid")
    runner = prelock.get("runner_execution") or {}
    if (
        runner.get("repair_execution_order") != execution_order
        or runner.get("repair_execution_order_sha256") != object_sha256(execution_order)
        or runner.get("repair_execution_plan") != execution_plan
        or runner.get("repair_execution_plan_sha256") != object_sha256(execution_plan)
    ):
        raise RepairPipelineError(f"{label} runner execution-order binding differs")
    return {
        "candidate_case_order": candidate,
        "repair_selection_order": repair_selection,
        "repair_execution_order": execution_order,
        "repair_execution_plan": execution_plan,
    }


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json_create_once(path: Path, payload: Any) -> None:
    """Atomically create a JSON artifact and refuse every existing target.

    ``write_json_atomic`` intentionally supports replacement.  Promotion
    handoffs are content-addressed create-once records, so a pre-check followed
    by replacement would leave a TOCTOU overwrite window.  A same-filesystem
    hard-link publishes the fully fsynced temporary inode only when ``path``
    does not exist.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp_path, path)
        except FileExistsError as exc:
            raise RepairPipelineError(f"refusing to overwrite create-once JSON: {path}") from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temp_path.unlink(missing_ok=True)


def verify_case_identity(checklist: Mapping[str, Any], case_id: str) -> None:
    if checklist.get("domain") != "androidworld":
        raise RepairPipelineError(f"{case_id} checklist domain is not androidworld")
    if checklist.get("case_unit_id") != case_id or checklist.get("task_id") != case_id:
        raise RepairPipelineError(f"{case_id} checklist identity differs")


def verify_checklist_pair(case_dir: Path, case_id: str) -> dict[str, Any]:
    yaml_path = case_dir / "checklist.yaml"
    json_path = case_dir / "checklist.json"
    yaml_value = load_yaml_mapping(yaml_path, f"{case_id} checklist YAML")
    json_value = load_json(json_path, f"{case_id} checklist JSON")
    if yaml_value != json_value:
        raise RepairPipelineError(f"{case_id} checklist YAML and JSON differ")
    verify_case_identity(yaml_value, case_id)
    return yaml_value


def verify_source_wave_complete(prelock: Mapping[str, Any]) -> tuple[Path, dict[str, dict[str, Any]]]:
    wave = source_wave(prelock)
    if not wave.is_dir():
        raise RepairPipelineError(f"source wave is missing: {wave}")
    order = list(prelock.get("case_order") or [])
    observed = {path.name for path in wave.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if observed != set(order):
        raise RepairPipelineError(
            f"source wave case set differs: missing={sorted(set(order)-observed)}, "
            f"extra={sorted(observed-set(order))}"
        )
    summary = load_json(wave / "_batch_summary.json", "source batch summary")
    expected = {
        "total_cases": EXPECTED_CASE_COUNT,
        "completed_cases": EXPECTED_CASE_COUNT,
        "success_cases": EXPECTED_CASE_COUNT,
        "skipped_cases": 0,
        "failed_cases": 0,
        "provider": "codex",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "codex_sandbox": "read-only",
        "quality_check": "none",
    }
    for field, wanted in expected.items():
        if summary.get(field) != wanted:
            raise RepairPipelineError(
                f"source batch summary {field}={summary.get(field)!r}, expected {wanted!r}"
            )
    records_list = load_jsonl(wave / "_batch_results.jsonl")
    records: dict[str, dict[str, Any]] = {}
    for record in records_list:
        case_id = str(record.get("case_unit_dir") or "")
        if case_id in records or case_id not in set(order):
            raise RepairPipelineError(f"source batch record identity is invalid: {case_id!r}")
        if record.get("status") != "success":
            raise RepairPipelineError(f"source batch case {case_id} is not successful")
        records[case_id] = record
    if set(records) != set(order):
        raise RepairPipelineError("source batch result set is not exactly 116 cases")
    for case_id in order:
        case_dir = wave / case_id
        verify_checklist_pair(case_dir, case_id)
        for name in REQUIRED_CASE_SIDECARS:
            if not (case_dir / name).is_file():
                raise RepairPipelineError(f"{case_id} source wave is missing {name}")
        attempts = list(records[case_id].get("attempts") or [])
        accepted = [
            item for item in attempts
            if isinstance(item, Mapping)
            and item.get("returncode") == 0
            and str(item.get("validator") or "").startswith("checklist valid:")
        ]
        if not accepted:
            raise RepairPipelineError(f"{case_id} has no accepted generation attempt")
    return wave, records


def canonical_diff(before: Any, after: Any, prefix: str = "$") -> list[dict[str, Any]]:
    """Return deterministic JSON-path changes without omitting deleted values."""
    changes: list[dict[str, Any]] = []
    if type(before) is not type(after):
        return [{"path": prefix, "before": before, "after": after, "change": "replace"}]
    if isinstance(before, Mapping):
        keys = sorted(set(before) | set(after))
        for key in keys:
            child = f"{prefix}.{key}"
            if key not in before:
                changes.append({"path": child, "after": after[key], "change": "add"})
            elif key not in after:
                changes.append({"path": child, "before": before[key], "change": "remove"})
            else:
                changes.extend(canonical_diff(before[key], after[key], child))
        return changes
    if isinstance(before, list):
        limit = max(len(before), len(after))
        for index in range(limit):
            child = f"{prefix}[{index}]"
            if index >= len(before):
                changes.append({"path": child, "after": after[index], "change": "add"})
            elif index >= len(after):
                changes.append({"path": child, "before": before[index], "change": "remove"})
            else:
                changes.extend(canonical_diff(before[index], after[index], child))
        return changes
    if before != after:
        changes.append({"path": prefix, "before": before, "after": after, "change": "replace"})
    return changes


def guarded_output_directory(path: Path) -> Path:
    """Create an adjacent staging directory; caller atomically renames it."""
    if path.exists():
        raise RepairPipelineError(f"refusing to overwrite output directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{path.name}.staging.", dir=path.parent))


def atomic_promote_directory(staging: Path, destination: Path) -> None:
    if destination.exists():
        raise RepairPipelineError(f"refusing to overwrite output directory: {destination}")
    os.replace(staging, destination)


def verify_internal_hash(value: Mapping[str, Any], fields: Iterable[str], label: str) -> str:
    for field in fields:
        if field in value:
            verify_self_hash(value, field, label)
            return field
    raise RepairPipelineError(f"{label} has no accepted self-hash field")


def _verify_repair_concurrency_samples(
    rows: list[dict[str, Any]],
    *,
    expected_attempt_by_case: Mapping[str, Mapping[str, Any]],
    batch_pid: int,
    drafter_path: str,
) -> dict[str, Any]:
    """Recompute concurrency facts from the self-hashed JSONL rows.

    This deliberately does not consume any aggregate fields from the audit
    summary.  Downstream promotion therefore depends on the raw observation
    stream, not on a self-consistent but potentially fabricated summary.
    """

    if not rows:
        raise RepairPipelineError("repair concurrency JSONL is empty")
    expected_cases = set(expected_attempt_by_case)
    covered: set[str] = set()
    peak = 0
    samples_at_peak = 0
    samples_at_six = 0
    previous_monotonic_ns: int | None = None
    for sequence, row in enumerate(rows):
        label = f"repair concurrency sample {sequence}"
        if (
            set(row)
            != {
                "schema_version",
                "sequence",
                "captured_at",
                "monotonic_ns",
                "batch_pid",
                "active_case_attempt_count",
                "active_case_attempts",
                "sample_sha256",
            }
            or row.get("schema_version") != REPAIR_CONCURRENCY_SAMPLE_SCHEMA
        ):
            raise RepairPipelineError(f"{label} schema is invalid")
        verify_internal_hash(row, ("sample_sha256",), label)
        if row.get("sequence") != sequence:
            raise RepairPipelineError(f"{label} sequence is not contiguous from zero")
        if row.get("batch_pid") != batch_pid:
            raise RepairPipelineError(f"{label} batch PID differs from summary")
        captured_at = row.get("captured_at")
        monotonic_ns = row.get("monotonic_ns")
        active_count = row.get("active_case_attempt_count")
        active = row.get("active_case_attempts")
        if not isinstance(captured_at, str) or not captured_at.strip():
            raise RepairPipelineError(f"{label} captured_at is missing")
        if not isinstance(monotonic_ns, int) or isinstance(monotonic_ns, bool) or monotonic_ns <= 0:
            raise RepairPipelineError(f"{label} monotonic_ns is invalid")
        if previous_monotonic_ns is not None and monotonic_ns <= previous_monotonic_ns:
            raise RepairPipelineError(f"{label} monotonic_ns is not strictly increasing")
        previous_monotonic_ns = monotonic_ns
        if not isinstance(active, list) or active_count != len(active):
            raise RepairPipelineError(f"{label} active count/list differs")
        if (
            not isinstance(active_count, int)
            or isinstance(active_count, bool)
            or active_count < 0
            or active_count > EXPECTED_PARALLELISM
        ):
            raise RepairPipelineError(f"{label} active count is outside 0..6")
        sample_cases: set[str] = set()
        sample_pids: set[int] = set()
        previous_sort_key: tuple[int, int] | None = None
        for active_index, item in enumerate(active):
            if not isinstance(item, Mapping):
                raise RepairPipelineError(f"{label} active row {active_index} is not an object")
            if set(item) != {
                "pid",
                "ppid",
                "pgid",
                "case_unit_id",
                "execution_rank",
                "execution_lane",
                "selection_rank",
                "command_sha256",
                "drafter_path",
                "case_packet_path",
                "case_output_dir",
                "expected_attempt_sha256",
            }:
                raise RepairPipelineError(f"{label} active row {active_index} schema is invalid")
            case_id = str(item.get("case_unit_id") or "")
            pid = item.get("pid")
            ppid = item.get("ppid")
            pgid = item.get("pgid")
            rank = item.get("selection_rank")
            execution_rank = item.get("execution_rank")
            command_sha256 = item.get("command_sha256")
            expected_attempt = expected_attempt_by_case.get(case_id) or {}
            if case_id not in expected_cases:
                raise RepairPipelineError(f"{label} observes extra/unknown case {case_id!r}")
            if rank != expected_attempt.get("selection_rank"):
                raise RepairPipelineError(f"{label} {case_id} selection rank differs")
            if (
                execution_rank != expected_attempt.get("execution_rank")
                or item.get("execution_lane") != expected_attempt.get("execution_lane")
            ):
                raise RepairPipelineError(f"{label} {case_id} execution plan rank/lane differs")
            if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
                raise RepairPipelineError(f"{label} {case_id} PID is invalid")
            if not isinstance(ppid, int) or isinstance(ppid, bool) or ppid < 0:
                raise RepairPipelineError(f"{label} {case_id} PPID is invalid")
            if ppid != batch_pid:
                raise RepairPipelineError(
                    f"{label} {case_id} is not a direct child of the isolated batch runner"
                )
            if pgid != batch_pid:
                raise RepairPipelineError(f"{label} {case_id} is outside the isolated batch PGID")
            if not isinstance(command_sha256, str) or SHA256_RE.fullmatch(command_sha256) is None:
                raise RepairPipelineError(f"{label} {case_id} command hash is invalid")
            allowed_command_hashes = expected_attempt.get("allowed_ps_command_line_sha256")
            if (
                not isinstance(allowed_command_hashes, list)
                or command_sha256 not in allowed_command_hashes
                or item.get("drafter_path") != drafter_path
                or item.get("case_packet_path") != expected_attempt.get("case_packet_path")
                or item.get("case_output_dir") != expected_attempt.get("case_output_dir")
                or item.get("expected_attempt_sha256") != object_sha256(expected_attempt)
            ):
                raise RepairPipelineError(
                    f"{label} {case_id} command is not an exact prelocked drafter attempt"
                )
            if case_id in sample_cases or pid in sample_pids:
                raise RepairPipelineError(f"{label} repeats an active case or PID")
            sort_key = (execution_rank, pid)
            if previous_sort_key is not None and sort_key <= previous_sort_key:
                raise RepairPipelineError(f"{label} active rows are not in canonical rank/PID order")
            previous_sort_key = sort_key
            sample_cases.add(case_id)
            sample_pids.add(pid)
        covered.update(sample_cases)
        if active_count > peak:
            peak = active_count
            samples_at_peak = 1
        elif active_count == peak:
            samples_at_peak += 1
        if active_count == EXPECTED_PARALLELISM:
            samples_at_six += 1
    missing = sorted(expected_cases - covered)
    extra = sorted(covered - expected_cases)
    if peak != EXPECTED_PARALLELISM or samples_at_six < 1:
        raise RepairPipelineError("raw concurrency samples do not prove an observed six-way overlap")
    if missing or extra:
        raise RepairPipelineError(
            f"raw concurrency samples do not cover exact repair universe: missing={missing}, extra={extra}"
        )
    return {
        "sample_count": len(rows),
        "observed_peak_active_case_attempts": peak,
        "samples_at_observed_peak": samples_at_peak,
        "samples_at_required_peak": samples_at_six,
        "observed_cases": sorted(covered),
        "observed_cases_sha256": object_sha256(sorted(covered)),
    }


def verify_repair_concurrency_evidence(
    prelock: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    repair_root: Path | None = None,
) -> dict[str, Any]:
    """Fail-closed revalidation of the repair six-worker audit evidence.

    The verifier re-reads the aggregate JSON and every raw JSONL sample, checks
    their self hashes and exact prelock/config/tool/process bindings, and then
    recomputes the peak and case coverage from raw rows.  Its returned
    self-hashed binding is safe to propagate unchanged through QC, semantic
    handoff, freeze, and the final run manifest.
    """

    if (
        prelock.get("schema_version") != REPAIR_PRELOCK_SCHEMA
        or prelock.get("status") != "frozen_before_first_repair_model_call"
    ):
        raise RepairPipelineError("repair concurrency verifier received an invalid prelock")
    verify_internal_hash(prelock, ("prelock_sha256",), "repair concurrency prelock")
    orders = verify_repair_order_bindings(prelock, "repair concurrency prelock")
    if (
        prelock.get("repair_count") != REPAIR_CONCURRENCY_CASE_COUNT
        or receipt.get("repair_count") != REPAIR_CONCURRENCY_CASE_COUNT
        or receipt.get("repair_id") != prelock.get("repair_id")
    ):
        raise RepairPipelineError("repair concurrency evidence is not the exact 80-case repair wave")

    config_path = verify_file_binding(
        prelock.get("repair_config"), "repair concurrency config", inside_candidate=True
    )
    config = load_json(config_path, "repair concurrency config")
    verify_internal_hash(config, ("config_sha256",), "repair concurrency config")
    if (
        config.get("schema_version") != REPAIR_CONFIG_SCHEMA
        or config.get("status") != "prelocked"
        or config.get("repair_id") != prelock.get("repair_id")
        or config.get("repair_count") != REPAIR_CONCURRENCY_CASE_COUNT
        or config.get("config_sha256") != prelock["repair_config"].get("config_sha256")
    ):
        raise RepairPipelineError("repair concurrency config identity differs from prelock")
    exact_trees = config.get("snapshot_exact_trees")
    if (
        not isinstance(exact_trees, Mapping)
        or exact_trees != prelock.get("snapshot_exact_trees")
        or set(exact_trees) != {"repair", "source_v3", "runtime_source"}
        or config.get("snapshot_exact_trees_sha256") != object_sha256(exact_trees)
        or prelock.get("snapshot_exact_trees_sha256") != object_sha256(exact_trees)
        or receipt.get("snapshot_exact_trees") != exact_trees
        or receipt.get("snapshot_exact_trees_sha256") != object_sha256(exact_trees)
    ):
        raise RepairPipelineError("repair exact-tree descriptors differ across artifacts")
    for name in ("repair", "source_v3", "runtime_source"):
        verify_exact_snapshot_tree_descriptor(
            exact_trees[name], f"repair receipt {name} snapshot"
        )
    bootstrap = isolated_bootstrap_record()
    if (
        bootstrap != config.get("isolated_bootstrap")
        or bootstrap != prelock.get("isolated_bootstrap")
        or bootstrap != receipt.get("isolated_bootstrap")
        or receipt.get("isolated_bootstrap_sha256") != object_sha256(bootstrap)
    ):
        raise RepairPipelineError("repair isolated-bootstrap binding differs across artifacts")
    runtime = config.get("python_runtime")
    if (
        not isinstance(runtime, Mapping)
        or runtime != (prelock.get("runner_execution") or {}).get("python_runtime")
        or receipt.get("python_runtime_sha256") != object_sha256(runtime)
        or runtime.get("required_execution_flags")
        != {"isolated": 1, "no_site": 1, "ignore_environment": 1, "safe_path": True}
        or runtime.get("required_execution_state") != {"dont_write_bytecode": True}
        or (runtime.get("python_startup_security") or {}).get(
            "required_execution_state"
        )
        != runtime.get("required_execution_state")
    ):
        raise RepairPipelineError("repair Python runtime binding differs across artifacts")
    runner_environment = verify_closed_child_environment(
        runtime.get("required_environment"),
        "repair receipt closed child environment",
    )
    if (
        runtime.get("semantic_environment_sha256")
        != object_sha256(runner_environment)
        or config.get("runner_environment") != runner_environment
        or config.get("runner_environment_sha256")
        != object_sha256(runner_environment)
        or (prelock.get("runner_execution") or {}).get("environment")
        != runner_environment
        or (prelock.get("runner_execution") or {}).get("environment_sha256")
        != object_sha256(runner_environment)
        or receipt.get("runner_environment") != runner_environment
        or receipt.get("runner_environment_sha256")
        != object_sha256(runner_environment)
    ):
        raise RepairPipelineError(
            "repair closed child environment hash chain differs"
        )
    auth_records: dict[str, Mapping[str, Any]] = {}
    for phase in ("pre", "post"):
        auth = receipt.get(f"codex_auth_{phase}")
        if not isinstance(auth, Mapping):
            raise RepairPipelineError(f"repair Codex {phase} auth record is missing")
        verify_internal_hash(
            auth, ("auth_check_sha256",), f"repair Codex {phase} auth record"
        )
        warning_present = auth.get("login_path_alias_warning_present")
        expected_warning = CODEX_PATH_ALIAS_WARNING if warning_present is True else None
        if (
            warning_present not in {True, False}
            or auth.get("schema_version")
            != "androidworld_checklist_repair_codex_auth_check/v1"
            or auth.get("login_status") != CODEX_LOGIN_SUCCESS_LINE
            or auth.get("auth_mode") != "codex_login"
            or auth.get("environment_sha256")
            != object_sha256(runner_environment)
            or auth.get("login_path_alias_warning") != expected_warning
            or auth.get("login_path_alias_warning_sha256")
            != (object_sha256(expected_warning) if expected_warning else None)
        ):
            raise RepairPipelineError(
                f"repair Codex {phase} auth/environment evidence differs"
            )
        auth_records[phase] = auth
    expected_warning_receipt = {
        phase: {
            "present": auth_records[phase]["login_path_alias_warning_present"],
            "sha256": auth_records[phase]["login_path_alias_warning_sha256"],
        }
        for phase in ("pre", "post")
    }
    if (
        receipt.get("codex_auth_checks_sha256")
        != object_sha256(
            {"pre": dict(auth_records["pre"]), "post": dict(auth_records["post"])}
        )
        or receipt.get("codex_login_path_alias_warnings")
        != expected_warning_receipt
    ):
        raise RepairPipelineError("repair Codex auth receipt binding differs")
    runtime_source_snapshot = config.get("runtime_source_snapshot")
    if (
        not isinstance(runtime_source_snapshot, Mapping)
        or runtime_source_snapshot != prelock.get("runtime_source_snapshot")
        or runtime_source_snapshot != receipt.get("runtime_source_snapshot")
        or config.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot.get("runtime_source_snapshot_sha256")
        or prelock.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot.get("runtime_source_snapshot_sha256")
        or receipt.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot.get("runtime_source_snapshot_sha256")
    ):
        raise RepairPipelineError(
            "repair runtime-source snapshot differs across artifacts"
        )
    verify_runtime_source_snapshot_binding(
        runtime_source_snapshot,
        "repair receipt runtime source snapshot",
        runtime=runtime,
        repair_exact_tree=exact_trees["repair"],
        runtime_source_exact_tree=exact_trees["runtime_source"],
    )
    if (
        config.get("candidate_case_order") != orders["candidate_case_order"]
        or config.get("candidate_case_order_sha256")
        != object_sha256(orders["candidate_case_order"])
        or config.get("repair_selection_order") != orders["repair_selection_order"]
        or config.get("repair_selection_order_sha256")
        != object_sha256(orders["repair_selection_order"])
        or config.get("repair_execution_order") != orders["repair_execution_order"]
        or config.get("repair_execution_order_sha256")
        != object_sha256(orders["repair_execution_order"])
        or config.get("repair_execution_plan") != orders["repair_execution_plan"]
        or config.get("repair_execution_plan_sha256")
        != object_sha256(orders["repair_execution_plan"])
    ):
        raise RepairPipelineError("repair concurrency config order bindings differ")
    command = config.get("runner_command")
    command_hash = config.get("runner_command_sha256")
    runner_execution = prelock.get("runner_execution") or {}
    prelock_path = resolve_repo_path(config.get("repair_prelock_path"), inside_candidate=True)
    prelock_file_sha256 = sha256_file(prelock_path)
    expanded_command = expand_prelock_sha256(
        command or [],
        file_sha256=prelock_file_sha256,
        internal_sha256=str(prelock.get("prelock_sha256") or ""),
    )
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(item, str) or not item for item in command)
        or command_hash != object_sha256(command)
        or runner_execution.get("command") != command
        or runner_execution.get("command_sha256") != command_hash
        or runner_execution.get("command_is_prelock_hash_template") is not True
        or "--appworld-v56-runtime-gate" in command
        or runner_execution.get("prelock_hash_placeholders")
        != {
            "file_sha256": PRELOCK_FILE_SHA256_PLACEHOLDER,
            "internal_sha256": PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
        }
        or receipt.get("runner_command_template_sha256") != command_hash
        or receipt.get("runner_execution_command_sha256")
        != object_sha256(expanded_command)
        or receipt.get("prelock_file_sha256_anchor") != prelock_file_sha256
        or receipt.get("prelock_internal_sha256_anchor")
        != prelock.get("prelock_sha256")
    ):
        raise RepairPipelineError("repair concurrency runner command/prelock/receipt binding differs")
    if (
        receipt.get("candidate_case_order_sha256")
        != prelock["candidate_case_order_sha256"]
        or receipt.get("repair_selection_order_sha256")
        != prelock["repair_selection_order_sha256"]
        or receipt.get("repair_execution_order") != orders["repair_execution_order"]
        or receipt.get("repair_execution_order_sha256")
        != prelock["repair_execution_order_sha256"]
        or receipt.get("repair_execution_plan") != orders["repair_execution_plan"]
        or receipt.get("repair_execution_plan_sha256")
        != prelock["repair_execution_plan_sha256"]
        or receipt.get("order_semantics") != REPAIR_ORDER_SEMANTICS
    ):
        raise RepairPipelineError("repair receipt case/execution order binding differs")
    raw_results_path = verify_file_binding(
        receipt.get("raw_batch_results"),
        "repair raw batch completion records",
        inside_candidate=True,
    )
    raw_completion_order = [
        str(row.get("case_unit_dir") or "") for row in load_jsonl(raw_results_path)
    ]
    if (
        len(raw_completion_order) != REPAIR_CONCURRENCY_CASE_COUNT
        or len(set(raw_completion_order)) != REPAIR_CONCURRENCY_CASE_COUNT
        or set(raw_completion_order) != set(orders["repair_execution_order"])
        or receipt.get("raw_batch_completion_order") != raw_completion_order
        or receipt.get("raw_batch_completion_order_sha256")
        != object_sha256(raw_completion_order)
    ):
        raise RepairPipelineError("repair receipt raw as_completed order binding differs")

    attempt_namespace = config.get("attempt_namespace")
    if (
        not isinstance(attempt_namespace, Mapping)
        or attempt_namespace != prelock.get("attempt_namespace")
        or attempt_namespace != receipt.get("attempt_namespace")
    ):
        raise RepairPipelineError(
            "repair attempt namespace differs across config/prelock/receipt"
        )
    verify_internal_hash(
        attempt_namespace,
        ("attempt_namespace_sha256",),
        "repair attempt namespace",
    )
    attempt_root = resolve_repo_path(config.get("attempt_root"), inside_candidate=True)
    output_root = resolve_repo_path(config.get("output_root"), inside_candidate=True)
    evidence_root = resolve_repo_path(config.get("evidence_root"), inside_candidate=True)
    scratch_root = resolve_repo_path(config.get("scratch_root"), inside_candidate=True)
    attempt_layout = {
        "wave": output_root,
        "evidence": evidence_root,
        "scratch": scratch_root,
    }
    expected_namespace = {
        "schema_version": "androidworld_checklist_repair_attempt_namespace/v1",
        "attempt_root": repo_relative(attempt_root),
        "layout": {
            role: repo_relative(attempt_layout[role]) for role in ATTEMPT_LAYOUT_ROLES
        },
        "root_must_be_absent_at_prelock_and_generation_preflight": True,
        "root_claim": "os.mkdir(mode=0700, parents=false, exist_ok=false)",
        "layout_precreated_inside_claim": True,
        "directory_fds_held_through_final_prelock_revalidation": True,
        "all_attempt_artifacts_must_be_contained": True,
        "restart_archives_entire_attempt_root": True,
        "appworld_v56_runtime_gate": False,
    }
    if (
        output_root != attempt_root / "wave"
        or evidence_root != attempt_root / "evidence"
        or scratch_root != attempt_root / "scratch"
        or any(
            attempt_namespace.get(key) != value
            for key, value in expected_namespace.items()
        )
        or receipt.get("attempt_namespace_sha256")
        != attempt_namespace.get("attempt_namespace_sha256")
    ):
        raise RepairPipelineError("repair attempt namespace contract differs")
    audit = config.get("concurrency_audit")
    if not isinstance(audit, Mapping) or audit != prelock.get("concurrency_audit"):
        raise RepairPipelineError("repair concurrency audit config differs across config/prelock")
    expected_fixed = {
        "schema_version": "androidworld_checklist_repair_concurrency_audit_config/v1",
        "required_observed_peak_active_case_attempts": EXPECTED_PARALLELISM,
        "maximum_allowed_active_case_attempts": EXPECTED_PARALLELISM,
        "minimum_samples_at_required_peak": 1,
        "every_repair_case_must_be_observed": True,
        "sample_interval_milliseconds": 100,
        "popen_start_new_session": True,
        "ps_command": ["/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,command="],
        "batch_runner_command_sha256": command_hash,
        "batch_runner_command_is_prelock_hash_template": True,
        "appworld_v56_runtime_gate": False,
        "runner_environment": runner_environment,
        "runner_environment_sha256": object_sha256(runner_environment),
        "attempt_namespace_sha256": attempt_namespace[
            "attempt_namespace_sha256"
        ],
        "isolated_bootstrap_sha256": object_sha256(bootstrap),
        "snapshot_exact_tree_hashes": {
            "repair": exact_trees["repair"]["descriptor_sha256"],
            "source_v3": exact_trees["source_v3"]["descriptor_sha256"],
            "runtime_source": exact_trees["runtime_source"]["descriptor_sha256"],
        },
        "runtime_source_snapshot_sha256": runtime_source_snapshot[
            "runtime_source_snapshot_sha256"
        ],
        "foreign_process_patterns": [
            "run_checklist_repair_batch.py",
            "run_draft_batch.py",
            "draft_case_checklist.py",
            "codex exec",
        ],
        "foreign_drafting_processes_must_be_absent_at_preflight_and_during_run": True,
        "immediate_foreign_preflight_required_inside_signal_block": True,
        "immediate_foreign_preflight_timing_policy": (
            "after deterministic generation-token revalidation and signal blocking, "
            "atomically claim attempt_root and precreate wave/evidence/scratch; then require "
            "final foreign-process absence immediately before the single batch Popen"
        ),
        "batch_process_group_must_be_empty_postflight": True,
        "repair_execution_plan": orders["repair_execution_plan"],
        "repair_execution_plan_sha256": object_sha256(orders["repair_execution_plan"]),
        "execution_order_semantics": (
            "execution_rank is the frozen lane-aware ThreadPoolExecutor submission plan: "
            "name-sorted regular packets, then name-sorted oversized packets; actual "
            "worker start/completion timing is scheduler-dependent and raw JSONL is "
            "as_completed order"
        ),
    }
    if any(audit.get(key) != value for key, value in expected_fixed.items()):
        raise RepairPipelineError("repair concurrency fixed audit contract differs")
    cleanup = audit.get("failure_cleanup")
    if cleanup != {
        "scope": "batch_process_group",
        "term_signal": "SIGTERM",
        "term_grace_seconds": 5,
        "kill_signal": "SIGKILL",
        "kill_wait_seconds": 5,
    }:
        raise RepairPipelineError("repair concurrency process-group cleanup contract differs")
    if audit.get("outer_signal_cleanup") != {
        "signals": ["SIGINT", "SIGTERM", "SIGHUP"],
        "block_during_popen_and_handler_install": True,
        "cleanup_scope": "batch_process_group",
        "restore_original_handlers_and_mask": True,
    }:
        raise RepairPipelineError("repair concurrency outer-signal cleanup contract differs")
    monitor = audit.get("monitor_implementation")
    if monitor != (prelock.get("repair_tool_bindings") or {}).get("repair_runner"):
        raise RepairPipelineError("repair concurrency monitor is not the prelocked repair runner")
    verify_file_binding(monitor, "repair concurrency monitor", inside_candidate=True)
    if audit.get("outer_wrapper_invocation") != monitor:
        raise RepairPipelineError("repair outer wrapper is not the prelocked repair runner")
    verify_file_binding(audit.get("frozen_drafter"), "repair concurrency drafter", inside_candidate=True)
    ps_binary = audit.get("ps_binary") or {}
    ps_path = Path(str(ps_binary.get("invocation_path") or ""))
    if (
        str(ps_path) != "/bin/ps"
        or not ps_path.is_file()
        or str(ps_path.resolve(strict=True)) != ps_binary.get("resolved_path")
        or sha256_file(ps_path) != ps_binary.get("sha256")
        or ps_path.stat().st_size != ps_binary.get("size_bytes")
    ):
        raise RepairPipelineError("repair concurrency bound /bin/ps bytes changed")

    expected_attempts = audit.get("expected_case_attempts")
    repair_inputs = list(prelock.get("repair_inputs") or [])
    if (
        not isinstance(expected_attempts, list)
        or len(expected_attempts) != REPAIR_CONCURRENCY_CASE_COUNT
        or audit.get("expected_case_attempts_sha256") != object_sha256(expected_attempts)
        or len(repair_inputs) != REPAIR_CONCURRENCY_CASE_COUNT
    ):
        raise RepairPipelineError("repair concurrency expected-attempt index is invalid")
    output_root = resolve_repo_path(config.get("output_root"), inside_candidate=True)
    if repair_root is not None and output_root != repair_root.resolve():
        raise RepairPipelineError("repair concurrency output root differs from receipt root")
    frozen_drafter_path = verify_file_binding(
        audit.get("frozen_drafter"), "repair concurrency drafter", inside_candidate=True
    )
    repair_prompt_path = verify_file_binding(
        (prelock.get("repair_tool_bindings") or {}).get("repair_prompt"),
        "repair concurrency prompt",
        inside_candidate=True,
    )
    python_invocation = str((config.get("python_runtime") or {}).get("invocation_path") or "")
    expected_attempt_by_case: dict[str, Mapping[str, Any]] = {}
    repair_by_case = {row["case_unit_id"]: row for row in repair_inputs}
    for index, (item, plan_row) in enumerate(
        zip(expected_attempts, orders["repair_execution_plan"], strict=True)
    ):
        repair_input = repair_by_case[plan_row["case_unit_id"]]
        if not isinstance(item, Mapping) or not isinstance(repair_input, Mapping):
            raise RepairPipelineError(f"repair concurrency expected-attempt row {index} is invalid")
        if set(item) != {
            "execution_rank",
            "execution_lane",
            "selection_rank",
            "case_unit_id",
            "task_id",
            "case_packet_path",
            "case_output_dir",
            "allowed_process_commands",
            "allowed_process_commands_sha256",
            "allowed_commands_are_prelock_hash_templates",
            "allowed_ps_command_line_sha256",
        }:
            raise RepairPipelineError(
                f"repair concurrency expected-attempt row {index} schema is invalid"
            )
        case_id = str(repair_input.get("case_unit_id") or "")
        rank = repair_input.get("selection_rank")
        if not case_id or case_id in expected_attempt_by_case or not isinstance(rank, int):
            raise RepairPipelineError("repair concurrency repair-input identity is invalid")
        packet_path = verify_file_binding(
            (repair_input.get("bindings") or {}).get("batch_packet"),
            f"{case_id} repair concurrency packet",
            inside_candidate=True,
        )
        if (
            item.get("execution_rank") != index
            or item.get("execution_rank") != plan_row["execution_rank"]
            or item.get("execution_lane") != plan_row["lane"]
            or item.get("case_unit_id") != case_id
            or item.get("case_unit_id") != plan_row["case_unit_id"]
            or item.get("task_id") != case_id
            or item.get("selection_rank") != rank
            or item.get("selection_rank") != plan_row["selection_rank"]
            or item.get("case_packet_path") != str(packet_path)
            or item.get("case_output_dir") != str((output_root / case_id).resolve())
            or item.get("allowed_commands_are_prelock_hash_templates") is not True
        ):
            raise RepairPipelineError(f"{case_id} repair concurrency expected command binding differs")
        allowed_commands = item.get("allowed_process_commands")
        allowed_hashes = item.get("allowed_ps_command_line_sha256")
        if (
            not isinstance(allowed_commands, list)
            or len(allowed_commands) != 3
            or item.get("allowed_process_commands_sha256") != object_sha256(allowed_commands)
            or allowed_hashes
            != [command.get("ps_command_line_sha256") for command in allowed_commands]
            or len(set(allowed_hashes or [])) != 3
        ):
            raise RepairPipelineError(f"{case_id} exact allowed-attempt command index is invalid")
        oversized = packet_path.stat().st_size > REPAIR_LARGE_CASE_THRESHOLD_BYTES
        expected_lane = "oversized" if oversized else "regular"
        expected_http_timeout = 480 if oversized else 180
        expected_codex_timeout = config.get(
            "large_codex_timeout_seconds" if oversized else "codex_timeout_seconds"
        )
        for attempt_index, (allowed, token_budget) in enumerate(
            zip(allowed_commands, (12000, 16000, 20000), strict=True), 1
        ):
            if not isinstance(allowed, Mapping):
                raise RepairPipelineError(f"{case_id} allowed command {attempt_index} is invalid")
            if set(allowed) != {
                "attempt_index",
                "max_output_tokens",
                "lane",
                "http_timeout_seconds",
                "codex_timeout_seconds",
                "command",
                "command_sha256",
                "ps_command_line_sha256",
            }:
                raise RepairPipelineError(
                    f"{case_id} allowed command {attempt_index} schema is invalid"
                )
            argv = allowed.get("command")
            if (
                not isinstance(argv, list)
                or not argv
                or len(argv) < 15
                or any(not isinstance(arg, str) or not arg or any(ch.isspace() for ch in arg) for arg in argv)
                or allowed.get("attempt_index") != attempt_index
                or allowed.get("max_output_tokens") != token_budget
                or allowed.get("lane") != expected_lane
                or allowed.get("http_timeout_seconds") != expected_http_timeout
                or allowed.get("codex_timeout_seconds") != expected_codex_timeout
                or allowed.get("command_sha256") != object_sha256(argv)
                or allowed.get("ps_command_line_sha256") != object_sha256(" ".join(argv))
                or argv[:5]
                != [python_invocation, "-I", "-S", "-c", bootstrap["payload"]]
                or argv[5:14]
                != [
                    str(prelock_path),
                    PRELOCK_FILE_SHA256_PLACEHOLDER,
                    PRELOCK_INTERNAL_SHA256_PLACEHOLDER,
                    exact_trees["repair"]["descriptor_sha256"],
                    exact_trees["source_v3"]["descriptor_sha256"],
                    exact_trees["runtime_source"]["descriptor_sha256"],
                    "script",
                    str(frozen_drafter_path),
                    "--",
                ]
                or argv[14] != str(packet_path)
            ):
                raise RepairPipelineError(
                    f"{case_id} allowed command {attempt_index} core binding is invalid"
                )
            flag_values: dict[str, str] = {}
            for flag in (
                "-o",
                "--raw-json-output",
                "--raw-api-response",
                "--model",
                "--provider",
                "--reasoning-effort",
                "--max-output-tokens",
                "--http-timeout-seconds",
                "--codex-timeout-seconds",
                "--codex-sandbox",
                "--prompt-supplement",
            ):
                if argv.count(flag) != 1:
                    raise RepairPipelineError(
                        f"{case_id} allowed command {attempt_index} flag {flag} differs"
                    )
                position = argv.index(flag)
                if position + 1 >= len(argv):
                    raise RepairPipelineError(
                        f"{case_id} allowed command {attempt_index} flag {flag} has no value"
                    )
                flag_values[flag] = argv[position + 1]
            prefix = f"attempt_{attempt_index:02d}"
            expected_values = {
                "-o": str((output_root / case_id / f"{prefix}.checklist.yaml").resolve()),
                "--raw-json-output": str(
                    (output_root / case_id / f"{prefix}.checklist.json").resolve()
                ),
                "--raw-api-response": str(
                    (output_root / case_id / f"{prefix}.api_response.json").resolve()
                ),
                "--model": "gpt-5.6-sol",
                "--provider": "codex",
                "--reasoning-effort": "xhigh",
                "--max-output-tokens": str(token_budget),
                "--http-timeout-seconds": str(expected_http_timeout),
                "--codex-timeout-seconds": str(expected_codex_timeout),
                "--codex-sandbox": "read-only",
                "--prompt-supplement": str(repair_prompt_path),
            }
            if flag_values != expected_values:
                raise RepairPipelineError(
                    f"{case_id} allowed command {attempt_index} exact output/model binding differs"
                )
        expanded_item = copy.deepcopy(dict(item))
        expanded_allowed: list[dict[str, Any]] = []
        for allowed in allowed_commands:
            expanded_allowed_row = copy.deepcopy(dict(allowed))
            expanded_argv = expand_prelock_sha256(
                list(expanded_allowed_row["command"]),
                file_sha256=prelock_file_sha256,
                internal_sha256=prelock["prelock_sha256"],
            )
            expanded_allowed_row["command"] = expanded_argv
            expanded_allowed_row["command_sha256"] = object_sha256(expanded_argv)
            expanded_allowed_row["ps_command_line_sha256"] = object_sha256(
                " ".join(expanded_argv)
            )
            expanded_allowed.append(expanded_allowed_row)
        expanded_item["allowed_process_commands"] = expanded_allowed
        expanded_item["allowed_process_commands_sha256"] = object_sha256(expanded_allowed)
        expanded_item["allowed_ps_command_line_sha256"] = [
            row["ps_command_line_sha256"] for row in expanded_allowed
        ]
        expanded_item["allowed_commands_are_prelock_hash_templates"] = False
        expected_attempt_by_case[case_id] = expanded_item

    summary_path = verify_file_binding(
        receipt.get("concurrency_audit"), "repair concurrency summary", inside_candidate=True
    )
    configured_summary_path = resolve_repo_path(audit.get("summary_path"), inside_candidate=True)
    if summary_path != configured_summary_path:
        raise RepairPipelineError("repair concurrency summary path differs from prelock")
    summary = load_json(summary_path, "repair concurrency summary")
    verify_internal_hash(summary, ("audit_sha256",), "repair concurrency summary")
    if (
        summary.get("audit_sha256") != (receipt.get("concurrency_audit") or {}).get("audit_sha256")
        or summary.get("schema_version") != REPAIR_CONCURRENCY_SUMMARY_SCHEMA
        or summary.get("status") != "pass"
        or summary.get("repair_id") != prelock.get("repair_id")
        or summary.get("repair_prelock_sha256") != prelock.get("prelock_sha256")
        or summary.get("batch_returncode") != 0
        or not isinstance(summary.get("batch_pid"), int)
        or isinstance(summary.get("batch_pid"), bool)
        or summary.get("batch_pid") <= 0
        or summary.get("sample_interval_milliseconds") != audit.get("sample_interval_milliseconds")
        or summary.get("ps_binary") != ps_binary
        or summary.get("ps_command") != audit.get("ps_command")
        or summary.get("monitor_implementation") != monitor
        or summary.get("outer_wrapper_invocation") != monitor
        or summary.get("batch_runner_command_sha256") != command_hash
        or summary.get("batch_runner_execution_command_sha256")
        != object_sha256(expanded_command)
        or summary.get("prelock_file_sha256_anchor") != prelock_file_sha256
        or summary.get("prelock_internal_sha256_anchor")
        != prelock.get("prelock_sha256")
        or summary.get("snapshot_exact_tree_hashes")
        != expected_fixed["snapshot_exact_tree_hashes"]
        or summary.get("isolated_bootstrap_sha256") != object_sha256(bootstrap)
        or summary.get("python_runtime_sha256")
        != object_sha256(config.get("python_runtime"))
        or summary.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot["runtime_source_snapshot_sha256"]
        or summary.get("runner_environment") != runner_environment
        or summary.get("runner_environment_sha256")
        != object_sha256(runner_environment)
        or summary.get("attempt_namespace_sha256")
        != attempt_namespace["attempt_namespace_sha256"]
        or summary.get("expected_case_attempts_sha256")
        != audit.get("expected_case_attempts_sha256")
        or summary.get("repair_execution_plan") != orders["repair_execution_plan"]
        or summary.get("repair_execution_plan_sha256")
        != object_sha256(orders["repair_execution_plan"])
        or summary.get("execution_order_semantics")
        != audit.get("execution_order_semantics")
        or summary.get("scope_rule") != audit.get("scope_rule")
        or summary.get("popen_start_new_session") is not True
        or summary.get("failure_cleanup_policy") != cleanup
        or summary.get("monitor_errors") != []
        or summary.get("cleanup_events") != []
        or summary.get("outer_wrapper_signal") is not None
    ):
        raise RepairPipelineError("repair concurrency summary contract/prelock bindings differ")
    foreign_preflight = summary.get("foreign_process_preflight")
    if not isinstance(foreign_preflight, Mapping):
        raise RepairPipelineError("repair concurrency foreign-process preflight is missing")
    verify_internal_hash(
        foreign_preflight,
        ("preflight_sha256",),
        "repair concurrency foreign-process preflight",
    )
    generation_preflight = summary.get("generation_preflight")
    if (
        not isinstance(generation_preflight, Mapping)
        or receipt.get("generation_preflight") != generation_preflight
    ):
        raise RepairPipelineError("repair generation launch preflight is missing")
    verify_internal_hash(
        generation_preflight,
        ("generation_preflight_sha256",),
        "repair generation launch preflight",
    )
    deterministic_preflight = generation_preflight.get("deterministic_preflight")
    immediate_preflight = generation_preflight.get("immediate_foreign_preflight")
    attempt_claim = generation_preflight.get("attempt_root_claim")
    if not isinstance(deterministic_preflight, Mapping) or not isinstance(
        immediate_preflight, Mapping
    ) or not isinstance(attempt_claim, Mapping):
        raise RepairPipelineError(
            "repair launch preflight lacks deterministic/immediate evidence"
        )
    verify_internal_hash(
        deterministic_preflight,
        ("generation_preflight_sha256",),
        "repair nested deterministic generation preflight",
    )
    verify_internal_hash(
        immediate_preflight,
        ("immediate_preflight_sha256",),
        "repair nested immediate foreign preflight",
    )
    generation_core = generation_preflight.get("core") or {}
    expected_output_root = output_root
    expected_absent_targets = [str(attempt_root)]
    parent_records = generation_core.get("creatable_parent_records")
    if (
        set(generation_preflight)
        != {
            "schema_version",
            "created_at",
            "monotonic_ns",
            "status",
            "core",
            "core_sha256",
            "deterministic_preflight",
            "deterministic_preflight_sha256",
            "immediate_foreign_preflight",
            "immediate_foreign_preflight_sha256",
            "attempt_root_claim",
            "attempt_root_claim_sha256",
            "popen_is_next_state_changing_operation",
            "generation_preflight_sha256",
        }
        or generation_preflight.get("schema_version")
        != "androidworld_checklist_repair_generation_launch_preflight/v2"
        or generation_preflight.get("status") != "pass"
        or generation_preflight.get("core_sha256") != object_sha256(generation_core)
        or generation_preflight.get("deterministic_preflight_sha256")
        != deterministic_preflight.get("generation_preflight_sha256")
        or generation_preflight.get("immediate_foreign_preflight_sha256")
        != immediate_preflight.get("immediate_preflight_sha256")
        or generation_preflight.get("attempt_root_claim") != attempt_claim
        or generation_preflight.get("attempt_root_claim_sha256")
        != attempt_claim.get("claim_sha256")
        or generation_preflight.get("popen_is_next_state_changing_operation")
        is not True
        or set(deterministic_preflight)
        != {
            "schema_version",
            "created_at",
            "monotonic_ns",
            "status",
            "core",
            "core_sha256",
            "generation_preflight_sha256",
        }
        or deterministic_preflight.get("schema_version")
        != "androidworld_checklist_repair_generation_preflight/v1"
        or deterministic_preflight.get("status") != "pass"
        or deterministic_preflight.get("core") != generation_core
        or deterministic_preflight.get("core_sha256")
        != object_sha256(generation_core)
        or summary.get("immediate_foreign_preflight") != immediate_preflight
        or receipt.get("immediate_foreign_preflight") != immediate_preflight
        or not isinstance(generation_preflight.get("monotonic_ns"), int)
        or isinstance(generation_preflight.get("monotonic_ns"), bool)
        or not isinstance(immediate_preflight.get("monotonic_ns"), int)
        or isinstance(immediate_preflight.get("monotonic_ns"), bool)
        or generation_preflight["monotonic_ns"]
        < immediate_preflight["monotonic_ns"]
        or generation_core.get("repair_id") != prelock["repair_id"]
        or generation_core.get("repair_prelock_sha256") != prelock["prelock_sha256"]
        or generation_core.get("repair_config_sha256") != config["config_sha256"]
        or generation_core.get("runner_command_template_sha256") != command_hash
        or generation_core.get("runner_execution_command_sha256")
        != object_sha256(expanded_command)
        or generation_core.get("prelock_file_sha256_anchor") != prelock_file_sha256
        or generation_core.get("prelock_internal_sha256_anchor")
        != prelock["prelock_sha256"]
        or generation_core.get("snapshot_exact_tree_hashes")
        != expected_fixed["snapshot_exact_tree_hashes"]
        or generation_core.get("isolated_bootstrap_sha256")
        != object_sha256(bootstrap)
        or generation_core.get("python_runtime_sha256")
        != object_sha256(config.get("python_runtime"))
        or generation_core.get("runtime_source_snapshot_sha256")
        != runtime_source_snapshot["runtime_source_snapshot_sha256"]
        or generation_core.get("candidate_case_order_sha256")
        != prelock["candidate_case_order_sha256"]
        or generation_core.get("repair_selection_order_sha256")
        != prelock["repair_selection_order_sha256"]
        or generation_core.get("repair_execution_order_sha256")
        != prelock["repair_execution_order_sha256"]
        or generation_core.get("repair_execution_plan_sha256")
        != prelock["repair_execution_plan_sha256"]
        or generation_core.get("expected_case_attempts_sha256")
        != audit["expected_case_attempts_sha256"]
        or generation_core.get("expected_case_ids") != orders["repair_execution_order"]
        or generation_core.get("expected_case_count") != REPAIR_CONCURRENCY_CASE_COUNT
        or generation_core.get("packet_root")
        != str(resolve_repo_path(config["packet_set_root"], inside_candidate=True))
        or generation_core.get("attempt_root") != str(attempt_root)
        or generation_core.get("attempt_layout")
        != {role: str(attempt_layout[role]) for role in ATTEMPT_LAYOUT_ROLES}
        or generation_core.get("attempt_namespace_sha256")
        != attempt_namespace["attempt_namespace_sha256"]
        or generation_core.get("output_root") != str(expected_output_root)
        or generation_core.get("absent_targets") != expected_absent_targets
        or not isinstance(parent_records, list)
        or [row.get("target") for row in parent_records if isinstance(row, Mapping)]
        != expected_absent_targets
        or any(
            not isinstance(row, Mapping)
            or row.get("writable") is not True
            or row.get("searchable") is not True
            or not isinstance(row.get("nearest_existing_ancestor"), str)
            for row in (parent_records or [])
        )
        or generation_core.get("foreign_process_preflight_sha256")
        != foreign_preflight["preflight_sha256"]
        or generation_core.get("required_environment") != runner_environment
        or generation_core.get("required_environment_sha256")
        != object_sha256(runner_environment)
        or generation_core.get("codex_auth_pre_sha256")
        != object_sha256(dict(receipt.get("codex_auth_pre") or {}))
        or generation_core.get("no_files_created_by_preflight") is not True
    ):
        raise RepairPipelineError("repair generation launch preflight binding is invalid")
    verify_immediate_foreign_preflight_evidence(
        immediate_preflight,
        audit=audit,
        early_foreign_preflight=foreign_preflight,
        deterministic_generation_preflight=deterministic_preflight,
        attempt_claim=attempt_claim,
        label="repair immediate foreign-process preflight",
    )
    verify_attempt_root_claim(
        attempt_claim,
        repair_id=prelock["repair_id"],
        attempt_root=attempt_root,
        expected_layout=attempt_layout,
        label="repair receipt attempt-root claim",
    )
    if (
        summary.get("attempt_root_claim") != attempt_claim
        or summary.get("attempt_root_claim_sha256")
        != attempt_claim.get("claim_sha256")
        or receipt.get("attempt_root_claim") != attempt_claim
        or receipt.get("attempt_root_claim_sha256")
        != attempt_claim.get("claim_sha256")
    ):
        raise RepairPipelineError("repair attempt-root claim chain differs")
    foreign_processes = foreign_preflight.get("foreign_processes")
    foreign_during = summary.get("foreign_processes_seen_during_run")
    if (
        foreign_preflight.get("schema_version")
        != "androidworld_checklist_repair_foreign_process_preflight/v1"
        or set(foreign_preflight)
        != {
            "schema_version",
            "captured_at",
            "monotonic_ns",
            "ps_binary",
            "ps_command",
            "patterns",
            "excluded_runner_pid",
            "excluded_runner_ancestor_pids",
            "foreign_processes",
            "foreign_process_count",
            "status",
            "binding_policy",
            "preflight_sha256",
        }
        or foreign_preflight.get("status") != "pass"
        or foreign_preflight.get("binding_policy")
        != "foreign drafting processes must be absent before batch launch"
        or foreign_processes != []
        or foreign_preflight.get("foreign_process_count") != 0
        or foreign_preflight.get("ps_binary") != ps_binary
        or foreign_preflight.get("ps_command") != audit.get("ps_command")
        or foreign_preflight.get("patterns") != audit.get("foreign_process_patterns")
        or not isinstance(foreign_preflight.get("captured_at"), str)
        or not foreign_preflight.get("captured_at")
        or not isinstance(foreign_preflight.get("monotonic_ns"), int)
        or isinstance(foreign_preflight.get("monotonic_ns"), bool)
        or foreign_preflight.get("monotonic_ns") <= 0
        or foreign_during != []
        or receipt.get("foreign_process_preflight") != foreign_preflight
        or receipt.get("foreign_processes_seen_during_run") != []
    ):
        raise RepairPipelineError("repair concurrency foreign-process absence proof is invalid")
    postflight = summary.get("batch_process_group_postflight")
    if not isinstance(postflight, Mapping):
        raise RepairPipelineError("repair batch process-group postflight is missing")
    verify_internal_hash(
        postflight,
        ("postflight_sha256",),
        "repair batch process-group postflight",
    )
    if (
        set(postflight)
        != {
            "schema_version",
            "captured_at",
            "status",
            "batch_pid",
            "process_group_id",
            "ps_binary",
            "ps_command",
            "members_detected_before_cleanup",
            "member_count_before_cleanup",
            "cleanup_was_required",
            "remaining_processes",
            "remaining_process_count",
            "process_group_empty",
            "cleanup_failures",
            "postflight_sha256",
        }
        or postflight.get("schema_version")
        != "androidworld_checklist_repair_batch_process_group_postflight/v1"
        or postflight.get("status") != "pass"
        or postflight.get("batch_pid") != summary.get("batch_pid")
        or postflight.get("process_group_id") != summary.get("batch_pid")
        or postflight.get("ps_binary") != ps_binary
        or postflight.get("ps_command") != audit.get("ps_command")
        or postflight.get("members_detected_before_cleanup") != []
        or postflight.get("member_count_before_cleanup") != 0
        or postflight.get("cleanup_was_required") is not False
        or postflight.get("remaining_processes") != []
        or postflight.get("remaining_process_count") != 0
        or postflight.get("process_group_empty") is not True
        or postflight.get("cleanup_failures") != []
        or not isinstance(postflight.get("captured_at"), str)
        or not postflight.get("captured_at")
    ):
        raise RepairPipelineError(
            "repair batch process group is not proven empty after the monitored run"
        )
    samples_path = verify_file_binding(
        summary.get("samples"), "repair concurrency JSONL samples", inside_candidate=True
    )
    configured_samples_path = resolve_repo_path(audit.get("samples_path"), inside_candidate=True)
    if samples_path != configured_samples_path:
        raise RepairPipelineError("repair concurrency sample path differs from prelock")
    rows = load_jsonl(samples_path)
    recomputed = _verify_repair_concurrency_samples(
        rows,
        expected_attempt_by_case=expected_attempt_by_case,
        batch_pid=summary["batch_pid"],
        drafter_path=str(frozen_drafter_path),
    )
    expected_cases = recomputed["observed_cases"]
    gates = summary.get("gates")
    if (
        not isinstance(gates, Mapping)
        or set(gates) != REPAIR_CONCURRENCY_GATE_KEYS
        or any(gates.get(key) is not True for key in REPAIR_CONCURRENCY_GATE_KEYS)
        or summary.get("sample_count") != recomputed["sample_count"]
        or summary.get("observed_peak_active_case_attempts")
        != recomputed["observed_peak_active_case_attempts"]
        or summary.get("samples_at_observed_peak") != recomputed["samples_at_observed_peak"]
        or summary.get("expected_case_count") != REPAIR_CONCURRENCY_CASE_COUNT
        or summary.get("observed_case_count") != REPAIR_CONCURRENCY_CASE_COUNT
        or summary.get("observed_cases") != expected_cases
        or summary.get("missing_cases") != []
        or summary.get("extra_cases") != []
        or receipt.get("observed_peak_active_case_attempts") != EXPECTED_PARALLELISM
        or receipt.get("all_repair_cases_observed_by_concurrency_audit") is not True
    ):
        raise RepairPipelineError("repair concurrency aggregate fields differ from raw samples")

    evidence = {
        "schema_version": REPAIR_CONCURRENCY_EVIDENCE_SCHEMA,
        "status": "pass",
        "repair_id": prelock["repair_id"],
        "repair_prelock_sha256": prelock["prelock_sha256"],
        "repair_config_sha256": config["config_sha256"],
        "runner_command_sha256": command_hash,
        "monitor_implementation": copy.deepcopy(dict(monitor)),
        "outer_wrapper_invocation": copy.deepcopy(dict(monitor)),
        "ps_binary": copy.deepcopy(dict(ps_binary)),
        "ps_command": list(audit["ps_command"]),
        "foreign_process_patterns": list(audit["foreign_process_patterns"]),
        "foreign_process_preflight_sha256": foreign_preflight["preflight_sha256"],
        "foreign_process_preflight_count": 0,
        "immediate_foreign_preflight_sha256": immediate_preflight[
            "immediate_preflight_sha256"
        ],
        "immediate_foreign_preflight_count": 0,
        "generation_launch_preflight_sha256": generation_preflight[
            "generation_preflight_sha256"
        ],
        "attempt_namespace_sha256": attempt_namespace[
            "attempt_namespace_sha256"
        ],
        "attempt_root_claim_sha256": attempt_claim["claim_sha256"],
        "runner_environment_sha256": object_sha256(runner_environment),
        "foreign_process_during_run_observation_count": 0,
        "foreign_drafting_processes_absent": True,
        "repair_execution_order_sha256": prelock["repair_execution_order_sha256"],
        "repair_execution_plan_sha256": prelock["repair_execution_plan_sha256"],
        "batch_process_group_postflight_sha256": postflight["postflight_sha256"],
        "batch_process_group_empty_postflight": True,
        "summary": file_binding(summary_path) | {"audit_sha256": summary["audit_sha256"]},
        "samples": file_binding(samples_path),
        "sample_count": recomputed["sample_count"],
        "observed_peak_active_case_attempts": recomputed[
            "observed_peak_active_case_attempts"
        ],
        "samples_at_required_peak": recomputed["samples_at_required_peak"],
        "expected_case_count": REPAIR_CONCURRENCY_CASE_COUNT,
        "observed_case_count": REPAIR_CONCURRENCY_CASE_COUNT,
        "observed_cases_sha256": recomputed["observed_cases_sha256"],
        "raw_samples_revalidated": True,
        "verifier_implementation": file_binding(Path(__file__).resolve()),
    }
    return add_self_hash(evidence, "evidence_sha256")


def binding_with_internal_hash(path: Path, field_names: Iterable[str]) -> dict[str, Any]:
    value = load_json(path, path.name)
    field = verify_internal_hash(value, field_names, path.name)
    return file_binding(path) | {field: value[field]}


def generated_record_base(schema_version: str) -> dict[str, Any]:
    return {"schema_version": schema_version, "created_at": utc_now()}
