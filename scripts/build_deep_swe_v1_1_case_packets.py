#!/usr/bin/env python3
"""Build and validate the frozen DeepSWE v1.1 full-113 case packets.

The builder is deliberately outcome-blind.  Its only inputs are the official
DeepSWE v1.1 task tree and the release documentation that describes the
available run-artifact types.  It never reads the DeepSWE trial index,
leaderboard, trajectories, model patches, verifier results, or released labels.

Each case directory has the same visibility split used by the other benchmark
corpora in this repository:

* ``agent_input.json`` is the sole model-visible file and contains only the
  official task name and instruction.
* ``case_packet.json``, ``case_packet.md``, and ``raw_case/`` are private
  checklist-drafting/reviewer/controller inputs.
* Official task, environment, artifact-capture, test, verifier, and grader
  sources are retained byte-for-byte.  ``tests/config.json`` is also retained
  byte-for-byte, but the Markdown packet renders a deterministic projection so
  very large pass-to-pass node-id inventories do not crowd out the case-specific
  decision semantics.
* ``solution/**`` is a reference answer and is not used by the released grader.
  Solution bytes are never copied or rendered; path/hash/size/source metadata is
  retained for provenance only.

The source lock pins the task tree introduced by the official ``DeepSWE V1.1``
commit and the immediately following README update.  Later official commits
have the identical task-tree Git object, so an exported worktree with the exact
same bytes is accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "experiments/case_packets/deep_swe_v1_1"

BENCHMARK_NAME = "DeepSWE"
BENCHMARK_VERSION = "1.1"
BENCHMARK_SPLIT = "full"
DATASET_NAME = "datacurve/deep-swe-1-1"
DATASET_REF = (
    "github:datacurve-ai/deep-swe@" "3cda4081fed96103a6395de39c85e9b20275e307#tasks"
)
OFFICIAL_REPOSITORY = "https://github.com/datacurve-ai/deep-swe"
V1_1_TASK_COMMIT = "8cae5984d5dd0ee37445beff0e928dc10c331116"
V1_1_DOCUMENTED_COMMIT = "3cda4081fed96103a6395de39c85e9b20275e307"
V1_1_TASKS_GIT_TREE_OID = "891e2975cd842071f62e567c3b11cae7362bf065"
V1_1_README_SHA256 = "d2cfb8c9cfa05e710c1abc83c0068c09762e4d0dd290cf10c17dae400eebfe27"
V1_1_README_SIZE_BYTES = 3_601
DATASET_MANIFEST_SHA256 = (
    "546dc070d1f4349c08d8cf8e616e2488c5dbe212f8cc02eb7f50207cbe10f4b2"
)
DATASET_MANIFEST_SIZE_BYTES = 16_644

EXPECTED_TASK_COUNT = 113
EXPECTED_SOURCE_FILE_COUNT = 1_243
EXPECTED_SOURCE_TOTAL_BYTES = 30_394_474
EXPECTED_SOURCE_TREE_SHA256 = (
    "ea99ceca8751014c27a78d9a57d1243d87c2588fc92968eadf25787c4ed8689b"
)
EXPECTED_SHARED_GRADER_SHA256 = (
    "47cc9eaadf21e636323c360ec4fa786f0733ec9fd1d21ea5a5717ff9f8c4077c"
)
EXPECTED_SHARED_SOLVE_SHA256 = (
    "2f111d19625d9685d00029c2c3efb7719ee2311c6ab4f0ab0ebcc37f09c35198"
)
MAX_OUTPUT_BYTES = 80 * 1024 * 1024

TREE_HASH_METHOD = "sha256(path<TAB>sha256<TAB>size_bytes<LF>), paths sorted UTF-8"
PIER_LOCAL_TASK_HASH_METHOD = (
    "sha256(relative_path<NUL>raw_file_bytes<NUL>), all non-.git files sorted UTF-8"
)
NODE_ID_LIST_HASH_METHOD = "sha256(canonical compact JSON UTF-8 list)"

CASE_PACKET_SCHEMA = "deep_swe_v1_1_case_packet/v1"
RAW_MANIFEST_SCHEMA = "deep_swe_v1_1_raw_case_manifest/v1"
SOURCE_LOCK_SCHEMA = "deep_swe_v1_1_source_lock/v1"
INDEX_SCHEMA = "deep_swe_v1_1_case_packet_index/v1"
EVALUATOR_PROJECTION_SCHEMA = "deep_swe_v1_1_evaluator_projection/v1"

REQUIRED_TASK_FILES = {
    "instruction.md",
    "task.toml",
    "pre_artifacts.sh",
    "environment/Dockerfile",
    "tests/Dockerfile",
    "tests/config.json",
    "tests/grader.py",
    "tests/test.sh",
    "tests/test.patch",
    "solution/solve.sh",
    "solution/solution.patch",
}

# These are prior-run data classes, not source-level words.  Official verifier
# files naturally contain words such as reward/pass/fail, so the boundary is
# enforced on generated provenance values and external URLs rather than by a
# naive text search over evaluator code.
FORBIDDEN_PRIOR_RUN_URL_MARKERS = (
    "deepswe.datacurve.ai/data/",
    "deepswe.datacurve.ai/artifacts/",
    "d3ujjcmjq6o8v6.cloudfront.net",
    "/trial-artifacts/",
)
FORBIDDEN_PRIOR_RUN_METADATA_KEYS = {
    "trial_name",
    "released_label",
    "released_evaluator_label",
    "outcome",
    "passed",
    "errored",
    "score_value",
    "model_name",
    "reasoning_effort",
}


class BuildError(RuntimeError):
    """Raised when a source or generated packet invariant is violated."""


@dataclass(frozen=True)
class SourceFile:
    task_slug: str
    relative_path: str
    sha256: str
    size_bytes: int
    text: str
    data: bytes

    @property
    def corpus_path(self) -> str:
        return f"{self.task_slug}/{self.relative_path}"


@dataclass(frozen=True)
class SourceSnapshot:
    tasks_root: Path
    files: tuple[SourceFile, ...]
    manifest_task_digests: Mapping[str, str]
    dataset_manifest_sha256: str
    transport: Mapping[str, Any]


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
        relative = path.relative_to(root).as_posix()
        rows.append((relative, sha256_file(path), path.stat().st_size))
    return tree_digest(rows)


def _git_output(repo: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def _locate_tasks_root(source_dir: Path) -> tuple[Path, Path | None]:
    source_dir = source_dir.resolve()
    candidates = (source_dir / "tasks", source_dir)
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        if (candidate / "dataset.toml").is_file() and len(
            list(candidate.glob("*/task.toml"))
        ) == EXPECTED_TASK_COUNT:
            repo_root = candidate.parent if candidate.name == "tasks" else None
            return candidate, repo_root
    raise BuildError(
        "unable to locate the DeepSWE v1.1 tasks tree; expected "
        "<source>/tasks/dataset.toml or <source>/dataset.toml with 113 task directories"
    )


def _parse_dataset_manifest(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    if (sha256_bytes(data), len(data)) != (
        DATASET_MANIFEST_SHA256,
        DATASET_MANIFEST_SIZE_BYTES,
    ):
        raise BuildError(
            "DeepSWE v1.1 dataset.toml identity mismatch: "
            f"sha256={sha256_bytes(data)}, bytes={len(data)}"
        )
    payload = tomllib.loads(data.decode("utf-8"))
    dataset = payload.get("dataset") or {}
    if dataset.get("name") != DATASET_NAME:
        raise BuildError("dataset.toml names a different DeepSWE dataset")
    result: dict[str, str] = {}
    for item in payload.get("tasks") or []:
        name = str(item.get("name") or "")
        digest = str(item.get("digest") or "")
        if not name.startswith("datacurve/") or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", digest
        ):
            raise BuildError(f"invalid dataset task entry: {item!r}")
        slug = name.removeprefix("datacurve/")
        if slug in result:
            raise BuildError(f"duplicate dataset task entry: {slug}")
        result[slug] = digest
    if len(result) != EXPECTED_TASK_COUNT:
        raise BuildError(
            f"dataset.toml must contain {EXPECTED_TASK_COUNT} tasks, got {len(result)}"
        )
    return dict(sorted(result.items()))


def _pier_local_task_digest(files: Iterable[SourceFile]) -> str:
    digest = hashlib.sha256()
    for source in sorted(files, key=lambda item: item.relative_path):
        digest.update(source.relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(source.data)
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _task_tree_stats(files: Iterable[SourceFile]) -> tuple[str, int, int]:
    return tree_digest(
        (source.relative_path, source.sha256, source.size_bytes) for source in files
    )


def _files_for_task(snapshot: SourceSnapshot, slug: str) -> list[SourceFile]:
    return [source for source in snapshot.files if source.task_slug == slug]


def _file_by_path(files: Iterable[SourceFile], relative_path: str) -> SourceFile:
    try:
        return next(source for source in files if source.relative_path == relative_path)
    except StopIteration as exc:
        raise BuildError(f"task source missing {relative_path}") from exc


def _task_config(files: Iterable[SourceFile]) -> dict[str, Any]:
    return tomllib.loads(_file_by_path(files, "task.toml").text)


def _grader_config(files: Iterable[SourceFile]) -> dict[str, Any]:
    value = json.loads(_file_by_path(files, "tests/config.json").text)
    if not isinstance(value, dict):
        raise BuildError("tests/config.json must contain an object")
    return value


def _validate_task_source(
    slug: str, files: Sequence[SourceFile], manifest_digest: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = {source.relative_path for source in files}
    if paths != REQUIRED_TASK_FILES:
        raise BuildError(
            f"task {slug} source inventory mismatch: "
            f"missing={sorted(REQUIRED_TASK_FILES-paths)}, "
            f"extra={sorted(paths-REQUIRED_TASK_FILES)}"
        )
    config = _task_config(files)
    if config.get("schema_version") != "1.1":
        raise BuildError(f"task {slug} has unexpected task schema")
    task = config.get("task") or {}
    metadata = config.get("metadata") or {}
    if task.get("name") != f"datacurve/{slug}":
        raise BuildError(f"task {slug} task.name mismatch")
    if metadata.get("task_id") != slug:
        raise BuildError(f"task {slug} metadata.task_id mismatch")
    # The official corpus contains two abbreviated seven-character Git SHAs and
    # one 39-character value in addition to full 40-character SHAs.  Preserve
    # those source bytes and require only Git's unambiguous hexadecimal form;
    # the grader config must still match the task metadata exactly below.
    if not re.fullmatch(r"[0-9a-f]{7,40}", str(metadata.get("base_commit_hash") or "")):
        raise BuildError(f"task {slug} has invalid base commit")
    if (config.get("verifier") or {}).get("environment_mode") != "separate":
        raise BuildError(f"task {slug} must use the separate verifier environment")
    if config.get("artifacts") != ["/logs/artifacts/model.patch"]:
        raise BuildError(f"task {slug} has unexpected artifact declaration")
    if str(manifest_digest) == "":
        raise BuildError(f"task {slug} has no dataset manifest digest")
    if _file_by_path(files, "tests/grader.py").sha256 != EXPECTED_SHARED_GRADER_SHA256:
        raise BuildError(f"task {slug} shared grader identity mismatch")
    if _file_by_path(files, "solution/solve.sh").sha256 != EXPECTED_SHARED_SOLVE_SHA256:
        raise BuildError(f"task {slug} shared oracle wrapper identity mismatch")

    grader = _grader_config(files)
    required_grader_keys = {"base_commit", "f2p_node_ids", "p2p_node_ids", "grade"}
    if set(grader) != required_grader_keys:
        raise BuildError(f"task {slug} grader config keys mismatch")
    if grader["base_commit"] != metadata["base_commit_hash"]:
        raise BuildError(f"task {slug} grader/base commit mismatch")
    for key in ("f2p_node_ids", "p2p_node_ids"):
        values = grader.get(key)
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(item, str) and item.strip() for item in values)
        ):
            raise BuildError(f"task {slug} has invalid {key}")
        if len(values) != len(set(values)):
            raise BuildError(f"task {slug} has duplicate {key}")
    grade = grader.get("grade") or {}
    if grade.get("format") not in {"ctrf", "junit"}:
        raise BuildError(f"task {slug} has unsupported report format")
    if not isinstance(grade.get("reports"), list) or not grade["reports"]:
        raise BuildError(f"task {slug} has no grader report paths")
    return config, grader


def load_source_directory(source_dir: Path) -> SourceSnapshot:
    tasks_root, repo_root = _locate_tasks_root(source_dir)
    manifest_digests = _parse_dataset_manifest(tasks_root / "dataset.toml")
    records: list[SourceFile] = []
    task_dirs = sorted(path.parent for path in tasks_root.glob("*/task.toml"))
    if {path.name for path in task_dirs} != set(manifest_digests):
        raise BuildError("task directories do not match dataset.toml membership")
    for task_dir in task_dirs:
        slug = task_dir.name
        for path in sorted(task_dir.rglob("*")):
            if path.is_symlink():
                raise BuildError(f"task source contains a symlink: {path}")
            if not path.is_file():
                continue
            relative = path.relative_to(task_dir).as_posix()
            data = path.read_bytes()
            if b"\0" in data:
                raise BuildError(
                    f"DeepSWE v1.1 task source is unexpectedly binary: {slug}/{relative}"
                )
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise BuildError(
                    f"task source is not UTF-8: {slug}/{relative}"
                ) from exc
            records.append(
                SourceFile(
                    task_slug=slug,
                    relative_path=relative,
                    sha256=sha256_bytes(data),
                    size_bytes=len(data),
                    text=text,
                    data=data,
                )
            )
    corpus = tree_digest(
        (source.corpus_path, source.sha256, source.size_bytes) for source in records
    )
    if corpus != (
        EXPECTED_SOURCE_TREE_SHA256,
        EXPECTED_SOURCE_FILE_COUNT,
        EXPECTED_SOURCE_TOTAL_BYTES,
    ):
        raise BuildError(
            "DeepSWE v1.1 official task-tree freeze mismatch: "
            f"sha256={corpus[0]}, files={corpus[1]}, bytes={corpus[2]}"
        )
    transport: dict[str, Any] = {
        "format": "verified_source_directory",
        "canonical_tasks_git_tree_oid": V1_1_TASKS_GIT_TREE_OID,
    }
    if repo_root is not None and (repo_root / ".git").exists():
        observed_tree = _git_output(repo_root, "rev-parse", "HEAD:tasks")
        if observed_tree != V1_1_TASKS_GIT_TREE_OID:
            raise BuildError(
                f"source repository HEAD:tasks mismatch: observed {observed_tree!r}"
            )
        readme = repo_root / "README.md"
        if not readme.is_file() or (sha256_file(readme), readme.stat().st_size) != (
            V1_1_README_SHA256,
            V1_1_README_SIZE_BYTES,
        ):
            raise BuildError("official v1.1 README identity mismatch")
        transport.update(
            {
                "observed_head_commit": _git_output(repo_root, "rev-parse", "HEAD"),
                "observed_head_tasks_tree_oid": observed_tree,
                "readme_sha256_verified": True,
            }
        )
    snapshot = SourceSnapshot(
        tasks_root=tasks_root,
        files=tuple(sorted(records, key=lambda item: item.corpus_path)),
        manifest_task_digests=manifest_digests,
        dataset_manifest_sha256=DATASET_MANIFEST_SHA256,
        transport=transport,
    )
    for slug, digest in manifest_digests.items():
        _validate_task_source(slug, _files_for_task(snapshot, slug), digest)
    return snapshot


def source_ref(slug: str, relative_path: str) -> str:
    return (
        "github://datacurve-ai/deep-swe@"
        f"{V1_1_DOCUMENTED_COMMIT}/tasks/{slug}/{relative_path}"
    )


def documentation_ref(relative_path: str) -> str:
    return "github://datacurve-ai/deep-swe@" f"{V1_1_DOCUMENTED_COMMIT}/{relative_path}"


def _markdown_language(path: str) -> str:
    name = PurePosixPath(path).name.lower()
    suffix = PurePosixPath(path).suffix.lower()
    if name == "dockerfile":
        return "dockerfile"
    return {
        ".json": "json",
        ".md": "markdown",
        ".patch": "diff",
        ".py": "python",
        ".sh": "bash",
        ".toml": "toml",
    }.get(suffix, "text")


def _fenced(text: str, language: str = "text") -> list[str]:
    longest = max(
        (len(match.group(0)) for match in re.finditer(r"`+", text)), default=0
    )
    fence = "`" * max(3, longest + 1)
    return [f"{fence}{language}", text.rstrip("\n"), fence]


def _node_list_sha256(values: Sequence[str]) -> str:
    return sha256_bytes(canonical_bytes(list(values)))


def _evaluator_projection(
    *, slug: str, grader: Mapping[str, Any], config_source: SourceFile
) -> dict[str, Any]:
    f2p = list(grader["f2p_node_ids"])
    p2p = list(grader["p2p_node_ids"])
    return {
        "schema_version": EVALUATOR_PROJECTION_SCHEMA,
        "case_unit_id": slug,
        "source": {
            "path": "official/tests/config.json",
            "source_ref": source_ref(slug, "tests/config.json"),
            "sha256": config_source.sha256,
            "size_bytes": config_source.size_bytes,
        },
        "base_commit": grader["base_commit"],
        "grade": dict(grader["grade"]),
        "native_test_sets": {
            "fail_to_pass": {
                "count": len(f2p),
                "node_ids": f2p,
                "node_ids_sha256": _node_list_sha256(f2p),
            },
            "pass_to_pass": {
                "count": len(p2p),
                "node_ids_sha256": _node_list_sha256(p2p),
                "node_ids_materialized_in_projection": False,
                "full_node_ids_path": "official/tests/config.json",
            },
        },
        "native_decision_rule": {
            "success": (
                "fail_to_pass is non-empty; every configured fail-to-pass node passes; "
                "and no configured pass-to-pass node fails"
            ),
            "failure": (
                "any configured fail-to-pass node is missing, skipped, or failed; or any "
                "configured pass-to-pass node is missing, skipped, or failed"
            ),
            "missing_or_skipped_test": "counts as failed",
            "duplicate_node_id": "worst status wins: passed < skipped < failed",
            "source_paths": [
                "official/tests/grader.py",
                "official/tests/config.json",
                "official/tests/test.sh",
            ],
        },
        "projection_policy": {
            "mechanical": True,
            "p2p_node_ids_omitted_from_markdown_projection": True,
            "reason": (
                "the complete official config is retained byte-for-byte; only the repeated "
                "pass-to-pass identifier inventory is hash/count represented in the compact "
                "drafter projection"
            ),
            "node_id_list_hash_method": NODE_ID_LIST_HASH_METHOD,
        },
    }


def _source_lock(snapshot: SourceSnapshot) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    language_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    manifest_digest_matches = 0
    for slug, manifest_digest in snapshot.manifest_task_digests.items():
        files = _files_for_task(snapshot, slug)
        config, grader = _validate_task_source(slug, files, manifest_digest)
        metadata = config["metadata"]
        language_counts[str(metadata["language"])] += 1
        category_counts[str(metadata["category"])] += 1
        task_tree = _task_tree_stats(files)
        pier_digest = _pier_local_task_digest(files)
        # dataset.toml was authored for Harbor publication, whereas official
        # leaderboard runs use Pier over the local task path.  Preserve both
        # identities without pretending the two hash namespaces are equal.
        if pier_digest == manifest_digest:
            manifest_digest_matches += 1
        solution_files = [
            source for source in files if source.relative_path.startswith("solution/")
        ]
        retained_files = [
            source
            for source in files
            if not source.relative_path.startswith("solution/")
        ]
        grader_config = _file_by_path(files, "tests/config.json")
        entries.append(
            {
                "case_unit_id": slug,
                "task_name": f"datacurve/{slug}",
                "dataset_manifest_task_digest": manifest_digest,
                "pier_local_task_digest": pier_digest,
                "pier_local_task_hash_method": PIER_LOCAL_TASK_HASH_METHOD,
                "source_tree_sha256": task_tree[0],
                "source_file_count": task_tree[1],
                "source_total_bytes": task_tree[2],
                "retained_official_file_count": len(retained_files),
                "retained_official_total_bytes": sum(
                    source.size_bytes for source in retained_files
                ),
                "protected_solution_file_count": len(solution_files),
                "protected_solution_total_bytes": sum(
                    source.size_bytes for source in solution_files
                ),
                "instruction_sha256": _file_by_path(files, "instruction.md").sha256,
                "task_config_sha256": _file_by_path(files, "task.toml").sha256,
                "grader_config_sha256": grader_config.sha256,
                "grader_config_size_bytes": grader_config.size_bytes,
                "f2p_node_id_count": len(grader["f2p_node_ids"]),
                "p2p_node_id_count": len(grader["p2p_node_ids"]),
                "language": metadata["language"],
                "category": metadata["category"],
                "repository_url": metadata["repository_url"],
                "base_commit_hash": metadata["base_commit_hash"],
            }
        )
    core = {
        "schema_version": SOURCE_LOCK_SCHEMA,
        "status": "frozen_pre_outcome_case_source",
        "benchmark": BENCHMARK_NAME,
        "version": BENCHMARK_VERSION,
        "split": BENCHMARK_SPLIT,
        "dataset_name": DATASET_NAME,
        "dataset_ref": DATASET_REF,
        "official_repository": OFFICIAL_REPOSITORY,
        "official_source": {
            "v1_1_task_commit": V1_1_TASK_COMMIT,
            "v1_1_documented_commit": V1_1_DOCUMENTED_COMMIT,
            "tasks_git_tree_oid": V1_1_TASKS_GIT_TREE_OID,
            "readme_sha256": V1_1_README_SHA256,
            "readme_size_bytes": V1_1_README_SIZE_BYTES,
            "readme_source_ref": documentation_ref("README.md"),
            "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
            "dataset_manifest_size_bytes": DATASET_MANIFEST_SIZE_BYTES,
        },
        "canonical_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
        "canonical_source_file_count": EXPECTED_SOURCE_FILE_COUNT,
        "canonical_source_total_bytes": EXPECTED_SOURCE_TOTAL_BYTES,
        "tree_hash_method": TREE_HASH_METHOD,
        "pier_local_task_hash_method": PIER_LOCAL_TASK_HASH_METHOD,
        "task_count": len(entries),
        "language_counts": dict(sorted(language_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "source_transport": dict(snapshot.transport),
        "dataset_manifest_digest_semantics": {
            "namespace": "Harbor publication metadata retained from official dataset.toml",
            "used_as_pier_local_task_digest": False,
            "pier_digest_equal_count": manifest_digest_matches,
            "note": (
                "Official DeepSWE evaluations use Pier over the local task directory. "
                "The packet joins to exact Git task-tree bytes and records both the "
                "dataset-manifest digest and the independently computed Pier local digest."
            ),
        },
        "artifact_inventory_contract": {
            "source_ref": documentation_ref("README.md"),
            "available_per_run_types": [
                "agent/trajectory.json",
                "agent/mini-swe-agent.txt",
                "artifacts/model.patch",
                "verifier/reward.json",
                "verifier/ctrf.json",
                "verifier/test-stdout.txt",
                "verifier/run.log",
                "verifier/reports/**",
            ],
            "inventory_only_pre_lock": True,
            "per_record_bytes_or_values_read_during_packet_generation": False,
        },
        "blind_generation_contract": {
            "allowed_inputs": [
                "official DeepSWE v1.1 task files",
                "official task dataset manifest",
                "official README artifact-type documentation",
            ],
            "forbidden_inputs": [
                "leaderboard rows",
                "trial index rows",
                "agent trajectories or logs",
                "per-run model patches",
                "per-run verifier outputs",
                "released evaluator labels or rewards",
            ],
            "packet_bytes_depend_only_on_allowed_inputs": True,
        },
        "solution_policy": (
            "controller_metadata_only; reference solution is not used at grading and "
            "solution bytes are not copied or rendered"
        ),
        "grader_config_render_policy": (
            "full official bytes retained under raw_case; deterministic projection rendered "
            "in case_packet.md with full f2p IDs and hash/count binding for p2p IDs"
        ),
        "entries": entries,
    }
    result = dict(core)
    result["source_lock_core_sha256"] = sha256_bytes(canonical_bytes(core))
    return result


def _controller_packet(
    *,
    slug: str,
    files: Sequence[SourceFile],
    config: Mapping[str, Any],
    grader: Mapping[str, Any],
    manifest_digest: str,
    source_lock_entry: Mapping[str, Any],
    agent_input_sha256: str,
) -> dict[str, Any]:
    metadata = config["metadata"]
    projection = _evaluator_projection(
        slug=slug,
        grader=grader,
        config_source=_file_by_path(files, "tests/config.json"),
    )
    return {
        "schema_version": CASE_PACKET_SCHEMA,
        "benchmark": {
            "name": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
            "split": BENCHMARK_SPLIT,
            "dataset_name": DATASET_NAME,
            "dataset_ref": DATASET_REF,
            "official_repository": OFFICIAL_REPOSITORY,
            "official_source_commit": V1_1_DOCUMENTED_COMMIT,
            "official_tasks_git_tree_oid": V1_1_TASKS_GIT_TREE_OID,
        },
        "task": {
            "case_unit_id": slug,
            "task_id": f"datacurve/{slug}",
            "task_name": f"datacurve/{slug}",
            "dataset_manifest_task_digest": manifest_digest,
            "pier_local_task_digest": source_lock_entry["pier_local_task_digest"],
            "instruction": _file_by_path(files, "instruction.md").text,
            "instruction_sha256": source_lock_entry["instruction_sha256"],
            "task_config": dict(config),
            "task_config_sha256": source_lock_entry["task_config_sha256"],
            "repository_url": metadata["repository_url"],
            "base_commit_hash": metadata["base_commit_hash"],
            "language": metadata["language"],
            "category": metadata["category"],
        },
        "model_visible_input": {
            "path": "agent_input.json",
            "sha256": agent_input_sha256,
            "field_allowlist": ["instruction", "task_name"],
        },
        "evaluator_reference": {
            "visibility": "drafter_reviewer_and_controller_only",
            "environment_mode": "separate",
            "verifier_entrypoint": "raw_case/official/tests/test.sh",
            "shared_grader_path": "raw_case/official/tests/grader.py",
            "grader_config_path": "raw_case/official/tests/config.json",
            "compact_projection_path": "raw_case/derived/evaluator_projection.json",
            "test_patch_path": "raw_case/official/tests/test.patch",
            "pre_artifacts_path": "raw_case/official/pre_artifacts.sh",
            "model_patch_artifact": "/logs/artifacts/model.patch",
            "native_reward_artifact": "/logs/verifier/reward.json",
            "native_test_report_artifact": "/logs/verifier/ctrf.json",
            "raw_test_output_artifact": "/logs/verifier/test-stdout.txt",
            "raw_run_log_artifact": "/logs/verifier/run.log",
            "framework_report_artifacts": "/logs/verifier/reports/**",
            "verifier_timeout_sec": (config.get("verifier") or {}).get("timeout_sec"),
            "projection": projection,
            "oracle_solution_source_paths": [
                "solution/solve.sh",
                "solution/solution.patch",
            ],
            "oracle_solution_materialized": False,
            "oracle_solution_used_by_native_grader": False,
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
            "retained_execution_artifact_types": [
                "agent/trajectory.json",
                "agent/mini-swe-agent.txt",
                "artifacts/model.patch",
                "verifier/ctrf.json",
                "verifier/test-stdout.txt",
                "verifier/run.log",
                "verifier/reports/**",
            ],
            "released_evaluator_record_type_retained_post_run": "verifier/reward.json",
            "released_evaluator_value_available_to_packet_or_scorer": False,
            "source_ref": documentation_ref("README.md"),
        },
        "provenance": {
            "dataset_ref": DATASET_REF,
            "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
            "dataset_manifest_task_digest": manifest_digest,
            "pier_local_task_digest": source_lock_entry["pier_local_task_digest"],
            "task_source_tree_sha256": source_lock_entry["source_tree_sha256"],
            "canonical_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
            "tree_hash_method": TREE_HASH_METHOD,
            "source_commit": V1_1_DOCUMENTED_COMMIT,
            "tasks_git_tree_oid": V1_1_TASKS_GIT_TREE_OID,
        },
        "leakage_control": {
            "policy": "allowlist_only_outcome_blind_v1",
            "model_receives_only_agent_input_json": True,
            "tests_verifier_solution_excluded_from_model_input": True,
            "oracle_solution_bytes_excluded_from_packet": True,
            "prior_run_records_excluded_from_packet_generation": True,
            "released_evaluator_results_excluded_from_packet_generation": True,
        },
        "visibility": "controller_and_human_review_only",
    }


def _materialize_raw_case(
    *,
    case_dir: Path,
    slug: str,
    files: Sequence[SourceFile],
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    raw_root = case_dir / "raw_case"
    copied: list[str] = []
    official: list[str] = []
    source_files: list[dict[str, Any]] = []
    file_sources: dict[str, str] = {}
    for source in files:
        is_solution = source.relative_path.startswith("solution/")
        materialized: str | None = None
        representation = "controller_metadata_hash_only_reference_solution"
        if not is_solution:
            materialized = f"official/{source.relative_path}"
            destination = raw_root / materialized
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.data)
            if sha256_file(destination) != source.sha256:
                raise BuildError(
                    f"materialized source hash mismatch: {slug}/{source.relative_path}"
                )
            copied.append(materialized)
            official.append(materialized)
            file_sources[materialized] = source_ref(slug, source.relative_path)
            representation = "byte_exact_utf8_official_source"
        source_files.append(
            {
                "source_path": source.relative_path,
                "materialized_path": materialized,
                "representation": representation,
                "sha256": source.sha256,
                "size_bytes": source.size_bytes,
                "source_ref": source_ref(slug, source.relative_path),
            }
        )

    projection = packet["evaluator_reference"]["projection"]
    projection_path = "derived/evaluator_projection.json"
    write_json(raw_root / projection_path, projection)
    copied.append(projection_path)
    derived = [projection_path]
    file_sources[projection_path] = (
        "derived://mechanical-projection-of/official/tests/config.json+"
        "official/tests/grader.py"
    )
    copied.sort()
    official.sort()
    source_files.sort(key=lambda item: str(item["source_path"]))

    raw_tree = filesystem_tree_digest(raw_root)
    source_tree = tree_digest(
        (
            str(item["source_path"]),
            str(item["sha256"]),
            int(item["size_bytes"]),
        )
        for item in source_files
    )
    projection_sha = sha256_file(raw_root / projection_path)
    sha_per_file = {
        str(item["materialized_path"]): str(item["sha256"])
        for item in source_files
        if item["materialized_path"] is not None
    }
    sha_per_file[projection_path] = projection_sha
    size_per_file = {
        str(item["materialized_path"]): int(item["size_bytes"])
        for item in source_files
        if item["materialized_path"] is not None
    }
    size_per_file[projection_path] = (raw_root / projection_path).stat().st_size
    manifest = {
        "schema_version": RAW_MANIFEST_SCHEMA,
        "domain": "deep_swe_v1_1",
        "case_unit_id": slug,
        "task_id": f"datacurve/{slug}",
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_name": DATASET_NAME,
        "dataset_ref": DATASET_REF,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "dataset_manifest_task_digest": packet["task"]["dataset_manifest_task_digest"],
        "pier_local_task_digest": packet["task"]["pier_local_task_digest"],
        "tree_hash_method": TREE_HASH_METHOD,
        "source_tree_sha256": source_tree[0],
        "source_file_count": source_tree[1],
        "source_total_bytes": source_tree[2],
        "raw_case_tree_sha256": raw_tree[0],
        "raw_case_file_count": raw_tree[1],
        "raw_case_total_bytes": raw_tree[2],
        "copied_files": copied,
        "official_files": official,
        "derived_files": derived,
        "packet_files": copied,
        "sha256_per_file": dict(sorted(sha_per_file.items())),
        "size_bytes_per_file": dict(sorted(size_per_file.items())),
        "file_sources": dict(sorted(file_sources.items())),
        "source_files": source_files,
        "controller_metadata_only_files": [
            item
            for item in source_files
            if item["representation"]
            == "controller_metadata_hash_only_reference_solution"
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
        "solution_policy": "controller_metadata_only_no_bytes",
        "grader_config_render_policy": (
            "official bytes retained; deterministic evaluator projection rendered in Markdown"
        ),
    }
    return manifest


def _render_packet(
    *, packet: Mapping[str, Any], raw_manifest: Mapping[str, Any], raw_root: Path
) -> str:
    task = packet["task"]
    config = task["task_config"]
    metadata = config["metadata"]
    environment = config["environment"]
    projection = packet["evaluator_reference"]["projection"]
    lines = [
        "# Case Packet",
        "",
        "## Case Metadata",
        "",
        "- domain: `deep_swe_v1_1`",
        f"- case_unit_id: `{task['case_unit_id']}`",
        f"- task_id: `{task['task_id']}`",
        f"- dataset: `{DATASET_NAME}`",
        f"- source commit: `{V1_1_DOCUMENTED_COMMIT}`",
        f"- tasks Git tree: `{V1_1_TASKS_GIT_TREE_OID}`",
        f"- source tree SHA-256: `{raw_manifest['source_tree_sha256']}`",
        f"- Pier local task digest: `{task['pier_local_task_digest']}`",
        "",
        "## Official Task Summary",
        "",
        f"- display title: {metadata['display_title']}",
        f"- display description: {metadata['display_description']}",
        f"- category: `{metadata['category']}`",
        f"- language: `{metadata['language']}`",
        f"- repository: `{metadata['repository_url']}`",
        f"- base commit: `{metadata['base_commit_hash']}`",
        f"- agent timeout seconds: `{(config.get('agent') or {}).get('timeout_sec')}`",
        f"- verifier timeout seconds: `{(config.get('verifier') or {}).get('timeout_sec')}`",
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
        "semantics below. Official case-specific requirements that exceed what the native",
        "evaluator operationalizes belong in a separate `stronger_measurement` layer.",
        "Requirements supported only by reviewer intuition are excluded from both checklist",
        "and scoring. Stronger failure is not benchmark error, and native-evidence/released-",
        "label disagreement is only a review trigger unless retained artifacts prove that the",
        "benchmark actually evaluated a different claimed outcome.",
        "",
        "## Native Evaluator Semantics",
        "",
        f"- fail-to-pass node count: `{projection['native_test_sets']['fail_to_pass']['count']}`",
        f"- pass-to-pass node count: `{projection['native_test_sets']['pass_to_pass']['count']}`",
        f"- report format: `{projection['grade']['format']}`",
        f"- node-id derivation: `{projection['grade'].get('node_id', 'classname.name')}`",
        "- native success: all configured fail-to-pass nodes pass, the fail-to-pass set is",
        "  non-empty, and no configured pass-to-pass node fails.",
        "- native failure: any configured node is missing, skipped, or failed.",
        "- duplicate node IDs: worst status wins (`passed < skipped < failed`).",
        "- decisive source pointers: `official/tests/grader.py`,",
        "  `official/tests/config.json`, `official/tests/test.sh`, and",
        "  `derived/evaluator_projection.json`.",
        "",
        "The complete official `tests/config.json` is retained byte-for-byte under",
        "`raw_case/official/tests/config.json`. Its large pass-to-pass identifier list is",
        "represented in the rendered projection by count and canonical-list SHA-256; all",
        "fail-to-pass identifiers remain rendered in full.",
        "",
        "## Available Artifact Inventory (types only; no per-record values)",
        "",
    ]
    inventory = packet["artifact_inventory"]
    for artifact_type in inventory["retained_execution_artifact_types"]:
        lines.append(f"- `{artifact_type}`")
    lines.extend(
        [
            f"- released evaluator record retained after execution: "
            f"`{inventory['released_evaluator_record_type_retained_post_run']}`",
            "",
            "## Visibility Boundary",
            "",
            "The tested agent receives only `agent_input.json`. The source-rich packet,",
            "task config, tests, verifier, grader, reference solution metadata, and artifact",
            "inventory must not be placed in the tested agent prompt or workspace.",
            "",
            "## Source Inventory",
            "",
        ]
    )
    for relative in raw_manifest["packet_files"]:
        lines.append(f"- `{relative}`")
    lines.extend(
        [
            "",
            "## Source Inventory Summary",
            "",
            f"- canonical official source files: `{raw_manifest['source_file_count']}`",
            f"- materialized official files: `{len(raw_manifest['official_files'])}`",
            f"- mechanically derived files: `{len(raw_manifest['derived_files'])}`",
            f"- protected reference-solution metadata-only files: "
            f"`{len(raw_manifest['controller_metadata_only_files'])}`",
            f"- canonical task source bytes: `{raw_manifest['source_total_bytes']}`",
            f"- retained raw-case bytes: `{raw_manifest['raw_case_total_bytes']}`",
            "",
            "### Protected reference solution metadata (bytes not copied)",
            "",
        ]
    )
    for item in raw_manifest["controller_metadata_only_files"]:
        lines.append(
            f"- `{item['source_path']}` — present, `{item['size_bytes']}` bytes, "
            f"SHA-256 `{item['sha256']}`, ref `{item['source_ref']}`"
        )
    lines.extend(["", "## Rendered Packet Sources", ""])
    for relative in raw_manifest["packet_files"]:
        if relative == "official/tests/config.json":
            continue
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
    rows: list[tuple[str, str, int]] = []
    for slug in sorted(slugs):
        path = output_root / slug / "agent_input.json"
        rows.append(
            (f"{slug}/agent_input.json", sha256_file(path), path.stat().st_size)
        )
    return tree_digest(rows)


def build_packets(source_dir: Path, output_root: Path) -> dict[str, Any]:
    snapshot = load_source_directory(source_dir)
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
        for slug, manifest_digest in snapshot.manifest_task_digests.items():
            files = _files_for_task(snapshot, slug)
            config, grader = _validate_task_source(slug, files, manifest_digest)
            case_dir = staging / slug
            case_dir.mkdir()
            agent_input = {
                "instruction": _file_by_path(files, "instruction.md").text,
                "task_name": f"datacurve/{slug}",
            }
            write_json(case_dir / "agent_input.json", agent_input)
            agent_input_sha = sha256_file(case_dir / "agent_input.json")
            packet = _controller_packet(
                slug=slug,
                files=files,
                config=config,
                grader=grader,
                manifest_digest=manifest_digest,
                source_lock_entry=lock_entries[slug],
                agent_input_sha256=agent_input_sha,
            )
            write_json(case_dir / "case_packet.json", packet)
            raw_manifest = _materialize_raw_case(
                case_dir=case_dir,
                slug=slug,
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
                    "task_name": f"datacurve/{slug}",
                    "dataset_manifest_task_digest": manifest_digest,
                    "pier_local_task_digest": lock_entries[slug][
                        "pier_local_task_digest"
                    ],
                    "source_tree_sha256": raw_manifest["source_tree_sha256"],
                    "source_file_count": raw_manifest["source_file_count"],
                    "source_total_bytes": raw_manifest["source_total_bytes"],
                    "official_file_count": len(raw_manifest["official_files"]),
                    "protected_solution_file_count": len(
                        raw_manifest["controller_metadata_only_files"]
                    ),
                    "f2p_node_id_count": len(grader["f2p_node_ids"]),
                    "p2p_node_id_count": len(grader["p2p_node_ids"]),
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

        agent_tree = _agent_input_tree_digest(staging, snapshot.manifest_task_digests)
        index_core = {
            "schema_version": INDEX_SCHEMA,
            "status": "frozen_pre_outcome_case_packets",
            "benchmark": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
            "split": BENCHMARK_SPLIT,
            "dataset_name": DATASET_NAME,
            "dataset_ref": DATASET_REF,
            "official_repository": OFFICIAL_REPOSITORY,
            "official_source_commit": V1_1_DOCUMENTED_COMMIT,
            "official_tasks_git_tree_oid": V1_1_TASKS_GIT_TREE_OID,
            "canonical_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
            "source_lock_path": "source_lock.json",
            "source_lock_sha256": source_lock_sha,
            "canonical_packet_filename": "case_packet.md",
            "packet_visibility": "drafter_and_reviewer_only",
            "model_visible_files_per_case": ["agent_input.json"],
            "solution_policy": "controller_metadata_only_no_bytes",
            "outcome_blind_generation": True,
            "packet_count": len(entries),
            "agent_input_tree_sha256": agent_tree[0],
            "agent_input_file_count": agent_tree[1],
            "agent_input_total_bytes": agent_tree[2],
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
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"expected JSON object: {path}")
    return value


def _source_inventory_paths(markdown: str) -> list[str]:
    if markdown.splitlines().count("## Source Inventory") != 1:
        raise BuildError("packet must contain exactly one Source Inventory heading")
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
            raise BuildError(f"invalid Source Inventory line: {line!r}")
        paths.append(match.group(1).replace("\\", "/"))
    if not paths or len(paths) != len(set(paths)):
        raise BuildError("packet Source Inventory is empty or duplicated")
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
        raise BuildError(
            f"case {slug} generated metadata contains prior-run keys: {sorted(forbidden_keys)}"
        )
    generated_text = (
        json.dumps(packet, ensure_ascii=False, sort_keys=True)
        + json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        + markdown
    ).lower()
    for marker in FORBIDDEN_PRIOR_RUN_URL_MARKERS:
        if marker in generated_text:
            raise BuildError(
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
        raise BuildError("unexpected DeepSWE source lock schema")
    if index.get("schema_version") != INDEX_SCHEMA:
        raise BuildError("unexpected DeepSWE packet index schema")
    if source_lock.get("canonical_source_tree_sha256") != EXPECTED_SOURCE_TREE_SHA256:
        raise BuildError("source lock does not name the frozen DeepSWE v1.1 task tree")
    if source_lock.get("task_count") != EXPECTED_TASK_COUNT:
        raise BuildError("source lock task count mismatch")
    if (
        source_lock.get("blind_generation_contract", {}).get(
            "per_record_bytes_or_values_read_during_packet_generation"
        )
        is True
    ):
        raise BuildError("source lock claims per-record prior-run access")
    if index.get("source_lock_sha256") != sha256_file(lock_path):
        raise BuildError("index/source-lock hash mismatch")
    lock_core = dict(source_lock)
    claimed_lock_core = str(lock_core.pop("source_lock_core_sha256", ""))
    if claimed_lock_core != sha256_bytes(canonical_bytes(lock_core)):
        raise BuildError("source lock core digest mismatch")
    index_core = dict(index)
    claimed_index_core = str(index_core.pop("index_core_sha256", ""))
    if claimed_index_core != sha256_bytes(canonical_bytes(index_core)):
        raise BuildError("index core digest mismatch")
    entries = list(index.get("entries") or [])
    if len(entries) != EXPECTED_TASK_COUNT or index.get("packet_count") != len(entries):
        raise BuildError("packet index must contain exactly 113 entries")
    lock_entries = {
        str(entry["case_unit_id"]): entry for entry in source_lock.get("entries") or []
    }
    if len(lock_entries) != EXPECTED_TASK_COUNT:
        raise BuildError("source lock must contain exactly 113 case entries")
    expected_root_names = {
        "index.json",
        "index.json.sha256",
        "source_lock.json",
        "source_lock.json.sha256",
        *(str(entry["case_unit_id"]) for entry in entries),
    }
    actual_root_names = {path.name for path in output_root.iterdir()}
    if actual_root_names != expected_root_names:
        raise BuildError(
            "output root inventory mismatch: "
            f"missing={sorted(expected_root_names-actual_root_names)}, "
            f"extra={sorted(actual_root_names-expected_root_names)}"
        )

    corpus_rows: list[tuple[str, str, int]] = []
    official_file_count = 0
    official_total_bytes = 0
    solution_metadata_count = 0
    projection_count = 0
    f2p_total = 0
    p2p_total = 0
    for entry in entries:
        slug = str(entry["case_unit_id"])
        case_dir = output_root / slug
        required_top = {
            "agent_input.json",
            "case_packet.json",
            "case_packet.md",
            "raw_case_manifest.json",
            "raw_case",
        }
        if {path.name for path in case_dir.iterdir()} != required_top:
            raise BuildError(f"case {slug} top-level inventory mismatch")
        for filename, field in (
            ("agent_input.json", "agent_input_sha256"),
            ("case_packet.json", "case_packet_json_sha256"),
            ("case_packet.md", "case_packet_markdown_sha256"),
            ("raw_case_manifest.json", "raw_case_manifest_sha256"),
        ):
            if sha256_file(case_dir / filename) != entry[field]:
                raise BuildError(f"case {slug} hash mismatch for {filename}")

        agent_input = _load_json(case_dir / "agent_input.json")
        if set(agent_input) != {"instruction", "task_name"}:
            raise BuildError(f"case {slug} agent input violates field allowlist")
        if agent_input["task_name"] != f"datacurve/{slug}":
            raise BuildError(f"case {slug} agent input task name mismatch")
        packet = _load_json(case_dir / "case_packet.json")
        manifest = _load_json(case_dir / "raw_case_manifest.json")
        markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
        if packet.get("schema_version") != CASE_PACKET_SCHEMA:
            raise BuildError(f"case {slug} packet schema mismatch")
        if manifest.get("schema_version") != RAW_MANIFEST_SCHEMA:
            raise BuildError(f"case {slug} raw manifest schema mismatch")
        if packet["task"]["case_unit_id"] != slug or manifest["case_unit_id"] != slug:
            raise BuildError(f"case {slug} identity mismatch")
        if packet["task"]["instruction"] != agent_input["instruction"]:
            raise BuildError(f"case {slug} instruction join mismatch")
        if packet["model_visible_input"]["sha256"] != entry["agent_input_sha256"]:
            raise BuildError(f"case {slug} model-visible hash mismatch")
        if (
            packet["leakage_control"][
                "prior_run_records_excluded_from_packet_generation"
            ]
            is not True
        ):
            raise BuildError(f"case {slug} outcome blindness is not asserted")
        _assert_outcome_blind_generated_metadata(
            packet=packet, manifest=manifest, markdown=markdown, slug=slug
        )

        raw_root = case_dir / "raw_case"
        actual_raw = sorted(
            path.relative_to(raw_root).as_posix()
            for path in raw_root.rglob("*")
            if path.is_file()
        )
        if actual_raw != sorted(manifest.get("copied_files") or []):
            raise BuildError(f"case {slug} raw copied-files inventory mismatch")
        if _source_inventory_paths(markdown) != actual_raw:
            raise BuildError(f"case {slug} Markdown Source Inventory mismatch")
        if any(path.startswith("official/solution/") for path in actual_raw):
            raise BuildError(f"case {slug} exposes reference-solution bytes")
        raw_tree = filesystem_tree_digest(raw_root)
        if raw_tree != (
            manifest["raw_case_tree_sha256"],
            manifest["raw_case_file_count"],
            manifest["raw_case_total_bytes"],
        ):
            raise BuildError(f"case {slug} raw tree mismatch")
        for relative in actual_raw:
            path = raw_root / relative
            if sha256_file(path) != manifest["sha256_per_file"][relative]:
                raise BuildError(f"case {slug} raw file hash mismatch: {relative}")
            if path.stat().st_size != manifest["size_bytes_per_file"][relative]:
                raise BuildError(f"case {slug} raw file size mismatch: {relative}")

        official_files = sorted(manifest.get("official_files") or [])
        derived_files = sorted(manifest.get("derived_files") or [])
        expected_official = sorted(
            f"official/{path}"
            for path in REQUIRED_TASK_FILES
            if not path.startswith("solution/")
        )
        if official_files != expected_official:
            raise BuildError(f"case {slug} official source inventory mismatch")
        if derived_files != ["derived/evaluator_projection.json"]:
            raise BuildError(f"case {slug} derived source inventory mismatch")
        if "### `official/tests/config.json`" in markdown:
            raise BuildError(
                f"case {slug} renders oversized official grader config verbatim"
            )
        if "### `derived/evaluator_projection.json`" not in markdown:
            raise BuildError(f"case {slug} does not render evaluator projection")

        config_path = raw_root / "official/tests/config.json"
        grader_config = _load_json(config_path)
        task_toml_path = raw_root / "official/task.toml"
        parsed_task = tomllib.loads(task_toml_path.read_text(encoding="utf-8"))
        if packet["task"]["task_config"] != parsed_task:
            raise BuildError(f"case {slug} parsed task config mismatch")
        if parsed_task["metadata"]["task_id"] != slug:
            raise BuildError(f"case {slug} raw task identity mismatch")
        config_source = SourceFile(
            task_slug=slug,
            relative_path="tests/config.json",
            sha256=sha256_file(config_path),
            size_bytes=config_path.stat().st_size,
            text=config_path.read_text(encoding="utf-8"),
            data=config_path.read_bytes(),
        )
        expected_projection = _evaluator_projection(
            slug=slug, grader=grader_config, config_source=config_source
        )
        actual_projection = _load_json(raw_root / "derived/evaluator_projection.json")
        if actual_projection != expected_projection:
            raise BuildError(f"case {slug} evaluator projection is not mechanical")
        if packet["evaluator_reference"]["projection"] != expected_projection:
            raise BuildError(f"case {slug} controller evaluator projection mismatch")
        f2p_count = len(grader_config["f2p_node_ids"])
        p2p_count = len(grader_config["p2p_node_ids"])
        if (f2p_count, p2p_count) != (
            entry["f2p_node_id_count"],
            entry["p2p_node_id_count"],
        ):
            raise BuildError(f"case {slug} node inventory count mismatch")
        f2p_total += f2p_count
        p2p_total += p2p_count
        projection_count += 1

        source_files = list(manifest.get("source_files") or [])
        if len(source_files) != len(REQUIRED_TASK_FILES):
            raise BuildError(f"case {slug} canonical source count mismatch")
        seen: set[str] = set()
        for item in source_files:
            source_path = str(item["source_path"])
            if source_path in seen:
                raise BuildError(f"case {slug} duplicate source path {source_path}")
            seen.add(source_path)
            corpus_rows.append(
                (f"{slug}/{source_path}", str(item["sha256"]), int(item["size_bytes"]))
            )
            if source_path.startswith("solution/"):
                if item["materialized_path"] is not None:
                    raise BuildError(f"case {slug} materializes solution source")
                if (
                    item["representation"]
                    != "controller_metadata_hash_only_reference_solution"
                ):
                    raise BuildError(f"case {slug} solution representation mismatch")
                solution_metadata_count += 1
            else:
                expected_path = f"official/{source_path}"
                if item["materialized_path"] != expected_path:
                    raise BuildError(f"case {slug} official source path mismatch")
                official_file_count += 1
                official_total_bytes += int(item["size_bytes"])
        if seen != REQUIRED_TASK_FILES:
            raise BuildError(f"case {slug} source-file membership mismatch")
        source_tree = tree_digest(
            (str(item["source_path"]), str(item["sha256"]), int(item["size_bytes"]))
            for item in source_files
        )
        if source_tree != (
            manifest["source_tree_sha256"],
            manifest["source_file_count"],
            manifest["source_total_bytes"],
        ):
            raise BuildError(f"case {slug} canonical source tree mismatch")
        if manifest["source_tree_sha256"] != lock_entries[slug]["source_tree_sha256"]:
            raise BuildError(f"case {slug} source-lock join mismatch")
        if (
            packet["task"]["dataset_manifest_task_digest"]
            != lock_entries[slug]["dataset_manifest_task_digest"]
        ):
            raise BuildError(f"case {slug} dataset manifest digest join mismatch")
        if (
            packet["task"]["pier_local_task_digest"]
            != lock_entries[slug]["pier_local_task_digest"]
        ):
            raise BuildError(f"case {slug} Pier digest join mismatch")

    corpus = tree_digest(corpus_rows)
    if corpus != (
        EXPECTED_SOURCE_TREE_SHA256,
        EXPECTED_SOURCE_FILE_COUNT,
        EXPECTED_SOURCE_TOTAL_BYTES,
    ):
        raise BuildError(f"reconstructed DeepSWE v1.1 corpus mismatch: {corpus}")
    agent_tree = _agent_input_tree_digest(output_root, lock_entries)
    if agent_tree != (
        index["agent_input_tree_sha256"],
        index["agent_input_file_count"],
        index["agent_input_total_bytes"],
    ):
        raise BuildError("agent-input tree mismatch")
    if (output_root / "source_lock.json.sha256").read_text(encoding="utf-8") != (
        f"{sha256_file(lock_path)}  source_lock.json\n"
    ):
        raise BuildError("source-lock checksum sidecar mismatch")
    if (output_root / "index.json.sha256").read_text(encoding="utf-8") != (
        f"{sha256_file(index_path)}  index.json\n"
    ):
        raise BuildError("index checksum sidecar mismatch")
    output_bytes = sum(
        path.stat().st_size for path in output_root.rglob("*") if path.is_file()
    )
    if output_bytes > MAX_OUTPUT_BYTES:
        raise BuildError(
            f"DeepSWE packet tree exceeds safety cap: {output_bytes} > {MAX_OUTPUT_BYTES}"
        )
    return {
        "status": "ok",
        "packet_count": len(entries),
        "canonical_source_tree_sha256": corpus[0],
        "canonical_source_file_count": corpus[1],
        "canonical_source_total_bytes": corpus[2],
        "materialized_official_file_count": official_file_count,
        "materialized_official_total_bytes": official_total_bytes,
        "protected_solution_file_count": solution_metadata_count,
        "evaluator_projection_count": projection_count,
        "f2p_node_id_count": f2p_total,
        "p2p_node_id_count": p2p_total,
        "agent_input_tree_sha256": agent_tree[0],
        "outcome_blind_generation": True,
        "output_total_bytes": output_bytes,
        "output_limit_bytes": MAX_OUTPUT_BYTES,
        "index_sha256": sha256_file(index_path),
        "source_lock_sha256": sha256_file(lock_path),
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        help=(
            "official DeepSWE repository checkout or its tasks/ directory; required "
            "unless --validate-only is used"
        ),
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output_root = args.output_root.resolve()
    if args.validate_only:
        if args.source_dir is not None:
            raise BuildError("--source-dir is not used with --validate-only")
        summary = validate_output(output_root)
    else:
        if args.source_dir is None:
            raise BuildError("--source-dir is required to build DeepSWE packets")
        summary = build_packets(args.source_dir.resolve(), output_root)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
