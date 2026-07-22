"""Seal a MiniWoB worker output tree on the benchmark host before retrieval."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat

from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.hashing import sha256_file, sha256_object


RECEIPT_NAME = "remote_tree_receipt.json"


def inventory(root: Path) -> list[dict[str, object]]:
    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("output root is not a directory")
    entries: list[dict[str, object]] = []
    for path in sorted(resolved.rglob("*")):
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"symlink is forbidden in worker output: {path}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"non-regular or hard-linked worker output: {path}")
        relative = path.relative_to(resolved).as_posix()
        if relative == RECEIPT_NAME:
            continue
        entries.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "size_bytes": info.st_size,
            }
        )
    return entries


def seal(root: Path, *, job_id: str) -> Path:
    entries = inventory(root)
    receipt = {
        "schema_version": "miniwob_remote_tree_receipt/v1",
        "status": "sealed",
        "job_id": job_id,
        "created_at": utc_now_iso(),
        "file_count": len(entries),
        "total_bytes": sum(int(entry["size_bytes"]) for entry in entries),
        "inventory_sha256": sha256_object(entries),
        "inventory": entries,
    }
    return write_json(root / RECEIPT_NAME, receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    output = seal(Path(args.output_dir), job_id=args.job_id)
    print(json.dumps({"status": "sealed", "receipt": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
