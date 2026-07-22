#!/usr/bin/env python3
"""Use the NeurIPS batch runner with frozen compact AndroidWorld packets."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from neurips_ed_track_minimal.scripts import run_draft_batch as upstream


ADAPTER = Path(__file__).resolve().with_name("draft_case_checklist_compact_adapter.py")


def discover_compact_case_packets(case_packet_root: Path) -> list[upstream.CasePacketInfo]:
    case_packets = sorted(case_packet_root.glob("*/compact_case_packet.md"))
    if not case_packets:
        raise SystemExit(f"No compact_case_packet.md files found under {case_packet_root}")
    return [
        upstream.CasePacketInfo(path=path, size_bytes=path.stat().st_size)
        for path in case_packets
    ]


upstream.DRAFT_SCRIPT = ADAPTER
upstream.discover_case_packets = discover_compact_case_packets


if __name__ == "__main__":
    raise SystemExit(upstream.main())
