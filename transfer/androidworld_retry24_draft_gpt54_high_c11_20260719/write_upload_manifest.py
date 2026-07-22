#!/usr/bin/env python3
"""Write a stable SHA-256 manifest for the retry upload tree."""

from __future__ import annotations

import hashlib
from pathlib import Path


root = Path(__file__).resolve().parent
targets = [root / "CASE_IDS.txt", root / "INPUT_LOCK.json"]
targets.extend(sorted((root / "case_packets").rglob("*")))
lines: list[str] = []
for path in targets:
    if not path.is_file():
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
(root / "UPLOAD_SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"files={len(lines)}")
