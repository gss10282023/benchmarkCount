#!/usr/bin/env python3
"""Finalize the per-VPS SHA-256 lock for official WebArena site data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time


OFFICIAL_COMMIT = "6473f72db5dcefc97b5725b59e734504edc28a21"
EXPECTED_SIZES = {
    "nominatim_volumes.tar": 124_774_901_760,
    "osm_tile_server.tar": 41_280_327_680,
    "osrm_routing.tar": 21_278_935_040,
    "wikipedia_en_all_maxi_2022-05.zim": 95_199_730_590,
}
MAP_FILES = frozenset(
    {"nominatim_volumes.tar", "osm_tile_server.tar", "osrm_routing.tar"}
)


class DataLockError(RuntimeError):
    """The data download or precomputed hash set is incomplete or invalid."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--map-hashes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wait-seconds", type=int, default=0)
    parser.add_argument("--poll-seconds", type=int, default=10)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_map_hashes(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise DataLockError("map hash file is missing or a symlink")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        pieces = line.split()
        if len(pieces) != 2:
            raise DataLockError("map hash file has a malformed line")
        digest, filename = pieces
        filename = filename.removeprefix("*")
        if filename in values or filename not in MAP_FILES:
            raise DataLockError("map hash file has duplicate or unexpected entries")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise DataLockError("map hash file has an invalid SHA-256")
        values[filename] = digest
    if set(values) != MAP_FILES:
        raise DataLockError("map hash file does not cover all three archives")
    return values


def _downloads_complete(data_root: Path) -> bool:
    for filename, size in EXPECTED_SIZES.items():
        path = data_root / filename
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            return False
        if Path(f"{path}.aria2").exists():
            return False
    return True


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run(args: argparse.Namespace) -> dict:
    if not args.data_root.is_dir() or args.data_root.is_symlink():
        raise DataLockError("data root is missing or a symlink")
    deadline = time.monotonic() + max(0, int(args.wait_seconds))
    while not _downloads_complete(args.data_root):
        if time.monotonic() >= deadline:
            raise DataLockError("official site data downloads are incomplete")
        time.sleep(max(1, int(args.poll_seconds)))

    digests = _parse_map_hashes(args.map_hashes)
    wikipedia = "wikipedia_en_all_maxi_2022-05.zim"
    digests[wikipedia] = _sha256(args.data_root / wikipedia)
    assets = {
        filename: {
            "size_bytes": EXPECTED_SIZES[filename],
            "sha256": digests[filename],
        }
        for filename in sorted(EXPECTED_SIZES)
    }
    payload = {
        "schema_version": "webarena_verified_site_data_sha256/v1",
        "official_commit": OFFICIAL_COMMIT,
        "hash_algorithm": "sha256",
        "assets": assets,
    }
    _atomic_json(args.output, payload)
    return payload


def main() -> int:
    args = _parser().parse_args()
    try:
        payload = run(args)
    except Exception as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "status": "pass",
                "output": str(args.output),
                "asset_count": len(payload["assets"]),
                "output_sha256": _sha256(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
