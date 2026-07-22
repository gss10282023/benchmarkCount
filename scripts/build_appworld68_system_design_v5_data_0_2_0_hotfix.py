#!/usr/bin/env python3
"""Build a versioned AppWorld-68 source/checklist hotfix from official data 0.2.0.

The builder reads only the frozen v4 source bundle and the independently recovered
official AppWorld ``data-0.2.0.bundle`` task projection.  It never reads execution
records, released labels, component evaluator outputs, or score outputs.  The v4
namespace remains immutable; this script writes a new v5 namespace.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evidence_system.contracts.appworld_checklist_semantics import (  # noqa: E402
    APPWORLD_ALL_TESTS_MARKER,
    appworld_benchmark_success_text,
    appworld_registered_test_fail_text,
    appworld_registered_test_success_text,
)
from evidence_system.contracts.case_packets import (  # noqa: E402
    _appworld_registered_test_registry,
    load_frozen_appworld_evaluator_semantics,
    render_case_packet,
)


SOURCE = (
    ROOT
    / "experiments"
    / "appworld_test_normal_68_system_design_v4_runtime_semantics_gpt54_high_v1"
)
OFFICIAL = (
    ROOT
    / "transfer"
    / "appworld68_official_task_sources_0.2.0_a072b7a"
    / "data"
)
OFFICIAL_BUNDLE = ROOT / "transfer" / "appworld_official_data-0.2.0.bundle"
SELECTION_ARCHIVE = (
    ROOT / "transfer" / "appworld68_task_sources_0.2.0_a072b7a.tar.gz"
)
OUTPUT = (
    ROOT
    / "experiments"
    / "appworld_test_normal_68_system_design_v5_data_0_2_0_hotfix_gpt54_high_v1"
)
V3_BUILDER = ROOT / "scripts/build_appworld68_system_design_v3.py"

EXPECTED_CASE_IDS_SHA256 = (
    "2b54ce295ac44589ff9ceb689ea52daf69c64dfb0c76118db34af2b3e1da7c96"
)
EXPECTED_DATA_BUNDLE_SHA256 = (
    "c9299e6cafe92bce4592a3c117c047c973d1554a667c21dd81537e78ab2f532e"
)
EXPECTED_SELECTION_ARCHIVE_SHA256 = (
    "fdcbd0d91f380043bf315bc1e7960643c1d8cffe9fe81bf3e1f7d35f2a38de59"
)
EXPECTED_RUNTIME_COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
EXPECTED_RUNTIME_CODE_VERSION = "0.2.0.dev0:a072b7a"
EXPECTED_RUNTIME_FILES_SHA256 = (
    "71decd1269ed052e45ca2a0eb1ca540295c5b5fcb40238b9a6feae7b05e83dbe"
)
EXPECTED_DATA_VERSION = "0.2.0"
EXPECTED_V4_DATA_VERSION = "0.1.0"
EXPECTED_CASE_COUNT = 68
EXPECTED_TEST_COUNT = 469
SEMANTICALLY_CHANGED_CASES = {"bde252e_2"}
TASK_RELATIVE_FILES = (
    "dbs/admin.jsonl",
    "dbs/amazon.jsonl",
    "dbs/api_docs.jsonl",
    "dbs/file_system.jsonl",
    "dbs/gmail.jsonl",
    "dbs/phone.jsonl",
    "dbs/simple_note.jsonl",
    "dbs/splitwise.jsonl",
    "dbs/spotify.jsonl",
    "dbs/supervisor.jsonl",
    "dbs/todoist.jsonl",
    "dbs/venmo.jsonl",
    "ground_truth/answer.json",
    "ground_truth/evaluation.py",
    "ground_truth/metadata.json",
    "ground_truth/private_data.json",
    "ground_truth/public_data.json",
    "ground_truth/test_data.json",
    "specs.json",
)
YAML_SOURCE_LOCK_HEADER = (
    "# AUTHORITATIVE APPWORLD SOURCE LOCK: data_version=0.2.0; db_version=0.2.0\n"
    "# Official task-local source: data-0.2.0.bundle; runtime commit=a072b7a86e7c1d5b1d7175659d750ebb9b79f10a\n"
)


class BuildError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_obj(value: Any) -> str:
    return sha_bytes(canonical(value))


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"could not read JSON {path}: {exc}") from exc


def import_v3_builder() -> Any:
    spec = importlib.util.spec_from_file_location("appworld_v3_builder", V3_BUILDER)
    if spec is None or spec.loader is None:
        raise BuildError("could not load v3 builder helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_records(root: Path, *, omit: set[str] | None = None) -> list[dict[str, Any]]:
    omitted = omit or set()
    records: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in omitted:
            continue
        records.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha_file(path),
            }
        )
    return records


def task_records(task_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": relative,
            "size_bytes": (task_root / relative).stat().st_size,
            "sha256": sha_file(task_root / relative),
        }
        for relative in TASK_RELATIVE_FILES
    ]


def ast_without_imports(text: str) -> str:
    tree = ast.parse(text)
    tree.body = [
        node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    return ast.dump(tree, include_attributes=False)


def validate_source_lock() -> tuple[list[str], dict[str, Any]]:
    if not SOURCE.is_dir() or not OFFICIAL.is_dir():
        raise BuildError("v4 source bundle or official 0.2.0 projection is missing")
    if sha_file(OFFICIAL_BUNDLE) != EXPECTED_DATA_BUNDLE_SHA256:
        raise BuildError("official encrypted data-0.2.0.bundle hash drift")
    if sha_file(SELECTION_ARCHIVE) != EXPECTED_SELECTION_ARCHIVE_SHA256:
        raise BuildError("official 68-case selection archive hash drift")
    if OFFICIAL.joinpath("version.txt").read_text(encoding="utf-8").strip() != EXPECTED_DATA_VERSION:
        raise BuildError("official data version is not 0.2.0")

    experiment = load_json(SOURCE / "experiment_manifest.json")
    ids = list(experiment.get("scope", {}).get("case_ids", []))
    if (
        len(ids) != EXPECTED_CASE_COUNT
        or len(set(ids)) != EXPECTED_CASE_COUNT
        or sha_obj(ids) != EXPECTED_CASE_IDS_SHA256
    ):
        raise BuildError("v4 case cohort drift")
    dataset_ids = set(
        OFFICIAL.joinpath("datasets/test_normal.txt").read_text(encoding="utf-8").split()
    )
    if not set(ids) <= dataset_ids:
        raise BuildError("the 68-case cohort is not contained in official 0.2.0 test_normal")

    semantic_changes: set[str] = set()
    diff_records: list[dict[str, Any]] = []
    for case_id in ids:
        old = SOURCE / "case_packets/appworld" / case_id / "raw_case/official"
        new = OFFICIAL / "tasks" / case_id
        actual = sorted(
            path.relative_to(new).as_posix()
            for path in new.rglob("*")
            if path.is_file()
        )
        if actual != sorted(TASK_RELATIVE_FILES):
            raise BuildError(f"{case_id}: official 0.2.0 task inventory drift")

        old_specs = load_json(old / "specs.json")
        new_specs = load_json(new / "specs.json")
        old_db_version = old_specs.pop("db_version", None)
        new_db_version = new_specs.pop("db_version", None)
        if (
            old_db_version != EXPECTED_V4_DATA_VERSION
            or new_db_version != EXPECTED_DATA_VERSION
            or old_specs != new_specs
        ):
            raise BuildError(f"{case_id}: specs differ beyond the expected db_version correction")

        old_metadata = load_json(old / "ground_truth/metadata.json")
        new_metadata = load_json(new / "ground_truth/metadata.json")
        old_mode = old_metadata.pop("mode", None)
        new_mode = new_metadata.pop("mode", None)
        if old_mode != "full" or new_mode != "minimal" or old_metadata != new_metadata:
            raise BuildError(f"{case_id}: metadata differ beyond full-to-minimal release mode")

        old_eval = (old / "ground_truth/evaluation.py").read_text(encoding="utf-8")
        new_eval = (new / "ground_truth/evaluation.py").read_text(encoding="utf-8")
        if ast_without_imports(old_eval) != ast_without_imports(new_eval):
            semantic_changes.add(case_id)

        changed = [
            relative
            for relative in TASK_RELATIVE_FILES
            if (old / relative).read_bytes() != (new / relative).read_bytes()
        ]
        expected_changed = {
            "specs.json",
            "ground_truth/evaluation.py",
            "ground_truth/metadata.json",
        }
        if case_id == "bde252e_2":
            expected_changed.add("ground_truth/test_data.json")
        if set(changed) != expected_changed:
            raise BuildError(f"{case_id}: unexpected 0.1.0-to-0.2.0 task file diff: {changed}")
        diff_records.append(
            {
                "case_unit_id": case_id,
                "changed_files": changed,
                "native_evaluator_non_import_semantics_changed": case_id
                in SEMANTICALLY_CHANGED_CASES,
            }
        )

    if semantic_changes != SEMANTICALLY_CHANGED_CASES:
        raise BuildError(
            "unexpected non-import evaluator semantic-change set: "
            + ", ".join(sorted(semantic_changes))
        )

    runtime = experiment.get("runtime_semantic_lock")
    if not isinstance(runtime, dict) or (
        runtime.get("commit") != EXPECTED_RUNTIME_COMMIT
        or runtime.get("code_version") != EXPECTED_RUNTIME_CODE_VERSION
        or runtime.get("files_sha256") != EXPECTED_RUNTIME_FILES_SHA256
    ):
        raise BuildError("v4 evaluator runtime lock drift")

    source_lock = {
        "schema_version": "appworld_official_task_source_lock.v1",
        "benchmark": "AppWorld",
        "dataset_name": "test_normal",
        "data_version": EXPECTED_DATA_VERSION,
        "db_version": EXPECTED_DATA_VERSION,
        "runtime_code_version": EXPECTED_RUNTIME_CODE_VERSION,
        "runtime_commit": EXPECTED_RUNTIME_COMMIT,
        "official_data_bundle_url": (
            "https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.2.0.bundle"
        ),
        "official_data_bundle_sha256": EXPECTED_DATA_BUNDLE_SHA256,
        "selected_task_source_archive_sha256": EXPECTED_SELECTION_ARCHIVE_SHA256,
        "case_count": EXPECTED_CASE_COUNT,
        "case_ids_sha256": EXPECTED_CASE_IDS_SHA256,
        "task_files_per_case": len(TASK_RELATIVE_FILES),
        "native_evaluator_non_import_semantics_changed_case_ids": sorted(
            SEMANTICALLY_CHANGED_CASES
        ),
        "construction_inputs": [
            SOURCE.relative_to(ROOT).as_posix(),
            OFFICIAL.relative_to(ROOT).as_posix(),
            OFFICIAL_BUNDLE.relative_to(ROOT).as_posix(),
            SELECTION_ARCHIVE.relative_to(ROOT).as_posix(),
        ],
        "outcome_or_released_result_inputs_read": [],
        "diff_records": diff_records,
    }
    return ids, source_lock


def update_checklist(
    original: dict[str, Any],
    *,
    case_id: str,
    instruction: str,
    registered_tests: list[dict[str, Any]],
) -> dict[str, Any]:
    checklist = copy.deepcopy(original)
    native = checklist.get("native")
    if not isinstance(native, dict):
        raise BuildError(f"{case_id}: native checklist missing")
    user_goal = native.get("user_goal")
    if not isinstance(user_goal, dict):
        raise BuildError(f"{case_id}: native.user_goal missing")
    user_goal["text"] = instruction
    user_goal["rationale"] = (
        "This is the exact frozen official AppWorld 0.2.0 instruction; the "
        "authoritative data_version and db_version are both 0.2.0."
    )

    markers = [str(item["marker"]) for item in registered_tests]
    native["benchmark_success"]["text"] = appworld_benchmark_success_text(markers)
    success_if = native.get("success_if")
    fail_if = native.get("fail_if")
    if (
        not isinstance(success_if, list)
        or not isinstance(fail_if, list)
        or len(success_if) != len(registered_tests)
        or len(fail_if) != len(registered_tests)
    ):
        raise BuildError(f"{case_id}: checklist registered-test cardinality drift")
    for index, record in enumerate(registered_tests):
        requirement = str(record["requirement"])
        marker = str(record["marker"])
        success_if[index]["text"] = appworld_registered_test_success_text(
            marker, requirement
        )
        fail_if[index]["text"] = appworld_registered_test_fail_text(marker, requirement)
    return checklist


def write_checklist_pair(base: Path, checklist: dict[str, Any], v3: Any) -> tuple[str, str]:
    json_payload = json_bytes(checklist)
    yaml_payload = YAML_SOURCE_LOCK_HEADER.encode("utf-8") + v3.yaml_bytes(checklist)
    base.mkdir(parents=True, exist_ok=True)
    (base / "checklist.json").write_bytes(json_payload)
    (base / "checklist.yaml").write_bytes(yaml_payload)
    roundtrip = subprocess.run(
        ["yq", "-o=json", ".", "-"],
        input=yaml_payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if roundtrip.returncode != 0 or json.loads(roundtrip.stdout) != checklist:
        raise BuildError(f"checklist YAML round-trip drift: {base}")
    return sha_bytes(json_payload), sha_bytes(yaml_payload)


def replace_task_sources(raw_case: Path, official_task: Path) -> None:
    official_root = raw_case / "official"
    for relative in ("dbs", "ground_truth"):
        target = official_root / relative
        if target.exists():
            shutil.rmtree(target)
    specs = official_root / "specs.json"
    if specs.exists():
        specs.unlink()
    for source in sorted(path for path in official_task.rglob("*") if path.is_file()):
        relative = source.relative_to(official_task)
        destination = official_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def update_raw_manifest(
    manifest: dict[str, Any],
    *,
    case_id: str,
    raw_case: Path,
    official_task: Path,
    source_lock: dict[str, Any],
) -> dict[str, Any]:
    updated = copy.deepcopy(manifest)
    records = task_records(official_task)
    task_tree_sha = sha_obj(records)
    versioned_ref = f"appworld://data/0.2.0/test_normal/{case_id}"
    bundle_url = str(source_lock["official_data_bundle_url"])
    for relative in TASK_RELATIVE_FILES:
        packet_relative = f"official/{relative}"
        updated.setdefault("sha256_per_file", {})[packet_relative] = sha_file(
            raw_case / packet_relative
        )
        updated.setdefault("file_sources", {})[packet_relative] = (
            f"{bundle_url}#data/tasks/{case_id}/{relative}"
        )

    actual_files = sorted(
        path.relative_to(raw_case).as_posix()
        for path in raw_case.rglob("*")
        if path.is_file()
    )
    for field in ("copied_files", "official_files", "packet_files"):
        updated[field] = actual_files
    updated["derived_files"] = []
    updated["source_ref"] = versioned_ref
    updated["source_refs"] = [versioned_ref, bundle_url]
    updated["task_dir"] = (
        OFFICIAL.joinpath("tasks", case_id).relative_to(ROOT).as_posix()
    )
    updated["task_tree_sha256"] = f"sha256:{task_tree_sha}"
    updated["catalog_item_sha256"] = f"sha256:{sha_obj({'case_unit_id': case_id, 'files': records})}"
    updated["task_source_lock"] = {
        key: source_lock[key]
        for key in (
            "data_version",
            "db_version",
            "runtime_code_version",
            "runtime_commit",
            "official_data_bundle_url",
            "official_data_bundle_sha256",
            "selected_task_source_archive_sha256",
        )
    }
    updated["task_source_lock"].update(
        {
            "case_unit_id": case_id,
            "task_file_count": len(records),
            "task_files_sha256": task_tree_sha,
            "native_evaluator_non_import_semantics_changed_from_v4": (
                case_id in SEMANTICALLY_CHANGED_CASES
            ),
            "outcome_or_released_result_inputs_read": [],
        }
    )
    updated["sha256_per_file"] = {
        relative: sha_file(raw_case / relative) for relative in actual_files
    }
    updated["file_sources"] = {
        relative: updated["file_sources"][relative] for relative in actual_files
    }
    return updated


def source_lock_banner(case_lock: dict[str, Any]) -> str:
    return "\n".join(
        [
            "## Authoritative AppWorld 0.2.0 Source Lock",
            "",
            "This packet is bound to the official task-local sources that match the retained benchmark execution version.",
            "",
            "- data_version: `0.2.0`",
            "- db_version: `0.2.0`",
            f"- runtime code version: `{case_lock['runtime_code_version']}`",
            f"- runtime commit: `{case_lock['runtime_commit']}`",
            f"- official encrypted data bundle SHA-256: `{case_lock['official_data_bundle_sha256']}`",
            f"- this case's 19-file task-source closure SHA-256: `{case_lock['task_files_sha256']}`",
            "- authority rule: the versioned `official/*` files embedded below are authoritative; the superseded v4/0.1.0 snapshot is not part of this packet.",
        ]
    )


def build(destination: Path) -> dict[str, Any]:
    if destination.exists():
        raise BuildError(f"refusing to overwrite: {destination}")
    ids, source_lock = validate_source_lock()
    v3 = import_v3_builder()
    evaluator_semantics = load_frozen_appworld_evaluator_semantics()

    shutil.copytree(SOURCE, destination)
    (destination / "task_source_lock.json").write_bytes(json_bytes(source_lock))

    visibility = load_json(SOURCE / "artifact_visibility_contract.json")
    visibility["authoritative_appworld_source_lock"] = {
        key: source_lock[key]
        for key in (
            "data_version",
            "db_version",
            "runtime_code_version",
            "runtime_commit",
            "official_data_bundle_sha256",
            "selected_task_source_archive_sha256",
        )
    }
    visibility["formal_semantics_binding"]["scope_note"] = (
        "The descriptor pins the released AppWorld runtime commit and evaluator.py "
        "source hash. Each case packet additionally freezes the exact official "
        "AppWorld 0.2.0 task-local evaluator, targets, metadata, specs, and initial-state "
        "database diffs."
    )
    (destination / "artifact_visibility_contract.json").write_bytes(json_bytes(visibility))

    checklists: dict[str, dict[str, Any]] = {}
    native_registries: dict[str, dict[str, Any]] = {}
    case_locks: dict[str, dict[str, Any]] = {}
    checklist_semantic_changes: list[str] = []

    for case_id in ids:
        packet_dir = destination / "case_packets/appworld" / case_id
        raw_case = packet_dir / "raw_case"
        official_task = OFFICIAL / "tasks" / case_id
        replace_task_sources(raw_case, official_task)
        raw_manifest_path = packet_dir / "raw_case_manifest.json"
        raw_manifest = update_raw_manifest(
            load_json(raw_manifest_path),
            case_id=case_id,
            raw_case=raw_case,
            official_task=official_task,
            source_lock=source_lock,
        )
        raw_manifest_path.write_bytes(json_bytes(raw_manifest))
        case_locks[case_id] = raw_manifest["task_source_lock"]

        registered_tests = _appworld_registered_test_registry(raw_case)
        original = load_json(SOURCE / "results" / case_id / "checklist.json")
        specs = load_json(official_task / "specs.json")
        checklist = update_checklist(
            original,
            case_id=case_id,
            instruction=specs["instruction"],
            registered_tests=registered_tests,
        )
        v3.validate_repaired_checklist(checklist, case_id=case_id)
        if checklist["stronger"] != original["stronger"]:
            raise BuildError(f"{case_id}: stronger checklist changed")
        if checklist["native"] != original["native"]:
            checklist_semantic_changes.append(case_id)
        checklists[case_id] = checklist
        native_registries[case_id] = {
            "schema_version": v3.PACKET_NATIVE_SCHEMA,
            "case_unit_id": case_id,
            "all_tests_marker": APPWORLD_ALL_TESTS_MARKER,
            "registered_tests": registered_tests,
            "registered_test_count": len(registered_tests),
            "native_verdict_rule": v3.NATIVE_SFU_RULE,
            "required_native": checklist["native"],
        }

    total_tests = sum(
        registry["registered_test_count"] for registry in native_registries.values()
    )
    if total_tests != EXPECTED_TEST_COUNT:
        raise BuildError(f"registered-test total drift: {total_tests}")

    stronger_registry = load_json(SOURCE / "stronger_registry.json")
    stronger_registry.update(
        {
            "schema_version": "appworld_stronger_gap_registry.v5_data_0_2_0_hotfix",
            "review_date": "2026-07-22",
            "review_mode": "deterministic_official_0_2_0_task_source_hotfix",
            "source_lock": {
                key: source_lock[key]
                for key in (
                    "data_version",
                    "db_version",
                    "runtime_code_version",
                    "runtime_commit",
                    "official_data_bundle_sha256",
                    "selected_task_source_archive_sha256",
                )
            },
            "outcome_or_released_result_inputs_read": [],
        }
    )
    stronger_cases = {
        item["case_unit_id"]: item for item in stronger_registry.get("cases", [])
    }
    if set(stronger_cases) != set(ids):
        raise BuildError("stronger-registry case closure drift")
    for case_id in ids:
        stronger_cases[case_id]["native_registry_canonical_json_sha256"] = sha_obj(
            native_registries[case_id]
        )
    stronger_bytes = json_bytes(stronger_registry)
    stronger_sha = sha_bytes(stronger_bytes)
    stronger_canonical_sha = sha_obj(stronger_registry)
    (destination / "stronger_registry.json").write_bytes(stronger_bytes)

    freeze_records: list[dict[str, Any]] = []
    repair_records: list[dict[str, Any]] = []
    for case_id in ids:
        packet_dir = destination / "case_packets/appworld" / case_id
        raw_case = packet_dir / "raw_case"
        raw_manifest = load_json(packet_dir / "raw_case_manifest.json")
        checklist = checklists[case_id]

        base_packet = render_case_packet(
            # Render only the generic source inventory/tail here.  The AppWorld
            # native header is replaced below with the v5 registry.  Using a
            # temporary domain avoids consulting the intentionally immutable v4
            # stronger-gap source-basis registry while materializing the new raw
            # source hashes.
            domain="appworld_source_hotfix",
            case_unit_id=case_id,
            task_id=case_id,
            raw_case_dir=raw_case,
            raw_case_manifest=raw_manifest,
        )
        marker = "## Frozen AppWorld Native Scoring Semantics (Mandatory)"
        base_packet = base_packet.replace(
            "- domain: `appworld_source_hotfix`", "- domain: `appworld`", 1
        )
        inventory_marker = "## Source Inventory"
        if inventory_marker not in base_packet:
            raise BuildError(f"{case_id}: base packet source inventory marker missing")
        base_packet = base_packet.replace(
            inventory_marker,
            source_lock_banner(case_locks[case_id])
            + "\n\n"
            + marker
            + "\n\nThis placeholder is replaced by the frozen v5 checklist contract.\n\n"
            + inventory_marker,
            1,
        )
        header = v3.render_packet_header(
            native_registry=native_registries[case_id],
            case_entry=stronger_cases[case_id],
            registry_canonical_json_sha256=stronger_canonical_sha,
            registry_file_sha256=stronger_sha,
            visibility=visibility,
            evaluator_semantics=evaluator_semantics,
        )
        header = header.replace(
            "This contract and the case-specific checklist are locked before access "
            "to any agent outcome, per-record released evaluator label, or component "
            "evaluator result.",
            "This v5 correction is derived only from the independently recovered "
            "official AppWorld 0.2.0 source bundle and is frozen before any subsequent "
            "scorer or audit invocation. It does not rewrite or relabel the historical "
            "v4 inputs or scores.",
            1,
        )
        packet = v3.replace_packet_contract(base_packet, header)
        packet_path = packet_dir / "case_packet.md"
        packet_path.write_text(packet, encoding="utf-8")

        result_json_sha, result_yaml_sha = write_checklist_pair(
            destination / "results" / case_id, checklist, v3
        )
        freeze_json_sha, freeze_yaml_sha = write_checklist_pair(
            destination / "claim_freeze/checklists" / case_id, checklist, v3
        )
        if (result_json_sha, result_yaml_sha) != (freeze_json_sha, freeze_yaml_sha):
            raise BuildError(f"{case_id}: result/freeze checklist projection drift")

        original_checklist = load_json(SOURCE / "results" / case_id / "checklist.json")
        record = {
            "schema_version": "appworld_checklist_source_version_hotfix_record.v1",
            "case_unit_id": case_id,
            "dataset_name": "test_normal",
            "source_bundle": SOURCE.relative_to(ROOT).as_posix(),
            "source_checklist_json_sha256": sha_file(
                SOURCE / "results" / case_id / "checklist.json"
            ),
            "output_checklist_json_sha256": result_json_sha,
            "output_checklist_yaml_sha256": result_yaml_sha,
            "output_case_packet_sha256": sha_file(packet_path),
            "output_raw_case_manifest_sha256": sha_file(
                packet_dir / "raw_case_manifest.json"
            ),
            "task_source_lock": case_locks[case_id],
            "native_object_changed_from_v4": checklist["native"]
            != original_checklist["native"],
            "native_evaluator_non_import_semantics_changed_from_v4": case_id
            in SEMANTICALLY_CHANGED_CASES,
            "stronger_object_unchanged_from_v4": True,
            "outcome_or_released_result_inputs_read": [],
        }
        (destination / "results" / case_id / "repair_record.json").write_bytes(
            json_bytes(record)
        )
        repair_records.append(record)
        freeze_records.append(
            {
                "case_unit_id": case_id,
                "checklist_json_sha256": result_json_sha,
                "checklist_yaml_sha256": result_yaml_sha,
                "case_packet_sha256": sha_file(packet_path),
                "raw_case_manifest_sha256": sha_file(
                    packet_dir / "raw_case_manifest.json"
                ),
                "task_files_sha256": case_locks[case_id]["task_files_sha256"],
                "native_evaluator_non_import_semantics_changed_from_v4": case_id
                in SEMANTICALLY_CHANGED_CASES,
            }
        )

    freeze = {
        "schema_version": "appworld_pre_score_checklist_freeze.v5_data_0_2_0_hotfix",
        "created_date": "2026-07-22",
        "case_count": EXPECTED_CASE_COUNT,
        "registered_test_count": total_tests,
        "lock_boundary": (
            "This new namespace is the source-corrected input for subsequent scoring "
            "and audit. It does not mutate or relabel the historical v4 inputs or scores."
        ),
        "task_source_lock": {
            key: source_lock[key]
            for key in (
                "data_version",
                "db_version",
                "runtime_code_version",
                "runtime_commit",
                "official_data_bundle_sha256",
                "selected_task_source_archive_sha256",
            )
        },
        "records": freeze_records,
        "records_sha256": sha_obj(freeze_records),
        "native_evaluator_non_import_semantics_changed_case_ids": sorted(
            SEMANTICALLY_CHANGED_CASES
        ),
        "outcome_or_released_result_inputs_read": [],
    }
    (destination / "claim_freeze/freeze_manifest.json").write_bytes(json_bytes(freeze))

    experiment = load_json(SOURCE / "experiment_manifest.json")
    experiment.update(
        {
            "schema_version": "appworld_test_normal_68_system_design_v5_data_0_2_0_hotfix.v1",
            "status": "official_0_2_0_task_sources_corrected_and_refrozen",
            "created_date": "2026-07-22",
            "task_source_lock": freeze["task_source_lock"],
            "v5_amendment": {
                "source_bundle": SOURCE.relative_to(ROOT).as_posix(),
                "official_task_source": OFFICIAL.relative_to(ROOT).as_posix(),
                "case_count": EXPECTED_CASE_COUNT,
                "task_source_files_replaced_per_case": len(TASK_RELATIVE_FILES),
                "specs_db_version_corrected_case_count": EXPECTED_CASE_COUNT,
                "metadata_release_mode_corrected_case_count": EXPECTED_CASE_COUNT,
                "evaluator_import_only_change_case_count": EXPECTED_CASE_COUNT
                - len(SEMANTICALLY_CHANGED_CASES),
                "native_evaluator_semantics_changed_case_ids": sorted(
                    SEMANTICALLY_CHANGED_CASES
                ),
                "stronger_object_changed_case_count": 0,
                "historical_v4_namespace_mutated": False,
                "historical_v4_scores_relabelled": False,
                "outcome_or_released_result_inputs_read": [],
            },
        }
    )
    (destination / "experiment_manifest.json").write_bytes(json_bytes(experiment))

    readme = destination / "README.md"
    prior_readme = readme.read_text(encoding="utf-8")
    readme.write_text(
        "# AppWorld test_normal-68 system-design-v5 official data-0.2.0 source hotfix\n\n"
        "The authoritative task-local source and checklist binding in this namespace "
        "use AppWorld `data_version=0.2.0` and `db_version=0.2.0`, with runtime commit "
        f"`{EXPECTED_RUNTIME_COMMIT}`. The encrypted official data bundle SHA-256 is "
        f"`{EXPECTED_DATA_BUNDLE_SHA256}`. The v4 namespace and its historical scores "
        "remain unchanged.\n\n"
        "Across these 68 cases, 67 evaluators differ from the v4 copy only by import "
        "relocation. `bde252e_2` has one official registered-test semantic correction, "
        "which is reflected in its v5 checklist and packet. Stronger conditions are "
        "unchanged.\n\n"
        + prior_readme,
        encoding="utf-8",
    )

    indexed = tree_records(destination, omit={"repair_manifest.json"})
    repair = {
        "schema_version": "appworld_official_0_2_0_source_hotfix.v1",
        "created_date": "2026-07-22",
        "case_count": EXPECTED_CASE_COUNT,
        "registered_test_count": total_tests,
        "source_bundle": SOURCE.relative_to(ROOT).as_posix(),
        "task_source_lock": source_lock,
        "repair_records": repair_records,
        "validation": {
            "official_0_2_0_task_source_case_count": EXPECTED_CASE_COUNT,
            "official_0_2_0_task_files_per_case": len(TASK_RELATIVE_FILES),
            "native_evaluator_non_import_semantics_changed_case_ids": sorted(
                SEMANTICALLY_CHANGED_CASES
            ),
            "stronger_object_unchanged_case_count": EXPECTED_CASE_COUNT,
            "historical_v4_namespace_mutated": False,
            "outcome_or_released_result_inputs_read": [],
        },
        "file_count_excluding_this_manifest": len(indexed),
        "files": indexed,
        "files_sha256": sha_obj(indexed),
    }
    (destination / "repair_manifest.json").write_bytes(json_bytes(repair))
    return repair


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output == ROOT or output == ROOT / "experiments":
        raise BuildError("unsafe broad output root")
    if output.exists():
        raise BuildError(f"refusing to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage_parent = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent)
    )
    stage = stage_parent / output.name
    try:
        repair = build(stage)
        os.replace(stage, output)
    finally:
        if stage_parent.exists():
            shutil.rmtree(stage_parent, ignore_errors=True)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output_root": str(output),
                "files_sha256": repair["files_sha256"],
                "case_count": repair["case_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BuildError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
