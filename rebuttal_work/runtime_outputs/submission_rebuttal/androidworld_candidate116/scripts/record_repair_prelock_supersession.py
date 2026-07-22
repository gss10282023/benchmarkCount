#!/usr/bin/env python3
"""Record a content-addressed, pre-call supersession without deleting evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from semantic_review_common import SemanticReviewError
from repair_pipeline_common import (
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    file_binding,
    load_json,
    repo_relative,
    resolve_repo_path,
    tree_record,
    utc_now,
    verify_file_binding,
    verify_internal_hash,
    write_json_create_once,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-selection", type=Path, required=True)
    parser.add_argument("--old-prelock", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=WORK_ROOT / "repair_generation" / "incidents" / "supersessions",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selection_path = args.old_selection.resolve()
    prelock_path = args.old_prelock.resolve()
    selection = load_json(selection_path, "superseded repair selection")
    prelock = load_json(prelock_path, "superseded repair prelock")
    if selection.get("schema_version") != "androidworld_checklist_repair_selection/v1":
        raise RepairPipelineError("supersession input selection is not the affected /v1 schema")
    verify_internal_hash(selection, ("selection_sha256",), "superseded selection")
    if prelock.get("schema_version") != "androidworld_checklist_repair_prelock/v1":
        raise RepairPipelineError("supersession input prelock schema is invalid")
    verify_internal_hash(prelock, ("prelock_sha256",), "superseded prelock")
    bound_selection = prelock.get("audit_selection") or {}
    if (
        verify_file_binding(bound_selection, "superseded selection binding", inside_candidate=True)
        != selection_path
        or bound_selection.get("selection_sha256") != selection.get("selection_sha256")
    ):
        raise RepairPipelineError("old prelock does not bind the supplied old selection")
    config_path = verify_file_binding(prelock.get("repair_config"), "old repair config", inside_candidate=True)
    config = load_json(config_path, "old repair config")
    verify_internal_hash(config, ("config_sha256",), "old repair config")
    output_root = resolve_repo_path(config.get("output_root"), inside_candidate=True)
    if output_root.exists():
        files = [path for path in output_root.rglob("*") if path.is_file()]
        if files:
            raise RepairPipelineError(
                "old repair output contains files; cannot attest superseded-before-first-model-call"
            )
        raise RepairPipelineError(
            "old repair output directory exists; remove no evidence and classify via a run incident instead"
        )
    snapshot_path = verify_file_binding(
        prelock.get("repair_toolchain_snapshot"), "old repair snapshot", inside_candidate=True
    )
    snapshot = load_json(snapshot_path, "old repair snapshot")
    verify_internal_hash(snapshot, ("snapshot_sha256",), "old repair snapshot")
    packet_root = resolve_repo_path(config.get("packet_set_root"), inside_candidate=True)
    if not packet_root.is_dir():
        raise RepairPipelineError("old prelocked packet set is missing")
    incident = {
        "schema_version": "androidworld_checklist_repair_supersession_incident/v1",
        "created_at": utc_now(),
        "status": "aborted_before_first_repair_model_call",
        "reason_code": "repair_issue_context_loss",
        "reason": (
            "repair selection /v1 normalized issues discarded automatic field/detail and manual "
            "evidence, and did not guarantee per-case unique stable issue ids"
        ),
        "promotion_forbidden": True,
        "repair_output_eligible": False,
        "model_calls_started": False,
        "model_output_root_absent": True,
        "superseded_selection": file_binding(selection_path)
        | {"selection_sha256": selection["selection_sha256"]},
        "superseded_prelock": file_binding(prelock_path)
        | {"prelock_sha256": prelock["prelock_sha256"]},
        "superseded_config": file_binding(config_path)
        | {"config_sha256": config["config_sha256"]},
        "superseded_toolchain_snapshot": file_binding(snapshot_path)
        | {"snapshot_sha256": snapshot["snapshot_sha256"]},
        "superseded_packet_set": tree_record(packet_root),
        "required_replacement": {
            "selection_schema": "androidworld_checklist_repair_selection/v2",
            "issue_schema": "androidworld_checklist_repair_issue/v2",
            "new_content_addressed_packets": True,
            "new_generation_prelock": True,
        },
        "preservation_policy": "all superseded files remain immutable historical evidence",
    }
    incident = add_self_hash(incident, "incident_sha256")
    if args.dry_run:
        print(json.dumps({"status": "dry_run_pass", "incident": incident}, indent=2))
        return 0
    output_root = args.output_root.resolve()
    try:
        output_root.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("supersession output root must be inside candidate116") from exc
    output_path = output_root / f"{incident['incident_sha256']}.json"
    output_root.mkdir(parents=True, exist_ok=True)
    write_json_create_once(output_path, incident)
    print(
        json.dumps(
            {
                "status": incident["status"],
                "incident": file_binding(output_path)
                | {"incident_sha256": incident["incident_sha256"]},
                "promotion_forbidden": True,
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
