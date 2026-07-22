#!/usr/bin/env python3
"""Build the non-launchable WebArena-Verified 2,436-slot machine preview."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.orchestrator.webarena_verified_machine_preview import (
    build_machine_preview,
    write_machine_preview,
)


def main() -> int:
    index, acceptance = build_machine_preview()
    index_path, acceptance_path = write_machine_preview(index, acceptance)
    print(
        "wrote non-launchable 2,436-slot preview: "
        f"index={index_path} acceptance={acceptance_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
