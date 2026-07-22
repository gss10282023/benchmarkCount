#!/usr/bin/env python3
"""Build and strictly validate the isolated AndroidWorld candidate-116 packets.

This script deliberately writes only below
``rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116``.
It treats the submitted baseline, legacy results, and the checked-in official100
selector as immutable inputs.
"""

from __future__ import annotations

import argparse
import ast
import copy
import datetime
import hashlib
import importlib.util
import inspect
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))

from evidence_system.contracts.case_packets import (  # noqa: E402
    build_case_packet_source_bundle,
    derive_source_context,
    render_case_packet,
    validate_case_packet_source,
)
from evidence_system.contracts.common import find_forbidden_inputs  # noqa: E402
from evidence_system.contracts.draft import (  # noqa: E402
    DEFAULT_PROMPT_VERSION,
    build_drafter_prompt,
    load_source_bundle,
)
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path  # noqa: E402
from evidence_system.core.schemas import validate_object  # noqa: E402

from freeze_and_slots import (  # noqa: E402
    EMPTY_LIST_HASH,
    EXPECTED_CANDIDATE116_SLOT_HASH,
    EXPECTED_EXTRA16_SLOT_HASH,
    EXPECTED_OFFICIAL100_SLOT_HASH,
    assert_known_slot_hashes,
    build_candidate116_slot_ledger,
    build_contract_drafter_config,
    build_draft_input_freeze,
    build_per_case_draft_bindings,
    build_prelock_manifest_binding,
    payload_sha256,
    project_contract_drafter_llm_role,
    validate_candidate116_slot_ledger,
    validate_draft_input_freeze,
)
from semantic_extractor import extract_canonical_semantic_records  # noqa: E402
from strict_acceptance import AcceptancePaths, validate_strict_acceptance  # noqa: E402


SELECTION_SALT = "appendix-androidworld-workarena-selection-v1"
EXPECTED_CANDIDATE_SHA256 = "7607547c0370671b697fa7cccbbffa36a6f97d4ca8de032b874c5ae9b59f3dbb"
EXPECTED_OFFICIAL100_SHA256 = "6aa7d2b447742c2333192424941198ca8c8226c29141badfcae09b644a12c320"
EXPECTED_SOURCE_COMMIT = "d9c569f764b3a5629321858de03ff653d0f24056"
BUILD_TIMESTAMP = "2026-07-16T00:00:00+10:00"

CANDIDATE_POOL = REPO_ROOT / "experiments/official_splits/androidworld_official_task_metadata_116.json"
OFFICIAL100 = REPO_ROOT / "experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json"
FULL100_MANIFEST = REPO_ROOT / "experiments/appendix/androidworld_full100_manifest.json"
LOCK_SPEC = REPO_ROOT / "rebuttal_work/00_submission_repo_lock/submission_repo_lock.json"

MANIFEST_DIR = WORK_ROOT / "manifests"
SELECTOR_DIR = WORK_ROOT / "official_splits"
PACKET_ROOT = WORK_ROOT / "case_packets"
BUNDLE_DIR = WORK_ROOT / "source_bundles"
VALIDATION_DIR = WORK_ROOT / "validation"
INDEX_DIR = WORK_ROOT / "indexes"
SHARED_DIR = WORK_ROOT / "shared_source"
SEMANTIC_DIR = WORK_ROOT / "semantic_records"
CONFIG_DIR = WORK_ROOT / "draft_config"
PROMPT_DIR = WORK_ROOT / "prompts"
FREEZE_DIR = WORK_ROOT / "freeze"
LEDGER_DIR = WORK_ROOT / "ledgers"
DRAFT_OUTPUT_DIR = WORK_ROOT / "drafts"
DRAFT_LOG_DIR = WORK_ROOT / "draft_logs"

CANDIDATE_MANIFEST = MANIFEST_DIR / "androidworld_candidate116_manifest.json"
EXTRA16_MANIFEST = MANIFEST_DIR / "androidworld_extra16_manifest.json"
CANDIDATE_SELECTOR = SELECTOR_DIR / "androidworld_candidate116_selected_task_sources.json"
EXTRA16_SELECTOR = SELECTOR_DIR / "androidworld_extra16_selected_task_sources.json"
CANDIDATE_BUNDLE = BUNDLE_DIR / "androidworld_candidate116_source_bundle.json"
EXTRA16_BUNDLE = BUNDLE_DIR / "androidworld_extra16_source_bundle.json"
PACKET_INDEX = INDEX_DIR / "androidworld_candidate116_packet_index.json"
SHARED_MANIFEST = SHARED_DIR / "androidworld_source_snapshot_manifest.json"
SHARED_TREE = SHARED_DIR / "source_tree"
SEMANTIC_INDEX = SEMANTIC_DIR / "androidworld_candidate116_semantic_index.json"
SEMANTIC_RAW_BUNDLE = SEMANTIC_DIR / "androidworld_candidate116_raw_semantic_extraction.json"
SLOT_LEDGER = LEDGER_DIR / "androidworld_candidate116_348_slot_ledger.json"
DRAFTER_CONFIG = CONFIG_DIR / "androidworld_candidate116_drafter_config.json"
PROMPT_SPEC = PROMPT_DIR / "androidworld_contract_drafter_prompt_v2.json"
PROMPT_INDEX = PROMPT_DIR / "androidworld_candidate116_rendered_prompt_index.json"
DRAFT_INPUT_FREEZE = FREEZE_DIR / "androidworld_candidate116_draft_input_freeze.json"
PRE_OPERATION_SNAPSHOT = VALIDATION_DIR / "pre_operation_readonly_snapshot.json"
POST_OPERATION_SNAPSHOT = VALIDATION_DIR / "post_operation_readonly_snapshot.json"
READONLY_GUARD_REPORT = VALIDATION_DIR / "readonly_pre_post_guard_report.json"
CONFLICT_LEDGER = SEMANTIC_DIR / "androidworld_candidate116_metadata_code_conflicts.json"
STRICT_ACCEPTANCE_REPORT = VALIDATION_DIR / "strict_acceptance_report.json"

BASELINE_AGENTS_CONFIG = REPO_ROOT / "configs/agents.yaml"

PROMPT_VERSION = "androidworld_contract_draft_prompt/v2"
CONTENT_TREE_HASH_ALGORITHM = "sha256-content-tree-v2:path-kind-size-content-or-link-target"
EXPECTED_GOAL_CATEGORY_COUNTS = {
    "format_template": 57,
    "computed_goal": 33,
    "branch_template": 1,
    "ir_proto_prompt": 25,
}

