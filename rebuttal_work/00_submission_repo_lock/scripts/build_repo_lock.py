#!/usr/bin/env python3
"""Create the Step 1 repository, dependency, archive, and diff lock."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ARTIFACT_COMMIT = "ffd9ff4e706d85ff2d12e60f087cde664dbae433"
PAPER_SOURCE_COMMIT = "35b962c8eb222acbbe4eaf05b9e48859c9d4832e"
LEGACY_HEAD = "4a29e3dda49e7b3b52c8ef37979a078ae92097a2"
FULL_ARCHIVE_SHA256 = "6fc564e106ba92317c931427cdab759070296857e3d1a22347bbb682ac156ea5"
LEGACY_IMMUTABLE_ROOTS = (
    ("neurips_ed_track_minimal", "legacy experiment code"),
    ("results", "legacy working experiment outputs"),
    ("paper_result_packages", "frozen public result packages"),
)


def run(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        list(args),
        cwd=root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def git(root: Path, *args: str) -> bytes:
    return run(root, "git", *args)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def commit_info(root: Path, commit: str) -> dict[str, str]:
    fields = git(root, "show", "-s", "--format=%H%x00%P%x00%cI%x00%s", commit).decode().rstrip("\n").split("\0")
    if len(fields) != 4:
        raise ValueError(f"unexpected commit metadata for {commit}")
    return {"commit": fields[0], "parents": fields[1], "committed_at": fields[2], "subject": fields[3]}


def object_exists(root: Path, spec: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", spec], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def top_level(path: str) -> str:
    return path.split("/", 1)[0]


def parse_name_status_z(data: bytes) -> list[tuple[str, str]]:
    tokens = data.decode("utf-8", errors="surrogateescape").split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    if len(tokens) % 2:
        raise ValueError("unexpected --name-status -z stream")
    return [(tokens[index], tokens[index + 1]) for index in range(0, len(tokens), 2)]


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def verify_recursive_immutable(path: Path) -> int:
    """Require macOS UF_IMMUTABLE on the root and every descendant."""
    immutable_flag = getattr(stat, "UF_IMMUTABLE", None)
    if immutable_flag is None:
        raise RuntimeError("UF_IMMUTABLE is unavailable; cannot prove legacy inputs read-only")
    count = 0
    for directory, dirnames, filenames in os.walk(path, followlinks=False):
        candidates = [Path(directory) / name for name in (*dirnames, *filenames)]
        if Path(directory) == path:
            candidates.insert(0, path)
        for candidate in candidates:
            count += 1
            if not (candidate.stat(follow_symlinks=False).st_flags & immutable_flag):
                raise PermissionError(f"legacy input is not filesystem-immutable: {candidate}")
    if count == 0:
        raise ValueError(f"legacy immutable root is empty or missing: {path}")
    return count


def build(root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    submission_snapshot = output / "snapshots/SUBMISSION_REPO"
    legacy_head_snapshot = output / "snapshots/LEGACY_HEAD_SNAPSHOT"
    execution_root = root / "rebuttal_work/runtime_outputs/submission_rebuttal"
    code_archive = output / "submission_source_archive.tar"

    submission_head = git(submission_snapshot, "rev-parse", "HEAD").decode().strip()
    legacy_snapshot_head = git(legacy_head_snapshot, "rev-parse", "HEAD").decode().strip()
    if submission_head != ARTIFACT_COMMIT or legacy_snapshot_head != LEGACY_HEAD:
        raise ValueError("snapshot worktree HEAD does not match its locked commit")
    if any(is_within(execution_root, snapshot) or is_within(snapshot, execution_root) for snapshot in (submission_snapshot, legacy_head_snapshot)):
        raise ValueError("execution root overlaps a locked repository snapshot")

    immutable_roots = []
    for relative_path, role in LEGACY_IMMUTABLE_ROOTS:
        path = root / relative_path
        immutable_roots.append(
            {
                "path": relative_path,
                "role": role,
                "recursive_entry_count": verify_recursive_immutable(path),
            }
        )

    artifact_info = commit_info(root, ARTIFACT_COMMIT)
    paper_info = commit_info(root, PAPER_SOURCE_COMMIT)
    legacy_info = commit_info(root, LEGACY_HEAD)
    artifact_tree = git(root, "rev-parse", f"{ARTIFACT_COMMIT}^{{tree}}").decode().strip()
    paper_tree = git(root, "rev-parse", f"{PAPER_SOURCE_COMMIT}^{{tree}}").decode().strip()
    legacy_tree = git(root, "rev-parse", f"{LEGACY_HEAD}^{{tree}}").decode().strip()
    minimal_tree = git(root, "rev-parse", f"{ARTIFACT_COMMIT}:neurips_ed_track_minimal").decode().strip()
    package_tree = git(root, "rev-parse", f"{ARTIFACT_COMMIT}:paper_result_packages").decode().strip()
    full_tree_listing = git(root, "ls-tree", "-r", "-z", ARTIFACT_COMMIT)

    dependency_paths = ["pyproject.toml", "uv.lock", "neurips_ed_track_minimal/requirements.txt"]
    dependency_rows: list[dict[str, str]] = []
    for path in dependency_paths:
        content = git(root, "show", f"{ARTIFACT_COMMIT}:{path}")
        blob_oid = git(root, "rev-parse", f"{ARTIFACT_COMMIT}:{path}").decode().strip()
        dependency_rows.append(
            {
                "path": path,
                "sha256": sha256_bytes(content),
                "git_blob_oid": blob_oid,
                "lock_strength": "exact_lock" if path == "uv.lock" else "project_spec_or_lower_bound",
            }
        )
    write_csv(output / "dependency_hashes.csv", ["path", "sha256", "git_blob_oid", "lock_strength"], dependency_rows)

    tree_lines = git(root, "ls-tree", "-r", "-l", ARTIFACT_COMMIT).decode("utf-8", errors="replace").splitlines()
    gitlink_count = sum(line.startswith("160000 ") for line in tree_lines)
    large_blob_count = 0
    for line in tree_lines:
        parts = line.split(None, 4)
        if len(parts) >= 4 and parts[0] == "100644" or (parts and parts[0] == "100755"):
            try:
                size = int(parts[3])
            except (ValueError, IndexError):
                continue
            large_blob_count += size >= 100 * 1024 * 1024

    commit_diff = git(root, "diff", "--no-renames", "--name-status", "-z", f"{ARTIFACT_COMMIT}..{LEGACY_HEAD}")
    commit_changes = parse_name_status_z(commit_diff)
    commit_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for status, path in commit_changes:
        commit_counts[top_level(path)][status] += 1

    untracked_stream = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    untracked_paths = [
        path
        for path in untracked_stream.decode("utf-8", errors="surrogateescape").split("\0")
        if path and not path.startswith("rebuttal_work/")
    ]
    untracked_counts = Counter(top_level(path) for path in untracked_paths)

    tracked_worktree_diff = git(root, "diff-files", "--name-status", "-z")
    tracked_worktree_changes = parse_name_status_z(tracked_worktree_diff)
    tracked_worktree_counts = Counter(top_level(path) for _, path in tracked_worktree_changes)

    diff_rows: list[dict[str, Any]] = []
    all_top = sorted(set(commit_counts) | set(untracked_counts) | set(tracked_worktree_counts))
    for name in all_top:
        diff_rows.append(
            {
                "top_level_path": name,
                "commit_added": commit_counts[name]["A"],
                "commit_modified": commit_counts[name]["M"],
                "commit_deleted": commit_counts[name]["D"],
                "legacy_worktree_tracked_changes": tracked_worktree_counts[name],
                "legacy_worktree_untracked": untracked_counts[name],
            }
        )
    write_csv(
        output / "repo_diff_top_level.csv",
        [
            "top_level_path",
            "commit_added",
            "commit_modified",
            "commit_deleted",
            "legacy_worktree_tracked_changes",
            "legacy_worktree_untracked",
        ],
        diff_rows,
    )
    repo_diff = {
        "schema_version": "step1_repo_diff/v1",
        "submission_artifact_commit": ARTIFACT_COMMIT,
        "legacy_head_commit": LEGACY_HEAD,
        "commit_diff_entry_count": len(commit_changes),
        "commit_diff_name_status_sha256": sha256_bytes(commit_diff),
        "legacy_worktree_tracked_change_count": len(tracked_worktree_changes),
        "legacy_worktree_tracked_diff_sha256": sha256_bytes(tracked_worktree_diff),
        "legacy_worktree_untracked_count_excluding_step1_outputs": len(untracked_paths),
        "legacy_worktree_untracked_paths_sha256": sha256_bytes("\0".join(sorted(untracked_paths)).encode("utf-8", errors="surrogateescape")),
        "top_level_index": "repo_diff_top_level.csv",
        "note": "The workspace root remains writable only for new rebuttal_work outputs; its three legacy scientific-input roots are recursively filesystem-immutable and never used as an unpinned inclusion source. LEGACY_HEAD_SNAPSHOT is a separate clean sparse reference, not a claim that the workspace is clean.",
    }
    write_json(output / "repo_diff_index.json", repo_diff)

    paper_path = "revised_agent_benchmark_paper.tex"
    paper_blob = git(root, "show", f"{PAPER_SOURCE_COMMIT}:{paper_path}") if object_exists(root, f"{PAPER_SOURCE_COMMIT}:{paper_path}") else b""
    selection_reflog = git(
        root,
        "reflog",
        "show",
        "--date=iso-strict",
        "--format=%H %gD %gs",
        "refs/remotes/origin/neurips-ed-code-release",
    ).decode("utf-8", errors="replace").splitlines()
    evidence_lines = [line for line in selection_reflog if line.startswith(ARTIFACT_COMMIT)]

    lock = {
        "schema_version": "step1_submission_repo_lock/v1",
        "selection_basis": {
            "artifact_execution_commit": artifact_info,
            "artifact_remote_ref_at_audit": "refs/remotes/origin/neurips-ed-code-release",
            "artifact_selection_evidence": evidence_lines,
            "paper_source_commit": paper_info,
            "paper_source_path": paper_path,
            "paper_source_sha256": sha256_bytes(paper_blob) if paper_blob else None,
            "qualification": "The artifact commit is the last locally evidenced push to the public code-release ref; no immutable submission tag or OpenReview-attached archive hash is available locally.",
        },
        "submission_repository": {
            "commit": ARTIFACT_COMMIT,
            "commit_tree_oid": artifact_tree,
            "full_recursive_ls_tree_sha256": sha256_bytes(full_tree_listing),
            "minimal_code_subtree_oid": minimal_tree,
            "paper_result_packages_subtree_oid": package_tree,
            "sparse_snapshot_path": submission_snapshot.relative_to(root).as_posix(),
            "sparse_snapshot_head": submission_head,
            "sparse_snapshot_scope": "minimal code plus all 1,282 decisive raw/native/score/score-manifest/checklist/artifact-manifest files and frozen selectors",
            "new_execution_output_root": execution_root.relative_to(root).as_posix(),
            "output_root_overlaps_locked_snapshots": False,
        },
        "archives": {
            "full_git_archive": {
                "scope": "entire artifact submission commit",
                "command": f"git archive --format=tar --prefix=submission_repo/ {ARTIFACT_COMMIT} | shasum -a 256",
                "sha256": FULL_ARCHIVE_SHA256,
                "materialized": False,
            },
            "minimal_source_archive": {
                "scope": "neurips_ed_track_minimal subtree only",
                "path": code_archive.relative_to(root).as_posix(),
                "sha256": sha256_file(code_archive),
                "materialized": True,
            },
        },
        "paper_source_tree_oid": paper_tree,
        "legacy_repository": {
            "actual_workspace_path": root.as_posix(),
            "head": legacy_info,
            "head_tree_oid": legacy_tree,
            "working_tree_clean_claim": False,
            "access_policy": "the three legacy scientific-input roots are recursively protected by macOS UF_IMMUTABLE (uchg); all generated outputs are confined to rebuttal_work and all inclusion is pinned to submission Git blobs",
            "filesystem_mount_read_only": False,
            "filesystem_immutable_flag": "UF_IMMUTABLE (uchg)",
            "filesystem_immutable_all_entries_verified": True,
            "filesystem_immutable_roots": immutable_roots,
            "clean_sparse_head_snapshot_path": legacy_head_snapshot.relative_to(root).as_posix(),
            "clean_sparse_head_snapshot_head": legacy_snapshot_head,
            "diff_index": "repo_diff_index.json",
        },
        "dependencies": {
            "manifest": "dependency_hashes.csv",
            "exact_lock_present": True,
            "exact_lock_path": "uv.lock",
            "minimal_requirements_is_exact_lock": False,
        },
        "submodules": {"gitmodules_present": object_exists(root, f"{ARTIFACT_COMMIT}:.gitmodules"), "gitlink_count": gitlink_count},
        "large_files": {
            "gitattributes_present_at_submission": object_exists(root, f"{ARTIFACT_COMMIT}:.gitattributes"),
            "lfs_rules_present_at_submission": False,
            "blobs_at_least_100_mib": large_blob_count,
            "note": "Git LFS rules and large VPS/result additions appear only in later legacy commits.",
        },
    }
    write_json(output / "submission_repo_lock.json", lock)

    top_tree = git(root, "ls-tree", ARTIFACT_COMMIT).decode("utf-8", errors="replace")
    with (output / "submission_top_level_tree.txt").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(top_tree)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build(args.root.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
    main()
