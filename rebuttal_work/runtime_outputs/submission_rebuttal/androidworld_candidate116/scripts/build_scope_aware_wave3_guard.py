#!/usr/bin/env python3
"""Build a non-destructive, scope-aware wave_003 drift incident and guard.

The original hard-coded generation guard remains authoritative evidence and is
never rewritten.  This second guard narrows the protected scope to the data
roots, official100, packet inputs, and immutable v3 snapshot actually used by
wave_003.  Live ``neurips_ed_track_minimal`` paths outside the v3 bindings may
drift only when explicitly declared; that drift is recorded, never hidden.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import SemanticReviewError

from repair_pipeline_common import (
    RepairPipelineError,
    add_self_hash,
    file_binding,
    load_json,
    load_source_prelock,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    utc_now,
    verify_file_binding,
    verify_internal_hash,
    write_json_atomic,
)


PROTECTED_ROOTS = (
    "results",
    "paper_result_packages",
    "paper_result_packages/androidworld_both_agents_scored_cases_official_full100",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pre-snapshot", type=Path, required=True)
    parser.add_argument("--post-snapshot", type=Path, required=True)
    parser.add_argument("--original-guard", type=Path, required=True)
    parser.add_argument("--source-prelock", type=Path, required=True)
    parser.add_argument(
        "--live-drift-path",
        action="append",
        default=[],
        help="Explicit repo-relative changed path under live neurips_ed_track_minimal; repeatable.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def parse_time(value: Any, label: str) -> datetime:
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise RepairPipelineError(f"{label} has invalid captured_at") from exc


def exact_snapshot_binding(path: Path, snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return file_binding(path) | {
        "captured_at": snapshot.get("captured_at"),
        "content_sha256": object_sha256(snapshot),
    }


def verify_v3_snapshot(source_prelock: Mapping[str, Any]) -> tuple[Path, dict[str, Any], set[Path]]:
    binding = source_prelock.get("toolchain_snapshot")
    if not isinstance(binding, Mapping):
        raise RepairPipelineError("source prelock has no v3 snapshot binding")
    manifest_path = resolve_repo_path(binding.get("path"), inside_candidate=True)
    if not manifest_path.is_file() or sha256_file(manifest_path) != binding.get("sha256"):
        raise RepairPipelineError("v3 snapshot manifest path/hash binding fails")
    if binding.get("size_bytes") is not None and manifest_path.stat().st_size != binding.get("size_bytes"):
        raise RepairPipelineError("v3 snapshot manifest explicit size binding fails")
    manifest = load_json(manifest_path, "v3 snapshot manifest")
    verify_internal_hash(manifest, ("snapshot_sha256",), "v3 snapshot manifest")
    if manifest.get("status") != "frozen" or manifest.get("file_count") != len(manifest.get("files") or []):
        raise RepairPipelineError("v3 snapshot manifest status/count is invalid")
    if binding.get("snapshot_sha256") != manifest.get("snapshot_sha256"):
        raise RepairPipelineError("v3 snapshot internal hash differs from source prelock")
    for index, item in enumerate(manifest.get("files") or []):
        verify_file_binding(item, f"v3 snapshot file {index}", inside_candidate=True)
    live_origins: set[Path] = set()
    for index, item in enumerate(manifest.get("live_origins_at_snapshot") or []):
        if not isinstance(item, Mapping):
            raise RepairPipelineError(f"v3 live origin {index} is not an object")
        snapshot_path = resolve_repo_path(item.get("snapshot_path"), inside_candidate=True)
        live_path = resolve_repo_path(item.get("live_path"), inside_candidate=False)
        if not snapshot_path.is_file() or not live_path.is_file():
            raise RepairPipelineError(f"v3 live origin {index} is missing")
        if sha256_file(snapshot_path) != item.get("snapshot_sha256"):
            raise RepairPipelineError(f"v3 snapshot origin bytes changed: {snapshot_path}")
        if sha256_file(live_path) != item.get("live_sha256_at_snapshot"):
            raise RepairPipelineError(f"v3-bound live origin drifted: {live_path}")
        live_origins.add(live_path)
    return manifest_path, manifest, live_origins


def verify_declared_drift(
    values: list[str],
    *,
    live_origins: set[Path],
    pre_time: datetime,
    post_time: datetime,
) -> list[dict[str, Any]]:
    if len(values) != len(set(values)):
        raise RepairPipelineError("duplicate --live-drift-path value")
    rows: list[dict[str, Any]] = []
    live_root = resolve_repo_path("neurips_ed_track_minimal")
    for raw in sorted(values):
        path = resolve_repo_path(raw, inside_candidate=False)
        try:
            path.relative_to(live_root)
        except ValueError as exc:
            raise RepairPipelineError(f"declared live drift is outside neurips_ed_track_minimal: {raw}") from exc
        if path in live_origins:
            raise RepairPipelineError(f"declared drift touches a v3-bound live origin: {raw}")
        if not path.is_file():
            raise RepairPipelineError(f"declared live drift path is not a current file: {raw}")
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=pre_time.tzinfo)
        if modified_at < pre_time or modified_at > post_time:
            raise RepairPipelineError(
                f"declared drift mtime is outside generation window: {raw} ({modified_at.isoformat()})"
            )
        rows.append(
            file_binding(path)
            | {
                "classification": "live_nonbinding_file_drift",
                "modified_at": modified_at.isoformat(),
                "bound_by_v3_snapshot": False,
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    for path in (args.pre_snapshot, args.post_snapshot, args.original_guard, args.source_prelock):
        if not path.resolve().is_file():
            raise RepairPipelineError(f"required evidence is missing: {path}")
    pre = load_json(args.pre_snapshot.resolve(), "wave3 pre snapshot")
    post = load_json(args.post_snapshot.resolve(), "wave3 post snapshot")
    original = load_json(args.original_guard.resolve(), "original wave3 guard")
    verify_internal_hash(original, ("guard_sha256",), "original wave3 guard")
    source_prelock = load_source_prelock(args.source_prelock.resolve())
    if original.get("generation_id") != "wave_003":
        raise RepairPipelineError("original guard is not for wave_003")
    if original.get("pre_snapshot", {}).get("sha256") != sha256_file(args.pre_snapshot.resolve()):
        raise RepairPipelineError("original guard does not bind the supplied pre snapshot")
    if original.get("post_snapshot", {}).get("sha256") != sha256_file(args.post_snapshot.resolve()):
        raise RepairPipelineError("original guard does not bind the supplied post snapshot")

    pre_roots = pre.get("roots") or {}
    post_roots = post.get("roots") or {}
    protected_equal: dict[str, bool] = {}
    for name in PROTECTED_ROOTS:
        protected_equal[name] = pre_roots.get(name) == post_roots.get(name)
    official_equal = pre.get("official100") == post.get("official100")
    if not all(protected_equal.values()) or not official_equal:
        raise RepairPipelineError(
            f"protected data changed: roots={protected_equal}, official100={official_equal}"
        )

    manifest_path, manifest, live_origins = verify_v3_snapshot(source_prelock)
    for row in source_prelock.get("packet_inputs") or []:
        verify_file_binding(row, f"packet {row.get('case_unit_id')}", inside_candidate=True)

    pre_time = parse_time(pre.get("captured_at"), "pre snapshot")
    post_time = parse_time(post.get("captured_at"), "post snapshot")
    if post_time < pre_time:
        raise RepairPipelineError("post snapshot predates pre snapshot")
    live_changed = pre_roots.get("neurips_ed_track_minimal") != post_roots.get("neurips_ed_track_minimal")
    if live_changed != bool(args.live_drift_path):
        raise RepairPipelineError(
            "live root aggregate drift and explicit --live-drift-path declarations disagree"
        )
    drift = verify_declared_drift(
        args.live_drift_path,
        live_origins=live_origins,
        pre_time=pre_time,
        post_time=post_time,
    )

    incident = {
        "schema_version": "androidworld_wave3_live_tool_drift_incident/v1",
        "created_at": utc_now(),
        "generation_id": "wave_003",
        "status": "transparent_nonbinding_live_drift" if live_changed else "no_live_drift",
        "original_guard": file_binding(args.original_guard.resolve())
        | {"guard_sha256": original["guard_sha256"], "status": original.get("status")},
        "pre_snapshot": exact_snapshot_binding(args.pre_snapshot.resolve(), pre),
        "post_snapshot": exact_snapshot_binding(args.post_snapshot.resolve(), post),
        "changed_paths": drift,
        "changed_path_count": len(drift),
        "attribution_scope": {
            "claim": "declared nonbinding live paths observed inside the pre/post window",
            "full_live_root_diff_exhaustively_reconstructable_from_aggregate_snapshots": False,
            "reason": "the legacy snapshots store aggregate tree hashes, not per-file before hashes",
        },
        "promotion_effect": "does_not_invalidate_wave3_only_if_scope_aware_guard_passes",
    }
    incident = add_self_hash(incident, "incident_sha256")
    guard = {
        "schema_version": "androidworld_candidate116_wave3_scope_aware_guard/v1",
        "created_at": utc_now(),
        "status": "pass",
        "generation_id": "wave_003",
        "policy": {
            "protected": [*PROTECTED_ROOTS, "official100", "packet_inputs", "v3_snapshot", "v3_live_origins"],
            "live_neurips_nonbinding_drift": "allowed_only_when_explicitly_incidented",
            "original_hardcoded_guard_may_remain_failed": True,
        },
        "original_guard": incident["original_guard"],
        "protected_root_equality": protected_equal,
        "official100_equal": official_equal,
        "packet_inputs_unchanged": True,
        "v3_snapshot": file_binding(manifest_path) | {"snapshot_sha256": manifest["snapshot_sha256"]},
        "v3_snapshot_files_unchanged": True,
        "v3_bound_live_origins_unchanged": True,
        "live_drift_incident_sha256": incident["incident_sha256"],
        "declared_live_drift_paths": [row["path"] for row in drift],
        "promotion_authorized_by_this_guard_alone": False,
    }
    guard = add_self_hash(guard, "scope_guard_sha256")

    if args.dry_run:
        print(json.dumps({"status": "dry_run_pass", "incident": incident, "guard": guard}, indent=2))
        return 0
    output_dir = args.output_dir.resolve()
    try:
        output_dir.relative_to(Path(__file__).resolve().parents[1])
    except ValueError as exc:
        raise RepairPipelineError("output directory must be inside candidate116") from exc
    incident_path = output_dir / "wave_003_live_tool_drift_incident.json"
    guard_path = output_dir / "wave_003_scope_aware_guard.json"
    if incident_path.exists() or guard_path.exists():
        raise RepairPipelineError("refusing to overwrite scope-aware guard evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(incident_path, incident)
    guard["live_drift_incident"] = file_binding(incident_path) | {
        "incident_sha256": incident["incident_sha256"]
    }
    guard = add_self_hash(guard, "scope_guard_sha256")
    write_json_atomic(guard_path, guard)
    print(
        json.dumps(
            {
                "status": "pass",
                "original_guard_status": original.get("status"),
                "incident": file_binding(incident_path) | {"incident_sha256": incident["incident_sha256"]},
                "scope_guard": file_binding(guard_path) | {"scope_guard_sha256": guard["scope_guard_sha256"]},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
