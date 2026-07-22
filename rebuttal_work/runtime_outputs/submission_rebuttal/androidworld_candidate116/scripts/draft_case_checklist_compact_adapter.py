#!/usr/bin/env python3
"""Run the NeurIPS checklist drafter on an unchanged compact AndroidWorld packet.

The upstream drafter expects three Markdown metadata bullets.  Candidate116 compact
packets carry the same identifiers in their frozen JSON ``identity`` object instead.
This adapter changes only local identifier extraction; the packet text supplied to
the model remains byte-for-byte identical to ``compact_case_packet.md``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from neurips_ed_track_minimal.scripts import draft_case_checklist as upstream


_UPSTREAM_EXTRACT = upstream.extract_case_metadata


def extract_case_metadata(packet_text: str) -> dict[str, str]:
    try:
        return _UPSTREAM_EXTRACT(packet_text)
    except upstream.DraftChecklistError:
        match = re.search(r"```json\s*(\{.*?\})\s*```", packet_text, flags=re.DOTALL)
        if not match:
            raise upstream.DraftChecklistError(
                "Compact packet has neither Markdown metadata bullets nor a fenced JSON payload"
            )
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise upstream.DraftChecklistError(f"Compact packet JSON is invalid: {exc}") from exc
        identity = payload.get("identity")
        if not isinstance(identity, dict):
            raise upstream.DraftChecklistError("Compact packet is missing the identity object")
        metadata = {
            "domain": str(identity.get("domain") or "").strip(),
            "case_unit_id": str(identity.get("case_unit_id") or "").strip(),
            "task_id": str(identity.get("task_id") or "").strip(),
        }
        missing = [key for key, value in metadata.items() if not value]
        if missing:
            raise upstream.DraftChecklistError(
                f"Compact packet identity is missing required fields: {', '.join(missing)}"
            )
        return metadata


upstream.extract_case_metadata = extract_case_metadata


if __name__ == "__main__":
    raise SystemExit(upstream.main())
