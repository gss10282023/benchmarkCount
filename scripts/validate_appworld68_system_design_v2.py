#!/usr/bin/env python3
"""Fail-closed validator for the AppWorld test_normal-68 system-design-v2 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / (
    "experiments/appworld_test_normal_68_system_design_v2_gpt54_high_v1"
)
SOURCE_ROOT = REPO_ROOT / (
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
    "/case_packets/appworld"
)
MARKER_RE = re.compile(r"^(\[appworld_stronger_gap_[0-9]{3}_([0-9a-f]{12})\])\s+")
LINE_RE = re.compile(r"^L([1-9][0-9]*)(?:-L([1-9][0-9]*))?$")
JSON_TOKEN_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)|\[([0-9]+)\]")


def fail(message: str) -> None:
    raise RuntimeError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_object(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def parse_json_block(section: str, label: str) -> dict[str, Any]:
    match = re.search(r"```json\n(.*?)\n```", section, flags=re.DOTALL)
    if match is None:
        fail(f"{label}: JSON block missing")
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        fail(f"{label}: JSON block must be an object")
    return value


def parse_packet(
    packet: str, case_id: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    visibility_start = packet.index("### Artifact visibility and phase separation")
    semantics_start = packet.index("### Released evaluator semantic binding")
    native_start = packet.index("### Machine-verifiable native registry")
    stronger_start = packet.index("### Machine-verifiable stronger registry")
    source_start = packet.index("## Source Inventory")
    visibility = parse_json_block(
        packet[visibility_start:semantics_start], f"{case_id}: visibility"
    )
    semantics = parse_json_block(
        packet[semantics_start:native_start], f"{case_id}: evaluator semantics"
    )
    native = parse_json_block(packet[native_start:stronger_start], f"{case_id}: native")
    stronger = parse_json_block(packet[stronger_start:source_start], f"{case_id}: stronger")
    return visibility, semantics, native, stronger


def yaml_as_json(path: Path) -> Any:
    completed = subprocess.run(
        ["yq", "-o=json", ".", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        fail(f"YAML parse failed for {path}: {completed.stderr.decode(errors='replace')}")
    return json.loads(completed.stdout)


def string_supports(checklist: dict[str, Any]) -> Iterable[str]:
    native = checklist["native"]
    for key in ("user_goal", "benchmark_success", "checked_by"):
        yield from native[key]["support"]
    for key in ("decisive_artifacts", "success_if", "fail_if", "undecided_if"):
        for item in native[key]:
            yield from item["support"]
    for condition in checklist["stronger"]["additional_conditions"]:
        yield from condition["support"]
        for artifact in condition["decisive_artifacts"]:
            yield from artifact["support"]


def validate_json_locator(path: Path, locator: str, case_id: str) -> None:
    if path.suffix == ".jsonl":
        fail(f"{case_id}: JSONL support must use an exact line range: {path}::{locator}")
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    if not locator.startswith("$"):
        fail(f"{case_id}: malformed JSON locator: {path}::{locator}")
    position = 1
    for match in JSON_TOKEN_RE.finditer(locator, position):
        if match.start() != position:
            fail(f"{case_id}: unsupported JSON locator syntax: {path}::{locator}")
        key, index = match.groups()
        if key is not None:
            if not isinstance(value, dict) or key not in value:
                fail(f"{case_id}: JSON support field missing: {path}::{locator}")
            value = value[key]
        else:
            offset = int(index)
            if not isinstance(value, list) or offset >= len(value):
                fail(f"{case_id}: JSON support index missing: {path}::{locator}")
            value = value[offset]
        position = match.end()
    if position != len(locator):
        fail(f"{case_id}: unsupported JSON locator tail: {path}::{locator}")


def validate_support(raw_case: Path, pointer: str, case_id: str) -> None:
    if "::" not in pointer:
        fail(f"{case_id}: support pointer lacks locator: {pointer}")
    relative, locator = pointer.split("::", 1)
    if "*" in relative or "?" in relative or "[" in relative:
        fail(f"{case_id}: support path must be an exact inventory path: {pointer}")
    if relative == "official/ground_truth/answer.json":
        fail(f"{case_id}: answer target is not an admissible checklist support pointer")
    candidates = [raw_case / relative]
    if not candidates or any(not path.is_file() for path in candidates):
        fail(f"{case_id}: support path missing: {pointer}")
    for path in candidates:
        line_match = LINE_RE.fullmatch(locator)
        if line_match:
            start = int(line_match.group(1))
            end = int(line_match.group(2) or start)
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if start > end or end > line_count:
                fail(
                    f"{case_id}: support line range {locator} exceeds {relative} "
                    f"({line_count} lines)"
                )
        elif locator == "evaluate":
            if "def evaluate(" not in path.read_text(encoding="utf-8"):
                fail(f"{case_id}: evaluator support target missing: {pointer}")
        elif locator.startswith("$"):
            validate_json_locator(path, locator, case_id)
        else:
            fail(f"{case_id}: unsupported support locator: {pointer}")


def validate_marker(condition: dict[str, Any], index: int, case_id: str) -> None:
    text = condition["text"]
    match = MARKER_RE.match(text)
    if match is None:
        fail(f"{case_id}: condition {index} marker missing")
    marker, observed_digest = match.groups()
    expected_prefix = f"[appworld_stronger_gap_{index:03d}_"
    if not marker.startswith(expected_prefix):
        fail(f"{case_id}: condition {index} marker index drift")
    markerless = dict(condition)
    markerless["text"] = text[match.end():]
    expected_digest = sha256_object(markerless)[:12]
    if observed_digest != expected_digest:
        fail(f"{case_id}: condition {index} marker digest drift")


def validate_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "repair_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_paths = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    )
    records = manifest["files"]
    if [item["path"] for item in records] != actual_paths:
        fail("repair manifest file inventory differs from output tree")
    for record in records:
        path = root / record["path"]
        if record["size_bytes"] != path.stat().st_size or record["sha256"] != sha256_file(path):
            fail(f"repair manifest hash/size mismatch: {record['path']}")
    if manifest["files_sha256"] != sha256_object(records):
        fail("repair manifest aggregate file hash mismatch")
    if manifest["file_count_excluding_this_manifest"] != len(records):
        fail("repair manifest file count mismatch")
    return manifest


def validate(root: Path) -> dict[str, Any]:
    source_module_root = str(REPO_ROOT / "src")
    if source_module_root not in sys.path:
        sys.path.insert(0, source_module_root)
    from evidence_system.contracts.appworld_support_pointers import (  # noqa: PLC0415
        official_pointer_resolves,
    )

    if not root.is_dir():
        fail(f"bundle root missing: {root}")
    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    if symlinks:
        fail(f"bundle contains symlinks: {symlinks[:3]}")
    manifest = validate_manifest(root)
    visibility_file = json.loads(
        (root / "artifact_visibility_contract.json").read_text(encoding="utf-8")
    )
    semantics_path = root / "frozen_semantics/appworld_evaluator_semantics.a072b7a8.json"
    semantics_file_sha = sha256_file(semantics_path)
    if semantics_file_sha != "f92952e8a35001848126397fc43f4b612ea607030c53deb783af57d93e624d9f":
        fail("frozen evaluator-semantics descriptor hash drift")
    evaluator_semantics = json.loads(semantics_path.read_text(encoding="utf-8"))
    registry_path = root / "stronger_registry.json"
    stronger_registry = json.loads(registry_path.read_text())
    registry_canonical_sha = sha256_object(stronger_registry)
    registry_file_sha = sha256_file(registry_path)
    registry_by_id = {item["case_unit_id"]: item for item in stronger_registry["cases"]}

    results = sorted((root / "results").glob("*/checklist.json"))
    packets = sorted((root / "case_packets/appworld").glob("*/case_packet.md"))
    freezes = sorted((root / "claim_freeze/checklists").glob("*/checklist.json"))
    if not (len(results) == len(packets) == len(freezes) == 68):
        fail("expected exactly 68 results, packets, and frozen checklists")
    case_ids = [path.parent.name for path in results]
    if len(set(case_ids)) != 68 or set(registry_by_id) != set(case_ids):
        fail("case ID closure mismatch")

    condition_count = 0
    gap_count = 0
    registered_test_count = 0
    support_pointer_count = 0
    support_pointer_occurrence_count = 0
    raw_file_count = 0
    for result_path in results:
        case_id = result_path.parent.name
        checklist = json.loads(result_path.read_text(encoding="utf-8"))
        repair_record = json.loads(
            (result_path.parent / "repair_record.json").read_text(encoding="utf-8")
        )
        if repair_record["outcome_or_released_result_inputs_read"] != []:
            fail(f"{case_id}: repair record declares outcome/result inputs")
        for path_key, hash_key in (
            ("source_checklist_path", "source_checklist_sha256"),
            ("source_packet_path", "source_packet_sha256"),
        ):
            source_path = REPO_ROOT / repair_record["source"][path_key]
            if not source_path.is_file() or sha256_file(source_path) != repair_record["source"][hash_key]:
                fail(f"{case_id}: source freeze binding drift: {path_key}")
        if repair_record["output"]["checklist_json_sha256"] != sha256_file(result_path):
            fail(f"{case_id}: repair-record JSON hash differs")
        if repair_record["output"]["checklist_yaml_sha256"] != sha256_file(
            result_path.with_suffix(".yaml")
        ):
            fail(f"{case_id}: repair-record YAML hash differs")
        if yaml_as_json(result_path.with_suffix(".yaml")) != checklist:
            fail(f"{case_id}: YAML and JSON checklist values differ")
        if (root / "claim_freeze/checklists" / case_id / "checklist.json").read_bytes() != result_path.read_bytes():
            fail(f"{case_id}: frozen JSON differs from result JSON")
        if (
            root / "claim_freeze/checklists" / case_id / "checklist.yaml"
        ).read_bytes() != result_path.with_suffix(".yaml").read_bytes():
            fail(f"{case_id}: frozen YAML differs from result YAML")

        packet_path = root / "case_packets/appworld" / case_id / "case_packet.md"
        packet = packet_path.read_text(encoding="utf-8")
        if repair_record["output"]["case_packet_sha256"] != sha256_file(packet_path):
            fail(f"{case_id}: repair-record packet hash differs")
        packet_visibility, packet_semantics, packet_native, packet_stronger = parse_packet(
            packet, case_id
        )
        if packet_visibility != visibility_file:
            fail(f"{case_id}: embedded visibility contract differs")
        if packet_semantics != evaluator_semantics:
            fail(f"{case_id}: embedded evaluator-semantics descriptor differs")
        if packet_native["required_native"] != checklist["native"]:
            fail(f"{case_id}: packet native registry differs from checklist")
        expected_conditions = [
            item["required_condition"] for item in packet_stronger["case"]["gaps"]
        ]
        if expected_conditions != checklist["stronger"]["additional_conditions"]:
            fail(f"{case_id}: packet stronger registry differs from checklist")
        if (
            packet_stronger["registry_canonical_json_sha256"] != registry_canonical_sha
            or packet_stronger["registry_file_sha256"] != registry_file_sha
        ):
            fail(f"{case_id}: packet stronger registry hash differs")
        if packet_stronger["case"] != registry_by_id[case_id]:
            fail(f"{case_id}: packet stronger case entry differs from registry")

        conditions = checklist["stronger"]["additional_conditions"]
        condition_count += len(conditions)
        gap_count += bool(conditions)
        registered_test_count += len(checklist["native"]["success_if"])
        if len(checklist["native"]["success_if"]) != len(checklist["native"]["fail_if"]):
            fail(f"{case_id}: native pass/fail registry length differs")
        if "official TestTracker results" in json.dumps(checklist, ensure_ascii=False):
            fail(f"{case_id}: old decisive TestTracker dependency remains")
        if "Native S iff every registered test is S" not in json.dumps(checklist["native"]):
            fail(f"{case_id}: explicit native S/F/U formula missing")
        for index, item in enumerate(conditions, start=1):
            validate_marker(item, index, case_id)

        raw_case = root / "case_packets/appworld" / case_id / "raw_case"
        raw_manifest = json.loads(
            (
                root
                / "case_packets/appworld"
                / case_id
                / "raw_case_manifest.json"
            ).read_text(encoding="utf-8")
        )
        official_inventory = set(raw_manifest["packet_files"])
        source_raw = SOURCE_ROOT / case_id / "raw_case"
        new_raw_paths = sorted(path.relative_to(raw_case) for path in raw_case.rglob("*") if path.is_file())
        old_raw_paths = sorted(path.relative_to(source_raw) for path in source_raw.rglob("*") if path.is_file())
        if new_raw_paths != old_raw_paths or len(new_raw_paths) != 19:
            fail(f"{case_id}: official raw source inventory differs or is not 19 files")
        for relative in new_raw_paths:
            if (raw_case / relative).read_bytes() != (source_raw / relative).read_bytes():
                fail(f"{case_id}: raw source bytes differ: {relative}")
        raw_file_count += len(new_raw_paths)

        source_packet = (SOURCE_ROOT / case_id / "case_packet.md").read_text(encoding="utf-8")
        if packet[packet.index("## Source Inventory"):] != source_packet[
            source_packet.index("## Source Inventory"):
        ]:
            fail(f"{case_id}: packet official source tail differs from source packet")

        seen_supports = set(string_supports(checklist))
        for pointer in sorted(seen_supports):
            validate_support(raw_case, pointer, case_id)
        all_supports = list(string_supports(checklist))
        for pointer in all_supports:
            if not official_pointer_resolves(
                task_dir=raw_case / "official",
                pointer=pointer,
                inventory_paths=official_inventory,
            ):
                fail(f"{case_id}: repository-native support resolver rejected {pointer}")
        support_pointer_count += len(seen_supports)
        support_pointer_occurrence_count += len(all_supports)

    if (gap_count, 68 - gap_count, condition_count, registered_test_count) != (34, 34, 44, 469):
        fail("cohort semantic counts drift")
    freeze_manifest = json.loads(
        (root / "claim_freeze/freeze_manifest.json").read_text(encoding="utf-8")
    )
    freeze_records = freeze_manifest["records"]
    if (
        freeze_manifest["case_count"] != 68
        or len(freeze_records) != 68
        or {item["case_unit_id"] for item in freeze_records} != set(case_ids)
        or freeze_manifest["records_sha256"] != sha256_object(freeze_records)
    ):
        fail("freeze manifest record hash mismatch")
    for record in freeze_records:
        case_id = record["case_unit_id"]
        expected = {
            "checklist_json_sha256": sha256_file(
                root / "claim_freeze/checklists" / case_id / "checklist.json"
            ),
            "checklist_yaml_sha256": sha256_file(
                root / "claim_freeze/checklists" / case_id / "checklist.yaml"
            ),
            "case_packet_sha256": sha256_file(
                root / "case_packets/appworld" / case_id / "case_packet.md"
            ),
        }
        if any(record[key] != value for key, value in expected.items()):
            fail(f"{case_id}: freeze record points to different bytes")

    experiment_manifest = json.loads(
        (root / "experiment_manifest.json").read_text(encoding="utf-8")
    )
    if (
        experiment_manifest["scope"]["case_ids_sha256"]
        != "2b54ce295ac44589ff9ceb689ea52daf69c64dfb0c76118db34af2b3e1da7c96"
        or experiment_manifest["artifact_visibility_contract_canonical_json_sha256"]
        != sha256_object(visibility_file)
        or experiment_manifest["artifact_visibility_contract_file_sha256"]
        != sha256_file(root / "artifact_visibility_contract.json")
        or experiment_manifest["stronger_registry_canonical_json_sha256"]
        != registry_canonical_sha
        or experiment_manifest["stronger_registry_file_sha256"] != registry_file_sha
        or experiment_manifest["frozen_evaluator_semantics_file_sha256"]
        != semantics_file_sha
        or experiment_manifest["pipeline_integration"]["status"]
        != "required_not_implemented_by_this_asset_repair"
    ):
        fail("experiment manifest semantic/hash binding drift")

    return {
        "status": "ok",
        "root": str(root),
        "case_count": 68,
        "registered_test_count": registered_test_count,
        "stronger_gap_case_count": gap_count,
        "stronger_no_gap_case_count": 68 - gap_count,
        "stronger_condition_count": condition_count,
        "unique_support_pointer_occurrence_count": support_pointer_count,
        "repository_resolved_support_pointer_occurrence_count": (
            support_pointer_occurrence_count
        ),
        "byte_identical_official_raw_file_count": raw_file_count,
        "manifest_files_sha256": manifest["files_sha256"],
        "stronger_registry_canonical_json_sha256": registry_canonical_sha,
        "stronger_registry_file_sha256": registry_file_sha,
        "frozen_evaluator_semantics_file_sha256": semantics_file_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    report = validate(args.root.expanduser().resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
