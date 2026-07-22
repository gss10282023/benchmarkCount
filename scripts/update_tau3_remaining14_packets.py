#!/usr/bin/env python3
"""Refresh the 14 remaining tau3 packets with pinned evaluator and artifact sources."""

from __future__ import annotations

import json
from pathlib import Path

from evidence_system.contracts.case_packets import (
    _materialize_tau3_drafting_sources,
    _raw_case_manifest,
    render_case_packet,
)
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path


CASE_IDS = ("104", "85", "88", "42", "44", "55", "63", "43", "96", "4", "48", "110", "9", "24")
PACKET_ROOT = Path("experiments/case_packets/tau3_retail")


def main() -> int:
    updated: list[dict[str, str]] = []
    for case_id in CASE_IDS:
        case_dir = resolve_repo_path(PACKET_ROOT / case_id)
        raw_case_dir = case_dir / "raw_case"
        manifest_path = case_dir / "raw_case_manifest.json"
        packet_path = case_dir / "case_packet.md"
        if not raw_case_dir.is_dir() or not manifest_path.is_file() or not packet_path.is_file():
            raise RuntimeError(f"incomplete existing packet for tau3 case {case_id}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("domain") != "tau3_retail" or str(manifest.get("task_id")) != case_id:
            raise RuntimeError(f"packet identity mismatch for tau3 case {case_id}")

        before_packet_sha256 = sha256_file(packet_path)
        before_manifest_sha256 = sha256_file(manifest_path)
        source_refs = [str(value) for value in manifest.get("source_refs") or []]
        file_sources = {
            str(key): str(value)
            for key, value in (manifest.get("file_sources") or {}).items()
        }
        official_files = [str(value) for value in manifest.get("official_files") or []]
        derived_files = [str(value) for value in manifest.get("derived_files") or []]
        packet_files = [str(value) for value in manifest.get("packet_files") or []]

        _materialize_tau3_drafting_sources(
            raw_case_dir,
            file_sources=file_sources,
            source_refs=source_refs,
            official_files=official_files,
            derived_files=derived_files,
            packet_files=packet_files,
        )
        refreshed_manifest = _raw_case_manifest(
            domain="tau3_retail",
            case_unit_id=case_id,
            task_id=case_id,
            raw_case_dir=raw_case_dir,
            source_refs=source_refs,
            file_sources=file_sources,
            official_files=official_files,
            derived_files=derived_files,
            packet_files=packet_files,
        )
        manifest_path.write_text(
            json.dumps(refreshed_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        packet_path.write_text(
            render_case_packet(
                domain="tau3_retail",
                case_unit_id=case_id,
                task_id=case_id,
                raw_case_dir=raw_case_dir,
                raw_case_manifest=refreshed_manifest,
            ),
            encoding="utf-8",
        )
        updated.append(
            {
                "case_id": case_id,
                "before_packet_sha256": before_packet_sha256,
                "after_packet_sha256": sha256_file(packet_path),
                "before_manifest_sha256": before_manifest_sha256,
                "after_manifest_sha256": sha256_file(manifest_path),
            }
        )

    print(json.dumps({"updated_count": len(updated), "updated": updated}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
