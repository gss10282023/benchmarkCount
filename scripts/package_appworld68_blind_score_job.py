#!/usr/bin/env python3
"""Build outcome-blind AppWorld-68 score tasks with released runtime semantics.

The builder deliberately never parses released evaluator outputs, evaluator reports,
or run summaries.  It copies only the allowlisted non-verdict projection into each
score task and emits a separate byte-level manifest for transferring the immutable
full records into a scorer-inaccessible retained area.  Version 3 also amends the
frozen checklist support pointers with the exact released AppWorld evaluator runtime
identified by the retained pre-verdict version receipt; rule text is unchanged.
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
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_ROOT = (
    REPO_ROOT
    / "experiments"
    / "appworld_test_normal_68_system_design_v4_runtime_semantics_gpt54_high_v1"
)
DEFAULT_RUN_ROOT = Path(
    "/Users/gss/Downloads/appworld585_20260719_full_v1_completed"
)
DEFAULT_RUNTIME_SOURCE_ROOT = (
    REPO_ROOT
    / "experiments"
    / "appworld_evaluator_runtime_0.2.0.dev0_a072b7a_v2_semantic_closure"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT
    / "transfer"
    / "appworld68_tn_blind_score_system_design_v4_runtime_semantics_20260719_v1"
)
SCHEMA_VERSION = "appworld68_blind_score_input_package.v3"
RETAINED_SCHEMA_VERSION = "appworld68_retained_record_transfer_manifest.v3"
RECEIPT_SCHEMA_VERSION = "appworld68_blind_score_input_build_receipt.v3"
EXPECTED_CASE_COUNT = 68
AGENTS = ("agent_a", "agent_b", "agent_c")
AGENT_LABELS = {
    "agent_a": "Agent A",
    "agent_b": "Agent B",
    "agent_c": "Agent C",
}
AGENT_MODELS = {
    "agent_a": "openai/gpt-5.4",
    "agent_b": "anthropic/claude-opus-4.7",
    "agent_c": "deepseek/deepseek-v4-pro",
}
EXPECTED_RECORD_COUNT = EXPECTED_CASE_COUNT * len(AGENTS)
EXPECTED_REGISTERED_TEST_COUNT = 469
EXPECTED_CASE_IDS_SHA256 = (
    "2b54ce295ac44589ff9ceb689ea52daf69c64dfb0c76118db34af2b3e1da7c96"
)
EXPECTED_EXPERIMENT_MANIFEST_SHA256 = (
    "2dc89cad1b0d903b18ea90cc11ea69e13e301a0f4398d637069172113808eae9"
)
EXPECTED_VISIBILITY_CONTRACT_SHA256 = (
    "e2bf3cfbf3d166334e029914c086ee78c84b3665067bf649e8496fdf2a9f01e6"
)
EXPECTED_FREEZE_MANIFEST_SHA256 = (
    "7b9007048eb1a9b1eceb36a2a53f834f71fc80dcb18057ed9a9482812ba57eeb"
)
EXPECTED_FREEZE_RECORDS_SHA256 = (
    "b33ff9a77101fb04126a6b28dc7f828ddd6e43c30ff4cb57c837b3e4a36b5794"
)
EXPECTED_REPAIR_MANIFEST_SHA256 = (
    "0be4a920caf5a31ba5b0640992817e5c52696dccd77aadeb852d7e1a0a3b2853"
)
EXPECTED_REPAIR_FILES_SHA256 = (
    "6e4a63fe7dbe0417dd376ab1f32ea1a0c3c5c1044a3498cdbb549693d94b2272"
)
EXPECTED_SEMANTICS_SHA256 = (
    "f92952e8a35001848126397fc43f4b612ea607030c53deb783af57d93e624d9f"
)
EXPECTED_RETRIEVAL_MANIFEST_SHA256 = (
    "911632c39c44f33ab2b2e9e12d2ebd05e375666d6cae7b411bcf3b6cc742131b"
)
EXPECTED_APPWORLD_CODE_VERSION = "0.2.0.dev0:a072b7a"
EXPECTED_APPWORLD_DATA_VERSION = "0.2.0"
EXPECTED_RETAINED_RECORD_FILE_COUNT = 32
EXPECTED_RUNTIME_COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
EXPECTED_RUNTIME_MANIFEST_SHA256 = (
    "acb788a51bc92e3896f763bcc5f11d5f21ea4bee9b151248b6d64ec755b08463"
)
EXPECTED_RUNTIME_FILES_SHA256 = (
    "71decd1269ed052e45ca2a0eb1ca540295c5b5fcb40238b9a6feae7b05e83dbe"
)
EXPECTED_RUNTIME_FILES = {
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
RUNTIME_SUPPORT_POINTERS = (
    "official/runtime/src/appworld/evaluator.py::TestTracker",
    "official/runtime/src/appworld/common/evaluation.py::assert_plus",
    "official/runtime/src/appworld/collections/models.py::ModelCollectionPair._changed_model_names",
    "official/runtime/src/appworld/collections/models.py::ModelCollectionPair._changed_records",
    "official/runtime/src/appworld/collections/models.py::ModelCollectionPair._changed_field_names",
    "official/runtime/src/appworld/common/collections.py::list_of",
    "official/runtime/src/appworld/common/collections.py::set_of",
    "official/runtime/src/appworld/common/collections.py::dict_of",
    "official/runtime/src/appworld/common/collections.py::dict_list_of",
)
CHECKLIST_SCHEMA_PATH = (
    REPO_ROOT / "neurips_ed_track_minimal" / "schemas" / "case_checklist.schema.json"
)
CASE_ID_RE = re.compile(r"^[0-9a-f]{7}_[123]$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_OFFICIAL_FILES = (
    "official/specs.json",
    "official/ground_truth/answer.json",
    "official/ground_truth/evaluation.py",
    "official/ground_truth/metadata.json",
    "official/ground_truth/private_data.json",
    "official/ground_truth/public_data.json",
    "official/ground_truth/test_data.json",
    "official/dbs/admin.jsonl",
    "official/dbs/amazon.jsonl",
    "official/dbs/api_docs.jsonl",
    "official/dbs/file_system.jsonl",
    "official/dbs/gmail.jsonl",
    "official/dbs/phone.jsonl",
    "official/dbs/simple_note.jsonl",
    "official/dbs/splitwise.jsonl",
    "official/dbs/spotify.jsonl",
    "official/dbs/supervisor.jsonl",
    "official/dbs/todoist.jsonl",
    "official/dbs/venmo.jsonl",
)
SAFE_RUN_FILES = (
    "native_evaluator_input.json",
    "official_runner_config.json",
    "job.json",
    "source_bundle_entry.json",
    "appworld_task_output/logs/api_calls.jsonl",
    "appworld_task_output/logs/environment_io.md",
    "appworld_task_output/misc/finished",
    "appworld_task_output/misc/usage.json",
    "appworld_task_output/version/code.txt",
    "appworld_task_output/version/data.txt",
)
SAFE_RUN_TREES = ("appworld_task_output/dbs",)
EXPECTED_POSTRUN_DB_FILES = (
    "appworld_task_output/dbs/admin.jsonl",
    "appworld_task_output/dbs/amazon.jsonl",
    "appworld_task_output/dbs/api_docs.jsonl",
    "appworld_task_output/dbs/file_system.jsonl",
    "appworld_task_output/dbs/gmail.jsonl",
    "appworld_task_output/dbs/model_hashes.json",
    "appworld_task_output/dbs/phone.jsonl",
    "appworld_task_output/dbs/simple_note.jsonl",
    "appworld_task_output/dbs/splitwise.jsonl",
    "appworld_task_output/dbs/spotify.jsonl",
    "appworld_task_output/dbs/supervisor.jsonl",
    "appworld_task_output/dbs/todoist.jsonl",
    "appworld_task_output/dbs/venmo.jsonl",
)
FORBIDDEN_BASENAMES = {
    "artifact_manifest.json",
    "component_evaluator_output.json",
    "evaluator_output.json",
    "evaluator_report.json",
    "logger.jsonl",
    "logger.log",
    "released_evaluator_label.json",
    "native_label.json",
    "native_evaluator_output.json",
    "run_summary.json",
    "raw_run.json",
    "report.md",
    "worker_config.json",
}
FORBIDDEN_PATH_PARTS = {"evaluation"}
INFRA_SECRET_RE = re.compile(
    r"(?:sk-or-v1-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{32,}|"
    r"Authorization\s*[:=]\s*Bearer\s+[A-Za-z0-9._~+/-]{20,})",
    re.IGNORECASE,
)
SCORING_LOCK = {
    "model": "gpt-5.4",
    "reasoning_effort": "high",
    "service_tier": "default",
    "fast_mode": False,
    "requested_parallelism": 34,
    "auth_mode": "codex_login",
    "sandbox": "read-only",
    "released_result_join": "local_only_after_blind_score_sha256_lock",
}
SOURCE_LOCK = {
    "experiment_manifest_sha256": EXPECTED_EXPERIMENT_MANIFEST_SHA256,
    "visibility_contract_sha256": EXPECTED_VISIBILITY_CONTRACT_SHA256,
    "freeze_manifest_sha256": EXPECTED_FREEZE_MANIFEST_SHA256,
    "freeze_records_sha256": EXPECTED_FREEZE_RECORDS_SHA256,
    "repair_manifest_sha256": EXPECTED_REPAIR_MANIFEST_SHA256,
    "repair_files_sha256": EXPECTED_REPAIR_FILES_SHA256,
    "frozen_semantics_sha256": EXPECTED_SEMANTICS_SHA256,
    "retrieval_manifest_sha256": EXPECTED_RETRIEVAL_MANIFEST_SHA256,
    "evaluator_runtime_commit": EXPECTED_RUNTIME_COMMIT,
    "evaluator_runtime_manifest_sha256": EXPECTED_RUNTIME_MANIFEST_SHA256,
    "evaluator_runtime_files_sha256": EXPECTED_RUNTIME_FILES_SHA256,
    "checklist_runtime_support_freeze": "pre_outcome_v4.official_source_only.v1",
}
OUTCOME_BLIND_LOCK = {
    "released_labels_present": False,
    "component_evaluator_outputs_present": False,
    "evaluator_reports_present": False,
    "forbidden_basename_count": 0,
    "scorer_visible_tree_policy": "strict_allowlist_casefold_deny.v3_runtime_semantics",
}
LM_PROJECTION_DESCRIPTION = (
    "output choices/message only; prompt, provider config, costs, and credentials omitted"
)
EVALUATOR_RUNTIME_LOCK = {
    "code_version": EXPECTED_APPWORLD_CODE_VERSION,
    "commit": EXPECTED_RUNTIME_COMMIT,
    "source_manifest_sha256": EXPECTED_RUNTIME_MANIFEST_SHA256,
    "source_files_sha256": EXPECTED_RUNTIME_FILES_SHA256,
    "checklist_support_freeze": "pre_outcome_v4.official_source_only.v1_rule_content_unchanged",
    "runtime_support_pointers": list(RUNTIME_SUPPORT_POINTERS),
}


class PackageError(RuntimeError):
    """Raised when the frozen input package cannot be built safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument(
        "--runtime-source-root",
        type=Path,
        default=DEFAULT_RUNTIME_SOURCE_ROOT,
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate an existing package without modifying it.",
    )
    return parser.parse_args()


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


