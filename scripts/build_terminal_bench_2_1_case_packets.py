#!/usr/bin/env python3
"""Build the frozen Terminal-Bench 2.1@6 full-89 source-rich packets.

The packet is deliberately asymmetric:

* ``agent_input.json`` is the only model-visible file and contains only the
  native task name and instruction.
* ``case_packet.md``, ``case_packet.json`` and ``raw_case/`` are private
  drafter/reviewer/controller inputs.  They include byte-exact UTF-8 task
  sources needed to interpret the native verifier (task config, tests and text
  environment files).
* Oracle ``solution/**`` files are answer keys.  They are never materialized or
  rendered; controller metadata retains only path/hash/size/Harbor reference.
* Binary task assets are not materialized.  Their canonical Harbor hashes,
  byte lengths and package references are retained in ``raw_case_manifest``.
* Packet/checklist drafting is outcome-blind.  Only the generic Harbor artifact
  type inventory is recorded before lock; no job/trial row, trajectory,
  verifier result, reward, or released evaluator label is read or copied.
* One frozen 1,029,394-byte expected-file hash manifest is metadata-only.  Its
  exact Harbor hash and size remain locked, while the verifier code that uses
  it is embedded byte-for-byte.  Repeating all 10,000 expected hashes is not
  necessary to state the decision rule and would exceed the drafter's sealed
  input limit.

The builder accepts either the locked source snapshot tar used for this
repository or an exported source directory produced by ``harbor download``.
It removes macOS AppleDouble records and task-root ``.gitignore`` files (which
are not present in the Harbor packages), and applies one audited 25-byte text
repair to the known Git/Harbor drift in ``sanitize-git-repo``.  The resulting
946-file corpus must match the byte-exact Harbor revision-6 tree hash before
any packet is written.  A verified directory is treated as an alternate
transport of the same logical frozen snapshot, so tar- and directory-backed
builds produce byte-identical packets.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import tarfile
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_TAR = Path("/private/tmp/terminal-bench-2-1-tasks-20260718.tar.gz")
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "experiments/case_packets/terminal_bench_2_1"

BENCHMARK_NAME = "Terminal-Bench"
BENCHMARK_VERSION = "2.1"
DATASET_REVISION = 6
DATASET_REF = "terminal-bench/terminal-bench-2-1@6"
DATASET_PACKAGE = "terminal-bench/terminal-bench-2-1"
DATASET_CONTENT_DIGEST = (
    "sha256:7d7bdc1cbedad549fc1140404bd4dc45e5fd0ea7c4186773687d177ad3a0699a"
)
DATASET_HUB_URL = (
    "https://hub.harborframework.com/datasets/terminal-bench/terminal-bench-2-1/6"
)
OFFICIAL_REPOSITORY = "https://github.com/harbor-framework/terminal-bench-2-1"

EXPECTED_TASK_COUNT = 89
EXPECTED_SOURCE_FILE_COUNT = 946
EXPECTED_SOURCE_TOTAL_BYTES = 58_322_214
EXPECTED_SOURCE_TREE_SHA256 = (
    "fb2afcd61ce43becc7b3f6329cb2f0c2e44b99929442d5bc1aa9c2138078cb55"
)
EXPECTED_DATASET_MANIFEST_SHA256 = (
    "d90b4389992d07ed6f4ab8de963a70241eaa4b60072eeaec4c3b261b6c4a6dd8"
)
EXPECTED_INPUT_SNAPSHOT_SHA256 = (
    "97b7b7fd7281dc3a6714530070608957833c7947d01c9f2206c0379624dc0b7c"
)
EXPECTED_INPUT_SNAPSHOT_SIZE_BYTES = 52_513_239
MAX_OUTPUT_BYTES = 30 * 1024 * 1024

# This is an official evaluator fixture, but its 10,000 concrete expected hash
# values are neither evaluator logic nor useful checklist prose.  Keep this
# exception exact and hash-locked rather than applying a broad size heuristic.
METADATA_ONLY_TEXT_SOURCES = {
    "reshard-c4-data/tests/files_hashes.json": {
        "sha256": "8a6b0c533db960d5534d3ab28ff4c683d6b5bca0a486e9a1921509a14db0e2fb",
        "size_bytes": 1_029_394,
        "reason": (
            "oversized official expected-file hash fixture; exact values are "
            "consumed by embedded verifier code but are not decision logic"
        ),
    }
}

TREE_HASH_METHOD = "sha256(path<TAB>sha256<TAB>size_bytes<LF>), paths sorted UTF-8"
HARBOR_PACKAGE_HASH_METHOD = (
    "sha256(relative_path<NUL>file_sha256<LF>), publishable paths sorted UTF-8"
)
CASE_PACKET_SCHEMA = "terminal_bench_2_1_case_packet/v2"
RAW_MANIFEST_SCHEMA = "terminal_bench_2_1_raw_case_manifest/v1"
SOURCE_LOCK_SCHEMA = "terminal_bench_2_1_source_lock/v2"
INDEX_SCHEMA = "terminal_bench_2_1_case_packet_index/v2"

HARBOR_ARTIFACT_INVENTORY_SOURCE = "https://www.harborframework.com/docs/sharing/jobs"
RETAINED_EXECUTION_ARTIFACT_TYPES = [
    "config.json",
    "lock.json",
    "agent/trajectory.json",
    "agent/*-stdout.txt",
    "agent/*-stderr.txt",
    "verifier/ctrf.json",
    "verifier/test-stdout.txt",
    "verifier/test-stderr.txt",
    "verifier/reports/**",
    "artifacts/**",
]
RELEASED_EVALUATOR_RECORD_TYPES = "result.json; verifier/reward.txt"

# Prior-run identifiers and endpoints are forbidden in generated packet
# metadata. Official task/verifier source naturally contains pass/fail/reward
# terminology, so this deliberately avoids naive scanning of source words.
FORBIDDEN_PRIOR_RUN_URL_MARKERS = (
    "hub.harborframework.com/jobs/",
    "hub.harborframework.com/trials/",
    "tbench.ai/leaderboard/",
)
FORBIDDEN_PRIOR_RUN_METADATA_KEYS = {
    "trial_id",
    "trial_name",
    "job_id",
    "job_uuid",
    "leaderboard_row_id",
    "released_label",
    "released_evaluator_label",
    "released_reward",
    "score_value",
}

CANONICAL_OVERRIDE_PATH = "sanitize-git-repo/tests/test_outputs.py"
DRIFTED_OVERRIDE_SHA256 = (
    "8b3c1094b4628f80fc402c867c21ab5a373f529ad5ae54e49a0a8ac3eb7aae5d"
)
DRIFTED_OVERRIDE_BYTES = 2_712
CANONICAL_OVERRIDE_SHA256 = (
    "57e4904177acac5807b51f7c32444bde1968ba0445855fa4333d9eb73865b59e"
)
CANONICAL_OVERRIDE_BYTES = 2_687
CANONICAL_OVERRIDE_TASK_DIGEST = (
    "sha256:6e86297715fae62cd499fbdd27013e11a38d05d7e05b7f661cb50b4ecead128f"
)
DRIFTED_OVERRIDE_TASK_DIGEST = (
    "sha256:73c94a21ebe370bae843adbeeaaa9e991374867b18483aaf56c7cd470dcddea7"
)
CANONICAL_OVERRIDE_ARCHIVE_REF = (
    "packages/terminal-bench/sanitize-git-repo/"
    "6e86297715fae62cd499fbdd27013e11a38d05d7e05b7f661cb50b4ecead128f/"
    "dist.tar.gz"
)
_JOINED_SECRET_VARIABLES = {
    "FAKE_AWS_ACCESS_KEY_ID",
    "FAKE_AWS_SECRET_ACCESS_KEY",
    "FAKE_GITHUB_TOKEN",
    "FAKE_HUGGINGFACE_TOKEN",
    "FAKE_HUGGINGFACE_TOKEN_2",
}


@dataclass(frozen=True)
class SourceFile:
    task_slug: str
    relative_path: str
    sha256: str
    size_bytes: int
    text: str | None

    @property
    def corpus_path(self) -> str:
        return f"{self.task_slug}/{self.relative_path}"

    @property
    def is_text(self) -> bool:
        return self.text is not None


@dataclass(frozen=True)
class SourceSnapshot:
    files: tuple[SourceFile, ...]
    task_digests: Mapping[str, str]
    input_archive_sha256: str
    input_archive_size_bytes: int
    dataset_manifest_sha256: str


def _metadata_only_text_policy(source: SourceFile) -> Mapping[str, Any] | None:
    policy = METADATA_ONLY_TEXT_SOURCES.get(source.corpus_path)
    if policy is None:
        return None
    if source.text is None:
        raise ValueError(
            f"metadata-only text source is not UTF-8: {source.corpus_path}"
        )
    if source.sha256 != policy["sha256"] or source.size_bytes != policy["size_bytes"]:
        raise ValueError(
            f"metadata-only text source lock mismatch: {source.corpus_path}"
        )
    return policy


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def tree_digest(rows: Iterable[tuple[str, str, int]]) -> tuple[str, int, int]:
    ordered = sorted(rows)
    payload = "".join(
        f"{path}\t{digest}\t{size}\n" for path, digest, size in ordered
    ).encode("utf-8")
    return sha256_bytes(payload), len(ordered), sum(size for _, _, size in ordered)


def filesystem_tree_digest(root: Path) -> tuple[str, int, int]:
    rows: list[tuple[str, str, int]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        rows.append((rel, sha256_file(path), path.stat().st_size))
    return tree_digest(rows)


def harbor_package_digest(files: Iterable[SourceFile]) -> str:
    """Reproduce Harbor ``Packager.compute_content_hash`` for one task."""
    outer = hashlib.sha256()
    for file in sorted(files, key=lambda item: item.relative_path):
        outer.update(f"{file.relative_path}\0{file.sha256}\n".encode("utf-8"))
    return f"sha256:{outer.hexdigest()}"


def _decode_text(data: bytes) -> str | None:
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _canonicalize_known_drift(corpus_path: str, data: bytes) -> bytes:
    if corpus_path != CANONICAL_OVERRIDE_PATH:
        return data
    digest = sha256_bytes(data)
    if digest == CANONICAL_OVERRIDE_SHA256:
        return data
    if digest != DRIFTED_OVERRIDE_SHA256 or len(data) != DRIFTED_OVERRIDE_BYTES:
        raise ValueError(
            f"unrecognized source bytes for {corpus_path}: sha256={digest}, bytes={len(data)}"
        )

    # Harbor rev6 contains the same five explicitly fake canary values as one
    # literal each.  The Git snapshot split each literal into two strings.  Do
    # the narrowly allowlisted source-to-package normalization without storing
    # secret-shaped constants in this build script.
    output: list[str] = []
    changed: set[str] = set()
    pattern = re.compile(r'^([A-Z0-9_]+) = (".*") \+ (".*")$')
    for line in data.decode("utf-8").splitlines(keepends=True):
        body = line[:-1] if line.endswith("\n") else line
        match = pattern.fullmatch(body)
        if match and match.group(1) in _JOINED_SECRET_VARIABLES:
            joined = ast.literal_eval(match.group(2)) + ast.literal_eval(match.group(3))
            replacement = f"{match.group(1)} = {json.dumps(joined)}"
            output.append(replacement + ("\n" if line.endswith("\n") else ""))
            changed.add(match.group(1))
        else:
            output.append(line)
    if changed != _JOINED_SECRET_VARIABLES:
        raise ValueError(
            f"known drift repair touched unexpected variable set: {sorted(changed)}"
        )
    canonical = "".join(output).encode("utf-8")
    if (
        sha256_bytes(canonical) != CANONICAL_OVERRIDE_SHA256
        or len(canonical) != CANONICAL_OVERRIDE_BYTES
    ):
        raise ValueError("known sanitize-git-repo Harbor rev6 repair did not verify")
    return canonical


def _parse_dataset_manifest(data: bytes) -> dict[str, str]:
    digest = sha256_bytes(data)
    if digest != EXPECTED_DATASET_MANIFEST_SHA256:
        raise ValueError(
            "dataset.toml digest mismatch: "
            f"expected {EXPECTED_DATASET_MANIFEST_SHA256}, got {digest}"
        )
    payload = tomllib.loads(data.decode("utf-8"))
    dataset = payload.get("dataset") or {}
    if dataset.get("name") != DATASET_PACKAGE:
        raise ValueError("dataset.toml names a different dataset")
    result: dict[str, str] = {}
    for item in payload.get("tasks") or []:
        name = str(item.get("name") or "")
        digest_value = str(item.get("digest") or "")
        if not name.startswith("terminal-bench/") or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", digest_value
        ):
            raise ValueError(f"invalid task lock in dataset.toml: {item!r}")
        slug = name.removeprefix("terminal-bench/")
        if slug in result:
            raise ValueError(f"duplicate task in dataset.toml: {slug}")
        result[slug] = digest_value
    if len(result) != EXPECTED_TASK_COUNT:
        raise ValueError(
            f"dataset.toml must lock {EXPECTED_TASK_COUNT} tasks, got {len(result)}"
        )
    sanitize_digest = result.get("sanitize-git-repo")
    if sanitize_digest == DRIFTED_OVERRIDE_TASK_DIGEST:
        # The Git snapshot manifest joins its split-literal source revision.
        # Packets join the canonical dataset revision-6 package verified from
        # Harbor, matching the byte repair applied above.
        result["sanitize-git-repo"] = CANONICAL_OVERRIDE_TASK_DIGEST
    elif sanitize_digest != CANONICAL_OVERRIDE_TASK_DIGEST:
        raise ValueError(
            "sanitize-git-repo task digest no longer matches the audited repair"
        )
    return dict(sorted(result.items()))


def _validate_source_records(
    records: Mapping[str, SourceFile],
    locked_task_digests: Mapping[str, str] | None,
) -> dict[str, str]:
    task_slugs = {file.task_slug for file in records.values()}
    if len(task_slugs) != EXPECTED_TASK_COUNT:
        raise ValueError(
            f"source must contain {EXPECTED_TASK_COUNT} task directories, "
            f"got {len(task_slugs)}"
        )
    if locked_task_digests is not None and task_slugs != set(locked_task_digests):
        raise ValueError("source task directories do not match the rev6 dataset lock")

    computed_task_digests: dict[str, str] = {}
    for slug in sorted(task_slugs):
        task_files = [file for file in records.values() if file.task_slug == slug]
        computed_task_digests[slug] = harbor_package_digest(task_files)
    if locked_task_digests is not None:
        for slug, expected_digest in locked_task_digests.items():
            actual_digest = computed_task_digests[slug]
            if actual_digest != expected_digest:
                raise ValueError(
                    f"Harbor package digest mismatch for {slug}: "
                    f"expected {expected_digest}, got {actual_digest}"
                )

    digest, count, total_bytes = tree_digest(
        (file.corpus_path, file.sha256, file.size_bytes) for file in records.values()
    )
    if (digest, count, total_bytes) != (
        EXPECTED_SOURCE_TREE_SHA256,
        EXPECTED_SOURCE_FILE_COUNT,
        EXPECTED_SOURCE_TOTAL_BYTES,
    ):
        raise ValueError(
            "canonical Harbor rev6 source freeze mismatch after normalization: "
            f"sha256={digest}, files={count}, bytes={total_bytes}"
        )
    if computed_task_digests.get("sanitize-git-repo") != CANONICAL_OVERRIDE_TASK_DIGEST:
        raise ValueError("canonical sanitize-git-repo package digest mismatch")
    return dict(sorted(computed_task_digests.items()))


def load_source_snapshot(source_tar: Path) -> SourceSnapshot:
    if not source_tar.is_file():
        raise FileNotFoundError(source_tar)
    archive_sha256 = sha256_file(source_tar)
    archive_size = source_tar.stat().st_size
    if (archive_sha256, archive_size) != (
        EXPECTED_INPUT_SNAPSHOT_SHA256,
        EXPECTED_INPUT_SNAPSHOT_SIZE_BYTES,
    ):
        raise ValueError(
            "locked source tar identity mismatch; use --source-dir for a fresh "
            "Harbor export: "
            f"sha256={archive_sha256}, bytes={archive_size}"
        )
    dataset_manifest: bytes | None = None
    records: dict[str, SourceFile] = {}

    with tarfile.open(source_tar, "r:gz") as archive:
        for member in archive.getmembers():
            name = member.name.removeprefix("./")
            parts = PurePosixPath(name).parts
            if not member.isfile() or not parts:
                continue
            if any(part.startswith("._") for part in parts):
                continue
            if parts == ("tasks", "dataset.toml"):
                handle = archive.extractfile(member)
                if handle is None:
                    raise ValueError("unable to read tasks/dataset.toml")
                dataset_manifest = handle.read()
                continue
            if len(parts) < 3 or parts[0] != "tasks":
                continue
            slug = parts[1]
            relative = PurePosixPath(*parts[2:]).as_posix()
            # Root .gitignore is a repository helper and is excluded by Harbor's
            # task packager.  Nested .gitignore assets remain canonical sources.
            if relative == ".gitignore":
                continue
            corpus_path = f"{slug}/{relative}"
            if corpus_path in records:
                raise ValueError(f"duplicate source file in archive: {corpus_path}")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError(f"unable to read archive member {name}")
            data = _canonicalize_known_drift(corpus_path, handle.read())
            text = _decode_text(data)
            records[corpus_path] = SourceFile(
                task_slug=slug,
                relative_path=relative,
                sha256=sha256_bytes(data),
                size_bytes=len(data),
                text=text,
            )

    if dataset_manifest is None:
        raise ValueError("source tar is missing the locked tasks/dataset.toml")
    task_digests = _validate_source_records(
        records, _parse_dataset_manifest(dataset_manifest)
    )
    return SourceSnapshot(
        files=tuple(sorted(records.values(), key=lambda item: item.corpus_path)),
        task_digests=task_digests,
        input_archive_sha256=archive_sha256,
        input_archive_size_bytes=archive_size,
        dataset_manifest_sha256=sha256_bytes(dataset_manifest),
    )


def _resolve_source_directory(source_dir: Path) -> tuple[Path, Path | None]:
    if not source_dir.is_dir():
        raise NotADirectoryError(source_dir)
    candidates = (
        source_dir / "tasks",
        source_dir / DATASET_PACKAGE.rsplit("/", 1)[-1],
        source_dir,
    )
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen or not candidate.is_dir():
            continue
        seen.add(candidate)
        task_tomls = list(candidate.glob("*/task.toml"))
        if len(task_tomls) == EXPECTED_TASK_COUNT:
            manifest = candidate / "dataset.toml"
            return candidate, manifest if manifest.is_file() else None
    expected = (
        "tasks/dataset.toml + tasks/<slug>/, tasks/<slug>/, or the Harbor "
        "export layout terminal-bench-2-1/<slug>/"
    )
    raise ValueError(f"unable to locate the 89-task source tree; expected {expected}")


def load_source_directory(source_dir: Path) -> SourceSnapshot:
    tasks_root, manifest_path = _resolve_source_directory(source_dir)
    records: dict[str, SourceFile] = {}
    task_dirs = sorted(path.parent for path in tasks_root.glob("*/task.toml"))
    for task_dir in task_dirs:
        slug = task_dir.name
        for path in sorted(task_dir.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"source directory contains a symlink: {path}")
            if not path.is_file():
                continue
            relative_path = path.relative_to(task_dir)
            if any(part.startswith("._") for part in relative_path.parts):
                continue
            relative = relative_path.as_posix()
            if relative == ".gitignore":
                continue
            corpus_path = f"{slug}/{relative}"
            if corpus_path in records:
                raise ValueError(f"duplicate source file in directory: {corpus_path}")
            data = _canonicalize_known_drift(corpus_path, path.read_bytes())
            records[corpus_path] = SourceFile(
                task_slug=slug,
                relative_path=relative,
                sha256=sha256_bytes(data),
                size_bytes=len(data),
                text=_decode_text(data),
            )

    locked_task_digests: Mapping[str, str] | None = None
    if manifest_path is not None:
        manifest_data = manifest_path.read_bytes()
        locked_task_digests = _parse_dataset_manifest(manifest_data)
        manifest_sha256 = sha256_bytes(manifest_data)
    else:
        # Harbor's export layout intentionally contains task packages only.
        # The exact corpus tree lock below proves membership in the same rev6
        # dataset; retain the logical dataset-manifest identity for deterministic
        # packet provenance across tar and directory transports.
        manifest_sha256 = EXPECTED_DATASET_MANIFEST_SHA256
    task_digests = _validate_source_records(records, locked_task_digests)
    return SourceSnapshot(
        files=tuple(sorted(records.values(), key=lambda item: item.corpus_path)),
        task_digests=task_digests,
        input_archive_sha256=EXPECTED_INPUT_SNAPSHOT_SHA256,
        input_archive_size_bytes=EXPECTED_INPUT_SNAPSHOT_SIZE_BYTES,
        dataset_manifest_sha256=manifest_sha256,
    )


def source_ref(task_slug: str, relative_path: str, task_digest: str) -> str:
    return f"harbor://terminal-bench/{task_slug}@{task_digest}/{relative_path}"


def _markdown_language(path: str) -> str:
    name = PurePosixPath(path).name.lower()
    suffix = PurePosixPath(path).suffix.lower()
    if name == "dockerfile":
        return "dockerfile"
    languages = {
        ".c": "c",
        ".cc": "cpp",
        ".cpp": "cpp",
        ".css": "css",
        ".go": "go",
        ".html": "html",
        ".java": "java",
        ".js": "javascript",
        ".json": "json",
        ".md": "markdown",
        ".py": "python",
        ".rs": "rust",
        ".sh": "bash",
        ".sql": "sql",
        ".toml": "toml",
        ".ts": "typescript",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return languages.get(suffix, "text")


def _fenced(text: str, language: str = "text") -> list[str]:
    longest = max(
        (len(match.group(0)) for match in re.finditer(r"`+", text)), default=0
    )
    fence = "`" * max(3, longest + 1)
    return [f"{fence}{language}", text.rstrip("\n"), fence]


def _files_for_task(snapshot: SourceSnapshot, slug: str) -> list[SourceFile]:
    return [file for file in snapshot.files if file.task_slug == slug]


def _task_config(files: Iterable[SourceFile]) -> dict[str, Any]:
    task_toml = next(file for file in files if file.relative_path == "task.toml")
    if task_toml.text is None:
        raise ValueError(f"{task_toml.corpus_path} is not UTF-8 text")
    return tomllib.loads(task_toml.text)


def _instruction(files: Iterable[SourceFile]) -> str:
    instruction = next(file for file in files if file.relative_path == "instruction.md")
    if instruction.text is None:
        raise ValueError(f"{instruction.corpus_path} is not UTF-8 text")
    return instruction.text


def _validate_task_source(
    slug: str, files: list[SourceFile], task_digest: str
) -> dict[str, Any]:
    required = {
        "instruction.md",
        "task.toml",
        "README.md",
        "tests/test.sh",
        "solution/solve.sh",
        "environment/Dockerfile",
    }
    paths = {file.relative_path for file in files}
    missing = required - paths
    if missing:
        raise ValueError(f"task {slug} is missing required sources: {sorted(missing)}")
    config = _task_config(files)
    if config.get("schema_version") != "1.1":
        raise ValueError(f"task {slug} has unexpected task schema")
    task = config.get("task") or {}
    if task.get("name") != f"terminal-bench/{slug}":
        raise ValueError(f"task {slug} has mismatched task.name")
    if not isinstance(config.get("verifier"), Mapping):
        raise ValueError(f"task {slug} has no verifier config")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", task_digest):
        raise ValueError(f"task {slug} has invalid Harbor digest")
    return config


def _task_tree_stats(files: Iterable[SourceFile]) -> tuple[str, int, int]:
    return tree_digest(
        (file.relative_path, file.sha256, file.size_bytes) for file in files
    )


def _source_lock(snapshot: SourceSnapshot) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    for slug, task_digest in snapshot.task_digests.items():
        files = _files_for_task(snapshot, slug)
        config = _validate_task_source(slug, files, task_digest)
        tree_sha, file_count, total_bytes = _task_tree_stats(files)
        text_files = [
            file
            for file in files
            if file.is_text
            and not file.relative_path.startswith("solution/")
            and _metadata_only_text_policy(file) is None
        ]
        metadata_only_text_files = [
            file for file in files if _metadata_only_text_policy(file) is not None
        ]
        protected_solution_files = [
            file for file in files if file.relative_path.startswith("solution/")
        ]
        binary_files = [
            file
            for file in files
            if not file.is_text and not file.relative_path.startswith("solution/")
        ]
        category = str((config.get("metadata") or {}).get("category") or "unknown")
        category_counts[category] += 1
        entries.append(
            {
                "case_unit_id": slug,
                "task_name": f"terminal-bench/{slug}",
                "task_digest": task_digest,
                "harbor_task_package_digest": task_digest,
                "harbor_package_content_hash_verified": True,
                "harbor_package_hash_method": HARBOR_PACKAGE_HASH_METHOD,
                "source_tree_sha256": tree_sha,
                "source_file_count": file_count,
                "source_total_bytes": total_bytes,
                "materialized_text_file_count": len(text_files),
                "materialized_text_total_bytes": sum(
                    file.size_bytes for file in text_files
                ),
                "metadata_only_text_file_count": len(metadata_only_text_files),
                "metadata_only_text_total_bytes": sum(
                    file.size_bytes for file in metadata_only_text_files
                ),
                "protected_solution_file_count": len(protected_solution_files),
                "protected_solution_total_bytes": sum(
                    file.size_bytes for file in protected_solution_files
                ),
                "external_binary_file_count": len(binary_files),
                "external_binary_total_bytes": sum(
                    file.size_bytes for file in binary_files
                ),
                "instruction_sha256": next(
                    file.sha256
                    for file in files
                    if file.relative_path == "instruction.md"
                ),
                "task_config_sha256": next(
                    file.sha256 for file in files if file.relative_path == "task.toml"
                ),
                "category": category,
            }
        )
    core = {
        "schema_version": SOURCE_LOCK_SCHEMA,
        "status": "frozen_pre_outcome_case_source",
        "benchmark": BENCHMARK_NAME,
        "version": BENCHMARK_VERSION,
        "split": "full",
        "dataset_ref": DATASET_REF,
        "dataset_revision": DATASET_REVISION,
        "dataset_content_digest": DATASET_CONTENT_DIGEST,
        "dataset_hub_url": DATASET_HUB_URL,
        "official_repository": OFFICIAL_REPOSITORY,
        "canonical_download_command": (
            "harbor download terminal-bench/terminal-bench-2-1@6 "
            "--output-dir <SOURCE_DIR>"
        ),
        "tree_hash_method": TREE_HASH_METHOD,
        "harbor_package_hash_method": HARBOR_PACKAGE_HASH_METHOD,
        "canonical_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
        "canonical_source_file_count": EXPECTED_SOURCE_FILE_COUNT,
        "canonical_source_total_bytes": EXPECTED_SOURCE_TOTAL_BYTES,
        "task_count": len(entries),
        "category_counts": dict(sorted(category_counts.items())),
        "input_snapshot": {
            "format": "tar.gz",
            "sha256": snapshot.input_archive_sha256,
            "size_bytes": snapshot.input_archive_size_bytes,
            "dataset_manifest_sha256": snapshot.dataset_manifest_sha256,
            "ignored_entries": [
                "macOS AppleDouble entries (any path component prefixed ._)",
                "task-root .gitignore files excluded by Harbor packaging",
                "dataset-level README.md (not task source)",
            ],
        },
        "canonicalization_overrides": [
            {
                "path": CANONICAL_OVERRIDE_PATH,
                "reason": "known Git snapshot versus Harbor revision-6 package drift",
                "input_sha256": DRIFTED_OVERRIDE_SHA256,
                "input_size_bytes": DRIFTED_OVERRIDE_BYTES,
                "canonical_sha256": CANONICAL_OVERRIDE_SHA256,
                "canonical_size_bytes": CANONICAL_OVERRIDE_BYTES,
                "verified_harbor_task_digest": CANONICAL_OVERRIDE_TASK_DIGEST,
                "input_snapshot_task_digest": DRIFTED_OVERRIDE_TASK_DIGEST,
                "verified_harbor_archive_ref": CANONICAL_OVERRIDE_ARCHIVE_REF,
                "archive_fetch_policy": "in-memory verification only; archive not retained",
            }
        ],
        "binary_asset_policy": (
            "hash_and_harbor_reference_only; binary bytes are not copied into packets"
        ),
        "metadata_only_text_policy": {
            "mode": "exact_hash_locked_allowlist",
            "sources": METADATA_ONLY_TEXT_SOURCES,
        },
        "artifact_inventory_contract": {
            "source_ref": HARBOR_ARTIFACT_INVENTORY_SOURCE,
            "available_per_run_types": [
                *RETAINED_EXECUTION_ARTIFACT_TYPES,
                "result.json",
                "verifier/reward.txt",
            ],
            "inventory_only_pre_lock": True,
            "per_record_bytes_or_values_read_during_packet_generation": False,
        },
        "blind_generation_contract": {
            "allowed_inputs": [
                "official Harbor terminal-bench/terminal-bench-2-1@6 task packages",
                "official revision-6 dataset manifest",
                "generic Harbor artifact-type documentation",
            ],
            "forbidden_inputs": [
                "leaderboard rows",
                "job or trial index rows",
                "agent trajectories or logs",
                "per-run artifacts",
                "per-run verifier outputs",
                "released evaluator labels, results, or rewards",
            ],
            "packet_bytes_depend_only_on_allowed_inputs": True,
        },
        "solution_policy": (
            "controller_metadata_only; solution bytes are not copied or rendered"
        ),
        "entries": entries,
    }
    result = dict(core)
    result["source_lock_core_sha256"] = sha256_bytes(canonical_bytes(core))
    return result


def _controller_packet(
    *,
    slug: str,
    task_digest: str,
    files: list[SourceFile],
    config: Mapping[str, Any],
    instruction: str,
    agent_input_sha256: str,
    source_lock_entry: Mapping[str, Any],
    input_snapshot_sha256: str,
) -> dict[str, Any]:
    tests = [
        file.relative_path for file in files if file.relative_path.startswith("tests/")
    ]
    solution = [
        file.relative_path
        for file in files
        if file.relative_path.startswith("solution/")
    ]
    environment = [
        file.relative_path
        for file in files
        if file.relative_path.startswith("environment/")
    ]
    binary = [
        file.relative_path
        for file in files
        if not file.is_text and not file.relative_path.startswith("solution/")
    ]
    metadata_only_text = [
        file.relative_path
        for file in files
        if _metadata_only_text_policy(file) is not None
    ]
    packet = {
        "schema_version": CASE_PACKET_SCHEMA,
        "benchmark": {
            "name": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
            "split": "full",
            "dataset_ref": DATASET_REF,
            "dataset_revision": DATASET_REVISION,
            "dataset_content_digest": DATASET_CONTENT_DIGEST,
            "dataset_hub_url": DATASET_HUB_URL,
            "official_repository": OFFICIAL_REPOSITORY,
        },
        "task": {
            "case_unit_id": slug,
            "task_id": f"terminal-bench/{slug}",
            "task_name": f"terminal-bench/{slug}",
            "task_digest": task_digest,
            "harbor_task_package_digest": task_digest,
            "instruction": instruction,
            "instruction_sha256": source_lock_entry["instruction_sha256"],
            "task_config": dict(config),
            "task_config_sha256": source_lock_entry["task_config_sha256"],
        },
        "model_visible_input": {
            "path": "agent_input.json",
            "sha256": agent_input_sha256,
            "field_allowlist": ["instruction", "task_name"],
        },
        "evaluator_reference": {
            "visibility": "drafter_reviewer_and_controller_only",
            "verifier_entrypoint": "raw_case/official/tests/test.sh",
            "oracle_solution_source_path": "solution/solve.sh",
            "oracle_solution_materialized": False,
            "task_config_path": "raw_case/official/task.toml",
            "test_source_paths": tests,
            "solution_source_paths": solution,
            "environment_source_paths": environment,
            "external_binary_source_paths": binary,
            "native_reward_artifact": "/logs/verifier/reward.txt",
            "native_test_report_artifact": "/logs/verifier/ctrf.json",
            "verifier_timeout_sec": (config.get("verifier") or {}).get("timeout_sec"),
        },
        "checklist_design_contract": {
            "native_layer": (
                "draft only from official task/user intent and the released evaluator/oracle "
                "semantics; evidence scoring independently asks whether retained execution "
                "evidence establishes native success, native failure, or is undecidable"
            ),
            "stronger_measurement_layer": (
                "official case-specific requirements with source support that exceed the "
                "released native criterion are recorded separately and never silently added "
                "to native success/failure"
            ),
            "unsupported_reviewer_requirements": "excluded from checklist and scoring",
            "released_label_visibility_during_drafting": "forbidden",
            "released_label_visibility_during_evidence_scoring": "forbidden",
            "released_label_use": "post-score comparison only",
            "disagreement_semantics": (
                "a native-evidence/released-label disagreement triggers record review but is "
                "not itself a confirmed benchmark conflict"
            ),
        },
        "artifact_inventory": {
            "inventory_known_pre_lock": True,
            "per_record_contents_or_values_in_packet": False,
            "retained_execution_artifact_types": RETAINED_EXECUTION_ARTIFACT_TYPES,
            "released_evaluator_record_type_retained_post_run": (
                RELEASED_EVALUATOR_RECORD_TYPES
            ),
            "released_evaluator_value_available_to_packet_or_scorer": False,
            "source_ref": HARBOR_ARTIFACT_INVENTORY_SOURCE,
        },
        "provenance": {
            "dataset_ref": DATASET_REF,
            "dataset_content_digest": DATASET_CONTENT_DIGEST,
            "task_digest": task_digest,
            "task_source_tree_sha256": source_lock_entry["source_tree_sha256"],
            "tree_hash_method": TREE_HASH_METHOD,
            "input_snapshot_sha256": input_snapshot_sha256,
            "canonical_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
        },
        "leakage_control": {
            "policy": "allowlist_only_outcome_blind_v1",
            "model_receives_only_agent_input_json": True,
            "tests_verifier_solution_excluded_from_model_input": True,
            "binary_assets_excluded_from_packet_bytes": True,
            "oracle_solution_bytes_excluded_from_packet": True,
            "prior_run_records_excluded_from_packet_generation": True,
            "released_evaluator_results_excluded_from_packet_generation": True,
        },
        "visibility": "controller_and_human_review_only",
    }
    if metadata_only_text:
        packet["evaluator_reference"]["metadata_only_text_source_paths"] = (
            metadata_only_text
        )
        packet["leakage_control"][
            "oversized_fixture_values_excluded_from_packet_bytes"
        ] = True
    return packet


def _materialize_raw_case(
    *,
    case_dir: Path,
    slug: str,
    task_digest: str,
    files: list[SourceFile],
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    raw_root = case_dir / "raw_case"
    copied: list[str] = []
    file_sources: dict[str, str] = {}
    source_files: list[dict[str, Any]] = []
    for source in files:
        reference = source_ref(slug, source.relative_path, task_digest)
        materialized: str | None = None
        is_solution = source.relative_path.startswith("solution/")
        metadata_only_policy = _metadata_only_text_policy(source)
        representation = (
            "controller_metadata_hash_only_solution"
            if is_solution
            else (
                "official_text_hash_only_oversized_fixture_manifest"
                if metadata_only_policy is not None
                else "external_binary_hash_only"
            )
        )
        if source.text is not None and not is_solution and metadata_only_policy is None:
            materialized = f"official/{source.relative_path}"
            destination = raw_root / materialized
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Encode the already verified text rather than copying from an
            # extraction tree, preserving canonical bytes and avoiding raw assets.
            destination.write_bytes(source.text.encode("utf-8"))
            if sha256_file(destination) != source.sha256:
                raise ValueError(
                    f"materialized text hash mismatch for {slug}/{source.relative_path}"
                )
            copied.append(materialized)
            file_sources[materialized] = reference
            representation = "byte_exact_utf8_text"
        source_files.append(
            {
                "source_path": source.relative_path,
                "materialized_path": materialized,
                "representation": representation,
                "sha256": source.sha256,
                "size_bytes": source.size_bytes,
                "source_ref": reference,
                **(
                    {"metadata_only_reason": metadata_only_policy["reason"]}
                    if metadata_only_policy is not None
                    else {}
                ),
            }
        )
    copied.sort()
    source_files.sort(key=lambda item: str(item["source_path"]))
    raw_tree_sha, raw_count, raw_bytes = filesystem_tree_digest(raw_root)
    source_tree_sha, source_count, source_bytes = tree_digest(
        (
            str(item["source_path"]),
            str(item["sha256"]),
            int(item["size_bytes"]),
        )
        for item in source_files
    )
    metadata_only_text_files = [
        item
        for item in source_files
        if item["representation"]
        == "official_text_hash_only_oversized_fixture_manifest"
    ]
    manifest = {
        "schema_version": RAW_MANIFEST_SCHEMA,
        "domain": "terminal_bench_2_1",
        "case_unit_id": slug,
        "task_id": f"terminal-bench/{slug}",
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_ref": DATASET_REF,
        "dataset_revision": DATASET_REVISION,
        "dataset_content_digest": DATASET_CONTENT_DIGEST,
        "task_digest": task_digest,
        "harbor_task_package_digest": task_digest,
        "tree_hash_method": TREE_HASH_METHOD,
        "source_tree_sha256": source_tree_sha,
        "source_file_count": source_count,
        "source_total_bytes": source_bytes,
        "raw_case_tree_sha256": raw_tree_sha,
        "raw_case_file_count": raw_count,
        "raw_case_total_bytes": raw_bytes,
        "copied_files": copied,
        "official_files": copied,
        "derived_files": [],
        "packet_files": copied,
        "sha256_per_file": {
            item["materialized_path"]: item["sha256"]
            for item in source_files
            if item["materialized_path"] is not None
        },
        "size_bytes_per_file": {
            item["materialized_path"]: item["size_bytes"]
            for item in source_files
            if item["materialized_path"] is not None
        },
        "file_sources": dict(sorted(file_sources.items())),
        "source_files": source_files,
        "external_binary_files": [
            item
            for item in source_files
            if item["representation"] == "external_binary_hash_only"
        ],
        "controller_metadata_only_files": [
            item
            for item in source_files
            if item["representation"] == "controller_metadata_hash_only_solution"
        ],
        "source_refs": sorted({str(item["source_ref"]) for item in source_files}),
        "model_visible_files": ["agent_input.json"],
        "drafter_reviewer_only_files": [
            "case_packet.md",
            "raw_case_manifest.json",
            "raw_case/**",
        ],
        "controller_runtime_files": ["case_packet.json"],
        "top_level_file_sha256": {
            "agent_input.json": sha256_file(case_dir / "agent_input.json"),
            "case_packet.json": sha256_file(case_dir / "case_packet.json"),
        },
        "binary_asset_policy": "hash_and_harbor_reference_only",
        "solution_policy": "controller_metadata_only_no_bytes",
    }
    if metadata_only_text_files:
        manifest["metadata_only_text_files"] = metadata_only_text_files
        manifest["metadata_only_text_policy"] = "exact_hash_locked_allowlist"
    return manifest


def _render_packet(
    *, packet: Mapping[str, Any], raw_manifest: Mapping[str, Any], raw_root: Path
) -> str:
    task = packet["task"]
    config = task["task_config"]
    metadata = config.get("metadata") or {}
    environment = config.get("environment") or {}
    lines = [
        "# Case Packet",
        "",
        "## Case Metadata",
        "",
        "- domain: `terminal_bench_2_1`",
        f"- case_unit_id: `{task['case_unit_id']}`",
        f"- task_id: `{task['task_id']}`",
        f"- task digest: `{task['task_digest']}`",
        f"- dataset: `{DATASET_REF}`",
        f"- dataset content digest: `{DATASET_CONTENT_DIGEST}`",
        f"- source tree SHA-256: `{raw_manifest['source_tree_sha256']}`",
        "",
        "## Benchmark Task Summary",
        "",
        f"- description: {(config.get('task') or {}).get('description', '')}",
        f"- category: `{metadata.get('category', 'unknown')}`",
        f"- difficulty: `{metadata.get('difficulty', 'unknown')}`",
        f"- verifier timeout seconds: `{(config.get('verifier') or {}).get('timeout_sec')}`",
        f"- agent timeout seconds: `{(config.get('agent') or {}).get('timeout_sec')}`",
        f"- container image reference: `{environment.get('docker_image', '')}`",
        "",
        "### Native agent-visible instruction",
        "",
        *_fenced(str(task["instruction"]), "markdown"),
        "",
        "## Measurement Boundary",
        "",
        "This packet is a pre-outcome checklist input. It contains no agent outcome,",
        "per-record trajectory, per-record verifier result, or released evaluator label.",
        "",
        "Native checklist conditions must follow the official task and released evaluator",
        "or oracle semantics in the retained source. Official case-specific requirements",
        "that exceed what the native evaluator operationalizes belong in a separate",
        "`stronger_measurement` layer. Requirements supported only by reviewer intuition",
        "are excluded from both checklist and scoring. Stronger failure is not benchmark",
        "error, and native-evidence/released-label disagreement is only a review trigger",
        "unless retained artifacts prove that the benchmark actually evaluated a different",
        "claimed outcome.",
        "",
        "## Native Evaluator Semantics",
        "",
        "- task-specific verifier entry point: `official/tests/test.sh`",
        "- exact evaluator/test sources: see `evaluator_reference.test_source_paths` in",
        "  `case_packet.json` and the complete Source Inventory below.",
        "- native success: the task-specific official verifier criterion is established by",
        "  retained execution evidence.",
        "- native failure: violation of that same task-specific criterion is established by",
        "  retained execution evidence.",
        "- undecidable (`U`): retained evidence is insufficient to establish either claim.",
        "- released reward/result values are unavailable during drafting and evidence",
        "  scoring; they are compared only after the independent verdict is fixed.",
        "",
        "No benchmark-wide predicate is invented here: each checklist must be derived from",
        "the case's exact instruction, task config, verifier/tests, and supported oracle",
        "semantics retained in this packet.",
        "",
        "## Available Artifact Inventory (types only; no per-record values)",
        "",
        *(
            f"- `{artifact_type}`"
            for artifact_type in packet["artifact_inventory"][
                "retained_execution_artifact_types"
            ]
        ),
        "- released evaluator records retained after execution: "
        f"`{packet['artifact_inventory']['released_evaluator_record_type_retained_post_run']}`",
        "",
        "## Visibility Boundary",
        "",
        "This source-rich packet is only for checklist drafting and human review. The",
        "tested agent receives only `agent_input.json`. Tests, verifier code, oracle",
        "solution metadata, task config, environment sources, artifact inventory, and this",
        "packet must not be placed in the tested agent prompt or workspace.",
        "",
        "## Source Inventory",
        "",
    ]
    for relative in raw_manifest["packet_files"]:
        lines.append(f"- `{relative}`")
    lines.extend(
        [
            "",
            "## Source Inventory Summary",
            "",
            f"- canonical source files: `{raw_manifest['source_file_count']}`",
            f"- byte-exact UTF-8 files materialized: `{raw_manifest['raw_case_file_count']}`",
            f"- external binary hash-only files: `{len(raw_manifest['external_binary_files'])}`",
            *(
                [
                    "- oversized official text fixtures represented by exact "
                    f"hash metadata only: `{len(raw_manifest['metadata_only_text_files'])}`"
                ]
                if raw_manifest.get("metadata_only_text_files")
                else []
            ),
            f"- protected solution metadata-only files: `{len(raw_manifest['controller_metadata_only_files'])}`",
            f"- canonical task source bytes: `{raw_manifest['source_total_bytes']}`",
            f"- materialized text bytes: `{raw_manifest['raw_case_total_bytes']}`",
            "",
        ]
    )
    if raw_manifest["external_binary_files"]:
        lines.extend(["### External binary assets (not copied)", ""])
        for item in raw_manifest["external_binary_files"]:
            lines.append(
                f"- `{item['source_path']}` — `{item['size_bytes']}` bytes, "
                f"SHA-256 `{item['sha256']}`, ref `{item['source_ref']}`"
            )
        lines.append("")
    if raw_manifest.get("metadata_only_text_files"):
        lines.extend(
            [
                "### Oversized official text fixtures (exact hash metadata only)",
                "",
                "These fixture values are consumed by the embedded verifier but are not",
                "the verifier logic. Their exact official bytes remain bound by path,",
                "size, SHA-256, task digest and Harbor reference.",
                "",
            ]
        )
        for item in raw_manifest["metadata_only_text_files"]:
            lines.append(
                f"- `{item['source_path']}` — `{item['size_bytes']}` bytes, "
                f"SHA-256 `{item['sha256']}`, ref `{item['source_ref']}`; "
                f"reason: {item['metadata_only_reason']}"
            )
        lines.append("")
    if raw_manifest["controller_metadata_only_files"]:
        lines.extend(
            ["### Protected oracle solution metadata (answer-key bytes not copied)", ""]
        )
        for item in raw_manifest["controller_metadata_only_files"]:
            lines.append(
                f"- `{item['source_path']}` — present, `{item['size_bytes']}` bytes, "
                f"SHA-256 `{item['sha256']}`, ref `{item['source_ref']}`"
            )
        lines.append("")
    lines.extend(["## Packet Source Files", ""])
    for relative in raw_manifest["packet_files"]:
        path = raw_root / str(relative)
        text = path.read_text(encoding="utf-8")
        lines.extend(
            [
                f"### `{relative}`",
                "",
                f"Source ref: `{raw_manifest['file_sources'][relative]}`",
                "",
                *_fenced(text, _markdown_language(str(relative))),
                "",
            ]
        )
    lines.extend(
        [
            "## Raw Source Provenance",
            "",
            *_fenced(
                json.dumps(raw_manifest, ensure_ascii=False, indent=2, sort_keys=True),
                "json",
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _agent_input_tree_digest(
    output_root: Path, slugs: Iterable[str]
) -> tuple[str, int, int]:
    rows = []
    for slug in sorted(slugs):
        path = output_root / slug / "agent_input.json"
        rows.append(
            (f"{slug}/agent_input.json", sha256_file(path), path.stat().st_size)
        )
    return tree_digest(rows)


def build_packets(
    source_tar: Path | None,
    output_root: Path,
    source_dir: Path | None = None,
) -> dict[str, Any]:
    if (source_tar is None) == (source_dir is None):
        raise ValueError("provide exactly one of source_tar or source_dir")
    snapshot = (
        load_source_snapshot(source_tar)
        if source_tar is not None
        else load_source_directory(source_dir)  # type: ignore[arg-type]
    )
    source_lock = _source_lock(snapshot)
    lock_entries = {
        str(entry["case_unit_id"]): entry for entry in source_lock["entries"]
    }
    staging = output_root.with_name(f".{output_root.name}.staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        write_json(staging / "source_lock.json", source_lock)
        source_lock_sha = sha256_file(staging / "source_lock.json")
        (staging / "source_lock.json.sha256").write_text(
            f"{source_lock_sha}  source_lock.json\n", encoding="utf-8"
        )

        entries: list[dict[str, Any]] = []
        for slug, task_digest in snapshot.task_digests.items():
            files = _files_for_task(snapshot, slug)
            config = _validate_task_source(slug, files, task_digest)
            instruction = _instruction(files)
            case_dir = staging / slug
            case_dir.mkdir()
            agent_input = {
                "instruction": instruction,
                "task_name": f"terminal-bench/{slug}",
            }
            write_json(case_dir / "agent_input.json", agent_input)
            agent_input_sha = sha256_file(case_dir / "agent_input.json")
            packet = _controller_packet(
                slug=slug,
                task_digest=task_digest,
                files=files,
                config=config,
                instruction=instruction,
                agent_input_sha256=agent_input_sha,
                source_lock_entry=lock_entries[slug],
                input_snapshot_sha256=snapshot.input_archive_sha256,
            )
            write_json(case_dir / "case_packet.json", packet)
            raw_manifest = _materialize_raw_case(
                case_dir=case_dir,
                slug=slug,
                task_digest=task_digest,
                files=files,
                packet=packet,
            )
            write_json(case_dir / "raw_case_manifest.json", raw_manifest)
            (case_dir / "case_packet.md").write_text(
                _render_packet(
                    packet=packet,
                    raw_manifest=raw_manifest,
                    raw_root=case_dir / "raw_case",
                ),
                encoding="utf-8",
            )
            entries.append(
                {
                    "case_unit_id": slug,
                    "task_name": f"terminal-bench/{slug}",
                    "task_digest": task_digest,
                    "source_tree_sha256": raw_manifest["source_tree_sha256"],
                    "source_file_count": raw_manifest["source_file_count"],
                    "source_total_bytes": raw_manifest["source_total_bytes"],
                    "materialized_text_file_count": raw_manifest["raw_case_file_count"],
                    "materialized_text_total_bytes": raw_manifest[
                        "raw_case_total_bytes"
                    ],
                    "external_binary_file_count": len(
                        raw_manifest["external_binary_files"]
                    ),
                    "metadata_only_text_file_count": len(
                        raw_manifest.get("metadata_only_text_files", [])
                    ),
                    "protected_solution_file_count": len(
                        raw_manifest["controller_metadata_only_files"]
                    ),
                    "agent_input_sha256": agent_input_sha,
                    "case_packet_json_sha256": sha256_file(
                        case_dir / "case_packet.json"
                    ),
                    "case_packet_markdown_sha256": sha256_file(
                        case_dir / "case_packet.md"
                    ),
                    "raw_case_manifest_sha256": sha256_file(
                        case_dir / "raw_case_manifest.json"
                    ),
                    "raw_case_tree_sha256": raw_manifest["raw_case_tree_sha256"],
                }
            )

        agent_tree_sha, agent_count, agent_bytes = _agent_input_tree_digest(
            staging, snapshot.task_digests
        )
        index_core = {
            "schema_version": INDEX_SCHEMA,
            "status": "frozen",
            "benchmark": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
            "split": "full",
            "dataset_ref": DATASET_REF,
            "dataset_revision": DATASET_REVISION,
            "dataset_content_digest": DATASET_CONTENT_DIGEST,
            "dataset_hub_url": DATASET_HUB_URL,
            "canonical_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
            "source_lock_path": "source_lock.json",
            "source_lock_sha256": source_lock_sha,
            "canonical_packet_filename": "case_packet.md",
            "packet_visibility": "drafter_and_reviewer_only",
            "model_visible_files_per_case": ["agent_input.json"],
            "binary_asset_policy": "hash_and_harbor_reference_only",
            "solution_policy": "controller_metadata_only_no_bytes",
            "packet_count": len(entries),
            "agent_input_tree_sha256": agent_tree_sha,
            "agent_input_file_count": agent_count,
            "agent_input_total_bytes": agent_bytes,
            "entries": entries,
        }
        index = dict(index_core)
        index["index_core_sha256"] = sha256_bytes(canonical_bytes(index_core))
        write_json(staging / "index.json", index)
        index_sha = sha256_file(staging / "index.json")
        (staging / "index.json.sha256").write_text(
            f"{index_sha}  index.json\n", encoding="utf-8"
        )
        summary = validate_output(staging)
        if output_root.exists():
            shutil.rmtree(output_root)
        staging.rename(output_root)
        return summary
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _source_inventory_paths(markdown: str) -> list[str]:
    if markdown.splitlines().count("## Source Inventory") != 1:
        raise ValueError("packet must contain exactly one Source Inventory heading")
    paths: list[str] = []
    in_inventory = False
    for line in markdown.splitlines():
        if line == "## Source Inventory":
            in_inventory = True
            continue
        if in_inventory and line.startswith("## "):
            break
        if not in_inventory or not line.strip():
            continue
        match = re.fullmatch(r"- `([^`]+)`", line.strip())
        if match is None:
            raise ValueError(f"non-parser-compatible Source Inventory line: {line!r}")
        paths.append(match.group(1).replace("\\", "/"))
    if not paths:
        raise ValueError("packet has no parseable Source Inventory entries")
    if len(paths) != len(set(paths)):
        raise ValueError("packet Source Inventory contains duplicate paths")
    return paths


def _walk_metadata_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_metadata_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_metadata_keys(child)


def _assert_outcome_blind_generated_metadata(
    *, packet: Mapping[str, Any], manifest: Mapping[str, Any], markdown: str, slug: str
) -> None:
    keys = set(_walk_metadata_keys(packet)) | set(_walk_metadata_keys(manifest))
    forbidden_keys = keys & FORBIDDEN_PRIOR_RUN_METADATA_KEYS
    if forbidden_keys:
        raise ValueError(
            f"case {slug} generated metadata contains prior-run keys: {sorted(forbidden_keys)}"
        )
    generated_text = (
        json.dumps(packet, ensure_ascii=False, sort_keys=True)
        + json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        + markdown
    ).lower()
    for marker in FORBIDDEN_PRIOR_RUN_URL_MARKERS:
        if marker in generated_text:
            raise ValueError(
                f"case {slug} packet leaks prior-run URL marker {marker!r}"
            )


def validate_output(output_root: Path) -> dict[str, Any]:
    if not output_root.is_dir():
        raise FileNotFoundError(output_root)
    lock_path = output_root / "source_lock.json"
    index_path = output_root / "index.json"
    source_lock = _load_json(lock_path)
    index = _load_json(index_path)
    if source_lock.get("schema_version") != SOURCE_LOCK_SCHEMA:
        raise ValueError("unexpected source lock schema")
    if index.get("schema_version") != INDEX_SCHEMA:
        raise ValueError("unexpected packet index schema")
    if source_lock.get("canonical_source_tree_sha256") != EXPECTED_SOURCE_TREE_SHA256:
        raise ValueError("source lock does not name the frozen Harbor rev6 tree")
    if int(source_lock.get("task_count", -1)) != EXPECTED_TASK_COUNT:
        raise ValueError("source lock task count mismatch")
    artifact_contract = source_lock.get("artifact_inventory_contract") or {}
    if (
        artifact_contract.get(
            "per_record_bytes_or_values_read_during_packet_generation"
        )
        is not False
    ):
        raise ValueError("source lock does not enforce outcome-blind artifact access")
    blind_contract = source_lock.get("blind_generation_contract") or {}
    if blind_contract.get("packet_bytes_depend_only_on_allowed_inputs") is not True:
        raise ValueError("source lock does not bind packet bytes to allowed inputs")
    if index.get("source_lock_sha256") != sha256_file(lock_path):
        raise ValueError("index source_lock_sha256 mismatch")
    index_core = dict(index)
    claimed_index_core = str(index_core.pop("index_core_sha256", ""))
    if claimed_index_core != sha256_bytes(canonical_bytes(index_core)):
        raise ValueError("index core digest mismatch")
    lock_core = dict(source_lock)
    claimed_lock_core = str(lock_core.pop("source_lock_core_sha256", ""))
    if claimed_lock_core != sha256_bytes(canonical_bytes(lock_core)):
        raise ValueError("source lock core digest mismatch")
    expected_root_names = {
        "index.json",
        "index.json.sha256",
        "source_lock.json",
        "source_lock.json.sha256",
        *(str(entry["case_unit_id"]) for entry in index.get("entries") or []),
    }
    actual_root_names = {path.name for path in output_root.iterdir()}
    if actual_root_names != expected_root_names:
        raise ValueError(
            f"output root inventory mismatch: missing={sorted(expected_root_names-actual_root_names)}, "
            f"extra={sorted(actual_root_names-expected_root_names)}"
        )
    entries = list(index.get("entries") or [])
    if len(entries) != EXPECTED_TASK_COUNT:
        raise ValueError("packet index must contain exactly 89 entries")
    lock_by_slug = {
        str(entry["case_unit_id"]): entry for entry in source_lock.get("entries") or []
    }
    corpus_rows: list[tuple[str, str, int]] = []
    binary_count = 0
    metadata_only_text_count = 0
    solution_metadata_count = 0
    materialized_count = 0
    materialized_bytes = 0
    harbor_package_verified_count = 0
    for entry in entries:
        slug = str(entry["case_unit_id"])
        case_dir = output_root / slug
        required = {
            "agent_input.json",
            "case_packet.json",
            "case_packet.md",
            "raw_case_manifest.json",
            "raw_case",
        }
        if {path.name for path in case_dir.iterdir()} != required:
            raise ValueError(f"case {slug} top-level inventory mismatch")
        for filename, field in (
            ("agent_input.json", "agent_input_sha256"),
            ("case_packet.json", "case_packet_json_sha256"),
            ("case_packet.md", "case_packet_markdown_sha256"),
            ("raw_case_manifest.json", "raw_case_manifest_sha256"),
        ):
            if sha256_file(case_dir / filename) != entry[field]:
                raise ValueError(f"case {slug} hash mismatch for {filename}")
        agent_input = _load_json(case_dir / "agent_input.json")
        if set(agent_input) != {"instruction", "task_name"}:
            raise ValueError(f"case {slug} agent input violates the field allowlist")
        if agent_input["task_name"] != f"terminal-bench/{slug}":
            raise ValueError(f"case {slug} agent input task name mismatch")
        packet = _load_json(case_dir / "case_packet.json")
        packet_markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
        source_inventory_paths = _source_inventory_paths(packet_markdown)
        if packet.get("schema_version") != CASE_PACKET_SCHEMA:
            raise ValueError(f"case {slug} controller packet schema mismatch")
        if packet["model_visible_input"]["sha256"] != entry["agent_input_sha256"]:
            raise ValueError(f"case {slug} model-visible hash mismatch")
        if packet["task"]["instruction"] != agent_input["instruction"]:
            raise ValueError(f"case {slug} instruction mismatch")
        if packet["task"]["task_digest"] != entry["task_digest"]:
            raise ValueError(f"case {slug} task digest join mismatch")
        raw = _load_json(case_dir / "raw_case_manifest.json")
        if raw.get("schema_version") != RAW_MANIFEST_SCHEMA:
            raise ValueError(f"case {slug} raw manifest schema mismatch")
        if raw.get("task_digest") != entry["task_digest"]:
            raise ValueError(f"case {slug} raw manifest task digest join mismatch")
        checklist_contract = packet.get("checklist_design_contract") or {}
        if (
            checklist_contract.get("released_label_visibility_during_drafting")
            != "forbidden"
            or checklist_contract.get(
                "released_label_visibility_during_evidence_scoring"
            )
            != "forbidden"
            or checklist_contract.get("released_label_use")
            != "post-score comparison only"
        ):
            raise ValueError(f"case {slug} checklist outcome-blind contract mismatch")
        artifact_inventory = packet.get("artifact_inventory") or {}
        if (
            artifact_inventory.get("inventory_known_pre_lock") is not True
            or artifact_inventory.get("per_record_contents_or_values_in_packet")
            is not False
            or artifact_inventory.get(
                "released_evaluator_value_available_to_packet_or_scorer"
            )
            is not False
            or artifact_inventory.get("retained_execution_artifact_types")
            != RETAINED_EXECUTION_ARTIFACT_TYPES
        ):
            raise ValueError(f"case {slug} artifact inventory boundary mismatch")
        leakage = packet.get("leakage_control") or {}
        if (
            leakage.get("prior_run_records_excluded_from_packet_generation") is not True
            or leakage.get("released_evaluator_results_excluded_from_packet_generation")
            is not True
        ):
            raise ValueError(f"case {slug} prior-run leakage boundary mismatch")
        _assert_outcome_blind_generated_metadata(
            packet=packet, manifest=raw, markdown=packet_markdown, slug=slug
        )
        actual_raw = sorted(
            path.relative_to(case_dir / "raw_case").as_posix()
            for path in (case_dir / "raw_case").rglob("*")
            if path.is_file()
        )
        if actual_raw != sorted(raw.get("copied_files") or []):
            raise ValueError(f"case {slug} copied_files inventory mismatch")
        if actual_raw != sorted(raw.get("official_files") or []):
            raise ValueError(f"case {slug} official_files inventory mismatch")
        if actual_raw != sorted(raw.get("packet_files") or []):
            raise ValueError(f"case {slug} packet_files inventory mismatch")
        if source_inventory_paths != actual_raw:
            raise ValueError(f"case {slug} Markdown Source Inventory mismatch")
        if any(path.startswith("official/solution/") for path in actual_raw):
            raise ValueError(
                f"case {slug} materializes protected oracle solution bytes"
            )
        raw_tree = filesystem_tree_digest(case_dir / "raw_case")
        if raw_tree != (
            raw["raw_case_tree_sha256"],
            raw["raw_case_file_count"],
            raw["raw_case_total_bytes"],
        ):
            raise ValueError(f"case {slug} raw text tree mismatch")
        for relative in actual_raw:
            path = case_dir / "raw_case" / relative
            if sha256_file(path) != raw["sha256_per_file"][relative]:
                raise ValueError(f"case {slug} raw file hash mismatch: {relative}")
            if path.stat().st_size != raw["size_bytes_per_file"][relative]:
                raise ValueError(f"case {slug} raw file size mismatch: {relative}")
        source_files = list(raw.get("source_files") or [])
        if len(source_files) != int(raw["source_file_count"]):
            raise ValueError(f"case {slug} full source inventory count mismatch")
        expected_metadata_only = [
            item
            for item in source_files
            if item.get("representation")
            == "official_text_hash_only_oversized_fixture_manifest"
        ]
        if raw.get("metadata_only_text_files", []) != expected_metadata_only:
            raise ValueError(f"case {slug} metadata-only text inventory mismatch")
        if bool(expected_metadata_only) != (
            raw.get("metadata_only_text_policy") == "exact_hash_locked_allowlist"
        ):
            raise ValueError(f"case {slug} metadata-only text policy mismatch")
        seen: set[str] = set()
        for item in source_files:
            source_path = str(item["source_path"])
            if source_path in seen:
                raise ValueError(f"case {slug} duplicate source path {source_path}")
            seen.add(source_path)
            corpus_rows.append(
                (f"{slug}/{source_path}", str(item["sha256"]), int(item["size_bytes"]))
            )
            materialized = item.get("materialized_path")
            if source_path.startswith("solution/") and materialized is not None:
                raise ValueError(f"case {slug} exposes protected solution source")
            if materialized is None:
                if item["representation"] == "external_binary_hash_only":
                    binary_count += 1
                elif (
                    item["representation"]
                    == "official_text_hash_only_oversized_fixture_manifest"
                ):
                    policy = METADATA_ONLY_TEXT_SOURCES.get(f"{slug}/{source_path}")
                    if policy is None:
                        raise ValueError(
                            f"case {slug} has unapproved metadata-only text source {source_path}"
                        )
                    if (
                        item["sha256"] != policy["sha256"]
                        or int(item["size_bytes"]) != policy["size_bytes"]
                        or item.get("metadata_only_reason") != policy["reason"]
                    ):
                        raise ValueError(
                            f"case {slug} metadata-only text source lock mismatch: {source_path}"
                        )
                    metadata_only_text_count += 1
                elif item["representation"] == "controller_metadata_hash_only_solution":
                    solution_metadata_count += 1
                else:
                    raise ValueError(
                        f"case {slug} has unknown non-materialized representation"
                    )
                if (case_dir / "raw_case" / source_path).exists():
                    raise ValueError(
                        f"case {slug} protected source was unexpectedly copied"
                    )
            else:
                materialized_count += 1
                materialized_bytes += int(item["size_bytes"])
        full_tree = tree_digest(
            (str(item["source_path"]), str(item["sha256"]), int(item["size_bytes"]))
            for item in source_files
        )
        if full_tree != (
            raw["source_tree_sha256"],
            raw["source_file_count"],
            raw["source_total_bytes"],
        ):
            raise ValueError(f"case {slug} full source tree mismatch")
        if raw["source_tree_sha256"] != lock_by_slug[slug]["source_tree_sha256"]:
            raise ValueError(f"case {slug} source lock join mismatch")
        harbor_outer = hashlib.sha256()
        for item in sorted(source_files, key=lambda value: str(value["source_path"])):
            harbor_outer.update(
                f"{item['source_path']}\0{item['sha256']}\n".encode("utf-8")
            )
        reconstructed_task_digest = f"sha256:{harbor_outer.hexdigest()}"
        if reconstructed_task_digest != entry["task_digest"]:
            raise ValueError(
                f"case {slug} Harbor package digest reconstruction mismatch"
            )
        harbor_package_verified_count += 1
    corpus_tree = tree_digest(corpus_rows)
    if corpus_tree != (
        EXPECTED_SOURCE_TREE_SHA256,
        EXPECTED_SOURCE_FILE_COUNT,
        EXPECTED_SOURCE_TOTAL_BYTES,
    ):
        raise ValueError(f"reconstructed canonical corpus mismatch: {corpus_tree}")
    agent_tree = _agent_input_tree_digest(output_root, lock_by_slug)
    if agent_tree != (
        index["agent_input_tree_sha256"],
        index["agent_input_file_count"],
        index["agent_input_total_bytes"],
    ):
        raise ValueError("agent-input tree mismatch")
    if (output_root / "source_lock.json.sha256").read_text(encoding="utf-8") != (
        f"{sha256_file(lock_path)}  source_lock.json\n"
    ):
        raise ValueError("source lock checksum sidecar mismatch")
    if (output_root / "index.json.sha256").read_text(encoding="utf-8") != (
        f"{sha256_file(index_path)}  index.json\n"
    ):
        raise ValueError("index checksum sidecar mismatch")
    output_bytes = sum(
        path.stat().st_size for path in output_root.rglob("*") if path.is_file()
    )
    if output_bytes > MAX_OUTPUT_BYTES:
        raise ValueError(
            f"packet tree exceeds 30 MiB safety cap: {output_bytes} > {MAX_OUTPUT_BYTES}"
        )
    return {
        "status": "ok",
        "packet_count": len(entries),
        "canonical_source_tree_sha256": corpus_tree[0],
        "canonical_source_file_count": corpus_tree[1],
        "canonical_source_total_bytes": corpus_tree[2],
        "materialized_text_file_count": materialized_count,
        "materialized_text_total_bytes": materialized_bytes,
        "external_binary_file_count": binary_count,
        "metadata_only_text_file_count": metadata_only_text_count,
        "protected_solution_file_count": solution_metadata_count,
        "harbor_package_digest_verified_count": harbor_package_verified_count,
        "agent_input_tree_sha256": agent_tree[0],
        "outcome_blind_generation": True,
        "output_total_bytes": output_bytes,
        "output_limit_bytes": MAX_OUTPUT_BYTES,
        "index_sha256": sha256_file(index_path),
        "source_lock_sha256": sha256_file(lock_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Fresh Harbor export (no packing step required):\n"
            "  harbor download terminal-bench/terminal-bench-2-1@6 "
            "--output-dir <SOURCE_DIR>\n"
            "  python scripts/build_terminal_bench_2_1_case_packets.py "
            "--source-dir <SOURCE_DIR>\n\n"
            "--source-dir accepts <SOURCE_DIR>/terminal-bench-2-1/<slug>/ "
            "(Harbor export), <SOURCE_DIR>/tasks/<slug>/ with optional "
            "tasks/dataset.toml, or the task-root directory itself."
        ),
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--source-tar",
        type=Path,
        help=(
            "locked task-source tar containing tasks/dataset.toml and tasks/<slug>/; "
            f"defaults to {DEFAULT_SOURCE_TAR} when neither source option is given"
        ),
    )
    source_group.add_argument(
        "--source-dir",
        type=Path,
        help="Harbor export or source tree containing all 89 task directories",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate an existing output tree without reading the source tar",
    )
    args = parser.parse_args()
    if args.validate_only:
        summary = validate_output(args.output_root.resolve())
    else:
        source_tar = args.source_tar
        if source_tar is None and args.source_dir is None:
            source_tar = DEFAULT_SOURCE_TAR
        summary = build_packets(
            source_tar.resolve() if source_tar is not None else None,
            args.output_root.resolve(),
            args.source_dir.resolve() if args.source_dir is not None else None,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