SAFE_CASE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
POST_RUN_TOKENS = (
    "native_score",
    "outcome_label",
    "evidence_label",
    "final_evidence_label",
    "scored_record",
    "unresolve_reason",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def semantic_object_sha256(payload: Any) -> str:
    """Mirror semantic_extractor's UTF-8 canonical JSON hash."""

    return sha256_bytes(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def run(command: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if check and completed.returncode != 0:
        fail(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def assert_safe_relative(value: str, label: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not value or value.startswith("./"):
        fail(f"unsafe {label}: {value!r}")


def immutable_root_guard() -> dict[str, dict[str, Any]]:
    lock = load_json(LOCK_SPEC)
    immutable_flag = getattr(stat, "UF_IMMUTABLE", None)
    if immutable_flag is None:
        fail("UF_IMMUTABLE is unavailable")
    counts: dict[str, dict[str, Any]] = {}
    for entry in lock["legacy_repository"]["filesystem_immutable_roots"]:
        root = REPO_ROOT / entry["path"]
        count = 0
        unlocked: list[str] = []
        for directory, dirnames, filenames in os.walk(root, followlinks=False):
            candidates = [Path(directory) / name for name in (*dirnames, *filenames)]
            if Path(directory) == root:
                candidates.insert(0, root)
            for candidate in candidates:
                count += 1
                if not candidate.stat(follow_symlinks=False).st_flags & immutable_flag:
                    unlocked.append(candidate.relative_to(REPO_ROOT).as_posix())
        expected = int(entry["recursive_entry_count"])
        counts[entry["path"]] = {
            "expected_at_step1_lock": expected,
            "observed_before_or_after_this_build": count,
            "delta_from_step1_lock": count - expected,
            "all_observed_entries_uf_immutable": not unlocked,
            "preexisting_unlocked_entry_count": len(unlocked),
            "preexisting_unlocked_entries": unlocked,
        }
    return counts


def _stream_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_tree_snapshot(root: Path) -> dict[str, Any]:
    """Hash every entry without mutating or following links.

    The digest binds relative path, entry kind, regular-file size/content, and
    symlink target.  Directory entries are included so empty directories are
    not silently ignored.
    """

    if not root.is_dir():
        fail(f"read-only snapshot root is missing: {root}")
    digest = hashlib.sha256()
    file_count = 0
    directory_count = 0
    symlink_count = 0
    other_count = 0
    total_file_bytes = 0
    immutable_flag = getattr(stat, "UF_IMMUTABLE", 0)
    unlocked: list[str] = []
    entries = sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())
    for path in entries:
        rel = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if immutable_flag and not metadata.st_flags & immutable_flag:
            unlocked.append(rel)
        if stat.S_ISLNK(metadata.st_mode):
            symlink_count += 1
            row: list[Any] = ["L", rel, os.readlink(path)]
        elif stat.S_ISDIR(metadata.st_mode):
            directory_count += 1
            row = ["D", rel]
        elif stat.S_ISREG(metadata.st_mode):
            file_count += 1
            total_file_bytes += metadata.st_size
            row = ["F", rel, metadata.st_size, _stream_sha256(path)]
        else:
            other_count += 1
            row = ["O", rel, metadata.st_mode]
        digest.update(json.dumps(row, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    root_metadata = root.lstat()
    if immutable_flag and not root_metadata.st_flags & immutable_flag:
        unlocked.insert(0, ".")
    return {
        "path": repo_relative(root),
        "hash_algorithm": CONTENT_TREE_HASH_ALGORITHM,
        "content_tree_sha256": digest.hexdigest(),
        "recursive_entry_count_excluding_root": len(entries),
        "recursive_entry_count_including_root": len(entries) + 1,
        "file_count": file_count,
        "directory_count": directory_count,
        "symlink_count": symlink_count,
        "other_entry_count": other_count,
        "total_file_bytes": total_file_bytes,
        "all_entries_uf_immutable": not unlocked,
        "unlocked_entry_count_including_root": len(unlocked),
        "unlocked_entries": unlocked,
    }


def readonly_operation_snapshot(*, phase: str) -> dict[str, Any]:
    lock = load_json(LOCK_SPEC)
    roots = [REPO_ROOT / entry["path"] for entry in lock["legacy_repository"]["filesystem_immutable_roots"]]
    submitted_androidworld = REPO_ROOT / "paper_result_packages/androidworld_both_agents_scored_cases_official_full100"
    if submitted_androidworld not in roots:
        roots.append(submitted_androidworld)
    return {
        "schema_version": "androidworld_candidate116_readonly_snapshot/v2",
        "phase": phase,
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "write_scope": repo_relative(WORK_ROOT),
        "policy": "legacy roots and official100 are read-only inputs; equality of full pre/post content-tree hashes is mandatory",
        "roots": {
            repo_relative(root): content_tree_snapshot(root)
            for root in roots
        },
        "official100": {
            "path": repo_relative(OFFICIAL100),
            "file_count": 1,
            "size_bytes": OFFICIAL100.stat().st_size,
            "sha256": sha256_file(OFFICIAL100),
        },
    }


def readonly_snapshot_core(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "write_scope": snapshot["write_scope"],
        "policy": snapshot["policy"],
        "roots": snapshot["roots"],
        "official100": snapshot["official100"],
    }


def clean_generated_outputs() -> None:
    """Remove only artifacts owned by this isolated candidate-116 workspace."""

    permitted_parent = REPO_ROOT / "rebuttal_work/runtime_outputs/submission_rebuttal"
    if WORK_ROOT.parent != permitted_parent or WORK_ROOT.name != "androidworld_candidate116":
        fail(f"refusing unsafe candidate workspace cleanup: {WORK_ROOT}")
    generated_roots = [
        MANIFEST_DIR,
        SELECTOR_DIR,
        PACKET_ROOT,
        BUNDLE_DIR,
        VALIDATION_DIR,
        INDEX_DIR,
        SHARED_DIR,
        SEMANTIC_DIR,
        CONFIG_DIR,
        PROMPT_DIR,
        FREEZE_DIR,
        LEDGER_DIR,
        DRAFT_OUTPUT_DIR,
        DRAFT_LOG_DIR,
    ]
    for root in generated_roots:
        if root.exists():
            if not root.is_relative_to(WORK_ROOT):
                fail(f"refusing cleanup outside candidate workspace: {root}")
            shutil.rmtree(root)
    readme = WORK_ROOT / "README.md"
    if readme.exists():
        readme.unlink()


def normalize_candidate_items(items: list[dict[str, Any]]) -> None:
    decorated: list[tuple[str, str, dict[str, Any]]] = []
    for item in items:
        case_id = str(item["case_unit_id"])
        task_id = str(item["task_id"])
        key = sha256_object(
            {"salt": SELECTION_SALT, "domain": "androidworld", "case_unit_id": case_id, "task_id": task_id}
        )
        item["selection_order_key"] = key
        decorated.append((key, case_id, item))
    decorated.sort(key=lambda row: (row[0], row[1]))
    for rank, (_, _, item) in enumerate(decorated):
        item["selection_rank"] = rank


def case_unit_records(items: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {"case_unit_id": str(item["case_unit_id"]), "task_id": str(item["task_id"])}
        for item in sorted(items, key=lambda row: str(row["case_unit_id"]))
    ]


def selection_order_records(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_unit_id": str(item["case_unit_id"]),
            "task_id": str(item["task_id"]),
            "selection_order_key": str(item["selection_order_key"]),
            "selection_rank": int(item["selection_rank"]),
        }
        for item in sorted(items, key=lambda row: int(row["selection_rank"]))
    ]


def module_from_androidworld_path(path: str) -> str:
    value = PurePosixPath(path)
    parts = list(value.parts)
    try:
        start = parts.index("android_world")
    except ValueError:
        fail(f"semantic source is not inside android_world: {path}")
    module_parts = parts[start:]
    if module_parts[-1] == "__init__.py":
        module_parts = module_parts[:-1]
    elif module_parts[-1].endswith(".py"):
        module_parts[-1] = module_parts[-1][:-3]
    else:
        fail(f"semantic Python module source is invalid: {path}")
    return ".".join(module_parts)


def semantic_artifact_binding(ref: Mapping[str, Any], *, fallback_symbol: str) -> dict[str, Any]:
    relative = str(ref.get("path") or "")
    assert_safe_relative(relative, "semantic source path")
    source = SHARED_TREE / relative
    if not source.is_file():
        fail(f"semantic source binding is missing: {relative}")
    declared = str(ref.get("file_sha256") or "")
    if declared != sha256_file(source):
        fail(f"semantic source binding hash mismatch: {relative}")
    module = str(ref.get("owner_module") or "")
    if not module and relative.endswith(".py"):
        module = module_from_androidworld_path(relative)
    if not module:
        module = "android_world.task_evals.information_retrieval.proto.tasks_textproto"
    return {
        "artifact_path": repo_relative(source),
        "sha256": declared,
        "owner_module": module,
        "owner_qualname": str(ref.get("symbol") or ref.get("owner_class") or fallback_symbol),
        "start_line": ref.get("start_line"),
        "end_line": ref.get("end_line"),
        "snippet_sha256": ref.get("snippet_sha256"),
        "ast_sha256": ref.get("ast_sha256"),
    }


def unique_semantic_bindings(
    refs: Iterable[Mapping[str, Any] | None], *, fallback_symbol: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        row = semantic_artifact_binding(ref, fallback_symbol=fallback_symbol)
        key = (row["artifact_path"], row["owner_module"], row["owner_qualname"])
        if key not in seen:
            seen.add(key)
            rows.append(row)
    return rows


def canonical_semantic_record(
    raw: Mapping[str, Any], *, selection_rank: int
) -> dict[str, Any]:
    task_id = str(raw["identity"]["task_id"])
    raw_goal = dict(raw["goal"])
    definition = dict(raw["definition"])
    parameters = dict(raw["parameters"])
    initialization = dict(raw["initialization"])
    evaluator = dict(raw["evaluator"])

    goal_refs: list[Mapping[str, Any] | None] = [
        raw_goal.get("effective_goal_ref"),
        raw_goal.get("effective_template_ref"),
    ]
    ir = raw_goal.get("ir_proto") if isinstance(raw_goal.get("ir_proto"), Mapping) else None
    if ir:
        goal_refs.extend(
            [
                ir.get("task_proto_source_ref"),
                ir.get("dynamic_property_ref"),
                ir.get("factory_ref"),
                ir.get("base_class_ref"),
            ]
        )
    goal_bindings = unique_semantic_bindings(goal_refs, fallback_symbol=f"{task_id}.goal")

    init_chain = list(initialization.get("mro_source_chain") or [])
    init_refs = [row.get("source_ref") for row in init_chain if isinstance(row, Mapping)]
    eval_chain = list(evaluator.get("mro_source_chain") or [])
    eval_refs = [row.get("source_ref") for row in eval_chain if isinstance(row, Mapping)]
    eval_refs.append((evaluator.get("runner_semantics") or {}).get("source_ref"))
    schema_refs = [parameters.get("source_ref"), parameters.get("generator_ref")]

    templates = list(raw_goal.get("templates") or [])
    branches: list[dict[str, Any]] = []
    if raw_goal.get("representation_kind") == "branch_template":
        for template in templates:
            branch_id = str(template["variant_id"])
            branches.append(
                {
                    "branch_id": branch_id,
                    "predicate": dict(template.get("when") or {"edit_type": branch_id}),
                    "template": str(template["template"]),
                    "semantics": "runtime-selected goal template; evaluator checks the corresponding edited note state",
                }
            )

    goal: dict[str, Any] = {
        "representation_kind": raw_goal["representation_kind"],
        "authority": raw_goal["authority"],
        "dispatch_phase": raw_goal["dispatch_phase"],
        "generation_semantics": {
            "templates": templates,
            "computed_goal_semantics": raw_goal.get("computed_goal_semantics"),
            "runtime_samples": raw_goal["runtime_samples"],
            "samples_are_examples_not_generic_templates": True,
        },
        "source_bindings": goal_bindings,
        "branches": branches,
    }
    if templates:
        goal["template"] = templates[0]["template"]
    if raw_goal.get("representation_kind") == "computed_goal":
        goal["computed_expression"] = raw_goal.get("computed_goal_semantics")
    if ir:
        task_definition = {
            "name": task_id,
            "prompt": ir["prompt"],
            "task_params": ir["task_params"],
            "success_criteria": ir["success_criteria"],
            "relevant_state": ir["relevant_state"],
        }
        proto_binding = semantic_artifact_binding(
            ir["task_proto_source_ref"], fallback_symbol=f'tasks[name="{task_id}"]'
        )
        goal["prompt"] = ir["prompt"]
        goal["proto_binding"] = {
            "task_name": task_id,
            "artifact_path": proto_binding["artifact_path"],
            "source_sha256": proto_binding["sha256"],
            "task_definition": task_definition,
            "task_definition_sha256": payload_sha256(task_definition),
            "selector": ir["task_proto_source_ref"].get("selector"),
            "task_proto_wire_sha256": ir["task_proto_sha256"],
        }

    comparison = copy.deepcopy(dict(raw["metadata_comparison"]))
    differing = comparison.get("status") in {"mismatch", "partial_variant_coverage"}
    comparison["has_difference"] = differing
    comparison["matches_runtime"] = not differing
    comparison["differences"] = (
        [
            {
                "difference_id": "task_template_vs_runtime_goal",
                "field": "task_template",
                "metadata_value": comparison["metadata_template"],
                "canonical_runtime_templates": comparison["canonical_templates"],
                "comparison_status": comparison["status"],
            }
        ]
        if differing
        else []
    )
    conflicts: list[dict[str, Any]] = []
    for conflict in raw.get("conflicts") or []:
        conflicts.append(
            {
                **dict(conflict),
                "difference_id": "task_template_vs_runtime_goal",
                "status": "resolved" if conflict.get("status") == "resolved" else "requires_contract_review",
                "resolution": conflict.get("resolution_rule")
                or "runtime goal and evaluator source take precedence over descriptive metadata",
            }
        )
    if differing and not conflicts:
        fail(f"semantic difference lacks conflict record: {task_id}")

    canonical_refs = list(definition.get("canonical_definition_refs") or [])
    definition_bindings = unique_semantic_bindings(canonical_refs, fallback_symbol=task_id)
    if not definition_bindings:
        fail(f"canonical task definition source is missing: {task_id}")
    primary_definition = definition_bindings[0]
    if definition.get("definition_kind") == "dynamic_ir_proto":
        primary_definition = next(
            (
                row
                for row in definition_bindings
                if row["artifact_path"].endswith("information_retrieval_registry.py")
            ),
            primary_definition,
        )
    canonical_module = primary_definition["owner_module"]
    canonical_source = primary_definition["artifact_path"]
    canonical_mro = []
    for mro_row in definition["mro"]:
        normalized_mro = dict(mro_row)
        if normalized_mro.get("module") == "abc":
            normalized_mro["runtime_reported_module"] = normalized_mro.pop("module")
        canonical_mro.append(normalized_mro)
    record = {
        "schema_version": "androidworld_case_semantics/v2",
        "case_unit_id": task_id,
        "task_id": task_id,
        "selection_rank": selection_rank,
        "group": "official100" if selection_rank < 100 else "extra16",
        "runtime_reported_module": definition.get("runtime_class_module"),
        "runtime_reported_class": definition.get("runtime_class_qualname"),
        "canonical_module": canonical_module,
        "canonical_source_file": canonical_source,
        "definition": {
            "definition_kind": definition["definition_kind"],
            "source_bindings": definition_bindings,
            "mro": canonical_mro,
            "runtime_reported_module": definition.get("runtime_class_module"),
            "incidental_runtime_module_excluded": definition.get("incidental_runtime_module_excluded"),
        },
        "raw_metadata": raw["raw_metadata"],
        "goal": goal,
        "schema": {
            "value": parameters["declared_schema"],
            "schema_completeness": parameters["schema_completeness"],
            "observed_parameter_keys": parameters["observed_parameter_keys"],
            "observed_parameter_types": parameters["observed_parameter_types"],
            "runner_injected_parameters": parameters["runner_injected_parameters"],
            "source_bindings": unique_semantic_bindings(
                schema_refs, fallback_symbol=f"{task_id}.schema/generate_random_params"
            ),
        },
        "initialize_task": {
            "device_execution_performed_during_extraction": False,
            "method_chain": init_chain,
            "source_bindings": unique_semantic_bindings(
                init_refs, fallback_symbol=f"{task_id}.initialize_task"
            ),
        },
        "is_successful": {
            "live_evaluator_execution_performed": False,
            "method_chain": eval_chain,
            "source_bindings": unique_semantic_bindings(
                eval_refs, fallback_symbol=f"{task_id}.is_successful"
            ),
            "branches": branches,
        },
        "evaluator": {
            "runner_score_semantics": evaluator["runner_semantics"],
            "method_chain": eval_chain,
            "source_bindings": unique_semantic_bindings(
                eval_refs, fallback_symbol=f"{task_id}.native_evaluator"
            ),
            "branches": branches,
        },
        "metadata_comparison": comparison,
        "metadata_conflicts": conflicts,
        "readiness": raw["readiness"],
        "raw_semantic_record_sha256": raw["record_sha256"],
    }
    record["record_sha256"] = payload_sha256(record)
    return record


def build_semantic_index(
    raw_bundle: Mapping[str, Any], items: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    raw_by_id = {row["identity"]["task_id"]: row for row in raw_bundle["records"]}
    ordered = sorted(items, key=lambda row: int(row["selection_rank"]))
    if set(raw_by_id) != {row["task_id"] for row in ordered}:
        fail("semantic extraction task set differs from candidate116")
    records = [
        canonical_semantic_record(raw_by_id[row["task_id"]], selection_rank=rank)
        for rank, row in enumerate(ordered)
    ]
    counts: dict[str, int] = {}
    for record in records:
        kind = record["goal"]["representation_kind"]
        counts[kind] = counts.get(kind, 0) + 1
    counts = dict(sorted(counts.items()))
    if counts != EXPECTED_GOAL_CATEGORY_COUNTS:
        fail(f"semantic category counts mismatch: {counts}")
    payload = {
        "schema_version": "androidworld_candidate116_semantic_index/v2",
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "source_snapshot_manifest_path": repo_relative(SHARED_MANIFEST),
        "source_snapshot_manifest_sha256": sha256_file(SHARED_MANIFEST),
        "raw_extraction_path": repo_relative(SEMANTIC_RAW_BUNDLE),
        "raw_extraction_sha256": sha256_file(SEMANTIC_RAW_BUNDLE),
        "raw_extraction_bundle_sha256": raw_bundle["bundle_sha256"],
        "expected_category_counts": EXPECTED_GOAL_CATEGORY_COUNTS,
        "category_counts": counts,
        "case_count": len(records),
        "records": records,
    }
    payload["semantic_index_sha256"] = payload_sha256(payload)
    return payload, {record["task_id"]: record for record in records}


def live_candidate_pool(venv_python: Path) -> tuple[list[dict[str, Any]], Path]:
    helper = r'''
import inspect
import json
import sys
from pathlib import Path
from android_world.registry import TaskRegistry

package = Path(inspect.getfile(TaskRegistry)).resolve().parent
metadata = json.loads((package / "task_metadata.json").read_text(encoding="utf-8"))
metadata_by_name = {item["task_name"]: item for item in metadata}
registry = TaskRegistry().get_registry(TaskRegistry.ANDROID_WORLD_FAMILY)
rows = []
for task_name, task_cls in sorted(registry.items()):
    row = dict(metadata_by_name[task_name])
    row.update({
        "task_name": task_name,
        "task_id": task_name,
        "case_unit_id": task_name,
        "class_name": task_cls.__name__,
        "module": task_cls.__module__,
        "source_file": inspect.getfile(task_cls),
        "base_class_name": task_cls.__mro__[1].__name__ if len(task_cls.__mro__) > 1 else None,
        "base_module": task_cls.__mro__[1].__module__ if len(task_cls.__mro__) > 1 else None,
        "base_source_file": inspect.getfile(task_cls.__mro__[1]) if len(task_cls.__mro__) > 1 else None,
    })
    rows.append(row)
print(json.dumps({"base_prefix": sys.base_prefix, "package": str(package), "items": rows}, sort_keys=True))
'''
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [str(venv_python), "-c", helper],
        cwd=Path(tempfile.gettempdir()),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        fail(f"live registry helper failed:\n{completed.stdout}\n{completed.stderr}")
    payload = json.loads(completed.stdout)
    package = Path(payload["package"]).resolve()
    base_prefix = Path(payload["base_prefix"]).resolve()

    def portable(path_text: str | None) -> str | None:
        if not path_text:
            return None
        path = Path(path_text).resolve()
        try:
            rel = path.relative_to(package)
            return f"<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/{rel.as_posix()}"
        except ValueError:
            pass
        runtime_root = base_prefix.parent
        try:
            rel = path.relative_to(runtime_root)
            return f"<PYTHON_RUNTIME>/{rel.as_posix()}"
        except ValueError:
            fail(f"cannot normalize live candidate source path: {path}")
    rows = [dict(row) for row in payload["items"]]
    for row in rows:
        row["source_file"] = portable(row.get("source_file"))
        row["base_source_file"] = portable(row.get("base_source_file"))
    normalize_candidate_items(rows)
    return rows, base_prefix.parent


class SourceResolver:
    def __init__(self, *, clean_root: Path, installed_root: Path, python_runtime_root: Path):
        self.clean_root = clean_root.resolve()
        self.package_root = self.clean_root / "android_world"
        self.installed_root = installed_root.resolve()
        self.site_package = self.installed_root / ".venv311/lib/python3.11/site-packages/android_world"
        self.python_runtime_root = python_runtime_root.resolve()
        self.git_blob_cache: dict[Path, str | None] = {}

    def resolve(self, portable: str) -> Path:
        install_prefix = "<ANDROIDWORLD_INSTALL_ROOT>/"
        runtime_prefix = "<PYTHON_RUNTIME>/"
        if portable.startswith(install_prefix):
            rel = portable[len(install_prefix) :]
            if rel.startswith("android_world/"):
                path = self.clean_root / rel
            elif rel.startswith(".venv311/lib/python3.11/site-packages/android_world/"):
                package_rel = rel.split("site-packages/android_world/", 1)[1]
                clean = self.package_root / package_rel
                path = clean if clean.is_file() else self.site_package / package_rel
            else:
                fail(f"unsupported AndroidWorld portable source: {portable}")
        elif portable.startswith(runtime_prefix):
            path = self.python_runtime_root / portable[len(runtime_prefix) :]
        else:
            fail(f"unresolved source token: {portable}")
        path = path.resolve()
        if not path.is_file():
            fail(f"resolved source is missing: {portable} -> {path}")
        return path

    def portable_for_clean(self, path: Path) -> str:
        rel = path.resolve().relative_to(self.clean_root)
        return f"<ANDROIDWORLD_INSTALL_ROOT>/{rel.as_posix()}"

    def archive_for_clean(self, path: Path) -> str:
        rel = path.resolve().relative_to(self.clean_root)
        return f"official/install/{rel.as_posix()}"

    def git_blob(self, path: Path) -> str | None:
        path = path.resolve()
        if path in self.git_blob_cache:
            return self.git_blob_cache[path]
        try:
            rel = path.relative_to(self.clean_root).as_posix()
        except ValueError:
            value = None
        else:
            completed = run(["git", "rev-parse", f"HEAD:{rel}"], cwd=self.clean_root, check=False)
            value = completed.stdout.strip() if completed.returncode == 0 else None
        self.git_blob_cache[path] = value
        return value


def core_descriptors(item: Mapping[str, Any], resolver: SourceResolver) -> list[dict[str, str]]:
    portable_paths = [
        "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_metadata.json",
        "<ANDROIDWORLD_INSTALL_ROOT>/android_world/registry.py",
        "<ANDROIDWORLD_INSTALL_ROOT>/android_world/task_evals/task_eval.py",
        str(item.get("source_file") or ""),
        str(item.get("base_source_file") or ""),
        *[str(value) for value in item.get("semantic_authority_files") or []],
    ]
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for portable in portable_paths:
        if not portable or portable in seen:
            continue
        seen.add(portable)
        source = resolver.resolve(portable)
        if portable.startswith("<ANDROIDWORLD_INSTALL_ROOT>/"):
            archive = "official/install/" + portable.split("<ANDROIDWORLD_INSTALL_ROOT>/", 1)[1]
        else:
            archive = f"official/files/{source.name}"
        result.append({"source_path": portable, "archive_path": archive, "sha256": sha256_file(source)})
    return result


def selected_item(candidate: Mapping[str, Any], resolver: SourceResolver) -> dict[str, Any]:
    item = copy.deepcopy(dict(candidate))
    item["source_ref"] = f"androidworld://{item['task_id']}"
    item["official_files"] = core_descriptors(item, resolver)
    item["packet_files"] = [row["archive_path"] for row in item["official_files"]] + [
        "derived/selected_task_source.json"
    ]
    item["source_sha256"] = sha256_object(
        {"task_name": item["task_id"], "source_files": [row["sha256"] for row in item["official_files"]]}
    )
    return item


def portable_from_semantic_artifact(path: str) -> str:
    source = (REPO_ROOT / path).resolve()
    try:
        relative = source.relative_to(SHARED_TREE.resolve())
    except ValueError as exc:
        fail(f"semantic artifact is outside the shared source tree: {path}")
    if not relative.as_posix().startswith("android_world/"):
        fail(f"semantic artifact is not an AndroidWorld source: {path}")
    return f"<ANDROIDWORLD_INSTALL_ROOT>/{relative.as_posix()}"


def corrected_selected_items(
    frozen_items: list[dict[str, Any]],
    semantic_by_id: Mapping[str, Mapping[str, Any]],
    resolver: SourceResolver,
) -> list[dict[str, Any]]:
    corrected: list[dict[str, Any]] = []
    for frozen in sorted(frozen_items, key=lambda row: int(row["selection_rank"])):
        task_id = str(frozen["task_id"])
        semantic = semantic_by_id[task_id]
        row = copy.deepcopy(frozen)
        row["metadata_task_template"] = row["task_template"]
        row["metadata_semantic_role"] = "descriptive_non_authoritative_when_conflicting"
        row["runtime_reported_module"] = row.pop("module", None)
        row["runtime_reported_source_file"] = row.pop("source_file", None)
        row["module"] = semantic["canonical_module"]
        row["source_file"] = portable_from_semantic_artifact(semantic["canonical_source_file"])
        row["semantic_record_path"] = repo_relative(
            SEMANTIC_DIR / "cases" / task_id / "canonical_task_semantics.json"
        )
        row["semantic_record_sha256"] = semantic["record_sha256"]
        row["canonical_goal_representation_kind"] = semantic["goal"]["representation_kind"]
        row["canonical_goal_authority"] = "runtime task goal plus evaluator code; metadata conflicts are recorded, never silently preferred"
        row["metadata_code_conflict_count"] = len(semantic["metadata_conflicts"])
        authority_paths: list[str] = []
        for block_name in ("definition", "goal", "schema", "initialize_task", "is_successful", "evaluator"):
            block = semantic[block_name]
            for binding in block.get("source_bindings") or []:
                portable = portable_from_semantic_artifact(binding["artifact_path"])
                if portable not in authority_paths:
                    authority_paths.append(portable)
        row["semantic_authority_files"] = authority_paths

        # IR runtime classes are dynamically manufactured by ABCMeta.  `abc`
        # is retained only as a diagnostic observation, never as definition
        # provenance or as a copied source descriptor.
        if semantic["definition"]["definition_kind"] == "dynamic_ir_proto":
            row["provenance_correction"] = {
                "status": "corrected",
                "runtime_reported_module": row["runtime_reported_module"],
                "runtime_reported_source_file": row["runtime_reported_source_file"],
                "canonical_definition_module": row["module"],
                "canonical_definition_source_file": row["source_file"],
                "reason": "dynamic type creation reports incidental ABCMeta provenance; registry factory, task proto, and InformationRetrieval base are authoritative",
            }
        corrected.append(selected_item(row, resolver))
    if [row["selection_rank"] for row in corrected] != list(range(116)):
        fail("corrected candidate items are not ordered ranks 0..115")
    return corrected


def module_paths(module: str, resolver: SourceResolver) -> list[Path]:
    if not module.startswith("android_world"):
        return []
    rel = Path(*module.split("."))
    candidates = [resolver.clean_root / rel.with_suffix(".py"), resolver.clean_root / rel / "__init__.py"]
    clean_matches = [path.resolve() for path in candidates if path.is_file()]
    if clean_matches:
        return clean_matches
    generated = resolver.installed_root / ".venv311/lib/python3.11/site-packages" / rel.with_suffix(".py")
    return [generated.resolve()] if generated.is_file() else []


def module_for_path(path: Path, resolver: SourceResolver) -> str | None:
    for root in (resolver.clean_root, resolver.installed_root / ".venv311/lib/python3.11/site-packages"):
        try:
            rel = path.resolve().relative_to(root)
        except ValueError:
            continue
        if rel.name == "__init__.py":
            rel = rel.parent
        else:
            rel = rel.with_suffix("")
        return ".".join(rel.parts)
    return None


def imports_for(path: Path, resolver: SourceResolver) -> tuple[set[str], set[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        fail(f"cannot parse Python source {path}: {exc}")
    current = module_for_path(path, resolver)
    modules: set[str] = set()
    external: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level and current:
                package = current.rsplit(".", 1)[0] if path.name != "__init__.py" else current
                try:
                    base = importlib.util.resolve_name("." * node.level + base, package)
                except (ImportError, ValueError):
                    base = ""
            if base:
                names.append(base)
                names.extend(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
        for name in names:
            if name.startswith("android_world"):
                modules.add(name)
            elif name:
                external.add(name.split(".", 1)[0])
    return modules, external


def source_closure(item: Mapping[str, Any], resolver: SourceResolver) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    core = [dict(row) for row in item["official_files"]]
    by_archive: dict[str, dict[str, Any]] = {}
    covered_actual: set[Path] = set()
    for row in core:
        actual = resolver.resolve(row["source_path"])
        if sha256_file(actual) != row["sha256"]:
            fail(f"core descriptor hash mismatch for {item['task_id']}: {row['source_path']}")
        archive = str(row["archive_path"])
        if archive in by_archive:
            fail(f"duplicate core archive path for {item['task_id']}: {archive}")
        by_archive[archive] = {
            **row,
            "source_kind": "frozen_core_descriptor",
            "git_blob_oid": resolver.git_blob(actual),
        }
        covered_actual.add(actual)

    seeds: set[Path] = set()
    for key in ("source_file", "base_source_file"):
        value = str(item.get(key) or "")
        if value:
            path = resolver.resolve(value)
            if path.is_relative_to(resolver.clean_root) or path.is_relative_to(
                resolver.installed_root / ".venv311/lib/python3.11/site-packages"
            ):
                seeds.add(path)
    seeds.add(resolver.package_root / "task_evals/task_eval.py")
    proto_root = resolver.package_root / "task_evals/information_retrieval/proto"
    # Generated pb2 modules enter the common TaskEval dependency graph through
    # setup_device/apps.py. Retain their defining protos for every case.
    seeds.add((proto_root / "state.proto").resolve())
    seeds.add((proto_root / "task.proto").resolve())

    is_ir = str(item.get("base_module") or "").startswith("android_world.task_evals.information_retrieval") or str(
        item.get("module") or ""
    ).startswith("android_world.task_evals.information_retrieval") or str(item.get("module")) == "abc"
    if is_ir:
        ir_root = resolver.package_root / "task_evals/information_retrieval"
        for path in ir_root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.name.endswith("_test.py"):
                continue
            if path.suffix in {".py", ".proto", ".textproto"}:
                seeds.add(path.resolve())
        for name in ("state_pb2.py", "task_pb2.py"):
            generated = resolver.site_package / "task_evals/information_retrieval/proto" / name
            if not generated.is_file():
                fail(f"required generated protobuf source is missing: {generated}")
            seeds.add(generated.resolve())
        seeds.add((ir_root / "information_retrieval_registry.py").resolve())

    queue = deque(sorted(seeds, key=str))
    scanned: set[Path] = set()
    import_edges: list[dict[str, str]] = []
    external: set[str] = set()
    unresolved: list[dict[str, str]] = []
    while queue:
        path = queue.popleft().resolve()
        if path in scanned:
            continue
        scanned.add(path)
        if path.suffix != ".py":
            continue
        modules, ext = imports_for(path, resolver)
        external.update(ext)
        for module in sorted(modules):
            resolved = module_paths(module, resolver)
            if not resolved:
                # A from-import can name a class/function. Its parent module is
                # included separately; only fail if no importable prefix exists.
                prefixes = [".".join(module.split(".")[:i]) for i in range(len(module.split(".")), 1, -1)]
                if not any(module_paths(prefix, resolver) for prefix in prefixes):
                    unresolved.append({"importer": resolver.portable_for_clean(path) if path.is_relative_to(resolver.clean_root) else str(path.name), "module": module})
                continue
            for target in resolved:
                import_edges.append({"importer": module_for_path(path, resolver) or path.name, "module": module})
                if target not in scanned:
                    queue.append(target)

    if unresolved:
        fail(f"unresolved internal imports for {item['task_id']}: {unresolved[:5]}")

    for actual in sorted(scanned | seeds, key=str):
        if actual in covered_actual:
            continue
        if actual.is_relative_to(resolver.clean_root):
            portable = resolver.portable_for_clean(actual)
            archive = resolver.archive_for_clean(actual)
            kind = "git_source_dependency"
        elif actual.is_relative_to(resolver.site_package):
            rel = actual.relative_to(resolver.site_package)
            portable = f"<ANDROIDWORLD_INSTALL_ROOT>/.venv311/lib/python3.11/site-packages/android_world/{rel.as_posix()}"
            archive = f"official/install/.venv311/lib/python3.11/site-packages/android_world/{rel.as_posix()}"
            kind = "generated_build_dependency"
        else:
            # Python stdlib files are already represented by core descriptors;
            # no new non-AndroidWorld external source is added to the closure.
            continue
        if archive in by_archive:
            fail(f"duplicate dependency archive path for {item['task_id']}: {archive}")
        by_archive[archive] = {
            "source_path": portable,
            "archive_path": archive,
            "sha256": sha256_file(actual),
            "source_kind": kind,
            "git_blob_oid": resolver.git_blob(actual),
        }
        covered_actual.add(actual)

    core_archives = [row["archive_path"] for row in core]
    descriptors = sorted(
        by_archive.values(),
        key=lambda row: (0, core_archives.index(row["archive_path"]))
        if row["archive_path"] in core_archives
        else (1, row["archive_path"]),
    )
    archives = [row["archive_path"] for row in descriptors]
    if len(archives) != len(set(archives)):
        fail(f"duplicate closure archive path for {item['task_id']}")
    closure_payload = {
        "schema_version": "androidworld_case_source_closure/v1",
        "task_id": item["task_id"],
        "case_unit_id": item["case_unit_id"],
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "algorithm": "recursive Python AST closure from task/base/task_eval plus explicit dynamic-IR resources; registry retained but not expanded",
        "core_descriptor_count": len(core),
        "closure_file_count": len(descriptors),
        "internal_import_edge_count": len(import_edges),
        "unresolved_internal_imports": [],
        "external_python_packages_not_embedded": sorted(external - {"android_world"}),
        "shared_source_snapshot_manifest_path": repo_relative(SHARED_MANIFEST),
        "shared_source_snapshot_manifest_sha256": sha256_file(SHARED_MANIFEST),
        "files": descriptors,
    }
    closure_payload["closure_sha256"] = sha256_object({"files": descriptors, "source_commit": EXPECTED_SOURCE_COMMIT})
    return descriptors, closure_payload


def raw_manifest(
    *, task_id: str, raw_dir: Path, file_sources: Mapping[str, str], official: list[str], derived: list[str], packet: list[str]
) -> dict[str, Any]:
    files = sorted(path for path in raw_dir.rglob("*") if path.is_file())
    copied = [path.relative_to(raw_dir).as_posix() for path in files]
    return {
        "domain": "androidworld",
        "case_unit_id": task_id,
        "task_id": task_id,
        "source_refs": sorted(set(file_sources.values())),
        "copied_files": copied,
        "official_files": sorted(official),
        "derived_files": sorted(derived),
        "packet_files": packet,
        "sha256_per_file": {path.relative_to(raw_dir).as_posix(): sha256_file(path) for path in files},
        "file_sources": dict(sorted(file_sources.items())),
    }


def compact_goal_semantics(goal: Mapping[str, Any]) -> dict[str, Any]:
    generation = dict(goal["generation_semantics"])
    compact_samples = []
    for sample in generation.get("runtime_samples") or []:
        params = sample.get("params_at_dispatch_model") or {}
        compact_samples.append(
            {
                "sample_kind": sample.get("sample_kind"),
                "suite_seed": sample.get("suite_seed"),
                "dispatch_goal_model": sample.get("dispatch_goal_model"),
                "dispatch_goal_sha256": sample.get("dispatch_goal_sha256"),
                "parameter_keys": sorted(params),
                "branch_selector": sample.get("branch_selector"),
                "pure_pre_dispatch_transforms": sample.get("pure_pre_dispatch_transforms") or [],
                "device_initialization_executed": False,
            }
        )
    generation["runtime_samples"] = compact_samples
    compact = {
        **dict(goal),
        "generation_semantics": generation,
    }
    return compact


def semantic_source_context(item: Mapping[str, Any], semantic: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_text": {
            "benchmark": "AndroidWorld",
            "task_name": item["task_name"],
            "metadata_task_template": item["metadata_task_template"],
            "metadata_semantic_role": item["metadata_semantic_role"],
            "canonical_goal": compact_goal_semantics(semantic["goal"]),
            "difficulty": item.get("difficulty"),
            "tags": item.get("tags") or [],
            "optimal_steps": item.get("optimal_steps"),
        },
        "official_policy": (
            "AndroidWorld has no separate policy document. The frozen task class, parameter generator/schema, "
            "initialize_task implementation, runtime-dispatched goal, is_successful implementation, and suite runner "
            "are authoritative. task_metadata.json is descriptive and is not allowed to override conflicting runtime semantics."
        ),
        "parameter_schema": semantic["schema"],
        "initialization": semantic["initialize_task"],
        "evaluator_description": {
            "task_class": item["class_name"],
            "canonical_module": item["module"],
            "definition": semantic["definition"],
            "is_successful": semantic["is_successful"],
            "evaluator": semantic["evaluator"],
        },
        "metadata_comparison": semantic["metadata_comparison"],
        "metadata_conflicts": semantic["metadata_conflicts"],
        "trace_schema": {
            "episodes_per_record": 1,
            "artifacts": [
                "device state",
                "system state",
                "checkpoint artifacts",
                "observations",
                "actions",
                "messages",
                "evaluator input",
                "evaluator output",
            ],
        },
        "available_post_run_artifact_types": [
            "post_state",
            "trace",
            "screenshot",
            "tool_log",
            "message",
            "native_evaluator_input",
            "native_evaluator_output",
            "file",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [
            {
                "source_ref": binding["artifact_path"],
                "source_sha256": binding["sha256"],
                "owner_module": binding["owner_module"],
                "owner_qualname": binding["owner_qualname"],
            }
            for block_name in ("definition", "goal", "schema", "initialize_task", "is_successful", "evaluator")
            for binding in semantic[block_name].get("source_bindings") or []
        ],
        "semantic_record": {
            "path": item["semantic_record_path"],
            "sha256": semantic["record_sha256"],
        },
    }


def render_compact_case_packet(
    *, item: Mapping[str, Any], semantic: Mapping[str, Any], closure: Mapping[str, Any]
) -> tuple[str, dict[str, Any]]:
    context = semantic_source_context(item, semantic)
    payload = {
        "schema_version": "androidworld_compact_draft_packet/v2",
        "identity": {
            "domain": "androidworld",
            "case_unit_id": item["case_unit_id"],
            "task_id": item["task_id"],
            "selection_rank": item["selection_rank"],
            "group": "official100" if int(item["selection_rank"]) < 100 else "extra16",
        },
        "authority_rule": (
            "Use canonical runtime goal/evaluator semantics. Treat task_metadata.json wording as descriptive only; "
            "every disagreement is retained in metadata_comparison and metadata_conflicts."
        ),
        "source_context": context,
        "integrity": {
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "shared_source_snapshot_manifest_path": repo_relative(SHARED_MANIFEST),
            "shared_source_snapshot_manifest_sha256": sha256_file(SHARED_MANIFEST),
            "source_closure_sha256": closure["closure_sha256"],
            "semantic_record_sha256": semantic["record_sha256"],
        },
    }
    body = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
    text = (
        "# AndroidWorld Compact Draft Packet\n\n"
        "This is the complete LLM-visible pre-run source packet for one contract draft. "
        "The full audit packet and frozen source closure remain available separately.\n\n"
        "```json\n"
        + body
        + "\n```\n"
    )
    if len(text.encode("utf-8")) > 180_000:
        fail(f"compact packet exceeds 180000 bytes: {item['task_id']}")
    return text, context


def build_packet_tree(
    *,
    output_root: Path,
    items: list[dict[str, Any]],
    resolver: SourceResolver,
    semantic_by_id: Mapping[str, Mapping[str, Any]],
    collect_index: bool,
) -> list[dict[str, Any]]:
    if output_root.exists() and any(output_root.iterdir()):
        fail(f"refusing to overwrite non-empty packet root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda row: int(row["selection_rank"])):
        task_id = str(item["task_id"])
        semantic = semantic_by_id[task_id]
        if not SAFE_CASE_ID.fullmatch(task_id):
            fail(f"unsafe task id: {task_id}")
        case_dir = output_root / "androidworld" / task_id
        raw_dir = case_dir / "raw_case"
        raw_dir.mkdir(parents=True, exist_ok=False)
        descriptors, closure = source_closure(item, resolver)
        file_sources: dict[str, str] = {}
        official: list[str] = []
        for descriptor in descriptors:
            portable = str(descriptor["source_path"])
            archive = str(descriptor["archive_path"])
            assert_safe_relative(archive, "archive path")
            source = resolver.resolve(portable)
            expected = str(descriptor["sha256"])
            actual = sha256_file(source)
            if actual != expected:
                fail(f"source drift before copy for {task_id}: {portable}: {expected} != {actual}")
            target = raw_dir / archive
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha256_file(target) != expected:
                fail(f"copy hash mismatch for {task_id}: {archive}")
            file_sources[archive] = portable
            official.append(archive)

        selected_path = raw_dir / "derived/selected_task_source.json"
        write_json(selected_path, item)
        closure_path = raw_dir / "derived/source_closure.json"
        write_json(closure_path, closure)
        semantics_path = raw_dir / "derived/canonical_task_semantics.json"
        write_json(semantics_path, semantic)
        selected_rel = selected_path.relative_to(raw_dir).as_posix()
        closure_rel = closure_path.relative_to(raw_dir).as_posix()
        semantics_rel = semantics_path.relative_to(raw_dir).as_posix()
        file_sources[selected_rel] = str(item["source_ref"])
        file_sources[closure_rel] = f"androidworld-source-closure://{task_id}@{EXPECTED_SOURCE_COMMIT}"
        file_sources[semantics_rel] = f"androidworld-canonical-semantics://{task_id}@{semantic['record_sha256']}"
        derived = [selected_rel, closure_rel, semantics_rel]
        packet_files = official + derived
        manifest = raw_manifest(
            task_id=task_id,
            raw_dir=raw_dir,
            file_sources=file_sources,
            official=official,
            derived=derived,
            packet=packet_files,
        )
        manifest_path = case_dir / "raw_case_manifest.json"
        write_json(manifest_path, manifest)
        packet_path = case_dir / "case_packet.md"
        packet_path.write_text(
            render_case_packet(
                domain="androidworld",
                case_unit_id=task_id,
                task_id=task_id,
                raw_case_dir=raw_dir,
                raw_case_manifest=manifest,
            ),
            encoding="utf-8",
        )
        compact_text, source_context = render_compact_case_packet(
            item=item, semantic=semantic, closure=closure
        )
        compact_path = case_dir / "compact_case_packet.md"
        compact_path.write_text(compact_text, encoding="utf-8")
        if compact_path.stat().st_size >= packet_path.stat().st_size:
            fail(f"compact packet is not smaller than full audit packet: {task_id}")
        if collect_index:
            index.append(
                {
                    "selection_rank": int(item["selection_rank"]),
                    "group": "official100" if int(item["selection_rank"]) < 100 else "extra16",
                    "case_unit_id": task_id,
                    "task_id": task_id,
                    "closure_file_count": len(descriptors),
                    "case_packet_path": repo_relative(packet_path),
                    "case_packet_sha256": sha256_file(packet_path),
                    "compact_case_packet_path": repo_relative(compact_path),
                    "compact_case_packet_sha256": sha256_file(compact_path),
                    "compact_case_packet_size_bytes": compact_path.stat().st_size,
                    "raw_case_manifest_path": repo_relative(manifest_path),
                    "raw_case_manifest_sha256": sha256_file(manifest_path),
                    "source_closure_sha256": closure["closure_sha256"],
                    "semantic_record_path": item["semantic_record_path"],
                    "semantic_record_sha256": semantic["record_sha256"],
                    "semantic_source_context_sha256": payload_sha256(source_context),
                }
            )
    return index


def experiment_manifest(
    *,
    items: list[dict[str, Any]],
    manifest_id: str,
    source_bundle_hash: str,
    source_bundle_path: Path,
    agents_config_hash: str,
    llm_roles: Mapping[str, Any],
    planned_record_slot_ids_hash: str,
    draft_input_freeze_id: str,
) -> dict[str, Any]:
    template = load_json(FULL100_MANIFEST)
    agents = copy.deepcopy(template["agents"])
    ordered = sorted(items, key=lambda row: int(row["selection_rank"]))
    record_slot_count = len(ordered) * len(agents)
    combined_order = [
        {
            "domain": "androidworld",
            "case_unit_id": item["case_unit_id"],
            "task_id": item["task_id"],
            "selection_order_key": item["selection_order_key"],
            "selection_rank": item["selection_rank"],
        }
        for item in ordered
    ]
    return {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": manifest_id,
        "manifest_version": "0.1.0-prelock",
        "created_at": BUILD_TIMESTAMP,
        "status": "draft",
        "paper_mapping_path": template["paper_mapping_path"],
        "paper_mapping_sha256": template["paper_mapping_sha256"],
        "source_bundle_hash": source_bundle_hash,
        "agents_config_hash": agents_config_hash,
        "infra_config_hash": template["infra_config_hash"],
        "deterministic_selection": {
            "hash_function": "sha256",
            "hash_salt_hash": sha256_object(SELECTION_SALT),
            "eligible_case_unit_set_hash": sha256_object({"androidworld": case_unit_records(ordered)}),
            "excluded_smoke_case_units": [],
            "smoke_exclusion_hash": sha256_object([]),
            "case_selection_order_hash": sha256_object(combined_order),
            "bootstrap_seed": int(template["deterministic_selection"]["bootstrap_seed"]),
            "bootstrap_resample_count": int(template["deterministic_selection"]["bootstrap_resample_count"]),
            "audit_sample_seed": int(template["deterministic_selection"]["audit_sample_seed"]),
            "rerun_subset_selection_rule": "predeclared hash order over locked AndroidWorld candidate pool",
        },
        "domains": [
            {
                "domain": "androidworld",
                "domain_display_name": "AndroidWorld",
                "experiment_type": "appendix",
                "priority": "P2",
                "case_unit_count": len(ordered),
                "record_slot_count": record_slot_count,
                "planned_record_slot_ids_hash": planned_record_slot_ids_hash,
                "official_split_eligible_case_units": 116,
                "official_split_hash": EXPECTED_CANDIDATE_SHA256,
                "official_split_exception_id": None,
                "contract_lock_status": "draft_required",
                "claim_scope": "native_aligned",
                "stronger_measurement_mapping": None,
                "case_units": [
                    {
                        "case_unit_id": item["case_unit_id"],
                        "task_id": item["task_id"],
                        "contract_lock_status": "draft_required",
                    }
                    for item in ordered
                ],
            }
        ],
        "agents": agents,
        "official_split_exceptions": [],
        "declared_appendix_diagnostics": copy.deepcopy(template["declared_appendix_diagnostics"]),
        "required_paper_labels": copy.deepcopy(template["required_paper_labels"]),
        "contract_locks": [],
        "contract_locks_hash": EMPTY_LIST_HASH,
    }


def validate_manifest_schema(path: Path) -> None:
    report = validate_object("experiment_manifest", load_json(path), formal=False, raise_on_error=False)
    if report.issues:
        fail(f"manifest schema validation failed for {path}: {[issue.message for issue in report.issues[:10]]}")


def build_prompt_policy_spec() -> dict[str, Any]:
    implementation_source = inspect.getsource(build_drafter_prompt)
    payload = {
        "schema_version": "androidworld_drafter_prompt_policy/v2",
        "prompt_version": PROMPT_VERSION,
        "repository_base_prompt_version": DEFAULT_PROMPT_VERSION,
        "implementation": {
            "module": build_drafter_prompt.__module__,
            "qualname": build_drafter_prompt.__qualname__,
            "source_file": repo_relative(Path(inspect.getsourcefile(build_drafter_prompt) or "")),
            "source_sha256": sha256_file(Path(inspect.getsourcefile(build_drafter_prompt) or "")),
            "function_source_sha256": sha256_bytes(implementation_source.encode("utf-8")),
        },
        "androidworld_packet_profile": {
            "schema_version": "androidworld_compact_draft_packet/v2",
            "authority": "runtime goal/evaluator sources override conflicting descriptive metadata",
            "forbidden_post_run_inputs": list(POST_RUN_TOKENS),
            "maximum_compact_packet_bytes": 180_000,
            "full_audit_packet_is_not_llm_visible": True,
        },
        "hash_definition": "sha256 of canonical JSON of this object excluding prompt_hash",
    }
    payload["prompt_hash"] = payload_sha256(payload)
    return payload


def write_drafter_configuration() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prompt_spec = build_prompt_policy_spec()
    write_json(PROMPT_SPEC, prompt_spec)
    config = build_contract_drafter_config(
        load_json(BASELINE_AGENTS_CONFIG),
        prompt_version=PROMPT_VERSION,
        prompt_hash=prompt_spec["prompt_hash"],
    )
    write_json(DRAFTER_CONFIG, config)
    role = project_contract_drafter_llm_role(config)
    return prompt_spec, config, {"contract_drafter": role}


def build_slot_ledger(items: list[dict[str, Any]]) -> dict[str, Any]:
    ordered_cases = [
        {
            "selection_rank": int(item["selection_rank"]),
            "case_unit_id": item["case_unit_id"],
            "task_id": item["task_id"],
        }
        for item in sorted(items, key=lambda row: int(row["selection_rank"]))
    ]
    ledger = build_candidate116_slot_ledger(ordered_cases)
    # Human/auditor-friendly aliases. The native rows/subsets remain the
    # canonical fields used by freeze_and_slots validation.
    ledger["slots"] = copy.deepcopy(ledger["rows"])
    ledger["slot_sets"] = {
        "candidate116": {
            "count": 348,
            "slot_ids": ledger["record_slot_ids"],
            "slot_ids_hash": ledger["record_slot_ids_hash"],
        },
        "official100": {
            "count": 300,
            "slot_ids": ledger["subsets"]["official100"]["record_slot_ids"],
            "slot_ids_hash": ledger["subsets"]["official100"]["record_slot_ids_hash"],
        },
        "extra16": {
            "count": 48,
            "slot_ids": ledger["subsets"]["extra16"]["record_slot_ids"],
            "slot_ids_hash": ledger["subsets"]["extra16"]["record_slot_ids_hash"],
        },
    }
    ledger.pop("ledger_sha256", None)
    ledger["ledger_sha256"] = payload_sha256(ledger)
    issues = validate_candidate116_slot_ledger(ledger)
    if issues:
        fail(f"slot ledger validation failed: {issues}")
    assert_known_slot_hashes(ledger)
    write_json(SLOT_LEDGER, ledger)
    return ledger


def finalize_compact_source_bundle(
    *,
    path: Path,
    packet_index: list[dict[str, Any]],
    semantic_by_id: Mapping[str, Mapping[str, Any]],
    prompt_version: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    bundle = load_json(path)
    index_by_id = {row["task_id"]: row for row in packet_index}
    prompts: dict[str, str] = {}
    for source in bundle["sources"]:
        task_id = str(source["task_id"])
        packet = index_by_id[task_id]
        semantic = semantic_by_id[task_id]
        source["audit_input"] = {
            "full_case_packet_path": packet["case_packet_path"],
            "full_case_packet_sha256": packet["case_packet_sha256"],
            "source_closure_sha256": packet["source_closure_sha256"],
            "semantic_record_path": packet["semantic_record_path"],
            "semantic_record_sha256": packet["semantic_record_sha256"],
        }
        source["draft_input"]["case_packet_path"] = packet["compact_case_packet_path"]
        source["draft_input"]["case_packet_sha256"] = packet["compact_case_packet_sha256"]
        source["draft_input"]["view_kind"] = "compact"
        source["source_context"] = semantic_source_context(
            load_json(
                PACKET_ROOT
                / "androidworld"
                / task_id
                / "raw_case/derived/selected_task_source.json"
            ),
            semantic,
        )
        prompt = build_drafter_prompt(source, prompt_version=prompt_version)
        prompt_hash = payload_sha256({"prompt": prompt})
        source["draft_input"]["prompt_version"] = prompt_version
        source["draft_input"]["prompt_sha256"] = prompt_hash
        prompts[task_id] = prompt
    write_json(path, bundle)
    reloaded = load_source_bundle(path)
    if reloaded != bundle:
        fail(f"source bundle does not round-trip through drafter loader: {path}")
    return bundle, prompts


def write_prompt_index(
    *, prompts: Mapping[str, str], items: list[dict[str, Any]], prompt_spec: Mapping[str, Any]
) -> dict[str, Any]:
    rows = []
    for item in sorted(items, key=lambda row: int(row["selection_rank"])):
        task_id = item["task_id"]
        prompt = prompts[task_id]
        rows.append(
            {
                "selection_rank": int(item["selection_rank"]),
                "case_unit_id": item["case_unit_id"],
                "task_id": task_id,
                "prompt_version": PROMPT_VERSION,
                "rendered_prompt_size_bytes": len(prompt.encode("utf-8")),
                "rendered_prompt_sha256": payload_sha256({"prompt": prompt}),
            }
        )
    hashes = [row["rendered_prompt_sha256"] for row in rows]
    if len(rows) != 116 or len(set(hashes)) != 116:
        fail("rendered drafter prompts must be exactly 116 unique inputs")
    payload = {
        "schema_version": "androidworld_rendered_prompt_index/v2",
        "prompt_version": PROMPT_VERSION,
        "prompt_policy_path": repo_relative(PROMPT_SPEC),
        "prompt_policy_file_sha256": sha256_file(PROMPT_SPEC),
        "prompt_policy_hash": prompt_spec["prompt_hash"],
        "prompt_count": len(rows),
        "prompt_hashes_hash": payload_sha256(hashes),
        "items": rows,
    }
    write_json(PROMPT_INDEX, payload)
    return payload


def write_conflict_ledger(semantic_index: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for record in semantic_index["records"]:
        rows.append(
            {
                "selection_rank": record["selection_rank"],
                "case_unit_id": record["case_unit_id"],
                "task_id": record["task_id"],
                "metadata_comparison_status": record["metadata_comparison"]["status"],
                "differences": record["metadata_comparison"]["differences"],
                "conflicts": record["metadata_conflicts"],
                "canonical_resolution_applied": record["readiness"][
                    "canonical_runtime_resolution_applied"
                ],
            }
        )
    payload = {
        "schema_version": "androidworld_metadata_code_conflict_ledger/v2",
        "authority_rule": "runtime goal/evaluator sources are canonical; conflicting metadata is retained as an audit record",
        "case_count": 116,
        "case_with_difference_count": sum(bool(row["differences"]) for row in rows),
        "conflict_record_count": sum(len(row["conflicts"]) for row in rows),
        "items": rows,
    }
    payload["ledger_sha256"] = payload_sha256(payload)
    write_json(CONFLICT_LEDGER, payload)
    return payload


def write_draft_input_freeze(
    *,
    items: list[dict[str, Any]],
    packet_index: list[dict[str, Any]],
    semantic_index: Mapping[str, Any],
    candidate_bundle: Mapping[str, Any],
    prompts: Mapping[str, str],
    prompt_index: Mapping[str, Any],
    drafter_config: Mapping[str, Any],
    llm_roles: Mapping[str, Any],
    slot_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    DRAFT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DRAFT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    if any(DRAFT_OUTPUT_DIR.iterdir()) or any(DRAFT_LOG_DIR.iterdir()):
        fail("draft output/log directories must be empty at input freeze")
    ordered_cases = [
        {
            "selection_rank": row["selection_rank"],
            "case_unit_id": row["case_unit_id"],
            "task_id": row["task_id"],
            "source_closure_sha256": row["source_closure_sha256"],
        }
        for row in packet_index
    ]
    semantic_contexts = {
        source["case_unit_id"]: source["source_context"]
        for source in candidate_bundle["sources"]
    }
    per_case = build_per_case_draft_bindings(
        ordered_cases,
        source_bundle=candidate_bundle,
        semantic_contexts=semantic_contexts,
        rendered_prompts=prompts,
    )
    manifest_bindings = {
        "candidate116": build_prelock_manifest_binding(
            name="candidate116",
            path=repo_relative(CANDIDATE_MANIFEST),
            sha256=sha256_file(CANDIDATE_MANIFEST),
            manifest=load_json(CANDIDATE_MANIFEST),
        ),
        "extra16": build_prelock_manifest_binding(
            name="extra16",
            path=repo_relative(EXTRA16_MANIFEST),
            sha256=sha256_file(EXTRA16_MANIFEST),
            manifest=load_json(EXTRA16_MANIFEST),
        ),
    }
    freeze = build_draft_input_freeze(
        freeze_id="androidworld_candidate116_draft_inputs_20260716_v1",
        frozen_at=BUILD_TIMESTAMP,
        manifest_bindings=manifest_bindings,
        ordered_cases=ordered_cases,
        packet_index_ref={"path": repo_relative(PACKET_INDEX), "sha256": sha256_file(PACKET_INDEX)},
        source_bundle_ref={"path": repo_relative(CANDIDATE_BUNDLE), "sha256": sha256_file(CANDIDATE_BUNDLE)},
        per_case_inputs=per_case,
        contract_drafter_config=drafter_config,
        contract_drafter_config_ref={"path": repo_relative(DRAFTER_CONFIG), "sha256": sha256_file(DRAFTER_CONFIG)},
        slot_ledger=slot_ledger,
        slot_ledger_ref={"path": repo_relative(SLOT_LEDGER), "sha256": sha256_file(SLOT_LEDGER)},
        llm_roles=llm_roles,
    )
    # Additional explicit bindings make the freeze self-explanatory without
    # weakening the pure module's native invariants.
    artifact_bindings = {
        "semantic_index": {"path": repo_relative(SEMANTIC_INDEX), "sha256": sha256_file(SEMANTIC_INDEX)},
        "raw_semantic_extraction": {
            "path": repo_relative(SEMANTIC_RAW_BUNDLE),
            "sha256": sha256_file(SEMANTIC_RAW_BUNDLE),
        },
        "metadata_conflicts": {"path": repo_relative(CONFLICT_LEDGER), "sha256": sha256_file(CONFLICT_LEDGER)},
        "source_bundle": {"path": repo_relative(CANDIDATE_BUNDLE), "sha256": sha256_file(CANDIDATE_BUNDLE)},
        "extra16_source_bundle": {"path": repo_relative(EXTRA16_BUNDLE), "sha256": sha256_file(EXTRA16_BUNDLE)},
        "candidate_manifest": {"path": repo_relative(CANDIDATE_MANIFEST), "sha256": sha256_file(CANDIDATE_MANIFEST)},
        "extra16_manifest": {"path": repo_relative(EXTRA16_MANIFEST), "sha256": sha256_file(EXTRA16_MANIFEST)},
        "slot_manifest": {"path": repo_relative(SLOT_LEDGER), "sha256": sha256_file(SLOT_LEDGER)},
        "prompt_spec": {"path": repo_relative(PROMPT_SPEC), "sha256": sha256_file(PROMPT_SPEC)},
        "prompt_index": {"path": repo_relative(PROMPT_INDEX), "sha256": sha256_file(PROMPT_INDEX)},
        "agents_config": {"path": repo_relative(DRAFTER_CONFIG), "sha256": sha256_file(DRAFTER_CONFIG)},
        "official100_selector": {"path": repo_relative(OFFICIAL100), "sha256": sha256_file(OFFICIAL100)},
    }
    freeze.update(
        {
            "source_count": 116,
            "frozen_before_runs": True,
            "prompt_version": PROMPT_VERSION,
            "prompt_policy_hash": load_json(PROMPT_SPEC)["prompt_hash"],
            "prompt_hashes_hash": prompt_index["prompt_hashes_hash"],
            "expected_category_counts": EXPECTED_GOAL_CATEGORY_COUNTS,
            "category_counts": semantic_index["category_counts"],
            "official100_selector_sha256": sha256_file(OFFICIAL100),
            "agents_config_hash": sha256_file(DRAFTER_CONFIG),
            "slot_sets": copy.deepcopy(slot_ledger["slot_sets"]),
            "artifact_bindings": artifact_bindings,
            "records": [
                {
                    **row,
                    "prompt_hash": row["rendered_prompt_sha256"],
                    "full_case_packet_path": packet_index[row["selection_rank"]]["case_packet_path"],
                    "full_case_packet_sha256": packet_index[row["selection_rank"]]["case_packet_sha256"],
                    "semantic_record_path": packet_index[row["selection_rank"]]["semantic_record_path"],
                    "semantic_record_sha256": packet_index[row["selection_rank"]]["semantic_record_sha256"],
                }
                for row in per_case
            ],
            "draft_output_assertions": {
                "draft_directory": repo_relative(DRAFT_OUTPUT_DIR),
                "draft_file_count_at_freeze": 0,
                "llm_log_directory": repo_relative(DRAFT_LOG_DIR),
                "llm_log_file_count_at_freeze": 0,
            },
        }
    )
    freeze.pop("freeze_sha256", None)
    freeze["freeze_sha256"] = payload_sha256(freeze)
    issues = validate_draft_input_freeze(
        freeze,
        expected_contract_drafter_config=drafter_config,
        expected_slot_ledger=slot_ledger,
    )
    if issues:
        fail(f"draft input freeze validation failed: {issues}")
    write_json(DRAFT_INPUT_FREEZE, freeze)
    return freeze


def validate_packets(
    *,
    items: list[dict[str, Any]],
    source_bundle: Path,
    resolver: SourceResolver,
    semantic_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    bundle = load_json(source_bundle)
    if bundle.get("source_count") != len(items) or len(bundle.get("sources") or []) != len(items):
        fail(f"source bundle count mismatch: {source_bundle}")
    source_by_id = {row["case_unit_id"]: row for row in bundle["sources"]}
    expected_ids = [row["case_unit_id"] for row in sorted(items, key=lambda row: int(row["selection_rank"]))]
    if list(source_by_id) != expected_ids:
        fail(f"source bundle order/set mismatch: {source_bundle}")
    rows: list[dict[str, Any]] = []
    totals = {"official_files": 0, "derived_files": 0, "copied_files": 0}
    for item in sorted(items, key=lambda row: int(row["selection_rank"])):
        task_id = item["task_id"]
        source = source_by_id[task_id]
        issues = validate_case_packet_source(source, f"$.sources[{item['selection_rank']}]")
        if issues:
            fail(f"source bundle validation failed for {task_id}: {[issue.to_dict() for issue in issues[:5]]}")
        forbidden = find_forbidden_inputs(source)
        if forbidden:
            fail(f"post-run fields leaked into source bundle for {task_id}: {[x.to_dict() for x in forbidden]}")
        manifest_path = REPO_ROOT / source["draft_input"]["raw_case_manifest_path"]
        compact_path = REPO_ROOT / source["draft_input"]["case_packet_path"]
        audit_input = source.get("audit_input") or {}
        packet_path = REPO_ROOT / str(audit_input.get("full_case_packet_path") or "")
        if source["draft_input"].get("view_kind") != "compact":
            fail(f"drafter source is not the compact packet for {task_id}")
        if "compact" not in compact_path.name or compact_path.name == "case_packet.md":
            fail(f"compact packet is not explicitly named for {task_id}")
        if not packet_path.is_file() or sha256_file(packet_path) != audit_input.get("full_case_packet_sha256"):
            fail(f"full audit packet binding mismatch for {task_id}")
        manifest = load_json(manifest_path)
        raw_dir = manifest_path.parent / "raw_case"
        actual_files = sorted(path.relative_to(raw_dir).as_posix() for path in raw_dir.rglob("*") if path.is_file())
        if actual_files != manifest["copied_files"]:
            fail(f"raw inventory mismatch for {task_id}")
        if set(actual_files) != set(manifest["sha256_per_file"]):
            fail(f"raw hash-key inventory mismatch for {task_id}")
        for rel in actual_files:
            if sha256_file(raw_dir / rel) != manifest["sha256_per_file"][rel]:
                fail(f"raw per-file hash mismatch for {task_id}: {rel}")
        for field in ("official_files", "derived_files", "packet_files"):
            values = list(manifest[field])
            if len(values) != len(set(values)) or not set(values).issubset(actual_files):
                fail(f"invalid {field} for {task_id}")
        if load_json(raw_dir / "derived/selected_task_source.json") != item:
            fail(f"selected-source helper mismatch for {task_id}")
        semantic = semantic_by_id[task_id]
        if load_json(raw_dir / "derived/canonical_task_semantics.json") != semantic:
            fail(f"canonical semantic helper mismatch for {task_id}")
        closure = load_json(raw_dir / "derived/source_closure.json")
        if closure["task_id"] != task_id or closure["unresolved_internal_imports"]:
            fail(f"invalid source closure for {task_id}")
        descriptors = closure["files"]
        if len(descriptors) != closure["closure_file_count"]:
            fail(f"closure count mismatch for {task_id}")
        closure_core = {
            (row["source_path"], row["archive_path"], row["sha256"])
            for row in descriptors
            if row["source_kind"] == "frozen_core_descriptor"
        }
        selected_core = {
            (row["source_path"], row["archive_path"], row["sha256"])
            for row in item["official_files"]
        }
        if closure_core != selected_core:
            fail(f"selected core descriptors are not preserved exactly for {task_id}")
        if not set(item["packet_files"]).issubset(set(manifest["packet_files"])):
            fail(f"selected packet files are not a subset of the strict packet for {task_id}")
        expected_source_hash = sha256_object(
            {"task_name": task_id, "source_files": [row["sha256"] for row in item["official_files"]]}
        )
        if item["source_sha256"] != expected_source_hash:
            fail(f"selected source_sha256 mismatch for {task_id}")
        for descriptor in descriptors:
            portable = descriptor["source_path"]
            archive = descriptor["archive_path"]
            expected = descriptor["sha256"]
            if sha256_file(resolver.resolve(portable)) != expected or sha256_file(raw_dir / archive) != expected:
                fail(f"closure source/copy hash mismatch for {task_id}: {archive}")
            if manifest["file_sources"].get(archive) != portable:
                fail(f"source pointer mismatch for {task_id}: {archive}")
        rerendered = render_case_packet(
            domain="androidworld",
            case_unit_id=task_id,
            task_id=task_id,
            raw_case_dir=raw_dir,
            raw_case_manifest=manifest,
        )
        if packet_path.read_text(encoding="utf-8") != rerendered:
            fail(f"case packet renderer mismatch for {task_id}")
        expected_context = semantic_source_context(item, semantic)
        if source.get("source_context") != expected_context:
            fail(f"explicit canonical source context mismatch for {task_id}")
        expected_compact, _ = render_compact_case_packet(item=item, semantic=semantic, closure=closure)
        if compact_path.read_text(encoding="utf-8") != expected_compact:
            fail(f"compact packet semantic rendering mismatch for {task_id}")
        if sha256_file(compact_path) != source["draft_input"]["case_packet_sha256"]:
            fail(f"compact packet source-bundle hash mismatch for {task_id}")
        prompt = build_drafter_prompt(source, prompt_version=PROMPT_VERSION)
        if payload_sha256({"prompt": prompt}) != source["draft_input"].get("prompt_sha256"):
            fail(f"rendered prompt hash mismatch for {task_id}")
        if not semantic["readiness"].get("static_draft_ready"):
            fail(f"semantic record is not statically draft-ready: {task_id}")
        forbidden_payload = find_forbidden_inputs({"manifest": manifest, "selected": item})
        if forbidden_payload:
            fail(f"post-run fields leaked into packet inputs for {task_id}: {[x.to_dict() for x in forbidden_payload]}")
        totals["official_files"] += len(manifest["official_files"])
        totals["derived_files"] += len(manifest["derived_files"])
        totals["copied_files"] += len(actual_files)
        rows.append(
            {
                "task_id": task_id,
                "selection_rank": item["selection_rank"],
                "status": "pass",
                "copied_file_count": len(actual_files),
                "closure_file_count": closure["closure_file_count"],
                "case_packet_sha256": sha256_file(packet_path),
                "compact_case_packet_sha256": sha256_file(compact_path),
                "rendered_prompt_sha256": source["draft_input"]["prompt_sha256"],
                "semantic_record_sha256": semantic["record_sha256"],
                "raw_case_manifest_sha256": sha256_file(manifest_path),
            }
        )
    return rows, totals


def scan_portability(paths: Iterable[Path], forbidden_roots: list[Path]) -> None:
    needles = [str(path).encode() for path in forbidden_roots] + [b"/Users/gss/"]
    for root in paths:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            data = path.read_bytes()
            for needle in needles:
                if needle and needle in data:
                    fail(f"local absolute path leaked into artifact: {path}: {needle.decode(errors='replace')}")


def runtime_preflight(installed_root: Path, clean_root: Path) -> dict[str, Any]:
    tracked_status = run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=installed_root, check=False)
    untracked_status = run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=installed_root, check=False)
    adb_candidates = [
        Path("/opt/homebrew/bin/adb"),
        Path.home() / "Library/Android/sdk/platform-tools/adb",
    ]
    adb = next((path for path in adb_candidates if path.is_file()), None)
    adb_result = run([str(adb), "devices", "-l"], check=False) if adb else None
    emulator_candidates = [
        Path.home() / "Library/Android/sdk/emulator/emulator",
        Path("/opt/homebrew/bin/emulator"),
    ]
    emulator = next((path for path in emulator_candidates if path.is_file()), None)
    avd_result = run([str(emulator), "-list-avds"], check=False) if emulator else None
    devices = []
    if adb_result:
        devices = [line for line in adb_result.stdout.splitlines()[1:] if line.strip() and "\tdevice" in line]
    avds = [line.strip() for line in (avd_result.stdout.splitlines() if avd_result else []) if line.strip()]
    blocked_reasons = []
    if tracked_status.stdout.strip():
        blocked_reasons.append("runtime checkout is dirty and can shadow the frozen site-package source")
    if not avds:
        blocked_reasons.append("no Android Virtual Device is currently registered")
    if not devices:
        blocked_reasons.append("no adb device is online")
    venv_python = installed_root / ".venv311/bin/python"
    pip_check = run([str(venv_python), "-m", "pip", "check"], check=False) if venv_python.is_file() else None
    if pip_check is None or pip_check.returncode != 0:
        blocked_reasons.append("the AndroidWorld Python environment does not pass pip check")
    return {
        "schema_version": "androidworld_runtime_preflight/v1",
        "status": "blocked" if blocked_reasons else "pass",
        "scope": "runtime/device readiness; intentionally separate from static packet acceptance",
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "clean_source_root_git_status": run(["git", "status", "--porcelain"], cwd=clean_root).stdout,
        "runtime_checkout_tracked_changes": tracked_status.stdout.splitlines(),
        "runtime_checkout_untracked_top_level": [
            line for line in untracked_status.stdout.splitlines() if line not in tracked_status.stdout.splitlines()
        ],
        "pip_check_returncode": pip_check.returncode if pip_check else None,
        "pip_check_output": (pip_check.stdout + pip_check.stderr).splitlines() if pip_check else [],
        "adb_path": str(adb) if adb else None,
        "adb_devices": devices,
        "emulator_path": str(emulator) if emulator else None,
        "registered_avds": avds,
        "blocked_reasons": blocked_reasons,
        "consequence": "Packets may be drafted from after static acceptance, but AndroidWorld executions must not start until this report passes on the frozen runtime/AVD.",
    }


def shared_source_inventory(resolver: SourceResolver) -> list[tuple[Path, Path, str]]:
    rows: list[tuple[Path, Path, str]] = []
    for source in sorted(path for path in resolver.package_root.rglob("*") if path.is_file()):
        if "__pycache__" in source.parts or source.suffix == ".pyc":
            continue
        target = SHARED_TREE / source.relative_to(resolver.clean_root)
        rows.append((source.resolve(), target, "git_source"))
    generated_root = resolver.site_package / "task_evals/information_retrieval/proto"
    for name in ("state_pb2.py", "state_pb2_grpc.py", "task_pb2.py", "task_pb2_grpc.py"):
        source = (generated_root / name).resolve()
        if not source.is_file():
            fail(f"required generated protobuf artifact is missing: {source}")
        target = SHARED_TREE / "android_world/task_evals/information_retrieval/proto" / name
        if any(existing_target == target for _, existing_target, _ in rows):
            fail(f"generated protobuf target collides with tracked source: {target}")
        rows.append((source, target, "generated_protobuf"))
    return rows


def build_shared_source_snapshot(resolver: SourceResolver) -> None:
    if SHARED_DIR.exists() and any(SHARED_DIR.iterdir()):
        fail(f"refusing to overwrite shared source snapshot: {SHARED_DIR}")
    entries: list[dict[str, Any]] = []
    for source, target, source_kind in shared_source_inventory(resolver):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        expected = sha256_file(source)
        if sha256_file(target) != expected:
            fail(f"shared source copy hash mismatch: {target}")
        entries.append(
            {
                "path": target.relative_to(SHARED_TREE).as_posix(),
                "sha256": expected,
                "source_kind": source_kind,
                "git_blob_oid": resolver.git_blob(source),
            }
        )
    payload = {
        "schema_version": "androidworld_shared_source_snapshot/v1",
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "source_tree_clean": True,
        "source_locator": "<ANDROIDWORLD_CLEAN_SOURCE_ROOT>",
        "tracked_and_resource_file_count": sum(1 for row in entries if row["source_kind"] == "git_source"),
        "generated_protobuf_file_count": sum(1 for row in entries if row["source_kind"] == "generated_protobuf"),
        "file_count": len(entries),
        "tree_sha256": sha256_path(SHARED_TREE),
        "files": entries,
    }
    write_json(SHARED_MANIFEST, payload)


def validate_shared_source_snapshot(resolver: SourceResolver) -> dict[str, Any]:
    payload = load_json(SHARED_MANIFEST)
    if payload.get("source_commit") != EXPECTED_SOURCE_COMMIT:
        fail("shared source snapshot commit mismatch")
    expected_rows = shared_source_inventory(resolver)
    expected = []
    for source, target, source_kind in expected_rows:
        expected.append(
            {
                "path": target.relative_to(SHARED_TREE).as_posix(),
                "sha256": sha256_file(source),
                "source_kind": source_kind,
                "git_blob_oid": resolver.git_blob(source),
            }
        )
    if payload.get("files") != expected:
        fail("shared source snapshot manifest differs from the pinned source inventory")
    actual_files = sorted(path.relative_to(SHARED_TREE).as_posix() for path in SHARED_TREE.rglob("*") if path.is_file())
    if actual_files != sorted(row["path"] for row in expected):
        fail("shared source snapshot file set mismatch")
    for row in expected:
        if sha256_file(SHARED_TREE / row["path"]) != row["sha256"]:
            fail(f"shared source snapshot file hash mismatch: {row['path']}")
    tree_hash = sha256_path(SHARED_TREE)
    if tree_hash != payload.get("tree_sha256"):
        fail("shared source snapshot tree hash mismatch")
    return {"file_count": len(expected), "tree_sha256": tree_hash}


def write_readme(static_report: Mapping[str, Any], runtime_report: Mapping[str, Any]) -> None:
    text = f"""# AndroidWorld candidate116 packet workspace

This directory is the isolated Step 4B source-packet workspace. It does not modify the submitted baseline, legacy `results/`, or the checked-in `official100` selector.

## Acceptance state

- Static packet validation: **{static_report['status']}** ({static_report['checks']['candidate_packet_count']}/116 candidate packets; {static_report['checks']['extra16_packet_count']}/16 extra packets).
- Independent strict acceptance: **pass** (116 semantic records, 116 unique real drafter prompts, and 348 predeclared slots).
- Goal mechanisms: 57 format templates, 33 computed goals, 1 branch template, and 25 IR proto prompts.
- Metadata/code audit: 23 differences are explicitly recorded; runtime goal/evaluator sources take precedence. All 25 incidental `abc.py` provenance labels are excluded from canonical provenance.
- Runtime/device preflight: **{runtime_report['status']}**. This is a separate gate and does not weaken static packet checks.
- Legacy-root guard: complete content-tree hashes and entry counts are byte-identical before/after for `neurips_ed_track_minimal`, `results/`, and `paper_result_packages`; the checked-in official100 selector hash is also unchanged. Pre-existing non-immutable flags are recorded rather than misreported as immutable.
- Experiment manifests remain honest `draft` / prelock manifests with empty contract locks. The draft-input sidecar is frozen, but no contract draft or run output exists yet.

## Canonical outputs

- `manifests/androidworld_candidate116_manifest.json`
- `manifests/androidworld_extra16_manifest.json`
- `official_splits/androidworld_candidate116_selected_task_sources.json`
- `official_splits/androidworld_extra16_selected_task_sources.json`
- `case_packets/androidworld/<case_id>/`
- `semantic_records/androidworld_candidate116_semantic_index.json`
- `semantic_records/androidworld_candidate116_metadata_code_conflicts.json`
- `source_bundles/androidworld_candidate116_source_bundle.json`
- `source_bundles/androidworld_extra16_source_bundle.json`
- `ledgers/androidworld_candidate116_348_slot_ledger.json`
- `draft_config/androidworld_candidate116_drafter_config.json`
- `prompts/androidworld_candidate116_rendered_prompt_index.json`
- `freeze/androidworld_candidate116_draft_input_freeze.json`
- `shared_source/androidworld_source_snapshot_manifest.json`
- `validation/pre_operation_readonly_snapshot.json`
- `validation/post_operation_readonly_snapshot.json`
- `validation/strict_acceptance_report.json`
- `validation/static_validation_report.json`
- `validation/runtime_preflight_report.json`
- `validation/SHA256SUMS`

Run `python3 scripts/build_and_validate.py --verify-only` to recheck all retained artifacts without rebuilding them.
"""
    (WORK_ROOT / "README.md").write_text(text, encoding="utf-8")


def write_inventory() -> None:
    excluded = {VALIDATION_DIR / "SHA256SUMS", VALIDATION_DIR / "artifact_inventory.json"}
    files = sorted(
        path
        for path in WORK_ROOT.rglob("*")
        if path.is_file()
        and path not in excluded
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
    inventory = {
        "schema_version": "androidworld_candidate116_artifact_inventory/v1",
        "file_count": len(files),
        "files": [{"path": path.relative_to(WORK_ROOT).as_posix(), "sha256": sha256_file(path)} for path in files],
    }
    inventory_path = VALIDATION_DIR / "artifact_inventory.json"
    write_json(inventory_path, inventory)
    checksum_files = files + [inventory_path]
    lines = [f"{sha256_file(path)}  {path.relative_to(WORK_ROOT).as_posix()}" for path in checksum_files]
    (VALIDATION_DIR / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_inputs(clean_root: Path, installed_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], SourceResolver, dict[str, Any]]:
    if sha256_file(CANDIDATE_POOL) != EXPECTED_CANDIDATE_SHA256:
        fail("candidate116 pool hash changed")
    if sha256_file(OFFICIAL100) != EXPECTED_OFFICIAL100_SHA256:
        fail("official100 selector hash changed")
    clean_head = run(["git", "rev-parse", "HEAD"], cwd=clean_root).stdout.strip()
    if clean_head != EXPECTED_SOURCE_COMMIT:
        fail(f"clean AndroidWorld source commit mismatch: {clean_head}")
    if run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=clean_root).stdout.strip():
        fail("the designated frozen AndroidWorld source tree is not clean")
    venv_python = installed_root / ".venv311/bin/python"
    if not venv_python.is_file():
        fail(f"AndroidWorld venv Python is missing: {venv_python}")
    live_items, python_runtime_root = live_candidate_pool(venv_python)
    resolver = SourceResolver(clean_root=clean_root, installed_root=installed_root, python_runtime_root=python_runtime_root)

    candidate = load_json(CANDIDATE_POOL)
    frozen_items = [dict(row) for row in candidate["items"]]
    if candidate.get("candidate_count") != 116 or len(frozen_items) != 116:
        fail("candidate pool does not contain exactly 116 items")
    if len({row["task_id"] for row in frozen_items}) != 116:
        fail("candidate task ids are not unique")
    if sorted(int(row["selection_rank"]) for row in frozen_items) != list(range(116)):
        fail("candidate selection ranks are not exactly 0..115")
    recalculated = copy.deepcopy(frozen_items)
    for row in recalculated:
        row.pop("selection_order_key", None)
        row.pop("selection_rank", None)
    normalize_candidate_items(recalculated)
    if sorted(recalculated, key=lambda row: row["task_id"]) != sorted(frozen_items, key=lambda row: row["task_id"]):
        fail("candidate selection keys/ranks cannot be reproduced")
    if sorted(live_items, key=lambda row: row["task_id"]) != sorted(frozen_items, key=lambda row: row["task_id"]):
        fail("live site-package registry/metadata differs from the frozen candidate pool")
    if sha256_object(case_unit_records(frozen_items)) != candidate["eligible_case_unit_set_hash"]:
        fail("candidate eligible-case hash mismatch")
    if sha256_object(selection_order_records(frozen_items)) != candidate["case_selection_order_hash"]:
        fail("candidate selection-order hash mismatch")

    official100 = load_json(OFFICIAL100)
    official_items = [dict(row) for row in official100["items"]]
    frozen_ordered = sorted(frozen_items, key=lambda row: int(row["selection_rank"]))
    for rank, existing in enumerate(official_items):
        stripped = {key: value for key, value in existing.items() if key not in {"source_ref", "official_files", "packet_files", "source_sha256"}}
        if stripped != frozen_ordered[rank]:
            fail(f"official100 is not the exact frozen candidate prefix at rank {rank}")
        for descriptor in existing["official_files"]:
            actual = resolver.resolve(descriptor["source_path"])
            if sha256_file(actual) != descriptor["sha256"]:
                fail(f"official100 descriptor source drift: {existing['task_id']} {descriptor['source_path']}")

    input_guard = {
        "candidate_pool_sha256": sha256_file(CANDIDATE_POOL),
        "official100_selector_sha256": sha256_file(OFFICIAL100),
        "source_commit": clean_head,
        "source_tree_clean": True,
        "live_registry_count": len(live_items),
        "live_registry_exact_match": True,
        "official100_membership_and_order_match_candidate_prefix": True,
        "official100_selector_remains_unmodified_input": True,
    }
    return frozen_ordered, frozen_ordered[100:], resolver, input_guard


def selector_payload(items: list[dict[str, Any]], *, parent: str | None = None) -> dict[str, Any]:
    payload = {
        "benchmark": "AndroidWorld",
        "schema_version": "official_case_source.androidworld_selected_tasks.v1",
        "selected_count": len(items),
        "selection_hash_function": "sha256",
        "selection_salt_hash": sha256_object(SELECTION_SALT),
        "candidate_pool_path": repo_relative(CANDIDATE_POOL),
        "candidate_pool_sha256": EXPECTED_CANDIDATE_SHA256,
        "items": items,
    }
    if parent:
        payload["parent_selected_sources_path"] = parent
        payload["selection_rank_range"] = [100, 115]
    return payload


def verify_only(clean_root: Path, installed_root: Path) -> dict[str, Any]:
    frozen_items, _, resolver, input_guard = prepare_inputs(clean_root, installed_root)
    shared = validate_shared_source_snapshot(resolver)
    raw_semantics = load_json(SEMANTIC_RAW_BUNDLE)
    raw_hash_input = dict(raw_semantics)
    declared_raw_hash = raw_hash_input.pop("bundle_sha256", None)
    if declared_raw_hash != semantic_object_sha256(raw_hash_input):
        fail("raw semantic extraction bundle hash mismatch")
    expected_semantic_index, semantic_by_id = build_semantic_index(raw_semantics, frozen_items)
    if load_json(SEMANTIC_INDEX) != expected_semantic_index:
        fail("semantic index differs from deterministic canonical reconstruction")
    for semantic in expected_semantic_index["records"]:
        retained = SEMANTIC_DIR / "cases" / semantic["task_id"] / "canonical_task_semantics.json"
        if load_json(retained) != semantic:
            fail(f"per-case semantic record differs from index: {semantic['task_id']}")
    items = corrected_selected_items(frozen_items, semantic_by_id, resolver)
    tail = items[100:]
    expected_candidate_selector = selector_payload(items)
    expected_extra_selector = selector_payload(tail, parent=repo_relative(CANDIDATE_SELECTOR))
    if load_json(CANDIDATE_SELECTOR) != expected_candidate_selector or load_json(EXTRA16_SELECTOR) != expected_extra_selector:
        fail("retained selected-source manifest differs from deterministic reconstruction")
    validate_manifest_schema(CANDIDATE_MANIFEST)
    validate_manifest_schema(EXTRA16_MANIFEST)
    candidate_rows, totals = validate_packets(
        items=items,
        source_bundle=CANDIDATE_BUNDLE,
        resolver=resolver,
        semantic_by_id=semantic_by_id,
    )
    extra_rows, _ = validate_packets(
        items=tail,
        source_bundle=EXTRA16_BUNDLE,
        resolver=resolver,
        semantic_by_id=semantic_by_id,
    )
    if [row["task_id"] for row in candidate_rows[100:]] != [row["task_id"] for row in extra_rows]:
        fail("extra16 source bundle is not the exact candidate116 tail")
    candidate_bundle = load_json(CANDIDATE_BUNDLE)
    extra_bundle = load_json(EXTRA16_BUNDLE)
    if extra_bundle["sources"] != candidate_bundle["sources"][100:]:
        fail("extra16 compact source entries are not the exact candidate tail")

    prompt_spec = build_prompt_policy_spec()
    if load_json(PROMPT_SPEC) != prompt_spec:
        fail("retained prompt policy spec differs from its implementation")
    expected_config = build_contract_drafter_config(
        load_json(BASELINE_AGENTS_CONFIG),
        prompt_version=PROMPT_VERSION,
        prompt_hash=prompt_spec["prompt_hash"],
    )
    if load_json(DRAFTER_CONFIG) != expected_config:
        fail("dedicated drafter config differs from deterministic projection")
    llm_roles = {"contract_drafter": project_contract_drafter_llm_role(expected_config)}
    for manifest_path, expected_slot_hash, expected_count in (
        (CANDIDATE_MANIFEST, EXPECTED_CANDIDATE116_SLOT_HASH, 348),
        (EXTRA16_MANIFEST, EXPECTED_EXTRA16_SLOT_HASH, 48),
    ):
        manifest = load_json(manifest_path)
        if manifest.get("status") != "draft" or not str(manifest.get("manifest_version", "")).endswith("-prelock"):
            fail(f"manifest is not truthfully draft/prelock: {manifest_path}")
        if manifest.get("contract_locks") != [] or manifest.get("contract_locks_hash") != EMPTY_LIST_HASH:
            fail(f"prelock manifest contains a contract lock: {manifest_path}")
        if manifest.get("agents_config_hash") != sha256_file(DRAFTER_CONFIG):
            fail(f"manifest drafter config hash mismatch: {manifest_path}")
        domain = manifest["domains"][0]
        if domain["record_slot_count"] != expected_count or domain["planned_record_slot_ids_hash"] != expected_slot_hash:
            fail(f"manifest slot declaration mismatch: {manifest_path}")

    ledger = load_json(SLOT_LEDGER)
    ledger_issues = validate_candidate116_slot_ledger(ledger)
    if ledger_issues:
        fail(f"slot ledger failed validation: {ledger_issues}")
    assert_known_slot_hashes(ledger)
    prompt_index = load_json(PROMPT_INDEX)
    prompt_hashes = [row["rendered_prompt_sha256"] for row in prompt_index["items"]]
    actual_prompt_hashes = [
        payload_sha256({"prompt": build_drafter_prompt(source, prompt_version=PROMPT_VERSION)})
        for source in candidate_bundle["sources"]
    ]
    if prompt_hashes != actual_prompt_hashes or len(set(actual_prompt_hashes)) != 116:
        fail("prompt index does not bind 116 unique real drafter prompts")
    if prompt_index["prompt_hashes_hash"] != payload_sha256(actual_prompt_hashes):
        fail("prompt set hash mismatch")

    freeze = load_json(DRAFT_INPUT_FREEZE)
    freeze_issues = validate_draft_input_freeze(
        freeze,
        expected_contract_drafter_config=expected_config,
        expected_slot_ledger=ledger,
    )
    if freeze_issues:
        fail(f"draft input freeze failed validation: {freeze_issues}")
    if freeze.get("source_count") != 116 or freeze.get("frozen_before_runs") is not True:
        fail("draft input freeze completeness assertion failed")
    if freeze.get("prompt_hashes_hash") != prompt_index["prompt_hashes_hash"]:
        fail("draft input freeze prompt set mismatch")
    if any(DRAFT_OUTPUT_DIR.iterdir()) or any(DRAFT_LOG_DIR.iterdir()):
        fail("draft outputs or LLM logs appeared after the pre-draft input freeze")

    pre_snapshot = load_json(PRE_OPERATION_SNAPSHOT)
    post_snapshot = load_json(POST_OPERATION_SNAPSHOT)
    if readonly_snapshot_core(pre_snapshot) != readonly_snapshot_core(post_snapshot):
        fail("old read-only root content-tree state differs before/after")
    if load_json(READONLY_GUARD_REPORT).get("status") != "pass":
        fail("read-only guard report is not pass")
    conflict_ledger = load_json(CONFLICT_LEDGER)
    if conflict_ledger.get("case_count") != 116 or conflict_ledger.get("conflict_record_count") != 23:
        fail("metadata/code conflict ledger completeness mismatch")

    scan_portability(
        [
            PACKET_ROOT,
            MANIFEST_DIR,
            SELECTOR_DIR,
            BUNDLE_DIR,
            SHARED_DIR,
            SEMANTIC_DIR,
            CONFIG_DIR,
            PROMPT_DIR,
            FREEZE_DIR,
            LEDGER_DIR,
        ],
        [clean_root, installed_root],
    )
    return {
        "schema_version": "androidworld_candidate116_static_validation/v2",
        "status": "pass",
        "scope": "strict pre-draft acceptance: selection, real task semantics, source closure, compact packets, prompts, manifests, slots, freeze, and read-only guards",
        "input_guard": input_guard,
        "checks": {
            "candidate_pool_count": 116,
            "official100_prefix_count": 100,
            "extra16_count": 16,
            "candidate_packet_count": len(candidate_rows),
            "extra16_packet_count": len(extra_rows),
            "source_bundle_candidate_count": load_json(CANDIDATE_BUNDLE)["source_count"],
            "source_bundle_extra16_count": load_json(EXTRA16_BUNDLE)["source_count"],
            "all_raw_inventories_exact": True,
            "all_declared_file_hashes_match": True,
            "all_core_descriptor_sources_match": True,
            "all_internal_source_closures_resolved": True,
            "all_rendered_packets_byte_exact": True,
            "all_source_contexts_derive": True,
            "all_116_semantic_records_complete": True,
            "semantic_consistency_checks_pass": True,
            "goal_category_counts": expected_semantic_index["category_counts"],
            "abc_runtime_provenance_corrected_count": 25,
            "metadata_code_conflict_records": conflict_ledger["conflict_record_count"],
            "all_compact_packets_byte_exact": True,
            "all_116_real_prompt_hashes_frozen": True,
            "slot_ledger_348_predeclared": True,
            "slot_hash_candidate116": EXPECTED_CANDIDATE116_SLOT_HASH,
            "slot_hash_official100": EXPECTED_OFFICIAL100_SLOT_HASH,
            "slot_hash_extra16": EXPECTED_EXTRA16_SLOT_HASH,
            "draft_input_freeze_valid": True,
            "manifests_draft_prelock": True,
            "old_roots_content_tree_pre_post_equal": True,
            "all_paths_portable": True,
            "post_run_fields_absent": True,
            "shared_frozen_source_snapshot_complete": True,
            "official100_untouched": sha256_file(OFFICIAL100) == EXPECTED_OFFICIAL100_SHA256,
        },
        "totals": totals,
        "shared_source_snapshot": shared,
        "semantic_index_sha256": sha256_file(SEMANTIC_INDEX),
        "prompt_index_sha256": sha256_file(PROMPT_INDEX),
        "slot_ledger_sha256": sha256_file(SLOT_LEDGER),
        "draft_input_freeze_file_sha256": sha256_file(DRAFT_INPUT_FREEZE),
        "draft_input_freeze_payload_sha256": freeze["freeze_sha256"],
        "packet_tree_sha256": sha256_path(PACKET_ROOT),
        "candidate_manifest_sha256": sha256_file(CANDIDATE_MANIFEST),
        "extra16_manifest_sha256": sha256_file(EXTRA16_MANIFEST),
        "candidate_source_bundle_sha256": sha256_file(CANDIDATE_BUNDLE),
        "extra16_source_bundle_sha256": sha256_file(EXTRA16_BUNDLE),
        "per_case": candidate_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clean-source-root",
        type=Path,
        default=Path("/Users/gss/Downloads/AgentHazard-dynamic-official/android_world"),
    )
    parser.add_argument(
        "--installed-root",
        type=Path,
        default=Path("/Users/gss/benchmarks/android_world"),
    )
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="replace only artifacts in the isolated androidworld_candidate116 workspace",
    )
    parser.add_argument(
        "--reuse-pre-snapshot",
        action="store_true",
        help="on a failed isolated rebuild retry, preserve the already captured old-root before snapshot",
    )
    args = parser.parse_args()
    clean_root = args.clean_source_root.resolve()
    installed_root = args.installed_root.resolve()
    if not WORK_ROOT.is_relative_to(REPO_ROOT / "rebuttal_work/runtime_outputs/submission_rebuttal"):
        fail(f"unsafe work root: {WORK_ROOT}")

    if args.verify_only:
        report = verify_only(clean_root, installed_root)
        checksum_file = VALIDATION_DIR / "SHA256SUMS"
        if checksum_file.is_file():
            completed = run(
                ["shasum", "-a", "256", "-c", checksum_file.relative_to(WORK_ROOT).as_posix()],
                cwd=WORK_ROOT,
                check=False,
            )
            if completed.returncode != 0:
                fail(f"retained artifact checksum verification failed:\n{completed.stdout}\n{completed.stderr}")
        print(json.dumps({"status": "pass", "mode": "verify-only", "packet_count": 116}, indent=2))
        return

    retained_pre_snapshot = None
    if args.reuse_pre_snapshot:
        if not args.rebuild or not PRE_OPERATION_SNAPSHOT.is_file():
            fail("--reuse-pre-snapshot requires --rebuild and an existing before snapshot")
        retained_pre_snapshot = load_json(PRE_OPERATION_SNAPSHOT)
    if args.rebuild:
        clean_generated_outputs()
    generated_roots = [
        MANIFEST_DIR,
        SELECTOR_DIR,
        PACKET_ROOT,
        BUNDLE_DIR,
        VALIDATION_DIR,
        INDEX_DIR,
        SHARED_DIR,
        SEMANTIC_DIR,
        CONFIG_DIR,
        PROMPT_DIR,
        FREEZE_DIR,
        LEDGER_DIR,
        DRAFT_OUTPUT_DIR,
        DRAFT_LOG_DIR,
    ]
    for root in generated_roots:
        if root.exists() and any(root.iterdir()):
            fail(f"refusing to overwrite existing generated root: {root}")

    pre_snapshot = retained_pre_snapshot or readonly_operation_snapshot(phase="before")
    write_json(PRE_OPERATION_SNAPSHOT, pre_snapshot)
    immutable_counts = immutable_root_guard()
    official100_before = sha256_file(OFFICIAL100)
    frozen_items, _, resolver, input_guard = prepare_inputs(clean_root, installed_root)
    build_shared_source_snapshot(resolver)

    raw_semantics = extract_canonical_semantic_records(
        shared_source_root=SHARED_TREE,
        venv_python=installed_root / ".venv311/bin/python",
        expected_task_ids=[row["task_id"] for row in frozen_items],
    )
    write_json(SEMANTIC_RAW_BUNDLE, raw_semantics)
    semantic_index, semantic_by_id = build_semantic_index(raw_semantics, frozen_items)
    for record in semantic_index["records"]:
        write_json(
            SEMANTIC_DIR / "cases" / record["task_id"] / "canonical_task_semantics.json",
            record,
        )
    write_json(SEMANTIC_INDEX, semantic_index)
    write_conflict_ledger(semantic_index)

    candidate_items = corrected_selected_items(frozen_items, semantic_by_id, resolver)
    tail = candidate_items[100:]
    write_json(CANDIDATE_SELECTOR, selector_payload(candidate_items))
    write_json(EXTRA16_SELECTOR, selector_payload(tail, parent=repo_relative(CANDIDATE_SELECTOR)))

    prompt_spec, drafter_config, llm_roles = write_drafter_configuration()
    agents_config_hash = sha256_file(DRAFTER_CONFIG)
    slot_ledger = build_slot_ledger(candidate_items)
    freeze_id = "androidworld_candidate116_draft_inputs_20260716_v1"

    write_json(
        CANDIDATE_MANIFEST,
        experiment_manifest(
            items=candidate_items,
            manifest_id="androidworld_candidate116_manifest",
            source_bundle_hash="0" * 64,
            source_bundle_path=CANDIDATE_BUNDLE,
            agents_config_hash=agents_config_hash,
            llm_roles=llm_roles,
            planned_record_slot_ids_hash=EXPECTED_CANDIDATE116_SLOT_HASH,
            draft_input_freeze_id=freeze_id,
        ),
    )
    write_json(
        EXTRA16_MANIFEST,
        experiment_manifest(
            items=tail,
            manifest_id="androidworld_extra16_manifest",
            source_bundle_hash="0" * 64,
            source_bundle_path=EXTRA16_BUNDLE,
            agents_config_hash=agents_config_hash,
            llm_roles=llm_roles,
            planned_record_slot_ids_hash=EXPECTED_EXTRA16_SLOT_HASH,
            draft_input_freeze_id=freeze_id,
        ),
    )

    packet_index = build_packet_tree(
        output_root=PACKET_ROOT,
        items=candidate_items,
        resolver=resolver,
        semantic_by_id=semantic_by_id,
        collect_index=True,
    )
    write_json(
        PACKET_INDEX,
        {
            "schema_version": "androidworld_candidate116_packet_index/v1",
            "candidate_count": 116,
            "official100_count": 100,
            "extra16_count": 16,
            "items": packet_index,
        },
    )

    build_case_packet_source_bundle(
        manifest_path=CANDIDATE_MANIFEST,
        case_packets_root=PACKET_ROOT,
        previous_source_bundle_path=WORK_ROOT / "nonexistent_candidate_bundle.json",
        output_path=CANDIDATE_BUNDLE,
        allow_generated_contract_ids=True,
    )
    build_case_packet_source_bundle(
        manifest_path=EXTRA16_MANIFEST,
        case_packets_root=PACKET_ROOT,
        previous_source_bundle_path=WORK_ROOT / "nonexistent_extra16_bundle.json",
        output_path=EXTRA16_BUNDLE,
        allow_generated_contract_ids=True,
    )
    candidate_bundle, candidate_prompts = finalize_compact_source_bundle(
        path=CANDIDATE_BUNDLE,
        packet_index=packet_index,
        semantic_by_id=semantic_by_id,
        prompt_version=PROMPT_VERSION,
    )
    extra_bundle, extra_prompts = finalize_compact_source_bundle(
        path=EXTRA16_BUNDLE,
        packet_index=packet_index,
        semantic_by_id=semantic_by_id,
        prompt_version=PROMPT_VERSION,
    )
    if extra_bundle["sources"] != candidate_bundle["sources"][100:]:
        fail("extra16 compact source bundle is not the exact candidate116 tail")
    if extra_prompts != {task_id: candidate_prompts[task_id] for task_id in extra_prompts}:
        fail("extra16 prompts are not the exact candidate116 tail prompts")
    prompt_index = write_prompt_index(
        prompts=candidate_prompts,
        items=candidate_items,
        prompt_spec=prompt_spec,
    )
    candidate_manifest = experiment_manifest(
        items=candidate_items,
        manifest_id="androidworld_candidate116_manifest",
        source_bundle_hash=sha256_file(CANDIDATE_BUNDLE),
        source_bundle_path=CANDIDATE_BUNDLE,
        agents_config_hash=agents_config_hash,
        llm_roles=llm_roles,
        planned_record_slot_ids_hash=EXPECTED_CANDIDATE116_SLOT_HASH,
        draft_input_freeze_id=freeze_id,
    )
    extra_manifest = experiment_manifest(
        items=tail,
        manifest_id="androidworld_extra16_manifest",
        source_bundle_hash=sha256_file(EXTRA16_BUNDLE),
        source_bundle_path=EXTRA16_BUNDLE,
        agents_config_hash=agents_config_hash,
        llm_roles=llm_roles,
        planned_record_slot_ids_hash=EXPECTED_EXTRA16_SLOT_HASH,
        draft_input_freeze_id=freeze_id,
    )
    write_json(CANDIDATE_MANIFEST, candidate_manifest)
    write_json(EXTRA16_MANIFEST, extra_manifest)

    write_draft_input_freeze(
        items=candidate_items,
        packet_index=packet_index,
        semantic_index=semantic_index,
        candidate_bundle=candidate_bundle,
        prompts=candidate_prompts,
        prompt_index=prompt_index,
        drafter_config=drafter_config,
        llm_roles=llm_roles,
        slot_ledger=slot_ledger,
    )

    post_snapshot = readonly_operation_snapshot(phase="after")
    write_json(POST_OPERATION_SNAPSHOT, post_snapshot)
    pre_core = readonly_snapshot_core(pre_snapshot)
    post_core = readonly_snapshot_core(post_snapshot)
    readonly_guard = {
        "schema_version": "androidworld_candidate116_readonly_guard/v2",
        "status": "pass" if pre_core == post_core else "fail",
        "pre_snapshot_path": repo_relative(PRE_OPERATION_SNAPSHOT),
        "pre_snapshot_sha256": sha256_file(PRE_OPERATION_SNAPSHOT),
        "post_snapshot_path": repo_relative(POST_OPERATION_SNAPSHOT),
        "post_snapshot_sha256": sha256_file(POST_OPERATION_SNAPSHOT),
        "content_tree_state_equal": pre_core == post_core,
        "official100_sha256_before": official100_before,
        "official100_sha256_after": sha256_file(OFFICIAL100),
        "official100_equal": official100_before == sha256_file(OFFICIAL100),
        "preexisting_immutable_flag_observations": immutable_counts,
    }
    write_json(READONLY_GUARD_REPORT, readonly_guard)
    if readonly_guard["status"] != "pass" or not readonly_guard["official100_equal"]:
        fail("legacy read-only roots or official100 changed during the build")

    report = verify_only(clean_root, installed_root)
    with tempfile.TemporaryDirectory(prefix="android116-determinism-") as temp_dir:
        second_root = Path(temp_dir) / "case_packets"
        build_packet_tree(
            output_root=second_root,
            items=candidate_items,
            resolver=resolver,
            semantic_by_id=semantic_by_id,
            collect_index=False,
        )
        second_hash = sha256_path(second_root)
    if second_hash != report["packet_tree_sha256"]:
        fail(f"deterministic rebuild mismatch: {report['packet_tree_sha256']} != {second_hash}")
    report["checks"]["deterministic_second_build_byte_exact"] = True
    immutable_counts_after = immutable_root_guard()
    if immutable_counts_after != immutable_counts:
        fail("legacy immutable-root state changed during the candidate116 build")
    report["checks"]["legacy_immutable_roots_pre_post_equal"] = True
    report["checks"]["legacy_immutable_roots_observed"] = immutable_counts
    report["checks"]["official100_pre_post_hash_equal"] = official100_before == sha256_file(OFFICIAL100)
    if not report["checks"]["official100_pre_post_hash_equal"]:
        fail("official100 changed during build")
    strict_report = validate_strict_acceptance(
        AcceptancePaths(
            repo_root=REPO_ROOT,
            work_root=WORK_ROOT,
            semantic_index=SEMANTIC_INDEX,
            source_bundle=CANDIDATE_BUNDLE,
            candidate_manifest=CANDIDATE_MANIFEST,
            extra16_manifest=EXTRA16_MANIFEST,
            slot_manifest=SLOT_LEDGER,
            draft_input_freeze=DRAFT_INPUT_FREEZE,
            old_snapshot_before=PRE_OPERATION_SNAPSHOT,
            old_snapshot_after=POST_OPERATION_SNAPSHOT,
            official100_selector=OFFICIAL100,
            conflict_ledger=CONFLICT_LEDGER,
            extra16_source_bundle=EXTRA16_BUNDLE,
            agents_config=DRAFTER_CONFIG,
        )
    )
    write_json(STRICT_ACCEPTANCE_REPORT, strict_report)
    report["checks"]["independent_strict_acceptance"] = strict_report["status"] == "pass"
    write_json(VALIDATION_DIR / "static_validation_report.json", report)
    runtime_report = runtime_preflight(installed_root, clean_root)
    write_json(VALIDATION_DIR / "runtime_preflight_report.json", runtime_report)
    write_readme(report, runtime_report)
    write_inventory()
    print(
        json.dumps(
            {
                "status": "pass",
                "static_packet_count": 116,
                "extra16_packet_count": 16,
                "packet_tree_sha256": report["packet_tree_sha256"],
                "runtime_preflight_status": runtime_report["status"],
                "semantic_category_counts": semantic_index["category_counts"],
                "slot_count": slot_ledger["record_slot_count"],
                "draft_input_freeze_sha256": load_json(DRAFT_INPUT_FREEZE)["freeze_sha256"],
                "work_root": str(WORK_ROOT),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
