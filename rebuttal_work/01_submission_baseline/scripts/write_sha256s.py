#!/usr/bin/env python3
"""Write deterministic SHA256SUMS files for Step 1 deliverables."""

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


def included_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        if "snapshots" in relative.parts or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(directory).as_posix())


def write(directory: Path) -> None:
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in included_files(directory)]
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directories", nargs="+", type=Path)
    args = parser.parse_args()
    for directory in args.directories:
        write(directory.resolve())


if __name__ == "__main__":
    main()
