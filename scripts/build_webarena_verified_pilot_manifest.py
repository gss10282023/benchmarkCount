#!/usr/bin/env python3
"""Build or verify the frozen WebArena-Verified 8x3 pilot manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.orchestrator.webarena_verified_pilot import (
    DEFAULT_PILOT_MANIFEST,
    build_pilot_manifest,
    write_pilot_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_PILOT_MANIFEST))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build_pilot_manifest()
    output = ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    if args.check:
        if not output.is_file():
            print(f"missing pilot manifest: {output}")
            return 1
        observed = json.loads(output.read_text(encoding="utf-8"))
        if observed != expected:
            print(f"pilot manifest is stale: {output}")
            return 1
        print(f"PASS: frozen 8-case/24-slot pilot manifest is current: {output}")
        return 0
    written = write_pilot_manifest(expected, output_path=output)
    print(f"wrote {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
