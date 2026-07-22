"""Create a content-blind, lifecycle-locked AgentDojo retrieval snapshot.

This helper runs on the execution VPS only after the controller has verified the
v2 checklist freeze and sent an exact, ordered blind completion index.  While
holding the execution-locked canonical lifecycle flock it validates every
canonical job, creates one regular-file-only tar snapshot, revalidates the live
tree, fsyncs the snapshot, and publishes a content-free receipt.

No raw JSON, trajectory, prompt, response, evaluator output, or native label is
deserialized or emitted.  The only JSON evidence file opened here is the
content-free ``formal_job_completion.json`` control marker.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile
import tempfile
from typing import Any, BinaryIO, Mapping, Sequence

from evidence_system.core.hashing import sha256_file, sha256_object


REQUEST_SCHEMA_VERSION = "agentdojo_remote_retrieval_snapshot_request/v1"
RECEIPT_SCHEMA_VERSION = "agentdojo_remote_retrieval_snapshot_receipt/v1"
EXPECTED_RECORD_SLOT_COUNT = 2_847
COMPLETION_MARKER = "adapter/formal_job_completion.json"

COMPLETION_INDEX_ENTRY_FIELDS = frozenset(
    {
        "schema_version",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "job_identity_sha256",
        "job_binding_sha256",
        "stage_authorization_sha256",
        "formal_stage_id",
        "formal_stage_session_id",
        "formal_execution_context_sha256",
        "canonical_job_relative_path",
        "completion_marker_relative_path",
        "completion_marker_file_sha256",
        "completion_marker_semantic_sha256",
        "artifact_tree_sha256",
        "artifact_file_count",
        "artifact_total_bytes",
        "native_episode_count",
        "attempt_tree_sha256",
        "attempt_file_count",
        "attempt_total_bytes",
        "supervisor_exit_receipt_sha256",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
)
COMPLETION_MARKER_FIELDS = frozenset(
    {
        "schema_version",
        "completed_at",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "job_binding_sha256",
        "job_identity_sha256",
        "stage_authorization_sha256",
        "formal_stage_id",
        "formal_stage_session_id",
        "formal_execution_context_sha256",
        "artifact_file_count",
        "artifact_tree_sha256",
        "artifact_total_bytes",
        "native_episode_count",
        "attempt_tree_sha256",
        "attempt_file_count",
        "attempt_total_bytes",
        "supervisor_exit_receipt_sha256",
        "worker_status",
        "postprocessor",
    }
)
REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "remote_raw_root",
        "remote_blind_root",
        "retrieval_snapshot_root",
        "retrieval_lifecycle_lock",
        "entry_count",
        "entries_sha256",
        "entries",
        "blind_metadata_entry_count",
        "blind_metadata_entries_sha256",
        "blind_metadata_entries",
    }
)
BLIND_METADATA_ENTRY_FIELDS = frozenset(
    {"relative_path", "sha256", "size_bytes"}
)


class RemoteInventoryError(RuntimeError):
    """The remote canonical tree cannot be snapshotted safely."""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote-raw-root", type=Path, required=True)
    parser.add_argument("--remote-blind-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument("--lifecycle-lock", type=Path, required=True)
    parser.add_argument("--self-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        _assert_equal(
            sha256_file(Path(__file__).absolute()),
            _digest(args.self_sha256, "locked helper hash"),
            "executed helper hash",
        )
        request = _load_request(sys.stdin.buffer.read())
        _assert_equal(
            str(args.remote_raw_root), request["remote_raw_root"], "remote raw root"
        )
        _assert_equal(
            str(args.snapshot_root),
            request["retrieval_snapshot_root"],
            "snapshot root",
        )
        _assert_equal(
            str(args.remote_blind_root),
            request["remote_blind_root"],
            "remote blind root",
        )
        _assert_equal(
            str(args.lifecycle_lock),
            request["retrieval_lifecycle_lock"],
            "lifecycle lock",
        )
        receipt = prepare_retrieval_snapshot(
            request=request,
            remote_raw_root=args.remote_raw_root,
            remote_blind_root=args.remote_blind_root,
            snapshot_root=args.snapshot_root,
            lifecycle_lock=args.lifecycle_lock,
        )
    except Exception as exc:
        failure = {
            "schema_version": "agentdojo_remote_retrieval_snapshot_error/v1",
            "status": "error",
            "error_type": type(exc).__name__,
            "error_sha256": sha256_object(
                {"type": type(exc).__name__, "message": str(exc)}
            ),
            "blind_only": True,
            "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
        }
        print(json.dumps(failure, separators=(",", ":"), sort_keys=True))
        return 2
    print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
    return 0


def prepare_retrieval_snapshot(
    *,
    request: Mapping[str, Any],
    remote_raw_root: Path,
    remote_blind_root: Path,
    snapshot_root: Path,
    lifecycle_lock: Path,
) -> dict[str, Any]:
    validated = _validate_request(request)
    for actual, expected, label in (
        (str(remote_raw_root), validated["remote_raw_root"], "remote raw root"),
        (
            str(remote_blind_root),
            validated["remote_blind_root"],
            "remote blind root",
        ),
        (
            str(snapshot_root),
            validated["retrieval_snapshot_root"],
            "snapshot root",
        ),
        (
            str(lifecycle_lock),
            validated["retrieval_lifecycle_lock"],
            "lifecycle lock",
        ),
    ):
        _assert_equal(actual, expected, label)
    raw_root = _regular_directory(remote_raw_root, "remote raw root")
    blind_root = _regular_directory(remote_blind_root, "remote blind root")
    snapshots = _regular_directory(snapshot_root, "retrieval snapshot root")
    lock_file = _regular_file(lifecycle_lock, "canonical lifecycle lock")
    _assert_disjoint_roots(raw_root, blind_root, snapshots, lock_file)

    descriptor = os.open(
        lock_file,
        os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        pre = _inventory_and_validate(raw_root, blind_root, validated)
        snapshot_id = sha256_object(
            {
                "schema_version": RECEIPT_SCHEMA_VERSION,
                "execution_lock_sha256": request["execution_lock_sha256"],
                "entries_sha256": request["entries_sha256"],
                "source_tree_sha256": pre["tree_sha256"],
            }
        )
        archive_path = snapshots / f"{snapshot_id}.tar"
        receipt_path = snapshots / f"{snapshot_id}.receipt.json"

        if receipt_path.exists() or receipt_path.is_symlink():
            receipt = _load_json(receipt_path, "retrieval snapshot receipt")
            _validate_snapshot_receipt(
                receipt,
                request=request,
                inventory=pre,
                archive_path=archive_path,
                receipt_path=receipt_path,
            )
            return receipt

        temporary_archive: Path | None = None
        if archive_path.exists() or archive_path.is_symlink():
            _regular_file(archive_path, "existing retrieval snapshot archive")
            _verify_archive(archive_path, pre["files"])
        else:
            temporary_archive = _create_archive_temporary(
                snapshot_root=snapshots,
                snapshot_id=snapshot_id,
                source_roots={"raw": raw_root, "blind": blind_root},
                files=pre["files"],
            )
        try:
            archive_candidate = temporary_archive or archive_path
            _verify_archive(archive_candidate, pre["files"])
            post = _inventory_and_validate(raw_root, blind_root, validated)
            _assert_equal(post, pre, "pre/post canonical inventory")
            if temporary_archive is not None:
                _publish_archive_noreplace(temporary_archive, archive_path)
                temporary_archive.unlink()
                temporary_archive = None
            archive = _regular_file(archive_path, "retrieval snapshot archive")
            _verify_archive(archive, pre["files"])
        finally:
            if temporary_archive is not None and temporary_archive.exists():
                temporary_archive.unlink()
        receipt = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "status": "snapshot_verified_content_blind",
            "snapshot_id": snapshot_id,
            "execution_lock_sha256": request["execution_lock_sha256"],
            "execution_policy_sha256": request["execution_policy_sha256"],
            "entries_sha256": request["entries_sha256"],
            "entry_count": EXPECTED_RECORD_SLOT_COUNT,
            "remote_raw_root": str(raw_root),
            "remote_blind_root": str(blind_root),
            "retrieval_lifecycle_lock": str(lock_file),
            "archive": {
                "path": str(archive),
                "sha256": sha256_file(archive),
                "size_bytes": archive.stat().st_size,
                "format": "tar_uncompressed_regular_files_only",
            },
            "source_inventory": pre,
            "pre_post_inventory_identical": True,
            "lifecycle_flock": "exclusive",
            "fsync_completed": True,
            "failed_attempt_archive_included": False,
            "blind_only": True,
            "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
        }
        _exclusive_write_json(receipt_path, receipt)
        _fsync_directory(snapshots)
        _validate_snapshot_receipt(
            receipt,
            request=request,
            inventory=pre,
            archive_path=archive,
            receipt_path=receipt_path,
        )
        return receipt
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _load_request(raw: bytes) -> dict[str, Any]:
    if len(raw) > 16 << 20:
        raise RemoteInventoryError("snapshot request exceeds the control-plane limit")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RemoteInventoryError("snapshot request is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise RemoteInventoryError("snapshot request must be an object")
    return _validate_request(value)


def _validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(request)
    _assert_equal(set(value), REQUEST_FIELDS, "snapshot request fields")
    _assert_equal(value.get("schema_version"), REQUEST_SCHEMA_VERSION, "request schema")
    for field in (
        "execution_lock_sha256",
        "execution_policy_sha256",
        "entries_sha256",
        "blind_metadata_entries_sha256",
    ):
        _digest(value.get(field), field)
    for field in (
        "remote_raw_root",
        "remote_blind_root",
        "retrieval_snapshot_root",
        "retrieval_lifecycle_lock",
    ):
        path = Path(str(value.get(field) or ""))
        if not path.is_absolute():
            raise RemoteInventoryError(f"{field} must be absolute")
    _assert_equal(
        value.get("entry_count"), EXPECTED_RECORD_SLOT_COUNT, "request entry count"
    )
    entries = value.get("entries")
    if not isinstance(entries, list) or len(entries) != EXPECTED_RECORD_SLOT_COUNT:
        raise RemoteInventoryError("request must contain exactly 2,847 entries")
    _assert_equal(value.get("entries_sha256"), sha256_object(entries), "entries hash")
    bindings: list[str] = []
    identities: list[str] = []
    for position, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, Mapping):
            raise RemoteInventoryError(f"completion entry {position} is malformed")
        entry = dict(raw_entry)
        _assert_equal(
            set(entry), COMPLETION_INDEX_ENTRY_FIELDS, "completion entry fields"
        )
        binding = _digest(entry.get("job_binding_sha256"), "job binding")
        identity = _digest(entry.get("job_identity_sha256"), "job identity")
        bindings.append(binding)
        identities.append(identity)
        _assert_equal(
            entry.get("canonical_job_relative_path"), binding, "canonical job path"
        )
        _assert_equal(
            entry.get("completion_marker_relative_path"),
            f"{binding}/{COMPLETION_MARKER}",
            "completion marker path",
        )
        for field in (
            "execution_lock_sha256",
            "execution_policy_sha256",
            "stage_authorization_sha256",
            "formal_execution_context_sha256",
            "completion_marker_file_sha256",
            "completion_marker_semantic_sha256",
            "artifact_tree_sha256",
            "attempt_tree_sha256",
            "supervisor_exit_receipt_sha256",
        ):
            _digest(entry.get(field), field)
        _assert_equal(
            entry.get("schema_version"),
            "agentdojo_formal_remote_completion_index_entry/v2",
            "completion entry schema",
        )
        _assert_equal(
            entry.get("execution_lock_sha256"),
            value["execution_lock_sha256"],
            "completion entry execution lock",
        )
        _assert_equal(
            entry.get("execution_policy_sha256"),
            value["execution_policy_sha256"],
            "completion entry execution policy",
        )
        for field in ("formal_stage_id", "formal_stage_session_id"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise RemoteInventoryError(f"{field} must be a non-empty string")
        for field in (
            "artifact_file_count",
            "artifact_total_bytes",
            "attempt_file_count",
            "attempt_total_bytes",
        ):
            number = entry.get(field)
            if isinstance(number, bool) or not isinstance(number, int) or number < 1:
                raise RemoteInventoryError(f"{field} must be a positive integer")
        _assert_equal(entry.get("native_episode_count"), 3, "native episode count")
        _assert_equal(entry.get("blind_only"), True, "completion entry blind flag")
        _assert_equal(
            entry.get(
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
            ),
            False,
            "completion entry content boundary",
        )
    if len(set(bindings)) != EXPECTED_RECORD_SLOT_COUNT:
        raise RemoteInventoryError("completion index job bindings are not unique")
    if len(set(identities)) != EXPECTED_RECORD_SLOT_COUNT:
        raise RemoteInventoryError("completion index job identities are not unique")
    blind_entries = value.get("blind_metadata_entries")
    blind_count = value.get("blind_metadata_entry_count")
    if (
        isinstance(blind_count, bool)
        or not isinstance(blind_count, int)
        or blind_count != 4
        or not isinstance(blind_entries, list)
        or len(blind_entries) != blind_count
    ):
        raise RemoteInventoryError(
            "request must contain exactly four blind metadata entries"
        )
    _assert_equal(
        value.get("blind_metadata_entries_sha256"),
        sha256_object(blind_entries),
        "blind metadata entries hash",
    )
    blind_paths: list[str] = []
    for position, raw_entry in enumerate(blind_entries):
        if not isinstance(raw_entry, Mapping):
            raise RemoteInventoryError(
                f"blind metadata entry {position} is malformed"
            )
        entry = dict(raw_entry)
        _assert_equal(
            set(entry), BLIND_METADATA_ENTRY_FIELDS, "blind metadata entry fields"
        )
        blind_paths.append(_safe_relative(str(entry.get("relative_path") or "")))
        _digest(entry.get("sha256"), "blind metadata hash")
        size = entry.get("size_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise RemoteInventoryError("blind metadata size must be non-negative")
    if len(blind_paths) != len(set(blind_paths)) or blind_paths != sorted(blind_paths):
        raise RemoteInventoryError("blind metadata paths are duplicate or unordered")
    lock_path = Path(str(value["retrieval_lifecycle_lock"]))
    blind_root = Path(str(value["remote_blind_root"]))
    if any(blind_root / relative == lock_path for relative in blind_paths):
        raise RemoteInventoryError("lifecycle lock cannot be archived as blind metadata")
    return value


def _inventory_and_validate(
    root: Path, blind_root: Path, request: Mapping[str, Any]
) -> dict[str, Any]:
    entries = [dict(item) for item in request["entries"]]
    expected_children = [str(item["job_binding_sha256"]) for item in entries]
    observed_children = sorted(path.name for path in root.iterdir())
    if sorted(expected_children) != observed_children:
        raise RemoteInventoryError("remote canonical job directory set differs")

    all_files: list[dict[str, Any]] = []
    for entry in entries:
        binding = str(entry["job_binding_sha256"])
        job_root = _regular_directory(root / binding, "canonical job root")
        if {path.name for path in job_root.iterdir()} != {"adapter"}:
            raise RemoteInventoryError("canonical job top-level set differs")
        job_files = _file_inventory(job_root)
        marker_relative = COMPLETION_MARKER
        marker_rows = [row for row in job_files if row["path"] == marker_relative]
        if len(marker_rows) != 1:
            raise RemoteInventoryError("canonical completion marker is missing")
        marker_path = _regular_file(
            job_root / marker_relative, "canonical completion marker"
        )
        marker = _load_json(marker_path, "canonical completion marker")
        _validate_marker(marker, entry=entry, marker_path=marker_path)
        artifacts = [row for row in job_files if row["path"] != marker_relative]
        artifact_projection = [
            {"path": row["path"], "sha256": row["sha256"]} for row in artifacts
        ]
        _assert_equal(
            len(artifacts), entry["artifact_file_count"], "artifact file count"
        )
        _assert_equal(
            sha256_object(artifact_projection),
            entry["artifact_tree_sha256"],
            "artifact tree hash",
        )
        _assert_equal(
            sum(int(row["size_bytes"]) for row in artifacts),
            entry["artifact_total_bytes"],
            "artifact total bytes",
        )
        all_files.extend(
            {
                "path": f"raw/{binding}/{row['path']}",
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
            }
            for row in job_files
        )

    blind_files: list[dict[str, Any]] = []
    for expected in request["blind_metadata_entries"]:
        relative = _safe_relative(str(expected["relative_path"]))
        path = _regular_file(blind_root / relative, "blind metadata file")
        observed = {
            "path": f"blind/{relative}",
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        _assert_equal(observed["sha256"], expected["sha256"], "blind metadata hash")
        _assert_equal(
            observed["size_bytes"], expected["size_bytes"], "blind metadata size"
        )
        blind_files.append(observed)
    all_files.extend(blind_files)
    all_files.sort(key=lambda row: str(row["path"]))

    tree_projection = [
        {"path": row["path"], "sha256": row["sha256"]} for row in all_files
    ]
    return {
        "tree_sha256": sha256_object(tree_projection),
        "file_count": len(all_files),
        "total_bytes": sum(int(row["size_bytes"]) for row in all_files),
        "files_sha256": sha256_object(all_files),
        "raw_file_count": len(all_files) - len(blind_files),
        "blind_metadata_file_count": len(blind_files),
        "blind_metadata_entries_sha256": request[
            "blind_metadata_entries_sha256"
        ],
        "files": all_files,
    }


def _validate_marker(
    marker: Mapping[str, Any], *, entry: Mapping[str, Any], marker_path: Path
) -> None:
    _assert_equal(set(marker), COMPLETION_MARKER_FIELDS, "completion marker fields")
    _assert_equal(
        marker.get("schema_version"),
        "agentdojo_formal_job_completion/v2",
        "completion marker schema",
    )
    _assert_equal(marker.get("worker_status"), "completed", "worker status")
    _assert_equal(
        marker.get("postprocessor"),
        "agentdojo_formal_postprocessor/v1",
        "postprocessor identity",
    )
    try:
        completed_at = datetime.fromisoformat(str(marker.get("completed_at") or ""))
    except ValueError as exc:
        raise RemoteInventoryError("completion marker timestamp is invalid") from exc
    if completed_at.tzinfo is None or completed_at.utcoffset() is None:
        raise RemoteInventoryError("completion marker timestamp is not timezone-aware")
    for field in (
        "execution_lock_sha256",
        "execution_policy_sha256",
        "job_binding_sha256",
        "job_identity_sha256",
        "stage_authorization_sha256",
        "formal_stage_id",
        "formal_stage_session_id",
        "formal_execution_context_sha256",
        "artifact_tree_sha256",
        "artifact_file_count",
        "artifact_total_bytes",
        "native_episode_count",
        "attempt_tree_sha256",
        "attempt_file_count",
        "attempt_total_bytes",
        "supervisor_exit_receipt_sha256",
    ):
        _assert_equal(marker.get(field), entry.get(field), f"completion marker {field}")
    _assert_equal(
        sha256_file(marker_path),
        entry.get("completion_marker_file_sha256"),
        "completion marker file hash",
    )
    _assert_equal(
        sha256_object(dict(marker)),
        entry.get("completion_marker_semantic_sha256"),
        "completion marker semantic hash",
    )


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def visit(directory: Path) -> None:
        _regular_directory(directory, "canonical inventory directory")
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda item: item.name)
        for entry in entries:
            path = directory / entry.name
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                visit(path)
                continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RemoteInventoryError(
                    "canonical evidence tree contains a link or special node"
                )
            relative = _safe_relative(path.relative_to(root).as_posix())
            result.append(
                {
                    "path": relative,
                    "sha256": sha256_file(path),
                    "size_bytes": info.st_size,
                }
            )

    visit(root)
    result.sort(key=lambda row: str(row["path"]))
    return result


def _create_archive_temporary(
    *,
    snapshot_root: Path,
    snapshot_id: str,
    source_roots: Mapping[str, Path],
    files: Sequence[Mapping[str, Any]],
) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{snapshot_id}.tar.", suffix=".tmp", dir=snapshot_root
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        with temporary.open("w+b") as handle:
            with tarfile.open(fileobj=handle, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for row in files:
                    relative = _safe_relative(str(row["path"]))
                    parts = PurePosixPath(relative).parts
                    source_root = source_roots.get(parts[0])
                    if source_root is None or len(parts) < 2:
                        raise RemoteInventoryError(
                            "archive entry lacks a locked source-root prefix"
                        )
                    source = _regular_file(
                        source_root.joinpath(*parts[1:]), "archive source evidence"
                    )
                    with _open_nofollow(source) as source_handle:
                        source_stat = os.fstat(source_handle.fileno())
                        _assert_equal(
                            source_stat.st_size, row["size_bytes"], "archive source size"
                        )
                        info = tarfile.TarInfo(relative)
                        info.size = source_stat.st_size
                        info.mode = 0o600
                        info.mtime = 0
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        tar.addfile(info, source_handle)
            handle.flush()
            os.fsync(handle.fileno())
        _verify_archive(temporary, files)
        return temporary
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def _publish_archive_noreplace(temporary: Path, archive_path: Path) -> None:
    try:
        os.link(temporary, archive_path, follow_symlinks=False)
    except FileExistsError as exc:
        raise RemoteInventoryError("snapshot archive destination already exists") from exc
    _fsync_directory(archive_path.parent)


def _verify_archive(
    archive_path: Path, files: Sequence[Mapping[str, Any]]
) -> None:
    archive = _regular_file(archive_path, "retrieval snapshot archive")
    expected = {str(row["path"]): dict(row) for row in files}
    observed: dict[str, dict[str, Any]] = {}
    with tarfile.open(archive, mode="r:") as tar:
        members = tar.getmembers()
        for member in members:
            relative = _safe_relative(member.name)
            if not member.isfile() or member.islnk() or member.issym():
                raise RemoteInventoryError("snapshot archive contains a non-regular member")
            if relative in observed:
                raise RemoteInventoryError("snapshot archive contains duplicate members")
            expected_row = expected.get(relative)
            if expected_row is None:
                raise RemoteInventoryError("snapshot archive contains an extra member")
            _assert_equal(member.size, expected_row["size_bytes"], "archive member size")
            extracted = tar.extractfile(member)
            if extracted is None:
                raise RemoteInventoryError("snapshot archive member is unreadable")
            digest, size = _hash_stream(extracted)
            _assert_equal(digest, expected_row["sha256"], "archive member hash")
            _assert_equal(size, expected_row["size_bytes"], "archive member bytes")
            observed[relative] = expected_row
    _assert_equal(set(observed), set(expected), "snapshot archive member set")


def _validate_snapshot_receipt(
    receipt: Mapping[str, Any],
    *,
    request: Mapping[str, Any],
    inventory: Mapping[str, Any],
    archive_path: Path,
    receipt_path: Path,
) -> None:
    expected_fields = {
        "schema_version",
        "status",
        "snapshot_id",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "entries_sha256",
        "entry_count",
        "remote_raw_root",
        "remote_blind_root",
        "retrieval_lifecycle_lock",
        "archive",
        "source_inventory",
        "pre_post_inventory_identical",
        "lifecycle_flock",
        "fsync_completed",
        "failed_attempt_archive_included",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
    _assert_equal(set(receipt), expected_fields, "snapshot receipt fields")
    for actual, expected, label in (
        (receipt.get("schema_version"), RECEIPT_SCHEMA_VERSION, "receipt schema"),
        (receipt.get("status"), "snapshot_verified_content_blind", "receipt status"),
        (
            receipt.get("execution_lock_sha256"),
            request["execution_lock_sha256"],
            "receipt execution lock",
        ),
        (
            receipt.get("execution_policy_sha256"),
            request["execution_policy_sha256"],
            "receipt execution policy",
        ),
        (receipt.get("entries_sha256"), request["entries_sha256"], "receipt entries"),
        (receipt.get("entry_count"), EXPECTED_RECORD_SLOT_COUNT, "receipt count"),
        (
            receipt.get("remote_raw_root"),
            request["remote_raw_root"],
            "receipt remote raw root",
        ),
        (
            receipt.get("remote_blind_root"),
            request["remote_blind_root"],
            "receipt remote blind root",
        ),
        (
            receipt.get("retrieval_lifecycle_lock"),
            request["retrieval_lifecycle_lock"],
            "receipt lifecycle lock",
        ),
        (receipt.get("source_inventory"), inventory, "receipt source inventory"),
        (receipt.get("pre_post_inventory_identical"), True, "pre/post flag"),
        (receipt.get("lifecycle_flock"), "exclusive", "lifecycle flock"),
        (receipt.get("fsync_completed"), True, "receipt fsync"),
        (receipt.get("failed_attempt_archive_included"), False, "failed attempts"),
        (receipt.get("blind_only"), True, "blind-only flag"),
        (
            receipt.get(
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
            ),
            False,
            "receipt content boundary",
        ),
    ):
        _assert_equal(actual, expected, label)
    expected_snapshot_id = sha256_object(
        {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "execution_lock_sha256": request["execution_lock_sha256"],
            "entries_sha256": request["entries_sha256"],
            "source_tree_sha256": inventory["tree_sha256"],
        }
    )
    _assert_equal(receipt.get("snapshot_id"), expected_snapshot_id, "snapshot id")
    _assert_equal(
        receipt_path,
        archive_path.with_suffix(".receipt.json"),
        "snapshot receipt path",
    )
    archive = _regular_file(archive_path, "receipt snapshot archive")
    archive_binding = receipt.get("archive")
    if not isinstance(archive_binding, Mapping):
        raise RemoteInventoryError("snapshot archive binding is missing")
    _assert_equal(
        dict(archive_binding),
        {
            "path": str(archive),
            "sha256": sha256_file(archive),
            "size_bytes": archive.stat().st_size,
            "format": "tar_uncompressed_regular_files_only",
        },
        "snapshot archive binding",
    )
    _verify_archive(archive, list(inventory["files"]))
    if receipt_path.exists():
        _regular_file(receipt_path, "snapshot receipt")


def _regular_directory(path: Path, label: str) -> Path:
    candidate = Path(path).absolute()
    _reject_symlink_ancestors(candidate, label)
    info = candidate.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise RemoteInventoryError(f"{label} is not a directory")
    return candidate


def _regular_file(path: Path, label: str) -> Path:
    candidate = Path(path).absolute()
    _reject_symlink_ancestors(candidate.parent, label)
    info = candidate.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RemoteInventoryError(f"{label} is not a single-link regular file")
    return candidate


def _reject_symlink_ancestors(path: Path, label: str) -> None:
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise RemoteInventoryError(f"{label} has a symlinked ancestor")


def _assert_disjoint_roots(
    raw_root: Path, blind_root: Path, snapshot_root: Path, lock_file: Path
) -> None:
    roots = (raw_root, blind_root, snapshot_root)
    for position, first in enumerate(roots):
        for second in roots[position + 1 :]:
            if _is_relative_to(first, second) or _is_relative_to(second, first):
                raise RemoteInventoryError("raw/blind/snapshot roots overlap")
    if _is_relative_to(lock_file, raw_root) or _is_relative_to(
        lock_file, snapshot_root
    ):
        raise RemoteInventoryError("lifecycle lock must be outside raw/snapshot roots")
    if not _is_relative_to(lock_file, blind_root):
        raise RemoteInventoryError("lifecycle lock must be inside the blind root")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _safe_relative(value: str) -> str:
    if not value or "\\" in value:
        raise RemoteInventoryError("inventory path is empty or non-POSIX")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RemoteInventoryError("inventory path escapes the snapshot root")
    normalized = path.as_posix()
    if normalized != value:
        raise RemoteInventoryError("inventory path is not canonical")
    return normalized


def _open_nofollow(path: Path) -> BinaryIO:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(descriptor)
        raise RemoteInventoryError("archive source is not a single-link regular file")
    return os.fdopen(descriptor, "rb")


def _hash_stream(stream: BinaryIO) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    while True:
        block = stream.read(1 << 20)
        if not block:
            break
        digest.update(block)
        total += len(block)
    return digest.hexdigest(), total


def _load_json(path: Path, label: str) -> dict[str, Any]:
    file = _regular_file(path, label)
    try:
        value = json.loads(file.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RemoteInventoryError(f"{label} is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise RemoteInventoryError(f"{label} must be an object")
    return dict(value)


def _exclusive_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise RemoteInventoryError("snapshot receipt write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _digest(value: Any, label: str) -> str:
    text = str(value or "")
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise RemoteInventoryError(f"{label} is not a lowercase SHA-256 digest")
    return text


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RemoteInventoryError(f"{label} differs")


if __name__ == "__main__":
    raise SystemExit(main())
