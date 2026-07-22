#!/usr/bin/env python3
"""Remove one oversized derived section while preserving official packet sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


OMITTED_PATH = "derived/canonical_task_semantics.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_bytes = args.source.read_bytes()
    source = source_bytes.decode("utf-8")
    heading = f"### `{OMITTED_PATH}`\n"
    start = source.find(heading)
    if start < 0:
        raise SystemExit(f"missing section heading: {heading.strip()}")
    next_heading = re.search(r"(?m)^### `[^`]+`\n", source[start + len(heading) :])
    raw_provenance = source.find("\n## Raw Source Provenance", start + len(heading))
    candidates = [
        value
        for value in (
            start + len(heading) + next_heading.start() if next_heading else -1,
            raw_provenance,
        )
        if value >= 0
    ]
    if not candidates:
        raise SystemExit("could not locate the end of the oversized derived section")
    end = min(candidates)
    replacement = (
        f"### `{OMITTED_PATH}` (body omitted from model-visible compact packet)\n\n"
        "The complete outcome-blind file remains byte-for-byte present under `raw_case/` "
        "for provenance and validator resolution, but its very large derived body is not "
        "part of this model input. It is non-authoritative relative to the embedded official "
        "task, evaluator, and runner sources and must not be cited by the draft.\n\n"
    )
    compact = source[:start] + replacement + source[end:]
    compact_bytes = compact.encode("utf-8")
    if len(compact_bytes) >= 900_000:
        raise SystemExit(f"compact packet remains too large: {len(compact_bytes)} bytes")
    if "## Source Inventory" not in compact or "official/install/android_world/suite_utils.py" not in compact:
        raise SystemExit("compact packet lost required official inventory/source material")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_bytes(compact_bytes)
    receipt = {
        "schema_version": "androidworld_model_visible_packet_compaction/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Codex CLI hard input limit of 1048576 characters",
        "source_path": str(args.source.resolve()),
        "source_sha256": sha256_bytes(source_bytes),
        "source_size_bytes": len(source_bytes),
        "destination_path": str(args.destination.resolve()),
        "destination_sha256": sha256_bytes(compact_bytes),
        "destination_size_bytes": len(compact_bytes),
        "omitted_model_visible_section": OMITTED_PATH,
        "raw_case_tree_preserved": True,
        "official_source_sections_preserved": True,
        "source_inventory_preserved": True,
        "outcomes_or_results_added": False,
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
