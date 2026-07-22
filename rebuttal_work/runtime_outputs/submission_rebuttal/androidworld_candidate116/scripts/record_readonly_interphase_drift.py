#!/usr/bin/env python3
"""Record the observed v1-to-v2 read-only interphase drift without attribution."""

from __future__ import annotations

import argparse
import importlib.util
import json
import stat
import sys
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import SemanticReviewError
from repair_pipeline_common import (
    REPO_ROOT,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    file_binding,
    load_json,
    object_sha256,
    repo_relative,
    sha256_file,
    verify_file_binding,
    verify_internal_hash,
    write_json_create_once,
)


SCHEMA = "androidworld_checklist_repair_readonly_interphase_drift/v1"
CONTENT_FIELDS = (
    "path",
    "hash_algorithm",
    "content_tree_sha256",
    "recursive_entry_count_excluding_root",
    "recursive_entry_count_including_root",
    "file_count",
    "directory_count",
    "symlink_count",
    "other_entry_count",
    "total_file_bytes",
    "all_entries_uf_immutable",
    "unlocked_entry_count_including_root",
    "unlocked_entries",
)
EXPECTED_NAMESPACE = "namespaces/tau3-retail-remaining14-vps-20260716"
NONBINDING_LIVE_TOOL_ROOT = "neurips_ed_track_minimal"
PROTECTED_EQUAL_ROOTS = (
    "paper_result_packages",
    "paper_result_packages/androidworld_both_agents_scored_cases_official_full100",
)
SOURCE_V3_PRELOCK_SCHEMA = "androidworld_candidate116_codex_draft_prelock/v3"
SOURCE_V3_SNAPSHOT_SCHEMA = "androidworld_candidate116_draft_toolchain_snapshot/v1"
SCOPE_GUARD_SCHEMA = "androidworld_candidate116_wave3_scope_aware_guard/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-v1-snapshot", type=Path, required=True)
    parser.add_argument("--new-v2-snapshot", type=Path, required=True)
    parser.add_argument("--source-v3-prelock", type=Path, required=True)
    parser.add_argument("--scope-aware-guard", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=WORK_ROOT / "repair_generation/incidents/readonly_interphase_drift",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def content_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    if any(field not in row for field in CONTENT_FIELDS):
        raise RepairPipelineError("read-only root summary lacks a v1 content field")
    return {field: row[field] for field in CONTENT_FIELDS}


def inside_candidate(path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError(f"{label} must be inside candidate116") from exc
    return resolved


def load_bound_helper(new: Mapping[str, Any]) -> Any:
    helper_binding = new.get("snapshot_helper") or {}
    helper_path = verify_file_binding(
        helper_binding, "v2 read-only snapshot helper", inside_candidate=True
    )
    expected = (WORK_ROOT / "scripts/readonly_snapshot_helper.py").resolve()
    if helper_path != expected or helper_binding != file_binding(expected):
        raise RepairPipelineError("v2 snapshot helper is not the current bound dedicated helper")
    spec = importlib.util.spec_from_file_location(
        "candidate116_interphase_readonly_helper", helper_path
    )
    if spec is None or spec.loader is None:
        raise RepairPipelineError("cannot load the bound dedicated read-only helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("readonly_operation_snapshot", "readonly_snapshot_core"):
        if not callable(getattr(module, name, None)):
            raise RepairPipelineError(f"bound dedicated helper lacks {name}")
    return module


def current_live_origin_row(origin: Mapping[str, Any]) -> dict[str, Any]:
    live_raw = str(origin.get("live_path") or "")
    live_path = (REPO_ROOT / live_raw).resolve()
    try:
        live_path.relative_to((REPO_ROOT / NONBINDING_LIVE_TOOL_ROOT).resolve())
    except ValueError as exc:
        raise RepairPipelineError("source-v3 live origin escapes the nonbinding live tool root") from exc
    try:
        metadata = live_path.lstat()
    except FileNotFoundError:
        current_kind = "missing"
        current_sha256 = None
        current_size_bytes = None
    else:
        if stat.S_ISLNK(metadata.st_mode):
            current_kind = "symlink"
            current_sha256 = None
            current_size_bytes = metadata.st_size
        elif stat.S_ISREG(metadata.st_mode):
            current_kind = "regular_file"
            current_sha256 = sha256_file(live_path)
            current_size_bytes = metadata.st_size
        else:
            current_kind = "other"
            current_sha256 = None
            current_size_bytes = metadata.st_size
    snapshot_sha256 = origin.get("snapshot_sha256")
    return {
        "name": origin.get("name"),
        "live_path": live_raw,
        "snapshot_path": origin.get("snapshot_path"),
        "snapshot_sha256": snapshot_sha256,
        "live_sha256_at_snapshot": origin.get("live_sha256_at_snapshot"),
        "current_kind": current_kind,
        "current_size_bytes": current_size_bytes,
        "current_live_sha256": current_sha256,
        "byte_identical_to_frozen_snapshot_now": (
            current_kind == "regular_file" and current_sha256 == snapshot_sha256
        ),
    }


def verify_source_v3_freeze(
    source_prelock_path: Path, scope_guard_path: Path
) -> dict[str, Any]:
    source_prelock_path = inside_candidate(source_prelock_path, "source-v3 prelock")
    source = load_json(source_prelock_path, "source-v3 prelock")
    verify_internal_hash(source, ("prelock_sha256",), "source-v3 prelock")
    if (
        source.get("schema_version") != SOURCE_V3_PRELOCK_SCHEMA
        or source.get("status") != "frozen_before_first_model_call"
    ):
        raise RepairPipelineError("source-v3 prelock contract is invalid")

    snapshot_binding = source.get("toolchain_snapshot") or {}
    snapshot_raw = str(snapshot_binding.get("path") or "")
    snapshot_path = inside_candidate(REPO_ROOT / snapshot_raw, "source-v3 snapshot")
    if (
        not snapshot_path.is_file()
        or sha256_file(snapshot_path) != snapshot_binding.get("sha256")
    ):
        raise RepairPipelineError("source-v3 snapshot byte binding differs")
    snapshot = load_json(snapshot_path, "source-v3 snapshot")
    verify_internal_hash(snapshot, ("snapshot_sha256",), "source-v3 snapshot")
    files = snapshot.get("files") or []
    if (
        snapshot.get("schema_version") != SOURCE_V3_SNAPSHOT_SCHEMA
        or snapshot.get("status") != "frozen"
        or snapshot.get("snapshot_sha256") != snapshot_binding.get("snapshot_sha256")
        or snapshot.get("file_count") != len(files)
        or snapshot.get("file_count") != snapshot_binding.get("file_count")
        or snapshot.get("files_sha256") != object_sha256(files)
    ):
        raise RepairPipelineError("source-v3 exact snapshot manifest is invalid")
    snapshot_files = {row.get("path"): row for row in files if isinstance(row, Mapping)}
    if len(snapshot_files) != len(files):
        raise RepairPipelineError("source-v3 snapshot file paths are duplicated or invalid")
    for binding in files:
        verify_file_binding(binding, "source-v3 frozen file", inside_candidate=True)

    tool_bindings = source.get("tool_bindings") or {}
    frozen_execution_tools: dict[str, Any] = {}
    for role in ("drafter", "batch_runner"):
        binding = tool_bindings.get(role) or {}
        verify_file_binding(binding, f"source-v3 frozen {role}", inside_candidate=True)
        if snapshot_files.get(binding.get("path")) != binding:
            raise RepairPipelineError(f"source-v3 frozen {role} is absent from exact snapshot")
        frozen_execution_tools[role] = dict(binding)

    origins = snapshot.get("live_origins_at_snapshot") or []
    if not isinstance(origins, list) or not origins:
        raise RepairPipelineError("source-v3 snapshot lacks bound live-origin evidence")
    origin_names: set[str] = set()
    origin_live_paths: set[str] = set()
    for origin in origins:
        if not isinstance(origin, Mapping):
            raise RepairPipelineError("source-v3 live-origin evidence row is invalid")
        name = str(origin.get("name") or "")
        live_path = str(origin.get("live_path") or "")
        snapshot_file = snapshot_files.get(origin.get("snapshot_path"))
        if (
            not name
            or not live_path
            or name in origin_names
            or live_path in origin_live_paths
            or snapshot_file is None
            or origin.get("snapshot_sha256") != snapshot_file.get("sha256")
            or origin.get("live_sha256_at_snapshot") != snapshot_file.get("sha256")
            or origin.get("byte_identical") is not True
        ):
            raise RepairPipelineError("source-v3 live-origin evidence is inconsistent")
        if name in ("drafter", "batch_runner"):
            frozen = frozen_execution_tools[name]
            if (
                origin.get("snapshot_path") != frozen.get("path")
                or origin.get("snapshot_sha256") != frozen.get("sha256")
            ):
                raise RepairPipelineError(
                    f"source-v3 live-origin evidence differs for frozen {name}"
                )
        origin_names.add(name)
        origin_live_paths.add(live_path)
    if not {"drafter", "batch_runner"}.issubset(origin_names):
        raise RepairPipelineError("source-v3 live origins omit a frozen execution tool")
    origin_rows = [current_live_origin_row(origin) for origin in origins]
    changed_paths = sorted(
        row["live_path"]
        for row in origin_rows
        if row["byte_identical_to_frozen_snapshot_now"] is not True
    )

    scope_guard_path = inside_candidate(scope_guard_path, "scope-aware guard")
    scope = load_json(scope_guard_path, "scope-aware guard")
    verify_internal_hash(scope, ("scope_guard_sha256",), "scope-aware guard")
    current_snapshot_binding = file_binding(snapshot_path) | {
        "snapshot_sha256": snapshot["snapshot_sha256"]
    }
    if (
        scope.get("schema_version") != SCOPE_GUARD_SCHEMA
        or scope.get("status") != "pass"
        or scope.get("v3_snapshot") != current_snapshot_binding
        or scope.get("v3_snapshot_files_unchanged") is not True
        or scope.get("v3_bound_live_origins_unchanged") is not True
        or scope.get("packet_inputs_unchanged") is not True
        or scope.get("official100_equal") is not True
        or any(
            (scope.get("protected_root_equality") or {}).get(root) is not True
            for root in (*PROTECTED_EQUAL_ROOTS, "results")
        )
        or (scope.get("policy") or {}).get("live_neurips_nonbinding_drift")
        != "allowed_only_when_explicitly_incidented"
        or not {"v3_snapshot", "v3_live_origins"}.issubset(
            set((scope.get("policy") or {}).get("protected") or [])
        )
    ):
        raise RepairPipelineError("scope-aware guard does not bind the exact source-v3 freeze")

    return {
        "source_v3_prelock": file_binding(source_prelock_path)
        | {"prelock_sha256": source["prelock_sha256"]},
        "source_v3_exact_snapshot": current_snapshot_binding
        | {
            "file_count": snapshot["file_count"],
            "files_sha256": snapshot["files_sha256"],
        },
        "scope_aware_guard": file_binding(scope_guard_path)
        | {"scope_guard_sha256": scope["scope_guard_sha256"]},
        "frozen_execution_tools": frozen_execution_tools,
        "live_origin_comparison": {
            "scope": "source-v3 snapshot live_origins_at_snapshot",
            "exhaustive_for_full_neurips_tree": False,
            "nonexhaustive_reason": (
                "the invalidated v1 root stored a full-tree aggregate hash/counts but no "
                "per-entry content manifest; these rows exhaustively cover the source-v3 "
                "bound live origins, including the frozen drafter and batch runner"
            ),
            "rows": origin_rows,
            "rows_sha256": object_sha256(origin_rows),
            "changed_paths": changed_paths,
            "changed_paths_sha256": object_sha256(changed_paths),
        },
        "execution_independence_policy": (
            "repair generation consumes the byte-bound candidate source-v3 drafter and batch "
            "runner from the exact frozen snapshot; current live neurips bytes are recorded "
            "but are not execution inputs"
        ),
    }


def build_incident(
    old_path: Path,
    new_path: Path,
    source_prelock_path: Path,
    scope_guard_path: Path,
) -> dict[str, Any]:
    old = load_json(old_path, "old v1 repair read-only snapshot")
    new = load_json(new_path, "new v2 repair read-only snapshot")
    verify_internal_hash(old, ("snapshot_sha256",), "old v1 read-only snapshot")
    verify_internal_hash(new, ("snapshot_sha256",), "new v2 read-only snapshot")
    if old.get("schema_version") != "androidworld_checklist_repair_readonly_snapshot/v1":
        raise RepairPipelineError("old snapshot is not the invalidated v1 schema")
    if new.get("schema_version") != "androidworld_checklist_repair_readonly_snapshot/v2":
        raise RepairPipelineError("new snapshot is not the replacement v2 schema")
    old_readonly = old.get("readonly_snapshot") or {}
    new_readonly = new.get("readonly_snapshot") or {}
    old_roots = old_readonly.get("roots") or {}
    new_roots = new_readonly.get("roots") or {}
    if set(old_roots) != set(new_roots):
        raise RepairPipelineError("v1/v2 read-only root sets differ")
    projected_old = {name: content_projection(row) for name, row in old_roots.items()}
    projected_new = {name: content_projection(row) for name, row in new_roots.items()}
    equality = {name: projected_old[name] == projected_new[name] for name in old_roots}
    required_equal = set(PROTECTED_EQUAL_ROOTS)
    if any(equality.get(name) is not True for name in required_equal):
        raise RepairPipelineError("unexpected protected interphase content drift")
    if equality.get("results") is not False:
        raise RepairPipelineError("expected results interphase drift is absent")
    old_official = old_readonly.get("official100") or {}
    new_official = new_readonly.get("official100") or {}
    if any(new_official.get(key) != value for key, value in old_official.items()):
        raise RepairPipelineError("official100 selector changed across the interphase")
    helper = load_bound_helper(new)
    current_readonly = helper.readonly_operation_snapshot(
        phase=str(new_readonly.get("phase") or new.get("phase") or "interphase_recheck"),
        repo_root=REPO_ROOT,
        work_root=WORK_ROOT,
    )
    captured_core = helper.readonly_snapshot_core(new_readonly)
    current_core = helper.readonly_snapshot_core(current_readonly)
    if current_core != captured_core:
        raise RepairPipelineError(
            "read-only endpoint changed after v2 capture and before incident recording"
        )
    current_nonbinding = current_readonly["roots"][NONBINDING_LIVE_TOOL_ROOT]
    if content_projection(current_nonbinding) != projected_new[NONBINDING_LIVE_TOOL_ROOT]:
        raise RepairPipelineError(
            "nonbinding live tool root changed after v2 capture and before incident recording"
        )
    source_v3_freeze = verify_source_v3_freeze(source_prelock_path, scope_guard_path)
    old_results = projected_old["results"]
    new_results = projected_new["results"]
    new_unlocked = sorted(
        set(new_results["unlocked_entries"]) - set(old_results["unlocked_entries"])
    )
    if not new_unlocked or any(
        path != EXPECTED_NAMESPACE and not path.startswith(EXPECTED_NAMESPACE + "/")
        for path in new_unlocked
    ):
        raise RepairPipelineError("results drift is not isolated to the identified namespace")
    deltas = {
        field: new_results[field] - old_results[field]
        for field in (
            "recursive_entry_count_excluding_root",
            "recursive_entry_count_including_root",
            "file_count",
            "directory_count",
            "symlink_count",
            "other_entry_count",
            "total_file_bytes",
            "unlocked_entry_count_including_root",
        )
    }
    incident = {
        "schema_version": SCHEMA,
        "status": "recorded_interphase_drift_before_repair_prelock",
        "promotion_forbidden_for_v1_baseline": True,
        "repair_model_calls_started": False,
        "repair_prelock_created": False,
        "repair_write_scope": repo_relative(WORK_ROOT),
        "old_v1_snapshot": file_binding(old_path)
        | {"snapshot_sha256": old["snapshot_sha256"]},
        "new_v2_snapshot": file_binding(new_path)
        | {"snapshot_sha256": new["snapshot_sha256"]},
        "root_content_equality": equality,
        "old_root_summaries": projected_old,
        "new_root_summaries": projected_new,
        "results_deltas": deltas,
        "identified_namespace_evidence": {
            "namespace": EXPECTED_NAMESPACE,
            "new_unlocked_entry_count": len(new_unlocked),
            "new_unlocked_entries_sha256": object_sha256(new_unlocked),
            "all_new_unlocked_entries_under_namespace": True,
        },
        "nonbinding_live_tool_root": {
            "path": NONBINDING_LIVE_TOOL_ROOT,
            "content_equal_to_invalidated_v1": equality[NONBINDING_LIVE_TOOL_ROOT],
            "old_root_summary": projected_old[NONBINDING_LIVE_TOOL_ROOT],
            "new_root_summary": projected_new[NONBINDING_LIVE_TOOL_ROOT],
            "current_recomputed_root_summary": content_projection(current_nonbinding),
            "current_recomputed_matches_new_v2_snapshot": True,
            "current_full_readonly_endpoint_matches_new_v2_snapshot": True,
            "source_v3_freeze": source_v3_freeze,
            "attribution": (
                "unknown; observed namespace/path/bytes are evidence, not actor or cause; "
                "this recorder writes only its candidate116 incident artifact"
            ),
            "binding_policy": (
                "recorded but nonbinding because the repair runner uses the exact candidate "
                "source-v3 frozen drafter/batch-runner bytes, not live neurips_ed_track_minimal"
            ),
        },
        "paper_result_packages_equal": equality["paper_result_packages"],
        "submitted_official100_package_equal": equality[
            "paper_result_packages/androidworld_both_agents_scored_cases_official_full100"
        ],
        "official100_selector_equal": True,
        "attribution": "not_attributed; namespace location is evidence, not actor or cause",
        "deletion_performed": False,
        "baseline_policy": (
            "the v1 snapshot remains invalidated historical evidence; the current v2 snapshot is "
            "the sole repair-phase pre baseline and must equal runner preflight/post endpoints"
        ),
    }
    return add_self_hash(incident, "incident_sha256")


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    output_root.relative_to(WORK_ROOT.resolve())
    incident = build_incident(
        args.old_v1_snapshot.resolve(),
        args.new_v2_snapshot.resolve(),
        args.source_v3_prelock.resolve(),
        args.scope_aware_guard.resolve(),
    )
    output = output_root / f"{incident['incident_sha256']}.json"
    if args.dry_run:
        print(json.dumps({"status": "dry_run_pass", "incident": incident}, indent=2))
        return 0
    write_json_create_once(output, incident)
    print(
        json.dumps(
            {
                "status": incident["status"],
                "incident": file_binding(output)
                | {"incident_sha256": incident["incident_sha256"]},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SemanticReviewError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
