#!/usr/bin/env python3
"""Entry point for WebArena-Verified monitoring and resumable full control."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.cli.webarena_full_control import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
