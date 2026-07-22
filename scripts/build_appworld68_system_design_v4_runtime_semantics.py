#!/usr/bin/env python3
"""Freeze the AppWorld-68 checklist bundle with exact released runtime semantics.

This source-only builder reads only the already frozen v3 checklist/case sources and
the pinned official AppWorld commit snapshot.  It must run before the score-package
builder is allowed to inspect any retained execution record.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/appworld_test_normal_68_system_design_v3_gpt54_high_v1"
RUNTIME = ROOT / "experiments/appworld_evaluator_runtime_0.2.0.dev0_a072b7a_v2_semantic_closure"
OUTPUT = ROOT / "experiments/appworld_test_normal_68_system_design_v4_runtime_semantics_gpt54_high_v1"
EXPECTED_IDS_SHA256 = "2b54ce295ac44589ff9ceb689ea52daf69c64dfb0c76118db34af2b3e1da7c96"
EXPECTED_RUNTIME_COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
RUNTIME_POINTERS = (
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


class BuildError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_obj(value: Any) -> str:
    return sha_bytes(canonical(value))


def yaml_bytes(value: Any) -> bytes:
    run = subprocess.run(
        ["yq", "-P", "-o=yaml", ".", "-"], input=json_bytes(value),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if run.returncode:
        raise BuildError(run.stderr.decode(errors="replace"))
    return run.stdout


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_inventory() -> tuple[dict[str, Any], list[str]]:
    manifest = load_json(RUNTIME / "SOURCE_MANIFEST.json")
    if manifest.get("commit") != EXPECTED_RUNTIME_COMMIT or manifest.get("file_count") != 12:
        raise BuildError("runtime semantic closure identity drift")
    paths: list[str] = []
    for entry in manifest.get("files", []):
        relative = entry.get("path")
        if not isinstance(relative, str):
            raise BuildError("runtime manifest path is malformed")
        source = RUNTIME.joinpath(*PurePosixPath(relative).parts)
        if not source.is_file() or sha_file(source) != entry.get("sha256"):
            raise BuildError(f"runtime source drift: {relative}")
        paths.append(relative)
    if manifest.get("files_sha256") != sha_obj(manifest["files"]):
        raise BuildError("runtime aggregate hash drift")
    actual = sorted(p.relative_to(RUNTIME).as_posix() for p in RUNTIME.rglob("*") if p.is_file())
    if actual != sorted(["SOURCE_MANIFEST.json", *paths]):
        raise BuildError("runtime tree is not closed by its manifest")
    return manifest, paths


def append_support(item: Any, label: str) -> None:
    if not isinstance(item, dict) or not isinstance(item.get("support"), list):
        raise BuildError(f"missing support list: {label}")
    for pointer in RUNTIME_POINTERS:
        if pointer not in item["support"]:
            item["support"].append(pointer)


def amend_checklist(original: dict[str, Any]) -> dict[str, Any]:
    repaired = copy.deepcopy(original)
    native = repaired.get("native")
    if not isinstance(native, dict):
        raise BuildError("native checklist missing")
    for field in ("benchmark_success", "checked_by"):
        append_support(native.get(field), f"native.{field}")
    for field in ("decisive_artifacts", "success_if", "fail_if", "undecided_if"):
        values = native.get(field)
        if not isinstance(values, list):
            raise BuildError(f"native.{field} is not a list")
        for index, item in enumerate(values):
            append_support(item, f"native.{field}[{index}]")
    if repaired.get("stronger") != original.get("stronger"):
        raise BuildError("stronger checklist changed")
    return repaired


def strip_native_support(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: strip_native_support(v) for k, v in value.items() if k != "support"}
    if isinstance(value, list):
        return [strip_native_support(v) for v in value]
    return value


def runtime_appendix(manifest: dict[str, Any], paths: list[str]) -> str:
    lines = [
        "## Released Evaluator Runtime Semantic Closure (Pre-outcome Frozen)", "",
        "These are official source files from the exact AppWorld commit recorded by the run version receipt. They define transitive evaluator helper semantics; they contain no per-record outcome or released evaluator result.", "",
        f"- Repository: `{manifest['repository']}`", f"- Commit: `{manifest['commit']}`",
        f"- Code version: `{manifest['code_version']}`", f"- Runtime files SHA-256: `{manifest['files_sha256']}`", "",
    ]
    all_paths = ["SOURCE_MANIFEST.json", *paths]
    for relative in all_paths:
        packet_path = f"official/runtime/{relative}"
        source = RUNTIME / relative
        language = "json" if source.suffix == ".json" else "python"
        lines.extend([
            f"### `{packet_path}`", "", f"Source ref: `{manifest['repository']}/blob/{manifest['commit']}/{relative}`", "",
            f"```{language}", source.read_text(encoding="utf-8"), "```", "",
        ])
    return "\n".join(lines).rstrip() + "\n\n"


def amend_packet(packet: str, manifest: dict[str, Any], paths: list[str]) -> str:
    inventory_marker = "## Source Inventory\n"
    provenance_marker = "## Raw Source Provenance\n"
    if inventory_marker not in packet or provenance_marker not in packet:
        raise BuildError("case packet section markers missing")
    bullets = "".join(f"- `official/runtime/{p}`\n" for p in ["SOURCE_MANIFEST.json", *paths])
    packet = packet.replace(inventory_marker, inventory_marker + "\n" + bullets, 1)
    packet = packet.replace(provenance_marker, runtime_appendix(manifest, paths) + provenance_marker, 1)
    binding = (
        "\n- Exact runtime semantic closure: `official/runtime/SOURCE_MANIFEST.json` "
        f"(commit `{manifest['commit']}`, files SHA-256 `{manifest['files_sha256']}`)."
        " In particular, raw database mutation inventories are not substitutes for the released "
        "`ModelCollectionPair.changed_model_names/changed_records/changed_field_names` semantics.\n"
    )
    anchor = "### Released evaluator semantic binding\n"
    if anchor not in packet:
        raise BuildError("semantic binding section missing")
    return packet.replace(anchor, anchor + binding, 1)


def amend_raw_case(case_dir: Path, manifest: dict[str, Any], paths: list[str]) -> None:
    raw = case_dir / "raw_case"
    raw_manifest_path = case_dir / "raw_case_manifest.json"
    raw_manifest = load_json(raw_manifest_path)
    additions = ["official/runtime/SOURCE_MANIFEST.json", *[f"official/runtime/{p}" for p in paths]]
    for relative in additions:
        source_relative = relative.removeprefix("official/runtime/")
        source = RUNTIME / source_relative
        destination = raw.joinpath(*PurePosixPath(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        for field in ("packet_files", "copied_files", "official_files"):
            values = raw_manifest.setdefault(field, [])
            if relative not in values:
                values.append(relative)
                values.sort()
        raw_manifest.setdefault("file_sources", {})[relative] = (
            f"{manifest['repository']}/blob/{manifest['commit']}/{source_relative}"
        )
        raw_manifest.setdefault("sha256_per_file", {})[relative] = sha_file(destination)
    raw_manifest["released_evaluator_runtime"] = {
        "commit": manifest["commit"], "code_version": manifest["code_version"],
        "source_manifest_sha256": sha_file(RUNTIME / "SOURCE_MANIFEST.json"),
        "files_sha256": manifest["files_sha256"], "file_count": manifest["file_count"],
        "outcome_or_released_result_fields_present": False,
    }
    raw_manifest_path.write_bytes(json_bytes(raw_manifest))


def tree_records(root: Path, omit: set[str] | None = None) -> list[dict[str, Any]]:
    omitted = omit or set()
    records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in omitted:
            continue
        records.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": sha_file(path)})
    return records


def build(destination: Path) -> dict[str, Any]:
    if destination.exists():
        raise BuildError(f"refusing to overwrite: {destination}")
    manifest, paths = runtime_inventory()
    shutil.copytree(SOURCE, destination)
    ids = sorted(p.name for p in (SOURCE / "results").iterdir() if p.is_dir())
    if len(ids) != 68 or sha_obj(ids) != EXPECTED_IDS_SHA256:
        raise BuildError("frozen 68-case cohort drift")

    freeze_records = []
    checklist_changes = []
    for case_id in ids:
        original = load_json(SOURCE / "results" / case_id / "checklist.json")
        repaired = amend_checklist(original)
        if strip_native_support(original["native"]) != strip_native_support(repaired["native"]):
            raise BuildError(f"{case_id}: native criterion text changed")
        if original["stronger"] != repaired["stronger"]:
            raise BuildError(f"{case_id}: stronger condition changed")
        jbytes, ybytes = json_bytes(repaired), yaml_bytes(repaired)
        for base in (destination / "results" / case_id, destination / "claim_freeze/checklists" / case_id):
            (base / "checklist.json").write_bytes(jbytes)
            (base / "checklist.yaml").write_bytes(ybytes)
        packet_dir = destination / "case_packets/appworld" / case_id
        amend_raw_case(packet_dir, manifest, paths)
        packet_path = packet_dir / "case_packet.md"
        packet_path.write_text(amend_packet(packet_path.read_text(encoding="utf-8"), manifest, paths), encoding="utf-8")
        freeze_records.append({
            "case_unit_id": case_id, "checklist_json_sha256": sha_bytes(jbytes),
            "checklist_yaml_sha256": sha_bytes(ybytes), "case_packet_sha256": sha_file(packet_path),
        })
        checklist_changes.append({
            "case_unit_id": case_id,
            "source_checklist_json_sha256": sha_file(SOURCE / "results" / case_id / "checklist.json"),
            "frozen_checklist_json_sha256": sha_bytes(jbytes),
            "native_non_support_content_unchanged": True, "stronger_object_unchanged": True,
        })

    freeze = {
        "schema_version": "appworld_pre_outcome_checklist_freeze.v3_runtime_semantics",
        "created_date": "2026-07-20", "case_count": 68,
        "lock_boundary": "Before access to agent outcomes, per-record released evaluator labels, or component evaluator results.",
        "runtime_semantic_lock": {
            "repository": manifest["repository"], "commit": manifest["commit"],
            "code_version": manifest["code_version"], "source_manifest_sha256": sha_file(RUNTIME / "SOURCE_MANIFEST.json"),
            "files_sha256": manifest["files_sha256"], "file_count": manifest["file_count"],
        },
        "records": freeze_records, "records_sha256": sha_obj(freeze_records),
        "outcome_or_released_result_inputs_read": [],
    }
    (destination / "claim_freeze/freeze_manifest.json").write_bytes(json_bytes(freeze))
    experiment = load_json(destination / "experiment_manifest.json")
    experiment.update({
        "schema_version": "appworld_test_normal_68_system_design_v4_runtime_semantics.v1",
        "status": "source_only_runtime_semantics_amended_and_refrozen",
        "created_date": "2026-07-20",
        "runtime_semantic_lock": freeze["runtime_semantic_lock"],
        "v4_amendment": {
            "source_bundle": SOURCE.relative_to(ROOT).as_posix(),
            "native_criterion_text_changed_case_count": 0,
            "native_official_support_amended_case_count": 68,
            "stronger_object_changed_case_count": 0,
            "packet_runtime_source_closure_added_case_count": 68,
            "outcome_or_released_result_inputs_read": [],
        },
    })
    (destination / "experiment_manifest.json").write_bytes(json_bytes(experiment))
    readme = destination / "README.md"
    readme.write_text(
        "# AppWorld test_normal-68 system-design-v4 runtime-semantic freeze\n\n"
        "This pre-outcome bundle preserves every v3 native rule and every stronger object, while binding native support to the exact official AppWorld evaluator runtime source closure at commit `a072b7a86e7c1d5b1d7175659d750ebb9b79f10a`. No execution outcome, released label, or component evaluator output is an input.\n\n"
        + readme.read_text(encoding="utf-8"), encoding="utf-8",
    )
    indexed = tree_records(destination, {"repair_manifest.json"})
    repair = {
        "schema_version": "appworld_checklist_runtime_semantics_repair.v1",
        "created_date": "2026-07-20", "case_count": 68,
        "source_bundle": SOURCE.relative_to(ROOT).as_posix(),
        "runtime_source": freeze["runtime_semantic_lock"],
        "checklist_changes": checklist_changes,
        "validation": {
            "pre_outcome_source_only": True, "native_non_support_content_unchanged_case_count": 68,
            "stronger_object_unchanged_case_count": 68, "packet_draft_exact_projection_case_count": 68,
            "outcome_or_released_result_inputs_read": [],
        },
        "file_count_excluding_this_manifest": len(indexed), "files": indexed,
        "files_sha256": sha_obj(indexed),
    }
    (destination / "repair_manifest.json").write_bytes(json_bytes(repair))
    return repair


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output == ROOT or ROOT in output.parents and output == ROOT / "experiments":
        raise BuildError("unsafe broad output root")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent)) / output.name
    try:
        result = build(stage)
        os.replace(stage, output)
    finally:
        if stage.parent.exists():
            shutil.rmtree(stage.parent, ignore_errors=True)
    print(json.dumps({"status": "PASS", "output_root": str(output), "files_sha256": result["files_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BuildError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=os.sys.stderr)
        raise SystemExit(2)
