#!/usr/bin/env python3
"""Fetch and lock the released AppWorld evaluator runtime used by these runs.

The retained AppWorld records identify code version ``0.2.0.dev0:a072b7a``.
This script downloads only evaluator-semantic source files from the corresponding
full official GitHub commit, verifies every pinned SHA-256, and writes a
deterministic source manifest.  It never opens benchmark run outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT
    / "experiments"
    / "appworld_evaluator_runtime_0.2.0.dev0_a072b7a_v2_semantic_closure"
)
COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
CODE_VERSION = "0.2.0.dev0:a072b7a"
BASE_URL = f"https://raw.githubusercontent.com/StonyBrookNLP/appworld/{COMMIT}/"
FILES = {
    "src/appworld/apps/lib/models/orm.py": (
        "df959a70b1cb39acd0f40a8fbec103f88f4b3481532d475cd079a551eb43abb9"
    ),
    "src/appworld/collections/models.py": (
        "8b2fac59d77c887ab08fe4092ec0811952d051bd56551dc239332c556df136e4"
    ),
    "src/appworld/common/collections.py": (
        "a35aa3ef4af05f1fc7a72387d2480a4f31043ebfad6dbbc6003b94d52b53e84a"
    ),
    "src/appworld/common/constants.py": (
        "776a1c2a97e8f3d7cbda00523be3fdf38ed6165d61ac729a82290a843524138d"
    ),
    "src/appworld/common/datetime.py": (
        "3edd3cdf00c3437da7cd57e397e1d4047cc6383f090c1dc50127e289fa647e5c"
    ),
    "src/appworld/common/evaluation.py": (
        "6edb5d01459427bc6f7f1ab427349009ee20a6e0895e8036fdbaad394db1061a"
    ),
    "src/appworld/common/errors.py": (
        "5b6469f2e487c6d1f040f1e48b66bdf05c875eeeb10736d6fd11387c3581702f"
    ),
    "src/appworld/common/finders.py": (
        "68d7fa9b55ad3c4ddb93ea6274ee3e4cef9f8b6df50f8cd83cfedb7cca034023"
    ),
    "src/appworld/common/naming.py": (
        "473345557003161f5708db9e50cbb198681e74eb3b3c822566ada0a083314327"
    ),
    "src/appworld/common/types.py": (
        "43f76d0b104bf49f979dd4490e3acc847dc8ef4f11687043050da8c88d28054b"
    ),
    "src/appworld/common/utils.py": (
        "e79ff266e466e6c688fa8e832ba338798173c44c6cef2324a3ab54040e508be5"
    ),
    "src/appworld/evaluator.py": (
        "bde9deb3b1e6ac0fa9819013729c0e817a97c90f579108fa032a90bba0ca51cb"
    ),
}


class FetchError(RuntimeError):
    """Raised when the official source snapshot cannot be verified."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_manifest_entries(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for relative, expected_sha256 in sorted(FILES.items()):
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.is_symlink() or not path.is_file():
            raise FetchError(f"missing official runtime source: {relative}")
        actual_sha256 = sha256_file(path)
        if actual_sha256 != expected_sha256:
            raise FetchError(
                f"official runtime SHA-256 drift for {relative}: "
                f"{actual_sha256} != {expected_sha256}"
            )
        entries.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": actual_sha256,
                "source_url": BASE_URL + relative,
            }
        )
    return entries


def validate(root: Path) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise FetchError(f"runtime source root is missing: {root}")
    manifest_path = root / "SOURCE_MANIFEST.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise FetchError("runtime source manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = expected_manifest_entries(root)
    expected = {
        "schema_version": "appworld_evaluator_runtime_source_lock.v1",
        "repository": "https://github.com/StonyBrookNLP/appworld",
        "commit": COMMIT,
        "code_version": CODE_VERSION,
        "file_count": len(entries),
        "files": entries,
        "files_sha256": sha256_bytes(canonical_json_bytes(entries)),
    }
    if manifest != expected:
        raise FetchError("runtime source manifest content differs from pinned sources")
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    expected_files = {"SOURCE_MANIFEST.json", *FILES}
    if actual_files != expected_files:
        raise FetchError(
            "runtime source tree drift; "
            f"missing={sorted(expected_files - actual_files)}, "
            f"extra={sorted(actual_files - expected_files)}"
        )
    return {
        "status": "PASS",
        "root": str(root),
        "commit": COMMIT,
        "file_count": len(entries),
        "files_sha256": expected["files_sha256"],
        "manifest_sha256": sha256_file(manifest_path),
    }


def build(root: Path) -> dict[str, Any]:
    if root.exists():
        raise FetchError(f"refusing to overwrite runtime source root: {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=root.name + ".tmp.", dir=root.parent))
    try:
        for relative, expected_sha256 in sorted(FILES.items()):
            request = urllib.request.Request(
                BASE_URL + relative,
                headers={"User-Agent": "appworld-evaluator-runtime-lock/1"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            actual_sha256 = sha256_bytes(payload)
            if actual_sha256 != expected_sha256:
                raise FetchError(
                    f"downloaded runtime SHA-256 drift for {relative}: "
                    f"{actual_sha256} != {expected_sha256}"
                )
            destination = temporary.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)

        entries = expected_manifest_entries(temporary)
        manifest = {
            "schema_version": "appworld_evaluator_runtime_source_lock.v1",
            "repository": "https://github.com/StonyBrookNLP/appworld",
            "commit": COMMIT,
            "code_version": CODE_VERSION,
            "file_count": len(entries),
            "files": entries,
            "files_sha256": sha256_bytes(canonical_json_bytes(entries)),
        }
        (temporary / "SOURCE_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, root)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return validate(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = validate(args.output_root.resolve()) if args.check else build(args.output_root.resolve())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FetchError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=os.sys.stderr)
        raise SystemExit(2)