def load_mapping(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise PackageError(f"{label} is missing or not a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"failed to read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PackageError(f"{label} must be a JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def require_regular_tree(root: Path, label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise PackageError(f"{label} is missing or not a real directory: {root}")
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        parent = Path(dirpath)
        for name in [*dirnames, *filenames]:
            path = parent / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise PackageError(f"{label} contains a symlink: {path}")
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise PackageError(f"{label} contains a special file: {path}")


def file_entries(root: Path) -> list[dict[str, Any]]:
    require_regular_tree(root, "tree")
    entries: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries


def entries_sha256(entries: Iterable[Mapping[str, Any]]) -> str:
    return sha256_bytes(canonical_json_bytes(list(entries)))


def copy_regular_file(source: Path, destination: Path, label: str) -> None:
    if source.is_symlink() or not source.is_file():
        raise PackageError(f"{label} is missing or not a regular file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_regular_tree(source: Path, destination: Path, label: str) -> None:
    require_regular_tree(source, label)
    if destination.exists():
        raise PackageError(f"destination already exists: {destination}")
    shutil.copytree(source, destination, symlinks=False)


def validate_runtime_source(root: Path) -> dict[str, Any]:
    require_regular_tree(root, "released AppWorld evaluator runtime")
    manifest_path = root / "SOURCE_MANIFEST.json"
    if sha256_file(manifest_path) != EXPECTED_RUNTIME_MANIFEST_SHA256:
        raise PackageError("released AppWorld runtime manifest hash drift")
    manifest = load_mapping(manifest_path, "released AppWorld runtime manifest")
    require_fields(
        manifest,
        {
            "schema_version": "appworld_evaluator_runtime_source_lock.v1",
            "repository": "https://github.com/StonyBrookNLP/appworld",
            "commit": EXPECTED_RUNTIME_COMMIT,
            "code_version": EXPECTED_APPWORLD_CODE_VERSION,
            "file_count": len(EXPECTED_RUNTIME_FILES),
            "files_sha256": EXPECTED_RUNTIME_FILES_SHA256,
        },
        "released AppWorld runtime manifest",
    )
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != len(EXPECTED_RUNTIME_FILES):
        raise PackageError("released AppWorld runtime file denominator drift")
    expected_paths = set(EXPECTED_RUNTIME_FILES)
    actual_paths: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise PackageError(f"runtime manifest files[{index}] is not an object")
        require_exact_keys(
            entry,
            {"path", "size_bytes", "sha256", "source_url"},
            f"runtime manifest files[{index}]",
        )
        relative = safe_relative_path(entry.get("path"), f"runtime files[{index}].path")
        if relative in actual_paths or relative not in expected_paths:
            raise PackageError(f"unexpected or duplicate runtime path: {relative}")
        actual_paths.add(relative)
        path = safe_child(root, *PurePosixPath(relative).parts, label="runtime source")
        expected_sha256 = EXPECTED_RUNTIME_FILES[relative]
        if (
            path.stat().st_size != entry.get("size_bytes")
            or entry.get("sha256") != expected_sha256
            or sha256_file(path) != expected_sha256
        ):
            raise PackageError(f"released AppWorld runtime source drift: {relative}")
    if actual_paths != expected_paths:
        raise PackageError("released AppWorld runtime source inventory drift")
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual_files != {"SOURCE_MANIFEST.json", *expected_paths}:
        raise PackageError("released AppWorld runtime tree contains unexpected files")
    return manifest


def append_support_pointers(item: Any, *, label: str) -> None:
    if not isinstance(item, dict):
        raise PackageError(f"{label} is not an object")
    support = item.get("support")
    if not isinstance(support, list) or not all(isinstance(value, str) for value in support):
        raise PackageError(f"{label}.support is not a string list")
    for pointer in RUNTIME_SUPPORT_POINTERS:
        if pointer not in support:
            support.append(pointer)


def repair_checklist_runtime_support(source: Path, destination: Path) -> dict[str, Any]:
    original = load_mapping(source, "frozen checklist JSON")
    repaired = json.loads(json.dumps(original))
    native = repaired.get("native")
    stronger = repaired.get("stronger")
    if not isinstance(native, dict) or not isinstance(stronger, dict):
        raise PackageError("frozen checklist native/stronger sections are invalid")

    for field in ("benchmark_success", "checked_by"):
        append_support_pointers(native.get(field), label=f"native.{field}")
    for field in ("decisive_artifacts", "success_if", "fail_if", "undecided_if"):
        values = native.get(field)
        if not isinstance(values, list):
            raise PackageError(f"native.{field} is not a list")
        for index, item in enumerate(values):
            append_support_pointers(item, label=f"native.{field}[{index}]")

    conditions = stronger.get("additional_conditions")
    if not isinstance(conditions, list):
        raise PackageError("stronger.additional_conditions is not a list")
    for index, condition in enumerate(conditions):
        append_support_pointers(
            condition,
            label=f"stronger.additional_conditions[{index}]",
        )
        artifacts = condition.get("decisive_artifacts")
        if not isinstance(artifacts, list):
            raise PackageError(
                f"stronger.additional_conditions[{index}].decisive_artifacts is not a list"
            )
        for artifact_index, artifact in enumerate(artifacts):
            append_support_pointers(
                artifact,
                label=(
                    f"stronger.additional_conditions[{index}]"
                    f".decisive_artifacts[{artifact_index}]"
                ),
            )

    schema = load_mapping(CHECKLIST_SCHEMA_PATH, "case checklist schema")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(repaired),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise PackageError(f"runtime-repaired checklist is invalid: {errors[0].message}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        yaml.safe_dump(
            repaired,
            allow_unicode=True,
            sort_keys=False,
            width=100,
        ),
        encoding="utf-8",
    )
    roundtrip = yaml.safe_load(destination.read_text(encoding="utf-8"))
    if roundtrip != repaired:
        raise PackageError("runtime-repaired checklist YAML round-trip drift")

    def without_support(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: without_support(child)
                for key, child in value.items()
                if key != "support"
            }
        if isinstance(value, list):
            return [without_support(child) for child in value]
        return value

    if without_support(original) != without_support(repaired):
        raise PackageError("runtime support repair changed checklist rule content")
    return {
        "source_checklist_json_sha256": sha256_file(source),
        "repaired_checklist_json_sha256": sha256_bytes(canonical_json_bytes(repaired)),
        "runtime_support_pointer_count": len(RUNTIME_SUPPORT_POINTERS),
        "rule_content_unchanged": True,
    }


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise PackageError(f"{label} is not a lowercase SHA-256 digest")
    return value


def require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise PackageError(
            f"{label} keys drift; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def require_fields(value: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise PackageError(
                f"{label}.{key} drift: expected {expected_value!r}, found {value.get(key)!r}"
            )


def safe_relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PackageError(f"{label} is not a safe POSIX relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise PackageError(f"{label} is not a normalized POSIX relative path: {value!r}")
    return value


def safe_child(root: Path, *parts: str, label: str) -> Path:
    candidate = root.joinpath(*parts).resolve()
    resolved_root = root.resolve()
    if candidate == resolved_root or resolved_root not in candidate.parents:
        raise PackageError(f"{label} escapes its root: {candidate}")
    return candidate


def roots_overlap(first: Path, second: Path) -> bool:
    first = first.resolve()
    second = second.resolve()
    return first == second or first in second.parents or second in first.parents


def require_disjoint_roots(
    bundle_root: Path,
    run_root: Path,
    runtime_source_root: Path,
    output_root: Path,
) -> None:
    pairs = (
        (bundle_root, run_root, "bundle root", "run root"),
        (bundle_root, runtime_source_root, "bundle root", "runtime source root"),
        (bundle_root, output_root, "bundle root", "output root"),
        (run_root, runtime_source_root, "run root", "runtime source root"),
        (run_root, output_root, "run root", "output root"),
        (runtime_source_root, output_root, "runtime source root", "output root"),
    )
    for first, second, first_label, second_label in pairs:
        if roots_overlap(first, second):
            raise PackageError(f"{first_label} and {second_label} must not overlap")


def expected_evidence_paths(*, include_index: bool = True) -> set[str]:
    paths = set(EXPECTED_OFFICIAL_FILES)
    paths.add("frozen_semantics/appworld_evaluator_semantics.a072b7a8.json")
    paths.add("official/runtime/SOURCE_MANIFEST.json")
    paths.update(f"official/runtime/{relative}" for relative in EXPECTED_RUNTIME_FILES)
    paths.update(f"run/{relative}" for relative in SAFE_RUN_FILES)
    paths.update(f"run/{relative}" for relative in EXPECTED_POSTRUN_DB_FILES)
    paths.add("run/appworld_task_output/logs/lm_calls.redacted.jsonl")
    paths.add("run/run_status.verdict_free.json")
    if include_index:
        paths.add("index.json")
    return paths


def expected_directory_paths(file_paths: Iterable[str]) -> set[str]:
    directories: set[str] = set()
    for value in file_paths:
        parent = PurePosixPath(value).parent
        while parent.as_posix() != ".":
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def validate_exact_file_tree(
    root: Path,
    expected_files: set[str],
    label: str,
) -> list[dict[str, Any]]:
    require_regular_tree(root, label)
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    actual_dirs = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_dir()
    }
    expected_dirs = expected_directory_paths(expected_files)
    if actual_files != expected_files:
        raise PackageError(
            f"{label} file allowlist drift; "
            f"missing={sorted(expected_files - actual_files)}, "
            f"extra={sorted(actual_files - expected_files)}"
        )
    if actual_dirs != expected_dirs:
        raise PackageError(
            f"{label} directory allowlist drift; "
            f"missing={sorted(expected_dirs - actual_dirs)}, "
            f"extra={sorted(actual_dirs - expected_dirs)}"
        )
    return file_entries(root)


def assert_casefold_path_deny(root: Path) -> None:
    forbidden_names = {value.casefold() for value in FORBIDDEN_BASENAMES}
    forbidden_parts = {value.casefold() for value in FORBIDDEN_PATH_PARTS}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        folded_parts = tuple(part.casefold() for part in relative.parts)
        if path.name.casefold() in forbidden_names or any(
            part in forbidden_parts for part in folded_parts
        ):
            raise PackageError(
                f"forbidden artifact escaped into scorer-visible tree: {relative.as_posix()}"
            )


def assert_no_infrastructure_credentials(root: Path) -> None:
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise PackageError(f"scorer-visible file is not UTF-8 text: {path}") from exc
        if INFRA_SECRET_RE.search(text):
            raise PackageError(
                f"infrastructure credential escaped into scorer-visible file: {path}"
            )


def validate_repair_manifest(bundle_root: Path) -> None:
    manifest_path = bundle_root / "repair_manifest.json"
    if sha256_file(manifest_path) != EXPECTED_REPAIR_MANIFEST_SHA256:
        raise PackageError("repair manifest does not match the frozen v3 source lock")
    manifest = load_mapping(manifest_path, "repair manifest")
    require_fields(
        manifest,
        {
            "schema_version": "appworld_checklist_runtime_semantics_repair.v1",
            "case_count": EXPECTED_CASE_COUNT,
            "files_sha256": EXPECTED_REPAIR_FILES_SHA256,
        },
        "repair manifest",
    )
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("file_count_excluding_this_manifest") != len(files):
        raise PackageError("repair manifest file denominator drift")
    if entries_sha256(files) != EXPECTED_REPAIR_FILES_SHA256:
        raise PackageError("repair manifest file aggregate hash drift")
    expected_paths: set[str] = set()
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise PackageError(f"repair manifest files[{index}] is not an object")
        require_exact_keys(entry, {"path", "size_bytes", "sha256"}, f"repair files[{index}]")
        relative = safe_relative_path(entry.get("path"), f"repair files[{index}].path")
        if relative == "repair_manifest.json" or relative in expected_paths:
            raise PackageError(f"duplicate or self-referential repair path: {relative}")
        expected_paths.add(relative)
        source = safe_child(bundle_root, *PurePosixPath(relative).parts, label="repair source")
        if source.is_symlink() or not source.is_file():
            raise PackageError(f"repair source is missing or not regular: {source}")
        if source.stat().st_size != entry.get("size_bytes"):
            raise PackageError(f"repair source size drift: {relative}")
        if sha256_file(source) != require_sha256(entry.get("sha256"), f"repair {relative}"):
            raise PackageError(f"repair source hash drift: {relative}")
    actual_paths = {
        path.relative_to(bundle_root).as_posix()
        for path in bundle_root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual_paths != expected_paths:
        raise PackageError(
            "bundle file inventory differs from repair manifest; "
            f"missing={sorted(expected_paths - actual_paths)}, "
            f"extra={sorted(actual_paths - expected_paths)}"
        )


def case_ids(bundle_root: Path) -> list[str]:
    manifest = load_mapping(bundle_root / "experiment_manifest.json", "experiment manifest")
    if sha256_file(bundle_root / "experiment_manifest.json") != EXPECTED_EXPERIMENT_MANIFEST_SHA256:
        raise PackageError("experiment manifest does not match the frozen v4 source lock")
    scope = manifest.get("scope")
    if not isinstance(scope, dict):
        raise PackageError("experiment manifest scope is missing")
    require_fields(
        scope,
        {
            "benchmark": "AppWorld",
            "dataset_name": "test_normal",
            "case_count": EXPECTED_CASE_COUNT,
            "registered_test_count": EXPECTED_REGISTERED_TEST_COUNT,
            "case_ids_sha256": EXPECTED_CASE_IDS_SHA256,
        },
        "experiment manifest scope",
    )
    values = scope.get("case_ids")
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise PackageError("experiment manifest scope.case_ids is invalid")
    ids = list(values)
    if len(ids) != EXPECTED_CASE_COUNT or len(set(ids)) != EXPECTED_CASE_COUNT:
        raise PackageError(f"expected {EXPECTED_CASE_COUNT} unique case ids, found {len(ids)}")
    for case_id in ids:
        if CASE_ID_RE.fullmatch(case_id) is None:
            raise PackageError(f"unsafe or malformed case id: {case_id!r}")
    expected_hash = str(scope.get("case_ids_sha256") or "")
    if (
        sha256_bytes(canonical_json_bytes(ids)) != expected_hash
        or expected_hash != EXPECTED_CASE_IDS_SHA256
    ):
        raise PackageError("case id set hash does not match the frozen experiment manifest")
    return ids


def validate_freeze_manifest(bundle_root: Path, ids: list[str]) -> dict[str, dict[str, Any]]:
    path = bundle_root / "claim_freeze/freeze_manifest.json"
    if sha256_file(path) != EXPECTED_FREEZE_MANIFEST_SHA256:
        raise PackageError("freeze manifest does not match the frozen v4 source lock")
    manifest = load_mapping(path, "freeze manifest")
    require_fields(
        manifest,
        {
            "schema_version": "appworld_pre_outcome_checklist_freeze.v3_runtime_semantics",
            "case_count": EXPECTED_CASE_COUNT,
            "records_sha256": EXPECTED_FREEZE_RECORDS_SHA256,
        },
        "freeze manifest",
    )
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != EXPECTED_CASE_COUNT:
        raise PackageError("freeze manifest denominator drift")
    if entries_sha256(records) != EXPECTED_FREEZE_RECORDS_SHA256:
        raise PackageError("freeze manifest record aggregate hash drift")
    by_case: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise PackageError(f"freeze records[{index}] is not an object")
        require_exact_keys(
            record,
            {
                "case_unit_id",
                "checklist_json_sha256",
                "checklist_yaml_sha256",
                "case_packet_sha256",
            },
            f"freeze records[{index}]",
        )
        case_id = record.get("case_unit_id")
        if not isinstance(case_id, str) or case_id in by_case:
            raise PackageError(f"duplicate or invalid frozen case id: {case_id!r}")
        for key in ("checklist_json_sha256", "checklist_yaml_sha256", "case_packet_sha256"):
            require_sha256(record.get(key), f"freeze {case_id}.{key}")
        checklist_root = safe_child(
            bundle_root,
            "claim_freeze",
            "checklists",
            case_id,
            label="frozen checklist directory",
        )
        checks = {
            "checklist_json_sha256": checklist_root / "checklist.json",
            "checklist_yaml_sha256": checklist_root / "checklist.yaml",
            "case_packet_sha256": safe_child(
                bundle_root,
                "case_packets",
                "appworld",
                case_id,
                "case_packet.md",
                label="case packet",
            ),
        }
        for key, source in checks.items():
            if sha256_file(source) != record[key]:
                raise PackageError(f"frozen source hash drift for {case_id}/{key}")
        by_case[case_id] = dict(record)
    if list(by_case) != ids:
        raise PackageError("freeze manifest case order/scope differs from experiment manifest")
    return by_case


def validate_bundle_source(
    bundle_root: Path,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    require_regular_tree(bundle_root, "system-design-v4 runtime-semantics bundle")
    validate_repair_manifest(bundle_root)
    ids = case_ids(bundle_root)
    freeze_by_case = validate_freeze_manifest(bundle_root, ids)
    visibility = bundle_root / "artifact_visibility_contract.json"
    semantics = bundle_root / "frozen_semantics/appworld_evaluator_semantics.a072b7a8.json"
    if sha256_file(visibility) != EXPECTED_VISIBILITY_CONTRACT_SHA256:
        raise PackageError("artifact visibility contract hash drift")
    if sha256_file(semantics) != EXPECTED_SEMANTICS_SHA256:
        raise PackageError("frozen evaluator semantics hash drift")
    return ids, freeze_by_case


def locate_record(run_root: Path, case_id: str, agent: str) -> tuple[str, Path]:
    matches: list[tuple[str, Path]] = []
    for vps in ("vps1", "vps2"):
        candidate = safe_child(
            run_root,
            vps,
            "outputs",
            agent,
            case_id,
            label="retained record",
        )
        if candidate.is_dir() and not candidate.is_symlink():
            matches.append((vps, candidate))
    if len(matches) != 1:
        raise PackageError(
            f"expected exactly one retained record for {case_id}/{agent}; found {len(matches)}"
        )
    return matches[0]


def validate_record_identity(
    record_root: Path,
    *,
    case_id: str,
    agent: str,
) -> dict[str, Any]:
    if agent not in AGENT_LABELS:
        raise PackageError(f"unknown agent key: {agent}")
    job = load_mapping(record_root / "job.json", "job metadata")
    source = load_mapping(record_root / "source_bundle_entry.json", "source bundle entry")
    native_input = load_mapping(
        record_root / "native_evaluator_input.json",
        "native evaluator input",
    )
    runner = load_mapping(record_root / "official_runner_config.json", "official runner config")
    source_ref = f"appworld://test_normal/{case_id}"
    require_fields(
        job,
        {
            "schema_version": "job/v1",
            "case_unit_id": case_id,
            "task_id": case_id,
            "agent_id": AGENT_LABELS[agent],
            "dataset_name": "test_normal",
            "domain": "appworld",
            "phase": "full",
            "provider": "openrouter",
            "model": AGENT_MODELS[agent],
        },
        f"{case_id}/{agent} job",
    )
    require_fields(
        source,
        {
            "dataset_name": "test_normal",
            "domain": "appworld",
            "source_ref": source_ref,
            "task_id": case_id,
        },
        f"{case_id}/{agent} source bundle entry",
    )
    require_fields(
        native_input,
        {
            "schema_version": "appworld_native_evaluator_input/v1",
            "dataset_name": "test_normal",
            "source_ref": source_ref,
            "task_id": case_id,
            "model_id": f"openrouter/{AGENT_MODELS[agent]}",
            "official_agent_name": "simplified_react_code_agent",
        },
        f"{case_id}/{agent} native evaluator input",
    )
    if native_input.get("runner_config") != runner:
        raise PackageError(f"{case_id}/{agent} runner config copies disagree")
    if runner.get("dataset") != "test_normal":
        raise PackageError(f"{case_id}/{agent} runner dataset drift")
    runner_agent = runner.get("agent")
    model_config = runner_agent.get("model_config") if isinstance(runner_agent, dict) else None
    if not isinstance(model_config, dict) or model_config.get("name") != (
        f"openrouter/{AGENT_MODELS[agent]}"
    ):
        raise PackageError(f"{case_id}/{agent} official runner model drift")
    code_path = record_root / "appworld_task_output/version/code.txt"
    data_path = record_root / "appworld_task_output/version/data.txt"
    if code_path.is_symlink() or not code_path.is_file() or data_path.is_symlink() or not data_path.is_file():
        raise PackageError(f"{case_id}/{agent} AppWorld version files are missing")
    code = code_path.read_text(encoding="utf-8").strip()
    data = data_path.read_text(encoding="utf-8").strip()
    if code != EXPECTED_APPWORLD_CODE_VERSION or data != EXPECTED_APPWORLD_DATA_VERSION:
        raise PackageError(
            f"{case_id}/{agent} AppWorld version drift: code={code!r}, data={data!r}"
        )
    return {
        "case_unit_id": case_id,
        "task_id": case_id,
        "agent_key": agent,
        "agent_id": AGENT_LABELS[agent],
        "dataset_name": "test_normal",
        "domain": "appworld",
        "source_ref": source_ref,
        "appworld_code_version": code,
        "appworld_data_version": data,
        "job_sha256": sha256_file(record_root / "job.json"),
        "source_bundle_entry_sha256": sha256_file(record_root / "source_bundle_entry.json"),
        "native_evaluator_input_sha256": sha256_file(record_root / "native_evaluator_input.json"),
        "official_runner_config_sha256": sha256_file(record_root / "official_runner_config.json"),
    }


def public_lm_record(raw: Mapping[str, Any], *, call_index: int) -> dict[str, Any]:
    output = raw.get("output")
    output_mapping = output if isinstance(output, Mapping) else {}
    public_choices: list[dict[str, Any]] = []
    choices = output_mapping.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, Mapping):
                continue
            message = choice.get("message")
            message_mapping = message if isinstance(message, Mapping) else {}
            public_choices.append(
                {
                    "index": choice.get("index"),
                    "finish_reason": choice.get("finish_reason"),
                    "message": {
                        key: message_mapping.get(key)
                        for key in ("role", "content", "function_call", "tool_calls")
                    },
                }
            )
    value = {
        "call_index": call_index,
        "call_id": raw.get("id"),
        "model": output_mapping.get("model"),
        "created": output_mapping.get("created"),
        "timestamps": output_mapping.get("timestamps"),
        "choices": public_choices,
    }
    encoded = json.dumps(value, ensure_ascii=False)
    encoded = INFRA_SECRET_RE.sub("<REDACTED_INFRA_CREDENTIAL>", encoded)
    result = json.loads(encoded)
    if not isinstance(result, dict):
        raise PackageError("derived LM action record is not an object")
    return result


def derive_lm_actions(source: Path, destination: Path) -> dict[str, Any]:
    if source.is_symlink() or not source.is_file():
        raise PackageError(f"LM call log is missing or not a regular file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    output_lines: list[str] = []
    for call_index, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PackageError(f"invalid LM call JSONL at {source}:{call_index}: {exc}") from exc
        if not isinstance(raw, dict):
            raise PackageError(f"LM call record is not an object at {source}:{call_index}")
        output_lines.append(json.dumps(public_lm_record(raw, call_index=call_index), ensure_ascii=False))
    destination.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
    text = destination.read_text(encoding="utf-8")
    if INFRA_SECRET_RE.search(text):
        raise PackageError(f"derived LM action log still contains an infrastructure credential: {destination}")
    return {
        "source_record_count": len(output_lines),
        "projection": LM_PROJECTION_DESCRIPTION,
    }


def build_run_status(record_root: Path, destination: Path) -> None:
    job = load_mapping(record_root / "job.json", "job metadata")
    source = load_mapping(record_root / "source_bundle_entry.json", "source bundle entry")
    finished = record_root / "appworld_task_output" / "misc" / "finished"
    if finished.is_symlink() or not finished.is_file():
        raise PackageError(f"verdict-free finished marker is missing: {finished}")
    value = {
        "schema_version": "appworld_verdict_free_run_status.v1",
        "case_unit_id": job.get("case_unit_id"),
        "task_id": job.get("task_id"),
        "agent_id": job.get("agent_id"),
        "record_slot_id": job.get("record_slot_id"),
        "dataset_name": job.get("dataset_name"),
        "domain": job.get("domain"),
        "provider": job.get("provider"),
        "model": job.get("model"),
        "seed": job.get("seed"),
        "source_ref": source.get("source_ref"),
        "termination_evidence": {
            "finished_marker_present": True,
            "finished_marker_sha256": sha256_file(finished),
        },
        "versions": {
            "code": (record_root / "appworld_task_output/version/code.txt").read_text(encoding="utf-8").strip(),
            "data": (record_root / "appworld_task_output/version/data.txt").read_text(encoding="utf-8").strip(),
        },
    }
    forbidden_keys = {"success", "score", "reward", "label", "passes", "failures", "num_tests"}
    if any(key in forbidden_keys for key in value):
        raise PackageError("verdict-free status unexpectedly contains a forbidden key")
    write_json(destination, value)


def validate_lm_projection(path: Path, expected_count: int) -> None:
    if path.is_symlink() or not path.is_file():
        raise PackageError(f"LM projection is missing or not regular: {path}")
    count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        count += 1
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PackageError(f"invalid projected LM JSONL at {path}:{line_number}") from exc
        if not isinstance(record, dict):
            raise PackageError(f"projected LM record is not an object at {path}:{line_number}")
        require_exact_keys(
            record,
            {"call_index", "call_id", "model", "created", "timestamps", "choices"},
            f"projected LM record {line_number}",
        )
        if not isinstance(record.get("call_index"), int) or record["call_index"] < 1:
            raise PackageError(f"invalid projected LM call index at {path}:{line_number}")
        choices = record.get("choices")
        if not isinstance(choices, list):
            raise PackageError(f"projected LM choices are invalid at {path}:{line_number}")
        for choice_index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                raise PackageError(
                    f"projected LM choice is not an object at {path}:{line_number}/{choice_index}"
                )
            require_exact_keys(
                choice,
                {"index", "finish_reason", "message"},
                f"projected LM choice {line_number}/{choice_index}",
            )
            message = choice.get("message")
            if not isinstance(message, dict):
                raise PackageError(
                    f"projected LM message is invalid at {path}:{line_number}/{choice_index}"
                )
            require_exact_keys(
                message,
                {"role", "content", "function_call", "tool_calls"},
                f"projected LM message {line_number}/{choice_index}",
            )
    if count != expected_count:
        raise PackageError(
            f"projected LM record count drift: expected {expected_count}, found {count}"
        )


def assert_blind_evidence(
    evidence_root: Path,
    *,
    include_index: bool = True,
) -> list[dict[str, Any]]:
    entries = validate_exact_file_tree(
        evidence_root,
        expected_evidence_paths(include_index=include_index),
        "blind evidence tree",
    )
    assert_casefold_path_deny(evidence_root)
    assert_no_infrastructure_credentials(evidence_root)
    return entries


def validate_evidence_index(
    evidence_root: Path,
    *,
    case_id: str,
    agent: str,
    vps: str,
) -> dict[str, Any]:
    index_path = evidence_root / "index.json"
    index = load_mapping(index_path, "blind evidence index")
    require_exact_keys(
        index,
        {
            "schema_version",
            "case_unit_id",
            "agent_id",
            "source_vps",
            "projection_contract",
            "evaluator_runtime",
            "released_result_artifacts_present",
            "component_evaluator_outputs_present",
            "evaluator_reports_present",
            "lm_projection",
            "files",
            "files_sha256",
        },
        f"{case_id}/{agent} evidence index",
    )
    require_fields(
        index,
        {
            "schema_version": "appworld_blind_evidence_inventory.v2_runtime_semantics",
            "case_unit_id": case_id,
            "agent_id": agent,
            "source_vps": vps,
            "projection_contract": "package_manifest.json::source_lock+outcome_blind.v3",
            "evaluator_runtime": EVALUATOR_RUNTIME_LOCK,
            "released_result_artifacts_present": False,
            "component_evaluator_outputs_present": False,
            "evaluator_reports_present": False,
        },
        f"{case_id}/{agent} evidence index",
    )
    indexed_files = index.get("files")
    if not isinstance(indexed_files, list):
        raise PackageError(f"{case_id}/{agent} evidence index files are invalid")
    actual_files = [
        entry
        for entry in file_entries(evidence_root)
        if entry["path"] != "index.json"
    ]
    if indexed_files != actual_files:
        raise PackageError(f"{case_id}/{agent} evidence index file inventory drift")
    if index.get("files_sha256") != entries_sha256(actual_files):
        raise PackageError(f"{case_id}/{agent} evidence index aggregate hash drift")
    lm_projection = index.get("lm_projection")
    if not isinstance(lm_projection, dict):
        raise PackageError(f"{case_id}/{agent} LM projection receipt is invalid")
    require_exact_keys(
        lm_projection,
        {"source_record_count", "projection"},
        f"{case_id}/{agent} LM projection receipt",
    )
    count = lm_projection.get("source_record_count")
    if not isinstance(count, int) or count < 0:
        raise PackageError(f"{case_id}/{agent} LM projection count is invalid")
    if lm_projection.get("projection") != LM_PROJECTION_DESCRIPTION:
        raise PackageError(f"{case_id}/{agent} LM projection contract drift")
    validate_lm_projection(
        evidence_root / "run/appworld_task_output/logs/lm_calls.redacted.jsonl",
        count,
    )
    return index


def build_task(
    *,
    bundle_root: Path,
    runtime_source_root: Path,
    record_root: Path,
    vps: str,
    case_id: str,
    agent: str,
    freeze_record: Mapping[str, Any],
    task_dir: Path,
) -> dict[str, Any]:
    identity = validate_record_identity(record_root, case_id=case_id, agent=agent)
    checklist_root = safe_child(
        bundle_root,
        "claim_freeze",
        "checklists",
        case_id,
        label="frozen checklist directory",
    )
    checklist_source = checklist_root / "checklist.yaml"
    checklist_json = checklist_root / "checklist.json"
    if sha256_file(checklist_source) != freeze_record.get("checklist_yaml_sha256"):
        raise PackageError(f"frozen checklist YAML hash drift for {case_id}")
    if sha256_file(checklist_json) != freeze_record.get("checklist_json_sha256"):
        raise PackageError(f"frozen checklist JSON hash drift for {case_id}")
    # The scorer receives the already-frozen v4 YAML byte-for-byte.  Checklist
    # amendment here would cross the pre-outcome lock boundary because this
    # function also handles retained execution records.
    copy_regular_file(
        checklist_source,
        task_dir / "checklist.yaml",
        f"pre-outcome frozen checklist {case_id}",
    )

    evidence_root = task_dir / "evidence"
    raw_case = safe_child(
        bundle_root,
        "case_packets",
        "appworld",
        case_id,
        "raw_case",
        label="official raw case",
    )
    for relative in EXPECTED_OFFICIAL_FILES:
        copy_regular_file(raw_case / relative, evidence_root / relative, f"official source {relative}")
    copy_regular_file(
        raw_case / "official/runtime/SOURCE_MANIFEST.json",
        evidence_root / "official/runtime/SOURCE_MANIFEST.json",
        "released AppWorld runtime source manifest",
    )
    for relative in EXPECTED_RUNTIME_FILES:
        copy_regular_file(
            raw_case / "official/runtime" / relative,
            evidence_root / "official/runtime" / relative,
            f"released AppWorld runtime source {relative}",
        )
    semantics = bundle_root / "frozen_semantics" / "appworld_evaluator_semantics.a072b7a8.json"
    copy_regular_file(
        semantics,
        evidence_root / "frozen_semantics" / semantics.name,
        "frozen evaluator semantics",
    )

    for relative in SAFE_RUN_FILES:
        copy_regular_file(
            record_root / relative,
            evidence_root / "run" / relative,
            f"allowlisted run artifact {relative}",
        )
    for relative in SAFE_RUN_TREES:
        copy_regular_tree(
            record_root / relative,
            evidence_root / "run" / relative,
            f"allowlisted run artifact tree {relative}",
        )
    lm_projection = derive_lm_actions(
        record_root / "appworld_task_output/logs/lm_calls.jsonl",
        evidence_root / "run/appworld_task_output/logs/lm_calls.redacted.jsonl",
    )
    build_run_status(record_root, evidence_root / "run/run_status.verdict_free.json")

    entries_before_index = assert_blind_evidence(evidence_root, include_index=False)
    inventory = {
        "schema_version": "appworld_blind_evidence_inventory.v2_runtime_semantics",
        "case_unit_id": case_id,
        "agent_id": agent,
        "source_vps": vps,
        "projection_contract": "package_manifest.json::source_lock+outcome_blind.v3",
        "evaluator_runtime": EVALUATOR_RUNTIME_LOCK,
        "released_result_artifacts_present": False,
        "component_evaluator_outputs_present": False,
        "evaluator_reports_present": False,
        "lm_projection": lm_projection,
        "files": entries_before_index,
        "files_sha256": entries_sha256(entries_before_index),
    }
    write_json(evidence_root / "index.json", inventory)
    entries = assert_blind_evidence(evidence_root)
    validate_evidence_index(
        evidence_root,
        case_id=case_id,
        agent=agent,
        vps=vps,
    )
    record_entries = file_entries(record_root)
    if len(record_entries) != EXPECTED_RETAINED_RECORD_FILE_COUNT:
        raise PackageError(
            f"expected {EXPECTED_RETAINED_RECORD_FILE_COUNT} retained files for "
            f"{case_id}/{agent}, found {len(record_entries)}"
        )
    return {
        "task_id": task_dir.name,
        "case_unit_id": case_id,
        "agent_id": agent,
        "source_vps": vps,
        "checklist_sha256": sha256_file(task_dir / "checklist.yaml"),
        "checklist_json_sha256": sha256_file(checklist_json),
        "frozen_checklist_yaml_sha256": sha256_file(checklist_source),
        "record_identity_sha256": sha256_bytes(canonical_json_bytes(identity)),
        "evidence_index_sha256": sha256_file(evidence_root / "index.json"),
        "evidence_file_count": len(entries),
        "evidence_size_bytes": sum(int(entry["size_bytes"]) for entry in entries),
        "evidence_files_sha256": entries_sha256(entries),
        "retained_record_file_count": len(record_entries),
        "retained_record_size_bytes": sum(int(entry["size_bytes"]) for entry in record_entries),
        "retained_record_files_sha256": entries_sha256(record_entries),
    }


def build_package(
    bundle_root: Path,
    run_root: Path,
    runtime_source_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    require_disjoint_roots(bundle_root, run_root, runtime_source_root, output_root)
    ids, freeze_by_case = validate_bundle_source(bundle_root)
    validate_runtime_source(runtime_source_root)
    require_regular_tree(run_root, "retrieved AppWorld records")
    retrieval_manifest = run_root / "RETRIEVAL_MANIFEST.json"
    if sha256_file(retrieval_manifest) != EXPECTED_RETRIEVAL_MANIFEST_SHA256:
        raise PackageError("retrieval manifest does not match the frozen source lock")
    if output_root.exists():
        raise PackageError(f"refusing to overwrite existing output root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=False)
    public_root = output_root / "public_score_job"
    tasks_root = public_root / "tasks"
    tasks_root.mkdir(parents=True)

    records: list[dict[str, Any]] = []
    retained_sources: list[dict[str, Any]] = []
    for case_id in ids:
        for agent in AGENTS:
            vps, record_root = locate_record(run_root, case_id, agent)
            task_id = f"{case_id}__{agent}"
            task_dir = safe_child(tasks_root, task_id, label="score task")
            record = build_task(
                bundle_root=bundle_root,
                runtime_source_root=runtime_source_root,
                record_root=record_root,
                vps=vps,
                case_id=case_id,
                agent=agent,
                freeze_record=freeze_by_case[case_id],
                task_dir=task_dir,
            )
            records.append(record)
            retained_sources.append(
                {
                    "task_id": task_id,
                    "case_unit_id": case_id,
                    "agent_id": agent,
                    "source_vps": vps,
                    "source_relative_path": f"{vps}/outputs/{agent}/{case_id}",
                    "file_count": record["retained_record_file_count"],
                    "size_bytes": record["retained_record_size_bytes"],
                    "files_sha256": record["retained_record_files_sha256"],
                }
            )

    if len(records) != EXPECTED_RECORD_COUNT:
        raise PackageError(f"expected {EXPECTED_RECORD_COUNT} score records, built {len(records)}")
    public_manifest = {
        "schema_version": SCHEMA_VERSION,
        "scope": {
            "benchmark": "AppWorld",
            "dataset_name": "test_normal",
            "case_count": len(ids),
            "registered_test_count": EXPECTED_REGISTERED_TEST_COUNT,
            "agents": list(AGENTS),
            "record_count": len(records),
            "case_ids": ids,
            "case_ids_sha256": sha256_bytes(canonical_json_bytes(ids)),
        },
        "scoring_lock": SCORING_LOCK,
        "source_lock": SOURCE_LOCK,
        "outcome_blind": OUTCOME_BLIND_LOCK,
        "records": records,
        "records_sha256": sha256_bytes(canonical_json_bytes(records)),
    }
    write_json(public_root / "package_manifest.json", public_manifest)
    retained_manifest = {
        "schema_version": RETAINED_SCHEMA_VERSION,
        "note": (
            "This byte-level manifest does not parse or expose released results. "
            "Transfer these source directories only to a root-owned 0700 area that the scorer user cannot read."
        ),
        "record_count": len(retained_sources),
        "records": retained_sources,
        "records_sha256": sha256_bytes(canonical_json_bytes(retained_sources)),
    }
    write_json(output_root / "retained_transfer_manifest.json", retained_manifest)
    public_entries = file_entries(public_root)
    write_json(
        output_root / "build_receipt.json",
        {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "public_package_manifest_sha256": sha256_file(public_root / "package_manifest.json"),
            "retained_transfer_manifest_sha256": sha256_file(output_root / "retained_transfer_manifest.json"),
            "public_task_count": len(records),
            "public_score_job_file_count": len(public_entries),
            "public_score_job_size_bytes": sum(int(entry["size_bytes"]) for entry in public_entries),
            "public_score_job_files_sha256": entries_sha256(public_entries),
            "source_bundle_file_sha256": EXPECTED_REPAIR_MANIFEST_SHA256,
            "source_retrieval_manifest_sha256": EXPECTED_RETRIEVAL_MANIFEST_SHA256,
            "source_evaluator_runtime_manifest_sha256": (
                EXPECTED_RUNTIME_MANIFEST_SHA256
            ),
            "builder_script_sha256": sha256_file(Path(__file__).resolve()),
        },
    )
    return validate_package(output_root)


def validate_run_status(
    evidence_root: Path,
    *,
    case_id: str,
    agent: str,
) -> None:
    path = evidence_root / "run/run_status.verdict_free.json"
    status = load_mapping(path, "verdict-free run status")
    require_exact_keys(
        status,
        {
            "schema_version",
            "case_unit_id",
            "task_id",
            "agent_id",
            "record_slot_id",
            "dataset_name",
            "domain",
            "provider",
            "model",
            "seed",
            "source_ref",
            "termination_evidence",
            "versions",
        },
        f"{case_id}/{agent} verdict-free run status",
    )
    require_fields(
        status,
        {
            "schema_version": "appworld_verdict_free_run_status.v1",
            "case_unit_id": case_id,
            "task_id": case_id,
            "agent_id": AGENT_LABELS[agent],
            "dataset_name": "test_normal",
            "domain": "appworld",
            "provider": "openrouter",
            "model": AGENT_MODELS[agent],
            "source_ref": f"appworld://test_normal/{case_id}",
        },
        f"{case_id}/{agent} verdict-free run status",
    )
    versions = status.get("versions")
    termination = status.get("termination_evidence")
    if versions != {
        "code": EXPECTED_APPWORLD_CODE_VERSION,
        "data": EXPECTED_APPWORLD_DATA_VERSION,
    }:
        raise PackageError(f"{case_id}/{agent} verdict-free version receipt drift")
    finished = evidence_root / "run/appworld_task_output/misc/finished"
    if termination != {
        "finished_marker_present": True,
        "finished_marker_sha256": sha256_file(finished),
    }:
        raise PackageError(f"{case_id}/{agent} termination receipt drift")


def validate_package(output_root: Path) -> dict[str, Any]:
    require_regular_tree(output_root, "blind score input package")
    root_files = {path.name for path in output_root.iterdir() if path.is_file()}
    root_dirs = {path.name for path in output_root.iterdir() if path.is_dir()}
    if root_files != {"build_receipt.json", "retained_transfer_manifest.json"} or root_dirs != {
        "public_score_job"
    }:
        raise PackageError(
            "blind package root allowlist drift; "
            f"files={sorted(root_files)}, directories={sorted(root_dirs)}"
        )

    public_root = output_root / "public_score_job"
    require_regular_tree(public_root, "scorer-visible public job")
    public_files = {path.name for path in public_root.iterdir() if path.is_file()}
    public_dirs = {path.name for path in public_root.iterdir() if path.is_dir()}
    if public_files != {"package_manifest.json"} or public_dirs != {"tasks"}:
        raise PackageError(
            "scorer-visible root allowlist drift; "
            f"files={sorted(public_files)}, directories={sorted(public_dirs)}"
        )
    assert_casefold_path_deny(public_root)

    manifest_path = public_root / "package_manifest.json"
    manifest = load_mapping(manifest_path, "public package manifest")
    schema = manifest.get("schema_version")
    if schema != SCHEMA_VERSION:
        if schema == "appworld68_blind_score_input_package.v1":
            raise PackageError(
                "public package schema v1 predates fail-closed whole-tree validation; "
                "rebuild the package with this v2 builder"
            )
        raise PackageError(f"public package manifest schema version drift: {schema!r}")
    require_exact_keys(
        manifest,
        {
            "schema_version",
            "scope",
            "scoring_lock",
            "source_lock",
            "outcome_blind",
            "records",
            "records_sha256",
        },
        "public package manifest",
    )
    scope = manifest.get("scope")
    records = manifest.get("records")
    if not isinstance(scope, dict) or not isinstance(records, list):
        raise PackageError("public package manifest scope or records is invalid")
    require_exact_keys(
        scope,
        {
            "benchmark",
            "dataset_name",
            "case_count",
            "registered_test_count",
            "agents",
            "record_count",
            "case_ids",
            "case_ids_sha256",
        },
        "public package scope",
    )
    ids = scope.get("case_ids")
    if not isinstance(ids, list) or not all(isinstance(value, str) for value in ids):
        raise PackageError("public package case id list is invalid")
    if len(ids) != EXPECTED_CASE_COUNT or len(set(ids)) != EXPECTED_CASE_COUNT:
        raise PackageError("public package case denominator or uniqueness drift")
    for case_id in ids:
        if CASE_ID_RE.fullmatch(case_id) is None:
            raise PackageError(f"unsafe or malformed packaged case id: {case_id!r}")
    expected_scope = {
        "benchmark": "AppWorld",
        "dataset_name": "test_normal",
        "case_count": EXPECTED_CASE_COUNT,
        "registered_test_count": EXPECTED_REGISTERED_TEST_COUNT,
        "agents": list(AGENTS),
        "record_count": EXPECTED_RECORD_COUNT,
        "case_ids": ids,
        "case_ids_sha256": EXPECTED_CASE_IDS_SHA256,
    }
    if scope != expected_scope or sha256_bytes(canonical_json_bytes(ids)) != EXPECTED_CASE_IDS_SHA256:
        raise PackageError("public package scope differs from the frozen 68-case scope")
    if manifest.get("scoring_lock") != SCORING_LOCK:
        raise PackageError("gpt-5.4/high/default/non-fast/Codex-login/c34 scoring lock drift")
    if manifest.get("source_lock") != SOURCE_LOCK:
        raise PackageError("public package frozen source lock drift")
    if manifest.get("outcome_blind") != OUTCOME_BLIND_LOCK:
        raise PackageError("public package outcome-blind contract drift")
    if len(records) != EXPECTED_RECORD_COUNT:
        raise PackageError("public package record list length drift")
    if manifest.get("records_sha256") != sha256_bytes(canonical_json_bytes(records)):
        raise PackageError("public package record aggregate hash drift")

    expected_pairs = [(case_id, agent) for case_id in ids for agent in AGENTS]
    expected_task_ids = [f"{case_id}__{agent}" for case_id, agent in expected_pairs]
    tasks_root = public_root / "tasks"
    require_regular_tree(tasks_root, "scorer-visible task root")
    immediate_task_files = [path.name for path in tasks_root.iterdir() if path.is_file()]
    actual_task_dirs = [path.name for path in tasks_root.iterdir() if path.is_dir()]
    if immediate_task_files or set(actual_task_dirs) != set(expected_task_ids):
        raise PackageError(
            "scorer-visible task Cartesian product drift; "
            f"unexpected_files={sorted(immediate_task_files)}, "
            f"missing={sorted(set(expected_task_ids) - set(actual_task_dirs))}, "
            f"extra={sorted(set(actual_task_dirs) - set(expected_task_ids))}"
        )

    record_keys = {
        "task_id",
        "case_unit_id",
        "agent_id",
        "source_vps",
        "checklist_sha256",
        "checklist_json_sha256",
        "frozen_checklist_yaml_sha256",
        "record_identity_sha256",
        "evidence_index_sha256",
        "evidence_file_count",
        "evidence_size_bytes",
        "evidence_files_sha256",
        "retained_record_file_count",
        "retained_record_size_bytes",
        "retained_record_files_sha256",
    }
    total_files = 0
    total_bytes = 0
    public_records_by_task: dict[str, dict[str, Any]] = {}
    for index, ((case_id, agent), expected_task_id, record) in enumerate(
        zip(expected_pairs, expected_task_ids, records, strict=True)
    ):
        if not isinstance(record, dict):
            raise PackageError(f"public package records[{index}] is not an object")
        require_exact_keys(record, record_keys, f"public package records[{index}]")
        require_fields(
            record,
            {
                "task_id": expected_task_id,
                "case_unit_id": case_id,
                "agent_id": agent,
            },
            f"public package records[{index}]",
        )
        vps = record.get("source_vps")
        if vps not in {"vps1", "vps2"}:
            raise PackageError(f"invalid source VPS for {expected_task_id}: {vps!r}")
        for key in (
            "checklist_sha256",
            "checklist_json_sha256",
            "frozen_checklist_yaml_sha256",
            "record_identity_sha256",
            "evidence_index_sha256",
            "evidence_files_sha256",
            "retained_record_files_sha256",
        ):
            require_sha256(record.get(key), f"{expected_task_id}.{key}")
        if record.get("evidence_file_count") != len(expected_evidence_paths()):
            raise PackageError(f"evidence file denominator drift for {expected_task_id}")
        if record.get("retained_record_file_count") != EXPECTED_RETAINED_RECORD_FILE_COUNT:
            raise PackageError(f"retained file denominator drift for {expected_task_id}")
        for key in ("evidence_size_bytes", "retained_record_size_bytes"):
            if not isinstance(record.get(key), int) or record[key] < 0:
                raise PackageError(f"invalid byte count {expected_task_id}.{key}")

        task_dir = safe_child(tasks_root, expected_task_id, label="score task")
        task_expected_files = {"checklist.yaml"} | {
            f"evidence/{relative}" for relative in expected_evidence_paths()
        }
        validate_exact_file_tree(task_dir, task_expected_files, f"task {expected_task_id}")
        checklist = task_dir / "checklist.yaml"
        evidence = task_dir / "evidence"
        if sha256_file(checklist) != record.get("checklist_sha256"):
            raise PackageError(f"checklist hash drift for {expected_task_id}")
        entries = assert_blind_evidence(evidence)
        validate_evidence_index(
            evidence,
            case_id=case_id,
            agent=agent,
            vps=str(vps),
        )
        validate_run_status(evidence, case_id=case_id, agent=agent)
        identity = validate_record_identity(evidence / "run", case_id=case_id, agent=agent)
        if sha256_bytes(canonical_json_bytes(identity)) != record.get("record_identity_sha256"):
            raise PackageError(f"record identity receipt drift for {expected_task_id}")
        if sha256_file(evidence / "index.json") != record.get("evidence_index_sha256"):
            raise PackageError(f"evidence index hash drift for {expected_task_id}")
        if len(entries) != record.get("evidence_file_count"):
            raise PackageError(f"evidence file-count drift for {expected_task_id}")
        if entries_sha256(entries) != record.get("evidence_files_sha256"):
            raise PackageError(f"evidence tree hash drift for {expected_task_id}")
        size_bytes = sum(int(entry["size_bytes"]) for entry in entries)
        if size_bytes != record.get("evidence_size_bytes"):
            raise PackageError(f"evidence size drift for {expected_task_id}")
        total_files += len(entries)
        total_bytes += size_bytes
        public_records_by_task[expected_task_id] = record

    assert_no_infrastructure_credentials(public_root)

    retained_path = output_root / "retained_transfer_manifest.json"
    retained = load_mapping(retained_path, "retained transfer manifest")
    require_exact_keys(
        retained,
        {"schema_version", "note", "record_count", "records", "records_sha256"},
        "retained transfer manifest",
    )
    if retained.get("schema_version") != RETAINED_SCHEMA_VERSION:
        raise PackageError("retained transfer manifest schema drift")
    retained_records = retained.get("records")
    if (
        retained.get("record_count") != EXPECTED_RECORD_COUNT
        or not isinstance(retained_records, list)
        or len(retained_records) != EXPECTED_RECORD_COUNT
    ):
        raise PackageError("retained transfer denominator drift")
    if retained.get("records_sha256") != sha256_bytes(canonical_json_bytes(retained_records)):
        raise PackageError("retained transfer aggregate hash drift")
    retained_keys = {
        "task_id",
        "case_unit_id",
        "agent_id",
        "source_vps",
        "source_relative_path",
        "file_count",
        "size_bytes",
        "files_sha256",
    }
    for index, (expected_task_id, retained_record) in enumerate(
        zip(expected_task_ids, retained_records, strict=True)
    ):
        if not isinstance(retained_record, dict):
            raise PackageError(f"retained records[{index}] is not an object")
        require_exact_keys(retained_record, retained_keys, f"retained records[{index}]")
        public_record = public_records_by_task[expected_task_id]
        expected_retained = {
            "task_id": expected_task_id,
            "case_unit_id": public_record["case_unit_id"],
            "agent_id": public_record["agent_id"],
            "source_vps": public_record["source_vps"],
            "source_relative_path": (
                f"{public_record['source_vps']}/outputs/"
                f"{public_record['agent_id']}/{public_record['case_unit_id']}"
            ),
            "file_count": public_record["retained_record_file_count"],
            "size_bytes": public_record["retained_record_size_bytes"],
            "files_sha256": public_record["retained_record_files_sha256"],
        }
        if retained_record != expected_retained:
            raise PackageError(f"public/retained crosscheck drift for {expected_task_id}")
        safe_relative_path(
            retained_record["source_relative_path"],
            f"retained records[{index}].source_relative_path",
        )

    receipt_path = output_root / "build_receipt.json"
    receipt = load_mapping(receipt_path, "build receipt")
    require_exact_keys(
        receipt,
        {
            "schema_version",
            "public_package_manifest_sha256",
            "retained_transfer_manifest_sha256",
            "public_task_count",
            "public_score_job_file_count",
            "public_score_job_size_bytes",
            "public_score_job_files_sha256",
            "source_bundle_file_sha256",
            "source_retrieval_manifest_sha256",
            "source_evaluator_runtime_manifest_sha256",
            "builder_script_sha256",
        },
        "build receipt",
    )
    public_entries = file_entries(public_root)
    expected_receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "public_package_manifest_sha256": sha256_file(manifest_path),
        "retained_transfer_manifest_sha256": sha256_file(retained_path),
        "public_task_count": EXPECTED_RECORD_COUNT,
        "public_score_job_file_count": len(public_entries),
        "public_score_job_size_bytes": sum(int(entry["size_bytes"]) for entry in public_entries),
        "public_score_job_files_sha256": entries_sha256(public_entries),
        "source_bundle_file_sha256": EXPECTED_REPAIR_MANIFEST_SHA256,
        "source_retrieval_manifest_sha256": EXPECTED_RETRIEVAL_MANIFEST_SHA256,
        "source_evaluator_runtime_manifest_sha256": EXPECTED_RUNTIME_MANIFEST_SHA256,
        "builder_script_sha256": sha256_file(Path(__file__).resolve()),
    }
    if receipt != expected_receipt:
        raise PackageError("build receipt or public scorer-view tree hash drift")
    expected_public_file_count = 1 + EXPECTED_RECORD_COUNT * (
        1 + len(expected_evidence_paths())
    )
    if len(public_entries) != expected_public_file_count:
        raise PackageError(
            f"public scorer-view file denominator drift: expected "
            f"{expected_public_file_count}, found {len(public_entries)}"
        )
    return {
        "status": "valid",
        "schema_version": SCHEMA_VERSION,
        "case_count": EXPECTED_CASE_COUNT,
        "record_count": EXPECTED_RECORD_COUNT,
        "evidence_file_count": total_files,
        "evidence_size_bytes": total_bytes,
        "public_score_job_file_count": len(public_entries),
        "public_package_manifest_sha256": sha256_file(manifest_path),
        "retained_transfer_manifest_sha256": sha256_file(retained_path),
        "public_score_job_files_sha256": entries_sha256(public_entries),
    }


def main() -> int:
    args = parse_args()
    bundle_root = args.bundle_root.resolve()
    run_root = args.run_root.resolve()
    runtime_source_root = args.runtime_source_root.resolve()
    output_root = args.output_root.resolve()
    try:
        if args.check:
            result = validate_package(output_root)
        else:
            result = build_package(bundle_root, run_root, runtime_source_root, output_root)
    except (OSError, PackageError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
