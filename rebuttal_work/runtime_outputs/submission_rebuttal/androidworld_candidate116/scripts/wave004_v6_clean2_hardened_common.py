#!/usr/bin/env python3
"""Shared, stdlib-only trust helpers for the clean5 hardened candidate gate.

This uniquely named development variant is intentionally not a production GO.  It
exists so its fail-closed mechanics can be reviewed without touching any earlier
create-once snapshot, prelock, config, or wave namespace.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping


CASE_COUNT = 116
PARALLELISM = 6
GENERATION_ID = "wave_004_v6_clean5_hardened"
PRELOCK_SCHEMA = "androidworld_candidate116_codex_draft_prelock/v6_clean5_hardened"
CONFIG_SCHEMA = "androidworld_candidate116_codex_draft_config/v6_clean5_hardened"
SNAPSHOT_SCHEMA = (
    "androidworld_candidate116_draft_toolchain_snapshot/v6_clean5_hardened"
)
CANDIDATE_REVIEW_SCHEMA = (
    "androidworld_candidate116_wave004_v6_clean5_hardened_candidate_review/v1"
)
INDEPENDENT_PRELOCK_REVIEW_SCHEMA = (
    "androidworld_candidate116_wave004_v6_clean5_hardened_independent_prelock_review/v1"
)
LAUNCH_APPROVAL_SCHEMA = "androidworld_candidate116_wave004_v6_clean5_hardened_independent_launch_approval/v1"
PRELOCK_CLAIM_SCHEMA = (
    "androidworld_candidate116_wave004_v6_clean5_hardened_prelock_claim/v1"
)
OWNER_NONCE_ENV = "ANDROIDWORLD_CANDIDATE116_CLEAN5_OWNER_NONCE"
LAUNCH_NONCE_ENV = "ANDROIDWORLD_CANDIDATE116_CLEAN5_LAUNCH_NONCE"
NONCE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_MODEL = "gpt-5.6-sol"
EXPECTED_REASONING = "xhigh"
EXPECTED_SANDBOX = "read-only"  # native runner interface; no Codex --sandbox flag
EXPECTED_PERMISSION_PROFILE = "candidate_draft_isolated"
EXPECTED_MODEL_CONTEXT_WINDOW = 272_000
EXPECTED_EFFECTIVE_CONTEXT_LIMIT = 258_400
EXPECTED_CODEX_VERSION = "codex-cli 0.144.4"
EXPECTED_FREEZE_SHA256 = (
    "fe2018595bf1ef44de803fffe82c81dd55f5368b8fde47d1a10a7958bdd8a9e4"
)
CASE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
SOURCE_PATH_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")


class Wave004V6Clean2HardenedError(RuntimeError):
    """Raised whenever a clean5 hardened trust assertion cannot be proven."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's ``False == 0`` coercion."""

    return canonical_bytes(left) == canonical_bytes(right)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_regular_bytes_bound(
    path: Path,
    *,
    label: str,
    expected_binding: Mapping[str, Any] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Read one non-symlink regular file and bind the bytes from the same fd.

    The lexical path and every resolved component must identify the same path.  The
    fd and directory entry are checked before and after the read, closing the usual
    lstat/open/read TOCTOU gap.  When supplied, ``expected_binding`` must match the
    resulting byte/mode/path binding exactly.
    """

    absolute = path.absolute()
    try:
        lexical = absolute.lstat()
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise Wave004V6Clean2HardenedError(f"cannot stat {label}: {exc}") from exc
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISREG(lexical.st_mode)
        or resolved != absolute
    ):
        raise Wave004V6Clean2HardenedError(
            f"{label} is not a lexical non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise Wave004V6Clean2HardenedError(f"cannot open {label}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 8 * 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        final = absolute.lstat()
    except OSError as exc:
        raise Wave004V6Clean2HardenedError(
            f"{label} disappeared after bound read: {exc}"
        ) from exc

    def identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if (
        not stat.S_ISREG(before.st_mode)
        or identity(before) != identity(after)
        or identity(before) != identity(final)
    ):
        raise Wave004V6Clean2HardenedError(
            f"{label} identity changed during bound read"
        )
    payload = b"".join(chunks)
    if len(payload) != before.st_size:
        raise Wave004V6Clean2HardenedError(f"{label} short read")
    binding = {
        "path": str(resolved),
        "kind": "regular_file",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": before.st_size,
        "mode": stat.S_IMODE(before.st_mode),
    }
    if expected_binding is not None and not canonical_json_equal(
        binding, expected_binding
    ):
        raise Wave004V6Clean2HardenedError(f"{label} binding changed")
    return payload, binding


def load_sealed_json_0444(
    path: Path, label: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load JSON from bytes bound to an exact lexical regular 0444 file."""

    payload, binding = read_regular_bytes_bound(path, label=label)
    if binding["mode"] != 0o444:
        raise Wave004V6Clean2HardenedError(f"{label} must be sealed mode 0444")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Wave004V6Clean2HardenedError(f"cannot load {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise Wave004V6Clean2HardenedError(f"{label} is not a JSON object")
    return value, binding


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Wave004V6Clean2HardenedError(f"cannot load {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise Wave004V6Clean2HardenedError(f"{label} is not a JSON object")
    return value


def add_self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result.pop(field, None)
    result[field] = canonical_sha256(result)
    return result


def verify_self_hash(value: Mapping[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if not isinstance(claimed, str) or claimed != canonical_sha256(core):
        raise Wave004V6Clean2HardenedError(f"{label} self-hash mismatch")


def consume_and_verify_nonce(
    approval: Mapping[str, Any],
    *,
    hash_field: str,
    environment_variable: str,
    label: str,
) -> dict[str, Any]:
    """Consume a one-shot secret from the environment and verify its bound hash.

    The secret is removed from ``os.environ`` before this function returns, including
    every failure path after lookup.  Callers retain only this hash-only receipt and
    must invoke the gate before creating any claim, runtime root, or model process.
    """

    expected = approval.get(hash_field)
    if not isinstance(expected, str) or not NONCE_SHA256_RE.fullmatch(expected):
        raise Wave004V6Clean2HardenedError(
            f"{label} approval has no canonical {hash_field}"
        )
    nonce = os.environ.pop(environment_variable, None)
    if nonce is None:
        raise Wave004V6Clean2HardenedError(
            f"{label} one-shot environment nonce is missing"
        )
    try:
        encoded = nonce.encode("utf-8")
        if not 32 <= len(encoded) <= 4096 or any(
            character in nonce for character in ("\x00", "\r", "\n")
        ):
            raise Wave004V6Clean2HardenedError(
                f"{label} one-shot environment nonce violates the length/encoding policy"
            )
        observed = hashlib.sha256(encoded).hexdigest()
        if not hmac.compare_digest(observed, expected):
            raise Wave004V6Clean2HardenedError(
                f"{label} one-shot environment nonce hash mismatch"
            )
    finally:
        nonce = ""
    return {
        "status": "verified_and_consumed_before_side_effects",
        "nonce_sha256": expected,
        "hash_field": hash_field,
        "raw_nonce_persisted": False,
        "inherited_by_children": False,
    }


def write_json_create_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise Wave004V6Clean2HardenedError(
            f"create-once destination already exists: {path}"
        ) from exc


def regular_file_binding(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise Wave004V6Clean2HardenedError(f"regular binding refuses symlink: {path}")
    resolved = path.resolve(strict=True)
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise Wave004V6Clean2HardenedError(f"not a regular file: {path}")
    return {
        "path": str(resolved),
        "kind": "regular_file",
        "sha256": sha256_file(resolved),
        "size_bytes": metadata.st_size,
        "mode": stat.S_IMODE(metadata.st_mode),
    }


def executable_binding(path: Path) -> dict[str, Any]:
    """Bind an executable path, including both symlink identity and target bytes."""

    absolute = path.absolute()
    metadata = absolute.lstat()
    resolved = absolute.resolve(strict=True)
    if not resolved.is_file():
        raise Wave004V6Clean2HardenedError(f"executable target is not a file: {path}")
    binding = {
        "path": str(absolute),
        "kind": "symlink" if stat.S_ISLNK(metadata.st_mode) else "regular_file",
        "resolved_path": str(resolved),
        "resolved_sha256": sha256_file(resolved),
        "resolved_size_bytes": resolved.stat().st_size,
        "mode": stat.S_IMODE(metadata.st_mode),
    }
    if stat.S_ISLNK(metadata.st_mode):
        binding["link_target"] = os.readlink(absolute)
    return binding


def verify_regular_file_binding(binding: Mapping[str, Any], label: str) -> Path:
    if (
        set(binding) != {"path", "kind", "sha256", "size_bytes", "mode"}
        or type(binding.get("size_bytes")) is not int
        or type(binding.get("mode")) is not int
        or not isinstance(binding.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", str(binding.get("sha256"))) is None
    ):
        raise Wave004V6Clean2HardenedError(f"{label} binding schema is invalid")
    path = Path(str(binding.get("path") or ""))
    if not path.is_absolute() or binding.get("kind") != "regular_file":
        raise Wave004V6Clean2HardenedError(f"{label} binding identity is invalid")
    if path.is_symlink() or not path.is_file():
        raise Wave004V6Clean2HardenedError(
            f"{label} is missing, non-regular, or symlinked"
        )
    metadata = path.lstat()
    if (
        path.resolve(strict=True) != path
        or metadata.st_size != binding.get("size_bytes")
        or stat.S_IMODE(metadata.st_mode) != binding.get("mode")
        or sha256_file(path) != binding.get("sha256")
    ):
        raise Wave004V6Clean2HardenedError(f"{label} physical binding mismatch")
    return path


def verify_executable_binding(binding: Mapping[str, Any], label: str) -> Path:
    kind_value = binding.get("kind")
    exact_keys = {
        "path",
        "kind",
        "resolved_path",
        "resolved_sha256",
        "resolved_size_bytes",
        "mode",
        *({"link_target"} if kind_value == "symlink" else set()),
    }
    if (
        kind_value not in {"symlink", "regular_file"}
        or set(binding) != exact_keys
        or type(binding.get("resolved_size_bytes")) is not int
        or type(binding.get("mode")) is not int
        or not isinstance(binding.get("resolved_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", str(binding.get("resolved_sha256"))) is None
    ):
        raise Wave004V6Clean2HardenedError(
            f"{label} executable binding schema is invalid"
        )
    path = Path(str(binding.get("path") or ""))
    if not path.is_absolute() or not path.exists():
        raise Wave004V6Clean2HardenedError(f"{label} executable path is missing")
    metadata = path.lstat()
    kind = "symlink" if stat.S_ISLNK(metadata.st_mode) else "regular_file"
    if kind != binding.get("kind") or stat.S_IMODE(metadata.st_mode) != binding.get(
        "mode"
    ):
        raise Wave004V6Clean2HardenedError(f"{label} executable link identity changed")
    if kind == "symlink" and os.readlink(path) != binding.get("link_target"):
        raise Wave004V6Clean2HardenedError(f"{label} executable symlink target changed")
    resolved = path.resolve(strict=True)
    if (
        str(resolved) != binding.get("resolved_path")
        or resolved.stat().st_size != binding.get("resolved_size_bytes")
        or sha256_file(resolved) != binding.get("resolved_sha256")
    ):
        raise Wave004V6Clean2HardenedError(f"{label} executable target bytes changed")
    return path


def require_safe_case_id(case_id: Any, label: str = "case_unit_id") -> str:
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        raise Wave004V6Clean2HardenedError(f"unsafe {label}: {case_id!r}")
    return case_id


def require_safe_source_path(value: Any, label: str = "Source Inventory path") -> str:
    """Return a canonical packet-relative path or fail closed.

    Exact Source Inventory paths are later materialized below ``packet_sources``.
    Absolute paths, traversal, empty segments, backslashes, and dot segments would
    make that namespace ambiguous and are therefore rejected before any write.
    """

    if not isinstance(value, str) or not SOURCE_PATH_RE.fullmatch(value):
        raise Wave004V6Clean2HardenedError(f"unsafe {label}: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts) or "\\" in value:
        raise Wave004V6Clean2HardenedError(f"unsafe {label}: {value!r}")
    return value


def relative_to(path: Path, root: Path, label: str) -> str:
    try:
        return (
            path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()
        )
    except ValueError as exc:
        raise Wave004V6Clean2HardenedError(
            f"{label} escapes required root: {path}"
        ) from exc


def verify_exact_directory_files(
    root: Path,
    expected: list[Mapping[str, Any]],
    *,
    label: str,
    excluded_relative_paths: set[str] | None = None,
) -> None:
    if root.is_symlink() or not root.is_dir():
        raise Wave004V6Clean2HardenedError(f"{label} root is missing or symlinked")
    excluded = excluded_relative_paths or set()
    observed: list[dict[str, Any]] = []
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()
    ):
        if path.is_symlink():
            raise Wave004V6Clean2HardenedError(f"symlink in {label}: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if relative in excluded:
                continue
            observed.append(
                {
                    "relative_path": relative,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    expected_rows = list(expected)
    for index, row in enumerate(expected_rows):
        if (
            not isinstance(row, Mapping)
            or set(row) != {"relative_path", "sha256", "size_bytes"}
            or not isinstance(row.get("relative_path"), str)
            or not isinstance(row.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256"))) is None
            or type(row.get("size_bytes")) is not int
            or row.get("size_bytes", -1) < 0
        ):
            raise Wave004V6Clean2HardenedError(
                f"{label} expected file row {index} schema is invalid"
            )
    if not canonical_json_equal(observed, expected_rows):
        raise Wave004V6Clean2HardenedError(f"{label} exact file namespace changed")


def require_empty_or_absent(path: Path, label: str) -> None:
    if path.is_symlink():
        raise Wave004V6Clean2HardenedError(f"{label} is symlinked")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise Wave004V6Clean2HardenedError(
            f"{label} must be absent or an empty directory"
        )
