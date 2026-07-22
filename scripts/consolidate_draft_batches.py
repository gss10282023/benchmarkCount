#!/usr/bin/env python3
"""Freeze a validated base draft batch, optionally overlaying successful repairs.

The command is deliberately fail closed.  It treats ``_batch_results.jsonl``
rows as the case ledger, keeps every successful base case, and permits a repair
case only where the base case was failed or not run.  Selected case directories
are copied through a sibling staging directory; source roots are never changed.

Example:

  python3 scripts/consolidate_draft_batches.py \
    --base-root /data/drafts/base \
    --repair-root /data/drafts/repair-01 \
    --repair-root /data/drafts/repair-02 \
    --output-root /data/drafts/consolidated \
    --json-manifest /data/drafts/consolidated.manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "draft_batch_consolidation.v1"
MANIFEST_SCHEMA_VERSION = "draft_batch_consolidation_manifest.v1"
SUMMARY_SCHEMA_VERSION = "draft_batch_consolidation_summary.v1"
ACCEPTED_STATUSES = frozenset({"success", "skipped_existing"})
KNOWN_STATUSES = ACCEPTED_STATUSES | {"failed"}
CANONICAL_SUFFIXES = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stderr.log",
    "stdout.log",
)
RESULTS_NAME = "_batch_results.jsonl"
SUMMARY_NAME = "_batch_summary.json"
ATTEMPT_CHECKLIST_RE = re.compile(r"attempt_([0-9]+)\.checklist\.yaml\Z")


class ConsolidationError(RuntimeError):
    """A deterministic consolidation precondition failed."""


@dataclass(frozen=True)
class BatchRow:
    case_unit_dir: str
    status: str
    payload: dict[str, Any]
    source_root: Path
    source_kind: str
    source_index: int
    line_number: int
    source_line_sha256: str
    row_sha256: str
    canonical_json: bytes


@dataclass(frozen=True)
class Batch:
    root: Path
    kind: str
    index: int
    summary: dict[str, Any]
    rows: dict[str, BatchRow]
    not_run_case_ids: tuple[str, ...]

    @property
    def universe(self) -> frozenset[str]:
        return frozenset((*self.rows, *self.not_run_case_ids))


@dataclass(frozen=True)
class TreeSnapshot:
    sha256: str
    file_count: int
    directory_count: int
    size_bytes: int
    files: dict[str, tuple[int, str]]


@dataclass(frozen=True)
class SelectedCase:
    row: BatchRow
    source_case_dir: Path
    source_tree: TreeSnapshot
    promotion_attempt_index: int
    promotion_attempt_prefix: str


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _require_nonnegative_int(value: Any, label: str) -> int:
    if not _is_int(value) or value < 0:
        raise ConsolidationError(f"{label} must be a non-negative integer")
    return value


def _validate_case_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConsolidationError(f"{label} must be a non-empty string")
    if value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
        raise ConsolidationError(f"{label} is not a safe single path component: {value!r}")
    if value in {RESULTS_NAME, SUMMARY_NAME}:
        raise ConsolidationError(f"{label} collides with a reserved batch filename: {value!r}")
    return value


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ConsolidationError(f"{label} is missing or is not a safe regular file: {path}")
    mode = path.stat(follow_symlinks=False).st_mode
    if not stat.S_ISREG(mode):
        raise ConsolidationError(f"{label} is not a regular file: {path}")
    return path


def _resolve_source_root(path: Path, label: str) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise ConsolidationError(f"{label} must not be a symlink: {expanded}")
    try:
        resolved = expanded.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ConsolidationError(f"{label} does not exist: {expanded}") from exc
    if not resolved.is_dir():
        raise ConsolidationError(f"{label} is not a directory: {resolved}")
    return resolved


def _absolute_future_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    _regular_file(path, label)
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ConsolidationError(f"invalid {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConsolidationError(f"{label} is not a JSON object: {path}")
    return value


def _load_rows(root: Path, kind: str, index: int) -> dict[str, BatchRow]:
    path = _regular_file(root / RESULTS_NAME, f"{kind} batch results")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ConsolidationError(f"cannot read batch results {path}: {exc}") from exc

    rows: dict[str, BatchRow] = {}
    for line_number, source_line in enumerate(data.splitlines(), start=1):
        if not source_line.strip():
            raise ConsolidationError(f"blank line {line_number} in {path}")
        try:
            payload = json.loads(
                source_line.decode("utf-8"),
                parse_constant=_reject_json_constant,
            )
        except (UnicodeDecodeError, ValueError) as exc:
            raise ConsolidationError(f"invalid JSON on line {line_number} of {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ConsolidationError(f"line {line_number} of {path} is not a JSON object")
        case_id = _validate_case_id(
            payload.get("case_unit_dir"),
            f"{path}:{line_number} case_unit_dir",
        )
        if case_id in rows:
            raise ConsolidationError(f"duplicate case_unit_dir {case_id!r} in {path}")
        status_value = payload.get("status")
        if not isinstance(status_value, str) or status_value not in KNOWN_STATUSES:
            raise ConsolidationError(
                f"unsupported status {status_value!r} for {case_id!r} in {path}"
            )
        canonical = _canonical_json_bytes(payload)
        rows[case_id] = BatchRow(
            case_unit_dir=case_id,
            status=status_value,
            payload=payload,
            source_root=root,
            source_kind=kind,
            source_index=index,
            line_number=line_number,
            source_line_sha256=_sha256_bytes(source_line),
            row_sha256=_sha256_bytes(canonical),
            canonical_json=canonical,
        )
    return rows


def _load_batch(root: Path, kind: str, index: int) -> Batch:
    rows = _load_rows(root, kind, index)
    summary = _load_json_object(root / SUMMARY_NAME, f"{kind} batch summary")

    total = _require_nonnegative_int(summary.get("total_cases"), f"{kind} total_cases")
    completed = _require_nonnegative_int(
        summary.get("completed_cases"), f"{kind} completed_cases"
    )
    success = _require_nonnegative_int(
        summary.get("success_cases"), f"{kind} success_cases"
    )
    failed = _require_nonnegative_int(summary.get("failed_cases"), f"{kind} failed_cases")
    if completed != len(rows):
        raise ConsolidationError(
            f"{kind} completed_cases={completed} but {len(rows)} result rows were found"
        )

    observed_success = sum(row.status == "success" for row in rows.values())
    observed_skipped = sum(row.status == "skipped_existing" for row in rows.values())
    observed_failed = sum(row.status == "failed" for row in rows.values())
    if success != observed_success:
        raise ConsolidationError(
            f"{kind} success_cases={success} but result rows contain {observed_success} successes"
        )
    if failed != observed_failed:
        raise ConsolidationError(
            f"{kind} failed_cases={failed} but result rows contain {observed_failed} failures"
        )
    if "skipped_cases" in summary:
        skipped = _require_nonnegative_int(
            summary.get("skipped_cases"), f"{kind} skipped_cases"
        )
        if skipped != observed_skipped:
            raise ConsolidationError(
                f"{kind} skipped_cases={skipped} but result rows contain "
                f"{observed_skipped} skipped rows"
            )
    if completed != observed_success + observed_skipped + observed_failed:
        raise ConsolidationError(f"{kind} result statuses do not close completed_cases")

    not_run_value = summary.get("not_run_case_ids", [])
    if not isinstance(not_run_value, list):
        raise ConsolidationError(f"{kind} not_run_case_ids must be a list")
    not_run: list[str] = []
    seen_not_run: set[str] = set()
    for position, value in enumerate(not_run_value):
        case_id = _validate_case_id(value, f"{kind} not_run_case_ids[{position}]")
        if case_id in seen_not_run:
            raise ConsolidationError(f"duplicate not-run case {case_id!r} in {root / SUMMARY_NAME}")
        if case_id in rows:
            raise ConsolidationError(f"case {case_id!r} is both completed and not run in {kind}")
        seen_not_run.add(case_id)
        not_run.append(case_id)

    not_run_count = _require_nonnegative_int(
        summary.get("not_run_case_count", len(not_run)),
        f"{kind} not_run_case_count",
    )
    if not_run_count != len(not_run):
        raise ConsolidationError(
            f"{kind} not_run_case_count={not_run_count} but "
            f"not_run_case_ids has {len(not_run)} entries"
        )
    if total != completed + not_run_count:
        raise ConsolidationError(
            f"{kind} coverage does not close: total_cases={total}, "
            f"completed_cases={completed}, not_run_case_count={not_run_count}"
        )
    if kind == "base" and total == 0:
        raise ConsolidationError("base batch has no cases")

    return Batch(
        root=root,
        kind=kind,
        index=index,
        summary=summary,
        rows=rows,
        not_run_case_ids=tuple(not_run),
    )


def _snapshot_tree(root: Path) -> TreeSnapshot:
    if root.is_symlink() or not root.is_dir():
        raise ConsolidationError(f"case directory is missing or unsafe: {root}")

    entries: list[dict[str, Any]] = []
    files: dict[str, tuple[int, str]] = {}
    file_count = 0
    directory_count = 0
    size_bytes = 0

    def visit(directory: Path, relative: Path) -> None:
        nonlocal file_count, directory_count, size_bytes
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise ConsolidationError(f"cannot enumerate case tree {directory}: {exc}") from exc
        for child in children:
            rel = relative / child.name
            rel_text = rel.as_posix()
            if child.is_symlink():
                raise ConsolidationError(f"symlink is forbidden in case tree: {child}")
            try:
                mode = child.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise ConsolidationError(f"cannot stat case-tree entry {child}: {exc}") from exc
            if stat.S_ISDIR(mode):
                directory_count += 1
                entries.append({"path": rel_text, "type": "directory"})
                visit(child, rel)
            elif stat.S_ISREG(mode):
                before = child.stat(follow_symlinks=False)
                digest = _sha256_file(child)
                after = child.stat(follow_symlinks=False)
                stable_fields_before = (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                )
                stable_fields_after = (
                    after.st_dev,
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                )
                if stable_fields_before != stable_fields_after:
                    raise ConsolidationError(f"case-tree file changed while hashing: {child}")
                file_count += 1
                size_bytes += before.st_size
                files[rel_text] = (before.st_size, digest)
                entries.append(
                    {
                        "path": rel_text,
                        "type": "file",
                        "size_bytes": before.st_size,
                        "sha256": digest,
                    }
                )
            else:
                raise ConsolidationError(f"special file is forbidden in case tree: {child}")

    visit(root, Path())
    return TreeSnapshot(
        sha256=_sha256_bytes(_canonical_json_bytes(entries)),
        file_count=file_count,
        directory_count=directory_count,
        size_bytes=size_bytes,
        files=files,
    )


def _validate_canonical_and_promotion(
    row: BatchRow,
    case_dir: Path,
    tree: TreeSnapshot,
) -> tuple[int, str]:
    missing = [suffix for suffix in CANONICAL_SUFFIXES if suffix not in tree.files]
    if missing:
        raise ConsolidationError(
            f"case {row.case_unit_dir!r} lacks complete canonical sidecars: {missing}"
        )

    candidates: list[tuple[int, str]] = []
    for relative_path in sorted(tree.files):
        if "/" in relative_path:
            continue
        match = ATTEMPT_CHECKLIST_RE.fullmatch(relative_path)
        if match is None:
            continue
        attempt_index = int(match.group(1))
        if attempt_index < 1:
            continue
        prefix = relative_path.removesuffix(".checklist.yaml")
        if prefix != f"attempt_{attempt_index:02d}":
            continue
        if all(
            tree.files.get(f"{prefix}.{suffix}") == tree.files[suffix]
            for suffix in CANONICAL_SUFFIXES
        ):
            candidates.append((attempt_index, prefix))

    if not candidates:
        raise ConsolidationError(
            f"case {row.case_unit_dir!r} canonical sidecars are not byte-identical "
            "to one complete attempt_N sidecar set"
        )

    if row.status == "success":
        attempts = row.payload.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            raise ConsolidationError(
                f"successful case {row.case_unit_dir!r} has no non-empty attempts list"
            )
        attempt_indices: list[int] = []
        for position, attempt in enumerate(attempts, start=1):
            if not isinstance(attempt, Mapping):
                raise ConsolidationError(
                    f"case {row.case_unit_dir!r} attempt {position} is not an object"
                )
            attempt_index = attempt.get("attempt_index")
            returncode = attempt.get("returncode")
            if not _is_int(attempt_index) or attempt_index != position:
                raise ConsolidationError(
                    f"case {row.case_unit_dir!r} attempt indices must be the unique "
                    f"ordered sequence 1..N; found {attempt_index!r} at position {position}"
                )
            if not _is_int(returncode):
                raise ConsolidationError(
                    f"case {row.case_unit_dir!r} attempt {position} lacks an integer returncode"
                )
            attempt_indices.append(attempt_index)
        final_attempt = attempts[-1]
        final_index = attempt_indices[-1]
        if final_attempt.get("returncode") != 0:
            raise ConsolidationError(
                f"successful case {row.case_unit_dir!r} final attempt did not return 0"
            )
        expected_prefix = f"attempt_{final_index:02d}"
        candidates = [
            item
            for item in candidates
            if item == (final_index, expected_prefix)
        ]
        if not candidates:
            raise ConsolidationError(
                f"case {row.case_unit_dir!r} canonical sidecars do not match its "
                f"final successful attempt {expected_prefix}"
            )

    # Multiple byte-identical attempts are harmless.  Choosing the numerically
    # last one makes the recorded provenance agree with normal retry promotion.
    attempt_index, prefix = sorted(candidates, key=lambda item: (item[0], item[1]))[-1]
    return attempt_index, prefix


def _select_rows(base: Batch, repairs: Sequence[Batch]) -> dict[str, BatchRow]:
    base_universe = base.universe
    for repair in repairs:
        extras = sorted(repair.universe - base_universe)
        if extras:
            raise ConsolidationError(
                f"repair root {repair.root} contains cases outside the base universe: {extras}"
            )

    base_accepted = {
        case_id for case_id, row in base.rows.items() if row.status in ACCEPTED_STATUSES
    }
    for repair in repairs:
        forbidden = sorted(case_id for case_id in repair.rows if case_id in base_accepted)
        if forbidden:
            raise ConsolidationError(
                f"repair root {repair.root} attempts to overwrite successful base cases: {forbidden}"
            )

    selected: dict[str, BatchRow] = {}
    for case_id in sorted(base_universe):
        base_row = base.rows.get(case_id)
        if base_row is not None and base_row.status in ACCEPTED_STATUSES:
            selected[case_id] = base_row
            continue

        candidates = [
            repair.rows[case_id]
            for repair in repairs
            if case_id in repair.rows and repair.rows[case_id].status in ACCEPTED_STATUSES
        ]
        if not candidates:
            base_state = "not_run" if base_row is None else base_row.status
            raise ConsolidationError(
                f"base case {case_id!r} is {base_state} and has no successful repair row"
            )
        if len(candidates) > 1:
            roots = [str(candidate.source_root) for candidate in candidates]
            raise ConsolidationError(
                f"base case {case_id!r} has multiple successful repair rows: {roots}"
            )
        selected[case_id] = candidates[0]

    if set(selected) != set(base_universe):
        raise ConsolidationError("internal coverage error while selecting consolidated rows")
    return selected


def _validate_selected_cases(selected_rows: Mapping[str, BatchRow]) -> list[SelectedCase]:
    selected_cases: list[SelectedCase] = []
    for case_id in sorted(selected_rows):
        row = selected_rows[case_id]
        case_dir = row.source_root / case_id
        tree = _snapshot_tree(case_dir)
        attempt_index, attempt_prefix = _validate_canonical_and_promotion(row, case_dir, tree)
        selected_cases.append(
            SelectedCase(
                row=row,
                source_case_dir=case_dir,
                source_tree=tree,
                promotion_attempt_index=attempt_index,
                promotion_attempt_prefix=attempt_prefix,
            )
        )
    return selected_cases


def _json_pretty_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise ConsolidationError(f"refusing to overwrite existing file: {path}") from exc


def _validate_output_target(output_root: Path) -> bool:
    if output_root.is_symlink():
        raise ConsolidationError(f"output root must not be a symlink: {output_root}")
    if not output_root.exists():
        return False
    if not output_root.is_dir():
        raise ConsolidationError(f"output root exists and is not a directory: {output_root}")
    try:
        first_entry = next(output_root.iterdir(), None)
    except OSError as exc:
        raise ConsolidationError(f"cannot inspect output root {output_root}: {exc}") from exc
    if first_entry is not None:
        raise ConsolidationError(f"output root must not exist or must be empty: {output_root}")
    return True


def _validate_manifest_target(manifest: Path, output_root: Path) -> Path | None:
    if manifest.is_symlink() or manifest.exists():
        raise ConsolidationError(f"JSON manifest target must not already exist: {manifest}")
    try:
        relative = manifest.relative_to(output_root)
    except ValueError:
        return None
    if len(relative.parts) != 1:
        raise ConsolidationError(
            "a manifest inside output-root must be a direct child of output-root"
        )
    if relative.name in {RESULTS_NAME, SUMMARY_NAME}:
        raise ConsolidationError(f"JSON manifest collides with reserved output: {manifest}")
    if relative.name.startswith("_"):
        raise ConsolidationError(
            "a manifest inside output-root must not use an underscore-prefixed "
            "batch-metadata filename"
        )
    return relative


def _assert_destinations_outside_sources(
    *,
    output_root: Path,
    manifest: Path,
    source_roots: Iterable[Path],
) -> None:
    for source_root in source_roots:
        if _is_within(output_root, source_root):
            raise ConsolidationError(
                f"output root is inside raw source root {source_root}: {output_root}"
            )
        if _is_within(manifest, source_root):
            raise ConsolidationError(
                f"JSON manifest is inside raw source root {source_root}: {manifest}"
            )


def _copy_cases_to_staging(
    selected_cases: Sequence[SelectedCase],
    staging_root: Path,
) -> None:
    for selected in selected_cases:
        destination = staging_root / selected.row.case_unit_dir
        shutil.copytree(
            selected.source_case_dir,
            destination,
            symlinks=True,
            copy_function=shutil.copy2,
        )
        copied_tree = _snapshot_tree(destination)
        if copied_tree != selected.source_tree:
            raise ConsolidationError(
                f"copied case tree differs from source for {selected.row.case_unit_dir!r}"
            )


def _build_results_bytes(selected_cases: Sequence[SelectedCase]) -> bytes:
    return b"".join(selected.row.canonical_json + b"\n" for selected in selected_cases)


def _build_summary(
    *,
    selected_cases: Sequence[SelectedCase],
    base_root: Path,
    repair_roots: Sequence[Path],
    output_root: Path,
    manifest: Path,
) -> dict[str, Any]:
    count = len(selected_cases)
    status_counts = {
        status: sum(selected.row.status == status for selected in selected_cases)
        for status in sorted(ACCEPTED_STATUSES)
    }
    source_roots = [str(base_root), *(str(root) for root in repair_roots)]
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "total_cases": count,
        "completed_cases": count,
        # Preserve the runner's ordinary status accounting so this output can
        # itself be loaded and checked as a batch. Both statuses are accepted,
        # but they remain distinct in the consolidated ledger and summary.
        "success_cases": status_counts["success"],
        "skipped_cases": status_counts["skipped_existing"],
        "failed_cases": 0,
        "not_run_case_count": 0,
        "not_run_case_ids": [],
        "warning_count": sum(
            len(selected.row.payload.get("quality_warnings", []))
            if isinstance(selected.row.payload.get("quality_warnings", []), list)
            else 0
            for selected in selected_cases
        ),
        "output_root": str(output_root),
        "source_roots": source_roots,
        "consolidation": {
            "schema_version": SCHEMA_VERSION,
            "base_root": str(base_root),
            "repair_roots": [str(root) for root in repair_roots],
            "source_roots": source_roots,
            "json_manifest": str(manifest),
            "success_semantics": "accepted_success_or_skipped_existing",
            "source_status_counts": status_counts,
        },
    }


def _build_manifest(
    *,
    selected_cases: Sequence[SelectedCase],
    base_root: Path,
    repair_roots: Sequence[Path],
    output_root: Path,
    results_bytes: bytes,
    summary_bytes: bytes,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for selected in selected_cases:
        row = selected.row
        cases.append(
            {
                "case_unit_dir": row.case_unit_dir,
                "source_kind": row.source_kind,
                "source_root": str(row.source_root),
                "source_batch_index": row.source_index,
                "source_row_line_number": row.line_number,
                "source_status": row.status,
                "row_sha256": row.row_sha256,
                "source_line_sha256": row.source_line_sha256,
                "case_tree_sha256": selected.source_tree.sha256,
                "case_tree_file_count": selected.source_tree.file_count,
                "case_tree_directory_count": selected.source_tree.directory_count,
                "case_tree_size_bytes": selected.source_tree.size_bytes,
                "promotion_attempt_index": selected.promotion_attempt_index,
                "promotion_attempt_prefix": selected.promotion_attempt_prefix,
            }
        )
    source_roots = [str(base_root), *(str(root) for root in repair_roots)]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "case_count": len(cases),
        "base_root": str(base_root),
        "repair_roots": [str(root) for root in repair_roots],
        "source_roots": source_roots,
        "output_root": str(output_root),
        "canonical_sidecars": list(CANONICAL_SUFFIXES),
        "row_hash": {
            "algorithm": "sha256",
            "basis": "UTF-8 canonical JSON (sorted keys, compact separators)",
        },
        "source_line_hash": {
            "algorithm": "sha256",
            "basis": "exact source JSONL line bytes, line terminator excluded",
        },
        "case_tree_hash": {
            "algorithm": "sha256",
            "basis": (
                "canonical JSON of sorted relative directory/file entries; "
                "file entries include size_bytes and sha256"
            ),
        },
        "batch_results_sha256": _sha256_bytes(results_bytes),
        "batch_summary_sha256": _sha256_bytes(summary_bytes),
        "cases": cases,
    }


def consolidate(
    *,
    base_root: Path,
    repair_roots: Sequence[Path],
    output_root: Path,
    json_manifest: Path,
) -> dict[str, Any]:
    """Validate and consolidate batches, returning the written manifest."""

    resolved_base = _resolve_source_root(base_root, "base root")
    resolved_repairs = [
        _resolve_source_root(path, f"repair root {index}")
        for index, path in enumerate(repair_roots, start=1)
    ]
    if len({resolved_base, *resolved_repairs}) != 1 + len(resolved_repairs):
        raise ConsolidationError("base-root and repair-root arguments must be distinct")

    # Check the caller-provided leaf before ``resolve`` follows it.  Otherwise
    # a directory symlink would become indistinguishable from its target.
    raw_output = output_root.expanduser()
    raw_manifest = json_manifest.expanduser()
    if raw_output.is_symlink():
        raise ConsolidationError(f"output root must not be a symlink: {raw_output}")
    if raw_manifest.is_symlink():
        raise ConsolidationError(f"JSON manifest target must not be a symlink: {raw_manifest}")
    resolved_output = _absolute_future_path(raw_output)
    resolved_manifest = _absolute_future_path(raw_manifest)
    output_existed_empty = _validate_output_target(resolved_output)
    manifest_relative = _validate_manifest_target(resolved_manifest, resolved_output)
    if manifest_relative is None and _is_within(resolved_output, resolved_manifest):
        raise ConsolidationError(
            f"JSON manifest cannot be an ancestor of output-root: {resolved_manifest}"
        )
    _assert_destinations_outside_sources(
        output_root=resolved_output,
        manifest=resolved_manifest,
        source_roots=[resolved_base, *resolved_repairs],
    )

    base = _load_batch(resolved_base, "base", 0)
    repairs = [
        _load_batch(root, "repair", index)
        for index, root in enumerate(resolved_repairs, start=1)
    ]
    selected_rows = _select_rows(base, repairs)
    if manifest_relative is not None and manifest_relative.name in selected_rows:
        raise ConsolidationError(
            f"JSON manifest path collides with case directory {manifest_relative.name!r}"
        )
    selected_cases = _validate_selected_cases(selected_rows)

    # No destination is created until all source ledgers, coverage, canonical
    # sidecars and promotion bytes have passed validation.
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(
            prefix=f".{resolved_output.name}.consolidating-",
            dir=resolved_output.parent,
        )
    )
    external_manifest_temp: Path | None = None
    external_manifest_committed = False
    committed_output = False
    try:
        _copy_cases_to_staging(selected_cases, staging_root)
        results_bytes = _build_results_bytes(selected_cases)
        summary = _build_summary(
            selected_cases=selected_cases,
            base_root=resolved_base,
            repair_roots=resolved_repairs,
            output_root=resolved_output,
            manifest=resolved_manifest,
        )
        summary_bytes = _json_pretty_bytes(summary)
        _write_exclusive(staging_root / RESULTS_NAME, results_bytes)
        _write_exclusive(staging_root / SUMMARY_NAME, summary_bytes)

        manifest = _build_manifest(
            selected_cases=selected_cases,
            base_root=resolved_base,
            repair_roots=resolved_repairs,
            output_root=resolved_output,
            results_bytes=results_bytes,
            summary_bytes=summary_bytes,
        )
        manifest_bytes = _json_pretty_bytes(manifest)
        if manifest_relative is not None:
            _write_exclusive(staging_root / manifest_relative, manifest_bytes)
        else:
            resolved_manifest.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{resolved_manifest.name}.",
                suffix=".tmp",
                dir=resolved_manifest.parent,
            )
            external_manifest_temp = Path(temp_name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(manifest_bytes)

        # Verify the exact staged ledger and the copied case set before the
        # single-directory commit.
        staged_case_dirs = sorted(
            child.name
            for child in staging_root.iterdir()
            if child.is_dir() and not child.is_symlink()
        )
        expected_case_dirs = [selected.row.case_unit_dir for selected in selected_cases]
        if staged_case_dirs != expected_case_dirs:
            raise ConsolidationError(
                f"staged case coverage differs: expected={expected_case_dirs}, "
                f"actual={staged_case_dirs}"
            )
        if (staging_root / RESULTS_NAME).read_bytes() != results_bytes:
            raise ConsolidationError("staged batch results changed before commit")
        if (staging_root / SUMMARY_NAME).read_bytes() != summary_bytes:
            raise ConsolidationError("staged batch summary changed before commit")

        if external_manifest_temp is not None:
            if resolved_manifest.is_symlink() or os.path.lexists(resolved_manifest):
                raise ConsolidationError(
                    f"JSON manifest target appeared before commit: {resolved_manifest}"
                )
            try:
                # Temp and destination share a parent/filesystem.  link(2) is
                # an atomic no-clobber publication, unlike os.replace().
                os.link(external_manifest_temp, resolved_manifest)
            except FileExistsError as exc:
                raise ConsolidationError(
                    f"JSON manifest target appeared before commit: {resolved_manifest}"
                ) from exc
            external_manifest_committed = True

        if resolved_output.is_symlink():
            raise ConsolidationError(
                f"output root became a symlink before commit: {resolved_output}"
            )
        if output_existed_empty:
            try:
                resolved_output.rmdir()
            except OSError as exc:
                raise ConsolidationError(
                    f"output root stopped being safely empty before commit: {resolved_output}"
                ) from exc
        elif resolved_output.exists() or os.path.lexists(resolved_output):
            raise ConsolidationError(
                f"output root appeared before commit: {resolved_output}"
            )
        try:
            os.replace(staging_root, resolved_output)
        except OSError:
            if output_existed_empty and not resolved_output.exists():
                resolved_output.mkdir()
            raise
        committed_output = True

        if external_manifest_temp is not None:
            external_manifest_temp.unlink()
            external_manifest_temp = None
        return manifest
    finally:
        if not committed_output and staging_root.exists():
            shutil.rmtree(staging_root)
        if external_manifest_committed and not committed_output:
            try:
                if (
                    external_manifest_temp is not None
                    and resolved_manifest.exists()
                    and os.path.samefile(external_manifest_temp, resolved_manifest)
                ):
                    resolved_manifest.unlink()
            except OSError:
                # Preserve the original failure.  A complete no-clobber
                # manifest is safer than deleting an unrelated path.
                pass
        if external_manifest_temp is not None and external_manifest_temp.exists():
            external_manifest_temp.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument(
        "--repair-root",
        type=Path,
        action="append",
        default=[],
        help=(
            "Optional repair batch root; repeat for more than one repair batch. "
            "Omit to freeze an already-complete all-accepted base batch."
        ),
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--json-manifest", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = consolidate(
            base_root=args.base_root,
            repair_roots=args.repair_root,
            output_root=args.output_root,
            json_manifest=args.json_manifest,
        )
    except (ConsolidationError, OSError) as exc:
        print(f"consolidation failed: {exc}", file=sys.stderr)
        return 2
    print(
        f"Consolidated {manifest['case_count']} cases into "
        f"{manifest['output_root']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
