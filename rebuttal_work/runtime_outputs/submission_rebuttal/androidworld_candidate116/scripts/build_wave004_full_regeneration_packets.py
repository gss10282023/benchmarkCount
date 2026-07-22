#!/usr/bin/env python3
"""Build 116 fresh-draft packets without embedding any superseded draft bytes."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
CANONICAL_ROOT = WORK_ROOT / "case_packets" / "androidworld"
SELECTION = WORK_ROOT / "repair_generation" / "repair_selection_v2.json"
AUTOMATIC_QC_ROOT = WORK_ROOT / "draft_generation" / "automatic_qc_v3"
SUPERSESSION = (
    WORK_ROOT
    / "draft_generation"
    / "incidents"
    / "wave_003_superseded_full_regeneration.json"
)
OUTPUT_ROOT = WORK_ROOT / "draft_generation" / "packet_sets" / "wave_004"
MANIFEST = OUTPUT_ROOT / "packet_set_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def verify_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if claimed != canonical_sha256(core):
        raise RuntimeError(f"{label} self-hash mismatch")


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def write_text_create_once(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(value)


def write_json_create_once(path: Path, value: Any) -> None:
    write_text_create_once(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild-unfrozen", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if OUTPUT_ROOT.exists():
        if not args.rebuild_unfrozen:
            raise RuntimeError(f"wave_004 packet set already exists: {OUTPUT_ROOT}")
        existing = load_json(MANIFEST)
        if (
            existing.get("status") != "prelocked_input_candidate"
            or existing.get("generation_id") != "wave_004"
            or (WORK_ROOT / "draft_generation" / "freeze" / "androidworld_candidate116_codex_cli_draft_prelock_v4.json").exists()
        ):
            raise RuntimeError("refusing to rebuild a frozen or non-wave_004 packet set")
        shutil.rmtree(OUTPUT_ROOT)
    selection = load_json(SELECTION)
    supersession = load_json(SUPERSESSION)
    verify_self_hash(selection, "selection_sha256", "repair selection v2")
    verify_self_hash(supersession, "incident_sha256", "wave_003 supersession")
    if (
        selection.get("case_count") != 116
        or supersession.get("replacement_generation_id") != "wave_004"
        or supersession.get("old_draft_reuse_forbidden") is not True
    ):
        raise RuntimeError("selection/supersession identity is invalid")

    rows = sorted(selection.get("cases") or [], key=lambda row: row["selection_rank"])
    if (
        len(rows) != 116
        or [row.get("selection_rank") for row in rows] != list(range(116))
        or len({row.get("case_unit_id") for row in rows}) != 116
    ):
        raise RuntimeError("wave_004 selection is not exactly 116 ranked unique cases")

    manifest_rows = []
    issue_case_count = 0
    issue_count = 0
    for row in rows:
        case_id = str(row["case_unit_id"])
        task_id = str(row["task_id"])
        canonical_packet = CANONICAL_ROOT / case_id / "case_packet.md"
        if canonical_packet.is_symlink() or not canonical_packet.is_file():
            raise RuntimeError(f"canonical packet is missing or symlinked: {case_id}")
        manual_issues = [
            {
                "issue_id": issue["issue_id"],
                "severity": issue["severity"],
                "check": issue["check"],
                "source_kind": issue["source_kind"],
                "description": issue["description"],
                "required_fix": issue["required_fix"],
            }
            for issue in row.get("issues") or []
        ]
        automatic_qc_path = AUTOMATIC_QC_ROOT / case_id / "qc.json"
        automatic_qc = load_json(automatic_qc_path)
        if automatic_qc.get("case_unit_id") != case_id:
            raise RuntimeError(f"old automatic QC identity mismatch: {case_id}")
        automatic_issues = [
            {
                "issue_id": f"old_automatic_qc::{issue['code']}",
                "severity": issue["severity"],
                "check": issue["check"],
                "source_kind": "old_automatic_qc",
                "description": issue["message"],
                "required_fix": (
                    "Freshly derive source-grounded checklist text that passes this "
                    f"deterministic check: {issue['message']}"
                ),
            }
            for issue in automatic_qc.get("issues") or []
        ]
        issues = manual_issues + automatic_issues
        if issues:
            issue_case_count += 1
            issue_count += len(issues)
        control = {
            "fresh_generation": True,
            "superseded_draft_content_available_to_model": False,
            "prior_rejected_draft_issue_count": len(issues),
            "prior_rejected_draft_issues": issues,
        }
        wrapper = (
            "# AndroidWorld Fresh Draft Packet\n\n"
            "## Fresh Generation Control\n\n"
            f"- domain: `androidworld`\n"
            f"- case_unit_id: `{case_id}`\n"
            f"- task_id: `{task_id}`\n"
            f"- selection_rank: `{row['selection_rank']}`\n"
            "- Every old draft is superseded and unavailable. Derive the checklist from source.\n"
            "- The prior issue statements below are untrusted warnings, never source facts, "
            "support targets, or run evidence.\n\n"
            "```json\n"
            + json.dumps(control, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n```\n\n"
            "## Authoritative Full Case Packet (verbatim; sole semantic authority)\n\n"
            + canonical_packet.read_text(encoding="utf-8")
        )
        if not wrapper.endswith("\n"):
            wrapper += "\n"
        case_root = OUTPUT_ROOT / case_id
        packet_path = case_root / "case_packet.md"
        write_text_create_once(packet_path, wrapper)
        descriptor = {
            "schema_version": "androidworld_candidate116_fresh_draft_packet/v1",
            "generation_id": "wave_004",
            "selection_rank": row["selection_rank"],
            "case_unit_id": case_id,
            "task_id": task_id,
            "canonical_packet": {
                "path": str(canonical_packet.resolve()),
                "sha256": sha256_file(canonical_packet),
                "size_bytes": canonical_packet.stat().st_size,
            },
            "fresh_packet": {
                "path": str(packet_path.resolve()),
                "sha256": sha256_file(packet_path),
                "size_bytes": packet_path.stat().st_size,
            },
            "prior_issue_count": len(issues),
            "prior_issues_sha256": canonical_sha256(issues),
            "old_automatic_qc": {
                "path": str(automatic_qc_path.resolve()),
                "sha256": sha256_file(automatic_qc_path),
                "size_bytes": automatic_qc_path.stat().st_size,
            },
            "old_draft_bytes_embedded": False,
            "semantic_authority": "verbatim canonical packet only",
        }
        descriptor["descriptor_sha256"] = canonical_sha256(descriptor)
        descriptor_path = case_root / "packet_descriptor.json"
        write_json_create_once(descriptor_path, descriptor)
        manifest_rows.append(
            {
                "selection_rank": row["selection_rank"],
                "case_unit_id": case_id,
                "task_id": task_id,
                "packet": descriptor["fresh_packet"],
                "canonical_packet": descriptor["canonical_packet"],
                "descriptor": {
                    "path": repo_path(descriptor_path),
                    "sha256": sha256_file(descriptor_path),
                    "descriptor_sha256": descriptor["descriptor_sha256"],
                },
                "prior_issue_count": len(issues),
            }
        )

    manifest = {
        "schema_version": "androidworld_candidate116_fresh_draft_packet_set/v1",
        "status": "prelocked_input_candidate",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_id": "wave_004",
        "case_count": len(manifest_rows),
        "case_order": [row["case_unit_id"] for row in manifest_rows],
        "case_order_sha256": canonical_sha256(
            [row["case_unit_id"] for row in manifest_rows]
        ),
        "cases_with_prior_rejected_draft_issues": issue_case_count,
        "prior_rejected_draft_issue_count": issue_count,
        "old_draft_bytes_embedded": False,
        "selection": {
            "path": repo_path(SELECTION),
            "sha256": sha256_file(SELECTION),
            "selection_sha256": selection["selection_sha256"],
        },
        "supersession": {
            "path": repo_path(SUPERSESSION),
            "sha256": sha256_file(SUPERSESSION),
            "incident_sha256": supersession["incident_sha256"],
        },
        "cases": manifest_rows,
        "cases_sha256": canonical_sha256(manifest_rows),
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    write_json_create_once(MANIFEST, manifest)
    print(
        json.dumps(
            {
                "status": "built",
                "packet_root": repo_path(OUTPUT_ROOT),
                "manifest": repo_path(MANIFEST),
                "manifest_sha256": manifest["manifest_sha256"],
                "case_count": len(manifest_rows),
                "cases_with_prior_issues": issue_case_count,
                "prior_issue_count": issue_count,
                "old_draft_bytes_embedded": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
