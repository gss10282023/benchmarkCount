#!/usr/bin/env python3
"""Write a deterministic checksum inventory for Step 2 deliverables."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    files = []
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        files.append(path)
    files.sort(key=lambda path: path.relative_to(directory).as_posix())
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in files]
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
